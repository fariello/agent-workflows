- Id: j08jky
- Status: open
- Blocks-Release: next
- Set: j08jky
- Priority: high
- Work-Kind: bug
- Summary: the non-isolated half of the turn-bounds permission-policy test fails whenever the ambient environment already sets OPENCODE_CONFIG_CONTENT, reddening the suite for an environmental reason

## Workflow history
- 2026-09-22 created (aw backlog): tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped fails whenever the ambient environment already sets OPENCODE_CONFIG_CONTENT, so the suite is red for an environmental reason and every post-merge revalidation in such a turn is a baseline-relative pass rather than a green tree

MEASURED in this worktree on 2026-09-23, both before and after an unrelated change, so it is not caused by that change: a bare `python3 -m pytest` gives `1 failed, 8567 passed, 3 skipped, 2 xfailed` before and `1 failed, 8600 passed` after, the single failure being the same test each time.

WHAT IT ASSERTS AND WHY IT FAILS. The case pins that a NON-isolated turn gets NO permission-denial policy, because such a turn works in the main checkout where external-directory denial would refuse its ordinary work (R4.1). It asserts this as `policy_key not in main_env`, i.e. that the key is ABSENT from the built environment. But the key is `OPENCODE_CONFIG_CONTENT`, which the AMBIENT environment of an agent turn already carries, and the builder inherits it. So the assertion is really 'this variable is absent from the process environment', which is a fact about the machine rather than about the code under test.

WHY IT MATTERS BEYOND ONE RED TEST. It makes the repository suite red for an environmental reason, and a red suite is what the post-merge revalidation gate measures. After `tgyfs2` that no longer strands lanes (the verdict is relative to the pre-work baseline, so a pre-existing failure is subtracted), but it means integrations in this environment routinely pass a RED tree on the no-regression path and emit the accompanying warning, which is strictly worse for an operator than a green tree. It also means every executor in such an environment must attribute this failure by hand.

THE FIX SHOULD ASSERT WHAT THE TEST MEANS. The property is 'the builder does not ADD a denial policy for a non-isolated turn', not 'the variable is absent from the environment'. Comparing the built env against the ambient env for that key (or clearing it in the fixture) states the real property and is immune to the ambient value. Do NOT simply delete the assertion: the isolation-scoped half of this pair is a real safety property.

WHERE: tests/test_turn_bounds.py:310, TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped.

Found while executing plan `tgyfs2` (revalbase 01).
