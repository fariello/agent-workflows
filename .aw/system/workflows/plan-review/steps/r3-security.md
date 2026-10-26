# Check R3: Security and Privacy

Review the plan against security and privacy requirements.

## Short form (for `simple` tier)
When evaluating a plan in the `simple` tier where tier question 2 is "yes" (touches code guarding private data, commits, worktree isolation, or the sandbox), review against the first three bullets:
- Identity is verified; authorization is default-deny and resource-scoped.
- Secrets are not hardcoded; trust-boundary inputs are validated.
- Queries, commands, files, uploads, and outbound calls are safe when present.

## Full form (for `standard` and `complex` tiers)
### B. Security and privacy
- Identity is verified; authorization is default-deny and resource-scoped.
- Secrets are not hardcoded; trust-boundary inputs are validated.
- Queries, commands, files, uploads, and outbound calls are safe when present.
- Sensitive data collection, logging, exposure, retention, and errors are
  minimized.
- Privileged bypasses and abuse controls are justified when relevant.

Record notes in the review record's `### Step R3` subsection starting with `- Checked: <what was examined>`.
Record findings per `_findings.md` in the current round's single `### Findings` table.
