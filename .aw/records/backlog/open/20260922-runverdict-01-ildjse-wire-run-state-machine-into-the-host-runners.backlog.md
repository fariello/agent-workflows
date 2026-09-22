- Id: ildjse
- Status: open
- Set: runverdict
- Priority: medium
- Work-Kind: chore
- Summary: Wire the run state machine into the two host runners, which import none of run_state, verify_roles or run_recovery

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan 1bfppy.

MEASURED by AST walk at 2026-09-22 (HEAD `d51be185`): neither `oc_runipd` nor `agy_runipd` imports `run_state`, `verify_roles` or `run_recovery` - zero matches in both drivers.

WHAT EXISTS AND IS UNUSED. `run_state.py` defines the closed state set, the complete legal transition table and per-edge transition AUTHORITY, including `verifying -> correction_required` (authority `verifier`/`runtime`) and `correction_required -> runnable`. `verify_roles.py` grants the verifier role exactly that `state_authority`. `agy_verifier.py` is the worked example of consuming it properly (`FINAL_CORRECTION_REQUIRED`). So this is a WIRING GAP between two of this repository's own components, not a missing concept.

WHAT PLAN `1bfppy` DID ABOUT IT, so this item is not over-scoped. That plan's `map_verdict` now CONSUMES `run_state`'s tokens (`STATE_VERIFIED`/`STATE_CORRECTION_REQUIRED`/`STATE_BLOCKED`) through a lazy in-function import in `runner_shared`, and records the resolved state on the attempt. That is one consumer of the vocabulary; it is NOT the state machine being wired. Nothing TRANSITIONS through `run_state`'s table, nothing checks its authority, and the runners still carry their own status vocabulary (`TERMINAL_STATES`, the `verify_disp` strings) in parallel.

THE HONEST LIMIT ON PRIORITY. This is a design-coherence defect, not a live bug: the runners' own status handling works, and three overlapping vocabularies is a maintenance cost rather than a wrong answer, which is why this is `chore` and not `bug`. It is worth recording because the cost is paid repeatedly - plan `1bfppy` had to decide from scratch which state a rejected verdict belongs in, and plan `fzxfph` faces the same question for three more facts (it measured that `run_state` has NO token for any of them).

RELATED: the requeue this enables is plan `1bfppy` OQ-01, deliberately deferred there because the drivers have no per-item retry loop at all for a requeue to consume.
