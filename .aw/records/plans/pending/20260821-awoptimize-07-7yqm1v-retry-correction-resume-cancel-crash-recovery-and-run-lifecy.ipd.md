# IPD: Retry Correction Resume Cancel Crash Recovery and Run Lifecycle CLI

- Date: 2026-08-21
- Kind: child
- Concern: Make a run resumable, retry-bounded, and crash-safe, and expose the run lifecycle through the CLI.
- Scope: Bounded retry/correction states + resume/cancel/crash recovery from the ledger (idempotency keys, unknown_outcome) + aw run start|next|record|resume|cancel|status|finalize + model-free simulations of the whole state space.
- Status: approved
- Approval: Gabriele Fariello (human), 2026-08-22
- Set: awoptimize
- Order: 7
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 7yqm1v

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-03 E-06..E-09 into 4 right-sized E-items (bounded retry/correction, resume/cancel/crash recovery, aw run lifecycle CLI, model-free full-state-space simulations); carries the resolved JSONL runtime-index OQ. E-03 records the `aw run` group ownership (EXTENDS Order 04's group) per the Layer-A PR-001 resolution.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. run_recovery.py genuinely absent; the aw run group-ownership resolution (EXTEND Order 04's group, do not re-register) is coherent and confirmed. PR-002 (LOW): the `aw run` CLI module was unnamed in E-03 and the scope fence; FIXED by naming `agent_workflows/run_cli.py` (the Order-04-owned module) in both. Recovery invariants sound (idempotency + unknown_outcome, no silent rerun; predicate-gated coordinator-only finalize). V-01..V-04 map 1:1 with falsifiable evidence. OQ-01 (runtime index = JSONL) resolved.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.

## Goal

Make a run bounded-retryable, resumable, and crash-safe, and expose the whole run lifecycle through
the CLI - so a run survives interruption, never loops forever, never silently reruns a destructive
action, and can only be finalized through the Order-04 completion predicate under coordinator
authority. This Order closes out the runtime layer on top of the Order-05 engine and Order-06
packets/gates.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: retry and correction

- [ ] E-01 Implement bounded retry + correction states keyed by failure class in `agent_workflows/run_recovery.py`: preserve every failed attempt in the ledger, prevent reuse of evidence after a relevant change, and escalate after the configured retry limit rather than looping.
  - Depends on: none
  - Expected outcome: retries are observable (each attempt preserved), a retry cannot convert failure to success by mere repetition, evidence is invalidated after a relevant change, and the run escalates once the limit is reached.
  - Execution state: pending

### Task group 2: resume, cancel, crash recovery

- [ ] E-02 Implement resume/cancel/crash recovery reconstructing run state from the ledger, with idempotency keys for deterministic actions and an explicit `unknown_outcome` state for a side effect interrupted mid-flight.
  - Depends on: E-01
  - Expected outcome: crash injection at every durable-write / side-effect boundary reconstructs the correct state on restart; an idempotent action is not duplicated; an interrupted uncertain side effect enters `unknown_outcome` and requires explicit reconciliation rather than a silent rerun.
  - Execution state: pending

### Task group 3: run lifecycle CLI

- [ ] E-03 EXTEND the existing `aw run` command group (created by Order 04, which owns the parser-group registration) with the mutating `start|next|record|resume|cancel|status|finalize` subcommands; ADD to the group, do NOT re-register it. Wire via `agent_workflows/run_cli.py` (the module Order 04 created and `agent_workflows/cli.py` registers); human + JSON/agent modes; the runtime INDEX over the ledger is append-only JSONL (per OQ-01); `finalize` calls the Order-04 completion predicate and requires coordinator authority.
  - Depends on: E-02
  - Expected outcome: the seven lifecycle subcommands are added to the Order-04-created `aw run` group with no duplicate-group registration; each has stable behavior and ANSI-free machine output; exit codes distinguish complete / incomplete / blocked / invalid-evidence / corrupted-ledger / operational-failure; `finalize` refuses an incomplete/invalid/unauthorized run and succeeds only after the Order-04 predicates pass.
  - Execution state: pending

### Task group 4: full state-space simulations

- [ ] E-04 Add model-free simulations `tests/test_run_recovery_cli.py` (stdlib unittest) covering every legal/illegal transition, crash boundary, human gate, retry path, dependency branch, packet budget, lock collision, evidence invalidation, and terminal refusal, mapped to the Order-05 transition table; then run the full serial suite and paste the tail.
  - Depends on: E-03
  - Expected outcome: deterministic fixtures exercise the entire runtime state space before any live model is involved; coverage maps to the transition table; the full serial suite is green (pasted).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Durable state is reconstructed from the ledger (Orders 02/03), never from conversation memory, so resume/crash-recovery reads the ledger rather than a chat summary.
