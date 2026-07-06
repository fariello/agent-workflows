# Section 3 per-phase report - Tests and regression

## What I did
- Captured real test evidence via verify/run_checks.py into verify-results.json (not self-report):
  46 tests, ran 1 command, passed, exit 0, ~8.9s.
- Assessed coverage per tool: all four tools tested; safety-critical paths covered
  (run_checks denylist, scan_secrets redaction/history, installer prune/migration/exec-bit,
  bench_env each-diagnosis).
- Ran run_checks.py --list and found it discovers 0 checks in this repo (S3-T2).

## Why
- Section 3 requires machine-checkable evidence for any pass claim, not code reading. Coverage of
  the SAFETY-critical behavior (the denylist, redaction, idempotent install) is what matters most
  for a tool that runs in other people's repos.

## Findings
- S3-T1 (T, Low/Low): capture_hpc() has no direct parse test (only diagnose() is tested with a
  hand-built dict). Optional monkeypatch test in Section 7.
- S3-T2 (T, Low/Low): verify/run_checks.py cannot auto-discover this repo's own test command (it
  lives only in CONTRIBUTING prose). The framework does not dogfood its own verify. Fix by adding a
  minimal Makefile/pyproject test target in Section 7 (low RR, also improves dogfooding).

## Current test health
- Strong. 46 stdlib-unittest tests, zero deps (matches the tools). All pass. The recent
  additions (bench_env 16 tests, scanner recommendation states) are covered. Regression test for
  the S2-B1 scanner-scope fix is planned for Section 7.

## What I considered but did NOT do
- Did NOT add/modify tests (Section 7 owns that).
- Did NOT flag the absence of lint/build/typecheck as a gap: the project is stdlib-only prose +
  tools; there is no build. Not applicable.
- Did NOT treat "prose bodies are untested" as a gap: CONTRIBUTING explicitly scopes tests to the
  mechanical tools; prose is reviewed by /assess prose. Consistent with stated philosophy (P-align).
