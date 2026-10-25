# IPD: Add the AW-REVIEW re-review marker, runner triggers, and the bounded re-review loop

- Date: 2026-10-24
- Kind: child
- Concern: A review that edits a plan can leave its own edits unreviewed: an E/V pair added in the S5 questions step is never checked by R2. Spec `k3yx72` (approved) Section 8 closes this with a re-review loop: the agent ends check S6 with `AW-REVIEW: AGAIN` or `AW-REVIEW: DONE` (MD-3), the runner also forces a pass when the plan's structure changed (Section 8.2), at most two passes run, and the verdict is written only after the loop ends (MD-15). Order 04 sends S6 once and, by design, delegates the marker and the loop to this plan when it is present. This is the Stage 1 part of spec Section 15 Order 05 (MD-20); the no-go clearing path of Section 9.4 is Stage 2 and is not in this plan.
- Scope: Add `agent_workflows/review_rereview.py` with the marker parser, the trigger check, and the loop driver that Order 04's `runner_shared.run_review_sequence` calls; record each pass in the review record layout (`### Pass <k>`) expectations and in run state; enforce the two-pass limit with the `no-go` plus blocking-question rule. EXCLUDES the `AW-MATERIAL` marker, `aw ipd recheck-readiness` automation, and targeted re-review after a human answer (spec Section 9.4, Stage 2), and any change to the single-turn `--review-mode single` path.
- Scope-Paths: agent_workflows/review_rereview.py, agent_workflows/runner_shared.py, tests/test_review_rereview.py, CHANGELOG.md
- Item-Dependencies: executed:uiyoax
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- From-Spec: k3yx72
- Set: revsteps
- Order: 5
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: is2xiv
- Approval: 2026-10-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-25 approved (aw set): status set to approved
- 2026-10-25 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED
- 2026-10-25 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED; review record .aw/records/reviews/20261024-revsteps-05-is2xiv-add-the-aw-review-re-review-marker-runner-triggers-and-the-b.review.md
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

