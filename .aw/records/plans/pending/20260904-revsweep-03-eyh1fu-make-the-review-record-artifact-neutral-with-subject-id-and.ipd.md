# IPD: make the review record artifact-neutral with Subject-Id and Subject-Type

- Date: 2026-09-04
- Kind: child
- Concern: THE REVIEW RECORD CANNOT DESCRIBE A SPEC REVIEW, so the repository's own checker would reject one. `review_findings.render_review` writes `- Plan-Id: <id6>` as the only subject field (`:353`), and `check_engine.check_review_dangling` resolves that field against the PLANS TREE ALONE, building its `known` set from `_iter_plan_ipds` (`:2477-2480`). File a review against a spec and `aw check` reports `check.review-dangling`, "Plan-Id ... does not resolve to any plan", advising you to "correct the Plan-Id ... or retire the review". That is a hard blocker for spec `25kzda` Section 3.3's mandated spec review and for its Section 4.8 checks, none of which can produce a record. The record carries no artifact-type field at all, so a review does not even record WHAT it reviewed. Notably the FILENAME grammar is already artifact-neutral (`build_review_name` delegates to `artifact_naming.build_clustered_name` with the `review` facet and the embedded id6 is simply the subject's), so only the front-matter field and the checker are plan-bound, which is evidence the original design intended neutrality and stopped short.
- Scope: Replace `- Plan-Id:` with the artifact-neutral pair `- Subject-Id:` plus `- Subject-Type: <ipd|spec>` across the writer, the parser, the checker, and every consumer, and migrate the 35 existing review records in the same change. Purely a SUBJECT-IDENTITY change: the findings columns, severity vocabulary, verdict vocabulary, decisions table, round structure, filename grammar, and every gating threshold stay exactly as they are. EXCLUDES the spec-review workflow and the attested transition (`5slbpi` owns both, and depends on this), excludes per-type review subdirectories (open backlog `sv0sf3`), and excludes any change to plan-review's behavior beyond reading and writing the new field names.
- Scope-Paths: agent_workflows/review_findings.py, agent_workflows/check_engine.py, agent_workflows/reviews.py, agent_workflows/specs.py, .aw/records/reviews, tests/test_review_findings.py, tests/test_review_findings_gate.py, tests/test_review_findings_cascade.py, tests/test_review_decisions.py, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long
- Item-Dependencies: none
- Status: to-review
- Set: revsweep
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: eyh1fu
- Blocks-Release: next
- From-Spec: 6m4kow

## Workflow history

- 2026-09-04 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored with the `revsweep` Set, graduating requirements R-01 through R-05 of spec `6m4kow`, which in turn completes spec `25kzda` Section 3.3. THE BLOCKER IS EXACT AND MEASURED, not inferred: the writer hardcodes `- Plan-Id:` at `review_findings.py:353`, and `check_engine._REVIEW_PLAN_ID_RE` (`:2455`) feeds `check_review_dangling` (`:2458`) whose `known` set comes from `_iter_plan_ipds` (`:2477-2480`), so a spec-subject review is reported dangling BY THE REPOSITORY'S OWN CHECKER with a recovery message telling the author to retire it. BLAST RADIUS MEASURED AT `3d4e5414`: the literal string `Plan-Id` appears 21 times across 9 tracked Python files, concentrated in `check_engine.py` (9) and `tests/test_review_findings.py` (4), plus 35 `.review.md` records each carrying the field once. That is small enough to do in ONE change, which is why D-02 of the spec chose replacement over a compatibility shim, and it is also why the migration must be MECHANICAL and shown rather than hand-edited. ONE THING DELIBERATELY NOT CHANGED, recorded so an executor does not "finish the job": the review FILENAME grammar is already artifact-neutral (`build_review_name:228-244` delegates to the shared `build_clustered_name` with the `review` facet) and only its DOCSTRINGS claim otherwise, so R-05 requires correcting prose, not code. THE RISK THAT DECIDES THE ORDER OF THIS PLAN'S ITEMS: `Subject-Type` makes the checker's resolution TYPE-DIRECTED, so a wrong or missing type silently sends resolution at the wrong tree and a real subject would read as dangling. E-03 therefore makes an absent-or-unknown `Subject-Type` a PARSE ERROR rather than a defaulted `ipd`, because defaulting is precisely how 35 migrated records would hide a migration bug.

## Goal

Make a review record able to name any reviewable artifact type, so a spec review can be filed and validated, without changing anything about how findings, verdicts, or gating work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the blocker, then change the record's shape

- [ ] E-01 Write the failing-first BLOCKER TEST before changing anything: construct a review record whose subject is a real SPEC and assert `aw check all` reports `check.review-dangling` for it. It MUST FAIL to be clean at current HEAD, demonstrating that the repository rejects a spec review today.
  This test is the plan's premise. Without it, the change looks like a rename; with it, the change is visibly a blocker removal. After E-03 the same subject must be clean, and a review whose subject genuinely does not exist must STILL be reported.
  - Depends on: none
  - Expected outcome: a test proving a spec-subject review is rejected at HEAD, with the `check.review-dangling` finding pasted.
  - Execution state: pending

- [ ] E-02 Change the WRITER and PARSER to the neutral pair: `- Subject-Id: <id6>` and `- Subject-Type: <ipd|spec>`, both REQUIRED on every record, replacing `- Plan-Id:` outright rather than adding a second field.
  `Subject-Type`'s vocabulary is CLOSED at `ipd|spec` (spec `6m4kow` R-02, D-03). Represent it as a closed tuple in one place, the way `SEVERITIES` and `DECISIONS` already are (`review_findings.py:54`, `:57`), so a new type requires amending the vocabulary and the dispatch table together rather than being introduced by writing a novel value into a file.
  ALSO UPDATE THE H1, which currently reads `# Plan review findings: <plan_id>` (`:351`), since it names the artifact type in prose that will now sometimes be wrong.
  DO NOT TOUCH the findings columns, `SEVERITIES`, `DECISIONS`, the round structure, `plan_readiness.VERDICTS`, or any threshold. This item changes WHO the record is about, nothing about what it says.
  - Depends on: E-01
  - Expected outcome: writer and parser use the required neutral pair; the type vocabulary is closed and declared once; the H1 no longer hardcodes "Plan"; no findings/verdict machinery changed.
  - Execution state: pending

- [ ] E-03 Make the dangling check TYPE-DIRECTED: resolve `Subject-Id` against the tree named by `Subject-Type`, not against the plans tree unconditionally.
  MAKE AN ABSENT OR UNKNOWN `Subject-Type` A PARSE ERROR, NOT A DEFAULT. This is the item's real design decision and the reason it is separate: if a missing type quietly defaults to `ipd`, then a migration that dropped the field on some records would still resolve those against the plans tree, they would still pass, and the bug would be invisible until a spec review silently read as dangling. Failing closed on an absent type converts that class of bug into an immediate loud error across 35 records.
  PRESERVE THE RULE'S ADVISORY SEVERITY. `check.review-dangling` is deliberately a `warning`, not an error, because "a review whose plan was deleted or superseded is untidy, not dangerous"; this plan makes it CORRECT for more types, and must not promote it to blocking as a side effect.
  PRESERVE THE PATH-LITERAL DISCIPLINE the function's own docstring records: discovery goes through `review_findings.iter_review_files`, and the function "deliberately contains NO `.aw/records/reviews` path literal". Do not add one while touching it.
  - Depends on: E-02
  - Expected outcome: resolution is directed by `Subject-Type`; a spec-subject review with a real subject is clean; a genuinely missing subject of EITHER type is still reported; an absent/unknown type is a loud parse error; the rule stays advisory; no new path literal.
  - Execution state: pending

### Task group 2: migrate the corpus and every consumer

- [ ] E-04 Migrate all 35 existing `.review.md` records MECHANICALLY, in this same change, setting `Subject-Type: ipd` for every one (all 35 are plan reviews today) and renaming the field.
  DO IT WITH A SCRIPT AND SHOW THE SCRIPT. 35 hand-edits is 35 chances to typo an id6, and an id6 typo produces exactly the dangling finding this plan exists to eliminate. Verify by counting: zero records retaining `Plan-Id`, 35 carrying both new fields, and every `Subject-Id` still resolving.
  DO NOT LEAVE A COMPATIBILITY READER. Pre-release conventions forbid shims (spec `6m4kow` D-02) and a parser that accepts both fields would let a half-migrated corpus pass, which is the state that makes the next change unsafe.
  - Depends on: E-03
  - Expected outcome: 35 records migrated by a shown script; zero `Plan-Id` remaining anywhere in the tree; all `Subject-Id` values resolve; no dual-field reader exists.
  - Execution state: pending

- [ ] E-05 Update every remaining consumer and its documentation. MEASURED SURFACE: the literal `Plan-Id` appears 21 times across 9 tracked Python files, concentrated in `check_engine.py` (9) and `tests/test_review_findings.py` (4), with single or double hits in `reviews.py`, `specs.py`, `review_findings.py`, and four other test files.
  INCLUDE THE DOCUMENTED CONTRACT, not just the code: `reviews.py:182-189` explains to a reader that "a review artifact carries `- Plan-Id:` instead ... So an id6 selector does NOT match a review's front matter", which becomes wrong prose the moment E-02 lands. Also correct `review_findings`'s docstrings that describe the filename's id6 as "the REVIEWED PLAN's id6" (`:19-21`, `:235`) and the gating predicates named `plan_gating_blocks`/`plan_blocks_dependents` (`:759`, `:842`), at minimum in their prose. RENAMING those functions is optional and, if done, must be a pure rename with no behavior change; say which you chose.
  UPDATE THE WORKFLOW BODIES that instruct an agent to write the record: `plan-review.md:178-185` and the parity copy under `plan-review-long/`. The two are held in DELIBERATE PARITY (`plan-review.md:17`), so an edit to one without the other is a fork; make both or neither.
  - Depends on: E-04
  - Expected outcome: zero `Plan-Id` references remain in code, tests, or workflow bodies; the `reviews.py` contract prose is corrected; both plan-review bodies updated in lockstep; any function rename stated and behavior-free.
  - Execution state: pending

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
| F-4 | THE BLAST RADIUS IS SMALL ENOUGH FOR ONE CHANGE, which is what makes replacement (rather than a compatibility shim) the cheaper option: 21 literal `Plan-Id` occurrences across 9 tracked Python files, and 35 review records each carrying it once. | measured at `3d4e5414`: `rg -c "Plan-Id"` over tracked `*.py` excluding worktrees gives `check_engine.py:9`, `tests/test_review_findings.py:4`, `reviews.py:2`, and 6 files with 1 each; `rg -c "^- Plan-Id:" .aw/records/reviews/*.review.md` matches 35 files |
| F-5 | A DOCUMENTED CONTRACT WILL BECOME FALSE PROSE, not merely stale code: `reviews.py` explains to readers that a review carries `Plan-Id` and that an id6 selector therefore does not match its front matter. Leaving it would misdocument the very field this plan introduces. | `reviews.py:182-189` |
| F-6 | ABSENCE OF A REVIEW IS DELIBERATELY SILENT TODAY (`plan_gating_blocks` returns EMPTY when no review artifact exists, documented because "zero `.review.md` files exist against 428 plans"). This plan does NOT change that, and must not be read as making a missing review an error; `5slbpi` R-11 is where absence becomes meaningful, and only for a spec transition. | `review_findings.py:758`, rationale at `:768-769` |
| F-7 | TYPE-DIRECTED RESOLUTION INTRODUCES A NEW SILENT-FAILURE MODE, which is why E-03 fails closed: if `Subject-Type` were defaulted rather than required, a migration that dropped the field would still resolve those records against the plans tree and still pass, hiding the bug across 35 files until a spec review read as dangling. | design consequence of `check_review_dangling` becoming type-directed; 35 records migrated at once by E-04 |
| F-8 | THE GATING PREDICATES ARE PLAN-NAMED IN THEIR SIGNATURES (`plan_gating_blocks(repo_root, plan_id6, ...)`, `plan_blocks_dependents`), so they will read as plan-only after this change even though they operate on a neutral record. Renaming is optional and must be behavior-free; leaving them is acceptable if the prose is corrected. | `review_findings.py:759`, `:842` |

## Proposed changes (ordered, validatable)

1. Failing-first test proving a spec-subject review is rejected at HEAD (E-01).
2. Writer and parser move to the required `Subject-Id`/`Subject-Type` pair with a closed, single-sourced type vocabulary (E-02).
3. The dangling check becomes type-directed, failing closed on an absent or unknown type, staying advisory (E-03).
4. All 35 records migrated by a shown script, with no dual-field reader left behind (E-04).
5. Every consumer, docstring, contract note, and both plan-review bodies updated (E-05).

## Deferred / out of scope (with reason)

- THE SPEC-REVIEW WORKFLOW AND THE ATTESTED `to-review -> reviewed` TRANSITION: `5slbpi` (spec `6m4kow` R-06 through R-13), which DEPENDS on this plan because it cannot file a conforming record until the record can describe a spec.
- MAKING A MISSING REVIEW MEANINGFUL FOR PLANS. Absence is deliberately silent (F-6) and 428 plans have no review record; changing that is a repository-wide policy change with no spec behind it. `5slbpi` requires a record only for the SPEC transition, going forward only.
- PER-TYPE SUBDIRECTORIES UNDER `.aw/records/reviews/`: open backlog `sv0sf3`, decided 65/35 toward the flat layout and orthogonal to the subject field.
- ADDING `reviews` TO THE ARTIFACT-TYPE ENUM. Deliberately absent with a documented rationale; adding it to the iterated `TYPE_FACET` map would make `aw set` accept a review file as status-settable.
- ANY CHANGE TO FINDINGS COLUMNS, SEVERITY OR VERDICT VOCABULARY, ROUND STRUCTURE, OR GATING THRESHOLDS. This plan changes the record's subject, not its content.
- WIDENING `Subject-Type` BEYOND `ipd|spec`. Backlog, research, releases and walkthroughs have no review action in spec `25kzda` Section 3 (3.6 gray-skips three of them; 3.4 gives backlog `graduate`), so a value for them would be unreachable surface.

## Scope check

- Over-scope: `.aw/system/workflows/plan-review*` is in Scope-Paths although this plan is not about plan-review's behavior. Justified and bounded: those bodies INSTRUCT an agent to write the record's front matter (`plan-review.md:178-185`), so leaving them would make every future review non-conforming the moment E-02 lands. The edit is limited to the field names, and the two bodies must change in lockstep because they are held in deliberate parity.
- Under-scope, DELIBERATE: a review record can DESCRIBE a spec after this plan, and nothing yet PRODUCES one; `5slbpi` does. This plan removes a blocker and delivers no user-visible capability on its own, which is stated rather than dressed up.
- Under-scope: the plan-named gating predicates may keep their names (F-8), with only their prose corrected.

## Required tests / validation

- E-01's blocker test, demonstrated FAILING at pre-change HEAD (the spec-subject review reported `check.review-dangling`), then clean after E-03.
- A review whose subject genuinely does NOT exist still reported dangling, for BOTH types. This is the regression that a type-directed resolver could silently lose, and it is what proves the check still works rather than merely stopping complaining.
- An absent or unknown `Subject-Type` producing a LOUD parse error, not a default (F-7).
- `check.review-dangling` still ADVISORY (`warning`), verified by exit code, not by reading the rule's declaration.
- MIGRATION COUNTS: zero `Plan-Id` anywhere in the tree, 35 records carrying both new fields, every `Subject-Id` resolving. Paste the migration script.
- `aw reviews decisions` still working against migrated records, since it is the only command that reads a record back.
- `aw check all` NO-WORSENING against your own fresh baseline; do NOT claim it passes (it has pre-existing findings, including backlog naming drift measured at authoring).
- The four review test modules plus `tests/test_selector_resolver_matrix.py` green.
- Full suite BARE (`python3 -m pytest`), compared against your own pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (backlog `dh0uno`).

## Spec / documentation sync

- This plan implements spec `6m4kow` R-01 through R-05. If execution proves a requirement wrong, amend the spec with `aw specs note` and say so; do not diverge silently.
- Both `plan-review` bodies must be updated in lockstep (they are held in deliberate parity), and `reviews.py`'s contract prose (F-5) corrected, since both would otherwise document a field that no longer exists.
- `.aw/records/reviews/README.md` must be checked and updated if it documents the front-matter shape.

## Open questions

### OQ-01: Should the plan-named gating predicates be renamed, or only their prose corrected?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT BLOCKING; either answer leaves behavior identical and E-05 permits both provided the choice is stated. The case for renaming `plan_gating_blocks`/`plan_blocks_dependents` to subject-neutral names: after this change they operate on a neutral record, so a plan-specific name misleads the next reader exactly as `Plan-Id` did. The case against: they are called from several sites and a rename inflates a diff whose value is the field change, making review harder for no behavior gain. Default is prose-only correction, on the ground that this plan's reviewable claim should stay "the record became neutral" rather than becoming a rename sweep; a follow-up may rename them cheaply once nothing else is in flight.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the spec-subject review record used, and paste `aw check all` reporting `check.review-dangling` against it at pre-change HEAD, including the message and recovery text. This is the plan's premise; without the observed rejection the rest reads as a rename.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a rendered record showing the required `- Subject-Id:`/`- Subject-Type:` pair and the corrected H1. Paste the closed type vocabulary declared ONCE, in the same shape as `SEVERITIES`/`DECISIONS`. Paste a diff or grep proving the findings columns, `SEVERITIES`, `DECISIONS`, round structure, and `plan_readiness.VERDICTS` are UNCHANGED, since this item's fence is that it touches only the subject.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the spec-subject review from V-01 now CLEAN. Then paste the regression that matters more: a review whose subject genuinely does not exist STILL reported dangling, for BOTH `ipd` and `spec` types, because a type-directed resolver that stopped complaining entirely would also look clean. Paste an absent `Subject-Type` and an unknown one each producing a LOUD parse error rather than defaulting to `ipd` (F-7). Paste the exit code proving the rule is still ADVISORY. Confirm no `.aw/records/reviews` path literal was added.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the migration SCRIPT (not a description of it). Paste counts: `Plan-Id` occurrences in the whole tree = 0, records carrying both new fields = 35, and every `Subject-Id` resolving to a real plan. Paste evidence NO dual-field reader was left, since a parser accepting both would let a half-migrated corpus pass. Paste `aw reviews decisions` working against migrated records.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste a tree-wide grep for `Plan-Id` returning ZERO hits in code, tests, workflow bodies, and records. Paste the corrected `reviews.py` contract prose (F-5) and the corrected `review_findings` docstrings. Paste BOTH plan-review bodies' updated record instructions side by side, proving parity was maintained rather than forked. STATE which OQ-01 option you took for the gating predicate names and, if renamed, paste evidence the rename was behavior-free. Then the review test modules, `aw check all` no-worsening against your own baseline, and the bare full suite with counts compared against your own pre-change measurement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 5 E-leaves across 2 task groups, one concern: the review record's subject becomes artifact-neutral. Task group 1 changes the shape (prove the blocker, then writer/parser, then checker); task group 2 propagates it (records, then consumers). E-02 and E-03 are separate because the writer change is mechanical while the checker change carries the real design decision (fail closed on an absent type rather than default), and folding them would let that decision pass unreviewed. E-04 and E-05 are separate because one migrates DATA and the other CODE, with different failure modes: a bad data migration produces false dangling findings, a missed code reference produces a crash.

Open questions: OQ-01 (rename the plan-named gating predicates, or correct prose only) is non-blocking with a recorded default and reason. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution. It has NO plan dependencies (`- Item-Dependencies: none`) and is the PREREQUISITE for `5slbpi`, which cannot file a conforming spec review until the record can describe one. It is independent of `76gsmv` and `6ypimw` and may proceed in parallel with them, since it touches the record and they touch the driver.

Scope fence: touch ONLY `agent_workflows/review_findings.py`, `agent_workflows/check_engine.py`, `agent_workflows/reviews.py`, `agent_workflows/specs.py`, the `.aw/records/reviews` records, the four review test modules, and the two plan-review workflow bodies. Do NOT change findings columns, `SEVERITIES`, `DECISIONS`, round structure, or `plan_readiness.VERDICTS`. Do NOT promote `check.review-dangling` from advisory to blocking. Do NOT add `reviews` to `ARTIFACT_TYPES` or `TYPE_FACET`. Do NOT make a MISSING review an error for plans (F-6). Do NOT leave a dual-field compatibility reader. Do NOT add a `.aw/records/reviews` path literal to `check_engine`. Do NOT create per-type review subdirectories. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is (1) V-01's observed REJECTION at HEAD, because without it this change reads as a rename rather than a blocker removal, and (2) V-03's proof that a genuinely missing subject is STILL reported, because a type-directed resolver that simply stopped complaining would look identical to a working one. Do NOT claim `aw check all` passes; the bar is no-worsening against your own fresh baseline. Do NOT report this plan as delivering spec review: it makes the record CAPABLE of describing one, and `5slbpi` produces it.

Execution contract: RE-READ `review_findings.py` and `check_engine.py` immediately before editing and locate every site BY SYMBOL, never by the line numbers in this plan. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. The 35 migrated records are DATA you are rewriting mechanically: verify `git diff --cached --name-only` lists exactly the records you migrated and nothing a co-worker touched, and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
