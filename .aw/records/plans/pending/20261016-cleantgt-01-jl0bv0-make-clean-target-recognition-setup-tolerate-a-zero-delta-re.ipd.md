# IPD: Make clean-target recognition setUp tolerate a zero-delta residue strip

- Date: 2026-10-16
- Kind: child
- Concern: tests/test_clean_target_recognition.py fixture setUp aborts on an empty residue-strip commit, so none of its seven fnnwj3 recognition tests run.
- Scope: test-fixture-only change to `TestCleanTargetRecognition._strip_in_target_residue`; no production code.
- Scope-Paths: tests/test_clean_target_recognition.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: a48b4m
- Blocks-Release: next
- Set: cleantgt
- Order: 1
- Highest E allocated: 01
- Author: opencode
- Id: jl0bv0

## Workflow history
- 2026-10-16 reviewed (aw set): status set to reviewed
- 2026-10-16 /plan-review (opencode/claude-opus): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004
- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog a48b4m; failure reproduced in-lane (7 failed).

## Goal

Restore the clean-target recognition coverage authored by `fnnwj3` by making the fixture helper `TestCleanTargetRecognition._strip_in_target_residue` tolerate the zero-delta case that `3m8aix` made normal, so all seven tests in `tests/test_clean_target_recognition.py` run and pass.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Fixture fix

- [ ] E-01 In `tests/test_clean_target_recognition.py`, change `TestCleanTargetRecognition._strip_in_target_residue` so that after `git rm -r --cached .` and `git add README.md` it runs `git -C <path> diff --cached --quiet` and only runs `git commit -m 'Clean residue'` when that exits nonzero (staged changes exist); keep the trailing `git clean -fdx` unchanged.
  - Depends on: none
  - Expected outcome: setUp no longer raises `CalledProcessError` from `git commit` on a zero-delta install. Both call sites (`clean_repo`, preset `completely-clean-target`, and `local_repo`, preset `local-only`) are currently zero-delta (review demonstration: `git diff --cached --quiet` exited 0 at both sites in every setUp), so the commit is skipped at both today; if a future install does leave tracked residue, the guard's nonzero branch still commits it clean, preserving the helper's original intent.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Routine gate is bare `python3 -m pytest`; `tests/test_clean_target_recognition.py` is NOT in `pyproject.toml` `testpaths`, so it must be run explicitly (AGENTS.md repo-local development contract).
- Narrowed per-test runs clear defaults with `python3 -m pytest -o addopts=""` (AGENTS.md).
- Tests assert observable behavior only; no code-pinning (AGENTS.md, GUIDING_PRINCIPLES P16). This change touches only fixture setup, not assertions.
- Sibling fixture `tests/test_clean_target_control_state.py` `_strip_in_target_residue(self, path, pre_sha)` uses a `git reset -q --hard <pre_sha>` + `git clean -fdxq` recipe and passes (9 passed in-lane), confirming the zero-delta install is the expected state rather than a production regression.
- Commit via `aw commit <plan> -- <paths>` (AGENTS.md execution contract).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | All 7 tests fail in setUp | In-lane run at f0ac1c64c: `python3 -m pytest -o addopts="" -q tests/test_clean_target_recognition.py` -> `7 failed in 18.17s`, `Command '['git', '-C', '/tmp/.../clean_repo', 'commit', '-m', 'Clean residue']' returned non-zero exit status 1.` |
| F-2 | Root cause is the fixture, not production | Executed plan `3m8aix` ("make a clean-target install write nothing into the target") makes the install zero-delta, so `git rm -r --cached .` + `git add README.md` re-stages exactly HEAD and `git commit` reports "nothing to commit". The `local-only` call site (`tests/test_clean_target_recognition.py:125`) is zero-delta as well (plan-review demonstration, 2026-10-16). |
| F-3 | Sibling fixture already adapted | `tests/test_clean_target_control_state.py` passes 9/9 with a reset-based strip. |

## Proposed changes (ordered, validatable)

1. E-01: guard the `Clean residue` commit in `_strip_in_target_residue` with `git diff --cached --quiet` (skip on exit 0). Chosen over `commit --allow-empty` because it does not add a meaningless commit to the fixture history, and over porting the reset recipe because it is the minimal change and keeps the helper signature used at both call sites (clean_repo and local_repo) unchanged.

## Deferred / out of scope (with reason)

- Adding `tests/test_clean_target_recognition.py` to `pyproject.toml` `testpaths` so the routine gate would have caught this: a gate-composition decision for the maintainer, not required by backlog `a48b4m`.
- Any production code change: F-2 shows production behavior is correct.

## Scope check

- Over-scope: none.
- Under-scope: none; the backlog's fix and its confirmation (seven tests pass) are both covered by E-01/V-01.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_clean_target_recognition.py` must report zero failed and zero errors with every collected test passing (7 at authoring; re-derive the collected count at execution rather than treating 7 as the bar) (performed by this plan, V-01).
- `python3 -m pytest -o addopts="" -q tests/test_clean_target_control_state.py tests/test_clean_target_zero_delta_e2e.py` still passes (regression on sibling clean-target modules, V-01).
- Bare `python3 -m pytest` routine gate passes (V-01).

## Spec / documentation sync

N/A: test-fixture-only change; no spec or user-facing doc describes this helper.

## Open questions

### OQ-01: Skip the commit or use --allow-empty?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: skip when `git diff --cached --quiet` exits 0; the backlog item names both as acceptable, and skipping keeps fixture history free of empty commits (see Proposed changes). Demonstrated at plan-review (2026-10-16) on a scratch copy of the module with exactly this guard: `7 passed in 42.40s`, with `git diff --cached --quiet` returning 0 at both `clean_repo` and `local_repo` in every setUp.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff` of `tests/test_clean_target_recognition.py` showing only the guarded commit in `_strip_in_target_residue`; pasted actual output of `python3 -m pytest -o addopts="" -q tests/test_clean_target_recognition.py` showing every collected test passed with zero failed and zero errors (in particular no setUp `CalledProcessError` from `Clean residue`), collected count re-derived at execution; pasted actual output of `python3 -m pytest -o addopts="" -q tests/test_clean_target_control_state.py tests/test_clean_target_zero_delta_e2e.py` with zero failures; pasted `N passed` summary line of bare `python3 -m pytest`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). All open questions are resolved (OQ-01).

SCOPE FENCE. `- Scope-Paths:` is the expected edit set. An out-of-scope edit is permitted only when justified at finalize with `--scope-reason <path>=<why>`; acknowledge a declared path left unmodified with `--scope-ack`.

HONESTY. Every V-01 evidence block MUST paste the ACTUAL runner output; never claim a pass that was not run.

COMMIT. Commit only `tests/test_clean_target_recognition.py` and this plan via `aw commit jl0bv0 -- <paths>`; never push.

POST-GATE LIFECYCLE. Once E-01 is performed, V-01 is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize jl0bv0`. Never `git mv` the plan by hand. This plan inherits `- Blocks-Release: next` from backlog `a48b4m`.