- [ ] E-02 In `review_rereview.py`, add `rereview_triggers(pass_start_text: str, now_text: str, *, after_r_text: str | None) -> list[str]` per spec Section 8.2, over `ipd_lint.parse`: returns a reason for each of (a) the set of `E-*`/`V-*` ids (`exec_leaves`/`valid_leaves` idents) differs between `pass_start_text` and `now_text` (added or removed, naming the ids); (b) the `Scope-Paths` meta value changed; (c) the `Item-Dependencies` meta value changed; (d) when `after_r_text` is not `None` (the plan text captured right after the pass's last prompt containing `R2` or `R4`), `review_sequence.structural_diff(after_r_text, now_text)` (Order 04 `uiyoax` E-04) returns any confirm-only entry, i.e. a confirm-listed item changed after R2/R4 ran. `after_r_text is None` (a tier or pass with no R2/R4 prompt, for example `simple` or `orchestrator` without R4) disables (d). The baseline for (a) to (c) is the plan at the START OF THE CURRENT PASS; an empty list means no trigger.
  - Depends on: none
  - Expected outcome: adding one E/V pair yields one reason; changing `- Scope-Paths:` yields one reason; rewording an `Expected outcome` after R2/R4 (with `after_r_text` given) yields one reason and the same edit with `after_r_text=None` yields none; a pass that changes nothing yields an empty list.
  - Execution state: pending

### Task group 2: the loop

- [ ] E-03 In `review_rereview.py`, add `run_rereview_loop(ctx: review_sequence.ReviewSequenceContext, s6_reply: str, *, after_r_text: str | None) -> RereviewResult`, where `ctx` is the object Order 04 (`uiyoax` E-06) defines in `review_sequence.py` and names in its docstring (`send_prompt`, `tier`, `variant`, `checks_run`, `plan_path`, `review_path`, `pass_start_text`, `pass_no`, `baseline`, `review_steps`), `s6_reply` is the pass-1 S6 reply text Order 04 obtained, and `after_r_text` is the pass-1 plan text after its last R2/R4 prompt (`None` when none ran). Every prompt is sent through `ctx.send_prompt`, which is Order 04's per-prompt path (postconditions, one re-ask, verdict-output guard, `review_steps` entry); this function never calls a launcher. `RereviewResult` is a NamedTuple `(outcome: "done" | "limit-reached" | "incomplete", passes: int, reasons: list[str], marker: str | None)`. It: (1) parses the S6 marker with E-01; on `None`, sends one marker-only re-ask through `ctx.send_prompt` (text: `Your last reply did not end with the re-review marker. Reply with exactly one last line: AW-REVIEW: AGAIN or AW-REVIEW: DONE.`), the one-re-ask-never-loop shape of `runner_shared.perform_defect_reask` (that function is defect-report specific and is not called); a second `None` returns `incomplete` (spec `k3yx72` Section 8.1 rule 3: a malformed marker is never `AGAIN` and never `no-go`); the same rule applies to the S6 reply of every pass; (2) computes `rereview_triggers(ctx.pass_start_text, <plan text now>, after_r_text=...)`; (3) when the marker is `AGAIN` or any trigger fired and fewer than two re-review passes have run, starts pass k+1: sets `ctx.pass_no = k+1` and `ctx.pass_start_text` to the current plan text, then sends, one prompt per group, the tier's prompt groups with `P`, `T`, `S5`, `S6`, `S7` removed and only checks in `ctx.checks_run` kept, empty groups dropped (so `simple` re-sends `Q`, `orchestrator` re-sends `R1+R2` then `R7`), each carrying the instruction to limit the check to the changed sections and the sections that depend on them, the trigger reasons and marker that started the pass, and (first prompt of the pass) the `git diff --no-index` of the plan file from the start of the previous pass to the start of this pass (spec Section 8.3); then `S5+S6`; never `S7`; (4) after each re-review pass's S6 reply, repeats (1) and (2); returns `done` when the marker is `DONE` and no trigger fired, and `limit-reached` when the second re-review pass (pass 3) still yields `AGAIN` or a trigger. Each re-review pass's first prompt instructs the agent to add a `### Pass <k>` subsection to the current `## Round <n>` naming the checks it re-ran (spec Section 7.1), and to record any history progress note only as `- <date> review progress (<agent/model>): ...` (`uiyoax` E-03). Any host failure or `incomplete` signal from `ctx.send_prompt` propagates unchanged and is not caught here, so a host failure is handled before any marker is parsed (rule 4).
  - Depends on: E-01, E-02
  - Expected outcome: the loop returns `done`, `limit-reached`, or `incomplete`, with the number of passes run and the trigger reasons.
  - Execution state: pending

- [ ] E-04 Limit rule (spec `k3yx72` Section 8.3): in `review_rereview.py` add the pure pieces `limit_reached_instruction(result: RereviewResult) -> str` (write `- Readiness: no-go` and add an open question with `Blocking: yes` and `Status: open` naming what still changed: the trigger reasons and the marker, so `aw ipd recheck-readiness` can clear it after a human looks) and `check_limit_s7(plan_before: str, plan_after: str) -> str | None` (`None` when `ipd_schema.read_readiness` of `plan_after` is `no-go` and `ipd_lint.parse(plan_after).open_questions` holds a question id absent from `plan_before` with `Blocking: yes` and `Status: open`; otherwise the failed postcondition text). In `runner_shared.run_review_sequence`, when the loop returns `limit-reached`, append that instruction to the S7 prompt Order 04 sends next and run `check_limit_s7` beside Order 04's `check_S7`; on failure, one re-ask, then `incomplete`.
  - Depends on: E-03
  - Expected outcome: a fixture that triggers after pass 2 ends `completed-negative` with a `Blocking: yes` question.
  - Execution state: pending

- [ ] E-05 Wire the loop into Order 04's `runner_shared.run_review_sequence` at its S6 delegation point (`uiyoax` E-06 item 6): call `review_rereview.run_rereview_loop(ctx, s6_reply, after_r_text=...)`, map `incomplete` to Order 04's `incomplete` outcome (E-09 there), and send S7 only after `done` or `limit-reached`. Make sure `ctx.send_prompt` is the same per-prompt path pass 1 uses, so the verdict-output guard (`uiyoax` E-08), the postconditions and one re-ask (`uiyoax` E-07), and the `attempt["review_steps"]` entry with `pass = ctx.pass_no` (`uiyoax` E-11 schema) apply to every prompt of every pass; if Order 04's `send_prompt` is a raw send, wrap it here rather than duplicating those checks. Persist the loop state after each prompt as `attempt["rereview"] = {"pass": k, "pass_start_sha256": <hash of pass-start text, snapshot written as `uiyoax` E-11 does>, "reasons": [...], "after_r_sha256": <or null>}`, so Order 04's resume (`uiyoax` E-12) can rebuild `ctx.pass_start_text` and continue a re-review pass at its next prompt (the pass's prompt list is a pure function of tier, variant, and `checks_run`).
  - Depends on: E-03, E-04
  - Expected outcome: a steps-mode review records pass numbers 1 to 3 in `review_steps` when two re-review passes run, and `attempt["rereview"]` names the last pass.
  - Execution state: pending

### Task group 3: tests and commit

- [ ] E-06 Add `tests/test_review_rereview.py`, marked `core` for its pure cases: marker parsing (valid `AGAIN` and `DONE`, surrounding whitespace, trailing fence, lowercase, not last line, both sentinels in the body with `DONE` last); triggers (E/V added, Scope-Paths changed, Item-Dependencies changed, confirm-only change after R2/R4 with and without `after_r_text`, nothing changed); `check_limit_s7` (pass and fail). Runner cases on both hosts (through `oc_runipd.execute_item` and `agy_runipd.execute_item`, reusing the scripted-host harness of `tests/test_review_sequence_runner.py` by import, not by editing that file), covering spec acceptance criteria `k3yx72` AC-03 (a malformed `AW-REVIEW:` line causes exactly one re-ask, and a second failure ends `incomplete` with no `- Readiness:` written and the plan at `to-review`), `k3yx72` AC-04 (a pass that changes nothing ends the loop; first pass adds an E/V pair, second changes nothing, result `completed-pass`; a fixture that still triggers after the second re-review pass ends `completed-negative` with `- Readiness: no-go` and a `Blocking: yes` question naming the change), `k3yx72` AC-05 (a finding recorded in pass 1 and not fixed still gates after pass 2: it is in the round's single `### Findings` table and `review_findings.subject_gating_blocks` reports it), `k3yx72` AC-06 (one invocation with two passes yields exactly one verdict-bearing history entry and exactly one `plan-review:` commit; `review progress` entries are ignored by `plan_readiness.newest_verdict`), `k3yx72` AC-07 second half (interrupted after pass 1, the plan stays `to-review` with no new `- Readiness:`), a fixture that writes `- Readiness:` in a pass-2 prompt has it reverted and is re-asked (E-05 routing), and a fixture interrupted inside pass 2 resumes at that pass's next prompt with the pass-start text rebuilt (`k3yx72` AC-14 within a pass).
  - Depends on: E-05
  - Expected outcome: a passing module on both hosts.
  - Execution state: pending

- [ ] E-07 Add one `CHANGELOG.md` entry (a steps-mode review re-checks its own edits at most twice before its verdict), no em or en dashes. Run `python3 -m pytest -o addopts="" -n auto tests/test_review_rereview.py tests/test_review_sequence.py tests/test_review_sequence_runner.py tests/test_defect_report.py tests/test_rereview_reviewed_plan.py`, the bare core gate `python3 -m pytest`, `make test-all` (this plan changes `runner_shared.run_review_sequence`, runner core), and `aw check`; commit through `aw commit is2xiv -- <each changed path>`. Never push.
  - Depends on: E-06
  - Expected outcome: all three pytest runs pass; `aw check` reports no error and no warning this plan introduced; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.perform_defect_reask` is the existing one-re-ask-never-loop primitive; it validates a defect report (`validate_defect_report`), so E-03 follows its shape without calling it.
- `uiyoax` E-06 defines `review_sequence.ReviewSequenceContext` and the S6 delegation point; this plan consumes that object and adds the S6 reply and the after-R2/R4 text as explicit arguments, because the context does not carry them.
- History progress notes use the `review progress` label, never `/plan-review` (`uiyoax` E-03, `3bwrfx` E-09), because `plan_readiness.is_review_history_entry` reads any `/plan-review` line as a review record.
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
  - Carrier: kk62qt

## Scope check

- Over-scope: none.
- Under-scope: none. Spec Section 8 (8.1, 8.2, 8.3) is covered; `k3yx72` AC-03 to AC-06 and AC-07 second half are tested, plus resume inside a re-review pass (Section 9.3).

## Required tests / validation

- `k3yx72` AC-03, AC-04, AC-05, AC-06, AC-07 (second half) on both hosts, and resume inside a re-review pass (`k3yx72` AC-14): E-06.
- Commands: E-07 named run, bare core gate, `make test-all`, `aw check`, summaries pasted.

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
  - Required evidence: paste the E-06 runner test output for the `k3yx72` AC-03 and `k3yx72` AC-04 two-pass fixtures on both hosts, quoting the asserted pass count and the single marker re-ask (observation produced by `review_rereview.run_rereview_loop` through `runner_shared.run_review_sequence`).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the E-06 test output for the `k3yx72` AC-04 limit-reached fixture on both hosts, quoting the asserted `Readiness: no-go` and the `Blocking: yes` question, and the `check_limit_s7` pure-case output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `git diff` of the `run_review_sequence` delegation point, and the E-06 test output for the `review_steps` pass numbers 1 to 3, the pass-2 `- Readiness:` revert (`k3yx72` AC-07), the `k3yx72` AC-06 single verdict and single commit, and the in-pass resume (`k3yx72` AC-14), quoting each assertion.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_rereview.py` with every test PASSED and none skipped, showing the `k3yx72` AC-03, `k3yx72` AC-04, `k3yx72` AC-05, `k3yx72` AC-06 and `k3yx72` AC-07 cases ran on both hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the summary lines of the E-07 named run, the bare `python3 -m pytest`, and `make test-all`, the `aw check` summary compared with the baseline taken before E-01, and the `aw commit` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`); every open question is resolved. Scope fence: the paths in `- Scope-Paths:` are a declaration, not a stop condition; a needed file outside the fence is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit only through `aw commit is2xiv -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize is2xiv` itself.
