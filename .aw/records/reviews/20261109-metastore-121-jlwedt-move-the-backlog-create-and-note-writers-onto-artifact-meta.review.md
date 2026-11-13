# Review: jlwedt - Move the backlog create and note writers onto artifact_meta

- Subject-Id: jlwedt
- Subject-Type: ipd
- Reviewed-At: 2026-11-13
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

#### Changes
- Replaced both em dashes (`U+2014`) in `## Validation and cross-check` with commas (`IPD-C802`), added serial commas in prose, and removed copy-pasted `specs._append_history` text from `D-1` that referred to `tests/test_specs_verbs.py` in a backlog-only plan.
- Upgraded bare symbol mentions to canonical `path::Symbol` citations (`agent_workflows/backlog.py::run_new`, `_render_item`, `run_note`, `_reattach_history`, `validate_item`, `_WORKFLOW_HISTORY_HEADING_RE`, `agent_workflows/artifact_meta.py::REGISTRY["backlog"]`, `is_valid_transition`, and `agent_workflows/set_records.py::close_on_answer`), qualified `spec 4sd62s` section references, and verified zero absolute paths and zero file-scheme URIs.
- Added a Requirement 12(b) `mermaid` `flowchart TD` dependency diagram in `## Proposed changes (ordered, validatable)` showing `E-03 -> E-04 -> E-01 -> E-02 -> E-05`, `E-03 -> E-02`, and `E-04 -> E-05`.

#### Issues
- None remaining after revision; checked against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

### Step T

1. Scope-Path count and nature: 3 paths (`agent_workflows/backlog.py`, `agent_workflows/artifact_meta.py`, and the plan file) modifying shared `artifact_meta` backlog schema/rendering and all active `backlog` create, note, and history-reattach writers.
2. Step count and coupling: 5 single-concern `E-*` steps (`E-03`, `E-04`, `E-01`, `E-02`, `E-05`) coupling `backlog` create, note, and in-memory history-reattach helpers to `artifact_meta` phase-B legacy rendering (`7yr827`) and downstream `set_records` callers (`x2dxvf`).
3. Safety, gate, and integrity surface: `Blocks-Release: next` and `From-Spec: 4sd62s`; touches writer-side string-safety refusals (`validate_new_events`), destination containment across `.aw/records/backlog`, companion, and `.agents/backlog` layouts, sidecar-after-durable-write ordering (`spec 4sd62s` C6) on both `run_new` (`--apply`) and `run_note`, and bounded history preservation (`attention_contract.history_block`).
4. Dependencies and sibling coordination: depends on `executed:tve77h`, `executed:2xwb9b`, and `executed:7yr827`; audited downstream by `g6tw94` (`E-03` zero writer-internal `Workflow history` or `f"- {(date|today|hdate)} "` hits) and `xexn45` (`E-14` raw-write audit), and consumed by `x2dxvf` (`promote_question_to_backlog` and `close_on_answer`) and `fekdwv` (`E-01` `short_description` at creation).
5. Tier classification: full `complex` review across `R1` through `R7`.

AW-TIER: complex

### Step R1

