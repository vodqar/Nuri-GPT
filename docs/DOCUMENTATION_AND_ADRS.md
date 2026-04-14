# Documentation and ADRs

## Purpose

Record not only code changes but also the rationale behind decisions to prevent future developers from repeating the same decision-making process.

## When to Use

- When making significant architectural decisions.
- When changing public APIs or user-facing behavior.
- When you find yourself repeating the same explanation multiple times.
- When the reasoning behind a major UI structure choice needs to be preserved.

## Nuri-GPT Documentation Principles

- Record the **reasoning for the decision**, not just the code.
- Prioritize documenting constraints, trade-offs, and alternative comparisons over implementation details.
- Manage documents alongside the Table of Contents (ToC).
- If code is changed, simultaneously verify the relevant Root, Backend, and Frontend documentation.
- Do not leave recurring failures or late-discovered constraints only in retrospective documents; promote them to appropriate high-level documentation.
- Aim for principle-centered guardrails that aid future decision-making rather than merely listing every exception.

## When an ADR is Required

- Changes to the dynamic template rendering method.
- Changes to the authentication/authorization structure.
- Changes to LLM invocation policies or core prompt rules.
- Changes to frontend state management strategies.
- Changes to external service integration methods.

## Recommended Record Format

```md
# Title

## Status

## Context

## Decision

## Alternatives Considered

## Consequences
```

## Operating Rules

- If a new document is created that is not in the Root `agents.md` ToC, the ToC must be updated accordingly.
- If Backend/Frontend implementation rules change, update the respective sub-directory `agents.md` or relevant `docs/`.
- Prioritize "gotcha" documentation necessary for preventing recurrence over obvious comments explaining the code.
- Use handoff, retrospective, and temporary plan documents for session-specific context, while `agents.md` or ToC documents handle repeatable rules.

## Completion Checklist

- [ ] The reason for the change is documented.
- [ ] Relevant ToCs are up to date.
- [ ] An ADR or decision document exists if the decision is repeatable.
- [ ] There are no contradictions between the code and the documentation.

*Last Updated: 2026-04-13*