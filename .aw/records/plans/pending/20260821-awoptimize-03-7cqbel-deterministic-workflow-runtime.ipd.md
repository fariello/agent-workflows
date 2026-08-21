# IPD: Deterministic Workflow Runtime

- Date: 2026-08-21
- Kind: child
- Concern: Move sequencing, persistence, retries, and terminal gates out of model memory into a deterministic resumable runtime.
- Scope: Workflow-run state machine, scheduler, step-packet renderer, interaction gates, resume/retry/cancel behavior, CLI, and focused tests using Orders 01 and 02. No host-specific launcher or model benchmark.
- Status: draft
- Set: awoptimize
- Order: 3
- Highest E allocated: 09
- Author: Codex GPT-5.6 Sol
- Id: 7cqbel

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created to make compliance a runtime property instead of a prompt-length bet.

## Goal

Implement a fail-closed state machine that releases only the next valid bounded work packet, captures tool evidence, pauses at declared human gates, survives interruption, and refuses terminal completion until the ledger's independent predicates pass.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### State machine and packets

- [ ] E-01 Define legal run, phase, step, attempt, evidence, verification, correction, cancellation, and terminal states with a complete transition table and explicit transition authority.
  - Depends on: none
  - Expected outcome: illegal skips, backward transitions, executor terminal transitions, and states lacking prerequisite events are rejected.
  - Execution state: pending
- [ ] E-02 Implement a single-writer state engine that consumes compiled workflows and append-only ledger events, checks dependency DAGs, and releases only runnable steps.
  - Depends on: E-01
  - Expected outcome: two concurrent coordinators cannot release or transition the same run; lock loss fails closed.
  - Execution state: pending
- [ ] E-03 Implement bounded just-in-time packets containing immutable run metadata, current requirements, scope, allowed tools/files, exact action, expected artifact, evidence contract, stop conditions, dependencies, and a short exit checklist.
  - Depends on: E-02
  - Expected outcome: the executor need not retain the monolithic workflow, and packet content has a source-to-requirement trace and size budget.
  - Execution state: pending
- [ ] E-04 Implement packet acknowledgements and outcome envelopes that require structured performed/blocked/failed status, artifact references, and captured tool-event IDs; ignore unsupported claims such as `all tests pass` without evidence IDs.
  - Depends on: E-03
  - Expected outcome: free-form model prose may explain an outcome but cannot mutate durable state.
  - Execution state: pending

### Interaction, recovery, and terminal safety

- [ ] E-05 Implement human decision gates with explicit options, default behavior, timeout policy, noninteractive refusal, and recorded authorization; never synthesize consent.
  - Depends on: E-04
  - Expected outcome: headless runs stop with a stable `needs_input` result before any gated side effect.
  - Execution state: pending
- [ ] E-06 Implement bounded retry and correction states keyed by failure class; preserve failed attempts, prevent evidence reuse after relevant changes, and escalate after the configured limit.
  - Depends on: E-05
  - Expected outcome: retries are observable and cannot loop forever or convert failure to success by repetition.
  - Execution state: pending
- [ ] E-07 Implement resume, cancel, and crash recovery from the ledger, including idempotency keys for deterministic actions and explicit `unknown_outcome` handling for interrupted side effects.
  - Depends on: E-06
  - Expected outcome: restart never silently reruns a potentially completed destructive action and exposes exact recovery choices.
  - Execution state: pending
- [ ] E-08 Implement `aw run start|next|record|resume|cancel|status|finalize` with JSON and agent modes; `finalize` must call Order 02 predicates and require coordinator authority.
  - Depends on: E-07
  - Expected outcome: CLI exit codes distinguish complete, incomplete, blocked, invalid evidence, corrupted ledger, and operational failure.
  - Execution state: pending
- [ ] E-09 Add model-free simulations for every legal/illegal transition, crash boundary, human gate, retry path, dependency branch, packet budget, lock collision, evidence invalidation, and terminal refusal.
  - Depends on: E-08
  - Expected outcome: deterministic fixtures exercise the entire state space before any live model is involved.
  - Execution state: pending

## State ownership

