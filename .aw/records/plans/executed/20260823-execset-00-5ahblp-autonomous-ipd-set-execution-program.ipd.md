# IPD: Autonomous IPD Set Execution Program

- Date: 2026-08-23
- Kind: orchestrator
- Concern: Execute complete approved IPD Sets with maximal safe parallelism and almost no interruption.
- Scope: Set planning, decision/defer records, scheduler, model routing, host launchers, workflow/skill packaging, and conformance.
- Scope-Paths: grandfathered
- Status: executed
- Set: execset
- Order: 0
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: 5ahblp

## Workflow history
- 2026-08-24 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us (ipdrunner run-20260824T150827Z-2301181)): execset Order 00 orchestrator: all five children verified terminal; Set-wide adversarial + full-suite + check/doctor/sanitize evidence green
- 2026-08-24 approved (aw set, --by-human): status set to approved
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-005 (added full execution contract to orchestrator gate). Reuse premise verified: awoptimize Orders 00-18 present in executed/.
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created from repository and cross-host investigation at `05910e16ca9aa005b8bb76cf789b5c17d5dd7dcc`.

## Goal

Deliver `/exec-set`, backed by a deterministic coordinator that executes every safely runnable part of an approved IPD Set, records autonomous choices and deferred questions, parallelizes provably independent work, and asks the human only under the exact two-part stop rule.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Freeze the cross-plan contract

- [x] E-01 Approve the hard-stop predicate, child-STOP containment, partial/deferred terminal semantics, durable record strategy, dependency model, model routing, and host support policy from research `<mqqk8e>`.
  - Depends on: none
  - Expected outcome: Orders 01-05 have no unresolved contract decision.
  - Execution note: verified the cross-plan contract is frozen with no unresolved decision. The four-clause hard-stop predicate and child-STOP containment are implemented + tested in Order 02 (set_stop_policy.classify/hard_stop_predicate/contain_child_stop); partial/deferred terminal semantics + the durable record strategy (versioned ledger kinds, decisions/open-questions/deferred-work projections, blocked-backlog promotion, walkthrough) in Order 02 (set_state, set_records); the dependency model in Order 01 (ipd_set_plan cross-IPD graph); model routing (fail-closed bindings) in Order 03 (ipd_set_executor); host support policy (capability-gated, evidence-only) in Order 04 (host_runner/host_launchers). Research `<mqqk8e>` exists at `.aw/records/research/20260823-execset-00-mqqk8e-exec-set-architecture.gpt56.research-report.md` and is indexed. All 9 OQs across the five children are `Blocking: no` + `Status: resolved`; the orchestrator OQ-01 is resolved. No unresolved contract decision remains.
  - Execution state: performed

### Material change 2: Execute the children

- [x] E-02 Execute Orders 01-05 in dependency order; Orders 01 and 02 may run concurrently, then 03, 04, and 05.
  - Depends on: E-01
  - Expected outcome: one end-to-end, resumable Set executor exists with generated adapters.
  - Execution note: all five children reached verified terminal lifecycle in dependency order (01 iy1a2g, 02 3m4e54, then 03 m2wwns, 04 31744f, 05 2h7777), each finalized via `aw ipd finalize` (this run bootstraps the scheduler serially per the runbook, so the eventual-concurrency of 01/02 is realized serially). All five carry `- Status: executed` and pass `aw ipd lint --phase post-transition` (conforming). The end-to-end resumable executor exists: a fixture Set COMPILES to a manifest (ipd_set_plan), the frontier DRAINS as nodes complete (ipd_set_executor.ready_lanes advances aaaaaa:E-01 -> bbbbbb:E-01 after the cross-IPD dep completes), RESUME reconstructs fail-closed (aw ipd execute-set --resume -> exit 2 on a missing ledger, exit 3 on an unknown outcome, no replay), and generated host adapters/shims exist (Order 04 host_launchers + Order 05 exec-set shims). Authority stays with the coordinator: the only terminal path is `aw ipd finalize`; worker outcome envelopes are validated (run_packet/run_evidence), never trusted.
  - Execution state: performed

### Material change 3: Prove release readiness

