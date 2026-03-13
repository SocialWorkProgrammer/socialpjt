import re
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


def normalize_profile(payload: dict[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for field in ALLOWED_PROFILE_FIELDS:
        value = payload.get(field, "")
        if value is None:
            value = ""
        value = str(value).strip()
        if field == "special_notes":
            value = mask_sensitive_text(value)
        normalized[field] = value
    return normalized
