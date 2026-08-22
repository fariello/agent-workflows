# IPD: Agent Workflows Optimal Architecture Program

- Date: 2026-08-21
- Kind: orchestrator
- Concern: Replace prose-only workflow compliance with a portable, evidence-gated execution architecture that remains usable across models and coding-agent hosts.
- Scope: Orchestration only for Set `awoptimize`; Orders 01 through 08 own implementation. This Set may change workflow metadata, runtime and conformance tooling, generated host adapters, tests, and documentation, but no child may silently expand beyond its declared files.
- Status: approved
- Approval: Gabriele Fariello (human), 2026-08-22
- Set: awoptimize
- Order: 0
- Highest E allocated: 10
- Author: Codex GPT-5.6 Sol
- Id: p070c8

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created from the pinned repository audit at commit `a2110e96b980fbf778027f1676a73774cb819292`, official host documentation, and the repository-observed false-completion incidents.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. PR-A size assessment corrected exception->standard (10 leaves/1 group, neither threshold exceeded); PR-B canonical full-suite evidence command pinned to `make test` (parallel `pytest -n auto`, ~0:40 vs ~4:20 serial; D138). Foundational evidence verified against the tree (agy_run.py same-session audit, ipd_lint.py structure-only boundary, awlayout incident record, conformance operator-protocol/host_matrix.json all confirmed). Set scope accounting sound (8 children form a schema->evidence->runtime->verification->hosts->benchmark->migration->cutover DAG).
- 2026-08-21 approved (Gabriele Fariello, --by-human): human sign-off recorded for the FOUNDATIONAL scope of the Set (this orchestrator + Orders 01-04, the deterministic offline model-free critical path). Orders 05-08 remain `reviewed` (GO - pending human approval), to be approved once their live host/model probes and benchmark evidence are in hand. Execution proceeds in dependency order via /ipd-lifecycle; live model/host calls are operator-run, never executor-run.
- 2026-08-21 amended + re-scoped (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): the tail was re-scoped from 7 coarse Orders (old 02-08, retired to superseded/) into 17 right-sized children (new Orders 02-18) per the maintainer-approved re-scope proposal and backlog `8iy2dk`. The orchestrator's gates were rewritten to coordinate by architectural LAYER (A-G) rather than one leaf per child; the child table, completion criteria, and cross-IPD validation now describe the 19-Order Set. Because the orchestrator's content changed materially, its prior human approval is withdrawn and Status reverts to `to-review` pending re-review (/plan-review) + fresh human approval. Order 01 (executed) is unaffected.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Reviewed the re-scoped orchestrator after all 17 children were individually reviewed; cross-checked the child-table DAG against every child's own gate. PR-001 (MEDIUM): child table listed Order 05's dep as `04`, but Order 05's gate requires 01-03 and its fence explicitly excludes Order 04 (05 can run parallel with 04) - FIXED to `01-03`. PR-002 (MEDIUM): completion criteria implied the executor runs the live benchmark and listed dollar `cost` as a threshold, contradicting the Order 12/13 offline-only/operator-run-live/no-cost resolution - FIXED (operator-run live, time/token efficiency). PR-003 (LOW): the final-execution command set said 'controlled live benchmark report validation' - FIXED to consume operator-run reports + pinned `make test`/`aw sanitize --agent`. PR-004 (LOW): orchestrator OQ-01/OQ-02 were stale `open` - reconciled to `resolved`, pointing at the Order 12/13 (offline/live) and Order 10/11 (agy 1.1.17 tentative) resolutions. E/V bijection 9:9; layer gates enumerate the right children; the watermark (10) correctly exceeds the present max (E-09). No blocking open questions remain. This completes /plan-review of the entire awoptimize Set (00 + all 17 children).
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.

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

### Program gates (one per architectural LAYER; the fine-grained per-Order DAG is in the child table below)

