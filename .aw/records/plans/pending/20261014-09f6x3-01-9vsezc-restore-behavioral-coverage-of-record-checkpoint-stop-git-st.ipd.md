# IPD: Restore behavioral coverage of _record_checkpoint_stop git status recording on a dirty isolated worktree

- Date: 2026-10-14
- Kind: child
- Concern: The level-3 checkpoint stop record (`_record_checkpoint_stop`) lost its only behavioral guard when `tests/test_runner_stop.py` was deleted in `19313eed7`; nothing now proves that a stop on a dirty isolated worktree records that worktree's real `git status` instead of an `<unobserved: ...>` error string.
- Scope: Add behavioral tests that call `_record_checkpoint_stop` (both host wrappers and the shared definition) against a real dirty git repository and assert on the returned record, the item's `stopped` field, and the appended `events.jsonl` line; then repoint the one docstring sentence in `runner_shared._record_checkpoint_stop` that claims "no live guard currently asserts this" at the new tests. No executable production change.
- Scope-Paths: tests/test_liftaudit_stop_halts_run.py, agent_workflows/runner_shared.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 09f6x3
- Set: 09f6x3
- Order: 1
- Highest E allocated: 04
- Author: OpenCode Claude Opus
- Id: 9vsezc

## Workflow history
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-15 reviewed (aw set): plan-review applied revisions

- 2026-10-14 draft (OpenCode Claude Opus): created.
- 2026-10-14 to-review (OpenCode Claude Opus): authored from backlog `09f6x3`; Step 0 evidence gathered; ready for `/plan-review`.

## Goal

Restore, as behavior-only tests, the property the deleted `tests/test_runner_stop.py::test_stop_isolated_git_status` guarded for `_record_checkpoint_stop` (yuhl6o site S-33): stopping at a checkpoint while an isolated lane worktree is dirty records that worktree's observed `git status`, naming the dirty file, on both hosts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Host-wrapper behavior on a dirty isolated worktree

