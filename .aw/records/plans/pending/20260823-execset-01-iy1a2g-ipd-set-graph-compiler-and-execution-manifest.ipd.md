# IPD: IPD Set Graph Compiler and Execution Manifest

- Date: 2026-08-23
- Kind: child
- Concern: Convert approved IPD Sets into deterministic, schedulable work.
- Scope: Set selection, IPD/E-item parsing, inter-plan dependencies, resource ownership, work classification, and plan-only output.
- Status: reviewed
- Set: execset
- Order: 1
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: iy1a2g

## Workflow history
- 2026-08-23 /plan-review focused (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (LaneRequest adapter/mapping + compiler-side serial-on-uncertainty made explicit in E-02/V-02), PR-002 (deferred_gate is net-new), PR-003 (cross-IPD child-table Depends-on parsing is net-new, compiler-owned), PR-004 (cite reuse: run_freeze/run ledger head/workflow_compiler), PR-005 (OQ-02: plan approval has no --by-human gate; documented trust boundary).
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-002 (corrected `ipd_lint.parse()` API claim: Depends-on graph is derived in the lint pass, not returned by parse()).
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created after current parser/runtime audit.

## Goal

Build a validated cross-IPD DAG and immutable execution manifest before any model or worktree is launched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Resolve and gate the Set

- [ ] E-01 Implement `agent_workflows/ipd_set_plan.py` using `plans_index`, selectors, and `ipd_lint.parse()` to resolve stable IDs, parse E-item leaves/dependencies, reject globally invalid Set structure, and classify an individually unapproved child as `deferred_gate` so only its descendants block while independent approved children continue.
  - Depends on: none
  - Note (verified - two net-new pieces the compiler OWNS): (1) `deferred_gate` and descendant-only blocking do NOT exist today (no plan-graph gating in the codebase; only the unrelated spec `deferred` gate exists). Per-child approval IS readable per file (`plans_index` exposes each child's `- Status:`, `set_id`, `order`; `approved`/`auto-approved` = approved), but the classification and "block descendants, continue independent siblings" propagation is entirely this plan's to build. (2) Cross-IPD (child->child) dependency edges are NOT parsed anywhere: `ipd_schema.parse_depends_on` (`ipd_schema.py:357`) handles ONLY intra-IPD `E-*` ids; the orchestrator's `## Child IPDs, sequence, and dependencies` table is unparsed markdown (`H_CHILD_IPDS` is only a heading constant). E-01 must parse that orchestrator child-table's `Depends on` column itself, with the E-03 legacy-inference fallback when the table is absent/ambiguous (ambiguity serializes, never prompts).
  - Expected outcome: one deterministic inventory contains every child and E/V leaf exactly once.
  - Execution state: pending

### Material change 2: Compile graph and ownership

- [ ] E-02 Compile inter-IPD dependencies and per-node `reads/writes/generates/shared_surfaces`, work class, model role, validation, deferrability, and confidence into `execution-plan.json`; uncertainty forces serial eligibility.
  - Depends on: E-01
  - Note (verified - adapter required): the manifest node schema does NOT map 1:1 to `analyze_concurrency_eligibility()`'s `LaneRequest` (`orchestrate_isolation.py:632-652`). The analyzer consumes `lane_id/actor_role/lane_kind/files_targeted/generated_files/depends_on/worktree_path/isolation_mode` and has NO `reads`, `shared_surfaces`, `work_class`, `deferrable`, or `confidence` inputs. E-02 MUST include a compiler-side adapter: `node->lane_id`, `writes->files_targeted`, `generates->generated_files`, derive `lane_kind` (read_only vs mutating) and `worktree_path`, fold `shared_surfaces` into the conflict file-sets, and - because the analyzer does NOT implement "uncertainty forces serial" - the COMPILER enforces serial eligibility for any node whose `confidence` is not `declared`/high before calling the analyzer. `reads` is retained in the manifest for provenance but is not an analyzer input.
  - Expected outcome: the existing concurrency analyzer receives typed lanes (via the adapter) instead of prose guesses.
  - Execution state: pending

### Material change 3: Expose plan-only inspection

- [ ] E-03 Add `aw ipd execute-set <set-id> --plan-only --agent` with compact human and stable JSON output, plus fixtures for legacy orchestrator tables and optional future structured hints.
  - Depends on: E-02
  - Expected outcome: users and agents can inspect waves, serial fallbacks, ownership, and model assignments without executing.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `ipd_lint.parse()` (`agent_workflows/ipd_lint.py:212`) returns `ParsedDoc.exec_leaves` (the E-item leaves, each with a `fields` dict). NOTE (verified): the within-IPD `Depends on` dependency GRAPH is NOT returned by `parse()`; it is derived inside the lint pass (`ipd_lint.py:539-547`, via `ipd_schema.parse_depends_on`). E-01 must therefore read `Depends on` from each leaf's `fields` and build the intra-IPD edge map itself (or lift that logic), rather than expecting `parse()` to hand back a dependency graph. Between-IPD dependencies and resource ownership are entirely absent and are this plan's to add.
- `status_set` and `plans_index` already resolve artifacts/Sets; stable IPD `Id` survives lifecycle moves.
- Unknown IPD metadata currently fails lint; use a per-run manifest first rather than silently extending front matter.

## Findings

`Order` alone cannot prove parallel independence. Current dependency/file fences often live in prose. A model may propose the manifest, but deterministic validation and conservative serial fallback must decide eligibility.

## Proposed changes (ordered, validatable)

```json
{"node":"abc123:E-02","depends_on":["abc123:E-01"],"work_class":"coding","model_role":"coding","writes":["agent_workflows/ipd_set_executor.py"],"shared_surfaces":["agent_workflows/cli.py"],"deferrable":true,"confidence":"declared"}
```

Require upstream child completion at verified terminal lifecycle, not merely `performed`. Freeze source IPD digests and base HEAD into the manifest.

Reuse existing primitives - do NOT reinvent freezing/digesting or byte-stable emit (all verified present, from the awoptimize Set):
- Digests: `run_freeze.freeze_requirements()` (`agent_workflows/run_freeze.py:131-172`) produces per-item sha256 `digest` + a set-level `requirement_digest`, with cosmetic-edit normalization; use it to freeze source IPD digests.
- Base HEAD: the run ledger `run` record already carries `head`/`repo`/`requirement_digest` (`run_ledger_schema.py:128-133`); freeze base HEAD there rather than inventing a field.
- Deterministic bytes: follow `workflow_compiler`'s sorted-keys/fixed-separator emit (`agent_workflows/workflow_compiler.py:56-62`) so `execution-plan.json` is byte-stable (V-03).
The `execution-plan.json` container is the only genuinely new artifact; its contents are assembled from these existing primitives.

## Deferred / out of scope (with reason)

- Scheduling/execution is Order 03; record types are Order 02.
- Optional IPD schema hints can follow after compatibility evidence; v1 uses the run manifest.

## Scope check

- Over-scope: none.
- Under-scope: include generated files, lockfiles, schemas, version/changelog, IPD/history, and decision logs as shared surfaces.

## Required tests / validation

Test empty/missing/duplicate Sets, globally invalid orchestrators, isolated unapproved children with independent approved siblings, cycles, legacy tables, parallel candidates, ambiguous serial fallback, mixed work, stable IDs after move, and deterministic plan bytes.

## Spec / documentation sync

Document the execution-manifest schema and legacy inference rules.

## Open questions

### OQ-01: Must v1 extend IPD front matter?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no; generate and freeze a per-run manifest. Propose optional hints only after v1 experience.

### OQ-02: What exactly is the approval trust boundary the compiler reads?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: the compiler treats a child's front-matter `- Status: approved` (or `auto-approved`) as the signal to include it as runnable; any other status classifies it `deferred_gate`. NOTE (verified): unlike SPECS, PLAN approval has NO `--by-human` attestation gate in `status_set` (`status_set.py:318-333` special-cases specs only), so `approved` on a plan is trusted at face value. The compiler MUST NOT itself set or infer approval; it only reads the recorded status. Downstream launch authority (Orders 03-04) remains gated separately - the manifest never grants execution authority.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: parser/selector tests show exact Set inventory, global-invalid rejection, child-level approval deferral/descendant propagation, continued independent siblings, E-item DAG, and cycle rejection. SPECIFICALLY: (a) a fixture with an orchestrator child-table proves the `Depends on` column is parsed into cross-IPD edges, and a fixture WITHOUT/with an ambiguous table proves legacy inference falls back to serial (never prompts); (b) a fixture with one unapproved child among approved siblings proves the unapproved child is classified `deferred_gate`, ONLY its descendants are blocked, and independent approved siblings remain runnable.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: golden manifests show stable node IDs, frozen source/base digests, complete resource/model/validation fields, correct cross-IPD edges, cycle rejection, and conservative serialization for ambiguous ownership. ADDITIONALLY: a test proves the manifest->`LaneRequest` adapter maps `writes->files_targeted` and `generates->generated_files`, derives `lane_kind`/`worktree_path`, folds `shared_surfaces` into the conflict sets, and that a node with non-`declared`/low `confidence` is forced onto a serial lane by the COMPILER before `analyze_concurrency_eligibility()` is called (the analyzer never sees an unresolved `confidence`).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: human and `--agent` plan-only snapshots report identical waves, leases, serial fallbacks, and model roles; repeated compilation is byte-stable and launches no worker.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes produce and expose one immutable execution plan.

Requires executed awoptimize runtime foundations and explicit approval. Touch only planner, CLI registration, schema/fixtures, and focused tests; never launch models.
