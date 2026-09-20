# IPD: Act on the integration-refusal answer at the turn seam so a lane is not lost to an unrelated red test

- Date: 2026-09-20
- Kind: child
- Concern: A lane's trust signal is a FULL TEST SUITE run, and a single red test refuses that lane's integration with NO way for the agent to say anything about it. Measured in run `run-20260919T194413Z-2056285`: one test unrelated to any lane's work went red, THREE lanes were refused, nothing merged, eight further items cascaded to `dependency-blocked`, and the run spent 2h 10m and $55.02 producing no integrated work. Every one of those lanes had done its job. The vocabulary to answer that refusal now EXISTS and is inert: `GATE_ANSWERS` (`not-mine`/`fixed`/`mine`/`needs-human`), `validate_gate_answer` and `gate_answer_question` are on main at `395fc06b`, and nothing reads them. This plan wires them in.
- Scope: IN: at the seam where `integration_is_earned` refuses for a suite failure, ask the agent the question, validate the answer, and act on it: `not-mine` integrates, `fixed` re-runs the full test suite and the RE-RUN decides, `mine` and `needs-human` refuse and preserve. Record the answer durably on the run record and surface `needs-human` in the run report. A failed `fixed` retries within the run's existing `--retry-budget`. OUT: any change to `integration_is_earned`'s own verdict logic (the gate stays hard 100% of the time), any new retry knob, any mechanical verification of a `not-mine` claim, and the review path (a review turn has no suite result to refuse on).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_gate_answer_wiring.py
- Item-Dependencies: none
- Status: to-review
- Set: gatewire
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: h5pyqa
- Blocks-Release: next
- Work-Kind: bug

## Workflow history

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

- [ ] E-02 Build the question with `gate_answer_question`, passing the failing-test text from `suite_result.summary` and this turn's changed files, then spend ONE follow-up turn in the SAME session and re-read the outcome file. MIRROR the shipped `perform_defect_reask` call site (`runner_shared.py:13884`) rather than inventing a second mechanism: bind each host's own resume primitive by name, re-collect the outcome file for an isolated lane, and count the turn against the session budget.
  - Depends on: E-01
  - Expected outcome: The agent is asked once per attempt, on both hosts, with the failing tests and its own changed files in front of it. The turn is charged to the session exactly as a defect re-ask is.
  - Execution state: pending

### Task group 2: Act on each answer

- [ ] E-03 Act on a usable answer. `not-mine` sets `integration.earned` true for this attempt so self-finalize and integration proceed. `mine` and `needs-human` leave the refusal standing and the lane preserved. An UNUSABLE answer (absent, unknown token, missing reason) leaves the refusal standing too.
  - Depends on: E-02
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
- Status: open
- Owner: maintainer
- Carrier-Declined: A PLACEMENT DECISION RESOLVED INSIDE THIS PLAN'S OWN EXECUTION, carrying no work beyond E-06. The requirement is fixed (it must be where the operator actually looks, not buried in a per-item table), and only the exact location is open. The maintainer asked to see this before it ships, which E-06 satisfies by proposing a placement for confirmation rather than deciding silently.
- Resolution or deferral rationale: NOT BLOCKING because E-06 is satisfiable at several placements and any of them beats today's behavior, which surfaces nothing. Recorded because the maintainer named it as one of three things to look at, and because a `needs-human` answer is worthless if the human never sees it: the answer exists precisely to route a decision, so its visibility IS its value.

### OQ-02: Should a `not-mine` release be permitted in a fully unattended run?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: A POLICY QUESTION THE CURRENT DESIGN ALREADY ANSWERS CONSERVATIVELY, with nothing outstanding. As specified, `not-mine` releases in any run, and the safeguard is attribution rather than supervision. Recorded because the maintainer flagged this exact item as the one to scrutinize, and because if the answer is "no", the remedy is a refusal plus a recorded request rather than new machinery, which E-03 could express without redesign.
- Resolution or deferral rationale: NOT BLOCKING because the wiring is identical either way; only the disposition of one branch changes. The case FOR allowing it: the alternative is tonight's outcome, where a correct lane is lost to an unrelated test and a human must hand-merge it anyway. The case AGAINST: an unattended run can integrate on an agent's unverified assertion, and nobody reads the record until morning.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste test output showing the ask fires for `suite-failed` and does NOT fire for `verifier-declined` or `no-trust-signal`. A run where a verifier's explicit decline could be answered away FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the rendered question from a real refusal, showing the failing test names and the turn's changed files both present. Paste evidence the follow-up ran in the SAME session on BOTH hosts and that the session turn count was bumped once.
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

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved h5pyqa --by-human`). It is the FIRST change in this sequence that alters what the runner does at runtime: parts already merged (`395fc06b`) are vocabulary and wording with no consumer. The maintainer named three things to see before it ships, and two are recorded above as OQ-01 (where `needs-human` surfaces) and OQ-02 (whether `not-mine` may release unattended); the third, sharing `--retry-budget`, was ruled on 2026-09-20 and is recorded in E-04 and Deferred.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
