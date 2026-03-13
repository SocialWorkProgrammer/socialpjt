# 사회서비스 API 필드 매핑표

## 공통 저장 정책
- 저장 모델: `SocialService`
- 고유 키: `source + external_id`
- 키 정책: `SOCIAL_SERVICE_API_KEY` 사용, `PUBLIC_API_KEY`는 빈 문자열 유지
- 수집 주기: 하루 1회

## 중앙부처복지서비스 (NationalWelfareInformationsV001)
| API 필드 | DB 필드 | 한글 주석 |
|---|---|---|
| `servId` | `external_id` | 서비스 ID |
| `servNm` | `title` | 서비스명 |
| `servDgst` | `summary` | 서비스 요약 |
| `servDtlLink` | `detail_url` | 서비스 상세 링크 |
| `jurMnofNm` | `ministry` | 소관부처명 |
| `jurOrgNm` | `organization` | 소관조직명 |
| `sprtCycNm` | `support_cycle` | 지원주기 |
| `srvPvsnNm` | `support_type` | 지원유형 |
| `onapPsbltYn` | `online_applicable` | 온라인신청 가능 여부 |
| `inqNum` | `view_count` | 조회수 |
| `svcfrstRegTs` | `first_registered_at` | 최초등록일 |
| `lifeArray` | `life_codes` | 생애주기 코드 |
| `trgterIndvdlArray` | `target_codes` | 가구상황 코드 |
| `intrsThemaArray` | `theme_codes` | 관심주제 코드 |
| `tgtrDtlCn` | `target_detail` | 지원대상 상세 |
| `slctCritCn` | `selection_criteria` | 선정기준 |
| `alwServCn` | `benefit_detail` | 지원내용 |
| `wlfareInfoOutlCn` | `welfare_outline` | 복지정보 개요 |

## 지자체복지서비스 (LocalGovernmentWelfareInformations)
| API 필드 | DB 필드 | 한글 주석 |
|---|---|---|
| `servId` | `external_id` | 서비스 ID |
| `servNm` | `title` | 서비스명 |
| `servDgst` | `summary` | 서비스 요약 |
| `servDtlLink` | `detail_url` | 서비스 상세 링크 |
| `bizChrDeptNm` | `department` | 담당부서명 |
| `ctpvNm` | `region_ctpv` | 시도명 |
| `sggNm` | `region_sgg` | 시군구명 |
| `sprtCycNm` | `support_cycle` | 지원주기 |
| `srvPvsnNm` | `support_type` | 지원유형 |
| `aplyMtdNm` | `apply_method_name` | 신청방법명 |
| `aplyMtdCn` | `apply_method_detail` | 신청방법 상세 |
| `sprtTrgtCn` | `target_detail` | 지원대상 |
| `slctCritCn` | `selection_criteria` | 선정기준 |
| `alwServCn` | `benefit_detail` | 지원내용 |
| `enfcBgngYmd` | `start_date` | 시행시작일 |
| `enfcEndYmd` | `end_date` | 시행종료일 |
| `lastModYmd` | `last_modified` | 최종수정일 |
| `lifeNmArray` | `life_names` | 생애주기명 |
| `trgterIndvdlNmArray` | `target_names` | 가구상황명 |
| `intrsThemaNmArray` | `theme_names` | 관심주제명 |

## 복지서비스정보 (odcloud)
| API 필드 | DB 필드 | 한글 주석 |
|---|---|---|
| `서비스아이디` | `external_id` | 서비스아이디 |
| `서비스명` | `title` | 서비스명 |
| `서비스URL` | `detail_url` | 서비스URL |
| `서비스요약` | `summary` | 서비스요약 |
| `사이트` | `site_url` | 사이트 |
| `대표문의` | `contact` | 대표문의 |
| `소관부처명` | `ministry` | 소관부처명 |
| `소관조직명` | `organization` | 소관조직명 |
| `기준연도` | `base_year` | 기준연도 |
| `최종수정일` | `last_modified` | 최종수정일 |
