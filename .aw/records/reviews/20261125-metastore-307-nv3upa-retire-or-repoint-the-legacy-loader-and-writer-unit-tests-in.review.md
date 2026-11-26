# Review findings: ipd nv3upa

- Subject-Id: nv3upa
- Subject-Type: ipd
- Reviewed-At: 2026-11-26
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261126T020242Z-3080634`). The target plan `.aw/records/plans/pending/20261125-metastore-307-nv3upa-retire-or-repoint-the-legacy-loader-and-writer-unit-tests-in.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings). The review examined backlog `ldfefd`, spec `4sd62s` (C10a, Sections 4.3, 5.2, 5.3, AC-14a, AC-15), `Set: metastore` siblings `2k5t16`, `89mtbl`, `cugg3w`, and `x1mmdp`, `.aw/system/cutover/metastore-code.cutover.patch` (confirming exact functions removed from `artifact_meta.py` and added to `m0001_metadata_v2.py`), all five target test modules (`tests/test_artifact_meta_legacy.py`, `tests/test_artifact_meta_shapes.py`, `tests/test_artifact_meta_legacy_write.py`, `tests/test_artifact_meta_legacy_writer.py`, `tests/test_m0001_sidecar.py`), and `tests/test_artifact_meta_write.py`. It found two `BLOCKER`, two `HIGH`, and one `MEDIUM` findings (`PR-001..PR-005`), all `Overall:Low` remediation risk and all fixed in place. No production code or test code was modified.

### Step T

1. No direct public-interface or spec change (edits test modules only inside `.aw/system/cutover/metastore-code.cutover.patch`), though all downstream test-conversion batches (`cugg3w..x3mig6`) and `x1mmdp` depend on `executed:nv3upa` and the regenerated cumulative patch.
2. No; it does not touch private-data sanitizers, commit/lock helpers, worktree isolation, merge-to-main gates, or host sandbox profiles.
3. No; bounded to 5 execution items across 3 task groups, focused on one cohesive concern (repointing or retiring the five legacy loader/writer/sidecar unit-test modules inside the inert code patch).
4. Yes; `- Scope-Paths:` declares both tracked files modified by this plan (the plan file itself and `.aw/system/cutover/metastore-code.cutover.patch`).
5. Yes; retiring `test_artifact_meta_legacy_write.py` without migrating uncovered AC-14a, AC-15, and writer-leak invariants would silently drop regression coverage for surviving log-writer guarantees, and mishandling the cumulative code patch could corrupt prior hunks.

AW-TIER: standard

### Step R1

- Checked: every target test module and patch hunk: `tests/test_artifact_meta_legacy.py` (21 tests; 15 calls to `meta.load_legacy_artifact`, plus `load_legacy_review`, `read_text`, `history_records`, `_newest_history_record`, `_last_history_at`), `tests/test_artifact_meta_shapes.py` (6 tests exercising phase-B `artifact_meta.query`/`read`/`history` over `tests/migration_corpus.py` plus `derive_id6`, `LegacyRender`, `SidecarRecord`), `tests/test_artifact_meta_legacy_write.py` (27 tests including AC-14a, AC-15, and writer-leak tests), `tests/test_artifact_meta_legacy_writer.py` (11 tests exercising `write_legacy`/`render_legacy_text`/`restore_legacy_snapshot`), `tests/test_m0001_sidecar.py` (4 tests calling `m0001_metadata_v2.run`/`rollback` and 1 call to `artifact_meta.load_legacy_artifact` at line 312, zero uses of `SidecarRecord`), `tests/test_artifact_meta_write.py` (12 tests, confirming AC-14a/AC-15/writer-leak tests are absent there), and `.aw/system/cutover/metastore-code.cutover.patch` (confirming `load_legacy_artifact` and `derive_id6` moved to `m0001_metadata_v2.py` while `load_legacy_review`, `read_text`, `history_records`, `_newest_history_record`, `_last_history_at` stayed in `artifact_meta.py`).
- Found: `tests/test_m0001_sidecar.py` never imports `SidecarRecord`; it fails solely on `artifact_meta.load_legacy_artifact` (`PR-001`). `tests/test_artifact_meta_shapes.py` tests phase-B legacy cache scanning and `derive_id6`/`LegacyRender`/`SidecarRecord`, not `load_legacy_artifact` (`PR-002`). `tests/test_artifact_meta_legacy_write.py` contains surviving AC-14a, AC-15, and writer-leak invariants not covered by `tests/test_artifact_meta_write.py` (`PR-003`). The cited `.aw/state/lane-submissions/.../failing-modules.txt` file is gitignored and absent in isolated lanes (`PR-004`). All fixed in place.

