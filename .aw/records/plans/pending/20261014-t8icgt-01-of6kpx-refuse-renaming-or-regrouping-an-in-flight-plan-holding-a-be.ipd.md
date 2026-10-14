# IPD: Refuse renaming or regrouping an in-flight plan holding a begin receipt

- Date: 2026-10-14
- Kind: child
- Concern: `69pxm5` (D163) guarded `aw rename` and `aw group` from rewriting CITATIONS inside a citing plan that holds a live begin receipt (`.aw/state/ipd-lifecycle/<id6>.receipt.json`), but left renaming or regrouping the IN-FLIGHT PLAN ITSELF unguarded (`69pxm5` F-07, filed as backlog `t8icgt` and pinned as baseline by `tests/test_rename_receipt_guard.py::test_i_renaming_the_in_flight_plan_itself_still_succeeds`). Authoring measured the four concrete execution geometries (F-01 through F-05): (1) in the default isolated-worktree runner geometry (`aw oc run` / `aw agy run`), renaming or regrouping the in-flight plan on `main` while its lane executes lets `aw ipd finalize` inside the lane move the old filename to `executed/` and consume the shared begin receipt, after which `oc_runipd.integrate_lane_branch` fails closed with `fail-merge` (`[aw-integration-cause=git-merge-conflict] CONFLICT (file location)` / `CONFLICT (rename/rename)`), stranding the lane with its receipt already deleted (F-02); (2) a metadata-only `aw group plans <id6> --set <newset> --apply` (without `--rename`) rewrites `- Set:` while leaving the filename's `<setid>` facet unchanged, causing `finalize` or post-merge `aw index plans --check` to fail with `name-metadata-mismatch` (F-03); (3) an uncommitted self-rename in the same checkout causes `finalize` to commit `executed/<new>` without deleting `pending/<old>` from `HEAD` and restore the staged rename onto `pending/`, leaving duplicate `p22222` plans in `pending/` and `executed/` (F-04); and (4) a committed self-rename in the same checkout writes `.aw/records/history.jsonl` via `record_history.record_rename`, which `finalize` refuses as an undeclared out-of-scope path (F-05).
- Scope: IN: (a) re-measuring the unguarded self-rename and self-regroup baseline at execution HEAD (E-01); (b) adding `_in_flight_target_error` in `agent_workflows/plans_refs.py` that reuses `artifact_refs.classify_citing_plans_for_rewrite` as the single liveness predicate (F-06) and wiring it into `plans_refs.run_mv`, `plans_refs.plan_set_assign`, and `plans_refs.apply_renames` so both preview and `--apply`, single-target and batch, `--rename` and metadata-only `--no-rename` refuse fail-closed with `artifact_types.EXIT_CANNOT_RUN` (exit 2, diagnostic rule `in-flight-plan`) before touching any file (E-02); (c) replacing the baseline test `test_i_renaming_the_in_flight_plan_itself_still_succeeds` in `tests/test_rename_receipt_guard.py` with outcome tests covering `aw rename plans` (apply and preview), `aw group plans` (`--rename`, metadata-only, and multi-target batch atomicity), `--agent`/`--json` machine diagnostics, and post-receipt-removal recovery (E-03); (d) recording the refuse-over-skip decision in `DECISIONS.md` (E-04); (e) adding one sentence to Section 4.5 of `.aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md` (E-05); and (f) adding one `Fixed:` line to `CHANGELOG.md` (E-06). OUT: citation rewrites into in-flight plans when *another* artifact is renamed (already skipped and reported by `69pxm5` / D163); `plans_archive` weekly-shard archival (operates only on `TERMINAL_DIRS = ("executed", "superseded", "not-executed")`, never on in-flight pending plans); non-plan artifact types (`specs`, `research`, `walkthroughs`, `prompts`, `comms`, which do not use `ipd_lifecycle` begin receipts); and any `--force` flag to override the live-receipt refusal (see OQ-01).
- Scope-Paths: agent_workflows/plans_refs.py, tests/test_rename_receipt_guard.py, DECISIONS.md, .aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md, CHANGELOG.md
- Item-Dependencies: executed:69pxm5
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: t8icgt
- Blocks-Release: next
- Set: t8icgt
- Order: 1
- Highest E allocated: 06
- Author: Antigravity
- Id: of6kpx

