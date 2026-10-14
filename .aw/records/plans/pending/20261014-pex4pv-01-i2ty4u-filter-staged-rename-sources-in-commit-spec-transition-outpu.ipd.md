# IPD: Filter staged rename sources in commit_spec_transition_output and pin spec transition commits

- Date: 2026-10-14
- Kind: child
- Concern: Backlog item `pex4pv` (`Work-Kind: bug`, `Priority: high`, `Blocks-Release: next`) was filed during execution of IPD `s95x79` (`a6a86e1d81`, `2026-10-13`) when `runner_shared.commit_spec_transition_output` (`def commit_spec_transition_output(` in `agent_workflows/runner_shared.py`, line 3918) called `_run_git(wt, ["add", "--", *allowed])` after `aw specs set <spec> --status implementing --message <msg> --no-commit` relocated the spec from `.aw/records/specs/approved/` to `.aw/records/specs/implementing/` via `git mv`. Because plan `a63epo` (`124b917238`, `2026-10-13`) removed the pre-reset in `status_set._offer_self_commit` (`def _offer_self_commit(` in `agent_workflows/status_set.py`, line 2193), `--no-commit` leaves the rename staged in the index (`RM <old> -> <new>`), so `<old>` is absent from both the working tree and the index and `git add -- <old> <new>` fails with exit code `128` (`fatal: pathspec '<old>' did not match any files`), aborting `commit_spec_transition_output` with `(None, ())`. Commit `a6a86e1d81` (`s95x79`) applied an out-of-scope (`Scope-Exceeded`) edit `add_paths = [p for p in allowed if (wt / p).exists()]` without linking `pex4pv`, omitting the `or _gch._in_index(wt, p)` check used by `runner_shared.commit_backlog_transition_output` (`def commit_backlog_transition_output(` in `agent_workflows/runner_shared.py`, line 4160) and `git_commit_helper.offer_commit` (`def offer_commit(` in `agent_workflows/git_commit_helper.py`, line 1192) for unstaged tracked deletions, and leaving `tests/test_spec_production.py` without unit or end-to-end assertions that `commit_spec_transition_output` actually commits the spec rename.
- Scope: Align `runner_shared.commit_spec_transition_output` (`agent_workflows/runner_shared.py`, lines 3948-3954) with `runner_shared.commit_backlog_transition_output` (`agent_workflows/runner_shared.py`, lines 4158-4165) and `git_commit_helper.offer_commit` (`agent_workflows/git_commit_helper.py`, lines 1192-1196) by filtering `add_paths` with `(wt / p).exists() or _gch._in_index(wt, p)`; add direct unit coverage of `runner_shared.commit_spec_transition_output` in `TestSpecProductionUnitE10` (`tests/test_spec_production.py`, line 250) across staged `git mv` renames (`RM`), unstaged moves (` D` + `??`), and in-place stage notes (`is_note=True`); and tighten `TestSpecProductionE08.test_5_5_success` (`tests/test_spec_production.py`, line 385) and `TestSpecProductionLifecycleArmAndReportE09.test_review_style_integration_asserted` (`tests/test_spec_production.py`, line 1201) on both hosts (`oc` and `agy`) to assert `spec_transition_commit`, the `spec-transition-committed` event, the `R` rename commit in git history, clean porcelain status, and clean lane teardown after moving the spec to `specs/implementing/`.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_spec_production.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: pex4pv
- Blocks-Release: next
- Set: pex4pv
- Order: 1
- Highest E allocated: 03
- Author: Antigravity
- Id: i2ty4u

## Workflow history
- 2026-10-14 to-review (aw set): Authored review-ready child IPD i2ty4u from backlog pex4pv

- 2026-10-14 draft (Antigravity): created.

## Goal

Ensure `runner_shared.commit_spec_transition_output` filters out already-staged `git mv` rename source paths (`not (wt / p).exists() and not _gch._in_index(wt, p)`) while still staging unstaged tracked deletions (`_gch._in_index(wt, p)`) before calling `git add`, matching `runner_shared.commit_backlog_transition_output` and `git_commit_helper.offer_commit`, and pin spec-transition commit creation across unit, non-isolated, and isolated spec-production tests on both runner hosts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Align commit_spec_transition_output and pin spec-transition commits

