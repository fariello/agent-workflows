# Spec: Cross-type review: reviewing specs as first-class review work items

- Date: 2026-09-04
- Status: approved
- Id: 6m4kow
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- From-Spec: 25kzda
- Scope: the spec-review capability that spec `25kzda` Section 3.3 mandates and nothing implements. Three
  parts: a spec-review workflow that can legally advance a spec from `to-review` to `reviewed`, an
  artifact-neutral review record so a spec review can be filed at all, and needs-review discovery that
  can see a tree other than `plans/`. It does NOT specify the `aw <host> review` alias, the `reviews`
  status selector, or the draft admission gate: those are `25kzda` Sections 2.1, 2.4a and 2.5a, amended
  2026-09-04, and this spec CONSUMES them. It does NOT specify the runner's flag surface (`uyeko5`), and
  it does NOT change any plan-review behavior beyond what generalizing the record shape forces.

## Workflow history

- 2026-09-23 note (aw specs): AMENDED by executed plan ui8b9b (specsweep Order 01), which delivered R-15's OPERATOR SURFACE: --type is now registered on BOTH hosts' start and resume parsers from the shared RUN_POLICY_FLAGS table and threaded to sweep_review_candidates_for_type, so 'aw <host> run reviews --type spec' is a real invocation. THREE corrections, each measured at HEAD a7e27f4a rather than inherited. (1) Section 0's R-15 row read 'IMPLEMENTED AT THE FUNCTION BOUNDARY, NOT OPERATOR-REACHABLE' with the evidence '--type is registered on NEITHER host'; both halves are now false. (2) That same row asserted the sweep 'returns the four to-review specs', a POPULATION claim that rotted TWICE in ten days (it returned [] at ui8b9b's review, because the spec-review round that filed ui8b9b advanced all four to approved, and returned one spec z7nbn1 at execution). The row is re-phrased on the PREDICATE and cites its tests, so it cannot rot the same way a third time; a reader wanting today's population runs the command. (3) The Section 0 gate table named plan mng63x as the execution half's carrier; mng63x was SUPERSEDED on 2026-09-18 by spec z7nbn1, which inherited Blocks-Release: next, so the table and Section 6 now point at z7nbn1 and record that the retired plan is in superseded/. WHAT IS UNCHANGED: this spec's - Status: (byte-identical, still approved) and its - Blocks-Release: (still ABSENT; it was cleared at authoring time in b16e1108 and was NOT re-cleared here, since a setter call against an absent field on an approved spec this plan's author did not approve would write a spurious record). THE LIMIT IS NARROWED, NOT REMOVED: selection ships, per-type EXECUTION does not, so a --type spec run selects the specs and then REFUSES to queue them (refuse_unrunnable_selected_types) naming what it selected, because a queue entry is plan-shaped and resolve_plan_path fails OPEN on a non-plan path. Spec z7nbn1 owns the remainder.
- 2026-09-13 approved (aw set, --by-human): status set to approved
- 2026-09-13 reviewed (aw set): spec-review round 1 (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; SR-101..SR-109, all nine FIXED, none deferred, none open. THIS REVIEW IS THE SPEC'S OWN ACCEPTANCE TEST: R-06 requires a spec-review capability producing a findings table, a verdict, a conforming record and a legal transition, and this record is that output, so A-01 is satisfied by the artifact itself. THE SPEC HAD SHIPPED AND READ AS THOUGH IT HAD NOT: 15 of 16 requirements are IMPLEMENTED (verified one by one) while Section 1 still said 'none of it is implementable today', so a new Section 0 carries a per-requirement status table with evidence and names the three delivering plans. NO CRITERION CITED A REQUIREMENT in a spec whose Section 2 gives every requirement a stable id for exactly that purpose; mapping them exposed R-05, R-10 and R-15 uncovered, and R-15 is the ONE unfinished requirement, so the uncovered and unfinished sets intersected where it was most dangerous. RELEASE GATE MOVED ON THE MAINTAINER'S RULING (a gate belongs on a plan, not a spec; plans preferred to backlog items; selection ships now with the execution half as its OWN blocker; HOW execution is implemented needs DISCUSSION captured loudly): filed ui8b9b (selection, conforming) and mng63x (execution, DESIGN-FIRST, Scope-Paths deliberately TBD, its OQ-01 being the design), both carrying Blocks-Release: next and From-Spec: 6m4kow, and this spec's gate is cleared in this same call. 2.0.0's blocker count is unchanged. Also corrected: the record population asserted as 34 (186 today, and already stale at 36 when the implementing plan was reviewed), the grandfathered count asserted as 20, the sizing note, R-10 presented as open nine days after it was ruled on, and 'aw find specs --status' recorded as broken at authoring and STILL broken (root-caused to a branch that never reads its status filter, affecting seven record types, tracked by no backlog item). Added the honest limit that filing a review record arms a no-override refusal on the spec's own approval, including for a record that merely fails to parse.
- 2026-09-04 to-review (aw set): Authored at the maintainer's direction while answering a question about naming a review-status command. Research established that spec 25kzda (approved, Blocks-Release: next) already MANDATES spec review in Section 3.3 and already defines three deterministic checks for it by name in Section 4.8 (SPEC-REVIEW-COMPLETE, SPEC-REVIEW-TRANSITION, SPEC-REVIEW-STRUCTURE), so this is COMPLETION of approved release-gating work rather than a new proposal; hence From-Spec: 25kzda and the inherited release gate. FOUR THINGS MEASURED AT AUTHORING, not inherited: (a) no spec-review workflow exists at all - .aw/system/workflows/ has plan-review and plan-review-long, /spec states it PRODUCES rather than reviews, and /advise spec-editor yields no verdict, findings, or transition; (b) review_findings.render_review hardcodes '- Plan-Id:' and check_engine.check_review_dangling resolves it against the plans tree ONLY, so a spec review would be flagged check.review-dangling by the repository's own checker; (c) runner_shared.discover_plans walks only the two plans trees, so no selector can reach a spec however it is spelled; (d) spec to-review -> reviewed has NO entry in attention_contract.TRANSITION_AUTHORITY, so it is an UNATTESTED status flip today - an agent can set a spec reviewed with no review, no findings and no record, while the same claim on a plan is policed by check.review-finding-unescalated and the approval verdict guard. That gap is what R-11 closes and is the strongest argument in the spec, given that specs are the artifact which AUTHORIZES plans. POPULATION MEASURED so nobody reads this as throughput work: 1 plan at to-review, 2 specs at draft, 0 specs at to-review, 34 existing review records; recorded as an honest limit rather than omitted, because the justification is structural (two thirds of needs-review artifacts have no workflow) and not volume. ONE DECISION LEFT OPEN DELIBERATELY (R-10, Section 5): a new spec-review/ workflow versus generalizing plan-review/. Left to the graduating plan because it needs the code in front of it and both answers are defensible - generalizing means changing two bodies held in deliberate parity and making plan-specific machinery conditional, while forking means two rubrics. The constraint binding either answer is stated instead: the findings/verdict/record machinery stays shared exactly once, so a plan that forks the record is rejected regardless of workflow shape. Also recorded: 'aw find specs --status' silently ignores its filter at authoring (verified for all nine statuses), so anything built on it inherits the bug.

## 0. Implementation status (added at review, 2026-09-13)

READ THIS BEFORE THE REST, because the rest is written in the future tense and most of it has SHIPPED.
This spec sat at `to-review` for nine days while three plans graduated from it and executed, so a reader
taking Section 1's "none of it is implementable today" at face value would re-derive work already done.
Measured at HEAD `9697856e`:

| Requirement | State | Evidence |
|---|---|---|
| R-01, R-02 | IMPLEMENTED | `review_findings.SUBJECT_TYPES == ('ipd', 'spec')`; `render_review` writes both bullets (`review_findings.py:398-399`) |
| R-03 | IMPLEMENTED | `check_engine.check_review_dangling` resolves by declared type via `_review_subject_id_sets` and deliberately does NOT fall back to plans |
| R-04 | IMPLEMENTED | 186 review records, ALL carrying the subject pair, ZERO carrying `- Plan-Id:` as a field |
| R-05 | CONFIRMED UNCHANGED | filename grammar untouched |
| R-06 | IMPLEMENTED | `.aw/system/workflows/spec-review/` exists and is the body this review ran |
| R-07, R-08, R-09 | IMPLEMENTED as prohibitions in that body's "Three prohibitions" section |
| R-10 | DECIDED | maintainer ruling 2026-09-04: a SEPARATE `spec-review/` package; recorded with its evidence in that package's README |
| R-11, R-12 | IMPLEMENTED | `TRANSITION_AUTHORITY["->reviewed"]` carries `review_record: True`; ONE predicate `review_findings.review_attestation_missing`, consulted by `specs.py`, `status_set.py` and `check_engine.check.spec-review-unattested` |
| R-13 | HOLDS | grandfathering is structural (the table is consulted only at transition time), not a cutover date |
| R-14, R-16 | IMPLEMENTED | exactly one `def needs_review` in the package (`run_selection_policy.py:542`), derived from the dispatch table |
| R-15 | IMPLEMENTED AND OPERATOR-REACHABLE | `aw <host> run reviews --type spec` selects the specs the shipped predicate answers `needs_review` True for; `--type` is registered on BOTH hosts' `start` and `resume` parsers from the shared `RUN_POLICY_FLAGS` table and threaded to `sweep_review_candidates_for_type` (`ui8b9b`, `tests/test_run_flag_surface.py::TypeScopedReviewSweepTests`) |

Delivered by `eyh1fu` (the record), `5slbpi` (the workflow plus the attestation), `wpomxa` (the
gating-predicate rename) and `ui8b9b` (R-15's operator surface), all `- Status: executed`.

THE R-15 ROW IS PHRASED ON THE PREDICATE, NOT ON A POPULATION, AND THAT IS DELIBERATE. It previously
read that the sweep "returns the four `to-review` specs", and that measurement rotted TWICE inside ten
days: by the time `ui8b9b` was reviewed the sweep returned `[]` (the same spec-review round that filed
`ui8b9b` advanced all four of those specs to `approved`), and by the time it was executed the sweep
returned one spec (`z7nbn1`, then at `to-review`). Every one of those three answers was correct for its
day, which is the point: a spec asserting a live population states something that becomes false without
anyone editing any code. So this row states WHAT THE SWEEP DECIDES and cites the tests that prove it,
and a reader wanting today's population runs the command.

WHAT IS NOT DONE, stated precisely because the distinction is easy to lose now that the row is green:
type-scoped SELECTION ships and per-type EXECUTION does not. `aw <host> run reviews --type spec` selects
the specs awaiting review, and a run then REFUSES to queue them
(`runner_shared.refuse_unrunnable_selected_types`), because a run queue entry is plan-shaped: the
manifest is compiled from the plans trees, the queue builder resolves each entry as an IPD, and
`resolve_plan_path` fails OPEN on a non-plan path, so queueing a spec would hand it to plan-shaped code
SILENTLY. That refusal names the selection it resolved, so the capability is usable even though the run
cannot act on it. Spec `z7nbn1` (universal artifact dispatch) owns the remainder and carries its own
`- Blocks-Release: next`. Section 6 states this limit.

WHERE THE RELEASE GATE LIVES NOW, and why it is no longer on this spec. This spec carried
`- Blocks-Release: next` while its work was outstanding. On 2026-09-13 the maintainer ruled that a release
gate belongs on a PLAN rather than on a spec, and that the spec's field is cleared once the plan carrying
it is filed. TWO plans now carry it, because the same ruling split R-15's remainder in half:

| Artifact | Carries | State |
|---|---|---|
| `ui8b9b` (`specsweep` Order 01) | R-15's SELECTION half: register `--type` on both runners so a spec sweep is operator-reachable | `executed` 2026-09-23; the gate is discharged with the work |
| spec `z7nbn1` (universal artifact dispatch) | R-15's EXECUTION half: how the runner dispatches a non-plan artifact | `- Blocks-Release: next`; SUPERSEDED plan `mng63x` on 2026-09-18 and inherited its gate |

So clearing this spec's field lost no gate, and the EXECUTION half's carrier has since MOVED. The
maintainer ruled on 2026-09-13 that the execution half needed DISCUSSION before it was built, so it was
filed as design-first plan `mng63x`; that discussion produced spec `z7nbn1`, which superseded `mng63x` on
2026-09-18 per its own OQ-03 and carries `- Blocks-Release: next` forward. A reader chasing the execution
half must therefore follow `z7nbn1` and not `mng63x`, which is retired in
`.aw/records/plans/superseded/`. The design-first instruction was honored rather than dropped: it
produced a spec, which is the discussion the maintainer asked for, instead of an unreviewed
implementation.

THE SPEC IS STILL WORTH REVIEWING AND APPROVING RATHER THAN RETIRING, because it is the contract those
three executed plans were built against and the two new ones are written against. What review must NOT do
is re-authorize the shipped work as though it were pending.

## 1. Why this exists

Spec `25kzda` is approved and gates the next release. Its Section 3.3 dispatch table states, for a spec
at `to-review`: "Run spec review; apply corrections; tool-set `reviewed`; redispatch." Its Section 4.8
goes further and defines three deterministic checks for that action by name, `SPEC-REVIEW-COMPLETE`,
`SPEC-REVIEW-TRANSITION`, and `SPEC-REVIEW-STRUCTURE`, each with an exact failure message and recovery
command.

None of it was implementable AT AUTHORING (2026-09-04), because there was no spec review to run. The gap
was not a missing flag or an unwired predicate; it was three missing mechanisms, each independently
blocking the action. All three are now closed (Section 0); the diagnosis is preserved in the past tense
because it is the reasoning the design rests on:

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

RE-MEASURED 2026-09-13: 6 plans and 4 specs at `to-review`, this spec among them. The structural argument
still carries the decision and the volume argument is still the weaker one, but the population is no longer
near-empty, and this spec is now itself a member of the set it exists to make reviewable.

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
  mechanism that produces divergence. EVERY existing review record is migrated in the same change that
  introduces the new field, mechanically, with the migration shown. The population is DERIVED from
  `review_findings.iter_review_files` at execution, never asserted as a literal: it was 34 when this
  requirement was written, 36 when the implementing plan was reviewed, and 186 on 2026-09-13, because
  filing a review adds one. A migration validated against a hardcoded count fails for a reason unrelated
  to the change, or passes only because someone edited the number.
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
  DECIDED 2026-09-04 by maintainer ruling: a SEPARATE `spec-review/` package. The evidence, the rejected
  option's measured cost (three plan-only obligations becoming six conditionals across two bodies held in
  deliberate parity), and the accepted cost (rubric drift, mitigated by a test) are recorded in
  `.aw/system/workflows/spec-review/README.md`. Section 5's tradeoff is preserved as the reasoning; the
  question it left open is closed.

### 2.3 The transition becomes attested

- **R-11** A spec's `to-review -> reviewed` transition MUST require evidence that a review occurred:
  specifically, a conforming review record whose `Subject-Id` is that spec. This closes the gap in
  `TRANSITION_AUTHORITY` and makes the spec transition as attested as the plan one.
- **R-12** The attestation MUST fail closed and MUST be enforced by the same shared predicate that the
  checker, the setter, and any hook consult. One predicate, several call sites; never a second copy.
- **R-13** Enforcement MUST NOT retroactively invalidate any spec already past `to-review` without a
  review record. Existing specs are grandfathered exactly as `25kzda` Section 2.11 grandfathers
  pre-cutover IPD dependency statements: the requirement binds transitions performed AFTER the change, not
  history. THE MECHANISM IS STRUCTURAL, NOT A CUTOVER DATE: the authority table is consulted only at
  transition time, so a spec that never transitions again is never re-tested. (At authoring the affected
  population was 15 `implemented` plus 5 `approved`; on 2026-09-13 it is 15 `implemented`, 7 `approved`
  and 1 `implementing`. The count is stated as context, never as the invariant, because grandfathering
  must hold for whatever the population turns out to be.)

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

EVERY CRITERION NAMES THE REQUIREMENTS IT COVERS, added at review because the mapping was absent: the
requirements carry stable ids expressly so a criterion and a later plan can cite them, and no criterion
did. The bijection is stated at the end of this section so an uncovered MUST is visible rather than
inferred.

- **A-01** (R-06) A spec at `to-review` can be reviewed end to end, producing a findings table, a verdict,
  a conforming review record, and a tool-authored transition to `reviewed`.
- **A-02** (R-03) `aw check all` reports no `check.review-dangling` for a spec review whose subject exists,
  and still reports it for a review whose subject does not.
- **A-03** (R-01, R-02, R-04) EVERY review record discovered by `review_findings.iter_review_files` carries
  `Subject-Id` and `Subject-Type`, no record retains a `- Plan-Id:` field, `Subject-Type` holds only a
  value in the closed vocabulary, and `aw check all` is no worse than its pre-change baseline. The
  population is DERIVED at execution, never asserted as a literal: it was 34 at authoring, 36 during the
  implementing plan's review, and 186 on 2026-09-13, because every review adds one. A criterion phrased as
  equality against a count would fail for a reason unrelated to the change.
- **A-04** (R-07, R-08) No spec acquires a `- Readiness:` field, and no spec's status or workflow history is
  written by anything other than `aw specs set` / `aw specs note`.
- **A-05** (R-11, R-12, R-13) Setting a spec `reviewed` without a conforming review record is REFUSED, with
  a message naming the missing record and a recovery command; setting it WITH one succeeds; the refusal
  comes from the ONE shared predicate (proven by grep, not by behavior alone); and a pre-existing
  `implemented` or `approved` spec is unaffected.
- **A-06** (R-14) The needs-review predicate has exactly one implementation. A grep shows no second copy in
  either runner, and both runners plus the preview consult it.
- **A-07** (R-16) A complete `draft` item appears in the needs-review set exactly when the dispatch table
  routes it to review, demonstrated for both a plan and a spec, so the sweep and the table agree.
- **A-08** (R-09) `25kzda`'s three named spec checks (`SPEC-REVIEW-COMPLETE`, `SPEC-REVIEW-TRANSITION`,
  `SPEC-REVIEW-STRUCTURE`) are each satisfiable, with the evidence each one inspects actually produced, and
  the structural gate exercised is `aw specs check` rather than `aw ipd lint`.
