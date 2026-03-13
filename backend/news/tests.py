import json
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import News


class NewsApiTest(TestCase):
    """News API 전용 동작을 검증한다."""

    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            email="news-user@example.com",
            password="password123",
        )
        News.objects.create(
            title="서울 노인 복지 알림",
            content="요양 관련 공고",
            source_url="https://example.com/news/1",
            created_at=date(2026, 1, 1),
        )
        News.objects.create(
            title="경기도 지원금 안내",
            content="지원금 공지",
            source_url="https://example.com/news/2",
            created_at=date(2026, 1, 2),
        )

    def test_news_list_api_requires_login(self):
        response = self.client.get("/news/api/")
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(data["error"]["code"], "authentication_required")

    def test_news_list_api_pagination_and_search(self):
        self.client.force_login(self.user)
        response = self.client.get("/news/api/?q=서울&page=1&page_size=1")
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["pagination"]["page_size"], 1)
        self.assertEqual(data["items"][0]["title"], "서울 노인 복지 알림")

    def test_news_detail_api_returns_item(self):
        target = News.objects.first()
        self.client.force_login(self.user)
        response = self.client.get(f"/news/api/{target.news_id}/")
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["item"]["news_id"], target.news_id)
