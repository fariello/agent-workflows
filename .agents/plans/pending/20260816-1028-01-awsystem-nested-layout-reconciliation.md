# IPD: Resolve the .aw/system/ layout contradiction: canonical nested system/workflows/

- Date: 2026-08-16
- Kind: child
- Concern: Two executed awphysical Orders shipped contradictory assumptions about the physical shape of `.aw/system/`: Order 04 (resolver + packaging + installer tests) assumed FLAT (workflow bundle directly at `.aw/system/`), while Order 09 (`clean_delta` pointers) and the controlling spec S4.1 assume NESTED (`.aw/system/workflows/`). Order 11's self-migration is the first consumer forced to pick, and the mismatch broke source resolution (E-05: `FileNotFoundError .aw/system/index.md`). Settle the canonical layout as NESTED and reconcile the Order-04 side.
- Scope: `engine.resolve_source_root` source descent, the classifier's `agents:workflows` disposition, packaging force-include for `.aw/system`, and the focused resolver/classifier/migration tests. Does NOT change workflow bodies, records, or the migration transaction engine.
- Status: draft
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 13
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: xzuxet

## Workflow history

- 2026-08-16 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created as a corrective IPD after the Order 11 (g5zl1u) Stage 3 E-05 verification exposed a cross-Order contradiction in the canonical `.aw/system/` shape. Maintainer ruled NESTED (spec-aligned, marginally better for agents: agents reach workflows by explicit path from shims + index.md, so depth is discovery-neutral and token-neutral; nested gives a clean invokable namespace separated from system metadata).

## Goal

Make NESTED `.aw/system/workflows/` the single canonical physical shape for the workflow bundle, consistently across the migration classifier (Order 11), the source resolver + packaging (Order 04), and the clean-delta pointers (Order 09, already nested) and spec S4.1 (already nested). After this, a real self-migration produces `.aw/system/workflows/index.md` and the installed/source-checkout resolver + packaged wheel load it without a FLAT/NESTED mismatch.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Reconcile the resolver and classifier to nested

- [ ] E-01 In `agent_workflows/engine.py resolve_source_root`, after resolving the system root, descend into `workflows/` when the bundle is nested (i.e. `<system>/index.md` is absent but `<system>/workflows/index.md` exists), so the returned root DIRECTLY contains `index.md`. Legacy `.agents/workflows` (already the bundle dir) is a no-op. Keep the Order-11 migration classifier mapping `.agents/workflows/X -> .aw/system/workflows/X` (NO wrapper strip), matching spec S4.1 and Order 09.
  - Depends on: none
  - Expected outcome: `resolve_source_root` returns the directory that directly holds `index.md` for both legacy and nested `.aw/system` layouts; the classifier preserves the `workflows/` level.
  - Execution state: pending

### Task group 2: Packaging carries the nested system tree

- [ ] E-02 Add the deferred `.aw/system` force-include (wheel) and sdist include so a built package ships the nested `.aw/system/workflows/` tree, and confirm `_compat.packaged_source_root()` + `resolve_source_root` resolve the packaged bundle to `<pkg>/_data/.aw/system/workflows`. Only declare the include once `.aw/system/` exists in the source tree (created by the Order 11 cutover), so hatchling does not fail on a missing path.
  - Depends on: E-01
  - Expected outcome: `python -m build` produces a wheel/sdist whose bundled system loads via the resolver; package inspection shows the nested workflow bundle present once.
  - Execution state: pending

### Task group 3: Lock it with tests

- [ ] E-03 Add/adjust falsifiable tests: the classifier maps `.agents/workflows/X -> system/workflows/X` (no strip); a migrated `.aw/system/workflows/` is loadable by `resolve_source_root` + `parse_manifest`; and the full suite + `tools.awphysical` tests pass. Mutation-probe the resolver descent (removing it must reproduce the E-05 `index.md`-not-found failure).
  - Depends on: E-01, E-02
  - Execution state: pending

## Project conventions discovered (Step 0)

- The engine's `resolve_source_root` already VALIDATED both `<system>/index.md` and `<system>/workflows/index.md` (Order 04 half-anticipated nested) but did not DESCEND, so `parse_manifest(<system>)` read the wrong path under nested.
- `is_source_checkout` accepts `.aw/system` via `managed-sections.json`/`VERSION`/`manifest.json` markers (still true under nested; `managed-sections.json` sits at `.aw/system/`).
- `clean_delta.py` (Order 09) already emits `.aw/system/workflows/<cmd>/<cmd>.md` pointers (nested); its tests + the order09 fixture + `test_awphysical_postcheck_deception` agree.
- Spec S4.1 lists `system/` as containing `workflows/` (nested) plus `VERSION`, `manifest.json`, `templates/`, skills as siblings.
- `pyproject.toml` explicitly reserves re-adding the `.aw/system` force-include for the Order-11 cutover.

