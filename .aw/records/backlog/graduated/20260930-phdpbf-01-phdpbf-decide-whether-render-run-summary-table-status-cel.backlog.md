- Id: phdpbf
- Status: graduated
- Graduated-To: phdpbf
- Set: phdpbf
- Priority: low
- Work-Kind: followup
- Summary: Decide whether render_run_summary_table Status cell should render Section 5 lifecycle glyph

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: qhpov0
- 2026-09-30 created (aw backlog): Decide whether render_run_summary_table Status cell should render Section 5 lifecycle glyph

Filed from plan 4taj2e (finding F-11, OQ-01). Sibling surfaces (attention.py, run_viewer.py, ipd_lint.py, status_set.py, cli.py) render format_lifecycle_marker into status columns; render_run_summary_table renders the styled word only. If aligned in the future, visible_width handling implemented in 4taj2e ensures zero-width variation selectors align properly.
