# IPD: Surface an id6 collision on the lookup surfaces instead of rendering it as an ordinary multi-result list

- Date: 2026-09-08
- Kind: child
- Concern: `aw find` PRESENTS A DUPLICATE id6 AS AN UNREMARKABLE MULTI-RESULT ANSWER, WITH EXIT 0, so the surface an operator uses to LOOK UP an artifact is the surface most likely to meet a corrupt identity first and it says nothing. The judgement already exists elsewhere in the package and `find` simply does not consult it: `selectors.resolve_for_mutation` treats exactly this case as fatal in its own words, an id6 matching several files being "a `id6` collision matching multiple files (a data bug to fix, not overridable by --force)" (`selectors.py:652-655`), because `MATCH_ID6` is in `UNIQUE_KINDS` (`:69`) alongside `path` and `stem`, while `MATCH_SETID` is deliberately allowed to be multi-target (`:651`). So the repository has already decided a duplicate id6 is corruption; the read surface is the one place that renders it as normal.
  MEASURED AT HEAD, AND THE ITEM'S OWN TWO EXAMPLES ARE BOTH GONE. `aw find y6mfgo` and `aw find ntf6sx` each return ONE plan today, because both instances were cleared in `ba8bcf2e`/`6a29f9c0` on 2026-08-31, the same commit that FILED the item. `aw attention` reports `valid: True`. A plan transcribing this item would therefore have been written against two examples that no longer exist, and its regression fixtures would have had nothing to reproduce.
  THE DEFECT IS STILL LIVE, ON A DIFFERENT AND MORE INTERESTING CASE. `aw find uyeko5` prints THREE rows with exit 0: the executed plan `runflags-01-uyeko5`, the research prompt `27rjro`, and a review file. Those three rows have THREE DIFFERENT CAUSES, which is precisely why one generic warning would be worse than useless: the plan is the genuine owner (`resolve` returns `kind=id6`); the research prompt is a PARSER ARTIFACT, since its real identity is `27rjro` and the `uyeko5` line is a QUOTED EXAMPLE in its prose at `:60` (that parser is fixed by plan `76w6mq`, from backlog `cqytxf` filed 2026-09-05, NOT by Order 01, whose E-04 was corrected to a consumption check); and the review file is CORRECT AND CONVENTIONAL, matched by `kind=substring` on its filename because a review record deliberately carries its SUBJECT's id6 in the identity slot.
  THE REVIEW CONVENTION IS THE FINDING THAT RESHAPES THIS PLAN, and it is why the item's recommended message would have been actively wrong. `.aw/records/reviews/README.md` states the rule explicitly: "`<id6>` is the REVIEWED ARTIFACT's id6, not a fresh identifier ... That is the load-bearing choice: the id6 is the repo's stable cross-tree handle, so the join survives a rename." So SEVENTY review files (measured: 70 review files, all 70 declaring a `- Subject-Id:`, and all 70 of those ids resolving to more than one artifact across types) legitimately share an id6 with their subject. The item's proposed warning, `! id6 <x> is held by 2 artifacts (plans, walkthroughs); an id6 identifies exactly ONE file (D140)`, would fire on EVERY reviewed plan in the repository. A warning that cries wolf 70 times is how a real one gets ignored.
