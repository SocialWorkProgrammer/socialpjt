from django.contrib import admin

from .models import Comment, Community


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("post_id", "title", "user", "hit", "created_at")
    search_fields = ("title", "description", "user__email")
    list_filter = ("is_image", "created_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("comment_id", "post", "user", "com_posted_at")
    search_fields = ("com_comment", "user__email")
