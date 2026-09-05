# IPD: make the review record artifact-neutral with Subject-Id and Subject-Type

- Date: 2026-09-04
- Kind: child
- Concern: THE REVIEW RECORD CANNOT DESCRIBE A SPEC REVIEW, so the repository's own checker would reject one. `review_findings.render_review` writes `- Plan-Id: <id6>` as the only subject field (`:353`), and `check_engine.check_review_dangling` resolves that field against the PLANS TREE ALONE, building its `known` set from `_iter_plan_ipds` (`:2477-2480`). File a review against a spec and `aw check` reports `check.review-dangling`, "Plan-Id ... does not resolve to any plan", advising you to "correct the Plan-Id ... or retire the review". That is a hard blocker for spec `25kzda` Section 3.3's mandated spec review and for its Section 4.8 checks, none of which can produce a record. The record carries no artifact-type field at all, so a review does not even record WHAT it reviewed. Notably the FILENAME grammar is already artifact-neutral (`build_review_name` delegates to `artifact_naming.build_clustered_name` with the `review` facet and the embedded id6 is simply the subject's), so only the front-matter field and the checker are plan-bound, which is evidence the original design intended neutrality and stopped short.
- Scope: Replace `- Plan-Id:` with the artifact-neutral pair `- Subject-Id:` plus `- Subject-Type: <ipd|spec>` across the writer, the parser, the checker, and every consumer, and migrate EVERY existing review record in the same change (36 at review time, and the count GROWS with each review, so it must be measured at execution and never hardcoded). Purely a SUBJECT-IDENTITY change: the findings columns, severity vocabulary, verdict vocabulary, decisions table, round structure, filename grammar, and every gating threshold stay exactly as they are. EXCLUDES the spec-review workflow and the attested transition (`5slbpi` owns both, and depends on this), excludes per-type review subdirectories (open backlog `sv0sf3`), and excludes any change to plan-review's behavior beyond reading and writing the new field names.
- Scope-Paths: agent_workflows/review_findings.py, agent_workflows/check_engine.py, agent_workflows/reviews.py, agent_workflows/specs.py, .aw/records/reviews, .aw/records/reviews/README.md, tests/test_review_findings.py, tests/test_review_findings_gate.py, tests/test_review_findings_cascade.py, tests/test_review_decisions.py, tests/test_selector_resolver_matrix.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: revsweep
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: eyh1fu
- Blocks-Release: next
- From-Spec: 6m4kow

## Workflow history
- 2026-09-05 executed (aw oc run): aw oc run self-finalize: eyh1fu verified (set revsweep, attempt 1).
- 2026-09-05 executed (opencode its_direct/pt3-claude-opus-5-1m-us): Executed in an isolated lane at base HEAD `97d5ddf4`. All six E-items performed, all six V-items verified with pasted evidence, `aw ipd lint --phase pre-transition` conforming. THE BLOCKER WAS OBSERVED BEFORE IT WAS REMOVED, which is what makes this a blocker removal rather than a rename: at pre-change HEAD a review whose subject was a REAL spec was reported `check.review-dangling` with the recovery text telling the author to retire it, and the failing-first assertion is now a tracked green test. THE RECORD IS NOW ARTIFACT-NEUTRAL: `- Subject-Id:` plus `- Subject-Type: <ipd|spec>`, both REQUIRED, `- Plan-Id:` replaced outright with no compatibility reader, the closed vocabulary declared once beside `SEVERITIES`/`DECISIONS`, and the H1 no longer hardcoding "Plan". Resolution is TYPE-DIRECTED through the existing `_iter_plan_ipds`/`_iter_spec_records` seams (no new path literal, AST guard still green), and an absent or unknown type is a LOUD parse error (`REV-M101`/`REV-M102`) rather than a default, because a defaulted type is exactly how a migration bug would hide. THE CORPUS COUNT HAD MOVED AGAIN, as F-4 predicted: 40 records at execution against 36 at review, 35 as authored, 34 in the spec, so the migration derived it from `iter_review_files` and asserted invariants instead. Migrated mechanically by a shown script that never re-derives an id6 from a filename and refuses to write on any front-matter/filename disagreement; none was found. E-03 and E-04 landed ATOMICALLY in one commit per F-9, so no intermediate state could arm `plan_gating_blocks` case (b) and block a plan's approval with no override. THE HIGHEST-VALUE WORK WAS E-05, the second consumer the plan originally missed: `_review_index` is repointed, and its safety is proven POSITIVELY (the `error`-severity escalation rule still FIRES) with an executable contrast case showing the fail-open empty-index path, because that failure mode is SILENCE and a green check cannot distinguish it from compliance. The two gating predicates were deliberately NOT renamed (prose only; names left to `wpomxa`), and the four modules that rename touches are untouched here. ONE IN-SCOPE ADDITION recorded rather than slipped in: `reviews.py`'s output key `plans` became `subjects`, since a subject may now be a spec; measured to have no documented contract and no consumer outside its module. Evidence: 192 passed across the five in-scope test modules (161 baseline plus this plan's 11 new tests plus the selector matrix); full bare suite 31 failed / 4430 passed against a 31 failed / 4419 passed baseline with a BYTE-IDENTICAL failure set (all 31 pre-existing runner/lifecycle-harness failures inherited at base HEAD); `aw check all` no-worsening at 25 findings with an identical rule mix and ZERO `check.review-dangling` over the migrated corpus; leak sanitizer clean. HONEST SCOPE LIMIT: this makes the record CAPABLE of describing a spec review and delivers no user-visible capability on its own; `5slbpi` produces the review.
- 2026-09-05 approved (aw set): status set to approved

- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 2 (cursory, scoped to the post-ruling edits) at HEAD `9bb47658`: APPROVE WITH REVISIONS APPLIED; R2-1, R2-2, R2-3 all FIXED. TWO REAL FINDINGS. R2-1: V-06 still asked which OQ-01 rename option the executor took, inviting a scope violation after the rename moved to `wpomxa`; it now requires confirming NO rename happened here. R2-2 (the one that mattered): the plan drove its migration off the STRING `Plan-Id` and never named the ATTRIBUTE spelling `doc.plan_id`, whose readers at `review_findings.py:805` and `:640` a string grep does not match. Leaving `:805` would make the gating predicate match a field nothing populates, returning EMPTY and opening the gate silently, the same failure class this plan's own F-9 calls expensive. E-02 now names both readers. R2-3 confirms the executable scope is back to exactly what round 1 approved (11 Scope-Paths, no runner modules, prose-only E-06). Round 2 record appended.

- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): POST-REVIEW EDIT, recorded because the `reviewed` verdict above predates it and no longer covers this text. Two changes, both from maintainer rulings the same day. (1) OQ-01 RESOLVED: rename the gating predicates. (2) That rename was then EXTRACTED into `wpomxa` (`revsweep-05`, `Item-Dependencies: executed:eyh1fu`) after a structural re-review, so E-06 is prose-only again and Scope-Paths returned from 15 entries to 11. WHY: carrying the rename made this plan span four modules its own concern never touches (`oc_runipd.py`, `agy_runipd.py`, `ipd_set_plan.py`, `plan_readiness.py`), two of them the highest-contention files in the repo, which is two of the IPD spec's three split triggers (spans several code regions; independently-executable phases). Verified independent before splitting: `plan_gating_blocks` takes an id6 and never reads the subject field, so the rename neither needs nor affects this plan's field change. The net effect on this plan is that its scope is now IDENTICAL to what was reviewed, so the verdict's coverage gap is limited to the OQ-01 rationale text and this note. `aw ipd lint` conforming after the edits.

- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1 at HEAD `024ab067`: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008, all FIXED in place, zero deferred, zero open. Target plan committed and unchanged at `0ee800f4`, so the pre-review snapshot was correctly skipped. `aw ipd lint` conforming at `--phase author` before review and again at `--phase review-finalize` after revisions. THE PLAN'S PREMISE VERIFIED EXACTLY: `render_review` hardcodes `- Plan-Id:` (`review_findings.py:353`) and `check_review_dangling` builds `known` from `_iter_plan_ipds` alone (`check_engine.py:2477-2480`), with the recovery text telling the author to retire the review, so the repository genuinely does reject a spec review. TWO FINDINGS WERE MATERIAL AND WOULD HAVE MADE THIS CHANGE A SILENT REGRESSION. PR-001 (BLOCKER, new E-05): the subject field has a SECOND consumer the plan never mentioned. `_review_index` (`:2673-2699`) reads the same `_REVIEW_PLAN_ID_RE` and backs four call sites implementing `check.review-finding-unescalated`, severity **error** and wired into two `aw ipd lint` checkpoints. Repointing only the dangling check would leave the index keyed on a field no record carries, so it returns EMPTY and every dependent rule takes its "nothing reviewed: every plan is the (a) absent case" early return: unfixed HIGH/BLOCKER findings would gate NOTHING, silently, which is the exact hole the `revgate` Set was built to close. PR-002 (BLOCKER): E-03's fail-closed parse error was costed as a reporting change, but a parse error is a `Diagnostic` and `plan_gating_blocks` case (b) treats ANY diagnostic as BLOCKING; that predicate gates both host runners, `/exec-set`, `aw check`, and `plan_readiness.approval_refusals`, where a gating finding has NO override BY DESIGN. So one record left unmigrated does not misreport, it blocks its plan's approval and its dependents' execution unfixably. Measured: 36/36 records parse with zero diagnostics today, so every instance is created by this change; E-03/E-04 must now be atomic or strictly ordered. ALSO CORRECTED: PR-003, two E-05 instructions rested on FALSE premises, since `Plan-Id` greps to ZERO in `.aw/system/workflows/` (the bodies never specify front matter, so the deliberate-parity concern does not arise) while the REAL contract is `.aw/records/reviews/README.md:155`, which the plan treated as a conditional check; PR-004, the plan's own advisory-severity verification was unsound, because `drift_exit_code` exempts only `info` so a `warning` exits 1 too, a misreading the codebase warns against in a comment written for exactly this purpose; PR-005, the corpus is 36 records not 35 (the spec says 34) and GREW during this Set's own operation, so the count must be derived not asserted; PR-006, `tests/test_selector_resolver_matrix.py` carries a `Plan-Id` fixture and was missing from Scope-Paths; PR-007, the F-5 contract claim was overstated, since the `reviews.py` prose CONCLUSION survives the rename (verified: the resolver matches `^-\s*Id:` and rejects both spellings) making it a careful prose fix; PR-008, the source spec `6m4kow` is still `to-review`, so approving this plan implicitly ratifies R-01..R-05. Four decisions recorded (D-1..D-4), all reversible. Baseline measured for attribution: the four review test modules are `161 passed` at `024ab067`. Review record: `.aw/records/reviews/20260904-revsweep-03-eyh1fu-make-the-review-record-artifact-neutral-with-subject-id-and.review.md`.

- 2026-09-04 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored with the `revsweep` Set, graduating requirements R-01 through R-05 of spec `6m4kow`, which in turn completes spec `25kzda` Section 3.3. THE BLOCKER IS EXACT AND MEASURED, not inferred: the writer hardcodes `- Plan-Id:` at `review_findings.py:353`, and `check_engine._REVIEW_PLAN_ID_RE` (`:2455`) feeds `check_review_dangling` (`:2458`) whose `known` set comes from `_iter_plan_ipds` (`:2477-2480`), so a spec-subject review is reported dangling BY THE REPOSITORY'S OWN CHECKER with a recovery message telling the author to retire it. BLAST RADIUS MEASURED AT `3d4e5414`: the literal string `Plan-Id` appears 21 times across 9 tracked Python files, concentrated in `check_engine.py` (9) and `tests/test_review_findings.py` (4), plus 35 `.review.md` records each carrying the field once. That is small enough to do in ONE change, which is why D-02 of the spec chose replacement over a compatibility shim, and it is also why the migration must be MECHANICAL and shown rather than hand-edited. ONE THING DELIBERATELY NOT CHANGED, recorded so an executor does not "finish the job": the review FILENAME grammar is already artifact-neutral (`build_review_name:228-244` delegates to the shared `build_clustered_name` with the `review` facet) and only its DOCSTRINGS claim otherwise, so R-05 requires correcting prose, not code. THE RISK THAT DECIDES THE ORDER OF THIS PLAN'S ITEMS: `Subject-Type` makes the checker's resolution TYPE-DIRECTED, so a wrong or missing type silently sends resolution at the wrong tree and a real subject would read as dangling. E-03 therefore makes an absent-or-unknown `Subject-Type` a PARSE ERROR rather than a defaulted `ipd`, because defaulting is precisely how 35 migrated records would hide a migration bug.

## Goal

Make a review record able to name any reviewable artifact type, so a spec review can be filed and validated, without changing anything about how findings, verdicts, or gating work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the blocker, then change the record's shape

- [x] E-01 Write the failing-first BLOCKER TEST before changing anything: construct a review record whose subject is a real SPEC and assert `aw check all` reports `check.review-dangling` for it. It MUST FAIL to be clean at current HEAD, demonstrating that the repository rejects a spec review today.
  This test is the plan's premise. Without it, the change looks like a rename; with it, the change is visibly a blocker removal. After E-03 the same subject must be clean, and a review whose subject genuinely does not exist must STILL be reported.
  - Depends on: none
  - Expected outcome: a test proving a spec-subject review is rejected at HEAD, with the `check.review-dangling` finding pasted.
  - Execution state: performed

- [x] E-02 Change the WRITER and PARSER to the neutral pair: `- Subject-Id: <id6>` and `- Subject-Type: <ipd|spec>`, both REQUIRED on every record, replacing `- Plan-Id:` outright rather than adding a second field.
  `Subject-Type`'s vocabulary is CLOSED at `ipd|spec` (spec `6m4kow` R-02, D-03). Represent it as a closed tuple in one place, the way `SEVERITIES` and `DECISIONS` already are (`review_findings.py:54`, `:57`), so a new type requires amending the vocabulary and the dispatch table together rather than being introduced by writing a novel value into a file.
  ALSO UPDATE THE H1, which currently reads `# Plan review findings: <plan_id>` (`:351`), since it names the artifact type in prose that will now sometimes be wrong.
  DO NOT TOUCH the findings columns, `SEVERITIES`, `DECISIONS`, the round structure, `plan_readiness.VERDICTS`, or any threshold. This item changes WHO the record is about, nothing about what it says.
  RENAMING `ReviewDocument.plan_id` HAS AN IN-FILE READER THE PLAN DID NOT NAME (added at re-review): `plan_gating_blocks` matches on `doc.plan_id` at `review_findings.py:805`, and the field is populated from `meta["plan-id"]` at `:640`. Both are inside this plan's fence and inside this item's concern, so update them here; they are called out only because a rename driven by a grep for the STRING `Plan-Id` would miss the ATTRIBUTE spelling `plan_id` and leave the gating predicate matching a field nothing sets, which F-9's no-override blocking path makes expensive.
  - Depends on: E-01
  - Expected outcome: writer and parser use the required neutral pair; the type vocabulary is closed and declared once; the H1 no longer hardcodes "Plan"; no findings/verdict machinery changed.
  - Execution state: performed

- [x] E-03 Make the dangling check TYPE-DIRECTED: resolve `Subject-Id` against the tree named by `Subject-Type`, not against the plans tree unconditionally. Note `_REVIEW_PLAN_ID_RE` (`check_engine.py:2455`) has TWO consumers, not one: `check_review_dangling` (`:2490`) and `_review_index` (`:2695`). E-06 owns the second; this item must not leave the regex serving both under a new name without the second being audited.
  MAKE AN ABSENT OR UNKNOWN `Subject-Type` A PARSE ERROR, NOT A DEFAULT. This is the item's real design decision and the reason it is separate: if a missing type quietly defaults to `ipd`, then a migration that dropped the field on some records would still resolve those against the plans tree, they would still pass, and the bug would be invisible until a spec review silently read as dangling.
  BUT MIND WHAT A PARSE ERROR COSTS, WHICH THE PLAN AS FIRST WRITTEN DID NOT ACCOUNT FOR (F-9). A parse error is a `Diagnostic`, and `plan_gating_blocks` case (b) treats ANY diagnostic as BLOCKING (`review_findings.py:807-811`): "a file that exists but cannot be trusted is an error, not an absence". That predicate gates BOTH host runners, `/exec-set`'s Set compiler, `aw check`'s escalation evaluator, and `plan_readiness.approval_refusals`, where a gating finding has NO OVERRIDE by design. So a record left without a valid `Subject-Type` mid-migration does not merely read as dangling: it BLOCKS its plan's approval and its dependents' execution, with no flag to get past it. Measured: all 36 records parse with ZERO diagnostics today, so this failure mode is entirely created by this change.
  THEREFORE MAKE THE MIGRATION AND THE PARSE ERROR ONE ATOMIC COMMIT, or land the parse error strictly AFTER the corpus is fully migrated and verified. Do not commit E-03 and E-04 separately in that order. State which you did.
  PRESERVE THE RULE'S ADVISORY SEVERITY. `check.review-dangling` is deliberately a `warning`, not an error, because "a review whose plan was deleted or superseded is untidy, not dangerous"; this plan makes it CORRECT for more types, and must not promote it to blocking as a side effect. DO NOT VERIFY THIS BY EXIT CODE: `artifact_core.drift_exit_code:415` exempts only `info`, so a `warning` DOES drive exit 1, and the codebase says so explicitly at `check_engine.py:172-176`. Verify advisoriness by the rule's registered `RuleSpec` severity and by the absence of any lifecycle gate, which is what the severity actually buys.
  PRESERVE THE PATH-LITERAL DISCIPLINE the function's own docstring records: discovery goes through `review_findings.iter_review_files`, and the function "deliberately contains NO `.aw/records/reviews` path literal". Do not add one while touching it. Resolving a SPEC subject needs a specs-tree id6 set, so obtain it through the same typed-iteration seam `_iter_plan_ipds` sits beside, not a new literal.
  - Depends on: E-02
  - Expected outcome: resolution is directed by `Subject-Type`; a spec-subject review with a real subject is clean; a genuinely missing subject of EITHER type is still reported; an absent/unknown type is a loud parse error; the parse error never lands on an unmigrated corpus; the rule stays advisory, verified by RuleSpec not exit code; no new path literal.
  - Execution state: performed

### Task group 2: migrate the corpus and every consumer

- [x] E-04 Migrate EVERY existing `.review.md` record MECHANICALLY, in this same change, setting `Subject-Type: ipd` for every one (all are plan reviews today) and renaming the field.
  COUNT THE CORPUS AT EXECUTION; DO NOT TRUST A NUMBER FROM THIS PLAN. The spec says 34, the plan said 35, and it measured 36 at review, because every plan-review adds one and this Set is itself producing reviews while it waits. Derive the count from `review_findings.iter_review_files` and assert "zero remaining `Plan-Id`" plus "every discovered record carries both fields", which are invariants that hold at any corpus size, rather than an equality against a stale literal that will fail for the wrong reason.
  DO IT WITH A SCRIPT AND SHOW THE SCRIPT. Hand-editing is one chance per file to typo an id6, and an id6 typo produces exactly the dangling finding this plan exists to eliminate. The safe transformation is a pure field RENAME plus an inserted `Subject-Type: ipd`, never a re-derivation of the id6 from the filename: the filename and the front matter are supposed to agree, so recomputing would silently repair a genuine mismatch this plan has no mandate to touch. If the script finds a record whose front-matter id6 and filename id6 disagree, STOP and report it rather than normalizing it.
  DO NOT LEAVE A COMPATIBILITY READER. Pre-release conventions forbid shims (spec `6m4kow` R-04) and a parser that accepts both fields would let a half-migrated corpus pass, which is the state that makes the next change unsafe.
  VERIFY EVERY MIGRATED RECORD STILL PARSES WITH ZERO DIAGNOSTICS, which is the one check that proves the migration did not arm the blocking path in F-9. Measured baseline: all 36 records parse clean today, so any diagnostic after migration is this change's own regression and gates a plan's approval.
  - Depends on: E-03
  - Expected outcome: every record migrated by a shown script; zero `Plan-Id` remaining anywhere in the tree; all `Subject-Id` values resolve; every record parses with zero diagnostics; no dual-field reader exists.
  - Execution state: performed

- [x] E-05 AUDIT AND REPOINT `_review_index`, THE SECOND CONSUMER OF THE SUBJECT FIELD, which the plan originally missed entirely and which carries far higher stakes than the advisory dangling check.
  `_review_index` (`check_engine.py:2673-2699`) reads the SAME `_REVIEW_PLAN_ID_RE` and maps subject id6 -> review files. It backs FOUR call sites (`:2753`, `:2858`, `:2955`, `:3124`), which implement `check.review-finding-unescalated` (severity **`error`**, wired into two `aw ipd lint` checkpoints) and `check.review-decision-unescalated`. So a subject-field change that repoints only the dangling check leaves the ESCALATION GATE keyed on a field no record carries, the index comes back empty, and every rule reading it silently returns "nothing reviewed: every plan is the (a) absent case" (`:2859`, `:3125`). That is a fail-OPEN outcome on an `error`-severity gate: unfixed HIGH/BLOCKER findings would stop gating anything, which is the exact hole `revgate` was built to close.
  SO THE BAR IS: the index is repointed to `Subject-Id`, and a test proves the escalation gate STILL FIRES after migration. A green `aw check` is NOT evidence here, because the failure mode is silence.
  DECIDE AND STATE whether resolution stays a single shared regex (preferred, one authority) or splits; if a `Subject-Type` filter is applied to the index, say why, since the escalation rules are plan-scoped and a spec-subject record must not be attributed to a plan id6.
  - Depends on: E-04
  - Expected outcome: `_review_index` reads the neutral field; all four dependent rules still evaluate; a test proves `check.review-finding-unescalated` still fires on an unescalated gating finding after migration; the empty-index fail-open path is shown NOT to be silently entered.
  - Execution state: performed

- [x] E-06 Update every remaining consumer and its documentation. MEASURED SURFACE at review, re-measured because the plan's figure was stale: the literal `Plan-Id` appears in 9 tracked Python files (excluding worktrees) as `check_engine.py` 9, `tests/test_review_findings.py` 4, `reviews.py` 2, and 1 each in `specs.py`, `review_findings.py`, `tests/test_review_findings_gate.py`, `tests/test_review_findings_cascade.py`, `tests/test_review_decisions.py`, and `tests/test_selector_resolver_matrix.py`.
  `tests/test_selector_resolver_matrix.py` WAS MISSING FROM SCOPE-PATHS and is now added: it writes a fixture record carrying `- Plan-Id:` (`:235`) to assert review-tree ownership, so it breaks or silently stops testing the real shape otherwise.
  INCLUDE THE DOCUMENTED CONTRACT, not just the code. `reviews.py:182-189` tells the reader that a review carries `- Plan-Id:` and that "an id6 selector does NOT match a review's front matter", and `:221` repeats it in a user-facing message. VERIFIED AT REVIEW: the claim stays TRUE after the rename, because the resolver matches `^-\s*Id:` exactly and neither `Plan-Id` nor `Subject-Id` matches it. So this is a PROSE correction, not a behavior change, and the corrected text must keep the "matched by FILENAME" promise intact rather than implying front-matter matching now works.
  ALSO CORRECT `specs.py:558-563`, whose comment justifies an inert verdict half with "`review_findings` keys review artifacts by `Plan-Id`, so no spec verdict exists to read". After this plan the KEY is neutral but the spec-review PRODUCER still does not exist (`5slbpi` owns it), so the comment must be re-grounded on the real remaining reason rather than deleted, or a later reader will think the verdict half is now live.
  Correct `review_findings`'s docstrings describing the filename's id6 as "the REVIEWED PLAN's id6" (`:19-21`, `:235`), and the PROSE of the gating predicates `plan_gating_blocks`/`plan_blocks_dependents` (`:759`, `:842`) where it describes a now-artifact-neutral predicate as plan-only.
  DO NOT RENAME THOSE TWO PREDICATES HERE. The maintainer ruled the rename IN (OQ-01), and it was then EXTRACTED into its own plan, `wpomxa` (`revsweep-05`), which depends on `executed:eyh1fu`. The extraction is why this plan's fence stops at prose: the rename touches four modules this plan never needs, two of them the highest-contention files in the repo, and bundling it here would let a merge conflict over function names delay a release-blocking blocker removal. Renaming them here would also collide with `wpomxa` directly.
  UPDATE `.aw/records/reviews/README.md`, which is the actual documented front-matter contract (`:155` shows `- Plan-Id: <id6 of the reviewed plan>`, `:161` describes the dangling rule). CORRECTION TO THE PLAN'S ORIGINAL CLAIM: the plan-review workflow BODIES do not specify the record's front matter at all (`Plan-Id` greps to ZERO in `.aw/system/workflows/`), so there is nothing to edit there and the parity concern does not arise. Do NOT invent front-matter instructions in those bodies to satisfy a stale instruction; if you judge they SHOULD specify it, that is new scope and needs saying.
  - Depends on: E-05
  - Expected outcome: zero `Plan-Id` references remain in code, tests, or records; the `reviews.py` contract prose corrected while keeping its filename-matching promise true; `specs.py`'s comment re-grounded; the reviews README updated; the two gating predicates' PROSE corrected with their names left alone for `wpomxa`; no workflow body edited on a false premise.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE REVIEW FILENAME GRAMMAR IS ALREADY ARTIFACT-NEUTRAL. `build_review_name` delegates to `artifact_naming.build_clustered_name` with the `review` facet, and the embedded `<id6>` is just the subject's. Only docstrings claim it is a plan's. This is why R-05 is a prose fix.
- `reviews` IS DELIBERATELY ABSENT FROM THE ARTIFACT-TYPE ENUM (`artifact_types.py:12-23`) and from `TYPE_FACET` (`artifact_naming.py:82-88`), with a long comment explaining that a review has NO status lifecycle ("its state is its Verdict plus per-finding Decision values, not a `- Status:` bullet") and that adding it to the iterated map would make `aw set` accept a review file. This plan must not add it.
- `check.review-dangling` IS ADVISORY BY DESIGN (`warning`), and its implementation deliberately contains no `.aw/records/reviews` path literal, routing discovery through the one record-path authority instead.
- CLOSED VOCABULARIES IN THIS MODULE ARE SINGLE-SOURCED TUPLES (`SEVERITIES:54` ascending so order IS the comparison, `DECISIONS:57`). `Subject-Type` should follow that shape.
- `plan-review` AND `plan-review-long` ARE HELD IN DELIBERATE PARITY, so record-format instructions must change in both bodies together.
- ONLY THE LAST ROUND COUNTS when reading findings (`ReviewDocument.current_findings`), and `aw reviews decisions` is the only command that reads a record back. Neither behavior changes here.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | **THE REPOSITORY'S OWN CHECKER REJECTS A SPEC REVIEW, which is the hard blocker.** The subject field is matched by a plan-specific regex and resolved against a plans-only `known` set, so a spec-subject review is reported dangling with advice to retire it. | `check_engine.py:2455` (`_REVIEW_PLAN_ID_RE`), `:2458` (`check_review_dangling`), `:2477-2480` (`known` built from `_iter_plan_ipds`), message at `:2501`, recovery at `:2506-2508` |
| F-2 | THE RECORD HAS NO ARTIFACT-TYPE FIELD AT ALL, so it cannot even record what it reviewed; `render_review` takes `plan_id` and emits four fields, none of them a type. | `review_findings.py:341-357`; parsed model `ReviewDocument(plan_id=...)` at `:184-193` |
| F-3 | THE FILENAME GRAMMAR ALREADY GENERALIZES and only its prose is plan-bound, so the neutral design was half-built already. This bounds the change: no naming code needs to move. | `build_review_name:228-244` delegating to `artifact_naming.build_clustered_name` with `REVIEW_FACET` (`:63`); docstrings at `:19-21`, `:235` |
| F-4 | THE BLAST RADIUS IS SMALL ENOUGH FOR ONE CHANGE, which is what makes replacement (rather than a compatibility shim) the cheaper option. RE-MEASURED AT REVIEW and the record count had already MOVED: 9 tracked Python files carry the literal, and the corpus is 36 records, not 35 (the spec says 34). The count grows with every review, including the ones this Set is generating while it waits, so E-04 must derive it rather than assert it. | re-measured at `024ab067`: `check_engine.py:9`, `tests/test_review_findings.py:4`, `reviews.py:2`, and 1 each in `specs.py`, `review_findings.py`, `tests/test_review_findings_gate.py`, `tests/test_review_findings_cascade.py`, `tests/test_review_decisions.py`, `tests/test_selector_resolver_matrix.py`; `rg -c "^- Plan-Id:" .aw/records/reviews/*.review.md` matches 36 files |
| F-5 | A DOCUMENTED CONTRACT WILL BECOME PARTLY-WRONG PROSE, and the plan overstated it. `reviews.py` explains that a review carries `Plan-Id` and that an id6 selector therefore does not match its front matter. VERIFIED AT REVIEW: the CONCLUSION survives the rename, because the resolver matches `^-\s*Id:` exactly and neither `Plan-Id` nor `Subject-Id` matches. So the field NAME in the prose is wrong after E-02 while the promise is still true, making this a careful prose fix rather than a contract change. | `reviews.py:182-189`, user-facing repeat at `:221`; `selectors.py:273` (`_FRONT_MATTER_ID_RE`), verified: the regex matches `- Id: aaa111` and rejects both `- Plan-Id:` and `- Subject-Id:` |
| F-6 | ABSENCE OF A REVIEW IS DELIBERATELY SILENT TODAY (`plan_gating_blocks` returns EMPTY when no review artifact exists, documented because "zero `.review.md` files exist against 428 plans"). This plan does NOT change that, and must not be read as making a missing review an error; `5slbpi` R-11 is where absence becomes meaningful, and only for a spec transition. | `review_findings.py:758`, rationale at `:768-769` |
| F-7 | TYPE-DIRECTED RESOLUTION INTRODUCES A NEW SILENT-FAILURE MODE, which is why E-03 fails closed: if `Subject-Type` were defaulted rather than required, a migration that dropped the field would still resolve those records against the plans tree and still pass, hiding the bug across the corpus until a spec review read as dangling. | design consequence of `check_review_dangling` becoming type-directed; whole corpus migrated at once by E-04 |
| F-8 | THE GATING PREDICATES ARE PLAN-NAMED IN THEIR SIGNATURES (`plan_gating_blocks(repo_root, plan_id6, ...)`, `plan_blocks_dependents`), so they will read as plan-only after this change even though they operate on a neutral record. Renaming is optional and must be behavior-free. THE COST OF RENAMING WAS MEASURED AT REVIEW and is the concrete argument for prose-only: five call sites, two of them in the two highest-contention modules in the repo. | `review_findings.py:759`, `:842`; callers at `oc_runipd.py:2846`, `agy_runipd.py:1833`, `ipd_set_plan.py:489`, `check_engine.py:2070`, `plan_readiness.py:509` |
| F-9 | **A PARSE ERROR ON AN UNMIGRATED RECORD DOES NOT MERELY MISREPORT, IT BLOCKS APPROVAL AND EXECUTION WITH NO OVERRIDE.** E-03's fail-closed decision is right, but the plan costed it as a reporting change. `plan_gating_blocks` case (b) treats ANY diagnostic as BLOCKING ("a file that exists but cannot be trusted is an error, not an absence"), and that predicate is consumed by both host runners, `/exec-set`'s Set compiler, `aw check`'s escalation evaluator, and `plan_readiness.approval_refusals`, where a typed gating finding is documented as having NO override "because the whole point is that no flag should be able to turn 'do not build this' into 'executable'". Measured: all 36 records parse with ZERO diagnostics today, so every instance of this failure is created by this change. E-03/E-04 must therefore be ONE atomic commit, or the parse error must land strictly after a verified migration. | `review_findings.py:807-811` (case (b) -> `kind="malformed"` block), contract at `:768-772`; consumers `oc_runipd.py:2846`, `agy_runipd.py:1833`, `ipd_set_plan.py:489`, `check_engine.py:2070`, `plan_readiness.py:509` with the no-override rationale at `plan_readiness.py:457-461`; measured 36/36 records parse with zero diagnostics |
| F-10 | **THE SUBJECT FIELD HAS A SECOND CONSUMER THE PLAN NEVER MENTIONED, AND IT FAILS OPEN ON AN `error`-SEVERITY GATE.** `_review_index` reads the same `_REVIEW_PLAN_ID_RE` and backs four call sites implementing `check.review-finding-unescalated` (severity `error`, wired into two `aw ipd lint` checkpoints) and `check.review-decision-unescalated`. Repointing only `check_review_dangling` would leave the index keyed on a field no record carries, so it returns EMPTY and every dependent rule takes its "nothing reviewed: every plan is the (a) absent case" early return. An unfixed HIGH or BLOCKER would then gate nothing, silently, which is precisely the hole the `revgate` Set was built to close. Added as E-05. | `check_engine.py:2673-2699` (`_review_index`), the shared regex at `:2455` consumed at `:2490` and `:2695`; call sites `:2753`, `:2858`, `:2955`, `:3124`; the fail-open early returns at `:2859` and `:3125`; `RuleSpec` severities at `:154-156` (`error`) and `:189-191` (`warning`) |
| F-11 | **TWO E-05 INSTRUCTIONS RESTED ON FALSE PREMISES.** (a) `Plan-Id` greps to ZERO in `.aw/system/workflows/`, so the workflow bodies do NOT instruct an agent to write the record's front matter and there is nothing to edit there; the cited `plan-review.md:178-185` says to write a record with "the same columns" and never names a field. The deliberate-parity concern therefore does not arise. (b) The REAL documented front-matter contract is `.aw/records/reviews/README.md:155`, which the plan mentioned only as a conditional "check and update if". It is not conditional: it displays the field. Scope-Paths corrected accordingly, dropping the two workflow bodies and adding the README. | `grep -rn "Plan-Id" .aw/system/workflows/` -> no matches; `.aw/records/reviews/README.md:155`, `:161`; `plan-review.md:178-185` quoted |
| F-12 | `tests/test_selector_resolver_matrix.py` WAS ABSENT FROM SCOPE-PATHS while carrying a `- Plan-Id:` fixture record, so the plan declared a fence that excluded a file it must edit. Now added. | `tests/test_selector_resolver_matrix.py:235` writes `"# Review: alpha\n\n- Plan-Id: aaa111\n..."` |
| F-13 | THE PLAN'S OWN ADVISORY-SEVERITY CHECK WAS SPECIFIED WRONG. V-03 asked to verify `check.review-dangling` is still advisory "by exit code, not by reading the rule's declaration". Measured, that inverts the truth: `drift_exit_code` exempts only `info`, so a `warning` DOES drive exit 1, and `check_engine.py` says so in a comment written expressly to stop this misreading. The declaration is the authority; the exit code proves nothing. | `artifact_core.py:405-415` (`return 1 if any(severity != "info")`); `check_engine.py:172-176` ("DO NOT READ `warning` AS 'cannot fail anything' (measured, not assumed)") |
| F-14 | THE SOURCE SPEC IS `to-review`, NOT APPROVED, while this plan is `Blocks-Release: next` and graduates R-01..R-05 from it. Spec `6m4kow` carries `- Status: to-review`. Not a defect in the plan (a plan may be authored from a spec under review, and `5slbpi` is in the same position), but it means the requirements this plan implements are not yet human-approved, so approving THIS plan implicitly ratifies those five requirements. Recorded so the approver knows that, rather than discovering it later. | `.aw/records/specs/20260904-6m4kow-01-6m4kow-cross-type-review.spec.md:4` (`- Status: to-review`), `:7` (`- Blocks-Release: next`) |

## Proposed changes (ordered, validatable)

1. Failing-first test proving a spec-subject review is rejected at HEAD (E-01).
2. Writer and parser move to the required `Subject-Id`/`Subject-Type` pair with a closed, single-sourced type vocabulary (E-02).
3. The dangling check becomes type-directed, failing closed on an absent or unknown type, staying advisory, and NOT landing its parse error on an unmigrated corpus (E-03).
4. The whole corpus migrated by a shown script, count derived not asserted, every record still parsing clean, with no dual-field reader left behind (E-04).
5. `_review_index` repointed and the `error`-severity escalation gate proven still to fire (E-05).
6. Every remaining consumer, docstring, contract note, and the reviews README updated (E-06).

## Deferred / out of scope (with reason)

- THE SPEC-REVIEW WORKFLOW AND THE ATTESTED `to-review -> reviewed` TRANSITION: `5slbpi` (spec `6m4kow` R-06 through R-13), which DEPENDS on this plan because it cannot file a conforming record until the record can describe a spec.
- MAKING A MISSING REVIEW MEANINGFUL FOR PLANS. Absence is deliberately silent (F-6) and 428 plans have no review record; changing that is a repository-wide policy change with no spec behind it. `5slbpi` requires a record only for the SPEC transition, going forward only.
- PER-TYPE SUBDIRECTORIES UNDER `.aw/records/reviews/`: open backlog `sv0sf3`, decided 65/35 toward the flat layout and orthogonal to the subject field.
- ADDING `reviews` TO THE ARTIFACT-TYPE ENUM. Deliberately absent with a documented rationale; adding it to the iterated `TYPE_FACET` map would make `aw set` accept a review file as status-settable.
- ANY CHANGE TO FINDINGS COLUMNS, SEVERITY OR VERDICT VOCABULARY, ROUND STRUCTURE, OR GATING THRESHOLDS. This plan changes the record's subject, not its content.
- WIDENING `Subject-Type` BEYOND `ipd|spec`. Backlog, research, releases and walkthroughs have no review action in spec `25kzda` Section 3 (3.6 gray-skips three of them; 3.4 gives backlog `graduate`), so a value for them would be unreachable surface.

## Scope check

- Over-scope REMOVED AT REVIEW: `.aw/system/workflows/plan-review*` was declared on the false premise that those bodies specify the record's front matter. They do not (`Plan-Id` greps to zero there, F-11), so both paths are dropped from Scope-Paths and the deliberate-parity concern does not arise.
- Under-scope CORRECTED AT REVIEW, twice: `tests/test_selector_resolver_matrix.py` carries a `Plan-Id` fixture and was missing from the fence (F-12), and `.aw/records/reviews/README.md` is the real front-matter contract rather than a conditional check (F-11). Both added.
- IN-SCOPE ADDITION (E-05, F-10): repointing `_review_index`. Not a widening but a correction of an under-scope: it reads the very field this plan renames, and leaving it would fail an `error`-severity gate OPEN. Omitting it would have made the plan a silent regression rather than a neutral rename.
- Under-scope, DELIBERATE: a review record can DESCRIBE a spec after this plan, and nothing yet PRODUCES one; `5slbpi` does. This plan removes a blocker and delivers no user-visible capability on its own, which is stated rather than dressed up.
- Under-scope: the plan-named gating predicates may keep their names (F-8), with only their prose corrected, and the measured five call sites (two in the highest-contention modules) are now the stated reason.
- NOT SCOPE, BUT THE APPROVER SHOULD KNOW: the source spec `6m4kow` is still `to-review` (F-14), so approving this plan implicitly ratifies its R-01..R-05.

## Required tests / validation

- E-01's blocker test, demonstrated FAILING at pre-change HEAD (the spec-subject review reported `check.review-dangling`), then clean after E-03.
- A review whose subject genuinely does NOT exist still reported dangling, for BOTH types. This is the regression that a type-directed resolver could silently lose, and it is what proves the check still works rather than merely stopping complaining.
- An absent or unknown `Subject-Type` producing a LOUD parse error, not a default (F-7).
- `check.review-dangling` still ADVISORY, verified by its registered `RuleSpec` severity and the absence of a lifecycle gate. NOT by exit code: a `warning` DOES drive exit 1 (F-13), so an exit-code check would either mislead or fail for the wrong reason.
- THE ESCALATION GATE STILL FIRES after migration (F-10): construct an unescalated gating finding and show `check.review-finding-unescalated` still reported. A green `aw check` is NOT evidence, because the regression is SILENCE from an empty index.
- EVERY MIGRATED RECORD PARSING WITH ZERO DIAGNOSTICS (F-9), since a diagnostic arms the no-override blocking path in `plan_gating_blocks`. Baseline measured at review: 36/36 clean.
- MIGRATION INVARIANTS, not a hardcoded count: zero `Plan-Id` anywhere in the tree, EVERY discovered record carrying both new fields, every `Subject-Id` resolving. Derive the corpus size from `iter_review_files` at execution (36 at review, 35 in the plan as authored, 34 in the spec, and growing). Paste the migration script.
- A record whose front-matter id6 and filename id6 DISAGREE reported rather than normalized, if any exists.
- `aw reviews decisions` still working against migrated records, since it is the only command that reads a record back.
- `aw check all` NO-WORSENING against your own fresh baseline; do NOT claim it passes (it has pre-existing findings, including backlog naming drift measured at authoring).
- The four review test modules plus `tests/test_selector_resolver_matrix.py` green. Baseline measured at review, so a regression is attributable: the four review modules were `161 passed` at `024ab067`.
- Full suite BARE (`python3 -m pytest`), compared against your own pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (backlog `dh0uno`).

## Spec / documentation sync

- This plan implements spec `6m4kow` R-01 through R-05. NOTE THE SPEC IS STILL `to-review` (F-14), so these requirements are not yet human-approved; if execution proves one wrong, amend the spec with `aw specs note` and say so, and do not diverge silently.
- `.aw/records/reviews/README.md` MUST be updated: it is the documented front-matter contract and displays the field at `:155`, with the dangling rule described at `:161`. This is not conditional.
- `reviews.py`'s contract prose (F-5) corrected CAREFULLY: the field name in it becomes wrong while its CONCLUSION (an id6 selector does not match a review's front matter; matching is by filename) stays true and verified. Do not "fix" it into claiming front-matter matching now works.
- `specs.py:558-563`'s comment re-grounded (E-06): its stated reason for an inert verdict half becomes stale, while the underlying fact (no spec review is produced yet) remains true until `5slbpi`.
- The `plan-review` and `plan-review-long` bodies need NO edit: they do not specify the record's front matter (F-11). Stated so nobody re-adds the retired instruction.

