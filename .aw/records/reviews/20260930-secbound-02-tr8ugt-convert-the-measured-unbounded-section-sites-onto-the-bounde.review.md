# Review findings: plan tr8ugt

- Subject-Id: tr8ugt
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-D01 (HIGH, fixed), PR-D02 (MEDIUM, fixed), PR-D03 (MEDIUM, fixed), PR-D04 (LOW, fixed), PR-D05 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `d1eb0ffd`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author` reported `conforming` BEFORE semantic review and again at `review-finalize`
after revision, including after a new E-08/V-08 pair was added. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply.

THE DECLARED DEPENDENCY IS REAL AND SELF-ANNOUNCING, VERIFIED BOTH WAYS. `- Item-Dependencies:
executed:78rxzc` is load-bearing exactly as the gate claims: `tests/support.py` exposes none of `section`,
`final_section`, `section_lines` or `SectionBoundError` today (all four `hasattr` False), so every E-item
would fail at import. And the runner refuses rather than running: `oc_runipd.edge_satisfied` returns
`(False, "executed:78rxzc: external target 78rxzc is 'reviewed' (directory 'pending'), needs one of
['executed'] (it is not in this run, so it cannot become satisfied here)")`. Order 01 is `reviewed` /
`go-pending-approval`, awaiting human approval.

THE THREE LIVE DEFECTS REPRODUCE EXACTLY, DRIVEN AGAINST REAL PRODUCERS RATHER THAN FIXTURES:

- F-01 to the token. Driving the real `backlog.run_new` with `--body "## Suggested work\n\n- bound the
  guard\n- add a control test\n"` and then the real `backlog.run_set` yields FOUR history bullets against
  an assertion of 2, and the two spurious entries are the body's own list items, exactly as claimed. I
  also confirmed the proposed fix: the record writes `## Workflow history` BEFORE `## Suggested work`, so
  `support.section(text, "## Workflow history", "\n## ")` returns precisely the 2 real records.
- F-02 to the number. `build_index_md` emits only `## Needs addressing (todo)` and `## Most recent`, so
  the tail is accidentally terminal; driving the real renderer at `limit=2` gives 2 bullets today, 3 with
  one appended section, and 2 when bounded.
- F-03 to the character, including the part most plans would overstate. Bounded `[### D130., ### D131.)`
  is 2,170 chars and `content[d130_start:]` is 73,887. I checked each of the five fixture topics
  individually: `physical .aw/`, `durable` and `runtime` are all present in the text AFTER D130 while
  `project.json` and `local.json` are not, so the 3-of-5 claim is right and is not a rounding of
  "most of them".

F-04's `total:` terminator, F-07's `esac` safety, F-06's direction, and F-08/F-09's exclusions all hold
too. OQ-01 in particular is resolved on a premise I could verify: `render_disposition_summary` appends its
`  total: ...` line unconditionally as the last element, its docstring states why, bounding there gives the
same counted total of 4, and the `total:` line does NOT itself match the test's `^  (\S+) \((\d+)\)`
counting regex, so bounding cannot perturb the sum.

THE ONE FINDING THAT WAS A GAP RATHER THAN AN INACCURACY.

PR-D01. `tests/test_orchestrator_retirement.py` is in `- Scope-Paths:` and appears NOWHERE else in the
plan: no E-item, no finding, no exclusion row. It holds a genuine in-class site,
`dest_text.split("## Detailed Implementation Checklist (TODO)")[1].split("## Validation")[0]` feeding
`assertIn(LC.ROLLUP_SUPERSEDED_STATEMENT, checklist_section)`. That `[0]` head's fallback is the whole
remaining text, so renaming the `## Validation` heading makes the "checklist section" absorb the validation
section and the assertion can then be satisfied by a `V-` item rather than by the checklist body it exists
to check. Demonstrated on a synthetic record: the segment grows from 24 to 144 chars and a statement
present ONLY in the validation section flips the assertion False to True. This is two failures at once: an
unnoticed instance of precisely the class the plan exists to close, and a declared-but-unmodified path that
would have forced a `--scope-ack` at finalize for work the plan had forgotten. Closed with a new E-08 and
V-08, which required bumping `- Highest E allocated:` to 08; lint re-confirmed conforming afterwards.

THREE MEASUREMENT CORRECTIONS. These matter because this plan's own gate instructs the executor to
re-measure every figure and report differences, so a wrong authored number would have produced a
false-discrepancy report, and one of them also carried a wrong VERDICT.

PR-D02 is the consequential one. E-05(a) claimed a renamed Section 6 widens the table scan "from 22 rows
to 118 (measured)", which framed the site as a latent defect. Re-driven, `_parse_spec_section5`'s PARSED
row count is 20 bounded and 20 to end of file: the widened scan picks up ZERO extra rows, because the
function's own three filters discard every later table line in the 1063-line spec. 22 and 118 are raw
PIPE-LINE counts, 96 of which are filtered out. So the conversion buys a refusal if the terminator ever
vanishes, which is worth having, and fixes nothing today. Given how carefully this plan labels F-07's two
sites as "correct today, uniformity only", leaving E-05(a) overclaimed would have been inconsistent with
its own standard.

PR-D03. E-06(c) justifies `anchored=False` by saying the marker "matches no line start in the original
text". Measured, the character immediately before `## conflict details` in the lowercased subject is `\n`,
so it IS at a line start and an anchored match on the lowercased text succeeds. The real obstacle is CASE:
the heading renders as `## Conflict Details`. `anchored=False` may be unnecessary. This needed fixing
because the plan asks the executor to encode this reason at the site, and a comment stating a false reason
outlives the diff.

PR-D04. E-03 states the D130 fallback as 71,763 chars in two places while F-03, V-03 and the gate all say
73,887. Measured: 73,887.

PR-D05. A batch of smaller items. F-06's corpus ratio has moved from 33-of-1806 to 98-of-2693 and the
`_records` figure from 69-of-1751 to 79-of-1938, both in the direction that STRENGTHENS the plan's
conclusion. The `Required tests` section had no pre-change reference for the declared files; I ran all
eleven together (306 passed) and recorded it as a reference rather than a bar, since E-01 must raise the
count. The narrative sections ("Six must change NOTHING", the proposed-changes list, the Scope line's "3
head sites") all needed reconciling with the added E-08, which is the sweep this workflow requires after a
correction.

WHAT IS STRONG, AND IT IS MOST OF THE PLAN. The decision to group E-items by WHAT THE CONVERSION PROVES
rather than by file is the right call and is argued explicitly; it is what let me check each group against
the right evidence, and it is why V-01's demand for a failing-then-passing case is more than ceremony. The
plan is unusually honest about sites that are CORRECT TODAY (F-07, and the whole "no site is converted for
tidiness without a stated verdict" section), and it excludes `tests/test_defect_report.py` for the right
reason with a comment so a future sweep cannot break it, which is a genuinely good instinct. The gate's
instruction to re-measure every authored figure is what makes the three numeric corrections above
low-cost rather than damaging, and F-09's separation of field parses from section reads keeps the plan from
sprawling into a rename sweep. All eleven declared test files are green at review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-D01 | HIGH | UNDER-SCOPE | Rubric D (anti-regression), G (executability); scope-fence integrity | plan `- Scope-Paths:` versus a whole-file search for `test_orchestrator_retirement`; the site read in that file; synthetic-record demonstration at review | `tests/test_orchestrator_retirement.py` is DECLARED and named by no E-item, finding, or exclusion row, while carrying a real in-class site: `split("## Detailed Implementation Checklist (TODO)")[1].split("## Validation")[0]` feeding `assertIn(ROLLUP_SUPERSEDED_STATEMENT, checklist_section)`. Renaming the `## Validation` heading makes the segment absorb the validation section, so the assertion is satisfiable from a `V-` item instead of the checklist body (demonstrated: 24 -> 144 chars, assertion False -> True). Two defects: an unnoticed instance of the class this plan exists to close, and a declared-but-unmodified path that would have forced a `--scope-ack` at finalize for forgotten work. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | Recorded as F-14. New E-08 converts the site with the fallback deleted; new V-08 demands an unchanged per-file count, a synthetic-record refusal demonstration, and confirmation that no real record under `.aw/records/` was edited. `- Highest E allocated:` bumped to 08; the proposed-changes list, the Scope line (3 -> 4 section-heading heads), the grouping rationale, E-07's `Depends on`, the Scope check, and OQ-02's completeness claim all swept to match. Lint re-confirmed conforming. |
| PR-D02 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy; Rubric D (do not report a non-defect as one) | plan E-05(a) and V-05; `_parse_spec_section5` re-driven on the real spec | E-05(a) claims a renamed Section 6 widens the table scan "from 22 rows to 118 (measured)", framing the site as a latent defect. Measured, the PARSED row count is 20 bounded and 20 to EOF: the function's own three filters discard every later table line, so the widened scan gains ZERO rows. 22 and 118 are raw PIPE-LINE counts (96 filtered out). The site has no present miscount, which contradicts the plan's own standard of labelling correct sites as uniformity conversions. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-10. E-05(a) now states the verdict as uniformity plus an explicit terminator assertion, with the corrected parsed-row figures and the explanation of where 22/118 came from. V-05 demands PARSED-row counts, names the correction, and instructs the executor to report loudly if the two counts ever differ (which would mean the site had become a live miscount). The gate's figure list updated. |
| PR-D03 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy; Rubric F (a comment must not state a false reason) | plan E-06(c) and V-06; `runner_shared.merge_conflict_question` driven with the test's own `adj_detail` | E-06(c) justifies `anchored=False` because the marker "matches no line start in the original text". Measured, the character before `## conflict details` in the lowercased subject is `\n`, so it IS at a line start and an anchored match on the lowercased text succeeds. The real obstacle is CASE: the heading renders `## Conflict Details`. The plan asks the executor to encode this reason at the site, and a false reason in a comment outlives the diff. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-11 with the driven measurement (head 271 of 2308 chars, `unknown` absent from head and present in tail). E-06(c) states the real obstacle, notes `anchored=False` may be unnecessary, and requires the executor to re-derive from the pasted heading line rather than adopt either story. V-06 forbids restating the false reason and requires the heading pasted verbatim. |
| PR-D04 | LOW | IN-SCOPE | Step 1 evidence accuracy | plan E-03 (twice) versus F-03, V-03 and the gate; `DECISIONS.md` measured | The plan contradicts itself on the D130 fallback length: E-03 says 71,763 chars in two places while F-03, V-03 and the gate say 73,887. Measured 73,887. Since the gate tells the executor to re-measure and report differences, the wrong value would have produced a false-discrepancy report. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-12. Both E-03 occurrences corrected to 73,887 with a note that the other three statements were right. The 3-of-5 topic claim was re-verified per topic and is exactly correct. |
| PR-D05 | LOW | IN-SCOPE | Rubric E (testing evidence); internal consistency | F-06 and E-01's `_records` note re-swept; `Required tests` section; narrative sections versus the added E-08 | Four small items: F-06's anchoring corpus has grown 33-of-1806 -> 98-of-2693 and E-01's `_records` figure 69-of-1751 -> 79-of-1938 (both strengthening the plan's conclusion); the validation section carried no pre-change reference for the eleven declared files; and the narrative sections still described a 7-item plan after E-08 was added. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-13. F-06's row carries the re-sweep; the gate's figure list is updated and now names the three corrected figures as the ones to trust; the validation section records the review's own 306-passed reference explicitly as a reference and not a bar, plus the re-measured 3387-passed suite; every narrative section swept to match E-08. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | An in-class site sits in a DECLARED path with no E-item. Add an E-item, or drop the path from `Scope-Paths`? | ADD E-08 and convert it. | Dropping the path: rejected, the site is a real false-green of exactly the class this plan exists to close, and dropping it would leave a correct-looking unbounded precedent in a file the plan had already read, which is the specific harm the plan's own Scope check argues against. Leaving the path declared and unconverted: rejected, it would force a `--scope-ack` at finalize for forgotten work and record a scope reconciliation that misrepresents an oversight as a decision. | The site read in `tests/test_orchestrator_retirement.py`; a whole-file search showing the path appears ONLY in `- Scope-Paths:`; the synthetic-record demonstration (segment 24 -> 144 chars, assertion False -> True); `aw ipd lint` conforming after the E-08/V-08 addition and the `Highest E allocated` bump. | yes |
| D-2 | E-05(a)'s figures are wrong. Correct the numbers only, or also change the site's stated verdict? | CHANGE THE VERDICT TOO, to uniformity plus an explicit terminator assertion. | Correcting 22/118 to 20/20 and leaving the "would widen the scan" framing: rejected, because with the corrected numbers there IS no widening, so the framing would be false with true numbers attached, which is harder for a reader to catch than a plainly wrong figure. Dropping the conversion: rejected, the refusal it adds is still valuable if the terminator ever vanishes, and the plan's uniformity rationale already covers exactly this case. | `_parse_spec_section5` re-driven: parsed rows 20 bounded and 20 to EOF; 6-cell rows in `[## 6., EOF)` = 0; pipe lines 22 and 118, the difference explained by the function's own three filters. | yes |
| D-3 | E-06(c) gives a false reason for `anchored=False`. Substitute the correct reason, or require the executor to re-derive? | REQUIRE RE-DERIVATION, while recording what review measured. | Simply writing "use `anchored=False` because of case": rejected, because the measurement suggests `anchored=False` may not be needed at all (anchoring works fine on the lowercased subject), and prescribing a mechanism I had not proven necessary would repeat the original error in the opposite direction. Leaving the false reason: rejected, the plan asks for it to be encoded at the site. | Driven `merge_conflict_question`: char before marker is `\n`; anchored match succeeds on the lowercased text and fails case-sensitively on the original; heading is `## Conflict Details`; head 271 of 2308 chars with `unknown` absent from head and present in tail. | yes |

No `Reversible: no` decision was taken in this round. OQ-01 and OQ-02 are both `resolved` and
`Blocking: no`, so no open question holds the plan under the 2026-09-10 ruling; OQ-02's resolution was
corrected in place because F-14 falsified its "every site has a verdict" completeness claim. No finding
was left `OPEN` or `DEFERRED`, so no escalation to a `- Blocking: yes` question is required. The plan
remains correctly gated on its Order 01 dependency, which is a sequencing fact rather than a review
finding.