- [ ] E-01 Update `runner_shared.commit_spec_transition_output` (`def commit_spec_transition_output(` in `agent_workflows/runner_shared.py`, lines 3948-3954) to import `git_commit_helper as _gch` before computing `add_paths` and filter `add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]`, matching `runner_shared.commit_backlog_transition_output` (`def commit_backlog_transition_output(` in `agent_workflows/runner_shared.py`, lines 4158-4165) and `git_commit_helper.offer_commit` (`def offer_commit(` in `agent_workflows/git_commit_helper.py`, lines 1192-1196), with a comment explaining why an already-staged `git mv` rename source (`(wt / p).exists() == False` and `_gch._in_index(wt, p) == False`) is excluded from `git add` (preventing `git add` `rc == 128` pathspec failure, backlog `pex4pv`) while an unstaged tracked deletion (`_gch._in_index(wt, p) == True`) is staged before `git commit`.
  - Depends on: none
  - Expected outcome: `runner_shared.commit_spec_transition_output` filters `add_paths` via `(wt / p).exists() or _gch._in_index(wt, p)`, preventing `git add` pathspec failures on staged `git mv` rename sources while staging unstaged tracked deletions into the index prior to `git commit`.
  - Execution state: pending

- [ ] E-02 Add direct unit and end-to-end spec-transition commit assertions in `tests/test_spec_production.py`:
  - In `TestSpecProductionUnitE10` (`class TestSpecProductionUnitE10(unittest.TestCase):` in `tests/test_spec_production.py`, line 250), add `test_commit_spec_transition_output_staged_rename_unstaged_move_and_note(self) -> None` covering three cases in scratch git repositories (`_make_test_repo`):
    1. **Staged `git mv` rename (`RM <old> -> <new>`)**: commit an `approved` spec (`spc010`) and a linked conforming plan (`pln010`), run `cli.main(["specs", "set", rel_spec, "--status", "implementing", "--message", "produced: pln010", "--no-commit", "--dir", str(repo)])`, assert `git status --porcelain --untracked-files=all` contains an `RM` rename line `specs/approved/... -> specs/implementing/...`, then invoke `runner_shared.commit_spec_transition_output(repo, "spc010", spec_path, run_id="run-unit-1", host_label="aw oc run")`. Assert it returns `(sha, (old_rel, new_rel))` with a non-empty `sha`, `git show --name-status -M --format=%B HEAD` records subject `transition(spec): move spc010 -> implementing`, trailers `AW-Run: run-unit-1`, `AW-Item: spc010`, and `AW-Committed-By: driver`, and a single `R` rename line `specs/approved/... -> specs/implementing/...`, and `git status --porcelain` has no tracked entries (`specs/approved/` and `specs/implementing/` absent).
    2. **Unstaged move (` D <old>` + `?? <new>`)**: commit an `approved` spec (`spc011`), move it to `specs/implementing/` via filesystem write and `unlink()` without `git mv` (leaving ` D .aw/records/specs/approved/...` and `?? .aw/records/specs/implementing/...` in porcelain), wrap `runner_shared._run_git` to record `git status --porcelain` immediately after the `["add", "--", ...]` call, and invoke `runner_shared.commit_spec_transition_output(repo, "spc011", dest_path, run_id="run-unit-2", host_label="aw agy run")`. Assert that immediately after `git add` the index already holds a single staged rename (`R` line in porcelain, with no unstaged ` D ` entry left behind), that `commit_spec_transition_output` returns `(sha, (old_rel, new_rel))` with a non-empty `sha`, and that `git show --name-status -M --format=%s HEAD` records `transition(spec): move spc011 -> implementing` with a single `R` rename.
    3. **In-place stage note (`is_note=True`)**: on the `implementing` spec (`spc010`), run `cli.main(["specs", "note", new_rel, "--message", "stage planned by run run-unit-3: pln012", "--dir", str(repo)])` and invoke `runner_shared.commit_spec_transition_output(repo, "spc010", new_spec_path, run_id="run-unit-3", is_note=True, host_label="aw oc run")`. Assert it returns `(sha, (new_rel,))` and `git show --name-status --format=%s HEAD` records `note(spec): record planned stage for spc010` modifying only `new_rel`.
  - In `TestSpecProductionE08.test_5_5_success` (`def test_5_5_success(self):` in `tests/test_spec_production.py`, line 385, non-isolated on both `oc` and `agy`), assert that `item["attempts"][0].get("spec_transition_commit")` is a non-empty commit SHA, `events.jsonl` contains a `"spec-transition-committed"` event with `"commit": item["attempts"][0]["spec_transition_commit"]`, `git show --name-status -M --format=%s <spec_transition_commit>` has subject `transition(spec): move spc101 -> implementing` and a single `R` rename line `specs/approved/... -> specs/implementing/...`, and `git status --porcelain` has no tracked entry for `spc101`.
  - In `TestSpecProductionLifecycleArmAndReportE09.test_review_style_integration_asserted` (`def test_review_style_integration_asserted(self):` in `tests/test_spec_production.py`, line 1201, isolated worktree on both `oc` and `agy`), assert that `item["attempts"][0].get("spec_transition_commit")` is a non-empty commit SHA, `"preserved_worktree"` is not in `item` (lane tore down cleanly), and in `repo` after integration `spc202` resides under `.aw/records/specs/implementing/` with `- Status: implementing` and no copy under `.aw/records/specs/approved/`.
  - Depends on: E-01
  - Expected outcome: `tests/test_spec_production.py` directly tests `commit_spec_transition_output` across staged rename, unstaged move, and in-place note shapes and verifies on both hosts (`oc` and `agy`) that non-isolated and isolated spec-production runs commit and integrate the `approved -> implementing` spec rename cleanly.
  - Execution state: pending

