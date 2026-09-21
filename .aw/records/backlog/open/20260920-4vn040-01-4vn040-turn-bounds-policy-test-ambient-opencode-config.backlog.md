- Id: 4vn040
- Status: open
- Blocks-Release: next
- Set: 4vn040
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds isolation-scoped permission policy test fails inside a runner lane because OPENCODE_CONFIG_CONTENT is ambient

## Workflow history
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
