# IPD: Resolve the .aw/system/ layout contradiction: canonical nested system/workflows/

- Date: 2026-08-16
- Kind: child
- Concern: Two executed awphysical Orders shipped contradictory assumptions about the physical shape of `.aw/system/`: Order 04 (resolver + packaging + installer tests) assumed FLAT (workflow bundle directly at `.aw/system/`), while Order 09 (`clean_delta` pointers) and the controlling spec S4.1 assume NESTED (`.aw/system/workflows/`). Order 11's self-migration is the first consumer forced to pick, and the mismatch broke source resolution (E-05: `FileNotFoundError .aw/system/index.md`). Settle the canonical layout as NESTED and reconcile the Order-04 side.
- Scope: `engine.resolve_source_root` source descent, the classifier's `agents:workflows` disposition, packaging force-include for `.aw/system`, and the focused resolver/classifier/migration tests. Does NOT change workflow bodies, records, or the migration transaction engine.
- Status: approved
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 13
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: xzuxet
- Approval: 2026-08-16 human maintainer (chat) - resolved OQ-02 (SIBLING placement) and approved this corrective layout-reconciliation IPD to execute; recorded by opencode Opus 4.8.

## Workflow history

- 2026-08-16 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created as a corrective IPD after the Order 11 (g5zl1u) Stage 3 E-05 verification exposed a cross-Order contradiction in the canonical `.aw/system/` shape. Maintainer ruled NESTED (spec-aligned, marginally better for agents: agents reach workflows by explicit path from shims + index.md, so depth is discovery-neutral and token-neutral; nested gives a clean invokable namespace separated from system metadata).
- 2026-08-16 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS. A full flat/nested census (PR-002) found the contradiction is broader than the initial Order-04 scope: `agent_workflows/__init__.py` self-version, `project_context.py:704`, `project_layout.install_system_tree` (FLAT candidate build vs NESTED read), and `is_source_checkout` VERSION level are all involved, on both sides. Added E-04 + V-04 to cover the full surface (UNDER-SCOPE fix). Surfaced a BLOCKING underspecified sub-question OQ-02 (do VERSION + manifest live at `.aw/system/` root [spec S4.1 sibling] or inside `.aw/system/workflows/` [legacy co-location]?), which must be decided before the reconciliation can be internally consistent. E-01 (resolver descent + classifier) already implemented and full suite green; E-02/E-03/E-04 pending. NO-GO pending OQ-02 + human approval. Status draft -> to-review.
- 2026-08-16 reviewed + approved (human maintainer via chat, recorded by opencode Opus 4.8): OQ-02 resolved as SIBLING (VERSION + manifest at `.aw/system/` root; only the workflow bundle nests under `.aw/system/workflows/`). All review findings resolved; no open questions remain. Status to-review -> reviewed -> approved; cleared to execute.

## Goal

Make NESTED `.aw/system/workflows/` the single canonical physical shape for the workflow bundle, consistently across the migration classifier (Order 11), the source resolver + packaging (Order 04), and the clean-delta pointers (Order 09, already nested) and spec S4.1 (already nested). After this, a real self-migration produces `.aw/system/workflows/index.md` and the installed/source-checkout resolver + packaged wheel load it without a FLAT/NESTED mismatch.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Reconcile the resolver and classifier to nested

- [ ] E-01 In `agent_workflows/engine.py resolve_source_root`, after resolving the system root, descend into `workflows/` when the bundle is nested (i.e. `<system>/index.md` is absent but `<system>/workflows/index.md` exists), so the returned root DIRECTLY contains `index.md`. Legacy `.agents/workflows` (already the bundle dir) is a no-op. In the Order-11 migration classifier, map `.agents/workflows/X -> .aw/system/workflows/X` for the bundle, EXCEPT `.agents/workflows/VERSION -> .aw/system/VERSION` (per OQ-02 SIBLING: VERSION is a system-root sibling, not part of the bundle). The self-install manifest already maps to `.aw/system/managed-sections.json` (sibling). Matches spec S4.1 and Order 09.
  - Depends on: none
  - Expected outcome: `resolve_source_root` returns the directory that directly holds `index.md` (`.aw/system/workflows/`); the migration places the bundle under `workflows/` and VERSION/manifest at the system root.
  - Execution state: pending

- [ ] E-04 Reconcile ALL remaining flat/nested VERSION+manifest decision points found by the /plan-review census to the OQ-02 resolution, so no module contradicts another: `agent_workflows/__init__.py` self-version (`resolve_version(bundled, ...)`), `agent_workflows/project_context.py:704` (`system_root/workflows/VERSION`), `agent_workflows/project_layout.py` (candidate build + install-snapshot version at :320-325/:381), and `engine.is_source_checkout` VERSION level. Add a single shared helper (or documented convention) for "the VERSION/manifest/bundle paths under a system root" so future code cannot re-diverge.
  - Depends on: E-01
  - Expected outcome: Every production reader/writer of VERSION, manifest, and the workflow bundle under a `.aw/system` root agrees on the same physical placement per the OQ-02 resolution; a grep census shows no contradictory level assumption. (Gated by OQ-02, which is a blocking open question.)
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

### /plan-review census (2026-08-16): the contradiction is broader than first scoped

A full flat/nested census of production code (not just Order 04) found the assumption scattered across MANY modules, on BOTH sides, and revealed an underspecified sub-question about VERSION/manifest placement:

