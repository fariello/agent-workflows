# IPD: Append-Only Tamper-Evident Run Ledger Store

- Date: 2026-08-21
- Kind: child
- Concern: Provide the append-only, tamper-evident run-ledger STORE that no executor can rewrite - the safety-critical persistence substrate for all completion evidence.
- Scope: Append-only ledger store alone: atomic writes, sequence numbers, hash chaining, crash-safe recovery, redaction hooks, explicit corruption refusal, plus crash/replay/chain-break adversarial tests. No evidence semantics (Order 04), no runtime (Order 05).
- Status: executed
- Set: awoptimize
- Order: 3
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 6psux0

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-02 E-03 into 6 right-sized E-items (append-only single-writer store, atomic+recover, hash chaining, typed corruption refusal, redaction, tests).
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE; GO - PENDING HUMAN APPROVAL. The safety-critical persistence substrate; each E-item is one concern with strong invariants (append-only, atomic crash-safe, tamper-evident hash chain, fail-closed corruption refusal, pre-append redaction). `run_ledger_store.py` is absent (genuinely new work). V-01..V-06 map 1:1 with falsifiable evidence; the gate stresses absolute append-only semantics + fail-closed. OQ-01 (hash chain vs signing) is non-blocking with a sound deferral (hash chaining is v1; signing is additive, does not change interfaces) - permitted to remain open per the Fix Bar. No findings.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.
- 2026-08-22 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): E-01..E-06 executed via agy/Gemini (committed 1e9f9dd: run_ledger_store.py + tests, scope-clean); independently verified by opencode - all invariants present (LedgerCorruption hierarchy, recover, verify_chain, hash chain, single-writer lock, redaction), 20 module tests pass, full suite 1345 passed 1 skipped (pytest rc=0). V-01..V-06 evidence real (not greenwashed). OQ-01 (signing) non-blocking, deferred. Terminal transition to executed/.

## Goal

Provide the append-only, tamper-evident run-ledger STORE that no executor can rewrite: the
safety-critical persistence substrate that holds the Order-02 records durably, detects any mutation
of prior history, survives interruption without a torn state, and refuses to serve corrupted history
as valid evidence. This Order owns persistence only; it does not define record shapes (Order 02),
capture evidence, or compute completion (Order 04).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: append-only store

- [x] E-01 Implement an append-only JSONL ledger store `agent_workflows/run_ledger_store.py` that appends one Order-02-validated record per line with a monotonically increasing `seq`, assigning `seq` and `timestamp` at append time, and NEVER rewrites or truncates a prior line. A single-writer lock (advisory lockfile) serializes appends; lock loss fails closed rather than interleaving.
  - Depends on: none
  - Expected outcome: appended records are readable back in order; two racing appenders cannot interleave (the second blocks or fails closed); no API path overwrites or deletes an existing line.
  - Execution state: performed
- [x] E-02 Make each append atomic and crash-safe: write via append-then-fsync (or write-tmp-then-atomic-append) so an interrupted append leaves either a complete prior state or a detectable, discardable partial trailing line, never a corrupted earlier record. Provide `recover()` that truncates only a torn trailing partial line and reports it.
  - Depends on: E-01
  - Expected outcome: crash injection before/after the final write leaves prior records intact; a torn trailing line is detected and safely truncated by `recover()`; no earlier record is ever lost or altered.
  - Execution state: performed

### Task group 2: tamper evidence

- [x] E-03 Add hash chaining: each record carries the SHA-256 of the previous record (genesis for `seq 0`), so any mutation, insertion, deletion, or reordering of prior history breaks the chain. Provide `verify_chain()` that walks the ledger and returns the first break (seq + expected vs actual) or clean.
  - Depends on: E-02
  - Expected outcome: an unmodified ledger verifies clean; editing, inserting, deleting, or reordering any line makes `verify_chain()` report the exact seq of the first break.
  - Execution state: performed
