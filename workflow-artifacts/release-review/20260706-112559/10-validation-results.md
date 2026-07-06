# 10 Validation results

## Evidence (machine-checkable, via verify/run_checks.py)

- Evidence file: `workflow-artifacts/verify/20260706-113000/verify-results.json`
- Command: `python3 -m unittest discover -s tests -t .`
- Result: discovered 1, ran 1, **passed 1, failed 0, timed_out 0**, exit code 0, ~8.9s.
  `all_ran_passed = true`. This is captured evidence, not self-report.

## Self-test detail (46 tests)
- test_installer.py: 13 (fresh install, idempotent re-run, prune, legacy migration, dry-run,
  catalog-row collapse, exec-bit staging, gitignored .opencode does not abort).
- test_scan_secrets.py: 9 (redaction, AWS-key in tree + history, clean-repo zero, recommendation
  states: no-nag-when-present / nag-when-absent / skipped, --version).
- test_run_checks.py: 8 (classify, denylist blocks, denylist never runs under --yes, pass/fail
  exit codes, no-checks honesty, metrics scrape, --version).
- test_bench_env.py: 16 (each diagnosis fires + clean-env-quiet, scrub, disk probe bounded+cleanup,
  warm, json context fields, bad-path usage error, --version).

## Static / safety checks (Section 2)
- gitleaks detect --source . : 0 leaks, 65 commits scanned.
- No shell=True / os.system / eval / exec in any tool or the installer.

## Not run / not applicable
- No lint/build/typecheck configured in the repo (stdlib-only, no packaging build step).
  run_checks.py --list discovers 0 checks (S3-T2): the test command is documented in CONTRIBUTING
  prose only. Recorded as a finding, not a validation failure.
