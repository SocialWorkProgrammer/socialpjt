import json
import logging
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from .prompts import build_recommendation_prompt


logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    provider: str
    used_fallback: bool
    message: str


class BaseLLMClient:
    provider = "base"

    def generate_recommendation(
        self,
        profile: dict[str, str],
        candidates: list[dict[str, str]],
    ) -> LLMResult:
        raise NotImplementedError


class LLMClientError(RuntimeError):
    pass


class StubLLMClient(BaseLLMClient):
    provider = "stub"

    def generate_recommendation(
        self,
        profile: dict[str, str],
        candidates: list[dict[str, str]],
    ) -> LLMResult:
        if not candidates:
            return LLMResult(
                provider=self.provider,
                used_fallback=False,
                message=(
                    "조건에 맞는 서비스 후보를 찾지 못했습니다. "
                    "검색 조건을 완화하거나 입력 프로파일을 확인해 주세요."
                ),
            )
        lines = []
        for item in candidates[:3]:
            lines.append(
                f"- {item.get('title', '-')}: 대상({item.get('target', '-')})/"
                f"지역({item.get('region', '-')}) 기준 후보, 링크 {item.get('url', '-')}"
            )
        lines.append("최종 판단은 사회복지사 검토가 필요합니다.")
        return LLMResult(
            provider=self.provider,
            used_fallback=False,
            message="\n".join(lines),
        )


class OllamaLLMClient(BaseLLMClient):
    provider = "ollama"

    def __init__(self, endpoint: str, model: str) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model = model

    def generate_recommendation(
        self,
        profile: dict[str, str],
        candidates: list[dict[str, str]],
    ) -> LLMResult:
        logger.info("llm_call_start provider=%s candidates=%d", self.provider, len(candidates))
        prompt = build_recommendation_prompt(profile=profile, candidates=candidates)
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8")
        request = Request(
            url=f"{self.endpoint}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=40) as response:  # noqa: S310
                raw = response.read().decode("utf-8", errors="ignore")
        except (HTTPError, URLError) as exc:
            logger.warning("llm_call_failure provider=%s error=%s", self.provider, exc)
            raise LLMClientError(f"ollama 요청 실패: {exc}") from exc
        data = json.loads(raw)
        text = str(data.get("response", "")).strip()
        if not text:
            text = "추천 문장을 생성하지 못했습니다."
        logger.info("llm_call_success provider=%s", self.provider)
        return LLMResult(provider=self.provider, used_fallback=False, message=text)


class GeminiLLMClient(BaseLLMClient):
    provider = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate_recommendation(
        self,
        profile: dict[str, str],
        candidates: list[dict[str, str]],
    ) -> LLMResult:
        logger.info("llm_call_start provider=%s candidates=%d", self.provider, len(candidates))
        prompt = build_recommendation_prompt(profile=profile, candidates=candidates)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = json.dumps(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2},
            }
        ).encode("utf-8")
        request = Request(
            url=url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=40) as response:  # noqa: S310
                raw = response.read().decode("utf-8", errors="ignore")
        except (HTTPError, URLError) as exc:
            logger.warning("llm_call_failure provider=%s error=%s", self.provider, exc)
            raise LLMClientError(f"gemini 요청 실패: {exc}") from exc

        data = json.loads(raw)
        text = ""
        candidates_data = data.get("candidates") or []
        if candidates_data:
            parts = (((candidates_data[0] or {}).get("content") or {}).get("parts") or [])
            if parts:
                text = str((parts[0] or {}).get("text", "")).strip()
        if not text:
            raise LLMClientError("gemini 응답 본문이 비어 있습니다.")
        logger.info("llm_call_success provider=%s", self.provider)
        return LLMResult(provider=self.provider, used_fallback=False, message=text)


