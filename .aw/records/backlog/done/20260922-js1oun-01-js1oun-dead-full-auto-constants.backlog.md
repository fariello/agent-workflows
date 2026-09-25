- Id: js1oun
- Status: done
- Set: js1oun
- Priority: low
- Work-Kind: chore
- Summary: runner_shared carries two dead FULL_AUTO_* constants whose values match no host

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: duplicate of zf999x
- 2026-09-22 created (aw backlog): runner_shared carries two dead FULL_AUTO_* constants whose values match no host

Found while executing plan li44r9 (hostdedup Order 01).

`agent_workflows/runner_shared.py` defines `FULL_AUTO_ACTOR = "aw-driver/full-auto"` and
`FULL_AUTO_APPROVAL_MESSAGE = "Auto-approved via --full-auto (review passed all gates)"`. Measured at
HEAD ee20e831: NOTHING reads either name -- not the module itself, not either runner, not the suite.
Each runner defines its OWN pair and reads those, and neither shared value matches either host: the
hosts' actor is `aw oc run --full-auto` / `aw agy run --full-auto` and their message is
"auto-approved by --full-auto: review readiness cleared (not human approval)".

WHY THIS IS WORTH REMOVING RATHER THAN LEAVING. When `set_plan_approved` was lifted into
`runner_shared` by `li44r9`, the obvious-looking implementation was for the shared body to read these
names, since they are already in scope under exactly the right spelling. That would have silently
re-attributed EVERY host's auto-approval to `aw-driver/full-auto` in permanent plan history AND changed
the recorded approval message on both hosts, while every existing test stayed green. The trap is live
for the next author who reaches for the obvious name.

MITIGATION IN PLACE, WHICH IS WHY THIS IS LOW AND A CHORE: both constants now carry a prominent note
at their definition stating that they are dead, that they match no host, and that the shared
`set_plan_approved` deliberately takes both values from its CALLER instead. So the trap is labelled.

WHY `li44r9` DID NOT DELETE THEM: removing a public module attribute is a compatibility change, and
that plan's scope is a pure code MOVE with no behavior change authorized.
