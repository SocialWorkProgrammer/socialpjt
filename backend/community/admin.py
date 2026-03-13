from django.contrib import admin

from .models import CommunityPost


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    """커뮤니티 게시글 데이터를 관리자 화면에서 관리한다."""

    list_display = ("title", "author_email", "is_pinned", "view_count", "created_at")
    list_filter = ("is_pinned",)
    search_fields = ("title", "content", "author_email")
