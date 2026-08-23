<!-- Durable turn-2 skeptical audit prompt for spec-to-IPD authoring. Fed by tools/agy_run.py. Version-controlled on purpose. -->
Perform a skeptical completeness and conformance audit of the authored Implementation Plan Document:

`{IPD_PATH}`

Against its controlling specification document:

`{SPEC_PATH}`

Procedure:

1. Verification against specification: trace every requirement, design invariant, and acceptance criterion in `{SPEC_PATH}` to ensure it is explicitly mapped to one or more `E-*` checklist items in the IPD.
2. Check for missing gaps: identify any unaddressed edge cases, error states, backward compatibility requirements, or missing tests.
3. Check for out-of-scope additions: verify that the IPD does not introduce gold-plating or scope creep beyond the specification's mandates.
4. Structural compliance check: run `aw ipd lint --phase author --agent {IPD_PATH}` and paste the exact runner output. Verify that heading order, frontmatter fields, E/V 1:1 bijection, and state tags conform strictly.
5. Falsifiability audit: verify that every `V-*` validation item requires falsifiable evidence rather than subjective assertion.
6. Fix any discovered gaps, missing requirements, or structural lint errors in place. Write target-repo files via `run_command` ONLY; never call `write_to_file` on a target-repo path (it is sandboxed to the brain dir and will be rejected).

Report back with:
- Verdict: `CONFORMING`, `CONFORMING AFTER CORRECTIONS`, or `NOT CONFORMING`
- Specification requirement coverage matrix (every spec section -> mapped E-items)
- Structural linter output (`aw ipd lint`)
- Fixes applied to the IPD (if any)
- Remaining open questions or ambiguities (if any)
