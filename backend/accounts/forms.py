from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class CustomUserCreationForm(forms.Form):
    """이메일·비밀번호 회원가입 폼 (CustomUser용)"""
    email = forms.EmailField(
        label="이메일",
        widget=forms.EmailInput(attrs={"autofocus": True, "placeholder": "example@email.com"}),
    )
    password1 = forms.CharField(
        label="비밀번호",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "8자 이상"}),
    )
    password2 = forms.CharField(
        label="비밀번호 확인",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "비밀번호 다시 입력"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("이미 사용 중인 이메일입니다.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError({"password2": "두 비밀번호가 일치하지 않습니다."})
        return cleaned_data

    def save(self, commit=True):
        user = User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
        )
        return user
