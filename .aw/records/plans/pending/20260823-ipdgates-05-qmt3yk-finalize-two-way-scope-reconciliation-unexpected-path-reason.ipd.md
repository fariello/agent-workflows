# IPD: Finalize two-way scope reconciliation (unexpected-path reason, in-scope-unmodified acknowledgment)

- Date: 2026-08-23
- Kind: child
- Concern: `aw ipd finalize` (Order 04) computes the scope delta - files this execution changed vs the frozen `Scope-Paths` - but only REFUSES on an out-of-scope path. In real complex work, discovering mid-stream that you must touch an unforeseen file is common (often the rule), and agents are NOT trained to update `Scope-Paths` en route or even to run `aw ipd finalize` at all. A hard refusal on every unforeseen edit trains agents to treat the gate as noise (which then misses the real p7dqwz violation), and a refusal alone catches only EXTRA work, never MISSING work (a file declared in scope but silently never touched - the "went off the rails / didn't do what it said" failure). This IPD turns finalize's one-directional refusal into a low-friction, unskippable TWO-WAY reconciliation that SURFACES and ATTRIBUTES both deltas without relying on the agent to remember anything mid-stream. (DECISIONS.md D141.)
- Scope: Add the two-way scope reconciliation to `aw ipd finalize` (the finalize path from Order 04) plus an OPTIONAL convenience en-route `aw ipd scope add`. Touch: the single-IPD lifecycle module (from Orders 03/04), agent_workflows/cli.py (the finalize prompt/flags + the optional `ipd scope add` verb + help), and tests/test_ipd_lifecycle_cli.py. Does NOT change how `aw ipd begin` freezes `Scope-Paths` (unchanged by human decision), does NOT alter the Order 04 refusal-vs-proceed decision beyond replacing bare refusal with reconciliation, and does NOT build rollback (Order 06) or remove the bypass (Order 07).
- Status: to-review
- Set: ipdgates
- Order: 5
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: qmt3yk

## Workflow history
- 2026-08-24 to-review (aw set): authored as new Order 05 (D141 finalize scope reconciliation); ready for review

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created - decomposed out of Order 04 at human direction (density: reconciliation is a distinct deliverable + test surface) and inserted as Order 05 (rollback -> 06, remove-bypass -> 07). Design per DECISIONS.md D141.

## Goal

Make `aw ipd finalize` reconcile the scope delta in BOTH directions at the one step that cannot be skipped (finalize is the chokepoint; Order 07 makes even `aw set executed` delegate into it). For files this execution CHANGED that are OUTSIDE the frozen `Scope-Paths`: require a short RECORDED REASON per file. For files declared IN `Scope-Paths` that were NOT modified: require a one-word ACKNOWLEDGMENT (e.g. "not-needed"). Both are collected in ONE batched, low-friction prompt and written verbatim into the terminal `## Workflow history`/evidence so the deviation is permanently visible and attributable. The mechanism SURFACES and ATTRIBUTES deviations (defeating hiding, enabling later human/verifier review); it does NOT judge their legitimacy. An OPTIONAL `aw ipd scope add <plan> <path> --reason` lets an agent/human pre-record an unforeseen need en route, pre-filling the finalize answer - a convenience, never required (agents will not reliably use it; finalize is the guarantee).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Two-way reconciliation at finalize

- [ ] E-01 In the single-IPD lifecycle module, extend `aw ipd finalize` so that, after computing the scope delta (reuse Order 04's exact computation - do not recompute differently), it presents ONE batched reconciliation prompt covering BOTH directions: (a) each path this execution changed that is OUTSIDE `Scope-Paths` requires a non-empty REASON (this replaces Order 04's bare unexplained-path refusal for the LEGITIMATE case: reason given -> record + proceed; reason refused/empty -> do not finalize); (b) each path declared IN `Scope-Paths` but NOT modified requires a one-word ACKNOWLEDGMENT (default-acceptable answers like "not-needed" are valid and recorded - this direction is acknowledge-and-proceed, NOT a hard blocker). Write every answer verbatim into the terminal history/evidence. On a clean delta (nothing out-of-scope, nothing declared-but-unmodified) the prompt is a no-op and finalize proceeds silently. Non-interactive/headless runs with a non-empty delta and no supplied answers fail closed (cannot silently skip the reconciliation).
  - Depends on: none
  - Expected outcome: finalize confronts the agent/human with the full two-way delta at the unskippable step; out-of-scope edits are recorded-with-reason, in-scope-unmodified are acknowledged, and both land in the durable record; a clean delta is frictionless.
  - Execution state: pending

