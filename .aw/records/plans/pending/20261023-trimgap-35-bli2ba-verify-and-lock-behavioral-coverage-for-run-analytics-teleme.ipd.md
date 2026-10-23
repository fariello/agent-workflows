# IPD: Verify and lock behavioral coverage for run_analytics_telemetry sampler, probe-adapter and collector keys

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `zd8l04` (Set `trimgap`, carried from `lrnh5f` via plan `b83dpg`) carries eight production keys of `agent_workflows/run_analytics_telemetry.py` whose `wo21z5` `## Budget probe results` verdict is `budget-exhausted` (the probe ran out of its time budget at 11130.81s before trying them), so no mutation verdict was ever recorded: `ResourceSampler.__init__`, `ResourceSampler.start`, `ResourceSampler.stop` and `TelemetryCollector.__init__` (operator `raise`), and `SystemResourceProbeAdapter.accelerators`, `SystemResourceProbeAdapter.disk`, `TelemetryCollector._emit` and `TelemetryCollector._observe_accelerators` (operator `return-none`). The `wo21z5` `## Probe queue` names the deleted control file `tests/test_run_analytics_telemetry.py` for every one of them; that file was restored by executed plan `8bhcd3` (commit `cbf70e39a`, 2026-10-17 19:34), which is NOT an ancestor of the `wo21z5` baseline HEAD `f3afece9` (F-01). Probing all eight at authoring HEAD `bc36f0175` shows every mutant KILLED under the routine `-m core` selection (F-02). The residual risk this plan closes is that no verdict is recorded, so the backlog item still reads as an open coverage gap.
- Scope: Run the eight `tools/mutation_probe.py` probes (the backlog item's operators) against `tests/test_run_analytics_telemetry.py` under the routine `core` selection at execution HEAD, and record the verdicts in this plan. ONLY IF a probe SURVIVES at execution HEAD, add one behavioral test to `tests/test_run_analytics_telemetry.py` that calls the surviving function (directly or through its public caller) and asserts on its returned value, raised error, or written telemetry. EXCLUDES any production-code change; EXCLUDES other `run_analytics_telemetry.py` keys (owned by executed `8bhcd3`, pending `qpmq2o`, or other `trimgap` items); EXCLUDES other test files.
- Scope-Paths: tests/test_run_analytics_telemetry.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: zd8l04
- Set: trimgap
- Order: 35
- Highest E allocated: 03
- Author: opencode
- Id: bli2ba

## Workflow history

- 2026-10-23 reviewed (opencode): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (unsatisfiable exit-0 bar in E-03/V-03 on an enforcing host, F-05) and PR-002 (F-02 operator grouping) fixed; three probes re-run killed at `72da75876` (F-04)
- 2026-10-23 to-review (opencode): authored from backlog `zd8l04`. Confirmed `8bhcd3` restored the control file after the `wo21z5` baseline (`git merge-base --is-ancestor cbf70e39a f3afece925` exits 1), then ran `tools/mutation_probe.py` for all eight keys at HEAD `bc36f0175`; every mutant was killed (F-02). The plan is therefore verification-first with a conditional restore step, following siblings `qpmq2o` and `92tzo6`.
- 2026-10-23 draft (opencode): created.

## Goal

Prove, with recorded mutation-probe output at execution HEAD, that the backlog item's mutation of each of the eight `zd8l04` keys turns a routine core-tier test red, and add a behavioral test only for any key where that is not true. Done means all eight keys have a pasted `verdict: killed` under `-m core`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: probe at execution HEAD

- [ ] E-01 Before the first probe, record `git rev-parse HEAD` as `<base>`. Then run `python3 tools/mutation_probe.py --op <op> agent_workflows/run_analytics_telemetry.py::<key> -- -o addopts= -q -p no:randomly -m core tests/test_run_analytics_telemetry.py` for each pair: `raise` with `ResourceSampler.__init__`, `ResourceSampler.start`, `ResourceSampler.stop`, `TelemetryCollector.__init__`; `return-none` with `SystemResourceProbeAdapter.accelerators`, `SystemResourceProbeAdapter.disk`, `TelemetryCollector._emit`, `TelemetryCollector._observe_accelerators`. `tools/mutation_probe.py` mutates inside its own detached worktree of committed `HEAD`, so the checkout's production code is never modified. Record each `head:`, `verdict:`, `baseline_failing:`, `mutant_failing:` and `newly_failing` list in Findings. A probe with `baseline_failing` above 0 or a `verdict:` other than `killed`/`survived` (for example `error` or `invalid`) is not a result: record it, fix the cause if it is in scope, and re-run.
  - Depends on: none
  - Expected outcome: eight probe outputs recorded; at authoring all eight were `verdict: killed` (F-02).
  - Execution state: pending

### Task group 2: conditional restore

- [ ] E-02 For every key E-01 reports `survived`, add one test to `tests/test_run_analytics_telemetry.py` in the class that already covers that function (`SamplerTests` for `ResourceSampler.*`; `ProbeAdapterTests` for `SystemResourceProbeAdapter.disk`; `AcceleratorProbeTests` for `SystemResourceProbeAdapter.accelerators` and `TelemetryCollector._observe_accelerators`; `CollectorLifecycleTests` for `TelemetryCollector.__init__` and `TelemetryCollector._emit`) and assert on the returned value, the raised error, or the JSONL events the collector writes; mine the body from `git show 19313eed^:tests/test_run_analytics_telemetry.py` where an equivalent test exists. Commit the test file through `aw commit bli2ba -- tests/test_run_analytics_telemetry.py` BEFORE re-running the E-01 probe for that key, because the probe sees only committed `HEAD`; then re-run it. If E-01 reported `killed` for all eight keys, make NO file change and record "no survivor; no edit" in Findings.
  - Depends on: E-01
  - Expected outcome: either no diff to `tests/test_run_analytics_telemetry.py`, or a diff adding only tests, after which the re-probe of each previously surviving key (with `head:` at or after that commit) reports `baseline_failing: 0`, `verdict: killed`, and a `newly_failing` list naming the added test.
  - Execution state: pending

- [ ] E-03 Run the routine bare gate `python3 -m pytest` and confirm it passes with `tests/test_run_analytics_telemetry.py` in the core selection. The conftest budget check (`conftest.pytest_sessionfinish`) sets exit 1 on a wall-time overrun only when enforced and otherwise prints a warning; the core tier already exceeded 30s on this host before this plan (sibling `qpmq2o` E-03 cites 34.68s measured by the `f6el0l` review). On a host with 12 or more CPUs and a 1-minute load average at or below the CPU count the overrun IS enforced, so the bare run can exit 1 with every test passing (review measured exactly that at `72da75876`, F-05). So paste any `CORE TIER BUDGET EXCEEDED` block verbatim and do not count it against this item unless E-02 added a test that is among the block's listed slowest tests.
  - Depends on: E-02
  - Expected outcome: the bare run's summary line shows `passed` with no `failed` or `error`, and it either exits 0 or exits 1 solely because of an enforced `CORE TIER BUDGET EXCEEDED` block (no `Core tier budget not enforced` line) whose listed slowest tests include no test added by E-02. Any other non-zero exit is a failure of this item.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"): any test E-02 adds calls the function and asserts on outputs, raised errors or written events; no source reading.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items. `tests/test_run_analytics_telemetry.py` carries a module-level `pytestmark = pytest.mark.core`, so every test in it is in the routine gate, and a new test added there inherits the marking.
- Probe tool: `tools/mutation_probe.py` (`--op {return-none,return-true,return-false,negate-return,raise}`, selection after `--`) is the same tool `wo21z5` used, so the verdicts are directly comparable with the queue's operators.
- Sibling precedent: pending `qpmq2o` (backlog `gmfupc`) applies the same verify-first shape to four other keys of this module; executed `8bhcd3` restored `tests/test_run_analytics_telemetry.py` from `19313eed^`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `wo21z5` `## Probe queue` rows for the eight keys (control `tests/test_run_analytics_telemetry.py`, priority `P2`) and `## Budget probe results` rows (`budget-exhausted`, "budget exhausted at 11130.81s"); `wo21z5` `## Baseline` `head: f3afece925f521dd5a6e930e02b584a2c08cf950`; `git log -1 cbf70e39a` (2026-10-17 19:34, `work(8bhcd3): Restore behavioral test coverage for run_analytics_telemetry`); `git merge-base --is-ancestor cbf70e39a f3afece925` exits 1 | No verdict was ever produced for these keys, and their named control file was restored after the probe baseline. The open gap is unmeasured rather than demonstrated. |
| F-02 | `tools/mutation_probe.py` at HEAD `bc36f0175`, selection `-o addopts= -q -p no:randomly -m core tests/test_run_analytics_telemetry.py` | All eight `verdict: killed`, `baseline_failing: 0`. `mutant_failing` under `raise`: `ResourceSampler.__init__` 13, `ResourceSampler.start` 6, `ResourceSampler.stop` 8, `TelemetryCollector.__init__` 30. Under `return-none`: `SystemResourceProbeAdapter.accelerators` 7, `SystemResourceProbeAdapter.disk` 2, `TelemetryCollector._emit` 18, `TelemetryCollector._observe_accelerators` 27. |
| F-03 | Same as F-02, `newly_failing` for `SystemResourceProbeAdapter.disk` | Killed by exactly two tests, `ProbeAdapterTests::test_a_denied_probe_degrades_to_a_structured_reason_rather_than_raising` and `ProbeAdapterTests::test_real_adapter_probes_this_machine_without_raising` (about 8s wall). It is the thinnest of the eight; E-02 is the remedy only if those tests are lost before execution. |
| F-04 | `/plan-review` re-run of `tools/mutation_probe.py` at HEAD `72da75876`, same selection, for a sample of three keys | `SystemResourceProbeAdapter.disk` (`return-none`) killed, `mutant_failing: 2`; `TelemetryCollector._emit` (`return-none`) killed, 18; `ResourceSampler.stop` (`raise`) killed, 8; all `baseline_failing: 0`. F-02 reproduces for the sample; E-01 still re-probes all eight. |
| F-05 | `/plan-review` bare `python3 -m pytest` at HEAD `72da75876`; `conftest.pytest_sessionfinish` (`not_enforced_reason` is set only for `AW_CORE_BUDGET_ENFORCE=0`, fewer than 12 CPUs, or load above CPU count, else `session.exitstatus = 1`) | `1675 passed, 11 warnings in 34.61s`, exit 1, with an enforced `CORE TIER BUDGET EXCEEDED` block ("Core tier wall time: 34.61s exceeded budget of 30.00s", load 5.88 on 12 CPUs, no "not enforced" line). The bare gate is already non-zero on this host before this plan, so an "exit 0" bar would be unsatisfiable for an out-of-scope reason. |

## Proposed changes (ordered, validatable)

1. E-01 probes all eight keys at execution HEAD under `-m core`.
2. E-02 adds a behavioral test only for a surviving key; otherwise no file change.
3. E-03 confirms the bare core gate passes.

## Deferred / out of scope (with reason)

- Adding redundant tests for `SystemResourceProbeAdapter.disk` beyond the two killing tests.
  - Carrier-Declined: no work is owed; killing tests meet the item's remedy ("probe then restore") and the repository's trim direction disfavors redundant tests.

## Scope check

- Over-scope: none. Only `tests/test_run_analytics_telemetry.py` is declared, and it changes only if a probe survives.
- Under-scope: none. All eight backlog keys are probed by E-01 with the item's operators and remedied by E-02 when needed.

## Required tests / validation

- The eight `tools/mutation_probe.py` runs of E-01 (and any E-02 re-probes), full `head`/`target`/`operator`/`selection`/`verdict`/`baseline_failing`/`mutant_failing`/`newly_failing` output pasted.
- `python3 -m pytest -o addopts="" -v tests/test_run_analytics_telemetry.py` passes, per-test list pasted (required only when E-02 edits the file).
- Bare `python3 -m pytest` summary line and exit status pasted, plus any `CORE TIER BUDGET EXCEEDED` block verbatim (exit 1 acceptable only per E-03's expected outcome).
- `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/` both empty (no production change committed or left in the tree).

## Spec / documentation sync

N/A: tests only (at most); no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore tests from `19313eed^` even though the keys are already guarded?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. `8bhcd3` already restored `tests/test_run_analytics_telemetry.py` from `19313eed^` (F-01) and the probe kills every mutant (F-02); restoring again would duplicate tests. E-02 keeps a conditional remedy in case the tree changes before execution.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the full output of all eight `tools/mutation_probe.py` runs (produced by `tools/mutation_probe.py` itself, E-01), each showing `head:`, its operator, `selection:` containing `-m core tests/test_run_analytics_telemetry.py`, `baseline_failing: 0`, its `verdict:` line and its `newly_failing` list; paste `<base>` and `git diff --stat <base>..HEAD -- agent_workflows/` plus `git diff --stat -- agent_workflows/`, both showing no change.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: either paste `git diff --stat tests/test_run_analytics_telemetry.py` showing no change together with the Findings line "no survivor; no edit", or paste the diff adding only test functions, the `aw commit` output for it, and the re-probe output with a `head:` at or after that commit showing `baseline_failing: 0` and `verdict: killed` for each previously surviving key, with a `newly_failing` list naming the added test, and `python3 -m pytest -o addopts="" -v tests/test_run_analytics_telemetry.py` with every test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the bare `python3 -m pytest` summary line showing `passed` and no `failed` or `error`, its exit status, and any `CORE TIER BUDGET EXCEEDED` block verbatim (including any "not enforced" reason). An exit status of 1 passes only when that block is present and enforced and none of its listed slowest tests was added by E-02; state that check explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit bli2ba -- tests/test_run_analytics_telemetry.py` (only if E-02 changed it; plus this plan when recording evidence); never `git add -A`, never push. You MUST paste the ACTUAL probe and runner output into each `V-*`; never claim a mutant was killed or a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which is the expected case here when E-02 makes no edit). No production file under `agent_workflows/` may change. Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize bli2ba` itself.