## Workflow history

- 2026-10-14 to-review (Antigravity): graduated from backlog `t8icgt`. Authoring measured all four self-rename/self-regroup execution geometries against `ipd_lifecycle` and `oc_runipd.integrate_lane_branch` (F-01 through F-05), proving that self-rename/regroup strands an isolated lane in `fail-merge` with its receipt already consumed, breaks `aw index plans --check` on metadata-only `group`, and corrupts or blocks same-tree `finalize`; resolved OQ-01 in favor of fail-closed refusal (`EXIT_CANNOT_RUN`, exit 2, rule `in-flight-plan`) reusing `artifact_refs.classify_citing_plans_for_rewrite` (F-06).
- 2026-10-14 draft (Antigravity): created.

## Goal

Refuse renaming or regrouping any plan that holds a live begin receipt (`aw rename plans` and `aw group plans`, in both preview and `--apply` modes and both `--rename` and metadata-only `--no-rename` modes) with `EXIT_CANNOT_RUN` (exit 2, diagnostic rule `in-flight-plan`), reusing `artifact_refs.classify_citing_plans_for_rewrite` so liveness is defined once and an executing plan can no longer be self-renamed or regrouped into a merge-back conflict, index mismatch, or finalize failure.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure the base

- [ ] E-01 Re-drive the F-01 reproduction at execution HEAD before editing any file: in a scratch git repo under `tempfile.TemporaryDirectory()`, create a pending plan `p22222` (`20260701-demo-01-p22222-orig.ipd.md`), create a live begin receipt via `ipd_lifecycle.begin(scratch, plan_path)` (or write `ipd_lifecycle.receipt_path_for(scratch, "p22222")`), and run `aw rename plans p22222 --slug renamed --apply --no-commit` and `aw group plans p22222 --set newset --apply --no-commit` through `cli.main`, recording the return codes and whether the in-flight plan file was renamed or modified. Also confirm `artifact_refs.classify_citing_plans_for_rewrite` is importable with its `(rewritable, must_skip)` return shape and that `tests/test_rename_receipt_guard.py` still contains `test_i_renaming_the_in_flight_plan_itself_still_succeeds`. Append a dated re-measurement line to Findings; if both commands already refuse with exit 2 at execution HEAD, mark this item `blocked`.
  - Depends on: none
  - Expected outcome: a dated re-measurement line appended to Findings with the driven return codes and file-mutation results; no source file modified.
  - Execution state: pending

### Task group 2: Guard `plans_refs` target operations against live begin receipts

- [ ] E-02 Add `_in_flight_target_error(repo_root: Path, src: Path, id6: str) -> Optional[str]` in `agent_workflows/plans_refs.py` and wire it into `run_mv`, `plan_set_assign`, and `apply_renames`. `_in_flight_target_error` MUST delegate receipt detection to `_refs.classify_citing_plans_for_rewrite(repo_root, [src])` (do not call `ipd_lifecycle.receipt_path_for` directly in `plans_refs.py`) and ignore `_refs._CLASSIFY_MISSING_ID_REASON` (matching `artifact_refs.filter_in_flight_plan_edits`), returning `"cannot rename or regroup in-flight plan %s (%s): %s (wait for aw ipd finalize or remove the stale receipt first)" % (id6, rel, reason)` when `must_skip` has a receipt entry and `None` otherwise. Wire the check at three sites in `agent_workflows/plans_refs.py`: (1) in `run_mv`, immediately after `src, err = resolve_target_plan(...)` succeeds (before preview/apply branching), printing `error: <msg>` and returning `_types.MutationResult(applied=False, returncode=_types.EXIT_CANNOT_RUN, diagnostics=[_types.MutationDiagnostic(message=in_flight_err, location=str(src), rule="in-flight-plan", severity="error")])`; (2) in `plan_set_assign`, inside the target-resolution loop immediately after `src, err = resolve_target_plan(...)` succeeds, returning `(plans, _set_assign_error(in_flight_err, location=str(src), rule="in-flight-plan"))` so `run_set_assign` refuses with `_types.EXIT_CANNOT_RUN` across preview and `--apply`, `--rename` and metadata-only `rename=False`, and single or multi-target batches before mutating any file; and (3) at the top of `apply_renames`, checking each `plan.src` in `plans` before any `apply_frontmatter_edit` or `_git_mv_or_rename` runs and returning `([], _types.MutationResult(applied=False, returncode=_types.EXIT_CANNOT_RUN, diagnostics=[_types.MutationDiagnostic(message=in_flight_err, location=str(plan.src), rule="in-flight-plan", severity="error")]))` on a hit. Leave `artifact_refs.filter_in_flight_plan_edits` untouched so citation rewrites into an in-flight plan when *another* artifact is renamed continue to skip and report per D163.
  - Depends on: E-01
  - Expected outcome: `plans_refs.run_mv`, `plans_refs.plan_set_assign`/`run_set_assign`, and `plans_refs.apply_renames` refuse in-flight target plans with `EXIT_CANNOT_RUN` (exit 2) and diagnostic rule `in-flight-plan`; non-in-flight plan renames and citation-rewrite skips remain unchanged.
  - Execution state: pending

