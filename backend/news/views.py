from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import NewsCommentForm
from .models import News, NewsComment, NewsFetchStatus


def _today_failure_message() -> str | None:
    today = date.today()
    status = NewsFetchStatus.objects.filter(
        fetch_date=today, status=NewsFetchStatus.STATUS_FAILURE
    ).first()
    return status.message if status else None


def news_list(request):
    news_items = News.objects.all()
    context = {
        "news_items": news_items,
        "failure_message": _today_failure_message(),
    }
    return render(request, "news/news_list.html", context)


def news_detail(request, news_id):
    news = get_object_or_404(
        News.objects.prefetch_related("comments__user"), pk=news_id
    )
    comments = news.comments.all()

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "댓글을 작성하려면 로그인해야 합니다.")
            login_url = f"{reverse('login')}?next={request.path}"
            return redirect(login_url)

        form = NewsCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.news = news
            comment.user = request.user
            comment.save()
            messages.success(request, "댓글이 등록되었습니다.")
            return redirect("news:news_detail", news_id=news.news_id)
    else:
        form = NewsCommentForm()

    return render(
        request,
        "news/news_detail.html",
        {
            "news": news,
            "comments": comments,
            "form": form,
            "failure_message": _today_failure_message(),
        },
    )


@login_required
def comment_delete(request, news_id, comment_id):
    comment = get_object_or_404(
        NewsComment.objects.select_related("user"),
        comment_id=comment_id,
        news_id=news_id,
    )
    if comment.user != request.user:
        raise PermissionDenied("자신의 댓글만 삭제할 수 있습니다.")

    if request.method == "POST":
        comment.delete()
        messages.success(request, "댓글이 삭제되었습니다.")

    return redirect("news:news_detail", news_id=news_id)
