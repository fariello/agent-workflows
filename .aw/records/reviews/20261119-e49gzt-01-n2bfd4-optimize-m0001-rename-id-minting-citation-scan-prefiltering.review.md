# Review findings: ipd n2bfd4

- Subject-Id: n2bfd4
- Subject-Type: ipd
- Reviewed-At: 2026-11-20
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `e8ff347af` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261119-e49gzt-01-n2bfd4-optimize-m0001-rename-id-minting-citation-scan-prefiltering.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, both `aw ipd lint --phase author --agent --verbose` and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` (`exit: 0`, `findings: 0`). Live inspection against backlog `e49gzt`, `agent_workflows/migrations/m0001_renames.py`, `agent_workflows/artifact_refs.py`, `agent_workflows/migrations/m0001_metadata_v2.py`, `tests/test_m0001_renames.py`, `tests/test_artifact_refs_rewrite.py`, `tests/test_m0001_preflight.py`, `pyproject.toml`, and `GUIDING_PRINCIPLES.md` produced findings `PR-001..PR-005`. All five findings have `Overall:Low` remediation risk and were fixed in place with zero human-owned blocking questions (`questions: []`).

### Proofreading

Checked `.aw/records/plans/pending/20261119-e49gzt-01-n2bfd4-optimize-m0001-rename-id-minting-citation-scan-prefiltering.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter & Workflow history | `- Status: to-review`, missing `- Readiness:` and `- Review-Depth:` | Added `- Readiness: go-pending-approval`, `- Review-Depth: standard`, `/plan-review` history line, and transitioned `- Status: reviewed` via `aw ipd set` | Step S7 review output requirements. |
| E-03, V-03, Proposed changes flowchart | Unspecified file-handle closure before `unlink()`, entry replay not isolated before `try ... finally:`, duplicate backup append on half-completed op unguarded, and eager stale-log unlink in `run()` | Required closing `fh` inside `try:` before `finally:` compaction/unlink (Windows-safe), running entry replay + compaction strictly before `try ... finally:`, skipping duplicate backup appends when `op_id in backed_up_by_id`, and unlinking stale `ops-progress.jsonl` in `run()` only when `prior_tx.get("status") != "applying"`; synced Mermaid flowchart | PR-001, crash-recovery & Windows compatibility, Technical Writing Standard Req 12(d)/(e). |
| E-02, V-02, Project conventions | Omitted explicit `re.escape` on `_compile_prefilter` tokens, zero-walk guard for `_index_records_stems`, and `@pytest.mark.core` on new tests in `tests/test_artifact_refs_rewrite.py` | Required `re.escape(token)` in `_compile_prefilter`, explicit zero-walk laziness on `_index_records_stems`, and `@pytest.mark.core` on the new fast behavioral test class in `tests/test_artifact_refs_rewrite.py` | PR-002, prefilter correctness & core-tier coverage. |
| E-04, E-05, V-01, V-02, V-04, V-05, Required tests | Used `-v` without `-o addopts=""` on targeted runs, omitted `- Short-Description:` note on E-04's >=10-op fixture, omitted `0 unlisted slow tests` and `--phase pre-transition` | Standardized targeted runs to `python3 -m pytest -o addopts="" -v --durations=0` with `0 unlisted slow tests`, noted `- Short-Description:` on E-04 synthetic records, and required `aw ipd lint --phase pre-transition` | PR-003, `pyproject.toml` `addopts` / `ya4ee4` / `test_slow_report.py` alignment. |
| Open questions (`OQ-01`, `OQ-02`), Concern, Scope | Omitted recommendation strength on `OQ-01`/`OQ-02` and some `path::Symbol` qualifiers in Concern/Scope | Added `Recommendation strength: strong.` to `OQ-01` and `OQ-02` and normalized `path::Symbol` citations | PR-005, `steps/s5-questions.md` MD-9 & `p-proofread.md` Section 11.1. |
| Approval and execution gate | Omitted resolved open-questions clause, declaration-style scope fence, shared-checkout safety rule, honesty rule, hand-`git mv` ban, and runner vs standalone `e49gzt` closure distinction | Replaced with full execution contract matching `steps/s7-finalize.md` | PR-004, `steps/s7-finalize.md`. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |
| (none) | | | | | |

