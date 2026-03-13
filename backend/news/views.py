from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import News


@login_required
def news_list(request):
    return render(request, "news/news_list.html", {"news_items": News.objects.all()})
