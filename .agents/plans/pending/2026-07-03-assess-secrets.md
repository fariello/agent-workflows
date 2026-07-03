# IPD: Assess secrets - committed secrets and sensitive data in ai-coding

- Date: 2026-07-03
- Concern: secrets (committed secrets/keys/PII/PHI, working tree + git history)
- Scope: whole repository (working tree + full git history)
- Status: PENDING (awaiting human approval; not executed)
- Author: assess-secrets workflow (agent)

## Goal

Determine whether any secrets, credentials, keys, or sensitive personal data (PII/PHI)
are committed to this repository - in the working tree or anywhere in git history - and
propose remediation and prevention. This repo is the authoring home of the
agent-workflows framework (instruction Markdown, a Python installer, a Python secrets
scanner, and docs); it has no application, database, API, or deployment credentials, so
the a-priori likelihood of live secrets is low, but history was scanned to be sure.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (present).
- Pending-plans location/format used: `.agents/plans/` exists with a `done/` subdir but
  no `pending/`; created `.agents/plans/pending/` and used it (dated `assess-<concern>`
  naming, per the harness).
- Contributor/spec-sync contract: `AGENTS.md` (workflow pointer), `CONTRIBUTING.md`.
- Stack / context: Markdown instruction sets + two Python tools (installer, scanner) +
  docs. No secrets-bearing runtime.
- Mature scanners installed: none (gitleaks, trufflehog, detect-secrets all absent), so
  this run used only the built-in dependency-free scanner
  (`.agents/workflows/assess/tools/scan_secrets.py`) over the working tree and full git
  history.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate for whether to
act now. No raw secret values appear here (none were found; the scanner also redacts).

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| S1 | Low | Low (usability) | security-arch / stakeholder | detection | No committed secrets or PII/PHI found. The scanner produced 226 candidates, ALL `low` severity: 224 `high-entropy-string` and 2 `generic-secret-env`; zero high-signal rule hits (no private keys, cloud/API/SaaS keys, tokens, passwords, connection strings, sensitive filenames) and zero PII/PHI. Triaged as false positives (see below). | `workflow-artifacts/assess-secrets/20260703-115728/scan.json`; top sources are `.opencode/package-lock.json` (npm integrity hashes; NOTE: this file is untracked/not committed - working-tree hits only), DECISIONS/plan docs and `release-review-validation-report.md` (git SHAs, long identifiers), `README.md` (dotted `.agents/workflows/...` paths), and `scan_secrets.py` matching its own regex source. |
| S2 | Low | Low (complexity/usability) | software-engineer | prevention | No **automated** secret scanning runs in CI or pre-commit, so a future accidental commit of a real secret would not be caught automatically. (Since the assessment, `gitleaks` and `detect-secrets` have been installed locally, so ad-hoc local scanning is now possible; the remaining gap is enforcement, not tool availability.) | No CI workflow performs secret scanning (no `.github/workflows`, verified); `gitleaks` now at `/usr/bin/gitleaks` (system), `detect-secrets` in the working venv. |
| S3 | Low | Low (usability) | software-engineer | prevention | `.gitignore` already ignores `.env` and `.env.*` (under "# Environment / secrets") but does NOT pre-empt other common secret-bearing patterns: `*.pem`, `*.key`, `*.p12`/`*.pfx`, `*.jks`/`*.keystore`, `.netrc`, `.npmrc`, `.pypirc`, `service-account*.json`, `credentials*.json`. Low risk today (none present), cheap insurance. | `.gitignore` lines 18-20 (`.env`, `.env.*` present); no other credential-file patterns. Verified by reading `.gitignore`. |
| S4 | Low | Low (usability) | software-engineer | detection-quality | The built-in scanner's high-entropy rule is noisy on this repo (224 FPs from doc paths, lockfile hashes, SHAs). Without a false-positive baseline/allow-list, future scans stay noisy and real hits could be missed in the noise. | 224 `high-entropy-string` candidates, all FPs; scanner supports pattern-based rules but has no repo-local allow-list yet. |

## Proposed changes (ordered, validatable)