- Checked: `agent_workflows/backlog.py` (all 1885 lines), `agent_workflows/artifact_meta.py` (`REGISTRY["backlog"]`, `is_valid_transition`, `validate_event`, `validate_new_events`, `_LEGACY_BULLET_LABEL`, `legacy_context`, `_render_status`, `_render_field`, `_render_gate`, `_render_history`, `render_legacy`, `_prepare_legacy_events`, `append_legacy`, `append`, `create`), `agent_workflows/set_records.py` (`promote_question_to_backlog`, `close_on_answer`), `agent_workflows/attention_contract.py` (`history_block`), `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (4.2, 4.2b, 4.2c, 4.3, 7), sibling plans `7yr827`, `g6tw94`, `b3l7y6`, `fekdwv`, `x2dxvf`, and `xexn45`, and 13 test modules (`182` passing baseline tests across `102 + 80` collected items).
- Found three blockers/high defects in the original plan:
  1. `agent_workflows/artifact_meta.py` could not remain unmodified (`Scope check` claimed `"acknowledge it at finalize when unmodified"`): `REGISTRY["backlog"]` omitted `set` (`spec 4sd62s` 4.2c, required by `backlog.validate_item` `backlog.set-missing`) and phase-B `summary` (`backlog.summary-missing` prior to `fekdwv` E-01), `is_valid_transition("backlog", None, to_status)` rejected non-`open` initial statuses such as `blocked` (`tests/test_backlog_descriptive_safety.py::BacklogDescriptiveSafetyTests::test_legitimate_multiword_message_and_gate_ref_succeed` and `set_records.promote_question_to_backlog`), and headerless backlog `op == "create"` lacked `- Id:` seeding and `writing_standard_pointer("backlog item")`-before-history / `body`-after-history placement (`tests/test_generators_writing_standard_pointer.py::test_backlog_new_writing_standard_pointer`) (`PR-001`).
  2. `E-02` routed `agent_workflows/backlog.py::_reattach_history` onto file-mutating `artifact_meta.append`, even though `_reattach_history(old_text, rendered, new_status, message, label="set", write_record=True) -> str` is a pure in-memory `str -> str` helper with no file path or `id6` (called before pre-write `evaluate_blocking_close` in `set_records.close_on_answer` and directly in `tests/test_history_label_parity.py::HistoryLabelParityTests::test_e_reattach_history_default_label_is_legacy_set`); `_render_item` (`source_text` optional) is likewise called directly as a pure `str -> str` helper and must delegate to `artifact_meta.render_legacy_text` (`PR-002`).
  3. `g6tw94` `E-03` requires zero hits of `rg -n "Workflow history" agent_workflows/backlog.py` inside `run_new`, `_render_item`, `run_note`, and `_reattach_history`, whereas `_render_item` and `_reattach_history` split on literal `"\n## Workflow history"` and carried `"Workflow history"` in comments/docstrings rather than using `agent_workflows/backlog.py::_WORKFLOW_HISTORY_HEADING_RE` and `attention_contract.history_block` (`PR-003`).

### Step R2

- Checked: `E-*`/`V-*` bijection (`E-01..E-05` <-> `V-01..V-05`), `- Scope-Paths:` completeness, PIN-FIRST determinism, `steps/r2-executability.md` non-binding test-count rules, and `aw ipd lint --phase author --detail`.
- Moved `tests/test_history_write_order.py` from `E-01` (`backlog new`, which it does not test) to `E-02` (`backlog note`, where `test_backlog_note_failed_write_leaves_no_sidecar_and_artifact_unchanged` lives), added `tests/test_generators_writing_standard_pointer.py` on `E-04` (`_render_item`) and `tests/test_history_label_parity.py` on `E-05` (`_reattach_history`), rooted `LegacyContext` at `_resolve_backlog_root(repo_root).parent` so `.agents/backlog` fixtures stay within containment, and framed `F-02` test counts and `V-*` test pointers as non-binding pointers re-derived dynamically at execution (`PR-003`, `PR-004`).

### Step R3

- Checked: writer-side string safety (`validate_new_events`), path-traversal and destination containment across `.aw/records/backlog`, companion, and `.agents/backlog` roots (`_resolve_backlog_root`), sidecar write-after-commit order (`spec 4sd62s` C6) on both `run_new` (`SidecarRecord` only on `--apply`, never on dry-run preview) and `run_note` (`chmod 0o500` failure injection in `test_backlog_note_failed_write_leaves_no_sidecar_and_artifact_unchanged`), and leak-sanitizer rules.
- Verified `run_new` preserves pre-mint exit-2 refusals (including `--agent` JSONL `cannot-run` envelopes in `test_agent_mode_refusal_shape` and 1200-char `--message` vs 300-char `--summary` asymmetry in `test_message_summary_length_asymmetry`) before minting or writing (`PR-001`, `PR-003`).

### Step R4

- Checked: atomic write replacement (`xexn45` E-14 raw-write audit), `set_release_exempt_kind_line` / `set_release_exempt_ref_line` / `set_close_evidence_line` retention (called as pure value delegates by `agent_workflows/artifact_meta.py::_render_field` per `2xwb9b`), wrapped continuation preservation in `_reattach_history` (`_prior_history_records(old_text)` via `op: "legacy", source: "history"`), and `write_record=False` duplicate suppression.
- Documented explicitly in `Scope` and `Step 0` that `set_release_exempt_*_line` and `set_close_evidence_line` remain intact for `artifact_meta._render_field`, while `rg -n "atomic_write\(|write_text\(" agent_workflows/backlog.py` and `rg -n "f\"- \{(date|today|hdate)\} " agent_workflows/backlog.py` both drop to zero (`PR-002`, `PR-003`).

### Step R5

- Checked: hostile inputs and boundary cases from maintainer, executor, and downstream-caller (`g6tw94`, `x2dxvf`, `fekdwv`, `xexn45`) perspectives: headerless backlog items carrying free-prose `body` with no `## ` heading (`"Prose body\n"` in `test_render_item_preserves_release_exempt_with_source_text`), prose-quoted indented history lines in item bodies (`tk1gqo` shape in `test_e2_writer_round_trip_wrapped_and_quoted`), dual `- Kind:` / `- Work-Kind:` deduplication, stale `- Gate-Summary:` removal on `blocked -> done`, and shared-checkout conflicts.
- Added explicit stop-and-report conditions in `## Approval and execution gate` for missing `7yr827` symbols, failing baseline tests on unmodified `HEAD`, or concurrent-edit conflicts (`PR-005`).

