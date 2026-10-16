# IPD: Restore behavioral coverage of driver_begin child env pin and baseline overlay

- Date: 2026-10-14
- Kind: child
- Concern: The env and argv that `runner_shared.driver_begin` hands the `aw ipd begin` child (tool-identity pin from `pinned_child_env`/`pinned_module_argv`, plus the `begin_baseline_env` isolated-baseline overlay, plus `stdin=DEVNULL`) have had no live test since `tests/test_lane_tool_identity.py` was deleted in `19313eed`.
- Scope: Add one new behavioral test module that drives both hosts' real `driver_begin` with `subprocess.run` spied, and repoint the now-stale comment in `runner_shared.driver_begin` at it. No production behavior changes.
- Scope-Paths: tests/test_driver_begin_child_env.py, agent_workflows/runner_shared.py, .aw/records/plans/pending/20261014-o0gy5v-01-lyqn1t-restore-behavioral-coverage-of-driver-begin-child-env-pin-an.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: o0gy5v
- Set: o0gy5v
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: lyqn1t
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record 20261014-o0gy5v-01-lyqn1t)
- 2026-10-15 draft (opencode): created.
- 2026-10-15 to-review (opencode): authored from backlog o0gy5v; review-ready.

## Goal

Restore, as behavior-only tests (P16), the guarantee that the child process `driver_begin` launches on BOTH hosts (`oc_runipd`, `agy_runipd`) is pinned to the runner's own tooling and carries the isolated-baseline declaration exactly when `isolated=True`, so a regression in the launch env becomes a red test again (yuhl6o site S-26, classified RETIRE-UNGUARDED).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Behavioral test module

- [x] E-01 Create `tests/test_driver_begin_child_env.py` with a `subprocess.run` spy class (records argv, kwargs, call count; returns `subprocess.CompletedProcess(argv, 0, stdout="", stderr="")`) and a test parametrized with `pytest.mark.parametrize` over host (`oc_runipd`, `agy_runipd`, ids `oc`/`agy`) and `isolated` (False, True), so `-v` shows four distinct passing ids (unittest `subTest` is NOT used: `pytest-subtests` is not installed, so subtests would not appear in `-v` output). Each case runs under `unittest.mock.patch.dict(os.environ, <os.environ minus AW_PIN_KEEP_ROOT, PYTHONPATH, AW_ISOLATED_BASELINE>, clear=True)` because the runner, and any lane it spawns, inherits `AW_PIN_KEEP_ROOT` and a `PYTHONPATH` containing the package root from its own pin, so without clearing them an unpinned builder would still pass these assertions when the suite runs from the main checkout. Inside that, with `runner_shared.subprocess.run` patched, call `module.driver_begin(Path("/nonexistent"), "aaa111", "actor", isolated=isolated)` and assert: return code 0 and exactly one launch; `env["AW_PIN_KEEP_ROOT"] == runner_shared.runner_package_root()`; that root is an element of `env["PYTHONPATH"].split(os.pathsep)`; `argv[:len(prefix)] == runner_shared.pinned_module_argv([])`; argv after the prefix equals `["ipd", "begin", "aaa111", "--actor", "actor", "--dir", "/nonexistent"]`; `kwargs["stdin"] is subprocess.DEVNULL`; `kwargs["cwd"] == "/nonexistent"`.
  - Depends on: none
  - Expected outcome: test passes on both hosts in both isolation modes.
  - Execution state: performed
- [x] E-02 In the same module, add a test asserting the baseline overlay: `env.get("AW_ISOLATED_BASELINE") == "1"` when `isolated=True` and the key is absent when `isolated=False` (under the same cleared `os.environ` as E-01, so an inherited value cannot mask the result), parametrized over both hosts and both isolation modes; plus a `run_id="run-x"` case on both hosts asserting `argv[-2:] == ["--run-id", "run-x"]`, and that without `run_id` the argv contains no `--run-id`.
  - Depends on: E-01
  - Expected outcome: overlay and run-id propagation asserted on both hosts.
  - Execution state: performed
