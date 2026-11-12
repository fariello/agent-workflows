# Review: 3466h8 - Move the releases create and line-setter writers onto artifact_meta

- Subject-Id: 3466h8
- Subject-Type: ipd
- Reviewed-At: 2026-11-12
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading
- Checked `.aw/records/plans/pending/20261109-metastore-134-3466h8-move-the-releases-create-and-line-setter-writers-onto-artifa.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`:
  1. Direct openings and scannable layout: Goal, task group, findings, behavior decisions, proposed changes, and validation sections open directly with concrete facts and obligations.
  2. Defined acronyms and project terms: `IPD`, `id6`, `UTC`, `CLI`, `YAML`, and `PIN-FIRST` contracts are explicit in context.
  3. Concrete wording: replaced vague `artifact_meta.append` delegation on pure `str -> str` helpers with exact `artifact_meta.set_legacy_bullet_line` and `artifact_meta.create` signatures, field keys, and anchor rules.
  4. Active voice and named actors: every `E-*` and `V-*` item names the exact module, symbol, and test module.
  5. Short sentences and one main idea per step: split the plan into five single-concern steps (`E-03`, `E-01`, `E-05`, `E-02`, `E-04`), each within `IPD-Z603` unit guidance (`<=8` named units).
  6. Parallel lists and tables: `Findings`, `Behavior decisions`, `Proposed changes`, and `V-01..V-05` use parallel structure.
  7. Positive instructions and explicit refusal contracts: `D-1`, `D-2`, and `D-3` state both kept outputs and refusal conditions (`ValueError` at library level, exit 2 at CLI).
  8. Consistent terminology: `artifact_meta.create`, `artifact_meta.set_legacy_bullet_line`, `LegacyRender`, and `REGISTRY["release"]` are used consistently throughout.
  9. Exact identifiers and repo-relative paths: verified every symbol and test path against `HEAD` (`9115b2a70`) with zero absolute paths and zero `file://` URIs.
  10. Honest evidence and citations: re-ran all 11 pinned test modules on `HEAD` (`103 + 75 = 178` test cases green) and labeled `def test_` counts in `F-02` as non-binding pointers re-derived at execution by the PIN-FIRST command.
  11. Clean punctuation: removed both em dashes in `## Validation and cross-check` (`IPD-C802`).
  12. Diagrams where ordering matters: added a `mermaid` `flowchart TD` dependency diagram in `## Proposed changes (ordered, validatable)` showing `E-03 -> E-01 -> E-05` and `E-03 -> E-02 -> E-04`.

### Step T: Triage
- Architectural and safety signals triggered:
  - Modifies shared `agent_workflows/artifact_meta.py` registry (`REGISTRY["release"]`) and phase-B field renderer (`_render_field`, `set_legacy_bullet_line`) alongside `agent_workflows/releases.py`.
  - Enforces per-record locking, atomic replacement, and writer-side string-safety refusals (`validate_new_events`, `spec 4sd62s` 4.2 and AC-15).
  - Coordinates directly with `2xwb9b` (`status_set` caller of `set_item_dependencies_line` and `set_graduated_to_line`), `7yr827` (`write_legacy` and `LegacyRender`), `fekdwv` (`short_description` on `releases.run_new`), `g6tw94` (family history audit), `xexn45` (E-13 `63zo2f` closure and E-14 raw-write audit), and `9o83cr` (adapter retirement).
- `AW-TIER: complex`

### Step R1: Evidence & Design Integrity
- Verified `agent_workflows/releases.py` in full (lines 1-1537) and `agent_workflows/artifact_meta.py` (`REGISTRY`, `validate_event`, `validate_new_events`, `_LEGACY_BULLET_LABEL`, `_render_field`, `create`).
- Found two blockers in the unedited plan:
  1. `E-02` instructed moving pure `str -> str` functions (`set_item_dependencies_line`, `set_graduated_to_line`) onto disk-writing `artifact_meta.append`, ignored `artifact_meta._render_field`'s existing reverse delegation to `_releases.set_*_line` (which causes immediate `RecursionError` once `releases.set_*_line` calls back into `artifact_meta`), and omitted the five sibling `releases.set_*_line` helpers (`set_blocks_release_line`, `set_priority_line`, `set_work_kind_line`, `set_from_backlog_line`, `set_from_spec_line`) that hold 5 of the 11 bullet literals cited in `- Concern:` and are tested together in `tests/test_releases_sibling_line_writers_bounding.py` (`PR-001`).
  2. `E-01` omitted `releases.run_new`'s direct `_core.atomic_write(dest, body)` call (leaving a raw write in `releases.py` that fails `xexn45` E-14), missed that `REGISTRY["release"]` in `artifact_meta.py` lacked `version`, `set`, and `order` (causing `validate_event` to raise `ValueError` on `create`), and missed `tests/test_specs_releases_descriptive_safety.py::test_non_regression_releases_library_functions_unchanged`, which asserted IPD `uz05bl`'s pre-`artifact_meta` library-level under-scope (`R.create_release(self.tmp, "2.0.0", "unsafe\n- Blocks-Release: next")` writing a smuggled bullet) that `artifact_meta.validate_new_events` now refuses (`PR-002`).
