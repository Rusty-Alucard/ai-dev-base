# Coding Conventions

## Languages

{{list_languages_and_their_roles}}

Examples:
- Python — data processing scripts, ETL pipelines
- SQL — DDL definitions, transformation queries
- HCL — infrastructure as code (Terraform)
- TypeScript — application logic, API clients

## Formatting & Linting

{{for_each_language}}

### {{language_name}}

- Formatter: {{formatter_tool}}
- Linter: {{linter_tool}}
- Style: {{style_guide_or_conventions}}

{{end}}

Example entries:

### Python
- Formatter: `ruff format`
- Linter: `ruff check`
- Style: PEP 8; Google-style docstrings

### SQL
- Formatter: `sqlfluff format`
- Linter: `sqlfluff lint`
- Style: keywords in UPPERCASE, identifiers in snake_case, 2-space indent

### HCL (Terraform)
- Formatter: `terraform fmt`
- Linter: `tflint`
- Style: snake_case resource names; all variables must have a `description`

## Type Annotations

{{type_annotation_policy}}

Example: Type hints are required on all public functions and methods. Internal helpers should use type hints where the signature is non-obvious.

## Documentation

{{docstring_style}}

Example: Use Google-style docstrings for Python. Every public function must have a one-line summary and document all parameters and return values.

## Commit Messages

- Language: English
- Format: `<type>: <subject>`
- Types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`
- Subject line: imperative mood, no trailing period, 72 characters or fewer
- Body (optional): explain *why*, not *what*

Examples:
```
feat: add pagination to user list endpoint
fix: handle null value in invoice total calculation
refactor: extract validation logic into separate module
```

## Lint Scope

- Always lint the entire project, not just changed files
- Run linters for all applicable languages before committing
- CI must enforce linting; local pre-commit checks are recommended but not a substitute
