# Network Error 해결 계획

## 문제 요약
- 증상: 프론트엔드에서 `/api/templates/` 요청 시 `ERR_NETWORK` 발생
- 위치: 브라우저 프리뷰(`127.0.0.1:44557`) → 백엔드(`127.0.0.1:8000`)
- CORS: 설정은 정상 (OPTIONS 응답 확인 완료)

## 원인 분석
1. 브라우저 프리뷰 프록시가 API 요청을 차단하거나 프록시 설정 문제
2. 프론트엔드 환경변수 `VITE_API_URL`이 명시적으로 설정되지 않음
3. 브라우저 캐시에 이전 실패 응답이 남아있을 수 있음

## 해결 방안 (3단계)

### 1단계: 프론트엔드 환경변수 명시적 설정
**파일**: `nuri-gpt-frontend/frontend/.env.local` 생성
```
VITE_API_URL=http://127.0.0.1:8000/api
```

**근거**: 현재 `api.ts:5`는 `import.meta.env.VITE_API_URL`를 먼저 확인. 명시적 설정으로 `localhost` → `127.0.0.1` 통일

### 2단계: 브라우저 프리뷰 재시작 (캐시 초기화)
- 브라우저 프리뷰 연결 해제
- 프론트엔드 개발 서버 재시작 (`npm run dev`)
- 브라우저 캐시 무효화 (Ctrl+Shift+R)

### 3단계: 대체 테스트 방식
Playwright MCP 연결 문제로 인해 다음 방식으로 전환:
1. **직접 브라우저 테스트**: `http://localhost:5173/observations` 접속
2. **API 단위 테스트**: curl로 각 엔드포인트 직접 호출
3. **스크린샷 검증**: 브라우저 프리뷰 스크린샷으로 UI 확인

## 검증 방법
```bash
# 1. 환경변수 적용 후 프론트엔드 재시art
cd nuri-gpt-frontend/frontend
pkill -f vite
npm run dev

# 2. 브라우저에서 직접 접속
open http://localhost:5173/observations

# 3. API 연결 테스트
curl -s http://127.0.0.1:8000/api/templates?user_id=00000000-0000-0000-0000-000000000001
```

## 예상 결과
- 템플릿 목록 정상 로드 (빈 배열 또는 기존 템플릿)
- Network Error 해소
- OBSERVATION 페이지 정상 표시

---

**작성일**: 2026-04-02  
**승인 후 진행 예정**
