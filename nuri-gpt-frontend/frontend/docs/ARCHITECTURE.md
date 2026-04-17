# Frontend Architecture

## 아키텍처: Feature-First

도메인 기능별로 코드를 응집시켜 변경 영향 범위를 국소화하고 유지보수성을 높인다.

## 디렉토리 구조

상세 트리 나열은 유지하지 않는다. 실제 구조는 항상 `src/`를 기준으로 확인한다.

- 도메인 로직과 전용 UI는 `src/features/{domain}` 내부에 배치
- 공용 UI는 `src/components`에 배치 (예: `ImageCropperModal`)
- 공용 훅은 `src/hooks`, 전역 상태는 `src/store`에 배치
- API/외부 연동 코드는 `src/services` 또는 feature 내부 `api`에 배치
- 이미지 및 형식 변환 유틸리티는 `src/utils`에 배치 (예: `cropImage.ts`, `imageFormatUtils.ts`)

## 의존성 규칙

| 규칙 | 내용 |
|------|------|
| Feature 간 직접 import 금지 | 공유 필요 시 `src/components` 또는 `src/hooks`로 이동 |

## 상태 관리

| 유형 | 도구 | 용도 |
|------|------|------|
| 서버 상태 | React Query (예정) | API 통신, 캐싱 |
| 전역 클라이언트 상태 | Zustand | 인증 정보, 사용자 설정(preferences), 다크모드 등 |
| 로컬 상태 | useState / useReducer | 모달, 폼 입력값 등 |

## 에러 핸들링 (Defense-in-Depth)

프론트엔드 전반에 걸쳐 다중 계층의 예외처리 구조를 갖는다.
- **전역 에러 바운더리 (Error Boundary)**: React 렌더링 중 발생하는 예외를 포착하여 백화현상을 방지 (Fallback UI 제공)
- **네트워크 레이어**: `services/api.ts`의 axios 인스턴스 인터셉터에서 공통 타임아웃, 401 자동 토큰 갱신, 4xx/5xx HTTP 에러, 네트워크 단절(오프라인) 상태를 전역 Toast 알림으로 처리. `authStore.refreshAccessToken()`만 인터셉터 순환 방지를 위해 의도적으로 `fetch`를 사용
- **비동기 로직**: 모든 비동기 호출(`async/await`)은 개별 `try-catch`로 감싸 사용자 친화적인 에러 피드백을 제공
- **브라우저 API 폴백**: 클립보드(`navigator.clipboard`) 등 환경에 따라 실패할 수 있는 Native API는 대안 로직(`document.execCommand`)으로 폴백

## UI 컴포넌트 원칙

- **Atoms**: 앱 전체에서 3회 이상 재사용되는 요소만 `src/components/`에 작성
- **Dumb Components**: UI 컴포넌트에 비즈니스 로직 포함 금지
- **Custom Hooks**: 비즈니스 로직은 `features/{domain}/hooks`로 분리

*마지막 업데이트: 2026-04-17* (사용자 설정(preferences) 상태 관리 전략 추가 — authStore에 preferences 필드 도입, user_preferences 테이블 기반)