### Step R2

- Checked: E/V bijection (`5/5`: `E-01..E-05` to `V-01..V-05`, `- Highest E allocated: 05`), dependency chain (`E-01 -> E-02 -> E-03 -> E-04 -> E-05`), `- Scope-Paths:` (2 tracked paths), `- Item-Dependencies: executed:89mtbl` (matching `63ib9r` row 307), concrete `V-*` evidence (all reachable by construction), durable carriers (`cugg3w`, `cxxmyv`), and `## Approval and execution gate`.
- Found: `E-04`/`V-04` ran `rg` over "the five paths" even after `E-03` deletes two of them (which causes `rg` to exit 2 on missing files) and left the removed-symbol pattern unspecified (`PR-004`); `## Approval and execution gate` unconditionally instructed running `aw ipd finalize`, `E-01` omitted exact patch paths, and `V-05` omitted clean-tree confirmation (`PR-005`). All fixed in place.

### Step R3

- Checked (full form, `standard` tier):
  - Security regression preservation: `tests/test_artifact_meta_legacy_write.py::test_owned_message_with_home_path_is_refused_by_the_writer` (writer leak sanitizer refusal) and AC-15/AC-14a event-ownership tests (`readiness`, `coverage`, `approval`, `review_kind`) guard trust boundaries against forged readiness/approval and local-path leaks. Requiring `E-03` to audit and migrate any uncovered invariant into `tests/test_artifact_meta_write.py` prevents silently losing those security checks (`PR-003`).
  - Workspace containment: edits occur strictly inside gitignored `.aw/state/nv3upa/scratch`, removed before commit; no live code, secrets, or outbound calls are touched.

### Step R4

- Checked: correctness, anti-regression, testing/verification, KISS, right-sizing/conceptual density per E-item, and `## Spec / documentation sync`.
- Found:
  - Misdiagnosis of `tests/test_m0001_sidecar.py` (`PR-001`) and `tests/test_artifact_meta_shapes.py` (`PR-002`).
  - Missing explicit audit/migration requirement for surviving AC-14a, AC-15, and writer-leak invariants in `tests/test_artifact_meta_legacy_write.py` (`PR-003`).
  - Absent gitignored census path and `rg`-on-deleted-files hazard (`PR-004`).
- Right-sizing check: 5 E-items across 3 task groups, 1 work `Scope-Path` (`.aw/system/cutover/metastore-code.cutover.patch`). Each E-item owns one clear unit (scratch setup, loader+shapes tests, writer test audit/retirement, sidecar repoint + verification, patch packaging) and fits one focused pass. No split needed.

### Step S5

- Checked: `## Open questions` (`None open`). All five findings (`PR-001..PR-005`) have `Overall:Low` remediation risk and are settled by authoritative repository evidence (`tests/test_m0001_sidecar.py`, `tests/test_artifact_meta_*.py`, `metastore-code.cutover.patch`, and spec `4sd62s`). Three reversible review decisions are recorded in `### Decisions` (`D-1..D-3`). No blocking or human-owned question remains; outcome JSON records `{"questions": []}`.

### Pass 2

