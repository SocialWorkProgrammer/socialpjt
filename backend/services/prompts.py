def build_recommendation_prompt(
    profile: dict[str, str],
    candidates: list[dict[str, str]],
) -> str:
    profile_lines = [
        f"- 연령대: {profile.get('age_group', '') or '-'}",
        f"- 시도: {profile.get('region_ctpv', '') or '-'}",
        f"- 시군구: {profile.get('region_sgg', '') or '-'}",
        f"- 대상유형: {profile.get('target_type', '') or '-'}",
        f"- 생애주기: {profile.get('life_stage', '') or '-'}",
        f"- 관심주제: {profile.get('interest_theme', '') or '-'}",
        f"- 상담 메모(비식별): {profile.get('special_notes', '') or '-'}",
    ]

    if candidates:
        candidate_lines = []
        for index, item in enumerate(candidates, start=1):
            candidate_lines.append(
                (
                    f"{index}) 서비스명: {item.get('title', '-')}, "
                    f"대상: {item.get('target', '-')}, "
                    f"지역: {item.get('region', '-')}, "
                    f"주제: {item.get('theme', '-')}, "
                    f"링크: {item.get('url', '-')}, "
                    f"요약: {item.get('summary', '-')[:180]}"
                )
            )
    else:
        candidate_lines = ["후보 서비스 없음"]

    return "\n".join(
        [
            "너는 사회복지사 상담 보조 AI다.",
            "제공된 후보 서비스 데이터만 사용해 답변하고, 없는 정보는 추측하지 마라.",
            "추천 3개를 제시하고 각 항목마다 근거와 신청 링크를 짧게 작성하라.",
            "마지막 줄에 '최종 판단은 사회복지사 검토가 필요합니다.' 문구를 넣어라.",
            "",
            "[상담 프로파일]",
            *profile_lines,
            "",
            "[후보 서비스]",
            *candidate_lines,
        ]
    )
