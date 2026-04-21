# Security Notes

보안 평가 보고서(`report/2026-04-21-redteam-security-assessment.md`)에 따른 14개 취약점(V-01~V-14) 중 V-04를 제외한 13개 수정 완료.

---

## 1. Rate Limiting ✅ 수정 완료 (V-08)

**파일**: `app/core/rate_limiter.py`, 각 엔드포인트

**적용 내용**:
- `slowapi` 기반 애플리케이션 레벨 rate limit 구현
- 엔드포인트별 제한: auth signup 5/min, login 10/min, generate 20/min, greeting 20/min, upload 10~20/min
- `RateLimitExceeded` 예외 핸들러 등록

---

## 2. 미사용 `/{user_id}` 엔드포인트 ✅ 제거 완료 (V-13)

**파일**: `app/api/endpoints/user.py`

**적용 내용**: `GET /api/users/{user_id}`, `PUT /api/users/{user_id}` 엔드포인트 제거. 프론트엔드는 `/api/users/me` 패턴 사용 중.

---

## 3. 쿠키 보안 설정 ✅ 수정 완료 (V-10)

**파일**: `app/api/endpoints/auth.py`

**적용 내용**: `debug` 설정 기반 환경 분기
- 프로덕션(`debug=False`): `secure=True`, `samesite="strict"`
- 개발(`debug=True`): `secure=False`, `samesite="lax"`

---

## 4. 토큰 만료 시간 조정 (Supabase 설정)

**현황**: Supabase 기본값 사용 중 (access token: 1시간, refresh token: 2주).

**프로덕션 권장값**:
- access token: 15분 (Supabase 대시보드 → Auth → JWT expiry)
- refresh token: 7일

**조정 방법**: Supabase 대시보드 → Authentication → Settings → JWT Settings에서 변경. 코드 변경 불필요.

---

## 5. 미인증 엔드포인트 ✅ 수정 완료 (V-01)

**파일**: `app/api/endpoints/upload.py`

**적용 내용**: `POST /api/upload/memo/text`에 `current_user: dict = Depends(get_current_user)` 추가.

---

## 6. 소유권 검증 — Journal 엔드포인트 ✅ 수정 완료 (V-02)

**파일**: `app/api/endpoints/journals.py`

**적용 내용**: `GET /api/journals/{id}`, `GET /api/journals/group/{id}`, `DELETE /api/journals/group/{id}` 세 엔드포인트에 `current_user` 의존성 + `user_id` 소유권 확인 추가.

---

## 7. 소유권 검증 — Template 엔드포인트 ✅ 수정 완료 (V-03)

**파일**: `app/api/endpoints/template.py`

**적용 내용**: `GET /api/templates/{id}`, `DELETE /api/templates/{id}`, `PATCH /api/templates/{id}`, `PUT /api/templates/order` 네 엔드포인트에 `current_user` 의존성 + `user_id` 소유권 확인 추가.

---

## 8. 내부 오류 정보 노출 ✅ 수정 완료 (V-05)

**파일**: auth.py, user.py, upload.py, template.py, generate.py, greeting.py, storage.py

**적용 내용**: 모든 엔드포인트·서비스의 `str(e)` → 제네릭 메시지 교체. 서버 측 분기 로직(`if "User already registered" in str(e)` 등)은 유지.

---

## 9. 전 Repository service_role 키 사용 🔶 장기 과제 (V-04)

**파일**: `app/core/dependencies.py`

**현황**: 모든 Repository가 `get_supabase_admin_client()`로 초기화됨. DB 수준 RLS가 작동하지 않음. 현재 엔드포인트 레벨 소유권 검증이 방어선.

**전환 계획**: 일반 사용자 요청 경로를 `get_supabase_client()`(anon key, RLS 적용)로 전환. `admin_client`는 관리자 전용 작업에만 제한적 사용. 전환 시 RLS 정책이 실제 접근 패턴을 허용하는지 사전 검증 필요. 별도 세션에서 진행.

---

## 10. CORS 제한 ✅ 수정 완료 (V-06)

**파일**: `app/main.py`

**적용 내용**:
- `allow_methods`: `["*"]` → `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`
- `allow_headers`: `["*"]` → `["Authorization", "Content-Type", "Accept"]`

---

## 11. 파일 업로드 매직넘버 검증 ✅ 수정 완료 (V-07)

**파일**: `app/utils/file_validator.py`

**적용 내용**: `filetype` 라이브러리로 파일 시그니처(매직넘버) 검증 추가. 확장자·MIME와 함께 3중 검증 구조. `filetype` 미설치 시 기존 동작 유지(ImportError catch).

---

## 12. 보안 헤더 ✅ 수정 완료 (V-09)

**파일**: `app/main.py` (`SecurityHeadersMiddleware`)

**적용 내용**:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'self'` (프로덕션만)
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (프로덕션만)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

---

## 13. 비밀번호 정책 ✅ 수정 완료 (V-11)

**파일**: `app/schemas/auth.py`

**적용 내용**:
- `min_length=8` + 대문자·소문자·숫자 필수 (`field_validator` + regex)
- `LoginRequest`, `SignupRequest` 모두 적용
- 기존 사용자 비밀번호는 소급 적용되지 않으므로, 다음 로그인 시 변경 안내 필요
- Supabase 대시보드에서 Leaked Password Protection 활성화 권장

---

## 14. RLS 정책 최적화 ✅ 완료 (V-12)

**적용 내용**: 모든 테이블 RLS 정책 `auth.uid()` → `(select auth.uid())` 최적화 (Supabase MCP 마이그레이션)

---

## 15. FK 인덱스 추가 ✅ 완료 (V-14)

**적용 내용**: `observation_journals.template_id` FK 인덱스 추가, 미사용 인덱스 정리 (Supabase MCP 마이그레이션)

---

> 상세 취약점 목록, 재현 절차, 단계별 개선 로드맵은 `report/2026-04-21-redteam-security-assessment.md` 참조.

*Last updated: 2026-04-21*
