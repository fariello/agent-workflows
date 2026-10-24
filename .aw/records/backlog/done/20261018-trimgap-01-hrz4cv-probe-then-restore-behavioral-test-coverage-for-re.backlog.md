- Id: hrz4cv
- Status: done
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Probe then restore behavioral test coverage for record_history

## Workflow history
- 2026-10-24 done (aw backlog): closed by aw agy run: IPD r495ec executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261023-trimgap-27-r495ec-lock-record-history-rename-ledger-mutation-coverage-into-the.ipd.md); evidence .aw/records/plans/executed/20261023-trimgap-27-r495ec-lock-record-history-rename-ledger-mutation-coverage-into-the.ipd.md
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175032Z-1384916: r495ec
- 2026-10-18 created (aw backlog): Probe then restore behavioral test coverage for record_history

Carries 3 candidate production keys for agent_workflows/record_history.py with remedy shape 'probe then restore'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- _endpoint_id6 (verdict: budget-exhausted, operator: return-none, control: tests/test_artifact_rename.py)
- append_rename (verdict: budget-exhausted, operator: raise, control: tests/test_rename_ledger.py)
- record_rename (verdict: budget-exhausted, operator: raise, control: tests/test_rename_ledger.py)

Deleted test files to mine: the queue's control files (tests/test_artifact_rename.py, tests/test_rename_ledger.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: probe then restore.
Carried from lrnh5f via plan b83dpg.
