- Id: yfbzqn
- Status: done
- Set: yfbzqn
- Priority: low
- Work-Kind: chore
- Summary: plan 3dki3o's V-06 requires test_no_call_site_was_rewritten to expect 38/36 save_state call sites but the table sums to 45/43 at HEAD, so an approved plan's validation criterion cites a stale number an executor cannot satisfy

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: moot: 3dki3o executed
- 2026-09-17 created (aw backlog): plan 3dki3o's V-06 requires test_no_call_site_was_rewritten to expect 38/36 save_state call sites but the table sums to 45/43 at HEAD, so an approved plan's validation criterion cites a stale number an executor cannot satisfy

FOUND BY: rununify Order 11 (`3dki3o`) while satisfying its own V-06(c).

WHAT THE PLAN REQUIRES: V-06(c) and Required tests item 6 both say
`tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten` 'must still expect 38/36
for `save_state` and 2/2 for `print_status`'.

WHAT IS ACTUALLY THERE at HEAD 761edad3. The test does not hold a single 38/36 literal. It holds a
`PREMOVE_CALL_SITES` baseline of 32/30 for `save_state` plus FIVE separately-named addition tables
(`ADDED_CALL_SITES`, `CLEAN_BASE_GUARD_CALL_SITES`, `INTEGRATION_LADDER_CALL_SITES`,
`LANE_BACKLOG_CLOSE_CALL_SITES`, `REVIEW_SWEEP_LANE_CALL_SITES`), each naming the plan that added its
callers. Summed:

    oc_runipd  save_state   45
    agy_runipd save_state   43
    oc_runipd  print_status  2
    agy_runipd print_status  2

So `print_status` 2/2 is exactly as the plan says, and the `save_state` figure has moved from the
38/36 the plan recorded to 45/43, because later plans legitimately added callers and NAMED each one,
which is precisely what that table's documented rule asks for.

WHY THIS IS WORTH A RECORD RATHER THAN A SILENT PASS. The test passes at this HEAD, so nothing is
broken in the code. The defect is in the VALIDATION CRITERION: an executor reading V-06(c) literally
cannot satisfy it, and the two honest responses are to report the discrepancy (what `3dki3o` did) or
to edit the number, which the table's own rule forbids ('If a count moves and you cannot name the new
call site, the wrapper ruling has been undone ... the correct action is to fix the code, NOT to add a
number here'). ANY sibling plan citing a raw call-site total has the same exposure, because the total
is designed to grow.

SUGGESTED FIX: where a plan needs to assert this guard, cite the TEST NAME and require it green,
rather than transcribing a total that is expected to move.
