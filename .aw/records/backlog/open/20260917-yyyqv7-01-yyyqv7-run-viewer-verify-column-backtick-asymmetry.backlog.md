- Id: yyyqv7
- Status: open
- Set: yyyqv7
- Priority: medium
- Work-Kind: bug
- Summary: run_viewer does not strip backticks for the verification column, so a backticked verify cell loses the [verified] badge

## Workflow history
- 2026-09-17 created (aw backlog): Found during rununify child 04 (tx6q0h). run_viewer.load_run_summary strips backticks for id6/setid/action/session (agent_workflows/run_viewer.py:1014-1038) but takes the verification column verbatim (cols[5].strip(), :1024), then run_viewer.py:1370 compares it to the bare string 'verified'. The Antigravity runner emitted a backticked cell, so no agy run ever rendered the [verified] badge. tx6q0h REPAIRED THE PRODUCER (both hosts now emit it bare, asserted end to end). This item is about the CONSUMER's latent asymmetry, which is still there: any future producer that backticks that cell silently loses the badge again, and the column is the only one of five the parser treats differently. Consider stripping backticks for column 5 too, or comparing case/markup-insensitively.
