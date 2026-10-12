# IPD: Verify GrandfatheringAndCheckerTests passes on the 89xjll spec and pin the prose Scope bound against the real corpus

- Date: 2026-10-11
- Kind: child
- Concern: `GrandfatheringAndCheckerTests.test_every_real_spec_in_this_repository_still_conforms` failed on spec `89xjll` with `attention.unsafe-field` because its 343-char `- Scope:` exceeded the then single 300-char descriptive bound.
- Scope: Confirm on current main that the real-corpus spec conformance test and the descriptive-length tests pass, that `specs.validate_spec` reports no drift for `89xjll`, and that the cause (Scope over the one-line bound) is closed by the prose length class; fix forward only if the re-run fails.
- Scope-Paths: tests/test_spec_review_attestation.py, tests/test_descriptive_length_classes.py, agent_workflows/specs.py, agent_workflows/attention_contract.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 6bolin
- Blocks-Release: next
- Set: 6bolin
- Order: 1
- Highest E allocated: 03
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: oehkmh

## Workflow history

- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready graduating backlog 6bolin; root cause and current-pass state established from repository evidence.

## Goal

Close backlog `6bolin` with evidence: show that the failing real-corpus test now passes on main, explain which change fixed it, and confirm that a regression guard for the fixed bound already exercises the behavior, so the release gate `next` is released by an executed carrier rather than by assertion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-run the failing test and the corpus validator

- [ ] E-01 Run `python3 -m pytest tests/test_spec_review_attestation.py -o addopts="" -k GrandfatheringAndCheckerTests` and record the pass/fail summary line.
  - Depends on: none
  - Expected outcome: all 4 `GrandfatheringAndCheckerTests` tests pass, including `test_every_real_spec_in_this_repository_still_conforms`.
  - Execution state: pending

- [ ] E-02 Run `specs.validate_spec` directly on the `89xjll` spec file (`.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md`) and `aw specs check`, recording the drift list and exit code.
  - Depends on: none
  - Expected outcome: `validate_spec` returns `[]` for `89xjll`; `aw specs check` reports no `attention.unsafe-field` for any spec.
  - Execution state: pending

### Task group 2: Confirm the regression guard and fix forward only if needed

- [ ] E-03 Run `python3 -m pytest tests/test_descriptive_length_classes.py -o addopts=""` to confirm the fixture guard (400-char Scope clean, 4301-char Scope drifts) passes; if E-01, E-02, or this run fails, fix forward within Scope-Paths (repair the validator or bound, never edit the approved `89xjll` spec body to dodge the check) and re-run all three.
  - Depends on: E-01, E-02
  - Expected outcome: the descriptive-length tests pass; no code change is needed in the expected case, and any change made is confined to Scope-Paths.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite invocation: run bare `python3 -m pytest`; narrowed runs clear defaults with `-o addopts=""` (AGENTS.md repository development contract).
