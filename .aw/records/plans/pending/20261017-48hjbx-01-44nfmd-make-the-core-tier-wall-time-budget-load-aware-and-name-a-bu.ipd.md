# IPD: Make the core-tier wall-time budget load-aware and name a budget-only red in suite reports

- Date: 2026-10-17
- Kind: child
- Concern: The core-tier wall-time budget guard in the root `conftest.py` turns an all-green test run into exit 1 when the host is loaded, and when that exit reaches a runner the operator and the agent are told the suite was RED with "no test ids recorded", which names no cause and gives nothing to fix.
- Scope: (1) Make the conftest budget guard demote an overrun to a warning when the host is measurably oversubscribed (1-minute load average above the CPU count), and print the measured load in the budget banner either way; (2) make `suite_cache.run_full_suite` report a nonzero exit whose only cause is the budget banner as a budget-only failure in its `reason` instead of a generic "suite FAILED"; (3) replace the runner's combined-red send-back text "no test ids recorded" with a sentence that states the recorded revalidation reason, through one small helper; (4) behavioral tests for all three; (5) sync the budget comment in `pyproject.toml`, the `CONTRIBUTING.md` suite paragraph, and a CHANGELOG `Fixed` line. It does NOT change the 30s budget value, the core marker membership, or the `ytz6z4` runner-side demotion already shipped in `8b798b0b8`.
- Scope-Paths: conftest.py, tests/test_core_tier_selection.py, agent_workflows/suite_cache.py, tests/test_suite_cache.py, agent_workflows/runner_shared.py, tests/test_combined_red_failure_lines.py, pyproject.toml, CONTRIBUTING.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 48hjbx
- Blocks-Release: next
- Set: 48hjbx
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 44nfmd
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 fixed (review record `.aw/records/reviews/20261017-48hjbx-01-44nfmd-make-the-core-tier-wall-time-budget-load-aware-and-name-a-bu.review.md`).
- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-17 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog 48hjbx with Step 0 evidence; review-ready.

## Goal

A core-tier run in which every test passes must not be reported as a failure merely because other work on the host slowed it down, and when the budget does fail a run, every report a human or agent reads (the pytest banner, the suite helper's `reason`, the runner's combined-red send-back) must say that the budget, not a test, was the cause.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: load-aware budget guard (conftest)

