import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render

from .llm_client import get_llm_client
from .models import ServiceFetchStatus, SocialService
from .privacy import normalize_profile
from .retrieval import retrieve_candidate_services, serialize_candidates


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


@login_required
@require_POST
def chat_recommendation(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "유효한 JSON 형식이 아닙니다."}, status=400)

    profile = normalize_profile(payload)
    candidates = retrieve_candidate_services(profile=profile, limit=5)
    candidate_payload = serialize_candidates(candidates)

    llm_client = get_llm_client()
    llm_result = llm_client.generate_recommendation(
        profile=profile,
        candidates=candidate_payload,
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
