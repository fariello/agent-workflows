# Review findings: plan zyy2yg

- Subject-Id: zyy2yg
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e9e14c28d`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `jycfw3`, Order 1), test-only, `Work-Kind: followup` (no release gate required; backlog `jycfw3` carries none).

Verified at the lane HEAD:
- `suite_cache.DEFAULT_AW_SUITE_SLOT_TIMEOUT: float = 3600.0`; `conftest._DEFAULT_TEST_WALL_TIMEOUT = 240.0`; `suite_cache.resolve_suite_lock_dir` precedence `AW_SUITE_LOCK_DIR` -> `XDG_RUNTIME_DIR/agent-workflows` -> tempdir; `suite_cache.suite_slot` short-circuits on `AW_SUITE_SLOT_HELD == "1"` and writes the waiting line to the parent's `sys.stderr`.
- `suite_cache.SUITE_KEY_ENV_VARS` does not contain `AW_SUITE_LOCK_DIR` (F-6 correct).
- `tests/test_suite_cache.py`: `_fixture_env` does `env = dict(os.environ)` at call time; the direct `run_full_suite` calls and the `mock.patch.dict(os.environ, _fixture_env())` seam block are as F-1 states; `_gate_env` is imported by the two budget tests; no `AW_SUITE_LOCK_DIR` elsewhere in the module. 17 tests collected; none are core-tier (bare `python3 -m pytest --collect-only` lists none of them).
- `platform_lock.held` exists; commit `548fa71da` subject matches (`test(twz0tw): isolate core-tier gate_suite tests ...`); backlog `jycfw3` exists (graduated, `Graduated-To: jycfw3`).
- Only this plan declares `tests/test_suite_cache.py` in `- Scope-Paths:` (F-7 correct).
- HOW demonstration (OQ-01 and E-02 design): scratch test under gitignored `.aw/state/` with the plan's fixture and E-02 body, invoking shell's `AW_SUITE_LOCK_DIR` cleared. Isolated: `{'acquired': True, 'waited_seconds': 0.001, 'slot_index': 0}`, waiting line absent from `capfd` err, passed. Setenv removed: `{'acquired': False, 'waited_seconds': 5.005, 'slot_index': None}`, waiting line present, failed on `assert res.slot["acquired"] is True` while `res.passed` stayed True. Recorded as plan F-8.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Testing (resource use / KISS) | `agent_workflows/suite_cache.py:1163` `build_suite_child_env` appends `-n <workers>`; probe output `created: 12/12 workers` | E-02 called `run_full_suite` with the default argv, so the child pytest spawns `cpus // slots` xdist workers (12 on the review host) for a one-test fixture repo, inside a file already run at `-n 4`: 2.6-2.9s per run and host oversubscription. The slot path under test does not depend on argv. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 passes the explicit serial argv the module's budget tests use (`-q -o addopts= -n 0`); demonstrated 1.25s green, red without isolation (F-8); V-02 demands it in the diff. |
| PR-002 | LOW | IN-SCOPE | G. Re-derivation convention | plan E-01 Expected outcome "same 17 tests"; Required tests "all 18 tests"; V-01 "17 passed"; V-04 "18 passed" | A collected test count is an artifact of test organization and may not be a V-item bar. | all Low | FIXED | E-01, Required tests, V-01 and V-04 now demand passed == collected count re-derived via `--collect-only -q`, zero failed/errors; authoring counts kept as context. |
| PR-003 | LOW | IN-SCOPE | Evidence accuracy | `tests/test_suite_cache.py:86` `def _run_aw_suite(`; `rg -c "= _run_aw_suite\("` -> 15 | F-1 said 16 `_run_aw_suite(` calls; that count included the definition. | all Low | FIXED | F-1 now says 15 call sites. |
| PR-004 | LOW | IN-SCOPE | V-item feasibility / shared-host safety | plan gate "plus this plan when recording evidence"; V-03 "showing only `tests/test_suite_cache.py` changed"; E-04 holder | V-03's `git diff --stat` bar conflicts with recording evidence into the plan file; the real-slot holder was bounded at 180s but not told to stop when the contended run finishes, holding peers off longer than needed. | all Low | FIXED | V-03 allows this plan file; E-04 terminates the holder once the contended run finishes. |

`aw ipd lint --phase review-finalize --agent`: `clean` after setting `Status: reviewed` and `Readiness: go-pending-approval`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Module autouse fixture or per-call `env` overrides (plan OQ-01)? | Keep the author's module autouse fixture | Per-call `env` at the four backlog-named sites (does not reach the 15 `aw suite` subprocess sites or the env-less seams) | `runner_shared.run_suite_check` calls `run_full_suite` without `env`; F-8 demonstration | yes |
| D-2 | Use the default argv or an explicit serial argv in E-02? | Explicit `-n 0` serial argv | Default `SUITE_CHECK_ARGV` (12 xdist workers, slower) | `build_suite_child_env`; F-8 timings; budget tests in the same file | yes |
| D-3 | Does a budget-only overrun in the bare gate fail this plan? | No, record verbatim (author's rule kept) | Treat as failure | `conftest.py` "CORE TIER BUDGET EXCEEDED"; review f4txy2 D-3 | yes |
