# IPD: Make the driver finalize idempotent and tell a consumed receipt from a never-issued one

- Date: 2026-09-17
- Kind: child
- Concern: A begin receipt is a SINGLE-USE token with TWO consumers, so a completed item can be reported as unauthorized. Measured in run `run-20260917T210518Z-1714328`, IPD `63425h`: the driver ran `aw ipd begin` and it succeeded; the agent turn did its work and then finalized the plan ITSELF at 21:45:49Z (`575f0b32 lifecycle(63425h): finalize 63425h -> executed`); a successful finalize CONSUMES the receipt (`ipd_lifecycle.py:3570-3573`, "the transaction is cleanly complete"); the driver's own `driver_finalize` then ran finalize a SECOND time at 21:51:27Z, found no receipt, and refused with "no begin receipt for 63425h: run `aw ipd begin` first (fail-closed: no receipt = no execution authority)". The item was recorded `substantially-complete` and its lane PRESERVED as not-integrated while its work was complete, committed, and already in `executed/` on the lane. A human had to diagnose and merge it by hand (`2cfdb85d`).
- Scope: TWO changes, one per defect, in the two places that own them. (1) BEHAVIOR: make the driver's finalize step idempotent, so an already-finalized item proceeds to INTEGRATION instead of being refused. (2) DIAGNOSIS: make `finalize_precheck` distinguish a CONSUMED receipt (the transition already succeeded) from a NEVER-ISSUED one (genuinely no authority), with distinct findings a caller can branch on. Also decide and DOCUMENT one owner of the transition per item, because idempotence alone masks the root defect rather than removing it.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_finidem_double_finalize.py, tests/test_ipd_lifecycle_cli.py
- Item-Dependencies: none
- Status: draft
- From-Backlog: 02371s
- Set: finidem
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: ld8lb3

## Workflow history

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Backlog provenance

This plan graduates TWO backlog items, and the machine-readable `- From-Backlog:` field can name only one:

- `02371s` (high) THE BEHAVIORAL DEFECT: two finalizers for a single-use receipt. Carried in front matter.
- `894vzu` (medium) THE DIAGNOSTIC DEFECT: a consumed receipt and a never-issued one are indistinguishable.
  Named here because the field cannot hold it.

They are graduated together because they share one measurement, one reproduction and one regression test;
see the Goal for why splitting them would invite two partial fixes. Neither carries a release gate, so no
`Blocks-Release` is inherited.

## Goal

Stop reporting finished work as unauthorized, and make the refusal message name the cause that is
actually true.

WHY BOTH HALVES ARE ONE PLAN. They are two backlog items (`02371s` behavioral, `894vzu` diagnostic)
because they are two defects, but they share one measurement, one reproduction and one regression test,
and fixing either alone leaves real harm: idempotence without the message fix leaves every other caller
of `finalize_precheck` reading "no execution authority" for a consumed receipt, and the message fix
without idempotence leaves the finished lane unintegrated with a clearer explanation of why. Splitting
them would duplicate the fixture and invite two partial fixes.

THE DEEPER POINT, and the reason this is `high`: the receipt exists to be a fail-closed proof of
execution authority, and its single-use consumption is what makes it a PROOF rather than a flag. That
design is correct. What is wrong is that two independent actors both try to spend it, so the second
one's failure carries no information about authority at all. Making the driver merely tolerant of a
missing receipt would weaken the gate; the fix must instead let the driver observe that the transition
it wanted has ALREADY HAPPENED, which is a stronger claim than "the receipt is gone".

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Reproduce before changing anything

- [ ] E-01 Build a FAILING reproduction in `tests/test_finidem_double_finalize.py`: a scratch repo with a begin receipt, one successful finalize, then a SECOND finalize of the same plan. Assert the second refuses with the receipt message today. This is the falsifiable baseline every later item is measured against; write it first so the fix cannot be declared without it.
  - Depends on: none
  - Expected outcome: a test that FAILS to finalize on the second call and whose refusal text matches the message measured in run `run-20260917T210518Z-1714328` ("no begin receipt for ... no execution authority"). Paste the failure.
  - Execution state: pending

### Task group 2: Tell the three causes apart (894vzu)

- [ ] E-02 In `finalize_precheck`, replace the single `receipt is None` verdict with a classification, and return a DISTINCT finding id per cause: ALREADY-FINALIZED (the plan sits in a terminal directory), NEVER-ISSUED (no receipt and the plan is still non-terminal), and keep today's STALE branch untouched. Use the shared `run_selection_policy.is_in_terminal_directory` predicate rather than a second directory test.
  - Depends on: E-01
  - Expected outcome: three distinguishable outcomes from `finalize_precheck`, each with its own finding id and message; the NEVER-ISSUED message keeps its current wording because it is correct for that case.
  - Execution state: pending

