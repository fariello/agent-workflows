# Review: d4w53g - Move the readiness re-check and coverage writers onto artifact_meta

- Subject-Id: d4w53g
- Subject-Type: ipd
- Reviewed-At: 2026-11-13
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

#### Changes
- Replaced both em dashes (`U+2014`) in `## Validation and cross-check` with commas (`IPD-C802`), added serial commas throughout, and tightened clause structure to direct active voice.
- Upgraded bare `module.symbol` mentions to canonical `path::Symbol` citations (`agent_workflows/plan_readiness.py::recheck_readiness`, `recheck_conditions`, `agent_workflows/readiness_recheck.py::run_recheck_readiness`, `agent_workflows/coverage_record.py::write`, `agent_workflows/artifact_meta.py::append`, and `agent_workflows/project_context.py::record_owner_root`), qualified all post-cutover `4sd62s` section/AC citations (`SPEC-PLAN-TRACE`), and emitted zero absolute paths or `file://` URIs.
- Added a Requirement 12(b) `mermaid` `flowchart TD` diagram in `## Proposed changes (ordered, validatable)` tracing both `recheck_readiness` (`E-01`, `E-02`) and `coverage_record.write` (`E-04`, `E-03`) plus generic `set` and `review_kind` refusal paths through `artifact_meta.append`.

#### Issues
- None remaining after revision; checked against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

### Step T

1. Scope-Path count and nature: 6 paths (`agent_workflows/plan_readiness.py`, `agent_workflows/readiness_recheck.py`, `agent_workflows/coverage_record.py`, `agent_workflows/artifact_meta.py`, `tests/test_writers_obligations.py`, and the plan file) modifying shared `artifact_meta` legacy rendering, both attestation writers, and creating the shared `tests/test_writers_obligations.py` module extended by `xexn45`.
2. Step count and coupling: 4 single-concern `E-*` steps (`E-01`, `E-02`, `E-04`, `E-03`) coupling `recheck_readiness` and `coverage_record.write` to `artifact_meta` phase-B legacy rendering (`2xwb9b`, `7yr827`) and log validation (`tve77h`).
3. Safety, gate, and integrity surface: `Blocks-Release: next` and `From-Spec: 4sd62s`; touches auto-approve gate inputs (`- Readiness:` write-target pin `RECHECK_TARGET_READINESS` and K2 verdict provenance), orchestrator retirement gate receipts (`- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:`, and `## Coverage findings` rollback on failure), and writer-side owned-field refusals (`4sd62s` AC-15, AC-14a).
4. Dependencies and sibling coordination: depends on `executed:tve77h`, `executed:2xwb9b`, and `executed:7yr827`; depended on by `8q27jt`, `b4y4ee`, and `xexn45` (`E-13`, `AC-15`, `AC-14a`).
5. Tier classification: full `complex` review across `R1` through `R7`.

AW-TIER: complex

### Step R1

- Checked: `agent_workflows/plan_readiness.py` (all 1486 lines), `agent_workflows/readiness_recheck.py` (all 411 lines), `agent_workflows/coverage_record.py` (all 373 lines), `agent_workflows/artifact_meta.py` (`OP_PAYLOAD_SCHEMAS`, `validate_event`, `validate_new_events`, `_check_owned_fields`, `replay`, `LegacyTarget`, `LegacyRender`, `render_legacy`, `append_legacy`, `append`), `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (4.1a K2/K3, 4.3, 4.4, N3, AC-14a, AC-15), sibling/parent plans `7yr827`, `8q27jt`, `9qhtrc`, `b4y4ee`, `63ib9r`, and `xexn45`, and all 8 baseline test modules (`110 passed, 2 skipped`).
- Found two blockers and one factual inaccuracy in the original plan:
  1. `E-01` set `ev["message"]` to `plan_readiness.format_recheck_history_entry`, which already begins with `- {date} readiness re-check ({actor}): `, causing `artifact_meta.render_legacy` (`entry = f"- {render.day} {render.tag} ({render.actor_label}): {msg}"`) to emit a malformed double-prefixed history line, and omitted required `OP_PAYLOAD_SCHEMAS["review"]["round"] = (int, True)`, causing `validate_event` to raise `ValueError` on every `recheck_readiness` call (`PR-001`).
  2. `E-03` assumed `artifact_meta` renders `- Coverage-Checked: <YYYY-MM-DD> by <model>` from the actor model while rendering `(<tool>)` in `## Workflow history`, whereas `agent_workflows/artifact_meta.py::render_legacy` currently uses `render.actor_label` for both lines, breaking either `coverage_record.read(...).model` (`tests/test_coverage_record.py::TestCoverageRecordReadWrite::test_write_and_read_fail`) or `(<tool>)` in history (`tests/test_coverage_record.py`, `tests/test_history_date_clock_residual.py`) (`PR-002`).
  3. `E-02` claimed `"when no token can be read the recheck refuses exactly as it does today"`, whereas `agent_workflows/plan_readiness.py::recheck_conditions` currently sets `holds=False` on `C_NEGATIVE_VERDICT` when `polarity is None` (`"none (no verdict token read)"`) (`PR-003`).

