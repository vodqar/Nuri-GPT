--

## 📋 목차

1. [인증 (Authentication)](#-인증-authentication)
2. [API 엔드포인트](#-api-엔드포인트)

---

## 🔐 인증 (Authentication)

### Auth (API) — prefix: `/api/auth`

| Method | Path | Description | Content-Type | 주요 파라미터 |
|--------|------|-------------|-------------|--------------|
| POST | `/api/auth/login` | 사용자 로그인 (access_token 반환 + httpOnly refresh_token 쿠키 설정) | `application/json` | `email`, `password` |
| POST | `/api/auth/refresh` | 토큰 갱신 (httpOnly 쿠키 기반) | `application/json` | - (쿠키에서 refresh_token 읽음) |
| POST | `/api/auth/logout` | 로그아웃 (쿠키 삭제 + 세션 무효화) | `application/json` | - |

### 인증 방식

- **access_token**: 메모리에만 저장 (localStorage 사용 금지 - XSS 방지)
- **refresh_token**: httpOnly, Secure, SameSite 쿠키로만 관리
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
| POST | `/api/upload/memo` | 수기 메모 이미지 업로드 + OCR | `multipart/form-data` | ✅ | `file` (user_id는 JWT에서 추출) |
| POST | `/api/upload/memo/text` | 텍스트 직접 입력 + 정규화 | `application/json` | ❌ | `text`, `child_name?` |
| POST | `/api/upload/template` | 빈 템플릿 이미지 업로드 + 계층 구조 분석 + DB 등록 | `multipart/form-data` | ✅ | `file`, `template_name` (user_id는 JWT에서 추출) |

### Template (API) — prefix: `/api/templates`

| Method | Path | Description | Content-Type | 인증 필요 | 주요 파라미터 |
|--------|------|-------------|-------------|-----------|--------------|
| GET | `/api/templates` | 템플릿 목록 조회 (활성화된 템플릿만, sort_order 순) | `application/json` | ✅ | `template_type?`, `is_default?`, `is_active?` (기본값 true, user_id는 JWT에서 추출) |
| GET | `/api/templates/{template_id}` | 특정 템플릿 상세 조회 | `application/json` | ✅ | `template_id` (UUID, path) |
| DELETE | `/api/templates/{template_id}` | 템플릿 소프트 삭제 (is_active=false) | - | ✅ | `template_id` (UUID, path) |
| PATCH | `/api/templates/{template_id}` | 템플릿 정보 수정 (이름 등) | `application/json` | ✅ | `template_id` (UUID, path), `name?`, `sort_order?`, `is_default?` |
| PUT | `/api/templates/order` | 템플릿 순서 일괄 변경 | `application/json` | ✅ | `orders` (Array: `{id, sort_order}`) |

### Generate (API) — prefix: `/api/generate`

| Method | Path | Description | Content-Type | 인증 필요 | 주요 파라미터 |
|--------|------|-------------|-------------|-----------|--------------|
| POST | `/api/generate/log` | 관찰일지 생성 (자동 저장). `template_id`로 생성 시 해당 템플릿의 `last_used_at` 자동 업데이트 | `application/json` | ✅ | `semantic_json?`, `ocr_text?`, `template_id?`, `additional_guidelines?`, `child_age` (0-5, 필수) (응답에 `updated_activities`, `journal_id` 포함) |
| POST | `/api/generate/regenerate` | 코멘트 기반 부분 재생성 | `application/json` | ✅ | `original_semantic_json`, `current_activities`, `comments`, `additional_guidelines?` |

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
| PUT | `/api/users/me` | 현재 사용자 정보(원장님 지침 등) 업데이트 | `application/json` | ✅ | `tone_and_manner?`, `kindergarten_name?`, `role?` (admin/org_manager/user) |
| DELETE | `/api/users/me` | 현재 사용자 계정 삭제 | - | ✅ | - |
| GET | `/api/users/{user_id}` | 특정 사용자 정보 조회 (본인만) | `application/json` | ✅ | `user_id` (UUID, path) - 본인 확인 |
| PUT | `/api/users/{user_id}` | 특정 사용자 정보 업데이트 (본인만) | `application/json` | ✅ | `user_id` (UUID, path), `tone_and_manner?`, `kindergarten_name?` - 본인 확인 |

### 상세 스키마

각 엔드포인트의 상세 요청/응답 스키마는 `app/schemas/` 디렉토리 참조 또는 Swagger UI (`/docs`)에서 확인 가능합니다.

---


> 마지막 업데이트: 2026-04-09 (파일 검증 개선 - MIME 타입에서 확장자 추론 지원, blob 파일명 처리)
>
> 이전 업데이트: 2026-04-07 (사용자 role 필드 추가 - admin/org_manager/user, DB 마이그레이션 적용)