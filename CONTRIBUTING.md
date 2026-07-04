# Contributing

This repo's value is disciplined, honest documentation, so the one rule that matters
most is: keep the docs in sync with what the framework actually does.

## Adding a workflow: the guided way

The fastest path is the `/scaffold` wizard (`.agents/workflows/scaffold/scaffold.md`):
it asks what to create (an `assess-*` lens, a standalone workflow, or a command),
generates it from the existing pattern, wires the manifest, and regenerates the shims.
The manual checklist below is what `/scaffold` automates - follow it if you prefer to do
it by hand.

## Doc-sync checklist: when you add or rename a workflow

The authoritative rules for how workflows are structured live in `ARCHITECTURE.md`
(see its "Capability layout" section) and `.agents/workflows/index.md` (the manifest
format). Do not restate those here; follow them, and use this as the step list:

1. Add or rename the workflow subdirectory under `.agents/workflows/<capability>/`.
2. Update the manifest row(s) in `.agents/workflows/index.md` (keep the
   `command | body | lens | description` columns stable).
3. For an `assess-*` concern, add the lens file under
   `.agents/workflows/assess/lenses/` and reference it in the manifest `lens` column.
 4. Regenerate the per-tool slash-command shims by running the installer
    (`install-workflows.py`, at the repo root); do not hand-edit the generated shims in
    `.opencode/commands/` or `.claude/commands/`.
5. Confirm `README.md` and `ARCHITECTURE.md` still describe the current set accurately.
6. If a decision changed the design, add a dated entry to `DECISIONS.md`. Never rewrite
   existing dated entries to match a later layout; the log is history (see
   `GUIDING_PRINCIPLES.md` P4).

## Secret scanning

Committed secrets and PII/PHI must never enter this repo, including its git history.

- **CI enforces it:** `.github/workflows/secret-scan.yml` runs `gitleaks` (full history)
  on every push and pull request.
- **Scan locally before pushing:** run `gitleaks detect --source . --no-banner`, or the
  built-in `python3 .agents/workflows/assess/tools/scan_secrets.py --repo .` (a
  dependency-free safety net that also auto-uses gitleaks/detect-secrets if installed).
- **False positives:** add the finding's fingerprint (printed by gitleaks) to the
  `.gitleaksignore` baseline at the repo root. Do not suppress a real secret - rotate
  it at the provider first, then purge it from history (`git filter-repo`/BFG).
- For a deeper pass, run `/assess secrets`.

## Self-tests (run before pushing tool changes)

The framework's Python tools have automated tests (stdlib `unittest`, zero dependencies -
consistent with the tools themselves). If you change `install-workflows.py`,
`scan_secrets.py`, or `run_checks.py`, run them:

```
python3 -m unittest discover -s tests -t .
```

They cover the installer (fresh install, idempotent re-run, prune of stale/legacy shims,
legacy-layout migration, dry-run makes no changes, the catalog-row collapse and the
`assess-all` prefix exception, `--version`), the secret scanner (planted secret in the
working tree AND in git history, redaction, clean-repo zero), and the check runner
(classification, the safety denylist never running under `--yes`, honest pass/fail exit
codes, no-checks honesty). The framework's own `verify` workflow discovers and runs them.
Test only the mechanical tools, not the instruction prose (prose is reviewed by
`/assess prose`, not unit-tested).

## Authoring conventions

- Match what the software does today; do not document aspirations
  (`GUIDING_PRINCIPLES.md` P2).
- Keep each policy or rule in exactly one canonical place and link to it, rather than
  duplicating it (P8).
- Do not use em dashes in authored Markdown; use hyphens or parenthetical dashes.
