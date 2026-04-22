# 프론트엔드 기술부채 보고서

*작성일: 2026-04-21*
*대상: `nuri-gpt-frontend/frontend/`*

---

## Executive Summary

현재 프론트엔드 코드베이스에서 **구조적 비대화**, **의존성 잔여물**, **개발용 코드 프로덕션 잔존**, **타입 안전성 저하** 등 다중 기술부채가 확인되었다. 이들은 빌드 안정성, 유지보수 속도, 보안 노출면에 직접적인 영향을 준다. 본 보고서는 심각도 기반으로 항목을 분류하고 수정 시 기대효과를 정리한다.

---

## Finding Inventory

### 🔴 구조 / 아키텍처 부채

| ID | 항목 | 위치 | 심각도 | 설명 |
|----|------|------|--------|------|
| A-01 | `features/observation` 비대화 | `src/features/observation/` | High | 관찰일지 생성·히스토리·템플릿 관리·템플릿 편집이 단일 feature에 집중. components 11개, hooks 4개, utils 2개, cheat-data 포함. 기능별 분리 필요. |
| A-02 | feature 격리 원칙 위반 | `src/App.tsx:6` | Medium | `JournalHistoryPage`를 `features/observation/components/`에서 직접 import. `features/observation/pages/`는 비어있음. |
| A-03 | 빈 디렉토리 다수 | `dashboard/`, `components/ui/`, `components/ImageCropper/`, `components/common/`, `features/observation/pages/` | Low | 아키텍처상 존재하나 내용 없음. 신규 기여자 혼란 유발. |
| A-04 | Export 불일치 | `src/App.tsx:5` | Medium | `GreetingPage`는 default export, 나머지는 named export. `agents.md` 규칙("모든 컴포넌트는 Named Export") 위반. |
| A-05 | placeholder 라우트 | `src/App.tsx:32,36,37` | Medium | `dashboard`, `logs`, `insights`가 하드코딩된 `<div>` placeholder로 사용자 혼란 유발. |

### 🟠 의존성 / 빌드 부채

| ID | 항목 | 위치 | 심각도 | 설명 |
|----|------|------|--------|------|
| D-01 | 중복 이미지 크롭 라이브러리 | `package.json` | Medium | `react-image-crop`(코드 사용 중) + `react-easy-crop`(의존성에만 존재, 코드 미사용). 번들 크기 불필요 증가. |
| D-02 | `@types/sortablejs` 위치 오류 | `package.json:21` | Low | devDependencies로 이동 필요. 또한 `@dnd-kit/sortable`과 `sortablejs` 중복 가능성. |
| D-03 | `lucide-react` 버전 이상 | `package.json:26` | Medium | `^1.0.1`은 실제 존재하지 않는 메이저 버전. 잘못된 해석으로 예상치 못한 업데이트 또는 빌드 실패 위험. |
| D-04 | MSW 완전 비활성화 | `src/main.tsx:24-37` | High | mocks import 주석 처리. 개발/테스트 시 외부 API에 강결합되어 통합 테스트 및 CI 안정성 저하. |
| D-05 | `index.css` 과도한 테마 변수 | `src/index.css` (2062줄) | Low | Tailwind v4 사용 중인데 커스텀 변수가 과도하게 많아 스타일 추적 어려움. |

### 🟡 코드 품질 부채

| ID | 항목 | 위치 | 심각도 | 설명 |
|----|------|------|--------|------|
| C-01 | 대형 파일 | `ObservationPage.tsx`, `SideNavBar.tsx`, `JournalHistoryPage.tsx`, `TemplateStructureEditor.tsx`, `LogGenerationResultView.tsx` | Medium | 12KB~17KB. 단일 파일에 너무 많은 책임. 분리 시 가독성·테스트 용이성 ↑. |
| C-02 | `cheat-data.ts` 프로덕션 잔존 | `src/features/observation/cheat-data.ts` | High | 하드코딩된 샘플 데이터 + URL `?cheat=regenerate` 치트 모드. 프로덕션 코드에 개발용 잔해가 노출됨. |
| C-03 | `DummyLoginPage.tsx` 잔존 | `src/features/auth/DummyLoginPage.tsx` | High | 개발용 더미 로그인이 프로덕션 소스에 남아있음. 보안/오용 위험. |
| C-04 | `any` 타입 사용 | `authStore.ts`, `ToastContainer.tsx`, `useLoginForm.ts` 등 6개 파일 | Medium | `Record<string, any>`, `(window as any).addToast`, `catch (error: any)` 등. 컴파일 시 실수 미방지. |
| C-05 | 전역 `window.addToast` 노출 | `src/components/global/ToastContainer.tsx:46` | Medium | Toast를 window 전역에 붙여 `showToast` 유틸이 이에 의존. 외부 오염 및 테스트 어려움. |
| C-06 | window 이벤트 기반 인증 처리 | `src/hooks/useAuthInterceptor.ts` | Low | `auth:unauthorized` 커스텀 이벤트를 window에 의존. React 외부 메커니즘 의존. |

