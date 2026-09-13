# Review: decide and record Priority and Work-Kind for the pending plans with no source item, child lc4unl (Set planprio)

- Subject-Id: lc4unl
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `5e0e9873`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED (clean,
exit 0, 0 findings) before semantic review. At `--phase review-finalize` the linter reports three
`IPD-Q501`, which is the escalation gate working as designed: they are the three blocking questions this
review added. The suite was measured bare: `5971 passed, 3 skipped, 2 xfailed in 58.02s`.

DISCLOSURE: this Set was authored in the same repository by the same model family, so treat this as a
near-self-review worth less than an independent one. Its value rests on what was EXECUTED. Nine things
were computed or driven rather than recalled: the population recomputed from disk with the plan's own
predicate; E-02's inheritance condition EVALUATED against every plan in it; the same condition
re-evaluated on the hypothesis that orchestrators are decided first, to price the route honestly; each
Set's orchestrator inspected individually for whether its value comes from sibling 02 or a human; the
setid-versus-terminal collision computed; a setid dry-run DRIVEN to confirm the revert hazard; the setter
driven on an `approved` plan in a throwaway copy to see the history line; `aw att --type plan` run piped
and as JSON; and `aw check plans` run bare with its findings tallied per rule.

SCOPE OF THE LEDGER. The invocation named this child only, so the ledger is that one plan. The
orchestrator `d0cbt3` (already `reviewed`, `no-go`) and siblings `lkexaw` and `8u6770` (the latter
reviewed immediately before this one) were read as EVIDENCE and NOT edited.

THE PLAN'S THESIS IS SOUND AND ONE OF ITS IDEAS IS BETTER THAN IT KNEW. A population with no source
genuinely needs a human decision, and shrinking that decision before asking is exactly right. The
Set-inheritance route is legitimate on the repository's own terms (a value taken from an artifact the
plan names, one level up) and review PRICED it rather than merely accepting it: once the orchestrators
are decided, 13 human decisions cover all 28 plans, with `runanalytics` alone settling 9 children from
one decision. That is a better result than the plan claimed. Neither the thesis nor the route was
changed.

THE FIRST BLOCKER IS THAT THE ROUTE RESOLVES ZERO PLANS AS SEQUENCED, and it was found by evaluating the
condition rather than reading it. E-02 inherits from a Set orchestrator "where the orchestrator carries
both fields", and E-02 runs BEFORE E-03. Evaluated over the live population: NOT ONE of the orchestrators
of those 28 plans carries both fields, so the condition holds for 0 of 28 and the entire population falls
through to E-03's human list. The plan's whole value proposition evaluates to zero reduction as written,
and the maintainer would receive the 28-row table they explicitly asked to avoid. The fix is an ordering
one (decide orchestrators, then derive children), which is why review restructured the checklist into
partition / decide / write / derive and escalated the restructure itself as blocking OQ-02: it changes
what the maintainer is asked to confirm.

THE SECOND BLOCKER IS A COST DEPENDENCY THE PLAN EXPLICITLY DENIED. Its gate says it "is INDEPENDENT of
sibling 02 and may run before, after or concurrently with it, because E-01 tests for the fields rather
than for the source reference." That is true for CORRECTNESS and false for COST. Inspecting each
orchestrator individually, two of them (`orchprobe`'s `yeh7gc` from source `5ev6lh`, and `lanectn`'s
`h0zljh` from source `vqv9im`) get their values from SIBLING 02 rather than from a human, so their 4
children can be derived at zero human cost if 02 has run, and become 4 needless confirmations if it has
not. Escalated as blocking OQ-03, with a recommendation to record an ordering PREFERENCE rather than add
a hard edge to a sibling that is itself blocked.

THE THIRD BLOCKER IS INHERITED FROM THE PARENT, and it bites harder here than on any other member of the
Set. `- Item-Dependencies: executed:lkexaw` is the edge the parent's review measured as stranding 18
already-approved pending plans. Of those 18, 13 have NO source, so they can be unblocked only by THIS
plan, which the edge holds behind the gate that stranded them. Escalated here as OQ-04 so this file
refuses execution too, with the decision made once at the parent.

