- Id: pzbcto
- Status: graduated
- Graduated-To: envhermet
- Blocks-Release: next
- Set: pzbcto
- Priority: low
- Work-Kind: bug
- Summary: test_turn_bounds isolation-scoped policy test fails when the suite runs under an OpenCode agent

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to the envhermet Set (orchestrator uvwqvz, child 01 heglfv for the DEFECT, child 02 fwgq2u for the missing GUARD). This item is one of TWENTY-THREE open filings of a single non-hermetic assertion: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reads the AMBIENT OPENCODE_CONFIG_CONTENT, which run_opencode always sets for a turn. MEASURED at HEAD 22cf67d9: bare '144 passed', and with the variable set '1 failed, 143 passed' on 'assert OPENCODE_CONFIG_CONTENT not in {...}'. So the file is green for a human and red for every lane agent, which is why so many agents filed it independently. THE FIX MUST NOT RELAX THE ASSERTION: R4.1 genuinely requires a non-isolated turn to receive NO denial policy (it works in the main checkout where external-directory denial would refuse its ordinary work), so heglfv fixes the SEAM the test reads, not the guarantee. A session-wide conftest scrub is explicitly REJECTED, because that mechanism is what made rolevac 8i0xa7's role guard vacuous and repeating it would be a known self-inflicted defect. NOT CLOSED AS A DUPLICATE HERE: consolidating these twenty-three needs human judgement (uvwqvz OQ-01), since the filings are not identical and at least two attribute the failure to AW_EXECUTION_ROLE, a different and already-scrubbed cause.
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
