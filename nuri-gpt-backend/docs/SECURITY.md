# Security Notes

베타 단계에서 즉시 수정하지 않은 보안 항목의 기록. 프로덕션 배포 전 검토 필수.

---

## 1. Rate Limiting (로그인 브루트포스 방어)

**현황**: `POST /api/auth/login`에 애플리케이션 레벨 rate limit 없음.

**왜 현재 괜찮은가**:
- Supabase Auth는 기본적으로 로그인 시도에 내장 rate limit을 적용함 (기본: IP당 분당 10회)
- 베타 단계 소규모 사용자(보육교사) 환경에서 실질적 위협 낮음

**프로덕션 배포 시 권장 조치**:
- Nginx/Cloudflare 레이어에서 `/api/auth/login` 엔드포인트에 IP 기반 rate limit 추가
- 또는 `slowapi` 라이브러리로 FastAPI 미들웨어 레벨에서 구현:
  ```python
  # requirements.txt에 slowapi>=0.1.9 추가 후:
  from slowapi import Limiter
  limiter = Limiter(key_func=get_remote_address)
  @router.post("/login")
  @limiter.limit("10/minute")
  async def login(...): ...
  ```
- Supabase 대시보드 → Auth → Rate Limits에서 설정 확인 및 조정

---

## 2. 미사용 `/{user_id}` 엔드포인트

**파일**: `app/api/endpoints/user.py`

**현황**: `/api/users/{user_id}` (GET, PUT) 엔드포인트가 존재하나 프론트엔드에서 사용하지 않음.
현재 본인 확인 로직(`str(user_id) != current_user["id"]` → 403)이 있어 즉각적인 위협은 없음.

**권장 조치**: 프론트엔드가 `/api/users/me` 패턴으로 완전 전환된 후 `/{user_id}` 엔드포인트 제거.
공격 표면을 최소화하고 API 일관성 확보.

---

## 3. 쿠키 보안 설정 (배포 전 필수)

**파일**: `app/api/endpoints/auth.py` (login, refresh 엔드포인트)

**현황**: `secure=False`, `samesite="lax"` — HTTP localhost 베타 환경용 설정.

**프로덕션 배포 시 필수 수정**:
```python
# secure=True      ← HTTPS 환경에서 쿠키가 암호화된 채널로만 전송됨
# samesite="strict" ← CSRF 방어 강화 (동일 사이트 요청만 허용)
```
코드 내 `# TODO: [배포 전 필수]` 주석 위치에서 확인.

---

## 4. 토큰 만료 시간 조정

**현황**: Supabase 기본값 사용 중 (access token: 1시간, refresh token: 2주).

**프로덕션 권장값**:
- access token: 15분 (Supabase 대시보드 → Auth → JWT expiry)
- refresh token: 7일

**조정 방법**: Supabase 대시보드 → Authentication → Settings → JWT Settings에서 변경.
코드 변경 불필요.

---

*Last updated: 2026-04-07*