THE ROOT CAUSE THE THREE BLOCKERS SHARE is that the plan reasoned about its derivation route abstractly
and never evaluated it against the corpus. Every one of the three is a statement about WHEN a value
exists relative to when it is read: the orchestrator's value does not exist when E-02 reads it; sibling
02's write does not exist if this plan runs first; and the gate exists before the values it demands. The
smaller findings are of the same family or are the ordinary kind (a stale count, two evidence commands
that cannot produce what they ask, and an E-item bundling three deliverables).

WHAT REVIEW CHANGED. Three findings are OPEN and escalated; nine are FIXED. E-items grew 4 to 6 and
V-items 4 to 6, keeping the bijection: E-02 was RE-SCOPED from "apply the route" to "partition and write
nothing", a new E-05 performs the derivation that previously had no home, and E-06 separates the
no-collateral-change and observability proofs the authored E-04 had bundled with the bulk write. E-03
gained a non-interactive record-and-defer branch (without it an unattended run either stalls or
fabricates a confirmation) and a coverage column so the maintainer can see that 13 rows dispose of 28
plans. E-04 gained the id6 mandate, the dry-run preflight, `--no-commit` and `--message`. All counts were
refreshed with prior readings kept visible.

WHAT REVIEW DID NOT CHANGE, recorded because a reviewer that rewrites a sound plan does harm: the
Set-inheritance idea, the single-table-not-N-questions shape the maintainer asked for, the refusal to
fabricate a value, the honest naming of this plan's own conflict of interest, OQ-01's reasoning (which
review STRENGTHENED with the measured payoff and by making the auditability its safety argument depends
on an actual requirement), the deferral of specs and research to the parent, and the `- Item-Dependencies:`
line, left alone because two of the parent's three options keep an edge in some form.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; G. executability | E-02's condition evaluated over the live population: 0 of 28 satisfied; re-evaluated with orchestrators decided first: 13 decisions cover 28 plans | **Set inheritance resolves ZERO plans as sequenced, so the plan's entire value proposition evaluates to nothing.** E-02 requires the orchestrator to ALREADY carry both fields and runs BEFORE E-03. No orchestrator of the 28 carries them, so every plan falls through to the human list and the maintainer receives exactly the per-plan table they asked to avoid. The route itself is sound and pays well once the order is inverted | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED to OQ-02 with `- Blocking: yes` and `- Finding: PR-001`; refusal verified (`IPD-Q501` at line 180). Three options costed (invert into partition/decide/write/derive; drop the route and decide 28; seed orchestrators mechanically) with (a) recommended and (c) named as the one to avoid because it is fabrication, which `xprio`'s ruling and this plan's own conventions forbid. Review restructured the checklist to shape (a) so it is inspectable: E-02 partitions and writes nothing, E-03 asks about 13 units, E-04 writes, new E-05 derives. Recorded as F-2b |
| PR-002 | BLOCKER | IN-SCOPE | C. operability; G. executability | `orchprobe` orchestrator `yeh7gc` carries source `5ev6lh`; `lanectn` orchestrator `h0zljh` carries source `vqv9im`; 4 children between them | **Four plans can be derived for free if sibling 02 runs first, and this plan's gate denies any dependency on it.** The independence claim holds for CORRECTNESS (the fields test is order-safe) but not for COST: two orchestrators in this population get their values from sibling 02, not from a human, so running first converts 4 free derivations into 4 needless confirmations on the maintainer's table. The gate's "whichever runs second simply sees a smaller population" is precisely the sentence that hides this | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED to OQ-03 with `- Blocking: yes` and `- Finding: PR-002`; refusal verified (`IPD-Q501` at line 192). Three options costed (record an ordering preference without a hard edge; add `executed:8u6770`; have E-02 resolve the source itself) with (a) recommended, since the cost of the wrong order is 4 extra confirmations rather than a wrong outcome and a hard edge would couple this plan to a sibling carrying its own two blockers. The gate's independence sentence is now qualified as order-safe but not order-neutral. Recorded as F-2c |
| PR-003 | BLOCKER | IN-SCOPE | A. correctness; C. operability | parent `d0cbt3` OQ-02 and its PR-001; of the 18 stranded approved plans, 13 have no source | **The dependency edge is the parent's blocking defect, and the circularity is sharpest on this plan.** `executed:lkexaw` holds this plan behind the gate that strands 18 approved plans, and 13 of those 18 have no source, so they can be unblocked ONLY by this plan's decision table. This plan defends the edge with the same reasoning the parent measured false | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED to OQ-04 with `- Blocking: yes` and `- Finding: PR-003`, worded to be decided ONCE at the parent and recorded here, so the maintainer is not asked twice while this file still refuses execution. The edge itself was NOT edited, because two of the parent's three options keep it in some form. The authored justification is retained in the gate but marked as not surviving the measurement. Recorded as F-7 in the plan's table |
| PR-004 | BLOCKER | UNDER-SCOPE | G. executability; C. operability | the drivers' non-interactive notice; the `askme` contract ("a runner turn means NO, go to Step 5"); E-04 depending on E-03 | **E-03's critical path is a human decision and the plan had no non-interactive branch.** Under `aw oc run` / `aw agy run` the driver states the run is non-interactive and forbids invoking an interactive question tool, yet E-04 through E-06 all depend on E-03 completing. An unattended run would either stall the queue or fabricate a confirmation, and a self-granted approval of a table the executor composed is the worse of the two | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now records-and-defers exactly as the `askme` contract prescribes: compose the table, WRITE it into this plan, touch no other plan, and report E-04 onward deferred. It states plainly that a derived recommendation is evidence rather than a decision and that fabricating or self-granting a confirmation is forbidden. V-03 makes a fabricated confirmation a FAILED validation and requires the driver's own notice pasted. Recorded as F-5 |
| PR-005 | HIGH | IN-SCOPE | B. safety; A. correctness | `aw ipd set approved runanalytics --dry-run` reporting `executed -> approved` on `xbwq8n`; 3 of 10 setids colliding; backlog `f5pttg` (`open`, high) | **A setid selector would revert an executed plan, and the temptation is acute here precisely because this plan reasons in Sets.** Its whole insight is that one decision covers a Set; the wrong way to apply that is one setid command. Measured: `integearn`, `lanectn` and `runanalytics` all name both a population plan and a terminal one, and the dry-run proves the revert. `f5pttg` records this command having reverted seven executed plans for real | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 mandates the id6, names the three colliding setids, requires a `--dry-run` preflight whose output must read `unchanged` for exactly the named plan with a STOP otherwise, and cites `f5pttg`. E-06 adds the proof: the three terminal directories must be clean, and V-06 makes a non-empty result a failed validation regardless of everything else. V-04 makes a single setid invocation a failed validation. Recorded as F-6 and as correction 2 in the gate list |
| PR-006 | HIGH | IN-SCOPE | A. correctness; D. domain invariants | driven on orchestrator `5lxvl3` (`approved`): `- <date> approved (aw set): status set to approved` written with no transition; 13 of 28 are `approved` | **The setter's fabricated history line applies to the MAJORITY of this population.** Sibling 02 escalated the same defect over 5 plans; here it is 13 of 28. The plan prescribed the bare invocation, so it would have written 13 fabricated approval events in a Set whose purpose is to make plan metadata trustworthy | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 mandates `--message` with the measured before and after, and states explicitly that sibling 02's blocking OQ-02 owns whether that is sufficient and that this plan must inherit rather than independently decide it. The conventions block and the gate's correction 3 carry the same. Recorded as F-7 |
| PR-007 | MEDIUM | IN-SCOPE | Evidence accuracy | recomputed: 28 across 10 Sets, split 13 `approved` / 11 `reviewed` / 4 `to-review`, against the title's 20 and the authored 24 | **The population count is stale again, which the plan itself predicted but did not fix.** Its history line argues the number is a moving target and then quotes 24 in four places. The Set distribution also matters and was absent: `runanalytics` 10, `planprio` 4, `nobugship` 4, `orchprobe` 3, `setidfix` 2, then five Sets with one each | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern carries the full re-measurement with date and HEAD; E-01 requires a fourth derivation and forbids quoting any prior reading; the per-Set and per-status distributions are recorded so E-02's partition has an input. Recorded as F-1 and as correction 4 |
| PR-008 | MEDIUM | IN-SCOPE | A. correctness; G. executability | 5 Sets in the population have no Order-0 plan in `pending/` at all | **E-02 assumed a Set has an orchestrator wherever it has an Order.** Measured, `setidfix`, `defreport`, `integearn`, `runnerbugs` and `rdyrecheck` have no Order-0 plan in `pending/`, so their children have nothing to inherit from. Without this check the partition would claim coverage it cannot deliver | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires verifying the orchestrator EXISTS in `pending/` before counting on it, names the five Sets, and places their children in the individual-decision class. V-02 requires the existence check pasted per Set. Recorded as F-8 |
| PR-009 | MEDIUM | IN-SCOPE | E. testing | piped `aw att --type plan` emitting no Priority column; `aw check plans` at `errors 140` | **Two prescribed evidence commands cannot produce what V-04 asks.** It requires `aw att --type plan` showing no unprioritized pending plan (that surface has no Priority column at all) and `aw check plans` clean (140 pre-existing errors). An executor would report a false pass or try to clean a foreign sweep by editing other agents' plans | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06/V-06 use `FORCE_COLOR=1 aw att --type plan` and `aw att --type plan --format json` with a before-and-after non-null count (13 measured before), and require a per-rule DELTA against a pre-edit baseline with the 140-error breakdown quoted. Recorded as F-9 and as correction 6 |
| PR-010 | MEDIUM | UNDER-SCOPE | G. executability | the authored E-04 carrying a bulk write, a collateral-change proof and an observability claim; no item performing the child derivation | **One E-item bundled three deliverables and the plan's central derivation had no item at all.** A partial completion of the authored E-04 would have been indistinguishable from a full one. Separately, because E-02's condition could never hold before E-03, nothing in the plan actually derived the children after their orchestrators were decided | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into E-04 (write), E-05 (derive the children, which is the step that makes the route pay and which had no home), and E-06 (prove nothing moved and the result is observable), each with its own V-item. E-05 requires a per-child record of the orchestrator it inherited from. Recorded as F-10 |
| PR-011 | LOW | IN-SCOPE | A. correctness; F. principles | D153 (a setid is a shared cross-type topic label, not a containment claim) | A child must be matched to its orchestrator on the `- Set:` value AND Order-0 position, never on a filename resemblance. The plan said "its Set's Order-0 orchestrator" without excluding the filename route, and D153 records that a shared setid is a topic label rather than a containment claim | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 forbids deriving across a Set boundary or from a non-Order-0 plan and cites D153; V-05 requires confirming the orchestrator is Order-0 of that child's own Set rather than a filename match |
| PR-012 | LOW | IN-SCOPE | E. testing; B. safety | the plan's silence on `--no-commit`; the shared-checkout contract | Without `--no-commit` the setter offers to commit after each write, mid-loop, and accepting one in this checkout sweeps whatever else is staged. The plan warns about the index and then prescribes the invocation that invites the problem | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04's mandated invocation carries `--no-commit` with the reason; the gate and V-04 require it |

