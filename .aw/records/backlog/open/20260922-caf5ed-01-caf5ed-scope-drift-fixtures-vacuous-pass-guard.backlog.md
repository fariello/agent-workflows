- Id: caf5ed
- Status: open
- Set: caf5ed
- Priority: low
- Work-Kind: chore
- Summary: Six scope-drift test arrangements dirty the MAIN checkout and would pass vacuously under lane-scoped measurement; the pattern has no guard

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan wmnmei (rcptstale-01): the fixtures were repaired in place, but nothing prevents the next one from being written the old way.

FOUND 2026-09-22 while implementing rcptstale wmnmei.

check.scope-drift now measures the plan's ISOLATED LANE and is SILENT for a plan with no lane. Six existing test arrangements asserted the advisory FIRES while creating their out-of-scope change in the MAIN checkout, so under the new rule each went silent for a reason unrelated to what it was testing, and every one of them would have passed VACUOUSLY had they been assertions of silence instead.

THE SIX, all repaired in the same change by allocating a real lane via worktree_lease.allocate_worktree and placing the change inside it:
  tests/test_check_engine_receipt_liveness.py (_arrange plus the three hand-built (c) cases)
  tests/test_event_derived_lifecycle.py (TestScopeDrift._repo, all four table rows)
  tests/test_phase4_hooks.py (_mk_repo plus two arrangements)
  tests/test_finalize_scope_ownership.py (the broad-time-window assertion)

WHY THIS IS WORTH A CARRIER RATHER THAN JUST A FIX: the danger is structural and survives the repair. A scope-drift test that forgets the lane does not fail loudly, it silently stops measuring, and three of the four files above contain docstrings explicitly warning that their silent rows must not become vacuous (test_event_derived_lifecycle's TestScopeDrift says so in as many words). The repair restores the intent; nothing enforces it for the NEXT test.

CANDIDATE DIRECTIONS (none asserted): (1) a shared fixture helper in one place that every scope-drift test must use to arrange an out-of-scope change, so the lane cannot be forgotten; (2) a meta-test asserting that each scope-drift test file allocates a lane; or (3) a positive-control convention, where any test asserting SILENCE also asserts a sibling arrangement that FIRES, which is the pattern test_phase4_hooks' SCOPE_CASES table already uses deliberately.
