# IPD: Pass decision.reason and inventory detail when _close_already_complete_backlog_item preserves a lane

- Date: 2026-10-14
- Kind: child
- Concern: Backlog item `txw63z` (`Work-Kind: bug`, `Priority: medium`, `Blocks-Release: next`) was filed during execution of IPD `a63epo` (`9d0ba2810` / `124b917238`, `2026-10-13`) when `runner_shared._close_already_complete_backlog_item` (`def _close_already_complete_backlog_item(` in `agent_workflows/runner_shared.py`, line 36833; introduced by `0owirm` in `c59ad329a`) entered its `if not decision.torn_down:` branch after `lane_containment.teardown_lane_if_classified` refused teardown of an isolated lane and evaluated `reason=f"teardown refused: {decision.why}"`, raising `AttributeError: 'LaneTeardownDecision' object has no attribute 'why'` because `lane_containment.LaneTeardownDecision` (`class LaneTeardownDecision(NamedTuple):` in `agent_workflows/lane_containment.py`, line 3771) defines `.reason`, `.reason_codes`, and `.inventory`, not `.why`. Commit `124b917238` (`a63epo`) applied an out-of-scope (`Scope-Exceeded`) edit replacing `decision.why` with `decision.reason` in `runner_shared._close_already_complete_backlog_item` without linking `txw63z` (`a63epo` carried `- From-Backlog: r73v9i`), without documenting the `LaneTeardownDecision` contract or passing `detail=decision.inventory.as_dict()` to `lane_containment.record_lane_preserved` (which all five other `teardown_lane_if_classified` -> `record_lane_preserved` call sites in `agent_workflows/runner_shared.py` pass per spec `7ckptx` R5.6), and without adding any unit or integration test exercising the `if not decision.torn_down:` branch of `_close_already_complete_backlog_item`.
- Scope: Update `runner_shared._close_already_complete_backlog_item` (`def _close_already_complete_backlog_item(` in `agent_workflows/runner_shared.py`, lines 37083-37096) to pass `detail=decision.inventory.as_dict()` alongside `reason=f"teardown refused: {decision.reason}"` and `reason_codes=decision.reason_codes` to `lane_containment.record_lane_preserved` and document the `LaneTeardownDecision` (`txw63z` / spec `7ckptx` R5.6) contract; add direct unit coverage in `TestBacklogAlreadyCompleteUnitE02` (`tests/test_backlog_already_complete.py`, line 69) and end-to-end isolated runner coverage across both hosts (`oc` and `agy`) in `TestBacklogAlreadyCompleteIntegrationE05` (`tests/test_backlog_already_complete.py`, line 149) exercising the `if not decision.torn_down:` branch of `_close_already_complete_backlog_item`; and verify failure sensitivity and full-suite conformance so `txw63z` closes with a verified release-gate carrier.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_backlog_already_complete.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: txw63z
- From-Spec: 7ckptx
- Blocks-Release: next
- Set: txw63z
- Order: 1
- Highest E allocated: 03
- Author: Antigravity
- Id: uwaasz

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: uwaasz verified (set txw63z, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed
- 2026-10-14 to-review (aw set): Authored review-ready child IPD uwaasz from backlog txw63z

- 2026-10-14 draft (Antigravity): created.

## Goal

Ensure `runner_shared._close_already_complete_backlog_item` records `decision.reason`, `decision.reason_codes`, and `detail=decision.inventory.as_dict()` via `lane_containment.record_lane_preserved` whenever `lane_containment.teardown_lane_if_classified` refuses teardown (`not decision.torn_down`), and pin that branch across unit and both-host (`oc` and `agy`) isolated runner tests so `txw63z` closes with an executed release-gate carrier.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Align _close_already_complete_backlog_item lane-preservation recording and pin teardown-refusal coverage

- [x] E-01 Update `runner_shared._close_already_complete_backlog_item` (`def _close_already_complete_backlog_item(` in `agent_workflows/runner_shared.py`, lines 37083-37096) in its `if not decision.torn_down:` branch to pass `detail=decision.inventory.as_dict()` alongside `reason=f"teardown refused: {decision.reason}"` and `reason_codes=decision.reason_codes` to `lane_containment.record_lane_preserved` (`def record_lane_preserved(` in `agent_workflows/lane_containment.py`, line 4059), and add an explanatory comment citing backlog `txw63z`, `lane_containment.LaneTeardownDecision` (`class LaneTeardownDecision(NamedTuple):` in `agent_workflows/lane_containment.py`, line 3771), and spec `7ckptx` R5.6 (matching the five sibling `teardown_lane_if_classified` -> `record_lane_preserved` call sites in `agent_workflows/runner_shared.py` at `def _finish(` line 12320, `def integrate_retired_lane(` line 36763, and `def execute_item_core(` lines 41308, 42100, and 43288).
  - Depends on: none
  - Expected outcome: `runner_shared._close_already_complete_backlog_item` passes `reason=f"teardown refused: {decision.reason}"`, `reason_codes=decision.reason_codes`, and `detail=decision.inventory.as_dict()` to `lane_containment.record_lane_preserved` and documents the `LaneTeardownDecision` (`txw63z` / spec `7ckptx` R5.6) invariant.
  - Execution state: performed

- [x] E-02 Add direct unit and end-to-end isolated runner tests for `_close_already_complete_backlog_item`'s `if not decision.torn_down:` branch in `tests/test_backlog_already_complete.py`:
  - In `TestBacklogAlreadyCompleteUnitE02` (`class TestBacklogAlreadyCompleteUnitE02(unittest.TestCase):` in `tests/test_backlog_already_complete.py`, line 69), add `test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory(self) -> None` driving `runner_shared._close_already_complete_backlog_item` directly against scratch git repositories (`_make_test_repo`) with `isolate=True` across both `LaneTeardownDecision.reason` branches (`class LaneTeardownDecision(NamedTuple):` in `agent_workflows/lane_containment.py`, lines 3783-3786). Harness requirements MEASURED at review with a scratch probe (each omission below crashes the call for a reason unrelated to the branch under test): commit a `.gitignore` holding `.aw/state/`, `.aw/records/runs/`, `.aw/worktrees/` with the fixtures (as `test_case_a_with_isolate_worktree` does); place `run_dir` under the gitignored `.aw/records/runs/`; build `item` with at least `{"id6": ..., "position": 1, "action": "plan", "status": "running"}` (without `"position"`, `lane_containment.item_slug` raises `KeyError: 'position'` inside `inventory_lane`); obtain `comp` from `runner_shared.backlog_item_already_complete(repo, <id6>)`; and pass `wt_handle=<handle>`, `isolate=True`, `run_checked=oc_runipd.run_checked`, `host_labels=runner_shared.OC_HOST_LABELS`, `save_state=lambda _r, _s: None`, and `integrate_review_lane_branch=oc_runipd.integrate_review_lane_branch` explicitly (`runner_shared` has no module-level `integrate_review_lane_branch`, so the `globals().get(...)` fallback yields `None`):
    1. **Unclassified lane content branch (`decision.error is None`, `decision.reason == decision.inventory.reason`)**: commit an `open` backlog item (`bklt01`) and an `executed` plan carrier (`plnt01`), allocate a real isolated lane worktree via `oc_runipd.allocate_isolation_worktree(repo, "bklt01")`, write an unclassified untracked file `(Path(wt_handle.path) / "untracked_residue.txt").write_text("keep me\n", encoding="utf-8")` in the lane, and call `runner_shared._close_already_complete_backlog_item` with real `lane_containment.teardown_lane_if_classified`. Assert it returns `True` without raising `AttributeError`, `bklt01` is moved to `.aw/records/backlog/done/` on `main`, the lane worktree directory and `untracked_residue.txt` still exist on disk, `item["preserved_worktree"] == str(wt_handle.path)`, `item["preserved_branch"] == wt_handle.branch`, `item["preserved_reason"]` starts with `"teardown refused: the lane holds content the driver cannot account for:"` and contains `"untracked_residue.txt"`, `item["preserved_retention_reasons"] == ["unknown-untracked-file"]`, and `events.jsonl` contains a `"worktree-preserved"` event with `"reason": item["preserved_reason"]`, `"retention_reasons": ["unknown-untracked-file"]`, `"unknown_untracked": ["untracked_residue.txt"]`, and `"inventory_readable": True`.
    2. **Authorized-teardown failure branch (`decision.error is not None`, `decision.reason == f"teardown was authorized but failed: {decision.error}"`)**: commit an `open` backlog item (`bklt02`) and an `executed` plan carrier (`plnt02`), allocate a clean isolated lane via `oc_runipd.allocate_isolation_worktree(repo, "bklt02")`, patch `runner_shared.teardown_isolation_worktree` to raise `RuntimeError("simulated worktree teardown error")`, and call `runner_shared._close_already_complete_backlog_item`. Assert it returns `True` without raising `AttributeError`, `item["preserved_reason"] == "teardown refused: teardown was authorized but failed: RuntimeError: simulated worktree teardown error"`, `item["preserved_retention_reasons"] == []`, and `events.jsonl` contains a `"worktree-preserved"` event with that exact `"reason"` and `"inventory_readable": True`.
  - In `TestBacklogAlreadyCompleteIntegrationE05` (`class TestBacklogAlreadyCompleteIntegrationE05(unittest.TestCase):` in `tests/test_backlog_already_complete.py`, line 149, appended after `test_case_i_post_turn_route` at line 786), add `test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane(self) -> None` driving `mod.run_queue(run_dir, retry_incomplete=False)` across both hosts (`for host_label, mod in _HOSTS:`) with worktree isolation enabled (no `--no-isolate-worktree`) on an `open` backlog item (`bklj01`) whose carrier plan (`plnj01`) starts in `pending/` at dispatch time and is moved to `executed/` and committed inside `work_dir` by `fake_agent` while `fake_agent` also writes an unclassified untracked file `(Path(work_dir) / "agent_scratch.txt").write_text("unclassified work\n", encoding="utf-8")` in the lane and produces 0 new plans. Assert `mod.run_queue` completes without raising `AttributeError`, `state["queue"][0]["status"] == "executed"`, `bklj01` is in `.aw/records/backlog/done/` on `main`, the lane worktree directory and `agent_scratch.txt` remain preserved on disk, and `events.jsonl` contains both `"backlog-already-complete"` and `"worktree-preserved"` events for `"bklj01"` where the `"worktree-preserved"` event has `"reason"` starting with `"teardown refused: the lane holds content the driver cannot account for:"` and containing `"agent_scratch.txt"`, `"retention_reasons": ["unknown-untracked-file"]`, and `"unknown_untracked": ["agent_scratch.txt"]`. `fake_agent` MUST move and commit the plan inside `kwargs["work_dir"]` (the lane), not in `repo`, so the lane commit is what reaches `main` through `integrate_under_repository_lock`. Do NOT assert the `"status"` field of the `"worktree-preserved"` event: it is a snapshot taken before `item["status"]` is set to `executed` and read `fail-verify` at review on both hosts.
  - Reachability (measured at review on HEAD `9e006dea9`, scratch probe under gitignored `.aw/state/`, deleted afterwards): on both `oc` and `agy`, this route reaches `_close_already_complete_backlog_item` via the post-turn call in `runner_shared.execute_item_core` (the `target_comp.status == BACKLOG_COMPLETE and not all_verified_plans` branch), ends `executed`, closes `bklj01` into `done/`, keeps `agent_scratch.txt`, and emits `worktree-preserved` with reason `teardown refused: the lane holds content the driver cannot account for: 1 unknown UNTRACKED file(s): agent_scratch.txt` and `retention_reasons == ["unknown-untracked-file"]`; with `LaneTeardownDecision.reason` forced to raise the txw63z `AttributeError`, `run_queue` propagated it on both hosts.
  - Depends on: E-01
  - Expected outcome: `tests/test_backlog_already_complete.py` directly tests `_close_already_complete_backlog_item`'s `if not decision.torn_down:` branch across both `LaneTeardownDecision.reason` paths and end-to-end across both runner hosts (`oc` and `agy`) with worktree isolation enabled.
  - Execution state: performed

- [x] E-03 Perform failure-sensitivity verification and run full repository validation:
  - Sensitivity check (1) (pre-fix bug from `txw63z`): temporarily replace `reason=f"teardown refused: {decision.reason}"` with `reason=f"teardown refused: {decision.why}"` in `runner_shared._close_already_complete_backlog_item` (`def _close_already_complete_backlog_item(` in `agent_workflows/runner_shared.py`, line 37094), run `python3 -m pytest -o addopts="" tests/test_backlog_already_complete.py -k "test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory or test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane"`, and verify both tests fail with `AttributeError: 'LaneTeardownDecision' object has no attribute 'why'`.
  - Sensitivity check (2) (`detail=decision.inventory.as_dict()` omission): temporarily remove `detail=decision.inventory.as_dict()` from `lane_containment.record_lane_preserved` in `runner_shared._close_already_complete_backlog_item` (`agent_workflows/runner_shared.py`, line 37090), run the same two tests, and verify both fail because `"unknown_untracked"` / `"inventory_readable"` are missing from the `"worktree-preserved"` event in `events.jsonl`. Restore `E-01`'s implementation after both sensitivity checks, then paste `git diff -- agent_workflows/runner_shared.py` proving the working tree holds exactly `E-01`'s change and no mutant (a mutant left in place would be committed by `aw commit`). The `-k` test names are non-binding pointers: if the executor names the tests differently, select the tests that pin these behaviours instead.
  - Run `python3 -m pytest -o addopts="" tests/test_backlog_already_complete.py tests/test_backlog_production.py tests/test_lane_retention_amended_r55.py tests/test_lane_submission_retention_narrowing.py`, `python3 -m unittest discover -s tests -t . -p test_backlog_already_complete.py -v`, `aw check release-gates`, `aw sanitize --agent`, and the bare repository test suite (`python3 -m pytest`).
  - Depends on: E-01, E-02
  - Expected outcome: Both sensitivity checks fail as expected when the corresponding code is reverted and pass once `E-01` is restored; targeted pytest modules, `unittest discover`, `aw check release-gates`, `aw sanitize --agent`, and bare `python3 -m pytest` all exit `0`.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Repository test runner contract (`AGENTS.md` section `## Repository development contract (repo-local rule)`): run the full test suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`). For narrowed runs, clear configured `addopts` explicitly with `python3 -m pytest -o addopts=""`.
- Outcome tests only (`AGENTS.md` section `TEST OUTCOMES, NOT CODE STRUCTURE (NO CODE-PINNING TESTS)`, P16): tests must drive functions, git worktrees, and runner queues and assert on return values, `state.json`, `events.jsonl`, and filesystem/git state, never inspecting source code text.
- Code citation convention (`AGENTS.md` and `IPD-C801`): cite code by symbol (`module.function`) or quoted string, with line numbers only appended to a symbol/quote and never alone.
- Release gate handoff (`AGENTS.md` section `### Every live bug gates the next release`): backlog `txw63z` carries `- Work-Kind: bug` and `- Blocks-Release: next`, so this graduating IPD inherits `- From-Backlog: txw63z` and `- Blocks-Release: next`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `lane_containment.LaneTeardownDecision` (`class LaneTeardownDecision(NamedTuple):` in `agent_workflows/lane_containment.py`, lines 3771-3791) defines fields `torn_down: bool`, `inventory: LaneInventory`, `error: str | None = None` and properties `preserved`, `reason`, and `reason_codes`. Neither `LaneTeardownDecision` nor `lane_containment.LaneInventory` (`class LaneInventory(NamedTuple):` in `agent_workflows/lane_containment.py`, line 3333) defines a `.why` attribute (`git grep -n "\.why\b" agent_workflows/` returns 0 matches). | `agent_workflows/lane_containment.py`, lines 3333-3431 and 3771-3791. |
| F-02 | When `runner_shared._close_already_complete_backlog_item` (`def _close_already_complete_backlog_item(` in `agent_workflows/runner_shared.py`, line 36833) was introduced by IPD `0owirm` (`c59ad329a`, `2026-10-13`), its `if not decision.torn_down:` branch called `lane_containment.record_lane_preserved` with `reason=f"teardown refused: {decision.why}"`. During execution of `a63epo` (`9d0ba2810` / `124b917238`, `2026-10-13`), when `commit_backlog_transition_output` left an uncommitted rename in the lane (`mlm0b5`), `teardown_lane_if_classified` returned `decision.torn_down == False` during `test_case_a_with_isolate_worktree` and crashed with `AttributeError: 'LaneTeardownDecision' object has no attribute 'why'`. The executor of `a63epo` filed `txw63z` (`9d0ba2810`) and patched `decision.why` -> `decision.reason` out-of-scope (`Scope-Exceeded` in `124b917238`) without linking `txw63z` (`a63epo` carried `- From-Backlog: r73v9i`), without documenting the `LaneTeardownDecision` contract, and without adding any test for the `if not decision.torn_down:` branch. | `git show c59ad329a -- agent_workflows/runner_shared.py`; `git show 9d0ba281051df6c32f6f6c1fb9832b662675c449`; `git show 124b9172380c6363c1fe29bdab9f45693c20dd55 -- agent_workflows/runner_shared.py`. |
| F-03 | Every other `lane_containment.teardown_lane_if_classified` -> `lane_containment.record_lane_preserved` call site in `agent_workflows/runner_shared.py` (`def _finish(` at line 12320, `def integrate_retired_lane(` at line 36763, and `def execute_item_core(` at lines 41308, 42100, and 43288) passes `detail=decision.inventory.as_dict()` so the `"worktree-preserved"` event in `events.jsonl` carries the structured `LaneInventory` fields (`dirty_tracked`, `unknown_untracked`, `uncollected_submission`, `unlanded_commits`, `inventory_readable`, etc., per `LaneInventory.as_dict` at `agent_workflows/lane_containment.py`, line 3416, and spec `7ckptx` R5.6). Only `runner_shared._close_already_complete_backlog_item` (`agent_workflows/runner_shared.py`, lines 37090-37096) omits `detail=decision.inventory.as_dict()`. | `agent_workflows/runner_shared.py`, lines 12316-12327, 36759-36770, 37083-37096, 41299-41315, 42090-42107, and 43279-43295. |
| F-04 | Across `tests/`, zero tests exercise the `if not decision.torn_down:` branch of `runner_shared._close_already_complete_backlog_item` (`git grep -n "teardown refused:" tests/` and `git grep -n "_close_already_complete_backlog_item" tests/` both return 0 matches): in `tests/test_backlog_already_complete.py`, `test_case_a_with_isolate_worktree` (line 237) only tests the clean-lane teardown (`decision.torn_down == True`), and `test_case_i_post_turn_route` (line 715) passes `--no-isolate-worktree` (`isolate=False`). | `tests/test_backlog_already_complete.py`, lines 237-326 and 715-786. |

## Proposed changes (ordered, validatable)

1. Update `runner_shared._close_already_complete_backlog_item` (`agent_workflows/runner_shared.py`, lines 37083-37096) to pass `detail=decision.inventory.as_dict()` to `lane_containment.record_lane_preserved` and document the `LaneTeardownDecision` (`txw63z` / spec `7ckptx` R5.6) contract (`E-01`).
2. Add `TestBacklogAlreadyCompleteUnitE02.test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory` and `TestBacklogAlreadyCompleteIntegrationE05.test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane` in `tests/test_backlog_already_complete.py` (`E-02`).
3. Run both failure-sensitivity checks, targeted test suites, `unittest discover`, `aw check release-gates`, `aw sanitize --agent`, and the bare repository test suite (`E-03`).

## Deferred / out of scope (with reason)

- Changing `runner_shared.reclaim_lanes_on_interrupt` (`def reclaim_lanes_on_interrupt(` in `agent_workflows/runner_shared.py`, lines 3021-3048) at normal run end (`mode == "run-end"`): `txw63z` scopes the defect to `runner_shared._close_already_complete_backlog_item` referencing `decision.why` on `LaneTeardownDecision`, and `reclaim_lanes_on_interrupt` already uses `decision.reason` and `decision.reason_codes` (lines 2992-2993 and 3181-3182).
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/runner_shared.py` (`_close_already_complete_backlog_item`) and `tests/test_backlog_already_complete.py` (unit and both-host isolated integration tests) are both declared in `- Scope-Paths:` and have disjoint edit regions from sibling pending plan `xocbpc` (`mlm0b5`).

## Required tests / validation

- Targeted pytest run: `python3 -m pytest -o addopts="" tests/test_backlog_already_complete.py tests/test_backlog_production.py tests/test_lane_retention_amended_r55.py tests/test_lane_submission_retention_narrowing.py`.
- Stdlib `unittest` discovery run: `python3 -m unittest discover -s tests -t . -p test_backlog_already_complete.py -v`.
- Sensitivity checks in `E-03` proving that (1) reverting `decision.reason` to `decision.why` in `_close_already_complete_backlog_item` fails both new tests with `AttributeError: 'LaneTeardownDecision' object has no attribute 'why'`, and (2) omitting `detail=decision.inventory.as_dict()` fails both new tests on missing inventory fields in the `"worktree-preserved"` event.
- Full repository suite and checks: bare `python3 -m pytest`, `aw check release-gates`, and `aw sanitize --agent`.

## Spec / documentation sync

N/A for `.spec.md` files and `CHANGELOG.md`: spec `7ckptx` R5.5 / R5.6 / R5.6a already specifies `teardown_lane_if_classified`, `LaneTeardownDecision`, and `record_lane_preserved`, and internal defect `txw63z` was introduced and patched within the unshipped `2.0.0 (pending)` window (`c59ad329a` / `124b917238`). Internal comment documentation in `runner_shared._close_already_complete_backlog_item` is updated in `E-01`.

## Open questions

### OQ-01: Since commit `124b917238` (`a63epo`) already replaced `decision.why` with `decision.reason` in `_close_already_complete_backlog_item` out-of-scope without linking `txw63z`, what remains to graduate and close `txw63z`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence (`git show c59ad329a`, `git show 9d0ba2810`, `git show 124b917238`, `agent_workflows/runner_shared.py` lines 37083-37096, `tests/test_backlog_already_complete.py`). First, `txw63z` carries `- Work-Kind: bug` and `- Blocks-Release: next`, so `check_engine.evaluate_blocking_close` requires a linked carrier (`- From-Backlog: txw63z`, `- Blocks-Release: next`) that executes to completion. Second, `124b917238` omitted `detail=decision.inventory.as_dict()` in `_close_already_complete_backlog_item`'s `record_lane_preserved` call (`F-03`), added no comment documenting the `LaneTeardownDecision` contract (`F-02`), and added zero unit or integration tests for the `if not decision.torn_down:` branch of `_close_already_complete_backlog_item` (`F-04`); `E-01`..`E-03` close all three gaps.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted `git diff -- agent_workflows/runner_shared.py` showing `runner_shared._close_already_complete_backlog_item` passing `reason=f"teardown refused: {decision.reason}"`, `reason_codes=decision.reason_codes`, and `detail=decision.inventory.as_dict()` to `lane_containment.record_lane_preserved` with the explanatory comment citing `txw63z`, `lane_containment.LaneTeardownDecision`, and spec `7ckptx` R5.6.
  - Observed evidence:
```diff
diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
index f2200f5ee..994a2a35f 100644
--- a/agent_workflows/runner_shared.py
+++ b/agent_workflows/runner_shared.py
@@ -37173,12 +37173,16 @@ def _close_already_complete_backlog_item(
             item=item,
         )
         if not decision.torn_down:
+            # txw63z: lane_containment.LaneTeardownDecision exposes .reason and .reason_codes
+            # (not .why). Spec 7ckptx R5.6 demands recording detail=decision.inventory.as_dict()
+            # on lane preservation matching sibling teardown_lane_if_classified call sites.
             lane_containment.record_lane_preserved(
                 run_dir=run_dir,
                 item=item,
                 handle=wt_handle,
                 reason=f"teardown refused: {decision.reason}",
                 reason_codes=decision.reason_codes,
+                detail=decision.inventory.as_dict(),
             )
     else:
         # Non-isolated path (--no-isolate-worktree)
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted `git diff -- tests/test_backlog_already_complete.py` and pasted outputs of (1) `python3 -m pytest -o addopts="" -v tests/test_backlog_already_complete.py` (reachable via `TestBacklogAlreadyCompleteUnitE02.test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory` and `TestBacklogAlreadyCompleteIntegrationE05.test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane` added in `E-02`) and (2) `python3 -m unittest discover -s tests -t . -p test_backlog_already_complete.py -v`, both showing all tests passing with exit code `0`. The bar is the behaviour, not the test names (which are non-binding pointers): the pasted output must show passing tests that pin (a) a direct `_close_already_complete_backlog_item` call returning `True` with the lane preserved and the `worktree-preserved` event carrying `decision.reason`, `retention_reasons`, and the `LaneInventory.as_dict()` fields, for both the unclassified-content and the authorized-teardown-failure branches, and (b) the isolated post-turn route on both `oc` and `agy` ending `executed` with the item in `done/` and the lane preserved.
  - Observed evidence:
    1. `git diff -- tests/test_backlog_already_complete.py`:
```diff
diff --git a/tests/test_backlog_already_complete.py b/tests/test_backlog_already_complete.py
index 9cdfbe7d0..f1b3a2d06 100644
--- a/tests/test_backlog_already_complete.py
+++ b/tests/test_backlog_already_complete.py
@@ -28,6 +28,7 @@ from pathlib import Path
 from unittest import mock

 from agent_workflows import (
+    oc_runipd,
     production_checks,
     runner_shared,
 )
@@ -145,6 +146,156 @@ class TestBacklogAlreadyCompleteUnitE02(unittest.TestCase):
             self.assertEqual(res_none.status, "NO_IPD_CARRIER")
             self.assertFalse(res_none.is_complete)

+    def test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory(
+        self,
+    ) -> None:
+        # 1. Unclassified lane content branch (decision.error is None, decision.reason == decision.inventory.reason)
+        with tempfile.TemporaryDirectory() as td1:
+            repo = _make_test_repo(Path(td1))
+            _write_backlog_item(repo, id6="bklt01", status="open")
+            _write_conforming_plan(
+                repo, id6="plnt01", backlog_id6="bklt01", bucket="executed"
+            )
+            (repo / ".gitignore").write_text(
+                ".aw/state/\n.aw/records/runs/\n.aw/worktrees/\n",
+                encoding="utf-8",
+            )
+            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
+            subprocess.run(
+                ["git", "commit", "-qm", "setup fixtures"],
+                cwd=repo,
+                check=True,
+            )
+
+            run_dir = repo / ".aw" / "records" / "runs" / "run-unit-01"
+            run_dir.mkdir(parents=True, exist_ok=True)
+            state = {"run_id": "run-unit-01", "options": {}}
+            item = {"id6": "bklt01", "position": 1, "action": "plan", "status": "running"}
+            comp = runner_shared.backlog_item_already_complete(repo, "bklt01")
+
+            wt_handle = oc_runipd.allocate_isolation_worktree(repo, "bklt01")
+            untracked_file = Path(wt_handle.path) / "untracked_residue.txt"
+            untracked_file.write_text("keep me\n", encoding="utf-8")
+
+            res = runner_shared._close_already_complete_backlog_item(
+                repo,
+                item,
+                state,
+                run_dir,
+                comp,
+                wt_handle=wt_handle,
+                isolate=True,
+                run_checked=oc_runipd.run_checked,
+                host_labels=runner_shared.OC_HOST_LABELS,
+                save_state=lambda _r, _s: None,
+                integrate_review_lane_branch=oc_runipd.integrate_review_lane_branch,
+            )
+            self.assertTrue(res)
+            bkl_files = list(
+                repo.glob(".aw/records/backlog/**/2026*bklt01*.backlog.md")
+            )
+            self.assertEqual(len(bkl_files), 1)
+            self.assertIn("/done/", str(bkl_files[0]).replace("\\", "/"))
+
+            self.assertTrue(Path(wt_handle.path).is_dir())
+            self.assertTrue(untracked_file.is_file())
+
+            self.assertEqual(item["preserved_worktree"], str(wt_handle.path))
+            self.assertEqual(item["preserved_branch"], wt_handle.branch)
+            self.assertTrue(
+                item["preserved_reason"].startswith(
+                    "teardown refused: the lane holds content the driver cannot account for:"
+                )
+            )
+            self.assertIn("untracked_residue.txt", item["preserved_reason"])
+            self.assertEqual(
+                item["preserved_retention_reasons"], ["unknown-untracked-file"]
+            )
+
+            events = [
+                json.loads(line)
+                for line in (run_dir / "events.jsonl")
+                .read_text(encoding="utf-8")
+                .splitlines()
+                if line
+            ]
+            pres_events = [
+                e for e in events if e.get("event") == "worktree-preserved"
+            ]
+            self.assertEqual(len(pres_events), 1)
+            pres_evt = pres_events[0]
+            self.assertEqual(pres_evt["reason"], item["preserved_reason"])
+            self.assertEqual(
+                pres_evt["retention_reasons"], ["unknown-untracked-file"]
+            )
+            self.assertEqual(
+                pres_evt["unknown_untracked"], ["untracked_residue.txt"]
+            )
+            self.assertTrue(pres_evt["inventory_readable"])
+
+        # 2. Authorized-teardown failure branch (decision.error is not None, decision.reason == f"teardown was authorized but failed: {decision.error}")
+        with tempfile.TemporaryDirectory() as td2:
+            repo2 = _make_test_repo(Path(td2))
+            _write_backlog_item(repo2, id6="bklt02", status="open")
+            _write_conforming_plan(
+                repo2, id6="plnt02", backlog_id6="bklt02", bucket="executed"
+            )
+            (repo2 / ".gitignore").write_text(
+                ".aw/state/\n.aw/records/runs/\n.aw/worktrees/\n",
+                encoding="utf-8",
+            )
+            subprocess.run(["git", "add", "-A"], cwd=repo2, check=True)
+            subprocess.run(
+                ["git", "commit", "-qm", "setup fixtures"],
+                cwd=repo2,
+                check=True,
+            )
+
+            run_dir2 = repo2 / ".aw" / "records" / "runs" / "run-unit-02"
+            run_dir2.mkdir(parents=True, exist_ok=True)
+            state2 = {"run_id": "run-unit-02", "options": {}}
+            item2 = {"id6": "bklt02", "position": 1, "action": "plan", "status": "running"}
+            comp2 = runner_shared.backlog_item_already_complete(repo2, "bklt02")
+
+            wt_handle2 = oc_runipd.allocate_isolation_worktree(repo2, "bklt02")
+
+            with mock.patch(
+                "agent_workflows.runner_shared.teardown_isolation_worktree",
+                side_effect=RuntimeError("simulated worktree teardown error"),
+            ):
+                res2 = runner_shared._close_already_complete_backlog_item(
+                    repo2,
+                    item2,
+                    state2,
+                    run_dir2,
+                    comp2,
+                    wt_handle=wt_handle2,
+                    isolate=True,
+                    run_checked=oc_runipd.run_checked,
+                    host_labels=runner_shared.OC_HOST_LABELS,
+                    save_state=lambda _r, _s: None,
+                    integrate_review_lane_branch=oc_runipd.integrate_review_lane_branch,
+                )
+            self.assertTrue(res2)
+            expected_reason = "teardown refused: teardown was authorized but failed: RuntimeError: simulated worktree teardown error"
+            self.assertEqual(item2["preserved_reason"], expected_reason)
+            self.assertEqual(item2["preserved_retention_reasons"], [])
+
+            events2 = [
+                json.loads(line)
+                for line in (run_dir2 / "events.jsonl")
+                .read_text(encoding="utf-8")
+                .splitlines()
+                if line
+            ]
+            pres_events2 = [
+                e for e in events2 if e.get("event") == "worktree-preserved"
+            ]
+            self.assertEqual(len(pres_events2), 1)
+            pres_evt2 = pres_events2[0]
+            self.assertEqual(pres_evt2["reason"], expected_reason)
+            self.assertTrue(pres_evt2["inventory_readable"])
+

 class TestBacklogAlreadyCompleteIntegrationE05(unittest.TestCase):
     """Spec runner integration matrix on both hosts (E-05)."""
@@ -783,3 +934,135 @@ class TestBacklogAlreadyCompleteIntegrationE05(unittest.TestCase):
                     self.assertNotIn(
                         "/graduated/", str(bkl_files[0]).replace("\\", "/")
                     )
+
+    def test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane(
+        self,
+    ) -> None:
+        """Case (j): isolated post-turn route when teardown is refused preserves lane and records reason/inventory."""
+        for host_label, mod in _HOSTS:
+            with self.subTest(host=host_label):
+                with tempfile.TemporaryDirectory() as td:
+                    repo = _make_test_repo(Path(td))
+                    _write_backlog_item(repo, id6="bklj01", status="open")
+                    p_path = _write_conforming_plan(
+                        repo, id6="plnj01", backlog_id6="bklj01", bucket="pending"
+                    )
+                    (repo / ".gitignore").write_text(
+                        ".aw/state/\n.aw/records/runs/\n.aw/worktrees/\n",
+                        encoding="utf-8",
+                    )
+                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
+                    subprocess.run(
+                        ["git", "commit", "-qm", "setup fixtures"],
+                        cwd=repo,
+                        check=True,
+                    )
+
+                    run_id = f"run-{host_label}-case-j"
+                    cmd = [
+                        "start",
+                        "bklj01",
+                        "--action",
+                        "plan",
+                        "--repo",
+                        str(repo),
+                        "--run-id",
+                        run_id,
+                    ]
+                    args = mod.build_parser().parse_args(cmd)
+                    buf = io.StringIO()
+                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
+                        buf
+                    ):
+                        run_dir = mod.initialize_run(args)
+
+                    def fake_agent(
+                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
+                    ):
+                        work_dir = Path(kwargs["work_dir"])
+                        exec_dir = work_dir / ".aw" / "records" / "plans" / "executed"
+                        exec_dir.mkdir(parents=True, exist_ok=True)
+                        source = (
+                            work_dir
+                            / ".aw"
+                            / "records"
+                            / "plans"
+                            / "pending"
+                            / p_path.name
+                        )
+                        dest = exec_dir / p_path.name
+                        shutil.move(str(source), str(dest))
+                        subprocess.run(
+                            ["git", "add", "-A"], cwd=work_dir, check=True
+                        )
+                        subprocess.run(
+                            ["git", "commit", "-qm", "carrier executed in lane"],
+                            cwd=work_dir,
+                            check=True,
+                        )
+                        (work_dir / "agent_scratch.txt").write_text(
+                            "unclassified work\n", encoding="utf-8"
+                        )
+                        return 0, "session", rdir / "log.txt", ["cmd"]
+
+                    with _patch_host_agent(mod, fake_agent):
+                        with contextlib.redirect_stdout(
+                            buf
+                        ), contextlib.redirect_stderr(buf):
+                            mod.run_queue(run_dir, retry_incomplete=False)
+
+                    state = json.loads(
+                        (run_dir / "state.json").read_text(encoding="utf-8")
+                    )
+                    self.assertEqual(state["queue"][0]["status"], "executed")
+
+                    bkl_files = list(
+                        repo.glob(".aw/records/backlog/**/2026*bklj01*.backlog.md")
+                    )
+                    self.assertEqual(len(bkl_files), 1)
+                    self.assertIn("/done/", str(bkl_files[0]).replace("\\", "/"))
+
+                    pres_wt = state["queue"][0].get("preserved_worktree")
+                    self.assertIsNotNone(pres_wt)
+                    lane_dir = Path(str(pres_wt))
+                    self.assertTrue(lane_dir.is_dir())
+                    self.assertTrue((lane_dir / "agent_scratch.txt").is_file())
+
+                    events = [
+                        json.loads(line)
+                        for line in (run_dir / "events.jsonl")
+                        .read_text(encoding="utf-8")
+                        .splitlines()
+                        if line
+                    ]
+                    bkl_complete_events = [
+                        e
+                        for e in events
+                        if e.get("id6") == "bklj01"
+                        and e.get("event") == "backlog-already-complete"
+                    ]
+                    self.assertEqual(len(bkl_complete_events), 1)
+
+                    pres_events = [
+                        e
+                        for e in events
+                        if e.get("id6") == "bklj01"
+                        and e.get("event") == "worktree-preserved"
+                    ]
+                    self.assertEqual(len(pres_events), 1)
+                    pres_evt = pres_events[0]
+                    self.assertTrue(
+                        pres_evt["reason"].startswith(
+                            "teardown refused: the lane holds content the driver cannot account for:"
+                        )
+                    )
+                    self.assertIn("agent_scratch.txt", pres_evt["reason"])
+                    self.assertEqual(
+                        pres_evt["retention_reasons"],
+                        ["unknown-untracked-file"],
+                    )
+                    self.assertEqual(
+                        pres_evt["unknown_untracked"],
+                        ["agent_scratch.txt"],
+                    )
```

    2. `python3 -m pytest -o addopts="" -v tests/test_backlog_already_complete.py`:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
cachedir: .pytest_cache
Using --randomly-seed=2392802139
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/uwaasz
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 13 items

tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane PASSED [  7%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_g_gated_item_no_gate_on_carrier PASSED [ 15%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_a_no_isolate_worktree PASSED [ 23%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_d_mixed_executed_and_superseded PASSED [ 30%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_i_post_turn_route PASSED [ 38%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_a_with_isolate_worktree PASSED [ 46%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_b_one_carrier_pending PASSED [ 53%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_c_every_carrier_retired PASSED [ 61%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_e_executed_ipd_plus_approved_spec PASSED [ 69%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_f_gated_item_matching_gate PASSED [ 76%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_h_backlog_graduate_count PASSED [ 84%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteUnitE02::test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory PASSED [ 92%]
tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteUnitE02::test_predicate_states PASSED [100%]

============================= 13 passed in 25.29s ==============================
```

    3. `python3 -m unittest discover -s tests -t . -p test_backlog_already_complete.py -v`:
```
test_case_a_no_isolate_worktree (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_a_no_isolate_worktree)
Case (a): every IPD carrier executed; item closed done, agent never called, ... ok
test_case_a_with_isolate_worktree (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_a_with_isolate_worktree)
Case (a) with isolation: shared checkout git status is empty before integration, ... ok
test_case_b_one_carrier_pending (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_b_one_carrier_pending)
Case (b): one carrier pending: agent called and item graduates as today. ... ok
test_case_c_every_carrier_retired (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_c_every_carrier_retired)
Case (c): every carrier retired (superseded/): item NOT closed, dispatched as today. ... ok
test_case_d_mixed_executed_and_superseded (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_d_mixed_executed_and_superseded)
Case (d): one executed and one superseded carrier: NOT closed. ... ok
test_case_e_executed_ipd_plus_approved_spec (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_e_executed_ipd_plus_approved_spec)
Case (e): one executed IPD carrier plus an approved (not implemented) spec carrier: NOT closed. ... ok
test_case_f_gated_item_matching_gate (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_f_gated_item_matching_gate)
Case (f): Blocks-Release: rel001 item whose executed carrier carries the same gate: ... ok
test_case_g_gated_item_no_gate_on_carrier (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_g_gated_item_no_gate_on_carrier)
Case (g): Blocks-Release item whose executed carrier carries NO gate and no other ... ok
test_case_h_backlog_graduate_count (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_h_backlog_graduate_count)
Case (h): backlog_graduate_count returns no finding for (a)'s tree and ... ok
test_case_i_post_turn_route (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_i_post_turn_route)
Case (i): post-turn route of E-04 (b): item becomes COMPLETE during turn, ... ok
test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteIntegrationE05.test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane)
Case (j): isolated post-turn route when teardown is refused preserves lane and records reason/inventory. ... ok
test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteUnitE02.test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory) ...   ✓ backlog item bklt01 is already complete (every IPD carrier is executed and every spec carrier is implemented (.aw/records/plans/executed/20260927-demo-01-plnt01-test-plan.ipd.md)); closed done
  ✓ backlog item bklt02 is already complete (every IPD carrier is executed and every spec carrier is implemented (.aw/records/plans/executed/20260927-demo-01-plnt02-test-plan.ipd.md)); closed done
ok
test_predicate_states (tests.test_backlog_already_complete.TestBacklogAlreadyCompleteUnitE02.test_predicate_states) ... ok

----------------------------------------------------------------------
Ran 13 tests in 26.352s

OK
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted outputs of both sensitivity checks in `E-03` (showing both `test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory` and `test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane` failing with `AttributeError: 'LaneTeardownDecision' object has no attribute 'why'` when `decision.why` is restored in `_close_already_complete_backlog_item`, and failing on missing inventory fields when `detail=decision.inventory.as_dict()` is omitted, followed by passing after restoration, and the post-restoration `git diff -- agent_workflows/runner_shared.py` showing only `E-01`'s change with neither mutant present); plus pasted exit-0 outputs of `python3 -m pytest -o addopts="" tests/test_backlog_already_complete.py tests/test_backlog_production.py tests/test_lane_retention_amended_r55.py tests/test_lane_submission_retention_narrowing.py`, `aw check release-gates`, `aw sanitize --agent`, and bare `python3 -m pytest`.
  - Observed evidence:
    1. Sensitivity check (1) (`decision.why` restored):
```
FAILED tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane
FAILED tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteUnitE02::test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory
======================= 2 failed, 11 deselected in 6.45s =======================
E               AttributeError: 'LaneTeardownDecision' object has no attribute 'why'
agent_workflows/runner_shared.py:37183: AttributeError
```

    2. Sensitivity check (2) (omitting `detail=decision.inventory.as_dict()`):
```
FAILED tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteIntegrationE05::test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane
FAILED tests/test_backlog_already_complete.py::TestBacklogAlreadyCompleteUnitE02::test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory
======================= 2 failed, 11 deselected in 3.74s =======================
E                   KeyError: 'unknown_untracked'
tests/test_backlog_already_complete.py:1065: KeyError
```

    3. Post-restoration test run:
```
tests/test_backlog_already_complete.py ..                                [100%]
======================= 2 passed, 11 deselected in 5.88s =======================
```

    4. Post-restoration `git diff -- agent_workflows/runner_shared.py`:
```diff
diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
index f2200f5ee..994a2a35f 100644
--- a/agent_workflows/runner_shared.py
+++ b/agent_workflows/runner_shared.py
@@ -37173,12 +37173,16 @@ def _close_already_complete_backlog_item(
             item=item,
         )
         if not decision.torn_down:
+            # txw63z: lane_containment.LaneTeardownDecision exposes .reason and .reason_codes
+            # (not .why). Spec 7ckptx R5.6 demands recording detail=decision.inventory.as_dict()
+            # on lane preservation matching sibling teardown_lane_if_classified call sites.
             lane_containment.record_lane_preserved(
                 run_dir=run_dir,
                 item=item,
                 handle=wt_handle,
                 reason=f"teardown refused: {decision.reason}",
                 reason_codes=decision.reason_codes,
+                detail=decision.inventory.as_dict(),
             )
     else:
         # Non-isolated path (--no-isolate-worktree)
```

    5. Targeted pytest run: `python3 -m pytest -o addopts="" tests/test_backlog_already_complete.py tests/test_backlog_production.py tests/test_lane_retention_amended_r55.py tests/test_lane_submission_retention_narrowing.py`:
```
tests/test_backlog_production.py ...............                         [ 33%]
tests/test_lane_retention_amended_r55.py ....                            [ 42%]
tests/test_lane_submission_retention_narrowing.py .............          [ 71%]
tests/test_backlog_already_complete.py .............                     [100%]

============================= 45 passed in 56.33s ==============================
```

    6. `aw check release-gates`:
```
AW check  release-gates                                                  1644 ms
✓ CONFORMS  78 release-gates checked

Evidence
  backlog  28   specs  19   plans  30   releases  1
  errors  0   warnings  0   info  0
```

    7. `aw sanitize --agent`:
```
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5242,"findings":0,"evidence":["leak-scan"],"next":null}
```

    8. Bare `python3 -m pytest`:
```
707 passed in 21.99s
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Execution contract**: Execute `E-01` through `E-03` in dependency order inside an isolated worktree. Start with `aw ipd begin uwaasz`. Do not mark any `E-*` item `performed` before completing its action, and do not mark any `V-*` item `pass` without pasting concrete observed command output into `Observed evidence:`. Run the repository suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`). You MUST paste the actual runner output for every test or check you report as passing; never claim a result you did not run. Scope fence: `- Scope-Paths:` declares the intended edit set; an edit outside it is permitted when the work requires it but must be justified at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Delete any scratch probe you create. Commit only files listed in `- Scope-Paths:` plus this IPD using `aw commit uwaasz -- <paths>`, and never push.
- **Post-gate lifecycle move**: Under `aw oc run` / `aw agy run`, the runner performs the finalize after its merge-and-revalidate gate, so the executor must not run `aw ipd finalize`. When executed by hand, once `E-01`..`E-03` are `performed`, `V-01`..`V-03` are `pass`, and `aw ipd lint --phase pre-transition` reports 0 errors, finalize the plan via `aw ipd finalize uwaasz`.