- [ ] E-03 Perform failure-sensitivity verification and run full repository validation:
  - Sensitivity check (1) (pre-fix bug from `pex4pv`): temporarily replace the `add_paths` block in `runner_shared.commit_spec_transition_output` (`agent_workflows/runner_shared.py`, lines 3948-3954) with `rc, _out, _err = _run_git(wt, ["add", "--", *allowed]); if rc != 0: return None, ()`, run `python3 -m pytest -o addopts="" tests/test_spec_production.py -k "test_commit_spec_transition_output_staged_rename_unstaged_move_and_note or test_5_5_success or test_review_style_integration_asserted"`, and verify all three tests fail.
  - Sensitivity check (2) (`_in_index` unstaged-deletion branch): temporarily replace the `add_paths` filter in `runner_shared.commit_spec_transition_output` with `add_paths = [p for p in allowed if (wt / p).exists()]` (omitting `or _gch._in_index(wt, p)`), run `python3 -m pytest -o addopts="" tests/test_spec_production.py -k test_commit_spec_transition_output_staged_rename_unstaged_move_and_note`, and verify subcase (2) fails because ` D .aw/records/specs/approved/...` remains unstaged after `git add`. Restore `E-01`'s implementation after both sensitivity checks.
  - Run `python3 -m pytest -o addopts="" tests/test_spec_production.py tests/test_implementing_spec_replan.py tests/test_production_baseline_same_commit.py`, `python3 -m unittest discover -s tests -t . -p test_spec_production.py -v`, `aw check release-gates`, `aw sanitize --agent`, and the bare repository test suite (`python3 -m pytest`).
  - Depends on: E-01, E-02
  - Expected outcome: Both sensitivity checks fail as expected when the corresponding code is reverted and pass once `E-01` is restored; targeted pytest modules, `unittest discover`, `aw check release-gates`, `aw sanitize --agent`, and bare `python3 -m pytest` all exit `0`.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Repository test runner contract (`AGENTS.md` section `## Repository development contract (repo-local rule)`): run the full test suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`). For narrowed runs, clear configured `addopts` explicitly with `python3 -m pytest -o addopts=""`.
- Outcome tests only (`AGENTS.md` section `TEST OUTCOMES, NOT CODE STRUCTURE (NO CODE-PINNING TESTS)`, P16): tests must drive functions, CLI verbs, and git repositories and assert on exit codes, commit SHAs, `git status --porcelain`, `git show`, and runner state/events, never reading source text.
- Code citation convention (`AGENTS.md` and `IPD-C801`): cite code by symbol (`module.function`) or quoted string, with line numbers only appended to a symbol/quote and never alone.
- Release gate handoff (`AGENTS.md` section `### Every live bug gates the next release`): backlog `pex4pv` carries `- Work-Kind: bug` and `- Blocks-Release: next`, so this graduating IPD inherits `- From-Backlog: pex4pv` and `- Blocks-Release: next`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | When a spec transitions from `approved` to `implementing` via `aw specs set <spec> --status implementing --message <msg> --no-commit` (`runner_shared.execute_item_core` in `agent_workflows/runner_shared.py`, lines 41173-41186), `status_set.apply_status_change` moves the file across directories with `artifact_core.git_mv` and edits the destination file. Since plan `a63epo` (`124b917238`, `2026-10-13`) removed the pre-reset in `status_set._offer_self_commit` (`def _offer_self_commit(` in `agent_workflows/status_set.py`, line 2193), `--no-commit` leaves `RM .aw/records/specs/approved/<file> -> .aw/records/specs/implementing/<file>` in `git status --porcelain --untracked-files=all`, where the old path is absent from both the working tree and the index (`(wt / old).exists() == False` and `git_commit_helper._in_index(wt, old) == False`). | Measured in scratch repo at HEAD `23b2a63af`: `cli.main(["specs", "set", rel_spec, "--status", "implementing", "--message", "test", "--no-commit", "--dir", str(repo)])` exits `0` and leaves `RM .aw/records/specs/approved/20260927-spc001-01-spc001-test-spec.spec.md -> .aw/records/specs/implementing/20260927-spc001-01-spc001-test-spec.spec.md`. |
| F-02 | In `runner_shared.commit_spec_transition_output` (`def commit_spec_transition_output(` in `agent_workflows/runner_shared.py`, lines 3918-3954), `status_paths` splits `old -> new` into both endpoints. Passing `*allowed` directly to `git add --` failed with `rc == 128` (`fatal: pathspec '.aw/records/specs/approved/...' did not match any files`), causing `commit_spec_transition_output` to return `(None, ())`. During execution of `s95x79` (`a6a86e1d81`, `2026-10-13`), the executor filed `pex4pv` as an out-of-scope defect (`Scope-Exceeded`) and patched `commit_spec_transition_output` with `add_paths = [p for p in allowed if (wt / p).exists()]` without linking `pex4pv`, omitting `or _gch._in_index(wt, p)` which `runner_shared.commit_backlog_transition_output` (`def commit_backlog_transition_output(` in `agent_workflows/runner_shared.py`, line 4160) and `git_commit_helper.offer_commit` (`def offer_commit(` in `agent_workflows/git_commit_helper.py`, line 1192) use. | `git show a6a86e1d811e19e2a4e2ed2140a9d559868acd41 -- agent_workflows/runner_shared.py`; `git show 124b9172380c6363c1fe29bdab9f45693c20dd55 -- agent_workflows/runner_shared.py`. |
| F-03 | Comparing `add_paths = [p for p in allowed if (wt / p).exists()]` vs `add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]` (`git_commit_helper._in_index` at `def _in_index(` in `agent_workflows/git_commit_helper.py`, line 898): for a staged `git mv` rename (`RM`), `_in_index(wt, old)` is `False` so both expressions pass only `[new]` to `git add`. However, for an unstaged move (` D <old>` + `?? <new>`, such as a `shutil.move` fallback or post-reset tree), `_in_index(wt, old)` is `True` while `(wt / old).exists()` is `False`; omitting `or _gch._in_index(wt, p)` skips `<old>` in `git add`, leaving ` D <old>` unstaged and `A  <new>` staged after `git add` (which causes `pre-commit` to stash and restore `<old>` during hook execution or leaves `<old>` unstaged on commit failure), whereas including `or _gch._in_index(wt, p)` stages the full rename `R  <old> -> <new>` in `git add`. | Measured in scratch repo at HEAD `23b2a63af`: after `git add -- *add_paths` on an unstaged move (` D` + `??`), `use_in_index=False` leaves ` D .aw/records/specs/approved/...` + `A  .aw/records/specs/implementing/...` in `git status --porcelain`, whereas `use_in_index=True` produces `R  .aw/records/specs/approved/... -> .aw/records/specs/implementing/...`. |
| F-04 | `tests/test_spec_production.py` did not fail when `a63epo` (`124b917238`) broke `commit_spec_transition_output` because: (1) `TestSpecProductionE08.test_5_5_success` (`tests/test_spec_production.py`, line 385) ran with `--no-isolate-worktree` and only checked `repo.glob(...)` on disk without asserting `attempt["spec_transition_commit"]`, the `spec-transition-committed` event, or clean git status; (2) `TestSpecProductionLifecycleArmAndReportE09.test_review_style_integration_asserted` (`tests/test_spec_production.py`, line 1201, isolated) only asserted `item["status"] == "executed"` and `item["prod_integrated"] == True`, missing that `spc202` in `repo` remained in `specs/approved/` with `- Status: approved` and that the dirty lane was preserved (`item["preserved_worktree"]`); and (3) no unit test called `commit_spec_transition_output` directly. | `tests/test_spec_production.py`, lines 385-458 and 1201-1252. |

