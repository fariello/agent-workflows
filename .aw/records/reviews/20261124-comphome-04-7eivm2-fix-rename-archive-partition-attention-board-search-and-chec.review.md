# Review: Fix rename archive partition attention board search and check_engine external-record bugs

- Subject-Id: 7eivm2
- Subject-Type: ipd
- Subject-Path: .aw/records/plans/pending/20261124-comphome-04-7eivm2-fix-rename-archive-partition-attention-board-search-and-chec.ipd.md
- Reviewed-At: 2026-11-25
- Reviewer: antigravity/Gemini 4 Neon (High)
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

Checked against `.aw/system/workflows/technical-writing/technical-writing.md` (all 12 requirements):
- Rewrote run-on semicolon-chained `E-01..E-04` paragraphs into numbered sub-steps with canonical `agent_workflows/<mod>.py::<Symbol>` references (Reqs 1, 2, 3, 5, 7).
- Added two Mermaid diagrams in `## Proposed changes (ordered, validatable)` illustrating the task execution graph and the logical-vs-physical record routing and git-root partitioning flow (Req 12).
- Verified zero em or en dashes in the revised IPD and this review record.

### Step T

Selected review tier: `complex` (`- Review-Depth: complex`). The plan spans 11 production modules and 2 test files (14 `Scope-Paths`), fixes 9 bug clusters across CLI record verbs, `attention`, `partition`, `plan_readiness`, `artifact_refs`, `ipd_authoring`, and `check_engine`, involves security path-containment and in-flight begin-receipt invariants, and shares files with sibling plans `7gverp` and `7hfx7r` inside Set `comphome`.

### Step R1

Verified every cited module, symbol, and call-site contract against the current repository:
- Found broken symbol `research_archive.apply_archive` (does not exist; actual function is `agent_workflows/research_archive.py::apply_moves` at L320) -> `PR-001`.
- Found broken `_core.git_mv` calling contract (`E-01` proposed passing `record_git_root`-relative paths to `_core.git_mv(repo_root, ...)`, which would join onto `repo_root`) and unspecified logical-vs-physical `touched` handoff between `E-01` (`repo_relative_posix` -> `.aw/records/...`) and `E-02` (`_offer_records_commit` / `_offer_archive_commit`) -> `PR-002`.
- Found unspecified return-key contract for `plan_readiness.py::review_staleness_index` across all four callers (`ipd_lint.py`, `status_set.py`, `attention.py`, `check_engine.py::check_review_stale`) and unspecified logical `review_ref` return format for `_resolve_recheck_review_binding` -> `PR-003`.

### Step R2

Audited architecture, edge cases, and failure modes across all 11 modules:
- Found missed `repo_root /` and `relative_to(repo_root)` sites in `partition.py` (`_is_active_member`, `classify_sets` `orch_p`/`mp`), `attention.py` (`_filter_drift_by_selection` `d.location`, `run_attention` `w.location`, legacy `.agents/docs/research` in `scan`), `cli.py` (`_run_plans` JSON/agent mode, `_run_search` `-s`/`--status` and `rel_p`), and `artifact_refs.py` (`rewrite_scope_path_citations` stdout/`Change.path`) -> `PR-004`.
- Identified containment and placement-resolution guards needed in `check_engine.py::stale_record_scope_paths`, `check_engine.py::resolve_gate_ref`, and `ipd_authoring.py::_run_bulk_id_backfill` -> `PR-005`.

### Step R3

Checked security and leak-posture boundaries:
- Added explicit containment checks (`is_relative_to(records_root)`) in `stale_record_scope_paths`, `resolve_gate_ref`, `_resolve_recheck_review_binding`, `_is_pending_plan_file`, and `filter_in_flight_plan_edits` so `..` traversals and out-of-root paths fail closed.
- Replaced absolute-path fallbacks with `artifact_core.py::repo_relative_posix` across all human, JSON, `--agent`, and `Drift` output surfaces to satisfy `docs/cli-output-contract.md` and `assert_valid_agent_record`.

### Step R4

Checked test coverage and validation commands:
- Expanded `## Required tests / validation`, `E-06`, and `V-06` from 2 companion test files to all 14 relevant regression suites (`test_artifact_rename.py`, `test_plans_archive.py`, `test_research_archive.py`, `test_partition.py`, `test_attention.py`, `test_plan_readiness_recheck.py`, `test_plans_board.py`, `test_cli_search.py`, `test_artifact_refs_rewrite.py`, `test_rename_receipt_guard.py`, `test_ipd_authoring.py`, `test_check_engine.py` plus the two companion test files) and mapped concrete companion/`~/.aw/` and negative containment tests into `E-05` -> `PR-006`.

### Step R5

