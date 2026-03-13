import json
import logging
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from services.models import ServiceFetchStatus, SocialService


logger = logging.getLogger(__name__)


class ApiClient:
    def get(self, base_url: str, path: str, params: dict[str, Any]) -> Any:
        query = urlencode(params, doseq=True)
        url = f"{base_url}{path}?{query}"
        with urlopen(url, timeout=30) as response:  # noqa: S310
            payload = response.read().decode("utf-8", errors="ignore")
        payload = payload.strip()
        if payload.startswith("{"):
            return json.loads(payload)
        return ET.fromstring(payload)


def _text(node: ET.Element, key: str) -> str:
    value = node.findtext(key)
    return value.strip() if value else ""


def _parse_date(raw: str) -> date | None:
    if not raw:
        return None
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _parse_int(raw: Any) -> int | None:
    try:
        if raw is None or raw == "":
            return None
        return int(raw)
    except (TypeError, ValueError):
        return None


def _to_bool(raw: str) -> bool | None:
    if raw == "Y":
        return True
    if raw == "N":
        return False
    return None


def _as_list(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


class Command(BaseCommand):
    help = "3종 공공데이터 API를 수집하여 사회서비스 정보를 저장합니다."
    failure_message = "금일 사회서비스 정보를 확인할 수 없습니다"

    NATIONAL_BASE = "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001"
    LOCAL_BASE = "https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations"
    ODCLOUD_BASE = "https://api.odcloud.kr/api/15083323/v1/uddi:3929b807-3420-44d7-a851-cc741fce65a1"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--max-pages", type=int, default=5, help="소스별 최대 페이지")
        parser.add_argument("--num-of-rows", type=int, default=100, help="페이지당 수집 건수")

    def handle(self, *args, **options):
        api_key = getattr(settings, "SOCIAL_SERVICE_API_KEY", "")
        if not api_key:
            raise CommandError("SOCIAL_SERVICE_API_KEY가 설정되지 않았습니다.")

        client = ApiClient()
        max_pages: int = options["max_pages"]
        num_of_rows: int = options["num_of_rows"]
        failures: list[str] = []

        sources = [
            (SocialService.SOURCE_NATIONAL, self._fetch_national),
            (SocialService.SOURCE_LOCAL, self._fetch_local),
            (SocialService.SOURCE_ODCLOUD, self._fetch_odcloud),
        ]

        for source, fetcher in sources:
            attempts = 0
            last_error: Exception | None = None
            while attempts < 2:
                try:
                    count = fetcher(client, api_key, max_pages, num_of_rows)
                    self._mark_status(source=source, success=True, message="")
                    self.stdout.write(
                        self.style.SUCCESS(  # type: ignore[attr-defined]
                            f"[{source}] {count}건 저장/갱신 완료"
                        ),
                    )
                    break
                except Exception as exc:  # pragma: no cover
                    attempts += 1
                    last_error = exc
                    logger.exception("[%s] 수집 실패: %s", source, exc)
                    if attempts < 2:
                        time.sleep(2)
            if last_error and attempts >= 2:
                self._mark_status(source=source, success=False, message=self.failure_message)
                failures.append(f"{source}: {last_error}")

        if failures:
            raise CommandError("; ".join(failures))

    def _fetch_national(
        self,
        client: ApiClient,
        api_key: str,
        max_pages: int,
        num_of_rows: int,
    ) -> int:
        saved_count = 0
        total_count = None
        for page_no in range(1, max_pages + 1):
            root = client.get(
                self.NATIONAL_BASE,
                "/NationalWelfarelistV001",
                {
                    "serviceKey": api_key,
                    "callTp": "L",
                    "pageNo": page_no,
                    "numOfRows": num_of_rows,
                    "orderBy": "date",
                },
            )
            if not isinstance(root, ET.Element):
                raise ValueError("중앙부처 목록 응답 형식이 XML이 아닙니다.")

            if total_count is None:
                total_count = _parse_int(root.findtext("totalCount"))

            items = root.findall("servList")
            if not items:
                break

            for item in items:
                external_id = _text(item, "servId")
                if not external_id:
                    continue
                defaults = {
                    "source": SocialService.SOURCE_NATIONAL,
                    "title": _text(item, "servNm"),
                    "summary": _text(item, "servDgst"),
                    "detail_url": _text(item, "servDtlLink"),
                    "ministry": _text(item, "jurMnofNm"),
                    "organization": _text(item, "jurOrgNm"),
                    "support_cycle": _text(item, "sprtCycNm"),
                    "support_type": _text(item, "srvPvsnNm"),
                    "life_codes": _text(item, "lifeArray"),
                    "target_codes": _text(item, "trgterIndvdlArray"),
                    "theme_codes": _text(item, "intrsThemaArray"),
                    "online_applicable": _to_bool(_text(item, "onapPsbltYn")),
                    "view_count": _parse_int(_text(item, "inqNum")),
                    "first_registered_at": _parse_date(_text(item, "svcfrstRegTs")),
                }
                SocialService.objects.update_or_create(
                    source=SocialService.SOURCE_NATIONAL,
                    external_id=external_id,
                    defaults=defaults,
                )
                saved_count += 1

                detail_root = client.get(
                    self.NATIONAL_BASE,
                    "/NationalWelfaredetailedV001",
                    {
                        "serviceKey": api_key,
                        "callTp": "D",
                        "servId": external_id,
                    },
                )
                if isinstance(detail_root, ET.Element):
                    self._merge_national_detail(external_id, detail_root)
                time.sleep(0.1)

            if total_count is not None and page_no * num_of_rows >= total_count:
                break

        return saved_count

    def _merge_national_detail(self, external_id: str, root: ET.Element) -> None:
        service = SocialService.objects.filter(
            source=SocialService.SOURCE_NATIONAL,
            external_id=external_id,
        ).first()
        if not service:
            return

        service.target_detail = _text(root, "tgtrDtlCn")
        service.selection_criteria = _text(root, "slctCritCn")
        service.benefit_detail = _text(root, "alwServCn")
        service.welfare_outline = _text(root, "wlfareInfoOutlCn")
        service.base_year = _parse_int(_text(root, "crtrYr"))
        service.contact = _text(root, "rprsCtadr")
        service.apply_method_detail = self._flatten_details(root.findall("applmetList"))
        service.contact_list = self._parse_servse_list(root.findall("inqplCtadrList"))
        service.homepage_list = self._parse_servse_list(root.findall("inqplHmpgReldList"))
        service.form_list = self._parse_servse_list(root.findall("basfrmList"))
        service.law_list = [
            {
                "servSeCode": _text(node, "servSeCode"),
                "servSeDetailNm": _text(node, "servSeDetailNm"),
            }
            for node in root.findall("baslawList")
        ]
        service.save()

    def _fetch_local(
        self,
        client: ApiClient,
        api_key: str,
        max_pages: int,
        num_of_rows: int,
    ) -> int:
        saved_count = 0
        total_count = None
        for page_no in range(1, max_pages + 1):
            payload = client.get(
                self.LOCAL_BASE,
                "/LcgvWelfarelist",
                {
                    "serviceKey": api_key,
                    "pageNo": page_no,
                    "numOfRows": num_of_rows,
                },
            )
            if isinstance(payload, dict):
                if total_count is None:
                    total_count = _parse_int(payload.get("totalCount"))
                items = _as_list(payload.get("servList"))
            elif isinstance(payload, ET.Element):
                if total_count is None:
                    total_count = _parse_int(payload.findtext("totalCount"))
                items = [
                    {
                        "servId": _text(node, "servId"),
                        "servNm": _text(node, "servNm"),
                        "servDgst": _text(node, "servDgst"),
                        "servDtlLink": _text(node, "servDtlLink"),
                        "bizChrDeptNm": _text(node, "bizChrDeptNm"),
                        "ctpvNm": _text(node, "ctpvNm"),
                        "sggNm": _text(node, "sggNm"),
                        "sprtCycNm": _text(node, "sprtCycNm"),
                        "srvPvsnNm": _text(node, "srvPvsnNm"),
                        "aplyMtdNm": _text(node, "aplyMtdNm"),
                        "lifeNmArray": _text(node, "lifeNmArray"),
                        "trgterIndvdlNmArray": _text(node, "trgterIndvdlNmArray"),
                        "intrsThemaNmArray": _text(node, "intrsThemaNmArray"),
                        "inqNum": _text(node, "inqNum"),
                        "lastModYmd": _text(node, "lastModYmd"),
                    }
                    for node in payload.findall("servList")
                ]
            else:
                raise ValueError("지자체 목록 응답 형식이 지원되지 않습니다.")

            if not items:
                break

            for item in items:
                external_id = str(item.get("servId", "")).strip()
                if not external_id:
                    continue
                defaults = {
                    "source": SocialService.SOURCE_LOCAL,
                    "title": str(item.get("servNm", "")),
                    "summary": str(item.get("servDgst", "")),
                    "detail_url": str(item.get("servDtlLink", "")),
                    "department": str(item.get("bizChrDeptNm", "")),
                    "region_ctpv": str(item.get("ctpvNm", "")),
                    "region_sgg": str(item.get("sggNm", "")),
                    "support_cycle": str(item.get("sprtCycNm", "")),
                    "support_type": str(item.get("srvPvsnNm", "")),
                    "apply_method_name": str(item.get("aplyMtdNm", "")),
                    "life_names": str(item.get("lifeNmArray", "")),
                    "target_names": str(item.get("trgterIndvdlNmArray", "")),
                    "theme_names": str(item.get("intrsThemaNmArray", "")),
                    "view_count": _parse_int(item.get("inqNum")),
                    "last_modified": _parse_date(str(item.get("lastModYmd", ""))),
                }
                SocialService.objects.update_or_create(
                    source=SocialService.SOURCE_LOCAL,
                    external_id=external_id,
                    defaults=defaults,
                )
                saved_count += 1

                detail_payload = client.get(
                    self.LOCAL_BASE,
                    "/LcgvWelfaredetailed",
                    {
                        "serviceKey": api_key,
                        "servId": external_id,
                    },
                )
                if isinstance(detail_payload, ET.Element):
                    detail_payload = {
                        "servNm": _text(detail_payload, "servNm"),
                        "servDgst": _text(detail_payload, "servDgst"),
                        "bizChrDeptNm": _text(detail_payload, "bizChrDeptNm"),
                        "ctpvNm": _text(detail_payload, "ctpvNm"),
                        "sggNm": _text(detail_payload, "sggNm"),
                        "sprtCycNm": _text(detail_payload, "sprtCycNm"),
                        "srvPvsnNm": _text(detail_payload, "srvPvsnNm"),
                        "aplyMtdNm": _text(detail_payload, "aplyMtdNm"),
                        "aplyMtdCn": _text(detail_payload, "aplyMtdCn"),
                        "sprtTrgtCn": _text(detail_payload, "sprtTrgtCn"),
                        "slctCritCn": _text(detail_payload, "slctCritCn"),
                        "alwServCn": _text(detail_payload, "alwServCn"),
                        "lifeNmArray": _text(detail_payload, "lifeNmArray"),
                        "trgterIndvdlNmArray": _text(detail_payload, "trgterIndvdlNmArray"),
                        "intrsThemaNmArray": _text(detail_payload, "intrsThemaNmArray"),
                        "inqNum": _text(detail_payload, "inqNum"),
                        "enfcBgngYmd": _text(detail_payload, "enfcBgngYmd"),
                        "enfcEndYmd": _text(detail_payload, "enfcEndYmd"),
                        "lastModYmd": _text(detail_payload, "lastModYmd"),
                        "inqplCtadrList": [
                            {
                                "wlfareInfoDtlCd": _text(node, "wlfareInfoDtlCd"),
                                "wlfareInfoReldNm": _text(node, "wlfareInfoReldNm"),
                                "wlfareInfoReldCn": _text(node, "wlfareInfoReldCn"),
                            }
                            for node in detail_payload.findall("inqplCtadrList")
                        ],
                        "inqplHmpgReldList": [
                            {
                                "wlfareInfoDtlCd": _text(node, "wlfareInfoDtlCd"),
                                "wlfareInfoReldNm": _text(node, "wlfareInfoReldNm"),
                                "wlfareInfoReldCn": _text(node, "wlfareInfoReldCn"),
                            }
                            for node in detail_payload.findall("inqplHmpgReldList")
                        ],
                        "baslawList": [
                            {
                                "wlfareInfoDtlCd": _text(node, "wlfareInfoDtlCd"),
                                "wlfareInfoReldNm": _text(node, "wlfareInfoReldNm"),
                                "wlfareInfoReldCn": _text(node, "wlfareInfoReldCn"),
                            }
                            for node in detail_payload.findall("baslawList")
                        ],
                        "basfrmList": [
                            {
                                "wlfareInfoDtlCd": _text(node, "wlfareInfoDtlCd"),
                                "wlfareInfoReldNm": _text(node, "wlfareInfoReldNm"),
                                "wlfareInfoReldCn": _text(node, "wlfareInfoReldCn"),
                            }
                            for node in detail_payload.findall("basfrmList")
                        ],
                    }

                if isinstance(detail_payload, dict):
                    self._merge_local_detail(external_id, detail_payload)
                time.sleep(0.1)

            if total_count is not None and page_no * num_of_rows >= total_count:
                break

        return saved_count

    def _merge_local_detail(self, external_id: str, payload: dict[str, Any]) -> None:
        service = SocialService.objects.filter(
            source=SocialService.SOURCE_LOCAL,
            external_id=external_id,
        ).first()
        if not service:
            return

        service.title = str(payload.get("servNm", service.title))
        service.summary = str(payload.get("servDgst", service.summary))
        service.department = str(payload.get("bizChrDeptNm", service.department))
        service.region_ctpv = str(payload.get("ctpvNm", service.region_ctpv))
        service.region_sgg = str(payload.get("sggNm", service.region_sgg))
        service.support_cycle = str(payload.get("sprtCycNm", service.support_cycle))
        service.support_type = str(payload.get("srvPvsnNm", service.support_type))
        service.apply_method_name = str(payload.get("aplyMtdNm", service.apply_method_name))
        service.apply_method_detail = str(payload.get("aplyMtdCn", ""))
        service.target_detail = str(payload.get("sprtTrgtCn", ""))
        service.selection_criteria = str(payload.get("slctCritCn", ""))
        service.benefit_detail = str(payload.get("alwServCn", ""))
        service.life_names = str(payload.get("lifeNmArray", service.life_names))
        service.target_names = str(payload.get("trgterIndvdlNmArray", service.target_names))
        service.theme_names = str(payload.get("intrsThemaNmArray", service.theme_names))
        service.view_count = _parse_int(payload.get("inqNum"))
        service.start_date = _parse_date(str(payload.get("enfcBgngYmd", "")))
        service.end_date = _parse_date(str(payload.get("enfcEndYmd", "")))
        service.last_modified = _parse_date(str(payload.get("lastModYmd", "")))
        service.contact_list = _as_list(payload.get("inqplCtadrList"))
        service.homepage_list = _as_list(payload.get("inqplHmpgReldList"))
        service.law_list = _as_list(payload.get("baslawList"))
        service.form_list = _as_list(payload.get("basfrmList"))
        service.save()

    def _fetch_odcloud(
        self,
        client: ApiClient,
        api_key: str,
        max_pages: int,
        num_of_rows: int,
    ) -> int:
        saved_count = 0
        for page_no in range(1, max_pages + 1):
            payload = client.get(
                self.ODCLOUD_BASE,
                "",
                {
                    "serviceKey": api_key,
                    "returnType": "JSON",
                    "page": page_no,
                    "perPage": num_of_rows,
                },
            )
            if not isinstance(payload, dict):
                raise ValueError("복지서비스정보 응답 형식이 JSON이 아닙니다.")
            items = payload.get("data") or []
            if not isinstance(items, list) or not items:
                break

            for item in items:
                if not isinstance(item, dict):
                    continue
                external_id = str(item.get("서비스아이디", "")).strip()
                if not external_id:
                    continue
                defaults = {
                    "source": SocialService.SOURCE_ODCLOUD,
                    "title": str(item.get("서비스명", "")),  # 서비스명
                    "summary": str(item.get("서비스요약", "")),  # 서비스요약
                    "detail_url": str(item.get("서비스URL", "")),  # 서비스URL
                    "site_url": str(item.get("사이트", "")),  # 사이트
                    "contact": str(item.get("대표문의", "")),  # 대표문의
                    "ministry": str(item.get("소관부처명", "")),  # 소관부처명
                    "organization": str(item.get("소관조직명", "")),  # 소관조직명
                    "base_year": _parse_int(item.get("기준연도")),  # 기준연도
                    "last_modified": _parse_date(str(item.get("최종수정일", ""))),  # 최종수정일
                }
                SocialService.objects.update_or_create(
                    source=SocialService.SOURCE_ODCLOUD,
                    external_id=external_id,
                    defaults=defaults,
                )
                saved_count += 1

            total_count = _parse_int(payload.get("totalCount"))
            if total_count is not None and page_no * num_of_rows >= total_count:
                break

        return saved_count

    def _mark_status(self, source: str, success: bool, message: str) -> None:
        status = ServiceFetchStatus.STATUS_SUCCESS if success else ServiceFetchStatus.STATUS_FAILURE
        ServiceFetchStatus.objects.update_or_create(
            source=source,
            fetch_date=date.today(),
            defaults={"status": status, "message": message},
        )

    def _flatten_details(self, nodes: list[ET.Element]) -> str:
        values = []
        for node in nodes:
            label = _text(node, "servSeDetailNm")
            link = _text(node, "servSeDetailLink")
            if label and link:
                values.append(f"{label}: {link}")
            elif label:
                values.append(label)
        return "\n".join(values)

    def _parse_servse_list(self, nodes: list[ET.Element]) -> list[dict[str, str]]:
        return [
            {
                "servSeCode": _text(node, "servSeCode"),
                "servSeDetailNm": _text(node, "servSeDetailNm"),
                "servSeDetailLink": _text(node, "servSeDetailLink"),
            }
            for node in nodes
        ]