class OpenRouterLLMClient(BaseLLMClient):
    provider = "openrouter"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate_recommendation(
        self,
        profile: dict[str, str],
        candidates: list[dict[str, str]],
    ) -> LLMResult:
        logger.info("llm_call_start provider=%s candidates=%d", self.provider, len(candidates))
        prompt = build_recommendation_prompt(profile=profile, candidates=candidates)
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "사회복지 상담 보조 추천 AI로 동작하고 후보 외 추정을 금지한다.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
        ).encode("utf-8")
        request = Request(
            url="https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=40) as response:  # noqa: S310
                raw = response.read().decode("utf-8", errors="ignore")
        except (HTTPError, URLError) as exc:
            logger.warning("llm_call_failure provider=%s error=%s", self.provider, exc)
            raise LLMClientError(f"openrouter 요청 실패: {exc}") from exc

        data = json.loads(raw)
        text = ""
        choices = data.get("choices") or []
        if choices:
            message = (choices[0] or {}).get("message") or {}
            text = str(message.get("content", "")).strip()
        if not text:
            raise LLMClientError("openrouter 응답 본문이 비어 있습니다.")
        logger.info("llm_call_success provider=%s", self.provider)
        return LLMResult(provider=self.provider, used_fallback=False, message=text)


class FallbackLLMClient(BaseLLMClient):
    provider = "fallback"

    def __init__(self, primary: BaseLLMClient, fallback: BaseLLMClient) -> None:
        self.primary = primary
        self.fallback = fallback

    def generate_recommendation(
        self,
        profile: dict[str, str],
        candidates: list[dict[str, str]],
    ) -> LLMResult:
        try:
            return self.primary.generate_recommendation(profile=profile, candidates=candidates)
        except Exception as exc:
            logger.warning(
                "llm_fallback_trigger primary=%s fallback=%s error=%s",
                self.primary.provider,
                self.fallback.provider,
                exc,
            )
            fallback_result = self.fallback.generate_recommendation(
                profile=profile,
                candidates=candidates,
            )
            fallback_result.used_fallback = True
            return fallback_result


def _external_llm_allowed() -> bool:
    return getattr(settings, "ALLOW_EXTERNAL_LLM", "false").lower() == "true"


def _build_from_mode(mode: str) -> BaseLLMClient:
    if mode == "ollama":
        return OllamaLLMClient(
            endpoint=getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            model=getattr(settings, "OLLAMA_MODEL", "qwen2.5:7b-instruct"),
        )
    if mode == "gemini":
        if not _external_llm_allowed():
            raise LLMClientError("외부 LLM 사용이 차단되었습니다. ALLOW_EXTERNAL_LLM=true 설정이 필요합니다.")
        api_key = getattr(settings, "GEMINI_API_KEY", "")
        if not api_key:
            raise LLMClientError("GEMINI_API_KEY가 설정되지 않았습니다.")
        return GeminiLLMClient(
            api_key=api_key,
            model=getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"),
        )
    if mode == "openrouter":
        if not _external_llm_allowed():
            raise LLMClientError("외부 LLM 사용이 차단되었습니다. ALLOW_EXTERNAL_LLM=true 설정이 필요합니다.")
        api_key = getattr(settings, "OPENROUTER_API_KEY", "")
        if not api_key:
            raise LLMClientError("OPENROUTER_API_KEY가 설정되지 않았습니다.")
        return OpenRouterLLMClient(
            api_key=api_key,
            model=getattr(settings, "OPENROUTER_MODEL", "qwen/qwen3-8b:free"),
        )
    return StubLLMClient()


def get_llm_client() -> BaseLLMClient:
    mode = getattr(settings, "SERVICE_LLM_MODE", "stub")
    fallback_mode = getattr(settings, "SERVICE_LLM_FALLBACK_MODE", "")
    primary = _build_from_mode(mode)
    if fallback_mode:
        fallback = _build_from_mode(fallback_mode)
        logger.info("llm_mode_config primary=%s fallback=%s", mode, fallback_mode)
        return FallbackLLMClient(primary=primary, fallback=fallback)
    logger.info("llm_mode_config primary=%s fallback=none", mode)
    return primary
