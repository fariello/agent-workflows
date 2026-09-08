- Id: jys5dp
- Status: graduated
- Blocks-Release: next
- Set: durablecapture
- Priority: high
- Work-Kind: feature
- Summary: a known unfixed defect named in an IPD's prose vanishes when the plan reaches executed: require handoff to a durable carrier, mirroring the release-gate close predicate

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan rnkqrc (to-review), which carries From-Backlog: jys5dp and inherits Blocks-Release: next.
- 2026-09-05 created (aw backlog): a known unfixed defect named in an IPD's prose vanishes when the plan reaches executed: require handoff to a durable carrier, mirroring the release-gate close predicate

THE PROBLEM, in the maintainer's words (2026-09-05): "A note in an executed IPD is 100% guaranteed
to be the same as not writing it anywhere."

That is literally true. Once a plan reaches `executed`, `aw attention` classes it `done`
(`attention_contract.py:222`), so every unfixed defect named in its prose disappears from every
"what needs attention" view - permanently, silently, with no record that anything was dropped. The
same holds for walkthroughs, which are `tracked=False` by design (`attention_contract.py:112-118`)
and get filename-only checking (`check_engine.py:28`), so a walkthrough may describe any number of
live defects and no tool will ever read a word of it.

THE RULE TO ENFORCE. Every known issue or item needing attention must live in a place that is
actually revisited: a backlog item or a plan. Not prose in a terminal artifact.

WHY "OR A TODO.md ENTRY" IS NOT ON THAT LIST. `TODO.md` holds ZERO work items today - it is a
pointer stub saying work moved to the backlog tree. Worse, it is in `SCAN_ROOTS`
(`artifact_core.py:158`) but is silently DROPPED as unclassified (`attention.py:262-277`), i.e.
invisible by construction. See the separate TODO.md retirement item.

WHY A SPEC IS NOT SUFFICIENT EITHER. `aw attention` does map spec `approved` -> `ready`
(`attention_contract.py:204`), so a spec is not invisible. But there is NO per-requirement tracking:
only a whole-spec status, no notion of partial implementation, and no join from a requirement (e.g.
"G5 [Must]") to an implementing plan. `From-Spec` validates only that the id6 resolves to A SPEC
(`check_engine.py:123-125`), never that its requirements are covered. And `implemented` requires
only a resolvable citation, not semantic verification - stated honestly at
`attention_contract.py:369-376`. So a spec can sit `approved` for weeks with half its requirements
unbuilt and nothing asks which half. Tracked separately as an open question; it must not block this
item.

THE PATTERN TO COPY - and it already exists. `evaluate_blocking_close`
(`check_engine.py:1708+`, verdict type `CloseVerdict` at `:1691-1706`) is the ONLY mechanism in
this repo that enforces "an obligation must survive in a place that is revisited". Closing a
backlog item carrying `Blocks-Release:` FAILS CLOSED unless one of three things holds:
  (1) HANDOFF - a plan carrying `From-Backlog: <id6>` and the same `Blocks-Release:`;
  (2) SATISFIED - a resolvable in-tree evidence citation;
  (3) DE-GATED - the gate is explicitly cleared.
One shared predicate backs the setter, three `aw check` rules
(`check_engine.py:105-110`, `:126-128`), and an opt-in hook, "so they cannot diverge".

GENERALIZE EXACTLY THAT SHAPE: an IPD may not reach `executed` while it names an unfixed defect,
unless that defect is (1) handed off to a durable carrier - a `backlog/open/` item or a pending plan
- (2) satisfied with cited evidence, or (3) explicitly declined with a recorded reason. Same three
escapes, same fail-closed posture, one shared predicate behind every surface.

