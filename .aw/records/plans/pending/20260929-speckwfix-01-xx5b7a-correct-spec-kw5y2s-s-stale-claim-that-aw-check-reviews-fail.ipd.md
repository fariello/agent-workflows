# IPD: Correct spec kw5y2s's stale claim that aw check reviews fails and that four vocabulary rows are net-new

- Date: 2026-09-29
- Kind: child
- Concern: APPROVED SPEC `kw5y2s` PRESENTS SHIPPED BEHAVIOR AS WORK STILL TO BE DONE. Its Section 3.2 correction 2 says "`aw check reviews` currently fails with `unknown artifact type 'reviews'`. This is intended, and the implementing plan must test it", and its vocabulary table's "Present today in" column marks four rows as present in only one of the two source vocabularies (`backlog`, `roadmaps`, `other` as "`ARTIFACT_TYPES` only (NEW to `RecordClass`)" and `reviews` as "`RecordClass` only (NEW to `ARTIFACT_TYPES`)"). Measured at HEAD `6def8fef` on 2026-09-29: `aw check reviews` SUCCEEDS (exit 0; `--agent` reports `"outcome":"conforms","exit":0,"target":"reviews","findings":0`), and ALL ELEVEN rows are now in BOTH vocabularies (`ARTIFACT_TYPES` and `RecordClass` each contain all eleven; `RecordClass` additionally carries the `records` carve-out). The implementing Set `wslayout` has fully EXECUTED (all six plans, Orders 00-05, are in `.aw/records/plans/executed/`), and the two commits that closed the vocabularies are `adf3c03d` (Order 02 `zvk796`, put `reviews` into `ARTIFACT_TYPES`) and `0c7405db` (Order 03 `rodj06`, put `backlog`/`roadmaps`/`other` into `RecordClass`). This is the third recurrence of the audit-and-correct shape that produced plans `wenmg4` and `olkeju` against spec `25kzda`.
- Scope: IN: rewrite Section 3.2 correction 2 so it states that `reviews` IS an accepted CLI type noun and that the behavior shipped, carrying a dated measurement and the commit that moved it; retitle and rewrite the vocabulary table's fourth column so it stops asserting a one-sided "NEW to ..." status for the four rows that are now in both; ADD a point-in-time snapshot preamble to `kw5y2s` modeled on `25kzda`'s, because `kw5y2s` has NO such convention today and without one the corrected lines decay invisibly exactly as these did; record the amendment with `aw specs note`. OUT: Section 3.4's traversal-exclusions paragraph (RE-MEASURED at HEAD and still ACCURATE: `selectors.EXCLUDED_RECORD_DIRS` holds exactly the seven entries it lists and none of `node_modules`/`venv`/`.venv`, so there is nothing to correct); Section 3.2.1's `records` carve-out (verified accurate); every normative requirement, the Section 4.1 schema, and Sections 5-7; the spec's `- Status:` field, which this plan does NOT change (see OQ-01); and any code or test change, since no shipped behavior is wrong.
- Scope-Paths: .aw/records/specs/approved/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: ddon4j
- Set: speckwfix
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: xx5b7a

## Workflow history

- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `ddon4j`. The item's two claims were RE-MEASURED at HEAD `6def8fef` and both hold; the audit widened the defect from the one line the item names (`:124`) to four table rows making the same stale assertion, and found `kw5y2s` carries no snapshot convention to adopt, so E-04 adds one.
- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make spec `kw5y2s`'s Section 3.2 state truthfully that the unified vocabulary SHIPPED, so a Set graduating from this spec consumes `aw check reviews` and the eleven-class vocabulary instead of setting out to build them, and give the spec the dated-snapshot convention that stops the same sentences going stale unnoticed a fourth time.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure

