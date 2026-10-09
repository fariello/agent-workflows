# IPD: Send one shared fix-it message that names what failed and says to fix the cause, not the gate

- Date: 2026-10-07
- Kind: child
- Concern: Fix-it turns today are built by several separate notices (`runner_shared.build_correction_notice`, `build_stale_receipt_notice`, `build_verification_refusal_notice`, the merge-conflict send-back), none of which tells the agent the rule the maintainer set on 2026-10-07: fix the thing that made the gate refuse, do not alter the gate; a small, clearly-a-bug fix to a gate or tool is acceptable with a stated reason; anything material belongs in a separately scoped artifact, so propose it. The execute prompt says only "Do not weaken checks", and nothing tells the agent what to do instead. Without this, widening what is retried (Orders 04 to 07) would invite an agent to "fix" a refusal by weakening the gate.
- Scope: Add one message builder, `build_fix_it_notice`, that every fix-it turn uses: what failed (kind, verbatim evidence, attempt n of N), what to do (fix the cause), the gate-and-tool rule, and how to propose (Order 02's `proposal` field). Route the existing notices through it so their specific evidence is kept and the rule text is stated once. Add the same rule, once, to the execute prompt. EXCLUDES new retry classes (Orders 04 to 07) and the proposal mechanism itself (Order 02).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_fix_it_notice.py
- Item-Dependencies: executed:tha7a6
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: mcbph5
- Approval: 2026-10-09, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-09 approved (aw set): status set to approved
- 2026-10-08 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED
- 2026-10-08 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. The three notices are concatenated into one prompt, so the rule is now deduplicated per prompt (`include_rule=False` plus one append at the `build_prompt` assembly site); E-03 handles body-vs-notice duplication and aligns `DEFAULT_RUNBOOK_TEXT`; new E-05/V-05 routes the production, review-orchestrator and merge-conflict (`merge_conflict_question`) correction texts, since the merge send-back is not a notice function; redaction, bound constant, `recovery=False` contract and test-pinned phrases made explicit; tests widened; gate contract added. Review record `.aw/records/reviews/20261007-fixfirst-03-mcbph5-send-one-shared-fix-it-message-that-names-what-failed-and-sa.review.md`.
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every fix-it turn reads the same way: here is what failed, fix the cause; a small, clearly-a-bug fix to a gate or tool is fine if you say why; anything bigger, propose it and stop.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the builder

- [ ] E-01 In `agent_workflows/runner_shared.py`, add `build_fix_it_notice(kind, evidence, attempt, budget, *, recovery, include_rule=True)` returning the full notice (`""` when `recovery` is False, matching the existing notices' contract that a first-attempt prompt is byte-identical). Define the part (3)/(4) text as ONE module constant (e.g. `FIX_IT_RULE_TEXT`) that E-03 also uses. Pass all agent-visible evidence through the same redaction the existing notices use (`render_stream._redact_absolute_paths`, as `build_verification_refusal_notice` does) so no absolute driver-side path reaches the prompt. It MUST contain, in order: (1) one line naming the failure kind and "attempt n of N"; (2) the evidence verbatim (hook output, exit code and missing file, failing tests, refused finding lines), bounded with a visible elision marker and a pointer to where the full text is; (3) the instruction: "Fix what caused this. Do not change the gate, check, hook or test that refused to make it pass."; (4) the judgement rule, in the maintainer's terms: "Changing a gate or an `aw` tool is normally the job of a plan scoped to change it. If you find a real, small bug in one that is clearly not working as intended, you may fix it, and you must say why in your outcome file and scope reason. For anything material, do not change it: record a `proposal` in your outcome file (what blocked you, why it cannot be fixed in scope, what should change) and stop."; (5) the outcome-file reminder.
  - Depends on: none
  STATE THE BOUND as a named constant (for example 4000 characters), and make the pointer name where the full text lives in terms the agent can read in its lane (e.g. the `Prior attempt:` field or the outcome path), never an absolute run-directory path.
  - Expected outcome: the function returns text containing all five parts for each kind passed; evidence longer than the bound is elided with a marker; `include_rule=False` omits parts (3) and (4) only; `recovery=False` returns `""`; an absolute path in the evidence is redacted.
  - Execution state: pending

- [ ] E-02 Route `build_correction_notice`, `build_stale_receipt_notice` and `build_verification_refusal_notice` through `build_fix_it_notice`, keeping each one's specific evidence and instructions (for example the stale-receipt "UNDO it ... or KEEP it ... and JUSTIFY it") as that kind's evidence and keeping their signatures and their `""`-when-not-relevant behavior unchanged.
  THE THREE ARE CONCATENATED INTO ONE PROMPT (`build_prompt`: `correction_notice = build_correction_notice(...) + build_stale_receipt_notice(...) + build_verification_refusal_notice(...)`), and more than one can be non-empty on the same recovery turn. So "exactly once" is per PROMPT, not per notice: change that one assembly site so the rule is appended once after the concatenation when any of the three is non-empty, and have the three call the builder with `include_rule=False`. That assembly site is the only call-site change.
  PRESERVE THE PHRASES EXISTING TESTS MATCH, and do not edit those tests: `tests/test_finalize_sendback.py` asserts "Change after begin:"; `tests/test_verification_sendback.py` asserts the heading "## Verification failed on the prior attempt (verifier-no-test-evidence)" and its absence on a first prompt. Re-derive the list at execution by grepping `tests/` for each notice's distinctive headings and phrases before editing.
  - Depends on: E-01
  - Expected outcome: each existing notice still contains its specific instruction text; a recovery prompt in which two or three notices are non-empty contains parts (3) and (4) exactly once; a first-attempt prompt is unchanged apart from E-03's single rule; `tests/test_finalize_sendback.py` and `tests/test_verification_sendback.py` pass unmodified.
  - Execution state: pending

- [ ] E-03 Add the part (3)/(4) rule once to the execute prompt (`build_prompt`) next to "Do not weaken checks, fabricate evidence, broaden approved scope", reusing `FIX_IT_RULE_TEXT` so the two cannot drift. On a recovery turn that carries a fix-it notice, the prompt must still contain the rule exactly once: either the body copy or the notice copy is omitted, and which one is stated in the code. Also align `DEFAULT_RUNBOOK_TEXT` directive 3 ("Do not weaken checks or fabricate evidence.") with a one-line pointer to the same rule, so the attached runbook does not read as an absolute prohibition the prompt then relaxes.
  - Depends on: E-01, E-02
  - Expected outcome: a rendered first-attempt execute prompt contains the rule exactly once; a rendered recovery prompt with two non-empty notices contains it exactly once; the runbook text no longer contradicts it.
  - Execution state: pending

- [ ] E-05 Route `build_production_set_correction_prompt` and `build_review_orchestrator_correction_prompt` (the production and review correction turns) and the merge-conflict send-back text built by `merge_conflict_question` through the same rule: each appends `FIX_IT_RULE_TEXT` exactly once, keeping its own heading, findings and instructions byte-identical otherwise. These are the other fix-it texts the runner already sends; leaving them out would make the rule "once" for some fix-it turns and absent for others.
  - Depends on: E-01
  - Expected outcome: each of the three rendered texts contains the rule exactly once and still contains its existing distinctive phrases (`tests/test_production_correction_turn.py` "never delete the checklist", "child-unauthored", "resolves to no plan on disk" pass unmodified).
  - Execution state: pending

### Task group 2: tests

- [ ] E-04 Add `tests/test_fix_it_notice.py` that calls the builder for every kind Orders 04 to 07 will send (nonzero exit, stall, spawn failure, hook refusal, red suite, out-of-scope, untooled status change, hook bypass) and the three existing notices, and asserts on the returned text: the kind line, the verbatim evidence, the fix-the-cause instruction, the gate-and-tool rule, the proposal instruction, elision of over-long evidence, redaction of an absolute path, and `""` for a non-recovery call. Also render real execute prompts through `build_prompt`: a first attempt, and a recovery attempt whose last attempt carries both a `turn_correction` packet and a stale-receipt `finalize_refused`; assert the rule appears exactly once in each. Render the E-05 texts and assert the rule appears once in each.
  - Depends on: E-02, E-03, E-05
  - Expected outcome: the module passes; no source introspection.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- What reaches the agent from the prior attempt is allowlisted (`lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`); evidence text added here must go through the same redaction the existing notices use.
- Tests assert on returned text and rendered prompts, never on source (GUIDING_PRINCIPLES P16).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Four separate fix-it texts exist and none states the gate-and-tool rule. | `runner_shared.build_correction_notice` ("Address ONLY the failed predicates"), `build_stale_receipt_notice`, `build_verification_refusal_notice` ("you must FIX the cause rather than re-implementing"), and the merge-conflict send-back. |
| F-02 | The execute prompt forbids weakening checks but offers no alternative. | Execute prompt text "Do not weaken checks, fabricate evidence, broaden approved scope, bypass lifecycle controls, discard unrelated work, or push." |
| F-04 | (review) The three notices are concatenated into ONE prompt and can co-occur, so "rule once per notice" puts it in the prompt up to three times. | `build_prompt`: `correction_notice = (build_correction_notice(item, recovery) + build_stale_receipt_notice(item, recovery) + build_verification_refusal_notice(item, recovery))`. |
| F-05 | (review) The merge-conflict send-back is not a notice function, and two more correction prompts exist. | `merge_conflict_question` (prompt for the `merge_conflict_sendback` loop); `build_production_set_correction_prompt`; `build_review_orchestrator_correction_prompt`; `DEFAULT_RUNBOOK_TEXT` directive 3 "Do not weaken checks or fabricate evidence." |
| F-03 | Maintainer ruling 2026-10-07: no absolute prohibition; the agent decides, needs a good reason, and material changes go to a separately scoped artifact. | Session 2026-10-07. |

## Proposed changes (ordered, validatable)

1. One builder (E-01).
2. Existing notices routed through it (E-02).
3. The rule once in the execute prompt and aligned in the runbook (E-03).
4. The rule in the production, review-orchestrator and merge-conflict correction texts (E-05).
5. Tests (E-04).

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none. `runner_shared.py` by E-01 to E-03 and E-05; the test module by E-04.
- Under-scope: none known after review (F-04, F-05 folded in).
- Scope fence: `- Scope-Paths:` is a declaration. If execution genuinely needs another file, edit it and justify it at finalize (`--scope-reason`); acknowledge a declared but unmodified path with `--scope-ack`.

## Required tests / validation

- `python3 -m pytest tests/test_fix_it_notice.py tests/test_production_correction_turn.py tests/test_finalize_sendback.py tests/test_verification_sendback.py tests/test_prior_attempt_projection.py -o addopts=""`, the last four unmodified.
- Bare `python3 -m pytest`, with failing node IDs recorded in the lane before any edit and compared after (review measured `6625 passed, 2 skipped` at HEAD `383ebc1ee`; re-derive).

## Spec / documentation sync

N/A: spec `25kzda` 5.5 states the rule (Order 01); this plan implements its text.

## Open questions

### OQ-01: Should the rule name specific protected paths?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No. The maintainer chose judgement over an absolute list (F-03). Kept scope edits are still recorded as `- Scope-Exceeded:` (Order 06), which is how they are tracked and analysed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste one full rendered notice for a hook refusal, one with elided evidence (showing the marker and the pointer), one whose evidence contained an absolute path (showing it redacted), and the `recovery=False` result.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a rendered recovery prompt (via `build_prompt`) carrying both the correction and the stale-receipt notice, with a count of `FIX_IT_RULE_TEXT` occurrences equal to 1, and paste each notice's own instruction text present.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the first-attempt execute-prompt excerpt with the rule and a count of 1, the recovery-prompt count of 1, and the amended `DEFAULT_RUNBOOK_TEXT` directive 3.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the passing run of the five named modules with per-test counts, `git diff --stat tests/` showing only `tests/test_fix_it_notice.py` changed, and the bare-suite summary line with before and after failing node IDs.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the tail of each of the three rendered texts (production Set correction, review-orchestrator correction, merge-conflict question) showing the rule once, and the passing `tests/test_production_correction_turn.py` run.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Execute only after `tha7a6` has executed (`- Item-Dependencies:`), because part (4) names Order 02's `proposal` field.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
