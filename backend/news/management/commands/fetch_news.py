import html
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import List
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from news.models import News, NewsFetchStatus


logger = logging.getLogger(__name__)


@dataclass
class CrawledNews:
    title: str
    content: str
    source_url: str
    created_at: date


class BokjiroNewsCrawler:
    BASE_URL = "https://www.bokjiro.go.kr/ssis-tbu/twatxa/wlfarePr/selectWlfareList.do"

    def __init__(
        self,
        limit: int = 20,
        user_agent: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.limit = limit
        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"
        )
        self.api_key = api_key

    def fetch(self) -> List[CrawledNews]:
        html_text = self._request_list_page()
        entries = self._extract_entries(html_text)
        return entries[: self.limit]

    def _request_list_page(self) -> str:
        payload = urlencode({"pageIndex": 1}).encode("utf-8")
        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": self.BASE_URL,
        }
        if self.api_key:
            headers["X-API-KEY"] = self.api_key

        request = Request(
            self.BASE_URL,
            data=payload,
            headers=headers,
        )
        with urlopen(request, timeout=20) as response:  # noqa: S310 (controlled URL)
            return response.read().decode("utf-8", errors="ignore")

    def _extract_entries(self, html_text: str) -> List[CrawledNews]:
        pattern = re.compile(
            r"<a[^>]+href=\"(?P<href>[^\"]+)\"[^>]*>(?P<title>.*?)</a>",
            re.IGNORECASE | re.DOTALL,
        )
        date_pattern = re.compile(r"(20\d{2})[./-](\d{2})[./-](\d{2})")
        entries: List[CrawledNews] = []

        for match in pattern.finditer(html_text):
            href = match.group("href")
            if not href or "javascript" in href.lower():
                continue
            title_text = self._clean_text(match.group("title"))
            if not title_text:
                continue

            context_window = html_text[max(0, match.start() - 300) : match.end() + 300]
            date_match = date_pattern.search(context_window)
            if not date_match:
                continue
            created_at = self._safe_parse_date(date_match)
            if not created_at:
                continue

            content_text = self._guess_content(context_window)
            source_url = urljoin(self.BASE_URL, href)

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

    def _guess_content(self, context: str) -> str:
        snippet = re.sub(r"<[^>]+>", " ", context)
        snippet = html.unescape(snippet)
        snippet = " ".join(snippet.split())
        return snippet[:500]

    def _safe_parse_date(self, match: re.Match[str]) -> date | None:
        try:
            return datetime.strptime("-".join(match.groups()), "%Y-%m-%d").date()
        except ValueError:
            return None


class Command(BaseCommand):
    help = "복지로 뉴스 목록을 크롤링하여 저장합니다."
    failure_message = "금일 뉴스를 확인할 수 없습니다"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--limit", type=int, default=20, help="저장할 최대 뉴스 수")

    def handle(self, *args, **options):
        limit: int = options["limit"]
        api_key = getattr(settings, "PUBLIC_API_KEY", "") or None
        crawler = BokjiroNewsCrawler(limit=limit, api_key=api_key)
        attempts = 0
        last_error: Exception | None = None

        while attempts < 2:
            try:
                entries = crawler.fetch()
                if not entries:
                    raise ValueError("수집된 뉴스가 없습니다.")
                created = self._store_entries(entries)
                self._mark_status(success=True, message="")
                self.stdout.write(
                    self.style.SUCCESS(  # type: ignore[attr-defined]
                        f"뉴스 {created}건 저장 완료 (총 {len(entries)}건)"
                    ),
                )
                return
            except Exception as exc:  # pragma: no cover - 네트워크 예외 다양
                attempts += 1
                last_error = exc
                logger.exception("뉴스 수집 실패: %s", exc)
                if attempts < 2:
                    time.sleep(2)

        self._mark_status(success=False, message=self.failure_message)
        raise CommandError(f"뉴스 수집 실패: {last_error}")

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
