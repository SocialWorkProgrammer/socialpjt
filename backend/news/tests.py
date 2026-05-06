from datetime import date
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import OutputWrapper
from django.test import SimpleTestCase

from news.management.commands.fetch_news import BokjiroNewsCrawler, Command, CrawledNews


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
            call_command("fetch_news", limit=10, source="http", stdout=stdout)

        saved_entries = mocked_store.call_args.args[0]
        self.assertEqual(len(saved_entries), 2)
        self.assertIn("고유가 피해지원금", saved_entries[0].title)
        mocked_status.assert_called_once_with(success=True, message="")
        self.assertIn("뉴스 2건 저장 완료", stdout.getvalue())

    def test_fetch_news_command_uses_browser_source_by_default(self) -> None:
        crawler_path = "news.management.commands.fetch_news.BokjiroNewsCrawler._fetch_rendered_entries"
        store_path = "news.management.commands.fetch_news.Command._store_entries"
        status_path = "news.management.commands.fetch_news.Command._mark_status"
        stdout = StringIO()
        crawler = BokjiroNewsCrawler(limit=10)
        entries = crawler._extract_entries(SAMPLE_BOKJIRO_HTML)

        with patch(crawler_path, return_value=entries) as mocked_rendered, patch(
            store_path,
            return_value=2,
        ), patch(status_path):
            call_command("fetch_news", limit=10, stdout=stdout)

        mocked_rendered.assert_called_once_with(1)
        self.assertIn("뉴스 2건 저장 완료", stdout.getvalue())

    def test_split_rendered_item_text_falls_back_without_news_classes(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10)

        title, content, date_text = crawler._split_rendered_item_text(
            "복지 서비스 신청 안내\n신청 대상과 기간을 확인하세요.\n2026.04.16",
        )

        self.assertEqual(title, "복지 서비스 신청 안내")
        self.assertEqual(content, "신청 대상과 기간을 확인하세요.")
        self.assertEqual(date_text, "2026.04.16")

    def test_move_to_rendered_page_passes_wait_argument_by_keyword(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10)
        item_locator = Mock()
        item_locator.all_inner_texts.return_value = ["이전 뉴스"]
        page_button_locator = Mock()
        page_button_locator.count.return_value = 1
        page = Mock()

        def locator_side_effect(selector):
            if selector == crawler.RENDERED_LIST_SELECTOR:
                return item_locator
            if selector == '.pagination a:text-is("2")':
                return page_button_locator
            missing_locator = Mock()
            missing_locator.count.return_value = 0
            return missing_locator

        page.locator.side_effect = locator_side_effect

        crawler._move_to_rendered_page(page, page_index=2)

        page_button_locator.first.click.assert_called_once()
        self.assertEqual(
            page.wait_for_function.call_args.kwargs["arg"],
            [crawler.RENDERED_LIST_SELECTOR, ["이전 뉴스"]],
        )
        self.assertEqual(
            page.wait_for_function.call_args.kwargs["timeout"],
            crawler.PLAYWRIGHT_TIMEOUT_MS,
        )

    def test_move_to_rendered_page_clicks_next_range_before_later_page(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10)
        item_locator = Mock()
        item_locator.all_inner_texts.return_value = ["이전 뉴스"]
        pagination_locator = Mock()
        pagination_locator.all_inner_texts.return_value = ["1 2 3 4 5 6 7 8 9 10"]
        next_range_locator = Mock()
        next_range_locator.count.return_value = 1
        page_button_locator = Mock()
        page_button_locator.count.return_value = 1
        missing_locator = Mock()
        missing_locator.count.return_value = 0
        page = Mock()
        page_button_requests = 0

        def locator_side_effect(selector):
            nonlocal page_button_requests
            if selector == crawler.RENDERED_LIST_SELECTOR:
                return item_locator
            if selector == crawler.PAGINATION_RANGE_SELECTOR:
                return pagination_locator
            if selector == '.pagination a:text-is("11")':
                page_button_requests += 1
                if page_button_requests == 1:
                    return missing_locator
                return page_button_locator
            if selector == crawler.NEXT_PAGE_RANGE_SELECTORS[0]:
                return next_range_locator
            return missing_locator

        page.locator.side_effect = locator_side_effect

        crawler._move_to_rendered_page(page, page_index=11)

        next_range_locator.first.click.assert_called_once()
        page_button_locator.first.click.assert_called_once()
        self.assertEqual(page.wait_for_function.call_count, 2)
        self.assertEqual(
            page.wait_for_function.call_args_list[0].kwargs["arg"],
            [crawler.PAGINATION_RANGE_SELECTOR, ["1 2 3 4 5 6 7 8 9 10"]],
        )
        self.assertEqual(
            page.wait_for_function.call_args_list[1].kwargs["arg"],
            [crawler.RENDERED_LIST_SELECTOR, ["이전 뉴스"]],
        )
        self.assertEqual(
            page.wait_for_function.call_args_list[0].kwargs["timeout"],
            crawler.PLAYWRIGHT_TIMEOUT_MS,
        )
        self.assertEqual(
            page.wait_for_function.call_args_list[1].kwargs["timeout"],
            crawler.PLAYWRIGHT_TIMEOUT_MS,
        )

    def test_pagination_selectors_are_scoped_to_pagination_area(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10)

        selectors = crawler._pagination_button_selectors("2")

        self.assertIn('.pagination a:text-is("2")', selectors)
        self.assertIn('nav button:text-is("2")', selectors)
        self.assertNotIn('text="2"', selectors)

    def test_next_page_range_selectors_target_bokjiro_next_button(self) -> None:
        selectors = BokjiroNewsCrawler.NEXT_PAGE_RANGE_SELECTORS

        self.assertIn(
            '.cl-pageindexer-next[role="button"][data-region="next"]',
            selectors,
        )
        self.assertIn(
            '[data-region="next"][aria-label="다음 페이지 범위"]',
            selectors,
        )

    def test_playwright_network_error_message_does_not_blame_install(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10)

        message = crawler._playwright_error_message(
            "Page.goto: net::ERR_CONNECTION_RESET at https://www.bokjiro.go.kr/",
        )

        self.assertIn("복지로 사이트 연결이 중간에 끊겼습니다", message)
        self.assertNotIn("브라우저가 설치되어 있지 않습니다", message)

    def test_crawler_accepts_headed_debug_options(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10, headless=False, slow_mo=250)

        self.assertFalse(crawler.headless)
        self.assertEqual(crawler.slow_mo, 250)

    def test_route_nonessential_resource_blocks_heavy_static_assets(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10)
        route = Mock()
        route.request.resource_type = "image"
        route.request.url = "https://www.bokjiro.go.kr/logo.png"

        crawler._route_nonessential_resource(route)

        route.abort.assert_called_once()
        route.continue_.assert_not_called()

    def test_route_nonessential_resource_allows_documents_and_scripts(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10)
        route = Mock()
        route.request.resource_type = "script"
        route.request.url = "https://www.bokjiro.go.kr/runtime/app.js"

        crawler._route_nonessential_resource(route)

        route.continue_.assert_called_once()
        route.abort.assert_not_called()

    def test_fetch_entries_with_retry_succeeds_after_transient_error(self) -> None:
        command = Command()
        crawler = Mock()
        entries = [
            CrawledNews(
                title="재시도 성공 뉴스",
                content="본문",
                source_url="https://example.com/retry",
                created_at=date(2026, 4, 16),
            ),
        ]
        crawler.fetch.side_effect = [RuntimeError("net::ERR_CONNECTION_RESET"), entries]

        with patch("news.management.commands.fetch_news.time.sleep") as mocked_sleep:
            result = command._fetch_entries_with_retry(crawler=crawler, page_index=1)

        self.assertEqual(result, entries)
        self.assertEqual(crawler.fetch.call_count, 2)
        mocked_sleep.assert_called_once_with(command.FETCH_RETRY_DELAY_SECONDS)

    def test_fetch_entries_with_retry_raises_after_max_attempts(self) -> None:
        command = Command()
        crawler = Mock()
        crawler.fetch.side_effect = RuntimeError("net::ERR_CONNECTION_RESET")

        with patch("news.management.commands.fetch_news.time.sleep") as mocked_sleep:
            with self.assertRaisesRegex(RuntimeError, "ERR_CONNECTION_RESET"):
                command._fetch_entries_with_retry(crawler=crawler, page_index=1)

        self.assertEqual(crawler.fetch.call_count, command.MAX_FETCH_ATTEMPTS)
        self.assertEqual(mocked_sleep.call_count, command.MAX_FETCH_ATTEMPTS - 1)

    def test_fetch_entries_with_retry_does_not_retry_missing_playwright(self) -> None:
        command = Command()
        crawler = Mock()
        crawler.fetch.side_effect = RuntimeError("Playwright가 설치되어 있지 않습니다")

        with patch("news.management.commands.fetch_news.time.sleep") as mocked_sleep:
            with self.assertRaisesRegex(RuntimeError, "Playwright"):
                command._fetch_entries_with_retry(crawler=crawler, page_index=1)

        crawler.fetch.assert_called_once_with(page_index=1)
        mocked_sleep.assert_not_called()

    def test_bootstrap_can_continue_when_page_has_only_existing_entries(self) -> None:
        command = Command()
        crawler = Mock()
        crawler.fetch.side_effect = [
            [
                CrawledNews(
                    title="이미 저장된 뉴스",
                    content="본문",
                    source_url="https://example.com/1",
                    created_at=date(2026, 4, 16),
                ),
            ],
            [
                CrawledNews(
                    title="다음 페이지 뉴스",
                    content="본문",
                    source_url="https://example.com/2",
                    created_at=date(2026, 4, 15),
                ),
            ],
        ]

        with patch.object(command, "_store_entries", return_value=0):
            pages_processed, created, total_entries = command._bootstrap_fetch(
                crawler=crawler,
                max_pages=2,
                continue_existing=True,
            )

        self.assertEqual(pages_processed, 2)
        self.assertEqual(created, 0)
        self.assertEqual(total_entries, 2)

    def test_bootstrap_writes_page_progress(self) -> None:
        command = Command()
        stdout = StringIO()
        command.stdout = OutputWrapper(stdout)
        crawler = Mock()
        crawler.fetch.return_value = [
            CrawledNews(
                title="진행 확인 뉴스",
                content="본문",
                source_url="https://example.com/progress",
                created_at=date(2026, 4, 16),
            ),
        ]

        with patch.object(command, "_store_entries", return_value=1):
            command._bootstrap_fetch(crawler=crawler, max_pages=1)

        output = stdout.getvalue()
        self.assertIn("백필 진행: 1/1페이지 수집 시작", output)
        self.assertIn("백필 진행: 1페이지 완료", output)

    def test_bootstrap_stops_when_same_page_fingerprint_repeats(self) -> None:
        command = Command()
        crawler = Mock()
        repeated_entries = [
            CrawledNews(
                title="반복 뉴스",
                content="같은 본문",
                source_url="https://example.com/volatile-1",
                created_at=date(2026, 4, 16),
            ),
        ]
        crawler.fetch.side_effect = [
            repeated_entries,
            [
                CrawledNews(
                    title="반복 뉴스",
                    content="같은 본문",
                    source_url="https://example.com/volatile-2",
                    created_at=date(2026, 4, 16),
                ),
            ],
        ]

        with patch.object(command, "_store_entries", return_value=1):
            with self.assertRaisesRegex(ValueError, "동일한 뉴스 목록이 반복"):
                command._bootstrap_fetch(
                    crawler=crawler,
                    max_pages=2,
                    continue_existing=True,
                )

    def test_builds_distinct_synthetic_urls_for_same_title_and_date(self) -> None:
        crawler = BokjiroNewsCrawler(limit=10)

        entries = crawler._extract_entries(SAMPLE_DUPLICATE_TITLE_HTML)

        self.assertEqual(len(entries), 2)
        self.assertNotEqual(entries[0].source_url, entries[1].source_url)
        self.assertIn("첫 번째 기사", entries[0].content)
        self.assertIn("두 번째 기사", entries[1].content)
