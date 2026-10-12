# Review findings: plan wizzis

- Subject-Id: wizzis
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `795862c5d` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `CommandResult.to_agent_record` (`agent_workflows/result_types.py`): `# Findings count` block, then changes,
  evidence, diagnostics, `next`, then `# Field filtering` (`_schema.filter_record_fields`), then
  `_schema.assert_valid_agent_record`.
- `Diagnostic.severity` defaults to `"error"`; `artifact_core.drift_exit_code` gates on `!= "info"`.
- `docs/cli-agent-protocol.md` headings: `## Outcomes and exit codes`, `## Stream truncation is honest`,
  `## Example records`, `## Stability` (additive-optional clause as quoted).
- `docs/cli-output-contract.md` `### Domain Findings Result (exit: 1)` example exists.
- PROBE: E-01 applied in-process via a pytest plugin (no source edit) over the bare suite. Baseline bare
  run on the same HEAD: `39 failed, 7180 passed, 2 skipped` (environment-dependent no-project/explicit-dir
  tests). Patched: `40 failed, 7179 passed, 2 skipped`; the ONLY new failure is
  `tests/test_cli_quality_gates.py::DeterministicByteGoldenTests::test_agent_goldens_stable`
  (`check_findings: agent golden drift`, `...,"findings_by_severity":{"error":2,...}`). Parity, budget,
  projection, and schema-validity gates all passed under the patch.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression | `tests/test_cli_quality_gates.py` `DeterministicByteGoldenTests.test_agent_goldens_stable`; `tests/fixtures/conformance_goldens/check_findings.agent.golden` | The plan omits the committed agent golden the new key changes; executing as written fails the suite with no authorized path to fix it. Measured by in-process probe. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05/V-05 (regenerate via `AW_CONFORMANCE_UPDATE_GOLDENS=1`, prove only that one golden changed by exactly the key) and the golden to Scope-Paths. |
| PR-002 | LOW | IN-SCOPE | C. Architecture | E-01 placement "directly after the `# Findings count` block" | Placement must precede `# Field filtering` and the validator for case (f) to hold; the plan implied but did not state it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 states the ordering requirement. |
| PR-003 | MEDIUM | UNDER-SCOPE | Honest documentation | `docs/cli-agent-protocol.md` `## Example records` "Domain findings"; `docs/cli-output-contract.md` `### Domain Findings Result` | Both docs' findings examples would misdescribe real output once every diagnostics-bearing record carries the key. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/E-04 now update those example records. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing | V-02 "full bare `python3 -m pytest` ... with zero failures" | This lane's bare baseline already carries 39 environment-dependent failures, so an absolute zero-failure bar is unsatisfiable for a correct change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 and Required tests now compare failing ids by name against a same-HEAD baseline. |
| PR-005 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Lacked OQ status, scope-as-declaration, MUST-paste rule, staged-set check, and conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate carries a bulleted execution contract. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Regenerate the agent golden, or emit the key only under `--verbose` to keep goldens stable? | Regenerate the golden | Verbose-only emission (defeats the goal: compact consumers stay blind) | backlog `3ouico` summary; `_read_or_write_golden` regeneration convention | yes |
| D-2 | Additive field vs redefining `findings` (OQ-01)? | Confirm additive | `aw.agent/v2` redefinition | `docs/cli-agent-protocol.md` `## Stability` | yes |
