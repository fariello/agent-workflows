# IPD: Restore behavioral coverage that evaluate_clean_base does not refuse on untracked files

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_lane_clean_base.py`, and with it `test_case_3_an_untracked_file_does_NOT_refuse` and `test_both_drivers_agree_on_every_case`, the only behavioral tests that an UNTRACKED file in the target checkout leaves the R5.4 clean-base guard CLEAN (no refusal, no dirty path) on BOTH hosts. Executed plan `yuhl6o` recorded that site as S-09 RETIRE-UNGUARDED. A regression is silent and costly: if the `--untracked-files=no` scope were dropped, every unattended run in an ordinary working checkout would be classified dirty (refused on the shared-tree path), the exact failure spec R5.4 / finding F-4 forbids.
- Scope: Add one new behavioral test module that drives the real `evaluate_clean_base_for_launch` on both hosts against a real temporary git repository and the real `runner_shared.clean_base_launch_decision`, and repoint the one source comment that says "no live guard currently asserts this" for this property. No production behavior change.
- Scope-Paths: tests/test_clean_base_untracked.py, agent_workflows/runner_shared.py, .aw/records/plans/pending/20261014-dc80rp-01-og11nj-restore-behavioral-coverage-that-evaluate-clean-base-does-no.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: dc80rp
- Set: dc80rp
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: og11nj

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: og11nj verified (set dc80rp, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed (review record 20261014-dc80rp-01-og11nj)
- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog `dc80rp`; review-ready.

## Goal

Restore behavioral (never source-reading, P16) test coverage that untracked files do not make the R5.4 clean-base guard refuse or report dirty, on both hosts and on both the isolated and shared-tree paths, while a dirty TRACKED file still classifies not-clean, so the guard is proven non-vacuous.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: untracked files leave the base clean (yuhl6o S-09)

- [x] E-01 Create `tests/test_clean_base_untracked.py` (`unittest.TestCase`) with a `setUp` that creates a `tempfile.TemporaryDirectory` (cleaned up via `addCleanup`), initializes it with `tests.support.init_repo` (local identity, `commit.gpgsign false`), removes every inherited local git variable from `os.environ` for the test's duration (`mock.patch.dict(os.environ, tests.support.clean_git_env(), clear=True)`, because the production `runner_shared._run_git` inherits `os.environ` and an inherited `GIT_DIR`/`GIT_INDEX_FILE` would point it at the wrong repository), commits one tracked file (`tracked.txt`), and a test that writes two untracked files (`scratch.log`, `notes.md`) plus one untracked file inside a new subdirectory, then for each host in (`oc_runipd`, `agy_runipd`) and each `shared_tree` in (`False`, `True`) calls `driver.evaluate_clean_base_for_launch(repo, shared_tree=...)` and asserts `result.clean is True`, `result.dirty_paths == ()`, and `result.refuses is False`, and that `runner_shared.clean_base_launch_decision(result).verdict == runner_shared.CLEAN_BASE_PROCEED`.
  - Depends on: none
  - Expected outcome: New module exists; the untracked test passes for all four host x path subtests (`self.subTest(host=..., shared_tree=...)`). Then, BEFORE E-04 touches the same file, perform the non-vacuity mutation: edit `--untracked-files=no` to `--untracked-files=all` in `runner_shared.evaluate_clean_base_for_launch` in place, run the module and observe the untracked test FAIL, then revert with `git checkout -- agent_workflows/runner_shared.py` and confirm `git diff --stat agent_workflows/runner_shared.py` is empty. The mutation is never committed.
  - Execution state: performed

### Task group 2: non-vacuity and host agreement

- [x] E-02 In the same module, add a control test: after modifying the committed `tracked.txt` (with the untracked files still present), each host returns `clean is False` and `dirty_paths == ("tracked.txt",)` (the untracked names absent), `refuses` is `True` on `shared_tree=True` and `False` on `shared_tree=False`, and `clean_base_launch_decision` yields `CLEAN_BASE_REFUSE` and `CLEAN_BASE_WARN` respectively. This proves the E-01 assertions are not vacuous (the guard does see the tree).
  - Depends on: E-01
  - Expected outcome: Control passes on both hosts and both paths.
  - Execution state: performed

- [x] E-03 In the same module, add a host-agreement test that snapshots `(clean, dirty_paths)` from both hosts at three states (clean, untracked only, untracked plus dirty tracked) and asserts both hosts agree at each state and the sequence of `clean` values is `[True, True, False]`. Do not read source files, use `ast`/`inspect`, or pin symbol identity or counts.
  - Depends on: E-02
  - Expected outcome: Agreement test passes.
  - Execution state: performed

### Task group 3: comment repointing

- [x] E-04 Repoint the comment in `agent_workflows/runner_shared.py` under "WHY (3) REPORTS RATHER THAN REFUSING" that cites `tests/test_lane_clean_base.py::test_case_3_an_untracked_file_does_NOT_refuse` and says "no live guard currently asserts this", so it names `tests/test_clean_base_untracked.py` as the live guard. Comment-only edit.
  - Depends on: E-03
  - Expected outcome: `rg -n "test_lane_clean_base" agent_workflows/` returns no matches; no code change.
  - Execution state: performed

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
  - Carrier-Declined: backlog `dc80rp` scopes this work to the yuhl6o S-09 untracked non-refusal property; no defect is known in the other classes, which the maintainer can file separately if wanted.
- Any production change to the guard: the behavior is correct; only its guard is missing.
  - Carrier-Declined: deliberate non-goal (coverage restoration only), not an outstanding obligation.

## Scope check

- Over-scope: none; no production logic changes.
- Under-scope: none; S-09 gets a behavioral guard plus a non-vacuity control.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_clean_base_untracked.py` passes.
- Non-vacuity: BEFORE E-04, in an in-place uncommitted edit, change `--untracked-files=no` to `--untracked-files=all` in `runner_shared.evaluate_clean_base_for_launch`; the E-01 test fails (E-02/E-03 may also fail, which is expected); revert with `git checkout -- agent_workflows/runner_shared.py` and confirm an empty diff before E-04 edits that file.
- Full suite `python3 -m pytest` passes.