## Proposed changes (ordered, validatable)

1. Update `runner_shared.commit_spec_transition_output` (`agent_workflows/runner_shared.py`, lines 3948-3954) to import `git_commit_helper as _gch` ahead of `add_paths` and filter `add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]`, matching `runner_shared.commit_backlog_transition_output` (`E-01`).
2. Add `TestSpecProductionUnitE10.test_commit_spec_transition_output_staged_rename_unstaged_move_and_note` and tighten `TestSpecProductionE08.test_5_5_success` and `TestSpecProductionLifecycleArmAndReportE09.test_review_style_integration_asserted` in `tests/test_spec_production.py` (`E-02`).
3. Run both failure-sensitivity checks, targeted production test suites, `unittest discover`, `aw check release-gates`, `aw sanitize --agent`, and the bare repository test suite (`E-03`).

## Deferred / out of scope (with reason)

- Changing `runner_shared.execute_item_core` (`agent_workflows/runner_shared.py`, lines 41187-41220) to treat a `None` return from `commit_spec_transition_output` as a `fail-gate` disposition: backlog item `pex4pv` scopes the defect and fix specifically to `commit_spec_transition_output` mirroring `commit_backlog_transition_output`, and `execute_item_core`'s backlog branch (`if bkl_trans_commit:` at line 41913) uses the same conditional pattern.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none. Both `agent_workflows/runner_shared.py` (`commit_spec_transition_output`) and `tests/test_spec_production.py` (unit and end-to-end spec production tests on both hosts) are declared in `- Scope-Paths:`.

