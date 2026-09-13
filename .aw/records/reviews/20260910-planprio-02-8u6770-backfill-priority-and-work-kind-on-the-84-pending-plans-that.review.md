# Review: backfill Priority and Work-Kind on the pending plans that can inherit from their source item, child 8u6770 (Set planprio)

- Subject-Id: 8u6770
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `fe57b1a4`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED (clean,
exit 0, 0 findings) before semantic review. At `--phase review-finalize` the linter reports two
`IPD-Q501`, which is the escalation gate working as designed: they are the two blocking questions this
review added. The suite was measured bare: `5971 passed, 3 skipped, 2 xfailed in 59.68s`.

A CORRECTION THIS REVIEW MADE TO ITSELF, recorded because the tooling caught it and a reader should see
that it did. PR-001 was first written as merely INHERITED from the parent, on the reasoning that
duplicating the parent's blocking question would ask the maintainer to answer the same thing twice. Then
`aw check plans` flagged this file with `check.review-finding-unescalated`, taking the plans-tree count
from 140 to 141. The rule is right and the reasoning was wrong: an OPEN finding at or above the gate
threshold must refuse execution of the ARTIFACT it is about, and this child is the artifact carrying the
edge, so the parent's refusal does not protect it. OQ-03 was added here with `- Finding: PR-001`, worded
to be decidable on its own but explicit that the answer is made ONCE at the parent and recorded here.
The count returned to 140 and no finding now names this file. This is exactly the backstop the rule was
built to be, and it worked against a reviewer who had talked himself out of the escalation.

DISCLOSURE: this Set was authored in the same repository by the same model family, so treat this as a
near-self-review worth less than an independent one. Its value rests on what was EXECUTED. Eight things
were driven rather than recalled: the whole pending corpus and its inheritance graph recomputed from
disk; the setter DRIVEN in a throwaway repo copy against one `reviewed` and one `approved` plan and the
resulting diffs read; the same call driven again WITH `--message` to see whether the false line changes;
`--dry-run` driven to confirm it writes nothing; a SETID selector dry-run driven to test the
mis-selection hazard; the setid-versus-terminal collision computed across the whole population;
`aw check plans` run bare with its findings tallied per rule; and `aw att --type plan` run piped to see
whether the Priority column exists there.

SCOPE OF THE LEDGER. The invocation named this child only, so the ledger is that one plan. The
orchestrator `d0cbt3` (already `reviewed`, `no-go`) and siblings `lkexaw` and `lc4unl` were read as
EVIDENCE and NOT edited. One consequence is stated where it matters: PR-001 is the parent's finding, not
a new one, and its remedy lands in the parent's answer rather than in this file.

THE PLAN'S THESIS IS CORRECT AND ITS SHAPE IS RIGHT, and review changed neither. Inheritance really is
judgement-free: re-measured at this HEAD, 92 pending plans carry a `- From-Backlog:`, ZERO references
dangle, ZERO sources are missing either field, and ZERO source values are out of vocabulary. The
inherited distribution is a genuine spread rather than a single default. Using the shipped `aw ipd set`
rather than hand-editing front matter is the right call, and the no-op persistence it relies on WORKS:
driven on both statuses that occur in the population, the call exits 0, prints `unchanged`, writes both
fields, and leaves `- Status:` untouched.

THE BLOCKER IS THAT THE SETTER WRITES A FALSE HISTORY LINE, and it was found by driving the tool rather
than reading its `--help`. On plan `5e4sb6` (status `approved`), `aw ipd set approved 5e4sb6 --priority
medium --work-kind chore` correctly writes both fields and then prepends `- 2026-09-12 approved (aw
set): status set to approved` to the workflow history, asserting an approval event that did not occur on
a plan whose real approval is already recorded with its own date and actor. 5 of the 81 plans in the
population are `approved`, so 5 records would carry a fabricated approval event. This Set exists
precisely to make plan metadata trustworthy, which is what turns a cosmetic-looking blemish into a
self-defeating outcome. A remedy is verified (`--message` replaces the sentence), and whether one line
per approved plan is acceptable at all is the maintainer's call. Escalated as blocking OQ-02 with three
costed options.

