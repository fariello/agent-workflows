- Id: tzqvjn
- Status: open
- Blocks-Release: next
- Set: exitblocked
- Priority: low
- Work-Kind: bug
- Summary: run_cli EXIT_BLOCKED is unreachable from any separate process: a step's running state is never durable

## Workflow history
- 2026-09-28 created (aw backlog): run_cli EXIT_BLOCKED is unreachable from any separate process: a step's running state is never durable

Measured at plan review of ck0vya (2026-09-28), independently of that plan's own authoring measurement.

WHAT IS WRONG. `run_cli._run_resume` returns `EXIT_BLOCKED` (3) only from its `except run_recovery.UnknownOutcomeError` arm. `run_recovery.detect_unknown_outcomes` raises only for a step whose reconstructed state is `run_state.STATE_RUNNING` with `last_attempt_state is None`. But `running` is absent from `run_ledger_schema.ATTEMPT_STATES` (`frozenset({'blocked','failed','performed'})`), so `RunLedgerStore.append` REFUSES a `step_attempt` carrying it, and the sole producer of that state is `run_engine.start_step`'s in-process `_ephemeral_step_states` dict, which no separate CLI invocation can observe.

MEASURED, end to end:

  - Appending a `step_attempt` with `state='running'` raises SchemaInvalidRecordError with finding RL-E030: "attempt state must be one of ['blocked', 'failed', 'performed']".
  - `aw run start <ledger> --workflow wf.json --step s1` prints `Started step s1 (state: running)` while the ledger's record kinds remain `['run']` (nothing appended).
  - A following `aw runs resume` in a NEW process reports `state: pending` and exits 0.
  - Each appendable attempt state (performed, blocked, failed) also yields exit 0.
  - `run_state.STATE_RUNNING in run_ledger_schema.ATTEMPT_STATES` is False.

So the fail-closed guarantee `run_recovery.resume`'s docstring describes ("Refuses to advance if any step is in an unknown_outcome condition (interrupted side effect)") cannot fire across a process boundary, which is the only boundary that matters for an interrupted run. That is the scenario the guarantee exists for.

WHAT THIS ITEM MUST DECIDE. First, whether a step's `running` state must survive a process boundary at all (the drivers do not use this ledger path today, so the answer may legitimately be no, in which case the dead arm and its docstring promise should be removed rather than fixed). If yes, then whether durability comes via a new appendable attempt state or a distinct record kind, plus the migration question for existing ledgers, `reconstruct_state`'s replay, and the single-writer lease `run start` takes.

NOT THE SAME AS bn58ha, which is about precheck ignoring an unknown-outcome journal. This one is that the unknown-outcome condition can never be reconstructed at all.

CARRIER FOR: plan ck0vya's OQ-01 and its first Deferred row. ck0vya only stops the DECLARATION asserting exit 3; it deliberately does not fix this.