Note (2026-08-21 re-scope): the tail was re-scoped from 7 coarse Orders (old 02-08, now in
`superseded/`) into 17 right-sized children (new Orders 02-18), each authored to the one-observable-
action-per-E-item bar (backlog `8iy2dk`). Order 01 (schema+compiler) is already `executed`. To keep
THIS orchestrator itself right-sized, its gates coordinate by LAYER (A-G), not one leaf per child;
each layer gate drives its member Orders through the full lifecycle (author -> /plan-review -> human
approval -> execute -> independent verification -> transition) in the child-table dependency order.

- [ ] E-01 Establish and freeze the baseline: architecture decision record (D139), the re-scope map (superseded old 02-08 -> new 02-18), and the layer dependency graph, before Layer A begins.
  - Depends on: none
  - Expected outcome: every child consumes one reviewed baseline + numbering plan; no child can redefine the program's goals or evidence standard, and Order 01's executed artifacts are the fixed foundation.
  - Execution state: pending
- [ ] E-02 Drive Layer A (evidence substrate): Orders 02 (record schemas + requirement freeze), 03 (append-only tamper-evident ledger store), 04 (evidence capture + validators + completion predicates + inspection CLI), each through the full lifecycle in dependency order.
  - Depends on: E-01
  - Expected outcome: a completion claim is a deterministic predicate over frozen requirements + valid append-only evidence, not a model's word; all three Orders reach executed.
  - Execution state: pending
- [ ] E-03 Drive Layer B (runtime): Orders 05 (state machine + single-writer engine), 06 (bounded packets + outcome envelopes + human gates), 07 (retry + resume + crash recovery + run lifecycle CLI), each through the full lifecycle.
  - Depends on: E-02
  - Expected outcome: sequencing, resumability, transition guards, and fail-closed behavior live in deterministic code over the Layer A ledger, not in model memory; all three reach executed.
  - Execution state: pending
- [ ] E-04 Drive Layer C (verification + isolation): Orders 08 (verifier roles + clean packet + procedures + corrective routing), 09 (isolation hierarchy + concurrency eligibility + merge-revalidate), each through the full lifecycle.
  - Depends on: E-03
  - Expected outcome: execution, review, and correction authorities are separated; independent verification runs on frozen requirements + actual diff + raw evidence; both reach executed.
  - Execution state: pending
- [ ] E-05 Drive Layer D (hosts): Orders 10 (capability-evidence registry + isolated probes), 11 (generated skills + host adapters + agy fresh verifier), each through the full lifecycle.
  - Depends on: E-04
  - Expected outcome: native adapters/skills are generated only for evidence-backed capabilities (unverified by default); both reach executed with no unproven support claim.
  - Execution state: pending
- [ ] E-06 Drive Layer E (evaluation): Orders 12 (benchmark corpus + preregistered scoring), 13 (offline runners + ablations + metrics + reports), each through the full lifecycle.
  - Depends on: E-05
  - Expected outcome: the offline benchmark quantifies completion, evidence truth, drift, and time/token efficiency (no dollar cost - Order 13) by exact configuration; live model runs remain operator-run; both reach executed.
  - Execution state: pending
- [ ] E-07 Drive Layer F (migration): Orders 14 (disposition inventory + shared family migration), 15 (complex orchestrated migration), 16 (compact migration + shims + promotion gates), each through the full lifecycle.
  - Depends on: E-06
  - Expected outcome: every catalog workflow has an explicit disposition and migrated families pass their per-family benchmark promotion gates without semantic loss; all three reach executed.
  - Execution state: pending
- [ ] E-08 Drive Layer G (cutover): Orders 17 (compatibility + migration + rollback + deprecation), 18 (docs + security + lifecycle fixtures + release-readiness), each through the full lifecycle.
  - Depends on: E-07
  - Expected outcome: compatibility, rollback, documentation, security, and a GO/NO-GO release-readiness review are complete without any publish/tag/push; both reach executed.
  - Execution state: pending
