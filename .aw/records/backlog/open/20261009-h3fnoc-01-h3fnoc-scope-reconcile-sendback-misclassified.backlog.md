- Id: h3fnoc
- Status: open
- Blocks-Release: next
- Set: h3fnoc
- Priority: high
- Work-Kind: bug
- Summary: Finalize send-back misclassifies a scope-reconciliation refusal as non-retryable because the attribution and 'Supply them with' lines fail Arm 3's every-line check

## Workflow history
- 2026-10-09 created (aw backlog): Finalize send-back misclassifies a scope-reconciliation refusal as non-retryable because the attribution and 'Supply them with' lines fail Arm 3's every-line check

MEASURED 2026-10-09, run run-20261009T030837Z-2088618, item m47znv attempt 2: finalize refused with RETRYABLE_SCOPE_RECONCILIATION_SUMMARY ('finalize needs scope reconciliation answers (plan left unmoved)') and one real finding 'IPD-FINALIZE out-of-scope path needs a --scope-reason: <backlog defect file>'. The event recorded retryable=false, retry_scheduled=false with budget 1 of 2 used, so verified work was stranded as fail-gate. Cause: runner_shared.finalize_refusal_is_retryable Arm 3 (added by psgyzw, 163874fcc) requires EVERY non-summary line to start with 'out-of-scope path needs a --scope-reason:', but ipd_lifecycle's refusal (ipd_lifecycle.py ~4990/5008) also emits '  attribution: run-record-exact ...', 'Supply them with:' and the suggested 'aw ipd finalize ... --scope-reason ...' command line. Reproduced on current main: finalize_refusal_is_retryable(<the recorded detail>) is False, while the same summary with only the IPD-FINALIZE finding line is True. Its unit tests evidently use the minimal message shape, not the real one. The out-of-scope path was the agent's own filed defect backlog item, i.e. exactly the answerable case Arm 3 exists for. Fix: have Arm 3 judge only IPD- finding lines (as Arm 1 does), and pin it with a test that feeds the real ipd_lifecycle refusal text. Recovery for m47znv: lane aw/lane/m47znv_attempt2 holds verified work; finalize with --scope-reason for the backlog file or resume the run.
