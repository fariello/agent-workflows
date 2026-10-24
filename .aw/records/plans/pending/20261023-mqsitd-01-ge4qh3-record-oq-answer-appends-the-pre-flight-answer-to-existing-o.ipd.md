# IPD: record_oq_answer appends the pre-flight answer to existing OQ rationale

- Date: 2026-10-23
- Kind: child
- Concern: The runner pre-flight question sweep (`aw oc run` / `aw agy run`) and `aw runs answer` write a human's answer into an artifact's `### OQ-*` block through `runner_shared.record_oq_answer`. That function substitutes the whole `- Resolution or deferral rationale:` line, including indented continuation lines (`rationale_pattern.sub(rationale_line, new_block, count=1)`), so any author text already in the field is silently and permanently lost. This is the same overwrite plan `lf4j52` forbids for agents as defect D-7. Backlog `mqsitd` (Work-Kind bug, Blocks-Release next; maintainer confirmed via /askme 2026-10-23: change the runner to append).
- Scope: Change only the existing-rationale branch of `runner_shared.record_oq_answer` so it appends `RESOLVED <date> by <who> via <channel>: <answer>` after the existing text (writing the `RESOLVED ...` text alone when the field is empty); update that function's docstring; add behavioral tests in `tests/test_question_preflight.py`. The status rewrite, hash refusal, Blocking/Owner invariance and the no-rationale-line insertion branch are unchanged.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_question_preflight.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: mqsitd
- Blocks-Release: next
- Set: mqsitd
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: ge4qh3
- Approval: 2026-10-24, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-24 approved (aw set): status set to approved
- 2026-10-24 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Re-verified F-1 at the lane HEAD and demonstrated F-2 by direct call (`\1` raises `re.error`; `\n` becomes a newline).

- 2026-10-23 draft (opencode): created.
- 2026-10-23 to-review (opencode): authored review-ready from backlog mqsitd (graduation turn).

## Goal

Make the runner's durable OQ write-back append the recorded answer to whatever rationale text the author already wrote, so the record keeps both what was asked or reasoned and what was decided, and prove it with a test that pre-existing rationale text survives the write.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Append instead of replace

- [ ] E-01 In `runner_shared.record_oq_answer`, replace the `rationale_pattern.sub(rationale_line, new_block, count=1)` call in the `if rationale_pattern.search(new_block):` branch with an append: keep the matched field text (first line plus any indented continuation lines) verbatim and strip trailing whitespace from the last line of the field and add ` RESOLVED {date} by {who} via {channel}: {answer}` (one separating space) at its end; when the existing field value is empty or whitespace only, emit `- Resolution or deferral rationale: RESOLVED {date} by {who} via {channel}: {answer}` exactly as today. Use a replacement function (not a replacement string) so backslashes or group references in the answer or existing text are written literally; today an answer containing `\1` makes `re.sub` raise `re.error` (invalid group reference), which propagates out of `record_oq_answer` uncaught at both call sites, and `\n` in an answer is written as a real newline (F-2). Leave the no-rationale-line insertion branch, the status rewrite, the hash refusal, and the Blocking/Owner invariance checks untouched. Update the docstring bullet `- Resolution or deferral rationale: RESOLVED ...` to say the text is appended to any existing rationale.
  - Depends on: none
  - Expected outcome: `record_oq_answer` on a block whose rationale reads `Pending: depends on vendor reply.` produces `- Resolution or deferral rationale: Pending: depends on vendor reply. RESOLVED <date> by <who> via <channel>: <answer>`; on a present-but-empty rationale field (`- Resolution or deferral rationale:` with nothing after it) it produces exactly `- Resolution or deferral rationale: RESOLVED <date> by <who> via <channel>: <answer>` (no double space), the same line it produces today; an answer containing `C:\new\1` is written literally and raises nothing.
  - Execution state: pending

### Task group 2: Behavioral tests

