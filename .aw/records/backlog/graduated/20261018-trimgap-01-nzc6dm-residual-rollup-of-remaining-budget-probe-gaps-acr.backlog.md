- Id: nzc6dm
- Status: graduated
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Residual rollup of remaining budget probe gaps across 37 module groups

## Workflow history
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175032Z-1384916: 1z19cn, e6lq6y, j77z5h, qx3ppg, sbcmke, v44udc
- 2026-10-18 created (aw backlog): Residual rollup of remaining budget probe gaps across 37 module groups

Carries the 37 residual budget probe gap groups (ranks 16 through 52) spanning 43 candidate production keys across 26 modules.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Enumeration of rolled-up groups:
- Group 16: agent_workflows/ipd_schema.py [probe then restore] (2 keys: _parse_item_dependency_edge, parse_item_dependencies)
- Group 17: agent_workflows/plans_refs.py [probe then restore] (2 keys: apply_renames, _dirs)
- Group 18: agent_workflows/render_stream.py [restore behavioral coverage] (2 keys: Palette.status, _status_glyph_char)
- Group 19: agent_workflows/result_types.py [probe then restore] (2 keys: CommandResult.to_agent_record, select_output)
- Group 20: agent_workflows/run_analytics_config.py [probe then restore] (2 keys: _coerce_bool, parse_telemetry_settings)
- Group 21: agent_workflows/term.py [probe then restore] (2 keys: stdin_is_interactive, is_interactive)
- Group 22: agent_workflows/agent_schema.py [probe then restore] (1 keys: validate_agent_record)
- Group 23: agent_workflows/artifact_rename.py [investigate probe] (1 keys: _existing_type_id6s)
- Group 24: agent_workflows/attention.py [restore behavioral coverage] (1 keys: _gate_ref_display)
- Group 25: agent_workflows/backlog.py [probe then restore] (1 keys: run_new)
- Group 26: agent_workflows/benchmark_ablations.py [investigate probe] (1 keys: AblationTrialSpec.cell_key)
- Group 27: agent_workflows/benchmark_manifest.py [restore behavioral coverage] (1 keys: BenchmarkManifest.to_dict)
- Group 28: agent_workflows/benchmark_metrics.py [investigate probe] (1 keys: MetricSummary.to_dict)
- Group 29: agent_workflows/benchmark_thresholds.py [investigate probe] (1 keys: GateEvaluationResult.to_dict)
- Group 30: agent_workflows/check_engine.py [investigate probe] (1 keys: _review_index)
- Group 31: agent_workflows/check_engine.py [restore behavioral coverage] (1 keys: check_push_authorization)
- Group 32: agent_workflows/cli.py [probe then restore] (1 keys: _dispatch)
- Group 33: agent_workflows/comms.py [restore behavioral coverage] (1 keys: validate_envelope_header)
- Group 34: agent_workflows/doctor.py [probe then restore] (1 keys: _infer_artifact_type)
- Group 35: agent_workflows/engine.py [probe then restore] (1 keys: resolve_source_root)
- Group 36: agent_workflows/engine.py [restore behavioral coverage] (1 keys: migrate_local_lanes_to_untracked)
- Group 37: agent_workflows/ipd_lifecycle.py [restore behavioral coverage] (1 keys: classify_commit_refusal)
- Group 38: agent_workflows/leak_sanitizer.py [probe then restore] (1 keys: scan_text)
- Group 39: agent_workflows/plan_readiness.py [restore behavioral coverage] (1 keys: cite_review_entry)
- Group 40: agent_workflows/project_context.py [probe then restore] (1 keys: _resolve_effective_aw_home)
- Group 41: agent_workflows/render_stream.py [probe then restore] (1 keys: format_spec_impact_announcement)
- Group 42: agent_workflows/renderers.py [probe then restore] (1 keys: BaseRenderer.emit)
- Group 43: agent_workflows/research_cmd.py [probe then restore] (1 keys: build_frontmatter)
- Group 44: agent_workflows/research_contract.py [probe then restore] (1 keys: validate_frontmatter)
- Group 45: agent_workflows/run_analytics_privacy.py [restore behavioral coverage] (1 keys: _project_number_map)
- Group 46: agent_workflows/run_analytics_telemetry.py [investigate probe] (1 keys: TelemetryCollector._observe_tool_versions)
- Group 47: agent_workflows/run_ledger_schema.py [probe then restore] (1 keys: validate_record)
- Group 48: agent_workflows/runner_shared.py [restore behavioral coverage] (1 keys: attributed_away_failure_ids)
- Group 49: agent_workflows/selectors.py [probe then restore] (1 keys: resolve_for_mutation)
- Group 50: agent_workflows/storage.py [investigate probe] (1 keys: get_git_common_dir)
- Group 51: agent_workflows/verify_roles.py [probe then restore] (1 keys: check_role_action)
- Group 52: agent_workflows/worktree_lease.py [probe then restore] (1 keys: lane_id_from_branch)

Deleted test files to mine: the queue's control files plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: per-group remedy shapes (probe then restore, restore behavioral coverage, investigate probe).
Carried from lrnh5f via plan b83dpg.
