- Id: tm5vnx
- Status: graduated
- Graduated-To: specrpt
- Blocks-Release: next
- Set: specviskey
- Priority: high
- Work-Kind: bug
- Summary: runner_shared.execute_item_core writes spec_edits_reconciliation but the only reader looks for spec_edits, so the end-of-run spec report reports every item as not-finalized

## Workflow history
- 2026-09-25 graduated (aw set): graduated into specrpt plan 9npssm (to-review)
- 2026-09-23 created (aw backlog): Found while executing runnerlayer 02 (1f7xno). runner_shared.record_item_spec_edits (:22801) stores its record under item['spec_edits_reconciliation'] and is the copy execute_item_core actually calls (no driver_module rebinding, measured by AST). oc_runipd.spec_edit_summary (:1323) reads item.get('spec_edits'), the key oc_runipd.record_item_spec_edits (:1292) writes. Since both hosts route finalize through execute_item_core, NO run writes the key the reader reads, so report_run_spec_edits reports every item as not_finalized. The record SHAPE also differs (shared writes reconciled/reasons/acks/refused; the reader expects state/declared/modified_not_declared/declared_not_modified), so even a key rename would not fix it. Grep: only three sites in the package mention either key.
