# Review findings: plan sa629y

- Subject-Id: sa629y
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `3158217ae`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `runner_shared.SuiteCheckResult` ends with `failures`, `cached`, `digest`, `slot` (all defaulted) and has
  no `budget_only`; `run_suite_check` builds it from `suite_cache.SuiteRunResult`, which carries `stdout`
  and `stderr` (Step 0 correct).
- `make_integration_validation_runner` `_runner`: the exit-5 branch, `measured = True` default, the
  `measurement` dict carrying `measured`, and `cache[tree_id] = measurement` exist as described; the
  only definition is in `runner_shared`, and `oc_runipd`/`agy_runipd` pass `suite_check=run_suite_check`.
- `_relative_revalidation_verdict` returns early on `measurement.get("measured") is False`;
  `revalidation_was_unmeasured` reads `measured is False` on a non-passing record; `record_integration_refusal`
  rewrites `INTEGRATION_REFUSAL_CONFLICT` to `INTEGRATION_REFUSAL_UNMEASURED` when unmeasured; the
  combined-red send-back loop carries `and not revalidation_was_unmeasured(item)`.
- `44nfmd` (`Status: reviewed`) E-03 defines `is_budget_only_failure(exit_code, stdout, stderr, failures)`
  and pins that name and signature for this plan.
- Spec `25kzda` Section 2.1 text quoted by the plan is accurate.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric A/C (deferral can never succeed) | `agent_workflows/runner_shared.py` `make_integration_validation_runner` "if tree_id and isinstance(cache, dict) and tree_id in cache:" and "cache[tree_id] = measurement"; plan E-02 "the cache-hit path inherits the same reading"; F-6 | E-02 kept the budget-only reading in the per-run tree cache and called that a feature. The cache-hit branch returns the stored reading without calling `suite_check`, and a deferred re-attempt over an unchanged main rebuilds the same tree. So every re-attempt would be served the cached refusal until the retry limit ran out and the item went terminal: the "re-attemptable" deferral the plan is for could never succeed. Demonstrated (F-6) with an unmeasured reading: the second call came back `cached True, measured False` and the suite was called once. Sibling `xc1xh9` E-02 ("integrates on the next re-attempt once the suite is green") depends on this being fixed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds a `budget_only_red` flag and skips `cache[tree_id] = measurement` for it. E-04 (d) now asserts re-measurement (two stub calls, second call passes, no cache entry). V-02 and V-04 updated, F-6 added. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric E (test fails under CI's xdist) | plan E-05 (f); fixture conftest "if \"PYTEST_XDIST_WORKER\" in os.environ: return"; `.github/workflows/tests.yml` `python -m pytest tests/ -n auto -rfEs`; F-8 | As written, (f) passes serially but fails under workers. The child pytest inherits `PYTEST_XDIST_WORKER`, so the budget hook returns early and the child exits 0. Measured (F-8): `-n 2` gave `(True, 0, ())`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 (f) pops `PYTEST_XDIST_WORKER`, `PYTEST_XDIST_WORKER_COUNT`, `PYTEST_ADDOPTS`, `AW_SUITE_SLOT_HELD` and `AW_TEST_TIER` inside the patch and builds the repo with the hermetic helpers. E-06 and V-05/V-06 also run under `-n 2`. Measured passing under `-n 0` and `-n 2`. |
| PR-003 | MEDIUM | UNDER-SCOPE | Spec sync | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 2.1 "never applies to ... a non-passing combined revalidation ... none reclassifies a failure as a deferral" | The plan's argument that a budget-only red is outside Section 2.1 is sound, but it lived only in the plan. On a literal reading the spec text covers this case, so a later reviewer would see a contradiction the contract never records. The plan itself named a spec note as the remedy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-07/V-07 adds one dated `aw specs note` line (no status or body change). The spec is added to Scope-Paths, and the spec-sync section is updated. |
| PR-004 | LOW | IN-SCOPE | Rubric G (execution contract) | plan `## Approval and execution gate`; plan E-03 "set this item `blocked` and report it rather than editing a file outside Scope-Paths" | The gate had no explicit lifecycle ownership (runner versus hand), no open-question statement, and no scope-fence declaration. E-03 told the executor to stop over a scope question, which the 2026-09-01 fence ruling forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate is rewritten with all execution-contract elements. Its one STOP is reserved for an absent `44nfmd` predicate (a missing-prerequisite case). E-03 now says to edit any host-local copy and justify it with `--scope-reason`. |
| PR-005 | LOW | IN-SCOPE | Rubric G (precision) | plan E-05 (e), V-05 "final `6 passed` line", OQ-01/OQ-02 "Owner: none" | (e) left out the required keyword arguments of `record_integration_refusal` (`run_dir`, `state`, `attempt`, `branch`). V-05 used a test count as its bar. Both resolved questions recorded the owner as `none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (e) now names every argument and asserts `deferred is True` (F-7 ran the call: `merge-unchecked True merge-retry True`). V-05's bar is now 0 failed. Owner is set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should a deferred re-attempt see a fresh measurement of an unchanged merged tree? | Do not store a budget-only measurement in the tree cache | Evict on re-attempt in `retry_deferred_integrations` (a second site per host); add load to the cache key (the measurement is not a tree property) | `make_integration_validation_runner` cache-hit branch; F-6 | yes |
| D-2 | Must the Section 2.1 reading be recorded on the spec? | Yes, as a history note with no body change | Leave it in the plan only (invisible to spec readers); amend Section 2.1's body (larger contract change than the reading needs) | `25kzda` Section 2.1 and 2.1a reasoning "none of which repetition fixes"; the plan's own spec-sync remedy | yes |
