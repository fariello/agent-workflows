# Review findings: plan 44nfmd

- Subject-Id: 44nfmd
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean` (one `info` `IPD-Z602` on E-07). Child plan, Set `48hjbx`, Order 1; downstream plans `sa629y` (`executed:44nfmd`) and `xc1xh9` (`executed:44nfmd`) depend on it, and `t54fet` cites it as carrier.

Verified:
- `conftest.pytest_sessionfinish` (docstring "Enforce the wall-time budget on the core tier (IPD hguae9 E-05)"): fails when `cpu_count >= 12 and enforce`, else writes `WARNING: ` + banner; banner text `CORE TIER BUDGET EXCEEDED`.
- `tests/test_core_tier_selection.py` is `pytestmark = pytest.mark.core`, holds `CONFTEST_HOOKS`, `temp_project`, `_clean_env`, `_gate_env`, `test_gate_suite_passes_an_all_green_over_budget_tree`, `test_gate_suite_honors_explicit_enforce`.
- `suite_cache.build_suite_child_env` `base.setdefault(AW_CORE_BUDGET_ENFORCE_ENV, "0")`; commit `8b798b0b8` 2026-10-16 21:20, backlog commit `a07064f80` 20:55 (git log).
- `suite_cache.run_full_suite` generic branch `f"suite FAILED with exit {exit_code} in {checkout_path} "`; `failures = extract_suite_failures(stdout, stderr)`; failure cache write only after `_confirm_failing_node_ids` on parsed node ids.
- Reason flow: `run_suite_check` `reason=res.reason` -> `make_integration_validation_runner` `measurement["reason"]` -> `_relative_revalidation_verdict` (prefix/suffix only) -> `_record_revalidation` `"reason": reason` -> combined-red loop `pre_rev = item.get(REVALIDATION_CACHE_KEY)`, `else "no test ids recorded"`.
- `run_analytics_telemetry` uses `os.getloadavg()`.
- Measured: host `nproc` 12; bare core run with `AW_CORE_BUDGET_ENFORCE=0`: load 9.82 before, 14.22 after, `753 passed in 75.10s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Testing (load independence) | `tests/test_core_tier_selection.py` `_gate_env` / `test_gate_suite_honors_explicit_enforce`; measured load 14.22 on 12 CPUs | E-02 pinned `AW_TEST_LOADAVG` only for "the existing enforce/warn tests", but `test_gate_suite_honors_explicit_enforce` also asserts a budget failure and would flip to a pass whenever the live 1-minute load exceeds 12, which the review measured happening during a normal core run. | all Low | FIXED | E-02 now pins `AW_TEST_LOADAVG=0` by default in `_clean_env`, covering every test including the `_gate_env` users; V-02 demands the hunk. |
| PR-002 | HIGH | IN-SCOPE | Correctness (predicate contract) | old E-03 "without the `WARNING:` prefix variant being the only occurrence"; conftest warning writes `f"\nWARNING: {msg}"` | The budget-only predicate's warning exclusion was ambiguous (substring `WARNING:` co-occurs with arbitrary test output) and is a cross-plan contract reused by `sa629y`. | all Low | FIXED | E-01 adds an exact `Core tier budget not enforced:` marker to every warning banner; E-03 adds `CORE_BUDGET_NOT_ENFORCED_MARKER` and defines the predicate as banner present AND marker absent, and pins the name/signature for `sa629y`. E-04 adds marker and exit-2 cases. |
| PR-003 | MEDIUM | UNDER-SCOPE | Correctness (unknown load) | E-01 `AW_TEST_LOADAVG` override | An unparseable `AW_TEST_LOADAVG` would raise inside `pytest_sessionfinish`; the fallback was defined only for `os.getloadavg` errors. | all Low | FIXED | E-01 treats an unparseable override as unknown (enforce); E-02 case (c) tests it. |
| PR-004 | MEDIUM | IN-SCOPE | Testing (end-to-end shape) | old E-04(b); `_gate_env` pops `AW_SUITE_SLOT_HELD`; `CONFTEST_HOOKS` | The end-to-end test would have needed a third copy of the hook and an unstated env, and had no failing-test control proving real failures keep today's reason. | all Low | FIXED | E-04 reuses `CONFTEST_HOOKS` and `_gate_env` by import, adds a failing-test control, and requires `budget` in test names so V-04's `-k budget` selects them. |
| PR-005 | MEDIUM | IN-SCOPE | Validation (V-08 feasibility) | AGENTS.md "HOW TO RUN THE SUITE"; measured `753 passed in 75.10s` under load | V-08 demanded a bare core run with zero failures and no exit statement, yet the bare run can still exit 1 on the budget on a quiet-but-slow host; and "no new `aw check` error" had no baseline. | all Low | FIXED | V-08 demands `exit=`, a banner plus `AW_CORE_BUDGET_ENFORCE=0` rerun when the budget fires, and an `aw check --agent` comparison against the base commit in a `/tmp/opencode` worktree; E-08 matches. |
| PR-006 | MEDIUM | IN-SCOPE | Evidence (stale finding) | F-6, Deferred "Closing the duplicate backlog items"; plans `t54fet`, `sa629y`, `xc1xh9` `- From-Backlog:` | F-6 and the Deferred row called `m8d13e`, `vtcqpf`, `o58dro` duplicates to be closed, but each has graduated to its own carrier that depends on this plan; the Carrier listed backlog ids rather than carriers. | all Low | FIXED | F-6 and the Deferred row rewritten to name the carriers `t54fet`, `sa629y`, `xc1xh9`. |
| PR-007 | LOW | IN-SCOPE | Process (gate, OQ owner) | gate paragraph; OQ-01/OQ-02 `Owner: none` | Gate lacked the scope-fence declaration and conditional runner/executor finalize ownership; OQ owners were `none` for author-resolved questions. | all Low | FIXED | Gate rewritten with full execution contract; owners set to `plan author`. |
| PR-008 | LOW | IN-SCOPE | Executability (E-05/E-07 detail) | combined-red loop `pre_rev.get("baseline_comparison") or {}`; E-07 Z602 | E-05 did not require tolerance of a `None` `baseline_comparison` nor show the reason actually reaches the send-back; E-07 read as four clauses. | all Low | FIXED | E-05 states the `None` tolerance and the reason flow; E-06 adds the `None` case; E-07 reworded as one sync concern. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Load threshold for demotion (OQ-01) | 1-minute load above CPU count | Fixed multiple (2x CPUs) (REJECTED: would still enforce the measured 14.22 run); 5-minute average (REJECTED: lags an episode) | backlog `m8d13e` load 26-31; review measurement 9.82 -> 14.22 at 75.10s on 12 CPUs | yes |
| D-2 | Keep budget-only red as a failure in `suite_cache` (OQ-02) | Keep; name the cause only | Convert to pass (REJECTED: explicit enforce is a request for enforcement) | `test_gate_suite_honors_explicit_enforce` | yes |
| D-3 | How the predicate tells enforced from warned banners | Explicit `Core tier budget not enforced:` marker on every warning | Parse the `WARNING:` prefix (REJECTED: ambiguous substring) | conftest warning `f"\nWARNING: {msg}"`; `sa629y` E-01 reuses the predicate | yes |
| D-4 | Unparseable `AW_TEST_LOADAVG` | Treat as unknown, keep enforcement | Raise / treat as zero load (REJECTED: crash in a session hook / silently equals enforce anyway) | E-01 fallback rule for `os.getloadavg` errors | yes |