- [ ] E-01 RE-MEASURE at the executing HEAD and paste each result. Let `SPEC` be the single path in `- Scope-Paths:`. (a) `rg -n "currently fails with" "$SPEC"` (the stale clause still present; it was UNIQUE at authoring, one hit). (b) `aw check reviews >/dev/null 2>&1; echo $?` then `aw check reviews --agent`. (c) a vocabulary census printing, for each of the eleven rows, its membership in BOTH vocabularies: `python3 -c "from agent_workflows import artifact_types, record_producers; AT=set(artifact_types.ARTIFACT_TYPES); RC={m.value for m in record_producers.RecordClass}; rows=['plans','specs','research','backlog','reviews','releases','prompts','walkthroughs','roadmaps','comms','other']; [print(r, r in AT, r in RC) for r in rows]; print('AT',sorted(AT)); print('RC',sorted(RC))"`. (d) the status of every `wslayout` plan: `find .aw/records/plans -name "*wslayout*" | sort`. (e) `rg -n "ARTIFACT_TYPES only|RecordClass only" "$SPEC"` (the four stale table rows; four hits at authoring). IF (a) RETURNS NOTHING, STOP and report that the clause was already corrected; if (b) now FAILS, STOP and report, because the premise of this plan is inverted and it must not be executed.
  - WHY (c) IS A CENSUS AND NOT A SPOT CHECK: the backlog item names only `reviews`, but the same stale assertion is made about `backlog`, `roadmaps`, and `other` in the table's fourth column. Measuring one row would correct one row and leave three, which is the partial-correction failure `olkeju`'s review caught as F-7 on the sibling spec. Report the census in full so E-03's rewrite is driven by measurement rather than by this plan's snapshot.
  - Depends on: none
  - Expected outcome: (a) one hit; (b) exit `0` and an `--agent` line containing `"outcome":"conforms"` and `"target":"reviews"`; (c) all eleven rows `True True`, with `RC` additionally holding `records`; (d) all six `wslayout` plans under `executed/`; (e) four hits.
  - Execution state: pending

- [ ] E-02 CAPTURE THE BASELINE that makes a later failure attributable: paste `aw specs check "$SPEC"` (conforming BEFORE any edit), the spec's current `- Status:` line, and `git rev-parse HEAD`. Also paste `rg -rn "kw5y2s" tests/` and confirm from the output that every hit is a PROSE CITATION in a docstring or comment rather than a test that opens this spec by path, so the suite cannot be coupled to the text being edited.
  - Depends on: none
  - Expected outcome: `aw specs check` conforming; `- Status: approved`; three `tests/` hits (`test_installer.py`, `test_layout.py`, `test_record_producers.py`), all prose, none reading the spec file.
  - Execution state: pending

### Task group 2: amend

- [ ] E-03 REWRITE SECTION 3.2's CORRECTION 2 AND THE TABLE'S FOURTH COLUMN so neither presents shipped behavior as pending. TWO EDITS, one sentence and one column.
  - FIRST, correction 2. Replace the sentence "`aw check reviews` currently fails with `unknown artifact type 'reviews'`. This is intended, and the implementing plan must test it." with, in substance and adjusted to E-01's measurements: "`reviews` IS NOW AN ACCEPTED CLI TYPE NOUN: this SHIPPED in `adf3c03d` (Set `wslayout` Order 02, plan `zvk796`), and `aw check reviews` succeeds (re-measured 2026-09-29 at `6def8fef`: exit 0, `findings 0`). It was net-new when this spec was written; a Set reading this today must CONSUME it, not build it." Keep the numbered-list shape and the leading "2. `reviews` becoming a member makes it an ACCEPTED CLI TYPE NOUN" clause's identity as item 2; adjust its tense so the item reads as a record of a shipped change rather than a forward instruction.
  - SECOND, the column. Retitle the table's fourth data column from "Present today in" to "Source vocabulary when specified (2026-09-01)" and change each of the four stale cells to state the historical fact plus its resolution, for example `ARTIFACT_TYPES` only; ADDED to `RecordClass` in `0c7405db` for `backlog`, `roadmaps`, and `other`, and `RecordClass` only; ADDED to `ARTIFACT_TYPES` in `adf3c03d` for `reviews`. Leave the seven `| both |` cells alone. DO NOT delete the column: it records WHY the union was needed, which is Section 3.2's argument, and deleting it would destroy the rationale while fixing the tense.
  - NO COUNTS OF ANYTHING THAT GROWS. Write no commit count and no artifact count. "ELEVEN record classes" MAY STAY, because it is a count of the spec's own table rows rather than of live data, and E-01(c) verifies the table still has eleven rows; if the census disagrees with eleven, STOP and report rather than silently renumbering, because a changed class count is a design change and outside this plan's fence.
  - WHY THE TENSE MATTERS MORE THAN THE WORDING: this spec's own correction 1 says dropping `roadmaps` "would break a shipped CLI surface", and the sibling spec `25kzda` records that a paragraph calling shipped machinery net-new is "the exact defect that destroyed `a54m79`". A Set graduating from `kw5y2s` as written is told to implement a CLI noun that already works.
  - Wrap lines to the surrounding text's existing width; the table rows are single lines and stay so.
  - Depends on: E-01
  - Expected outcome: `rg -n "currently fails with" "$SPEC"` returns nothing (exit 1); `rg -n "ARTIFACT_TYPES only|RecordClass only" "$SPEC"` still returns four hits but each now names the commit that closed it; `rg -n "Present today in" "$SPEC"` returns nothing; the seven `| both |` cells are unchanged.
  - Execution state: pending

