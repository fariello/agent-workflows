- Id: 1pgrii
- Status: open
- Blocks-Release: next
- Set: 1pgrii
- Priority: medium
- Work-Kind: bug
- Summary: The defect-report bare-except guard scans to end of file, so it goes red on unrelated code

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing skn8uk: tests/test_defect_report.py::ValidatorTests::test_no_bare_except_was_introduced_around_the_new_code took section = src[start:] (7150 lines, to EOF) rather than bounding at the next banner (709 lines), and went red for an unrelated suppression added 5400 lines later by 894d7924. Bounded in place while executing skn8uk with a control test; this item records the class of defect for the other guards written the same way.
