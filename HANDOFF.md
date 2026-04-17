# Handoff Document — 범용 사용자 설정(User Preferences) 시스템 + 인삿말 지역 기억

*Last Updated: 2026-04-17*

---

## 🎯 Goal

인삿말 생성기에서 선택한 지역을 계정 단위로 저장하여, 다른 기기에서 로그인해도 자동 선택되도록 구현. 이 저장 메커니즘은 향후 다른 기능에서도 범용적으로 사용할 수 있도록 설계.

---

## ✅ Current Progress

### 완료된 작업 (9단계 전부 완료)

1. **DB 마이그레이션** — `user_preferences` 테이블 생성 (복합 PK: user_id + key, JSONB value, RLS)
2. **데이터 이관** — 기존 `users.preferred_region` → `user_preferences`(key=`greeting.preferred_region`) 이관 후 컬럼 제거
3. **Backend 모델/스키마/레포지토리** — `UserPreferenceRepository` (get_all, get, upsert, upsert_many, delete)
4. **Backend API** — `GET/PATCH /users/me/preferences` 엔드포인트 추가
5. **Backend auth 응답 확장** — login/refresh/signup 응답에 `preferences: Dict[str, Any]` 포함
6. **Backend 인삿말 엔드포인트 수정** — `UserUpdate(preferred_region=...)` → `pref_repo.upsert("greeting.preferred_region", region)`
7. **Frontend authStore** — User 타입에 `preferences: Record<string, any>` 추가, `updatePreferences` 액션 추가
8. **Frontend 인삿말 페이지** — `user.preferred_region` → `user.preferences['greeting.preferred_region']`, 생성 후 즉시 updatePreferences 호출
9. **문서 업데이트** — API_REFERENCE.md, ARCHITECTURE.md (backend+frontend) 업데이트

### 검증 결과
- `python3 -m py_compile` 전체 통과
- `npx tsc --noEmit` 에러 없음

---

## 🔧 What Worked

- `user_preferences` 테이블의 key-value(JSONB) 설계가 스키마 변경 없이 새 설정값 추가 가능
- `{feature}.{name}` 네이밍 컨벤션으로 설정 키의 충돌 방지
- auth 응답(login/refresh/signup)에 preferences를 포함시켜 별도 API 호출 없이 초기 로드
- 프론트엔드 `updatePreferences` 액션으로 생성 즉시 상태 갱신 (백엔드 저장과 프론트 상태 동기화)

---

## ⚠️ What Didn't Work / Gotchas

- **auth.py Dependency 주입**: `Depends(lambda: UserPreferenceRepository(get_supabase_client()))` 패턴 사용. 정석적인 FastAPI Depends 체인(`get_user_preference_repository`)을 사용하면 함수가 async generator이므로 auth 엔드포인트에서 기존 동기 Supabase 클라이언트와 충돌 가능. 현재 람다 방식으로 우회했으나, 장기적으로는 DI 리팩토링 필요
- **JSONB 기본값**: `DEFAULT '{}'::jsonb` 작성 시 따옴표 이스케이프 주의 — `'{}'`가 아닌 `"{}"` 사용하면 JSON 파싱 에러 발생

---

## 📋 Next Steps

- **E2E 검증**: 로그인 → 지역 선택 → 인삿말 생성 → 로그아웃 → 재로그인 시 지역 자동 선택 확인
- **할당량 연동**: 인삿말 생성 시 UsageService 할당량 차감 로직 추가
- **auth.py DI 리팩토링**: 람다 Dependency → 정식 async generator Depends로 전환
- **프론트엔드 preferences API 서비스**: `PATCH /users/me/preferences` 직접 호출 서비스 함수 (현재는 authStore.updatePreferences로 메모리만 갱신, 새로고침 시 백엔드에서 재조회)
- **기존 테스트 수정**: `cheat-data.ts`, `useTemplateManagement.ts` 등 기존 TS 에러 수정 (본 작업과 무관)

---

## 🏷️ Key Files

| 파일 | 역할 |
|------|------|
| `nuri-gpt-backend/app/db/models/user_preference.py` | UserPreference 모델 (Base, Create, InDB) |
| `nuri-gpt-backend/app/db/repositories/user_preference_repository.py` | UserPreferenceRepository (get_all, upsert, upsert_many, delete) |
| `nuri-gpt-backend/app/schemas/user_preference.py` | PreferencesResponse, PreferencesUpdateRequest 스키마 |
| `nuri-gpt-backend/app/api/endpoints/user.py` | GET/PATCH /users/me/preferences 엔드포인트 |
| `nuri-gpt-backend/app/api/endpoints/auth.py` | login/refresh/signup에 preferences 포함 |
| `nuri-gpt-backend/app/api/endpoints/greeting.py` | 인삿말 생성 시 greeting.preferred_region 저장 |
| `nuri-gpt-backend/app/schemas/auth.py` | UserAuthInfo에 preferences 필드 추가 |
| `nuri-gpt-frontend/frontend/src/store/authStore.ts` | User.preferences + updatePreferences 액션 |
| `nuri-gpt-frontend/frontend/src/features/greeting/pages/GreetingPage.tsx` | preferences에서 지역 읽기/쓰기 |
| `nuri-gpt-frontend/frontend/src/features/greeting/hooks/useGreeting.ts` | preferredRegion을 preferences에서 읽기 |

---

## 📐 Architecture Summary

```
DB: user_preferences (user_id UUID, key VARCHAR, value JSONB, updated_at TIMESTAMPTZ)
  PK: (user_id, key) | RLS: 본인만 읽기/쓰기

Backend:
  POST /api/auth/login  → UserAuthInfo(preferences={...})
  POST /api/auth/refresh → UserAuthInfo(preferences={...})
  POST /api/auth/signup  → UserAuthInfo(preferences={...})
  GET  /api/users/me/preferences → { preferences: { "greeting.preferred_region": "서울특별시 강남구" } }
  PATCH /api/users/me/preferences → upsert 복수 키
  POST /api/greeting/generate → 내부적으로 pref_repo.upsert("greeting.preferred_region", region)

Frontend:
  authStore.user.preferences: Record<string, any>
  authStore.updatePreferences(prefs) → 메모리 즉시 갱신
  GreetingPage → user.preferences['greeting.preferred_region']로 초기값 로드
  생성 버튼 클릭 → updatePreferences({...prefs, 'greeting.preferred_region': selectedRegion})
```

---

## 📜 이전 작업 기록

### 인삿말 생성기 백엔드 (2026-04-16 완료)
- WeatherService (단기/중기예보 분기), GreetingService (날씨+날짜+절기→Dify Chatflow)
- POST /api/greeting/generate, 270개 시군구 매핑, 27개 단위 테스트 통과
- **Dify Chatflow 타임아웃 이슈**: blocking 모드 + 10초 타임아웃으로 지속 타임아웃. 상세: `report/2026-04-16-dify-chatflow-timeout.md`