- Re-checked the complete revised plan: front matter, `## Workflow history`, `## Goal`, `E-01..E-05`, `## Project conventions discovered (Step 0)`, `## Findings` (`F-01..F-04`), `## Proposed changes` and Mermaid `flowchart TD`, `## Deferred / out of scope` (carriers `cugg3w`, `cxxmyv`), `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync`, `## Open questions`, `V-01..V-05`, and `## Approval and execution gate`.
- Swept for superseded wording (removed every false reference to `SidecarRecord` in `test_m0001_sidecar.py`; corrected `test_artifact_meta_shapes.py` handling from `load_legacy_artifact` to `derive_id6` + phase-B retirement; specified explicit `rg` pattern over surviving paths only; updated gate with conditional managed-lane vs hand-run finalize ownership).
- Verified `5/5` E/V bijection, unchanged `- Scope-Paths:` and `- Item-Dependencies:`, zero bare `file:line` citations, zero em/en dashes, and clean `aw ipd lint --phase review-finalize --agent`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R4 / `E-04` misdiagnoses `tests/test_m0001_sidecar.py` | tests/test_m0001_sidecar.py:312 (`artifact_meta.load_legacy_artifact(spec_path, rec_root)`); tests/test_m0001_sidecar.py:1-406 (zero `SidecarRecord` occurrences); `.aw/system/cutover/metastore-code.cutover.patch` (`m0001_metadata_v2.load_legacy_artifact`) | `Scope`, `E-04`, and `F-03` instructed converting `tests/test_m0001_sidecar.py` off `artifact_meta.SidecarRecord` onto an `m0001` sidecar reader. The file never uses `SidecarRecord`; it already drives `m0001_metadata_v2.run`/`rollback`, and its only broken reference is line 312 calling `artifact_meta.load_legacy_artifact` instead of `m0001_metadata_v2.load_legacy_artifact`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected `Scope`, `E-04`, `F-03`, `F-04`, and `V-04` to repoint `tests/test_m0001_sidecar.py` from `artifact_meta.load_legacy_artifact` to `m0001_metadata_v2.load_legacy_artifact` (`D-1`). Recommendation strength: very strong. |
| PR-002 | BLOCKER | IN-SCOPE | R1 / R4 / `E-02` misclassifies `tests/test_artifact_meta_shapes.py` | tests/test_artifact_meta_shapes.py:51-268 (`artifact_meta.query`, `read`, `history`, `derive_id6`, `LegacyRender`, `SidecarRecord`); `.aw/system/cutover/metastore-code.cutover.patch` (`LOADER_VERSION = "log_v1"`, `m0001_metadata_v2.derive_id6`); spec `4sd62s` C10a, Sections 5.2 and 5.3 | `E-02` instructed repointing `tests/test_artifact_meta_shapes.py` to `m0001_metadata_v2.load_legacy_artifact`. The module never calls `load_legacy_artifact`; all 6 tests exercise phase-B legacy cache scanning and derived-id6 synthesis (removed post-cutover by spec `4sd62s` C10a / 5.2 / 5.3) plus `derive_id6` (moved to `m0001_metadata_v2.derive_id6`) and `LegacyRender`/`SidecarRecord`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-02`, `F-02`, `F-04`, and `V-02` to keep `m0001_metadata_v2.derive_id6` determinism/collision coverage and retire the phase-B legacy cache-scan and `LegacyRender`/`SidecarRecord` tests with spec `4sd62s` C10a / 5.2 / 5.3 cited in `F-02` (`D-2`). Recommendation strength: very strong. |
| PR-003 | HIGH | IN-SCOPE | R3 / R4 / Surviving AC-14a, AC-15, and writer-leak invariants in `test_artifact_meta_legacy_write.py` | tests/test_artifact_meta_legacy_write.py (`test_owned_ac15_1`..`5`, `test_review_kind_ac14a_1`..`2`, `test_refinement_ac14a_3`, `test_owned_message_with_home_path_is_refused_by_the_writer`); tests/test_artifact_meta_write.py (12 tests; none covers AC-14a, AC-15, or writer leak refusals) | Retiring `tests/test_artifact_meta_legacy_write.py` without explicitly auditing AC-14a (`review_kind`), AC-15 (event-owned `readiness`/`coverage`/`approval`/backward-transition), and writer leak refusals against existing log-writer tests risks silently dropping coverage for surviving spec `4sd62s` invariants. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required `E-03` and `V-03` to audit AC-14a, AC-15, and writer-leak invariants against `tests/test_artifact_meta_write.py` and `tests/test_artifact_meta_replay.py`, migrating any uncovered invariant to `tests/test_artifact_meta_write.py` and recording the receiving test in `F-02` (`D-3`). Recommendation strength: very strong. |
| PR-004 | HIGH | IN-SCOPE | R1 / R2 / Absent gitignored census path and `rg` over deleted files | plan `Concern`, `E-04`, `F-04`, `V-04`; verified `.aw/state/lane-submissions/run-20261125T162650Z-1337442/...` is absent in isolated lanes | `Concern` and `F-04` cited a gitignored `.aw/state/lane-submissions/` file absent in isolated lanes, and `E-04`/`V-04` ran `rg` over "the five paths" with an unspecified symbol pattern even after `E-03` deletes two of those files (causing `rg` exit 2). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Marked the attempt-1 census reference as historical provenance (directing execution to start from `89mtbl` F-04), and specified the exact removed-symbol `rg` pattern over only the **surviving** target paths (plus any receiving test module from `E-03`) in `E-04`/`V-04`. Recommendation strength: very strong. |
| PR-005 | MEDIUM | IN-SCOPE | R2 / S7 / Gate finalize ownership, patch paths, clean-tree check, and technical writing | plan `E-01`, `E-05`, `V-01..V-05`, `## Approval and execution gate`; .aw/system/workflows/plan-review/steps/s7-finalize.md; .aw/system/workflows/technical-writing/technical-writing.md | `## Approval and execution gate` unconditionally instructed running `aw ipd finalize` without distinguishing managed runner lanes from hand-run sessions; `E-01` omitted exact patch paths; `V-05` omitted clean-tree confirmation; and `## Deferred / out of scope` omitted `cxxmyv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `## Approval and execution gate` with conditional runner/executor finalize ownership and explicit open-questions status, named exact patch paths in `E-01`/`V-01`, added `git status --short` check to `E-05`/`V-05`, added `cxxmyv` carrier, and synchronized the Mermaid diagram and `path::Symbol` citations. Recommendation strength: very strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter (`Concern`, `Scope`) | Cited gitignored census file, grouped `test_artifact_meta_shapes.py` as `load_legacy_artifact`, and claimed `test_m0001_sidecar.py` uses `SidecarRecord` | Accurately classified all 5 target modules with exact `path::Symbol` references and `4sd62s` clauses | PR-001..PR-005 |
| `E-01..E-05`, `V-01..V-05` | Wrong `test_m0001_sidecar.py` diagnosis, wrong `test_artifact_meta_shapes.py` action, vague E-03 invariant check, unspecified `rg` over deleted files, omitted patch paths | Concrete per-module actions, explicit AC-14a/AC-15/writer-leak audit, exact `rg` pattern over surviving paths only, exact patch paths, and clean-tree check | PR-001..PR-005 |
| `## Findings`, `## Proposed changes`, `## Deferred / out of scope`, `## Approval and execution gate` | Misleading F-03/F-04, unconditional `aw ipd finalize` gate wording | Verified per-module classification in F-04, corrected F-03, synchronized Mermaid flowchart, added `cxxmyv` carrier, and conditional managed-lane vs hand-run finalize ownership | PR-001..PR-005 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `tests/test_m0001_sidecar.py` be fixed on the switched tree? | Repoint line 312 from `artifact_meta.load_legacy_artifact` to `m0001_metadata_v2.load_legacy_artifact` and keep all 4 `m0001_metadata_v2.run`/`rollback` tests intact. | Convert `test_m0001_sidecar.py` off `SidecarRecord` (rejected: the file never imports or references `SidecarRecord`). | `tests/test_m0001_sidecar.py:1-406`, `.aw/system/cutover/metastore-code.cutover.patch`. | yes |
| D-2 | How should `tests/test_artifact_meta_shapes.py` be handled on the switched tree? | Retain `m0001_metadata_v2.derive_id6` determinism/collision coverage and retire the phase-B legacy cache-scanning and `LegacyRender`/`SidecarRecord` tests (`test_a`..`test_d`, `test_f`, phase-B portion of `test_e`), citing spec `4sd62s` C10a and Sections 5.2 and 5.3 in F-02. | Repoint `test_artifact_meta_shapes.py` to `load_legacy_artifact` (rejected: none of its 6 tests calls `load_legacy_artifact`; they test phase-B `artifact_meta.query` on unmigrated legacy shapes, which spec `4sd62s` removes and `tests/test_m0001_any_repo.py` tests for migration). | `tests/test_artifact_meta_shapes.py:1-268`, `.aw/system/cutover/metastore-code.cutover.patch`, spec `4sd62s` C10a, Sections 5.2 and 5.3. | yes |
| D-3 | How should `E-03` prevent coverage loss when retiring `tests/test_artifact_meta_legacy_write.py`? | Explicitly audit AC-14a (`review_kind`), AC-15 (event-owned `readiness`/`coverage`/`approval`/backward-transition), and writer leak refusals against `tests/test_artifact_meta_write.py` and `tests/test_artifact_meta_replay.py`, migrating any uncovered invariant into `tests/test_artifact_meta_write.py` and recording the receiving test in F-02. | Delete `test_artifact_meta_legacy_write.py` wholesale without auditing those specific invariants (rejected: `tests/test_artifact_meta_write.py` currently has only 12 tests and does not cover AC-14a, AC-15, or writer leak refusals). | `tests/test_artifact_meta_legacy_write.py`, `tests/test_artifact_meta_write.py`, spec `4sd62s` AC-14a, AC-15, Section 4.3. | yes |

