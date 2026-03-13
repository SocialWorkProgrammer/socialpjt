# AI 구축/운영 전체 가이드 (사회복지 서비스 추천 챗봇)

이 문서는 지금까지의 AI 관련 대화 내용을 전부 정리하고, 이후 혼자서도 모델을 구축/운영할 수 있도록 실무 단계로 상세히 정리한 문서입니다.

---

## 1) 프로젝트 목표와 전제

### 목표
- 사회복지사가 상담 시, 어떤 복지서비스를 안내해야 할지 빠르게 추천받는 챗봇 구축
- 단순 대화형이 아니라, 공공 API 기반 데이터(`SocialService`)를 근거로 답변하는 보조 시스템

### 사용 데이터 원천
- 중앙부처복지서비스 API
- 지자체복지서비스 API
- 복지서비스정보(odcloud) API

### 이미 확정된 정책
- API 키 정책
  - `SOCIAL_SERVICE_API_KEY`를 실제 수집 키로 사용
  - `PUBLIC_API_KEY`는 추후용으로 `.env`에 빈 문자열 유지
- 수집 정책
  - DB 저장 후 하루 1회 갱신
- 필드 정책
  - 내부 DB 필드명은 영문
  - 코드에는 한글 주석 병기
  - 문서 매핑표(`docs/social-service-field-mapping.md`)에 한글 설명 병기

---

## 2) 개인정보/보안 원칙 (가장 중요)

사회복지 상담 데이터는 민감정보가 포함되므로 아래 원칙을 반드시 지켜야 함.

### 절대 원칙
- 원문 상담기록(이름/주소/연락처/재산/건강상태 등)을 외부 LLM으로 직접 전송하지 않음
- LLM에는 비식별화된 요약 특성만 전달

### 실무 처리 방식
- 원문 저장 위치: 내부 DB
- LLM 전달 데이터: 프로파일화된 값
  - 예: `연령대=노년`, `지역=서울특별시`, `가구유형=저소득`, `상황=임신출산`
- 프롬프트 전송 전 마스킹
  - 이름, 휴대폰, 상세주소, 주민번호, 계좌번호 패턴 제거
- 로그
  - 프롬프트/응답 원문 저장 시 민감정보 제거
  - 접근 권한 최소화, 보관 기간 제한

### 권장 문구(응답 정책)
- "아래 추천은 보조 참고 정보이며 최종 판단은 사회복지사 검토가 필요합니다."

---

## 3) 로컬 vs 온라인 LLM 의사결정 기준

### 로컬 LLM
- 장점: 데이터 통제, 외부 전송 최소화
- 단점: GPU/서빙/모니터링 직접 운영 필요

### 온라인 LLM
- 장점: 빠른 MVP, 초기 품질 검증 쉬움
- 단점: 무료 티어 변동, 민감정보 전송 통제 필요

### 권장 전략
- 1단계: 빠르게 MVP 구축(온라인 또는 로컬)
- 2단계: RAG 품질/보안 체계 고정
- 3단계: 비용/속도/보안 요구에 맞춰 하이브리드 또는 로컬 고도화

---

## 4) 현재 장비 기준 로컬 LLM 가능 여부

### 보유 장비
- 노트북: 갤럭시북5 프로
- 데스크탑: GTX 1660 Super(6GB), RAM 32GB, Ryzen 5 9600X(6코어)

### 결론
- 로컬 LLM 시작 가능
- 현실적인 모델 크기: 7B 4bit(GGUF)
- 14B 이상은 1660S(6GB)에서 속도/메모리 부담이 큼

### 트래픽 가정
- 하루 10명, 1시간 간격
- 동시성이 낮아 현 사양으로 PoC/초기 운영 가능

---

## 5) 온라인 무료 모델 선택 가이드

### 추천(무료 중심)
- 기본 모델: `Gemini 2.0 Flash` 무료 티어
- 폴백 모델: `Qwen` 계열 무료 라우트
- 보조 폴백: `DeepSeek` 계열 무료 라우트

### 운영 포인트
- 무료 모델은 쿼터/속도/가용성 변동이 있으므로 단일 모델 고정보다 기본+폴백 구조 권장
- 온라인 사용 시에도 비식별화/마스킹 정책은 동일하게 적용

---

## 6) 권장 시스템 아키텍처 (실전)

### 핵심 구조
1. 공공 API 수집 (`fetch_social_services`)
2. 내부 DB 저장 (`SocialService`)
3. 검색 계층(RAG): 조건 필터링으로 후보 서비스 추출
4. LLM 계층: 후보를 근거 중심으로 설명/정리
5. UI 계층: 상담 입력 + 추천 결과 + 링크 표시