- Scope: Make `aw find` DISTINGUISH a genuine identity collision from the legitimate reference conventions it currently renders identically, and flag only the former, naming the remedy that actually applies to the shape found. Read-only: `find` keeps SHOWING every match and keeps exit 0 for the human path. EXCLUDES the minting and detection half (Order 01), the two-tier re-authoring of `find` (`f8m2z2`), and setid uniqueness (`sjsoqq`).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/selectors.py, tests/test_cli_find.py, tests/test_find_collision_surface.py
- Item-Dependencies: executed:sk7ggr
- Status: to-review
- Set: id6integ
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: paw8so
- From-Backlog: h2ceme
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `h2ceme`, RESHAPED around a finding that makes the item's recommended message wrong. The item asks `find` to warn whenever an id6 is held by more than one artifact. MEASURED: 70 review files exist, all 70 declare a `- Subject-Id:`, and all 70 of those ids resolve to more than one artifact across types, because `reviews/README.md` REQUIRES a review to carry its subject's id6 in the identity slot as the deliberate cross-tree join. So the item's message would fire on every reviewed plan in the repo. The plan therefore turns on DISCRIMINATION rather than detection. Two further corrections. (1) The item's ROOT CAUSE citation is stale: it names `plans_index.run_find:401-410` as the bypass, but the CLI's `aw find` no longer routes there for the general case; `cli._run_find` fans out across every type via `_find_type_records`, which for plans calls `scan_plans` + `query` and for other types calls `selectors.resolve_selectors`, so the bypass is real but sits at a different symbol than the item names, and `resolve_one` deliberately drops the `resolve_for_mutation` policy layer. (2) The item's scope-honesty question ("confirm a plans-only find cannot see a walkthrough") is ANSWERED: `aw find` already spans every type, so the cross-type case is visible and the fix is not vacuous. A NEW asymmetry was found instead: `find` spans `reviews`, `comms` and `other`, while `check_collisions`'s SUPPORTED set does NOT include them, so `find` can see pairs the checker never examines - which is exactly why this plan cannot simply delegate to the checker's verdict.

## Goal

Make the lookup surface tell the truth about identity: flag a real collision with the remedy that fits its shape, and stay silent on the reference conventions the repository deliberately relies on.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: define what counts as a collision at this surface

- [ ] E-01 CLASSIFY THE MULTI-ROW CASES BEFORE CHANGING ANY OUTPUT, and write the classification down. This is the whole difficulty of the plan: `aw find` currently renders at least four distinct situations identically, and three of them are legitimate.
  THE FOUR SHAPES, each with a live or measured example. (a) GENUINE CROSS-TYPE DUPLICATE: two artifacts each DECLARE the same id6 as their own. (b) PARSER ARTIFACT: a document whose body QUOTES another artifact's metadata, read as a declaration; live today as research prompt `27rjro` "declaring" `uyeko5` at `:60`. That parser is fixed by plan `76w6mq` (from backlog `cqytxf`, filed 2026-09-05), NOT by Order 01: Order 01's E-04 was CORRECTED to a consumption check after the duplication was found. So this shape should vanish once `76w6mq` lands, which is NOT gated by this Set's own dependency edge, and E-01 must therefore re-measure rather than assume it has happened. (c) LEGITIMATE REFERENCE BY CONVENTION: a review record carrying its SUBJECT's id6 in its filename slot, required by `reviews/README.md`; 70 files, all 70 affected. (d) SAME-TYPE LIFECYCLE DUPLICATE: one plan present in two disposition directories (the `ntf6sx` shape). No instance exists today.
  USE `resolve`'s OWN `kind` AS THE PRIMARY DISCRIMINATOR, because it already distinguishes (a) from (c) without new heuristics. Measured: for `uyeko5`, `resolve(..., 'plans', tok).kind == 'id6'` while `resolve(..., 'reviews', tok).kind == 'substring'`. A row matched by SUBSTRING on a filename is a reference, not an identity claim; a row matched by `id6` is a declaration. That distinction is already computed and is currently thrown away by the display layer.
  - Depends on: none
  - Expected outcome: a written classification of the multi-row shapes with, per shape, the discriminator that identifies it and whether it warrants a warning; re-measured at your HEAD after Order 01 landed.
  - Execution state: pending

