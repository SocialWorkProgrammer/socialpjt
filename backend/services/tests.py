import json
from typing import Any

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import SocialService
from .privacy import mask_sensitive_text, normalize_profile


class PrivacyTest(TestCase):
    def test_mask_sensitive_text(self):
        raw = "연락처 010-1234-5678, 주민등록번호 900101-1234567"
        masked = mask_sensitive_text(raw)
        self.assertNotIn("010-1234-5678", masked)
        self.assertNotIn("900101-1234567", masked)
        self.assertIn("[MASKED]", masked)

    def test_normalize_profile(self):
        payload = {
            "age_group": "노년",
            "special_notes": "주소는 서울시 강남구 테헤란로 123",
        }
        profile = normalize_profile(payload)
        self.assertEqual(profile["age_group"], "노년")
        self.assertIn("[MASKED]", profile["special_notes"])


class ChatRecommendationTest(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        SocialService.objects.create(
            source=SocialService.SOURCE_LOCAL,
            external_id="L-1",
            title="어르신 건강 지원 서비스",
            summary="저소득 어르신 대상 건강관리 지원",
            region_ctpv="서울특별시",
            region_sgg="송파구",
            target_names="저소득",
            theme_names="신체건강",
            detail_url="https://example.com/service/1",
        )
    def test_chat_recommendation_requires_login(self):
        response: Any = self.client.post(
            reverse("services:chat_recommendation"),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_chat_recommendation_returns_recommendations(self):
        self.client.force_login(self.user)
        response: Any = self.client.post(
            reverse("services:chat_recommendation"),
            data=json.dumps(
                {
                    "age_group": "노년",
                    "region_ctpv": "서울특별시",
                    "region_sgg": "송파구",
                    "target_type": "저소득",
                    "interest_theme": "신체건강",
                    "special_notes": "연락처 010-2222-3333",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("recommendations", data)
        self.assertTrue(data["recommendations"])
        self.assertEqual(data["llm"]["provider"], "stub")
