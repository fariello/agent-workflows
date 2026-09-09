- Id: cnwy8g
- Status: graduated
- Set: runnerlayer
- Priority: medium
- Work-Kind: bug
- Summary: agy_runipd imports 40 names from oc_runipd, so the two host runners are not peers: a host driver depends on the other host's driver module, which the rununify shared library must correct rather than preserve

## Workflow history
- 2026-09-09 graduated (aw set): Clear the stray Blocks-Release: next. The item's own ## Gate section says 'No Blocks-Release gate. This is a layering correction, not a live failure', and its 2026-09-08 re-measurement states twice that consequence 1 (DriverError) is DISCHARGED by executed plan 818uru E-03 which carried the gate, so 'this item correctly carries NO Blocks-Release gate, and the graduated plans deliberately carry none either'. The front-matter field disagreed with the body, which made aw check report check.from-backlog-gate-mismatch on all three graduated runnerlayer plans (lyo1tz, 9kmbr0, 1f7xno) for faithfully carrying no gate. Fixing the field, not the plans.
- 2026-09-08 graduated (aw set): Graduated to the runnerlayer Set: orchestrator lyo1tz with children 9kmbr0 (classify all 47 against a stated criterion and FREEZE the sorted set so accretion fails a test) and 1f7xno (re-home the host-neutral names into runner_shared in reviewable batches; closes this item). Split into two because this item's own first requirement is 'Classify all 40 first ... Do not bulk-move'. See the RE-MEASUREMENT AND CORRECTIONS section appended: the count is 47 not 40 across eight statements not six, nine names arrived and two left in five days, consequence 1 (DriverError) is DISCHARGED by executed plan 818uru E-03 so no Blocks-Release gate is carried or invented, the cited wrapper at agy_runipd.py:87-93 is gone, the module is runner_shared.py not runner_common.py, and the 818uru sequencing precondition is satisfied (executed, with a fence explicitly excluding this work).
- 2026-09-03 set (aw backlog): RECLASSIFIED followup -> bug AND GATED, maintainer ruling 2026-09-03. Each of these three describes shipped behavior that does not match what the product claims, so under the all-bugs-block-release rule they are bugs, and the 'followup' label was the reason the 2026-09-03 gating audit skipped them. Work-Kind edited directly because 'aw backlog set' has no --work-kind flag (its 'aw ipd set' twin does); that tooling gap is filed separately.

FOUND 2026-09-03 by E-01 of orchestrator `5e4sb6` (research `tvnq50`), while inventorying the two host
runners for de-duplication. Filed because the finding would otherwise live ONLY in the Deferred section
of plan `818uru`, and once that plan reaches `executed/` the finding leaves the live tree.

## The measurement

`agy_runipd.py` imports **40 names FROM `agent_workflows.oc_runipd`**, across six `ImportFrom`
statements (4 names at `:69`, 21 at `:111`, 12 at `:136`, and one each at `:1403`, `:1404`, `:2395`).
`oc_runipd` imports **ZERO** names from `agy_runipd`. Verified by AST walk, not grep, so a re-export
alias is counted once and a string mention is not counted at all.

The 40: `BacklogCloseVerdict`, `CARRIER_KIND_IPD`, `CARRIER_KIND_OTHER`, `DEPENDENCY_FATAL_RULES`,
`DriverError`, `SuiteCheckResult`, `ToolIdentityError`, `_artifact_owners`, `_read_from_backlog`,
`_read_item_dependencies`, `assert_child_tool_identity`, `build_isolation_notice`,
`cascade_dependency_blocked`, `close_backlog_item`, `collect_earned_paths`, `commit_backlog_close`,
`dependency_depth`, `dependency_reasons`, `dependency_status`, `dependency_target_id6`,
`edge_satisfied`, `emit_shutdown_report`, `enforce_dependency_preflight`, `evaluate_backlog_close`,
`integration_is_earned`, `parse_dependency_token`, `pinned_child_env`, `pinned_module_argv`,
`preflight_dependency_findings`, `process_backlog_close`, `queue_sort_key`,
`record_unclosed_backlog_items`, `register_signal_report`, `render_runs_pointer`,
`render_unclosed_report`, `resolve_backlog_item`, `run_earned_paths`, `run_suite_check`,
`signal_report_callback`, `unclosed_backlog_items`.

## Why this is a defect and not just a shortcut

The two modules are the HOST DRIVERS: `oc_runipd` drives opencode, `agy_runipd` drives antigravity.
They are supposed to be siblings over a shared core. Instead one host driver depends on the other
host's driver module for 40 names, most of which are not opencode-specific at all (dependency-graph
evaluation, backlog closing, shutdown reporting, suite checking).

THE CONSEQUENCES ARE ALREADY OBSERVABLE, which is why this is filed rather than left as a style note:

1. **It has already produced a real bug class.** `DriverError` is defined in BOTH modules as two
   DISTINCT classes AND imported across, so `enforce_dependency_preflight` raises oc's class where
   agy's `main` catches agy's. The in-tree comment at `agy_runipd.py:87-93` documents a hand-written
   wrapper that exists only to translate one into the other. That wrapper is a symptom of this layering,
   not of that one symbol.
2. **It makes the import list fragile against tooling.** The same comment records that `ruff` REMOVED 6
   of these re-exports on a first commit attempt, caught only by a cross-driver symmetry test, which is
   why the `as <same-name>` form is load-bearing rather than cosmetic.
