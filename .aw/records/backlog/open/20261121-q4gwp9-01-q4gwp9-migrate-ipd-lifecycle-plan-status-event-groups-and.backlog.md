- Id: q4gwp9
- Status: open
- Set: q4gwp9
- Work-Kind: followup
- Priority: medium
- Summary: Migrate ipd_lifecycle._plan_status_event_groups and HISTORY_RECORD_RE callers before Order 11 tdhav3 deletes HISTORY_RECORD_RE
- Short-Description: Migrate ipd_lifecycle._plan_status_event_groups and HISTORY_RECORD_RE callers before Order 11 tdhav3 deletes HISTORY_RECORD_RE

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): Migrate ipd_lifecycle._plan_status_event_groups and HISTORY_RECORD_RE callers before Order 11 tdhav3 deletes HISTORY_RECORD_RE

During the residual audit in plan h58z9n (E-05), two gaps in Order 11 cleanup appeared. First, agent_workflows/ipd_lifecycle.py::_plan_status_event_groups (called by agent_workflows/check_engine.py::check_lifecycle_transitions and check_lifecycle_transition_coverage) directly parses the inline '## Workflow history' heading and imports attention_contract.HISTORY_RECORD_RE, and no plan in Set metastore moves those working-tree lifecycle-transition checks onto artifact_meta.history before 9o83cr E-14 audits 'Workflow history' across agent_workflows/. Second, Order 11 plan tdhav3 (Order 248, E-02) deletes attention_contract.HISTORY_RECORD_RE, while five active callers outside tdhav3 Scope-Paths still import or reference it: agent_workflows/ipd_lifecycle.py, agent_workflows/plan_readiness.py, agent_workflows/record_history.py, agent_workflows/specs.py, and agent_workflows/migrations/m0001_convert.py. Update the Order 11 plan set so every remaining HISTORY_RECORD_RE caller and _plan_status_event_groups is migrated or retargeted before tdhav3 deletes HISTORY_RECORD_RE and 9o83cr E-14 runs its AC-1 audit.