- [ ] E-02 STOP DISCARDING THE MATCH KIND IN THE DISPLAY LAYER, so the classification of E-01 is available where the decision must be made. `cli._find_type_records` resolves per type and returns formatted LINES plus paths; the `Resolution.kind` that would answer "was this an identity match or a filename match" is computed inside `resolve` and dropped.
  RE-LOCATE BY SYMBOL. The item's cited `plans_index.run_find:401-410` is NOT the general CLI path: `cli._run_find` fans out over `at.ARTIFACT_TYPES` calling `_find_type_records`, which uses `scan_plans` + `query` for plans and `sel.resolve_selectors` for other types. `plans_index.run_find` remains registered as the plans backend in `artifact_types.TYPE_BACKENDS`, so BOTH paths exist and you must establish which one your invocation takes before editing either.
  NOTE THE PLANS PATH DOES NOT GO THROUGH `resolve` AT ALL FOR ITS DISPLAY DATA. It calls `scan_plans` and intersects with `resolve_selectors`' paths, so for plans you have the paths but not the kind unless you ask `resolve` directly. Say in a comment which source of truth you chose and why, because a future reader will otherwise assume the two agree.
  DO NOT CHANGE WHAT `find` RETURNS. Every matching row must still be printed. This E-item threads metadata through; it removes no result.
  - Depends on: E-01
  - Expected outcome: the display layer knows, per row, whether the match was an identity declaration or a filename reference; the returned result set is byte-identical to today's; the chosen source of truth is documented at the site.
  - Execution state: pending

### Task group 2: flag the real thing, name the right remedy

- [ ] E-03 EMIT A WARNING ONLY FOR A GENUINE DUPLICATE, and name the remedy for the SHAPE FOUND rather than a generic one. The item is right that conflating shapes is worse than silence, and its own two shapes have different fixes.
  THE TWO REMEDIES, kept distinct. Same id6 across DIFFERENT types where both DECLARE it: the non-owning artifact needs its own id6 plus a typed reference to its source (`aw rename <type> <path> --to-id6`, then a `Target-Id:`/`References:` field), per D140. Same id6, SAME type, two lifecycle directories: one copy is stale and must be removed or retired, which is a lifecycle problem and not an identity one. Emitting one message for both would send half of readers down the wrong path.
  SAY NOTHING FOR A REVIEW RECORD MATCHED BY ITS SUBJECT'S id6. This is non-negotiable and is the reason the item's proposed message could not ship: 70 files would trigger it. If your implementation cannot avoid warning on those, the discrimination in E-01/E-02 is not working and you must fix that rather than adding an exception list.
  KEEP EXIT 0 AND KEEP SHOWING EVERYTHING. `find` is read-only and is often exactly what someone runs WHILE diagnosing a mess, so refusing to answer would make it useless when most needed. A structured finding in `--agent`/`--json` output is where a machine consumer gets an actionable signal; a hard exit code, if wanted at all, belongs behind an explicit `--check` flag mirroring `aw attention --check`, and this plan does not add one.
  - Depends on: E-02
  - Expected outcome: a genuine duplicate produces one warning naming its shape's remedy; a review-convention match produces none; exit stays 0; every row still prints.
  - Execution state: pending

