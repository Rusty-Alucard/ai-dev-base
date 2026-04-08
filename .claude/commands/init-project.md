# Initialize Project

You are setting up a new project from the ai-dev-base template. Your job is to replace all `{{placeholder}}` values with project-specific content based on the user's description.

## Instructions

1. **Ask the user to describe their project** in a few sentences. Prompt:

   > Describe your project: what it does, the tech stack (languages, frameworks, cloud provider, databases), and who's working on it.

2. **Once the user responds**, fill in ALL placeholder files in one pass. The files containing `{{placeholder}}` values are:

   ### CLAUDE.md (root config)

   - `{{project_description}}` — one-paragraph project overview
   - `{{languages}}`, `{{frameworks_and_libraries}}`, `{{cloud_and_infra}}`, `{{databases_and_storage}}`, `{{iac_tool}}`
   - `{{current_phase_name}}`, `{{current_phase_description}}`
   - `{{in_scope_item_1}}`, `{{in_scope_item_2}}`, `{{out_of_scope_item_1}}`, `{{out_of_scope_item_2}}`
   - `{{lint_command}}`, `{{format_command}}`, `{{test_command}}`
   - `{{iac_init_command}}`, `{{iac_plan_command}}`, `{{iac_apply_command}}`, `{{custom_script_example}}`
   - `{{primary_language}}`, `{{formatter}}`, `{{linter}}`, `{{sql_dialect}}`
   - `{{secret_manager}}`
   - `{{external_spec_tool}}` — if not applicable, remove the "External Design Spec Integration" section entirely

   ### .claude/rules/coding-conventions.md

   - Replace the `{{placeholder}}` blocks and example entries with the actual languages and tools for this project
   - Remove the "Example entries" section — replace with real entries
   - Fill in `{{type_annotation_policy}}` and `{{docstring_style}}`

   ### context/project.md (Universal Context Template)

   - Fill in What, Why, Who, Constraints, Current State, Phase Plan
   - Leave Decisions and Notes minimal (just remove placeholder text or add a brief note)

   ### context/architecture.md

   - Fill in based on the tech stack described
   - It's OK to keep sections brief if details aren't known yet — use "TBD" rather than leaving `{{placeholder}}`

3. **Do NOT modify** these files (they are generic and should stay as-is):
   - `.claude/rules/multi-agent-workflow.md`
   - `.claude/rules/agent-common.md`
   - `.claude/rules/branch-protection.md`
   - `.claude/rules/security.md`
   - `.claude/agents/_template.md`
   - `queue/README.md`

4. **Agent personas**: Based on the tech stack, suggest which domain-specific agent personas to create (e.g., `python-coder.md`, `react-coder.md`, `infra-coder.md`). Copy `_template.md` and fill in each one.

5. **After filling in all files**, give the user a summary of what was configured and any sections they should review or refine manually.

## Guidelines

- Infer reasonable defaults from the project description — don't ask 20 follow-up questions
- If something is unclear, make a sensible assumption and note it in the summary
- Use the project's primary language for the main coding conventions
- Match the tone and style of the existing template content (professional, concise)
- All markdown must have blank lines after headings and before lists (markdownlint compliance)
