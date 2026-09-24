- Id: 7p08pw
- Status: graduated
- Graduated-To: envhermet
- Blocks-Release: next
- Set: 7p08pw
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds' isolation-scoped policy test fails when the runner's own OPENCODE_CONFIG_CONTENT is inherited from the ambient env

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to the envhermet Set (orchestrator uvwqvz, child 01 heglfv for the DEFECT, child 02 fwgq2u for the missing GUARD). This item is one of TWENTY-THREE open filings of a single non-hermetic assertion: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reads the AMBIENT OPENCODE_CONFIG_CONTENT, which run_opencode always sets for a turn. MEASURED at HEAD 22cf67d9: bare '144 passed', and with the variable set '1 failed, 143 passed' on 'assert OPENCODE_CONFIG_CONTENT not in {...}'. So the file is green for a human and red for every lane agent, which is why so many agents filed it independently. THE FIX MUST NOT RELAX THE ASSERTION: R4.1 genuinely requires a non-isolated turn to receive NO denial policy (it works in the main checkout where external-directory denial would refuse its ordinary work), so heglfv fixes the SEAM the test reads, not the guarantee. A session-wide conftest scrub is explicitly REJECTED, because that mechanism is what made rolevac 8i0xa7's role guard vacuous and repeating it would be a known self-inflicted defect. NOT CLOSED AS A DUPLICATE HERE: consolidating these twenty-three needs human judgement (uvwqvz OQ-01), since the filings are not identical and at least two attribute the failure to AW_EXECUTION_ROLE, a different and already-scrubbed cause.
- 2026-09-20 created (aw backlog): test_turn_bounds' isolation-scoped policy test fails when the runner's own OPENCODE_CONFIG_CONTENT is inherited from the ambient env

MEASURED at 283b3c92 while executing plan i1hlgx, which changed nothing in either file.

`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` fails at tests/test_turn_bounds.py:310.

WHAT IT ASSERTS. That the external-directory denial policy is ISOLATION-SCOPED (R4.1): `OPENCODE_CONFIG_ENV` present and denying for an isolated turn, and ABSENT for a non-isolated one, because a main-checkout turn would have its ordinary work refused by such a denial.

WHY IT FAILS HERE. The non-isolated assertion is `policy_key not in main_env`, and `main_env` is the env the runner would hand to the child. When the test runs INSIDE an agent turn that itself was launched with `OPENCODE_CONFIG_CONTENT` set (which is exactly the case under `aw oc run`: confirmed present in this turn's own environment), the variable is INHERITED into the constructed env and the absence assertion fails. The failure is therefore environment-dependent, not a product regression: it passes in a shell without that variable and fails in one with it.

WHY IT MATTERS ANYWAY. This is a test that ONLY fails when run from inside the runner it describes, so it is red for every agent turn in an `aw oc run` queue while being green for a maintainer running the suite by hand. That asymmetry costs every executing agent a baseline investigation, and it makes the failing-node-id comparison the execution contract relies on noisier than it should be.

SUGGESTED FIX. Either clear `OPENCODE_CONFIG_CONTENT` from the base environment the test builds `main_env` from, or assert that the runner does not SET it for a non-isolated turn (distinguishing 'not added by us' from 'not present at all'), which is the claim R4.1 actually makes.

FOUND BY: plan i1hlgx (unrelated change to run_cli.py's absent-ledger message). Present in the before-baseline as well as after.