### 중요한 분리 원칙
- "후보 검색"과 "문장 생성"을 분리
  - 검색: DB/규칙 기반(정확성)
  - 생성: LLM(가독성/설명)

---

## 7) 현재 코드 기준 연동 포인트

이미 생성된 파일 기준으로 AI 기능을 붙일 수 있는 위치:

- 수집 명령
  - `backend/services/management/commands/fetch_social_services.py`
- 모델
  - `backend/services/models.py`
- 목록/상세 뷰
  - `backend/services/views.py`
- 라우팅
  - `backend/services/urls.py`
- 템플릿
  - `backend/services/templates/services/service_list.html`
  - `backend/services/templates/services/service_detail.html`
- 매핑 문서
  - `docs/social-service-field-mapping.md`

### 새로 추가된 AI 연동 파일
- `backend/services/privacy.py`
  - 비식별화/마스킹 함수
- `backend/services/retrieval.py`
  - 상담 프로파일 기반 후보 서비스 검색 및 직렬화
- `backend/services/prompts.py`
  - 추천용 프롬프트 생성
- `backend/services/llm_client.py`
  - LLM 어댑터(stub/ollama/gemini/openrouter + fallback)
- `backend/services/views.py`
  - `chat_recommendation` API 엔드포인트
- `backend/services/urls.py`
  - `services/chat/` 라우트

---

## 7-1) 챗봇 API 명세

### 엔드포인트
- `POST /services/chat/`

### 요청 JSON 예시

```json
{
  "age_group": "노년",
  "region_ctpv": "서울특별시",
  "region_sgg": "송파구",
  "target_type": "저소득",
  "life_stage": "노년",
  "interest_theme": "신체건강",
  "special_notes": "연락처 010-1234-5678, 거동이 불편"
}
```

### 응답 JSON 예시

```json
{
  "profile": {
    "age_group": "노년",
    "region_ctpv": "서울특별시",
    "region_sgg": "송파구",
    "target_type": "저소득",
    "life_stage": "노년",
    "interest_theme": "신체건강",
    "special_notes": "연락처 [MASKED], 거동이 불편"
  },
  "recommendations": [
    {
      "service_id": "L-1",
      "source": "local",
      "title": "어르신 건강 지원 서비스",
      "summary": "...",
      "region": "서울특별시 송파구",
      "target": "저소득",
      "theme": "신체건강",
      "apply": "...",
      "url": "https://..."
    }
  ],
  "llm": {
    "provider": "stub",
    "used_fallback": false,
    "message": "..."
  },
  "disclaimer": "추천 결과는 참고용이며 최종 판단은 사회복지사 검토가 필요합니다."
}
```

### 상태 코드
- `200`: 정상
- `400`: JSON 파싱 실패
- `302`: 미로그인(로그인 필요)

---

## 8) 실제 구축 순서 (혼자 구축 가능한 단계별 가이드)

## 8-1. 환경 준비

프로젝트 루트 `.env` 예시:

```env
DJANGO_SECRET_KEY=your-secret
DJANGO_DEBUG=True
SOCIAL_SERVICE_API_KEY=your-public-data-key
PUBLIC_API_KEY=
```

백엔드 실행 기본:

```bash
cd /home/minho/socialpjt/backend
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

데이터 수집 테스트:

```bash
python3 manage.py fetch_social_services --max-pages 1 --num-of-rows 20
```

---

## 8-2. 챗봇 입력 스키마 설계 (권장)

상담 입력은 원문을 그대로 쓰지 말고 정규화된 입력 스키마를 만든다.

```json
{
  "age_group": "노년",
  "region_ctpv": "서울특별시",
  "region_sgg": "송파구",
  "target_type": "저소득",
  "life_stage": "노년",
  "interest_theme": "신체건강",
  "special_notes": "거동이 불편하고 병원 방문이 잦음"
}
```

원문 상담기록은 내부 저장하되, LLM에는 위처럼 정규화/비식별한 값만 전달.

---

## 8-3. 검색(RAG) 우선 구현

LLM 붙이기 전에 먼저 검색 정확도를 확보한다.

검색 로직 예시(개념):
- 지역 일치(`region_ctpv`, `region_sgg`)
- 대상/생애주기 일치(`target_codes`, `target_names`, `life_codes`, `life_names`)
- 관심주제 일치(`theme_codes`, `theme_names`)
- 최신성 가중치(`last_modified`)

추천 후보는 상위 5~10개를 추려 LLM에 전달.

---

## 8-4. 로컬 LLM 붙이기 (권장 시작)

### A안: Ollama
1) Ollama 설치
2) 모델 pull

```bash
ollama pull qwen2.5:7b-instruct
```

3) API 호출 예시

```bash
curl http://localhost:11434/api/generate \
  -d '{
    "model": "qwen2.5:7b-instruct",
    "prompt": "아래 후보 서비스 중 사용자 조건에 맞는 항목을 근거와 함께 3개 추천해줘...",
    "stream": false
  }'
