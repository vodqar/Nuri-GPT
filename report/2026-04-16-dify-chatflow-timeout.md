## Dify Chatflow 호출 타임아웃 — 응답 방식 미확인

### What Happened
GreetingService에서 Dify Chatflow `/chat-messages` 엔드포인트를 `response_mode: "blocking"`으로 호출했으나, 12~15초 내 응답이 오지 않고 지속적으로 타임아웃 발생. Dify 서버 자체는 살아있고(`/parameters` 401 정상 응답), API 키도 유효하지만, Chatflow 실행이 완료되지 않아 blocking 요청이 계속 대기함.

### Root Cause
- **Chatflow 구성 상태 미확인**: Dify 대시보드에서 Chatflow가 실제로 완성되어 실행 가능한 상태인지 확인하지 않고 코드를 작성함
- **`response_mode` 선택 근거 부재**: `blocking` 모드는 LLM이 전체 응답을 생성할 때까지 대기하므로, Chatflow 내부에 시간이 걸리는 노드(LLM 호출 등)가 있으면 쉽게 타임아웃 발생
- **타임아웃 값(10초) 과소**: `weather.py`의 외부 API 호출 타임아웃을 그대로 사용했으나, LLM 기반 Chatflow는 10초 내 응답이 어려울 수 있음
- **스트리밍 미고려**: `streaming` 모드를 사용하면 첫 토큰 도착으로 연결 확인이 가능하나, 이를 검토하지 않음
- **인삿말 서비스 응답 파싱 한계**: 당시 `GreetingService`는 `blocking` JSON 응답에서 `answer`만 읽도록 구현되어 있어, Dify가 `text/event-stream` 형태로 응답하거나 응답 형식이 달라질 경우 실제 답변이 생성되어도 백엔드에서 빈 문자열로 처리될 수 있었음

### Why Not Caught
- 단위 테스트는 mock 기반이라 실제 Dify 호출 타임아웃을 검증 불가
- "Dify Chatflow가 이미 존재하고 정상 동작한다"는 가정을 명시하지 않아 검증 누락
- 코드 리뷰/구현 단계에서 "Chatflow가 실제로 구성되어 있는가?" 확인 단계가 없었음

### Preventability
**예방 가능했음.** 다음이 사전에 확인 가능했음:
- Dify 대시보드에서 Chatflow가 "게시(publish)" 상태인지 확인
- `curl` 또는 간단한 스크립트로 Chatflow에 최소 요청을 보내 응답 시간 측정
- `blocking` vs `streaming` 선택 시 LLM 응답 지연을 고려한 타임아웃 산정
- 기존 `llm.py`의 Dify 호출 패턴(타임아웃, 응답 모드) 참조 가능

### Prevention
- **`nuri-gpt-backend/docs/DEVELOPMENT.md`** 디버깅 가이드에 추가: "Dify Chatflow/Workflow 연동 전, 대시보드에서 게시 상태 확인 후 curl로 최소 요청 응답 시간을 측정할 것. blocking 모드 타임아웃은 측정된 응답 시간의 2배 이상으로 설정할 것."
- **`docs/RECURRING_FAILURES_AND_GUARDRAILS.md`**에 패턴 추가: "외부 서비스 연동 시 해당 서비스가 실제로 구성·게시되어 호출 가능한 상태인지 코드 작성 전에 확인한다. mock 테스트만으로는 연동 가능성을 보증하지 못한다."
- **`app/services/greeting.py`** 타임아웃 상향: 10초 → 30초 이상 (다음 세션에서 적용)
- **`app/services/greeting.py`**는 기존 `llm.py`와 동일하게 `streaming`/`blocking` 응답을 모두 파싱하도록 구현하고, 요청 input key 및 응답 길이를 로그로 남겨 실연동 디버깅 시 payload 누락과 응답 파싱 문제를 분리해서 확인할 것