## Required tests / validation

- Targeted pytest run: `python3 -m pytest -o addopts="" tests/test_spec_production.py tests/test_implementing_spec_replan.py tests/test_production_baseline_same_commit.py`.
- Stdlib `unittest` discovery run: `python3 -m unittest discover -s tests -t . -p test_spec_production.py -v`.
- Sensitivity checks in `E-03` proving that (1) reverting `add_paths` to `rc, _out, _err = _run_git(wt, ["add", "--", *allowed])` fails `test_commit_spec_transition_output_staged_rename_unstaged_move_and_note`, `test_5_5_success`, and `test_review_style_integration_asserted`, and (2) omitting `or _gch._in_index(wt, p)` fails subcase (2) of `test_commit_spec_transition_output_staged_rename_unstaged_move_and_note`.
- Full repository suite and checks: bare `python3 -m pytest`, `aw check release-gates`, and `aw sanitize --agent`.

## Spec / documentation sync

N/A for `.spec.md` files and `CHANGELOG.md`: spec `25kzda` Section 5.5 already specifies that a passing spec-production turn transitions an `approved` spec to `implementing` via the setter and commits the transition in the lane before integration, and `CHANGELOG.md` already records the `a63epo` staged-rename behavior under `## 2.0.0 (pending)`. Internal comment documentation in `runner_shared.commit_spec_transition_output` is updated in `E-01`.

