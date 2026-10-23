# Review findings: plan 3wkrng

- Subject-Id: 3wkrng
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `6d63e108a`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `tests/test_ipd_dependency_check.py` has `import pytest`; `@pytest.mark.core` sits only on
  `EvaluatorRuleMatrixTests.test_every_dependency_shape_produces_its_own_rule`; both named
  `PhasedLintTests` methods exist; last change to the file is `5620a5a13` (`zhoul7`).
- `-m core --collect-only` on the file lists one test (11 deselected).
- `tools/mutation_probe.py --op return-none` over the two `PhasedLintTests` node ids plus the existing core
  test: `lint_file` killed (`mutant_failing: 1`), `check_item_dependencies` killed (`mutant_failing: 2`),
  `baseline_failing: 0` both. Under the current `-m core tests/test_ipd_dependency_check.py`: both survived.
- `grep -c ipd-dependency tests/test_ipd_lint.py` prints `0` (plan F-04 holds).
- Bare `python3 -m pytest` before any change: `1675 passed, 11 warnings in 59.22s`, with
  `CORE TIER BUDGET EXCEEDED` and "Core tier budget not enforced: host oversubscribed".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric E (unsatisfiable validation) | plan E-03/V-03 "no core-budget overrun message"; `conftest.pytest_sessionfinish`; review bare run `59.22s` with `CORE TIER BUDGET EXCEEDED` | The core tier already overruns 30s before this change, so E-03/V-03 as written would fail for reasons unrelated to this plan (or invite the executor to fudge). | all Low | FIXED | E-03/V-03 now require exit 0 with no failures, paste any budget block verbatim, and attribute cost via the module's `--durations=0` output; F-06 records the pre-existing overrun. |
| PR-002 | LOW | IN-SCOPE | Live-artifact criteria convention | plan E-01/V-01 "lists exactly three tests" | A collected-test count was the bar; it would break if another plan core-marks a test in this file first. | all Low | FIXED | Bar is now the before/after `--collect-only` difference being exactly the two `PhasedLintTests` tests. |
| PR-003 | LOW | IN-SCOPE | Rubric E | plan V-02 | The probe's `verdict: killed` was not tied to a clean baseline, and the head check would break if a later evidence commit of the plan lands first; `<E-01 commit>` was never recorded. | all Low | FIXED | E-01 records `<E-01 commit>`; E-02/V-02 require `baseline_failing: 0` and allow a later commit of this plan. |
| PR-004 | LOW | UNDER-SCOPE | Execution contract | plan `## Approval and execution gate` | Gate lacked the paste-actual-output rule, a declarative scope fence, the no-production-change check, and runner versus hand `aw ipd finalize` ownership. | all Low | FIXED | Gate rewritten to the repo's standard contract; V-03 and Required tests add `git diff ... -- agent_workflows/` empty. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should E-03 treat a pre-existing core budget overrun? | Record it with the module's own durations; not a failure of this plan | Keep "no overrun" (unsatisfiable on this host); drop the budget check entirely (loses cost attribution) | review bare run at `6d63e108a`; `conftest.pytest_sessionfinish` | yes |
| D-2 | Are the two decorators sufficient, or must FromSpec test also be core-marked? | The two `PhasedLintTests` only, as planned | Also mark `FromSpecSchemaRecognitionTests.test_from_spec_does_not_raise_unknown_field` | review probe: the two kill both keys with a clean baseline | yes |
