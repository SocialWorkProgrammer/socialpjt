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
    PLAYWRIGHT_TIMEOUT_MS = 10_000
    RENDERED_ITEM_TEXT_TIMEOUT_MS = 5_000
    BLOCKED_RESOURCE_TYPES = ("image", "media", "font")
    BLOCKED_RESOURCE_SUFFIXES = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
    )
    CONTEXT_EXTRA_HTTP_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.bokjiro.go.kr/",
    }
    PAGINATION_CONTAINER_SELECTORS = (
        ".pagination",
        ".paging",
        ".paging-wrap",
        ".paging_wrap",
        ".page-navi",
        ".page_nav",
        ".board-paging",
        ".cl-pageindexer",
        "nav",
        '[class*="pagination"]',
        '[class*="paging"]',
        '[id*="pagination"]',
        '[id*="paging"]',
    )
    PAGINATION_RANGE_SELECTOR = ".cl-pageindexer"
    NEXT_PAGE_RANGE_SELECTORS = (
        '.cl-pageindexer-next[role="button"][data-region="next"]',
        '.cl-pageindexer [data-region="next"][aria-label="다음 페이지 범위"]',
        '[data-region="next"][aria-label="다음 페이지 범위"]',
        'div[role="button"][aria-label="다음 페이지 범위"]',
    )
    PLAYWRIGHT_INSTALL_ERROR_MARKERS = (
        "Executable doesn't exist",
        "playwright install",
        "Looks like Playwright was just installed or updated",
    )
    PLAYWRIGHT_NETWORK_ERROR_MARKERS = (
        "net::ERR_CONNECTION_RESET",
        "net::ERR_CONNECTION_CLOSED",
        "net::ERR_CONNECTION_TIMED_OUT",
        "net::ERR_NAME_NOT_RESOLVED",
        "net::ERR_INTERNET_DISCONNECTED",
    )

    def __init__(
        self,
        limit: int = 20,
        user_agent: str | None = None,
        source: str = SOURCE_BROWSER,
        headless: bool = True,
        slow_mo: int = 0,
    ) -> None:
        """수집 개수 제한과 요청 헤더 정보를 준비한다."""
        self.limit = limit
        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"
        )
        self.source = source
        self.headless = headless
        self.slow_mo = slow_mo

    def fetch(self, page_index: int = 1) -> List[CrawledNews]:
        """복지로 목록 페이지 1개를 요청하고 기사 목록으로 변환한다."""
        if self.source == self.SOURCE_BROWSER:
            return self._fetch_rendered_entries(page_index)
        elif self.source == self.SOURCE_HTTP:
            html_text = self._request_list_page(page_index)
        else:
            raise ValueError(f"지원하지 않는 뉴스 수집 방식입니다: {self.source}")

        entries = self._extract_entries(html_text)
        return entries[: self.limit]

    def _fetch_rendered_entries(self, page_index: int) -> List[CrawledNews]:
        """Playwright로 JS 렌더링이 끝난 뉴스 항목을 화면 텍스트 기준으로 수집한다."""
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
                launch_options: dict[str, bool | int] = {"headless": self.headless}
                if self.slow_mo > 0:
                    launch_options["slow_mo"] = self.slow_mo
                browser = playwright.chromium.launch(**launch_options)
                context = None
                try:
                    context = browser.new_context(
                        user_agent=self.user_agent,
                        locale="ko-KR",
                        timezone_id="Asia/Seoul",
                        extra_http_headers=self.CONTEXT_EXTRA_HTTP_HEADERS,
                        service_workers="block",
                    )
                    context.set_default_timeout(self.PLAYWRIGHT_TIMEOUT_MS)
                    context.set_default_navigation_timeout(self.PLAYWRIGHT_TIMEOUT_MS)
                    page = context.new_page()
                    page.route("**/*", self._route_nonessential_resource)
                    page.set_default_timeout(self.PLAYWRIGHT_TIMEOUT_MS)
                    page.set_default_navigation_timeout(self.PLAYWRIGHT_TIMEOUT_MS)
                    self._goto_rendered_base_page(page)
                    page.wait_for_selector(
                        self.RENDERED_LIST_SELECTOR,
                        timeout=self.PLAYWRIGHT_TIMEOUT_MS,
                    )
                    self._move_to_rendered_page(page, page_index)
                    page.wait_for_selector(
                        self.RENDERED_LIST_SELECTOR,
                        timeout=self.PLAYWRIGHT_TIMEOUT_MS,
                    )
                    return self._extract_rendered_entries_from_page(page)
                finally:
                    if context is not None:
                        context.close()
                    browser.close()
        except playwright_timeout_error as exc:
            raise RuntimeError("복지로 뉴스 목록 렌더링 대기 시간이 초과되었습니다.") from exc
        except playwright_error as exc:
            raise RuntimeError(self._playwright_error_message(str(exc))) from exc

    def _playwright_error_message(self, error_text: str) -> str:
        """Playwright 오류 원인에 맞는 안내 메시지를 만든다."""
        if any(marker in error_text for marker in self.PLAYWRIGHT_INSTALL_ERROR_MARKERS):
            return (
                "Playwright 브라우저가 설치되어 있지 않습니다. "
                "`python -m playwright install --with-deps chromium`을 실행하세요."
            )
        if any(marker in error_text for marker in self.PLAYWRIGHT_NETWORK_ERROR_MARKERS):
            return (
                "복지로 사이트 연결이 중간에 끊겼습니다. "
                "네트워크 상태를 확인한 뒤 같은 명령을 다시 실행하세요. "
                f"원본 오류: {error_text}"
            )
        return f"Playwright 실행 중 오류가 발생했습니다. 원본 오류: {error_text}"

    def _route_nonessential_resource(self, route) -> None:
        """뉴스 목록 렌더링에 불필요한 무거운 정적 리소스를 차단한다."""
        request = route.request
        url = request.url.split("?", 1)[0].lower()
        if request.resource_type in self.BLOCKED_RESOURCE_TYPES or url.endswith(
            self.BLOCKED_RESOURCE_SUFFIXES,
        ):
            route.abort()
            return
        route.continue_()

    def _goto_rendered_base_page(self, page) -> None:
        """복지로 첫 화면 진입을 짧은 대기 안에서 시도한다."""
        page.goto(
            self.BASE_URL,
            wait_until="domcontentloaded",
            timeout=self.PLAYWRIGHT_TIMEOUT_MS,
        )

    def _extract_rendered_entries_from_page(self, page) -> List[CrawledNews]:
        """Playwright locator로 렌더링된 뉴스 항목의 화면 텍스트를 읽는다."""
        items = page.locator(self.RENDERED_LIST_SELECTOR)
        entries: List[CrawledNews] = []

        for index in range(items.count()):
            item = items.nth(index)
            item_text = self._clean_text(
                item.inner_text(timeout=self.RENDERED_ITEM_TEXT_TIMEOUT_MS),
            )
            href = self._first_href_from_rendered_item(item)
            entry = self._extract_rendered_entry(item=item, item_text=item_text, href=href)
            if entry is None:
                continue

            entries.append(entry)
            if len(entries) >= self.limit:
                break

        return entries

    def _first_href_from_rendered_item(self, item) -> str:
        """렌더링된 뉴스 항목에서 첫 번째 링크 href를 가져온다."""
        links = item.locator("a[href]")
        if links.count() == 0:
            return ""
        return links.first.get_attribute("href") or ""

    def _extract_rendered_entry(self, item, item_text: str, href: str) -> CrawledNews | None:
        """렌더링된 뉴스 항목 1개를 CrawledNews로 변환한다."""
        title_text = self._text_from_rendered_child(item, ".news-title")
        content_text = self._text_from_rendered_child(item, ".news-txt")
        date_text = self._text_from_rendered_child(item, ".news-date")

        fallback_title, fallback_content, fallback_date = self._split_rendered_item_text(
            item_text,
        )
        title_text = title_text or fallback_title
        content_text = content_text or fallback_content or title_text
        created_at = self._parse_date_text(date_text or fallback_date or item_text)
        if not title_text or not created_at:
            return None

        source_url = self._build_source_url(
            title=title_text,
            content=content_text,
            created_at=created_at,
            href=href,
        )
        return CrawledNews(
            title=title_text,
            content=content_text,
            source_url=source_url,
            created_at=created_at,
        )

    def _text_from_rendered_child(self, item, selector: str) -> str:
        """하위 selector 텍스트를 읽되 없으면 빈 문자열을 반환한다."""
        child = item.locator(selector)
        if child.count() == 0:
            return ""
        return self._clean_text(
            child.first.inner_text(timeout=self.RENDERED_ITEM_TEXT_TIMEOUT_MS),
        )

    def _split_rendered_item_text(self, item_text: str) -> tuple[str, str, str]:
        """클래스 기반 추출이 실패했을 때 화면 텍스트에서 제목/본문/날짜를 나눈다."""
        lines = [line.strip() for line in item_text.splitlines() if line.strip()]
        date_text = ""
        content_lines: list[str] = []
        title_text = ""

        for line in lines:
            if not date_text and DATE_PATTERN.search(line):
                date_text = line
                continue
            if not title_text:
                title_text = line
                continue
            content_lines.append(line)

        return title_text, " ".join(content_lines), date_text

    def _move_to_rendered_page(self, page, page_index: int) -> None:
        """렌더링된 페이지 안에서 요청한 목록 페이지로 이동한다."""
        if page_index <= 1:
            return

        page_number = str(page_index)
        previous_fingerprint = self._rendered_items_text_fingerprint(page)
        max_range_moves = (page_index - 1) // 10 + 1

        for _ in range(max_range_moves):
            if self._click_rendered_page_button(page, page_number, previous_fingerprint):
                return
            if not self._click_next_page_range(page):
                break

        raise RuntimeError(
            f"복지로 뉴스 {page_index}페이지 버튼을 페이지네이션 영역에서 찾지 못했습니다. "
            "복지로 페이지네이션 HTML 구조 확인이 필요합니다."
        )

    def _click_rendered_page_button(
        self,
        page,
        page_number: str,
        previous_fingerprint: list[str],
    ) -> bool:
        """현재 페이지네이션 범위에서 요청한 페이지 번호를 클릭한다."""
        for selector in self._pagination_button_selectors(page_number):
            locator = page.locator(selector)
            if locator.count() == 0:
                continue
            locator.first.click(timeout=self.PLAYWRIGHT_TIMEOUT_MS)
            page.wait_for_function(
                r"""
                ([itemSelector, previousFingerprint]) => {
                    const normalize = (value) => value.replace(/\s+/g, " ").trim();
                    const currentFingerprint = Array.from(
                        document.querySelectorAll(itemSelector),
                    )
                        .map((item) => normalize(item.innerText))
                        .filter(Boolean);
                    return currentFingerprint.length > 0
                        && JSON.stringify(currentFingerprint) !== JSON.stringify(previousFingerprint);
                }
                """,
                arg=[self.RENDERED_LIST_SELECTOR, previous_fingerprint],
                timeout=self.PLAYWRIGHT_TIMEOUT_MS,
            )
            return True
        return False

    def _click_next_page_range(self, page) -> bool:
        """복지로 페이지네이션의 다음 페이지 범위 버튼을 클릭한다."""
        previous_fingerprint = self._pagination_range_text_fingerprint(page)
        for selector in self.NEXT_PAGE_RANGE_SELECTORS:
            locator = page.locator(selector)
            if locator.count() == 0:
                continue
            locator.first.click(timeout=self.PLAYWRIGHT_TIMEOUT_MS)
            page.wait_for_function(
                r"""
                ([paginationSelector, previousFingerprint]) => {
                    const normalize = (value) => value.replace(/\s+/g, " ").trim();
                    const currentFingerprint = Array.from(
                        document.querySelectorAll(paginationSelector),
                    )
                        .map((item) => normalize(item.innerText))
                        .filter(Boolean);
                    return currentFingerprint.length > 0
                        && JSON.stringify(currentFingerprint) !== JSON.stringify(previousFingerprint);
                }
                """,
                arg=[self.PAGINATION_RANGE_SELECTOR, previous_fingerprint],
                timeout=self.PLAYWRIGHT_TIMEOUT_MS,
            )
            return True
        return False

    def _pagination_button_selectors(self, page_number: str) -> list[str]:
        """페이지네이션 영역 안에서만 특정 페이지 버튼 후보 selector를 만든다."""
        target_selectors = [
            f'a:text-is("{page_number}")',
            f'button:text-is("{page_number}")',
            f'[role="link"]:text-is("{page_number}")',
            f'[role="button"]:text-is("{page_number}")',
            f'[aria-label="{page_number}"]',
            f'[aria-label="Page {page_number}"]',
            f'[aria-label="페이지 {page_number}"]',
            f'[title="{page_number}"]',
            f'[data-page="{page_number}"]',
            f':text-is("{page_number}")',
        ]
        return [
            f"{container_selector} {target_selector}"
            for container_selector in self.PAGINATION_CONTAINER_SELECTORS
            for target_selector in target_selectors
        ]

    def _rendered_items_text_fingerprint(self, page) -> list[str]:
        """현재 렌더링된 뉴스 목록의 텍스트 fingerprint를 만든다."""
        fingerprint: list[str] = []
        for text in page.locator(self.RENDERED_LIST_SELECTOR).all_inner_texts():
            cleaned_text = self._clean_text(text)
            if cleaned_text:
                fingerprint.append(cleaned_text)
        return fingerprint

    def _pagination_range_text_fingerprint(self, page) -> list[str]:
        """현재 페이지네이션 영역의 텍스트 fingerprint를 만든다."""
        fingerprint: list[str] = []
        for text in page.locator(self.PAGINATION_RANGE_SELECTOR).all_inner_texts():
            cleaned_text = self._clean_text(text)
            if cleaned_text:
                fingerprint.append(cleaned_text)
        return fingerprint

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
    MAX_FETCH_ATTEMPTS = 3
    FETCH_RETRY_DELAY_SECONDS = 1

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
        parser.add_argument(
            "--continue-existing",
            action="store_true",
            help="bootstrap 중 이미 저장된 페이지만 나와도 max-pages까지 계속 순회",
        )
        parser.add_argument(
            "--headed",
            action="store_true",
            help="Playwright 브라우저 창을 표시하여 수집 진행 상황을 직접 확인",
        )
        parser.add_argument(
            "--slow-mo",
            type=int,
            default=0,
            help="headed 디버깅 시 Playwright 동작을 지정한 밀리초만큼 천천히 실행",
        )

    def handle(self, *args, **options):
        """모드에 따라 증분 수집 또는 초기 백필을 실행하고 상태를 기록한다."""
        limit: int = options["limit"]
        mode: str = options["mode"]
        max_pages: int = options["max_pages"]
        source: str = options["source"]
        continue_existing: bool = options["continue_existing"]
        headed: bool = options["headed"]
        slow_mo: int = options["slow_mo"]
        if slow_mo < 0:
            raise CommandError("--slow-mo 값은 0 이상이어야 합니다.")

        crawler = BokjiroNewsCrawler(
            limit=limit,
            source=source,
            headless=not headed,
            slow_mo=slow_mo,
        )
        try:
            if mode == self.MODE_BOOTSTRAP:
                pages_processed, created, total_entries = self._bootstrap_fetch(
                    crawler=crawler,
                    max_pages=max_pages,
                    continue_existing=continue_existing,
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

            self.stdout.write("증분 수집 진행: 1페이지 수집 시작")
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
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_FETCH_ATTEMPTS + 1):
            try:
                return crawler.fetch(page_index=page_index)
            except Exception as exc:  # pragma: no cover - 네트워크 예외 다양
                last_error = exc
                logger.exception(
                    "뉴스 수집 실패 (page=%s, attempt=%s/%s): %s",
                    page_index,
                    attempt,
                    self.MAX_FETCH_ATTEMPTS,
                    exc,
                )
                if not self._should_retry_fetch_error(exc):
                    raise
                if attempt < self.MAX_FETCH_ATTEMPTS:
                    time.sleep(self.FETCH_RETRY_DELAY_SECONDS)

        if last_error is None:
            raise ValueError("알 수 없는 이유로 뉴스 수집에 실패했습니다.")
        raise last_error

    def _should_retry_fetch_error(self, exc: Exception) -> bool:
        """일시적인 네트워크/렌더링 오류만 재시도 대상으로 판단한다."""
        message = str(exc)
        non_retryable_markers = (
            "Playwright가 설치되어 있지 않습니다",
            "Playwright 브라우저가 설치되어 있지 않습니다",
            "지원하지 않는 뉴스 수집 방식입니다",
        )
        if any(marker in message for marker in non_retryable_markers):
            return False
        retryable_markers = BokjiroNewsCrawler.PLAYWRIGHT_NETWORK_ERROR_MARKERS + (
            "Timeout",
            "대기 시간이 초과",
            "렌더링 대기 시간이 초과",
        )
        return any(marker in message for marker in retryable_markers)

    def _bootstrap_fetch(
        self,
        crawler: BokjiroNewsCrawler,
        max_pages: int,
        continue_existing: bool = False,
    ) -> tuple[int, int, int]:
        """초기 적재 모드에서 여러 페이지를 순회하며 누적 저장 결과를 계산한다."""
        pages_processed = 0
        total_created = 0
        total_entries = 0
        seen_page_fingerprints: set[tuple[tuple[str, str, str], ...]] = set()

        for page_index in range(1, max_pages + 1):
            self.stdout.write(f"백필 진행: {page_index}/{max_pages}페이지 수집 시작")
            entries = self._fetch_entries_with_retry(crawler, page_index=page_index)
            if not entries:
                self.stdout.write(
                    f"백필 중단: {page_index}페이지에서 수집된 뉴스가 없습니다.",
                )
                break

            page_fingerprint = self._entries_fingerprint(entries)
            if page_fingerprint in seen_page_fingerprints:
                raise ValueError(
                    f"{page_index}페이지에서 이전 페이지와 동일한 뉴스 목록이 반복되었습니다. "
                    "페이지네이션 이동 실패 가능성이 있어 저장을 중단합니다."
                )
            seen_page_fingerprints.add(page_fingerprint)

            created = self._store_entries(entries)
            pages_processed += 1
            total_created += created
            total_entries += len(entries)
            self.stdout.write(
                "백필 진행: "
                f"{page_index}페이지 완료, "
                f"확인 {len(entries)}건, 신규 {created}건, "
                f"누적 확인 {total_entries}건, 누적 신규 {total_created}건",
            )

            if created == 0 and not continue_existing:
                self.stdout.write(
                    "백필 중단: 신규 저장 뉴스가 없어 이후 페이지 순회를 멈춥니다. "
                    "계속 확인하려면 --continue-existing 옵션을 사용하세요.",
                )
                break

        return pages_processed, total_created, total_entries

    def _entries_fingerprint(
        self,
        entries: List[CrawledNews],
    ) -> tuple[tuple[str, str, str], ...]:
        """source_url 변동과 무관하게 페이지 내용 동일성을 판단할 fingerprint를 만든다."""
        return tuple(
            (
                entry.created_at.isoformat(),
                " ".join(entry.title.split()),
                " ".join(entry.content.split()),
            )
            for entry in entries
        )

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
