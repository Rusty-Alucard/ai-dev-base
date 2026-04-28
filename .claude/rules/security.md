# Security Rules

## Files That Must Never Be Committed

The following file types must never be added to version control under any circumstances:

- `.env` — environment variables, API keys, secrets
- `*-key.json` — service account or private key files
- `credentials.json` — OAuth or service credentials
- `*.pem`, `*.key` — TLS/SSL certificates and private keys
- Any file containing tokens, passwords, or other secrets

If any of these are accidentally staged, remove them immediately and rotate the exposed credentials.

## API Key and Secret Management

**Development:** Store secrets in a local `.env` file. Ensure `.env` is listed in `.gitignore` before creating the file.

**Production:** Use a dedicated secret management service (e.g. a cloud provider's secret manager, HashiCorp Vault, or equivalent). Do not embed secrets in application code or configuration files that are committed to the repository.

## Data Files

- Directories containing sensitive or production data must be listed in `.gitignore`
- Never commit personally identifiable information (PII) or confidential business data
- Only sample data or dummy data may be committed; it must not resemble real records
- If sample data is needed, generate it synthetically rather than anonymizing real records

## Access Control

- Apply the principle of least privilege: grant only the permissions required for the task
- Use separate credentials or service accounts for different purposes (e.g. read-only reporting vs. write access)
- Revoke credentials that are no longer in use
- Avoid sharing credentials across services or team members; use per-identity credentials where possible

## Claude Code Permissions Model

Subagent autonomous execution is enabled via `.claude/settings.json`. The
permissions layer enforces what subagents can write or read; combined with
mandatory Reviewer gating, this enables Harness Engineering operation
(subagents act autonomously, the Reviewer ensures quality).

### File Hierarchy

| File | Scope | Git | Purpose |
|---|---|---|---|
| `.claude/settings.json` | Team-shared | Committed | Write/Edit allow paths + secret-file deny patterns |
| `.claude/settings.local.json` | Per-developer | Gitignored (global gitignore) | Individual machine commands (e.g. local SDK paths) |

### Files Protected by the `deny` List

`.claude/settings.json` should deny `Read`, `Edit`, and `Write` for all of:

- `.env`, `.env.*`
- `**/*-key.json`
- `**/credentials.json`
- `**/*.pem`, `**/*.key`

This forms a **double defense** with the "Files That Must Never Be Committed"
list above: `.gitignore` prevents commits, while the `deny` list prevents
Claude Code itself from reading or modifying these files.

### Maintenance Rules

- Adding a new write-target directory to `allow` requires team consensus and
  is committed via `.claude/settings.json`
- Discovering a sensitive file pattern? Add it to `deny` immediately
- Do not put `Write` or `Edit` entries in `.claude/settings.local.json`;
  anything that should apply across the team belongs in `settings.json`
