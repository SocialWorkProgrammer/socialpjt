# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# CustomUser를 관리하는 클래스
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("이메일은 반드시 입력해야 합니다.")
        email = self.normalize_email(email) # 이메일 표준화(ex : 도메인을 대문자로 써도 소문자화 해주는 등)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # 비밀번호 해시 저장
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

# 실제 db에 들어가는 모델
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"   # 로그인 시 사용할 필드
    REQUIRED_FIELDS = []       # 슈퍼유저 생성 시 추가 필드 없음

    objects = CustomUserManager()

    def __str__(self):
        return self.email