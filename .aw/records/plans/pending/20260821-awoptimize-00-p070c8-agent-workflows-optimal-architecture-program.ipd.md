# IPD: Agent Workflows Optimal Architecture Program

- Date: 2026-08-21
- Kind: orchestrator
- Concern: Replace prose-only workflow compliance with a portable, evidence-gated execution architecture that remains usable across models and coding-agent hosts.
- Scope: Orchestration only for Set `awoptimize`; Orders 01 through 08 own implementation. This Set may change workflow metadata, runtime and conformance tooling, generated host adapters, tests, and documentation, but no child may silently expand beyond its declared files.
- Status: reviewed
- Set: awoptimize
- Order: 0
- Highest E allocated: 10
- Author: Codex GPT-5.6 Sol
- Id: p070c8

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created from the pinned repository audit at commit `a2110e96b980fbf778027f1676a73774cb819292`, official host documentation, and the repository-observed false-completion incidents.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. PR-A size assessment corrected exception->standard (10 leaves/1 group, neither threshold exceeded); PR-B canonical full-suite evidence command pinned to `make test` (parallel `pytest -n auto`, ~0:40 vs ~4:20 serial; D138). Foundational evidence verified against the tree (agy_run.py same-session audit, ipd_lint.py structure-only boundary, awlayout incident record, conformance operator-protocol/host_matrix.json all confirmed). Set scope accounting sound (8 children form a schema->evidence->runtime->verification->hosts->benchmark->migration->cutover DAG). Non-blocking OQ-01/OQ-02 (live budget, agy version) remain open, owner human maintainer; they gate child Orders 05/06 execution, not this orchestrator's review.

## Goal

Deliver one canonical workflow system whose semantics do not depend on a model remembering a monolithic prompt. The resulting system must compile portable workflow packages and host adapters, enforce lifecycle gates with deterministic code, isolate execution from independent verification, and measure behavior per exact model, host, version, and configuration before claiming support.

Architectural invariants:

1. Canonical semantics live in one typed source; skills, slash commands, prompt bundles, and host agent definitions are generated or thin adapters.
2. A model response, checklist mark, or zero process exit is never completion evidence by itself.
3. The runtime owns state transitions; executors propose evidence but cannot certify or perform terminal transitions.
4. Required evidence is bound to stable requirement IDs and captures command, working directory, repository state, timestamps, exit code, and immutable output reference.
5. The independent verifier receives the approved requirements, actual diff, and raw evidence through a fresh or isolated context, not the executor's summary.
6. Read-only analysis may run concurrently. Mutating agents are serial unless each receives a separate worktree, a disjoint ownership fence, and a deterministic merge-and-revalidate gate.
7. Model profiles may tune packet size, reasoning level, and verifier policy only where controlled evidence supports the difference; they may not fork functional requirements.
8. Unsupported or untested host capability claims default to `unverified`, never `supported`.
9. Approved requirements are frozen. Any semantic change requires an explicit revision or corrective IPD with traceability.
10. Backward compatibility remains until generated adapters and live conformance probes pass their named cutover gates.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Program gates

- [ ] E-01 Establish and freeze the baseline inventory, current failure taxonomy, architecture decision record, stable requirement catalog, and acceptance-scenario ownership map before Order 01 begins.
  - Depends on: none
  - Expected outcome: every later child consumes one reviewed baseline and cannot redefine the program's goals or evidence standard.
  - Execution state: pending
- [ ] E-02 Execute and independently validate Order 01, then freeze the canonical schema, compiler contract, and generated-artifact drift policy.
  - Depends on: E-01
  - Expected outcome: subsequent children import a versioned schema and compiled intermediate representation instead of parsing prose ad hoc.
  - Execution state: pending
- [ ] E-03 Execute and independently validate Order 02 after Order 01.
  - Depends on: E-02
  - Expected outcome: an append-only run ledger and evidence contract exist before any runtime claims completion.
  - Execution state: pending
