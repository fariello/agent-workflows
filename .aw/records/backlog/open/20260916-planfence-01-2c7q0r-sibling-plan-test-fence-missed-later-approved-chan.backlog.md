- Id: 2c7q0r
- Status: open
- Set: planfence
- Priority: low
- Work-Kind: followup
- Summary: 3i0aaz left tests/test_dirty_base_gate.py asserting the isolated dirty-base refusal that approved sibling d7qoxv was already signed off to remove

## Workflow history
- 2026-09-16 created (aw backlog): Found while executing dirtygates Order 01 (d7qoxv); a process observation, not a code bug.

WHAT HAPPENED. Plan `3i0aaz` (dirtybase Order 01) executed on 2026-09-14 and created `tests/test_dirty_base_gate.py`. Five of its tests assert that a dirty ISOLATED base REFUSES. Plan `d7qoxv` (dirtygates Order 01) was ALREADY approved at that point, with the explicit scope of removing that exact isolated refusal, and its blocking OQ-03 had been resolved by the maintainer to run `3i0aaz` first and `d7qoxv` second.

So the ordering was decided and honored, but the NEW test file the first plan wrote encoded the behavior the second plan was approved to delete, and that file is not in the second plan's `Scope-Paths` (it could not be: it did not exist when that plan was authored or reviewed). The executor of `d7qoxv` therefore had to edit an undeclared path to keep the suite green, and justify it as an out-of-scope edit.

WHY THIS IS WORTH RECORDING. The two plans' collision over the OTHER test file (`tests/test_lane_clean_base.py`) was found at review, escalated as blocking OQ-03, and settled by the maintainer. This one was structurally identical and was NOT caught, because review can only fence files that exist. The generalizable gap: when plan A executes while an approved plan B is known to change the same behavior, any NEW test A writes for that behavior inherits the same conflict, and nothing currently prompts A's executor to check B's scope before pinning the behavior.

CHEAP MITIGATIONS to consider: when a plan creates a test asserting behavior an approved sibling is signed off to change, note the sibling in the test's docstring so the next executor finds the authorization instead of rediscovering the conflict; or have `d7qoxv`-style plans declare a directory rather than a file when the sibling is expected to add coverage. NO CODE CHANGE IS PROPOSED HERE and nothing is broken now: the tests were retargeted and the suite is green (7321 passed).
