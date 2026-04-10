# 일지 생성 목록 로드 Fail-Safe 구현 계획

## 문제점

### 1. 무한 재시도 현상 (원인 분석)
- `useTemplateManagement.ts`의 `fetchTemplates`에서 API 호출 실패 시 별도의 재시도 제한이 없음
- **무한 스크롤 원인은 아님**: `JournalHistoryPage.tsx`는 빈 배열이면 `lastItemRef`가 연결될 요소가 없어 트리거되지 않음
- **실제 원인**:
  - React StrictMode(개발 모드)에서 `useEffect`가 두 번 실행됨
  - `useEffect` 의존성 배열에 `fetchTemplates`가 포함되어 있음
  - `fetchTemplates`가 `useCallback`으로 memoized되어 있지만, `userId`가 undefined → defined로 변경되는 시점에 재생성됨
  - 로그인 직후 또는 인증 상태 변경 시 연속 호출 발생

### 2. 로딩 UX 불일치
- `LogInputView.tsx`는 블러+스피너로 로딩 표시가 구현됨
- `TemplateSelectionView.tsx`는 `isLoading` prop을 받지만 블러 오버레이가 없음
- `JournalHistoryPage.tsx`는 단순 스피너만 표시

### 3. 에러 피드백 부족
- 템플릿 로드 실패 시 단순 에러 메시지만 표시
- "다시 시도" 버튼이나 자동 재시도 로직 없음
- 최종 실패 시 사용자가 취할 수 있는 행동이 제한적

## 해결 계획

### Step 1: `useTemplateManagement.ts` 개선
1. **재시도 로직 추가**
   - 최대 3회 자동 재시도 (exponential backoff: 1s, 2s, 4s)
   - 재시도 횟수 상태 관리 (`retryCount`, `maxRetries`)

2. **로딩 상태 세분화**
   - `isLoading`: 초기 로딩
   - `isRetrying`: 재시도 중
   - `isFailed`: 최종 실패

3. **에러 핸들링 개선**
   - 최종 실패 시 사용자에게 "다시 시도" 버튼 제공
   - 에러 메시지에 구체적인 원인 포함

### Step 2: `TemplateSelectionView.tsx` 개선
1. **블러+스피너 오버레이 추가**
   - `LogInputView.tsx`와 동일한 스타일 적용
   - 로딩 중일 때 배경 블러 처리

2. **실패 상태 UI 추가**
   - 최종 실패 시 에러 카드 표시
   - "다시 시도" 버튼 제공

### Step 3: `JournalHistoryPage.tsx` 개선
1. **재시도 로직 추가** (Step 1과 동일 패턴)

2. **로딩/실패 UI 개선**
   - 블러 오버레이 추가
   - 실패 시 "다시 시도" 버튼

### Step 4: 공통 유틸리티 추출 (선택적)
- 재시도 로직을 커스텀 훅으로 분리: `useRetryableFetch`
- 중복 코드 방지

## 구현 범위

| 파일 | 변경 내용 |
|------|----------|
| `useTemplateManagement.ts` | 재시도 로직, 상태 세분화 |
| `TemplateSelectionView.tsx` | 블러 오버레이, 실패 UI |
| `JournalHistoryPage.tsx` | 재시도 로직, 블러 오버레이 |
| `ObservationPage.tsx` | 실패 상태 전달 (필요시) |

## 검증 방법

1. 백엔드 서버 중지 상태에서 프론트엔드 접속 → 재시도 동작 확인
2. 네트워크 탭에서 요청 실패 시뮬레이션 → 최대 3회 재시도 후 실패 UI 확인
3. "다시 시도" 버튼 클릭 → 수동 재시도 동작 확인

---

**승인 요청**: 위 계획대로 진행해도 될까요?
