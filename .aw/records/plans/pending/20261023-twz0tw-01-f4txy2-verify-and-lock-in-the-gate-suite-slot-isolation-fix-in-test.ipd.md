# IPD: Verify and lock in the gate_suite slot-isolation fix in tests/test_core_tier_selection.py

- Date: 2026-10-23
- Kind: child
- Concern: Three tests in `tests/test_core_tier_selection.py` (`test_gate_suite_passes_an_all_green_over_budget_tree[subprocess|run-evidence]` and `test_gate_suite_honors_explicit_enforce`) failed twice on 2026-10-18 in the bare routine gate under host load. Backlog `twz0tw` records the root cause: `suite_cache.run_full_suite` enters `suite_cache.suite_slot`, which waits (default bound `DEFAULT_AW_SUITE_SLOT_TIMEOUT = 3600.0`) for one of N machine-wide slot locks; when the enclosing suite run or peer drivers held every slot, the wait outlived the conftest per-test wall ceiling (`_DEFAULT_TEST_WALL_TIMEOUT = 240.0`). Commit `548fa71da` ("test(twz0tw): isolate core-tier gate_suite tests from the machine-wide suite slot lock") already points `AW_SUITE_LOCK_DIR` at a per-test private dir via `_gate_env`. What is missing is (a) re-verification on the current tree and (b) a behavioral regression test that would go red if the isolation were lost, since today nothing fails fast when it regresses: the failure only reappears as a 240s hang under real contention.
- Scope: Re-verify the existing fix under simulated full-slot contention; add one behavioral regression test in `tests/test_core_tier_selection.py` that holds every slot of a contended lock dir set in the ambient environment and asserts that `run_full_suite` driven with `_gate_env(...)` acquires a private slot promptly. Test-only; no production change.
- Scope-Paths: tests/test_core_tier_selection.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: twz0tw
- Set: twz0tw
- Order: 1
- Highest E allocated: 03
- Author: OpenCode Claude Opus
- Id: f4txy2

## Workflow history

- 2026-10-23 draft (OpenCode Claude Opus): created.
- 2026-10-23 to-review (OpenCode Claude Opus): authored from backlog twz0tw with findings, checklist, and validation.

## Goal

Confirm the slot-isolation fix already landed for backlog `twz0tw` holds on the current tree, and lock it in with a fast behavioral regression test so a future edit that drops the private lock dir fails in seconds instead of resurfacing as a load-only 240s hang. Non-goals: no change to `suite_cache.suite_slot` semantics, slot counts, or the hang-guard ceiling; no retry/xfail/quarantine marker.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-verify the existing fix

- [ ] E-01 Reproduce the contended condition and confirm the three named tests pass under it. In a scratch script under `/tmp/opencode/f4txy2/` (never committed), resolve the real lock dir with `suite_cache.resolve_suite_lock_dir()` and slot count with `suite_cache.resolve_suite_slots()`, hold every `suite-slot-<k>.lock` with `platform_lock.acquire(path, blocking=False)` in a background process, then run `python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_core_tier_selection.py -k gate_suite -v` while they are held, and release them afterwards. If any real slot is already busy (a peer driver), hold only the free ones and record that. Record the runner output and wall time.
  - Depends on: none
  - Expected outcome: the three gate_suite nodes report `passed` in well under 240s while every real slot is held.
  - Execution state: pending

### Task group 2: Behavioral regression test

- [ ] E-02 Add `test_gate_env_isolates_run_full_suite_from_a_contended_slot_dir` to `tests/test_core_tier_selection.py`. Using `tmp_path` and the existing `temp_project` fixture: create a `contended` lock dir, set it as the ambient `AW_SUITE_LOCK_DIR` with `monkeypatch.setenv`, set ambient `AW_SUITE_SLOTS=1` and `AW_SUITE_SLOT_TIMEOUT=5` (so a regression fails in about 5s rather than hanging), delete `AW_SUITE_SLOT_HELD`, and hold `contended/suite-slot-0.lock` via `platform_lock.held(...)` for the duration of the call. Inside, call `suite_cache.run_full_suite(temp_project, argv=[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"], use_cache=False, env=_gate_env(tmp_path / "private-locks"))`. Assert on observable outputs only: `res.slot["acquired"] is True`, `res.slot["slot_index"] == 0`, `res.slot["waited_seconds"] < 2.0`, and that `res.stderr` (or captured stderr via `capfd`) does not contain `waiting for a test-suite slot`. Use `_gate_env` exactly as the three gate_suite tests do, so the test exercises the same helper they depend on.
  - Depends on: E-01
  - Expected outcome: new test passes in a few seconds on the current tree.
  - Execution state: pending
- [ ] E-03 Prove the new test detects the regression it guards. Temporarily (uncommitted, reverted afterwards) remove the `AW_SUITE_LOCK_DIR=str(lock_dir),` override from `_gate_env`, run the new test, and confirm it fails (slot not acquired / timed-out message), then restore the line and confirm it passes again. `git diff tests/test_core_tier_selection.py` after restoration must show only the E-02 addition.
  - Depends on: E-02
  - Expected outcome: red with the override removed, green with it restored; final diff contains only the new test.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Routine gate is bare `python3 -m pytest`; narrowed per-test counts use `-o addopts=""` (AGENTS.md "Repository development contract").
