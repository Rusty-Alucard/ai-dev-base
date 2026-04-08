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