- [ ] E-03 Make the ALREADY-FINALIZED message state the true situation and NOT prescribe `aw ipd begin`. Running begin on an already-finalized plan would mint authority for work that is complete, which is the actively harmful remedy today's message recommends.
  - Depends on: E-02
  - Expected outcome: the ALREADY-FINALIZED text names the terminal directory and the finalize commit if resolvable, and recommends no begin. Quote the before and after wording.
  - Execution state: pending

### Task group 3: Make the driver idempotent (02371s)

- [ ] E-04 At the driver's finalize site, treat ALREADY-FINALIZED as success: proceed to integration and record the item `executed`, rather than leaving it `substantially-complete` with a preserved lane. Consume E-02's finding id; do NOT re-derive the condition, and do NOT treat a bare missing receipt as success, which would weaken the fail-closed gate.
  - Depends on: E-02
  - Expected outcome: an item whose agent self-finalized ends `executed` and INTEGRATED. A genuinely never-issued receipt still refuses exactly as it does today.
  - Execution state: pending

- [ ] E-05 Apply the same change to the agy host, or prove it already shares the site. Both hosts call `driver_finalize`; if the finalize-result handling is forked, this fix must land on both or the two hosts will disagree about whether a self-finalized item is executed.
  - Depends on: E-04
  - Expected outcome: both hosts handle ALREADY-FINALIZED identically, evidenced either by one shared code path or by two changed sites.
  - Execution state: pending

### Task group 4: Remove the root cause, not just its symptom

