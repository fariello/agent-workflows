# Spec: Cross-type review: reviewing specs as first-class review work items

- Date: 2026-09-04
- Status: to-review
- Id: 6m4kow
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Blocks-Release: next
- From-Spec: 25kzda
- Scope: the spec-review capability that spec `25kzda` Section 3.3 mandates and nothing implements. Three
  parts: a spec-review workflow that can legally advance a spec from `to-review` to `reviewed`, an
  artifact-neutral review record so a spec review can be filed at all, and needs-review discovery that
  can see a tree other than `plans/`. It does NOT specify the `aw <host> review` alias, the `reviews`
  status selector, or the draft admission gate: those are `25kzda` Sections 2.1, 2.4a and 2.5a, amended
  2026-09-04, and this spec CONSUMES them. It does NOT specify the runner's flag surface (`uyeko5`), and
  it does NOT change any plan-review behavior beyond what generalizing the record shape forces.

## Workflow history
- 2026-09-04 to-review (aw set): Authored at the maintainer's direction while answering a question about naming a review-status command. Research established that spec 25kzda (approved, Blocks-Release: next) already MANDATES spec review in Section 3.3 and already defines three deterministic checks for it by name in Section 4.8 (SPEC-REVIEW-COMPLETE, SPEC-REVIEW-TRANSITION, SPEC-REVIEW-STRUCTURE), so this is COMPLETION of approved release-gating work rather than a new proposal; hence From-Spec: 25kzda and the inherited release gate. FOUR THINGS MEASURED AT AUTHORING, not inherited: (a) no spec-review workflow exists at all - .aw/system/workflows/ has plan-review and plan-review-long, /spec states it PRODUCES rather than reviews, and /advise spec-editor yields no verdict, findings, or transition; (b) review_findings.render_review hardcodes '- Plan-Id:' and check_engine.check_review_dangling resolves it against the plans tree ONLY, so a spec review would be flagged check.review-dangling by the repository's own checker; (c) runner_shared.discover_plans walks only the two plans trees, so no selector can reach a spec however it is spelled; (d) spec to-review -> reviewed has NO entry in attention_contract.TRANSITION_AUTHORITY, so it is an UNATTESTED status flip today - an agent can set a spec reviewed with no review, no findings and no record, while the same claim on a plan is policed by check.review-finding-unescalated and the approval verdict guard. That gap is what R-11 closes and is the strongest argument in the spec, given that specs are the artifact which AUTHORIZES plans. POPULATION MEASURED so nobody reads this as throughput work: 1 plan at to-review, 2 specs at draft, 0 specs at to-review, 34 existing review records; recorded as an honest limit rather than omitted, because the justification is structural (two thirds of needs-review artifacts have no workflow) and not volume. ONE DECISION LEFT OPEN DELIBERATELY (R-10, Section 5): a new spec-review/ workflow versus generalizing plan-review/. Left to the graduating plan because it needs the code in front of it and both answers are defensible - generalizing means changing two bodies held in deliberate parity and making plan-specific machinery conditional, while forking means two rubrics. The constraint binding either answer is stated instead: the findings/verdict/record machinery stays shared exactly once, so a plan that forks the record is rejected regardless of workflow shape. Also recorded: 'aw find specs --status' silently ignores its filter at authoring (verified for all nine statuses), so anything built on it inherits the bug.

## 1. Why this exists

Spec `25kzda` is approved and gates the next release. Its Section 3.3 dispatch table states, for a spec
at `to-review`: "Run spec review; apply corrections; tool-set `reviewed`; redispatch." Its Section 4.8
goes further and defines three deterministic checks for that action by name, `SPEC-REVIEW-COMPLETE`,
`SPEC-REVIEW-TRANSITION`, and `SPEC-REVIEW-STRUCTURE`, each with an exact failure message and recovery
command.

None of it is implementable today, because there is no spec review to run. The gap is not a missing flag
or an unwired predicate; it is three missing mechanisms, and each one independently blocks the action:

1. **No spec-review workflow exists.** `.aw/system/workflows/` contains `plan-review` and
   `plan-review-long`, and nothing that reviews a spec. `/spec` authors specs and says so explicitly
   ("`spec` PRODUCES the artifact"); `/advise spec-editor` coaches interactively and produces no verdict,
   no findings, and no status transition.
2. **The review record cannot describe a spec review.** `review_findings.render_review` writes
   `- Plan-Id: <id6>` as the join key, and `check_engine.check_review_dangling` resolves that field
   against the plans tree alone. A review filed against a spec would therefore be reported as
   `check.review-dangling` by the repository's own checker.
3. **Needs-review discovery cannot see a spec.** `runner_shared.discover_plans` walks
   `.aw/records/plans` and `.agents/plans` and nothing else, so no selector can reach a spec however it
   is spelled.

The consequence is not theoretical. `to-review -> reviewed` for a spec has no entry in
`attention_contract.TRANSITION_AUTHORITY`, so nothing requires evidence that a review happened: an agent
may set a spec `reviewed` with no review, no findings, and no record. For plans that same claim is
policed by `check.review-finding-unescalated` and the approval verdict guard. Specs are the artifact
that AUTHORIZES plans, and they are the artifact whose review is unattested.

A note on sizing, stated plainly so nobody reads this spec as urgent throughput work. At authoring the
repository held 1 plan at `to-review` and 2 specs at `draft`; no spec was at `to-review`. The volume
argument for this work is weak and should not be made. The argument is structural: two thirds of the
artifacts that need review have no workflow that can review them, and the transition they would take is
unattested.

## 2. Requirements

Each requirement has a stable ID so a graduating plan can trace to it (`25kzda` Section 4.8's
`SPEC-PLAN-TRACE` requires that mapping).

### 2.1 The review record becomes artifact-neutral

- **R-01** The review record MUST identify its subject with an artifact-neutral field pair: a
  `- Subject-Id: <id6>` naming the reviewed artifact and a `- Subject-Type: <ipd|spec>` naming its type.
  A review record MUST carry both.
- **R-02** `Subject-Type` MUST be drawn from a closed vocabulary. It admits `ipd` and `spec` in this
  spec. It is not open-ended: a type is added by amending this vocabulary and the dispatch table
  together, never by writing a new value into a record.
- **R-03** The dangling-reference check MUST resolve `Subject-Id` against the tree named by
  `Subject-Type`, not against the plans tree unconditionally. A spec review whose subject exists MUST
  NOT be reported as dangling.
- **R-04** `- Plan-Id:` is REPLACED, not carried alongside. This repository is pre-release and its
  conventions forbid compatibility shims; two fields meaning one thing is precisely the duplicate
  mechanism that produces divergence. The 34 existing review records are migrated in the same change
  that introduces the new field, mechanically, with the migration shown.
- **R-05** The review filename grammar is UNCHANGED. It is already artifact-neutral:
  `build_review_name` delegates to `artifact_naming.build_clustered_name` with the `review` facet, and
  the embedded `<id6>` is simply the subject's. Only the docstrings claim otherwise, and only they need
  correcting.

### 2.2 A spec review exists and can be run

- **R-06** A spec-review capability MUST exist that produces, for a spec: a findings table, a verdict
  from the existing four-value vocabulary, a review record conforming to Section 2.1, and a legal
  tool-authored transition to `reviewed`.
- **R-07** It MUST NOT write `- Readiness:` onto a spec. `Readiness` is a plan field. Section 3.3 of
  `25kzda` stops a reviewed spec at a human approval gate unconditionally, even under `--full-auto`, so
  a spec has no automated readiness signal to record and inventing the field would create a machine
  signal that no consumer may act on.
- **R-08** It MUST NOT hand-edit a spec's `- Status:` or its workflow-history section. Both are owned by
  `aw specs set` / `aw specs note`, the spec README forbids hand-editing them, and a
  `status_untooled_gate` hook exists for exactly this bypass.
