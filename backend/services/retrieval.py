from datetime import date

from .models import SocialService


def _match_score(service: SocialService, profile: dict[str, str]) -> int:
    score = 0

    region_ctpv = profile.get("region_ctpv", "")
    region_sgg = profile.get("region_sgg", "")
    target_type = profile.get("target_type", "")
    life_stage = profile.get("life_stage", "")
    interest_theme = profile.get("interest_theme", "")
    notes = profile.get("special_notes", "")

    if region_ctpv and region_ctpv in (service.region_ctpv or ""):
        score += 3
    if region_sgg and region_sgg in (service.region_sgg or ""):
        score += 2

    target_pool = " ".join([service.target_codes or "", service.target_names or "", service.target_detail or ""])
    if target_type and target_type in target_pool:
        score += 3

    life_pool = " ".join([service.life_codes or "", service.life_names or "", service.summary or ""])
    if life_stage and life_stage in life_pool:
        score += 2

    theme_pool = " ".join([service.theme_codes or "", service.theme_names or "", service.summary or ""])
    if interest_theme and interest_theme in theme_pool:
        score += 2

    if notes:
        merged = " ".join(
            [
                service.summary or "",
                service.target_detail or "",
                service.benefit_detail or "",
                service.selection_criteria or "",
            ]
        )
        tokens = [token for token in notes.split() if len(token) > 1][:8]
        score += sum(1 for token in tokens if token in merged)

    if service.detail_url:
        score += 1
    if service.last_modified and service.last_modified >= date(2024, 1, 1):
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
        data.append(
            {
                "service_id": service.external_id,
                "source": service.source,
                "title": service.title,
                "summary": service.summary,
                "region": " ".join(
                    value for value in [service.region_ctpv, service.region_sgg] if value
                ),
                "target": service.target_names or service.target_codes,
                "theme": service.theme_names or service.theme_codes,
                "apply": service.apply_method_name or service.apply_method_detail,
                "url": service.detail_url,
            }
        )
    return data