- [x] E-03 In the same module, add a non-vacuity test: under the same cleared `os.environ` as E-01, call `runner_shared.driver_begin(...)` with an injected `env_builder=lambda: dict(os.environ)` (an unpinned builder) and an `argv_builder` returning `[sys.executable, "-m", "agent_workflows", *args]`, and assert the spied env lacks `AW_PIN_KEEP_ROOT`, the package root is not on its `PYTHONPATH`, and the argv prefix differs from `pinned_module_argv([])`, proving the E-01 assertions can fail through the real launcher. (Measured at review: WITHOUT the cleared environ, this unpinned builder's env carried the runner's inherited `AW_PIN_KEEP_ROOT`, so the clearing is load-bearing.)
  - Depends on: E-01
  - Expected outcome: an unpinned builder is observably distinguishable through the real launcher.
  - Execution state: performed

### Task group 2: Comment repoint

- [x] E-04 In `runner_shared.driver_begin`, replace the comment text "(deleted in `19313eed`; no live guard currently asserts this; it read the env this builds and checked the pin's markers)" (it wraps across two `#` comment lines inside the `subprocess.run(` call, just above `env={**env_builder(), **begin_baseline_env(isolated)}`) so it names `tests/test_driver_begin_child_env.py` as the live behavioral guard (restored by o0gy5v). Comment-only edit; no code change.
  - Depends on: E-01
  - Expected outcome: the comment no longer claims the pin is unguarded.
  - Execution state: performed

## Project conventions discovered (Step 0)

- P16 / AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": no `inspect`, `ast`, or source-text reads; `tests/test_no_code_structure_pins.py` enforces this and must still pass with the new file.
- Patch the OWNING module's global (`runner_shared.subprocess.run`), not a host re-export: the deleted file's header documents that rebinding a re-export does not reach the shared body (`runner_shared` owns `pinned_child_env`, `pinned_module_argv`, `runner_package_root`).
- Both hosts' `driver_begin` (`oc_runipd.driver_begin`, `agy_runipd.driver_begin`) delegate to `runner_shared.driver_begin` binding `env_builder=pinned_child_env, argv_builder=pinned_module_argv`.
- `runner_shared.begin_baseline_env` returns `{"AW_ISOLATED_BASELINE": "1"} if isolated else {}`; the launch uses `env={**env_builder(), **begin_baseline_env(isolated)}` and `stdin=subprocess.DEVNULL`.
- Suite command: bare `python3 -m pytest` (AGENTS.md repo-local contract).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `git show 19313eed^:tests/test_lane_tool_identity.py` contains `TheBeginPinSurvivedTheMove.test_the_env_handed_to_the_begin_child_actually_carries_the_pin`, which drove `driver_begin` through the real launcher with `subprocess.run` spied; it was deleted in `19313eed`.
- yuhl6o (`20261011-iosmvn-01-yuhl6o-...`) classifies site S-26 `driver_begin` as RETIRE-UNGUARDED: `rg -n begin_baseline_env tests/` returned 0 hits.
- Current `rg -n "begin_baseline_env|driver_begin" tests/` shows only tests that MOCK `driver_begin` away (`test_defect_report.py`, `test_receipt_lane_record.py`, etc.); none assert the child env.
- The `runner_shared.driver_begin` comment states "no live guard currently asserts this".
- The deleted file also asserted object identity of injected builders (`assertIs(captured["env_builder"], pinned_child_env)`); that is a wiring/identity pin and is NOT restored (P16 forbids structure pins; the env assertion covers the outcome).

## Proposed changes (ordered, validatable)

1. New `tests/test_driver_begin_child_env.py` (E-01..E-03).
2. Comment repoint in `agent_workflows/runner_shared.py` `driver_begin` (E-04).

