# Review findings: ipd j1f454

- Subject-Id: j1f454
- Subject-Type: ipd
- Reviewed-At: 2026-11-26
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261126T155852Z-1343378`). The target plan `.aw/records/plans/pending/20261126-metastore-319-j1f454-make-selectors-status-matching-typed-subject-ownership-and-a.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings). The review examined backlog `ldfefd`, spec `4sd62s` (Sections 4.1, 4.1a, 4.2, 4.3), `Set: metastore` orchestrator `63ib9r` (row 319, E-231) and siblings `e0g2gt`, `p109wy`, `lec341`, and `qi0kl6` (F-05, OQ-01), both cutover patches (`.aw/system/cutover/metastore-docs.cutover.patch` and `.aw/system/cutover/metastore-code.cutover.patch`, inspected via a read-only temporary git index), `agent_workflows/selectors.py`, `agent_workflows/artifact_rename.py`, `agent_workflows/artifact_meta.py`, `tests/test_readers_selectors_find.py`, `tests/test_spec_id6_filenames.py`, and `tests/test_metastore_cutover_code_patch.py`. It found two `BLOCKER`, one `MEDIUM`, and one `LOW` findings (`PR-001..PR-004`), all `Overall:Low` remediation risk and all fixed in place. No production code or test code was modified.

### Step T

1. Yes; the plan changes `selectors.py` status matching, mirror identity reading, and typed-subject ownership and `artifact_rename.py` `--to-id6` log creation and id6 helpers inside `.aw/system/cutover/metastore-code.cutover.patch`, which downstream metastore plans (`lec341`, `qi0kl6`, `x3mig6`, `x1mmdp`, `cxxmyv`) rely on.
2. No; it does not touch leak sanitizers, commit/lock helpers, worktree isolation boundaries, merge-to-main gates, or host sandbox profiles.
3. No; bounded to 5 execution items across 3 task groups, focused on the first of two maintainer-ordered prerequisite production-fix plans ahead of batch E (`qi0kl6` OQ-01 Option 2, Order 319).
4. Yes; `- Scope-Paths:` declares both tracked files modified by this plan (the plan file itself and `.aw/system/cutover/metastore-code.cutover.patch`).
5. Yes; mistakes in `selectors` ownership/status matching or `artifact_rename --to-id6` log creation and rollback could misclassify id6 collisions, miss records during `aw find <type> <status>`, leave renamed files without companion logs or with duplicate legacy bullet blocks, or corrupt prior hunks in `.aw/system/cutover/metastore-code.cutover.patch`.

AW-TIER: standard

### Step R1

- Checked: every cited artifact, patch, module, and test file: backlog `ldfefd`, spec `4sd62s` (Sections 4.1, 4.1a, 4.2, 4.3), orchestrator `63ib9r` (row 319, E-231), sibling plans `e0g2gt`, `p109wy`, `lec341`, and `qi0kl6` (F-05, OQ-01), `.aw/system/cutover/metastore-code.cutover.patch` (reconstructed in a read-only temporary git index), `agent_workflows/selectors.py` (post-patch lines 420-495, 850-1265: `_read_id`, `_read_status`, `_cached_states_by_path`, `_state_matches_status`, `resolve`, `declares_id6`, `declared_id6`, `id6_ownership`, `_declares_typed_subject`), `agent_workflows/artifact_rename.py` (post-patch lines 40-105, 277-775, 855-1170, 1415-1555: `_meta_target_for_file`, `_id6_write_message`, `_read_existing_id6`, `log_format_id6`, `append_log_rename`, `_existing_type_id6s`, `move_with_log_event`, `_apply_log_rename`, `run_rename_generic`, `run_group`), `agent_workflows/artifact_meta.py` (post-patch `_normalize_legacy_types` line 6210, `create` lines 6664-6771), `tests/test_readers_selectors_find.py`, `tests/test_spec_id6_filenames.py`, and `tests/test_metastore_cutover_code_patch.py`.
- Found: `selectors._read_id` and `resolve._states` fail on post-cutover staged prompts and BOM-prefixed YAML mirrors, and `_declares_typed_subject` needs repo-scoped `project_context` resolution from `path` (`PR-001`); `artifact_rename._meta_target_for_file` returns plural `m_type` whereas `artifact_meta.create` requires singular `registry_type`, registry-filtered `fields` (no `status` on walkthroughs), legacy bullets/comments stripped from `body`, `git_mv` rollback on `create` failure, and `read_mirror_id6` check in `_id6_write_message` (`PR-002`); `selectors._read_status` also reads `legacy_raw_status` only and `_existing_type_id6s` should cover managed and legacy prompt comments (`PR-003`). All findings fixed in place.

