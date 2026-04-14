# Planning and Task Breakdown

## Purpose

Break down large tasks into small, verifiable units to keep the system in a functional state at every stage.

## When to Use

- When a task involves modifying multiple files.
- When a task requires synchronized changes across frontend, backend, and documentation.
- When fixing bugs with a high risk of regression.
- When a task requires approval points before full implementation.

## Nuri-GPT Planning Principles

- Proceed with only one logical change at a time.
- Each step must be immediately verifiable upon completion.
- Do not postpone testing, building, or documentation updates until the end.
- Avoid creating new abstractions that supersede existing rules unless absolutely necessary.

## Recommended Breakdown Methods

1. **Vertical Slice First**
   - Example: Instead of doing "Add API → Connect Frontend → Display UI" separately, cut the task into the smallest possible end-to-end flow visible to the user.

2. **Risk-First Splitting**
   - Validate the most uncertain parts first.
   - Example: For a dynamic form layout, verify the rendering capability first before implementing detailed interactions.

3. **Include Document Synchronization**
   - Explicitly list the modification of relevant ToC documents as a standalone task.

## Plan Format

```md
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

## Example

```md
1. Clarify the template rendering data path -> verify: existing template loading remains intact
2. Attach a minimal layout renderer -> verify: core sample JSON renders in the browser
3. Update documentation and verification routines -> verify: relevant docs and agents.md are up to date
```

## Completion Checklist

- [ ] Task is divided into 2–5 outcome-oriented steps.
- [ ] Each step has a specific verification method.
- [ ] Only one step is in progress at any given time.
- [ ] Documentation updates are included in the plan.
- [ ] No incomplete items remain after finishing the plan.

*Last Updated: 2026-04-13*
