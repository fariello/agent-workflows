- Id: xuc9v0
- Status: open
- Blocks-Release: next
- Set: xuc9v0
- Priority: high
- Work-Kind: bug
- Summary: The default test command hides 33 real slow-marked failures, including every end-to-end runner-stop test; a green routine run proves less than it appears to

## Workflow history
- 2026-09-23 created (aw backlog): The default test command hides 33 real slow-marked failures, including every end-to-end runner-stop test; a green routine run proves less than it appears to

## What

`pyproject.toml`'s `addopts` includes `-m 'not slow'`, and the repository's agent contract instructs
every agent to run the suite BARE (`python3 -m pytest`) and explicitly not to add flags. The result is
that no routine run, and no agent following the contract, ever executes the `slow` set.

Measured on 2026-09-23 at HEAD `67d1f8c0` in lane `aw/lane/13xo5k`:

- `python3 -m pytest` (the contract's command): `8725 passed, 1 failed`.
- `python3 -m pytest -m slow`: `33 failed, 375 passed`.

Nineteen of those 33 were the end-to-end runner-stop tests, i.e. the ONLY tests that drive a real
level-3 or level-4 stop through a real driver subprocess. They had been red for some time, and plan
`13xo5k`'s own `/plan-review` recorded a baseline of "8287 passed, ZERO failures" at review time,
which was true of the command it ran and false of the repository.

## Why it is a bug and not a chore

It is user-perceptible in the way that matters most here: it caused a WRONG DECISION. The stop-path
crash plan `13xo5k` was written for was already covered by shipped tests that were already failing.
Had the slow set been visible, the defect would have been found by the suite instead of by an
operator hitting it in a live paid run, and the plan would not have been authored believing only one
handler was broken. A gate that is green while 33 real failures exist is worse than no gate, because
it is actively consulted as evidence.

## Two things to separate

1. The 33 failures themselves. Nineteen are fixed by `13xo5k`. The remaining 14 are unrelated
   (installer deep-cleanup, CLI conformance matrix, role-declaration guard, release readiness,
   `test_turn_bounds` permission policy) and each needs its own triage; they are NOT addressed here.
2. The VISIBILITY problem, which is this item. Options worth weighing:
   - Have CI run the slow set (if it does not already) and make its result reachable, so "the suite is
     green" cannot be asserted from the fast subset alone.
   - Have the agent contract require the slow set at a defined boundary (before a plan may be marked
     executed, say) rather than never.
   - Report the deselected count prominently, so a reader of `8725 passed` also sees `408 deselected`
     and knows the number is partial.

Do NOT simply drop `-m 'not slow'` from `addopts` without measuring: the marker exists because those
tests spawn real subprocesses and cost minutes.

## Evidence

Both runs are pasted in plan `13xo5k`'s execution report, along with the per-node-id comparison showing
19 fixed and zero newly broken.
