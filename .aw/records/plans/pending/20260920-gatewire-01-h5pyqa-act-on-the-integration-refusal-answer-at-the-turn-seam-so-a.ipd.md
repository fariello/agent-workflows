# IPD: Act on the integration-refusal answer at the turn seam so a lane is not lost to an unrelated red test

- Date: 2026-09-20
- Kind: child
- Concern: A lane's trust signal is a FULL TEST SUITE run, and a single red test refuses that lane's integration with NO way for the agent to say anything about it. Measured in run `run-20260919T194413Z-2056285`: one test unrelated to any lane's work went red, THREE lanes were refused, nothing merged, eight further items cascaded to `dependency-blocked`, and the run spent 2h 10m and $55.02 producing no integrated work. Every one of those lanes had done its job. The vocabulary to answer that refusal now EXISTS and is inert: `GATE_ANSWERS` (`not-mine`/`fixed`/`mine`/`needs-human`), `validate_gate_answer` and `gate_answer_question` are on main at `395fc06b`, and nothing reads them. This plan wires them in.
- Scope: IN: at the seam where `integration_is_earned` refuses for a suite failure, ask the agent the question, validate the answer, and act on it: `not-mine` integrates, `fixed` re-runs the full test suite and the RE-RUN decides, `mine` and `needs-human` refuse and preserve. Record the answer durably on the run record and surface `needs-human` in the run report. A failed `fixed` retries within the run's existing `--retry-budget`. OUT: any change to `integration_is_earned`'s own verdict logic (the gate stays hard 100% of the time), any new retry knob, any mechanical verification of a `not-mine` claim, and the review path (a review turn has no suite result to refuse on).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_gate_answer_wiring.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: gatewire
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: h5pyqa
- Approval: 2026-09-20, recorded via aw ipd set: status set to approved
- Blocks-Release: next
- Work-Kind: bug

## Workflow history
- 2026-09-20 approved (aw set): status set to approved
- 2026-09-20 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH) and PR-002 fixed; OQ-01 resolved from evidence, OQ-02 by maintainer ruling; readiness go-pending-approval

- 2026-09-20 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH) and PR-002 FIXED, none deferred, none open; readiness go-pending-approval. SELF-REVIEW DISCLOSED: I authored this plan, so the findings were kept mechanical and every claim was re-derived by executing code or reading a cited line. PR-001 is the one that mattered: the plan's central mechanism could not work, because it built the question from `suite_result.summary`, which `_SUITE_SUMMARY_RE` (oc_runipd.py:3845-3847) reduces to a COUNT LINE - measured, the `FAILED <nodeid>` lines are dropped and `stdout_excerpt` is discarded at :3907. The agent would have been asked to attribute a failure it was never shown. Split into E-02 (capture the names) and E-07 (ask, using them), with V-02 now failing a count-only field. PR-002 recorded the `needs-human` exit-code gap as a declined deferral rather than half-wiring an aggregator that has zero driver call sites (runner_shared.py:11267-11269). OQ-01 resolved FROM EVIDENCE (the `Diagnostics / Blocked Items:` block already exists at render_stream.py:2530-2533, is already conditional, and is where an operator looks), so no maintainer turn was spent on placement. OQ-02 was the maintainer's alone and they ruled 2026-09-20 that `not-mine` integrates in ANY run: attribution is the safeguard, and refusing unattended would preserve the measured 2026-09-19 loss exactly where it costs most. Five decisions recorded as D-1..D-5. Structural lint conforming at author AND review-finalize.
- 2026-09-20 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored as part 2 of defect 2 from the 2026-09-19 incident. Part 1 (vocabulary, validator, question) merged at `395fc06b` and is inert. Carries `Blocks-Release: next` because the defect it closes cost a full run.

## Goal

Let an agent answer a refused integration in the closed vocabulary already shipped, so one red test in a file a lane never touched stops costing the whole lane, while the gate itself stays hard and every answer stays attributable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Ask the question and read the answer