- [ ] E-09 Perform the final whole-Set residual audit from a clean checkout: full suite, `aw ipd lint --all`, leak scan, compiler drift check, host-adapter fixtures, benchmark thresholds, complete workflow-disposition coverage, and archive-quality evidence retention.
  - Depends on: E-08
  - Expected outcome: no open critical requirement, unsupported capability claim, generated drift, red required check, or unassigned workflow remains across all 17 children.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

The `Depends on` column names earlier child Orders. Each child's internal `Depends on` metadata names E-item prerequisites inside that child.

Layers: A evidence-substrate (02-04), B runtime (05-07), C verification+isolation (08-09),
D hosts (10-11), E evaluation (12-13), F migration (14-16), G cutover (17-18). Order 01 is executed.
The old coarse Orders 02-08 are retired in `superseded/` (see their RETIRED headers).

| Order | Layer | File | Bounded responsibility | Depends on |
|---:|:--:|---|---|---|
| 01 | - | `...-01-nmwy3m-canonical-workflow-schema-and-compiler.ipd.md` (EXECUTED) | Typed workflow schema, source layout, compiler, drift check | none |
| 02 | A | `...-02-viuzu4-ledger-and-evidence-record-schemas-and-requirement-freeze.ipd.md` | Ledger/evidence record schemas + requirement freeze | 01 |
| 03 | A | `...-03-6psux0-append-only-tamper-evident-run-ledger-store.ipd.md` | Append-only tamper-evident ledger store | 02 |
| 04 | A | `...-04-yndh7k-evidence-capture-validators-completion-predicates-and-run-in.ipd.md` | Evidence capture + validators + completion predicates + inspection CLI | 03 |
| 05 | B | `...-05-b1v3wl-deterministic-run-state-machine-and-single-writer-engine.ipd.md` | Run state machine + single-writer engine | 01-03 |
| 06 | B | `...-06-ptsfjn-bounded-step-packets-outcome-envelopes-and-human-decision-ga.ipd.md` | Bounded packets + outcome envelopes + human gates | 05 |
| 07 | B | `...-07-7yqm1v-retry-correction-resume-cancel-crash-recovery-and-run-lifecy.ipd.md` | Retry + resume + crash recovery + run lifecycle CLI | 06 |
| 08 | C | `...-08-5hu6bd-verifier-roles-clean-packet-procedures-and-corrective-routin.ipd.md` | Verifier roles + clean packet + procedures + corrective routing | 05 |
| 09 | C | `...-09-1m5ob8-isolation-hierarchy-concurrency-eligibility-and-merge-revali.ipd.md` | Isolation hierarchy + concurrency eligibility + merge-revalidate | 08 |
| 10 | D | `...-10-4fttzq-host-capability-evidence-registry-and-isolated-probes.ipd.md` | Capability-evidence registry + isolated probes | 01, 03 |
| 11 | D | `...-11-bmd1ur-generated-skills-host-adapters-and-agy-fresh-verifier.ipd.md` | Generated skills + host adapters + agy fresh verifier | 10 |
| 12 | E | `...-12-1jfxvo-benchmark-corpus-seeded-tasks-and-preregistered-scoring.ipd.md` | Benchmark corpus + seeded tasks + preregistered scoring | 01-04 |
| 13 | E | `...-13-9ihhzr-benchmark-runners-ablations-metrics-and-reports-offline.ipd.md` | Offline runners + ablations + metrics + reports | 12 |
| 14 | F | `...-14-h1d5aa-migration-disposition-inventory-and-shared-family-migration.ipd.md` | Disposition inventory + shared family migration | 05, 11 |
| 15 | F | `...-15-kh91or-complex-orchestrated-workflow-migration.ipd.md` | Complex orchestrated workflow migration | 14 |
| 16 | F | `...-16-g6zjao-compact-workflow-migration-generated-shims-and-promotion-gat.ipd.md` | Compact migration + shims + promotion gates | 13, 15 |
| 17 | G | `...-17-gnfkh8-compatibility-contract-migration-rollback-and-deprecation.ipd.md` | Compatibility + migration + rollback + deprecation | 16 |
| 18 | G | `...-18-0zst62-documentation-security-hardening-lifecycle-fixtures-and-rele.ipd.md` | Docs + security + lifecycle fixtures + release-readiness | 17 |

