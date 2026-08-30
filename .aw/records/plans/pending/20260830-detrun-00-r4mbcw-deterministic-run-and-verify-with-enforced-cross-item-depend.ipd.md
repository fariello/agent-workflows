# IPD: Deterministic run-and-verify with enforced cross-item dependencies and fault containment

- Date: 2026-08-30
- Kind: orchestrator
- Concern: Runner consolidation, multi-type selector resolution, mandatory cross-item `Item-Dependencies` graph enforcement, fail-closed per-host capability gating, worktree fault containment, and deterministic completion verification.
- Scope: Orchestrates the 5 child implementation plans of Set `detrun` implementing approved spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`). Defines the child plan sequence, dependency graph, integration validation, and Set completion criteria.
- Scope-Paths: agent_workflows/**, tests/**, .aw/records/specs/**
- Item-Dependencies: none
- Status: approved
- Set: detrun
- Order: 0
- Highest E allocated: 05
- Author: antigravity
- Id: r4mbcw
- Approval: 2026-08-30, human ("approved"): Approved by the maintainer: 'I APPROVE all the reviewed IPDs' (2026-08-30 session, verbatim standing instruction before stepping away).
- Blocks-Release: next

## Workflow history
- 2026-08-30 approved (aw set, --by-human): Approved by the maintainer: 'I APPROVE all the reviewed IPDs' (2026-08-30 session, verbatim standing instruction before stepping away).
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): PR-006 fix. Normalized this history block to NEWEST-FIRST, the order `ipd_lifecycle._plan_status_events` assumes (it reverses to derive oldest-first). As authored the block was oldest-first, so the derived event stream read `to-review -> draft` and `aw check plans` reported `check.lifecycle-transition-invalid` ("backwards transition") on all 6 detrun plans. Verified pre-existing at pre-review commit `d4d265b6` (6 findings) and 0 after this fix. Content of every entry is unchanged; only line order.
- 2026-08-30 reviewed (aw set): plan-review: REJECT - NEEDS REPLAN (most of Set already shipped; collides with 3 approved Sets)
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001..PR-006. The Set was authored at 00:08/00:14 against a spec paragraph that declared the whole design net-new; the maintainer corrected that paragraph at `a59f2c53` (00:35), 21 minutes later, and the corrected spec says a graduating Set "must CONSUME, not rebuild" the shipped machinery. Verified at HEAD `d4d265b6` that most of the Set re-implements working code: child 01's parser/evaluator/rules/lint/setter/hook/tests all ship (graduated from this same spec by the executed `ipddeps` Set); child 05's ledger, inspection CLI, completion checker, and resume all ship as `run_ledger_store.py`/`run_cli.py`/`run_evidence.py`/`run_recovery.py`; child 02's descriptor and probe harness largely duplicate `host_capability_registry.py`. Also found three collisions with APPROVED sibling Sets that the Set never reconciled: `lanetruth-03` (`8guhs0`) owns runner consumption of the dependency predicate that child 03 E-05/E-06 rebuilds, `wtiso-07` (`1o4eif`) owns the typed host capability contract that child 02 rebuilds, and `rununify` (`5e4sb6`) is de-duplicating the two runners that children 02-05 each add code to. Recorded the per-item evidence in each child, closed all six gates, added the missing execution contract to the parent gate, and opened two BLOCKING maintainer questions (OQ-02 contract ownership, OQ-03 sequencing against `rununify`). NO-GO. Retire rather than execute; the surviving residue is enumerated in the REPLAN NOTICE.
- 2026-08-30 to-review (antigravity): deepened edge case integration, verification evidence matrices, and Set-level validation.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 draft (antigravity): created.

## Goal

Provide the single canonical, deterministic runner verb (`aw oc run` / `aw agy run`) that resolves typed work items, builds and validates their cross-item `Item-Dependencies` DAG, enforces fail-closed host capability guarantees, isolates mutations in disposable worktrees, captures tamper-evident run ledgers, and authorizes completions through deterministic repository checks rather than agent self-reported prose. Implements approved spec `25kzda`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Set orchestration and sequence verification

- [ ] E-01 Execute and verify child plan `detrun-01` (`bmh754`): `Item-Dependencies` syntax parser, pure graph evaluator, and phased check/lint rules.
  - Depends on: none
  - Expected outcome: `Item-Dependencies` grammar (`none`, `executed:<id6>`, `exists:<type>:<id6>`, `state:<type>:<status>:<id6>`) and `From-Spec` link metadata are enforced across `check_engine.py`, `ipd_lint.py`, `aw ipd dependencies set`, and the opt-in commit hook `ipd-dependency-statement-gate`.
  - Execution state: pending

- [ ] E-02 Execute and verify child plan `detrun-02` (`a54m79`): Per-host capability descriptor, probe harness, and fail-closed action gating.
  - Depends on: E-01
  - Expected outcome: `host_capabilities.py` defines positive/fail-closed probe harnesses for OpenCode (`oc`) and Antigravity (`agy`), enforcing action-level capability requirements (`RUN-HOST-CAPABILITY`) with item-local refusal.
  - Execution state: pending

- [ ] E-03 Execute and verify child plan `detrun-03` (`kaygwo`): Multi-type selector resolution, mixed-type gate, and DAG queue scheduler.
  - Depends on: E-01, E-02
  - Expected outcome: Unified `aw <host> run` resolves items across all 7 types (`ipd`, `spec`, `backlog`, `prompt`, `research`, `release`, `walkthrough`), enforces the `run mixed` confirmation gate, and executes ready items in pure DAG topological order with dependency-not-met cascading.
  - Execution state: pending

- [ ] E-04 Execute and verify child plan `detrun-04` (`k7o7el`): Isolated worktree fault containment, quarantine transaction, and commit gateway trailers.
  - Depends on: E-03
  - Expected outcome: Worktree allocation isolates item changes; out-of-scope mutations trigger deterministic containment (quarantine bundle hashing + baseline restoration) without aborting independent items; commits carry immutable `AW-Run:` and `AW-Item:` trailers.
  - Execution state: pending

- [ ] E-05 Execute and verify child plan `detrun-05` (`7f7782`): Fresh skeptical verifier session, tamper-evident run ledger, and deterministic completion checker.
  - Depends on: E-04
  - Expected outcome: Fresh verifier session executes without inherited memory; deterministic checker validates all 13 common checks; append-only ledger verifies run integrity; exit code policy and `--unverifiable-ok` aggregate neutrality are enforced.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Plan File | What it does | Item-Dependencies |
|---|---|---|---|---|
| 01 | `bmh754` | `20260830-detrun-01-bmh754-item-dependencies-syntax-parser-pure-graph-evaluator-and-pha.ipd.md` | `Item-Dependencies` syntax parser, graph evaluator, `From-Spec` links, phased checks, and setter | `none` |
| 02 | `a54m79` | `20260830-detrun-02-a54m79-per-host-capability-descriptor-probe-harness-and-fail-closed.ipd.md` | Per-host capability descriptor, probe harnesses (`oc`/`agy`), and fail-closed preflight | `executed:bmh754` |
| 03 | `kaygwo` | `20260830-detrun-03-kaygwo-multi-type-selector-resolution-mixed-type-gate-and-dag-queue.ipd.md` | Multi-type selector resolution, mixed-type confirmation gate, and DAG queue scheduler | `executed:bmh754`, `executed:a54m79` |
| 04 | `k7o7el` | `20260830-detrun-04-k7o7el-isolated-worktree-fault-containment-quarantine-transaction-a.ipd.md` | Worktree isolation, fault containment transaction, and commit gateway trailers | `executed:kaygwo` |
| 05 | `7f7782` | `20260830-detrun-05-7f7782-fresh-skeptical-verifier-session-tamper-evident-run-ledger-a.ipd.md` | Skeptical verifier turn, tamper-evident run ledger, and deterministic completion checker | `executed:k7o7el` |

## REPLAN NOTICE (/plan-review 2026-08-30)

This Set is `REJECT - NEEDS REPLAN`. Do NOT execute it as written, and do NOT approve it. The
reason is not a defect of craft: the plans are structurally clean (`aw ipd lint --phase author`
reports conforming for all six) and internally coherent. The reason is that they were authored
against a spec paragraph that was factually wrong at authoring time and was corrected 21 minutes
later, so the Set's central premise (that this machinery must be built) does not hold. Executing it
would create a second `Item-Dependencies` parser, a second graph evaluator, a second run ledger, and
a second capability registry alongside the shipped ones, violating GUIDING_PRINCIPLES P8 (single
source of truth; no drift) and P6 (KISS). See `## Scope check` for the per-item evidence.

