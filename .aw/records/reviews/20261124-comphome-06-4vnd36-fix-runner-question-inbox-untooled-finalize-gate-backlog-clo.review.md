# Review: Fix runner question inbox untooled finalize gate backlog close companion review and AW_HOME lanes

- Subject-Id: 4vnd36
- Subject-Type: ipd
- Subject-Path: .aw/records/plans/pending/20261124-comphome-06-4vnd36-fix-runner-question-inbox-untooled-finalize-gate-backlog-clo.ipd.md
- Reviewed-At: 2026-11-25
- Reviewer: antigravity/Gemini 4 Neon (High)
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

Checked against `.aw/system/workflows/technical-writing/technical-writing.md` (all 12 requirements):

### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `E-01`..`E-04`, `Concern`, `Findings` | Single-paragraph items with headline summaries and informal symbol names | Numbered sub-steps with canonical `agent_workflows/<mod>.py::<Symbol>` citations, explicit isolated vs non-isolated contracts, and exact failure/preservation rules | Technical Writing Reqs 1, 2, 3, 5, 7 and Spec Section 11.1 citation form |
| `## Proposed changes (ordered, validatable)` | Five-line numbered list without diagrams | Added two Mermaid diagrams (task dependency graph and companion/`home` isolated-lane lifecycle flowchart) matching text terminology | Technical Writing Req 12 (5 modules and multi-branch routing/teardown lifecycle) |
| `## Deferred / out of scope`, `## Spec / documentation sync`, `## Approval and execution gate` | Uncarried `c8a130148` bullet, missing sibling carriers, bare `N/A`, abbreviated gate line | Added `- Carrier-Declined:` for `c8a130148`, listed all five Set `comphome` sibling carriers, substantiated spec/doc sync against `7ckptx`/`6kwd2e`/`25kzda`/`4sd62s`, and added complete execution contract | `steps/s7-finalize.md`, `steps/r7-cross-plan.md`, and `check.ipd-uncarried-obligation` |

### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|

### Step T

- Checked: plan metadata, `- Scope-Paths:` (10 paths across 5 core runner/lane modules and 4 test suites), 4 task groups, 5 `E-*`/`V-*` items, and Set `comphome` Order 06 position depending on `ywl7uc`, `mmuv3v`, and `7hfx7r`.
1. Yes: modifies runner gate enforcement, preflight answer durability, isolated-lane staging/routing/merge guards for `records_backend == "home"`, and `review_findings` lookup.
2. Yes: directly modifies worktree isolation, target-repo `.aw/records/**` merge guards, lane teardown preservation (`lane_containment.py`), runner commits (`runner_shared.py`), and finalize idempotence (`ipd_lifecycle.py`).
3. Yes: cross-cutting across 9 bug clusters in 5 core runner/lane modules (`- Size assessment: exception`), closing Set `comphome`.
4. Yes: `- Scope-Paths:` explicitly lists all 10 target files.
5. Yes: defects here can lose human preflight answers, let untooled `executed/` moves bypass finalize, leak `.aw/records/**` onto target `main`, mutate live companion records prematurely, or discard unrouted work during teardown.
AW-TIER: complex

### Step R1

- Checked: `agent_workflows/runner_shared.py` (`consume_answers`, `record_oq_answer`, `finalize_already_done`, `finalize_outcome`, `execute_item_core`, `lane_executed_carrier_override`, `process_backlog_close`, `commit_backlog_close`, `resolve_backlog_item`, `read_zero_work_evidence`, `turn_attempted_nothing`, `handle_review_orchestrator_readiness`, `_promote_reviewed_plan`, `perform_carrier_verification`, `reconcile_disposition`, `commit_review_shared_output`, `check_review_lane_artifacts`, `_companion_aware_eval_root`, `route_companion_lane_records`, `_collect_companion_lane_record_changes`, `integrate_lane_branch`, `_project_lane_artifact_path`, `_resolve_companion_context`, `_is_companion_records_context`), `agent_workflows/question_inbox.py` (`write_question`), `agent_workflows/review_findings.py` (`review_dirs`, `_cached_subject_review_files`), `agent_workflows/lane_containment.py` (`companion_staged_records_root`, `stage_companion_lane_artifact`, `resolve_companion_lane_path`, `driver_written_lane_paths`, `inventory_lane`), `agent_workflows/ipd_lifecycle.py` (`plan_already_finalized`, `_resolve_staged_companion_lane_plan`), and `agent_workflows/storage.py` (`_resolve_records_git_root`).
- Verified all 9 bug descriptions match live code, and identified critical under-specified interactions across `consume_answers`, `plan_already_finalized`, `process_backlog_close`, re-review demote (`overwrite=True`), the 12 `records_backend == "companion"` sites, and R5.5 teardown preservation -> `PR-001..PR-005`.

