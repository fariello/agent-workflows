# IPD: Update stale .agents prompt path assertion in test_tracking_warning_scan

- Date: 2026-10-12
- Kind: child
- Concern: `tests/test_installer.py::TrackingWarningScanTests::test_tracking_warning_scan` asserts the legacy `.agents/prompts/untracked/` lane path, but a fresh install into a clean repo now resolves the canonical `.aw/records/` layout and prints `.aw/records/prompts/untracked/`, so the test fails.
- Scope: Update the single stale assertion in `test_tracking_warning_scan` to the canonical `.aw/records/prompts/untracked/` path (and assert the sibling comms lane), leaving production code unchanged.
- Scope-Paths: tests/test_installer.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: upkghw
- Blocks-Release: next
- Set: upkghw
- Order: 1
- Highest E allocated: 02
- Author: opencode
- Id: ic6vpg

## Workflow history

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog upkghw; review-ready.

## Goal

Make `test_tracking_warning_scan` pass again by asserting the lane path the installer actually prints for a fresh (non-legacy) target, `.aw/records/prompts/untracked/`, so the suite stops failing on a stale pre-migration expectation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Fix the stale assertion

- [ ] E-01 In `tests/test_installer.py`, in `TrackingWarningScanTests.test_tracking_warning_scan`, replace `self.assertIn(".agents/prompts/untracked/", out_clean)` with `self.assertIn(".aw/records/prompts/untracked/", out_clean)` and add `self.assertIn(".aw/records/comms/untracked/", out_clean)`.
  - Depends on: none
  - Expected outcome: the test asserts the canonical lane paths printed by `engine.warn_tracking_and_scan` for a fresh repo; no other line of the file changes.
  - Execution state: pending

### Task group 2: Verify

- [ ] E-02 Run the targeted test and the full bare suite (`python3 -m pytest`) and capture the output.
  - Depends on: E-01
  - Expected outcome: `test_tracking_warning_scan` passes and the full suite reports no new failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Production path: `engine.warn_tracking_and_scan` builds the lane strings from `resolve_target_layout(plan.repo_root)` and `_record_scaffold_dirs(layout)` (`prompts_lane = f"{dirs['prompts']}/untracked/"`), so the printed path follows the resolved layout rather than a hard-coded `.agents/`.
- A fresh repo resolves the canonical `.aw/records/` layout; a `--keep-legacy` target still prints `.agents/...`, which is already covered and passing in `tests/test_installed_text_current.py` (`test_keep_legacy_retains_legacy_paths`).
- Suite contract (AGENTS.md repo-local): run bare `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Tests must assert on observable output (P16); this test drives `INS.install_into_repo` and asserts on captured stdout, which stays so.

## Findings

Reproduced on this worktree at `db0f10424`:

```
$ python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_tracking_warning_scan
>       self.assertIn(".agents/prompts/untracked/", out_clean)
E       AssertionError: '.agents/prompts/untracked/' not found in "... - or use the gitignored untracked lanes: .aw/records/prompts/untracked/ and .aw/records/comms/untracked/.\n"
1 failed, 143 deselected in 3.13s
```

| Location | Finding | Action |
|---|---|---|
| `tests/test_installer.py` `test_tracking_warning_scan` | Asserts legacy `.agents/prompts/untracked/` for a fresh repo | Update to `.aw/records/...` (E-01) |
| `tests/test_installed_text_current.py` `test_keep_legacy_retains_legacy_paths` | Asserts `.agents/prompts/untracked/` for a `--keep-legacy` target; passes (5 passed) | Correct as-is; no change |
| `agent_workflows/engine.py` `warn_tracking_and_scan` | Output is correct and layout-driven | No change |

## Proposed changes (ordered, validatable)

1. Edit the one assertion in `test_tracking_warning_scan` and add the comms-lane assertion (E-01), validated by V-01.
2. Run targeted and full suite (E-02), validated by V-02.

## Deferred / out of scope (with reason)

None. (Production code in `engine.warn_tracking_and_scan` and the legacy-layout test in `tests/test_installed_text_current.py` are already correct, per Findings, so no work is left over.)

## Scope check

- Over-scope: none.
- Under-scope: none; the only failing stale assertion of this path in the fresh-install case is the one in `test_tracking_warning_scan` (grep of `tests/` for `.agents/prompts/untracked` finds only it and the legitimate legacy test).

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_tracking_warning_scan` must report `1 passed`.
- Bare `python3 -m pytest` must show no new failures relative to the pre-change baseline.

## Spec / documentation sync

N/A: test-only change correcting a stale expectation; no spec or user-facing doc describes this assertion.

## Open questions

### OQ-01: Should the production notice be changed back to `.agents/` instead?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. `engine.warn_tracking_and_scan` derives the path from the resolved layout, the repo has migrated to `.aw/records/`, and the legacy branch is separately tested; the test is what is stale, as the backlog item states.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff -- tests/test_installer.py` showing only the `.agents/prompts/untracked/` assertion replaced by `.aw/records/prompts/untracked/` plus the added `.aw/records/comms/untracked/` assertion, and no other hunks.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted actual output of `python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_tracking_warning_scan` showing `1 passed`, and the summary line of a bare `python3 -m pytest` run showing no failure in `test_tracking_warning_scan` and no new failures versus baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Commit via `aw commit <this plan> -- tests/test_installer.py` (plus the plan file), never push. After every E-item is `performed` and every V-item is `pass` with pasted evidence, and `aw ipd lint --phase pre-transition` conforms, transition the plan to `.aw/records/plans/executed/` through the tooled lifecycle.