- [ ] E-01 Add a test to `tests/test_liftaudit_stop_halts_run.py` that, for each host module (`oc_runipd`, `agy_runipd`, via `subTest`), creates a temp main repo and a SEPARATE temp git repo standing in for the isolated lane (reuse the file's `_init_clean_repo` helper), writes an untracked `dirty_file.txt` into the lane only, builds a `runner_stop.CheckpointObserver(detector=lambda line: True, requested_level=3)`, calls `mod._record_checkpoint_stop(run_dir, state, item, obs, work_dir=lane)`, and asserts: the returned `git_state` contains `dirty_file.txt`; it does not start with `<unobserved`; `item["stopped"]["git_state"]` equals the returned value; `item["stopped"]["stopped_deliberately"]` is True and `level` is 3; and `run_dir / "events.jsonl"` gained exactly one JSON line whose `id6` matches the item.
  - Depends on: none
  - Expected outcome: a new test exercising both real host wrappers end to end through real `git status --short`, passing against current code.
  - Execution state: pending

- [ ] E-02 Add a test in the same file proving the worktree-resolution precedence observably, with BOTH repos dirty under DISTINCT names (lane: untracked `dirty_file.txt`; main: untracked `main_dirty.txt`), so every case asserts a POSITIVE observation rather than an absence that an `<unobserved: ...>` string would also satisfy. For each host via `subTest`: (a) NO `work_dir`, `item["worktree"] = str(lane)`: `git_state` contains `dirty_file.txt` and not `main_dirty.txt`; (b) NO `work_dir`, `item = {"attempts": [{"worktree": str(lane)}]}`: likewise; (c) `work_dir=lane` AND `item["worktree"] = str(main)`: `git_state` contains `dirty_file.txt` and not `main_dirty.txt` (`work_dir` wins); (d) none set: `git_state` contains `main_dirty.txt` (fallback to `state["repo"]`). In every case assert `git_state` does not start with `<unobserved`.
  - Depends on: E-01
  - Expected outcome: the record observes the isolated lane, not the main checkout, whenever the call or the item names one, with `work_dir` taking precedence, and falls back to `state["repo"]` otherwise.
  - Execution state: pending

### Task group 2: Shared definition contract

- [ ] E-03 Add a test calling `runner_shared._record_checkpoint_stop` directly with an injected `git_status_fn=lambda repo: f"?? {repo.name}-dirty"` and asserting the record's `git_state` is exactly that string for the resolved lane path; plus a test that a raising `git_status_fn` yields a `git_state` beginning `<unobserved:` without the call raising; plus a test that omitting `git_status_fn` raises `TypeError` (mirroring the existing `test_record_forced_stop_omitted_git_status_fn_raises`).
  - Depends on: none
  - Expected outcome: the injection seam, honest-failure note, and no-default rule documented in `runner_shared._record_checkpoint_stop` are each asserted by calling the function.
  - Execution state: pending

### Task group 3: Repoint the in-code citation

- [ ] E-04 In the `runner_shared._record_checkpoint_stop` docstring, replace only the parenthetical "(`tests/test_runner_stop.py::test_stop_isolated_git_status` was deleted in `19313eed`; no live guard currently asserts this)" with wording that the deleted test was removed in `19313eed` and the property is now asserted behaviorally by the dual-host dirty-lane tests in `tests/test_liftaudit_stop_halts_run.py`. Leave every other line of the docstring, the function body, and the separate `test_runner_stop.py` mention near the `signal.signal` design-history comment in `runner_shared` (a different property) unchanged.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: after this plan the docstring no longer falsely claims the property is unguarded; docstring-only diff in `agent_workflows/runner_shared.py`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 / AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": tests must call the code and assert on outputs and side effects; no `inspect`/`ast`/source reading. Every E-item here calls `_record_checkpoint_stop` and reads its return value, `item`, and `events.jsonl`.
- The sibling forced-stop coverage already lives in `tests/test_liftaudit_stop_halts_run.py` (`test_record_forced_stop_injected_git_status`, `test_record_forced_stop_omitted_git_status_fn_raises`), and that file defines `_init_clean_repo`; it is therefore the natural home and the only Scope-Path.
- Suite is run bare: `python3 -m pytest` (repo-local development contract). Narrowed runs use `python3 -m pytest -o addopts="" <file>`.
- Host wrappers: `oc_runipd._record_checkpoint_stop` and `agy_runipd._record_checkpoint_stop` bind each host's own `git_status` (which calls `runner_shared.git_status(repo, run_checked=run_checked)`, i.e. `git status --short`) and delegate to `runner_shared._record_checkpoint_stop`.
- `runner_stop.CheckpointObserver` is a dataclass whose first field is `detector`; the deleted test's `CheckpointObserver(run_dir)` positional call is therefore not reused as-is.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The guard was deleted in `19313eed7` ("trim test suite"). | `git show 19313eed7^:tests/test_runner_stop.py` contains `def test_stop_isolated_git_status` (checks both `_record_forced_stop` and `_record_checkpoint_stop` on a dirty lane). |
| F-2 | No live test calls `_record_checkpoint_stop`. | `grep -n _record_checkpoint_stop tests/*.py` returns nothing; only `_record_forced_stop` is covered in `tests/test_liftaudit_stop_halts_run.py`. |
| F-3 | The docstring of `runner_shared._record_checkpoint_stop` states the defect class explicitly: without the injected `git_status_fn`, `git_state` became `<unobserved: git_status() missing 1 required keyword-only argument ...>` silently, and "no live guard currently asserts this". | `runner_shared._record_checkpoint_stop` docstring. |
| F-4 | yuhl6o recorded S-33 as RETIRE-UNGUARDED with `Removed-by: 19313eed`. | `.aw/records/plans/executed/20261011-iosmvn-01-yuhl6o-...ipd.md`, S-33 row. |
| F-5 | Review probe: both host wrappers resolve `git_status` from module globals at call time (`git_status_fn=git_status` inside each wrapper), so `mock.patch.object(<host>, "git_status", runner_shared.git_status)` reproduces the ORIGINAL defect exactly: the recorded `git_state` becomes `<unobserved: git_status() missing 1 required keyword-only argument: 'run_checked'>`. Measured against current code: real call `'?? dirty_file.txt'`; `item["worktree"]`, `attempts[-1]["worktree"]`, and `work_dir` over `item["worktree"]` all observe the lane; fallback with a clean main gives `''`, with a dirty main gives `'?? main_dirty.txt'`. | The mutation check needs no source edit; and a clean-main fallback assertion "does not contain `dirty_file.txt`" would pass on an `<unobserved` string too, so E-02 uses a dirty main. |
| F-6 | Once E-01..E-03 land, the `runner_shared._record_checkpoint_stop` docstring's "no live guard currently asserts this" becomes false. Sibling plan `90yi49` repoints its equivalent S-03 docstring in scope. | E-04 (Task group 3) repoints it rather than deferring a known-false sentence. |

## Proposed changes (ordered, validatable)

1. E-01: dual-host dirty-lane test via real git.
2. E-02: worktree-resolution precedence test (`work_dir` > `item["worktree"]` > last attempt's `worktree` > `state["repo"]`).
3. E-03: shared-definition injection, honest-failure, and no-default tests.
4. E-04: repoint the `runner_shared._record_checkpoint_stop` docstring's "no live guard" clause at the new tests (F-6).

## Deferred / out of scope (with reason)

- `_record_forced_stop` dirty-lane coverage via the host wrappers: already partially covered by the shared-level injection tests (`test_record_forced_stop_injected_git_status`, `test_record_forced_stop_omitted_git_status_fn_raises`), and not the property this backlog item names.
  - Carrier-Declined: backlog `09f6x3` names only `_record_checkpoint_stop`; no defect is recorded against `_record_forced_stop`, so filing an item is a maintainer's choice and not an obligation of this plan.

## Scope check

- Over-scope: none.
- Under-scope: none; the backlog item names one property (isolated git status recording on a dirty worktree for `_record_checkpoint_stop`) and E-01/E-02 assert it on both hosts, E-03 asserts the shared seam the property depends on, and E-04 keeps the in-code citation honest once the guard exists (F-6).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_liftaudit_stop_halts_run.py -v` shows each new test passing.
- Mutation check, in-process only, never editing production source: a throwaway `python3 -c` driver (not committed) that loads the E-01 test and runs it under `unittest` while `mock.patch.object(<host>, "git_status", runner_shared.git_status)` is active for each host, which reproduces the original unbound-`run_checked` defect (F-5); the test must FAIL, then PASS with the patch removed. `git diff --stat -- agent_workflows/` afterwards shows only the E-04 docstring edit.
- Full suite bare: `python3 -m pytest` shows no failure that does not also fail on the base commit (compare failing test ids by name against a base-commit run when anything fails).
- `git diff -- agent_workflows/runner_shared.py` shows only docstring lines of `_record_checkpoint_stop` changed.

## Spec / documentation sync

N/A: restores test coverage plus one in-code docstring correction (E-04); no spec or user-facing behavior changes.

## Open questions

### OQ-01: Which test file should host the restored coverage?

- Blocking: no
- Status: resolved
- Owner: plan author (OpenCode Claude Opus); confirmed by /plan-review
- Resolution or deferral rationale: `tests/test_liftaudit_stop_halts_run.py`, because it already holds the sibling `_record_forced_stop` tests and the `_init_clean_repo` helper (F-2); recreating `tests/test_runner_stop.py` would revive a file the suite trim deliberately removed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_liftaudit_stop_halts_run.py -v` output showing the E-01 test PASSED with both `driver=oc_runipd` and `driver=agy_runipd` subtests exercised; plus pasted output of the in-process mutation driver (each host's `git_status` patched to the unbound `runner_shared.git_status`) showing that test FAILED with the recorded `<unobserved: ... 'run_checked'>` value visible, then PASSED unpatched, and `git diff --stat -- agent_workflows/` showing no executable change.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the E-02 precedence test PASSED, and the test source excerpt showing the dirty-main (`main_dirty.txt`) / dirty-lane (`dirty_file.txt`) setup and the four resolution cases (`item["worktree"]`, `attempts[-1]["worktree"]`, `work_dir` over `item["worktree"]`, fallback to `state["repo"]`), each asserting a positive observation.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing the injected-string, raising-`git_status_fn` (`<unobserved:` prefix), and omitted-`git_status_fn` (`TypeError`) tests PASSED; plus the pasted summary line of a bare `python3 -m pytest` run, with any failure shown to fail identically on the base commit; plus pasted `git diff` of the new test code showing no `inspect`/`ast` import and no read of any `agent_workflows/*.py` source file (any `read_text` reads only the test's own `events.jsonl`) (P16).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff -- agent_workflows/runner_shared.py` showing only lines inside the `_record_checkpoint_stop` docstring changed, the sentence "no live guard currently asserts this" removed from that docstring, and `tests/test_liftaudit_stop_halts_run.py` named in its place; plus pasted `rg -n "no live guard currently asserts this" agent_workflows/runner_shared.py` output showing that the `_record_checkpoint_stop` occurrence is gone (other unrelated occurrences may remain).
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Open questions: OQ-01 is resolved; none remain. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no pasted output does not satisfy it. Start with `aw ipd begin 9vsezc`. Commit ONLY the `- Scope-Paths:` (`tests/test_liftaudit_stop_halts_run.py`, `agent_workflows/runner_shared.py`), through `aw commit 9vsezc -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`. Verify the staged set with `git diff --cached --name-only` before committing. All git fixtures live in temp directories; the mutation check patches in-process only and never leaves a modified production file on disk.

DO NOT WIDEN. No executable change in `runner_shared.py`, `oc_runipd.py` or `agy_runipd.py`; do not recreate `tests/test_runner_stop.py`; do not add host-wrapper `_record_forced_stop` dirty-lane coverage; do not edit any other `19313eed` citation or executed plan `yuhl6o`. An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`.

POST-GATE LIFECYCLE. Execution requires explicit human approval (`aw ipd set approved 9vsezc`). On completion every `V-*` carries pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` must conform before the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that finalize, so the executor must NOT run it; executed by hand, run `aw ipd finalize 9vsezc`. Never hand-roll the move or `git mv` the plan.