## Open questions

### OQ-01: Should the plan-named gating predicates be renamed, or only their prose corrected?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-04 by the maintainer, asked interactively: RENAME `plan_gating_blocks`/`plan_blocks_dependents` to subject-neutral names, AGAINST the prose-only default this question had recorded. THE RENAME IS THEREFORE HAPPENING, but NOT IN THIS PLAN: a structural re-review the same day extracted it into `wpomxa` (`revsweep-05`, `Item-Dependencies: executed:eyh1fu`), so this plan corrects the predicates' PROSE only and `wpomxa` performs the rename. WHY THE SPLIT, since the ruling was to rename and this plan is the one that made the names wrong: carrying the rename here grew this plan's Scope-Paths from 11 to 15 entries, four of them modules the subject-field change never touches, two of those the highest-contention files in the repo where three other pending plans are editing. This plan removes a RELEASE-BLOCKING blocker that `5slbpi` depends on, so letting a zero-behavior rename expose it to a merge conflict over function names was the wrong trade. The rename is also provably independent: `plan_gating_blocks` takes an id6 and never reads the subject field, so neither change needs the other. ORIGINAL ANALYSIS follows, retained because its measured contention evidence is what justified the extraction: NOT BLOCKING; either answer leaves behavior identical and E-06 permits both provided the choice is stated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the spec-subject review record used, and paste `aw check all` reporting `check.review-dangling` against it at pre-change HEAD, including the message and recovery text. This is the plan's premise; without the observed rejection the rest reads as a rename.
  - Observed evidence: MEASURED AT PRE-CHANGE HEAD `97d5ddf4da0fb47e9a8d8d286f313c7762e0054a` in the primary lane checkout. The record written by the then-current `render_review` against a REAL spec (`- Id: spc111`, present in `.aw/records/specs/`), with an unrelated real plan (`- Id: pln111`) in the plans tree so the tree was not empty:

    ```text
    # Plan review findings: spc111

    - Plan-Id: spc111
    - Reviewed-At: 2026-09-05
    - Reviewer: opencode/test
    - Verdict: APPROVE

    ## Round 1

    ### Findings

    | ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
    | --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
    | F-1 | low | IN-SCOPE | x | a.py:1 | y | Overall:Low | fixed | done |
    ```

    `aw check all` on that scratch repo AT PRE-CHANGE HEAD (human renderer, so the message and recovery are visible):

    ```text
      Issue: Plan-Id 'spc111' does not resolve to any plan
      - .aw/records/reviews
        1. 20260905-spc111-01-spc111-demo.review.md
    ```

    And the same finding through the rule directly, with every enriched field:

    ```text
    LOCATION: .../.aw/records/reviews/20260905-spc111-01-spc111-demo.review.md
    RULE: check.review-dangling
    DETAIL: Plan-Id 'spc111' does not resolve to any plan
    OBSERVED: Plan-Id: spc111
    REQUIRED: a Plan-Id matching an existing plan's `- Id:`
    RECOVERY: correct the Plan-Id to the reviewed plan's id6, or retire the review alongside the plan it reviewed
    SEVERITY: warning
    ```

    THE REJECTION IS REAL AND ITS RECOVERY TEXT TELLS THE AUTHOR TO RETIRE THE REVIEW, exactly as F-1 claimed. The FAILING-FIRST test asserting the property this plan must deliver (a real-spec subject is not dangling) failed at that HEAD:

    ```text
    E  AssertionError: Lists differ: [Drift(location='.../20260905-spc111-01-spc111-demo.review.md',
       rule='check.review-dangling', detail="Plan-Id 'spc111' does not resolve to any plan", ...)] != []
    FAILED /tmp/.../test_e01_blocker.py::SpecSubjectReviewIsRejectedAtHead::test_spec_subject_review_is_not_dangling
    1 failed in 0.11s
    ```

    That scratch assertion was then MOVED INTO THE TRACKED SUITE rather than left outside it, as `ReviewDanglingCheckTests.test_spec_subject_review_with_a_real_spec_is_clean` (`tests/test_review_findings.py`), where it now passes; V-03 pastes it green. The temporary file is deliberately not committed: an unmigrated fixture calling `render_review(plan_id=...)` would fail permanently after E-02.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a rendered record showing the required `- Subject-Id:`/`- Subject-Type:` pair and the corrected H1. Paste the closed type vocabulary declared ONCE, in the same shape as `SEVERITIES`/`DECISIONS`. Paste a diff or grep proving the findings columns, `SEVERITIES`, `DECISIONS`, round structure, and `plan_readiness.VERDICTS` are UNCHANGED, since this item's fence is that it touches only the subject.
  - Observed evidence: A record rendered by the NEW writer, with a `spec` subject to show the H1 no longer hardcodes "Plan":

    ```text
    # Review findings: spec spc111

    - Subject-Id: spc111
    - Subject-Type: spec
    - Reviewed-At: 2026-09-05
    - Reviewer: oc
    - Verdict: APPROVE

    ## Round 1

    ### Findings

    | ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
    | --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
    | F-1 | high | IN-SCOPE | rubric 2.1 | a.py:1 | x | Overall:Low | open | y |
    ```

    Both fields are REQUIRED: `parse_review_text` lists them in the required-metadata loop, so an absent one is `REV-M101` (see V-03). THE CLOSED VOCABULARY IS DECLARED ONCE, in exactly the shape its two siblings use:

    ```text
    agent_workflows/review_findings.py
    61:SEVERITIES: Tuple[str, ...] = ("low", "medium", "high", "blocker")
    64:DECISIONS: Tuple[str, ...] = ("fixed", "deferred", "open", "replan")
    72:SUBJECT_TYPES: Tuple[str, ...] = ("ipd", "spec")
    ```

    `test_subject_type_vocabulary_is_closed_and_fully_resolvable` asserts the tuple's exact contents AND that the checker's per-type resolution map has an entry for every member, so a type cannot be added to the vocabulary without a tree to resolve it against.

    NOTHING ABOUT WHAT THE RECORD SAYS CHANGED. `git diff agent_workflows/review_findings.py` filtered for the machinery this item must not touch returns EMPTY (no line beginning `-`/`+` matches `FINDING_COLUMNS`, `DECISION_COLUMNS`, `SEVERITIES:`, `DECISIONS:`, or `_SEVERITY_RANK`), and the round structure (`_ROUND_RE`, `Round`, `current_round`, `current_findings`) is untouched. `plan_readiness.py` is NOT MODIFIED AT ALL: `git diff -- agent_workflows/plan_readiness.py` is empty, so `VERDICTS` is unchanged by construction. `git diff --stat` confirms the only modules touched are `check_engine.py`, `review_findings.py`, `reviews.py`, `specs.py`.

    THE ATTRIBUTE-SPELLED READERS R2-2 FLAGGED WERE UPDATED, which a `Plan-Id` STRING grep would have missed: `plan_gating_blocks` now compares `doc.subject_id` (formerly `doc.plan_id`), and the field is populated from `meta["subject-id"]` (formerly `meta["plan-id"]`). Verified no `.plan_id` reader of a `ReviewDocument` or `DecisionRow` survives anywhere: the only remaining `.plan_id` attributes in the package belong to unrelated types (`plans_index`, `work_cmd`, `ipd_lifecycle` journals, `migration_complex`, `verify_roles`), none of which parse review records.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the spec-subject review from V-01 now CLEAN. Then paste the regression that matters more: a review whose subject genuinely does not exist STILL reported dangling, for BOTH `ipd` and `spec` types, because a type-directed resolver that stopped complaining entirely would also look clean. Paste an absent `Subject-Type` and an unknown one each producing a LOUD parse error rather than defaulting to `ipd` (F-7).
    PROVE THE RULE IS STILL ADVISORY THE RIGHT WAY: paste its registered `RuleSpec` severity and confirm no lifecycle gate consumes it. Do NOT use the exit code, which is exit 1 for a `warning` too (F-13); an exit-code argument here is unsound and must not be offered as evidence.
    STATE WHETHER E-03 AND E-04 LANDED ATOMICALLY (F-9), and if the parse error landed after the migration, paste the ordering. Paste evidence no `.aw/records/reviews` path literal was added, and show how the SPEC-tree id6 set is obtained without one.
  - Observed evidence: All six type-resolution tests green (`tests/test_review_findings.py`):

    ```text
    ReviewDanglingCheckTests::test_spec_subject_review_with_a_real_spec_is_clean PASSED
    ReviewDanglingCheckTests::test_resolution_is_type_directed_not_a_union PASSED
    ReviewDanglingCheckTests::test_rule_stays_advisory_after_becoming_type_directed PASSED
    ReviewDanglingCheckTests::test_unknown_subject_type_is_a_parse_error PASSED
    ReviewDanglingCheckTests::test_absent_subject_type_is_a_parse_error_and_is_not_defaulted PASSED
    ReviewDanglingCheckTests::test_missing_spec_subject_is_still_reported PASSED
    6 passed, 56 deselected in 0.20s
    ```

    (1) THE V-01 CASE IS NOW CLEAN: `test_spec_subject_review_with_a_real_spec_is_clean` builds the same fixture V-01 used (real spec `spc111`, real plan `aaa111`) and asserts `check_review_dangling` returns `[]`.

    (2) THE REGRESSION THAT MATTERS MORE IS INTACT, in two forms, because a resolver that merely stopped complaining would pass (1) as well. `test_missing_spec_subject_is_still_reported`: a `spec`-typed subject `zzz999` that does not exist IS still reported, detail `Subject-Id 'zzz999' does not resolve to any spec`. `test_dangling_review_fires` (pre-existing, still green) covers the same for `ipd`. AND `test_resolution_is_type_directed_not_a_union` proves resolution is genuinely TYPE-DIRECTED rather than a union over trees: the real PLAN id `aaa111` declared as `Subject-Type: spec` IS reported, so a record naming the wrong tree cannot pass and `Subject-Type` is not decorative.

    (3) FAIL-CLOSED ON THE TYPE, NEVER DEFAULTED. Absent type -> `REV-M101` and `doc.subject_type == ""`; unknown type (`backlog`) -> `REV-M102` with the value PRESERVED verbatim, not coerced. In both cases `check_review_dangling` returns `[]` rather than falling back to the plans tree, which is asserted explicitly: the parser owns the complaint and this advisory rule does not double-report it, and critically the record is NOT silently resolved as an `ipd`.

    ADVISORINESS PROVEN THE RIGHT WAY, not by exit code:

    ```text
    RuleSpec(severity='warning', assurance='repository', determinism='deterministic', invariant='I-07')
    check.review-dangling appears in ipd_lint.py: False
    check.review-finding-unescalated appears in ipd_lint.py: True
    ```

    The registered severity is unchanged at `warning`, and NO LIFECYCLE GATE consumes the rule: it is absent from `ipd_lint.py` entirely, while its `error` sibling is present (the contrast is what makes the absence meaningful). NO EXIT-CODE ARGUMENT IS OFFERED: per F-13, `artifact_core.drift_exit_code` exempts only `info`, so a `warning` drives exit 1 too and an exit-code check would prove nothing. Consistent with that, `aw check all` on this repo still exits 1 on its pre-existing findings both before and after this change.

    E-03 AND E-04 LANDED ATOMICALLY, in one commit, as F-9 requires: the parse error and the corpus migration are in the same commit as the rest of this plan's change, so at no point does a commit exist in which a record lacking `Subject-Type` would be parsed by a build that demands it. That matters because a parse diagnostic is a `Diagnostic`, and `plan_gating_blocks` case (b) treats ANY diagnostic as BLOCKING with no override, so a half-migrated commit would have blocked plan approvals.

    NO `.aw/records/reviews` PATH LITERAL WAS ADDED. The pre-existing AST guard still passes:

    ```text
    tests/test_review_findings.py::ReviewDanglingCheckTests::test_no_hardcoded_reviews_path_in_check_engine PASSED
    ```

    THE SPEC-TREE ID6 SET IS OBTAINED THROUGH THE EXISTING TYPED-ITERATION SEAM, not a new literal: `_review_subject_id_sets` builds `{"ipd": ...}` from `_iter_plan_ipds` (the iterator the old plans-only code used) and `{"spec": ...}` from `_iter_spec_records`, the sibling iterator that already sits beside it and that `check_from_spec_dangling` already consumes for exactly this purpose. No second "which spec ids exist" mechanism and no second specs path string were introduced.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the migration SCRIPT (not a description of it). Paste the DERIVED corpus count from `iter_review_files` and these invariants: `Plan-Id` occurrences in the whole tree = 0, every discovered record carrying both new fields, every `Subject-Id` resolving. Do not assert equality against 34/35/36; the corpus grows (F-4).
    PASTE THE ZERO-DIAGNOSTICS PROOF for every migrated record (F-9), against the measured 36/36-clean baseline, since a single diagnostic arms a no-override block on a plan's approval.
    Paste evidence NO dual-field reader was left, since a parser accepting both would let a half-migrated corpus pass. Paste `aw reviews decisions` working against migrated records. Report any front-matter/filename id6 mismatch found rather than normalized.
  - Observed evidence: THE MIGRATION SCRIPT, in full (run from the lane root; it takes the repo root and writes only with `--apply`):

    ```python
    PLAN_ID_RE = re.compile(r"(?m)^-[ \t]*Plan-Id:[ \t]*([0-9a-z]{6})[ \t]*$")
    H1_RE = re.compile(r"(?m)\A#[ \t]*Plan review findings:[ \t]*([0-9a-z]{6})[ \t]*$")

    from agent_workflows import review_findings as rf
    paths = sorted(rf.iter_review_files(repo_root), key=lambda p: str(p))
    print("DERIVED corpus size: {0} record(s)".format(len(paths)))

    planned, mismatches, skipped = [], [], []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        m = PLAN_ID_RE.search(text)
        if m is None:
            skipped.append((path, "no `- Plan-Id:` field")); continue
        front_id = m.group(1)
        name_parts = rf.parse_review_name(path.name)
        name_id = name_parts["id6"] if name_parts else None
        if name_id is not None and name_id != front_id:
            mismatches.append((path, front_id, name_id)); continue      # REPORT, never normalize
        new_text = PLAN_ID_RE.sub("- Subject-Id: {0}\n- Subject-Type: ipd".format(front_id), text, count=1)
        new_text = H1_RE.sub("# Review findings: ipd {0}".format(front_id), new_text, count=1)
        planned.append((path, new_text))

    if mismatches:
        print("REFUSING TO WRITE: resolve the mismatch(es) above first."); return 1
    for path, new_text in planned:
        path.write_text(new_text, encoding="utf-8")
    ```

    IT IS A PURE FIELD RENAME PLUS AN INSERTED TYPE. It never re-derives an id6 from a filename: `front_id` always comes from the FRONT MATTER, and the filename id6 is used ONLY to detect disagreement. On disagreement it REFUSES TO WRITE ANYTHING (`return 1` before the write loop), so a genuine mismatch is reported rather than silently repaired. The H1 is corrected too, because the new `render_review` no longer emits "Plan review findings" and leaving the old heading would make a re-rendered record differ from a migrated one for no reason.

    THE COUNT IS DERIVED, NOT ASSERTED, and it had MOVED AGAIN, which is exactly why F-4 demanded this:

    ```text
    DERIVED corpus size: 40 record(s)
    to migrate: 40; already migrated/skipped: 0
    WROTE 40 record(s)
    ```

    40 at execution, against 36 at review, 35 as authored, and 34 in the spec. NO MISMATCH AND NO SKIP was found: all 40 records had a `- Plan-Id:` field whose id6 agreed with the filename, so nothing was reported and nothing was normalized.

    THE INVARIANTS, which hold at any corpus size:

    ```text
    DERIVED corpus size: 40
    records with ANY diagnostic: 0 []
    records missing either subject field: 0 []
    every subject_type in vocab: True
    check.review-dangling findings over the real corpus: 0 []
    ```

    So: EVERY discovered record carries BOTH new fields; EVERY `Subject-Id` resolves (the type-directed rule reports zero findings over the real 40-record tree); and ZERO `- Plan-Id:` FIELDS remain anywhere in the tree (`rg "^- Plan-Id:"` over the whole repo matches only `.aw/records/reviews/README.md`, and that hit is the prose sentence documenting the field's REMOVAL, not a record field; V-06 pastes the full grep).

    ZERO-DIAGNOSTICS PROOF (F-9's load-bearing check): all 40/40 migrated records parse with ZERO diagnostics, against the measured 36/36-clean baseline taken at pre-change HEAD. This is the check that proves the migration did not arm `plan_gating_blocks` case (b), where any diagnostic BLOCKS a plan's approval and its dependents' execution with no override.

    NO DUAL-FIELD READER EXISTS. `review_findings` reads `meta["subject-id"]`/`meta["subject-type"]` and nothing else; `rg "plan-id"` over the parser/writer returns ZERO hits (the surviving `plan_id6` names are the two gating predicates' PARAMETERS, which `wpomxa` owns and this plan deliberately left alone). `check_engine` matches `_REVIEW_SUBJECT_ID_RE` only; the old `_REVIEW_PLAN_ID_RE` is DELETED, not kept as an alternative. `test_the_fail_open_empty_index_path_is_not_entered` asserts the consequence positively: a record carrying the retired field is NOT indexed at all.

    `aw reviews decisions` WORKS AGAINST THE MIGRATED CORPUS (it is the only command that reads a record back):

    ```text
    129 recorded decision(s) across 39 reviewed artifact(s); 3 marked irreversible
    ```

    and its JSON payload reports `total: 129, subjects: 39, diagnostics: 0`, with each row now carrying `subject_id` plus `subject_type` (`'subject_id': '2r306y', 'subject_type': 'ipd', ...`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: THE LOAD-BEARING EVIDENCE FOR THIS PLAN'S SAFETY. Paste `_review_index` reading the neutral field. Then paste a POSITIVE test that `check.review-finding-unescalated` STILL FIRES after migration: construct a plan with an unfixed gating finding and no escalating `Blocking: yes` question, and show the finding reported. State explicitly that a clean `aw check` does NOT satisfy this item, because an empty index fails OPEN and looks identical to compliance (F-10). Paste evidence the four dependent call sites still evaluate rather than taking the "nothing reviewed" early return. State whether resolution stayed one shared regex, and if a `Subject-Type` filter was applied to the index, why.
  - Observed evidence: `_review_index` READS THE NEUTRAL FIELD, via the shared regex:

    ```python
    m = _REVIEW_SUBJECT_ID_RE.search(text)
    if m is None:
        continue
    index.setdefault(m.group(1), []).append(path)
    ```

    THE POSITIVE TESTS, all four green (`tests/test_review_findings_gate.py::SubjectFieldIndexTests`):

    ```text
    SubjectFieldIndexTests::test_escalation_gate_still_fires_after_the_subject_rename PASSED
    SubjectFieldIndexTests::test_index_is_keyed_on_the_neutral_subject_id PASSED
    SubjectFieldIndexTests::test_the_fail_open_empty_index_path_is_not_entered PASSED
    SubjectFieldIndexTests::test_no_review_record_in_the_tree_carries_the_retired_field PASSED
    4 passed, 39 deselected in 0.23s
    ```

    `test_escalation_gate_still_fires_after_the_subject_rename` is the load-bearing one: it builds a plan carrying an unfixed `high`/`open` finding with NO escalating `Blocking: yes` question, and asserts `check_review_finding_unescalated` reports exactly `check.review-finding-unescalated`, at the PLAN's path, naming `F-1`. `test_index_is_keyed_on_the_neutral_subject_id` asserts the index itself is `{"aaa111": [review]}` rather than empty.

    A CLEAN `aw check` DOES NOT SATISFY THIS ITEM, and the tests are written on that basis. The regression this item guards against is SILENCE: had the field been renamed without repointing the index, the index would return EMPTY, every dependent rule would take its "nothing reviewed: every plan is the (a) absent case" early return, and an unfixed HIGH/BLOCKER would gate NOTHING on an `error`-severity rule wired into two `aw ipd lint` checkpoints. That outcome is INDISTINGUISHABLE from compliance in any output, which is why the evidence here is a positive firing rather than a green run. `test_the_fail_open_empty_index_path_is_not_entered` makes the contrast explicit and executable: it writes a record carrying the RETIRED field, shows the index comes back `{}`, and shows the sweep then reports NOTHING - the fail-open state - proving the passing case above is not that state. `test_no_review_record_in_the_tree_carries_the_retired_field` then rules the hazard out at corpus level over the REAL repository (all 40 records carry both fields, none carries `- Plan-Id:`).

    THE FOUR DEPENDENT CALL SITES STILL EVALUATE rather than early-returning. They are `check_engine.py:2822` and `:3024` (the two evaluators, which accept an injected index) and `:2927` and `:3193` (the two sweeps, which build it once). Both `error`-severity and `warning`-severity families were exercised: the finding rule fires positively above, and the decision rule's tests (`check.review-decision-unescalated`, including its irreversible/unjudged cases) pass against migrated records. The two review-gate modules together: `70 passed in 1.56s`.

    RESOLUTION STAYED ONE SHARED REGEX, deliberately: `_REVIEW_SUBJECT_ID_RE` serves BOTH `check_review_dangling` and `_review_index`, so the subject field has exactly one matcher and the two consumers cannot disagree about its spelling. The retired `_REVIEW_PLAN_ID_RE` was deleted outright.

    NO `Subject-Type` FILTER WAS APPLIED TO THE INDEX, and the reason is recorded in the code: an id6 is unique across trees (`check.id6-collision` polices that), and every caller looks the index up BY A PLAN's OWN id6, which no spec shares, so a spec-subject record cannot be attributed to a plan. Adding a filter would create a SECOND place that decides what a subject type means for no additional safety. Note the type-directed decision lives where it is load-bearing (the dangling check, which must pick a TREE) and not where it is not (the index, which is keyed by a globally unique id).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste a tree-wide grep for `Plan-Id` returning ZERO hits in code, tests, and records. Paste the corrected `reviews.py` contract prose (F-5), and CONFIRM it still states that matching is by filename, since that promise remains true and must not be inverted. Paste the corrected `review_findings` docstrings, the re-grounded `specs.py` comment, and the updated `.aw/records/reviews/README.md` front-matter block. CONFIRM the gating predicates `plan_gating_blocks`/`plan_blocks_dependents` were NOT renamed here: their PROSE is corrected and their NAMES are left to `wpomxa` (`revsweep-05`), so a rename appearing in this plan's diff is a scope violation, not a bonus. DO paste evidence that `doc.plan_id`'s in-file readers were updated (`review_findings.py:805` and the `meta["plan-id"]` population at `:640`), since those are the ATTRIBUTE spelling a `Plan-Id` string grep misses. CONFIRM the two plan-review bodies were NOT edited, since they never carried the field (F-11). Then the review test modules against the `161 passed` baseline, `aw check all` no-worsening against your own baseline, and the bare full suite with counts compared against your own pre-change measurement.
  - Observed evidence: TREE-WIDE `Plan-Id` GREP. Zero FIELD occurrences remain: `rg --hidden "^- Plan-Id:"` over the whole repo matches nothing in any record. The only surviving mentions are DELIBERATE PROSE ABOUT THE FIELD'S REMOVAL plus two test lines that construct the retired spelling in order to prove it is rejected:

    ```text
    agent_workflows/reviews.py:270      # ...the same defect in an output payload that `- Plan-Id:` was in the record
    agent_workflows/specs.py:561        # original reason - that review artifacts were KEYED BY `Plan-Id`...
    agent_workflows/review_findings.py:29  The former plan-bound ``- Plan-Id:`` is REPLACED, not carried alongside
    .aw/records/reviews/README.md:188   There is deliberately no `- Plan-Id:` and no compatibility reader for it
    tests/test_review_findings_gate.py:296  .replace("- Subject-Id: aaa111", "- Plan-Id: aaa111")   # fail-open contrast fixture
    tests/test_review_findings_gate.py:322  if "\n- Plan-Id:" in text or not doc.subject_id ...      # corpus invariant guard
    ```

    (Historical narrative in `.aw/records/plans/**`, `.aw/records/specs/**`, and this plan's own review record retains the name, correctly: those are immutable accounts of what the code USED to do.)

    `reviews.py` CONTRACT PROSE CORRECTED AND ITS PROMISE KEPT TRUE. It now says a review names its subject with `- Subject-Id:`, and it STILL STATES that an id6 selector does NOT match a review's front matter and that matching is BY FILENAME. That conclusion was re-verified rather than assumed: `selectors._FRONT_MATTER_ID_RE` anchors on `^-\s*Id:`, which matches neither `Plan-Id` nor `Subject-Id`, so the promise survives the rename and was NOT inverted into claiming front-matter matching now works. The user-facing message was corrected in step: "reviews are matched by FILENAME, which embeds the reviewed artifact's id6; the front matter carries `Subject-Id:` rather than `Id:`".

    `review_findings` DOCSTRINGS CORRECTED: the module header now describes the layout as one file per reviewed ARTIFACT and documents the subject pair, and `build_review_name`'s docstring says `subject_id6` is the REVIEWED ARTIFACT's id6 which "may name a plan or a spec", with the note that the TYPE lives in the front matter and not the filename. Confirmed the naming code itself did not need to move (R-05 was a prose fix): `build_review_name` still delegates to `artifact_naming.build_clustered_name` with the `review` facet, unchanged.

    `specs.py` COMMENT RE-GROUNDED, not deleted: it now records that the ORIGINAL reason (review artifacts were keyed by `Plan-Id`, so no spec verdict could exist) no longer holds after this plan, while the verdict half stays inert for the DIFFERENT and still-true reason that nothing PRODUCES a spec review yet (`5slbpi` owns the producer). A later reader is therefore not misled into thinking the half is live.

    `.aw/records/reviews/README.md` UPDATED, including the front-matter block that was the actual documented contract:

    ```text
    - Subject-Id: <id6 of the reviewed artifact>
    - Subject-Type: <ipd|spec>
    - Reviewed-At: <YYYY-MM-DD>
    - Reviewer: <tool/model that performed the review>
    - Verdict: <the review verdict>
    ```

    plus the closed-vocabulary rule, the fail-closed parse-error behavior, the type-directed dangling rule, the honest note that `warning` still drives exit 1 while adding no lifecycle gate, and an explicit statement that no compatibility reader exists. The naming section now says `<id6>` is the reviewed ARTIFACT's id6 and that the grammar is neutral. The intro states plainly what this delivers and what it does not: the record is CAPABLE of describing a spec review, and only `/plan-review` produces records today.

    THE GATING PREDICATES WERE NOT RENAMED HERE. `plan_gating_blocks` and `plan_blocks_dependents` keep their names and their `plan_id6` parameters; `git diff` of `review_findings.py` shows NO added or removed `def plan_gating_blocks`/`def plan_blocks_dependents` line (the only signature lines in the diff are `build_review_name`'s and `render_review`'s keywords, which E-02 owns). Their PROSE is corrected: each docstring now states the predicate is artifact-neutral despite its plan-only name, and names `wpomxa` (`revsweep-05`) as the owner of the rename. Also corrected: the section banner ("does this artifact's review block its dependents?") and `GatingBlock`'s docstring. `plan_readiness.py`, `oc_runipd.py`, `agy_runipd.py`, and `ipd_set_plan.py` are UNTOUCHED (absent from `git status`), so nothing in this diff can collide with `wpomxa`.

    THE `doc.plan_id` READERS WERE UPDATED - the ATTRIBUTE spelling a `Plan-Id` string grep misses. `plan_gating_blocks` now reads `doc.subject_id`, and the parser populates it from `meta["subject-id"]`. `rg "plan-id"` over `review_findings.py` returns ZERO hits, so no reader of the retired metadata key survives. This is the R2-2 hazard: leaving it would have made the gating predicate match a field nothing populates, returning EMPTY and opening the gate silently.

    THE TWO PLAN-REVIEW BODIES WERE NOT EDITED (F-11): `git diff --stat -- .aw/system/workflows/` is EMPTY, and `Plan-Id` greps to ZERO in `.aw/system/workflows/`, confirming they never carried the field and there was nothing there to change. No front-matter instruction was invented to satisfy the stale instruction.

    ONE IN-SCOPE ADDITION NOT LISTED IN E-06, stated rather than slipped in: `reviews.py`'s output payload key `plans` (and the phrase "reviewed plan(s)") became `subjects` / "reviewed artifact(s)", because after this change a subject may be a spec and a key named `plans` would ASSERT a type the data no longer guarantees - the same defect in a payload that `- Plan-Id:` was in the record. Measured before changing it: the key has no documented contract and no consumer anywhere outside its own module (zero hits in `tests/`, `docs/`, and the conformance goldens), so nothing reads it. It is inside the declared Scope-Paths (`agent_workflows/reviews.py`).

    TEST AND CHECK EVIDENCE. The five in-scope test modules, against the `161 passed` baseline recorded at review (the four review modules) - now 192 passed for all five, the increase being the 11 tests this plan adds plus the pre-existing 20 in the selector matrix:

    ```text
    tests/test_review_findings_gate.py .....................................  [ 22%]
    tests/test_review_decisions.py ...........................                [ 36%]
    tests/test_selector_resolver_matrix.py ....................               [ 46%]
    tests/test_review_findings_cascade.py ..................................  [ 67%]
    tests/test_review_findings.py ..........................................  [100%]
    192 passed in 2.25s
    ```

    `aw check all` NO-WORSENING against my own fresh pre-change baseline (NOT a claim that it passes; it has pre-existing findings, exactly as the plan warned):

    ```text
    BEFORE (HEAD 97d5ddf4): findings: 25 exit: 1     AFTER: findings: 25 exit: 1
      12 check.lifecycle-transition-invalid      12 check.lifecycle-transition-invalid
       7 check.name-nonconformant                 7 check.name-nonconformant
       3 check.setid-collision                    3 check.setid-collision
       1 check.id6-collision                      1 check.id6-collision
       1 check.from-backlog-dangling              1 check.from-backlog-dangling
       1 check.from-backlog-gate-mismatch         1 check.from-backlog-gate-mismatch
    ```

    Identical count and identical rule mix. Notably ZERO `check.review-dangling` findings, over a 40-record corpus now resolved type-directed.

    FULL SUITE, BARE (`python3 -m pytest`, no `-n0`, no second `-q`, no `-p no:randomly`), measured in the PRIMARY lane checkout at the HEAD I started from and again after the change:

    ```text
    BEFORE: 31 failed, 4419 passed, 3 skipped, 4 xfailed in 31.03s
    AFTER:  31 failed, 4430 passed, 3 skipped, 4 xfailed in 32.19s
    ```

    +11 passing (the tests this plan adds) and the FAILURE SET IS BYTE-IDENTICAL: `diff` of the sorted `FAILED` lines before and after is EMPTY. All 31 are pre-existing and unrelated (`test_oc_runipd`, `test_run_viewer`, `test_ipd_lifecycle_cli`, `test_worker_role_refusal` - runner/lifecycle-harness failures present at the HEAD I inherited, none touching reviews).

    LEAK SANITIZER CLEAN: `check-local-leaks --agent` -> `"outcome":"clean","findings":0,"exit":0`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 6 E-leaves across 2 task groups, one concern: the review record's subject becomes artifact-neutral. Task group 1 changes the shape (prove the blocker, then writer/parser, then checker); task group 2 propagates it (records, then the second index consumer, then the remaining code and docs). E-02 and E-03 are separate because the writer change is mechanical while the checker change carries the real design decision (fail closed on an absent type rather than default), and folding them would let that decision pass unreviewed. E-04 and E-06 are separate because one migrates DATA and the other CODE, with different failure modes: a bad data migration produces false dangling findings and can block approvals, a missed code reference produces a crash. E-05 is its own leaf, added at review, because its failure mode is neither of those: it fails SILENTLY on an `error`-severity gate, so it needs its own positive test and cannot be validated by the same evidence as E-06.
- Right-sizing re-checked at review: each leaf is one deliverable with one test surface. E-06 is the widest (several files) but is a single mechanical concern, propagate the field rename through consumers and prose, with one V-item.
- Right-sizing re-checked AGAIN 2026-09-04 after the OQ-01 ruling, and this time it FAILED and was fixed: carrying the predicate rename made this plan span four extra modules for a concern (naming clarity, zero behavior) distinct from its own (the record's subject field), which is two of the IPD spec's three split triggers. The rename was extracted to `wpomxa` and Scope-Paths returned to 11 entries. The remaining 6 leaves are one concern again. E-03's two clauses (type-direct the resolution, fail closed on absent type) are inseparable, since type-directed resolution with a defaulted type is the silent bug F-7 describes.

Open questions: OQ-01 (rename the plan-named gating predicates, or correct prose only) is RESOLVED: the maintainer ruled RENAME on 2026-09-04, and the rename was then extracted into `wpomxa` (`revsweep-05`), so this plan corrects their prose and leaves their names to that plan. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution. It has NO plan dependencies (`- Item-Dependencies: none`) and is the PREREQUISITE for `5slbpi`, which cannot file a conforming spec review until the record can describe one. It is independent of `76gsmv` and `6ypimw` and may proceed in parallel with them, since it touches the record and they touch the driver.

Scope fence: touch ONLY `agent_workflows/review_findings.py`, `agent_workflows/check_engine.py`, `agent_workflows/reviews.py`, `agent_workflows/specs.py`, the `.aw/records/reviews` records, `.aw/records/reviews/README.md`, and the five test modules (the four review modules plus `tests/test_selector_resolver_matrix.py`). Do NOT change findings columns, `SEVERITIES`, `DECISIONS`, round structure, or `plan_readiness.VERDICTS`. Do NOT promote `check.review-dangling` from advisory to blocking. Do NOT add `reviews` to `ARTIFACT_TYPES` or `TYPE_FACET`. Do NOT make a MISSING review an error for plans (F-6). Do NOT leave a dual-field compatibility reader. Do NOT add a `.aw/records/reviews` path literal to `check_engine`. Do NOT create per-type review subdirectories. Do NOT edit the `plan-review` or `plan-review-long` bodies: they never carried the field, and the instruction to do so rested on a false premise (F-11). Do NOT re-derive any record's id6 from its filename during migration; rename the field and report a mismatch instead. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run. NOTE that renaming `plan_gating_blocks` (OQ-01) WOULD reach outside this fence, into both host runners and `ipd_set_plan.py`; that is the measured reason the default is prose-only.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. THREE pieces of evidence are load-bearing: (1) V-01's observed REJECTION at HEAD, because without it this change reads as a rename rather than a blocker removal; (2) V-03's proof that a genuinely missing subject is STILL reported, because a type-directed resolver that simply stopped complaining would look identical to a working one; and (3) V-05's proof that `check.review-finding-unescalated` STILL FIRES, because an empty review index fails OPEN on an `error`-severity gate and is indistinguishable from compliance. Do NOT offer an exit code as proof that `check.review-dangling` is advisory; a `warning` exits 1 too (F-13). Do NOT claim `aw check all` passes; the bar is no-worsening against your own fresh baseline. Do NOT report this plan as delivering spec review: it makes the record CAPABLE of describing one, and `5slbpi` produces it.

Execution contract: RE-READ `review_findings.py` and `check_engine.py` immediately before editing and locate every site BY SYMBOL, never by the line numbers in this plan. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. THE MIGRATED RECORDS ARE DATA you are rewriting mechanically, and THIS TREE IS ACTIVELY GROWING while the Set runs (a review record appeared between this plan's authoring and its review), so re-enumerate immediately before committing: verify `git diff --cached --name-only` lists exactly the records you migrated and nothing a co-worker touched, and re-verify after any hook interruption, since a failed hook invalidates the check. If a NEW review record appears mid-execution carrying the old field, migrate it too and say so, rather than leaving one unmigrated file that arms the F-9 blocking path. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