## Round 2

This re-review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261126T161303Z-1366371`) after `nv3upa` was demoted `reviewed -> to-review` for `[stale-review]`. The target plan `.aw/records/plans/pending/20261125-metastore-307-nv3upa-retire-or-repoint-the-legacy-loader-and-writer-unit-tests-in.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings). The re-review re-verified every reference against the current tree and `.aw/system/cutover/metastore-code.cutover.patch`, including `agent_workflows/artifact_meta.py` (patched `append`, `create`, `replay`, `_require_schema`, `load_legacy_review`, `read_text`, `history_records`, `_newest_history_record`, `_last_history_at`), `agent_workflows/migrations/m0001_metadata_v2.py` (patched `load_legacy_artifact` and `derive_id6`), all five target test modules (`tests/test_artifact_meta_legacy.py`, `tests/test_artifact_meta_shapes.py`, `tests/test_artifact_meta_legacy_write.py`, `tests/test_artifact_meta_legacy_writer.py`, `tests/test_m0001_sidecar.py`), receiving modules (`tests/test_artifact_meta_write.py`, `tests/test_artifact_meta_replay.py`), `tests/test_prompts_new.py`, `tests/test_metastore_cutover_code_patch.py`, spec `4sd62s` (C10a, Sections 4.1-4.3, 4.2b, 5.2, 5.3, AC-14a, AC-15), backlog `ldfefd`, and `Set: metastore` siblings (`63ib9r`, `89mtbl`, `fljn9b`, `cugg3w`, `x1mmdp`). It uncovered one `BLOCKER`, two `MEDIUM`, and one `LOW` findings (`PR-006..PR-009`), all `Overall:Low` remediation risk and all fixed in place. No production code or test code was modified.