## Findings

- FLAT camp (pre-fix): `_compat.SYSTEM_DATA_RELATIVE`, `engine.resolve_source_root` (read `<system>/index.md`), `parse_manifest`, `test_installer`/`test_packaging`/`test_cli`.
- NESTED camp: `clean_delta.py` + its tests + fixture, spec S4.1.
- The engine's dual validity check made the contradiction latent until Order 11 produced a real `.aw/system/`.
- Agent-consumption analysis: workflows are reached by explicit path (host shims `Read and execute @.../<cmd>/<cmd>.md`, `index.md` manifest), never by scanning `system/`; so nesting depth is discovery- and token-neutral. Nested wins only on reasoning clarity (clean invokable namespace).

## Proposed changes (ordered, validatable)

1. Descend into `workflows/` in `resolve_source_root` (nested-aware); keep classifier nested.
2. Add packaging force-include/sdist for `.aw/system`.
3. Tests + mutation probe.

## Deferred / out of scope (with reason)

- The Order 11 cutover itself (creating `.aw/`, records/config/state) remains Order 11's job; this IPD only settles the system-layout contract it depends on.
- No workflow body, record, or migration-engine change.

## Scope check

- Over-scope: none; confined to source-root resolution, packaging, classifier disposition, and tests.
- Under-scope: resolver descent, packaging, classifier, and their falsifiable tests are all included.

## Required tests / validation

- `python3 -m unittest tests.test_installer tests.test_packaging tests.test_cli tests.test_layout_migration`
- `python3 -m unittest tools.awphysical.test_awphysical_tools`
- `python3 -m unittest discover -s tests -t .` (full serial suite)
- `python -m build` + wheel/sdist inspection for the nested bundle (E-02).
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

### Per-item evidence matrix

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_layout_migration.TestLayoutMigration.test_migrated_system_is_loadable_by_source_resolver tools.awphysical.test_awphysical_tools.InventoryTests.test_workflows_migrate_under_system_workflows` | migrated `.aw/system/workflows/` on a temp repo | Migration maps `.agents/workflows/X -> system/workflows/X`; `resolve_source_root` descends and `parse_manifest` loads `.aw/system/workflows/index.md`. | classifier strips `workflows/`, or resolver fails to find `index.md` under nested |
| E-02 | `python -m build && python3 - <<'PY' ...inspect wheel/sdist...` | built wheel + sdist | Package ships `_data/.aw/system/workflows/index.md`; `packaged_source_root()`+resolver load it. | `.aw/system` absent from the artifact or resolver cannot load the packaged bundle |
| E-03 | `python3 -m unittest discover -s tests -t . && python3 -m unittest tools.awphysical.test_awphysical_tools` | full suite + tools | All green; mutation-probe of the resolver descent reproduces the E-05 not-found failure then restores. | any test red, or the descent cannot be mutation-probed |

## Spec / documentation sync

- Spec S4.1 already describes nested; no spec change required (this IPD reconciles the CODE to the spec).
- Note in `pyproject.toml` where the `.aw/system` include is added.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Maintainer ruled NESTED with full analysis; the resolver already half-supported it, so the corrective surface is small and unambiguous.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Run the E-01 command; paste output showing the classifier maps to `system/workflows/...` and the migrated `.aw/system/workflows/` loads via `resolve_source_root`+`parse_manifest`. Failure condition observed by mutation (remove the descent -> `index.md` not found).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Build the package; paste inspection proving `_data/.aw/system/workflows/index.md` is present and the resolver loads the packaged bundle.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste the full serial suite + tools result (all green) and the resolver-descent mutation probe (RED then GREEN).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: One layout-contract reconciliation across resolver + packaging + classifier + tests; a single cohesive correctness change.

Execution requires human approval recorded as `Status: approved` + attributed `- Approval:` line. The executor implements E-01..E-03, pastes actual command output (including the mutation probe), commits only the explicitly scoped paths (`agent_workflows/engine.py`, `tools/awphysical/aw_layout_inventory.py`, `pyproject.toml`, `hatch_build.py` if needed, and the affected tests), never pushes without confirmation, runs `aw ipd lint --phase pre-transition --agent` and the full serial suite before any transition, and the orchestrator owns the terminal move to `executed/`. This IPD is a prerequisite for completing Order 11's cutover.
