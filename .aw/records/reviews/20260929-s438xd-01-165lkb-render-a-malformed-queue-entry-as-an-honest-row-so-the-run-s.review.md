# Review findings: plan 165lkb

- Subject-Id: 165lkb
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-102 (BLOCKER, fixed), PR-101, PR-103 (HIGH, fixed), PR-104 (MEDIUM, fixed), PR-105, PR-106 (LOW, fixed)

## Round 1

Reviewed at lane HEAD `4e7dd52c` in an isolated review lane. The plan file was committed and unchanged,
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize --agent` reports
`conforming` after revision.

THE PLAN IS UNUSUALLY WELL EVIDENCED AND ITS CENTRAL ARGUMENT SURVIVES SCRUTINY. Its headline claim is
that the backlog item's one-guard framing is wrong, and that claim is correct and was reproduced in full.
I re-ran the cascade myself, applying guards in stages against a patched copy of the module: with no
guards the `run_order`-present state raises in the `sorted()` key lambda; with the sort key and row loop
guarded it raises in `item_is_dispatchable_work`; with the four helpers additionally guarded it raises in
an outcome-ladder genexpr. Three distinct guard groups, each a separate defect, exactly as F-03 says.

F-04's contrast is real and is the plan's sharpest observation. The backlog item's own reproduction (no
`run_order`) crashes at `pos = item.get("position", idx + 1)`, while the realistic shape (with `run_order`,
which every dispatching run writes) crashes EARLIER in the sort key. A test copied from the item would
therefore exercise only the later site. F-07's direction measurement reproduced exactly (`1/1` for `False`,
`1/2` for `True`). F-11 reproduced exactly across all six queue shapes, with `queue_performed_no_work`
called ZERO times and the outcome words `QUEUED`, `PARTIAL`, `QUEUED`, `QUEUED`, `FAILED`, `QUEUED`.
F-13's resolver probe returns stage `unknown` with the diagnostic `unrecognized native status
'malformed-entry' for family 'runner-item'`, styles without raising, and the token is in neither owner
enum. F-08's harder half reproduced too: `execution_index` crashes on a WELL-FORMED item when a malformed
sibling is in the queue, with the frame inside `item_is_dispatchable_work`, so E-04's guard genuinely does
not save it. F-14 reproduced against a real temporary run directory. F-17's baseline matched to the test:
`3246 passed, 2 skipped, 3 warnings in 54.63s`.

WHAT REVIEW FOUND, and the two findings that matter were found by STAGING the plan's own prescribed
implementation rather than by reading it. That is the method the plan's own evidence standard invites, and
it is the only method that would have caught either.

FIRST, AND THE ONE THAT WOULD HAVE SHIPPED A NON-FIX: E-05's summary of its own sites undercounts them,
and the undercount is in the instruction an executor follows rather than in the measurement. F-03's
twelve-entry enumeration is accurate and lists the two success tuples separately as its entries (8) and
(9); I re-measured it and it holds. But E-05, which is what an executor actually reads while editing,
calls them "the four outcome-ladder comprehensions" while parenthetically naming five things, so the
arithmetic only works if the `COMPLETED` and `NO WORK PERFORMED` branches' byte-identical success-tuple
`all(...)` calls count as one guard. That is the discrepancy, and it is worth stating precisely: the plan
MEASURED correctly and INSTRUCTED incorrectly, which is harder to catch than a bad measurement because
the findings table vindicates the author. I staged precisely that reading - every other guard applied, plus a
`replace(count=1)` over the shared text, which is the natural implementation of an edit to two identical
strings - and the mixed queue `["not-a-mapping", {"status": "reviewed", ...}]` still raised `AttributeError`
from the second branch's genexpr. The failure mode is self-concealing in a way worth stating: the guarded
first test correctly returns `False`, and that is exactly what hands control to the unguarded twin. An
all-malformed single-entry queue reaches the same twin, so the plan's own minimal reproduction does not
distinguish a one-guard from a two-guard implementation. Without a mixed queue and an occurrence count, an
executor could paste a passing E-01 run and a green suite over a still-broken renderer.

SECOND, E-03 directed the executor into a closed trap. It requires the `Pos` cell to carry a marker rather
than a fabricated number, and that requirement is right (the gate's third silent-failure mode defends it
well). But the row loop builds `"pos": f"{pos:02d}"`, and `f"{'??':02d}"` raises `ValueError: Unknown
format code 'd' for object of type 'str'`. So assigning the marker and letting the shared
`items_data.append(...)` run converts this plan's `AttributeError` into a `ValueError` at the same point
in the same tail, losing the table just as completely from code that reads as a correct fix. The two
obvious escapes are both closed - fabricating a number is forbidden by the gate, and formatting the marker
is impossible - so the only correct implementation is a separate append plus `continue`, and the plan did
not say so.

THIRD, the exit tail is eight shared statements, not the five F-02 lists. Read statement by statement from
both hosts' `run_queue`, the omitted two are `report_run_spec_edits` and `report_driver_committed_reviews`,
and they sit BETWEEN surfaces this plan discusses. Neither crashes, but `report_run_spec_edits` DEGRADES,
printing `SPEC CHANGES: could not be computed (AttributeError); the run is starting anyway. Any declared
spec edit in this queue is therefore UNREPORTED, not absent.` where a well-formed queue prints nothing.
This matters mechanically because V-06 demands a probe of the tail "in tail order" and would have been
satisfied by probing an incomplete list. Sibling plan `cup9r7`'s review independently measured the same
eight and the same degradation, which is corroboration.

I ALSO MEASURED WHAT THE PLAN ASKS ITS EXECUTOR TO MEASURE, so V-05 has a bar rather than an open
instruction. With all three guard groups staged, 300 malformed-entry inputs (a malformed entry against
each of nine well-formed sibling shapes plus alone, both queue orders, crossed with `run_order`, tracker,
color and `exit_reason`) rendered with ZERO failures, which is what establishes the guard set COMPLETE and
not merely sufficient for E-01's cases. Separately, the pre-fix and post-fix renderers were compared over
96 well-formed inputs and produced byte-identical output in all 96, with zero disagreements. Both numbers
are now F-21 and V-05 states them as the floor.

THE PLAN'S HONESTY DISCIPLINE IS EXEMPLARY AND I WANT TO RECORD IT, because it is the reason review could
be this cheap. It declines to fix `execution_index` in its own file and explains why on a measured
boundary; it declines to file two unowned defects and explains whose decision that is; its gate forbids
the executor from claiming the closing report is restored when it demonstrably is not; and it carries no
`- Readiness:` field, correctly leaving that attestation to this review. Nothing in the three corrections
above impeaches any of that.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-102 | BLOCKER | IN-SCOPE | A. Correctness / E. Testing (a fix that does not fix) | Staged implementation: all guards except the second success tuple, applied as `replace(..., count=1)` over the byte-identical text; queue `["not-a-mapping", {"id6":"aaaaaa","position":2,"status":"reviewed"}]` raises `AttributeError: 'str' object has no attribute 'get'` from a genexpr at the `NO WORK PERFORMED` branch's `all(` (enclosing `elif (`); the shared text occurs exactly twice in `render_stream.render_run_summary_table`; F-03's entries (8) and (9) already list both separately | **E-05's summary of its own sites undercounts them, and the undercount is a working non-fix.** It lists "four outcome-ladder comprehensions" while parenthetically naming five things, treating the two byte-identical success tuples as one. F-03's enumeration is CORRECT and lists them separately, so the defect is in the instruction an executor follows rather than in the measurement, which is harder to catch because the findings table vindicates the author. Guarding one leaves the other raising, and the failure is self-concealing: the guarded `COMPLETED` test returns `False`, which is precisely what reaches the unguarded twin, so the plan's own single-entry reproduction passes with only one guarded. An executor could paste a passing E-01 run and a green suite over a renderer that still crashes on the realistic mixed queue | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | New F-19 records the staged measurement, the mechanism that hides it, the two-occurrence count, and that F-03 had it right. E-05 rewritten to enumerate SIX sites individually and numbered, stating that the success tuples are distinct textual occurrences and that a count-of-one replacement leaves one raw. V-05 now demands an occurrence count proving both are guarded PLUS a render of the mixed queue, and notes the all-malformed queue does not distinguish the two. Goal now states the count is CONFIRMED and that the instruction was what was wrong; F-03 annotated as re-measured; Scope, Scope check and proposed-changes item 5 reconciled; added as the FOURTH silent-failure mode in the gate |
| PR-101 | HIGH | IN-SCOPE | Evidence accuracy (the plan's motive claim, and what V-06 probes) | Both hosts' `run_queue` tails read statement by statement (`oc_runipd` 3978-4090, `agy_runipd` 3407-3476); eight probes on `queue=["not-a-mapping"]`; `report_run_spec_edits` prints `SPEC CHANGES: could not be computed (AttributeError); the run is starting anyway...`; `report_driver_committed_reviews` carries its own `isinstance(item, Mapping): continue`; `grep` of `.aw/records/backlog/` for the symbol returns only the done `tm5vnx` | **F-02 lists five exit-tail statements and the shared tail has eight**, omitting `report_run_spec_edits` and `report_driver_committed_reviews`, which sit BETWEEN the surfaces the plan discusses. The first DEGRADES on this input rather than crashing, printing a could-not-compute line where a clean queue prints nothing, so a declared spec edit in such a queue goes unreported and no backlog item covers it. V-06 demands a tail probe "in tail order" and would have been satisfied by probing the short list | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-02 rewritten with all eight statements numbered, both omissions named, each probed with its observed behavior, and the degraded line quoted verbatim. V-06 now requires all eight and the verbatim degraded line. New Deferred row for the degradation with `Carrier-Declined` explaining that `cup9r7`'s F-15 already carries the executor obligation to report it, so duplicating it would produce two reports of one gap. The "statements THREE and FOUR" phrase in the disposition-surfaces deferral corrected to THREE and SIX; Under-scope extended to name the unreported spec edit |
| PR-103 | HIGH | IN-SCOPE | G. Plan executability (an instruction whose natural implementation fails) | `f"{'??':02d}"` raises `ValueError: Unknown format code 'd' for object of type 'str'`; the row loop's append builds `"seq": f"{seq:02d}"` and `"pos": f"{pos:02d}"`; the review prototype renders only because its placeholder branch appends pre-formatted strings and `continue`s | **E-03 requires a marker in the `Pos` cell and the cell is formatted `:02d`, so the natural implementation converts the crash instead of removing it.** Assigning the marker to `pos` and falling through to the shared `items_data.append(...)` raises `ValueError` at the same point in the same tail, losing the table just as completely from code that reads as correct. Both obvious escapes are closed - the gate forbids fabricating a number, and the marker cannot be `:02d`-formatted - so the only correct shape is a separate append plus `continue`, which the plan never states | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-20 records the `ValueError` probe, the two formatted cells, and why both escape routes are closed. E-03 now requires the placeholder to carry PRE-FORMATTED `seq`/`pos` strings and to `continue` past the well-formed body, with an explicit prohibition on applying `:02d` to a non-integer; its Expected outcome now names the `ValueError` as a way the item can fail. V-03 requires confirming no `:02d` reaches the marker, pasting the placeholder's own append. Added as the FIFTH silent-failure mode, cross-referenced to the third so the executor sees both routes closed |
| PR-104 | MEDIUM | IN-SCOPE | Evidence accuracy (concurrent-plan census) | `grep -l` for the path over `.aw/records/plans/pending/*.ipd.md` then each hit's `- Scope-Paths:` and `- Status:` read: `35mjqc` reviewed, `4taj2e` reviewed, `it6tpj` reviewed, `zhqt51` reviewed, `entv1d` reviewed, `7sc8fk` to-review; `entv1d` mentions `EXIT_MALFORMED_ENTRY_TOKEN` as a pattern, `7sc8fk` names this plan in its own overlap census | **F-15 says four other pending plans declare this file and there are five, and four of its five statuses are stale.** It omits `7sc8fk` entirely and reports `4taj2e`, `it6tpj` and `entv1d` as `to-review` when all three are now `reviewed`. The row's conclusion (no plan covers this crash, none collides, `4taj2e` constrains test style) survives, but a reader auditing the overlap claim would find the census wrong and discount the conclusion with it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-15 corrected: five declarers enumerated with measured statuses, `7sc8fk` added with its subject, the two plans that mention "malformed" classified as non-colliding with the reason, and the DECLARES-versus-mentions distinction made explicit in the evidence column. The row now tells the executor to re-read the statuses at execution HEAD rather than trust it, since these plans are moving through review concurrently, which is the property that made it stale within a day |
| PR-105 | LOW | IN-SCOPE | Evidence accuracy (carrier statuses) | `aw find plans 0kh97v cup9r7`: both pending; `cup9r7`'s front matter reads `- Status: reviewed`; `aw find backlog fcodik 3z91mq s438xd`: all three `graduated` | **Three places assert the sibling carrier plans are `to-review` and `cup9r7` is now `reviewed`.** The `graduated` carrier-item claims are correct and the conclusion (the work is owned, do not duplicate it) is unaffected, but a stale status in a row whose whole purpose is to prove active ownership invites a reader to re-check the ownership itself | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The `write_report` deferral now says "pending" with the measured value parenthesized and an instruction to re-read; the disposition deferral corrected to `reviewed` with the staleness noted; Under-scope changed from "with `to-review` plans" to "with pending plans". V-06 now requires reporting each carrier's status as read at execution HEAD rather than repeating a value from the plan's prose |
| PR-106 | LOW | UNDER-SCOPE | F. Prevent silent failure (a redundant-edit hazard in an edited branch) | Per-helper probe over every `render_stream` function this renderer calls: `refusal_of_item` -> `None`, `integration_was_refused` -> `False`, `review_integration_was_refused` -> `False`, `format_stranded_work_section` -> `[]`, `_review_lane_branch` -> `None`, each on a non-mapping entry; the first two are called inside the success-branch conjuncts E-05 edits | **The plan names four crashing helpers but never states that five others are ALREADY tolerant**, and two of those five (`refusal_of_item`, `integration_was_refused`) are called from inside the very conjuncts E-05 edits. An executor working that branch will meet them and may add a defensive `isinstance` check, which would be dead code in a function whose every well-formed byte this plan forbids moving, and would enlarge the diff V-05 requires to show exactly the guarded sites | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-22 records all five probes with their return values, explains why the two in-branch ones create the hazard, and says plainly to leave all five alone. E-05 gained a clause stating their tolerance explicitly so it cannot be mistaken for a missing guard, phrased as "this clause exists only so an executor does not mistake their tolerance for a missing guard" |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-102: F-03's count is right and E-05's summary of it is wrong. Should the plan's headline number change, or only E-05's wording? | Only E-05's wording, with the Goal restated to say the count is CONFIRMED and the INSTRUCTION was the defect | Raising the headline count to thirteen (counting the second success tuple as an extra site); leaving the count vague ("a dozen-odd sites"); changing E-05 silently | I first drafted this as a count correction to thirteen and it was wrong: re-reading F-03 shows entries (8) and (9) ALREADY list the two success tuples separately, so twelve was accurate and inflating it would have introduced a false measurement while fixing a real instruction. The count is not decoration - it is the plan's headline argument against the item's single-guard framing, and the gate tells a reviewer to audit the cascade enumeration first - so it must say exactly what was measured. Naming the discrepancy as measured-right/instructed-wrong is also the more useful record, because it tells a future reviewer that a correct findings table does not vindicate an executable step | yes |
| D-2 | PR-103: should E-03 mandate a specific implementation shape for the placeholder row, or just warn about the `:02d` hazard? | Mandate the shape (pre-formatted cells plus `continue`), because it is the only shape that satisfies the plan's other constraints | Warning only and leaving the shape to the executor; relaxing the `Pos`-marker requirement to allow the enumeration index; changing the shared formatting to `f"{pos}"` for every row | A warning alone leaves the executor to derive that both escapes are closed, which is the derivation that failed at authoring. Relaxing the marker requirement is rejected by the gate's third silent-failure mode on measured grounds (`position` is the frozen identity filenames key on) and I will not overturn a measured prohibition to make an implementation easier. Changing the shared formatting would move well-formed bytes, which the plan's central prohibition forbids and which V-05 would catch. That leaves exactly one shape, so naming it is a statement of fact rather than a design imposition | yes |
| D-3 | PR-101: should this plan FIX the `report_run_spec_edits` degradation, since its tail enumeration now names it? | No; record it as Deferred with `Carrier-Declined`, and rely on `cup9r7`'s existing executor obligation to report it | Adding it to this plan's fence; filing a new backlog item for it; leaving it out of the plan entirely | It is in a different module outside `- Scope-Paths:`, and it is a DEGRADATION rather than a lost surface, so it needs its own decision about whether the advisory wrapper should fail louder - a decision this plan's tests would say nothing about. Filing is not mine to do here for the same reason the plan's own OQ-03 declines it, and `cup9r7`'s F-15 already routes the report to the maintainer's turn, so a second obligation would produce two reports of one gap. Leaving it out entirely was rejected because F-02 now names the statement, and an unexplained silent statement in an enumerated tail invites a reader to think it was missed | yes |
| D-4 | Should review add the 300-input malformed sweep and the 96-input byte-identity comparison to the plan as measured findings, or simply require the executor to run their own? | Add both as F-21 and state them in V-05 and Required tests as the floor to meet or beat | Requiring the probes without numbers, as the plan originally did; running them and mentioning the result only in this record | An open-ended "compare over a cross product" instruction is satisfiable by a two-input comparison, and the probe that matters most (the malformed sweep) was not required at all, yet it is the one that would have caught PR-102 - a narrower one provably would not, since the single-entry case passes with one success tuple guarded. Putting concrete counts in the plan converts a probe an executor can under-run into one they must justify under-running. Keeping the numbers only here would hide them from the executor, who is the reader who needs them | yes |
| D-5 | The plan carries three `Owner: opencode` resolved open questions (OQ-01 count-and-render, OQ-02 leave the token unmapped, OQ-03 report-do-not-file). Should review reopen any? | None; all three verified and left resolved | Reopening OQ-02 as a maintainer question about lifecycle vocabulary; reopening OQ-03 to force the two unowned defects to be filed | Each was checked against the evidence it cites rather than accepted. OQ-01's count-and-render is corroborated by the in-source guarantee of one row per matched artifact and by `render_zero_work_notes`' existing conditional skip, and I rendered the mixed table to confirm the box stays rectangular. OQ-02 is settled by direct probe: the token resolves to `unknown` with a diagnostic, styles without raising, is in neither owner enum, and the criterion-A2 assertion is `owner_enum <= mapped_keys` with a docstring forbidding tidying it to an equality, so nothing breaks. OQ-03's reasoning that the two unowned sites are naturally ONE mid-run-surface item is sound, and filing them would presuppose the maintainer's work-kind judgement under the repository's own perceptibility test | yes |
