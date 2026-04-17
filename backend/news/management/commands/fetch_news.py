import html
import hashlib
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
        super().__init__()
        self.items: list[_ParsedNewsItem] = []
        self._current_item: _ParsedNewsItem | None = None
        self._item_depth = 0
        self._title_depth = 0
        self._content_depth = 0
        self._date_depth = 0
        self._tag_stack: list[tuple[bool, bool, bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
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
        if self._title_depth > 0:
            return "title"
        if self._content_depth > 0:
            return "content"
        if self._date_depth > 0:
            return "date"
        return None


class BokjiroNewsCrawler:
    BASE_URL = "https://www.bokjiro.go.kr/ssis-tbu/twatxa/wlfarePr/selectWlfareList.do"

    def __init__(self, limit: int = 20, user_agent: str | None = None) -> None:
        self.limit = limit
        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"
        )

    def fetch(self, page_index: int = 1) -> List[CrawledNews]:
        html_text = self._request_list_page(page_index)
        entries = self._extract_entries(html_text)
        return entries[: self.limit]

    def _request_list_page(self, page_index: int) -> str:
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

    def handle(self, *args, **options):
        limit: int = options["limit"]
        mode: str = options["mode"]
        max_pages: int = options["max_pages"]
        crawler = BokjiroNewsCrawler(limit=limit)
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
            self._mark_status(success=False, message=self.failure_message)
            raise CommandError(f"뉴스 수집 실패: {exc}") from exc

    def _success_message(self, message: str) -> str:
        success_style = getattr(self.style, "SUCCESS", lambda value: value)
        return success_style(message)

    def _fetch_entries_with_retry(
        self,
        crawler: BokjiroNewsCrawler,
        page_index: int,
    ) -> List[CrawledNews]:
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
        status = NewsFetchStatus.STATUS_SUCCESS if success else NewsFetchStatus.STATUS_FAILURE
        NewsFetchStatus.objects.update_or_create(
            fetch_date=date.today(),
            defaults={"status": status, "message": message},
        )
