- Id: 7fzqop
- Status: graduated
- Graduated-To: 7fzqop
- Set: 7fzqop
- Priority: low
- Work-Kind: followup
- Summary: Document the table-driven (tabulated) test convention: row shape, the why column, and when to tabulate

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053059Z-3200713: prj0vm
- 2026-09-29 created (aw backlog): Document the table-driven (tabulated) test convention: row shape, the why column, and when to tabulate

Split out of nos070 while authoring plans vtup6x and t5txjk.

The repository has converted many suites to TABLE-DRIVEN form and the convention is real and consistent: a module- or class-level table of tuples shaped (case, <inputs...>, expected, needles, forbidden, why), the case string FIRST as a human-readable prose id, and a trailing 'why' column quoted back in the failure message as 'this row exists because: <why>'. Commit 75b90271 ('test: tabulate eleven more suites (385 -> 160 tests)') states the method in its message: 'clusters differing only in DATA become one table whose rows each carry the rule they encode and which reports every failing row at once. What was a CLASS per mode is now a COLUMN'.

THE CONVENTION IS UNDOCUMENTED. Measured 2026-09-29: 'tabulat', 'table-driven' and 'subtest' appear nowhere in GUIDING_PRINCIPLES.md, CONTRIBUTING.md, AGENTS.md, ARCHITECTURE.md or docs/. It exists purely as a code idiom plus one commit message, so a new author has to infer the row shape by reading tests, and a reviewer has no cited rule to hold a new table to.

WHAT TO WRITE DOWN: the row shape and the case-first rule; the 'why' column and why it is not optional (it is what makes a failing row self-explaining); when tabulating is right (clusters differing only in data) and when it is NOT (the 75b90271 message records that migration tests were deliberately left un-merged, for rollback order, idempotence pairs, consent transcripts, and every assertRaises); and the rule that a row's failure must be raised INSIDE the subTest context or the row's per-row verdict is unobtainable (see nos070 and plan t5txjk).

NOT A DEFECT IN THE TABULATION. This item is documentation of an existing good practice.
