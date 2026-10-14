# IPD: Pass decision.reason and inventory detail when _close_already_complete_backlog_item preserves a lane

- Date: 2026-10-14
- Kind: child
- Concern: Backlog item `txw63z` (`Work-Kind: bug`, `Priority: medium`, `Blocks-Release: next`) was filed during execution of IPD `a63epo` (`9d0ba2810` / `124b917238`, `2026-10-13`) when `runner_shared._close_already_complete_backlog_item` (`def _close_already_complete_backlog_item(` in `agent_workflows/runner_shared.py`, line 36833; introduced by `0owirm` in `c59ad329a`) entered its `if not decision.torn_down:` branch after `lane_containment.teardown_lane_if_classified` refused teardown of an isolated lane and evaluated `reason=f"teardown refused: {decision.why}"`, raising `AttributeError: 'LaneTeardownDecision' object has no attribute 'why'` because `lane_containment.LaneTeardownDecision` (`class LaneTeardownDecision(NamedTuple):` in `agent_workflows/lane_containment.py`, line 3771) defines `.reason`, `.reason_codes`, and `.inventory`, not `.why`. Commit `124b917238` (`a63epo`) applied an out-of-scope (`Scope-Exceeded`) edit replacing `decision.why` with `decision.reason` in `runner_shared._close_already_complete_backlog_item` without linking `txw63z` (`a63epo` carried `- From-Backlog: r73v9i`), without documenting the `LaneTeardownDecision` contract or passing `detail=decision.inventory.as_dict()` to `lane_containment.record_lane_preserved` (which all five other `teardown_lane_if_classified` -> `record_lane_preserved` call sites in `agent_workflows/runner_shared.py` pass per spec `7ckptx` R5.6), and without adding any unit or integration test exercising the `if not decision.torn_down:` branch of `_close_already_complete_backlog_item`.
- Scope: Update `runner_shared._close_already_complete_backlog_item` (`def _close_already_complete_backlog_item(` in `agent_workflows/runner_shared.py`, lines 37083-37096) to pass `detail=decision.inventory.as_dict()` alongside `reason=f"teardown refused: {decision.reason}"` and `reason_codes=decision.reason_codes` to `lane_containment.record_lane_preserved` and document the `LaneTeardownDecision` (`txw63z` / spec `7ckptx` R5.6) contract; add direct unit coverage in `TestBacklogAlreadyCompleteUnitE02` (`tests/test_backlog_already_complete.py`, line 69) and end-to-end isolated runner coverage across both hosts (`oc` and `agy`) in `TestBacklogAlreadyCompleteIntegrationE05` (`tests/test_backlog_already_complete.py`, line 149) exercising the `if not decision.torn_down:` branch of `_close_already_complete_backlog_item`; and verify failure sensitivity and full-suite conformance so `txw63z` closes with a verified release-gate carrier.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_backlog_already_complete.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: txw63z
- Blocks-Release: next
- Set: txw63z
- Order: 1
- Highest E allocated: 03
- Author: Antigravity
- Id: uwaasz

## Workflow history
- 2026-10-14 to-review (aw set): Authored review-ready child IPD uwaasz from backlog txw63z

- 2026-10-14 draft (Antigravity): created.

## Goal

Ensure `runner_shared._close_already_complete_backlog_item` records `decision.reason`, `decision.reason_codes`, and `detail=decision.inventory.as_dict()` via `lane_containment.record_lane_preserved` whenever `lane_containment.teardown_lane_if_classified` refuses teardown (`not decision.torn_down`), and pin that branch across unit and both-host (`oc` and `agy`) isolated runner tests so `txw63z` closes with an executed release-gate carrier.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Align _close_already_complete_backlog_item lane-preservation recording and pin teardown-refusal coverage

