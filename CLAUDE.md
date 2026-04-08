# CLAUDE.md

## Project Overview

{{project_description}}

## Tech Stack

- **Languages**: {{languages}}
- **Frameworks / Libraries**: {{frameworks_and_libraries}}
- **Infrastructure / Cloud**: {{cloud_and_infra}}
- **Data / Storage**: {{databases_and_storage}}
- **IaC**: {{iac_tool}} (`infra/` directory)

## Directory Structure

```
.
├── CLAUDE.md
├── .claude/
│   ├── agents/          # IC agent personas
│   ├── commands/        # Reusable slash-command skills
│   └── rules/           # Shared agent rules
├── context/             # Project knowledge, architecture, ADRs
├── memory/              # Long-term agent memory
├── queue/               # YAML task queue (backlog / in_progress / done)
├── infra/               # Infrastructure-as-code
├── schema/              # Database schemas / DDL
├── scripts/             # Data processing and utility scripts
├── tests/               # Automated tests
└── docs/                # User-facing guides and operation runbooks
```

Add project-specific directories above as needed.

## Current Phase

**{{current_phase_name}}**

{{current_phase_description}}

### In scope for this phase
- {{in_scope_item_1}}
- {{in_scope_item_2}}

### Out of scope (deferred)
- {{out_of_scope_item_1}}
- {{out_of_scope_item_2}}

## Commands

```bash
# Lint / Format
{{lint_command}}
{{format_command}}

# Tests
{{test_command}}

# Infrastructure
cd infra/
{{iac_init_command}}
{{iac_plan_command}}
{{iac_apply_command}}

# Project-specific scripts
{{custom_script_example}}
```

## Coding Conventions

See `.claude/rules/coding-conventions.md` for the full reference.

Project-specific additions:
- **Primary language**: {{primary_language}} — formatter: `{{formatter}}`, linter: `{{linter}}`
- **SQL dialect**: {{sql_dialect}}
- **Commit message format**: `<type>: <subject>` (English)
  - Types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`

## Branch Strategy

See `.claude/rules/branch-protection.md` for the full reference.

- Direct commits and pushes to `main` are prohibited.
- All changes must go through a pull request.
- Branch naming: `<type>/<description>` (e.g., `feat/add-ingestion`, `fix/schema-typo`)

## Security

See `.claude/rules/security.md` for the full reference.

- Never commit secrets, credentials, or service account keys.
- Never commit real user data or personally identifiable information.
- Secrets in development: local `.env` file (git-ignored).
- Secrets in production: {{secret_manager}} (Phase 2+).

## 4-Layer Context Management Architecture

Structured knowledge management so agents always have the right context at the right granularity.

| Layer | Name | Location | Update Frequency | Content |
|---|---|---|---|---|
| Layer 0 | Tool Config | `CLAUDE.md`, `.claude/rules/` | Low | Agent behavior config, coding conventions |
| Layer 1 | Memory | `memory/` (auto-memory) | Per session | Long-term knowledge across sessions |
| Layer 2 | Project Context | `context/` | Per phase change | Project knowledge, design, ADRs |
| Layer 3 | Task Queue | `queue/` | Per task | YAML-based task management |

### Key files

- `context/project.md` — Universal Context Template (What / Why / Who / Constraints / Current State / Decisions / Notes)
- `context/architecture.md` — Technical architecture, data model, infrastructure overview
- `context/decisions.md` — Decision log (ADR format)
- `queue/README.md` — Task YAML spec and workflow definition

## External Design Spec Integration

*(Optional — remove this section if design specs are managed entirely within this repo.)*

Design specifications are maintained externally in {{external_spec_tool}}. When implementing a feature, always fetch the latest spec from the external source before starting work.

### Two-Layer Document Pattern

External design documents follow a two-layer structure:

| Section | Audience | Content |
|---|---|---|
| Upper half | Humans (stakeholders, PMs) | Summary, background, rationale |
| Lower half (code blocks) | Agents | Structured specs in YAML/JSON |

When conflicts exist between the narrative and the structured spec, **the structured spec takes precedence**. Report any conflicts.

### Structured Spec Block Types

Code blocks in design documents use a `lang # tag` convention:

- `yaml # schema` — table/model schema definition
- `yaml # etl-flow` — pipeline spec (source, transforms, destination)
- `yaml # api-spec` — external API connection spec
- `yaml # mapping` — code/value mapping tables
- `json # sample-data` — sample data for testing

### Implementation Flow

```
1. Fetch the design spec from the external source
2. Extract structured spec blocks
3. Implement according to the spec
4. After testing, record results back in the external source
```

## Session Recovery Steps (after /clear)

Restore context in this order:

1. `CLAUDE.md` (auto-loaded)
2. Read `context/project.md` — current phase, progress, constraints
3. Check `queue/in_progress/` — any tasks currently in flight
4. Review `memory/` — prior decisions and lessons learned
5. Read `context/architecture.md` and `context/decisions.md` as needed
