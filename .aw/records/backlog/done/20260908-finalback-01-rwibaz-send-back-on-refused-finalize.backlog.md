- Id: rwibaz
- Status: done
- Blocks-Release: next
- Set: finalback
- Priority: high
- Work-Kind: bug
- Summary: a finalize refused on unchecked E/V state ends the run as SUCCESS instead of sending the item back to the agent: spec 25kzda 4.6 requires RETRY for IPD-EXEC-E-COMPLETE, V-EVIDENCE and PRE-TRANSITION, and no code implements it

## Workflow history
- 2026-09-09 done (aw set): CLOSED via HANDOFF, not because the code is written. The design is graduated to plan zzcrlo (finalback-01, .aw/records/plans/pending/20260908-finalback-01-zzcrlo-send-a-refused-finalize-back-to-the-same-agent-with-the-gate.ipd.md), which carries - From-Backlog: rwibaz and the SAME - Blocks-Release: next, so the 2.0.0 release gate is PROVABLY PRESERVED rather than dropped by this close. Verified rather than assumed: check_engine.evaluate_blocking_close(repo, <this item>, 'done') returns severity 'ok' with reason "gate 'next' handed off to a From-Backlog plan or spec", which is the same predicate the setter, the aw check rules and the opt-in pre-commit hook all consult, so this is the HANDOFF fix and not a de-gating. WHY THE CLOSE IS CORRECT NOW: aw attention raised check.orphaned-live-blocker, whose whole point is that an OPEN release-blocking item already handed to a plan is double-counted; the release blocker now lives on zzcrlo, and leaving the item open would report one gate twice. WHAT IS EXPLICITLY NOT CLAIMED: the bug is NOT fixed. zzcrlo is at to-review with two OPEN questions, so it is neither approved nor executed. The underlying defect stands (spec 25kzda 4.6 requires RETRY for IPD-EXEC-E-COMPLETE, V-EVIDENCE and PRE-TRANSITION-REFUSED, while a finalize refused on unchecked E/V state currently ends the run as SUCCESS). Anyone reading this item as 'shipped' is misreading it: done here means the DESIGN is handed off and the gate travels with the plan. The release gate is discharged only when zzcrlo is executed. Item not authored by me; closed on the maintainer's instruction after verifying the handoff is real.
- 2026-09-08 created (aw backlog): Measured in run-20260908T213552Z-3724920 (agy, plan xbwq8n): the agent wrote correct code and committed it to a lane, never ticked its E/V boxes, finalize refused with nine IPD-S404 findings, and the runner recorded substantially-complete, printed COMPLETED, exited 0, and stranded the work. Spec 25kzda is approved and MANDATES RETRY plus a bounded correction packet for exactly these three checks; the IPD-EXEC-* codes grep to zero files, which the spec itself admits at :39. Filed with Blocks-Release: next because this is a spec-conformance gap on an approved release-gating spec, not a feature request.

THE REFUSAL IS CORRECT. WHAT IS MISSING IS THE SEND-BACK. Nothing here asks for a weaker gate: the
pre-transition gate did exactly its job. The defect is what happens NEXT, which today is nothing.

THE MEASURED INCIDENT, `run-20260908T213552Z-3724920` (host antigravity, plan `xbwq8n`, Order 01 of
Set `runanalytics`). The agent produced GOOD work: `state_root` resolved through `project_context`
rather than the hardcoded literal, containment applied to all three run enumerators plus the ledger
builder, `5882 passed` in the lane, a symmetric AST guard against reintroducing the literal, and a
negative control that genuinely fails against pre-fix code (all independently re-verified). It then
never ticked a single `E-*` or `V-*` box and pasted no `Observed evidence`. `aw ipd finalize` refused
with nine findings:

    IPD-FINALIZE IPD-S404 E-01/E-02/E-03: not 'performed' at pre-transition
    IPD-FINALIZE IPD-S404 V-01/V-02/V-03: not 'pass' at pre-transition
    IPD-FINALIZE IPD-S404 V-01/V-02/V-03: empty Observed evidence at pre-transition

