- Id: otc788
- Status: open
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for clean_delta

## Workflow history
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for clean_delta

Carries 9 candidate production keys for agent_workflows/clean_delta.py (160 exclusive lines): convert_legacy_adapters, uninstall_adapters, detect_adapter_drift, repair_adapters, verify_adapter_purity, ... (9 keys).

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Rollup mutation totals.
Reach class and verdict: all 9 keys are unreached at baseline HEAD (reach class unreached, final verdict unguarded-unreached).
Deleted test files to mine: test_clean_delta.py at 19313eed^ (see hpjj44 ## Derived properties).
Remedy: restore behavioral test coverage for clean_delta.
