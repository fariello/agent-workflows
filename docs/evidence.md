# Evidence layer

Every run records tamper-evident evidence in an append-only ledger. The modules are
`agent_workflows/run_ledger_store.py`, `run_ledger_schema.py`, and `run_evidence.py`.

## The ledger

The run ledger is an append-only JSONL file. Each record carries a sequence number and a
SHA-256 hash chained to the previous record. `RunLedgerStore.verify_chain` walks the chain and
reports any broken link, sequence gap, or unparseable line. `recover` truncates the ledger to
the last intact record when a write was interrupted.

## Provenance envelopes

`build_evidence_envelope` wraps a step's tool events, captured output, and artifact references.
`build_tool_event` and `capture_command` record what ran and what it produced. The environment
is filtered (`filter_environment`) so secret-bearing keys never land verbatim.

## Redaction

`RedactionPolicy` masks sensitive keys and patterns BEFORE a record is appended. If a required
verification payload is redacted such that the check cannot be conclusively made, validation
fails closed (`EV-REDACTION-CONFLICT`) rather than passing on masked data. See
[security.md](security.md) for the evidence-redaction boundary.

## Inspecting evidence

Read-only inspection commands (they make no writes):

```
aw run show <run-id-or-path>
aw run evidence <run-id-or-path>
aw run verify-ledger <run-id-or-path>
```

`aw run show` reports run state, steps, verifier decisions, and completion predicates.
`aw run evidence` lists the captured envelopes and tool events. `aw run verify-ledger` verifies
the hash chain and evidence validity. Add `--agent` or `--json` for machine-readable output.

## Responsibility boundary

The runtime records evidence; it does not decide truth. The verifier reads the evidence and
decides. A redaction that would hide the fact being verified fails the check rather than
letting it pass.

## Limitations

- The ledger proves WHAT was recorded and that it was not altered. It does not prove the work
  was correct; that is the verifier's and the benchmark's job (see
  [verification.md](verification.md), [benchmark.md](benchmark.md)).