### Step T

1. No. Optimizes internal migration/citation paths while keeping every public API signature, `journal.json` schema, CLI flag, and rewrite output unchanged.
2. No. Touches no module guarding private data, commits, worktree isolation, merges to `main`, or sandboxes.
3. No. Compact child plan with 5 execution items in 2 task groups across 7 Scope-Paths (3 production modules, 3 test modules, and this plan).
4. Yes. `- Scope-Paths:` explicitly declares all 7 modified files.
5. Yes. `m0001_metadata_v2._execute_planned_operations` mutates repository files during migration (a crash-recovery or backup bug risks failed rollback or corrupted backups), `build_rename_map` mints repository-unique `id6`s, and `artifact_refs.plan_reference_rewrites_with_warnings` rewrites citations across the repository.

AW-TIER: standard

### Step R1

- Checked: backlog `e49gzt`, `agent_workflows/migrations/m0001_renames.py::build_rename_map:441-660`, `agent_workflows/artifact_refs.py` (`_boundaried`, `_facetless_boundaried`, `_mask_fenced_code`, `_mask_permalinks`, `count_legacy_prefix_records`, `_index_records_facetless_stems`, `plan_reference_rewrites_with_warnings`), `agent_workflows/migrations/m0001_metadata_v2.py` (`_peek_journal`, `_execute_planned_operations`, `_cleanup_marker`, `_rollback_all_locked`, `_resume_applying_journal`, `run`, `rollback`), `tests/test_m0001_renames.py`, `tests/test_artifact_refs_rewrite.py`, `tests/test_m0001_preflight.py`, `pyproject.toml`, and `60mazt`.
- Verified all cited symbols resolve verbatim (`_execute_planned_operations`, `_index_records_facetless_stems`, `count_legacy_prefix_records`, `build_rename_map`, `global_id6s`, `generate_id6`, `test_journal_interrupt_mid_apply_resume_and_rollback`), and verified `tests/test_artifact_refs_rewrite.py` has no module-level `pytestmark = pytest.mark.core` (`PR-002`).

### Step R2

- Checked: 5:5 `E-01..E-05` <-> `V-01..V-05` bijection; `- Highest E allocated: 05`; `- Scope-Paths:` completeness; `- Item-Dependencies: none`; concrete per-item evidence in `V-01..V-05`; durable carriers (`Carrier: 60mazt`, two `Carrier-Declined:`); runtime-demonstration reachability; and execution-contract completeness (`PR-004`).

### Step R3

- Checked: Security and data safety across crash recovery, atomic `journal.json` writes (`mgr._save_transaction`), backup preservation on half-completed operations, mid-file JSONL corruption fail-closed refusal (`MigrationError`), `re.escape` protection against regex metacharacters in filenames (`PR-002`), and `aw sanitize --agent` leak check in `E-05`/`V-05`. No secrets or trust-boundary changes introduced.

### Step R4

- Checked: Engineering rubric (A: atomic compaction, Windows-safe handle closure before unlink, corrupt-log preservation before `try ... finally:`, backup-entry deduplication, non-`applying` stale-log guard in `PR-001`; C: reuses `MigrationManager._save_transaction`, `artifact_core.global_id6s`/`generate_id6`, and existing filter helpers; D & E: exact parity and crash-recovery behavioral tests with zero source-code inspection per P16, `@pytest.mark.core` on new fast tests in `test_artifact_refs_rewrite.py`, `0 unlisted slow tests`, `-o addopts=""` on targeted verbose runs; F & right-sizing: 5 focused E-items in 2 task groups across 7 Scope-Paths, one concern per E-item; Spec/doc sync: N/A verified as purely internal runtime optimization preserving `4sd62s` 5.1/5.2 contracts).

### Step S5