ALL THREE OPEN FINDINGS ARE DEFERRED-AS-OPEN UNDER THE FIX BAR, and every element the Bar demands is
stated.

PR-001 is overall Medium-High on FUNCTIONALITY with a secondary usability axis: functionality because as
sequenced the plan delivers none of its intended reduction, and usability because the maintainer receives
a 28-row table instead of 13. It reaches the threshold because the fix changes WHAT THE HUMAN IS ASKED TO
CONFIRM (orchestrator-level rows with a fan-out rather than a per-plan list), which is a scope decision
rather than a repair. The required decision is the maintainer's choice among three options. The
consequence of leaving it unresolved is that the plan runs, resolves nothing by inheritance, and hands
over the exact table it was written to avoid.

PR-002 is overall Medium-High on FUNCTIONALITY with a secondary usability axis: functionality because the
remedy options range from a recorded preference to a new dependency edge that couples this plan to a
blocked sibling, and usability because the wrong order costs the maintainer 4 unnecessary decisions. It
reaches the threshold because adding or refusing a dependency edge changes the Set's runnability, which
the parent's child table also states. The required decision is which of the three couplings to adopt. The
consequence of leaving it unresolved is a silently more expensive human step whenever the runner happens
to pick this plan first.

PR-003 is overall Medium-High on FUNCTIONALITY: the axis is functionality because the wrong ordering
makes 18 approved plans unrunnable and 13 of them are unblockable only by this plan. It reaches the
threshold because the remedy is a Set-level sequencing choice among three options, not an edit to this
file. The required decision is the maintainer's answer to the PARENT's OQ-02. The consequence of leaving
it unresolved is a circular Set: the gate blocks the plans that only this plan can fix, and this plan
waits on the gate.

