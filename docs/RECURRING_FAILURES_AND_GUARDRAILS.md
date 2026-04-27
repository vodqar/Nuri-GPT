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

## Macro Guardrails (핵심 철학)

가장 빈번하게 발생하는 실패를 관통하는 두 가지 핵심 행동 원칙입니다. 모든 에이전트는 작업 시 이 두 가지 원칙을 최우선으로 준수해야 합니다.

### 1. 추측(Assumption) 기반 구현 및 땜질(Band-aid) 금지
과거 지식이나 표면적인 현상만 보고 코드를 짜거나 임시방편을 적용하지 마십시오.
- **외부 연동**: API나 외부 서비스 연동 구현 전, 반드시 최신 공식 문서를 확인하고 스크립트(`curl` 등)로 실제 연결과 지연 시간을 증명한 후 구현하십시오. (사례: 잘못된 주소 사용, 타임아웃 미확인)
- **레이아웃/오버플로우**: 넘치는 현상을 가리기 위해 `overflow-hidden`을 맹목적으로 덥어씌우지 마십시오. 구조 계산을 통해 근본 원인을 수정해야 합니다.

### 2. 맹목적 검증 패스(Blind-Pass) 불가 및 적극적 에스컬레이션
코드를 수정한 뒤 임의로 검증을 생략하거나 건너뛰고 턴을 종료하지 마십시오.
- **기계적 검증**: 편집 도구의 특성상 들여쓰기 훼손이나 구문 오류가 발생할 수 있습니다. 수정 직후 파이썬 환경이라면 터미널(`py_compile` 등)로 최소한의 무결성을 스스로 입증해야 합니다.
- **장애 대처**: 브라우저 UI 검증 중 "로그인이 필요하다" 등 테스트할 수 없는 장벽을 만났을 때, "확인이 불가하여 종료한다"고 타협하지 마십시오. 사용자에게 권한이나 해결 방법을 강하게 요구(Escalate)하십시오.

---

## Completion Checklist

- [ ] Distinguished whether the lessons learned this time are one-off notes or repeatable principles.
- [ ] Reflected repeatable principles in the appropriate higher-level documentation.
- [ ] Ensured documentation is not so overly specific that it fails to account for necessary exceptions.
- [ ] Verified that there are no conflicts in roles or priorities between related documents.

### 3. 환경 변수 → 설정 객체 파싱: pydantic-settings `List[str]` 함정

pydantic-settings의 `EnvSettingsSource`는 단일 문자열 값을 `List[str]` 필드에 안전하게 파싱하지 않는다. `.env`의 단일 URL과 다중 URL(쉼표 구분)이 모두 동일하게 작동해야 할 때, `List[str]` 타입 대신 `str`로 선언하고 애플리케이션 레벨에서 `split(",")` 처리하라. (사례: `CORS_ORIGINS` — `report/2026-04-22-pydantic-settings-list-env-parse.md` 참조)

> **판단 기준**: env source의 파싱이 `field_validator`보다 먼저 실행될 수 있다. validator로 "추후 보완"하는 설계는 구멍이 생긴다.

---

*Last Updated: 2026-04-22*