- [ ] E-04 GIVE `kw5y2s` THE POINT-IN-TIME SNAPSHOT CONVENTION IT LACKS, which is what stops E-03's corrections decaying invisibly the way the originals did. VERIFIED AT AUTHORING that the spec has none: `rg -n "POINT-IN-TIME|RE-MEASURE|SNAPSHOT" "$SPEC"` returns NOTHING, so this is an addition and not an edit to existing prose. Insert a short paragraph immediately after the `- Scope:` metadata block and before `## Workflow history`, modeled on `25kzda`'s preamble convention but sized to this spec (which has ONE decaying region, not three): state that Section 3.2's vocabulary table and its corrections are a POINT-IN-TIME SNAPSHOT of what was shipped on the date each carries, that a Set graduating from this spec MUST re-measure current state rather than trust the entry, that the entry tells the reader WHERE TO LOOK and WHAT THE ANSWER WAS rather than what the answer is, and that NOTHING ENFORCES THIS (no test and no `aw check` rule reads these lines, so accuracy rests on whoever next touches them). Record that the table's currency claims were measured stale once, on 2026-09-29, corrected by this plan, as the evidence for the convention.
  - ADOPT THE PRECEDENT'S REASONING, NOT JUST ITS WORDS. `25kzda`'s convention explains WHY the snapshots survive at all rather than being deleted in favor of "measure it yourself": "their function is to WARN, not to inform ... A reader who re-measures loses nothing by their presence; a reader who would have rebuilt shipped machinery is stopped by it." Carry that justification across, because without it the next editor may reasonably delete the dated lines instead of re-measuring them, and the warning is the part with value.
  - Depends on: E-03
  - Expected outcome: a new preamble paragraph exists between `- Scope:` and `## Workflow history` containing a re-measure instruction, the 2026-09-29 date, and an explicit statement that nothing enforces it; `rg -n "POINT-IN-TIME" "$SPEC"` now returns at least one hit.
  - Execution state: pending

