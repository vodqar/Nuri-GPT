# Nuri-GPT Red-Team Security Assessment Report

Pre-launch localhost 환경에서 코드 리뷰 및 수동 검증 기반으로 식별된 취약점 목록과 개선 로드맵.

---

## Executive Summary

총 **14개 취약점**을 식별했다. 그중 **Critical 3개**, **High 4개**, **Medium 4개**, **Low/Info 3개**이다. 가장 심각한 문제는 (1) 인증 없이 접근 가능한 엔드포인트, (2) 소유권 검증 누락으로 인한 타 사용자 데이터 접근, (3) 모든 데이터 쿼리가 RLS를 우회하는 service_role 키로 실행되는 구조적 설계이다. 이 세 가지가 결합하면 인증된 사용자가 타인의 관찰일지·템플릿·설정을 열람·수정·삭제할 수 있다.

---

## Finding Inventory

### V-01 · 미인증 엔드포인트 노출 — `POST /api/upload/memo/text`

| 항목 | 내용 |
|------|------|
| **심각도** | 🔴 Critical |
| **파일** | `nuri-gpt-backend/app/api/endpoints/upload.py:110-127` |
| **영향** | 인증 없이 누구나 텍스트 정규화 API를 호출할 수 있음. OCR 서비스 리소스 무단 사용 가능 |
| **원인** | `upload_memo_text` 함수에 `current_user: dict = Depends(get_current_user)` 의존성이 없음 |

**재현 절차**
```bash
# 인증 토큰 없이 호출 → 200 OK 반환
curl -X POST http://127.0.0.1:8001/api/upload/memo/text \
  -H "Content-Type: application/json" \
  -d '{"text":"임의 텍스트","child_name":"테스트"}'
```

**완화 방안**
- `current_user: dict = Depends(get_current_user)` 의존성 추가
- 또는 해당 엔드포인트가 공개 의도라면 명시적 `public` 태그와 별도 라우터로 분리

---

### V-02 · 소유권 검증 누락 — Journal 엔드포인트

| 항목 | 내용 |
|------|------|
| **심각도** | 🔴 Critical |
| **파일** | `nuri-gpt-backend/app/api/endpoints/journals.py:42-82` |
| **영향** | 인증된 사용자가 다른 사용자의 관찰일지를 열람·삭제할 수 있음 |
| **원인** | `get_journal`, `get_journal_group_history`, `delete_journal_group` 세 엔드포인트 모두 `current_user` 의존성이 없으며, Repository 쿼리에 `user_id` 필터가 없음 |

**영향받는 엔드포인트**
- `GET /api/journals/{journal_id}` — `journals.py:42`
- `GET /api/journals/group/{group_id}` — `journals.py:59`
- `DELETE /api/journals/group/{group_id}` — `journals.py:69`

**재현 절차**
```bash
# 사용자 A의 토큰으로 사용자 B의 일지 열람
curl -H "Authorization: Bearer <USER_A_TOKEN>" \
  http://127.0.0.1:8001/api/journals/<USER_B_JOURNAL_ID>
# → 200 OK + 타 사용자 일지 데이터 반환
```

**완화 방안**
- 세 엔드포인트에 `current_user: dict = Depends(get_current_user)` 추가
- 조회/삭제 전 리소스의 `user_id`가 `current_user["id"]`와 일치하는지 확인
- 일치하지 않으면 403 반환

---

### V-03 · 소유권 검증 누락 — Template 엔드포인트

| 항목 | 내용 |
|------|------|
| **심각도** | 🔴 Critical |
| **파일** | `nuri-gpt-backend/app/api/endpoints/template.py:160-260` |
| **영향** | 인증된 사용자가 다른 사용자의 템플릿을 열람·수정·삭제·순서변경할 수 있음 |
| **원인** | `get_template`, `delete_template`, `update_template`, `update_template_order` 네 엔드포인트에 `current_user` 의존성이 없음 |

