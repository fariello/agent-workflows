# IPD: Make the core-tier wall-time budget load-aware and name a budget-only red in suite reports

- Date: 2026-10-17
- Kind: child
- Concern: The core-tier wall-time budget guard in the root `conftest.py` turns an all-green test run into exit 1 when the host is loaded, and when that exit reaches a runner the operator and the agent are told the suite was RED with "no test ids recorded", which names no cause and gives nothing to fix.
- Scope: (1) Make the conftest budget guard demote an overrun to a warning when the host is measurably oversubscribed (1-minute load average above the CPU count), and print the measured load in the budget banner either way; (2) make `suite_cache.run_full_suite` report a nonzero exit whose only cause is the budget banner as a budget-only failure in its `reason` instead of a generic "suite FAILED"; (3) replace the runner's combined-red send-back text "no test ids recorded" with a sentence that states the recorded revalidation reason, through one small helper; (4) behavioral tests for all three; (5) sync the budget comment in `pyproject.toml`, the `CONTRIBUTING.md` suite paragraph, and a CHANGELOG `Fixed` line. It does NOT change the 30s budget value, the core marker membership, or the `ytz6z4` runner-side demotion already shipped in `8b798b0b8`.
- Scope-Paths: conftest.py, tests/test_core_tier_selection.py, agent_workflows/suite_cache.py, tests/test_suite_cache.py, agent_workflows/runner_shared.py, tests/test_combined_red_failure_lines.py, pyproject.toml, CONTRIBUTING.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
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

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 44nfmd verified (set 48hjbx, attempt 1).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 fixed (review record `.aw/records/reviews/20261017-48hjbx-01-44nfmd-make-the-core-tier-wall-time-budget-load-aware-and-name-a-bu.review.md`).
- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-17 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog 48hjbx with Step 0 evidence; review-ready.

## Goal

A core-tier run in which every test passes must not be reported as a failure merely because other work on the host slowed it down, and when the budget does fail a run, every report a human or agent reads (the pytest banner, the suite helper's `reason`, the runner's combined-red send-back) must say that the budget, not a test, was the cause.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: load-aware budget guard (conftest)

