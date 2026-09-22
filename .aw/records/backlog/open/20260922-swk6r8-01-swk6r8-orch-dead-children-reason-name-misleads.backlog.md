- Id: swk6r8
- Status: open
- Set: swk6r8
- Priority: medium
- Work-Kind: chore
- Summary: The orchestrator refusal reason children-terminally-failed fires for a child merely awaiting approval, so its name misleads

## Workflow history
- 2026-09-22 created (aw backlog): Filed by aw oc run while executing plan zyw4n3.

MEASURED 2026-09-22 while executing plan `zyw4n3` (runghostid Order 01), driving the real `aw oc run` on the scenario backlog item `i2fjf8` complained about: an `approved` orchestrator over a `reviewed` (unapproved) child.

WHAT IS WRONG. `runner_shared.decide_orchestrator_dispatch` returns reason `ORCH_REASON_DEAD_CHILDREN` = `children-terminally-failed` whenever a child's run status is `in terminal_states and not in success_states`. `reviewed` IS in `TERMINAL_STATES` (printed to confirm: approved, blocked, dependency-blocked, executed, failed-safely, integration-blocked, merge-conflict, merge-needs-human, merge-refused, not-attempted, partial, reviewed, substantially-complete), because an unapproved plan is frozen and never dispatched. So the code name and its own detail string ("reached a non-success terminal state") describe a FAILURE for what is overwhelmingly the commonest case: a child simply waiting for human approval. Nothing failed.

WHY IT MATTERS. The reason code is now operator-visible (plan `zyw4n3` renders it in the run summary's diagnostics block, in `aw runs`' Details/Refusals sections, and in the `--agent --issues` JSON payload as `refusal.code`), so a name meaning "your child crashed" is read by an operator whose child merely needs approving. It also reads as a failure to any tooling keying on the code.

WHAT WAS DONE IN THE MEANTIME, so this item is a naming/structure concern and not a live misleading message: `zyw4n3` E-02's REMEDY and reason prose for this code name the approval case FIRST and explicitly say "The usual cause is a child that was never dispatched because it is not approved, NOT a child that crashed", with a test (`test_the_dead_children_remedy_covers_the_awaiting_approval_case`) pinning it. So the message is honest today; the CODE is still misnamed.

THE REAL FIX, which is out of `zyw4n3`'s scope (it may not change what the dispatch DECIDES): split the reason, e.g. `children-not-approved` for a child whose terminal status is `reviewed`/`approved` (never dispatched) versus `children-terminally-failed` for one that ran and failed. That changes the typed vocabulary spec `77tr3o` governs and a read surface's codes, so it needs its own plan.

WHERE: `agent_workflows/runner_shared.py`, `decide_orchestrator_dispatch`'s `dead` branch and `ORCH_REASON_DEAD_CHILDREN`.
