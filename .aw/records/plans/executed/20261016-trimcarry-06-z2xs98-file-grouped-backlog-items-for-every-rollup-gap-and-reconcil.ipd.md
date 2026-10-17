# IPD: File grouped backlog items for every rollup gap and reconcile the 770 outcomes

- Date: 2026-10-16
- Kind: child
- Concern: Orders 01 to 05 measure and settle the 770 carrier-needed outcomes rolled into backlog `9qvfie` (1 `unprovable` + 764 `triaged-not-mutated` + 1 `replay-env-limited` + 4 `recreated` files with missing names), but a measurement in a findings doc is invisible to `aw attention` (`AGENTS.md` "What needs attention": "Do NOT keep committed backlog only in prose"). Every outcome the Set leaves unguarded needs a tracked carrier, and the Set needs one place that proves no outcome was dropped.
- Scope: IN: group every remaining gap (`unguarded`, `unguarded-unreached`, `unprovable`, `property-unidentifiable`, `budget-exhausted` keys; `exclusive-now` and `replay-unverified` pass-shared files; `gap` and `regression` recreated names; `PROP-02` when Order 01 did not end `guarded`; any suspected regression Order 02 recorded) by (production module, remedy shape); dedupe each group against live items; file one backlog item per group with `aw backlog new` (cap 15 groups, the rest in ONE residual rollup item naming them); write `## Filing plan`, `## Filed items` and `## Reconciliation` in the Set's findings doc; run the whole-Set checks. OUT: writing replacement tests or fixing regressions (each filed item's own work); changing backlog `9qvfie`'s status (the runner sets `graduated`; closing it `done` follows from this Set executing).
- Scope-Paths: .aw/records/backlog/, .aw/records/research/*-trimcarry-01-*.findings.md
- Item-Dependencies: executed:24h56i, executed:x9z0ve, executed:8dyt88, executed:we3kkb, executed:rf1xxr
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qvfie
- Set: trimcarry
- Order: 6
- Highest E allocated: 04
- Author: opencode
- Id: z2xs98

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: z2xs98 verified (set trimcarry, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set trimcarry graduating backlog 9qvfie.

## Goal

Leave every one of the 770 rollup outcomes either closed by evidence in this Set or carried by a specific, live backlog item, and prove it with a reconciliation that sums to 770.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Group and dedupe

- [x] E-01 Capture the per-rule counts of `aw check --agent` into the gitignored `.aw/state/trimcarry-z2xs98/check-before.jsonl` (E-04 compares against it). Collect the gaps: from the Set doc, keys with final verdict `unguarded`, `unguarded-unreached`, `unprovable`, `property-unidentifiable` or `budget-exhausted` (`## Rollup mutation results`), files `exclusive-now` or `replay-unverified` (`## Pass-shared re-diff`; `8dyt88` E-04 requires a `replay-unverified` file to be carried exactly like `exclusive-now`), and names `gap` or `regression` (`## Recreated missing names`); from the executed plans, `PROP-02` when Order 01's (`24h56i`) V-03 final verdict is not `guarded`, and every suspected regression recorded in Order 02's (`x9z0ve`) V-02. Everything else is CARRIER-FREE and is not grouped: keys `pin-retired`, `key-gone`, `guarded`; pass-shared `shared-confirmed`; recreated names `deliberately-removed`, `moved`, `retired-pin`, `intended-change`, `covered-by-shared-reach`. All `budget-exhausted` keys form ONE group of their own (remedy shape `probe then restore`, as `rf1xxr` `## Deferred` declares), not per-module groups. Group by (production module stem, remedy shape: `restore behavioral coverage` or `fix regression`). For each group, search live work with `grep -rslnwF -e <module stem> -e <deleted test basename> .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending` (`-s` because a status directory with no items, such as `blocked/` at review, does not exist and plain grep then exits 2), excluding the Set's own `9qvfie` and `trimcarry` plans from the hits, run the group's `aw backlog new ...` WITHOUT `--apply` to read its duplicate-candidate report, open every hit, and record `owned-confirmed` / `owned-rejected` (`aw find backlog` is not a text search: `xmr5qj` F-05). Write `## Filing plan`: one row per group with module, keys or names covered, counts, remedy shape, dedupe judgement, Work-Kind and Priority with a one-sentence justification, and `filed` / `owned` / `rolled-up`.
  - Depends on: none
  - Expected outcome: every gap is in exactly one group; every carrier-free item is named with its class; every group has a dedupe judgement.
  - Execution state: performed

### Task group 2: File

- [x] E-02 File each non-owned group, regressions first then by covered exclusive lines, up to 15 (a `regression` group is NEVER rolled up into the residual: each is filed as its own `bug` even past the cap, because the residual is a `chore` and cannot carry the release gate), with `aw backlog new --summary "<...>" --set trimgap --priority <low|medium|high> --work-kind <chore|bug> [--blocks-release next] --body "<keys or test names covered, reach class and verdict, Set doc id6 and section, deleted test files to mine>" --apply`, pasting each output. Work-Kind: `chore` for an absent test (no user-visible wrong behavior observed, the `xmr5qj` precedent); `bug` with `--blocks-release next` for a `regression`, because a live bug must carry the gate (`AGENTS.md` "Every live bug gates the next release"; `next` resolves to the single `planned` release, `f33nrj` 2.0.0 at authoring). If more than 15 non-regression groups remain, file ONE residual `chore` item listing the remaining groups by module with counts and the Set doc section that enumerates them. `aw backlog new` only writes files (it does not commit), so all filed paths are committed together in E-04. Record each filed id6 and path in `## Filed items`.
  - Depends on: E-01
  - Expected outcome: one item per filed group (at most 15 non-regression groups, plus every regression group) plus at most one residual item; every `regression` item carries `- Blocks-Release: next`.
  - Execution state: performed

### Task group 3: Reconcile

- [x] E-03 Write `## Reconciliation` with (a) the 770-outcome table: one row per backlog `9qvfie` outcome class with its count and where it ended: `PROP-02` (1) -> Order 01 (`24h56i`) verdict; `tests/test_run_evidence_completion.py` (1) -> restored by Order 02 (`x9z0ve`); 747 keys -> per-verdict counts from `## Rollup mutation totals`, each non-carrier-free count mapped to a filed id6, an `owned-confirmed` id6, or carrier-free (`pin-retired`, `key-gone`, `guarded`); 17 pass-shared files -> `shared-confirmed` (declined with the partition reason, flagged `Human review requested` in the row) or a filed id6 (`exclusive-now`, `replay-unverified`); 4 recreated files -> per-class name counts from `## Recreated missing names`, each `gap`/`regression` count mapped to an id6 and every other class marked carrier-free. A `PROP-02` row that is not `guarded`, and each Order 02 suspected regression, names its filed id6. The table total MUST equal 770 (1 + 764 + 1 + 4). (b) A check that every id6 named resolves: `aw find backlog <id6>` for each. (c) The Set's own code and test footprint: `git log --name-only --format= -E --grep '(24h56i|x9z0ve|8dyt88|we3kkb|rf1xxr|z2xs98)' -- agent_workflows tests tools | sort -u` lists only `tests/test_benchmark_runners_reports.py` and `tests/test_run_evidence_completion.py`.
  - Depends on: E-02
  - Expected outcome: reconciliation total 770; every id6 resolves; footprint is exactly the two restored modules.
  - Execution state: performed

- [x] E-04 Run `aw check --agent`, compare its per-rule counts with `check-before.jsonl`, and explain any NEW finding that names a file this plan wrote (fix it with the owning `aw backlog` or `aw research` verb). Run `aw research index`, then commit exactly the files this plan wrote: `aw commit <this plan> -- <each filed backlog path> <Set doc path>`.
  - Depends on: E-03
  - Expected outcome: no new `aw check` finding on this plan's files; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Committed backlog is created with `aw backlog new` (requires `--priority`; `--work-kind` or its alias `--kind`; `--set`, `--body`, `--blocks-release`), never hand-written; `--set trimgap` clusters the filed items (authoring dry run: would write `.aw/records/backlog/open/20261016-trimgap-01-<id6>-<slug>.backlog.md`).
- Grouping, dedupe method, the 10-plus-rollup cap pattern and the `chore` default for an absent test follow executed plan `xmr5qj` (E-01, E-02); the cap is 15 here because the population is larger (747 keys across about 100 modules at authoring).
- A live `bug` must carry `- Blocks-Release:`; the only `planned` release record is `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md`.
- The research index is gitignored, so only the doc and the backlog files are committed.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | The rollup holds 770 outcomes: 1 + 764 + 1 + 4. | Backlog `9qvfie` body; `hpjj44` `## Reconciliation` (d) carrier table rows assigned to `9qvfie`. |
| F2 | The 747 keys span about 100 production modules; the largest are `run_analytics_telemetry.py` (47), `migration_complex.py` (40), `compat_migration.py` (36), `migration_inventory.py` (31), `run_analytics_taxonomy.py` (29). | Authoring count over `hpjj44` `## Triaged not mutated`. |
| F3 | The earlier filing found no regression and filed `chore`. | `hpjj44` `## Filed items`: "No group was filed as `bug` because `PROP-01` represents an absent behavioral test without observed regression". |
| F4 | Review checks at HEAD `1d1701d21`: `aw backlog new --summary ... --set trimgap --priority low --work-kind chore` (preview) would write `.aw/records/backlog/open/20261016-trimgap-01-<id6>-<slug>.backlog.md` and prints a duplicate-candidate report; `--work-kind bug --blocks-release next` previews cleanly; `aw backlog new` has no commit option; `.aw/records/backlog/blocked/` does not exist (grep exit 2 without `-s`); `aw check --agent` currently reports 75 findings (3 error, 1 warning, 71 info), so E-04's before/after comparison, not a clean exit, is the right bar; `9qvfie` is `graduated` and carries no `- Blocks-Release:`. | Review lane. |
| F5 | Upstream classes this plan must carry that its first draft did not list: `replay-unverified` pass-shared files (`8dyt88` E-04 and its review cross-plan note), `property-unidentifiable` keys (carrier-needed per `hpjj44` `## Reconciliation` (d)), and a non-`guarded` `PROP-02` (`24h56i` E-03 records `unprovable` as a possible outcome). | Sibling plans as cited. |

## Proposed changes (ordered, validatable)

1. Group and dedupe (E-01).
2. File groups and at most one residual item (E-02).
3. 770-outcome reconciliation and footprint check (E-03).
4. `aw check` comparison, index, commit (E-04).

## Deferred / out of scope (with reason)

- Writing replacement tests or fixing regressions: each filed item's own work.
  - Carrier-Declined: deliberate non-goal; each gap is carried by the item E-02 files for it.
- Setting backlog `9qvfie` to `done`: done follows from the Set's carriers executing, and the close-legitimacy rule applies at that time.
  - Carrier-Declined: outside this plan's authority per the production contract for `9qvfie`.

## Scope check

- Over-scope: none.
- Under-scope: none; E-03 accounts for all 770 outcomes.

## Required tests / validation

No tests are authored. Validity: the reconciliation totals 770 (V-03), every named id6 resolves (V-03), and `aw check` shows no new finding on this plan's files (V-04).

## Spec / documentation sync

N/A: backlog and research records only.

## Open questions

### OQ-01: Should a `shared-confirmed` pass-shared file be filed anyway?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. It reaches no line a surviving test does not reach, which is the partition `hpjj44` used; filing it would carry a gap that the measurement says is not there. The row is flagged for human review so the maintainer can overrule it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `## Filing plan` table; pasted output of a `python3 -c` check that every item of the three source sections is either in exactly one group or named carrier-free with its class (counts shown per section: 747 keys, 17 files, E-01-of-`we3kkb` name count), plus the `PROP-02` and Order 02 inputs with their source lines; for each group, the pasted grep hit list and the dry-run duplicate report line.
  - Observed evidence:
    Filing plan table:
    ```markdown
Grouped filing plan for every remaining gap from the uncited trim-deleted test audit rollup (Set `trimcarry`, Order 06 `z2xs98`). Groups are ranked with regressions first (0 regressions observed), then by covered exclusive line count descending. The top 15 groups are filed individually under `--set trimgap`; all remaining groups (ranks 16 through 60) are rolled into a single residual rollup backlog item.

| Group | Module | Keys or Names Covered | Counts | Exclusive Lines | Remedy Shape | Dedupe Judgement | Work-Kind | Priority | Justification | Action |
|---|---|---|---|---:|---|---|---|---|---|---|
| 1 | `multiple (budget-exhausted)` | 319 budget-exhausted candidate keys | 319 keys | 1954 | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | filed |
| 2 | `agent_workflows/run_analytics_cli.py` | 1 key (`run_analyze`) + 75 test names from `tests/test_run_analytics_cli.py` | 76 (1 key, 75 names) | 449 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 3 | `agent_workflows/compat_migration.py` | `CompatRollback.scan_future_data`, `CompatRollback.rollback`, `CompatRollback.assess`, ... (36 keys) | 36 keys | 446 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 4 | `agent_workflows/run_analytics_taxonomy.py` | `classify_command`, `classify_tool_call`, `ClassAccounting.format_report`, ... (29 keys) | 29 keys | 416 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 5 | `agent_workflows/run_packet.py` | `StepPacket.to_dict`, `StepOutcomeEnvelope.to_dict`, `_compute_packet_digest`, ... (10 keys) | 10 keys | 396 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 6 | `agent_workflows/run_analytics_submit.py` | `open_url`, `_redact_url`, `_refusal_result`, ... (14 keys) | 14 keys | 311 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 7 | `agent_workflows/run_analytics_export.py` | `build_manifest`, `_bundle_readme`, `_sha256_file`, ... (10 keys) | 10 keys | 291 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 8 | `agent_workflows/migration_complex.py` | `SetupRepoStateMachine.apply_change`, `IssueLedger.disposition_all`, `ReleaseReviewCoordinator.__post_init__`, ... (40 keys) | 40 keys | 265 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 9 | `agent_workflows/engine.py` | `create_dependency_gate_hook`, `is_stale_shim_customized`, `_wire_optin_precommit_hook`, ... (12 keys) | 12 keys | 264 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 10 | `agent_workflows/lifecycle_fixtures.py` | `run_downgrade_warning`, `run_customized_file`, `run_multi_host_discovery`, ... (21 keys) | 21 keys | 244 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 11 | `agent_workflows/migration_compact.py` | `evaluate_promotion_gate`, `build_metric_summary`, `TypedContract.validate`, ... (24 keys) | 24 keys | 210 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 12 | `agent_workflows/migration_inventory.py` | `_harness_ir`, `HarnessRegistry.catalog_rows`, `plan_rollup`, ... (25 keys) | 25 keys | 189 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 13 | `agent_workflows/clean_delta.py` | `convert_legacy_adapters`, `uninstall_adapters`, `detect_adapter_drift`, ... (9 keys) | 9 keys | 160 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 14 | `agent_workflows/run_gates.py` | `execute_gated_action`, `GateDecision.is_approved`, `evaluate_gate` | 3 keys | 157 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 15 | `agent_workflows/run_analytics_telemetry.py` | `_parse_accelerator_csv`, `SystemResourceProbeAdapter._run_bounded`, `build_event`, ... (24 keys) | 24 keys | 151 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
| 16 | `agent_workflows/run_analytics_wizard.py` | `apply_choices`, `read_settings`, `plan_deletion`, ... (10 keys) | 10 keys | 145 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 17 | `agent_workflows/ipd_set_executor.py` | `disposition_pass`, `build_lanes`, `routing_config_from_mapping`, ... (13 keys) | 13 keys | 133 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 18 | `agent_workflows/check_engine.py` | `check_system_layout`, `evaluate_ipd_dependencies`, `evaluate_review_decision_escalation`, ... (5 keys) | 5 keys | 124 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 19 | `agent_workflows/run_analytics_report.py` | `_publish_flat`, `verify_bundle`, `prune_snapshots`, ... (5 keys) | 5 keys | 74 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 20 | `agent_workflows/set_lifecycle.py` | `derive_progress`, `stale_evidence_seqs_after_integration`, `make_invalidation_records`, ... (5 keys) | 5 keys | 71 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 21 | `agent_workflows/run_analytics_findings.py` | `format_findings_report`, `price_era_paradox_finding`, `detect_pooled_era_comparison` | 3 keys | 68 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 22 | `agent_workflows/benchmark_manifest.py` | `manifest_from_dict`, `validate_manifest`, `validate_ceilings_dict`, ... (8 keys) | 8 keys | 64 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 23 | `agent_workflows/storage.py` | `move_companion`, `get_git_commit_boundaries`, `load_local_attachment_record`, ... (4 keys) | 4 keys | 55 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 24 | `agent_workflows/host_launchers.py` | `plan_launch`, `verify_fresh`, `enforce_model_binding`, ... (4 keys) | 4 keys | 47 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 25 | `agent_workflows/benchmark_protocol.py` | `assert_frozen`, `freeze_protocol`, `validate_protocol`, ... (7 keys) | 7 keys | 45 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 26 | `agent_workflows/layout_migration.py` | `is_stale_tool_litter`, `_apply_grammar_facet`, `_grammar_facet_for` | 3 keys | 42 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 27 | `agent_workflows/benchmark_corpus.py` | `hash_tree`, `materialize_task`, `is_ground_truth_accessible`, ... (8 keys) | 8 keys | 36 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 28 | `agent_workflows/worktree_lease.py` | `LeaseTable.claim`, `assert_worker_scope`, `LeaseTable.release`, ... (7 keys) | 7 keys | 29 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 29 | `agent_workflows/host_adapters.py` | `SkillPackage.to_dict`, `resolve_role_target`, `SkillPackage.resource_paths`, ... (4 keys) | 4 keys | 22 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 30 | `agent_workflows/agy_sessions.py` | `parse_args`, `main` | 2 keys | 21 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 31 | `agent_workflows/ipd_set_plan.py` | `_run_resume_report`, `run_execute_set`, `_resolve_repo_and_plans` | 3 keys | 21 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 32 | `agent_workflows/term.py` | `Term.format_diagnostic`, `Term.diagnostic`, `Term.title`, ... (8 keys) | 8 keys | 16 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 33 | `agent_workflows/agy_verifier.py` | `AgySessionDouble.invoke`, `finalize_run` | 2 keys | 15 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 34 | `agent_workflows/run_analytics_sources.py` | `inventory_corpus`, `CorpusInventory.generation_counts` | 2 keys | 14 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 35 | `agent_workflows/set_state.py` | `derive_set_state` | 1 keys | 13 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 36 | `agent_workflows/attention.py` | `_colorize_tree_segment` | 1 keys | 12 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 37 | `agent_workflows/record_history.py` | `_synthetic_key`, `read_renames_for` | 2 keys | 11 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 38 | `agent_workflows/agy_view.py` | `main` | 1 keys | 10 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 39 | `agent_workflows/run_analytics_config.py` | `clamp_interval` | 1 keys | 10 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 40 | `agent_workflows/render_stream.py` | 34 test names from `tests/test_run_summary_table.py` | 34 names | 10 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 41 | `agent_workflows/set_records.py` | `write_local_projections` | 1 keys | 9 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 42 | `agent_workflows/result_types.py` | `Diagnostic.from_drift`, `CommandResult.has_findings`, `CommandResult.is_error` | 3 keys | 9 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 43 | `agent_workflows/host_runner.py` | `validate_terminal_envelope` | 1 keys | 7 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 44 | `agent_workflows/run_state.py` | `is_legal_edge` | 1 keys | 7 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 45 | `agent_workflows/cli.py` | `_nv_resolve_types`, `_rewrite_help_token`, `_run_noun_verb` | 3 keys | 6 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 46 | `agent_workflows/research_cmd.py` | `plan_set_priority` | 1 keys | 5 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 47 | `agent_workflows/benchmark_scorer.py` | `intended_verdict`, `is_critical_class` | 2 keys | 5 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 48 | `agent_workflows/agy_run.py` | `main` | 1 keys | 4 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 49 | `agent_workflows/runner_shared.py` | `gate_answer_needs_human_remedy` | 1 keys | 4 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 50 | `agent_workflows/run_analytics_privacy.py` | `redact_text._replace` | 1 keys | 3 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 51 | `agent_workflows/hooks/ipd_dependency_statement_gate.py` | `check._on_staged_file` | 1 keys | 2 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 52 | `agent_workflows/research_refs.py` | `plan_reference_rewrites` | 1 keys | 2 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 53 | `agent_workflows/review_findings.py` | `ReviewDocument.current_decisions` | 1 keys | 2 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 54 | `agent_workflows/runner_stop.py` | `reset_signal_ladder` | 1 keys | 2 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 55 | `agent_workflows/selectors.py` | `Resolution.is_unique` | 1 keys | 2 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 56 | `agent_workflows/comms.py` | `is_ack_valid`, `is_envelope_header_valid` | 2 keys | 2 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 57 | `agent_workflows/artifact_refs.py` | `_rp_type_facet` | 1 keys | 1 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 58 | `agent_workflows/doctor.py` | `_version_drift` | 1 keys | 1 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 59 | `agent_workflows/plan_readiness.py` | `RecheckResult.holding` | 1 keys | 1 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
| 60 | `agent_workflows/run_engine.py` | `RunEngine.run_state` | 1 keys | 1 | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    ```
    Output of python3 -c source section check:
    ```
=== V-01 Source Section Verification Check ===
Section 1 (Rollup mutation keys): 747 keys
  - Carrier-free: 35 ({'guarded': 30, 'pin-retired': 5})
  - Grouped in exactly one group: 712 keys across groups [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60]
Section 2 (Pass-shared files): 17 files
  - Carrier-free: 17 ({'shared-confirmed': 17})
  - Grouped: 0 files
Section 3 (Recreated missing names): 136 names
  - Carrier-free: 27 ({'deliberately-removed': 10, 'moved': 13, 'intended-change': 3, 'retired-pin': 1})
  - Grouped in exactly one group: 109 names across groups [2, 40]
Executed plan inputs:
  - PROP-02 (Order 01 / 24h56i V-03): final verdict 'guarded' (probe verdict 'killed', 4 newly failing tests in restored module; source: .aw/records/plans/executed/20261016-trimcarry-01-24h56i-restore-the-deleted-benchmark-runners-and-reports-tests-and.ipd.md lines 178-188) -> CARRIER-FREE
  - Order 02 (x9z0ve V-02): 0 suspected regressions recorded (all 84 tests passed bare; source: .aw/records/plans/executed/20261016-trimcarry-02-x9z0ve-restore-the-env-limited-run-evidence-completion-tests-with-a.ipd.md lines 155-274) -> CARRIER-FREE
ALL CHECKS PASSED: Every item of all 3 source sections is either in exactly one group or named carrier-free with its class.
    ```
    Per-group deduplication search commands, hits, and dry-run duplicate candidate reports:
    ```
Group 1 (multiple (budget-exhausted)):
  Grep command: grep -rslnwF -e budget_exhausted -e test_agent_schema -e test_agy_tools_graduation -e test_artifact_group -e test_artifact_rename -e test_attention_priority_blocker -e test_attention_stem -e test_awcmdsurf_merge_and_renames -e test_awcmdsurf_mutation_verbs -e test_awmigrename -e test_awphysical_migration -e test_awretrofit_install_scaffolder -e test_backlog_graduated -e test_begin_dirty_gate_scope -e test_benchmark_corpus -e test_benchmark_runners_reports -e test_bug_gate_default -e test_check_engine_receipt_liveness -e test_check_engine_scope_drift -e test_clean_delta -e test_cli_layout -e test_command_shims -e test_commit_refusal_diagnosis -e test_comms -e test_compat_migration_rollback -e test_discovery -e test_doctor_and_marker -e test_duration -e test_evidence_receipts -e test_exec_set_workflow -e test_finalize_exact_attribution -e test_finalize_scope_ownership -e test_gate_answer_propagation -e test_gate_answer_wiring -e test_git_diagnostics -e test_host_adapters_skills -e test_host_runner -e test_installer_skill_emission -e test_integration_revalidation_baseline -e test_interrupt_tty_wedge -e test_ipd_dependency_check -e test_ipd_dependency_statement_gate -e test_layout_inventory_gitignore -e test_layout_migration -e test_lifecycle_fixtures -e test_lifecycle_palette_singleness -e test_merge_conflict_reason -e test_migration_compact_shims -e test_migration_complex -e test_migration_inventory_shared -e test_oc_models_cli -e test_oc_profile_cli -e test_oc_runipd_shim -e test_output_mode -e test_phase4_hooks -e test_plan_readiness_recheck -e test_prompt_id6_filenames -e test_reference_matcher_parity -e test_rename_ledger -e test_research_priority -e test_resumedupe -e test_run_analytics_cache -e test_run_analytics_config -e test_run_analytics_e2e -e test_run_analytics_findings -e test_run_analytics_packaging -e test_run_analytics_privacy -e test_run_analytics_privacy_boundary -e test_run_analytics_report -e test_run_analytics_submit -e test_run_analytics_telemetry -e test_run_ledger_store -e test_run_noun_split -e test_run_packet_gates -e test_run_state_engine -e test_run_viewer_liveness -e test_runipd_selector_admission -e test_selector_resolver_matrix -e test_selector_resolver_parity -e test_show_records -e test_spec_visibility -e test_status_untooled_gate -e test_storage -e test_term_components -e test_token_control -e test_untracked_lane_both_layouts -e test_work_commit .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 2 (agent_workflows/run_analytics_cli.py):
  Grep command: grep -rslnwF -e run_analytics_cli -e test_run_analytics_cli -e test_run_analytics_submit .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
Group 3 (agent_workflows/compat_migration.py):
  Grep command: grep -rslnwF -e compat_migration -e test_compat_migration_rollback -e test_lifecycle_fixtures .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 4 (agent_workflows/run_analytics_taxonomy.py):
  Grep command: grep -rslnwF -e run_analytics_taxonomy -e test_run_analytics_taxonomy .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 5 (agent_workflows/run_packet.py):
  Grep command: grep -rslnwF -e run_packet -e test_host_runner -e test_run_packet_gates .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 6 (agent_workflows/run_analytics_submit.py):
  Grep command: grep -rslnwF -e run_analytics_submit -e test_run_analytics_privacy_boundary -e test_run_analytics_submit -e test_run_analytics_wizard .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 7 (agent_workflows/run_analytics_export.py):
  Grep command: grep -rslnwF -e run_analytics_export -e test_run_analytics_privacy_boundary -e test_run_analytics_submit -e test_run_analytics_wizard .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
Group 8 (agent_workflows/migration_complex.py):
  Grep command: grep -rslnwF -e migration_complex -e test_migration_complex .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/plans/pending/20261014-uypgvi-01-kmmoca-consume-the-release-readiness-report-in-release-review-secti.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 9 (agent_workflows/engine.py):
  Grep command: grep -rslnwF -e engine -e test_command_shims -e test_comms -e test_compat_migration_rollback -e test_exec_set_workflow -e test_host_adapters_skills -e test_ipd_dependency_statement_gate -e test_migration_compact_shims -e test_phase4_hooks -e test_shared_checkout_contract -e test_untracked_lane_both_layouts .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (9): ['.aw/records/backlog/open/20261016-q3ogs0-01-q3ogs0-installer-reports-agents-md-aw-pointer-as-manually.backlog.md', '.aw/records/backlog/open/20261016-mo9oza-01-mo9oza-static-typecheck-gate-fails-with-3-mypy-errors-in.backlog.md', '.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md', '.aw/records/plans/pending/20261014-uypgvi-01-kmmoca-consume-the-release-readiness-report-in-release-review-secti.ipd.md', '.aw/records/plans/pending/20261016-uypgvi-04-snhhw2-release-readiness-disposition-a-managed-repo-s-own-workflow.ipd.md', '.aw/records/plans/pending/20261016-cmpreloc-02-fo08zx-execute-companion-placement-switches-with-companion-staging.ipd.md', '.aw/records/plans/pending/20261016-cmpreloc-03-y1e2m9-make-companion-placement-switches-reachable-from-aw-install.ipd.md', '.aw/records/plans/pending/20261016-rbswitch-03-vv9ki4-wire-records-only-relocation-into-aw-install-relocate-with-e.ipd.md', '.aw/records/plans/pending/20261016-rbswitch-02-fxbm7j-records-only-relocation-in-the-placement-switch-planner-and.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 10 (agent_workflows/lifecycle_fixtures.py):
  Grep command: grep -rslnwF -e lifecycle_fixtures -e test_lifecycle_fixtures .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 11 (agent_workflows/migration_compact.py):
  Grep command: grep -rslnwF -e migration_compact -e test_exec_set_workflow -e test_migration_compact_shims .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/plans/pending/20261016-uypgvi-04-snhhw2-release-readiness-disposition-a-managed-repo-s-own-workflow.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 12 (agent_workflows/migration_inventory.py):
  Grep command: grep -rslnwF -e migration_inventory -e test_migration_inventory_shared .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (2): ['.aw/records/backlog/graduated/20261016-uypgvi-01-ufawpb-readiness-custom-wf-disposition.backlog.md', '.aw/records/plans/pending/20261016-uypgvi-04-snhhw2-release-readiness-disposition-a-managed-repo-s-own-workflow.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 13 (agent_workflows/clean_delta.py):
  Grep command: grep -rslnwF -e clean_delta -e test_clean_delta .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 14 (agent_workflows/run_gates.py):
  Grep command: grep -rslnwF -e run_gates -e test_migration_complex -e test_run_packet_gates .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/plans/pending/20261014-uypgvi-01-kmmoca-consume-the-release-readiness-report-in-release-review-secti.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 15 (agent_workflows/run_analytics_telemetry.py):
  Grep command: grep -rslnwF -e run_analytics_telemetry -e test_run_analytics_packaging -e test_run_analytics_telemetry .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 16 (agent_workflows/run_analytics_wizard.py):
  Grep command: grep -rslnwF -e run_analytics_wizard -e test_run_analytics_submit -e test_run_analytics_wizard .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 17 (agent_workflows/ipd_set_executor.py):
  Grep command: grep -rslnwF -e ipd_set_executor -e test_host_runner -e test_ipd_set_executor .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 18 (agent_workflows/check_engine.py):
  Grep command: grep -rslnwF -e check_engine -e test_cli_layout -e test_doctor_and_marker -e test_ipd_dependency_check -e test_ipd_dependency_statement_gate .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (7): ['.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md', '.aw/records/backlog/graduated/20261002-sbh1o1-01-1vd74h-decide-spec-anchor-stale-gating.backlog.md', '.aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-should-reviews-move-to-per-type-subdirs.backlog.md', '.aw/records/plans/pending/20261016-cleantgt-09-diya77-map-record-files-under-a-companion-records-root-to-their-own.ipd.md', '.aw/records/plans/pending/20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.ipd.md', '.aw/records/plans/pending/20261016-testprune-04-c8bfp9-speed-up-the-slowest-tests-and-shared-fixtures-so-the-retain.ipd.md', '.aw/records/plans/pending/20261016-testprune-02-tv72xy-delete-tests-that-pin-code-structure-names-or-architecture-r.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 19 (agent_workflows/run_analytics_report.py):
  Grep command: grep -rslnwF -e run_analytics_report -e test_run_analytics_report .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 20 (agent_workflows/set_lifecycle.py):
  Grep command: grep -rslnwF -e set_lifecycle -e test_ipd_set_executor .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 21 (agent_workflows/run_analytics_findings.py):
  Grep command: grep -rslnwF -e run_analytics_findings -e test_run_analytics_findings .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 22 (agent_workflows/benchmark_manifest.py):
  Grep command: grep -rslnwF -e benchmark_manifest -e test_benchmark_corpus .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 23 (agent_workflows/storage.py):
  Grep command: grep -rslnwF -e storage -e test_storage .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (6): ['.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md', '.aw/records/backlog/graduated/20261016-cfgreloc-01-n9vd2h-companion-placement-switch.backlog.md', '.aw/records/plans/pending/20261016-cmpreloc-00-aqun5z-support-placement-switches-into-and-out-of-the-public-target.ipd.md', '.aw/records/plans/pending/20261016-cmpreloc-02-fo08zx-execute-companion-placement-switches-with-companion-staging.ipd.md', '.aw/records/plans/pending/20261016-cmpreloc-03-y1e2m9-make-companion-placement-switches-reachable-from-aw-install.ipd.md', '.aw/records/plans/pending/20261016-rbswitch-03-vv9ki4-wire-records-only-relocation-into-aw-install-relocate-with-e.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 24 (agent_workflows/host_launchers.py):
  Grep command: grep -rslnwF -e host_launchers -e test_host_runner .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 25 (agent_workflows/benchmark_protocol.py):
  Grep command: grep -rslnwF -e benchmark_protocol -e test_benchmark_corpus .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 26 (agent_workflows/layout_migration.py):
  Grep command: grep -rslnwF -e layout_migration -e test_awmigrename -e test_layout_migration .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/plans/pending/20261016-rbswitch-02-fxbm7j-records-only-relocation-in-the-placement-switch-planner-and.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 27 (agent_workflows/benchmark_corpus.py):
  Grep command: grep -rslnwF -e benchmark_corpus -e test_benchmark_corpus .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 28 (agent_workflows/worktree_lease.py):
  Grep command: grep -rslnwF -e worktree_lease -e test_ipd_set_executor .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/plans/pending/20261016-testprune-02-tv72xy-delete-tests-that-pin-code-structure-names-or-architecture-r.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 29 (agent_workflows/host_adapters.py):
  Grep command: grep -rslnwF -e host_adapters -e test_host_adapters_skills -e test_host_runner -e test_migration_compact_shims .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 30 (agent_workflows/agy_sessions.py):
  Grep command: grep -rslnwF -e agy_sessions -e test_agy_tools_graduation .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 31 (agent_workflows/ipd_set_plan.py):
  Grep command: grep -rslnwF -e ipd_set_plan -e test_exec_set_workflow .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 32 (agent_workflows/term.py):
  Grep command: grep -rslnwF -e term -e test_term_components .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (2): ['.aw/records/plans/pending/20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.ipd.md', '.aw/records/plans/pending/20261016-rbswitch-03-vv9ki4-wire-records-only-relocation-into-aw-install-relocate-with-e.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 33 (agent_workflows/agy_verifier.py):
  Grep command: grep -rslnwF -e agy_verifier -e test_host_adapters_skills .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 34 (agent_workflows/run_analytics_sources.py):
  Grep command: grep -rslnwF -e run_analytics_sources -e test_run_analytics_e2e .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 35 (agent_workflows/set_state.py):
  Grep command: grep -rslnwF -e set_state -e test_ipd_set_executor .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 36 (agent_workflows/attention.py):
  Grep command: grep -rslnwF -e attention -e test_attention_priority_blocker -e test_attention_stem .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (5): ['.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md', '.aw/records/backlog/graduated/20260929-denypush-01-wcbpqf-decide-port-denial-capability-posture.backlog.md', '.aw/records/plans/pending/20261014-uypgvi-01-kmmoca-consume-the-release-readiness-report-in-release-review-secti.ipd.md', '.aw/records/plans/pending/20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.ipd.md', '.aw/records/plans/pending/20261016-testprune-04-c8bfp9-speed-up-the-slowest-tests-and-shared-fixtures-so-the-retain.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 37 (agent_workflows/record_history.py):
  Grep command: grep -rslnwF -e record_history -e test_artifact_rename -e test_rename_ledger .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 38 (agent_workflows/agy_view.py):
  Grep command: grep -rslnwF -e agy_view -e test_agy_tools_graduation .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 39 (agent_workflows/run_analytics_config.py):
  Grep command: grep -rslnwF -e run_analytics_config -e test_run_analytics_config -e test_run_analytics_telemetry .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 40 (agent_workflows/render_stream.py):
  Grep command: grep -rslnwF -e render_stream -e test_run_summary_table .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/plans/pending/20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 41 (agent_workflows/set_records.py):
  Grep command: grep -rslnwF -e set_records -e test_exec_set_workflow .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 42 (agent_workflows/result_types.py):
  Grep command: grep -rslnwF -e result_types -e test_output_contract -e test_renderer_boundary .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 43 (agent_workflows/host_runner.py):
  Grep command: grep -rslnwF -e host_runner -e test_host_runner .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 44 (agent_workflows/run_state.py):
  Grep command: grep -rslnwF -e run_state -e test_migration_complex -e test_run_state_engine .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 45 (agent_workflows/cli.py):
  Grep command: grep -rslnwF -e cli -e test_artifact_group -e test_artifact_rename -e test_cli_help_and_errors -e test_help_token .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (12): ['.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md', '.aw/records/backlog/graduated/20260929-fcnz1r-01-fcnz1r-unify-backlog-set-dispatch-paths.backlog.md', '.aw/records/plans/pending/20261014-uypgvi-01-kmmoca-consume-the-release-readiness-report-in-release-review-secti.ipd.md', '.aw/records/plans/pending/20261016-cleantgt-09-diya77-map-record-files-under-a-companion-records-root-to-their-own.ipd.md', '.aw/records/plans/pending/20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.ipd.md', '.aw/records/plans/pending/20261016-cmpreloc-02-fo08zx-execute-companion-placement-switches-with-companion-staging.ipd.md', '.aw/records/plans/pending/20261016-cmpreloc-03-y1e2m9-make-companion-placement-switches-reachable-from-aw-install.ipd.md', '.aw/records/plans/pending/20261016-testprune-04-c8bfp9-speed-up-the-slowest-tests-and-shared-fixtures-so-the-retain.ipd.md', '.aw/records/plans/pending/20261016-rbswitch-03-vv9ki4-wire-records-only-relocation-into-aw-install-relocate-with-e.ipd.md', '.aw/records/plans/pending/20261016-707qi4-01-t1fri2-govern-and-regression-test-the-work-begin-plan-path-relativi.ipd.md', '.aw/records/plans/pending/20261016-rbswitch-00-vg7zw3-stop-a-records-backend-change-from-orphaning-the-existing-re.ipd.md', '.aw/records/plans/pending/20261016-askmeplain-02-lkn1zt-run-live-askme-interactive-trials-per-host-model-and-record.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 46 (agent_workflows/research_cmd.py):
  Grep command: grep -rslnwF -e research_cmd -e test_research_priority .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/plans/pending/20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 47 (agent_workflows/benchmark_scorer.py):
  Grep command: grep -rslnwF -e benchmark_scorer -e test_benchmark_corpus .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 48 (agent_workflows/agy_run.py):
  Grep command: grep -rslnwF -e agy_run -e test_agy_tools_graduation .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/plans/pending/20261016-testprune-02-tv72xy-delete-tests-that-pin-code-structure-names-or-architecture-r.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 49 (agent_workflows/runner_shared.py):
  Grep command: grep -rslnwF -e runner_shared -e test_gate_answer_wiring .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (8): ['.aw/records/backlog/graduated/20260930-vmrhj0-01-vmrhj0-retry-allowlist-legacy-token-only.backlog.md', '.aw/records/backlog/graduated/20261001-setdispgate-01-pyhq6s-blast-radius-test-rejects-non-plan-dep-edge.backlog.md', '.aw/records/backlog/graduated/20261002-sbh1o1-01-1vd74h-decide-spec-anchor-stale-gating.backlog.md', '.aw/records/plans/pending/20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.ipd.md', '.aw/records/plans/pending/20261016-707qi4-01-t1fri2-govern-and-regression-test-the-work-begin-plan-path-relativi.ipd.md', '.aw/records/plans/pending/20261016-testprune-01-qqrgv3-build-the-test-classification-and-per-test-coverage-tooling.ipd.md', '.aw/records/plans/pending/20261016-askmeplain-02-lkn1zt-run-live-askme-interactive-trials-per-host-model-and-record.ipd.md', '.aw/records/plans/pending/20261016-testprune-02-tv72xy-delete-tests-that-pin-code-structure-names-or-architecture-r.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 50 (agent_workflows/run_analytics_privacy.py):
  Grep command: grep -rslnwF -e run_analytics_privacy -e test_run_analytics_cache -e test_run_analytics_privacy -e test_run_analytics_privacy_boundary .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 51 (agent_workflows/hooks/ipd_dependency_statement_gate.py):
  Grep command: grep -rslnwF -e ipd_dependency_statement_gate -e test_ipd_dependency_statement_gate .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 52 (agent_workflows/research_refs.py):
  Grep command: grep -rslnwF -e research_refs -e test_reference_matcher_parity .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 53 (agent_workflows/review_findings.py):
  Grep command: grep -rslnwF -e review_findings -e test_doctor_and_marker .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (2): ['.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md', '.aw/records/plans/pending/20261016-testprune-04-c8bfp9-speed-up-the-slowest-tests-and-shared-fixtures-so-the-retain.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 54 (agent_workflows/runner_stop.py):
  Grep command: grep -rslnwF -e runner_stop -e test_interrupt_tty_wedge .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/backlog/parked/20260921-w07sbr-01-w07sbr-runner-stop-trigger-slow-tests-fail.backlog.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 55 (agent_workflows/selectors.py):
  Grep command: grep -rslnwF -e selectors -e test_selector_resolver_matrix -e test_selector_resolver_parity .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 56 (agent_workflows/comms.py):
  Grep command: grep -rslnwF -e comms -e test_comms .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (4): ['.aw/records/backlog/parked/20260815-agent-comms-trust-01-w1ib6z-aw-comms-helper-tool.backlog.md', '.aw/records/backlog/parked/20260815-agent-comms-trust-01-5114n4-agent-comms-verifiable-provenance.backlog.md', '.aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-should-reviews-move-to-per-type-subdirs.backlog.md', '.aw/records/backlog/parked/20260815-agent-comms-trust-01-5wmo8y-agent-comms-trust-tiers.backlog.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 57 (agent_workflows/artifact_refs.py):
  Grep command: grep -rslnwF -e artifact_refs -e test_reference_matcher_parity .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (0): none
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 58 (agent_workflows/doctor.py):
  Grep command: grep -rslnwF -e doctor -e test_doctor_and_marker .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (3): ['.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md', '.aw/records/plans/pending/20261016-testprune-04-c8bfp9-speed-up-the-slowest-tests-and-shared-fixtures-so-the-retain.ipd.md', '.aw/records/plans/pending/20261016-testprune-00-8wfzb5-prune-consolidate-and-speed-up-the-test-suite-to-a-full-reta.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 59 (agent_workflows/plan_readiness.py):
  Grep command: grep -rslnwF -e plan_readiness -e test_plan_readiness_recheck .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (2): ['.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md', '.aw/records/plans/pending/20261016-cleantgt-09-diya77-map-record-files-under-a-companion-records-root-to-their-own.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
Group 60 (agent_workflows/run_engine.py):
  Grep command: grep -rslnwF -e run_engine -e test_run_state_engine .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
  Grep hits (1): ['.aw/records/plans/pending/20261016-testprune-02-tv72xy-delete-tests-that-pin-code-structure-names-or-architecture-r.ipd.md']
  Dry-run duplicate report: aw backlog new: no duplicate candidates detected.
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of every `aw backlog new ... --apply`; pasted `## Filed items` table; pasted `git status --short .aw/records/backlog` listing exactly the filed paths as untracked; for every `bug` item, pasted `grep -n 'Blocks-Release' <path>` showing `next`.
  - Observed evidence:
    Pasted outputs of all 16 `aw backlog new ... --apply` commands:
    ```
=== [1/16] Group 1 (multiple: budget-exhausted) -> lrnh5f ===
Command: aw backlog new --summary Probe then restore behavioral test coverage for 319 budget-exhausted rollup keys --set trimgap --priority --body "<...>" --apply
aw backlog new: no duplicate candidates detected.
  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-lrnh5f-probe-then-restore-behavioral-test-coverage-for-31.backlog.md

=== [2/16] Group 2 (agent_workflows/run_analytics_cli.py) -> n6h5eg ===
Command: aw backlog new --summary Restore behavioral test coverage for run_analytics_cli --set trimgap --priority --body "<...>" --apply
aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
  - dtml3p [done]: Declare the five oc profile CLI leaves so the conformance matrix gate stops failing
  - cm80ge [done]: run_analytics_cli._emit_query_agent's crash-workaround comment goes stale once the --fields projection defect is fixed
  - o8vgss [done]: the --fields projection workaround comment in run_analytics_cli._emit_query_agent asserts a defect that gygujf already fixed, so it misdescribes live behavior
  - d6u2hz [done]: refresh the run_analytics_cli query-summary comment once a --fields projection preserves next, since its stated reason becomes false
  - 9qvfie [graduated]: Rollup of uncited trim-deleted test audit carrier-needed outcomes
  ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-n6h5eg-restore-behavioral-test-coverage-for-run-analytics.backlog.md

=== [3/16] Group 3 (agent_workflows/compat_migration.py) -> 2mcirl ===
Command: aw backlog new --summary Restore behavioral test coverage for compat_migration --set trimgap --priority --body "<...>" --apply
aw backlog new: no duplicate candidates detected.
  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-2mcirl-restore-behavioral-test-coverage-for-compat-migrat.backlog.md

=== [4/16] Group 4 (agent_workflows/run_analytics_taxonomy.py) -> aux1f6 ===
Command: aw backlog new --summary Restore behavioral test coverage for run_analytics_taxonomy --set trimgap --priority --body "<...>" --apply
aw backlog new: no duplicate candidates detected.
  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-aux1f6-restore-behavioral-test-coverage-for-run-analytics.backlog.md

=== [5/16] Group 5 (agent_workflows/run_packet.py) -> aq04yg ===
Command: aw backlog new --summary Restore behavioral test coverage for run_packet --set trimgap --priority --body "<...>" --apply
aw backlog new: no duplicate candidates detected.
  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-aq04yg-restore-behavioral-test-coverage-for-run-packet.backlog.md

=== [6/16] Group 6 (agent_workflows/run_analytics_submit.py) -> gjmiuw ===
Command: aw backlog new --summary Restore behavioral test coverage for run_analytics_submit --set trimgap --priority --body "<...>" --apply
aw backlog new: no duplicate candidates detected.
  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-gjmiuw-restore-behavioral-test-coverage-for-run-analytics.backlog.md

=== [7/16] Group 7 (agent_workflows/run_analytics_export.py) -> liybkg ===
Command: aw backlog new --summary Restore behavioral test coverage for run_analytics_export --set trimgap --priority --body "<...>" --apply
aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
  - spvm3v [done]: Two classes deleted from tests/test_docs.py remain unrestored: RunAnalyticsPrivacyDocTests (run_analytics_export detector blind spots vs docs/run-analytics.md) and LifecycleLegendAndDocsDriftGuardTests (no test asserts the lifecycle legend reaches aw --help output)
  - gjmiuw [open]: Restore behavioral test coverage for run_analytics_submit
  ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-liybkg-restore-behavioral-test-coverage-for-run-analytics.backlog.md

=== [8/16] Group 8 (agent_workflows/migration_complex.py) -> x62jok ===
Command: aw backlog new --summary Restore behavioral test coverage for migration_complex --set trimgap --priority --body "<...>" --apply
aw backlog new: no duplicate candidates detected.
  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-x62jok-restore-behavioral-test-coverage-for-migration-com.backlog.md

=== [9/16] Group 9 (agent_workflows/engine.py) -> 7df9md ===
Command: aw backlog new --summary Restore behavioral test coverage for engine --set trimgap --priority --body "<...>" --apply
aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
  - 4y7nzh [done]: The runner can commit a corrupt records tree and nothing stops it locally, so 36 duplicate-id items accumulated over two days while CI's fail-closed attention gate stayed red and 143 commits were pushed past it
  ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-7df9md-restore-behavioral-test-coverage-for-engine.backlog.md

=== [10/16] Group 10 (agent_workflows/lifecycle_fixtures.py) -> lzn56i ===
Command: aw backlog new --summary Restore behavioral test coverage for lifecycle_fixtures --set trimgap --priority --body "<...>" --apply
aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
  - 2mcirl [open]: Restore behavioral test coverage for compat_migration
  ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-lzn56i-restore-behavioral-test-coverage-for-lifecycle-fix.backlog.md

=== [11/16] Group 11 (agent_workflows/migration_compact.py) -> fdyjv6 ===
Command: aw backlog new --summary Restore behavioral test coverage for migration_compact --set trimgap --priority --body "<...>" --apply
aw backlog new: no duplicate candidates detected.
  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-fdyjv6-restore-behavioral-test-coverage-for-migration-com.backlog.md

=== [12/16] Group 12 (agent_workflows/migration_inventory.py) -> igefrj ===
Command: aw backlog new --summary Restore behavioral test coverage for migration_inventory --set trimgap --priority --body "<...>" --apply
aw backlog new: no duplicate candidates detected.
  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-igefrj-restore-behavioral-test-coverage-for-migration-inv.backlog.md

=== [13/16] Group 13 (agent_workflows/clean_delta.py) -> otc788 ===
Command: aw backlog new --summary Restore behavioral test coverage for clean_delta --set trimgap --priority --body "<...>" --apply
aw backlog new: no duplicate candidates detected.
  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-otc788-restore-behavioral-test-coverage-for-clean-delta.backlog.md

=== [14/16] Group 14 (agent_workflows/run_gates.py) -> ziuj5c ===
Command: aw backlog new --summary Restore behavioral test coverage for run_gates --set trimgap --priority --body "<...>" --apply
aw backlog new: no duplicate candidates detected.
  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-ziuj5c-restore-behavioral-test-coverage-for-run-gates.backlog.md

=== [15/16] Group 15 (agent_workflows/run_analytics_telemetry.py) -> yqpb7q ===
Command: aw backlog new --summary Restore behavioral test coverage for run_analytics_telemetry --set trimgap --priority --body "<...>" --apply
aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
  - xelvyi [done]: The sole-blocking-caller guard was a text search a docstring could trip, so it went red against a correct tree
  ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-yqpb7q-restore-behavioral-test-coverage-for-run-analytics.backlog.md

=== [16/16] Residual Rollup (Groups 16-60) -> q86fxm ===
Command: aw backlog new --summary Residual rollup of remaining uncited trim-deleted test audit gaps across 45 modules --set trimgap --priority --body "<...>" --apply
aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
  - 1sdkvd [done]: Normalize runner interactive output into a shared renderer and graduate remaining tools (runagy, pwatch, agy sessions/view) under aw
  - sr47pt [done]: Rename research status 'intake' -> 'todo' (intuitive 'you still need to do this'); migrate the 8 modules + existing docs; ride with 5tapom's state-advancement so 'todo' means genuinely-not-started
  - dhuape [done]: Unify aw oc run and aw agy run onto a shared tool-agnostic runner library
  - suugsf [done]: installed agent contract never warns that other agents or humans share the checkout, so agents sweep others' uncommitted work into their own commits
  - l6rh0z [done]: begin's in-scope-dirty gate measures the MAIN tree for an isolated lane, so another agent's uncommitted edit to a commonly-scoped file (cli.py) withholds execution authority from an unrelated lane that would run clean at its frozen base
  - y9lcem [done]: The runner cannot read Item-Dependencies: oc_runipd matches only the legacy Dependencies/Depends-on field, so 11 pending plans declare edges the queue silently ignores and ordering falls back to Set/Order
  - e6b9kt [done]: aw run ledger resolution claims the runner's events.jsonl and misdiagnoses it as a corrupt ledger
  - wyw936 [done]: Both runners' verifier gate fails OPEN: only BLOCKED/NOT CONFORMING downgrade, so the schema's own CORRECTION_REQUIRED verdict (and any typo/empty/garbage) is recorded 'verified' and proceeds to finalize+merge
  - qzhfk2 [done]: Should specs get lifecycle subdirs? 24 specs sit intermixed in a flat tree while carrying a real 6-state lifecycle, 16 of them terminal
  - rxoazt [done]: No aw verb sets/removes dependencies for backlog items or specs, none removes a single edge, none accepts a setid target, and 'aw ipd dependencies set' accepts a dangling id6 pre-write (validated only later by aw check)
  - a8eufb [done]: finalize still demands a scope reason for a CONCURRENT agent's COMMITTED out-of-scope path (the committed half of the shared-checkout attribution defect)
  - wx95o4 [done]: id6 is minted per-tree not globally, D140's identity-slot rule cannot catch a walkthrough that DECLARES a plan's id6, and the cross-type collision rule only runs in the full sweep
  - f8m2z2 [done]: re-author aw find as two-tier filesystem-first (maintainer ruling 2026-08-31 displaced e32j35's index-first design): filename listing 20ms vs 357ms, content fallback mandatory for status queries and 8 legacy records
  - tk1gqo [done]: aw check reports check.lifecycle-transition-invalid on conformant plans: _plan_status_events reverses inline history on a newest-first assumption while the repo's actual convention is oldest-first (9 diagnostics repo-wide, incl. approved plans)
  - egqt32 [done]: A mutating pre-commit hook (whitespace/eof fixer, formatter) rewrites a staged file and rejects, and offer_commit unstages and exits 1 instead of re-staging, so routine whitespace churn costs every agent a full commit round trip plus a mandated index re-verify
  - okm6e6 [done]: aw attention's no-project message never checks whether cwd is a git repo, so it reports where it looked but cannot offer the install that would fix it
  - isg0kg [done]: Every aw command should accept a uniform trio of presentation overrides: --no-color (exists on 59/60 top-level but missing from 9 nested host-driver subcommands), --color (force 256-color ANSI, no env var needed), and --tty (behave as if attached to an interactive TTY)
  - ydbhfd [done]: aw runs reports abandoned? for a crashed driver step whose outcome file on disk already records the real disposition: run_viewer flips running -> abandoned? on a dead lock holder without ever reading outcomes/*.json
  - plbkp5 [done]: surface a plain count of waiting .aw/inbox/ drops in aw attention, by LISTING the directory only and never opening a file, so a forgotten drop is visible without inbox content ever being parsed
  - f1sw71 [done]: attention has no per-requirement spec tracking, so an approved spec can sit half-built with nothing asking which half: decide whether requirement-level tracking should exist
  - jys5dp [done]: a known unfixed defect named in an IPD's prose vanishes when the plan reaches executed: require handoff to a durable carrier, mirroring the release-gate close predicate
  - yocdq4 [done]: no way to re-integrate a verified lane without a full agent re-run, and resume re-dispatches finished work instead of merging it: add aw <host> integrate and call it from resume
  - r4qliv [done]: two lanes from run-20260905 remain unintegrated: cqx5v7 needs conflict resolution in both runners, i6015i never did its work and needs re-running
  - trjfyy [done]: spec 25kzda 2.1 retry/correction budget is dormant: plan_retry and retry_budget_remaining have zero production callers, so a failed run item gets no automatic correction attempt
  - ol8iyx [done]: wtiso retirement debt: the out-of-repo control-state relocation (Phase 4, 58ha43) has no successor plan, and six in-code pointers plus spec c4gd2h OQ-03 still name retired wtiso plans as the live owner of unbuilt work
  - lmjc8h [done]: check_collisions include_retired disagreement: aw doctor and aw check report different populations from one predicate
  - x15f0q [done]: install --to-aw leaves empty legacy directories and .agents/README.md behind, so every migrated repo permanently reports a dual-layout split-brain and doctor advises a migration that already ran
  - 7ts6ek [done]: finalize's commit-cohesion scope audit demands reasons for other plans' paths when several lanes share a hot file
  - fci7yn [done]: Stranded-lane remedy says 'no aw integrate verb exists yet' though it shipped: lane_remedy_hint probes cmd_integrate, a symbol that does not exist
  - a3ugp1 [done]: The approval gate refuses three pending reaskscore plans on a stale negative verdict, failing tests/test_plan_readiness.py at HEAD
  - lv92c6 [done]: Plan yaxr4i asserts the color engine is already correct and complete, which measurement falsifies
  - nyz8dt [done]: Unify the three divergent should_color implementations and stop FORCE_COLOR=0 forcing color on
  - 4y4xo5 [done]: aw group research clobbers each record Order to 0 when --order is omitted (the e3hzyc defect in research_refs)
  - 4znh53 [done]: Color-env tests race under xdist: NO_COLOR/FORCE_COLOR/TERM mutate process-global os.environ, so parallel workers cross-contaminate and a different color node fails per run
  - ci9kx2 [done]: aw attention --dir <non-AW-directory> prints nothing and exits 0, so an explicitly named wrong directory looks like success
  - q1ov25 [done]: status_set._ID_RE is a THIRD unbounded identity reader outside 76w6mq's declared scope, so a quoted - Id: is still read as a declaration after that plan lands
  - xqm16x [done]: aw check's errors/warnings tally keys on the rule NAME prefix instead of the finding's severity, so every warning is counted as an error
  - zf999x [done]: A third FULL_AUTO_ACTOR in runner_shared disagrees with both host copies in value AND message, and nothing reads it, so consolidating the hosts onto it would silently rewrite every recorded actor and overstate what the gate proved
  - 0vbdll [done]: A lane worktree's own code is invisible to the installed 'aw', so an agent measures the main checkout and reports the wrong result
  - 5x195l [done]: aw ipd --agent crashes with a schema ValueError in a non-project directory (exit_code=3 is unemittable)
  - lw1rhj [done]: test_artifact_audit VerdictParityTests::test_four_verdict_shapes failed once under random ordering and did not reproduce in four subsequent full runs
  - axayfn [done]: Three identity readers outside plan 76w6mq's fence are still unbounded to the metadata region
  - hd5bkk [done]: aw find reports a zero-match selector as CLEAN exit 0, the same fail-open aw attention just fixed
  - ildjse [done]: Wire the run state machine into the two host runners, which import none of run_state, verify_roles or run_recovery
  - uin96r [done]: The aw console script resolves agent_workflows from the main checkout, so a lane worktree's edits are invisible to CLI evidence
  - mblu3p [done]: aw archive/rename/group for research bypass the ONE resolver, contradicting selectors.py's documented single-resolver claim
  - zftbta [done]: aw rename leaves 44 record citations dangling in agent_workflows source, so a maintainer keeps hand-fixing the shipped package after every rename
  - dtq6jr [done]: every aw config verb except the exclude subgroup (seven of them) crashes with an unhandled ImportError when passed --agent, so the whole config family has no machine-readable surface
  - phdpbf [done]: Decide whether render_run_summary_table Status cell should render Section 5 lifecycle glyph
  - n8adhb [done]: tools/test_agy_run.py is not collected by any gate
  - 3ouico [done]: aw.agent/v1 findings counts every Diagnostic regardless of severity, so one warning-severity diagnostic reports findings 1 on a clean repo (outcome clean, exit 0), blocking the cheap route for any advisory that should reach an agent
  - 7jl2bf [done]: Decide whether aw check --source-anchors should resolve <file>.py:<line> offsets in tracked source, not only spec anchors
  - hegwri [done]: Nothing in the package can create a run ledger: no writer of a kind='run' header record exists, so RunLedgerStore refuses every first append with RL-E041
  - 23p80m [done]: aw rename rewrites citing Scope-Paths entries with no in-flight begin-receipt guard, so renaming an artifact can stale an executing plan's frozen contract and strand its lane at finalize
  - wxpytg [done]: Doctor machine diagnostic construction hardcodes severity error for every drift
  - y11p5u [done]: Raw 38;5 escapes in pwatch, runners_monitor and render_stream headers bypass the color_depth pin
  - 5slmvq [done]: Restore behavioral test coverage for _run_migrate_layout
  - ms06pi [graduated]: Decide where aw-only artifact metadata lives (inline md vs sidecar JSONL vs sqlite) and finish the awhistory plans migration with real timestamps; tk1gqo is a symptom of the deferred b0behn follow-up
  - 9qvfie [graduated]: Rollup of uncited trim-deleted test audit carrier-needed outcomes
  ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
  What it can and cannot tell you:
    - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
    - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
    - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
  Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/z2xs98/.aw/records/backlog/open/20261016-trimgap-01-q86fxm-residual-rollup-of-remaining-uncited-trim-deleted.backlog.md

    ```
    Filed items table:
    ```markdown
| Item Id | File Path | Scope | Work-Kind | Priority | Summary |
|---|---|---|---|---|---|
| `lrnh5f` | `.aw/records/backlog/open/20261016-trimgap-01-lrnh5f-probe-then-restore-behavioral-test-coverage-for-31.backlog.md` | Group 1 (multiple: budget-exhausted) | `chore` | `low` | Probe then restore behavioral test coverage for 319 budget-exhausted rollup keys |
| `n6h5eg` | `.aw/records/backlog/open/20261016-trimgap-01-n6h5eg-restore-behavioral-test-coverage-for-run-analytics.backlog.md` | Group 2 (agent_workflows/run_analytics_cli.py) | `chore` | `low` | Restore behavioral test coverage for run_analytics_cli |
| `2mcirl` | `.aw/records/backlog/open/20261016-trimgap-01-2mcirl-restore-behavioral-test-coverage-for-compat-migrat.backlog.md` | Group 3 (agent_workflows/compat_migration.py) | `chore` | `low` | Restore behavioral test coverage for compat_migration |
| `aux1f6` | `.aw/records/backlog/open/20261016-trimgap-01-aux1f6-restore-behavioral-test-coverage-for-run-analytics.backlog.md` | Group 4 (agent_workflows/run_analytics_taxonomy.py) | `chore` | `low` | Restore behavioral test coverage for run_analytics_taxonomy |
| `aq04yg` | `.aw/records/backlog/open/20261016-trimgap-01-aq04yg-restore-behavioral-test-coverage-for-run-packet.backlog.md` | Group 5 (agent_workflows/run_packet.py) | `chore` | `low` | Restore behavioral test coverage for run_packet |
| `gjmiuw` | `.aw/records/backlog/open/20261016-trimgap-01-gjmiuw-restore-behavioral-test-coverage-for-run-analytics.backlog.md` | Group 6 (agent_workflows/run_analytics_submit.py) | `chore` | `low` | Restore behavioral test coverage for run_analytics_submit |
| `liybkg` | `.aw/records/backlog/open/20261016-trimgap-01-liybkg-restore-behavioral-test-coverage-for-run-analytics.backlog.md` | Group 7 (agent_workflows/run_analytics_export.py) | `chore` | `low` | Restore behavioral test coverage for run_analytics_export |
| `x62jok` | `.aw/records/backlog/open/20261016-trimgap-01-x62jok-restore-behavioral-test-coverage-for-migration-com.backlog.md` | Group 8 (agent_workflows/migration_complex.py) | `chore` | `low` | Restore behavioral test coverage for migration_complex |
| `7df9md` | `.aw/records/backlog/open/20261016-trimgap-01-7df9md-restore-behavioral-test-coverage-for-engine.backlog.md` | Group 9 (agent_workflows/engine.py) | `chore` | `low` | Restore behavioral test coverage for engine |
| `lzn56i` | `.aw/records/backlog/open/20261016-trimgap-01-lzn56i-restore-behavioral-test-coverage-for-lifecycle-fix.backlog.md` | Group 10 (agent_workflows/lifecycle_fixtures.py) | `chore` | `low` | Restore behavioral test coverage for lifecycle_fixtures |
| `fdyjv6` | `.aw/records/backlog/open/20261016-trimgap-01-fdyjv6-restore-behavioral-test-coverage-for-migration-com.backlog.md` | Group 11 (agent_workflows/migration_compact.py) | `chore` | `low` | Restore behavioral test coverage for migration_compact |
| `igefrj` | `.aw/records/backlog/open/20261016-trimgap-01-igefrj-restore-behavioral-test-coverage-for-migration-inv.backlog.md` | Group 12 (agent_workflows/migration_inventory.py) | `chore` | `low` | Restore behavioral test coverage for migration_inventory |
| `otc788` | `.aw/records/backlog/open/20261016-trimgap-01-otc788-restore-behavioral-test-coverage-for-clean-delta.backlog.md` | Group 13 (agent_workflows/clean_delta.py) | `chore` | `low` | Restore behavioral test coverage for clean_delta |
| `ziuj5c` | `.aw/records/backlog/open/20261016-trimgap-01-ziuj5c-restore-behavioral-test-coverage-for-run-gates.backlog.md` | Group 14 (agent_workflows/run_gates.py) | `chore` | `low` | Restore behavioral test coverage for run_gates |
| `yqpb7q` | `.aw/records/backlog/open/20261016-trimgap-01-yqpb7q-restore-behavioral-test-coverage-for-run-analytics.backlog.md` | Group 15 (agent_workflows/run_analytics_telemetry.py) | `chore` | `low` | Restore behavioral test coverage for run_analytics_telemetry |
| `q86fxm` | `.aw/records/backlog/open/20261016-trimgap-01-q86fxm-residual-rollup-of-remaining-uncited-trim-deleted.backlog.md` | Residual Rollup (Groups 16-60) | `chore` | `low` | Residual rollup of remaining uncited trim-deleted test audit gaps across 45 modules |
    ```
    Pasted git status --short .aw/records/backlog (exactly 16 filed paths untracked before commit):
    ```
?? .aw/records/backlog/open/20261016-trimgap-01-2mcirl-restore-behavioral-test-coverage-for-compat-migrat.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-7df9md-restore-behavioral-test-coverage-for-engine.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-aq04yg-restore-behavioral-test-coverage-for-run-packet.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-aux1f6-restore-behavioral-test-coverage-for-run-analytics.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-fdyjv6-restore-behavioral-test-coverage-for-migration-com.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-gjmiuw-restore-behavioral-test-coverage-for-run-analytics.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-igefrj-restore-behavioral-test-coverage-for-migration-inv.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-liybkg-restore-behavioral-test-coverage-for-run-analytics.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-lrnh5f-probe-then-restore-behavioral-test-coverage-for-31.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-lzn56i-restore-behavioral-test-coverage-for-lifecycle-fix.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-n6h5eg-restore-behavioral-test-coverage-for-run-analytics.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-otc788-restore-behavioral-test-coverage-for-clean-delta.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-q86fxm-residual-rollup-of-remaining-uncited-trim-deleted.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-x62jok-restore-behavioral-test-coverage-for-migration-com.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-yqpb7q-restore-behavioral-test-coverage-for-run-analytics.backlog.md
?? .aw/records/backlog/open/20261016-trimgap-01-ziuj5c-restore-behavioral-test-coverage-for-run-gates.backlog.md
    ```
    Blocks-Release evidence:
    Zero items filed as `bug` (0 regressions observed across Set trimcarry); all 16 items filed as `chore` with Priority `low` (absent behavioral test coverage / deferred probing). No file carries `- Blocks-Release:`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `## Reconciliation` table with the total shown as 770; pasted `aw find backlog <id6>` output for every id6 named; pasted footprint command output listing only the two restored test modules.
  - Observed evidence:
    Reconciliation table (total 770):
    ```markdown
| 9qvfie Outcome Class | Sub-Category / Verdict | Count | Set trimcarry Resolution & Terminal Status | Carrier or Carrier-Free Disposition |
|---|---|---:|---|---|
| `unprovable` (1) | `PROP-02` (`compute_aggregate_metrics`) | 1 | Settled in Order 01 (`24h56i`) V-03 via narrowed mutation probe (`killed`, 4 newly failing tests in restored module, wall_s: 4.6s); final verdict `guarded` | Carrier-free (`guarded`) |
| `replay-env-limited` (1) | `tests/test_run_evidence_completion.py` | 1 | Restored in Order 02 (`x9z0ve`) with id6 spec lookup and contract updates; 84 tests pass bare and fast suite | Carrier-free (restored in tree) |
| `triaged-not-mutated` keys (747) | `pin-retired` | 5 | Classified in `hpjj44` / `b1mx2w`; code-structure tests forbidden by P16 / AGENTS.md | Carrier-free (`pin-retired`) |
| | `key-gone` | 0 | Subject functions still present at HEAD | Carrier-free (`key-gone`) |
| | `guarded` | 30 | Mutation probe killed by surviving test suite in Order 05 (`rf1xxr`) | Carrier-free (`guarded`) |
| | `budget-exhausted` | 319 | Unprobed keys stopped after cumulative wall time reached 10,800s cap in Order 05 (`rf1xxr`) | Backlog item `lrnh5f` (Group 1) |
| | `run_analytics_cli` key (`run_analyze`) | 1 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 4 excl lines) | Backlog item `n6h5eg` (Group 2) |
| | `compat_migration` keys | 36 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 446 excl lines) | Backlog item `2mcirl` (Group 3) |
| | `run_analytics_taxonomy` keys | 29 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 416 excl lines) | Backlog item `aux1f6` (Group 4) |
| | `run_packet` keys | 10 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 396 excl lines) | Backlog item `aq04yg` (Group 5) |
| | `run_analytics_submit` keys | 14 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 311 excl lines) | Backlog item `gjmiuw` (Group 6) |
| | `run_analytics_export` keys | 10 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 291 excl lines) | Backlog item `liybkg` (Group 7) |
| | `migration_complex` keys | 40 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 265 excl lines) | Backlog item `x62jok` (Group 8) |
| | `engine` keys | 12 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 264 excl lines) | Backlog item `7df9md` (Group 9) |
| | `lifecycle_fixtures` keys | 21 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 244 excl lines) | Backlog item `lzn56i` (Group 10) |
| | `migration_compact` keys | 24 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 210 excl lines) | Backlog item `fdyjv6` (Group 11) |
| | `migration_inventory` keys | 25 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 189 excl lines) | Backlog item `igefrj` (Group 12) |
| | `clean_delta` keys | 9 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 160 excl lines) | Backlog item `otc788` (Group 13) |
| | `run_gates` keys | 3 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 157 excl lines) | Backlog item `ziuj5c` (Group 14) |
| | `run_analytics_telemetry` keys | 24 | Unreached at baseline HEAD (verdict `unguarded-unreached`, 151 excl lines) | Backlog item `yqpb7q` (Group 15) |
| | Residual key modules (44 modules) | 135 | Unreached at baseline HEAD (verdicts `unguarded-unreached` [129], `unguarded` [2], `property-unidentifiable` [3], `unprovable` [1]; 1,173 excl lines) | Residual backlog item `q86fxm` (Groups 16-60) |
| `triaged-not-mutated` pass-shared files (17) | `shared-confirmed` | 17 | Measured in Order 03 (`8dyt88`) `## Pass-shared re-diff`: 0 exclusive lines reached; covered by surviving tests. Declined with partition reason. [Human review requested] | Carrier-free (`shared-confirmed`) |
| `recreated` files with missing names (4) | 4 files holding 136 missing test names | 4 | Evaluated in Order 04 (`we3kkb`) `## Recreated missing names`: 10 `deliberately-removed`, 13 `moved`, 1 `retired-pin`, 3 `intended-change` (27 carrier-free); 75 `gap` names in `tests/test_run_analytics_cli.py` carried by `n6h5eg`; 34 `gap` names in `tests/test_run_summary_table.py` carried by `q86fxm` | Carried across `n6h5eg`, `q86fxm`, and carrier-free classifications |
| **Total Rollup Outcomes** | - | **770** | **Sum of all 770 outcomes accounted for across Set trimcarry** | **Reconciles exactly: 1 + 1 + 747 + 17 + 4 = 770** |
    ```
    Pasted aw find backlog <id6> output for every filed item:
    ```
$ aw find backlog lrnh5f
◕  open          lrnh5f  .aw/records/backlog/open/20261016-trimgap-01-lrnh5f-probe-then-restore-behavioral-test-coverage-for-31.backlog.md
$ aw find backlog n6h5eg
◕  open          n6h5eg  .aw/records/backlog/open/20261016-trimgap-01-n6h5eg-restore-behavioral-test-coverage-for-run-analytics.backlog.md
$ aw find backlog 2mcirl
◕  open          2mcirl  .aw/records/backlog/open/20261016-trimgap-01-2mcirl-restore-behavioral-test-coverage-for-compat-migrat.backlog.md
$ aw find backlog aux1f6
◕  open          aux1f6  .aw/records/backlog/open/20261016-trimgap-01-aux1f6-restore-behavioral-test-coverage-for-run-analytics.backlog.md
$ aw find backlog aq04yg
◕  open          aq04yg  .aw/records/backlog/open/20261016-trimgap-01-aq04yg-restore-behavioral-test-coverage-for-run-packet.backlog.md
$ aw find backlog gjmiuw
◕  open          gjmiuw  .aw/records/backlog/open/20261016-trimgap-01-gjmiuw-restore-behavioral-test-coverage-for-run-analytics.backlog.md
$ aw find backlog liybkg
◕  open          liybkg  .aw/records/backlog/open/20261016-trimgap-01-liybkg-restore-behavioral-test-coverage-for-run-analytics.backlog.md
$ aw find backlog x62jok
◕  open          x62jok  .aw/records/backlog/open/20261016-trimgap-01-x62jok-restore-behavioral-test-coverage-for-migration-com.backlog.md
$ aw find backlog 7df9md
◕  open          7df9md  .aw/records/backlog/open/20261016-trimgap-01-7df9md-restore-behavioral-test-coverage-for-engine.backlog.md
$ aw find backlog lzn56i
◕  open          lzn56i  .aw/records/backlog/open/20261016-trimgap-01-lzn56i-restore-behavioral-test-coverage-for-lifecycle-fix.backlog.md
$ aw find backlog fdyjv6
◕  open          fdyjv6  .aw/records/backlog/open/20261016-trimgap-01-fdyjv6-restore-behavioral-test-coverage-for-migration-com.backlog.md
$ aw find backlog igefrj
◕  open          igefrj  .aw/records/backlog/open/20261016-trimgap-01-igefrj-restore-behavioral-test-coverage-for-migration-inv.backlog.md
$ aw find backlog otc788
◕  open          otc788  .aw/records/backlog/open/20261016-trimgap-01-otc788-restore-behavioral-test-coverage-for-clean-delta.backlog.md
$ aw find backlog ziuj5c
◕  open          ziuj5c  .aw/records/backlog/open/20261016-trimgap-01-ziuj5c-restore-behavioral-test-coverage-for-run-gates.backlog.md
$ aw find backlog yqpb7q
◕  open          yqpb7q  .aw/records/backlog/open/20261016-trimgap-01-yqpb7q-restore-behavioral-test-coverage-for-run-analytics.backlog.md
$ aw find backlog q86fxm
◕  open          q86fxm  .aw/records/backlog/open/20261016-trimgap-01-q86fxm-residual-rollup-of-remaining-uncited-trim-deleted.backlog.md
    ```
    Set trimcarry code and test footprint:
    ```
$ git log --name-only --format= -E --grep '(24h56i|x9z0ve|8dyt88|we3kkb|rf1xxr|z2xs98)' -- agent_workflows tests tools | sort -u
tests/test_benchmark_runners_reports.py
tests/test_run_evidence_completion.py
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted before/after per-rule counts of `aw check --agent` with any new finding explained; pasted `aw commit` output and `git show --stat HEAD` listing exactly the filed backlog files and the Set doc.
  - Observed evidence:
    Pasted before/after per-rule counts of aw check --agent:
    ```
Rule Comparison (Before vs After):
  check.ipd-carrier-finished-unverified: before=3, after=3, diff=+0
  check.lifecycle-transition-unvalidated: before=17, after=17, diff=+0
  check.scope-not-audited: before=1, after=1, diff=+0
  check.source-test-citation-dangling: before=42, after=42, diff=+0
  check.spec-criteria-uncovered: before=1, after=1, diff=+0
  check.system-layout-missing: before=1, after=1, diff=+0
Total findings before: 65; total findings after: 65 (0 new findings).
Zero new findings on any file authored or updated by this plan.
    ```
    Pasted aw commit output:
    ```
aw commit: committed 17 path(s): f6f9e2cee925978228c1028840a06f6c04de098e
    ```
    Pasted git show --stat HEAD:
    ```
commit f6f9e2cee925978228c1028840a06f6c04de098e (HEAD -> aw/lane/z2xs98)
Author: Gabriele Fariello <gabriele.fariello@gmail.com>
Date:   Fri Oct 16 23:15:45 2026 -0400

    work(z2xs98): File grouped backlog items for every rollup gap and reconcile the 770 outcomes

    AW-Run: run-20261016T221501Z-3469718
    AW-Item: z2xs98
    AW-Runner: aw agy run

 ...oral-test-coverage-for-compat-migrat.backlog.md |  16 +++
 ...-behavioral-test-coverage-for-engine.backlog.md |  16 +++
 ...avioral-test-coverage-for-run-packet.backlog.md |  16 +++
 ...oral-test-coverage-for-run-analytics.backlog.md |  16 +++
 ...oral-test-coverage-for-migration-com.backlog.md |  16 +++
 ...oral-test-coverage-for-run-analytics.backlog.md |  16 +++
 ...oral-test-coverage-for-migration-inv.backlog.md |  16 +++
 ...oral-test-coverage-for-run-analytics.backlog.md |  16 +++
 ...tore-behavioral-test-coverage-for-31.backlog.md |  16 +++
 ...oral-test-coverage-for-lifecycle-fix.backlog.md |  16 +++
 ...oral-test-coverage-for-run-analytics.backlog.md |  16 +++
 ...vioral-test-coverage-for-clean-delta.backlog.md |  16 +++
 ...up-of-remaining-uncited-trim-deleted.backlog.md |  62 ++++++++
 ...oral-test-coverage-for-migration-com.backlog.md |  16 +++
 ...oral-test-coverage-for-run-analytics.backlog.md |  16 +++
 ...havioral-test-coverage-for-run-gates.backlog.md |  16 +++
 ...16-trimcarry-01-b1mx2w-rollup-reach.findings.md | 158 +++++++++++++++++++++
 17 files changed, 460 insertions(+)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Orders 01 to 05 are `executed`. Scope fence: `- Scope-Paths:` declares `.aw/records/backlog/` (new items only; do not edit existing items, including `9qvfie`) and the Set's findings doc; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command; never record a filing or a count you did not produce. Commit only the files this plan wrote through `aw commit <plan> -- <paths>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
