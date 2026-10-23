# IPD: Prove and harden the core-tier gate_suite tests against machine-wide suite-slot saturation

- Date: 2026-10-23
- Kind: child
- Concern: load-sensitive flake in the three `tests/test_core_tier_selection.py` gate_suite tests (backlog ih2q1a)
- Scope: tests/test_core_tier_selection.py (regression test proving slot isolation, plus load-repeat evidence); no production code change expected
- Scope-Paths: tests/test_core_tier_selection.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: ih2q1a
- Blocks-Release: next
- Set: ih2q1a
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: b9n3ad

## Workflow history

- 2026-10-23 draft (opencode): created.
- 2026-10-23 to-review (opencode): authored from backlog ih2q1a; root cause traced to the twz0tw slot-lock finding, fix already on HEAD, plan adds the missing regression proof and load evidence.

## Goal

Backlog `ih2q1a` records that `test_gate_suite_passes_an_all_green_over_budget_tree[run-evidence|subprocess]` and `test_gate_suite_honors_explicit_enforce` failed once in the bare gate under heavy host load and passed in isolation, "cause unknown". Repository evidence shows the cause was found and fixed under sibling backlog `twz0tw`, but the fix carries no test that would catch a regression. This plan confirms the cause on current HEAD, adds a behavioral regression test that fails if the gate_suite tests ever again share the machine-wide suite slots, and records repeated passes under artificial host load so the item can close on evidence rather than on a rerun.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm the cause on current HEAD

- [ ] E-01 Reproduce the saturation condition against current HEAD without editing any file: in one shell, hold every slot of the DEFAULT lock directory (the path `agent_workflows.suite_cache.resolve_suite_lock_dir` returns with `AW_SUITE_LOCK_DIR` unset; slot count from `suite_cache.resolve_suite_slots`) using a short Python helper that calls `agent_workflows.platform_lock.acquire(<dir>/suite-slot-<k>.lock)` for every k and sleeps; while held, run `python3 -m pytest -o addopts="" -n 0 tests/test_core_tier_selection.py -k "gate_suite"` and record the summary line and wall time. Then release the slots.
  - Depends on: none
  - Expected outcome: `3 passed` in well under the 240s per-test wall ceiling (`conftest._DEFAULT_TEST_WALL_TIMEOUT`), proving the `twz0tw` private-lock-dir fix (`_gate_env` setting `AW_SUITE_LOCK_DIR`, commit `548fa71da`) is present and effective on HEAD. If instead any test waits on a slot or fails, mark this item `failed`, record the output, and treat the cause as NOT the slot lock (see OQ-01 resolution: stop and report rather than inventing a fix).
  - Execution state: pending

### Task group 2: Regression test

- [ ] E-02 Add `test_gate_suite_ignores_saturated_ambient_slots` to `tests/test_core_tier_selection.py`, parametrized over the three launch shapes the flaky tests use (`subprocess` via `monkeypatch.setenv` of `_gate_env(...)`, `run-evidence` via the same plus `run_id` and `monkeypatch.chdir`, and `explicit-env` via `env=_gate_env(..., AW_CORE_BUDGET_ENFORCE="0")`). Setup: create an "ambient" lock dir under `tmp_path` with mode 0o700, acquire ALL `suite_cache.resolve_suite_slots()` slots in it in-process with `platform_lock.acquire`, and `monkeypatch.setenv("AW_SUITE_LOCK_DIR", <ambient>)` plus `monkeypatch.setenv("AW_SUITE_SLOT_TIMEOUT", "5")` so a regression fails fast instead of hanging; release the handles in `finally`. Then call `suite_cache.run_full_suite(temp_project, argv=[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"], use_cache=False, ...)` exactly as the existing gate_suite tests do, with the private lock dir from `_gate_env(temp_project / ".suite-locks")`. Assert on observable outcomes only: `res.passed`, `res.exit_code == 0`, `res.slot["slot_acquired"] is True`, and `res.slot["waited_seconds"] < 5.0`. The module-level `pytestmark = pytest.mark.core` covers it; add no new marker.
  - Depends on: E-01
  - Expected outcome: the new test passes in a few seconds per parameter on HEAD; it exercises `run_full_suite` and `suite_slot` for real (no mocks, no source inspection).
  - Execution state: pending

- [ ] E-03 Mutation check of the regression test, then revert: temporarily make `_gate_env` stop overriding `AW_SUITE_LOCK_DIR` (delete the `AW_SUITE_LOCK_DIR=str(lock_dir)` argument), run `python3 -m pytest -o addopts="" -n 0 tests/test_core_tier_selection.py -k saturated_ambient`, record the failure, then restore the line and confirm `git diff` shows only the E-02 addition.
  - Depends on: E-02
  - Expected outcome: all three parameters FAIL with the mutation (assertion on `slot_acquired` / `waited_seconds`, after about the 5s slot timeout), and pass again after restore. This proves the test detects the exact `twz0tw` regression.
  - Execution state: pending

