# Review: b3l7y6 - Move the specs create, note, and migrate writers onto artifact_meta

- Subject-Id: b3l7y6
- Subject-Type: ipd
- Reviewed-At: 2026-11-13
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

#### Changes
- Replaced both em dashes (`U+2014`) in `## Validation and cross-check` with commas (`IPD-C802`), added serial commas in the title and prose, and removed semicolon clause-chaining (`IPD-Z602`).
- Upgraded bare symbol mentions to canonical `path::Symbol` citations (`agent_workflows/specs.py::run_new`, `_render_new_spec`, `run_note`, `run_migrate`, `_sidecar_append`, and `agent_workflows/artifact_meta.py::REGISTRY`), with zero absolute paths and zero `file://` URIs.
- Added a Requirement 12(b) `mermaid` `flowchart TD` dependency diagram in `## Proposed changes (ordered, validatable)` showing `E-03 -> E-01 -> E-05 -> E-02 -> E-04` and `E-03 -> E-02`.

#### Issues
- None remaining after revision; checked against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

### Step T

1. Scope-Path count and nature: 5 paths (`agent_workflows/specs.py`, `agent_workflows/artifact_meta.py`, `tests/test_specs_date_containment.py`, `tests/test_specs_releases_descriptive_safety.py`, and the plan file) modifying shared `artifact_meta` schema/rendering and all active `specs` metadata writers.
2. Step count and coupling: 5 single-concern `E-*` steps (`E-03`, `E-01`, `E-05`, `E-02`, `E-04`) coupling `specs` create, note, and migrate surfaces to `artifact_meta` phase-B legacy rendering (`7yr827`).
3. Safety, gate, and integrity surface: `Blocks-Release: next` and `From-Spec: 4sd62s`; touches writer-side string-safety refusals (`validate_new_events`), destination-containment across `.aw/records`, companion, and `.agents/docs/specs` layouts, sidecar-after-durable-write ordering (`spec 4sd62s` C6), and byte-identical pre-write validation on `specs migrate`.
4. Dependencies and sibling coordination: depends on `executed:tve77h`, `executed:2xwb9b`, and `executed:7yr827`; audited downstream by `g6tw94` (`E-03`) and `xexn45` (`E-14`), and consumed by `fekdwv` (`E-02` `short_description` and body summary).
5. Tier classification: full `complex` review across `R1` through `R7`.

AW-TIER: complex

### Step R1

- Checked: `agent_workflows/specs.py` (lines 1-1350), `agent_workflows/artifact_meta.py` (`OP_PAYLOAD_SCHEMAS`, `REGISTRY["spec"]`, `validate_event`, `validate_new_events`, `_LEGACY_BULLET_LABEL`, `_LEGACY_REMOVE_RE`, `legacy_context`, `_check_owned_fields`, `_render_status`, `_render_field`, `_render_gate`, `_render_history`, `render_legacy`, `_prepare_legacy_events`, `append_legacy`, `append`, `create`), `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (3b, 4.2, 4.2b, 4.2c, 7), sibling plans `7yr827`, `g6tw94`, `jlwedt`, `3466h8`, `fekdwv`, and `xexn45`, and 9 test modules (`98` passing tests across the 8 original modules plus `tests/test_generators_writing_standard_pointer.py`).
- Found two blockers in the original plan:
  1. `agent_workflows/artifact_meta.py::REGISTRY["spec"]` omitted `author`, `canonical` (`spec 4sd62s` 4.2c), and migration-only `implemented` (`unset` of `- Implemented:`), and `_render_status` matched only single-token `^-\s*Status:\s*(\S+)\s*$` on `specs` (`plural == "plans"` gated the annotated fallback), causing `specs.run_migrate` (`tests/test_specs_verbs.py::test_migrate_free_form_to_bare_enum`, `test_migrate_to_deferred_with_gate`, `test_migrate_folds_implemented_line`) to fail with `ValueError: unknown field 'canonical'`, duplicate `- Status:` drift (`spec.metadata-bullet-repeated`), or un-removed `- Implemented:` lines (`PR-001`).
  2. `E-01` collided with two pinned pre-`artifact_meta` injection tests calling `specs._render_new_spec` directly with embedded `\n` (`tests/test_specs_releases_descriptive_safety.py::test_pre_fix_title_injection_forges_approval_and_checker_blind`, `test_pre_fix_summary_injection_smuggles_gate_and_checker_blind`), one exact-byte test asserting `- Date:`, `- Scope:`, and `## Workflow history\n\n` (`tests/test_specs_date_containment.py::test_non_regression_conforming_bytes`), and `test_conforming_new_in_legacy_layout` where `project_records_dir` returns `<repo>/.aw/records` while `resolve_type_dir("specs")` resolves `<repo>/.agents/docs/specs` (`PR-002`).

