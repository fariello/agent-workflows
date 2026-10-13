# IPD: Verify GrandfatheringAndCheckerTests passes on the 89xjll spec and pin the prose Scope bound against the real corpus

- Date: 2026-10-11
- Kind: child
- Concern: `GrandfatheringAndCheckerTests.test_every_real_spec_in_this_repository_still_conforms` failed on spec `89xjll` with `attention.unsafe-field` because its 343-char `- Scope:` exceeded the then single 300-char descriptive bound.
- Scope: Confirm on current main that the real-corpus spec conformance test and the descriptive-length tests pass, that `specs.validate_spec` reports no drift for `89xjll`, and that the cause (Scope over the one-line bound) is closed by the prose length class; fix forward only if the re-run fails.
- Scope-Paths: tests/test_spec_review_attestation.py, tests/test_descriptive_length_classes.py, agent_workflows/specs.py, agent_workflows/attention_contract.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 6bolin
- From-Spec: none
- Blocks-Release: next
- Set: 6bolin
- Order: 1
- Highest E allocated: 03
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: oehkmh
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007

- 2026-10-12 /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 fixed (review record 20261011-6bolin-01-oehkmh)
- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready graduating backlog 6bolin; root cause and current-pass state established from repository evidence.

## Goal

Close backlog `6bolin` with evidence: show that the failing real-corpus test now passes on main, explain which change fixed it, and confirm that a regression guard for the fixed bound already exercises the behavior, so the release gate `next` is released by an executed carrier rather than by assertion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-run the failing test and the corpus validator

- [ ] E-01 Run `python3 -m pytest tests/test_spec_review_attestation.py -o addopts="" -k GrandfatheringAndCheckerTests -v` and record the per-test PASSED/FAILED lines and the summary line.
  - Depends on: none
  - Expected outcome: zero failed and zero errors, with `test_every_real_spec_in_this_repository_still_conforms` listed PASSED (it is the test that exercises `specs.validate_spec` over the real corpus, the behavior the defect broke). The selected-test count is context, not the bar (4 at review HEAD `bd8b8e993`); a filter that selects nothing is a failure of this item, not a pass.
  - Execution state: pending

- [ ] E-02 Locate the `89xjll` spec by id6 (`aw find specs 89xjll`; its directory moves with its status, and at review it is `.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md`), call `specs.validate_spec(path, path.read_text())` on it printing the drift list, then run `aw specs check` and record its exit code and the count of `unsafe-field` lines in its output.
  - Depends on: none
  - Expected outcome: `validate_spec` returns `[]` for `89xjll`; `aw specs check` exits 0 with zero `unsafe-field` lines. A drift on another spec whose rule is NOT `attention.unsafe-field` is outside this defect: record it and file it with `aw backlog new` rather than fixing it here.
  - Execution state: pending

### Task group 2: Confirm the regression guard and fix forward only if needed

- [ ] E-03 Run `python3 -m pytest tests/test_descriptive_length_classes.py -o addopts=""` to confirm the fixture guard (400-char Scope clean, 4301-char Scope drifts) passes; if E-01, E-02, or this run fails with an `attention.unsafe-field` on Scope/Concern/Question, first take a bare `python3 -m pytest` baseline recording its FAILED node ids, then fix forward within Scope-Paths (repair the validator or bound; never edit the approved `89xjll` spec body to dodge the check). A change to either bound value or to which fields are prose-class is a contract change to Section 8.8 of spec `attention-registry-and-cross-tree-status`, so it MUST be made in that spec in the same commit (declared in Scope-Paths). Then re-run E-01, E-02, this file, and the bare suite, comparing its FAILED node ids to the baseline. Otherwise record that no change was required and capture `git diff --stat -- <Scope-Paths>`.
  - Depends on: E-01, E-02
  - Expected outcome: zero failed in `tests/test_descriptive_length_classes.py`, including `test_spec_validation_prose_and_oneline_fields`; either an empty Scope-Paths diff (expected case) or a fix confined to Scope-Paths with every re-run passing and no FAILED node id absent from the baseline.
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
| F-2 | Commit `8c460a9a1` ("Fix baseline test failures on main (spec scope length, ...)") shortened the `89xjll` Scope from 343 to 257 characters, a content fix. Later spec-review commits (`e54d822bc`, `5b449d000`, `1c4352876`) grew it back past 300, so the content fix alone is NOT what keeps the spec passing now (see F-3). | `git show 8c460a9a1 -- .aw/records/specs/` (Scope `-` 343, `+` 257, measured at review); `git log -- '.aw/records/specs/*89xjll*'`. |
| F-3 | Commit `b325725d2` (`pl1lbb`) split the bound into a one-line class (300) and a prose class (4300) and moved Scope to the prose class, a structural fix that removes the root cause for any spec Scope. The current `89xjll` Scope is 358 characters and is valid only because of this split. | `attention_contract.is_safe_prose_descriptive`, `MAX_PROSE_DESCRIPTIVE_LEN = 4300`; measured length 358. |
| F-4 | On current main (worktree at `1d6203a20`) `GrandfatheringAndCheckerTests` passes: "4 passed, 26 deselected". Re-measured at review HEAD `bd8b8e993`: same `4 passed, 26 deselected` with `test_every_real_spec_in_this_repository_still_conforms PASSED`; `validate_spec` on `89xjll` -> `[]`; `aw specs check` exit 0 with 0 `unsafe-field` lines; `tests/test_descriptive_length_classes.py` `6 passed`; current `- Scope:` line 367 characters including its 9-character prefix (358 content). | Pre-authoring run; review re-run. |
| F-5 | A behavioral regression guard for the fixed bound already exists: `tests/test_descriptive_length_classes.py::test_spec_validation_prose_and_oneline_fields` asserts a 400-char Scope is clean and a 4301-char Scope drifts. No new test is required. | `tests/test_descriptive_length_classes.py` docstring item (d). |
| F-6 | Sibling backlog `md2o3y` ("Spec 89xjll fails validate_spec with attention.unsafe-field") records the same root cause from the validator side and is now `graduated`, carried by its own pending plan `k6clui` (reviewed). It is not in scope here and is not modified; each gate is released by its own executed carrier. | `.aw/records/backlog/graduated/20261001-md2o3y-01-md2o3y-spec-89xjll-fails-validate-spec-with-attention-uns.backlog.md`; `.aw/records/plans/pending/20261011-md2o3y-01-k6clui-verify-specs-validate-spec-accepts-spec-89xjll-and-close-the.ipd.md` |

