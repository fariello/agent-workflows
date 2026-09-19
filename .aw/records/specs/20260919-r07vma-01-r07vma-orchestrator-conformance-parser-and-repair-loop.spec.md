# Spec: Orchestrator conformance: one parser, review-time repair, run-time refusal

- Date: 2026-09-19
- Status: reviewed
- Id: r07vma
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Spec: 77tr3o
- Scope: An Order-0 orchestrator may hold only child-tracking items; one shared parser enforces AUTHORING CONFORMANCE deterministically, plan-review repairs violations in a bounded loop, and a run re-parses and refuses with every finding at once. ADDITIVE to the existing semantic coverage probe, which it does not replace.
- Parent: `.aw/records/specs/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md` (`77tr3o`,
  `approved`), which owns runner-owned retirement. This spec ADDS a deterministic authoring-conformance
  control beside that spec's R-12 semantic probe. It leaves R-1 through R-12 intact and does NOT retire
  the probe; see SR-001 and Section 3.
- Constrained-by: `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`
  (`25kzda`, `approved`) Section 2.5b, which owns the coverage gate's MECHANISM and states that the check
  is semantic, that a syntactic rule MUST NOT be added in its place, and why. This spec is written to be
  compatible with that prohibition rather than to amend it: it adds a conformance check with a different
  question, and does not substitute a syntactic rule for the semantic one.

## Workflow history
- 2026-09-19 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; SR-001..SR-006, all six FIXED, none deferred, none open. SR-001 was a BLOCKER the draft did not see: it proposed RETIRING the semantic coverage probe and replacing it with a syntactic parser, but approved spec 25kzda 2.5b states the check is SEMANTIC and that 'A syntactic rule MUST NOT be added in its place', and the draft did not cite 2.5b at all. The prohibition's prediction was TESTED rather than accepted on authority and it held: a child-reference signal PASSES rh5tt6 E-02 (the actual production failure, which name-drops 16 children while being pure parent-only work) and a confession-phrase signal catches only 2 of 5 sampled violators, so the substitution would have narrowed real coverage while deleting 476 lines of shipped code and 1265 lines of tests merged the same day. The parser is now ADDITIVE and ordered parser-then-probe. Also FIXED: a missing honest-limits section (SR-002, now five numbered limits including that a clean parse is NOT evidence of coverage), a cost count already stale within hours (SR-003, ten -> eleven pending orchestrators, re-measured with the shape that must survive), three missing acceptance criteria covering the two controls' coexistence, distinguishability and ordering (SR-004), OQ-03 resolved from repository evidence rather than left open (SR-005, decision SR-D1), and a scope line that claimed the probe's territory (SR-006). Two decisions recorded, both reversible. Verified every draft measurement against shipped source: evaluate_set_retirement has zero E-/V-/checklist references, rh5tt6's retirement commit says its items were NOT performed, the 2026-09-06 Readiness incident and IPD-M107 are as described. DISCLOSURE: same agent and model authored this spec earlier in the session, so claims were verified against source and the uncited governing spec was sought out rather than the prose re-read.

- 2026-09-19 to-review (aw specs): Drafted from a maintainer design conversation after a live run refused tb63qv on its single E-item. Establishes that an Order-0 orchestrator may hold only child-tracking items, because retirement is programmatic and skips the E/V checkpoint, so a parent item needing an agent can never be performed (measured: evaluate_set_retirement contains zero references to E-/V-/items/checklist; rh5tt6 was retired 2026-09-08 with its own commit message saying its items were NOT performed). REPLACES 77tr3o R-12's model probe with one shared parser called by both plan-review and the run. The maintainer rejected a new front-matter attestation field: a gate-read field written by the authoring agent is the shape - Readiness: already proved unreliable, and the 2026-09-06 incident was pattern-completion rather than deception, so the fix is to not create the blank. Two open questions recorded rather than settled: how to keep authoring instructions from drifting from the enforcing code, and whether the checklist should become a typed structure.
## 1. The problem, and what the existing control does not reach