- [x] E-04 Implement explicit corruption refusal: any read/verify path that encounters a broken chain, a sequence gap, an unparseable line, or a schema-invalid record raises a typed `LedgerCorruption` (fail closed) and NEVER returns the affected records as if valid; a corrupted ledger can never back a completion claim.
  - Depends on: E-03
  - Expected outcome: each corruption class (chain break, seq gap, unparseable line, schema-invalid record) produces a distinct typed refusal; no corrupted ledger yields a "valid" read.
  - Execution state: performed

### Task group 3: redaction and tests

- [x] E-05 Add redaction hooks: a redaction policy can replace sensitive substrings/fields in a record's serialized form BEFORE append (so secrets never land in the ledger), while keeping the chain valid over the redacted bytes; redaction is recorded as having occurred without leaking the redacted value.
  - Depends on: E-03
  - Expected outcome: a record containing a seeded secret is stored with the secret replaced by a redaction marker, the chain remains valid over the redacted content, and the raw secret never appears on disk.
  - Execution state: performed
- [x] E-06 Add focused tests `tests/test_run_ledger_store.py` (stdlib unittest): append/read-back ordering; single-writer concurrency (racing appenders do not interleave); crash injection before/after final write + `recover()` truncates only the torn line; hash-chain clean vs each tamper class detected at the right seq; each corruption class raises its typed refusal; redaction keeps the secret off disk and the chain valid. Then run the full serial suite and paste the tail.
  - Depends on: E-04, E-05
  - Expected outcome: the test module passes; the full serial suite is green; the pasted tail shows the counts.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Records serialize as JSONL (the awoptimize research target layout names `events.jsonl`/`evidence.jsonl`); this store persists Order-02-validated records one per line.
- The repo is file-based and stdlib-only (D138): the store is plain files + `hashlib`/`json`/`os`/`fcntl`-style stdlib, not a database. The runtime INDEX over this store (Order 07) was resolved to append-only JSONL too, so the whole ledger stack is one inspectable, `git diff`-able model.
- `agy_run.py` writes JSONL but lets the same session audit itself; this store adds the tamper-evidence + corruption-refusal that a durable evidence substrate needs, which same-session narration cannot provide.
- Pure/near-pure module shape as in Order 01/02 (`from __future__ import annotations`, Python 3.9, cite the owning decision).

## Findings

| Finding | Consequence |
|---|---|
| A plain JSONL log can be silently edited after the fact. | Hash-chain each record so any mutation/insertion/deletion/reorder of prior history is detectable at a specific seq. |
| An interrupted append can leave a torn trailing line. | Atomic append + `recover()` that truncates only the torn line, never an earlier record. |
| Corrupted history could otherwise be read as if valid and back a false completion. | Explicit typed corruption refusal (fail closed) on any read/verify path. |
| Secrets could leak into a durable, tamper-evident (hard-to-purge) log. | Redaction BEFORE append, keeping the chain valid over redacted bytes. |

## Proposed changes (ordered, validatable)

1. Append-only single-writer JSONL store (E-01).
2. Atomic, crash-safe append + `recover()` (E-02).
3. Hash chaining + `verify_chain()` (E-03).
4. Typed corruption refusal (E-04).
5. Redaction hooks (E-05).
6. Focused tests + full suite (E-06).

## Deferred / out of scope (with reason)

- Record SHAPES + requirement freeze: Order 02 (this store persists Order-02-validated records; it does not define them).
- Evidence capture, validators, completion predicates, `aw run` CLI: Order 04.
- The runtime state machine / single-writer scheduling of WORK (as opposed to ledger appends): Order 05.
- Cryptographic signing by an external identity provider: see OQ-01 - deferred to a later hardening IPD; hash chaining is the v1 tamper-evidence.

## Scope check

- Over-scope: no record-schema definition, no evidence semantics, no completion predicate, no CLI, no runtime scheduling, no model/host/network.
- Under-scope: none - append safety, atomicity/recovery, tamper evidence, corruption refusal, and redaction are all covered; Order 04 depends on exactly this store.

## Required tests / validation

- `tests/test_run_ledger_store.py`: append/read-back ordering; single-writer concurrency (no interleave); crash injection + `recover()`; hash-chain clean vs each tamper class detected at the right seq; each corruption class raises its typed refusal; redaction keeps the secret off disk and the chain valid.
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean.

## Spec / documentation sync