Effort, time, cost and tokens played no part in any of the three deferrals.

Per the escalation rule all three are raised in the plan as open questions carrying `- Blocking: yes` and
a `- Finding:` id, and the refusal was verified rather than assumed: `aw ipd lint --phase review-finalize`
exits 1 with `IPD-Q501` naming OQ-02 at line 180, OQ-03 at line 192 and OQ-04 at line 203, so the plan
cannot reach `approved` or `begin` until the maintainer answers. `aw check plans` also stayed at its
140-error baseline with no finding naming this file, confirming the escalations are recorded in the shape
the consistency rule expects.

ONE THING IS WORTH THE MAINTAINER'S ATTENTION BEYOND THE FOUR QUESTIONS. All three children of this Set
are now `reviewed`/`no-go`, and their blockers are not independent: the parent's ordering question
(OQ-02 there) gates all three, sibling 02's setter question affects this plan's 13 approved plans too,
and this plan's own ordering question determines how much human work the Set costs. Answering the
PARENT's OQ-02 first is the highest-leverage single decision, because two of its three options also
dissolve the circularity that PR-003 describes.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Set inheritance resolves nothing as sequenced. Restructure the checklist myself, or reject the plan? | RESTRUCTURE IN PLACE into partition / decide / write / derive, and escalate the restructure as blocking OQ-02 rather than treating it as applied. | (a) `REJECT - NEEDS REPLAN`, rejected because the route, the population, the single-table shape and the conflict-of-interest handling are all correct; only the ORDER of two items is wrong, which is a bounded edit. (b) Restructuring silently and calling it fixed, rejected because it changes what the maintainer is asked to confirm (13 orchestrator rows with a fan-out, versus a per-plan list), and that is a scope decision rather than a repair. (c) Leaving the order and noting the problem in prose, rejected because it fails OPEN: an executor would run E-02, resolve nothing, and hand over the 28-row table. | E-02's condition evaluated over the live population (0 of 28); re-evaluated with orchestrators decided first (13 decisions covering 28) | yes |
| D-2 | Four plans depend on sibling 02 running first. Add the dependency edge myself? | NO. Escalate as OQ-03 with a recommendation to record an ordering PREFERENCE, and qualify the gate's independence claim. | (a) Adding `executed:8u6770` myself, rejected because it would couple this plan to a sibling carrying its own two blocking questions and would remove the concurrency the parent's child table explicitly grants, which is a Set-level change made from a child. (b) Leaving the independence sentence as written, rejected because it is the sentence that hides the cost and an operator reading it would see no reason to prefer either order. (c) Having E-02 resolve the orchestrator's backlog source itself, rejected because it duplicates sibling 02's logic in a second plan and the two would then have to agree about resolution and exclusion rules. | `yeh7gc` source `5ev6lh` and `h0zljh` source `vqv9im`, each inspected individually; 4 affected children | yes |
| D-3 | The plan's critical path needs a human. Prescribe the deferral branch, or escalate it? | PRESCRIBE IT. The `askme` contract already specifies record-and-defer under a runner, so this is applying a documented rule rather than making a judgement. | Escalating it as a question, rejected because the repository has already decided what a non-interactive run does with a human question (record and defer, never block, never fabricate), so asking would re-litigate settled policy. Leaving it silent, rejected because the failure mode is either a stalled unattended queue or a self-granted approval of a table the executor itself composed, and the second is the more damaging. | the drivers' non-interactive notice; `askme` Step 1 ("a runner turn means NO ... go to Step 5"); E-04's dependency on E-03 | yes |
| D-4 | Was reading the setter enough, or should it be driven on this population's majority status? | DRIVE IT, in a throwaway copy, on an `approved` orchestrator, because 13 of 28 plans here are `approved`. | Reusing sibling 02's finding without re-driving, rejected because the population differs (13 approved here versus 5 there) and the proportion is what turns an edge case into the majority case; the measurement is what justifies the emphasis. Driving it against the real tree, rejected outright: it is a shared checkout and the write would have landed on a co-worker's plan; the copy was used and discarded. | the throwaway copy; `5lxvl3` diff showing `status set to approved` with no transition; 13 of 28 measured `approved` | yes |
| D-5 | The plan reasons in Sets. Is warning about setid selectors in prose enough? | NO. Drive the hazard, name the three colliding setids, and make the terminal-directory emptiness a validation that fails the item. | Warning in prose only, rejected because `f5pttg`'s own analysis is that prose did not prevent the original incident, and because this plan's Set-oriented reasoning makes the setid the NATURAL selector to reach for, so the pressure toward the mistake is higher here than in sibling 02. Assuming sibling 02's collision list applies, rejected because the populations differ: 3 setids collide here against 6 there, and the specific names matter to the executor. | the `runanalytics` dry-run reporting `executed -> approved` on `xbwq8n`; 3 of 10 setids colliding; backlog `f5pttg` (`open`, high) | yes |