**영향받는 엔드포인트**
- `GET /api/templates/{template_id}` — `template.py:166`
- `DELETE /api/templates/{template_id}` — `template.py:186`
- `PATCH /api/templates/{template_id}` — `template.py:213`
- `PUT /api/templates/order` — `template.py:242`

**재현 절차**
```bash
# 사용자 A의 토큰으로 사용자 B의 템플릿 삭제
curl -X DELETE -H "Authorization: Bearer <USER_A_TOKEN>" \
  http://127.0.0.1:8001/api/templates/<USER_B_TEMPLATE_ID>
# → 204 No Content (삭제 성공)
```

**완화 방안**
- 네 엔드포인트에 `current_user` 의존성 추가
- 리소스 조회 후 `user_id` 일치 여부 확인, 불일치 시 403

---

### V-04 · 전 Repository service_role 키 사용 (RLS 전면 우회)

| 항목 | 내용 |
|------|------|
| **심각도** | 🟠 High |
| **파일** | `nuri-gpt-backend/app/core/dependencies.py:95-166` |
| **영향** | 모든 Repository가 `get_supabase_admin_client()`로 초기화됨 → DB 수준의 RLS가 전혀 작동하지 않음. V-02, V-03의 소유권 누락과 결합 시 즉시 타인 데이터 접근 가능 |
| **원인** | 설계상 편의를 위해 모든 데이터 쓰기를 service_role로 처리 |

**영향받는 Repository**
- `UserRepository` — `dependencies.py:97`
- `LogRepository` — `dependencies.py:103`
- `TemplateRepository` — `dependencies.py:109`
- `JournalRepository` — `dependencies.py:115`
- `UsageRepository` — `dependencies.py:121`
- `UserPreferenceRepository` — `dependencies.py:165`

**완화 방안 (구조적 개선)**
- 일반 사용자 요청 경로: `get_supabase_client()` (anon key, RLS 적용) 사용
- `admin_client`는 관리자 전용 작업(계정 삭제, 사용자 관리 등)에만 제한적 사용
- 전환 시 RLS 정책이 실제로 필요한 접근을 허용하는지 사전 검증 필요

---

### V-05 · 내부 오류 정보 노출 (Error Message Leakage)

| 항목 | 내용 |
|------|------|
| **심각도** | 🟠 High |
| **파일** | 다수 (upload.py, template.py, user.py, auth.py, generate.py, greeting.py, storage.py) |
| **영향** | 예외 메시지(`str(e)`)가 응답에 그대로 포함되어 DB 연결 정보, 스택트레이스, 외부 API 응답 구조 등이 노출될 수 있음 |

**대표 사례**
- `upload.py:106` — `detail=f"업로드 또는 OCR 처리 실패: {str(e)}"`
- `auth.py:125` — `raise AuthenticationError(f"회원가입 중 오류가 발생했습니다: {str(e)}")`
- `greeting.py:155` — SSE 스트림에서 `str(e)` 직접 전송
- `storage.py:173,242,276,297,323,414` — 모든 예외에 `str(e)` 포함

**완화 방안**
- 프로덕션에서는 `str(e)` 대신 고정 메시지 사용
- 상세 오류는 서버 로그에만 기록
- `greeting.py` SSE 에러 이벤트도 내부 메시지 노출 방지

---

### V-06 · CORS 과도 허용

| 항목 | 내용 |
|------|------|
| **심각도** | 🟠 High |
| **파일** | `nuri-gpt-backend/app/main.py:56-65` |
| **영향** | `allow_methods=["*"]`, `allow_headers=["*"]`, `allow_credentials=True` 조합으로 인해, 허용된 오리진에서는 모든 HTTP 메서드와 헤더로 크리덴셜 요청 가능. Debug 모드에서는 localhost 임의 포트가 추가 허용됨 |
| **원인** | 개발 편의를 위한 와일드카드 설정이 프로덕션 설정과 분리되지 않음 |