### Task group 3: Load evidence and gate

- [ ] E-04 Run the full module five times under artificial host load: start `2 x os.cpu_count()` busy-loop processes (for example `python3 -c "while True: pass"` in the background, recorded PIDs), run `python3 -m pytest -o addopts="" -n 3 tests/test_core_tier_selection.py` five times in a row, then kill the load processes. Record each summary line and the 1-minute load average sampled during the run (`cat /proc/loadavg`).
  - Depends on: E-02
  - Expected outcome: five consecutive runs report all tests passed with no failures and no `TestHangTimeout`, at a load average above the CPU count.
  - Execution state: pending

- [ ] E-05 Run the routine gate bare, `python3 -m pytest`, and commit through `aw commit b9n3ad -- tests/test_core_tier_selection.py` after verifying `git diff --cached --name-only` lists only that path.
  - Depends on: E-03, E-04
  - Expected outcome: the bare gate reports `N passed` with zero failures; the commit contains only `tests/test_core_tier_selection.py`.
  - Execution state: pending

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
| F-02 | The identical symptom on the same three tests was diagnosed under sibling backlog `twz0tw`: `run_full_suite` takes a machine-wide suite slot; when the enclosing suite or peer drivers hold every slot, the tests wait and hit the 240s wall guard ("`waiting for a test-suite slot (2 of 2 held)`"). | `.aw/records/backlog/open/20261018-twz0tw-01-twz0tw-tests-test-core-tier-selection-py-gate-suite-tests.backlog.md`, note "cause found." |
| F-03 | The fix (private `AW_SUITE_LOCK_DIR` per test in `_gate_env`) landed in `548fa71da`, which is NOT an ancestor of `686468e2a`, so the `ih2q1a` observation predates the fix. | `git merge-base --is-ancestor 548fa71da 686468e2a` -> not ancestor. |
| F-04 | No test proves the isolation: deleting the `AW_SUITE_LOCK_DIR` override from `_gate_env` would pass every existing test on an idle machine and only reappear as a load flake. | `tests/test_core_tier_selection.py::_gate_env`; existing gate_suite tests assert only `res.passed` / `res.exit_code`. |
| F-05 | The 240s "isolation" pass time in F-01's sibling run ("`3 passed, 8 deselected in 240.87s`") matches a slot wait, not test work (normal about 3s per test, `.aw/records/research/20261016-testprune-02-hwuvpx-test-prune-decision-table.assessment.md` lists `[run-evidence]` at 3.02s). | twz0tw history; testprune assessment. |

## Proposed changes (ordered, validatable)

1. Confirm the slot-saturation cause and the HEAD fix (E-01, V-01).
2. Add the saturation regression test (E-02, V-02) and prove it catches the regression by mutation (E-03, V-03).
3. Gather repeated passes under artificial load (E-04, V-04) and run the bare gate, then commit (E-05, V-05).

## Deferred / out of scope (with reason)

- Closing or annotating backlog `twz0tw` (a duplicate of this item, typed `followup`): it is a separate record outside this plan's Scope-Paths; the maintainer can close it citing this plan once executed.
- The `_gate_env` fallback `tempfile.mkdtemp` directory is never removed. It leaks one empty temp dir per call when no `lock_dir` is passed; the three gate tests always pass one, so it has no user-perceptible effect. Not a flake cause; out of scope.
- Any production change to `suite_cache.suite_slot` (for example a shorter default slot timeout): the slot wait is correct behavior for real gate runs; only the tests were mis-isolated.

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

- [ ] V-01 validates E-01
  - Required evidence: pasted output of the slot-holder helper showing the lock dir path and that all `resolve_suite_slots()` slots were acquired, plus the pasted pytest summary line (`3 passed ... in <t>s`) with `<t>` under 60s. Observation produced by E-01's helper and `suite_cache.suite_slot`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff tests/test_core_tier_selection.py` pasted showing only the new test (and any helper it needs), and the pasted summary of `python3 -m pytest -o addopts="" -n 0 tests/test_core_tier_selection.py -k saturated_ambient` reporting `3 passed`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted failing summary (`3 failed`) and the assertion line under the mutation, then the pasted `3 passed` summary after restore, and `git diff` showing the mutation reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: five pasted pytest summary lines with zero failures, and at least one pasted `/proc/loadavg` sample taken during the runs whose first field exceeds `os.cpu_count()` (paste that value too).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted final summary line of bare `python3 -m pytest` with zero failures, and pasted `git diff --cached --name-only` (or `aw commit` output) listing only `tests/test_core_tier_selection.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit b9n3ad -- tests/test_core_tier_selection.py`; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
