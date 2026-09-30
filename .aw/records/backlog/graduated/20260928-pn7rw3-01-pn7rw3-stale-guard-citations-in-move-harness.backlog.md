- Id: pn7rw3
- Status: graduated
- Graduated-To: pn7rw3
- Set: pn7rw3
- Priority: low
- Work-Kind: chore
- Summary: test_runner_shared.py's SUPERSEDED_SINCE_MOVE comment cites two deleted guard files as shipped guards

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: x3zno3
- 2026-09-28 note (aw backlog): Maintainer ruling: Code-pinning guards (refork tables/module ownership pins) were deleted in the suite trim and will not be restored. Stale comments should simply remove references to them without seeking to restore code pins.
- 2026-09-28 created (aw backlog): test_runner_shared.py's SUPERSEDED_SINCE_MOVE comment cites two deleted guard files as shipped guards

Found while authoring plan t0ovw6 (backlog xw4rb7), measured at HEAD 98e3ea9a.

WHAT IS WRONG. The `should_color` exemption note inside `tests/test_runner_shared.py`'s `SUPERSEDED_SINCE_MOVE` comment block justifies keeping a delegating `def` by naming "three shipped guards" that assert `runner_shared` DEFINES the symbol. TWO of the three do not exist:

* `tests/test_runner_refork_guard.py` (cited for its `Owned("should_color", "runner_shared", BOTH)` row) was DELETED in 19313eed;
* `tests/test_rununify_run_queue.py` (cited for its `RESOLVES_IN_RUNNER_SHARED` table) was DELETED in the same commit.

Only the third, `test_exactly_one_definition_package_wide`, might survive, and `rg -n test_exactly_one_definition_package_wide tests/` returns ONLY this comment: no test of that name exists either.

WHY IT MATTERS. The comment's whole job is to stop a future author replacing the delegating `def` with an import. Its stated reason is that three tests would fail; measured, zero would. So the protection is prose, and the next author who checks the citation finds nothing and may reasonably conclude the `def` is free to remove.

WHY IT IS FILED SEPARATELY. Plan t0ovw6 edits this same file and could correct the citation incidentally, but the comment's SUBJECT is `should_color`, a symbol that plan does not touch, and deciding what (if anything) now guards the single-definition property of `should_color` is a real question rather than a text fix.

FILED chore, NOT bug: no user-perceptible behavior is wrong. The cost is to a future maintainer, not to an operator.
