- Id: cfgj8s
- Status: graduated
- Graduated-To: envhermet
- Blocks-Release: next
- Set: turnbounds
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds isolation-scope assertion fails when the runner's own OPENCODE_CONFIG_CONTENT is in the ambient env

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to the envhermet Set (orchestrator uvwqvz, child 01 heglfv for the DEFECT, child 02 fwgq2u for the missing GUARD). This item is one of TWENTY-THREE open filings of a single non-hermetic assertion: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reads the AMBIENT OPENCODE_CONFIG_CONTENT, which run_opencode always sets for a turn. MEASURED at HEAD 22cf67d9: bare '144 passed', and with the variable set '1 failed, 143 passed' on 'assert OPENCODE_CONFIG_CONTENT not in {...}'. So the file is green for a human and red for every lane agent, which is why so many agents filed it independently. THE FIX MUST NOT RELAX THE ASSERTION: R4.1 genuinely requires a non-isolated turn to receive NO denial policy (it works in the main checkout where external-directory denial would refuse its ordinary work), so heglfv fixes the SEAM the test reads, not the guarantee. A session-wide conftest scrub is explicitly REJECTED, because that mechanism is what made rolevac 8i0xa7's role guard vacuous and repeating it would be a known self-inflicted defect. NOT CLOSED AS A DUPLICATE HERE: consolidating these twenty-three needs human judgement (uvwqvz OQ-01), since the filings are not identical and at least two attribute the failure to AW_EXECUTION_ROLE, a different and already-scrubbed cause.
- 2026-09-21 created (aw backlog): filed from lane run run-20260922T003657Z-1022108 while executing y9vpvv

MEASURED IN A LANE RUN 2026-09-21 (run-20260922T003657Z-1022108, item y9vpvv), on a tree whose only
changes were to the commit verb and the managed contract, so the failure is unrelated to that work.

THE FAILURE. `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`
asserts that a NON-isolated turn's environment carries NO `OPENCODE_CONFIG_CONTENT` denial policy
(R4.1: a non-isolated turn works in the main checkout, where external-directory denial would refuse
its ordinary work). It fails with:

    assert 'OPENCODE_CONFIG_CONTENT' not in {...}

THE CAUSE IS AMBIENT ENVIRONMENT BLEED, not a defect in the policy code. The test builds the
non-isolated turn's env by INHERITING the current process environment, and an OpenCode-hosted agent
is itself launched with `OPENCODE_CONFIG_CONTENT` set. So the key the assertion forbids is present
before the code under test does anything.

PROOF BY ISOLATION, both directions, same tree and same HEAD:

    $ python3 -m pytest                      # ambient var present
    1 failed, 8016 passed, 3 skipped, 2 xfailed

    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts="" -k "isolation_scoped"
    1 passed, 42 deselected in 0.30s

WHY THIS IS USER-PERCEPTIBLE AND THEREFORE A BUG RATHER THAN A CHORE. Every agent turn run under
OpenCode inside this repository sees a RED suite that is not red, on a test whose whole purpose is to
police a safety property. That costs a human (or an agent) time diagnosing a non-defect on every run,
and worse, it TRAINS readers to dismiss a failure in exactly the isolation-policy area where a real
regression most needs to be noticed. Backlog `gjadwm` records that class of harm: a check that fires
on correct behavior teaches people to ignore it.

THE FIX SHAPE, not prescribed. The test should construct the non-isolated env from a CONTROLLED base
rather than inheriting the ambient one (or explicitly drop the keys it then asserts absent), so the
assertion measures what the code PUT THERE instead of what the host happened to export. Check the
sibling cases in the same file for the same inheritance, since the isolated-turn half may be
passing for the same accidental reason.