### Step R2

- Checked: `E-*`/`V-*` bijection (`E-01..E-04` <-> `V-01..V-04`), `- Scope-Paths:` completeness (`agent_workflows/artifact_meta.py` already declared), PIN-FIRST determinism, `steps/r2-executability.md` non-binding test-count rules, and `aw ipd lint --phase author --detail`.
- Added `E-04`/`V-04` decoupling `LegacyRender.checked_by` from `LegacyRender.actor_label` in `agent_workflows/artifact_meta.py`, specified `dry_run=not apply` plus dynamic `RECHECK_TARGET_READINESS` lookup and `_READINESS_LINE_SUB_RE` retention in `E-01` (`tests/test_plan_readiness_recheck.py::WriteTargetIsPinnedTests`), recorded `D-3` and `D-4` in `## Behavior decisions`, and framed `F-01`/`F-02` test counts and named test pointers as non-binding authoring-time context re-derived at execution (`PR-001`, `PR-002`, `PR-003`, `PR-006`).

### Step R3

- Checked: auto-approve gate write-target pin (`RECHECK_TARGET_READINESS` never from caller input; `set readiness` refused alone and beside `review`), K2 gate verdict provenance (never minting or omitting `verdict` when `classify_verdict` reads `(None, None)`), `AC-14a` (1)-(2) review-kind boundaries (`gate` with refinement verdict refused; `refinement` with `readiness` refused), standalone temp-file lock containment (`record_owner_root` fallback so `test_history_date_clock_residual.py` never writes locks into the live checkout), and leak-sanitizer rules.
- Verified every refused write asserts unchanged file `sha256` in `tests/test_writers_obligations.py` (`V-02`, `V-03`).

### Step R4

- Checked: error handling and write atomicity across `recheck_readiness` and `coverage_record.write`.
- Specified pre-call byte snapshot restoration in `E-03` when `artifact_meta.append` raises after `## Coverage findings` body adjustment (`4sd62s` N3), preserving `coverage_record.write`'s never-raise `CoverageWriteResult(written=False, committed=False, detail=...)` contract (`tests/test_coverage_not_written.py`) with zero partial write (`PR-005`).

### Step R5

- Checked: hostile inputs and boundary cases across maintainer, executor, and downstream-consumer (`xexn45`, `8q27jt`, `b4y4ee`) perspectives: monkeypatched `RECHECK_TARGET_READINESS` falsification test, `model=""` and `model="host-default"` (`by host-default` in `- Coverage-Checked:` and `model by host-default` in history vs `model <name>` when named), id-less standalone `tmp_path / "test.ipd.md"` outside `.aw/records/` (`LegacyTarget` `path-<12hex>` key), plans with `.review.md` rounds vs history-only fixtures (`round_num` resolution), and removed two copy-pasted irrelevant Step 0 bullets about finalize scope reconciliation and rollup retirement (`PR-001`, `PR-005`, `PR-006`).

### Step R6

- Checked: step granularity against `IPD-Z602` and `IPD-Z603` (`<=5` E-items, `<=8` named units per step, `<=8` work `Scope-Paths`), plus execution stop rules.
- Split the `artifact_meta.py` `LegacyRender.checked_by` change into `E-04` (`V-04`) so all 4 steps stay `<=8` units (`0` `IPD-Z603` advisories), and added an explicit unsafe-condition stop rule in `## Approval and execution gate` (`PR-002`, `PR-006`).

### Step R7

