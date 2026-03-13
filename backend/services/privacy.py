import re
from dataclasses import dataclass
from typing import Any


ALLOWED_PROFILE_FIELDS = (
    "age_group",
    "region_ctpv",
    "region_sgg",
    "target_type",
    "life_stage",
    "interest_theme",
    "special_notes",
)


def mask_sensitive_text(raw_text: str) -> str:
    text = raw_text
    patterns = [
        r"\b\d{6}-?[1-4]\d{6}\b",  # resident id
        r"\b01[0-9]-?\d{3,4}-?\d{4}\b",  # mobile
        r"\b\d{2,3}-?\d{3,4}-?\d{4}\b",  # phone
        r"\b\d{2,3}\s?[가-힣A-Za-z0-9]+\s?(로|길)\s?\d+[-\d]*\b",  # address part
        r"\b\d{2,3}-\d{2}-\d{4,6}\b",  # account-like
    ]
    for pattern in patterns:
        text = re.sub(pattern, "[MASKED]", text)
    return text


SENSITIVE_PATTERNS = [
    r"\b\d{6}-?[1-4]\d{6}\b",  # resident id
    r"\b01[0-9]-?\d{3,4}-?\d{4}\b",  # mobile
    r"\b\d{2,3}-?\d{3,4}-?\d{4}\b",  # phone
    r"\b\d{2,3}\s?[가-힣A-Za-z0-9]+\s?(로|길)\s?\d+[-\d]*\b",  # address part
    r"\b\d{2,3}-\d{2}-\d{4,6}\b",  # account-like
    r"\b\d{1,2}억\b",  # asset hint
    r"\b\d{1,3}(,\d{3})+원\b",  # amount
]


@dataclass
class SafetyReport:
    blocked: bool
    findings: list[str]


def normalize_profile(payload: dict[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for field in ALLOWED_PROFILE_FIELDS:
        value = payload.get(field, "")
        if value is None:
            value = ""
        value = str(value).strip()
        value = mask_sensitive_text(value)
        normalized[field] = value
    return normalized


def analyze_profile_safety(payload: dict[str, Any]) -> SafetyReport:
    findings: list[str] = []
    for field in ALLOWED_PROFILE_FIELDS:
        raw = payload.get(field, "")
        text = str(raw or "")
        for pattern in SENSITIVE_PATTERNS:
            if re.search(pattern, text):
                findings.append(field)
                break

    unique_findings = sorted(set(findings))
    return SafetyReport(blocked=bool(unique_findings), findings=unique_findings)