### Step R6

- Checked: step granularity against `IPD-Z602` and `IPD-Z603` (`<=5` E-items, `<=8` named units per step, `<=8` work `Scope-Paths`).
- Split the plan into 5 single-concern steps (`E-03` `artifact_meta.py` backlog support, `E-04` `_render_item`, `E-01` `run_new`, `E-02` `run_note`, `E-05` `_reattach_history` + module audit) with `<=5` named units per step and 2 work `Scope-Paths`; `aw ipd lint --phase author --detail` reports `conforming` with 0 advisories (`PR-002`, `PR-006`).

### Step R7

- Checked: `- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827` (`tve77h` and `2xwb9b` executed; `7yr827` reviewed in `pending/`) and downstream alignment with `b3l7y6` (parallel 5-step structure), `g6tw94` (`E-03` family history audit), `x2dxvf` (`promote_question_to_backlog` and `close_on_answer` callers of `_render_item` and `_reattach_history`), `fekdwv` (`E-01` `short_description` at creation), and `xexn45` (`E-14` raw-write audit).
- Confirmed zero circular dependencies and complete alignment across the `metastore` Set.

### Step S5

- All six findings (`PR-001`..`PR-006`) are `IN-SCOPE`, concrete engineering alignments with `spec 4sd62s`, `7yr827`, `g6tw94`, `x2dxvf`, `fekdwv`, and `xexn45` with `Low` remediation risk. Zero material questions require human decision (`questions: []`).

### Pass 2

