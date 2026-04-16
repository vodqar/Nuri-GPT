## 중기예보 API 엔드포인트/인증방식 오구현

### What Happened
중기예보 API를 `apis.data.go.kr`의 `serviceKey` 인증 방식으로 구현했으나, 실제로는 단기예보와 동일한 `apihub.kma.go.kr`의 `authKey` 방식이었다. 별도의 `KMA_MID_API_KEY` 환경변수와 `mid_api_key` 생성자 파라미터를 만들었고, 401 Unauthorized 에러가 발생한 후에야 공식 문서를 확인하여 원인을 파악했다.

### Root Cause
- 구현 시 기상청 API 공식 문서를 직접 확인하지 않고, 과거 학습 데이터(공공데이터포털 기반 중기예보)를 근거로 코드를 작성
- 기상청이 중기예보 API를 공공데이터포털에서 자체 apihub 포털로 이관한 사실을 놓침
- 단기/중기가 동일 포털·동일 인증키(authKey)를 사용한다는 점을 가정에서 배제

### Why Not Caught
- 단위 테스트는 mock 기반이므로 실제 API 엔드포인트/인증 방식 검증 불가
- 코드 리뷰 단계에서 "API 문서를 직접 확인했는가?" 체크가 없었음
- 401 에러가 발생한 후에도 처음에는 "키 값이 잘못되었다"고 추측하고, 실제 URL을 분석해보지 않음

### Preventability
**예방 가능했음.** 다음 정보가 사전에 확인 가능했음:
- 기상청 apihub 포털의 중기예보 API 문서는 공개 접근 가능
- 단기예보 URL(`apihub.kma.go.kr/api/typ02/openApi/...`)과 중기예보 URL이 동일 도메인/동일 패턴
- API 키가 하나(authKey)로 통일되어 있다는 것은 문서에서 명확히 확인 가능

### Prevention
- **`docs/DEVELOPMENT.md`**에 원칙 추가: "외부 API 연동 시 구현 전 공식 문서의 엔드포인트·인증방식을 직접 확인할 것. 과거 지식이나 유추에만 의존하지 않을 것."
- **`docs/RECURRING_FAILURES_AND_GUARDRAILS.md`**에 섹션 추가: "API 엔드포인트 가정 금지 — 실제 문서 확인 전까지 엔드포인트·인증키·파라미터명을 확정하지 않는다."