### Step R2

- Checked: `E-*`/`V-*` bijection (`E-01..E-05` <-> `V-01..V-05`), `- Scope-Paths:` completeness, PIN-FIRST determinism, `steps/r2-executability.md` non-binding test-count rules, and `aw ipd lint --phase author --detail`.
- Widened `- Scope-Paths:` to include `tests/test_specs_releases_descriptive_safety.py` (`D-3`) and `tests/test_specs_date_containment.py` (`D-4`), moved `tests/test_history_write_order.py` to `E-02` (`specs.run_note`, which writes the sidecar; `specs.run_new` writes none), pinned `tests/test_generators_writing_standard_pointer.py` on `E-01`, and framed `F-02` test counts and named test pointers as non-binding pointers re-derived at execution (`PR-002`, `PR-004`).

### Step R3

- Checked: writer-side string safety (`validate_new_events`), path-traversal and destination containment (`record_placement.resolve_type_dir("specs")` and `_check_path_safety`), `run_note` `--date` non-traversal (`date="../../../ESCAPED"` in `test_non_regression_run_set_and_run_note_date_behavior`), sidecar write-after-commit order (`chmod 0o500` failure injection in `test_specs_note_failed_write_leaves_no_sidecar_and_artifact_unchanged`), and leak-sanitizer rules.
- Verified `E-01` closes IPD `uz05bl`'s library-level newline injection hole in `_render_new_spec` via `validate_new_events` (`D-3`), `E-05` keeps `run_new`'s pre-mint exit-2 descriptive/date refusals and destination containment across `.aw/records`, companion, and `.agents/docs/specs` roots (`specs_dir.parent`), and `E-04` previews via `dry_run=True` and validates via `validate_spec` before writing so non-conforming migrations leave the target file byte-identical (`PR-002`, `PR-003`).

### Step R4

- Checked: atomic write replacement (`xexn45` E-14 raw-write audit), dead private helper cleanup, `PRODUCER_INVENTORY` anchor usage in `agent_workflows/record_producers.py`, and `MAX_PROSE_DESCRIPTIVE_LEN` (`4300` chars) boundary behavior on `specs new --summary` and `specs note --message`.
- Verified `agent_workflows/record_producers.py::PRODUCER_INVENTORY` (`anchor="_set_status"`) is declarative metadata with zero runtime `getattr`/AST resolution (`tests/test_record_producers.py`), so removing all six unreferenced private writer helpers (`_sidecar_append`, `_append_history`, `_set_status`, `_gate_field_indices`, `_remove_gate_fields`, `_add_gate_fields`) in `E-02` and `E-04` leaves zero raw `atomic_write` calls and zero hand-built metadata/history literals in `agent_workflows/specs.py` (`PR-003`).

### Step R5

- Checked: hostile inputs and boundary cases from maintainer, executor, and downstream-auditor (`g6tw94`, `xexn45`, `fekdwv`) perspectives: 400-char and 4300-char `--summary` values (`## Scope` body prose + `prose=True` `message`), standalone temp files outside any repo in `NoteTests` and `MigrateTests` (`LegacyTarget` path fallback), duplicate `note` and `migrated` deduplication (`same_status_message_is_duplicate`), and shared-checkout conflicts.
- Added explicit stop-and-report conditions in `## Approval and execution gate` for missing `7yr827` symbols, failing baseline tests on unmodified `HEAD`, or concurrent-edit conflicts (`PR-005`).

### Step R6

