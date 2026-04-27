import html
import hashlib
from importlib import import_module
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from typing import List
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from news.models import News, NewsFetchStatus


logger = logging.getLogger(__name__)
DATE_PATTERN = re.compile(r"(20\d{2})[./-](\d{2})[./-](\d{2})")


@dataclass
class CrawledNews:
    title: str
    content: str
    source_url: str
    created_at: date


@dataclass
class _ParsedNewsItem:
    title_parts: list[str]
    content_parts: list[str]
    date_parts: list[str]
    href: str = ""


class _BokjiroListPageParser(HTMLParser):
    def __init__(self) -> None:
        """목록 페이지에서 기사 단위를 모으기 위한 파서를 초기화한다."""
        super().__init__()
        self.items: list[_ParsedNewsItem] = []
        self._current_item: _ParsedNewsItem | None = None
        self._item_depth = 0
        self._title_depth = 0
        self._content_depth = 0
        self._date_depth = 0
        self._tag_stack: list[tuple[bool, bool, bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """시작 태그를 만났을 때 현재 기사와 필드 상태를 갱신한다."""
        attrs_dict = {key: value or "" for key, value in attrs}
        classes = set(attrs_dict.get("class", "").split())

        if self._current_item is None and "news-item" not in classes:
            return

        if self._current_item is None:
            self._current_item = _ParsedNewsItem([], [], [])

        self._item_depth += 1

        started_title = "news-title" in classes
        started_content = "news-txt" in classes
        started_date = "news-date" in classes

        if started_title:
            self._title_depth += 1
        if started_content:
            self._content_depth += 1
        if started_date:
            self._date_depth += 1

        self._tag_stack.append((started_title, started_content, started_date))

        if tag == "a" and self._active_field == "title":
            href = attrs_dict.get("href", "").strip()
            if href and not self._current_item.href:
                self._current_item.href = href

    def handle_endtag(self, tag: str) -> None:
        """끝 태그를 만났을 때 수집 범위를 정리하고 기사 하나를 확정한다."""
        if self._current_item is None or not self._tag_stack:
            return

        started_title, started_content, started_date = self._tag_stack.pop()
        if started_title:
            self._title_depth -= 1
        if started_content:
            self._content_depth -= 1
        if started_date:
            self._date_depth -= 1

        self._item_depth -= 1
        if self._item_depth == 0 and self._current_item is not None:
            self.items.append(self._current_item)
            self._current_item = None

    def handle_data(self, data: str) -> None:
        """현재 읽는 필드가 제목/본문/날짜 중 무엇인지에 따라 텍스트를 저장한다."""
        if self._current_item is None:
            return

        active_field = self._active_field
        if active_field == "title":
            self._current_item.title_parts.append(data)
        elif active_field == "content":
            self._current_item.content_parts.append(data)
        elif active_field == "date":
            self._current_item.date_parts.append(data)

    @property
    def _active_field(self) -> str | None:
        """지금 파서가 어떤 필드의 텍스트를 읽는 중인지 반환한다."""
        if self._title_depth > 0:
            return "title"
        if self._content_depth > 0:
            return "content"
        if self._date_depth > 0:
            return "date"
        return None


class BokjiroNewsCrawler:
    BASE_URL = "https://www.bokjiro.go.kr/ssis-tbu/twatxa/wlfarePr/selectWlfareList.do"
    SOURCE_BROWSER = "browser"
    SOURCE_HTTP = "http"
    RENDERED_LIST_SELECTOR = ".news-item"

    def __init__(
        self,
        limit: int = 20,
        user_agent: str | None = None,
        source: str = SOURCE_BROWSER,
    ) -> None:
        """수집 개수 제한과 요청 헤더 정보를 준비한다."""
        self.limit = limit
        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"
        )
        self.source = source

    def fetch(self, page_index: int = 1) -> List[CrawledNews]:
        """복지로 목록 페이지 1개를 요청하고 기사 목록으로 변환한다."""
        if self.source == self.SOURCE_BROWSER:
            html_text = self._request_rendered_list_page(page_index)
        elif self.source == self.SOURCE_HTTP:
            html_text = self._request_list_page(page_index)
        else:
            raise ValueError(f"지원하지 않는 뉴스 수집 방식입니다: {self.source}")

        entries = self._extract_entries(html_text)
        return entries[: self.limit]

    def _request_rendered_list_page(self, page_index: int) -> str:
        """Playwright로 JS 렌더링이 끝난 목록 DOM을 가져온다."""
        try:
            playwright_sync_api = import_module("playwright.sync_api")
        except ImportError as exc:  # pragma: no cover - 환경 의존 오류 메시지
            raise RuntimeError(
                "Playwright가 설치되어 있지 않습니다. "
                "`pip install playwright` 후 `python -m playwright install --with-deps chromium`을 실행하세요."
            ) from exc

        playwright_error = playwright_sync_api.Error
        playwright_timeout_error = playwright_sync_api.TimeoutError
        sync_playwright = playwright_sync_api.sync_playwright

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page(user_agent=self.user_agent)
                    page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=30_000)
                    page.wait_for_selector(self.RENDERED_LIST_SELECTOR, timeout=30_000)
                    self._move_to_rendered_page(page, page_index)
                    page.wait_for_selector(self.RENDERED_LIST_SELECTOR, timeout=30_000)
                    return page.content()
                finally:
                    browser.close()
        except playwright_timeout_error as exc:
            raise RuntimeError("복지로 뉴스 목록 렌더링 대기 시간이 초과되었습니다.") from exc
        except playwright_error as exc:
            raise RuntimeError(
                "Playwright 실행 중 오류가 발생했습니다. "
                "브라우저가 설치되어 있는지 확인하려면 "
                "`python -m playwright install --with-deps chromium`을 실행하세요."
            ) from exc

    def _move_to_rendered_page(self, page, page_index: int) -> None:
        """렌더링된 페이지 안에서 요청한 목록 페이지로 이동한다."""
        if page_index <= 1:
            return

        page_number = str(page_index)
        candidates = [
            f'a:has-text("{page_number}")',
            f'button:has-text("{page_number}")',
            f'[role="button"]:has-text("{page_number}")',
            f'text="{page_number}"',
        ]
        first_item_before = page.locator(self.RENDERED_LIST_SELECTOR).first.inner_text(
            timeout=5_000,
        )

        for selector in candidates:
            locator = page.locator(selector)
            if locator.count() == 0:
                continue
            locator.first.click()
            page.wait_for_function(
                """
                ([itemSelector, previousText]) => {
                    const item = document.querySelector(itemSelector);
                    return item && item.innerText !== previousText;
                }
                """,
                [self.RENDERED_LIST_SELECTOR, first_item_before],
                timeout=10_000,
            )
            return

        raise RuntimeError(f"복지로 뉴스 {page_index}페이지 버튼을 찾지 못했습니다.")

    def _request_list_page(self, page_index: int) -> str:
        """pageIndex 값을 넣어 복지로 뉴스 목록 HTML을 가져온다."""
        payload = urlencode({"pageIndex": page_index}).encode("utf-8")
        request = Request(
            self.BASE_URL,
            data=payload,
            headers={
                "User-Agent": self.user_agent,
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": self.BASE_URL,
            },
        )
        with urlopen(request, timeout=20) as response:  # noqa: S310 (controlled URL)
            return response.read().decode("utf-8", errors="ignore")

    def _extract_entries(self, html_text: str) -> List[CrawledNews]:
        """목록 HTML에서 기사 제목, 본문, 날짜, source_url 을 추출한다."""
        parser = _BokjiroListPageParser()
        parser.feed(html_text)
        entries: List[CrawledNews] = []

        for item in parser.items:
            title_text = self._clean_text(" ".join(item.title_parts))
            if not title_text:
                continue

            created_at = self._parse_date_text(" ".join(item.date_parts))
            if not created_at:
                continue

            content_text = self._clean_text(" ".join(item.content_parts))
            source_url = self._build_source_url(
                title=title_text,
                content=content_text or title_text,
                created_at=created_at,
                href=item.href,
            )

            entries.append(
                CrawledNews(
                    title=title_text,
                    content=content_text or title_text,
                    source_url=source_url,
                    created_at=created_at,
                )
            )
            if len(entries) >= self.limit:
                break

        return entries

    def _clean_text(self, raw_html: str) -> str:
        """HTML 태그와 불필요한 공백을 제거해 읽기 쉬운 텍스트로 만든다."""
        text = re.sub(r"<[^>]+>", " ", raw_html)
        text = html.unescape(text)
        return " ".join(text.split())

    def _build_source_url(
        self,
        title: str,
        content: str,
        created_at: date,
        href: str,
    ) -> str:
        """기사 href 가 있으면 실제 링크를, 없으면 중복 방지용 대체 URL을 만든다."""
        normalized_href = href.strip()
        if normalized_href and "javascript" not in normalized_href.lower():
            return urljoin(self.BASE_URL, normalized_href)

        synthetic_key = hashlib.sha256(
            f"{created_at.isoformat()}::{title}::{content}".encode("utf-8"),
        ).hexdigest()[:16]
        query_string = urlencode(
            {
                "news_date": created_at.isoformat(),
                "news_key": synthetic_key,
            },
        )
        return f"{self.BASE_URL}?{query_string}"

    def _parse_date_text(self, raw_text: str) -> date | None:
        """텍스트 안의 날짜 문자열을 찾아 date 객체로 바꾼다."""
        match = DATE_PATTERN.search(raw_text)
        if not match:
            return None
        try:
            return datetime.strptime("-".join(match.groups()), "%Y-%m-%d").date()
        except ValueError:
            return None


