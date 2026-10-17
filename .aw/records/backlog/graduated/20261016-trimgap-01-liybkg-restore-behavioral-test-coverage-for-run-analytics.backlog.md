- Id: liybkg
- Status: graduated
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for run_analytics_export

## Workflow history
- 2026-10-17 graduated (aw backlog): graduated by run run-20261017T053805Z-509296: 438gkf
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for run_analytics_export

Carries 10 candidate production keys for agent_workflows/run_analytics_export.py (291 exclusive lines): build_manifest, _bundle_readme, _sha256_file, archive_member_refusal, select_raw_files, ... (10 keys).

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Rollup mutation totals.
Reach class and verdict: all 10 keys are unreached at baseline HEAD (reach class unreached, final verdict unguarded-unreached).
Deleted test files to mine: test_run_analytics_privacy_boundary.py, test_run_analytics_submit.py, test_run_analytics_wizard.py at 19313eed^ (see hpjj44 ## Derived properties).
Remedy: restore behavioral test coverage for run_analytics_export.