- Checked: step granularity against `IPD-Z602` and `IPD-Z603` (`<=5` E-items, `<=8` named units per step, `<=8` work `Scope-Paths`).
- Split the plan into 5 single-concern steps (`E-03` `artifact_meta.py` spec support, `E-01` `_render_new_spec`, `E-05` `run_new`, `E-02` `run_note` + `_sidecar_append` removal, `E-04` `run_migrate` + dead writer helper removal) with 4 work `Scope-Paths`; `aw ipd lint --phase author --detail` reports `conforming` with 0 advisories (`PR-003`, `PR-006`).

### Step R7

- Checked: `- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827` (`tve77h` and `2xwb9b` executed; `7yr827` reviewed in `pending/`) and downstream alignment with `g6tw94` (`E-03` family history audit), `fekdwv` (`E-02` `short_description` + body summary on `specs.run_new`), `3466h8` (parallel 5-step structure and `D-3` test-file pattern), and `xexn45` (`E-14` raw-write audit).
- Confirmed zero circular dependencies and complete alignment across the `metastore` Set.

### Step S5

- All six findings (`PR-001`..`PR-006`) are `IN-SCOPE`, concrete engineering alignments with `spec 4sd62s`, `7yr827`, `g6tw94`, `fekdwv`, and `xexn45` with `Low` remediation risk. Zero material questions require human decision (`questions: []`).

### Pass 2

