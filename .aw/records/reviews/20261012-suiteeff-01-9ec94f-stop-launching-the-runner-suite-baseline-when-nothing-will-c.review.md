# Review findings: plan 9ec94f

- Subject-Id: 9ec94f
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `80a174bf6` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` was clean after revisions.

Re-verified:
- `runner_shared.execute_item_core`: the baseline start condition (`not is_review and not is_production and self_finalize and callable(baseline_extractor) and getattr(driver_module, "SUITE_CHECK_ARGV", None)`, runner_shared.py:35809) carries no validation term; `validate = opts.get("validate", False)` / `if "validate" not in opts: validate = not (opts.get("no_verify") or opts.get("no_audit"))` is computed after the turn (runner_shared.py:36301); collection sits under `if integration_gate_relevant and not validate:` (runner_shared.py:37118, `suite_baseline_run.collect(wait_seconds=0.0)` at :37156); the `finally` abandons and removes the checkout (runner_shared.py:40366).
- The only other reader of the pre-turn `suite_baseline` value is the gate-answer follow-up (`baseline=suite_baseline`, runner_shared.py:37319/:37337), reached only when `gate_answer_is_warranted` asks, which it does only on the suite-failure signal; with validation ON no driver suite runs, so ON mode loses nothing. `revalidation_baseline_for` reads `attempt["suite_baseline"]`, written only in the OFF branch.
- Both hosts share the seam (`agy_runipd.execute_item` -> `runner_shared.execute_item_core`, `driver_module=sys.modules[__name__]`, agy_runipd.py:3033); `SUITE_CHECK_ARGV` and `extract_suite_failures` are re-exported by both drivers, so the fix covers both.
- Harness probe (scratch tests under gitignored `.aw/state/`, since deleted), unchanged code: `oc_runipd.execute_item` with `AttemptLaneFactsTests._oc_state_and_item` options (validation ON by default) produced baseline events `['suite-baseline-started']`, `suite_baseline_started` present, `suite_baseline` absent, and the baseline directory EMPTY afterwards. With `validate: False` plus `SUITE_CHECK_ARGV` patched to `(sys.executable, "-c", "print('1 passed')")` and `run_suite_check` patched to a passing `SuiteCheckResult`: `[('suite-baseline-started', None), ('suite-baseline-collected', 'completed')]`.
- `tests/test_suite_baseline.py` was deleted by `19313eed7` ("test: trim test suite from 9,136 to under 2,000 tests"); no remaining test references `start_suite_baseline` or the baseline events.
- The October run records behind F-01/F-03 are gitignored (`.aw/.gitignore:14`) and not in this lane; they are context, not a V bar, and E-03's reverted-condition cell re-proves the mechanism.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing / evidence | plan E-03 "reuse the harness used by `tests/test_suite_baseline.py`"; V-03 "`python3 -m pytest ... tests/test_suite_baseline.py`"; Required tests "`tests/test_suite_baseline.py` must still pass"; file deleted in `19313eed7` | The plan named a deleted test file three times as both harness and required-passing evidence; V-03 was unsatisfiable as written and E-03 named no harness that exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now names the existing harness (`tests.test_oc_runipd._init_repo_with_conforming_plan`, `AttemptLaneFactsTests` builders/fake agent) plus the two patches cell (c) needs, both demonstrated at review; V-03 and Required tests name `tests/test_suite_baseline_direction.py` and `tests/test_attempt_lane_facts.py`. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing | plan E-02/E-03 "no baseline checkout directory"; runner_shared.py:40366 `remove_suite_baseline_checkout` in `finally`; probe: directory empty after a default-mode run today | "No baseline checkout directory" holds before AND after the fix, so as a distinguishing assertion it cannot fail with E-02 reverted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with "no `attempt[\"suite_baseline_started\"]` key" (present today, measured) beside the event assertions; E-03 says why the directory is not a signal. |
| PR-003 | MEDIUM | UNDER-SCOPE | D. Anti-regression | plan E-03 (a) "four option shapes"; runner_shared.py:36303 `opts.get("no_verify") or opts.get("no_audit")` | The `no_audit` arm of the expression (the one `oc_runipd` sets, oc_runipd.py:5443) had no cell, so a hoist that dropped it would pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cell (a) now covers five shapes including absent-with-`no_audit`-True; invariants I1-I3 named in Required tests. |
| PR-004 | MEDIUM | IN-SCOPE | F. Silent failure / precision | plan E-02 "When skipped, append one `suite-baseline-skipped` event" | "When skipped" did not say skipped for WHICH reason, so a review or production turn could start emitting a misleading "validation is ON" event. The rationale for ON mode not needing the baseline (gate-answer reader) was also unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Event emitted only when every pre-existing condition held and validation alone blocked it; payload fields named; the gate-answer reasoning added to the WHY comment. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked `aw ipd begin`, the scope-fence declaration, the MUST-paste honesty rule, and runner-vs-hand ownership of the terminal transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All added; no STOP-on-scope wording. |
| PR-006 | LOW | IN-SCOPE | Project rule (OQ owner) / docs | OQ-01 "Owner: none"; E-04 "at the top of `## 2.0.0 (pending)` list" vs CHANGELOG.md:7 heading with trailing title and prose before the bullets | OQ-01 resolver unrecorded; E-04's insertion point ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner `plan author` (D-1); E-04 names the insertion point as the first bullet under the prefixed heading. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep the baseline for validation-OFF mode (OQ-01)? | Yes, as authored | Delete the baseline machinery (loses `revalidation_baseline_for`'s permissive relative verdict) | runner_shared.py:27017 `revalidation_baseline_for`; spec `25kzda` HONEST LIMIT paragraph | yes |
| D-2 | Which harness should E-03 use now that `tests/test_suite_baseline.py` is gone? | `AttemptLaneFactsTests` builders + `_init_repo_with_conforming_plan`, patching `run_opencode`, `SUITE_CHECK_ARGV`, `run_suite_check` | Recreate the deleted file's harness (larger, unrequested); call `start_suite_baseline` directly (does not exercise the gate condition) | review probe output above | yes |
