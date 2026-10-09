---
id: utb2qr
created: 20261007
set: runledger
order: 00
topic: [run-ledger, driver, run-recovery]
model: 
kind: findings
status: todo
outcome: none-yet
summary: Analysis and decision on driver run hash-chained ledger and run_recovery reachability
consumed-by: [rdjka2]
---

# Analysis and Decision: Driver Run Hash-Chained Ledger and run_recovery Reachability

- Artifact Id: `utb2qr`
- Set: `runledger` (Order 00)
- Date: 2026-10-07
- Governing Plan: `rdjka2` (from backlog item `ye28s6`)

## 1. Executive Summary and Context

Shipped code in `agent_workflows/runner_shared.py` contains a section header ("retrywire") asserting that:
1. `run_recovery.plan_retry` and `retry_budget_remaining` "REMAIN THE INTENDED LONG-TERM HOME".
2. They are "UNREACHABLE from a driver run".
3. "WHETHER A DRIVER RUN SHOULD WRITE A LEDGER IS STILL OPEN and is NOT decided here ... Nobody may cite this section as a decision to abandon the ledger design."

This framing presents an aspirational long-term architecture as an open decision, while in reality:
- Neither runner driver (`oc_runipd.py` or `agy_runipd.py`) references any ledger symbol.
- Every one of `run_recovery`'s eight public functions requires a `RunEngine` instance.
- No code path anywhere in the package can create a hash-chained `ledger.jsonl` because no writer exists for the mandatory `kind: "run"` root record.
- The driver was forced to build and maintain a complete second implementation of retry semantics (`handle_turn_failure_retry`, `frozen_retry_budget`, `turn_retry_budget_remaining`, `TURN_RETRY_CLASSIFICATION`, etc.) with a disjoint state vocabulary.

The question posed by backlog item `ye28s6` is: should driver runs emit a hash-chained ledger (making `run_engine` and `run_recovery` reachable), or is the ledger scoped to the `aw run` execution path?

This document provides the empirical measurements, the spec-conformance analysis, the true costs of both options, the historical precedents, and a concrete recommendation.

---

## 2. Re-measured Evidence at Executing HEAD (Findings F-01 through F-13)

All measurements below were independently reproduced at HEAD `d4efba10e0a640010c65d664175e3cc40550c731`:

### Finding F-01: Zero `ledger.jsonl` Files Exist
- **Measurement**: `find . -name 'ledger.jsonl' -not -path './.git/*' | wc -l`
- **Observed Result**: `0`
- **Implication**: No execution in this repository has ever written a persistent `ledger.jsonl` outside test fixtures.

### Finding F-02: Neither Driver References Any Ledger Symbol
- **Measurement**: `grep -cE 'run_engine|run_recovery|run_ledger_store|RunLedgerStore|RunEngine|ledger\.jsonl' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py`
- **Observed Result**:
  - `agent_workflows/oc_runipd.py: 0`
  - `agent_workflows/agy_runipd.py: 0`
- **Implication**: The execution paths that actually run (`aw oc run` and `aw agy run`) are completely decoupled from the ledger subsystem.

### Finding F-03: All Eight `run_recovery` Public Functions Require `RunEngine`
- **Measurement**: Inspect signatures of all 8 public functions in `agent_workflows.run_recovery`:
  - `plan_retry(engine, ...)`
  - `retry_budget_remaining(engine, ...)`
  - `resume(engine, ...)`
  - `cancel(engine, ...)`
  - `recover_crash(engine, ...)`
  - `detect_unknown_outcomes(engine, ...)`
  - `reconcile_unknown_outcome(engine, ...)`
  - `correction_required(engine, ...)`
- **Observed Result**: Every single public function takes `engine` as its first positional parameter.
- **Implication**: Without a `RunEngine` (which requires a `RunLedgerStore`), the entire `run_recovery` module is structurally unreachable.

### Finding F-04: Second Retry Implementation in `runner_shared.py`
- **Measurement**: Symbol census in `agent_workflows/runner_shared.py`:
  - `handle_turn_failure_retry`: Present
  - `frozen_retry_budget`: Present
  - `turn_retry_budget_remaining`: Present
  - `TURN_RETRY_CLASSIFICATION`: Present
  - `turn_retry_idempotency_key`: Present
  - `invalidate_turn_evidence`: Present
- **Observed Result**: All 6 symbols exist and operate on `state.json`/`events.jsonl`. The `retrywire` header acknowledges: "this repository normally refuses one".

### Finding F-05: Disjoint State Vocabularies
- **Measurement**: Set intersection of `run_state.ALL_STATES` (11 states) and `runner_shared.TERMINAL_STATES_CANONICAL` (14 states).
- **Observed Result**: Intersection is exactly `{'failed'}`. Furthermore, `run_recovery.plan_retry` raises `NoRetryableStateError` for any step not in `STATE_FAILED` or `STATE_BLOCKED`, neither of which a driver queue item ever holds.

