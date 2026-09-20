- Id: nos070
- Status: open
- Set: nos070
- Priority: medium
- Work-Kind: followup
- Summary: A tabulated test suite makes named-test and test-count evidence requirements in already-approved IPDs unsatisfiable as written

## Workflow history
- 2026-09-20 created (aw backlog): A tabulated test suite makes named-test and test-count evidence requirements in already-approved IPDs unsatisfiable as written

Found 2026-09-20 while executing IPD i4c0c3, which was reviewed on 2026-09-08.

WHAT IS WRONG. Approved IPDs commonly write validation evidence requirements that name individual test FUNCTIONS and assert a COLLECTED COUNT, e.g. i4c0c3's V-03 ('paste the passing results of `test_hand_edited_status_executed_without_receipt_refused` and `test_hand_edit_outside_a_merge_still_refused`') and its V-04 ('showing a total of 31 (27 existing plus 4 new); a count below 31 means tests were lost'). The repository is concurrently converting suites to TABLE-DRIVEN form: commit 75b90271 ('test: tabulate eleven more suites (385 -> 160 tests)') turned those two named functions into ROWS of two `SITUATIONS`/`MERGE_DECISIONS` tables and collapsed the file from 27 collected tests to 6.

The consequence is that an approved plan's evidence contract can become literally unsatisfiable between review and execution, through a change that IMPROVED the tests and removed nothing. The executing agent then faces a bad menu: report the V-item unverifiable, or silently substitute different evidence and leave a plan whose pasted evidence does not match its own stated requirement. Neither is good, and the second is how evidence quality erodes quietly.

This is NOT a defect in the tabulation, and not in either plan. It is a missing convention at the seam between them.

WHAT TO SOLVE FOR.
  1. AUTHORING GUIDANCE: a V-item should demand the BEHAVIOUR pinned and the mechanism that pins it, not a collected-test count, since a count is an artifact of test organization rather than of coverage. Naming a test function is still useful as a pointer; treating its name as the contract is what breaks.
  2. A SUBSTITUTION RULE: when a named test has provably become a table row, state the successor row by its case string and paste its individual verdict. Row-level verdicts are obtainable (a small driver over the table data prints PASS/FAIL per row) but a passing `subTest` is SILENT under both pytest and `unittest -v`, so nothing in the toolchain surfaces them today.
  3. POSSIBLE TOOLING: a verb that enumerates table rows with verdicts would make row-level evidence a first-class, repeatable paste instead of a per-plan ad-hoc script. Worth considering, not obviously worth building yet.

EVIDENCE. i4c0c3's V-03/V-04 observed-evidence blocks record the substitution actually made, with the row counts read off the tables (29 rows at HEAD, 33 after) and each merge row's verdict printed by name.