## Proposed changes (ordered, validatable)

1. E-01: re-run the originally failing test class and capture the result.
2. E-02: validate the `89xjll` spec and the whole specs tree directly.
3. E-03: confirm the existing fixture guard passes; fix forward only on failure.

In the expected case this plan changes no source or test file; its deliverable is executed evidence that releases the `next` gate on `6bolin`.

## Deferred / out of scope (with reason)

- Closing `md2o3y`: a separate backlog item with its own lifecycle; this plan only records the shared evidence (F-6).
  - Carrier: k6clui
  - Carrier-Evidence: .aw/records/plans/executed/20261011-md2o3y-01-k6clui-verify-specs-validate-spec-accepts-spec-89xjll-and-close-the.ipd.md
- Editing the approved `89xjll` spec body: forbidden as a way to pass the check, and unnecessary because the prose bound already accepts it.
  - Carrier-Declined: a forbidden shortcut, not owed work

## Scope check

- Over-scope: none. Scope-Paths lists only the files a fix-forward in E-03 could touch; the attention spec is declared only for a possible Section 8.8 amendment. The plan file itself always changes (evidence) and is committed too.
- Under-scope: none. Every V-* item demands a test result or a command output, reachable by construction.

## Required tests / validation

- `python3 -m pytest tests/test_spec_review_attestation.py -o addopts="" -k GrandfatheringAndCheckerTests -v`: zero failed, `test_every_real_spec_in_this_repository_still_conforms` PASSED (E-01).
- `specs.validate_spec` on `89xjll` returns `[]`, and `aw specs check` exits 0 with no `unsafe-field` line (E-02).
- `python3 -m pytest tests/test_descriptive_length_classes.py -o addopts=""`: zero failed (E-03).
- If any code changed in E-03, the bare full suite `python3 -m pytest` shows no FAILED node id absent from its pre-edit baseline.

## Spec / documentation sync

N/A in the expected case: no behavior changes. The prose-length class is already specified in spec `attention-registry-and-cross-tree-status` Section 8.8 and shipped by `pl1lbb`. That spec is declared in Scope-Paths ONLY because an E-03 fix-forward that changed a bound or a field's class would amend Section 8.8, and the runners announce declared spec edits up front; in the expected case it is not touched and is acknowledged with `--scope-ack` at finalize.

## Open questions

None. The root cause and the current state were resolved from repository evidence (F-1 to F-5).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `-v` output for `-k GrandfatheringAndCheckerTests` showing `test_every_real_spec_in_this_repository_still_conforms PASSED` and a summary line with zero failed and zero errors (and at least one selected test).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw find specs 89xjll` line, pasted output of the `specs.validate_spec` call on that file printing `[]`, and pasted `aw specs check` tail plus `exit=0` and the `unsafe-field` line count (0).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest summary line for `tests/test_descriptive_length_classes.py` showing zero failed, and `git diff --stat` for Scope-Paths (empty in the expected case); if non-empty, also the pre-edit and post-edit bare full-suite summary lines with FAILED node ids showing no new failure, and, if a bound or field class changed, the spec Section 8.8 diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved oehkmh --by-human`); there are no open questions. Begin with `aw ipd begin oehkmh`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition. In the expected (verify-only) case no declared path changes; acknowledge each declared-but-unmodified path at finalize with `--scope-ack <path>`. If an edit outside Scope-Paths proves necessary, make it and justify it with `--scope-reason <path>=<why>`. Never edit the `89xjll` spec body to pass the check.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run.

Commits: this plan's own record always changes (E/V marks and evidence), so commit it, plus any Scope-Paths you changed, through `aw commit oehkmh -- <paths>`; verify `git diff --cached --name-only` before any raw commit; never push, never tag.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize oehkmh`. Never `git mv` the plan or hand-edit `- Status:`. Release gate: this plan carries `- From-Backlog: 6bolin` and the inherited `- Blocks-Release: next`; once it is executed, `aw backlog set done 6bolin` closes the item through the HANDOFF rule (this plan is its only carrier). Sibling `md2o3y` is closed separately by its own carrier `k6clui`.