Checked `docs/cli-output-contract.md` and `.aw/records/specs/` (`4sd62s`, `25kzda`): upgraded `## Spec / documentation sync` from a bare `N/A` to an explicit verification statement.

### Step R6

Evaluated `IPD-Z603` advisories (6 E-items, 14 `Scope-Paths`, 11 production modules). Confirmed `- Size assessment: exception` is justified by single-root-cause cohesion and tight cross-module coupling (`attention` <-> `plan_readiness` <-> `check_engine`, `artifact_rename`/`archive` <-> `cli::_offer_records_commit`); strengthened `- Cohesion rationale:` and added the full execution contract in `## Approval and execution gate` -> `PR-007`.

### Step R7

Verified Set `comphome` dependencies and sibling overlaps:
- `Item-Dependencies: executed:ywl7uc` accurately captures the `artifact_core.py::git_mv` and `project_context.py` prerequisite.
- Overlaps with `7gverp` (`cli.py`) and `7hfx7r` (`check_engine.py`, `attention.py`, `tests/test_companion_doctor_and_carriers.py`) are functionally disjoint and safely handled by isolated runner worktrees and the merge-and-revalidate gate.
- Preserved `post_relocation_citation_rewrite` return-path compatibility with `mmuv3v` (`status_set.py`), and documented all five Set `comphome` sibling carriers in `## Deferred / out of scope (with reason)`.

### Step S5

All seven findings (`PR-001..PR-007`) are Low or Medium Remediation Risk and resolved directly from repository code and documented contracts. Zero human-only blocking questions remain; recorded four autonomous engineering decisions (`D-1..D-4`) below.

### Pass 2