- [ ] E-01 At the seam in `execute_item` where `integration = integration_is_earned(...)` is computed (`runner_shared.py:13996`), detect the case worth asking about: `integration_gate_relevant` is true, `integration.earned` is false, and `integration.signal` is `INTEGRATION_REFUSED_SUITE_FAILED`. Ask ONLY for that signal.
  - Depends on: none
  - Expected outcome: A suite-failure refusal reaches the ask. `verifier-declined` and `no-trust-signal` do NOT: a verifier that explicitly declined is a stronger and more specific signal than a red suite, and "no trust signal at all" has nothing for an agent to attribute. Both keep refusing exactly as today.
  - Execution state: pending

- [ ] E-02 CAPTURE THE FAILING TEST NAMES, which are NOT available today. FOUND AT REVIEW and this item exists because the plan's original E-02 was unsatisfiable as written: it said to pass "the failing-test text from `suite_result.summary`", but `_SUITE_SUMMARY_RE` (`oc_runipd.py:3845-3847`) captures ONLY the count line. Measured by running that regex over real pytest output: it yields `'1 failed, 7080 passed, 3 skipped, 2 xfailed in 98.49s'` and the `FAILED tests/...::test_name` lines are absent. The full text exists as `stdout_excerpt` at `oc_runipd.py:3907` and is DISCARDED after the regex, and `attempt["suite_check"]` (`runner_shared.py:13987-13994`) persists only the summary. So add a field to `SuiteCheckResult` carrying the failing-test lines, populate it in `run_suite_check`, and persist it on `attempt["suite_check"]`.
  - Depends on: E-01
  - Expected outcome: A suite failure yields the actual `FAILED <nodeid>` lines, available both to the question in E-03 and to a human reading the run record. A count line alone is NOT sufficient: "1 failed" tells an agent nothing it can attribute, which is the whole judgement the answer turns on.
  - Execution state: pending

- [ ] E-07 Build the question with `gate_answer_question`, passing the failing-test lines from E-02 and this turn's changed files, then spend ONE follow-up turn in the SAME session and re-read the outcome file. MIRROR the shipped `perform_defect_reask` call site (`runner_shared.py:13884`) rather than inventing a second mechanism: bind each host's own resume primitive by name, re-collect the outcome file for an isolated lane, and count the turn against the session budget.
  - Depends on: E-02
  - Expected outcome: The agent is asked once per attempt, on both hosts, with the failing tests and its own changed files in front of it. The turn is charged to the session exactly as a defect re-ask is.
  - Execution state: pending

### Task group 2: Act on each answer

- [ ] E-03 Act on a usable answer. `not-mine` sets `integration.earned` true for this attempt so self-finalize and integration proceed. `mine` and `needs-human` leave the refusal standing and the lane preserved. An UNUSABLE answer (absent, unknown token, missing reason) leaves the refusal standing too.
  - Depends on: E-07
  - Expected outcome: Only `not-mine` releases. Silence and every malformed answer refuse, which is the fail-closed direction: a wrongly refused lane is preserved and recoverable, a wrongly integrated one merges work no trust signal cleared.
  - Execution state: pending

- [ ] E-04 Act on `fixed` by RE-RUNNING the full test suite and believing the re-run, never the claim. If it passes, integrate. If it fails, hand the NEW failure back and allow another attempt, bounded by the run's existing `--retry-budget` (default 2, resolved once by `resolve_retry_budget`). Do NOT add a second retry knob: the maintainer ruled 2026-09-19 that sharing the existing budget is correct for now.
  - Depends on: E-03
  - Expected outcome: A `fixed` claim is verified, not trusted. A repair that works integrates; one that does not gets another bounded attempt and then refuses with the lane preserved.
  - Execution state: pending

### Task group 3: Make the answer durable and visible

- [ ] E-05 Record the answer on the run record at the SAME per-item seam as `attempt["integration_signal"]`, mirroring `defect_report_record`'s shape: the answer, the agent's reason, whether it was re-asked, and what the re-ask produced. This is what makes the claim attributable and reviewable, which is the property the design rests on INSTEAD of mechanical verification.
  - Depends on: E-03
  - Expected outcome: A human reading the run record can see which answer was given, by which session, with what reason, and whether a re-run followed. A false `not-mine` is legible afterwards.
  - Execution state: pending

