# Review: Fix pre-commit hooks staged gates runners monitor run viewer checkup and clean-delta inbox

- Subject-Id: 7hfx7r
- Subject-Type: ipd
- Subject-Path: .aw/records/plans/pending/20261124-comphome-05-7hfx7r-fix-pre-commit-hooks-staged-gates-runners-monitor-run-viewer.ipd.md
- Reviewed-At: 2026-11-25
- Reviewer: antigravity/Gemini 4 Neon (High)
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

Checked against `.aw/system/workflows/technical-writing/technical-writing.md` (all 12 requirements):

### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `E-01`..`E-04`, `Concern`, `Findings` | Semicolon-chained paragraphs with informal module/symbol references | Numbered sub-steps with canonical `agent_workflows/<mod>.py::<Symbol>` citations and explicit conditions/fallbacks | Technical Writing Reqs 1, 2, 3, 5, 7 and Spec Section 11.1 citation form |
| `## Proposed changes (ordered, validatable)` | Linear list with no visual overview | Added two Mermaid diagrams (task dependency graph and layout routing flowchart) using exact text terms | Technical Writing Req 12 (3+ components and multi-branch routing) |
| `## Deferred / out of scope`, `## Spec / documentation sync`, `## Approval and execution gate` | Single sibling listed, bare `N/A`, abbreviated gate line | Listed all five Set `comphome` sibling carriers, substantiated spec/doc sync against `4sd62s`/`25kzda`/`docs/cli-output-contract.md`, and added full execution contract | `steps/s7-finalize.md` and `steps/r7-cross-plan.md` completeness |

### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|

### Step T

- Checked: plan metadata, `- Scope-Paths:` (13 paths across 10 production modules and 2 test suites), 4 task groups, 6 `E-*`/`V-*` items, and Set `comphome` membership.
1. Yes: changes pre-commit hook enforcement, `aw check` staged governance behavior, `aw runners`/`aw runs` discovery, and `clean-delta` inbox/workflow-artifacts locations (`<AW_HOME>/projects/<pid>/inbox` and `workflow-artifacts`).
2. Yes: modifies commit-gating pre-commit hooks (`executed_transition_gate.py`, `meta_log_append_gate.py`, `ipd_dependency_statement_gate.py`), staged commit invariant rules (`check_engine.py`), and single-directory inbox containment (`artifact_adopt.py`).
3. Yes: cross-cutting across 10 production modules in 4 task groups with `- Size assessment: exception` inside a 6-child Set (`comphome`).
4. Yes: `- Scope-Paths:` explicitly lists all 13 target files (10 production modules, 2 test files, and the plan itself).
5. Yes: an error in pre-commit hooks or staged `check_engine` rules can either fail open on corrupt transitions or block legitimate commits/handoffs, and misrouting `clean-delta` inbox or `set_records` breaks zero-footprint containment.
AW-TIER: complex

### Step R1

- Checked: `agent_workflows/hooks/executed_transition_gate.py`, `agent_workflows/hooks/meta_log_append_gate.py`, `agent_workflows/hooks/ipd_dependency_statement_gate.py`, `agent_workflows/hooks/status_untooled_gate.py`, `agent_workflows/hooks/backlog_blocking_close_gate.py`, `agent_workflows/hooks/precommit_scope_gate.py`, `agent_workflows/check_engine.py`, `agent_workflows/project_context.py`, `agent_workflows/storage.py`, `agent_workflows/ipd_lifecycle.py`, `agent_workflows/artifact_meta.py`, `agent_workflows/runners_monitor.py`, `agent_workflows/run_viewer.py`, `agent_workflows/checkup.py`, `agent_workflows/set_records.py`, `agent_workflows/artifact_adopt.py`, `agent_workflows/attention.py`, `agent_workflows/runner_shared.py`, `agent_workflows/run_cli.py`, and `agent_workflows/pwatch.py`.
- Found broken `record_owner_root(root)` premise in `E-01` (`project_context.py::record_owner_root:1603-1609` returns `None` when `"records"` is absent from path parts) -> `PR-001`.
- Found missed `_is_plan_ipd_path`, `_plan_lifecycle_bucket`, `check_release_gate_consistency`, `check_commit_invariants`, and `_candidate_state_durable_dirs` sites -> `PR-002`.
- Found git-ref asymmetry in `check_status_untooled_range` (`runner_shared.py:48630` passes `target_repo` lane SHAs) and `_lane_carrier_is_executed` -> `PR-003`.

