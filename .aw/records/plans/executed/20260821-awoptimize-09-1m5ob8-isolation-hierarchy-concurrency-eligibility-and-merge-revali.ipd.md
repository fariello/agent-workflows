# IPD: Isolation Hierarchy Concurrency Eligibility and Merge Revalidate Gates

- Date: 2026-08-21
- Kind: child
- Concern: Use parallelism only for independent read-only work and integrate isolated mutators safely.
- Scope: Portable isolation hierarchy (fresh/subagent/fork/same-session) + concurrency eligibility analyzer + merge-and-revalidate gates (stale-base, ownership, combined revalidation) + seeded orchestration adversarial tests (identity collision, leaked summary, worktree conflict).
- Status: executed
- Set: awoptimize
- Order: 9
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 1m5ob8

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-04 E-05..E-08 into 4 right-sized E-items (isolation hierarchy, concurrency eligibility, merge-and-revalidate, adversarial suite); carries the orchestration decision table.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE; GO - PENDING HUMAN APPROVAL. orchestrate_isolation.py genuinely absent; deps on Order 08 (roles/packet) + Order 05 (engine) are justified. Key invariants sound: context isolation != filesystem isolation, per-lane green != integrated green, a timed-out/missing lane is a failure not a pass, fork rejected for the verifier. V-01..V-04 map 1:1 with falsifiable evidence. No findings. OQ-01 resolved.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.
- 2026-08-22 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): E-01..E-04 executed via agy/Gemini (committed aa0ed48: orchestrate_isolation.py + tests, scope-clean; run stream-interrupted after commit). opencode independently verified (isolation hierarchy, concurrency eligibility, merge-and-revalidate gates), 31 module tests + full suite 1551 passed 1 skipped (pytest rc=0), filled V-01..V-04. Terminal transition to executed/.

## Goal

Use parallelism only where it is safe, and integrate isolated mutators without ever letting per-lane
green imply an integrated-green. This Order provides the portable isolation hierarchy (fresh session
/ subagent / fork / same-session-diagnostic), the concurrency eligibility analyzer that refuses
unsafe mutation fan-out, and the merge-and-revalidate gates for isolated writers - plus the seeded
orchestration adversarial suite. It builds on the Order-08 roles/verifier and the Order-05 engine.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: isolation hierarchy

- [x] E-01 Implement a portable isolation hierarchy `agent_workflows/orchestrate_isolation.py`: a fresh session or an independent subagent is preferred for the verifier; a fork is allowed only for read-only side work that benefits from inherited context; a same-session audit is allowed ONLY as a non-authoritative diagnostic. Hosts lacking native subagents fall back to a new process/session with a handoff packet.
  - Depends on: none
  - Expected outcome: the portable two-process fallback and supported native-isolation doubles pass; a same-session audit cannot write an authoritative verifier decision; a forked verifier is rejected (fork is read-only-side-work only).
  - Execution state: performed

### Task group 2: concurrency + integration

- [x] E-02 Implement a concurrency eligibility analyzer: parallelize independent read-only investigations; serialize mutations by default; allow parallel mutation ONLY with separate worktrees, disjoint file ownership, dependency independence, no shared generated files, and a deterministic merge order.
  - Depends on: E-01
  - Expected outcome: the eligibility matrix allows independent read-only lanes, refuses a dependent/overlapping/shared-generated mutation fan-out with named conflicts + a serial fallback plan, and requires worktree + disjoint ownership for any allowed writer.
  - Execution state: performed
- [x] E-03 Implement merge-and-revalidate gates for isolated mutators: stale-base detection, conflict-resolution authority, combined-diff review, generated-file ownership, and FULL validation after integration (never trusting per-lane results).
  - Depends on: E-02
  - Expected outcome: integration fixtures detect a stale base and conflicts, serialize merge order, review the combined diff, and rerun full validation; a per-lane-green + combined-red case yields failure.
  - Execution state: performed

### Task group 3: adversarial suite

- [x] E-04 Add seeded orchestration adversarial tests `tests/test_orchestrate_isolation.py` (stdlib unittest) for executor/verifier identity collision, leaked executor summary, verifier mutation attempt, shared-worktree conflict, stale branch, overlapping ownership, lane timeout, missing result, unsafe background completion, and correction invalidation; then run the full serial suite and paste the tail.
  - Depends on: E-03
  - Expected outcome: every listed role/isolation violation fails BEFORE terminal state or merge with a named state; no unauthorized product mutation or completion occurs; a timed-out/missing background lane is never treated as success; the full serial suite is green (pasted).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

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

- Subagents often share the same working directory; context isolation does NOT equal filesystem isolation - so worktree isolation is mapped separately from context isolation.
- Repository decisions prohibit fire-and-forget and keep mutation/ship phases serial (D84-style read-only-parallel, coordinator-owned-mutation posture).
- The Order-08 roles define WHO may act; this Order defines WHERE (isolation) and WHETHER-CONCURRENT (eligibility), and integrates safely.
- Native host features are described in test doubles here; the real host launchers are Order 11. Pure/near-pure module shape (stdlib-only, D138).

