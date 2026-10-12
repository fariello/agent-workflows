# IPD: Verify specs.validate_spec accepts spec 89xjll and close the attention.unsafe-field defect with evidence

- Date: 2026-10-11
- Kind: child
- Concern: `specs.validate_spec` reported `attention.unsafe-field` for spec `89xjll` because its `- Scope:` (343 chars at filing) exceeded the then single 300-char descriptive bound applied to Scope.
- Scope: Confirm on current main that `specs.validate_spec` returns no drift for `89xjll` and for every real spec, that `aw specs check` reports no `attention.unsafe-field`, and that the prose length class guard tests pass; fix forward in the validator or bound only if a re-run fails.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/attention_contract.py, tests/test_descriptive_length_classes.py, tests/test_spec_review_attestation.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: md2o3y
- Blocks-Release: next
- Set: md2o3y
- Order: 1
- Highest E allocated: 03
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: k6clui

## Workflow history

- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready graduating backlog md2o3y; root cause and current-pass state established from repository evidence.

## Goal

Release the `next` gate on backlog `md2o3y` with executed evidence: show that `specs.validate_spec` now accepts spec `89xjll` (and the whole real specs corpus), name the change that fixed it, and confirm a behavioral regression guard already covers the fixed bound.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-run the validator that reported the defect

- [ ] E-01 Call `specs.validate_spec(path, path.read_text())` on `.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md` and on every `*.spec.md` under `.aw/records/specs/`, printing each non-empty drift list, then run `aw specs check` and record its exit code.
  - Depends on: none
  - Expected outcome: `89xjll` returns `[]`; no spec reports an `attention.unsafe-field` drift; `aw specs check` exits 0.
  - Execution state: pending

### Task group 2: Confirm the regression guards

- [ ] E-02 Run `python3 -m pytest tests/test_descriptive_length_classes.py tests/test_spec_review_attestation.py -o addopts="" -k "LengthClass or Grandfathering or prose"` and, if the `-k` filter selects nothing, rerun both files without `-k`; record the summary line.
  - Depends on: none
  - Expected outcome: zero failures, including `test_spec_validation_prose_and_oneline_fields` and `test_every_real_spec_in_this_repository_still_conforms`.
  - Execution state: pending

### Task group 3: Fix forward only on failure

- [ ] E-03 If E-01 or E-02 failed, repair the validator or bound within Scope-Paths (never edit the approved `89xjll` spec body to dodge the check) and re-run E-01, E-02 and the bare suite `python3 -m pytest`; otherwise record that no change was required and capture `git diff --stat -- <Scope-Paths>`.
  - Depends on: E-01, E-02
  - Expected outcome: either an empty Scope-Paths diff (expected case) or a fix confined to Scope-Paths with all re-runs passing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite invocation: run bare `python3 -m pytest`; narrowed runs clear defaults with `-o addopts=""` (AGENTS.md repository development contract).
- Tests exercise behavior, not source structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); the guards call `specs.validate_spec` on real input.
- `specs.validate_spec` signature is `(path: Path, text: str) -> List[core.Drift]`; it checks Scope with `A.is_safe_prose_descriptive(scope)` and message "Scope is over-length or has control chars/newlines".
- `attention_contract.PROSE_DESCRIPTIVE_FIELDS` is `("Scope", "Concern", "Question")`, bound `attention_contract.MAX_PROSE_DESCRIPTIVE_LEN = 4300`, versus one-line `attention_contract.MAX_DESCRIPTIVE_LEN = 300`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | At filing (2026-10-01) the `89xjll` Scope was 343 characters, over the single 300-char bound then enforced on Scope by `specs.validate_spec`, producing `attention.unsafe-field`. | Sibling plan `oehkmh` F-1 (`git show cb3ea8546:` of the spec, measured 343). |
| F-2 | Commit `b325725d2` (`pl1lbb`) split the bound into a one-line class (300) and a prose class (4300) and moved Scope to the prose class, removing the root cause for any spec Scope. | `attention_contract.is_safe_prose_descriptive`, `MAX_PROSE_DESCRIPTIVE_LEN = 4300`. |
| F-3 | The current `89xjll` Scope line measures 369 characters (including the `- Scope: ` prefix), above 300 and accepted only because of F-2. | `grep "^- Scope:"` on the spec, `awk length`. |
| F-4 | On this worktree's base (`1feee61ca`) `specs.validate_spec` on `89xjll` returns `[]`, and `aw specs check` exits 0 with zero `unsafe-field` lines. | Pre-authoring runs during this turn. |
| F-5 | A behavioral guard exists: `tests/test_descriptive_length_classes.py::test_spec_validation_prose_and_oneline_fields` asserts a 400-char Scope is clean and a 4301-char Scope drifts. No new test is required. | test name in that file. |
| F-6 | Sibling backlog `6bolin` (same root cause, test side) is carried by pending plan `oehkmh`. That plan is not modified here; the two carriers are independent so each gate is released by its own executed plan. | `.aw/records/plans/pending/20261011-6bolin-01-oehkmh-...ipd.md` |

## Proposed changes (ordered, validatable)

1. E-01: re-run `specs.validate_spec` on `89xjll` and the whole corpus, plus `aw specs check`.
2. E-02: run the existing guard tests.
3. E-03: fix forward only on failure; otherwise record an empty diff.

In the expected case this plan changes no source or test file.

## Deferred / out of scope (with reason)

- Closing `6bolin` or editing plan `oehkmh`: separate lifecycle (F-6).
- Editing the approved `89xjll` spec body: forbidden as a way to pass the check, and unnecessary since the prose bound accepts it.

## Scope check

- Over-scope: none. Scope-Paths lists only files a fix-forward in E-03 could touch.
- Under-scope: none. Every V-* demands command or test output, reachable by construction.

## Required tests / validation

- `specs.validate_spec` on `89xjll` returns `[]`; no real spec yields `attention.unsafe-field`; `aw specs check` exits 0 (E-01).
- `tests/test_descriptive_length_classes.py` and `tests/test_spec_review_attestation.py` guards pass (E-02).
- If code changed, the bare full suite `python3 -m pytest` passes (E-03).

## Spec / documentation sync

N/A: no behavior change expected. The prose length class is already specified and shipped by `pl1lbb`; no spec is touched.

## Open questions

None. Root cause and current state were resolved from repository evidence (F-1 to F-5).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of the `specs.validate_spec` call printing `[]` for `89xjll` and no `attention.unsafe-field` drift for any spec, and pasted `aw specs check` tail plus `exit=0`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted pytest summary line showing zero failed, with `test_spec_validation_prose_and_oneline_fields` and `test_every_real_spec_in_this_repository_still_conforms` among the passed tests.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff --stat` for Scope-Paths (empty in the expected case); if non-empty, also the pasted bare full-suite summary line with zero failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Commit only paths changed under Scope-Paths through `aw commit k6clui -- <paths>`; never push. After every V-* item passes with pasted evidence and `aw ipd lint --phase pre-transition` conforms, transition the plan to `executed/` through the lifecycle tooling.
