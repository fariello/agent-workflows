# Review findings: plan 4bw2u5

- Subject-Id: 4bw2u5
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e1e49e8ac`. The plan was committed and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. The plan is a child, not an orchestrator.

Verified:
- `release_readiness.GateResult` has fields `name, passed, detail, evidence`; `failing_gates` is `not g.passed`; `verdict` is `all(g.passed)` (F-02 holds).
- Only `agent_workflows/cli.py` (dispatch) uses the module in production (F-05 holds); `tests/test_host_capability_registry.py` also calls `gate_capability_freshness` on this repo's shipped matrix, which stays present.
- Targeted readiness suites: `82 passed in 16.48s` (F-06 holds).
- This repo: `aw releases readiness --suite-passed --residual-risk-signer qa --json` gives all 11 gates passing, `generated_drift True | no canonical workflow packages to check` (F-03 holds).
- `_setup_full_go_tree` minus `docs/`, `CHANGELOG.md`, `host_matrix.json`: `docs_checks`, `capability_freshness`, `changelog_versioning` FAIL, `generated_drift` vacuous PASS; removing `index.md` gives `workflow_disposition` "could not run: FileNotFoundError" (F-04 holds).
- `versioning.resolve_version` on a `git init` tree with no commits and `.aw/system/VERSION=1.0.0` returns `1.0.0`, so item 9's git-initialised tree resolves the version.
- No spec names the gates (`git grep` over `.aw/records/specs/` empty).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric D (regression set) | `tests/test_releases_readiness_cli.py:100` `assert proc.stderr == ""`; `:245` `rec_go["findings"] == 0`; `:223` `rec["findings"] == 2`; `tests/test_release_readiness_producers.py:620` `gate_generated_drift(repo_root=tmp_path).passed is True`; `_setup_full_go_tree` has zero `workflow.yaml` | E-06's known set missed the GO-tree tests: every shared GO fixture now carries `generated_drift` not-applicable, so the stderr WARNING and the extra warning diagnostic break three more tests. An executor following the "change ONLY absent-input tests" rule could misclassify these as regressions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-07 and named the three tests in E-06 with their new assertions; forbade adding a compiled package to the shared fixture (`yaml` dependency). V-06 updated. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric E (unsatisfiable evidence) | `result_types.CommandResult.to_agent_record` non-verbose diagnostics are `{location, rule}` only (probe) | E-02 item 9 asserted `severity: "warning"` per diagnostic in `--agent` output, which the default record does not emit. | all Low | FIXED | Item 9 now asserts the rule set, `outcome == "clean"`, and `findings_by_severity == {error: 0, warning: 4, info: 0}` (or `--verbose`). V-05 aligned. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric A (diagnostic parity) | `release_readiness.run_readiness` diagnostics filter `if not g.passed` | NA gates carry `passed=False`, so the existing filter would emit an `error` diagnostic for each NA gate beside the new warning. E-05 did not say to change the filter. | all Low | FIXED | E-05 now requires the error filter to iterate `report.failing_gates()` (applicable and failed). |
| PR-004 | MEDIUM | UNDER-SCOPE | Rubric G (cross-plan contract) | kmmoca E-01(e) and test 8 tree has no `index.md`; `gate_artifact_manifest` fails on missing `index.md` (Scope OUT here) | kmmoca expects `authorize_release` to succeed on a managed-style tree without `index.md`; after this plan that tree is still `NO-GO` via `artifact_manifest`. | all Low | FIXED | E-04 states the interaction; `## Deferred` records the cross-reference with Carrier `kmmoca` (owning plan edits its own tree). |
| PR-005 | LOW | UNDER-SCOPE | Rubric E (baseline) | E-08(6) "compared by name against the execution-base baseline"; no E-item captured it | No step records the pre-edit bare-suite baseline. | all Low | FIXED | E-01(e) and V-01(e) capture it before any edit. |
| PR-006 | LOW | IN-SCOPE | Rubric F (silent/garbled output) | `ReleaseReadinessReport.render` `"empty gate set (no gates evaluated)"`; `run_readiness` `f"Verdict: NO-GO ({', '.join(failing)})"` | An all-NA report is NO-GO with an empty failing list, rendering a misleading "empty gate set" line and `NO-GO ()`; E-04 also did not say NA results keep existing empty evidence keys. | all Low | FIXED | E-03 specifies the all-NA wording; E-04 requires existing evidence keys be kept. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the shared GO fixture gain a compiled workflow package so GO tests stay NA-free? | No; update the three GO-tree tests to expect `generated_drift` not-applicable. | Add a compiled package to `_setup_full_go_tree` (REJECTED: drags `yaml` into every readiness test, which the drift tests `importorskip`). | `tests/test_release_readiness_producers.py` drift arms call `pytest.importorskip("yaml")`. | yes |
| D-2 | Who fixes kmmoca's managed-style tree lacking `index.md`? | kmmoca (cross-reference recorded here). | Make `artifact_manifest` not-applicable here (REJECTED: plan Scope OUT and maintainer ruling names only five inputs). | Plan Scope OUT; plan-review Step 2.4 "fix it in the owning plan and cross-reference". | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