- Re-read `.aw/records/plans/pending/20261109-metastore-121-jlwedt-move-the-backlog-create-and-note-writers-onto-artifact-meta.ipd.md` top-to-bottom after applying revisions and running `aw ipd sync --apply`.
- Verified `aw ipd lint --phase author --detail` and `--agent`: `outcome: clean`, `findings: 0` (`conforming`, 0 errors, 0 warnings, 0 advisories).
- Verified every class-qualified pytest node ID against the test suite, zero `TODO` placeholders, zero em/en dashes, zero absolute paths, zero file-scheme URIs, and zero leak-sanitizer hits.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R2 | `agent_workflows/artifact_meta.py::REGISTRY["backlog"]`, `is_valid_transition`, `render_legacy`; `tests/test_backlog_descriptive_safety.py`; `tests/test_generators_writing_standard_pointer.py` | `REGISTRY["backlog"]` omitted `set` (`spec 4sd62s` 4.2c) and phase-B `summary` (`backlog.summary-missing`), `is_valid_transition("backlog", None, ...)` rejected `blocked`/`parked`/`graduated`/`done`, and headerless backlog `op == "create"` lacked `- Id:` seeding and pointer-before-history / `body`-after-history placement | Low | FIXED | Added `E-03`/`V-03` registering `set` and migration-only `summary` on `REGISTRY["backlog"]`, widening initial `backlog` transition statuses to `backlog.STATUSES` plus `draft`, and supporting headerless backlog `op == "create"` layout in `render_legacy` |
| PR-002 | BLOCKER | IN-SCOPE | R1 / R2 / R4 | `agent_workflows/backlog.py::_reattach_history`, `_render_item`; `agent_workflows/set_records.py::close_on_answer`; `tests/test_history_label_parity.py` | `E-02` routed `_reattach_history` onto file-mutating `artifact_meta.append`, even though `_reattach_history` and `_render_item` are pure `str -> str` helpers with no file path or `id6` | Low | FIXED | Split `_render_item` (`E-04`/`V-04`) and `_reattach_history` (`E-05`/`V-05`) onto `artifact_meta.render_legacy_text`, keeping `run_new` (`E-01`) on `artifact_meta.create` and `run_note` (`E-02`) on `artifact_meta.append` |
| PR-003 | HIGH | IN-SCOPE | R2 / R3 / R4 | `agent_workflows/backlog.py::_WORKFLOW_HISTORY_HEADING_RE`, `_resolve_backlog_root`; `g6tw94` E-03; `tests/test_history_write_order.py`; `tests/test_backlog.py` | `test_history_write_order.py` (`backlog note`) was mis-assigned to `E-01`, `.agents/backlog` fixtures fell outside `project_records_dir`, `test_generators_writing_standard_pointer.py` and `test_history_label_parity.py` were unpinned, and writer-internal `"Workflow history"` strings violated `g6tw94` E-03 | Low | FIXED | Reassigned `test_history_write_order.py` to `E-02`, pinned `test_generators_writing_standard_pointer.py` (`E-04`) and `test_history_label_parity.py` (`E-05`), rooted `LegacyContext` at `backlog_root.parent`, specified `SidecarRecord` on `run_new` (`--apply`) and `run_note`, and switched header/body splits to `_WORKFLOW_HISTORY_HEADING_RE` and `attention_contract.history_block` |
| PR-004 | LOW | IN-SCOPE | R2 | `F-02`, `D-1`, `D-2`, `V-01..V-05` | Static `def test_` counts in `F-02` lacked non-binding framing (`steps/r2-executability.md`), and `D-1` contained copy-pasted `specs._append_history` / `tests/test_specs_verbs.py` prose from `g6tw94` | Low | FIXED | Framed `F-02` counts and `V-*` test pointers as non-binding pointers re-derived at execution and rewrote `D-1`..`D-3` specifically for `backlog` |
| PR-005 | LOW | IN-SCOPE | R3 / R5 | `## Approval and execution gate` | Execution gate lacked explicit stop-and-report conditions if `7yr827` symbols are absent on `HEAD`, if baseline pinned modules fail before editing, or if shared-checkout edits conflict | Low | FIXED | Added narrow stop-and-report conditions in `## Approval and execution gate` |
| PR-006 | LOW | IN-SCOPE | Proofreading / R6 | `## Proposed changes`, `## Validation and cross-check` | Plan had two `IPD-C802` em dashes, bare `module.func` citations, unqualified `4.3` spec reference, and no Requirement 12(b) diagram | Low | FIXED | Removed em dashes, upgraded citations to `path::Symbol` and `spec 4sd62s`, and added a `mermaid` `flowchart TD` diagram (`0` lint advisories) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| DEC-001 | How should `jlwedt` satisfy phase-B `backlog.validate_item` (`- Set:` and `- Summary:`), non-`open` initial statuses (`blocked`, `parked`, `graduated`, `done`), and headerless pointer-before-history creation without hand-built bullets in `backlog.py`? | Add `E-03` (`V-03`) in `agent_workflows/artifact_meta.py` registering `set` (`generic`, `spec 4sd62s` 4.2c) and `summary` (`migration-only`), widening `is_valid_transition("backlog", None, ...)` to `backlog.STATUSES` plus `draft`, and supporting headerless backlog `op == "create"` layout | Leave `artifact_meta.py` unmodified and keep `- Set:` / `- Summary:` / `- Status:` bullet rendering by hand in `backlog.py` | Keeping hand-built metadata bullets in `backlog.py` violates `jlwedt` Goal and `spec 4sd62s` AC-1, while `agent_workflows/artifact_meta.py` is already declared in `- Scope-Paths:` | yes |
| DEC-002 | Which `artifact_meta` entry point should pure `str -> str` helpers `backlog._render_item` and `backlog._reattach_history` use? | Route `_render_item` (`E-04`) and `_reattach_history` (`E-05`) through `artifact_meta.render_legacy_text`, while CLI `run_new` (`E-01`) uses `artifact_meta.create` and CLI `run_note` (`E-02`) uses `artifact_meta.append` | Route `_reattach_history` through `artifact_meta.append` on a temporary file or inline its callers | `_reattach_history` and `_render_item` are pure `str -> str` contracts called directly by `set_records` (`x2dxvf`, out of scope here) and unit tests; `7yr827` added `render_legacy_text` specifically for pure string writer helpers | yes |
| DEC-003 | How should the checklist be decomposed so every step stays single-concern, within `IPD-Z603` unit limits, and compliant with `g6tw94` E-03's zero writer-internal `"Workflow history"` rule? | Split into 5 steps (`E-03` `artifact_meta.py`, `E-04` `_render_item`, `E-01` `run_new`, `E-02` `run_note`, `E-05` `_reattach_history` + module audit) using `_WORKFLOW_HISTORY_HEADING_RE` and `attention_contract.history_block` | Keep 2 bundled multi-concern steps or leave `"\n## Workflow history"` string splits inside `_render_item` and `_reattach_history` | Eliminates `IPD-Z603` pressure (`<=5` units per step) and guarantees `g6tw94` E-03 finds zero `Workflow history` or hand-built date-bullet hits inside any of the four backlog writer functions | yes |
