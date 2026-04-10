# 테스트 파일 경고 해결 계획

## 문제 분석

**파일:**
- `/home/kj/Projects/Nuri-GPT/nuri-gpt-frontend/frontend/src/routes/PrivateRoute.test.tsx`
- `/home/kj/Projects/Nuri-GPT/nuri-gpt-frontend/frontend/src/routes/PublicRoute.test.tsx`

**현상:**
테스트는 통과하지만 IDE/콘솔에서 다음 경고가 표시됨:
```
An update to PrivateRoute inside a test was not wrapped in act(...)
```

**원인:**
Zustand의 `useAuthStore.setState()`가 비동기 상태 업데이트를 일으키는데, 이를 `act()`로 감싸지 않았거나 `waitFor`로 기다리지 않음.

## 해결 계획

### 변경 내용
1. `waitFor` import 추가 (`@testing-library/react`)
2. `expect` 구문을 `waitFor`로 감싸 비동기 렌더링 완료 대기

### 적용 파일
- `PrivateRoute.test.tsx`: 1개 테스트 수정
- `PublicRoute.test.tsx`: 2개 테스트 수정

### 예상 결과
- 경고 메시지 소거
- 테스트 여전히 통과