TWO CONCRETE HOOKS, BOTH CURRENTLY DEAD CODE:

  A) `## Deferred / out of scope (with reason)` is a REQUIRED IPD section that NO TOOL READS. It is
     declared `H_DEFERRED` (`ipd_schema.py:48`) and mandatory in both `CHILD_H2_ORDER`
     (`:70`) and `ORCHESTRATOR_H2_ORDER` (`:86`), and `H_DEFERRED` appears NOWHERE in
     `ipd_lint.py` (verified: no match). The lint enforces that the section exists and is ordered,
     and never reads its contents. Every "deferred to its own IPD" row in the entire corpus is
     unverified prose. Requiring each row to carry a RESOLVABLE carrier reference is the single
     highest-value change here.

  B) THE BLOCKING-OPEN-QUESTION GATE RUNS AT `pre-execution` ONLY, never at `pre-transition`
     (`ipd_lint.py:681-693` versus `:694-724`; the exclusion is deliberate and documented at
     `:1078`). `pre-transition` checks only E-item state, V-item results, and evidence presence. So
     a blocking open question gates the START of work and not the CLAIM THAT IT IS DONE. Worse, an OQ
     is "resolved" by any non-empty prose: `open_question_error` (`ipd_schema.py:1338-1354`)
     requires only that a rationale be non-empty, and its own docstring says "Semantics are the
     reviewer's job" (`:1341`). There is no `Backlog:` field in `OQ_FIELDS`
     (`ipd_schema.py:1329-1335`), which `:1314-1318` records as having "NO consumer anywhere in
     the codebase (it is defined here and never read)". `ipd_lint.py` has zero occurrences of
     `From-Backlog`: the linter has no concept of backlog linkage at all.

THE NEAREST PRECEDENT, AND EXACTLY WHERE IT STOPS. `check.review-finding-unescalated`
(`check_engine.py:2630+`, evaluator `evaluate_review_finding_escalation` at `:2702`) enforces
that an unfixed review finding at or above a severity threshold must be escalated into a
`Blocking: yes` open question naming its id. Its design properties are the right ones to reuse: one
shared evaluator serving both `aw check` and `aw ipd lint` "so the sweep and the checkpoint gate
cannot drift apart" (`:2711-2715`); TYPED FIELD MATCHING, never prose, because "a substring search
over prose would be both spoofable ... and brittle" (`:2645-2647`); and a configurable threshold
(`:2742-2746`).

But it escalates a finding into an open question INSIDE THE SAME PLAN. It never requires a durable,
attention-visible carrier. So once that plan is `executed`, the OQ is frozen in a terminal artifact
and the finding is gone from every attention view even though it was never fixed. Its own comment
concedes the adjacent weakness: "this design blocks one step removed from the finding"
(`:2624-2627`). THIS ITEM IS THAT REMAINING STEP.

MANDATORY ROLLOUT CAUTION - do not skip this. When zero existing artifacts satisfy a new
requirement, a fail-closed rule mass-fails the corpus on day one. `check.review-finding-unescalated`
chose SILENCE on an absent artifact for exactly this reason: "zero .review.md files exist against
428 plan files, so a fail-closed absent case would mass-fail the entire corpus on day one"
(`check_engine.py:2721-2732`). There are ~484 plans here. So ship this as `warning` for existing
plans and `error` for newly authored ones (or gate on a date/format-version boundary), or the first
`aw check` run blocks everything.

IMPLEMENTATION NOTES.
  * Typed fields only. Match a structured carrier reference; never grep prose for "TODO" or
    "future work". The one TODO/FIXME scanner that exists (`verify_roles.py:1670-1714`) is
    diff-scoped, unwired to `aw check`, and looks for residual debug markers - not applicable.
  * Severity vocabulary must be shared, not forked (see `review_findings.is_gating`,
    `review_findings.py:694-708`).
  * CI already runs `aw check plans` fail-closed (`.github/workflows/tests.yml:153-155`), so a new
    plans rule inherits enforcement automatically. Note `check backlog` is only ADVISORY there
    (`:166-170`); consider whether that should change alongside this.
  * `aw check` and `aw ipd lint` must call ONE predicate, per the precedent above.

RELATED GAPS FOUND WHILE INVESTIGATING (each may deserve its own item):
walkthroughs are untracked and names-only checked; source-code comments are never scanned
(`artifact_core.py:174` limits reading to .md/.txt); `releases` is a declared tracked tree with NO
scan root, so the one release record is invisible to `aw attention`; the `reviews` tree has no
TreePolicy at all.
