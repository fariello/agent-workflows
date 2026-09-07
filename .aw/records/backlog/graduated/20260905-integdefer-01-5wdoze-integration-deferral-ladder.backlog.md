- Id: 5wdoze
- Status: graduated
- Blocks-Release: next
- Set: integdefer
- Priority: high
- Work-Kind: bug
- Summary: a refused lane integration is terminal on first attempt: add the defer/poll/ask ladder so transient dirt in main does not permanently block a verified lane

## Workflow history
- 2026-09-07 graduated (aw set): Graduated to plans 6sb3yu (integpath-02, the shared extraction seam) and 51vw4y (integpath-03, the three-rung deferral ladder). Provenance also recorded on orchestrator cczotj. Closed by 51vw4y, which delivers the ladder.
- 2026-09-05 created (aw backlog): a refused lane integration is terminal on first attempt: add the defer/poll/ask ladder so transient dirt in main does not permanently block a verified lane

MEASURED INCIDENT. Run `run-20260905T050043Z-639569` (34 items, 7h40m, \$165.90). Four items
finished their work, passed their gates, finalized on their lane branches, and then FAILED TO
INTEGRATE because the main tree had dirty paths overlapping their changes:

    08:06:32 ipd-integration-blocked 76gsmv  agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py
    08:51:26 ipd-integration-blocked eyh1fu  .aw/records/reviews/*.review.md (3 files)
    10:48:33 ipd-integration-blocked txc9l1  agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py
    11:47:04 ipd-integration-blocked uyeko5  agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py

Three more items (`6ypimw`, `wpomxa`, `5slbpi`) then cascaded to `dependency-blocked` because
their prerequisites had not reached `executed`. Seven of 34 items lost to transient dirt.

Verified 2026-09-05: all four lane branches still exist and ALL FOUR MERGE CLEAN against main today
(`git merge-tree --write-tree main aw/lane/<id6>` succeeds for each). The work was never in
conflict. It was refused because of WHEN it was attempted.

THE CURRENT BEHAVIOR. `integrate_lane_branch` (`oc_runipd.py:1881`) calls `dirty_tree_overlap`
(`oc_runipd.py:1849`) BEFORE the gate and returns `integration-blocked` on any overlap
(`oc_runipd.py:1913-1920`), leaving main untouched and the lane preserved. That refusal is correct
and must stay. The DEFECT is what happens next: the caller (`oc_runipd.py:5308-5352`) writes
`integration-blocked`, which is in `TERMINAL_STATES` (`oc_runipd.py:249`), so the item is never
re-attempted for the rest of the run. One transient condition, permanent loss.

The refusal cause is TRANSIENT BY NATURE: another writer's uncommitted file in a shared checkout.
Waiting 30 minutes would very likely have cleared it. Nothing waited.

THE FIX: A THREE-RUNG LADDER. Maintainer-approved design (2026-09-05).

RUNG 1 - DEFER AND RE-ATTEMPT (while other work exists). Add a NON-TERMINAL
`integration-deferred` status. On a dirty-overlap refusal, mark the item deferred rather than
blocked and re-attempt integration at the top of the existing dispatch loop
(`oc_runipd.py:5793`), which already reloads state and already runs `cascade_dependency_blocked`
each iteration. A lane refused at 08:06 would have integrated at 08:40 when the next item finished.
Zero waiting, zero tokens, nothing blocked.

RUNG 2 - BOUNDED POLL (when nothing else is dispatchable). The trigger is NOT "is this the last
item" but "is there any item I could dispatch instead" - the condition the loop ALREADY computes
as `runnable is None` (`oc_runipd.py:5823-5833`). That one condition covers both the last-item
case and the case where five items remain and ALL are deferred, which a last-item test would miss.
When `runnable is None` and deferred items exist, poll `dirty_tree_overlap` instead of ending the
run.

TWO INDEPENDENT BOUNDS, both required:
  (i)  max poll count (default 10);
  (ii) max staleness of activity in main. Stop polling when the NEWER of main's HEAD commit time and
       its most recent dirty-file mtime exceeds a threshold (default ~1h). Poll count alone is the
       wrong sole bound: 10 polls at 30s is 5 minutes whether main is alive or has been idle since
       yesterday. If nothing has moved in main for an hour, nobody is about to commit and polling is
       superstition. Bound (ii) is what makes the wait EVIDENCE-BASED rather than arbitrary.

Report both honestly: "polled 10x over 5m; main last active 3m ago" and "gave up immediately,
main idle 4h" are very different facts. The second tells the operator the dirt is abandoned and
needs a human.

RUNG 3 - ASK (default after 1 and 2 fail, overridable). Prompt the operator. HARD CONSTRAINT: the
ask MUST NOT be able to hang the run forever, or this rebuilds the unbounded-wait deadlock that
`qyaime` closed (whose own honest limit was that the ask is "bounded and recorded, not
architecturally prevented"). So the prompt needs its own timeout, and on timeout it falls to
terminal `integration-blocked` with the lane preserved - never sits there. Suppress `ask`
automatically when no TTY is attached: an unattended overnight run must never stop on a question
nobody will see.

Then, and only then, terminal `integration-blocked`.

Override: `--on-integration-blocked=defer|poll|ask|block` plus a config default.

THE BUDGET MUST BE SEPARATE FROM THE CORRECTION BUDGET. Do NOT reuse `DEFAULT_RETRY_LIMIT`.
Two different quantities are being counted:

  * `DEFAULT_RETRY_LIMIT = 2` counts PAID CORRECTION TURNS. `run_recovery.py:56-64` gives the
    reason: "a retry cannot turn failure into success by mere repetition", so a third attempt
    "mostly buys another paid turn".
  * An integration re-attempt costs one `git status` and one `git merge-tree`. Milliseconds, zero
    tokens, and repetition genuinely CAN succeed here, because the blocker is another process's
    transient dirt.

Sharing the budget would be a category error. New knob `--integration-retry-limit`, default 10.
Note also that there is nothing to reuse even if we wanted to: `plan_retry` /
`retry_budget_remaining` have zero production callers (see `trjfyy`), so this is a new counter
either way. And do NOT force an integration-poll count into spec 2.1's 0..10 range, which bounds the
CORRECTION budget specifically.

RE-VERIFICATION IS MANDATORY ON EVERY ATTEMPT. A lane verified against yesterday's main is not
verified against today's. Every re-attempt must route through the existing
`orchestrate_isolation.execute_merge_and_revalidate_gate`, which already encodes "per-lane green
never implies integrated green". Do NOT shortcut to a bare `git merge` because `merge-tree` came
back clean: that proves absence of TEXTUAL conflict and says nothing about whether the suite still
passes.

BOTH RUNNERS. `oc_runipd.py` and `agy_runipd.py` each carry a copy of `integrate_lane_branch`
(`oc_runipd.py:1881`, `agy_runipd.py:1067`). The ladder belongs in shared code with both calling
it, not copy-pasted twice; see `cnwy8g` on the 40-symbol import coupling.

CONSIDERED AND DELIBERATELY DECLINED (2026-09-05, maintainer): narrowing the false-positive rate by
comparing content. If main's dirty version of a path is BYTE-IDENTICAL to what the merge would
produce, the overlap provably cannot affect the outcome, so the refusal could be skipped. Tabled as
low-value relative to the ladder. Anything BEYOND that (path-pattern allowlists, "docs are safe",
"review records are harmless") is explicitly REJECTED: it reasons about who probably wrote a file
rather than whether it can conflict, which is the fail-open inference `d07nz2` prohibits. Narrow on
content, never on category.

RELATED. `h1ksy6` (open) fixes the same function but WIDENS its input set, making refusal MORE
reachable; it is diagnostic-only and does not address "then what". These two must be reconciled,
not stacked blindly. `2c122z` (superseded, never landed) is the only prior art that designed a
softer disposition (`dirty_main_policy="pause"`). `a8eufb` (open) would let the runner tell its
own dirt from a co-worker's. Sibling items: the startup gate, the re-integrate verb, and the
deferred-orchestrator fix in this Set.