An Order-0 orchestrator IPD is retired PROGRAMMATICALLY. `runner_shared.evaluate_set_retirement` decides
eligibility from four facts: an orchestrator exists, the Set has at least one child, every child's
`- Status:` is exactly `executed`, and no child-table row resolves to nothing. It then retires the parent
with no agent turn, deliberately SKIPPING the pre-transition `E-*`/`V-*` checkpoint that every child
must pass (`77tr3o` R-5, shape (b)).

Measured while drafting this spec: `evaluate_set_retirement` contains ZERO references to `E-`, `V-`,
`items`, `checklist`, `execution state`, `lint`, or `checkpoint`. It never opens the parent's checklist.
That is not an oversight; it follows from R-5's premise that a parent's items are performed by nobody.

The consequence is arithmetic rather than policy: an orchestrator item that requires an AGENT to do
something can never be performed, because no agent turn exists in which to perform it. It is marked
complete having never run. Production confirmed this on 2026-09-08, when `aw oc run` retired `rh5tt6`
with a commit message that says outright "Its own `E-*`/`V-*` items were NOT performed", while its E-02
still read `Execution state: pending` and its V-02 was blank.

`77tr3o` R-12 addressed that by asking a MODEL, once per queued orchestrator before any agent turn,
whether the parent carries work no child covers. That gate works, has already refused a real run, and is
the right control for the case it targets: work stated in PROSE, which no parser can see.

WHAT IT DOES NOT DO, and this is the gap this spec fills rather than a defect in the probe:

1. IT CANNOT REPAIR. The refusal lands at run start, where editing another agent's plan is exactly what
   a run must not do. The operator is told to fix something by hand, having already queued a run. Nothing
   in the pipeline offers to fix the violation at the one point that is licensed to rewrite a plan, which
   is review.
2. IT SPENDS A MODEL CALL FOR THE TIDY CASE TOO. An orchestrator whose violation is plainly visible in
   its checklist costs the same probe as one whose violation is buried in prose.
3. IT HAS AN AVAILABILITY FAILURE MODE. A `could-not-ask` proceeds with a warning and a recorded hole.
   That is the correct call for an outage, and it means the probe alone leaves a known gap on the days it
   cannot be reached; a deterministic check has no such day.

THE DRAFT OF THIS SPEC MISREAD THAT LIST AS A CASE FOR REPLACEMENT, and review corrected it. `25kzda`
2.5b, approved, states that the check is semantic and that a syntactic rule MUST NOT be substituted, with
a measured reason. So this spec adds a control and retires nothing. Section 3 records the correction and
the measurements that settled it.

The maintainer's framing, which is the load-bearing observation and is recorded here because it explains
the whole design: the orchestrator exists to help an AGENT run a complex Set with fewer errors, by
mitigating context limits and length-of-execution drift. Under a runner that reason does not hold, since
the runner already sequences children, isolates each one, and gives each a fresh context-bearing
session. So under a runner the parent's checklist is redundant instrumentation, and having an agent
"run" the orchestrator up front makes outcomes worse rather than better.

## 2. What is actually being enforced

R1 (THE INVARIANT). An Order-0 orchestrator's `E-*` and `V-*` items may contain only CHILD-TRACKING
work: confirming, sequencing, tracking, or verifying the state of named children. They may not contain
work an agent must perform: producing a deliverable, establishing a baseline before any child runs,
running a suite or a proof, or reconciling records afterwards.

R2 (THE CHECKLIST STAYS). R1 is not "a parent has no items". The checklist is what makes a Set execute
completely and in order when a human or agent runs it BY HAND with no runner involved, which is how many
Sets are run. Deleting it causes the lost or partial work the invariant exists to prevent. Every plan
carrying `- Kind: orchestrator` is expected to carry checklist items.

R3 (ONE IMPLEMENTATION, TWO CONSUMERS). The conformance rule is ONE function. `/plan-review` calls it to
decide whether a plan may be cleared, and a run calls the SAME function to decide whether to proceed.
There is no second implementation, no digest shortcut standing in for the check, and no "cheap version"
at one consumer. This is the pattern `check_engine.evaluate_blocking_close` already establishes, where
one predicate backs a setter, three `aw check` rules, and a pre-commit hook.