- [ ] E-01 In the root `conftest.py` `pytest_sessionfinish` budget hook (the function whose docstring reads "Enforce the wall-time budget on the core tier (IPD hguae9 E-05)"), read the 1-minute load average with `os.getloadavg()[0]` (overridable by a new env `AW_TEST_LOADAVG` for tests, mirroring the existing `AW_TEST_CPU_COUNT` override; an `AW_TEST_LOADAVG` that does not parse as a float, or `OSError`/`AttributeError` from `os.getloadavg`, means "unknown", and unknown keeps today's enforcement). Read it only inside the over-budget branch. When over budget AND enforcement would otherwise apply (`cpu_count >= 12` and `AW_CORE_BUDGET_ENFORCE != "0"`), demote the failure to the existing `WARNING:` banner if the load average is known and greater than `cpu_count`. In both the failing and the warning banner add one line `Host 1-minute load average: <x:.2f> on <n> CPUs` (or `Host 1-minute load average: unknown on <n> CPUs`). In EVERY warning case (and never in the failing case) add one line beginning with the exact marker `Core tier budget not enforced:` followed by the reason that applies (`AW_CORE_BUDGET_ENFORCE=0`; `fewer than 12 CPUs`; or `host oversubscribed (1-minute load average above the CPU count)`). Keep the exact `CORE TIER BUDGET EXCEEDED` banner text; E-03 keys on the banner and on the absence of that marker.
  - Depends on: none
  - Expected outcome: an over-budget core run with `AW_TEST_LOADAVG` above the CPU count exits 0 with the warning banner, the load line and the `Core tier budget not enforced:` marker; with `AW_TEST_LOADAVG` at or below the CPU count (or unparseable) it exits 1 as today, printing the load line and no marker.
  - Execution state: pending

- [ ] E-02 Update the hook copy `CONFTEST_HOOKS` in `tests/test_core_tier_selection.py` to match E-01, and make `_clean_env` default `AW_TEST_LOADAVG` to `"0"` (still overridable by its keyword arguments) so EVERY existing test in the file, including `_gate_env` users `test_gate_suite_passes_an_all_green_over_budget_tree` and `test_gate_suite_honors_explicit_enforce`, is independent of the live host load (measured at review: the 1-minute load on the 12-CPU host read 14.22 at the end of a bare core run, which would otherwise flip `test_gate_suite_honors_explicit_enforce` to a pass). Add behavioral subprocess tests in that file (it is `core`-marked) driving the temp project with `AW_CORE_BUDGET_SECONDS=0.01`, `AW_TEST_CPU_COUNT=12`, `AW_CORE_BUDGET_ENFORCE=1`: (a) `AW_TEST_LOADAVG=30` exits 0 and the combined output contains `WARNING:`, `CORE TIER BUDGET EXCEEDED`, `load average: 30.00` and `Core tier budget not enforced:`; (b) `AW_TEST_LOADAVG=2` exits nonzero, contains the banner and `load average: 2.00`, and does not contain `Core tier budget not enforced:`; (c) `AW_TEST_LOADAVG=not-a-number` exits nonzero and contains `load average: unknown`.
  - Depends on: E-01
  - Expected outcome: the new tests and every existing test in `tests/test_core_tier_selection.py` pass independent of the real host load.
  - Execution state: pending

### Task group 2: name a budget-only failure in suite reports

- [ ] E-03 In `agent_workflows/suite_cache.py`, add a module constant `CORE_BUDGET_BANNER = "CORE TIER BUDGET EXCEEDED"` and a module constant `CORE_BUDGET_NOT_ENFORCED_MARKER = "Core tier budget not enforced:"` (the E-01 marker), and a pure function `is_budget_only_failure(exit_code, stdout, stderr, failures) -> bool` that is True only when `exit_code == 1`, `failures` is empty, `CORE_BUDGET_BANNER` appears in stdout or stderr, and `CORE_BUDGET_NOT_ENFORCED_MARKER` appears in neither (an enforced banner never carries the marker, so a warned overrun beside some other exit-1 cause is not misnamed). Plan `sa629y` (backlog `o58dro`) reuses this predicate by that exact name and signature, so neither may change. A cached failure is stored only after `_confirm_failing_node_ids` re-runs parsed node ids, which a budget-only run has none of, so the cached-serve branch of `run_full_suite` needs no change. In `run_full_suite`, in the generic nonzero-exit branch that builds `reason = f"suite FAILED with exit {exit_code} in ..."`, use instead `f"suite FAILED with exit {exit_code} in {checkout_path} ONLY on the core-tier wall-time budget (no test failed; {summary or 'no summary line parsed'})"` when that predicate holds. `passed` stays False: this plan names the cause, it does not convert the verdict (the gate path already defaults enforcement off via `build_suite_child_env`, backlog `ytz6z4`).
  - Depends on: none
  - Expected outcome: a run whose only failure is the enforced budget carries a `reason` naming the budget; any run with a real failing test keeps today's reason unchanged.
  - Execution state: pending

- [ ] E-04 Add behavioral tests to `tests/test_suite_cache.py`: (a) unit tests of `is_budget_only_failure` over synthetic outputs (banner + exit 1 + no failures -> True; banner + a `FAILED tests/x.py::t` line -> False; exit 0 -> False; banner carrying the `Core tier budget not enforced:` marker with exit 1 -> False; exit 2 with the banner -> False); (b) one end-to-end `run_full_suite` call on a temp project built the same way as `tests/test_core_tier_selection.py::temp_project` (write its conftest from `tests.test_core_tier_selection.CONFTEST_HOOKS` by import rather than a third copy of the hook; argv `[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"]`, `use_cache=False`) with `AW_CORE_BUDGET_ENFORCE=1`, `AW_CORE_BUDGET_SECONDS=0.01`, `AW_TEST_CPU_COUNT=12`, `AW_TEST_LOADAVG=1` passed via `env=tests.test_core_tier_selection._gate_env(AW_CORE_BUDGET_ENFORCE="1", AW_TEST_LOADAVG="1")` (the helper already pops `AW_SUITE_SLOT_HELD` and the xdist/tier variables), asserting `not res.passed`, `res.exit_code == 1`, `res.failures == ()` and `"wall-time budget" in res.reason`; plus a control on the same project with a deliberately failing core test, asserting the reason does NOT contain `wall-time budget`. Every new test name contains `budget` so V-04's `-k budget` selects them.
  - Depends on: E-01, E-03
  - Expected outcome: the new tests pass and assert on the returned `SuiteRunResult`, not on source text.
  - Execution state: pending

### Task group 3: combined-red send-back names the cause

- [ ] E-05 In `agent_workflows/runner_shared.py`, extract the failing-test text built inside the combined-red send-back loop (the block that today assigns `fail_lines = ... else "no test ids recorded"`, beside the `combined-red-sent-back` event) into a module-level pure helper `combined_red_failure_lines(revalidation: Mapping[str, Any]) -> str`. It returns the bulleted `new_ids` (else `failures`) exactly as today when any exist; when none exist it returns `"no failing test id was recorded; the recorded revalidation reason was: <reason>"` using `revalidation["reason"]` (or `"(no reason recorded)"` when that key is absent or empty). It must tolerate a missing or `None` `baseline_comparison`, exactly as the inline code does today (`pre_rev.get("baseline_comparison") or {}`). Call it from the loop, passing the same `pre_rev` mapping, so the send-back prompt and its behavior are otherwise unchanged. The recorded `reason` reaches this point unmodified from `suite_cache.run_full_suite` through `runner_shared.run_suite_check` (`reason=res.reason`), the `measurement["reason"]` in `make_integration_validation_runner`, `_relative_revalidation_verdict` (which only prefixes or suffixes it) and `_record_revalidation` (`"reason": reason`), which is why E-03's wording becomes visible here.
  - Depends on: E-03
  - Expected outcome: an agent receiving a combined-red send-back with no ids reads the revalidation reason, which after task group 2 names the budget when that is the cause.
  - Execution state: pending

- [ ] E-06 Add `tests/test_combined_red_failure_lines.py` (module `pytestmark = pytest.mark.core`) calling `runner_shared.combined_red_failure_lines` with: a record carrying `baseline_comparison.new_ids` (asserts each id appears as a `- ` bullet and the old-ids are not listed); a record with only `failures` and `baseline_comparison: None`; a record with neither and `reason` naming the budget (asserts the reason text appears and the string `no test ids recorded` does not); and an empty mapping (asserts `(no reason recorded)`). Also run the existing send-back test `tests/test_hook_and_suite_fix_it.py` unchanged to show the populated-id path is preserved.
  - Depends on: E-05
  - Expected outcome: new tests pass; `tests/test_hook_and_suite_fix_it.py` passes unchanged.
  - Execution state: pending

### Task group 4: documentation sync and suite run

- [ ] E-07 Sync the three documents that state the enforcement rule to the shipped behavior, one edit each: in `pyproject.toml`, the `[tool.pytest.ini_options]` header comment and the `core` marker comment (both read "enforced on >=12 CPUs / 6 workers; escape with AW_CORE_BUDGET_ENFORCE=0") gain "not enforced when the 1-minute load average exceeds the CPU count"; the `CONTRIBUTING.md` suite paragraph (beginning "`make test` (or bare `python3 -m pytest`) runs the core test tier") gains one sentence saying the same and that the budget banner prints the measured load; and the pending 2.0.0 section of `CHANGELOG.md` gains one `- Fixed:` bullet beside the existing `- Fixed:` bullets, in plain user-facing language with no em or en dashes, covering both the load-aware budget and the named cause in suite and runner reports.
  - Depends on: E-01
  - Expected outcome: the three files describe the shipped behavior; `git diff` touches only those lines.
  - Execution state: pending

- [ ] E-08 Run the bare core tier `python3 -m pytest` and the touched test files explicitly (`python3 -m pytest tests/test_core_tier_selection.py tests/test_suite_cache.py tests/test_combined_red_failure_lines.py tests/test_hook_and_suite_fix_it.py`), plus `aw check --agent` on the changed tree and on the plan's base commit (a throwaway worktree under `/tmp/opencode`) for comparison, and `aw sanitize --agent`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: all pass; no new `aw check` or sanitizer finding.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The budget guard is `conftest.pytest_sessionfinish` (docstring "Enforce the wall-time budget on the core tier (IPD hguae9 E-05)"); it fails when `cpu_count >= 12` and `AW_CORE_BUDGET_ENFORCE != "0"`, reading `AW_TEST_CPU_COUNT` and `AW_CORE_BUDGET_SECONDS` overrides. The xdist relay of `_core_filter_applied` lives in `tests/deselect_notice.py` (`pytest_testnodedown`).
- `tests/test_core_tier_selection.py` tests the hook through a COPY in `CONFTEST_HOOKS` run in a temp project subprocess (plan `hguae9` E-05). That copy must be updated in step with `conftest.py`, which is why E-01 has a sibling test item that edits it.
- Backlog `ytz6z4` (done, commit `8b798b0b8`, "suite gate: demote the core-tier wall-time budget to a warning for runner-launched suites") made `suite_cache.build_suite_child_env` default `AW_CORE_BUDGET_ENFORCE=0` and mirrored it on the run-evidence path in `run_full_suite`. So the runner's own gate suite is already demoted; `48hjbx` was filed at 20:55 and `8b798b0b8` landed at 21:20 the same evening (git log), so the remaining live defect is bare `pytest` (`make test`, an agent's in-lane validation, the documented routine gate) plus the unexplained send-back text.
- The send-back text "no test ids recorded" is built in `runner_shared` inside the combined-red loop beside `"event": "combined-red-sent-back"`, from `item[REVALIDATION_CACHE_KEY]` (`new_ids` else `failures`). The recorded revalidation shape is written by `runner_shared._record_revalidation` and includes a `reason` key.
- `suite_cache.run_full_suite` builds `reason` from `exit_code` with dedicated 0/124/127 branches and a generic "suite FAILED with exit" branch; `failures` comes from `extract_suite_failures` (`FAILED`/`ERROR` lines).
- `os.getloadavg` is already used in the package (`run_analytics_telemetry` `load()` probe, catching `OSError`/`AttributeError`), which is the precedent for the unknown-load fallback.
- Tests must assert behavior (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); new test modules in the core tier carry `pytestmark = pytest.mark.core` as `tests/test_core_tier_selection.py` does.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The guard fails an all-green run on host load alone | backlog `m8d13e` summary: load average ~26-31 measured 54-72s core wall time on 12 CPUs; `48hjbx` summary "though all tests pass" |
| F-2 | The runner gate path is already demoted | commit `8b798b0b8`; `suite_cache.build_suite_child_env` `base.setdefault(AW_CORE_BUDGET_ENFORCE_ENV, "0")`; tests `test_gate_suite_passes_an_all_green_over_budget_tree` |
| F-3 | Bare `python3 -m pytest` still enforces, and it is the routine gate agents are told to run and paste | AGENTS.md repo-local "HOW TO RUN THE SUITE"; `conftest.pytest_sessionfinish` |
| F-4 | A red with no ids prints "no test ids recorded" with no cause | `runner_shared` combined-red send-back loop |
| F-5 | The suite itself contributes about 6 to the load average (6 xdist workers on 12 CPUs), so a threshold of "load above CPU count" fires only when other work at least matches the suite's own demand | `conftest.pytest_xdist_auto_num_workers` caps at min(6, cpus/2) (plan `hguae9` conventions) |
| F-6 | Three other backlog items (`m8d13e`, `vtcqpf`, `o58dro`) describe surfaces of the same defect, and each has graduated to its own carrier that builds on this plan: `t54fet` (seam regression tests, declares `44nfmd` as carrier of the bare-pytest and send-back halves), `sa629y` (budget-only red defers as unmeasured; `- Item-Dependencies: executed:44nfmd`, reuses `suite_cache.is_budget_only_failure`), `xc1xh9` (host end-to-end proof; depends on `executed:44nfmd`) | their `- Summary:` lines; those plans' `- From-Backlog:` and `- Item-Dependencies:` fields |

