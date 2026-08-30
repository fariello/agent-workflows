# IPD: Record self-resolved decisions in the review artifact so a wrong turn is auditable

- Date: 2026-08-29
- Kind: child
- Concern: Agents are instructed to resolve obstacles themselves rather than refuse, but a self-resolved judgement call is recorded nowhere the maintainer will see it, so an agent can take a road trip in the wrong direction invisibly.
- Scope: Make a reviewer or executor RECORD each decision it made instead of asking, into the tracked `## Decisions` section defined by `15zvu6`, and give the maintainer one command to audit them. (The drafted second clause, "fix the location defect in the gitignored autonomous-decisions register", was REMOVED at review: F-7 refutes the premise and E-05 now leaves `set_records.py` untouched.)
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md, agent_workflows/review_findings.py, agent_workflows/reviews.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/check_engine.py, .aw/records/reviews/README.md, tests/test_review_decisions.py, tests/test_plan_review_parity.py
- Item-Dependencies: executed:15zvu6
- Status: reviewed
- Set: revgate
- Order: 4
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: c621h9
- Blocks-Release: next

## Workflow history
- 2026-08-30 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 fixed in place (wrong long-variant file; three unstated CLI declaration gates; unspecified selector + absent-tree crash; E-06 bundled build+test+parity and the check rule lacked placement/registry/grandfathering/fail-mode; duplicate parity harness; own history order invalid)

- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored on maintainer instruction that decisions which would have been open questions, but for the resolve-before-refusing rule, must remain auditable.
- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make "the agent decided this itself" a durable, reviewable fact. The resolve-before-refusing rule is
right, but it converts questions into silent choices; this plan keeps the rule and removes the silence,
so a maintainer can find a wrong turn after the fact instead of discovering it in the code.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make recording mandatory, not optional

- [ ] E-01 Amend the plan-review workflow body (`.aw/system/workflows/plan-review/plan-review.md`,
      Step 3.1 "Build the question set" and 3.2, which today say to resolve from authoritative evidence
      and cite the source) to require that EVERY question resolved from evidence rather than asked is
      recorded as a row in the review artifact's `## Decisions` section. State the rule positively: a
      resolved question is not "gone", it is a recorded decision with an alternative that was rejected
      and a basis that can be checked. Keep the existing citation requirement.
  - Depends on: none
  - Expected outcome: the workflow instruction demands a decision row for each self-resolution.
  - Execution state: pending

- [ ] E-02 Mirror the same amendment into the long variant, which the manifest states is kept in
      DELIBERATE PARITY with the single-file variant. Parity is a documented property, so an
      instruction added to one and not the other is a defect.
      DO NOT EDIT `plan-review-long/plan-review-long.md`, which the draft named (F-11, the identical
      defect sibling `plqjt7` hit as its own F-6). That file is a 92-line ORCHESTRATOR: it carries the
      memory kernel, the parallel-lane note, and a three-line "Steps" list (`:62-66`), and contains NO
      question-resolution step at all (verified: zero occurrences of "question set" or "Decisions").
      Editing it would leave long-variant reviewers with no instruction while a naive parity check
      passed. The instruction that corresponds to E-01's Step 3.1/3.2 lives in
      `plan-review-long/03-resolve-and-finalize.md`, section "1. Resolve open questions" (`:8-52`,
      whose `:17` is the "Resolve questions already answered by authoritative evidence and cite it"
      line E-01 amends). Amend THAT file. Also amend `02-review-and-revise.md` "1. Record findings"
      (`:18-37`) if and only if E-01's edit touches the single-file variant's Step 2.2; say which you
      did and keep the two variants' text equivalent either way.
  - Depends on: E-01
  - Expected outcome: both variants carry equivalent decision-recording wording, with the long
    variant's text in the STEP file that actually instructs the reviewer, not in the orchestrator.
  - Execution state: pending

- [ ] E-03 Require a `Reversible: yes|no` judgement on each decision row and require that an
      IRREVERSIBLE self-made decision ALSO be surfaced, not merely logged: it must either be raised as a
      blocking open question, or carry an explicit note that the maintainer was told. The distinction is
      the point of the whole plan: a reversible wrong turn costs a rewrite, an irreversible one cannot
      be undone, and the resolve-before-refusing rule must not silently authorize the latter.
  - Depends on: E-01
  - Expected outcome: the instruction distinguishes reversible from irreversible self-resolution and
    escalates the irreversible case.
  - Execution state: pending

### Task group 2: give the maintainer one command

