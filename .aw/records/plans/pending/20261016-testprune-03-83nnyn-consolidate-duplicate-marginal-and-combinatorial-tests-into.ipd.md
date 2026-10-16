# IPD: Consolidate duplicate, marginal and combinatorial tests into table-driven tests without losing a covered line or branch

- Date: 2026-10-16
- Kind: child
- Concern: Prompt `4ul37x` (Set `testprune`) items 5 and 6 and its CONSOLIDATE section. Baseline research `offdhr` (main `6ea45c974`): of 3714 recorded in-process test contexts, 1331 cover no line that some other test does not also cover, and in 70 modules every recorded test is in that set. Measured at authoring (`pytest tests/ -m '' --collect-only -q -o addopts=""`, this worktree): 8799 collected, of which 1922 node ids are parametrize cases of just 92 functions; one function alone (`tests/test_descriptive_refusal_hoist.py::test_all_five_routes_match_frozen_table_for_nonempty_verbs`) contributes 900 cases, and that module 997 of the 8799. Duplicate and combinatorial tests cost collection, worker dispatch and maintenance without catching more regressions.
- Scope: Batch by subsystem. For each batch, read every candidate (zero-unique-line tests from `offdhr`/the `qqrgv3` tooling, plus large parametrize matrices), merge near-identical tests into one table-driven test (P16 row shape: case id first, trailing `why`), reduce combinatorial matrices to happy path, boundaries, one representative per equivalence class and every distinct error branch, fold defect-citing tests into rows that keep their id6 in `why`, introduce a shared copy-on-write temp git repo fixture for the duplicated per-module repo builders the batch touches, and prove per batch with branch coverage that no line or branch of `agent_workflows/` lost its last covering test. Records one decision-table row per consolidated or deleted node id. Converts no subprocess test to in-process and does no timing work (child `c8bfp9`).
- Scope-Paths: tests/, conftest.py, .aw/records/research/*testprune*
- Item-Dependencies: executed:tv72xy
- Status: to-review
- Work-Kind: chore
- Priority: high
- Set: testprune
- Order: 3
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 83nnyn

## Workflow history
- 2026-10-16 to-review (aw set): authored from prompt 4ul37x (Set testprune) with baseline research offdhr/7ry5kv

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every duplicate, marginal and combinatorial test identified by measurement is merged into a table-driven test or recorded as deleted with a reason, cutting collected node ids substantially while union line and branch coverage of `agent_workflows/` and the hguae9 `core` per-module coverage stay at or above the pre-batch baseline.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Per-batch protocol (applies to E-02 through E-08; each is one subsystem and one `aw commit 83nnyn -- <paths>`): (a) list candidates from the `qqrgv3` per-test line+branch contexts and the parametrize census of E-01; (b) READ each candidate and its nearest covering sibling: equal lines are not equal assertions, so a candidate is merged only when its assertions are a subset of the surviving row's, and otherwise kept with a decision-table reason; (c) subprocess-only tests (no in-process context) are classified by reading, never by the 0-unique-lines metric; (d) a test citing a backlog id6, plan id6 or incident becomes a row whose `why` keeps that id; (e) never weaken an assertion; (f) rerun the batch's modules with branch coverage and diff against the E-01 baseline for the batch's source modules; (g) append one decision-table row per affected node id (node id, category `consolidate`/`delete-duplicate`/`delete-marginal`, surviving node id, reason).

### Task group 1: baseline for this child

- [ ] E-01 Using the `qqrgv3` tooling, regenerate per-test line+branch contexts (`--cov-context=test --cov-branch`, full suite `-m ''`) at this child's starting commit and record in the decision-table research: union line and branch totals, the hguae9 core per-module coverage table, and a parametrize census (cases per function from `--collect-only -q`, functions with at least 9 cases, sorted descending).
  - Depends on: none
  - Expected outcome: baseline totals and census recorded; census top rows match the authoring measurement (descriptive_refusal_hoist 900 and 90, usage_refusal_agent_record 67 and 67, statusline_stop_tally 60, shared_flag_honored 51/51/32/32, agent_surface_conformance 51/32, statusline_visible_width 32) or the drift is noted.
  - Execution state: pending

### Task group 2: combinatorial matrices (boundary and equivalence reduction)

- [ ] E-02 Reduce `tests/test_descriptive_refusal_hoist.py`: the 900-case and 90-case functions are the cross product routes(5) x verbs(10) x bound_length(2) x values(9). Keep EVERY route x EVERY value class x both `bound_length` settings against `FROZEN_SUFFIX_TABLE` for one representative verb plus the empty verb (the value axis is where the branches are: newline, CR, control char, late control char, over-length, at-length boundary), and keep EVERY verb against one rejecting value to prove the verb prefix is rendered for each (the verb axis is a formatting pass-through, one equivalence class). Express the reduced set as one table with case ids and `why`.
  - Depends on: E-01
  - Expected outcome: module drops from 997 to roughly 110 node ids; branch-coverage diff for `attention_contract`, `backlog`, `specs`, `status_set`, `research_cmd`, `releases` shows zero lines or branches newly uncovered.
  - Execution state: pending
- [ ] E-03 Reduce the statusline matrices: `tests/test_statusline_stop_tally.py::TestStatuslineStopTallyRendering::test_statusline_rectangular_with_badges` (stop_level 5 x tally 3 x styled 2 x unicode 2 = 60), `tests/test_statusline_visible_width.py::test_statusline_box_is_rectangular` (32), the two 16-case sweeps in `tests/test_statusline_ascii_mode.py`, and `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_exhaustive_sweep` (`itertools.product(*_STATUSLINE_SWEPT_DOMAINS)` over 9 domains, 20.5s, `slow`). Replace full products with a pairwise covering array (every value of every domain appears, and every pair of domain values appears at least once) generated deterministically in the test module, plus explicit boundary rows (no badge, max stop level, zero tally, widest glyph, ascii mode) and every hostile-input row; invariants asserted are unchanged.
  - Depends on: E-01
  - Expected outcome: statusline node ids and the sweep's iteration count drop; branch-coverage diff for the statusline renderer modules shows zero lost lines or branches; the sweep's duration recorded before and after.
  - Execution state: pending
- [ ] E-04 Merge mode-pair leaf matrices without reducing the leaf axis: `tests/test_usage_refusal_agent_record.py::test_required_arg_leaf_agent_mode` and `::test_required_arg_leaf_json_mode` (67 + 67, both in-process via `_capture_cli`) become one parametrized-per-leaf test asserting both the `--agent` cannot-run record (schema-valid via `agent_schema.validate_agent_record`, `exit` 2, `next`, no `/home/` or `/tmp/` leak) and the `--json` cannot-run object, with mode as an accumulate column. Apply the same merge to any other pair in the E-01 census whose two functions share argv construction and differ only in an output mode, provided the merged test reports every failing mode at once.
  - Depends on: E-01
  - Expected outcome: 134 node ids become 67, every leaf still exercised in both modes (a temporarily broken `--json` branch fails the merged test with the mode named); coverage diff zero lost.
  - Execution state: pending

### Task group 3: duplicate and marginal tests, by subsystem

- [ ] E-05 Runner batch: zero-unique candidates in `tests/test_oc_runipd.py` (60 of 105 recorded), `tests/test_runner_shared.py` (32 of 71), `tests/test_agy_runipd_cli.py` (29 of 38), `tests/test_finalize_sendback.py` (16 of 31), `tests/test_orchestrator_retirement.py` (15 of 30), `tests/test_runner_backlog_close_behavior.py` (12 of 30), plus the runner-named modules in the `offdhr` all-zero list (`test_agy_failed_state_parity`, `test_lane_reaper_callshape`, `test_prior_attempt_projection`, `test_retry_class_mapping`, `test_run_cli_human_redaction`, `test_run_dir_outcomes_parent_is_guaranteed`, `test_run_progress_count`, `test_run_summary_visible_width`, `test_runner_safety_probe_memo`, `test_runs_flag_position_parity`). Host-parity pairs (oc versus agy) become one test with a HOST column. Apply the per-batch protocol.
  - Depends on: E-01
  - Expected outcome: decision-table rows for every candidate; coverage diff for `oc_runipd`, `agy_runipd`, `runner_shared`, `finalize*`, `run_*` modules shows zero lost lines or branches.
  - Execution state: pending
- [ ] E-06 Records batch: `tests/test_status_set.py` (22 of 44), `tests/test_backlog.py` (17 of 33), `tests/test_group_verb_policy.py` (17 of 28; includes the 9-case setid warn matrices), `tests/test_research_index.py` (9 of 28), `tests/test_attention.py` (10 of 37), plus all-zero modules `test_attention_blind_spot`, `test_attention_degraded_item`, `test_backlog_close_host_label`, `test_backlog_gate_follows_status`, `test_backlog_history_dedup_parity`, `test_backlog_transition_authority`, `test_history_date_clock_sidecar`, `test_history_label_parity`, `test_history_write_order`, `test_prompts_attention`, `test_releases_line_writers`, `test_specs_metadata_duplicate_bullet`, `test_index_check_agent_records`. Release-gate and status-transition-gate tests are merged only into rows that keep every refusal code individually asserted (P16 "keep refusals individually detectable").
  - Depends on: E-01
  - Expected outcome: decision-table rows; coverage diff for `status_set`, `backlog`, `specs`, `research*`, `attention*`, `releases`, `check_engine` shows zero lost lines or branches.
  - Execution state: pending
- [ ] E-07 IPD batch: `tests/test_ipd_lifecycle_cli.py` (19 of 45), `tests/test_ipd_lint.py` (13 of 39; fold into its existing `RULES` table, whose row shape P16 cites as canonical), `tests/test_ipd_templates.py`, `tests/test_lifecycle_dirs.py`, `tests/test_lifecycle_gate_coverage.py`, `tests/test_scaffold_history_clock.py`. `livecorpus` tests are not candidates (they stay in the thorough tier).
  - Depends on: E-01
  - Expected outcome: decision-table rows; coverage diff for `ipd_*`, `executed_transition_gate`, `plan_*` modules shows zero lost lines or branches.
  - Execution state: pending
- [ ] E-08 CLI-surface and remaining all-zero modules: the rest of the 70 `offdhr` all-zero modules (for example `test_cli_parser_conflict_policy`, `test_subparser_descriptions`, `test_help_nontty_claim`, `test_human_renderer_agent_hint`, `test_severity_tier_contract`, `test_exit_vocabulary_boundary`, `test_no_project_exit_is_cannot_run`, `test_selector_type_containment`, `test_install_report_truth`, `test_install_source_option`, `test_uninstall_layout_artifacts`, `test_bidi_control_rejection`, `test_home_path_pattern_source`, `test_capture_command_stream_bounds`, `test_check_engine_metadata_region`, `test_check_engine_status_meta`, `test_check_recovery_fidelity`, `test_coverage_record`, `test_deselect_notice`, `test_explicit_dir_non_project`, `test_loaded_code`, `test_support_section`, `test_typecheck_gate`, `test_uncollected_test_modules`). Small single-concern modules whose tests are rows of a sibling module's table are moved into that table and the file removed. Conformance sweeps that are universal over declared leaves (`test_agent_surface_conformance`, `test_exit_contract_conformance`, `test_family_root_agent_conformance`, `test_shared_flag_honored`, `test_live_conformance_sweep`) keep their leaf axis; they are subprocess-driven, so their zero-unique status is a metric artifact and they are classified `keep` (or `speed-up`, carried to `c8bfp9`) by reading. Leak-sanitizer, exit-code and `aw.agent/v1` tests are merged only without loss.
  - Depends on: E-01
  - Expected outcome: every one of the 70 modules has a decision-table row (keep, consolidate into `<target>`, or delete with reason); coverage diff for the CLI, check, sanitizer and install modules shows zero lost lines or branches.
  - Execution state: pending

### Task group 4: shared fixture and child-level proof

- [ ] E-09 Add one shared copy-on-write temp git repository fixture (session-scoped template built once with `git init`, local identity and a minimal `.aw/records/` tree; a function-scoped fixture `shutil.copytree`s it per test) in a non-collected helper under `tests/` registered from the root `conftest.py`, and migrate to it the duplicate per-module repo builders in the modules E-02 to E-08 touched (authoring census: 263 `"git", "init"` call sites and 37 module-local `_make_repo`/`_init_repo`/`_git_init`-style helpers under `tests/`). A test that asserts on fresh-repo state (for example no commits) keeps its own setup and says why in a one-line docstring.
  - Depends on: E-05, E-06, E-07, E-08
  - Expected outcome: migrated modules pass under `-p randomly` and `-n 6`; a per-test mutation of the copied repo is not visible to another test (demonstrated by a test that writes a file and a second that asserts its absence, both in one worker); `rg -c '"git", "init"' tests` count before and after recorded.
  - Execution state: pending
- [ ] E-10 Child-level proof: full suite `-m ''` pass; collected count before (E-01) and after; union line and branch coverage after versus E-01 with every newly uncovered line or branch listed (target: none; any found is restored in this child, not deferred); hguae9 core per-module coverage table unchanged or higher; the hguae9 core wall-time guard passes; decision table row count equals the number of removed or merged node ids.
  - Depends on: E-02, E-03, E-04, E-09
  - Expected outcome: all measurements pasted in V-10; zero lost lines and branches.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 "Tabulated and table-driven tests" in `GUIDING_PRINCIPLES.md`: case id first, mandatory trailing `why`, aggregate failure message (accumulate pattern), and an explicit list of when NOT to tabulate (sequence or rollback order, idempotence pairs, consent transcripts, phase ordering, `assertRaises`, dynamic-versus-dynamic comparisons, outcome contrasts). Those stay separate tests with a one-line docstring saying why.
- P16 safety-gate traps: keep each refusal code individually asserted; use string literals, not production constants, in expected columns; keep tri-states three-valued.
- `tests/test_ipd_lint.py` `RULES` table comment is the canonical row shape; `tests/test_runner_profiles.py` (`ProfileNameGrammarTests.test_every_name_is_accepted_or_refused_by_the_grammar`) is the canonical aggregate message.
- `tests/conformance_matrix.py` (`run_cli`, `run_cli_tty`, `LIVE_SAFE_LEAVES`, `build_installed_project_template`, `clone_isolated_project`) already provides a session-template plus clone pattern for installed projects; E-09 mirrors it for bare repos rather than inventing a second shape.
- `pytest-randomly` is declared and must stay on; `conftest.pytest_xdist_auto_num_workers` caps at 6 workers.
- Subprocess-launched tests record no in-process coverage context (research `offdhr`), so the zero-unique metric under-reports them.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | 1331 of 3714 recorded test contexts have zero unique lines; 70 modules are entirely such | research `offdhr` |
| F-2 | 1922 of 8799 node ids are parametrize cases of 92 functions | authoring `--collect-only -q` count, `grep '\['` |
| F-3 | One module holds 997 node ids; its 900-case function is a 5 x 10 x 2 x 9 cross product whose verb axis is a formatting pass-through | `tests/test_descriptive_refusal_hoist.py` `REAL_NONEMPTY_VERBS`, `TEST_VALUES`, `FROZEN_SUFFIX_TABLE` |
| F-4 | Statusline tests use full Cartesian products, one of them over 9 domains at 20.5s | `_STATUSLINE_SWEPT_DOMAINS`, `itertools.product` in `test_box_renderer_invariants_exhaustive_sweep`; research `7ry5kv` durations |
| F-5 | Paired agent/json leaf tests duplicate argv construction over 67 leaves | `tests/test_usage_refusal_agent_record.py` |
| F-6 | Universal-over-leaves conformance sweeps are subprocess-driven, so their zero-unique status is not evidence of redundancy | `run_cli` builds `[sys.executable, "-m", "agent_workflows", ...]` in `tests/conformance_matrix.py` |
| F-7 | Repo builders are duplicated widely: 263 `"git", "init"` sites, 37 module-local repo helpers | `rg` counts at authoring |

## Proposed changes (ordered, validatable)

E-01 baseline -> E-02..E-04 matrix reductions (largest node-id savings, mechanical branch proof) -> E-05..E-08 subsystem batches, one commit each -> E-09 shared fixture over the touched modules -> E-10 child-level proof. Each batch is independently revertible because each is its own commit.

## Deferred / out of scope (with reason)

- Converting subprocess tests to in-process `cli.main`, caching install fixtures, removing sleeps, splitting long tests: speed work.
  - Carrier: c8bfp9
- Mutation spot-check of consolidated and deleted tests, flake check, final before/after report and CHANGELOG line.
  - Carrier: vgus66
- Structure, name and architecture pins: already removed by the previous child.
  - Carrier: tv72xy
- Reducing the LEAF axis of universal conformance sweeps: declined, because "every declared leaf" is the contract those sweeps enforce (a new leaf must be covered automatically); only value or permutation axes are reduced.
  - Carrier-Declined: the leaf axis is the behavior under test, not a combinatorial redundancy.

## Scope check

- Over-scope: none.
- Under-scope: none; the `livecorpus` and keep-category exclusions are deliberate (prompt `4ul37x` "Keep, regardless of speed").

## Required tests / validation

Per batch: the batch's test modules plus a branch-coverage diff over its source modules. At the end: full `python3 -m pytest tests/ -m ''` and bare `python3 -m pytest` (core), both pasted, plus the E-10 coverage comparison.

## Spec / documentation sync

N/A: no spec governs test layout; the decision-table research record is updated per batch. The CHANGELOG line is owned by `vgus66`.

## Open questions

### OQ-01: Parametrize or accumulate for consolidated tables?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from P16 and xdist behavior: use the accumulate pattern (one node id, aggregate message, `why` per row) when rows are cheap in-process calls, because per-case node ids cost collection and dispatch for no diagnostic gain; use `pytest.mark.parametrize` with readable ids when a row is expensive (subprocess, repo build), so `--dist=worksteal` can balance rows across workers.

### OQ-02: Do the four private delegating aliases in `test_descriptive_refusal_hoist.py` stay rows?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved: yes. Each alias is reached by a different verb implementation, so a divergence would be a real behavioral regression; the route axis costs 5x and is kept, while the verb and value products are reduced (E-02). If `tv72xy` already removed alias-identity assertions, only behavioral parity rows remain.

### OQ-03: What if a merged test is slower than the sum it replaces?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved: a consolidation is accepted only if the batch's measured duration does not rise; otherwise the rows are re-split by parametrize (OQ-01) so workers can balance them. Wall-time targets themselves are `c8bfp9`'s.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted baseline union line and branch totals, the census top 15 rows, and the decision-table research section heading where they are recorded.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted before and after `--collect-only -q` counts for the module, the reduced table's row count, and the per-module branch-coverage diff showing zero newly uncovered lines and branches.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted before and after node-id counts and sweep iteration counts, the sweep's before and after duration, and the branch-coverage diff for the statusline modules (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted 134-to-67 count, a run of the merged test with a temporary one-line break of the `--json` cannot-run path showing the failure names the mode, the revert with empty `git diff` on production code, and the coverage diff (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted decision-table rows for the runner batch, the batch's test run summary line, and the branch-coverage diff for the runner modules (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted decision-table rows for the records batch, the test summary line, and the branch-coverage diff (zero lost); for each merged gate test, the row showing its refusal code still asserted literally.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted decision-table rows, the test summary line, and the branch-coverage diff for the IPD modules (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted decision-table rows covering all 70 all-zero modules (count equals 70), list of removed files, the test summary line, and the coverage diff (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted isolation demonstration (write then assert-absent in one worker), migrated modules passing under `-n 6` with randomization (summary line and seed), and before and after `"git", "init"` counts.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: pasted full `-m ''` summary line, before and after collected counts, union line and branch totals before and after with the list of newly uncovered lines and branches (expected empty), the core per-module table comparison, the bare `python3 -m pytest` summary line, and the decision-table row count reconciliation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and explicit human approval, and only after `tv72xy` is executed. Work in an isolated worktree via `aw work begin 83nnyn`; commit each batch separately with `aw commit 83nnyn -- <paths>`; never push or tag; publish via `aw integration-lock -- git merge --ff-only <branch>`. Paste ACTUAL runner and coverage output in every V-item. On completion, run `aw ipd lint --phase pre-transition` and move the plan to `executed/` through the lifecycle tooling.