- [ ] E-02 Add a test to `tests/test_question_preflight.py` that builds a plan via `_create_plan_with_oqs` with an OQ carrying `"rationale": "Original question context: SQLite or Postgres?"`, calls `runner_shared.record_oq_answer` with a matching `expected_hash`, and asserts it returns True, the file still contains the original rationale text, the line reads `- Resolution or deferral rationale: Original question context: SQLite or Postgres? RESOLVED 2026-10-17 by developer via aw oc run pre-flight: Use PostgreSQL 16 JSONB`, `- Status: resolved` is present, and `- Blocking: yes` / `- Owner: test author` are unchanged. Add a second case where the existing rationale has an indented continuation line (written directly into the fixture file) and assert both the first line and the continuation line survive and the `RESOLVED ...` text appears once, after them. Add a third case whose answer is `C:\new\1` and assert the call returns True without raising and the written rationale line ends with the literal `: C:\new\1`. Add a fourth case whose fixture carries a present-but-empty field (`- Resolution or deferral rationale:` written directly into the fixture file) and assert the line reads exactly `- Resolution or deferral rationale: RESOLVED 2026-10-17 by developer via aw oc run pre-flight: Use PostgreSQL 16 JSONB`. Mark each new test `@pytest.mark.core` (the module carries no core marker, so without it the bare routine gate never runs them; each takes about 0.03 s, measured at review on the existing A40 test).
  - Depends on: E-01
  - Expected outcome: four new core-marked tests; against the unmodified function the first two fail (original text lost) and the third errors with `re.error`, while the fourth passes before and after (it pins the empty-field shape); all four pass after E-01.
  - Execution state: pending

- [ ] E-03 Run the existing preflight tests unchanged, including `test_a40_durable_artifact_write_back` (its fixture writes no prior rationale, so it exercises the insertion branch and its exact-line assertion must still hold) and `test_stale_artifact_refusal`, then the routine core gate `python3 -m pytest`. Note the module is otherwise not core-marked, so the bare gate runs only the four new tests from this file; the explicit-path run is what exercises the rest of the file.
  - Depends on: E-02
  - Expected outcome: `tests/test_question_preflight.py` fully passes and the core gate reports no failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests must exercise behavior and assert on real outputs and file side effects, never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). The new tests call `record_oq_answer` and read the written artifact.
