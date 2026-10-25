# IPD: Add the AW-REVIEW re-review marker, runner triggers, and the bounded re-review loop

- Date: 2026-10-24
- Kind: child
- Concern: A review that edits a plan can leave its own edits unreviewed: an E/V pair added in the S5 questions step is never checked by R2. Spec `k3yx72` (approved) Section 8 closes this with a re-review loop: the agent ends check S6 with `AW-REVIEW: AGAIN` or `AW-REVIEW: DONE` (MD-3), the runner also forces a pass when the plan's structure changed (Section 8.2), at most two passes run, and the verdict is written only after the loop ends (MD-15). Order 04 sends S6 once and, by design, delegates the marker and the loop to this plan when it is present. This is the Stage 1 part of spec Section 15 Order 05 (MD-20); the no-go clearing path of Section 9.4 is Stage 2 and is not in this plan.
- Scope: Add `agent_workflows/review_rereview.py` with the marker parser, the trigger check, and the loop driver that Order 04's `runner_shared.run_review_sequence` calls; record each pass in the review record layout (`### Pass <k>`) expectations and in run state; enforce the two-pass limit with the `no-go` plus blocking-question rule. EXCLUDES the `AW-MATERIAL` marker, `aw ipd recheck-readiness` automation, and targeted re-review after a human answer (spec Section 9.4, Stage 2), and any change to the single-turn `--review-mode single` path.
- Scope-Paths: agent_workflows/review_rereview.py, agent_workflows/runner_shared.py, tests/test_review_rereview.py, CHANGELOG.md
- Item-Dependencies: executed:uiyoax
- Status: to-review
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- From-Spec: k3yx72
- Set: revsteps
- Order: 5
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: is2xiv

## Workflow history
- 2026-10-25 to-review (aw set): authored review-ready from spec k3yx72 Stage 1 (MD-20)

- 2026-10-25 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make a steps-mode review re-check its own material edits at most twice before the verdict, decided by an exact reply marker and by runner-detected structural changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: marker and triggers (pure)

- [ ] E-01 Create `agent_workflows/review_rereview.py` with `parse_rereview_marker(reply_text: str) -> str | None` per spec Section 8.1: only the last non-empty line counts; surrounding whitespace is ignored; a trailing code-fence line is ignored; otherwise the comparison is exact and case-sensitive against `AW-REVIEW: AGAIN` and `AW-REVIEW: DONE`; returns `"AGAIN"`, `"DONE"`, or `None`. The reply text is extracted by the caller with `runner_shared.probe_reply_text` (rule 5); `classify_probe_reply` is not used.
  - Depends on: none
  - Expected outcome: the function returns `None` for a lowercase marker, a marker not on the last line, and a reply with no marker.
  - Execution state: pending

- [ ] E-02 In `review_rereview.py`, add `rereview_triggers(pass_start_text: str, now_text: str, *, confirm_after_r: bool) -> list[str]` per spec Section 8.2, over `ipd_lint.parse`: returns a reason for each of E/V items added or removed, `- Scope-Paths:` changed, `- Item-Dependencies:` changed, and (when `confirm_after_r`) a confirm-only change of Order 04's `review_sequence.structural_diff` made after the pass's R2/R4 checks ran. The baseline is the plan at the START OF THE CURRENT PASS; an empty list means no trigger.
  - Depends on: none
  - Expected outcome: adding one E/V pair yields one reason; a pass that changes nothing yields an empty list.
  - Execution state: pending

### Task group 2: the loop