```

### B안: llama.cpp
- GGUF 7B Q4 계열 모델 사용
- GPU offload 가능한 범위에서 설정

---

## 8-5. 온라인 LLM 붙이기 (무료 우선)

### 권장 구성
- Primary: Gemini 2.0 Flash
- Fallback: Qwen 무료 라우트

프로젝트 설정값(`.env`) 예시:

```env
SERVICE_LLM_MODE=gemini
SERVICE_LLM_FALLBACK_MODE=openrouter

GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.0-flash

OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=qwen/qwen3-8b:free
```

로컬 사용 시:

```env
SERVICE_LLM_MODE=ollama
SERVICE_LLM_FALLBACK_MODE=stub
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

### 라우팅 의사코드

```text
try primary_model
if timeout or quota_error:
    try fallback_model
if both fail:
    return "현재 AI 응답이 불안정하므로 검색 결과만 제공합니다."
```

---

## 8-6. 프롬프트 템플릿 (실무형)

시스템 프롬프트 예시:

```text
너는 사회복지사 업무를 돕는 추천 보조 AI다.
반드시 제공된 후보 서비스 데이터만 사용해 답변한다.
모르면 모른다고 답한다.
답변에는 각 추천의 근거(대상/지역/조건 일치)를 포함한다.
개인정보는 절대 재구성하거나 추정하지 않는다.
```

사용자 프롬프트 예시:

```text
[상담 프로파일]
- 연령대: 노년
- 지역: 서울특별시 송파구
- 대상유형: 저소득
- 관심주제: 신체건강

[후보 서비스 목록]
1) ...
2) ...

아래 형식으로 3개 추천해줘:
- 서비스명
- 추천 이유(조건 일치 근거)
- 신청 방법/링크
- 주의사항
```

---

## 8-7. 출력 포맷 표준화

권장 출력(JSON):

```json
{
  "recommendations": [
    {
      "service_id": "WLF...",
      "service_name": "...",
      "why": ["저소득 대상 일치", "서울 지역 지원 가능"],
      "apply": "온라인/오프라인...",
      "url": "https://..."
    }
  ],
  "disclaimer": "최종 판단은 사회복지사 검토가 필요합니다."
}
```

이 형식으로 고정하면 프론트에서 렌더링이 쉬워지고, 품질 평가도 쉬워짐.

---

## 8-8. 품질 평가 기준 (최소)

테스트 케이스 20~30개를 만들어 아래를 점검:
- Top-3 추천에 정답 서비스 포함 여부
- 근거 문장 정확성
- 지역/대상 불일치 서비스 추천률
- 응답 시간

### KPI 예시
- Top-3 포함률 >= 70%
- 명백한 오추천률 <= 10%
- 평균 응답시간 <= 10초(초기 목표)

---

## 8-9. 운영 자동화

하루 1회 수집 cron 예시:

```bash
0 3 * * * /usr/bin/python3 /home/minho/socialpjt/backend/manage.py fetch_social_services --max-pages 5 --num-of-rows 100
```

실패 시:
- `ServiceFetchStatus` 상태 확인
- 화면 팝업/알림 표시
- 관리자 로그 확인

---

## 9) 단계별 로드맵

### Phase 1: 동작 MVP
- 수집 자동화
- 검색 API/화면
- 로컬 또는 온라인 단일 모델 연결

### Phase 2: 정확도 강화
- 필터/점수화 로직 고도화
- 프롬프트 튜닝
- 테스트셋 기반 개선

### Phase 3: 보안/운영 강화
- 마스킹 자동화 고도화
- 접근권한/감사로그
- 폴백/재시도/장애대응

---

## 10) 자주 발생하는 문제와 해결

### 문제 1: 응답이 느림
- 모델 크기 줄이기(7B 유지)
- 컨텍스트 길이 줄이기
- 후보 서비스 개수 줄이기(예: 10 -> 5)

