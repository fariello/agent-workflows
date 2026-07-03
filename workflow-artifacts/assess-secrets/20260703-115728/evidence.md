# Evidence - assess-secrets 20260703-115728

## Commands run (all read-only)

- `date +%Y%m%d-%H%M%S` -> run ID 20260703-115728.
- `git status --short` -> clean working tree before the run.
- Discovery: `ls` of `.agents/plans`, `.agents/plans/pending` (absent -> created),
  `AGENTS.md`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES.md`; `command -v gitleaks
  trufflehog detect-secrets` -> all missing.
- Scanner (read-only, redacted), working tree + full git history:
  `python3 .agents/workflows/assess/tools/scan_secrets.py --repo . --format json
   --out workflow-artifacts/assess-secrets/20260703-115728/scan.json`
  (stderr captured to `scanner-stderr.txt`).
- Triage via `python3 -c` aggregation over `scan.json` (rule counts, category counts,
  high-signal filter, PII filter, top files).
- Spot-check: `sed -n '35p' README.md` confirmed a high-entropy hit was the doc path
  `.agents/workflows/release-review/fix-decision-policy.md`.

## Scanner result

- Total candidates: 226 (working-tree 123, history 103). All severity `low`, all
  category `secret`. Rules: `high-entropy-string` 224, `generic-secret-env` 2.
- High-signal rules (private keys, cloud/API/SaaS keys, tokens, passwords, connection
  strings, sensitive filenames): 0 hits. PII/PHI: 0 hits.
- Full redacted output: `scan.json` in this directory. No raw secret values anywhere
  (none found; the scanner also redacts by design).

## Top false-positive sources (candidate counts)

- `.opencode/package-lock.json` (49) - npm integrity hashes.
- `.agents/plans/done/*.md` and their historical blobs - git SHAs / long identifiers.
- `release-review-validation-report.md` (historical) - identifiers.
- `README.md` (4) - dotted `.agents/workflows/...` paths.
- `.agents/workflows/assess/tools/scan_secrets.py:169` (2) - the scanner's own regex.

## Coverage / limits

- Full git history scanned (no `--max-commits`/`--since` bound; repo is small enough).
- Binary/asset extensions skipped by the scanner; files over 2 MB skipped (default cap).
- Only the built-in scanner ran; no mature scanner (gitleaks/trufflehog/detect-secrets)
  was available to cross-check. The IPD recommends installing one.

## Execution follow-up (2026-07-03, plan executed)

- Independent cross-check with the mature scanner: `gitleaks detect --source . --no-banner`
  scanned all 31 commits and reported **no leaks found** - corroborating the built-in
  scanner's "no committed secrets" conclusion with an authoritative tool.
- Baseline: `.gitleaksignore` is intentionally EMPTY (gitleaks reports zero findings);
  it documents the fingerprint format for future false positives.
- Prevention added (IPD Steps 1-3): `.gitignore` extended with credential-file patterns
  (`*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `.netrc`, `.npmrc`,
  `.pypirc`, `service-account*.json`, `credentials*.json`; `.env`/`.env.*` already
  present); `.github/workflows/secret-scan.yml` runs gitleaks on push/PR (full history);
  `CONTRIBUTING.md` documents local scanning + baseline handling.
- Clean-state baseline for future diffs: gitleaks = 0 findings across history as of
  this date.