- [ ] E-04 Execute and independently validate Order 03 after Orders 01 and 02.
  - Depends on: E-03
  - Expected outcome: deterministic orchestration, resumability, transition guards, and fail-closed exit behavior consume the canonical schema and ledger.
  - Execution state: pending
- [ ] E-05 Execute and independently validate Order 04 after Orders 01 through 03.
  - Depends on: E-04
  - Expected outcome: execution, review, correction, and terminal-transition authorities are separated with portable fallback behavior.
  - Execution state: pending
- [ ] E-06 Execute and independently validate Order 05 after Orders 01, 03, and 04.
  - Depends on: E-05
  - Expected outcome: native host adapters and skills are generated only for evidence-backed capabilities and preserve canonical semantics.
  - Execution state: pending
- [ ] E-07 Execute and independently validate Order 06 after Orders 01 through 05.
  - Depends on: E-06
  - Expected outcome: offline smoke fixtures and controlled live-model evaluations quantify completion, evidence truth, drift, and cost by exact configuration.
  - Execution state: pending
- [ ] E-08 Execute and independently validate Order 07 after Orders 01 through 06.
  - Depends on: E-07
  - Expected outcome: every catalog workflow has an explicit disposition and the selected families run through the new architecture without semantic loss.
  - Execution state: pending
- [ ] E-09 Execute and independently validate Order 08 after Orders 01 through 07.
  - Depends on: E-08
  - Expected outcome: compatibility, documentation, migration, rollback, release boundary, and cutover gates are complete.
  - Execution state: pending
- [ ] E-10 Perform the final whole-Set residual audit from a clean checkout, including full suite, IPD lint, leak scan, compiler drift check, host adapter fixtures, benchmark thresholds, complete workflow disposition coverage, and archive-quality evidence retention.
  - Depends on: E-09
  - Expected outcome: no open critical requirement, unsupported capability claim, generated drift, red required check, or unassigned workflow remains.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

The `Depends on` column names earlier child Orders. Each child's internal `Depends on` metadata names E-item prerequisites inside that child.

| Order | File | Bounded responsibility | Depends on |
|---:|---|---|---|
| 01 | `20260821-awoptimize-01-nmwy3m-canonical-workflow-schema-and-compiler.ipd.md` | Typed workflow schema, canonical source layout, compiler, generated-artifact parity | none |
| 02 | `20260821-awoptimize-02-7qs57e-run-ledger-and-evidence-contract.ipd.md` | Requirement freeze, run ledger, evidence envelopes, completion predicates | 01 |
| 03 | `20260821-awoptimize-03-7cqbel-deterministic-workflow-runtime.ipd.md` | State machine, step packets, resume/retry, interaction and terminal gates | 01, 02 |
| 04 | `20260821-awoptimize-04-mcubhc-independent-verification-and-orchestration.ipd.md` | Role separation, isolated verifier, subagent and worktree policy, corrective loop | 01, 02, 03 |
| 05 | `20260821-awoptimize-05-5elu0u-host-adapters-skills-and-capability-registry.ipd.md` | Skills, slash commands, agents, host/version capability evidence | 01, 03, 04 |
| 06 | `20260821-awoptimize-06-ozlus1-behavioral-benchmark-and-regression-harness.ipd.md` | Seeded tasks, ablations, live-model matrix, metrics, release thresholds | 01 through 05 |
| 07 | `20260821-awoptimize-07-01iuql-workflow-family-migration.ipd.md` | Per-workflow disposition and migration of complex, shared-harness, and simple families | 01 through 06 |
| 08 | `20260821-awoptimize-08-kk41rr-compatibility-documentation-and-cutover.ipd.md` | Compatibility, operator docs, migration, rollback, release and cutover | 01 through 07 |

## Completion criteria (the whole Set is done only when)

