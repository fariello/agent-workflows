- Id: cnwy8g
- Status: open
- Set: runnerlayer
- Priority: medium
- Work-Kind: followup
- Summary: agy_runipd imports 40 names from oc_runipd, so the two host runners are not peers: a host driver depends on the other host's driver module, which the rununify shared library must correct rather than preserve

## Workflow history
- 2026-09-03 created (aw backlog): agy_runipd imports 40 names from oc_runipd, so the two host runners are not peers: a host driver depends on the other host's driver module, which the rununify shared library must correct rather than preserve

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
