- Id: 1bxw6o
- Status: open
- Set: 1bxw6o
- Priority: medium
- Work-Kind: followup
- Summary: Restore r2i1b1's deleted diagnostics guards (TestNoStatusAllowlist, TestNoFieldNameMismatch) or decide deliberately that the suite trim retires them

## Workflow history
- 2026-09-28 created (aw backlog): Restore r2i1b1's deleted diagnostics guards (TestNoStatusAllowlist, TestNoFieldNameMismatch) or decide deliberately that the suite trim retires them

MEASURED 2026-09-28 while authoring plan `5o1jye` from backlog item `fvsyqk`. Executed plan `orchprobe` `r2i1b1` built two guards over `render_stream`s diagnostics block and recorded in its own E-07 why: `TestNoStatusAllowlist` pinned that no hardcoded status allowlist gates the block, and `TestNoFieldNameMismatch` pinned "the defect class F-4 actually found: a branch whose rendering condition reads a field the producing code never writes". Its V-07 evidence records the guard FINDING A REAL THIRD DEFECT on first run before any mutation, which is the strongest argument for it existing.

BOTH GUARDS ARE GONE. `tests/test_refusal_surfacing.py` was deleted in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24); `rg` for either class name across `tests/` returns nothing at HEAD. The timing matters: `git merge-base --is-ancestor 19313eed 6b94a4d9` confirms the deletion landed ONE DAY BEFORE `statusvocab` `cyamvi` (2026-09-25) broke that very block by leaving a status equality pointing at a token the runner stopped writing. The suite stayed green through a change that silenced an operator-facing surface, which is exactly the outcome the deleted guards existed to prevent.

THE DECISION OWED IS DELIBERATE, NOT AUTOMATIC. The trim was a repository-wide reduction with its own rationale and test-count budget, and `80db6750` ("delete 366 tests that pinned code structure instead of behaviour") suggests a principled objection to structural/AST-derived guards specifically, which is what `TestNoFieldNameMismatch` was. So the question is NOT simply "restore the file": it is whether this class of guard earns its place under the current budget, and if not, what behavioral pin replaces it. Plan `5o1jye` adds behavioral coverage for the ONE arm its own defect touches (`tests/test_dependency_block_reporting.py`), which narrows but does not close this question: the field-mismatch class spans every special-cased status in the block, not just the dependency arm.

Filed `followup` because no user-perceptible defect is measured in this item itself; the measured defects are carried by `fvsyqk` (fixed by `5o1jye`) and by `cxrpwv` (the unaudited dead-status-key class). This item holds the test-policy decision those two exposed.