- [ ] E-03 In `review_rereview.py`, add `run_rereview_loop(ctx) -> RereviewResult`, where `ctx` is the small context object Order 04's `run_review_sequence` already holds (send-prompt callable, tier, variant, checks already run, plan path, review-record path, the plan text at the start of the pass). It: (1) reads the S6 reply marker; on `None`, re-asks once in the same session for the marker only (the `runner_shared.perform_defect_reask` single-re-ask pattern); a second failure returns `incomplete` (rule 3: a malformed marker is never `AGAIN` and never `no-go`); (2) computes triggers against the pass-start text; (3) when the marker is `AGAIN` or any trigger fired, starts pass k+1: sends the tier's review checks (`Q` or `R1` to `R7`, grouped as the tier's prompt list groups them) with the instruction to limit them to the changed sections and the sections that depend on them, plus the `git diff --no-index` of the plan file from the start of the previous pass to the start of this pass (Section 8.3), then `S5+S6`; never `S7`; (4) ends when the marker is `DONE` and no trigger fired, or after two re-review passes. Each pass instructs the agent to add a `### Pass <k>` subsection naming the checks it re-ran (spec Section 7.1). Host failures are raised to the caller before any marker is parsed (rule 4).
  - Depends on: E-01, E-02
  - Expected outcome: the loop returns `done`, `limit-reached`, or `incomplete`, with the list of passes run.
  - Execution state: pending

- [ ] E-04 Limit rule (spec Section 8.3): when the loop returns `limit-reached` (the second re-review pass still produced `AGAIN` or a trigger), the S7 prompt that Order 04 sends next carries an added instruction: write `- Readiness: no-go` and add an open question `Blocking: yes` naming what still changed (the trigger reasons and the marker), so `aw ipd recheck-readiness` can clear it after a human looks. Add a postcondition for that S7 prompt, checked by the runner: `- Readiness:` is `no-go` and an open question with `Blocking: yes` and `Status: open` was added in this invocation; on failure, one re-ask, then `incomplete`.
  - Depends on: E-03
  - Expected outcome: a fixture that triggers after pass 2 ends `completed-negative` with a `Blocking: yes` question.
  - Execution state: pending

- [ ] E-05 Wire the loop into Order 04's `runner_shared.run_review_sequence` at its S6 delegation point (Order 04 E-06 item 6), record each pass in `attempt["review_steps"]` with its pass number (Order 04 E-11 schema already has `pass`), and confirm the verdict-output guard (Order 04 E-08) applies to every prompt of every pass, so no pass before S7 writes a verdict.
  - Depends on: E-03, E-04
  - Expected outcome: a steps-mode review records pass numbers 1 to 3 in `review_steps` when two re-review passes run.
  - Execution state: pending

### Task group 3: tests and commit

- [ ] E-06 Add `tests/test_review_rereview.py`, marked `core` for its pure cases: marker parsing (valid, trailing fence, lowercase, not last line, both sentinels in the body with `DONE` last); triggers (E/V added, Scope-Paths changed, nothing changed). Runner cases on both hosts with the Order 04 scripted-host harness of `tests/test_review_sequence_runner.py`, covering spec acceptance criteria AC-03 (a malformed `AW-REVIEW:` line causes exactly one re-ask, and a second failure ends `incomplete` with no `- Readiness:` written and the plan at `to-review`), AC-04 (a pass that changes nothing ends the loop; first pass adds an E/V pair, second changes nothing, result `completed-pass`; a fixture that still triggers after the second re-review pass ends `no-go` with a `Blocking: yes` question naming the change), AC-05 (a finding recorded in pass 1 and not fixed still gates after pass 2: it is in the round's single `### Findings` table and `review_findings.subject_gating_blocks` reports it), AC-06 (one invocation with two passes yields exactly one verdict-bearing history entry and exactly one `plan-review:` commit; progress entries without a verdict token are ignored by `plan_readiness.newest_verdict`), and AC-07 second half (interrupted after pass 1, the plan stays `to-review` with no new `- Readiness:`).
  - Depends on: E-05
  - Expected outcome: a passing module on both hosts.
  - Execution state: pending

- [ ] E-07 Add one `CHANGELOG.md` entry (a steps-mode review re-checks its own edits at most twice before its verdict), no em or en dashes. Run `python3 -m pytest -o addopts="" -n auto tests/test_review_rereview.py tests/test_review_sequence.py tests/test_review_sequence_runner.py tests/test_defect_report.py`, the bare core gate `python3 -m pytest`, and `aw check`; commit through `aw commit is2xiv -- <each changed path>`. Never push.
  - Depends on: E-06
  - Expected outcome: both pytest runs pass; `aw check` reports no error and no warning this plan introduced; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.perform_defect_reask` is the existing one-re-ask-never-loop primitive; E-03 follows its shape.
- `runner_shared.probe_reply_text` extracts reply text for both hosts; `classify_probe_reply` reads the first line and is wrong for this marker (spec Section 8.1 rule 5).
- `review_findings.parse_review_text` reads finding rows only under a `Findings` heading, so `### Pass <k>` subsections do not affect gating.
- Order 04 (`uiyoax`) owns the sequence, the verdict guard, and `review_steps`; this plan plugs into its S6 delegation point.

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -n "AW-REVIEW" agent_workflows` returns nothing | No marker parser exists. |
| F-02 | Spec `k3yx72` MD-15, Section 8.3 | The loop runs before S7, so a re-review can never leave a stale verdict. |
| F-03 | Spec `k3yx72` MD-20 | The no-go clearing path (Section 9.4) is Stage 2; this plan is the Stage 1 "marker and loop only" part. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: marker and triggers.
2. E-03 to E-05: loop, limit rule, wiring.
3. E-06, E-07: tests, gates, commit.

## Deferred / out of scope (with reason)

- Section 9.4 no-go clearing (`AW-MATERIAL`, recheck, targeted re-review): Stage 2 of spec Section 15 Order 05, authored only after Order 09 records BUILD THE REST.

## Scope check

- Over-scope: none.
- Under-scope: none. Spec Section 8 (8.1, 8.2, 8.3) is covered; AC-03 to AC-07 (second half) are tested.

## Required tests / validation

- AC-03, AC-04, AC-05, AC-06, AC-07 (second half) on both hosts: E-06.
- Commands: E-07 named run, bare core gate, `aw check`, summaries pasted.

## Spec / documentation sync

N/A: spec `k3yx72` Section 8 already specifies this behavior, and runner spec `25kzda` is amended for multi-prompt reviews by Order 04 (`uiyoax`). No user-facing doc names the loop beyond the CHANGELOG entry.

## Open questions

### OQ-01: Should the re-review pass send the full prompt groups or one combined prompt?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The tier's own groups (E-03), so a pass has the same runner-visible units as the first pass and the pilot measures one design, not two. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_rereview.py -k marker` with every selected test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_rereview.py -k trigger` with every selected test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the E-06 runner test output for AC-04's two-pass fixture on both hosts, quoting the asserted pass count (observation produced by `review_rereview.run_rereview_loop` through `runner_shared.run_review_sequence`).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the E-06 test output for the limit-reached fixture, quoting the asserted `Readiness: no-go` and the `Blocking: yes` question.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `git diff` of the `run_review_sequence` delegation point and the E-06 assertion on `review_steps` pass numbers.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_rereview.py` with every test PASSED and none skipped.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the summary lines of the E-07 named run and the bare `python3 -m pytest`, the `aw check` summary compared with the baseline taken before E-01, and the `aw commit` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit is2xiv -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
