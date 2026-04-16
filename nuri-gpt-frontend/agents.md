## 문서 목록

| 경로 | 설명 |
|------|------|
| `frontend/docs/OVERVIEW.md` | 서비스 목적·핵심 기능·기술 스택·실행 방법 |
| `frontend/docs/ARCHITECTURE.md` | Feature-First 디렉토리 구조·의존성 규칙·상태 관리 전략 |
| `frontend/docs/DEVELOPMENT.md` | 코드 작성 원칙·컴포넌트 규칙·MSW 모킹·DoD 체크리스트 |
| `frontend/docs/SERVER_GUIDE.md` | 프론트엔드·백엔드 서버 실행 방법·포트 설정·트러블슈팅 |
| `frontend/docs/DIFY_CHATFLOW_SETUP.md` | 재생성 API용 Dify Chatflow 설정 가이드 |
| `frontend/docs/DESIGN.md` | UIUX의 디자인 철학 (Color, Typography, Elevation) |
| `frontend/docs/GUARDRAILS.md` | 반복 실수 방지 가드레일 (레이아웃 오버플로우 등) |

---

# Frontend 개발 가이드 (프로젝트 전용)

## 1. 아키텍처: Feature-First

- 도메인 로직·전용 UI는 반드시 해당 `features/` 폴더 안에 위치
- 다른 feature에서 직접 import 금지 → 공유가 필요하면 `shared/` 또는 `components/global/`로 이동

## 2. 컴포넌트 계층 (실용적 Atomic Design)

> **Simplicity First**: 단일 사용 코드에 추상화 레이어 생성 금지

| 레벨 | 설명 | 위치 |
|------|------|------|
| Atoms | 최소 UI 단위 (Button, Input) | 실제 재사용 필요 시 생성 |
| Molecules/Organisms | Atoms 조합 | 기본: `features/` 내부. 3개+ feature에서 사용 시 `components/`로 이동 |
| Pages | 데이터 패칭 및 feature 조합 진입점 | - |

## 3. 엔지니어링 규칙

- **Custom Hook**: 비즈니스 로직은 feature 폴더 내 Custom Hook으로 분리 → UI 컴포넌트는 presentational 유지
- **TypeScript**: 현재 필요한 타입만 정의. 복잡한 제네릭 지양
- **상태 관리**: 서버 데이터 → TanStack Query / 전역 클라이언트 상태 → Zustand / 기본은 `useState` 우선
- **임시 개발 장치**: 개발 편의용 우회나 실험 흐름이 필요하면 목적과 범위를 분명히 하고, 기본 사용자 흐름과 섞이지 않게 유지
- **상호작용 일관성**: 사용자 피드백과 확인 흐름은 가능한 한 프로젝트의 공통 상호작용 패턴을 따른다

## 4. 에이전트 실행 프로토콜

1. 작업 전 범위 선언: `Global UI` 변경인지 `Feature-specific` 변경인지 명시
2. 신규 UI 요소 생성 전 `components/atoms` 확인 → 기존 스타일 매칭
3. 모든 컴포넌트는 **Named Export** 사용
4. 반복해서 발견되는 UI gotcha나 임시 우회는 세션 메모에만 두지 말고 관련 `docs/` 또는 `agents.md`로 승격
5. UI 버그 수정 시 `overflow-hidden` 같은 맹목적 땜질을 금지하며, 로그인 벽 등에 막혀 시각적 검증이 불가능한 경우 임의 패스 금지(사용자에게 계정 또는 우회법을 즉시 에스컬레이션할 것).

## 5. 완료 기준 (DoD)

- [ ] UI가 `DESIGN.md` / 기획안 레이아웃과 일치
- [ ] ESLint·TypeScript 에러 없음 (`npm run lint`, `npm run build`)
- [ ] **레이아웃 오버플로우**: 중첩 카드/컨테이너 레이아웃이 부모 경계를 침범하지 않음 (see [GUARDRAILS.md](frontend/docs/GUARDRAILS.md))
- [ ] `features/` 격리 원칙 준수 (아키텍처 1항 참조)
- [ ] 상태 관리 레벨 적절 (Local vs Zustand)
- [ ] 템플릿 없는 경우 → 안내 모달 없이 즉시 템플릿 생성 화면으로 분기
- [ ] 하위 지침(DEVELOPMENT.md)에 정의된 구현 패턴 준수
- [ ] 임시 개발용 흐름이나 디버깅 편의 장치가 의도 없이 기본 UX에 남지 않았다

- 작업 완료 후 ToC의 관련 문서가 변경된 경우 반드시 업데이트
- 문서 수정 시 하단에 날짜 기록: `*Last Updated: YYYY-MM-DD*`

---

*Last Updated: 2026-04-14*