### Task group 3: Tests

- [ ] E-03 Update `tests/test_rename_receipt_guard.py` (driving `cli.main` against scratch git repos under `tempfile.TemporaryDirectory` and asserting only on exit codes, stdout, structured machine output, and file bytes per GUIDING_PRINCIPLES P16): replace `test_i_renaming_the_in_flight_plan_itself_still_succeeds` with outcome tests pinning: (i) `aw rename plans <in-flight-id6> --slug renamed --apply --no-commit` exits `2` (`EXIT_CANNOT_RUN`), prints `cannot rename or regroup in-flight plan <id6>` naming `live begin receipt present`, leaves the original plan file in place and byte-identical, and does not create the renamed path; (j) preview `aw rename plans <in-flight-id6> --slug renamed` (no `--apply`) also exits `2` with the same error and prints no `rename:` preview line; (k) `aw group plans <in-flight-id6> --set newset --rename --apply --no-commit` and metadata-only `aw group plans <in-flight-id6> --set newset --apply --no-commit` (without `--rename`) both exit `2` and leave the in-flight plan's filename and `- Set:`/`- Order:` bytes untouched; (l) multi-target batch atomicity `aw group plans <other-id6> <in-flight-id6> --set newset --rename --apply --no-commit` exits `2` and leaves BOTH `<other-id6>` and `<in-flight-id6>` unmoved and byte-identical; (m) under `--agent` and `--json`, `aw rename plans <in-flight-id6> --slug renamed --apply --no-commit` exits `2`, validates with `agent_schema.assert_valid_agent_record`, and emits `status == "fail"`, `applied is False`, and a diagnostic with `rule == "in-flight-plan"` and `severity == "error"`; and (n) once the receipt file is removed, `aw rename plans <id6> --slug renamed --apply --no-commit` and `aw group plans <id6> --set newset --rename --apply --no-commit` succeed with `rc == 0` and rename the plan file.
  - Depends on: E-02
  - Expected outcome: `tests/test_rename_receipt_guard.py` passes with behaviors (a) through (n) pinned via real CLI invocations and file-byte/exit-code assertions.
  - Execution state: pending

### Task group 4: Records and documentation sync

- [ ] E-04 Append ONE `### D<n>` entry to `DECISIONS.md`, re-deriving `<n>` as one more than the highest existing `### D` heading at execution time (`D167` was highest at authoring; do not trust that number), in the house shape (`- **Context:**`, `- **Decision:**` with rejected alternatives and trade-off, `- **Applied:**`). It records that renaming or regrouping an in-flight plan's own file or Set/Order metadata (`aw rename plans`, `aw group plans`, `plans_refs.apply_renames`) is REFUSED fail-closed with `EXIT_CANNOT_RUN` (exit 2, rule `in-flight-plan`), reusing `artifact_refs.classify_citing_plans_for_rewrite` (D159), and explains why the posture differs from D163's skip-and-report for citation rewrites (citing F-02 through F-05 and batch `--order` atomicity). Modify no existing entry.
  - Depends on: E-02
  - Expected outcome: an append-only diff in `DECISIONS.md` adding one new `### D<n>` entry.
  - Execution state: pending