**완화 방안**
- `allow_methods`를 실제 사용 메서드(`GET`, `POST`, `PUT`, `PATCH`, `DELETE`)로 제한
- `allow_headers`를 `Authorization`, `Content-Type`으로 제한
- Debug 모드 regex는 프로덕션 빌드에서 비활성화 확인

---

### V-07 · 파일 업로드 MIME 스푸핑 가능

| 항목 | 내용 |
|------|------|
| **심각도** | 🟠 High |
| **파일** | `nuri-gpt-backend/app/utils/file_validator.py:75-122` |
| **영향** | 확장자와 `content_type` 헤더만 검증하고 파일 바이트의 매직넘버(시그니처)를 검증하지 않음. 악의적 파일을 `.jpg` 확장자와 `image/jpeg` 헤더로 위장하여 업로드 가능 |
| **원인** | `validate_file`이 `file.filename`과 `file.content_type`만 확인 |

**재현 절차**
```bash
# 악의적 파일을 image/jpeg로 위장
mv malicious.html test.jpg
curl -X POST -H "Authorization: Bearer <TOKEN>" \
  -F "file=@test.jpg;type=image/jpeg" \
  http://127.0.0.1:8001/api/upload/memo
# → 확장자 .jpg + MIME image/jpeg → 검증 통과
```

**완화 방안**
- 파일 바이트의 매직넘버(예: JPEG `FF D8 FF`, PNG `89 50 4E 47`) 검증 추가
- `python-magic` 또는 `filetype` 라이브러리 사용 권장

---

### V-08 · Rate Limiting 전면 부재

| 항목 | 내용 |
|------|------|
| **심각도** | 🟡 Medium |
| **파일** | `nuri-gpt-backend/app/main.py` (미들웨어 없음) |
| **영향** | 로그인 브루트포스, 회원가입 자동화, LLM 생성 API 남용, 파일 업로드 남용에 대한 보호 없음. Supabase 기본 제한에만 의존 |

**완화 방안**
- `slowapi` 또는 FastAPI 미들웨어로 엔드포인트별 rate limit 추가
- 우선순위: `POST /api/auth/login` (브루트포스), `POST /api/generate/*` (LLM 비용), `POST /api/upload/*` (스토리지 비용)
- 프로덕션에서는 Nginx/Cloudflare 레이어에서도 적용

---

### V-09 · 보안 헤더 전면 누락

| 항목 | 내용 |
|------|------|
| **심각도** | 🟡 Medium |
| **파일** | `nuri-gpt-backend/app/main.py` (미들웨어 없음) |
| **영향** | CSP, X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, X-XSS-Protection 헤더가 모두 없음. XSS, 클릭재킹, MIME 스니핑 공격에 취약 |

