# IPD: Bounded Step Packets Outcome Envelopes and Human Decision Gates

- Date: 2026-08-21
- Kind: child
- Concern: Release only bounded just-in-time work and never synthesize human consent.
- Scope: Bounded JIT step packets + structured outcome envelopes + human decision gates (headless needs_input, no synthesized consent). No retry/recovery (Order 07).
- Status: approved
- Approval: Gabriele Fariello (human), 2026-08-22
- Set: awoptimize
- Order: 6
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: ptsfjn

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-03 E-03/E-04/E-05 into 4 right-sized E-items (bounded JIT packet rendering, evidence-linked outcome envelopes, human decision gates, tests).
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. run_packet.py genuinely absent; envelope correctly rejects unsupported prose; gates enforce needs_input + no synthesized consent. PR-001 (LOW): the human-gate module was unnamed in E-03 and the scope fence; FIXED by naming it `agent_workflows/run_gates.py` in both. V-01..V-04 map 1:1 with falsifiable evidence. OQ-01 resolved.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.

## Goal

Release only bounded, just-in-time work; accept only structured, evidence-linked outcomes; and never
synthesize human consent. This Order renders the packets the Order-05 engine releases, defines the
outcome envelope that maps model responses onto durable state (ignoring unsupported prose), and
implements human decision gates that stop headless runs before any gated side effect.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: bounded packets

- [x] E-01 Implement bounded just-in-time step-packet rendering `agent_workflows/run_packet.py`: a packet carries immutable run metadata, the CURRENT requirements + scope, allowed tools/files, the exact action, the expected artifact, the evidence contract, stop conditions, dependencies, and a short exit checklist - and nothing else (a size/token budget bounds it), with a source-to-requirement trace.
  - Depends on: none
  - Expected outcome: golden packets contain every contract field, map all current requirements, omit unrelated bulk context, respect the size budget, and the packet digest changes when a bound requirement changes; the executor need not retain the monolithic workflow.
  - Execution state: performed

### Task group 2: outcome envelopes

- [x] E-02 Implement packet acknowledgements + outcome envelopes: a returned outcome must carry a structured `performed|blocked|failed` status, artifact references, and captured tool-event ids (Order 04); an unsupported claim (e.g. `all tests pass` with no evidence id) is ignored and cannot mutate durable state.
  - Depends on: E-01
  - Expected outcome: a structured envelope updates only legal states; free-form model prose may explain an outcome but cannot change durable state; missing evidence ids, a wrong attempt number, or a foreign actor are rejected.
  - Execution state: performed

### Task group 3: human gates

- [x] E-03 Implement human decision gates in `agent_workflows/run_gates.py`: explicit options, a declared default, a timeout policy, non-interactive refusal, and recorded authorization; consent is NEVER synthesized. A headless run reaching a gate stops with a stable `needs_input` result before any gated side effect.
  - Depends on: E-02
  - Expected outcome: interactive fixtures record each choice; a headless/non-interactive run stops at `needs_input` with no gated side effect performed; timeout follows the declared policy; no default consent is invented.
  - Execution state: performed

### Task group 4: tests

- [x] E-04 Add `tests/test_run_packet_gates.py` (stdlib unittest, model-free): golden packet field/requirement/budget/digest tests; outcome-envelope legality (structured accepted, unsupported prose / missing-evidence / wrong-attempt / foreign-actor rejected); interactive + headless gate fixtures (choice recorded, `needs_input` stop, no synthesized consent, timeout policy). Then run the full serial suite and paste the tail.
  - Depends on: E-03
  - Expected outcome: packet, envelope, and gate tests pass; the full serial suite is green (pasted).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The Order-05 engine chooses the next runnable step; this Order renders that step into a bounded packet, so the model never has to hold the whole workflow.
- Some workflows are interactive and headless hosts cannot supply mid-run answers, so an explicit `needs_input` stop state is required (established as a runtime need in old Order 03).
- Outcome envelopes reference Order-04 evidence ids; prose is explanatory only, never state-changing (the anti-false-completion posture).
- Machine output is ANSI-free with stable structure, matching the repo CLIs.

## Findings

| Finding | Consequence |
|---|---|
| A monolithic prompt degrades attention and loses obligations. | Render a bounded packet with only the current step's fields + a size budget + a source-to-requirement trace. |
| Free-form model prose can assert success it did not achieve. | The outcome envelope accepts only structured status + evidence-id references; unsupported prose is ignored. |
| Headless sessions may hit a decision point after launch. | An explicit `needs_input` stop + declared default/timeout, never synthesized consent. |

## Proposed changes (ordered, validatable)

1. Render bounded, traceable, budgeted step packets (E-01).
2. Accept only structured, evidence-linked outcome envelopes (E-02).
3. Implement human decision gates with `needs_input` + no synthesized consent (E-03).
4. Model-free packet/envelope/gate tests + full suite (E-04).

## Deferred / out of scope (with reason)

- The state machine + scheduling that DECIDES which step to release: Order 05 (this Order renders the released step).
- Retry/correction, resume/cancel/crash recovery, the `aw run` CLI, and full state-space simulations: Order 07.
- Evidence CAPTURE + completion predicate: Order 04 (the envelope references its evidence ids).
- Verifier isolation: Orders 08/09.

## Scope check

- Over-scope: no scheduling/state-machine logic, no recovery/CLI, no evidence capture, no provider calls.
- Under-scope: none - packet rendering, outcome envelopes, and human gates are covered; Order 07 builds recovery + CLI on top.

## Required tests / validation

- `tests/test_run_packet_gates.py`: golden packet tests (fields, requirement mapping, budget, digest-changes-on-requirement-change); outcome-envelope legality (structured accepted; unsupported prose / missing-evidence-id / wrong-attempt / foreign-actor rejected); interactive + headless gate fixtures (`needs_input` stop, recorded choice, timeout policy, no synthesized consent).
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean.

## Spec / documentation sync

- Publish the packet contract (fields + size budget), the outcome-envelope schema, and the human-gate behavior (options/default/timeout/`needs_input`). No user-facing README change at this layer.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The packet contract, envelope schema, and gate behavior are enumerated from old Order 03's E-03/E-04/E-05; no open decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted golden-packet test output showing every contract field present, all current requirements mapped, unrelated bulk omitted, the size budget respected, and the packet digest changing when a bound requirement changes.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted test output showing a structured performed/blocked/failed envelope updates only legal states, and unsupported prose / a missing evidence id / a wrong attempt / a foreign actor are ignored or rejected.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted interactive + headless gate fixtures showing each choice recorded, a headless run stopping at `needs_input` before any gated side effect, timeout following the declared policy, and no synthesized default consent.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `tests/test_run_packet_gates.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 05 (the engine that releases the step this Order renders), and Orders 01-04 upstream. Scope fence: touch only `agent_workflows/run_packet.py`, `agent_workflows/run_gates.py`, and `tests/test_run_packet_gates.py`; do NOT implement scheduling/state transitions (Order 05), recovery/CLI (Order 07), or evidence capture (Order 04) - if it seems to need more, STOP and report. Never synthesize human consent; a headless gated run must stop at `needs_input`. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
