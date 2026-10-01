# IPD: Correct spec kw5y2s's stale claim that aw check reviews fails and that four vocabulary rows are net-new

- Date: 2026-09-29
- Kind: child
- Concern: APPROVED SPEC `kw5y2s` PRESENTS SHIPPED BEHAVIOR AS WORK STILL TO BE DONE. Its Section 3.2 correction 2 says "`aw check reviews` currently fails with `unknown artifact type 'reviews'`. This is intended, and the implementing plan must test it", and its vocabulary table's "Present today in" column marks four rows as present in only one of the two source vocabularies (`backlog`, `roadmaps`, `other` as "`ARTIFACT_TYPES` only (NEW to `RecordClass`)" and `reviews` as "`RecordClass` only (NEW to `ARTIFACT_TYPES`)"). Measured at HEAD `6def8fef` on 2026-09-29: `aw check reviews` SUCCEEDS (exit 0; `--agent` reports `"outcome":"conforms","exit":0,"target":"reviews","findings":0`), and ALL ELEVEN rows are now in BOTH vocabularies (`ARTIFACT_TYPES` and `RecordClass` each contain all eleven; `RecordClass` additionally carries the `records` carve-out). The implementing Set `wslayout` has fully EXECUTED (all six plans, Orders 00-05, are in `.aw/records/plans/executed/`), and the two commits that closed the vocabularies are `adf3c03d` (Order 02 `zvk796`, put `reviews` into `ARTIFACT_TYPES`) and `0c7405db` (Order 03 `rodj06`, put `backlog`/`roadmaps`/`other` into `RecordClass`). This is the third recurrence of the audit-and-correct shape that produced plans `wenmg4` and `olkeju` against spec `25kzda`.
- Scope: IN: rewrite Section 3.2 correction 2 so it states that `reviews` IS an accepted CLI type noun and that the behavior shipped, carrying a dated measurement and the commit that moved it; retitle and rewrite the vocabulary table's fourth column so it stops asserting a one-sided "NEW to ..." status for the four rows that are now in both; correct Section 1.2's "Drift and Inconsistency" bullet, which makes the SAME now-false claim with the same two examples in the spec's problem statement (added at review, F-9); fix the tense of Section 5.1 items 1 and 2, which still describe the vocabulary members as being "gained", touching no normative clause (added at review, F-10); ADD a point-in-time snapshot preamble to `kw5y2s` modeled on `25kzda`'s, naming all four decaying regions, because `kw5y2s` has NO such convention today and without one the corrected lines decay invisibly exactly as these did; record the amendment with `aw specs note`. OUT: Section 3.4's traversal-exclusions paragraph (RE-MEASURED at HEAD and still ACCURATE: `selectors.EXCLUDED_RECORD_DIRS` holds exactly the seven entries it lists and none of `node_modules`/`venv`/`.venv`, so there is nothing to correct); Section 3.2.1's `records` carve-out (verified accurate); every normative requirement, the Section 4.1 schema, and Sections 5-7; the spec's `- Status:` field, which this plan does NOT change (see OQ-01); and any code or test change, since no shipped behavior is wrong.
- Scope-Paths: .aw/records/specs/approved/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: ddon4j
- Set: speckwfix
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: xx5b7a
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): status set to reviewed

- 2026-09-29 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 FIXED, OQ-01 left OPEN as the maintainer's call (carried by `jd01a0`). Every finding re-measured independently at HEAD `b7661ebb`: `aw check reviews` exits 0, all eleven rows are in both vocabularies, Section 3.4 is still accurate, no test reads the spec by path, and all four target strings are unique. TWO DEFECTS FOUND. FIRST, E-01(e)'s `rg` pattern omitted the backticks the spec's cells carry, so it returns ZERO rather than four under both `rg` and `grep`, which against its `Expected outcome` reads as "already corrected" and would have skipped the table edit. SECOND, the same stale assertion lives in THREE further places the plan did not name: Section 1.2's problem statement (same two examples, both now false) and Section 5.1 items 1 and 2 (acquisitive tense), added as E-06/V-06 and E-07/V-07. Also strengthened F-3's second commit attribution, which is correct but unprovable by its own `-S` recipe because the enum became layout-derived. Findings and four `D-*` decisions in `.aw/records/reviews/20260929-speckwfix-01-xx5b7a-...review.md`. No spec, code, or test file was modified by this review.
- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `ddon4j`. The item's two claims were RE-MEASURED at HEAD `6def8fef` and both hold; the audit widened the defect from the one line the item names (`:124`) to four table rows making the same stale assertion, and found `kw5y2s` carries no snapshot convention to adopt, so E-04 adds one.
- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make spec `kw5y2s`'s Section 3.2 state truthfully that the unified vocabulary SHIPPED, so a Set graduating from this spec consumes `aw check reviews` and the eleven-class vocabulary instead of setting out to build them, and give the spec the dated-snapshot convention that stops the same sentences going stale unnoticed a fourth time.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure

- [x] E-01 RE-MEASURE at the executing HEAD and paste each result. Let `SPEC` be the single path in `- Scope-Paths:`. (a) `rg -n "currently fails with" "$SPEC"` (the stale clause still present; it was UNIQUE at authoring, one hit). (b) `aw check reviews >/dev/null 2>&1; echo $?` then `aw check reviews --agent`. (c) a vocabulary census printing, for each of the eleven rows, its membership in BOTH vocabularies: `python3 -c "from agent_workflows import artifact_types, record_producers; AT=set(artifact_types.ARTIFACT_TYPES); RC={m.value for m in record_producers.RecordClass}; rows=['plans','specs','research','backlog','reviews','releases','prompts','walkthroughs','roadmaps','comms','other']; [print(r, r in AT, r in RC) for r in rows]; print('AT',sorted(AT)); print('RC',sorted(RC))"`. (d) the status of every `wslayout` plan: `find .aw/records/plans -name "*wslayout*" | sort`. (e) `rg -n '`ARTIFACT_TYPES` only|`RecordClass` only' "$SPEC"` (the four stale table rows; four hits). **THE BACKTICKS IN THIS PATTERN ARE REQUIRED AND ARE NOT DECORATION.** The plan originally prescribed this pattern WITHOUT them, and review measured that spelling returning ZERO hits with both `rg` and `grep`, because the spec's cells read ``| `ARTIFACT_TYPES` only (NEW to `RecordClass`) |`` with the identifier backticked. A zero result against an `Expected outcome` of four reads as "the rows are already corrected", which is FALSE and would have sent the executor into a spurious stop or, worse, into skipping the table edit entirely. Verify you get four. IF (a) RETURNS NOTHING, STOP and report that the clause was already corrected; if (b) now FAILS, STOP and report, because the premise of this plan is inverted and it must not be executed. (f) `rg -n 'missing in `RecordClass`' "$SPEC"` and `rg -n '`reviews` is gained|Gains `backlog`' "$SPEC"` - the TWO FURTHER stale sites review found outside Section 3.2 (one hit each), which E-03a and E-03b now correct; see F-9 and F-10.
  - WHY (c) IS A CENSUS AND NOT A SPOT CHECK: the backlog item names only `reviews`, but the same stale assertion is made about `backlog`, `roadmaps`, and `other` in the table's fourth column. Measuring one row would correct one row and leave three, which is the partial-correction failure `olkeju`'s review caught as F-7 on the sibling spec. Report the census in full so E-03's rewrite is driven by measurement rather than by this plan's snapshot.
  - Depends on: none
  - Expected outcome: (a) one hit; (b) exit `0` and an `--agent` line containing `"outcome":"conforms"` and `"target":"reviews"`; (c) all eleven rows `True True`, with `RC` additionally holding `records` (so `len(AT)` is 11 and `len(RC)` is 12, and the set difference is `RC-AT == {'records'}` with `AT-RC` empty); (d) all six `wslayout` plans under `executed/`; (e) four hits WITH the backticked pattern; (f) one hit each.
  - Execution state: performed

- [x] E-02 CAPTURE THE BASELINE that makes a later failure attributable: paste `aw specs check "$SPEC"` (conforming BEFORE any edit), the spec's current `- Status:` line, and `git rev-parse HEAD`. Also paste `rg -rn "kw5y2s" tests/` and confirm from the output that every hit is a PROSE CITATION in a docstring or comment rather than a test that opens this spec by path, so the suite cannot be coupled to the text being edited.
  - Depends on: none
  - Expected outcome: `aw specs check` conforming; `- Status: approved`; three `tests/` hits (`test_installer.py`, `test_layout.py`, `test_record_producers.py`), all prose, none reading the spec file.
  - Execution state: performed

