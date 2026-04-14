## ExampleOverlay 오버플로우 오진 — overflow-hidden 반복 적용으로 3회 수정

### What Happened
HANDOFF.md에 보고된 "예시 오버레이 오버플로우" 문제를 해결하는 데 3번의 시도가 필요했다. 첫 번째는 HANDOFF에 적힌 대로 카드 컴포넌트에 `w-full overflow-hidden`을 적용했고, 두 번째는 부모 컨테이너와 오버레이에 `overflow-hidden`을 추가했으며, 세 번째에서야 `absolute inset-0` 포지셔닝이 근본 원인임을 파악하고 normal flow로 전환했다.

### Root Cause
`ExampleOverlay`는 `absolute inset-0`으로 부모에 맞춰 크기가 결정되는데, 부모 컨테이너(`relative space-y-4`)의 자연 높이는 tree가 비어 있을 때 "카테고리 추가" 버튼 하나뿐이었다. 따라서 오버레이의 콘텐츠(놀이 + 일상생활 카드)가 부모 높이를 초과하여 넘쳤다.

이 문제에 `overflow-hidden`을 적용하면 넘침은 막지만 콘텐츠가 잘려 예시 기능 자체가 무효화된다.

### Why Not Caught
1. **HANDOFF.md의 수정 방법을 검증 없이 수용**: HANDOFF에 "CategoryCard, SubcategoryCard 루트에 `w-full overflow-hidden` 추가"라고 적혀 있었고, 이를 실제 DOM 구조를 분석하지 않고 그대로 따랐다. 이 수정은 카드 너비 오버플로우에 대한 것이었지, 예시 오버레이 높이 오버플로우와는 무관했다.
2. **증상 대응 반복**: "넘친다 → overflow-hidden" 이라는 단순 패턴 매칭으로 접근했다. `absolute` 요소가 부모 높이를 받는 메커니즘, 그리고 부모의 자연 높이가 어디서 결정되는지를 분석하지 않았다.
3. **브라우저 확인 생략**: 로그인이 필요하다는 이유로 1차, 2차 수정 모두 시각적 검증 없이 완료 선언했다.

### Preventability
완전히 예측 가능했다. 코드를 읽는 시점에 다음이 모두 확인 가능했다:
- `ExampleOverlay`가 `absolute inset-0`이고, `showOverlay`는 `tree.length === 0`일 때만 true
- tree가 비어있으면 부모 div 안에 "카테고리 추가" 버튼 하나만 flow에 참여
- 따라서 `absolute inset-0`인 오버레이는 버튼 높이로 제한됨
- 오버레이의 콘텐츠(카드 2개 + 버튼)는 이 높이를 확실히 초과

`overflow-hidden`이 아니라 포지셔닝 전략 변경이 필요하다는 결론은 코드만으로 도출 가능했다.

### Prevention

**1. `docs/RECURRING_FAILURES_AND_GUARDRAILS.md`에 새 섹션 추가 권장:**

> **overflow-hidden은 해결이 아니라 은폐일 수 있다**: 콘텐츠가 컨테이너를 벗어날 때, `overflow-hidden`을 적용하기 전에 "이 콘텐츠가 잘려도 되는가?"를 먼저 판단한다. 잘리면 안 되는 콘텐츠라면, 컨테이너가 콘텐츠 크기를 수용하도록 레이아웃을 수정해야 한다.

**2. `nuri-gpt-frontend/frontend/docs/GUARDRAILS.md` — 레이아웃 오버플로우 섹션에 판단 기준 추가 권장:**

> - **"이 콘텐츠가 잘려도 기능적으로 문제없는가?"** → 잘리면 안 되면 `overflow-hidden` 대신 레이아웃(포지셔닝, 높이) 자체를 수정

**3. Root `agents.md`는 변경 불필요** — 이미 "증상이 아닌 근본 원인을 해결하라"는 원칙이 있음. 이번 실패는 원칙의 부재가 아니라 원칙의 미적용이었음.