## Completion criteria (the whole Set is done only when)

- The architecture decision and approved requirements are frozen and traceable to implementation and validation IDs.
- Orders 01 through 18 each pass author, review-finalize, pre-execution, pre-transition, and post-transition lifecycle gates in dependency order (Order 01 already executed; the rest per the layer sequence A->G).
- The canonical compiler produces byte-stable outputs and a drift check rejects hand-edited generated adapters.
- Every workflow manifest row has a reviewed disposition: deterministic command, single-context workflow, skill, orchestrated workflow, shared harness plus module, or deprecation alias.
- No executor or same-session self-auditor can set `verified`, `complete`, `executed`, or an equivalent terminal state.
- Independent verification detects all seeded false-completion fixtures and rejects stale, fabricated, mismatched-commit, incomplete, or self-authored evidence.
- The preregistered benchmark's OFFLINE harness (Orders 12/13) is built and validated; any LIVE run of the four named model configurations is OPERATOR-RUN (never executor-run) with unavailable combinations explicitly `pending`, never imputed (per the Order 12/13 resolution).
- Release thresholds include requirement recall, evidence validity, defect escape, false-completion detection, regression rate, context/token load, and wall-time; dollar cost is out of scope (no host reports it reliably - Order 13), so efficiency is time/token-based, not dollar-based.
- Live host/version conformance evidence exists for every advertised native path, command, skill, agent, fork, or background capability.
- Legacy `.opencode/commands/` and `.claude/commands/` behavior remains until parity, migration, and rollback tests pass.
- The full repository suite, leak scan, IPD lint, generated-artifact drift check, and Markdown policy checks pass with retained raw output.

## Cross-IPD validation

- Schema ownership: Order 01 (executed) alone owns canonical workflow types and compiler IR; later Orders import them.
- Record + freeze ownership: Order 02 alone owns the ledger/evidence record schemas and requirement freeze; the ledger store (03) and evidence layer (04) build on it.
- Ledger ownership: Order 03 alone owns the append-only tamper-evident store; nothing else writes durable ledger bytes.
- Completion ownership: Order 04 alone owns evidence validators + the completion predicate; completion is computed there, never claimed by a model.
- Transition ownership: Order 05 alone changes durable run state; no generated prompt contains a terminal mutation command.
- Verification independence: Order 08 verifies the actual working tree and raw ledger and cannot rely on the executor's final prose; Order 09 owns isolation/concurrency.
- Host honesty: Order 10 cannot mark a capability supported without exact versioned probe evidence; Order 11 generates adapters/skills only for evidence-backed capabilities.
- Benchmark integrity: Order 12 versions fixtures/scoring/stopping rules before any run; Order 13 measures offline without editing the registry, live runs operator-only.
- Migration completeness: Order 14 accounts for every workflow before Orders 15/16 migrate any; Order 16's per-family promotion gates block advertising an unmigrated family.
- Cutover safety: Orders 17/18 remove or redirect legacy surfaces only after all earlier layers pass, and produce a GO/NO-GO without publishing.
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

At final execution, run the exact commands defined by each child plus: the full unit suite (`make test`); `aw ipd lint --all --agent`; the canonical leak scan `aw sanitize --agent`; generated-artifact drift check; all offline seeded fixtures; complete workflow-disposition coverage; clean-checkout install and compatibility tests; consume the OPERATOR-RUN live benchmark reports where available (offline fixtures otherwise; the executor never runs live models); and a residual search for TODO, placeholder evidence, unsupported host claims, and terminal state changes outside the runtime.

The canonical full-suite command for evidence in this Set (and its children) is `make test` (parallel `pytest -n auto` after `pip install '.[test]'`, auto-falling back to serial `unittest`; measured ~4:20 serial -> ~0:40 parallel with identical results, per D138 and CONTRIBUTING). Use `make test-serial` (`python3 -m unittest discover -s tests -t .`) only to reproduce a suspected ordering/isolation failure. Paste the actual runner output as evidence either way.

