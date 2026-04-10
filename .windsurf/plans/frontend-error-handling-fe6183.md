# 프론트엔드 예외처리 종합 개선 계획서

**요약**: 사용자 입장에서 발생 가능한 모든 예외 상황을 처리하고, 서비스가 죽거나 피드백 없이 장애가 발생하지 않도록 전역/지역 예외처리 체계를 구축합니다.

---

## 1. 현재 예외처리 현황 분석

### 1.1 구현된 부분 ✅
| 위치 | 구현 내용 |
|------|----------|
| `services/api.ts` | 401 Unauthorized 처리 (로그아웃 + 리다이렉트) |
| `useTemplateManagement.ts` | 템플릿 로딩 재시도 로직 (3회, exponential backoff) |
| `JournalHistoryPage.tsx` | 일지 목록 로딩 재시도 로직 |
| `ToastContainer.tsx` | 전역 토스트 알림 시스템 |
| 개별 컴포넌트 | try-catch + 사용자 에러 메시지 표시 |

### 1.2 미흡한 부분 ❌
| 영역 | 문제점 | 위험도 |
|------|--------|--------|
| **전역 에러 핸들러** | React Error Boundary 없음 | 🔴 높음 |
| **API 타임아웃** | axios/fetch 타임아웃 설정 없음 | 🔴 높음 |
| **네트워크 에러** | 오프라인/네트워크 단절 처리 없음 | 🟠 중간 |
| **응답 파싱 에러** | JSON 파싱 실패 처리 없음 | 🟠 중간 |
| **서버 장애 폴백** | 500/503 에러 시 폴백 UI 없음 | 🟠 중간 |
| **에러 로깅** | 외부 로깅(Sentry 등) 없음 | 🟡 낮음 |
| **일관된 에러 메시지** | 에러 메시지 체계화 안 됨 | 🟡 낮음 |
| **API 재시도** | 템플릿/일지 외 API는 재시도 없음 | 🟠 중간 |
| **Zustand 에러** | 스토어 오류 시 복구 로직 없음 | 🟡 낮음 |
| **파일 업로드** | 대용량 파일/네트워크 단절 처리 부족 | 🟠 중간 |

---

## 2. 개선 목표 및 우선순위

### Phase 1 (필수) - 서비스 안정성
1. **전역 에러 바운더리** - 예상치 못한 에러로 앱이 죽는 것 방지
2. **API 타임아웃/재시도** - 응답 없음/느린 응답 처리
3. **네트워크 상태 감지** - 오프라인 상태 알림

### Phase 2 (중요) - 사용자 경험
4. **일관된 에러 UI** - 에러 페이지/폴백 컴포넌트
5. **API 에러 통합 처리** - 500, 502, 503 등 서버 에러 처리
6. **에러 로깅 시스템** - 개발자가 문제를 인지할 수 있게

### Phase 3 (개선) - 완성도
7. **에러 메시지 체계화** - 사용자 친화적 메시지
8. **낙관적 업데이트 롤백** - 실패 시 원복
9. **zustand persist 오류 처리** - 저장소 오류 대응

---

## 3. 상세 구현 계획

### 3.1 전역 에러 바운더리 (Phase 1)

**위치**: `components/global/ErrorBoundary.tsx`

**기능**:
- React 컴포넌트 트리에서 발생하는 에러 캐치
- 에러 발생 시 폴백 UI 표시
- "새로고침" 버튼 제공
- 에러 정보 로깅 (콘솔 + 외부)

**적용 위치**:
- `App.tsx` 최상위에서 라우트 전체 감싸기
- 주요 feature별로 세분화된 바운더리 (옵션)

**폴백 UI 구성**:
- 친근한 에러 메시지 ("문제가 발생했습니다")
- 새로고침 버튼
- 홈으로 이동 버튼
- (개발 모드) 에러 상세 정보

---

### 3.2 API 타임아웃 & 재시도 (Phase 1)

**위치**: `services/api.ts`

**구현 내용**:
```typescript
// 타임아웃 설정
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30초
  timeoutErrorMessage: '요청 시간이 초과되었습니다.'
});

// 재시도 인터셉터 (axios-retry 또는 직접 구현)
- GET 요청: 3회 재시도 (exponential backoff)
- POST/PUT/DELETE: 멱등성 고려, 선택적 재시도
```

