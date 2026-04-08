# Branch Protection Rules

## Prohibited Actions
- Direct commits to the `main` branch are not allowed
- Direct pushes to the `main` branch are not allowed

## Required Practices
- All work must be done on a feature branch
- Branch names must follow the format: `<type>/<description>`
  - Examples: `feat/add-auth`, `fix/null-pointer`, `refactor/rename-module`, `docs/update-readme`
- Merging into `main` must be done via pull request only

## Branch Name Types

| Type | When to use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behavior change |
| `docs` | Documentation only |
| `chore` | Maintenance, dependency updates, config changes |
| `test` | Adding or updating tests |
