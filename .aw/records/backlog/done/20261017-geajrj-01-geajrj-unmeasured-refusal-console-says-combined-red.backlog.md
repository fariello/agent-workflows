- Id: geajrj
- Status: done
- Graduated-To: geajrj
- Blocks-Release: next
- Set: geajrj
- Priority: low
- Work-Kind: bug
- Summary: Execute-path console line labels an unmeasured integration refusal as combined-red

## Workflow history
- 2026-10-18 done (aw backlog): closed by aw oc run: IPD h8peam executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261017-geajrj-01-h8peam-print-reclassified-refusal-reason-on-unmeasured-integration.ipd.md); evidence .aw/records/plans/executed/20261017-geajrj-01-h8peam-print-reclassified-refusal-reason-on-unmeasured-integration.ipd.md
- 2026-10-17 graduated (aw backlog): graduated by run run-20261017T231229Z-2639110: h8peam
- 2026-10-17 created (aw backlog): Execute-path console line labels an unmeasured integration refusal as combined-red

## Detail

Found while reviewing plan `xc1xh9` (2026-10-17, HEAD `4af5e66b1`). When the post-merge revalidation is
UNMEASURED (`measured: False`, for example the suite raised), `runner_shared.record_integration_refusal`
correctly reclassifies the refusal to `merge-unchecked` and the item's `integration_deferral` and
`integration_ladder` say "could not MEASURE". But the operator's console line in
`runner_shared.execute_item_core` ("finalized on lane ... but NOT integrated to main ({fail_status}):
{integ_reason}") prints the ORIGINAL `integ_reason` from the gate, which still reads
"integration gate did not pass (integration_failed_combined_red): ... Full test suite / revalidation
failed after merging isolated lanes (per-lane-green + combined-red)".

Observed with a prototype driving `oc_runipd.execute_item` and `agy_runipd.execute_item` on a git
fixture whose revalidation `suite_check` raised: the item ended `merge-retry`, ladder kind
`merge-unchecked`, yet stderr printed the combined-red line above. Once plan `sa629y` lands, a
budget-only red follows the same path, so the operator still sees "combined-red" for the exact
`vtcqpf`/`o58dro` symptom even though the recorded state is correct. User-perceptible: this is the
line an operator reads to decide what to do.

Remedy sketch: print the reclassified reason (the value `record_integration_refusal` wrote to
`item["integration_deferral"]`) instead of the raw gate reason, on both the first-attempt path and
the deferred re-attempt path.