| Location | Concern | Current assumption |
|---|---|---|
| `engine.py:454-471` `resolve_source_root` | source-root descent | NESTED-aware (descends into `workflows/`) - fixed under E-01 |
| `engine.py:510` `parse_manifest` | reads `<root>/index.md` | level-agnostic (OK once resolve descends) |
| `engine.py:377` `is_source_checkout` | `sys_dir/VERSION` | FLAT VERSION check (works nested only via the `managed-sections.json` fallback) |
| `agent_workflows/__init__.py:34` | package self-version | FLAT: `resolve_version(bundled, bundled/VERSION)` reads `<system>/VERSION` |
| `project_context.py:704` | resolved version file | NESTED: `system_root/workflows/VERSION` |
| `project_layout.py:320-325` | install candidate build | FLAT: `candidate/VERSION` from `source_root/VERSION` |
| `project_layout.py:381` | install snapshot version | FLAT: `system_root/VERSION` |
| `project_layout.py:420-422` | uninstall manifest probe | root-level `managed-sections.json`/`manifest.json` (consistent in BOTH layouts) |
| `clean_delta.py` | host-pointer target | NESTED: `.aw/system/workflows/<cmd>/<cmd>.md` |

Consequences:
1. The corrective surface is LARGER than the initial E-01/E-02 scope: it must also reconcile `agent_workflows/__init__.py` self-version, `is_source_checkout`'s VERSION level, and `project_layout.install_system_tree` (the installer materialize path builds a FLAT candidate `.aw/system` today, contradicting `project_context.py`'s NESTED read).
1b. E-05 re-cutover discovery (2026-08-16): with SIBLING VERSION, once the SOURCE repo has `.aw/system`, the installer resolves its source to the descended bundle root `.aw/system/workflows/`, which NO LONGER contains VERSION (now the sibling `.aw/system/VERSION`). So `collect_source_members` (rglob under the bundle root) stops shipping VERSION, and installed targets lose `.agents/workflows/VERSION` - breaking 10 installer/CLI tests (`test_fresh_install`, `test_setup_noninteractive_root_yes`, the `test_cli` install verbs, etc.). E-04 MUST also make the installer ship the sibling VERSION to the target's expected `.agents/workflows/VERSION` (e.g. `collect_source_members` additionally includes `<system_root>/VERSION` when the bundle is nested, and `install_all` resolves that member from the sibling). `read_version(source_root)` also reads `source_root/VERSION`; under nested that is the descended bundle root, so it must read the sibling `<bundle>/../VERSION`. This is the load-bearing installer-behavior reconciliation; verified failing at commit 76bd7ca when `.aw/` is present.
2. There is a genuine underspecified sub-question (OQ-02): the spec S4.1 lists `VERSION` and `manifest.json` as siblings of `workflows/` under `system/`, but the legacy `.agents/workflows/` co-locates VERSION + index.md inside the bundle. So under NESTED, does `VERSION` live at `.aw/system/VERSION` (spec sibling) or `.aw/system/workflows/VERSION` (preserve legacy co-location)? `project_context.py:704` assumes the latter; `__init__.py`/`project_layout` assume the former. This must be settled before the reconciliation can be internally consistent.

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

### OQ-01: canonical layout FLAT vs NESTED

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: Maintainer ruled NESTED (`.aw/system/workflows/`) with full agent-consumption analysis (workflows reached by explicit path, so depth is discovery/token-neutral; nested gives a clean invokable namespace and matches spec S4.1).

### OQ-02: where do VERSION and the manifest live under NESTED? (BLOCKS a consistent reconciliation)

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED 2026-08-16 (human maintainer via chat): SIBLING placement. The canonical `.aw/system/` shape is: `VERSION`, `managed-sections.json`/`manifest.json`, and `templates/` at the `.aw/system/` ROOT (metadata siblings), and only the invokable workflow bundle (`index.md` + bodies) nested under `.aw/system/workflows/`. Matches spec S4.1 exactly and gives the cleanest metadata/bundle separation. Consequences for execution: (1) the Order-11 migration must place `.agents/workflows/VERSION` -> `.aw/system/VERSION` and the self-install manifest -> `.aw/system/managed-sections.json` (already there) at the system root, i.e. split VERSION out of the bundle via a per-file destination override, while the rest of `.agents/workflows/X` -> `.aw/system/workflows/X`; (2) `project_context.py:704` is fixed to read `system_root/VERSION` (sibling); (3) `agent_workflows/__init__.py`, `project_layout`, and `is_source_checkout` already expect sibling VERSION - confirm. The workflow bundle root passed to `parse_manifest` is `.aw/system/workflows/` (resolver descent, E-01).

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
- [ ] V-04 validates E-04
  - Required evidence: Paste a grep census over production code showing every VERSION/manifest/bundle reader-writer under a `.aw/system` root uses the OQ-02-decided placement (no contradictory level), plus a test/probe that a migrated `.aw/system` reports the correct package self-version (`agent_workflows.__version__`) and resolves the version via `project_context` consistently. Failure condition: any module still reads/writes VERSION or the bundle at a level inconsistent with the OQ-02 decision.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: One layout-contract reconciliation across resolver + packaging + classifier + tests; a single cohesive correctness change.

Execution requires human approval recorded as `Status: approved` + attributed `- Approval:` line. The executor implements E-01..E-03, pastes actual command output (including the mutation probe), commits only the explicitly scoped paths (`agent_workflows/engine.py`, `tools/awphysical/aw_layout_inventory.py`, `pyproject.toml`, `hatch_build.py` if needed, and the affected tests), never pushes without confirmation, runs `aw ipd lint --phase pre-transition --agent` and the full serial suite before any transition, and the orchestrator owns the terminal move to `executed/`. This IPD is a prerequisite for completing Order 11's cutover.
