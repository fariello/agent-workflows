# Review findings: plan t54fet

- Subject-Id: t54fet
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `4e7e2aea5`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean` (advisory `IPD-Z602` only). Not an orchestrator.

Verified at review:
- `8b798b0b8` is an ancestor of HEAD (F-2); `tests/test_runner_seams_core_budget.py` does not exist yet.
- `conftest.pytest_sessionfinish` rule as described (xdist-worker early return, `_core_filter_applied`
  gate, `AW_CORE_BUDGET_SECONDS` default 30.0, enforce when `cpu_count >= 12` and
  `AW_CORE_BUDGET_ENFORCE != "0"`).
- `suite_cache.build_suite_child_env` `base.setdefault(AW_CORE_BUDGET_ENFORCE_ENV, "0")` and appends
  `-n <workers>`; `run_full_suite` run-evidence branch mirrors and restores the variable;
  `SUITE_KEY_ENV_VARS` excludes it (one-repo-per-test rationale holds).
- `runner_shared.run_suite_check`, `start_suite_baseline` (argv rewrite to `agent_workflows suite --agent
  --no-serve-failures`; `SuiteBaselineRun` copies `os.environ`), `make_integration_validation_runner`
  record keys `passed`/`failures`/`measured` exist as cited; `tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun`
  and `tests/test_core_tier_selection.py::test_gate_suite_passes_an_all_green_over_budget_tree` /
  `::test_gate_suite_honors_explicit_enforce` exist (F-3).
- Pending plan `44nfmd` exists (F-5). Backlog `m8d13e` is `graduated` with `Blocks-Release: next`; the plan
  inherits it.
- HOW demonstration: a scratch prototype of exactly E-01's fixture and the E-02..E-04 calls (under the
  gitignored `.aw/state/review-t54fet/`, since removed) produced, with env applied `clear=True`:
  unset -> seam1 `passing True exit 0 cached False`, `AW_CORE_BUDGET_ENFORCE` absent after; seam2
  `completed exit 0 failures ()`; seam3 `True`/`passed True`. ENFORCE=1 -> seam1 `passing False exit 1
  failures ()`; seam2 `completed exit 1 failures ()`; seam3 `False`/`passed False`/`failures []`. Each
  about 2-4s; outer checkout `git status` unchanged. Temp fixture dirs were left under the system temp
  dir (`/tmp/t54fet-review-*`); the sandbox refused their removal.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric D/E (vacuous green under xdist) | E-02 "`mock.patch.dict(os.environ, ..., clear=False)`"; `unittest.mock.patch.dict` with `clear=False` only sets keys; prototype with parent `PYTEST_XDIST_WORKER=gw0` and `clear=False`: seam-1 control `passing True exit 0` | The helper "pops" `PYTEST_XDIST_WORKER` from a dict, but applying that dict with `clear=False` never removes the key from `os.environ`. Under the thorough tier's `-n auto` every child inherits the worker marker, the fixture hook returns early, all three green tests pass vacuously and all three controls fail. The serial run E-05 specified would not reveal it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires the env applied so removed keys are truly absent (`clear=True`, or `monkeypatch.delenv`), with the measured contrast recorded; E-02 references that rule. |
| PR-002 | MEDIUM | UNDER-SCOPE | Rubric E (validation does not cover the run mode CI uses) | E-05 explicit run `-o addopts=""` (serial); CI thorough tier runs `-n auto` | Validating only serially leaves PR-001's class of defect undetectable at execution. | all Low | FIXED | E-05 and V-05 add a `-n 2` run of the module with its summary line. |
| PR-003 | LOW | IN-SCOPE | Rubric G (fixture under-specified / ambiguous wording) | E-01 "reproduces the root `conftest.pytest_sessionfinish` ENFORCEMENT RULE" with no start timer; "Commit everything"; V-01 "under `/tmp/opencode`" | The fixture conftest needs its own session-start timestamp (the root one is set in `pytest_sessionstart`); "Commit everything" could be read as committing to this checkout; V-01 named a host-specific scratch path. | all Low | FIXED | E-01 names the `pytest_sessionstart` timer and scopes the commit to the fixture repo; V-01 uses `tempfile.mkdtemp()` and a clean env. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How must the env be applied so removed keys are absent? | Either `mock.patch.dict(..., clear=True)` or `monkeypatch.setenv`/`delenv`; executor's choice | Keep `clear=False` (measured vacuous under xdist) | review prototype contrast in PR-001; `tests/test_core_tier_selection.py::test_gate_suite_passes_an_all_green_over_budget_tree` uses `monkeypatch.delenv` | yes |
