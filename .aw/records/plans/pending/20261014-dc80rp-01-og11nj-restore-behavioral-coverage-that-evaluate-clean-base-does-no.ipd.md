# IPD: Restore behavioral coverage that evaluate_clean_base does not refuse on untracked files

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_lane_clean_base.py`, and with it `test_case_3_an_untracked_file_does_NOT_refuse` and `test_both_drivers_agree_on_every_case`, the only behavioral tests that an UNTRACKED file in the target checkout leaves the R5.4 clean-base guard CLEAN (no refusal, no dirty path) on BOTH hosts. Executed plan `yuhl6o` recorded that site as S-09 RETIRE-UNGUARDED. A regression is silent and costly: if the `--untracked-files=no` scope were dropped, every unattended run in an ordinary working checkout would be classified dirty (refused on the shared-tree path), the exact failure spec R5.4 / finding F-4 forbids.
- Scope: Add one new behavioral test module that drives the real `evaluate_clean_base_for_launch` on both hosts against a real temporary git repository and the real `runner_shared.clean_base_launch_decision`, and repoint the one source comment that says "no live guard currently asserts this" for this property. No production behavior change.
- Scope-Paths: tests/test_clean_base_untracked.py, agent_workflows/runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: dc80rp
- Set: dc80rp
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: og11nj

## Workflow history

- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog `dc80rp`; review-ready.

## Goal

Restore behavioral (never source-reading, P16) test coverage that untracked files do not make the R5.4 clean-base guard refuse or report dirty, on both hosts and on both the isolated and shared-tree paths, while a dirty TRACKED file still classifies not-clean, so the guard is proven non-vacuous.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: untracked files leave the base clean (yuhl6o S-09)

- [ ] E-01 Create `tests/test_clean_base_untracked.py` with a `setUp` that `git init`s a temp repo, configures a local user, commits one tracked file (`tracked.txt`), and a test that writes two untracked files (`scratch.log`, `notes.md`) plus one untracked file inside a new subdirectory, then for each host in (`oc_runipd`, `agy_runipd`) and each `shared_tree` in (`False`, `True`) calls `driver.evaluate_clean_base_for_launch(repo, shared_tree=...)` and asserts `result.clean is True`, `result.dirty_paths == ()`, and `result.refuses is False`, and that `runner_shared.clean_base_launch_decision(result).verdict == runner_shared.CLEAN_BASE_PROCEED`.
  - Depends on: none
  - Expected outcome: New module exists; the untracked test passes for all four host x path subtests.
  - Execution state: pending

### Task group 2: non-vacuity and host agreement

- [ ] E-02 In the same module, add a control test: after modifying the committed `tracked.txt` (with the untracked files still present), each host returns `clean is False` and `dirty_paths == ("tracked.txt",)` (the untracked names absent), `refuses` is `True` on `shared_tree=True` and `False` on `shared_tree=False`, and `clean_base_launch_decision` yields `CLEAN_BASE_REFUSE` and `CLEAN_BASE_WARN` respectively. This proves the E-01 assertions are not vacuous (the guard does see the tree).
  - Depends on: E-01
  - Expected outcome: Control passes on both hosts and both paths.
  - Execution state: pending

- [ ] E-03 In the same module, add a host-agreement test that snapshots `(clean, dirty_paths)` from both hosts at three states (clean, untracked only, untracked plus dirty tracked) and asserts both hosts agree at each state and the sequence of `clean` values is `[True, True, False]`. Do not read source files, use `ast`/`inspect`, or pin symbol identity or counts.
  - Depends on: E-02
  - Expected outcome: Agreement test passes.
  - Execution state: pending

### Task group 3: comment repointing

- [ ] E-04 Repoint the comment in `agent_workflows/runner_shared.py` under "WHY (3) REPORTS RATHER THAN REFUSING" that cites `tests/test_lane_clean_base.py::test_case_3_an_untracked_file_does_NOT_refuse` and says "no live guard currently asserts this", so it names `tests/test_clean_base_untracked.py` as the live guard. Comment-only edit.
  - Depends on: E-03
  - Expected outcome: `rg -n "test_lane_clean_base" agent_workflows/` returns no matches; no code change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests must exercise behavior (P16, AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): no source reading, no `ast`/`inspect`, no symbol censuses.
- The RULE is the pure `lane_containment.evaluate_clean_base(porcelain, shared_tree=...)`; the untracked EXCLUSION is the caller's: `runner_shared.evaluate_clean_base_for_launch` runs `git status --porcelain --untracked-files=no`, and the host wrappers `oc_runipd.evaluate_clean_base_for_launch` / `agy_runipd.evaluate_clean_base_for_launch` delegate to it. Measured in this lane: `lane_containment.evaluate_clean_base('?? scratch.log\n')` returns `clean=False, dirty_paths=('scratch.log',)`, so a pure-rule test cannot express the property; the test MUST drive the real git path through the host wrappers.
- `CleanBaseResult.refuses` is `not clean and shared_tree`; `runner_shared.clean_base_launch_decision` maps a result to `CLEAN_BASE_PROCEED` / `CLEAN_BASE_WARN` / `CLEAN_BASE_REFUSE` / `CLEAN_BASE_CONSENTED`.
- Both hosts must be covered in every assertion (CID-3), the pattern of the deleted file's `DRIVERS` tuple.
- Suite is run bare: `python3 -m pytest`.

## Findings

| Site | Lost test (in `19313eed^:tests/test_lane_clean_base.py`) | Live coverage today |
|---|---|---|
| yuhl6o S-09 | `test_case_3_an_untracked_file_does_NOT_refuse`, `test_both_drivers_agree_on_every_case` | None: `rg -ln "evaluate_clean_base" tests/` returns no matches. |

## Proposed changes (ordered, validatable)

1. New `tests/test_clean_base_untracked.py` (E-01..E-03).
2. Comment repoint in `agent_workflows/runner_shared.py` (E-04).

## Deferred / out of scope (with reason)

- The deleted file's other classes (no-spawn-before-refusal ordering, shared-tree message wording): not named by backlog `dc80rp`, which is scoped to untracked non-refusal only.
- Any production change to the guard: the behavior is correct; only its guard is missing.

## Scope check

- Over-scope: none; no production logic changes.
- Under-scope: none; S-09 gets a behavioral guard plus a non-vacuity control.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_clean_base_untracked.py` passes.
- Non-vacuity: in a scratch, uncommitted edit, change `--untracked-files=no` to `--untracked-files=all` in `runner_shared.evaluate_clean_base_for_launch`; the E-01 and E-03 tests fail; revert.
- Full suite `python3 -m pytest` passes.

## Spec / documentation sync

N/A: test-only addition plus a comment repoint; no spec text changes.

## Open questions

### OQ-01: Should the deleted file's structural or ordering tests also be restored?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Backlog `dc80rp` names only the untracked non-refusal property and states "only behavioral outcomes may be restored, never a source-reading pin (P16)".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_clean_base_untracked.py` showing the untracked test passing; plus pasted output of the scratch non-vacuity run (`--untracked-files=all` in `runner_shared.evaluate_clean_base_for_launch`) showing it FAIL, then `git diff --stat agent_workflows/runner_shared.py` showing the scratch edit reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the dirty-tracked control test passing on both hosts and both `shared_tree` values.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest output showing the host-agreement test passing, and `rg -n "import ast|import inspect|read_text\(.*\.py" tests/test_clean_base_untracked.py` returning no matches.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff agent_workflows/runner_shared.py` showing only comment lines changed and naming `tests/test_clean_base_untracked.py`; pasted `rg -n "test_lane_clean_base" agent_workflows/` with no matches; pasted bare `python3 -m pytest` summary line showing the full suite passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the Scope-Paths files through `aw commit <plan> -- <paths>`; never push. After every `V-*` item records pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle (`aw ipd finalize`).
