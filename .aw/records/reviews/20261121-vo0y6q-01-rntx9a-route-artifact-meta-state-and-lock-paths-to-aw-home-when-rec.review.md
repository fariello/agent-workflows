# Review findings: ipd rntx9a

- Subject-Id: rntx9a
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T064614Z-2150223`). The target plan `.aw/records/plans/pending/20261119-vo0y6q-01-rntx9a-route-artifact-meta-state-and-lock-paths-to-aw-home-when-rec.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` non-blocking `IPD-C802` info advisories on template prose). Inspection of backlog item `vo0y6q`, commit `5ca9a65a2` (2026-11-20), `agent_workflows/artifact_meta.py` (`legacy_context` plus all 13 `ctx.logical_roots["state"]` entry points including `resolve_mirror_at` and `read_path_at`), `agent_workflows/meta_cli.py` (`meta_context`), `agent_workflows/project_context.py` (`resolve_project_context`, `_stored_physical_classes`, `project_records_dir`), `agent_workflows/project_schema.py` (`ProjectContext`, `Provenance`), `agent_workflows/ipd_lint.py` (`_meta_context_and_state_map`), `tests/test_records_root_accessor.py`, and `tests/test_artifact_meta_shapes.py` surfaced three `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-005`), all fixed in place. Pass 2 re-checked `Concern`, `Scope`, `Goal`, `E-01..E-04`, `Step 0`, `Findings`, `Proposed changes`, the Mermaid flowchart, `Required tests / validation`, `Open questions`, `V-01..V-04`, and `Approval and execution gate` for full internal consistency.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Concern`, `Scope`, `Goal`, `E-01`, `Findings`, `Proposed changes`, `V-01` | Described pre-`5ca9a65a2` `legacy_context` as failing `test_home_records_reproduction_backlog` and proposed leaving `companion` on `<target>/.aw/state` | Updated premise for post-`5ca9a65a2` HEAD, resolved `resolve_project_context` first so explicit `local.json` `state_root` overrides work on external roots, and preserved `<companion>/state` clean-target routing for `companion` records (`D-1`) | PR-001, `steps/r1-references.md`, `steps/r4-engineering.md` |
| `Scope`, `E-01`, `F-04`, `Proposed changes`, `V-01` | Listed only 11 `artifact_meta.py` state-root entry points and subscripted `provenance["records_backend"]["source"]` directly | Added the 2 missed entry points (`resolve_mirror_at`, `read_path_at`, covering all 13 sites) and used defensive dict/attribute `Provenance` source access | PR-002, `steps/r1-references.md`, `steps/r4-engineering.md` |
| `Approval and execution gate` | Omitted resolved-OQ precondition, `--scope-reason`/`--scope-ack` scope fence, shared-checkout safety, explicit hand-`git mv` prohibition, no-code-pinning-tests rule, and explicit conditional runner/standalone finalize ownership | Rewrote `Approval and execution gate` with all required execution-contract clauses and conditional runner/standalone `aw ipd finalize rntx9a` ownership | PR-003, `steps/r2-executability.md`, `steps/s7-finalize.md` |
| `E-03`, `E-04`, `Required tests / validation`, `V-03`, `V-04` | Omitted direct `ProjectContext` `artifact_meta.query` test, `aw index rebuild` clean-target test, `companion` parity + `local.json` `state_root` test, `tests/test_artifact_meta_shapes.py`, `aw sanitize --agent`, and zero-source-inspection check | Added all missing behavioral test cases, zero-source-inspection constraint (`rg` check), `tests/test_artifact_meta_shapes.py`, and `aw sanitize --agent` | PR-004, `steps/r4-engineering.md` |
| `E-04`, `F-05`, `Scope`, `Goal`, `Proposed changes` | Left `E-NEW` template line, authoring-time count in `F-05`, unqualified symbol citations, and pre-revision Mermaid diagram | Removed `E-NEW` line, clarified `F-05` as authoring-time context, qualified citations to `path::Symbol`, and synchronized the Mermaid flowchart with `E-01` | PR-005, `steps/p-proofread.md` Section 11.1, technical writing standard Requirement 12(d)/(e) |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No; internal `artifact_meta` / `meta_cli` state-root routing fix keeping `agent_workflows/project_context.py::resolve_project_context` and `spec 20260810-1447-01` Section 5 unchanged without altering any CLI option, output format, or file format.
2. No; touches only metadata state/lock/cache path resolution in `agent_workflows/artifact_meta.py`, `agent_workflows/meta_cli.py`, and `tests/test_records_root_accessor.py`, with no private-data sanitizer, commit helper, worktree isolation, merge-to-main, or sandbox code.
3. No; small and focused (`4` E-items in `1` task group across `2` production files and `1` test file).
4. Yes; `- Scope-Paths:` explicitly lists `agent_workflows/artifact_meta.py`, `agent_workflows/meta_cli.py`, `tests/test_records_root_accessor.py`, and this IPD.
5. Yes; `artifact_meta.legacy_context` and `_meta_state_root` govern lock and SQLite cache placement for every metadata reader and writer across all backends (`home`, `companion`, `repository`, `repository-untracked`, `clean-delta`, and unconfigured), so a wrong redirect could split locks from `index.db`, drop `local.json` `state_root` overrides, or regress clean-target isolation.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261117-vo0y6q-01-vo0y6q-backlog-new-home-records-target-state-lock.backlog.md`, commit `5ca9a65a2`, `agent_workflows/artifact_meta.py` (`legacy_context` and all 13 `ctx.logical_roots["state"]` call sites), `agent_workflows/meta_cli.py` (`meta_context`), `agent_workflows/project_context.py` (`resolve_project_context`, `_stored_physical_classes`, `project_records_dir`), `agent_workflows/project_schema.py` (`ProjectContext`, `Provenance`), `agent_workflows/ipd_lint.py` (`_meta_context_and_state_map`), `tests/test_records_root_accessor.py`, and `tests/test_artifact_meta_shapes.py`.
- Found that commit `5ca9a65a2` (2026-11-20) had already modified `legacy_context` for external records roots (making `F-01`/`F-02` stale and introducing a `local.json` `state_root` bypass and `companion` preservation requirement, `PR-001`), and that two new `artifact_meta.py` functions (`resolve_mirror_at`, `read_path_at`) also read `ctx.logical_roots["state"]` (`PR-002`). All fixed in place.

### Step R2

- Checked: `E-*`/`V-*` bijection (`4/4`: `E-01..E-04` <-> `V-01..V-04`, `- Highest E allocated: 04`), dependency chain (`E-01 -> E-02 -> E-03 -> E-04`), `- Scope-Paths:` completeness, `- Item-Dependencies: none`, runtime reachability of `V-01..V-04` (all demand git diffs, Python/pytest outputs, `rg`, or `aw` CLI outputs, reachable by construction), and `Approval and execution gate`.
- Found non-conforming execution contract in `Approval and execution gate` (`PR-003`) and leftover `E-NEW` template text (`PR-005`). Both fixed in place.

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). Routing `artifact_meta` locks, journals, and `index.db` under `<AW_HOME>/projects/<project_id>/state` (for `home`) and `<companion>/state` (for `companion`) prevents leaking private metadata identifiers (`meta-<id6>.lock`, `index.db`) into a clean public target repository working tree, while respecting explicit `local.json` `state_root` overrides preserves operator-configured trust boundaries. No secrets, outbound calls, or privileged bypasses are introduced.

### Step R4

- Checked: correctness and data integrity (`PR-001` honors `local.json` `state_root` first and preserves `5ca9a65a2`'s clean-target routing for `companion`; `PR-002` closes all 13 `artifact_meta.py` `logical_roots["state"]` sites including `resolve_mirror_at` and `read_path_at`), anti-regression and testing (`PR-004` adds direct `ProjectContext` `artifact_meta.query`, `aw index rebuild`, `companion` + `local.json` `state_root` parity, zero-source-inspection check, `tests/test_artifact_meta_shapes.py`, and `aw sanitize --agent`), right-sizing (`4` E-items, `4` Scope-Paths, cohesive single bugfix), and `## Spec / documentation sync` (`None` verified truthful against `spec 4sd62s` Section 4.5 and `spec 20260810-1447-01` Section 5).

