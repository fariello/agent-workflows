- Id: 089bq4
- Status: graduated
- Graduated-To: 089bq4
- Blocks-Release: next
- Set: 089bq4
- Priority: low
- Work-Kind: bug
- Summary: Spec 25kzda 4.2 claims tests/test_run_evidence_completion.py enforces byte equality on the finding-code table, but that file was deleted

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: h65phz
- 2026-09-29 created (aw backlog): Filed while authoring plan 00pirb (graduating backlog b7tlsh), which measured this as finding F-10 and deliberately kept it out of scope. THE DEFECT: spec 25kzda Section 4.2's 'NOTE ON TRANSCRIBING THIS TABLE' asserts that 'run_evidence.RUN_FINDING_CODES transcribes the inspects and pass_criterion cells VERBATIM, and tests/test_run_evidence_completion.py asserts byte equality, so editing a cell here is a code change'. MEASURED in lane b7tlsh: that test file does NOT exist under tests/, and git log shows it was deleted in commit 19313eed ('test: trim test suite from 9,136 to under 2,000 tests', 1722 deletions). No test in tests/ references RUN_FINDING_CODES at all (grep -rln RUN_FINDING_CODES tests/ is empty). So the spec tells an editor that a guard will catch a divergence between its table and the shipped vocabulary, and nothing will. USER-PERCEPTIBLE: an author who edits a 4.2 cell trusting the stated guard silently desynchronizes the spec from run_evidence's shipped operator messages, which are the exact strings an operator sees on a failure. WHY IT WAS NOT FIXED IN 00pirb: that plan amends the commit-gateway enforcement claims in 2.1 and 5.2 and adding a 4.2 table guard is a different concern needing its own decision, namely whether to RESTORE a byte-equality test (the suite was deliberately trimmed, so restoring must respect that trim's intent and the no-code-pinning rule) or to CORRECT the spec sentence to stop promising a guard that no longer exists.
