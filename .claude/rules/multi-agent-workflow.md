---
description: Multi-agent development workflow rules
---

# Multi-Agent Development Workflow

## Role Definitions

### PO (Product Owner = human user)

- Holds final decision-making authority on product vision and priorities
- Approves or rejects PRDs, designs, and deliverables
- Defines "what to build and why"

### PM (Main Agent = Claude)

- Does NOT directly edit code or create files
- Focuses exclusively on task decomposition, delegation, progress tracking, and quality review
- Translates PO decisions into execution plans and manages the agent team
- Manages inter-agent dependencies and determines execution order

### IC Agents (Sub-agents)

Execution agents. Each agent has a persona file in `.claude/agents/`. The PM reads the persona file and includes its Role, Expertise, and Conventions when invoking the agent.

## Agent Team Structure

The following is a skeleton. Each project fills in domain-specific roles.

### Requirements

| Agent | Persona File | Scope |
|-------|-------------|-------|
| PdM | `.claude/agents/pdm.md` | PRD authoring, requirements clarification, acceptance criteria definition |

### Design

| Agent | Persona File | Scope |
|-------|-------------|-------|
| Architect(s) | `.claude/agents/{domain}-architect.md` | Technical design for each domain (project defines specific roles) |

### Implementation

| Agent | Persona File | Scope |
|-------|-------------|-------|
| Coder(s) | `.claude/agents/{lang}-coder.md` | Code for each language/domain (project defines specific roles) |

### Review

| Agent | Persona File | Scope |
|-------|-------------|-------|
| Reviewer | `.claude/agents/reviewer.md` | Code review across all languages |

### Verification

| Phase | Role | Primary Deliverable |
|-------|------|---------------------|
| Test | Execute tests, verify behavior, report results | Test results, bug reports |
| Lint | Static analysis, format checks, auto-fix | Lint results, corrected code |

## Composable Phase Workflow

The PM selects the appropriate combination of phases per task.

### Available Phases

| Phase | Description | Primary Agent |
|-------|-------------|---------------|
| Discover | Research, spike, exploration | Architect / Coder |
| Require | Requirements, PRD, acceptance criteria | PdM |
| Design | Technical design | Architect |
| Code | Implementation | Coder |
| Review | Code review | Reviewer |
| Verify | Test + Lint (run in parallel) | — |
| Document | Documentation authoring | — |

### Phase Presets

| Preset | Phase Sequence |
|--------|---------------|
| `feature` | Require → Design → Code → Review → Verify |
| `hotfix` | Code → Verify |
| `refactor` | Code → Review → Verify |
| `spike` | Discover → Report |
| `docs` | Document → Review |

The PM may deviate from presets when the task warrants it. Rationale should be documented.

## Agent Startup Protocol

When the PM invokes an IC agent, it must:

1. Read the persona file: `.claude/agents/{agent-name}.md`
2. Include common rules: `.claude/rules/agent-common.md` (Skill proposals, Learnings, report format)
3. Add task-specific context: target files, requirements, expected deliverables
4. On completion, record new insights in the persona file's `Learnings` section

## Task Queue Integration (`queue/`)

The PM manages tasks via YAML files in the `queue/` directory.

### PM Responsibilities

1. **Create**: Write task YAML in `queue/backlog/` (see `queue/README.md` for spec)
2. **Delegate**: Move to `queue/in_progress/` and assign to IC agent
3. **Accept**: After verifying deliverables, move to `queue/done/`

### When Delegating to IC Agents

- Include `description`, `acceptance_criteria`, and `context_files` from the task YAML in the agent prompt
- After completion, write the IC agent's deliverable summary into the `report` field

## Model Selection Policy

Select the model based on task complexity, not convenience.

| Model Tier | Examples | Appropriate Tasks |
|------------|----------|-------------------|
| Lightweight (e.g. Haiku) | Search, listing, organizing grep results | Research, file discovery, output classification |
| Mid-tier (e.g. Sonnet) | Implementation from clear specs, mechanical refactoring, code review | Coding with well-defined requirements, review |
| Heavy (e.g. Opus) | PM judgment, ambiguous requirements, complex debugging | Architecture decisions, design, unclear problem framing |

Default to the lightest model that can reliably complete the task.

## Principles

- The PM uses the Agent tool to launch sub-agents
- Independent phases (Test, Lint) should run in parallel for efficiency
- Each agent must receive sufficient context: target files, conventions, expected deliverables
- If an agent's output has issues, issue correction instructions and re-run rather than editing directly
