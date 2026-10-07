# IPD: Send one shared fix-it message that names what failed and says to fix the cause, not the gate

- Date: 2026-10-07
- Kind: child
- Concern: Fix-it turns today are built by several separate notices (`runner_shared.build_correction_notice`, `build_stale_receipt_notice`, `build_verification_refusal_notice`, the merge-conflict send-back), none of which tells the agent the rule the maintainer set on 2026-10-07: fix the thing that made the gate refuse, do not alter the gate; a small, clearly-a-bug fix to a gate or tool is acceptable with a stated reason; anything material belongs in a separately scoped artifact, so propose it. The execute prompt says only "Do not weaken checks", and nothing tells the agent what to do instead. Without this, widening what is retried (Orders 04 to 07) would invite an agent to "fix" a refusal by weakening the gate.
- Scope: Add one message builder, `build_fix_it_notice`, that every fix-it turn uses: what failed (kind, verbatim evidence, attempt n of N), what to do (fix the cause), the gate-and-tool rule, and how to propose (Order 02's `proposal` field). Route the existing notices through it so their specific evidence is kept and the rule text is stated once. Add the same rule, once, to the execute prompt. EXCLUDES new retry classes (Orders 04 to 07) and the proposal mechanism itself (Order 02).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_fix_it_notice.py
- Item-Dependencies: executed:tha7a6
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: mcbph5

## Workflow history
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every fix-it turn reads the same way: here is what failed, fix the cause; a small, clearly-a-bug fix to a gate or tool is fine if you say why; anything bigger, propose it and stop.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the builder

- [ ] E-01 In `agent_workflows/runner_shared.py`, add `build_fix_it_notice(kind, evidence, attempt, budget, *, recovery)` returning the full notice. It MUST contain, in order: (1) one line naming the failure kind and "attempt n of N"; (2) the evidence verbatim (hook output, exit code and missing file, failing tests, refused finding lines), bounded with a visible elision marker and a pointer to where the full text is; (3) the instruction: "Fix what caused this. Do not change the gate, check, hook or test that refused to make it pass."; (4) the judgement rule, in the maintainer's terms: "Changing a gate or an `aw` tool is normally the job of a plan scoped to change it. If you find a real, small bug in one that is clearly not working as intended, you may fix it, and you must say why in your outcome file and scope reason. For anything material, do not change it: record a `proposal` in your outcome file (what blocked you, why it cannot be fixed in scope, what should change) and stop."; (5) the outcome-file reminder.
  - Depends on: none
  - Expected outcome: the function returns text containing all five parts for each kind passed; evidence longer than the bound is elided with a marker.
  - Execution state: pending

- [ ] E-02 Route `build_correction_notice`, `build_stale_receipt_notice` and `build_verification_refusal_notice` through `build_fix_it_notice`, keeping each one's specific evidence and instructions (for example the stale-receipt "UNDO it ... or KEEP it ... and JUSTIFY it") as that kind's evidence and keeping their call sites unchanged.
  - Depends on: E-01
  - Expected outcome: each existing notice still contains its specific instruction text and now also contains parts (3) and (4) exactly once.
  - Execution state: pending

- [ ] E-03 Add the part (3)/(4) rule once to the execute prompt next to "Do not weaken checks, fabricate evidence, broaden approved scope", reusing the same constant as the builder so the two cannot drift.
  - Depends on: E-01
  - Expected outcome: a rendered execute prompt contains the rule exactly once.
  - Execution state: pending

### Task group 2: tests

- [ ] E-04 Add `tests/test_fix_it_notice.py` that calls the builder for every kind Orders 04 to 07 will send (nonzero exit, stall, spawn failure, hook refusal, red suite, out-of-scope, untooled status change, hook bypass) and the three existing notices, and asserts on the returned text: the kind line, the verbatim evidence, the fix-the-cause instruction, the gate-and-tool rule, the proposal instruction, and elision of over-long evidence. Also render a real execute prompt and assert the rule appears once.
  - Depends on: E-02, E-03
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
| F-03 | Maintainer ruling 2026-10-07: no absolute prohibition; the agent decides, needs a good reason, and material changes go to a separately scoped artifact. | Session 2026-10-07. |

## Proposed changes (ordered, validatable)

1. One builder (E-01).
2. Existing notices routed through it (E-02).
3. The rule once in the execute prompt (E-03).
4. Tests (E-04).

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none. `runner_shared.py` by E-01 to E-03; the test module by E-04.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_fix_it_notice.py tests/test_production_correction_turn.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

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
  - Required evidence: paste one full rendered notice for a hook refusal and one with elided evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rendered stale-receipt notice showing its own instruction and the shared rule once.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the execute-prompt excerpt with the rule and a count showing it appears once.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the passing run of both named modules with per-test counts and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.