THE SECOND HAZARD IS THE ONE MOST LIKELY TO CAUSE REAL DAMAGE, and it is a live shipped defect rather
than a hypothetical. `aw ipd set` resolves a SETID to every plan carrying it, terminal ones included.
Measured across this population, 6 of the 57 setids also name a plan in `executed/`, and `aw ipd set
approved rununify --priority medium --work-kind chore --dry-run` reports `executed -> approved` on TWO
plans in `executed/`. Backlog `f5pttg` (`open`, high) records that this exact command silently reverted
seven executed plans in one invocation, caught only because the operator ran `git status` out of
caution. The authored plan said "one plan at a time" but never said BY WHAT SELECTOR, and an executor
looping over a Set would reach for the setid naturally. Fixed in place with a mandated id6, a
dry-run preflight, and a terminal-directory emptiness proof.

THE ROOT CAUSE THE SMALLER FINDINGS SHARE is that the plan trusted documentation and its own authored
measurement where it could have driven the tool. The `--help` text says the flags persist on a no-op, so
the plan treated the write as solved and called the transition guard an unknown to discover at execution
time; driving it settled the guard AND surfaced the history line. The authored counts were taken once
and never re-derived, so 11 plans that already carry both fields were never excluded. And two prescribed
evidence commands were written from an assumption about what they print.

WHAT REVIEW CHANGED. Two findings are OPEN (one inherited from the parent, one newly escalated) and nine
are FIXED. E-items grew 4 to 6 and V-items 4 to 6, keeping the bijection: E-05 proves the result is
observable on a surface that actually carries Priority, and E-06 reports the residue so sibling 03's
population can be reconciled. E-01 now excludes the 11 already-complete plans and records each plan's
status; E-02 carries review's measured expectations so a divergence is informative; E-03 gained the id6
mandate, the dry-run preflight, `--no-commit`, and the `--message` requirement; E-04 gained the
terminal-directory proof and lost the unobtainable "clean checker" bar. All stale counts were corrected
with both readings kept visible.

