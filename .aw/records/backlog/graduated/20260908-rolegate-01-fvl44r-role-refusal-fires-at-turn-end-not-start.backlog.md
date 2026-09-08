- Id: fvl44r
- Status: graduated
- Blocks-Release: next
- Set: rolegate
- Priority: high
- Work-Kind: bug
- Summary: The execute prompt implies the agent should finalize and never says the runner owns begin/finalize, so an agent does a full turn, attempts it, and is refused at the very end by AW-LIFECYCLE-ROLE-001; the rule is correct but is stated only in the refusal, not up front

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan 8b9ufm (Set roleadv, .aw/records/plans/pending/20260908-roleadv-01-8b9ufm-...ipd.md), which carries From-Backlog: fvl44r and inherits this item's Blocks-Release: next. Status graduated (design handed off), NOT done. TWO OF THE FIVE ASKS ARE DEAD ON MEASUREMENT AND WERE NOT GRADUATED, so nobody rebuilds them. ASK (4) IS A NO-OP: this item says the refusal should stop emitting the --scope-reason/--scope-ack reconciliation demand. IT EMITS NEITHER. Captured by invoking _refuse_worker_role_verb('finalize') at HEAD fac69fbd and substring-checking its stderr: both absent. The scope demand is built in _reconcile_scope (ipd_lifecycle.py:1716, flag strings :1768 and :1770) and surfaced only by finalize()'s findings branch (:2493-2508), which the role guard at :3126 returns BEFORE ever reaching. So whatever scope block 03ie04 reported came from the agent's own reasoning or from a non-worker invocation, not from this refusal. There is nothing to remove. ASK (3) IS HALF DEAD: the message already says 'The runner performs begin/finalize for this lane' and 'let the driver transition the plan' (ipd_lifecycle.py:96-99), so only the NON-ERROR FRAMING ('expected path, no further action required') is missing; that survives as the plan's E-05. TEST (f) needs no work either: zero side effects is already guaranteed by the guard's placement as the first statement of run_begin (:2946) and run_finalize (:3126) and already pinned by tests/test_worker_role_refusal.py and tests/test_turn_bounds.py. WHAT SURVIVED AND WAS GRADUATED: ask (1), the runner-owns-begin/finalize statement, unbuilt in ALL FOUR prompt builders (oc_runipd.build_prompt :4785, oc_runipd.build_verifier_prompt :4913, agy_runipd.build_prompt :2297, agy_runipd.build_verifier_prompt :2410) and in the three fragments they concatenate (lane_containment.isolation_notice :352, reporting_contract.prompt_block :114, DEFAULT_RUNBOOK_TEXT oc_runipd.py:2598); substring-verified absent: AW-LIFECYCLE-ROLE, begin/finalize, do not run, runner owns/runner performs. Ask (2), the misleading sentence, still verbatim at oc_runipd.py:4881-4884. Ask (5) is unbuilt and became the plan's OQ-01 rather than an E-item, because at build_prompt time the runner cannot know whether its own suite gate will later refuse, so a prompt promising the runner will finalize would be a claim it cannot keep. TWO DIAGNOSES IN THIS ITEM ARE WRONG AND ARE CORRECTED HERE. The misleading sentence exists on ONE host only: agy_runipd.build_prompt mentions finalize ZERO times, so REWORD has one site while STATE has four. And neither verifier prompt mentions finalize at all, so 'the verifier prompt shares the role' is wrong as a diagnosis while the remedy still applies (a verifier runs in the same worker lane under the same env selector). NO PLAN COVERED ANY PART: searched all five plan dispositions for AW-LIFECYCLE-ROLE, worker_role, rolegate, _refuse_worker, begin/finalize, build_prompt, build_verifier_prompt; the only pending hit is yvvf98:382, a note that its own lane runs as AW_EXECUTION_ROLE=worker. daexj1 (suite gate), ys1dor (run summary), u06zo2 (lifecycle policy spec) are all disjoint. THE PLAN REVERSES A RECORDED DECISION and says so: superseded tch3bo (lanecontain-01) F-12 recorded this exact mixed prompt signal and declined to fix it by wording, holding it is 'handled by ENFORCEMENT rather than by prompt wording'. NOT RE-VERIFIABLE FROM A LANE: this item's 46-turn/25-recovery figure needs .aw/records/runs/, which is gitignored and absent in a worktree; the plan rests on code measurements instead. Cited HEAD 31169afd is stale; all prompt claims were re-measured at fac69fbd.
- 2026-09-08 created (aw backlog): The execute prompt implies the agent should finalize and never says the runner owns begin/finalize, so an agent does a full turn, attempts it, and is refused at the very end by AW-LIFECYCLE-ROLE-001; the rule is correct but is stated only in the refusal, not up front

FOUND 2026-09-08, after a maintainer challenge to justify the finalize-time role refusal. The
refusal turns out to be JUSTIFIED but MIS-TIMED and MIS-ADVERTISED, and the cost is paid at the
end of a turn when it is most expensive.

## What is correct and must not be removed

`AW-LIFECYCLE-ROLE-001` prevents a SPLIT-BRAIN lifecycle transaction. An in-lane agent running
`aw ipd begin`/`aw ipd finalize` itself forks a SECOND receipt and a SECOND transaction the driver
cannot see, and the in-lane receipt copy then HIDES the split (`ipd_lifecycle.py:49-62`). The
receipt binds a frozen region digest and a base HEAD, so two transactions genuinely can disagree
about what was frozen. That hazard is real and this item does NOT propose weakening the rule.

