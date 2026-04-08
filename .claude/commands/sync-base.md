# Sync Base Template

You are syncing this project's base-derived files from the upstream ai-dev-base template.

## Instructions

1. **Read the sync manifest** at `.base-sync.yml` to determine:
   - The upstream repo URL and branch
   - The list of base-derived files to sync

2. **Fetch the latest base files** by cloning the upstream repo to a temporary directory:

   ```bash
   TMPDIR=$(mktemp -d)
   git clone --depth 1 https://github.com/<repo>.git "$TMPDIR"
   ```

3. **For each file in the manifest**, compare the local version with the upstream version:
   - If identical: report "up to date"
   - If different: show a brief summary of what changed (not the full diff)
   - If missing locally: note it will be added

4. **Ask the user for confirmation** before applying changes. Show:

   > The following base files will be updated:
   > - `.claude/rules/multi-agent-workflow.md` — 3 sections changed
   > - `.claude/rules/security.md` — up to date (no changes)
   > - ...
   >
   > Apply these updates? (Project-specific files will not be touched.)

5. **On confirmation**, copy each changed file from the temp directory to this project, overwriting the local version.

6. **Clean up** the temporary directory.

7. **Report** what was updated and suggest the user run `git diff` to review before committing.

## Important

- ONLY sync files listed in `.base-sync.yml` — never touch project-specific files
- If `.base-sync.yml` does not exist, tell the user to create one (provide the template from the ai-dev-base README)
- If the upstream repo is not accessible, suggest the user provide a local path: `/sync-base ~/workspace/ai-dev-base`
- If the user provides a local path as an argument, use that instead of cloning