## Proposed changes (ordered, validatable)

1. E-01 and E-02: load-aware demotion in the conftest guard, with load printed in the banner.
2. E-03 and E-04: `suite_cache` names a budget-only failure in `reason`.
3. E-05 and E-06: the runner send-back uses that reason when no ids exist.
4. E-07 and E-08: docs sync and full validation.

## Deferred / out of scope (with reason)

- Changing the 30s budget value or re-balancing core membership: that is a performance decision with its own plan lineage (`hguae9`), and this bug is about load, not about the suite getting slower.
  - Carrier-Declined: not a defect; the 30s value and core membership are deliberate design choices of executed plan hguae9, and nothing here is left unfixed.
- The remaining surfaces filed as backlog `m8d13e`, `vtcqpf`, `o58dro` (runner-seam regression tests, budget-only revalidation classified as unmeasured, host end-to-end proof): each is carried by its own graduated plan (`t54fet`, `sa629y`, `xc1xh9`) that depends on or cites this plan; closing those items is outside this plan's authority.
  - Carrier: t54fet, sa629y, xc1xh9
- Converting a budget-only red to a pass inside `suite_cache`: the gate is already demoted by `ytz6z4`, and an explicit `AW_CORE_BUDGET_ENFORCE=1` caller asked for enforcement (`test_gate_suite_honors_explicit_enforce`), so the verdict stays and only the explanation changes.
  - Carrier-Declined: deliberate decision recorded in OQ-02; the existing contract test pins the explicit-enforce verdict, so no work is outstanding.