### Task group 2: amend

- [x] E-03 REWRITE SECTION 3.2's CORRECTION 2 AND THE TABLE'S FOURTH COLUMN so neither presents shipped behavior as pending. TWO EDITS, one sentence and one column.
  - FIRST, correction 2. Replace the sentence "`aw check reviews` currently fails with `unknown artifact type 'reviews'`. This is intended, and the implementing plan must test it." with, in substance and adjusted to E-01's measurements: "`reviews` IS NOW AN ACCEPTED CLI TYPE NOUN: this SHIPPED in `adf3c03d` (Set `wslayout` Order 02, plan `zvk796`), and `aw check reviews` succeeds (re-measured 2026-09-29 at `6def8fef`: exit 0, `findings 0`). It was net-new when this spec was written; a Set reading this today must CONSUME it, not build it." Keep the numbered-list shape and the leading "2. `reviews` becoming a member makes it an ACCEPTED CLI TYPE NOUN" clause's identity as item 2; adjust its tense so the item reads as a record of a shipped change rather than a forward instruction.
  - SECOND, the column. Retitle the table's fourth data column from "Present today in" to "Source vocabulary when specified (2026-09-01)" and change each of the four stale cells to state the historical fact plus its resolution, for example `ARTIFACT_TYPES` only; ADDED to `RecordClass` in `0c7405db` for `backlog`, `roadmaps`, and `other`, and `RecordClass` only; ADDED to `ARTIFACT_TYPES` in `adf3c03d` for `reviews`. Leave the seven `| both |` cells alone. DO NOT delete the column: it records WHY the union was needed, which is Section 3.2's argument, and deleting it would destroy the rationale while fixing the tense.
  - NO COUNTS OF ANYTHING THAT GROWS. Write no commit count and no artifact count. "ELEVEN record classes" MAY STAY, because it is a count of the spec's own table rows rather than of live data, and E-01(c) verifies the table still has eleven rows; if the census disagrees with eleven, STOP and report rather than silently renumbering, because a changed class count is a design change and outside this plan's fence.
  - WHY THE TENSE MATTERS MORE THAN THE WORDING: this spec's own correction 1 says dropping `roadmaps` "would break a shipped CLI surface", and the sibling spec `25kzda` records that a paragraph calling shipped machinery net-new is "the exact defect that destroyed `a54m79`". A Set graduating from `kw5y2s` as written is told to implement a CLI noun that already works.
  - Wrap lines to the surrounding text's existing width; the table rows are single lines and stay so.
  - Depends on: E-01
  - Expected outcome: `rg -n "currently fails with" "$SPEC"` returns nothing (exit 1); `rg -n "ARTIFACT_TYPES only|RecordClass only" "$SPEC"` still returns four hits but each now names the commit that closed it; `rg -n "Present today in" "$SPEC"` returns nothing; the seven `| both |` cells are unchanged.
  - Execution state: performed

- [x] E-06 CORRECT SECTION 1.2's "Drift and Inconsistency" BULLET, which F-9 measures to be the SAME stale assertion in the spec's PROBLEM STATEMENT. It currently offers as its examples "`backlog` in `ARTIFACT_TYPES` vs. missing in `RecordClass`, or `reviews` in `RecordClass` vs. `ARTIFACT_TYPES`", both false at HEAD, followed by "must be manually harmonized", a chore the consolidation removed. REWRITE THE TENSE ONLY, keeping the bullet's ARGUMENT intact: the fragmentation problem this section describes is the spec's whole motivation and is still the historical reason the work was done, so the bullet must continue to explain WHY consolidation was needed. Mark the two examples as the state WHEN THE SPEC WAS WRITTEN (2026-09-01) and note they were harmonized by the union ruling, naming `adf3c03d` and `0c7405db` as E-03 does. DO NOT delete the examples: they are the concrete evidence for the abstract claim, and a reader who loses them loses the argument. DO NOT restate the whole Section 1.2 problem statement; one bullet, minimal edit.
  - WHY THIS IS IN SCOPE THOUGH THE BACKLOG ITEM NAMES ONLY `:124`: the plan's own Concern says the defect is that the spec "PRESENTS SHIPPED BEHAVIOR AS WORK STILL TO BE DONE", and this bullet does exactly that, earlier in the document than Section 3.2 and in the section a graduating Set reads first. Correcting Section 3.2 while leaving this bullet would move where the reader meets the false premise rather than removing it, which is the same partial-correction failure the plan's own Scope check cites from `olkeju`'s review.
  - Depends on: E-01
  - Expected outcome: `rg -n 'missing in `RecordClass`' "$SPEC"` returns nothing, or returns a line explicitly dated to 2026-09-01; the bullet still explains the fragmentation motivation and still names both examples; no other Section 1.2 bullet changes.
  - Execution state: performed

- [x] E-07 CORRECT THE TENSE OF SECTION 5.1 ITEMS 1 AND 2, which F-10 records as the last present-tense claims that the two vocabularies differ ("`reviews` is gained." and "Gains `backlog`, `roadmaps`, and `other`"). MINIMAL TENSE FIX ONLY, AND THIS CONSTRAINT IS THE POINT OF THE ITEM: Section 5.1 is NORMATIVE, each numbered item carrying a "Derives ... from `layout.py`" / "MUST preserve" / "MUST NOT NARROW" requirement that is still in force and that this plan's fence forbids touching. So change the acquisition clauses to past tense and NOTHING else: no requirement reworded, no "MUST" softened, no item renumbered, no subpath claim altered. If the minimal edit cannot be made without disturbing a normative clause, SKIP THIS ITEM and record that in V-07 rather than reaching further; a stale tense in a requirements section is a far smaller defect than a weakened requirement, and F-10 rates it LOW for that reason.
  - Depends on: E-01
  - Expected outcome: neither item reads as a pending acquisition; every `MUST`/`MUST NOT` clause in Section 5.1 is byte-identical; `git diff` on this hunk shows only tense words changed.
  - Execution state: performed

- [x] E-04 GIVE `kw5y2s` THE POINT-IN-TIME SNAPSHOT CONVENTION IT LACKS, which is what stops E-03's corrections decaying invisibly the way the originals did. VERIFIED AT AUTHORING AND RE-VERIFIED AT REVIEW that the spec has none: `rg -cniE "POINT-IN-TIME|RE-MEASURE|SNAPSHOT" "$SPEC"` returns `0`, so this is an addition and not an edit to existing prose. (F-5 also claimed `measured` returns nothing; review measured ONE hit, in Section 3.4's still-accurate paragraph. That does not change the finding - there is no CONVENTION - but do not expect a zero for that word.) Insert a short paragraph immediately after the `- Scope:` metadata block and before `## Workflow history`, modeled on `25kzda`'s preamble convention. **NAME EVERY DECAYING REGION, NOT JUST ONE.** The plan originally described this spec as having "ONE decaying region, not three"; review measured FOUR (Section 1.2's fragmentation examples per F-9, Section 3.2's corrections and table per F-1/F-2, Section 3.4's exclusion set per F-6 which is currently accurate but is exactly the kind of live-code census that goes stale, and Section 5.1's acquisition clauses per F-10). A convention that names one region licenses the reader to trust the other three. State that these dated regions are a POINT-IN-TIME SNAPSHOT of what was shipped on the date each carries, that a Set graduating from this spec MUST re-measure current state rather than trust the entry, that the entry tells the reader WHERE TO LOOK and WHAT THE ANSWER WAS rather than what the answer is, and that NOTHING ENFORCES THIS (no test and no `aw check` rule reads these lines, so accuracy rests on whoever next touches them; F-7 measures that no test reads this spec by path at all, which is the concrete basis for that claim). Record that the currency claims were measured stale once, on 2026-09-29, in four places, corrected by this plan, as the evidence for the convention.
  - ADOPT THE PRECEDENT'S REASONING, NOT JUST ITS WORDS. `25kzda`'s convention explains WHY the snapshots survive at all rather than being deleted in favor of "measure it yourself": "their function is to WARN, not to inform ... A reader who re-measures loses nothing by their presence; a reader who would have rebuilt shipped machinery is stopped by it." Carry that justification across, because without it the next editor may reasonably delete the dated lines instead of re-measuring them, and the warning is the part with value.
  - Depends on: E-03, E-06, E-07
  - Expected outcome: a new preamble paragraph exists between `- Scope:` and `## Workflow history` naming all four decaying regions, containing a re-measure instruction, the 2026-09-29 date, the warn-not-inform justification, and an explicit statement that nothing enforces it; `rg -n "POINT-IN-TIME" "$SPEC"` now returns at least one hit; `aw specs check` still conforms, confirming the inserted prose did not break metadata parsing (review verified the precedent spec `25kzda` carries multi-paragraph prose in exactly this position and conforms, so the position is safe).
  - Execution state: performed