All items are prevention/detection hardening; there is no live-secret remediation to do
(no confirmed secrets found). Every item is low Remediation Risk, so proposed by default.

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | S3 | Extend the existing "# Environment / secrets" section of `.gitignore` with the patterns NOT already present (`.env`/`.env.*` are already there - do not duplicate): `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `.netrc`, `.npmrc`, `.pypirc`, `service-account*.json`, `credentials*.json`. | `.gitignore` | Low (usability) | `git check-ignore -v server.pem id_rsa.key` returns matches; confirm no currently-tracked file is newly ignored. |
| 2 | S2 | Add a minimal CI job that runs `gitleaks detect` on push/PR (gitleaks is a standalone binary that installs cleanly in a runner). Optionally add a pre-commit hook - use `gitleaks protect` for the hook too (portable binary), NOT the venv-scoped `detect-secrets`, so it works for any contributor/environment. Document local scanning in `CONTRIBUTING.md`. | new `.github/workflows/secret-scan.yml`, optional `.pre-commit-config.yaml`, `CONTRIBUTING.md` note | Low (complexity) | CI runs green on a clean tree; fails on a planted test secret in a scratch branch (then delete the branch). |
| 3 | S4 | Add a false-positive baseline so scans stay actionable: either a `detect-secrets` baseline / `.gitleaksignore`, or extend `scan_secrets.py` with an optional `--allowlist` file and ship a repo `.secretsallow` covering lockfile-hash / doc-path patterns. | `.gitleaksignore` or scanner `--allowlist` support + `.secretsallow` | Low-Medium (complexity) | Re-run the scanner with the baseline; candidate count drops to near-zero with no true positive suppressed. |
| 4 | S1 | Record the clean result and this baseline in the run record so future runs can diff against it. | run record (already written) | Low | N/A (documentation). |

## Deferred / out of scope (with reason)

- None deferred. No finding met the Medium-High Remediation-Risk bar. (Item 3's baseline
  work is the only one approaching Medium complexity; if extending `scan_secrets.py`
  proves non-trivial, prefer the zero-code `.gitleaksignore`/detect-secrets-baseline
  route instead - down-scope, do not defer the intent.)

## Scope check

- Over-scope: none. (Do NOT build an elaborate secret-management system - there are no
  secrets to manage here; the Complexity axis says stop at gitignore + CI scan + baseline.)
- Under-scope: the absence of automated secret scanning (S2) is the one genuine gap;
  Step 2 fills it.

## Required tests / validation

- After Step 1: `git check-ignore -v server.pem id_rsa.key` returns matches (`.env` is
  already ignored); `git status` shows no newly-ignored tracked files.
- After Step 2: the CI job passes on `main`; planting a fake `AKIA...`-style string on a
  throwaway branch makes it fail (then delete the branch).
- After Step 3: `scan_secrets.py` (or `gitleaks`) reports ~0 candidates with the baseline,
  and still flags a planted test secret.

## Spec / documentation sync

Behavior changes are additive (gitignore, CI). Add a short "Secret scanning" note to
`CONTRIBUTING.md` (how to run the scanner locally, that CI enforces it). No user-facing
product spec exists to sync.

## Open questions

1. Preferred mature scanner and CI host: `gitleaks` on GitHub Actions is the default
   (gitleaks is now installed system-wide, so it is the natural CI choice - it is a
   standalone binary that installs cleanly in a runner). `detect-secrets` is installed
   only in the working venv, so treat it as a LOCAL/pre-commit helper, NOT a CI
   dependency. Confirm, or name an alternative.
2. Baseline approach (S4/Step 3): zero-code `.gitleaksignore`/detect-secrets baseline
   (recommended) vs. adding `--allowlist` to the built-in scanner. Which do you want?
3. `.opencode/package-lock.json` is the dominant FP source (npm integrity hashes) but
   is NOT tracked by git (verified via `git ls-files`), so it is a working-tree-only
   artifact, not a committed-file concern. No action needed; the FP baseline (Step 3)
   should still cover npm-lockfile-hash patterns for local scans. (Corrected during
   plan-review; the original phrasing wrongly implied it was committed.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. There are no confirmed secrets requiring urgent rotation;
all proposed work is preventive. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute Steps 1-4, run the validation, and add the CONTRIBUTING note.
3. Then move this IPD from `.agents/plans/pending/` to `.agents/plans/done/` per the
   project's lifecycle convention.