## Scope check

- Over-scope: none.
- Under-scope: none; every surface that reports the budget failure (pytest banner, suite helper reason, runner send-back) and every doc that states the enforcement rule is covered.

## Required tests / validation

- `tests/test_core_tier_selection.py` (new load tests plus existing ones), `tests/test_suite_cache.py` (new predicate and end-to-end tests), new `tests/test_combined_red_failure_lines.py`, unchanged `tests/test_hook_and_suite_fix_it.py`; then the bare core tier, `aw check`, and `aw sanitize --agent`. Actual runner output must be pasted in each `V-*`.

## Spec / documentation sync

- No `.spec.md` governs the core-tier budget (the rule lives in plan `hguae9` and in `pyproject.toml`/`CONTRIBUTING.md`), so no spec is amended. `pyproject.toml`, `CONTRIBUTING.md` and `CHANGELOG.md` are updated in E-items of task group 4. The repo-local AGENTS.md section says only "budgeted under 30s wall time on 6 workers", which stays true, so it is not edited.

## Open questions

### OQ-01: What load threshold demotes the budget?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence: demote when the 1-minute load average exceeds the CPU count. The suite alone contributes about 6 on the 12-CPU reference host (F-5), so the threshold trips only when outside work at least doubles the suite's own demand; the failing measurements in `m8d13e` were at load 26-31, well above 12, while the passing median of 27.13s in plan `hguae9` was measured on a quiet host. The value is one comparison in one hook and is trivially adjustable after review. Re-measured at review on the 12-CPU host: a bare core run (`AW_CORE_BUDGET_ENFORCE=0`) started at 1-minute load 9.82, ended at 14.22, and took 75.10s for 753 passed, so the threshold demotes exactly such a run while a run on a quiet host (load below 12) is still enforced. Known limit: the 1-minute average is read at session end and includes the suite's own contribution, so it is a proxy for contention, not a measurement of it.

