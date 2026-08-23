# IPD: Verifier Roles Clean Packet Procedures and Corrective Routing

- Date: 2026-08-21
- Kind: child
- Concern: Make independent verification an architectural role with least privilege and fresh evidence, not a second prompt in the executor's conversation.
- Scope: Coordinator/executor/investigator/verifier/corrector/human role contracts + the clean verifier packet (frozen requirements + actual diff + raw evidence, no executor conclusion) + verification procedures + corrective-IPD routing. No concurrency/isolation machinery (Order 09).
- Status: approved
- Approval: Gabriele Fariello (human), 2026-08-22
- Set: awoptimize
- Order: 8
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 5hu6bd

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-04 E-01..E-04 into 5 right-sized E-items (roles, clean verifier packet, verification procedures, corrective routing, tests); carries the cross-model-verifier OQ.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. verify_roles.py genuinely absent; role policy is the semantic layer over Order-02 RL-E032. PR-001 (MEDIUM, architecture): the gate declared a dependency on Order 07 (recovery/CLI) that this Order consumes nothing from, needlessly serializing Layer C behind all of Layer B. FIXED: dependency corrected to Order 05 + Orders 01-04 (07 dropped) in the gate, and the orchestrator child-table cell reconciled to `05`. V-01..V-05 map 1:1 with falsifiable evidence. OQ-01 (cross-model verifier) non-blocking, deferred to the benchmark.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.

## Goal

Make independent verification an architectural ROLE with least privilege and fresh, primary-artifact
evidence - not a second prompt in the executor's own conversation. This Order defines the role
contracts, the clean verifier packet (frozen requirements + actual diff + raw evidence, no executor
conclusion prose), the requirement-by-requirement verification procedures, and corrective routing so
findings never vanish into prose. It does not implement context/worktree isolation or concurrency
(Order 09), or host-specific verifier launchers (Order 11).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: roles and packet

- [x] E-01 Define the coordinator, executor, read-only investigator, independent verifier, corrector, and human-approver roles in `agent_workflows/verify_roles.py`, each with explicit inputs, outputs, permissions, state authority, and forbidden actions.
  - Depends on: none
  - Expected outcome: only the coordinator releases work and finalizes; the executor and corrector cannot verify their own work; the verifier cannot mutate product code; forbidden role actions are rejected by policy (consistent with the Order-02 RL-E032 verifier-authorship rule).
  - Execution state: complete
- [x] E-02 Define the clean verifier packet builder: it contains frozen requirements, base/head identity, the actual diff + untracked inventory, a raw-evidence manifest, the declared scope, the test-change diff, prior-attempt metadata, and the verification rubric - and it EXCLUDES the executor's conclusion prose.
  - Depends on: E-01
  - Expected outcome: a golden verifier-packet test includes every primary artifact + frozen requirements, contains no executor verdict prose, binds base/head/worktree, and rejects a missing or mismatched input.
  - Execution state: complete

### Task group 2: procedures and correction

- [x] E-03 Implement the verifier procedures: requirement-by-requirement inspection, scope audit, symbol-wiring check, negative cases, test falsifiability, targeted + full checks, artifact presence, residual search, and evidence validation, each producing an explicit `satisfied|partial|failed|not_verifiable` result with evidence ids.
  - Depends on: E-02
  - Expected outcome: every V-item produces one explicit result with evidence ids; a symbol/negative-case/falsifiability/full-suite/artifact/residual/scope gap blocks completion.
  - Execution state: complete
- [x] E-04 Implement corrective routing: a verifier finding produces either a bounded in-scope correction or an explicit pending corrective-IPD artifact - never disappearing into prose; the original failure is preserved immutably and all invalidated checks are rerun after a correction.
  - Depends on: E-03
  - Expected outcome: each seeded gap creates a correction or corrective artifact, original findings remain immutable, a changed artifact invalidates linked evidence, and all affected checks rerun before any pass.
  - Execution state: complete

### Task group 3: tests

- [x] E-05 Add `tests/test_verify_roles_packet.py` (stdlib unittest): a role/permission/authority matrix with negative tests (every forbidden role action rejected); a verifier-packet golden test (all primary artifacts, no executor prose, base/head bound, missing/mismatched input rejected); a seeded requirement set producing one explicit result per V-item with each gap class blocking completion; corrective-routing fixtures (immutable original, evidence invalidation, rerun). Then run the full serial suite and paste the tail.
  - Depends on: E-04
  - Expected outcome: role/packet/procedure/correction tests pass; the full serial suite is green (pasted).
  - Execution state: complete

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `agy_run.py` performs execution and skeptical audit in the SAME conversation; a prior 11-child rollout (`awlayout`) recorded rosy self-audits followed by independent detection of red suites and real defects. This Order exists to make verification structurally independent.
- The Order-02 ledger already forbids an executor-authored `verifier_decision` (RL-E032); this Order's role policy is the semantic layer over that structural rule.
- `plan-review-long` already allows coordinator-owned, read-only audit lanes; repository decisions prohibit fire-and-forget and keep mutation/ship phases serial.
- Pure/near-pure module shape as in Orders 01-07 (`from __future__ import annotations`, Python 3.9, stdlib-only per D138).

