- Id: zgndje
- Status: graduated
- Graduated-To: envhermet
- Blocks-Release: next
- Set: zgndje
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds isolation-scoped policy test fails when the suite inherits OPENCODE_CONFIG_CONTENT from a lane turn

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to the envhermet Set (orchestrator uvwqvz, child 01 heglfv for the DEFECT, child 02 fwgq2u for the missing GUARD). This item is one of TWENTY-THREE open filings of a single non-hermetic assertion: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reads the AMBIENT OPENCODE_CONFIG_CONTENT, which run_opencode always sets for a turn. MEASURED at HEAD 22cf67d9: bare '144 passed', and with the variable set '1 failed, 143 passed' on 'assert OPENCODE_CONFIG_CONTENT not in {...}'. So the file is green for a human and red for every lane agent, which is why so many agents filed it independently. THE FIX MUST NOT RELAX THE ASSERTION: R4.1 genuinely requires a non-isolated turn to receive NO denial policy (it works in the main checkout where external-directory denial would refuse its ordinary work), so heglfv fixes the SEAM the test reads, not the guarantee. A session-wide conftest scrub is explicitly REJECTED, because that mechanism is what made rolevac 8i0xa7's role guard vacuous and repeating it would be a known self-inflicted defect. NOT CLOSED AS A DUPLICATE HERE: consolidating these twenty-three needs human judgement (uvwqvz OQ-01), since the filings are not identical and at least two attribute the failure to AW_EXECUTION_ROLE, a different and already-scrubbed cause.
- 2026-09-20 created (aw backlog): test_turn_bounds isolation-scoped policy test fails when the suite inherits OPENCODE_CONFIG_CONTENT from a lane turn

MEASURED 2026-09-20 in lane n5qca5 at HEAD 340c9174.

`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` asserts that a NON-isolated turn carries NO `OPENCODE_CONFIG_CONTENT` denial policy (lane_containment.OPENCODE_RUNTIME_CONFIG_ENV), because a turn working in the main checkout would be refused its ordinary work by an external-directory denial (R4.1).

The assertion reads the env the driver would build, which INHERITS os.environ. When the suite itself runs INSIDE a managed lane turn, the runner has already exported OPENCODE_CONFIG_CONTENT for that turn, so the variable is present in os.environ, flows into the non-isolated env under test, and the assertion fails.

PROOF, environment alone, no code change:

    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q
    43 passed in 4.84s
    $ python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q
    1 failed, 42 passed in 4.73s

WHY THIS IS USER-PERCEPTIBLE: every agent turn run by `aw oc run` that executes the bare suite sees a red run it did not cause, so each such turn spends time diagnosing a phantom regression and each must justify the failure in its report. It also weakens the empty-delta criterion the execution contract relies on, since a real regression in this file would be masked by an expected failure.

LIKELY FIX: the test should control the variable rather than inherit it, e.g. build the env under a `mock.patch.dict(os.environ, ..., clear=...)` that removes OPENCODE_RUNTIME_CONFIG_ENV before driving, so the assertion measures what the DRIVER adds rather than what the ambient session already had. Whether the PRODUCTION path should also strip an inherited policy for a non-isolated turn is a separate and more interesting question: if it does not, a non-isolated turn launched from inside a lane session would inherit a denial policy that R4.1 says it must not have, which would be a real defect rather than a test artifact. Investigate that before fixing only the test.
