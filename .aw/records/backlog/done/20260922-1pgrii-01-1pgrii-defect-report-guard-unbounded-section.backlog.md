- Id: 1pgrii
- Status: done
- Graduated-To: secbound
- Blocks-Release: next
- Set: 1pgrii
- Priority: medium
- Work-Kind: bug
- Summary: The defect-report bare-except guard scans to end of file, so it goes red on unrelated code

## Workflow history
- 2026-10-02 done (aw backlog): closed by aw oc run: IPD tr8ugt executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260929-secbound-01-78rxzc-give-the-suite-one-bounded-section-extractor-that-refuses-in.ipd.md, .aw/records/plans/executed/20260929-secbound-02-tr8ugt-convert-the-measured-unbounded-section-sites-onto-the-bounde.ipd.md); evidence .aw/records/plans/executed/20260929-secbound-01-78rxzc-give-the-suite-one-bounded-section-extractor-that-refuses-in.ipd.md
- 2026-09-29 set (aw backlog): graduated by run run-20260928T235941Z-1396311: 78rxzc, tr8ugt
- 2026-09-22 created (aw backlog): Found while executing skn8uk: tests/test_defect_report.py::ValidatorTests::test_no_bare_except_was_introduced_around_the_new_code took section = src[start:] (7150 lines, to EOF) rather than bounding at the next banner (709 lines), and went red for an unrelated suppression added 5400 lines later by 894d7924. Bounded in place while executing skn8uk with a control test; this item records the class of defect for the other guards written the same way.
