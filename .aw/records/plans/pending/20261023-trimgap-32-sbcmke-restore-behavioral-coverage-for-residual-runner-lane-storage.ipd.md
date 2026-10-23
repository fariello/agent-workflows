# IPD: Restore behavioral coverage for residual runner, lane, storage, telemetry and push-gate helpers

- Date: 2026-10-23
- Kind: child
- Concern: Residual backlog item `nzc6dm` carries five runner-side keys the routine core tier does not guard, all with operator `return-none`: `runner_shared.attributed_away_failure_ids` (group 48, `wo21z5` `unguarded`), `worktree_lease.lane_id_from_branch` (group 52, `budget-exhausted`), `storage.get_git_common_dir` (group 50, `unprovable`), `run_analytics_telemetry.TelemetryCollector._observe_tool_versions` (group 46, `unprovable`) and `check_engine.check_push_authorization` (group 31, `unguarded`). Measured at authoring HEAD `6c0a6b72a` (F-01, F-02): `attributed_away_failure_ids` is not reached by core and its mutant survives every surviving file that reaches it; the other four ARE reached by core but their `return-none` mutants SURVIVE the core-reaching files. The verdict `unprovable` was a missing assertion, not an inapplicable probe: each key returns a non-None value that a test can observe (F-03). So a regression that dropped the gate-answer attribution, lost a lane id, lost the git common dir, dropped tool versions from telemetry or silently allowed every push would pass the routine gate.
- Scope: Add ONE new core-marked test module, `tests/test_runner_residual_helpers.py`, with direct behavioral tests of the five keys (through `hooks.prepush_authorization_gate.check` for the push gate, through `TelemetryCollector.start` for the tool-version observation, and directly for the other three), asserting on returned tuples, strings, exit codes and emitted events (values measured at F-03); then probe all five under the core selection. EXCLUDES any production-code change; EXCLUDES restoring the deleted control files whole (`tests/test_gate_answer_propagation.py` is 1290 lines and 46 tests; `tests/test_resumedupe.py` 675 lines; `tests/test_phase4_hooks.py` patches the very rule it would guard), and EXCLUDES the other `runner_shared` keys owned by backlog `l2zsa9`.
- Scope-Paths: tests/test_runner_residual_helpers.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: nzc6dm
- Set: trimgap
- Order: 32
- Highest E allocated: 07
- Author: opencode
- Id: sbcmke

## Workflow history
- 2026-10-23 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 fixed (execution contract, E-06 commit/parent recorded, hermetic git fixture in E-03); F-03 values, operator applicability and F-04 control facts reproduced at f76595a5a

- 2026-10-23 to-review (opencode): authored from backlog `nzc6dm` (groups 31, 46, 48, 50, 52). Measured core reach at HEAD `6c0a6b72a`, probed each key against its core-reaching or surviving files, and measured every asserted return value before writing expected outcomes.
- 2026-10-23 draft (opencode): created.

## Goal

Make a `return-none` mutation of any of the five keys turn a routine core-tier test red, using direct assertions on what each returns or emits. Done means all five report `verdict: killed` under a `-m core` selection containing the new module.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the new core-tier module

- [ ] E-01 Create `tests/test_runner_residual_helpers.py` with a provenance docstring naming backlog `nzc6dm`, plan `sbcmke` and findings `wo21z5`; `import pytest`; module-level `pytestmark = pytest.mark.core`; and an `AttributedAwayFailureIdsTests` class. With `K = runner_shared.GATE_ANSWER_RECORD_KEY`, assert: `{K: {"answer": "not-mine", "usable": True, "failing_tests": ["FAILED tests/test_a.py::T::test_x - boom", "FAILED tests/test_b.py::test_y", "FAILED tests/test_a.py::T::test_x - again", "garbage line ???"]}}` returns exactly `("FAILED tests/test_a.py::T::test_x", "FAILED tests/test_b.py::test_y")` (normalized, de-duplicated in order, the unparseable line dropped); the same record with `"answer": "mine"` returns `()`; with `"usable": False` returns `()`; with `failing_tests` a bare string returns `()`; an item with no record (`{}`) returns `()`.
  - Depends on: none
  - Expected outcome: the class's tests PASS at HEAD (values measured at F-03).
  - Execution state: pending

