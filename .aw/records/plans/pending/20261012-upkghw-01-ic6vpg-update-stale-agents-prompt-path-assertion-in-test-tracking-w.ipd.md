# IPD: Update stale .agents prompt path assertion in test_tracking_warning_scan

- Date: 2026-10-12
- Kind: child
- Concern: `tests/test_installer.py::TrackingWarningScanTests::test_tracking_warning_scan` asserts the legacy `.agents/prompts/untracked/` lane path, but a fresh install into a clean repo now resolves the canonical `.aw/records/` layout and prints `.aw/records/prompts/untracked/`, so the test fails.
- Scope: Update the single stale assertion in `test_tracking_warning_scan` to the canonical `.aw/records/prompts/untracked/` path (and assert the sibling comms lane), leaving production code unchanged.
- Scope-Paths: tests/test_installer.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: upkghw
- Blocks-Release: next
- Set: upkghw
- Order: 1
- Highest E allocated: 02
- Author: opencode
- Id: ic6vpg
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-002 fixed; review record .aw/records/reviews/20261012-upkghw-01-ic6vpg-update-stale-agents-prompt-path-assertion-in-test-tracking-w.review.md

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

- [ ] E-02 BEFORE E-01's edit, run the bare suite `python3 -m pytest` and record its summary line and FAILED node ids as the baseline (`test_tracking_warning_scan` is expected among them). After E-01, run the targeted test and the bare suite again and capture the output.
  - Depends on: E-01
  - Expected outcome: `test_tracking_warning_scan` passes, and the post-change FAILED node ids are a subset of the baseline's (the baseline minus `test_tracking_warning_scan`).
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
| Review demonstration (2026-10-12) | Driving `TrackingWarningScanTests._install_capture` on a fresh `init_repo` in-process: `.aw/records/prompts/untracked/` True, `.aw/records/comms/untracked/` True, `.agents/prompts/untracked/` False | Confirms both E-01 assertions hold |

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
- Owner: plan author
- Resolution or deferral rationale: No. `engine.warn_tracking_and_scan` derives the path from the resolved layout, the repo has migrated to `.aw/records/`, and the legacy branch is separately tested; the test is what is stale, as the backlog item states.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff -- tests/test_installer.py` showing only the `.agents/prompts/untracked/` assertion replaced by `.aw/records/prompts/untracked/` plus the added `.aw/records/comms/untracked/` assertion, and no other hunks.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted actual output of `python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_tracking_warning_scan` showing `1 passed`, and the summary lines plus FAILED node-id lists of the bare `python3 -m pytest` runs before and after E-01, showing `test_tracking_warning_scan` dropped out and no new node id appeared.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Resolved questions: OQ-01 is resolved; nothing awaits the maintainer.
- Scope declaration (not a stop directive): `- Scope-Paths:` lists `tests/test_installer.py`. If another edit proves necessary, make it and justify it at finalize with `--scope-reason <path>=<why>`. Production code is not to change.
- Honesty: paste the ACTUAL runner output into every `V-*`; never record a pass you did not observe.
- Commits: `aw commit ic6vpg -- tests/test_installer.py`; never `git add -A`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` as an isolated worker, do not run `aw ipd begin`/`finalize` in the lane; the driver finalizes. By hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize ic6vpg`; never `git mv` the plan by hand.
- Release gate: inherits `- Blocks-Release: next` from backlog `upkghw`, which closes through the handoff once this plan is executed.
