# IPD: Prove and harden the core-tier gate_suite tests against machine-wide suite-slot saturation

- Date: 2026-10-23
- Kind: child
- Concern: load-sensitive flake in the three `tests/test_core_tier_selection.py` gate_suite tests (backlog ih2q1a)
- Scope: tests/test_core_tier_selection.py (regression test proving slot isolation, plus load-repeat evidence); no production code change expected
- Scope-Paths: tests/test_core_tier_selection.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: ih2q1a
- Blocks-Release: next
- Set: ih2q1a
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: b9n3ad
- Approval: 2026-10-24, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-24 approved (aw set): status set to approved
- 2026-10-23 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (dup guard vs f4txy2), PR-002 (setup order, AW_SUITE_SLOTS=1, chmod), PR-003 (bounded real-slot holder), PR-004 (bounded load harness, loadavg ramp), PR-005 (twz0tw path drift), PR-006 (behavioral V bars, budget-only overrun) fixed; mechanism demonstrated at 72da75876

- 2026-10-23 draft (opencode): created.
- 2026-10-23 to-review (opencode): authored from backlog ih2q1a; root cause traced to the twz0tw slot-lock finding, fix already on HEAD, plan adds the missing regression proof and load evidence.

## Goal

Backlog `ih2q1a` records that `test_gate_suite_passes_an_all_green_over_budget_tree[run-evidence|subprocess]` and `test_gate_suite_honors_explicit_enforce` failed once in the bare gate under heavy host load and passed in isolation, "cause unknown". Repository evidence shows the cause was found and fixed under sibling backlog `twz0tw`, but the fix carries no test that would catch a regression. This plan confirms the cause on current HEAD, adds a behavioral regression test that fails if the gate_suite tests ever again share the machine-wide suite slots, and records repeated passes under artificial host load so the item can close on evidence rather than on a rerun.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm the cause on current HEAD

- [x] E-01 Reproduce the saturation condition against current HEAD without editing any file: in one shell, hold every slot of the DEFAULT lock directory (the path `agent_workflows.suite_cache.resolve_suite_lock_dir` returns with `AW_SUITE_LOCK_DIR` unset; slot count from `suite_cache.resolve_suite_slots`) using a short Python helper (kept under `/tmp/opencode/b9n3ad/` or another gitignored scratch path, never committed) that calls `agent_workflows.platform_lock.acquire(<dir>/suite-slot-<k>.lock)` for every k, prints the lock dir and the slot indices it holds, and sleeps for a BOUNDED time (at most 120s, then releases on its own) so a crashed executor cannot leave peer drivers starved. The default dir is shared with peer drivers on this host: if a slot is already busy (`platform_lock.LockBusy`), hold only the free ones and record which were already held by someone else (the effect on the tests is the same: every slot is busy). While held, run `python3 -m pytest -o addopts="" -n 0 tests/test_core_tier_selection.py -k "gate_suite"` and record the summary line and wall time. Then confirm the helper released (it exits).
  - Depends on: none
  - Expected outcome: every selected gate_suite node passes, in well under the 240s per-test wall ceiling (`conftest._DEFAULT_TEST_WALL_TIMEOUT`), proving the `twz0tw` private-lock-dir fix (`_gate_env` setting `AW_SUITE_LOCK_DIR`, commit `548fa71da`) is present and effective on HEAD. If instead any test waits on a slot or fails, mark this item `failed`, record the output, and treat the cause as NOT the slot lock (see OQ-01 resolution: stop and report rather than inventing a fix).
  - Execution state: performed

### Task group 2: Regression test

