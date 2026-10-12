# Review findings: plan a8yn86

- Subject-Id: a8yn86
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `d9aa65367`. The pending plan matched the sealed lane input byte for byte and was already committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` reported `clean`. `- Kind: child`.

Claims checked against the code: `runner_shared.ensure_frozen_host_capabilities` (`agent_workflows/runner_shared.py:30800`) returns the frozen descriptor, and when that is absent it probes once and freezes the result. `runner_shared.execute_item_core` preflight (`:35039-35077`) appends `host_capability_unavailable` with disposition `fail-gate` and records `SKIP_HOST_CAPABILITY_UNAVAILABLE` (`run_selection_policy.py:1369`). `ACTION_EXECUTE` requires `CAP_FRESH_VERIFIER_SESSION` (`host_sandbox_profile.py:2128-2130`). The `_oc.run_opencode(` sentinel inside `_capture_turn_argv` (`host_sandbox_profile.py:1261`) confirms F-3. `rg assert_distinct_sessions tests/` matches only the target file. The last commit touching the file is `163874fcc work(psgyzw)`.

The E-01/E-02 shape was prototyped in a gitignored scratch copy, which was then deleted. The mutated case passes every E-02 assertion. The unmutated control also ends `fail-gate`, from a later lifecycle gate, with `verification_status == verified`.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | D/E (test discrimination) | Review prototype: `CONTROL fail-gate verified ['executor', 'verifier'] True`; attempt `turn_retry_skipped` "lifecycle gate or clean-base gate refused" | In this fixture the unmutated control ALSO ends `item["status"] == "fail-gate"`, so `status` does not separate the mutated run from the control. An executor who added a natural `status != "fail-gate"` control assertion would get a red test, and one who leaned on `status` alone would get a test that cannot tell the two runs apart. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now names the discriminators (the `host_capability_unavailable` attempt key, the refusal code, and the spawn list) and forbids a status assertion in the control. Added F-7 with the measured outputs. |
| PR-002 | LOW | IN-SCOPE | G (execution contract) | Plan `## Approval and execution gate` (pre-review text) | The gate had no scope declaration with `--scope-reason`/`--scope-ack` and no conditional finalize ownership (runner versus hand). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate to add the scope declaration, the honesty rule, path-scoped commit with never-push, and runner-owned versus hand finalize. |
| PR-003 | LOW | IN-SCOPE | G (coordination / honesty) | E-01 comment instruction; sibling `jo55oo` E-01 adds a comment on the same `host_capabilities` key; OQ-01 `Owner: none` | Both plans add a comment to the same line, and if both land they would duplicate it. OQ-01 was resolved by the author but recorded no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now says to extend the existing comment if `jo55oo` landed first. OQ-01 now reads `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the unfrozen control be dropped or marked slow given its runtime? | Keep it in the fast suite. | Mark it `slow`, or drop the control. | Review `--durations`: control 21.97s versus the existing frozen test at 25.35s; an unfrozen `detect_host_capabilities('opencode')` costs 0.81s. The unfrozen path adds no material cost, and the control is what proves the refusal is caused by the mutation. | yes |
| D-2 | Should OQ-01 (keep the frozen descriptor by default) be reopened? | No; keep it resolved. | Remove the frozen descriptor fixture-wide. | `runner_shared.py:30800` `ensure_frozen_host_capabilities` docstring (bqtgmo: read the frozen descriptor rather than re-probing per item). | yes |
