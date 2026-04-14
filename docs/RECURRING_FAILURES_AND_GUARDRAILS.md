# Recurring Failures and Guardrails

## Purpose

Establish criteria for promoting recurring failures, structural constraints discovered post-implementation, and lessons learned from retrospectives into higher-level context to ensure they are integrated into future workflows.

## When to Use

- When similar mistakes or workarounds occur repeatedly.
- When core constraints are discovered late in the development cycle or during browser validation.
- When critical lessons remain trapped in handoffs, retrospectives, or plan documents without being reflected in high-level documentation.
- When there is a risk of development-only bypasses, experimental paths, or environment-specific workarounds bleeding into the actual user flow.

## Principles

### 1. Promote Recurring Lessons
- Decision-making criteria with a high probability of re-emergence should be elevated to `agents.md` or relevant `docs/` rather than remaining as one-time notes.
- Retrospectives, plans, and handoffs are starting points, not final destinations.

### 2. Prioritize Judgment Criteria Over Rules
- Instead of a "blacklist" of every exception, provide the judgment criteria needed to identify risks in various situations.
- Documentation should act as guardrails that facilitate good default choices, rather than a rigid rulebook that stifles the worker.

### 3. Prevent Temporary Bypasses from Becoming Defaults
- Bypasses for development convenience, experimental flows, and debugging tools must have a clear purpose and scope.
- If these tools persist, they must remain isolated from the primary user experience, and their current status must be explained in relevant documentation.

### 4. Solve Structural Issues Structurally
- If the responsibility for an issue is unclear among prompts, UI, API, or data structures, redefine the interfaces/boundaries.
- If one layer expects a stable contract, document which layer is responsible for guaranteeing that contract.

### 5. Clarify Document Hierarchy
- Operational rules and current task instructions are governed primarily by `agents.md` and documents listed in the ToC.
- `README`, `SUMMARY`, handoffs, and temporary plan documents provide background and context but must not serve as the final source of truth for operational rules.

## Promotion Criteria

Review for promotion to higher-level documentation if any of the following apply:

- The same or a similar failure has occurred two or more times.
- An issue was discovered late in the process, resulting in high correction costs.
- Lack of knowledge regarding a specific area's hidden constraints easily leads to incorrect implementations.
- Adding a single-sentence principle is highly likely to improve the quality of future work.

## Location Guide

- **Root `agents.md` / root `docs/`**: Cross-domain workflows, documentation standards, and verification methods.
- **Backend Documentation**: API contracts, post-processing responsibilities, output stabilization, and data boundaries.
- **Frontend Documentation**: User flows, temporary UI bypasses, interaction consistency, and browser validation perspectives.
- **Handoff / Plan**: Specific context for the current session, task handovers, and observational notes pending promotion.

## Known Patterns

### overflow-hidden은 해결이 아니라 은폐일 수 있다
콘텐츠가 컨테이너를 벗어날 때, `overflow-hidden`을 적용하기 전에 "이 콘텐츠가 잘려도 되는가?"를 먼저 판단한다. 잘리면 안 되는 콘텐츠라면, 컨테이너가 콘텐츠 크기를 수용하도록 레이아웃(포지셔닝, 높이, flow 방식)을 수정해야 한다. `overflow-hidden`은 증상 은폐이지 근본 수정이 아닐 수 있다.

- **사례**: `absolute inset-0` 오버레이가 부모의 자연 높이(버튼 1개)에 제한되어 콘텐츠가 넘침 → `overflow-hidden`으로 잘라내면 예시 기능 무효화 → normal flow로 전환이 올바른 수정
- **참고**: `nuri-gpt-frontend/frontend/docs/GUARDRAILS.md`, `report/2026-04-14-overlay-overflow-misdiagnosis.md`

### 복잡한 백엔드 수정 시 구문 검증은 필수이다
`multi_replace_file_content` 등을 활용하여 다중 라인 혹은 여러 지점을 동시에 수정할 때, 특히 파이썬처럼 들여쓰기에 민감한 언어의 경우 의도치 않은 `IndentationError`나 `SyntaxError`가 발생할 가능성이 매우 높다. 대규모 수정 후에는 반드시 수동으로 코드를 재검토하거나, 공식적인 구문 검사 도구를 실행하여 무결성을 확인해야 한다.

- **원칙**: 모든 백엔드 코드 수정 작업 완료 직후, `python -m py_compile <수정된_파일_경로>`를 실행하여 구문 오류 여부를 즉시 확인한다.
- **사례**: Quota 시스템 통합 과정에서 다중 `return` 블록의 범위를 잘못 지정하여 `IndentationError` 및 `SyntaxError` 유입 → 서버 로딩 중단 발생
- **참고**: `report/2026-04-15-endpoint-syntax-errors.md`

---

## Completion Checklist

- [ ] Distinguished whether the lessons learned this time are one-off notes or repeatable principles.
- [ ] Reflected repeatable principles in the appropriate higher-level documentation.
- [ ] Ensured documentation is not so overly specific that it fails to account for necessary exceptions.
- [ ] Verified that there are no conflicts in roles or priorities between related documents.

*Last Updated: 2026-04-14*