- [ ] E-05 RECORD THE AMENDMENT on the spec's own workflow history with `aw specs note "$SPEC" --message "AMENDED 2026-09-29 (plan xx5b7a, backlog ddon4j): corrected Section 3.2's stale claim that aw check reviews fails with unknown artifact type reviews (it succeeds; shipped in adf3c03d, Set wslayout Order 02 zvk796) and the vocabulary table's fourth column, which marked backlog, roadmaps, other and reviews as present in only one source vocabulary when all eleven rows are now in both (adf3c03d and 0c7405db); added a point-in-time snapshot convention to the preamble because this spec had none. Status unchanged at approved; no normative requirement, Section 3.4, or the Section 4.1 schema touched."` (the flag is `--message`). Then run `aw specs check "$SPEC"` and paste it.
  - THE FLAG AND THE APPROVED-SPEC BEHAVIOR ARE ESTABLISHED, not assumed: plan `olkeju` used exactly this invocation on an `approved` spec, verified it prepends the record to the newest-first history block and leaves `- Status:` untouched, and its E-04 records that it probed this on a scratch COPY rather than the tracked file. Do NOT probe `aw specs note` against the tracked spec; if a probe is wanted, copy the file to a scratch location first.
  - DO NOT TOUCH `- Status:`. This is a factual-status correction, which on the `a59f2c53` precedent (cited by the backlog item) is not a design change and leaves the spec `approved`. See OQ-01 for the separate question this plan deliberately does not answer.
  - Depends on: E-04
  - Expected outcome: a new `- 2026-09-29 note (aw specs): AMENDED 2026-09-29 (plan xx5b7a ...` line at the TOP of `## Workflow history`; `- Status: approved` unchanged; `aw specs check` conforming.
  - Execution state: pending

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
| F-3 | INFO | the commits that moved it | `reviews` entered `ARTIFACT_TYPES` in `adf3c03d` (2026-09-05, "wslayout Order 02 (zvk796)"); `backlog`/`roadmaps`/`other` entered `RecordClass` in `0c7405db` ("wslayout Order 03 (rodj06)"). So the spec has described its own implementation as pending for over three weeks. | `git log --oneline -S"reviews" -- agent_workflows/artifact_types.py`; `git log --oneline -S"roadmaps" -- agent_workflows/record_producers.py` |
| F-4 | INFO | Set `wslayout` | The implementing Set is COMPLETE: all six plans (Orders 00-05, `rh5tt6`, `wpu5zu`, `zvk796`, `rodj06`, `hauwqh`, `30jug9`) are under `.aw/records/plans/executed/`, and the orchestrator carries `- From-Spec: kw5y2s`. `agent_workflows/layout.py` exists and `aw layout` resolves, so Sections 4 and 6 shipped too. | `ls .aw/records/plans/executed/ \| grep wslayout` -> six files; `aw layout --help` -> usage; `ls agent_workflows/layout.py` |
| F-5 | INFO | spec `kw5y2s` preamble | THE SPEC HAS NO SNAPSHOT CONVENTION to adopt: `rg -n "POINT-IN-TIME\|RE-MEASURE\|SNAPSHOT\|measured" <spec>` returns NOTHING. So the backlog item's "ideally adopting the point-in-time snapshot convention" is an ADDITION (E-04), not a reference to something already present, and without it the corrected lines have no defeat mechanism for their own staleness. | the `rg` returning no hits |
| F-6 | INFO | spec `kw5y2s` Section 3.4 | OUT OF SCOPE BECAUSE STILL TRUE, verified rather than assumed: the section says `selectors.EXCLUDED_RECORD_DIRS` holds seven entries and that `node_modules`/`venv`/`.venv` are "NOT in the code today". Both hold at HEAD, so this plan touches nothing there. | `len(selectors.EXCLUDED_RECORD_DIRS)` -> `7`, exactly the seven listed; each of the three absent |
| F-7 | INFO | test coupling | THE EDIT IS SAFE FOR THE SUITE. No test reads this spec by path; the three `kw5y2s` hits in `tests/` are prose citations in a docstring or comment (`test_installer.py`, `test_layout.py`, `test_record_producers.py`). `aw specs check` conforms BEFORE the edit, so a failure after is attributable. | `rg -rn "kw5y2s" tests/` reviewed in full, no `read_text`/`open(` on the spec; `aw specs check` -> "all specs conform" |
| F-8 | LOW | target-string uniqueness | Each string E-03 rewrites is UNIQUE, so the edits cannot hit the wrong occurrence: "currently fails with" 1, "Present today in" 1, "ELEVEN record classes" 1, "Two corrections to this table" 1. The seven `| both |` cells E-03 must leave alone are correspondingly identifiable. | `grep -c` for each |

## Proposed changes (ordered, validatable)

1. E-01 re-measures both claims plus a full eleven-row vocabulary census, with an explicit stop if either premise has inverted.
2. E-02 captures the pre-edit `aw specs check` and test-coupling baseline.
3. E-03 rewrites correction 2 and the table's fourth column so neither presents shipped behavior as pending, naming the commits that shipped it.
4. E-04 adds the point-in-time snapshot convention the spec lacks, carrying across the precedent's warn-not-inform justification.
5. E-05 records the amendment with `aw specs note` and re-checks the spec.

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

- Over-scope: none. E-03's second edit (the table column) goes beyond the single line the backlog item names, but it is the SAME assertion in the SAME section, and F-2 measures three further stale cells; correcting one and leaving three would reproduce the partial-correction defect that `olkeju`'s review caught on the sibling spec. E-04 adds a preamble paragraph the item explicitly asks for ("ideally adopting the point-in-time snapshot convention"). Both stay inside the one declared file.
- Under-scope: the backlog item names only `kw5y2s:124`. This plan widens to the four table cells (F-2) and adds the missing convention (F-5), and deliberately stops short of the `approved` -> `implemented` status question (OQ-01), which is the maintainer's.
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