- **R-09** It MUST NOT run `aw ipd lint` against a spec. That linter is IPD-only. The equivalent
  structural gate for a spec is `aw specs check`, which is what `25kzda`'s `SPEC-REVIEW-STRUCTURE`
  recovery command already names.
- **R-10** Whether the capability is a NEW workflow (`spec-review/`) or a GENERALIZATION of
  `plan-review/` is deliberately left to the graduating plan, which must decide it against the code and
  record the decision. Section 5 states the tradeoff and the constraint either answer must satisfy.

### 2.3 The transition becomes attested

- **R-11** A spec's `to-review -> reviewed` transition MUST require evidence that a review occurred:
  specifically, a conforming review record whose `Subject-Id` is that spec. This closes the gap in
  `TRANSITION_AUTHORITY` and makes the spec transition as attested as the plan one.
- **R-12** The attestation MUST fail closed and MUST be enforced by the same shared predicate that the
  checker, the setter, and any hook consult. One predicate, several call sites; never a second copy.
- **R-13** Enforcement MUST NOT retroactively invalidate the 15 specs already at `implemented` or the 5
  at `approved`, none of which have review records. Existing specs are grandfathered exactly as
  `25kzda` Section 2.11 grandfathers pre-cutover IPD dependency statements: the requirement binds
  transitions performed AFTER the change, not history.

### 2.4 Needs-review discovery spans types

- **R-14** The needs-review predicate defined by `25kzda` Section 2.4a MUST be implemented ONCE, in a
  shared module, consulted by every host runner and by the preview. It MUST NOT be a closure inside a
  runner's selector expansion, which is how the current plans-only copy came to be duplicated verbatim
  in two runners and to diverge from the dispatch table.
- **R-15** Discovery MUST be able to enumerate needs-review artifacts from a tree other than `plans/`.
  Type scoping follows `25kzda` Section 2.4a: IPDs only unless `--type` names otherwise.
- **R-16** The predicate MUST derive membership from the Section 3 dispatch table, so an item the table
  routes to review and an item the sweep selects are the same set BY CONSTRUCTION. The existing
  divergence (a complete `draft` plan is reviewed when named, absent when swept) MUST be fixed by
  construction rather than by patching both copies.

## 3. Acceptance criteria

- **A-01** A spec at `to-review` can be reviewed end to end, producing a findings table, a verdict, a
  conforming review record, and a tool-authored transition to `reviewed`.
- **A-02** `aw check all` reports no `check.review-dangling` for a spec review whose subject exists,
  and still reports it for a review whose subject does not.
- **A-03** All 34 pre-existing review records carry `Subject-Id`/`Subject-Type` after migration, no
  record retains `- Plan-Id:`, and `aw check all` is no worse than its pre-change baseline.
- **A-04** No spec acquires a `- Readiness:` field, and no spec's status or workflow history is written
  by anything other than `aw specs set` / `aw specs note`.
- **A-05** Setting a spec `reviewed` without a conforming review record is REFUSED, with a message
  naming the missing record and a recovery command; setting it WITH one succeeds. A pre-existing
  `implemented` or `approved` spec is unaffected.
- **A-06** The needs-review predicate has exactly one implementation. A grep shows no second copy in
  either runner, and both runners plus the preview consult it.
- **A-07** A complete `draft` item appears in the needs-review set exactly when the dispatch table
  routes it to review, demonstrated for both a plan and a spec, so the sweep and the table agree.
- **A-08** `25kzda`'s three named spec checks (`SPEC-REVIEW-COMPLETE`, `SPEC-REVIEW-TRANSITION`,
  `SPEC-REVIEW-STRUCTURE`) are each satisfiable, with the evidence each one inspects actually produced.

## 4. Decisions

- **D-01 The record becomes artifact-neutral rather than gaining a parallel spec record.** A second
  record type would double the parser, the checker, the naming rules, and the gating predicates, to
  express one concept. The filename grammar is already neutral, which is evidence the original design
  intended this.
- **D-02 `Plan-Id` is replaced, not deprecated in place.** Pre-release conventions forbid shims, and
  the population is 34 files with one mechanical edit each.