3. **It hides the de-duplication.** A pairwise "do both runners define this?" check sees an imported
   symbol as already shared, so the true shared surface is understated by up to 40 names.

## What must happen, and who owns which part

`818uru` (rununify child 02) creates `agent_workflows/runner_common.py`. That module is the correct home
for the host-neutral members of this list, and `818uru`'s scope fence explicitly EXCLUDES re-homing them,
so the work is real and currently unowned.

REQUIRED OF WHOEVER TAKES THIS:
- Classify all 40 first. Some are genuinely opencode-specific and must stay in `oc_runipd` (with agy
  importing them only if the behavior is genuinely oc's); the rest belong in the shared library. Do not
  bulk-move.
- The `oc -> agy` direction must stay at ZERO imports, so no fix may create a cycle. `runner_common` must
  import NEITHER runner, which is already `818uru` E-01's stated admission rule.
- Preserve the `as <same-name>` re-export form for anything that remains re-exported, or an autoformatter
  will delete it again (consequence 2 above).
- The cross-driver symmetry test that caught the ruff deletion must keep passing, and should be extended
  rather than replaced.

## Sequencing

Do this AFTER `818uru` executes, because that plan creates the module this work moves things into, and
because both edit the same two highest-contention files in the repo. Doing it before would mean moving
symbols twice.

## Gate

No `Blocks-Release` gate. This is a layering correction, not a live failure: the ONE behavioral defect it
has produced (`DriverError`) is owned by `818uru` E-03, which carries the release gate and must prove the
fix with pasted evidence in V-03. If a second behavioral defect is traced to this layering, gate it then.

## RE-MEASUREMENT AND CORRECTIONS, 2026-09-08 at HEAD 44d4950d during graduation

THE COUNT IS 47, NOT 40, and it grew across EIGHT `ImportFrom` statements rather than six (4 at
`agy_runipd.py:266`, 21 at `:308`, 17 at `:333`, one each at `:1399`, `:2371`, `:2380`, `:2387`,
`:2399`). `oc_runipd` still imports ZERO from agy. Measured by AST walk, the same method this item used.

THE DELTA AGAINST THIS ITEM'S 40-NAME LIST, because an executor working from the list above would search
for names that are no longer there:
- LEFT (2): `DriverError`, `build_isolation_notice`.
- ARRIVED (9): `_read_kind`, `announce_run_order`, `build_verify_and_continue_notice`,
  `classify_recovery_disposition`, `resolve_prior_lane`, `route_recovery_turn`, `run_order_rationale`,
  `simulate_dispatch_order`, `update_execution_order`.
That is roughly 1.4 names per day with a green suite throughout, which is the argument for the freeze
guard the graduated Set adds rather than only a one-time move.

CONSEQUENCE 1 IS DISCHARGED. This item's only behavioral defect (`DriverError` as two distinct classes
with a hand-written translation wrapper) is FIXED: measured `oc.DriverError is agy.DriverError is
runner_shared.DriverError` -> `True`, both drivers binding it from `runner_shared` (`oc_runipd.py:176`,
`agy_runipd.py:181`). Executed plan `818uru` E-03 did it and carried the release gate. So this item
correctly carries NO `Blocks-Release` gate, and the graduated plans deliberately carry none either.

STALE CITATION CORRECTED: this item cites the hand-written wrapper at `agy_runipd.py:87-93`. That code is
GONE; the range now holds a `render_stream` re-export comment. Navigating by those line numbers reads the
wrong code.

THE SEQUENCING PRECONDITION IS SATISFIED. This item says "Do this AFTER `818uru` executes". `818uru`
reads `- Status: executed` in `.aw/records/plans/executed/`, and its scope fence says verbatim "Do NOT
re-home the 40 oc-to-agy imports", so the work is real and unowned.

MODULE NAME CORRECTED: the shared module is `runner_shared.py`, not `runner_common.py` as written above.
`818uru` OQ-01 renamed it by maintainer ruling because `runner_common` "can be misread as a generic
dumping ground".

CONSEQUENCE 2 IS STILL LIVE AND IS THE MAIN EXECUTION HAZARD: `ruff` and `ruff-format` are both
pre-commit hooks in this repository, so the re-export deletion this item records will be attempted again.
The test that caught it is `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` (`:1179`),
whose `test_the_implementation_is_shared_not_copied` (`:1201`) asserts OBJECT IDENTITY for eleven of
these names and whose `_SHARED_NAMES` tuple (`:1182`) is where a re-homed name is registered.

ONE THING RECORDED THAT IS NOT THIS ITEM'S SUBJECT: `build_isolation_notice` left the import list because
BOTH hosts now DEFINE it (`oc_runipd.py:4717`, `agy_runipd.py:2348`), which is a re-fork rather than an
improvement. Re-forks are `2r306y`'s subject, not this item's, so it is noted rather than folded in.

GRADUATED to the `runnerlayer` Set: orchestrator `lyo1tz`, child 01 `9kmbr0` (classify all 47 against a
stated criterion and FREEZE the sorted set so accretion fails a test), child 02 `1f7xno` (re-home the
host-neutral names into `runner_shared` in reviewable batches, preserving the `as <same-name>` form and
keeping the shared module free of runner imports). Split into two children because this item's own first
requirement is "Classify all 40 first ... Do not bulk-move". `1f7xno` closes this item.
