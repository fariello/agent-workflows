- Id: hegwri
- Status: open
- Set: runledger
- Priority: medium
- Work-Kind: chore
- Summary: Nothing in the package can create a run ledger: no writer of a kind='run' header record exists, so RunLedgerStore refuses every first append with RL-E041

## Workflow history
- 2026-10-09 same-status (aw backlog): Scoped to aw run execution path per rdjka2 maintainer decision (option b); not a driver obligation
- 2026-10-02 created (aw backlog): Filed while graduating backlog ye28s6 into plan rdjka2: this is the measured prerequisite for any ledger wiring, whichever way ye28s6's question is answered.

MEASURED at 2026-10-02 (lane worktree ye28s6, HEAD fb75224d), both by static search and by driving the API live.

THE DEFECT, STATED AS A CAPABILITY GAP. `RunLedgerStore.append` refuses any ledger whose FIRST record is not `kind: "run"`, raising `SchemaInvalidRecordError` with finding `RL-E041` ('first ledger record must be kind run'); `run_ledger_schema.validate_records` enforces the same rule on read. But a repository-wide search for a writer of such a record under `agent_workflows/` returns ZERO matches: every occurrence of the token is a READER or a refusal (in `run_cli`, `run_engine`'s replay, and the two store guards). `RunEngine`'s only five append paths write `step_attempt`, `human_approval`, `verifier_decision` and `terminal_transaction` - never the header.

REPRODUCED LIVE. Constructing a `RunLedgerStore` over a fresh temp path and driving the LEGAL engine sequence (`release_step` -> `start_step` -> `record_step_attempt`) raises `SchemaInvalidRecordError: Schema-invalid record at seq 0: (Finding(code='RL-E041', where='kind', message="first ledger record must be kind 'run'"),)` and leaves no file on disk. Consistent with that, zero `ledger.jsonl` files exist anywhere in the tree outside `.git`, and the product says so: `aw run start run-abc123 --step S-01` exits 2 with 'no driver run writes one today'.

WHY THIS MATTERS EVEN THOUGH NO RUN FAILS. The consequence is that the whole `aw run` write surface is unreachable in practice: `aw run start`, `next`, `record`, `resume`, `cancel`, `status` and `finalize` all build a `RunEngine` over a ledger that nothing can create, and `tests/conformance_matrix.py` encodes eight of those leaves as permanently not-runnable for exactly this reason. Only tests have ever created a ledger, by appending the header record themselves (see the `_run_record` helper in `tests/test_run_recovery_cli.py`), which is why the suite passes while no operator can reach the behavior.

WHAT THIS ITEM MUST DELIVER. At minimum a ledger-CREATION path that writes a conformant header record (it needs `workflow_digest`, `requirement_digest`, `repo` and `head` beyond the common envelope), and a decision on spec 25kzda Section 6.2's still-open 'durable storage location for run ledgers'. A driver-side step model is additionally required if, and only if, ye28s6 is answered in favour of driver runs writing a ledger.

RELATION TO ye28s6 AND TO hrdmfy. This item is the PREREQUISITE that ye28s6's option (a) depends on, and it is worth fixing independently of that answer because the `aw run` CLI's own write surface needs it. Pending plan hrdmfy owns `run_engine.py`, `run_ledger_store.py` and `run_ledger_schema.py` for its `step_started` record kind, so sequence behind it rather than editing those files concurrently. Executed plan e834yk's OQ-01 reached the same measurement and recorded the honest conclusion as 'neither, yet'.
