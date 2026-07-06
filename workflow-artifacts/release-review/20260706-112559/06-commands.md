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