- [ ] E-02 Add a `LaneIdFromBranchTests` class: `worktree_lease.lane_id_from_branch("aw/lane/ntf6sx") == "ntf6sx"`, `("aw/lane/abc123_attempt2") == "abc123_attempt2"`, and `None` for `"aw/lane/"`, `"main"` and `""`.
  - Depends on: E-01
  - Expected outcome: the class's tests PASS at HEAD (values measured at F-03).
  - Execution state: pending

- [ ] E-03 Add a `GitCommonDirTests` class using `tmp_path`: init a git repo `r` (`git init -q -b main`, set `user.email`/`user.name` and `commit.gpgsign false` locally so a host-level signing config cannot fail the commit, the pattern of `tests/support.py`, commit one file) and add a linked worktree `wt` with `git worktree add -q`. Assert `storage.get_git_common_dir(r)` and `storage.get_git_common_dir(wt)` are both equal to `os.path.realpath(r / ".git")` (a linked worktree resolves to the MAIN repository's git dir, which is the property the function exists for), and `storage.get_git_common_dir(<a plain non-git tmp dir>)` is `None`.
  - Depends on: E-01
  - Expected outcome: the class's tests PASS at HEAD (behavior measured at F-03).
  - Execution state: pending

- [ ] E-04 Add a `TelemetryToolVersionsTests` class: build `run_analytics_telemetry.TelemetryCollector(tmp_path / "s.jsonl", execution_id="e1", salt="s", adapter=run_analytics_telemetry.FakeResourceProbeAdapter(tool_versions=run_analytics_telemetry.ProbeOutcome("ok", {"python": "3.14.0"})))`, call `start()` and assert the returned event has `event_kind == "start"` and `tool_versions == {"python": "3.14.0"}`; then call `close()`. A second collector whose adapter returns `ProbeOutcome("unavailable")` emits a start event with no `tool_versions` key; a third whose adapter subclass raises from `tool_versions()` also emits a start event with no `tool_versions` key (the probe failure does not take the run down).
  - Depends on: E-01
  - Expected outcome: the class's tests PASS at HEAD (behavior measured at F-03).
  - Execution state: pending

- [ ] E-05 Add a `PushAuthorizationGateTests` class driving the hook `agent_workflows.hooks.prepush_authorization_gate.check(tmp_path)` with `monkeypatch` controlling `AW_PUSH_AUTHORIZED` (`check_engine.PUSH_ACK_ENV`): unset -> returns exit `1` with exactly one message containing `check.push-unauthorized` and `AW_PUSH_AUTHORIZED=1`; set to `1` -> returns `(0, [])`. Also call `check_engine.check_push_authorization(tmp_path, ack=False)` directly and assert one `Drift` with `rule == "check.push-unauthorized"` and `location == "<push>"`, and `ack=True` returns `[]`. Do NOT patch `check_push_authorization`: the point is to exercise the real rule.
  - Depends on: E-01
  - Expected outcome: the class's tests PASS at HEAD (values measured at F-03).
  - Execution state: pending

### Task group 2: commit and prove the mutants die in core

- [ ] E-06 Commit the module with `aw commit sbcmke -- tests/test_runner_residual_helpers.py` and record the resulting commit hash as `<E-06 commit>` (its parent is `<E-06 parent>`, used by V-07 and Required tests), then run the routine bare gate `python3 -m pytest` and record its summary line and any `CORE TIER BUDGET EXCEEDED` block verbatim, plus `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_runner_residual_helpers.py`.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: bare run shows no failures and includes the new tests; the module costs about one second serial (one throwaway git repo plus worktree; everything else in memory).
  - Execution state: pending

- [ ] E-07 For each key K in (`agent_workflows/runner_shared.py::attributed_away_failure_ids`, `agent_workflows/worktree_lease.py::lane_id_from_branch`, `agent_workflows/storage.py::get_git_common_dir`, `agent_workflows/run_analytics_telemetry.py::TelemetryCollector._observe_tool_versions`, `agent_workflows/check_engine.py::check_push_authorization`), run `python3 tools/mutation_probe.py --op return-none --format json K -- -o addopts= -q -p no:randomly -n0 -m core tests/test_runner_residual_helpers.py`, after E-06's commit. A kill under this core-marked subset is a kill under the full core tier, a superset. Record each `verdict`, `baseline_failing` and `mutant_failing`; if any key survives, add the missing assertion, commit the same way, and re-probe.
  - Depends on: E-06
  - Expected outcome: five `verdict: killed`, each `baseline_failing: 0`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16): every test calls the real function or hook and asserts on what it returns or emits; E-05 deliberately does not mock the rule under test.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget; module-level `pytestmark = pytest.mark.core` is the established way in.
