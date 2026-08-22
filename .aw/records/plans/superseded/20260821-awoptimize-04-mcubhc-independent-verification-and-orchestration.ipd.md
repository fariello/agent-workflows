RETIRED 2026-08-21: superseded by the awoptimize re-scope (right-sizing into smaller child IPDs; see the re-scope proposal and DECISIONS). This old Order is resplit into new Orders 08, 09.

# IPD: Independent Verification and Orchestration

- Date: 2026-08-21
- Kind: child
- Concern: Separate coordination, execution, and verification so completion claims are checked in an isolated context against actual state.
- Scope: Role contracts, verifier packet, subagent/session/worktree policy, correction loop, portable fallback, and focused orchestration tests. No host-specific adapter files or live benchmark execution.
- Status: superseded
- Set: awoptimize
- Order: 4
- Highest E allocated: 08
- Author: Codex GPT-5.6 Sol
- Id: mcubhc

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created in response to repeated same-session self-audit false positives recorded in the repository.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Role separation (coordinator/executor/verifier), the clean verifier packet that excludes executor conclusion prose, the fork-rejected-for-verifier rule, and the worktree/ownership/merge-revalidate concurrency gates are well-reasoned and directly answer the awlayout same-session-audit failure. Portable two-process fallback keeps it host-neutral. Size assessment standard (correct). OQ-01 (cross-model verifier) is non-blocking and correctly deferred to the Order 06 benchmark. No blocking open questions.
- 2026-08-21 approved (Gabriele Fariello, --by-human): human sign-off recorded; part of the approved foundational scope (Orders 00-04). Ready to execute via /ipd-lifecycle in dependency order (after Orders 01-03).

## Goal

Make independent verification an architectural role with least privilege and fresh evidence, not a second prompt in the executor's conversation. Define when isolation, forking, background execution, and worktrees are appropriate without making any one host feature mandatory.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Roles and verifier contract

- [ ] E-01 Define coordinator, executor, read-only investigator, independent verifier, corrector, and human approver roles with explicit inputs, outputs, permissions, state authority, and forbidden actions.
  - Depends on: none
  - Expected outcome: only the coordinator releases work and finalizes; executor and corrector cannot verify themselves; verifier cannot mutate product code.
  - Execution state: pending
- [ ] E-02 Define a clean verifier packet containing frozen requirements, base/head identity, actual diff and untracked inventory, raw evidence manifest, declared scope, test-change diff, prior attempt metadata, and verification rubric without executor conclusion prose.
  - Depends on: E-01
  - Expected outcome: verifier judgments are grounded in primary artifacts and do not inherit the executor's framing.
  - Execution state: pending
- [ ] E-03 Implement verifier procedures for requirement-by-requirement inspection, scope audit, symbol wiring, negative cases, test falsifiability, targeted and full checks, artifact presence, residual search, evidence validation, and explicit satisfied/partial/failed/not-verifiable results.
  - Depends on: E-02
  - Expected outcome: every V-item produces a decision and evidence IDs; any gap blocks completion.
  - Execution state: pending
- [ ] E-04 Implement corrective-IPD or bounded-correction routing so verifier findings never disappear into prose; preserve original failure and rerun all invalidated checks after corrections.
  - Depends on: E-03
  - Expected outcome: safe in-scope corrections are traceable and out-of-scope gaps create an explicit pending artifact.
  - Execution state: pending

### Context and concurrency policy

- [ ] E-05 Implement a portable isolation hierarchy: fresh session or independent subagent preferred for verifier; fork only for read-only side work that benefits from inherited context; same-session audit allowed only as non-authoritative diagnostic.
  - Depends on: E-04
  - Expected outcome: hosts lacking native subagents still run via a new process/session, while native isolation is exploited only through adapters.
  - Execution state: pending
- [ ] E-06 Implement a concurrency eligibility analyzer: parallelize independent read-only investigations; serialize mutations by default; allow parallel mutation only with separate worktrees, disjoint file ownership, dependency independence, no shared generated files, and deterministic merge order.
  - Depends on: E-05
  - Expected outcome: unsafe mutation fan-out is refused with named conflicts and a serial fallback plan.
  - Execution state: pending
- [ ] E-07 Implement merge-and-revalidate gates for isolated mutators, including stale-base detection, conflict resolution authority, combined-diff review, generated-file ownership, and full validation after integration.
  - Depends on: E-06
  - Expected outcome: per-lane green results never imply the integrated branch is green.
  - Execution state: pending
- [ ] E-08 Add seeded orchestration tests for executor/verifier identity collision, leaked executor summary, verifier mutation attempt, shared-worktree conflict, stale branch, overlapping ownership, lane timeout, missing result, unsafe background completion, and correction invalidation.
  - Depends on: E-07
  - Expected outcome: role and isolation violations fail before terminal state or merge.
  - Execution state: pending

