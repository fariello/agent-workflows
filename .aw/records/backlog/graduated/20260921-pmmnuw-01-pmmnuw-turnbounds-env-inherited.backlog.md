- Id: pmmnuw
- Status: graduated
- Graduated-To: envhermet
- Blocks-Release: next
- Set: pmmnuw
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds isolation-policy test fails whenever the running agent turn exports OPENCODE_CONFIG_CONTENT

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to the envhermet Set (orchestrator uvwqvz, child 01 heglfv for the DEFECT, child 02 fwgq2u for the missing GUARD). This item is one of TWENTY-THREE open filings of a single non-hermetic assertion: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reads the AMBIENT OPENCODE_CONFIG_CONTENT, which run_opencode always sets for a turn. MEASURED at HEAD 22cf67d9: bare '144 passed', and with the variable set '1 failed, 143 passed' on 'assert OPENCODE_CONFIG_CONTENT not in {...}'. So the file is green for a human and red for every lane agent, which is why so many agents filed it independently. THE FIX MUST NOT RELAX THE ASSERTION: R4.1 genuinely requires a non-isolated turn to receive NO denial policy (it works in the main checkout where external-directory denial would refuse its ordinary work), so heglfv fixes the SEAM the test reads, not the guarantee. A session-wide conftest scrub is explicitly REJECTED, because that mechanism is what made rolevac 8i0xa7's role guard vacuous and repeating it would be a known self-inflicted defect. NOT CLOSED AS A DUPLICATE HERE: consolidating these twenty-three needs human judgement (uvwqvz OQ-01), since the filings are not identical and at least two attribute the failure to AW_EXECUTION_ROLE, a different and already-scrubbed cause.
- 2026-09-21 created (aw backlog): test_turn_bounds isolation-policy test fails whenever the running agent turn exports OPENCODE_CONFIG_CONTENT

MEASURED 2026-09-21 in lane 4y95tp, at HEAD f763be8c, before any edit: a bare `python3 -m pytest` reports `1 failed, 8022 passed, 3 skipped, 2 xfailed`, the failure being
`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`.

THE TEST IS ASSERTING A TRUE PROPERTY AND STILL FAILING, which is what makes this worth filing rather
than dismissing. It drives the lane-containment environment builder twice (isolated and not) and
requires that a NON-isolated turn carry NO denial policy:

    assert policy_key not in main_env, (
        "a non-isolated turn must get NO denial policy; it works in the main checkout "
        "where external-directory denial would refuse its ordinary work (R4.1)")

`policy_key` is `lane_containment.OPENCODE_RUNTIME_CONFIG_ENV` == `OPENCODE_CONFIG_CONTENT`. The
builder does not SET it for a non-isolated turn, correctly; the variable is present because the AGENT
TURN RUNNING THE SUITE exports it, and the test reads the inherited process environment rather than a
constructed-from-empty one.

PROVEN BY ISOLATING THE VARIABLE, nothing else changed:

    $ python3 -m pytest tests/test_turn_bounds.py::...::test_the_permission_policy_by_contrast_IS_isolation_scoped -o addopts=""
    1 failed in 1.00s
    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py::...::test_the_permission_policy_by_contrast_IS_isolation_scoped -o addopts=""
    1 passed in 0.57s

WHY IT MATTERS BEYOND ONE RED LINE. Every agent lane in this repository runs the suite as its own
validation evidence, and an OpenCode-driven lane exports this variable by construction, so this test
fails for EVERY such lane regardless of what that lane changed. Each executor then has to diagnose it
from scratch and decide whether it is their regression - I did, costing a full extra suite run - and
the real hazard is the other direction: a genuine future regression in this same test is
indistinguishable from the environmental failure, so it will be waved off.

SUGGESTED FIX, not prescribed: have the test construct the parent environment it passes to the builder
explicitly (or pop the key from a copy) rather than inheriting `os.environ`, so the assertion measures
what the builder DID rather than what the harness happened to export. The property under test is
unchanged by that; only the input becomes controlled, which is how the sibling isolated-case assertion
already behaves in effect.

NOT FIXED HERE: `tests/test_turn_bounds.py` is outside plan 4y95tp's declared Scope-Paths (the
completion module, the CLI, and `tests/test_completion.py`).
