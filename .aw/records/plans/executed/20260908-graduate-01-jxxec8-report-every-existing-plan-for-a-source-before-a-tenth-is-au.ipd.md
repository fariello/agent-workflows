# IPD: Report every existing plan for a source before a tenth is authored, distinguishing decomposition from duplication

- Date: 2026-09-08
- Kind: child
- Concern: Nothing asks whether a spec or backlog item ALREADY has plans, so the expensive failure the maintainer named has no guard: "we need a way to make sure that the spec / backlog items have not already been addressed. We don't want multiple IPDs for the same things, especially if already implemented." VERIFIED AT HEAD `a2e0438a`: `check_engine` carries `check.from-backlog-dangling` and `check.from-spec-dangling`, both of which validate that a plan's source id6 RESOLVES to a real artifact. Neither asks the reverse question, and grepping the rule table for a duplicate or already-implemented check returns nothing.
  THE RAW MATERIAL EXISTS AND HAS GROWN, which is what makes an advisory view tractable rather than speculative. Measured across the whole plans tree at HEAD `a2e0438a`: 120 plans carry a source link (backlog `6h7y2y` recorded 71), spanning 72 distinct sources, of which 17 have MORE THAN ONE plan.
  THE "125" THIS PLAN FIRST STATED IS THE BULLET COUNT, NOT THE FILE COUNT, AND THE GAP IS AN INDEXING REQUIREMENT RATHER THAN A TYPO (review, F-8). There are 125 source-link BULLETS across 120 FILES, because FIVE plans carry BOTH a `From-Spec:` and a `From-Backlog:` bullet: `5942n7`, `pgq326`, `84j8d7` and `ueg5cf` (each `Backlog: kxkc04` + `Spec: 77tr3o`), and `h0zljh` (`Spec: 7ckptx` + `Backlog: vqv9im`). So E-01's reverse index MUST record every source bullet a plan carries; an index built with a single first-match read per file drops one edge on each of those five and under-reports the `77tr3o` and `vqv9im` clusters. Re-measured at review one day later: 166 bullets over 106 sources with 24 multi-plan clusters, which is this plan's own derive-never-pin rule demonstrating itself. The largest clusters are `From-Spec: 25kzda` x9 (8 `executed`, 1 `not-executed`), `From-Backlog: kjzlgw` x8 (all `executed`), `From-Spec: 7ckptx` x7 (4 `executed`, 3 `approved`), `From-Spec: kw5y2s` x6 (all `executed`), and `From-Backlog: 1ap48y` x4 (3 `executed`, 1 `superseded`). So someone about to graduate `25kzda` a tenth time faces eight executed siblings and nothing says so.
  THIS SET'S OWN MOTIVATING CASE IS THE STRONGEST EVIDENCE. Spec `6m4kow`, which backlog `6h7y2y` cites as having independently recorded the same measurement, ALREADY has three executed plans carrying `From-Spec: 6m4kow` (`eyh1fu`, `5slbpi`, `wpomxa`). Had this view existed, whoever filed the item would have seen those three and scoped it differently, and in fact two of the item's three premises turned out to be already-shipped work.
  AND THAT SAME CASE EXPOSES THE PLAN'S OWN BLIND SPOT (review, F-11). Spec `6m4kow` itself carries `- From-Backlog: 25kzda`, so it is BOTH a source (of three plans) and a CARRIER (of backlog `25kzda`). A reverse index over plans only would tell someone graduating `25kzda` about nine plans and say nothing about the spec that already addresses it. Measured at review, all five specs carrying a source link sit on named example clusters: `c4gd2h`->`kjzlgw`, `7ckptx`->`vqv9im`, `6m4kow`->`25kzda`, `77tr3o`->`kxkc04`, `2vev8j`->`ms06pi`. So the plans-only shape would have missed a carrier on EVERY example this plan uses to argue its case.
  THE HARD PART IS THAT MULTIPLE PLANS PER SOURCE ARE NORMAL AND CORRECT, so a naive uniqueness rule would be worse than nothing. A spec is deliberately decomposed into an ordered Set of children with distinct Orders and non-overlapping scope, and spec `25kzda`'s own graduation text says a run "may produce more than one IPD ... because a single item's design does not always decompose into exactly one plan". The nine-plan `25kzda` cluster is right, not a defect.
- Scope: Add a READ-ONLY, ADVISORY pre-graduation view that reports every existing PLAN OR SPEC carrying a given source id6, with its type, status and Set, so whoever graduates sees the cluster before authoring. Specs are IN scope deliberately and not as an extension: a spec is an equally valid graduation carrier, five specs carry a source link today, and every named example cluster has one, so a plans-only view would be silent on exactly the already-addressed case (F-11). It SHOWS; it does not decide. It must state in its own output which of the three cases it can and cannot detect. EXCLUDES any `count > 1` uniqueness rule; excludes any refusal or gate; excludes the already-implemented verdict, which is not mechanically answerable and is tracked by backlog `f1sw71`; excludes wiring the view into the graduation path (child 02 `iuxtjy`); excludes changing either forward dangling check.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/cli.py, tests/test_graduation_view.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: graduate
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: jxxec8
- From-Backlog: 6h7y2y

