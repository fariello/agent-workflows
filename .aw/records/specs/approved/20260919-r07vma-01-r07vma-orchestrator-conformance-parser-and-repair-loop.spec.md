# Spec: Orchestrator conformance: a typed child-tracking checklist, review-time repair, run-time refusal

- Date: 2026-09-19
- Status: approved
- Id: r07vma
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Spec: 77tr3o
- Scope: An Order-0 orchestrator may hold only child-tracking items; one shared parser enforces AUTHORING CONFORMANCE deterministically, plan-review repairs violations in a bounded loop, and a run re-parses and refuses with every finding at once. ADDITIVE to the existing semantic coverage probe, which it does not replace.
- Parent: `.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md` (`77tr3o`,
  `approved`), which owns runner-owned retirement. This spec ADDS a deterministic authoring-conformance
  control beside that spec's R-12 semantic probe. It leaves R-1 through R-12 intact and does NOT retire
  the probe; see SR-001 and Section 3.
- Constrained-by: `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`
  (`25kzda`, `approved`) Section 2.5b, which owns the coverage gate's MECHANISM and states that the check
  is semantic, that a syntactic rule MUST NOT be added in its place, and why. This spec is written to be
  compatible with that prohibition rather than to amend it: it adds a conformance check with a different
  question, and does not substitute a syntactic rule for the semantic one.

## Workflow history

- 2026-09-19 approved (aw specs, --by-human): APPROVED by the human maintainer (Gabriele Fariello) 2026-09-19, recorded by the agent at their explicit instruction in session. Approval covers the design as hardened through two review rounds: R1a's typed child-tracking row as the enforcement mechanism (chosen over a prose vocabulary after the maintainer resolved OQ-02 as TYPED), R1b's rule that a cross-child check is a final child with sibling dependencies, the bounded review-time repair loop with honest exhaustion, the batch-report-then-refuse run gate, and the RETENTION of the semantic coverage probe beside the new control per 25kzda 2.5b. The maintainer is on notice of the principal cost: ZERO of 32 live orchestrator rows conform to the new grammar, so every one of the 11 pending orchestrators needs its checklist rewritten, and the migration route is the implementing plan's to choose under acceptance criterion 12. OQ-01 (keeping authoring instructions from drifting from the enforcing code) remains open and non-blocking.
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
4. IT LEAVES THE AUTHORING SURFACE UNCHANGED, so the violation stays EXPRESSIBLE and the probe's job is to
   notice it afterwards. The deeper fix is to make a deliverable unwriteable in a checklist row at all,
   which is what R1a does and which no detector of any kind can achieve.

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

R1a (THE INVARIANT IS ENFORCED BY SHAPE, NOT BY WORDING). An orchestrator's checklist item is a TYPED
CHILD-TRACKING ROW, not free prose whose verbs are policed. Each `E-*` item names exactly one child of
its own Set and the on-disk status that child must reach, in a form a parser reads deterministically:

    - [ ] E-NN CONFIRM <child-id6> REACHED <status>
      - Depends on: <E-NN | none>
      - Expected outcome: <child-id6> reads `- Status: <status>` on disk.
      - Execution state: pending

THE THREE TYPED FIELDS ARE `<child-id6>`, `<status>`, AND THE `Depends on:` EDGE. A conforming item
supplies all three, its `<child-id6>` resolves to a row of this orchestrator's own child table, and its
`<status>` is a member of the plan status vocabulary. Free prose MAY follow on continuation lines as
human-readable context, and is NOT parsed; it may not introduce a second obligation (see R1b).

WHY SHAPE RATHER THAN VOCABULARY, since the draft of this spec proposed the opposite. A vocabulary rule
polices HOW an item is worded and therefore always has a recall question and a false-positive rate: the
measurement at review round 1 put a leading-verb allowlist at 11 flags of 32 items, catching every known
violator but also flagging `ao1rb7` E-01/E-02, which are legitimate sequencing worded as "EXECUTE THE
CHILDREN IN ORDER". A shape rule has neither property: an item either supplies the three typed fields or
it does not, and a deliverable has nowhere to be expressed. R1 becomes true BY CONSTRUCTION rather than
by detection, which is the stronger guarantee and the reason this spec changed direction at review round
2. The cost is a migration (Section 5 cost 3) and a less discursive hand-run checklist (R2).

