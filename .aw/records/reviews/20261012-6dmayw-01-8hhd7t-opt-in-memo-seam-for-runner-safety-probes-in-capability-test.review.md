# Review findings: plan 8hhd7t

- Subject-Id: 8hhd7t
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `4e9e7c69e`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize` both reported `clean`. `- Kind: child`.

Evidence verified: `probe_runner_safety_capabilities` (`agent_workflows/host_sandbox_profile.py:1126`) runs every non-`None` `_RUNNER_SAFETY_PROBES` entry (`:1084`) per call, with the `_FORCED_RUNNER_SAFETY` branch first (`:1141-1147`) and the "Deliberately NOT cached" docstring (`:1129`). `forced_runner_safety_verdicts` (`:1102`) restores in `__exit__`. `detect_host_capabilities` calls the prober only when `plat == running_platform` (`:1606-1610`). `tests/test_runner_safety_probe_memo.py` does not exist. The plan's call-count baseline reproduced exactly (`SAFETY_PROBE calls=67`, 113 passed).

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (verification feasibility) | `agent_workflows/host_sandbox_profile.py:1126` `probe_runner_safety_capabilities`; E-02 places the memo INSIDE it; review run `SAFETY_PROBE calls=67` | E-01/E-05/V-01/V-05 measured calls to `probe_runner_safety_capabilities`. The memo lives inside that function, so the call count is identical before and after, and V-05's "lower `calls=`" demand is unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/E-05/V-01/V-05 now count EXECUTIONS of the wrapped `_RUNNER_SAFETY_PROBES` callables. The plugin is embedded in "Required tests / validation" and was run at review: `PROBE_EXEC executions=198 total=9.81s`, `113 passed`. Added F-06. |
| PR-002 | MEDIUM | IN-SCOPE | C/G (design effectiveness) | Review per-class breakdown: `CheckerTests`, `FailClosedPreflightTests`, `DenyPushRemovedTests`, `CommitGatewayClaimConsistencyTests` each 1 call in 1 test; `CapabilityProbeTests` 3 calls in 3 tests | E-04 allowed `setUp`/`addCleanup`, a per-test scope. Most consumer classes call the prober about once per test, so a per-test memo saves almost nothing and E-05's "materially below" bar could fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires class scope (`setUpClass` plus `cls.addClassCleanup`), which restores even when `setUpClass` or a test fails. V-04 demands the per-class breakdown at no more than one execution per probe. |
| PR-003 | MEDIUM | UNDER-SCOPE | G (scope completeness) | `tests/test_host_sandbox_profile.py` `AdversarialOsDenialTests`, `DiscoveryThenExecutionTests`, `ProbeMustProveDenialTests` each call `detect_host_capabilities("opencode")`; review breakdown 6/3/3 executions | The Scope check claimed every consumer was listed, but three consumer classes were missing. "The `ThirdHost*` classes" was also imprecise, because only two of the four reach the prober. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the three classes and named `ThirdHostCapabilitiesTests` and `ThirdHostInitializationAndLimitTests`. E-04 now re-derives the list from the E-01 breakdown at execution time. Added F-07. |
| PR-004 | LOW | IN-SCOPE | C (canonical mechanism) | `agent_workflows/host_sandbox_profile.py:192-193` `__all__` lists `probe_runner_safety_capabilities`, `forced_runner_safety_verdicts` | E-02 did not export the new context manager, unlike its sibling seam. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and V-02 now include the `__all__` entry. |
| PR-005 | LOW | IN-SCOPE | G (execution contract) | Approval gate lacked the scope-fence declaration, the paste-actual-output rule, conditional finalize ownership, and a no-commit rule for the measurement plugin; OQ-01 `Owner: none` | The gate was incomplete per plan-review Step 4. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate (scope declaration with `--scope-reason`/`--scope-ack`, plugin never committed, honesty rule, runner versus hand finalize, backlog close by the runner). Set `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What should E-01/E-05 measure? | Executions of the `_RUNNER_SAFETY_PROBES` callables, via a plugin that wraps each entry once at import. | Calls to `probe_runner_safety_capabilities` (unchanged by an internal memo); timing only (noisy; review timings ranged 9.81s to 33.59s under load). | `agent_workflows/host_sandbox_profile.py:1148-1156`; review runs of both plugins. Wrapped callables stay stable, so they remain valid memo keys and survive the tests' save/restore of `_RUNNER_SAFETY_PROBES`. | yes |
| D-2 | Per-test or per-class memo scope? | Per-class (`setUpClass` plus `addClassCleanup`). | Per-test `setUp` (little saving); module-wide fixture (already rejected in the plan's Deferred section). | Review per-class breakdown; `unittest.TestCase.addClassCleanup` exists on the 3.9 floor (`pyproject.toml:12`). | yes |
| D-3 | Do the sandbox-ladder classes and `HostCapGateDescriptorFreezeTests` lose coverage by sharing verdicts? | No; opt them in. | Exclude them. | None of them patches a runner-safety probe input (grep of `_RUNNER_SAFETY_PROBES`, `_FORCED_RUNNER_SAFETY`, `_deny_tcp_probe_allowed_ports`, `_EGRESS_PROBE_NS_ARGV`, `_landlock_abi` in those classes). The freeze test's concurrency property concerns `_capture_turn_argv` Popen interception, which still runs because it clears `_HOST_ARGV_CACHE` per call. | yes |