## Orchestration decision table

| Work shape | Context | Concurrency | Write policy |
|---|---|---|---|
| One bounded dependent implementation | current or fresh executor | serial | scoped writer |
| Large read-only inventory | isolated investigators | parallel allowed | no product writes |
| Independent implementation lanes | fresh agents in worktrees | conditional parallel | disjoint owners, serial integration |
| Verification | fresh verifier context | after execution | read-only product tree; ledger decision only |
| Same-session skeptical audit | inherited context | serial | diagnostic only, never completion gate |
| Release or destructive mutation | coordinator plus human gate | serial | explicit authority and rollback |

## Project conventions discovered (Step 0)

- `plan-review-long` already allows coordinator-owned, read-only audit lanes.
- Repository decisions prohibit fire-and-forget and keep mutation/ship phases serial.
- `agy_run.py` performs execution and skeptical audit in the same conversation.
- A prior 11-child rollout recorded rosy self-audits followed by independent detection of red suites and real defects.

## Findings

| Finding | Consequence |
|---|---|
| Same-session audit shares assumptions and narrative momentum. | It cannot be authoritative verification. |
| Fresh context alone is insufficient if the packet repeats the executor's conclusion. | Supply primary artifacts and omit conclusion framing. |
| Subagents often share the same working directory. | Context isolation does not equal filesystem isolation. |
| Parallel mutations can each pass locally but fail after merge. | Worktrees, ownership, integration order, and combined revalidation are mandatory. |

## Proposed changes (ordered, validatable)

1. Freeze role permissions and state authority.
2. Define a primary-artifact verifier packet.
3. Implement evidence-first verification and corrective routing.
4. Add portable fresh-context fallback and guarded native isolation.
5. Analyze concurrency eligibility and gate integration.
6. Prove refusal behavior with seeded orchestration failures.

## Deferred / out of scope (with reason)

- Concrete Claude, Gemini, Kiro, OpenCode, Codex, or agy definitions belong to Order 05.
- Live behavior measurements belong to Order 06.
- Product workflow migration belongs to Order 07.
- Distributed coordination across machines is deferred until local orchestration is proven.

## Scope check

- Over-scope: no live providers, production workflow edits, or release operations.
- Under-scope: roles, verifier packets, corrections, isolation hierarchy, concurrency, integration, and adversarial tests are covered.

## Required tests / validation

- Role-permission and state-authority matrix tests.
- Seeded false-completion suite where the independent verifier must detect every planted gap.
- Same-session audit ablation retained as non-authoritative comparison.
- Worktree concurrency fixtures with overlaps, stale bases, generated files, and combined regressions.
- Portable no-subagent fallback test using two clean local processes and a handoff packet.
- Full suite and leak scan.

## Spec / documentation sync

- Document role boundaries, verifier independence, fork versus fresh context, worktree isolation, concurrency eligibility, and correction lifecycle.
- Include host-neutral fallback steps for operators without native subagents.

## Open questions

### OQ-01: Must verifier identity be a different model?

- Blocking: no
- Status: open
- Owner: benchmark owner
- Resolution or deferral rationale: a fresh context with read-only permissions is the minimum. Order 06 will compare same-model fresh verification with cross-model verification before adding a costlier policy.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a complete role/permission/transition matrix plus negative tests proving every forbidden role action is rejected by runtime or ledger policy.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: verifier packet golden test includes all primary artifacts and frozen requirements, excludes executor verdict prose, binds base/head/worktree, and rejects missing or mismatched inputs.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: seeded requirements produce one explicit verifier result per V-item with evidence IDs; symbol, negative-case, falsifiability, full-suite, artifact, residual, and scope gaps block completion.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: each seeded gap creates a correction or corrective IPD, original findings remain immutable, changed artifacts invalidate evidence, and all affected checks rerun before pass.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: portable two-process fallback and supported native-isolation doubles pass; same-session audit cannot write authoritative verifier decisions; forked verifier use is rejected.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: eligibility matrix allows independent read-only lanes, refuses dependent/overlapping/shared-generated mutation, and requires worktree plus disjoint ownership for allowed writers.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: integration fixtures detect stale base and conflicts, serialize merge order, review combined diff, and rerun full validation; per-lane green plus combined red yields failure.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: all listed orchestration adversaries fail with named states, no unauthorized product mutation or completion occurs, and timed-out/missing background lanes are not treated as success.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: role authority, isolation, verification, correction, and concurrency policy form one safety boundary.

Requires executed Orders 01 through 03. Native host features may be described in test doubles only; portable semantics must work with separate processes and files. Do not accept a same-session audit as V evidence.

Execution contract: path-scoped commits, no push, no broad staging, raw evidence retained. Product mutation by the verifier is a hard failure. Terminal transition remains coordinator-owned.