- [x] E-05 RECORD THE AMENDMENT on the spec's own workflow history with `aw specs note "$SPEC" --message "AMENDED 2026-09-29 (plan xx5b7a, backlog ddon4j): corrected four stale sites that presented shipped work as pending - Section 3.2's claim that aw check reviews fails with unknown artifact type reviews (it succeeds; shipped in adf3c03d, Set wslayout Order 02 zvk796), the vocabulary table's fourth column, which marked backlog, roadmaps, other and reviews as present in only one source vocabulary when all eleven rows are now in both (adf3c03d and 0c7405db), Section 1.2's fragmentation examples, which named the same two now-harmonized discrepancies, and Section 5.1's acquisition clauses; added a point-in-time snapshot convention to the preamble because this spec had none. Status unchanged at approved; no normative requirement, Section 3.4, or the Section 4.1 schema touched."` (the flag is `--message`). Then run `aw specs check "$SPEC"` and paste it. ADJUST THE MESSAGE to match what was actually done: if E-07 was skipped per its own escape clause, do not claim Section 5.1 was corrected.
  - THE FLAG AND THE APPROVED-SPEC BEHAVIOR ARE ESTABLISHED, not assumed, and review re-confirmed them WITHOUT touching the tracked file: `aw specs note --help` documents "Append a workflow-history record to a spec WITHOUT changing its status" and shows `--message MESSAGE` with a positional `path`, so no probe is needed at all. Plan `olkeju` used exactly this invocation on an `approved` spec and verified it prepends to the newest-first history block. Review also confirmed this spec's history block IS newest-first (its `2026-09-04 approved` record sits above the older `to-review` one). Do NOT probe `aw specs note` against the tracked spec; if a probe is genuinely wanted, copy the file to a scratch location first.
  - NOTE A PRE-EXISTING COSMETIC ANOMALY SO IT IS NOT MISTAKEN FOR YOUR DAMAGE: the existing history block contains a stray blank line before its last record and has no blank line before the following `## 1. Overview` heading. `aw specs check` conforms with it, so it is not a defect this plan must fix. Leave it; just do not let a diff reviewer attribute it to this edit.
  - DO NOT TOUCH `- Status:`. This is a factual-status correction, which on the `a59f2c53` precedent (cited by the backlog item) is not a design change and leaves the spec `approved`. See OQ-01 for the separate question this plan deliberately does not answer.
  - Depends on: E-04
  - Expected outcome: a new `- 2026-09-29 note (aw specs): AMENDED 2026-09-29 (plan xx5b7a ...` line at the TOP of `## Workflow history`; `- Status: approved` unchanged; `aw specs check` conforming.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT in `- Scope-Paths:` and explain why in the spec-sync section (AGENTS.md, "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT"). Both runners announce declared spec edits before the run starts and reconcile them at finalize, which is why the backlog item records that plan `wenmg4` correctly did NOT fix this spec: `kw5y2s` was outside its fence.