### OQ-02: Should a budget-only red become a pass in `suite_cache`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Resolved from the existing contract test `test_gate_suite_honors_explicit_enforce` in `tests/test_core_tier_selection.py`, which pins that an explicit enforce request still fails at the gate. This plan only names the cause.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff conftest.py` showing the load read, the unknown fallback, the demotion condition, the load banner line and the `Core tier budget not enforced:` marker; plus the pasted banner and `echo "exit=$?"` output of two manual over-budget bare runs in the real repo (code path: `conftest.pytest_sessionfinish`, reached on the controller via the `tests/deselect_notice.py` relay): `AW_CORE_BUDGET_SECONDS=1 AW_TEST_CPU_COUNT=12 AW_CORE_BUDGET_ENFORCE=1 AW_TEST_LOADAVG=99 python3 -m pytest` showing `exit=0`, `WARNING:`, the load line and the marker; then the same command with `AW_TEST_LOADAVG=1` showing `exit=1`, the load line and no marker.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_core_tier_selection.py` showing the new load tests (high load warns and exits 0 with the marker, low load fails without it, unparseable load reports `unknown` and fails) and every pre-existing test PASSED, with the final `N passed` line; plus the `git diff tests/test_core_tier_selection.py` hunk showing `_clean_env` pinning `AW_TEST_LOADAVG`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff agent_workflows/suite_cache.py` showing `CORE_BUDGET_BANNER`, `CORE_BUDGET_NOT_ENFORCED_MARKER`, `is_budget_only_failure(exit_code, stdout, stderr, failures)`, and the budget-only `reason` branch, with the `passed = exit_code == 0` line and the cached-serve branch unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_suite_cache.py -k budget` listing each new predicate case, the end-to-end budget-only `run_full_suite` test and its failing-test control PASSED (code path: `suite_cache.run_full_suite` on a temp project), plus the `N passed` line of `python3 -m pytest -o addopts="" tests/test_suite_cache.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff agent_workflows/runner_shared.py` showing `combined_red_failure_lines` and the send-back loop calling it, with the literal `no test ids recorded` removed and no other send-back text changed.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_combined_red_failure_lines.py tests/test_hook_and_suite_fix_it.py` with all four new cases and every existing send-back test PASSED.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted `git diff pyproject.toml CONTRIBUTING.md CHANGELOG.md` showing only the load-threshold wording and one `- Fixed:` line, and pasted output of `grep -nP '[\x{2013}\x{2014}]'` on the added CHANGELOG/CONTRIBUTING lines returning nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted tail of the bare `python3 -m pytest` run (its `N passed` summary line with zero failed, and `echo "exit=$?"`). If that run exits 1 with the enforced budget banner (which after E-01 carries the load line), paste the banner and repeat the run once with `AW_CORE_BUDGET_ENFORCE=0`, pasting its tail and `exit=0`, which proves the exit was the budget and not a test; any FAILED or ERROR line is a fail. Also: the tail of the explicit four-file run; the `aw check --agent` diagnostic rule ids compared with the same command run on the plan's base commit (in a throwaway `git worktree add /tmp/opencode/44nfmd-base <base>`) showing no new error rule id; and the `aw sanitize --agent` result record with outcome pass.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`); every open question is resolved. Follow the execution contract in AGENTS.md: commit only files you changed, through `aw commit 44nfmd -- <paths>`, never `git add -A`, and never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; if an out-of-scope edit proves necessary, make it and justify it (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path). Lifecycle: the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