- [ ] E-06 Surface `needs-human` in the run summary as its own line, distinct from an ordinary refusal. It means the item is waiting on a DECISION rather than on work, and those route to different people. Do not bury it in a per-item table a reader scrolls past.
  - Depends on: E-05
  - Expected outcome: A run containing a `needs-human` answer says so where the operator looks, naming the item and the decision the agent asked for.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-20 on this base: `GATE_ANSWERS`, `validate_gate_answer` and `gate_answer_question` are present and unreferenced. This plan is the only consumer.
- The seam is `runner_shared.py:13996`; `integration.earned` gates self-finalize at `:14120` (isolated lane) and `:14325` (non-isolated). Both paths must honor a `not-mine` release or the fix works on one lane shape only.
- `perform_defect_reask` (`runner_shared.py`, called at `:13884`) is the shipped pattern for a bounded same-session follow-up: it never loops, is host-agnostic by injecting the resume primitive as a name, re-collects the outcome file from a lane, and bumps the session turn count in one place. Reuse it rather than forking a second re-ask.
- `resolve_retry_budget` already resolves the run's budget once, CLI over a default of 2, with a 0..10 bound owned by `run_recovery.validate_retry_budget`.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md.
- `- Readiness:` is deliberately absent: it is `/plan-review`'s output and IPD-M107 refuses an unattested value.

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The refusal is computed and recorded but never told to the agent, so a lane whose work is correct has no way to say the failure is not its own. | `grep integration_signal` across `runner_shared.py` returns record-and-report sites only; no prompt builder mentions it (measured 2026-09-19). |
| F-02 | High | One red test refuses EVERY concurrent lane, because each lane's trust signal is the same whole-repository suite. Blast radius is the run, not the item. | Run `run-20260919T194413Z-2056285`: three lanes refused on one unrelated failure; eight items cascaded. |
| F-03 | Medium | `not-mine` releases a lane on the agent's assertion, which is the FIRST place this system lets a claim substitute for a green suite. That is the deliberate design (mechanical verification was considered and rejected as unreliable and expensive), and it is the one item a reviewer should scrutinize hardest. | Maintainer ruling 2026-09-19; `GATE_ANSWER_NOT_MINE`'s docstring records the rejected alternative. |
| F-04 | Medium | Only the SUITE-FAILED signal should be askable. A `verifier-declined` refusal is a stronger, more specific judgement and must not be answerable away by the agent it judged. | `integration_is_earned`'s own comment: "a green suite deliberately does NOT override an explicit verifier verdict". |

## Proposed changes (ordered, validatable)

1. Detect the suite-failure refusal at the seam and ask only for it (E-01).
2. Ask via the shipped same-session follow-up pattern, showing failing tests and changed files (E-02).
3. Release on `not-mine`; refuse on `mine`, `needs-human`, and anything unusable (E-03).
4. Verify a `fixed` claim by re-running the suite, retrying within `--retry-budget` (E-04).
5. Record the answer durably beside the integration signal (E-05).
6. Surface `needs-human` in the run summary as a decision request (E-06).

## Deferred / out of scope (with reason)