WHAT REVIEW DID NOT CHANGE, recorded because a reviewer that rewrites a sound plan does harm: the
inheritance design itself, the refusal to fabricate a value, the refusal to correct a source backlog
item, the choice to use the shipped setter rather than a script, the deferral of the no-source plans to
sibling 03, OQ-01's faithful-inheritance answer (which review NARROWED with a measurement rather than
overturning), and the `- Item-Dependencies:` line, which was deliberately left alone because it is the
parent's open question and editing it here would pre-empt the maintainer's choice among three options.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; C. operability; G. executability | parent `d0cbt3` OQ-02 and its PR-001; this plan's `- Item-Dependencies: executed:lkexaw`; the authored gate justification | **The dependency edge this plan carries is the parent's blocking defect, and this plan defends it with reasoning the parent's review measured to be false.** The parent found that `executed:lkexaw` strands 18 already-approved pending plans the moment sibling 01 lands, because the gate fires at every lint phase for a plan at the ready-to-execute tier. This child's gate justifies the edge with "backfilling before the gate exists would write values nothing enforces", which inverts the mechanism: a value written before the gate exists is exactly what the gate then finds satisfied. The edge may be reversed or removed by the parent's answer | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED to OQ-03 on THIS plan with `- Blocking: yes` and `- Finding: PR-001`, after `check.review-finding-unescalated` correctly rejected the first attempt to treat it as merely inherited (see the correction note above). The question is worded to be decided ONCE at the parent (`d0cbt3` OQ-02, three costed options, "stamp inside Order 01" recommended) and recorded here, so the maintainer is not asked twice while this file still refuses execution. The edge itself was NOT edited, because two of the parent's three options keep it in some form. Recorded as F-7; the authored justification is retained in the gate but explicitly marked as not surviving the measurement, with an instruction not to defend the edge with it and to bring the metadata into agreement in whatever change answers the parent |
| PR-002 | BLOCKER | IN-SCOPE | A. correctness; D. domain invariants | driven in a throwaway copy on `5e4sb6` (`approved`): the diff shows both fields added, `- Status:` unchanged, and `- 2026-09-12 approved (aw set): status set to approved` prepended; the same call with `--message` writes the supplied text instead; backlog `x6tk1u` | **A same-status write appends a history line asserting a transition that did not happen.** 5 of the 81 plans are `approved`, so 5 records would carry a fabricated approval event, on plans whose real approval is already recorded with its own date and actor. A Set whose purpose is to make plan metadata trustworthy cannot fabricate approval history in service of it. `--message` replaces the sentence (verified), but whether to write any line onto an approved plan is a judgement, and the honest fix is code work in the shared setter that intersects the still-open `x6tk1u` | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED to OQ-02 with `- Blocking: yes` and `- Finding: PR-002`; refusal verified mechanically (`IPD-Q501` at line 167, exit 1). Three options costed (write all 81 with a truthful message / write the 76 `reviewed` and defer the 5 `approved` / fix the setter first) with (a) recommended and (c) named as the right long-term fix but the wrong thing to block this Set on. E-03 now mandates `--message` and forbids proceeding past the first `approved` plan until answered; V-03 requires the resulting history line pasted and checked |
| PR-003 | HIGH | IN-SCOPE | B. safety; A. correctness | `aw ipd set approved rununify --dry-run` reporting `executed -> approved` on two `executed/` plans; 6 of 57 setids colliding with terminal plans; backlog `f5pttg` (`open`, high) | **A setid selector would revert executed plans, and the plan never said which selector to use.** It says "one plan at a time" but not by what token, and an executor working through a Set would reach for the setid. Measured: `hostdefault`, `integearn`, `integpath`, `lanectn`, `rununify`, `setidhard` all name both a population plan and a terminal one. `f5pttg` records this exact command having reverted seven executed plans, and it is still open, so nothing protects the executor but the selector choice | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now mandates the id6, names all six colliding setids, requires a `--dry-run` preflight whose output must read `unchanged` for exactly the one named plan (with a STOP if it does not), and cites `f5pttg`. E-04 adds the proof: `git status --porcelain` over the three terminal directories must be EMPTY, and V-04 makes a non-empty result a failed validation regardless of everything else. Recorded as F-6 and as correction 1 in the gate list |
| PR-004 | HIGH | IN-SCOPE | A. correctness; Evidence accuracy | recomputed at review: 11 pending plans already carry BOTH fields | **11 plans already carry both fields and the plan would have overwritten them.** The authored derivation selects on having a resolving source, not on needing a value, so the write population was 92 rather than 81. Overwriting a deliberately chosen value with an inherited one is a silent downgrade, and it is invisible afterwards because both values are in-vocabulary | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now excludes a plan carrying both fields, states that a plan carrying exactly one is in scope for the missing field only, and requires the excluded list pasted. V-01 demands that list. Recorded as F-1b and as correction 3 in the gate list |
| PR-005 | MEDIUM | IN-SCOPE | Evidence accuracy | recomputed: 120 pending, 92 with a resolving source, 81 needing a field, 28 with no source, against authored 104/84/84/20 | **Every headline count is stale, and one is structurally wrong rather than merely dated.** The population grew (104 to 120) and the no-source remainder grew (20 to 28), but the load-bearing error is that `84` conflated "can inherit" with "needs a value" (PR-004). The parent's review had already re-measured these and this child was not updated | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern block carries the full re-measurement with date and HEAD; E-01 instructs deriving a third reading and forbids quoting either prior one; F-1 rewritten; the parent's figures are offered as orientation only. Recorded as correction 4 in the gate list |
| PR-006 | MEDIUM | IN-SCOPE | E. testing | `aw att --type plan` piped emitting `- [plans] <path> (<status>)` with no Priority column; `aw check plans` measured at `errors 140` (124 `check.scope-drift`, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`) | **Two prescribed evidence commands cannot produce what V-04 asks for.** It requires `aw att --type plan` showing a populated Priority column (that surface has none; the column exists only in the colored renderer) and `aw check plans` clean (it is 140 errors deep before this plan touches anything). An executor would either report a false pass or try to make a foreign sweep clean by editing other agents' plans, which the shared-checkout rule forbids | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05/V-05 now use `FORCE_COLOR=1 aw att --type plan` and `aw att --type plan --format json` with a before-and-after non-null `priority` count. E-04/V-04 require a per-rule DELTA against a pre-edit baseline, quote review's 140-error breakdown, and forbid reducing a count by editing another party's artifact. Recorded as F-8 and as corrections 5 and 6 |
| PR-007 | MEDIUM | UNDER-SCOPE | G. executability; E. testing | the plan's Goal (a populated Priority column) with no item observing it; no item reporting the residue | **Nothing proved the plan achieved its stated goal, and nothing reported what remained.** The goal is a populated Priority column on the attention board, and the only prescribed surface for it cannot show one (PR-006). Separately, no item re-counted the plans still missing a field afterwards, so the Set could not reconcile the residue against sibling 03's population and a partial backfill would report success | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added E-05 (observe on both real surfaces, with a before-and-after count whose delta must match the number of plans written) and E-06 (re-count the residue, reconcile it against sibling 03's 28, and NAME every skipped plan with its reason), each with a matching V-item. The scope check now records both as gaps found at review rather than leaving `- Under-scope:` understated |
| PR-008 | MEDIUM | IN-SCOPE | B. safety | the setter's commit offer on each write; the shared-checkout contract | **Without `--no-commit` the setter offers to commit after each write, mid-loop, in a shared checkout.** The plan's own gate warns about the index hazard and then prescribes an invocation that invites exactly it: accepting an offered commit sweeps whatever else is staged, including another agent's work | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03's mandated invocation now carries `--no-commit` with the reason stated, and the gate repeats it. Recorded as F-10 |
| PR-009 | MEDIUM | IN-SCOPE | G. executability | E-03's authored text: "a no-op transition on some statuses may refuse or may require a message. Record exactly which invocation form worked" | **E-03 defers to execution time a question review could settle in one command, on a plan that then writes 81 files.** Discovering the invocation form mid-bulk-write is how a loop half-completes. Driven at review: both statuses that actually occur (`reviewed`, `approved`) accept the call, so there is no guard to discover | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now states the verified invocation explicitly and records that the no-op write is confirmed on both statuses, replacing the discovery instruction. The conventions block carries the same fact, plus the field-insertion position the diff revealed |
| PR-010 | LOW | IN-SCOPE | E. testing; G. executability | E-02's authored text asking for tails without saying what to expect; review's measured distribution and tails | E-02 asks for a distribution and out-of-vocabulary check with no expected result, so an executor cannot tell a normal reading from an anomalous one. Measured: zero out-of-vocabulary, zero absent, and the release-blocking tail is 17 of 81 with every one `medium` and none `low` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 carries review's full distribution and both tail counts as expectations to compare against, with divergence called out as informative. V-02 requires the comparison and the `low` count stated |
| PR-011 | LOW | IN-SCOPE | E. testing | OQ-01 as authored, worrying about a release blocker inheriting `low` | OQ-01's central worry does not occur in the current population: of the 17 release-blocking plans, all inherit `medium` and none `low`, so the residual question is only whether `medium` plus a gate is acceptable, which source item `p9o1oo` already answers yes | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 kept `open` (the population moves and looking at the 17 is the human's call) but NARROWED with the measurement, so the executor knows the `low` case is currently empty. Recorded as F-9 |

BOTH OPEN FINDINGS ARE DEFERRED-AS-OPEN UNDER THE FIX BAR, and every element the Bar demands is stated.

PR-001 is overall Medium-High on FUNCTIONALITY: the axis is functionality because the wrong ordering
makes 18 already-approved plans unrunnable, and it reaches the threshold because the remedy is a
Set-level sequencing choice among three options with different costs, not an edit to this file. The
required decision is the maintainer's answer to the PARENT's OQ-02. The consequence of leaving it
unresolved is that this plan executes behind a gate that has already stranded the queue it was meant to
serve. It IS escalated here, as OQ-03, after the checker rejected the alternative: the answer is made
once at the parent and recorded in both places, so the maintainer decides one thing while both artifacts
refuse execution until they agree.

PR-002 is overall Medium-High on FUNCTIONALITY with a secondary usability axis: functionality because
the alternative to a workaround is code work in the shared status setter that intersects an open defect
(`x6tk1u`), and usability because a fabricated approval line is read by humans auditing a plan's
history. It reaches the threshold because the choice trades record cleanliness against Set completeness
and because option (c) would block this Set behind a new plan. The required decision is the maintainer's
choice among the three options. The consequence of leaving it unresolved is 5 plans carrying a
fabricated approval event, in the Set that exists to make plan metadata trustworthy.

Effort, time, cost and tokens played no part in either deferral.

Per the escalation rule BOTH open findings are raised in the plan as open questions carrying `- Blocking:
yes` and a `- Finding:` id (PR-002 as OQ-02, PR-001 as OQ-03), and the refusal was verified rather than
assumed: `aw ipd lint --phase review-finalize` exits 1 with `IPD-Q501` naming OQ-02 at line 167 and OQ-03
at line 181, so the plan cannot reach `approved` or `begin` until the maintainer answers. `aw check
plans` also returned to its 140-error baseline with no finding naming this file, confirming the
escalation is recorded in the shape the consistency rule expects.

ONE THING IS WORTH THE MAINTAINER'S ATTENTION BEYOND THE TWO QUESTIONS. The setter behavior PR-002
found is not specific to this plan: any agent doing a field-only write through `aw ipd set` on a
same-status artifact writes the same misleading line, and the backlog already carries its mirror image
(`x6tk1u`, where a same-status `--message` is DISCARDED on the backlog path). Those two are one design
question about what a no-op transition should record, currently answered differently on two paths.
Whatever OQ-02 decides for this plan, that question probably deserves its own carrier; review did not
file one, because filing work is the maintainer's call.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The setter writes a false history line. Work around it with `--message` on my own authority, or escalate? | ESCALATE as blocking OQ-02, while writing the `--message` workaround into E-03 so the plan is executable the moment it is answered. | (a) Mandating `--message` and calling it resolved, rejected because the line still leads with the plan's current status and an auditor could read `approved (aw set)` on an approved plan as a re-approval; whether that is honest enough is a judgement about the repository's own provenance standard, which is the maintainer's. (b) Prescribing the setter fix, rejected because it is code in `status_set` outside this plan's declared `Scope-Paths` and it intersects the open `x6tk1u`, whose preferred fix moves the opposite way. (c) Silently accepting the default line, rejected outright: it fabricates approval history in the Set that exists to make plan metadata trustworthy. | driven on `5e4sb6` in a throwaway copy, both with and without `--message`; backlog `x6tk1u` naming `status_set.apply_status_change` as the shared setter | yes |
| D-2 | The dependency edge is the parent's blocking defect. Edit it here, leave it silent, or escalate on this file too? | ESCALATE HERE AS OQ-03 while leaving the edge itself unedited, and word the question so the decision is made once at the parent. CORRECTED MID-REVIEW: the first choice was to inherit without escalating, and `check.review-finding-unescalated` rejected it. | (a) Rewriting `- Item-Dependencies:` to `none` myself, rejected because the parent's OQ-02 offers three options and two of them KEEP an edge in some form, so choosing here would pre-empt the maintainer and leave the parent's child table disagreeing with the child. (b) INHERITING WITHOUT ESCALATING, which is what I first did and what the checker overturned: the reasoning was that duplicating a blocking question asks the maintainer to answer twice, but the gate threshold is about which ARTIFACT refuses to execute, and the parent's refusal does not protect this child. The rule is right. (c) Deleting the false justification silently, rejected because it is the reasoning an executor would otherwise reuse to defend the edge; marking it corrected is what stops that. | parent `d0cbt3` OQ-02 with its three costed options; this plan's authored gate sentence; the parent's measured 18-plan stranding; `aw check plans` flagging `check.review-finding-unescalated` at 141 then returning to 140 | yes |
| D-3 | Should review test the setter, or trust its documented no-op persistence? | TEST IT, in a throwaway copy of the repo, on one plan of each status in the population. | Trusting the `--help` text, rejected because "persists on a no-op transition" describes the FIELD write and says nothing about what else the call does; the false history line is invisible from the documentation and was the review's most consequential finding. Testing against the real tree, rejected outright: it is a shared checkout and the write would have landed on a co-worker's plan; the copy was used and discarded. | the throwaway copy at `/tmp/opencode/pp`; diffs read for both `reviewed` and `approved`; real tree confirmed untouched by `git status` | yes |
| D-4 | The plan says "one plan at a time" without naming a selector. Is that enough? | NO. Mandate the id6 explicitly, prove the hazard, and require a dry-run preflight plus a terminal-directory emptiness check. | Leaving it implicit, rejected because a setid is the natural token when working through a Set and the consequence is measured, not theoretical: a dry-run reverts two `executed` plans, and `f5pttg` records the same command having done it to seven for real. Only warning in prose, rejected because `f5pttg`'s own analysis is that prose did not prevent it; the dry-run and the empty-terminal-status assertion are the mechanical guards. | the setid dry-run output; the 6-setid collision computed over the population; backlog `f5pttg` (`open`, high) | yes |
| D-5 | 11 plans already carry both fields. Overwrite them for uniformity, or exclude them? | EXCLUDE. Inheritance may fill a hole but must not replace an existing value. | Overwriting for consistency, rejected because an existing in-vocabulary value is evidence someone chose it, the overwrite would be invisible afterwards (both values are legal), and the plan's own principle is that a value must never be fabricated. Treating a plan with exactly ONE field as fully complete, also rejected: it is in scope for the missing field only, which E-01 now states so the case is not silently skipped. | 11 measured at review; the `xprio` no-fabrication rule cited in the plan's own conventions | yes |

Every decision above is `Reversible: yes`, so recording is sufficient and no escalation is owed beyond
the finding already escalated. None changes a published interface, migrates data, deletes anything, or
touches a released artifact; the two that could have (choosing the Set's ordering, changing the shared
status setter) are precisely the two left to the maintainer.

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
| PR-001 | BLOCKER | IN-SCOPE | G. Plan executability | the parent's OQ-02, now resolved; this plan's `- Item-Dependencies: executed:lkexaw` | Carried forward: THIS PLAN'S DEPENDENCY EDGE IS THE PARENT'S BLOCKING DEFECT, so it could not be settled here. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | RESOLVED BY RULING 1. The `executed:lkexaw` edge is INVERTED and must be removed: Order 01 now depends on THIS plan. OQ-03 is `resolved` and says so explicitly rather than leaving the executor to infer it. |
| PR-002 | BLOCKER | IN-SCOPE | A. Correctness and data integrity / F. Honest documentation | measured at round 1 on orchestrator `5lxvl3`: a same-status write appends a history line asserting a transition that did not happen | Carried forward: A SAME-STATUS WRITE FABRICATES A HISTORY LINE unless `--message` is passed, and the 5 approved plans were the exposed population. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | RESOLVED BY RULING 1's CONSEQUENCE. Running before the gate removes the stranding risk that made deferring the 5 approved plans attractive, so the concern reduces to writing a TRUTHFUL `--message` (fields backfilled by inheritance from the named source item, never wording that asserts a lifecycle transition). OQ-02 now records that, and that the 5 must NOT be deferred. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the 5 approved plans still be deferred, as round 1 offered? | NO. Backfill them, with a truthful `--message`. | Defer them to a later child (rejected: deferral was only necessary because the gate was landing first, and Ruling 1 removes that; deferring would leave 5 approved plans without values for no remaining reason). | Ruling 1; round 1's own measurement that the risk came from gate ordering rather than from the write itself. | yes |
