# 06 Commands

| # | Command (summary) | Purpose | Result |
|---|---|---|---|
| 1 | git status/branch/rev-parse/remote | run setup: git state | clean, main @ a7cf5c3 |
| 2 | git ls-files, count by dir | inventory structure | 182 files; 103 .agents |
| 3 | ls .agents/plans/pending, done | pending-plan discovery | pending empty; 15 done all EXECUTED |
| 4 | git grep TODO/FIXME/HACK/XXX in *.py | code backlog markers | 0 real markers |
| 5 | python3 -m unittest discover -s tests -t . | baseline test evidence | 46 tests, all pass |
| 6 | install-workflows.py --version; cat VERSION; grep index stamp | version consistency | all = 20260704-05 |
| 7 | ls shims; count lenses/personas/tools | surface inventory | 16 shims, 29 lenses, 7 personas, 4 tools |
| 8 | install-workflows.py --repo . --dry-run | drift check on source | NO drift (manifest == shims) |
| 9 | grep python version claims; grep runtime modern-syntax | 3.7+ compat check | annotations stringized; no runtime 3.8+ feature found |
| 10 | grep shell=True/os.system/eval/exec | injection surface | none found |
| 11 | scan_secrets.py --repo . --format json --out secrets-scan.json | mandatory secrets scan | 518 candidates, all FP (saved) |
| 12 | gitleaks detect --source . --no-banner | authoritative history scan | 0 leaks, 65 commits |
| 13 | python triage of scan.json | classify candidates | 508 entropy FP, 8 intentional emails, 91 in workflow-artifacts, 49 lockfile |
| 14 | read setup_tools.py / run_checks.py / scan_secrets.py | tool correctness/safety | clean; S2-B1/M1/M2 noted |
| 15 | run_checks.py --repo . --list | verify discovery | 0 checks discovered (S3-T2) |
| 16 | run_checks.py --add "python3 -m unittest discover -s tests -t ." --yes --out verify-results.json | capture real test evidence | ran 1, passed 1, exit 0, 8.9s |
| 17 | grep counts across README/ARCHITECTURE/getting-started | doc accuracy vs framework | found S4-D1/D2/D3 (stale from D41) |
| 18 | edit scan_secrets/setup_tools + tests | S7 batch1 | 52 tests pass; scanner 518->289 |
| 19 | make test | dogfood verify discovery | 52 tests pass |
| 20 | run_checks.py --list (after Makefile) | S3-T2 dogfood | discovers 3 checks (was 0) |
| 21 | install-workflows.py --dry-run | drift check post-edits | no framework drift |
