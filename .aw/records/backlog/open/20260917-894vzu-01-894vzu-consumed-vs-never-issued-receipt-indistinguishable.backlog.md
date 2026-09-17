- Id: 894vzu
- Status: open
- Set: 894vzu
- Priority: medium
- Work-Kind: bug
- Summary: A CONSUMED begin receipt (finalize already succeeded) and a NEVER-ISSUED one (no execution authority) produce an identical refusal message, so a completed lane is indistinguishable from an unauthorized one

## Workflow history
- 2026-09-17 created (aw backlog): A CONSUMED begin receipt (finalize already succeeded) and a NEVER-ISSUED one (no execution authority) produce an identical refusal message, so a completed lane is indistinguishable from an unauthorized one

## Observed

Run `run-20260917T210518Z-1714328`, IPD `63425h`, 2026-09-17. `finalize_precheck` reported:

```
no begin receipt for 63425h: run `aw ipd begin` first (fail-closed: no receipt = no execution authority).
IPD-FINALIZE missing begin receipt at .aw/state/ipd-lifecycle/63425h.receipt.json
```

Every clause of that is defensible in isolation and the conclusion it implies was WRONG. Begin HAD
run and HAD written the receipt; a successful finalize had then consumed it
(`ipd_lifecycle.py:3570-3573`). The true state was "already finalized", the opposite of "never
authorized".

## Root cause

`finalize_precheck` (`ipd_lifecycle.py:1602-1611`) tests only `read_receipt(...) is None` and maps
that single condition onto one message asserting a specific cause:

```python
receipt = read_receipt(repo_root, plan_id)
if receipt is None:
    return (EXIT_FINDINGS,
            f"no begin receipt for {plan_id}: run `aw ipd begin` first (fail-closed: no receipt = "
            "no execution authority).", ...)
```

But absence has at least three causes with opposite meanings:

1. begin never ran -> genuinely no authority (refuse, and the message is correct)
2. finalize already SUCCEEDED and consumed it -> the work is done (refusing is a false negative)
3. the receipt was written to a different control root -> the `dh0uno` class of bug

The remedy the message prescribes is actively harmful in case 2: running `aw ipd begin` again on an
already-finalized plan mints authority for work that is complete.

## Why this matters beyond one confusing string

It sent the diagnosis down the wrong path for an extended investigation, including checking whether
the runner called begin at all (it does, `oc_runipd.py:6698`) and whether the lane had a split receipt
store (it does not; `checkout_control_root` collapses correctly). The message named a cause with
confidence and that confidence was misplaced, which is worse than naming no cause.

## Expected

Distinguish the cases before asserting one. A precheck that cannot tell success from
never-authorized should say so rather than pick the alarming reading. Where the plan is already in a
terminal directory, the correct report is "already finalized", not "no execution authority".

## Fix sketch

1. On a missing receipt, check whether the plan is already in a terminal directory (and, where
   available, whether a finalize journal records a COMPLETE phase). Report "already finalized" for
   that case, with a distinct finding id so a caller can branch on it.
2. Keep the existing message for the genuine never-issued case; it is correct there.
3. Do NOT let a consumed receipt read as an authority failure. That distinction is what a caller like
   the driver needs in order to integrate rather than preserve a finished lane (`02371s`).
4. Regression test: assert the three cases produce three DISTINGUISHABLE outcomes, not one.

## Honest scope note

This is the DIAGNOSTIC half. `02371s` is the behavioral half (two finalizers for a single-use token).
Fixing this one improves every future diagnosis but does not by itself stop a finished lane being
left unintegrated.
