# Nuri-GPT Testing Guide

테스트 실행 방법, 모킹 전략, 디버깅 절차를 정리한 가이드입니다. AI 에이전트가 터미널 조작으로 테스트를 수행할 수 있도록 구성되었습니다.

---

## 1. 테스트 실행 방법

### 1.1 백엔드 테스트

```bash
cd nuri-gpt-backend

# 전체 테스트
./venv/bin/pytest -q

# 특정 파일만
./venv/bin/pytest tests/test_integration.py -v

# 커버리지 포함
./venv/bin/pytest --cov=app --cov-report=html -q
```

### 1.2 프론트엔드 테스트

```bash
cd nuri-gpt-frontend/frontend

# 패키지 설치 (최초 1회)
npm install

# 테스트 실행
npm run test

# UI 모드 (watch)
npm run test:ui
```

---

## 2. 테스트 구조

### 2.1 백엔드 테스트 유형

| 파일 | 유형 | 외부 의존성 | 설명 |
|------|------|-------------|------|
| `test_*.py` | 단위/통합 | Mock (LLM/DB) | API 엔드포인트별 테스트 |
| `test_integration.py` | 통합 | Mock LLM만 | 템플릿 업로드→생성 파이프라인 검증 |
| `test_generate.py` | 스모크 | 없음 | 라우터 등록 여부만 확인 |
| `test_e2e.py` | 레거시 | - | `test_integration.py`로 대체됨 |

### 2.2 프론트엔드 테스트 유형

| 파일 | 대상 | 설명 |
|------|------|------|
| `*.test.tsx` | Route Guard | 인증 기반 라우팅 동작 확인 |
| `src/test/setup.ts` | 설정 | `@testing-library/jest-dom` 임포트 |

---

## 3. Mocking 가이드

### 3.1 백엔드: DI Override 패턴

```python
from unittest.mock import MagicMock, AsyncMock
from app.main import app
from app.core.dependencies import get_llm_service, get_template_repository

# Mock 객체 생성
mock_llm = MagicMock()
mock_llm.generate_observation_log.return_value = {"title": "테스트"}

# 의존성 주입
app.dependency_overrides[get_llm_service] = lambda: mock_llm

# 테스트 실행
response = client.post("/api/generate/log", json={...})

# 정리 (필수)
app.dependency_overrides.clear()
```

### 3.2 Mock 범위 원칙

- **LLM API (Gemini/Dify)**: 반드시 Mock
- **DB (Supabase)**: 테스트 목적에 따라 실제 사용 가능
- **Storage**: 테스트 목적에 따라 실제 사용 가능

### 3.3 프론트엔드: Zustand Store Mock

```typescript
import { useAuthStore } from '../store/authStore';

afterEach(() => {
  useAuthStore.setState({
    isAuthenticated: false,
    accessToken: null,
    user: null,
  });
  localStorage.clear();
});
```

---

## 4. 디버깅 절차

### 4.1 백엔드 테스트 실패 시

```bash
# 1. 상세 출력
./venv/bin/pytest tests/test_xxx.py -v -s

# 2. 특정 테스트만
./venv/bin/pytest tests/test_xxx.py::test_function_name -v

# 3. PDB 디버깅
./venv/bin/pytest tests/test_xxx.py --pdb
```

### 4.2 프론트엔드 테스트 실패 시

```bash
# 1. UI 모드로 디버깅
npm run test:ui

# 2. 특정 파일만
npx vitest run src/routes/PublicRoute.test.tsx
```

---

## 5. 신규 테스트 추가 체크리스트

- [ ] 테스트 파일명: `test_{target}.py` 또는 `{target}.test.tsx`
- [ ] Mock 필요 시 `app.dependency_overrides` 또는 `vi.mock` 사용
- [ ] 테스트 후 `app.dependency_overrides.clear()` 또는 `afterEach`로 정리
- [ ] 실제 비용 발생 API (LLM)는 반드시 Mock 처리
- [ ] 기존 테스트와 중복되지 않는지 확인

---

## 6. 프론트엔드 예외처리 (Error Handling) 수동 테스트

최근 도입된 4가지 주요 예외처리(ErrorBoundary, 타임아웃/에러, 오프라인 감지, 클립보드 폴백)는 다음 절차로 브라우저에서 검증할 수 있습니다.

### 6.1 전역 ErrorBoundary
- 컴포넌트 렌더링 코드에 임의의 `throw new Error('Test')` 삽입 후 화면 확인
- 앱 전체가 크래시되지 않고 "문제가 발생했습니다" 폴백 UI가 렌더링되는지 확인

### 6.2 API 타임아웃 & 공통 HTTP 에러 (MSW 활용)
- MSW 핸들러(`src/mocks/handlers.ts`) 내 특정 라우트에 `await delay('infinite')` 또는 에러 응답(`HttpResponse.json(null, { status: 504 })`) 설정
- 지정된 타임아웃(일반 30초, LLM/생성 120초, 파일 60초) 초과 후 Toast 알림 확인

### 6.3 네트워크 상태 (오프라인 배너)
- 브라우저 개발자 도구 (Network 탭) -> 'Throttling' -> 'Offline' 선택
- 화면 최상단에 오프라인 경고 배너 표시 확인
- 'No throttling' (온라인)으로 복귀 시 배너 사라짐 확인

### 6.4 비동기 함수 예외 피드백
- 템플릿 삭제/수정, 일지 생성 등 주요 비동기 작업 중 강제로 네트워크를 끊거나 에러 응답 주입
- `console.error`가 아닌 화면 우측 하단 Toast 메시지('삭제 중 오류가 발생했습니다.' 등) 표시 확인

---

## 7. CI/자동화 고려사항

```bash
# 백엔드 (exit code 0 = 성공)
./venv/bin/pytest -q --tb=short

# 프론트엔드 (exit code 0 = 성공)
npm run test -- --run
```

---

*Last Updated: 2025-04-05*