- **A-09** (R-15) A CALLER passing the spec type enumerates the specs at `to-review` from the specs tree.
  State plainly, as a limit and not a success, whether an OPERATOR can reach it: at 2026-09-13 they cannot,
  because `--type` is registered on neither host. A criterion satisfied only at the function boundary must
  say so, or a green result reads as a shipped feature.
- **A-10** (R-05) The review filename grammar is unchanged, proven by the naming authority still building a
  review name from the subject's setid and id6, with only docstrings corrected.
- **A-11** (R-10) The workflow-shape decision is RECORDED with its evidence and its accepted cost, in a
  durable place a later reader will find, so it is not silently re-litigated.

REQUIREMENT COVERAGE, which is the check the ids exist for: R-01 A-03; R-02 A-03; R-03 A-02; R-04 A-03;
R-05 A-10; R-06 A-01; R-07 A-04; R-08 A-04; R-09 A-08; R-10 A-11; R-11 A-05; R-12 A-05; R-13 A-05;
R-14 A-06; R-15 A-09; R-16 A-07. Every MUST is covered and every criterion maps back; A-09 through A-11
were added at review to close R-05, R-10 and R-15, which had no criterion at all.

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

## 5. The one decision left to the graduating plan (SINCE DECIDED)

DECIDED 2026-09-04: a SEPARATE `spec-review/` package (see R-10). This section is retained because it is
the reasoning the ruling weighed, not an open question. The tradeoff as originally stated:

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
  structurally, not by throughput, and a graduating plan should not claim otherwise. (10 on 2026-09-13,
  which strengthens the case without changing which argument carries it.)
