import json
from dataclasses import dataclass
from urllib.request import Request, urlopen

from django.conf import settings

from .prompts import build_recommendation_prompt


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
        with urlopen(request, timeout=40) as response:  # noqa: S310
            raw = response.read().decode("utf-8", errors="ignore")
        data = json.loads(raw)
        text = str(data.get("response", "")).strip()
        if not text:
            text = "추천 문장을 생성하지 못했습니다."
        return LLMResult(provider=self.provider, used_fallback=False, message=text)


def get_llm_client() -> BaseLLMClient:
    mode = getattr(settings, "SERVICE_LLM_MODE", "stub")
    if mode == "ollama":
        return OllamaLLMClient(
            endpoint=getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            model=getattr(settings, "OLLAMA_MODEL", "qwen2.5:7b-instruct"),
        )
    return StubLLMClient()