- Checked: Pre-existing `OQ-01` and `OQ-02` (`Blocking: no`, `Status: resolved`, `Owner: plan author`); added explicit `Recommendation strength: strong.` (`PR-005`). All 5 findings fixed in place; every decision `D-1..D-4` recorded in `### Decisions` is `Reversible: yes` and grounded in repository code. Zero human-owned blocking questions remain (`questions: []` in `.aw/state/lane-submissions/run-20261120T054627Z-1732272/02-n2bfd4/attempt-2/outcomes/02-n2bfd4.json`).

### Pass 2

- Re-reviewed the complete revised `n2bfd4` plan (`E-01..E-05`, `V-01..V-05`, `Project conventions`, `Findings`, all three Mermaid diagrams, `Deferred / out of scope`, `Scope check`, `Required tests / validation`, `Open questions`, and `Approval and execution gate`) per `steps/s6-rereview.md`.
- Verified `aw ipd lint --phase review-finalize --agent --verbose` exited `0` (`clean`, `findings: 0`), `review_findings` parser returned `0` diagnostics, `check_review_finding_unescalated` returned `0` findings, and `leak_sanitizer.scan_text` returned `0` hits.
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR-001 | HIGH | IN-SCOPE | R4 A Correctness / Crash Recovery & Windows Compatibility | `.aw/records/plans/pending/20261119-e49gzt-01-n2bfd4-optimize-m0001-rename-id-minting-citation-scan-prefiltering.ipd.md:57-61` (`E-03`); `agent_workflows/migrations/m0001_metadata_v2.py::_execute_planned_operations:722-865`; `agent_workflows/migrations/m0001_metadata_v2.py::run:2106-2189` | `E-03` had four crash-recovery/portability gaps: (1) did not require closing `fh` before `finally:` calls `unlink()` (raises `PermissionError` on Windows); (2) did not isolate entry replay/compaction before `try ... finally:` (a mid-file corruption error inside `try:` would make `finally:` overwrite `journal.json` and unlink the corrupt log); (3) unlinking stale `ops-progress.jsonl` unconditionally at `run()` start could destroy an interrupted `applying` journal's progress log during `apply=False`; and (4) did not forbid appending duplicate `backup` entries when `op_id in backed_up_by_id`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-03`, `V-03`, and the `_execute_planned_operations` Mermaid flowchart to require `with open(...)` strictly inside `try:` (closing `fh` before `finally:`), entry replay/compaction strictly before `try ... finally:`, non-duplication of `backup` entries when `op_id in backed_up_by_id`, and unlinking stale `ops-progress.jsonl` in `run()` only when `prior_tx.get("status") != "applying"`. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | R4 A / R4 E (`artifact_refs` prefilter escaping & core tier) | `.aw/records/plans/pending/20261119-e49gzt-01-n2bfd4-optimize-m0001-rename-id-minting-citation-scan-prefiltering.ipd.md:45-51` (`E-02`); `agent_workflows/artifact_refs.py::_boundaried:110-125`; `tests/test_artifact_refs_rewrite.py:1-100` | `E-02` omitted explicit `re.escape(token)` in `_compile_prefilter` (filenames contain `.`, which acts as a wildcard if unescaped), omitted the zero-walk laziness check on `_index_records_stems`, and omitted `@pytest.mark.core` on the new fast test class in `tests/test_artifact_refs_rewrite.py` (which lacks module-level `pytestmark = pytest.mark.core`, so bare `python3 -m pytest` would deselect the new tests). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `re.escape(token)` and empty-kept `None` handling to `E-02` item 3, stated zero-walk laziness in item 1, and marked the new fast behavioral test class in `tests/test_artifact_refs_rewrite.py` with `@pytest.mark.core` (leaving existing slower CLI-spawning classes unmarked). Recommendation strength: strong. |
| PR-003 | MEDIUM | IN-SCOPE | R2 / R4 E (test command flags, `ya4ee4` fixture descriptions & slow report) | `.aw/records/plans/pending/20261119-e49gzt-01-n2bfd4-optimize-m0001-rename-id-minting-citation-scan-prefiltering.ipd.md:67,75,225-246`; `pyproject.toml:224`; `tests/test_m0001_preflight.py::_init_repo:72,84` | Targeted `pytest -v` commands omitted `-o addopts=""` (compounding with `pyproject.toml`'s `-q -n auto` addopts) and `--durations=0` (`0 unlisted slow tests`); `E-04`'s >=10-op fixture omitted noting `- Short-Description:` on synthetic records (needed post-`ya4ee4` for zero host spawns); and `E-05`/`V-05` used bare `aw ipd lint` rather than `aw ipd lint --phase pre-transition`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated targeted commands in `E-05`, `Required tests`, and `V-01`/`V-02`/`V-04`/`V-05` to `python3 -m pytest -o addopts="" -v --durations=0` with `0 unlisted slow tests`, noted `- Short-Description:` in `E-04`, and required `aw ipd lint --phase pre-transition`. Recommendation strength: strong. |
| PR-004 | MEDIUM | IN-SCOPE | R2 / S7 (`Approval and execution gate`) | `.aw/records/plans/pending/20261119-e49gzt-01-n2bfd4-optimize-m0001-rename-id-minting-citation-scan-prefiltering.ipd.md:249-254`; `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46` | `## Approval and execution gate` omitted resolved open-questions summary, declaration-style scope fence (`--scope-reason`/`--scope-ack`), shared-checkout safety rule, honesty rule, hand-`git mv` ban, `aw ipd lint --phase pre-transition`, and runner vs standalone ownership of closing backlog `e49gzt`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced gate prose with the complete execution contract conforming to `steps/s7-finalize.md`. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | S5 / Proofreading (`OQ-01`/`OQ-02` strength & `path::Symbol` citations) | `.aw/records/plans/pending/20261119-e49gzt-01-n2bfd4-optimize-m0001-rename-id-minting-citation-scan-prefiltering.ipd.md:5-6,206-218`; `.aw/system/workflows/plan-review/steps/s5-questions.md:77` | `OQ-01` and `OQ-02` omitted explicit recommendation strength per MD-9 (`steps/s5-questions.md`), and `Concern`/`Scope` used bare module names on several symbols. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `Recommendation strength: strong.` to `OQ-01` and `OQ-02` and normalized `path::Symbol` citations in `Concern`, `Scope`, `Project conventions`, and `Findings`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D-1 | How should `_execute_planned_operations` avoid Windows `PermissionError` and corrupt-log loss during `finally:` compaction? | Run entry replay/compaction before `try ... finally:`, and open `ops-progress.jsonl` inside `try:` (`with open(...) as fh:`) so `fh` is closed before `finally:` calls `mgr._save_transaction` and `unlink()`. | Keep `with open(...)` wrapping `try ... finally:` (fails on Windows with `PermissionError`) or replay inside `try:` (wipes corrupt log in `finally:`). | `agent_workflows/migrations/m0001_metadata_v2.py::_execute_planned_operations:722-865`; Windows CI portability | yes |
| D-2 | When should `run()` unlink a stale `ops-progress.jsonl`? | Only when `prior_tx.get("status") != "applying"` under lock. | Unlink unconditionally on every non-resume `run()` (risks deleting an interrupted `applying` journal's progress log if `run(apply=False)` is invoked). | `agent_workflows/migrations/m0001_metadata_v2.py::run:2034-2189` | yes |
| D-3 | Should the new tests in `tests/test_artifact_refs_rewrite.py` carry `@pytest.mark.core`? | Mark the new fast unit/parity test class `@pytest.mark.core` while leaving existing slower CLI-spawning classes in that file unmarked. | Add module-level `pytestmark = pytest.mark.core` (pulls slow CLI subprocess tests into the 30s core budget) or leave new tests unmarked (leaves prefilter regressions out of bare `pytest`). | `tests/test_artifact_refs_rewrite.py:1-100`; `pyproject.toml:208-224` | yes |
| D-4 | Should `_compile_prefilter` require `re.escape` on kept tokens? | Yes; escape every kept token with `re.escape(token)` before joining into the alternation regex. | Join raw filename tokens without escaping (treats `.` in `.spec.md`/`.ipd.md` as regex wildcard, degrading prefilter selectivity). | `agent_workflows/artifact_refs.py::_boundaried:110-125`; `n2bfd4` `E-02` | yes |