- **Grandfathering leaves a permanent honest hole.** The specs already past `to-review` without a review
  record never acquire one, so the attestation is a going-forward invariant only. Any consumer that treats
  "has a review record" as a property of all reviewed specs will be wrong about history.
- **`aw find specs --status` is broken and STILL broken.** It silently ignores its filter, returning every
  spec for every value. Re-verified 2026-09-13: `--status to-review`, `--status implemented` and an invalid
  `--status bogusvalue` each return all 32 specs at exit 0. Root cause located: `cli._find_type_records`'s
  "All other types" branch never consults `explicit_flags.status`, unlike the `plans` and `research`
  branches which each call a `query(...)` helper, so the defect affects SEVEN record types, not just specs.
  The executed plan `5slbpi` deliberately AVOIDED the filter rather than fixing it (its D4, the fix being
  outside its scope) and used `check_engine._iter_spec_records` instead. Anything built on the filter
  inherits the bug; it is not tracked by any backlog item, which is itself a gap.
- **R-15's operator surface SHIPS, and this bullet used to say the opposite.** It read that the sweep
  "works when called with the spec type, and `--type` is registered on neither host, so no invocation can
  supply one". Executed plan `ui8b9b` registered `--type` on BOTH hosts' `start` and `resume` parsers from
  the shared `RUN_POLICY_FLAGS` table and threaded it to the sweep, so `aw <host> run reviews --type spec`
  is now a real invocation. The flag's grammar is still `25kzda` 2.2/2.3's, and `uyeko5` still excluded it
  deliberately; what changed is that a later plan took ownership of the row rather than the exclusion
  standing forever.