- Re-read `.aw/records/plans/pending/20261109-metastore-120-b3l7y6-move-the-specs-create-note-and-migrate-writers-onto-artifact.ipd.md` top-to-bottom after applying revisions and running `aw ipd sync --apply`.
- Verified `aw ipd lint --phase author --detail` and `--agent`: `outcome: clean`, `findings: 0` (`conforming`, 0 errors, 0 warnings, 0 advisories).
- Verified zero `TODO` placeholders, zero em/en dashes, zero absolute paths, zero `file://` URIs, and zero leak-sanitizer hits.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R2 | `agent_workflows/artifact_meta.py::REGISTRY["spec"]`, `_LEGACY_BULLET_LABEL`, `_LEGACY_REMOVE_RE`, `_render_status`; `tests/test_specs_verbs.py::test_migrate_free_form_to_bare_enum`, `test_migrate_folds_implemented_line` | `REGISTRY["spec"]` lacked `author`, `canonical` (`spec 4sd62s` 4.2c), and migration-only `implemented` (`unset` of `- Implemented:`), and `_render_status` matched only single-token `- Status:` on `specs`, causing `run_migrate` to fail validation or emit duplicate `- Status:` bullets | Low | FIXED | Added `E-03`/`V-03` registering `author`, `canonical`, and migration-only `implemented` on `REGISTRY["spec"]`, adding their bullet/unset mappings, and replacing in-front free-form `- Status:` (or dropping bare `Status:`) in `_render_status` for `specs` |
| PR-002 | BLOCKER | IN-SCOPE | R1 / R2 | `agent_workflows/specs.py::run_new`, `_render_new_spec`; `tests/test_specs_releases_descriptive_safety.py`; `tests/test_specs_date_containment.py`; `tests/test_history_write_order.py` | Moving `_render_new_spec` and `run_new` onto `artifact_meta` collided with two unnamed `_render_new_spec` newline-injection tests and `test_non_regression_conforming_bytes`, broke `.agents/docs/specs` containment when `project_records_dir` returns `.aw/records`, and mis-assigned `test_history_write_order.py` (`specs note`) to `E-01` | Low | FIXED | Added `D-3` and `D-4`, declared both test files in `- Scope-Paths:`, rooted `run_new`'s `LegacyContext` at `specs_dir.parent` (`E-05`), pinned `test_generators_writing_standard_pointer.py` on `E-01`, and moved `test_history_write_order.py` to `E-02` |
| PR-003 | HIGH | IN-SCOPE | R2 / R4 / R6 | `agent_workflows/specs.py::run_note`, `run_migrate`, `_sidecar_append`, `_append_history`, `_set_status`, `_add_gate_fields`; `xexn45` E-14 | `E-02` bundled `run_note` and `run_migrate`, omitted `run_migrate`'s `dry_run=True` -> `validate_spec` byte-identical refusal before write, and left 6 unreferenced private writer helpers holding dead `Workflow history` and `- Field:` literals in `specs.py` | Low | FIXED | Split into 5 single-concern steps (`E-03`, `E-01`, `E-05`, `E-02`, `E-04`), specified `dry_run=True` -> `validate_spec` -> `dry_run=False` in `E-04`, and removed `_sidecar_append` (`E-02`) plus `_append_history`, `_set_status`, `_gate_field_indices`, `_remove_gate_fields`, and `_add_gate_fields` (`E-04`) |
| PR-004 | LOW | IN-SCOPE | R2 | `F-02`, `E-01..E-05`, `V-01..V-05` | Static `def test_` counts in `F-02` and named test pointers lacked explicit non-binding framing re-derived dynamically at execution (`steps/r2-executability.md`) | Low | FIXED | Framed `F-02` counts and named test units in `D-1`, `V-01`, `V-02`, `V-04`, and `V-05` as non-binding pointers re-derived at execution by the PIN-FIRST command |
| PR-005 | LOW | IN-SCOPE | R3 / R5 | `## Approval and execution gate` | Execution gate lacked explicit stop-and-report conditions if `7yr827` symbols are absent on `HEAD`, if baseline pinned modules fail before editing, or if shared-checkout edits conflict | Low | FIXED | Added narrow stop-and-report conditions in `## Approval and execution gate` |
| PR-006 | LOW | IN-SCOPE | Proofreading | `E-01`, `## Proposed changes`, `## Validation and cross-check` | Plan had two `IPD-C802` em dashes, `IPD-Z602` semicolon clause-chaining in `E-01`, bare `module.func` citations, and no Requirement 12(b) diagram | Low | FIXED | Removed em dashes and semicolon chains, upgraded citations to `path::Symbol`, and added a `mermaid` `flowchart TD` diagram (`0` lint advisories) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| DEC-001 | How should `b3l7y6` align new-spec layout and library-level `_render_new_spec` string safety with `spec 4sd62s`, `fekdwv` E-02, and `g6tw94` E-03 under the PIN-FIRST rule? | Add `D-3` and `D-4` plus `tests/test_specs_releases_descriptive_safety.py` and `tests/test_specs_date_containment.py` in `- Scope-Paths:`, moving `Scope` prose to `## Scope` body (`author` on `REGISTRY["spec"]`, omitting day-only `Date`) and asserting `ValueError` on `_render_new_spec` newline injection while keeping raw-string `validate_spec` checks | Keep `- Date:` and `- Scope:` as non-registry bullets or bypass `validate_new_events` in `_render_new_spec` | `spec 4sd62s` 4.2, 4.2b, 4.2c, AC-15, and AC-32(5), `fekdwv` E-02 ("writes the body summary"), `g6tw94` E-03 (zero history literals in `_render_new_spec`), and sibling `3466h8` `D-1`/`D-3` | yes |
| DEC-002 | Should `b3l7y6` add a dedicated `E-03` step in `agent_workflows/artifact_meta.py` for `spec` fields (`author`, `canonical`, migration-only `implemented` unset) and in-place free-form `- Status:` replacement on `specs`? | Yes: add `E-03` (`V-03`) on `agent_workflows/artifact_meta.py` (already declared in `- Scope-Paths:`) | Leave `artifact_meta.py` untouched and keep custom status/bullet string surgery inside `specs.run_migrate` | Keeping `- Status:` / `- Canonical:` surgery in `specs.py` violates `b3l7y6` Goal and `4sd62s` AC-1; `4sd62s` 4.2c explicitly lists `canonical` as a registry field | yes |
| DEC-003 | How should the checklist be decomposed so every step stays single-concern and within `IPD-Z603` unit limits while removing dead writer helpers in `specs.py`? | Split into 5 steps (`E-03` `artifact_meta.py`, `E-01` `_render_new_spec`, `E-05` `run_new`, `E-02` `run_note` + `_sidecar_append` removal, `E-04` `run_migrate` + dead writer helper removal) | Keep 2 bundled multi-concern steps or leave dead `_append_history`/`_set_status`/`_add_gate_fields` helpers in `specs.py` | Eliminates `IPD-Z602` and `IPD-Z603` advisories (`<=6` units per step) and removes dead writer `Workflow history` and `- Field:` literals from `specs.py` | yes |