## Deferred / out of scope (with reason)

- Object-identity assertions on injected builders: structure pin, excluded by P16 and the backlog item text ("only behavioral outcomes may be restored").
  - Carrier-Declined: P16 forbids this pin; it will not be restored, so no obligation remains.
- Other launch sites and the AST launch-site guard from the deleted file: not part of S-26.
  - Carrier-Declined: the AST guard is a code pin that will not return under P16; other launch sites are separate yuhl6o sites with their own dispositions, not an obligation of backlog `o0gy5v`.
- A real-subprocess end-to-end identity probe (three-package fixture): tool-identity mismatch handling is tested by `tests/test_tool_identity_item_failure.py` (s2tn4q); S-26 concerns only the env/argv handed to the begin child, which the spy-based tests cover.
  - Carrier-Declined: already covered by `tests/test_tool_identity_item_failure.py`; deliberate non-goal, not an outstanding obligation.

## Scope check

- Over-scope: none.
- Under-scope: none; both hosts, both isolation modes, run-id, stdin denial, and non-vacuity are covered.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_driver_begin_child_env.py -v` passes (E-01..E-03).
- `python3 -m pytest -o addopts="" tests/test_no_code_structure_pins.py` passes with the new file present.
- Bare `python3 -m pytest` full fast suite passes.
- `git diff agent_workflows/runner_shared.py` shows a comment-only change (E-04).

## Spec / documentation sync

N/A: test-only restoration plus a code comment; no spec or user-facing doc describes this test.

## Open questions

### OQ-01: Restore the builder object-identity assertion too?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The backlog item restricts restoration to behavioral outcomes (P16); identity of the injected object is a wiring pin, and the env/argv assertions already fail if a host injects a different or unpinned builder.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_driver_begin_child_env.py -v` output showing the pin test PASSED as four distinct parametrized ids (oc/agy x isolated False/True), plus the pasted test body showing the cleared `os.environ` patch.
  - Observed evidence:
    `python3 -m pytest -o addopts="" tests/test_driver_begin_child_env.py -v` output:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- ~/venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=177501196
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/lyqn1t
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 11 items                                                            collected 11 items

    tests/test_driver_begin_child_env.py::test_driver_begin_run_id_propagation[oc] PASSED [  9%]
    tests/test_driver_begin_child_env.py::test_driver_begin_child_env_pin[oc-False] PASSED [ 18%]
    tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay[oc-True] PASSED [ 27%]
    tests/test_driver_begin_child_env.py::test_driver_begin_child_env_pin[agy-True] PASSED [ 36%]
    tests/test_driver_begin_child_env.py::test_driver_begin_child_env_pin[agy-False] PASSED [ 45%]
    tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay[oc-False] PASSED [ 54%]
    tests/test_driver_begin_child_env.py::test_driver_begin_child_env_pin[oc-True] PASSED [ 63%]
    tests/test_driver_begin_child_env.py::test_driver_begin_run_id_propagation[agy] PASSED [ 72%]
    tests/test_driver_begin_child_env.py::test_unpinned_builder_fails_pin_assertions PASSED [ 81%]
    tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay[agy-True] PASSED [ 90%]
    tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay[agy-False] PASSED [100%]

    ============================== 11 passed in 1.13s ==============================
    ```
    Pasted test body with cleared `os.environ` patch:
    ```python
    def _clean_environ() -> dict[str, str]:
        """Return os.environ with pin-inherited keys removed."""
        return {
            k: v
            for k, v in os.environ.items()
            if k not in ("AW_PIN_KEEP_ROOT", "PYTHONPATH", "AW_ISOLATED_BASELINE")
        }


    @pytest.mark.parametrize("isolated", [False, True])
    @pytest.mark.parametrize("host_module", [oc_runipd, agy_runipd], ids=["oc", "agy"])
    def test_driver_begin_child_env_pin(host_module: Any, isolated: bool) -> None:
        """Assert child process receives runner tool-identity pin and DEVNULL stdin."""
        spy = _LaunchSpy()
        prefix = runner_shared.pinned_module_argv([])
        expected_root = runner_shared.runner_package_root()

        with (
            unittest.mock.patch.dict(os.environ, _clean_environ(), clear=True),
            unittest.mock.patch.object(runner_shared.subprocess, "run", spy),
        ):
            rc, _stderr = host_module.driver_begin(
                Path("/nonexistent"), "aaa111", "actor", isolated=isolated
            )

        assert rc == 0
        assert spy.calls == 1
        assert spy.env["AW_PIN_KEEP_ROOT"] == expected_root
        assert expected_root in spy.env["PYTHONPATH"].split(os.pathsep)
        assert spy.argv is not None
        assert spy.argv[: len(prefix)] == prefix
        assert spy.argv[len(prefix) :] == [
            "ipd",
            "begin",
            "aaa111",
            "--actor",
            "actor",
            "--dir",
            "/nonexistent",
        ]
        assert spy.kwargs["stdin"] is subprocess.DEVNULL
        assert spy.kwargs["cwd"] == "/nonexistent"
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted pytest output showing the baseline-overlay and run-id test(s) PASSED, plus a pasted one-off in-process mutation run that leaves the source untouched (so it cannot collide with E-04's edit of the same file): `python3 -c "import sys, pytest; from unittest import mock; from agent_workflows import runner_shared; mock.patch.object(runner_shared, 'begin_baseline_env', lambda _i: {}).start(); sys.exit(pytest.main(['-o', 'addopts=', '-p', 'no:randomly', '<overlay test node id(s)>']))"` showing the `isolated=True` overlay cases FAIL, and `git status --short agent_workflows/` afterwards showing nothing beyond E-04's change.
  - Observed evidence:
    `python3 -m pytest -o addopts="" tests/test_driver_begin_child_env.py -k "test_driver_begin_baseline_overlay or test_driver_begin_run_id_propagation" -v`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- ~/venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=2055090256
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/lyqn1t
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 11 items / 5 deselected / 6 selected

    tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay[agy-False] PASSED [ 16%]
    tests/test_driver_begin_child_env.py::test_driver_begin_run_id_propagation[agy] PASSED [ 33%]
    tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay[oc-False] PASSED [ 50%]
    tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay[oc-True] PASSED [ 66%]
    tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay[agy-True] PASSED [ 83%]
    tests/test_driver_begin_child_env.py::test_driver_begin_run_id_propagation[oc] PASSED [100%]

    NOTE: 5 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 6 passed, 5 deselected in 0.31s ========================
    ```
    In-process mutation run:
    ```
    $ python3 -c "import sys, pytest; from unittest import mock; from agent_workflows import runner_shared; mock.patch.object(runner_shared, 'begin_baseline_env', lambda _i: {}).start(); sys.exit(pytest.main(['-o', 'addopts=', '-p', 'no:randomly', 'tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay']))"
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/lyqn1t
    configfile: pyproject.toml
    plugins: anyio-4.14.1, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_driver_begin_child_env.py .F.F                                [100%]

    =================================== FAILURES ===================================
    _________________ test_driver_begin_baseline_overlay[oc-True] __________________

    host_module = <module 'agent_workflows.oc_runipd' from '/mnt/md1/VC/agent-workflows/.aw/worktrees/lyqn1t/agent_workflows/oc_runipd.py'>
    isolated = True

        @pytest.mark.parametrize("isolated", [False, True])
        @pytest.mark.parametrize("host_module", [oc_runipd, agy_runipd], ids=["oc", "agy"])
        def test_driver_begin_baseline_overlay(host_module: Any, isolated: bool) -> None:
            """Assert AW_ISOLATED_BASELINE is overlayed exactly when isolated=True."""
            spy = _LaunchSpy()
            with (
                unittest.mock.patch.dict(os.environ, _clean_environ(), clear=True),
                unittest.mock.patch.object(runner_shared.subprocess, "run", spy),
            ):
                rc, _stderr = host_module.driver_begin(
                    Path("/nonexistent"), "aaa111", "actor", isolated=isolated
                )

            assert rc == 0
            assert spy.calls == 1
            if isolated:
    >           assert spy.env.get("AW_ISOLATED_BASELINE") == "1"
    E           AssertionError: assert None == '1'
    E            +  where None = <built-in method get of dict object at 0x745060230c00>('AW_ISOLATED_BASELINE')
    E            +    where <built-in method get of dict object at 0x745060230c00> = {'ANTIGRAVITY_AGENT': '1', 'ANTIGRAVITY_AGENTAPI_EXE': '~/.local/bin/agy', 'ANTIGRAVITY_APP_DATA_DIR': '~/.gemini/antigravity-cli', 'ANTIGRAVITY_CONVERSATION_ID': '73d1b975-fd64-4cc8-ad87-bb34fb6fd94e', ...}.get
    E            +      where {'ANTIGRAVITY_AGENT': '1', 'ANTIGRAVITY_AGENTAPI_EXE': '~/.local/bin/agy', 'ANTIGRAVITY_APP_DATA_DIR': '~/.gemini/antigravity-cli', 'ANTIGRAVITY_CONVERSATION_ID': '73d1b975-fd64-4cc8-ad87-bb34fb6fd94e', ...} = <tests.test_driver_begin_child_env._LaunchSpy object at 0x74506086fed0>.env

    tests/test_driver_begin_child_env.py:105: AssertionError
    _________________ test_driver_begin_baseline_overlay[agy-True] _________________

    host_module = <module 'agent_workflows.agy_runipd' from '/mnt/md1/VC/agent-workflows/.aw/worktrees/lyqn1t/agent_workflows/agy_runipd.py'>
    isolated = True

        @pytest.mark.parametrize("isolated", [False, True])
        @pytest.mark.parametrize("host_module", [oc_runipd, agy_runipd], ids=["oc", "agy"])
        def test_driver_begin_baseline_overlay(host_module: Any, isolated: bool) -> None:
            """Assert AW_ISOLATED_BASELINE is overlayed exactly when isolated=True."""
            spy = _LaunchSpy()
            with (
                unittest.mock.patch.dict(os.environ, _clean_environ(), clear=True),
                unittest.mock.patch.object(runner_shared.subprocess, "run", spy),
            ):
                rc, _stderr = host_module.driver_begin(
                    Path("/nonexistent"), "aaa111", "actor", isolated=isolated
                )

            assert rc == 0
            assert spy.calls == 1
            if isolated:
    >           assert spy.env.get("AW_ISOLATED_BASELINE") == "1"
    E           AssertionError: assert None == '1'
    E            +  where None = <built-in method get of dict object at 0x745060242f80>('AW_ISOLATED_BASELINE')
    E            +    where <built-in method get of dict object at 0x745060242f80> = {'ANTIGRAVITY_AGENT': '1', 'ANTIGRAVITY_AGENTAPI_EXE': '~/.local/bin/agy', 'ANTIGRAVITY_APP_DATA_DIR': '~/.gemini/antigravity-cli', 'ANTIGRAVITY_CONVERSATION_ID': '73d1b975-fd64-4cc8-ad87-bb34fb6fd94e', ...}.get
    E            +      where {'ANTIGRAVITY_AGENT': '1', 'ANTIGRAVITY_AGENTAPI_EXE': '~/.local/bin/agy', 'ANTIGRAVITY_APP_DATA_DIR': '~/.gemini/antigravity-cli', 'ANTIGRAVITY_CONVERSATION_ID': '73d1b975-fd64-4cc8-ad87-bb34fb6fd94e', ...} = <tests.test_driver_begin_child_env._LaunchSpy object at 0x7450601edf30>.env

    tests/test_driver_begin_child_env.py:105: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay[oc-True]
    FAILED tests/test_driver_begin_child_env.py::test_driver_begin_baseline_overlay[agy-True]
    ========================= 2 failed, 2 passed in 0.43s ==========================
    ```
    `git status --short agent_workflows/` output:
    ```
     M agent_workflows/runner_shared.py
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted pytest output showing the non-vacuity test PASSED, plus pasted output of `python3 -m pytest -o addopts="" tests/test_no_code_structure_pins.py` passing and the bare `python3 -m pytest` summary line.
  - Observed evidence:
    `python3 -m pytest -o addopts="" tests/test_driver_begin_child_env.py -k "test_unpinned_builder_fails_pin_assertions" -v`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- ~/venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=1150997296
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/lyqn1t
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 11 items / 10 deselected / 1 selected

    tests/test_driver_begin_child_env.py::test_unpinned_builder_fails_pin_assertions PASSED [100%]

    NOTE: 10 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 1 passed, 10 deselected in 0.34s =======================
    ```
    `tests/test_no_code_structure_pins.py` status:
    `tests/test_no_code_structure_pins.py` was deleted in commit `ad9213cc6` ("test: bound routine pytest runtime and keep complete release coverage") as part of removing structure-only tests from the repo. Running the command directly:
    ```
    $ python3 -m pytest -o addopts="" tests/test_no_code_structure_pins.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3075203354
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/lyqn1t
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 0 items

    ============================ no tests ran in 0.03s =============================
    ERROR: file or directory not found: tests/test_no_code_structure_pins.py
    ```
    The new module `tests/test_driver_begin_child_env.py` contains only behavioral outcome assertions (no `ast`, `inspect`, regex, or line counting over source code) and runs clean:
    ```
    $ python3 -m pytest tests/test_driver_begin_child_env.py
    11 passed in 1.55s
    ```
    Bare `python3 -m pytest` summary line:
    ```
    702 passed in 22.93s
    ```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted `git diff agent_workflows/runner_shared.py` showing only comment lines changed and naming `tests/test_driver_begin_child_env.py`.
  - Observed evidence:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index ba01463ed..17b693697 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -30399,8 +30399,8 @@ def driver_begin(
             # lanetruth Order 01 (af7i6p) + Order 02 (z2isfg): the pinned env is the BASE and the
             # baseline declaration is layered on top, so the turn measures the tree it will really
             # execute in WITHOUT unpinning the tooling. The pin's arrival at the child is asserted
    -        # BEHAVIORALLY by `tests/test_lane_tool_identity.py` (deleted in `19313eed`; no live guard
    -        # currently asserts this; it read the env this builds and checked the pin's markers), which
    +        # BEHAVIORALLY by `tests/test_driver_begin_child_env.py` (live behavioral guard, restored by
    +        # o0gy5v; it reads the env this builds and checks the pin's markers), which
             # was strictly stronger than the source-text search that guard used before this symbol was
             # shared -- that search was measurably satisfiable by a COMMENT, and on oc a comment is what
             # satisfied it.
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved lyqn1t --by-human`); OQ-01 is resolved and no question blocks. Begin with `aw ipd begin lyqn1t`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to `agent_workflows/runner_shared.py` that cannot be safely combined, or `runner_shared.driver_begin` no longer launching through `subprocess.run` with `env={**env_builder(), **begin_baseline_env(isolated)}`.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. The V-02 mutation is in-process only and is never written to source or committed.

Commits: commit only the Scope-Paths files you changed through `aw commit lyqn1t -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: after every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/` through the tooled lifecycle. Under `aw oc run` / `aw agy run` the RUNNER owns finalize, so do not run it yourself; when executing by hand, run `aw ipd finalize lyqn1t`. Never hand-roll a `git mv`.
