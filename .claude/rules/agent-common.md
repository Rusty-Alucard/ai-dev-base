# Agent Common Rules

Rules applied to all IC agents (PdM, Architect, Coder, Reviewer, and others).

## Skill Proposals

When completing a task, if you discover a reusable work pattern, propose it to the PM.
There are two types of proposals: new skills and improvements to existing skills.

### Existing Skills

Review `.claude/commands/` before starting any task. If a relevant skill exists, use it.

### New Skill Proposal

When you identify a repeatable pattern with clear inputs and outputs:

```text
Skill Proposal (New): {skill name}
- Trigger: when and why this skill would be invoked
- Input: required parameters or context
- Output: what is generated or executed
- Recurrence: how often this pattern is likely to repeat
```

### Existing Skill Improvement Proposal

When you notice a gap or deficiency in an existing skill during execution:

```text
Skill Improvement: {target command name}
- Current problem: what is missing or not working
- Proposed change: specific improvement
- Target file: .claude/commands/{file}.md
```

### Do Not Propose

- One-time tasks with no recurrence
- Things already defined in `.claude/rules/` or project-level docs
- Simple commands already automated by CI (e.g. a linter invocation)

## Learnings

When completing a task, record newly gained insights in your persona file's `Learnings` section
(`.claude/agents/{your-name}.md`).

Record:

- Project-specific constraints or gotchas (e.g. a field that is intentionally null in production)
- Design decision rationale that is useful but does not warrant a formal ADR
- Workarounds for known issues or environment quirks

## Deliverable Report

When reporting back to the PM after task completion, always include:

1. **Files created/changed** — list of absolute file paths with a brief description of each change
2. **Acceptance criteria fulfillment** — status of each criterion (met / not met / partial, with notes)
3. **Skill proposals** — if any (use format above); omit section if none
4. **Learnings** — if any new insights were gained; omit section if none