R1b (A CROSS-CHILD CONDITION IS A FINAL CHILD, NOT A RICHER PARENT ROW). When a Set needs a check that no
single child can perform - the merged result of several children, a constant unchanged across all of
them, a whole-Set measurement - that check is a CHILD plan whose `- Item-Dependencies:` name every
sibling it must follow. It is NOT an extra clause on a parent row, and the typed shape deliberately
gives it nowhere to live.

THIS IS NOT A THEORETICAL REMEDY; IT IS THE PATTERN ALREADY IN USE. Measured 2026-09-19: Set `reaskscore`
carries child 04 `svacmz`, whose child-table row states it "OWNS THE VERIFICATION E-02 AND E-03 DESCRIBE,
so it is performed and verified by an agent turn instead of being retired unperformed", with
`- Item-Dependencies: executed:skn8uk, executed:ty7w6o, executed:dy9ymn`. That Set's author reached this
conclusion independently and applied it before this spec was written, which is the best available evidence
that the remedy is natural rather than imposed.

AND THE OBJECTION TO A TYPED SHAPE WAS MEASURED AND DID NOT SURVIVE. Review round 1 argued that some
parent rows carry conditions a typed row cannot express, and named three. All three failed on
examination: `y9s4vm` E-02's condition (the child consumed the existing `discover_specs`) is asserted by
child `iuxtjy`'s own Scope and three of its V-items; `lyo1tz` E-02's (the import count fell, with the
residual set matching) is asserted seven times by child `1f7xno`; and `s0gnha` E-02's (five shared
constants unchanged on the merged result) had ALREADY been moved into child `svacmz`. Two were
duplication this spec should reject, and the third was the R1b remedy in the wild. No counter-example was
found in 32 items across 11 orchestrators, so the expressiveness objection is withdrawn rather than
accommodated.

R2 (THE CHECKLIST STAYS). R1 is not "a parent has no items". The checklist is what makes a Set execute
completely and in order when a human or agent runs it BY HAND with no runner involved, which is how many
Sets are run. Deleting it causes the lost or partial work the invariant exists to prevent. Every plan
carrying `- Kind: orchestrator` is expected to carry checklist items.

R2a (THE TYPED ROW MUST STILL SERVE THE HAND-RUN READER). R2's reason for keeping the checklist is that a
human or agent executes the Set from it. A typed row is terser than prose, so it must remain sufficient
for that: the row names the child, the required status, and its ordering edge, which is exactly what a
hand-runner needs to execute the Set in order. Where a Set genuinely needs narrative for the hand-run
path, it goes in the continuation lines (R1a) or in the orchestrator's own prose sections, NOT in a way
that adds an obligation to the row.

R3 (ONE IMPLEMENTATION, TWO CONSUMERS). The conformance rule is ONE function. `/plan-review` calls it to
decide whether a plan may be cleared, and a run calls the SAME function to decide whether to proceed.
There is no second implementation, no digest shortcut standing in for the check, and no "cheap version"
at one consumer. This is the pattern `check_engine.evaluate_blocking_close` already establishes, where
one predicate backs a setter, three `aw check` rules, and a pre-commit hook.

R4 (NO NEW FRONT-MATTER FIELD). Conformance is NOT recorded as its own metadata field. `- Readiness:`
already means "a review ran and reached a verdict", and conformance is part of what a review checks. A
second field asserting a subset of the same fact would be two fields that can disagree.

R5 (REVIEW REPAIRS, IN A BOUNDED LOOP). When the shape check reports a violation during `/plan-review`,
the review asks the agent to fix it and re-runs the check, up to a configurable number of attempts
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