### Step R2

- Checked: E/V 1:1 bijection (`E-01..E-06` <-> `V-01..V-06`), `- Scope-Paths:` fence, `- Item-Dependencies: executed:ywl7uc`, evidence feasibility, runtime-demonstration reachability, and execution-contract clauses.
- Verified that fixing `check_engine.py` and `executed_transition_gate.py` repairs `status_untooled_gate.py`, `backlog_blocking_close_gate.py`, and `precommit_scope_gate.py` without editing those wrapper files or widening `- Scope-Paths:`.
- Upgraded `## Approval and execution gate` with explicit approval, non-stopping scope-fence justification, hard-MUST output-pasting, path-scoped commit, and conditional runner vs standalone finalize ownership -> `PR-007`.

### Step R3

- Checked: fail-closed pre-commit gates, `m0001` migration marker validation, `clean-delta` zero-footprint containment, single-directory inbox containment (`artifact_adopt.py::plan_adoption`), symlink escape resistance (`source.resolve().relative_to(inbox)`), zero-file-open untrusted drop safety (`attention.py::inbox_waiting`), and leak-free output labels (`<project home>/inbox` instead of raw `~/.aw/` paths).
- Verified `tests/test_attention.py::InboxWaitingCountTests.test_counts_without_opening_any_file:3795-3816` would fail if `inbox_waiting` unconditionally opened config files via `resolve_project_context` -> `PR-004`.

### Step R4

- Checked: correctness, atomicity/isolation, single-source-of-truth helpers (`_staged_meta_layout`, `resolve_inbox_dir`), anti-regression invariants, test suites, right-sizing/conceptual density, and spec/doc sync.
- Expanded `## Required tests / validation`, `E-05`, `E-06`, and `V-01..V-06` from 2 test files to all 18 relevant behavioral/regression suites -> `PR-006`.
- Added missing edge cases for `runners_monitor` invoked directly on a companion repo, `run_viewer` worktree/error handling and legacy `.agents/` fallback, and `checkup.run_start_checkup` `run_id` fallback -> `PR-005`.

### Step R5

- Checked: QA/QC, testing/regression, UI/UX (footer label `<project home>/inbox/` in `clean-delta`), architect (shared `_staged_meta_layout` and `resolve_inbox_dir` single sources of truth), software engineer (git toplevel normalization and git-ref ownership checks), power user (running hooks/monitors from companion repos and worktrees), novice (clear refusal messages naming actual inbox label), and stakeholder (complete remediation of all 8 verified `/assess-bugs` defects).

### Step R6

- Checked: `IPD-Z603` advisories (6 `E-*` items, 13 `Scope-Paths`, 10 production modules) and conceptual density per E-item.
- Confirmed `- Size assessment: exception` is justified: `E-01` and `E-02` are tightly coupled through `check_engine.py` and the companion pre-commit hooks, while `E-03` and `E-04` are small directory-resolution fixes sharing the same companion/`clean-delta` helpers; keeping Order 05 unified preserves Set `comphome` (`92ujfc`) and `4vnd36`'s `executed:7hfx7r` dependency cleanly. Recorded as `D-4`.

### Step R7

