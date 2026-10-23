# Review findings: plan 2qlg0w

- Subject-Id: 2qlg0w
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `623eb73c`. Plan committed and byte-identical to the lane
input (`diff` empty), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after
revisions `--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- All eight E-02 node ids exist at `19313eed^` in the named classes (`git show 19313eed^:<file>`).
- The five `tests.test_ipd_lifecycle_cli` helpers exist (`_init_git`, `_commit_all`, `_ready_plan_text`,
  `_completed_plan_text`, `_write_plan`); `tests/test_engine_restored_behavior.py` carries
  `pytestmark = pytest.mark.core`; target symbols `ipd_lifecycle.begin`, `_baseline_ambiguity`,
  `_execution_cohesive_committed_paths`, `finalize_precheck`, `_run_record_committed_paths` exist.
- The eight tests run from `/tmp` copies: `8 passed in 3.82s` (with the lane's worker-role env unset, which
  the repo `conftest.py` pops anyway).
- The untested `_baseline_ambiguity` swap (plan F-04): probe `verdict: killed`, `mutant_failing: 1`.
- `conftest.pytest_sessionfinish` sets exit 1 on budget overrun only when enforced (>=12 CPUs, not
  oversubscribed, `AW_CORE_BUDGET_ENFORCE` != 0).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Rubric G (commit will be rejected) | `19313eed^:tests/test_begin_dirty_gate_scope.py` "from agent_workflows import oc_runipd as OC" used only by excluded `RunnerDeclaresTheExecutionBaselineTests`; `.pre-commit-config.yaml` `id: ruff` `args: [--fix]` | Copying the fixture module's imports verbatim would leave `OC` (and `inspect`) unused, so the mutating ruff hook rewrites and rejects the commit; E-01 did not list the needed imports. | all Low | FIXED | E-01 names the exact import set and forbids `OC`/`inspect`; V-01 demands clean `ruff check`/`ruff format --check`. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric A/G (mechanism underspecified) | `19313eed^` `_commit_paths` in `test_finalize_exact_attribution.py` returns the sha; in `test_finalize_scope_ownership.py` returns `None`; `ACTOR`/`SCOPE` identical | "Rename only where the two sources differ" left the executor to discover which collide; a single merged `_commit_paths` would break `ExactSourceWinsTests` (uses the returned sha). | all Low | FIXED | E-01 states `ACTOR`/`SCOPE` are defined once and names `_ea_commit_paths`/`_so_commit_paths`. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (validation does not localize the kill) | plan V-03 "verdict: killed" only | A `killed` verdict under the whole core selection does not prove the new module did the killing, nor rule out a broken baseline. | all Low | FIXED | V-03 also demands `baseline_failing: 0` and a `newly_failing` entry from the new module. |
| PR-004 | LOW | IN-SCOPE | Rubric G (contradictory instruction) | plan E-03 "or passed via `--extra-test`"; `tools/mutation_probe.py --help` "Extra test blob to read from COMMIT^:PATH" | `--extra-test` reads a parent-commit blob, so it cannot inject an uncommitted file; offering it as an alternative was misleading. | all Low | FIXED | E-03 requires commit-then-probe and explains why `--extra-test` is not used. |
| PR-005 | LOW | IN-SCOPE | Live-artifact criteria convention; Rubric E | plan E-02/V-02 "8 PASSED", "`8 passed` summary line"; E-04 "includes the 8 new tests"; V-03 `<E-04 base>` undefined | Collected test counts were the bar; `<base>` was never recorded; bare-tier collection of the module was not demanded; budget-block disposition was unstated. | all Low | FIXED | Bars rewritten to all-collected-PASSED re-derived at execution plus a bare `--collect-only` check; E-01 records `<base>`; E-04 states how a pre-existing budget block is treated. |
| PR-006 | LOW | UNDER-SCOPE | Plan executability (execution contract) | plan `## Approval and execution gate` | The gate lacked the paste-actual-output rule, a declarative scope fence, and the runner/hand finalize ownership; E-02 had no disposition for a copied test failing at execution HEAD. | all Low | FIXED | Gate rewritten to the repo's standard contract (`aw ipd finalize`, never hand `git mv`); E-02 carries the `jy7439`-style disposition rule. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the untested `_baseline_ambiguity` swap acceptable? | Keep the swap; F-08 records it kills with `mutant_failing: 1` | Revert to the F-04 pair (duplicates a `begin` test) | Review probe at HEAD `623eb73c`, plan F-08 | yes |
| D-2 | How to treat a `CORE TIER BUDGET EXCEEDED` block in E-04? | Record it; not a failure when it already fires at `<base>` | Treat any budget block as item failure (unsatisfiable on this host, F-05) | `conftest.pytest_sessionfinish`; plan F-05 | yes |
