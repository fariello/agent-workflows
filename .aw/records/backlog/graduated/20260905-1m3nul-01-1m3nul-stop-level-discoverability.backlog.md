- Id: 1m3nul
- Status: graduated
- Set: 1m3nul
- Priority: low
- Work-Kind: feature
- Summary: the four-level graceful-stop protocol is undiscoverable: Ctrl-C never mentions that stop-after-call, stop-after-set, or stop-at-checkpoint exist

## Workflow history
- 2026-09-08 graduated (aw set): MOSTLY OBSOLETE, HEAVILY NARROWED, central premise FALSE. Verified by RUNNING the code as the item instructed: all four levels ship with no skeletons (runner_stop.py:210-215); a full out-of-band verb ships whose --help renders all four per-level descriptions plus four worked commands; and the R16 report ALREADY states level, awaited boundary and exact escalation command (I called render_request_accepted:1691 and pasted its output in plan wqq8ua). Its 'RELATED' note is stale too: i6015i is executed, not pending. THREE surfaces survive and are all plan wqq8ua does: the continuity footer (oc_runipd:7539, agy:4479), the main KeyboardInterrupt message (oc_runipd:8389-8399), and the run-level help (verified silent). SEPARATE FINDING, not fixed here: the item's explicit non-goal (an interactive Ctrl-C prompt) SHIPPED in 646be41f, and _sigint (runner_stop.py:1936-1953) bypasses SIGINT_LADDER on any TTY, recording LEVEL_NOW_FORCE, so a first Ctrl-C requests level 4 where spec c4gd2h R12 requires level 1. That is a correctness/spec-conformance defect and a maintainer decision, filed as item 4awwg4.
- 2026-09-05 created (aw backlog): the four-level graceful-stop protocol is undiscoverable: Ctrl-C never mentions that stop-after-call, stop-after-set, or stop-at-checkpoint exist

MOSTLY OBSOLETE 2026-09-08, HEAVILY NARROWED, AND ITS CENTRAL PREMISE IS FALSE. Read this before acting
on anything below. Graduated to plan `wqq8ua`
(`.aw/records/plans/pending/20260908-stopdisc-01-wqq8ua-...ipd.md`, carrying `- From-Backlog: 1m3nul`).

THIS ITEM SAID TO VERIFY WHICH LEVELS SHIP BEFORE DOCUMENTING THEM. I did, by RUNNING the code, and the
answer invalidates most of the ask.

DEAD 1: ALL FOUR LEVELS SHIP, none a skeleton. `LEVEL_AFTER_CALL`/`AFTER_SET`/`NOW`/`NOW_FORCE`
(`runner_stop.py:210-215`), budgets (`:248`), `request_stop` (`:547`), `poll_stop` (`:640`), with agy
mirroring each.

DEAD 2: A FULL OUT-OF-BAND VERB SHIPS, WITH EXCELLENT PER-LEVEL HELP. `python3 -m agent_workflows oc run
stop --help` exits 0 and renders a description of what each of the four levels does plus four worked
example commands, and `stop` appears in the `oc run --help` subcommand table. So this item's framing
that an operator "has no way to learn that this is precisely level 1" is wrong at the verb level:
`aw oc run stop <run-id> --after-call` exists and is documented.

DEAD 3: THE INTERRUPT REPORT ALREADY SAYS ALL THREE THINGS. This item claims "the interrupt report does
not say how to request one". I called the reporter directly and got: `stop accepted: level 1
(after-call) (requested by signal pid=123); waiting for the in-flight agent turn to finish; no further
item will be started; to stop harder, press Ctrl-C again (or run \`aw oc run stop <run-id> --now\`) to
request level 3 (now)`. That is the level, the awaited boundary, and the exact escalation command
(`render_request_accepted:1691`, with `AWAITING:1646`, `escalation_target:1654`,
`_escalation_hint:1669`), which satisfies spec R16.

DEAD 4: THE "RELATED" NOTE IS STALE. `i6015i` is not pending; it is in
`.aw/records/plans/executed/`, so there is no adjacent pending overlap. No pending plan covers this item.

WHAT SURVIVES, and it is all plan `wqq8ua` does: THREE surfaces say nothing about stopping. The
continuity footer (`oc_runipd.render_continuation_hint:7539`, `agy_runipd:4479`) prints session ids, a
reuse command, and either `aw runs <id>` or a resume command, and mentions stopping nowhere. The `main`
KeyboardInterrupt message (`oc_runipd.py:8389-8399`) is only "Interrupted; durable run state was
preserved." or the no-cleanup variant. And the run-level help says nothing: `aw oc run start --help`
grepped for stop, interrupt and ctrl matches nothing. The summary table is partial coverage: it labels a
COMPLETED stop as `STOPPED (Level N: ...)` (`oc_runipd.py:7462-7465`) but never advertises a possible
one.

THE ITEM'S EXPLICIT NON-GOAL HAS SHIPPED, AND IT BROKE THE SPEC. This item lists an interactive Ctrl-C
prompt under "EXPLICITLY NOT WANTED" with two reasons. That prompt shipped the SAME DAY in `646be41f`
(`prompt_interrupt_action:1794`), and `_sigint` (`runner_stop.py:1936-1953`) BYPASSES `SIGINT_LADDER`
entirely on any TTY, recording `LEVEL_NOW_FORCE` for two of its three choices. So on a terminal the FIRST
Ctrl-C requests level 4, while spec `c4gd2h` R12 (`:106`) requires level 1 then 1 -> 3 -> 4. That is a
CORRECTNESS and spec-conformance defect, contradicting this item's own "this is a DISCOVERABILITY item,
not a correctness one". It is NOT fixed by `wqq8ua`, because resolving it means either removing shipped
maintainer-authored behavior or amending an approved spec requirement, neither of which is an agent's
call. Filed as its own item, `4awwg4` (Set `stopladder`, high, bug). Plan `wqq8ua` E-01 exists precisely
to keep its new text TRUE ON BOTH PATHS so no documentation asserts a ladder a terminal does not run.

TWO CITATIONS IN THIS ITEM ARE STALE: `oc_runipd.py:5931` is now TWO handlers, `:6410` in `execute_item`
and `:8358` in `main` (only the latter is the interrupt report); and the `:5936-5941` repeated-interrupt
citation now lives in `prompt_interrupt_action` (`runner_stop.py:1832-1837`).

ORIGINAL ITEM TEXT FOLLOWS, uncorrected.

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