- [ ] E-04 Add a read-only `aw reviews decisions [<selector>]` verb that prints the recorded decisions
      for one plan, a Set, or the whole tree, reading the `## Decisions` sections through `15zvu6`'s
      parser. Support `--agent`/`--json` per the house machine-output contract, and `--irreversible` to
      filter to the rows that matter most. Read-only: it makes no writes. Put the implementation in a new
      `agent_workflows/reviews.py` rather than inside `cli.py`, matching the owner-verb shape used by
      `specs`/`backlog` (a module with a `run_*` entry point that `cli.py` dispatches to); emit through
      the `CommandResult`/`select_output`/`get_renderer` pipeline rather than a bare `print`.
      NOTE THIS CREATES THE `reviews` CLI NAMESPACE: verified that `aw reviews` is NOT a valid top-level
      command today, and that `15zvu6` does NOT add one (its `Scope-Paths` has no `cli.py`), so this verb
      brings the noun into existence. Register it at the two `cli.py` edit points AND declare it, because
      the declaration is MANDATORY, not optional: every parser leaf must carry an entry in
      `command_surface.COMMAND_INVENTORY` or `find_undeclared_leaves` reports it. Model the declaration
      on an existing READ-ONLY verb (a `query`/`read` class, NOT the `mutation`/`dry_run_default` shape
      used by `specs new`), since this verb writes nothing. `command_surface.py` is in `Scope-Paths`.
      BE HONEST ABOUT THE BASELINE: `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`
      is ALREADY FAILING with 59 undeclared leaves (re-measured at review at `451739c`: still exactly 59,
      F-9), so it will not go green from your change. Do NOT declare the other 59. Prove only that
      `reviews decisions` is not in the reported set and that the count did not grow.
      THREE MORE DECLARATION FACTS, MEASURED AT REVIEW so the "declare it" instruction is actually
      executable (F-12). (a) `test_empty_error_renderer_classification_consistency`
      (`test_command_surface_declarations.py:117-149`) branches on a HARDCODED literal set of query
      commands and requires `empty_error_renderer="renderer_boundary"` for everything else, so declaring
      `reviews decisions` with `shared_empty_result` FAILS that test while `renderer_boundary` passes.
      This collides with CONTRIBUTING.md item 8, which tells a query verb to use the shared empty-state
      path. RESOLVE IT EXPLICITLY: declare `renderer_boundary` (the test is the mechanical gate, and 20
      of 21 existing `read` leaves already do this), and if you want the shared empty renderer's UX, add
      `reviews decisions` to that test's literal query set in the SAME commit so the two agree. Do not
      leave the contradiction unstated. (b) `command_class="read"` with `exit_contract` containing `1`
      makes the conformance matrix REQUIRE a `domain_failure` scenario
      (`tests/conformance_matrix.py:76-93`); a read-only audit printer has no findings exit, so declare
      `exit_contract=(0, 2)` like `find`/`ipd board` (`command_surface.py:377`, `:616`) unless you
      genuinely implement an exit-1 case. (c) `tests/test_cli.py::SubcommandDescriptionTests` requires
      EVERY subparser (the `reviews` family node AND the `decisions` leaf) to carry a `_DESCRIPTIONS`
      entry strictly longer than its `help=` text, or it reports "empty description"; that test is also
      already red (47 gaps at review), so again prove only that YOUR two paths are absent from its
      report. Add both entries to `_DESCRIPTIONS` (`cli.py:52`).
      SPECIFY THE SELECTOR AND THE DISCOVERY PATH, which the draft left as a bare `[<selector>]`
      (F-13). Resolve selectors through the ONE shared resolver `selectors.resolve`/`resolve_selectors`
      (`selectors.py:347`, `:503`), never a hand-rolled match: the id6/setid/status/stem/substring
      precedence and the ambiguity policy are already defined there. Note the resolver reads the
      REVIEWED PLAN's id6 out of the review file's own front matter only if the writer emits a `- Id:`
      bullet; `15zvu6` E-02 specifies `- Plan-Id:` instead, so state plainly which selector kinds work
      (`plan-id6` will resolve via `stem`/`substring` on the clustered filename, which embeds the plan's
      id6) and do not promise an `id6` match the artifact cannot support. Enumerate files through the
      record-path authority `15zvu6` E-09 registers; do NOT hardcode `.aw/records/reviews`. AND HANDLE
      THE PRE-DEPENDENCY REALITY: this Set's Order 01 is not executed yet, so at execution time
      `selectors.record_dirs(repo, "reviews")` returns `[]` (verified at review). An empty tree must
      produce the clean "no decisions recorded" empty state, exit 0, NOT a crash and NOT exit 1.
  - Depends on: none
  - Expected outcome: `aw reviews --help` and `aw reviews decisions --help` work, the verb is declared in
    `COMMAND_INVENTORY` with a read-only class and an exit contract the matrix can cover, both parser
    nodes carry `_DESCRIPTIONS` entries, `find_undeclared_leaves` does not report it, the pre-existing
    59 undeclared leaves and 47 description gaps are untouched, selector resolution goes through the
    shared resolver, an absent `reviews/` tree yields a clean empty state at exit 0, and a maintainer can
    answer "what did the agents decide without asking me?" in one command instead of grepping the corpus.
  - Execution state: pending

