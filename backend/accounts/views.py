from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings

from .forms import CustomUserCreationForm


def LoginView(request):
    """로그인 뷰. 실패 시 오류 메시지를 템플릿에 전달한다."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL or "/")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get("next") or settings.LOGIN_REDIRECT_URL or "/"
            return redirect(next_url)
        # 로그인 실패: form.errors / form.non_field_errors 가 채워진 상태로 같은 페이지 렌더
        return render(
            request,
            "accounts/login.html",
            {"form": form},
            status=400,
        )

    form = AuthenticationForm(request)
    return render(request, "accounts/login.html", {"form": form})


def SignUpView(request):
    """회원가입 뷰. 성공 시 로그인 후 리다이렉트, 실패 시 오류와 함께 폼 다시 표시."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL or "/")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL or "/")
        return render(
            request,
            "accounts/signup.html",
            {"form": form},
            status=400,
        )

    form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})