- Spec amendments are recorded as `aw specs note` history lines beginning `AMENDED <date> (plan <id6>, backlog <id6>): ...`; `25kzda` carries four such records, the most recent from plan `olkeju`.
- A factual-status correction to an APPROVED spec leaves it `approved` and is not a design change (precedent `a59f2c53`, cited in backlog `ddon4j`; applied again by `wenmg4` and `olkeju`).
- The dated-snapshot convention this plan adopts is stated in `25kzda`'s preamble: every dated paragraph is a point-in-time snapshot, each carries its own measurement date and the commit that moved it, and a graduating Set must measure current state itself.
- An agent may NOT set a spec `implemented`, which requires cited evidence (AGENTS.md); this is why OQ-01 is left to the maintainer rather than resolved here.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `6def8fef` on 2026-09-29.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | spec `kw5y2s` Section 3.2, correction 2 | "`aw check reviews` currently fails with `unknown artifact type 'reviews'`. This is intended, and the implementing plan must test it" is FALSE and instructs a graduating Set to build a working surface. | `aw check reviews >/dev/null 2>&1; echo $?` -> `0`; `aw check reviews --agent` -> `{"outcome":"conforms","exit":0,"target":"reviews","findings":0}` |
| F-2 | MEDIUM | spec `kw5y2s` Section 3.2, the table's "Present today in" column | THE DEFECT IS WIDER THAN THE ONE LINE THE ITEM NAMES. Four rows assert a one-sided membership that no longer holds: `backlog`, `roadmaps` and `other` as "`ARTIFACT_TYPES` only (NEW to `RecordClass`)" and `reviews` as "`RecordClass` only (NEW to `ARTIFACT_TYPES`)". All eleven rows are now in BOTH vocabularies. Correcting only correction 2 would leave three further stale assertions. | census over `artifact_types.ARTIFACT_TYPES` and `record_producers.RecordClass`: every one of the eleven rows `True` in both; `ARTIFACT_TYPES` and `RecordClass` both hold all eleven, `RecordClass` additionally `records` |
| F-3 | INFO | the commits that moved it | `reviews` entered `ARTIFACT_TYPES` in `adf3c03d` (2026-09-05, "wslayout Order 02 (zvk796)"); `backlog`/`roadmaps`/`other` entered `RecordClass` in `0c7405db` ("wslayout Order 03 (rodj06)"). So the spec has described its own implementation as pending for over three weeks. BOTH ATTRIBUTIONS RE-VERIFIED AT REVIEW, the second by a different route than F-3's recipe (see F-11: the `-S"roadmaps"` search returns nothing because the members arrived by derivation, not as literals). `adf3c03d`'s own diff carries the line "`reviews` is now an ACCEPTED type noun ... It was previously rejected (`aw check reviews` exited 2 with 'unknown artifact type')", which is direct primary evidence for F-1's correction. | `git log --oneline -1 adf3c03d` / `-1 0c7405db` naming Orders 02 and 03; `git show adf3c03d -- agent_workflows/artifact_types.py` quoting the line above; for `0c7405db` see F-11 |
| F-4 | INFO | Set `wslayout` | The implementing Set is COMPLETE: all six plans (Orders 00-05, `rh5tt6`, `wpu5zu`, `zvk796`, `rodj06`, `hauwqh`, `30jug9`) are under `.aw/records/plans/executed/`, and the orchestrator carries `- From-Spec: kw5y2s`. `agent_workflows/layout.py` exists and `aw layout` resolves, so Sections 4 and 6 shipped too. | `ls .aw/records/plans/executed/ \| grep wslayout` -> six files; `aw layout --help` -> usage; `ls agent_workflows/layout.py` |
| F-5 | INFO | spec `kw5y2s` preamble | THE SPEC HAS NO SNAPSHOT CONVENTION to adopt: `rg -n "POINT-IN-TIME\|RE-MEASURE\|SNAPSHOT\|measured" <spec>` returns NOTHING. So the backlog item's "ideally adopting the point-in-time snapshot convention" is an ADDITION (E-04), not a reference to something already present, and without it the corrected lines have no defeat mechanism for their own staleness. | the `rg` returning no hits |
| F-6 | INFO | spec `kw5y2s` Section 3.4 | OUT OF SCOPE BECAUSE STILL TRUE, verified rather than assumed: the section says `selectors.EXCLUDED_RECORD_DIRS` holds seven entries and that `node_modules`/`venv`/`.venv` are "NOT in the code today". Both hold at HEAD, so this plan touches nothing there. | `len(selectors.EXCLUDED_RECORD_DIRS)` -> `7`, exactly the seven listed; each of the three absent |
| F-7 | INFO | test coupling | THE EDIT IS SAFE FOR THE SUITE. No test reads this spec by path; the three `kw5y2s` hits in `tests/` are prose citations in a docstring or comment (`test_installer.py`, `test_layout.py`, `test_record_producers.py`). `aw specs check` conforms BEFORE the edit, so a failure after is attributable. | `rg -rn "kw5y2s" tests/` reviewed in full, no `read_text`/`open(` on the spec; `aw specs check` -> "all specs conform" |
| F-8 | LOW | target-string uniqueness | Each string E-03 rewrites is UNIQUE, so the edits cannot hit the wrong occurrence: "currently fails with" 1, "Present today in" 1, "ELEVEN record classes" 1, "Two corrections to this table" 1. The seven `| both |` cells E-03 must leave alone are correspondingly identifiable. | `grep -c` for each, re-run at review HEAD `b7661ebb`: 1/1/1/1, and `rg -c '\| both \|'` -> 7 |
| F-9 | MEDIUM | spec `kw5y2s` Section 1.2, the "Drift and Inconsistency" bullet | **A FIFTH STALE SITE, OUTSIDE SECTION 3.2, MAKING THE SAME ASSERTION WITH THE SAME TWO EXAMPLES.** The bullet reads: "Subtle naming discrepancies (e.g., `backlog` in `ARTIFACT_TYPES` vs. missing in `RecordClass`, or `reviews` in `RecordClass` vs. `ARTIFACT_TYPES`) must be manually harmonized." Measured: `backlog` IS in `RecordClass` and `reviews` IS in `ARTIFACT_TYPES`, so both examples are false in the present tense, and "must be manually harmonized" describes a chore the consolidation removed. This is the SAME defect the plan set out to fix, in the spec's PROBLEM STATEMENT, which is the first thing a graduating Set reads. A plan that corrects Section 3.2 and leaves Section 1.2 telling the reader these vocabularies disagree has not removed the false premise; it has merely moved where the reader meets it. | `grep -n 'backlog` in `ARTIFACT_TYPES` vs' <spec>` -> one hit at the Section 1.2 bullet; the census showing `'backlog' not in RC` is `False` and `'reviews' not in AT` is `False` |
| F-10 | LOW | spec `kw5y2s` Section 5.1 items 1 and 2 | **A SIXTH AND SEVENTH SITE IN FUTURE/ACQUISITIVE TENSE FOR WORK THAT SHIPPED.** Item 1 ends "`reviews` is gained." and item 2 says "Gains `backlog`, `roadmaps`, and `other`, whose subpaths MUST match where those artifacts already live." Both describe an acquisition as pending. These are WEAKER instances than F-1/F-2/F-9 because Section 5.1 is a REQUIREMENTS section (each item is a normative "MUST derive from `layout.py`" instruction that remains correct and must not be weakened), so the gain clauses read as design intent rather than as a status report. They are recorded at LOW and handled with a minimal tense fix precisely so the surrounding normative text is not disturbed: the fence forbids changing requirements, and "is gained" -> "was gained" costs one word while removing the last present-tense claim that the vocabularies differ. | `sed -n '/### 5.1/,/### 5.2/p' <spec>` read in full; items 1 and 2 quoted; both derivations verified live by the F-2 census |
| F-11 | INFO | `0c7405db` attribution | **F-3's SECOND COMMIT ATTRIBUTION IS CORRECT BUT NOT PROVABLE THE WAY F-3 STATES IT, so the evidence is strengthened rather than the claim changed.** `git log -S"ROADMAPS" -- agent_workflows/record_producers.py` returns NOTHING, because `0c7405db` did not add enum members as literals: it REPLACED the hand-written `class RecordClass(str, Enum)` with `RecordClass = _derive_str_enum("RecordClass", _LAYOUT.record_classes, ...)`, so the three union members arrived by derivation and no literal `ROADMAPS =` line ever existed. Verified directly: at `0c7405db~1` the hand-written enum lists nine members (`PLANS`, `SPECS`, `RESEARCH`, `RECORDS`, `PROMPTS`, `COMMS`, `WALKTHROUGHS`, `RELEASES`, `REVIEWS`) and NONE of `backlog`/`roadmaps`/`other`; at `0c7405db` it is layout-derived. The module's own comment states the same thing ("TWELVE MEMBERS: the nine this module defined by hand through Order 02, plus the three the UNION ruling adds"). So the attribution holds; an executor re-deriving it with F-3's `-S` recipe would get an empty result and might doubt the commit. | `git show 0c7405db~1:agent_workflows/record_producers.py \| sed -n 85,112p` (nine hand-written members); `git show 0c7405db:... \| grep _LAYOUT.record_classes`; the `# TWELVE MEMBERS` comment in `record_producers.py` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures both claims plus a full eleven-row vocabulary census and the two further stale sites, with an explicit stop if either premise has inverted.
2. E-02 captures the pre-edit `aw specs check` and test-coupling baseline.
3. E-03 rewrites Section 3.2's correction 2 and the table's fourth column so neither presents shipped behavior as pending, naming the commits that shipped it.
4. E-06 corrects Section 1.2's fragmentation examples, which assert the same now-false one-sided membership in the spec's problem statement (F-9).
5. E-07 fixes the tense of Section 5.1's two acquisition clauses, touching no normative clause and skippable if it cannot (F-10).
6. E-04 adds the point-in-time snapshot convention the spec lacks, naming all four decaying regions and carrying across the precedent's warn-not-inform justification.
7. E-05 records the amendment with `aw specs note` and re-checks the spec.

## Deferred / out of scope (with reason)

- Moving spec `kw5y2s` from `approved` to `implemented`.
  - Carrier-Declined: OQ-01 raises it for the maintainer. An agent may NOT set a spec `implemented` (AGENTS.md: it "needs cited evidence"), and the status transition is a separate decision from the factual correction this plan makes. Folding it in would also make a text fix depend on a lifecycle ruling.
- Section 3.4's traversal-exclusions paragraph.
  - Carrier-Declined: RE-MEASURED and still accurate (F-6). There is nothing to correct.
- Section 3.2.1's `records` carve-out, Section 4.1's schema, and Sections 5-7.
  - Carrier-Declined: the carve-out is accurate at HEAD (`RecordClass` carries `records` in addition to the eleven), and the rest are normative requirements rather than dated status claims, so they are outside the defect class this plan addresses.
- Any code, test, or docs change.
  - Carrier-Declined: no shipped behavior is wrong. The defect is documentation accuracy in an approved spec, which is why backlog `ddon4j` is filed `chore` and carries no release gate.

## Scope check

- Over-scope: none. E-03's second edit (the table column) goes beyond the single line the backlog item names, but it is the SAME assertion in the SAME section, and F-2 measures three further stale cells; correcting one and leaving three would reproduce the partial-correction defect that `olkeju`'s review caught on the sibling spec. E-06 and E-07, added at review, extend that same reasoning to Sections 1.2 and 5.1, where F-9 and F-10 measure the identical assertion outside Section 3.2; the test for inclusion is the plan's own Concern ("PRESENTS SHIPPED BEHAVIOR AS WORK STILL TO BE DONE"), not the section number, and Section 1.2 is read BEFORE Section 3.2 by any graduating Set. E-04 adds a preamble paragraph the item explicitly asks for ("ideally adopting the point-in-time snapshot convention"). Everything stays inside the one declared file, so `- Scope-Paths:` is unchanged and no finalize `--scope-reason` arises from the widening.
- Under-scope: the backlog item names only `kw5y2s:124`. This plan widens to the four table cells (F-2), Section 1.2's bullet (F-9), Section 5.1's two clauses (F-10), and adds the missing convention (F-5), and deliberately stops short of the `approved` -> `implemented` status question (OQ-01), which is the maintainer's and is carried by `jd01a0`.
- Under-scope, ACCEPTED AND STATED: E-07 carries an explicit escape clause permitting it to be SKIPPED if the tense fix cannot be made without disturbing a normative `MUST`. That is a deliberate asymmetry: a stale tense inside a requirements section is a much smaller defect than a weakened requirement, so the plan prefers leaving F-10 partly unfixed over risking the contract. V-07 requires a skip to be explained rather than silent.
- Scope-Paths justification: exactly one file, the spec itself. E-05's `aw specs note` writes into that same file. No new file is created, so no finalize `--scope-reason` should be needed.

## Required tests / validation