### Step R2

- Checked: E/V bijection (`5/5`: `E-01..E-05` to `V-01..V-05`, `- Highest E allocated: 05`), dependency chain (`E-01 -> E-02 -> E-03 -> E-04 -> E-05`), `- Scope-Paths:` (2 tracked paths), `- Item-Dependencies: executed:e0g2gt` (verified consistent with `63ib9r` row 319, `e0g2gt`, and `lec341` depending on `executed:j1f454`, with zero module overlap against `lec341` and proper ordering after `p109wy`), runtime-demonstration reachability (`V-02` and `V-03` name the `selectors.py` and `artifact_rename.py` code paths updated by `E-02`/`E-03`; `V-01`, `V-04`, and `V-05` are reachable by construction), durable carriers for all deferred items (`lec341`, `qi0kl6`, `q6fiws`, `cxxmyv`), no hardcoded test counts, and `## Approval and execution gate` execution contract.
- Found: `V-02`, `V-03`, and `V-05` strengthened to cover `declared_id6`/`id6_ownership` on staged prompts, repo-scoped `_declares_typed_subject`, singular `registry_type` and body stripping in `artifact_rename`, and explicit guard behaviors in `V-05` (`PR-001..PR-004`).

### Step R3

- Checked (full form, `standard` tier):
  - Identity and collision integrity: checking `artifact_meta.read_mirror_id6(text)` first in `selectors._read_id`, `artifact_rename._read_existing_id6`, and `_existing_type_id6s` prevents false `OWNERSHIP_SLOT_ONLY` verdicts on staged prompts and prevents minting duplicate id6 values across YAML-mirror and managed-prompt records (`PR-001`, `PR-003`).
  - Cross-repo isolation: resolving `owner = project_context.record_owner_root(path)` and passing `project_context=artifact_meta.legacy_context(owner)` in `selectors._declares_typed_subject` prevents reading the process CWD repository's logs when classifying an external or temporary repo path (`PR-001`).
  - Transaction rollback safety: rolling back `git_mv` if `artifact_meta.create` raises or returns `committed=False` in `artifact_rename.run_rename_generic` prevents leaving a half-renamed file with no log (`PR-002`).
  - Workspace containment and secrets: all code/test edits occur inside the gitignored scratch worktree `.aw/state/j1f454/scratch`, removed before commit; no secrets, credentials, or outbound network calls are introduced.

### Step R4

- Checked: correctness, data integrity, architecture, anti-regression, testing/verification, KISS, right-sizing/conceptual density per E-item, and `## Spec / documentation sync`.
- Found:
  - Missing prompt-mirror/BOM handling in `selectors._read_id` and `resolve._states`, plus missing repo-scoped `project_context` in `_declares_typed_subject` (`PR-001`).
  - Singular `registry_type`, registry-filtered fields (no `status` on walkthroughs), body bullet/comment stripping, `git_mv` rollback, and post-write `_id6_write_message` mirror recognition in `artifact_rename.py` (`PR-002`).
  - `selectors._read_status` log parity and `_existing_type_id6s` prompt coverage (`PR-003`).
  - Technical writing polish, first-use ID explanations, `F-04` anchor table, and diagram sync (`PR-004`).
- Right-sizing check: 5 E-items across 3 task groups, 1 work `Scope-Path` (`.aw/system/cutover/metastore-code.cutover.patch`), matching the maintainer's Option 2 split decision for `qi0kl6` OQ-01 (Order 319 part 1 of 2, paired with Order 320 `lec341`). No further split needed.
- Spec and documentation sync check: verified spec `4sd62s` Sections 4.1, 4.1a, and 4.3 and `.aw/system/cutover/metastore-docs.cutover.patch` already cover the format; no doc changes needed here.

### Step S5

- Checked: `## Open questions` (`None open`). All four findings (`PR-001..PR-004`) have `Overall:Low` remediation risk and are settled by authoritative repository evidence (`spec 4sd62s`, `metastore-code.cutover.patch`, `agent_workflows/*.py`, and `tests/*.py`). Three reversible review decisions are recorded in `### Decisions` (`D-1..D-3`). No blocking or human-owned question remains; outcome JSON records `{"questions": []}`.

### Pass 2

