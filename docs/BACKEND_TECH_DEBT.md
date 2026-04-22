# Backend 기술부채 보고서

> 작성일: 2026-04-21
> 대상: `nuri-gpt-backend/`
> 산출 범위: Python 소스 코드, 설정 파일, 의존성 정의

---

## 1. 보안 부채 (Security Debt)

### 1.1 쿠키 보안 설정 — 배포 전 미완료

- **위치**: `app/api/endpoints/auth.py` (3곳)
  - `signup()` 내 `TODO` 주석 (line ~108)
  - `login()` 내 `TODO` 주석 (line ~168)
  - `refresh_token()` 내 `TODO` 주석 (line ~226)
- **내용**: HTTPS 환경에서 `secure=True`, `samesite="strict"`로 변경 필요
- **현재**: `_set_auth_cookies()`가 `debug` 여부에 따라 `secure=False / samesite="lax"` 자동 분기
- **리스크**: 프로덕션 배포 시 `DEBUG=False`가 보장되지 않으면 refresh_token 탈취 및 CSRF 공격 가능성

### 1.2 보안 헤더 조건부 비활성화

- **위치**: `app/main.py` (line 78–80)
- **내용**: `debug=True`일 때 `Content-Security-Policy`, `Strict-Transport-Security` 미발급
- **리스크**: 개발/스테이집 환경 구분이 모호할 경우 운영 서버에서 보안 헤더 누락

---

## 2. 코드 품질/구조 부채

### 2.1 중복 Import

- **위치**: `app/api/endpoints/generate.py`
  - `from uuid import UUID`가 함수 내부에 3회 선언 (line ~55, ~91, ~167)
- **위치**: `app/api/endpoints/upload.py`
  - `from uuid import UUID` 2회 중복 (line ~56, ~202)
  - `from app.utils.file_validator ...` 3회 중복 (line ~57, ~149, ~203)
  - `from io import BytesIO` 2회 중복 (line ~81, ~230)
- **영향**: 가독성 저하, 린터/형식 검사 시 warning 유발

### 2.2 중첩 함수 정의 (재사용 불가)

- **위치**: `app/api/endpoints/generate.py` (line ~138–147)
- **내용**: `get_leaf_paths()`가 엔드포인트 함수 내부에 중첩 정의
- **영향**: 다른 모듈에서 재사용 불가, 단위 테스트 불가

### 2.3 Repository Factory DRY 위반

- **위치**: `app/core/dependencies.py`
- **내용**: Admin(RLS bypass) / RLS-enabled 버전의 거의 동일한 factory가 7쌍(14개) 존재
- **영향**: 신규 repository 추가 시 14줄 이상의 보일러플레이트 코드 필요

### 2.4 과도한 하드코딩 프롬프트

- **위치**: `app/services/llm.py`
  - `generate_updated_activities()` 시스템 프롬프트 (line ~314–333)
  - `generate_journal_content()` 시스템 프롬프트 (line ~663–691)
- **영향**: 프롬프트 튜닝 시 코드 수정 및 재배포 필요. 비개발자(기획/교육 전문가) 접근 불가

### 2.5 Dify API 호출 로직 중복

- **위치**: `app/services/llm.py`
- **내용**: `generate_observation_log()`, `generate_regenerated_activities()`, `generate_journal_content()` 3메서드가 SSE 스트리밍 파싱 로직을 거의 동일하게 중복 구현
- **영향**: 버그 수정(예: SSE 이벤트 파싱 오류) 시 3곳 동시 수정 필요 — 누락 위험

### 2.6 광범위한 예외 포장

- **위치**: `app/api/endpoints/auth.py`
  - `except Exception` → `AuthenticationError` 변환 (line ~132, ~193, ~251)
- **영향**: DB 연결 끊김, Supabase 서버 오류 등 내부 시스템 오류가 사용자에게 "로그인 중 오류"로만 노출되어 원인 분석 및 모니터링 어려움

---

## 3. 성능/확장성 부채

### 3.1 Async 뷰 내 동기 I/O 블로킹

- **위치**: `app/services/llm.py`
  - `generate_observation_log()`: `requests.post(..., stream=True, timeout=120)` (line ~86)
  - `generate_regenerated_activities()`: 동일 패턴 (line ~521)
  - `generate_journal_content()`: 동일 패턴 (line ~729)
- **영향**: `requests`는 동기(blocking) 라이브러리. FastAPI 이벤트 루프 전체가 120초 정지되어 다른 요청(로그인, 조회 등) 동시 처리 불가

### 3.2 WeatherService ThreadPoolExecutor 오버헤드

- **위치**: `app/services/weather.py` (line ~542)
- **내용**: 중기육상/기온 API 2개를 `ThreadPoolExecutor`로 병렬 호출
- **영향**: FastAPI 이벤트 루프 내에서 스레드풀 생성/관리 오버헤드 발생. `asyncio.gather` + 비동기 HTTP 클라이언트 권장