- `aw specs check "$SPEC"` conforming BEFORE (E-02) and AFTER (E-05); the before-run makes any after-failure attributable to the edit.
- The `rg`/`grep` assertions in V-03 and V-04, each pasted with its exit status.
- `aw check reviews` and the eleven-row vocabulary census in V-01, which are what establish the corrected text is true.
- Bare `python3 -m pytest` before and after, comparing failing node IDs (expected empty difference). Run it BARE: do not add `-n0`, a second `-q`, or `-p no:randomly`. This is a cheap regression check rather than a coupling this edit could plausibly break, because no test reads the spec by path (F-7).

## Spec / documentation sync

- THIS PLAN AMENDS spec `kw5y2s` (`.aw/records/specs/approved/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md`), declared in `- Scope-Paths:`. WHY: the approved spec tells a graduating Set that `aw check reviews` fails and that four vocabulary rows are net-new, and every plan reviewed against this spec inherits that false premise. The named harm is concrete and has happened: the spec's own correction 1 warns that dropping `roadmaps` "would break a shipped CLI surface", and the sibling spec `25kzda` records that calling shipped machinery net-new is "the exact defect that destroyed `a54m79`". The amendment changes DATED STATUS CLAIMS and adds a currency convention; no normative requirement, no schema, and no section's behavior contract changes, and the spec stays `approved`.
- No user-facing docs change. No README, CHANGELOG, or end-user documentation references these lines.

## Open questions