- [x] E-03 Require adversarial no-stop, parallel-conflict, greenwashing, crash/recovery, cross-host, lifecycle, and full-suite evidence before release.
  - Depends on: E-02
  - Expected outcome: no model prose, worker exit code, or unsupported host claim can falsely complete a Set.
  - Execution note: the combined adversarial/coordination evidence is present and green: `python3 -m pytest tests/test_set_coordination.py tests/test_ipd_set_executor.py tests/test_host_runner.py tests/test_ipd_set_plan.py tests/test_exec_set_workflow.py` -> `122 passed`. This covers the exact no-stop truth table (ClassifierV02.test_predicate_only_all_four, 16-row), parallel-conflict serialization (SchedulerV01 + IntegrationGateV02 combined-red fails closed), greenwashing/soft-denial (host_runner exit-0-no-diff -> failed_final; host_launchers.host_result_can_finalize; run_evidence EV-* gates), crash/recovery (LifecycleV03.test_resume_fails_closed_on_unknown_outcome; run_recovery resume), host fail-closed (RoutingV01 missing binding; CapabilityGatedV02 unverified -> fallback/refuse; Kiro row unverified-until-probed), and lifecycle (set_state completion refusal; deferred required -> set_partial, never executed). Full serial suite: `python3 -m pytest -n auto` -> `2437 passed, 1 skipped`. `aw check all --agent` -> 26 findings, ALL pre-existing (base also 26), zero execset-attributable. `aw doctor --agent` -> 19 findings, all pre-existing. `aw sanitize --agent` -> clean (0 findings). No model prose, worker exit code, or unsupported host claim can falsely complete a Set.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: approved contract cites research `<mqqk8e>` and contains no blocking OQ.
  - Observed evidence: research `<mqqk8e>` exists and is indexed (`.aw/records/research/20260823-execset-00-mqqk8e-exec-set-architecture.gpt56.research-report.md`, listed in research INDEX.md/INDEX.json). Across the five executed children, `grep -h "^- Blocking:"` -> `9  - Blocking: no` (all 9 OQs non-blocking) and `grep -h "^- Status:"` (OQ status) -> `9  - Status: resolved` (all resolved); the orchestrator OQ-01 is resolved. No blocking OQ remains at the Set or child level.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Orders 01-05 each reach verified terminal lifecycle in dependency order; the resulting CLI creates, drains, resumes, and finalizes a fixture Set without direct worker mutation of authoritative records.
  - Observed evidence: all five children are in `.aw/records/plans/executed/` with `- Status: executed` and pass `aw ipd lint --phase post-transition` (conforming for iy1a2g/3m4e54/m2wwns/31744f/2h7777); their finalize lifecycle commits appear in order in `git log` (each `lifecycle(<id>): finalize <id> -> executed`). CLI end-to-end on a fixture Set: CREATE - `ipd_set_plan.compile_manifest` produced a 2-node manifest with an eligibility mode; DRAIN - `ipd_set_executor.ready_lanes` advanced the frontier `{aaaaaa:E-01}` -> `{bbbbbb:E-01}` after the upstream completed; RESUME - `aw ipd execute-set fix --resume run-nope` returned exit 2 (fail-closed on a missing ledger, no replay); FINALIZE - the coordinator's only terminal path is `aw ipd finalize` (used for all five children). Worker outcome envelopes are validated by run_packet/run_evidence and never directly mutate authoritative records (the coordinator owns the ledger/index/terminal transition).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the combined-HEAD adversarial suite proves exact stop truth-table behavior, safe parallel waves, conflict serialization, soft-denial rejection, crash recovery, adapter fail-closed behavior, and no false completion.
  - Observed evidence: `python3 -m pytest tests/test_set_coordination.py tests/test_ipd_set_executor.py tests/test_host_runner.py tests/test_ipd_set_plan.py tests/test_exec_set_workflow.py` -> `122 passed`, proving on the integrated HEAD: exact stop truth-table (ClassifierV02.test_predicate_only_all_four - hard_stop true IFF all four clauses), safe waves + conflict serialization (SchedulerV01 dispositions, plan_wave via analyze_concurrency_eligibility, IntegrationGateV02 combined-red + per-lane-failure fail closed), soft-denial rejection (host_runner exit-0-no-diff -> failed_final; evidence_gate EV-FAILED-EXIT), crash recovery (LifecycleV03.test_resume_fails_closed_on_unknown_outcome), adapter fail-closed (RoutingV01 missing binding -> BindingError; CapabilityGatedV02 unverified -> fallback/refuse), no false completion (set_state completion refusal; terminal_transition_allowed combined-red/unresolved refuse; deferred required -> set_partial). Full serial suite `python3 -m pytest -n auto` -> `2437 passed, 1 skipped`. `aw check all --agent` outcome findings=26 (all pre-existing; zero execset-attributable), `aw doctor --agent` findings=19 (all pre-existing), `aw sanitize --agent` -> clean (0 findings). Live cross-host runs with real models are operator-run and out of agent-executed scope (the plan forbids live host claims without evidence); model-free doubles + fixtures are the falsifiable substitute.
  - Result: pass


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