- No code-pinning tests: the regression test must drive `suite_cache.run_full_suite` and assert on its `SuiteRunResult.slot` dict and stderr, not inspect `_gate_env` source (AGENTS.md P16).
- `platform_lock` is deliberately NOT re-entrant ("NOT RE-ENTRANT, ON PURPOSE" in `agent_workflows/platform_lock.py` module docstring), so a lock held in-process via `platform_lock.held` makes a second non-blocking `acquire` on the same path raise `LockBusy` from within the same process; this lets the test simulate contention without a second process.
- `suite_cache.suite_slot` honors `AW_SUITE_LOCK_DIR` (`AW_SUITE_LOCK_DIR_ENV`), `AW_SUITE_SLOTS` (`resolve_suite_slots`), `AW_SUITE_SLOT_TIMEOUT` (`resolve_suite_slot_timeout`), and short-circuits on `AW_SUITE_SLOT_HELD=1`; `run_full_suite` reads all of these from its `env` argument and returns `slot=slot_outcome.to_dict()`.
- `_gate_env` is also imported by `tests/test_suite_cache.py` (`test_run_full_suite_budget_only_failure_names_budget_in_reason`), so its signature must not change.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Root cause is slot starvation, not timing of the tests themselves. | Backlog `twz0tw` third history note: reproduced with both slots held, log `waiting for a test-suite slot (2 of 2 held)`, then `TestHangTimeout ... exceeded its 240s wall ceiling`. |
| F-2 | Fix already committed. | `git show 548fa71da`; `_gate_env(lock_dir=None, **overrides)` in `tests/test_core_tier_selection.py` sets `AW_SUITE_LOCK_DIR=str(lock_dir)` and pops `AW_SUITE_SLOT_HELD`; all three gate_suite tests pass `temp_project / ".suite-locks"`. Follow-up `d8b534637` ("resolve gate_env signature") touched it again. |
| F-3 | No test guards the fix. A regression would only show as a 240s hang under real contention, which the backlog shows is rare and load-dependent. | `grep -n AW_SUITE_LOCK_DIR tests/test_core_tier_selection.py` hits only `_gate_env`; no test holds slots and asserts isolation. |
| F-4 | The slot wait default bound is 3600s, far above the 240s per-test ceiling, so any unisolated `run_full_suite` call in a test is exposed. | `suite_cache.DEFAULT_AW_SUITE_SLOT_TIMEOUT = 3600.0`; `conftest._DEFAULT_TEST_WALL_TIMEOUT = 240.0`. |

## Proposed changes (ordered, validatable)

1. E-01: re-verify under real full-slot contention (no code change).
2. E-02: add one behavioral regression test in `tests/test_core_tier_selection.py`.
3. E-03: mutation-check that test against removal of the isolation override.

## Deferred / out of scope (with reason)

- `_gate_env(lock_dir=None)` falls back to `tempfile.mkdtemp`, which is never cleaned up. All current callers pass an explicit dir, so this leaks nothing today; changing it is unrelated to the flake.
- Auditing other test modules for unisolated `run_full_suite` calls: outside this backlog item's named tests; file a separate backlog item if E-01 observation suggests one.

## Scope check

- Over-scope: none.
- Under-scope: none. The backlog item names three tests and a cause; the fix exists, and this plan adds verification and a guard. Closing the backlog item is the runner's job after execution.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_core_tier_selection.py -v` passes, including the new test (V-02).
- Contended-slot run of the gate_suite nodes passes well under 240s (V-01).
- Mutation check red/green (V-03).
- Bare routine gate `python3 -m pytest` passes (V-02 evidence includes the summary line).

## Spec / documentation sync

N/A: test-only change; no spec describes `_gate_env` or test-suite slot isolation in tests.

## Open questions

### OQ-01: Should the regression test hold real machine-wide slots instead of a tmp contended dir?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Holding the real `$XDG_RUNTIME_DIR/agent-workflows` slots from inside the suite would starve peer drivers and the enclosing run itself. Setting a tmp contended dir as the AMBIENT `AW_SUITE_LOCK_DIR` reproduces the same condition (every slot `_clean_env` would inherit is busy) hermetically. E-01 covers the real-slot condition once, out of band.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output showing the three `gate_suite` node ids `PASSED` with the summary line and duration, plus the scratch holder's output naming the lock dir and the slot indices it held (observation produced by E-01's holder process plus `suite_cache.suite_slot`).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `git diff tests/test_core_tier_selection.py` showing the new test; pasted output of `python3 -m pytest -o addopts="" tests/test_core_tier_selection.py -v` with every node `PASSED` including `test_gate_env_isolates_run_full_suite_from_a_contended_slot_dir`; pasted summary line of the bare `python3 -m pytest` routine gate.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted failing output of the new test with the override removed (showing the failed assertion on `slot`/`waited`), pasted passing output after restoration, and `git diff --stat` showing only the E-02 addition.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_core_tier_selection.py` via `aw commit f4txy2 -- tests/test_core_tier_selection.py`; never push. Move to `executed/` through the tooled lifecycle only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
