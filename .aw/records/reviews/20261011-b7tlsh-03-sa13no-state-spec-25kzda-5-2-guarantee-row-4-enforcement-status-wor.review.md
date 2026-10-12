# Review findings: plan sa13no

- Subject-Id: sa13no
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `8520463e4`. The pending plan matched the sealed lane input (sha256 `18336aaa...`) and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` reported `clean`. `- Kind: child`, so `IPD-S407`/`IPD-S408` do not apply.

Re-derived every E-01 measurement: `isolated_worktree True False False`, `path_policy True False False`, `timeout_cancel True False False`; execute `unrepresented` contains all three; `resolve_isolation(Namespace(), <tmp>)` -> `{'execute': True, 'review': True}`, with `isolate_worktree=False` -> both False; with `{"run": {"isolate_worktree": false}}` written to the tmp dir -> both False plus a warning (V-02 leg B falsification is feasible); `isolation_for_action({}, "execute")` -> True; `MAX_TURN_TIMEOUT` 14400.0; `select_execution_profile("hardened", HostSandboxCapabilities())` raises `HardModeUnavailableError`; `select_execution_profile(None, ...)` -> `default`. The row 4 cell is unamended at spec line 1263 and rows 1-3 carry the shape the plan follows. `GuaranteeRowEnforcementStatusTests` exists and `argparse`/`dataclasses` are already imported. The pinned parser tests pass (`58 passed`). `evaluate_durable_carrier` returns `[]`, `aw check release-gates` conforms, `aw sanitize --agent` is clean. Other pending plans declaring this spec (`o58r3r` edits 5.5 and history; `nrdrv6` does not declare it in Scope-Paths) touch no 5.2 row.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A (honest documentation) | `agent_workflows/oc_runipd.py` comment at the `execution_profile` writer: "an agy run SILENTLY IGNORES a stored request rather than refusing it"; `docs/runner-profiles.md:305` "IT IS OPENCODE ONLY, AND ANTIGRAVITY IGNORES IT RATHER THAN REFUSING" | E-03's target text said the `hardened` profile "refuses rather than degrading" with no host qualifier. On Antigravity the request is silently dropped, so the amendment would write a new overclaim into the row it exists to de-overclaim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-9; E-03 target text now names `hardened` as an OpenCode-only Linux/Landlock boundary and states `aw agy run` runs the request unsandboxed; V-03 clause (v) and the E-04 note message now require it. |
| PR-002 | LOW | IN-SCOPE | G (accuracy) | Spec `25kzda` `## Workflow history` is newest-first (line 1720 is the 2026-10-11 entry) | E-04/V-04 said "appended" history line; `aw specs note` inserts at the top. An executor diffing for an appended line would look in the wrong place. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and V-04 now say one new/added line. |
| PR-003 | LOW | IN-SCOPE | Project rule (OQ owner) | Plan OQ-01/OQ-02 `- Owner: none`; plan-review Step 3.1 rule 5 | Both questions were resolved by the plan author but recorded `Owner: none`, which hides who decided. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both now read `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the agy silent-ignore of `hardened` be fixed in code here instead of documented in the cell? | Document only; this plan stays records-only. | Make agy refuse a `hardened` request. | Plan Scope OUT "every production module"; `oc_runipd` comment "Making agy refuse is a change to that host and is deliberately not smuggled in here". | yes |