### Step R2

- Checked: E/V 1:1 bijection (`E-01..E-05` <-> `V-01..V-05`), `- Scope-Paths:` fence, `- Item-Dependencies: executed:7hfx7r, executed:mmuv3v, executed:ywl7uc`, evidence feasibility, runtime-demonstration reachability, uncarried-obligation check (`c8a130148` bullet), and execution-contract clauses.
- Fixed missing `- Carrier-Declined:` on the `c8a130148` deferred bullet and added full execution-contract clauses -> `PR-007`.

### Step R3

- Checked: fail-closed target-repo `.aw/records/**` merge guard (`integrate_lane_branch:9993-10006`), untooled `executed/` move refusal (`plan_already_finalized` + `execute_item_core`), R1 prompt purity for `home` lanes, R5.5 fail-toward-preservation during lane teardown, and live-companion non-mutation prior to integration.
- Found that blindly registering staged `.aw/records/**` as discardable in `driver_written_lane_paths` would violate R5.5 if routing failed or unrouted worker edits existed; constrained teardown discardability strictly to paths whose current SHA-256 matches `companion-staged-baseline.json` (plus the baseline file itself) -> `PR-005`.

### Step R4

- Checked: single-source-of-truth external-records predicate (`is_external_records_backend`) replacing 12 duplicated `records_backend == "companion"` checks, atomicity of isolated backlog closes and preflight answer writes, anti-regression preservation of `finidem` receipt-consumed idempotence and `commit_backlog_close` `None`-means-refused semantics, test coverage, right-sizing, and spec/doc sync.
- Expanded `## Required tests / validation`, `E-05`, and `V-01..V-05` from 4 test files to all 14 verified existing suites -> `PR-006`.

### Step R5

- Checked: QA/QC, testing/regression, UI/UX (clear refusal codes and non-loss of preflight answers), architect (single `is_external_records_backend` predicate and unified companion/`home` routing), software engineer (removing `overwrite=True` clobber on re-review demote and preventing target-branch `.aw/records/**` commits in `process_backlog_close` / `handle_review_orchestrator_readiness`), power user (non-isolated `--no-isolate-worktree` companion and unversioned `home` flows), novice (preserving existing work without silent answer rollbacks), and stakeholder (closing all 9 remaining Set `comphome` bugs cleanly).

### Step R6

- Checked: `IPD-Z603` advisory (5 `E-*` items, 10 `Scope-Paths`, 5 production modules) and conceptual density.
- Confirmed `- Size assessment: exception` is justified: all 5 modules share one external-records lane-staging, routing, baseline-accounting, and gate contract across `companion` and `home` backends, and keeping Order 06 unified avoids churning orchestrator `92ujfc`'s child table. Recorded as `D-4`.

### Step R7

- Checked: Set `comphome` orchestrator `92ujfc` and prerequisites `ywl7uc` (Order 01), `mmuv3v` (Order 03), and `7hfx7r` (Order 05).
- Verified `Item-Dependencies: executed:7hfx7r, executed:mmuv3v, executed:ywl7uc` matches `92ujfc` and accurately captures: `ywl7uc` (`AW_HOME` unification and `record_owner_root`), `mmuv3v` (`_resolve_staged_companion_lane_plan` in `ipd_lifecycle.py::finalize` and `offer_commit` containment), and `7hfx7r` (`check_status_untooled_range` and `_lane_carrier_is_executed` companion support).
- Listed all five Set `comphome` sibling carriers in `## Deferred / out of scope (with reason)`.

### Step S5

- Checked: all 7 findings (`PR-001..PR-007`) have Low or Medium Remediation Risk and were fixed directly from verified repository code and documented specs (`7ckptx`, `6kwd2e`, `25kzda`, `4sd62s`). Zero open questions or unfixed `HIGH`/`BLOCKER` findings remain; all 4 autonomous engineering decisions (`D-1..D-4`) are `Reversible: yes`.

### Pass 2

