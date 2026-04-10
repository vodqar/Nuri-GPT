# 프론트엔드 향후 작업 사항 (TODO)

## 보안 및 인증 관련
- [ ] **Refresh Token 연동 구현**
  - 현재는 Access Token 기반의 단일 인증 방식으로 통신 모듈(Axios Interceptors)이 구현되어 있습니다.
  - 향후 보안성 강화 및 사용자 경험(UX) 개선을 위해 `401 Unauthorized` 에러 발생 시 Refresh Token을 사용해 Access Token을 재발급(Silent Refresh) 받는 로직을 `src/services/api.ts`에 추가해야 합니다.
  - 백엔드 측의 Token 갱신 엔드포인트 마련 및 Cookie 기반(HttpOnly) Refresh Token 저장 처리와 맞물려 작업해야 합니다.
