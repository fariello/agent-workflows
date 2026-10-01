- Id: nzqj6m
- Status: open
- Set: nzqj6m
- Priority: low
- Work-Kind: chore
- Summary: Sweep the uonrjg color-axis criteria and renderers for other dangling test citations and unconverted lifecycle surfaces

## Workflow history
- 2026-09-30 created (aw backlog): Sweep the uonrjg color-axis criteria and renderers for other dangling test citations and unconverted lifecycle surfaces

RAISED BY plan nw088c (backlog p5qx91), which deliberately fixed one criterion's cell and left the rest.

WHAT nw088c COVERED. The depth cell of the 256/16/none ladder (a live user-visible defect where a pinned 'none' still produced 256-color ANSI), plus the three dangling test citations the p5qx91 item names: uonrjg Section 9.3's claim that 'tests/test_term.py asserts the single-originating-definition property', and the two tests/test_term.py::OneOriginatingDefinitionTests citations inside agent_workflows/term.py docstrings. Both cited classes were deleted in commit 19313eed and will not be restored (maintainer ruling, 2026-09-28).

WHAT IT DID NOT COVER, and why a sweep is a separate job. Commit 19313eed deleted a large volume of tests, so other criteria of this release-gating approved spec may cite coverage that no longer exists, and other renderers may remain unconverted. nw088c measured and excluded: the glyph table, the authored 16-color palette (R9.3a.3 / A12b), the width policy (Section 9.4), and the consumer conversion requirement (R10.3 / A17). Each needs its own per-criterion judgement about whether the cited coverage exists, whether the behavior is actually correct, and what the conforming replacement is - which is why bundling them into a one-line bug fix was rejected.

THE RULE ANY SUCH WORK MUST FOLLOW. Restore no AST/source/text pins (GUIDING_PRINCIPLES P16; the p5qx91 ruling for this axis specifically). Where a criterion's cited coverage is gone, re-cover the OUTCOME by asserting rendered output across terminal surfaces, or correct the citation to say plainly that no guard exists. Note the one narrow P16 exception that already applies here: tests/test_lifecycle_style.py legitimately parses this spec's own Section 5 table, because there the spec is the artifact under test rather than production source.

SUGGESTED FIRST STEP, cheap and mechanical: for each of A1..A21, extract every tests/ path and test class it cites and check existence, then triage only the ones that dangle.