- [ ] E-06 Decide and DOCUMENT one owner of the terminal transition per item, then make the non-owner not attempt it. Idempotence (E-04) stops the false refusal but leaves two actors racing for a single-use token; that race is the actual defect. Record the decision where an agent will read it: if the agent may self-finalize, the driver must not re-run finalize; if the driver owns it, the runbook/prompt must say so explicitly. NOTE the runbook currently does NOT instruct a finalize (measured: zero occurrences of `aw ipd finalize` in the lane's runbook input), so the agent finalized on its own initiative, which is why documentation is part of the fix rather than a nicety.
  - Depends on: E-04
  - Expected outcome: a written ownership rule, and the non-owner demonstrably not calling finalize. State which owner was chosen and why.
  - Execution state: pending

- [ ] E-07 Extend `tests/test_finidem_double_finalize.py` to pin the end state: the E-01 reproduction now reaches `executed` and INTEGRATED; a never-issued receipt still refuses; a STALE receipt still refuses. Assert the three finding ids are distinct, so a future change cannot silently collapse them back into one verdict.
  - Depends on: E-03, E-05, E-06
  - Expected outcome: a guard covering all three causes plus the integration outcome, shown to fail if any two causes are merged.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- THE RECEIPT IS DELIBERATELY SINGLE-USE. `ipd_lifecycle.py:3570-3573` consumes it on success with the
  comment "Consume the begin receipt (the transaction is cleanly complete)". That is the design and this
  plan must NOT change it; single use is what makes the receipt a proof rather than a flag.
- THE FAIL-CLOSED RULE IS LOAD-BEARING: "no receipt = no execution authority". E-04 must therefore key on
  ALREADY-FINALIZED (a positive observation) and never on "the receipt is absent", or it would convert a
  fail-closed gate into a fail-open one.
- `run_selection_policy.is_in_terminal_directory` is the SHARED predicate for "is this plan in a terminal
  disposition" (`TERMINAL_DIRECTORY_SEGMENTS` at `:506`). Verified: it returns True for an `executed/`
  path and False for a `pending/` one. Use it; do not write a second directory test.
- THE FINALIZE JOURNAL IS NOT AN AVAILABLE SIGNAL. `PHASE_COMPLETE` is written and then
  `_clear_finalize_journal` removes it in the same block (`:3986-3988`), so no journal survives a
  successful finalize. The terminal DIRECTORY is the durable evidence.
- `sync_receipt_into_worktree` IS A DELIBERATE NO-OP and must stay one. Its docstring records that copying
  the receipt into the lane was retired by the `dh0uno` control-root fix, that research `x03wgn` Section 7
  names the copy as its own hazard ("two authorities diverge or are consumed independently"), and that the
  prescribed guard is to DELETE the copy path. Restoring a copy is not an available fix here.
- `checkout_control_root` collapses a lane and the main tree to ONE control store, verified live. So the
  receipt was never split across trees in the measured incident; do not re-diagnose it that way.
- Both hosts call the shared `driver_finalize` (`runner_shared.py:8440` region for begin, and each host
  wraps finalize at its own name), so E-05 must check whether the RESULT HANDLING is shared or forked.
- The execution contract forbids `git add -A` and pushing; commit only declared `Scope-Paths`, path-scoped.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | A successful finalize consumes the receipt, by design | `ipd_lifecycle.py:3570-3573`, comment "the transaction is cleanly complete" |
| F-2 | With `self_finalize=True` (this run's value, and the default) TWO actors finalize one item | run state `options.self_finalize: True`; the agent finalized at `575f0b32` and the driver's `driver_finalize` ran after |
| F-3 | Begin DID run and DID succeed, so "no execution authority" was false | no `ipd-begin-refused` event, no `begin_refused` key on the attempt, and the agent turn launched (a nonzero begin returns before launching) |
| F-4 | The refusal came 5m38s AFTER the agent's own successful finalize | agent finalize commit 2026-09-17T21:45:49Z; `ipd-finalize-refused` event 2026-09-17T21:51:27Z |
| F-5 | The item was left `substantially-complete` with its lane preserved while the work was complete | run state disposition; the lane held 3 commits and the plan already in `executed/`; merged by hand as `2cfdb85d` |
| F-6 | `finalize_precheck` maps ONE condition onto a message asserting ONE specific cause | `ipd_lifecycle.py:1602-1611`: `if receipt is None:` -> "no begin receipt ... no execution authority" |
| F-7 | Absence has at least three causes with opposite meanings | never-issued (refuse, message correct); consumed by a successful finalize (work is DONE); the `dh0uno` split-store class (fixed, but the shape recurs) |
| F-8 | The remedy the message prescribes is harmful in the consumed case | running `aw ipd begin` again would mint fresh authority for work already finalized |
| F-9 | A durable ALREADY-FINALIZED signal EXISTS and is ignored | the plan sits in a terminal directory; `is_in_terminal_directory` returns True for it. The finalize journal does NOT survive (`_clear_finalize_journal` at `:3988`) |
| F-10 | The agent finalized on its OWN initiative, not because the runbook said to | zero occurrences of `aw ipd finalize` in the lane's runbook input, so E-06's documentation is part of the fix |
| F-11 | Restoring a receipt copy into the lane is NOT an available fix | `sync_receipt_into_worktree` is a deliberate no-op; research `x03wgn` S7 names the copy a hazard and prescribes deleting the path |

## Proposed changes (ordered, validatable)

1. Write the failing double-finalize reproduction first (E-01).
2. Classify receipt-absence in `finalize_precheck` into ALREADY-FINALIZED / NEVER-ISSUED, keeping STALE as
   is, with distinct finding ids (E-02) and an honest ALREADY-FINALIZED message (E-03).
3. Make the driver treat ALREADY-FINALIZED as success and integrate (E-04), on both hosts (E-05).
4. Decide and document one transition owner per item, and make the non-owner not attempt it (E-06).
5. Pin all three causes and the integration outcome (E-07).

## Deferred / out of scope (with reason)

- MAKING THE RECEIPT MULTI-USE is explicitly rejected, not deferred. Single-use consumption is what makes
  it a proof of a completed transaction; a reusable token would let two actors both believe they hold
  authority, which is the hazard `x03wgn` S7 already documents for the receipt-copy path.
- REPAIRING THE MEASURED RUN'S STATE FILE is out of scope. `63425h` still reads `substantially-complete`
  in `run-20260917T210518Z-1714328`'s state, and rewriting a historical run record would falsify history;
  the plan is correctly in `executed/` in main, so the durable record is right.
- The pre-existing duplicate-status backlog items (`egqt32`, `nuanaw`, tracked as `5bmq5f`) are unrelated
  and are the 2 violations `aw backlog check` reports today; do not "fix" them here.

## Scope check

- Over-scope: arguably E-06, which is a documentation/ownership decision rather than a code fix. Included
  deliberately: without it E-04 leaves two actors racing for a single-use token and merely hides the
  outcome, which is the definition of masking a defect.
- Under-scope: this plan does not audit every other `finalize_precheck` caller for the same misreading. If
  E-02 reveals callers that branch on the refusal TEXT rather than a finding id, name them as a follow-on
  rather than widening here.

## Required tests / validation

- `python3 -m pytest` bare and green with the actual summary line pasted (authoring baseline
  `7855 passed, 3 skipped, 2 xfailed`).
- The E-01 reproduction shown FAILING before the fix and PASSING after, both pasted. A test that passes in
  both states proves nothing here.
- Evidence the fail-closed property survives: a NEVER-ISSUED receipt still refuses, and the refusal text
  is unchanged for that case.
- A REAL driver execution in which the agent self-finalizes, ending `executed` and integrated with no
  preserved lane. This defect was invisible to the unit suite for as long as it existed, so an end-to-end
  demonstration is required rather than optional.

## Spec / documentation sync

No `.spec.md` is declared in `Scope-Paths`, and that is a deliberate claim rather than an omission: this
plan restores the intended behavior of an existing gate rather than changing a contract. HOWEVER, E-06
decides WHO owns the terminal transition, which is arguably contract-level. If the executor finds that
spec `25kzda` (or the `ipd-spec`) states or implies an owner, the amendment MUST be declared in
`Scope-Paths` before editing, per the plan-may-amend-a-spec rule, and the reason recorded here.

## Open questions

### OQ-01: Who should own the terminal transition, the agent or the driver?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN, and E-06 must resolve it with the maintainer rather than pick a
  side silently, because both defensible answers have a visible cost. DRIVER-OWNED is the tidier control
  story (one actor spends the token, the agent never touches lifecycle) but it means an agent that
  legitimately completes its work cannot record that fact itself, and every self-finalize in the field
  becomes a contract violation to police. AGENT-OWNED matches what agents actually do today (measured: the
  agent finalized with no runbook instruction to, F-10) and keeps the transition adjacent to the work that
  justifies it, but it makes the driver's job purely observational and requires the driver to trust a
  lane's own claim, which the fail-closed posture generally resists. E-04's idempotence makes the system
  CORRECT under either answer, which is why this does not block: the plan can land and be validated
  without it, and E-06 then records the decision. What is NOT acceptable is leaving it undecided and
  undocumented, which is the state that produced this defect.

### OQ-02: Should the driver treat a bare missing receipt as success if the plan is terminal?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and the distinction is the whole safety argument of this plan. The
  driver must key on a POSITIVE observation (the plan is in a terminal directory, i.e. the transition
  demonstrably happened) and never on the ABSENCE of a receipt. Keying on absence would convert
  "no receipt = no execution authority" from fail-closed to fail-open: any path that lost or never wrote a
  receipt would be read as success. The terminal directory is evidence a finalize RAN; a missing receipt is
  evidence of nothing in particular (F-7 lists three causes). E-02 and E-04 are written in that direction
  deliberately.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the reproduction's FAILURE output pasted, showing the second finalize refused with
    the "no begin receipt ... no execution authority" text. A reproduction that does not fail at HEAD is not
    a reproduction of this defect.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the three outcomes demonstrated with their DISTINCT finding ids: ALREADY-FINALIZED,
    NEVER-ISSUED, STALE. Show that the STALE branch's behavior is unchanged from HEAD.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the before and after ALREADY-FINALIZED message text, showing the new wording states
    the true situation and does NOT tell the operator to run `aw ipd begin`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the E-01 reproduction now reaching `executed` AND integrated; PLUS the fail-closed
    control, a never-issued receipt still refusing with unchanged text. Both pasted. The control is the
    load-bearing half: without it this item cannot be distinguished from weakening the gate.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: either proof the finalize-result handling is ONE shared code path both hosts reach
    (so one change covers both), or the two changed sites with matching behavior demonstrated per host.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the written ownership rule, quoted, naming which actor owns the transition and why;
    plus evidence the non-owner no longer calls finalize. If the maintainer resolved OQ-01, cite their
    answer; if not, state that the rule is recorded provisionally and the question remains theirs.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `python3 -m pytest tests/test_finidem_double_finalize.py` green; evidence it FAILS if
    two of the three causes are collapsed into one verdict (make the edit, paste the failure, revert);
    `python3 -m pytest` bare and green with the summary line pasted; AND a real driver execution in which
    the agent self-finalizes and the item still ends `executed` and integrated.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. It touches a FAIL-CLOSED SAFETY GATE, so the
executor carries one non-negotiable constraint: the fix must key on the positive observation that a
transition already happened, never on the absence of a receipt (OQ-02). Any diff that makes a missing
receipt sufficient for success is out of scope even if the suite passes.

Execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped,
never `git add -A`, never push. Paste ACTUAL runner output for every V-item.

Post-gate lifecycle: `aw ipd finalize` moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence. V-04's fail-closed
control and V-07's real driver execution are both mandatory: this defect passed the entire unit suite for
as long as it existed, so structural green is not evidence that it is fixed.