## Workflow history
- 2026-09-22 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: jxxec8 verified (set graduate, attempt 1). [Scope reconciliation - out-of-scope agent_workflows/command_surface.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_command_surface_declarations.py: changed by the plan's approved execution (auto-reconciled by aw oc run)]
- 2026-09-22 executed (opencode/its_direct/pt3-claude-opus-5-1m-us, via `aw oc run` lane `jxxec8`): E-01..E-05 performed, V-01..V-05 verified with pasted evidence. Commits `caa4c993` (the three declared `Scope-Paths`), `08139e1c` (the two out-of-scope registry entries) and `deeacb3c` (the defect filed as backlog `v45wb7`).
  WHAT SHIPPED: `aw graduation <source-id6>`, a READ-ONLY advisory view over `check_engine.build_graduation_reverse_index` / `graduation_cluster`, reporting every plan AND spec citing a source with its type, status and Set, and stating its own three-case limits plus its coverage boundary IN THE OUTPUT (human, `--json` and the compact `--agent` record alike).
  OQ-01 RESOLVED TO THE READ SURFACE, NOT A `check` RULE, and no rule was registered; so the `RuleSpec`/`info`-severity half of V-02's evidence requirement is inapplicable rather than skipped. Reason measured rather than argued: 33 of 131 live sources carry more than one artifact, most legitimately, and `aw check all` already reports 475 findings on this tree, so an `info` rule firing on correct work would be noise a reader is already filtering. OQ-02 resolved to an AFFIRMATIVE zero answer through the shared empty-result renderer.
  EVERY CORPUS FIGURE MOVED AGAIN, which is this plan's own derive-never-pin rule demonstrating itself a fourth time: 243 source bullets over 237 artifacts across 131 sources with 33 multi-artifact clusters, against the 166/106/24 review measured and the 125/120/72 authoring measured. The `25kzda` cluster is now TEN (nine plans plus spec `6m4kow`), and the DUAL-LINK population grew from five plans to SIX (`4fodkt` joined), which is why `finditer` rather than `.search` is load-bearing. No test asserts any of these numbers.
  TWO PATHS OUTSIDE THE DECLARED `Scope-Paths` were changed deliberately and are each the minimum a new CLI leaf requires: a `CommandDeclaration` in `agent_workflows/command_surface.py` (an undeclared leaf fails `test_zero_undeclared_parser_leaves` closed) and one allowlist entry in `tests/test_command_surface_declarations.py` (a selector-driven listing must declare `shared_empty_result`). Recorded as DECISION 02-jxxec8-D4 with the alternatives considered.
  A DEFECT WAS FOUND AND FILED: `aw commit <plan>` hard-refuses an out-of-scope path and, unlike `aw ipd finalize`, offers no `--scope-reason` escape, so the justified out-of-scope edge AGENTS.md explicitly authorizes forces `aw commit --no-plan` (which announces it skips Scope-Paths enforcement and plan validation). Measured: zero occurrences of `scope_reason` in `work_cmd.py` against eight in `ipd_lifecycle.py`. Filed as backlog `v45wb7`, `- Work-Kind: bug`, `- Blocks-Release: next`. Both of this turn's implementation commits therefore used `--no-plan`, named in their messages with the reason.
  SUITE, BARE, compared by failing NODE ID: baseline `1 failed, 8022 passed, 3 skipped, 2 xfailed`; after `1 failed, 8043 passed, 3 skipped, 2 xfailed`. Same single failure both times, `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, which is environmental to an isolated lane (it asserts a NON-isolated turn carries no denial policy) and touches none of this change's files. `aw check all` unpiped exit code 1 before and 1 after, with no rule's count changed except `check.scope-drift` 376 -> 387, fully attributed in V-02.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-09 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-604 all FIXED; readiness `go-pending-approval`. SELF-REVIEW disclosure: the same agent/model authored this plan, so its value rests on EXECUTING its claims rather than re-reading them. Six things were run: the whole plans tree was re-walked parsing both source fields plus status and Set; the SPECS tree was walked the same way; every caller of `find_from_backlog_plans`/`find_from_backlog_artifacts` was grepped and read; `drift_exit_code` and the rule registry were read and severities counted; the full bare suite was run; and `aw check all`'s per-rule counts were parsed. THE ONE FINDING THAT MATTERS is PR-601 (HIGH): the view was scoped to PLANS ONLY, which would reintroduce the exact defect `bklgrad` Order 01 (`v58bvy`) E-06 already fixed ("the HANDOFF route previously scanned plan IPDs ONLY, so a spec-first graduation ... was invisible"), and measurement made it concrete: FIVE specs carry a source link and ALL FIVE sit on clusters this plan names as its own examples, including the motivating spec `6m4kow`, which is itself a carrier of backlog `25kzda`. So the plan-as-written would have told someone graduating `25kzda` about nine plans and stayed silent about the spec that already addresses it, which is precisely the already-addressed case the maintainer asked to be shown. Specs are now in scope at no cost in `Scope-Paths` (both spec helpers already live in `check_engine.py`), with a second live assertion, a spec-only fixture, and a third mutation that makes the plans-only regression impossible to reintroduce silently. Also named the existing `find_from_backlog_artifacts` shared lookup the plan gestured at but did not cite (PR-602), qualified the view's silence so a zero-result is not read as completeness (PR-603), and pinned the `info` severity precedent to two real rules (PR-604). Every corpus figure was re-measured (171 bullets / 166 files / 106 sources / 24 clusters, up from 125/120/72/17 one day earlier), which is this plan's own derive-never-pin rule demonstrating itself a third time.
- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `6h7y2y` Half 2, which the item itself calls "THE ONE THAT MATTERS". The item carries no `- Blocks-Release:` so none is inherited or invented. This child is Order 01 because the item's sequencing note is explicit and gives its reason: "build the guard BEFORE or WITH the verb, not after. A working `--action plan` with no duplicate check is a machine for generating redundant plans faster than a human can."
  EVERY CLAIM RE-MEASURED at HEAD `a2e0438a` and the item held, with its numbers updated: 125 source-linked plans rather than 71, 72 distinct sources, 17 with more than one plan, and the three named clusters confirmed with their exact status breakdowns. The absence of a reverse-direction check also confirmed by grepping the rule table rather than by trusting the item.
  THE ITEM'S OWN CASE PROVED ITS POINT, and I recorded it as F-3 because it is the most persuasive argument in the plan: spec `6m4kow` already has three executed plans, and this very item was filed partly on premises that had already shipped. That is exactly the waste the view prevents.
  I IMPLEMENT THE ITEM'S "MINIMUM USEFUL VERSION" DELIBERATELY, NOT AS A SHORTCUT. The item offers a full three-way classifier and then says: "MINIMUM USEFUL VERSION, if the full classifier is too much: a PRE-GRADUATION WARNING that reports every existing plan carrying this source id6 with its status and Set ... Advisory and read-only; it does not need to decide, only to show. That alone would prevent the costly case." The full classifier is NOT chosen because one of its three cases is mechanically unanswerable: there is no per-requirement tracking, a spec carries ONE whole-artifact status with no partial-implementation state, and `implemented` requires only a resolvable citation rather than semantic verification. Backlog `f1sw71` (`graduated` to decision plan `si24ia`, which measures and recommends rather than building a requirement model; the GAP itself is unbuilt) tracks that, and the item explicitly permits shipping the plan-level guard without it provided the plan "say honestly which of the three cases above it can and cannot detect". E-03 makes that honesty part of the OUTPUT rather than only part of this document, which is the one place I went beyond the item.

## Goal

Let whoever is about to graduate a source see, before they author anything, every plan that source already has and what became of it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: read the cluster from the authority that already exists

- [x] E-01 BUILD THE REVERSE INDEX from source id6 to the ARTIFACTS that cite it, reusing the enumeration the forward dangling checks already use rather than walking the tree afresh. `check.from-backlog-dangling` and `check.from-spec-dangling` already parse `From-Backlog:` and `From-Spec:` to validate the forward direction, so the parse exists; this item inverts it.
  INDEX PLANS **AND SPECS**, NOT PLANS ONLY, AND THIS IS THE SINGLE MOST IMPORTANT CORRECTION IN THIS PLAN (F-11). A SPEC is an equally valid graduation carrier: `AGENTS.md` calls it an "equally valid gate carrier", `find_from_backlog_artifacts` (`check_engine.py:1947-1960`) exists precisely because "the HANDOFF route previously scanned plan IPDs ONLY, so a spec-first graduation ... was invisible", and `check_from_spec_dangling` (`:2959`) already reuses BOTH `_iter_plan_ipds` and `_iter_spec_records` for the same reason. Measured at review: FIVE specs carry a source link (`c4gd2h`->`kjzlgw`, `7ckptx`->`vqv9im`, `6m4kow`->`25kzda`, `77tr3o`->`kxkc04`, `2vev8j`->`ms06pi`), and EVERY ONE of the five clusters this plan names as its examples has a spec carrier the plan-only view would MISS. So a plans-only index tells someone graduating `25kzda` about nine plans and stays silent about the `6m4kow` spec, which is exactly the already-addressed case the maintainer asked to be shown. Worse, it would REINTRODUCE the defect `bklgrad` Order 01 (`v58bvy`) E-06 already fixed.
  PREFER THE EXISTING SHARED LOOKUP OVER A NEW WALK. `find_from_backlog_artifacts(repo_root, item_id6)` ALREADY answers "which plans and specs carry `From-Backlog: <id6>`", and `oc_runipd.py:1153-1158` documents it as "THE ONE SHARED LOOKUP ... A second implementation here would be the same divergence defect this repository keeps hitting, so there is deliberately no local scan". Follow that precedent: consume that symbol for the backlog direction, and add the `From-Spec` direction in the same shape rather than in a private walk. If you conclude a new function is genuinely needed (for example because per-source calls would re-walk the tree, the cost `check_engine.py:2256-2262` already worked around with a single-pass index), say WHY in the plan and put it beside its siblings in the same module, not in a new one.
  DO NOT ADD A SECOND PARSER FOR `From-Backlog:`/`From-Spec:`. Two readers of one field drift, and the forward checks are `error` severity, so a divergence would mean the view and the checker disagree about which artifacts cite a source. Reuse `_META_FROM_BACKLOG_RE` (`:1843`) and `_ITEM_FROM_SPEC_RE` (`:2940`); locate them by symbol.
  CARRY THE STATUS AND THE SET, because they are what makes the output actionable: the item's own example is "25kzda already has 9 plans, 7 executed" (measured at review: 8 executed, 1 not-executed). A list of ids without statuses would not distinguish "already built" from "in flight". CARRY THE ARTIFACT TYPE TOO, since a cluster may now mix plans and specs and "a spec at `to-review`" means something different from "a plan at `to-review`".
  INCLUDE TERMINAL DIRECTORIES, NOT ONLY `pending/`. The costly case the maintainer named is re-doing landed work, so a view that reads only pending plans would miss every executed sibling and would be worst exactly where it matters most. Measured, most cluster members are `executed`. This comes free from the existing iterator: `_iter_plan_ipds` (`:1880-1897`) `rglob`s the whole `.aw/records/plans` tree, so terminal directories are already covered and the requirement is to NOT filter them out.
  INDEX EVERY SOURCE BULLET AN ARTIFACT CARRIES, NOT THE FIRST MATCH, and this is a measured requirement rather than a defensive one (F-8). Five plans carry BOTH kinds of link, so a `re.search`-style first-match read per file silently drops one edge on each and under-reports two real clusters. Re-verified at review: `20260906-orchretire-{00,01,02,03}` (`84j8d7`, `5942n7`, `ueg5cf`, `pgq326`) each carry `Backlog: kxkc04` PLUS `Spec: 77tr3o`, and `20260901-lanectn-00-h0zljh` carries `Backlog: vqv9im` PLUS `Spec: 7ckptx`. Note the existing forward readers are single-match BY DESIGN (`find_from_backlog_plans` uses `_META_FROM_BACKLOG_RE.search` at `:1929`, and `check_from_spec_dangling` uses `_ITEM_FROM_SPEC_RE.search` at `:3000`), which is correct for their question ("does THIS artifact's link resolve?") and insufficient for this one. Reusing `find_from_backlog_artifacts` per source is SAFE here despite that, because it filters by a caller-supplied id6 rather than reading one link per file; the multi-match concern applies to a whole-corpus single-pass build, which is the shape `check_engine.py:2256-2262` uses. Whichever shape you pick, prove the dual-link plans appear under BOTH sources.
  DO NOT BUILD A SECOND TRAVERSAL OF THIS EDGE. Pending plan `bwgyum` (Set `setidhard`, Order 02, `reviewed`, `go-pending-approval`) adds the FORWARD `- Graduated-To:` link and `check.graduated-to-dangling` over the SAME `_iter_plan_ipds` in the SAME module. Whichever of the two lands second consumes the first rather than re-walking; the orchestrator (`y9s4vm`) carries that as a binding constraint and verifies it as CID-7. Check `bwgyum`'s status before writing E-01 and record which case you are in.
  - Depends on: none
  - Expected outcome: a reverse index mapping each source id6 to its citing PLANS AND SPECS with each artifact's id6, type, status and Set, built by reusing the existing field readers and both iterators (or by consuming `find_from_backlog_artifacts`); EVERY source bullet indexed (the five dual-link plans appear under both sources); terminal directories included; no second parser added; `bwgyum`'s status checked and the shared-traversal case recorded.
  - Execution state: performed

### Task group 2: report it without deciding

- [x] E-02 EXPOSE IT AS A READ-ONLY SURFACE, and choose the surface deliberately (OQ-01). The item is explicit that this is "Advisory and read-only; it does not need to decide, only to show".
  DO NOT IMPLEMENT A `count > 1` RULE, and this is the single most important prohibition in the plan. Measured, 17 of 72 sources have more than one plan and the largest cluster of nine is CORRECT decomposition; spec `25kzda` says a run "may produce more than one IPD". A rule that flags count would report 17 legitimate clusters as defects and would teach people to ignore it, which is worse than having no guard.
  IF YOU CHOOSE A `check` RULE, ITS SEVERITY MUST BE `info`, AND THE PRECEDENT IS NAMED RATHER THAN HYPOTHETICAL. Verified at review: `artifact_core.drift_exit_code` (`:405-415`) returns 1 if ANY finding's severity `!= "info"`, so `warning` DOES exit nonzero, and `check_engine.py:188-190` documents that exact misreading in its own comment. Registration is mandatory because `_DEFAULT_RULESPEC` (`:343`) is `error` with an EMPTY invariant, so an unregistered rule silently becomes an error. Two `info` rules already exist as precedent to copy (`check.ipd-draft-ready-to-review`, `check.stale-index-missing`; measured 24 error / 6 warning / 2 info across 32 registered rules). A rule must also carry an INVARIANT id or an explicit empty-with-reason: `check.review-finding-unescalated`'s registration comment sets the precedent for a legitimately uncatalogued id, so do not claim a neighbouring invariant you have not checked.
  MAKE IT ANSWER THE QUESTION SOMEONE ACTUALLY ASKS, which is "I am about to graduate X, what exists already?". That means accepting a source selector and reporting its cluster, not dumping every cluster and leaving the reader to search. Measured at review there are 106 distinct sources and 24 multi-plan clusters, so a full dump is unreadable.
  - Depends on: E-01
  - Expected outcome: a read-only surface that takes a source selector and reports its cluster with types, statuses and Sets; NO uniqueness rule; if implemented as a `check` rule, severity `info` and a deliberate invariant id, with the `drift_exit_code` behavior verified rather than assumed.
  - Execution state: performed

- [x] E-03 STATE THE LIMITS IN THE OUTPUT, not only in this plan. The item requires the work "say honestly which of the three cases above it can and cannot detect", and a limit recorded only in a plan file is invisible to the person reading the view.
  THE THREE CASES AND WHAT THIS VIEW CAN DO ABOUT EACH, which the output must convey: LEGITIMATE DECOMPOSITION (several children of one Set, distinct Orders, non-overlapping scope) is VISIBLE, because the view shows the Set and the reader can see one Set with many Orders; ACCIDENTAL DUPLICATION (two plans in DIFFERENT Sets covering the same requirement) is PARTLY VISIBLE, because the view shows that the Sets differ but cannot judge whether the scopes overlap; ALREADY IMPLEMENTED is NOT DETECTABLE, because there is no per-requirement tracking.
  SAY WHY THE THIRD IS UNDETECTABLE, briefly, rather than just declining it. A spec carries ONE whole-artifact status with no partial-implementation state, and `implemented` requires only a resolvable citation rather than semantic verification. Point at backlog `f1sw71`. A reader who knows WHY will not assume the view failed.
  DO NOT OVERSTATE THE SECOND CASE. The view cannot compare scopes; claiming it detects duplication would be the same kind of false confidence this whole item exists to prevent.
  STATE THE COVERAGE BOUNDARY EXPLICITLY, so a reader knows what "no existing plans" is a claim ABOUT (F-11, F-13). The output must say which artifact types were searched (plans and specs) and, if the reverse index reads only the two `From-*` bullets, that a source addressed WITHOUT such a link is invisible to it. That second limit is real and measurable: 106 of the tree's sources carry a link, and any earlier work that predates the convention or simply omitted the bullet will not appear. A view whose silence is mistaken for "nothing exists" would cause the very duplication it exists to prevent, so its silence must be qualified in the output rather than in this plan.
  - Depends on: E-02
  - Expected outcome: the view's own output states, per case, whether it is visible, partly visible, or undetectable, with the reason for the undetectable one and a pointer to `f1sw71`; it names the artifact types searched and qualifies what its silence means; no case is overstated.
  - Execution state: performed

### Task group 3: prove it against the real corpus and against over-reach

- [x] E-04 TEST AGAINST THE LIVE CORPUS FOR THE NO-FALSE-POSITIVE PROPERTY, and against fixtures for everything else. This split is deliberate: the property "correct real work is not flagged" can only be demonstrated on the real corpus, while every behavioral case needs a fixture to be stable.
  THE LIVE ASSERTION: for `From-Spec: 25kzda` (nine plans, eight executed at review), the view REPORTS the cluster and flags NO defect. That is the anti-over-reach guard and it is the reason a fixture alone is insufficient, since a fixture proves only that the code does what its author expected.
  A SECOND LIVE ASSERTION IS REQUIRED FOR THE SPEC CARRIER (F-11), because the plans-only failure mode passes every plans-only test by construction. Assert that the `25kzda` cluster ALSO surfaces spec `6m4kow`, and that the `kxkc04` cluster surfaces spec `77tr3o` alongside its four plans. Derive both, do not pin. Without this assertion nothing in the suite would catch a reverse index that silently omits every spec.
  THE FIXTURE CASES: a source with zero artifacts; a source with one; a source with several in ONE Set (decomposition); a source with several across DIFFERENT Sets (the partly-visible case); a source whose plans are all terminal (the already-landed case, which must be clearly visible since it is the costly one); and a source carried by a SPEC ONLY, with no plan at all, which must still be reported (the spec-first graduation shape `find_from_backlog_artifacts` exists to cover).
  DO NOT PIN THE LIVE COUNTS. The corpus grows measurably: the item recorded 71 source-linked plans, this plan recorded 125 bullets over 120 files, and review measured 171 bullets over 166 files across 106 sources with 24 multi-plan clusters ONE DAY later. So a test asserting "nine plans for 25kzda" breaks on the next graduation. Assert the PROPERTY (no defect flagged, cluster reported, the known member PRESENT) and derive the count.
  - Depends on: E-03
  - Expected outcome: live-corpus assertions that the largest real cluster is reported and not flagged AND that its spec carrier appears, with counts derived rather than pinned; six fixture cases covering zero, one, one-Set-many, many-Sets, all-terminal, and spec-only.
  - Execution state: performed

- [x] E-05 MUTATION-CHECK THE ANTI-OVER-REACH GUARD, because a test asserting "nothing was flagged" passes trivially if the view flags nothing ever.
  INTRODUCE A `count > 1` RULE deliberately, show the live-corpus assertion FAILS (it should flag every multi-plan cluster including the correct nine-plan one; measured 24 such clusters at review, but DERIVE the number rather than asserting 24), then revert and show it passes. That demonstrates the guard actually detects the failure mode the item warns about.
  ALSO MUTATE THE OTHER DIRECTION: make the view ignore terminal plans, and show the all-terminal fixture case FAILS. That is the costly case the maintainer named, so a view that silently dropped executed siblings must be caught.
  MUTATE THE SPEC CARRIER TOO (F-11), which is the mutation this plan most needed and did not have: make the index read `_iter_plan_ipds` ONLY, and show BOTH the spec-only fixture and the live `25kzda`-surfaces-`6m4kow` assertion FAIL. This is the exact regression `bklgrad` `v58bvy` E-06 already fixed once, so a mutation proving it cannot silently return is worth more than the other two combined.
  - Depends on: E-04
  - Expected outcome: three mutations, each failing the assertion it should and passing after revert, all six outputs pasted.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE FORWARD DIRECTION IS ALREADY PARSED AND VALIDATED. `check.from-backlog-dangling` and `check.from-spec-dangling` read the same two fields at `error` severity, so the reverse index must reuse those readers rather than adding a third.
- A SPEC IS AN EQUALLY VALID GRADUATION CARRIER, AND THE PLANS-ONLY BUG WAS ALREADY FIXED ONCE. `find_from_backlog_artifacts` (`check_engine.py:1947-1960`) exists because the handoff route "previously scanned plan IPDs ONLY, so a spec-first graduation ... was invisible"; `check_from_spec_dangling` (`:2959`) reuses BOTH `_iter_plan_ipds` and `_iter_spec_records`. Measured: 5 specs carry a source link and all 5 sit on this plan's own example clusters (F-11).
- THERE IS ALREADY A NAMED "ONE SHARED LOOKUP" FOR THIS QUESTION. `oc_runipd.py:1153-1158` calls `find_from_backlog_artifacts` under the comment that a second implementation "would be the same divergence defect this repository keeps hitting, so there is deliberately no local scan". Follow it (F-12).
- PER-SOURCE CALLS RE-WALK THE TREE, AND THE FIX IS ALREADY IN-TREE. `check_engine.py:2256-2262` builds a single-pass `plan_gates_by_backlog` index precisely because "calling `find_from_backlog_plans` for every open blocker re-walked the complete plans tree per item". Copy that shape if you need whole-corpus data.
- TERMINAL DIRECTORIES COME FREE. `_iter_plan_ipds` (`:1880-1897`) `rglob`s the entire plans tree, so `executed/` and the rest are already included; the requirement is to not filter them out.
- `info` SEVERITY HAS TWO IN-TREE PRECEDENTS: `check.ipd-draft-ready-to-review` and `check.stale-index-missing` (measured 24 error / 6 warning / 2 info of 32 registered rules). A new rule also owes a deliberate invariant id or an explicit empty-with-reason.
- A NEW RULE IS NEVER SILENTLY UNCLASSIFIED. `check_engine._DEFAULT_RULESPEC` exists for exactly that reason, so a new rule must be classified deliberately.
- A `warning` EXITS NONZERO; ONLY `info` DOES NOT. The repository documents this explicitly as a misreading to avoid, and it decides E-02's severity if a `check` rule is chosen: 17 legitimate clusters at `warning` would red every run.
- MULTIPLE PLANS PER SOURCE ARE CORRECT BY DESIGN. Spec `25kzda`'s graduation text says a run "may produce more than one IPD", and measured, the largest cluster is correct decomposition.
- THE ALREADY-IMPLEMENTED CASE HAS NO MECHANISM. A spec carries one whole-artifact status with no partial-implementation state, and `implemented` requires only a resolvable citation rather than semantic verification. Backlog `f1sw71` tracks it.
- THE CORPUS GROWS DURING WORK. The item measured 71 source-linked plans; it is 120 five days later (125 bullets), and 166 bullets over 106 sources one day after that at review. An executed plan in this repository's history was reviewed with a note that its own corpus count "GREW during this Set's own operation, so the count must be derived not asserted". Derive, never pin.
- THE EXISTING FORWARD READERS ARE SINGLE-MATCH BY DESIGN. `find_from_backlog_plans` and `check_from_spec_dangling` each use `.search`, which answers "does THIS plan's link resolve" correctly and cannot build a reverse index over the five dual-link plans. Reuse the patterns; do the multi-match walk here (F-8).
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals. CORRECTED AT REVIEW: the `1 failed, 5648 passed` figure and its attribution to `tests/test_orchestrator_retirement.py` are BOTH stale. Re-confirmed at review round 2: `1 failed, 5919 passed, 3 skipped, 2 xfailed in 51.59s`, the failing node being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL (a gitignored local `opencode-recovery/` dump in this checkout) and may be absent elsewhere; `test_orchestrator_retirement.py` PASSES (112 passed). Measure your own and quote neither.
- `aw check all` PER-RULE COUNTS COME FROM THE `diagnostics` ARRAY of the single `--agent` JSON object; there are no tab-separated records and `--format json` raises `JSONDecodeError` on this surface. Baseline at review: 238 findings, `check.scope-drift` 174, `check.setid-collision` 40, `check.lifecycle-transition-invalid` 15, `check.name-nonconformant` 3, others at 1 or 2.

## Findings

| Id | Severity | Location (measured at HEAD `a2e0438a`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `check_engine.py` rule table | Only the FORWARD direction is checked (`check.from-backlog-dangling`, `check.from-spec-dangling`). No reverse, duplicate, or already-implemented check exists. | grepped the rule table; no hits for duplicate/already-implemented |
| F-2 | MED | plans tree | 125 plans carry a source link across 72 sources, 17 with more than one plan. `25kzda` x9 (8 executed, 1 not-executed), `kjzlgw` x8 (all executed), `7ckptx` x7 (4 executed, 3 approved), `kw5y2s` x6 (all executed), `1ap48y` x4 (3 executed, 1 superseded). The item recorded 71 plans. RE-MEASURED AT REVIEW ROUND 2: 171 bullets over 166 files across 106 sources with 24 multi-plan clusters; `25kzda` x9 (8 executed, 1 not-executed), `kjzlgw` x8, `7ckptx` x7 (5 executed, 2 approved), `kw5y2s` x6, then `1ap48y`/`5wdoze`/`kxkc04`/`77tr3o` at 4. The growth is the point: DERIVE, never pin. | walked the tree parsing both fields plus `- Status:` |
| F-3 | HIGH | executed plans `eyh1fu`, `5slbpi`, `wpomxa` | THE ITEM'S OWN SOURCE WAS ALREADY PARTLY GRADUATED: spec `6m4kow` has three executed plans, and two of `6h7y2y`'s three premises had already shipped when it was filed. This is the waste the view prevents, demonstrated on this very Set. | grepped `From-Spec: 6m4kow` |
| F-4 | CONSTRAINT | spec `25kzda` graduation text; F-2 | A `count > 1` RULE WOULD BE WRONG: multiple plans per source is deliberate decomposition, and the nine-plan cluster is correct. Flagging it would teach readers to ignore the warning. | spec text plus measured cluster statuses |
| F-5 | CONSTRAINT | `check_engine` `drift_exit_code` and `_DEFAULT_RULESPEC` | A `warning` exits nonzero; only `info` is exempt. So a `check` rule over 17 legitimate clusters must be `info` or it reds every run. The repository documents this as a misreading to avoid. | source read |
| F-6 | BLOCKER-FOR-ONE-CASE | backlog `f1sw71`; `attention_contract` | THE ALREADY-IMPLEMENTED CASE IS NOT MECHANICALLY ANSWERABLE: one whole-artifact status, no partial-implementation state, and `implemented` needs only a resolvable citation. The item permits shipping without it if the limit is stated honestly. | the item's citation re-verified; `f1sw71` open |
| F-7 | MED | F-2 | MOST CLUSTER MEMBERS ARE TERMINAL (`executed`), so a view reading only `pending/` would miss the costly case entirely. | status breakdown per cluster |
| F-8 | MED (added at review) | plans tree; five named plans; `_META_FROM_BACKLOG_RE`, `_ITEM_FROM_SPEC_RE` | THE BULLET COUNT IS NOT THE FILE COUNT AND THE EXISTING READERS ARE SINGLE-MATCH BY DESIGN. 125 bullets over 120 files at `a2e0438a`, because `5942n7`, `pgq326`, `84j8d7`, `ueg5cf` and `h0zljh` each carry BOTH link kinds. The forward checks use `.search` (one match), which is right for "does this plan's link resolve" and wrong for building a reverse index; reusing a reader without noticing this drops one edge per dual-link plan. | re-walked a clean `a2e0438a` archive: 125 / 120; read both regex call sites |
| F-9 | HIGH (added at review) | pending plan `bwgyum` (Set `setidhard`, Order 02, `reviewed`, `go-pending-approval`) | THE OPPOSITE DIRECTION OF THIS EDGE IS BEING BUILT BY ANOTHER SET AND NEITHER PLAN MENTIONS THE OTHER. `bwgyum` adds the forward `Graduated-To` link plus its dangling check over the same `_iter_plan_ipds` in the same module. Two traversals of one relationship is the drift P8 forbids and they could disagree about what a source became. The orchestrator now carries the coordination constraint and CID-7. | grepped both Sets for cross-references (zero hits); read `bwgyum` E-01/E-03 |
| F-10 | LOW (added at review) | backlog `f1sw71` | STATUS LABEL STALE: this plan calls `f1sw71` "open" twice; it is `graduated`, to decision plan `si24ia` (`to-review`) which measures and recommends rather than building a requirement model. The GAP is unbuilt, so every exclusion resting on it is unchanged, but an executor finding it graduated with a plan attached could wrongly conclude the exclusion was overtaken. | `aw find backlog f1sw71` -> `graduated ...`; `si24ia` carries `- From-Backlog: f1sw71` |
| F-11 | HIGH (added at review round 2) | `check_engine.py:1947-1960`, `:2959`, `oc_runipd.py:1153-1158`; five specs | **THE VIEW WAS SCOPED TO PLANS ONLY, WHICH WOULD REINTRODUCE A DEFECT ALREADY FIXED AND WOULD BE SILENT ON A CARRIER OF EVERY EXAMPLE CLUSTER.** A SPEC is an equally valid graduation carrier. `find_from_backlog_artifacts` exists because "the HANDOFF route previously scanned plan IPDs ONLY, so a spec-first graduation ... was invisible", and `check_from_spec_dangling` already reuses BOTH iterators for the same reason. Measured: 5 specs carry a source link, and ALL FIVE sit on clusters this plan names (`kjzlgw`, `vqv9im`, `25kzda`, `kxkc04`, `ms06pi`). The motivating spec `6m4kow` is itself a carrier of `25kzda`. A plans-only reverse index answers "what exists for 25kzda" with nine plans and omits the spec, which is precisely the already-addressed case the maintainer asked to see. | walked `.aw/records/specs` parsing both fields; read all three cited call sites |
| F-12 | MED (added at review round 2) | `find_from_backlog_artifacts`; `oc_runipd.py:1153-1158`; `check_engine.py:2256-2262` | A DIRECTLY REUSABLE SHARED LOOKUP ALREADY EXISTS AND THE PLAN DOES NOT NAME IT. `find_from_backlog_artifacts(repo, id6)` already returns every plan and spec carrying `From-Backlog: <id6>`, and the runner calls it under the comment "THE ONE SHARED LOOKUP ... A second implementation here would be the same divergence defect this repository keeps hitting". The plan's E-01 said only "reuse the existing readers", which an executor could satisfy by reusing a REGEX while still writing a third traversal. The single-pass index at `:2256-2262` also shows the performance shape already solved. | grepped every caller of both symbols; read the comments |
| F-13 | MED (added at review round 2) | the view's silence | THE VIEW'S "NOTHING EXISTS" ANSWER IS UNQUALIFIED, WHICH IS THE ONE OUTPUT THAT CAN CAUSE THE HARM IT PREVENTS. The index reads only the two `From-*` bullets, so a source addressed by work that carries no such link is invisible. OQ-02 recommends an affirmative "nothing yet, proceed" message, which without a stated coverage boundary is a stronger claim than the data supports. | 106 of the tree's sources carry a link; the index's own input is the bullet, not the work |
| F-14 | LOW (added at review round 2) | `artifact_core.py:405-415`; `check_engine.py:188-190`, `:343`; `RULE_REGISTRY` | F-5 IS EXACTLY RIGHT AND ITS PRECEDENT IS NOW NAMED. `drift_exit_code` returns 1 if any severity `!= "info"`, the engine documents that misreading in its own comment, `_DEFAULT_RULESPEC` is `error` with an EMPTY invariant so an unregistered rule silently errors, and TWO `info` rules already exist to copy (`check.ipd-draft-ready-to-review`, `check.stale-index-missing`; 24 error / 6 warning / 2 info of 32). A new rule also owes a deliberate invariant id or an explicit empty-with-reason. | read the function and the registry; counted severities |

## Proposed changes (ordered, validatable)

1. E-01 inverts the existing forward parse into a source-to-ARTIFACTS index over plans AND specs, carrying type, status and Set, including terminal directories, and consuming the existing shared lookup rather than adding a third traversal.
2. E-02 exposes it as a read-only surface taking a source selector, with no uniqueness rule and `info` severity plus a deliberate invariant id if it is a rule.
3. E-03 puts the three-case honesty into the OUTPUT, with the reason the third is undetectable and a stated coverage boundary so its silence is not over-read.
4. E-04 asserts the no-false-positive property AND the spec-carrier property against the live corpus, and six behavioral cases against fixtures.
5. E-05 mutation-checks the guard in three directions, including the plans-only regression.

## Deferred / out of scope (with reason)

- THE FULL THREE-WAY CLASSIFIER. The item offers it and then offers the minimum version; the minimum is chosen because one of the three cases is mechanically unanswerable (F-6) and a classifier that guessed it would produce exactly the false confidence this item exists to prevent.
- THE ALREADY-IMPLEMENTED VERDICT. Backlog `f1sw71` (`graduated` to decision plan `si24ia`; the gap is unbuilt, so this exclusion is unchanged: F-10). The item explicitly permits shipping without it.
- ANY `count > 1` UNIQUENESS RULE, REFUSAL, OR GATE. F-4 and the item's own "advisory and read-only; it does not need to decide, only to show".
- WIRING THE VIEW INTO THE GRADUATION PATH. Child 02 (`iuxtjy`), which makes a spec or backlog selector reachable for the `plan` action and calls this view there. Split because the view is useful and testable on its own, and because the item required the guard to exist FIRST.
- SCOPE-OVERLAP DETECTION between two plans in different Sets. That would need a scope comparison the repository has no mechanism for; E-03 states the limit instead of faking it.
- CHANGING EITHER FORWARD DANGLING CHECK. They work, they are `error` severity, and this item adds a view rather than altering validation.
- WORK THAT ADDRESSES A SOURCE WITHOUT CARRYING A `From-*` BULLET (F-13). The index's input is the bullet, so unlinked work is invisible and no amount of walking fixes it. E-03 states this boundary in the OUTPUT instead of pretending to completeness; retro-fitting links across the corpus is a separate concern nobody has scoped.
- OTHER ARTIFACT TYPES BEYOND PLANS AND SPECS. Measured, only plans and specs carry `From-Backlog`/`From-Spec` today, and `find_from_backlog_artifacts` recognizes exactly those two, so widening further would be speculative. If a future type gains the field, the reverse index inherits it by reusing that symbol rather than by a change here.

## Scope check

- Over-scope: `check_engine.py` is in scope ONLY to add the reverse index and, if OQ-01 chooses a rule, one `info` rule. Do NOT change either forward dangling check or any existing severity.
- Scope-Paths justification: `check_engine.py` holds both forward readers, both iterators, `find_from_backlog_artifacts` and the rule registry, so the reverse index belongs beside its siblings there rather than in a new module. `cli.py` is where a read surface is registered. `tests/test_graduation_view.py` is new. NOTE the spec-carrier correction (F-11) does NOT widen these paths: `_iter_spec_records` and `find_from_backlog_specs` already live in `check_engine.py`, so covering specs costs no additional path.
- Under-scope: stated rather than left as `none`. After this child the view exists but nothing CALLS it during graduation, so it helps only whoever remembers to run it; child 02 closes that. Accidental duplication is only partly visible, since scopes are not compared. And the view sees only linked work (F-13), so its silence is a statement about links rather than about work.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. Re-measured at review round 2 on main: `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the single failure being the ENVIRONMENTAL `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (a gitignored local dump), which may be absent in your worktree. Do NOT attribute the known failure to `tests/test_orchestrator_retirement.py`: measured, it PASSES (`112 passed`), so citing it as the pinning example is doubly wrong and the caution below is restated without it.

THE LIVE-CORPUS ASSERTIONS IN E-04 MUST DERIVE THEIR COUNTS, NEVER PIN THEM, and the evidence for that is this plan's own numbers moving three times: 71 source-linked plans in the item, 125 bullets over 120 files when this plan was authored, and 171 bullets over 166 files across 106 sources with 24 multi-plan clusters at review one day later. An executed plan's review record separately warns that a corpus count "GREW during this Set's own operation, so the count must be derived not asserted". Assert PRESENCE of a known member and the absence of a flag; never a total.

Run `aw check all` before and after to prove no existing rule's output changed, comparing PER RULE from the `diagnostics` array of the single emitted `--agent` JSON object (there are no tab-separated records, and `--format json` emits nothing parseable on this surface). Baseline at review: 238 findings, led by `check.scope-drift` 174 and `check.setid-collision` 40. If OQ-01 adds an `info` rule the total WILL rise, which is expected; what must not change is any other rule's count or `aw check`'s exit code.

## Spec / documentation sync

Spec `25kzda` (`- Status: approved`) is the authority for what graduation MEANS and its §1.3 lists graduation as a disposition of `aw <host> run`. This child adds an ADVISORY VIEW and no dispatch, so it neither implements nor contradicts that section, and no amendment is expected.
TWO THINGS TO CHECK RATHER THAN ASSUME. FIRST, whether §1.3 or the graduation text specifies a DUPLICATE CHECK as part of the graduation disposition; if it does, this child is implementing a specified behavior and that is the justification to record, and if it specifies more than this child delivers, record the remaining gap rather than amending the spec to match a partial implementation. SECOND, if OQ-01 chooses a `check` rule, the rule table is documented in the check engine's own contract and a new rule id belongs in whatever document enumerates them; grep for a rule-id enumeration outside the code before adding one.
Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Is the view a `check` rule, a read surface, or both?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer only if a new rule severity is proposed
- Resolution or deferral rationale: NOT blocking, because E-02 requires a read-only surface answering the source-selector question either way, and both shapes satisfy the item's minimum version. The considerations, measured: a `check` RULE runs on every `aw check` and in CI, so over 17 legitimate clusters it must be `info` (F-5) or it reds every run, and an `info` finding that always fires on correct work is close to noise. A READ SURFACE is consulted deliberately by whoever graduates, which matches "advisory and read-only", but only helps if someone runs it, which is precisely why child 02 wires it into the graduation path. The likely right answer is the read surface FIRST (it is what child 02 calls) with a rule only if the maintainer wants passive surfacing. Decide and record; do not add a `warning`-severity rule.

### OQ-02: Should the view report a source with ZERO plans as a distinct outcome?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-04 covers the zero case as a fixture either way and the plan completes under both answers. It matters for how the surface reads during graduation: "no existing plans for this source" is the EXPECTED and reassuring answer, and rendering it identically to an error or to empty output would make the common case look like a failure. Recommend an explicit affirmative statement, since the view's purpose is to be consulted before authoring and its most frequent honest answer is "nothing yet, proceed".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the reverse index's construction, showing it REUSES the existing `From-Backlog:`/`From-Spec:` readers and iterators (show the CALL, not a similar regex), and name which symbol you consumed (`find_from_backlog_artifacts`, or both iterators directly with the reason a new function was needed: F-12). Paste the index entry for `25kzda` listing every citing ARTIFACT with its type, status and Set, with the count DERIVED rather than compared against the nine measured here, and confirm terminal directories are included by showing the `executed` members. PASTE THE SPEC CARRIER (F-11): show spec `6m4kow` present in the `25kzda` entry, and spec `77tr3o` present in the `kxkc04` entry; an index that reports only plans FAILS this validation regardless of how clean the rest is. Paste a grep proving no second parser for either field was added. Paste one of the five dual-link plans (F-8) appearing under BOTH of its sources. State `bwgyum`'s status at your execution time and which shared-traversal case applies (F-9).
  - Observed evidence: THE CONSTRUCTION, showing the actual CALLS to both existing iterators and both existing readers (`inspect.getsource(check_engine.build_graduation_reverse_index)`, body only):

    ```python
        index: Dict[Tuple[str, str], List[GraduationArtifact]] = {}
        for artifact_type, iterator in (
            ("plan", _iter_plan_ipds),
            ("spec", _iter_spec_records),
        ):
            for path, text in iterator(repo_root):
                sources: List[Tuple[str, str]] = [
                    ("backlog", m.group(1)) for m in _META_FROM_BACKLOG_RE.finditer(text)
                ] + [("spec", m.group(1)) for m in _ITEM_FROM_SPEC_RE.finditer(text)]
                if not sources:
                    continue
                declared_id = _read_declared_id(text) or ""
                status_match = _PLAN_STATUS_RE.search(_metadata_region(text))
                setid, _descriptive = _parse_setid(text)
    ```

    WHICH SYMBOL WAS CONSUMED, AND WHY NOT `find_from_backlog_artifacts` FOR THE WHOLE INDEX. Both iterators directly (`_iter_plan_ipds`, `_iter_spec_records`), plus both existing field readers (`_META_FROM_BACKLOG_RE`, `_ITEM_FROM_SPEC_RE`) and the existing identity/status/Set readers (`_read_declared_id`, `_PLAN_STATUS_RE` over `_metadata_region`, `_parse_setid`). `find_from_backlog_artifacts` answers the SINGLE-id6 question and is the right shared lookup for that; it cannot build the whole reverse map, because it takes a caller-supplied id6 and filters, so producing a map would call it once per source and re-walk the entire tree per source. That is the exact cost the in-tree `plan_gates_by_backlog` single-pass index at `check_engine.py` already works around, and this copies that shape. Also NOTE it covers only the `From-Backlog` half; there is no `find_from_spec_artifacts`. The reason is written into the new code's own comment block, not only here.

    THE `25kzda` ENTRY, COUNT DERIVED (`len(cluster.artifacts)`, printed, never compared to a literal):

    ```
    sources: 131 bullets: 243
    25kzda count 10 setids ('revsweep', 'runbypass', 'runcodes', 'runflags', 'runmixed', 'runtrail')
      plan wlxkoz executed     runcodes  .aw/records/plans/executed/20260830-runcodes-01-wlxkoz-...ipd.md
      plan 6lu3rq executed     runmixed  .aw/records/plans/executed/20260830-runmixed-01-6lu3rq-...ipd.md
      plan m73aet executed     runtrail  .aw/records/plans/executed/20260830-runtrail-01-m73aet-...ipd.md
      plan zub5f1 executed     runcodes  .aw/records/plans/executed/20260903-runcodes-02-zub5f1-...ipd.md
      plan sq61qd executed     runcodes  .aw/records/plans/executed/20260903-runcodes-03-sq61qd-...ipd.md
      plan uyeko5 executed     runflags  .aw/records/plans/executed/20260903-runflags-01-uyeko5-...ipd.md
      plan 76gsmv executed     revsweep  .aw/records/plans/executed/20260904-revsweep-01-76gsmv-...ipd.md
      plan 6ypimw executed     revsweep  .aw/records/plans/executed/20260904-revsweep-02-6ypimw-...ipd.md
      plan ki6tom not-executed runbypass .aw/records/plans/not-executed/20260904-runbypass-01-ki6tom-...ipd.md
      spec 6m4kow approved     (none)    .aw/records/specs/20260904-6m4kow-01-6m4kow-cross-type-review.spec.md
    terminal: 9
    ```

    TERMINAL DIRECTORIES ARE INCLUDED: nine of the ten members are terminal (eight `executed/` plus one `not-executed/`), so a view reading `pending/` only would have reported ONE artifact here. Mutation 2 below proves that empirically.

    THE SPEC CARRIER, BOTH REQUIRED CASES. `6m4kow` is the last row of the `25kzda` entry above. For `kxkc04`:

    ```
    kxkc04 5 [('plan', '84j8d7'), ('plan', '5942n7'), ('plan', 'ueg5cf'), ('plan', 'pgq326'), ('spec', '77tr3o')]
    ```

    NO SECOND PARSER FOR EITHER FIELD. Every `re.compile` of either pattern in the package:

    ```
    $ grep -rn 'compile(r"(?m)\^-.*From-' agent_workflows/*.py
    agent_workflows/check_engine.py:2767:_META_FROM_BACKLOG_RE = _re.compile(r"(?m)^- From-Backlog:[ \t]*(\S+)[ \t]*$")
    agent_workflows/check_engine.py:4277:_ITEM_FROM_SPEC_RE = _re.compile(r"(?m)^-[ \t]*From-Spec:[ \t]*(\S+)[ \t]*$")
    agent_workflows/releases.py:479:_FROM_BACKLOG_LINE_RE = re.compile(r"(?m)^- From-Backlog:[ \t]*\S+[ \t]*$\n?")
    agent_workflows/releases.py:540:_ITEM_FROM_BACKLOG_RE = re.compile(r"(?m)^- From-Backlog:\s*(\S+)\s*$")
    ```

    The two `check_engine` patterns are the PRE-EXISTING ones this work consumes (line numbers unchanged by this change; the new code adds neither). The two `releases.py` ones are also pre-existing and untouched: verified by `git show caa4c993 --stat`, which lists only `check_engine.py`, `cli.py` and the new test file, so `releases.py` was not modified at all.

    A DUAL-LINK PLAN UNDER BOTH OF ITS SOURCES. `84j8d7` carries `From-Backlog: kxkc04` AND `From-Spec: 77tr3o`:

    ```
    kxkc04 (backlog) -> [('plan', '84j8d7', 'executed')]
    77tr3o (spec)    -> [('plan', '84j8d7', 'executed')]
    ```

    RE-MEASURED AT EXECUTION, and the dual-link population GREW from the five this plan names to SIX: `h0zljh` (`vqv9im` + `7ckptx`), the four `orchretire` plans `84j8d7`/`5942n7`/`ueg5cf`/`pgq326` (each `kxkc04` + `77tr3o`), and NEW since review `4fodkt` (`vqv9im` + `7ckptx`). That is the derive-never-pin rule demonstrating itself a fourth time, and it is why `finditer` rather than `.search` is load-bearing rather than defensive. Also measured: ZERO artifacts carry more than one bullet of the SAME kind, and for every artifact the whole-text read equals the metadata-region read, so no bullet is being picked up from quoted prose.

    `bwgyum`'s STATUS AT EXECUTION TIME AND THE SHARED-TRAVERSAL CASE (F-9). `bwgyum` reads `- Status: approved` and is still in `.aw/records/plans/pending/`; `grep -rn "Graduated-To\|graduated-to-dangling" agent_workflows/` returns ZERO hits, so it has landed NOTHING. THIS CHILD LANDED FIRST. Per the orchestrator's coordination constraint the obligation therefore falls on `bwgyum` as the second to land: its `check.graduated-to-dangling` must resolve through what this child exposed (`build_graduation_reverse_index` / `graduation_cluster` in `check_engine`, beside its `_iter_plan_ipds`/`_iter_spec_records` siblings) rather than re-walking the tree. Nothing here makes its data stale, because this index derives the reverse edge from the `From-*` bullets it reads live on each call and caches nothing.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the ACTUAL output of the surface for `25kzda`, and separately for a single-artifact source and a zero-artifact source. State OQ-01's answer. Paste a grep proving no `count > 1` comparison exists in the added code. If a `check` rule was added, paste its `RuleSpec` showing severity `info` AND its invariant id (or the explicit empty-with-reason), name which of the two existing `info` rules you copied, and paste `aw check all`'s UNPIPED exit code before and after (`aw check all >/dev/null 2>&1; echo $?`) proving it did not become nonzero. Also paste per-rule counts before and after from the `diagnostics` array, showing no OTHER rule's count changed.
  - Observed evidence: OQ-01'S ANSWER: a READ SURFACE, `aw graduation <source-id6>`. NO `check` rule was added, so the `RuleSpec`/severity/invariant branch of this evidence requirement does not apply and nothing was copied from either `info` precedent. Recorded with its full reasoning as DECISION 02-jxxec8-D1 in the run's decisions register. In short: an `info` rule would fire on all 33 measured multi-artifact clusters on every `aw check` and in CI, most of which are CORRECT decomposition, landing in a stream already carrying 475 findings; and a rule cannot answer "I am about to graduate X, what exists?", which needs a selector.

    THE SURFACE ON `25kzda` (ten artifacts; paths elided mid-row for width only):

    ```
    $ python3 -m agent_workflows graduation 25kzda --no-color
    Existing artifacts for source 25kzda
    TYPE  ID      STATUS        SET        PATH
    plan  wlxkoz  executed      runcodes   .aw/records/plans/executed/20260830-runcodes-01-wlxkoz-...ipd.md
    plan  6lu3rq  executed      runmixed   .aw/records/plans/executed/20260830-runmixed-01-6lu3rq-...ipd.md
    plan  m73aet  executed      runtrail   .aw/records/plans/executed/20260830-runtrail-01-m73aet-...ipd.md
    plan  zub5f1  executed      runcodes   .aw/records/plans/executed/20260903-runcodes-02-zub5f1-...ipd.md
    plan  sq61qd  executed      runcodes   .aw/records/plans/executed/20260903-runcodes-03-sq61qd-...ipd.md
    plan  uyeko5  executed      runflags   .aw/records/plans/executed/20260903-runflags-01-uyeko5-...ipd.md
    plan  76gsmv  executed      revsweep   .aw/records/plans/executed/20260904-revsweep-01-76gsmv-...ipd.md
    plan  6ypimw  executed      revsweep   .aw/records/plans/executed/20260904-revsweep-02-6ypimw-...ipd.md
    plan  ki6tom  not-executed  runbypass  .aw/records/plans/not-executed/20260904-runbypass-01-ki6tom-...ipd.md
    spec  6m4kow  approved      -          .aw/records/specs/20260904-6m4kow-01-6m4kow-cross-type-review.spec.md

      10 linked artifact(s); Sets: revsweep, runbypass, runcodes, runflags, runmixed, runtrail
      ALREADY LANDED (9): wlxkoz [executed], 6lu3rq [executed], m73aet [executed], zub5f1 [executed], sq61qd [executed], uyeko5 [executed], 76gsmv [executed], 6ypimw [executed], ki6tom [not-executed] - read these before authoring; re-doing landed work is the costly case.
    ```

    A SINGLE-ARTIFACT SOURCE (derived from the index, not hand-picked: the first source whose bucket has length 1):

    ```
    $ python3 -m agent_workflows graduation 3gr7fk --no-color
    Existing artifacts for source 3gr7fk
    TYPE  ID      STATUS    SET          PATH
    plan  3b4f8u  executed  agentadhere  .aw/records/plans/executed/20260825-agentadhere-00-3b4f8u-...ipd.md

      1 linked artifact(s); Sets: agentadhere
      ALREADY LANDED (1): 3b4f8u [executed] - read these before authoring; re-doing landed work is the costly case.
    ```

    A ZERO-ARTIFACT SOURCE, rendered as an AFFIRMATIVE answer through the shared empty-result path (OQ-02, recorded as DECISION 02-jxxec8-D2):

    ```
    $ python3 -m agent_workflows graduation zzzzzz --no-color; echo "exit=$?"
    Existing artifacts for source zzzzzz
    ✓ CLEAN  nothing yet: no plan or spec links to source zzzzzz. Proceed.

    Active filters:
      source: zzzzzz
      kind: any

    Next  aw show zzzzzz (read the source before authoring)
    ...
    exit=0
    ```

    NO `count > 1` COMPARISON. Asserted by a TEST rather than only by a grep here, so a later edit that adds the prohibited rule goes red: `tests/test_graduation_view.py::NoUniquenessRuleTests::test_the_added_code_contains_no_count_comparison` extracts the region between `def build_graduation_reverse_index` and `class CloseVerdict`, strips comment lines (the prohibition is DISCUSSED in prose deliberately), and asserts `re.search(r"len\([^)]*\)\s*>\s*1", code_only)` is None. Its sibling `test_no_check_rule_was_registered_for_this_view` asserts no `RULE_REGISTRY` id contains `graduation` or `duplicate`. Both pass.

    `aw check all` UNPIPED EXIT CODE, BEFORE AND AFTER: `1` and `1`. Unchanged (it was already nonzero on this tree; what matters is that this change did not make it so, and did not change its class):

    ```
    before: $ aw check all >/dev/null 2>&1; echo $?   -> 1
    after:  $ aw check all >/dev/null 2>&1; echo $?   -> 1
    ```

    PER-RULE COUNTS, from the `diagnostics` array of the single `--agent` JSON object, before -> after:

    ```
    total before=475 after=486
    check.from-backlog-dangling: 1 -> 1
    check.from-backlog-gate-mismatch: 2 -> 2
    check.id6-collision: 19 -> 19
    check.id6-outside-metadata-region: 2 -> 2
    check.identity-absent-from-name: 2 -> 2
    check.ipd-lint-diagnostic: 1 -> 1
    check.ipd-uncarried-obligation: 58 -> 58
    check.lifecycle-transition-invalid: 7 -> 7
    check.live-bug-ungated: 2 -> 2
    check.name-nonconformant: 4 -> 4
    check.scope-drift: 376 -> 387   <== CHANGED
    check.system-layout-missing: 1 -> 1
    ```

    NO OTHER RULE'S COUNT CHANGED, and NO NEW RULE ID APPEARS (which is the substantive claim, since OQ-01 chose no rule). `check.scope-drift` rose by 11 and that rise is fully explained rather than waved at. Two of the eleven are THIS plan's own two out-of-scope paths (`command_surface.py`, `test_command_surface_declarations.py`; DECISION 02-jxxec8-D4). The other nine are attributed to FOUR OTHER plans' live begin receipts (`m7gvuz` 202->204, `4h7tt0` 42->45, `lc4unl` 60->62, `qdd5jq` 72->74), because `check_scope_drift` compares the whole working tree against each live receipt's frozen base and is documented as a TIME WINDOW, NOT AN ATTRIBUTION (`ipd_lifecycle._paths_changed_by_this_execution`: "In a shared checkout the range base..HEAD also contains every concurrent agent's commit"). Confirmed by inspection: those plans' findings name `agent_workflows/check_engine.py` and `agent_workflows/cli.py`, i.e. THIS child's files appearing in THEIR windows. A set-difference of (location, rule, detail) triples across the two runs reports exactly ONE new finding line and ZERO disappeared.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the limits statement AS IT APPEARS IN THE OUTPUT, not as a code comment or a plan quote. Confirm it addresses all three cases with the correct verdict each (visible, partly visible, undetectable), gives the reason for the undetectable one, and names `f1sw71`. Confirm it does NOT claim to detect duplication. Paste the COVERAGE BOUNDARY sentence too (F-13): it must name the artifact types searched and qualify what a zero-result answer does and does not prove, so the reassuring case is not read as a completeness claim.
  - Observed evidence: THE LIMITS STATEMENT AS IT APPEARS IN THE OUTPUT (verbatim tail of `python3 -m agent_workflows graduation 25kzda --no-color`; this is stdout, not a code comment and not a quote from this plan):

    ```
      ADVISORY ONLY: this view shows; it does not decide, and it refuses nothing.
      What it can and cannot tell you:
        - legitimate decomposition: VISIBLE - the Set and Order of each artifact are shown, so one Set with several Orders reads as the deliberate decomposition it is; a source with many artifacts is NOT a defect
        - accidental duplication: PARTLY VISIBLE - the view shows that two artifacts belong to DIFFERENT Sets, but it cannot compare their scopes, so it cannot tell overlapping work from adjacent work; a human must read them
        - already implemented: NOT DETECTABLE - there is no per-requirement tracking: a spec carries ONE whole-artifact status with no partial-implementation state, and `implemented` requires only a resolvable citation rather than semantic verification, so 'is requirement G5 built?' cannot be answered mechanically. Tracked by backlog `f1sw71`
      Searched: PLANS and SPECS (every lifecycle directory, including executed/ and the other terminal ones), matched by their `- From-Backlog:` / `- From-Spec:` bullet. Work that addresses this source WITHOUT carrying such a bullet is invisible here, so 'no artifacts' means 'nothing LINKED to it', never 'nothing exists'.
    ```

    ALL THREE CASES, EACH WITH THE CORRECT VERDICT: decomposition `VISIBLE`, duplication `PARTLY VISIBLE`, already-implemented `NOT DETECTABLE`. THE REASON FOR THE UNDETECTABLE ONE IS GIVEN (one whole-artifact status, no partial-implementation state, `implemented` needs only a resolvable citation rather than semantic verification) AND `f1sw71` IS NAMED. Asserted by `OutputHonestyTests::test_the_human_output_states_all_three_cases_with_its_verdict_for_each`.

    IT DOES NOT CLAIM TO DETECT DUPLICATION. The duplication row says explicitly "it cannot compare their scopes, so it cannot tell overlapping work from adjacent work; a human must read them", and the block opens "it does not decide, and it refuses nothing". Asserted negatively too by `test_the_output_does_not_claim_to_detect_duplication`, which fails if the output ever contains a detection claim.

    THE COVERAGE BOUNDARY SENTENCE is the final line above. It NAMES THE TYPES SEARCHED (plans and specs, every lifecycle directory including the terminal ones), names WHAT IS MATCHED (the two `From-*` bullets, so the input is the LINK and not the work), and QUALIFIES THE ZERO ANSWER in the same breath: "'no artifacts' means 'nothing LINKED to it', never 'nothing exists'". It is printed on EVERY answer including the zero case, which is the case it exists for; `test_the_human_output_qualifies_what_its_silence_proves` asserts it on the zero answer specifically.

    THE HONESTY REACHES THE MACHINE SURFACES TOO, which was not in the original requirement but is necessary for it to be true of the OUTPUT rather than of one renderer. `--json` carries `data.limits` (a list of `{case, verdict, why}`) and `data.coverage`. The COMPACT `--agent` record deliberately drops `data` (`CommandResult.to_agent_record`), so each verdict and the coverage boundary also travel as `Evidence`, which compaction preserves (DECISION 02-jxxec8-D3):

    ```
    $ python3 -m agent_workflows graduation 25kzda --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"graduation","outcome":"clean","exit":0,...,"findings":0,
     "evidence":["graduation-cluster",
                 "limit:legitimate decomposition:VISIBLE",
                 "limit:accidental duplication:PARTLY VISIBLE",
                 "limit:already implemented:NOT DETECTABLE",
                 "coverage:Searched: PLANS and SPECS (... ), never 'nothing exists'."],
     "next":"aw show 25kzda"}
    ```

    Asserted by `test_the_COMPACT_agent_record_still_states_every_limit`, which first asserts `data` is ABSENT (so the test would be vacuous if the schema changed) and then requires every verdict present.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the live-corpus test and its actual output, showing the largest real cluster is REPORTED and NOT flagged, with the count DERIVED (paste the derivation, and confirm no literal count is asserted). Paste the SECOND live assertion showing the spec carrier surfaces (`6m4kow` under `25kzda`, `77tr3o` under `kxkc04`). Paste all six fixture cases with output: zero, one, one-Set-many, many-Sets, all-terminal, and SPEC-ONLY. The all-terminal case is the costly one, so show it is clearly visible; the spec-only case is the one that would silently pass a plans-only implementation, so show it too.
  - Observed evidence: THE LIVE NO-FALSE-POSITIVE TEST, with its derivation, driven through the REAL CLI rather than only the helper (a helper-only assertion would be satisfied by a view that is clean in Python and flags at the CLI, which is the prohibited rule):

    ```python
    cluster = check_engine.graduation_cluster(REPO_ROOT, "25kzda", index=self.index)
    derived = len(cluster.artifacts)                       # DERIVED, never a literal
    self.assertGreater(derived, 1, "... count DERIVED, never pinned")
    self.assertEqual(cluster.artifact_count, derived)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli.main(["graduation", "25kzda", "--dir", str(REPO_ROOT), "--json"])
    record = json.loads(buf.getvalue())
    self.assertEqual(rc, 0, "a legitimate multi-artifact cluster must not make the view exit nonzero")
    self.assertEqual(record["diagnostics"], [], "the view flagged the {derived}-artifact 25kzda cluster ...")
    self.assertEqual(record["status"], "clean")
    self.assertEqual(len(record["data"]["artifacts"]), derived, "the cluster must be REPORTED in full")
    ```

    NO LITERAL COUNT IS ASSERTED ANYWHERE in the live class: every comparison is against `derived`, `len(...)`, or a membership test. The only numeric literals are `1` in `assertGreater(derived, 1)` (a floor proving the index read the corpus at all, not a total) and `3` in `assertEqual(len(GRADUATION_VIEW_LIMITS), 3)` (the CASE COUNT from the plan, not a corpus count).

    THE SECOND LIVE ASSERTION, the spec carrier:

    ```python
    kz = check_engine.graduation_cluster(REPO_ROOT, "25kzda", index=self.index)
    self.assertIn("6m4kow", [a.id6 for a in kz.artifacts if a.artifact_type == "spec"], ...)
    kx = check_engine.graduation_cluster(REPO_ROOT, "kxkc04", index=self.index)
    self.assertIn("77tr3o", [a.id6 for a in kx.artifacts if a.artifact_type == "spec"], ...)
    self.assertGreater(len([a for a in kx.artifacts if a.artifact_type == "plan"]), 1, ...)
    ```

    The third assertion is there so the spec check cannot be satisfied by an index that returns ONLY specs; both halves of the mixed cluster must survive.

    ALL EIGHT FIXTURE CASES AND ALL FIVE LIVE ASSERTIONS, ACTUAL OUTPUT (the plan required six fixtures; two were added: `--kind` non-conflation, and a dual-link artifact under both sources):

    ```
    $ python3 -m pytest tests/test_graduation_view.py -o addopts="" -v
    tests/test_graduation_view.py::ReverseIndexFixtureTests::test_a_source_with_no_artifacts_reports_an_empty_cluster PASSED
    tests/test_graduation_view.py::ReverseIndexFixtureTests::test_a_source_with_one_artifact_reports_it_with_type_status_and_set PASSED
    tests/test_graduation_view.py::ReverseIndexFixtureTests::test_several_artifacts_in_ONE_set_are_reported_as_one_set PASSED
    tests/test_graduation_view.py::ReverseIndexFixtureTests::test_artifacts_across_DIFFERENT_sets_expose_the_partly_visible_case PASSED
    tests/test_graduation_view.py::ReverseIndexFixtureTests::test_an_all_terminal_cluster_is_visible_and_flagged_as_landed PASSED
    tests/test_graduation_view.py::ReverseIndexFixtureTests::test_a_SPEC_ONLY_source_is_still_reported PASSED
    tests/test_graduation_view.py::ReverseIndexFixtureTests::test_a_dual_link_artifact_appears_under_BOTH_of_its_sources PASSED
    tests/test_graduation_view.py::ReverseIndexFixtureTests::test_the_two_link_kinds_are_not_conflated PASSED
    tests/test_graduation_view.py::LiveCorpusTests::test_the_largest_real_cluster_is_reported_and_flags_no_defect PASSED
    tests/test_graduation_view.py::LiveCorpusTests::test_the_spec_carrier_surfaces_in_the_live_cluster PASSED
    tests/test_graduation_view.py::LiveCorpusTests::test_terminal_directories_are_included_not_filtered PASSED
    tests/test_graduation_view.py::LiveCorpusTests::test_a_real_dual_link_plan_appears_under_both_of_its_sources PASSED
    tests/test_graduation_view.py::LiveCorpusTests::test_the_live_index_covers_both_artifact_types PASSED
    tests/test_graduation_view.py::OutputHonestyTests::test_the_human_output_states_all_three_cases_with_its_verdict_for_each PASSED
    tests/test_graduation_view.py::OutputHonestyTests::test_the_human_output_qualifies_what_its_silence_proves PASSED
    tests/test_graduation_view.py::OutputHonestyTests::test_the_output_does_not_claim_to_detect_duplication PASSED
    tests/test_graduation_view.py::OutputHonestyTests::test_the_json_record_carries_the_cluster_and_the_limits PASSED
    tests/test_graduation_view.py::OutputHonestyTests::test_the_COMPACT_agent_record_still_states_every_limit PASSED
    tests/test_graduation_view.py::OutputHonestyTests::test_the_surface_is_a_declared_read_leaf_with_no_findings_exit PASSED
    tests/test_graduation_view.py::NoUniquenessRuleTests::test_no_check_rule_was_registered_for_this_view PASSED
    tests/test_graduation_view.py::NoUniquenessRuleTests::test_the_added_code_contains_no_count_comparison PASSED
    ============================== 21 passed in 3.96s ==============================
    ```

    THE ALL-TERMINAL CASE IS CLEARLY VISIBLE: its fixture writes two `- Status: executed` plans into `plans/executed/` and asserts BOTH that the cluster reports 2 artifacts AND that `len(cluster.terminal_artifacts) == 2`, i.e. that they are surfaced AS ALREADY LANDED rather than merely counted. In the human renderer that becomes the `ALREADY LANDED (n): ... - read these before authoring; re-doing landed work is the costly case.` line shown in V-02. Mutation 2 in V-05 shows this fixture is what catches a pending-only reader.

    THE SPEC-ONLY CASE writes a spec carrying `- From-Backlog:` and NO PLAN AT ALL, then asserts the cluster has one member whose `artifact_type == "spec"`. Mutation 3 in V-05 shows it is what catches the plans-only regression.

    FULL SUITE, BARE, IN THIS WORKTREE, baseline first (before any edit) then after:

    ```
    baseline: 1 failed, 8022 passed, 3 skipped, 2 xfailed, 3 warnings in 385.68s (0:06:25)
    after:    1 failed, 8043 passed, 3 skipped, 2 xfailed, 3 warnings in 260.38s (0:04:20)
    ```

    COMPARED BY FAILING NODE ID, NOT BY TOTAL: the single failure is the SAME node in both runs, `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, and it is ENVIRONMENTAL to this lane rather than caused by this work: it asserts that a NON-isolated turn receives no `OPENCODE_CONFIG_CONTENT` denial policy, and this turn runs INSIDE an isolated lane worktree whose environment carries exactly that policy. It touches none of this change's files. The +21 passed is exactly the 21 new tests in `tests/test_graduation_view.py`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste ALL THREE mutations in full. Mutation 1: introduce a `count > 1` rule, paste the live-corpus assertion FAILING and showing it flagged the legitimate clusters, revert, paste passing. Mutation 2: make the view ignore terminal plans, paste the all-terminal fixture FAILING, revert, paste passing. Mutation 3 (F-11): make the index read `_iter_plan_ipds` ONLY, paste BOTH the spec-only fixture and the spec-carrier live assertion FAILING, revert, paste passing. All three are required: mutation 1 proves the anti-over-reach guard works, mutation 2 proves the costly case is covered, and mutation 3 proves the plans-only regression that `bklgrad` `v58bvy` E-06 already fixed once cannot silently return.
  - Observed evidence: All three mutations were applied to the COMMITTED implementation (commit `caa4c993`) and reverted with `git checkout --`, so each revert is byte-exact rather than a re-edit. Six outputs follow.

    MUTATION 1: INTRODUCE THE PROHIBITED `count > 1` RULE, in `cli.py`'s `_run_graduation`:

    ```python
    # MUTATION 1 (E-05, temporary): the PROHIBITED `count > 1` uniqueness rule.
    _mutation_diagnostics = []
    if len(cluster.artifacts) > 1:
        from agent_workflows.result_types import Diagnostic as _D
        _mutation_diagnostics.append(
            _D(location=str(repo_root), rule="check.graduation-duplicate",
               detail=f"{source} already has {cluster.artifact_count} artifacts")
        )
    ...
            status="findings" if _mutation_diagnostics else "clean",
            exit_code=1 if _mutation_diagnostics else 0,
            diagnostics=_mutation_diagnostics,
    ```

    FAILING (the live-corpus assertion, flagging the LEGITIMATE cluster):

    ```
    $ python3 -m pytest tests/test_graduation_view.py -o addopts="" -q
            rc = cli.main(["graduation", "25kzda", "--dir", str(REPO_ROOT), "--json"])
        record = json.loads(buf.getvalue())
    >       self.assertEqual(
                rc, 0, "a legitimate multi-artifact cluster must not make the view exit nonzero")
    E       AssertionError: 1 != 0 : a legitimate multi-artifact cluster must not make the view exit nonzero
    FAILED tests/test_graduation_view.py::OutputHonestyTests::test_the_COMPACT_agent_record_still_states_every_limit
    FAILED tests/test_graduation_view.py::OutputHonestyTests::test_the_json_record_carries_the_cluster_and_the_limits
    FAILED tests/test_graduation_view.py::LiveCorpusTests::test_the_largest_real_cluster_is_reported_and_flags_no_defect
    3 failed, 18 passed in 18.52s
    ```

    The rule fired on the real ten-artifact `25kzda` cluster, which is CORRECT decomposition, exactly the over-reach the item warns about. AFTER REVERT (`git checkout -- agent_workflows/cli.py`): `21 passed in 15.54s`.

    MUTATION 2: MAKE THE VIEW IGNORE TERMINAL PLANS, in `build_graduation_reverse_index`:

    ```python
    # MUTATION 2 (E-05, temporary): ignore terminal plans, i.e. read `pending/` only.
    if artifact_type == "plan" and "/pending/" not in str(path).replace("\\", "/"):
        continue
    ```

    FAILING (the all-terminal fixture, plus the live terminal-inclusion assertion):

    ```
    $ python3 -m pytest tests/test_graduation_view.py -o addopts="" -q
    E       AssertionError: 1 not greater than 1 : spec 25kzda is the repository's largest source
            cluster; if this is <=1 the index is not reading the corpus (count DERIVED, never pinned)
    FAILED tests/test_graduation_view.py::OutputHonestyTests::test_the_json_record_carries_the_cluster_and_the_limits
    FAILED tests/test_graduation_view.py::ReverseIndexFixtureTests::test_an_all_terminal_cluster_is_visible_and_flagged_as_landed
    FAILED tests/test_graduation_view.py::LiveCorpusTests::test_terminal_directories_are_included_not_filtered
    FAILED tests/test_graduation_view.py::LiveCorpusTests::test_the_spec_carrier_surfaces_in_the_live_cluster
    FAILED tests/test_graduation_view.py::LiveCorpusTests::test_a_real_dual_link_plan_appears_under_both_of_its_sources
    FAILED tests/test_graduation_view.py::LiveCorpusTests::test_the_largest_real_cluster_is_reported_and_flags_no_defect
    6 failed, 15 passed in 10.04s
    ```

    THE REQUIRED FAILURE IS PRESENT (`test_an_all_terminal_cluster_is_visible_and_flagged_as_landed`), and the blast radius is itself informative: the ten-artifact live cluster collapsed to ONE, which is precisely the "view that silently dropped executed siblings" this mutation exists to catch. AFTER REVERT: `21 passed in 10.68s`.

    MUTATION 3: MAKE THE INDEX READ `_iter_plan_ipds` ONLY, the regression `bklgrad` `v58bvy` E-06 already fixed once:

    ```python
    # MUTATION 3 (E-05, temporary): PLANS ONLY - the exact regression bklgrad v58bvy E-06 fixed.
    for artifact_type, iterator in (
        ("plan", _iter_plan_ipds),
    ):
    ```

    FAILING (BOTH required assertions: the spec-only fixture AND the live spec-carrier assertion):

    ```
    $ python3 -m pytest tests/test_graduation_view.py -o addopts="" -q
    E       AssertionError: '6m4kow' not found in [] : spec 6m4kow carries `- From-Backlog: 25kzda`-side
            provenance for this source and MUST appear; a plans-only reverse index omits it and thereby
            hides the already-addressed case the view exists to show
    E       AssertionError: Items in the second set but not the first:
    E       'spec'
    FAILED tests/test_graduation_view.py::ReverseIndexFixtureTests::test_a_SPEC_ONLY_source_is_still_reported
    FAILED tests/test_graduation_view.py::LiveCorpusTests::test_the_spec_carrier_surfaces_in_the_live_cluster
    FAILED tests/test_graduation_view.py::LiveCorpusTests::test_the_live_index_covers_both_artifact_types
    3 failed, 18 passed in 8.35s
    ```

    `'6m4kow' not found in []` is the exact silent failure the plans-only shape produces: the `25kzda` cluster still reports nine plans and goes quiet about the spec that already addresses the source. AFTER REVERT: `21 passed in 7.68s`, and `git status --short` is clean, so no mutation residue survives.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the three paths in `- Scope-Paths:`. Do NOT implement a `count > 1` rule, a refusal, or any gate. Do NOT attempt the already-implemented verdict. Do NOT add a `warning`-severity rule. Do NOT add a second parser for `From-Backlog:`/`From-Spec:`. Do NOT build a THIRD traversal of this edge when `find_from_backlog_artifacts` already answers the backlog half (F-12). Do NOT ship a PLANS-ONLY index: specs are carriers and omitting them reintroduces a fixed defect (F-11). Do NOT change either forward dangling check or any existing rule severity. Do NOT pin a live corpus count in a test. Do NOT wire the view into the graduation path (child 02 owns that). Do NOT edit spec `25kzda`'s §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find the `check.from-backlog-dangling` and `check.from-spec-dangling` implementations, `find_from_backlog_artifacts`, `find_from_backlog_plans`, `find_from_backlog_specs`, `_iter_plan_ipds`, `_iter_spec_records`, `_META_FROM_BACKLOG_RE`, `_ITEM_FROM_SPEC_RE`, `_DEFAULT_RULESPEC`, `RULE_REGISTRY` and `drift_exit_code` by name. Every line number cited anywhere in this plan was measured at review round 2 and is an orientation aid only.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved jxxec8 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. Do NOT close backlog `6h7y2y` here: its Half 1 ships in child 02, and closing it after the guard alone would claim a graduation path that is still unreachable. Child 02 (`iuxtjy`) closes it.