- Checked: `- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827` and cross-plan references in `63ib9r` (`E-72`), `8q27jt` (`F-01`, `F-02`, `Deferred`), `b4y4ee` (`aw ipd recheck-readiness`), and `xexn45` (`E-13` line 44 and traceability rows lines 176-177).
- Caught a cross-plan obligation gap (`PR-004`): `d4w53g` line 100 and `xexn45` line 177 assign `4sd62s` `AC-14a` (1)-(2) (`gate` review with refinement verdict refused; `refinement` review with `readiness` refused) to `d4w53g` `E-01, E-02`, yet `E-02`/`V-02` omitted both `AC-14a` cases from `tests/test_writers_obligations.py`. Added both `AC-14a` (1)-(2) cases to `E-02` and `V-02` while preserving `E-01`, `E-02`, and `E-03` numbering so `xexn45` citations remain exact.

### Step S5

- All six findings (`PR-001`..`PR-006`) are `IN-SCOPE`, deterministic engineering alignments with approved spec `4sd62s`, `7yr827`, `8q27jt`, and `xexn45` with `Low` remediation risk. Zero material questions require human decision (`questions: []`).

### Pass 2

- Re-read `.aw/records/plans/pending/20261109-metastore-130-d4w53g-move-the-readiness-re-check-and-coverage-writers-onto-artifa.ipd.md` top-to-bottom after applying revisions and running `aw ipd sync --apply`.
- Caught and corrected test node id paths in `V-03` (`TestCoverageRecordReadWrite` in `tests/test_coverage_record.py` and module-level `test_coverage_record_write_records_utc_date` in `tests/test_history_date_clock_residual.py`).
- Verified `aw ipd lint --phase author --detail` and `--agent`: `outcome: clean`, `findings: 0` (`conforming`, 0 errors, 0 warnings, 0 advisories).
- Verified zero `TODO` placeholders, zero em/en dashes, zero absolute paths, zero `file://` URIs, and zero leak-sanitizer hits.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R2 / R4 | `agent_workflows/plan_readiness.py::format_recheck_history_entry`, `recheck_readiness`; `agent_workflows/artifact_meta.py::OP_PAYLOAD_SCHEMAS["review"]`, `render_legacy`; `tests/test_plan_readiness_recheck.py::WriteTargetIsPinnedTests` | `E-01` passed full `format_recheck_history_entry` text as `ev["message"]` (double-prefixing `- <day> readiness re-check (<actor>): ` under `LegacyRender`), omitted required `round: (int, True)` on `op: "review"`, and omitted `dry_run=not apply` plus dynamic `RECHECK_TARGET_READINESS` / `_READINESS_LINE_SUB_RE` pins | Low | FIXED | Specified `round`, unprefixed `_format_recheck_history_message` body, `dry_run=not apply`, dynamic `RECHECK_TARGET_READINESS` lookup, and `_READINESS_LINE_SUB_RE` retention in `E-01` |
| PR-002 | BLOCKER | IN-SCOPE | R1 / R2 / R4 | `agent_workflows/artifact_meta.py::LegacyRender`, `render_legacy`; `agent_workflows/coverage_record.py::write`, `read`; `tests/test_coverage_record.py::TestCoverageRecordReadWrite::test_write_and_read_fail`; `tests/test_history_date_clock_residual.py::test_coverage_record_write_records_utc_date` | `render_legacy` used `render.actor_label` for both `- Coverage-Checked: <day> by ...` (which must record `<model>` or `host-default`) and `(<tool>)` on the history line, colliding on `coverage_record.write` | Low | FIXED | Added `E-04`/`V-04` and `D-4` adding optional `LegacyRender.checked_by` fallback in `artifact_meta.py` while keeping existing single-label `LegacyRender` callers unchanged |
| PR-003 | HIGH | IN-SCOPE | R1 / R3 | `agent_workflows/plan_readiness.py::recheck_conditions`; `4sd62s` 4.1a K2 | `E-02` claimed `recheck_conditions` already refuses when no verdict token can be read, whereas today `C_NEGATIVE_VERDICT` sets `holds=False` on `polarity is None` | Low | FIXED | Added `D-3` and updated `E-02`/`V-02` so `recheck_conditions` holds `C_NEGATIVE_VERDICT` when `entry is None` or `classify_verdict(entry)[0] is None`, tested in `tests/test_writers_obligations.py` |
| PR-004 | HIGH | IN-SCOPE | R2 / R7 | `d4w53g` `## Required tests / validation`; `xexn45` lines 176-177; `4sd62s` AC-14a (1)-(2) | `xexn45` assigns `4sd62s` `AC-14a` (1)-(2) (`gate` with refinement verdict refused; `refinement` with `readiness` refused) to `d4w53g` `E-01, E-02`, but `E-02`/`V-02` omitted both cases from `tests/test_writers_obligations.py` | Low | FIXED | Added `AC-14a` cases (1) and (2) with `sha256` byte-identity assertions to `E-02` and `V-02` while preserving `E-01..E-03` numbering |
| PR-005 | MEDIUM | IN-SCOPE | R3 / R4 / R5 | `agent_workflows/coverage_record.py::write`; `tests/test_coverage_not_written.py`; `tests/test_history_date_clock_residual.py` | `E-03` omitted pre-call byte restoration when `artifact_meta.append` raises after `## Coverage findings` body mutation (`4sd62s` N3) and omitted `record_owner_root` fallback so standalone `tmp_path` plans outside `.aw/records/` never lock in the live cwd | Low | FIXED | Specified pre-call byte rollback returning `CoverageWriteResult(written=False, ...)` and Step 0 owner-root lock resolution in `E-03` |
| PR-006 | LOW | IN-SCOPE | Proofreading / R2 / R6 | `E-01..E-03`, `## Project conventions discovered`, `## Proposed changes`, `## Validation and cross-check`, `## Approval and execution gate` | Plan had two `IPD-C802` em dashes, unqualified `4sd62s` citations, hardcoded test counts without non-binding framing, irrelevant copy-pasted Step 0 bullets, no Requirement 12(b) diagram, and no unsafe-condition stop rule | Low | FIXED | Removed em dashes and irrelevant Step 0 bullets, qualified `4sd62s` and `path::Symbol` citations, framed test counts as non-binding context, added `mermaid` `flowchart TD` diagram, and added the stop rule (`0` lint advisories) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| DEC-001 | How should `op == "coverage"` render `- Coverage-Checked: <day> by <model>` alongside `- <day> coverage <verdict> (<tool>): ...` without breaking existing `LegacyRender` tests? | Add `E-04` (`D-4`) introducing optional `checked_by: Optional[str] = None` on `LegacyRender` (`render.checked_by or ev.get("actor", {}).get("model") or render.actor_label`) in `agent_workflows/artifact_meta.py` (already in `- Scope-Paths:`) | Overload `actor_label` with either `<tool>` or `<model>` and alter existing `test_coverage_record.py` or `test_artifact_meta_legacy_write.py` assertions | Preserves both `coverage_record.read(...).model` + `(<tool>)` history (`IPD-M112`, `test_coverage_record.py`, `test_history_date_clock_residual.py`) and `test_owned_ac15_3` in `test_artifact_meta_legacy_write.py` with zero assertion churn | yes |
| DEC-002 | How should `recheck_readiness` handle a `no-go` plan whose `## Workflow history` contains no `plan_readiness.VERDICTS` token under `4sd62s` 4.1a K2? | Hold `C_NEGATIVE_VERDICT` in `plan_readiness.recheck_conditions` (`D-3`) so the re-check fails closed without minting or omitting `verdict` | Mint a synthetic `APPROVE`/`REVIEWED` token or emit `verdict=None` on a `gate` review event | `4sd62s` 4.1a K2 requires a `gate` review event's `verdict` to be in `plan_readiness.VERDICTS`, `8q27jt` E-01 forbids minting a verdict, and all pinned readiness fixtures already carry a `VERDICTS` token | yes |
| DEC-003 | Should `d4w53g` preserve `E-01`, `E-02`, and `E-03` numbering when splitting out the `artifact_meta.py` coverage-render step as `E-04`? | Yes: keep `E-01` (readiness move), `E-02` (verdict rule + readiness/`AC-14a` obligations), and `E-03` (coverage move + `AC-15` (3) obligations), and allocate `E-04` via `aw ipd sync --apply` with `E-03` depending on `E-02, E-04` | Renumber `E-03` or split `tests/test_writers_obligations.py` out of `E-02`/`E-03` | Preserves `xexn45` lines 44 and 176-177 cross-plan citations to `d4w53g E-01, E-02` and `d4w53g E-02, E-03` while keeping every step `<=8` named units (`0` `IPD-Z603` advisories) | yes |
