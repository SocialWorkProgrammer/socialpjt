from django.contrib import admin

from .models import News, NewsComment, NewsFetchStatus


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("news_id", "title", "created_at", "fetched_at")
    search_fields = ("title", "content")
    list_filter = ("created_at",)


@admin.register(NewsComment)
class NewsCommentAdmin(admin.ModelAdmin):
    list_display = ("comment_id", "news", "user", "created_at")
    search_fields = ("content", "user__email")


@admin.register(NewsFetchStatus)
class NewsFetchStatusAdmin(admin.ModelAdmin):
    list_display = ("fetch_date", "status", "message", "updated_at")
    list_filter = ("status",)