- [ ] E-05 Amend Section 4.5 ("Regroup / rename verb") of `.aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md` with ONE added sentence immediately after the sentence added by `69pxm5` ("...after it finalizes (decision D163)."): state that a plan holding a live begin receipt cannot itself be renamed or regrouped by `aw rename plans` or `aw group plans`; the verb refuses with `EXIT_CANNOT_RUN` until the plan finalizes or the stale receipt is removed (decision `D<n>` from E-04). Change no other text and do not change the spec's `- Status:`.
  - Depends on: E-04
  - Expected outcome: a one-sentence additive diff in Section 4.5 of `.aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md`.
  - Execution state: pending

- [ ] E-06 Add one `Fixed:` bullet under the existing `## 2.0.0 (pending)` heading in `CHANGELOG.md` stating that `aw rename plans` and `aw group plans` now refuse to rename or regroup a plan that is mid-execution (one holding a live begin receipt), preventing isolated-lane merge conflicts and finalize failures while the plan is in flight. Do not add a new heading, do not reword neighbouring bullets, and write no em or en dashes (user-facing prose).
  - Depends on: E-03
  - Expected outcome: a single added `Fixed:` bullet in `CHANGELOG.md` with zero em/en dashes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE LIVENESS PREDICATE (`artifact_refs.classify_citing_plans_for_rewrite`). Introduced by `5h3qyy` (D159) and reused by `69pxm5` (D163) inside `artifact_refs.filter_in_flight_plan_edits`, this helper resolves a plan's `- Id:` and checks `ipd_lifecycle.receipt_path_for(repo_root, plan_id).exists()`. Because `ipd_lifecycle.begin` requires a valid `- Id:`, any plan without `- Id:` (`_CLASSIFY_MISSING_ID_REASON`) cannot hold a begin receipt; `filter_in_flight_plan_edits` therefore checks `reason != _CLASSIFY_MISSING_ID_REASON`. Reusing `classify_citing_plans_for_rewrite` in `plans_refs._in_flight_target_error` honors the backlog item's requirement to reuse the existing liveness predicate rather than defining receipt lookup a second time.