- **D-03 Backlog, research, releases, and walkthroughs are OUT of scope.** None has a `to-review`
  status; `25kzda` Section 3.6 gray-skips research, releases and walkthroughs at every status, and
  Section 3.4 gives backlog `graduate`, not `review`. `Subject-Type` is closed at `ipd|spec` for that
  reason, and widening it means amending the dispatch table too.
- **D-04 Attestation is required for the spec transition even though it is new pressure.** The
  alternative is a `reviewed` status that means nothing, which is worse than an inconvenient gate: it
  is precisely the "false claim" failure mode the repository's execution contract exists to prevent.
- **D-05 The plans-only closure is deleted, not extended.** Two verbatim copies inside two runner
  closures is the shape that caused the divergence; the fix is one shared predicate derived from the
  dispatch table.

## 5. The one decision left to the graduating plan

R-10 deliberately does not choose between a new `spec-review/` workflow and generalizing
`plan-review/`. Both are defensible and the choice needs the code in front of it:

- GENERALIZING keeps one review body, so a rubric improvement reaches both artifact types. But
  `plan-review` and `plan-review-long` are held in deliberate parity, so it means changing two bodies in
  lockstep, and the body is saturated with plan-specific machinery (the `aw ipd lint --phase author`
  preflight, the required `- Readiness:` write, the E/V and Scope-Paths rubric items) that must become
  conditional. Conditionals in a workflow body are read by an agent under load, and a mis-taken branch
  is a wrong lifecycle write.
- A SEPARATE WORKFLOW keeps each body linear and lets the spec rubric ask spec questions (are the
  requirements testable, do acceptance criteria cover them, are decisions recorded with rationale)
  rather than plan questions. But it forks the shared parts, and this repository has paid for forks
  before.

The constraint either answer MUST satisfy: the FINDINGS/VERDICT/RECORD machinery is shared, exactly
once. Whatever happens to the workflow bodies, `review_findings` remains the single writer and parser of
a review record, and the verdict vocabulary remains the one in `plan_readiness.VERDICTS`. A plan that
forks the record is rejected regardless of which workflow shape it picks.

## 6. Honest limits

- **Review quality remains non-deterministic.** This spec adds a proof that a spec review OCCURRED and
  was recorded. It cannot prove the reviewer noticed every flaw. `25kzda` Section 6.1 already states
  this limit for plans; it holds identically here, and R-11's attestation must not be described as a
  quality guarantee.
- **The immediate payoff is small.** 3 artifacts need review at authoring. The work is justified
  structurally, not by throughput, and a graduating plan should not claim otherwise.
- **Grandfathering leaves a permanent honest hole.** The 20 specs already at `approved` or
  `implemented` will never have review records, so the attestation is a going-forward invariant only.
  Any consumer that treats "has a review record" as a property of all reviewed specs will be wrong
  about history.
- **`aw find specs --status` is broken at authoring** and silently ignores its filter, returning all 26
  specs for every value. Anything built on top of it inherits that bug, so a graduating plan must either
  fix it or avoid depending on it, and must not assume the filter works because the flag exists.

## 7. Non-goals

- The `aw <host> review` alias, the `reviews` selector, and the draft admission gate: `25kzda`
  Sections 2.1, 2.4a, 2.5a. Consumed here, not specified here.
- The runner flag surface, including `--type` and `--allow-drafts` registration: plan `uyeko5`.
- Multi-type SELECTION and the mixed-type gate wiring: `25kzda` Sections 2.2/2.3/2.5, gate built by
  executed plan `6lu3rq`, wiring owned by `uyeko5`.
- Reviewing backlog, research, release, or walkthrough records (D-03).
- Any change to plan-review's rubric, severity vocabulary, verdict vocabulary, or findings columns.
  Only the record's subject fields change.
- Per-type subdirectories under `.aw/records/reviews/`: that is open backlog `sv0sf3`, decided 65/35
  toward the flat layout, and it is orthogonal to the subject-field change.
