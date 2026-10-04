# Review findings: plan 5etev3

- Subject-Id: 5etev3
- Subject-Type: ipd
- Reviewed-At: 2026-10-04
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261004T134544Z-4052083` at HEAD `b1ff0278e`. The plan was
committed and byte-identical to the sealed lane input (rev-5, sha256 `d43792bd...`); no snapshot needed. `- Kind: child`,
so `IPD-S407` does not apply. `aw ipd lint --phase author` clean before; `review-finalize` clean after.

Re-measured in `agent_workflows/runner_shared.py`: `queued_orchestrator_targets` (filters only `kind`),
`enforce_orchestrator_probe_gate(run_dir, state, *, repo, host, ..., retry_budget, asker, runner)` and its
`labels = AGY_HOST_LABELS if host == "agy" else OC_HOST_LABELS`; `probe_argv` `if host == "agy"`;
`dispatch_orchestrator_item` (no `host` parameter; RETIRE branch calls `_lifecycle.retire_orchestrator`; terminate tail
calls `record_refusal` and appends `orchestrator-deferred`); `ORCH_REASON_FINALIZE_REFUSED` remedy text ("retire the
orchestrator through `aw ipd finalize`"); `frozen_retry_budget`; `resolve_cli_host`; `state["host_capabilities"]["host"]`;
the `--full-auto` bridge `item["action"] = "execute"`; queue-build `status = "auto-approved"` before `action_for`.
Host loops: `oc_runipd.run_queue` and `agy_runipd.run_queue` both call `dispatch_orchestrator_item` under
`if runnable.get("action") == "orchestrate":` passing no host. Measured: `action_for('orchestrator', s)` for five
statuses; `resolve_cli_host` returns `opencode`/`antigravity`; `ask_orchestrator_probe` under `PYTEST_CURRENT_TEST`
raises `DriverError`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness | `runner_shared.probe_argv` `if host == "agy"`; `resolve_cli_host` returns `antigravity`/`opencode`; `oc_runipd.run_queue` / `agy_runipd.run_queue` `dispatch_orchestrator_item(` calls pass no host | E-03's "read it from `state`" would yield `antigravity`, which `probe_argv` treats as opencode, so an agy run's re-check would spawn the wrong binary. E-03 also claimed host modules may need no change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds a keyword `host` passed as `"oc"`/`"agy"` from each loop with a mapped fallback; host modules added to Scope-Paths; E-04 case (h); V-03 rewritten. |
| PR-002 | HIGH | UNDER-SCOPE | D anti-regression | `tests/test_orchestrator_retirement.py` `test_reconsidered_then_retired_in_the_same_run_on_both_hosts` patches only `retire_orchestrator`; `_assert_probe_spawn_is_permitted` | After E-02 every existing test reaching RETIRE asks the probe first and raises under pytest; that file was not in scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 requires seeding a pass verdict in those tests without changing assertions; file added to Scope-Paths; V-04 lists touched tests. |
| PR-003 | MEDIUM | IN-SCOPE | E/UX | `dispatch_orchestrator_item` terminate tail already calls `record_refusal`; `ORCH_REASON_FINALIZE_REFUSED` remedy "retire ... through `aw ipd finalize`" | E-02 asked for a second `record_refusal`, and the inherited remedy would tell the operator to finalize by hand, wrong for an uncovered-work refusal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Refusal flows through the existing tail; the detail carries the Order 03 shared remedy per finding; status follows existing `finalize-refused` behavior. |
| PR-004 | MEDIUM | IN-SCOPE | C operability | `probe_orchestrator(..., retry_budget, ...)` is required; `frozen_retry_budget(state)` | E-02 named no retry budget for the retirement-time ask. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 passes `frozen_retry_budget(state)`. |
| PR-005 | LOW | IN-SCOPE | A soundness | `execute_item_core` `item["action"] = "execute"` after `set_plan_approved`; queue build `status = "auto-approved"` before `action_for` | The frozen-action filter's soundness under `--full-auto` was unstated; empty-target behavior unspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records why no item becomes `orchestrate` mid-run and specifies the empty-target event. |
| PR-006 | LOW | IN-SCOPE | E/G | E-04 cases; gate | No could-not-ask case at retirement, no second mutation for E-02, no pinning-test citation; gate lacked scope fence and paste-actual-output rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cases (g), (h) and a second mutation added; citation added; gate contract completed; required test list widened. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does `dispatch_orchestrator_item` learn the host? | Keyword `host` passed by each loop, fallback mapping from `host_capabilities.host` | read state only (needs a mapping anyway, implicit); new state field (more surface) | `probe_argv`; `resolve_cli_host` measured | yes |
| D-2 | Status of a retirement refused by the re-check? | Existing `finalize-refused` terminate path, plan left in `pending/` | new non-failing status (unspecified, touches renderers) | every other retirement refusal uses it; spec 2.5d says plan stays in `pending/` | yes |
| D-3 | Fix existing retirement tests how? | Seed a pass verdict in their setup | patch `review_readiness` (hides the new call from those tests) | `record_probe_verdict` exists; tests keep their assertions | yes |
