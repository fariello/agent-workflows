- Id: fvl44r
- Status: open
- Blocks-Release: next
- Set: rolegate
- Priority: high
- Work-Kind: bug
- Summary: The execute prompt implies the agent should finalize and never says the runner owns begin/finalize, so an agent does a full turn, attempts it, and is refused at the very end by AW-LIFECYCLE-ROLE-001; the rule is correct but is stated only in the refusal, not up front

## Workflow history
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