- Process exit 0 means the host completed a turn, not that workflow predicates passed; `finalize` is therefore a SEPARATE call that runs the Order-04 completion predicate under coordinator authority.
- Repo CLIs use stable exit-code separation and ANSI-free agent output (mirrors `aw ipd lint`, `aw workflow`); `aw run` follows suit.
- The runtime index over the ledger is append-only JSONL (OQ-01, resolved), consistent with the Order-03 file-based store; no database dependency (D138).

## Findings

| Finding | Consequence |
|---|---|
| Retries can loop or launder a failure into a pass by repetition. | Bound retries by failure class, preserve every failed attempt, and escalate at the limit. |
| An interrupted side effect could be silently rerun on restart. | Idempotency keys + an explicit `unknown_outcome` state that requires reconciliation, never a silent rerun. |
| Process exit 0 is not workflow completion. | `finalize` is a distinct CLI call gated on the Order-04 completion predicate + coordinator authority. |
| A resumed run must not trust stale conversation state. | Recovery reconstructs from the ledger; the JSONL index is a rebuildable cache, not authoritative. |

## Proposed changes (ordered, validatable)

1. Bounded retry + correction keyed by failure class (E-01).
2. Resume/cancel/crash recovery with idempotency + `unknown_outcome` (E-02).
3. The `aw run` lifecycle CLI with a JSONL index and predicate-gated `finalize` (E-03).
4. Model-free full-state-space simulations + full suite (E-04).

## Deferred / out of scope (with reason)

- The state machine + scheduling engine: Order 05 (this Order recovers/retries/finalizes over it).
- Packet rendering + outcome envelopes + human gates: Order 06.
- The completion PREDICATE definition + evidence capture: Order 04 (`finalize` calls it).
- Verifier isolation: Orders 08/09. Host command lines / native agents: Orders 10/11.

## Scope check

- Over-scope: no state-machine definition, no packet rendering, no completion-predicate definition, no provider calls, no host files.
- Under-scope: none - retry/correction, resume/cancel/crash recovery, the run CLI, and full-state-space simulations complete the runtime layer.

## Required tests / validation

- `tests/test_run_recovery_cli.py`: retry fixtures (attempts preserved, limit enforced, class-routed, no repetition-to-success, evidence invalidated after change); crash injection at every boundary + idempotency + `unknown_outcome`; CLI golden tests (every subcommand + exit class; `finalize` refuses incomplete/invalid/unauthorized, succeeds only after Order-04 predicates); model-free simulations covering the whole transition table.
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean; machine-output ANSI checks.

## Spec / documentation sync

- Publish the retry policy, the recovery runbook (resume/cancel/`unknown_outcome`), the `aw run` command reference + exit codes, and the runtime-index (JSONL) format. Reiterate that host turn success is not workflow completion.

## Open questions

### OQ-01: SQLite or append-only files as the runtime index?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED to append-only JSONL files (2026-08-21, /plan-review with the maintainer). The Order-02/03 ledger remains authoritative; the runtime index is a rebuildable per-run cache over it (dozens of records), so SQLite's query/locking advantages are largely wasted while its opacity fights the repo's file-based, `cat`/`git diff`-inspectable model; the engine already has single-writer leases (Order 05). JSONL needs no dependency (D138) and matches the research target layout. `sqlite3` (stdlib) could be revisited only if large cross-run queries emerge, which would belong to the benchmark harness (Orders 12/13), not the runtime.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted retry-fixture output showing attempts preserved, the limit enforced, routing by failure class, evidence invalidated after a relevant change, and escalation rather than an infinite loop or repetition-to-success.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted crash-injection output showing correct state reconstruction at every boundary, no duplication of idempotent actions, and an interrupted uncertain side effect entering `unknown_outcome` requiring explicit reconciliation.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted CLI golden output covering every `aw run` subcommand + exit class, no ANSI in machine modes, the JSONL index rebuilt from the ledger, and `finalize` refusing incomplete/invalid/unauthorized runs while succeeding only after the Order-04 predicates pass.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `tests/test_run_recovery_cli.py` exists and passes; the model-free simulations cover every declared transition/branch/failure/gate/collision/invalidation/terminal-refusal with coverage mapped to the transition table; pasted full serial-suite tail showing green counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Orders 05 (engine) and 06 (packets/gates), plus Orders 01-04 upstream. Scope fence: touch only `agent_workflows/run_recovery.py`, `agent_workflows/run_cli.py` (the Order-04-owned `aw run` CLI module, EXTENDED here - add subcommands, do not re-register the group) + its wiring in `agent_workflows/cli.py`, and `tests/test_run_recovery_cli.py`; do NOT define the state machine (Order 05), render packets (Order 06), or define the completion predicate (Order 04) - if it seems to need more, STOP and report. Never silently rerun a potentially-completed destructive action (use `unknown_outcome` + reconciliation); `finalize` is coordinator-authority-only and predicate-gated. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
