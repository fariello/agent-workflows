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
| S1 | Low | Low (usability) | security-arch / stakeholder | detection | No committed secrets or PII/PHI found. The scanner produced 226 candidates, ALL `low` severity: 224 `high-entropy-string` and 2 `generic-secret-env`; zero high-signal rule hits (no private keys, cloud/API/SaaS keys, tokens, passwords, connection strings, sensitive filenames) and zero PII/PHI. Triaged as false positives (see below). | `workflow-artifacts/assess-secrets/20260703-115728/scan.json`; top sources are `.opencode/package-lock.json` (npm integrity hashes), DECISIONS/plan docs and `release-review-validation-report.md` (git SHAs, long identifiers), `README.md` (dotted `.agents/workflows/...` paths), and `scan_secrets.py` matching its own regex source. |
| S2 | Low | Low (complexity/usability) | software-engineer | prevention | No secret-scanning runs in CI or pre-commit, and no mature scanner is installed, so a future accidental commit of a real secret would not be caught automatically. | No CI workflow performs secret scanning; `gitleaks`/`trufflehog`/`detect-secrets` not on PATH. |
| S3 | Low | Low (usability) | software-engineer | prevention | `.gitignore` does not pre-empt common secret-bearing file patterns (`.env*`, `*.pem`, `*.p12`/`*.pfx`, `*.key`, keystores, `service-account*.json`, `.netrc`). Low risk today (none present), but cheap insurance. | `.gitignore` (current entries cover pyc/backups/OS files, not credential files). |
| S4 | Low | Low (usability) | software-engineer | detection-quality | The built-in scanner's high-entropy rule is noisy on this repo (224 FPs from doc paths, lockfile hashes, SHAs). Without a false-positive baseline/allow-list, future scans stay noisy and real hits could be missed in the noise. | 224 `high-entropy-string` candidates, all FPs; scanner supports pattern-based rules but has no repo-local allow-list yet. |

## Proposed changes (ordered, validatable)

All items are prevention/detection hardening; there is no live-secret remediation to do
(no confirmed secrets found). Every item is low Remediation Risk, so proposed by default.

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | S3 | Add common secret-bearing patterns to `.gitignore` (`.env`, `.env.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `.netrc`, `.npmrc`, `.pypirc`, `service-account*.json`, `credentials*.json`). | `.gitignore` | Low (usability) | `git check-ignore` on sample names; confirm no currently-tracked file is newly ignored. |
| 2 | S2 | Recommend + document installing a mature scanner (`gitleaks`) and add a minimal CI job (and optional pre-commit hook) that runs `gitleaks detect` (or `scan_secrets.py`) on push/PR. | new `.github/workflows/secret-scan.yml` (or equivalent), `CONTRIBUTING.md` note | Low (complexity) | CI runs green on a clean tree; fails on a planted test secret in a scratch branch. |
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

- After Step 1: `git check-ignore -v .env id_rsa server.pem` returns matches; `git status`
  shows no newly-ignored tracked files.
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
   assumption - confirm, or name an alternative.
2. Baseline approach (S4/Step 3): zero-code `.gitleaksignore`/detect-secrets baseline
   (recommended) vs. adding `--allowlist` to the built-in scanner. Which do you want?
3. Is `.opencode/package-lock.json` intended to be committed? It is the dominant FP
   source (npm integrity hashes) and is unrelated to the framework; not a secrets issue,
   just noted.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. There are no confirmed secrets requiring urgent rotation;
all proposed work is preventive. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute Steps 1-4, run the validation, and add the CONTRIBUTING note.
3. Then move this IPD from `.agents/plans/pending/` to `.agents/plans/done/` per the
   project's lifecycle convention.