- CHECKOUT-ANCHORED RECEIPT DIRECTORY. `ipd_lifecycle.receipt_dir` resolves through `checkout_control_root` (git common-dir), so a rename or regroup invoked either in the primary checkout or inside an isolated worktree lane sees the same `.aw/state/ipd-lifecycle/<id6>.receipt.json` state.
- REFUSAL DIAGNOSTIC CONTRACT (`artifact_types.EXIT_CANNOT_RUN`). `plans_refs.run_mv` and `plans_refs.run_set_assign` return `artifact_types.MutationResult(applied=False, returncode=artifact_types.EXIT_CANNOT_RUN, diagnostics=[artifact_types.MutationDiagnostic(message=..., location=..., rule=..., severity="error")])`, which `cli.map_mutation_result_to_command_result` projects into `status="fail"`, `exit_code=2` (`EXIT_CANNOT_RUN`), and structured `diagnostics` in `--agent` and `--json` output (`tests/test_mutation_result_facts.py`).
- ALL PLAN RENAME / REGROUP ENTRYPOINTS CONVERGE IN `plans_refs`. `artifact_types.TYPE_BACKENDS["plans"]` maps `"rename"` to `plans_refs.run_mv` and `"group"` to `plans_refs.run_set_assign` (which calls `plans_refs.plan_set_assign` and, when `rename=True`, `plans_refs.apply_renames`). The legacy `aw plans-mv` / `aw plans-set-assign` aliases were removed in `awcmdsurf` Order 05 (`cli.py` `_REMOVED_VERBS`). Guarding `run_mv`, `plan_set_assign`, and `apply_renames` covers every CLI and programmatic entrypoint.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Where | Finding and evidence |
|---|---|---|---|
| F-01 | **HIGH** | `plans_refs.run_mv`, `plans_refs.plan_set_assign`, `plans_refs.apply_renames` | **SELF-RENAME AND SELF-REGROUP OF AN IN-FLIGHT PLAN SUCCEED TODAY at HEAD `640fe1825`.** `plans_refs.apply_renames` calls `_refs.filter_in_flight_plan_edits(repo_root, ref_edits)`, which filters `RefEdit` citation rewrites into citing files and never inspects `plans: List[RenamePlan]`, `run_mv`'s target `src`, or `plan_set_assign`'s target list (especially when `rename=False`, which never calls `apply_renames`). Driven on a scratch git repo with `p22222` (`20260701-demo-01-p22222-orig.ipd.md`) holding a live receipt from `ipd_lifecycle.begin` (`exit_code=0`): `aw rename plans p22222 --slug renamed --apply --no-commit` printed `rename: .aw/records/plans/pending/20260701-demo-01-p22222-orig.ipd.md -> .aw/records/plans/pending/20260701-demo-01-p22222-renamed.ipd.md`, `rc=0`, moving the file on disk; `aw group plans p22222 --set newset --apply --no-commit` printed `set-assign (no rename): .aw/records/plans/pending/20260701-demo-01-p22222-orig.ipd.md (- Set: newset, - Order: 1)`, `rc=0`. |
| F-02 | **HIGH** | `ipd_lifecycle.finalize`, `oc_runipd.integrate_lane_branch` | **MEASURED LANE STRANDING IN DEFAULT ISOLATED-WORKTREE RUNNER GEOMETRY.** Driven end-to-end in a scratch repo at HEAD `640fe1825`: (1) `ipd_lifecycle.begin(repo, p22222)` wrote `.aw/state/ipd-lifecycle/p22222.receipt.json` (`exit_code=0`); (2) `worktree_lease.allocate_worktree(repo, item_id="p22222", run_id="run-test")` branched `aw/lane/p22222` at `.aw/worktrees/p22222`; (3) on `main`, `aw rename plans p22222 --slug renamed --apply` renamed and committed `pending/20260701-demo-01-p22222-orig.ipd.md` -> `pending/20260701-demo-01-p22222-renamed.ipd.md` (`rc=0`); (4) inside the lane worktree, the worker performed `E-01`/`V-01` and ran `ipd_lifecycle.finalize(lane_path, lane_plan_path)`, which found the shared receipt via `checkout_control_root`, moved `pending/20260701-demo-01-p22222-orig.ipd.md` -> `executed/20260701-demo-01-p22222-orig.ipd.md` (`exit_code=0`), and **deleted the shared begin receipt** (`receipt_exists_after_lane_finalize=False`); (5) `oc_runipd.integrate_lane_branch(repo, lease=lease, target_branch="main", run_suite_check=False)` failed closed with `integ_ok=False`, `integ_kind='fail-merge'`, `integ_summary='[aw-integration-cause=git-merge-conflict][aw-conflict-shape=unknown] merge-back conflict in 3 file(s): .aw/records/plans/executed/20260701-demo-01-p22222-orig.ipd.md, .aw/records/plans/executed/20260701-demo-01-p22222-renamed.ipd.md, .aw/records/plans/STATUS.md'` (`CONFLICT (file location)` and `CONFLICT (rename/rename)`). The lane is stranded in `fail-merge` with its begin receipt already consumed. The identical `fail-merge` stranding occurred when `aw group plans p22222 --set newset --rename --apply` was run on `main`. |
| F-03 | **HIGH** | `plans_refs.run_set_assign` (`rename=False`), `ipd_lifecycle.finalize` | **MEASURED `name-metadata-mismatch` ON METADATA-ONLY `aw group plans` (WITHOUT `--rename`).** `aw group plans` defaults to `rename=False` unless `--rename` is passed (`cli.py` `group` parser), editing `- Set:` and `- Order:` in place without calling `apply_renames`. Driven at HEAD `640fe1825`: when `aw group plans p22222 --set newset --apply` ran on `main` while `p22222` executed in a lane, `integrate_lane_branch` auto-merged the `- Set: newset` frontmatter line into `executed/20260701-demo-01-p22222-orig.ipd.md`, after which `aw index plans --check` failed with `rc=1`: `.aw/records/plans/executed/20260701-demo-01-p22222-orig.ipd.md: name-metadata-mismatch: name set demo != metadata Set newset`. When run in the same checkout before `finalize`, `ipd_lifecycle.finalize` failed with `exit_code=1`: `finalize is COMMITTED-INCOMPLETE for p22222 ... executed/20260701-demo-01-p22222-orig.ipd.md: name-metadata-mismatch: name set demo != metadata Set newset`. Thus the guard MUST live in `plan_set_assign` (before `rename=False` branches), not only in `apply_renames`. |
| F-04 | MEDIUM | `ipd_lifecycle.finalize` (same-checkout uncommitted self-rename) | **MEASURED DUPLICATE-PLAN CORRUPTION WHEN SELF-RENAME IS UNCOMMITTED IN THE SAME CHECKOUT.** Driven at HEAD `640fe1825`: when `aw rename plans p22222 --slug renamed --apply --no-commit` ran in the same checkout (staging `R .aw/records/plans/pending/20260701-demo-01-p22222-orig.ipd.md -> .aw/records/plans/pending/20260701-demo-01-p22222-renamed.ipd.md`), `ipd_lifecycle.finalize(repo, renamed_path)` snapshotted and restored staged index entries outside `[renamed_path, dest_path, status_path]` around its commit. As a result, `finalize` committed `A .aw/records/plans/executed/20260701-demo-01-p22222-renamed.ipd.md` WITHOUT deleting `.aw/records/plans/pending/20260701-demo-01-p22222-orig.ipd.md` from `HEAD`, and restored the staged rename onto `pending/`, leaving duplicate `p22222` files in both `pending/` and `executed/`. |
| F-05 | MEDIUM | `plans_refs.apply_renames`, `record_history.record_rename`, `ipd_lifecycle.finalize` | **MEASURED OUT-OF-SCOPE `.aw/records/history.jsonl` REFUSAL WHEN SELF-RENAME IS COMMITTED IN-LANE.** `plans_refs.apply_renames` calls `record_history.record_rename`, which appends to `.aw/records/history.jsonl` and commits it (`touched_paths`). Driven at HEAD `640fe1825`: when a self-rename commit is attributed to `p22222` (via `AW-Item: p22222` or `commit-cohesion`), `ipd_lifecycle.finalize` refuses with `exit_code=1`: `finalize needs scope reconciliation answers (plan left unmoved): --scope-reason .aw/records/history.jsonl=<why-this-out-of-scope-edit-was-needed>`. |
| F-06 | MEDIUM | `artifact_refs.classify_citing_plans_for_rewrite` | **THE `5h3qyy` PREDICATE IS DIRECTLY REUSABLE FOR TARGET PLANS.** `artifact_refs.classify_citing_plans_for_rewrite(repo_root, [src])` returns `(rewritable, must_skip)` where `must_skip` maps `src` to `"live begin receipt present"` whenever `ipd_lifecycle.receipt_path_for(repo_root, plan_id).exists()` is True. Calling it from `plans_refs._in_flight_target_error(repo_root, src, id6)` (and ignoring `_CLASSIFY_MISSING_ID_REASON`, just as `artifact_refs.filter_in_flight_plan_edits` does) keeps receipt-liveness logic in one place across status setters (`5h3qyy`), citation rewrites (`69pxm5`), and target plan renames/regroups (`of6kpx`). |