The runner then printed `! IPD xbwq8n finalize refused (left substantially-complete, not forced)`,
preserved the lane, rendered a run summary reading `Outcome: COMPLETED`, `Progress: 1/1 [==========]
100%`, and exited 0. Two commits (`661643bb`, `ff092eae`) remain stranded on `aw/lane/xbwq8n`,
unmerged. A human who trusted the summary would believe Order 01 of a ten-plan Set had landed. It had
not, and the nine other plans in that Set depend on the resolver it delivers.

WHY THE RUN REPORTED SUCCESS, which is the part worth fixing first: `substantially-complete` is a
MEMBER of `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:337`, `{"executed", "substantially-complete"}`).
So a refused finalize lands the item in a state the summary counts as success. The agent's own outcome
JSON claimed `"disposition": "executed"`, and the runner correctly downgraded it one notch
(`oc_runipd.py:6007-6010`), but one notch down is still success.

THE SPEC ALREADY REQUIRES THE FIX, so this is conformance work rather than a proposal. Spec `25kzda`
(`- Status: approved`, `- Blocks-Release: next`) Section 4.6 assigns `RETRY` to precisely the three
checks this run failed:

  - `IPD-EXEC-E-COMPLETE` (`:711`), "Every E item is checked and has an action receipt or artifact
    binding" -> action `RETRY, then FAIL ITEM`.
  - `IPD-EXEC-V-EVIDENCE` (`:712`), "Every V item has a passing result, nonempty concrete observed
    evidence" -> action `RETRY, then FAIL ITEM`.
  - `IPD-EXEC-PRE-TRANSITION` (`:714`), "Linter passes before terminal mutation" -> action
    `RETRY, then FAIL ITEM`.

Section 4.1 (`:586`) defines the verb: "RETRY: enter `correction_required`, issue a bounded correction
packet, and retry the checker while the frozen retry budget remains. The default correction budget is
2." Section 5.5 (`:974-975`) explicitly ALLOWS spending budget on "failed deterministic check for
which a bounded correction is safe" and "missing or stale validation evidence", and its prohibition
list (`:978-989`) does NOT contain them. Section 5.3 (`:922`) specifies the mechanism: "If a known
partial state exists and retry budget remains, it emits a correction packet containing only failed
predicates and existing evidence."

NONE OF IT IS BUILT, and the spec says so about itself at `:39`: "EVERY OTHER FAMILY GREPS TO ZERO
FILES under `agent_workflows/`: all 11 `IPD-EXEC-*` ...". Confirmed at HEAD:
`grep -rn "IPD-EXEC-E-COMPLETE\|IPD-EXEC-V-EVIDENCE\|IPD-EXEC-PRE-TRANSITION" agent_workflows/`
returns nothing. Only the 13 `RUN-*` codes were ever bound.

THE THREE CONCRETE MISSING PIECES, each verified at HEAD:

  1. NO TRIGGER. The refusal arm is terminal. `agy_runipd.py:3910-3930` writes
     `attempt["finalize_refused"]` and `item["finalize_refusal"]`, emits an `ipd-finalize-refused`
     event, prints, and falls through; twin at `oc_runipd.py:6853-6873`. Nothing classifies an
     `IPD-S404` refusal as correctable.
  2. NO FEEDBACK. `finalize_refusal` is WRITTEN at exactly two sites (`agy_runipd.py:3911`,
     `oc_runipd.py:6854`) and READ AT ZERO. It is also absent from `lane_containment.py`'s
     prior-attempt allowlist, so even the existing recovery prompt could not tell the agent WHAT
     refused.
  3. NO SAME-RUN RE-DISPATCH, and no budget spend. `run_recovery.plan_retry` (`:269`) and
     `retry_budget_remaining` (`:415`) have ZERO production callers; the module documents its own
     dormancy at `run_recovery.py:53`. The only re-prompt paths are `interrupted` requeue and an
     OPERATOR-invoked `resume --retry-incomplete`.

