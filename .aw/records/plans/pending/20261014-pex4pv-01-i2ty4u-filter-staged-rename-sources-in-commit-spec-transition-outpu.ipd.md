# IPD: Filter staged rename sources in commit_spec_transition_output and pin spec transition commits

- Date: 2026-10-14
- Kind: child
- Concern: Backlog item `pex4pv` (`Work-Kind: bug`, `Priority: high`, `Blocks-Release: next`) was filed during execution of IPD `s95x79` (`a6a86e1d81`, `2026-10-13`) when `runner_shared.commit_spec_transition_output` (`def commit_spec_transition_output(` in `agent_workflows/runner_shared.py`, line 3918) called `_run_git(wt, ["add", "--", *allowed])` after `aw specs set <spec> --status implementing --message <msg> --no-commit` relocated the spec from `.aw/records/specs/approved/` to `.aw/records/specs/implementing/` via `git mv`. Because plan `a63epo` (`124b917238`, `2026-10-13`) removed the pre-reset in `status_set._offer_self_commit` (`def _offer_self_commit(` in `agent_workflows/status_set.py`, line 2193), `--no-commit` leaves the rename staged in the index (`RM <old> -> <new>`), so `<old>` is absent from both the working tree and the index and `git add -- <old> <new>` fails with exit code `128` (`fatal: pathspec '<old>' did not match any files`), aborting `commit_spec_transition_output` with `(None, ())`. Commit `a6a86e1d81` (`s95x79`) applied an out-of-scope (`Scope-Exceeded`) edit `add_paths = [p for p in allowed if (wt / p).exists()]` without linking `pex4pv`, omitting the `or _gch._in_index(wt, p)` check used by `runner_shared.commit_backlog_transition_output` (`def commit_backlog_transition_output(` in `agent_workflows/runner_shared.py`, line 4129; its filter at line 4160) and `git_commit_helper.offer_commit` (`def offer_commit(` in `agent_workflows/git_commit_helper.py`, line 972; its `_in_index` filter at lines 1192-1196) for unstaged tracked deletions, and leaving `tests/test_spec_production.py` without unit or end-to-end assertions that `commit_spec_transition_output` actually commits the spec rename.
- Scope: Align `runner_shared.commit_spec_transition_output` (`agent_workflows/runner_shared.py`, lines 3948-3954) with `runner_shared.commit_backlog_transition_output` (`agent_workflows/runner_shared.py`, lines 4158-4165) and `git_commit_helper.offer_commit` (`agent_workflows/git_commit_helper.py`, lines 1192-1196) by filtering `add_paths` with `(wt / p).exists() or _gch._in_index(wt, p)`; add direct unit coverage of `runner_shared.commit_spec_transition_output` in `TestSpecProductionUnitE10` (`tests/test_spec_production.py`, line 250) across staged `git mv` renames (`RM`), unstaged moves (` D` + `??`), and in-place stage notes (`is_note=True`); and tighten `TestSpecProductionE08.test_5_5_success` (`tests/test_spec_production.py`, line 385) and `TestSpecProductionLifecycleArmAndReportE09.test_review_style_integration_asserted` (`tests/test_spec_production.py`, line 1201) on both hosts (`oc` and `agy`) to assert `spec_transition_commit`, the `spec-transition-committed` event, the `R` rename commit in git history, clean porcelain status, and clean lane teardown after moving the spec to `specs/implementing/`.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_spec_production.py, .aw/records/plans/pending/20261014-pex4pv-01-i2ty4u-filter-staged-rename-sources-in-commit-spec-transition-outpu.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: pex4pv
- Blocks-Release: next
- Set: pex4pv
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: i2ty4u
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (/plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed; readiness GO - PENDING HUMAN APPROVAL
- 2026-10-14 to-review (aw set): Authored review-ready child IPD i2ty4u from backlog pex4pv

- 2026-10-14 draft (Antigravity): created.

## Goal

Ensure `runner_shared.commit_spec_transition_output` filters out already-staged `git mv` rename source paths (`not (wt / p).exists() and not _gch._in_index(wt, p)`) while still staging unstaged tracked deletions (`_gch._in_index(wt, p)`) before calling `git add`, matching `runner_shared.commit_backlog_transition_output` and `git_commit_helper.offer_commit`, and pin spec-transition commit creation across unit, non-isolated, and isolated spec-production tests on both runner hosts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Align commit_spec_transition_output and pin spec-transition commits

- [x] E-01 Update `runner_shared.commit_spec_transition_output` (`def commit_spec_transition_output(` in `agent_workflows/runner_shared.py`, lines 3948-3954) to import `git_commit_helper as _gch` before computing `add_paths` and filter `add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]`, matching `runner_shared.commit_backlog_transition_output` (`def commit_backlog_transition_output(` in `agent_workflows/runner_shared.py`, lines 4158-4165) and `git_commit_helper.offer_commit` (`def offer_commit(` in `agent_workflows/git_commit_helper.py`, lines 1192-1196), with a comment explaining why an already-staged `git mv` rename source (`(wt / p).exists() == False` and `_gch._in_index(wt, p) == False`) is excluded from `git add` (preventing `git add` `rc == 128` pathspec failure, backlog `pex4pv`) while an unstaged tracked deletion (`_gch._in_index(wt, p) == True`) is staged before `git commit`.
  - Depends on: none
  - Expected outcome: `runner_shared.commit_spec_transition_output` filters `add_paths` via `(wt / p).exists() or _gch._in_index(wt, p)`, preventing `git add` pathspec failures on staged `git mv` rename sources while staging unstaged tracked deletions into the index prior to `git commit`.
  - Execution state: performed

- [x] E-02 In `TestSpecProductionUnitE10` (`class TestSpecProductionUnitE10(unittest.TestCase):` in `tests/test_spec_production.py`, line 250), add `test_commit_spec_transition_output_staged_rename_unstaged_move_and_note(self) -> None` covering three cases in scratch git repositories (`_make_test_repo`, each inside `tempfile.TemporaryDirectory()`):
    1. **Staged `git mv` rename (`RM <old> -> <new>`)**: commit an `approved` spec (`spc010`) and a linked conforming plan (`_write_conforming_plan(repo, id6="pln010", spec_id6="spc010")`; without it `specs set` refuses with `[no-handoff]`, measured at review), run `cli.main(["specs", "set", rel_spec, "--status", "implementing", "--message", "produced: pln010", "--no-commit", "--dir", str(repo)])` (assert it returns `0`), assert `git status --porcelain --untracked-files=all` contains an `RM` rename line `specs/approved/... -> specs/implementing/...`, then invoke `runner_shared.commit_spec_transition_output(repo, "spc010", spec_path, run_id="run-unit-1", host_label="aw oc run")`. Assert it returns `(sha, (old_rel, new_rel))` with a non-empty `sha`, `git show --name-status -M --format=%B HEAD` records subject `transition(spec): move spc010 -> implementing`, trailers `AW-Run: run-unit-1`, `AW-Item: spc010`, and `AW-Committed-By: driver`, and a single `R` rename line `specs/approved/... -> specs/implementing/...`, and `git status --porcelain` has no entry other than untracked `??` lines (the setter leaves `?? .aw/records/history.jsonl`, measured at review).
    2. **Unstaged move (` D <old>` + `?? <new>`)**: commit an `approved` spec (`spc011`), move it to `specs/implementing/` via filesystem write and `unlink()` without `git mv` (leaving ` D .aw/records/specs/approved/...` and `?? .aw/records/specs/implementing/...` in porcelain). (2a) Invoke `runner_shared.commit_spec_transition_output(repo, "spc011", dest_path, run_id="run-unit-2", host_label="aw agy run")` and assert it returns `(sha, (old_rel, new_rel))` with a non-empty `sha` and `git show --name-status -M --format=%s HEAD` records `transition(spec): move spc011 -> implementing` with a single `R` rename. (2b) In a fresh repository with the same unstaged move, install an executable `.git/hooks/pre-commit` that exits `1`, invoke the function again, and assert it returns `(None, (old_rel, new_rel))` and that `git status --porcelain` then shows exactly one staged rename line `R  <old> -> <new>` and no ` D ` line. (2b) is the observable consequence of the `_gch._in_index` branch: `git commit -- <paths>` commits working-tree state, so the SUCCESSFUL commit is identical with or without that branch (measured at review: both give `R089`); only the index left behind by a REJECTED commit differs (` D <old>` + `A  <new>` without it, `R  <old> -> <new>` with it).
    3. **In-place stage note (`is_note=True`)**: on the `implementing` spec (`spc010`) from case 1, run `cli.main(["specs", "note", str(new_spec_path), "--message", "stage planned by run run-unit-3: pln012"])` with the ABSOLUTE spec path (`specs note` has no `--dir` option: passing one exits `2` with `unrecognized arguments`, measured at review) and assert it returns `0`, then invoke `runner_shared.commit_spec_transition_output(repo, "spc010", new_spec_path, run_id="run-unit-3", is_note=True, host_label="aw oc run")`. Assert it returns `(sha, (new_rel,))` and `git show --name-status --format=%s HEAD` records `note(spec): record planned stage for spc010` modifying only `new_rel`.
  - Depends on: E-01
  - Expected outcome: `tests/test_spec_production.py` directly tests `commit_spec_transition_output` across the staged rename, unstaged move (successful and hook-rejected), and in-place note shapes.
  - Execution state: performed

- [x] E-03 Tighten the two end-to-end spec-production tests in `tests/test_spec_production.py` on both hosts (`oc` and `agy`, via the existing `_HOSTS` loop):
  - In `TestSpecProductionE08.test_5_5_success` (`def test_5_5_success(self):`, line 385, non-isolated), assert that `item["attempts"][0].get("spec_transition_commit")` is a non-empty commit SHA, `events.jsonl` contains a `"spec-transition-committed"` event with `"commit": item["attempts"][0]["spec_transition_commit"]`, `git show --name-status -M --format=%s <spec_transition_commit>` has subject `transition(spec): move spc101 -> implementing` and a single `R` rename line `specs/approved/... -> specs/implementing/...`, and `git status --porcelain` has no non-`??` entry for `spc101`.
  - In `TestSpecProductionLifecycleArmAndReportE09.test_review_style_integration_asserted` (`def test_review_style_integration_asserted(self):`, line 1201, isolated worktree), assert that `item["attempts"][0].get("spec_transition_commit")` is a non-empty commit SHA, `"preserved_worktree"` is not in `item` (lane tore down cleanly), and in `repo` after integration `spc202` resides under `.aw/records/specs/implementing/` with `- Status: implementing` and no copy under `.aw/records/specs/approved/`.
  - Depends on: E-01
  - Expected outcome: on both hosts, non-isolated and isolated spec-production runs are shown to commit and integrate the `approved -> implementing` spec rename; a silent `None` from `commit_spec_transition_output` now fails these tests instead of leaving an `executed` item with an untransitioned spec.
  - Execution state: performed

- [x] E-04 Perform failure-sensitivity verification and run full repository validation:
  - Sensitivity check (1) (pre-fix bug from `pex4pv`): temporarily replace the `add_paths` block in `runner_shared.commit_spec_transition_output` (`agent_workflows/runner_shared.py`, lines 3948-3954) with `rc, _out, _err = _run_git(wt, ["add", "--", *allowed]); if rc != 0: return None, ()`, run `python3 -m pytest -o addopts="" tests/test_spec_production.py -k "test_commit_spec_transition_output_staged_rename_unstaged_move_and_note or test_5_5_success or test_review_style_integration_asserted"`, and verify all three tests fail on both host subtests (review emulated this mutation: the non-isolated run recorded no `spec_transition_commit` and no `spec-transition-committed` event and left `RM` staged; the isolated run kept `spc202` under `specs/approved/` and set `preserved_worktree`; both still ended `executed`).
  - Sensitivity check (2) (`_in_index` unstaged-deletion branch): temporarily replace the `add_paths` filter in `runner_shared.commit_spec_transition_output` with `add_paths = [p for p in allowed if (wt / p).exists()]` (omitting `or _gch._in_index(wt, p)`), run `python3 -m pytest -o addopts="" tests/test_spec_production.py -k test_commit_spec_transition_output_staged_rename_unstaged_move_and_note`, and verify subcase (2b) fails because the rejected commit leaves ` D <old>` + `A  <new>` instead of `R  <old> -> <new>` (measured at review). Restore `E-01`'s implementation after both sensitivity checks with `git checkout -- agent_workflows/runner_shared.py` followed by re-applying E-01 (or by reverting only the mutated lines), and confirm `git diff -- agent_workflows/runner_shared.py` shows exactly the E-01 change. Neither mutation is ever committed.
  - Run `python3 -m pytest -o addopts="" tests/test_spec_production.py tests/test_implementing_spec_replan.py tests/test_production_baseline_same_commit.py`, `python3 -m unittest discover -s tests -t . -p test_spec_production.py -v`, `aw check release-gates`, `aw sanitize --agent`, and the bare repository test suite (`python3 -m pytest`).
  - Depends on: E-01, E-02, E-03
  - Expected outcome: Both sensitivity checks fail as expected when the corresponding code is reverted and pass once `E-01` is restored; targeted pytest modules, `unittest discover`, `aw check release-gates`, `aw sanitize --agent`, and bare `python3 -m pytest` all exit `0`.
  - Execution state: performed

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
| F-02 | In `runner_shared.commit_spec_transition_output` (`def commit_spec_transition_output(` in `agent_workflows/runner_shared.py`, lines 3918-3954), `status_paths` splits `old -> new` into both endpoints. Passing `*allowed` directly to `git add --` failed with `rc == 128` (`fatal: pathspec '.aw/records/specs/approved/...' did not match any files`), causing `commit_spec_transition_output` to return `(None, ())`. During execution of `s95x79` (`a6a86e1d81`, `2026-10-13`), the executor filed `pex4pv` as an out-of-scope defect (`Scope-Exceeded`) and patched `commit_spec_transition_output` with `add_paths = [p for p in allowed if (wt / p).exists()]` without linking `pex4pv`, omitting `or _gch._in_index(wt, p)` which `runner_shared.commit_backlog_transition_output` (`def commit_backlog_transition_output(` in `agent_workflows/runner_shared.py`, line 4129; its filter at line 4160) and `git_commit_helper.offer_commit` (`def offer_commit(` in `agent_workflows/git_commit_helper.py`, line 972; its `_in_index` filter at lines 1192-1196) use. | `git show a6a86e1d811e19e2a4e2ed2140a9d559868acd41 -- agent_workflows/runner_shared.py`; `git show 124b9172380c6363c1fe29bdab9f45693c20dd55 -- agent_workflows/runner_shared.py`. |
| F-03 | Comparing `add_paths = [p for p in allowed if (wt / p).exists()]` vs `add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]` (`git_commit_helper._in_index` at `def _in_index(` in `agent_workflows/git_commit_helper.py`, line 898): for a staged `git mv` rename (`RM`), `_in_index(wt, old)` is `False` so both expressions pass only `[new]` to `git add`. However, for an unstaged move (` D <old>` + `?? <new>`, such as a `shutil.move` fallback or post-reset tree), `_in_index(wt, old)` is `True` while `(wt / old).exists()` is `False`; omitting `or _gch._in_index(wt, p)` skips `<old>` in `git add`, leaving ` D <old>` unstaged and `A  <new>` staged after `git add`, whereas including it stages the full rename `R  <old> -> <new>`. Because the commit is `git commit -- *allowed` (which commits the working-tree state of the named paths), a SUCCESSFUL commit is identical either way; the difference is observable only in the index a REJECTED commit leaves behind (re-measured at review with a pre-commit hook that exits 1: ` D <old>` + `A  <new>` without the branch, `R  <old> -> <new>` with it). The fix is therefore consistency and failure-state hygiene, not the primary `pex4pv` defect, which `a6a86e1d81` already fixed at HEAD. | Measured in scratch repo at HEAD `23b2a63af`: after `git add -- *add_paths` on an unstaged move (` D` + `??`), `use_in_index=False` leaves ` D .aw/records/specs/approved/...` + `A  .aw/records/specs/implementing/...` in `git status --porcelain`, whereas `use_in_index=True` produces `R  .aw/records/specs/approved/... -> .aw/records/specs/implementing/...`. |
| F-04 | `tests/test_spec_production.py` did not fail when `a63epo` (`124b917238`) broke `commit_spec_transition_output` because: (1) `TestSpecProductionE08.test_5_5_success` (`tests/test_spec_production.py`, line 385) ran with `--no-isolate-worktree` and only checked `repo.glob(...)` on disk without asserting `attempt["spec_transition_commit"]`, the `spec-transition-committed` event, or clean git status; (2) `TestSpecProductionLifecycleArmAndReportE09.test_review_style_integration_asserted` (`tests/test_spec_production.py`, line 1201, isolated) only asserted `item["status"] == "executed"` and `item["prod_integrated"] == True`, missing that `spc202` in `repo` remained in `specs/approved/` with `- Status: approved` and that the dirty lane was preserved (`item["preserved_worktree"]`); and (3) no unit test called `commit_spec_transition_output` directly. | `tests/test_spec_production.py`, lines 385-458 and 1201-1252. |

## Proposed changes (ordered, validatable)

1. Update `runner_shared.commit_spec_transition_output` (`agent_workflows/runner_shared.py`, lines 3948-3954) to import `git_commit_helper as _gch` ahead of `add_paths` and filter `add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]`, matching `runner_shared.commit_backlog_transition_output` (`E-01`).
2. Add `TestSpecProductionUnitE10.test_commit_spec_transition_output_staged_rename_unstaged_move_and_note` (`E-02`).
3. Tighten `TestSpecProductionE08.test_5_5_success` and `TestSpecProductionLifecycleArmAndReportE09.test_review_style_integration_asserted` in `tests/test_spec_production.py` (`E-03`).
4. Run both failure-sensitivity checks, targeted production test suites, `unittest discover`, `aw check release-gates`, `aw sanitize --agent`, and the bare repository test suite (`E-04`).

## Deferred / out of scope (with reason)

- Changing `runner_shared.execute_item_core` (`agent_workflows/runner_shared.py`, lines 41187-41220) to treat a `None` return from `commit_spec_transition_output` as a `fail-gate` disposition: backlog item `pex4pv` scopes the defect and fix specifically to `commit_spec_transition_output` mirroring `commit_backlog_transition_output`, and `execute_item_core`'s backlog branch (`if bkl_trans_commit:` in `runner_shared.execute_item_core`, near line 37030) uses the same conditional pattern.
  - Carrier-Declined: changing the disposition contract of spec production (and its backlog twin) is a spec `25kzda` Section 5.5 decision outside `pex4pv`; the E-03 assertions now make a silent `None` from `commit_spec_transition_output` fail the suite on both hosts, so this defect class can no longer pass unnoticed.

## Scope check

- Over-scope: none.
- Under-scope: none. Both `agent_workflows/runner_shared.py` (`commit_spec_transition_output`) and `tests/test_spec_production.py` (unit and end-to-end spec production tests on both hosts) are declared in `- Scope-Paths:`.

## Required tests / validation

- Targeted pytest run: `python3 -m pytest -o addopts="" tests/test_spec_production.py tests/test_implementing_spec_replan.py tests/test_production_baseline_same_commit.py`.
- Stdlib `unittest` discovery run: `python3 -m unittest discover -s tests -t . -p test_spec_production.py -v`.
- Sensitivity checks in `E-04` proving that (1) reverting `add_paths` to `rc, _out, _err = _run_git(wt, ["add", "--", *allowed])` fails `test_commit_spec_transition_output_staged_rename_unstaged_move_and_note`, `test_5_5_success`, and `test_review_style_integration_asserted`, and (2) omitting `or _gch._in_index(wt, p)` fails subcase (2b) of `test_commit_spec_transition_output_staged_rename_unstaged_move_and_note`.
- Full repository suite and checks: bare `python3 -m pytest`, `aw check release-gates`, and `aw sanitize --agent`.

## Spec / documentation sync

N/A for `.spec.md` files and `CHANGELOG.md`: spec `25kzda` Section 5.5 already specifies that a passing spec-production turn transitions an `approved` spec to `implementing` via the setter and commits the transition in the lane before integration, and `CHANGELOG.md` already records the `a63epo` staged-rename behavior under `## 2.0.0 (pending)`. Internal comment documentation in `runner_shared.commit_spec_transition_output` is updated in `E-01`.

## Open questions

### OQ-01: Since commit `a6a86e1d81` (`s95x79`) already added `add_paths = [p for p in allowed if (wt / p).exists()]` to `commit_spec_transition_output` out-of-scope without linking `pex4pv`, what remains to graduate and close `pex4pv`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence (`git show a6a86e1d81`, `git show 124b917238`, `agent_workflows/runner_shared.py` lines 3948-3954 and 4158-4165, `tests/test_spec_production.py`). First, `pex4pv` carries `- Work-Kind: bug` and `- Blocks-Release: next`, so `check_engine.evaluate_blocking_close` requires a linked carrier (`- From-Backlog: pex4pv`, `- Blocks-Release: next`) that executes to completion. Second, `a6a86e1d81` omitted `or _gch._in_index(wt, p)` (unlike `commit_backlog_transition_output` and `git_commit_helper.offer_commit`, `F-02`/`F-03`) and added no unit or end-to-end assertions in `tests/test_spec_production.py` (`F-04`); `E-01`..`E-04` close both gaps.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted `git diff -- agent_workflows/runner_shared.py` showing `runner_shared.commit_spec_transition_output` importing `git_commit_helper as _gch` and filtering `add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]` with the explanatory comment citing `pex4pv`.
  - Observed evidence:
```diff
diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
index d6c3706d5..ba01463ed 100644
--- a/agent_workflows/runner_shared.py
+++ b/agent_workflows/runner_shared.py
@@ -3945,12 +3945,17 @@ def commit_spec_transition_output(
     if not allowed:
         return None, ()

-    add_paths = [p for p in allowed if (wt / p).exists()]
+    from agent_workflows import git_commit_helper as _gch
+
+    # Filter paths for git add (pex4pv): when a spec transitions, 'specs set --no-commit'
+    # renames the file via git mv, leaving the old path staged as deleted (RM). Passing
+    # the old path to git add fails with pathspec errors. Only add paths that exist on disk
+    # or are in the index (to stage unstaged deletions).
+    add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]
     if add_paths:
         rc, _out, _err = _run_git(wt, ["add", "--", *add_paths])
         if rc != 0:
             return None, ()
-    from agent_workflows import git_commit_helper as _gch

     if is_note:
         subject = f"note(spec): record planned stage for {spec_id6}"
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted `git diff -- tests/test_spec_production.py` showing the new unit test, and pasted output of `python3 -m pytest -o addopts="" -v tests/test_spec_production.py -k test_commit_spec_transition_output_staged_rename_unstaged_move_and_note` showing it PASSED (the test calls `runner_shared.commit_spec_transition_output` directly, created by this E-item).
  - Observed evidence:
```diff
+    def test_commit_spec_transition_output_staged_rename_unstaged_move_and_note(
+        self,
+    ) -> None:
+        # Case 1: Staged git mv rename (RM <old> -> <new>) and Case 3: In-place stage note
+        with tempfile.TemporaryDirectory() as td:
+            repo = _make_test_repo(Path(td))
+            spec_path = _write_spec(repo, id6="spc010", status="approved")
+            _write_conforming_plan(repo, id6="pln010", spec_id6="spc010")
+            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
+            subprocess.run(
+                ["git", "commit", "-qm", "add spec and plan"], cwd=repo, check=True
+            )
+
+            rel_spec = str(spec_path.relative_to(repo))
+            rc = cli.main(
+                [
+                    "specs",
+                    "set",
+                    rel_spec,
+                    "--status",
+                    "implementing",
+                    "--message",
+                    "produced: pln010",
+                    "--no-commit",
+                    "--dir",
+                    str(repo),
+                ]
+            )
+            self.assertEqual(rc, 0)
+
+            st_proc = subprocess.run(
+                ["git", "status", "--porcelain", "--untracked-files=all"],
+                cwd=repo,
+                capture_output=True,
+                text=True,
+                check=True,
+            )
+            rm_lines = [
+                line
+                for line in st_proc.stdout.splitlines()
+                if line.startswith("RM ")
+                and "specs/approved/" in line
+                and "specs/implementing/" in line
+            ]
+            self.assertEqual(len(rm_lines), 1, st_proc.stdout)
+
+            sha, rel_paths = runner_shared.commit_spec_transition_output(
+                repo, "spc010", spec_path, run_id="run-unit-1", host_label="aw oc run"
+            )
+            self.assertTrue(sha)
+            self.assertEqual(len(rel_paths), 2)
+            old_rel, new_rel = rel_paths
+            self.assertIn("specs/approved/", old_rel)
+            self.assertIn("specs/implementing/", new_rel)
+
+            show_proc = subprocess.run(
+                ["git", "show", "--name-status", "-M", "--format=%B", "HEAD"],
+                cwd=repo,
+                capture_output=True,
+                text=True,
+                check=True,
+            )
+            show_out = show_proc.stdout
+            self.assertIn("transition(spec): move spc010 -> implementing", show_out)
+            self.assertIn("AW-Run: run-unit-1", show_out)
+            self.assertIn("AW-Item: spc010", show_out)
+            self.assertIn("AW-Committed-By: driver", show_out)
+            r_lines = [
+                line
+                for line in show_out.splitlines()
+                if line.startswith("R")
+                and "specs/approved/" in line
+                and "specs/implementing/" in line
+            ]
+            self.assertEqual(len(r_lines), 1, show_out)
+
+            st_after = subprocess.run(
+                ["git", "status", "--porcelain"],
+                cwd=repo,
+                capture_output=True,
+                text=True,
+                check=True,
+            )
+            non_untracked = [
+                line
+                for line in st_after.stdout.splitlines()
+                if not line.startswith("?? ")
+            ]
+            self.assertEqual(non_untracked, [])
+
+            # Case 3: In-place stage note (is_note=True)
+            new_spec_path = repo / new_rel
            rc_note = cli.main(
+                [
+                    "specs",
+                    "note",
+                    str(new_spec_path),
+                    "--message",
+                    "stage planned by run run-unit-3: pln012",
+                ]
+            )
+            self.assertEqual(rc_note, 0)
+
+            sha_note, rel_paths_note = runner_shared.commit_spec_transition_output(
+                repo,
+                "spc010",
+                new_spec_path,
+                run_id="run-unit-3",
+                is_note=True,
+                host_label="aw oc run",
+            )
+            self.assertTrue(sha_note)
+            self.assertEqual(rel_paths_note, (new_rel,))
+
+            show_note = subprocess.run(
+                ["git", "show", "--name-status", "--format=%s", "HEAD"],
+                cwd=repo,
+                capture_output=True,
+                text=True,
+                check=True,
+            )
+            note_lines = show_note.stdout.strip().splitlines()
+            self.assertEqual(
+                note_lines[0], "note(spec): record planned stage for spc010"
+            )
+            mod_lines = [line for line in note_lines[1:] if line.strip()]
+            self.assertEqual(len(mod_lines), 1)
+            self.assertEqual(mod_lines[0].split()[-1], new_rel)
+
+        # Case 2: Unstaged move ( D <old> + ?? <new>)
+        # (2a) Successful unstaged move commit
+        with tempfile.TemporaryDirectory() as td:
+            repo = _make_test_repo(Path(td))
+            spec_path = _write_spec(repo, id6="spc011", status="approved")
+            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
+            subprocess.run(
+                ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
+            )
+
+            content = spec_path.read_text(encoding="utf-8")
+            spec_path.unlink()
+            dest_path = (
+                repo
+                / ".aw"
+                / "records"
+                / "specs"
+                / "implementing"
+                / spec_path.name
+            )
+            dest_path.parent.mkdir(parents=True, exist_ok=True)
+            dest_path.write_text(content, encoding="utf-8")
+
+            old_rel = str(spec_path.relative_to(repo))
+            new_rel = str(dest_path.relative_to(repo))
+
+            st_unstaged = subprocess.run(
+                ["git", "status", "--porcelain", "--untracked-files=all"],
+                cwd=repo,
+                capture_output=True,
+                text=True,
+                check=True,
+            )
+            self.assertIn(f" D {old_rel}", st_unstaged.stdout)
+            self.assertIn(f"?? {new_rel}", st_unstaged.stdout)
+
+            sha_2a, rel_paths_2a = runner_shared.commit_spec_transition_output(
+                repo,
+                "spc011",
+                dest_path,
+                run_id="run-unit-2",
+                host_label="aw agy run",
+            )
+            self.assertTrue(sha_2a)
+            self.assertEqual(rel_paths_2a, (old_rel, new_rel))
+
+            show_2a = subprocess.run(
+                ["git", "show", "--name-status", "-M", "--format=%s", "HEAD"],
+                cwd=repo,
+                capture_output=True,
+                text=True,
+                check=True,
+            )
+            lines_2a = show_2a.stdout.strip().splitlines()
+            self.assertEqual(
+                lines_2a[0], "transition(spec): move spc011 -> implementing"
+            )
+            r_lines_2a = [
+                ln
+                for ln in lines_2a[1:]
+                if ln.startswith("R") and old_rel in ln and new_rel in ln
+            ]
+            self.assertEqual(len(r_lines_2a), 1, show_2a.stdout)
+
+        # (2b) Unstaged move with rejecting pre-commit hook
+        with tempfile.TemporaryDirectory() as td:
+            repo = _make_test_repo(Path(td))
+            spec_path = _write_spec(repo, id6="spc011", status="approved")
+            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
+            subprocess.run(
+                ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
+            )
+
+            content = spec_path.read_text(encoding="utf-8")
+            spec_path.unlink()
+            dest_path = (
+                repo
+                / ".aw"
+                / "records"
+                / "specs"
+                / "implementing"
+                / spec_path.name
+            )
+            dest_path.parent.mkdir(parents=True, exist_ok=True)
+            dest_path.write_text(content, encoding="utf-8")
+
+            old_rel = str(spec_path.relative_to(repo))
+            new_rel = str(dest_path.relative_to(repo))
+
+            hook_path = repo / ".git" / "hooks" / "pre-commit"
+            hook_path.parent.mkdir(parents=True, exist_ok=True)
+            hook_path.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
+            hook_path.chmod(0o755)
+
+            sha_2b, rel_paths_2b = runner_shared.commit_spec_transition_output(
+                repo,
+                "spc011",
+                dest_path,
+                run_id="run-unit-2",
+                host_label="aw agy run",
+            )
+            self.assertIsNone(sha_2b)
+            self.assertEqual(rel_paths_2b, (old_rel, new_rel))
+
+            st_2b = subprocess.run(
+                ["git", "status", "--porcelain"],
+                cwd=repo,
+                capture_output=True,
+                text=True,
+                check=True,
+            )
+            st_2b_lines = [
+                ln.strip() for ln in st_2b.stdout.splitlines() if ln.strip()
+            ]
+            self.assertEqual(
+                st_2b_lines,
+                [f"R  {old_rel} -> {new_rel}"],
+                st_2b.stdout,
+            )
+            self.assertFalse(
+                any(ln.startswith(" D ") or ln.startswith("D ") for ln in st_2b_lines)
+            )
```
```
$ python3 -m pytest -o addopts="" -v tests/test_spec_production.py -k test_commit_spec_transition_output_staged_rename_unstaged_move_and_note
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
cachedir: .pytest_cache
Using --randomly-seed=2842385264
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/i2ty4u
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collecting 4 items                                                             collected 20 items / 19 deselected / 1 selected

tests/test_spec_production.py::TestSpecProductionUnitE10::test_commit_spec_transition_output_staged_rename_unstaged_move_and_note PASSED [100%]

NOTE: 19 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
======================= 1 passed, 19 deselected in 4.04s =======================
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted `git diff -- tests/test_spec_production.py` hunks for `test_5_5_success` and `test_review_style_integration_asserted`, and pasted outputs of (1) `python3 -m pytest -o addopts="" -v tests/test_spec_production.py` and (2) `python3 -m unittest discover -s tests -t . -p test_spec_production.py -v`, both showing all tests passing with exit code `0` (the runs are produced by `oc_runipd.run_queue` / `agy_runipd.run_queue` reaching `runner_shared.execute_item_core`'s spec-transition branch, as the existing tests already do).
  - Observed evidence:
```diff
@@ -709,6 +709,64 @@ class TestSpecProductionE08(unittest.TestCase):
                     self.assertEqual(gen_acts[0]["id6"], "pln101")
                     self.assertEqual(gen_acts[0]["from_spec"], "spc101")

+                    # Assert spec transition commit
+                    spec_commit = item["attempts"][0].get("spec_transition_commit")
+                    self.assertTrue(spec_commit)
+                    events = [
+                        json.loads(line)
+                        for line in (run_dir / "events.jsonl")
+                        .read_text(encoding="utf-8")
+                        .splitlines()
+                        if line.strip()
+                    ]
+                    self.assertTrue(
+                        any(
+                            e.get("event") == "spec-transition-committed"
+                            and e.get("commit") == spec_commit
+                            for e in events
+                        )
+                    )
+                    show_out = subprocess.run(
+                        [
+                            "git",
+                            "show",
+                            "--name-status",
+                            "-M",
+                            "--format=%s",
+                            spec_commit,
+                        ],
+                        cwd=repo,
+                        capture_output=True,
+                        text=True,
+                        check=True,
+                    ).stdout
+                    show_lines = show_out.strip().splitlines()
+                    self.assertEqual(
+                        show_lines[0], "transition(spec): move spc101 -> implementing"
+                    )
+                    rename_lines = [
+                        ln
+                        for ln in show_lines[1:]
+                        if ln.startswith("R")
+                        and "specs/approved/" in ln
+                        and "specs/implementing/" in ln
+                    ]
+                    self.assertEqual(len(rename_lines), 1, show_out)
+                    status_out = subprocess.run(
+                        ["git", "status", "--porcelain"],
+                        cwd=repo,
+                        capture_output=True,
+                        text=True,
+                        check=True,
+                    ).stdout
+                    self.assertFalse(
+                        any(
+                            "spc101" in ln and not ln.startswith("??")
+                            for ln in status_out.splitlines()
+                        ),
+                        status_out,
+                    )
+
@@ -1560,6 +1560,22 @@ class TestSpecProductionLifecycleArmAndReportE09(unittest.TestCase):
                     self.assertEqual(item["status"], "executed")
                     self.assertTrue(item.get("prod_integrated"))
                     self.assertTrue(item["attempts"][0].get("prod_integrated"))
+                    self.assertTrue(item["attempts"][0].get("spec_transition_commit"))
+                    self.assertNotIn("preserved_worktree", item)
+                    appr_files = list(
+                        repo.glob(
+                            ".aw/records/specs/approved/**/20260927-spc202*.spec.md"
+                        )
+                    )
+                    self.assertEqual(appr_files, [])
+                    impl_files = list(
+                        repo.glob(
+                            ".aw/records/specs/implementing/**/20260927-spc202*.spec.md"
+                        )
+                    )
+                    self.assertEqual(len(impl_files), 1)
+                    impl_txt = impl_files[0].read_text(encoding="utf-8")
+                    self.assertIn("- Status: implementing", impl_txt)
```
```
$ python3 -m pytest -o addopts="" -v tests/test_spec_production.py
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
cachedir: .pytest_cache
Using --randomly-seed=201903118
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/i2ty4u
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 20 items

tests/test_spec_production.py::TestActionPlanEnforcementE07::test_action_plan_legal_for_approved_spec PASSED [  5%]
tests/test_spec_production.py::TestActionPlanEnforcementE07::test_action_plan_illegal_for_plan PASSED [ 10%]
tests/test_spec_production.py::TestSpecProductionUnitE10::test_spec_plan_gate_carry PASSED [ 15%]
tests/test_spec_production.py::TestSpecProductionUnitE10::test_spec_plan_conformance PASSED [ 20%]
tests/test_spec_production.py::TestSpecProductionUnitE10::test_spec_plan_count PASSED [ 25%]
tests/test_spec_production.py::TestSpecProductionUnitE10::test_commit_spec_transition_output_staged_rename_unstaged_move_and_note PASSED [ 30%]
tests/test_spec_production.py::TestSpecProductionE08::test_5_5_refusal_count_missing_from_spec PASSED [ 35%]
tests/test_spec_production.py::TestSpecProductionE08::test_5_5_trace_refusal_missing_requirement PASSED [ 40%]
tests/test_spec_production.py::TestSpecProductionE08::test_5_5_refusal_count_zero PASSED [ 45%]
tests/test_spec_production.py::TestSpecProductionE08::test_5_5_trace_success PASSED [ 50%]
tests/test_spec_production.py::TestSpecProductionE08::test_5_5_trace_unknown_reference PASSED [ 55%]
tests/test_spec_production.py::TestSpecProductionE08::test_duplicate_clause_live_plan_in_baseline PASSED [ 60%]
tests/test_spec_production.py::TestSpecProductionE08::test_5_5_success PASSED [ 65%]
tests/test_spec_production.py::TestSpecProductionE08::test_5_5_refusal_conformance_draft PASSED [ 70%]
tests/test_spec_production.py::TestSpecProductionE08::test_5_5_trace_grandfathered_pass PASSED [ 75%]
tests/test_spec_production.py::TestSpecProductionE08::test_5_5b_gate_carry_both_directions PASSED [ 80%]
tests/test_spec_production.py::TestSpecProductionLifecycleArmAndReportE09::test_no_execute_path_side_effects PASSED [ 85%]
tests/test_spec_production.py::TestSpecProductionLifecycleArmAndReportE09::test_report_only_and_resume_spawns_nothing PASSED [ 90%]
tests/test_spec_production.py::TestSpecProductionLifecycleArmAndReportE09::test_review_style_integration_asserted PASSED [ 95%]
tests/test_spec_production.py::TestSpecProductionLifecycleArmAndReportE09::test_quarantine_lane_preserved_on_failure PASSED [100%]

============================= 20 passed in 36.51s ==============================
```
```
$ python3 -m unittest discover -s tests -t . -p test_spec_production.py -v
test_action_plan_illegal_for_plan (tests.test_spec_production.TestActionPlanEnforcementE07.test_action_plan_illegal_for_plan)
--action plan is illegal for a plan, message names plan and gives plan recovery. ... ok
test_action_plan_legal_for_approved_spec (tests.test_spec_production.TestActionPlanEnforcementE07.test_action_plan_legal_for_approved_spec)
--action plan is legal for an approved spec. ... ok
test_5_5_refusal_conformance_draft (tests.test_spec_production.TestSpecProductionE08.test_5_5_refusal_conformance_draft)
Case (4): fake agent writes plan with - Status: draft -> ends fail-gate with ... ok
test_5_5_refusal_count_missing_from_spec (tests.test_spec_production.TestSpecProductionE08.test_5_5_refusal_count_missing_from_spec)
Case (3): fake agent writes plan lacking From-Spec -> ends fail-gate with SPEC-PLAN-COUNT, ... ok
test_5_5_refusal_count_zero (tests.test_spec_production.TestSpecProductionE08.test_5_5_refusal_count_zero)
Case (2): fake agent writes nothing -> ends fail-gate with SPEC-PLAN-COUNT, ... ok
test_5_5_success (tests.test_spec_production.TestSpecProductionE08.test_5_5_success)
Case (1): fake agent writes one conformant to-review plan carrying From-Spec; ... ok
test_5_5_trace_grandfathered_pass (tests.test_spec_production.TestSpecProductionE08.test_5_5_trace_grandfathered_pass)
Case: pre-cutover spec predating cutover; plan omits requirements -> passes. ... ok
test_5_5_trace_refusal_missing_requirement (tests.test_spec_production.TestSpecProductionE08.test_5_5_trace_refusal_missing_requirement)
Case: post-cutover spec; plan omits R-2 -> fail-gate with SPEC-PLAN-TRACE, lane preserved. ... ok
test_5_5_trace_success (tests.test_spec_production.TestSpecProductionE08.test_5_5_trace_success)
Case: post-cutover spec with requirements and ACs; agent produces plan citing all -> executed. ... ok
test_5_5_trace_unknown_reference (tests.test_spec_production.TestSpecProductionE08.test_5_5_trace_unknown_reference)
Case: plan cites an unknown spec requirement -> fail-gate with SPEC-PLAN-TRACE. ... ok
test_5_5b_gate_carry_both_directions (tests.test_spec_production.TestSpecProductionE08.test_5_5b_gate_carry_both_directions)
Case (6): 5.5b both directions of SPEC-PLAN-GATE-CARRY: ... ok
test_duplicate_clause_live_plan_in_baseline (tests.test_spec_production.TestSpecProductionE08.test_duplicate_clause_live_plan_in_baseline)
Case (5): live plan with same From-Spec already exists in baseline -> fails SPEC-PLAN-COUNT, ... ok
test_no_execute_path_side_effects (tests.test_spec_production.TestSpecProductionLifecycleArmAndReportE09.test_no_execute_path_side_effects)
A production turn runs NO suite check, makes NO aw ipd finalize call against spec, ... ok
test_quarantine_lane_preserved_on_failure (tests.test_spec_production.TestSpecProductionLifecycleArmAndReportE09.test_quarantine_lane_preserved_on_failure)
A failed production leaves its isolated lane recorded as preserved in state (F-10). ... ok
test_report_only_and_resume_spawns_nothing (tests.test_spec_production.TestSpecProductionLifecycleArmAndReportE09.test_report_only_and_resume_spawns_nothing)
Report-only (5.5a): queue IDs before == after; generated_next_actions rendered ... ok
test_review_style_integration_asserted (tests.test_spec_production.TestSpecProductionLifecycleArmAndReportE09.test_review_style_integration_asserted)
Production turn takes review-style integration without suite revalidation. ... ok
test_commit_spec_transition_output_staged_rename_unstaged_move_and_note (tests.test_spec_production.TestSpecProductionUnitE10.test_commit_spec_transition_output_staged_rename_unstaged_move_and_note) ... ok
test_spec_plan_conformance (tests.test_spec_production.TestSpecProductionUnitE10.test_spec_plan_conformance) ... ok
test_spec_plan_count (tests.test_spec_production.TestSpecProductionUnitE10.test_spec_plan_count) ... ok
test_spec_plan_gate_carry (tests.test_spec_production.TestSpecProductionUnitE10.test_spec_plan_gate_carry) ... ok

----------------------------------------------------------------------
Ran 20 tests in 36.482s

OK
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted outputs of both sensitivity checks in `E-04` (showing `test_commit_spec_transition_output_staged_rename_unstaged_move_and_note`, `test_5_5_success`, and `test_review_style_integration_asserted` failing when `_run_git(wt, ["add", "--", *allowed])` is restored in `runner_shared.commit_spec_transition_output`, and subcase (2b) failing when `or _gch._in_index(wt, p)` is omitted), followed by passing after restoration and a pasted `git diff -- agent_workflows/runner_shared.py` showing only the E-01 change; plus pasted exit-0 outputs of `python3 -m pytest -o addopts="" tests/test_spec_production.py tests/test_implementing_spec_replan.py tests/test_production_baseline_same_commit.py`, `aw check release-gates`, `aw sanitize --agent`, and bare `python3 -m pytest` with its `N passed` summary line.
  - Observed evidence:
    1. Sensitivity check (1) output with `rc, _out, _err = _run_git(wt, ["add", "--", *allowed])`:
    ```
    $ python3 -m pytest -o addopts="" tests/test_spec_production.py -k "test_commit_spec_transition_output_staged_rename_unstaged_move_and_note or test_5_5_success or test_review_style_integration_asserted"
    =========================== short test summary info ============================
    FAILED tests/test_spec_production.py::TestSpecProductionE08::test_5_5_success
    FAILED tests/test_spec_production.py::TestSpecProductionLifecycleArmAndReportE09::test_review_style_integration_asserted
    FAILED tests/test_spec_production.py::TestSpecProductionUnitE10::test_commit_spec_transition_output_staged_rename_unstaged_move_and_note
    ======================= 3 failed, 17 deselected in 4.59s =======================
    ```

    2. Sensitivity check (2) output omitting `or _gch._in_index(wt, p)`:
    ```
    $ python3 -m pytest -o addopts="" tests/test_spec_production.py -k test_commit_spec_transition_output_staged_rename_unstaged_move_and_note
    =========================== short test summary info ============================
    FAILED tests/test_spec_production.py::TestSpecProductionUnitE10::test_commit_spec_transition_output_staged_rename_unstaged_move_and_note
    ======================= 1 failed, 19 deselected in 2.68s =======================
    ```

    3. Passing after restoration of E-01:
    ```
    $ python3 -m pytest -o addopts="" tests/test_spec_production.py -k test_commit_spec_transition_output_staged_rename_unstaged_move_and_note
    ======================= 1 passed, 19 deselected in 3.16s =======================
    ```

    4. Clean diff on `runner_shared.py`:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index d6c3706d5..ba01463ed 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -3945,12 +3945,17 @@ def commit_spec_transition_output(
         if not allowed:
             return None, ()

    -    add_paths = [p for p in allowed if (wt / p).exists()]
    +    from agent_workflows import git_commit_helper as _gch
    +
    +    # Filter paths for git add (pex4pv): when a spec transitions, 'specs set --no-commit'
    +    # renames the file via git mv, leaving the old path staged as deleted (RM). Passing
    +    # the old path to git add fails with pathspec errors. Only add paths that exist on disk
    +    # or are in the index (to stage unstaged deletions).
    +    add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]
         if add_paths:
             rc, _out, _err = _run_git(wt, ["add", "--", *add_paths])
             if rc != 0:
                 return None, ()
    -    from agent_workflows import git_commit_helper as _gch

         if is_note:
             subject = f"note(spec): record planned stage for {spec_id6}"
    ```

    5. Targeted pytest output:
    ```
    $ python3 -m pytest -o addopts="" tests/test_spec_production.py tests/test_implementing_spec_replan.py tests/test_production_baseline_same_commit.py
    ============================= 31 passed in 53.56s ==============================
    ```

    6. Release gates check:
    ```
    $ aw check release-gates
    AW check  release-gates                                                  1694 ms
    ✓ CONFORMS  156 release-gates checked

    Evidence
      backlog  65   specs  19   plans  71   releases  1
      errors  0   warnings  0   info  0
    ```

    7. Leak sanitize:
    ```
    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5219,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    8. Bare pytest suite:
    ```
    $ python3 -m pytest
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    702 passed in 40.23s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved i2ty4u --by-human`); OQ-01 is resolved and no question blocks. Begin with `aw ipd begin i2ty4u`, then execute `E-01` through `E-04` in dependency order. Do not mark any `E-*` item `performed` before completing its action.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. The E-04 mutations of `agent_workflows/runner_shared.py` are temporary and are never committed. STOP only for a genuinely unsafe condition: `runner_shared.commit_spec_transition_output` or `git_commit_helper._in_index` no longer existing in the shape cited, or a concurrent edit to a Scope-Path that cannot be safely combined.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never mark a `V-*` `pass` without concrete observed output. Run the repository suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`).

Commits: commit only the Scope-Paths files you changed through `aw commit i2ty4u -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the RUNNER performs finalize after its merge-and-revalidate gate, so do not run `aw ipd finalize` yourself. When executing by hand, once `E-01`..`E-04` are `performed`, `V-01`..`V-04` are `pass`, and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize i2ty4u`. Never hand-roll a `git mv`.