- [x] E-01 In the root `conftest.py` `pytest_sessionfinish` budget hook (the function whose docstring reads "Enforce the wall-time budget on the core tier (IPD hguae9 E-05)"), read the 1-minute load average with `os.getloadavg()[0]` (overridable by a new env `AW_TEST_LOADAVG` for tests, mirroring the existing `AW_TEST_CPU_COUNT` override; an `AW_TEST_LOADAVG` that does not parse as a float, or `OSError`/`AttributeError` from `os.getloadavg`, means "unknown", and unknown keeps today's enforcement). Read it only inside the over-budget branch. When over budget AND enforcement would otherwise apply (`cpu_count >= 12` and `AW_CORE_BUDGET_ENFORCE != "0"`), demote the failure to the existing `WARNING:` banner if the load average is known and greater than `cpu_count`. In both the failing and the warning banner add one line `Host 1-minute load average: <x:.2f> on <n> CPUs` (or `Host 1-minute load average: unknown on <n> CPUs`). In EVERY warning case (and never in the failing case) add one line beginning with the exact marker `Core tier budget not enforced:` followed by the reason that applies (`AW_CORE_BUDGET_ENFORCE=0`; `fewer than 12 CPUs`; or `host oversubscribed (1-minute load average above the CPU count)`). Keep the exact `CORE TIER BUDGET EXCEEDED` banner text; E-03 keys on the banner and on the absence of that marker.
  - Depends on: none
  - Expected outcome: an over-budget core run with `AW_TEST_LOADAVG` above the CPU count exits 0 with the warning banner, the load line and the `Core tier budget not enforced:` marker; with `AW_TEST_LOADAVG` at or below the CPU count (or unparseable) it exits 1 as today, printing the load line and no marker.
  - Execution state: performed

- [x] E-02 Update the hook copy `CONFTEST_HOOKS` in `tests/test_core_tier_selection.py` to match E-01, and make `_clean_env` default `AW_TEST_LOADAVG` to `"0"` (still overridable by its keyword arguments) so EVERY existing test in the file, including `_gate_env` users `test_gate_suite_passes_an_all_green_over_budget_tree` and `test_gate_suite_honors_explicit_enforce`, is independent of the live host load (measured at review: the 1-minute load on the 12-CPU host read 14.22 at the end of a bare core run, which would otherwise flip `test_gate_suite_honors_explicit_enforce` to a pass). Add behavioral subprocess tests in that file (it is `core`-marked) driving the temp project with `AW_CORE_BUDGET_SECONDS=0.01`, `AW_TEST_CPU_COUNT=12`, `AW_CORE_BUDGET_ENFORCE=1`: (a) `AW_TEST_LOADAVG=30` exits 0 and the combined output contains `WARNING:`, `CORE TIER BUDGET EXCEEDED`, `load average: 30.00` and `Core tier budget not enforced:`; (b) `AW_TEST_LOADAVG=2` exits nonzero, contains the banner and `load average: 2.00`, and does not contain `Core tier budget not enforced:`; (c) `AW_TEST_LOADAVG=not-a-number` exits nonzero and contains `load average: unknown`.
  - Depends on: E-01
  - Expected outcome: the new tests and every existing test in `tests/test_core_tier_selection.py` pass independent of the real host load.
  - Execution state: performed

### Task group 2: name a budget-only failure in suite reports

- [x] E-03 In `agent_workflows/suite_cache.py`, add a module constant `CORE_BUDGET_BANNER = "CORE TIER BUDGET EXCEEDED"` and a module constant `CORE_BUDGET_NOT_ENFORCED_MARKER = "Core tier budget not enforced:"` (the E-01 marker), and a pure function `is_budget_only_failure(exit_code, stdout, stderr, failures) -> bool` that is True only when `exit_code == 1`, `failures` is empty, `CORE_BUDGET_BANNER` appears in stdout or stderr, and `CORE_BUDGET_NOT_ENFORCED_MARKER` appears in neither (an enforced banner never carries the marker, so a warned overrun beside some other exit-1 cause is not misnamed). Plan `sa629y` (backlog `o58dro`) reuses this predicate by that exact name and signature, so neither may change. A cached failure is stored only after `_confirm_failing_node_ids` re-runs parsed node ids, which a budget-only run has none of, so the cached-serve branch of `run_full_suite` needs no change. In `run_full_suite`, in the generic nonzero-exit branch that builds `reason = f"suite FAILED with exit {exit_code} in ..."`, use instead `f"suite FAILED with exit {exit_code} in {checkout_path} ONLY on the core-tier wall-time budget (no test failed; {summary or 'no summary line parsed'})"` when that predicate holds. `passed` stays False: this plan names the cause, it does not convert the verdict (the gate path already defaults enforcement off via `build_suite_child_env`, backlog `ytz6z4`).
  - Depends on: none
  - Expected outcome: a run whose only failure is the enforced budget carries a `reason` naming the budget; any run with a real failing test keeps today's reason unchanged.
  - Execution state: performed

- [x] E-04 Add behavioral tests to `tests/test_suite_cache.py`: (a) unit tests of `is_budget_only_failure` over synthetic outputs (banner + exit 1 + no failures -> True; banner + a `FAILED tests/x.py::t` line -> False; exit 0 -> False; banner carrying the `Core tier budget not enforced:` marker with exit 1 -> False; exit 2 with the banner -> False); (b) one end-to-end `run_full_suite` call on a temp project built the same way as `tests/test_core_tier_selection.py::temp_project` (write its conftest from `tests.test_core_tier_selection.CONFTEST_HOOKS` by import rather than a third copy of the hook; argv `[sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-n", "0"]`, `use_cache=False`) with `AW_CORE_BUDGET_ENFORCE=1`, `AW_CORE_BUDGET_SECONDS=0.01`, `AW_TEST_CPU_COUNT=12`, `AW_TEST_LOADAVG=1` passed via `env=tests.test_core_tier_selection._gate_env(AW_CORE_BUDGET_ENFORCE="1", AW_TEST_LOADAVG="1")` (the helper already pops `AW_SUITE_SLOT_HELD` and the xdist/tier variables), asserting `not res.passed`, `res.exit_code == 1`, `res.failures == ()` and `"wall-time budget" in res.reason`; plus a control on the same project with a deliberately failing core test, asserting the reason does NOT contain `wall-time budget`. Every new test name contains `budget` so V-04's `-k budget` selects them.
  - Depends on: E-01, E-03
  - Expected outcome: the new tests pass and assert on the returned `SuiteRunResult`, not on source text.
  - Execution state: performed

### Task group 3: combined-red send-back names the cause

- [x] E-05 In `agent_workflows/runner_shared.py`, extract the failing-test text built inside the combined-red send-back loop (the block that today assigns `fail_lines = ... else "no test ids recorded"`, beside the `combined-red-sent-back` event) into a module-level pure helper `combined_red_failure_lines(revalidation: Mapping[str, Any]) -> str`. It returns the bulleted `new_ids` (else `failures`) exactly as today when any exist; when none exist it returns `"no failing test id was recorded; the recorded revalidation reason was: <reason>"` using `revalidation["reason"]` (or `"(no reason recorded)"` when that key is absent or empty). It must tolerate a missing or `None` `baseline_comparison`, exactly as the inline code does today (`pre_rev.get("baseline_comparison") or {}`). Call it from the loop, passing the same `pre_rev` mapping, so the send-back prompt and its behavior are otherwise unchanged. The recorded `reason` reaches this point unmodified from `suite_cache.run_full_suite` through `runner_shared.run_suite_check` (`reason=res.reason`), the `measurement["reason"]` in `make_integration_validation_runner`, `_relative_revalidation_verdict` (which only prefixes or suffixes it) and `_record_revalidation` (`"reason": reason`), which is why E-03's wording becomes visible here.
  - Depends on: E-03
  - Expected outcome: an agent receiving a combined-red send-back with no ids reads the revalidation reason, which after task group 2 names the budget when that is the cause.
  - Execution state: performed

- [x] E-06 Add `tests/test_combined_red_failure_lines.py` (module `pytestmark = pytest.mark.core`) calling `runner_shared.combined_red_failure_lines` with: a record carrying `baseline_comparison.new_ids` (asserts each id appears as a `- ` bullet and the old-ids are not listed); a record with only `failures` and `baseline_comparison: None`; a record with neither and `reason` naming the budget (asserts the reason text appears and the string `no test ids recorded` does not); and an empty mapping (asserts `(no reason recorded)`). Also run the existing send-back test `tests/test_hook_and_suite_fix_it.py` unchanged to show the populated-id path is preserved.
  - Depends on: E-05
  - Expected outcome: new tests pass; `tests/test_hook_and_suite_fix_it.py` passes unchanged.
  - Execution state: performed

### Task group 4: documentation sync and suite run

- [x] E-07 Sync the three documents that state the enforcement rule to the shipped behavior, one edit each: in `pyproject.toml`, the `[tool.pytest.ini_options]` header comment and the `core` marker comment (both read "enforced on >=12 CPUs / 6 workers; escape with AW_CORE_BUDGET_ENFORCE=0") gain "not enforced when the 1-minute load average exceeds the CPU count"; the `CONTRIBUTING.md` suite paragraph (beginning "`make test` (or bare `python3 -m pytest`) runs the core test tier") gains one sentence saying the same and that the budget banner prints the measured load; and the pending 2.0.0 section of `CHANGELOG.md` gains one `- Fixed:` bullet beside the existing `- Fixed:` bullets, in plain user-facing language with no em or en dashes, covering both the load-aware budget and the named cause in suite and runner reports.
  - Depends on: E-01
  - Expected outcome: the three files describe the shipped behavior; `git diff` touches only those lines.
  - Execution state: performed

- [x] E-08 Run the bare core tier `python3 -m pytest` and the touched test files explicitly (`python3 -m pytest tests/test_core_tier_selection.py tests/test_suite_cache.py tests/test_combined_red_failure_lines.py tests/test_hook_and_suite_fix_it.py`), plus `aw check --agent` on the changed tree and on the plan's base commit (a throwaway worktree under `/tmp/opencode`) for comparison, and `aw sanitize --agent`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: all pass; no new `aw check` or sanitizer finding.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: pasted `git diff conftest.py` showing the load read, the unknown fallback, the demotion condition, the load banner line and the `Core tier budget not enforced:` marker; plus the pasted banner and `echo "exit=$?"` output of two manual over-budget bare runs in the real repo (code path: `conftest.pytest_sessionfinish`, reached on the controller via the `tests/deselect_notice.py` relay): `AW_CORE_BUDGET_SECONDS=1 AW_TEST_CPU_COUNT=12 AW_CORE_BUDGET_ENFORCE=1 AW_TEST_LOADAVG=99 python3 -m pytest` showing `exit=0`, `WARNING:`, the load line and the marker; then the same command with `AW_TEST_LOADAVG=1` showing `exit=1`, the load line and no marker.
  - Observed evidence: PASS. Load read, unknown fallback, demotion condition, load banner line, marker, and manual runs verified.
    `git diff conftest.py`:
    ```diff
    diff --git a/conftest.py b/conftest.py
    index 48239c244..ef822cd16 100644
    --- a/conftest.py
    +++ b/conftest.py
    @@ -202,15 +202,50 @@ def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
                 f"  {idx + 1:2d}. {dur:6.2f}s  {nodeid}"
                 for idx, (dur, nodeid) in enumerate(slowest)
             )
    +        cpu_count = int(os.environ.get("AW_TEST_CPU_COUNT", str(os.cpu_count() or 1)))
    +        enforce = os.environ.get("AW_CORE_BUDGET_ENFORCE") != "0"
    +
    +        load_avg: float | None = None
    +        env_load = os.environ.get("AW_TEST_LOADAVG")
    +        if env_load is not None:
    +            try:
    +                load_avg = float(env_load)
    +            except ValueError:
    +                load_avg = None
    +        else:
    +            try:
    +                load_avg = os.getloadavg()[0]
    +            except (OSError, AttributeError):
    +                load_avg = None
    +
    +        if load_avg is not None:
    +            load_line = f"Host 1-minute load average: {load_avg:.2f} on {cpu_count} CPUs"
    +        else:
    +            load_line = f"Host 1-minute load average: unknown on {cpu_count} CPUs"
    +
    +        not_enforced_reason: str | None = None
    +        if not enforce:
    +            not_enforced_reason = "AW_CORE_BUDGET_ENFORCE=0"
    +        elif cpu_count < 12:
    +            not_enforced_reason = "fewer than 12 CPUs"
    +        elif load_avg is not None and load_avg > cpu_count:
    +            not_enforced_reason = "host oversubscribed (1-minute load average above the CPU count)"
    +
    +        not_enforced_line = (
    +            f"Core tier budget not enforced: {not_enforced_reason}\n"
    +            if not_enforced_reason
    +            else ""
    +        )
    +
             msg = (
                 f"\n================================ CORE TIER BUDGET EXCEEDED ================================\n"
                 f"Core tier wall time: {elapsed:.2f}s exceeded budget of {budget:.2f}s.\n"
    +            f"{load_line}\n"
    +            f"{not_enforced_line}"
                 f"Top 10 slowest core tests:\n{slowest_lines}\n"
                 f"===========================================================================================\n"
             )
    -        cpu_count = int(os.environ.get("AW_TEST_CPU_COUNT", str(os.cpu_count() or 1)))
    -        enforce = os.environ.get("AW_CORE_BUDGET_ENFORCE") != "0"
    -        if cpu_count >= 12 and enforce:
    +        if not_enforced_reason is None:
                 sys.stderr.write(msg)
                 session.exitstatus = 1
             else:
    ```
    Manual bare run 1 (`AW_CORE_BUDGET_SECONDS=1 AW_TEST_CPU_COUNT=12 AW_CORE_BUDGET_ENFORCE=1 AW_TEST_LOADAVG=99 python3 -m pytest; echo "exit=$?"`):
    ```
    WARNING:
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 94.84s exceeded budget of 1.00s.
    Host 1-minute load average: 99.00 on 12 CPUs
    Core tier budget not enforced: host oversubscribed (1-minute load average above the CPU count)
    Top 10 slowest core tests:
       1.   8.48s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
       2.   5.99s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
       3.   5.66s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
       4.   5.04s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
       5.   4.00s  tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_pytest_runs_without_xdist_plugin
       6.   3.90s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
       7.   3.67s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
       8.   3.55s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
       9.   2.43s  tests/test_status_set.py::TestScopePathCitationRewriteSetter::test_g_setter_spellings_rewrite_citing_pending_plan_and_skip_receipt_plan
      10.   2.40s  tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_backlog_item_typed_and_untyped_spellings
    ===========================================================================================

    NOTE: 7945 tests were deselected by core filter/-m/-k and did not run (default bare run selects 'core' and marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    ============================== SLOW TESTS REPORT ===============================
    WARNING: 2 test(s) exceeded 2s and are not listed in tests/slow_allowlist.txt:
        4.00s  tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_pytest_runs_without_xdist_plugin
        2.43s  tests/test_status_set.py::TestScopePathCitationRewriteSetter::test_g_setter_spellings_rewrite_citing_pending_plan_and_skip_receipt_plan
    810 passed in 94.83s (0:01:34)
    exit=0
    ```
    Manual bare run 2 (`AW_CORE_BUDGET_SECONDS=1 AW_TEST_CPU_COUNT=12 AW_CORE_BUDGET_ENFORCE=1 AW_TEST_LOADAVG=1 python3 -m pytest; echo "exit=$?"`):
    ```
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 34.82s exceeded budget of 1.00s.
    Host 1-minute load average: 1.00 on 12 CPUs
    Top 10 slowest core tests:
       1.   9.96s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
       2.   5.68s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
       3.   5.44s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
       4.   4.28s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
       5.   3.79s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
       6.   3.41s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
       7.   3.22s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
       8.   2.59s  tests/test_local_leaks.py::ThisRepoTests::test_this_repo_working_tree_is_clean
       9.   2.13s  tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_backlog_item_typed_and_untyped_spellings
      10.   1.83s  tests/test_status_set.py::TestScopePathCitationRewriteSetter::test_g_setter_spellings_rewrite_citing_pending_plan_and_skip_receipt_plan
    ===========================================================================================

    NOTE: 7945 tests were deselected by core filter/-m/-k and did not run (default bare run selects 'core' and marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    810 passed in 34.80s
    exit=1
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_core_tier_selection.py` showing the new load tests (high load warns and exits 0 with the marker, low load fails without it, unparseable load reports `unknown` and fails) and every pre-existing test PASSED, with the final `N passed` line; plus the `git diff tests/test_core_tier_selection.py` hunk showing `_clean_env` pinning `AW_TEST_LOADAVG`.
  - Observed evidence: PASS. Core tier selection unit tests pass with load average pinning and overrides verified.
    `python3 -m pytest -o addopts="" -v tests/test_core_tier_selection.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=1739527687
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/44nfmd
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 11 items                                                            collected 11 items

    tests/test_core_tier_selection.py::test_budget_exceeded_high_load_warns_and_demotes PASSED [  9%]
    tests/test_core_tier_selection.py::test_budget_exceeded_unparseable_load_fails PASSED [ 18%]
    tests/test_core_tier_selection.py::test_gate_suite_passes_an_all_green_over_budget_tree[run-evidence] PASSED [ 27%]
    tests/test_core_tier_selection.py::test_gate_suite_honors_explicit_enforce PASSED [ 36%]
    tests/test_core_tier_selection.py::test_budget_exceeded_enforced_fails PASSED [ 45%]
    tests/test_core_tier_selection.py::test_budget_exceeded_enforce_zero_warns PASSED [ 54%]
    tests/test_core_tier_selection.py::test_explicit_path_runs_non_core PASSED [ 63%]
    tests/test_core_tier_selection.py::test_bare_run_selects_core_only PASSED [ 72%]
    tests/test_core_tier_selection.py::test_gate_suite_passes_an_all_green_over_budget_tree[subprocess] PASSED [ 81%]
    tests/test_core_tier_selection.py::test_budget_exceeded_low_load_fails PASSED [ 90%]
    tests/test_core_tier_selection.py::test_thorough_env_runs_all PASSED     [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== 11 passed in 9.10s ==============================
    ```
    `git diff tests/test_core_tier_selection.py` (`_clean_env` hunk):
    ```diff
    @@ -117,6 +147,7 @@ def _clean_env(**overrides: str) -> dict[str, str]:
         env = dict(os.environ)
         env.pop("PYTEST_XDIST_WORKER", None)
         env.pop("AW_TEST_TIER", None)
    +    env["AW_TEST_LOADAVG"] = "0"
         env.update(overrides)
         return env
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git diff agent_workflows/suite_cache.py` showing `CORE_BUDGET_BANNER`, `CORE_BUDGET_NOT_ENFORCED_MARKER`, `is_budget_only_failure(exit_code, stdout, stderr, failures)`, and the budget-only `reason` branch, with the `passed = exit_code == 0` line and the cached-serve branch unchanged.
  - Observed evidence: PASS. Suite cache budget-only failure predicate and reason reporting implemented and verified.
    `git diff agent_workflows/suite_cache.py`:
    ```diff
    diff --git a/agent_workflows/suite_cache.py b/agent_workflows/suite_cache.py
    index 71014f0a4..3020f127c 100644
    --- a/agent_workflows/suite_cache.py
    +++ b/agent_workflows/suite_cache.py
    @@ -142,6 +142,32 @@ def extract_failing_node_ids(failures: Sequence[str]) -> Tuple[str, ...]:
         return tuple(seen)


    +CORE_BUDGET_BANNER: str = "CORE TIER BUDGET EXCEEDED"
    +CORE_BUDGET_NOT_ENFORCED_MARKER: str = "Core tier budget not enforced:"
    +
    +
    +def is_budget_only_failure(
    +    exit_code: int,
    +    stdout: str,
    +    stderr: str,
    +    failures: Sequence[str],
    +) -> bool:
    +    """Return True if exit_code is 1, failures is empty, banner is present, and not-enforced marker is absent."""
    +    if exit_code != 1:
    +        return False
    +    if failures:
    +        return False
    +    out = stdout or ""
    +    err = stderr or ""
    +    banner_present = (CORE_BUDGET_BANNER in out) or (CORE_BUDGET_BANNER in err)
    +    if not banner_present:
    +        return False
    +    marker_present = (CORE_BUDGET_NOT_ENFORCED_MARKER in out) or (
    +        CORE_BUDGET_NOT_ENFORCED_MARKER in err
    +    )
    +    return not marker_present
    +
    +
     class SuiteKey:
         """Result of `suite_key(checkout, argv)`.

    @@ -1582,6 +1608,11 @@ def run_full_suite(
                     f"suite could not be executed in {checkout_path} (exit 127); "
                     "treated as a failure (fail-closed)"
                 )
    +        elif is_budget_only_failure(exit_code, stdout, stderr, failures):
    +            reason = (
    +                f"suite FAILED with exit {exit_code} in {checkout_path} "
    +                f"ONLY on the core-tier wall-time budget (no test failed; {summary or 'no summary line parsed'})"
    +            )
             else:
                 reason = (
                     f"suite FAILED with exit {exit_code} in {checkout_path} "
    ```
    `passed = exit_code == 0` (line 1571 / 1597) and cached-serve branch (lines 1437-1469) remain completely unchanged.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_suite_cache.py -k budget` listing each new predicate case, the end-to-end budget-only `run_full_suite` test and its failing-test control PASSED (code path: `suite_cache.run_full_suite` on a temp project), plus the `N passed` line of `python3 -m pytest -o addopts="" tests/test_suite_cache.py`.
  - Observed evidence: PASS. Suite cache unit tests and end-to-end temp project tests pass.
    `python3 -m pytest -o addopts="" -v tests/test_suite_cache.py -k budget`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=422710496
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/44nfmd
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 17 items / 10 deselected / 7 selected

    tests/test_suite_cache.py::test_is_budget_only_failure_banner_exit_1_no_failures PASSED [ 14%]
    tests/test_suite_cache.py::test_is_budget_only_failure_exit_2_with_banner PASSED [ 28%]
    tests/test_suite_cache.py::test_run_full_suite_budget_only_failure_names_budget_in_reason PASSED [ 42%]
    tests/test_suite_cache.py::test_is_budget_only_failure_exit_0 PASSED     [ 57%]
    tests/test_suite_cache.py::test_is_budget_only_failure_with_not_enforced_marker PASSED [ 71%]
    tests/test_suite_cache.py::test_is_budget_only_failure_with_failing_test_line PASSED [ 85%]
    tests/test_suite_cache.py::test_run_full_suite_budget_control_with_failing_test PASSED [100%]

    NOTE: 10 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ======================= 7 passed, 10 deselected in 1.87s =======================
    ```
    `python3 -m pytest -o addopts="" tests/test_suite_cache.py`:
    ```
    ============================= 17 passed in 50.25s ==============================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `git diff agent_workflows/runner_shared.py` showing `combined_red_failure_lines` and the send-back loop calling it, with the literal `no test ids recorded` removed and no other send-back text changed.
  - Observed evidence: PASS. Runner shared combined red failure lines helper extracted and wired cleanly.
    `git diff agent_workflows/runner_shared.py`:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index d893137e6..1bd312d88 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -30394,6 +30394,19 @@ def revalidation_was_unmeasured(item: Mapping[str, Any]) -> bool:
         return record.get("measured") is False


    +def combined_red_failure_lines(revalidation: Mapping[str, Any]) -> str:
    +    """Format failing test lines for a combined-red send-back prompt."""
    +    base_comp = revalidation.get("baseline_comparison") or {}
    +    new_ids = base_comp.get("new_ids")
    +    failures = new_ids if new_ids else (revalidation.get("failures") or [])
    +    if failures:
    +        return "\n".join(f"- {f}" for f in failures)
    +    reason = str(revalidation.get("reason") or "").strip()
    +    if not reason:
    +        reason = "(no reason recorded)"
    +    return f"no failing test id was recorded; the recorded revalidation reason was: {reason}"
    +
    +
     SPEC_REVIEW_REFUSAL_CODE: str = "spec-review-refused"


    @@ -43653,16 +43666,7 @@ def execute_item_core(
                                 )

                                 pre_rev = item.get(REVALIDATION_CACHE_KEY) or {}
    -                            base_comp = pre_rev.get("baseline_comparison") or {}
    -                            new_ids = base_comp.get("new_ids")
    -                            failures = (
    -                                new_ids if new_ids else (pre_rev.get("failures") or [])
    -                            )
    -                            fail_lines = (
    -                                "\n".join(f"- {f}" for f in failures)
    -                                if failures
    -                                else "no test ids recorded"
    -                            )
    +                            fail_lines = combined_red_failure_lines(pre_rev)
                                 merged_files = (
                                     pre_rev.get("merged_files")
                                     or pre_rev.get("files")
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_combined_red_failure_lines.py tests/test_hook_and_suite_fix_it.py` with all four new cases and every existing send-back test PASSED.
  - Observed evidence: PASS. Combined red failure lines unit tests and hook fix-it tests pass.
    `python3 -m pytest -o addopts="" -v tests/test_combined_red_failure_lines.py tests/test_hook_and_suite_fix_it.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=596899192
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/44nfmd
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 4 items                                                             collected 14 items

    tests/test_combined_red_failure_lines.py::test_combined_red_failure_lines_empty_mapping PASSED [  7%]
    tests/test_combined_red_failure_lines.py::test_combined_red_failure_lines_with_only_failures_and_none_baseline PASSED [ 14%]
    tests/test_combined_red_failure_lines.py::test_combined_red_failure_lines_with_baseline_comparison_new_ids PASSED [ 21%]
    tests/test_combined_red_failure_lines.py::test_combined_red_failure_lines_without_ids_and_budget_reason PASSED [ 28%]
    tests/test_hook_and_suite_fix_it.py::UnitHookAndSuiteFixItTests::test_v01_finalize_refusal_is_retryable_positive_and_diagnosis_negative PASSED [ 35%]
    tests/test_hook_and_suite_fix_it.py::UnitHookAndSuiteFixItTests::test_v01_extract_hook_finalize_output_and_notice PASSED [ 42%]
    tests/test_hook_and_suite_fix_it.py::UnitHookAndSuiteFixItTests::test_v04_per_kind_counters_and_exhaustion_unit PASSED [ 50%]
    tests/test_hook_and_suite_fix_it.py::UnitHookAndSuiteFixItTests::test_v02_tag_integration_hook_refusals_unit PASSED [ 57%]
    tests/test_hook_and_suite_fix_it.py::DriverHookAndSuiteFixItTests::test_v04_e04_budget_zero_and_exhaustion_with_kind_naming PASSED [ 64%]
    tests/test_hook_and_suite_fix_it.py::DriverHookAndSuiteFixItTests::test_v03_e03_combined_red_sendback_and_warning_on_out_of_scope PASSED [ 71%]
    tests/test_hook_and_suite_fix_it.py::DriverHookAndSuiteFixItTests::test_v03_e03_unmeasured_revalidation_negative_not_sent_back PASSED [ 78%]
    tests/test_hook_and_suite_fix_it.py::DriverHookAndSuiteFixItTests::test_v06_e06_integration_hook_refusal_negative_no_session PASSED [ 85%]
    tests/test_hook_and_suite_fix_it.py::DriverHookAndSuiteFixItTests::test_v06_e06_integration_hook_refusal_sendback PASSED [ 92%]
    tests/test_hook_and_suite_fix_it.py::DriverHookAndSuiteFixItTests::test_v01_e01_hook_refusal_finalize_sendback_and_recovery PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================= 14 passed in 29.08s ==============================
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: pasted `git diff pyproject.toml CONTRIBUTING.md CHANGELOG.md` showing only the load-threshold wording and one `- Fixed:` line, and pasted output of `grep -nP '[\x{2013}\x{2014}]'` on the added CHANGELOG/CONTRIBUTING lines returning nothing.
  - Observed evidence: PASS. Documentation synced across pyproject.toml, CONTRIBUTING.md, and CHANGELOG.md without em/en dashes.
    `git diff pyproject.toml CONTRIBUTING.md CHANGELOG.md`:
    ~~~diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 1143e52e4..d79f25a73 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -31,6 +31,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
     - Added: `aw oc run` and `aw agy run` accept `--label` and `--review-variant`, and every run records the repository commit, working-tree state and toolkit version at start.
     - Added: a **Tokens and cost** dashboard tab showing in + out, input, output, cached and cache-write tokens separately, each with count, total, average, median and p90, plus their costs, overall and split by agent (host and model) or any other dimension.
     - Fixed: static type checking (`make typecheck`, CI "static type gate") passes again after three mypy errors in the comms broker, the installer engine and IPD authoring were fixed.
    +- Fixed: the core test tier wall-time budget now demotes to a warning when host load exceeds CPU count, prints the measured load in its banner, and is reported as a budget-only failure in suite and runner reports.
     - Fixed: `aw install --records-backend <new>` on an installed repository no longer silently leaves existing records where no reader looks: it refuses when records would be orphaned, and `--relocate` (with `--dry-run` preview, `--relocate-resume`, `--relocate-rollback`) moves them.
     - Fixed: `aw releases readiness` no longer reports a false `workflow_disposition` NO-GO in a managed repository that adds its own workflows.
     - Fixed: `aw work begin` no longer crashes on clean-delta installs (`completely-clean-target`, `local-only`) whose plans live outside the repository.
    diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
    index 7387a1909..03d6af844 100644
    --- a/CONTRIBUTING.md
    +++ b/CONTRIBUTING.md
    @@ -144,7 +144,7 @@ layout migration, pypi_links) or the workflow tools (`scan_secrets.py`, `run_che
     make test
     ```

    -`make test` (or bare `python3 -m pytest`) runs the core test tier (budgeted under 30s wall time on 6 workers) that covers every first-party module and declared leaf command. The core tier is the runner merge gate. Running an explicit path (e.g. `python3 -m pytest tests/test_foo.py` or `python3 -m pytest tests/`) runs everything non-slow in that path without marker deselection. Run `make test-all` or `aw suite --thorough` for the thorough tier (used before git push, in CI, and before release). Install the test dependencies with `pip install '.[test]'`.
    +`make test` (or bare `python3 -m pytest`) runs the core test tier (budgeted under 30s wall time on 6 workers) that covers every first-party module and declared leaf command. The core tier is the runner merge gate. The budget is not enforced when the 1-minute load average exceeds the CPU count, and the budget banner prints the measured load. Running an explicit path (e.g. `python3 -m pytest tests/test_foo.py` or `python3 -m pytest tests/`) runs everything non-slow in that path without marker deselection. Run `make test-all` or `aw suite --thorough` for the thorough tier (used before git push, in CI, and before release). Install the test dependencies with `pip install '.[test]'`.


     If you need the guaranteed no-dependency serial runner (for a minimal environment, or to
    diff --git a/pyproject.toml b/pyproject.toml
    index 686de7861..f54f5d7cf 100644
    --- a/pyproject.toml
    +++ b/pyproject.toml
    @@ -198,11 +198,12 @@ include = [
     # Bare `python3 -m pytest` runs the core behavioral regression tier in under 30s
     # (the runner merge gate; an explicit path runs everything non-slow it names).
     # Thorough tier: `make test-all` or `aw suite --thorough` (pre-push, CI, release).
    -# Wall-time budget: 30s (leaves ~10s margin for broadening; enforced on >=12 CPUs / 6 workers; escape with AW_CORE_BUDGET_ENFORCE=0).
    +# Wall-time budget: 30s (leaves ~10s margin for broadening; enforced on >=12 CPUs / 6 workers; not enforced when the 1-minute load average exceeds the CPU count; escape with AW_CORE_BUDGET_ENFORCE=0).
     testpaths = ["tests"]
     markers = [
         # Core tier: fast behavioral regression test run by bare pytest in under 30s
         # (wall-time budget: 30s, leaving ~10s margin for broadening; enforced on >=12 CPUs / 6 workers;
    +    # not enforced when the 1-minute load average exceeds the CPU count;
         # escape with AW_CORE_BUDGET_ENFORCE=0). Author-assigned; see CONTRIBUTING.
         "core: fast behavioral regression test run by a bare `pytest`; author-assigned; see CONTRIBUTING",
         "slow: heavy subprocess/integration tests (spawn the CLI, install into temp repos). Deselected by default for a fast per-run suite; run them with `make test-all` / `-m ''`.",
    ~~~
    `git diff pyproject.toml CONTRIBUTING.md CHANGELOG.md | grep -nP '[\x{2013}\x{2014}]'`:
    ```
    (empty - exit 1)
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: pasted tail of the bare `python3 -m pytest` run (its `N passed` summary line with zero failed, and `echo "exit=$?"`). If that run exits 1 with the enforced budget banner (which after E-01 carries the load line), paste the banner and repeat the run once with `AW_CORE_BUDGET_ENFORCE=0`, pasting its tail and `exit=0`, which proves the exit was the budget and not a test; any FAILED or ERROR line is a fail. Also: the tail of the explicit four-file run; the `aw check --agent` diagnostic rule ids compared with the same command run on the plan's base commit (in a throwaway `git worktree add /tmp/opencode/44nfmd-base <base>`) showing no new error rule id; and the `aw sanitize --agent` result record with outcome pass.
  - Observed evidence: PASS. Full bare test suite passes, 4 explicit files pass, aw check shows 0 new rules, aw sanitize clean.
    Tail of bare `python3 -m pytest; echo "exit=$?"`:
    ```
    NOTE: 7952 tests were deselected by core filter/-m/-k and did not run (default bare run selects 'core' and marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    817 passed in 30.00s
    exit=0
    ```
    Tail of explicit four-file run (`python3 -m pytest tests/test_core_tier_selection.py tests/test_suite_cache.py tests/test_combined_red_failure_lines.py tests/test_hook_and_suite_fix_it.py`):
    ```
    42 passed in 34.68s
    ```
    `aw check --agent` rule ids comparison with base commit `2c9ddbc53023a5589b799417bb2653b11ba61ba0`:
    Both runs emit the identical set of diagnostic rules (`check.lifecycle-transition-unvalidated`, `check.scope-drift`, `check.ipd-uncarried-obligation`, `check.ipd-carrier-finished-unverified`, `check.ipd-lint-diagnostic`, `check.spec-criteria-uncovered`, `check.graduation-incomplete`, `check.source-test-citation-dangling`, `check.system-layout-missing`, `check.identity-absent-from-name`). 0 new error rule IDs introduced.
    `aw sanitize --agent`:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5860,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`); every open question is resolved. Follow the execution contract in AGENTS.md: commit only files you changed, through `aw commit 44nfmd -- <paths>`, never `git add -A`, and never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; if an out-of-scope edit proves necessary, make it and justify it (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path). Lifecycle: the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
