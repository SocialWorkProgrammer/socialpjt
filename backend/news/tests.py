from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from news.management.commands.fetch_news import BokjiroNewsCrawler


SAMPLE_BOKJIRO_HTML = """
<div class="news-list">
  <a href="https://example.com/ignore-me">무관한 링크</a>
  <div class="news-item">
    <div class="news-title">
      <a class="cl-text-wrapper" role="link">정부 \"고유가 피해지원금 'URL 문자·알림'은 100% 사기\"</a>
    </div>
    <div class="news-txt">
      (서울=연합뉴스) 양정우 기자 = 정부는 고유가 피해지원금 관련 URL이 포함된 문자는 발송하지 않는다고 밝혔다.
    </div>
    <div class="news-date news-date-line">2026.04.16</div>
  </div>
  <div class="news-item">
    <div class="news-title">
      <a class="cl-text-wrapper" href="/article/2" role="link">저소득 중증 소아청소년·장애아동 의료급여 품목 확대</a>
    </div>
    <div class="news-txt">
      의료급여법 시행규칙 일부개정령안 입법 예고 소식이다.
    </div>
    <div class="news-date news-date-line">2026.04.16</div>
  </div>
</div>
"""

SAMPLE_DUPLICATE_TITLE_HTML = """
<div class="news-list">
  <div class="news-item">
    <div class="news-title">
      <a class="cl-text-wrapper" role="link">동일 제목 기사</a>
    </div>
    <div class="news-txt">첫 번째 기사 본문입니다.</div>
    <div class="news-date news-date-line">2026.04.16</div>
  </div>
  <div class="news-item">
    <div class="news-title">
      <a class="cl-text-wrapper" role="link">동일 제목 기사</a>
    </div>
    <div class="news-txt">두 번째 기사 본문입니다.</div>
    <div class="news-date news-date-line">2026.04.16</div>
  </div>
</div>
"""


class BokjiroNewsCrawlerTests(SimpleTestCase):
    def test_extract_entries_parses_news_items_only(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10)

        entries = crawler._extract_entries(SAMPLE_BOKJIRO_HTML)

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].title, '정부 "고유가 피해지원금 \'URL 문자·알림\'은 100% 사기"')
        self.assertIn("URL이 포함된 문자는 발송하지 않는다", entries[0].content)
        self.assertEqual(str(entries[0].created_at), "2026-04-16")
        self.assertTrue(entries[0].source_url.startswith(f"{crawler.BASE_URL}?"))

        self.assertEqual(entries[1].title, "저소득 중증 소아청소년·장애아동 의료급여 품목 확대")
        self.assertEqual(
            entries[1].source_url,
            "https://www.bokjiro.go.kr/article/2",
        )

    def test_fetch_news_command_saves_news_and_status(self) -> None:
        crawler_path = "news.management.commands.fetch_news.BokjiroNewsCrawler._request_list_page"
        store_path = "news.management.commands.fetch_news.Command._store_entries"
        status_path = "news.management.commands.fetch_news.Command._mark_status"
        stdout = StringIO()

        with patch(crawler_path, return_value=SAMPLE_BOKJIRO_HTML), patch(
            store_path,
            return_value=2,
        ) as mocked_store, patch(status_path) as mocked_status:
            call_command("fetch_news", limit=10, stdout=stdout)

        saved_entries = mocked_store.call_args.args[0]
        self.assertEqual(len(saved_entries), 2)
        self.assertIn("고유가 피해지원금", saved_entries[0].title)
        mocked_status.assert_called_once_with(success=True, message="")
        self.assertIn("뉴스 2건 저장 완료", stdout.getvalue())

    def test_builds_distinct_synthetic_urls_for_same_title_and_date(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10)

        entries = crawler._extract_entries(SAMPLE_DUPLICATE_TITLE_HTML)

        self.assertEqual(len(entries), 2)
        self.assertNotEqual(entries[0].source_url, entries[1].source_url)
        self.assertIn("첫 번째 기사", entries[0].content)
        self.assertIn("두 번째 기사", entries[1].content)
