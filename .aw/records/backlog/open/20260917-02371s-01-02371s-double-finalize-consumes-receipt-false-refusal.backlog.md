- Id: 02371s
- Status: open
- Set: 02371s
- Priority: high
- Work-Kind: bug
- Summary: With self_finalize=True both the agent and the driver run finalize, so the second one hits a receipt the first consumed and reports 'no begin receipt = no execution authority' for work that actually succeeded

## Workflow history
- 2026-09-17 created (aw backlog): With self_finalize=True both the agent and the driver run finalize, so the second one hits a receipt the first consumed and reports 'no begin receipt = no execution authority' for work that actually succeeded

## Observed

Run `run-20260917T210518Z-1714328`, IPD `63425h`, 2026-09-17. The item ended
`substantially-complete` with its lane PRESERVED as "not integrated", and the driver printed:

```
! IPD 63425h finalize refused (left substantially-complete, not forced): refused: no begin
  receipt for 63425h: run `aw ipd begin` first (fail-closed: no receipt = no execution authority).
  IPD-FINALIZE missing begin receipt at .aw/state/ipd-lifecycle/63425h.receipt.json
```

The work was COMPLETE. The lane held three commits, the plan was already in `executed/` there, and
the full suite passed. The refusal was a FALSE NEGATIVE.

## What actually happened

1. The driver ran `aw ipd begin` exactly as designed (`oc_runipd.py:6698`). Proof it succeeded: the
   run recorded NO `ipd-begin-refused` event, the attempt carries no `begin_refused` key, and the
   agent turn launched. A nonzero begin returns early and never launches the turn.
2. The AGENT then finalized the plan itself, producing `575f0b32 lifecycle(63425h): finalize 63425h
   -> executed`.
3. A successful finalize CONSUMES the receipt (`ipd_lifecycle.py:3570-3573`, comment: "Consume the
   begin receipt (the transaction is cleanly complete)").
4. The driver's `driver_finalize` then ran finalize a SECOND time for the same item and found no
   receipt, because step 3 had deleted it.

So with `self_finalize=True` (this run's setting, and the default) there are TWO finalizers for one
item, and the receipt is a single-use token. Whichever runs second is guaranteed to fail.

## Why the diagnosis is not "begin did not run"

That is the reading the message invites and it cost real investigation time here. `checkout_control_root`
was verified to collapse lane and main to ONE control store, so the `dh0uno` split-receipt bug is NOT
in play: `checkout_control_root(<lane>) == checkout_control_root(<main>)` returns True. Begin ran, in
the right place, and wrote the right file.

## Cost

The lane was left preserved and unintegrated with its work finished, so a human had to diagnose and
merge it by hand (`2cfdb85d`). Unattended, the item reads as incomplete in the run summary while its
work sits on a branch nobody is told is mergeable.

## Expected

The driver must not attempt a finalize that already happened. Before refusing, it should establish
whether the transition ALREADY SUCCEEDED (the plan is in `executed/`, and the finalize commit exists
on the lane) and, if so, treat the item as `executed` and integrate it.

## Fix sketch

1. Make the driver's finalize step idempotent: detect an already-finalized plan (terminal directory +
   a finalize commit on the lane) and skip to integration instead of refusing.
2. Decide and document ONE owner of the transition per item. If the agent may self-finalize, the
   driver must not re-run it; if the driver owns it, the agent's runbook must not instruct a finalize.
   Two finalizers for a single-use token is the root defect, and item 1 alone only masks it.
3. Regression test: an item whose agent self-finalizes must end `executed` and INTEGRATED, not
   `substantially-complete` with a preserved lane.

## Related

`894vzu` is the sibling defect that made this hard to diagnose: a consumed receipt and a never-issued
one produce the same message. Fixing `894vzu` alone would not fix this; fixing this alone would leave
the misleading message for other callers.
