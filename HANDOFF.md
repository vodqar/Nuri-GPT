# Handoff Document — Security Remediation (Phase 1–5)

*Last Updated: 2026-04-21*

---

## 🎯 Goal

보안 평가 보고서(`report/2026-04-21-redteam-security-assessment.md`)에 따른 14개 취약점(V-01~V-14) 전수 수정 완료.

---

## ✅ Current Progress

### Phase 1 — 인증/인가 (완료)
- **V-01**: `upload_memo_text`에 `current_user` 의존성 추가
- **V-02**: `journals.py` — `get_journal`, `get_journal_group_history`, `delete_journal_group`에 소유권 검증 추가
- **V-03**: `template.py` — `get_template`, `delete_template`, `update_template`, `update_template_order`에 소유권 검증 추가
- **V-05**: 모든 엔드포인트·서비스의 `str(e)` → 제네릭 메시지 교체 (auth, user, upload, template, generate, greeting, storage)

### Phase 3 — 인프라 강화 (완료)
- **V-06**: CORS `allow_methods`/`allow_headers` 제한적 설정
- **V-07**: `file_validator.py`에 `filetype` 기반 매직넘버 검증 추가
- **V-08**: `slowapi` Rate Limiting — `app/core/rate_limiter.py` 신규 모듈(순환 임포트 해결), 엔드포인트별 데코레이터 적용
- **V-09**: `SecurityHeadersMiddleware` 추가 (X-Content-Type-Options, X-Frame-Options, CSP, HSTS 등)
- **V-10**: 쿠키 `secure`/`samesite` 환경 분기 (`debug` 설정 기준)

### Phase 4 — 정책/최적화 (완료)
- **V-11**: `auth.py` 스키마에 비밀번호 복잡성 검증 추가 (대문자+소문자+숫자)
- **V-12**: RLS 정책 `auth.uid()` → `(select auth.uid())` 최적화 + 중복 permissive 정책 병합
- **V-13**: `user.py`에서 미사용 `GET /{user_id}`, `PUT /{user_id}` 엔드포인트 제거
- **V-14**: FK 인덱스 추가 (Supabase MCP 마이그레이션 완료)

### Phase 5 — V-04 anon_key 전환 + 코드 품질 (완료)
- **V-04**: 모든 엔드포인트 Repository를 `anon_key` + 사용자 JWT 기반 RLS 적용 팩토리(`*_with_rls`)로 전환
- `create_rls_client(token)`: 요청별 anon_key 클라이언트 생성, `postgrest.auth(token)` 설정
- `get_current_user` 확장: JWT 토큰도 함께 반환 (`"token"` 키 추가)
- 코드 품질: `print()` → `logger`, `str(e)` → 고정 메시지

### slowapi `request` 파라미터 이슈 수정 (완료)
- `slowapi` 데코레이터가 함수 시그니처에서 `request: Request` 파라미터를 요구
- `upload.py`, `generate.py`, `greeting.py`에서 `http_request: Request` → `request: Request`로 이름 변경
- Pydantic 요청 본체 파라미터명 충돌 해결: `request` → `log_request`, `regen_request`, `greeting_request`
- 내부 참조 모두 업데이트 완료

### 테스트 수정 완료 (184 passed, 0 failed)
- `conftest.py`에 `limiter.enabled = False` 추가 (Rate Limiter 테스트 비활성화)
- 소유권 검증 테스트: `mock_current_user` override + `user_id` 일치시킴 (journals, templates)
- 매직넘버 검증 테스트: 실제 PNG/JPEG 매직넘버 바이트 사용 (`_MINIMAL_PNG`, `_MINIMAL_JPEG`)
- `usage_service` mock 추가 (할당량 429 방지)
- `user.py` 버그 수정: `except Exception`이 `HTTPException(404)`를 삼키는 문제 → `except HTTPException: raise` 추가
- V-05 메시지 변경 반영: `"LLM 생성 서비스 예외"` → `"일지 생성 서비스 오류"`
- regenerate 테스트 3개: `mock_usage_service` 파라미터 및 `dependency_overrides` 누락 수정
- 통합 테스트: `vision_service.extract_template_structure` AsyncMock → MagicMock (동기 메서드)

---

## ⚠️ What Didn't Work / Gotchas

- **slowapi `request` 파라미터**: `limiter.limit` 데코레이터는 함수 시그니처에서 **정확히** `request`라는 이름의 `Request` 타입 파라미터를 찾음. `http_request` 등 다른 이름 사용 시 `Exception: No "request" or "websocket" argument` 에러 발생
- **`limiter.reset()` 미작동**: `reset()`은 저장소만 초기화, `enabled=False` 설정해야 실제로 비활성화됨
- **`except Exception`이 HTTPException 삼킴**: `user.py`의 `try/except Exception`이 먼저 발생한 `HTTPException(404)`를 포착하여 500으로 변환. `except HTTPException: raise`를 먼저 배치해야 함
- **매직넘버 검증 + BytesIO**: 테스트에서 `b"fake image content"`는 `filetype.guess()`가 `None` 반환 → 검증 실패. 실제 PNG(`\x89PNG...`)/JPEG(`\xff\xd8\xff\xe0...`) 매직넘버 필요
- **순환 임포트**: `rate_limiter.py`를 `app/main.py`에서 분리하지 않으면 `limiter` 참조 시 순환 임포트 발생 → 독립 모듈 `app/core/rate_limiter.py`로 해결
- **AsyncMock vs 동기 메서드**: `VisionService.extract_template_structure`는 동기 메서드인데 `AsyncMock`으로 설정하면 coroutine 객체가 반환되어 500 에러 발생. 동기 메서드는 반드시 `MagicMock` 사용

