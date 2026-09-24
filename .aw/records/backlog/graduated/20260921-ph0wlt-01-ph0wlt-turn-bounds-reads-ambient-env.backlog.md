- Id: ph0wlt
- Status: graduated
- Graduated-To: envhermet
- Blocks-Release: next
- Set: ph0wlt
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds reads the ambient OPENCODE_CONFIG_CONTENT, so it fails inside an opencode-driven turn

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to the envhermet Set (orchestrator uvwqvz, child 01 heglfv for the DEFECT, child 02 fwgq2u for the missing GUARD). This item is one of TWENTY-THREE open filings of a single non-hermetic assertion: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reads the AMBIENT OPENCODE_CONFIG_CONTENT, which run_opencode always sets for a turn. MEASURED at HEAD 22cf67d9: bare '144 passed', and with the variable set '1 failed, 143 passed' on 'assert OPENCODE_CONFIG_CONTENT not in {...}'. So the file is green for a human and red for every lane agent, which is why so many agents filed it independently. THE FIX MUST NOT RELAX THE ASSERTION: R4.1 genuinely requires a non-isolated turn to receive NO denial policy (it works in the main checkout where external-directory denial would refuse its ordinary work), so heglfv fixes the SEAM the test reads, not the guarantee. A session-wide conftest scrub is explicitly REJECTED, because that mechanism is what made rolevac 8i0xa7's role guard vacuous and repeating it would be a known self-inflicted defect. NOT CLOSED AS A DUPLICATE HERE: consolidating these twenty-three needs human judgement (uvwqvz OQ-01), since the filings are not identical and at least two attribute the failure to AW_EXECUTION_ROLE, a different and already-scrubbed cause.
- 2026-09-21 created (aw backlog): Filed by the i1hlgx execution turn, in whose environment it fails.

MEASURED 2026-09-21 during plan i1hlgx's bare-suite runs.

WHAT IS WRONG. `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` asserts that a NON-isolated turn's computed environment carries NO `OPENCODE_CONFIG_CONTENT` denial policy. The assertion inspects an environment that INHERITS the ambient one, so when the suite itself runs inside an opencode-driven turn (where that variable is already exported) the key is present and the test fails, having found the harness's own variable rather than anything the code under test added.

EVIDENCE.

    $ env | grep -c OPENCODE_CONFIG_CONTENT
    1
    $ python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q
    1 failed
    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q
    43 passed

The failure message names the leak directly: `assert 'OPENCODE_CONFIG_CONTENT' not in {...}`.

WHY IT IS A BUG. It is a FALSE RED in exactly the situation the repository's own contract makes load-bearing: an agent executing a plan must run the bare suite and compare failing node ids against a baseline. A failure that appears only when an agent runs the suite, and never when a human does, forces every such agent to investigate and then argue the failure is environmental, which is both a recurring cost and an invitation to wave away a real failure as 'probably the known env one'. It also asserts the negative of a condition the test does not control, which is the classic shape of an order- and environment-dependent test.

WHERE. `tests/test_turn_bounds.py:310`, in the non-isolated control branch of `test_the_permission_policy_by_contrast_IS_isolation_scoped`.

LIKELY FIX. Make the control case deterministic rather than ambient: clear the key from the base environment the helper starts from (or patch `os.environ` for the test), so the assertion measures what the code ADDED rather than what the harness already had. The behavior being pinned (R4.1, the policy is isolation-scoped) is correct and worth keeping; only the measurement is contaminated.

NOT CAUSED BY i1hlgx, whose change touches `agent_workflows/run_cli.py` only; this node id was failing identically in that plan's before-baseline.