- Checked: re-read the entire revised IPD end-to-end (`Concern`, `Scope`, `E-01..E-05`, `Findings`, `Proposed changes` + both Mermaid diagrams, `Deferred / out of scope`, `Required tests / validation`, `Spec / documentation sync`, `V-01..V-05`, and `Approval and execution gate`). Verified exact 1:1 `E-*`/`V-*` bijection, all 14 validation test filenames verified on disk, zero em/en dashes, and valid `- Readiness: go-pending-approval` and `- Review-Depth: complex`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | High | in-scope | Correctness / Question Inbox | `agent_workflows/runner_shared.py::consume_answers:28477-28488,28553-28705`; `agent_workflows/question_inbox.py::write_question:379-427` | `E-01` left exact fallback precedence (`record_owner_root(run_dir)` before parent walk, plus `configured_file` fallback in `write_question`), external `rel_art_path` preservation (`art_p.resolve().as_posix()`), and the split between versioned `record_git_root` commits and unversioned `~/.aw/` non-rollback durability under-specified. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Specified all three sub-steps explicitly in `E-01` (recommendation strength: very strong). |
| PR-002 | High | in-scope | Correctness / Anti-Regression | `agent_workflows/ipd_lifecycle.py::plan_already_finalized:1588-1648`; `agent_workflows/runner_shared.py::finalize_already_done:38998-39048`, `execute_item_core:48620-48675` | `E-02` did not specify preserving `finidem` receipt-consumed idempotence (`read_receipt is None` -> `already=True`) alongside refusing unconsumed-receipt moves (`read_receipt is not None` -> `already=False`), nor extending `finalize_already_done`'s external-lane guard and `execute_item_core`'s staged-baseline move inspection to both `companion` and `home` lanes. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Specified exact `read_receipt` gating in `plan_already_finalized`, `home`-lane coverage in `finalize_already_done`, and staged-baseline `check.status-untooled` detection in `execute_item_core` in `E-02` (recommendation strength: very strong). |
| PR-003 | High | in-scope | Correctness / Backlog Close Isolation | `agent_workflows/runner_shared.py::lane_executed_carrier_override:18008-18057`, `process_backlog_close:54469-54685`, `commit_backlog_close:54331-54466` | In isolated companion/`home` lanes, `process_backlog_close` would mutate live external backlog files if `item_path` is not staged into the lane first, and calling `commit_backlog_close` on the target lane branch would trip the target `.aw/records/**` merge guard; in non-isolated unversioned `~/.aw/` mode, handling `record_git_root is None` must not weaken `commit_backlog_close`'s `None`-means-refused contract on versioned repos. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Specified in-lane staging + routing (skipping target-branch commit) for isolated external-records lanes and `record_git_root`-partitioned commits / unversioned-`home` handling for non-isolated closes in `E-03` (recommendation strength: very strong). |
| PR-004 | High | in-scope | Correctness / Companion Review & Carrier Helpers | `agent_workflows/runner_shared.py::read_zero_work_evidence:13116-13146`, `handle_review_orchestrator_readiness:33070-33210`, `_promote_reviewed_plan:44803-44854`, `execute_item_core:47980-48071`, `perform_carrier_verification:38339-38433`, `reconcile_disposition:45085-45106`, `commit_review_shared_output:4706-4793`, `check_review_lane_artifacts:9029-9175`, `integrate_lane_branch:10134-10152`; `agent_workflows/review_findings.py::review_dirs:326-367`, `_cached_subject_review_files:858-960` | `E-03` listed 9 helpers in one dense sentence without specifying concrete hazards: `handle_review_orchestrator_readiness` runs `git add`/`git commit` on target lane after demote; `execute_item_core:48068` passes `overwrite=True` after re-review demote (which would overwrite an in-lane demoted copy with untouched live companion bytes); `_promote_reviewed_plan` and `rereview` demote pass bare `id6` (mutating live companion); `read_zero_work_evidence` must preserve `bool` `dirty` for both `companion` and `home`; and `check_review_lane_artifacts` must overlay newly created lane carriers. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Expanded `E-03` into 5 explicit numbered sub-steps covering all 9 helpers with exact staged-lane contracts (recommendation strength: very strong). |
| PR-005 | High | in-scope | Architecture & Security Containment | `agent_workflows/lane_containment.py:608-789,3724-3768,3954-4035`; `agent_workflows/runner_shared.py:4650,4817,4943,5046,5171,9007-9027,9250-9268,9560-9845,9941-10007,13117,44738,44931,50732`; `agent_workflows/storage.py::_resolve_records_git_root:153-168` | `records_backend == "companion"` is duplicated across 12 sites; additionally, unconditionally marking staged `.aw/records/**` as driver-written in `driver_written_lane_paths` would violate spec `7ckptx` R5.5 by discarding unrouted worker edits on teardown, and `clean-delta` lanes also leave `.aw/state/companion-staged-baseline.json` untracked. | C:Medium; U:Low; S:Medium; F:Medium; Overall:Medium | fixed | Specified one shared `is_external_records_backend(ctx)` predicate across all 12 sites, verified `storage._resolve_records_git_root` handles unversioned and local-git `home`, and restricted teardown discardability in `E-04` strictly to `COMPANION_STAGED_BASELINE_REL` plus baseline-listed `.aw/records/**` paths whose current SHA-256 matches the baseline (recommendation strength: very strong). |
| PR-006 | Medium | in-scope | Testing / Validation | `.aw/records/plans/pending/20261124-comphome-06-4vnd36-fix-runner-question-inbox-untooled-finalize-gate-backlog-clo.ipd.md` (`E-05`, `## Required tests / validation`, `V-01..V-05`) | Validation only ran 4 test files and omitted 10 existing regression suites directly pinning `consume_answers`, `plan_already_finalized`, `finalize_already_done`, `process_backlog_close`, `reconcile_disposition`, `commit_review_shared_output`, `perform_carrier_verification`, `review_findings`, and `clean-delta` control state. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Expanded `## Required tests / validation`, `E-05`, and `V-01..V-05` to all 14 verified existing suites and mapped per-file positive and negative behavioral cases (recommendation strength: strong). |
| PR-007 | Medium | in-scope | Structure / Prose / Diagrams / Carriers | `.aw/records/plans/pending/20261124-comphome-06-4vnd36-fix-runner-question-inbox-untooled-finalize-gate-backlog-clo.ipd.md` | Plan lacked Mermaid diagrams (Technical Writing Req 12), left the `c8a130148` bullet in `## Deferred / out of scope` without a `- Carrier-*:` tag, omitted the five Set `comphome` sibling carriers, used a bare `N/A` in `## Spec / documentation sync`, and lacked the required execution-contract clauses in `## Approval and execution gate`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Added two Mermaid diagrams, added `- Carrier-Declined:` for `c8a130148` and all five Set `comphome` sibling carriers, substantiated spec/doc sync, and added the complete execution contract (recommendation strength: strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `ipd_lifecycle.py::plan_already_finalized` distinguish a legitimate already-finalized plan from an untooled hand move into `executed/`? | Check `read_receipt(repo_root, plan_id)` when `bucket == "executed"`: return `already=False` whenever an unconsumed begin receipt still sits on disk, while preserving `already=True` when the receipt was consumed. | Require a reachable `lifecycle(<id6>): finalize` commit in every checkout (rejected: breaks `ipd_lifecycle.py:1609-1615` where a legitimate finalize commit lives on an unmerged lane branch). | `agent_workflows/ipd_lifecycle.py::plan_already_finalized:1588-1648`; `tests/test_finidem_reusable_not_finalized.py` | yes |
| D-2 | How should `lane_containment.py` and `runner_shared.py` generalize isolated-lane external-records handling to `records_backend == "home"` without breaking existing callers? | Introduce one shared `is_external_records_backend(ctx)` predicate (`records_backend in ("companion", "home")` or `git_policies.get("records") == "companion-git"`) and route all 12 sites through it while keeping existing `companion_*` helper names backwards-compatible. | Rename all `companion_*` public helpers to `external_*` (rejected: would churn external callers and existing tests unnecessarily) or duplicate `"home"` branches per site (rejected: violates `GUIDING_PRINCIPLES.md` P8). | `agent_workflows/lane_containment.py:608-789`; `agent_workflows/runner_shared.py:9260-9268`; `agent_workflows/storage.py::_resolve_records_git_root:153-168`; `GUIDING_PRINCIPLES.md` P8 | yes |
| D-3 | How should `lane_containment.py::driver_written_lane_paths` / `inventory_lane` classify staged `.aw/records/**` paths during teardown on un-upgraded companion and `clean-delta` repos? | Account for `COMPANION_STAGED_BASELINE_REL` plus each `.aw/records/<rel>` entry in `read_companion_staged_baseline(lane_root)` ONLY when its current on-disk SHA-256 matches the baseline digest; leave modified-unrouted or newly-created unrouted files as `unknown_untracked`. | Unconditionally discard all `.aw/records/**` in external-records lanes (rejected: violates spec `7ckptx` R5.5 fail-toward-preservation if routing fails or is skipped). | `agent_workflows/lane_containment.py::driver_written_lane_paths:3724-3768`, `inventory_lane:3954-4035`; `agent_workflows/runner_shared.py::route_companion_lane_records:9690-9700` | yes |
| D-4 | Should `4vnd36` stay a single `- Size assessment: exception` Order 06 child IPD in Set `comphome` or split further? | Retain `4vnd36` as Order 06 with `- Size assessment: exception` and strengthened `- Cohesion rationale:`. | Split `question_inbox`/`ipd_lifecycle` from `home` lane containment (rejected: all 5 modules share one external-records lane contract and splitting would churn orchestrator `92ujfc`'s child table). | `.aw/records/plans/pending/20261124-comphome-00-92ujfc-coordinate-companion-repo-and-aw-home-bug-fixes.ipd.md` | yes |
