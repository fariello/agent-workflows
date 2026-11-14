# Review: ernmom - Move the plan scaffold, plan sync and prompt create writers onto artifact_meta

- Subject-Id: ernmom
- Subject-Type: ipd
- Reviewed-At: 2026-11-13
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

#### Changes
- Replaced the two em dashes (`U+2014`) in the `## Validation and cross-check` reachability sentence with commas (`IPD-C802`).
- Added a Requirement 12(b) `mermaid` `flowchart TD` in `## Proposed changes (ordered, validatable)` showing `E-04 -> E-01 -> E-02`, `E-04 -> E-02`, and `E-03` independent, plus one sentence explaining why `E-03` has no edge.
- Framed the `F-02` test counts and every named test unit as non-binding pointers that the PIN-FIRST command re-derives at execution, and qualified the pointer names by test class (`ScaffoldTests::`, `SyncTests::`, `TestDryRunDefault::`), because `test_dry_run_writes_nothing` exists in both `ScaffoldTests` and `SyncTests`.
- Rewrote the `## Open questions` sentence so it names the decisions (`D-2` to `D-7`) that carry the answers.

#### Issues
- None remaining after revision; checked against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`. Recommendation strength for the remaining prose: strong.

### Step T

1. Scope-Path count and nature: 4 paths (`agent_workflows/ipd_authoring.py`, `agent_workflows/prompts.py`, `agent_workflows/artifact_meta.py`, and the plan file); the change edits the shared `artifact_meta.REGISTRY` schema, which feeds `compute_schema_hash` and every typed cache table.
2. Step count and coupling: 4 single-concern `E-*` steps after revision (`E-04` registry, `E-01` scaffold, `E-02` sync, `E-03` prompts), coupled to the phase-B legacy writer that `7yr827` adds.
3. Safety, gate, and integrity surface: `Blocks-Release: next` and `From-Spec: 4sd62s`; touches writer-side string-safety refusals (`validate_new_events`), destination containment (`_check_path_safety`) across `.aw/records`, companion, and legacy `.agents/prompts` roots, and byte-pinned templates (`tests/test_ipd_templates.py`).
4. Dependencies and sibling coordination: `executed:tve77h` and `executed:2xwb9b` are executed; `7yr827` is `reviewed` and `g6tw94` is `to-review`; parent `n5sxxk` E-03 audits this plan's writers; `py2vu9` later adds `--summary` to both commands; siblings `b3l7y6` and `3466h8` were reviewed at `complex`.
5. Tier classification: full `complex` review across `R1` through `R7`.

AW-TIER: complex

### Step R1

- Checked: `agent_workflows/ipd_authoring.py` (`_SECTION_BODY`, `build_skeleton`, `run_scaffold`, `compute_sync`, `insert_id_line`, `_backfill_id`, `run_sync`, `_WATERMARK_RE`), `agent_workflows/prompts.py` (`prompts_root`, `render_metadata_comment`, `run_new`), `agent_workflows/artifact_meta.py` (`REGISTRY`, `_COMMON_FIELDS`, `_check_path_safety`, `validate_new_events`, `LegacyRender`, `LegacyTarget`, `WritePreview`, `_LEGACY_BULLET_LABEL`, `legacy_context`, `_check_owned_fields`, `_render_history`, `render_legacy`, `_prepare_legacy_events`, `append_legacy`, `create`, `compute_schema_hash`), `agent_workflows/ipd_schema.py::META_REQUIRED`, spec `4sd62s` 4.2, 4.2b, 4.2c, N3, AC-32(5), AC-40, and section 7 step 4, and the `7yr827` E-01 signatures (`write_legacy`, `render_legacy_text`, phase-B `create(..., legacy_render=...)`).
- Probes in a scratch repository showed `_prepare_legacy_events("ipd", ...)` refuses `author` and `highest_e_allocated` with "unknown field '<f>' for type 'ipd'", accepts the other skeleton fields, and `_check_owned_fields` refuses a `set` of `id`. The original plan passed "its fields" to `create` and the watermark to `append` without naming either gap (`PR-001`, `PR-003`).
- The original `E-01` check `rg -n "Workflow history" agent_workflows/ipd_authoring.py` is vacuous: the only hit is the `build_skeleton` docstring, and the history record is built in `build_skeleton` from `_SECTION_BODY`, not in `run_scaffold` (`PR-004`).

### Step R2

- Checked: the `E-*`/`V-*` bijection (`E-01..E-04` <-> `V-01..V-04` after `aw ipd sync --apply` assigned `E-04`), `- Scope-Paths:` completeness, PIN-FIRST determinism, the pinned modules each move actually exercises, and `aw ipd lint --phase author --agent` and `--phase review-finalize --agent` (both `clean`, 0 findings).
- Widened each E-item's pinned module list to the modules that drive the moved code: `tests/test_ipd_templates.py`, `tests/test_atomic_write_mode.py`, `tests/test_record_owner_root.py`, and `tests/test_companion_record_owner_root.py` for `E-01`; the five `artifact_meta` modules for `E-04`. `V-01` now proves the move by `cmp` of pre-move and post-move scaffold output inside and outside a records root, and `V-03` by comparing the written prompt to `render_metadata_comment` output (`PR-004`, `PR-008`).
- No test file needs editing: `D-3` to `D-7` keep every pinned assertion, so `- Scope-Paths:` stays at three work paths.

### Step R3

- Checked: writer-side string safety (`validate_new_events` on `--author`, `--targets`, `--concerns`), path containment (`_check_path_safety` refuses absolute, `..`, and outside-root paths), the `--path --legacy-name` arbitrary-directory route used by `ScaffoldTests` and `SyncTests`, the legacy `.agents/prompts` root, and the companion and AW_HOME roots driven by `tests/test_record_owner_root.py` and `tests/test_companion_record_owner_root.py`.
- `D-7` now states the containment root (`legacy_context` records root, or `prompts_root(repo_root).parent` for prompts) and the outside-root fallback (`render_legacy_text` plus one `_atomic_write`, the `7yr827` E-03 `_write_fallback_record` pattern), so the move neither refuses today's accepted paths nor bypasses the refusals (`PR-002`). `D-3` and `D-5` state the one CHANGED behavior: an unsafe descriptive value is now refused at exit 2 with nothing written (`PR-007`).

### Step R4

- Checked: single-write atomicity of sync (E/V numbering and watermark in one `_atomic_write`), byte stability of `build_skeleton` for its direct callers (`tests/support.py`, `tests/test_plan_priority_required.py`, `tests/test_ipd_authoring.py`), preview-equals-apply for both commands, and the registry change's effect on `compute_schema_hash` (a cache rebuild, exercised by `tests/test_artifact_meta_cache.py` and `tests/test_artifact_meta_loader_parity.py`).
- `D-6` adds one keyword-only `history_record: bool = True` parameter so default output stays byte-identical, `D-4` keeps one write and states why `write_legacy` is not used for sync, and `D-3`/`D-4` state that each preview prints the rendered text of the same call (`PR-004`, `PR-006`).

### Step R5

- Checked: maintainer, executor, and downstream-auditor (`n5sxxk` E-03, `xexn45` E-14 and F-09, `cxxmyv`, `py2vu9`) perspectives; an approved legacy plan with no `- Id:` (`test_sync_backfills_id_on_approved_plan_without_touching_structure`); a placeholder value the legacy renderer might reformat (`Scope-Paths` TODO text); `--overwrite` of an existing file; and the prompt `Created` key against spec `4sd62s` 4.2b ("New creations use a full timestamp, not `created_day`").
- `D-5` keeps `Created:` in the phase-B comment mirror (pinned by `test_first_line_is_single_line_aw_prompt_comment_with_fields`) and records that `cxxmyv` owns the cutover form (`PR-005`). `D-3` names the fallback when a placeholder would be reformatted. The gate now lists the stop-and-report conditions (`PR-009`).

### Step R6

- Checked: step granularity against `IPD-Z602` and `IPD-Z603` (at most 5 E-items, at most 5 named pointer units per step, at most 8 work `Scope-Paths`).
- Split the registry change into its own step `E-04` so `E-01` and `E-02` each touch one module (`agent_workflows/ipd_authoring.py`); the plan has 4 E-items and 3 work `Scope-Paths`. Lint reports `conforming` with 0 advisories.

### Step R7

- Checked: `- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94`; parent `n5sxxk` (its E-03 audit treats a `Workflow history` hit inside an `ernmom` writer as a defect; after `D-6` the only hits are the `build_skeleton` docstring and the `_SECTION_BODY` key, neither inside `run_scaffold` or `run_sync`); `xexn45` AC-40 case 3 (assigned to `ernmom` E-03, consistent with `D-5`); `b3l7y6` E-03 (adds `author` for `spec`, so `E-04` adds it for `ipd` only when absent); `7yr827` E-01 (maps `highest_e_allocated` to its bullet label).
- The `executed:g6tw94` edge is not needed by any E-item here, but removing it would reorder the Set, which is the author's call; kept (`DEC-004`). No circular dependency: `g6tw94` does not depend on `ernmom`.

### Step S5

- All ten findings (`PR-001`..`PR-010`) are `IN-SCOPE` or `UNDER-SCOPE` and fixed in place with `Low` or `Medium` remediation risk. Every decision (`DEC-001`..`DEC-004`) is reversible and answered from repository code and spec `4sd62s`. No material question requires a human decision (`questions: []`).

### Pass 2

- Re-read `.aw/records/plans/pending/20261109-metastore-123-ernmom-move-the-plan-scaffold-plan-sync-and-prompt-create-writers-o.ipd.md` top to bottom after the revisions and `aw ipd sync --apply` (which assigned `E-04`, its `V-04` skeleton, and advanced `- Highest E allocated:` to `04`), then filled `V-04`.
- Swept superseded wording: no remaining reference to "passes its fields and its created-history message as events", "thin adapter over the legacy writer", or the vacuous `Workflow history` check; `F-03`, `## Scope check`, `## Required tests / validation`, and `## Proposed changes` match `D-3` to `D-7`.
- `aw ipd lint --phase review-finalize --agent`: `outcome: clean`, `findings: 0`. Zero em or en dashes, zero `TODO` placeholders in E or V items, and `aw sanitize --agent`: `outcome: clean`, `findings: 0`.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | UNDER-SCOPE | R1 / R2 | `agent_workflows/artifact_meta.py::REGISTRY["ipd"]`, `_prepare_legacy_events` ("unknown field 'author' for type 'ipd'"); `agent_workflows/ipd_schema.py::META_REQUIRED` | The scaffold's `- Author:` and the sync's `- Highest E allocated:` are not registry fields for `ipd`, so passing them as events raises `ValueError` on the normal path; `Date`, `Concern`, and `Scope` are required bullets with no registry field and no stated disposition | Low | FIXED | Added `E-04`/`V-04` registering `author` and `highest_e_allocated` (string, generic); `D-3` keeps `Date`, `Concern`, and `Scope` as skeleton text in phase B with the spec basis (4.2b, 4.2) and names `cxxmyv` as owner of their removal |
| PR-002 | HIGH | UNDER-SCOPE | R3 | `agent_workflows/artifact_meta.py::_check_path_safety`; `tests/test_ipd_authoring.py::ScaffoldTests` (`tempfile.mkdtemp()`, `legacy_name=True`); `agent_workflows/prompts.py::prompts_root` (legacy `.agents/prompts`) | `artifact_meta.create` refuses a destination outside the records root, but scaffold accepts any `--path` with `--legacy-name` and prompts may live under `.agents/prompts`; the plan named no containment root and no fallback, so the move would break pinned tests or tempt a bypass | Medium | FIXED | Added `D-7`: containment root `legacy_context(repo_root)` records root (prompts: `prompts_root(repo_root).parent`), and an outside-root or `--overwrite` fallback through `render_legacy_text` plus one `_atomic_write` that still runs the writer-side refusals and writes identical bytes |
| PR-003 | HIGH | IN-SCOPE | R1 / R4 | `agent_workflows/ipd_authoring.py::run_sync`, `compute_sync`, `_backfill_id`; `agent_workflows/artifact_meta.py::_check_owned_fields` ("refuse generic set of identity/status field: 'id'"); `tests/test_ipd_authoring.py::SyncTests::test_sync_backfills_id_on_approved_plan_without_touching_structure` | `E-02` said "move `run_sync` onto `artifact_meta.append`" but sync makes three edits (Id backfill, E/V numbering, watermark), only one of which is an aw-owned field write; an `id` set is refused, and a separate `append` after the body write would split one write into two | Low | FIXED | Added `D-4`: Id backfill and E/V numbering stay body edits, the watermark renders through `render_legacy_text` with `history=False`, and the whole result is written once; rewrote `E-02`/`V-02` to match |
| PR-004 | HIGH | IN-SCOPE | R1 / R2 / R4 | `agent_workflows/ipd_authoring.py::build_skeleton` (`_SECTION_BODY[S.H_WORKFLOW_HISTORY]`, docstring "stamps the ``draft`` history record"); `tests/test_ipd_templates.py`; `tests/support.py`; `tests/test_plan_priority_required.py` | The `E-01`/`V-01` check `rg -n "Workflow history"` is vacuous (the only hit is a docstring and the record is built in `build_skeleton`), and moving the history record out of `build_skeleton` would break the byte-pinned templates and direct callers that no pinned module listed | Low | FIXED | Added `D-6` (keyword-only `history_record: bool = True`, default bytes unchanged); replaced the `rg` check with a pre-move/post-move `cmp` of scaffold output inside and outside a records root; added the template, mode, and owner-root modules to the `E-01` pin |
| PR-005 | MEDIUM | IN-SCOPE | R5 | `agent_workflows/prompts.py::render_metadata_comment` (`f"Created: {created}"`); `tests/test_prompts_new.py` ("Created: 2026-08-30"); spec `4sd62s` 4.2b ("New creations use a full timestamp, not `created_day`") | `prompts new` writes `Created:`, which maps only to the migration-only `created_day`; the plan did not say whether the phase-B mirror keeps it | Low | FIXED | Added `D-5`: keep `created_day` in the phase-B comment mirror (pinned, reversible); the 4.2b rule governs log events after the cutover, owned by `cxxmyv` |
| PR-006 | MEDIUM | IN-SCOPE | R4 | `agent_workflows/artifact_meta.py::create` (log-only today, `---\nid:` prefix), `append_legacy` (`WritePreview.text`); `tests/test_ipd_authoring.py::ScaffoldTests::test_dry_run_writes_nothing` | The plan required "preview prints the exact bytes `--apply` writes" without naming where the previewed text comes from after the move | Low | FIXED | `D-3` and `D-4` state that each preview prints the rendered text of the same `dry_run=True` call; `V-01` demands a preview-versus-apply `cmp` |
| PR-007 | MEDIUM | UNDER-SCOPE | R3 | `agent_workflows/artifact_meta.py::validate_new_events`; spec `4sd62s` 4.2 and AC-15 | Routing through `artifact_meta` adds writer-side refusal of unsafe descriptive values (`--author`, `--targets`, `--concerns`), a behavior change the plan did not declare ("no documented behavior changes") | Low | FIXED | `D-3` and `D-5` declare the CHANGED refusal, map it to the existing exit-2 refusal with nothing written, and `V-01`/`V-03` demand a refusal check |
| PR-008 | LOW | IN-SCOPE | R2 | `F-02`; `V-01` ("`test_dry_run_writes_nothing` (both classes)"); `tests/test_ipd_authoring.py::SyncTests::test_dry_run_writes_nothing`; `tests/test_prompts_set_surface.py::create_conforming_prompt` | Static test counts and "names 6 units" read as binding; `V-01` claimed the `SyncTests` copy of `test_dry_run_writes_nothing`, which exercises `E-02`; `F-03` misdescribed the `render_metadata_comment` caller | Low | FIXED | Framed counts and pointer units as non-binding, qualified each pointer by class and assigned it to the E-item it exercises, and corrected `F-03` |
| PR-009 | LOW | UNDER-SCOPE | R5 | `## Approval and execution gate` | The gate had no stop-and-report conditions for absent `7yr827` entry points, a pinned module failing on unmodified `HEAD`, or a shared-checkout conflict | Low | FIXED | Added the three stop conditions, matching siblings `b3l7y6` and `3466h8` |
| PR-010 | LOW | IN-SCOPE | Proofreading | `## Validation and cross-check` (two `U+2014`); `## Proposed changes` | Two `IPD-C802` em dashes and no Requirement 12(b) dependency diagram | Low | FIXED | Replaced the em dashes with commas and added the `mermaid` flowchart |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| DEC-001 | How do `Date`, `Concern`, and `Scope`, which `META_REQUIRED` needs but the registry does not hold, survive the scaffold move? | Keep them as skeleton text inside `body` in phase B (`D-3`) | Register `date`, `concern`, and `scope` as `ipd` fields; drop them now | Spec `4sd62s` 4.2b forbids `created_day` on new creations and 4.2 moves prose fields to the body; registering them would contradict the spec and change `compute_schema_hash` for fields the cutover removes; dropping them breaks `META_REQUIRED` and lint | Yes |
| DEC-002 | Does phase-B `prompts new` keep the `Created:` comment key? | Keep it as a `created_day` mirror value (`D-5`) | Omit it now and edit `tests/test_prompts_new.py` | The PIN-FIRST rule forbids unnamed assertion changes; the 4.2b rule concerns log events after the cutover, which `cxxmyv` owns | Yes |
| DEC-003 | Where is the containment root, and what happens outside it? | `legacy_context` records root (prompts: `prompts_root(repo_root).parent`), with a `render_legacy_text` plus `_atomic_write` fallback (`D-7`) | Refuse outside-root targets; widen `_check_path_safety` | Refusing breaks `ScaffoldTests` and `--legacy-name`; widening the validator weakens a security check every writer shares; the fallback has precedent in `7yr827` E-03 and `b3l7y6` (`specs_dir.parent`) | Yes |
| DEC-004 | Remove the `executed:g6tw94` edge, which no E-item needs? | Keep it | Remove it | Set ordering is the author's choice and the edge creates no cycle; removing it could change Set execution order without a maintainer decision | Yes |
