# Review findings: plan 2t9l37

- Subject-Id: 2t9l37
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `6aa8c3441`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize` both reported `clean`. `- Kind: child`.

Re-measured with the lane package (`PYTHONPATH=.`, `AW_NO_REEXEC=1`). The fallback chain is present in `doctor.inspect_repo` (`agent_workflows/doctor.py:2229-2231`), and `git blame` attributes it to `64ccf6758`, which removed `severity="error"`. The `_RUN_DOCTOR_CODE` seam works: four drifts give `info, warning, info, error`, and an info-only list gives `clean`/0. `check_engine.rule_spec`: `doctor.dangling-doc-reference` is `info`, unregistered rules are `error`. `tests/test_doctor_diagnostic_severity.py` does not exist.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (test feasibility) | `agent_workflows/result_types.py:463-474` `CommandResult.to_agent_record` compact branch `{"location": ..., "rule": d.rule}`; review run: bare `aw doctor --agent` diagnostics carry no `severity` key | E-04 asserted severities on bare `aw doctor --agent`, which emits none. The test as written fails, or passes vacuously if it iterates `.get("severity")` loosely. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now drives `--agent --verbose` and `--json`, both measured to carry severity. |
| PR-002 | MEDIUM | IN-SCOPE | D/E (regression power) | `check_engine.rule_spec('doctor.git-untracked').severity == 'error'`; E-04 relied on the untracked drift | E-04's only fixture drifts resolve to `error`, so the test could not tell the fix from the regression it exists to catch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now adds an `AGENTS.md` managed-block dangling reference, so `doctor.dangling-doc-reference` reaches the CLI as `info`, measured on both surfaces. Added F-04. |
| PR-003 | MEDIUM | UNDER-SCOPE | E (verification strength) | V-02 and V-04 demanded only passing output | Nothing proved the tests would go red on the regression. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now requires a mutation run (hardcode `severity="error"`, show E-02 and E-04 red, restore, empty diff). V-04 cites it. Added F-05 recording the seam probe. |
| PR-004 | LOW | IN-SCOPE | G (execution contract) | Approval gate lacked the scope-fence declaration, the paste-actual-output rule, and conditional finalize ownership; OQ-01 `Owner: none` | The gate was incomplete per plan-review Step 4. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate (scope declaration with `--scope-ack` for an unmodified `doctor.py`, the honesty rule, runner versus hand finalize, backlog close by the runner). Set `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should compact `--agent` diagnostics also carry severity so the bare surface is testable? | No; test `--agent --verbose` and `--json`. | Extend the compact record (a public output-contract change outside the backlog item). | `docs/cli-output-contract.md:308` "minimal diagnostic fields" and `:312` "`--verbose` in agent mode includes full nested diagnostics"; backlog `wxpytg` asks only that the real severity be preserved. | yes |
