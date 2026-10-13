# IPD: Verify and close tests/test_scope_exceeded.py setUp mint_driver_attestation regression

- Date: 2026-10-12
- Kind: child
- Concern: tests/test_scope_exceeded.py setUp called ipd_lifecycle.mint_driver_attestation, which e25iy9 (commit 86181232a) deleted, so all 7 cases errored on main.
- Scope: Confirm the already-landed fix (commit 64b8c94f3) holds on the current tree, that no caller of the deleted symbol remains anywhere in tests or the package, and repair tests/test_scope_exceeded.py only if either check fails.
- Scope-Paths: tests/test_scope_exceeded.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: u18kic
- Blocks-Release: next
- Set: u18kic
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 3or4ce
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004. Record: .aw/records/reviews/20261012-u18kic-01-3or4ce-verify-and-close-tests-test-scope-exceeded-py-setup-mint-dri.review.md Round 1

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog u18kic; repository evidence shows the defect already fixed by 64b8c94f3, so the plan verifies and closes rather than re-implements.

## Goal

Graduate backlog `u18kic` by proving, with pasted runner output, that `tests/test_scope_exceeded.py` no longer depends on the deleted `ipd_lifecycle.mint_driver_attestation` and that its 7 cases pass, repairing the file only if the evidence shows a residual failure.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm the fix and the absence of residual callers

- [x] E-01 Search the tracked package and test tree for any remaining reference to `mint_driver_attestation`: `git grep -n mint_driver_attestation -- agent_workflows tests` (exit 1 means no match). Markdown records under `.aw/records/` legitimately mention the name as history and are not callers.
  - Depends on: none
  - Expected outcome: zero matches in `agent_workflows/` and `tests/`; any match is recorded as a finding for E-03.
  - Execution state: performed

- [x] E-02 Run the module's tests with per-test output: `python3 -m pytest -o addopts="" -v tests/test_scope_exceeded.py`.
  - Depends on: none
  - Expected outcome: every collected test in the module passes, with zero errors and zero failures, and the collected set includes every `test_*` method of `TestScopeExceededMetadataAndSendBack` (7 at authoring and at review; context, not the bar).
  - Execution state: performed

### Task group 2: Conditional repair