### Task group 2: Optional en-route scope pre-record

- [ ] E-02 Add an OPTIONAL convenience verb `aw ipd scope add <plan> <path> --reason <why>` (registered in `cli.py` with help) that records an unforeseen in-scope-widening (path + reason + timestamp) to the plan's live run state so that finalize's E-01 reconciliation finds the answer already supplied and does not re-prompt for that path. It is NEVER required (finalize's E-01 is the guarantee); it exists only to let a careful agent/human capture the "why" AT THE MOMENT of realization, which is more honest than reconstructing it at finalize. It does NOT edit the frozen begin receipt (the receipt's `Scope-Paths` stays as declared; the widening is an additive, timestamped en-route record).
  - Depends on: E-01
  - Expected outcome: an agent/human MAY pre-record an unforeseen edit with its reason en route; finalize consumes that record instead of re-prompting; forgetting to use it costs nothing (finalize still asks).
  - Execution state: pending

### Task group 3: Prove reconciliation + attribution + low friction

- [ ] E-03 Add `tests/test_ipd_lifecycle_cli.py` reconciliation tests: (out-of-scope) an execution that changed a path outside `Scope-Paths` prompts for a reason, records the given reason in the terminal history, and proceeds; refusing/empty reason does NOT finalize. (in-scope-unmodified) a declared-but-untouched path prompts for a one-word acknowledgment, records it, and proceeds. (both-at-once) a single batched prompt covers both directions. (clean) a fully in-scope, fully-covered execution shows no prompt and finalizes silently. (headless) a non-empty delta with no answers fails closed. (en-route) a prior `aw ipd scope add` pre-fills the reason so finalize does not re-prompt that path. (attribution) the recorded reasons/acknowledgments are present verbatim in the terminal `## Workflow history`/evidence. Confirm `pytest -n auto` is green.
  - Depends on: E-01, E-02
  - Expected outcome: both delta directions, the batched single-prompt UX, the clean no-op, the headless fail-closed, the en-route pre-fill, and the durable attribution are all proven.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Order 04 (`v7e88a`) already computes the scope delta (diff base-HEAD..now restricted to `Scope-Paths`, per the path-overlap rule shared with Order 03) and currently REFUSES on an out-of-scope path; this IPD reuses that exact computation and replaces bare refusal with reconciliation for the legitimate case.
- `aw ipd begin` freezes `Scope-Paths` at start and is UNCHANGED by human decision; unforeseen mid-stream edits are handled by reconciliation at finalize, not by re-freezing.
- Finalize is the unskippable chokepoint: Order 07 makes `aw set executed` DELEGATE into finalize, so the reconciliation cannot be bypassed even by the "just mark it done" path.
- Agents are not trained to update scope en route or even to run finalize; the design therefore makes finalize (not the en-route verb) the load-bearing, mandatory, auto-computed mechanism.

## Findings

The reconciliation's power is SURFACING + ATTRIBUTION, not judgment: a low-barrier "give a reason" field is trivially greenwashed ("n/a"), so the reason text alone does not prove legitimacy - but it makes the deviation impossible to HIDE, cheap to legitimately explain, and permanently ON THE RECORD for a human/verifier to weigh. Making finalize (not an en-route verb the agent will forget) the mandatory chokepoint is what guarantees the confrontation happens. The in-scope-unmodified direction is the only mechanism in the Set that catches MISSING work ("said it would touch X, didn't"); it is acknowledge-and-proceed because a declared-but-unneeded file is normal, not a failure. Out-of-scope edits carry slightly more weight (recorded reason) because they are the p7dqwz signature.

