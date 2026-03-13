# Session Notes (2026-02-24)

## 진행 내용 요약
- `socialpjt` 프로젝트 경로와 파일 존재 여부를 확인했다.
- 사용자는 이후 Codex와 함께 실제 코드 구현을 진행할 계획을 공유했다.
- 프론트엔드 코드 스타일/규칙 분석을 수행했다.
  - React + TypeScript + Vite 기반
  - 라우팅 분리 구조 (`App -> main/auth`)
  - 주석/포맷 규칙은 아직 완전 통일 전
- 사용자의 요청으로 `main` 외 `backend` 브랜치도 확인했다.
  - `origin/backend` 존재 확인
  - 로컬 추적 브랜치 `backend` 생성 및 체크아웃
  - Django 백엔드(계정/로그인/회원가입 관련) 코드 포함 확인
- 코드와 주석 스타일을 바탕으로 사용자 개발 성향을 추정해 전달했다.
  - 학습형/설명형, 기능 우선 실용형, 점진적 정리 스타일

## 현재 상태
- 현재 체크아웃 브랜치: `backend`
- 프로젝트 주요 스택
  - Frontend: React, TypeScript, Tailwind, Firebase
  - Backend: Django, MySQL

## 다음 작업 합의
- 내일부터 기능 단위로 설명을 받고 실제 구현 진행 예정
- 빠른 진행을 위해 시작 시 아래 3가지를 제공받기로 함
  1. 기능 요구사항
  2. 완료 조건(성공/실패 기준)
  3. 적용 범위(프론트/백/둘 다, 대상 브랜치)

## 참고
- 대화 내역 보존은 환경에 따라 달라질 수 있으므로,
  중요한 결정사항은 문서(`docs/`)에 기록하는 방식 권장.

## 운영 합의 (2026-02-27)
- 앞으로 진행하는 작업/대화는 이 문서에 요약 기록한다.
- 각 기록에는 요청 내용, 수행 내용, 결정 사항, 다음 작업을 포함한다.

## 환경 변수 관리 안내 (2026-03-11)
- `python-dotenv`를 `backend/requirements.txt`에 추가했으며, `manage.py`, `asgi.py`, `wsgi.py`에서 `.env`를 자동 로드한다.
- 루트 `.env` 파일에 `DJANGO_SECRET_KEY`, `PUBLIC_API_KEY` 등을 정의하고 `git`에는 커밋하지 않는다.
- 공공 API 연동 시 `PUBLIC_API_KEY`를 채우면 Django 설정(`settings.PUBLIC_API_KEY`)과 크롤러에서 자동으로 이를 사용한다.
