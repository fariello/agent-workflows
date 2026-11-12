# Review findings: plan 7yr827

- Subject-Id: 7yr827
- Subject-Type: ipd
- Reviewed-At: 2026-11-12
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `2e800a642` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261107-metastore-21-7yr827-add-the-phase-b-legacy-writer-and-move-the-runner-writer-hel.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` `IPD-C802` info advisories on line 120), and the pinned existing test modules passed (`104 passed, 2 skipped`). During revision, `aw ipd sync --apply` assigned `E-03` and `E-04` (advancing `- Highest E allocated:` from `02` to `04`), Pass 2 re-checked the split items (`E-01..E-04` and `V-01..V-04`), and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Scope, Scope check | Cited `xexn45` E-14 as reading `.aw/state/xexn45/` baselines and omitted tracked SHA summary | Cites `xexn45` E-17 and records baseline SHA and counts in `F-04` alongside `.aw/state/xexn45/` | PR-006 (post-split `xexn45` numbering and cross-lane gitignored state). |
| Detailed Implementation Checklist (PIN-FIRST RULE) | Referenced "Behavior decisions D-1 to D-6 below" | References "Behavior decisions D-1, D-2, and D-5 below" | PR-006 (`7yr827` carries `D-1`, `D-2`, and `D-5` only). |
| E-01, E-02 -> E-01..E-04 | Two bundled items covering baselines, extraction, new test module, and two runner modules; hardcoded `(24 tests, ...)` | Four single-concern items (`E-01` writer extraction and phase-B `create`/`append` dispatch, `E-02` core test module and 5-type corpus round trip, `E-03` `runner_shared` moves, `E-04` `review_sequence.restore_pre_s7_plan` move) with non-binding test pointers | PR-001..PR-005, PR-007. |
| Findings (F-01..F-04) | Counted hidden units at `ac76110f4` only; no corpus count or cross-lane baseline row | Re-measured at `2e800a642` (`1` release `f33nrj`, `33` qualifying corpus records, `create` log-test contract) and added `F-04` baseline row | PR-001, PR-002, PR-006. |
| Behavior decisions (D-1, D-5) | D-1 cited non-existent local `E-05`; D-5 routed `restore_pre_s7_plan` through `render_legacy_text` | D-1 attributes specs normalization pin diff to `g6tw94`/`b3l7y6`; D-5 routes `restore_pre_s7_plan` through `artifact_meta.restore_legacy_snapshot` | PR-003, PR-006. |
| Proposed changes | Two-line prose list with no diagram | Four ordered steps plus a Mermaid `flowchart TD` routing diagram | Technical Writing Standard Requirement 12. |
| OQ-04 | `- Owner: none`; omitted `mark_plan_attended` and `_write_fallback_record`; conflicted with `D-5` on `validate_new_events` | Named owner, added `mark_plan_attended`, `_write_fallback_record`, and `restore_legacy_snapshot`, and recorded review probe evidence | PR-003, PR-004, Step S5 HOW rule. |
| Validation and cross-check (line 120, V-01..V-04) | Two em dashes in rule preamble (`IPD-C802`); `V-01` hardcoded `40 byte-identical` | Replaced em dashes with commas; mapped `V-01..V-04` 1:1 to `E-01..E-04` with `>=33` 5-type corpus check and `tve77h`/`2xwb9b` regression pins | Proofreading (`IPD-C802`), PR-001, PR-002, PR-007. |
| Approval and execution gate | Omitted explicit stop condition for concurrent-edit conflict or missing prerequisite symbol | Added narrow unsafe-condition stop sentence while preserving declaration-only scope fence | Step S7 gate check. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `write_legacy`, `render_legacy_text`, and `restore_legacy_snapshot` form the shared phase-B writer contract consumed by sibling parts `g6tw94`, `n5sxxk`, `6e93gt`, `bsl45u`, `8q27jt`, their sub-parts (`b3l7y6`..`h06gs7`), and the test-data builder (`59aiyh`/`j6o96i`).
2. Yes. Touching `artifact_meta.create`, `artifact_meta.append`, `runner_shared` proposal/merge-rederive helpers, and `review_sequence.restore_pre_s7_plan` affects per-artifact file locking (`platform_lock.held`), atomic file writes, lane merge front-matter re-derivation, and pre-S7 review-gate rollback.
3. Yes. Four E-items across three core infrastructure modules (`agent_workflows/artifact_meta.py`, `agent_workflows/runner_shared.py`, `agent_workflows/review_sequence.py`) and a new multi-type test suite (`tests/test_artifact_meta_legacy_writer.py`), pinned against nine existing test modules.
4. No. All five `- Scope-Paths:` entries are explicit file paths, not directory globs, though three are foundational shared modules.
5. Yes. A defect in `write_legacy` or `create` corrupts in-file metadata across plans, specs, backlog items, releases, research docs, or prompts, or breaks `tve77h`/`2xwb9b` log-branch invariants.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (C1, C10a, N3, 4.2, 4.3, section 7 steps 4 and 6, AC-15, AC-21, AC-34); orchestrator `63ib9r`; parent/finishing plan `xexn45` (`E-01`, `E-11`, `E-14`, `E-17`); executed dependencies `tve77h` and `2xwb9b`; downstream plans `g6tw94`, `n5sxxk`, `6e93gt`, `bsl45u`, `8q27jt`, `b3l7y6`, `jlwedt`, `s95hj6`, `ernmom`, `1hfmpb`, `3466h8`, `x2dxvf`, `59aiyh`, `j6o96i`, `cxxmyv`; production modules `agent_workflows/artifact_meta.py`, `agent_workflows/runner_shared.py`, `agent_workflows/review_sequence.py`, `agent_workflows/prompts.py`, `agent_workflows/artifact_rename.py`; test modules `tests/test_artifact_meta_write.py`, `tests/test_artifact_meta_legacy_write.py`, `tests/test_status_set_meta_writer.py`, `tests/test_run_proposal_channel.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_review_sequence_runner.py`, `tests/test_history_date_clock_residual.py`, `tests/test_question_preflight.py`, `tests/test_attended_session.py`.
- Found contract conflict on `artifact_meta.create` (`PR-001`): `tests/test_artifact_meta_write.py` (`tve77h`) and `tests/test_artifact_meta_legacy_write.py::test_render_storage_format_dispatch_log_vs_legacy` (`2xwb9b`) invoke `artifact_meta.create` on an empty `records_root` without `meta/` and assert `records/meta/<id6>.jsonl` is created. Routing `create` unconditionally when `meta/<id6>.jsonl` is absent breaks both suites. Fixed by gating `create`'s phase-B branch on `legacy_render is not None` alongside `_storage_format == "legacy"`, matching `append` (`agent_workflows/artifact_meta.py:4430`), and pinning `tests/test_artifact_meta_write.py` in `E-01`/`V-01`.
- Found contradiction between `D-5` and `OQ-04` (`PR-003`): `render_legacy_text` runs `validate_new_events` and `_check_owned_fields` (which refuses `set readiness`), so `restore_pre_s7_plan` cannot revert `- Status:`, `- Readiness:`, and post-snapshot review history lines through `render_legacy_text` without a dedicated snapshot-restore entry point (`restore_legacy_snapshot`) sharing the internal primitives.
- Found incomplete extraction delta in `E-01` (`PR-005`) and missing runner-helper invariants in `E-02` (`PR-004`): `render_legacy` and `append_legacy` already exist in `artifact_meta.py` from `2xwb9b`, but `_render_history` does not yet preserve a blank line (`D-1`), `_set_bullet` drops bullets when no anchor matches instead of applying `D-2`/`a88210`, field/YAML/`aw-prompt` mappings are incomplete for downstream phase-B callers, `mark_plan_attended` is also pure `str -> str`, `rederive_front_matter` requires pre-render `DriverError` guards plus verbatim `verdict.history_lines`, and `_write_fallback_record` writes outside `.aw/records/`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`4/4` after `aw ipd sync --apply`), dependency ordering (`E-02`, `E-03`, `E-04` each depend on `E-01`), `- Scope-Paths:` accuracy (all 5 paths match planned edits), runtime reachability of every `V-*` demand, and corpus/test counts against HEAD `2e800a642`.
- Found unsatisfiable evidence bar in `V-01` (`PR-002`): `.aw/records/releases/` contains `1` tracked release (`20260820-f33nrj-01-f33nrj-2-0-0.release.md`), so `8` records per type across `5` types yields at most `33` records (`8 + 8 + 8 + 1 + 8`), never `40 byte-identical`. In addition, `4` of the first `8` sorted plans (`5c6bkj`, `509kn1`, `wxh9go`, `d5tz36`) and `1` of the first `8` sorted specs (`25kzda`) carry only `Date`/`Concern`/`Scope`/`Status`/`Author`/`Id`, which `_check_owned_fields` refuses on `set` or `REGISTRY` treats as migration-only/body prose, and `REGISTRY["release"]` needs `set` in `legacy_vocab` to edit `f33nrj` in place. Fixed in `E-01`, `E-02`, `F-02`, and `V-02`.
- Converted hardcoded test count `(24 tests, ...)` into non-binding pointers re-derived at execution by the PIN-FIRST command (`PR-007`).

### Step R3

- Checked: per-record lock discipline (`platform_lock.held` under `.aw/state/locks/meta-<key>.lock`), `artifact_core.atomic_write`, `validate_new_events` descriptive-safety and leak-sanitizer checks (`_writer_ruleset`), path traversal checks (`_check_path_safety`), `rederive_front_matter` allow-list enforcement (`REDERIVABLE_FRONT_MATTER_KEYS`), and prompt purity (`20260808-1958-01-prompt-purity-lint` R1/P4).
- Preserving `rederive_front_matter`'s `DriverError` allow-list guard (`PR-004`) prevents an untrusted lane modification outside `Work-Kind`/`Priority` from reaching `render_legacy_text`, and routing `_write_fallback_record` through `render_legacy_text` avoids writing untrusted fallback paths into `.aw/records/` or `.aw/state/journals/`.

### Step R4

- Checked: correctness, error handling (`source_digest` mismatch and `validate_new_events` refusal before disk mutation), operability in isolated lane worktrees, `4sd62s` C1/C10a/AC-15/AC-34 invariants, right-sizing (`IPD-Z602` and `nj8zdp`), and outcome-based testing (`AGENTS.md` no source-pinning rule).
- Right-sizing (`PR-007`): split the 2 dense items into 4 single-concern items (`E-01` `artifact_meta.py` implementation, `E-02` `tests/test_artifact_meta_legacy_writer.py`, `E-03` `runner_shared.py` move, `E-04` `review_sequence.py` move) and eliminated semicolon-chained multi-concern phrasing (`IPD-Z602`).
- Cross-lane operability (`PR-006`): added `F-04` to persist the baseline commit SHA and counts in tracked plan text alongside gitignored `.aw/state/xexn45/`.

### Step R5

- Checked: QA/QC (`V-01..V-04` falsifiability and corpus counts), Architect (single legacy renderer shared across path I/O, validated string rendering, and pre-S7 snapshot rollback), Software Engineer (`append_legacy` thin delegation and complete field mapping table for downstream plans), Security/Runner Operator (`rederive_front_matter` allow-list and fallback-record isolation), and Modest Executor (explicit 4-step checklist with zero unstated edge cases).

### Step R6

- Checked: 4 `E-*` items in 2 task groups across 5 explicit `- Scope-Paths:` entries (`- Size assessment: standard`). Within `nj8zdp` guidance (`<=5` E-items, `<=5` Scope-Paths, single module/test-surface per item after splitting `E-01..E-04`). No child-plan split is needed; `7yr827` is already the first leaf split out of `xexn45`, and every downstream `xexn45` part depends on `executed:7yr827`.

### Step R7

- Checked: `- Item-Dependencies: executed:tve77h, executed:2xwb9b` (both verified under `.aw/records/plans/executed/`), `xexn45` (`E-01`, `E-11`, `E-17`), and downstream dependents `g6tw94`, `n5sxxk`, `6e93gt`, `bsl45u`, `8q27jt`, `b3l7y6`..`h06gs7`, and `59aiyh`/`j6o96i`.
- Fixed stale post-split references (`xexn45` E-14 -> E-17, `D-1 to D-6` -> `D-1, D-2, and D-5`, and `D-1` `E-05` -> `g6tw94`/`b3l7y6`, `PR-006`) and ensured `E-01`'s field/comment/YAML table covers the registry fields downstream writer moves pass (`PR-005`).

### Step S5

- Checked: `OQ-04` (pre-existing resolved non-blocking question) and four HOW/contract choices surfaced by `PR-001`..`PR-004`.
- Demonstrated at review via Python probe against `agent_workflows/artifact_meta.py` at `2e800a642`: `_prepare_legacy_events` + `_check_owned_fields` + `render_legacy` updates `- Priority:` and `- Work-Kind:` in memory with zero file I/O while raising `ValueError: refuse set of review-owned field 'readiness'` on `set readiness`, and `project_context` inspection confirmed `tests/test_artifact_meta_write.py` passes a bare `logical_roots`-only `Ctx` with `legacy_render=None`.
- Recorded all four self-resolved engineering choices in `### Decisions` (`D-1`..`D-4`), all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-01..E-04` and `V-01..V-04` per `steps/s6-rereview.md` rule 1 because `E-03`/`E-04` and `V-03`/`V-04` were added via `aw ipd sync --apply`.
- Verified `E-01..E-04` <-> `V-01..V-04` 1:1 bijection, `- Highest E allocated: 04`, unchanged `- Scope-Paths:` and `- Item-Dependencies:`, and resolved one Pass-2 `IPD-Z602` clause-chaining advisory in `E-03` so `aw ipd lint --phase author --detail` reported `0` findings (`conforming`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | R1 / E-01 | `agent_workflows/artifact_meta.py:4430`, `agent_workflows/artifact_meta.py:4613`, `tests/test_artifact_meta_write.py:44` | `E-01` routed `artifact_meta.create` through `write_legacy` without a dispatch rule, but `meta/<id6>.jsonl` never exists at creation time, so `_storage_format == "legacy"` alone would break `tve77h` and `2xwb9b` log-branch unit tests that call `create(..., project_context=ctx)` on an empty `records_root`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified `create(..., legacy_render=None, **legacy_kwargs)` routing to `write_legacy` when `legacy_render is not None` and `_storage_format == "legacy"` (matching `append`), keeping `legacy_render=None` on the v2 log branch, and pinned `tests/test_artifact_meta_write.py` in `E-01` and `V-01`. |
| PR-002 | HIGH | IN-SCOPE | R2 / E-01, V-01 | `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md:1`, `agent_workflows/artifact_meta.py:306` | `V-01` demanded `"reporting 40 byte-identical"` across 5 types (`8` each), which is impossible because `.aw/records/releases/` has only `1` release (`max = 33`), and `4` of the first `8` sorted plans plus `1` of the first `8` sorted specs carry no non-owned `set`-writable bullet while `REGISTRY["release"]` relies on `legacy_vocab` for `set`/`version`/`order`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Filtered the sorted per-type selection in `E-02` to records carrying an in-file non-owned `set`-writable field, included `set`/`order`/`version` in `_LEGACY_BULLET_LABEL` (`legacy_vocab`), documented the `33`-record measurement in `F-02`, and updated `V-02` to require `<N>/<N> byte-identical` across all 5 types (`N >= 33`). |
| PR-003 | HIGH | IN-SCOPE | R1 / E-02, D-5, OQ-04 | `agent_workflows/artifact_meta.py:3871`, `agent_workflows/review_sequence.py:180` | `OQ-04` required `render_legacy_text` to run `validate_new_events` (and `_check_owned_fields`, which refuses `set`/`unset` of `status` and `readiness`), contradicting `D-5` and `E-02` which routed `restore_pre_s7_plan`'s `- Status:`, `- Readiness:`, and review-history rollback through `render_legacy_text` with zero `set readiness` event. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Kept `render_legacy_text` strictly validated by `validate_new_events` + `_check_owned_fields` and added `artifact_meta.restore_legacy_snapshot` over the same internal bullet/history primitives for `restore_pre_s7_plan` (`E-01`, `E-04`, `D-5`, `OQ-04`). |
| PR-004 | HIGH | IN-SCOPE | R1 / E-02 | `agent_workflows/runner_shared.py:595`, `agent_workflows/runner_shared.py:628`, `agent_workflows/runner_shared.py:1388` | `E-02` counted only two pure text helpers (omitting `mark_plan_attended`, which is also `str -> str`), omitted `rederive_front_matter`'s `DriverError` allow-list/shape guards and verbatim lane history lines, and omitted that `_write_fallback_record` writes outside `.aw/records/` under `<run_dir>/proposals/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified all three `runner_shared` helpers cleanly in `E-03`, added `op == "legacy"` (`source == "history"`) verbatim history-line support in `E-01`, preserved `rederive_front_matter`'s `DriverError` pre-checks, and routed `_write_fallback_record` through `render_legacy_text` + `atomic_write`. |
| PR-005 | MEDIUM | IN-SCOPE | R1 / E-01 | `agent_workflows/artifact_meta.py:3918`, `agent_workflows/artifact_meta.py:4050`, `agent_workflows/artifact_meta.py:4112` | `E-01` did not enumerate the concrete gaps between `2xwb9b`'s existing `append_legacy`/`render_legacy` and full phase-B writer support (`_render_history` blank-line preservation, `_set_bullet` `D-2`/`a88210` fallback, and missing bullet, research YAML, and `aw-prompt` comment field mappings needed by downstream plans). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Enumerated the three deltas and complete bullet, YAML, and `aw-prompt` field mappings in `E-01`, keeping `append_legacy` as a thin delegate to `write_legacy`. |
| PR-006 | MEDIUM | IN-SCOPE | R7 / Scope, E-01, D-1 | `.aw/records/plans/pending/20261107-metastore-21-7yr827-add-the-phase-b-legacy-writer-and-move-the-runner-writer-hel.ipd.md:6`, `.aw/records/plans/pending/20261107-metastore-21-7yr827-add-the-phase-b-legacy-writer-and-move-the-runner-writer-hel.ipd.md:36`, `.aw/records/plans/pending/20261107-metastore-21-7yr827-add-the-phase-b-legacy-writer-and-move-the-runner-writer-hel.ipd.md:77` | Plan text retained pre-split references (`xexn45` E-14 instead of E-17, `D-1 to D-6`, and local `E-05` in `D-1`) and stored `xexn45` baselines only under gitignored `.aw/state/xexn45/`, which does not cross isolated lane worktrees. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `xexn45` E-14 -> E-17, fixed `D-1, D-2, and D-5` and `g6tw94`/`b3l7y6` references, and added `F-04` to record the baseline SHA and counts in tracked plan text. |
| PR-007 | MEDIUM | IN-SCOPE | R6 / E-01, E-02 | `.aw/records/plans/pending/20261107-metastore-21-7yr827-add-the-phase-b-legacy-writer-and-move-the-runner-writer-hel.ipd.md:40`, `.aw/records/plans/pending/20261107-metastore-21-7yr827-add-the-phase-b-legacy-writer-and-move-the-runner-writer-hel.ipd.md:45` | `E-01` bundled production writer extraction with authoring a multi-scenario test module (`~19` hidden units), `E-02` bundled two independent runner modules and hardcoded `(24 tests, ...)`, and `Proposed changes` lacked a Requirement 12 diagram. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into `E-01..E-04` (`V-01..V-04`) via `aw ipd sync --apply`, framed test names as non-binding pointers re-derived by the PIN-FIRST command, removed em dashes (`IPD-C802`), and added a Mermaid `flowchart TD` diagram. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `artifact_meta.create` distinguish phase-B legacy writes from v2 log writes when `meta/<id6>.jsonl` never exists at creation time? | Gate phase-B `create` on `legacy_render is not None` alongside `_storage_format(records_root, target) == "legacy"`, matching `2xwb9b`'s `append` contract and leaving `legacy_render=None` on the v2 log branch. | Dispatch solely on `_storage_format == "legacy"` (breaks `tests/test_artifact_meta_write.py` and `test_render_storage_format_dispatch_log_vs_legacy`); require callers to call `write_legacy` directly instead of `create` (violates `b3l7y6`, `jlwedt`, `3466h8`, and `59aiyh` contracts). | `agent_workflows/artifact_meta.py:4430`, `tests/test_artifact_meta_write.py:44`, `tests/test_artifact_meta_legacy_write.py:669` | yes |
| D-2 | How should the 5-type tracked-corpus byte-identity round trip select records given only 1 tracked release and legacy 2026-07 records lacking `Set`/`Priority`? | Select up to 8 tracked records per type in sorted path order carrying an in-file non-owned `set`-writable field (including `set` in `legacy_vocab` for `release`), requiring 100% byte-identity across all selected records (`33` at `2e800a642`). | Hardcode `40` records (impossible with 1 release); pick blind first-8 sorted paths (hits owned-only bullets on 4 early plans and 1 spec). | `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md:1`, `agent_workflows/artifact_meta.py:4257` | yes |
| D-3 | How should `review_sequence.restore_pre_s7_plan` restore `- Status:`, `- Readiness:`, and review history without violating `render_legacy_text`'s `validate_new_events` refusal on `set readiness`? | Expose `artifact_meta.restore_legacy_snapshot` over the same internal `_render_status`, `_set_bullet`, and history primitives inside `artifact_meta.py`, keeping `render_legacy_text` strictly validated. | Bypass `_check_owned_fields` on all `render_legacy_text` calls (weakens AC-15 refusal); leave regex metadata writers inside `review_sequence.py` (violates `4sd62s` section 7 step 4 / AC-1). | `agent_workflows/artifact_meta.py:3876`, `agent_workflows/review_sequence.py:180`, `4sd62s` AC-15 | yes |
| D-4 | How should `rederive_front_matter` and `_write_fallback_record` render history lines and stubs outside `.aw/records/`? | Support `op: "legacy", source: "history", line: <str>` in `render_legacy_text` for verbatim lane history lines while keeping `rederive_front_matter`'s `DriverError` guards, and render `_write_fallback_record` via `render_legacy_text` + `atomic_write`. | Re-format lane history lines from `LegacyRender` (alters lane actor/tag formatting); route `_write_fallback_record` through `artifact_meta.create` (pollutes `.aw/records/` or fails on `"unknown"` `id6`). | `agent_workflows/runner_shared.py:628`, `agent_workflows/runner_shared.py:1388`, `agent_workflows/artifact_meta.py:155` | yes |
