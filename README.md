# ai-dev-base

A reusable base template for AI-driven software development using Claude Code multi-agent workflows.

Fork or copy this repo as the starting point for any new project. Fill in the `{{placeholder}}` values in `CLAUDE.md` and adapt the agent personas under `.claude/agents/` to your stack.

---

## What this repo provides

Eight core patterns for structured, repeatable AI-agent development:

### 1. 4-Layer Context Management

Organizes all project knowledge into four layers so agents always operate with the right information at the right granularity:

| Layer | Name | Location | Content |
|---|---|---|---|
| 0 | Tool Config | `CLAUDE.md`, `.claude/rules/` | Agent behavior, conventions |
| 1 | Memory | `memory/` | Long-term knowledge across sessions |
| 2 | Project Context | `context/` | Architecture, ADRs, current state |
| 3 | Task Queue | `queue/` | YAML task management (backlog → done) |

### 2. PO-PM-IC Model

Three-role separation of concerns:

- **PO (Product Owner)** — decides what to build and why; approves deliverables
- **PM (Main Agent)** — decomposes tasks, delegates to IC agents, reviews quality; does not write code directly
- **IC Agents** — specialized implementers (PdM, Architect, Coder, Reviewer, etc.)

### 3. Agent Startup Protocol

A consistent checklist the PM follows before spawning any IC agent: load the persona file, inject common rules, add task-specific context, and specify the expected deliverable format.

### 4. Skill Evolution Loop

Agents propose new slash-command skills whenever they detect a repeatable work pattern. Proposals include trigger conditions, inputs, outputs, and estimated reuse frequency. Approved skills are added to `.claude/commands/`.

### 5. Two-Layer Document Pattern

External design documents (e.g., in a wiki or project management tool) follow a two-layer structure:

- Upper half: Human-readable narrative for stakeholders
- Lower half: Machine-readable structured specs (YAML/JSON code blocks) for agents

When conflicts exist, structured specs take precedence over narrative.

### 6. Model Selection Policy

Match model capability to task complexity to control cost and latency:

| Task Type | Recommended Model |
|---|---|
| Search / lookup / summarize | Haiku (fast, cheap) |
| Implementation / code generation | Sonnet (balanced) |
| Architecture decisions / trade-off analysis | Opus (highest capability) |

### 7. Session Recovery Steps

After `/clear` or a new session, agents recover context in this order:

1. `CLAUDE.md` (auto-loaded)
2. `context/project.md`
3. `queue/in_progress/`
4. Memory (prior decisions, relationships)
5. `context/architecture.md`, `context/decisions.md` as needed

### 8. Feedback-Memory Loop

User corrections and lessons learned are written to `memory/` files and referenced in future sessions. This prevents the same mistakes from recurring across sessions.

---

## Directory Structure

```
.
├── CLAUDE.md                    # Project root config (fill in placeholders)
├── .claude/
│   ├── agents/                  # IC agent persona definitions
│   │   ├── pdm.md
│   │   ├── python-coder.md
│   │   ├── sql-coder.md
│   │   ├── infra-coder.md
│   │   ├── reviewer.md
│   │   └── ...
│   ├── commands/                # Reusable slash-command skills
│   └── rules/                   # Shared agent rules (applied to all agents)
│       ├── agent-common.md
│       ├── branch-protection.md
│       ├── coding-conventions.md
│       ├── documentation.md
│       └── security.md
├── context/
│   ├── project.md               # Universal Context Template
│   ├── architecture.md          # Technical architecture & data model
│   └── decisions.md             # Decision log (ADR format)
├── memory/                      # Long-term agent memory (session-persistent)
└── queue/
    ├── README.md                # Task YAML spec & workflow definition
    ├── backlog/
    ├── in_progress/
    └── done/
```

---

## How to Use

1. **Fork or copy** this repository as the foundation for your new project.
2. **Run `/init-project`** in Claude Code — describe your project and all `{{placeholder}}` values will be filled in automatically.
3. **Review the generated files** — refine any sections that need more detail.
4. **Create agent personas** under `.claude/agents/` for any domain-specific roles your project needs (the init skill will suggest these).
5. **Start working** — describe your task to the PM agent and let it delegate.

Alternatively, you can fill in the `{{placeholder}}` values manually in `CLAUDE.md`, `.claude/rules/coding-conventions.md`, and `context/` files.

---

## Keeping Up with Upstream

When ai-dev-base is updated with new patterns or improvements, sync them into your project:

```
/sync-base
```

This reads `.base-sync.yml` (included in the template) to determine which files are base-derived, fetches the latest versions, and shows you what changed before applying. Project-specific files are never touched.

You can also sync from a local copy:

```
/sync-base ~/workspace/ai-dev-base
```

---

## License

MIT
