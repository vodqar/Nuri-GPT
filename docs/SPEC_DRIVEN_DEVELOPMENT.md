# Spec-Driven Development

## Purpose

Define the problem, scope, non-goals, and success criteria clearly before implementation to reduce the cost of failure for large-scale tasks.

## When to Use

- When implementing requirements that are subject to multiple interpretations.
- When performing tasks that change the user experience (UX) or API behavior.
- When a task simultaneously affects both the frontend and backend.
- When design choices dictate the quality of the outcome, such as in dynamic UI rendering.

## Nuri-GPT Basic Procedure

1. **Problem Definition**
   - Write a single sentence describing what is inconvenient, what is broken, or what you intend to change.

2. **Verify Related Documentation**
   - Always read the root `agents.md` first.
   - For backend tasks, read `nuri-gpt-backend/agents.md` and the relevant `docs/`.
   - For frontend tasks, read `nuri-gpt-frontend/agents.md` and the relevant `frontend/docs/`.
   - For dynamic form/layout tasks, prioritize checking `nuri-gpt-backend/docs/DYNAMIC_UI_PLAN.md` and `nuri-gpt-frontend/frontend/docs/DESIGN.md`.

3. **Separate Scope and Non-Goals**
   - List only the items that will be changed in this specific task.
   - Explicitly define "Non-Goals" for items that may seem beneficial but are not included in the current scope.

4. **Define Success Criteria**
   - Describe how success will be proven after the code changes.
   - Examples: `venv/bin/pytest -q` pass, `npm run lint` pass, manual browser verification complete, relevant documentation updated.

5. **Establish Approval Points Before Implementation**
   - For large tasks, record the problem and proposed solution in a planning document or a short Markdown file before starting implementation.

## Output Template

```md
## Problem

## Context

## Scope

## Non-Goals

## Proposed Change

## Verification
```

## Project Principles

- Do not implement based on speculation.
- If the documentation differs from the actual structure, include a plan to update the documentation.
- Any change that alters behavior must include a test or a reproducible verification procedure.
- If design uncertainty remains, do not proceed with implementation immediately; instead, summarize the available options and trade-offs first.

## Completion Checklist

- [ ] The problem and scope are clearly defined.
- [ ] Relevant documentation has been reviewed and reflected.
- [ ] Success criteria are in a verifiable format.
- [ ] Approval points have been established before implementation.
- [ ] Documents to be updated after the change have been identified.

*Last Updated: 2026-04-13*