THE WIRING IS UNUSUALLY CLOSE, which is the argument for doing it now: `substantially-complete` is
ALREADY in the `--retry-incomplete` status set (`oc_runipd.py:7221-7223`), the recovery prompt already
interpolates a `Mode: RECOVERY/CONTINUATION` header and a `Prior attempt:` summary
(`agy_runipd.py:2371-2373`), and the budget helpers are already written and tested. What is missing is
the trigger, one allowlist entry, and the automatic dispatch.

WHY THE VERIFIER DID NOT CATCH IT, recorded so nobody assumes verification covers this. The verifier
prompt DOES instruct the agent to check the evidence table (`agy_runipd.py:2496-2499`, "Check every
Execution item (`E-*`) and every Validation item (`V-*`)"), and this run recorded
`verification: verified` anyway. That is the fail-open documented by backlog `wyw936`: only
`BLOCKED`/`NOT CONFORMING` downgrade, so the schema's own `CORRECTION_REQUIRED` verdict is recorded
`verified`. So the verifier cannot be relied on as the enforcement point here; the deterministic gate
already has the right answer and simply needs to be acted upon.

RELATIONSHIP TO EXISTING WORK, so this does not duplicate or collide:

  - `xipfy1` (`to-review`, Set `retrywire`, `Blocks-Release: next`) is the BUDGET METER. It does not
    cover this trigger: its input vocabulary is the `disposition` enum, and `substantially-complete`
    is a SUCCESS value there, not a failure class to allowlist. Its own Deferred section (`:114`)
    excludes "ROUTING `CORRECTION_REQUIRED` BACK TO RUNNABLE" and states the mutual dependency
    exactly: "a correction route with no budget is unbounded; a budget with no correction route is
    dead". Its blocking OQ-01 (`:135-140`) already warns that landing the budget alone leaves "the
    most valuable trigger disconnected". SEQUENCE THIS WITH `xipfy1`.
  - `wyw936` (`graduated`) plus its plan `1bfppy` (`to-review`) own the VERDICT MAPPING fail-open.
    `1bfppy:114` explicitly defers the `correction_required -> runnable` requeue. Different trigger (a
    verifier verdict string, not a deterministic gate refusal), same missing edge.
  - `r2i1b1` (`approved`, Set `orchprobe`) makes refusal reasons VISIBLE and adds a remedy field, but
    its scope states "OUT: ... changing what any existing gate decides". Surfacing is not sending back.
  - `daexj1` (`reviewed`, `Readiness: no-go`) is the RULED PRECEDENT for bounded agent re-prompting:
    on 2026-09-08 the maintainer rejected a hard programmatic gate as "very fragile" and directed the
    runner to ASK THE AGENT, parsing three sentinels and re-prompting when none is present, with both
    loops explicitly bounded. Its trigger is a red test suite, not E/V state, but its shape is the one
    to follow here.

SUGGESTED SHAPE, keeping the gate's authority intact: on an `IPD-S404` refusal, if retry budget
remains, emit a correction packet containing ONLY the failed predicates (the gate's own findings, which
are already computed and already in `finalize_refusal`), re-dispatch the SAME item in the SAME run with
`recovery=True` so the existing recovery prompt carries them, and spend one unit of the frozen budget.
On budget exhaustion, FAIL THE ITEM rather than reporting success, which is Section 4.6's "then FAIL
ITEM" half and is the part that matters most: the run must not print `COMPLETED` over a refused
finalize.

TWO CONSTRAINTS A PLAN MUST HONOR. FIRST, never let the correction turn WEAKEN the gate: the agent may
tick a box only by doing the work and pasting real evidence, and `AGENTS.md` already forbids writing an
attestation for work not performed, so the correction prompt must say that explicitly or it invites
exactly the forgery this repository fails closed against. SECOND, bound the loop, per `daexj1`'s ruling:
a correction route with no bound is how an unattended run hangs.

VERIFY WITH: reproduce by executing any approved plan with a host that does not update its checkboxes,
then assert the run does NOT report `COMPLETED`, that a correction attempt was dispatched carrying the
`IPD-S404` findings, and that budget exhaustion fails the item. Regression-guard that
`substantially-complete` plus a non-empty `finalize_refusal` can never be counted as run success.
