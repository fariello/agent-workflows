# IPD: Isolate tests/test_suite_cache.py from the machine-wide suite slot lock

- Date: 2026-10-23
- Kind: child
- Concern: `tests/test_suite_cache.py` drives `suite_cache.run_full_suite` (directly in `test_reproducible_failure_stored_and_not_served_to_seam`, `test_collection_error_and_corrupt_or_expired_records` and `test_runner_seams_cache_hit_miss_and_failure_rerun`; indirectly through the `aw suite` subprocess helper `_run_aw_suite` and the `runner_shared` seams `run_suite_check`, `start_suite_baseline`, `make_integration_validation_runner`) without pointing `AW_SUITE_LOCK_DIR` at a private directory. Every such call enters `suite_cache.suite_slot`, which waits up to `DEFAULT_AW_SUITE_SLOT_TIMEOUT = 3600.0` seconds for one of N slot locks in the machine-wide per-user directory (`$XDG_RUNTIME_DIR/agent-workflows`). When the enclosing suite run or peer drivers hold every slot, a test waits past the conftest per-test wall ceiling (`_DEFAULT_TEST_WALL_TIMEOUT = 240.0`) and fails with `TestHangTimeout`. This is the same starvation fixed for `tests/test_core_tier_selection.py` in commit `548fa71da` (backlog `twz0tw`); the two budget tests at the end of this file already borrow that fix via `_gate_env`, the rest do not.
- Scope: Add one module-level autouse fixture in `tests/test_suite_cache.py` that sets `AW_SUITE_LOCK_DIR` to a per-test private directory under `tmp_path`, so every in-process call, every `_fixture_env()` copy and every `aw suite` subprocess in the module resolves a private slot directory; add one behavioral regression test that holds every slot of a contended ambient lock directory and asserts a `run_full_suite` call driven the way this module's tests drive it acquires a private slot promptly; mutation-check that test. Test-only; no production change, no change to slot semantics, slot counts, timeouts or the hang-guard ceiling.
- Scope-Paths: tests/test_suite_cache.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: jycfw3
- Set: jycfw3
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: zyy2yg
- Approval: 2026-10-24, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-24 approved (aw set): status set to approved
- 2026-10-24 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (E-02 serial argv, no 12-worker child), PR-002 (re-derived test-count bars), PR-003 (F-1 call-site count), PR-004 (V-03 diff bar, holder early stop) fixed; mechanism demonstrated at e9e14c28d

- 2026-10-23 draft (opencode): created.
- 2026-10-23 to-review (opencode): authored from backlog `jycfw3` (carried from plan `f4txy2` deferred row 2) with findings measured at HEAD `3969bf382`, checklist, and validation.

## Goal