## Proposed changes (ordered, validatable)

1. Two-way batched reconciliation in finalize: out-of-scope -> recorded reason (proceed) / empty -> refuse; in-scope-unmodified -> one-word acknowledgment (proceed); clean delta -> silent; headless with delta + no answers -> fail closed (E-01).
2. Optional `aw ipd scope add <plan> <path> --reason` en-route pre-record that finalize consumes (E-02).
3. Tests for both directions, batched UX, clean no-op, headless fail-closed, en-route pre-fill, durable attribution (E-03).

## Deferred / out of scope (with reason)

- Changing how `aw ipd begin` freezes `Scope-Paths`: explicitly OUT (human decision - the frozen baseline stays; reconciliation absorbs mid-stream discovery).
- JUDGING whether a recorded reason is adequate: out of scope - that is human/verifier review reading the recorded reasons, not a linter.
- Rollback semantics (Order 06) and removing the raw bypass (Order 07): sibling orders.
- The `Scope-Paths` granularity/ergonomics debate (directory vs exact-file, narrowness expectations): a design tension recorded for Orders 02/03 (D141), not implemented here.

## Scope check

- Over-scope: none. Only the finalize reconciliation prompt + the optional en-route verb + their tests.
- Under-scope: none for reconciliation; adequacy-judgment is deliberately human/verifier review, not this gate.

## Required tests / validation

- `tests/test_ipd_lifecycle_cli.py` reconciliation tests per E-03 (out-of-scope reason, in-scope-unmodified ack, batched single prompt, clean no-op, headless fail-closed, en-route pre-fill, durable attribution).
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Amend the IPD lifecycle spec + `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md` + CLI `--help` (via managed verbs) to document the finalize two-way reconciliation, the optional `aw ipd scope add`, and the honest framing (surfaces + attributes, does not judge). Cite DECISIONS.md D141.

## Open questions

### OQ-01: none blocking

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: the design is human-resolved in DECISIONS.md D141 (two-way reconciliation; out-of-scope = recorded reason, in-scope-unmodified = one-word acknowledgment; finalize is the mandatory chokepoint; optional en-route `scope add`; surfaces + attributes, does not judge; begin's frozen `Scope-Paths` unchanged). No blocking open question remains.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: tests show an out-of-scope changed path prompts for and RECORDS a reason then proceeds (empty reason does NOT finalize); a declared-but-unmodified path prompts for and records a one-word acknowledgment then proceeds; both appear in ONE batched prompt; a clean delta produces NO prompt and finalizes silently; a headless run with a non-empty delta and no answers FAILS CLOSED.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: a test shows `aw ipd scope add <plan> <path> --reason` records the path+reason to run state WITHOUT editing the begin receipt, and a subsequent finalize consumes it (no re-prompt for that path); omitting the en-route call still finalizes (finalize prompts instead).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the full reconciliation test set (both directions, batched UX, clean no-op, headless fail-closed, en-route pre-fill, and verbatim durable attribution in the terminal history) passes; `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - the finalize two-way scope reconciliation (surface + attribute both deltas at the unskippable step) plus its optional en-route pre-record convenience.

### Execution contract

1. Open questions RESOLVED: no blocking OQ (design fixed by DECISIONS.md D141). PREREQUISITE: extends `aw ipd finalize` (Order 04) and reuses its scope-delta computation, so execute AFTER Order 04; if Order 04's delta computation is not available, STOP and report rather than recomputing it differently.
2. Scope fence: touch ONLY the single-IPD lifecycle module, `cli.py` (finalize reconciliation prompt + optional `ipd scope add` verb + help), `tests/test_ipd_lifecycle_cli.py`, and the lifecycle doc/spec via managed verbs. Do NOT change `aw ipd begin`'s frozen `Scope-Paths`, do NOT build rollback (Order 06) or remove the bypass (Order 07). If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, transition via `aw ipd finalize` (append the `## Workflow history` line, set `Status: executed`, move the plan, path-scoped lifecycle commit); if the finalizer cannot finalize this plan, STOP and report.