- **SELECTING a spec is STILL not RUNNING one, and this is now the whole of R-15's remainder.** The limit
  did not go away with the flag; it moved from "you cannot ask" to "you can ask and the runner refuses".
  Measured while filing `mng63x` and re-verified while executing `ui8b9b`: the manifest is compiled from
  discovered plans only, a queue entry is plan-shaped and its path resolves through the plans tree, and two
  of the three declared spec actions are not review turns at all (`approved` means author IPDs from the
  spec, and `implementing` dispatches children and has no dispatch row). A `--type spec` run therefore
  SELECTS the specs and then refuses to queue them, NAMING what it selected, rather than handing a spec to
  plan-shaped code - which would fail SILENTLY, because `resolve_plan_path` fails open on a non-plan path.
  Spec `z7nbn1` owns the remainder. Do not read a green R-15 as "the runner can review a spec".
- **The attestation is only as strong as the record.** A review record that fails to PARSE is treated as
  BLOCKING, so a malformed record refuses its own spec's approval with a parse code rather than a finding.
  That is intended fail-closed behavior, and it means a careless reviewer can block a maintainer's spec.

## 7. Non-goals

- The `aw <host> review` alias, the `reviews` selector, and the draft admission gate: `25kzda`
  Sections 2.1, 2.4a, 2.5a. Consumed here, not specified here.
- The runner flag surface: plan `uyeko5`, which built the shared `RUN_POLICY_FLAGS` table and registered
  `--allow-drafts`. `--type`'s registration in that table is plan `ui8b9b` (it was an explicitly NAMED
  exclusion of `uyeko5`, not an oversight, and `ui8b9b` moved the row rather than adding a second one).
- Multi-type SELECTION and the mixed-type gate wiring: `25kzda` Sections 2.2/2.3/2.5, gate built by
  executed plan `6lu3rq`, wiring owned by `uyeko5`.
- Reviewing backlog, research, release, or walkthrough records (D-03).
- Any change to plan-review's rubric, severity vocabulary, verdict vocabulary, or findings columns.
  Only the record's subject fields change.
- Per-type subdirectories under `.aw/records/reviews/`: that is open backlog `sv0sf3`, decided 65/35
  toward the flat layout, and it is orthogonal to the subject-field change.
