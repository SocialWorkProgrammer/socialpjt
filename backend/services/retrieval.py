from datetime import date

from .models import SocialService


def _match_score(service: SocialService, profile: dict[str, str]) -> int:
    score = 0
    region_ctpv_value = str(service.region_ctpv or "")
    region_sgg_value = str(service.region_sgg or "")
    target_codes_value = str(service.target_codes or "")
    target_names_value = str(service.target_names or "")
    target_detail_value = str(service.target_detail or "")
    life_codes_value = str(service.life_codes or "")
    life_names_value = str(service.life_names or "")
    summary_value = str(service.summary or "")
    theme_codes_value = str(service.theme_codes or "")
    theme_names_value = str(service.theme_names or "")
    benefit_detail_value = str(service.benefit_detail or "")
    selection_criteria_value = str(service.selection_criteria or "")
    title_value = str(service.title or "")

    region_ctpv = profile.get("region_ctpv", "")
    region_sgg = profile.get("region_sgg", "")
    target_type = profile.get("target_type", "")
    life_stage = profile.get("life_stage", "")
    interest_theme = profile.get("interest_theme", "")
    notes = profile.get("special_notes", "")

    if region_ctpv and region_ctpv in region_ctpv_value:
        score += 5
    elif region_ctpv:
        score -= 1
    if region_sgg and region_sgg in region_sgg_value:
        score += 4
    elif region_sgg and region_sgg_value:
        score -= 1

    target_pool = " ".join([target_codes_value, target_names_value, target_detail_value])
    if target_type and target_type in target_pool:
        score += 5

    life_pool = " ".join([life_codes_value, life_names_value, summary_value])
    if life_stage and life_stage in life_pool:
        score += 4

    theme_pool = " ".join([theme_codes_value, theme_names_value, summary_value])
    if interest_theme and interest_theme in theme_pool:
        score += 4

    if notes:
        merged = " ".join(
            [
                summary_value,
                target_detail_value,
                benefit_detail_value,
                selection_criteria_value,
            ]
        )
        tokens = [token for token in notes.split() if len(token) > 1][:8]
        score += sum(2 for token in tokens if token in merged)

    primary_tokens = [
        profile.get("target_type", ""),
        profile.get("life_stage", ""),
        profile.get("interest_theme", ""),
    ]
    searchable = " ".join(
        [
            title_value,
            summary_value,
            target_detail_value,
            benefit_detail_value,
        ]
    )
    score += sum(1 for token in primary_tokens if token and token in searchable)

    detail_url_value = str(service.detail_url or "")
    if detail_url_value:
        score += 1
    if service.last_modified and service.last_modified >= date(2024, 1, 1):
        score += 2
    if service.source == SocialService.SOURCE_LOCAL:
        score += 1

    return score


def retrieve_candidate_services(profile: dict[str, str], limit: int = 5) -> list[SocialService]:
    queryset = SocialService.objects.all()

    region_ctpv = profile.get("region_ctpv", "")
    region_sgg = profile.get("region_sgg", "")
    if region_ctpv:
        queryset = queryset.filter(region_ctpv__icontains=region_ctpv)
    if region_sgg:
        queryset = queryset.filter(region_sgg__icontains=region_sgg)

    services = list(queryset[:400])
    if not services:
        services = list(SocialService.objects.all()[:200])

    ranked = sorted(
        services,
        key=lambda service: (_match_score(service, profile), service.fetched_at),
        reverse=True,
    )
    return ranked[:limit]


def serialize_candidates(services: list[SocialService]) -> list[dict[str, str]]:
    data: list[dict[str, str]] = []
    for service in services:
        service_id = str(service.external_id)
        source = str(service.source)
        title = str(service.title)
        summary = str(service.summary or "")
        region_ctpv = str(service.region_ctpv or "")
        region_sgg = str(service.region_sgg or "")
        region = " ".join(value for value in [region_ctpv, region_sgg] if value)
        target = str(service.target_names or service.target_codes or "")
        theme = str(service.theme_names or service.theme_codes or "")
        apply = str(service.apply_method_name or service.apply_method_detail or "")
        url = str(service.detail_url or "")
        data.append(
            {
                "service_id": service_id,
                "source": source,
                "title": title,
                "summary": summary,
                "region": region,
                "target": target,
                "theme": theme,
                "apply": apply,
                "url": url,
            }
        )
    return data
