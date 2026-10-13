- Id: 046nys
- Status: done
- Graduated-To: 046nys
- Set: 046nys
- Priority: medium
- Work-Kind: chore
- Summary: Record retirement of test_no_new_module_level_first_party_import_in_runner_shared in runner_shared and ipd_lint comments

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD dtelfb executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261011-046nys-01-dtelfb-record-retirement-of-the-runner-shared-module-level-import-p.ipd.md); evidence .aw/records/plans/executed/20261011-046nys-01-dtelfb-record-retirement-of-the-runner-shared-module-level-import-p.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005617Z-2321742: dtelfb
- 2026-10-01 created (aw backlog): Record retirement of test_no_new_module_level_first_party_import_in_runner_shared in runner_shared and ipd_lint comments

Commit 80db6750c retired test_no_new_module_level_first_party_import_in_runner_shared as a code pin (P16 violation) from tests/test_orchestrator_probe_cache.py, and commit 19313eed deleted that test file. However, runner_shared.py (7 sites) and ipd_lint.py (1 site) still cite the test as an active guard. The comments should be updated to state that the pin was retired and will not return.