- [ ] E-01 Update `runner_shared._close_already_complete_backlog_item` (`def _close_already_complete_backlog_item(` in `agent_workflows/runner_shared.py`, lines 37083-37096) in its `if not decision.torn_down:` branch to pass `detail=decision.inventory.as_dict()` alongside `reason=f"teardown refused: {decision.reason}"` and `reason_codes=decision.reason_codes` to `lane_containment.record_lane_preserved` (`def record_lane_preserved(` in `agent_workflows/lane_containment.py`, line 4059), and add an explanatory comment citing backlog `txw63z`, `lane_containment.LaneTeardownDecision` (`class LaneTeardownDecision(NamedTuple):` in `agent_workflows/lane_containment.py`, line 3771), and spec `7ckptx` R5.6 (matching the five sibling `teardown_lane_if_classified` -> `record_lane_preserved` call sites in `agent_workflows/runner_shared.py` at `def _finish(` line 12320, `def handle_in_lane_retired(` line 36763, and `def execute_item_core(` lines 41308, 42100, and 43288).
  - Depends on: none
  - Expected outcome: `runner_shared._close_already_complete_backlog_item` passes `reason=f"teardown refused: {decision.reason}"`, `reason_codes=decision.reason_codes`, and `detail=decision.inventory.as_dict()` to `lane_containment.record_lane_preserved` and documents the `LaneTeardownDecision` (`txw63z` / spec `7ckptx` R5.6) invariant.
  - Execution state: pending

- [ ] E-02 Add direct unit and end-to-end isolated runner tests for `_close_already_complete_backlog_item`'s `if not decision.torn_down:` branch in `tests/test_backlog_already_complete.py`:
  - In `TestBacklogAlreadyCompleteUnitE02` (`class TestBacklogAlreadyCompleteUnitE02(unittest.TestCase):` in `tests/test_backlog_already_complete.py`, line 69), add `test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory(self) -> None` driving `runner_shared._close_already_complete_backlog_item` directly against scratch git repositories (`_make_test_repo`) with `isolate=True` across both `LaneTeardownDecision.reason` branches (`class LaneTeardownDecision(NamedTuple):` in `agent_workflows/lane_containment.py`, lines 3783-3786):
    1. **Unclassified lane content branch (`decision.error is None`, `decision.reason == decision.inventory.reason`)**: commit an `open` backlog item (`bklt01`) and an `executed` plan carrier (`plnt01`), allocate a real isolated lane worktree via `oc_runipd.allocate_isolation_worktree(repo, "bklt01")`, write an unclassified untracked file `(Path(wt_handle.path) / "untracked_residue.txt").write_text("keep me\n", encoding="utf-8")` in the lane, and call `runner_shared._close_already_complete_backlog_item` with real `lane_containment.teardown_lane_if_classified`. Assert it returns `True` without raising `AttributeError`, `bklt01` is moved to `.aw/records/backlog/done/` on `main`, the lane worktree directory and `untracked_residue.txt` still exist on disk, `item["preserved_worktree"] == str(wt_handle.path)`, `item["preserved_branch"] == wt_handle.branch`, `item["preserved_reason"]` starts with `"teardown refused: the lane holds content the driver cannot account for:"` and contains `"untracked_residue.txt"`, `item["preserved_retention_reasons"] == ["unknown-untracked"]`, and `events.jsonl` contains a `"worktree-preserved"` event with `"reason": item["preserved_reason"]`, `"retention_reasons": ["unknown-untracked"]`, `"unknown_untracked": ["untracked_residue.txt"]`, and `"inventory_readable": True`.
    2. **Authorized-teardown failure branch (`decision.error is not None`, `decision.reason == f"teardown was authorized but failed: {decision.error}"`)**: commit an `open` backlog item (`bklt02`) and an `executed` plan carrier (`plnt02`), allocate a clean isolated lane via `oc_runipd.allocate_isolation_worktree(repo, "bklt02")`, patch `runner_shared.teardown_isolation_worktree` to raise `RuntimeError("simulated worktree teardown error")`, and call `runner_shared._close_already_complete_backlog_item`. Assert it returns `True` without raising `AttributeError`, `item["preserved_reason"] == "teardown refused: teardown was authorized but failed: RuntimeError: simulated worktree teardown error"`, `item["preserved_retention_reasons"] == []`, and `events.jsonl` contains a `"worktree-preserved"` event with that exact `"reason"` and `"inventory_readable": True`.
  - In `TestBacklogAlreadyCompleteIntegrationE05` (`class TestBacklogAlreadyCompleteIntegrationE05(unittest.TestCase):` in `tests/test_backlog_already_complete.py`, line 149, appended after `test_case_i_post_turn_route` at line 786), add `test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane(self) -> None` driving `mod.run_queue(run_dir, retry_incomplete=False)` across both hosts (`for host_label, mod in _HOSTS:`) with worktree isolation enabled (no `--no-isolate-worktree`) on an `open` backlog item (`bklj01`) whose carrier plan (`plnj01`) starts in `pending/` at dispatch time and is moved to `executed/` and committed inside `work_dir` by `fake_agent` while `fake_agent` also writes an unclassified untracked file `(Path(work_dir) / "agent_scratch.txt").write_text("unclassified work\n", encoding="utf-8")` in the lane and produces 0 new plans. Assert `mod.run_queue` completes without raising `AttributeError`, `state["queue"][0]["status"] == "executed"`, `bklj01` is in `.aw/records/backlog/done/` on `main`, the lane worktree directory and `agent_scratch.txt` remain preserved on disk, and `events.jsonl` contains both `"backlog-already-complete"` and `"worktree-preserved"` events for `"bklj01"` where the `"worktree-preserved"` event has `"reason"` starting with `"teardown refused: the lane holds content the driver cannot account for:"` and containing `"agent_scratch.txt"`, `"retention_reasons": ["unknown-untracked"]`, and `"unknown_untracked": ["agent_scratch.txt"]`.
  - Depends on: E-01
  - Expected outcome: `tests/test_backlog_already_complete.py` directly tests `_close_already_complete_backlog_item`'s `if not decision.torn_down:` branch across both `LaneTeardownDecision.reason` paths and end-to-end across both runner hosts (`oc` and `agy`) with worktree isolation enabled.
  - Execution state: pending