R4 (NO NEW FRONT-MATTER FIELD). Conformance is NOT recorded as its own metadata field. `- Readiness:`
already means "a review ran and reached a verdict", and conformance is part of what a review checks. A
second field asserting a subset of the same fact would be two fields that can disagree.

R5 (REVIEW REPAIRS, IN A BOUNDED LOOP). When the parser reports a violation during `/plan-review`, the
review asks the agent to fix it and re-runs the parser, up to a configurable number of attempts
(default 2). `/plan-review` already applies in-place revisions and already re-runs `aw ipd lint --phase
review-finalize` after them, so this is one more rule at a checkpoint that already exists.

R6 (EXHAUSTION IS HONEST). If the attempts are exhausted with the violation unresolved, the plan stays
`to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Not
`no-go`: that is a verdict the review did not reach. Each attempt is logged, so an agent that "fixed" it
by deleting the checklist is visible in the record rather than hidden behind a passing later round.

R7 (THE REFUSAL STATES THE INVARIANT AND LEAVES THE REMEDY OPEN). The message must say what is wrong and
why, must explicitly forbid satisfying it by deletion, and must name BOTH legitimate remedies: move the
step to a child with dependencies that put it in the right order, or remove it because it is redundant.
It must not prescribe one. The reasoning is that an agent trusted to author the plan is trusted to judge
which remedy fits; and a prohibition-only message gets complied with by deleting the checklist, which is
the failure R2 exists to prevent.

R8 (THE RUN SCANS, AND REPORTS EVERYTHING BEFORE EXITING). A run re-runs the parser over every queued
orchestrator before spending anything, collects ALL findings across ALL orchestrators, reports them
together, and then refuses. It does not stop at the first violation. The maintainer's stated requirement
is that a fix-one-then-rediscover-the-next cycle is the worst possible operator experience.

R9 (THE RUN'S CHECK IS DETERMINISTIC, AND THE MODEL PROBE IS RETAINED BESIDE IT). The parser-based
run-time check spends no tokens and has no availability failure mode. It does NOT replace the model
probe, and this spec does not retire that probe. See Section 3's "why the probe is retained" paragraph
and SR-001: an approved spec (`25kzda` 2.5b) states that the coverage check is SEMANTIC, that a
syntactic rule MUST NOT be added in its place, and gives the measured reason. This spec is therefore
scoped to a DIFFERENT and narrower question than the probe's, and the two coexist:

- THE PARSER answers "does this orchestrator's checklist conform to the authoring rules?" It is
  deterministic, catches the tidy violation, and is the thing review can repair in a loop.
- THE PROBE answers "does this orchestrator carry work no child covers, including work stated only in
  prose?" It is semantic, catches the harmful violation a parser cannot see, and blocks unattended.

Neither subsumes the other, and the ordering is parser first (free, and repairable at review) then
probe (costly, and the backstop for prose). A run that the parser refuses never reaches the probe, so
the common case still spends nothing.

## 3. Why this shape, rather than the alternatives considered

This section records the reasoning, not a prohibition on revisiting it. Each choice below was made
against the information available on 2026-09-19 and could reasonably be revisited if that information
changes; where a choice rests on a measurement, the measurement is named so a future reader can re-take
it rather than argue from the prose.

WHY THE CHECK RUNS AT REVIEW AND ALSO AT RUN START, rather than at one of them. Review is the only place
already licensed to rewrite a plan, so it is the only place a violation can be FIXED rather than merely
reported; a run editing another agent's plan mid-flight is exactly what the shared-checkout rule
forbids. But review is agent-run, so its verdict asserts a check the same agent performed. The run-time
scan is what makes that independent. Neither alone is satisfying: review-only trusts a self-report, and
run-only leaves the operator holding a refusal they must fix by hand before re-running. If the review
pipeline later gains independent verification, the run-time scan becomes belt-and-braces rather than
load-bearing, and dropping it would be a reasonable simplification at that point.

WHY A PARSER IN ADDITION TO A MODEL, given that a parser cannot be complete. A textual rule cannot reliably
distinguish "verify the Set's combined outcome" (agent work) from "verify child X reached executed"
(tracking) in every phrasing, and this spec does not claim otherwise. Two things make the parser worth
ADDING anyway. First, its failure direction is safe: a false refusal leaves the plan in `pending/`, which
is the status quo, whereas a false pass loses work silently and is what `rh5tt6` measured. Second, R5
changes what a false refusal COSTS: with an agent asked to fix and re-check, an over-strict parser
produces a revision rather than a dead end, so strictness is cheap in a way it would not be if the
parser were the last word. That second reason is the one that made a tight vocabulary acceptable to the
maintainer, having been reluctant about it earlier in the same conversation.

AND THE PARSER IS EXPLICITLY NOT THE LAST WORD, which is what keeps it compatible with `25kzda` 2.5b's
prohibition. That section forbids substituting a syntactic rule for the semantic check, on the measured
grounds that false positives would drive agents to delete the child checklist. The prohibition is against
REPLACEMENT. A parser that runs FIRST, whose refusal is routed to a repair loop that names both remedies
and forbids deletion (R7), and behind which the semantic probe still runs, does not substitute for
anything. An implementer who finds themselves removing the probe has left this spec's scope.

WHY NO ATTESTATION FIELD, and the affordance argument behind it. An earlier draft of this design carried
a "this orchestrator passed conformance on this date" field plus a content digest, so a run could check
the stamp cheaply instead of re-parsing. It was dropped for two reasons. The mechanical one: a field a
gate reads, written by the agent authoring the file, is the shape `- Readiness:` already demonstrated to
be unreliable. Measured 2026-09-06, an agent authoring a four-plan Set wrote `Readiness:
go-pending-approval` into all four having run no review, and the auto-approve predicate returned True
for every one, which is why `aw ipd scaffold` omits the field and `ipd_lint` refuses an unattested value
(`IPD-M107`). THE READING THAT MATTERS IS NOT DECEPTION: that agent was completing a pattern it saw in a
template, which is what authoring metadata looks like. A blank in the front matter is a blank an author
fills in. So the durable fix is not to guard the field but to not create it. The second reason is scope:
the front matter is already large, and `tmp/notes.md` item 3 records an open question about moving
`aw`-specific metadata out of the `.md` files entirely; adding a field now would add to the surface that
question is about. A pleasant side effect is migration safety, since a rule keyed on the checklist and
child table (prose that agents genuinely read) survives a metadata move that a rule keyed on a new field
would not.

THE COST OF DROPPING THE DIGEST, stated rather than hidden: the run re-parses instead of comparing a
hash. That is an in-process parse of the queued orchestrators (order of ten files on this repository
today), against a run that spends dollars and hours, so the cost is not material. If the orchestrator
population grew by orders of magnitude the trade would be worth re-examining.

WHY THE REMEDY IS NOT PRESCRIBED. An earlier draft said the refusal should tell the agent to ADD A
CHILD. That is sometimes wrong: `rh5tt6` E-02 is the worked example, and it welds together a genuinely
redundant half (re-run the suite and leak sanitization, which every child already does and which the
pre-commit hook enforces on every commit) and a genuinely uncovered half (an end-to-end install proof in
a temporary target repo, which the plan itself calls "the part no child owns"). The correct repair is
DELETE for the first and a CHILD for the second. A message prescribing one remedy would have produced a
pointless child plan for work already done four times over.

WHY TWO ATTEMPTS BY DEFAULT. It matches `runner_shared.resolve_retry_budget`, which implements spec
2.1's `CLI > repository policy > default 2` precedence, so the knob follows an existing precedent rather
than inventing a number. Note that resolver's middle tier is NOT implemented today (backlog `dh3us4`
tracks a repository-policy home), so a configurable default here will face the same gap and should not
pretend otherwise.

WHY THE MODEL PROBE IS RETAINED, CORRECTING THIS SPEC'S FIRST DRAFT. The draft proposed retiring the
probe, on the reasoning that two mechanisms answering one question eventually disagree and that a
fail-open backstop contributes nothing to an absolute rule. That reasoning was wrong on its premise,
and the correction is the most important thing this spec learned at review.

THE TWO MECHANISMS DO NOT ANSWER ONE QUESTION. A parser can only see syntax. Spec `25kzda` 2.5b states
the decisive case plainly: the dangerous violation is stated in PROSE ("the database must be migrated
before the children run"), which matches no checklist syntax, "so a syntactic rule catches only the tidy
mistake and misses the harmful one". It goes further and forbids the substitution outright: "A syntactic
rule MUST NOT be added in its place", because `77tr3o` R-5's resolution forbids teaching the linter
about `Kind`, and because a syntactic rule's false positives "would teach agents to DELETE the child
checklist that makes `execute <setid>` complete with no runner involved" - which is R2's whole concern,
arriving from the direction this spec did not expect.

THAT PREDICTION WAS TESTED AT REVIEW AND HELD. The candidate deterministic signals were measured
against the live corpus and each missed real violations. A reference test (does the item name a child
id6?) passes `rh5tt6` E-02, the actual production failure, because it name-drops sixteen children while
being pure parent-only work. A confession-phrase test ("no child owns/covers/can") catches `s0gnha` and
`wfjsp4` but misses `5e4sb6`, `tb63qv` and `a5wdne`, which carry parent-only work in ordinary prose: 2
of 5 on a sample this spec already had in hand. So the parser's recall on the harmful case is
demonstrably partial, and retiring the semantic check would have narrowed coverage while claiming to
harden it.

WHAT THE PARSER IS STILL FOR, given that. It is cheap, it is deterministic, it runs at REVIEW where a
violation can be repaired rather than merely reported, and a false refusal there costs a revision
instead of a dead end (R5). That is a real contribution to a real problem; it is just not a replacement
for the semantic check. The honest framing is defense in depth with distinct coverage, not one mechanism
superseding another.

THE COST OF HAVING BEEN WRONG HERE IS WORTH RECORDING, because it is the argument for reading the
governing spec before proposing to replace its mechanism: the draft would have deleted 476 lines of
shipped code across seven functions and 1265 lines of tests, merged the same day, and contradicted an
approved spec's explicit prohibition. Nothing in the draft's reasoning was sufficient to justify that,
and the draft did not cite 2.5b at all.

THE PROBE'S SUPPORTING MACHINERY IS ALSO WHAT THIS SPEC BUILDS ON rather than salvages: its bounded
payload, its cache keyed on exactly the inputs it reasons over, and its collect-all-then-partition
structure. R8's batch reporting is that structure generalized across check kinds.

WHAT IS GENUINELY UNRESOLVED, flagged rather than papered over. The maintainer raised, and this spec does
not settle, how to keep the ENFORCEMENT CODE and the AUTHORING INSTRUCTIONS from drifting apart: a
vocabulary and structure the parser enforces must also be documented for the agent writing a Set, and
two hand-maintained statements of one rule drift. OQ-01 carries a proposed direction (generate the
instructions from the rule) rather than a decision.

## 3a. Honest limits: what this spec does NOT prove

Stated explicitly because the draft claimed more than it delivers, and a spec that oversells is worse
than one with a narrow scope.

1. A CLEAN PARSER RESULT IS NOT EVIDENCE THAT AN ORCHESTRATOR CARRIES NO UNCOVERED WORK. It is evidence
   that the checklist conforms to the authoring rules. The prose case is out of a parser's reach by
   construction (`25kzda` 2.5b), which is why the semantic probe is retained rather than replaced.
2. THE PARSER'S RECALL IS NOT QUANTIFIED. Two candidate signals were measured on a five-plan sample at
   review and both missed real violations. An implementer should measure recall on the live corpus and
   RECORD it, so the residue is known rather than assumed.
3. REVIEW-TIME REPAIR IS AGENT-PERFORMED AND SELF-ASSESSED. R5/R6 bound and log it; they do not make it
   independent. The run-time consumer is what provides independence, and it re-parses rather than trusting
   the review's verdict.
4. NOTHING HERE PREVENTS A DELIBERATELY CONCEALED DELIVERABLE. An author intent on hiding agent work in
   an orchestrator can phrase it to pass both a parser and, plausibly, a probe. The controls raise the
   cost of the ACCIDENTAL violation, which is the measured failure mode (`rh5tt6`, and the 2026-09-06
   `Readiness` incident, were both pattern-completion rather than deception).
5. THIS SPEC DOES NOT ESTABLISH THAT A PARSER IS SUFFICIENT. It establishes that a parser is a cheap,
   repairable first line. If measurement later shows its recall is negligible on real violations, dropping
   it and keeping only the probe would be a reasonable response to that evidence.

## 4. Non-goals

- Changing `evaluate_set_retirement`'s four eligibility facts, or R-5's choice of a rollup that skips the
  E/V checkpoint. This spec makes R-5's premise TRUE rather than relaxing the shape it chose.
- Teaching `ipd_lint` to be `Kind`-aware in the sense `77tr3o` OQ-1 rejected as shape (a). The
  conformance rule is its own function; whether `ipd_lint` CALLS it is an implementation question for the
  graduating plan, but the honesty checker gains no orchestrator special case.
- Backfilling the orchestrators that carry this debt today. `77tr3o` Section 4 already places that out of
  scope and states the honest consequence, which this spec inherits: see Section 6.
- Moving `aw`-specific metadata out of the `.md` files (`tmp/notes.md` item 3). Named here only because
  R4's reasoning touches it.
- Deciding whether the orchestrator checklist should become a TYPED child-tracking table rather than
  prose with an enforced vocabulary. See OQ-02.

## 5. Accepted costs

1. THE PARSER WILL FALSE-REFUSE. An unusual but legitimate phrasing will be flagged. R5 is what makes
   this tolerable rather than obstructive, and R6 is what keeps an exhausted loop honest instead of
   silently passing.
2. TWO CONSUMERS MEANS THE CHECK RUNS TWICE. Deliberate, per Section 3's first paragraph. The cost is a
   second parse, not a second rule.
3. THE EXISTING PENDING ORCHESTRATORS WILL REFUSE OR NEED REWORDING. Measured during the design
   conversation: of ten pending `Kind: orchestrator` plans, seven were classified as carrying at least
   one parent-only item. RE-MEASURED AT REVIEW, and the population moved WITHIN HOURS, which is why this
   is a dated snapshot and not a fixture: there are now ELEVEN (`7ewc74` left by being finalized;
   `2xz59a` and `s0gnha` arrived). The SHAPE is what must survive re-measurement - a majority of live
   orchestrators carry at least one parent-only item - and it did. An implementer must re-derive the
   count and report the denominator. A date cutover (the `check_engine.CARRIER_CUTOVER_DATE` pattern) can
   make this gradual, which is the implementing plan's decision to make.
4. REVIEW STILL ASSERTS A CHECK THE SAME AGENT PERFORMED. R8 mitigates rather than eliminates this. It is
   a property of the whole review pipeline, not something introduced here.
5. THE PARSER'S RECALL ON THE HARMFUL CASE IS PARTIAL AND UNQUANTIFIED. Measured at review on a
   five-plan sample, a confession-phrase signal caught 2 of 5 and a child-reference signal passed the
   known production failure outright (Section 3). This spec therefore does NOT claim the parser detects
   parent-only work in general; it claims the parser enforces AUTHORING CONFORMANCE deterministically and
   repairs it at review, while the semantic probe remains the control for the prose case. A consumer must
   not read a clean parser result as evidence that an orchestrator carries no uncovered work.

## 6. Acceptance criteria

Each criterion states a SHAPE plus the evidence that satisfies it. Counts in this spec are dated
snapshots of a moving corpus; an implementer must RE-DERIVE them and report the denominator rather than
quoting this document.

1. ONE function decides conformance, and both consumers call it. Evidence: the function, and both call
   sites, with a grep showing no second implementation of the rule.
2. A conforming orchestrator passes at both consumers; one carrying a parent-only item fails at both.
   Evidence: a fixture of each, plus a MUTATION check (break the rule, show the pin fails, restore).
3. The refusal text states the invariant, forbids satisfying it by deletion, and names both remedies
   without prescribing one. Evidence: the rendered message.
4. `/plan-review` repairs a violating orchestrator within the attempt budget and the repaired plan
   passes. Evidence: the before and after checklists plus the round record.
5. An exhausted loop leaves the plan `to-review` with `- Readiness:` ABSENT and the attempts logged.
   Evidence: the plan's front matter and the round record after a deliberately unfixable case.
6. A run reports EVERY finding across EVERY queued orchestrator in one pass, then refuses. Evidence: a
   multi-violation queue's output showing all findings before the exit.
7. The model probe STILL RUNS and still blocks, and the parser did not displace it. Evidence: a queued
   orchestrator carrying parent-only work stated only in PROSE (no matching checklist syntax) is still
   refused after this change, plus `tests/test_orchestrator_probe.py` passing UNEDITED, plus `grep`
   showing the probe's seven functions intact. This criterion inverts the draft's criterion 7 and is the
   pin for SR-001.
8. The parser's REFUSAL and the probe's REFUSAL are distinguishable to an operator, so a human reading a
   refused run knows which control fired and therefore which remedy applies. Evidence: both messages,
   side by side, naming different rule ids.
9. The ordering is parser-then-probe, and a parser refusal spends no model call. Evidence: a run refused
   by the parser showing zero probe invocations (an empty probe event stream or an equivalent assertion).
10. The full suite passes and `aw check all` is no worse than its pre-change baseline, both counts pasted.

## 7. Open questions

### OQ-01: How should the authoring instructions be kept from drifting away from the enforcing code?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because the conformance rule and its two consumers can
  be built and tested before this is settled; an implementer would simply hand-write the instructions and
  inherit the drift risk. It matters because a rule the parser enforces must also be documented for the
  agent AUTHORING a Set, and two hand-maintained statements of one rule diverge, which is the failure
  this whole spec is a response to at a different level. PROPOSED DIRECTION, not a decision: keep the
  vocabulary and prohibitions as DATA in the rule module, and render the refusal message, the `aw ipd
  scaffold` guidance, and the documentation from that one source, so the instructions cannot disagree with
  the check. The alternative (prose beside code, kept in step by discipline) is what the repository does
  today for most rules and is honestly workable; it just has a known decay mode.

### OQ-02: Should the orchestrator checklist stay prose with an enforced vocabulary, or become a typed child-tracking structure?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking: R1 through R9 are expressible either way, and the
  prose-with-vocabulary route is the smaller change and the one this spec is written against. The
  question is worth recording because the two routes converge: a vocabulary and structure strict enough
  to parse reliably IS most of a typed table, at which point the vocabulary rules become redundant
  scaffolding around it. A typed structure would also make R1 true BY CONSTRUCTION (there would be
  nowhere to park a deliverable) rather than by detection, which is the stronger guarantee. Against it:
  it is a bigger migration for the existing orchestrators, it makes the hand-run path (R2's reason for
  keeping the checklist) less readable to a human, and it is harder to extend when a Set needs to say
  something the schema did not anticipate. Deferred rather than answered because the maintainer leaned
  toward the prose route once R5 made strictness cheap, and that lean should be tested by building it
  before committing to a schema.

### OQ-03: Does the conformance rule apply to an orchestrator a runner will never queue?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM REPOSITORY EVIDENCE as APPLY UNIFORMLY, and
  recorded as review decision SR-D1 (reversible). The question is real: R1's justification is mechanical
  and specific to the runner's retirement path, and `77tr3o`'s own Scope states it "does NOT change the
  agent-driven path (a human or agent running a Set by hand still executes the orchestrator's own
  `E-*`/`V-*` items)". So an orchestrator that will only ever be hand-run is genuinely not exposed to the
  failure R1 prevents.
  WHAT SETTLES IT is that the exemption is not expressible. Nothing in the plan schema marks a Set as
  hand-run-only, a Set's execution route is chosen at run time and not at authoring time, and the same
  plan is routinely run both ways (this repository's Sets are run by `aw oc run` and by hand). A rule
  conditioned on an unknowable future property would therefore have to guess, and guessing wrong in the
  permissive direction reintroduces exactly the silent loss `rh5tt6` measured.
  THE ACCEPTED COST, stated rather than hidden: a Set that will only ever be hand-run loses the ability
  to put a whole-Set step on its parent, and must put it in a final child instead. That is a small
  authoring inconvenience with a mechanical remedy (R7's first option), weighed against a failure mode
  that is silent and has occurred in production. REVISIT IF a durable marker for execution route is ever
  introduced, at which point a conditional rule becomes expressible and this trade can be re-taken.
