# Review findings: plan d2vfp2

- Subject-Id: d2vfp2
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `90330c5b2`. The plan was already committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 6), test-only.

Verified in the lane (scratch files under the gitignored `.aw/state/`, deleted; production mutations reverted; `git status` clean apart from the plan and this record, `git diff agent_workflows/` empty):
- `19313eed^:tests/test_run_analytics_submit.py` exists; every test the plan names exists there, the `# --- E-01: the two leaves` section begins after `test_no_network_call_happens_while_building_a_bundle`, and both source-grep tests import `tests.test_run_analytics_export._code_lines`. `tests/test_run_analytics_submit.py` does not exist at HEAD; only `tests/test_core_module_coverage.py` imports the module.
- Trimmed subset (CLI section and the three E-02 tests removed) with `--cov`: `36 passed in 0.67s`, `177 stmts, 11 miss, 94%`, missing `114, 117, 119, 168, 202, 230-231, 334, 369, 499-500`, matching F-04. (F-03's "37" was measured with the bundle-building test still present; E-02 drops it too.)
- Every E-03 (a)..(h) value re-measured by direct call at HEAD and matched exactly.
- `b1mx2w` carries 14 `run_analytics_submit.py::` rows with `unguarded-unreached`, matching F-01.
- Mutation: retry once after a `SubmitRefusal` in `submit_bundle` -> `2 failed` (both no-retry tests). Second `open_url` call after a successful send -> `1 failed, 38 passed`, the one failure being the missing-helper import in a test E-02 removes, so the success-path double send SURVIVES the kept tests.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|----------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D. Anti-regression (no-retry invariant) | `run_analytics_submit.submit_bundle` (the `open_url(` call in its final `try`); review mutation `1 failed, 38 passed` | The Goal claims a no-retry weakening turns a test red, but the kept tests count opener calls only on the two failure paths; a duplicate transmission after a successful send survives. That is a privacy-relevant duplicate disclosure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-03 (i) (one opener call on a successful attested submit), F-06, a success-path mutation in Required tests and V-03; split the ambiguous "call `open_url` twice" mutation into the failure-retry (V-02) and success double-send (V-03) forms. |
| PR-002 | MEDIUM | IN-SCOPE | G. Executability (stop directive) | E-01 "STOP on that test"; E-03 "apply the same STOP rule" | STOP plus an out-of-scope `bug` filing with no justification route, the same defect fixed in siblings `9gjvrq`/`438gkf`. | all Low | FIXED | Replaced with the Set's disposition rule (cite and adjust, or gated `bug` + `xfail(strict=True)` + `--scope-reason`, continue). |
| PR-003 | LOW | IN-SCOPE | E. Validation (evidence hygiene and cross-reference) | Required tests "Reach" command; V-01 `git status --short`; E-03 Expected outcome "explained in V-02" | A default `--cov` run writes an untracked `.coverage` at the repo root (observed at review), which would contradict V-01's "only the test file added"; E-03 pointed its leftover-line explanation at V-02 instead of V-03. | all Low | FIXED | Reach uses `COVERAGE_FILE=.aw/state/d2vfp2.coverage` and deletes it; V-01/V-03 demand a clean status; reference corrected to V-03. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the honesty rule, the staged-set check, the scope-fence wording, and conditional finalize ownership. | all Low | FIXED | Gate rewritten as an execution contract matching the Set's siblings. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a success-path duplicate send be guarded by this plan? | Yes, one new E-03 test with a counting stub opener | Leave no-retry guarded only on failure paths | Goal line "the no-retry rule"; review mutation result | yes |
| D-2 | Which failure disposition replaces STOP? | The Set's cite-or-xfail-and-file rule | Keep STOP | Sibling `9gjvrq` RESTORE RULE and its review PR-004 | yes |