Every decision above is `Reversible: yes`, so recording is sufficient and no escalation is owed beyond
the three findings already escalated. None changes a published interface, migrates data, deletes
anything, or touches a released artifact; the three that could have (reordering the Set, adding a
dependency edge, deciding the setter's history behavior) are precisely the three left to the maintainer.

## Round 2


Opened 2026-09-12 to record the maintainer's answers to the questions round 1 escalated. Round 1 is left
exactly as written: the findings gate reads only the CURRENT round, and the reviews README states rounds
are appended rather than edited, so flipping a round-1 cell would hide that the question was ever put.
NO PLAN CONTENT WAS RE-CRITIQUED IN THIS ROUND and no new finding was derived; this records dispositions
and the in-plan edits that carry them. No product code was modified.

THE MAINTAINER ANSWERED THE SET'S ROOT QUESTION AND TWO CONSEQUENCES, in one interactive round:

RULING 1, ORDERING: RUN ORDERS 02 AND 03 BEFORE ORDER 01, chosen over stamping a grandfather sentinel
inside Order 01 (the shipped `Scope-Paths` precedent round 1 cited) and over staging the gate as
advisory. So no exemption marker is written anywhere and the corpus is real-valued before the gate
exists. The maintainer reached this by asking directly "Why not just do Order 02 and 03 before 01?",
which the review had costed but not recommended; the cost that made it viable is Ruling 2.

RULING 2, THE 13 UNDECIDED PLANS, accepted as a per-Set table rather than 13 separate answers:
`lanectn`/`xdr83v` high+bug (Concern: teardown destroys content silently; already gated);
`runnerbugs`/`hp9rot` high+bug (self-describing: "bugs/correctness", "verified runner defects");
`orchprobe`/`m7gvuz`+`r2i1b1` medium+bug (correctness defects, no data loss);
`runanalytics` all 9 children medium+feature (new capability, nothing pre-existing breaks).

RULING 3, GATING: "ALL BUGS MUST BLOCK THE NEXT RELEASE", verbatim, widening the reviewer's proposal.
Put as a decision separate from naming the work-kind, and the maintainer widened it deliberately, so
`hp9rot`, `m7gvuz` and `r2i1b1` gain `Blocks-Release: next` in the SAME setter call that writes
`Work-Kind: bug`.

A CORRECTION MADE DURING THAT ROUND, worth recording because it wasted a turn: the reviewer's first
framing conflated `Priority`/`Work-Kind` (which this Set makes REQUIRED) with `From-Backlog` (which it
does not touch and which stays optional; 28 of 120 pending plans have none and remain legal). The
maintainer caught it with "Are you planning on making all plans require From-Backlog?". `From-Backlog`
matters here for ONE reason only: Order 02 backfills by INHERITING from the source item, so its absence
is why 13 plans needed a human decision at all.


### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | G. Plan executability / C. Right-sizing | round 1: Set inheritance resolves ZERO plans while E-02 precedes E-03 | Carried forward: THE PARTITION ORDER MADE THE INHERITANCE ROUTE DEAD, so E-02 could resolve nothing before E-03 ran. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | MOOT UNDER RULING 2 for this execution: the per-Set table supplies all 13 values directly, so no inheritance route is needed. OQ-02 is `resolved` and instructs the executor to treat Ruling 2 as E-03's ANSWER rather than re-asking, while still re-deriving the population per E-01 and RAISING any plan found outside the recorded 13 instead of inferring a value for it. |
| PR-002 | BLOCKER | IN-SCOPE | G. Plan executability | round 1: four plans can inherit for free IF sibling 02 runs first | Carried forward: THE INDEPENDENCE CLAIM DEPENDED ON SIBLING ORDER. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | MOOT UNDER RULING 2: the table covers all 13 including those four, so independence stands and no route is built. OQ-03 is `resolved` and says to keep the observation as a note only. |
| PR-003 | BLOCKER | IN-SCOPE | G. Plan executability | the parent's OQ-02, now resolved; this plan's `- Item-Dependencies: executed:lkexaw` | Carried forward: SAME INVERTED DEPENDENCY EDGE as sibling 02's PR-001, deliberately worded to be decided ONCE at the parent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | RESOLVED BY RULING 1, identically: the edge is inverted and must be removed. OQ-04 is `resolved`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Ruling 3 gates three plans on `next` as a side effect of a metadata backfill. Is that in scope for THIS plan? | YES, and in the SAME setter call as `--work-kind bug`, per the maintainer's explicit widening. | Write `bug` now and gate later in `qmgn12` (rejected: it would leave a live `Work-Kind: bug` with no `Blocks-Release`, which is exactly the inconsistency `qmgn12` is built to DETECT, and in a shared checkout another agent's `aw check` could observe and report that window). | Maintainer Ruling 3 verbatim; E-04 and V-04 amended to require the flags together and to fail a bug lacking a gate. | yes |
| D-2 | Should Ruling 3 be applied repo-wide while we are here? | NO. Scoped to this plan's measured 13. | Sweep every `bug` artifact in the repo (rejected: that is `qmgn12`'s deliverable, and touching artifacts this plan never measured is scope creep in a shared checkout). | The plan's own population definition; `qmgn12`'s scope. | yes |