- Mechanically verifying a `not-mine` claim (re-running the suite at the lane's base commit and attributing the test to changed files).
  - Carrier-Declined: CONSIDERED AND REJECTED BY THE MAINTAINER 2026-09-19, not deferred. Attributing a test to the files that can break it is not reliable (a test can fail from a change three modules away), and the three lanes in the incident had three DIFFERENT base commits, so there is no single base run to cache: verification would mean a full extra suite run per item to re-derive what the agent already knows. What makes the answer safe is that it is durable and attributed, exactly as a `- Readiness:` field is.
- A dedicated retry knob for a failed `fixed` claim.
  - Carrier-Declined: The maintainer ruled 2026-09-20 to SHARE the existing `--retry-budget` for now. A second knob would be a new dial for the same question, and the existing one already carries a validated bound.
- Changing `integration_is_earned`'s verdict logic so fewer refusals happen.
  - Carrier-Declined: EXPLICITLY OUT OF SCOPE by the same ruling: the gate stays hard 100% of the time, and the agent answers it. Softening the gate would trade a recoverable refusal for an unnoticed bad merge.
- Making the whole-repository suite stop being every lane's trust signal.
  - Carrier: 7pntcb
- Giving a `needs-human` answer its own run EXIT CODE. FOUND AT REVIEW: `needs-human` is semantically the same "a human is required" condition that `NEEDS_INPUT_TOKEN` represents, and `run_evidence.aggregate_run_exit` already maps that to spec `25kzda` 5.6's exit 3 and already outranks a plain item failure. So the mapping exists and is correct.
  - Carrier-Declined: DELIBERATELY NOT REACHED, because the blocker is not this plan's. `runner_shared.py:11267-11269` records that the aggregator has ZERO call sites in either driver, so reaching exit 3 at all means wiring both drivers to it, which changes EVERY run's exit classification. That is a far larger and riskier change than adding a refusal answer, it was already fenced out of an earlier Set (that comment's own `zz5yxq` OQ-02), and doing it here would smuggle a run-wide behavior change into a per-item feature. This plan therefore leaves the exit code exactly as a refusal produces today and says so, rather than half-wiring it. Recorded so a later reader does not mistake the omission for an oversight.

## Scope check

- Over-scope: none. Every E-item maps to one clause of the ruling.
- Under-scope: none for the wiring. Note the ADJACENT defect this does not fix: the run continued for 90 minutes after the first item failed to integrate, dispatching dependents that could not succeed. That is a queue-level stop condition rather than a gate answer, and it belongs to its own plan.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`, and paste the actual summary line. New tests in `tests/test_gate_answer_wiring.py` must cover: only `suite-failed` is asked about; `not-mine` releases on BOTH lane shapes (isolated and not); `mine`, `needs-human`, silence and a malformed answer all refuse; a `fixed` claim is re-verified and a passing re-run integrates while a failing one retries then refuses; the retry count never exceeds the resolved `--retry-budget`; and the recorded answer is present and attributable.

## Spec / documentation sync

No `.spec.md` edit, so none is declared in `- Scope-Paths:`. The behavior this adds is a refusal ANSWER, not a change to any state, transition, or exit code that a spec defines. If review finds that spec `25kzda`'s reporting section should name the new run-summary line, that amendment belongs to this plan and must be declared before it is made.

## Open questions

### OQ-01: Where exactly should a `needs-human` item appear in the run summary?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution: RESOLVED AT REVIEW 2026-09-20 FROM REPOSITORY EVIDENCE, so no maintainer turn is spent on it. An operator-facing section for exactly this purpose already exists: `render_stream.py:2530-2533` emits a `Diagnostics / Blocked Items:` block, conditionally (only when there is something to say, so an empty run gains no spurious line) and after the summary table where an operator already looks for why an item did not finish. A `needs-human` answer belongs there, as its own bullet naming the item and the decision the agent asked for.
  WHY THIS IS NOT MERELY A PREFERENCE: the maintainer's stated requirement was that the answer be where the operator actually looks rather than buried in a per-item table, and this is the one section that already satisfies that and is already conditional. Inventing a second location would fragment the place an operator checks. E-06 is therefore narrowed to "add a distinct bullet to the existing block", which is smaller and lower-risk than the open question implied.
  WHAT REMAINS THE MAINTAINER'S: nothing about placement. If they prefer a different location on sight, that is a one-line change to E-06 and not a redesign.
- Carrier-Declined: A PLACEMENT DECISION RESOLVED INSIDE THIS PLAN'S OWN EXECUTION, carrying no work beyond E-06. The requirement is fixed (it must be where the operator actually looks, not buried in a per-item table), and only the exact location is open. The maintainer asked to see this before it ships, which E-06 satisfies by proposing a placement for confirmation rather than deciding silently.
- Resolution or deferral rationale: NOT BLOCKING because E-06 is satisfiable at several placements and any of them beats today's behavior, which surfaces nothing. Recorded because the maintainer named it as one of three things to look at, and because a `needs-human` answer is worthless if the human never sees it: the answer exists precisely to route a decision, so its visibility IS its value.

### OQ-02: Should a `not-mine` release be permitted in a fully unattended run?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution: RESOLVED BY THE MAINTAINER 2026-09-20: YES, allow it in any run, attended or not. ATTRIBUTION IS THE SAFEGUARD, not supervision. A `not-mine` answer therefore integrates unconditionally, and E-03 needs no attended/unattended branch.
  THE REASONING, recorded because this is the one place in the system where an agent's assertion substitutes for a green test suite. The alternative was measured on 2026-09-19: three lanes whose work was correct were refused over one unrelated red test, nothing integrated, 2h 10m and $55.02 were spent, and a human had to hand-merge afterwards anyway. Refusing unattended would preserve exactly that loss for the runs where it costs most, since an unattended overnight run is precisely when nobody is there to release a correct lane.
  IT IS CONSISTENT WITH HOW THIS REPOSITORY ALREADY TREATS A FALSE CLAIM. A forged `- Readiness:` field and an unobserved `V-*` evidence block are both prevented by being durable, attributed and reviewable rather than by machine verification. A false `not-mine` is the same class of offense and gets the same treatment, which is why E-05 (record the answer, its reason and its session) is not optional bookkeeping but the safeguard itself.
  THE ACCEPTED COST, stated plainly rather than argued away: a false `not-mine` in an unattended run merges work whose trust signal nobody cleared, and the record is not read until morning. The maintainer accepted that in exchange for not re-incurring the measured loss.
- Carrier-Declined: A POLICY QUESTION THE CURRENT DESIGN ALREADY ANSWERS CONSERVATIVELY, with nothing outstanding. As specified, `not-mine` releases in any run, and the safeguard is attribution rather than supervision. Recorded because the maintainer flagged this exact item as the one to scrutinize, and because if the answer is "no", the remedy is a refusal plus a recorded request rather than new machinery, which E-03 could express without redesign.
- Resolution or deferral rationale: NOT BLOCKING because the wiring is identical either way; only the disposition of one branch changes. The case FOR allowing it: the alternative is tonight's outcome, where a correct lane is lost to an unrelated test and a human must hand-merge it anyway. The case AGAINST: an unattended run can integrate on an agent's unverified assertion, and nobody reads the record until morning.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste test output showing the ask fires for `suite-failed` and does NOT fire for `verifier-declined` or `no-trust-signal`. A run where a verifier's explicit decline could be answered away FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste a real suite failure's captured failing-test lines, showing at least one `FAILED <nodeid>` line PRESENT in the new field and in the persisted `attempt["suite_check"]`. Then paste the OLD behavior for contrast: `_SUITE_SUMMARY_RE` run over the same output, yielding only the count line. A field containing just "N failed" FAILS this item, because a count tells an agent nothing it can attribute.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste, for each of `not-mine`, `mine`, `needs-human`, a missing answer, an unknown token, and a reasonless `not-mine`, whether the lane integrated. Only `not-mine` may integrate. Show the `not-mine` release on BOTH the isolated-lane path (`:14120`) and the non-isolated path (`:14325`), since a fix on one is a fix on neither.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste three cases: a `fixed` claim whose re-run PASSES (integrates), one whose re-run FAILS then succeeds on a further attempt (integrates), and one that never passes (refuses, lane preserved). Paste the attempt count beside the resolved `--retry-budget` and show it was never exceeded.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the recorded answer from a real run record, showing the answer, the reason, the session id, and the re-ask outcome. Confirm a reader could identify WHO claimed `not-mine` and why.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the run summary for a run containing a `needs-human` answer, showing the item and the requested decision in the operator-facing output. Paste the same summary for a run with none, showing no spurious line.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Paste the rendered question from a real refusal, showing the failing test names (from E-02) and the turn's changed files both present. Paste evidence the follow-up ran in the SAME session on BOTH hosts and that the session turn count was bumped exactly once.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved h5pyqa --by-human`). It is the FIRST change in this sequence that alters what the runner does at runtime: parts already merged (`395fc06b`) are vocabulary and wording with no consumer. The maintainer named three things to see before it ships, and two are recorded above as OQ-01 (where `needs-human` surfaces) and OQ-02 (whether `not-mine` may release unattended); the third, sharing `--retry-budget`, was ruled on 2026-09-20 and is recorded in E-04 and Deferred.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