**재시도 조건**:
- 네트워크 에러 (ECONNABORTED, ETIMEDOUT)
- 5xx 서버 에러 (500, 502, 503, 504)
- 429 Too Many Requests (Rate Limit)

**재시도 제외**:
- 4xx 클라이언트 에러 (400, 401, 403, 404, 422)
- 401은 재시도 없이 바로 로그아웃

---

### 3.3 네트워크 상태 감지 (Phase 1)

**위치**: `hooks/useNetworkStatus.ts` + 전역 상태

**기능**:
- `navigator.onLine` API 사용
- 오프라인 상태 진입 시 토스트 알림
- 온라인 복귀 시 자동 재연결/새로고침 옵션
- 주요 동작 시도 시 오프라인 확인

**UI 표시**:
- 상단 고정 배너로 오프라인 상태 표시
- "오프라인 모드입니다" + "다시 시도" 버튼

---

### 3.4 API 에러 통합 처리 (Phase 2)

**위치**: `services/api.ts` 인터셉터 확장

**에러 카테고리별 처리**:

| 상태 코드 | 처리 방식 |
|-----------|----------|
| 400 | 사용자 입력 오류 - 입력값 확인 메시지 |
| 401 | 인증 만료 - 로그아웃 후 로그인 페이지 |
| 403 | 권한 없음 - 접근 제한 메시지 |
| 404 | 리소스 없음 - "데이터를 찾을 수 없습니다" |
| 422 | 유효성 검사 실패 - 필드별 에러 표시 |
| 500 | 서버 오류 - "일시적인 문제입니다" + 재시도 |
| 502/503/504 | 게이트웨이/서비스 unavailable - 재시도 |
| NETWORK_ERROR | 네트워크 단절 - 오프라인 모드 진입 |
| TIMEOUT | 타임아웃 - 재시도 또는 "나중에 다시" |

**에러 응답 파싱 안전장치**:
```typescript
// error.response.data가 JSON이 아닐 수 있음
try {
  errorBody = await response.json();
} catch {
  errorBody = { message: '알 수 없는 오류가 발생했습니다.' };
}
```

---

### 3.5 폴백 UI 컴포넌트 (Phase 2)

**위치**: `components/global/ErrorFallback.tsx`

**상태별 컴포넌트**:
1. **NetworkErrorFallback** - 네트워크 단절 시
2. **ServerErrorFallback** - 5xx 에러 시
3. **NotFoundFallback** - 404 에러 시
4. **GenericErrorFallback** - 기타 예상치 못한 에러

**공통 기능**:
- 일러스트/아이콘
- 명확한 메시지
- 액션 버튼 (재시도, 홈 이동, 고객센터)

---

### 3.6 에러 로깅 시스템 (Phase 2)

**위치**: `utils/errorLogger.ts`

**기능**:
```typescript
// 에러 로깅 유틸리티
interface ErrorLog {
  timestamp: string;
  type: 'api' | 'component' | 'runtime' | 'network';
  message: string;
  stack?: string;
  context?: Record<string, unknown>; // 사용자 ID, 페이지, 액션 등
}

// 로깅 방식 (단계별)
1. console.error (개발/테스트)
2. localStorage buffer (오프라인 대응)
3. 외부 서비스 (Sentry/LogRocket) - 향후 추가
```

**자동 로깅 대상**:
- ErrorBoundary에서 잡힌 에러
- API 실패 (4xx, 5xx)
- 예상치 못한 runtime 에러

---

### 3.7 에러 메시지 체계화 (Phase 3)

**위치**: `locales/ko/errors.ts`, `locales/en/errors.ts`

**카테고리별 메시지**:
```typescript
export const errorMessages = {
  network: {
    offline: '인터넷 연결이 없습니다. 연결 상태를 확인해주세요.',
    timeout: '서버 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.',
    serverError: '일시적인 서버 문제가 발생했습니다. 잠시 후 다시 시도해주세요.',
  },
  auth: {
    sessionExpired: '세션이 만료되었습니다. 다시 로그인해주세요.',
    unauthorized: '접근 권한이 없습니다.',
  },
  validation: {
    required: '필수 입력 항목입니다.',
    invalidFormat: '입력 형식이 올바르지 않습니다.',
  },
  file: {
    tooLarge: '파일 크기가 너무 큽니다. (최대 10MB)',
    invalidType: '지원하지 않는 파일 형식입니다.',
    uploadFailed: '파일 업로드에 실패했습니다.',
  },
  template: {
    loadFailed: '템플릿을 불러오는 데 실패했습니다.',
    createFailed: '템플릿 생성에 실패했습니다.',
    deleteFailed: '템플릿 삭제에 실패했습니다.',
  },
  generation: {
    failed: '일지 생성에 실패했습니다.',
    regenerateFailed: '재생성 중 오류가 발생했습니다.',
  }
};
```

