- Id: 1m3nul
- Status: open
- Set: 1m3nul
- Priority: low
- Work-Kind: feature
- Summary: the four-level graceful-stop protocol is undiscoverable: Ctrl-C never mentions that stop-after-call, stop-after-set, or stop-at-checkpoint exist

## Workflow history
- 2026-09-05 created (aw backlog): the four-level graceful-stop protocol is undiscoverable: Ctrl-C never mentions that stop-after-call, stop-after-set, or stop-at-checkpoint exist

THE GAP. Spec `c4gd2h` (status: implementing) defines a four-level stop protocol, and
`runner_stop` implements it: level 1 = stop after this call (R20/A1), level 2 = stop after this set
(R20/A4), level 3 = stop at a safe checkpoint inside the running turn, each with a bounded wind-down
budget that ESCALATES rather than hangs (R11). The driver polls a stop-request flag at cooperative
checkpoints (R7).

None of this is discoverable from the interface an operator actually reaches for. Ctrl-C does not
mention the levels exist, and the interrupt report does not say how to request one. An operator who
wants "finish the current item and stop cleanly" has no way to learn that this is precisely level 1.

WHAT CTRL-C ACTUALLY DOES TODAY, recorded because it is easy to assume otherwise: it is handled
correctly. In run `run-20260905T050043Z-639569` the interrupt propagated through the
`except KeyboardInterrupt` handler (`oc_runipd.py:5931`), reclaimed and preserved lanes,
printed a lane report, and ended the run. The item in flight (`i6015i`) was marked `interrupted`;
the 18 items that show `queued` were never started. It did NOT continue to the next item. Durable
state was preserved and the run is resumable. So this is a DISCOVERABILITY item, not a correctness
one.

THE ASK. Surface the levels where an operator will meet them: in the interrupt report, in
`--help`, and in the run summary's continuity footer. State what each level does, and give the exact
command to request one.

EXPLICITLY NOT WANTED - an interactive prompt on Ctrl-C. A three-way "clean up and terminate /
terminate without cleanup / resume" question at interrupt time was considered and rejected
(2026-09-05) for two reasons:

  1. It fights an existing deliberate design. A SECOND Ctrl-C from an impatient operator during the
     prompt is a real scenario, and the code already handles it: on repeated interrupt it stops
     prompting and finishes preservation unattended (`oc_runipd.py:5936-5941`, laneorphan-01 E-10),
     precisely so that "the operator is trying harder to stop" is never met with another question.
  2. Ctrl-C is the path an operator takes when they want OUT. Blocking that path on a question risks
     the unbounded-wait failure `qyaime` documented.

So: better reporting and better help, no new prompt.

RELATED. Spec `c4gd2h` is the authority and has sat in `implementing` since 2026-08-29, so confirm
which levels are actually wired before documenting them - do not document an unshipped level as
available. `i6015i` (pending, worksequence-01) touches adjacent operator-facing surfacing.