- Checked: Set `comphome` orchestrator `92ujfc`, predecessor `ywl7uc` (Order 01), sibling `7eivm2` (Order 04, which also touches `check_engine.py`, `attention.py`, and `tests/test_companion_doctor_and_carriers.py`), and successor `4vnd36` (Order 06, depending on `executed:7hfx7r`).
- Verified `ywl7uc` `E-02` (`Preset.LOCAL_ONLY` -> `DeliveryMode.CLEAN_DELTA`) is honored by `E-04` (`set_records.py::run_artifacts_dir` and `artifact_adopt.py::resolve_inbox_dir`).
- Verified `7eivm2`'s edits to `check_engine.py` (`stale_record_scope_paths`, `resolve_gate_ref`, `graduated_closable_warnings`, `check_review_stale`) and `attention.py` (`scan`, `_order_primary`, selector/warning filters) are disjoint from `7hfx7r`'s edits (`_git_read_at_context`, staged/range gates, `_lane_carrier_is_executed`, `inbox_waiting`).
- Verified `4vnd36` `E-02` cleanly owns the runner-side unstaged companion-lane `executed/` move check in `runner_shared.py::execute_item_core`, complementing `7hfx7r` `E-02`'s commit-range check.

### Step S5

- Checked: all 7 findings (`PR-001..PR-007`) have Low or Medium Remediation Risk and were fixed directly from verified repository code and documented contracts. Zero open questions or unfixed `HIGH`/`BLOCKER` findings remain; all 4 autonomous engineering decisions (`D-1..D-4`) are `Reversible: yes`.

### Pass 2