The refusal is also already well built in two respects. It fires BEFORE any selector resolution,
gate, receipt write or plan mutation, so a refused invocation has NO side effect
(`_refuse_worker_role_verb`, `:84-101`). And the runner GENUINELY RECOVERS: measured across every
recorded outcome file, agents hit this refusal in 46 turns and in 25 of them the runner then
performed the finalize itself and the item reached `executed`. Of the 21 that did not, 19 failed
for unrelated reasons (11 `suite-failed`, 4 `integration-blocked`, 3 `merge-conflict`, 1
`interrupted`). So the recoverable handoff the maintainer asked for exists and works.

MEASURED, so this item is not misattributed: the finalize gate is NOT what stranded the eleven
lanes recovered on 2026-09-08. All twelve stranded items show `suite passing = False` and NO
finalize attempt at all; the driver-run suite gate refused before finalize was ever reached. That
cause is owned by plan `daexj1`.

## The actual defect: the agent is told to try, then refused for trying

THE PROMPT INVITES THE FORBIDDEN ACTION. Measured in the execute-prompt builder at HEAD
`31169afd`: the only mention of finalize is the sentence "If the IPD cannot validly finalize,
preserve partial work using the repository-supported ..." which presupposes the agent is the party
that finalizes. The prompt NEVER states that the runner owns begin/finalize, never names
`AW-LIFECYCLE-ROLE-001`, and never says "do not run these two verbs". Confirmed by substring:
`AW-LIFECYCLE-ROLE` absent, `begin/finalize` absent, `do not run` absent.

So the sequence an agent experiences is: do an hour of work, read a prompt implying you should
finalize, attempt it, get refused at the very end, and then have to reason out what to do. That is
the whole cost, and it is avoidable by saying so up front.

OBSERVED CONSEQUENCE 2026-09-08, which is what prompted this item. Plan `03ie04` completed all
seven E-items and all seven V-items with pasted evidence, then reported
`substantially-complete` with an `incomplete_requirements` entry explaining at length that
finalize had refused with `AW-LIFECYCLE-ROLE-001`, that no begin receipt existed, and listing the
scope reconciliation inputs a human would need. Every word of that was correct and none of it
should have been necessary: the agent spent output reasoning about a rule it could have been told
in one sentence at the start.

## What is wanted

1. STATE THE RULE AT TURN START. The execute prompt (and the verifier prompt, which shares the
   role) must say plainly that the runner performs `aw ipd begin` and `aw ipd finalize` for this
   lane, that the agent must NOT run them, and that the agent's terminal obligation is to write its
   outcome file and stop. Put it where the agent will act on it, not only in a refusal it may never
   see.
2. FIX THE MISLEADING SENTENCE. "If the IPD cannot validly finalize" must stop implying the agent
   finalizes. Reword to describe the CONDITION (the work is not validly complete) rather than the
   ACTION the agent is forbidden to take.
3. MAKE THE END-OF-TURN REFUSAL SAY "DONE, NOT BLOCKED". The current message is already corrective
   and already names the remedy, which is good. What it does not say is that this is the EXPECTED,
   NON-ERROR path for a managed lane, so an agent reads a hard refusal and reasonably reports its
   turn as incomplete. Say that the runner will now transition the plan and that no further action
   is required.
4. DO NOT ASK THE AGENT FOR SCOPE ANSWERS IT CANNOT GIVE. When the refusal fires, do not also emit
   the `--scope-reason`/`--scope-ack` reconciliation demand: the agent is not the party that will
   pass them, and computing them is `driver_finalize`'s job (`_compute_scope_reconciliation`).
   Emitting them invites the agent to record a long recommended-next-action block for a human, which
   is exactly what `03ie04` did.
5. CONSIDER WHETHER THE AGENT SHOULD BE ABLE TO ASK. The maintainer's framing is that a refusal is
   only acceptable when there is a recoverable route. There is one here (the runner finalizes), so
   no new escalation is needed for the normal case. But if the runner is NOT going to finalize
   (validation off and the suite gate refused, for instance) the agent should be told THAT, because
   then its work really is stranded and reporting it as complete is the misreport plan `ys1dor`
   fixes from the other end.

## Explicitly out of scope

- REMOVING OR WEAKENING the role rule. The split-brain hazard is real (see above) and the honest
  limit is already documented: it is an environment selector, not a hardened boundary, and hard
  enforcement is an OS sandbox question tracked elsewhere.
- The SUITE GATE that actually stranded the eleven lanes (`daexj1`).
- The green-COMPLETED misreport for a stranded run (`ys1dor`).
- `aw attention` blindness to a stranded lane (`nuanaw`).

## Test

(a) the execute prompt contains the runner-owns-begin/finalize statement, asserted by a prompt-text
test so it cannot silently regress; (b) the same for the verifier prompt; (c) the misleading
"cannot validly finalize" sentence no longer implies the agent performs the transition; (d) the
refusal message states that the runner will transition and that no further action is required; (e)
the refusal does NOT emit a scope-reconciliation demand; (f) the refusal still has zero side
effects, which the existing behavior already guarantees and must keep.