- The architecture decision and approved requirements are frozen and traceable to implementation and validation IDs.
- Orders 01 through 08 each pass author, review-finalize, pre-execution, pre-transition, and post-transition lifecycle gates in dependency order.
- The canonical compiler produces byte-stable outputs and a drift check rejects hand-edited generated adapters.
- Every workflow manifest row has a reviewed disposition: deterministic command, single-context workflow, skill, orchestrated workflow, shared harness plus module, or deprecation alias.
- No executor or same-session self-auditor can set `verified`, `complete`, `executed`, or an equivalent terminal state.
- Independent verification detects all seeded false-completion fixtures and rejects stale, fabricated, mismatched-commit, incomplete, or self-authored evidence.
- The four named model configurations run a preregistered benchmark on the supported hosts available to the operator; unavailable combinations are explicitly `pending`, never imputed.
- Release thresholds include requirement recall, evidence validity, defect escape, false-completion detection, regression rate, context/token use, latency, and cost.
- Live host/version conformance evidence exists for every advertised native path, command, skill, agent, fork, or background capability.
- Legacy `.opencode/commands/` and `.claude/commands/` behavior remains until parity, migration, and rollback tests pass.
- The full repository suite, leak scan, IPD lint, generated-artifact drift check, and Markdown policy checks pass with retained raw output.

## Cross-IPD validation

- Schema ownership: Order 01 alone owns canonical workflow types and compiler IR; later Orders import them.
- Evidence ownership: Order 02 alone owns evidence-envelope validation and completion predicates; runtime and verifier call it.
- Transition ownership: Order 03 alone changes durable run state; no generated prompt contains a terminal mutation command.
- Verification independence: Order 04 verifies the actual working tree and raw ledger and cannot rely on the executor's final prose.
- Host honesty: Order 05 cannot mark a capability supported without exact versioned probe evidence; Order 06 measures behavior without editing the registry.
- Benchmark integrity: fixtures, expected outcomes, scoring, randomization, and retry policy are versioned before a live run.
- Migration parity: Order 07 maps every manifest row and proves generated adapters resolve to the same semantic digest.
- Cutover safety: Order 08 removes or redirects legacy surfaces only after all earlier gates pass and documents rollback.

## Risk register

| Risk | Detection | Mitigation | Stop condition |
|---|---|---|---|
| Model checks boxes without doing work | ledger lacks valid evidence; independent verifier reruns checks | runtime-owned states and verifier gate | any required item has no valid evidence |
| Long prompts cause directive loss | ablation benchmark and packet completion metrics | bounded just-in-time packets plus durable ledger | packet exceeds calibrated budget or omitted requirement |
| Same-context confirmation bias | compare executor claim with clean verifier result | fresh verifier context and raw evidence packet | verifier cannot establish isolation |
| Parallel agents collide | worktree/ownership preflight and merge conflict checks | read-only parallelism by default; isolated mutation only | shared mutable files or unresolved dependency |
| Tests are changed to make green | test-integrity diff, mutation/falsifiability checks | independent review and baseline comparison | requirement-backing test cannot fail when behavior breaks |
| Host documentation or CLI drifts | exact version probe expiry and registry status | evidence TTL plus fail-closed adapter generation | capability evidence missing, stale, or contradictory |
| Skills silently fail to activate | discovery and invocation evals separated from outcome evals | direct command fallback and generated diagnostics | activation rate below release threshold |
| Model-specific fork drifts semantics | semantic digest parity across compiled profiles | profiles restricted to transport and packet knobs | profile changes a requirement or acceptance predicate |

## Deferred / out of scope (with reason)

| Item | Reason | Later step |
|---|---|---|
| Product feature work unrelated to workflow execution | This Set changes the workflow framework only. | Separate product IPD. |
| Unattended deployment, publishing, tagging, or pushing | External mutation needs separate authority and security review. | Release workflow after explicit approval. |
| Declaring one model universally superior | The requested configurations require controlled, task-specific evidence. | Periodic benchmark program. |
| Supporting an undocumented host feature | Documentation and live conformance are required before adoption. | Capability-registry follow-up after probe. |
| Replacing human approval for high-impact actions | Evidence gates improve rigor but do not grant authority. | Remains a product policy. |

