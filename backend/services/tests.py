import json
from typing import Any

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .llm_client import LLMClientError, get_llm_client
from .models import SocialService
from .privacy import analyze_profile_safety, mask_sensitive_text, normalize_profile
from .retrieval import retrieve_candidate_services


class PrivacyTest(TestCase):
    def test_mask_sensitive_text(self):
        raw = "연락처 010-1234-5678, 주민등록번호 900101-1234567"
        masked = mask_sensitive_text(raw)
        self.assertNotIn("010-1234-5678", masked)
        self.assertNotIn("900101-1234567", masked)
        self.assertIn("[MASKED]", masked)

    def test_normalize_profile_masks_all_fields(self):
        payload = {
            "age_group": "노년",
            "region_ctpv": "서울특별시",
            "special_notes": "주소는 서울시 강남구 테헤란로 123, 연락처 010-1111-2222",
        }
        profile = normalize_profile(payload)
        self.assertEqual(profile["age_group"], "노년")
        self.assertIn("[MASKED]", profile["special_notes"])

    def test_analyze_profile_safety_detects_sensitive(self):
        payload = {
            "special_notes": "재산 2억, 연락처 010-5555-6666",
        }
        report = analyze_profile_safety(payload)
        self.assertTrue(report.blocked)
        self.assertIn("special_notes", report.findings)


class RetrievalQualityTest(TestCase):
    def setUp(self):
        SocialService.objects.create(
            source=SocialService.SOURCE_LOCAL,
            external_id="L-1",
            title="송파구 어르신 건강 지원",
            summary="저소득 어르신 건강관리 서비스",
            region_ctpv="서울특별시",
            region_sgg="송파구",
            target_names="저소득",
            life_names="노년",
            theme_names="신체건강",
            detail_url="https://example.com/local/1",
        )
        SocialService.objects.create(
            source=SocialService.SOURCE_NATIONAL,
            external_id="N-1",
            title="전국 문화 지원 서비스",
            summary="청년 대상 문화 여가 지원",
            target_names="청년",
            life_names="청년",
            theme_names="문화·여가",
            detail_url="https://example.com/national/1",
        )

    def test_retrieval_prefers_region_and_target_match(self):
        profile = {
            "region_ctpv": "서울특별시",
            "region_sgg": "송파구",
            "target_type": "저소득",
            "life_stage": "노년",
            "interest_theme": "신체건강",
            "special_notes": "정기 진료 필요",
            "age_group": "노년",
        }
        results = retrieve_candidate_services(profile=profile, limit=2)
        self.assertTrue(results)
        self.assertEqual(str(results[0].external_id), "L-1")


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
                    "special_notes": "건강 지원이 필요함",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("recommendations", data)
        self.assertTrue(data["recommendations"])
        self.assertIn(data["llm"]["provider"], ["stub", "blocked", "none"])

    def test_chat_recommendation_fail_closed_on_sensitive_input(self):
        self.client.force_login(self.user)
        response: Any = self.client.post(
            reverse("services:chat_recommendation"),
            data=json.dumps(
                {
                    "special_notes": "연락처 010-2222-3333, 주소 서울시 송파구 올림픽로 88",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["llm"]["provider"], "blocked")
        self.assertIn("blocked_fields", data)


class LLMExternalGateTest(TestCase):
    @override_settings(
        SERVICE_LLM_MODE="gemini",
        ALLOW_EXTERNAL_LLM="false",
        GEMINI_API_KEY="dummy",
    )
    def test_external_llm_is_blocked_by_default(self):
        with self.assertRaises(LLMClientError):
            get_llm_client()