- Checked: re-read the entire revised IPD end-to-end after all edits (`Concern`, `Scope`, `E-01..E-06`, `Findings`, `Proposed changes` + both Mermaid diagrams, `Deferred / out of scope`, `Required tests / validation`, `Spec / documentation sync`, `V-01..V-06`, and `Approval and execution gate`). Verified zero stale wording from superseded premises (no bare `record_owner_root(root)` left anywhere), exact 1:1 `E-*`/`V-*` bijection, zero em/en dashes, and valid `- Readiness: go-pending-approval` and `- Review-Depth: complex`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | High | in-scope | References / Companion Owner | `agent_workflows/project_context.py::record_owner_root:1603-1609`; `agent_workflows/check_engine.py::_git_read_at_context:3537-3576`; `agent_workflows/hooks/executed_transition_gate.py:390-411`; `agent_workflows/hooks/ipd_dependency_statement_gate.py:98-108` | `E-01` proposed calling `record_owner_root(root) or root` on a companion repo root `root`, but `record_owner_root` Branch B requires a `"records"` component in path parts and always returns `None` for bare `root`; `ipd_dependency_statement_gate.py::check` also omitted git toplevel normalization. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Revised `E-01` to pass `root / "records"` (or a staged plan path) to `record_owner_root`, detect companion layout before `resolve_project_context(target_repo=str(root))` in `_git_read_at_context` (with standalone `load_companion_identity` fallback), and normalize git toplevel in `ipd_dependency_statement_gate.py::check` (recommendation strength: very strong). |
| PR-002 | High | in-scope | Correctness / Hook Completeness | `agent_workflows/check_engine.py::_is_plan_ipd_path:3500-3503`, `_plan_lifecycle_bucket:3527-3535`, `check_release_gate_consistency:7956-7987`, `check_commit_invariants:5160-5208`; `agent_workflows/hooks/executed_transition_gate.py:73,97-100,524-563` | `_is_plan_ipd_path` and `_plan_lifecycle_bucket` hardcode `.aw/records/plans/` (causing `_check_untooled_plan_transition` to skip companion/home paths); `check_release_gate_consistency` and `check_commit_invariants` passed `companion_dir` to `evaluate_blocking_close`/`check_scope_drift` instead of `owner_root`; `executed_transition_gate.py` missed `_candidate_state_durable_dirs` `owner_root` lookup for `m0001` markers and needed `root`-scoped index inspection so target code commits are not blocked by unrelated staged companion files. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Added explicit fixes for all missed sites in `E-01` and `E-02`, and delegated `meta_log_append_gate.py::_staged_meta_logs` to `check_engine.py::_staged_meta_layout` (recommendation strength: very strong). |
| PR-003 | High | in-scope | Correctness / Git-Ref Asymmetry | `agent_workflows/check_engine.py::check_status_untooled_range:3844-3914`, `_lane_carrier_is_executed:6875-6941`; `agent_workflows/runner_shared.py:48630,54533-54607` | Unconditionally redirecting `check_status_untooled_range` and `_lane_carrier_is_executed` to `record_git_root(records_root)` fails with `fatal: bad revision` when `runner_shared.py` passes `target_repo` lane-branch SHAs or refs that live in `target_repo` rather than the companion repo, and `read_at` must bind to the same repo where the ref resolved. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Updated `E-02` to verify which git repo (`repo_root` vs `record_git_root`) owns `base`/`head` or `ref` via `git rev-parse --verify` and bind both git commands and `read_at` context to that matching repo (recommendation strength: very strong). |
| PR-004 | High | in-scope | Anti-Regression / Security Containment | `agent_workflows/attention.py::inbox_waiting:2844-2890,5518-5523`; `tests/test_attention.py:3795-3816`; `agent_workflows/artifact_adopt.py:64,740-755,1043`; `agent_workflows/set_records.py::run_artifacts_dir:46-48` | Unconditionally calling `resolve_project_context` inside `attention.py::inbox_waiting` opens JSON config files and breaks `tests/test_attention.py::InboxWaitingCountTests.test_counts_without_opening_any_file`; `attention.py:5522` and `artifact_adopt.py` hardcoded `.aw/inbox` display labels; and `set_records.py::run_artifacts_dir` routing under `clean-delta` (including `local-only` from `ywl7uc`) was under-specified. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Specified one shared `artifact_adopt.py::resolve_inbox_dir` helper with a zero-file-open fast path for non-git and tracked `.aw/config/project.json` repos, leak-free `<project home>/inbox` labeling for `clean-delta`, strict containment assertions, and explicit `clean_delta_control_root`/`delivery_mode` routing in `set_records.py::run_artifacts_dir` in `E-04` (recommendation strength: very strong). |
| PR-005 | Medium | in-scope | Edge Cases / Completeness | `agent_workflows/runners_monitor.py::find_active_runners:101-141`; `agent_workflows/run_viewer.py::_find_stem_for_id6:537-551`, `discover_runs_in_directory:1640-1691`; `agent_workflows/checkup.py::run_start_checkup:684-694` | `E-03`/`E-04` omitted companion-root `--repo` fallback in `find_active_runners`, `runs_repo_root` + exception guard in `discover_runs_in_directory`, legacy `.agents/` fallback and `executed/*` shards in `_find_stem_for_id6`, and exact replacement of `.aw/runs/` with `state_root(runs_repo_root(repo_path))` in `checkup.run_start_checkup`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Added all edge-case specifications to `E-03` and `E-04` (recommendation strength: strong). |
| PR-006 | Medium | in-scope | Testing / Validation | `.aw/records/plans/pending/20261124-comphome-05-7hfx7r-fix-pre-commit-hooks-staged-gates-runners-monitor-run-viewer.ipd.md` (`E-05`, `E-06`, `## Required tests / validation`, `V-06`) | Validation only ran 2 companion/home test files and omitted the 16 existing regression suites pinning the 10 modified production modules; `E-05` omitted negative containment, companion-handoff, `home` local-git prefix, and dual-repo ref cases. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Expanded `## Required tests / validation`, `E-05`, `E-06`, and `V-01..V-06` to cover all 18 pytest suites and concrete positive/negative behavioral assertions (recommendation strength: strong). |
| PR-007 | Medium | in-scope | Structure / Prose / Diagrams | `.aw/records/plans/pending/20261124-comphome-05-7hfx7r-fix-pre-commit-hooks-staged-gates-runners-monitor-run-viewer.ipd.md` | Plan lacked Mermaid diagrams (Technical Writing Req 12), used dense semicolon-chained `E-*` text with informal symbol names, lacked full execution-contract clauses in `## Approval and execution gate`, listed only `4vnd36` in `## Deferred / out of scope`, and used a bare `N/A` in `## Spec / documentation sync`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Added two Mermaid diagrams, structured numbered sub-steps with canonical `path::Symbol` citations, added the full execution contract, substantiated spec/doc sync, and listed all five Set `comphome` sibling carriers (recommendation strength: strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should `executed_transition_gate.check(root)` inspect `root`'s own git index or redirect to `record_git_root(records_root)` when called on a target repo with companion records? | Inspect `root`'s own git index (deriving `plans_prefix` from `root`'s layout: `records/plans/` for companion, `plans/` for `home` local-git, `.aw/records/plans/` for target), while reading finalize journals and `m0001` markers from `owner_root = record_owner_root(root / "records") or root`. | Redirect `git diff --cached` from `target_repo` to `companion_dir` (rejected: would block unrelated code commits in `target_repo` whenever `companion_dir` has staged work). | `agent_workflows/hooks/executed_transition_gate.py:173-178,399`; `agent_workflows/project_context.py::record_owner_root:1603-1609` | yes |
| D-2 | Where should the shared `clean-delta`-aware inbox resolver live so `artifact_adopt.py` and `attention.py` share one source of truth without widening `- Scope-Paths:`? | Place `resolve_inbox_dir(repo_root)` in `agent_workflows/artifact_adopt.py` with a zero-file-open fast path for non-git dirs and tracked `.aw/config/project.json` repos, and import it from `agent_workflows/attention.py::inbox_waiting` and the footer formatter. | Add a helper to `agent_workflows/project_context.py` (rejected: `project_context.py` is owned by `ywl7uc` and outside `7hfx7r`'s `Scope-Paths`) or duplicate resolution in `attention.py` (rejected: violates `GUIDING_PRINCIPLES.md` P8). | `tests/test_attention.py:3795-3816`; `agent_workflows/artifact_adopt.py:64,740`; `GUIDING_PRINCIPLES.md` P8 | yes |
| D-3 | What user-facing display label should `attention.py` and `artifact_adopt.py` emit for the `clean-delta` inbox directory? | Emit `<project home>/inbox` (rendered as `` `<project home>/inbox/` `` in `attention.py`'s footer), preserving `.aw/inbox` byte-identically for tracked repositories. | Print the raw `~/.aw/projects/<pid>/inbox` absolute path (rejected: leaks machine-local home paths into output, violating `docs/cli-output-contract.md` and `aw sanitize`). | `agent_workflows/checkup.py:920`; `docs/cli-output-contract.md`; `tests/test_attention.py:3891` | yes |
| D-4 | Should `7hfx7r` stay a single `- Size assessment: exception` child IPD in Set `comphome` or split into two children? | Retain `7hfx7r` as Order 05 with `- Size assessment: exception` and strengthened `- Cohesion rationale:`. | Split hooks/`check_engine` from `runners_monitor`/`run_viewer`/`checkup`/`set_records`/`adopt` (rejected: all are small bounded fixes in an already-decomposed 6-child Set and splitting would churn orchestrator `92ujfc` and `4vnd36`'s `Item-Dependencies`). | `.aw/records/plans/pending/20261124-comphome-00-92ujfc-coordinate-companion-repo-and-aw-home-bug-fixes.ipd.md`; `.aw/records/plans/pending/20261124-comphome-06-4vnd36-fix-runner-question-inbox-untooled-finalize-gate-backlog-clo.ipd.md` | yes |