- `FakeResourceProbeAdapter` is the module's own deterministic test adapter ("no device, no subprocess, no `/proc`, no sleep"), so E-04 needs no host probing.
- Probe tool: `tools/mutation_probe.py` as used by `wo21z5` and siblings.
- Commit only through `aw commit sbcmke -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `python3 tools/replay_coverage_diff.py baseline --out .aw/state/nzc6dm-auth/core -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` at HEAD `6c0a6b72a` | `attributed_away_failure_ids` is absent from the core baseline. Core reaches `lane_id_from_branch` (12 contexts, `tests/test_runner_shared.py`), `get_git_common_dir` (1, `tests/test_storage.py`), `_observe_tool_versions` (31, 2 files) and `check_push_authorization` (1, `tests/test_core_module_coverage.py`). |
| F-02 | `tools/mutation_probe.py --op return-none --format json <K> -- -o addopts= -q -p no:randomly -n 6 -m <sel> <files>` at `6c0a6b72a` | Under `-m "core and not slow and not livecorpus"` over each key's core-reaching files: `lane_id_from_branch` `survived` 0 (48.26s); `get_git_common_dir` `survived` 0 (7.22s); `_observe_tool_versions` `survived` 0 (53.63s); `check_push_authorization` `survived` 0 (19.62s). Under `-m "not slow and not livecorpus"` over `tests/test_suite_baseline_direction.py tests/test_suite_cache.py`: `attributed_away_failure_ids` `survived` 0 (102.94s). |
| F-03 | direct calls at HEAD `6c0a6b72a` | `attributed_away_failure_ids` of the E-01 record -> `('FAILED tests/test_a.py::T::test_x', 'FAILED tests/test_b.py::test_y')`; `mine`, unusable, bare-string and absent -> `()`. `lane_id_from_branch`: `ntf6sx`, `abc123_attempt2`, and `None` x3. `get_git_common_dir`: main repo and linked worktree both -> `<r>/.git`; non-git dir -> `None`. `TelemetryCollector.start()` with tool versions ok -> `tool_versions {'python': '3.14.0'}`; with a raising adapter -> start event without `tool_versions`. `prepush_authorization_gate.check`: unset -> `(1, ['<push>: check.push-unauthorized: ... fix: if this push is intended and authorized, set AW_PUSH_AUTHORIZED=1 ...'])`; `AW_PUSH_AUTHORIZED=1` -> `(0, [])`. |
| F-04 | `git show 19313eed^:<control>` | The `wo21z5` controls are large or unsuitable: `tests/test_gate_answer_propagation.py` (1290 lines, 46 tests), `tests/test_resumedupe.py` (675 lines, 26 tests, mostly lane-recovery integration), and the push-gate test in `tests/test_phase4_hooks.py` patches `check_push_authorization` with a spy, so it cannot guard that key. Direct tests are cheaper and target each key. |

## Proposed changes (ordered, validatable)

1. E-01 creates the module and the gate-answer attribution tests.
2. E-02 adds the lane-id tests.
3. E-03 adds the git-common-dir tests.
4. E-04 adds the telemetry tool-version tests.
5. E-05 adds the push-gate tests.
6. E-06 commits the module and records the bare core gate.
7. E-07 probes all five keys under the core selection.

## Deferred / out of scope (with reason)

- Restoring the `wo21z5` control files whole.
  - Carrier-Declined: no work is owed; F-04 shows they are large or mock the guarded rule, and direct tests close each key's gap at far lower core cost.
- Other `runner_shared` keys of the trim population (`spec_impacts_for_queue`, `expand_selectors`, `route_recovery_turn`).
  - Carrier-Declined: no work is owed here; they belong to sibling backlog item `l2zsa9`, not to `nzc6dm`.

## Scope check

- Over-scope: none. Only the new test module is declared; no production file or existing test changes.
- Under-scope: none. All five keys get direct assertions (E-01 to E-05) and a core-selection probe (E-07).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_runner_residual_helpers.py`: every test PASSED, list pasted (E-01 to E-05).
- Bare `python3 -m pytest` summary line and any budget block pasted, plus the module's `--durations=0` output (E-06).
- Five `tools/mutation_probe.py` JSON results pasted, each `verdict: killed`, `baseline_failing: 0` (E-07).
- `git diff --stat <E-06 parent>..HEAD -- agent_workflows/` empty (no production change).

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: `get_git_common_dir` and `_observe_tool_versions` were `unprovable` in `wo21z5`; is the probe applicable?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. `return-none` applies to both (verified with `tools.mutation_probe.apply_operator` at HEAD), and both return observable non-None values (F-03): a path string and a dict that lands in the emitted event. `wo21z5`'s "control survived" meant no test asserted on those values; E-03, E-04 and E-07 close and prove that.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the head of `tests/test_runner_residual_helpers.py` showing the provenance docstring (naming `nzc6dm`, `sbcmke`, `wo21z5`) and `pytestmark = pytest.mark.core`; the `-v` lines for every `AttributedAwayFailureIdsTests` test, each PASSED; and `grep -nE "inspect|getsource|ast\." tests/test_runner_residual_helpers.py` returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` lines for every `LaneIdFromBranchTests` test, each PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` lines for every `GitCommonDirTests` test, each PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` lines for every `TelemetryToolVersionsTests` test, each PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` lines for every `PushAuthorizationGateTests` test, each PASSED, and `grep -n "mock\|patch" tests/test_runner_residual_helpers.py` showing no patch of `check_push_authorization`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `aw commit` output (or `git show --stat HEAD`) naming only `tests/test_runner_residual_helpers.py`; the bare `python3 -m pytest` summary line with no `failed`, any `CORE TIER BUDGET EXCEEDED` block verbatim, and the module's `--durations=0` output.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the recorded `<E-06 commit>` and `<E-06 parent>` hashes; paste the five JSON outputs produced by `tools/mutation_probe.py` (E-07), each with `head` equal to the E-06 commit or later, a selection containing `-m core tests/test_runner_residual_helpers.py`, `verdict: killed` and `baseline_failing: 0`; and `git diff --stat <E-06 parent>..HEAD -- agent_workflows/` showing no change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Scope fence: `- Scope-Paths:` (`tests/test_runner_residual_helpers.py`) is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and then justified (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path). No production file under `agent_workflows/` may change. Commit only files you changed, through `aw commit sbcmke -- tests/test_runner_residual_helpers.py` (plus this plan when recording evidence); never `git add -A`, never push. You MUST paste the ACTUAL runner and probe output into each `V-*`; never claim a test passed or a mutant was killed that you did not run. Lifecycle: after every `V-*` reads `Result: pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize sbcmke` itself.