- Remediated both blockers directly in the plan (`E-03`, `E-01`, `E-05`, `E-02`, `E-04`, `D-1..D-3`).

### Step R2: Structural & Scope Audit
- Widened `- Scope-Paths:` to include `tests/test_specs_releases_descriptive_safety.py` for the `D-3` assertion update alongside `agent_workflows/releases.py` and `agent_workflows/artifact_meta.py` (3 work paths, well within the 8-path guidance).
- Split the checklist into 5 single-concern `E-*` steps (`E-03`, `E-01`, `E-05`, `E-02`, `E-04`) with a 1:1 `V-01..V-05` bijection via `aw ipd sync --apply`; `aw ipd lint --phase author --detail` reports `conforming` with zero advisories (`PR-003`).

### Step R3: Verification & Acceptance Completeness
- Every `V-*` item demands deterministic before/after test outcome diffs under `.aw/state/3466h8/`, named unit `PASSED` lines, per-module `PASSED` counts, and targeted `rg` proofs confirming zero `_releases.set_*_line` back-calls in `artifact_meta.py` (`V-03`), zero hand-built `Workflow history` lines in `releases.py` (`V-01`), zero `atomic_write` or `write_text` calls in `releases.py` (`V-05`), and zero hand-built `- Field:` bullet literals in `releases.py` (`V-04`).

### Step R4: Risk, Edge-Case & Regression Audit
- Verified every edge case pinned by the existing test suite:
  - `plan_release` performs zero filesystem I/O (`dry_run=True` on `artifact_meta.create`) and previews the exact bytes `create_release` and `run_new --apply` write (`test_plan_release_previews_exactly_what_create_writes`).
  - Anchor-less metadata blocks and `---` YAML-fenced research fixtures return `text` unchanged in `set_legacy_bullet_line` (`test_anchor_in_body_does_not_divert_insertion` Part 3, `test_yaml_fenced_fixture_body_bullet_survives`).
  - `set_item_dependencies_line` preserves its three-tier anchor order (after `- Scope-Paths:`, else before `- Status:`, else after `- Id:` per `spec 25kzda` 2.7).
  - Pre-existing duplicate bullets are healed to one line and `"-"` / `None` strip cleanly without residue (`tests/test_releases_line_writers.py`).
  - Library-level `create_release` and `plan_release` refuse embedded newlines and control characters via `artifact_meta.validate_new_events` (`D-3`), while CLI `releases.run_new` preserves its pre-render exit-2 `aw.agent/v1` `cannot-run` envelope (`test_non_regression_releases_new_agent_envelope`, `test_releases_run_new_cli_empty_verb_single_prefix`).

### Step R5: Hostile & Failure-Mode Audit
- Checked bullet-smuggling (`"unsafe\n- Blocks-Release: next"`), infinite recursion (`_render_field` <-> `releases.set_*_line`), body-section anchor spoofing (`- Status:` inside markdown body prose or fenced code blocks), and partial writes on refusal (`dry_run` and pre-write `validate_new_events`). All four failure modes are closed by `E-03`, `E-01`, `E-05`, `E-02`, and `E-04`.

### Step R6: Simplicity & Minimalism Audit
- Reusing one bounded helper `artifact_meta.set_legacy_bullet_line` for both `artifact_meta._render_field` and the seven thin `releases.set_*_line` adapters avoids duplicating `selectors.metadata_region` slicing across two modules and lets `9o83cr` delete the thin adapters in one clean step after direct callers retire.

### Step R7: Sequencing & Dependency Audit
- Verified `- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827`: `tve77h` and `2xwb9b` are in `.aw/records/plans/executed/`; `7yr827` is `reviewed` in `.aw/records/plans/pending/`. Internal step order `E-03 -> E-01 -> E-05` and `E-03 -> E-02 -> E-04` ensures `REGISTRY["release"]` and `set_legacy_bullet_line` land before `releases.py` switches over. Added explicit missing-prerequisite and concurrent-edit stop conditions to `## Approval and execution gate` (`PR-004`).

### Step S5: Remediation Risk
- Overall remediation risk: **Low**. Every finding (`PR-001`..`PR-004`) is a concrete engineering alignment with `spec 4sd62s`, `7yr827`, `g6tw94`, and `xexn45`, verified directly against live repository code and 178 passing baseline tests, with zero product or public-CLI scope changes requiring human arbitration.

