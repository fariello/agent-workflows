# Check P: Proofread

Apply the "Proofreading procedure" section of `../../technical-writing/technical-writing.md` and its numbered requirements, including requirement 12 (diagrams).

## Structural Preservation Constraints (Section 6.1)

The runner checks structural preservation before and after check P. You must NOT change:
- Any front-matter metadata value.
- The list or order of H2 headings.
- The set of `E-*` and `V-*` ids, or their checkbox states.
- Any `Execution state` value.
- The set of field names under any `E-*` or `V-*` item.
- The `Status:` or `Blocking:` value of an existing open question.

The runner refuses any edit that changes any of the above, restores the plan to its pre-check content, and re-asks once.

Proofreading may add open questions only through the review record's Issues table below (Section 6.1); check S5 moves material ones into the plan.

## Code Citations (Section 11.1)

Write citations in the forms of spec Section 11.1:
- Python code: `path::Name`, `path::Class.method`, `path::outer.inner`, `path::CONSTANT`.
- Markdown: `path#Heading text`, with the exact heading text.
- Quoted text: `` `path` "text" `` (backticked path, one space, text in double quotes; unique single-line occurrence).
- Records: `<id6>`, `<id6> R-3`, `E-04`, `D153`, each with a descriptive name.
- Generated files: cite the generator (`path::Symbol`), not the generated file.

A line number may follow an anchor as a hint (e.g. `path::Symbol:line`), but a line number alone is only a hint, not a citation.

## Review Record Subsection

In the typed review record (`.aw/records/reviews/<...>.review.md`), record material changes and unresolved ambiguities in the current round's `### Proofreading` subsection as two tables:

### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|

### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|

Every recommendation strength in the Issues table must be stated as one of `very weak`, `weak`, `medium`, `strong`, or `very strong`.
