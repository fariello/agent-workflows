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
