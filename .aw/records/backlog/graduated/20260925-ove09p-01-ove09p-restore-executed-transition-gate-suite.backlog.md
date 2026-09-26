- Id: ove09p
- Status: graduated
- Graduated-To: restorecov
- Set: ove09p
- Priority: medium
- Work-Kind: followup
- Summary: restore the deleted 1267-line tests/test_executed_transition_gate.py suite (6 tests, still passing) covering the hook end-to-end, merge stages and pre-commit registration

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set restorecov (commit 2c7068ca).
- 2026-09-25 created (aw backlog): Found at review of plan kecxnb: the path kecxnb creates for four unit cases was a 1267-line suite deleted in 19313eed. Recovered and run at review: 6 passed in 3.65s against today's hook, and 6 passed again with kecxnb's proposed _has_executed_status monkeypatched in. Its coverage (end-to-end refusal verdicts, merge-aware in-tree evidence, both git stages, pre-commit config registration) is not replaced by kecxnb's narrow unit cases.
