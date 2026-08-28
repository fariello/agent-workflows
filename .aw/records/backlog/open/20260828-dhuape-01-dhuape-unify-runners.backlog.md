- Id: dhuape
- Status: open
- Blocks-Release: next
- Set: dhuape
- Priority: medium
- Kind: chore
- Summary: Unify aw oc run and aw agy run onto a shared tool-agnostic runner library

## Workflow history
- 2026-08-28 open (aw set): gate 2.0.0 on unifying the two runners
- 2026-08-28 created (aw backlog): Unify aw oc run and aw agy run onto a shared tool-agnostic runner library

PROBLEM. agent_workflows/oc_runipd.py (2279 lines) and agent_workflows/agy_runipd.py (2363 lines) are near-duplicate host runners that have DIVERGED. A raw diff shows ~954 changed lines, and neither imports any shared runner library - despite host_adapters.py / host_launchers.py / host_capability_registry.py existing (a host-abstraction layer the runners currently bypass). Recent work went into the OPENCODE runner (oc_runipd) and NOT the agy runner, so oc_runipd has finalize/lifecycle features the agy runner lacks.

GOAL. All logic NOT specific to the underlying tool (opencode vs agy) must live in ONE common library both runners import. Each tool-specific runner shrinks to just the tool-specific surface (launch/talk to that CLI, parse its event stream, resolve its binary).

CONCRETE DIVERGENCE (def-name comm, snapshot 20260828 - re-verify at plan time):
- In oc_runipd, MISSING from agy_runipd: action_for, finalize_orchestrator, _read_kind, _set_children_all_executed, run_opencode. These are the self-finalize / orchestrator-lifecycle features built recently - the agy runner never got them. Exactly the present-in-one-not-the-other gap called out.
- In agy_runipd, not in oc_runipd: render_agy_event, resolve_agy, run_agy_turn, _one_line, _strip_ansi, and an event-formatter class (format_idle/format_message/status). Some are genuinely agy-specific (event rendering, binary resolution); others (_strip_ansi, _one_line) may be generic and belong in the shared lib.

REQUIRED WORK.
1. Function-by-function inventory of both runners: classify each as (a) common, (b) tool-specific, or (c) present in one but missing in the other (a divergence bug). This inventory is a deliverable answering which functions/outputs exist in one and not the other.
2. Extract the common set into a shared module (candidate: runipd_core / host_runner, or fold into existing host_adapters/host_launchers - decide at plan time).
3. Reconcile divergences: where oc has a feature agy lacks (orchestrator self-finalize) or vice versa, decide common-vs-tool-specific and bring runners to parity on the common surface. Outputs/event rendering that should be uniform must be unified.
4. Both runners end up thin adapters over shared lib + tool-specific bits.

CONSTRAINTS.
- Do NOT regress oc_runipd behavior just landed (action_for/finalize_orchestrator/_read_kind/_set_children_all_executed and the orchestrators-not-agent-executed fix).
- Interacts with the driverfin plan (self-finalize + worktree isolation) and spec 25kzda (aw-run deterministic) - coordinate so driverfin fixes land ONCE in the shared lib, not twice.
- Full runner suites (test_oc_runipd + agy runner tests) must pass; add tests for the shared lib.

Blocking (Blocks-Release: next set separately): shipping 2.0.0 with two divergent runner copies (one missing the other's finalize/lifecycle features) is a maintenance + correctness liability.
