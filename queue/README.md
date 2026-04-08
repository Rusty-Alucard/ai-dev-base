# Task Queue

This directory manages tasks using a YAML-based queue system.
The PM agent owns the lifecycle of all task files.

## Directory Structure

```
queue/
  backlog/      — Tasks not yet started
  in_progress/  — Tasks currently being worked on
  done/         — Completed tasks (retained for knowledge)
```

## Task YAML Specification

### Required Fields

```yaml
id: "NNNN"                    # Task ID (4-digit zero-padded, e.g. "0001")
title: "Task title"
type: feat|fix|refactor|docs|chore|test
status: backlog|in_progress|done
priority: high|medium|low
assignee: pm|design|coding|test|lint
created: "YYYY-MM-DD"
description: |
  What to do and why.
acceptance_criteria:
  - "Criterion 1"
  - "Criterion 2"
context_files:
  - "path/to/relevant/file"
report: |
  Execution report — filled in by the IC agent upon completion.
```

### Optional Fields

```yaml
depends_on:
  - "NNNN"                    # IDs of tasks that must complete first
branch: "feat/my-feature"     # Git branch name for this task
estimated_hours: 2
```

## File Naming

Files must be named: `NNNN-slug.yaml`

Examples:
- `0001-init-schema.yaml`
- `0002-add-etl-script.yaml`
- `0015-fix-type-error.yaml`

## Workflow

```
1. PM creates task YAML in backlog/
2. PM moves file to in_progress/, delegates to IC agent
3. IC agent executes task, fills in the report field
4. PM reviews the report and acceptance criteria
5. PM moves file to done/
```

## Rules

- Task IDs are sequential integers. Gaps are allowed (e.g. after deletion).
- Completed tasks remain in `done/` — they serve as a knowledge record.
- Each task should be assigned to exactly one IC agent role. Split complex work into multiple tasks.
- The `report` field is left empty (`""` or omitted) until the task is completed.
- Do not delete task files from `done/` — archive instead by setting `status: done`.