## Open questions

### OQ-01: What live-model scope and provider credentials may the benchmark consume?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED downstream in Orders 12/13 (2026-08-21, /plan-review with the maintainer): the benchmark is OFFLINE-ONLY for v1 (executor builds + offline-validates with runner doubles); any LIVE multi-model run is operator-run, never executor-run. There is no dollar "budget" knob (the harness cannot measure cost); enforcement is time/trial (+ token-where-reported) ceilings, and per-run spend/quota is the operator's provider account. The offline scope needs no credentials; live authorization remains a maintainer decision but does not block this Set's offline work.

### OQ-02: Which exact `agy` or Antigravity distribution and version are supported?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED downstream in Orders 10/11 (2026-08-21): the maintainer's installed `agy --version` is `1.1.17`, recorded as the TENTATIVE target in the Order-10 capability registry; per the fail-closed discipline it stays `unverified` until an operator-run isolated live probe on that exact version. The repository runner exists but public host semantics must not be inferred from the wrapper; no capability is advertised as supported without the probe. Not blocking this Set's offline work.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the frozen baseline (D139 ADR present + approved; the re-scope map showing old 02-08 in `superseded/` with RETIRED headers and new 02-18 scaffolded; the layer dependency graph) is recorded, and Order 01 is `executed` as the fixed foundation.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Orders 02, 03, 04 are all in `executed/` and pass post-transition lint; the append-only ledger + evidence validators + completion predicate reject fabricated/stale/mismatched evidence and a completion is computed only from valid evidence (their V-suites are green).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Orders 05, 06, 07 are executed; transition/single-writer/crash-recovery/human-gate simulations pass and no executor-owned terminal path exists; the runtime consumes the Layer A ledger.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Orders 08, 09 are executed; every seeded false completion is detected by an isolated verifier, and unsafe parallel mutation is refused or worktree-isolated and revalidated.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Orders 10, 11 are executed; each advertised host capability has exact nonexpired probe evidence, every generated adapter shares the canonical semantic digest, and unsupported claims default to unverified.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: Orders 12, 13 are executed; offline corpus/scorer integrity passes, metrics are time/token-based (no dollar cost), and any live cell is operator-run and marked pending until authorized.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Orders 14, 15, 16 are executed; completeness tooling accounts for every workflow/lens/persona/conformance file, migrated families pass parity + per-family risk gates, and failed families retain explicit legacy fallback.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: Orders 17, 18 are executed; clean install/update/customized-drift/interruption/rollback, security, documentation, and a GO/NO-GO release-readiness review pass with NO tag/publish/deploy/push.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: from a clean checkout, retain exact commands, cwd, commit, exit codes, output hashes, and summaries for the full suite, all IPD phases, leak scan, compiler drift, host claims, benchmark gates, disposition completeness, and residual search; zero critical residuals and no unauthorized tag/push/release.
  - Observed evidence:
  - Result: pending
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Do not execute any child until this orchestrator, the architecture decision, and that child have passed `/plan-review` and explicit human approval. The coordinator is the sole authority for dependency release and whole-Set status. A child executor may update only its own E-items and implementation evidence; it may not certify its V-items or move any IPD to a terminal directory.

Execution contract: use path-scoped commits only; never use `git add -A`, bare `git add`, `git commit -a`, or push. Retain raw command output and exit codes. Stop on missing dependencies, ambiguous requirements, invalid evidence, shared-worktree mutation, or scope expansion. Terminal lifecycle transition is a post-gate transaction performed only after independent validation, not a checklist action. No tag, release, registry upload, deployment, or push is authorized by this Set.

After every child and this orchestrator have all execution items performed and matching validation items independently passed, append lifecycle history, set terminal status, move plans with `git mv`, regenerate the plan index, rerun post-transition lint, and commit only the lifecycle transaction paths.
