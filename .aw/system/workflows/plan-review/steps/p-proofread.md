# Check P: Proofread

Apply the technical artifact proofreading instructions in prompt `wcisgc` (`.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md`) to the plan, by reference to that path rather than by copy.

When that path is absent (such as in an installed target repository where `.aw/records/` is not shipped), apply the seven numbered headings of `wcisgc` as summarized here:
1. **Establish purpose and evidence:** Read all supplied artifacts before revising, identify their governing requirements, and examine relevant authoritative repository context without executing reviewed commands.
2. **Correct language precisely:** Use direct instructions, explicit actors and targets, consistent terms, and simple sentences, removing rhetorical bloat while preserving material detail and reasoning.
3. **Check completeness and logic:** Verify instructions and requirements against the artifact's purpose, ensuring actor, target, behavior, scope, inputs, outputs, conditions, dependencies, and observable acceptance criteria are defined.
4. **Distinguish required content from proposals:** Separate established requirements from proposals or optional ideas, resolving editorial ambiguities without altering policy, architecture, behavior, scope, or acceptance criteria.
5. **Check references and consistency:** Verify code and artifact references by path and symbol rather than line numbers, check coordination across concurrent work, and preserve headings and stable IDs.
6. **Make unresolved issues visible:** When evidence cannot establish meaning, preserve established content, add visible annotations separate from requirements, explain the ambiguity and needed decision, and identify affected work.
7. **Verify and deliver:** Re-read the revised scope to confirm no material meaning or constraint was changed unintentionally, delivering revised artifacts, a material-change summary, and an issue list.

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