## Findings

| Finding | Consequence |
|---|---|
| Same-session audit shares assumptions and narrative momentum. | It cannot be authoritative verification; the verifier is a distinct role with a fresh packet. |
| Fresh context alone is insufficient if the packet repeats the executor's conclusion. | The verifier packet supplies primary artifacts and OMITS conclusion framing. |
| A verifier finding can quietly evaporate into summary prose. | Corrective routing forces every finding into a bounded correction or an explicit pending artifact, with an immutable original. |

## Proposed changes (ordered, validatable)

1. Freeze role permissions + state authority (E-01).
2. Define the primary-artifact verifier packet (E-02).
3. Implement evidence-first verification procedures (E-03).
4. Implement corrective routing that preserves the original + reruns invalidated checks (E-04).
5. Role/packet/procedure/correction tests + full suite (E-05).

## Deferred / out of scope (with reason)

- Context/worktree ISOLATION + concurrency eligibility + merge-and-revalidate: Order 09.
- Host-specific verifier launchers / fresh-session mechanics: Order 11 (this Order defines the packet + role; Order 11 wires the native launch).
- Live behavior measurements / cross-model verifier evaluation: Orders 12/13 (see OQ-01).
- Distributed coordination across machines: deferred until local orchestration is proven.

## Scope check

- Over-scope: no isolation/worktree machinery, no host launchers, no live providers, no production workflow edits, no release operations.
- Under-scope: none - roles, the clean packet, verification procedures, and corrective routing are covered; Order 09 adds isolation/concurrency on top.

## Required tests / validation

- `tests/test_verify_roles_packet.py`: role-permission + state-authority matrix (forbidden actions rejected); verifier-packet golden (primary artifacts present, executor prose absent, base/head bound, bad input rejected); per-V-item result with each gap class blocking completion; corrective-routing (immutable original, evidence invalidation, rerun).
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean.

## Spec / documentation sync

- Document the role boundaries, verifier independence, the packet contract, and the correction lifecycle. No user-facing README change at this layer.

## Open questions

### OQ-01: Must the verifier identity be a DIFFERENT model?

- Blocking: no
- Status: open
- Owner: benchmark owner
- Resolution or deferral rationale: A fresh context with read-only permissions is the MINIMUM this Order requires (and is sufficient for correctness). Whether to additionally require a DIFFERENT model is a costlier policy whose benefit must be measured; Orders 12/13 (benchmark) compare same-model fresh verification vs cross-model verification before any such policy is adopted. Non-blocking: this Order ships the fresh-context read-only verifier; cross-model is an additive later policy that does not change these interfaces.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted role/permission/authority matrix test output proving every forbidden role action is rejected (executor/corrector cannot self-verify; verifier cannot mutate product code; only coordinator finalizes), consistent with Order-02 RL-E032.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted verifier-packet golden test showing all primary artifacts + frozen requirements present, no executor verdict prose, base/head/worktree bound, and a missing/mismatched input rejected.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted test output where a seeded requirement set produces one explicit `satisfied|partial|failed|not_verifiable` result per V-item with evidence ids, and each gap class (symbol/negative/falsifiability/full-suite/artifact/residual/scope) blocks completion.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted test output showing each seeded gap creates a correction or a pending corrective artifact, the original finding stays immutable, a changed artifact invalidates linked evidence, and all affected checks rerun before a pass.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `tests/test_verify_roles_packet.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 05 (the state machine whose `verified -> complete` edge this Order's roles gate) plus Orders 01-04 upstream (the completion predicate is Order 04). It does NOT depend on Order 07 (recovery/CLI): defining verifier roles/packet/procedures consumes no Order-07 content, so Order 08 may execute once Order 05 lands, in parallel with Orders 06/07. Scope fence: touch only `agent_workflows/verify_roles.py`, the verifier-packet + procedures modules it defines, and `tests/test_verify_roles_packet.py`; do NOT implement context/worktree isolation or concurrency (Order 09), host launchers (Order 11), or live model behavior - if it seems to need more, STOP and report. Product mutation by the verifier is a hard failure; a same-session audit is never authoritative V evidence. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
