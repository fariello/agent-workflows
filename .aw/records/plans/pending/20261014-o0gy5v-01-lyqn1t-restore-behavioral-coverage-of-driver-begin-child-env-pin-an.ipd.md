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

- [ ] E-01 Create `tests/test_driver_begin_child_env.py` with a `subprocess.run` spy class (records argv, kwargs, call count; returns `subprocess.CompletedProcess(argv, 0, stdout="", stderr="")`) and a test parametrized with `pytest.mark.parametrize` over host (`oc_runipd`, `agy_runipd`, ids `oc`/`agy`) and `isolated` (False, True), so `-v` shows four distinct passing ids (unittest `subTest` is NOT used: `pytest-subtests` is not installed, so subtests would not appear in `-v` output). Each case runs under `unittest.mock.patch.dict(os.environ, <os.environ minus AW_PIN_KEEP_ROOT, PYTHONPATH, AW_ISOLATED_BASELINE>, clear=True)` because the runner, and any lane it spawns, inherits `AW_PIN_KEEP_ROOT` and a `PYTHONPATH` containing the package root from its own pin, so without clearing them an unpinned builder would still pass these assertions when the suite runs from the main checkout. Inside that, with `runner_shared.subprocess.run` patched, call `module.driver_begin(Path("/nonexistent"), "aaa111", "actor", isolated=isolated)` and assert: return code 0 and exactly one launch; `env["AW_PIN_KEEP_ROOT"] == runner_shared.runner_package_root()`; that root is an element of `env["PYTHONPATH"].split(os.pathsep)`; `argv[:len(prefix)] == runner_shared.pinned_module_argv([])`; argv after the prefix equals `["ipd", "begin", "aaa111", "--actor", "actor", "--dir", "/nonexistent"]`; `kwargs["stdin"] is subprocess.DEVNULL`; `kwargs["cwd"] == "/nonexistent"`.
  - Depends on: none
  - Expected outcome: test passes on both hosts in both isolation modes.
  - Execution state: pending
- [ ] E-02 In the same module, add a test asserting the baseline overlay: `env.get("AW_ISOLATED_BASELINE") == "1"` when `isolated=True` and the key is absent when `isolated=False` (under the same cleared `os.environ` as E-01, so an inherited value cannot mask the result), parametrized over both hosts and both isolation modes; plus a `run_id="run-x"` case on both hosts asserting `argv[-2:] == ["--run-id", "run-x"]`, and that without `run_id` the argv contains no `--run-id`.
  - Depends on: E-01
  - Expected outcome: overlay and run-id propagation asserted on both hosts.
  - Execution state: pending
- [ ] E-03 In the same module, add a non-vacuity test: under the same cleared `os.environ` as E-01, call `runner_shared.driver_begin(...)` with an injected `env_builder=lambda: dict(os.environ)` (an unpinned builder) and an `argv_builder` returning `[sys.executable, "-m", "agent_workflows", *args]`, and assert the spied env lacks `AW_PIN_KEEP_ROOT`, the package root is not on its `PYTHONPATH`, and the argv prefix differs from `pinned_module_argv([])`, proving the E-01 assertions can fail through the real launcher. (Measured at review: WITHOUT the cleared environ, this unpinned builder's env carried the runner's inherited `AW_PIN_KEEP_ROOT`, so the clearing is load-bearing.)
  - Depends on: E-01
  - Expected outcome: an unpinned builder is observably distinguishable through the real launcher.
  - Execution state: pending

### Task group 2: Comment repoint

- [ ] E-04 In `runner_shared.driver_begin`, replace the comment text "(deleted in `19313eed`; no live guard currently asserts this; it read the env this builds and checked the pin's markers)" (it wraps across two `#` comment lines inside the `subprocess.run(` call, just above `env={**env_builder(), **begin_baseline_env(isolated)}`) so it names `tests/test_driver_begin_child_env.py` as the live behavioral guard (restored by o0gy5v). Comment-only edit; no code change.
  - Depends on: E-01
  - Expected outcome: the comment no longer claims the pin is unguarded.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_driver_begin_child_env.py -v` output showing the pin test PASSED as four distinct parametrized ids (oc/agy x isolated False/True), plus the pasted test body showing the cleared `os.environ` patch.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the baseline-overlay and run-id test(s) PASSED, plus a pasted one-off in-process mutation run that leaves the source untouched (so it cannot collide with E-04's edit of the same file): `python3 -c "import sys, pytest; from unittest import mock; from agent_workflows import runner_shared; mock.patch.object(runner_shared, 'begin_baseline_env', lambda _i: {}).start(); sys.exit(pytest.main(['-o', 'addopts=', '-p', 'no:randomly', '<overlay test node id(s)>']))"` showing the `isolated=True` overlay cases FAIL, and `git status --short agent_workflows/` afterwards showing nothing beyond E-04's change.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing the non-vacuity test PASSED, plus pasted output of `python3 -m pytest -o addopts="" tests/test_no_code_structure_pins.py` passing and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff agent_workflows/runner_shared.py` showing only comment lines changed and naming `tests/test_driver_begin_child_env.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved lyqn1t --by-human`); OQ-01 is resolved and no question blocks. Begin with `aw ipd begin lyqn1t`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to `agent_workflows/runner_shared.py` that cannot be safely combined, or `runner_shared.driver_begin` no longer launching through `subprocess.run` with `env={**env_builder(), **begin_baseline_env(isolated)}`.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. The V-02 mutation is in-process only and is never written to source or committed.

Commits: commit only the Scope-Paths files you changed through `aw commit lyqn1t -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: after every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/` through the tooled lifecycle. Under `aw oc run` / `aw agy run` the RUNNER owns finalize, so do not run it yourself; when executing by hand, run `aw ipd finalize lyqn1t`. Never hand-roll a `git mv`.
