# Review findings: plan bli2ba

- Subject-Id: bli2ba
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `72da75876`. The plan was byte-identical to the lane input and already committed at `a0a5e4ba0` (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 35), test-only verify-first plan.

Verified at the lane HEAD:
- F-01: `git log -1 cbf70e39a` is `work(8bhcd3): Restore behavioral test coverage for run_analytics_telemetry` (2026-10-17 19:34:52); `git merge-base --is-ancestor cbf70e39a f3afece925` exits 1. `wo21z5` findings doc carries `head: f3afece925...`, the eight Probe-queue rows with control `tests/test_run_analytics_telemetry.py` and `P2`, and "budget exhausted at 11130.81s". Backlog `zd8l04` lists exactly the eight keys and operators the plan names.
- All eight symbols exist in `agent_workflows/run_analytics_telemetry.py` (`ResourceSampler.__init__/start/stop`, `SystemResourceProbeAdapter.disk/accelerators`, `TelemetryCollector.__init__/_emit/_observe_accelerators`); all five test classes E-02 names exist; module carries `pytestmark = pytest.mark.core`; F-03's two test names exist in `ProbeAdapterTests`; `19313eed` resolves.
- Re-ran three probes (`disk`, `_emit`, `ResourceSampler.stop`): all `verdict: killed`, `baseline_failing: 0`, counts match F-02 (recorded as plan F-04).
- Ran bare `python3 -m pytest`: `1675 passed, 11 warnings in 34.61s`, exit 1 from an ENFORCED `CORE TIER BUDGET EXCEEDED` block (12 CPUs, load 5.88) (recorded as plan F-05).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Validation (satisfiable bar) | `conftest.py:228` `not_enforced_reason` / `conftest.py:254` `session.exitstatus = 1`; review bare run exit 1 with 1675 passed | E-03 expected "the bare run exits 0" and V-03 demanded the exit status, but on this 12-CPU host the 30s budget is enforced and already overrun (34.61s) before this plan, so the bar was unsatisfiable for an out-of-scope reason; the plan's own prose assumed the overrun only warns. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/V-03 accept exit 1 only when it is caused solely by an enforced budget block listing no E-02-added test; any other non-zero exit fails. Required-tests bullet aligned. F-05 records the measurement. |
| PR-002 | LOW | IN-SCOPE | Clarity (Findings) | plan F-02 row, "`TelemetryCollector.__init__` 30 (`raise`)" inside the return-none run | F-02 grouped `TelemetryCollector.__init__` (operator `raise`) between return-none keys, misreading as mixed operators. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 regrouped by operator. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does a pre-existing, enforced core-tier wall-time overrun fail this plan? | No; exit 1 is acceptable only when solely caused by the enforced budget block with no E-02-added test among the slowest | Keep exit-0 bar (unsatisfiable on this host); set `AW_CORE_BUDGET_ENFORCE=0` (hides the signal) | `conftest.pytest_sessionfinish`; plan F-05; sibling `qpmq2o` review D-1 | yes |
| D-2 | Keep the plan verification-first rather than restoring tests now? | Keep; conditional E-02 only | Restore redundant tests from `19313eed^` (duplicates `8bhcd3`) | plan OQ-01; F-04 re-probe killed | yes |