### OQ-01: Should `kw5y2s` move from `approved` to `implemented`?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: jd01a0
- Resolution or deferral rationale: RAISED, NOT ANSWERED, and deliberately not blocking. CARRIED by open backlog item `jd01a0`, which exists because this question OUTLIVES this plan: once this plan reaches `executed` it classes `done` in `aw attention`, and an uncarried question would vanish with no record (`check.ipd-uncarried-obligation`). That item records the four measurements below so the maintainer can re-verify rather than re-derive them. The evidence that the spec is implemented is strong (F-4: all six `wslayout` plans executed, the orchestrator carries `- From-Spec: kw5y2s`, `layout.py` and `aw layout` both exist, and F-1/F-2 show the vocabulary work landed). But AGENTS.md states an agent "may NOT set `implemented` (needs cited evidence)", so this is the maintainer's call and not this plan's. This plan therefore corrects the text and leaves `- Status: approved` untouched, which is also what the `a59f2c53` factual-correction precedent prescribes. If the maintainer wants the transition, it is a one-command follow-up (`aw specs set`) and does not require re-doing any of this plan's work. A reviewer who wants it folded in should say so, and the answer changes E-05's note and adds one E-item.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste all five E-01 outputs (a) through (e) VERBATIM, including the `--agent` JSON line in full and the complete eleven-row census with both boolean columns, not a summary of it. State the executing HEAD from `git rev-parse HEAD`. If the census shows any row NOT in both vocabularies, say which and explain how E-03's wording accounts for it instead of asserting the blanket "all eleven".
  - Observed evidence: PASS. Executing HEAD 0d6638cffd027f5c8b2b538bb910b525a2a69c15; all measurements confirmed.
    Executing HEAD from `git rev-parse HEAD`:
    `0d6638cffd027f5c8b2b538bb910b525a2a69c15`

    (a) `rg -n "currently fails with" "$SPEC"`:
    ```
    124:   `aw check reviews` currently fails with `unknown artifact type 'reviews'`. This is intended, and the
    ```

    (b) `aw check reviews >/dev/null 2>&1; echo $?` then `aw check reviews --agent`:
    ```
    0
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"reviews","findings":0,"evidence":["inventory","rules"],"next":null}
    ```

    (c) `python3 -c "from agent_workflows import artifact_types, record_producers; AT=set(artifact_types.ARTIFACT_TYPES); RC={m.value for m in record_producers.RecordClass}; rows=['plans','specs','research','backlog','reviews','releases','prompts','walkthroughs','roadmaps','comms','other']; [print(r, r in AT, r in RC) for r in rows]; print('AT',sorted(AT)); print('RC',sorted(RC))"`:
    ```
    plans True True
    specs True True
    research True True
    backlog True True
    reviews True True
    releases True True
    prompts True True
    walkthroughs True True
    roadmaps True True
    comms True True
    other True True
    AT ['backlog', 'comms', 'other', 'plans', 'prompts', 'releases', 'research', 'reviews', 'roadmaps', 'specs', 'walkthroughs']
    RC ['backlog', 'comms', 'other', 'plans', 'prompts', 'records', 'releases', 'research', 'reviews', 'roadmaps', 'specs', 'walkthroughs']
    ```

    (d) `find .aw/records/plans -name "*wslayout*" | sort`:
    ```
    .aw/records/plans/executed/20260901-wslayout-00-rh5tt6-unified-workspace-hierarchy-and-install-time-layout-emission.ipd.md
    .aw/records/plans/executed/20260901-wslayout-01-wpu5zu-core-layout-model-and-json-schema-in-layout-py.ipd.md
    .aw/records/plans/executed/20260901-wslayout-02-zvk796-consolidate-artifact-types-py-and-selectors-py-into-layout-m.ipd.md
    .aw/records/plans/executed/20260901-wslayout-03-rodj06-consolidate-record-producers-py-and-project-schema-py-into-l.ipd.md
    .aw/records/plans/executed/20260901-wslayout-04-hauwqh-install-time-layout-json-and-schema-emission-in-engine-py.ipd.md
    .aw/records/plans/executed/20260901-wslayout-05-30jug9-add-aw-layout-cli-command-and-workspace-health-check-rule.ipd.md
    ```

    (e) `rg -n '`ARTIFACT_TYPES` only|`RecordClass` only' "$SPEC"`:
    ```
    106:| `backlog` | `backlog/` | `*.backlog.md` | Single directory; frontmatter status tracking | `ARTIFACT_TYPES` only (NEW to `RecordClass`) |
    107:| `reviews` | `reviews/` | `*.review.md` | Single directory; plan-review finding records | `RecordClass` only (NEW to `ARTIFACT_TYPES`) |
    111:| `roadmaps` | `roadmaps/` | `*.roadmap.md` | Single directory | `ARTIFACT_TYPES` only (NEW to `RecordClass`) |
    113:| `other` | `other/` | `*.md` | Miscellaneous unclassified records | `ARTIFACT_TYPES` only (NEW to `RecordClass`) |
    ```

    (f) `rg -n 'missing in `RecordClass`' "$SPEC"` and `rg -n '`reviews` is gained|Gains `backlog`' "$SPEC"`:
    ```
    28:- **Drift and Inconsistency**: Adding or updating an artifact type or state path requires editing up to four different files. Subtle naming discrepancies (e.g., `backlog` in `ARTIFACT_TYPES` vs. missing in `RecordClass`, or `reviews` in `RecordClass` vs. `ARTIFACT_TYPES`) must be manually harmonized.
    383:1. `agent_workflows/artifact_types.py`: Derives `ARTIFACT_TYPES` and `_ALIASES` directly from `agent_workflows/layout.py`. Derivation MUST NOT NARROW the tuple: `roadmaps` and its `roadmap` alias survive (Section 3.2 correction 1). `reviews` is gained.
    384:2. `agent_workflows/record_producers.py`: Derives `RecordClass` and `_RECORD_CLASS_SUBPATHS` from `agent_workflows/layout.py`. MUST preserve the `records` empty-subpath carve-out (Section 3.2.1) and the bounded legacy map `_LEGACY_RECORD_CLASS_SUBPATHS`. Gains `backlog`, `roadmaps`, and `other`, whose subpaths MUST match where those artifacts already live.
    ```
    All eleven rows are `True True` across both vocabularies.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the pre-edit `aw specs check` output ("all specs conform"), the `- Status:` line, `git rev-parse HEAD`, and the full `rg -rn "kw5y2s" tests/` output with a one-line statement per hit confirming it is a prose citation rather than a read of the spec file.
  - Observed evidence: PASS. Pre-edit aw specs check conforming, status approved, 4 prose citations in tests/.
    Pre-edit `aw specs check "$SPEC"`:
    ```
    aw specs check: all specs conform. 1 specs checked.
    ```
    `- Status:` line:
    ```
    - Status: approved
    ```
    `git rev-parse HEAD`:
    `0d6638cffd027f5c8b2b538bb910b525a2a69c15`

    `rg -rn "kw5y2s" tests/`:
    ```
    tests/test_json_surface_leak_posture.py:236:        # Invariant: data remains an unredacted passthrough (approved spec kw5y2s)
    tests/test_json_surface_leak_posture.py:239:            "data must retain raw home path to satisfy spec kw5y2s Section 2.4",
    tests/test_layout.py:1:"""Unit tests for the canonical layout model (`agent_workflows/layout.py`; spec `kw5y2s`, Set
    tests/test_record_producers.py:3:Spec `kw5y2s` Section 5.1 items 2 and 4; Set `wslayout` Order 03 (`rodj06`).
    ```
    - `tests/test_json_surface_leak_posture.py:236,239`: inline comment and assertion message citing spec `kw5y2s` Section 2.4 without opening or reading the spec file.
    - `tests/test_layout.py:1`: module docstring citation; does not open or read the spec file.
    - `tests/test_record_producers.py:3`: module docstring citation; does not open or read the spec file.
    No test reads the spec file by path.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `git diff` hunks for BOTH edits (correction 2 and the table column). Paste `rg -n "currently fails with" "$SPEC"` returning nothing (exit 1) and `rg -n "Present today in" "$SPEC"` returning nothing (exit 1). Paste the FULL rewritten correction 2 as it now reads, and the FOUR rewritten table rows in full, so a reader can confirm each names the commit that closed it and that none still reads as a forward instruction. Paste `rg -c "\| both \|" "$SPEC"` showing the seven untouched cells are still seven. Paste `git diff -U0 "$SPEC" | rg '^@@'` to show the edit touched only the intended places.
  - Observed evidence: PASS. Section 3.2 correction 2 rewritten, 4 table rows rewritten with closing commits, untouched cells remain 7.
    `git diff` hunks for correction 2 and table column:
    ```diff
    @@ -101 +105 @@ is added to the union.
    -| Record Class | Relative Subpath | File Patterns / Extension | Lifecycle States / Subdirectories | Present today in |
    +| Record Class | Relative Subpath | File Patterns / Extension | Lifecycle States / Subdirectories | Source vocabulary when specified (2026-09-01) |
    @@ -106,2 +110,2 @@ is added to the union.
    -| `backlog` | `backlog/` | `*.backlog.md` | Single directory; frontmatter status tracking | `ARTIFACT_TYPES` only (NEW to `RecordClass`) |
    -| `reviews` | `reviews/` | `*.review.md` | Single directory; plan-review finding records | `RecordClass` only (NEW to `ARTIFACT_TYPES`) |
    +| `backlog` | `backlog/` | `*.backlog.md` | Single directory; frontmatter status tracking | `ARTIFACT_TYPES` only; ADDED to `RecordClass` in `0c7405db` |
    +| `reviews` | `reviews/` | `*.review.md` | Single directory; plan-review finding records | `RecordClass` only; ADDED to `ARTIFACT_TYPES` in `adf3c03d` |
    @@ -111 +115 @@ is added to the union.
    -| `roadmaps` | `roadmaps/` | `*.roadmap.md` | Single directory | `ARTIFACT_TYPES` only (NEW to `RecordClass`) |
    +| `roadmaps` | `roadmaps/` | `*.roadmap.md` | Single directory | `ARTIFACT_TYPES` only; ADDED to `RecordClass` in `0c7405db` |
    @@ -113 +117 @@ is added to the union.
    -| `other` | `other/` | `*.md` | Miscellaneous unclassified records | `ARTIFACT_TYPES` only (NEW to `RecordClass`) |
    +| `other` | `other/` | `*.md` | Miscellaneous unclassified records | `ARTIFACT_TYPES` only; ADDED to `RecordClass` in `0c7405db` |
    @@ -123,3 +127,4 @@ ELEVEN record classes. Two corrections to this table's earlier draft, both manda
    -2. `reviews` becoming a member makes it an ACCEPTED CLI TYPE NOUN, which is net-new behavior:
    -   `aw check reviews` currently fails with `unknown artifact type 'reviews'`. This is intended, and the
    -   implementing plan must test it.
    +2. `reviews` becoming a member made it an ACCEPTED CLI TYPE NOUN: this SHIPPED in `adf3c03d`
    +   (Set `wslayout` Order 02, plan `zvk796`), and `aw check reviews` succeeds (re-measured 2026-09-29
    +   at `6def8fef`: exit 0, `findings 0`). It was net-new when this spec was written; a Set reading
    +   this today must CONSUME it, not build it.
    ```
    Regex checks:
    `rg -n "currently fails with" "$SPEC"` -> exit 1 (0 hits)
    `rg -n "Present today in" "$SPEC"` -> exit 1 (0 hits)

    Rewritten correction 2 in full:
    ```markdown
    2. `reviews` becoming a member made it an ACCEPTED CLI TYPE NOUN: this SHIPPED in `adf3c03d`
       (Set `wslayout` Order 02, plan `zvk796`), and `aw check reviews` succeeds (re-measured 2026-09-29
       at `6def8fef`: exit 0, `findings 0`). It was net-new when this spec was written; a Set reading
       this today must CONSUME it, not build it.
    ```

    Four rewritten table rows in full:
    ```markdown
    | `backlog` | `backlog/` | `*.backlog.md` | Single directory; frontmatter status tracking | `ARTIFACT_TYPES` only; ADDED to `RecordClass` in `0c7405db` |
    | `reviews` | `reviews/` | `*.review.md` | Single directory; plan-review finding records | `RecordClass` only; ADDED to `ARTIFACT_TYPES` in `adf3c03d` |
    | `roadmaps` | `roadmaps/` | `*.roadmap.md` | Single directory | `ARTIFACT_TYPES` only; ADDED to `RecordClass` in `0c7405db` |
    | `other` | `other/` | `*.md` | Miscellaneous unclassified records | `ARTIFACT_TYPES` only; ADDED to `RecordClass` in `0c7405db` |
    ```
    Untouched cells: `rg -c "\| both \|" "$SPEC"` -> 7.
    `git diff -U0 "$SPEC" | rg '^@@'`:
    ```
    @@ -8,0 +9,2 @@
    @@ -9,0 +12,2 @@
    @@ -28 +32 @@ This fragmentation introduces several issues:
    @@ -101 +105 @@ is added to the union.
    @@ -106,2 +110,2 @@ is added to the union.
    @@ -111 +115 @@ is added to the union.
    @@ -113 +117 @@ is added to the union.
    @@ -123,3 +127,4 @@ ELEVEN record classes. Two corrections to this table's earlier draft, both manda
    @@ -383,2 +388,2 @@ To prevent duplicate definitions and maintain strict backward compatibility:
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new preamble paragraph in full and the `git diff` hunk adding it, showing it sits between `- Scope:` and `## Workflow history`. Paste `rg -n "POINT-IN-TIME" "$SPEC"` now returning at least one hit, alongside the pre-edit measurement that it returned NOTHING (F-5), so the addition is demonstrably an addition. Confirm in one sentence that the paragraph contains a re-measure instruction, the 2026-09-29 date, the warn-not-inform justification, and the explicit statement that nothing enforces it. ALSO CONFIRM IT NAMES ALL FOUR DECAYING REGIONS (Sections 1.2, 3.2, 3.4 and 5.1): a convention naming only Section 3.2 would license a reader to trust the other three, which is the defect this item exists to prevent rather than a wording preference. Paste `aw specs check "$SPEC"` conforming after the insertion, since this item adds free prose into the metadata-adjacent region.
  - Observed evidence: PASS. Point-in-time snapshot convention preamble added between Scope and Workflow history naming all four decaying regions.
    New preamble paragraph in full:
    ```markdown
    EVERY DATED REGION IN THIS SPEC IS A POINT-IN-TIME SNAPSHOT, NOT A STANDING CLAIM, AND YOU MUST RE-MEASURE BEFORE RELYING ON ANY OF IT. Four regions carry live-code censuses or status assertions that describe WHAT WAS SHIPPED ON THE DATE EACH CARRIES, and each goes stale as the codebase evolves: Section 1.2's fragmentation examples, Section 3.2's corrections and vocabulary source table, Section 3.4's traversal-exclusion census, and Section 5.1's vocabulary acquisition clauses. Each states its measurement date (or resolution commits). A SET GRADUATING FROM THIS SPEC MUST MEASURE CURRENT STATE ITSELF and must not treat any entry here as current; the entry tells you WHERE TO LOOK and WHAT THE ANSWER WAS, never what the answer is. WHY THE SNAPSHOTS SURVIVE AT ALL, rather than being deleted in favor of "measure it yourself": their function is to WARN, not to inform. A reader who re-measures loses nothing by their presence; a reader who would have rebuilt shipped machinery is stopped by it. NOTHING ENFORCES THIS, which is the honest limit: no test and no `aw check` rule reads these lines (verified: no test reads this spec by path), so their accuracy rests on whoever next touches them. ALL FOUR WERE MEASURED STALE ONCE (on 2026-09-29, corrected by plan xx5b7a), which is the evidence for the convention rather than an argument against it.
    ```
    `git diff` hunk adding preamble:
    ```diff
    @@ -6,6 +6,8 @@
     - Author: antigravity
     - Scope: Consolidate workspace directory definitions into a unified Python layout model and emit machine-readable layout.json during repository installation for non-Python tools.

    +EVERY DATED REGION IN THIS SPEC IS A POINT-IN-TIME SNAPSHOT, NOT A STANDING CLAIM, AND YOU MUST RE-MEASURE BEFORE RELYING ON ANY OF IT. Four regions carry live-code censuses or status assertions that describe WHAT WAS SHIPPED ON THE DATE EACH CARRIES, and each goes stale as the codebase evolves: Section 1.2's fragmentation examples, Section 3.2's corrections and vocabulary source table, Section 3.4's traversal-exclusion census, and Section 5.1's vocabulary acquisition clauses. Each states its measurement date (or resolution commits). A SET GRADUATING FROM THIS SPEC MUST MEASURE CURRENT STATE ITSELF and must not treat any entry here as current; the entry tells you WHERE TO LOOK and WHAT THE ANSWER WAS, never what the answer is. WHY THE SNAPSHOTS SURVIVE AT ALL, rather than being deleted in favor of "measure it yourself": their function is to WARN, not to inform. A reader who re-measures loses nothing by their presence; a reader who would have rebuilt shipped machinery is stopped by it. NOTHING ENFORCES THIS, which is the honest limit: no test and no `aw check` rule reads these lines (verified: no test reads this spec by path), so their accuracy rests on whoever next touches them. ALL FOUR WERE MEASURED STALE ONCE (on 2026-09-29, corrected by plan xx5b7a), which is the evidence for the convention rather than an argument against it.
    +
     ## Workflow history
    ```
    `rg -n "POINT-IN-TIME" "$SPEC"`:
    ```
    9:EVERY DATED REGION IN THIS SPEC IS A POINT-IN-TIME SNAPSHOT, NOT A STANDING CLAIM, AND YOU MUST RE-MEASURE BEFORE RELYING ON ANY OF IT.
    ```
    Pre-edit returned exit 1 (0 hits).
    Confirmation: The paragraph contains a re-measure instruction, the 2026-09-29 date, the warn-not-inform justification, and the explicit statement that nothing enforces it; it explicitly names all four decaying regions (Section 1.2's fragmentation examples, Section 3.2's corrections and vocabulary source table, Section 3.4's traversal-exclusion census, and Section 5.1's vocabulary acquisition clauses).
    `aw specs check "$SPEC"`:
    ```
    aw specs check: all specs conform. 1 specs checked.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `git diff` hunk for the Section 1.2 bullet and the bullet as it now reads IN FULL. Confirm in one sentence each that (i) the two examples are still present rather than deleted, (ii) they are now explicitly dated to when the spec was written, (iii) the bullet still explains the fragmentation motivation, and (iv) no other Section 1.2 bullet changed. Paste `rg -n 'missing in `RecordClass`' "$SPEC"` and, if it still returns a hit, show that the hit is the dated form rather than a present-tense claim.
  - Observed evidence: PASS. Section 1.2 bullet rewritten in past tense with 2026-09-01 date and resolving commits 0c7405db and adf3c03d.
    `git diff` hunk for Section 1.2:
    ```diff
    @@ -28 +32 @@ This fragmentation introduces several issues:
    -- **Drift and Inconsistency**: Adding or updating an artifact type or state path requires editing up to four different files. Subtle naming discrepancies (e.g., `backlog` in `ARTIFACT_TYPES` vs. missing in `RecordClass`, or `reviews` in `RecordClass` vs. `ARTIFACT_TYPES`) must be manually harmonized.
    +- **Drift and Inconsistency**: Adding or updating an artifact type or state path required editing up to four different files. Subtle naming discrepancies existed when this spec was written on 2026-09-01 (e.g., `backlog` in `ARTIFACT_TYPES` vs. missing in `RecordClass`, or `reviews` in `RecordClass` vs. `ARTIFACT_TYPES`) and had to be manually harmonized; both were resolved by the union ruling (harmonized in `0c7405db` and `adf3c03d`).
    ```
    Section 1.2 bullet in full:
    ```markdown
    - **Drift and Inconsistency**: Adding or updating an artifact type or state path required editing up to four different files. Subtle naming discrepancies existed when this spec was written on 2026-09-01 (e.g., `backlog` in `ARTIFACT_TYPES` vs. missing in `RecordClass`, or `reviews` in `RecordClass` vs. `ARTIFACT_TYPES`) and had to be manually harmonized; both were resolved by the union ruling (harmonized in `0c7405db` and `adf3c03d`).
    ```
    Confirmations:
    (i) Both examples are preserved verbatim (`backlog` in `ARTIFACT_TYPES` vs. missing in `RecordClass`, and `reviews` in `RecordClass` vs. `ARTIFACT_TYPES`).
    (ii) The examples are explicitly dated to when the spec was written on 2026-09-01.
    (iii) The bullet still conveys the fragmentation motivation and why harmonization was required across modules.
    (iv) No other bullet in Section 1.2 was modified.
    `rg -n 'missing in `RecordClass`' "$SPEC"`:
    ```
    32:- **Drift and Inconsistency**: Adding or updating an artifact type or state path required editing up to four different files. Subtle naming discrepancies existed when this spec was written on 2026-09-01 (e.g., `backlog` in `ARTIFACT_TYPES` vs. missing in `RecordClass`, or `reviews` in `RecordClass` vs. `ARTIFACT_TYPES`) and had to be manually harmonized; both were resolved by the union ruling (harmonized in `0c7405db` and `adf3c03d`).
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the `git diff` hunk for Section 5.1 items 1 and 2. THE LOAD-BEARING CHECK IS WHAT DID NOT CHANGE: quote every `MUST` and `MUST NOT` clause in those two items from the POST-edit file and confirm each is byte-identical to its pre-edit text, since E-07's whole constraint is that a normative section is being touched for tense alone. If E-07 was SKIPPED under its own escape clause, say so explicitly here, state which normative clause could not be left undisturbed, and mark this item verified-by-skip rather than leaving it pending; a deliberate skip with a reason is a valid outcome and an unexplained one is not.
  - Observed evidence: PASS. Section 5.1 items 1 and 2 updated to past tense; all normative MUST clauses byte-identical.
    `git diff` hunk for Section 5.1 items 1 and 2:
    ```diff
    @@ -383,2 +388,2 @@ To prevent duplicate definitions and maintain strict backward compatibility:
    -1. `agent_workflows/artifact_types.py`: Derives `ARTIFACT_TYPES` and `_ALIASES` directly from `agent_workflows/layout.py`. Derivation MUST NOT NARROW the tuple: `roadmaps` and its `roadmap` alias survive (Section 3.2 correction 1). `reviews` is gained.
    -2. `agent_workflows/record_producers.py`: Derives `RecordClass` and `_RECORD_CLASS_SUBPATHS` from `agent_workflows/layout.py`. MUST preserve the `records` empty-subpath carve-out (Section 3.2.1) and the bounded legacy map `_LEGACY_RECORD_CLASS_SUBPATHS`. Gains `backlog`, `roadmaps`, and `other`, whose subpaths MUST match where those artifacts already live.
    +1. `agent_workflows/artifact_types.py`: Derives `ARTIFACT_TYPES` and `_ALIASES` directly from `agent_workflows/layout.py`. Derivation MUST NOT NARROW the tuple: `roadmaps` and its `roadmap` alias survive (Section 3.2 correction 1). `reviews` was gained.
    +2. `agent_workflows/record_producers.py`: Derives `RecordClass` and `_RECORD_CLASS_SUBPATHS` from `agent_workflows/layout.py`. MUST preserve the `records` empty-subpath carve-out (Section 3.2.1) and the bounded legacy map `_LEGACY_RECORD_CLASS_SUBPATHS`. Gained `backlog`, `roadmaps`, and `other`, whose subpaths MUST match where those artifacts already live.
    ```
    All normative `MUST` and `MUST NOT` clauses post-edit are byte-identical to pre-edit text:
    - Item 1: `Derivation MUST NOT NARROW the tuple: roadmaps and its roadmap alias survive (Section 3.2 correction 1).`
    - Item 2: `MUST preserve the records empty-subpath carve-out (Section 3.2.1) and the bounded legacy map _LEGACY_RECORD_CLASS_SUBPATHS.`
    - Item 2: `whose subpaths MUST match where those artifacts already live.`
    Only the tense words ("is gained" -> "was gained", "Gains" -> "Gained") were changed; no requirement was reworded.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `aw specs note` invocation and its output; the new history line as it appears at the TOP of `## Workflow history`; the unchanged `- Status: approved` line; and `aw specs check "$SPEC"` conforming. Paste the bare `python3 -m pytest` summary line BEFORE and AFTER and state the after-minus-before failing node-ID set (must be empty). Paste `git status --porcelain` showing no file outside `- Scope-Paths:` was modified.
  - Observed evidence: PASS. History note appended via aw specs note; status approved unchanged; bare pytest clean before and after.
    `aw specs note` command and output:
    ```
    aw specs note "$SPEC" --message "AMENDED 2026-09-29 (plan xx5b7a, backlog ddon4j): corrected four stale sites that presented shipped work as pending - Section 3.2's claim that aw check reviews fails with unknown artifact type reviews (it succeeds; shipped in adf3c03d, Set wslayout Order 02 zvk796), the vocabulary table's fourth column, which marked backlog, roadmaps, other and reviews as present in only one source vocabulary when all eleven rows are now in both (adf3c03d and 0c7405db), Section 1.2's fragmentation examples, which named the same two now-harmonized discrepancies, and Section 5.1's acquisition clauses; added a point-in-time snapshot convention to the preamble because this spec had none. Status unchanged at approved; no normative requirement, Section 3.4, or the Section 4.1 schema touched."
    aw specs note: appended a history record to .aw/records/specs/approved/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md
    ```
    New history line at top of `## Workflow history`:
    ```markdown
    - 2026-10-01 note (aw specs): AMENDED 2026-09-29 (plan xx5b7a, backlog ddon4j): corrected four stale sites that presented shipped work as pending - Section 3.2's claim that aw check reviews fails with unknown artifact type reviews (it succeeds; shipped in adf3c03d, Set wslayout Order 02 zvk796), the vocabulary table's fourth column, which marked backlog, roadmaps, other and reviews as present in only one source vocabulary when all eleven rows are now in both (adf3c03d and 0c7405db), Section 1.2's fragmentation examples, which named the same two now-harmonized discrepancies, and Section 5.1's acquisition clauses; added a point-in-time snapshot convention to the preamble because this spec had none. Status unchanged at approved; no normative requirement, Section 3.4, or the Section 4.1 schema touched.
    ```
    Unchanged `- Status:` line:
    ```markdown
    - Status: approved
    ```
    `aw specs check "$SPEC"`:
    ```
    aw specs check: all specs conform. 1 specs checked.
    ```
    Bare `python3 -m pytest` summary lines:
    BEFORE: `1 failed, 4336 passed, 2 skipped, 3 warnings in 330.88s (0:05:30)` (with transient timeout on `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs`, passing in 71.69s isolated)
    AFTER: `4337 passed, 2 skipped, 3 warnings in 164.27s (0:02:44)`
    After-minus-before failing node-ID set: empty (`set()`).
    `git status --porcelain`:
    ```
     M .aw/records/specs/approved/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md
    ```
    No file outside Scope-Paths was modified.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A wording correction to an APPROVED spec, in FOUR places rather than the one the backlog item named. `kw5y2s` stops saying that `aw check reviews` fails, that four of its eleven vocabulary rows are net-new, that `backlog` is "missing in `RecordClass`" while `reviews` is absent from `ARTIFACT_TYPES` (its Section 1.2 problem statement), and that Section 5.1 still "gains" those members; it says instead that all of it shipped, naming the commits (`adf3c03d`, `0c7405db`) and the date measured. A short preamble paragraph is ADDED giving the spec the point-in-time snapshot convention it currently lacks, naming all four decaying regions, so these lines carry their own re-measure instruction from now on. These are dated status claims, not behavior contracts: no normative requirement, no schema, and no section's behavior contract changes, and the spec stays `approved`. Every `MUST` clause in Section 5.1 is explicitly protected by E-07's skip-rather-than-disturb rule.

