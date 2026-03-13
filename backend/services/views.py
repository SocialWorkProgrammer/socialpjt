from datetime import date

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import ServiceFetchStatus, SocialService


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
