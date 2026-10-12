# IPD: Verify and close tests/test_scope_exceeded.py setUp mint_driver_attestation regression

- Date: 2026-10-12
- Kind: child
- Concern: tests/test_scope_exceeded.py setUp called ipd_lifecycle.mint_driver_attestation, which e25iy9 (commit 86181232a) deleted, so all 7 cases errored on main.
- Scope: Confirm the already-landed fix (commit 64b8c94f3) holds on the current tree, that no caller of the deleted symbol remains anywhere in tests or the package, and repair tests/test_scope_exceeded.py only if either check fails.
- Scope-Paths: tests/test_scope_exceeded.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: u18kic
- Blocks-Release: next
- Set: u18kic
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 3or4ce

## Workflow history

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog u18kic; repository evidence shows the defect already fixed by 64b8c94f3, so the plan verifies and closes rather than re-implements.

## Goal

Graduate backlog `u18kic` by proving, with pasted runner output, that `tests/test_scope_exceeded.py` no longer depends on the deleted `ipd_lifecycle.mint_driver_attestation` and that its 7 cases pass, repairing the file only if the evidence shows a residual failure.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm the fix and the absence of residual callers

- [ ] E-01 Search the package and test tree for any remaining reference to `mint_driver_attestation` (e.g. `grep -rn mint_driver_attestation agent_workflows tests`).
  - Depends on: none
  - Expected outcome: zero matches in `agent_workflows/` and `tests/`; any match is recorded as a finding for E-03.
  - Execution state: pending

- [ ] E-02 Run the module's tests: `python3 -m pytest tests/test_scope_exceeded.py`.
  - Depends on: none
  - Expected outcome: `7 passed`, no errors.
  - Execution state: pending

### Task group 2: Conditional repair

- [ ] E-03 If E-01 found a reference inside `tests/test_scope_exceeded.py` or E-02 reported a failure, remove the stale attestation setup from `TestScopeExceededMetadataAndSendBack.setUp` (finalize no longer reads the attestation, per commit 64b8c94f3's message) and re-run E-02; otherwise record "no change required" with the E-01/E-02 evidence.
  - Depends on: E-01, E-02
  - Expected outcome: either a minimal diff to `tests/test_scope_exceeded.py` followed by a passing re-run, or an explicit no-change record.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The suite is run bare as `python3 -m pytest` (AGENTS.md repo-local development contract); narrowed runs pass the file path only.
- Commits go through `aw commit <plan> -- <paths>` (AGENTS.md execution contract).
- Tests must exercise behavior, not pin source text (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); hence no new test asserting the symbol's absence is added. The grep in E-01 is a one-off executor check, not a committed test.
- Cite by symbol: `TestScopeExceededMetadataAndSendBack.setUp` in `tests/test_scope_exceeded.py`; deleted symbol `agent_workflows.ipd_lifecycle.mint_driver_attestation`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The deleted-symbol call was removed from setUp on 2026-10-09. | `git log -- tests/test_scope_exceeded.py` shows `64b8c94f3 test(scope_exceeded): drop the deleted driver-attestation setup (fixes 7 red tests on main)`, a 7-line deletion in that file. |
| F-2 | The current setUp no longer references the symbol. | `TestScopeExceededMetadataAndSendBack.setUp` now only declares the execution role, makes a temp git repo, builds the parser, and creates the run dir. |
| F-3 | The module passes at authoring time. | `python3 -m pytest tests/test_scope_exceeded.py` printed `7 passed in 6.97s` on 2026-10-12 in this lane. |
| F-4 | No other `.py` file in the tree references the symbol at authoring time. | `grep -rn mint_driver_attestation --include=*.py .` returned no matches. |

The backlog item was filed the same day the fix landed and was never closed; this plan supplies the evidence to close it.

## Proposed changes (ordered, validatable)

1. E-01/E-02: verification only, no file changes expected.
2. E-03: conditional minimal edit to `tests/test_scope_exceeded.py` setUp only if verification fails.

## Deferred / out of scope (with reason)

- `h3fnoc` (scope-reconciliation send-back misclassification) and `8o7gco` (checkout git identity overwritten), filed in the same commit 64b8c94f3, are separate backlog items with their own lifecycle; not touched here.
- Adding a test that pins absence of the symbol is out of scope: it would be a code-pinning test, which the repository forbids.

## Scope check

- Over-scope: none.
- Under-scope: none; the only file the defect touches is `tests/test_scope_exceeded.py`, and the full-suite run in V-03 covers regressions elsewhere.

## Required tests / validation

- `python3 -m pytest tests/test_scope_exceeded.py` reports `7 passed` (V-02, V-03).
- Bare `python3 -m pytest` shows no failure in `tests/test_scope_exceeded.py` (V-03).
- Reference search shows no remaining caller (V-01).

## Spec / documentation sync

N/A: the change (if any) is confined to a test module's fixture setup; no spec or user-facing doc describes it.

## Open questions

### OQ-01: Is any work left given the fix already landed?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Repository evidence (F-1 to F-4) shows the code fix is done; the remaining work is verification with pasted evidence plus a conditional repair, which is what this plan carries.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `grep -rn mint_driver_attestation agent_workflows tests` showing no matches (exit status 1), or the listed matches with their disposition under E-03.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted pytest summary line from `python3 -m pytest tests/test_scope_exceeded.py` reading `7 passed` with zero errors.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: either `git diff -- tests/test_scope_exceeded.py` of the repair plus a re-run showing `7 passed`, or a "no change required" record citing V-01/V-02; in both cases the pasted summary of a bare `python3 -m pytest` run showing no failure attributed to `tests/test_scope_exceeded.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. The executor follows the AGENTS.md execution contract: commit only `tests/test_scope_exceeded.py` (if changed) via `aw commit 3or4ce -- tests/test_scope_exceeded.py`, never push, and paste actual runner output. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass`.
