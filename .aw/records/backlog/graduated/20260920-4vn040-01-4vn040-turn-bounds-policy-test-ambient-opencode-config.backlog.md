- Id: 4vn040
- Status: graduated
- Graduated-To: envhermet
- Blocks-Release: next
- Set: 4vn040
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds isolation-scoped permission policy test fails inside a runner lane because OPENCODE_CONFIG_CONTENT is ambient

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to the envhermet Set (orchestrator uvwqvz, child 01 heglfv for the DEFECT, child 02 fwgq2u for the missing GUARD). This item is one of TWENTY-THREE open filings of a single non-hermetic assertion: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reads the AMBIENT OPENCODE_CONFIG_CONTENT, which run_opencode always sets for a turn. MEASURED at HEAD 22cf67d9: bare '144 passed', and with the variable set '1 failed, 143 passed' on 'assert OPENCODE_CONFIG_CONTENT not in {...}'. So the file is green for a human and red for every lane agent, which is why so many agents filed it independently. THE FIX MUST NOT RELAX THE ASSERTION: R4.1 genuinely requires a non-isolated turn to receive NO denial policy (it works in the main checkout where external-directory denial would refuse its ordinary work), so heglfv fixes the SEAM the test reads, not the guarantee. A session-wide conftest scrub is explicitly REJECTED, because that mechanism is what made rolevac 8i0xa7's role guard vacuous and repeating it would be a known self-inflicted defect. NOT CLOSED AS A DUPLICATE HERE: consolidating these twenty-three needs human judgement (uvwqvz OQ-01), since the filings are not identical and at least two attribute the failure to AW_EXECUTION_ROLE, a different and already-scrubbed cause.
- 2026-09-20 created (aw backlog): Filed from zx9dkq execution; measured environmental failure, gated on no-new-failures rather than fixed in an out-of-scope plan.

MEASURED 2026-09-20 during execution of plan `zx9dkq` in an isolated `aw oc run` lane at HEAD `e87eaca4`, with NO code change of mine in play (the baseline run, taken before any edit, already showed it).

WHAT IS WRONG. A bare `python3 -m pytest` in a managed worker lane reports `1 failed, 7626 passed`, the failure being `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`. That test asserts a NON-isolated turn gets no permission-denial policy (`assert policy_key not in main_env`, `tests/test_turn_bounds.py:310`), but `OPENCODE_CONFIG_CONTENT` is present in the ambient environment of an OpenCode lane turn, so the constructed `main_env` inherits it and the assertion fails.

PROOF IT IS ENVIRONMENTAL, NOT A CODE DEFECT: same tree, same commit, single test.
- as-is: `1 failed in 2.45s`
- `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest ...`: `1 passed in 2.43s`
And `env | grep -c OPENCODE_CONFIG_CONTENT` = 1 in the lane.

WHY IT MATTERS. It is the same class of defect as backlog `1uq1cu`: the damage is to EVIDENCE, not to shipped behavior. An agent measuring its own before/after suite counts sees the phantom failure in both, so the delta cancels and the check passes by luck; an agent that reads the 1 as real either excuses a genuine regression or reports one that does not exist, and then pastes that count into a `V-*` `Observed evidence` block as fact. `conftest.py:78` already scrubs the sibling `AW_EXECUTION_ROLE` marking at the session boundary for exactly this reason.

LIKELY FIX, for the owner of the runner contract to judge: scrub or neutralize `OPENCODE_CONFIG_CONTENT` at the same session boundary in `conftest.py`, OR have the test build `main_env` from an explicit dict rather than inheriting the ambient environment. DO NOT relax the assertion: it encodes the real isolation contract (R4.1), and weakening it would hide a genuine future regression in which a non-isolated turn gains a denial policy.

NOT FIXED IN `zx9dkq` because that plan declares `tests/test_run_analytics_spa.py` as its only Scope-Path; fixing this there would have been an undeclared widening into the runner isolation contract. That plan gated on NO NEW failures in the same tree instead (before: 1 failed / 7626 passed; after: 1 failed / 7626 passed, same test).
