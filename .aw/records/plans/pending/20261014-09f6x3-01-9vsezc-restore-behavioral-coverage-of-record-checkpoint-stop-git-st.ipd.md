# IPD: Restore behavioral coverage of _record_checkpoint_stop git status recording on a dirty isolated worktree

- Date: 2026-10-14
- Kind: child
- Concern: The level-3 checkpoint stop record (`_record_checkpoint_stop`) lost its only behavioral guard when `tests/test_runner_stop.py` was deleted in `19313eed7`; nothing now proves that a stop on a dirty isolated worktree records that worktree's real `git status` instead of an `<unobserved: ...>` error string.
- Scope: Add behavioral tests that call `_record_checkpoint_stop` (both host wrappers and the shared definition) against a real dirty git repository and assert on the returned record, the item's `stopped` field, and the appended `events.jsonl` line. Test-only; no production change.
- Scope-Paths: tests/test_liftaudit_stop_halts_run.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 09f6x3
- Set: 09f6x3
- Order: 1
- Highest E allocated: 03
- Author: OpenCode Claude Opus
- Id: 9vsezc

## Workflow history

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

- [ ] E-02 Add a test in the same file proving the worktree-resolution precedence observably: with the main repo CLEAN and the lane DIRTY, calling the host wrapper with NO `work_dir` but `item["worktree"] = str(lane)` records the lane's dirty file; and with `item = {"attempts": [{"worktree": str(lane)}]}` likewise; and with none of those set the record reflects the clean main repo (`git_state` does not contain `dirty_file.txt`).
  - Depends on: E-01
  - Expected outcome: the record observes the isolated lane, not the main checkout, whenever the item names one, and falls back to `state["repo"]` otherwise.
  - Execution state: pending

### Task group 2: Shared definition contract

- [ ] E-03 Add a test calling `runner_shared._record_checkpoint_stop` directly with an injected `git_status_fn=lambda repo: f"?? {repo.name}-dirty"` and asserting the record's `git_state` is exactly that string for the resolved lane path; plus a test that a raising `git_status_fn` yields a `git_state` beginning `<unobserved:` without the call raising; plus a test that omitting `git_status_fn` raises `TypeError` (mirroring the existing `test_record_forced_stop_omitted_git_status_fn_raises`).
  - Depends on: none
  - Expected outcome: the injection seam, honest-failure note, and no-default rule documented in `runner_shared._record_checkpoint_stop` are each asserted by calling the function.
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

## Proposed changes (ordered, validatable)

1. E-01: dual-host dirty-lane test via real git.
2. E-02: worktree-resolution precedence test (`work_dir` > `item["worktree"]` > last attempt's `worktree` > `state["repo"]`).
3. E-03: shared-definition injection, honest-failure, and no-default tests.

## Deferred / out of scope (with reason)

- Editing the `runner_shared._record_checkpoint_stop` docstring sentence "no live guard currently asserts this": that is production source outside Scope-Paths and a comment edit, not behavior; leave for a separate chore if desired.
- `_record_forced_stop` dirty-lane coverage via the host wrappers: already partially covered by the shared-level injection tests, and not the property this backlog item names.

## Scope check

- Over-scope: none.
- Under-scope: none; the backlog item names one property (isolated git status recording on a dirty worktree for `_record_checkpoint_stop`) and E-01/E-02 assert it on both hosts, E-03 asserts the shared seam the property depends on.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_liftaudit_stop_halts_run.py -v` shows each new test passing.
- Mutation check (temporary, not committed): make the host wrapper's `git_status_fn` raise (e.g. temporarily bind `git_status_fn=lambda r: (_ for _ in ()).throw(TypeError("x"))` in a scratch copy, or monkeypatch `oc_runipd.git_status` to raise inside the test run) and confirm E-01's assertion fails, proving the test detects the original defect class; revert.
- Full suite bare: `python3 -m pytest` passes with no new failures.

## Spec / documentation sync

N/A: test-only change restoring coverage; no spec or user-facing behavior changes.

## Open questions

### OQ-01: Which test file should host the restored coverage?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `tests/test_liftaudit_stop_halts_run.py`, because it already holds the sibling `_record_forced_stop` tests and the `_init_clean_repo` helper (F-2); recreating `tests/test_runner_stop.py` would revive a file the suite trim deliberately removed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_liftaudit_stop_halts_run.py -v` output showing the E-01 test PASSED with both `driver=oc_runipd` and `driver=agy_runipd` subtests exercised; plus pasted output of the mutation check (host `git_status` forced to raise) showing that test FAILED, then passing again after revert.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the E-02 precedence test PASSED, and the test source excerpt showing the clean-main/dirty-lane setup and the three resolution cases (`item["worktree"]`, `attempts[-1]["worktree"]`, fallback to `state["repo"]`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing the injected-string, raising-`git_status_fn` (`<unobserved:` prefix), and omitted-`git_status_fn` (`TypeError`) tests PASSED; plus pasted output of a bare `python3 -m pytest` run showing the `N passed` summary with no new failures; plus pasted `git diff` of the new test code showing no `inspect`/`ast` import and no read of any `agent_workflows/*.py` source file (any `read_text` reads only the test's own `events.jsonl`) (P16).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_liftaudit_stop_halts_run.py` via `aw commit <this plan> -- tests/test_liftaudit_stop_halts_run.py`; never push. Move the plan to `executed/` through the tooled lifecycle only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
