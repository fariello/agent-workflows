---
id: hwuvpx
created: 20261017
set: testprune
order: 02
topic: [testing]
model: 
kind: assessment
status: active
outcome: informational
summary: Per-test coverage and classification baseline across 576 modules and 9801 tests
consumed-by: [tv72xy, 83nnyn, c8bfp9, vgus66]
---

# Test Prune Decision Table (Baseline Run 2026-10-17)

## Measurement Metadata
- **Baseline Directory**: `.aw/state/percov/baseline`
- **Baseline Git HEAD**: `161e629b9d44b5e1a393902195a51e731fabb3ea`
- **Host**: Linux 12-CPU
- **Worker Count**: 6 xdist workers (`--dist=worksteal`)
- **Total Instrumented Wall Time**: 1936.61s (32.3m)
- **Python Version**: 3.14.6 (main, Jul  8 2026, 13:05:09) [GCC 13.3.0]
- **Coverage Version**: 7.15.0 (core: `ctrace`, `patch = subprocess`)

## Suite Coverage Totals
- **Total Collected Tests**: 9801
- **No-Coverage Tests**: 476
- **Covered Statements**: 125221 / 98508 (82.79%)
- **Covered Branches**: 163531 / 40074 (74.56%)
- **Tests with 0 Unique Lines**: 8006
- **Tests with 0 Unique Arcs**: 7808

## Disposition Summary
- **Module Dispositions (576 total)**:
  - `keep`: 178
  - `consolidate`: 204
  - `speed-up`: 33
  - `read-required`: 150
  - `delete-candidate`: 11
- **Test Dispositions (9801 total)**:
  - `keep`: 4552
  - `consolidate`: 2641
  - `speed-up`: 256
  - `read-required`: 613
  - `delete-candidate`: 1739

## Read-Required Tests (613 total)
Tests flagged with no recorded coverage or matching static structure-pin patterns requiring human or LLM reading before modification or deletion:

