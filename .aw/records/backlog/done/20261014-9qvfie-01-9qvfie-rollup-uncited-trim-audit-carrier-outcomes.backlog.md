- Id: 9qvfie
- Status: done
- Graduated-To: trimcarry
- Set: 9qvfie
- Priority: low
- Work-Kind: chore
- Summary: Rollup of uncited trim-deleted test audit carrier-needed outcomes

## Workflow history
- 2026-10-17 done (aw backlog): closed by aw agy run: IPD e5jijr executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261016-trimcarry-00-e5jijr-carry-the-uncited-trim-audit-carrier-needed-outcomes-to-reso.ipd.md, .aw/records/plans/executed/20261016-trimcarry-01-24h56i-restore-the-deleted-benchmark-runners-and-reports-tests-and.ipd.md, .aw/records/plans/executed/20261016-trimcarry-02-x9z0ve-restore-the-env-limited-run-evidence-completion-tests-with-a.ipd.md, .aw/records/plans/executed/20261016-trimcarry-03-8dyt88-re-measure-surviving-reach-for-every-rollup-key-and-pass-sha.ipd.md, .aw/records/plans/executed/20261016-trimcarry-04-we3kkb-classify-each-test-name-the-recreated-files-did-not-restore.ipd.md, .aw/records/plans/executed/20261016-trimcarry-05-rf1xxr-mutation-probe-the-reached-rollup-properties-on-a-bounded-bu.ipd.md, .aw/records/plans/executed/20261016-trimcarry-06-z2xs98-file-grouped-backlog-items-for-every-rollup-gap-and-reconcil.ipd.md); evidence .aw/records/plans/executed/20261016-trimcarry-00-e5jijr-carry-the-uncited-trim-audit-carrier-needed-outcomes-to-reso.ipd.md
- 2026-10-16 graduated (aw backlog): graduated by run run-20261016T145446Z-2140972: 24h56i, 8dyt88, e5jijr, rf1xxr, we3kkb, x9z0ve, z2xs98
- 2026-10-15 created (aw backlog): Rollup of uncited trim-deleted test audit carrier-needed outcomes

Rollup carrier for 770 carrier-needed outcomes from the uncited trim-deleted test audit (findings doc hpjj44, .aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md).

Carrier-needed outcomes covered:
1. unprovable (1 property):
   - PROP-02: agent_workflows/benchmark_metrics.py::compute_aggregate_metrics (reached by tests/test_benchmark_runners_reports.py; survivor error: mutant run could not produce junit XML; control killed).
2. triaged-not-mutated (764 items):
   - 38 budget-exhausted candidate keys from the mutation shortlist (details in hpjj44 ## Triaged not mutated and ## Mutation totals).
   - 709 cost-cap candidate keys exceeding the top-40 shortlist budget (details in hpjj44 ## Triaged not mutated).
   - 17 pass-shared test files with no exclusive reach (details in hpjj44 ## Triaged not mutated: test_agy_runipd_shim.py, test_askme_blocking_gate.py, test_attention_compact.py, test_auto_index_on_mutation.py, test_awretrofit_install_selfheal.py, test_check_clean_worktree_untracked_repo_root.py, test_cli_attention_live.py, test_cli_commands.py, test_cli_ipd_board.py, test_cli_plans_board.py, test_dirty_clean_detection.py, test_format_run_summary.py, test_git_integration_lock.py, test_integration_lock_contention.py, test_lane_merge_conflicts.py, test_precommit_unstaged_preservation.py, test_runner_phase_timing.py).
3. replay-env-limited (1 test file):
   - tests/test_run_evidence_completion.py (84 removed funcs; replay requires specialized multi-agent environment).
4. recreated with missing test names (4 test files):
   - tests/test_lane_input_manifest.py (4 missing deleted test names: test_its_docstring_states_it_has_no_consumer, test_part_i_the_manifest_file_has_no_write_bit, test_part_ii_every_materialized_input_has_no_write_bit, test_part_iii_lane_inputs_file_has_no_write_bit).
   - tests/test_release_readiness.py (19 missing deleted test names).
   - tests/test_run_analytics_cli.py (79 missing deleted test names).
   - tests/test_run_summary_table.py (34 missing deleted test names).
