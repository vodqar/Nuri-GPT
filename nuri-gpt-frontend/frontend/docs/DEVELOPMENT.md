# Frontend 개발 가이드 (프로젝트 전용)

> **상위 지침**: [agents.md](../../agents.md) - 아키텍처 원칙 및 에이전트 프로토콜 참조

## 코드 작성 원칙

| 원칙 | 내용 |
|------|------|
| 단순성 | 과도한 추상화, 미래 대비 제네릭 타입 지양. 현재 필요한 기능만 구현 |
| 부수 효과 최소화 | `useEffect` 최소화. 파생 상태는 렌더링 중 계산 |

## 도구 및 패턴

### 클래스 결합
- `clsx` + `tailwind-merge` (또는 `cn` 유틸리티) 사용

### 폼 & 유효성 검증
- **React Hook Form**: Uncontrolled 방식으로 렌더링 성능 최적화
- **Zod**: 폼 스키마 선언적 정의 → `@hookform/resolvers/zod`로 연결
- **자동 저장**: 복잡한 입력 화면 등에서는 디바운스를 활용해 `localStorage` 등에 임시 저장하여 데이터 유실 방지
- **로그인 폼 remember**: `remember`는 이메일 저장이 아닌 인증 세션 지속성(persistent/session cookie) 정책으로 사용

### 로딩 UX 및 스켈레톤
- 전체 페이지 차단보다는 컴포넌트 단위의 로컬 로딩 오버레이(`backdrop-blur` 등) 지향
- 로딩 전후 과정에서 레이아웃 깨짐(Layout Shift) 방지를 위해 그리드 고정 및 스켈레톤 UI 적극 활용

### 모킹 (MSW)
- 핸들러 위치: `src/lib/msw/` (도메인별 분리)
- `npm run dev` 실행 시 브라우저에 MSW 자동 등록

## 에러 핸들링 & 비동기 처리

- **비동기 함수**: `await` 사용 시 반드시 `try-catch` 블록으로 감싸고, 실패 시 사용자에게 Toast 알림으로 구체적인 피드백 제공 (`console.error`에만 의존하지 않음)
- **타임아웃**: LLM 호출 등 지연이 예상되는 API는 개별 타임아웃(예: 120초) 설정
- **클린업**: `URL.createObjectURL` 사용 시 `URL.revokeObjectURL`로 해제

## Definition of Done

- [ ] UI가 `DESIGN.md` / 기획안 레이아웃과 일치
- [ ] ESLint·TypeScript 에러 없음 (`npm run lint`, `npm run build`)
- [ ] `features/` 격리 원칙 미위반 (agents.md 아키텍처 원칙 준수)
- [ ] 상태 관리 레벨 적절 (Local vs Zustand)
- [ ] 템플릿 없는 경우 → 안내 모달 없이 즉시 템플릿 생성 화면으로 분기

## API 클라이언트 규약

- 네트워크 호출은 `services/api.ts`의 axios 인스턴스 `api`를 통해 수행한다.
- FormData 업로드도 axios로 처리한다 (내부 `uploadFormData` 헬퍼 사용). 업로드에서는 `Content-Type`을 제거해 브라우저가 `multipart/form-data` boundary를 자동 설정하도록 위임한다.
- `authStore.refreshAccessToken()`은 예외적으로 `fetch`를 유지한다. 이유는 해당 함수 주석 및 `ARCHITECTURE.md §에러 핸들링` 참조.
- 호출부의 에러 메시지 추출은 `utils/apiError.ts`의 `extractApiErrorMessage()`를 사용한다.

## 알려진 기술 부채

(현재 없음. 이전에 있던 `fetchFormData` / axios refresh 경쟁은 axios 통합으로 해소됨.)

---

## 임시 개발 장치

개발 편의용 우회, 실험 흐름, 샘플 진입점은 완전히 금지되는 것이 아니라 다음 원칙을 따른다.

- 기본 사용자 흐름과 의도 없이 섞이지 않게 유지한다.
- 목적, 범위, 제거 또는 유지 조건이 설명 가능해야 한다.
- 장기간 유지되거나 반복해서 문제를 만든다면 개별 메모가 아니라 상위 문서의 규칙으로 승격한다.
- 특정 장치의 존재 자체보다, 그것이 사용자 경험과 운영 판단을 흐리지 않는지가 더 중요하다.

*마지막 업데이트: 2026-04-15*