### Step T

1. No direct public-interface or spec change (edits test modules only inside `.aw/system/cutover/metastore-code.cutover.patch`), though all downstream children (`fljn9b`, `cugg3w`..`x3mig6`, `x1mmdp`) depend on `executed:nv3upa` and the regenerated cumulative patch.
2. No; it does not touch private-data sanitizers, commit/lock helpers, worktree isolation, merge-to-main gates, or host sandbox profiles.
3. No; bounded to 5 execution items across 3 task groups, focused on one cohesive concern (repointing or retiring the five legacy loader/writer/sidecar unit-test modules inside the inert code patch).
4. Yes; `- Scope-Paths:` declares both tracked files modified by this plan (the plan file itself and `.aw/system/cutover/metastore-code.cutover.patch`).
5. Yes; retiring legacy writer tests without migrating uncovered spec `4sd62s` AC-14a, AC-15, and writer-leak invariants would drop regression coverage, and a broken receiving-module gate (`test_append_dry_run`) or wrong AC-15 precondition would halt execution.

AW-TIER: standard

### Step R1

- Checked: `.aw/system/cutover/metastore-code.cutover.patch` (`agent_workflows/artifact_meta.py` hunks for `append`, `create`, `LOADER_VERSION`, `_require_schema`, and `m0001_metadata_v2.py` hunks for `derive_id6` and `load_legacy_artifact`), `agent_workflows/artifact_meta.py::replay` (lines 1650-1795), `tests/test_artifact_meta_write.py` (all 12 tests), `tests/test_artifact_meta_replay.py` (all 18 tests), `tests/test_artifact_meta_legacy.py`, `tests/test_artifact_meta_shapes.py`, `tests/test_artifact_meta_legacy_write.py`, `tests/test_artifact_meta_legacy_writer.py`, `tests/test_m0001_sidecar.py`, `tests/test_prompts_new.py`, `tests/test_metastore_cutover_code_patch.py`, spec `4sd62s`, backlog `ldfefd`, and `Set: metastore` plans `63ib9r`, `89mtbl`, `fljn9b`, `cugg3w`, and `x1mmdp`.
- Found:
  - In `.aw/system/cutover/metastore-code.cutover.patch`, post-cutover `artifact_meta.append` raises `ValueError` when `not log_path.exists()` and `not _from_create`. Consequently `tests/test_artifact_meta_write.py::test_append_dry_run` fails on the switched tree until `cugg3w` (Order 308, E-02 item 4) runs AFTER `nv3upa` (Order 307) and `fljn9b` (Order 314), contradicting `nv3upa` E-04 and V-03 ("showing all tests PASSED" on `tests/test_artifact_meta_write.py`) (`PR-006`).
  - In `agent_workflows/artifact_meta.py::replay`, the spec `4sd62s` AC-15 case 5 backward-transition `unset readiness` refusal triggers only when `"readiness" in current_fields` (unlike legacy `_check_owned_fields`), so a direct translation of `test_owned_ac15_5_backward_transition_requires_unset_readiness` without a prior gate `op: "review"` event setting `readiness` would fail to raise. Also, retiring `test_prompt_create_and_cli_new_preserve_prompt_kind_and_created_day` and `test_stale_prompt_cache_rebuilt_under_legacy_loader_version` in `tests/test_artifact_meta_legacy_writer.py` rests on spec `4sd62s` Section 4.2b and `LOADER_VERSION = "log_v1"` (`PR-007`).
  - Confirmed `load_legacy_review`, `read_text`, `history_records`, `_newest_history_record`, and `_last_history_at` remain intact in patched `artifact_meta.py` with zero calls to removed symbols, and `m0001_metadata_v2.load_legacy_artifact` and `derive_id6` keep identical signatures in patched `m0001_metadata_v2.py`. All 18 tests in `tests/test_artifact_meta_replay.py` and the other 11 tests in `tests/test_artifact_meta_write.py` match post-cutover `artifact_meta`.