A reviewer cannot repair this with bounded edits, because the fix is not a correction inside these
five children: it is a different, much smaller decomposition. Nearly all of children 01 and 05, and
the descriptor/probe half of child 02, must be deleted rather than rewritten, and the remainder must
be re-cut against boundaries owned by three approved sibling Sets. Rewriting the Set inside a review
would be authoring, not reviewing.

Minimum shape of a sound replacement (the residue that is genuinely unbuilt):

1. `From-Spec` metadata recognition plus a `check.from-spec-dangling` rule, mirroring the shipped
   `From-Backlog` precedent. Small, self-contained, and blocked by nothing. This is the one piece of
   child 01 that survives.
2. The runner-safety capability vocabulary (`isolated_worktree`, `commit_gateway`, `deny_push`,
   `fresh_verifier_session`, `argv_capture`, `timeout_cancel`), the action-to-capability requirement
   map, and the fail-closed `RUN-HOST-CAPABILITY` preflight - authored as an EXTENSION of the shipped
   `host_capability_registry.py`, not a new `host_capabilities.py`, and reconciled with `wtiso-07`,
   which already claims the typed host capability contract. Decide explicitly whether this work
   belongs to `wtiso-07` or to a successor of this Set; it must not be in both.
3. The `AW-Run:`/`AW-Item:` commit trailers and the commit gateway that emits them, wired into the
   SHIPPED ledger (`run_ledger_store.py`), sequenced AFTER `rununify` so the trailers are added once
   to a unified runner instead of twice to two diverging ones.