## Scope check

- Over-scope: no application features, releases, credential changes, pushes, or production deployments.
- Under-scope: none; schema, evidence, runtime, verification, hosts, evaluation, workflow migration, and cutover are all represented.

## Required tests / validation

At final execution, run the exact commands defined by each child plus: the full unit suite; `aw ipd lint --all --agent`; local leak scan; generated-artifact drift check; all offline seeded fixtures; complete workflow-disposition coverage; clean-checkout install and compatibility tests; controlled live benchmark report validation; and a residual search for TODO, placeholder evidence, unsupported host claims, and terminal state changes outside the runtime.

The canonical full-suite command for evidence in this Set (and its children) is `make test` (parallel `pytest -n auto` after `pip install '.[test]'`, auto-falling back to serial `unittest`; measured ~4:20 serial -> ~0:40 parallel with identical results, per D138 and CONTRIBUTING). Use `make test-serial` (`python3 -m unittest discover -s tests -t .`) only to reproduce a suspected ordering/isolation failure. Paste the actual runner output as evidence either way.

## Open questions

### OQ-01: What live-model budget and provider credentials may the benchmark consume?

- Blocking: no
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: Order 06 must run deterministic offline tests without credentials and emit exact pending commands until budget and credentials are authorized.

### OQ-02: Which exact `agy` or Antigravity distribution and version are supported?

- Blocking: no
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: the repository runner exists, but no executable is installed in the research environment and public host semantics must not be inferred from the wrapper.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: signed-off baseline artifact with pinned commit, complete workflow inventory, failure taxonomy, requirement IDs, acceptance ownership, and zero unresolved critical ambiguity.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Order 01 is in `executed/`, passes post-transition lint, compiler source/IR versions are frozen, and two clean compilations plus semantic-profile mutation tests pass.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Order 02 is executed; ledger corruption, stale evidence, fabricated success, and identity-collision fixtures fail closed while valid evidence round-trips.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Order 03 is executed; exhaustive transition tests prove no illegal or executor-owned terminal path and crash/retry/headless simulations pass.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Order 04 is executed; every seeded false completion is detected by an isolated verifier and unsafe parallel mutation is refused or worktree-isolated and revalidated.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: Order 05 is executed; each advertised host capability has exact nonexpired probe evidence, every generated adapter shares the canonical digest, and unsupported claims are rejected.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Order 06 is executed; offline corpus/scorer integrity passes and every authorized live result links exact configuration and raw trials, with unavailable cells marked pending.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: Order 07 is executed; completeness tooling accounts for every workflow/lens/persona/conformance file, migrated families pass parity and risk gates, and failed families retain explicit fallback.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: Order 08 is executed; clean install, update, customized drift, interruption, rollback, security, documentation, and release-readiness checks pass without a release side effect.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: from a clean checkout, retain exact commands, cwd, commit, exit codes, output hashes, and summaries for the full suite, all IPD phases, leak scan, compiler drift, host claims, benchmark gates, disposition completeness, and residual search; zero critical residuals and no unauthorized tag/push/release.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Do not execute any child until this orchestrator, the architecture decision, and that child have passed `/plan-review` and explicit human approval. The coordinator is the sole authority for dependency release and whole-Set status. A child executor may update only its own E-items and implementation evidence; it may not certify its V-items or move any IPD to a terminal directory.

Execution contract: use path-scoped commits only; never use `git add -A`, bare `git add`, `git commit -a`, or push. Retain raw command output and exit codes. Stop on missing dependencies, ambiguous requirements, invalid evidence, shared-worktree mutation, or scope expansion. Terminal lifecycle transition is a post-gate transaction performed only after independent validation, not a checklist action. No tag, release, registry upload, deployment, or push is authorized by this Set.

After every child and this orchestrator have all execution items performed and matching validation items independently passed, append lifecycle history, set terminal status, move plans with `git mv`, regenerate the plan index, rerun post-transition lint, and commit only the lifecycle transaction paths.