### Step R2

- Checked: E/V bijection (`5/5`: `E-01..E-05` to `V-01..V-05`, `- Highest E allocated: 05`), `- Scope-Paths:` (2 tracked paths), `- Item-Dependencies: executed:89mtbl` (matching `63ib9r` row 307; `fljn9b` Order 314 chains on `executed:nv3upa`), concrete `V-*` evidence and re-derivation convention, `rg` coverage, durable carriers (`cugg3w`, `cxxmyv`), and `## Approval and execution gate`.
- Found:
  - `V-03` demanded every test in `tests/test_artifact_meta_write.py` pass despite `test_append_dry_run` being owned by later child `cugg3w` (`PR-006`).
  - `V-05` hardcoded a collected test count (`with all 3 tests PASSED`), violating the `r2-executability.md` re-derivation convention; `V-04`'s `rg` regex omitted `meta\.derive_id6`; `E-02` item 2 abbreviated `tests/test_artifact_meta_shapes.py` function names (`PR-008`). All fixed in place.

### Step R3

- Checked (full form, `standard` tier):
  - Security regression preservation: `E-03` and `V-03` preserve writer leak refusal (`home` path in `message`) and event-owned attestation refusals (spec `4sd62s` AC-14a `review_kind`, AC-15 `readiness`/`coverage`/`approval`/backward-transition) in `tests/test_artifact_meta_write.py`, and `PR-007` ensures the migrated AC-15 case 5 test actually exercises the `readiness`-present replay branch rather than failing or being weakened.
  - Workspace containment: edits occur strictly inside gitignored `.aw/state/nv3upa/scratch`, removed before commit; no live code, secrets, or outbound calls are touched.

### Step R4

- Checked: correctness, anti-regression, testing/verification, KISS, right-sizing/conceptual density per E-item, and `## Spec / documentation sync`.
- Found:
  - Cross-plan collision between `nv3upa` E-04/V-03 and `cugg3w` E-02 item 4 on `tests/test_artifact_meta_write.py::test_append_dry_run` (`PR-006`).
  - Unstated log-format `replay` precondition for AC-15 case 5 and Section 4.2b retirement basis for legacy prompt writer tests (`PR-007`).
  - Hardcoded collected test count in `V-05`, missing `meta\.derive_id6` in `V-04`, and abbreviated function names in `E-02` (`PR-008`).
  - Missing E-01 stop branch in Mermaid flowchart and missing explicit `test_append_dry_run` deferred entry (`PR-009`).
- Right-sizing check: 5 E-items across 3 task groups, 1 work `Scope-Path` (`.aw/system/cutover/metastore-code.cutover.patch`). Each E-item owns one focused pass. No split needed.

### Step S5

- Checked: `## Open questions` (`None open`). All four findings (`PR-006..PR-009`) have `Overall:Low` remediation risk and are settled by authoritative repository evidence (`.aw/system/cutover/metastore-code.cutover.patch`, `agent_workflows/artifact_meta.py::replay`, `tests/test_artifact_meta_write.py`, `cugg3w`, spec `4sd62s`, `r2-executability.md`, `technical-writing.md`). Two reversible review decisions are recorded in `### Decisions` (`D-1..D-2`). No blocking or human-owned question remains; outcome JSON records `{"questions": []}`.

### Pass 2