### 문제 2: 엉뚱한 서비스 추천
- 검색 계층 점수화 강화
- 후보 품질 먼저 개선 후 LLM 사용
- 프롬프트에 "후보 외 정보 금지" 명시

### 문제 3: 개인정보 노출 우려
- 전송 전 마스킹 함수 적용 여부 점검
- 로그 저장 시 민감정보 필터링 재확인
- 외부 API 호출 payload 샘플 정기 점검

---

## 11) 최소 구현 체크리스트

- [ ] `.env`에 `SOCIAL_SERVICE_API_KEY` 설정
- [ ] `migrate` 완료
- [ ] `fetch_social_services` 정상 수집 확인
- [ ] 챗봇 입력 스키마(비식별) 확정
- [ ] 검색 우선 로직 구현
- [ ] LLM 연결(로컬 또는 온라인)
- [ ] 출력 포맷 고정(JSON)
- [ ] 테스트 케이스 20개 이상 검증
- [ ] 개인정보 마스킹/로그 정책 적용

---

## 12) 최종 권장 결론

- 지금 장비로는 "로컬 7B + RAG"가 충분히 시작 가능
- 온라인 무료 모델을 쓸 경우에도 비식별화는 필수
- 품질은 모델 자체보다 검색 데이터 품질과 프롬프트/출력 구조가 더 크게 좌우됨
- 따라서 "검색 정확도 -> LLM 설명" 순서로 설계하면 실패 확률이 낮음

---

## 13) 현재 구현 완료 상태 (최신)

아래 항목은 실제 코드로 반영된 상태다.

### 13-1. 사회서비스 게시판/수집
- `services` 앱 생성 및 라우팅 연결
- `SocialService`, `ServiceFetchStatus` 모델 추가
- `fetch_social_services` 관리명령 추가
  - 중앙부처복지서비스: 목록 + 상세(XML)
  - 지자체복지서비스: 목록/상세(JSON/XML 혼합 대응)
  - 복지서비스정보(odcloud): 목록(JSON)
- `external_id + source` 기준 중복 방지(`update_or_create`)
- 일별 수집 상태 저장

### 13-2. AI 추천 API
- 엔드포인트: `POST /services/chat/`
- 처리 흐름:
  1) 입력 JSON 파싱
  2) 비식별/마스킹(`privacy.py`)
  3) 후보 검색/정렬(`retrieval.py`)
  4) LLM 생성(`llm_client.py`)
  5) JSON 응답 반환
- 미로그인 사용자는 접근 제한(로그인 필요)

### 13-3. LLM 모드
- `stub`: LLM 없이 후보 요약 문장 반환(개발 기본 모드)
- `ollama`: 로컬 모델 호출
- `gemini`: Google Generative Language API 호출
- `openrouter`: OpenRouter 모델 호출
- fallback: `SERVICE_LLM_FALLBACK_MODE` 설정 시 자동 전환

### 13-4. UI
- `services` 목록 화면에 AI 추천 폼 추가
- 입력: 연령대/지역/대상/생애주기/관심주제/비식별 메모
- 결과: LLM 응답 + 후보 서비스 목록 + 디스클레이머

### 13-5. 문서
- `docs/social-service-field-mapping.md` 필드 매핑표 정리
- `docs/AI.md` 구축/운영 전체 가이드 정리

---

## 14) 즉시 실행 절차 (처음부터 따라하기)

## 14-1. 환경 변수 준비

`.env` 예시(최소):

```env
DJANGO_SECRET_KEY=your-secret
DJANGO_DEBUG=True

SOCIAL_SERVICE_API_KEY=your-public-data-key
PUBLIC_API_KEY=

SERVICE_LLM_MODE=stub
SERVICE_LLM_FALLBACK_MODE=
```

온라인 모드 예시(Primary + Fallback):

```env
SERVICE_LLM_MODE=gemini
SERVICE_LLM_FALLBACK_MODE=openrouter

GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.0-flash

OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=qwen/qwen3-8b:free
```

로컬 모드 예시(Ollama):

```env
SERVICE_LLM_MODE=ollama
SERVICE_LLM_FALLBACK_MODE=stub
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

## 14-2. 서버 실행

```bash
cd /home/minho/socialpjt/backend
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

## 14-3. 데이터 수집

```bash
python3 manage.py fetch_social_services --max-pages 1 --num-of-rows 20
```

## 14-4. AI API 테스트

브라우저 로그인 후 `services` 목록 화면에서 폼으로 테스트하는 방법이 가장 간단하다.