## Spec / documentation sync

N/A: test-only addition plus a comment repoint; no spec text changes.

## Open questions

### OQ-01: Should the deleted file's structural or ordering tests also be restored?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Backlog `dc80rp` names only the untracked non-refusal property and states "only behavioral outcomes may be restored, never a source-reading pin (P16)".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_clean_base_untracked.py` showing the untracked test passing on all four subtests; plus pasted output of the in-place non-vacuity run (`--untracked-files=all` in `runner_shared.evaluate_clean_base_for_launch`), made BEFORE E-04, showing the untracked test FAIL with the untracked names in `dirty_paths`; then pasted `git diff --stat agent_workflows/runner_shared.py` printing nothing (reverted, and E-04 not yet applied).
  - Observed evidence:
    Passing test run (`python3 -m unittest -v tests.test_clean_base_untracked.CleanBaseUntrackedCoverageTests.test_untracked_files_leave_clean_base_clean_on_both_hosts` and `python3 -m pytest -o addopts="" -v tests/test_clean_base_untracked.py`):
    ```
    test_untracked_files_leave_clean_base_clean_on_both_hosts (tests.test_clean_base_untracked.CleanBaseUntrackedCoverageTests.test_untracked_files_leave_clean_base_clean_on_both_hosts)
    E-01: untracked files leave evaluate_clean_base clean and proceeding on both hosts. ... ok

    ----------------------------------------------------------------------
    Ran 1 test in 0.044s

    OK
    ```
    ```
    tests/test_clean_base_untracked.py::CleanBaseUntrackedCoverageTests::test_untracked_files_leave_clean_base_clean_on_both_hosts PASSED [ 33%]
    ```

    In-place non-vacuity run with `--untracked-files=all` before E-04:
    ```
    _ CleanBaseUntrackedCoverageTests.test_untracked_files_leave_clean_base_clean_on_both_hosts _

    self = <tests.test_clean_base_untracked.CleanBaseUntrackedCoverageTests testMethod=test_untracked_files_leave_clean_base_clean_on_both_hosts>

        def test_untracked_files_leave_clean_base_clean_on_both_hosts(self) -> None:
            """E-01: untracked files leave evaluate_clean_base clean and proceeding on both hosts."""
            self._create_untracked_files()

            hosts = (
                ("oc_runipd", oc_runipd),
                ("agy_runipd", agy_runipd),
            )
            for host_name, driver in hosts:
                for shared_tree in (False, True):
                    with self.subTest(host=host_name, shared_tree=shared_tree):
                        result = driver.evaluate_clean_base_for_launch(
                            self.repo, shared_tree=shared_tree
                        )
    >                   self.assertEqual(result.dirty_paths, ())
    E                   AssertionError: Tuples differ: ('new_subdir/nested.txt', 'notes.md', 'scratch.log') != ()
    E
    E                   First tuple contains 3 additional elements.
    E                   First extra element 0:
    E                   'new_subdir/nested.txt'
    E
    E                   - ('new_subdir/nested.txt', 'notes.md', 'scratch.log')
    E                   + ()

    tests/test_clean_base_untracked.py:61: AssertionError
    ```

    Revert and confirmation before E-04:
    ```
    $ git checkout -- agent_workflows/runner_shared.py
    $ git diff --stat agent_workflows/runner_shared.py
    ```
    (empty output)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the dirty-tracked control test passing on both hosts and both `shared_tree` values.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_clean_base_untracked.py -k test_dirty_tracked_file_control_refuses_or_warns_on_both_hosts
    tests/test_clean_base_untracked.py::CleanBaseUntrackedCoverageTests::test_dirty_tracked_file_control_refuses_or_warns_on_both_hosts PASSED [100%]
    ============================== 1 passed, 2 deselected in 0.45s ===============================
    ```
    and unittest:
    ```
    test_dirty_tracked_file_control_refuses_or_warns_on_both_hosts (tests.test_clean_base_untracked.CleanBaseUntrackedCoverageTests.test_dirty_tracked_file_control_refuses_or_warns_on_both_hosts)
    E-02: control test modifying tracked.txt proves guard sees tree and is non-vacuous. ... ok
    ----------------------------------------------------------------------
    Ran 1 test in 0.046s

    OK
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted pytest output showing the host-agreement test passing, and `rg -n "import ast|import inspect|read_text\(.*\.py" tests/test_clean_base_untracked.py` returning no matches.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_clean_base_untracked.py -k test_both_hosts_agree_across_states
    tests/test_clean_base_untracked.py::CleanBaseUntrackedCoverageTests::test_both_hosts_agree_across_states PASSED [100%]
    ============================== 1 passed, 2 deselected in 0.44s ===============================
    ```
    and check for forbidden imports / source inspection:
    ```
    $ rg -n "import ast|import inspect|read_text\(.*\.py" tests/test_clean_base_untracked.py
    (no matches, exit code 1)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted `git diff agent_workflows/runner_shared.py` showing only comment lines changed and naming `tests/test_clean_base_untracked.py`; pasted `rg -n "test_lane_clean_base" agent_workflows/` with no matches; pasted bare `python3 -m pytest` summary line showing the full suite passing.
  - Observed evidence:
    Diff of `agent_workflows/runner_shared.py`:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index de26cd4f2..51e945556 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -17362,9 +17362,9 @@ def expand_dependency_closure(
     #
     # WHY (3) REPORTS RATHER THAN REFUSING, since the asymmetry looks like an oversight and is not.
     # Refusing on untracked content would make an unattended run unstartable in essentially any working
    -# checkout (`evaluate_clean_base`'s own docstring says so, and `tests/test_lane_clean_base.py
    -# ::test_case_3_an_untracked_file_does_NOT_refuse` asserted it before deletion in `19313eed`; no
    -# live guard currently asserts this), and a gate that false-positives on correct behavior trains
    +# checkout (`evaluate_clean_base`'s own docstring says so; `tests/test_clean_base_untracked.py`
    +# asserts this as a live behavioral guard across both hosts), and a gate that false-positives on
    +# correct behavior trains
     # operators to bypass it. The measured incident is the other half: a stray
     # `aw install` wrote 130+ uncommitted, largely UNTRACKED files into a working tree and on at least two
     # occasions an agent did not realize the pollution was its own. Reporting puts that in front of the
    ```
    Grep check for deleted test reference:
    ```
    $ rg -n "test_lane_clean_base" agent_workflows/
    (no matches, exit code 1)
    ```
    Full suite summary line:
    ```
    705 passed in 32.57s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved og11nj --by-human`); OQ-01 is resolved and no question blocks. Begin with `aw ipd begin og11nj`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to `agent_workflows/runner_shared.py` that cannot be safely combined, or `runner_shared.evaluate_clean_base_for_launch` no longer running `git status --porcelain --untracked-files=no` (the premise of this plan).

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. The non-vacuity mutation is temporary, MUST be reverted before E-04, and is never committed.

Commits: commit only the Scope-Paths files you changed through `aw commit og11nj -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, run `aw ipd finalize og11nj` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.