### 🔵 문서 / 기능 부채

| ID | 항목 | 위치 | 심각도 | 설명 |
|----|------|------|--------|------|
| F-01 | `TODO.md` 불일치 | `frontend/TODO.md` | Low | "Refresh Token 연동 구현"이 미완료로 표시되나, 실제 `api.ts`와 `authStore.ts`에 이미 구현되어 있음. 문서 동기화 필요. |
| F-02 | 레이아웃 오버플로우 반복 | `report/2026-04-14-overlay-overflow-misdiagnosis.md` | Medium | `overflow-hidden` 맹목적 적용으로 3회 수정. 근본 원인 분석 부재. |
| F-03 | `remember-me` 정책 불일치 | `report/2026-04-15-auth-remember-me-fix-plan.md` | Medium | 체크박스 값과 백엔드 쿠키 정책이 분리되어 UX/동작 불일치. |

### 🟣 테스트 부채

| ID | 항목 | 위치 | 심각도 | 설명 |
|----|------|------|--------|------|
| T-01 | feature 단위 테스트 부재 | `src/features/` 하위 전체 | High | 테스트가 `routes/`에만 2개 존재. 복잡한 feature 로직에 회귀 방지 장치 없음. |
| T-02 | MSW 비활성화로 인한 통합 테스트 어려움 | `src/main.tsx` | High | mocking 인프라가 무력화되어 외부 API 상태에 테스트가 좌우됨. |

### ⚪ 기타

| ID | 항목 | 위치 | 심각도 | 설명 |
|----|------|------|--------|------|
| M-01 | ESLint `react/recommended` 부재 | `eslint.config.js` | Low | `react-hooks`, `react-refresh`만 설정. JSX 관련 규칙 미적용. |
| M-02 | `eslint-disable` 주문 다수 | `ToastContainer.tsx` 3회, `useLoginForm.ts` 1회 등 | Low | 규칙 우회가 반복되면 코드 품질 저하. |

---

## 수정 시 예상 기대효과

### Build & Bundle
- `react-easy-crop` + `@types/sortablejs` 제거 → 번들 크기 약 **15-30KB 감소**
- `lucide-react` 버전 고정 → 빌드 해석 경고 제거, 안정성 ↑

### Maintainability
- `observation` feature 분리 → 코드 탐색/리뷰 시간 **30-50% 단축**
- `cheat-data.ts`, `DummyLoginPage.tsx` 제거 → 프로덕션 코드에 개발용 잔해 제거, 보안 노출면 축소
- `any` → 구체 타입 교체 → 리팩토링 시 컴파일러가 **~70% 실수 사전 차단**

### Architecture
- Named Export 통일, `pages/` 디렉토리 활용 → import 규칙 일관성, onboarding 용이
- 빈 디렉토리 정리 → 프로젝트 구조 신뢰도 ↑

### Testing & DevEx
- MSW 복원 → 개발/CI 시 외부 API 의존 없는 테스트 가능, 플레이크 감소
- `eslint react/recommended` 추가 → hooks 규칙 외 JSX 이슈 자동 검출

### Security & UX
- `window.addToast` 전역 노출 제거 → 외부 오염 공격면 감소
- `remember-me` 정책 일치 → 사용자 인지와 동작 불일치 제거, CS 문의 ↓
- placeholder 라우트 제거/구현 → 사용자 혼란 ↓

---

## 권장 우선순위

1. **즉시 (P0)**: `cheat-data.ts` 제거, `DummyLoginPage.tsx` 제거, `lucide-react` 버전 수정
2. **단기 (P1)**: `react-easy-crop` 의존성 제거, `any` 타입 제거, `observation` feature 분리 기획
3. **중기 (P2)**: MSW 복원 및 통합 테스트 작성, placeholder 라우트 구현/제거, 대형 파일 분리
4. **지속 (P3)**: 빈 디렉토리 정리, `index.css` 테마 변수 정리, `TODO.md` 동기화