## Open questions

### OQ-01: Since commit `a6a86e1d81` (`s95x79`) already added `add_paths = [p for p in allowed if (wt / p).exists()]` to `commit_spec_transition_output` out-of-scope without linking `pex4pv`, what remains to graduate and close `pex4pv`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence (`git show a6a86e1d81`, `git show 124b917238`, `agent_workflows/runner_shared.py` lines 3948-3954 and 4158-4165, `tests/test_spec_production.py`). First, `pex4pv` carries `- Work-Kind: bug` and `- Blocks-Release: next`, so `check_engine.evaluate_blocking_close` requires a linked carrier (`- From-Backlog: pex4pv`, `- Blocks-Release: next`) that executes to completion. Second, `a6a86e1d81` omitted `or _gch._in_index(wt, p)` (unlike `commit_backlog_transition_output` and `git_commit_helper.offer_commit`, `F-02`/`F-03`) and added no unit or end-to-end assertions in `tests/test_spec_production.py` (`F-04`); `E-01`..`E-03` close both gaps.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `git diff -- agent_workflows/runner_shared.py` showing `runner_shared.commit_spec_transition_output` importing `git_commit_helper as _gch` and filtering `add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]` with the explanatory comment citing `pex4pv`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- tests/test_spec_production.py` and pasted outputs of (1) `python3 -m pytest -o addopts="" -v tests/test_spec_production.py` (reachable via `TestSpecProductionUnitE10.test_commit_spec_transition_output_staged_rename_unstaged_move_and_note`, `TestSpecProductionE08.test_5_5_success`, and `TestSpecProductionLifecycleArmAndReportE09.test_review_style_integration_asserted` updated in `E-02`) and (2) `python3 -m unittest discover -s tests -t . -p test_spec_production.py -v`, both showing all tests passing with exit code `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted outputs of both sensitivity checks in `E-03` (showing `test_commit_spec_transition_output_staged_rename_unstaged_move_and_note`, `test_5_5_success`, and `test_review_style_integration_asserted` failing when `_run_git(wt, ["add", "--", *allowed])` is restored in `runner_shared.commit_spec_transition_output`, and subcase (2) of `test_commit_spec_transition_output_staged_rename_unstaged_move_and_note` failing when `or _gch._in_index(wt, p)` is omitted, followed by passing after restoration); plus pasted exit-0 outputs of `python3 -m pytest -o addopts="" tests/test_spec_production.py tests/test_implementing_spec_replan.py tests/test_production_baseline_same_commit.py`, `aw check release-gates`, `aw sanitize --agent`, and bare `python3 -m pytest`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Execution contract**: Execute `E-01` through `E-03` in dependency order inside an isolated worktree. Start with `aw ipd begin i2ty4u`. Do not mark any `E-*` item `performed` before completing its action, and do not mark any `V-*` item `pass` without pasting concrete observed command output into `Observed evidence:`. Run the repository suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`). Commit only files listed in `- Scope-Paths:` plus this IPD using `aw commit i2ty4u -- <paths>`, and never push.
- **Post-gate lifecycle move**: Under `aw oc run` / `aw agy run`, the runner performs the finalize after its merge-and-revalidate gate, so the executor must not run `aw ipd finalize`. When executed by hand, once `E-01`..`E-03` are `performed`, `V-01`..`V-03` are `pass`, and `aw ipd lint --phase pre-transition` reports 0 errors, finalize the plan via `aw ipd finalize i2ty4u`.