**완화 방안**
- Starlette `Middleware` 또는 `secure` 패키지로 보안 헤더 일괄 추가
- 최소: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy: default-src 'self'`
- 프로덕션: `Strict-Transport-Security: max-age=31536000; includeSubDomains`

---

### V-10 · 쿠키 보안 설정 미비 (개발용 하드코딩)

| 항목 | 내용 |
|------|------|
| **심각도** | 🟡 Medium |
| **파일** | `nuri-gpt-backend/app/api/endpoints/auth.py:30-34` |
| **영향** | `secure=False`, `samesite="lax"`가 하드코딩됨. HTTP 환경에서 쿠키가 네트워크에 평문 노출, CSRF 위험 증가 |
| **원인** | 개발/베타 환경을 위한 설정이 프로덕션 설정과 분리되지 않음 (TODO 주석만 존재) |

**완화 방안**
- `secure`와 `samesite` 값을 `settings.debug` 또는 환경 변수 기반으로 조건부 설정
- 프로덕션: `secure=True`, `samesite="strict"`

---

### V-11 · 비밀번호 정책 약화 + 유출 비밀번호 보호 비활성

| 항목 | 내용 |
|------|------|
| **심각도** | 🟡 Medium |
| **파일** | `nuri-gpt-backend/app/schemas/auth.py:17,25`; Supabase Auth 설정 |
| **영향** | `min_length=8`만 있고 복잡도 요구 없음. Supabase HaveIBeenPwned 유출 비밀번호 보호가 비활성화됨 |
| **원인** | 스키마에 복잡도 검증 미구현, Supabase 프로젝트 설정에서 기능 꺼짐 |

**완화 방안**
- Supabase 대시보드에서 Leaked Password Protection 활성화
- 스키마에 비밀번호 복잡도 검증 추가(대소문자, 숫자, 특수문자 조합)
- 또는 Supabase Auth 설정에서 최소 비밀번호 강도 상향

---

### V-12 · RLS 정책 성능 최적화 누락

| 항목 | 내용 |
|------|------|
| **심각도** | 🟢 Low / Info |
| **파일** | Supabase RLS 정책 (7개 테이블 전체) |
| **영향** | `auth.uid()` 대신 `(select auth.uid())` 패턴 미사용으로 행별 재평가 발생. 대규모 데이터에서 쿼리 성능 저하 |
| **출처** | Supabase Performance Advisor — 14건 WARN |

**영향받는 테이블**
- `users`, `observation_journals`, `templates`, `user_usages`, `user_logs`, `user_preferences`

**완화 방안**
- RLS 정책에서 `auth.uid()` → `(select auth.uid())` 로 변경
- [Supabase 가이드](https://supabase.com/docs/guides/database/postgres/row-level-security#call-functions-with-select) 참조

---

### V-13 · Unused Endpoints & Attack Surface

| 항목 | 내용 |
|------|------|
| **심각도** | 🟢 Low / Info |
| **파일** | `nuri-gpt-backend/app/api/endpoints/user.py:74-107,169-203` |
| **영향** | `GET /api/users/{user_id}`, `PUT /api/users/{user_id}` 엔드포인트가 프론트엔드에서 사용되지 않으나 존재함. 본인 확인 로직은 있으나 공격 표면 불필요하게 증가 |

**완화 방안**
- 프론트엔드 미사용 엔드포인트 제거
- 또는 관리자 전용 라우터로 이동

---

### V-14 · FK 인덱스 누락 및 기타

| 항목 | 내용 |
|------|------|
| **심각도** | 🟢 Low / Info |
| **파일** | Supabase DB 스키마 |
| **영향** | `observation_journals.template_id` FK에 커버링 인덱스 없음. 조인 쿼리 성능 저하. 미사용 인덱스 2개 존재 |

**완화 방안**
- `observation_journals.template_id`에 인덱스 추가
- 미사용 인덱스(`idx_templates_last_used_at`, `idx_journals_user_final_created`) 검토 후 제거

---

## Authorization Boundary Map

### 엔드포인트별 인가 상태

| 엔드포인트 | 인증 | 소유권 검증 | RLS 적용 | 위험도 |
|-----------|------|------------|---------|--------|
| `POST /api/auth/*` | N/A | N/A | N/A | — |
| `GET /api/users/me` | ✅ | ✅ (토큰 기반) | ❌ (admin) | 낮음 |
| `GET /api/users/{user_id}` | ✅ | ✅ (문자열 비교) | ❌ (admin) | 낮음 |
| `POST /api/upload/memo` | ✅ | ✅ | ❌ (admin) | 낮음 |
| **`POST /api/upload/memo/text`** | **❌** | **N/A** | **N/A** | **Critical** |
| `POST /api/upload/template` | ✅ | ✅ | ❌ (admin) | 낮음 |
| `POST /api/templates/` | ✅ | ✅ | ❌ (admin) | 낮음 |
| **`GET /api/templates/{id}`** | **❌** | **❌** | **❌ (admin)** | **Critical** |
| **`DELETE /api/templates/{id}`** | **❌** | **❌** | **❌ (admin)** | **Critical** |
| **`PATCH /api/templates/{id}`** | **❌** | **❌** | **❌ (admin)** | **Critical** |
| **`PUT /api/templates/order`** | **❌** | **❌** | **❌ (admin)** | **Critical** |
| `GET /api/templates/` | ✅ | ✅ (user_id 필터) | ❌ (admin) | 낮음 |
| `GET /api/journals/` | ✅ | ✅ (user_id 필터) | ❌ (admin) | 낮음 |
| **`GET /api/journals/{id}`** | **❌** | **❌** | **❌ (admin)** | **Critical** |
| **`GET /api/journals/group/{id}`** | **❌** | **❌** | **❌ (admin)** | **Critical** |
| **`DELETE /api/journals/group/{id}`** | **❌** | **❌** | **❌ (admin)** | **Critical** |
| `POST /api/generate/log` | ✅ | ✅ | ❌ (admin) | 낮음 |
| `POST /api/generate/regenerate` | ✅ | ✅ | ❌ (admin) | 낮음 |
| `POST /api/greeting/generate` | ✅ | ✅ | ❌ (admin) | 낮음 |
| `GET /api/greeting/regions` | ❌ | N/A | N/A | 낮음 (공개 데이터) |
| `GET /api/users/me/bootstrap` | ✅ | ✅ | ❌ (admin) | 낮음 |

---

## RLS-Compliant Target Architecture

### 현재 구조 (문제점)

```
Request → Endpoint → Repository(admin_client) → Supabase(RLS bypassed)
```

모든 데이터 접근이 `service_role` 키로 이루어져 DB 수준의 RLS가 무력화됨. 엔드포인트 레벨의 소유권 검증이 유일한 방어선이나, V-02, V-03에서 확인한 대로 다수 누락됨.

### 목표 구조

```
Request → Endpoint → Repository(client) → Supabase(RLS enforced)
                              ↓
                   AdminRepository(admin_client)  ← 관리자 전용 작업만
```

### 전환 단계

1. **Phase 1: 즉시 수정 (Quick Wins)**
   - V-01: `upload_memo_text`에 인증 추가
   - V-02: Journal 3개 엔드포인트에 `current_user` + 소유권 검증 추가
   - V-03: Template 4개 엔드포인트에 `current_user` + 소유권 검증 추가
   - V-05: `str(e)` 응답 노출 제거

2. **Phase 2: Repository 분리**
   - `dependencies.py`에 `get_<repo>_with_rls()` 팩토리 추가 (anon_key 클라이언트 주입)
   - 일반 사용자 요청 경로는 `*_with_rls` 의존성 사용
   - `admin_client`는 관리자 전용 엔드포인트(계정 삭제, 사용자 관리 등)에만 유지
   - RLS 정책이 실제 사용 패턴을 허용하는지 검증 (특히 `user_usages` INSERT/UPDATE)

3. **Phase 3: 인프라 강화**
   - Rate limiting 미들웨어 추가
   - 보안 헤더 미들웨어 추가
   - CORS 설정 프로덕션 분리
   - 쿠키 보안 설정 환경 분기
   - 파일 업로드 매직넘버 검증

4. **Phase 4: Supabase 설정 강화**
   - Leaked Password Protection 활성화
   - RLS 정책 `(select auth.uid())` 최적화
   - FK 인덱스 추가
   - 토큰 만료 시간 프로덕션 값 설정 (access: 15min, refresh: 7d)

---

## Phased Remediation Roadmap

| Phase | 기간 | 항목 | 전제조건 |
|-------|------|------|---------|
| **1** | 1-2일 | V-01, V-02, V-03, V-05 | 없음 |
| **2** | 3-5일 | V-04 (Repository 분리) | Phase 1 완료 + RLS 정책 검증 |
| **3** | 2-3일 | V-06, V-07, V-08, V-09, V-10 | Phase 2 완료 |
| **4** | 1일 | V-11, V-12, V-13, V-14 | Phase 3 완료 |

---

*Assessment Date: 2026-04-21*
*Environment: localhost (pre-launch)*
