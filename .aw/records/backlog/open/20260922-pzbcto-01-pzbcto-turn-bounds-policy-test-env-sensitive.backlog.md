- Id: pzbcto
- Status: open
- Blocks-Release: next
- Set: pzbcto
- Priority: low
- Work-Kind: bug
- Summary: test_turn_bounds isolation-scoped policy test fails when the suite runs under an OpenCode agent

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan fduoj4 (runrecon-02).

MEASURED 2026-09-22 in an isolated lane worktree, on UNMODIFIED code before any edit of plan fduoj4 (that plan's baseline measurement).

WHAT HAPPENS. `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` asserts that a NON-isolated turn receives no denial policy:

    assert policy_key not in main_env, (
        'a non-isolated turn must get NO denial policy; it works in the main checkout '
        'where external-directory denial would refuse its ordinary work (R4.1)')

It fails with `assert 'OPENCODE_CONFIG_CONTENT' not in {...}`. The variable is present because the SUITE ITSELF is running inside an OpenCode agent session that exports it, and the env the test builds inherits the ambient environment rather than a controlled one.

WHY THIS IS A DEFECT AND NOT JUST AN ENVIRONMENT QUIRK. The property under test is real and worth pinning: R4.1 says an external-directory denial must be scoped to isolated turns, because applying it to a main-checkout turn would refuse that turn's ordinary work. But the test cannot distinguish 'the product added the policy' from 'the harness inherited the variable', so in exactly the environment where the toolkit is most used (an agent session) it reports a failure that says nothing about the product. A test that is red for an irrelevant reason trains readers to ignore it, which costs the R4.1 guarantee its guard.

USER-PERCEPTIBLE IMPACT: any agent running this repository's own suite inside an OpenCode session sees a failing test and must spend a round trip establishing that it is not theirs. Measured cost in this run: one full baseline suite run plus a targeted re-run to confirm.

LIKELY FIX. Build the comparison env from an explicit base (or pop the key) rather than from `os.environ`, so the assertion is about what the code under test ADDS. Do not simply delete the assertion: the isolation-scoping half is the property R4.1 actually needs.

NOT A REGRESSION FROM ANY PLAN IN FLIGHT: reproduced with a clean tree at HEAD 27a446d4.