- [ ] E-03 Perform failure-sensitivity verification and run full repository validation:
  - Sensitivity check (1) (pre-fix bug from `txw63z`): temporarily replace `reason=f"teardown refused: {decision.reason}"` with `reason=f"teardown refused: {decision.why}"` in `runner_shared._close_already_complete_backlog_item` (`def _close_already_complete_backlog_item(` in `agent_workflows/runner_shared.py`, line 37094), run `python3 -m pytest -o addopts="" tests/test_backlog_already_complete.py -k "test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory or test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane"`, and verify both tests fail with `AttributeError: 'LaneTeardownDecision' object has no attribute 'why'`.
  - Sensitivity check (2) (`detail=decision.inventory.as_dict()` omission): temporarily remove `detail=decision.inventory.as_dict()` from `lane_containment.record_lane_preserved` in `runner_shared._close_already_complete_backlog_item` (`agent_workflows/runner_shared.py`, line 37090), run the same two tests, and verify both fail because `"unknown_untracked"` / `"inventory_readable"` are missing from the `"worktree-preserved"` event in `events.jsonl`. Restore `E-01`'s implementation after both sensitivity checks.
  - Run `python3 -m pytest -o addopts="" tests/test_backlog_already_complete.py tests/test_backlog_production.py tests/test_lane_retention_amended_r55.py tests/test_lane_submission_retention_narrowing.py`, `python3 -m unittest discover -s tests -t . -p test_backlog_already_complete.py -v`, `aw check release-gates`, `aw sanitize --agent`, and the bare repository test suite (`python3 -m pytest`).
  - Depends on: E-01, E-02
  - Expected outcome: Both sensitivity checks fail as expected when the corresponding code is reverted and pass once `E-01` is restored; targeted pytest modules, `unittest discover`, `aw check release-gates`, `aw sanitize --agent`, and bare `python3 -m pytest` all exit `0`.
  - Execution state: pending

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
| F-03 | Every other `lane_containment.teardown_lane_if_classified` -> `lane_containment.record_lane_preserved` call site in `agent_workflows/runner_shared.py` (`def _finish(` at line 12320, `def handle_in_lane_retired(` at line 36763, and `def execute_item_core(` at lines 41308, 42100, and 43288) passes `detail=decision.inventory.as_dict()` so the `"worktree-preserved"` event in `events.jsonl` carries the structured `LaneInventory` fields (`dirty_tracked`, `unknown_untracked`, `uncollected_submission`, `unlanded_commits`, `inventory_readable`, etc., per `LaneInventory.as_dict` at `agent_workflows/lane_containment.py`, line 3416, and spec `7ckptx` R5.6). Only `runner_shared._close_already_complete_backlog_item` (`agent_workflows/runner_shared.py`, lines 37090-37096) omits `detail=decision.inventory.as_dict()`. | `agent_workflows/runner_shared.py`, lines 12316-12327, 36759-36770, 37083-37096, 41299-41315, 42090-42107, and 43279-43295. |
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