### Finding F-06: Zero Writers of Root `kind: "run"` Record
- **Measurement**: `grep -rn '"kind": "run"' agent_workflows/`
- **Observed Result**: Exactly 0 matches. Every occurrence of `"run"` in relation to `kind` across `agent_workflows/` is a reader or validation refusal (`RL-E041`).
- **Implication**: There is no code in the entire repository that creates the opening record of a ledger.

### Finding F-07: Live Reproduction of `RL-E041` Ledger Creation Refusal
- **Measurement**: Instantiated `RunLedgerStore` against a fresh temporary directory, created `RunEngine` with a valid workflow, and executed `release_step` followed by `start_step` and `record_step_attempt(..., attempt_state='performed')`.
- **Observed Result**:
  - `start_step` raised: `SchemaInvalidRecordError: Schema-invalid record at seq 0: (Finding(code='RL-E041', where='kind', message="first ledger record must be kind 'run'"),)`
  - Files in temporary directory: `['ledger.jsonl.lock']`
  - `ledger.jsonl` exists: `False`
- **Implication**: No code path can create a ledger today. Attempting to record any step attempt on a fresh store fails with `RL-E041` and leaves no ledger file on disk.

### Finding F-08: Product Surface Decoupling
- **Measurement**: `AW_NO_REEXEC=1 python3 -m agent_workflows run start run-abc123 --step S-01`
- **Observed Result**: Exited code `2` with:
  `error: ledger file not found for target 'run-abc123': this reads the hash-chained ledger.jsonl, and no driver run writes one today, so there is nothing here to read rather than something missing from this run. The drivers' own events.jsonl is a different file in a different format and is not a ledger.`

### Finding F-09: `run_recovery` Is Not Dead Code
- **Measurement**: Census of importers across `agent_workflows/`:
  - `run_cli._run_resume` calls `run_recovery.resume` and `detect_unknown_outcomes`, handling `UnknownOutcomeError` and `UNKNOWN_OUTCOME`.
  - `run_cli._run_cancel` calls `run_recovery.cancel`.
  - `set_lifecycle` delegates `resume` to `run_recovery.resume`.
- **Implication**: `run_recovery` is actively consumed by `run_cli` and cannot be deleted or retired.

### Finding F-10: Drivers' `events.jsonl` Is Not a Hash-Chained Ledger
- **Measurement**: Scanned all 126 `append_jsonl` call sites in `runner_shared.py` (125 targeting `run_dir / "events.jsonl"`).
- **Observed Result**:
  - `at` timestamp is present across append sites.
  - Zero append sites pass `seq`, `prev_hash`, `schema_version`, or `parent`.
  - `append_jsonl` writes un-chained JSON Lines and performs `fsync` with no hashing or sequence tracking.

### Finding F-11: Spec `25kzda` Already Governs the Drivers
- **Measurement**: Inspected `agent_workflows/runner_shared.py` `initialize_run_core` signature and inline comments.
- **Observed Result**: Parameters `driver_path` and `labels` are keyword-only with no default, explicitly implementing spec `25kzda` Section 5.3 requirement: "A shared initialization core must receive both that creator module path and the host's label descriptor explicitly from its caller with no defaults".

### Finding F-12: Discarded Records Fail Validation on `run_suite_check`
- **Measurement**: `run_evidence.capture_command('run-abcdef1234', ['echo', 'hello'], actor='driver', evidence_kind='tests')`
- **Observed Result**:
  - `tool_event` fails validation with `RL-E014: unknown actor role 'driver'`.
  - `envelope` fails validation with `RL-E014` and `RL-E033: unknown evidence_kind 'tests'`.
  - Default caller (`host_runner` with defaults `actor="executor"`, `evidence_kind="command"`) validates cleanly `(True, [])`.
- **Implication**: `run_suite_check` produces schema-invalid records and discards them (`_envelope`). Filed as carrier `1g8lbe`.

### Finding F-13: Precedent Analysis
- **Measurement**: Reviewed backlog `sv8z1e` and plan `xipfy1` OQ-03.
- **Observed Result**: Both previous investigations rejected ledger emission for driver runs on cost grounds, choosing actionable error messages and the driver's own `state.json`/`events.jsonl` substrate.

---

## 3. Spec Conformance Analysis (F-11)

Spec `25kzda` ("Canonical runner verb `aw oc run` / `aw agy run`") explicitly defines the contract for driver runs:
1. **Declared Scope**: "the behavior of the single canonical runner verb `aw oc run` / `aw agy run`".
2. **Section 1.2 Step 8**: Requires that the runner "Capture tool calls, outputs, changed paths, commits, and artifacts in a tamper-evident run ledger".
3. **Section 5.1**: Lists "the append-only, hash-chained run ledger" as an admissible completion input.
4. **Section 5.3**: Dictates shared initialization requirements, which `runner_shared.initialize_run_core` already implements to the letter.