API 직접 호출 예시(curl):

```bash
curl -X POST "http://127.0.0.1:8000/services/chat/" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf_token>" \
  -b "sessionid=<session_id>; csrftoken=<csrf_token>" \
  -d '{
    "age_group": "노년",
    "region_ctpv": "서울특별시",
    "region_sgg": "송파구",
    "target_type": "저소득",
    "life_stage": "노년",
    "interest_theme": "신체건강",
    "special_notes": "연락처 010-1234-5678, 거동이 불편"
  }'
```

---

## 15) 현재 코드 구조(파일별 역할)

- `backend/services/privacy.py`
  - `mask_sensitive_text`: 기본 민감정보 패턴 마스킹
  - `normalize_profile`: 입력 스키마 정규화
- `backend/services/retrieval.py`
  - 프로파일 기반 후보 서비스 검색/점수화/직렬화
- `backend/services/prompts.py`
  - 추천 프롬프트 생성(근거 중심 출력 유도)
- `backend/services/llm_client.py`
  - provider 별 호출 어댑터 + fallback 클라이언트
- `backend/services/views.py`
  - `chat_recommendation` API 오케스트레이션
- `backend/services/templates/services/service_list.html`
  - AI 폼 입력 및 결과 렌더링

---

## 16) 리스크 및 다음 보완 우선순위

### 16-1. 리스크 5개
1. 마스킹 패턴 누락 가능성
2. 규칙 기반 검색 점수의 정확도 편차
3. fallback 발생 원인 관측성 부족
4. 온라인 LLM 모드 오설정 시 외부 전송 리스크
5. provider/fallback 분기 테스트 커버리지 부족

### 16-2. 우선 보완 순서(권장)
1. 마스킹 강화 + 실패 시 전송 차단(fail-closed)
2. LLM 호출/실패/폴백 구조화 로그 추가
3. `ALLOW_EXTERNAL_LLM` 같은 운영 게이트 추가
4. 검색 가중치 튜닝(테스트셋 20~30개 기반)
5. `llm_client` 모킹 테스트 확장

---

## 17) 운영 체크 포인트

- AI 답변은 항상 "추천 + 근거 + 링크 + 디스클레이머" 포맷 유지
- 상담 원문은 내부 저장, LLM에는 비식별 프로파일만 전달
- 무료 온라인 모델 사용 시 quota/지연 대비 fallback 유지
- daily 수집 실패는 `ServiceFetchStatus`로 모니터링

---

## 18) 보안 강화 반영 사항 (최신)

이번 단계에서 아래 항목을 실제 코드에 반영했다.

### 18-1. 외부 LLM 차단 게이트
- 기본값: 외부 LLM 사용 차단
- 설정 키: `ALLOW_EXTERNAL_LLM`
  - `false`(기본): `gemini`, `openrouter` 모드 차단
  - `true`: 외부 LLM 모드 허용
- 목적: 운영 실수로 외부 전송이 켜지는 상황 방지

`.env` 예시:

```env
ALLOW_EXTERNAL_LLM=false
```

외부 LLM이 필요한 경우에만:

```env
ALLOW_EXTERNAL_LLM=true
SERVICE_LLM_MODE=gemini
```

### 18-2. fail-closed 정책
- 입력값에서 민감정보 패턴(연락처/주소/주민번호/계좌/금액 등)을 탐지
- 탐지 시 LLM 호출을 아예 차단하고 검색 결과만 반환
- API 응답에 `blocked_fields`를 포함해 어떤 필드가 차단 원인인지 표시

### 18-3. 구조화 로그
- `llm_mode_config`: 현재 primary/fallback 모드 기록
- `llm_call_start`: provider, 후보 개수 기록
- `llm_call_success`: provider 성공 기록
- `llm_call_failure`: provider 실패 기록
- `llm_fallback_trigger`: 폴백 전환 기록
- `llm_call_blocked`: 민감정보 차단 기록

운영 시 로그 기반으로 장애/전환 원인을 추적할 수 있다.

### 18-4. 검색 튜닝
- 지역/대상/생애주기/관심주제 가중치 상향
- 지역 불일치 시 경미한 감점
- 노트 토큰 매칭 가중치 상향
- 로컬 서비스 및 최신 수정일 가산점 적용

### 18-5. 테스트 보강
- `analyze_profile_safety` 탐지 테스트
- fail-closed API 테스트
- retrieval 랭킹 우선순위 테스트
- 외부 LLM 게이트 차단 테스트
