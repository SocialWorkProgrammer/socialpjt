from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import News


def _auth_required_json_response():
    """비로그인 요청에 대해 템플릿 redirect 대신 JSON 401을 반환한다."""

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


def _to_positive_int(
    raw_value: str | None,
    default: int,
    min_value: int = 1,
    max_value: int = 50,
) -> int:
    """페이지네이션 파라미터를 비정상 값으로부터 안전하게 정규화한다."""

    try:
        value = int(raw_value or "")
    except (TypeError, ValueError):
        return default
    if value < min_value:
        return default
    if value > max_value:
        return max_value
    return value


def _serialize_news_item(item: News) -> dict:
    """News 객체를 프론트에서 바로 쓰기 좋은 JSON 형태로 변환한다."""

    return {
        "news_id": item.news_id,
        "title": item.title,
        "content": item.content,
        "source_url": item.source_url,
        "created_at": item.created_at.isoformat(),
        "fetched_at": item.fetched_at.isoformat(),
    }


@login_required
def news_list(request):
    return render(request, "news/news_list.html", {"news_items": News.objects.all()})


def news_list_api(request):
    """뉴스 목록 조회 전용 API. SPA에서 JSON으로 목록을 소비한다."""

    if not request.user.is_authenticated:
        return _auth_required_json_response()

    query = (request.GET.get("q") or "").strip()
    page = _to_positive_int(request.GET.get("page"), 1)
    page_size = _to_positive_int(request.GET.get("page_size"), 12, max_value=50)

    queryset = News.objects.all()
    if query:
        queryset = queryset.filter(title__icontains=query)

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    return JsonResponse(
        {
            "ok": True,
            "items": [_serialize_news_item(item) for item in page_obj.object_list],
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


def news_detail_api(request, news_id: int):
    """뉴스 상세 조회 전용 API."""

    if not request.user.is_authenticated:
        return _auth_required_json_response()

    news_item = get_object_or_404(News, news_id=news_id)
    return JsonResponse({"ok": True, "item": _serialize_news_item(news_item)})