class Command(BaseCommand):
    help = "복지로 뉴스 목록을 크롤링하여 저장합니다."
    failure_message = "금일 뉴스를 확인할 수 없습니다"
    MODE_INCREMENTAL = "incremental"
    MODE_BOOTSTRAP = "bootstrap"

    def add_arguments(self, parser) -> None:
        """명령행에서 사용할 옵션들을 등록한다."""
        parser.add_argument("--limit", type=int, default=20, help="저장할 최대 뉴스 수")
        parser.add_argument(
            "--mode",
            choices=[self.MODE_INCREMENTAL, self.MODE_BOOTSTRAP],
            default=self.MODE_INCREMENTAL,
            help="incremental은 1페이지 증분 수집, bootstrap은 전체 페이지 초기 적재",
        )
        parser.add_argument(
            "--max-pages",
            type=int,
            default=100,
            help="bootstrap 모드에서 순회할 최대 페이지 수",
        )
        parser.add_argument(
            "--source",
            choices=[BokjiroNewsCrawler.SOURCE_BROWSER, BokjiroNewsCrawler.SOURCE_HTTP],
            default=BokjiroNewsCrawler.SOURCE_BROWSER,
            help="browser는 Playwright 렌더링 DOM을, http는 기존 직접 요청 HTML을 사용",
        )

    def handle(self, *args, **options):
        """모드에 따라 증분 수집 또는 초기 백필을 실행하고 상태를 기록한다."""
        limit: int = options["limit"]
        mode: str = options["mode"]
        max_pages: int = options["max_pages"]
        source: str = options["source"]
        crawler = BokjiroNewsCrawler(limit=limit, source=source)
        try:
            if mode == self.MODE_BOOTSTRAP:
                pages_processed, created, total_entries = self._bootstrap_fetch(
                    crawler=crawler,
                    max_pages=max_pages,
                )
                if total_entries == 0:
                    raise ValueError("초기 적재를 위한 뉴스가 없습니다.")
                self._mark_status(success=True, message="")
                self.stdout.write(
                    self._success_message(
                        f"초기 적재 완료: {pages_processed}페이지 순회, 뉴스 {created}건 신규 저장 (총 {total_entries}건 확인)"
                    ),
                )
                return

            entries = self._fetch_entries_with_retry(crawler, page_index=1)
            if not entries:
                raise ValueError("수집된 뉴스가 없습니다.")
            created = self._store_entries(entries)
            self._mark_status(success=True, message="")
            self.stdout.write(
                self._success_message(f"뉴스 {created}건 저장 완료 (총 {len(entries)}건)"),
            )
        except Exception as exc:
            try:
                self._mark_status(success=False, message=self.failure_message)
            except Exception:
                logger.exception("뉴스 수집 실패 상태 기록 중 추가 오류가 발생했습니다.")
            raise CommandError(f"뉴스 수집 실패: {exc}") from exc

    def _success_message(self, message: str) -> str:
        """Django 스타일이 있으면 성공 메시지 형식으로 감싸서 돌려준다."""
        success_style = getattr(self.style, "SUCCESS", lambda value: value)
        return success_style(message)

    def _fetch_entries_with_retry(
        self,
        crawler: BokjiroNewsCrawler,
        page_index: int,
    ) -> List[CrawledNews]:
        """일시적인 요청 실패에 대비해 한 페이지 수집을 한 번 더 재시도한다."""
        attempts = 0
        last_error: Exception | None = None

        while attempts < 2:
            try:
                return crawler.fetch(page_index=page_index)
            except Exception as exc:  # pragma: no cover - 네트워크 예외 다양
                attempts += 1
                last_error = exc
                logger.exception("뉴스 수집 실패 (page=%s): %s", page_index, exc)
                if attempts < 2:
                    time.sleep(2)

        if last_error is None:
            raise ValueError("알 수 없는 이유로 뉴스 수집에 실패했습니다.")
        raise last_error

    def _bootstrap_fetch(
        self,
        crawler: BokjiroNewsCrawler,
        max_pages: int,
    ) -> tuple[int, int, int]:
        """초기 적재 모드에서 여러 페이지를 순회하며 누적 저장 결과를 계산한다."""
        pages_processed = 0
        total_created = 0
        total_entries = 0

        for page_index in range(1, max_pages + 1):
            entries = self._fetch_entries_with_retry(crawler, page_index=page_index)
            if not entries:
                break

            created = self._store_entries(entries)
            pages_processed += 1
            total_created += created
            total_entries += len(entries)

            if created == 0:
                break

        return pages_processed, total_created, total_entries

    def _store_entries(self, entries: List[CrawledNews]) -> int:
        """수집한 기사들을 source_url 기준으로 저장하거나 갱신한다."""
        created_count = 0
        for entry in entries:
            _, created = News.objects.update_or_create(
                source_url=entry.source_url,
                defaults={
                    "title": entry.title,
                    "content": entry.content,
                    "created_at": entry.created_at,
                },
            )
            if created:
                created_count += 1
        return created_count

    def _mark_status(self, success: bool, message: str) -> None:
        """오늘 뉴스 수집이 성공했는지 실패했는지 상태 테이블에 남긴다."""
        status = NewsFetchStatus.STATUS_SUCCESS if success else NewsFetchStatus.STATUS_FAILURE
        NewsFetchStatus.objects.update_or_create(
            fetch_date=date.today(),
            defaults={"status": status, "message": message},
        )