- Test fixture helper `tests/test_question_preflight.py::_create_plan_with_oqs` already accepts a `rationale` key per OQ and writes `- Resolution or deferral rationale: <text>` after `- Owner:`; no fixture change is needed for the single-line case.
- Callers: `record_oq_answer` is called from the `aw runs answer` path (the call that logs reason "record_oq_answer failed or artifact hash moved") and from the pre-flight sweep (the call passing `answer=ans_clean, who=user_who, channel=channel_str`), both in `agent_workflows/runner_shared.py`. Neither passes or relies on prior rationale text, so the change needs no caller edits.
- Spec `6kwd2e` R1.5 / A40 (`.aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md`) require "a rationale naming the human and date" and `- Blocking:` unchanged; appending satisfies that wording, so no spec amendment is required.
- The `/askme` workflow already prescribes the append shape for agents (plan `lf4j52` E-02: "append the resolution after the existing rationale text, never delete or rewrite it ... when the field is empty, write the `RESOLVED ...` text alone"); this plan makes the runner match it.
- Commit through `aw commit <plan> -- <paths>`; never push.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Existing rationale text, including continuation lines, is replaced wholesale | `runner_shared.record_oq_answer`: `rationale_pattern = re.compile(r"(?m)^-[ \t]+Resolution or deferral rationale:[^\n]*(?:\n[ \t]+[^\n]*)*")` followed by `rationale_pattern.sub(rationale_line, new_block, count=1)` |
| F-2 | Current `re.sub` with a string replacement interprets backslashes in the answer: `\1` raises `re.error` out of `record_oq_answer`, `\n` becomes a real newline | same call passes `rationale_line` (built from the human's answer) as the replacement template; demonstrated at review 2026-10-24: answer `C:\new\1` raised `PatternError invalid group reference 1`, answer `C:\new` wrote `...: C:` then a line `ew`. Neither caller (`aw runs answer` path near reason "record_oq_answer failed or artifact hash moved"; pre-flight sweep loop) wraps the call in `try` |
| F-3 | Existing A40 test does not cover pre-existing rationale | `test_a40_durable_artifact_write_back` fixture OQ dict has no `rationale` key, so `_create_plan_with_oqs` writes no rationale line (checked 2026-10-23 in backlog `mqsitd`, re-checked during authoring) |
| F-4 | Same defect class as agent-side D-7 | plan `lf4j52` Concern: "D-7: the original question text in `- Resolution or deferral rationale:` is deleted and replaced instead of appended to" |

## Proposed changes (ordered, validatable)

1. E-01: append logic plus docstring in `agent_workflows/runner_shared.py` (validated by V-01).
2. E-02: four new core-marked behavioral tests in `tests/test_question_preflight.py` (validated by V-02).
3. E-03: regression run of existing preflight tests and the core gate (validated by V-03).

## Deferred / out of scope (with reason)

none. (Agent-side `/askme` recording is not deferred work of this plan; it is already planned in `lf4j52`.)

## Scope check

- Over-scope: none.
- Under-scope: none; the only writer of the runner's OQ answers is `record_oq_answer`, and both callers route through it.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_question_preflight.py -v` must show the four new tests and the existing `test_a40_durable_artifact_write_back` and `test_stale_artifact_refusal` passing (V-02, V-03).
- `python3 -m pytest` (core gate) must report no failures (V-03).
- Before E-01, the new tests from E-02 are expected to fail on the first two cases and error on the third. The executor may demonstrate this (optional, strengthens V-02) by writing the E-02 tests BEFORE making the E-01 edit and running them once; do not use `git stash` or any revert to recreate the unmodified function.
- The bare core gate is a regression gate here; it runs only the four new core-marked tests from this module.

## Spec / documentation sync

- N/A: spec `6kwd2e` R1.5 and A40 require only a rationale naming the human and date, which the appended form still provides; the function docstring is updated in E-01. No user-facing docs describe the overwrite. No CHANGELOG entry is needed: `record_oq_answer` was introduced by commit `eb85f275d` (work 4kkcex), which is not an ancestor of the latest tag `v1.3.0-rc.1`, so the overwrite never shipped; the existing pending-2.0.0 entries describing the pre-flight sweep and `aw runs answer` remain accurate.

## Open questions

None. The one design question (append vs replace) was decided by the maintainer via /askme on 2026-10-23 and is recorded in backlog `mqsitd` workflow history.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` of `agent_workflows/runner_shared.py` showing the existing-rationale branch now appends via a replacement function, the empty-field case still emits the bare `RESOLVED ...` line, the docstring updated, and no other hunks in that file.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the actual output of `python3 -m pytest -o addopts="" tests/test_question_preflight.py -v -k "rationale"` (or the new tests' names) showing each of the four new tests PASSED, plus the `git diff` of `tests/test_question_preflight.py` showing the `@pytest.mark.core` markers and the assertions on preserved original text, preserved continuation line, single `RESOLVED` occurrence, literal backslash answer with no exception, and the exact empty-field line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the actual summary line of `python3 -m pytest -o addopts="" tests/test_question_preflight.py` showing all tests passed including `test_a40_durable_artifact_write_back` and `test_stale_artifact_refusal`, and the actual `N passed` summary line of the bare `python3 -m pytest` core gate with zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Tests assert observable behavior (return values and written file content), never source text (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). Commit only files you changed, through `aw commit ge4qh3 -- agent_workflows/runner_shared.py tests/test_question_preflight.py`, and verify `git diff --cached --name-only` lists only your paths; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*` Observed evidence; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every `V-*` reads `Result: pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