---

## 4. 파일별 변경 계획

### 신규 파일
| 파일 경로 | 설명 |
|-----------|------|
| `components/global/ErrorBoundary.tsx` | React 에러 바운더리 컴포넌트 |
| `components/global/ErrorFallback.tsx` | 에러 폴백 UI 모음 |
| `hooks/useNetworkStatus.ts` | 네트워크 상태 감지 훅 |
| `utils/errorLogger.ts` | 에러 로깅 유틸리티 |
| `utils/retry.ts` | 재시도 로직 유틸리티 |
| `locales/ko/errors.ts` | 한국어 에러 메시지 |
| `locales/en/errors.ts` | 영어 에러 메시지 |

### 수정 파일
| 파일 경로 | 변경 내용 |
|-----------|----------|
| `services/api.ts` | 타임아웃 설정, 재시도 인터셉터, 에러 파싱 강화 |
| `App.tsx` | ErrorBoundary 적용, NetworkStatusProvider 적용 |
| `main.tsx` | 전역 에러 핸들러 (window.onerror) |
| `hooks/useTemplateManagement.ts` | 통합 재시도 유틸리티 사용 |
| `JournalHistoryPage.tsx` | 통합 재시도 유틸리티 사용 |
| `ObservationPage.tsx` | 에러 바운더리 세분화 (선택) |

---

## 5. 테스트 계획

### 수동 테스트 시나리오
1. **전역 에러**: 개발자 도구에서 강제 에러 발생 → 폴백 UI 확인
2. **타임아웃**: 네트워크 throttling + API 호출 → 타임아웃 메시지 확인
3. **오프라인**: 네트워크 끊기 → 오프라인 배너 확인
4. **5xx 에러**: MSW로 500 응답 모킹 → 재시도 로직 확인
5. **401 에러**: 토큰 만료 모킹 → 로그아웃 + 리다이렉트 확인

### 자동 테스트 (향후)
- ErrorBoundary 렌더링 테스트
- retry 유틸리티 유닛 테스트
- useNetworkStatus 훅 테스트

---

## 6. 구현 순서

```
Phase 1 (필수 - 먼저 구현)
├── 1. ErrorBoundary 컴포넌트
├── 2. 전역 에러 핸들러 (window.onerror)
├── 3. API 타임아웃 설정
├── 4. useNetworkStatus 훅
└── 5. App.tsx에 적용

Phase 2 (중요 - 그 다음)
├── 6. API 재시도 인터셉터
├── 7. ErrorFallback 컴포넌트들
├── 8. 에러 로깅 시스템
└── 9. API 에러 통합 처리

Phase 3 (개선 - 나중에)
├── 10. 에러 메시지 체계화 (i18n)
├── 11. 낙관적 업데이트 롤백
└── 12. zustand persist 오류 처리
```

---

## 7. 예상 리스크 및 대응

| 리스크 | 대응 방안 |
|--------|----------|
| 과도한 재시도로 서버 부하 | 재시도 간격 최소 1초, 최대 3회 제한 |
| 민감한 에러 정보 노출 | 프로덕션에서는 에러 상세 숨김 |
| 에러 UI가 너무 많이 뜸 | 에러 우선순위 설정, 중복 방지 |
| 오프라인 체크 과도하게 민감 | 디바운스 적용, 상태 변화 후 3초 대기 |

---

## 8. 완료 기준 (DoD)

- [ ] ErrorBoundary가 모든 라우트를 감싸고 있음
- [ ] API 타임아웃이 30초로 설정됨
- [ ] 네트워크 단절 시 사용자에게 알림이 표시됨
- [ ] 5xx 에러 시 자동 재시도가 동작함
- [ ] 모든 API 에러가 적절한 메시지로 변환됨
- [ ] 에러 발생 시 콘솔에 로그가 남음
- [ ] 테스트 시나리오 5개가 모두 통과함

---

*계획 작성일: 2026-04-07*
*다음 단계: 사용자 승인 후 Phase 1 구현 시작*