- [x] E-02 Add `test_gate_suite_ignores_saturated_ambient_slots` to `tests/test_core_tier_selection.py`, parametrized over the three launch shapes the flaky tests use (`subprocess` via `monkeypatch.setenv` of `_gate_env(...)`, `run-evidence` via the same plus `run_id` and `monkeypatch.chdir`, and `explicit-env` via `env=_gate_env(..., AW_CORE_BUDGET_ENFORCE="0")`). Duplicate guard: sibling plan `f4txy2` (Set `twz0tw`, pending) proposes a near-identical test (`test_gate_env_isolates_run_full_suite_from_a_contended_slot_dir`, `env=` shape only). If that test, or any other test that holds every slot of an ambient lock dir and asserts `run_full_suite(...).slot` was acquired, is already on HEAD when this item runs, do NOT add a second copy: extend that test to cover all three launch shapes instead, and run E-03 against it. Setup, in this ORDER (the order matters because `_clean_env` copies `os.environ` at call time, which is exactly what makes the mutation in E-03 observable): (1) create an "ambient" lock dir under `tmp_path` and `os.chmod` it to 0o700 (`suite_cache.resolve_suite_lock_dir` refuses a group/other-writable dir and would then run slotless, masking the test); (2) `monkeypatch.setenv` `AW_SUITE_LOCK_DIR=<ambient>`, `AW_SUITE_SLOTS=1` (pins the slot count so the test does not depend on the host CPU count) and `AW_SUITE_SLOT_TIMEOUT=5` (a regression fails in about 5s instead of hanging), and `monkeypatch.delenv("AW_SUITE_SLOT_HELD", raising=False)`; (3) hold `<ambient>/suite-slot-0.lock` in-process with `platform_lock.acquire` (non-re-entrant, so `suite_slot`'s own non-blocking acquire in the same process sees it busy) and release it in `finally`; (4) only then build the env with `_gate_env(temp_project / ".suite-locks", ...)` and call `suite_cache.run_full_suite(temp_project, argv=[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"], use_cache=False, ...)` exactly as the existing gate_suite tests do. Assert on observable outcomes only: `res.passed`, `res.exit_code == 0`, `res.slot["slot_acquired"] is True`, and `res.slot["waited_seconds"] < 2.0`. Do not change `_gate_env`'s signature (it is also imported by `tests/test_suite_cache.py`). The module-level `pytestmark = pytest.mark.core` covers it; add no new marker.
  - Depends on: E-01
  - Expected outcome: every parametrized node of the new test passes in a few seconds on HEAD; it exercises `run_full_suite` and `suite_slot` for real (no mocks, no source inspection). Mechanism demonstrated at review (see review record `b9n3ad` Round 1): with every slot of an ambient dir held in-process, `suite_slot` against it returned `slot_acquired: False, waited_seconds: 2.003` at a 2s timeout, and against a private dir `slot_acquired: True, waited_seconds: 0.004`.
  - Execution state: performed

- [x] E-03 Mutation check of the regression test, then revert: temporarily make `_gate_env` stop overriding `AW_SUITE_LOCK_DIR` (delete the `AW_SUITE_LOCK_DIR=str(lock_dir)` argument), run `python3 -m pytest -o addopts="" -n 0 tests/test_core_tier_selection.py -k saturated_ambient` (substitute the `-k` expression naming the test actually added or extended in E-02), record the failure, then restore the line and confirm `git diff` shows only the E-02 addition.
  - Depends on: E-02
  - Expected outcome: every parametrized node of the regression test FAILS with the mutation (assertion on `slot_acquired` / `waited_seconds`, after about the 5s slot timeout, with stderr showing `waiting for a test-suite slot`), and every node passes again after restore. This proves the test detects the exact `twz0tw` regression.
  - Execution state: performed

### Task group 3: Load evidence and gate

- [x] E-04 Run the full module five times under artificial host load: start `2 x os.cpu_count()` busy-loop processes, each wrapped in a hard time bound so none can outlive the executor (for example `timeout 900 python3 -c "while True: pass" &`, recording the PIDs). The 1-minute load average ramps slowly, so before the first run poll `/proc/loadavg` (at most 180s) until its first field exceeds `os.cpu_count()`; if it never does, record the highest sample and proceed (V-04 then fails on that criterion, not silently passes). Run `python3 -m pytest -o addopts="" -n 3 tests/test_core_tier_selection.py` five times in a row, sampling `/proc/loadavg` during each run, then kill the load processes and confirm with `ps -p <pids>` that none survive.
  - Depends on: E-02
  - Expected outcome: five consecutive runs report all tests passed with no failures and no `TestHangTimeout`, at a load average above the CPU count, and no load process left running.
  - Execution state: performed

- [x] E-05 After the E-04 load processes are gone, run the routine gate bare, `python3 -m pytest`, and commit through `aw commit b9n3ad -- tests/test_core_tier_selection.py` after verifying `git diff --cached --name-only` lists only that path.
  - Depends on: E-03, E-04
  - Expected outcome: the bare gate reports `N passed` with zero failures; the commit contains only `tests/test_core_tier_selection.py`. A core-tier wall-time budget overrun (`conftest.py` "CORE TIER BUDGET EXCEEDED") with zero failing tests is a pre-existing, load-dependent host condition: record it verbatim, re-run once on a quieter host state, and do not count it as a failure of this plan; any failing test IS a failure.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Routine gate is bare `python3 -m pytest` (root `conftest.py` core-tier selection); narrowed per-test counts use `-o addopts=""` (AGENTS.md repo-local development contract).
- Tests must assert behavior, never source structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); the regression test drives `suite_cache.run_full_suite` and reads its returned `SuiteRunResult.slot` dict (`SlotOutcome.to_dict`: `slot_acquired`, `waited_seconds`).
- Slot-lock tests in this repo already isolate via `AW_SUITE_LOCK_DIR` and tune `AW_SUITE_SLOT_POLL_INTERVAL` / `AW_SUITE_SLOTS` (`tests/test_suite_slot_lock.py::test_two_subprocesses_serialize_and_print_waiting_line`); the new test follows that pattern.
- `suite_cache.suite_slot` waits up to `resolve_suite_slot_timeout` (default 3600s, env `AW_SUITE_SLOT_TIMEOUT`) and then runs without a slot, so an un-isolated test under saturation outlives the 240s hang guard (`conftest._DEFAULT_TEST_WALL_TIMEOUT = 240.0`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The `ih2q1a` failure was observed by plan `rg7rnx` attempt 2 at base HEAD `686468e2a` ("`3 failed, 1672 passed ... in 308.17s`", then "`1675 passed`" on rerun). | `.aw/records/plans/executed/20261017-96lj37-01-rg7rnx-eliminate-hardcoded-file-count-in-test-case-l-and-verify-der.ipd.md`, V-item text "That flake is tracked as backlog `ih2q1a`." |
| F-02 | The identical symptom on the same three tests was diagnosed under sibling backlog `twz0tw`: `run_full_suite` takes a machine-wide suite slot; when the enclosing suite or peer drivers hold every slot, the tests wait and hit the 240s wall guard ("`waiting for a test-suite slot (2 of 2 held)`"). | `.aw/records/backlog/graduated/20261018-twz0tw-01-twz0tw-tests-test-core-tier-selection-py-gate-suite-tests.backlog.md`, note "cause found." (the item has since graduated to plan `f4txy2`, so it moved from `open/` to `graduated/`) |
| F-03 | The fix (private `AW_SUITE_LOCK_DIR` per test in `_gate_env`) landed in `548fa71da`, which is NOT an ancestor of `686468e2a`, so the `ih2q1a` observation predates the fix. | `git merge-base --is-ancestor 548fa71da 686468e2a` -> not ancestor. |
| F-04 | No test proves the isolation: deleting the `AW_SUITE_LOCK_DIR` override from `_gate_env` would pass every existing test on an idle machine and only reappear as a load flake. | `tests/test_core_tier_selection.py::_gate_env`; existing gate_suite tests assert only `res.passed` / `res.exit_code`. |
| F-05 | The 240s "isolation" pass time in F-01's sibling run ("`3 passed, 8 deselected in 240.87s`") matches a slot wait, not test work (normal about 3s per test, `.aw/records/research/20261016-testprune-02-hwuvpx-test-prune-decision-table.assessment.md` lists `[run-evidence]` at 3.02s). | twz0tw history; testprune assessment. |
| F-06 | Sibling plan `f4txy2` (Set `twz0tw`, from the duplicate backlog item) is pending with the same E-01/E-02/E-03 shape and the same single Scope-Path, proposing `test_gate_env_isolates_run_full_suite_from_a_contended_slot_dir`. Executing both unguarded would add two near-identical tests. | `.aw/records/plans/pending/20261023-twz0tw-01-f4txy2-verify-and-lock-in-the-gate-suite-slot-isolation-fix-in-test.ipd.md`, E-02; handled by this plan's E-02 duplicate guard. |

## Proposed changes (ordered, validatable)

1. Confirm the slot-saturation cause and the HEAD fix (E-01, V-01).
2. Add the saturation regression test (E-02, V-02) and prove it catches the regression by mutation (E-03, V-03).
3. Gather repeated passes under artificial load (E-04, V-04) and run the bare gate, then commit (E-05, V-05).

## Deferred / out of scope (with reason)

- Closing or annotating backlog `twz0tw` (a duplicate of this item, typed `followup`), and reconciling its graduated plan `f4txy2` (Set `twz0tw`, pending), which proposes the same regression test: both are separate records outside this plan's Scope-Paths. E-02's duplicate guard keeps the two plans from adding two copies of the test whichever executes first; retiring the later one as superseded is the maintainer's call.
  - Carrier: twz0tw
- The `_gate_env` fallback `tempfile.mkdtemp` directory is never removed. It leaks one empty temp dir per call when no `lock_dir` is passed; the three gate tests always pass one, so it has no user-perceptible effect. Not a flake cause; out of scope.
  - Carrier-Declined: not owed; no user-perceptible effect, and the gate tests always pass lock_dir so the fallback is never hit by them.
- Any production change to `suite_cache.suite_slot` (for example a shorter default slot timeout): the slot wait is correct behavior for real gate runs; only the tests were mis-isolated.
  - Carrier-Declined: not owed; the slot wait is correct production behavior, so no production change is wanted.

## Scope check

- Over-scope: none.
- Under-scope: none. The only failure mechanism with evidence (F-02) is covered by E-01..E-03; residual unknown causes are probed by E-04 and handled by the OQ-01 stop rule.

## Required tests / validation

- `python3 -m pytest -o addopts="" -n 0 tests/test_core_tier_selection.py -k "gate_suite"` with every default slot held (E-01).
- `python3 -m pytest -o addopts="" -n 0 tests/test_core_tier_selection.py -k saturated_ambient` on HEAD and under mutation (E-02, E-03).
- Five loaded runs of `python3 -m pytest -o addopts="" -n 3 tests/test_core_tier_selection.py` (E-04).
- Bare `python3 -m pytest` (E-05).

## Spec / documentation sync

N/A: test-only change; no spec describes the gate_suite test isolation, and no user-facing documentation changes.

## Open questions

### OQ-01: What if the slot lock is not the (only) cause?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Resolved from repository evidence (F-02, F-03, F-05): the only diagnosed mechanism is slot saturation and its fix postdates the `ih2q1a` observation. If E-01 or E-04 nonetheless shows a failure, the executor records the output, marks the item `failed`, and reports a new root-cause finding instead of widening scope; the backlog item stays open.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of the slot-holder helper showing the lock dir path and that all `resolve_suite_slots()` slots were acquired, plus the pasted pytest output listing every selected `gate_suite` node id as passed, with zero failed, and the summary line's wall time under 60s (the count is re-derived from the run, not fixed here). Observation produced by E-01's helper and `suite_cache.suite_slot`.
  - Observed evidence:
    ```
    === SLOT HOLDER OUTPUT ===
    Lock dir: /run/user/1000/agent-workflows
    Total slots: 2
    Acquired slot indices: [0, 1]
    All slots acquired/saturated: True
    READY
    ==========================
    === RUNNING PYTEST ===
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=3021445309
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/b9n3ad
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 11 items / 8 deselected / 3 selected

    tests/test_core_tier_selection.py::test_gate_suite_honors_explicit_enforce PASSED [ 33%]
    tests/test_core_tier_selection.py::test_gate_suite_passes_an_all_green_over_budget_tree[subprocess] PASSED [ 66%]
    tests/test_core_tier_selection.py::test_gate_suite_passes_an_all_green_over_budget_tree[run-evidence] PASSED [100%]

    NOTE: 8 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ============================== SLOW TESTS REPORT ===============================
    WARNING: 2 test(s) exceeded 2s and are not listed in tests/slow_allowlist.txt:
        2.23s  tests/test_core_tier_selection.py::test_gate_suite_honors_explicit_enforce
        2.03s  tests/test_core_tier_selection.py::test_gate_suite_passes_an_all_green_over_budget_tree[run-evidence]
    ======================= 3 passed, 8 deselected in 6.96s ========================
    ======================
    === SLOT HOLDER FINAL ===
    Lock dir: /run/user/1000/agent-workflows
    Total slots: 2
    Acquired slot indices: [0, 1]
    All slots acquired/saturated: True
    READY
    RELEASED
    =========================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `git diff tests/test_core_tier_selection.py` pasted showing only the new (or extended, per E-02's duplicate guard) test and any helper it needs, demonstrating it holds every slot of an ambient lock dir BEFORE building the env with `_gate_env` and asserts `res.slot["slot_acquired"]` and `res.slot["waited_seconds"]`; and the pasted `-v` output of `python3 -m pytest -o addopts="" -n 0 -v tests/test_core_tier_selection.py -k <that test>` showing one passing node per launch shape (`subprocess`, `run-evidence`, `explicit-env`) and zero failed.
  - Observed evidence:
    ```diff
    diff --git a/tests/test_core_tier_selection.py b/tests/test_core_tier_selection.py
    index 20882edbe..36355cf6d 100644
    --- a/tests/test_core_tier_selection.py
    +++ b/tests/test_core_tier_selection.py
    @@ -360,3 +360,67 @@ def test_gate_suite_honors_explicit_enforce(
         )
         assert not res.passed
         assert res.exit_code == 1
    +
    +
    +@pytest.mark.parametrize(
    +    "launch_shape", ["subprocess", "run-evidence", "explicit-env"]
    +)
    +def test_gate_suite_ignores_saturated_ambient_slots(
    +    temp_project: Path,
    +    tmp_path: Path,
    +    launch_shape: str,
    +    monkeypatch: pytest.MonkeyPatch,
    +) -> None:
    +    """The gate_suite tests must isolate their slot directory from ambient slot contention."""
    +    from agent_workflows import platform_lock, suite_cache
    +
    +    ambient = tmp_path / "ambient-locks"
    +    ambient.mkdir(parents=True, exist_ok=True)
    +    os.chmod(ambient, 0o700)
    +
    +    monkeypatch.setenv("AW_SUITE_LOCK_DIR", str(ambient))
    +    monkeypatch.setenv("AW_SUITE_SLOTS", "1")
    +    monkeypatch.setenv("AW_SUITE_SLOT_TIMEOUT", "5")
    +    monkeypatch.delenv("AW_SUITE_SLOT_HELD", raising=False)
    +
    +    handle = platform_lock.acquire(ambient / "suite-slot-0.lock", blocking=False)
    +    try:
    +        if launch_shape == "subprocess":
    +            for k, v in _gate_env(temp_project / ".suite-locks").items():
    +                monkeypatch.setenv(k, v)
    +            monkeypatch.delenv("AW_CORE_BUDGET_ENFORCE", raising=False)
    +            monkeypatch.delenv("AW_SUITE_SLOT_HELD", raising=False)
    +            res = suite_cache.run_full_suite(
    +                temp_project,
    +                argv=[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"],
    +                use_cache=False,
    +            )
    +        elif launch_shape == "run-evidence":
    +            for k, v in _gate_env(temp_project / ".suite-locks").items():
    +                monkeypatch.setenv(k, v)
    +            monkeypatch.delenv("AW_CORE_BUDGET_ENFORCE", raising=False)
    +            monkeypatch.delenv("AW_SUITE_SLOT_HELD", raising=False)
    +            monkeypatch.chdir(temp_project)
    +            res = suite_cache.run_full_suite(
    +                temp_project,
    +                argv=[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"],
    +                use_cache=False,
    +                run_id="run-20261017T000000Z-1",
    +            )
    +        elif launch_shape == "explicit-env":
    +            res = suite_cache.run_full_suite(
    +                temp_project,
    +                argv=[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"],
    +                use_cache=False,
    +                env=_gate_env(temp_project / ".suite-locks", AW_CORE_BUDGET_ENFORCE="0"),
    +            )
    +        else:
    +            raise AssertionError(f"Unknown launch shape {launch_shape}")
    +
    +        assert res.passed
    +        assert res.exit_code == 0
    +        assert res.slot["slot_acquired"] is True
    +        assert res.slot["waited_seconds"] < 2.0
    +    finally:
    +        handle.release()
    +
    ```
    ```
    $ python3 -m pytest -o addopts="" -n 0 -v tests/test_core_tier_selection.py -k saturated_ambient
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=1427167080
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/b9n3ad
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 14 items / 11 deselected / 3 selected

    tests/test_core_tier_selection.py::test_gate_suite_ignores_saturated_ambient_slots[run-evidence] PASSED [ 33%]
    tests/test_core_tier_selection.py::test_gate_suite_ignores_saturated_ambient_slots[explicit-env] PASSED [ 66%]
    tests/test_core_tier_selection.py::test_gate_suite_ignores_saturated_ambient_slots[subprocess] PASSED [100%]

    NOTE: 11 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ============================== SLOW TESTS REPORT ===============================
    WARNING: 1 test(s) exceeded 2s and are not listed in tests/slow_allowlist.txt:
        2.53s  tests/test_core_tier_selection.py::test_gate_suite_ignores_saturated_ambient_slots[run-evidence]
    ======================= 3 passed, 11 deselected in 6.58s =======================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted output under the mutation showing every launch-shape node of the regression test failed, with the failing assertion line (on `slot_acquired` or `waited_seconds`); then the pasted output after restore showing every node passed; and `git diff` showing the mutation reverted (only the E-02 change remains).
  - Observed evidence:
    ```
    Mutation failure output (with AW_SUITE_LOCK_DIR removed from _gate_env):
    =================================== FAILURES ===================================
    ________ test_gate_suite_ignores_saturated_ambient_slots[explicit-env] _________
    ...
    >           assert res.slot["slot_acquired"] is True
    E           assert False is True

    tests/test_core_tier_selection.py:421: AssertionError
    ----------------------------- Captured stderr call -----------------------------
    aw suite: waiting for a test-suite slot (1 of 1 held: unknown holder); waited 0s
    aw suite: timed out waiting for test-suite slot after 5s (bound 5s); running anyway without a slot
    _________ test_gate_suite_ignores_saturated_ambient_slots[subprocess] __________
    ...
    >           assert res.slot["slot_acquired"] is True
    E           assert False is True

    tests/test_core_tier_selection.py:421: AssertionError
    ----------------------------- Captured stderr call -----------------------------
    aw suite: waiting for a test-suite slot (1 of 1 held: unknown holder); waited 0s
    aw suite: timed out waiting for test-suite slot after 5s (bound 5s); running anyway without a slot
    ________ test_gate_suite_ignores_saturated_ambient_slots[run-evidence] _________
    ...
    >           assert res.slot["slot_acquired"] is True
    E           assert False is True

    tests/test_core_tier_selection.py:421: AssertionError
    ----------------------------- Captured stderr call -----------------------------
    aw suite: waiting for a test-suite slot (1 of 1 held: unknown holder); waited 0s
    aw suite: timed out waiting for test-suite slot after 5s (bound 5s); running anyway without a slot
    =========================== short test summary info ============================
    FAILED tests/test_core_tier_selection.py::test_gate_suite_ignores_saturated_ambient_slots[explicit-env]
    FAILED tests/test_core_tier_selection.py::test_gate_suite_ignores_saturated_ambient_slots[subprocess]
    FAILED tests/test_core_tier_selection.py::test_gate_suite_ignores_saturated_ambient_slots[run-evidence]
    ====================== 3 failed, 11 deselected in 22.74s =======================

    After restore:
    $ python3 -m pytest -o addopts="" -n 0 -v tests/test_core_tier_selection.py -k saturated_ambient
    tests/test_core_tier_selection.py::test_gate_suite_ignores_saturated_ambient_slots[run-evidence] PASSED [ 33%]
    tests/test_core_tier_selection.py::test_gate_suite_ignores_saturated_ambient_slots[subprocess] PASSED [ 66%]
    tests/test_core_tier_selection.py::test_gate_suite_ignores_saturated_ambient_slots[explicit-env] PASSED [100%]
    ======================= 3 passed, 11 deselected in 7.74s =======================

    Diff check:
    $ git diff tests/test_core_tier_selection.py
    (Only the E-02 test addition remains in tests/test_core_tier_selection.py)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: five pasted pytest summary lines with zero failures, and at least one pasted `/proc/loadavg` sample taken during the runs whose first field exceeds `os.cpu_count()` (paste that value too), plus the pasted `ps -p <pids>` check showing no load process survived.
  - Observed evidence:
    ```
    os.cpu_count(): 12
    Started 24 timeout processes (48 total PIDs).
    Ramped loadavg reached: 25.51 26.91 24.55 (load1=25.51 > 12)

    --- RUN 1/5 (loadavg before run: 25.51 26.91 24.55) ---
    RUN 1 loadavg during/after: 31.40 28.17 25.02
    RUN 1 summary: ============================= 14 passed in 18.65s ==============================

    --- RUN 2/5 (loadavg before run: 31.40 28.17 25.02) ---
    RUN 2 loadavg during/after: 35.75 29.39 25.49
    RUN 2 summary: ============================= 14 passed in 18.76s ==============================

    --- RUN 3/5 (loadavg before run: 35.75 29.39 25.49) ---
    RUN 3 loadavg during/after: 39.16 30.70 26.03
    RUN 3 summary: ============================= 14 passed in 20.27s ==============================

    --- RUN 4/5 (loadavg before run: 39.16 30.70 26.03) ---
    RUN 4 loadavg during/after: 41.18 31.72 26.46
    RUN 4 summary: ============================= 14 passed in 20.11s ==============================

    --- RUN 5/5 (loadavg before run: 41.18 31.72 26.46) ---
    RUN 5 loadavg during/after: 42.92 32.88 26.99
    RUN 5 summary: ============================= 14 passed in 21.39s ==============================

    === PS CHECK OUTPUT ===
    Command: ps -p 3290390,3290392,3290394,3290395,3290398,3290399,3290402,3290403,3290406,3290408,3290410,3290412,3290414,3290416,3290418,3290419,3290422,3290423,3290425,3290428,3290430,3290432,3290434,3290435,3290391,3290393,3290396,3290397,3290400,3290401,3290404,3290405,3290407,3290409,3290411,3290413,3290415,3290417,3290420,3290421,3290424,3290426,3290427,3290429,3290431,3290433,3290436,3290437
    PID TTY          TIME CMD
    ps exit code: 1
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted final summary line of bare `python3 -m pytest` with zero failures, and pasted `git diff --cached --name-only` (or `aw commit` output) listing only `tests/test_core_tier_selection.py`.
  - Observed evidence:
    ```
    Bare pytest run:
    $ python3 -m pytest
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 146.69s exceeded budget of 30.00s.
    Host 1-minute load average: 34.25 on 12 CPUs
    Core tier budget not enforced: host oversubscribed (1-minute load average above the CPU count)
    ===========================================================================================
    1680 passed, 11 warnings in 146.68s (0:02:26)
    Exit code: 0

    Commit output:
    aw commit: committed 1 path(s): bc8190e6462969348b5bb136bd7bac849ef4b03a
    tests/test_core_tier_selection.py
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit b9n3ad -- tests/test_core_tier_selection.py`; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