---

## 📋 Next Steps (우선순위 순)

1. **Supabase 마이그레이션 적용** — `supabase/migrations/20260421_rls_optimize_and_deduplicate.sql` 을 Supabase 대시보드나 CLI로 적용
2. **Supabase 대시보드 설정** — Leaked Password Protection 활성화, 토큰 만료 시간 조정

---

## 🏷️ Key Files Modified

| 파일 | 변경 내용 |
|------|-----------|
| `app/core/rate_limiter.py` | **신규** — `slowapi.Limiter` 인스턴스 (순환 임포트 방지) |
| `app/utils/file_validator.py` | V-07: 매직넘버 검증 (`filetype` 라이브러리) |
| `app/main.py` | V-06: CORS 제한, V-08: Limiter/RateLimitExceeded 핸들러, V-09: SecurityHeadersMiddleware |
| `app/api/endpoints/auth.py` | V-05: str(e) 제거, V-08: rate limit 데코레이터, V-10: 쿠키 환경 분기, V-11: 비밀번호 정책 연동 |
| `app/api/endpoints/upload.py` | V-01: 인증 추가, V-05: str(e) 제거, V-08: rate limit + `request` 파라미터 |
| `app/api/endpoints/journals.py` | V-02: 소유권 검증, V-05: str(e) 제거 |
| `app/api/endpoints/template.py` | V-03: 소유권 검증, V-05: str(e) 제거 |
| `app/api/endpoints/generate.py` | V-05: str(e) 제거, V-08: rate limit + `request`→`log_request`/`regen_request` |
| `app/api/endpoints/greeting.py` | V-05: str(e) 제거, V-08: rate limit + `request`→`greeting_request` |
| `app/api/endpoints/user.py` | V-05: str(e) 제거, V-13: 미사용 엔드포인트 제거, HTTPException re-raise 버그 수정 |
| `app/services/storage.py` | V-05: str(e) 제거 |
| `app/schemas/auth.py` | V-11: 비밀번호 복잡성 검증 (field_validator + regex) |
| `requirements.txt` | `filetype>=1.2.0`, `slowapi>=0.1.9` 추가 |
| `tests/conftest.py` | `limiter.enabled = False` 추가 |
| `tests/test_journals_api.py` | 소유권 검증 대응 (user_id 일치, current_user override) |
| `tests/test_template_api.py` | 소유권 검증 대응 (user_id 일치, current_user override) |
| `tests/test_storage.py` | 매직넘버 바이트 사용 |
| `tests/test_upload_api.py` | usage_service mock, PNG 매직넘버 |
| `tests/test_generate_api.py` | usage_service mock, 메시지 변경 반영, `*_with_rls` 의존성 override |
| `tests/test_template_upload.py` | usage_service mock, 매직넘버 바이트, 비전 어설션 |
| `tests/test_integration.py` | usage_service, vision_service mock, `*_with_rls` 의존성 override |
| `tests/test_user_api.py` | 404 응답 예상 (HTTPException re-raise 수정 반영), `*_with_rls` 의존성 override |
| `app/core/dependencies.py` | V-04: `*_with_rls` Repository 팩토리 추가, `get_current_user` 토큰 반환, `print()` → `logger` |
| `app/db/connection.py` | V-04: `create_rls_client(token)` 함수 추가 |
| `supabase/migrations/20260421_rls_optimize_and_deduplicate.sql` | V-12: RLS 최적화 + 중복 정책 병합 마이그레이션 |

---

## 📐 Security Architecture Summary

```
Rate Limiting:
  slowapi Limiter (app/core/rate_limiter.py)
  ├── auth: signup 5/min, login 10/min
  ├── generate: log 20/min, regenerate 20/min
  ├── greeting: generate 20/min, stream 20/min
  └── upload: memo 20/min, template/analyze 10/min

File Upload Validation:
  validate_file() → 확장자 + MIME + 매직넘버(filetype) 검증
  filetype 미설치 시 ImportError catch → 기존 동작 유지

Cookie Security:
  _set_auth_cookies() → debug=False: secure=True, samesite=strict
                       → debug=True:  secure=False, samesite=lax

Security Headers Middleware:
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Content-Security-Policy: default-src 'self'
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()

Password Policy:
  min_length=8, 대문자+소문자+숫자 필수 (LoginRequest, SignupRequest)
```

---

## 📜 이전 작업 기록

### 인삿말 생성기 백엔드 (2026-04-16 완료)
- WeatherService, GreetingService, POST /api/greeting/generate
- Dify Chatflow 타임아웃 이슈: `report/2026-04-16-dify-chatflow-timeout.md`

### 범용 사용자 설정 시스템 (2026-04-17 완료)
- `user_preferences` 테이블, `UserPreferenceRepository`, GET/PATCH /users/me/preferences
- auth 응답에 preferences 포함, 프론트엔드 preferences 연동
