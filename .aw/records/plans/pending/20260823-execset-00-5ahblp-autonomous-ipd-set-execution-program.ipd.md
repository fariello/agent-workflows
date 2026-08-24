# IPD: Autonomous IPD Set Execution Program

- Date: 2026-08-23
- Kind: orchestrator
- Concern: Execute complete approved IPD Sets with maximal safe parallelism and almost no interruption.
- Scope: Set planning, decision/defer records, scheduler, model routing, host launchers, workflow/skill packaging, and conformance.
- Status: approved
- Set: execset
- Order: 0
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: 5ahblp
- Approval: 2026-08-24, human ("approved. go."): status set to approved

## Workflow history
- 2026-08-24 approved (aw set, --by-human): status set to approved
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-005 (added full execution contract to orchestrator gate). Reuse premise verified: awoptimize Orders 00-18 present in executed/.
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created from repository and cross-host investigation at `05910e16ca9aa005b8bb76cf789b5c17d5dd7dcc`.

## Goal

Deliver `/exec-set`, backed by a deterministic coordinator that executes every safely runnable part of an approved IPD Set, records autonomous choices and deferred questions, parallelizes provably independent work, and asks the human only under the exact two-part stop rule.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Freeze the cross-plan contract

- [ ] E-01 Approve the hard-stop predicate, child-STOP containment, partial/deferred terminal semantics, durable record strategy, dependency model, model routing, and host support policy from research `<mqqk8e>`.
  - Depends on: none
  - Expected outcome: Orders 01-05 have no unresolved contract decision.
  - Execution state: pending

### Material change 2: Execute the children

- [ ] E-02 Execute Orders 01-05 in dependency order; Orders 01 and 02 may run concurrently, then 03, 04, and 05.
  - Depends on: E-01
  - Expected outcome: one end-to-end, resumable Set executor exists with generated adapters.
  - Execution state: pending

### Material change 3: Prove release readiness

- [ ] E-03 Require adversarial no-stop, parallel-conflict, greenwashing, crash/recovery, cross-host, lifecycle, and full-suite evidence before release.
  - Depends on: E-02
  - Expected outcome: no model prose, worker exit code, or unsupported host claim can falsely complete a Set.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File | Purpose | Depends on |
| --- | --- | --- | --- |
| 01 | `20260823-execset-01-iy1a2g-ipd-set-graph-compiler-and-execution-manifest.ipd.md` | Compile Sets and E-items into a validated graph/manifest. | none |
| 02 | `20260823-execset-02-3m4e54-deferred-questions-autonomous-decisions-and-skip-records.ipd.md` | Add records and the exact stop/defer policy. | none |
| 03 | `20260823-execset-03-m2wwns-parallel-scheduler-worktree-integration-and-model-routing.ipd.md` | Schedule, isolate, integrate, validate, and resume. | 01, 02 |
| 04 | `20260823-execset-04-31744f-host-session-adapters-and-capability-gated-launchers.ipd.md` | Launch fresh workers across supported hosts. | 03 |
| 05 | `20260823-execset-05-2h7777-exec-set-workflow-skill-shims-and-conformance-tests.ipd.md` | Expose `/exec-set`, generate wrappers, document, and prove parity. | 04 |

## Completion criteria (the whole Set is done only when)

- `/exec-set <set-id>` runs the internal planner automatically and keeps draining runnable work.
- `hard_stop = needs_human AND no_robust_decision AND cannot_defer_subgraph AND cannot_defer_ipd`, evaluated only after independent work is drained.
- Deferred work produces a partial result, durable walkthrough, and attention-visible blocked backlog item; it is never marked executed.
- Parallel writers use isolated worktrees, disjoint leases, deterministic integration, and combined-HEAD validation.
- Coding/prose/verifier roles use operator-configured, host-specific model bindings; unsupported capability evidence fails closed.

## Cross-IPD validation

- Reuse existing `run_*`, `orchestrate_isolation`, `verify_roles`, `host_capability_registry`, `host_adapters`, `ipd_lint`, and lifecycle code; do not fork equivalents.
- Ensure the coordinator alone owns the ledger, main worktree, IPD evidence/checkmarks, integration, and terminal transitions.
- Validate existing Sets without new metadata by safe legacy inference; ambiguity serializes instead of prompting.

## Deferred / out of scope (with reason)

- Publishing, deployment, releases, approval, and destructive authority remain separate explicit human gates.
- Selecting universal “best” models is out of scope; configuration binds semantic roles to available host models.
- Host-native team features are optional accelerators, never the source of truth.

## Scope check

- Over-scope: none.
- Under-scope: remote/distributed execution beyond one machine is deferred.

## Required tests / validation

Run child tests, generated parity, capability probes/doubles, adversarial fixtures, full serial suite, `aw check all`, `aw doctor --agent`, and `aw sanitize --agent`. Paste actual outputs and combined-HEAD evidence.

## Open questions

### OQ-01: Canonical deterministic CLI spelling

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: use `aw ipd execute-set <set-id>` for noun-verb CLI consistency; `/exec-set` remains the human/agent workflow invocation. Plan-only is a mode over the same coordinator.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: approved contract cites research `<mqqk8e>` and contains no blocking OQ.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Orders 01-05 each reach verified terminal lifecycle in dependency order; the resulting CLI creates, drains, resumes, and finalizes a fixture Set without direct worker mutation of authoritative records.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the combined-HEAD adversarial suite proves exact stop truth-table behavior, safe parallel waves, conflict serialization, soft-denial rejection, crash recovery, adapter fail-closed behavior, and no false completion.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: five small children build one missing coordinator over already-executed runtime foundations (the awoptimize Set, Orders 00-18, verified present in `.aw/records/plans/executed/`).

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved. Each child carries its own resolved OQ-01; no blocking OQ remains at the Set level.
2. Scope fence: Build ONLY the missing coordinator layer (Set compiler, records/stop-policy, scheduler/integration, host runner/adapters, workflow/skill packaging) by reusing the executed awoptimize runtime (`run_engine`, `run_state`, `run_packet`, `run_evidence`, `run_recovery`, `run_gates`, `verify_roles`, `orchestrate_isolation`, `host_capability_registry`, `host_adapters`, `agy_verifier`, `ipd_lint`, the closed run ledger, and `ipd-lifecycle`); do NOT fork equivalents. Remote/distributed execution beyond one machine stays deferred. Publishing/deploy/release/approval stay separate human gates.
3. Honesty rule (hard MUST): When reporting any test/suite/check passed, paste the ACTUAL runner output (child suites, generated-parity, capability probes/doubles, adversarial fixtures, full serial suite, `aw check all`, `aw doctor --agent`, `aw sanitize --agent`, and combined-HEAD evidence); never claim a pass without running the actual command.
4. Commit ONLY each order's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push. Executors cannot approve, verify, or terminally transition their own work; the coordinator alone owns the ledger, main worktree, IPD evidence/checkmarks, integration, and terminal transitions.
5. Lifecycle move: Each child transitions to `executed` only after every E item is performed and every V item is verified with pasted evidence; a child with deferred work stays `pending` and produces a partial result + durable walkthrough + attention-visible blocked backlog item. This orchestrator transitions to `executed` only after all five children reach verified terminal lifecycle.

Requires plan review and explicit human approval before any child executes.
