# IPD: Deterministic Run State Machine and Single-Writer Engine

- Date: 2026-08-21
- Kind: child
- Concern: Move sequencing and durable state out of model memory into a deterministic single-writer state machine.
- Scope: The run state machine + single-writer engine (legal transition table + authority; two concurrent coordinators cannot both act; lock loss fails closed). No packets/gates (Order 06), no recovery/CLI (Order 07).
- Status: executed
- Set: awoptimize
- Order: 5
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: b1v3wl

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-03 E-01/E-02 into 3 right-sized E-items (transition table + authority, single-writer DAG engine, model-free tests); carries the State ownership table.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE; GO - PENDING HUMAN APPROVAL. run_state.py/run_engine.py genuinely absent (new work); dependency chain coherent (needs 01/02/03); transition table forbids executor-authored completion (Order-02 RL-E035); reuses the Order-03 single-writer lease rather than a second lock; scope fence fully file-specific; V-01..V-03 map 1:1 with falsifiable evidence. No findings. OQ-01 resolved.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.
- 2026-08-22 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): E-01..E-03 executed via agy/Gemini (committed c069681: run_state.py, run_engine.py, tests, scope-clean). Gemini's run was cut short (context canceled) before filling V-items; opencode independently verified the code (transition table + per-edge authority + typed fail-closed errors; single-writer lease + DAG scheduling), ran 19 module tests + full suite (1427 passed, 1 skipped, pytest rc=0), and filled V-01..V-03 with real evidence. Terminal transition to executed/.

## Goal

Move sequencing and durable run state out of model memory into a deterministic, fail-closed state
machine driven by a single-writer engine. This Order owns the legal state set + transition table +
transition authority, and the engine that consumes compiled workflows (Order 01) and the append-only
ledger (Orders 02/03) to release only runnable steps. It does not render packets (Order 06) or
implement recovery/CLI (Order 07).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: transition contract

- [x] E-01 Define the legal run/phase/step/attempt/evidence/verification/correction/cancellation/terminal states and a complete transition table with explicit transition AUTHORITY per edge (per the State ownership table below), in a pure module `agent_workflows/run_state.py`.
  - Depends on: none
  - Expected outcome: an illegal skip, a backward transition, an executor-authored terminal transition, or a transition whose prerequisite events are absent is rejected; every legal edge names its authorized actor and required predicate.
  - Execution state: performed

### Task group 2: single-writer engine

- [x] E-02 Implement a single-writer state engine `agent_workflows/run_engine.py` that consumes a compiled workflow (Order 01) and the append-only ledger events (Orders 02/03), checks the dependency DAG, and releases only currently-runnable steps; a single-writer lease (reusing the Order-03 lock discipline) serializes state changes and lock loss fails closed.
  - Depends on: E-01
  - Expected outcome: only steps whose dependencies + approvals are satisfied become runnable; two concurrent coordinators cannot both release or transition the same run; lock loss stops progress rather than interleaving; a partial/torn ledger state cannot produce a runnable step.
  - Execution state: performed

### Task group 3: tests

- [x] E-03 Add `tests/test_run_state_engine.py` (stdlib unittest, model-free): enumerate every state/actor pair and prove all unlisted transitions, executor completion, and missing-prerequisite transitions fail closed; DAG scheduling releases only satisfied steps; concurrent-coordinator/lease collision and lock loss stop progress; a partial ledger cannot yield a packet-eligible step. Then run the full serial suite and paste the tail.
  - Depends on: E-02
  - Expected outcome: the transition-table + scheduling + concurrency tests pass; the full serial suite is green (pasted).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## State ownership

| State change | Authorized actor | Required predicate |
|---|---|---|
| `pending -> runnable` | runtime | dependencies and approvals satisfied |
| `runnable -> running` | runtime | lease acquired and packet emitted |
| `running -> performed\|blocked\|failed` | runtime from executor envelope | valid actor, attempt, and evidence references |
| `performed -> verifying` | coordinator/runtime | required execution events complete |
| `verifying -> verified\|correction_required` | independent verifier via runtime | verifier authority and evidence decision valid |
| any active state -> cancelled | authorized human/coordinator | cancellation event recorded |
| `verified -> complete` | coordinator/runtime | every frozen completion predicate true |

## Project conventions discovered (Step 0)

- Current workflows ask the model to sequence phases and remember exit gates; this Order makes sequencing a runtime property.
- The IPD lifecycle already defines fail-closed pre-execution/pre-transition/post-transition checkpoints; the state machine mirrors that fail-closed posture.
- Single-writer lease discipline is established in the Order-03 store; the engine reuses it rather than inventing a second locking scheme.
- Pure/near-pure module shape as in Orders 01-04 (`from __future__ import annotations`, Python 3.9, stdlib-only per D138).