- [ ] E-05 DO NOT "FIX" `set_records`; it is not the defect this plan thought it was, and touching it
      would damage a working design. The draft called `set_records.py:152-153` a LOCATION DEFECT because
      `.aw/workflow-artifacts/` is gitignored. That premise is REFUTED by the module itself (F-7): the
      untracked projections are DELIBERATE ("Local run projections written under the untracked
      run-artifacts dir (the local authoritative run convention)") and they already HAVE a tracked
      counterpart, because the same module writes a TRACKED walkthrough to `.aw/records/walkthroughs/`
      (`render_walkthrough:166`, `write_walkthrough:200`) and `promote_local_checkpoints:411` exists
      precisely to promote an untracked decision checkpoint into that tracked walkthrough BEFORE
      releasing another lane, with the stated purpose that "a crash never loses a recorded decision".
      So the untracked/tracked split is the same disposable-projection-plus-durable-record convention
      this plan cites as its own precedent, already implemented. There is no lost-decision defect to fix.
      Two further facts remove the motive: `set_records` is the SET-COORDINATION register (execset Order
      02), not the review path, and `write_local_projections` has NO production caller at all today (only
      two tests call it), so it is not the surface through which plan-review decisions would flow.
      WHAT THIS ITEM ACTUALLY OWES: nothing in `set_records`. Instead, make the review path's durability
      explicit where it belongs, which is the tracked `## Decisions` section in `15zvu6`'s `.review.md`
      artifact that E-01 through E-04 already use. State in the review artifact README (see Spec sync)
      that the tracked `.review.md` is the source of truth for review-time decisions and that
      `set_records`' untracked projections are a DIFFERENT, Set-coordination surface with its own
      tracked walkthrough. If you find a real gap in the Set path while doing this, file it as a separate
      backlog item; do NOT widen this plan into `set_records.py`.
  - Depends on: E-04
  - Expected outcome: `set_records.py` is UNMODIFIED (prove it with a diff); the review path's tracked
    source of truth is documented as the `.review.md` `## Decisions` section; and the distinction between
    the two registers is recorded so a later agent does not "fix" the Set one either.
  - Execution state: pending

### Task group 3: prove it cannot silently regress

- [ ] E-07 BUILD THE `aw check` RULE THIS PLAN NEEDS, as its own execution item. The draft buried this
      inside E-06's test item, which is a category error: E-06 is the test surface, and an item that both
      builds a production rule and writes the suite is two concerns in one pass (right-sizing). The
      draft's deeper defect was that NO E-item created the rule at all while E-06 demanded evidence of it
      firing (F-8; verified no sibling owns it: `plqjt7` owns the findings-threshold rule and `7nkcgp` the
      dependency cascade, and neither mentions decisions or `Reversible`).
      Add `check.review-decision-unescalated` to `check_engine.py`: a CURRENT-round decision row with
      `Reversible: no` and no escalation (neither a `Blocking: yes` open question in the reviewed plan nor
      an explicit maintainer-told note on the row) is reported.
      WIRE IT AT A NAMED POINT and follow the three registration facts the sibling review already
      established for the identical shape (F-14, so this plan does not repeat `plqjt7`'s F-7):
      (1) PLACEMENT. Put it in the plans-type content path beside `check_ipd_dependencies`
      (`check_engine.py:441`), which is reached by BOTH `aw check plans` and the `aw check all` fan-out
      exactly once. Do NOT use the collisions-only cross-tree block (`:1187-1214`), which runs only in the
      full sweep. Wrap it in the same `try/except` fail-isolated shape its neighbours use.
      Note the consequence honestly: the rule is keyed off the PLAN, so it fires while checking plans even
      though the artifact it reads is a review; that is deliberate, matching the "every dependency source
      is an IPD" reasoning already documented at `:436-438`. `aw check reviews` is NOT a valid type today
      (the `type` choices are plans/specs/prompts/research/backlog/walkthroughs/roadmaps/comms/releases;
      verified), and adding one is OUT OF SCOPE for this plan.
      (2) REGISTRY. Register the id in `RULE_REGISTRY` (`check_engine.py:85-171`). This is NOT optional
      bookkeeping: an unregistered id silently falls back to `_DEFAULT_RULESPEC` (`:173`), which is
      `error`/`ASSURANCE_REPOSITORY`/`DET_DETERMINISTIC` with an EMPTY invariant id, so an unregistered
      rule would be reported at ERROR and contradict this plan's report-only posture BY DEFAULT. Declare
      `RuleSpec("warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "<invariant or \"\">")`, with
      `check.orphaned-live-blocker` (`:117-119`) as the in-tree advisory precedent. State which catalog
      invariant it traces to, or `""` with a one-line reason if none fits (the catalog is spec `pqsx96`;
      I-07/I-08/I-09 are release-gate/dependency/naming and none covers review decisions).
      (3) GRANDFATHERING. Scope the rule to PENDING-lane plans, following `check_ipd_draft_ready`
      (`:866-867`) and `check_lifecycle_transitions` (`:918-923`), so the terminal-plan corpus is never
      retroactively litigated.
      (4) FAIL-OPEN VS FAIL-CLOSED, stated rather than inherited from an enclosing `except`: an ABSENT
      review artifact is SILENT (mandatory - zero `.review.md` files exist today, so a fail-closed absent
      case would mass-report the whole corpus), a MALFORMED artifact is REPORTED via `15zvu6`'s parser
      diagnostics, and neither case may raise.
      Enumerate review files through the record-path authority `15zvu6` E-09 registers, never a hardcoded
      `.aw/records/reviews` string.
  - Depends on: E-03, E-04
  - Expected outcome: the rule exists, is registered at `warning` with a stated invariant, fires on an
    unescalated `Reversible: no` row in a pending-lane plan's current round, is silent on an absent
    artifact, reports a malformed one, and is reached by both `aw check plans` and `aw check all`.
  - Execution state: pending

- [ ] E-06 Write `tests/test_review_decisions.py` proving: a decisions row round-trips; the
      `aw reviews decisions` verb prints a recorded decision and exits per the house contract;
      `--irreversible` filters correctly; the machine mode is ANSI-free and parses as JSON; and the
      adversarial case, that E-07's rule REPORTS a `Reversible: no` row with no escalation and does NOT
      fire on an escalated one (a rule never seen to fire, and never seen to stay quiet, is not covered).
      Add E-07's three state cases: absent artifact SILENT, malformed artifact REPORTED, neither raising.
      Add E-04's empty-tree case: `aw reviews decisions` on a repo with no `reviews/` tree exits 0 with a
      clean empty state.
      USE ISOLATED FIXTURE REPOS, not this checkout's live state (the repo has a known live-state-
      asserting test defect class that `i79rgh` exists to fix; a rule test that scans the real
      `.aw/records/` would be order-dependent and would break the moment a real review lands).
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-07, E-08
  - Expected outcome: the mechanism is covered by fixture-isolated tests, and the adversarial guard is
    demonstrated both firing and staying quiet.
  - Execution state: pending

- [ ] E-08 Put the workflow-body PARITY assertion in the file that already owns this exact parity pair,
      rather than starting a second parity harness in `tests/test_review_decisions.py` as the draft did.
      `tests/test_plan_review_parity.py` exists for precisely this purpose: it holds `PLAN_REVIEW`,
      `PRL_02`, and `PRL_03` handles (`:18-23`) and already asserts content parity across the single-file
      body and the long variant's STEP files (`:147-208`). A duplicate harness is the duplicate-mechanism
      pattern the house rules forbid, and it would drift from the one the suite already trusts.
      Assert that the decision-recording instruction from E-01 is present in BOTH `plan-review.md` AND
      `03-resolve-and-finalize.md` (plus `02-review-and-revise.md` if E-02 amended it), so E-02 cannot
      silently drift. `tests/test_plan_review_parity.py` is in `Scope-Paths`.
  - Depends on: E-01, E-02
  - Expected outcome: the parity guard lives in the existing parity module, covers the step file rather
    than the orchestrator, and fails if either variant loses the instruction.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The mechanism partly EXISTS and is well shaped: `set_records.py:41-42` defines `DECISIONS_FILE` and
  `OPEN_QUESTIONS_FILE`, `write_local_projections` (`:143-158`) writes them, and real examples under
  `.aw/workflow-artifacts/assess-*/` show a genuinely useful format (concern/scope, method, verdict
  rationale, what was intentionally NOT done and why, assumptions, open questions for the user). This
  plan should REUSE that VOCABULARY (the field shape) rather than invent a new one.
- `.aw/workflow-artifacts/` is gitignored (`.gitignore:68`), but that is NOT a defect and E-05 must not
  "fix" it (F-7, corrected at review). The untracked projections are the deliberate "local authoritative
  run convention" and they already have a tracked counterpart: `set_records` writes a TRACKED walkthrough
  and `promote_local_checkpoints` promotes untracked decision state into it so a crash never loses a
  recorded decision. That module is also the SET-COORDINATION register, not the review path, and
  `write_local_projections` has no production caller. Reuse its format; leave its plumbing alone.
- `plan-review` does NOT use the register today: `.aw/workflow-artifacts/` contains a `release-review`
  directory but no `plan-review` one, so review-time self-resolutions have never been recorded through
  this path.
- The plan-review manifest row states the long variant is kept in "deliberate parity" with the
  single-file one, which is why E-02 exists and why E-06 asserts parity mechanically.
- The repo already treats a private/scratch copy as disposable and the tracked copy as the source of
  truth (the AGENTS.md rule about brain/memory dirs). E-05 follows that precedent instead of inventing
  a new durability rule.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Self-resolution is already widespread and already unauditable. RE-MEASURED TWICE: the figures are a live measurement, not a constant, and they GREW at each reading, which strengthens rather than weakens the case. Treat them as a measurement to redo, never as a constant to paste. | plan text: 112 entries across 92 plans. First review at `93da8af`: 115 entries across 95 plans. Second review at `4ee5282`: 117 `Resolution or deferral rationale: RESOLVED` entries across 96 plans; no consolidated view exists |
| F-11 | ADDED AT REVIEW (HIGH): E-02 named the WRONG long-variant file, the identical defect the sibling `plqjt7` caught as its own F-6 and fixed there, which this plan then reproduced. `plan-review-long/plan-review-long.md` is a 92-line ORCHESTRATOR with no question-resolution step at all, so the drafted edit would have left long-variant reviewers with NO decision-recording instruction while a naive parity check passed. The instruction corresponding to E-01's Step 3.1/3.2 lives in `03-resolve-and-finalize.md` section "1. Resolve open questions". E-02 rewritten to name the step file(s); `Scope-Paths` corrected. | `plan-review-long.md` is 92 lines, steps only listed at `:62-66`; `grep -c 'question set\|Decisions'` in it returns 0; `03-resolve-and-finalize.md:8-52` is the resolve step, `:17` the "Resolve questions already answered by authoritative evidence and cite it" line; `plqjt7` F-6 records the same correction |
| F-12 | ADDED AT REVIEW (HIGH): E-04's "declare it in `COMMAND_INVENTORY`" instruction was not executable as written, because three further gates bind a new leaf and two of them CONTRADICT the plan's stated intent. (a) `test_empty_error_renderer_classification_consistency` branches on a HARDCODED literal query set and demands `renderer_boundary` for anything outside it, so declaring the read-only verb with `shared_empty_result` (what CONTRIBUTING item 8 asks of a query verb) FAILS that test; the collision must be resolved in one direction explicitly. (b) A `read` class whose `exit_contract` includes `1` forces a `domain_failure` scenario the read-only printer cannot produce, so the contract must be `(0, 2)` like `find`/`ipd board`. (c) `SubcommandDescriptionTests` requires a `_DESCRIPTIONS` entry longer than `help=` for BOTH new parser nodes. E-04 now states all three with the measured baselines. | `test_command_surface_declarations.py:117-149` (hardcoded query set + `renderer_boundary` else-branch), verified: a `reviews decisions` decl with `shared_empty_result` fails it; `tests/conformance_matrix.py:76-93` (`domain_failure` required when 1 in exit_contract for read/check/bare), `command_surface.py:377` + `:616` (`find`/`ipd board` use `(0, 2)`); `tests/test_cli.py:535-566` + measured 47 pre-existing "empty description" gaps; `CONTRIBUTING.md:182-186` (item 8) |
| F-13 | ADDED AT REVIEW (HIGH): E-04's `[<selector>]` was unspecified, and two concrete facts make a naive implementation wrong. First, the repo has ONE shared selector resolver with a documented precedence and ambiguity policy, and a hand-rolled match would be the duplicate mechanism the house rules forbid; but that resolver keys `id6` off a `- Id:` bullet, while `15zvu6` E-02 specifies the review artifact carries `- Plan-Id:`, so an `id6` selector will NOT match the front matter and must resolve via the clustered filename instead. Second, and more immediately, `15zvu6` is not executed yet, so the `reviews` tree does not resolve AT ALL today: an unguarded implementation would crash or exit 1 on the empty case instead of rendering a clean empty state. E-04 now specifies the resolver, the honest selector-kind list, and the absent-tree behavior. | `selectors.py:347` (`resolve`, precedence + allow/deny), `:503` (`resolve_selectors`), `:88` (`_ID_RE` matches `^- Id:` only), `:332` (`_stem_of`); `15zvu6` E-02 specifies `- Plan-Id:`; measured at review: `selectors.record_dirs(Path('.'), 'reviews')` returns `[]` |
| F-14 | ADDED AT REVIEW (HIGH): E-06 was asked to BUILD the `aw check` rule and WRITE the test suite in one item, and the build half was specified only as "registered in the `RuleSpec` table", which omits every load-bearing decision the sibling review already had to fix for the identical rule shape. Missing: the wiring point (the two candidates have different reach), pending-lane grandfathering, and the fail-open/fail-closed split. Worse, the registry note read as bookkeeping when it is behavioral: an unregistered id falls back to a default at ERROR severity with an empty invariant, so skipping it would silently contradict this plan's report-only posture. Split into E-07 (build, one concern) and E-06 (test), with placement, registry classification, grandfathering, and the absent/malformed/`off` states all named. | `check_engine.py:430-476` (plans-type content path, reached by `aw check plans` AND `aw check all`) vs `:1187-1214` (collisions-only, full sweep only); `:436-438` (the "every dependency source is an IPD" placement precedent); `:866-867` + `:918-923` (pending-lane grandfathering precedents); `:85-171` (`RULE_REGISTRY`) + `:173` (`_DEFAULT_RULESPEC` = error/empty-invariant); `:117-119` (`check.orphaned-live-blocker` advisory precedent); `plqjt7` F-7/F-8 record the same corrections |
| F-15 | ADDED AT REVIEW (MED): E-06's parity assertion would have started a SECOND parity harness for a pair that already has one, which is both the duplicate-mechanism antipattern and a guaranteed drift source. `tests/test_plan_review_parity.py` already holds handles for the single-file body and both long-variant step files and already asserts content parity across them. Moved the assertion there as E-08 and added the module to `Scope-Paths`. The same finding was raised on the sibling `plqjt7` (its F-10), so this is a Set-wide pattern, not a one-off. | `tests/test_plan_review_parity.py:18-23` (`PLAN_REVIEW`/`PRL_02`/`PRL_03` handles), `:147-208` (existing cross-variant content parity assertions incl. one on `02-review-and-revise.md`); `plqjt7` F-10 |
| F-16 | ADDED AT REVIEW (MED): the plan's own recorded history is INVALID under the repo's transition checker, so `aw check plans` reports this plan today, before any of its work is done. The inline history is stored newest-first, but its two authoring lines are in oldest-first order, so the derived event stream reads `to-review -> draft` and `validate_transition` rejects it as a backwards transition. Verified the fix is a pure line reorder: with the two lines swapped the stream derives `draft -> to-review` and validates. NOTE the three approved siblings share the same defect, so do not "fix" theirs from this plan; this is a pre-existing authoring-order bug worth a separate item. | measured: `ipd_lifecycle._plan_status_events(text)` returns `[('2026-08-29','to-review',...), ('2026-08-29','draft',...)]` and `validate_transition('to-review','draft')` -> `ok=False, "backwards transition"`; `aw check plans` reports `check.lifecycle-transition-invalid` for this file and for `15zvu6`/`plqjt7`/`7nkcgp`; after swapping the two lines the stream is `draft -> to-review` and validates `ok=True` |
| F-7 | ADDED AT REVIEW (HIGH): E-05's "LOCATION DEFECT" premise is REFUTED, and acting on it would have damaged a working design. The untracked `decisions.md` is DELIBERATE, not a bug, and it already HAS a tracked counterpart: `set_records` writes a TRACKED walkthrough to `.aw/records/walkthroughs/` and `promote_local_checkpoints` exists specifically to promote an untracked decision checkpoint into it before releasing another lane, with the stated purpose that "a crash never loses a recorded decision". So the module already implements the disposable-projection-plus-durable-record convention this plan cites as its own precedent. Two further facts remove the motive entirely: `set_records` is the SET-COORDINATION register (execset Order 02), a different surface from the review path, and `write_local_projections` has NO production caller today (only two tests call it), so review decisions would never flow through it. E-05 rewritten to leave `set_records.py` untouched and to document the review path's own tracked source of truth instead. | `set_records.py:5-11` (module docstring naming the untracked dir "the local authoritative run convention"), `:166` `render_walkthrough`, `:200` `write_walkthrough` ("Write a TRACKED walkthrough"), `:411-441` `promote_local_checkpoints` ("so a crash never loses a recorded decision"); `grep -rn write_local_projections` finds only `tests/test_exec_set_workflow.py:74` and `tests/test_set_coordination.py:446` |
| F-8 | ADDED AT REVIEW (HIGH): E-06 required `aw check` to report the unescalated-irreversible case, but NO E-item created that rule and no sibling owns it, so the plan demanded validation evidence for a mechanism it never built. Verified the two siblings that touch `check_engine.py` cover different subjects: `plqjt7` the findings threshold, `7nkcgp` the dependency cascade; neither mentions decisions or `Reversible`. E-06 now builds `check.review-decision-unescalated` itself, and `check_engine.py` was added to `Scope-Paths`. | `plqjt7` Scope-Paths + Concern (threshold/blocking open question); `7nkcgp` Scope-Paths + Concern (dependency cascade); no occurrence of `Reversible` or `decision` in either plan's E-items |
| F-9 | ADDED AT REVIEW (HIGH): E-04 creates a NEW CLI namespace and would have been undeclarable within the stated fence. Verified `aw reviews` is not a valid top-level command and that sibling `15zvu6` does NOT add one (no `cli.py` in its `Scope-Paths`), so this verb brings the noun into existence. Every parser leaf MUST carry a `command_surface.COMMAND_INVENTORY` entry or `find_undeclared_leaves` reports it, yet `command_surface.py` was absent from `Scope-Paths`. Also note the declaration test is ALREADY RED at baseline with 59 undeclared leaves, so it cannot serve as a green gate. | `aw reviews decisions` -> `invalid choice: 'reviews'`; `15zvu6` Scope-Paths has no `cli.py`; `pytest tests/test_command_surface_declarations.py -m ''` at `f02c64e`: `AssertionError: 59 != 0` |
| F-10 | ADDED AT REVIEW (MED): the plan's Spec sync correctly flagged the command-surface requirement but pointed at the wrong test (`tests/test_cli_conformance_matrix.py`); the assertion that fails for an undeclared leaf is `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` via `find_undeclared_leaves`. Corrected so the executor runs the test that actually gates. | `test_command_surface_declarations.py:46-52` contains the `find_undeclared_leaves` assertion; the conformance matrix module enumerates leaves for a different purpose |
| F-2 | plan-review has never written a decisions register. | `.aw/workflow-artifacts/` has a `release-review` dir but no `plan-review` dir |
| F-3 | Even when written, the register is invisible to the repo. | `.gitignore:68` ignores `.aw/workflow-artifacts/`; `set_records.py:152-153` writes the register there |
| F-4 | The existing register format is good and worth reusing. | e.g. `.aw/workflow-artifacts/assess-bugs/20260715-205322/decisions.md` records scope, method, verdict rationale, deliberate non-actions with reasons, assumptions, and open questions for the user |
| F-5 | The resolve-before-refusing rule increases the volume of silent decisions, so the audit trail is a precondition for it, not a nicety. | Maintainer instruction 2026-08-29 requiring agents to find a strong recommended path before refusing |
| F-6 | Parity between the two review variants is a documented property that mechanical drift would break. | The plan-review-long manifest row states the two are kept in deliberate parity |

## Proposed changes (ordered, validatable)

1. Require a recorded decision for every self-resolved question, in both review variants (E-01, E-02;
   E-02 corrected at review to amend the long variant's STEP file, not its orchestrator).
2. Distinguish reversible from irreversible, and escalate the irreversible (E-03).
3. Give the maintainer one read-only command to audit decisions, creating and DECLARING the `reviews`
   CLI namespace against the three real declaration gates, and resolving selectors through the shared
   resolver (E-04).
4. Document the review path's tracked source of truth and leave the Set-coordination register alone
   (E-05, rewritten at review: there is no location defect to fix).
5. Build the advisory `aw check` rule at a named wiring point, registered and grandfathered (E-07, split
   out of the drafted E-06 at review because no item built the rule the plan demanded evidence for).
6. Prove all of it with fixture-isolated tests including a firing AND a quiet guard (E-06), and put the
   workflow parity assertion in the module that already owns that parity pair (E-08).

## Deferred / out of scope (with reason)

- **Retro-recording the 112 existing self-resolutions.** Out of scope: they are already written as prose
  inside their plans' open-question sections, which is auditable if imperfect, and manufacturing typed
  decision rows from them would be re-authoring history rather than recording it.
- **The same treatment for EXECUTION-time decisions.** Partially deferred: this plan covers the review
  path, which is where the resolve-before-refusing rule bites hardest and where 112 instances already
  exist. Execution-time self-decisions deserve the same audit trail, but the executor writes into a
  plan's own V-item evidence, which is a different seam and a different instruction surface. Recorded
  here so it is not forgotten; a follow-up should cover it.
- **Un-ignoring `.aw/workflow-artifacts/`.** Explicitly rejected: it holds machine-local run noise, and
  tracking all of it would create leak and churn problems.
- **Any change to `set_records.py`.** Rejected at review (F-7). The drafted "location defect" does not
  exist: the untracked projections are deliberate, they already have a tracked walkthrough counterpart
  with a promotion path built so a crash never loses a decision, that module is the Set-coordination
  register rather than the review path, and its writer has no production caller. Reuse its field
  vocabulary; do not touch its plumbing. If a real gap turns up in the Set path, file a backlog item.
- **Gating on decisions.** Out of scope and now RESOLVED rather than open (OQ-01): an unescalated
  irreversible decision is REPORTED by the new `check.review-decision-unescalated` rule at warning
  severity, but nothing blocks, because `plqjt7` owns the gating machinery and GUIDING_PRINCIPLES 6 warns
  against gold-plating a third overlapping enforcement path. E-03's escalation-at-decision-time is the
  preventive control; the check is the backstop.

## Scope check

- OVER-SCOPE FOUND AND REMOVED AT REVIEW: the drafted E-05 would have modified `set_records.py` to fix a
  "location defect" that does not exist (F-7). That module's untracked projections are deliberate and
  already paired with a tracked walkthrough plus a promotion path, it serves Set coordination rather than
  the review path, and its writer has no production caller. E-05 now documents the review path's own
  tracked source of truth and explicitly leaves `set_records.py` alone; `set_records.py` is NOT in
  `Scope-Paths`.
- UNDER-SCOPE FOUND AND FIXED AT THE FIRST REVIEW, two items. E-06 demanded `aw check` evidence for a
  rule no E-item built and no sibling owns (F-8), so the rule became this plan's to build and
  `check_engine.py` joined `Scope-Paths`. E-04 creates a new CLI namespace whose MANDATORY
  `COMMAND_INVENTORY` declaration was outside the fence (F-9), so `command_surface.py` and a new
  `agent_workflows/reviews.py` joined `Scope-Paths`, as did `.aw/records/reviews/README.md`, which the
  Spec sync section already required this plan to amend.
- WRONG-PATH FIXED AT THE SECOND REVIEW: `Scope-Paths` named `plan-review-long/plan-review-long.md`, the
  orchestrator, which carries no instruction to amend (F-11). Replaced with the two STEP files
  (`02-review-and-revise.md`, `03-resolve-and-finalize.md`) that hold the real instruction surface.
- UNDER-SCOPE FOUND AND FIXED AT THE SECOND REVIEW: the parity assertion belonged in the existing
  `tests/test_plan_review_parity.py` rather than a second harness (F-15), so that module joined
  `Scope-Paths` as E-08.
- RIGHT-SIZING FIXED AT THE SECOND REVIEW: the drafted E-06 bundled three concerns (build a production
  check rule, write the mechanism suite, assert cross-file workflow parity) across three independent test
  surfaces, so it failed the one-concern/one-focused-pass rule regardless of the passing count lint. Split
  into E-07 (build the rule), E-06 (the mechanism suite), and E-08 (the parity assertion in its existing
  home). E-leaf count rises from 6 to 8, still well under the structural threshold.
- Otherwise over-scope: none. Instruction text, one read-only verb, one advisory check rule, and tests.
- Under-scope: acknowledged. This plan makes decisions VISIBLE and AUDITABLE; it does not prevent a bad
  decision, and it does not block execution when one is recorded. Detection after the fact is the honest
  claim. Prevention would require a human gate on every self-resolution, which would defeat the
  resolve-before-refusing rule the maintainer asked for.

## Required tests / validation

1. `python3 -m pytest tests/test_review_decisions.py tests/test_plan_review_parity.py` green, run BARE
   (the repo's `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not pass `-n0`
   or a second `-q`).
2. Full default suite green with counts pasted, compared against a baseline YOU measure at execution
   time. Do not reuse a recorded number: concurrent agents commit to this checkout.
3. The THREE already-red gates must be run EXPLICITLY and reported as unchanged, not skipped, because
   E-04 adds parser leaves that each one polices and none of them can serve as a green gate (F-9, F-12).
   Run with `-m ''` since they are `slow`-marked: `tests/test_command_surface_declarations.py`
   (baseline 59 undeclared leaves), `tests/test_cli_conformance_matrix.py` (same undeclared set),
   `tests/test_cli.py::SubcommandDescriptionTests` (baseline 47 description gaps). For each, paste the
   before/after counts and prove YOUR leaves are absent from the reported set. A count that GREW is a
   failure of this plan even though the test was already red.
4. A worked end-to-end demonstration: review a scratch plan, self-resolve one question, and show the
   decision appearing in `aw reviews decisions` output.
5. The parity assertion demonstrated failing: remove the instruction from one variant and show E-08's
   parity test catches it.
6. `aw check plans` run on this repo before and after, showing E-07's rule adds no finding to the live
   corpus (the tree has no `.review.md` files, so the absent case must be silent).

## Spec / documentation sync

- Both workflow bodies change (E-01, E-02); they are the instruction surface agents load, so this IS the
  documentation. For the long variant that means the STEP file `03-resolve-and-finalize.md` (and
  `02-review-and-revise.md` if E-01 touches the single-file Step 2.2), NOT the orchestrator (F-11).
- CONTRIBUTING.md's "Adding a CLI command" checklist (`:157-186`) is the authored contract E-04 must
  satisfy; note its item 8 (a query verb uses the shared empty-state path) CONFLICTS with the
  classification test's hardcoded query set, and E-04 resolves that conflict explicitly rather than
  discovering it mid-execution (F-12). If you resolve it by adding the leaf to the test's query set,
  that is a test edit inside `Scope-Paths`; if you resolve it by declaring `renderer_boundary`, say so
  and no CONTRIBUTING change is needed.
- `agent_workflows/cli.py`'s `_DESCRIPTIONS` map (`:52`) must gain entries for both new parser nodes, or
  the description test reports them (F-12c).
- `.aw/records/reviews/README.md` (created by `15zvu6`) must gain the decisions-section convention and
  the `Reversible` semantics.
- The new `aw reviews decisions` verb must be declared in `command_surface.COMMAND_INVENTORY`, and the
  assertion that actually gates an undeclared leaf is
  `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` via
  `find_undeclared_leaves`, NOT `tests/test_cli_conformance_matrix.py` as the draft stated (F-10,
  corrected). Add the declaration in the same pass as E-04, and remember that test is already red with 59
  pre-existing undeclared leaves (F-9), so the provable claim is "my leaf is not among them".
- `agent_workflows/reviews.py` is a NEW module hosting the read-only verb, keeping `cli.py` to
  registration and dispatch as the other owner verbs do.

## Open questions

### OQ-01: Should an unescalated irreversible self-decision block execution, or only be reported?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW as REPORT-ONLY, from repository evidence rather
  than as a bare preference, so this plan carries no open question into approval. Three principles decide
  it. GUIDING_PRINCIPLES 10 ("Safety and reversibility") asks for "staged, reversible changes and a clear
  record of what was done", which is exactly a recorded, queryable decision row; it does NOT ask for a
  block. GUIDING_PRINCIPLES 6 (KISS, and the explicit warning that "fix by default invites gold-plating")
  argues against adding a second enforcement gate when a sibling in the same Set already owns the gating
  machinery: `plqjt7` (Order 02) holds the threshold gate and `7nkcgp` (Order 03) the dependency cascade,
  and neither mentions decisions, so a blocking rule here would be a third, overlapping enforcement path.
  GUIDING_PRINCIPLES 11 supports the shape actually chosen: the deterministic part (detecting an
  unescalated `Reversible: no` row) belongs in a tested check with an `--agent` mode, which is what E-06
  now builds. The plan's own Scope check already states detection-after-the-fact as the honest claim, and
  E-03 independently requires the irreversible case be escalated at DECISION time, which is the real
  preventive control; the check is the backstop that catches a reviewer who skipped it. Note the residual
  risk plainly: report-only means a reviewer who both skips E-03's escalation and ignores the warning
  still proceeds. If that is observed in practice, the fix is to raise this ONE rule's severity, not to
  add a gate. Revisit then.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the amended Step 3 wording from `plan-review.md`, showing it requires a
    recorded decision row for each self-resolved question and that the pre-existing citation requirement
    survived. Paste a `git diff` of the hunk proving no other instruction was weakened.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the corresponding wording from `03-resolve-and-finalize.md` (and
    `02-review-and-revise.md` if amended) and a diff showing the two variants' decision-recording text is
    equivalent. State explicitly that parity was checked, not assumed. ALSO paste a `git diff --stat` (or
    a grep) proving `plan-review-long/plan-review-long.md` was NOT edited, since the draft named that
    orchestrator by mistake and editing it would leave the real instruction surface untouched (F-11).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `Reversible` instruction, and paste the escalation rule for the
    irreversible case. Then paste a worked example of each: one reversible decision recorded and left as
    a row, one irreversible decision recorded AND escalated, showing the two are treated differently.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw reviews decisions` human output for a fixture with at least two
    decisions, the `--irreversible` filtered output, and the `--agent` output showing it parses as JSON
    and contains no ANSI escape (`\x1b[`). Paste the exit codes.
    Then paste the DECLARATION evidence (F-12), all four parts: the new `CommandDeclaration` showing the
    `command_class`, the chosen `empty_error_renderer` WITH a one-line statement of how you resolved the
    CONTRIBUTING-item-8-vs-test conflict, and an `exit_contract` the matrix can cover; the two
    `_DESCRIPTIONS` entries; a run of `tests/test_command_surface_declarations.py -m ''` and
    `tests/test_cli.py::SubcommandDescriptionTests -m ''` showing the undeclared count is still 59 and the
    description-gap count still 47, with `reviews`/`reviews decisions` absent from both reported sets; and
    `tests/test_cli_conformance_matrix.py -m ''` unchanged. A count that GREW fails this item.
    Then paste the SELECTOR evidence (F-13): a grep proving resolution goes through `selectors.resolve`
    or `resolve_selectors` and that no hand-rolled id6/status matcher was added; a statement of which
    selector kinds actually resolve given the artifact carries `- Plan-Id:` rather than `- Id:`; and the
    ABSENT-TREE run on a repo with no `.aw/records/reviews/` showing a clean empty state at EXIT 0.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff --stat -- agent_workflows/set_records.py` showing it is UNMODIFIED,
    since E-05 was rewritten at review to leave that module alone (F-7). Paste the evidence that refutes
    the original premise, so the record shows WHY it was not "fixed": the `promote_local_checkpoints`
    docstring and the `write_walkthrough` "Write a TRACKED walkthrough" line, plus a grep showing
    `write_local_projections` has no production caller. Then paste the README text documenting that the
    tracked `.review.md` `## Decisions` section is the review path's source of truth and that the
    Set-coordination register is a separate surface. Confirm `.aw/workflow-artifacts/` is still ignored.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the new rule's code hunk showing (a) its call site in the plans-type content
    path beside `check_ipd_dependencies`, NOT the collisions block; (b) its `RULE_REGISTRY` entry with the
    `warning` severity and the stated invariant id (or `""` plus the one-line reason); (c) the pending-lane
    scoping guard; and (d) the absent/malformed handling. Then paste `aw check plans` on THIS repo before
    and after the change, showing the live corpus gains NO new finding (the tree has no `.review.md`
    files, so the absent case must be silent). Also paste `aw check all` reaching the rule exactly once
    (no double report).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the test file result with counts, AND the adversarial guard OBSERVED BOTH
    WAYS: construct a fixture review artifact with `Reversible: no` and no escalation, paste `aw check`
    reporting it, then escalate the fixture row and paste the clean run showing the rule goes quiet. A
    guard never seen to fail is not evidence; a guard never seen to pass is not evidence either. Paste the
    absent-artifact SILENT case and the malformed-artifact REPORTED case. Paste proof the tests use
    ISOLATED FIXTURE REPOS and not this checkout's live `.aw/records/` (e.g. the tmpdir setup), since a
    live-state assertion would break the moment a real review lands.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the new assertion(s) as they appear in `tests/test_plan_review_parity.py`,
    proving the parity guard lives in the module that already owns this pair rather than in a second
    harness. Then paste it FAILING when the instruction is removed from ONE variant and PASSING when
    restored, naming which file you removed it from. Confirm no duplicate parity harness was added to
    `tests/test_review_decisions.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

RESOLVE-BEFORE-REFUSING (maintainer instruction, 2026-08-29): if you hit an obstacle while executing
this plan, you MUST first do the work of finding a strong recommended path from repository evidence.
Reporting "cannot proceed" is a LAST resort, acceptable only when you can state (a) what you tried,
(b) the specific evidence that blocks each candidate approach, and (c) a concrete recommended option
with trade-offs for the maintainer to choose. This plan is itself the audit trail for that rule, so any
question you resolve while executing it MUST be recorded as a decision row in this plan's own review
artifact: practice what the plan installs.

Execution contract: commit only the files changed for this plan, path-scoped
(`git commit -m msg -- <path>`), never `git add -A` and never push. Other agents and runs are ACTIVE in
this checkout; verify the staged set before every commit with `git diff --cached --name-only` and never
stage, revert, or discard another party's work. Run the suite BARE. When every `V-*` item carries pasted
evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`.