| Test Node ID | Reason |
| --- | --- |
| `tests/test_action_table_runner_parity.py::TestActionTableRunnerParity::test_execute_item_core_guard_raises_on_skip_action` | defect-cited (z7nbn1); read-required (pin: inspect_getsource) |
| `tests/test_action_table_runner_parity.py::TestActionTableRunnerParity::test_executed_maps_to_skip_on_both_hosts` | defect-cited (z7nbn1); read-required (pin: inspect_getsource); delete-candidate (0 unique) |
| `tests/test_action_table_runner_parity.py::TestActionTableRunnerParity::test_four_draft_cases_agreement` | defect-cited (z7nbn1); read-required (pin: inspect_getsource); delete-candidate (0 unique) |
| `tests/test_action_table_runner_parity.py::TestActionTableRunnerParity::test_parity_matrix_across_all_statuses_and_kinds` | defect-cited (z7nbn1); read-required (pin: inspect_getsource) |
| `tests/test_action_table_runner_parity.py::TestActionTableRunnerParity::test_retired_statuses_parity_direct` | defect-cited (z7nbn1); read-required (pin: inspect_getsource); consolidate (identical peer) |
| `tests/test_action_table_runner_parity.py::TestConsumerCases::test_consumer_action_legality_on_incomplete_draft` | defect-cited (z7nbn1); read-required (pin: inspect_getsource) |
| `tests/test_action_table_runner_parity.py::TestConsumerCases::test_consumer_exit_code` | defect-cited (z7nbn1); read-required (pin: inspect_getsource); delete-candidate (0 unique) |
| `tests/test_action_table_runner_parity.py::TestConsumerCases::test_consumer_retry_incomplete_requeue_exclusion` | defect-cited (z7nbn1); read-required (pin: inspect_getsource) |
| `tests/test_action_table_runner_parity.py::TestConsumerCases::test_consumer_reviewed_orchestrator_order_sensitivity` | defect-cited (z7nbn1); read-required (pin: inspect_getsource); delete-candidate (0 unique) |
| `tests/test_agent_user_config_containment.py::test_conftest_scrub` | defect-cited (9y27t2); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_agents_block_target_neutral.py::AgentsBlockTargetNeutralTests::test_this_repo_agents_md_has_suite_in_repo_local_region_only` | defect-cited (ka0g86); read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_agy_models.py::AgyRunIpdModelFlagTests::test_model_flag_included_when_explicitly_passed` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_agy_models.py::AgyRunIpdModelFlagTests::test_model_flag_omitted_when_not_explicitly_passed` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_agy_run.py::AntigravityExecuteIpdCompatibilityTests::test_delegates_through_compat_shim_to_packaged_core` | defect-cited (5s31xp); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_agy_run.py::AntigravityExecuteIpdCompatibilityTests::test_delegation_to_agy_run` | defect-cited (5s31xp); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_agy_run.py::AntigravityExecuteIpdCompatibilityTests::test_re_exports_and_interface_parity` | defect-cited (5s31xp); read-required (no-coverage); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_agy_runipd_cli.py::AgyDependencyPathsAreSharedTests::test_both_dependency_entry_points_are_the_shared_objects` | read-required (no-coverage); read-required (pin: assert_is_host_attr); delete-candidate (0 unique) |
| `tests/test_agy_runipd_cli.py::AgyEndOfRunDispositionSummaryTests::test_both_hosts_render_the_line_from_the_same_object` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_agy_runipd_cli.py::AgyFullAutoApprovalTests::test_predicate_is_the_shared_one_and_local_copies_are_gone` | read-required (no-coverage); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_agy_runipd_cli.py::AgyPerArtifactDispositionLineTests::test_both_hosts_render_the_line_from_the_same_object` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_agy_runipd_cli.py::AgyVerdictMappingTests::test_this_host_binds_the_shared_mapping_and_holds_no_copy` | read-required (no-coverage); read-required (pin: assert_is_host_attr); delete-candidate (0 unique) |
| `tests/test_agy_runipd_cli.py::AgyVerificationAbsenceTests::test_plan_path_resolution` | defect-cited (IPD agy404); read-required (pin: assert_is_host_attr); delete-candidate (0 unique) |
| `tests/test_artifact_adopt.py::ModuleContractTests::test_only_research_is_supported_on_day_one` | defect-cited (lznpv6); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_artifact_core_git_mv_containment.py::TestArtifactCoreGitMvContainment::test_case_d_symlink_destination_pointing_outside_refused` | defect-cited (7sy2gm); read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_attempt_agy_model_observation.py::TestAttemptAgyModelObservation::test_case_e_seam_contract_resolution_through_driver_module` | defect-cited (rejqff); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_attention.py::SharedLifecycleResolverTests::test_lifecycle_resolution_and_escapes` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_authoring_coverage_guidance.py::FreshInstallManagedBlockTests::test_fresh_install_writes_agents_md_with_precondition` | defect-cited (dalmk4); read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_aw_upgrade_test.py::ChildToolPinningTests::test_probe_import_origin_in_simulated_worktree_reports_worktree` | read-required (pin: sys_modules_check); delete-candidate (0 unique) |
| `tests/test_aw_upgrade_test.py::ChildToolPinningTests::test_run_install_in_simulated_worktree_imports_from_worktree` | read-required (pin: sys_modules_check); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::CompareTests::test_complete_copy_map_passes` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::CompareTests::test_missing_and_unapproved_items_fail` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::PostcheckTests::test_clean_context_passes` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::PostcheckTests::test_copied_adapter_logic_and_wrong_git_owner_fail` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::PostcheckTests::test_e03` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::PostcheckTests::test_e07` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::PostcheckTests::test_fabricated_clean_context_fails_without_external_evidence` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::PostcheckTests::test_tracked_runtime_and_legacy_route_fail` | defect-cited (writer); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::ScenarioBindingTests::test_bad_binding_is_rejected` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::ScenarioBindingTests::test_every_binding_loads_a_real_test_method_and_names_an_assertion` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::ScenarioBindingTests::test_every_expected_token_is_bound` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::ScenarioBindingTests::test_legacy_crosswalk_assertion_tokens_are_bound` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::ScenarioCatalogTests::test_legacy_crosswalk_assertions_bind_to_scenarios` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_awphysical_tools.py::ScenarioCatalogTests::test_scenario_ids_are_unique_and_complete` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_backlog_descriptive_safety.py::BacklogDescriptiveSafetyTests::test_helper_refuse_unsafe_descriptive_contract` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_backlog_handoff_close.py::BacklogGateDirSplitTests::test_backlog_set_declared_flag_surface_matches_parser` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_check_engine_metadata_region.py::test_bounded_accessors_ignore_body_quotations` | defect-cited (xvon5j); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_check_engine_spec_criteria.py::CheckEngineSpecCriteriaTests::test_rule_id_contains_neither_graduation_nor_duplicate` | defect-cited (3dexf1); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_b2_identity_table` | defect-cited (fnnwj3); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_protocol_and_contract_agree_on_token_control_hatches` | defect-cited (moegsl); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_token_control_count_word_agrees_with_bullet_count` | defect-cited (moegsl); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_token_control_enumerates_limit` | defect-cited (moegsl); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_cli_checkout_reexec.py::test_01_mismatch_cwd_fake_reexecs` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_cli_checkout_reexec.py::test_02_mismatch_cwd_subdir_reexecs` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_cli_checkout_reexec.py::test_03_mismatch_git_file_reexecs` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_cli_checkout_reexec.py::test_07c_keep_root_env_alone_does_not_exempt` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_cli_checkout_reexec.py::test_13_notice_survives_piped_stderr` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_cli_quality_gates.py::GoldenInventoryTests::test_every_committed_golden_is_read_and_every_read_golden_exists` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_commit_isolated_raced.py::CommitIsolatedRacedTests::test_case_5_retained_ref_invisible_to_operator_views` | defect-cited (a1ygjp); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_commit_run_trailers_env.py::test_conftest_scrubs_run_and_item_env_vars` | defect-cited (a6xbso); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_completion_stale_notice.py::DocumentationAndDocstringTests::test_readme_tab_completion_section` | read-required (no-coverage); read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_completion_stale_notice.py::DocumentationAndDocstringTests::test_test_completion_docstring_updated` | read-required (no-coverage); read-required (pin: module_doc_assertion); delete-candidate (0 unique) |
| `tests/test_completion_stale_notice.py::NoticeStampTests::test_stamp_write_readonly_parent` | read-required (pin: hasattr_prod) |
| `tests/test_concurrent_driver_guard.py::BoundedWaitTests::test_the_default_bound_is_FINITE` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_concurrent_driver_guard.py::OperatorVerbTests::test_the_verb_and_the_driver_genuinely_CONTEND` | read-required (pin: read_prod_source) |
| `tests/test_cross_tree_session_refusal.py::CrossTreeSessionRefusalTests::test_decisive_negative_case_sweep_session_preserved` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dead_status_token_scan.py::DeadStatusTokenScanBehavioralTests::test_fixture_a_bare_legacy_failed_safely_flags` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dead_status_token_scan.py::DeadStatusTokenScanBehavioralTests::test_fixture_b_paired_fail_gate_does_not_flag` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dead_status_token_scan.py::DeadStatusTokenScanBehavioralTests::test_fixture_c_function_canonicalizer_does_not_flag` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dead_status_token_scan.py::DeadStatusTokenScanBehavioralTests::test_fixture_d_ambiguous_tokens_blocked_and_partial_do_not_flag` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dead_status_token_scan.py::DeadStatusTokenScanBehavioralTests::test_fixture_e_canonical_twin_in_different_arm_does_not_flag` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dead_status_token_scan.py::DeadStatusTokenScanBehavioralTests::test_fixture_f_bare_equality_comparison_flags` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dead_status_token_scan.py::DeadStatusTokenScanBehavioralTests::test_fixture_g_well_formed_exemption_marker_does_not_flag` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dead_status_token_scan.py::DeadStatusTokenScanBehavioralTests::test_fixture_h_uncited_marker_still_flags` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dead_status_token_scan.py::DeadStatusTokenScanFilesystemTests::test_domain_computation_and_dynamic_derivation` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dead_status_token_scan.py::DeadStatusTokenScanFilesystemTests::test_scan_paths_on_temporary_directory` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_case_a_pass` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_case_b_fail` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_case_c_error_import` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_case_d_error_collect` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_case_e_no_tests` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_case_f_timeout` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_case_g_parents_and_conftest` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_cli_no_paths_exits_2` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_cli_subprocess_from_json` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_overwrote_head_path_true` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_dependency_block_reporting.py::test_dependency_reason_rendering_all_producer_shapes[case_i_drain_external]` | read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_dependency_block_reporting.py::test_dependency_reason_rendering_all_producer_shapes[case_ii_findings_gate]` | read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_dependency_block_reporting.py::test_dependency_reason_rendering_all_producer_shapes[case_iii_cascade_token_free]` | read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_dependency_block_reporting.py::test_dependency_reason_rendering_all_producer_shapes[case_iv_frozen_record]` | read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_dependency_block_reporting.py::test_dependency_reason_rendering_all_producer_shapes[case_v_report_and_transient_waits]` | read-required (pin: md_doc_prose) |
| `tests/test_dependency_block_reporting.py::test_dependency_reason_rendering_all_producer_shapes[case_vi_mid_sentence_no_overstrip]` | read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_dependency_block_reporting.py::test_dependency_reason_rendering_all_producer_shapes[case_vii_declared_bare_id6]` | read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_dependency_block_reporting.py::test_drain_and_cascade_report_renders_correct_host_attribution` | read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_dependency_block_reporting.py::test_orchestrator_item_surfaces_child_in_report_not_summary_table` | read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_dependency_block_reporting.py::test_write_report_dependency_blocks_section_for_canonical_and_legacy_statuses[dependency-blocked]` | read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_dependency_block_reporting.py::test_write_report_dependency_blocks_section_for_canonical_and_legacy_statuses[fail-depend]` | read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_dependency_block_reporting.py::test_write_report_renders_one_recovery_line_for_each_producer` | read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_descriptive_length_classes.py::DescriptiveLengthClassesTests::test_bounds_are_distinct_and_constants_defined` | defect-cited (Spec: Sample, pl1lbb); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_descriptive_refusal_hoist.py::test_public_hoisted_helper_exists` | defect-cited (685iq8); read-required (no-coverage); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_deselect_notice.py::DeselectNoticePluginTests::test_mixed_marker_and_keyword_deselection` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deselect_notice.py::DeselectNoticePluginTests::test_no_marker_filter_with_keyword_deselection` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deselect_notice.py::DeselectNoticePluginTests::test_three_categories_named_in_notice` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deselect_notice.py::DeselectNoticePluginTests::test_unconditional_print_regression_under_selected_marker` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_deselect_notice.py::DeselectNoticePluginTests::test_verbatim_fallback_for_unparsed_marker_expression` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_docs_test_citations.py::test_published_docs_test_citations_exist` | defect-cited (specifying); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_egress_policy.py::TestEgressBrokerUnixSocket::test_af_unix_broker_lifecycle_and_directory_mode` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_absent_policy_raises` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_explicit_configuration_formats` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[   ]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[*.example.com:443]` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[12345]` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[example.com:0]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[example.com:70000]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[example.com:not_a_number]` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[invalid_config10]` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[invalid_config8]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[invalid_config9]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises[not_a_valid_destination]` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_allow_listed_destination_allowed` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_duplicates` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries[entry0-wildcard host not allowed]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries[entry1-wildcard host not allowed]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries[entry2-empty host]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries[entry3-empty host]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries[entry4-port out of range]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries[entry5-port out of range]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries[entry6-port out of range]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries[entry7-host cannot contain whitespace]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries[entry8-host cannot contain whitespace]` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries[entry9-host cannot contain whitespace]` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_empty_policy_denies_everything` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_policy_has_no_allow_all_or_negation_switch` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_same_host_different_port_denied` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_unlisted_destination_denied` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_egress_policy.py::TestHermeticBrokerEndToEnd::test_broker_refusal_distinguishable_from_network_fault` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestHermeticBrokerEndToEnd::test_hermetic_same_port_and_port_partition` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestHermeticBrokerEndToEnd::test_omitted_model_endpoint_refusal_visible` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_egress_policy.py::TestHermeticBrokerEndToEnd::test_refuse_non_connect_method` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestHermeticBrokerEndToEnd::test_refuse_over_long_request_head` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestHermeticBrokerEndToEnd::test_refuse_target_carrying_newline` | read-required (pin: hasattr_prod) |
| `tests/test_egress_policy.py::TestHermeticBrokerEndToEnd::test_upstream_connection_failure` | read-required (pin: hasattr_prod) |
| `tests/test_finalize_sendback.py::ARefusedItemDoesNotSatisfyADependentEdge::test_the_cascade_and_edge_gate_remain_ONE_shared_object_per_host` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_finalize_sendback.py::BothHostsBehaveIdentically::test_both_hosts_agree_on_the_success_bars` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_finalize_sendback.py::BothHostsBehaveIdentically::test_the_send_back_symbols_are_reachable_from_both_hosts` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_finalize_sendback.py::TheOrchestratorBarIsNotKilledWhileRetryBudgetRemains::test_a_retrying_child_is_not_terminal_which_is_what_makes_it_actionable` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_finalize_sendback.py::TheOrchestratorBarIsNotKilledWhileRetryBudgetRemains::test_the_exhausted_status_is_terminal_and_not_a_success` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_finalize_sendback.py::TheRefusalArmPerformsTheSendBack::test_finalize_refused_is_an_ALLOWLISTED_prior_attempt_key` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_finalize_sendback.py::TheRetryTriggerIsAPositiveAllowlist::test_the_reduction_invariant_text_matches_ipd_lifecycle_findings` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fix_it_global_caps.py::TestFixItTurnsSpent::test_gate_answer_accumulates_in_retry_attempts` | defect-cited (38hwvk, c0oysi); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fix_it_notice.py::E05CorrectionTextsTests::test_runbook_directive_aligned` | defect-cited (mcbph5); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_e05_spec_abort_classes_match` | defect-cited (25kzda, iksylm); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests::test_question_timeouts_are_180s` | defect-cited (184tn9); read-required (pin: assert_is_host_attr) |
| `tests/test_fresh_target_install_regression.py::test_install_d01_n2_version_consistency` | defect-cited (kck7a5); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fresh_target_install_regression.py::test_install_d02_state_and_config_ignored` | defect-cited (kck7a5); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fresh_target_install_regression.py::test_install_d03_n1_clean_porcelain_and_run_scratch_ignored` | defect-cited (kck7a5); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fresh_target_install_regression.py::test_install_d04_consent_plan_paths_exist` | defect-cited (kck7a5); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fresh_target_install_regression.py::test_install_d06_no_root_workflow_artifacts` | defect-cited (kck7a5); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fresh_target_install_regression.py::test_install_d07_managed_agents_block_neutral` | defect-cited (kck7a5); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fresh_target_install_regression.py::test_install_d08_d09_no_retired_agents_paths_or_intake` | defect-cited (kck7a5); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fresh_target_install_regression.py::test_install_d14_inbox_readme_tracked_and_drops_ignored` | defect-cited (kck7a5); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fresh_target_install_regression.py::test_install_d15_tracking_truth_table` | defect-cited (kck7a5); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_fresh_target_install_regression.py::test_install_doctor_zero_dangling_references` | defect-cited (kck7a5); read-required (no-coverage); speed-up (duration 4.42s > 2s); delete-candidate (0 unique) |
| `tests/test_fresh_target_install_regression.py::test_research_composition_d10_d11_d12` | defect-cited (kck7a5); read-required (no-coverage); speed-up (duration 4.86s > 2s); delete-candidate (0 unique) |
| `tests/test_git_commit_helper.py::test_hook_rewrite_retry_and_peer_isolation` | defect-cited (m73aet); read-required (pin: md_doc_prose) |
| `tests/test_git_config_guard.py::test_guard_catches_leak_and_restores_config` | read-required (no-coverage); speed-up (duration 2.34s > 2s); delete-candidate (0 unique) |
| `tests/test_git_config_guard.py::test_guard_disables_itself_on_non_git_target` | read-required (no-coverage); speed-up (duration 2.33s > 2s); delete-candidate (0 unique) |
| `tests/test_git_config_guard.py::test_guard_ignores_non_identity_keys` | read-required (no-coverage); speed-up (duration 3.41s > 2s); delete-candidate (0 unique) |
| `tests/test_git_config_guard.py::test_guard_restores_preexisting_identity_value` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_git_config_guard.py::test_init_repo_failure_does_not_leak_to_enclosing_repo` | read-required (no-coverage); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_git_config_guard.py::test_init_repo_with_inherited_git_dir_does_not_leak` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_2_reverse_only` | defect-cited (Backlog: rev001); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_6_no_source_at_all` | defect-cited (plan setids, pw2ln3, record, source); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_group_verb_policy.py::test_group_verb_policy_sanity` | defect-cited (949enf); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_hang_guard_budget.py::test_cpu_runaway_caught_and_named` | defect-cited (6ye76g); read-required (no-coverage); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_hang_guard_budget.py::test_guard_under_xdist_workers` | defect-cited (6ye76g); read-required (no-coverage); read-required (pin: hasattr_prod); speed-up (duration 3.01s > 2s); delete-candidate (0 unique) |
| `tests/test_hang_guard_budget.py::test_marker_above_wall_ceiling_floors_and_raises_wall_allowance` | defect-cited (6ye76g); read-required (no-coverage); read-required (pin: hasattr_prod); speed-up (duration 2.60s > 2s); delete-candidate (0 unique) |
| `tests/test_hang_guard_budget.py::test_marker_lowers_cpu_budget` | defect-cited (6ye76g); read-required (no-coverage); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_hang_guard_budget.py::test_sleep_past_cpu_budget_inside_wall_ceiling_passes` | defect-cited (6ye76g); read-required (no-coverage); read-required (pin: hasattr_prod); speed-up (duration 2.31s > 2s); delete-candidate (0 unique) |
| `tests/test_hang_guard_budget.py::test_subprocess_bound_runaway_loop_caught_by_wall_ceiling` | defect-cited (6ye76g); read-required (no-coverage); read-required (pin: hasattr_prod); speed-up (duration 3.38s > 2s); delete-candidate (0 unique) |
| `tests/test_hang_guard_budget.py::test_syscall_bound_spin_caught_by_cpu_arm` | defect-cited (6ye76g); read-required (no-coverage); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_hang_guard_budget.py::test_timeout_zero_disables_both_arms` | defect-cited (6ye76g); read-required (no-coverage); read-required (pin: hasattr_prod); speed-up (duration 2.62s > 2s); delete-candidate (0 unique) |
| `tests/test_hang_guard_budget.py::test_zero_cpu_deadlock_caught_by_wall_ceiling` | defect-cited (6ye76g); read-required (no-coverage); read-required (pin: hasattr_prod); speed-up (duration 2.24s > 2s); delete-candidate (0 unique) |
| `tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_derived_history_writing_surface_coverage_and_floor` | defect-cited (2vev8j); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_precondition_at_least_one_zone_in_skew_window` | defect-cited (2vev8j); read-required (no-coverage); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_scoped_timezone_restores_environment` | defect-cited (2vev8j); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_history_date_clock_sidecar.py::HistoryDateClockSidecarTests::test_in_process_temporary_timezone_restoration` | defect-cited (2vev8j, dmrbqa); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_a_newest_first` | defect-cited (63h054); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_b_oldest_first` | defect-cited (63h054); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_c_mixed_blocks` | defect-cited (63h054); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_d_negative_cross_day_backwards` | defect-cited (63h054); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_e_discriminating_single_date_tie` | defect-cited (63h054); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_home_isolation.py::PopDoesNotLeakAcrossTests::test_1_strip_the_sandbox_like_a_careless_cleanup` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_home_path_pattern_source.py::test_cross_module_agreement_corpus` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_home_path_pattern_source.py::test_prefilter_coherence` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_home_path_pattern_source.py::test_rule_name_and_order_preservation` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_host_capability_extension.py::DenyPushRemovedTests::test_supports_deny_push_and_unenforced_action_verdicts_removed` | defect-cited (25kzda, SPEC rather); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_host_capability_extension.py::FailClosedPreflightTests::test_the_finding_code_string_is_exact` | defect-cited (25kzda, SPEC rather); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_host_capability_extension.py::GuaranteeRow4EnforcementStatusTests::test_row_4_leg_a_no_descriptor_field_proves_guarantee` | defect-cited (25kzda, SPEC rather); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_host_capability_extension.py::GuaranteeRowEnforcementStatusTests::test_row_1_push_denial_enforcement_status` | defect-cited (25kzda, SPEC rather); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_host_capability_extension.py::GuaranteeRowEnforcementStatusTests::test_row_3_hook_preserving_commit_enforcement_status` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_host_capability_extension.py::RequirementMapTests::test_requirement_map_structure_and_coverage` | defect-cited (25kzda, SPEC rather); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_host_capability_extension.py::RunnerSafetyProbeTests::test_presence_vs_observation_table` | defect-cited (25kzda, SPEC rather); read-required (pin: hasattr_prod) |
| `tests/test_host_capability_wiring.py::test_execute_item_core_refuses_when_host_capability_unavailable_and_starts_no_session` | defect-cited (iot7hc); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_host_sandbox_profile.py::CapabilityContractTests::test_every_contract_field_exists_and_defaults_false` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_host_sandbox_profile.py::ProfileDispatchTests::test_module_publishes_its_guarantees` | read-required (no-coverage); read-required (pin: module_doc_assertion); delete-candidate (0 unique) |
| `tests/test_hostdedup_third_host.py::HostLabelsDriverIdResolverAndConsumerTests::test_discovered_host_descriptors_driver_keys_are_collision_free` | defect-cited (driver); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_hostdedup_third_host.py::ThirdHostDescriptorTests::test_descriptor_is_distinct_from_existing_hosts` | defect-cited (driver); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_hostdedup_third_host.py::ThirdHostDescriptorTests::test_third_host_needs_no_runner_module` | defect-cited (driver); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_hostdedup_third_host.py::ThirdHostInitializationAndLimitTests::test_each_real_host_records_own_driver_identity_and_consumers_route` | defect-cited (o55eli); read-required (pin: read_prod_source); delete-candidate (0 unique) |
| `tests/test_hostdedup_third_host.py::ThirdHostInitializationAndLimitTests::test_pin_measured_turn_execution_limits` | defect-cited (driver); read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_installed_version_reporting.py::InstalledVersionReportingTests::test_e2e_wheel_build_installed_version_reporting` | defect-cited (whz0oi); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_installer.py::AwBlockMigrationTests::test_legacy_block_conversion_and_sibling_preservation` | read-required (pin: md_doc_prose) |
| `tests/test_installer.py::AwBlockMigrationTests::test_reinstall_idempotence_and_declined_section` | read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_installer.py::InstallLeftoverDefaultRemoveTests::test_safety_case_b2_committed_leftover_with_staged_edit_survives_remove` | read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_installer.py::InstallLeftoverDefaultRemoveTests::test_safety_case_b_committed_leftover_with_uncommitted_edit_survives_remove` | read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_installer.py::InstallerEndToEndTests::test_fresh_install` | read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_installer.py::InstallerEndToEndTests::test_readme_templates_are_created_on_a_fresh_install` | read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_installer.py::UninstallApplyTests::test_changed_out_collects_paths_and_sections_preserved` | read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_ipd_exec_finding_codes.py::IpdExecFindingCodesTests::test_spec_pinning_e04` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_ipd_templates.py::SpecCleanlinessTests::test_ipd_spec_has_no_relational_placement_language` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_ipd_templates.py::SpecCleanlinessTests::test_ipd_spec_points_at_schema` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_ipd_templates.py::TemplateStructureTests::test_child_h2_matches_schema_order` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_ipd_templates.py::TemplateStructureTests::test_execution_immediately_after_goal_in_both` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_ipd_templates.py::TemplateStructureTests::test_no_transition_as_checklist_item` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_ipd_templates.py::TemplateStructureTests::test_orchestrator_h2_matches_schema_order` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_ipdrunner_runagy_shim.py::AgyExecutionLifecycleTests::test_default_start_subcommand_inference` | defect-cited (runner); read-required (pin: read_prod_source); delete-candidate (0 unique) |
| `tests/test_ipdrunner_runagy_shim.py::AgyExecutionLifecycleTests::test_explicit_run_id` | defect-cited (runner); read-required (pin: read_prod_source); delete-candidate (0 unique) |
| `tests/test_ipdrunner_runagy_shim.py::AgyExecutionLifecycleTests::test_prepare_only_mode` | defect-cited (runner); read-required (pin: read_prod_source); delete-candidate (0 unique) |
| `tests/test_ipdrunner_runagy_shim.py::AgyExecutionLifecycleTests::test_runagy_no_verify_skips_turn2` | defect-cited (runner); read-required (pin: read_prod_source); delete-candidate (0 unique) |
| `tests/test_ipdrunner_runagy_shim.py::AgyExecutionLifecycleTests::test_runagy_status_and_report_commands` | defect-cited (runner); read-required (pin: read_prod_source) |
| `tests/test_ipdrunner_runagy_shim.py::AgyExecutionLifecycleTests::test_runagy_two_turn_execution_with_clean_verification` | defect-cited (runner); read-required (pin: read_prod_source); delete-candidate (0 unique) |
| `tests/test_ipdrunner_runagy_shim.py::AgyExecutionLifecycleTests::test_stall_timeout_and_resume_recovery` | defect-cited (runner); read-required (pin: read_prod_source) |
| `tests/test_ipdrunner_runagy_shim.py::AgyExecutionLifecycleTests::test_verification_blocked_sets_status_fail_verify` | defect-cited (runner); read-required (pin: read_prod_source); delete-candidate (0 unique) |
| `tests/test_isolation_per_action.py::PolicyIsolationTests::test_isolate_worktree_is_not_registered_in_config_schema` | defect-cited (bzlxn0); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lane_import_root.py::LaneImportRootGuardTests::test_both_directions_hold_from_multiple_non_root_subdirectories` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lane_import_root.py::LaneImportRootGuardTests::test_control_plane_caller_from_lane_subdir_resolves_driver_package` | defect-cited (7ckptx); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lane_import_root.py::LaneImportRootGuardTests::test_evidence_caller_from_lane_subdir_resolves_lane_package` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lane_import_root.py::LaneImportRootGuardTests::test_unpinned_launch_from_lane_subdir_reproduces_defect` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lane_owner_record_anchoring.py::LaneOwnerRecordAnchoringTests::test_absent_versus_unreachable_owner_store` | defect-cited (tjags7, voxbcx); read-required (pin: hasattr_prod) |
| `tests/test_lifecycle_dirs.py::ConsumerAgreementTests::test_backlog_status_dirs` | defect-cited (d1lo52); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lifecycle_dirs.py::ConsumerAgreementTests::test_engine_constants` | defect-cited (d1lo52); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lifecycle_dirs.py::ConsumerAgreementTests::test_plans_disposition_dirs` | defect-cited (d1lo52); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lifecycle_dirs.py::ConsumerAgreementTests::test_specs_status_vocabularies` | defect-cited (d1lo52); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lifecycle_legend_help_reach.py::LifecycleLegendAndDocsDriftGuardTests::test_docs_reference_canonical_legend_without_duplicate_tables` | defect-cited (uonrjg); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lifecycle_style.py::CriterionA5VariationSelectorTests::test_committed_golden_fixtures_contain_no_emoji_variation_selector` | defect-cited (uonrjg); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lifecycle_style.py::MappingTotalityTests::test_every_family_has_exactly_one_policy_and_stages_defined` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lifecycle_style.py::MappingTotalityTests::test_prompts_directory_derived` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lifecycle_style.py::StageTableTests::test_stage_styling_and_presentation_properties` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_liftaudit_stop_halts_run.py::LiftauditStopHaltsRunTests::test_record_checkpoint_stop_omitted_git_status_fn_raises` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lost_guard_census.py::LostGuardCensusBehavioralTests::test_classifier_bidirectional_and_mixed` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_acknowledged_non_citations_and_placeholders` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_cli_summary_output_and_rules` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_mixed_candidate_annotation_contract` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_synthetic_axes_attribution` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_synthetic_census_computation` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_uncited_inventory_and_cli` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_interactive_wizard_decline_makes_no_mutations` | defect-cited (1ue3kr); read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_decorated_function` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_method_c_m` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_missing_qualname_returns_none` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_negate_return` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_negate_return_no_return_expr_returns_none` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_nested_function_negate_return_inner_preserved` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_one_line_def` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_raise` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_return_false` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_return_none` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_return_true` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ApplyOperatorUnitTests::test_unknown_operator_returns_none` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ProbeGitFixtureTests::test_always_failing_extra_test_not_credited_as_kill` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ProbeGitFixtureTests::test_cli_subprocess_json_and_exit_codes` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ProbeGitFixtureTests::test_flaky_test_excluded_from_kill` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ProbeGitFixtureTests::test_positive_control_extra_test_kills_unused` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_error_isolation_preflight` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_invalid_qualname_no_pytest_run` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_killed_by_import_boot_raise` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_killed_is_even_negate_return` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_survived_unused_return_none` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_timeout` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::ActionLegalityTests::test_alias_refusal_and_acceptance` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::AllSelectorAndFullAutoTests::test_full_auto_reviews_approves_and_executes_plan` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::AllSelectorAndFullAutoTests::test_is_plan_review_approved_is_the_shared_predicate_not_a_local_copy` | read-required (no-coverage); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::AllSelectorAndFullAutoTests::test_without_full_auto_stops_at_reviewed` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::DriverTests::test_atomic_state_and_set_session_continuity` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::EmptyReviewSweepExitsZeroTests::test_end_to_end_empty_sweep_cli` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::HostReviewAliasExpansionTests::test_alias_freezes_the_same_run_state_as_the_canonical_invocation` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::LaunchProfileDurableStateTests::test_report_and_status_render_the_launch_identity` | read-required (no-coverage); read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::LaunchProfileDurableStateTests::test_state_records_resolved_fields_and_per_field_provenance` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::LaunchProfileFrozenTurnArgvTests::test_absent_store_is_a_no_op_not_a_failure` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::LaunchProfileFrozenTurnArgvTests::test_direct_start_without_a_profile_is_behavior_equivalent` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::LaunchProfileFrozenTurnArgvTests::test_resume_does_not_reload_profiles_after_the_store_changes` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::PlanBucketRecognitionTests::test_the_docstring_states_that_a_bucket_is_not_a_readiness` | read-required (no-coverage); read-required (pin: module_doc_assertion); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::ReviewPlanRoutingTests::test_to_review_plans_invoke_plan_review_and_share_session` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::RunipdBugsFixesTests::test_read_deps_and_set_parsing` | defect-cited (IPD: aaaaaa, pr2nd0); read-required (pin: hasattr_prod) |
| `tests/test_oc_runipd.py::SelectorResolutionTests::test_default_start_command_invocation` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_does_not_trip_on_active_child` | defect-cited (ncpc8z); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::VerdictLanePreservationTests::test_every_non_verified_verdict_refuses_integration_on_both_hosts` | read-required (pin: assert_is_host_attr); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::VerificationAbsenceTests::test_the_pre_fix_contrast_all_three_facts_were_one_value` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::VerifierLaunchFreezeTests::test_a_dangling_verify_with_refuses_before_any_durable_side_effect` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::VerifierLaunchFreezeTests::test_launch_identity_rendering` | read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::VerifierLaunchFreezeTests::test_verifier_launch_freeze_options` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_oc_runipd.py::VerifierLaunchFreezeTests::test_verify_with_cli_and_resume` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_orchestrate_isolation.py::TestIsolationHierarchy::test_all_isolation_modes_defined` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_orchestrator_probe_quotes.py::TestProbeOrchestratorPlanRecord::test_store_file_not_written` | defect-cited (8mabmu); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::ADeadSetTerminatesInsteadOfLooping::test_a_child_only_on_disk_terminates_instead_of_spinning` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::ADeadSetTerminatesInsteadOfLooping::test_a_terminally_failed_child_terminates_with_a_reason_naming_it` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::AFailedRetirementCannotDestroyAPeersInFlightEdit::test_rollback_preserves_peer_edits_restores_half_moves_and_is_idempotent` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_failed_retirement_preserves_manifest_absence_presence_and_peer_writes` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_success_path_regenerates_index_and_failure_reporting_invariants` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_orchestrator_retirement.py::AnOrchestratorIsRetiredMidRun::test_an_unfinished_child_yields_RECONSIDER_and_never_a_TERMINAL_disposition` | defect-cited (exists); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::AnOrchestratorIsRetiredMidRun::test_reconsidered_then_retired_in_the_same_run_on_both_hosts` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::AnOrchestratorIsRetiredMidRun::test_the_reconsidered_item_is_left_queued_and_not_relabelled_by_the_cascade` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::ChildTableParserTests::test_every_table_shape_parses_to_its_exact_declared_tokens` | defect-cited (review, run-20260922T003657Z); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::GateParityBetweenTheTwoPaths::test_gate_parity_declarations_and_reasons` | read-required (no-coverage); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::MembershipReadsThePlansTree::test_every_selector_yields_its_exact_membership` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_orchestrator_retirement.py::MembershipReadsThePlansTree::test_membership_resolution_edge_cases_and_repo_corpus` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::NoReceiptIsRequiredAndNoneIsLeftBehind::test_no_receipt_required_or_left_behind_and_lifecycle_paths_safe` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_orchestrator_retirement.py::OrchestratorRetirementRowAuditAndHonestRecord::test_an_orchestrator_with_untyped_checklist_rows_is_refused_at_retirement` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::OrchestratorRetirementRowAuditAndHonestRecord::test_retired_orchestrator_file_states_items_were_superseded_in_body` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::RollupRetiresAnEligibleSet::test_an_eligible_set_retires_and_lands_in_executed` | defect-cited (77tr3o, kjqqzf); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheActionDecisionIsSHAREDCode::test_action_decision_shared_code_binding_and_queue_derivation` | defect-cited (record, review); read-required (pin: assert_is_host_attr); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheAgyHostActsOnTheDecision::test_neither_host_forks_the_dispatch_or_the_decision` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheAgyHostActsOnTheDecision::test_the_orchestrate_branch_SHORT_CIRCUITS_before_execute_item_on_both_hosts` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheFourRefusalReasonsAreDistinguishable::test_each_cause_yields_a_DISTINCT_reason_and_a_detail_that_substantiates_it` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheGateDoesNotOpenForOrdinaryPlans::test_a_child_of_ANOTHER_set_cannot_ride_an_eligible_sets_verdict` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheGateDoesNotOpenForOrdinaryPlans::test_every_gate_refuses_its_own_target_for_its_own_typed_reason` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_orchestrator_retirement.py::TheHonestTerminalRecord::test_honest_terminal_record_history_entry_and_actor` | defect-cited (run-20260906T000000Z); read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_orchestrator_retirement.py::TheHumanFacingGateIsUNCHANGED::test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheIndexGateIsStillLiveUnderTheNewOrdering::test_index_gate_refreshes_after_reconciliation_and_fails_loud_on_non_convergence` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheRejectedShapeWasNotTaken::test_the_pre_transition_ev_requirement_is_identical_for_every_kind` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheSelectionGateUsesTheSameDecision::test_selection_gate_admits_complete_sets_and_blocks_live_children` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheSelectionGateUsesTheSameDecision::test_the_gate_and_the_dispatch_cannot_disagree` | defect-cited (status); read-required (pin: ast_parse_walk); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheSharedCheckoutIsNotWhereTheMutationHappens::test_shared_checkout_mutation_isolation_and_commit_landing` | read-required (pin: ast_parse_walk, inspect_getsource); consolidate (identical peer) |
| `tests/test_orchestrator_retirement.py::TheSharedGatesActuallyFireOnTheRollupPath::test_a_FAILING_plans_index_refresh_fails_the_whole_transaction` | defect-cited (plan-holder); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheSharedGatesActuallyFireOnTheRollupPath::test_committed_incomplete_rollup_remains_unreachable_control` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheSharedGatesActuallyFireOnTheRollupPath::test_lock_lint_and_empty_actor_gates` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_orchestrator_retirement.py::TheSharedGatesActuallyFireOnTheRollupPath::test_transaction_journal_lifecycle_and_fault_recovery` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheSharedGatesAreSharedAsCODE::test_the_rollup_performs_no_plan_move_or_commit_of_its_own` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_clean_arm_fast_forwards_and_only_permitted_mutations_touch_shared_tree` | read-required (pin: ast_parse_walk, inspect_getsource); consolidate (identical peer) |
| `tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_contended_arm_clears_journal_and_retry_succeeds` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_contended_arm_refuses_and_the_peers_bytes_survive` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_diverged_arm_is_a_race_with_its_own_exit_code` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TheWorkerRoleIsRefused::test_worker_role_is_refused_and_coordinator_unaffected` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_orchestrator_retirement.py::ThisChildDecidesOnly::test_driving_every_decision_path_writes_NOTHING_to_the_plans_tree` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TypedRefusalReasons::test_a_deliberately_retired_child_does_not_wedge_its_set` | defect-cited (31y86f); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TypedRefusalReasons::test_allowlist_and_outcome_distinctness_invariants` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TypedRefusalReasons::test_every_cause_yields_its_OWN_typed_reason_with_its_OWN_specifics` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_retirement.py::TypedRefusalReasons::test_only_the_exact_token_executed_qualifies` | read-required (no-coverage); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_orchestrator_shape_composed.py::TestDistinguishableRefusalsAndMixedQueueOrdering::test_shape_and_probe_refusal_codes_differ` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_orchestrator_shape_composed.py::TestProbeSurvivedAndStillBlocks::test_probe_test_file_absent_from_orchtyped_commits` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_orchestrator_shape_gate.py::BothHostsShareOneDefinition::test_each_host_resolves_the_gate_to_the_SAME_object` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_orchestrator_shape_gate.py::BothHostsShareOneDefinition::test_no_new_host_attribute_is_added` | defect-cited (review); read-required (no-coverage); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_orchestrator_shape_gate.py::TheProbeSurvivesAndRefusalsAreDistinct::test_rule_ids_differ_between_shape_and_probe_refusals` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_outcome_word_ladder.py::OutcomeWordLadderBehavioralFenceTests::test_case_b_totality` | defect-cited (064awu); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging.py::PackagingTests::test_wheel_declares_only_the_allowlisted_runtime_dependency` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging.py::PackagingTests::test_wheel_ship_vs_dev_boundary` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging_distribution.py::SdistPackagingDistributionTests::test_sdist_ships_analytics_and_layout_modules_by_name` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging_distribution.py::SdistPackagingDistributionTests::test_sdist_ships_bundled_system_data_tree` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging_distribution.py::SdistPackagingDistributionTests::test_sdist_ships_every_browser_asset_by_name` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging_distribution.py::WheelPackagingDistributionTests::test_a_gitignored_asset_would_be_detected_rather_than_silently_dropped` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging_distribution.py::WheelPackagingDistributionTests::test_declared_assets_match_the_module` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging_distribution.py::WheelPackagingDistributionTests::test_wheel_browser_assets_are_non_empty` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging_distribution.py::WheelPackagingDistributionTests::test_wheel_registers_three_console_scripts` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging_distribution.py::WheelPackagingDistributionTests::test_wheel_ships_every_browser_asset_by_name` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_packaging_distribution.py::WheelPackagingDistributionTests::test_wheel_ships_protected_analytics_and_layout_modules_by_name` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_placement_switch_retire.py::TestPlacementSwitchRetire::test_01_target_side_simulated_flip_home_snapshot_byte_identical_and_staged_deletions` | defect-cited (gjylny); read-required (pin: md_doc_prose) |
| `tests/test_plan_holder_predicate.py::PlanHolderPredicateTests::test_11_unreadable_runs_tree_discovery_failure_reports_undeterminable` | defect-cited (scoped, urv602); read-required (pin: hasattr_prod) |
| `tests/test_plan_holder_predicate.py::PlanHolderPredicateTests::test_unreadable_lock_reports_undeterminable` | defect-cited (run-20261009T010000Z); read-required (pin: hasattr_prod) |
| `tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_long_form_plan_review_feasibility_rule` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_no_error_added_proof_shape_in_rubrics` | defect-cited (k6t24p, review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_single_file_plan_review_feasibility_rule` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_spec_review_feasibility_rule_reference` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_plans_archive.py::DefaultAgeTests::test_default_age` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_platform_lock.py::ImportsWithoutFcntlTests::test_all_affected_modules_import_without_fcntl` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_platform_lock.py::ImportsWithoutFcntlTests::test_the_lock_still_excludes_without_fcntl` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_platform_lock.py::ImportsWithoutFcntlTests::test_the_probe_reports_undetermined_without_the_posix_primitive` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_platform_lock.py::ImportsWithoutFcntlTests::test_this_test_would_have_FAILED_before_the_fix` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_platform_lock.py::NonReentrancyTests::test_the_raw_filelock_object_would_have_been_reentrant` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_precommit_verbatim_exclusions.py::TestPrecommitVerbatimExclusions::test_mutating_hook_excludes_contain_no_dead_paths` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_precommit_verbatim_exclusions.py::TestPrecommitVerbatimExclusions::test_mutating_hook_ids_are_complete` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_precommit_verbatim_exclusions.py::TestPrecommitVerbatimExclusions::test_mutating_hooks_exclude_verbatim_preserved_trees` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_precommit_verbatim_exclusions.py::TestPrecommitVerbatimExclusions::test_safety_hooks_do_not_exclude_verbatim_preserved_trees` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_private_file.py::PrivateFileTests::test_windows_dacl_is_protected_and_owner_only` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_project_context.py::TestProjectSchema::test_canonical_enums_and_constants` | read-required (pin: hasattr_prod) |
| `tests/test_project_layout.py::PhysicalPolicyMatrixTests::test_e06` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_prompts_attention.py::PromptsContractTests::test_docs_prompts_is_excluded` | defect-cited (dx0u4s); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_prompts_attention.py::PromptsContractTests::test_tracked_trees_contains_prompts` | defect-cited (dx0u4s); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_prompts_new.py::TestAgentEnvelope::test_the_declared_flag_surface_matches_the_parser` | defect-cited (jxqdcw, ubac5n); read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_read_class_callers_refuse.py::test_check_miscategorized_bare_outside_project` | defect-cited (rlhmt9); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_read_class_callers_refuse.py::test_releases_new_negative_control_sub` | defect-cited (rlhmt9); read-required (no-coverage); speed-up (duration 2.63s > 2s); delete-candidate (0 unique) |
| `tests/test_read_class_callers_refuse.py::test_research_mutations_negative_control_sub` | defect-cited (rlhmt9); read-required (no-coverage); speed-up (duration 5.57s > 2s); delete-candidate (0 unique) |
| `tests/test_read_class_callers_refuse.py::test_root_controls_see_seeded_observables` | defect-cited (rlhmt9); read-required (no-coverage); speed-up (duration 7.39s > 2s); delete-candidate (0 unique) |
| `tests/test_read_class_callers_refuse.py::test_write_targets_on_surveyable_root` | defect-cited (rlhmt9); read-required (no-coverage); speed-up (duration 6.94s > 2s); delete-candidate (0 unique) |
| `tests/test_reaskscore_composed.py::TestSharedConstantsByteIdenticalAndUnwidened::test_execute_reporting_success_states_is_derived_by_subtraction` | defect-cited (svacmz); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_reaskscore_composed.py::TestSharedConstantsByteIdenticalAndUnwidened::test_five_constants_eight_definition_sites_values_and_types` | defect-cited (svacmz); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_reaskscore_composed.py::TestSharedConstantsByteIdenticalAndUnwidened::test_reexports_are_identical_objects` | defect-cited (svacmz); read-required (no-coverage); read-required (pin: assert_is_host_attr); delete-candidate (0 unique) |
| `tests/test_reaskscore_composed.py::TestSharedConstantsByteIdenticalAndUnwidened::test_terminal_states_three_copies_are_mutually_equal` | defect-cited (svacmz); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_record_producers.py::DerivedRecordClassTests::test_enum_module_is_this_module_so_members_stay_picklable` | defect-cited (review); read-required (no-coverage); read-required (pin: module_doc_assertion); delete-candidate (0 unique) |
| `tests/test_record_producers.py::DerivedRecordClassTests::test_every_record_class_member_resolves_to_its_pinned_value` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_record_producers.py::DerivedRecordClassTests::test_state_class_enums_are_derived_and_unchanged` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_record_producers.py::DerivedRecordClassTests::test_str_mixin_is_preserved_so_value_comparisons_keep_working` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_record_producers.py::LegacyReadPathTests::test_the_legacy_map_overrides_exactly_the_doc_family_and_inherits_the_rest` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_record_producers.py::ProducerInventoryTests::test_inventory_is_non_empty_and_every_category_is_a_known_class` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_record_producers.py::ProducerInventoryTests::test_the_legacy_allowlist_still_holds_only_non_writers` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_record_producers.py::ProjectSchemaAlignmentTests::test_both_root_vocabularies_match_the_model_and_stay_distinct` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_records_only_lane_rederive.py::test_the_allow_list_is_exactly_the_two_measured_keys` | defect-cited (Backlog: bbb222, review, run-20260922T024054Z); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_records_only_lane_rederive.py::test_the_seam_is_shared_by_both_runners[classify_records_only_conflict_set]` | defect-cited (Backlog: bbb222, review, run-20260922T024054Z); read-required (no-coverage); read-required (pin: module_doc_assertion); delete-candidate (0 unique) |
| `tests/test_records_only_lane_rederive.py::test_the_seam_is_shared_by_both_runners[classify_records_only_front_matter_conflict]` | defect-cited (Backlog: bbb222, review, run-20260922T024054Z); read-required (no-coverage); read-required (pin: module_doc_assertion); delete-candidate (0 unique) |
| `tests/test_records_only_lane_rederive.py::test_the_seam_is_shared_by_both_runners[format_records_only_conflict_refusal_reason]` | defect-cited (Backlog: bbb222, review, run-20260922T024054Z); read-required (no-coverage); read-required (pin: module_doc_assertion); delete-candidate (0 unique) |
| `tests/test_records_only_lane_rederive.py::test_the_seam_is_shared_by_both_runners[integrate_lane_branch]` | defect-cited (Backlog: bbb222, review, run-20260922T024054Z); read-required (no-coverage); read-required (pin: module_doc_assertion); delete-candidate (0 unique) |
| `tests/test_records_only_lane_rederive.py::test_the_seam_is_shared_by_both_runners[rederive_front_matter]` | defect-cited (Backlog: bbb222, review, run-20260922T024054Z); read-required (no-coverage); read-required (pin: module_doc_assertion); delete-candidate (0 unique) |
| `tests/test_recovone_single_definition.py::TestSingleDefinitionIdentity::test_identity_pins` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_red_ci_stop.py::test_case_b_override_runs_and_records_reason_in_events_and_summary` | read-required (pin: md_doc_prose) |
| `tests/test_release_sentinel_succession.py::TestReleaseSentinelSuccession::test_check_release_gates_agent_cli_exits_nonzero_in_bad_states` | defect-cited (x4vf9p); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_release_sentinel_succession.py::TestReleaseSentinelSuccession::test_override_flag_permits_write_records_history_refuses_empty` | defect-cited (x4vf9p); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_release_sentinel_succession.py::TestReleaseSentinelSuccession::test_set_shipped_refuses_last_planned_preserves_bytes` | defect-cited (x4vf9p); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_release_sentinel_succession.py::TestReleaseSentinelSuccession::test_set_shipped_succeeds_when_successor_exists` | defect-cited (x4vf9p); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_releases.py::ReleasesClassTests::test_deep_cleanup_includes_releases` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_releases_cli.py::ReleasesDocsTests::test_releases_readme_documents_the_owner_verb` | defect-cited (w0ln4q); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_releases_cli.py::ReleasesParserTests::test_no_releases_check_subcommand` | defect-cited (w0ln4q); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_replay_coverage_diff.py::TestCoverageRefusal::test_coverage_not_installed_refusal` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_def_line_exclusion_uncalled_function_absent` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_main_flow_contexts` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_main_flow_exclusive_and_shared_lines` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_stale_baseline_refusal` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_subprocess_only_flag` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_research_descriptive_safety.py::TestHelperContract::test_helper_refuse_unsafe_descriptive_contract` | defect-cited (deftzy); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_research_set_assign_date_containment.py::TestMechanismAndDetectionBlindness::test_git_index_inconsistency_after_shutil_move` | defect-cited (plb8jx); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_research_set_assign_date_containment.py::TestMechanismAndDetectionBlindness::test_mechanism_git_mv_refusal_and_shutil_fallback` | defect-cited (7sy2gm, ki1uqk); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_retry_class_mapping.py::test_derivation_is_single_source_of_truth` | defect-cited (25kzda, 4gx141, rb4wgj); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_retry_class_mapping.py::test_vocabulary_coverage_is_one_directional` | defect-cited (25kzda, 4gx141, rb4wgj); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_review_failure_reason.py::ReviewFailureReasonIntegrationTests::test_case_a_child_review_content_filter_error` | defect-cited (ckxypc); read-required (pin: md_doc_prose) |
| `tests/test_run_analytics.py::ModelAttributionTests::test_case_7_cost_attribution_key_agreement` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_analytics_privacy_docs.py::RunAnalyticsPrivacyDocTests::test_detector_covered_and_blind_spot_lists_match_code_as_sets` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_analytics_privacy_docs.py::RunAnalyticsPrivacyDocTests::test_every_detector_blind_spot_is_NAMED_in_the_documentation` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_analytics_privacy_docs.py::RunAnalyticsPrivacyDocTests::test_no_document_claims_an_artifact_PASSES_the_sanitizer` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_analytics_privacy_docs.py::RunAnalyticsPrivacyDocTests::test_the_analytics_doc_exists_and_is_linked_from_the_index` | read-required (no-coverage); read-required (pin: md_doc_prose); delete-candidate (0 unique) |
| `tests/test_run_analytics_privacy_docs.py::RunAnalyticsPrivacyDocTests::test_the_documentation_covers_every_audience_this_plan_owes` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_analytics_privacy_docs.py::RunAnalyticsPrivacyDocTests::test_the_documentation_distinguishes_measured_derived_and_missing` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_analytics_privacy_docs.py::RunAnalyticsPrivacyDocTests::test_the_documentation_states_the_no_anonymity_and_no_causation_limits` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_analytics_statistics.py::PricingTests::test_pricing_eras_boundaries_and_rates` | read-required (pin: hasattr_prod) |
| `tests/test_run_dashboard.py::RenderTests::test_assets_ship_beside_module` | read-required (no-coverage); read-required (pin: read_prod_source); delete-candidate (0 unique) |
| `tests/test_run_dashboard.py::TestUnifiedToolExtractionRouting::test_dashboard_schema_version_is_6` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_abort_class_set_is_verbatim_from_spec_4_1` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_abort_tristate_agrees_with_the_specs_action_text` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_every_bound_codes_predicate_actually_resolves` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_every_code_records_a_known_binding_state` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_every_failure_action_is_verbatim_from_the_spec` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_every_message_carries_the_specs_recovery_command` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_every_message_is_verbatim_from_the_spec` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_inspects_and_pass_criterion_are_verbatim_from_the_spec` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_spec_defines_exactly_twelve_run_codes` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestUnverifiableOkAggregateNeutrality::test_exit_table_is_spec_5_6_not_the_run_cli_inspection_table` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_evidence_completion.py::TestUnverifiableOkAggregateNeutrality::test_non_maskable_classes_match_the_spec_text` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_finding_abort_partition.py::TestRunFindingAbortPartition::test_spec_action_cells_match_module_actions_byte_for_byte` | defect-cited (25kzda, action); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_finding_abort_partition.py::TestRunFindingAbortPartition::test_spec_defines_exactly_twelve_run_codes` | defect-cited (25kzda); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_every_bound_code_has_resolving_predicate_anti_rot` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_finding_spec_transcription.py::TestRunFindingSpecTranscription::test_mutation_sensitivity` | defect-cited (25kzda, xjmjq4); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_finding_spec_transcription.py::TestRunFindingSpecTranscription::test_non_vacuous_parse` | defect-cited (25kzda, xjmjq4); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_finding_spec_transcription.py::TestRunFindingSpecTranscription::test_spec_transcription_byte_equality` | defect-cited (25kzda, xjmjq4); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_recovery_cli.py::TestLedgerResolutionAndWrongFormatVerdict::test_run_engine_step_sequence_without_run_header_refuses_ledger_creation` | read-required (pin: hasattr_prod) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchGuardFalsifiabilityTests::test_allows_the_anchored_gitignore_pattern` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchGuardFalsifiabilityTests::test_allows_the_bare_segment_name_used_as_code` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchGuardFalsifiabilityTests::test_allows_the_installer_template_filename` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchGuardFalsifiabilityTests::test_allows_the_live_prefixed_path` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchGuardFalsifiabilityTests::test_detects_reintroduced_bare_reference` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchGuardFalsifiabilityTests::test_detects_two_references_on_one_line` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchGuardFalsifiabilityTests::test_sweep_detects_poisoned_docs_page` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchGuardFalsifiabilityTests::test_sweep_detects_poisoned_root_doc` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchGuardFalsifiabilityTests::test_sweep_detects_poisoned_shipped_body` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchGuardFalsifiabilityTests::test_sweep_honors_root_doc_exclusions` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchPathTests::test_docs_dir_exists` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchPathTests::test_no_bare_run_scratch_path_in_swept_surfaces` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchPathTests::test_no_doubled_aw_prefix_in_swept_surfaces` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_scratch_path_guard.py::ShippedRunScratchPathTests::test_shipped_dir_exists` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_viewer.py::LiveRunsGuardSelfTests::test_fixture_fails_a_test_that_reads_a_guarded_root` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_viewer.py::LiveRunsGuardSelfTests::test_guard_ignores_unguarded_and_existence_probes` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_run_viewer.py::LiveRunsGuardSelfTests::test_guard_records_a_read_under_a_guarded_root` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runfresh_end_to_end.py::RunfreshEndToEndTests::test_e01_pre_run_linter_drift` | defect-cited (25kzda, hohlc6, review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runfresh_end_to_end.py::RunfreshEndToEndTests::test_e02_agy_restart_disabled` | defect-cited (25kzda, hohlc6, review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runfresh_end_to_end.py::RunfreshEndToEndTests::test_e02_agy_restart_enabled` | defect-cited (25kzda, hohlc6, review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runfresh_end_to_end.py::RunfreshEndToEndTests::test_e02_oc_restart_disabled` | defect-cited (25kzda, hohlc6, review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runfresh_end_to_end.py::RunfreshEndToEndTests::test_e02_oc_restart_enabled` | defect-cited (25kzda, hohlc6, review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runfresh_end_to_end.py::RunfreshEndToEndTests::test_e05_nested_call_pin_reestablished_after_exec` | defect-cited (25kzda, hohlc6, review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_backlog_close_behavior.py::TestShutdownReportOnInterrupt::test_the_callable_is_handler_safe` | defect-cited (exists, record, review, status); read-required (pin: hasattr_prod) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[_read_from_backlog]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[emit_shutdown_report]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[evaluate_backlog_close]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[record_unclosed_backlog_items]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[register_signal_report]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[render_runs_pointer]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[render_unclosed_report]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[resolve_backlog_item]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[run_earned_paths]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[signal_report_callback]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity[unclosed_backlog_items]` | defect-cited (1o7i7g); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerHostIndependence::test_host_independence_with_peer_blocked[agy_runipd-oc_runipd]` | defect-cited (1o7i7g); read-required (pin: sys_modules_check); delete-candidate (0 unique) |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerHostIndependence::test_host_independence_with_peer_blocked[oc_runipd-agy_runipd]` | defect-cited (1o7i7g); read-required (pin: sys_modules_check); delete-candidate (0 unique) |
| `tests/test_runner_fallback_bindings.py::test_fallback_integrate_review_lane_branch_forwards_host_equivalent_arguments` | defect-cited (vfjw09); read-required (pin: hasattr_prod); speed-up (duration 2.54s > 2s) |
| `tests/test_runner_fork_scan_constants.py::test_host_pair_divergent_constant_reported_with_values` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_fork_scan_constants.py::test_same_value_different_reference_not_divergent` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_fork_scan_constants.py::test_three_way_matches_neither` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_fork_scan_constants.py::test_tuple_target_constant_collected_in_unresolved` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_fork_scan_constants.py::test_unresolvable_chain_reported_in_unresolved` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_profiles.py::PerHostValidateDefaultTests::test_every_registered_row_declares_a_real_bool_posture` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_profiles.py::RolesExtendVerifyWithTests::test_the_provenance_vocabulary_stays_a_closed_renderable_set` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_profiles.py::RolesExtendVerifyWithTests::test_verify_with_is_neither_removed_nor_renamed` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_profiles.py::SchemaVersionCompatibilityTests::test_the_module_writes_2_and_reads_1_and_2` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_profiles.py::SourceAuditTests::test_every_error_class_derives_from_one_base` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_profiles.py::SourceAuditTests::test_no_arbitrary_argv_or_credential_field_is_persistable` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runner_profiles.py::VerifyWithSchemaTests::test_verify_with_is_not_a_forbidden_injection_surface_field` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runwire_verifier_authority.py::test_authority_rules_agreement` | defect-cited (checks, eow7p4); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runwire_verifier_authority.py::test_host_verifier_gating_defaults_measured` | defect-cited (a8yn86, qkzet8); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_runwire_verifier_authority.py::test_set_level_checks` | defect-cited (checks, eow7p4); read-required (pin: hasattr_prod, sys_modules_check); delete-candidate (0 unique) |
| `tests/test_runwire_verifier_authority.py::test_verify_disp_vocabulary_unchanged` | defect-cited (checks, eow7p4); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_selector_two_dialect_readers.py::HarnessProvenanceTests::test_harness_measures_workspace_package` | read-required (no-coverage); read-required (pin: read_prod_source); delete-candidate (0 unique) |
| `tests/test_set_dispatch_parity.py::TestNormalizersSubstitute::test_normalizers_substitute_on_real_record` | defect-cited (afdmn6, wy9aru); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_severity_tier_contract.py::SeverityTierContractTests::test_rule_registry_contains_at_least_one_advisory_info_rule` | defect-cited (wm40yl); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_severity_tier_contract.py::SeverityTierContractTests::test_rule_registry_severities_conform_to_canonical_enum` | defect-cited (wm40yl); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_shared_flag_honored.py::test_known_broken_citations_resolve` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_shared_flag_honored.py::test_known_broken_no_dead_entries` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_spec_path_citations.py::test_package_source_spec_path_citations_resolve` | read-required (no-coverage); read-required (pin: read_prod_source); delete-candidate (0 unique) |
| `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_the_rule_is_registered_as_an_error_with_its_invariant` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_spec_review_attestation.py::ManifestAndDocumentationTests::test_no_generated_projection_to_compile_for_this_package` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_spec_review_attestation.py::ManifestAndDocumentationTests::test_the_index_attributes_spec_review_not_plan_review` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_spec_review_attestation.py::SharedVocabularyTests::test_the_body_names_exactly_the_shared_verdicts` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_spec_review_attestation.py::WorkflowPackageTests::test_every_mention_of_a_forbidden_act_is_a_prohibition` | defect-cited (passes, review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_spec_review_attestation.py::WorkflowPackageTests::test_the_body_does_not_apply_the_ipd_ev_rubric` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_spec_review_attestation.py::WorkflowPackageTests::test_the_body_does_not_restate_the_shared_severity_glosses` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_spec_review_attestation.py::WorkflowPackageTests::test_the_package_carries_every_load_bearing_element` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_spec_review_attestation.py::WorkflowPackageTests::test_the_package_has_both_a_body_and_a_readme` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_spec_review_attestation.py::WorkflowPackageTests::test_the_rubric_asks_spec_questions_not_plan_questions` | defect-cited (rubric, spec-shaped); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_set_declaration_agreement` | read-required (pin: hasattr_prod); consolidate (identical peer) |
| `tests/test_specs_metadata_duplicate_bullet.py::TestSpecsMetadataDuplicateBullet::test_rule_registry_entry` | defect-cited (1znlxy, yields); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_specs_releases_descriptive_safety.py::SpecsReleasesDescriptiveSafetyTests::test_helper_refuse_unsafe_descriptive_contract` | defect-cited (across, uz05bl); read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_specs_status_dirs.py::LiveSpecsTreeInvariantTests::test_specs_readme_documents_layout_and_has_no_en_or_em_dashes` | defect-cited (1bdxcp, r9uvwc, status); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_covering_array_generator_contract` | defect-cited (mat9bt); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_support_section.py::SectionExtractorTests::test_absent_end_marker_raises_and_points_to_final_section` | defect-cited (78rxzc); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_support_section.py::SectionExtractorTests::test_absent_start_marker_raises` | defect-cited (78rxzc); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_support_section.py::SectionExtractorTests::test_anchored_skips_body_prose_and_anchored_false_matches_prose` | defect-cited (78rxzc); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_support_section.py::SectionExtractorTests::test_bounded_section_extraction` | defect-cited (78rxzc); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_support_section.py::SectionExtractorTests::test_end_marker_search_starts_after_start_marker` | defect-cited (78rxzc); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_support_section.py::SectionExtractorTests::test_final_section_terminal_success_and_refusal` | defect-cited (78rxzc); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_support_section.py::SectionExtractorTests::test_marker_only_in_prose_refuses_anchored_and_points_to_anchored_false` | defect-cited (78rxzc); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_support_section.py::SectionExtractorTests::test_section_bound_error_is_assertion_error_subclass` | defect-cited (78rxzc); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_support_section.py::SectionExtractorTests::test_section_lines_agreement_and_refusal` | defect-cited (78rxzc); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_suppress_narrowing.py::test_collect_lane_submissions_absorbs_oserror` | defect-cited (8o709f, cv5n6t); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_suppress_narrowing.py::test_e02_guard_unit_isolation_none_handle` | defect-cited (8o709f, cv5n6t); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_tabulated_test_convention.py::TestTabulatedTestConvention::test_contributing_carries_pointer_to_p16_subsection` | defect-cited (prj0vm); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_tabulated_test_convention.py::TestTabulatedTestConvention::test_guiding_principles_p16_carries_tabulated_convention_subsection` | defect-cited (prj0vm); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_term.py::AuthoredSixteenColorPaletteTests::test_palette_coverage_named_colors_separations_and_collapses` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::AuthoredSixteenColorPaletteTests::test_validator_rejects_corrupted_palettes` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_term.py::CapabilityMatrixTests::test_force_color_and_16_color_profiles` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_term.py::CapabilityMatrixTests::test_standard_profiles_1_to_6` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::CliNeverLeaksTheColorOverrideTests::test_early_exit_paths_and_nested_invocations` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_term.py::CliNeverLeaksTheInteractivityOverrideTests::test_early_exit_paths_and_nested_invocations` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_term.py::ColorDepthConfigContractTests::test_config_enum_matches_resolver` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::ColorDepthEndToEndLadderTests::test_end_to_end_ladder_observable_ansi_rendering` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::ColorDepthPrecedenceTests::test_rung1_color_off_and_accessibility_convention` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::ColorDepthPrecedenceTests::test_rung2_pinned_depth_overrides_detection` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::ColorDepthPrecedenceTests::test_rung3_and_rung4_detection_and_defaults` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_term.py::ColorPrecedenceTests::test_precedence_rungs_flag_beats_env_beats_detection` | read-required (pin: ast_parse_walk, inspect_getsource); consolidate (identical peer) |
| `tests/test_term.py::ColorPrecedenceTests::test_process_wide_override_and_namespace` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_term.py::CompactFormAndLegendTests::test_lifecycle_compact_and_legend` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::EveryTierKeepsTheInvariantTests::test_invariant_glyph_and_word_preserved_across_tiers` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::FullRowStylingTests::test_lifecycle_row_styling` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_term.py::GraphemeSafetyTests::test_encoding_safety_ascii_and_presentation` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::GraphemeSafetyTests::test_grapheme_width_variation_selectors_and_ansi` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::GraphemeSafetyTests::test_visible_truncation_safety` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::InteractivityAndColorIndependenceTests::test_2x2_independence_matrix` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::LifecycleColorDepthCrossSurfaceCliTests::test_cross_surface_cli_color_depth_ladder` | defect-cited (Backlog: Sample); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::LifecycleColorDepthSeamSweepTests::test_seam_sweep_across_all_stages_tiers_and_streams` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::LifecycleDepthConsumerTests::test_lifecycle_depth_consumer_and_two_consumer_agreement` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::ResolutionIsSeparateFromRenderingTests::test_resolution_is_pure_data_and_deterministic` | read-required (pin: ast_parse_walk, inspect_getsource) |
| `tests/test_term.py::ResolutionIsSeparateFromRenderingTests::test_term_delegates_to_lifecycle_style` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::ShouldColorGridTests::test_force_color_extended_falsey_and_forcing` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::ShouldColorGridTests::test_force_color_falsey_membership` | read-required (no-coverage); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::ShouldColorGridTests::test_should_color_grid_expectations` | read-required (pin: ast_parse_walk, inspect_getsource); consolidate (identical peer) |
| `tests/test_term.py::ShouldColorTests::test_should_color_basics_and_tty` | read-required (pin: ast_parse_walk, inspect_getsource); consolidate (identical peer) |
| `tests/test_term.py::StylingTests::test_attention_shared_lifecycle_integration` | read-required (pin: hasattr_prod); delete-candidate (0 unique) |
| `tests/test_term.py::StylingTests::test_colorize_and_256_styling` | read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_term.py::WorkedCasesContractTests::test_worked_cases_table_matches_should_color` | read-required (pin: ast_parse_walk, inspect_getsource); consolidate (identical peer) |
| `tests/test_terminal_status_vocabulary.py::TestArtifactAuditNoCompleteCoercion::test_artifact_audit_module_constants` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_terminal_status_vocabulary.py::TestExecutionSuccessStatesNarrowingAndBlastRadius::test_execution_success_states_narrowed_and_identical` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_terminal_status_vocabulary.py::TestInterruptedPromotion::test_interrupted_is_canonical_terminal_and_distinct_from_fail_gate` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_canonical_terminal_states_set` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_object_identity_re_export_across_hosts` | read-required (no-coverage); read-required (pin: assert_is_host_attr); delete-candidate (0 unique) |
| `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_terminal_states_union` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_terminal_status_aliases_map` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_terminal_status_vocabulary.py::TestWriterCanonicalEmissionsAndFourWaySplit::test_four_way_split_producers` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_testprune_tools.py::test_covctx_plugin_subprocess_context_propagation` | defect-cited (qqrgv3); read-required (no-coverage); speed-up (duration 2.50s > 2s); delete-candidate (0 unique) |
| `tests/test_turn_bounds.py::test_constants_names_defaults_and_zero_disable` | defect-cited (7ckptx); read-required (pin: hasattr_prod) |
| `tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit` | defect-cited (m7fllj); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_uncollected_test_modules.py::UncollectedTestModulesGuardTests::test_evaluate_test_module_collection_synthetic_inputs` | defect-cited (5s31xp, 96xtmi, n8adhb); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_usage_refusal_agent_record.py::test_exclusion_set_size_and_members` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_v_item_demonstration_reachability.py::TestVItemDemonstrationReachability::test_long_form_review_rubric_reachability_rule_parity` | defect-cited (review); read-required (no-coverage); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_v_item_demonstration_reachability.py::TestVItemDemonstrationReachability::test_scaffolded_validation_intro_carries_reachability_rule` | defect-cited (76ic0k, 9aprci, review, ua133b); read-required (pin: ast_parse_walk, inspect_getsource); consolidate (identical peer) |
| `tests/test_v_item_demonstration_reachability.py::TestVItemDemonstrationReachability::test_single_file_plan_review_reachability_rule` | defect-cited (review); read-required (no-coverage); read-required (pin: ast_parse_walk, inspect_getsource); delete-candidate (0 unique) |
| `tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_long_form_plan_review_evidence_durability_parity` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_single_file_plan_review_evidence_durability` | defect-cited (review); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_spec_section_5_4_evidence_reachability` | defect-cited (5q9a6a, review, vtup6x, xl1iko); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_verification_sendback.py::VerificationRetryDecisionUnitTests::test_cross_driver_object_identity` | defect-cited (t18l64); read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_verifier_corroboration.py::TestCorroborationInteractionAndOutcomeEquality::test_cross_driver_symmetry` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_verifier_corroboration.py::TestSharedToolCallExtraction::test_behavioral_import_purity` | read-required (pin: sys_modules_check); delete-candidate (0 unique) |
| `tests/test_verifier_evidence.py::ExecutionReportRenderingTests::test_write_report_omits_section_when_no_verification_evidence` | defect-cited (run-20260924T000000Z); read-required (pin: md_doc_prose); consolidate (identical peer) |
| `tests/test_verifier_evidence.py::ExecutionReportRenderingTests::test_write_report_renders_verification_evidence_section` | defect-cited (run-20260924T000000Z); read-required (pin: md_doc_prose) |
| `tests/test_verifier_evidence.py::RunnerVerificationGateTests::test_cross_driver_symmetry` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_versioning.py::BakedVersionGuardTests::test_baked_version_is_a_clean_release_string` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_versioning.py::BakedVersionGuardTests::test_baked_version_matches_tag_when_head_is_a_release_tag` | read-required (no-coverage); delete-candidate (0 unique) |
| `tests/test_worktree_lease_stdlib_only.py::WorktreeLeaseStdlibOnlyTests::test_lane_merged_into_target_lazy_delegation` | defect-cited (d8sc5n, rdl9lh); read-required (pin: sys_modules_check); delete-candidate (0 unique) |
| `tests/test_worktree_lease_stdlib_only.py::WorktreeLeaseStdlibOnlyTests::test_worktree_lease_imports_no_first_party_modules` | defect-cited (d8sc5n, rdl9lh); read-required (pin: sys_modules_check); delete-candidate (0 unique) |
| `tests/test_write_report_malformed_entry.py::test_well_formed_report_byte_identical_to_fixture` | read-required (pin: md_doc_prose); delete-candidate (0 unique) |

## Slow Tests (Duration > 2.0s, 273 total)
Tests exceeding 2.0 seconds wall time during the baseline instrumented run targeted for speed-up or fixture optimization:

| Test Node ID | Wall Time (s) |
| --- | --- |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_heavy[doctor]` | 302.97s |
| `tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun` | 51.83s |
| `tests/test_suite_cache.py::test_collection_error_and_corrupt_or_expired_records` | 35.90s |
| `tests/test_suite_cache.py::test_reproducible_failure_stored_and_not_served_to_seam` | 33.70s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_heavy[attention]` | 32.55s |
| `tests/test_shared_flag_honored.py::test_partition_fields_branch_behavior` | 31.42s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[status]` | 28.79s |
| `tests/test_suite_cache.py::test_pass_stored_and_served` | 26.67s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[ipd lint]` | 26.63s |
| `tests/test_usage_refusal_agent_record.py::test_e04_missing_required_handler_leaves[leaf_tokens0-backlog new]` | 26.27s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[next]` | 22.39s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[releases readiness]` | 19.58s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[checkup]` | 18.82s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_heavy[status]` | 18.65s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[checkup]` | 16.81s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[releases readiness]` | 16.25s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[releases readiness]` | 16.22s |
| `tests/test_suite_cache.py::test_flaky_failure_not_stored` | 15.91s |
| `tests/test_run_init.py::test_case_d_refusals_leave_filesystem_unchanged` | 15.91s |
| `tests/test_run_init.py::test_case_b_follow_on_sequence` | 15.23s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[next]` | 14.70s |
| `tests/test_record_owner_root.py::test_ipd_coverage_from_clean_target_root` | 14.50s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[checkup]` | 14.40s |
| `tests/test_record_owner_root.py::test_resolver_ignores_non_record_paths` | 14.21s |
| `tests/test_record_owner_root.py::test_ipd_lint_resolves_home_sibling_dependency` | 14.10s |
| `tests/test_record_owner_root.py::test_group_a_walkers_return_target` | 13.83s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[next]` | 13.78s |
| `tests/test_system_root_accessor.py::test_read_side_clean_delta_home_bundle` | 13.77s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[releases show]` | 13.47s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[status]` | 12.80s |
| `tests/test_run_init.py::test_case_i_dag_execution_without_workflow_flag` | 12.53s |
| `tests/test_suite_cache.py::test_suite_thorough_explain_differs_and_narrowed_selection_refused` | 11.66s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[lanes list]` | 11.31s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[releases show]` | 11.18s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[lanes list]` | 10.84s |
| `tests/test_run_proposal_channel.py::test_material_proposal_creates_backlog_item_on_main[oc]` | 10.76s |
| `tests/test_config_agent_surface.py::test_config_exclude_add_and_rm_lifecycle_agent` | 10.75s |
| `tests/test_run_cli_declarations.py::test_runs_status_declared_exit_codes_are_reachable` | 10.59s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[partition]` | 10.49s |
| `tests/test_run_proposal_channel.py::test_three_item_continuation_e03[oc]` | 10.12s |
| `tests/test_system_root_accessor.py::test_write_side_clean_delta_install` | 10.07s |
| `tests/test_run_proposal_channel.py::test_material_proposal_creates_backlog_item_on_main[agy]` | 10.02s |
| `tests/test_record_owner_root.py::test_identity_rename_hint_for_home_record` | 9.97s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[releases show]` | 9.83s |
| `tests/test_run_proposal_channel.py::test_small_proposal_creates_draft_plan_on_main[oc]` | 9.60s |
| `tests/test_run_proposal_channel.py::test_injection_attempt_neutralized[agy]` | 9.55s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[status]` | 9.32s |
| `tests/test_run_cli_declarations.py::test_runs_next_declared_exit_codes_are_reachable` | 9.08s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[runs submit]` | 9.07s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[partition]` | 8.59s |
| `tests/test_run_cli_declarations.py::test_runs_resume_declared_exit_codes_are_reachable` | 8.48s |
| `tests/test_release_readiness_not_applicable.py::test_cli_surfaces_not_applicable_in_every_mode` | 8.45s |
| `tests/test_record_owner_root.py::test_specs_note_history_lands_in_project_records` | 8.30s |
| `tests/test_record_owner_root.py::test_install_writes_back_pointer_without_target_delta` | 8.23s |
| `tests/test_suite_cache.py::test_narrowed_selection_refused` | 8.05s |
| `tests/test_run_proposal_channel.py::test_injection_attempt_neutralized[oc]` | 7.86s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[research check-refs]` | 7.82s |
| `tests/test_agent_user_config_containment.py::test_incident_end_to_end_per_host` | 7.76s |
| `tests/test_releases_readiness_cli.py::test_arm_f_agent_mode_emits_schema_valid_record_with_exit_and_diagnostic_parity` | 7.72s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[graduation]` | 7.72s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[sanitize]` | 7.66s |
| `tests/test_atomic_write_mode.py::test_plan_preserve_mode_on_rewrite` | 7.62s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[suite]` | 7.60s |
| `tests/test_release_readiness.py::test_build_report_nonconforming_plan_flips_only_ipd_lint` | 7.57s |
| `tests/test_run_proposal_channel.py::test_three_item_continuation_e03[agy]` | 7.53s |
| `tests/test_read_class_callers_refuse.py::test_root_controls_see_seeded_observables` | 7.39s |
| `tests/test_suite_slot_lock.py::test_stall_watchdog_heartbeat_e2e_agy` | 7.30s |
| `tests/test_read_class_callers_refuse.py::test_research_check_miscategorized_refuses_human_only` | 7.28s |
| `tests/test_suite_slot_lock.py::test_stall_watchdog_heartbeat_e2e_oc` | 7.25s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[check-local-leaks]` | 7.03s |
| `tests/test_read_class_callers_refuse.py::test_write_targets_on_surveyable_root` | 6.94s |
| `tests/test_run_proposal_channel.py::test_coordinator_performer_retries_on_raced_tip` | 6.90s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[lanes list]` | 6.87s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[ipd lint]` | 6.75s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[graduation]` | 6.70s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[suite]` | 6.68s |
| `tests/test_atomic_write_mode.py::test_ipd_scaffold_and_terminal_set_mode` | 6.67s |
| `tests/test_rename_group_machine_output.py::test_human_stdout_byte_identical` | 6.50s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[ipd lint]` | 6.42s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[ipd lint]` | 6.28s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_mutation[suite]` | 6.07s |
| `tests/test_shared_flag_honored.py::test_config_json_refusals_branch_behavior` | 6.03s |
| `tests/test_run_proposal_channel.py::test_small_proposal_creates_draft_plan_on_main[agy]` | 5.90s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[lanes prune]` | 5.84s |
| `tests/test_rename_group_machine_output.py::test_stdout_parses_plans_and_research` | 5.77s |
| `tests/test_record_owner_root.py::test_resolver_maps_home_record_from_unrelated_cwd` | 5.75s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[research check-miscategorized]` | 5.74s |
| `tests/test_atomic_write_mode.py::test_adopt_mode` | 5.61s |
| `tests/test_read_class_callers_refuse.py::test_research_mutations_negative_control_sub` | 5.57s |
| `tests/test_atomic_write_mode.py::test_umask_002_mode` | 5.48s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[research check-refs]` | 5.47s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[graduation]` | 5.36s |
| `tests/test_atomic_write_mode.py::test_research_new_mode` | 5.35s |
| `tests/test_run_proposal_channel.py::test_needs_attended_proposal_marks_plan_and_files_no_stub[oc]` | 5.35s |
| `tests/test_mutation_result_facts.py::test_human_stdout_byte_identical` | 5.28s |
| `tests/test_record_owner_root.py::test_resolver_rejects_stale_or_foreign_back_pointer` | 5.26s |
| `tests/test_record_owner_root.py::test_resolver_maps_home_record_to_target_from_target_cwd` | 5.21s |
| `tests/test_run_init.py::test_case_m_deleted_workflow_json_falls_back` | 5.15s |
| `tests/test_atomic_write_mode.py::test_install_leaves_managed_sections_644` | 5.11s |
| `tests/test_fresh_target_install_regression.py::test_install_d05_no_root_state_files` | 5.10s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[partition]` | 5.09s |
| `tests/test_shared_flag_honored.py::test_ipd_coverage_fields_branch_behavior` | 4.94s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[backlog new]` | 4.92s |
| `tests/test_shared_flag_honored.py::test_oc_models_fields_branch_behavior` | 4.91s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[index]` | 4.91s |
| `tests/test_run_cli_corruption_exit.py::test_corrupted_ledger_readers[status]` | 4.88s |
| `tests/test_fresh_target_install_regression.py::test_research_composition_d10_d11_d12` | 4.86s |
| `tests/test_shared_flag_honored.py::test_upgrade_test_json_harness_error_and_redaction` | 4.73s |
| `tests/test_no_project_exit_is_cannot_run.py::test_no_project_cross_surface_exit_and_payload[git-todo]` | 4.73s |
| `tests/test_releases_readiness_cli.py::test_arm_g_json_output_verdict_matches_exit_code` | 4.64s |
| `tests/test_run_proposal_channel.py::test_malformed_proposal_handled_normally[oc]` | 4.62s |
| `tests/test_runner_fallback_bindings.py::test_host_preference_preserved_for_shipped_hosts` | 4.58s |
| `tests/test_records_root_accessor.py::test_home_records_find_attention_check` | 4.53s |
| `tests/test_severity_truth_surfaces.py::test_attention_diagnostic_preserves_drift_severity_and_exit_code` | 4.49s |
| `tests/test_releases_readiness_cli.py::test_arm_i_release_alias_is_byte_identical_under_agent` | 4.46s |
| `tests/test_fresh_target_install_regression.py::test_install_doctor_zero_dangling_references` | 4.42s |
| `tests/test_core_smoke.py::test_smoke_host_capabilities_json` | 4.40s |
| `tests/test_install_inbox_lane.py::test_attention_board_inbox_footer` | 4.36s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[research check-refs]` | 4.36s |
| `tests/test_shared_flag_honored.py::test_upgrade_test_clean_json_branches` | 4.31s |
| `tests/test_install_inbox_lane.py::test_fresh_install_inbox_lane` | 4.29s |
| `tests/test_releases_readiness_cli.py::test_arm_a_go_tree_exits_0_and_renders_go_verdict` | 4.28s |
| `tests/test_readiness_absence_invariant.py::test_corpus_partition_pre_review_plans_lack_readiness_field` | 4.26s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[research check-refs]` | 4.19s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[agy profile add]` | 4.09s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[host capabilities]` | 4.09s |
| `tests/test_install_inbox_lane.py::test_upgrade_from_seeded_inbox_gitignore` | 4.06s |
| `tests/test_records_root_accessor.py::test_home_records_runner_discovery` | 4.06s |
| `tests/test_read_class_callers_refuse.py::test_read_verbs_refuse_explicit_subdir_human_and_agent[cmd_prefix2]` | 4.03s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[index]` | 4.02s |
| `tests/test_suite_cache.py::test_suite_key_stability_sensitivity_and_zero_side_effects` | 3.96s |
| `tests/test_run_init.py::test_case_e_default_id_generation` | 3.94s |
| `tests/test_suite_slot_lock.py::test_slot_timeout_runs_anyway_with_warning` | 3.86s |
| `tests/test_run_proposal_channel.py::test_malformed_proposal_handled_normally[agy]` | 3.86s |
| `tests/test_run_cli_corruption_exit.py::test_missing_ledger_reports_invalid_invocation` | 3.85s |
| `tests/test_rename_group_machine_output.py::test_stdout_parses_specs_and_backlog` | 3.83s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[check-local-leaks]` | 3.75s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[precommit-scope-gate]` | 3.74s |
| `tests/test_install_source_option.py::test_install_with_source_string_end_to_end` | 3.74s |
| `tests/test_install_inbox_lane.py::test_nested_sub_readme_in_inbox_is_ignored` | 3.72s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[host capabilities]` | 3.69s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[workflow compile]` | 3.69s |
| `tests/test_cli_checkout_reexec.py::test_11_completion_both_surfaces_silent_and_fast` | 3.69s |
| `tests/test_run_init.py::test_case_f_machine_modes_agent_and_json` | 3.67s |
| `tests/test_agent_surface_conformance.py::test_mutation_exemption_registry_contract` | 3.65s |
| `tests/test_run_proposal_channel.py::test_attended_plan_not_dispatched_at_queue_freeze[agy]` | 3.57s |
| `tests/test_config_agent_surface.py::test_config_exclude_bare_root_agent` | 3.55s |
| `tests/test_shared_flag_honored.py::test_storage_reattach_fields_branch_behavior` | 3.52s |
| `tests/test_release_readiness.py::test_build_report_go_with_live_subprocess_gates` | 3.50s |
| `tests/test_config_agent_surface.py::test_config_remove_success_agent` | 3.48s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[check-local-leaks]` | 3.48s |
| `tests/test_run_init.py::test_case_k_edited_workflow_json_refused` | 3.48s |
| `tests/test_severity_truth_surfaces.py::test_doctor_summary_bucket_count_conservation` | 3.45s |
| `tests/test_rename_group_machine_output.py::test_refusals_are_error_records` | 3.45s |
| `tests/test_agent_user_config_containment.py::test_turn_failure_and_popen_raise_still_reconciles` | 3.44s |
| `tests/test_run_proposal_channel.py::test_needs_attended_proposal_marks_plan_and_files_no_stub[agy]` | 3.43s |
| `tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[resume]` | 3.41s |
| `tests/test_agent_user_config_containment.py::test_aw_config_dir_precedence` | 3.41s |
| `tests/test_git_config_guard.py::test_guard_ignores_non_identity_keys` | 3.41s |
| `tests/test_hang_guard_budget.py::test_subprocess_bound_runaway_loop_caught_by_wall_ceiling` | 3.38s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[backlog check]` | 3.36s |
| `tests/test_read_class_callers_refuse.py::test_read_verbs_refuse_explicit_subdir_human_and_agent[cmd_prefix0]` | 3.35s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[check-local-leaks]` | 3.35s |
| `tests/test_agent_user_config_containment.py::test_read_and_format_discarded_user_config_helpers` | 3.35s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[workflow validate]` | 3.35s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[precommit-scope-gate]` | 3.34s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[host capabilities]` | 3.32s |
| `tests/test_read_class_callers_refuse.py::test_read_verbs_refuse_bare_outside_project[cmd_prefix1]` | 3.25s |
| `tests/test_config_agent_surface.py::test_config_exclude_json_arms` | 3.24s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[host probe]` | 3.23s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[runs show]` | 3.21s |
| `tests/test_selector_type_containment.py::test_must_not_refuse_matrix` | 3.21s |
| `tests/test_releases_readiness_cli.py::test_arm_e_unproven_host_matrix_claim_fails_capability_freshness` | 3.19s |
| `tests/test_spec_citation_anchors.py::test_f_cli_check_specs_source_anchors_agent_clean_reports_clean_exit_zero` | 3.18s |
| `tests/test_suite_slot_lock.py::test_two_slots_concurrent_and_third_waits` | 3.17s |
| `tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[evidence]` | 3.12s |
| `tests/test_config_agent_surface.py::test_config_get_success_agent` | 3.12s |
| `tests/test_suite_slot_lock.py::test_two_subprocesses_serialize_and_print_waiting_line` | 3.07s |
| `tests/test_config_agent_surface.py::test_config_is_success_agent` | 3.05s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[research index]` | 3.04s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[precommit-scope-gate]` | 3.04s |
| `tests/test_run_proposal_channel.py::test_attended_plan_not_dispatched_at_queue_freeze[oc]` | 3.03s |
| `tests/test_runs_machine_output_paths.py::test_evidence_machine_ledger_is_relative[--json]` | 3.03s |
| `tests/test_core_tier_selection.py::test_gate_suite_passes_an_all_green_over_budget_tree[run-evidence]` | 3.02s |
| `tests/test_hang_guard_budget.py::test_guard_under_xdist_workers` | 3.01s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[specs check]` | 2.99s |
| `tests/test_read_class_callers_refuse.py::test_read_verbs_refuse_bare_outside_project[cmd_prefix2]` | 2.98s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[index]` | 2.95s |
| `tests/test_core_tier_selection.py::test_explicit_path_runs_non_core` | 2.94s |
| `tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[next]` | 2.91s |
| `tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[show]` | 2.87s |
| `tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[status]` | 2.86s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_mutation[archive]` | 2.85s |
| `tests/test_run_cli_human_redaction.py::test_runs_evidence_ledger_content_secret_redacted` | 2.81s |
| `tests/test_no_project_exit_is_cannot_run.py::test_no_project_cross_surface_exit_and_payload[git-ipd]` | 2.79s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[host probe]` | 2.78s |
| `tests/test_pwatch_signal_exit.py::test_subprocess_sigterm_exit_143` | 2.76s |
| `tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[verify-ledger]` | 2.75s |
| `tests/test_agent_aw_home_containment.py::test_incident_end_to_end_per_host` | 2.74s |
| `tests/test_read_class_callers_refuse.py::test_read_verbs_refuse_explicit_subdir_human_and_agent[cmd_prefix1]` | 2.72s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[storage attach]` | 2.68s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_mutation[runs analyze]` | 2.66s |
| `tests/test_rename_group_machine_output.py::test_index_verbs_unaffected` | 2.64s |
| `tests/test_read_class_callers_refuse.py::test_releases_new_negative_control_sub` | 2.63s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[backlog check]` | 2.62s |
| `tests/test_hang_guard_budget.py::test_timeout_zero_disables_both_arms` | 2.62s |
| `tests/test_agent_aw_home_containment.py::test_prepare_none_inherits_driver_aw_home_per_host` | 2.62s |
| `tests/test_hang_guard_budget.py::test_marker_above_wall_ceiling_floors_and_raises_wall_allowance` | 2.60s |
| `tests/test_runs_machine_output_paths.py::test_projection_missing_human_line_is_relative` | 2.60s |
| `tests/test_no_project_exit_is_cannot_run.py::test_no_project_cross_surface_exit_and_payload[nongit-todo]` | 2.57s |
| `tests/test_no_project_exit_is_cannot_run.py::test_no_project_cross_surface_exit_and_payload[nongit-ipd]` | 2.55s |
| `tests/test_plans_order_grammar.py::test_bmhoxe_repair_sequence_leaves_well_formed_name` | 2.55s |
| `tests/test_read_class_callers_refuse.py::test_read_verbs_refuse_bare_outside_project[cmd_prefix0]` | 2.54s |
| `tests/test_runner_fallback_bindings.py::test_fallback_integrate_review_lane_branch_forwards_host_equivalent_arguments` | 2.54s |
| `tests/test_runs_machine_output_paths.py::test_evidence_human_has_no_absolute_root` | 2.53s |
| `tests/test_testprune_tools.py::test_covctx_plugin_subprocess_context_propagation` | 2.50s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[host probe]` | 2.49s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[check]` | 2.48s |
| `tests/test_runs_machine_output_paths.py::test_evidence_machine_ledger_is_relative[--agent]` | 2.47s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[backlog-blocking-close-gate]` | 2.47s |
| `tests/test_run_init.py::test_case_f2_agent_honors_fields_projection` | 2.44s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[include]` | 2.42s |
| `tests/test_plans_order_grammar.py::test_allow_invalid_order_does_not_bypass_range_check` | 2.42s |
| `tests/test_selector_type_containment.py::test_six_type_refusal_matrix` | 2.38s |
| `tests/test_runs_machine_output_paths.py::test_verify_ledger_human_has_relative_ledger_line` | 2.38s |
| `tests/test_pwatch_signal_exit.py::test_subprocess_sigint_exit_0` | 2.37s |
| `tests/test_releases_readiness_cli.py::test_arm_c_suite_failed_exits_1_with_full_suite_red` | 2.36s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[storage attach]` | 2.36s |
| `tests/test_git_config_guard.py::test_guard_catches_leak_and_restores_config` | 2.34s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_mutation[storage attach]` | 2.34s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[storage move]` | 2.33s |
| `tests/test_git_config_guard.py::test_guard_disables_itself_on_non_git_target` | 2.33s |
| `tests/test_run_cli_corruption_exit.py::test_corrupted_ledger_readers[resume]` | 2.32s |
| `tests/test_releases_readiness_cli.py::test_arm_b_no_suite_flag_reports_not_supplied_and_emits_stderr_hint` | 2.32s |
| `tests/test_hang_guard_budget.py::test_sleep_past_cpu_budget_inside_wall_ceiling_passes` | 2.31s |
| `tests/test_no_project_exit_is_cannot_run.py::test_no_project_cross_surface_exit_and_payload[nongit-attention]` | 2.31s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_mutation[normalize-lanes]` | 2.31s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read[search]` | 2.29s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[runs next]` | 2.29s |
| `tests/test_runs_machine_output_paths.py::test_show_human_has_relative_ledger_line` | 2.28s |
| `tests/test_records_root_accessor.py::test_home_records_reproduction_prompts_index` | 2.25s |
| `tests/test_hang_guard_budget.py::test_zero_cpu_deadlock_caught_by_wall_ceiling` | 2.24s |
| `tests/test_runs_machine_output_paths.py::test_decisions_machine_output_lists_entry_ids` | 2.21s |
| `tests/test_runs_machine_output_paths.py::test_projection_missing_machine_error[decisions]` | 2.20s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[layout]` | 2.20s |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read[doctor]` | 2.19s |
| `tests/test_no_project_exit_is_cannot_run.py::test_no_project_cross_surface_exit_and_payload[nongit-next]` | 2.18s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[exclude]` | 2.18s |
| `tests/test_records_root_accessor.py::test_bare_unconfigured_repo_parity` | 2.17s |
| `tests/test_runs_machine_output_paths.py::test_projection_human_output_is_file_text[decisions]` | 2.17s |
| `tests/test_runner_fallback_bindings.py::test_fallback_driver_finalize_forwards_host_equivalent_arguments` | 2.16s |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[ipd-dependency-statement-gate]` | 2.16s |
| `tests/test_releases_readiness_cli.py::test_arm_d_missing_signer_exits_1_with_residual_risk_failing` | 2.15s |
| `tests/test_releases_readiness_cli.py::test_arm_j_tree_is_byte_identical_before_and_after_run` | 2.15s |
| `tests/test_run_init.py::test_case_l_workflow_json_array_refused` | 2.15s |
| `tests/test_run_init.py::test_case_j_mismatched_workflow_flag_refused` | 2.13s |
| `tests/test_runs_machine_output_paths.py::test_projection_machine_output_parses_empty[questions---agent]` | 2.13s |
| `tests/test_commit_run_trailers_env.py::test_malformed_values_dropped_with_warning` | 2.12s |
| `tests/test_runs_machine_output_paths.py::test_projection_machine_output_parses_empty[questions---json]` | 2.12s |
| `tests/test_config_agent_surface.py::test_config_is_refusal_syntax_agent` | 2.12s |
| `tests/test_config_agent_surface.py::test_config_unset_success_agent` | 2.12s |
| `tests/test_agent_surface_conformance.py::test_attention_non_project_cwd` | 2.09s |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap[spec check]` | 2.09s |
| `tests/test_run_init.py::test_case_c_second_init_existing_id_refusal` | 2.08s |
| `tests/test_no_project_exit_is_cannot_run.py::test_no_project_cross_surface_exit_and_payload[git-ipd-board]` | 2.07s |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[oc profile add]` | 2.05s |
| `tests/test_run_init.py::test_case_h_init_creates_workflow_json_beside_ledger` | 2.04s |
| `tests/test_rename_group_machine_output.py::test_nested_line_gone_from_human_surface` | 2.04s |
| `tests/test_config_agent_surface.py::test_config_add_refusal_syntax_agent` | 2.03s |
| `tests/test_runs_machine_output_paths.py::test_projection_machine_output_parses_empty[decisions---agent]` | 2.03s |
| `tests/test_lanes_prune.py::test_lanes_list_verdicts` | 2.02s |
| `tests/test_runs_machine_output_paths.py::test_projection_machine_output_parses_empty[decisions---json]` | 2.01s |
| `tests/test_run_cli_corruption_exit.py::test_corrupted_ledger_readers[next]` | 2.00s |

## Per-Module Decision Table

| Module | Tests | Wall (s) | Unique Lines | Unique Arcs | Proposed Disposition | Reason | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `tests/test_action_table_runner_parity.py` | 9 | 0.00 | 18 | 37 | `read-required` | 9 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_agent_aw_home_containment.py` | 9 | 5.82 | 122 | 169 | `speed-up` | 2 tests > 2s | `c8bfp9` |
| `tests/test_agent_checked_count.py` | 13 | 0.00 | 3 | 5 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_agent_commit_identity.py` | 9 | 0.00 | 19 | 27 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_agent_field_projection.py` | 7 | 0.62 | 21 | 43 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_agent_findings_severity.py` | 7 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_agent_record_guard.py` | 9 | 0.00 | 55 | 73 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_agent_schema_paths.py` | 4 | 0.00 | 1 | 2 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_agent_surface_conformance.py` | 86 | 265.35 | 0 | 1 | `speed-up` | protected family/livecorpus/core; 30 tests > 2s | `c8bfp9` |
| `tests/test_agent_user_config_containment.py` | 9 | 19.46 | 78 | 107 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_agents_block_target_neutral.py` | 5 | 0.00 | 10 | 23 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_agy_failed_state_parity.py` | 5 | 0.00 | 1 | 3 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_agy_models.py` | 9 | 0.00 | 6 | 9 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_agy_profile_cli.py` | 12 | 0.00 | 58 | 82 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_agy_run.py` | 44 | 0.00 | 305 | 373 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_agy_run_resolve_ipd_recursive.py` | 10 | 0.00 | 9 | 19 | `consolidate` | 5 tests with identical coverage peers | `83nnyn` |
| `tests/test_agy_run_resolve_spec_recursive.py` | 9 | 0.00 | 3 | 8 | `consolidate` | 7 tests with identical coverage peers | `83nnyn` |
| `tests/test_agy_runipd_cli.py` | 61 | 0.00 | 97 | 139 | `read-required` | 6 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_agy_skill_install.py` | 6 | 0.00 | 17 | 25 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_agy_skip_permissions_default.py` | 11 | 0.00 | 0 | 2 | `consolidate` | 9 tests with identical coverage peers | `83nnyn` |
| `tests/test_agy_tool_name_precedence.py` | 9 | 0.03 | 22 | 30 | `consolidate` | 7 tests with identical coverage peers | `83nnyn` |
| `tests/test_already_landed_dispatch.py` | 14 | 0.00 | 30 | 40 | `consolidate` | 6 tests with identical coverage peers | `83nnyn` |
| `tests/test_artifact_adopt.py` | 39 | 0.00 | 157 | 229 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_artifact_audit.py` | 26 | 0.00 | 109 | 149 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_artifact_audit_cache_eviction.py` | 4 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_artifact_audit_identity_staleness.py` | 6 | 0.00 | 13 | 18 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_artifact_audit_index_cache.py` | 6 | 0.00 | 0 | 0 | `consolidate` | 6 tests with identical coverage peers | `83nnyn` |
| `tests/test_artifact_audit_verdicts.py` | 4 | 0.00 | 0 | 1 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_artifact_core_git_mv_containment.py` | 10 | 0.00 | 6 | 12 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_artifact_naming_round_trip.py` | 4 | 0.00 | 1 | 3 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_artifact_refs_rewrite.py` | 25 | 0.00 | 43 | 68 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_askme_command_delivery.py` | 3 | 0.00 | 0 | 0 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_atomic_write_mode.py` | 7 | 36.92 | 1 | 2 | `speed-up` | 6 tests > 2s | `c8bfp9` |
| `tests/test_attempt_agy_model_observation.py` | 7 | 0.00 | 6 | 14 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_attempt_host_model_observation.py` | 13 | 0.00 | 91 | 117 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_attempt_lane_facts.py` | 7 | 0.00 | 5 | 9 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_attempt_model_consumers.py` | 7 | 0.00 | 4 | 9 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_attempt_model_identity.py` | 11 | 0.00 | 13 | 17 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_attention.py` | 76 | 0.00 | 214 | 335 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_attention_blind_spot.py` | 9 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_attention_contract.py` | 27 | 0.00 | 2 | 5 | `consolidate` | protected family/livecorpus/core; 3 candidate consolidate tests | `83nnyn` |
| `tests/test_attention_degraded_item.py` | 12 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_attention_excluded_tree_selector.py` | 8 | 0.00 | 2 | 5 | `consolidate` | 5 tests with identical coverage peers | `83nnyn` |
| `tests/test_attention_lane_detail_bound.py` | 3 | 0.00 | 2 | 4 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_attention_output_safety.py` | 7 | 0.00 | 8 | 11 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_authoring_coverage_guidance.py` | 6 | 0.00 | 1 | 3 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_aw_upgrade_test.py` | 51 | 0.00 | 360 | 500 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_awphysical_tools.py` | 40 | 0.00 | 357 | 454 | `read-required` | 14 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_backlog.py` | 47 | 0.00 | 92 | 141 | `consolidate` | protected family/livecorpus/core; 12 candidate consolidate tests | `83nnyn` |
| `tests/test_backlog_already_complete.py` | 13 | 0.00 | 233 | 281 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_backlog_close_evidence_plan_disposition.py` | 27 | 0.00 | 12 | 16 | `consolidate` | 9 tests with identical coverage peers | `83nnyn` |
| `tests/test_backlog_close_gate_prose.py` | 3 | 0.18 | 23 | 27 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_backlog_close_host_label.py` | 3 | 0.26 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_backlog_descriptive_safety.py` | 19 | 0.00 | 3 | 5 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_backlog_duplicate_guard.py` | 9 | 0.00 | 58 | 76 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_backlog_gate_follows_status.py` | 18 | 0.00 | 0 | 0 | `consolidate` | 5 tests with identical coverage peers | `83nnyn` |
| `tests/test_backlog_handoff_close.py` | 40 | 0.00 | 28 | 42 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_backlog_history_dedup_parity.py` | 6 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_backlog_history_empty_rule.py` | 7 | 0.96 | 2 | 3 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_backlog_metadata_duplicate_and_gate_summary.py` | 8 | 0.00 | 16 | 27 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_backlog_new_gate_vocabulary.py` | 5 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_backlog_positional_close_gate.py` | 23 | 0.00 | 7 | 10 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_backlog_production.py` | 16 | 0.00 | 73 | 99 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_backlog_set_adapter.py` | 8 | 0.00 | 4 | 6 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_backlog_transition_authority.py` | 8 | 0.00 | 0 | 0 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_backlog_transition_gate.py` | 14 | 0.00 | 3 | 5 | `consolidate` | protected family/livecorpus/core; 1 candidate consolidate tests | `83nnyn` |
| `tests/test_benchmark_runners_reports.py` | 14 | 0.08 | 1196 | 1562 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_bidi_control_rejection.py` | 19 | 0.00 | 0 | 0 | `consolidate` | 18 tests with identical coverage peers | `83nnyn` |
| `tests/test_blocks_release_reader_bounding.py` | 9 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_broken_pipe_exit.py` | 10 | 0.00 | 21 | 34 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_canonical_status_reader_sweep.py` | 10 | 0.00 | 9 | 21 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_capture_command_contract.py` | 11 | 6.46 | 14 | 27 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_capture_command_stream_bounds.py` | 10 | 3.31 | 0 | 0 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_carrier_detail_descriptive_bound.py` | 5 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_carrier_finished_verification.py` | 4 | 0.00 | 62 | 77 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_carrier_reverse_lookup.py` | 4 | 0.00 | 0 | 0 | `delete-candidate` | all 4 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_carrier_ungated_rule.py` | 9 | 0.00 | 27 | 37 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_check_ci_local_parity.py` | 8 | 0.00 | 4 | 9 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_check_engine.py` | 57 | 0.00 | 83 | 130 | `consolidate` | protected family/livecorpus/core; 7 candidate consolidate tests | `83nnyn` |
| `tests/test_check_engine_from_spec_missing.py` | 37 | 0.00 | 48 | 71 | `consolidate` | 16 tests with identical coverage peers | `83nnyn` |
| `tests/test_check_engine_metadata_region.py` | 3 | 0.12 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_check_engine_plan_date_filename.py` | 7 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_check_engine_release_gate.py` | 52 | 0.00 | 82 | 127 | `consolidate` | protected family/livecorpus/core; 5 candidate consolidate tests | `83nnyn` |
| `tests/test_check_engine_source_test_citation.py` | 11 | 0.00 | 37 | 51 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_check_engine_spec_criteria.py` | 15 | 0.00 | 2 | 4 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_check_engine_status_meta.py` | 5 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_check_engine_test_citation.py` | 5 | 0.00 | 14 | 20 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_check_finding_path_relativity.py` | 4 | 0.00 | 8 | 10 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_check_findings_grouping.py` | 7 | 0.41 | 3 | 5 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_check_recovery_fidelity.py` | 3 | 0.00 | 0 | 0 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_check_scope_drift.py` | 6 | 0.00 | 7 | 11 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_check_severity_tally.py` | 4 | 0.00 | 0 | 1 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_checkup.py` | 16 | 0.00 | 137 | 183 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_clean_base_tracked_scope.py` | 2 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_clean_base_untracked.py` | 3 | 0.00 | 21 | 31 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_clean_target_config_home.py` | 23 | 0.00 | 103 | 158 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_clean_target_control_state.py` | 9 | 0.00 | 43 | 53 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_clean_target_recognition.py` | 7 | 0.00 | 6 | 10 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_clean_target_zero_delta_e2e.py` | 2 | 0.00 | 12 | 19 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_cli.py` | 64 | 0.00 | 308 | 429 | `consolidate` | 13 tests with identical coverage peers | `83nnyn` |
| `tests/test_cli_agent_protocol_doc.py` | 3 | 0.00 | 0 | 0 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_cli_checkout_reexec.py` | 15 | 20.24 | 10 | 16 | `read-required` | 5 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_cli_dest_shadow_refusal.py` | 8 | 0.00 | 22 | 34 | `consolidate` | 5 tests with identical coverage peers | `83nnyn` |
| `tests/test_cli_dest_shadowing.py` | 3 | 0.00 | 2 | 4 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_cli_find.py` | 12 | 0.00 | 47 | 59 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_cli_parser_conflict_policy.py` | 18 | 0.00 | 0 | 0 | `consolidate` | 18 tests with identical coverage peers | `83nnyn` |
| `tests/test_cli_quality_gates.py` | 15 | 0.00 | 16 | 23 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_cli_search.py` | 16 | 0.00 | 93 | 136 | `consolidate` | protected family/livecorpus/core; 5 candidate consolidate tests | `83nnyn` |
| `tests/test_cli_show.py` | 6 | 0.00 | 33 | 42 | `delete-candidate` | all 6 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_collision_population_parity.py` | 1 | 0.00 | 1 | 3 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_command_surface_declarations.py` | 2 | 0.00 | 0 | 0 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_commit_default_message.py` | 7 | 0.00 | 18 | 27 | `consolidate` | protected family/livecorpus/core; 1 candidate consolidate tests | `83nnyn` |
| `tests/test_commit_isolated_directory.py` | 3 | 0.00 | 8 | 14 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_commit_isolated_raced.py` | 6 | 0.00 | 20 | 26 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_commit_lock.py` | 7 | 0.00 | 3 | 5 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_commit_run_trailers_env.py` | 8 | 4.85 | 11 | 21 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_commit_scope_reason.py` | 12 | 0.00 | 14 | 22 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_comms_acks.py` | 20 | 1.57 | 170 | 224 | `consolidate` | 6 tests with identical coverage peers | `83nnyn` |
| `tests/test_comms_broker.py` | 19 | 1.78 | 76 | 99 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_comms_broker_registry.py` | 21 | 0.00 | 140 | 181 | `consolidate` | 6 tests with identical coverage peers | `83nnyn` |
| `tests/test_completion.py` | 31 | 0.00 | 433 | 591 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_completion_stale_notice.py` | 17 | 0.00 | 34 | 49 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_concurrent_driver_guard.py` | 31 | 0.00 | 113 | 164 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_config.py` | 37 | 0.00 | 220 | 355 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_config_agent_surface.py` | 27 | 63.04 | 193 | 239 | `speed-up` | 9 tests > 2s | `c8bfp9` |
| `tests/test_config_release_gate_kinds.py` | 9 | 0.00 | 18 | 30 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_conformance_matrix_structure.py` | 8 | 0.00 | 0 | 0 | `consolidate` | protected family/livecorpus/core; 5 candidate consolidate tests | `83nnyn` |
| `tests/test_contention_wait.py` | 12 | 0.00 | 32 | 52 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_core_module_coverage.py` | 25 | 1.18 | 1367 | 1839 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_core_smoke.py` | 6 | 11.00 | 4 | 6 | `speed-up` | protected family/livecorpus/core; 1 tests > 2s | `c8bfp9` |
| `tests/test_core_tier_selection.py` | 8 | 15.95 | 0 | 0 | `speed-up` | protected family/livecorpus/core; 2 tests > 2s | `c8bfp9` |
| `tests/test_coverage_not_written.py` | 8 | 0.00 | 27 | 41 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_coverage_record.py` | 7 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_cross_tree_session_refusal.py` | 3 | 0.00 | 29 | 36 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_date_reader_clock_parity.py` | 8 | 0.00 | 0 | 0 | `consolidate` | 8 tests with identical coverage peers | `83nnyn` |
| `tests/test_dead_status_token_scan.py` | 10 | 0.00 | 0 | 0 | `read-required` | 10 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_decision_ref_resolution.py` | 11 | 0.00 | 44 | 57 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_deep_cleanup_regenerable.py` | 5 | 0.00 | 0 | 1 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_defect_report.py` | 23 | 0.00 | 114 | 165 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_deferral_passthrough_reachability.py` | 3 | 0.00 | 1 | 2 | `delete-candidate` | all 3 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_deferred_reattempt_revalidation.py` | 2 | 0.00 | 16 | 26 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_deleted_test_replay.py` | 10 | 0.00 | 0 | 0 | `read-required` | 10 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_dependency_block_reporting.py` | 21 | 0.37 | 24 | 31 | `read-required` | 12 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_descriptive_length_classes.py` | 6 | 0.00 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_descriptive_refusal_hoist.py` | 997 | 2.41 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_deselect_notice.py` | 9 | 0.00 | 0 | 0 | `read-required` | 5 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_docs_check.py` | 15 | 0.00 | 23 | 37 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_docs_render.py` | 9 | 0.00 | 59 | 81 | `consolidate` | 5 tests with identical coverage peers | `83nnyn` |
| `tests/test_docs_test_citations.py` | 1 | 0.02 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_doctor.py` | 38 | 0.00 | 116 | 169 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_doctor_diagnostic_severity.py` | 3 | 0.00 | 5 | 7 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_drift_detail_escaping.py` | 18 | 0.00 | 31 | 46 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_drift_rule_registration.py` | 5 | 0.00 | 0 | 0 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_driver_begin_child_env.py` | 11 | 0.11 | 1 | 2 | `consolidate` | 8 tests with identical coverage peers | `83nnyn` |
| `tests/test_driver_prompt_ascii.py` | 3 | 0.00 | 2 | 4 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_driver_restart.py` | 16 | 0.00 | 104 | 124 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_durable_carrier_shared_predicate.py` | 2 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_egress_policy.py` | 37 | 0.00 | 307 | 392 | `read-required` | 37 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_empty_result_convention_doc.py` | 5 | 0.00 | 0 | 0 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_executed_transition_gate.py` | 12 | 0.00 | 3 | 7 | `consolidate` | protected family/livecorpus/core; 5 candidate consolidate tests | `83nnyn` |
| `tests/test_executed_transition_gate_e2e.py` | 7 | 0.00 | 0 | 0 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_exit_contract_conformance.py` | 28 | 444.53 | 12 | 16 | `speed-up` | protected family/livecorpus/core; 14 tests > 2s | `c8bfp9` |
| `tests/test_exit_vocabulary_boundary.py` | 3 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_explicit_dir_non_project.py` | 13 | 0.00 | 18 | 24 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_explicit_dir_subdir_resolution.py` | 7 | 0.00 | 2 | 4 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_failed_safely_live_writers.py` | 8 | 0.00 | 11 | 13 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_family_root_agent_conformance.py` | 27 | 30.05 | 48 | 76 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_fields_flag_reach.py` | 5 | 0.00 | 0 | 0 | `consolidate` | protected family/livecorpus/core; 2 candidate consolidate tests | `83nnyn` |
| `tests/test_finalize_disregarded_record.py` | 7 | 0.00 | 2 | 3 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_finalize_empty_declared_scope.py` | 6 | 0.00 | 2 | 3 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_finalize_refusal_findings.py` | 4 | 0.00 | 12 | 18 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_finalize_sendback.py` | 62 | 0.00 | 78 | 114 | `read-required` | 7 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_finalize_stale_plan_path.py` | 7 | 0.00 | 47 | 63 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_finalize_trailer_attribution.py` | 6 | 0.00 | 12 | 16 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_find_agent_stream.py` | 14 | 0.00 | 28 | 41 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_find_filters.py` | 18 | 0.00 | 58 | 94 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_find_human_limit.py` | 10 | 0.00 | 28 | 42 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_find_prompts_lane_status.py` | 8 | 0.18 | 1 | 2 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_find_single_read.py` | 6 | 0.25 | 2 | 7 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_finidem_reusable_not_finalized.py` | 3 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_fix_it_global_caps.py` | 27 | 0.00 | 151 | 199 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_fix_it_notice.py` | 15 | 0.00 | 20 | 32 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_fixfirst_end_to_end.py` | 35 | 0.00 | 57 | 90 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_flag_surface_uniformity.py` | 9 | 0.00 | 10 | 16 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_foreign_merge_refusal.py` | 5 | 0.00 | 14 | 19 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_forkresid_shared_shells.py` | 6 | 0.00 | 76 | 99 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_freeze_time_refusal.py` | 16 | 0.00 | 75 | 110 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_fresh_target_install_regression.py` | 12 | 16.98 | 0 | 0 | `read-required` | 11 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_from_backlog_cardinality.py` | 7 | 0.00 | 5 | 8 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_front_matter_loose_whitespace.py` | 4 | 0.00 | 4 | 7 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_gate_answer_baseline_indifference.py` | 3 | 0.00 | 10 | 17 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_gate_answer_record_released.py` | 9 | 0.00 | 19 | 31 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_gate_drop_audit.py` | 10 | 0.00 | 0 | 0 | `consolidate` | 6 tests with identical coverage peers | `83nnyn` |
| `tests/test_gate_pair_validation_parity.py` | 12 | 0.00 | 0 | 2 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_gate_ref_resolution.py` | 15 | 0.00 | 71 | 99 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_gate_summary_refusal_vocabulary.py` | 16 | 0.00 | 1 | 2 | `consolidate` | 15 tests with identical coverage peers | `83nnyn` |
| `tests/test_generic_color_depth.py` | 11 | 0.00 | 104 | 163 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_git_commit_helper.py` | 30 | 6.75 | 92 | 139 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_git_config_guard.py` | 6 | 9.90 | 0 | 0 | `read-required` | 6 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_gradcover_end_to_end.py` | 5 | 0.00 | 85 | 113 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_graduated_closable_warning.py` | 9 | 0.00 | 29 | 41 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_graduation_forward_links.py` | 9 | 0.00 | 49 | 82 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_group_verb_policy.py` | 73 | 0.00 | 49 | 68 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_handoff_ready_gate.py` | 16 | 0.00 | 64 | 101 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_hang_guard_budget.py` | 9 | 21.25 | 0 | 0 | `read-required` | 9 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_help_nontty_claim.py` | 1 | 0.00 | 0 | 0 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_history_block_bounding.py` | 9 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_history_consumers_shared_reader.py` | 5 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_history_date_clock.py` | 5 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_history_date_clock_parity.py` | 6 | 0.00 | 0 | 0 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_history_date_clock_readers.py` | 3 | 0.00 | 2 | 3 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_history_date_clock_residual.py` | 4 | 5.14 | 1 | 4 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_history_date_clock_sidecar.py` | 4 | 0.00 | 0 | 1 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_history_label_parity.py` | 5 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_history_order.py` | 7 | 0.00 | 29 | 44 | `read-required` | 5 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_history_provenance.py` | 7 | 0.00 | 6 | 9 | `delete-candidate` | all 7 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_history_write_order.py` | 8 | 0.00 | 0 | 5 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_home_isolation.py` | 4 | 0.00 | 1 | 2 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_home_path_pattern_source.py` | 8 | 1.02 | 0 | 0 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_hook_and_suite_fix_it.py` | 10 | 0.00 | 11 | 21 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_host_capability_extension.py` | 48 | 0.00 | 48 | 67 | `read-required` | 7 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_host_capability_registry.py` | 30 | 0.00 | 442 | 562 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_host_capability_wiring.py` | 3 | 1.18 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_host_runner_output_bound.py` | 11 | 0.00 | 16 | 20 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_host_runner_redaction.py` | 4 | 0.00 | 53 | 66 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_host_sandbox_profile.py` | 47 | 0.00 | 161 | 227 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_hostcapgate_descriptor_freeze.py` | 4 | 0.00 | 4 | 6 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_hostcapgate_execute_requirement.py` | 10 | 0.00 | 0 | 0 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_hostdedup_third_host.py` | 16 | 0.00 | 5 | 11 | `read-required` | 5 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_human_renderer_agent_hint.py` | 3 | 0.01 | 0 | 1 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_id6_global_mint.py` | 2 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_identity_rename_hint.py` | 4 | 0.00 | 27 | 36 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_implementing_spec_replan.py` | 7 | 0.00 | 45 | 56 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_index_check_agent_records.py` | 16 | 0.00 | 23 | 31 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_index_write_agent_records.py` | 19 | 0.00 | 78 | 121 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_inlane_retirement_lands.py` | 10 | 0.00 | 5 | 11 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_install_consent_truth.py` | 6 | 0.00 | 6 | 10 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_install_inbox_lane.py` | 4 | 16.42 | 0 | 0 | `speed-up` | 4 tests > 2s | `c8bfp9` |
| `tests/test_install_report_truth.py` | 3 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_install_source_option.py` | 4 | 4.03 | 0 | 0 | `speed-up` | 1 tests > 2s | `c8bfp9` |
| `tests/test_install_state_records.py` | 3 | 0.00 | 33 | 45 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_installed_text_current.py` | 5 | 0.00 | 33 | 38 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_installed_version_reporting.py` | 9 | 0.00 | 89 | 108 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_installer.py` | 149 | 0.00 | 570 | 790 | `read-required` | 7 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_installer_scaffold_preview_parity.py` | 8 | 0.00 | 6 | 12 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_interactivity_resolver.py` | 19 | 0.00 | 9 | 15 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_interrupt_attempt_metadata.py` | 14 | 0.00 | 17 | 26 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_interrupt_reconcile.py` | 15 | 0.00 | 87 | 103 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_ipd_authoring.py` | 31 | 0.00 | 143 | 190 | `consolidate` | 5 tests with identical coverage peers | `83nnyn` |
| `tests/test_ipd_exec_finding_codes.py` | 4 | 0.00 | 31 | 45 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_ipd_lifecycle_backward_edges.py` | 5 | 0.00 | 3 | 5 | `consolidate` | protected family/livecorpus/core; 2 candidate consolidate tests | `83nnyn` |
| `tests/test_ipd_lifecycle_cli.py` | 73 | 0.00 | 220 | 312 | `consolidate` | protected family/livecorpus/core; 11 candidate consolidate tests | `83nnyn` |
| `tests/test_ipd_lint.py` | 76 | 0.00 | 199 | 308 | `consolidate` | protected family/livecorpus/core; 5 candidate consolidate tests | `83nnyn` |
| `tests/test_ipd_schema.py` | 27 | 0.00 | 60 | 111 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_ipd_set_plan.py` | 34 | 0.00 | 363 | 495 | `consolidate` | 12 tests with identical coverage peers | `83nnyn` |
| `tests/test_ipd_templates.py` | 10 | 0.00 | 0 | 0 | `read-required` | 6 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_ipdrunner_runagy_shim.py` | 25 | 0.00 | 71 | 103 | `read-required` | 8 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_isolation_per_action.py` | 23 | 0.00 | 29 | 45 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_json_and_exitcodes.py` | 5 | 0.00 | 12 | 14 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_json_surface_leak_posture.py` | 20 | 0.00 | 1 | 2 | `consolidate` | protected family/livecorpus/core; 11 candidate consolidate tests | `83nnyn` |
| `tests/test_lane_import_root.py` | 5 | 0.00 | 0 | 0 | `read-required` | 4 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_lane_input_manifest.py` | 17 | 0.00 | 99 | 134 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_lane_input_revision_scope.py` | 4 | 0.00 | 9 | 13 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_lane_landing_anchor.py` | 5 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_lane_missing_input_token.py` | 4 | 0.01 | 4 | 6 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_lane_owner_record_anchoring.py` | 4 | 0.00 | 12 | 20 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_lane_reaper_callshape.py` | 3 | 0.11 | 0 | 1 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_lane_reclaim_decision_order.py` | 7 | 0.00 | 48 | 55 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_lane_retention_amended_r55.py` | 4 | 0.44 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_lane_rule_break_detection.py` | 10 | 0.00 | 27 | 36 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_lane_submission_retention_narrowing.py` | 12 | 3.73 | 18 | 28 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_lanes_prune.py` | 10 | 5.10 | 219 | 299 | `speed-up` | 1 tests > 2s | `c8bfp9` |
| `tests/test_layout.py` | 41 | 0.00 | 17 | 32 | `consolidate` | 25 tests with identical coverage peers | `83nnyn` |
| `tests/test_layout_inventory.py` | 6 | 0.00 | 19 | 27 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_leak_sanitizer.py` | 17 | 0.00 | 64 | 95 | `consolidate` | protected family/livecorpus/core; 1 candidate consolidate tests | `83nnyn` |
| `tests/test_leak_sanitizer_machine_flags.py` | 4 | 0.00 | 89 | 120 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_lifecycle_dirs.py` | 9 | 0.00 | 0 | 0 | `read-required` | 4 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_lifecycle_gate_coverage.py` | 6 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_lifecycle_holder_gate.py` | 14 | 0.00 | 72 | 97 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_lifecycle_lane_nudge.py` | 13 | 0.00 | 20 | 28 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_lifecycle_legend_help_reach.py` | 4 | 0.00 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_lifecycle_style.py` | 16 | 0.00 | 51 | 88 | `read-required` | 4 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_liftaudit_stop_halts_run.py` | 11 | 0.00 | 30 | 42 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_limit_reach_check_search.py` | 15 | 0.00 | 63 | 79 | `consolidate` | 5 tests with identical coverage peers | `83nnyn` |
| `tests/test_live_conformance_sweep.py` | 92 | 0.00 | 10 | 16 | `consolidate` | protected family/livecorpus/core; 52 candidate consolidate tests | `83nnyn` |
| `tests/test_livecorpus_notice.py` | 3 | 1.23 | 0 | 0 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_loaded_code.py` | 12 | 0.00 | 0 | 1 | `consolidate` | 7 tests with identical coverage peers | `83nnyn` |
| `tests/test_local_leaks.py` | 9 | 0.00 | 53 | 75 | `consolidate` | protected family/livecorpus/core; 1 candidate consolidate tests | `83nnyn` |
| `tests/test_lost_guard_census.py` | 7 | 0.00 | 0 | 0 | `read-required` | 7 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_manifest.py` | 11 | 0.00 | 3 | 6 | `consolidate` | protected family/livecorpus/core; 2 candidate consolidate tests | `83nnyn` |
| `tests/test_manifest_entry_selectable.py` | 2 | 0.00 | 5 | 8 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_merge_conflict_sendback.py` | 11 | 0.00 | 199 | 248 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_merge_gate_spec_anchors.py` | 7 | 0.00 | 198 | 247 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_migrate_layout_cli.py` | 9 | 0.00 | 73 | 86 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_model_vocab.py` | 11 | 0.00 | 49 | 69 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_mutation_probe.py` | 22 | 0.00 | 0 | 0 | `read-required` | 22 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_mutation_result_facts.py` | 8 | 6.63 | 27 | 40 | `speed-up` | 1 tests > 2s | `c8bfp9` |
| `tests/test_no_project_exit_is_cannot_run.py` | 13 | 27.87 | 0 | 0 | `speed-up` | 7 tests > 2s | `c8bfp9` |
| `tests/test_non_isolated_permission_posture.py` | 6 | 0.00 | 43 | 67 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_nonsurveyable_root_refusal.py` | 15 | 0.01 | 5 | 10 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_nv_backend_args_climb.py` | 4 | 0.00 | 3 | 7 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_oc_models.py` | 28 | 0.00 | 229 | 318 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_oc_profile_cli_regression.py` | 5 | 0.00 | 40 | 51 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_oc_runipd.py` | 182 | 0.00 | 285 | 413 | `read-required` | 23 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_oc_runipd_main_interrupt.py` | 3 | 0.00 | 3 | 6 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_options_anywhere.py` | 20 | 0.00 | 2 | 3 | `consolidate` | 16 tests with identical coverage peers | `83nnyn` |
| `tests/test_orchestrate_isolation.py` | 33 | 0.00 | 290 | 385 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_orchestrator_child_retired.py` | 8 | 0.00 | 98 | 122 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_orchestrator_kind_derivation.py` | 8 | 0.00 | 2 | 3 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_orchestrator_not_approved_reason.py` | 10 | 0.00 | 10 | 14 | `consolidate` | 8 tests with identical coverage peers | `83nnyn` |
| `tests/test_orchestrator_probe_payload.py` | 11 | 0.00 | 2 | 3 | `consolidate` | protected family/livecorpus/core; 7 candidate consolidate tests | `83nnyn` |
| `tests/test_orchestrator_probe_quotes.py` | 19 | 0.00 | 29 | 48 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_orchestrator_probe_scope.py` | 9 | 0.00 | 1 | 5 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_orchestrator_readiness.py` | 24 | 0.00 | 83 | 120 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_orchestrator_refusal_reason_translation.py` | 4 | 0.00 | 5 | 7 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_orchestrator_retire_closes_backlog.py` | 2 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_orchestrator_retirement.py` | 44 | 0.00 | 92 | 140 | `read-required` | 44 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_orchestrator_row_grammar_source.py` | 5 | 0.02 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_orchestrator_shape_composed.py` | 9 | 0.00 | 4 | 6 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_orchestrator_shape_gate.py` | 15 | 0.00 | 19 | 33 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_orchestrator_status_gate.py` | 13 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_outcome_word_ladder.py` | 7 | 0.00 | 10 | 18 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_outer_close_spec_carrier.py` | 6 | 0.00 | 8 | 14 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_packaging.py` | 2 | 0.00 | 0 | 0 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_packaging_distribution.py` | 9 | 0.00 | 0 | 0 | `read-required` | 9 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_pad_visible.py` | 7 | 0.00 | 4 | 7 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_partition.py` | 26 | 7.87 | 109 | 193 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_partition_set_cohesion.py` | 17 | 7.25 | 232 | 351 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_placement_switch_cli.py` | 9 | 0.00 | 147 | 207 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_placement_switch_companion_plan.py` | 21 | 0.00 | 107 | 161 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_placement_switch_execute.py` | 9 | 0.00 | 64 | 97 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_placement_switch_guard.py` | 5 | 0.00 | 37 | 46 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_placement_switch_plan.py` | 12 | 0.00 | 26 | 42 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_placement_switch_retire.py` | 7 | 0.00 | 29 | 52 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_plan_holder_predicate.py` | 14 | 0.00 | 41 | 55 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_plan_priority_required.py` | 27 | 0.00 | 42 | 62 | `consolidate` | 8 tests with identical coverage peers | `83nnyn` |
| `tests/test_plan_review_feasibility_rule.py` | 4 | 0.00 | 0 | 0 | `read-required` | 4 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_plan_status.py` | 10 | 0.00 | 0 | 0 | `consolidate` | protected family/livecorpus/core; 8 candidate consolidate tests | `83nnyn` |
| `tests/test_plan_transition_gate.py` | 10 | 0.00 | 25 | 33 | `consolidate` | protected family/livecorpus/core; 1 candidate consolidate tests | `83nnyn` |
| `tests/test_plans_archive.py` | 15 | 0.00 | 19 | 27 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_plans_archive_selectors.py` | 13 | 7.06 | 14 | 19 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_plans_board.py` | 10 | 0.00 | 27 | 47 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_plans_group_order_preservation.py` | 8 | 3.58 | 1 | 2 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_plans_index.py` | 18 | 0.00 | 3 | 8 | `consolidate` | protected family/livecorpus/core; 2 candidate consolidate tests | `83nnyn` |
| `tests/test_plans_order_grammar.py` | 12 | 17.98 | 30 | 42 | `speed-up` | 2 tests > 2s | `c8bfp9` |
| `tests/test_plans_rename_selectors.py` | 15 | 6.21 | 18 | 29 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_platform_lock.py` | 24 | 0.00 | 6 | 12 | `read-required` | 5 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_platform_lock_preserve.py` | 8 | 0.00 | 47 | 63 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_poll_rung_merge_awareness.py` | 4 | 0.00 | 21 | 28 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_precommit_scope_gate_severity.py` | 8 | 0.00 | 18 | 29 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_precommit_verbatim_exclusions.py` | 4 | 0.00 | 0 | 0 | `read-required` | 4 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_prior_attempt_projection.py` | 2 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_private_file.py` | 7 | 0.00 | 20 | 27 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_production_baseline_same_commit.py` | 4 | 0.00 | 8 | 18 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_production_checks_trace.py` | 29 | 0.00 | 23 | 37 | `consolidate` | 6 tests with identical coverage peers | `83nnyn` |
| `tests/test_production_correction_turn.py` | 9 | 0.00 | 312 | 368 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_production_resume_handoff.py` | 9 | 0.00 | 35 | 55 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_production_set_check.py` | 16 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_project_context.py` | 20 | 0.00 | 91 | 134 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_project_layout.py` | 13 | 0.00 | 99 | 133 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_project_registry.py` | 9 | 0.00 | 62 | 85 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_prompts_attention.py` | 5 | 0.00 | 0 | 0 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_prompts_index.py` | 15 | 0.00 | 44 | 71 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_prompts_new.py` | 22 | 0.00 | 95 | 118 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_prompts_set_surface.py` | 6 | 0.00 | 21 | 30 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_pwatch_signal_exit.py` | 4 | 6.59 | 8 | 12 | `speed-up` | 2 tests > 2s | `c8bfp9` |
| `tests/test_pwatch_tty_color.py` | 3 | 0.00 | 8 | 13 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_pypi_links.py` | 15 | 0.00 | 61 | 84 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_read_class_callers_refuse.py` | 12 | 50.32 | 42 | 57 | `read-required` | 5 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_read_verb_zero_match_refusal.py` | 11 | 0.00 | 121 | 167 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_readiness_absence_invariant.py` | 10 | 4.33 | 3 | 6 | `speed-up` | protected family/livecorpus/core; 1 tests > 2s | `c8bfp9` |
| `tests/test_reaskscore_composed.py` | 11 | 0.00 | 69 | 84 | `read-required` | 4 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_receipt_lane_record.py` | 6 | 0.00 | 10 | 19 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_receipt_liveness_suppressors.py` | 3 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_record_owner_root.py` | 12 | 99.47 | 62 | 85 | `speed-up` | 10 tests > 2s | `c8bfp9` |
| `tests/test_record_placement.py` | 8 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_record_producers.py` | 28 | 0.00 | 85 | 124 | `read-required` | 8 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_records_only_lane_rederive.py` | 39 | 1.66 | 201 | 307 | `read-required` | 6 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_records_root_accessor.py` | 19 | 17.02 | 8 | 12 | `speed-up` | 4 tests > 2s | `c8bfp9` |
| `tests/test_records_root_switch_guard.py` | 7 | 0.00 | 47 | 64 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_records_untracked_backend.py` | 10 | 0.00 | 69 | 101 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_recovone_single_definition.py` | 9 | 0.00 | 6 | 12 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_red_ci_stop.py` | 12 | 0.00 | 330 | 437 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_redaction_key_casefold.py` | 9 | 0.00 | 9 | 12 | `consolidate` | 6 tests with identical coverage peers | `83nnyn` |
| `tests/test_refusal_record_redaction.py` | 7 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_reinstall_preserves_config.py` | 16 | 0.00 | 24 | 39 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_release_gate_one_way_mismatch.py` | 2 | 0.00 | 0 | 0 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_release_readiness.py` | 35 | 11.87 | 9 | 17 | `speed-up` | 2 tests > 2s | `c8bfp9` |
| `tests/test_release_readiness_child_pin.py` | 2 | 2.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_release_readiness_docs_gate.py` | 7 | 1.46 | 6 | 10 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_release_readiness_not_applicable.py` | 13 | 8.73 | 0 | 0 | `speed-up` | 1 tests > 2s | `c8bfp9` |
| `tests/test_release_readiness_producers.py` | 26 | 1.40 | 36 | 65 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_release_sentinel_succession.py` | 9 | 0.00 | 5 | 8 | `read-required` | 4 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_releases.py` | 21 | 0.00 | 10 | 18 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_releases_cli.py` | 37 | 0.00 | 35 | 51 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_releases_line_writers.py` | 23 | 0.00 | 5 | 9 | `consolidate` | 13 tests with identical coverage peers | `83nnyn` |
| `tests/test_releases_readiness_cli.py` | 12 | 34.34 | 7 | 14 | `speed-up` | 9 tests > 2s | `c8bfp9` |
| `tests/test_releases_sibling_line_writers_bounding.py` | 9 | 0.00 | 12 | 25 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_rename_group_machine_output.py` | 14 | 32.59 | 51 | 91 | `speed-up` | 6 tests > 2s | `c8bfp9` |
| `tests/test_rename_receipt_guard.py` | 14 | 0.00 | 107 | 150 | `consolidate` | 5 tests with identical coverage peers | `83nnyn` |
| `tests/test_replay_coverage_diff.py` | 6 | 0.00 | 0 | 0 | `read-required` | 6 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_repo_relative_posix.py` | 21 | 0.00 | 25 | 38 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_rereview_reviewed_plan.py` | 10 | 0.00 | 116 | 168 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_research_archive.py` | 26 | 0.00 | 92 | 132 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_research_cmd_create.py` | 20 | 0.00 | 26 | 41 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_research_companion.py` | 10 | 0.00 | 126 | 170 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_research_date_containment.py` | 23 | 0.00 | 36 | 49 | `consolidate` | 6 tests with identical coverage peers | `83nnyn` |
| `tests/test_research_descriptive_safety.py` | 24 | 0.00 | 37 | 52 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_research_first_order.py` | 10 | 0.00 | 14 | 18 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_research_index.py` | 52 | 0.00 | 40 | 72 | `consolidate` | protected family/livecorpus/core; 9 candidate consolidate tests | `83nnyn` |
| `tests/test_research_index_name_fm_mismatch.py` | 7 | 0.00 | 15 | 24 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_research_rename_frontmatter.py` | 14 | 5.73 | 9 | 14 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_research_set_assign_date_containment.py` | 21 | 0.00 | 27 | 41 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_research_unsafe_field.py` | 11 | 0.00 | 0 | 0 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_resolve_plan_path_typed.py` | 13 | 0.00 | 10 | 18 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_resolver_bypass_sites_climb.py` | 15 | 0.00 | 49 | 65 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_retry_budget_citation.py` | 1 | 0.01 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_retry_class_mapping.py` | 3 | 0.01 | 0 | 0 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_review_failure_reason.py` | 21 | 0.00 | 59 | 82 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_review_lane_output_commit.py` | 7 | 0.41 | 10 | 16 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_review_record_classifier.py` | 13 | 0.00 | 160 | 217 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_review_staleness_advisory.py` | 12 | 0.00 | 61 | 86 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_reviews_type_noun_surface.py` | 8 | 1.36 | 12 | 17 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_root_run_scratch_migration.py` | 17 | 0.00 | 109 | 145 | `consolidate` | 9 tests with identical coverage peers | `83nnyn` |
| `tests/test_run_analytics.py` | 32 | 0.00 | 249 | 394 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_run_analytics_cli.py` | 11 | 0.00 | 193 | 269 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_run_analytics_privacy_docs.py` | 7 | 0.00 | 0 | 0 | `read-required` | 7 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_run_analytics_statistics.py` | 25 | 0.00 | 523 | 716 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_run_cli_corruption_exit.py` | 8 | 18.54 | 19 | 23 | `speed-up` | 4 tests > 2s | `c8bfp9` |
| `tests/test_run_cli_declarations.py` | 6 | 30.36 | 12 | 22 | `speed-up` | 3 tests > 2s | `c8bfp9` |
| `tests/test_run_cli_error_payload_keys.py` | 4 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_run_cli_human_redaction.py` | 15 | 31.86 | 0 | 0 | `speed-up` | 7 tests > 2s | `c8bfp9` |
| `tests/test_run_dashboard.py` | 23 | 0.00 | 95 | 144 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_run_dir_outcomes_parent_is_guaranteed.py` | 6 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_run_dir_parents_are_guaranteed.py` | 5 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_run_evidence_completion.py` | 84 | 0.00 | 268 | 387 | `read-required` | 11 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_run_exit_aggregate.py` | 11 | 0.00 | 6 | 9 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_run_finding_abort_partition.py` | 9 | 0.00 | 7 | 12 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_run_finding_reachability.py` | 5 | 0.00 | 17 | 28 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_run_finding_spec_transcription.py` | 3 | 0.00 | 0 | 0 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_run_freeze.py` | 12 | 0.04 | 58 | 87 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_run_id_collision.py` | 7 | 0.00 | 4 | 6 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_run_init.py` | 14 | 74.27 | 26 | 46 | `speed-up` | 12 tests > 2s | `c8bfp9` |
| `tests/test_run_progress_count.py` | 2 | 0.00 | 0 | 0 | `delete-candidate` | all 2 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_run_proposal_channel.py` | 25 | 102.48 | 140 | 195 | `speed-up` | 15 tests > 2s | `c8bfp9` |
| `tests/test_run_recovery_cli.py` | 54 | 0.00 | 295 | 432 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_run_scratch_path_guard.py` | 14 | 0.00 | 0 | 0 | `read-required` | 14 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_run_selection_policy.py` | 62 | 0.00 | 132 | 188 | `consolidate` | protected family/livecorpus/core; 4 candidate consolidate tests | `83nnyn` |
| `tests/test_run_summary_lifecycle_glyph.py` | 6 | 0.15 | 0 | 0 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_run_summary_malformed_entry.py` | 4 | 0.00 | 1 | 2 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_run_summary_table.py` | 9 | 0.00 | 60 | 90 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_run_summary_visible_width.py` | 7 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_run_viewer.py` | 64 | 0.00 | 760 | 1076 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_runfresh_end_to_end.py` | 6 | 0.00 | 0 | 0 | `read-required` | 6 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_runner_active_conflict.py` | 21 | 0.00 | 84 | 121 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_runner_backlog_close_behavior.py` | 48 | 0.00 | 121 | 169 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_runner_bare_verb_shim.py` | 4 | 0.00 | 107 | 138 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_runner_delegation_and_host_independence.py` | 23 | 0.00 | 2 | 4 | `read-required` | 13 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_runner_fallback_bindings.py` | 6 | 13.00 | 53 | 85 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_runner_finalize_message.py` | 7 | 0.02 | 0 | 0 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_runner_findings_dependency_gate.py` | 7 | 0.17 | 2 | 7 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_runner_fork_scan_constants.py` | 5 | 0.04 | 0 | 0 | `read-required` | 5 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_runner_peer_dependency.py` | 10 | 0.00 | 189 | 248 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_runner_profile_wizard_discovery.py` | 7 | 0.00 | 13 | 22 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_runner_profiles.py` | 63 | 0.00 | 147 | 290 | `read-required` | 7 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_runner_safety_probe_memo.py` | 5 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_runner_shared.py` | 136 | 0.00 | 395 | 563 | `consolidate` | protected family/livecorpus/core; 27 candidate consolidate tests | `83nnyn` |
| `tests/test_runner_stop_interactive.py` | 6 | 0.00 | 78 | 99 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_runner_stop_triggers_e2e.py` | 2 | 0.00 | 0 | 0 | `delete-candidate` | all 2 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_runners_monitor.py` | 18 | 4.70 | 194 | 267 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_runs_empty_agent_record.py` | 7 | 1.47 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_runs_flag_position_parity.py` | 4 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_runs_machine_output_paths.py` | 16 | 36.09 | 24 | 34 | `speed-up` | 13 tests > 2s | `c8bfp9` |
| `tests/test_runs_repo_alias.py` | 24 | 4.56 | 0 | 0 | `consolidate` | 22 tests with identical coverage peers | `83nnyn` |
| `tests/test_runs_subdir_root.py` | 8 | 0.00 | 15 | 21 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_runwire_state_translation.py` | 13 | 1.17 | 6 | 9 | `consolidate` | 5 tests with identical coverage peers | `83nnyn` |
| `tests/test_runwire_verifier_authority.py` | 15 | 0.00 | 29 | 37 | `read-required` | 4 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_sanitizer_severity_vocabulary.py` | 3 | 0.00 | 16 | 25 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_scaffold_history_clock.py` | 8 | 0.00 | 0 | 0 | `consolidate` | 8 tests with identical coverage peers | `83nnyn` |
| `tests/test_scan_root_classification.py` | 4 | 0.00 | 0 | 0 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_scope_drift_lane_resolution.py` | 6 | 0.00 | 27 | 44 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_scope_exceeded.py` | 7 | 0.00 | 40 | 59 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_scope_match.py` | 6 | 0.00 | 0 | 3 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_scope_path_target_stale.py` | 25 | 0.00 | 27 | 41 | `consolidate` | 6 tests with identical coverage peers | `83nnyn` |
| `tests/test_scope_paths_status_agnostic.py` | 6 | 0.00 | 2 | 4 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_scope_reconcile_sendback_real_text.py` | 6 | 0.00 | 2 | 4 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_section_consent.py` | 12 | 0.00 | 17 | 25 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_security_hardening.py` | 11 | 0.00 | 144 | 207 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_selector_echo_sanitization.py` | 20 | 0.00 | 2 | 5 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_selector_precedence_outcomes.py` | 3 | 0.00 | 0 | 0 | `delete-candidate` | all 3 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_selector_two_dialect_readers.py` | 11 | 0.00 | 1 | 2 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_selector_type_containment.py` | 10 | 10.35 | 0 | 0 | `speed-up` | 2 tests > 2s | `c8bfp9` |
| `tests/test_set_dispatch_dedup.py` | 10 | 0.00 | 0 | 1 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_set_dispatch_parity.py` | 40 | 0.00 | 11 | 19 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_set_refuses_review_record.py` | 5 | 2.00 | 6 | 10 | `delete-candidate` | all 5 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_severity_tier_contract.py` | 9 | 0.00 | 0 | 0 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_severity_truth_surfaces.py` | 2 | 7.95 | 0 | 0 | `speed-up` | 2 tests > 2s | `c8bfp9` |
| `tests/test_shared_flag_honored.py` | 259 | 543.58 | 114 | 173 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_silent_turn_observability.py` | 12 | 0.00 | 19 | 30 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_slug_slice_trailing_hyphen.py` | 2 | 0.00 | 35 | 36 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_source_citation_scan.py` | 3 | 1.18 | 128 | 165 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_source_offsets.py` | 12 | 2.05 | 204 | 276 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_spec_citation_anchors.py` | 15 | 10.71 | 93 | 130 | `speed-up` | 1 tests > 2s | `c8bfp9` |
| `tests/test_spec_edit_ack_gate.py` | 8 | 0.00 | 109 | 143 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_spec_id6_filenames.py` | 21 | 0.00 | 97 | 129 | `consolidate` | protected family/livecorpus/core; 6 candidate consolidate tests | `83nnyn` |
| `tests/test_spec_path_citations.py` | 1 | 0.07 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_spec_production.py` | 23 | 0.00 | 17 | 30 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_spec_review_attestation.py` | 29 | 0.00 | 57 | 91 | `read-required` | 10 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_spec_review_dispatch.py` | 7 | 0.00 | 47 | 69 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_specs_date_containment.py` | 15 | 0.00 | 0 | 0 | `consolidate` | 5 tests with identical coverage peers | `83nnyn` |
| `tests/test_specs_evidence_gate_parity.py` | 8 | 0.00 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_specs_from_backlog.py` | 8 | 0.00 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_specs_metadata_duplicate_bullet.py` | 7 | 0.00 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_specs_recursive_read.py` | 8 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_specs_releases_descriptive_safety.py` | 19 | 0.00 | 3 | 5 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_specs_releases_unsafe_field.py` | 14 | 0.00 | 0 | 0 | `consolidate` | 4 tests with identical coverage peers | `83nnyn` |
| `tests/test_specs_set_adapter.py` | 6 | 0.00 | 14 | 20 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_specs_set_gate_parity.py` | 8 | 0.00 | 0 | 0 | `delete-candidate` | all 8 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_specs_status_dirs.py` | 8 | 0.00 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_specs_verbs.py` | 20 | 0.00 | 87 | 113 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_staged_illegal_backlog_transition_gate.py` | 13 | 0.00 | 13 | 21 | `consolidate` | protected family/livecorpus/core; 5 candidate consolidate tests | `83nnyn` |
| `tests/test_stall_progress_agy.py` | 8 | 0.00 | 94 | 134 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_status_set.py` | 110 | 0.00 | 239 | 342 | `consolidate` | protected family/livecorpus/core; 11 candidate consolidate tests | `83nnyn` |
| `tests/test_status_set_descriptive_safety.py` | 15 | 0.00 | 30 | 38 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_status_set_metadata_region.py` | 3 | 0.12 | 0 | 0 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_status_set_partial_batch.py` | 16 | 0.00 | 105 | 143 | `consolidate` | 2 tests with identical coverage peers | `83nnyn` |
| `tests/test_statusline_ascii_mode.py` | 43 | 0.00 | 4 | 7 | `consolidate` | 39 tests with identical coverage peers | `83nnyn` |
| `tests/test_statusline_behavior.py` | 54 | 0.00 | 96 | 164 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_statusline_stop_tally.py` | 70 | 0.00 | 10 | 25 | `consolidate` | 41 tests with identical coverage peers | `83nnyn` |
| `tests/test_statusline_visible_width.py` | 35 | 0.98 | 1 | 2 | `consolidate` | 16 tests with identical coverage peers | `83nnyn` |
| `tests/test_stdin_interactive.py` | 5 | 0.06 | 16 | 20 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_stranded_run_exit_code.py` | 9 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_subparser_descriptions.py` | 3 | 0.00 | 0 | 0 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_subtest_row_verdicts.py` | 8 | 0.00 | 78 | 101 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_suite_baseline_direction.py` | 2 | 0.01 | 46 | 72 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_suite_baseline_mode_gate.py` | 3 | 0.00 | 0 | 3 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_suite_cache.py` | 10 | 187.71 | 178 | 246 | `speed-up` | 8 tests > 2s | `c8bfp9` |
| `tests/test_suite_exit_code_authority.py` | 6 | 0.00 | 29 | 43 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_suite_slot_lock.py` | 8 | 26.81 | 55 | 84 | `speed-up` | 5 tests > 2s | `c8bfp9` |
| `tests/test_support_section.py` | 11 | 0.00 | 0 | 1 | `read-required` | 9 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_suppress_narrowing.py` | 9 | 7.88 | 2 | 7 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_system_root_accessor.py` | 12 | 24.07 | 29 | 47 | `speed-up` | 2 tests > 2s | `c8bfp9` |
| `tests/test_tabulated_test_convention.py` | 2 | 0.00 | 0 | 0 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_telemetry_platform_release.py` | 2 | 0.00 | 0 | 1 | `delete-candidate` | all 2 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_term.py` | 32 | 0.00 | 46 | 77 | `read-required` | 32 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_terminal_status_vocabulary.py` | 16 | 0.00 | 3 | 6 | `read-required` | 8 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_testprune_tools.py` | 7 | 2.69 | 0 | 0 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_tool_identity_item_failure.py` | 5 | 2.14 | 10 | 13 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_turn_bounds.py` | 10 | 2.50 | 25 | 48 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_turn_fix_it.py` | 9 | 0.00 | 95 | 116 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_typecheck_gate.py` | 3 | 0.00 | 0 | 2 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_typed_queue_entries.py` | 22 | 0.00 | 234 | 344 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_unclosed_report_grouping.py` | 3 | 0.00 | 57 | 83 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_uncollected_test_modules.py` | 2 | 0.00 | 2657 | 3276 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_uninstall_layout_artifacts.py` | 5 | 0.00 | 0 | 0 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_unresolved_selector_near_match.py` | 3 | 1.46 | 10 | 17 | `delete-candidate` | all 3 tests are 0-unique delete candidates | `tv72xy` |
| `tests/test_usage_refusal_agent_record.py` | 253 | 91.68 | 46 | 74 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_v_item_demonstration_reachability.py` | 3 | 0.00 | 0 | 0 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_v_item_evidence_durability.py` | 3 | 0.00 | 0 | 0 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_validator_nonsurveyable_dir.py` | 13 | 0.00 | 15 | 20 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_verbose_flag_reach.py` | 4 | 0.00 | 0 | 0 | `consolidate` | protected family/livecorpus/core; 2 candidate consolidate tests | `83nnyn` |
| `tests/test_verification_sendback.py` | 14 | 0.00 | 8 | 11 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_verifier_corroboration.py` | 59 | 0.00 | 101 | 139 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_verifier_evidence.py` | 15 | 0.00 | 21 | 38 | `read-required` | 3 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_versioning.py` | 17 | 0.00 | 15 | 23 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_walkthrough_id6.py` | 4 | 0.00 | 70 | 80 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_work_commit_routes_through_shared_helper.py` | 5 | 0.00 | 3 | 4 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_work_gate_severity.py` | 14 | 0.00 | 12 | 21 | `consolidate` | 7 tests with identical coverage peers | `83nnyn` |
| `tests/test_workflow_artifacts_prune.py` | 24 | 0.00 | 193 | 268 | `consolidate` | 1 tests with identical coverage peers | `83nnyn` |
| `tests/test_workflow_schema_compiler.py` | 30 | 0.00 | 167 | 279 | `consolidate` | 7 tests with identical coverage peers | `83nnyn` |
| `tests/test_worktree_lease.py` | 1 | 0.00 | 1 | 2 | `keep` | provides unique coverage; keep | `keep` |
| `tests/test_worktree_lease_stdlib_only.py` | 2 | 0.00 | 0 | 0 | `read-required` | 2 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_write_report_malformed_entry.py` | 5 | 0.00 | 15 | 27 | `read-required` | 1 tests require reading (pinscan or no-coverage) | `tv72xy` |
| `tests/test_xdist_auto_workers.py` | 11 | 0.00 | 0 | 0 | `keep` | protected family/livecorpus/core; keep | `keep` |
| `tests/test_zero_dispatch_outcome.py` | 25 | 0.00 | 24 | 29 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |
| `tests/test_zero_dispatch_progress_denominator.py` | 6 | 0.00 | 0 | 0 | `consolidate` | 3 tests with identical coverage peers | `83nnyn` |


## Structure-Pin Classification Table (IPD tv72xy)

### Summary Counts
- Total pinscan candidate hits: 235
- Verdicts: true-pin: 92, false-positive: 143
- Categories: structure: 12, name-shape: 51, arch-freeze: 29, none: 143
- Actions: delete: 72, convert: 10, keep: 153

| File | Test | Line Pattern | Verdict | Category | Action | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| `tests/test_action_table_runner_parity.py` | `<module>` | `inspect_getsource` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a live source inspection |
| `tests/test_agents_block_target_neutral.py` | `AgentsBlockTargetNeutralTests::test_this_repo_agents_md_has_suite_in_repo_local_region_only` | `md_doc_prose` | `false-positive` | `none` | `keep` | Published markdown documentation / workflow body under test (P16 exception); kept / handed to 83nnyn |
| `tests/test_agy_run.py` | `AntigravityExecuteIpdCompatibilityTests::test_re_exports_and_interface_parity` | `hasattr_prod` | `true-pin` | `structure` | `convert` | Compat wrapper re-export pins; convert to behavioral --help CLI invocation (E-09) |
| `tests/test_agy_run.py` | `AntigravityExecuteIpdCompatibilityTests::test_re_exports_and_interface_parity` | `hasattr_prod` | `true-pin` | `structure` | `convert` | Compat wrapper re-export pins; convert to behavioral --help CLI invocation (E-09) |
| `tests/test_agy_run.py` | `AntigravityExecuteIpdCompatibilityTests::test_re_exports_and_interface_parity` | `hasattr_prod` | `true-pin` | `structure` | `convert` | Compat wrapper re-export pins; convert to behavioral --help CLI invocation (E-09) |
| `tests/test_agy_run.py` | `AntigravityExecuteIpdCompatibilityTests::test_re_exports_and_interface_parity` | `hasattr_prod` | `true-pin` | `structure` | `convert` | Compat wrapper re-export pins; convert to behavioral --help CLI invocation (E-09) |
| `tests/test_agy_run.py` | `AntigravityExecuteIpdCompatibilityTests::test_re_exports_and_interface_parity` | `hasattr_prod` | `true-pin` | `structure` | `convert` | Compat wrapper re-export pins; convert to behavioral --help CLI invocation (E-09) |
| `tests/test_agy_run.py` | `AntigravityExecuteIpdCompatibilityTests::test_re_exports_and_interface_parity` | `hasattr_prod` | `true-pin` | `structure` | `convert` | Compat wrapper re-export pins; convert to behavioral --help CLI invocation (E-09) |
| `tests/test_agy_runipd_cli.py` | `AgyFullAutoApprovalTests::test_predicate_is_the_shared_one_and_local_copies_are_gone` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Runner host identity and placement pin (E-02) |
| `tests/test_agy_runipd_cli.py` | `AgyDependencyPathsAreSharedTests::test_both_dependency_entry_points_are_the_shared_objects` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_agy_runipd_cli.py` | `AgyDependencyPathsAreSharedTests::test_both_dependency_entry_points_are_the_shared_objects` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_agy_runipd_cli.py` | `AgyVerdictMappingTests::test_this_host_binds_the_shared_mapping_and_holds_no_copy` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_agy_runipd_cli.py` | `AgyVerificationAbsenceTests::test_plan_path_resolution` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_artifact_core_git_mv_containment.py` | `TestArtifactCoreGitMvContainment::test_case_d_symlink_destination_pointing_outside_refused` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_attempt_agy_model_observation.py` | `TestAttemptAgyModelObservation::test_case_e_seam_contract_resolution_through_driver_module` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_attention.py` | `SharedLifecycleResolverTests::test_lifecycle_resolution_and_escapes` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed symbol _STATUS_COLOR_256 hasattr pin (E-03) |
| `tests/test_authoring_coverage_guidance.py` | `FreshInstallManagedBlockTests::test_fresh_install_writes_agents_md_with_precondition` | `md_doc_prose` | `false-positive` | `none` | `keep` | Published markdown documentation / workflow body under test (P16 exception); kept / handed to 83nnyn |
| `tests/test_aw_upgrade_test.py` | `ChildToolPinningTests::test_run_install_in_simulated_worktree_imports_from_worktree` | `sys_modules_check` | `false-positive` | `none` | `keep` | Harness module cache manipulation, mock blocker, or conftest loader |
| `tests/test_aw_upgrade_test.py` | `ChildToolPinningTests::test_probe_import_origin_in_simulated_worktree_reports_worktree` | `sys_modules_check` | `false-positive` | `none` | `keep` | Harness module cache manipulation, mock blocker, or conftest loader |
| `tests/test_backlog_descriptive_safety.py` | `BacklogDescriptiveSafetyTests::test_helper_refuse_unsafe_descriptive_contract` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_backlog_handoff_close.py` | `BacklogGateDirSplitTests::test_backlog_set_declared_flag_surface_matches_parser` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_backlog_handoff_close.py` | `BacklogGateDirSplitTests::test_backlog_set_declared_flag_surface_matches_parser` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_check_engine.py` | `CarrierEvidencePlanAndSpecDisposition::test_fall_through_live_carrier_accepted` | `hasattr_prod` | `true-pin` | `structure` | `delete` | Vacuous if hasattr guard around check_engine private helper (E-06) |
| `tests/test_check_engine_metadata_region.py` | `test_bounded_accessors_ignore_body_quotations` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | hasattr pins on _read_item_id etc.; behavior tested directly on following lines (E-03) |
| `tests/test_clean_target_recognition.py` | `TestCleanTargetRecognition::test_b2_identity_table` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_clean_target_recognition.py` | `TestCleanTargetRecognition::test_b2_identity_table` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_clean_target_recognition.py` | `TestCleanTargetRecognition::test_b2_identity_table` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_completion_stale_notice.py` | `NoticeStampTests::test_stamp_write_readonly_parent` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_completion_stale_notice.py` | `DocumentationAndDocstringTests::test_readme_tab_completion_section` | `md_doc_prose` | `false-positive` | `none` | `keep` | Published markdown documentation / workflow body under test (P16 exception); kept / handed to 83nnyn |
| `tests/test_completion_stale_notice.py` | `DocumentationAndDocstringTests::test_test_completion_docstring_updated` | `module_doc_assertion` | `true-pin` | `name-shape` | `delete` | Test module docstring pin (E-04) |
| `tests/test_concurrent_driver_guard.py` | `OperatorVerbTests::_run` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_concurrent_driver_guard.py` | `OperatorVerbTests::test_the_verb_and_the_driver_genuinely_CONTEND` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_core_tier_selection.py` | `pytest_runtest_logreport` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_dependency_block_reporting.py` | `test_write_report_dependency_blocks_section_for_canonical_and_legacy_statuses` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_dependency_block_reporting.py` | `test_orchestrator_item_surfaces_child_in_report_not_summary_table` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_dependency_block_reporting.py` | `test_write_report_renders_one_recovery_line_for_each_producer` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_dependency_block_reporting.py` | `test_drain_and_cascade_report_renders_correct_host_attribution` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_dependency_block_reporting.py` | `test_dependency_reason_rendering_all_producer_shapes` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_descriptive_refusal_hoist.py` | `test_public_hoisted_helper_exists` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_egress_policy.py` | `TestEgressPolicyUnit::test_policy_has_no_allow_all_or_negation_switch` | `hasattr_prod` | `true-pin` | `arch-freeze` | `convert` | Allow-all / negation hasattr pin; converted to TypeError on construction (E-07) |
| `tests/test_egress_policy.py` | `TestEgressPolicyUnit::test_policy_has_no_allow_all_or_negation_switch` | `hasattr_prod` | `true-pin` | `arch-freeze` | `convert` | Allow-all / negation hasattr pin; converted to TypeError on construction (E-07) |
| `tests/test_egress_policy.py` | `TestEgressPolicyUnit::test_policy_has_no_allow_all_or_negation_switch` | `hasattr_prod` | `true-pin` | `arch-freeze` | `convert` | Allow-all / negation hasattr pin; converted to TypeError on construction (E-07) |
| `tests/test_egress_policy.py` | `<module>` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_fix_it_global_caps.py` | `TestEndToEndGlobalCaps::fake_launcher` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_fix_it_global_caps.py` | `TestEndToEndGlobalCaps::fake_launcher` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_forkresid_shared_shells.py` | `LanePromptSuppressionTests::test_question_timeouts_are_180s` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_forkresid_shared_shells.py` | `LanePromptSuppressionTests::test_question_timeouts_are_180s` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_forkresid_shared_shells.py` | `LanePromptSuppressionTests::test_shared_and_declined_constants_guards` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Runner host identity and placement pin (E-02) |
| `tests/test_git_commit_helper.py` | `_FakeStdin::test_hook_rewrite_retry_and_peer_isolation` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_git_commit_helper.py` | `_FakeStdin::test_hook_rewrite_retry_and_peer_isolation` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_git_config_guard.py` | `_clean_git_env` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_git_config_guard.py` | `test_init_repo_failure_does_not_leak_to_enclosing_repo` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_graduation_forward_links.py` | `GraduationForwardLinksTests::test_case_2_reverse_only` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_graduation_forward_links.py` | `GraduationForwardLinksTests::test_case_6_no_source_at_all` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_hang_guard_budget.py` | `<module>` | `hasattr_prod` | `false-positive` | `none` | `keep` | hasattr on object or module attribute |
| `tests/test_history_date_clock_parity.py` | `scoped_timezone` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_history_date_clock_parity.py` | `scoped_timezone` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_history_date_clock_parity.py` | `HistoryDateClockParityTests::test_precondition_at_least_one_zone_in_skew_window` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_history_date_clock_residual.py` | `_check_and_select_skew` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_history_date_clock_sidecar.py` | `temporary_timezone` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_history_date_clock_sidecar.py` | `temporary_timezone` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_history_order.py` | `HistoryOrderFixtureTests::test_fixture_a_newest_first` | `hasattr_prod` | `true-pin` | `structure` | `delete` | Vacuous if hasattr guard around private helper; public drift check retained (E-06) |
| `tests/test_history_order.py` | `HistoryOrderFixtureTests::test_fixture_b_oldest_first` | `hasattr_prod` | `true-pin` | `structure` | `delete` | Vacuous if hasattr guard around private helper; public drift check retained (E-06) |
| `tests/test_history_order.py` | `HistoryOrderFixtureTests::test_fixture_c_mixed_blocks` | `hasattr_prod` | `true-pin` | `structure` | `delete` | Vacuous if hasattr guard around private helper; public drift check retained (E-06) |
| `tests/test_history_order.py` | `HistoryOrderFixtureTests::test_fixture_d_negative_cross_day_backwards` | `hasattr_prod` | `true-pin` | `structure` | `delete` | Vacuous if hasattr guard around private helper; public drift check retained (E-06) |
| `tests/test_history_order.py` | `HistoryOrderFixtureTests::test_fixture_e_discriminating_single_date_tie` | `hasattr_prod` | `true-pin` | `structure` | `delete` | Vacuous if hasattr guard around private helper; public drift check retained (E-06) |
| `tests/test_history_write_order.py` | `_skip_if_root` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_host_capability_extension.py` | `RunnerSafetyProbeTests::test_presence_vs_observation_table` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed/private symbol CAP_DENY_PUSH / _probe_egress_filtering hasattr pin (E-03) |
| `tests/test_host_capability_extension.py` | `DenyPushRemovedTests::test_supports_deny_push_and_unenforced_action_verdicts_removed` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed/private symbol CAP_DENY_PUSH / _probe_egress_filtering hasattr pin (E-03) |
| `tests/test_host_capability_wiring.py` | `test_execute_item_core_refuses_when_host_capability_unavailable_and_starts_no_session` | `hasattr_prod` | `false-positive` | `none` | `keep` | Version-compatibility conditional check in test helper |
| `tests/test_host_sandbox_profile.py` | `_Boom::test_module_publishes_its_guarantees` | `module_doc_assertion` | `true-pin` | `name-shape` | `delete` | Module docstring pin on hsp guarantees (E-04) |
| `tests/test_hostdedup_third_host.py` | `ThirdHostInitializationAndLimitTests::test_pin_measured_turn_execution_limits` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Turn execution limit freeze forbidding runner unification (E-07) |
| `tests/test_hostdedup_third_host.py` | `ThirdHostInitializationAndLimitTests::test_pin_measured_turn_execution_limits` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Turn execution limit freeze forbidding runner unification (E-07) |
| `tests/test_hostdedup_third_host.py` | `ThirdHostInitializationAndLimitTests::test_pin_measured_turn_execution_limits` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Turn execution limit freeze forbidding runner unification (E-07) |
| `tests/test_hostdedup_third_host.py` | `ThirdHostInitializationAndLimitTests::test_pin_measured_turn_execution_limits` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Turn execution limit freeze forbidding runner unification (E-07) |
| `tests/test_hostdedup_third_host.py` | `ThirdHostInitializationAndLimitTests::test_pin_measured_turn_execution_limits` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Turn execution limit freeze forbidding runner unification (E-07) |
| `tests/test_hostdedup_third_host.py` | `ThirdHostInitializationAndLimitTests::test_pin_measured_turn_execution_limits` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Turn execution limit freeze forbidding runner unification (E-07) |
| `tests/test_hostdedup_third_host.py` | `ThirdHostInitializationAndLimitTests::test_each_real_host_records_own_driver_identity_and_consumers_route` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_hostdedup_third_host.py` | `ThirdHostInitializationAndLimitTests::test_each_real_host_records_own_driver_identity_and_consumers_route` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_installer.py` | `drives::test_fresh_install` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `drives::test_fresh_install` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `drives::test_readme_templates_are_created_on_a_fresh_install` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `drives::test_readme_templates_are_created_on_a_fresh_install` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `UninstallApplyTests::test_changed_out_collects_paths_and_sections_preserved` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `AwBlockMigrationTests::test_legacy_block_conversion_and_sibling_preservation` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `AwBlockMigrationTests::test_legacy_block_conversion_and_sibling_preservation` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `AwBlockMigrationTests::test_reinstall_idempotence_and_declined_section` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `AwBlockMigrationTests::test_reinstall_idempotence_and_declined_section` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `AwBlockMigrationTests::test_reinstall_idempotence_and_declined_section` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `ResolvedIndexStampTests::_source_index` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `InstallLeftoverDefaultRemoveTests::test_safety_case_b_committed_leftover_with_uncommitted_edit_survives_remove` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_installer.py` | `InstallLeftoverDefaultRemoveTests::test_safety_case_b2_committed_leftover_with_staged_edit_survives_remove` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_ipd_lint.py` | `StructuralRuleTests::test_the_dash_rule_code_is_gone_rather_than_merely_silent` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed rule C_DASH hasattr pin; lint table proves rule never fires (E-03) |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_runagy_two_turn_execution_with_clean_verification` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_default_start_subcommand_inference` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_prepare_only_mode` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_explicit_run_id` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_runagy_no_verify_skips_turn2` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_verification_blocked_sets_status_fail_verify` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_stall_timeout_and_resume_recovery` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_stall_timeout_and_resume_recovery` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_runagy_status_and_report_commands` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_runagy_status_and_report_commands` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_runagy_status_and_report_commands` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_ipdrunner_runagy_shim.py` | `AgyExecutionLifecycleTests::test_runagy_status_and_report_commands` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_lane_owner_record_anchoring.py` | `LaneOwnerRecordAnchoringTests::test_absent_versus_unreachable_owner_store` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_leak_sanitizer.py` | `SelfCleanTests::test_engine_source_is_self_clean` | `read_prod_source` | `false-positive` | `none` | `keep` | Self-sanitizer test: source file is artifact under test (P16 exception) |
| `tests/test_leak_sanitizer.py` | `FixTests::test_fix_rewrites_reports_or_refrains_according_to_mode_and_leak_class` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_local_leaks.py` | `ThisRepoTests::test_module_source_is_self_clean` | `read_prod_source` | `false-positive` | `none` | `keep` | Self-sanitizer test: source file is artifact under test (P16 exception) |
| `tests/test_lost_guard_census.py` | `LostGuardCensusBehavioralTests::test_no_new_module_level_first_party_import_in_runner_shared` | `ast_parse_walk` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a production AST walk |
| `tests/test_lost_guard_census.py` | `LostGuardCensusBehavioralTests::test_no_new_module_level_first_party_import_in_runner_shared` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_lost_guard_census.py` | `LostGuardCensusBehavioralTests::test_no_new_module_level_first_party_import_in_runner_shared` | `ast_parse_walk` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a production AST walk |
| `tests/test_lost_guard_census.py` | `LostGuardCensusBehavioralTests::test_no_new_module_level_first_party_import_in_runner_shared` | `ast_parse_walk` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a production AST walk |
| `tests/test_lost_guard_census.py` | `LostGuardCensusSyntheticRepoTests::_setup_repo` | `ast_parse_walk` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a production AST walk |
| `tests/test_migrate_layout_cli.py` | `MigrateLayoutCliTests::test_interactive_wizard_decline_makes_no_mutations` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_migrate_layout_cli.py` | `MigrateLayoutCliTests::test_interactive_wizard_decline_makes_no_mutations` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_migrate_layout_cli.py` | `MigrateLayoutCliTests::test_interactive_wizard_decline_makes_no_mutations` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_oc_runipd.py` | `DummyProcess::kill` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_oc_runipd.py` | `AllSelectorAndFullAutoTests::test_is_plan_review_approved_is_the_shared_predicate_not_a_local_copy` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed helper extract_last_history_entry hasattr pin (E-02) |
| `tests/test_oc_runipd.py` | `AllSelectorAndFullAutoTests::test_is_plan_review_approved_is_the_shared_predicate_not_a_local_copy` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed helper extract_last_history_entry hasattr pin (E-02) |
| `tests/test_oc_runipd.py` | `RunipdBugsFixesTests::test_read_deps_and_set_parsing` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed helper _read_deps and _DEPS_RE hasattr pin (E-02) |
| `tests/test_oc_runipd.py` | `RunipdBugsFixesTests::test_read_deps_and_set_parsing` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed helper _read_deps and _DEPS_RE hasattr pin (E-02) |
| `tests/test_oc_runipd.py` | `PlanBucketRecognitionTests::test_the_docstring_states_that_a_bucket_is_not_a_readiness` | `module_doc_assertion` | `true-pin` | `name-shape` | `delete` | plan_bucket docstring pin; behavior covered by test_edge_satisfied (E-04) |
| `tests/test_oc_runipd.py` | `LaunchProfileDurableStateTests::test_report_and_status_render_the_launch_identity` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_oc_runipd.py` | `VerifierLaunchFreezeTests::test_verify_with_cli_and_resume` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_oc_runipd.py` | `VerifierLaunchFreezeTests::test_launch_identity_rendering` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_oc_runipd.py` | `VerifierLaunchFreezeTests::test_launch_identity_rendering` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_oc_runipd.py` | `VerdictLanePreservationTests::test_every_non_verified_verdict_refuses_integration_on_both_hosts` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_orchestrator_retirement.py` | `<module>` | `inspect_getsource` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a live source inspection |
| `tests/test_orchestrator_retirement.py` | `<module>` | `ast_parse_walk` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a production AST walk |
| `tests/test_orchestrator_retirement.py` | `<module>` | `inspect_getsource` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a live source inspection |
| `tests/test_orchestrator_retirement.py` | `TheActionDecisionIsSHAREDCode::test_action_decision_shared_code_binding_and_queue_derivation` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_orchestrator_retirement.py` | `TheSelectionGateUsesTheSameDecision::test_the_gate_and_the_dispatch_cannot_disagree` | `ast_parse_walk` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a production AST walk |
| `tests/test_orchestrator_retirement.py` | `OrchestratorRetirementRowAuditAndHonestRecord::test_retired_orchestrator_file_states_items_were_superseded_in_body` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | ROLLUP_SUPERSEDED_STATEMENT hasattr pin; constant usage in section check retained (E-02) |
| `tests/test_orchestrator_shape_gate.py` | `BothHostsShareOneDefinition::test_no_new_host_attribute_is_added` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | enforce_orchestrator_shape_gate host hasattr pin forbidding host attribute addition (E-07) |
| `tests/test_orchestrator_shape_gate.py` | `BothHostsShareOneDefinition::test_no_new_host_attribute_is_added` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | enforce_orchestrator_shape_gate host hasattr pin forbidding host attribute addition (E-07) |
| `tests/test_packaging.py` | `PackagingTests::tearDownClass` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_packaging_distribution.py` | `WheelPackagingDistributionTests::tearDownClass` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_packaging_distribution.py` | `SdistPackagingDistributionTests::tearDownClass` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_placement_switch_retire.py` | `TestPlacementSwitchRetire::test_01_target_side_simulated_flip_home_snapshot_byte_identical_and_staged_deletions` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_placement_switch_retire.py` | `TestPlacementSwitchRetire::test_01_target_side_simulated_flip_home_snapshot_byte_identical_and_staged_deletions` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_plain_command_delivery.py` | `test_installer_delivers_plain_and_the_repair_rule` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_plan_holder_predicate.py` | `PlanHolderPredicateTests::test_unreadable_lock_reports_undeterminable` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_plan_holder_predicate.py` | `PlanHolderPredicateTests::test_11_unreadable_runs_tree_discovery_failure_reports_undeterminable` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_platform_lock.py` | `_Blocker::find_spec` | `sys_modules_check` | `false-positive` | `none` | `keep` | Harness module cache manipulation, mock blocker, or conftest loader |
| `tests/test_platform_lock.py` | `_Blocker::find_spec` | `sys_modules_check` | `false-positive` | `none` | `keep` | Harness module cache manipulation, mock blocker, or conftest loader |
| `tests/test_production_correction_turn.py` | `TestProductionCorrectionTurn::fake_agent` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_project_context.py` | `TestProjectSchema::test_canonical_enums_and_constants` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed enum member DURABLE_PRIVATE hasattr pin; normalization retained (E-03) |
| `tests/test_prompts_new.py` | `TestAgentEnvelope::test_the_declared_flag_surface_matches_the_parser` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_prompts_new.py` | `TestAgentEnvelope::test_the_declared_flag_surface_matches_the_parser` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_reaskscore_composed.py` | `TestSharedConstantsByteIdenticalAndUnwidened::test_reexports_are_identical_objects` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_reaskscore_composed.py` | `TestSharedConstantsByteIdenticalAndUnwidened::test_reexports_are_identical_objects` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_record_producers.py` | `DerivedRecordClassTests::test_enum_module_is_this_module_so_members_stay_picklable` | `module_doc_assertion` | `false-positive` | `none` | `keep` | Enum pickling metadata contract: functional Enum API records calling frame module unless set explicitly |
| `tests/test_records_only_lane_rederive.py` | `test_the_seam_is_shared_by_both_runners` | `module_doc_assertion` | `true-pin` | `name-shape` | `delete` | Module identity pin on shared seam attributes (E-02) |
| `tests/test_red_ci_stop.py` | `test_case_b_override_runs_and_records_reason_in_events_and_summary` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_releases_cli.py` | `ReleasesParserTests::test_no_releases_check_subcommand` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed subcommand run_check hasattr pin; CLI exit 2 check retained (E-03) |
| `tests/test_research_descriptive_safety.py` | `TestHelperContract::test_helper_refuse_unsafe_descriptive_contract` | `hasattr_prod` | `true-pin` | `name-shape` | `keep` | Contract check asserting retained delegating alias exists on public module |
| `tests/test_review_failure_reason.py` | `_MockFinding::test_case_a_child_review_content_filter_error` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_run_analytics_privacy_docs.py` | `RunAnalyticsPrivacyDocTests::test_the_analytics_doc_exists_and_is_linked_from_the_index` | `md_doc_prose` | `false-positive` | `none` | `keep` | Published markdown documentation / workflow body under test (P16 exception); kept / handed to 83nnyn |
| `tests/test_run_analytics_statistics.py` | `PricingTests::test_pricing_eras_boundaries_and_rates` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed rate column cache_write_per_mtok hasattr pin; PricingRefusal retained (E-03) |
| `tests/test_run_dashboard.py` | `RenderTests::test_assets_ship_beside_module` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_run_recovery_cli.py` | `TestLedgerResolutionAndWrongFormatVerdict::test_run_engine_step_sequence_without_run_header_refuses_ledger_creation` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_run_selection_policy.py` | `test_type_mapping_is_one_data_table_covering_the_resolver_vocabulary` | `len_const_eq` | `true-pin` | `name-shape` | `convert` | SPEC_TYPE_ORDER length pin; convert to member-set equality citing spec 2.2 (E-05) |
| `tests/test_run_selection_policy.py` | `test_asymmetry_two_an_ungated_draft_is_excluded_while_the_run_proceeds` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_runner_backlog_close_behavior.py` | `TestShutdownReportOnInterrupt::test_the_callable_is_handler_safe` | `hasattr_prod` | `false-positive` | `none` | `keep` | Test handler safety probe |
| `tests/test_runner_backlog_close_behavior.py` | `TestShutdownReportOnInterrupt::test_the_callable_is_handler_safe` | `hasattr_prod` | `false-positive` | `none` | `keep` | Test handler safety probe |
| `tests/test_runner_delegation_and_host_independence.py` | `TestRunnerHostIndependence::test_host_independence_with_peer_blocked` | `sys_modules_check` | `false-positive` | `none` | `keep` | Harness module cache manipulation, mock blocker, or conftest loader |
| `tests/test_runner_delegation_and_host_independence.py` | `PeerBlocker::find_spec` | `sys_modules_check` | `false-positive` | `none` | `keep` | Harness module cache manipulation, mock blocker, or conftest loader |
| `tests/test_runner_delegation_and_host_independence.py` | `PeerBlocker::find_spec` | `sys_modules_check` | `false-positive` | `none` | `keep` | Harness module cache manipulation, mock blocker, or conftest loader |
| `tests/test_runner_fallback_bindings.py` | `test_fallback_integrate_review_lane_branch_forwards_host_equivalent_arguments` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | integrate_review_lane_branch hasattr pin; fallback forwarding behavior retained (E-02) |
| `tests/test_runner_shared.py` | `CrossHostSuccessBarEqualityTests::test_cross_host_success_bar_constants_and_tokens` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `CrossHostSuccessBarEqualityTests::test_cross_host_success_bar_constants_and_tokens` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `CrossHostSuccessBarEqualityTests::test_cross_host_success_bar_constants_and_tokens` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `CrossHostSuccessBarEqualityTests::test_cross_host_success_bar_constants_and_tokens` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `DriverErrorUnificationTests::test_both_runners_share_the_one_class_and_stall_timeout_hierarchy` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `DriverErrorUnificationTests::test_both_runners_share_the_one_class_and_stall_timeout_hierarchy` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `DriverErrorUnificationTests::test_both_runners_share_the_one_class_and_stall_timeout_hierarchy` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `DriverErrorUnificationTests::test_both_runners_share_the_one_class_and_stall_timeout_hierarchy` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `CrossHostReadIdReExportTests::test_cross_host_read_id_permissive_reader_reexport` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `CrossHostReadIdReExportTests::test_cross_host_read_id_permissive_reader_reexport` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `RunagyShimReadIdReExportTests::test_runagy_shim_reexports_permissive_read_id` | `sys_modules_check` | `false-positive` | `none` | `keep` | Harness module cache manipulation, mock blocker, or conftest loader |
| `tests/test_runner_shared.py` | `RunagyShimReadIdReExportTests::test_runagy_shim_reexports_permissive_read_id` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `DiscoverPlansRecordTypeTests::test_both_runners_discover_plans_yields_shared_record_with_kind` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `DiscoverPlansRecordTypeTests::test_both_runners_discover_plans_yields_shared_record_with_kind` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_runner_shared.py` | `AgyVerificationFlagSurfaceTests::test_contradictory_flag_refusal_and_partial_namespace` | `assert_is_host_attr` | `false-positive` | `none` | `keep` | Boolean value check (assertIs False), not a host attribute identity pin |
| `tests/test_runner_shared.py` | `VerificationDestAsymmetryPerHostTests::test_contradictory_pair_handling_refused_on_both_hosts` | `assert_is_host_attr` | `false-positive` | `none` | `keep` | Boolean value check (assertIs False), not a host attribute identity pin |
| `tests/test_runner_shared.py` | `ContentLandedReadingTests::_unanswerable` | `inspect_getsource` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a live source inspection |
| `tests/test_runner_shared.py` | `LaneWorktreeDisplayExistenceTests::test_the_guard_protects_the_SUCCESS_return_not_only_the_reconstruction` | `inspect_getsource` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a live source inspection |
| `tests/test_runwire_verifier_authority.py` | `test_set_level_checks` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Orchestrator set-level check (a)/(b) single-definition and private copy pins (E-07) |
| `tests/test_runwire_verifier_authority.py` | `test_set_level_checks` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Orchestrator set-level check (a)/(b) single-definition and private copy pins (E-07) |
| `tests/test_runwire_verifier_authority.py` | `test_set_level_checks` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Orchestrator set-level check (a)/(b) single-definition and private copy pins (E-07) |
| `tests/test_runwire_verifier_authority.py` | `test_set_level_checks` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Orchestrator set-level check (a)/(b) single-definition and private copy pins (E-07) |
| `tests/test_runwire_verifier_authority.py` | `test_set_level_checks` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Orchestrator set-level check (a)/(b) single-definition and private copy pins (E-07) |
| `tests/test_runwire_verifier_authority.py` | `test_set_level_checks` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Orchestrator set-level check (a)/(b) single-definition and private copy pins (E-07) |
| `tests/test_runwire_verifier_authority.py` | `test_set_level_checks` | `hasattr_prod` | `true-pin` | `arch-freeze` | `delete` | Orchestrator set-level check (a)/(b) single-definition and private copy pins (E-07) |
| `tests/test_runwire_verifier_authority.py` | `test_set_level_checks` | `sys_modules_check` | `true-pin` | `arch-freeze` | `delete` | Subprocess ledger fence assertions (d)/(e) without spec citation (OQ-02) |
| `tests/test_runwire_verifier_authority.py` | `test_set_level_checks` | `sys_modules_check` | `true-pin` | `arch-freeze` | `delete` | Subprocess ledger fence assertions (d)/(e) without spec citation (OQ-02) |
| `tests/test_runwire_verifier_authority.py` | `test_set_level_checks` | `sys_modules_check` | `true-pin` | `arch-freeze` | `delete` | Subprocess ledger fence assertions (d)/(e) without spec citation (OQ-02) |
| `tests/test_scaffold_history_clock.py` | `temporary_timezone` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_scaffold_history_clock.py` | `temporary_timezone` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_scaffold_history_clock.py` | `temporary_cwd` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_selector_two_dialect_readers.py` | `HarnessProvenanceTests::test_harness_measures_workspace_package` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_spec_path_citations.py` | `test_package_source_spec_path_citations_resolve` | `read_prod_source` | `false-positive` | `none` | `keep` | Locates repo root, fixture dir or passes module path to subprocess; does not assert on code structure |
| `tests/test_spec_review_attestation.py` | `WorkflowPackageTests::setUp` | `md_doc_prose` | `false-positive` | `none` | `keep` | Published markdown documentation / workflow body under test (P16 exception); kept / handed to 83nnyn |
| `tests/test_spec_review_attestation.py` | `WorkflowPackageTests::setUp` | `md_doc_prose` | `false-positive` | `none` | `keep` | Published markdown documentation / workflow body under test (P16 exception); kept / handed to 83nnyn |
| `tests/test_spec_review_attestation.py` | `SharedVocabularyTests::setUp` | `md_doc_prose` | `false-positive` | `none` | `keep` | Published markdown documentation / workflow body under test (P16 exception); kept / handed to 83nnyn |
| `tests/test_spec_review_attestation.py` | `ManifestAndDocumentationTests::setUp` | `md_doc_prose` | `false-positive` | `none` | `keep` | Published markdown documentation / workflow body under test (P16 exception); kept / handed to 83nnyn |
| `tests/test_specs_evidence_gate_parity.py` | `SpecsEvidenceGateParityTests::test_set_declaration_agreement` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_specs_releases_descriptive_safety.py` | `SpecsReleasesDescriptiveSafetyTests::test_helper_refuse_unsafe_descriptive_contract` | `hasattr_prod` | `true-pin` | `name-shape` | `keep` | Contract check asserting retained delegating alias exists on public module |
| `tests/test_suppress_narrowing.py` | `fake_launch` | `hasattr_prod` | `false-positive` | `none` | `keep` | Attribute check on standard library module, argparse namespace, test fixture or result object |
| `tests/test_term.py` | `<module>` | `inspect_getsource` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a live source inspection |
| `tests/test_term.py` | `<module>` | `ast_parse_walk` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a production AST walk |
| `tests/test_term.py` | `StylingTests::test_attention_shared_lifecycle_integration` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed/private symbol _STATUS_COLOR_256 / _CLASS_COLOR_256 hasattr pin (E-03) |
| `tests/test_term.py` | `StylingTests::test_attention_shared_lifecycle_integration` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed/private symbol _STATUS_COLOR_256 / _CLASS_COLOR_256 hasattr pin (E-03) |
| `tests/test_terminal_status_vocabulary.py` | `TestTerminalStatusVocabularyDefinitions::test_object_identity_re_export_across_hosts` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_terminal_status_vocabulary.py` | `TestTerminalStatusVocabularyDefinitions::test_object_identity_re_export_across_hosts` | `assert_is_host_attr` | `true-pin` | `name-shape` | `delete` | Runner host identity pin (E-02) |
| `tests/test_testprune_tools.py` | `test_pinscan_fixture_candidate` | `inspect_getsource` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a live source inspection |
| `tests/test_testprune_tools.py` | `test_pinscan_fixture_candidate` | `ast_parse_walk` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a production AST walk |
| `tests/test_turn_bounds.py` | `test_constants_names_defaults_and_zero_disable` | `hasattr_prod` | `true-pin` | `name-shape` | `delete` | Removed name MAX_TURN_DEADLINE hasattr pin (E-03) |
| `tests/test_v_item_demonstration_reachability.py` | `<module>` | `inspect_getsource` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a live source inspection |
| `tests/test_v_item_demonstration_reachability.py` | `<module>` | `inspect_getsource` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a live source inspection |
| `tests/test_v_item_demonstration_reachability.py` | `<module>` | `ast_parse_walk` | `false-positive` | `none` | `keep` | Docstring, comment or scanner test fixture, not a production AST walk |
| `tests/test_verifier_corroboration.py` | `TestSharedToolCallExtraction::test_behavioral_import_purity` | `sys_modules_check` | `true-pin` | `arch-freeze` | `keep` | Behavioral import purity test in clean subprocess |
| `tests/test_verifier_corroboration.py` | `TestSharedToolCallExtraction::test_behavioral_import_purity` | `sys_modules_check` | `true-pin` | `arch-freeze` | `keep` | Behavioral import purity test in clean subprocess |
| `tests/test_verifier_evidence.py` | `ExecutionReportRenderingTests::test_write_report_renders_verification_evidence_section` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_verifier_evidence.py` | `ExecutionReportRenderingTests::test_write_report_omits_section_when_no_verification_evidence` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_worktree_lease_stdlib_only.py` | `WorktreeLeaseStdlibOnlyTests::test_worktree_lease_imports_no_first_party_modules` | `sys_modules_check` | `true-pin` | `arch-freeze` | `keep` | Behavioral import purity guarding against measured 2.10x import regression and cycle with runner_shared |
| `tests/test_worktree_lease_stdlib_only.py` | `WorktreeLeaseStdlibOnlyTests::test_worktree_lease_imports_no_first_party_modules` | `sys_modules_check` | `true-pin` | `arch-freeze` | `keep` | Behavioral import purity guarding against measured 2.10x import regression and cycle with runner_shared |
| `tests/test_worktree_lease_stdlib_only.py` | `WorktreeLeaseStdlibOnlyTests::test_lane_merged_into_target_lazy_delegation` | `sys_modules_check` | `true-pin` | `arch-freeze` | `keep` | Behavioral import purity guarding against measured 2.10x import regression and cycle with runner_shared |
| `tests/test_worktree_lease_stdlib_only.py` | `WorktreeLeaseStdlibOnlyTests::test_lane_merged_into_target_lazy_delegation` | `sys_modules_check` | `true-pin` | `arch-freeze` | `keep` | Behavioral import purity guarding against measured 2.10x import regression and cycle with runner_shared |
| `tests/test_worktree_lease_stdlib_only.py` | `WorktreeLeaseStdlibOnlyTests::test_lane_merged_into_target_lazy_delegation` | `sys_modules_check` | `true-pin` | `arch-freeze` | `keep` | Behavioral import purity guarding against measured 2.10x import regression and cycle with runner_shared |
| `tests/test_worktree_lease_stdlib_only.py` | `WorktreeLeaseStdlibOnlyTests::test_lane_merged_into_target_lazy_delegation` | `sys_modules_check` | `true-pin` | `arch-freeze` | `keep` | Behavioral import purity guarding against measured 2.10x import regression and cycle with runner_shared |
| `tests/test_write_report_malformed_entry.py` | `test_well_formed_report_byte_identical_to_fixture` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_write_report_malformed_entry.py` | `test_well_formed_report_byte_identical_to_fixture` | `md_doc_prose` | `false-positive` | `none` | `keep` | Reads test execution artifact or test fixture markdown; does not pin production doc prose |
| `tests/test_xdist_auto_workers.py` | `_load_conftest` | `sys_modules_check` | `false-positive` | `none` | `keep` | Harness module cache manipulation, mock blocker, or conftest loader |

## 83nnyn baseline

- **Run Directory**: `.aw/state/percov/83nnyn-base`
- **Git HEAD**: `d3ef9d175b2d20312393e3fa30c94f553c149857`
- **Host**: Linux 12-CPU
- **Worker Count**: 6 xdist workers (`--dist=worksteal`)
- **Instrumented Wall Time**: 1422.63s
- **Python Version**: 3.14.6 (main, Jul  8 2026, 13:05:09) [GCC 13.3.0]
- **Coverage Version**: 7.15.0 (core: `ctrace`, `patch = subprocess`)
- **meta.json pytest_exit**: 1 (7 known pre-existing adjacent/environmental failures noted below)

### Pre-existing Failures Recorded

- `tests.test_clean_target_config_home.TestCleanTargetConfigHome::test_case_l_tracked_install_still_writes_target`
- `tests.test_cli.Order15CliTests::test_install_legacy_repo_interactive_accept_migrates_to_aw`
- `tests.test_cli.Order15CliTests::test_install_legacy_repo_interactive_decline_keeps_legacy`
- `tests.test_docs_test_citations::test_published_docs_test_citations_exist`
- `tests.test_install_report_truth.TestInstallReportTruth::test_second_install_nochange_leaves_clean_status_and_no_false_lines`
- `tests.test_term.CliNeverLeaksTheInteractivityOverrideTests::test_early_exit_paths_and_nested_invocations`
- `tests.test_testprune_tools::test_covctx_plugin_subprocess_context_propagation`
- `tests/test_clean_target_config_home.py::TestCleanTargetConfigHome::test_case_l_tracked_install_still_writes_target`
- `tests/test_cli.py::Order15CliTests::test_install_legacy_repo_interactive_accept_migrates_to_aw`
- `tests/test_cli.py::Order15CliTests::test_install_legacy_repo_interactive_decline_keeps_legacy`
- `tests/test_docs_test_citations.py::test_published_docs_test_citations_exist`
- `tests/test_install_report_truth.py::TestInstallReportTruth::test_second_install_nochange_leaves_clean_status_and_no_false_lines`
- `tests/test_term.py::CliNeverLeaksTheInteractivityOverrideTests::test_early_exit_paths_and_nested_invocations`
- `tests/test_testprune_tools.py::test_covctx_plugin_subprocess_context_propagation`

### Suite Coverage Totals

- **Total Collected Tests**: 9846
- **No-Coverage Tests**: 458
- **Covered Statements**: 126515 / 99474 (82.81%)
- **Covered Branches**: 165366 / 40572 (74.62%)
- **Tests with 0 Unique Lines**: 8043
- **Tests with 0 Unique Arcs**: 7846

### Core Tier Coverage Totals (`core_measure`)

- **Core Covered Lines**: 35899 / 99474 (31.8%)
- **Core Covered Branches**: 8678 / 40572 (21.4%)
- **Zero Core Coverage Modules**: 0 / 197

### Owner 83nnyn Test Count and Head

Total tests assigned to `83nnyn`: 2635 across 288 modules.

| Test Node ID | Module | Duration | Reason |
| --- | --- | --- | --- |
| `tests/test_agent_findings_severity.py::AgentFindingsSeverityTests::test_case_d_data_findings_fallback_omits_severity_breakdown` | `tests/test_agent_findings_severity.py` | 0.000s | defect-cited (wizzis); consolidate (identical peer) |
| `tests/test_agent_findings_severity.py::AgentFindingsSeverityTests::test_case_e_clean_result_no_diagnostics_omits_severity_breakdown` | `tests/test_agent_findings_severity.py` | 0.000s | defect-cited (wizzis); consolidate (identical peer) |
| `tests/test_agent_record_guard.py::AgentRecordGuardTests::test_guarded_serializer_substitutes_on_invalid_records` | `tests/test_agent_record_guard.py` | 0.000s | defect-cited (wqiofa); consolidate (identical peer) |
| `tests/test_agent_record_guard.py::AgentRecordGuardTests::test_no_leak_property` | `tests/test_agent_record_guard.py` | 0.000s | defect-cited (wqiofa); consolidate (identical peer) |
| `tests/test_agent_schema_paths.py::NormalizeRepoPathTests::test_relative_path_is_taken_relative_to_root` | `tests/test_agent_schema_paths.py` | 0.000s | consolidate (identical peer) |
| `tests/test_agent_schema_paths.py::NormalizeRepoPathTests::test_symlinked_root_relativizes_a_resolved_path` | `tests/test_agent_schema_paths.py` | 0.000s | consolidate (identical peer) |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[ipd scaffold]` | `tests/test_agent_surface_conformance.py` | 0.967s | protected (family); defect-cited (f36de0, kjr5ol); consolidate (identical peer) |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[research new-comparison]` | `tests/test_agent_surface_conformance.py` | 1.118s | protected (family); defect-cited (f36de0, kjr5ol); consolidate (identical peer) |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[research new]` | `tests/test_agent_surface_conformance.py` | 1.009s | protected (family); defect-cited (f36de0, kjr5ol); consolidate (identical peer) |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation[storage move]` | `tests/test_agent_surface_conformance.py` | 0.974s | protected (family); defect-cited (f36de0, kjr5ol); consolidate (identical peer) |
| `tests/test_agy_failed_state_parity.py::test_cross_reader_agy_tool_state_parity[ACTIVE]` | `tests/test_agy_failed_state_parity.py` | 0.000s | consolidate (identical peer) |
| `tests/test_agy_failed_state_parity.py::test_cross_reader_agy_tool_state_parity[CANCELED]` | `tests/test_agy_failed_state_parity.py` | 0.000s | consolidate (identical peer) |
| `tests/test_agy_failed_state_parity.py::test_cross_reader_agy_tool_state_parity[ERROR]` | `tests/test_agy_failed_state_parity.py` | 0.000s | consolidate (identical peer) |
| `tests/test_agy_failed_state_parity.py::test_cross_reader_agy_tool_state_parity[FAILED]` | `tests/test_agy_failed_state_parity.py` | 0.000s | consolidate (identical peer) |
| `tests/test_agy_run.py::AgyRunArgParseTests::test_dangerous_and_add_dirs_flags` | `tests/test_agy_run.py` | 0.000s | defect-cited (5s31xp); consolidate (identical peer) |
| `tests/test_agy_run.py::AgyRunArgParseTests::test_default_options` | `tests/test_agy_run.py` | 0.000s | defect-cited (5s31xp); consolidate (identical peer) |
| `tests/test_agy_run.py::AgyRunArgParseTests::test_explicit_file_mode` | `tests/test_agy_run.py` | 0.000s | defect-cited (5s31xp); consolidate (identical peer) |
| `tests/test_agy_run.py::AgyRunArgParseTests::test_explicit_ipd_mode` | `tests/test_agy_run.py` | 0.000s | defect-cited (5s31xp); consolidate (identical peer) |
| `tests/test_agy_run.py::AgyRunArgParseTests::test_explicit_model` | `tests/test_agy_run.py` | 0.000s | defect-cited (5s31xp); consolidate (identical peer) |
| `tests/test_agy_run.py::AgyRunArgParseTests::test_explicit_prompt_mode` | `tests/test_agy_run.py` | 0.000s | defect-cited (5s31xp); consolidate (identical peer) |

### Per-Batch Target Durations (`junit.xml`)

- **E-02 (descriptive_refusal_hoist)**: 2.081s
  - `tests/test_descriptive_refusal_hoist.py`: 2.081s
- **E-03 (statusline)**: 0.969s
  - `tests/test_statusline_stop_tally.py`: 0.312s
  - `tests/test_statusline_visible_width.py`: 0.506s
  - `tests/test_statusline_ascii_mode.py`: 0.151s
- **E-04 (usage_refusal)**: 42.806s
  - `tests/test_usage_refusal_agent_record.py`: 42.806s
- **E-05 (runner)**: 371.891s
  - `tests/test_oc_runipd.py`: 222.258s
  - `tests/test_runner_shared.py`: 44.458s
  - `tests/test_agy_runipd_cli.py`: 38.202s
  - `tests/test_finalize_sendback.py`: 5.131s
  - `tests/test_orchestrator_retirement.py`: 14.310s
  - `tests/test_runner_backlog_close_behavior.py`: 22.857s
  - `tests/test_agy_failed_state_parity.py`: 0.015s
  - `tests/test_lane_reaper_callshape.py`: 0.080s
  - `tests/test_prior_attempt_projection.py`: 0.006s
  - `tests/test_retry_class_mapping.py`: 0.005s
  - `tests/test_run_cli_human_redaction.py`: 23.779s
  - `tests/test_run_dir_outcomes_parent_is_guaranteed.py`: 0.097s
  - `tests/test_run_progress_count.py`: 0.005s
  - `tests/test_run_summary_visible_width.py`: 0.059s
  - `tests/test_runner_safety_probe_memo.py`: 0.016s
  - `tests/test_runs_flag_position_parity.py`: 0.613s
- **E-06 (records)**: 162.388s
  - `tests/test_status_set.py`: 43.253s
  - `tests/test_backlog.py`: 2.860s
  - `tests/test_group_verb_policy.py`: 12.507s
  - `tests/test_research_index.py`: 1.073s
  - `tests/test_attention.py`: 19.278s
  - `tests/test_attention_blind_spot.py`: 6.813s
  - `tests/test_attention_degraded_item.py`: 10.279s
  - `tests/test_backlog_close_host_label.py`: 0.159s
  - `tests/test_backlog_gate_follows_status.py`: 2.415s
  - `tests/test_backlog_history_dedup_parity.py`: 3.275s
  - `tests/test_backlog_transition_authority.py`: 1.207s
  - `tests/test_history_date_clock_sidecar.py`: 2.032s
  - `tests/test_history_label_parity.py`: 1.409s
  - `tests/test_history_write_order.py`: 1.276s
  - `tests/test_prompts_attention.py`: 0.020s
  - `tests/test_releases_line_writers.py`: 8.922s
  - `tests/test_specs_metadata_duplicate_bullet.py`: 0.017s
  - `tests/test_index_check_agent_records.py`: 45.593s
- **E-07 (ipd)**: 115.812s
  - `tests/test_ipd_lifecycle_cli.py`: 39.140s
  - `tests/test_ipd_lint.py`: 76.069s
  - `tests/test_ipd_templates.py`: 0.034s
  - `tests/test_lifecycle_dirs.py`: 0.019s
  - `tests/test_lifecycle_gate_coverage.py`: 0.216s
  - `tests/test_scaffold_history_clock.py`: 0.334s

### Parametrize Census (Functions with >= 9 cases: 34)

| Function | Cases |
| --- | --- |
| `tests/test_descriptive_refusal_hoist.py::test_all_five_routes_match_frozen_table_for_nonempty_verbs` | 900 |
| `tests/test_usage_refusal_agent_record.py::test_handler_usage_refusal_across_modes` | 102 |
| `tests/test_descriptive_refusal_hoist.py::test_all_five_routes_match_frozen_table_for_empty_verb` | 90 |
| `tests/test_shared_flag_honored.py::test_parser_usage_refusal_fields_honored_required_leaves` | 69 |
| `tests/test_usage_refusal_agent_record.py::test_required_arg_leaf_agent_mode` | 69 |
| `tests/test_usage_refusal_agent_record.py::test_required_arg_leaf_json_mode` | 69 |
| `tests/test_statusline_stop_tally.py::TestStatuslineStopTallyRendering::test_statusline_rectangular_with_badges` | 60 |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance` | 51 |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_read` | 51 |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_read` | 51 |
| `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation` | 33 |
| `tests/test_shared_flag_honored.py::test_json_flag_honored_mutation` | 33 |
| `tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation` | 33 |
| `tests/test_statusline_visible_width.py::test_statusline_box_is_rectangular` | 32 |
| `tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage` | 24 |
| `tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two` | 24 |
| `tests/test_family_root_agent_conformance.py::test_family_root_agent_conformance` | 23 |
| `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap` | 21 |
| `tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves` | 21 |
| `tests/test_statusline_ascii_mode.py::TestStatuslineAsciiModePurity::test_format_statusline_lines_ascii_purity_swept_states` | 16 |
| `tests/test_statusline_ascii_mode.py::TestStatuslineAsciiModePurity::test_statusline_class_ascii_purity_swept_states` | 16 |
| `tests/test_no_project_exit_is_cannot_run.py::test_no_project_cross_surface_exit_and_payload` | 12 |
| `tests/test_egress_policy.py::TestEgressPolicyLoader::test_unparseable_policy_raises` | 11 |
| `tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity` | 11 |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::test_construction_refuses_malformed_entries` | 10 |
| `tests/test_runs_repo_alias.py::test_repo_alias_parses_to_dir_attr` | 10 |
| `tests/test_runs_repo_alias.py::test_dir_control_parses_to_dir_attr` | 10 |
| `tests/test_group_verb_policy.py::test_group_setid_refusal` | 9 |
| `tests/test_group_verb_policy.py::test_group_setid_warning` | 9 |
| `tests/test_group_verb_policy.py::test_group_setid_quiet_at_warn_limit` | 9 |
| `tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max` | 9 |
| `tests/test_statusline_ascii_mode.py::TestStatuslineAsciiModePurity::test_progress_bar_visible_width_parity_and_ascii_purity` | 9 |
| `tests/test_statusline_behavior.py::TestStatuslineHostileInputs::test_hostile_inputs_return_well_formed_rectangular_box` | 9 |
| `tests/test_statusline_behavior.py::TestStatuslineFormatters::test_token_magnitude_boundaries` | 9 |


## Recorded deletions

| Node ID | Category | Reason | Unique Lines Lost | Unique Arcs Lost | Justification / Behavioral Sibling | Child ID6 | Commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `tests/test_agy_runipd_cli.py::AgyDependencyPathsAreSharedTests::test_both_dependency_entry_points_are_the_shared_objects` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | `492c07b77` |
| `tests/test_agy_runipd_cli.py::AgyPerArtifactDispositionLineTests::test_both_hosts_render_the_line_from_the_same_object` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | `492c07b77` |
| `tests/test_agy_runipd_cli.py::AgyEndOfRunDispositionSummaryTests::test_this_hosts_footer_names_ANTIGRAVITY_and_shared_object` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | `492c07b77` |
| `tests/test_agy_runipd_cli.py::AgyVerdictMappingTests::test_this_host_binds_the_shared_mapping_and_holds_no_copy` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | `492c07b77` |
| `tests/test_agy_runipd_cli.py::AgyFullAutoApprovalTests::test_predicate_is_the_shared_one_and_local_copies_are_gone` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | |
| `tests/test_attention.py::LaneRemedyHintTests::` (`self.assertTrue(hasattr(oc_runipd, att.LANE_INTEGRATE_PROBE_SYMBOL))`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_attention.py::LaneRemedyHintTests::` (`self.assertTrue(hasattr(agy_runipd, att.LANE_INTEGRATE_PROBE_SYMBOL))`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests::` (`self.assertIs(oc_runipd.LANE_PROMPT_TIMEOUT, runner_shared.LANE_PROMPT_TIMEOUT)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests::` (`self.assertIs(agy_runipd.LANE_PROMPT_TIMEOUT, runner_shared.LANE_PROMPT_TIMEOUT)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests::test_shared_and_declined_constants_guards` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | |
| `tests/test_oc_runipd.py::AllSelectorAndFullAutoTests::test_is_plan_review_approved_is_the_shared_predicate_not_a_local_copy` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | `492c07b77` |
| `tests/test_orchestrator_retirement.py::TheActionDecisionIsSHAREDCode::` (`self.assertIs(agy_runipd.PlanRecord, oc_runipd.PlanRecord)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_orchestrator_retirement.py::OrchestratorRetirementRowAuditAndHonestRecord::` (`self.assertTrue(`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_orchestrator_shape_gate.py::BothHostsShareOneDefinition::test_each_host_resolves_the_gate_to_the_SAME_object` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | `492c07b77` |
| `tests/test_reaskscore_composed.py::TestSharedConstantsByteIdenticalAndUnwidened::test_reexports_are_identical_objects` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | `492c07b77` |
| `tests/test_records_only_lane_rederive.py::test_the_seam_is_shared_by_both_runners` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | `492c07b77` |
| `tests/test_runner_fallback_bindings.py::test_fallback_integrate_review_lane_branch_forwards_host_equivalent_argument` (`assert not hasattr(runner_shared, "integrate_review_lane_branch")`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests::` (`self.assertIs(oc_runipd.SUCCESS_STATES, runner_shared.SUCCESS_STATES)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests::` (`self.assertIs(agy_runipd.SUCCESS_STATES, runner_shared.SUCCESS_STATES)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests::` (`self.assertIs(`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests::` (`self.assertIs(`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests::` (`self.assertIs(getattr(oc_runipd, name), shared)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests::` (`self.assertIs(getattr(agy_runipd, name), shared)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::DriverErrorUnificationTests::` (`self.assertIs(oc_runipd.DriverError, agy_runipd.DriverError)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::DriverErrorUnificationTests::` (`self.assertIs(oc_runipd.DriverError, runner_shared.DriverError)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::DriverErrorUnificationTests::` (`self.assertIs(getattr(oc_runipd, name), shared_cls)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::DriverErrorUnificationTests::` (`self.assertIs(getattr(agy_runipd, name), shared_cls)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::CrossHostReadIdReExportTests::` (`self.assertIs(oc_runipd._read_id, selectors.read_front_matter_id)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::CrossHostReadIdReExportTests::` (`self.assertIs(agy_runipd._read_id, selectors.read_front_matter_id)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::RunagyShimReadIdReExportTests::` (`self.assertIs(shim._read_id, agy_runipd._read_id)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests::` (`self.assertIs(oc_runipd.PlanRecord, agy_runipd.PlanRecord)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests::` (`self.assertIs(oc_runipd.PlanRecord, runner_shared.PlanRecord)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests::` (`self.assertIn("kind", runner_shared.PlanRecord._fields)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests::` (`self.assertIs(type(record), runner_shared.PlanRecord)`) | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted assertion (E-02); test retains behavioral checks | `tv72xy` | `492c07b77` |
| `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_object_identity_re_export_across_hosts` | `name-shape` | Runner host-identity and placement pins | 0 | 0 | Deleted pin (E-02); behavioral coverage retained in module | `tv72xy` | `492c07b77` |
| `tests/test_attention.py::SharedLifecycleResolverTests::` (`self.assertFalse(hasattr(att, "_STATUS_COLOR_256"))`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_attention.py::SharedLifecycleResolverTests::` (`self.assertEqual(`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_check_engine_metadata_region.py::test_bounded_accessors_ignore_body_quotations` (`assert hasattr(ce, "_read_item_id"), "check_engine must expose _read_item_id"`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_check_engine_metadata_region.py::test_bounded_accessors_ignore_body_quotations` (`assert hasattr(`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_check_engine_metadata_region.py::test_bounded_accessors_ignore_body_quotations` (`assert hasattr(`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_descriptive_refusal_hoist.py::test_public_hoisted_helper_exists` (`assert not hasattr(attention_contract, "_refuse_unsafe_descriptive")`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_host_capability_extension.py::RunnerSafetyProbeTests::` (`self.assertTrue(`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_host_capability_extension.py::DenyPushRemovedTests::` (`self.assertFalse(hasattr(hsp, "CAP_DENY_PUSH"))`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_ipd_lint.py::StructuralRuleTests::test_the_dash_rule_code_is_gone_rather_than_merely_silent` | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted pin (E-03); behavioral coverage retained in module | `tv72xy` | `b07b6ef2a` |
| `tests/test_project_context.py::TestProjectSchema::` (`self.assertFalse(hasattr(DurabilityState, "DURABLE_PRIVATE"))`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_releases_cli.py::ReleasesParserTests::` (`self.assertFalse(hasattr(releases, "run_check"))`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_run_analytics_statistics.py::PricingTests::` (`self.assertFalse(hasattr(rates, "cache_write_per_mtok"))`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_term.py::StylingTests::` (`self.assertFalse(hasattr(att, "_STATUS_COLOR_256"))`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_term.py::StylingTests::` (`self.assertTrue(hasattr(att, "_CLASS_COLOR_256"))`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_term.py::StylingTests::` (`self.assertEqual(`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_turn_bounds.py::test_constants_names_defaults_and_zero_disable` (`assert not hasattr(lane_containment, "MAX_TURN_DEADLINE")`) | `name-shape` | Removed-symbol and private-name pins | 0 | 0 | Deleted assertion (E-03); test retains behavioral checks | `tv72xy` | `b07b6ef2a` |
| `tests/test_agy_run.py::AntigravityExecuteIpdCompatibilityTests::` (`self.assertTrue(hasattr(antigravity_execute_ipd, "ScriptError"))`) | `structure` | Compat wrapper re-exports converted to behavioral CLI test | 0 | 0 | Deleted assertion (E-09); test retains behavioral checks | `tv72xy` | `9ab05b7ef` |
| `tests/test_agy_run.py::AntigravityExecuteIpdCompatibilityTests::` (`self.assertTrue(hasattr(antigravity_execute_ipd, "AgyResult"))`) | `structure` | Compat wrapper re-exports converted to behavioral CLI test | 0 | 0 | Deleted assertion (E-09); test retains behavioral checks | `tv72xy` | `9ab05b7ef` |
| `tests/test_agy_run.py::AntigravityExecuteIpdCompatibilityTests::` (`self.assertTrue(hasattr(antigravity_execute_ipd, "resolve_ipd"))`) | `structure` | Compat wrapper re-exports converted to behavioral CLI test | 0 | 0 | Deleted assertion (E-09); test retains behavioral checks | `tv72xy` | `9ab05b7ef` |
| `tests/test_agy_run.py::AntigravityExecuteIpdCompatibilityTests::` (`self.assertTrue(hasattr(antigravity_execute_ipd, "run_agy"))`) | `structure` | Compat wrapper re-exports converted to behavioral CLI test | 0 | 0 | Deleted assertion (E-09); test retains behavioral checks | `tv72xy` | `9ab05b7ef` |
| `tests/test_agy_run.py::AntigravityExecuteIpdCompatibilityTests::` (`self.assertTrue(hasattr(antigravity_execute_ipd, "main"))`) | `structure` | Compat wrapper re-exports converted to behavioral CLI test | 0 | 0 | Deleted assertion (E-09); test retains behavioral checks | `tv72xy` | `9ab05b7ef` |
| `tests/test_agy_run.py::AntigravityExecuteIpdCompatibilityTests::` (`self.assertTrue(hasattr(antigravity_execute_ipd, "run"))`) | `structure` | Compat wrapper re-exports converted to behavioral CLI test | 0 | 0 | Deleted assertion (E-09); test retains behavioral checks | `tv72xy` | `9ab05b7ef` |
| `tests/test_completion_stale_notice.py::DocumentationAndDocstringTests::test_test_completion_docstring_updated` | `name-shape` | Docstring and prose pins; covered by behavioral review-target test | 0 | 0 | Deleted pin (E-04); behavioral coverage retained in module | `tv72xy` | `d9f5baa33` |
| `tests/test_host_sandbox_profile.py::ProfileDispatchTests::test_module_publishes_its_guarantees` | `name-shape` | Docstring and prose pins; covered by behavioral review-target test | 0 | 0 | Deleted pin (E-04); behavioral coverage retained in module | `tv72xy` | `d9f5baa33` |
| `tests/test_oc_runipd.py::PlanBucketRecognitionTests::test_the_docstring_states_that_a_bucket_is_not_a_readiness` | `name-shape` | Docstring and prose pins; covered by behavioral review-target test | 0 | 0 | Deleted pin (E-04); behavioral coverage retained in module | `tv72xy` | `d9f5baa33` |
| `tests/test_attention_contract.py::RuleCatalogTests::` (`self.assertGreaterEqual(len(A.RULE_IDS), 12)`) | `structure` | Count and vocabulary-size pins; converted to member equality or deleted | 0 | 0 | Deleted assertion (E-05); test retains behavioral checks | `tv72xy` | `0d0439fe7` |
| `tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::` (`self.assertEqual(len(runner_shared.VERIFY_ABSENCE_CODES), 4)`) | `structure` | Count and vocabulary-size pins; converted to member equality or deleted | 0 | 0 | Deleted assertion (E-05); test retains behavioral checks | `tv72xy` | `0d0439fe7` |
| `tests/test_fix_it_global_caps.py::TestFixItTurnsSpent::` (`self.assertEqual(len(runner_shared.FIX_IT_COUNT_KEYS), 13)`) | `structure` | Count and vocabulary-size pins; converted to member equality or deleted | 0 | 0 | Deleted assertion (E-05); test retains behavioral checks | `tv72xy` | `0d0439fe7` |
| `tests/test_fix_it_global_caps.py::TestFixItTurnsSpent::` (`self.assertEqual(runner_shared.fix_it_turns_spent(item), 13)`) | `structure` | Count and vocabulary-size pins; converted to member equality or deleted | 0 | 0 | Deleted assertion (E-05); test retains behavioral checks | `tv72xy` | `0d0439fe7` |
| `tests/test_ipd_exec_finding_codes.py::IpdExecFindingCodesTests::` (`self.assertEqual(len(run_evidence.run_finding_codes()), 12)`) | `structure` | Count and vocabulary-size pins; converted to member equality or deleted | 0 | 0 | Deleted assertion (E-05); test retains behavioral checks | `tv72xy` | `0d0439fe7` |
| `tests/test_ipd_exec_finding_codes.py::IpdExecFindingCodesTests::` (`self.assertEqual(len(run_evidence.bound_run_finding_codes()), 10)`) | `structure` | Count and vocabulary-size pins; converted to member equality or deleted | 0 | 0 | Deleted assertion (E-05); test retains behavioral checks | `tv72xy` | `0d0439fe7` |
| `tests/test_run_analytics.py::ProvenanceTests::` (`self.assertEqual(len(schema.ABSENT_PROVENANCE), 3)`) | `structure` | Count and vocabulary-size pins; converted to member equality or deleted | 0 | 0 | Deleted assertion (E-05); test retains behavioral checks | `tv72xy` | `0d0439fe7` |
| `tests/test_run_selection_policy.py::test_type_mapping_is_one_data_table_covering_the_resolver_vocabulary` (`assert set(pol.RESOLVER_TYPE_BY_SPEC_TYPE) == set(pol.SPEC_TYPE_ORDER)`) | `structure` | Count and vocabulary-size pins; converted to member equality or deleted | 0 | 0 | Deleted assertion (E-05); test retains behavioral checks | `tv72xy` | `0d0439fe7` |
| `tests/test_run_selection_policy.py::test_type_mapping_is_one_data_table_covering_the_resolver_vocabulary` (`assert len(pol.SPEC_TYPE_ORDER) == 7`) | `structure` | Count and vocabulary-size pins; converted to member equality or deleted | 0 | 0 | Deleted assertion (E-05); test retains behavioral checks | `tv72xy` | `0d0439fe7` |
| `tests/test_history_order.py::HistoryOrderFixtureTests::` (`self.assertEqual(`) | `structure` | Vacuous if hasattr guards around private helper; public drift check retained | 0 | 0 | Deleted assertion (E-06); test retains behavioral checks | `tv72xy` | `545199f5a` |
| `tests/test_history_order.py::HistoryOrderFixtureTests::` (`self.assertEqual(`) | `structure` | Vacuous if hasattr guards around private helper; public drift check retained | 0 | 0 | Deleted assertion (E-06); test retains behavioral checks | `tv72xy` | `545199f5a` |
| `tests/test_history_order.py::HistoryOrderFixtureTests::` (`self.assertEqual(`) | `structure` | Vacuous if hasattr guards around private helper; public drift check retained | 0 | 0 | Deleted assertion (E-06); test retains behavioral checks | `tv72xy` | `545199f5a` |
| `tests/test_history_order.py::HistoryOrderFixtureTests::` (`self.assertEqual(`) | `structure` | Vacuous if hasattr guards around private helper; public drift check retained | 0 | 0 | Deleted assertion (E-06); test retains behavioral checks | `tv72xy` | `545199f5a` |
| `tests/test_history_order.py::HistoryOrderFixtureTests::` (`self.assertEqual(`) | `structure` | Vacuous if hasattr guards around private helper; public drift check retained | 0 | 0 | Deleted assertion (E-06); test retains behavioral checks | `tv72xy` | `545199f5a` |
| `tests/test_check_engine.py::CarrierEvidencePlanAndSpecDisposition::test_fall_through_live_carrier_accepted` (`if hasattr(ce, "_evidence_spec_unshipped"):`) | `structure` | Vacuous if hasattr guard around check_engine private helper; public verdict.path retained | 0 | 0 | Deleted assertion (E-06); test retains behavioral checks | `tv72xy` | |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::` (`assert not hasattr(policy, "allow_all")`) | `arch-freeze` | Architecture freeze pins; refactoring prohibitions and stdlib-only imports | 0 | 0 | Deleted assertion (E-07); test retains behavioral checks | `tv72xy` | `48e479330` |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::` (`assert not hasattr(policy, "deny_list")`) | `arch-freeze` | Architecture freeze pins; refactoring prohibitions and stdlib-only imports | 0 | 0 | Deleted assertion (E-07); test retains behavioral checks | `tv72xy` | `48e479330` |
| `tests/test_egress_policy.py::TestEgressPolicyUnit::` (`assert not hasattr(policy, "negation")`) | `arch-freeze` | Architecture freeze pins; refactoring prohibitions and stdlib-only imports | 0 | 0 | Deleted assertion (E-07); test retains behavioral checks | `tv72xy` | `48e479330` |
| `tests/test_hostdedup_third_host.py::ThirdHostInitializationAndLimitTests::test_pin_measured_turn_execution_limits` | `arch-freeze` | Architecture freeze pins; refactoring prohibitions and stdlib-only imports | 0 | 0 | Deleted pin (E-07); behavioral coverage retained in module | `tv72xy` | `48e479330` |
| `tests/test_ipd_authoring.py::AtomicWriteTests::test_authoring_module_is_stdlib_only` | `arch-freeze` | Architecture freeze pins; refactoring prohibitions and stdlib-only imports | 0 | 0 | Deleted pin (E-07); behavioral coverage retained in module | `tv72xy` | `48e479330` |
| `tests/test_ipd_lint.py::AgentOutputTests::test_lint_module_is_stdlib_only` | `arch-freeze` | Architecture freeze pins; refactoring prohibitions and stdlib-only imports | 0 | 0 | Deleted pin (E-07); behavioral coverage retained in module | `tv72xy` | `48e479330` |
| `tests/test_ipd_lint.py::ScopePathsCheckpointTests::test_enforcement_lives_in_the_checkpoint_layer_not_in_metadata` | `arch-freeze` | Architecture freeze pins; refactoring prohibitions and stdlib-only imports | 0 | 0 | Deleted pin (E-07); behavioral coverage retained in module | `tv72xy` | `48e479330` |
| `tests/test_ipd_schema.py::DensityHeuristicTests::test_module_is_stdlib_only` | `arch-freeze` | Architecture freeze pins; refactoring prohibitions and stdlib-only imports | 0 | 0 | Deleted pin (E-07); behavioral coverage retained in module | `tv72xy` | `48e479330` |
| `tests/test_orchestrator_shape_gate.py::test_no_new_host_attribute_is_added` | `arch-freeze` | Architecture freeze pins; refactoring prohibitions and stdlib-only imports | 0 | 0 | Deleted pin (E-07); behavioral coverage retained in module | `tv72xy` | `48e479330` |
| `tests/test_runwire_verifier_authority.py::test_set_level_checks` | `arch-freeze` | Architecture freeze pins; refactoring prohibitions and stdlib-only imports | 0 | 0 | Deleted pin (E-07); behavioral coverage retained in module | `tv72xy` | `48e479330` |
