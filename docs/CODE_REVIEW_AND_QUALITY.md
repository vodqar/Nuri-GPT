# Code Review and Quality

## Purpose

Reduce incomplete changes by verifying scope, quality, validation, and documentation synchronization before finishing a task.

## When to Use

- When finalizing an implementation.
- When a final check is required before a PR or commit.
- When verifying for regressions after a bug fix.

## Common Quality Gates

### Scope
- Does it solve only the requested problem?
- Has adjacent code been left untouched unless necessary?
- Is the new abstraction actually required?

### Correctness
- Does the implementation align with existing rules and documentation?
- Does exception handling point to actual failure points?
- For bug fixes: Is there a reproduction path or a test case?

### Verification
- **Backend changes**: `venv/bin/pytest -q`
- **Frontend changes**: `npm run lint`, `npm run build`
- **Browser/UI changes**: Validate console, network, and visual state.

### Documentation
- Are the relevant documents listed in the Root / Backend / Frontend ToCs up to date?
- Are new operational rules or "known gotchas" reflected in the documentation?
- Is there any role conflict or "information drift" between the README, SUMMARY, handoff, temporary plans, and ToC documents?
- Have repeatable lessons learned from this task been promoted to appropriate high-level documentation rather than remaining only in session logs?

## Project-Specific Checks

### Backend
- Is the DI (Dependency Injection) pattern maintained?
- Are external dependencies connected via constructor injection or factories?
- Is the structure unit-testable without external infrastructure?

### Frontend
- Is the `features/` isolation principle followed?
- Is business logic kept separate from UI components?
- Does it adhere to the color, layer, and spacing principles defined in `DESIGN.md`?

## Review Result Format

```md
## Scope
- pass/fail

## Verification
- pass/fail

## Docs
- pass/fail

## Risks
- item