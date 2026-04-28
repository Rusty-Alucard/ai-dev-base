# Subagent Launch Preamble

Before starting the task you are about to receive, run this 30-second checklist.

## Pre-Task 30-Second Checklist

### Step 1 — Check existing skills

<!-- Project teams: keep this table in sync with .claude/commands/ -->
<!-- If a project has no custom skills, leave the (none defined) row in place — do not remove the heading or table. -->

| Command | Scope |
|---|---|
| (none defined) | — |

### Step 2 — Scope match and action

| Match | Action |
|---|---|
| Task falls **fully within** a skill's scope | `Skill({ skill: "{command}", args: "..." })`, then build on its output |
| **Similar but not identical** | Record a skill improvement proposal, then proceed |
| **Unrelated** | Proceed with the task |

Skill Improvement Proposal format (record and report to PM):

```text
Skill Improvement: {command} / Current problem: ... / Proposed change: ... / Target: .claude/commands/{file}.md
```

## Required Completion Report Fields

1. Files created/changed (absolute paths)
2. Acceptance criteria status (item-by-item Yes/No)
3. Skill proposals (only if applicable — new or improvement)
4. Learnings (only if applicable — `#tag` required at the head of each entry)
5. Branch protection confirmation — no direct commit or push to `main`

## Permissions Note

Write/Edit can only reach paths listed in `.claude/settings.json` under `allow`.
If blocked, do not try to work around it — report the block to the PM
immediately.

## Detailed References

- Full skill checklist: `.claude/rules/skill-activation.md`
- Learnings tag rules: `.claude/rules/agent-common.md`
- Coding conventions: `.claude/rules/coding-conventions.md`
- Security and permissions: `.claude/rules/security.md`
