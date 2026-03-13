from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import CommunityPost


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


def _serialize_post_item(post: CommunityPost) -> dict:
    """게시글 ORM 객체를 프론트에서 바로 쓰는 JSON 형태로 변환한다."""

    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author_email": post.author_email,
        "is_pinned": post.is_pinned,
        "view_count": post.view_count,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
    }


@login_required
def community_list(request):
    return render(request, "community/community_list.html")


def community_list_api(request):
    """커뮤니티 목록 조회 전용 API. SPA에서 JSON으로 목록을 소비한다."""

    if not request.user.is_authenticated:
        return _auth_required_json_response()

    query = (request.GET.get("q") or "").strip()
    page = request.GET.get("page")
    try:
        page_num = max(1, int(page or 1))
    except (TypeError, ValueError):
        page_num = 1

    queryset = CommunityPost.objects.all()
    if query:
        queryset = queryset.filter(title__icontains=query)

    paginator = Paginator(queryset, 12)
    page_obj = paginator.get_page(page_num)

    return JsonResponse(
        {
            "ok": True,
            "items": [_serialize_post_item(post) for post in page_obj.object_list],
            "pagination": {
                "page": page_obj.number,
                "page_size": 12,
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
                "has_previous": page_obj.has_previous(),
                "has_next": page_obj.has_next(),
            },
        }
    )


def community_detail_api(request, post_id: int):
    """커뮤니티 상세 조회 전용 API."""

    if not request.user.is_authenticated:
        return _auth_required_json_response()

    post = get_object_or_404(CommunityPost, id=post_id)
    return JsonResponse({"ok": True, "item": _serialize_post_item(post)})