- Re-checked the complete revised plan: front matter (`- Status: reviewed`, `- Review-Depth: standard`, `- Readiness: go-pending-approval`), `## Workflow history`, `## Goal`, `E-01..E-05`, `## Project conventions discovered (Step 0)`, `## Findings` (`F-01..F-04`), `## Proposed changes` and Mermaid `flowchart TD`, `## Deferred / out of scope` (carriers `lec341`, `qi0kl6`, `q6fiws`, `cxxmyv`), `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync`, `## Open questions`, `V-01..V-05`, and `## Approval and execution gate`.
- Swept for superseded wording across all sections.
- Verified `5/5` E/V bijection, unchanged `- Scope-Paths:` and `- Item-Dependencies:`, zero bare `file:line` citations, zero em/en dashes, and clean `aw ipd lint --phase review-finalize --agent`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R3 / R4 / `selectors.py` staged-prompt and BOM `_read_id` / `resolve._states` blind spot and `_declares_typed_subject` repo context | post-patch agent_workflows/selectors.py:441-455 (`_read_id`), 1005-1012 (`resolve._states`), 1101-1133 (`declares_id6`, `declared_id6`), 1186-1238 (`id6_ownership`, `_declares_typed_subject`) | `_read_id(text)` calls `read_text(region)` with default `record_type="ipd"` and checks `startswith("---")` without BOM stripping, returning `None` on post-cutover staged prompts and BOM-prefixed YAML mirrors so `id6_ownership` misclassifies staged prompts as `OWNERSHIP_SLOT_ONLY`. `resolve._states` also omits `record_type` on its fallback `read_text` call. `_declares_typed_subject(path, id6)` takes no `repo_root`, so calling `artifact_meta.read(own_id6)` without `project_context=legacy_context(record_owner_root(path))` queries the process CWD repo instead of `path`'s repo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-02(1)-(3)`, `E-04(1)`, `F-04`, and `V-02` to check `read_mirror_id6(text)` first in `_read_id`, pass `record_type` in `resolve._states`, and resolve `owner = project_context.record_owner_root(path)` with `project_context=artifact_meta.legacy_context(owner)` inside `ephemeral_if_uninitialized()` in `_declares_typed_subject` (`D-1`). Recommendation strength: very strong. |
| PR-002 | BLOCKER | IN-SCOPE | R1 / R3 / R4 / `artifact_rename.py` `--to-id6` singular type, registry-filtered fields, body bullet stripping, `git_mv` rollback, and post-write `_id6_write_message` | post-patch agent_workflows/artifact_rename.py:277-310 (`_meta_target_for_file`), 362-421 (`_id6_write_message`), 1076-1126 (`run_rename_generic`); post-patch agent_workflows/artifact_meta.py:6210-6221 (`_normalize_legacy_types`), 6664-6771 (`create`) | `_meta_target_for_file` discards singular `registry_type` and returns plural `m_type`, whereas `artifact_meta.create` requires singular `registry_type` and registry-valid `fields` (walkthroughs forbid `status` per spec `4sd62s` Section 4.1). Passing raw `dst_text` as `body` would leave legacy bullets or a duplicate prompt comment below the new mirror. `git_mv` runs before `create`, so a failed or uncommitted `create` must roll back `git_mv`. After `create` writes the YAML mirror and strips bullets, `_id6_write_message(..., preview=False, src=dst)` would falsely print `FILENAME ONLY` unless it checks `read_mirror_id6` first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-03(2)-(3)`, `E-04(2)`, `F-04`, and `V-03` to pass singular `registry_type`, filter fields per `REGISTRY[registry_type]` (no `status` on walkthroughs), strip legacy bullets/prompt comments from `body`, roll back `git_mv` on `create` failure, and check `read_mirror_id6` first in `_id6_write_message` while keeping `"would inject"` on preview (`D-2`). Recommendation strength: very strong. |
| PR-003 | MEDIUM | IN-SCOPE | R1 / R4 / `selectors._read_status` log parity and `artifact_rename._existing_type_id6s` prompt coverage | post-patch agent_workflows/selectors.py:457-468 (`_read_status`), 915-933 (`_state_matches_status`); post-patch agent_workflows/artifact_rename.py:587-604 (`_existing_type_id6s`) | `selectors._read_status` reads only `st.legacy_raw_status`, diverging from `_state_matches_status` on log-format mirror text, and `artifact_rename._existing_type_id6s` calls only `_bullet_id6(text)`, missing YAML mirrors and prompt metadata comments when building the mint collision set. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-02(1)`, `E-03(1)`, and `E-04` to check `st.status` before `st.legacy_raw_status` in both `_state_matches_status` and `_read_status`, and check `read_mirror_id6` plus prompt comment readers in `_existing_type_id6s` (`D-3`). Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | P / R2 / R4 / Technical writing polish, first-use ID explanations, and diagram sync | .aw/records/plans/pending/20261126-metastore-319-j1f454-make-selectors-status-matching-typed-subject-ownership-and-a.ipd.md:5-6, 45-106, 146-168; .aw/system/workflows/technical-writing/technical-writing.md | Front-matter `Concern` and `Scope` packed multiple clauses into run-on sentences with unexplained internal IDs; `F-04` was needed to anchor verified post-patch constraints; `V-05` and the Mermaid diagram needed syncing with the revised scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Concern`, `Scope`, `Goal`, `Project conventions`, `Proposed changes`, Mermaid `flowchart TD`, and `V-05` in clear direct sentences with explained first-use IDs, and added `F-04`. Recommendation strength: strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter (`Concern`, `Scope`), `## Goal`, `## Project conventions` | Dense run-on sentences with unexplained IDs (`ldfefd`, `qi0kl6`, `lec341`, `g45vyv`); omitted `_read_id`, `_read_status`, `resolve._states`, singular `registry_type`, and rollback | Clear direct sentences explaining first-use IDs and naming every updated symbol and constraint | PR-001..PR-004 |
| `E-02`, `E-03`, `E-04` | Omitted `_read_id` prompt/BOM handling, `resolve._states` `record_type`, repo-scoped `project_context` in `_declares_typed_subject`, singular `registry_type`, walkthrough no-status rule, body stripping, `git_mv` rollback, and `_read_status` | Explicit per-unit contracts and core behavioral tests covering every verified code path and rollback invariant | PR-001..PR-003 |
| `## Findings`, `## Proposed changes`, Mermaid diagram, `## Scope check` | 3 findings (`F-01..F-03`); diagram and prose predated `PR-001..PR-003` additions | Added `F-04` anchoring all verified post-patch constraints; synchronized `Proposed changes`, `Scope check`, and Mermaid `flowchart TD` | PR-001..PR-004 |
| `V-02`, `V-03`, `V-05` | Omitted prompt `OWNERSHIP_DECLARED`, repo-scoped `_declares_typed_subject`, preview `"would inject"` / apply no-`FILENAME ONLY`, clean body stripping, and explicit guard behaviors | Falsifiable behavioral evidence for every updated code path and guard behavior | PR-001..PR-004 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `selectors._read_id`, `resolve._states`, and `_declares_typed_subject` handle post-cutover staged prompts, BOM mirrors, and companion log lookups? | Check `artifact_meta.read_mirror_id6(text)` first in `_read_id`, pass `record_type=_META_TYPE_FOR_RECORD.get(record_type)` in `resolve._states`, and resolve `owner = project_context.record_owner_root(path)` with `project_context=artifact_meta.legacy_context(owner)` inside `ephemeral_if_uninitialized()` in `_declares_typed_subject`. | Patch only `_state_matches_status` and leave `_read_id` / `project_context` untouched (rejected: misclassifies every post-cutover staged prompt as `OWNERSHIP_SLOT_ONLY` and queries CWD repo instead of `path`'s repo in `_declares_typed_subject`). | Post-patch `agent_workflows/selectors.py:441-455,1005-1012,1186-1238`; spec `4sd62s` Sections 4.1 and 4.1a. | yes |
| D-2 | How should `artifact_rename.run_rename_generic` (`--to-id6 --apply` on unlogged files) invoke `artifact_meta.create` and handle errors and messages? | Resolve singular `registry_type` via `artifact_meta._normalize_legacy_types`, filter fields to `artifact_meta.REGISTRY[registry_type]` (no `status` on walkthroughs), strip legacy bullets or prompt comments from `body`, roll back `git_mv` if `create` raises or returns `committed=False`, append the log path to `touched`, and check `read_mirror_id6` first in `_id6_write_message` while keeping `"would inject"` on preview. | Pass plural `m_type` and raw `dst_text` directly to `create` without rollback or mirror check in `_id6_write_message` (rejected: `create` rejects plural types and walkthrough `status`, duplicates legacy bullets in body, leaves half-renamed files on failure, and prints false `FILENAME ONLY` on apply). | Post-patch `agent_workflows/artifact_rename.py:277-310,362-421,647-690,1076-1126`; post-patch `agent_workflows/artifact_meta.py:6210-6221,6664-6771`; `tests/test_spec_id6_filenames.py:279-475`. | yes |
| D-3 | Should `selectors._read_status` and `artifact_rename._existing_type_id6s` be updated alongside `_state_matches_status` and `_read_existing_id6`? | Yes: check `st.status` before `st.legacy_raw_status` in `_read_status`, and check `read_mirror_id6` plus prompt comment readers in `_existing_type_id6s`. | Leave `_read_status` and `_existing_type_id6s` legacy-only (rejected: causes status-helper drift on mirrors and risks minting colliding id6 values on log-format prompts). | Post-patch `agent_workflows/selectors.py:457-468,915-933`; post-patch `agent_workflows/artifact_rename.py:587-604`. | yes |
