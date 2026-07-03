# Decisions and assumptions - assess-secrets 20260703-115728

## Concern and scope

- Concern: secrets (committed secrets/keys/PII/PHI).
- Scope: whole repository, working tree AND full git history (no `$ARGUMENTS` narrowing).

## Project conventions discovered

- Guiding principles: `GUIDING_PRINCIPLES.md` present.
- Plans dir: `.agents/plans/` existed with only `done/`; created `.agents/plans/pending/`
  and wrote the IPD there (dated `assess-<concern>` naming).
- Contributor contract: `AGENTS.md`, `CONTRIBUTING.md`.
- No mature scanner installed (gitleaks/trufflehog/detect-secrets absent) -> used the
  built-in `scan_secrets.py` only, and the IPD recommends installing a mature one.

## Key decisions

- **Explicit-subject exception applied.** The framework's own scope-exclusion rule says
  not to review `.agents/workflows/`. But here the user explicitly targeted this repo
  (which *is* the framework), so the whole repo was scanned. `workflow-artifacts/` run
  records were still treated as out of scope for findings.
- **Triage: all 226 scanner candidates are false positives.** 0 high-signal rule hits,
  0 PII/PHI. The 224 high-entropy hits are npm lockfile integrity hashes
  (`.opencode/package-lock.json`), git SHAs and long identifiers in DECISIONS/plan/
  validation docs, dotted `.agents/workflows/...` paths in README, and the scanner
  matching its own regex source (the 2 `generic-secret-env` hits at `scan_secrets.py:169`).
- **Verdict: strong.** No remediation of live secrets is needed; only preventive
  hardening proposed. Nothing to rotate, nothing to purge from history.

## What was intentionally NOT proposed, and why

- **A secret-management system / vault integration:** over-scope (Complexity axis) - there
  are no secrets in this repo to manage. Stopped at gitignore + CI scan + baseline.
- **Rewriting git history:** not applicable - no confirmed secret exists in history to
  purge. (Had one been found, the plan would have led with rotate-first + purge.)
- **Suppressing/deleting the 224 FP candidates individually:** churn with no value;
  proposed a baseline/allow-list instead so future scans self-quiet.

## Assumptions (confirm)

- `gitleaks` on GitHub Actions is the assumed mature scanner + CI host (open question 1).
- `.opencode/package-lock.json` is intended to be committed; it is only noted as the main
  FP source, not a secrets issue (open question 3).

## Open questions for the user

1. Preferred mature scanner + CI host (default: gitleaks on GitHub Actions)?
2. Baseline approach: zero-code `.gitleaksignore`/detect-secrets baseline (recommended)
   vs. adding `--allowlist` to the built-in scanner?
3. Is committing `.opencode/package-lock.json` intended? (FP-noise source, not a secret.)
