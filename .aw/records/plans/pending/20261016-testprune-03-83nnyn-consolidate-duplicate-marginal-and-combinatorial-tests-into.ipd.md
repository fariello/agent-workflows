# IPD: Consolidate duplicate, marginal and combinatorial tests into table-driven tests without losing a covered line or branch

- Date: 2026-10-16
- Kind: child
- Concern: Prompt `4ul37x` (Set `testprune`) items 5 and 6 and its CONSOLIDATE section. Baseline research `offdhr` (main `6ea45c974`): of 3714 recorded in-process test contexts, 1331 cover no line that some other test does not also cover, and in 70 modules every recorded test is in that set. Measured at authoring (`pytest tests/ -m '' --collect-only -q -o addopts=""`, this worktree): 8799 collected, of which 1922 node ids are parametrize cases of just 92 functions; one function alone (`tests/test_descriptive_refusal_hoist.py::test_all_five_routes_match_frozen_table_for_nonempty_verbs`) contributes 900 cases, and that module 997 of the 8799. Duplicate and combinatorial tests cost collection, worker dispatch and maintenance without catching more regressions.
- Scope: Batch by subsystem. For each batch, read every candidate (the rows the `qqrgv3` decision table assigns to owner `83nnyn`, plus large parametrize matrices; the `offdhr` lists are authoring context only, because `offdhr` itself records that its per-test numbers under-record and "must not drive any deletion"), merge near-identical tests into one table-driven test (P16 row shape: case id first, trailing `why`), reduce combinatorial matrices to happy path, boundaries, one representative per equivalence class and every distinct error branch, fold defect-citing tests into rows that keep their id6 in `why`, introduce a shared copy-on-write temp git repo helper for the duplicated per-module repo builders the batch touches, and prove per batch with `qqrgv3`'s `percov_analyze --compare` (line and arc) that no line or branch of `agent_workflows/` lost its last covering test. Records one decision-table row per consolidated or deleted node id. Converts no subprocess test to in-process and does no timing work (child `c8bfp9`).
- Scope-Paths: tests/, conftest.py, .aw/records/research/*testprune*
- Item-Dependencies: executed:tv72xy
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: high
- Set: testprune
- Order: 3
- Highest E allocated: 11
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 83nnyn
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): status set to reviewed
- 2026-10-16 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009, PR-010, PR-011
- 2026-10-16 to-review (aw set): authored from prompt 4ul37x (Set testprune) with baseline research offdhr/7ry5kv

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every duplicate, marginal and combinatorial test identified by measurement is merged into a table-driven test or recorded as deleted with a reason, cutting collected node ids substantially while union line and branch coverage of `agent_workflows/` and the hguae9 `core` per-module coverage stay at or above the pre-batch baseline.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Per-batch protocol (applies to E-02 through E-08; each is one subsystem, committed via `aw commit 83nnyn -- <paths>`; a batch spanning many modules (E-05, E-06, E-08) is worked and committed in module groups of at most about ten modules, each group with its own test run and decision-table rows, so a long batch never has to be held in one pass and each group stays independently revertible; the batch's `percov_analyze --compare` runs once after its last group): (a) list candidates from the `qqrgv3` decision table (rows whose owner is `83nnyn`, plus the identical/subset groups and unique line/arc counts in `percov.json`) and the parametrize census of E-01; module names and counts quoted below from research `offdhr` are AUTHORING CONTEXT ONLY (that record states its numbers under-record and "must not drive any deletion"), so a listed module the decision table does not assign to `83nnyn` is recorded `keep` with that reason, and a module the table assigns that is not listed below is still processed; (b) READ each candidate and its nearest covering sibling: equal lines are not equal assertions, so a candidate is merged only when its assertions are a subset of the surviving row's, and otherwise kept with a decision-table reason; (c) a test the `qqrgv3` classifier flags `read-required` (no recorded coverage) or `protected` is classified by reading, never by the 0-unique metric, and a protected test is never deleted; (d) a test citing a backlog id6, plan id6 or incident becomes a row whose `why` keeps that id; (e) never weaken an assertion; (f) re-run the instrumented suite with `python3 -m tests.tools.percov_run --out <dir>` and diff with `python3 -m tests.tools.percov_analyze <dir> --compare <E-01 dir>`, restricting the reported lost lines and arcs to the batch's source modules (any lost line or arc outside them is also investigated, not ignored); before deleting a whole file or renaming a test, run `git grep -n <file-or-test-name>` over `agent_workflows/`, `tools/`, `.aw/records/specs/` and `.aw/records/backlog/` and over `tests/` for `from tests.<module> import` (for example `tests/test_shared_flag_honored.py` imports `REQUIRED_LEAVES` and `_capture_cli` from `tests/test_usage_refusal_agent_record.py`), and keep or move every imported name; (g) append one decision-table row per affected node id (node id, category `consolidate`/`delete-duplicate`/`delete-marginal`/`keep`, surviving node id, reason) to the `qqrgv3` research record's "Recorded deletions" table, with `83nnyn` as child id6 and the batch commit.

### Task group 1: baseline for this child

- [ ] E-01 At this child's starting commit, regenerate per-test line+branch contexts with the `qqrgv3` tooling, NOT pytest-cov flags (pytest-cov's `--cov-context=test` labels contexts differently and does not attribute subprocess children, so a comparison against it reports spurious losses; `qqrgv3` F-7): `python3 -m tests.tools.percov_run --out .aw/state/percov/83nnyn-base`, then `python3 -m tests.tools.percov_analyze .aw/state/percov/83nnyn-base` and `python3 -m tests.tools.classify .aw/state/percov/83nnyn-base`. Refuse to proceed if `meta.json` `pytest_exit` is nonzero (fix or record the pre-existing failures first; `qqrgv3` E-02 states truncated coverage cannot drive decisions). Record in the `qqrgv3` decision-table research (new section `83nnyn baseline`): the run directory and `meta.json` HEAD, union line and branch totals, the hguae9 core per-module coverage table (`python3 -m tests.tools.core_measure --out <dir>`, from `hguae9` E-02), the list of rows the refreshed classifier assigns to owner `83nnyn`, the per-batch durations of the E-02..E-08 target modules (`--durations=0` from `junit.xml`, needed by OQ-03), and a parametrize census (cases per function from `--collect-only -q -o addopts=""`, functions with at least 9 cases, sorted descending).
  - Depends on: none
  - Expected outcome: baseline directory, totals, owner list and census recorded. Census is re-derived at execution and is the bar; the authoring and review measurements are context only (review HEAD `6b16af225`: 9496 collected, 2171 parametrize cases; descriptive_refusal_hoist 900 and 90, usage_refusal_agent_record `test_handler_usage_refusal_across_modes` 102 and the agent/json leaf pair 69 and 69, shared_flag_honored 69/51/51/33/33, statusline_stop_tally 60, agent_surface_conformance 51/33, statusline_visible_width 32).
  - Execution state: pending

### Task group 2: combinatorial matrices (boundary and equivalence reduction)

- [ ] E-02 Reduce `tests/test_descriptive_refusal_hoist.py`: the 900-case and 90-case functions are the cross product routes(5) x verbs(10) x bound_length(2) x values(9). Keep EVERY route x EVERY value class x both `bound_length` settings against `FROZEN_SUFFIX_TABLE` for one representative verb plus the empty verb (the value axis is where the branches of `attention_contract.refuse_unsafe_descriptive` are: `None`, accepted, empty, newline, CR, control char, late control char past the bound, over-length), ADD the missing length boundary rows (`"x" * 300` accepted and `"x" * 301` refused with `(301 > 300)` under `bound_length=True`, both accepted under `False`; `TEST_VALUES` today has 340 and 1200 but nothing at the boundary, so an off-by-one in `MAX_DESCRIPTIVE_LEN` comparison is undetected), and keep EVERY verb against one rejecting value to prove the verb prefix is rendered for each (the verb axis is a formatting pass-through, one equivalence class). Rows are cheap in-process calls, so per OQ-01 they are ONE accumulate table (case id first, expected literal, trailing `why`, aggregate message naming every failing route/value/verb), not parametrize cases. `test_bound_length_asymmetry_survived` becomes rows of that table (its three asymmetry pairs are a subset of the table's rows); `test_releases_run_new_cli_empty_verb_single_prefix` stays a separate test (it drives `releases.run_new`, a different surface).
  - Depends on: E-01
  - Expected outcome: every (route, value, bound_length) combination for the representative and empty verb, every verb, and the two new boundary rows are asserted against string literals in one table; `percov_analyze --compare` against the E-01 baseline lists zero lines or arcs newly uncovered in `attention_contract`, `backlog`, `specs`, `status_set`, `research_cmd`, `releases`; the module's before and after collected counts are recorded as context, not as the bar.
  - Execution state: pending
- [ ] E-03 Collapse the statusline parametrize matrices (node ids, not combinations): `tests/test_statusline_stop_tally.py::TestStatuslineStopTallyRendering::test_statusline_rectangular_with_badges` (stop_level 5 x tally 3 x styled 2 x unicode 2 = 60), `tests/test_statusline_visible_width.py::test_statusline_box_is_rectangular` (32), and the two 16-case sweeps in `tests/test_statusline_ascii_mode.py`. These are cheap in-process renders (all three modules, 146 node ids, ran in 0.66s serial at review), so collapse each parametrized product into ONE accumulate test that iterates the FULL product in a loop (case id per combination, aggregate message naming every failing combination, `why` per invariant), keeping every combination and every assertion: node ids drop with zero detection loss. Do NOT substitute a pairwise covering array for these: pairwise provably misses 3-way-only defects (plan `mat9bt` F-06: 288 of 7,776 statusline combinations failed a 3-way mutation that zero pairwise rows caught), and the full product here costs milliseconds. `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_exhaustive_sweep` (the `slow`, `timeout(300)` full product over `_STATUSLINE_SWEPT_DOMAINS`) is NOT a reduction candidate: `mat9bt` OQ-01 deliberately kept it as the exhaustive companion of the pairwise fast arm (`test_box_renderer_invariants_across_swept_inputs`, which uses the existing `generate_pairwise_covering_array`); record it `keep` (or `speed-up`, carried to `c8bfp9`, which owns its wall time) with that reason. Invariants asserted are unchanged.
  - Depends on: E-01
  - Expected outcome: every combination the old parametrized products asserted is still asserted (the loop's combination count equals the old product's size, derived from the domains in the test, not a hand literal); a deliberately broken renderer row (V-03) fails the accumulate test naming the combination; `percov_analyze --compare` lists zero lost lines or arcs in `render_stream`, `term`, `lifecycle_style`; the exhaustive sweep is unchanged and recorded `keep`/`speed-up`.
  - Execution state: pending
- [ ] E-04 Merge mode-pair leaf matrices without reducing the leaf axis: `tests/test_usage_refusal_agent_record.py::test_required_arg_leaf_agent_mode` and `::test_required_arg_leaf_json_mode` (69 + 69 at review HEAD, both in-process via `_capture_cli`, over `REQUIRED_LEAVES`) become one parametrized-per-leaf test asserting both the `--agent` cannot-run record (schema-valid via `agent_schema.validate_agent_record`, `kind` `error`, `outcome` `cannot-run`, `exit` 2, `next` `aw <leaf> --help`, no `/home/` or `/tmp/` leak) and the `--json` cannot-run object (`status` `cannot-run`, `exit_code` 2, a `next_actions` entry whose `command` is `aw <leaf> --help`), with mode as an accumulate column. Every assertion either function makes today is kept (the union, nothing dropped). Keep the names `REQUIRED_LEAVES` and `_capture_cli` importable from this module, because `tests/test_shared_flag_honored.py` imports both. Apply the same merge to any other pair in the E-01 census whose two functions share argv construction and differ only in an output mode, provided the merged test reports every failing mode at once. `test_handler_usage_refusal_across_modes` already carries mode as a column and is not a candidate.
  - Depends on: E-01
  - Expected outcome: the two per-leaf functions become one, so per-leaf node ids halve (re-derived from `REQUIRED_LEAVES` at execution); every leaf is still exercised in both modes; a temporarily broken `--json` cannot-run path fails the merged test with the mode named (V-04); `tests/test_shared_flag_honored.py` still collects and passes; `percov_analyze --compare` zero lost.
  - Execution state: pending

### Task group 3: duplicate and marginal tests, by subsystem

- [ ] E-05 Runner batch (authoring-context counts from `offdhr`; the work list is the E-01 owner list, per protocol (a)): zero-unique candidates in `tests/test_oc_runipd.py` (60 of 105 recorded), `tests/test_runner_shared.py` (32 of 71), `tests/test_agy_runipd_cli.py` (29 of 38), `tests/test_finalize_sendback.py` (16 of 31), `tests/test_orchestrator_retirement.py` (15 of 30), `tests/test_runner_backlog_close_behavior.py` (12 of 30), plus the runner-named modules in the `offdhr` all-zero list (`test_agy_failed_state_parity`, `test_lane_reaper_callshape`, `test_prior_attempt_projection`, `test_retry_class_mapping`, `test_run_cli_human_redaction`, `test_run_dir_outcomes_parent_is_guaranteed`, `test_run_progress_count`, `test_run_summary_visible_width`, `test_runner_safety_probe_memo`, `test_runs_flag_position_parity`). Host-parity pairs (oc versus agy) become one test with a HOST column. Apply the per-batch protocol.
  - Depends on: E-01
  - Expected outcome: decision-table rows for every candidate; coverage diff for `oc_runipd`, `agy_runipd`, `runner_shared`, `finalize*`, `run_*` modules shows zero lost lines or branches.
  - Execution state: pending
- [ ] E-06 Records batch (authoring-context counts from `offdhr`; the work list is the E-01 owner list, per protocol (a)): `tests/test_status_set.py` (22 of 44), `tests/test_backlog.py` (17 of 33), `tests/test_group_verb_policy.py` (17 of 28; includes the 9-case setid warn matrices), `tests/test_research_index.py` (9 of 28), `tests/test_attention.py` (10 of 37), plus all-zero modules `test_attention_blind_spot`, `test_attention_degraded_item`, `test_backlog_close_host_label`, `test_backlog_gate_follows_status`, `test_backlog_history_dedup_parity`, `test_backlog_transition_authority`, `test_history_date_clock_sidecar`, `test_history_label_parity`, `test_history_write_order`, `test_prompts_attention`, `test_releases_line_writers`, `test_specs_metadata_duplicate_bullet`, `test_index_check_agent_records`. Release-gate and status-transition-gate tests are merged only into rows that keep every refusal code individually asserted (P16 "keep refusals individually detectable").
  - Depends on: E-01
  - Expected outcome: decision-table rows; coverage diff for `status_set`, `backlog`, `specs`, `research*`, `attention*`, `releases`, `check_engine` shows zero lost lines or branches.
  - Execution state: pending
- [ ] E-07 IPD batch (authoring-context counts from `offdhr`; the work list is the E-01 owner list, per protocol (a)): `tests/test_ipd_lifecycle_cli.py` (19 of 45), `tests/test_ipd_lint.py` (13 of 39; fold into its existing `RULES` table, whose row shape P16 cites as canonical), `tests/test_ipd_templates.py`, `tests/test_lifecycle_dirs.py`, `tests/test_lifecycle_gate_coverage.py`, `tests/test_scaffold_history_clock.py`. `livecorpus` tests are not candidates (they stay in the thorough tier).
  - Depends on: E-01
  - Expected outcome: decision-table rows; coverage diff for `ipd_*`, `executed_transition_gate`, `plan_*` modules shows zero lost lines or branches.
  - Execution state: pending
- [ ] E-08 CLI-surface and remaining modules: every remaining E-01 owner-list row, and, so the `offdhr` candidate list is closed out explicitly, the rest of the 70 `offdhr` all-zero modules (authoring context; `test_descriptive_refusal_hoist` is E-02's) (for example `test_cli_parser_conflict_policy`, `test_subparser_descriptions`, `test_help_nontty_claim`, `test_human_renderer_agent_hint`, `test_severity_tier_contract`, `test_exit_vocabulary_boundary`, `test_no_project_exit_is_cannot_run`, `test_selector_type_containment`, `test_install_report_truth`, `test_install_source_option`, `test_uninstall_layout_artifacts`, `test_bidi_control_rejection`, `test_home_path_pattern_source`, `test_capture_command_stream_bounds`, `test_check_engine_metadata_region`, `test_check_engine_status_meta`, `test_check_recovery_fidelity`, `test_coverage_record`, `test_deselect_notice`, `test_explicit_dir_non_project`, `test_loaded_code`, `test_support_section`, `test_typecheck_gate`, `test_uncollected_test_modules`). Small single-concern modules whose tests are rows of a sibling module's table are moved into that table and the file removed (only after the protocol (f) `git grep` for citations and `from tests.<module> import` users; a citation in a spec or a live backlog item is updated in the same commit). `tests/test_uncollected_test_modules.py` and `tests/test_deselect_notice.py` guard the suite's own collection and are `keep` unless merged into each other without loss. Conformance sweeps that are universal over declared leaves (`test_agent_surface_conformance`, `test_exit_contract_conformance`, `test_family_root_agent_conformance`, `test_shared_flag_honored`, `test_live_conformance_sweep`) keep their leaf axis; they are subprocess-driven (the `offdhr` zero-unique status was a measurement artifact) and protected by `qqrgv3`'s classifier, so they are classified `keep` (or `speed-up`, carried to `c8bfp9`) by reading. Leak-sanitizer, exit-code and `aw.agent/v1` tests are merged only without loss.
  - Depends on: E-01
  - Expected outcome: every E-01 owner-list module and every one of the 70 `offdhr` all-zero modules (a fixed historical list, so its count is a stable bar) has a decision-table row across E-02..E-08 (keep, consolidate into `<target>`, or delete with reason); `percov_analyze --compare` zero lost lines or arcs for the CLI, check, sanitizer and install modules.
  - Execution state: pending

### Task group 4: shared fixture and child-level proof

- [ ] E-09 Add one shared temp git repository template helper in a non-collected module `tests/repo_template.py` (no `test_` prefix, beside `tests/support.py`): a per-process, lazily built, cached template (`git init`, local `user.name`/`user.email`, a minimal `.aw/records/` tree, no commits; built in a `tempfile.mkdtemp` removed at exit) and a plain function `copy_template_repo(dest: Path) -> Path` that `shutil.copytree(..., symlinks=True)`s it. It MUST be a plain function, not only a pytest fixture: 430 of 557 test modules are `unittest.TestCase` classes, into whose methods pytest does not inject function-scoped fixtures, and `make test-serial` runs `python3 -m unittest discover`, which never loads `conftest.py`. A thin optional pytest fixture wrapper (`template_repo`, in the root `conftest.py`, calling the same function with `tmp_path`) is allowed for pytest-style modules. Per-process caching is correct under xdist (each worker builds its own template; nothing is shared across processes). Add behavioral tests in a new `tests/test_repo_template.py`: two copies are independent (a file written and committed in one is absent from the other and from the template), a copy has no commits (`git rev-parse --verify -q HEAD` exits 1), a copy keeps the local identity, and `git rev-parse --show-toplevel` in a copy is the copy. Review probe of this mechanism (scratch, `git 2.43.0`): copy B did not see A's committed file, template unchanged, B `HEAD` absent (exit 1), B `user.name` preserved, toplevel equals B; `git init` plus config 9.3ms versus `copytree` 3.7ms per repo.
  - Depends on: none
  - Expected outcome: `tests/repo_template.py` and `tests/test_repo_template.py` exist; the new tests pass under pytest (`-n 6`, randomized) and under `python3 -m unittest tests.test_repo_template`; `tests/test_uncollected_test_modules.py` passes.
  - Execution state: pending
- [ ] E-11 Migrate to `copy_template_repo` the duplicate per-module repo builders in the modules E-02 to E-08 touched (review census at HEAD `6b16af225`: 328 `"git", "init"` occurrences across 186 files and 44 files defining a `_make_repo`/`_init_repo`/`_create_repo`/`_git_init`-style helper; authoring had 263 and 37 with a narrower pattern). Migrate a builder only when it is a plain empty-repo init plus identity; a builder that installs, commits a fixture, or sets other config either stays or copies the template and then applies its own steps. A test that asserts on fresh-repo state the template differs from keeps its own setup and says why in a one-line docstring. Modules not touched by E-02 to E-08 are left to `c8bfp9` E-06, which reuses this helper.
  - Depends on: E-05, E-06, E-07, E-08, E-09
  - Expected outcome: every migrated module passes under `-n 6` with randomization (seed recorded) and under `python3 -m unittest <module>` when it is a `TestCase` module; the `rg -c '"git", "init"' tests` total before and after is recorded; `percov_analyze --compare` zero lost.
  - Execution state: pending
- [ ] E-10 Child-level proof: full suite `python3 -m pytest tests/ -m ''` pass; collected count before (E-01) and after (context, not the bar); a fresh `percov_run` plus `percov_analyze --compare <E-01 dir>` over all of `agent_workflows/` with every newly uncovered line or arc listed (target: none; any found is restored in this child, not deferred); `core_measure` core per-module table unchanged or higher than E-01 (no module drops); bare `python3 -m pytest` passes including the hguae9 core wall-time guard; per-batch durations of the touched modules versus E-01 (OQ-03: a batch whose duration rose is re-split before this item completes); the decision-table rows appended by this child reconcile with the removed and merged node ids derived from `git diff <E-01 HEAD>..HEAD -- tests/` and the before/after `--collect-only` lists; `aw research index --check` passes after the record edits.
  - Depends on: E-02, E-03, E-04, E-11
  - Expected outcome: all measurements pasted in V-10; zero lost lines and branches.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 "Tabulated and table-driven tests" in `GUIDING_PRINCIPLES.md`: case id first, mandatory trailing `why`, aggregate failure message (accumulate pattern), and an explicit list of when NOT to tabulate (sequence or rollback order, idempotence pairs, consent transcripts, phase ordering, `assertRaises`, dynamic-versus-dynamic comparisons, outcome contrasts). Those stay separate tests with a one-line docstring saying why.
- P16 safety-gate traps: keep each refusal code individually asserted; use string literals, not production constants, in expected columns; keep tri-states three-valued.
- `tests/test_ipd_lint.py` `RULES` table comment is the canonical row shape; `tests/test_runner_profiles.py` (`ProfileNameGrammarTests.test_every_name_is_accepted_or_refused_by_the_grammar`) is the canonical aggregate message.
- `tests/conformance_matrix.py` (`run_cli`, `run_cli_tty`, `LIVE_SAFE_LEAVES`, `build_installed_project_template`, `clone_isolated_project`) already provides a template plus `shutil.copytree` clone pattern for installed projects; E-09 mirrors it for bare repos as plain functions rather than inventing a second shape.
- 430 of 557 `tests/test_*.py` modules use `unittest.TestCase` (review `rg -l` count), and `make test-serial` (`python3 -m unittest discover -s tests -t .`) never loads `conftest.py`, so a shared helper must be callable as a plain function (E-09).
- `qqrgv3` owns the measurement tooling (`tests/tools/percov_run.py`, `percov_analyze.py` with `--compare`, `classify.py`) and the decision-table research record with its "Recorded deletions" table; `hguae9` owns `tests/tools/core_measure.py` and the core wall-time guard. This child consumes both and builds no measurement tooling.
- Plan `mat9bt` (executed) deliberately kept the exhaustive statusline sweep as a `slow` companion of a pairwise fast arm because pairwise misses 3-way defects (its F-06, OQ-01).
- `pytest-randomly` is declared and must stay on; `conftest.pytest_xdist_auto_num_workers` caps at 6 workers.
- Subprocess-launched tests recorded no coverage context in the `offdhr` baseline, so its zero-unique metric under-reports them; `qqrgv3`'s plugin attributes subprocess children to the spawning node id, and its classifier still flags uncovered tests `read-required`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | 1331 of 3714 recorded test contexts have zero unique lines; 70 modules are entirely such. Authoring context only: `offdhr`'s own CORRECTION section says these numbers under-record and "must not drive any deletion"; `qqrgv3`'s decision table supersedes them | research `offdhr` "CORRECTION (2026-10-16" |
| F-2 | 1922 of 8799 node ids are parametrize cases of 92 functions at authoring; 2171 of 9496 at review HEAD `6b16af225` (so counts drift and are re-derived in E-01) | `--collect-only -q -o addopts=""`, `grep '\['` |
| F-3 | One module holds 997 node ids; its 900-case function is a 5 x 10 x 2 x 9 cross product whose verb axis is a formatting pass-through | `tests/test_descriptive_refusal_hoist.py` `REAL_NONEMPTY_VERBS`, `TEST_VALUES`, `FROZEN_SUFFIX_TABLE` |
| F-4 | Statusline tests use parametrized full Cartesian products (cheap: 146 node ids in 0.66s serial at review); the 9-domain exhaustive sweep (20.5s, `slow`) is the deliberate companion of an existing pairwise fast arm, not a redundancy | `_STATUSLINE_SWEPT_DOMAINS`, `generate_pairwise_covering_array`, `test_box_renderer_invariants_exhaustive_sweep` docstring "preserved in slow suite (plan mat9bt E-05)"; research `7ry5kv` durations |
| F-5 | Paired agent/json leaf tests duplicate argv construction over `REQUIRED_LEAVES` (67 at authoring, 69 at review) | `tests/test_usage_refusal_agent_record.py` `test_required_arg_leaf_agent_mode`, `test_required_arg_leaf_json_mode`; `tests/test_shared_flag_honored.py` imports `REQUIRED_LEAVES, _capture_cli` from it |
| F-6 | Universal-over-leaves conformance sweeps are subprocess-driven, so their zero-unique status is not evidence of redundancy | `run_cli` builds `[sys.executable, "-m", "agent_workflows", ...]` in `tests/conformance_matrix.py` |
| F-7 | Repo builders are duplicated widely: 263 `"git", "init"` sites and 37 helpers at authoring; 328 occurrences in 186 files and 44 helper-defining files at review with a wider helper pattern | `rg` counts |
| F-8 | `TEST_VALUES` in the descriptive-refusal hoist test has no value at the length boundary (300/301), so the 900-case product never tests the `len(value) > max_len` edge | `tests/test_descriptive_refusal_hoist.py` `VAL_LEN340`, `VAL_LEN1200`; `attention_contract.refuse_unsafe_descriptive` "if len(value) > max_len" |

## Proposed changes (ordered, validatable)

E-01 baseline -> E-02..E-04 matrix reductions (largest node-id savings, mechanical branch proof) -> E-05..E-08 subsystem batches, one commit each -> E-09 shared repo-template helper and its tests (independent; may run any time after E-01) -> E-11 migrate the touched modules' builders -> E-10 child-level proof. Each batch is independently revertible because each is its own commit.

## Deferred / out of scope (with reason)

- Converting subprocess tests to in-process `cli.main`, caching install fixtures, removing sleeps, splitting long tests: speed work.
  - Carrier: c8bfp9
- Mutation spot-check of consolidated and deleted tests, flake check, final before/after report and CHANGELOG line.
  - Carrier: vgus66
- Structure, name and architecture pins: already removed by the previous child.
  - Carrier: tv72xy
- Reducing the exhaustive statusline sweep (`test_box_renderer_invariants_exhaustive_sweep`) or other untouched-module repo builders: its wall time and the remaining builders are speed work.
  - Carrier: c8bfp9
- Reducing the LEAF axis of universal conformance sweeps: declined, because "every declared leaf" is the contract those sweeps enforce (a new leaf must be covered automatically); only value or permutation axes are reduced.
  - Carrier-Declined: the leaf axis is the behavior under test, not a combinatorial redundancy.

## Scope check

- Over-scope: none.
- Under-scope: none; the `livecorpus` and keep-category exclusions are deliberate (prompt `4ul37x` "Keep, regardless of speed").

## Required tests / validation

Per batch: `python3 -m pytest <batch modules> -o addopts="" -n 6` (randomized, seed pasted) plus `python3 -m tests.tools.percov_run --out <dir>` and `python3 -m tests.tools.percov_analyze <dir> --compare .aw/state/percov/83nnyn-base` restricted to the batch's source modules. E-09: `python3 -m pytest tests/test_repo_template.py tests/test_uncollected_test_modules.py -o addopts=""` and `python3 -m unittest tests.test_repo_template`. At the end: full `python3 -m pytest tests/ -m ''` and bare `python3 -m pytest` (core), both pasted, plus the E-10 coverage comparison.

## Spec / documentation sync

N/A: no spec governs test layout, and no production code changes. The `qqrgv3` decision-table research record is updated per batch and re-indexed with `aw research index`. If a removed or renamed test is cited by a spec or a live backlog item (protocol (f)), the citation is updated in the same commit and the `.spec.md` path is declared at finalize with `--scope-reason`. The CHANGELOG line is owned by `vgus66`.

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
  - Required evidence: pasted `meta.json` (HEAD, `pytest_exit: 0`, core, worker count), `percov_analyze` union line and arc totals, the `core_measure` per-module table totals, the count and list head of rows the classifier assigns to owner `83nnyn`, the census top 15 rows, the per-batch durations, and the `83nnyn baseline` section heading in the decision-table research record.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted before and after `--collect-only -q` counts for the module (context); the table's case ids showing every route x value x `bound_length` for the representative and empty verb, every verb, and the 300/301 boundary rows; a run with a temporary one-line mutation of `attention_contract.refuse_unsafe_descriptive` (for example `>` changed to `>=` in the length comparison) showing the table FAILS naming the boundary row and listing every failing row in one message, then the revert with empty `git diff -- agent_workflows/`; the module's pass line; and `percov_analyze --compare` output for the six source modules showing zero newly uncovered lines and arcs.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted before and after node-id counts (context); for each collapsed test, the old product size (from the old parametrize domains) next to the loop's combination count derived from the new test's domains (must be equal); a run with a temporary one-line break in rendered output (for example one extra column on the bottom border in `render_stream.format_statusline_lines` for one stop level) showing the accumulate test fails and names the affected combinations, then the revert with empty `git diff -- agent_workflows/`; the modules' pass line; an unchanged `git diff` of `test_box_renderer_invariants_exhaustive_sweep` and its decision-table row; and `percov_analyze --compare` for `render_stream`, `term`, `lifecycle_style` (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted per-leaf node-id counts before and after (after equals `len(REQUIRED_LEAVES)`, re-derived); a run of the merged test with a temporary one-line break of the `--json` cannot-run path (for example `renderers.emit_usage_refusal` passing a wrong `next_cmd` only when `ctx.is_json`) showing the failure names the `json` mode while the `agent` mode still passes, then the revert with empty `git diff -- agent_workflows/`; `tests/test_shared_flag_honored.py` pass line; and `percov_analyze --compare` (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted decision-table rows for the runner batch (every E-01 owner-list runner module plus every module named in E-05 has a row), the batch's test run summary line with seed, the citation `git grep` output for every removed file or renamed test, and `percov_analyze --compare` for the runner modules (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted decision-table rows for the records batch, the test summary line with seed, the citation `git grep` output for every removed file or renamed test, and `percov_analyze --compare` (zero lost); for each merged gate test, the table row showing its refusal code still asserted as a string literal.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted decision-table rows, the test summary line with seed, the citation `git grep` output for every removed file or renamed test, and `percov_analyze --compare` for the IPD modules (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted decision-table rows for this batch; a reconciliation listing each of the 70 `offdhr` all-zero modules with the E-item and decision-table row that covers it (count equals 70) and each E-01 owner-list module with its row; list of removed files with their citation `git grep` output; the test summary line; and `percov_analyze --compare` (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted `tests/test_repo_template.py` source of the isolation, no-commit, identity and toplevel tests; their pass lines under `python3 -m pytest tests/test_repo_template.py -o addopts="" -n 6` (seed) and under `python3 -m unittest tests.test_repo_template`; `tests/test_uncollected_test_modules.py` pass line.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: pasted list of migrated modules with the builder each replaced, the modules' pass line under `-n 6` (seed) and, for `TestCase` modules, under `python3 -m unittest <modules>`; the list of kept builders with their one-line reason; before and after `rg -c '"git", "init"' tests` totals; and `percov_analyze --compare` (zero lost).
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: pasted full `-m ''` summary line, before and after collected counts, `percov_analyze` union line and arc totals before and after with the `--compare` list of newly uncovered lines and arcs (expected empty), the `core_measure` per-module table comparison, the bare `python3 -m pytest` summary line (core wall-time guard passing), the per-batch duration table versus E-01, the decision-table row reconciliation against the removed and merged node ids from `git diff` and the `--collect-only` lists, and `aw research index --check` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and explicit human approval (all open questions resolved), and only after `tv72xy` is executed (Item-Dependencies), in an isolated worktree (`aw work begin 83nnyn`, or the runner's lane). Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit (for example a spec or backlog citation that must follow a removed test, or a `pyproject.toml` `testpaths` entry naming a removed module) is allowed when needed and justified at finalize (`--scope-reason`), and a declared but unmodified path is acknowledged (`--scope-ack`). This plan changes no production code: every temporary mutation under `agent_workflows/` is reverted and shown reverted with an empty `git diff -- agent_workflows/`. Never weaken an assertion to make a test pass; a consolidation that cannot keep every assertion is recorded `keep`. Respect `hguae9`'s `core` marker: a `core` test may be consolidated but its behavioral assertions keep running in the core tier. Commit each batch separately via `aw commit 83nnyn -- <paths>` (never `git add -A`); never push or tag. You MUST paste the ACTUAL runner and coverage output in each V-item; never claim a pass you did not run. Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize and the move to `executed/`; executed by hand, finish with `aw ipd lint --phase pre-transition` conforming and then `aw ipd finalize 83nnyn` (never a hand `git mv`), and publish with `aw integration-lock -- git merge --ff-only <branch>`.
