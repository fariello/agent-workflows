# IPD: Restore behavioral coverage that run_queue exits nonzero on a substantially-complete item

- Date: 2026-10-14
- Kind: child
- Concern: The property that `run_queue` computes its EXIT CODE from the completion bar `SUCCESS_STATES` (which excludes `substantially-complete`), so a run whose only item ended `substantially-complete` exits NONZERO, lost its only end-to-end guard when `tests/test_rununify_run_queue.py` was deleted in `19313eed7` (yuhl6o site S-29, RETIRE-UNGUARDED). Nothing now drives `run_queue` on either host and asserts that return value.
- Scope: Add behavioral tests to `tests/test_run_exit_aggregate.py` that drive the real `oc_runipd.run_queue` and `agy_runipd.run_queue` over a synthetic one-item `state.json` with only the agent turn (`execute_item`) stubbed, and assert the returned exit code per terminal item status. Test-only; no production change.
- Scope-Paths: tests/test_run_exit_aggregate.py, .aw/records/plans/pending/20261014-bzjclz-01-eg6r2t-restore-behavioral-coverage-that-run-queue-exits-nonzero-on.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: bzjclz
- Set: bzjclz
- Order: 1
- Highest E allocated: 03
- Author: OpenCode Claude Opus
- Id: eg6r2t
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (/plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed; readiness GO - PENDING HUMAN APPROVAL

- 2026-10-14 draft (OpenCode Claude Opus): created.
- 2026-10-14 to-review (OpenCode Claude Opus): authored from backlog `bzjclz`; Step 0 evidence gathered (including a throwaway dual-host probe of `run_queue`); ready for `/plan-review`.

## Goal

Restore, as behavior-only tests, the property the deleted `TheExitCodeReflectsTheRealOutcome.test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES` guarded: on both hosts, `run_queue` returns 0 for a fully `executed` queue and a NONZERO code when the only item ends `substantially-complete` (or `failed-safely`), so an incomplete execution is never reported as a clean run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: A run_queue driving harness

- [x] E-01 Add to `tests/test_run_exit_aggregate.py` a new `unittest.TestCase` class (e.g. `RunQueueExitCodeReflectsTheRealOutcome`) with a helper that, given a host module and a terminal status, writes a temp `run_dir/state.json` (`schema_version: 1`, `run_id`, `repo` = the temp root, `created_at`/`updated_at`, `selectors`, `options: {}`, `set_sessions: {}`, and a single queue item `{"position": 1, "id6": "aaa111", "setid": "s", "action": "execute", "kind": "child", "status": "queued", "dependencies": [], "attempts": []}`), patches `module.execute_item` with a fake that sets `item["status"]` to the given status and calls `module.save_state(run_dir, state)`, redirects stdout/stderr, calls `module.run_queue(run_dir, retry_incomplete=False)`, and returns the exit code plus the reloaded `state.json`. Use `tempfile.TemporaryDirectory` with `addCleanup` so no run dir outlives the test; do not patch `dispatch_orchestrator_item` or anything else (a one-item `execute` queue needs no other stub, demonstrated at review). Mirror the harness shape of `DispatchRunCase.make_run`/`drive` in `tests/test_orchestrator_retirement.py`. Add a control test asserting, for each host via `subTest`, that a status of `executed` returns 0 and the reloaded item status is `executed`.
  - Depends on: none
  - Expected outcome: a reusable dual-host harness, and a passing control proving a clean run exits 0 (so a later nonzero assertion is not vacuous).
  - Execution state: performed

### Task group 2: The restored property

- [x] E-02 Add a test asserting, for each host via `subTest`, that when the stubbed turn leaves the item `substantially-complete`, `run_queue` returns a nonzero code, and that the reloaded `state.json` item status is `substantially-complete` (proving the status reached the exit computation rather than being rewritten). The assertion message must state that `substantially-complete` is not a completion success for the exit code.
  - Depends on: E-01
  - Expected outcome: the S-29 property is guarded end to end on both hosts.
  - Execution state: performed

- [x] E-03 Add a test asserting, for each host via `subTest`, that a `failed-safely` terminal item makes `run_queue` return nonzero and the reloaded `state.json` item status is `failed-safely` (the sibling `test_a_queue_with_a_non_success_terminal_item_exits_nonzero` deleted in the same commit).
  - Depends on: E-01
  - Expected outcome: a plain failure is also never reported as a clean run, on both hosts.
  - Execution state: performed

## Project conventions discovered (Step 0)

- P16 / AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": restored coverage must call the code and assert on outputs. The deleted test ALSO asserted the literal contents of `module.SUCCESS_STATES` and `module.EXECUTION_SUCCESS_STATES`; that half is a constant pin and is NOT restored (and is now false anyway: `runner_shared.EXECUTION_SUCCESS_STATES = {"executed"}` after `1f7xno`). Only the `run_queue` return-value half is restored.
- Both hosts' `run_queue` delegate their return value to `runner_shared.run_exit_code` (comment "mh60nd/q32qeg: wire the exit code to spec 25kzda 5.6's run aggregate via `runner_shared.run_exit_code`" in each host). `tests/test_run_exit_aggregate.py` already covers `run_exit_code` directly but never drives `run_queue`; it is the natural home, so it is the only Scope-Path.
- `tests/test_orchestrator_retirement.py::DispatchRunCase.drive` is the established pattern for stubbing `execute_item` and calling `module.run_queue(run_dir, retry_incomplete=False)`.
- Suite runs bare: `python3 -m pytest`; narrowed runs use `python3 -m pytest -o addopts="" <file>` (repo-local development contract).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The guard was deleted in `19313eed7` ("test: trim test suite from 9,136 to under 2,000 tests"). | `git show 19313eed^:tests/test_rununify_run_queue.py` contains `class TheExitCodeReflectsTheRealOutcome(RunQueueCase)` with `test_a_fully_executed_queue_exits_zero`, `test_a_queue_with_a_non_success_terminal_item_exits_nonzero`, and `test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES`. |
| F-2 | yuhl6o recorded S-29 as RETIRE-UNGUARDED, Removed-by `19313eed`. | `.aw/records/plans/executed/20261011-iosmvn-01-yuhl6o-...ipd.md`, E-02 disposition row S-29. |
| F-3 | No live test drives `run_queue` and asserts its exit code for a `substantially-complete` item. | Re-derived at review: `grep -rl substantially-complete tests` matches about 30 files and several also call `run_queue(` (`test_finalize_sendback.py`, `test_reaskscore_composed.py`, `test_runner_shared.py`, `test_oc_runipd.py`, `test_agy_runipd_cli.py`, `test_orchestrator_retirement.py`, `test_typed_queue_entries.py`, `test_action_table_runner_parity.py`), but none asserts `run_queue`'s return value for a `substantially-complete` item: they either discard the return value, drive resume/integration paths, or assert the exit predicate directly (`runner_stop.deliberate_stop_exit_code` in `test_typed_queue_entries.py` and `test_action_table_runner_parity.py`, `test_finalize_sendback.py::test_the_exit_code_is_UNCHANGED_and_was_never_zero`). |
| F-4 | The property holds today on both hosts, so the tests will pass against current code. | Throwaway Step 0 probe (stubbed `execute_item`, real `run_queue`) printed: `oc_runipd executed 0`, `oc_runipd substantially-complete 1`, `oc_runipd failed-safely 1`, `agy_runipd executed 0`, `agy_runipd substantially-complete 1`, `agy_runipd failed-safely 1`. |

## Proposed changes (ordered, validatable)

1. E-01: dual-host harness plus the `executed` -> 0 control.
2. E-02: `substantially-complete` -> nonzero on both hosts.
3. E-03: `failed-safely` -> nonzero on both hosts.

## Deferred / out of scope (with reason)

- Asserting the literal membership of `SUCCESS_STATES` / `EXECUTION_SUCCESS_STATES`: a constant pin, prohibited by P16 and named as non-restorable by the backlog item.
  - Carrier-Declined: P16 forbids this pin; it will not be restored, so no obligation remains.
- Pinning the specific nonzero value (for example 1): the exit vocabulary is owned by `run_evidence._CLASSIFICATION_EXITS` and already tested in this file; the property is only "nonzero".
  - Carrier-Declined: deliberate non-goal; the exit vocabulary is already covered in this file, so no obligation remains.

## Scope check

- Over-scope: none.
- Under-scope: none; the backlog item names one property (exit code nonzero on `substantially-complete`), asserted on both hosts by E-02, with E-01 as the non-vacuity control and E-03 restoring the sibling deleted case at the same site.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_run_exit_aggregate.py -v` shows each new test passing.
- Mutation check (temporary, never committed): both hosts call `runner_shared.run_exit_code` by module attribute (`oc_runipd.run_queue` and `agy_runipd.run_queue` end in `return runner_shared.run_exit_code(...)`), so make `return 0` the first statement of `runner_shared.run_exit_code` in place, run `python3 -m pytest -o addopts="" tests/test_run_exit_aggregate.py -v`, confirm the E-02 and E-03 tests FAIL (the E-01 control still passes), then `git checkout -- agent_workflows/runner_shared.py` and confirm `git diff --exit-code agent_workflows/runner_shared.py` is empty. Review demonstrated the mechanism with the equivalent `mock.patch.object(runner_shared, "run_exit_code", return_value=0)`: `substantially-complete` and `failed-safely` went from 1 to 0 on both hosts.
- Full suite bare: `python3 -m pytest` passes with no new failures.

## Spec / documentation sync

N/A: test-only change restoring coverage; no spec or user-facing behavior changes.

## Open questions

### OQ-01: Which test file should host the restored coverage?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `tests/test_run_exit_aggregate.py`, which already owns exit-code aggregate coverage for `runner_shared.run_exit_code`; recreating `tests/test_rununify_run_queue.py` would revive a file the suite trim deliberately removed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_run_exit_aggregate.py -v` output showing the E-01 control test PASSED, and the test source excerpt showing the harness calls the real `module.run_queue(run_dir, retry_incomplete=False)` for both `oc_runipd` and `agy_runipd` with only `execute_item` patched.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" tests/test_run_exit_aggregate.py -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- .../venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=3213845463
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/eg6r2t
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 11 items

    tests/test_run_exit_aggregate.py::TestRunExitEquivalenceSweep::test_exhaustive_equivalence_sweep PASSED [  9%]
    tests/test_run_exit_aggregate.py::RunQueueExitCodeReflectsTheRealOutcome::test_a_fully_executed_queue_exits_zero PASSED [ 18%]
    tests/test_run_exit_aggregate.py::RunQueueExitCodeReflectsTheRealOutcome::test_the_exit_code_reads_success_states_not_execution_success_states PASSED [ 27%]
    tests/test_run_exit_aggregate.py::RunQueueExitCodeReflectsTheRealOutcome::test_a_queue_with_a_non_success_terminal_item_exits_nonzero PASSED [ 36%]
    tests/test_run_exit_aggregate.py::TestRunExitAggregate::test_case_b_spec_review_regression_prevented_returns_exit_0 PASSED [ 45%]
    tests/test_run_exit_aggregate.py::TestRunExitAggregate::test_case_a_defect_fixed_human_gate_returns_exit_3 PASSED [ 54%]
    tests/test_run_exit_aggregate.py::TestRunExitAggregate::test_case_c_precedence_gate_over_failure_returns_exit_3 PASSED [ 63%]
    tests/test_run_exit_aggregate.py::TestRunExitAggregate::test_case_e_malformed_entry_is_nonzero_under_both_stopped_arms PASSED [ 72%]
    tests/test_run_exit_aggregate.py::TestRunExitAggregate::test_case_f_nothing_is_mutated PASSED [ 81%]
    tests/test_run_exit_aggregate.py::TestRunExitAggregate::test_case_d2_gated_deliberate_stop_still_exits_0 PASSED [ 90%]
    tests/test_run_exit_aggregate.py::TestRunExitAggregate::test_case_d_deliberate_stop_with_queued_remainder_exits_0 PASSED [100%]

    ============================== 11 passed in 2.97s ==============================
    ```

    Harness calls real `module.run_queue(run_dir, retry_incomplete=False)` for both `oc_runipd` and `agy_runipd` with only `execute_item` patched:
    ```python
    def _drive_run(self, module, terminal_status: str) -> tuple[int, dict]:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        run_dir = root / "run-test"
        run_dir.mkdir(parents=True, exist_ok=True)
        item = {
            "position": 1,
            "id6": "aaa111",
            "setid": "s",
            "action": "execute",
            "kind": "child",
            "status": "queued",
            "dependencies": [],
            "attempts": [],
        }
        state = {
            "schema_version": 1,
            "run_id": "run-test",
            "repo": str(root),
            "created_at": "2026-10-14T00:00:00+00:00",
            "updated_at": "2026-10-14T00:00:00+00:00",
            "selectors": ["synthetic"],
            "options": {},
            "set_sessions": {},
            "queue": [item],
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        def fake_exec(rd, st, it, *a, **kw):
            it["status"] = terminal_status
            module.save_state(rd, st)

        buf = io.StringIO()
        with (
            patch.object(module, "execute_item", side_effect=fake_exec),
            contextlib.redirect_stdout(buf),
            contextlib.redirect_stderr(buf),
        ):
            exit_code = module.run_queue(run_dir, retry_incomplete=False)

        reloaded_state = json.loads(
            (run_dir / "state.json").read_text(encoding="utf-8")
        )
        return exit_code, reloaded_state
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted pytest output showing the `substantially-complete` test PASSED on both host subtests; plus pasted output of the in-place mutation check (first statement of `runner_shared.run_exit_code` made `return 0`) showing that test FAILED; plus pasted empty `git diff --exit-code agent_workflows/runner_shared.py` after the revert and the test passing again.
  - Observed evidence:
    Pytest passing run showing `test_the_exit_code_reads_success_states_not_execution_success_states` PASSED:
    ```
    tests/test_run_exit_aggregate.py::RunQueueExitCodeReflectsTheRealOutcome::test_the_exit_code_reads_success_states_not_execution_success_states PASSED [ 27%]
    ```
    Subtest execution detail (via `python3 -m unittest -v tests/test_run_exit_aggregate.py`):
    ```
    test_the_exit_code_reads_success_states_not_execution_success_states (tests.test_run_exit_aggregate.RunQueueExitCodeReflectsTheRealOutcome.test_the_exit_code_reads_success_states_not_execution_success_states)
    Restored S-29 property (E-02): substantially-complete exits nonzero on both hosts. ... ok
    ```

    In-place mutation check (`runner_shared.run_exit_code` made `return 0` as first statement) showing failure:
    ```
    _ RunQueueExitCodeReflectsTheRealOutcome.test_the_exit_code_reads_success_states_not_execution_success_states _

    self = <tests.test_run_exit_aggregate.RunQueueExitCodeReflectsTheRealOutcome testMethod=test_the_exit_code_reads_success_states_not_execution_success_states>

        def test_the_exit_code_reads_success_states_not_execution_success_states(self):
            """Restored S-29 property (E-02): substantially-complete exits nonzero on both hosts."""
            for host_name, module in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
                with self.subTest(host=host_name):
                    exit_code, state = self._drive_run(module, "substantially-complete")
    >               self.assertNotEqual(
                        exit_code,
                        0,
                        f"{host_name}: substantially-complete is not a completion success for the exit code",
                    )
    E               AssertionError: 0 == 0 : oc_runipd: substantially-complete is not a completion success for the exit code

    tests/test_run_exit_aggregate.py:244: AssertionError
    ```

    Revert and empty diff check:
    ```
    $ git checkout -- agent_workflows/runner_shared.py
    $ git diff --exit-code agent_workflows/runner_shared.py
    (exit code 0, empty diff)
    ```
    Post-revert test run passed:
    ```
    ============================== 11 passed in 2.97s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted pytest output showing the `failed-safely` test PASSED, and the same mutation run as V-02 showing it FAILED under the mutation; plus pasted bare `python3 -m pytest` output with the `N passed` summary and no new failures; plus pasted `git diff` of the new test code showing no `inspect`/`ast` import, no read of any `agent_workflows/*.py` source, and no assertion on the contents of `SUCCESS_STATES`/`EXECUTION_SUCCESS_STATES` (P16).
  - Observed evidence:
    Pytest passing run showing `test_a_queue_with_a_non_success_terminal_item_exits_nonzero` PASSED:
    ```
    tests/test_run_exit_aggregate.py::RunQueueExitCodeReflectsTheRealOutcome::test_a_queue_with_a_non_success_terminal_item_exits_nonzero PASSED [ 36%]
    ```
    Subtest execution detail (via `python3 -m unittest -v tests/test_run_exit_aggregate.py`):
    ```
    test_a_queue_with_a_non_success_terminal_item_exits_nonzero (tests.test_run_exit_aggregate.RunQueueExitCodeReflectsTheRealOutcome.test_a_queue_with_a_non_success_terminal_item_exits_nonzero)
    Restored sibling property (E-03): failed-safely exits nonzero on both hosts. ... ok
    ```

    In-place mutation check failure for `failed-safely`:
    ```
    _ RunQueueExitCodeReflectsTheRealOutcome.test_a_queue_with_a_non_success_terminal_item_exits_nonzero _

    self = <tests.test_run_exit_aggregate.RunQueueExitCodeReflectsTheRealOutcome testMethod=test_a_queue_with_a_non_success_terminal_item_exits_nonzero>

        def test_a_queue_with_a_non_success_terminal_item_exits_nonzero(self):
            """Restored sibling property (E-03): failed-safely exits nonzero on both hosts."""
            for host_name, module in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
                with self.subTest(host=host_name):
                    exit_code, state = self._drive_run(module, "failed-safely")
    >               self.assertNotEqual(exit_code, 0)
    E               AssertionError: 0 == 0

    tests/test_run_exit_aggregate.py:256: AssertionError
    ```

    Bare full pytest suite run (`python3 -m pytest`):
    ```
    bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...
    ........................................................................ [ 10%]
    ........................................................................ [ 20%]
    ........................................................................ [ 30%]
    ......................................................................... [ 41%]
    ........................................................................ [ 51%]
    ........................................................................ [ 61%]
    ........................................................................ [ 71%]
    ........................................................................ [ 82%]
    ........................................................................ [ 92%]
    .....................................................                    [100%]
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    702 passed in 28.95s
    ```

    Git diff of the new test code in `tests/test_run_exit_aggregate.py` demonstrating no `inspect`/`ast` import, no read of `agent_workflows/*.py` source, and no assertion on `SUCCESS_STATES`/`EXECUTION_SUCCESS_STATES`:
    ```diff
    diff --git a/tests/test_run_exit_aggregate.py b/tests/test_run_exit_aggregate.py
    index ba8f556c1..bdd0cb0f4 100644
    --- a/tests/test_run_exit_aggregate.py
    +++ b/tests/test_run_exit_aggregate.py
    @@ -1,9 +1,22 @@
     """Tests for runner_shared.aggregated_run_items and run_exit_code (mh60nd/q32qeg E-05, E-06)."""

    +import contextlib
     import copy
    +import io
    +import json
    +import tempfile
     import unittest
    +from pathlib import Path
    +from unittest.mock import patch

    -from agent_workflows import run_evidence, runner_shared, runner_shutdown, runner_stop
    +from agent_workflows import (
    +    agy_runipd,
    +    oc_runipd,
    +    run_evidence,
    +    runner_shared,
    +    runner_shutdown,
    +    runner_stop,
    +)


     class TestRunExitAggregate(unittest.TestCase):
    @@ -164,3 +177,81 @@ class TestRunExitEquivalenceSweep(unittest.TestCase):
                 all((d[4], d[5]) == (1, 3) for d in diffs),
                 "Every differing combination must be exactly (old, new) == (1, 3)",
             )
    +
    +
    +class RunQueueExitCodeReflectsTheRealOutcome(unittest.TestCase):
    +    """Behavioral tests verifying run_queue exit code reflects terminal item status across hosts (eg6r2t)."""
    +
    +    def _drive_run(self, module, terminal_status: str) -> tuple[int, dict]:
    +        td = tempfile.TemporaryDirectory()
    +        self.addCleanup(td.cleanup)
    +        root = Path(td.name)
    +        run_dir = root / "run-test"
    +        run_dir.mkdir(parents=True, exist_ok=True)
    +        item = {
    +            "position": 1,
    +            "id6": "aaa111",
    +            "setid": "s",
    +            "action": "execute",
    +            "kind": "child",
    +            "status": "queued",
    +            "dependencies": [],
    +            "attempts": [],
    +        }
    +        state = {
    +            "schema_version": 1,
    +            "run_id": "run-test",
    +            "repo": str(root),
    +            "created_at": "2026-10-14T00:00:00+00:00",
    +            "updated_at": "2026-10-14T00:00:00+00:00",
    +            "selectors": ["synthetic"],
    +            "options": {},
    +            "set_sessions": {},
    +            "queue": [item],
    +        }
    +        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    +
    +        def fake_exec(rd, st, it, *a, **kw):
    +            it["status"] = terminal_status
    +            module.save_state(rd, st)
    +
    +        buf = io.StringIO()
    +        with (
    +            patch.object(module, "execute_item", side_effect=fake_exec),
    +            contextlib.redirect_stdout(buf),
    +            contextlib.redirect_stderr(buf),
    +        ):
    +            exit_code = module.run_queue(run_dir, retry_incomplete=False)
    +
    +        reloaded_state = json.loads(
    +            (run_dir / "state.json").read_text(encoding="utf-8")
    +        )
    +        return exit_code, reloaded_state
    +
    +    def test_a_fully_executed_queue_exits_zero(self):
    +        """Control test (E-01): an executed item exits 0 and remains executed on both hosts."""
    +        for host_name, module in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
    +            with self.subTest(host=host_name):
    +                exit_code, state = self._drive_run(module, "executed")
    +                self.assertEqual(exit_code, 0)
    +                self.assertEqual(state["queue"][0]["status"], "executed")
    +
    +    def test_the_exit_code_reads_success_states_not_execution_success_states(self):
    +        """Restored S-29 property (E-02): substantially-complete exits nonzero on both hosts."""
    +        for host_name, module in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
    +            with self.subTest(host=host_name):
    +                exit_code, state = self._drive_run(module, "substantially-complete")
    +                self.assertNotEqual(
    +                    exit_code,
    +                    0,
    +                    f"{host_name}: substantially-complete is not a completion success for the exit code",
    +                )
    +                self.assertEqual(state["queue"][0]["status"], "substantially-complete")
    +
    +    def test_a_queue_with_a_non_success_terminal_item_exits_nonzero(self):
    +        """Restored sibling property (E-03): failed-safely exits nonzero on both hosts."""
    +        for host_name, module in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
    +            with self.subTest(host=host_name):
    +                exit_code, state = self._drive_run(module, "failed-safely")
    +                self.assertNotEqual(exit_code, 0)
    +                self.assertEqual(state["queue"][0]["status"], "failed-safely")
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved eg6r2t --by-human`); OQ-01 is resolved and no question blocks. Begin with `aw ipd begin eg6r2t`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. The temporary `agent_workflows/runner_shared.py` mutation is reverted before commit and is never committed. STOP only for a genuinely unsafe condition: `oc_runipd.run_queue` or `agy_runipd.run_queue` no longer returning `runner_shared.run_exit_code(...)`, or a concurrent edit to `tests/test_run_exit_aggregate.py` that cannot be safely combined.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run.

Commits: commit only the Scope-Paths files you changed through `aw commit eg6r2t -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: after every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/` through the tooled lifecycle. Under `aw oc run` / `aw agy run` the RUNNER owns finalize, so do not run it yourself; when executing by hand, run `aw ipd finalize eg6r2t`. Never hand-roll a `git mv`.