## Proposed changes (ordered, validatable)

1. Re-drive the F-01 reproduction at execution HEAD and record the baseline in Findings (E-01).
2. Add `plans_refs._in_flight_target_error` delegating to `artifact_refs.classify_citing_plans_for_rewrite` and wire it into `plans_refs.run_mv`, `plans_refs.plan_set_assign`, and `plans_refs.apply_renames` to refuse in-flight target plans with `EXIT_CANNOT_RUN` (exit 2, rule `in-flight-plan`) on both preview and `--apply` (E-02).
3. Replace `test_i_renaming_the_in_flight_plan_itself_still_succeeds` in `tests/test_rename_receipt_guard.py` with comprehensive CLI outcome tests (i) through (n) covering `rename` and `group` (`--apply`, preview, `--rename`, metadata-only, multi-target batch atomicity, `--agent`/`--json` diagnostics, and post-receipt-removal success) (E-03).
4. Append the `DECISIONS.md` entry, amend Section 4.5 of `.aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md`, and add the `CHANGELOG.md` bullet (E-04, E-05, E-06).

## Deferred / out of scope (with reason)

- **A `--force` flag on `aw rename plans` / `aw group plans` to bypass the live begin-receipt check.** Not added; see OQ-01.
  - Carrier-Declined: a forced self-rename or self-regroup while a lane is executing directly triggers the measured `fail-merge` stranding (F-02) or `name-metadata-mismatch` (F-03). When a receipt is genuinely orphaned from a dead session, removing the stale receipt (or finishing `aw ipd finalize`) is the explicit recovery step.
