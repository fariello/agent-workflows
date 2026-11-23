- Id: napot2
- Status: open
- Set: napot2
- Work-Kind: bug
- Priority: low
- Summary: Prevent ipd_lint continuation loop from stopping on more-indented key-colon bullets under Observed evidence
- Short-Description: Prevent ipd_lint continuation loop from stopping on more-indented key-colon bullets under Observed evidence
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-23 created (aw backlog): Prevent ipd_lint continuation loop from stopping on more-indented key-colon bullets under Observed evidence

## Context

In `agent_workflows/ipd_lint.py`, the leaf-subfield continuation loop for `_CONTINUATION_SUBFIELDS` (`Observed evidence` and `Execution note`) breaks whenever a subsequent line matches `_SUBFIELD_RE = re.compile(r"^\s+- ([A-Za-z][A-Za-z /-]*?):\s?(.*)$")`. Because `_SUBFIELD_RE` matches any leading whitespace (`^\s+`) without comparing indentation depth against the parent sub-field bullet, a more-indented child bullet whose label before `:` contains only letters, spaces, slashes, or hyphens (for example `    - State directory ensured: ...` under `  - Observed evidence:`) terminates the continuation loop immediately. When `- Observed evidence:` has no text on its own line and starts with such a nested bullet, `ipd_lint` parses `Observed evidence` as empty and refuses pre-transition lint with `IPD-S402` and `IPD-S404`. Observed during execution of `jd7874` V-05.

## Acceptance

1. Update the `_CONTINUATION_SUBFIELDS` loop in `agent_workflows/ipd_lint.py` so a line matching `_SUBFIELD_RE` ends the continuation only when its indentation is less than or equal to the parent sub-field bullet's indentation (a sibling sub-field such as `  - Result: pass`), not when it is a more-indented nested bullet inside the evidence block.
2. Add behavioral tests in `tests/test_ipd_lint.py` verifying that a multi-line `Observed evidence:` block starting with a 4-space nested `Key: value` bullet parses as non-empty and passes `pre-transition` lint, while a sibling 2-space `- Result: pass` bullet still terminates the block cleanly.
