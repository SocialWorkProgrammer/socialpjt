from django.contrib.auth import login, logout as logout_user
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import CustomUserCreationForm


def _is_ajax_request(request):
    """AJAX/JSON 요청 여부를 판단한다."""

    accept_header = request.headers.get("Accept", "")
    requested_with = request.headers.get("X-Requested-With", "")
    return requested_with == "XMLHttpRequest" or "application/json" in accept_header


def _serialize_user(user):
    return {"id": user.id, "email": user.email}


def _collect_form_errors(form):
    errors = {field: [str(error) for error in message_list] for field, message_list in form.errors.items()}
    if form.non_field_errors():
        errors["non_field_errors"] = [str(error) for error in form.non_field_errors()]
    return errors


@ensure_csrf_cookie
def SessionView(request):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "로그인이 필요합니다."}, status=401)

    return JsonResponse({"ok": True, "user": _serialize_user(request.user)})


@ensure_csrf_cookie
def LoginView(request):
    """로그인 뷰. 실패 시 오류 메시지를 템플릿에 전달한다."""
    if request.user.is_authenticated:
        if _is_ajax_request(request):
            return JsonResponse({"ok": True, "user": _serialize_user(request.user)})
        return redirect(settings.LOGIN_REDIRECT_URL or "/")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if _is_ajax_request(request):
                return JsonResponse({"ok": True, "user": _serialize_user(user)})
            next_url = request.GET.get("next") or settings.LOGIN_REDIRECT_URL or "/"
            return redirect(next_url)

        if _is_ajax_request(request):
            return JsonResponse(
                {
                    "ok": False,
                    "error": "이메일 또는 비밀번호가 일치하지 않습니다.",
                    "fields": _collect_form_errors(form),
                },
                status=400,
            )

        # 로그인 실패: form.errors / form.non_field_errors 가 채워진 상태로 같은 페이지 렌더
        return render(
            request,
            "accounts/login.html",
            {"form": form},
            status=400,
        )

    form = AuthenticationForm(request)
    return render(request, "accounts/login.html", {"form": form})


@ensure_csrf_cookie
def SignUpView(request):
    """회원가입 뷰. 성공 시 로그인 후 리다이렉트, 실패 시 오류와 함께 폼 다시 표시."""
    if request.user.is_authenticated:
        if _is_ajax_request(request):
            return JsonResponse({"ok": True, "user": _serialize_user(request.user)})
        return redirect(settings.LOGIN_REDIRECT_URL or "/")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if _is_ajax_request(request):
                return JsonResponse({"ok": True, "user": _serialize_user(user)})
            return redirect(settings.LOGIN_REDIRECT_URL or "/")

            
        if _is_ajax_request(request):
            return JsonResponse(
                {
                    "ok": False,
                    "error": "입력한 정보를 확인해주세요.",
                    "fields": _collect_form_errors(form),
                },
                status=400,
            )
        return render(
            request,
            "accounts/signup.html",
            {"form": form},
            status=400,
        )

    form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})


@require_POST
@ensure_csrf_cookie
def LogoutView(request):
    logout_user(request)
    if _is_ajax_request(request):
        return JsonResponse({"ok": True})

    return redirect(settings.LOGIN_REDIRECT_URL or "/")
