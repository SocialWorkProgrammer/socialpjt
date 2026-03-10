from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Prefetch
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, CommunityForm
from .models import Comment, Community


@login_required
def community_list(request):
    posts = Community.objects.select_related("user")
    return render(
        request,
        "community/community_list.html",
        {"posts": posts},
    )


@login_required
def community_detail(request, post_id):
    queryset = Community.objects.select_related("user").prefetch_related(
        Prefetch("comments", queryset=Comment.objects.select_related("user"))
    )
    post = get_object_or_404(queryset, post_id=post_id)

    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            messages.success(request, "댓글이 등록되었습니다.")
            return redirect("community:community_detail", post_id=post_id)
    else:
        comment_form = CommentForm()
        Community.objects.filter(post_id=post_id).update(hit=F("hit") + 1)
        post.refresh_from_db(fields=["hit"])

    return render(
        request,
        "community/community_detail.html",
        {
            "post": post,
            "comment_form": comment_form,
        },
    )


@login_required
def community_create(request):
    if request.method == "POST":
        form = CommunityForm(request.POST)
        if form.is_valid():
            community = form.save(commit=False)
            community.user = request.user
            community.save()
            messages.success(request, "게시글이 생성되었습니다.")
            return redirect("community:community_detail", post_id=community.post_id)
    else:
        form = CommunityForm()

    return render(
        request,
        "community/community_form.html",
        {"form": form, "is_edit": False},
    )


@login_required
def community_update(request, post_id):
    post = get_object_or_404(Community, post_id=post_id)
    if post.user != request.user:
        return HttpResponseForbidden("자신의 글만 수정할 수 있습니다.")

    if request.method == "POST":
        form = CommunityForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "게시글이 수정되었습니다.")
            return redirect("community:community_detail", post_id=post_id)
    else:
        form = CommunityForm(instance=post)

    return render(
        request,
        "community/community_form.html",
        {"form": form, "is_edit": True, "post": post},
    )


@login_required
def community_delete(request, post_id):
    post = get_object_or_404(Community, post_id=post_id)
    if post.user != request.user:
        return HttpResponseForbidden("자신의 글만 삭제할 수 있습니다.")

    if request.method == "POST":
        post.delete()
        messages.success(request, "게시글이 삭제되었습니다.")
        return redirect("community:community_list")

    return render(
        request,
        "community/community_confirm_delete.html",
        {"post": post},
    )


@login_required
def comment_delete(request, post_id, comment_id):
    comment = get_object_or_404(Comment, comment_id=comment_id, post_id=post_id)
    if comment.user != request.user:
        return HttpResponseForbidden("자신의 댓글만 삭제할 수 있습니다.")

    if request.method == "POST":
        comment.delete()
        messages.success(request, "댓글이 삭제되었습니다.")

    return redirect("community:community_detail", post_id=post_id)

# Create your views here.
