---
description: Skill activation gate for subagents
---

# Skill Activation Gate

Before starting any task, the agent must run the checklist below. This applies
to both the PM and subagents.

## Pre-Task Checklist

### Step 1 — Enumerate existing skills

Review the skill table at the top of `.claude/templates/subagent-preamble.md`,
which mirrors the files under `.claude/commands/`. Project teams maintain that
table as skills are added or removed.

### Step 2 — Scope match

| Match | Action |
|---|---|
| Task falls **fully within** an existing skill's scope | Invoke the skill via the Skill tool |
| Task is **similar but not identical** | Record a skill improvement proposal, then proceed with the task |
| Task is **unrelated** | Proceed with the task |

### Step 3 — Invoke the skill

```text
Skill({ skill: "{command-name}", args: "{arguments}" })
```

Use the skill output as the starting point for the deliverable. Modify as
required.

### Step 4 — Record a skill improvement proposal (when applicable)

Use the format defined in `.claude/rules/agent-common.md`
("Skill Improvement Proposal").

### Step 5 — Confirm recurrence

After task completion, consider whether this work will recur:

- **Recurs** → propose a new skill using the format in
  `.claude/rules/agent-common.md` ("New Skill Proposal")
- **One-off** → no proposal needed

## Instructing Subagents

When the PM invokes a subagent, it must paste the entire content of
`.claude/templates/subagent-preamble.md` at the top of the prompt. The
preamble contains the inline checklist (Steps 1–3). Only when a task requires
Steps 4–5 or the periodic monitoring details should the subagent be directed
to read this file in full.

## Periodic Monitoring

| Cadence | Action |
|---|---|
| Weekly | Review the skill activation rate in the usage report |
| 2 weeks of zero activations | Review the skill's documentation and announcement; check whether the description is unclear |
| When a skill is added or removed | Sync the skill table in `.claude/templates/subagent-preamble.md` |