Make every test in `tests/test_suite_cache.py` independent of the machine-wide test-suite slot pool, so host load or peer drivers can no longer push one of them past the 240s per-test ceiling, and lock that in with a fast behavioral test that goes red if the isolation is lost. Non-goals: no change to `agent_workflows/suite_cache.py`, no retry/xfail/quarantine marker, no change to `tests/test_core_tier_selection.py` (owned by plans `f4txy2` and `b9n3ad`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Isolate the module

- [ ] E-01 Add a module-level `@pytest.fixture(autouse=True)` named `_private_suite_lock_dir(tmp_path, monkeypatch)` near the top of `tests/test_suite_cache.py` (after `REPO_ROOT`) that calls `monkeypatch.setenv("AW_SUITE_LOCK_DIR", str(tmp_path / ".suite-locks"))` and yields that path. Carry a short comment naming the cause (machine-wide slot wait vs the 240s hang guard, backlog `jycfw3`, same fix as `twz0tw` / `548fa71da`). Do NOT touch `AW_SUITE_SLOT_HELD` (keep current nested-guard behavior), and do NOT change `_fixture_env`, `_run_aw_suite`, or any test body: because the fixture mutates `os.environ` before each test body runs, `_fixture_env()` (which copies `os.environ`), the `aw suite` subprocesses (which inherit it), the `mock.patch.dict(os.environ, _fixture_env())` seam block, and the env-less `run_full_suite` calls in `test_runner_seams_cache_hit_miss_and_failure_rerun` all resolve the private directory. `AW_SUITE_LOCK_DIR` is not in `suite_cache.SUITE_KEY_ENV_VARS`, so cache keys and every digest assertion are unaffected. The two budget tests that pass an explicit `_gate_env(tmp_path / ".suite-locks", ...)` keep working (explicit env wins, same path).
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_suite_cache.py -n 4` reports zero failed and zero errors, with the passed count equal to the file's collected count re-derived at execution (`--collect-only -q`; 17 at authoring, F-5, context only), and only the fixture added to the diff.
  - Execution state: pending

### Task group 2: Behavioral regression test

- [ ] E-02 Add `test_module_suite_runs_ignore_a_contended_ambient_slot_dir(tmp_path, monkeypatch, capfd)` to `tests/test_suite_cache.py`. Set up contention in the AMBIENT environment that the fixture is supposed to shadow: create `tmp_path / "xdg"` and `tmp_path / "xdg" / "agent-workflows"` with mode `0o700`, `monkeypatch.setenv("XDG_RUNTIME_DIR", <xdg>)`, `monkeypatch.setenv("AW_SUITE_SLOTS", "1")`, `monkeypatch.setenv("AW_SUITE_SLOT_TIMEOUT", "5")` (a regression then fails in about 5s instead of hanging), and `monkeypatch.delenv("AW_SUITE_SLOT_HELD", raising=False)` (otherwise `suite_slot` short-circuits and nothing is tested). Build a fixture repo with `_init_fixture_repo(tmp_path / "repo")`, then, while holding `<xdg>/agent-workflows/suite-slot-0.lock` via `platform_lock.held(...)`, call `suite_cache.run_full_suite(repo, argv=[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"], use_cache=False, stream=False, env=_fixture_env())` (explicit serial argv, the same shape the module's two budget tests use: with the default `SUITE_CHECK_ARGV`, `build_suite_child_env` appends `-n <workers>` and the child spawned 12 xdist workers on the review host for a one-test fixture repo; the slot path under test is identical either way). Assert on observable outputs only: `res.passed is True`, `res.slot["acquired"] is True`, `res.slot["slot_index"] == 0`, `res.slot["waited_seconds"] < 2.0`, and that `capfd.readouterr().err` (the PARENT process's stderr, where `suite_slot` prints) does not contain `waiting for a test-suite slot`. Do NOT assert on `res.stderr` (child pytest's stderr; vacuous, per plan `f4txy2` review PR-001). Do NOT inspect the fixture or `os.environ["AW_SUITE_LOCK_DIR"]`; the assertion is on slot acquisition behavior.
  - Depends on: E-01
  - Expected outcome: the new test passes in a few seconds. Mechanism measured at authoring (F-4): with the contended ambient slot held in-process, a `suite_slot` call resolving the ambient dir returned `slot_acquired: False, waited_seconds: 2.002` at a 2s bound; with a private `AW_SUITE_LOCK_DIR` it returned `slot_acquired: True, slot_index: 0, waited_seconds: 0.001`. Re-demonstrated at review (F-8) with this exact test shape: green in 1.25s with isolation, red without it.
  - Execution state: pending
- [ ] E-03 Prove the new test detects the regression it guards. Temporarily (uncommitted, reverted afterwards) remove the `monkeypatch.setenv("AW_SUITE_LOCK_DIR", ...)` line from the E-01 fixture (leave the fixture yielding), run the E-02 test with `AW_SUITE_LOCK_DIR` cleared from the invoking shell (`env -u AW_SUITE_LOCK_DIR python3 -m pytest -o addopts="" -p no:cacheprovider "tests/test_suite_cache.py::test_module_suite_runs_ignore_a_contended_ambient_slot_dir"`) and confirm it FAILS on the slot assertion after about the 5s slot timeout; restore the line and confirm it passes. `git diff tests/test_suite_cache.py` after restoration must show only the E-01 fixture and the E-02 test.
  - Depends on: E-02
  - Expected outcome: red with the isolation removed (at review the first failing assertion was `res.slot["acquired"] is True`, with `waited_seconds` about 5.0 and the waiting line present in parent stderr, F-8), green with it restored; final diff contains only the E-01 and E-02 additions.
  - Execution state: pending

### Task group 3: Validation runs

- [ ] E-04 Run the validation set: `tests/test_suite_cache.py` in full three times (`python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_suite_cache.py -n 4 -p randomly --randomly-seed=<n>` for seeds 1, 2, 3); the same file once while every REAL machine-wide slot is held by a bounded background holder (scratch script under `/tmp/opencode/zyy2yg/`, never committed, that resolves the real dir with `suite_cache.resolve_suite_lock_dir()` and count with `suite_cache.resolve_suite_slots()`, holds every free `suite-slot-<k>.lock` via `platform_lock.acquire(path, blocking=False)`, prints the dir and held indices, and releases on its own after at most 180s so a crashed executor cannot starve peer drivers; terminate it as soon as the contended run finishes rather than waiting out the bound; if a slot is already held by a peer, hold only the free ones and record that); the bare routine gate `python3 -m pytest`; and `aw sanitize --agent`.
  - Depends on: E-03
  - Expected outcome: every run reports zero failures and zero errors; the contended run completes well under 240s per test with no `waiting for a test-suite slot` line attributable to this module; sanitizer exit 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Routine gate is bare `python3 -m pytest` (core tier only); narrowed runs clear defaults with `-o addopts=""`; do not add `-q` or `-p no:randomly` (AGENTS.md "Repository development contract"). `tests/test_suite_cache.py` carries no `core` marker (`-m core` collects 0 of 17 at authoring), so its tests run in explicit-path runs and the thorough tier (`make test-all` / `aw suite --thorough`), which is where the starvation bites.
- No code-pinning tests (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): the regression test drives `suite_cache.run_full_suite` and asserts on `SuiteRunResult.slot` and parent stderr.
- `platform_lock` is deliberately NOT re-entrant, so an in-process `platform_lock.held(path)` makes `suite_slot`'s non-blocking `platform_lock.acquire` on the same path raise `LockBusy`; contention is simulated without a second process (pattern from plan `f4txy2` E-02).
- `suite_cache.resolve_suite_lock_dir` precedence: `AW_SUITE_LOCK_DIR`, then `$XDG_RUNTIME_DIR/agent-workflows`, then `<tempdir>/agent-workflows-<uid>`; it creates a missing dir with mode `0o700` and refuses a dir writable by group/other.
- `suite_cache.suite_slot` short-circuits (`acquired=True, slot_index=None`) when `AW_SUITE_SLOT_HELD=1`, which `build_suite_child_env` sets for every suite it launches; the regression test therefore deletes it and asserts `slot_index == 0`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Unisolated `run_full_suite` reach in this module: direct calls in `test_reproducible_failure_stored_and_not_served_to_seam` (`seam_res = suite_cache.run_full_suite(`), `test_collection_error_and_corrupt_or_expired_records` (`run_res = suite_cache.run_full_suite(repo, env=env)`), and `test_runner_seams_cache_hit_miss_and_failure_rerun` (`adv_fail = ...`, `adv_fail_hit = ...`, env-less, reading `os.environ`); plus 15 `_run_aw_suite(` subprocess call sites (each `aw suite` reaches `cli` `_sc.run_full_suite(`) and the three `runner_shared` seams. None sets `AW_SUITE_LOCK_DIR`. | `grep -n "run_full_suite\|_run_aw_suite(\|AW_SUITE_LOCK_DIR" tests/test_suite_cache.py` at `3969bf382`; `_fixture_env` copies `os.environ` and sets only `AW_NO_REEXEC`, `PYTHONPATH` |
| F-2 | The two budget tests already isolate via `_gate_env(tmp_path / ".suite-locks", ...)` imported from `tests/test_core_tier_selection.py`. | `test_run_full_suite_budget_only_failure_names_budget_in_reason`, `test_run_full_suite_budget_control_with_failing_test` |
| F-3 | Slot wait bound (3600s) far exceeds the per-test ceiling (240s), so any unisolated call is exposed whenever every machine-wide slot is held. Ambient at authoring: real dir `/run/user/<uid>/agent-workflows`, 2 slots, no `AW_SUITE_*` vars set. | `suite_cache.DEFAULT_AW_SUITE_SLOT_TIMEOUT = 3600.0`; `conftest._DEFAULT_TEST_WALL_TIMEOUT = 240.0`; `resolve_suite_lock_dir()`/`resolve_suite_slots()` printed in this lane |
| F-4 | Mechanism demonstrated in this lane: holding `<xdg>/agent-workflows/suite-slot-0.lock` in-process with `AW_SUITE_SLOTS=1`, `AW_SUITE_SLOT_TIMEOUT=2`: ambient resolution printed `aw suite: waiting for a test-suite slot (1 of 1 held: unknown holder); waited 0s` then `timed out ... running anyway without a slot`, outcome `{'slot_acquired': False, 'waited_seconds': 2.002, 'slot_index': None}`; with `AW_SUITE_LOCK_DIR=<private>` outcome `{'slot_acquired': True, 'waited_seconds': 0.001, 'slot_index': 0}`. A fresh private dir is created `0o700` and left containing only `suite-slot-0.lock` after release. | inline probe run 2026-10-23 at `3969bf382` |
| F-5 | Baseline: `AW_NO_REEXEC=1 python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_suite_cache.py -q -n 4` -> `17 passed in 72.28s (0:01:12)`. | measured 2026-10-23 in this lane |
| F-6 | `AW_SUITE_LOCK_DIR` is not a cache-key input (`SUITE_KEY_ENV_VARS` = `AW_EXECUTION_ROLE`, `AW_NO_REEXEC`, `FORCE_COLOR`, `NO_COLOR`, `PYTEST_ADDOPTS`, `PYTHONPATH`, `TERM`), so setting it cannot change any digest compared in this module. | `agent_workflows/suite_cache.py` `SUITE_KEY_ENV_VARS` |
| F-7 | No other pending plan declares `tests/test_suite_cache.py` in `- Scope-Paths:` (`f4txy2`, `b9n3ad` declare `tests/test_core_tier_selection.py`; `sbcmke` declares `tests/test_runner_residual_helpers.py` and only names this file as a probe target). | grep of `.aw/records/plans/pending/` |
| F-8 | Review demonstration of E-02/E-03 (scratch test under the gitignored `.aw/state/`, never committed), with the invoking shell's `AW_SUITE_LOCK_DIR` cleared: with the fixture's setenv present, `res.slot` = `{'acquired': True, 'waited_seconds': 0.001, 'slot_index': 0}`, waiting line absent from `capfd` err, `1 passed in 1.25s` (serial argv); with the setenv removed, `{'acquired': False, 'waited_seconds': 5.005, 'slot_index': None}`, waiting line present, `1 failed in 6.17s` on `assert res.slot["acquired"] is True` while `res.passed` stayed True. With the default argv the child reported `created: 12/12 workers` and the test took 2.6-2.9s. | probe run 2026-10-23 in the review lane at `e9e14c28d` |

## Proposed changes (ordered, validatable)

1. E-01: autouse private-lock-dir fixture in `tests/test_suite_cache.py`.
2. E-02: behavioral regression test under simulated ambient contention.
3. E-03: mutation check red/green.
4. E-04: validation runs, including one under real full-slot contention.

## Deferred / out of scope (with reason)

- Auditing test modules other than `tests/test_suite_cache.py` for unisolated `run_full_suite` reach: outside this backlog item, which names this file only; `tests/test_core_tier_selection.py` is covered by `548fa71da` and plans `f4txy2` / `b9n3ad`.
  - Carrier-Declined: the backlog item is scoped to one file; no other unisolated module was identified at authoring, so there is nothing concrete to carry.
- Centralizing the isolation in the root `conftest.py` (a suite-wide autouse fixture): broader blast radius (it would also shadow `tests/test_suite_slot_lock.py`, which deliberately exercises real lock-dir resolution) and not asked for.
  - Carrier-Declined: rejected design option, not deferred work.

## Scope check

- Over-scope: none.
- Under-scope: if the slow-tests report of an E-04 run lists the new E-02 test as unlisted (only core-tier durations are reported, and this module is not core, so this is not expected), add a `tests/slow_allowlist.txt` entry and justify it with `--scope-reason` at finalize; `- Scope-Paths:` is a declaration, not a stop condition.

## Required tests / validation

- `python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_suite_cache.py -n 4 -p randomly --randomly-seed=<n>` for seeds 1, 2, 3: zero failed and zero errors, with the passed count equal to the collected count re-derived at execution and including the E-02 test (V-01, V-04).
- New regression test passes and the mutation check is red then green (V-02, V-03).
- `tests/test_suite_cache.py` passes while every real machine-wide slot is held (V-04).
- Bare routine gate `python3 -m pytest` passes; a core-tier wall-time budget overrun ("CORE TIER BUDGET EXCEEDED") with zero failing tests is a pre-existing load-dependent host condition: record it verbatim, re-run once, and do not count it as a failure of this plan; any failing test IS a failure (V-04).
- `aw sanitize --agent` exits 0 (V-04).

## Spec / documentation sync

N/A: test-only change; no spec or user-facing doc describes test-suite slot isolation in `tests/test_suite_cache.py`. No `.spec.md` is declared in `- Scope-Paths:`.

## Open questions

### OQ-01: Fixture per module, or per-call `env` overrides at the four named call sites?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Module-level autouse fixture. The backlog names four direct call sites, but F-1 shows the same exposure through 16 `aw suite` subprocess calls and the `runner_shared` seams, which take no `env` argument (`run_suite_check` calls `run_full_suite` without `env`, reading `os.environ`). Only an `os.environ`-level override reaches all of them, and `monkeypatch` scopes it to one test.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff tests/test_suite_cache.py` hunk showing the autouse fixture setting `AW_SUITE_LOCK_DIR` under `tmp_path` and no change to `_fixture_env`, `_run_aw_suite` or any existing test body; paste the `--collect-only -q` count line and the pytest summary line of the full-file run (before E-02 is added) showing the passed count equal to that collected count with zero failed and zero errors.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff` hunk of the new test showing ambient `XDG_RUNTIME_DIR`/`AW_SUITE_SLOTS`/`AW_SUITE_SLOT_TIMEOUT` set and `AW_SUITE_SLOT_HELD` deleted before `_fixture_env()` is called, the lock held via `platform_lock.held`, the explicit serial `argv`, and the assertions on `res.slot` and `capfd` (not `res.stderr`); paste `python3 -m pytest -o addopts="" -p no:cacheprovider "tests/test_suite_cache.py::test_module_suite_runs_ignore_a_contended_ambient_slot_dir" -v` output showing `PASSED` with its duration.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the failing output of the new test with the fixture's `setenv` line removed (showing the failed assertion on `slot`/`waited_seconds`, after about 5s), the passing output after restoration, and `git diff --stat` showing no changed path other than `tests/test_suite_cache.py` and this plan file (evidence recording).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `--collect-only -q` count line and the summary line of each seeded full-file run (seeds 1, 2, 3; passed equals collected, including the E-02 test, with 0 failed and 0 errors each); the scratch holder's output naming the real lock dir and the slot indices it held, plus the summary line and wall time of the full-file run made while they were held (observation produced by E-04's holder process plus `suite_cache.suite_slot`); the bare `python3 -m pytest` summary line; and the `aw sanitize --agent` result record with its exit code.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit zyy2yg -- tests/test_suite_cache.py` (plus this plan when recording evidence), after verifying `git diff --cached --name-only` lists only those paths; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize zyy2yg` itself.