- [ ] V-01 validates E-01
  - Required evidence: paste all five E-01 outputs (a) through (e) VERBATIM, including the `--agent` JSON line in full and the complete eleven-row census with both boolean columns, not a summary of it. State the executing HEAD from `git rev-parse HEAD`. If the census shows any row NOT in both vocabularies, say which and explain how E-03's wording accounts for it instead of asserting the blanket "all eleven".
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the pre-edit `aw specs check` output ("all specs conform"), the `- Status:` line, `git rev-parse HEAD`, and the full `rg -rn "kw5y2s" tests/` output with a one-line statement per hit confirming it is a prose citation rather than a read of the spec file.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff` hunks for BOTH edits (correction 2 and the table column). Paste `rg -n "currently fails with" "$SPEC"` returning nothing (exit 1) and `rg -n "Present today in" "$SPEC"` returning nothing (exit 1). Paste the FULL rewritten correction 2 as it now reads, and the FOUR rewritten table rows in full, so a reader can confirm each names the commit that closed it and that none still reads as a forward instruction. Paste `rg -c "\| both \|" "$SPEC"` showing the seven untouched cells are still seven. Paste `git diff -U0 "$SPEC" | rg '^@@'` to show the edit touched only the intended places.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new preamble paragraph in full and the `git diff` hunk adding it, showing it sits between `- Scope:` and `## Workflow history`. Paste `rg -n "POINT-IN-TIME" "$SPEC"` now returning at least one hit, alongside the authoring-time measurement that it returned NOTHING before (F-5), so the addition is demonstrably an addition. Confirm in one sentence that the paragraph contains a re-measure instruction, the 2026-09-29 date, the warn-not-inform justification, and the explicit statement that nothing enforces it.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `aw specs note` invocation and its output; the new history line as it appears at the TOP of `## Workflow history`; the unchanged `- Status: approved` line; and `aw specs check "$SPEC"` conforming. Paste the bare `python3 -m pytest` summary line BEFORE and AFTER and state the after-minus-before failing node-ID set (must be empty). Paste `git status --porcelain` showing no file outside `- Scope-Paths:` was modified.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A wording correction to an APPROVED spec. `kw5y2s`'s Section 3.2 stops saying that `aw check reviews` fails and that four of its eleven vocabulary rows are net-new, and says instead that both shipped, naming the commits (`adf3c03d`, `0c7405db`) and the date measured. A short preamble paragraph is ADDED giving the spec the point-in-time snapshot convention it currently lacks, so these lines carry their own re-measure instruction from now on. These are dated status claims, not behavior contracts: no normative requirement, no schema, and no other section changes, and the spec stays `approved`.

TWO THINGS THAT GO BEYOND THE BACKLOG ITEM'S LETTER, both measured. FIRST, the item names one line (`:124`), but the identical stale assertion is made about three further rows in the same table's fourth column (`backlog`, `roadmaps`, `other`), so the fix covers all four; correcting one and leaving three is the partial correction that `olkeju`'s review caught on the sibling spec `25kzda`. SECOND, the item suggests "ideally adopting the point-in-time snapshot convention"; that convention does NOT exist in this spec (verified: no hit for `POINT-IN-TIME`, `RE-MEASURE`, or `SNAPSHOT`), so E-04 adds one rather than referencing one.

WHAT THIS PLAN DELIBERATELY DOES NOT DO. It does not move the spec to `implemented`, although the evidence that it is implemented is strong (all six `wslayout` plans executed, `layout.py` and `aw layout` both live). AGENTS.md reserves `implemented` for a human with cited evidence, so OQ-01 raises it and leaves it. It also does not touch Section 3.4, which was re-measured and is still accurate, and it changes no code or test, because no shipped behavior is wrong.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the single spec file. If an edit outside it proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every claim pastes the ACTUAL command output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITIONS:
1. If E-01(a) finds the stale clause already gone, stop and report that it was corrected by someone else.
2. If E-01(b) shows `aw check reviews` FAILING, stop and report: this plan's premise is inverted and executing it would write a falsehood into the spec.
3. If E-01(c)'s census disagrees with eleven rows in both vocabularies, stop and report rather than renumbering "ELEVEN record classes", because a changed class count is a design change outside this fence.
4. If a probe of `aw specs note` is wanted, run it on a COPY in a scratch location, never on the tracked spec.

Commit ONLY the spec through `aw commit xx5b7a -- .aw/records/specs/approved/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md` (never `git add -A`, never push). The runner announces this declared spec edit before the run starts. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Backlog `ddon4j` reaches `graduated` on this plan being authored and `done` once this plan has executed.