- [ ] E-04 DO NOT FORK A SECOND DETECTOR, and record honestly why this surface cannot simply ask the existing one. The item's recommendation 3 says to reuse `check_engine.check_collisions` rather than growing a duplicate scan, and the principle is right, but a measurement complicates it.
  THE MEASURED OBSTACLE: `check_collisions`'s `SUPPORTED` set is `backlog, plans, prompts, releases, research, roadmaps, specs, walkthroughs`, while `aw find` spans `at.ARTIFACT_TYPES`, which ALSO includes `reviews`, `comms` and `other`. So `find` can display a pair the checker never examines, and delegating wholesale would make `find` silent on exactly the type (reviews) whose convention this plan must reason about. Also relevant: `check_collisions` builds a repo-wide inventory, which is a real cost to pay inside an interactive lookup.
  SO THE RULE IS: SHARE THE PREDICATE, NOT THE SCAN. Reuse the existing NOTION of a collision (`UNIQUE_KINDS` and `resolve`'s `kind`, which are already the authority `resolve_for_mutation` consults) rather than re-implementing "same id6 twice" with new heuristics, and do not invoke the repo-wide scan from a lookup. If you find yourself writing a fresh duplicate-detection loop, stop: that is the fork this E-item exists to prevent, and the two surfaces will drift and disagree about what a collision is.
  - Depends on: E-03
  - Expected outcome: no second duplicate-detection implementation exists; the warning derives from the existing `UNIQUE_KINDS`/`resolve` authority; no repo-wide collision scan is invoked from `find`; the type-coverage gap between `find` and the checker is documented.
  - Execution state: pending

### Task group 3: prove it on the shapes that actually exist

- [ ] E-05 TEST EVERY SHAPE, INCLUDING THE THREE THAT MUST STAY SILENT, using fixtures rather than the live tree. Four assertions minimum: a genuine cross-type declared duplicate warns, with the D140 remedy; a same-type two-directory duplicate warns, with the lifecycle remedy; a review record carrying its subject's id6 does NOT warn; and a setid multi-match does NOT warn, because `MATCH_SETID` is deliberately multi-target (`selectors.py:651`).
  BUILD FIXTURES, DO NOT ASSERT AGAINST THE LIVE REPOSITORY. Neither of the item's two examples exists any more, which is itself the lesson: a test pinned to live records rots. The live tree may be used for a one-off measurement in evidence, never as a test's input.
  ASSERT THE FALSE-POSITIVE COUNT REPO-WIDE, since that is the failure this plan most needs to avoid. Run the new logic over every reviewed id6 in the real tree as a MEASUREMENT (70 files measured at authoring) and report how many warnings it produces; the target is ZERO. A single warning there means the convention is being flagged as corruption.
  RUN THE SUITE BARE and judge on the DELTA. Baseline on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `test_orchestrator_retirement` case. Roughly 32 further failures inside a lane are environmental. Criterion: AFTER minus BEFORE is EMPTY.
  ALSO ASSERT THE READ CONTRACT IS UNCHANGED: same rows, same order, exit 0, and `--paths` output byte-identical, since scripts consume it.
  - Depends on: E-04
  - Expected outcome: all four shapes asserted from fixtures; zero warnings across the real tree's reviewed ids; the read contract byte-unchanged; bare-suite delta empty with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE COLLISION POLICY ALREADY EXISTS AND IS ALREADY WRITTEN DOWN. `resolve_for_mutation` refuses a `UNIQUE_KINDS` multi-match as "a data bug to fix, not overridable by --force" (`selectors.py:652-655`); `MATCH_ID6` is in `UNIQUE_KINDS` (`:69`) and `MATCH_SETID` is explicitly excluded (`:651`). This plan makes a READ surface consult the same notion.
- `resolve_one` DELIBERATELY DROPS THE POLICY LAYER: it is a back-compat shim returning `resolve(...).paths` and nothing else (`selectors.py:666-676`), which is precisely how the ambiguity verdict is lost on the read path.
- A REVIEW RECORD CARRIES ITS SUBJECT'S id6 BY DESIGN (`reviews/README.md`), as the deliberate cross-tree join that survives a rename. Measured: 70 review files, 70 declaring `Subject-Id`, all 70 of those ids resolving to more than one artifact. This is a convention to respect, never a collision to report.
- `aw find` SPANS MORE TYPES THAN `aw check` DOES. `at.ARTIFACT_TYPES` includes `reviews`, `comms` and `other`; `check_engine.SUPPORTED` does not. So the two surfaces cannot share a scan even though they must share a definition.
- THE CLI HAS TWO FIND PATHS. `cli._run_find` fans out through `_find_type_records`; `plans_index.run_find` is still the registered plans backend in `artifact_types.TYPE_BACKENDS`. Establish which one an invocation takes before editing.
- THE PLANS DISPLAY PATH DOES NOT CONSULT `resolve` FOR ITS DATA: it uses `scan_plans` + `query` and intersects with `resolve_selectors`' paths, so the match kind is not naturally available there.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the item's message would fire 70 times | A review record legitimately carries its SUBJECT's id6, by documented design. Measured: 70 review files, all 70 declaring `Subject-Id`, and all 70 of those ids resolving to more than one artifact across types. The item's proposed warning would flag every reviewed plan in the repository. | `reviews/README.md` ("the REVIEWED ARTIFACT's id6, not a fresh identifier"); counts measured at HEAD |
| F-2 | HIGH | BOTH of the item's examples are gone | `aw find y6mfgo` and `aw find ntf6sx` each return ONE plan today; both instances were cleared in `ba8bcf2e`/`6a29f9c0` (2026-08-31), the same commit that FILED the item. `aw attention` reports `valid: True`. | both commands run at HEAD; `git log` on those shas |
| F-3 | HIGH | the defect is still live, on a three-cause example | `aw find uyeko5` prints THREE rows with exit 0, from THREE different causes: a genuine owner (`kind=id6`), a parser artifact (research prompt `27rjro` quoting `- Id: uyeko5` at `:60`, owned by `76w6mq`/`cqytxf`, not by this Set), and a correct review reference (`kind=substring`). One generic warning cannot serve all three. | command run at HEAD; `resolve` kinds measured per type |
| F-4 | HIGH | the discriminator already exists and is discarded | `resolve` returns a `kind`, and it already separates declaration from filename reference: for `uyeko5`, plans -> `kind=id6`, reviews -> `kind=substring`. The display layer throws it away. | measured via direct `selectors.resolve` calls |
| F-5 | MEDIUM | the item's root-cause citation is stale | It names `plans_index.run_find:401-410` as the bypass. The general CLI path is `cli._run_find` -> `_find_type_records`, which uses `scan_plans`+`query` for plans and `resolve_selectors` elsewhere. The bypass is real but at a different symbol, and `plans_index.run_find` is still registered as the plans backend, so BOTH paths exist. | `cli.py` `_run_find`/`_find_type_records`; `artifact_types.TYPE_BACKENDS` |
| F-6 | MEDIUM | the item's scope-honesty worry is answered | It asks whether a plans-only `find` could see a walkthrough at all, warning the fix might be vacuous. `aw find` already fans out over every artifact type, so the cross-type case IS visible. | `_run_find` iterating `at.ARTIFACT_TYPES` |
| F-7 | MEDIUM | but a NEW coverage asymmetry exists | `find` spans `reviews`, `comms`, `other`; `check_engine.SUPPORTED` does not. So `find` can display pairs the checker never examines, which is why it cannot simply delegate to the checker's verdict. | `at.ARTIFACT_TYPES` versus `ce.SUPPORTED`, both printed |
| F-8 | MEDIUM | the policy layer is dropped on purpose | `resolve_one` is a back-compat shim returning only `.paths`, so the `UNIQUE_KINDS` verdict `resolve_for_mutation` acts on never reaches a read caller. | `selectors.py:666-676` |
| F-9 | LOW | exit 0 is the right default | `find` is read-only and is run WHILE diagnosing. A nonzero exit would change a read verb's contract and could break a caller piping it; the actionable signal belongs in structured output. | the item's own recommendation 4, adopted |
| F-10 | LOW | Order 01 changes this plan's input | Order 01 E-04 bounds identity parsing to front matter, which should make the research-prompt row vanish. This plan must re-measure after that lands rather than encoding today's three-row output. | Order 01 `sk7ggr` E-04 |

## Proposed changes (ordered, validatable)

1. Classify the four multi-row shapes and name the discriminator for each, re-measured after Order 01 (E-01).
2. Thread the match kind through the display layer without changing the result set (E-02).
3. Warn only for a genuine duplicate, with the remedy matching its shape, at exit 0 (E-03).
4. Share the existing collision NOTION rather than forking a detector or invoking the repo-wide scan (E-04).
5. Prove all four shapes from fixtures, with zero false positives across the real tree's reviewed ids (E-05).

## Deferred / out of scope (with reason)

- MINTING AND DETECTION. Order 01 (`sk7ggr`) owns global minting, D140's declared-duplicate case, the prose-match parser bug, and the terminal-artifact enumeration. This plan is the PRESENTATION half and depends on Order 01, because the parser fix changes which rows exist.
- THE TWO-TIER RE-AUTHORING OF `aw find` (`f8m2z2`). The item suggests folding this work into that re-authoring. Declined as a SEQUENCING choice rather than a scope one: `f8m2z2` is an open backlog item with no plan, and its own text records that a filename-first tier cannot answer status queries and that precedence cannot change without sign-off. Waiting for it would park a live misreport behind unscheduled work. This plan is deliberately small and additive so it does not constrain that re-authoring: it adds no new precedence rule and no new resolver.
- A `--check` FLAG OR A NONZERO EXIT. Explicitly not added, per the item's own recommendation 4 and F-9: changing a read verb's exit contract could break a caller. Structured output carries the machine signal.
- SETID UNIQUENESS (`sjsoqq`). A setid multi-match is DELIBERATELY legitimate (`selectors.py:651`), and E-05 pins that it stays silent. Making setids unique is a separate policy decision.
- EDITING OR RENAMING ANY EXISTING ARTIFACT. This plan changes a report, not records. If it surfaces a genuine collision, that is a finding for a human.
- THE RESEARCH YAML DIALECT (`05aqbj`). Order 01 handles it only as far as the parser bound requires; full YAML fluency in selectors is that item's subject.
- `aw search`. A content search legitimately returns every mention. Only `find` claims to return the artifact that IS the selector.

## Scope check

- Over-scope: none. One display path, one metadata thread-through, two test modules.
- Scope-Paths justification: `agent_workflows/cli.py` holds `_run_find` and `_find_type_records`, the display layer that currently discards the match kind and prints the rows (E-02, E-03); `agent_workflows/selectors.py` holds `resolve`, `resolve_one`, `UNIQUE_KINDS` and `resolve_for_mutation`, i.e. the existing collision notion E-04 must share rather than fork, and is where a kind-preserving read helper belongs if one is needed; `tests/test_cli_find.py` is the existing `find` suite and must show the read contract unchanged; `tests/test_find_collision_surface.py` is new and carries the four-shape fixtures plus the false-positive measurement. `plans_index.py` is deliberately NOT in scope: F-5 establishes that the general CLI path does not run its `run_find`, so editing it would be speculative; if the executor establishes that a real invocation DOES route there and needs the same treatment, that is a scope-widening finding to record and reconcile at finalize, not a silent addition.
- Under-scope, stated rather than left as `none`: this plan does not change minting or detection, does not re-author `find` as two-tier, does not add a `--check` flag or change exit codes, does not address setid uniqueness, does not edit or rename any record, does not teach selectors YAML front matter, and does not touch `aw search`. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- FOUR FIXTURE-BASED SHAPE TESTS: genuine cross-type declared duplicate WARNS with the D140 remedy; same-type two-directory duplicate WARNS with the lifecycle remedy; review-convention match SILENT; setid multi-match SILENT.
- A REPO-WIDE FALSE-POSITIVE MEASUREMENT over every reviewed id6 in the real tree, reporting the warning count. Target ZERO; 70 review files were measured at authoring. This is a measurement in evidence, NOT a test input.
- READ-CONTRACT INVARIANCE: same rows in the same order for a normal single-match lookup, exit 0, and `--paths` output byte-identical, since scripts consume it.
- `aw find uyeko5` re-run after Order 01 has landed, with its output pasted, so the plan's own motivating example is reported as it actually stands rather than as authored.
- NEGATIVE PROOF that no second duplicate-detection loop was added and that no repo-wide collision scan is invoked from `find` (show the searches).
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`selectors.py`'s PRECEDENCE COMMENT BLOCK and `resolve_one`'s docstring are the authoritative prose on what each match kind means. `resolve_one`'s docstring must record that dropping the ambiguity verdict is what left the read surfaces silent, so the shim is not later reused for a new read path in the belief that it carries the policy.

`reviews/README.md` already states the subject-id6 convention clearly and needs no change; cite it at the code site instead, because a future reader looking at a suppression rule for reviews will otherwise take it for an exception hack rather than the documented design.

DECISIONS.md D140 governs. This plan does not amend it: D140 is about IDENTITY SLOTS, and the review convention is a documented reference use that D140's own text anticipates by distinguishing identity from reference. If the executor concludes the two genuinely conflict, that is a finding for a human and a spec-level question, not an edit to make in passing.

No spec change is expected. If spec text asserts that `aw find` returns exactly one artifact per id6, that is a claim this plan makes true only for the warning, not for the row set; declare the spec file in `Scope-Paths` before editing it, per the spec-amendment rule, and say why here.

## Open questions

### OQ-01: Should a review record's subject-id6 match be silent, or shown as an explicitly labelled reference?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SILENT AS TO WARNINGS, and it is not close. Warning is excluded by measurement: 70 review files carry a subject's id6 by documented design, so a warning fires 70 times and trains the reader to ignore it, which is the precise dynamic that makes the real case invisible. Whether the ROW might additionally be LABELLED as a reference is a display nicety this plan leaves alone, because `find`'s row format is consumed by readers and by `--paths` scripts and changing it is a separate, larger question that `f8m2z2` may settle. The rule implemented is therefore: reference matches print exactly as today and produce no warning.

### OQ-02: Should the warning live in `find` alone, or in every read surface that resolves an id6?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `find` ALONE, for now, because it is the surface the item names and the one an operator uses to LOOK UP an artifact, and because a narrow change is verifiable. The generalization is real but is a bigger contract question (every read verb's output shape), and doing it here would multiply the false-positive risk across surfaces before the discrimination has been proven in one. E-04's discipline is what keeps the door open: by sharing the existing `UNIQUE_KINDS`/`resolve` notion rather than forking a detector, a later plan can reuse the same predicate elsewhere instead of re-deriving it.

### OQ-03: What if Order 01's parser fix removes the only live example?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE PLAN STILL STANDS, AND E-01/E-05 ARE WRITTEN FOR IT. That outcome is likely: the research-prompt row is a parser artifact and should vanish. It changes nothing structural, because the defect is that `find` CANNOT DISTINGUISH a collision from a reference, and that is true whether or not an instance is present today. This is exactly why E-05 forbids asserting against live records and requires fixtures: the item's own two examples evaporated between filing and graduation, and a plan pinned to live state would have rotted the same way. The executor must re-run `aw find uyeko5` and report what it actually shows rather than reproducing this plan's authored measurement.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the written classification. It must name, per shape, the discriminator and the warn/silent verdict. Paste the RE-MEASUREMENT at your HEAD (after Order 01): `aw find uyeko5` output with its unpiped exit code, plus the `resolve(...).kind` per type for at least one id6 shared between a plan and its review, showing `id6` versus `substring`. If a shape has no live instance, say so rather than implying you observed one.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the code threading the match kind through, and state which source of truth you used for the PLANS path (whose display data comes from `scan_plans`+`query`, not from `resolve`) and why, quoting the comment you left. THEN paste before/after output of a normal single-match lookup proving the row set and order are byte-identical, and the `--paths` output likewise.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the ACTUAL output for a genuine cross-type duplicate fixture, showing the warning text and that the D140 remedy is named; then for the same-type two-directory fixture, showing the LIFECYCLE remedy and that it is a DIFFERENT message. Paste the unpiped exit code for both, which must be 0, and confirm every matching row still printed. Quote the structured `--agent`/`--json` finding for a machine consumer.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste NEGATIVE proof that no second duplicate-detection loop exists and that `check_collisions` is not invoked from the find path (show the searches). Paste the code showing the warning derives from the existing `UNIQUE_KINDS`/`resolve` authority. Paste the documented note about the type-coverage gap, and confirm in one sentence that `reviews`/`comms`/`other` are handled by the shared predicate even though the checker does not cover them.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of all four fixture tests, and quote the two SILENT assertions (review convention, setid multi-match) so it is visible they assert absence rather than presence. Paste the repo-wide false-positive MEASUREMENT over every reviewed id6 with its count; anything above zero is a FAILED validation, not a caveat. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This is Order 02 of a two-child Set and carries `- Item-Dependencies: executed:sk7ggr` deliberately. Order 01 must land first because its E-04 parser fix changes WHICH rows this surface has to classify: executing this plan against today's unfixed parser would build discrimination logic around a row that is about to disappear.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol by NAME, never by the line numbers cited here; note in particular that the item's original `plans_index.run_find` citation is already stale, which is why F-5 exists. Do NOT edit or rename any file under `.aw/records/`: if a genuine collision surfaces, report it. Build tests from FIXTURES, never from live records, and never report a repo-wide false positive as an acceptable caveat. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the zero-false-positive measurement across the real tree's reviewed ids.