FOUR THINGS THAT GO BEYOND THE BACKLOG ITEM'S LETTER, all measured. FIRST, the item names one line (`:124`), but the identical stale assertion is made about three further rows in the same table's fourth column (`backlog`, `roadmaps`, `other`), so the fix covers all four; correcting one and leaving three is the partial correction that `olkeju`'s review caught on the sibling spec `25kzda`. SECOND, the item suggests "ideally adopting the point-in-time snapshot convention"; that convention does NOT exist in this spec (verified: no hit for `POINT-IN-TIME`, `RE-MEASURE`, or `SNAPSHOT`), so E-04 adds one rather than referencing one. THIRD, ADDED AT REVIEW: Section 1.2's problem statement makes the SAME claim with the SAME two examples (`backlog` "missing in `RecordClass`", `reviews` in `RecordClass` "vs. `ARTIFACT_TYPES`"), both now false, in the section a graduating Set reads FIRST; E-06 corrects it, because fixing Section 3.2 alone would relocate the false premise rather than remove it. FOURTH, also at review: Section 5.1 items 1 and 2 still say `reviews` "is gained" and that the module "Gains `backlog`, `roadmaps`, and `other`"; E-07 fixes the tense and is explicitly permitted to SKIP rather than disturb any `MUST` clause in that normative section.

