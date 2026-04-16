--

## 📋 목차

1. [인증 (Authentication)](#-인증-authentication)
2. [API 엔드포인트](#-api-엔드포인트)

---

## 🔐 인증 (Authentication)

### Auth (API) — prefix: `/api/auth`

| Method | Path | Description | Content-Type | 주요 파라미터 |
|--------|------|-------------|-------------|--------------|
| POST | `/api/auth/login` | 사용자 로그인 (access_token 반환 + httpOnly refresh_token/remember_me 쿠키 설정) | `application/json` | `email`, `password`, `remember` |
| POST | `/api/auth/refresh` | 토큰 갱신 (httpOnly 쿠키 기반) | `application/json` | - (쿠키에서 refresh_token 읽음) |
| POST | `/api/auth/logout` | 로그아웃 (쿠키 삭제 + 세션 무효화) | `application/json` | - |

### 인증 방식

- **access_token**: 메모리에만 저장 (localStorage 사용 금지 - XSS 방지)
- **refresh_token**: httpOnly, Secure, SameSite 쿠키로만 관리
- **remember 정책**: 로그인 시 `remember=true`면 persistent 쿠키(`max_age=7일`), `remember=false`면 세션 쿠키
- **remember_me 쿠키**: refresh token rotation 시 remember 정책 유지를 위한 보조 httpOnly 쿠키
- **API 요청**: `Authorization: Bearer <access_token>` 헤더 필요
- **토큰 갱신**: 401 응답 시 `/api/auth/refresh`로 자동 갱신 후 재요청

---

## 📡 API 엔드포인트

### Health Check

| Method | Path | Description | 인증 필요 |
|--------|------|-------------|-----------|
| GET | `/` | 루트 헬스체크 | ❌ |
| GET | `/health` | 상세 헬스체크 (uptime 포함) | ❌ |

### Upload (API) — prefix: `/api`

| Method | Path | Description | Content-Type | 인증 필요 | 주요 파라미터 |
|--------|------|-------------|-------------|-----------|--------------|
| POST | `/api/upload/memo` | 수기 메모 이미지 업로드 + OCR (분석 할당량 차감) | `multipart/form-data` | ✅ | `file` (user_id는 JWT에서 추출) |
| POST | `/api/upload/memo/text` | 텍스트 직접 입력 + 정규화 (LLM 미사용) | `application/json` | ❌ | `text`, `child_name?` |
| POST | `/api/upload/template` | 빈 템플릿 이미지 업로드 + 분석 + DB 등록 (분석 할당량 차감) | `multipart/form-data` | ✅ | `file`, `template_name` |
| POST | `/api/upload/template/analyze` | 템플릿 이미지 분석 전용 (분석 할당량 차감) | `multipart/form-data` | ✅ | `file` |

### Template (API) — prefix: `/api/templates`

| Method | Path | Description | Content-Type | 인증 필요 | 주요 파라미터 |
|--------|------|-------------|-------------|-----------|--------------|
| POST | `/api/templates` | 템플릿 생성 — `structure_json` + 선택적 이미지로 DB 등록. 이미지 없으면 수동 트랙 (file_storage_path=null) | `multipart/form-data` | ✅ | `template_name`, `structure_json` (JSON 문자열), `file?` (user_id는 JWT에서 추출) |
| GET | `/api/templates` | 템플릿 목록 조회 (활성화된 템플릿만, sort_order 순) | `application/json` | ✅ | `template_type?`, `is_default?`, `is_active?` (기본값 true, user_id는 JWT에서 추출) |
| GET | `/api/templates/{template_id}` | 특정 템플릿 상세 조회 | `application/json` | ✅ | `template_id` (UUID, path) |
| DELETE | `/api/templates/{template_id}` | 템플릿 소프트 삭제 (is_active=false) | - | ✅ | `template_id` (UUID, path) |
| PATCH | `/api/templates/{template_id}` | 템플릿 정보 수정 (이름 등) | `application/json` | ✅ | `template_id` (UUID, path), `name?`, `sort_order?`, `is_default?` |
| PUT | `/api/templates/order` | 템플릿 순서 일괄 변경 | `application/json` | ✅ | `orders` (Array: `{id, sort_order}`) |

### Generate (API) — prefix: `/api/generate`

| Method | Path | Description | Content-Type | 인증 필요 | 주요 파라미터 |
|--------|------|-------------|-------------|-----------|--------------|
| POST | `/api/generate/log` | 관찰일지 생성 (자동 저장). (생성 할당량 차감) | `application/json` | ✅ | `semantic_json?`, `ocr_text?`, `template_id?`, `child_age` (필수) |
| POST | `/api/generate/regenerate` | 코멘트 기반 부분 재생성 (버전 관리 지원). (생성 할당량 차감) | `application/json` | ✅ | `original_semantic_json`, `current_activities`, `comments`, `group_id?` |

### Journal (API) — prefix: `/api/journals`

| Method | Path | Description | Content-Type | 인증 필요 | 주요 파라미터 |
|--------|------|-------------|-------------|-----------|--------------|
| GET | `/api/journals` | 사용자의 관찰일지 목록 조회 (최신순) | `application/json` | ✅ | `limit?` (기본: 20, 최대: 100), `offset?` (기본: 0) (user_id는 JWT에서 추출) |
| GET | `/api/journals/{journal_id}` | 특정 관찰일지 상세 조회 | `application/json` | ✅ | `journal_id` (UUID, path) |
| GET | `/api/journals/group/{group_id}` | 그룹 히스토리 조회 | `application/json` | ✅ | `group_id` (UUID, path) |
| DELETE | `/api/journals/group/{group_id}` | 그룹 삭제 | - | ✅ | `group_id` (UUID, path) |

### User (API) — prefix: `/api/users`

| Method | Path | Description | Content-Type | 인증 필요 | 주요 파라미터 |
|--------|------|-------------|-------------|-----------|--------------|
| GET | `/api/users/me` | 현재 사용자 정보(톤앤매너 포함) 조회 | `application/json` | ✅ | - (JWT에서 user_id 추출) |
| GET | `/api/users/me/usage` | 현재 사용자 사용량(할당량) 정보 조회 | `application/json` | ✅ | - (JWT에서 user_id 추출) |
| PUT | `/api/users/me` | 현재 사용자 정보(원장님 지침 등) 업데이트 | `application/json` | ✅ | `tone_and_manner?`, `kindergarten_name?`, `role?` |
| DELETE | `/api/users/me` | 현재 사용자 계정 삭제 | - | ✅ | - |
| GET | `/api/users/{user_id}` | 특정 사용자 정보 조회 (본인만) | `application/json` | ✅ | `user_id` |
| PUT | `/api/users/{user_id}` | 특정 사용자 정보 업데이트 (본인만) | `application/json` | ✅ | `user_id`, `tone_and_manner?` |

### Greeting (API) — prefix: `/api/greeting`

| Method | Path | Description | Content-Type | 인증 필요 | 주요 파라미터 |
|--------|------|-------------|-------------|-----------|--------------|
| POST | `/api/greeting/generate` | 알림장 인삿말 생성 (날씨/날짜/절기/공휴일/기념일/잡절 맥락 기반) | `application/json` | ✅ | `region` (시군구명), `target_date` (YYYY-MM-DD) |

#### Greeting Dify inputs 상세

| Key | Source | Description |
|-----|--------|-------------|
| `date_info` | GreetingService | 날짜+요일 (예: "2026년 5월 5일 (화요일)") |
| `month_week` | GreetingService | 월 내 주차 (예: "5월 1주차") |
| `weather_context` | WeatherService | 날씨 요약 (예: "맑음, 최고 22℃") |
| `seasonal_info` | SpecialDayService | 24절기 구간 (예: "곡우(4월 20일) ~ 소만(5월 21일)") |
| `holiday_info` | SpecialDayService | 공휴일명 or "해당 없음" (음력공휴일·대체공휴일·임시공휴일 포함) |
| `anniversary_info` | SpecialDayService | 기념일명 or "해당 없음" (스승의날, 어버이날 등) |
| `sundry_day_info` | SpecialDayService | 잡절명 or "해당 없음" (단오, 한식 등) |

### 상세 스키마

각 엔드포인트의 상세 요청/응답 스키마는 `app/schemas/` 디렉토리 참조 또는 Swagger UI (`/docs`)에서 확인 가능합니다.

---


> 마지막 업데이트: 2026-04-16 (특일 정보 API 연동 — SpecialDayService 신규, Dify inputs에 anniversary_info/sundry_day_info 추가)
>
> 이전 업데이트: 2026-04-16 (알림장 인삿말 생성기 — POST /api/greeting/generate 신설, 기상청 단기/중기예보 연동)
>
> 이전 업데이트: 2026-04-15 (로그인 유지 정책 반영 — `remember` 파라미터 및 refresh 쿠키 지속성 규칙 문서화)
>
> 이전 업데이트: 2026-04-15 (할당량 관리 시스템 구축 — /api/users/me/usage 신설, LLM 기반 API에 Quota Check 로직 통합)
>
> 이전 업데이트: 2026-04-14 (반자동 템플릿 생성 지원 — POST /upload/template/analyze 신설, POST /templates 신설, file_storage_path optional화)
> 이전 업데이트: 2026-04-10 (버전 관리 기능 추가 - group_id, journal_id 필드 추가, regenerate 시 버전 저장 로직 구현)