- Id: mepbmp
- Status: done
- Graduated-To: envhermet
- Blocks-Release: next
- Set: mepbmp
- Priority: high
- Work-Kind: bug
- Summary: test_turn_bounds asserts a non-isolated turn carries NO permission policy, but run_opencode now always sets OPENCODE_CONFIG_CONTENT, so 1 node fails on a clean tree

## Workflow history
- 2026-09-24 set (aw backlog): closed by aw oc run: IPD heglfv executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260923-envhermet-01-heglfv-make-the-turn-bounds-policy-assertions-read-the-constructed.ipd.md); evidence .aw/records/plans/executed/20260923-envhermet-01-heglfv-make-the-turn-bounds-policy-assertions-read-the-constructed.ipd.md
- 2026-09-23 graduated (aw set): Graduated to the envhermet Set (orchestrator uvwqvz, child 01 heglfv for the DEFECT, child 02 fwgq2u for the missing GUARD). This item is one of TWENTY-THREE open filings of a single non-hermetic assertion: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reads the AMBIENT OPENCODE_CONFIG_CONTENT, which run_opencode always sets for a turn. MEASURED at HEAD 22cf67d9: bare '144 passed', and with the variable set '1 failed, 143 passed' on 'assert OPENCODE_CONFIG_CONTENT not in {...}'. So the file is green for a human and red for every lane agent, which is why so many agents filed it independently. THE FIX MUST NOT RELAX THE ASSERTION: R4.1 genuinely requires a non-isolated turn to receive NO denial policy (it works in the main checkout where external-directory denial would refuse its ordinary work), so heglfv fixes the SEAM the test reads, not the guarantee. A session-wide conftest scrub is explicitly REJECTED, because that mechanism is what made rolevac 8i0xa7's role guard vacuous and repeating it would be a known self-inflicted defect. NOT CLOSED AS A DUPLICATE HERE: consolidating these twenty-three needs human judgement (uvwqvz OQ-01), since the filings are not identical and at least two attribute the failure to AW_EXECUTION_ROLE, a different and already-scrubbed cause.
- 2026-09-20 created (aw backlog): test_turn_bounds asserts a non-isolated turn carries NO permission policy, but run_opencode now always sets OPENCODE_CONFIG_CONTENT, so 1 node fails on a clean tree

One node in `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn` fails on a CLEAN checkout at
main (`5211f722`), with no working-tree changes at all:

    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped

THE ASSERTION AND WHAT IT MEASURES. The test drives `oc_runipd.run_opencode` twice, once with a lane
worktree and once with `work_dir=None`, and asserts the runtime-config env var is present for the
isolated turn and ABSENT for the non-isolated one (tests/test_turn_bounds.py:310):

    assert policy_key not in main_env, (
        "a non-isolated turn must get NO denial policy; it works in the main checkout "
        "where external-directory denial would refuse its ordinary work (R4.1)"
    )
    E  AssertionError: assert 'OPENCODE_CONFIG_CONTENT' not in {...}

The isolated half PASSES (policy present, `external_directory: deny`, `question: deny`,
`AW_EXECUTION_ROLE: worker`); only the ABSENCE half fails, so `OPENCODE_CONFIG_CONTENT` is now set on
the non-isolated path too.

WHY THIS NEEDS A HUMAN RULING RATHER THAN A SILENT TEST EDIT, which is why it is filed instead of fixed.
Two readings are possible and they differ in what SHIPS, not merely in what the test says. Either the
runner regressed and a non-isolated turn is now being handed an external-directory denial it must not
have (the test is right and the behavior is the bug, and R4.1's stated reason is that denial would refuse
a main-checkout turn's ordinary work), or the runtime config legitimately grew a second purpose beyond
the denial policy so its mere PRESENCE is no longer evidence of denial (the behavior is right and the
test is asserting on the wrong signal, and it should assert on the policy's CONTENT instead). Relaxing
the assertion without deciding which would destroy the only guard on an isolation-scoped denial.

Found while executing plan `udgilu`; unrelated to that plan's scope (lifecycle_style).