Because spec `25kzda` demonstrably governs the runner drivers today, Option (b) cannot be adopted by claiming the spec was meant for a different subsystem. Choosing Option (b) requires acknowledging a divergence from Section 1.2 Step 8 and Section 5.1, which must be formalized through a follow-on spec amendment or an explicit documented divergence.

---

## 4. Two Analyzed Options and Their True Costs

### Option (a): Driver runs emit a hash-chained `ledger.jsonl`

Under this option, the driver is modified to emit a schema-valid, hash-chained `ledger.jsonl` for every run, making `RunEngine` and `run_recovery` reachable.

**True Cost**: This is not an incremental wiring patch; it is a multi-plan program requiring three distinct deliverables:
1. **Ledger Root Verb**: Authoring a ledger-creation mechanism that writes the mandatory `kind: "run"` header record with required digest fields (`workflow_digest`, `requirement_digest`, `repo`, `head`), unlocking the `RunLedgerStore` append guard (`RL-E041`).
2. **Driver Step/Attempt Model**: Mapping driver turns, agent invocations, and verification checks into `RunEngine` steps and step attempts, reconciling the disjoint state vocabularies (F-05) and correcting invalid actor roles / evidence kinds (F-12).
3. **Storage Location Resolution**: Resolving spec `25kzda` Section 6.2's open architectural question ("the durable storage location for run ledgers").

*Carrier*: Filed as `hegwri` (Order 01 program).

### Option (b): The hash-chained ledger is scoped to the `aw run` execution path

Under this option, the repository acknowledges reality: driver runs use their own established `state.json`/`events.jsonl` substrate, while `RunLedgerStore`, `RunEngine`, and `run_recovery` serve the discrete workflow CLI (`aw run` / `aw runs`).

**True Cost**:
1. **Spec Obligation**: Formalizing the divergence from spec `25kzda` Section 1.2 Step 8 and Section 5.1 via a declared follow-on spec amendment.
2. **Prose Reconciliation**: Rewriting the `retrywire` header block in `runner_shared.py` to retire the aspirational claims ("REMAIN THE INTENDED LONG-TERM HOME" and "IS STILL OPEN"), and updating `run_recovery.py` to clarify that it serves the `aw run` path.
3. **Carrier Scoping**: Amending carrier `hegwri` so it remains scoped to the `aw run` path and does not obligate driver wiring.

---

## 5. Precedents as Precedent and Not as an Answer (F-13)

These two decisions (`sv8z1e` and `xipfy1` OQ-03) are presented here strictly as precedent and NOT as an answer to the current question: both chose against the ledger on immediate cost grounds while explicitly declining to settle whether driver runs should ever emit a ledger.

1. **Backlog `sv8z1e`**: When addressing the cryptic failure of `aw run start` against driver runs, making the drivers emit a real `ledger.jsonl` was evaluated and deliberately rejected in favor of actionable error reporting (F-08), leaving the architecture decision open.
2. **Plan `xipfy1` OQ-03 (resolved 2026-09-10)**: When implementing turn failure retry budgets, the maintainer selected Option (b) (spending the budget in the driver's own `state.json`), while explicitly appending: "Nobody may cite this section as a decision to abandon the ledger design."

Both precedents demonstrate that when faced with the cost of wiring the ledger into the drivers, previous implementations consistently selected the lightweight, driver-local solution.

---

## 6. Recommendation and Rationale

The author recommends **Option (b)**: scope the hash-chained ledger to the `aw run` path, acknowledge the driver's `state.json`/`events.jsonl` substrate as canonical for driver runs, and formalize the spec divergence.

### Rationale:
1. **Substrate Stability**: The drivers' existing substrate (`state.json` and `events.jsonl`) has supported thousands of autonomous runs reliably. It provides per-turn crash isolation, worktree containment, and granular telemetry.
2. **Disproportionate Cost of (a)**: Because no writer of `kind: "run"` exists anywhere in the repository, Option (a) requires building an entire orchestration substrate from scratch just to support retry helpers that `runner_shared.py` already implements natively.
3. **Clear Boundary of Responsibility**: `run_recovery` and `RunEngine` are well-suited for discrete, human-stepped workflow execution (`aw run`). Driver runs operate on a queue of autonomous agent turns where worktree sandboxing and git commits provide the primary tamper-evidence and recovery boundaries.
4. **Actionable Follow-on**: Option (b) allows the repository to clean up stale comments immediately, keeps carrier `hegwri` focused on making `aw run` functional, and schedules a tidy spec amendment for `25kzda`.