- **`plans_archive` weekly-shard archival.** Out of scope.
  - Carrier-Declined: `plans_archive.TERMINAL_DIRS` is `("executed", "superseded", "not-executed")`; pending in-flight plans are never archived by `aw archive plans`.
- **Non-plan artifact types (`specs`, `research`, `walkthroughs`, `prompts`, `comms`).** Out of scope.
  - Carrier-Declined: only IPD plans have `ipd_lifecycle` begin receipts; citations inside in-flight plans when those other types are renamed are already guarded by `69pxm5` (D163).

## Scope check

- Over-scope: none. Every path in `- Scope-Paths:` is modified by a named E-item: `agent_workflows/plans_refs.py` (E-02), `tests/test_rename_receipt_guard.py` (E-03), `DECISIONS.md` (E-04), `.aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md` (E-05), and `CHANGELOG.md` (E-06).
- Under-scope: none known. `agent_workflows/cli.py` and `agent_workflows/artifact_types.py` require no edits because `plans_refs.run_mv` and `plans_refs.run_set_assign` already return `MutationResult(applied=False, returncode=EXIT_CANNOT_RUN, diagnostics=[...])` and `cli.map_mutation_result_to_command_result` already maps that to exit code 2 and `status="fail"` in `--agent`/`--json`. `agent_workflows/artifact_refs.py` requires no edits because `classify_citing_plans_for_rewrite` is already public and exported.

## Required tests / validation

- `python3 -m pytest tests/test_rename_receipt_guard.py tests/test_artifact_refs_rewrite.py tests/test_rename_group_machine_output.py tests/test_plans_rename_selectors.py tests/test_plans_group_order_preservation.py tests/test_plans_order_grammar.py tests/test_mutation_result_facts.py` for the new and directly adjacent surfaces.
- `python3 -m pytest` run BARE (configured `addopts` supply `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`), with the actual `N passed` summary line pasted; no added flags.
- `aw ipd lint` on this plan reporting conforming.

## Spec / documentation sync

AMENDS `.aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md` Section 4.5 (E-05), declared in `- Scope-Paths:`. WHY: Section 4.5 defines the contract of the plans regroup/rename verb (`aw group plans` / `aw rename plans`) and already records `69pxm5`'s D163 exception for citing plans holding a live begin receipt; recording that a target plan holding a live begin receipt is refused with `EXIT_CANNOT_RUN` keeps the spec's Section 4.5 contract complete and accurate. No user-facing README enumerates `aw rename plans` refusal codes; the `CHANGELOG.md` bullet (E-06) documents the user-visible fix.

## Open questions