### Pass 2: Verification & Drift Audit
- Re-read `.aw/records/plans/pending/20261109-metastore-134-3466h8-move-the-releases-create-and-line-setter-writers-onto-artifa.ipd.md` top-to-bottom after edits.
- Verified `aw ipd lint --phase author --detail`: `conforming` (0 errors, 0 warnings, 0 advisories).
- Verified zero unresolved `TODO` placeholders, zero em/en dashes, zero absolute paths, and zero `file://` URIs.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Category | Location | Finding | Action / Disposition | Status | Remediation Risk |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R2 | `E-02`, `E-03`, `E-04`, `D-2` | `E-02` routed pure `str -> str` helpers (`set_item_dependencies_line`, `set_graduated_to_line`) to disk-writing `artifact_meta.append`, missed `artifact_meta._render_field`'s reverse delegation to `_releases.set_*_line` (causing `RecursionError`), and omitted the 5 sibling `releases.set_*_line` writers holding 5 of the 11 bullet literals in `releases.py` | Added `E-03` (`artifact_meta.set_legacy_bullet_line` + `_render_field` rewiring) and `E-04` (5 sibling adapters), and updated `E-02` and `D-2` to preserve bounded `metadata_region` anchors, YAML/no-anchor no-ops, duplicate healing, and dash/None clearing | FIXED | Low |
| PR-002 | BLOCKER | IN-SCOPE | R1 / R2 | `E-03`, `E-01`, `E-05`, `D-1`, `D-3`, `Scope-Paths` | `E-01` omitted `releases.run_new`'s raw `_core.atomic_write` (`xexn45` E-14), missed `version`/`set`/`order` in `REGISTRY["release"]` (`ValueError` on `create`), and left `test_non_regression_releases_library_functions_unchanged` (`uz05bl` pre-`artifact_meta` library-level injection test) unnamed under the PIN-FIRST rule | Registered `version`, `set`, and `order` in `E-03`, moved `plan_release`/`create_release` (`E-01`) and `run_new` (`E-05`) onto `artifact_meta.create` with `## Summary` body prose (`D-1`), and named the `D-3` assertion update with `tests/test_specs_releases_descriptive_safety.py` in `Scope-Paths` | FIXED | Low |
| PR-003 | MEDIUM | IN-SCOPE | R2 / R3 | `E-01..E-05`, `V-01..V-05`, `F-02` | Combining `artifact_meta.py`, library create, CLI `run_new`, and 7 line writers exceeded `IPD-Z603` per-item unit guidance and lacked `rg` verification for remaining raw writes and hand-built bullet literals | Split into 5 focused steps (`E-03`, `E-01`, `E-05`, `E-02`, `E-04`) via `aw ipd sync --apply` (`<=8` units each, 0 advisories) and added explicit `rg` checks in `V-01`, `V-03`, `V-04`, and `V-05` | FIXED | Low |
| PR-004 | LOW | IN-SCOPE | Proofreading / S7 | `Validation and cross-check`, `Proposed changes`, `Approval and execution gate` | Line 99 contained two em dashes (`IPD-C802`), `Proposed changes` lacked a Requirement 12 dependency diagram, `F-02` lacked non-binding test-count framing, and `Approval and execution gate` lacked missing-prerequisite and concurrent-edit stop conditions | Replaced em dashes, added a Mermaid `flowchart TD` diagram, framed `F-02` counts as non-binding pointers, and added explicit stop conditions in `Approval and execution gate` | FIXED | Low |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where should `summary` live in phase-B release creation so `releases.py` builds zero `- Field:` bullets? | Move `summary` to `## Summary` body prose while passing `version` and `status` as `create` fields and `summary` as the `created` event message | Keep `- Summary:` as a special-case non-registry legacy bullet | `spec 4sd62s` 4.2c ("the prose itself moves to the body"), `parse_release` and `validate_release` (`tests/test_releases.py`), and `fekdwv` adding `short_description` separately | yes |
| D-2 | Which `artifact_meta` entry point should back the seven pure `str -> str` `releases.set_*_line` helpers without recursion? | Add `artifact_meta.set_legacy_bullet_line` over `selectors.metadata_region` and route both `_render_field` and all seven `releases.set_*_line` adapters through it | Route through file-based `artifact_meta.append` or leave `_render_field` calling `_releases.set_*_line` | `artifact_meta.append` requires disk paths and `id6`, while `_render_field` calling `_releases.set_*_line` causes `RecursionError`; `9o83cr` retires the thin adapters later | yes |
| D-3 | How should `3466h8` resolve `test_non_regression_releases_library_functions_unchanged` under the PIN-FIRST rule? | Declare `D-3` and `tests/test_specs_releases_descriptive_safety.py` in `- Scope-Paths:` and assert `ValueError` with zero written `.release.md` files on embedded newlines | Pass `migration_import=True` to bypass writer-side string safety | `spec 4sd62s` 4.2 and AC-15 mandate writer-side refusal on every non-migration `artifact_meta` write, closing IPD `uz05bl`'s former library-level under-scope | yes |
| D-4 | How should the checklist be structured so every item stays within `IPD-Z603` unit guidance? | Split into five single-concern steps (`E-03`, `E-01`, `E-05`, `E-02`, `E-04`) | Keep all moves in two multi-file steps | Keeps the plan at 5 steps (`<=5`) and `<=8` named units per step (`aw ipd lint --phase author --detail` conforming with zero advisories) | yes |
