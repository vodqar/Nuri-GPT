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

## 알려진 기술 부채

### fetchFormData / axios 인터셉터 refresh 경쟁

`api.ts`의 FormData 요청(`fetchFormData`)과 JSON 요청(axios)은 각자 독립적으로 401 처리 후 토큰 갱신을 시도함. 동시에 두 종류의 요청이 401을 받으면 `isRefreshing` 플래그가 공유되지 않아 중복 refresh 요청이 발생할 수 있음.

**현재 괜찮은 이유**: 서비스 흐름이 순차적(OCR 업로드 → 생성 →보내기)이므로 실제 동시 발생 가능성 낮음.

**장기 권장**: `fetchFormData`를 axios 기반으로 통합하거나, refresh 상태를 모듈 공유 변수로 일원화.

---

## 임시 개발 장치

개발 편의용 우회, 실험 흐름, 샘플 진입점은 완전히 금지되는 것이 아니라 다음 원칙을 따른다.

- 기본 사용자 흐름과 의도 없이 섞이지 않게 유지한다.
- 목적, 범위, 제거 또는 유지 조건이 설명 가능해야 한다.
- 장기간 유지되거나 반복해서 문제를 만든다면 개별 메모가 아니라 상위 문서의 규칙으로 승격한다.
- 특정 장치의 존재 자체보다, 그것이 사용자 경험과 운영 판단을 흐리지 않는지가 더 중요하다.

*마지막 업데이트: 2026-04-14*

### 주요 변경사항 (2026-04-14)
- **템플릿 생성 반자동화**: `TemplateCreationView` → 트랙 선택 진입점으로 재정의
  - **트랙 1 (이미지)**: 이미지 업로드 → `/upload/template/analyze` 호출 → LLM 분석 중 로딩 → `TemplateStructureEditor`
  - **트랙 2 (수동)**: 빈 상태로 `TemplateStructureEditor` 바로 진입
  - `CreationStep` 타입: `'entry' | 'image-upload' | 'analyzing' | 'editing'`
- **`TemplateStructureEditor` 카드 UI 리디자인** (`features/observation/components/`):
  - **카테고리 카드**: 대분류를 폴더 아이콘(`FolderOpen`) + 색상 배경의 카드로 표현
  - **소분류 미니카드**: 대분류 카드 안에 중첩된 형태로 표현 (`ChevronRight` 구분자)
  - **항목 라인**: `List` 아이콘 + 텍스트, 최소 UI로 간결하게 표현
  - **역할별 추가 버튼**: "+ 카테고리/소분류/항목 추가" 3단계 명확 분리
  - 수동 트랙 빈 상태에서 카드 형태 예시 오버레이 표시
  - 인라인 편집 (Enter 저장, ESC 취소), 호버 시 삭제 버튼
  - localStorage 디바운스 자동저장 + 복원 (수동 트랙 전용)
  - `POST /templates/` 호출로 저장 (이미지 있으면 함께 전송)
- **`templateStructureUtils.ts` 업데이트** (`features/observation/utils/`):
  - `TreeNode` 타입 추가 (`{id, label, children[]}`) — 카드 UI 전용
  - `structureToTreeNodes` / `treeNodesToStructure` 변환 함수
  - `createTreeNode` 헬퍼
  - 기존 `flatToTree` / `treeToFlat` 유지 (하위 호환성)
- **`api.ts` 신규 함수**: `analyzeTemplateImage`, `createTemplate`

### 주요 변경사항 (2026-04-10)
- **일지 작성 필드 테이블 레이아웃 적용**: `LogInputView.tsx`의 manual 모드 입력 영역을 아코디언 카드에서 doc-table 구조로 교체
  - 대분류 → `doc-header-col`, 소분류 → `doc-sub-header-col`, 입력 영역 → `doc-content-col`
  - 요일 필드는 아코디언 없이 행으로 나열 (`subKey · dayKey` 레이블)
  - OCR 버튼: 데스크탑 hover 시 표시 / 모바일(`≤640px`) 항상 표시 (static position fallback)
  - CSS 클래스: `index.css`에 `.doc-table`, `.doc-row`, `.doc-header-col`, `.doc-sub-header-col`, `.doc-content-col`, `.doc-textarea`, `.doc-ocr-btn` 추가
  - `PathBreadcrumb`, `ChevronDown/Right`, `useState`, `getFlatFields`, 아코디언 state 제거

### 주요 변경사항 (2026-04-09)
- **이미지 크롭 좌표 변환 개선**: `react-image-crop`이 반환하는 CSS 표시 크기 기준 좌표를 원본 이미지 크기 기준으로 변환 (`cropCoordinateTransform.ts` 추가)
- **회전 이미지 크롭 지원**: 0/90/180/270도 회전 후에도 정확한 영역 크롭 가능
- **blob 파일명 처리**: MIME 타입에서 확장자 추론하여 업로드 가능 (`file_validator.py`)