### OQ-01: Should renaming or regrouping an in-flight plan itself refuse fail-closed (exit 2) or skip-and-report (exit 0)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence and empirical measurement: refuse fail-closed with `artifact_types.EXIT_CANNOT_RUN` (exit 2, diagnostic rule `in-flight-plan`) on both preview and `--apply`. D163 (`69pxm5`) chose skip-and-report for CITATION REWRITES because the operator's primary action is renaming another artifact (e.g., a spec or sibling plan), and skipping one citing plan lets the requested rename succeed while leaving only a stale citation string. Here, by contrast, the operator's primary target IS the in-flight plan. Allowing the rename or regroup causes the four failure modes measured in F-02 through F-05 (stranding the isolated lane in `fail-merge` with its begin receipt already consumed, breaking `aw index plans --check` with `name-metadata-mismatch` on metadata-only `group`, duplicating the plan across `pending/` and `executed/` on uncommitted same-tree rename, or failing `finalize` on `.aw/records/history.jsonl` scope reconciliation). Conversely, "skipping" the target while returning exit 0 (`status="clean"`, `applied=True` in `--agent`/`--json`) would falsely report that the requested rename succeeded when nothing was renamed, and in a multi-target `aw group plans <id1> <id2> --set <s >` batch would either silently drop a member or shift sequential `--order` numbering (`start_order + i`) across a half-regrouped Set (violating the batch atomicity invariant established in `yqv6b7`). Refusing with `EXIT_CANNOT_RUN` (exit 2) before any file is touched is honest, atomic, and reversible once the plan finalizes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted dated re-measurement line in Findings plus the actual driven output from the scratch repo for `aw rename plans p22222 --slug renamed --apply --no-commit` and `aw group plans p22222 --set newset --apply --no-commit` with a live receipt present, the pasted confirmation that `classify_citing_plans_for_rewrite` is importable from `agent_workflows.artifact_refs`, and the pasted `pytest` run of `tests/test_rename_receipt_guard.py::RenameReceiptGuardTests::test_i_renaming_the_in_flight_plan_itself_still_succeeds` before E-02.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff agent_workflows/plans_refs.py` showing `_in_flight_target_error` delegating to `_refs.classify_citing_plans_for_rewrite(repo_root, [src])` (with zero direct calls to `receipt_path_for` in `plans_refs.py`) and wired into `run_mv`, `plan_set_assign`, and `apply_renames`; plus pasted output of re-running the E-01 scratch-repo commands (induced by the E-02 code paths in `run_mv` and `plan_set_assign`) showing `rc=2`, the `error: cannot rename or regroup in-flight plan p22222` output line, and the plan file unmoved and byte-identical on disk.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted verbose test run `python3 -m pytest -o addopts="" -v tests/test_rename_receipt_guard.py` showing every test in the module (including new tests covering behaviors (i) through (n)) passing; pasted run of the adjacent test modules listed in Required tests / validation; and the pasted BARE `python3 -m pytest` summary line. Quote the test assertions confirming they check only exit codes, stdout, structured records, and file bytes (P16).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff DECISIONS.md` showing additions only, exactly one new `### D<n>` entry with Context, Decision (including rejected alternatives and trade-off), and Applied bullets citing D159, D163, and F-02..F-05; plus pasted evidence of the highest existing `### D` heading before the edit proving `<n>` was re-derived without collision.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff .aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md` showing one additive sentence in Section 4.5 citing the E-04 decision number, no removed requirements, and an unchanged `- Status: implemented` header.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `git diff CHANGELOG.md` showing exactly one added `Fixed:` bullet under `## 2.0.0 (pending)`, no other changes, and a pasted check confirming zero em or en dashes (`\u2013`, `\u2014`) in the added line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires `/plan-review` and explicit human approval before execution.

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE and paste the actual runner output; never claim a test result that was not produced. Mark an `E-*` item `performed` only after performing it, and a `V-*` item `pass` only after inspecting the evidence in a separate pass. Do not claim done until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item carries concrete pasted evidence with `Result: pass`. Ownership of the transition is conditional: in a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`, so the executor commits its work and leaves the move to the runner; executing BY HAND, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit the status or `git mv` the file. SCOPE FENCE: an edit outside `- Scope-Paths:` that proves necessary is made and then justified with `aw ipd finalize --scope-reason`, never silently.

A NOTE ON THIS PLAN'S OWN EXECUTION: E-01 and the tests build their scratch repositories under the system temp directory, never inside the checkout, and write receipts only there, so no real `.aw/state/ipd-lifecycle/` receipt is created or touched.