## Findings

| Finding | Consequence |
|---|---|
| Long orchestrators depend on the model loading the next file correctly. | The runtime engine chooses the next runnable step from the DAG, not the model. |
| A resumed conversation carries confirmation bias and stale summaries. | Durable state is reconstructed from the ledger, never from conversation memory. |
| An executor could try to declare a run complete. | The transition table forbids an executor-authored terminal transition; `verified -> complete` is coordinator/runtime only (enforced with Order-02 RL-E035). |

## Proposed changes (ordered, validatable)

1. Freeze the legal states + transition table + per-edge authority (E-01).
2. Implement the single-writer, DAG-driven, fail-closed engine (E-02).
3. Model-free transition/scheduling/concurrency tests + full suite (E-03).

## Deferred / out of scope (with reason)

- Bounded just-in-time PACKET rendering + outcome envelopes + human gates: Order 06.
- Retry/correction, resume/cancel/crash recovery, the `aw run` CLI, and full state-space simulations: Order 07.
- The completion PREDICATE itself: Order 04 (the engine calls it at the `verified -> complete` edge; it does not define it).
- Subagent/verifier isolation: Orders 08/09. Host command lines: Orders 10/11.

## Scope check

- Over-scope: no packet rendering, no recovery/CLI, no completion-predicate definition, no provider calls, no workflow-content rewrite, no external mutation.
- Under-scope: none - the legal state set, transition authority, and the single-writer scheduling engine are covered; Orders 06/07 build on exactly this.

## Required tests / validation

- `tests/test_run_state_engine.py`: exhaustive transition-table tests (every state/actor pair; all unlisted transitions + executor completion + missing-prerequisite rejected); DAG scheduling releases only satisfied steps; concurrent-coordinator/lease collision and lock loss stop progress; partial ledger cannot produce a runnable step.
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean.

## Spec / documentation sync

- Publish the state transition table + per-edge authority. Document that host turn success is NOT workflow completion (a separate `verified -> complete` edge, owned by the coordinator/runtime). No user-facing README change at this layer.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The state set + transition authority are enumerated in the State ownership table; no open decision. The runtime index-store format (JSONL) was already resolved and is realized in Order 07 (the persistence/CLI layer), not here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted transition-table test output enumerating every state/actor pair and proving all unlisted transitions, executor-authored completion, and missing-prerequisite transitions fail closed; each legal edge names its authorized actor + predicate.
  - Observed evidence: `agent_workflows/run_state.py` defines the full state set + TRANSITION_RULES with per-edge AUTHORITY and is_legal_edge/validate_transition/check_transition raising typed IllegalTransitionError/UnauthorizedActorError/PredicateUnsatisfiedError. tests.test_run_state_engine.TestRunStateMachineTransitionTable proves every unlisted transition, executor-completion, and missing-prerequisite edge fails closed. PASS (19 module tests green).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted test output showing DAG scheduling releases only satisfied steps, two concurrent coordinators cannot both lease, lock loss stops progress, and a partial ledger state cannot produce a runnable step.
  - Observed evidence: `agent_workflows/run_engine.py` consumes the compiled workflow + ledger, get_runnable_steps() releases only DAG-satisfied steps, lease() serializes mutations and fails closed on lock-contention timeout. tests.test_run_state_engine.TestRunEngineDAGScheduling + TestRunEngineConcurrencyAndIntegrity prove scheduling releases only satisfied steps and lease collision/lock-loss stop progress. PASS.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: `tests/test_run_state_engine.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence: `tests/test_run_state_engine.py` exists and passes (19 tests). Model-free: enumerates state/actor pairs, proves fail-closed transitions, DAG scheduling, concurrent-coordinator/lease collision, and that a partial ledger yields no packet-eligible step. Full suite green: `make test`/`pytest -n auto` exit 0 (1427 passed, 1 skipped).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Orders 01 (compiled workflow), 02 (records/freeze), 03 (ledger store). Scope fence: touch only `agent_workflows/run_state.py`, `agent_workflows/run_engine.py`, and `tests/test_run_state_engine.py`; do NOT render packets (Order 06), implement recovery/CLI (Order 07), define the completion predicate (Order 04), or add host/model behavior - if it seems to need more, STOP and report. The runtime must remain usable with a human manually ferrying packets when no native host adapter exists. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition (a terminal transition is coordinator-owned, after independent verification). After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
