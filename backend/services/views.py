import json
import logging
from typing import Any
from datetime import date

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render

from .llm_client import LLMClientError, get_llm_client
from .models import ServiceFetchStatus, SocialService
from .privacy import analyze_profile_safety, normalize_profile
from .retrieval import retrieve_candidate_services, serialize_candidates


logger = logging.getLogger(__name__)


def _auth_required_json_response():
    """API 요청에 대한 공통 인증 실패 응답을 반환한다."""

    return JsonResponse(
        {
            "ok": False,
            "error": {
                "code": "authentication_required",
                "message": "로그인이 필요합니다.",
            },
        },
        status=401,
    )


def _to_positive_int(raw_value: str | None, default: int, min_value: int = 1, max_value: int = 50) -> int:
    try:
        value = int(raw_value or "")
    except (TypeError, ValueError):
        return default
    if value < min_value:
        return default
    if value > max_value:
        return max_value
    return value


def _serialize_service_item(item: Any) -> dict[str, Any]:
    return {
        "id": item.social_service_id,
        "source": item.source,
        "source_label": item.get_source_display() if hasattr(item, "get_source_display") else item.source,
        "external_id": item.external_id,
        "title": item.title,
        "summary": item.summary,
        "detail_url": item.detail_url,
        "site_url": item.site_url,
        "region_ctpv": item.region_ctpv,
        "region_sgg": item.region_sgg,
        "target_names": item.target_names,
        "theme_names": item.theme_names,
        "life_names": item.life_names,
        "apply_method_name": item.apply_method_name,
        "support_type": item.support_type,
        "fetched_at": item.fetched_at.isoformat() if item.fetched_at else None,
        "online_applicable": item.online_applicable,
        "view_count": item.view_count,
    }


def _today_failure_message() -> str | None:
    today = date.today()
    status = ServiceFetchStatus.objects.filter(
        fetch_date=today,
        status=ServiceFetchStatus.STATUS_FAILURE,
    ).first()
    return status.message if status else None


def service_list(request):
    queryset = SocialService.objects.all()
    keyword = request.GET.get("q", "").strip()
    source = request.GET.get("source", "").strip()
    category = request.GET.get("category", "").strip()
    region = request.GET.get("region", "").strip()

    if keyword:
        queryset = queryset.filter(title__icontains=keyword)
    if source:
        queryset = queryset.filter(source=source)
    if category:
        queryset = queryset.filter(theme_codes__icontains=category)
    if region:
        queryset = queryset.filter(region_ctpv__icontains=region)

    paginator = Paginator(queryset, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "keyword": keyword,
        "source": source,
        "category": category,
        "region": region,
        "source_choices": SocialService.SOURCE_CHOICES,
        "failure_message": _today_failure_message(),
    }
    return render(request, "services/service_list.html", context)


def service_list_api(request):
    """서비스 목록 조회 전용 API."""

    if not request.user.is_authenticated:
        return _auth_required_json_response()

    keyword = request.GET.get("q", "").strip()
    source = request.GET.get("source", "").strip()
    category = request.GET.get("category", "").strip()
    region = request.GET.get("region", "").strip()
    page = _to_positive_int(request.GET.get("page"), 1)
    page_size = _to_positive_int(request.GET.get("page_size"), 12)

    queryset = SocialService.objects.all()
    if keyword:
        queryset = queryset.filter(title__icontains=keyword)
    if source:
        queryset = queryset.filter(source=source)
    if category:
        queryset = queryset.filter(theme_names__icontains=category)
    if region:
        queryset = queryset.filter(region_ctpv__icontains=region)

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    return JsonResponse(
        {
            "ok": True,
            "items": [_serialize_service_item(service) for service in page_obj.object_list],
            "pagination": {
                "page": page_obj.number,
                "page_size": page_size,
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
                "has_previous": page_obj.has_previous(),
                "has_next": page_obj.has_next(),
            },
        }
    )


def service_detail(request, service_id):
    service = get_object_or_404(SocialService, pk=service_id)
    return render(
        request,
        "services/service_detail.html",
        {
            "service": service,
            "failure_message": _today_failure_message(),
        },
    )


def service_detail_api(request, service_id: int):
    """서비스 상세 조회 전용 API."""

    if not request.user.is_authenticated:
        return _auth_required_json_response()

    service = get_object_or_404(SocialService, pk=service_id)
    return JsonResponse({"ok": True, "item": _serialize_service_item(service)})


@require_POST
def chat_recommendation(request):
    if not request.user.is_authenticated:
        return _auth_required_json_response()

    return recommend_services(request)


@require_POST
def recommend_services(request):
    if not request.user.is_authenticated:
        return _auth_required_json_response()

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "유효한 JSON 형식이 아닙니다."}, status=400)

    safety_report = analyze_profile_safety(payload)
    profile = normalize_profile(payload)
    candidates = retrieve_candidate_services(profile=profile, limit=5)
    candidate_payload = serialize_candidates(candidates)

    if safety_report.blocked:
        logger.warning(
            "llm_call_blocked reason=sensitive_input fields=%s user_id=%s",
            ",".join(safety_report.findings),
            getattr(request.user, "id", None),
        )
        return JsonResponse(
            {
                "profile": profile,
                "recommendations": candidate_payload,
                "llm": {
                    "provider": "blocked",
                    "used_fallback": False,
                    "message": "민감정보가 감지되어 AI 문장 생성을 차단했습니다. 검색 결과만 제공합니다.",
                },
                "blocked_fields": safety_report.findings,
                "disclaimer": "추천 결과는 참고용이며 최종 판단은 사회복지사 검토가 필요합니다.",
            },
            status=200,
        )

    try:
        llm_client = get_llm_client()
        llm_result = llm_client.generate_recommendation(
            profile=profile,
            candidates=candidate_payload,
        )
    except Exception as exc:
        fallback_message = "AI 응답 생성에 실패해 검색 결과만 제공합니다."
        if isinstance(exc, LLMClientError):
            fallback_message = f"AI 설정 오류: {exc}"
        logger.warning("llm_call_error error=%s user_id=%s", exc, getattr(request.user, "id", None))
        return JsonResponse(
            {
                "profile": profile,
                "recommendations": candidate_payload,
                "llm": {
                    "provider": "none",
                    "used_fallback": False,
                    "message": fallback_message,
                },
                "disclaimer": "추천 결과는 참고용이며 최종 판단은 사회복지사 검토가 필요합니다.",
            },
            status=200,
        )

    return JsonResponse(
        {
            "profile": profile,
            "recommendations": candidate_payload,
            "llm": {
                "provider": llm_result.provider,
                "used_fallback": llm_result.used_fallback,
                "message": llm_result.message,
            },
            "disclaimer": "추천 결과는 참고용이며 최종 판단은 사회복지사 검토가 필요합니다.",
        }
    )
