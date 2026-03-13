from django.contrib import admin

from .models import News, NewsFetchStatus


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("news_id", "title", "created_at", "fetched_at")
    search_fields = ("title", "content")


@admin.register(NewsFetchStatus)
class NewsFetchStatusAdmin(admin.ModelAdmin):
    list_display = ("fetch_date", "status", "message", "updated_at")
    list_filter = ("status",)