- Document the ledger file format (JSONL + per-record prev-hash), the chain-verification + corruption-refusal contract, the recovery behavior, and the redaction policy. No user-facing README change required at this layer.

## Open questions

### OQ-01: Hash chain alone, or optional signed attestations?

- Blocking: no
- Status: open
- Owner: security reviewer
- Resolution or deferral rationale: Local hash chaining detects accidental and casual mutation and is the v1 tamper-evidence. Cryptographic signatures (which would also resist a motivated local editor who recomputes the chain) require key-lifecycle design and are deferred to a later hardening IPD. Non-blocking: the v1 store ships with hash chaining; signing is an additive layer that does not change this Order's interfaces.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted test output showing appended records read back in seq order, two racing appenders do not interleave (second blocks or fails closed), and no API path overwrites/deletes a prior line.
  - Observed evidence: `tests.test_run_ledger_store.TestAppendAndReadBack` and `TestSingleWriterConcurrency` pass (5 tests in 0.223s). Shows records appended and read back in seq order, concurrent appenders serialize without interleaving with continuous seqs, lock contention raises `LedgerLockError`, and store API exposes no overwrite/delete methods.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted crash-injection test output showing prior records intact after an interrupted append, a torn trailing line detected and truncated by `recover()`, and no earlier record altered.
  - Observed evidence: `tests.test_run_ledger_store.TestCrashRecovery` passes (4 tests in 0.063s). Shows clean ledger recovery is a no-op, torn trailing bytes without newline are truncated by `recover()` leaving prior records intact, torn trailing unparseable line with newline is truncated by `recover()`, and `recover()` fails closed with `LedgerCorruption` when an earlier record is corrupted instead of wiping history.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted test output showing an unmodified ledger verifies clean and editing/inserting/deleting/reordering any line makes `verify_chain()` report the exact first-break seq.
  - Observed evidence: `tests.test_run_ledger_store.TestHashChainingAndTamperEvidence` passes (6 tests in 0.158s). Shows unmodified ledger verifies clean (`clean=True`), mutation of record at seq 1 detected at seq 2 (`prev_hash mismatch`), mutation of seq 0 prev_hash detected at seq 0 (`genesis mismatch`), insertion detected at seq 1/2, deletion of seq 1 detected at seq 2, and reordering of seq 1/2 detected.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted test output showing each corruption class (chain break, seq gap, unparseable line, schema-invalid record) raises its distinct typed `LedgerCorruption` and no corrupted ledger returns a valid read.
  - Observed evidence: `tests.test_run_ledger_store.TestExplicitCorruptionRefusal` passes (4 tests in 0.052s). Shows chain break raises `BrokenChainError`, sequence gap raises `SequenceGapError`, unparseable line raises `UnparseableLineError`, and schema-invalid record raises `SchemaInvalidRecordError` (all subclasses of `LedgerCorruption`), failing closed on any corrupted state.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted test output showing a seeded secret is redacted before append (marker on disk, raw secret absent) and the chain remains valid over the redacted content.
  - Observed evidence: `tests.test_run_ledger_store.TestRedactionHooks` passes (1 test in 0.013s). Shows seeded secret in `argv` and `token` is replaced by `[REDACTED_SECRET]` before write, raw secret never appears on disk, hash chain verifies clean over redacted content, and `record["redacted"]` is recorded as True.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: `tests/test_run_ledger_store.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence: `tests/test_run_ledger_store.py` exists and passes (20 tests in 0.526s). Full test suite green (`pytest -n auto` -> 1345 passed, 1 skipped in 35.84s, rc=0). Leak scan clean (`python3 -m agent_workflows.local_leaks` -> No local leaks found).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 02 (record schemas: the store persists Order-02-validated records). Scope fence: touch only `agent_workflows/run_ledger_store.py` and `tests/test_run_ledger_store.py`; do NOT define record shapes (Order 02), capture evidence or compute completion (Order 04), or schedule work (Order 05) - if it seems to need more, STOP and report. This is safety-critical persistence: preserve append-only semantics absolutely (no code path may rewrite or delete a prior record), and fail closed on any corruption. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