4. The prompt `Run contract` block and its deterministic verification.
5. The multi-type selector work of child 03 (E-01..E-04), which is the least duplicated part of the
   Set, re-scoped to consume the shipped scheduler/ledger and to leave the runtime dependency
   semantics to `lanetruth-03` rather than reimplementing them.

Before that replacement Set is authored, resolve the two blocking questions now recorded as OQ-02
and OQ-03 below, because they are ownership decisions that no amount of repository evidence can
settle.

## Completion criteria (the whole Set is done only when)

- All 5 child IPDs are verified `executed` in `.aw/records/plans/executed/`.
- `aw <host> run` resolves IPDs, specs, backlog items, and prompts with deterministic verification.
- `Item-Dependencies` is enforced across `aw check`, `aw ipd lint`, commit hooks, and runner preflight.
- Full pytest test suite passes with zero regressions.
- `aw check all` and `aw sanitize --agent` report clean repository state.

## Cross-IPD validation

- Spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) is linked and cited across all child plans.
- Release blocker `- Blocks-Release: next` is preserved across all plans.
- DAG dependency edges between child plans are satisfied sequentially.

## Deferred / out of scope (with reason)

- **Source-side dependency declarations for specs and backlog items**: Spec Section 2.8 explicitly defers source-side `Item-Dependencies` for specs and backlog items to future designs (they serve as targets in v1).
- **Authenticated cryptographic human signatures**: Spec Section 6.1 clarifies that named human approver signatures are an operational extension; `--by-human` attestation remains the speed bump in v1.

## Scope check