R8 (THE RUN SCANS, AND REPORTS EVERYTHING BEFORE EXITING). A run re-runs the shape check over every queued
orchestrator before spending anything, collects ALL findings across ALL orchestrators, reports them
together, and then refuses. It does not stop at the first violation. The maintainer's stated requirement
is that a fix-one-then-rediscover-the-next cycle is the worst possible operator experience.

R9 (THE RUN'S CHECK IS DETERMINISTIC, AND THE MODEL PROBE IS RETAINED BESIDE IT). The parser-based
run-time check spends no tokens and has no availability failure mode. It does NOT replace the model
probe, and this spec does not retire that probe. See Section 3's "why the probe is retained" paragraph
and SR-001: an approved spec (`25kzda` 2.5b) states that the coverage check is SEMANTIC, that a
syntactic rule MUST NOT be added in its place, and gives the measured reason. This spec is therefore
scoped to a DIFFERENT and narrower question than the probe's, and the two coexist:

- THE SHAPE CHECK answers "is every checklist row a well-formed typed child-tracking row whose child
  resolves and whose status is legal?" It is deterministic with no recall question, because it validates
  STRUCTURE rather than judging wording, and it is the thing review can repair in a loop.
- THE PROBE answers "does this orchestrator carry work no child covers, including work stated only in
  prose?" It is semantic, and it remains the control for the continuation lines and the orchestrator's
  prose sections, which R1a explicitly does NOT parse.

Neither subsumes the other, and the ordering is shape check first (free, and repairable at review) then
probe (costly, and the backstop for prose). A run the shape check refuses never reaches the probe, so the
common case still spends nothing.

WHY THE PROBE IS STILL NEEDED EVEN WITH A TYPED SHAPE, stated because a typed row makes it tempting to
conclude otherwise. The typed shape removes the place a deliverable could be parked IN A ROW. It does not
remove the continuation lines, the `## Completion criteria` section, or the `## Cross-IPD validation`
section, all of which are prose an author can still load with an obligation. `25kzda` 2.5b's prohibition
on substituting a syntactic rule therefore still binds: the shape check narrows the probe's job
substantially but does not retire it.

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

WHY A SHAPE CHECK RATHER THAN A VOCABULARY CHECK, which is this spec's largest change of direction and
happened at review round 2. The draft policed WORDING: an allowlist of tracking verbs, optionally plus a
requirement that an item name a child id6. Both were measured across all 11 live pending orchestrators
(32 `E-*` items) and both have a recall problem that cannot be tuned away:

- A LEADING-VERB ALLOWLIST flags 11 of 32. It catches every known violator, but it also flags `ao1rb7`
  E-01/E-02, whose "EXECUTE THE CHILDREN IN ORDER" is legitimate sequencing, and it can be satisfied by
  opening a deliverable with an allowlisted verb - `wfjsp4` E-02 and E-04 both begin "VERIFY" while
  describing whole-Set work no child covers.
- A CHILD-REFERENCE REQUIREMENT flags 11 of 32 and independently PASSES `rh5tt6` E-02, the one violation
  measured in production, because that item name-drops sixteen children while being pure parent-only work.
- A CONFESSION-PHRASE TEST ("no child owns/covers/can") fires on only 2 of 32. Every hit is a true
  positive, but the recall is near zero.

A TYPED SHAPE HAS NO RECALL QUESTION because it is not a judgement. A row either supplies a resolvable
child id6, a legal status, and an ordering edge, or it does not. A deliverable cannot be phrased into that
form, so the invariant holds by construction instead of by detection. That is a different kind of
guarantee from any of the three signals above, and it is why the vocabulary work the draft specified is
not merely improved but unnecessary.

WHAT IS GIVEN UP, AND WHY IT WAS JUDGED AFFORDABLE. A typed row cannot carry a cross-child condition, and
review round 1 treated that as disqualifying. Measurement reversed it: all three candidate counter-examples
were either duplication of a child's own assertion or work already relocated into a final child (R1b). The
remaining cost is real but smaller: 11 existing orchestrators need rewriting, and the hand-run checklist
becomes terser (R2a addresses that directly).

THE PROHIBITION IN `25kzda` 2.5b STILL BINDS AND IS STILL SATISFIED. That section forbids substituting a
syntactic rule for the semantic check, on the measured grounds that false positives would drive agents to
delete the child checklist. A shape check runs FIRST, its refusal is routed to a repair loop that names
both remedies and forbids deletion (R7), and the semantic probe still runs behind it over the prose the
shape check does not read. Nothing is substituted. An implementer who finds themselves removing the probe
has left this spec's scope.

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
of 5 on a sample this spec already had in hand. So a WORDING-BASED rule's recall on the harmful case is
demonstrably partial, and retiring the semantic check in favour of one would have narrowed coverage while
claiming to harden it. (Review round 2 then removed the wording rule entirely in favour of the typed
shape, which is why these measurements survive here as the REASON for that change rather than as a
description of what ships.)

WHAT THE DETERMINISTIC CHECK IS STILL FOR, given that. It is cheap, it runs at REVIEW where a violation
can be repaired rather than merely reported, and a refusal there costs a revision instead of a dead end
(R5). That is a real contribution to a real problem; it is just not a replacement for the semantic check.
The honest framing is defense in depth with distinct coverage, not one mechanism superseding another. Note
the typed shape chosen in round 2 is STRONGER than the wording rule measured above: it does not detect a
deliverable, it makes one unwriteable in a row.

THE COST OF HAVING BEEN WRONG HERE IS WORTH RECORDING, because it is the argument for reading the
governing spec before proposing to replace its mechanism: the draft would have deleted 476 lines of
shipped code across seven functions and 1265 lines of tests, merged the same day, and contradicted an
approved spec's explicit prohibition. Nothing in the draft's reasoning was sufficient to justify that,
and the draft did not cite 2.5b at all.

THE PROBE'S SUPPORTING MACHINERY IS ALSO WHAT THIS SPEC BUILDS ON rather than salvages: its bounded
payload, its cache keyed on exactly the inputs it reasons over, and its collect-all-then-partition
structure. R8's batch reporting is that structure generalized across check kinds.

WHAT IS GENUINELY UNRESOLVED, flagged rather than papered over. The maintainer raised, and this spec does
not settle, how to keep the ENFORCEMENT CODE and the AUTHORING INSTRUCTIONS from drifting apart: the row
grammar the check enforces must also be documented for the agent writing a Set, and two hand-maintained
statements of one rule drift. OQ-01 carries a proposed direction (render the instructions from the rule)
rather than a decision, and records that the TYPED choice shrinks this question because a conforming
scaffold shows an author the shape instead of telling them a rule.

## 3a. Honest limits: what this spec does NOT prove

Stated explicitly because the draft claimed more than it delivers, and a spec that oversells is worse
than one with a narrow scope.

1. A CONFORMING CHECKLIST IS NOT EVIDENCE THAT AN ORCHESTRATOR CARRIES NO UNCOVERED WORK. It is evidence
   that every ROW is a well-formed child-tracking row. R1a deliberately does not parse the continuation
   lines, the `## Completion criteria` section, or the `## Cross-IPD validation` section, and an
   obligation can still be written there. That residue is the semantic probe's job, which is why `25kzda`
   2.5b's prohibition still binds and the probe is retained.
2. THE SHAPE CHECK HAS NO RECALL QUESTION FOR ROWS, AND AN UNQUANTIFIED ONE FOR PROSE. Within a row the
   check is structural, so "recall" does not apply: a deliverable cannot take the typed form. Outside a
   row it has no reach at all. An implementer should measure how much of the real violation population
   lived in ROWS versus in PROSE before and after, and RECORD it, because that ratio is what says whether
   the shape change closed most of the gap or merely moved it.
3. REVIEW-TIME REPAIR IS AGENT-PERFORMED AND SELF-ASSESSED. R5/R6 bound and log it; they do not make it
   independent. The run-time consumer is what provides independence, and it re-validates rather than
   trusting the review's verdict.
4. NOTHING HERE PREVENTS A DELIBERATELY CONCEALED DELIVERABLE. An author intent on hiding agent work can
   put it in the prose R1a does not read, and plausibly phrase it past a probe too. The controls raise the
   cost of the ACCIDENTAL violation, which is the measured failure mode (`rh5tt6`, and the 2026-09-06
   `Readiness` incident, were both pattern-completion rather than deception).
5. THE TYPED SHAPE IS A CONSTRAINT ON THE ROW, NOT A PROOF ABOUT THE SET. It guarantees that what a row
   SAYS is a child-tracking obligation. It does not guarantee the Set's children actually cover the Set's
   work: a parent can conform perfectly while its author simply omitted a needed final child. R1b names
   the remedy but nothing detects the omission, and this spec does not claim to.
6. THE MIGRATION IS NOT DESIGNED HERE. Section 5 cost 3 states that 11 orchestrators need rewriting and
   names the cutover pattern; choosing between a cutover, a sweep, and a grandfather clause is the
   implementing plan's decision, and a wrong choice there could strand a Set mid-flight.

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
3. EVERY EXISTING ORCHESTRATOR NEEDS ITS CHECKLIST REWRITTEN, AND THE COST IS LARGER THAN THE DRAFT SAID.
   This is the principal cost of choosing TYPED over a vocabulary rule, and it is stated at full size
   rather than minimised. Measured during the design conversation: of ten pending `Kind: orchestrator`
   plans, seven carried at least one parent-only item. RE-MEASURED AT REVIEW the population was ELEVEN
   (`7ewc74` left by being finalized; `2xz59a` and `s0gnha` arrived), which is why this is a dated
   snapshot and not a fixture.
   THE DRAFT UNDERSTATED THE REWRITE by claiming most items were already schema-shaped. Measured properly,
   only 11 of 32 `E-*` items are even close (a single resolvable child reference and a short body); the
   other 21 have first lines between 133 and 1528 characters.
   MEASURED AGAINST THE R1a GRAMMAR ITSELF, THE ANSWER IS BLUNTER AND IS STATED RATHER THAN SOFTENED:
   **ZERO of 32 rows conform today.** Every `E-*` item on every live orchestrator needs rewriting, because
   none is currently written as `CONFIRM <child-id6> REACHED <status>`. This is the single largest cost in
   this spec and the honest counterweight to the by-construction guarantee: the guarantee is bought with a
   total rewrite of an existing surface, not with a formatting pass. Prose currently carrying genuine
   orchestration meaning must be relocated into continuation lines (R1a), into the orchestrator's prose
   sections, or into a final child (R1b).
   AN IMPLEMENTER SHOULD RE-DERIVE THAT ZERO rather than trust it, and should expect it to stay near zero
   until the migration runs: the grammar is new, so nothing authored before this spec can satisfy it by
   accident. A non-zero count before migration would mean the grammar was quietly widened.
   THE ROUTE IS THE IMPLEMENTING PLAN'S TO CHOOSE and criterion 12 constrains the outcome rather than the
   method: a date cutover (the `check_engine.CARRIER_CUTOVER_DATE` pattern), a migration sweep, or an
   explicit grandfather clause are all admissible, but none may leave a Set refused with no available
   remedy. An implementer must re-derive the population and report the denominator.
4. REVIEW STILL ASSERTS A CHECK THE SAME AGENT PERFORMED. R8 mitigates rather than eliminates this. It is
   a property of the whole review pipeline, not something introduced here.
5. THE SHAPE CHECK GOVERNS ROWS ONLY, AND ITS REACH ENDS THERE. Within a row it is structural and has no
   recall question, because a deliverable cannot be expressed as three typed fields (R1a). Outside a row
   it has no reach at all: R1a deliberately does not parse continuation lines or the orchestrator's prose
   sections, so the semantic probe remains the control for those. A consumer must not read a conforming
   checklist as evidence that an orchestrator carries no uncovered work. The vocabulary signals the draft
   proposed were measured and abandoned for exactly this reason (Section 3): each policed wording and each
   had a measurable miss rate, which by-construction avoids rather than improves.

## 6. Acceptance criteria

Each criterion states a SHAPE plus the evidence that satisfies it. Counts in this spec are dated
snapshots of a moving corpus; an implementer must RE-DERIVE them and report the denominator rather than
quoting this document.

1. ONE function decides conformance, and both consumers call it. Evidence: the function, and both call
   sites, with a grep showing no second implementation of the rule.
2. THE TYPED ROW IS PARSED AS THREE FIELDS, and each is validated. Evidence: a conforming row yielding
   `(child_id6, status, depends_on)`; a row whose `<child-id6>` resolves to no row of that orchestrator's
   own child table REFUSED; a row whose `<status>` is outside the plan status vocabulary REFUSED; a row
   missing the `Depends on:` edge REFUSED. One fixture per case, each with the rendered message.
3. A DELIVERABLE CANNOT BE EXPRESSED AS A CONFORMING ROW. Evidence: take the three real parent-only items
   measured at review (`5e4sb6` E-01 "Produce the function-by-function INVENTORY", `wfjsp4` E-02 "VERIFY
   THE BROWSE AFFORDANCE ACTUALLY ARRIVED", `tb63qv` E-01 "After both children are executed, verify the
   Set's combined outcome") and show each is refused. This is the pin for R1a's by-construction claim and
   it must include `wfjsp4` E-02 specifically, since that item opens with an allowlisted VERB and would
   have passed the draft's vocabulary rule.
4. A CONFORMING ORCHESTRATOR AND A CROSS-CHILD CHECK COEXIST. Evidence: an orchestrator whose rows all
   conform, plus a final child carrying `- Item-Dependencies:` naming every sibling, together passing. Cite
   `svacmz` as the in-tree precedent rather than inventing a fixture shape.
5. The refusal text states the invariant, forbids satisfying it by deletion, and names both remedies
   without prescribing one. Evidence: the rendered message.
6. `/plan-review` repairs a violating orchestrator within the attempt budget and the repaired plan
   passes. Evidence: the before and after checklists plus the round record.
7. An exhausted loop leaves the plan `to-review` with `- Readiness:` ABSENT and the attempts logged.
   Evidence: the plan's front matter and the round record after a deliberately unfixable case.
8. A run reports EVERY finding across EVERY queued orchestrator in one pass, then refuses. Evidence: a
   multi-violation queue's output showing all findings before the exit.
9. The model probe STILL RUNS and still blocks, and the shape check did not displace it. Evidence: a
   queued orchestrator whose ROWS all conform but which carries an obligation in its continuation lines or
   its `## Completion criteria` section is still refused, plus `tests/test_orchestrator_probe.py` passing
   UNEDITED, plus `grep` showing the probe's seven functions intact. This criterion inverts the draft's
   criterion 7 and is the pin for SR-001.
10. The shape check's REFUSAL and the probe's REFUSAL are distinguishable to an operator, so a human
    reading a refused run knows which control fired and therefore which remedy applies. Evidence: both
    messages, side by side, naming different rule ids.
11. The ordering is shape-check-then-probe, and a shape refusal spends no model call. Evidence: a run
    refused by the shape check showing zero probe invocations.
12. THE MIGRATION LEAVES NO SET STRANDED. Evidence: after whichever migration route is chosen, every one
    of the pre-existing orchestrators either conforms or is explicitly grandfathered with its mechanism
    named, and NONE is left in a state where a run refuses it with no available remedy. Re-derive the
    population; it was 11 at review and moves.
13. The full suite passes and `aw check all` is no worse than its pre-change baseline, both counts pasted.

## 7. Open questions

### OQ-01: How should the authoring instructions be kept from drifting away from the enforcing code?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because the conformance rule and its two consumers can
  be built and tested before this is settled; an implementer would simply hand-write the instructions and
  inherit the drift risk. It matters because a rule the check enforces must also be documented for the
  agent AUTHORING a Set, and two hand-maintained statements of one rule diverge, which is the failure
  this whole spec is a response to at a different level. PROPOSED DIRECTION, not a decision: hold the row
  GRAMMAR as data in the rule module and render the refusal message, the `aw ipd scaffold` skeleton, and
  the documentation from that one source, so the instructions cannot disagree with the check. The
  alternative (prose beside code, kept in step by discipline) is what the repository does today for most
  rules and is honestly workable; it just has a known decay mode.
  NARROWED BY THE OQ-02 RESOLUTION, AND THIS IS THE USEFUL PART: choosing TYPED shrinks this question
  considerably. A vocabulary would have meant documenting a verb list, its rationale, and its edge cases in
  prose for authors while the code held the same list - two statements that drift. A typed row is mostly
  self-documenting through the scaffold: an author who starts from a conforming skeleton is shown the shape
  rather than told the rule. So the residual drift risk is the GRAMMAR plus the refusal wording, which is a
  much smaller surface than a vocabulary and its exceptions would have been.

### OQ-02: Should the orchestrator checklist stay prose with an enforced vocabulary, or become a typed child-tracking structure?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-19 AS **TYPED**, and R1a/R1b/R2a
  are that resolution written into the normative section. The decision reversed this spec's draft, which
  specified a prose vocabulary, so the reasoning is recorded in full rather than as an outcome.
  WHAT THE DRAFT ARGUED, AND WHY IT WAS WRONG. It claimed some parent rows carry cross-child conditions a
  typed row cannot express, and named three. Measurement refuted all three: `y9s4vm` E-02's condition is
  already asserted by child `iuxtjy`'s own Scope and three of its V-items; `lyo1tz` E-02's is asserted
  seven times by child `1f7xno`; and `s0gnha` E-02's had already been relocated into child `svacmz`,
  which carries `- Item-Dependencies:` naming all three siblings. So two were duplication the spec should
  reject and the third was the R1b remedy already in production use. Zero counter-examples were found in
  32 items across 11 orchestrators.
  A SECOND DRAFT CLAIM WAS ALSO FALSE and is corrected here because it made the migration look cheaper
  than it is: the draft asserted that "21 of 32 items already reduce to confirm-child-X-is-executed, so
  the corpus is mostly typed already". Measured properly, only 11 of 32 are schema-shaped; the rest have
  first lines from 133 to 1528 characters. The migration is therefore LARGER than the draft implied, and
  Section 5 cost 3 now says so.
  WHY TYPED WON ANYWAY. A vocabulary rule polices wording, so it always carries a recall question and a
  false-positive rate, both measured: a verb allowlist flags 11 of 32 but passes `wfjsp4` E-02 (a
  deliverable opening with "VERIFY") and wrongly flags `ao1rb7`'s legitimate sequencing; a child-reference
  rule passes `rh5tt6` E-02, the production failure. A typed row has neither property, because a
  deliverable cannot be phrased into three typed fields. The maintainer's standing objection to this whole
  area was brittleness of enforcement, and by-construction is the only answer to that which does not
  depend on a heuristic.
  WHAT REMAINS ARGUABLE, since this is a trade and not a proof: a typed row is terser for the hand-run
  reader R2 exists to serve (R2a addresses it but does not eliminate it), and the schema cannot express
  something a future Set genuinely needs, in which case the answer is a child (R1b) rather than a wider
  schema. If an implementer finds a legitimate case that is neither expressible as a row nor sensible as a
  child, that is evidence worth bringing back rather than a reason to widen the row quietly.

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