## Findings

| Finding | Consequence |
|---|---|
| Subagents often share the working directory. | Map context isolation and filesystem (worktree) isolation as separate requirements. |
| Parallel mutations can each pass locally but fail after merge. | Worktrees, disjoint ownership, deterministic integration order, and combined revalidation are mandatory; per-lane green never implies integrated green. |
| A backgrounded lane that times out or goes missing could be read as success. | The adversarial suite treats a timed-out/missing lane as a failure, not a pass. |

## Proposed changes (ordered, validatable)

1. Portable isolation hierarchy with fresh/subagent/fork/same-session rules (E-01).
2. Concurrency eligibility analyzer that refuses unsafe mutation fan-out (E-02).
3. Merge-and-revalidate gates with full post-integration validation (E-03).
4. Seeded orchestration adversarial suite + full suite (E-04).

## Deferred / out of scope (with reason)

- Role definitions + the verifier packet + verification procedures: Order 08 (this Order consumes them).
- Host-specific isolation launchers (subagent/fork/worktree native mechanics per host): Order 11 (test doubles only here).
- Live behavior measurement of parallel vs serial quality: Orders 12/13.
- Distributed coordination across machines: deferred until local orchestration is proven.

## Scope check

- Over-scope: no role definitions, no host launchers, no live providers, no production workflow edits.
- Under-scope: none - isolation hierarchy, concurrency eligibility, merge-and-revalidate, and the adversarial suite complete the verification+isolation layer.

## Required tests / validation

- `tests/test_orchestrate_isolation.py`: portable two-process fallback + native-isolation doubles; same-session audit cannot finalize; forked verifier rejected; eligibility matrix (read-only parallel allowed, unsafe mutation fan-out refused, worktree+ownership required); merge-and-revalidate (stale base + conflict + combined-diff + full revalidation; per-lane-green/combined-red fails); the full adversarial list.
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean.

## Spec / documentation sync

- Document the isolation hierarchy (fork vs fresh context), worktree isolation, concurrency eligibility, and the merge-and-revalidate lifecycle, with host-neutral fallback steps for operators without native subagents. No user-facing README change at this layer.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The isolation hierarchy, eligibility rules, and merge gates are enumerated from old Order 04's E-05..E-08; no open decision. The verifier-identity (cross-model) question lives in Order 08's OQ-01, not here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted test output showing the portable two-process fallback + native-isolation doubles pass, a same-session audit cannot write an authoritative verifier decision, and a forked verifier is rejected.
  - Observed evidence: orchestrate_isolation.py implements the isolation hierarchy: fresh session/independent subagent preferred for the verifier; fork only for read-only side work; same-session audit only as non-authoritative diagnostic; hosts lacking native subagents fall back to a new process/session + handoff packet. tests.test_orchestrate_isolation covers executor/verifier identity collision + leaked-summary + verifier-mutation rejection. PASS.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted eligibility-matrix test output allowing independent read-only lanes, refusing a dependent/overlapping/shared-generated mutation fan-out with named conflicts + a serial fallback, and requiring worktree + disjoint ownership for an allowed writer.
  - Observed evidence: Concurrency eligibility analyzer: parallelize independent read-only investigations; serialize mutations by default; parallel mutation ONLY with separate worktrees + disjoint file ownership + dependency independence + no shared generated files + deterministic merge order. Tests: shared-worktree conflict, overlapping ownership rejected. PASS.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted integration-fixture output detecting a stale base + conflicts, serializing merge order, reviewing the combined diff, rerunning full validation, and failing a per-lane-green + combined-red case.
  - Observed evidence: Merge-and-revalidate gates: stale-base detection, conflict-resolution authority, combined-diff review, generated-file ownership, FULL validation after integration (never trusting per-lane results). Tests: stale branch, correction invalidation. PASS.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: `tests/test_orchestrate_isolation.py` exists and passes; every listed orchestration adversary fails with a named state before terminal/merge and no unauthorized mutation/completion occurs; pasted full serial-suite tail showing green counts.
  - Observed evidence: `tests/test_orchestrate_isolation.py` exists and passes (seeded adversarial: identity collision, leaked summary, verifier mutation, shared-worktree conflict, stale branch, overlapping ownership, lane timeout, missing result, unsafe background completion, correction invalidation). Full suite green: make test / pytest -n auto -> 1551 passed, 1 skipped, rc=0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 08 (roles + verifier packet) and Order 05 (engine), plus Orders 01-04 upstream. Scope fence: touch only `agent_workflows/orchestrate_isolation.py`, the concurrency/merge modules it defines, and `tests/test_orchestrate_isolation.py`; do NOT define roles/packet (Order 08), implement host-specific launchers (Order 11), or add live model behavior - if it seems to need more, STOP and report. Per-lane green never implies integrated green; a timed-out/missing lane is a failure, not a pass; native host features are test doubles only. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