### Step S5

- Checked: `## Open questions` (`OQ-01` and `OQ-02`, both `Blocking: no`, `Status: resolved`, `Owner: plan author`, verified against `agent_workflows/project_context.py::resolve_project_context:2190-2216`). Every finding (`PR-001..PR-005`) has `Overall:Low` Remediation Risk and is settled by repository evidence. Recorded `D-1` (`Reversible: yes`) in `### Decisions`. Zero blocking or human-owned questions remain.

### Pass 2

- Re-checked the complete revised plan across `Concern`, `Scope`, `Goal`, `E-01..E-04`, `Step 0`, `Findings`, `Proposed changes`, Mermaid flowchart, `Deferred / out of scope`, `Scope check`, `Required tests / validation`, `Spec / documentation sync`, `Open questions`, `V-01..V-04`, and `Approval and execution gate`.
- Verified `4/4` E/V bijection, `- Highest E allocated: 04`, zero unresolved questions, and clean `aw ipd lint --phase review-finalize --agent` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / R4 / Post-`5ca9a65a2` premise, `local.json` `state_root`, and `companion` preservation | .aw/records/plans/pending/20261119-vo0y6q-01-rntx9a-route-artifact-meta-state-and-lock-paths-to-aw-home-when-rec.ipd.md:5-6,38-41,74-76,91-93; agent_workflows/artifact_meta.py::legacy_context:6028-6060 | Commit `5ca9a65a2` (2026-11-20) added `if not records_res.is_relative_to(root): state = records_res.parent / "state"` to `legacy_context`, so `F-01`/`F-02` are stale at HEAD, `5ca9a65a2`'s shortcut silently ignores explicit `local.json` `state_root` overrides on external records roots, and reverting `companion` back to `<target>/.aw/state` as `rntx9a` originally wrote would regress `5ca9a65a2`'s clean-target protection for `companion` repos. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `Concern`, `Scope`, `Goal`, `E-01`, `Findings` (`F-01`, `F-02`), `Proposed changes` (and Mermaid flowchart), and `V-01` to resolve `resolve_project_context` first (honoring explicit `local.json` `state_root`), redirect default `<repo>/.aw/state` to `<AW_HOME>/projects/<project_id>/state` for stored `home`, and preserve `<companion>/state` for external `companion` records (`D-1`). Recommendation strength: very strong. |
| PR-002 | HIGH | UNDER-SCOPE | R1 / R4 / Missing `artifact_meta.py` state-root sites | .aw/records/plans/pending/20261119-vo0y6q-01-rntx9a-route-artifact-meta-state-and-lock-paths-to-aw-home-when-rec.ipd.md:38,77,82; agent_workflows/artifact_meta.py::resolve_mirror_at:5381; agent_workflows/artifact_meta.py::read_path_at:5517 | `E-01` and `F-04` listed 11 `artifact_meta.py` state-root entry points and missed `resolve_mirror_at` and `read_path_at` (all 13 `ctx.logical_roots["state"]` call sites), and subscripted `provenance["records_backend"]["source"]` without guarding `Provenance` objects. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `resolve_mirror_at` and `read_path_at` to `Scope`, `E-01`, `F-04`, `Proposed changes`, and `V-01`, and used defensive dict/attribute `Provenance` source extraction. Recommendation strength: very strong. |
| PR-003 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261119-vo0y6q-01-rntx9a-route-artifact-meta-state-and-lock-paths-to-aw-home-when-rec.ipd.md:162-167; .aw/system/workflows/plan-review/steps/r2-executability.md:57-60; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | `Approval and execution gate` omitted the resolved-blocking-open-questions precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule, shared-checkout safety, explicit prohibition on hand-`git mv` to `executed/`, no-code-pinning-tests rule, and explicit conditional runner-versus-standalone `aw ipd finalize rntx9a` ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` with all required execution-contract clauses and conditional runner/standalone finalize ownership. Recommendation strength: very strong. |
| PR-004 | MEDIUM | UNDER-SCOPE | R4 / Behavioral testing and verification coverage | .aw/records/plans/pending/20261119-vo0y6q-01-rntx9a-route-artifact-meta-state-and-lock-paths-to-aw-home-when-rec.ipd.md:48-56,152-160; tests/test_artifact_meta_shapes.py:166-180; agent_workflows/ipd_lint.py::_meta_context_and_state_map:600 | `E-03` did not test direct `ProjectContext` `artifact_meta.query` clean-target routing, `aw index rebuild --dir <target>` on `home_records_env`, or `companion` default + `local.json` `state_root` parity, and omitted the no-code-pinning check; `E-04` omitted `tests/test_artifact_meta_shapes.py` and `aw sanitize --agent`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expanded `E-03`/`V-03` with direct `ProjectContext` `artifact_meta.query`, `aw index rebuild`, `companion` parity, and zero-source-inspection verification, and added `tests/test_artifact_meta_shapes.py` and `aw sanitize --agent` to `E-04`/`V-04`. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | Proofreading / R1 / Technical writing standard | .aw/records/plans/pending/20261119-vo0y6q-01-rntx9a-route-artifact-meta-state-and-lock-paths-to-aw-home-when-rec.ipd.md:6,58,78,80-96 | Plan contained a leftover `E-NEW` template instruction, unqualified symbol references, stale authoring-time test count in `F-05`, and a Mermaid flowchart needing alignment with the refined `E-01` logic. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed the `E-NEW` template line, qualified citations to `path::Symbol`, reframed `F-05` as authoring-time context, and synchronized the Mermaid diagram with `E-01`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `artifact_meta.legacy_context` and `artifact_meta._meta_state_root` handle `companion` external records roots and explicit `local.json` `state_root` overrides post-`5ca9a65a2`? | Resolve `project_context` first so any explicit `local.json` `state_root` override (`state != repo_root/.aw/state`) is honored on all backends, then redirect default tracked `<repo>/.aw/state` to `<AW_HOME>/projects/<project_id>/state` for stored `home` and preserve `<companion>/state` (`records_res.parent / "state"`) for external `companion` records across `legacy_context`, `meta_context`, and all 13 `artifact_meta` entry points. | Restrict the override to `home` only and revert `companion` back to `<target>/.aw/state` (rejected: regresses commit `5ca9a65a2`'s clean-target protection for `companion` repositories), or keep `5ca9a65a2`'s `if not records_res.is_relative_to(root)` shortcut untouched (rejected: ignores explicit `local.json` `state_root` overrides and leaves `meta_cli.meta_context` and all 13 direct `ProjectContext` `artifact_meta` sites broken). | `agent_workflows/artifact_meta.py::legacy_context:6028-6060` (commit `5ca9a65a2`), `agent_workflows/project_context.py::resolve_project_context:2190-2216`, `agent_workflows/meta_cli.py::meta_context:72-93` | yes |