- Tests must exercise behavior, not pin source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); the existing guards call `specs.validate_spec` and `check_engine.check_spec_review_attestation` on real input, which conforms.
- Spec Scope is a PROSE descriptive field: `attention_contract.PROSE_DESCRIPTIVE_FIELDS` contains `"Scope"`, checked in `specs.validate_spec` via `A.is_safe_prose_descriptive(scope)` with message "Scope is over-length or has control chars/newlines"; bound `attention_contract.MAX_PROSE_DESCRIPTIVE_LEN = 4300`, versus the one-line `MAX_DESCRIPTIVE_LEN = 300`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Backlog `6bolin` was filed in commit `cb3ea8546` (2026-10-01, during `z3ifg8` execution). At that revision the `89xjll` spec Scope was 343 characters, over the single 300-char bound then enforced on Scope by `specs.validate_spec`, producing `attention.unsafe-field`. | `git show cb3ea8546:.aw/records/specs/to-review/20261001-89xjll-...spec.md` Scope length measured 343; pre-split `attention_contract.MAX_DESCRIPTIVE_LEN = 300`. |
| F-2 | Commit `8c460a9a1` ("Fix baseline test failures on main (spec scope length, ...)") shortened the `89xjll` Scope, a content fix. | `git show 8c460a9a1 -- .aw/records/specs/` |
| F-3 | Commit `b325725d2` (`pl1lbb`) split the bound into a one-line class (300) and a prose class (4300) and moved Scope to the prose class, a structural fix that removes the root cause for any spec Scope. The current `89xjll` Scope is 358 characters and is valid only because of this split. | `attention_contract.is_safe_prose_descriptive`, `MAX_PROSE_DESCRIPTIVE_LEN = 4300`; measured length 358. |
| F-4 | On current main (worktree at `1d6203a20`) `GrandfatheringAndCheckerTests` passes: "4 passed, 26 deselected". | Pre-authoring run of `pytest tests/test_spec_review_attestation.py -o addopts="" -k Grandfathering`. |
| F-5 | A behavioral regression guard for the fixed bound already exists: `tests/test_descriptive_length_classes.py::test_spec_validation_prose_and_oneline_fields` asserts a 400-char Scope is clean and a 4301-char Scope drifts. No new test is required. | `tests/test_descriptive_length_classes.py` docstring item (d). |
| F-6 | Sibling backlog `md2o3y` ("Spec 89xjll fails validate_spec with attention.unsafe-field") records the same root cause from the validator side. It is not in scope here and is not modified; its owner can close it on this plan's evidence. | `.aw/records/backlog/open/20261001-md2o3y-01-md2o3y-spec-89xjll-fails-validate-spec-with-attention-uns.backlog.md` |

## Proposed changes (ordered, validatable)

1. E-01: re-run the originally failing test class and capture the result.
2. E-02: validate the `89xjll` spec and the whole specs tree directly.
3. E-03: confirm the existing fixture guard passes; fix forward only on failure.

In the expected case this plan changes no source or test file; its deliverable is executed evidence that releases the `next` gate on `6bolin`.

## Deferred / out of scope (with reason)

- Closing `md2o3y`: a separate backlog item with its own lifecycle; this plan only records the shared evidence (F-6).
- Editing the approved `89xjll` spec body: forbidden as a way to pass the check, and unnecessary because the prose bound already accepts it.

## Scope check

- Over-scope: none. Scope-Paths lists only the files a fix-forward in E-03 could touch.
- Under-scope: none. Every V-* item demands a test result or a command output, reachable by construction.

## Required tests / validation

- `python3 -m pytest tests/test_spec_review_attestation.py -o addopts="" -k GrandfatheringAndCheckerTests` passes (E-01).
- `specs.validate_spec` on `89xjll` returns `[]`, and `aw specs check` shows no `attention.unsafe-field` (E-02).
- `python3 -m pytest tests/test_descriptive_length_classes.py -o addopts=""` passes (E-03).
- If any code changed in E-03, the bare full suite `python3 -m pytest` passes.

## Spec / documentation sync

N/A: no behavior changes. The prose-length class is already specified and shipped by `pl1lbb`; no spec is touched.

## Open questions

None. The root cause and the current state were resolved from repository evidence (F-1 to F-5).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest summary line showing `4 passed` (zero failed) for `-k GrandfatheringAndCheckerTests`, including `test_every_real_spec_in_this_repository_still_conforms`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of a `specs.validate_spec` call on the `89xjll` file printing `[]`, and pasted `aw specs check` output plus exit code showing no `attention.unsafe-field` finding.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest summary line for `tests/test_descriptive_length_classes.py` showing zero failed, and `git diff --stat` for Scope-Paths (empty in the expected case; if non-empty, also the pasted bare full-suite summary line).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Commit only paths changed under Scope-Paths through `aw commit oehkmh -- <paths>`; never push. After every V-* item passes with pasted evidence and `aw ipd lint --phase pre-transition` conforms, transition the plan to `executed/` through the lifecycle tooling.
