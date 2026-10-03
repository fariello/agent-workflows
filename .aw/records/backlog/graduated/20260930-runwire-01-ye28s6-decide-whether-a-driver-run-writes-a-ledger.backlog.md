- Id: ye28s6
- Status: graduated
- Graduated-To: runledger
- Set: runwire
- Priority: medium
- Work-Kind: chore
- Summary: Decide whether a driver run writes a hash-chained ledger, which is what makes run_engine and run_recovery reachable at all

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: rdjka2
- 2026-09-30 created (aw backlog): Filed while authoring Set runwire from backlog ildjse: the Set wires run_state and verify_roles into the runners but CANNOT wire run_recovery, because its whole API takes a run_engine.RunEngine and calls reconstruct_state(), RunEngine requires a RunLedgerStore over a ledger.jsonl, and no driver run writes one. This item exists so that residual has a durable carrier rather than living only in an executed plan's prose.

MEASURED at 2026-09-30 (lane worktree ildjse, HEAD cedab274): neither oc_runipd nor agy_runipd imports run_engine or run_recovery (zero grep matches in both). run_recovery's public surface (plan_retry, retry_budget_remaining, resume, cancel, recover_crash, detect_unknown_outcomes, reconcile_unknown_outcome) every one takes a run_engine.RunEngine first positional and calls engine.reconstruct_state().

WHY THIS IS NOT SIMPLY 'GO WIRE IT'. runner_shared's own retrywire comment states the position plainly and forbids treating it as settled: run_recovery.plan_retry / retry_budget_remaining 'REMAIN THE INTENDED LONG-TERM HOME', they are 'UNREACHABLE from a driver run', and 'WHETHER A DRIVER RUN SHOULD WRITE A LEDGER IS STILL OPEN and is NOT decided here ... Nobody may cite this section as a decision to abandon the ledger design'. Approved spec 25kzda concedes the ledger is built but unwired. Plans i1hlgx and executed 7wei1o both name it as an out-of-scope design question.

THE COST OF LEAVING IT OPEN IS ALREADY BEING PAID, and that is the argument for deciding rather than deferring indefinitely. Because the shared layer is unreachable, the driver carries a SECOND implementation of retry semantics (handle_turn_failure_retry, frozen_retry_budget, turn_retry_budget_remaining, TURN_RETRY_CLASSIFICATION, shipped by plan xipfy1), and runner_shared's comment says of that duplication: 'this repository normally refuses one'. The state vocabularies are disjoint too: plan_retry raises NoRetryableStateError for any step not in run_state.STATE_FAILED/STATE_BLOCKED, and a driver queue item never holds either value.

WHAT THIS ITEM MUST DECIDE. (a) Do driver runs emit a real hash-chained ledger.jsonl alongside the existing state.json/events.jsonl, making run_engine and therefore run_recovery reachable; or (b) is the ledger design for a different (aw run) execution path, in which case the driver's own retry implementation is the intended one and run_recovery's status as 'the intended long-term home' should be corrected in the comment rather than left as an aspiration. Either answer is actionable; the current state, where the code says one thing and the runtime does another, is the defect.

RELATED: backlog tzqvjn (EXIT_BLOCKED unreachable because a step's running state is never durable) is a concrete symptom of the same unwired substrate, and done item sv8z1e deliberately chose NOT to build a second resume engine, recording options 1 and 2 as rejected. Set runwire (orchestrator i18yaz OQ-01, children 32jpl1 and eow7p4) proceeds without this answer and forecloses neither.
