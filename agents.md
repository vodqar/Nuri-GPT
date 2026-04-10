Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

---

## Documentation ToC

### Root
- **TESTING_GUIDE.md** — Guide for running tests, mocking strategies, and debugging procedures

### Backend (`nuri-gpt-backend/`)
- **agents.md** — Backend-specific guidelines (dependency management, testing isolation, DB schema, framework specs, DoD)
- **docs/OVERVIEW.md** — Project purpose, tech stack, environment setup, execution methods
- **docs/ARCHITECTURE.md** — Layer structure, module dependencies, data flow diagrams
- **docs/API_REFERENCE.md** — Full REST API endpoint list and parameter definitions
- **docs/DEVELOPMENT.md** — DI structure, feature addition checklist, debugging guide, test structure
- **docs/DYNAMIC_UI_PLAN.md** — Dynamic rendering of template structure JSON in frontend
- **docs/SECURITY.md** — Authentication, authorization security policies and implementation guide

### Frontend (`nuri-gpt-frontend/frontend/`)
- **agents.md** — Frontend-specific guidelines (Feature-First architecture, component hierarchy, engineering rules, agent protocols, DoD)
- **docs/OVERVIEW.md** — Service purpose, core features, tech stack, execution methods
- **docs/ARCHITECTURE.md** — Feature-First directory structure, dependency rules, state management strategy
- **docs/DEVELOPMENT.md** — Code writing principles, component rules, MSW mocking, DoD checklist
- **docs/SERVER_GUIDE.md** — Frontend/backend server execution, port settings, troubleshooting
- **docs/DIFY_CHATFLOW_SETUP.md** — Dify Chatflow setup guide for regeneration API
- **docs/DESIGN.md** — UI/UX design philosophy (Color, Typography, Elevation)

> **Note**: After completing work, update the relevant documents in this ToC that were affected by your changes. If no documentation was updated, the task is not complete.

---

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## 5. Plan-Approve-Commit Workflow

For substantive coding or multi-step changes:
1. **Plan**: Document problem and solution in MD file
2. **Approve**: Get user approval before implementing
3. **Commit**: Ask user to confirm commit after completion

Does not apply to simple questions, quick lookups, or trivial one-line edits.