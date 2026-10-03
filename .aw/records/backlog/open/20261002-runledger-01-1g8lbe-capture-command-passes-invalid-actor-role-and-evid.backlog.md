- Id: 1g8lbe
- Status: open
- Blocks-Release: next
- Set: runledger
- Priority: medium
- Work-Kind: bug
- Summary: capture_command is called with actor='driver' and evidence_kind='tests', neither in the ledger schema's closed vocabulary, so both produced records fail validation

## Workflow history
- 2026-10-02 created (aw backlog): Filed while graduating backlog ye28s6 into plan rdjka2: found while measuring whether a driver run could write a ledger.

MEASURED at 2026-10-02 (lane worktree ye28s6, HEAD fb75224d) by calling the function live and validating its output with run_ledger_schema.validate_record.

THE DEFECT. `runner_shared.run_suite_check` calls `run_evidence.capture_command(..., actor="driver", evidence_kind="tests")`. Neither value is in the schema's closed vocabulary: `run_ledger_schema.ROLES` is {coordinator, corrector, executor, human, investigator, runtime, verifier} and has no `driver`, so the returned `tool_event` fails `RL-E014` ('unknown actor role'); and `EVIDENCE_KINDS` is {artifact, command, diff, inspection, test_report} and has no `tests`, so the returned `evidence_envelope` additionally fails `RL-E033`. Validated live: with `actor="driver"` the tool_event is INVALID; with `actor="runtime"` the same record is VALID, which isolates the cause to the argument rather than to the record shape.

SECOND CALL SITE. `host_runner`'s default branch (the `else` arm that runs when no injected `runner` is supplied) also calls `capture_command`, taking the `actor` default of `executor`, which IS legal; it is listed here because it is the other production caller and any fix must consider it.

WHY IT IS LATENT RATHER THAN BREAKING ANYTHING TODAY. The records are never appended to a ledger: `run_suite_check` binds the envelope to `_envelope` and discards it, reading only the out-of-band `stdout`/`stderr` attributes. So nothing validates them at runtime and no run fails. That is exactly why it is worth filing: the invalid values are invisible until someone wires these records to a store, at which point an append refuses.

WHAT THIS ITEM MUST DECIDE, and why it is not a one-line fix. Under a decision that driver runs DO write a ledger, these records must become valid, so the fix is to pass a legal role and a legal evidence kind (`runtime` and `test_report` are the obvious candidates). Under a decision that the ledger is scoped to the `aw run` path, the honest question is whether `run_suite_check` should construct ledger-shaped records at all given it discards them. That decision is plan rdjka2's OQ-01, carried by backlog ye28s6; this item is OQ-02 there and should be acted on after it.

NOT A CODE-PINNING FIX: any test must call `capture_command` and assert on `validate_record`'s findings, never grep the source for the literal argument.
