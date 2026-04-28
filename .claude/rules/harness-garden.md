---
description: Harness Gardening — Learnings promotion process
---

# Harness Gardening

## Principle

"Failure is not punishment — it is a signal that the harness can be strengthened."

Insights that agents record as `Learnings` graduate from local observations to
team-wide rules through repeated occurrence. This graduation process is called
gardening.

## The 3-Strike Promotion Rule

When entries sharing the same `#tag` have been recorded **three or more times**
across persona Learnings, the PM should consider promoting that knowledge into
a shared rule file under `.claude/rules/`.

### Promotion Criteria

| Question | Yes | No |
|---|---|---|
| Applies to all agents? | Promote to `.claude/rules/` | Keep in persona Learnings |
| Limited to a specific domain (e.g. SQL, Python)? | Keep in persona Learnings, or update that persona only | — |
| Can be absorbed by an existing rule file? | Extend the existing file | Create a new rule file |

### Detection Procedure

1. Run the weekly usage report (`bin/claude-usage.py`) and review the
   Learnings tag aggregation section
2. Any tag with three or more occurrences is a promotion candidate
3. The PM evaluates context and decides: promote, retain, or merge
4. When a promotion occurs, append an entry to the Promotion History below

### Promotion Workflow

1. Collect the Learnings entries for the target tag
2. Abstract and generalize the pattern (add a "why" rationale, not just a list)
3. Add to the appropriate file under `.claude/rules/` (extend or create)
4. Annotate each original persona Learnings entry with
   `→ promoted to .claude/rules/<file>.md`
5. Record the promotion in the Promotion History table below

## Periodic Monitoring

| Cadence | Action |
|---|---|
| Weekly | Check for 3-strike tags in the usage report |
| Monthly | Review promoted rules for continued relevance; archive if obsolete |
| PR review | Reviewer flags Learnings tags approaching the 3-strike threshold |

## Promotion History

Append one row per promotion event.

| Date | Tags | Target File | Summary |
|---|---|---|---|
| — | — | — | — |
