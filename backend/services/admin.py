from django.contrib import admin

from .models import ServiceFetchStatus, SocialService


@admin.register(SocialService)
class SocialServiceAdmin(admin.ModelAdmin):
    list_display = (
        "social_service_id",
        "source",
        "external_id",
        "title",
        "region_ctpv",
        "last_modified",
        "fetched_at",
    )
    list_filter = ("source", "region_ctpv", "online_applicable")
    search_fields = (
        "external_id",
        "title",
        "summary",
        "ministry",
        "organization",
        "life_codes",
        "theme_codes",
        "life_names",
        "theme_names",
    )


@admin.register(ServiceFetchStatus)
class ServiceFetchStatusAdmin(admin.ModelAdmin):
    list_display = ("fetch_date", "source", "status", "message", "updated_at")
    list_filter = ("source", "status")
