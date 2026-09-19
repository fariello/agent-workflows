# Spec: Orchestrator conformance: one parser, review-time repair, run-time refusal

- Date: 2026-09-19
- Status: to-review
- Id: r07vma
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Spec: 77tr3o
- Scope: An Order-0 orchestrator may hold only child-tracking items; one shared parser enforces that, plan-review repairs violations in a bounded loop, and a run re-parses and refuses with every finding at once.
- Parent: `.aw/records/specs/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md` (`77tr3o`,
  `approved`), which owns runner-owned retirement. This spec REPLACES that spec's R-12 mechanism (a
  model probe at run start) with a deterministic one, and leaves R-1 through R-11 untouched.

## Workflow history

- 2026-09-19 to-review (aw specs): Drafted from a maintainer design conversation after a live run refused tb63qv on its single E-item. Establishes that an Order-0 orchestrator may hold only child-tracking items, because retirement is programmatic and skips the E/V checkpoint, so a parent item needing an agent can never be performed (measured: evaluate_set_retirement contains zero references to E-/V-/items/checklist; rh5tt6 was retired 2026-09-08 with its own commit message saying its items were NOT performed). REPLACES 77tr3o R-12's model probe with one shared parser called by both plan-review and the run. The maintainer rejected a new front-matter attestation field: a gate-read field written by the authoring agent is the shape - Readiness: already proved unreliable, and the 2026-09-06 incident was pattern-completion rather than deception, so the fix is to not create the blank. Two open questions recorded rather than settled: how to keep authoring instructions from drifting from the enforcing code, and whether the checklist should become a typed structure.
## 1. The problem, and why the existing fix is the wrong shape

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
whether the parent carries work no child covers. That gate works and has already refused a real run. But
three properties make it a poor fit for this particular invariant, and they are why this spec proposes a
different mechanism rather than tuning the existing one:

1. IT IS A SOFT CHECK ON A HARD INVARIANT. Whether a parent can hold agent work is not a judgement call
   under R-5; it is decided by the retirement path having no agent turn. A model verdict introduces
   variance into something the design settles.
2. IT FAILS OPEN ON AVAILABILITY. A `could-not-ask` (missing binary, timeout, empty reply) proceeds with
   a warning and a recorded hole, which is the right call for an availability failure and the wrong
   place for the only enforcement of an absolute rule to live.
3. IT REFUSES AT THE WRONG MOMENT. The refusal lands at run start, when the remedy (editing a plan's
   checklist, possibly authoring a child) is exactly what a run must not do to another agent's plan. The
   operator is told to go fix something by hand, having already queued a run.

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

R9 (THE RUN ASKS NO MODEL). The run-time check spends no tokens and has no availability failure mode.
The model probe R-12 introduced is RETIRED by this spec rather than layered beneath the parser, because
two mechanisms answering one question is how they come to disagree.

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

WHY A PARSER RATHER THAN A MODEL, given that a parser cannot be complete. A textual rule cannot reliably
distinguish "verify the Set's combined outcome" (agent work) from "verify child X reached executed"
(tracking) in every phrasing, and this spec does not claim otherwise. Two things make the parser the
better trade anyway. First, its failure direction is safe: a false refusal leaves the plan in `pending/`,
which is the status quo, whereas a false pass loses work silently and is what `rh5tt6` measured. Second,
R5 changes what a false refusal COSTS: with an agent asked to fix and re-check, an over-strict parser
produces a revision rather than a dead end, so strictness is cheap in a way it would not be if the
parser were the last word. That second reason is the one that made a tight vocabulary acceptable to the
maintainer, having been reluctant about it earlier in the same conversation.

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

WHY THE MODEL PROBE IS RETIRED RATHER THAN KEPT AS A BACKSTOP. Keeping both means two answers to one
question, and they will eventually differ; the probe also fails open, so as a backstop it would
contribute nothing on the one axis that matters. The probe's SUPPORTING machinery is worth salvaging
though: its bounded payload, its cache keyed on the same inputs it reasons over, and its
collect-all-then-partition structure are all reusable, and R8's batch reporting is that structure
generalized across check kinds.

WHAT IS GENUINELY UNRESOLVED, flagged rather than papered over. The maintainer raised, and this spec does
not settle, how to keep the ENFORCEMENT CODE and the AUTHORING INSTRUCTIONS from drifting apart: a
vocabulary and structure the parser enforces must also be documented for the agent writing a Set, and
two hand-maintained statements of one rule drift. OQ-01 carries a proposed direction (generate the
instructions from the rule) rather than a decision.

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
   one parent-only item. A date cutover (the `check_engine.CARRIER_CUTOVER_DATE` pattern) can make this
   gradual, which is the implementing plan's decision to make.
4. REVIEW STILL ASSERTS A CHECK THE SAME AGENT PERFORMED. R8 mitigates rather than eliminates this. It is
   a property of the whole review pipeline, not something introduced here.

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
7. The model probe is gone, not merely bypassed. Evidence: `grep` for its symbols, and the tests that
   pinned it either removed with a reason or retargeted.
8. The full suite passes and `aw check all` is no worse than its pre-change baseline, both counts pasted.

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
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking for the run-time consumer, which by construction sees
  only queued orchestrators. It is a real question for the REVIEW consumer, which sees every plan it
  reviews. The invariant's justification is mechanical and specific to the runner's retirement path, so
  an orchestrator that will only ever be hand-run is not subject to the failure R1 prevents: a human or
  agent running it by hand DOES execute its items, which is exactly what `77tr3o`'s own Scope preserves.
  PROPOSED DIRECTION: apply the rule uniformly anyway, because nothing marks a plan as hand-run-only, and
  a Set's execution route is not fixed at authoring time. The cost of uniformity is that a legitimately
  hand-run Set loses the ability to put a whole-Set step on its parent; the cost of non-uniformity is a
  rule that depends on an unknowable future, which is worse.
