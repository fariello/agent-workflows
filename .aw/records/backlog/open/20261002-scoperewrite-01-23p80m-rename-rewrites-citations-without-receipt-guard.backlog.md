- Id: 23p80m
- Status: open
- Blocks-Release: next
- Set: scoperewrite
- Priority: low
- Work-Kind: bug
- Summary: aw rename rewrites citing Scope-Paths entries with no in-flight begin-receipt guard, so renaming an artifact can stale an executing plan's frozen contract and strand its lane at finalize

## Workflow history
- 2026-10-02 created (aw backlog): aw rename rewrites citing Scope-Paths entries with no in-flight begin-receipt guard, so renaming an artifact can stale an executing plan's frozen contract and strand its lane at finalize

RAISED while authoring plan `5h3qyy` (Set `scoperewrite`, graduating backlog `es7wdp`) as that plan's F-06. It is filed separately rather than bundled because it changes a SECOND verb's contract and deserves its own review; plan `5h3qyy` names this item as the durable carrier of its deferred row.

THE MECHANISM, MEASURED. `artifact_refs.plan_reference_rewrites` plus `apply_reference_rewrites` rewrite every citation of a renamed artifact across `artifact_core.REFERENCE_SCAN_ROOTS`, which includes `.aw/records/plans`. A citing plan's `- Scope-Paths:` entry is therefore rewritten. But a plan mid-execution has a begin receipt that FREEZES its `Scope-Paths`, and a rewritten entry invalidates it: driven on real pending plan `qjm4bg`, simulating one frozen entry changing, `ipd_lifecycle.receipt_is_current` went `True -> False`, and `frozen_region_comparison` returned `removed=(<old entry>,)`, `added=(<new entry>,)`, `non_scope_identical=True`, `eligible=True`, `widening_is_acceptable=False`. The last value is the decisive one: rcptwiden `63425h`'s additive-widening accept requires `not removed` (see `widening_is_acceptable`), and a RENAME is a removal plus an addition, so the accept does NOT apply and `finalize_precheck` refuses as STALE.

NO GUARD EXISTS TODAY. Measured: `grep -c 'receipt\|in_flight\|in-flight'` returns 0 for each of `agent_workflows/artifact_rename.py`, `plans_refs.py`, `research_refs.py` and `plans_archive.py`. The only three modules that call `ipd_lifecycle.read_receipt` / `receipt_path_for` are `check_engine.py`, `ipd_lifecycle.py` and `runner_shared.py`. So nothing on the rename path consults a receipt before editing a plan's frozen region.

THE COST CLASS IS MEASURED, not hypothetical. This is the same stranding `rcptwiden 63425h` exists to prevent: run `run-20260917T023628Z-4108757` stranded three of twelve items (`i3d6ml`, `tx6q0h`, `sy7uwh`) on a stale frozen region, costing $95.71 and 3h10m and cascading into a `dependency-blocked` orchestrator.

THE FIX SHAPE IS ALREADY SPECIFIED ELSEWHERE, so this is small. `check_engine` already demonstrates the enumeration: walk plan files, read `- Id:`, call `read_receipt`, skip when absent ("no active execution -> nothing to reconcile"), and filter on `_receipt_is_live` ("spent authority ... not an in-flight scope"). Plan `5h3qyy` E-04 builds exactly that predicate for the status setter; this item is to REUSE it on the rename path rather than define liveness a second time, which is why it is cheapest to do AFTER `5h3qyy` lands.

WHY LOW PRIORITY DESPITE GATING THE RELEASE. The exposure needs a rename to coincide with a live begin receipt citing the renamed artifact, and receipts are short-lived (measured in this authoring worktree: `.aw/state/ipd-lifecycle/` does not exist, i.e. zero live receipts). It is a real latent defect rather than an active one. The automatic `- Blocks-Release: next` is the repository's every-live-bug-gates-the-release policy and is left in place deliberately; a maintainer who disagrees can de-gate it.