### 3.3 SupabaseManager 싱글톤 스레드 안전성

- **위치**: `app/db/connection.py`
- **내용**: `__new__`로 싱글톤 보장하나 `_client` 초기화 시 thread-safe 미보장
- **영향**: 멀티프로세스/멀티스레드 환경(예: Gunicorn worker)에서 중복 초기화 가능성

---

## 4. 의존성/설정 부채

### 4.1 버전 제약 누락

- **위치**: `requirements.txt` (line 36)
- **내용**: `requests`에 버전 제약 없음 (`requests>=2.31.0` 등 미지정)
- **영향**: 의존성 업그레이드 시 예상치 못한 breaking change로 운영 장애 가능

### 4.2 미사용 설정값

- **위치**: `.env.example` (line 38–41)
- **내용**: `KMA_MID_API_KEY`, `KMA_SPECIAL_DAY_API_KEY`가 설정 파일에만 존재
- **영향**: `weather.py`는 `kma_api_key`만 사용하고 중기예보/특일 API에 대한 별도 키 활용 안 함. 설정 혼란 및 관리 부담

---

## 5. 데이터베이스/아키텍처 부채

### 5.1 Sync→Async 래퍼 중복

- **위치**: `app/db/repositories/*.py`
- **내용**: 모든 repository가 `run_sync(lambda: self.client.table(...)...)` 패턴 반복
- **영향**: Supabase 클라이언트 버전 업그레이드(v1→v2 등) 시 7개 이상 파일 동시 수정 필요

### 5.2 Admin/RLS 클라이언트 혼용 문서화 부재

- **위치**: `app/core/dependencies.py`
- **내용**: 일부 엔드포인트는 Admin(RLS bypass), 일부는 RLS 적용으로 혼용
- **영향**: 신규 개발자가 잘못된 권한으로 API 작성 시 데이터 접근 제어 위반 가능

---

## 6. 수정 우선순위

| 우선순위 | 항목 | 위치 | 위험도 | 예상 공수 |
|---|---|---|---|---|
| **P0** | 쿠키 secure/samesite 배포 설정 | `auth.py` | 보안 | 소 |
| **P0** | Async 뷰 내 동기 requests 블로킹 | `llm.py` | 성능 | 중 |
| **P1** | Dify API 호출 중복 로직 추출 | `llm.py` | 유지보수 | 중 |
| **P1** | 중복 import/함수 정리 | `generate.py`, `upload.py` | 가독성 | 소 |
| **P2** | Repository factory DRY 적용 | `dependencies.py` | 구조 | 중 |
| **P2** | 프롬프트 외부 파일 분리 | `llm.py` | 유지보수 | 중 |
| **P2** | 광범위 예외 포장 개선 | `auth.py` | 안정성 | 소 |
| **P2** | WeatherService async 전환 | `weather.py` | 성능 | 중 |
| **P3** | requests 버전 제약 | `requirements.txt` | 안정성 | 소 |
| **P3** | SupabaseManager thread-safety | `connection.py` | 안정성 | 소 |

---

## 7. 예상 기대효과

### 보안
- 프로덕션 배포 시 수동 점검 없이도 refresh_token 탈취/CSRF 위험 자동 차단
- 환경별 보안 헤더 전략 명확화로 설정 누락 사고 방지

### 성능
- LLM 생성 요청 120초 대기 중에도 다른 API 응답 지연 사라짐
- 고동시 접속 시 스레드 고갈 및 context-switch 오버헤드 감소

### 유지보수
- 코드량 약 15~20% 감소, 신규 기능 추가 시 onboarding 시간 단축
- 프롬프트 외부화 시 비개발자가 파일만 수정하여 튜닝 가능 (배포 없이 실험)

### 안정성
- 예외 원인 분리로 운영 장애 MTTR 단축
- 사용자 불필요한 "로그인 중 오류" 재시도 감소

### 아키텍처
- 데이터 모델 변경 시 수정 지점 1곳으로 축소
- 신규 개발자의 잘못된 권한 API 작성 확률 감소

---

## 종합

| 관점 | Before | After |
|---|---|---|
| **보안** | 배포 시 쿠키 설정 수동 점검 필요 | 환경변수 자동 분기, 배포 누락 위험 제거 |
| **성능** | LLM 호출 시 전체 서버 멈춤 | 비동기 처리, 동시 요청 처리량 ↑ |
| **개발 속도** | 신규 repo 추가 시 14줄 복사 | 1줄 호출, 프롬프트는 파일만 교체 |
| **장애 대응** | 모든 오류가 "로그인 중 오류" | 원인 분리, 모니터링/알림 정확도 ↑ |
| **리팩토링 비용** | Supabase 교체 시 20+ 파일 수정 | Base class 1곳 수정 |

> 전체 수정 완료 시 예상 효과: **배포 안전성 향상 + 동시 사용자 처리량 증가 + 신규 기능 개발 속도 20~30% 단축**