- Re-checked the complete revised plan: front matter (`- Status: reviewed`, `- Review-Depth: standard`, `- Readiness: go-pending-approval`), `## Workflow history`, `## Goal`, `E-01..E-05`, `## Project conventions discovered (Step 0)`, `## Findings` (`F-01..F-04`), `## Proposed changes` and updated Mermaid `flowchart TD`, `## Deferred / out of scope` (carriers `cugg3w`, `cxxmyv`), `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync`, `## Open questions`, `V-01..V-05`, and `## Approval and execution gate`.
- Swept for superseded wording across all sections (reconciled `E-03`, `E-04`, `F-04`, `Proposed changes`, `Deferred / out of scope`, `Required tests / validation`, and `V-03` for `-k "not test_append_dry_run"`; removed hardcoded `all 3 tests PASSED` in `V-05`; qualified spec `4sd62s` AC-14a/AC-15; verified exact symbol names in `E-02`).
- Verified `5/5` E/V bijection, unchanged `- Scope-Paths:` and `- Item-Dependencies:`, zero bare `file:line` citations, zero em/en dashes, and clean `aw ipd lint --phase review-finalize --agent`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-006 | BLOCKER | IN-SCOPE | R1 / R2 / R4 / Receiving-module `test_append_dry_run` collision with `cugg3w` | `.aw/system/cutover/metastore-code.cutover.patch` (`agent_workflows/artifact_meta.py::append`, refusing `not log_path.exists()` when `not _from_create`); `tests/test_artifact_meta_write.py::test_append_dry_run`; `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md` (`E-02` item 4) | `nv3upa` (Order 307) executes before `fljn9b` (Order 314) and `cugg3w` (Order 308), yet `E-04` and `V-03` demanded all tests in `tests/test_artifact_meta_write.py` pass without filtering `test_append_dry_run`. On the switched tree, `test_append_dry_run` fails because post-cutover `artifact_meta.append` refuses `op: "create"` without `_from_create=True` on a nonexistent log, and `cugg3w` E-02 item 4 owns updating it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-03`, `E-04`, `F-04`, `## Proposed changes`, `## Deferred / out of scope`, `## Required tests / validation`, and `V-03` to run `tests/test_artifact_meta_write.py` with `-k "not test_append_dry_run"` (passing every other existing test plus all migrated tests) and explicitly leave `test_append_dry_run` untouched for `cugg3w` (`Carrier: cugg3w`) (`D-1`). Recommendation strength: very strong. |
| PR-007 | MEDIUM | IN-SCOPE | R1 / R4 / AC-15 (5) log-format `replay` precondition and Section 4.2b legacy prompt retirement basis | `agent_workflows/artifact_meta.py::replay` (`if backward_to_draft_or_review and "readiness" in current_fields:`); `tests/test_artifact_meta_legacy_write.py::test_owned_ac15_5_backward_transition_requires_unset_readiness`; `tests/test_artifact_meta_legacy_writer.py::test_prompt_create_and_cli_new_preserve_prompt_kind_and_created_day` and `test_stale_prompt_cache_rebuilt_under_legacy_loader_version`; spec `4sd62s` Section 4.2b | Unlike legacy `_check_owned_fields`, log-format `artifact_meta.replay` triggers the AC-15 (5) backward-transition `unset readiness` refusal only when `readiness` is present in `current_fields`; a naive translation of `test_owned_ac15_5` without first setting `readiness` via a gate `op: "review"` event would fail to raise. Additionally, `E-03` omitted spec `4sd62s` Section 4.2b as the basis for retiring `test_artifact_meta_legacy_writer.py`'s legacy `created_day` and `LEGACY_LOADER_VERSION` prompt tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Documented the `readiness`-present `replay` precondition in `E-03` item 2 and `F-04`, and added the spec `4sd62s` Section 4.2b / `LOADER_VERSION = "log_v1"` retirement basis (noting `prompt_kind` coverage in `89mtbl` / `tests/test_prompts_new.py` and stale `schema_hash` coverage in `tests/test_artifact_meta_loader_parity.py`) to `E-03` item 1 and `F-04` (`D-2`). Recommendation strength: very strong. |
| PR-008 | MEDIUM | IN-SCOPE | R2 / Re-derivation convention (`V-05` test count), `V-04` `rg` pattern, and `E-02` symbol precision | plan `V-05` (`with all 3 tests PASSED`), `V-04` (`rg` pattern), `E-02` item 2 (`test_a..test_f`); `.aw/system/workflows/plan-review/steps/r2-executability.md` (re-derivation convention); `tests/test_artifact_meta_shapes.py` | `V-05` hardcoded a collected test count (`all 3 tests PASSED`) as a validation bar contrary to `r2-executability.md`; `V-04`'s removed-symbol `rg` pattern omitted `meta\.derive_id6`; and `E-02` abbreviated the test function names in `tests/test_artifact_meta_shapes.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced `with all 3 tests PASSED` in `V-05` with the pinned guard-test behaviors, added `meta\.derive_id6` to `V-04`'s `rg` pattern, qualified `spec 4sd62s` on `AC-14a`/`AC-15` in `E-03`/`V-03`, and listed exact function names in `E-02` item 2. Recommendation strength: very strong. |
| PR-009 | LOW | IN-SCOPE | Check P / Technical writing requirement 12 (diagram) and downstream chain clarity | plan `## Proposed changes` Mermaid flowchart, `## Deferred / out of scope`, `E-01`; `.aw/system/workflows/technical-writing/technical-writing.md` requirement 12(b)/(d) | The Mermaid `flowchart TD` omitted the `E-01` patch-rejection stop branch, and `## Deferred / out of scope` did not reflect `test_append_dry_run` or Order 314 `fljn9b` ahead of `cugg3w`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the `Patches apply cleanly?` stop branch to the Mermaid diagram matching `E-01`, and updated `## Deferred / out of scope` with the explicit `test_append_dry_run` deferral (`Carrier: cugg3w`) and `fljn9b` chain context. Recommendation strength: strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `E-02` item 2 | Abbreviated `test_a`..`test_d`, `test_f`, `test_e` | Exact function names from `tests/test_artifact_meta_shapes.py` | PR-008 |
| `E-03`, `E-04`, `F-04`, `## Required tests / validation`, `V-03` | Ran all of `tests/test_artifact_meta_write.py` unfiltered; omitted AC-15 (5) `replay` precondition and Section 4.2b prompt-test retirement basis | Added `-k "not test_append_dry_run"` for `tests/test_artifact_meta_write.py` (leaving `test_append_dry_run` to `cugg3w`), documented `replay` `readiness`-present precondition and Section 4.2b basis, qualified `spec 4sd62s` on `AC-14a`/`AC-15` | PR-006, PR-007, PR-008 |
| `V-04`, `V-05` | `V-04` omitted `meta\.derive_id6`; `V-05` hardcoded `with all 3 tests PASSED` | Added `meta\.derive_id6` to `V-04` `rg`; replaced `all 3 tests PASSED` in `V-05` with pinned guard-test behaviors | PR-008 |
| `## Proposed changes`, `## Deferred / out of scope` | Linear Mermaid flowchart; omitted `test_append_dry_run` deferral and `fljn9b` chain note | Added E-01 patch-apply branch to Mermaid diagram; added `test_append_dry_run` deferred entry (`Carrier: cugg3w`) and `fljn9b` note | PR-006, PR-009 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `nv3upa` verify migrated tests in `tests/test_artifact_meta_write.py` while `test_append_dry_run` is still owned by later child `cugg3w`? | Keep `tests/test_artifact_meta_write.py` as the receiving module, run it with `-k "not test_append_dry_run"` in `nv3upa` E-04/V-03, and explicitly defer `test_append_dry_run` to `cugg3w` (`Carrier: cugg3w`). | (a) Update `test_append_dry_run` inside `nv3upa` (rejected: duplicates/trespasses on `cugg3w` E-02 item 4 without being authorized to edit `cugg3w`); (b) create a separate new test file for migrated writer tests (rejected: splits log-writer tests unnecessarily across two modules). | `.aw/system/cutover/metastore-code.cutover.patch` (`artifact_meta.py::append`), `tests/test_artifact_meta_write.py::test_append_dry_run`, `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md` (`E-02` item 4). | yes |
| D-2 | How should `nv3upa` E-03 specify migrating AC-15 (5) and retiring the legacy prompt tests in `tests/test_artifact_meta_legacy_writer.py`? | Require the migrated AC-15 (5) test to set `readiness` via a gate `op: "review"` event before testing backward-transition refusal, and cite spec `4sd62s` Section 4.2b and `LOADER_VERSION = "log_v1"` when retiring the legacy `created_day` and `LEGACY_LOADER_VERSION` prompt tests. | Leave both details implicit for the executor to discover during execution (rejected: naive translation of `test_owned_ac15_5` would fail to raise under `artifact_meta.replay`, triggering a false stop). | `agent_workflows/artifact_meta.py::replay`, `tests/test_artifact_meta_legacy_write.py::test_owned_ac15_5_backward_transition_requires_unset_readiness`, `tests/test_artifact_meta_legacy_writer.py`, spec `4sd62s` Section 4.2b. | yes |