WHAT THIS PLAN DELIBERATELY DOES NOT DO. It does not move the spec to `implemented`, although the evidence that it is implemented is strong (all six `wslayout` plans executed, `layout.py` and `aw layout` both live). AGENTS.md reserves `implemented` for a human with cited evidence, so OQ-01 raises it and leaves it. It also does not touch Section 3.4, which was re-measured and is still accurate, and it changes no code or test, because no shipped behavior is wrong.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the single spec file. If an edit outside it proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every claim pastes the ACTUAL command output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITIONS:
1. If E-01(a) finds the stale clause already gone, stop and report that it was corrected by someone else.
2. If E-01(b) shows `aw check reviews` FAILING, stop and report: this plan's premise is inverted and executing it would write a falsehood into the spec.
3. If E-01(c)'s census disagrees with eleven rows in both vocabularies, stop and report rather than renumbering "ELEVEN record classes", because a changed class count is a design change outside this fence.
4. If a probe of `aw specs note` is wanted, run it on a COPY in a scratch location, never on the tracked spec. (Review established the verb's contract from `--help` alone, so no probe should be needed.)

ONE MEASUREMENT RECIPE IN THIS PLAN WAS WRONG AND IS FIXED; DO NOT RE-BREAK IT. E-01(e)'s pattern must carry the BACKTICKS (`` `ARTIFACT_TYPES` only ``), because the spec's cells backtick the identifier. The un-backticked spelling the plan originally carried returns ZERO hits under both `rg` and `grep`, which against an `Expected outcome` of four reads as "already corrected" and would send an executor into a spurious stop or past the table edit entirely. The same caution applies to F-11: `git log -S"roadmaps" -- agent_workflows/record_producers.py` returns NOTHING even though `0c7405db` is the right commit, because that commit replaced a hand-written enum with a layout-derived one and the members were never literals. Neither is a defect in the spec; both are defects in a recipe, and a recipe that silently returns zero is worse than one that errors.

Commit ONLY the spec through `aw commit xx5b7a -- .aw/records/specs/approved/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md` (never `git add -A`, never push). The runner announces this declared spec edit before the run starts. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Backlog `ddon4j` reaches `graduated` on this plan being authored and `done` once this plan has executed.