- **CORRECTED BY /plan-review 2026-08-30 (PR-001, BLOCKER).** The original claim below ("Over-scope:
  none") was false. It was written against a STALE paragraph of spec `25kzda` that declared the whole
  design net-new. The maintainer corrected that paragraph at commit `a59f2c53` (2026-08-30 00:35),
  AFTER this Set was authored (`453673b6` 00:08, `647bfd32` 00:14). The corrected spec now states
  plainly that `Item-Dependencies` (field, grammar, shared predicate), `aw ipd dependencies`, and
  `aw runs` ALREADY SHIPPED and "a graduating Set must CONSUME, not rebuild" them.
- Over-scope: SEVERE, and it is the reason this Set is `REPLAN`. Most of the Set re-implements
  machinery that already ships. Verified at HEAD `d4d265b6`:
  - Child 01 (`bmh754`) E-01/E-03: the grammar parser and the pure graph evaluator with cycle
    detection already exist as `ipd_schema.parse_item_dependencies` / `canonical_item_dependencies`
    (`agent_workflows/ipd_schema.py:634,690`) and `check_engine.evaluate_ipd_dependencies`
    (`agent_workflows/check_engine.py:1750`). Ran them; they accept all edge types, canonicalize
    ordering, and reject duplicates and `state:ipd:executed:`.
  - Child 01 E-02/E-04/E-05/E-06/E-07: `META_ITEM_DEPENDENCIES` is already recognized
    (`ipd_schema.py:207`); all six `check.ipd-dependency-*` rules are already registered
    (`check_engine.py:121-137`); the cutover helper already exists as
    `config.dependency_cutover_date` (`config.py:816`); phased lint already consumes the shared
    evaluator (`ipd_lint.py:1046`); `aw ipd dependencies set` already ships; and the opt-in hook
    already ships (`agent_workflows/hooks/ipd_dependency_statement_gate.py`, exposed as the
    `ipd-dependency-statement-gate` verb). Tests already exist
    (`tests/test_ipd_dependency_check.py`, `tests/test_ipd_dependency_statement_gate.py`).
  - Child 05 (`7f7782`) E-02/E-03: the append-only hash-chained ledger with integrity verification
    already ships as `run_ledger_store.py` (`prev_hash`, `BrokenChainError`), completion predicates
    and false-completion validators already ship as `run_evidence.py`, and `aw run
    show|evidence|verify-ledger` already ships (`run_cli.py`). Creating `run_ledger.py` beside
    `run_ledger_store.py` would give the repo two ledgers.
  - Child 02 (`a54m79`) E-01/E-02/E-03: a capability-evidence registry with unverified default,
    TTL expiry, fail-closed migration, and positive plus 9-class negative probe harnesses already
    ships as `host_capability_registry.py` (1593 lines, awoptimize Order `4fttzq`).
  - Genuinely net-new across the whole Set: `From-Spec` recognition plus a `check.from-spec-dangling`
    rule; the runner-safety capability VOCABULARY (`isolated_worktree`, `commit_gateway`,
    `deny_push`, `fresh_verifier_session`), which greps to zero hits and which the shipped registry
    does not cover; the action-to-capability requirement map and its fail-closed preflight; the
    `AW-Run:`/`AW-Item:` commit trailers (zero hits); and the prompt `Run contract` block.
- Under-scope: the Set never inventoried the existing `run_*` modules (11 of them: `run_engine`,
  `run_state`, `run_ledger_schema`, `run_ledger_store`, `run_evidence`, `run_freeze`, `run_gates`,
  `run_packet`, `run_recovery`, `run_cli`, `run_viewer`) nor reconciled itself against three APPROVED
  sibling Sets that own overlapping territory, so its child boundaries are not safe to execute:
  - `lanetruth-03` (`8guhs0`, approved) already owns making runner preflight consume the shared
    `Item-Dependencies` predicate and implementing the 25kzda 2.9/5.4 runtime satisfaction semantics
    in `oc_runipd.py`/`agy_runipd.py`. Child 03 E-05/E-06 duplicates it.
  - The `wtiso` Set (7 approved plans) owns worktree isolation and the driver-owned control plane,
    and `wtiso-07` (`1o4eif`, approved) explicitly owns "a typed host capability contract" plus
    fail-closed dispatch. Children 02 and 04 duplicate them.
  - `rununify` (`5e4sb6`, approved) is actively DE-DUPLICATING `oc_runipd.py`/`agy_runipd.py`.
    Children 02-05 each add new code to both runners, which fights that Set head-on.

## Required tests / validation

- `python3 -m pytest` full test suite passing with pasted counts.
- `python3 -m agent_workflows.cli check all` passing.
- `python3 -m agent_workflows.cli sanitize --agent` passing.

## Open questions

### OQ-01: How should the dependency-schema cutover commit be configured in the test harness?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 2.11
- Resolution or deferral rationale: RESOLVED, AND NOW MOOT (/plan-review PR-001). The helper already
  exists as `config.dependency_cutover_date` (`agent_workflows/config.py:816`) and is already consumed
  by `check_engine.evaluate_ipd_dependencies`. Nothing to build. Note the shipped helper keys on the
  plan's DATE, not on a cutover COMMIT as this question assumed, so a replacement Set must not
  reintroduce a commit-based variant.

### OQ-02: Does the runner-safety capability contract belong to `wtiso-07` or to a successor of this Set?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN (/plan-review PR-002). `wtiso-07` (`1o4eif`) is APPROVED and
  its Scope declares "a typed host capability contract" plus fail-closed dispatch when hard mode is
  unavailable; this Set's child 02 declares a per-host capability descriptor with fail-closed action
  gating. These are the same contract described twice. A third module already ships
  (`host_capability_registry.py`). Exactly one owner must be chosen, and the other two references
  must become consumers. This is a scope/ownership call for the maintainer, not something repository
  evidence can decide.

### OQ-03: Must the trailer and preflight work be sequenced after `rununify`?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN (/plan-review PR-003). `rununify` (`5e4sb6`, approved) exists
  to collapse the ~93 percent duplication between `oc_runipd.py` and `agy_runipd.py`. Children 02-05
  of this Set each add new code to BOTH runners, which increases exactly the duplication `rununify`
  is chartered to remove and guarantees merge pain in whichever Set runs second. The maintainer must
  decide the order (recommendation: `rununify` first, then a successor Set touches one unified
  runner) and accept the delay that implies for this Set's release gate.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste execution receipt of `detrun-01` (`bmh754`) in `executed/` and pytest run for `tests/test_item_dependencies.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste execution receipt of `detrun-02` (`a54m79`) in `executed/` and pytest run for `tests/test_host_capabilities.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste execution receipt of `detrun-03` (`kaygwo`) in `executed/` and pytest run for `tests/test_run_selector_and_queue.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste execution receipt of `detrun-04` (`k7o7el`) in `executed/` and pytest run for `tests/test_fault_containment.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste execution receipt of `detrun-05` (`7f7782`) in `executed/` and pytest run for `tests/test_deterministic_checker.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**GATE: CLOSED. This Set is `REJECT - NEEDS REPLAN` and is NOT executable.** See `## REPLAN NOTICE`.

Open questions: NOT all resolved. OQ-02 and OQ-03 are BLOCKING and are maintainer ownership/sequencing
decisions. OQ-01 is resolved but moot. Per the plan contract, a plan with an open blocking question is
NO-GO regardless of anything else in this gate.

Do NOT execute, and do NOT set this plan or any `detrun` child to `approved`. An executor who reaches
this gate must STOP and report rather than proceeding, because the work the children describe is
largely already shipped and executing them would create duplicate parsers, evaluators, ledgers, and
capability registries.

Retirement path (for whoever acts on this): this Set should be RETIRED, not executed. Per
`.aw/records/plans/README.md`, prepend a `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>`
header and `git mv` all six files to `.aw/records/plans/superseded/` once the replacement Set exists,
or to `.aw/records/plans/not-executed/` if the maintainer decides the residue is not worth a Set.
Never silently delete them; the record and the reason are the point. Do NOT file them under
`executed/`, which would falsely claim implementation.

Release gate: all six plans carry `- Blocks-Release: next`. Retiring them without a replacement would
silently drop that gate, so the residue in the REPLAN NOTICE must be re-gated onto the replacement
Set (or the gate explicitly cleared by the maintainer) as part of retirement.

Scope fence for any corrective action: touch ONLY the six `detrun` plan files under
`.aw/records/plans/pending/`. Do NOT touch product code, do NOT touch the sibling `wtiso`/`lanetruth`/
`rununify` plans (other sessions own them), and do NOT edit spec `25kzda` (it is already corrected and
approved). If it seems to need more, STOP and report.

Honesty rule (HARD MUST): when reporting tests or validation, paste the ACTUAL runner output with the
`git rev-parse HEAD` it was measured at. This review ran `aw ipd lint` and the shipped parser/evaluator
directly and reports their real output; it did NOT run the full pytest suite, because this review
changed no product code.

Execution contract: commit ONLY the plan files changed, path-scoped (`git commit -m msg -- <paths>`),
never `git add -A`, never push. This is a SHARED CHECKOUT: verify `git diff --cached --name-only`
before every commit and unstage anything not yours.
