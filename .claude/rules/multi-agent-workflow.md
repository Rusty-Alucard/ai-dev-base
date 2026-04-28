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
4. **Paste the full contents of `.claude/templates/subagent-preamble.md` at the top of the prompt.** Task-specific context follows below the preamble. This is mandatory — it is the mechanism that enforces the skill activation gate.
5. Specify the `model` parameter explicitly (see "Model Selection Policy" below)
6. On completion, record new insights in the persona file's `Learnings` section

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

### Reasoning Sandwich — Phase-to-Model Mapping

| Phase | Typical Agents | Recommended Model | Rationale |
|---|---|---|---|
| Plan / Design | PdM, Architect(s) | `claude-opus` | Trade-off analysis and ambiguity resolution benefit from deeper reasoning |
| Review | Reviewer | `claude-opus` | Multi-axis scoring and cross-cutting quality judgment |
| Implementation | Coder(s) | `claude-sonnet` | Specs are clear; deep reasoning is not required |
| Search / Research | Grep/Read-only agents | `claude-haiku` | File lookup and reference confirmation only |

Model family names (`claude-opus`, `claude-sonnet`, `claude-haiku`) are generic;
use the current stable version identifiers supported by your Claude Code install.

### Principle: The `model` Parameter Must Not Be Omitted

The PM **must specify** the `model` parameter on every Agent launch. When the
parameter is omitted, the session falls back to the heaviest model, which
drives unnecessary cost on implementation and research tasks. When in doubt,
default to `sonnet`; escalate to `opus` only for planning or review.

In practice, teams that skip this rule see a large majority of token spend
concentrated on the heaviest model even though most work is well within
`sonnet` capability — defeating the purpose of the matrix above.

## Principles

- The PM uses the Agent tool to launch sub-agents
- Independent phases (Test, Lint) should run in parallel for efficiency
- Each agent must receive sufficient context: target files, conventions, expected deliverables
- If an agent's output has issues, issue correction instructions and re-run rather than editing directly
- **Reviewer is a mandatory gate.** The PM must not skip Review. Work may not
  proceed to Verify (Test + Lint) until the Reviewer approves (overall score
  ≥ 4.0; see `.claude/agents/reviewer.md` for the scoring rubric).

## Permissions Model and Autonomous Execution

Subagent autonomous execution (write/edit) is enabled via
`.claude/settings.json` (team-shared, committed). See
`.claude/rules/security.md` ("Claude Code Permissions Model") for details.

### PM Responsibilities (Permissions)

- If a subagent is blocked on permissions, updating `.claude/settings.json`
  so the subagent can execute autonomously is preferable to the PM editing
  files directly. Direct edits are a last resort.
- When a new write-target directory appears, add it to `allow` in
  `.claude/settings.json` before delegating.
- If a sensitive file pattern is discovered, add it to `deny` immediately.