- [ ] V-01 validates E-01
  - Required evidence: Pasted `git diff -- agent_workflows/runner_shared.py` showing `runner_shared._close_already_complete_backlog_item` passing `reason=f"teardown refused: {decision.reason}"`, `reason_codes=decision.reason_codes`, and `detail=decision.inventory.as_dict()` to `lane_containment.record_lane_preserved` with the explanatory comment citing `txw63z`, `lane_containment.LaneTeardownDecision`, and spec `7ckptx` R5.6.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- tests/test_backlog_already_complete.py` and pasted outputs of (1) `python3 -m pytest -o addopts="" -v tests/test_backlog_already_complete.py` (reachable via `TestBacklogAlreadyCompleteUnitE02.test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory` and `TestBacklogAlreadyCompleteIntegrationE05.test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane` added in `E-02`) and (2) `python3 -m unittest discover -s tests -t . -p test_backlog_already_complete.py -v`, both showing all tests passing with exit code `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted outputs of both sensitivity checks in `E-03` (showing both `test_close_already_complete_backlog_item_teardown_refused_preserves_lane_and_records_reason_and_inventory` and `test_case_j_isolated_post_turn_route_teardown_refused_preserves_lane` failing with `AttributeError: 'LaneTeardownDecision' object has no attribute 'why'` when `decision.why` is restored in `_close_already_complete_backlog_item`, and failing on missing inventory fields when `detail=decision.inventory.as_dict()` is omitted, followed by passing after restoration); plus pasted exit-0 outputs of `python3 -m pytest -o addopts="" tests/test_backlog_already_complete.py tests/test_backlog_production.py tests/test_lane_retention_amended_r55.py tests/test_lane_submission_retention_narrowing.py`, `aw check release-gates`, `aw sanitize --agent`, and bare `python3 -m pytest`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Execution contract**: Execute `E-01` through `E-03` in dependency order inside an isolated worktree. Start with `aw ipd begin uwaasz`. Do not mark any `E-*` item `performed` before completing its action, and do not mark any `V-*` item `pass` without pasting concrete observed command output into `Observed evidence:`. Run the repository suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`). Commit only files listed in `- Scope-Paths:` plus this IPD using `aw commit uwaasz -- <paths>`, and never push.
- **Post-gate lifecycle move**: Under `aw oc run` / `aw agy run`, the runner performs the finalize after its merge-and-revalidate gate, so the executor must not run `aw ipd finalize`. When executed by hand, once `E-01`..`E-03` are `performed`, `V-01`..`V-03` are `pass`, and `aw ipd lint --phase pre-transition` reports 0 errors, finalize the plan via `aw ipd finalize uwaasz`.