| State change | Authorized actor | Required predicate |
|---|---|---|
| `pending -> runnable` | runtime | dependencies and approvals satisfied |
| `runnable -> running` | runtime | lease acquired and packet emitted |
| `running -> performed|blocked|failed` | runtime from executor envelope | valid actor, attempt, and evidence references |
| `performed -> verifying` | coordinator/runtime | required execution events complete |
| `verifying -> verified|correction_required` | independent verifier via runtime | verifier authority and evidence decision valid |
| any active state -> cancelled | authorized human/coordinator | cancellation event recorded |
| `verified -> complete` | coordinator/runtime | every frozen completion predicate true |

## Project conventions discovered (Step 0)

- Current workflows ask the model to sequence phases and remember exit gates.
- IPD lifecycle already defines fail-closed pre-execution, pre-transition, and post-transition checkpoints.
- Some workflows are interactive; headless hosts cannot supply mid-run answers.
- Existing CLIs use stable exit code separation and agent-oriented output.

## Findings

| Finding | Consequence |
|---|---|
| Long orchestrators still depend on the model loading the next file correctly. | The runtime must choose and render the next packet. |
| A resumed conversation carries confirmation bias and stale summaries. | Durable state must reconstruct from ledger, not conversation memory. |
| Headless sessions may need input after launch. | Preflight and explicit `needs_input` state are required. |
| Process exit 0 means the host completed a turn, not that workflow predicates passed. | Runtime finalization must be a separate call. |

## Proposed changes (ordered, validatable)

1. Freeze states and transition authorities.
2. Implement single-writer scheduling.
3. Render bounded traceable packets.
4. Accept only structured outcomes linked to evidence.
5. Add human gates, retries, resume, cancel, and crash recovery.
6. Expose stable CLI operations and simulate every boundary.

## Deferred / out of scope (with reason)

- Subagent roles and verifier packets belong to Order 04.
- Host command lines and native agent formats belong to Order 05.
- Performance thresholds and live model quality belong to Order 06.
- Production workflow migration belongs to Order 07.

## Scope check

- Over-scope: no direct provider calls, workflow content rewrite, or external mutation.
- Under-scope: state transitions, packets, interaction, recovery, retry, CLI, and simulations are covered.

## Required tests / validation

- Exhaustive transition-table tests and property checks that no unauthorized terminal path exists.
- Crash injection before and after each durable write and side-effect acknowledgement.
- Concurrent coordinator/lease tests.
- Golden packet tests with requirement coverage and byte/token budgets.
- Headless gate and unknown-outcome recovery tests.
- Full suite, leak scan, and machine-output checks.

## Spec / documentation sync

- Publish the transition table, packet contract, exit codes, human-gate behavior, retry policy, and recovery runbook.
- Document that host turn success is not workflow completion.

## Open questions

### OQ-01: SQLite or append-only files as the runtime index?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: the ledger remains authoritative; choose the smallest recoverable index after filesystem locking and portability tests.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: transition-table tests enumerate every state/actor pair and prove all unlisted transitions, executor completion, and missing-prerequisite transitions fail closed.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: DAG scheduling tests release only satisfied steps, concurrent coordinators cannot both lease, lock loss stops progress, and partial ledger state cannot produce a packet.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: golden packets contain every contract field, map all current requirements, omit unrelated bulk context, respect size budgets, and change digest when a bound requirement changes.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: structured performed/blocked/failed envelopes update only legal states; unsupported prose, missing evidence IDs, wrong attempt, and foreign actor are ignored or rejected.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: interactive and headless fixtures prove each choice is recorded, no default consent is invented, timeout follows declared policy, and no gated side effect occurs before authorization.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: retry fixtures preserve attempts, enforce limits, route by failure class, invalidate affected evidence after correction, and escalate rather than looping.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: crash injection at every boundary reconstructs state; idempotent actions do not duplicate; interrupted uncertain side effects enter `unknown_outcome` and require explicit reconciliation.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: command golden tests cover every operation and exit class; `finalize` refuses incomplete/invalid/unauthorized runs and succeeds only after Order 02 predicates pass.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: model-free simulations cover every declared transition, dependency branch, failure, gate, collision, invalidation, and terminal refusal with coverage mapped to the transition table.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: scheduler, packet renderer, persistence, and recovery share the same transition authority.

Requires executed Orders 01 and 02. Do not add host-specific commands or model-specific semantic branches. The runtime must remain usable with a human manually ferrying packets when no native host adapter exists.

Execution contract: path-scoped commits, no push, raw evidence retained, no executor V-items, no broad staging. Terminal transition remains coordinator-owned after independent verification.
