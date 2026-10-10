# Walkthrough: recovery of the 2026-10-09 overnight run failures

- Id: 04qifi
- Date: 2026-10-09
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us

## What failed

Three runs from one `aw partition -n 3` (`run-20261009T013333Z-334392`, `run-20261009T024714Z-1667714`,
`run-20261009T030837Z-2088618`) ended with seven non-executed items: five orchestrators refused
`children-not-in-this-run`, `m47znv` refused at finalize, and `ytas91` refused at dispatch. The bare
suite on main was also red (8 failures).

## What was done, with evidence

- `m47znv` (lifegate 03): its verified work on `aw/lane/m47znv_attempt2` was refused at finalize only
  because the agent filed a defect backlog item (`i6dzbj`) outside Scope-Paths, a retryable class the
  runner misclassified (backlog `h3fnoc`). Finalized in the lane with a `--scope-reason` for that file
  (`efc370344`), then integrated by `aw agy run integrate m47znv --run-id run-20261009T030837Z-2088618`
  with the suite re-run in the primary checkout: `7202 passed, 2 skipped, 3 warnings`.
- `h3fnoc` fixed in `09e9199d0`: `runner_shared.finalize_refusal_is_retryable` Arm 3 now judges only
  `IPD-` finding lines; `tests/test_scope_reconcile_sendback_real_text.py` drives a real
  `ipd_lifecycle.finalize` refusal through the runner-rendered shape and failed before the fix.
- `ytas91` (fixfirst 04): stale `pending/` path of retired `p47qfu` dropped from Scope-Paths
  (`b8f0bf4b1`).
- Red suite: `tests/test_scope_exceeded.py` still minted the driver attestation `e25iy9` deleted
  (`64b8c94f3`, closes `fdkkco` and its duplicate `i6dzbj`); `tests/test_attempt_lane_facts.py`
  case 2 broke when `w9nvq4` made a red merge retryable (`d62ef31f3`). Bare suite after all fixes:
  `7202 passed, 2 skipped, 3 warnings`.
- Checkout `.git/config` carried `[user] name = Test, email = test@example.com` from 2026-10-08 01:31,
  so 320 unpushed commits are authored `Test`. The `[user]` block was removed on maintainer instruction;
  the leaking test is still unidentified (backlog `8o7gco`).

## What is not done here

Open work is tracked in backlog, not here: the partition defect (orchestrators split from their
children, and Sets with unrunnable children admitted), `dparot` (rename destination refused at
dispatch), `8o7gco` (find the leaking test), and the two `to-review` netnsfilter children
(`2j4pd0`, `wn956n`) that block `m0kl28`.
