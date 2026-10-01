- Id: p5qx91
- Status: graduated
- Graduated-To: p5qx91
- Set: p5qx91
- Priority: medium
- Work-Kind: chore
- Summary: Approved spec uonrjg cites two color-axis test pins that commit 19313eed deleted, so the single-originating-definition guarantee is unenforced

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053059Z-3200713: nw088c
- 2026-09-28 note (aw backlog): Maintainer ruling: We test outcomes and functionality, never code structure or text in a script. Zero tests that pin code. Do NOT restore single-originating-definition AST/text pins; testing on color-axis should only verify functional rendering outcomes across terminal surfaces.
- 2026-09-28 created (aw backlog): Approved spec uonrjg cites two color-axis test pins that commit 19313eed deleted, so the single-originating-definition guarantee is unenforced

Approved spec uonrjg references two test pins for the color axis that were deleted in commit 19313eed.

Maintainer ruling (2026-09-28): We test outcomes and functionality, never code structure or text in a script. Zero tests that pin code. Do NOT restore single-originating-definition AST/source pins; any color testing must focus strictly on observable outcomes (e.g. proper styling and ANSI output across terminal and non-terminal environments).