Re-read the revised IPD end-to-end: every `E-01..E-06` pairs 1:1 with `V-01..V-06`, all symbol names and line-verified contracts match the codebase, zero unresolved `TODO` or open questions exist, both Mermaid diagrams render cleanly, `- Readiness: go-pending-approval` and `- Review-Depth: complex` are set, and `ipd lint --phase review-finalize` is ready to run.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | High | in-scope | References / Atomicity | `agent_workflows/research_archive.py:320-386` | Plan cited nonexistent `research_archive.apply_archive` instead of `research_archive.py::apply_moves` and did not specify pre-validating source/destination existence and `research_root` containment before `artifact_meta.append` mutates status on disk. | Medium | fixed | Fixed in `Concern`, `E-01`, `Findings`, and `V-01` to name `research_archive.py::apply_moves` and require pre-validation of all move paths and companion dirs before the first status write (recommendation strength: very strong). |
| PR-002 | High | in-scope | Contract / Self-Commit | `agent_workflows/artifact_core.py:465-540,656-665`; `agent_workflows/artifact_rename.py:286-290,521,564,697-711`; `agent_workflows/cli.py:8753-8813`; `agent_workflows/plans_archive.py:486-538`; `agent_workflows/research_archive.py:763-816` | `E-01` instructed passing `record_git_root`-relative paths to `_core.git_mv(repo_root, ...)` (which joins onto `repo_root` and fails) and left the logical-vs-physical `touched` handoff between `E-01` (`repo_relative_posix` -> `.aw/records/...`) and `E-02` (`_offer_records_commit`/`_offer_archive_commit`) unspecified; `artifact_rename.py` L289 and L564 also misresolved external roots. | Medium | fixed | Updated `E-01` to pass full resolved paths for external `_core.git_mv` moves (and `move_with_log_event` rollback), use `repo_relative_posix` for display/`touched`, and fix `_meta_target_for_file`/`find_unrewritable_path_citations`; updated `E-02` to resolve logical `.aw/records/...` paths before `record_git_root` partitioning in `cli.py::_offer_records_commit` and delegate both `_offer_archive_commit` helpers to it (recommendation strength: very strong). |
| PR-003 | High | in-scope | Contract / Callers | `agent_workflows/plan_readiness.py:1219-1252,1474-1617`; `agent_workflows/attention.py:957-968`; `agent_workflows/check_engine.py:4300-4340`; `agent_workflows/ipd_lint.py:3080-3085`; `agent_workflows/status_set.py:1723-1732` | `E-03` did not specify the return-key contract for `plan_readiness.py::review_staleness_index` across its 4 callers (where `ipd_lint`/`status_set` pass `companion_root` while `attention`/`check_engine` pass `target_repo`), omitted `check_engine.py::check_review_stale`, and did not specify leak-free logical `review_ref` formatting in `_resolve_recheck_review_binding`. | Medium | fixed | Specified per-`git_root` partitioning, `(git_root, git_rel, mtime_ns)` caching, and `repo_relative_posix(abs_path, repo_root_path)` return keys in `E-03`, updated `attention.py::scan` and `check_engine.py::check_review_stale`, and required contained logical `review_ref` output in `_resolve_recheck_review_binding` (recommendation strength: very strong). |
| PR-004 | High | in-scope | Completeness / Leak Posture | `agent_workflows/partition.py:281,531,609`; `agent_workflows/attention.py:786,4104-4132,5402-5440`; `agent_workflows/cli.py:13099,17756,17816`; `agent_workflows/artifact_refs.py:1096-1133` | Several sibling `repo_root /` and `relative_to(repo_root)` sites in already-scoped modules were missed (`partition.py::_is_active_member` and `classify_sets` `orch_p`/`mp`, `attention.py` warning/drift location matching and legacy `.agents/docs/research`, `cli.py::_run_plans` JSON/agent mode and `_run_search` `-s`/`rel_p`, and `artifact_refs.py::rewrite_scope_path_citations` stdout/`Change` paths). | Medium | fixed | Added all missed sites to `E-02`, `E-03`, and `E-04` using a shared logical-to-physical resolver and `repo_relative_posix` while keeping `post_relocation_citation_rewrite` return paths compatible with `mmuv3v` (recommendation strength: strong). |
| PR-005 | High | in-scope | Security / Containment | `agent_workflows/check_engine.py:9510-9525,10369-10435`; `agent_workflows/ipd_authoring.py:1036-1053` | `E-04` did not explicitly mandate strict `records_root` containment (`is_relative_to`) when resolving `.aw/records/<rest>` in `stale_record_scope_paths` and `resolve_gate_ref`, nor `resolve_verb_repo_root` in `ipd_authoring.py::_run_bulk_id_backfill`. | Medium | fixed | Added explicit containment guards against `..` traversal in `stale_record_scope_paths` and `resolve_gate_ref`, required `_core.repo_relative_posix` normalization on `hit_rels` and `StaleScopePath.resolved`, and specified `resolve_verb_repo_root` + `has_stored_records_placement` in `_run_bulk_id_backfill` (recommendation strength: very strong). |
| PR-006 | Medium | in-scope | Testing / Validation | `.aw/records/plans/pending/20261124-comphome-04-7eivm2-fix-rename-archive-partition-attention-board-search-and-chec.ipd.md` (`E-05`, `E-06`, `## Required tests / validation`, `V-06`) | Validation only ran 2 companion test files and omitted the 12 existing unit/contract regression suites covering the 11 modified production modules; `E-05` did not specify negative traversal or in-flight receipt skip cases. | Low | fixed | Added all 12 existing module regression suites to `## Required tests / validation`, `E-06`, and `V-06`, and detailed per-file positive and negative behavioral test coverage in `E-05` (recommendation strength: strong). |
| PR-007 | Medium | in-scope | Structure / Prose / Diagrams | `.aw/records/plans/pending/20261124-comphome-04-7eivm2-fix-rename-archive-partition-attention-board-search-and-chec.ipd.md` | Plan lacked Mermaid diagrams (Technical Writing Standard Req 12), used dense semicolon-chained `E-*` paragraphs and informal symbol names, lacked full execution-contract clauses in `## Approval and execution gate`, and listed only one Set `comphome` sibling in `## Deferred / out of scope`. | Low | fixed | Added two Mermaid diagrams, structured numbered sub-steps with canonical `path::Symbol` citations, strengthened `- Cohesion rationale:` and execution contract, upgraded `## Spec / documentation sync`, and listed all Set `comphome` sibling carriers (recommendation strength: strong). |

### Decisions

- D-1: Delegate `agent_workflows/plans_archive.py::_offer_archive_commit` and `agent_workflows/research_archive.py::_offer_archive_commit` to `agent_workflows/cli.py::_offer_records_commit` rather than duplicating git-root partitioning logic across three files (recommendation strength: strong; eliminates ~90 lines of duplicated self-commit logic with zero new `Scope-Paths`).
- D-2: Key `agent_workflows/plan_readiness.py::review_staleness_index` results by `artifact_core.py::repo_relative_posix(abs_path, repo_root_path)` and cache by `(git_root, git_rel, st.st_mtime_ns)` so all four callers (`ipd_lint.py`, `status_set.py`, `attention.py`, `check_engine.py::check_review_stale`) share one consistent contract without touching `ipd_lint.py` or `status_set.py` (recommendation strength: very strong).
- D-3: Keep `agent_workflows/artifact_refs.py::post_relocation_citation_rewrite`'s returned path list contract unchanged for `status_set.py` (`mmuv3v`) while using `artifact_core.py::repo_relative_posix` for `rewrite_scope_path_citations` stdout and `Change` entries to satisfy `assert_valid_agent_record` (recommendation strength: strong).
- D-4: Retain `7eivm2` as a single `- Size assessment: exception` child IPD rather than splitting into additional Set `comphome` children (recommendation strength: strong; preserves cross-module key/path cohesion and avoids churning orchestrator `92ujfc`'s child table).
