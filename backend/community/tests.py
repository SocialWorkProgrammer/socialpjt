import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import CommunityPost


class CommunityApiTest(TestCase):
    """Community API 전용 동작을 검증한다."""

    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            email="community-user@example.com",
            password="password123",
        )
        CommunityPost.objects.create(
            title="첫 글",
            content="환영합니다.",
            author_email=self.user.email,
            is_pinned=True,
        )
        CommunityPost.objects.create(
            title="둘째 글",
            content="공지 안내",
            author_email="other@example.com",
        )

    def test_community_list_api_requires_login(self):
        response = self.client.get("/community/api/")
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(data["error"]["code"], "authentication_required")

    def test_community_list_api_returns_items(self):
        self.client.force_login(self.user)
        response = self.client.get("/community/api/?q=둘째")
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["title"], "둘째 글")

    def test_community_detail_api_returns_item(self):
        target = CommunityPost.objects.first()
        self.client.force_login(self.user)
        response = self.client.get(f"/community/api/{target.id}/")
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["item"]["id"], target.id)