- [x] E-03 If E-01 found a reference inside `tests/test_scope_exceeded.py` or E-02 reported a failure, remove the stale attestation setup from `TestScopeExceededMetadataAndSendBack.setUp` (finalize no longer reads the attestation, per commit 64b8c94f3's message) and re-run E-02; otherwise record "no change required" with the E-01/E-02 evidence.
  - Depends on: E-01, E-02
  - Expected outcome: either a minimal diff to `tests/test_scope_exceeded.py` followed by a passing re-run, or an explicit no-change record. In both cases, run the bare suite `python3 -m pytest` and record its summary line.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The suite is run bare as `python3 -m pytest` (AGENTS.md repo-local development contract); a narrowed run that needs per-test output clears the defaults with `-o addopts=""`.
- Commits go through `aw commit <plan> -- <paths>` (AGENTS.md execution contract).
- Tests must exercise behavior, not pin source text (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); hence no new test asserting the symbol's absence is added. The grep in E-01 is a one-off executor check, not a committed test.
- Cite by symbol: `TestScopeExceededMetadataAndSendBack.setUp` in `tests/test_scope_exceeded.py`; deleted symbol `agent_workflows.ipd_lifecycle.mint_driver_attestation`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The deleted-symbol call was removed from setUp on 2026-10-09. | `git log -- tests/test_scope_exceeded.py` shows `64b8c94f3 test(scope_exceeded): drop the deleted driver-attestation setup (fixes 7 red tests on main)`, a 7-line deletion in that file. |
| F-2 | The current setUp no longer references the symbol. | `TestScopeExceededMetadataAndSendBack.setUp` now only declares the execution role, makes a temp git repo, builds the parser, and creates the run dir. |
| F-3 | The module passes at authoring time. | `python3 -m pytest tests/test_scope_exceeded.py` printed `7 passed in 6.97s` on 2026-10-12 in this lane. |
| F-4 | No other `.py` file in the tree references the symbol at authoring time. | `grep -rn mint_driver_attestation --include=*.py .` returned no matches; re-checked at review with `git grep -n mint_driver_attestation -- ':!*.md'` (no output). |
| F-5 | `u18kic` is the THIRD backlog item for this one defect. `fdkkco` and `i6dzbj` were filed the same day and are already `done`, both closed with walkthrough `04qifi` as evidence, which records `64b8c94f3` as "closes `fdkkco` and its duplicate `i6dzbj`". `u18kic` was missed by that close. | `.aw/records/backlog/done/20261009-fdkkco-01-...backlog.md` and `...-i6dzbj-...backlog.md` (`- Close-Evidence: .aw/records/walkthroughs/20261009-runfix1009-01-04qifi-run-failure-recovery-2026-10-09.walkthrough.md`); walkthrough line naming `64b8c94f3`. |

The backlog item was filed the same day the fix landed and was never closed (its two duplicates were, F-5); this plan supplies the evidence to close it. Because `u18kic` carries `- Blocks-Release: next` and this plan is its only `From-Backlog` carrier with the same gate, it closes through the HANDOFF rule once this plan is `executed` (the runner's `process_backlog_close` when run under `aw oc run`/`aw agy run`; otherwise `aw backlog set done u18kic --evidence <this plan's executed path>`).

## Proposed changes (ordered, validatable)

1. E-01/E-02: verification only, no file changes expected.
2. E-03: conditional minimal edit to `tests/test_scope_exceeded.py` setUp only if verification fails.

## Deferred / out of scope (with reason)

- `h3fnoc` (scope-reconciliation send-back misclassification) and `8o7gco` (checkout git identity overwritten), filed in the same commit 64b8c94f3, are separate backlog items with their own lifecycle; not touched here.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Adding a test that pins absence of the symbol is out of scope: it would be a code-pinning test, which the repository forbids.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none; the only file the defect touches is `tests/test_scope_exceeded.py`, and the full-suite run in V-03 covers regressions elsewhere.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_scope_exceeded.py`: every collected test passes with no error (V-02, V-03).
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

- [x] V-01 validates E-01
  - Required evidence: pasted output and exit status of `git grep -n mint_driver_attestation -- agent_workflows tests` showing no matches (exit status 1), or the listed matches with their disposition under E-03.
  - Observed evidence:
    ```
    $ git grep -n mint_driver_attestation -- agent_workflows tests
    Exit status: 1
    Matches: none
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted per-test `-v` output and summary line from `python3 -m pytest -o addopts="" -v tests/test_scope_exceeded.py`, showing every collected test `PASSED` with zero errors and zero failures.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_scope_exceeded.py
    tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_a_finalize_inserts_scope_exceeded_metadata PASSED [ 14%]
    tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_e_commit_scope_reason_recording_only_without_paths PASSED [ 28%]
    tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_f_commit_scope_reason_rejects_paths_not_out_of_scope PASSED [ 42%]
    tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_d_runner_retry_loop_out_of_scope_notice PASSED [ 57%]
    tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_b_finalize_leaves_metadata_untouched_when_fully_in_scope PASSED [ 71%]
    tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_g_recorded_scope_justifications_survive_recovery_rebegin PASSED [ 85%]
    tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_c_multiple_out_of_scope_paths_sorted_and_sanitized PASSED [100%]

    ============================== 7 passed in 8.17s ===============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: either `git diff -- tests/test_scope_exceeded.py` of the repair plus a pasted re-run with every collected test passing, or a "no change required" record citing V-01/V-02; in both cases the pasted summary of a bare `python3 -m pytest` run showing no failure attributed to `tests/test_scope_exceeded.py`.
  - Observed evidence:
    No change required: V-01 confirmed zero matches for `mint_driver_attestation` in `agent_workflows` and `tests` (exit code 1), and V-02 confirmed all 7 tests in `tests/test_scope_exceeded.py` pass with zero failures and zero errors. The regression was already fixed in commit 64b8c94f3.

    Bare suite summary (`python3 -m pytest`):
    ```
    7615 passed, 2 skipped, 3 warnings in 701.49s (0:11:41)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Open questions: OQ-01 is resolved; none remain. `- Scope-Paths:` is a DECLARATION reconciled at finalize: an out-of-scope edit that proves necessary is made and justified with `--scope-reason`, and an unmodified `tests/test_scope_exceeded.py` (the expected no-change outcome) is acknowledged with `--scope-ack`. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no output does not satisfy it. Start with `aw ipd begin 3or4ce`. Commit only `tests/test_scope_exceeded.py` (if changed) through `aw commit 3or4ce -- tests/test_scope_exceeded.py` (never `git add -A`, `-a`, or `--no-verify`), verify the staged set with `git diff --cached --name-only` first, and never push. The terminal transition is MANDATORY and its owner is conditional: under `aw oc run` / `aw agy run` the runner performs the finalize after its merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize`; executed by hand, the executor runs `aw ipd finalize 3or4ce` once `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass`. Never hand-roll the move or `git mv` this plan into `executed/`. Release gate: keep the inherited `- Blocks-Release: next`; the item `u18kic` closes through the HANDOFF rule after this plan executes (see the Findings note), not by hand before it.
