# IPD: Opt-in memo seam for runner-safety probes in capability test suites

- Date: 2026-10-12
- Kind: child
- Concern: Host capability test suites re-execute the runner-safety probes (fresh-verifier, deny-tcp-port, egress-filtering) on every `detect_host_capabilities` call, spending measurable wall time on identical verdicts.
- Scope: Add an OPT-IN, default-off, restore-on-exit memo seam to `host_sandbox_profile.probe_runner_safety_capabilities`, and enable it in the capability test classes that consume `detect_host_capabilities` output but do not test the runner-safety probes themselves. Production behavior (uncached) is unchanged.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, tests/test_host_capability_extension.py, tests/test_host_sandbox_profile.py, tests/test_hostcapgate_descriptor_freeze.py, tests/test_hostdedup_third_host.py, tests/test_runner_safety_probe_memo.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 6dmayw
- Set: 6dmayw
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 8hhd7t

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 8hhd7t verified (set 6dmayw, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog 6dmayw with measured baseline; review-ready.

## Goal

Stop the host capability test suites from re-running the three executed runner-safety probes on every `detect_host_capabilities` call, by adding a default-off memo seam that tests opt into, while keeping the production prober deliberately uncached and keeping every probe-behavior test executing the real probe.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline measurement

- [x] E-01 Record the baseline with the measurement plugin defined under "Required tests / validation" (saved OUTSIDE the tracked tree, e.g. under the gitignored `.aw/state/` or `/tmp`, and never committed). It wraps each non-`None` entry of `host_sandbox_profile._RUNNER_SAFETY_PROBES` once at import and counts EXECUTIONS of the probe callables (and their wall time) per test class. Counting executions, not calls to `probe_runner_safety_capabilities`, is required: the memo lives inside that function, so its call count is unchanged by this plan and cannot show the effect. Run it serially (`-n0`, because the counter is per-process and xdist workers would each hold a partial count) over the four capability modules and paste the output.
  - Depends on: none
  - Expected outcome: A pasted baseline `PROBE_EXEC executions=<n> total=<t>s` line, its per-class breakdown, and the pytest summary line, to compare E-05 against. Context only, not a bar: at review on 2026-10-12 this read `PROBE_EXEC executions=198 total=9.81s` with `113 passed in 17.72s` (machine under load; timings vary run to run).
  - Execution state: performed

### Task group 2: Memo seam

- [x] E-02 Add an opt-in memo seam to `agent_workflows/host_sandbox_profile.py`: a module-level `_RUNNER_SAFETY_MEMO` (default `None`, meaning disabled) and a context manager `memoized_runner_safety_verdicts` that enables it and restores the previous value on exit even when the body raises (same pattern as `forced_runner_safety_verdicts`). Inside `probe_runner_safety_capabilities`, when the memo is enabled, cache each EXECUTED probe's `(ok, note)` keyed by `(capability name, probe callable)` so a test that swaps an entry in `_RUNNER_SAFETY_PROBES` gets a fresh execution, and keep the `_FORCED_RUNNER_SAFETY` check AHEAD of the memo so a forced verdict is never cached and never shadowed. Add `memoized_runner_safety_verdicts` to `__all__` beside `forced_runner_safety_verdicts`. Update the function docstring: production stays uncached for the stated staleness reason; the memo exists only for test processes and is off unless entered.
  - Depends on: E-01
  - Expected outcome: With the memo off, behavior is byte-identical to today; with it on, each probe callable executes at most once per memo scope.
  - Execution state: performed

- [x] E-03 Add `tests/test_runner_safety_probe_memo.py` exercising the seam by behavior: install counting probe callables into `_RUNNER_SAFETY_PROBES` (saved and restored), then assert (a) with the memo off two calls execute each probe twice, (b) inside `memoized_runner_safety_verdicts()` two calls execute each probe once and return equal verdicts and notes, (c) swapping a probe callable inside the scope re-executes it, (d) a forced verdict via `forced_runner_safety_verdicts` inside the memo scope wins and is not cached for later unforced calls, (e) the memo is disabled again after the context exits, including after the body raises.
  - Depends on: E-02
  - Expected outcome: A new test module that fails if the memo leaks, shadows forced verdicts, or ignores probe swaps.
  - Execution state: performed

### Task group 3: Opt the suites in

- [x] E-04 Enable the memo at CLASS scope (enter `memoized_runner_safety_verdicts()` in `setUpClass` and register its `__exit__` with `cls.addClassCleanup`, so one memo spans every test in the class and is restored even when a test or `setUpClass` fails; a per-test `setUp` scope is NOT acceptable because most consumer classes call the prober about once per test, so a per-test memo would save almost nothing) in the test classes that call `detect_host_capabilities` or the `aw host` verbs for reasons OTHER than testing the runner-safety probes: in `tests/test_host_capability_extension.py` `InspectionVerbTests`, `SessionResumeArgvTrackingTests`, `StructuredToolEventsRendererTrackingTests`, `CheckerTests`, `FailClosedPreflightTests`, `DenyPushRemovedTests`, `CommitGatewayClaimConsistencyTests`; in `tests/test_host_sandbox_profile.py` `StructuredToolEventsProbeTests`, `SessionResumeProbeTests`, `CapabilityProbeTests`, `ProbeMustProveDenialTests`, `DiscoveryThenExecutionTests`, `AdversarialOsDenialTests` (the last three call `detect_host_capabilities` for sandbox-ladder reasons and patch no runner-safety probe input); `HostCapGateDescriptorFreezeTests` in `tests/test_hostcapgate_descriptor_freeze.py`; and `ThirdHostCapabilitiesTests` and `ThirdHostInitializationAndLimitTests` in `tests/test_hostdedup_third_host.py` (the only `ThirdHost*` classes that reach the prober). If an existing class already defines `setUpClass`, call `super().setUpClass()` and keep its body. Do NOT enable it in `RunnerSafetyProbeTests`, `MockSeamTests`, `DenyTcpPortProbeTests`, or `EgressFilteringProbeTests`, which test the probes and their arrangements and must execute them every time.
  - Depends on: E-02
  - Expected outcome: Only consumer classes share probe verdicts; probe-behavior classes still execute the real probes per call. Re-derive at execution time, with the E-01 per-class breakdown, that every class still executing probes after E-04 is either one of the four excluded probe-behavior classes or is named in this item; add any newly appearing consumer class here rather than leaving it uncached.
  - Execution state: performed

### Task group 4: Measure and validate

- [x] E-05 Re-run the E-01 measurement and the full bare suite; record the after numbers next to the baseline.
  - Depends on: E-03, E-04
  - Expected outcome: Probe EXECUTIONS and probe time in the four modules (plus the new module) drop materially below the E-01 baseline measured in the same execution session, each opted-in class executes each probe at most once, all tests pass, and the bare suite passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Process-global test seams in `host_sandbox_profile` are restored by a context manager so a failing test cannot leak them: `forced_runner_safety_verdicts` ("Restoring in `__exit__` makes the leak impossible even when the body raises").
- The sandbox ladder already memoizes per process in `_SANDBOX_PROBE_CACHE` via `_probe_linux_sandbox`; tests save/restore it in `setUp`/`tearDown` (`CapabilityProbeTests.setUp` in `tests/test_host_sandbox_profile.py`).
- `probe_runner_safety_capabilities` docstring: "Deliberately NOT cached ... a stale memo here would be a way for one turn's verdict to outlive the state it was measured against." This plan keeps that production property; the memo is opt-in and default off.
- Tests swap probe callables in `_RUNNER_SAFETY_PROBES` and restore them (`DenyTcpPortProbeTests`, `EgressFilteringProbeTests`, `RunnerSafetyProbeTests` in the two test modules), which is why the memo key must include the callable.
- Repo contract: run the suite bare (`python3 -m pytest`); no code-pinning tests (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | `probe_runner_safety_capabilities` executes every probe on every call; `detect_host_capabilities` calls it for the running platform. | `host_sandbox_profile.detect_host_capabilities`: "verdicts, notes = probe_runner_safety_capabilities()". |
| F-02 | Per-call cost is about 80ms (three probes at roughly 0.03 to 0.05s each, measured 2026-10-12 by calling each entry of `_RUNNER_SAFETY_PROBES`). | Authoring measurement: `supports_fresh_verifier_session 0.04`, `supports_deny_tcp_port 0.05`, `supports_egress_filtering 0.03`, `safety 0.08`. |
| F-03 | Across the four capability modules run serially, the probes ran 67 times for 5.22s of a 9.36s run. The backlog's "~10s" is the order of magnitude of the whole serial run; the probe share measured here is about 5s. | Authoring measurement: `113 passed in 9.36s`, `SAFETY_PROBE calls=67 total=5.22s`. |
| F-04 | The heaviest consumers are `RunnerSafetyProbeTests` (9 calls, must stay uncached), `MockSeamTests` (8, mostly forced), `InspectionVerbTests` (8), `HostCapGateDescriptorFreezeTests` (6), `StructuredToolEventsRendererTrackingTests` (6). | Authoring per-class breakdown of the same run. |
| F-06 | Calls to `probe_runner_safety_capabilities` are the wrong metric: the memo sits inside it, so the 67 calls stay 67. Each call executes three probes, so executions are the measurable unit (198 at review). | Review run with a call-counting plugin: `SAFETY_PROBE calls=67`; with a plugin wrapping each `_RUNNER_SAFETY_PROBES` entry: `PROBE_EXEC executions=198 total=9.81s`, `113 passed in 17.72s`. |
| F-07 | Three more classes reach the prober for sandbox-ladder reasons: `AdversarialOsDenialTests` (6 executions), `DiscoveryThenExecutionTests` (3), `ProbeMustProveDenialTests` (3). | Same review run, per-class breakdown; `tests/test_host_sandbox_profile.py` `detect_host_capabilities("opencode")` in each. |
| F-05 | This is a `chore`, not a `bug`: under the default `-n auto` the cost is spread across workers and no operator command waits on it. | AGENTS.md "INEFFICIENCY A USER CAN NOTICE IS A DEFECT" test; backlog `Work-Kind: chore`. |

## Proposed changes (ordered, validatable)

1. Measure the baseline (E-01).
2. Add the default-off memo seam and its context manager (E-02).
3. Add behavioral tests for the seam (E-03).
4. Opt the consumer test classes in (E-04).
5. Measure again and run the bare suite (E-05).

## Deferred / out of scope (with reason)

- Caching in production (`aw host`, runner preflight): out of scope; the docstring's staleness rationale stands and the backlog item is about test suites only.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- A pytest-wide autouse fixture enabling the memo: rejected because it would silently cache inside probe-behavior tests; per-class opt-in keeps those tests honest.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Reducing `_capture_turn_argv` or sandbox-ladder costs: separate concern, not named by the backlog item.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none; every consumer class in the review-time per-class breakdown (F-04, F-07) is listed in E-04, the probe-behavior classes are explicitly excluded, and E-04 re-derives the list at execution time.

## Required tests / validation

Measurement plugin for E-01 and E-05 (save as `aw_probe_exec_plugin.py` in an untracked directory such as `.aw/state/memo-measure/`, run with `PYTHONPATH=<that dir> python3 -m pytest -o addopts="" -q -n0 -p aw_probe_exec_plugin <modules>`; `-n0` is required here only because the counter is per-process):

```python
import time, collections
import pytest
from agent_workflows import host_sandbox_profile as hsp

stats, tm, cur = collections.Counter(), [0.0], ["?"]

def _wrap(fn):
    def counted():
        t = time.perf_counter()
        try:
            return fn()
        finally:
            tm[0] += time.perf_counter() - t
            stats[cur[0].rsplit("::", 1)[0]] += 1
    return counted

for _n, _fn in list(hsp._RUNNER_SAFETY_PROBES.items()):
    if _fn is not None:
        hsp._RUNNER_SAFETY_PROBES[_n] = _wrap(_fn)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    cur[0] = item.nodeid
    yield

def pytest_sessionfinish():
    print(f"\nPROBE_EXEC executions={sum(stats.values())} total={tm[0]:.2f}s")
    for c, v in sorted(stats.items()):
        print(c, "executions=", v)
```

The wrapped callables are installed once and stay stable, so they are valid memo keys; tests that save and restore `_RUNNER_SAFETY_PROBES` restore the wrapped entries.

- `python3 -m pytest -o addopts="" -q -n0 tests/test_runner_safety_probe_memo.py` passes (E-03).
- The plugin command above over `tests/test_host_sandbox_profile.py tests/test_host_capability_extension.py tests/test_hostdedup_third_host.py tests/test_hostcapgate_descriptor_freeze.py` (E-01), then the same four plus `tests/test_runner_safety_probe_memo.py` (E-05), passes, with fewer probe executions and less probe time than the E-01 baseline (E-05).
- Bare `python3 -m pytest` passes (E-05).

## Spec / documentation sync

N/A: spec `25kzda` cites `probe_runner_safety_capabilities()` only for its verdicts, which this plan does not change; production remains uncached. No user-facing docs describe test-suite internals. The function docstring is updated in E-02.

## Open questions

### OQ-01: Should the memo also apply in production preflight?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The existing docstring of `probe_runner_safety_capabilities` deliberately keeps it uncached so a verdict cannot outlive the state it was measured against, and the backlog item scopes the problem to test suites. Out of scope.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of the baseline measurement showing the pytest summary line (`N passed in Xs`), the `PROBE_EXEC executions=<n> total=<t>s` line, and the per-class breakdown, produced by the plugin under "Required tests / validation" (E-01 creates the observation), plus `git status --short` showing the plugin file is not tracked or staged.
  - Observed evidence:
```
$ PYTHONPATH=.aw/state/memo-measure python3 -m pytest -o addopts="" -q -n0 -p aw_probe_exec_plugin tests/test_host_sandbox_profile.py tests/test_host_capability_extension.py tests/test_hostdedup_third_host.py tests/test_hostcapgate_descriptor_freeze.py
........................................................................ [ 63%]
.........................................                                [100%]
PROBE_EXEC executions=198 total=15.59s
tests/test_host_capability_extension.py::CheckerTests executions= 3
tests/test_host_capability_extension.py::CommitGatewayClaimConsistencyTests executions= 3
tests/test_host_capability_extension.py::DenyPushRemovedTests executions= 3
tests/test_host_capability_extension.py::FailClosedPreflightTests executions= 3
tests/test_host_capability_extension.py::InspectionVerbTests executions= 24
tests/test_host_capability_extension.py::MockSeamTests executions= 24
tests/test_host_capability_extension.py::RunnerSafetyProbeTests executions= 26
tests/test_host_capability_extension.py::SessionResumeArgvTrackingTests executions= 12
tests/test_host_capability_extension.py::StructuredToolEventsRendererTrackingTests executions= 18
tests/test_host_sandbox_profile.py::AdversarialOsDenialTests executions= 6
tests/test_host_sandbox_profile.py::CapabilityProbeTests executions= 9
tests/test_host_sandbox_profile.py::DenyTcpPortProbeTests executions= 2
tests/test_host_sandbox_profile.py::DiscoveryThenExecutionTests executions= 3
tests/test_host_sandbox_profile.py::EgressFilteringProbeTests executions= 2
tests/test_host_sandbox_profile.py::ProbeMustProveDenialTests executions= 3
tests/test_host_sandbox_profile.py::SessionResumeProbeTests executions= 9
tests/test_host_sandbox_profile.py::StructuredToolEventsProbeTests executions= 15
tests/test_hostcapgate_descriptor_freeze.py::HostCapGateDescriptorFreezeTests executions= 18
tests/test_hostdedup_third_host.py::ThirdHostCapabilitiesTests executions= 6
tests/test_hostdedup_third_host.py::ThirdHostInitializationAndLimitTests executions= 9

113 passed in 33.07s

$ git status --short
(clean output - plugin under .aw/state/memo-measure is gitignored)
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `git diff` of `agent_workflows/host_sandbox_profile.py` showing `_RUNNER_SAFETY_MEMO` defaulting to `None`, the `memoized_runner_safety_verdicts` context manager restoring on `__exit__`, the forced-verdict branch preceding the memo lookup, the memo key including the probe callable, the `__all__` entry, and the updated docstring.
  - Observed evidence:
```diff
diff --git a/agent_workflows/host_sandbox_profile.py b/agent_workflows/host_sandbox_profile.py
index fb604031c..4a7fc195f 100644
--- a/agent_workflows/host_sandbox_profile.py
+++ b/agent_workflows/host_sandbox_profile.py
@@ -191,6 +191,7 @@ __all__ = [
     "UNREPRESENTED_SPEC_CAPABILITIES",
     "probe_runner_safety_capabilities",
     "forced_runner_safety_verdicts",
+    "memoized_runner_safety_verdicts",
     "ACTION_READ_ONLY",
     "ACTION_EXECUTE",
     "ACTION_CLASSES",
@@ -1123,22 +1124,60 @@ class forced_runner_safety_verdicts:
         _FORCED_RUNNER_SAFETY = self._saved


+#: Opt-in test seam memo for runner-safety probe verdicts: `{(capability, probe_fn): (supported, note)}`.
+#:
+#: Default is None (disabled). Enabled inside `memoized_runner_safety_verdicts` context manager.
+_RUNNER_SAFETY_MEMO: Optional[Dict[Tuple[str, Callable[..., Any]], Tuple[bool, str]]] = None
+
+
+class memoized_runner_safety_verdicts:
+    """Context manager enabling memoization of runner-safety probe verdicts, restoring on exit.
+
+    Exists to eliminate redundant probe executions in test suites that exercise host capability
+    consumers without testing the probes themselves. Off by default. Restoring in `__exit__`
+    makes leaks impossible even when the body raises.
+    """
+
+    def __init__(
+        self,
+        memo: Optional[Dict[Tuple[str, Callable[..., Any]], Tuple[bool, str]]] = None,
+    ) -> None:
+        self._memo = {} if memo is None else memo
+        self._saved: Any = None
+
+    def __enter__(self) -> Dict[Tuple[str, Callable[..., Any]], Tuple[bool, str]]:
+        global _RUNNER_SAFETY_MEMO
+        self._saved = _RUNNER_SAFETY_MEMO
+        _RUNNER_SAFETY_MEMO = self._memo
+        return _RUNNER_SAFETY_MEMO
+
+    def __exit__(self, *exc_info: Any) -> None:
+        global _RUNNER_SAFETY_MEMO
+        _RUNNER_SAFETY_MEMO = self._saved
+
+
 def probe_runner_safety_capabilities() -> Tuple[Dict[str, bool], Dict[str, str]]:
-    """Decide the two runner-safety capabilities, returning (verdicts, notes).
+    """Decide runner-safety capabilities, returning (verdicts, notes).

-    Deliberately NOT cached. The sandbox ladder is memoized because it spawns jail
-    subprocesses whose answer cannot change mid-process; these probes are in-process and
+    Deliberately NOT cached in production. The sandbox ladder is memoized because it spawns
+    jail subprocesses whose answer cannot change mid-process; these probes are in-process and
     cheap, and a stale memo here would be a way for one turn's verdict to outlive the state
     it was measured against. (Note the shipped `_SANDBOX_PROBE_CACHE` is a plain per-process
     memo with NO staleness/TTL notion; the expiry model in `host_capability_registry` belongs
     to a different concern and is deliberately not imported by implication.)

+    For test processes that call `detect_host_capabilities` repeatedly without testing the
+    probes themselves, an opt-in memo seam is available via `memoized_runner_safety_verdicts`.
+    Production behavior remains uncached for the staleness reason stated above; the memo
+    is off unless entered.
+
     A capability with no probe reports not-supported with the reason recorded, never
     supported-by-assumption.
     """
     verdicts: Dict[str, bool] = {}
     notes: Dict[str, str] = {}
     forced = _FORCED_RUNNER_SAFETY
+    memo = _RUNNER_SAFETY_MEMO
     for name in RUNNER_SAFETY_CAPABILITIES:
         if forced is not None and name in forced:
             ok, note = forced[name]
@@ -1152,10 +1191,18 @@ def probe_runner_safety_capabilities() -> Tuple[Dict[str, bool], Dict[str, str]]
                 name, "declared but not probed; not supported (fail-closed)"
             )
             continue
+        memo_key = (name, probe)
+        if memo is not None and memo_key in memo:
+            ok, note = memo[memo_key]
+            verdicts[name] = bool(ok)
+            notes[name] = note
+            continue
         try:
             ok, note = probe()
         except Exception as exc:  # a probe must never propagate; unknown => False
             ok, note = False, f"probe raised {type(exc).__name__}: {exc}"
+        if memo is not None:
+            memo[memo_key] = (ok, note)
         verdicts[name] = bool(ok)
         notes[name] = note
     return verdicts, notes
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted runner output of `python3 -m pytest -o addopts="" -q -n0 tests/test_runner_safety_probe_memo.py` showing all tests passed, plus the test names covering cases (a) through (e).
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" -q -n0 tests/test_runner_safety_probe_memo.py
.....                                                                    [100%]
5 passed in 0.26s

Test coverage for cases (a) through (e):
- RunnerSafetyProbeMemoTests::test_memo_off_executes_probes_on_each_call (case a)
- RunnerSafetyProbeMemoTests::test_memo_scope_executes_each_probe_once_and_returns_equal_verdicts_and_notes (case b)
- RunnerSafetyProbeMemoTests::test_swapping_probe_callable_inside_scope_re_executes_it (case c)
- RunnerSafetyProbeMemoTests::test_forced_verdict_wins_and_is_not_cached (case d)
- RunnerSafetyProbeMemoTests::test_memo_disabled_after_context_exit_including_on_raise (case e)
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `git diff` of the four existing test modules showing the memo entered at class scope (`setUpClass` plus `addClassCleanup`) only in the E-04 consumer classes and absent from `RunnerSafetyProbeTests`, `MockSeamTests`, `DenyTcpPortProbeTests`, and `EgressFilteringProbeTests`, plus the E-05 per-class breakdown showing each opted-in class at no more than one execution per probe (at most 3 executions per class) and the four excluded classes still executing per call.
  - Observed evidence:
```
git diff across the four test modules confirms setUpClass and addClassCleanup(cm.__exit__, None, None, None) were added only to the 16 consumer classes:
- tests/test_host_capability_extension.py: CheckerTests, FailClosedPreflightTests, InspectionVerbTests, DenyPushRemovedTests, SessionResumeArgvTrackingTests, StructuredToolEventsRendererTrackingTests, CommitGatewayClaimConsistencyTests
- tests/test_host_sandbox_profile.py: CapabilityProbeTests, ProbeMustProveDenialTests, DiscoveryThenExecutionTests, AdversarialOsDenialTests, SessionResumeProbeTests, StructuredToolEventsProbeTests
- tests/test_hostcapgate_descriptor_freeze.py: HostCapGateDescriptorFreezeTests
- tests/test_hostdedup_third_host.py: ThirdHostCapabilitiesTests, ThirdHostInitializationAndLimitTests

The four probe-behavior classes (RunnerSafetyProbeTests, MockSeamTests, DenyTcpPortProbeTests, EgressFilteringProbeTests) remain absent from the diff and uncached.

The E-05 breakdown confirms each opted-in consumer class executes at most 3 times (1 execution per probe), while excluded classes continue executing per call:
- InspectionVerbTests: 3 executions (down from 24)
- SessionResumeArgvTrackingTests: 3 executions (down from 12)
- StructuredToolEventsRendererTrackingTests: 3 executions (down from 18)
- MockSeamTests: 24 executions (unchanged)
- RunnerSafetyProbeTests: 26 executions (unchanged)
- DenyTcpPortProbeTests: 2 executions (unchanged)
- EgressFilteringProbeTests: 2 executions (unchanged)
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted after-measurement output (same plugin, same four modules plus `tests/test_runner_safety_probe_memo.py`) with a lower `executions=` and `total=` than V-01, and pasted output of a bare `python3 -m pytest` ending in its `N passed` summary with no failures.
  - Observed evidence:
```
$ PYTHONPATH=.aw/state/memo-measure python3 -m pytest -o addopts="" -q -n0 -p aw_probe_exec_plugin tests/test_host_sandbox_profile.py tests/test_host_capability_extension.py tests/test_hostdedup_third_host.py tests/test_hostcapgate_descriptor_freeze.py tests/test_runner_safety_probe_memo.py
........................................................................ [ 61%]
..............................................                           [100%]
PROBE_EXEC executions=102 total=2.53s
tests/test_host_capability_extension.py::CheckerTests executions= 3
tests/test_host_capability_extension.py::CommitGatewayClaimConsistencyTests executions= 3
tests/test_host_capability_extension.py::DenyPushRemovedTests executions= 3
tests/test_host_capability_extension.py::FailClosedPreflightTests executions= 3
tests/test_host_capability_extension.py::InspectionVerbTests executions= 3
tests/test_host_capability_extension.py::MockSeamTests executions= 24
tests/test_host_capability_extension.py::RunnerSafetyProbeTests executions= 26
tests/test_host_capability_extension.py::SessionResumeArgvTrackingTests executions= 3
tests/test_host_capability_extension.py::StructuredToolEventsRendererTrackingTests executions= 3
tests/test_host_sandbox_profile.py::AdversarialOsDenialTests executions= 3
tests/test_host_sandbox_profile.py::CapabilityProbeTests executions= 3
tests/test_host_sandbox_profile.py::DenyTcpPortProbeTests executions= 2
tests/test_host_sandbox_profile.py::DiscoveryThenExecutionTests executions= 3
tests/test_host_sandbox_profile.py::EgressFilteringProbeTests executions= 2
tests/test_host_sandbox_profile.py::ProbeMustProveDenialTests executions= 3
tests/test_host_sandbox_profile.py::SessionResumeProbeTests executions= 3
tests/test_host_sandbox_profile.py::StructuredToolEventsProbeTests executions= 3
tests/test_hostcapgate_descriptor_freeze.py::HostCapGateDescriptorFreezeTests executions= 3
tests/test_hostdedup_third_host.py::ThirdHostCapabilitiesTests executions= 3
tests/test_hostdedup_third_host.py::ThirdHostInitializationAndLimitTests executions= 3

118 passed in 8.15s

Executions dropped from 198 to 102 (-48.5%).
Total probe wall time dropped from 15.59s to 2.53s (-83.8%).

Bare pytest suite output:
$ python3 -m pytest
=============================== warnings summary ===============================
tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_the_lock_is_reacquirable_after_the_holder_exits
tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_KILLED_holder_does_not_strand_the_lock
tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_second_holder_is_genuinely_EXCLUDED_and_the_holder_is_NAMED
  multiprocessing/popen_fork.py:76: DeprecationWarning: This process is multi-threaded, use of fork() may lead to deadlocks in the child.
    self.pid = os.fork()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
NOTE: 291 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
7739 passed, 4 skipped, 3 warnings in 437.37s (0:07:17)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). OQ-01 is resolved; none remain. `- Scope-Paths:` is a declaration that finalize reconciles: an out-of-scope edit that proves necessary is made and then justified with `--scope-reason`, and a declared path left unmodified gets a `--scope-ack`. The measurement plugin is NOT a deliverable and must never be committed. Commit through `aw commit 8hhd7t -- <paths>` (never `git add -A`), and never push. Paste the ACTUAL runner output for every claim that a test passed or a measurement moved; never claim a result you did not run. After every `E-*` reads `performed`, every `V-*` reads `pass` with pasted evidence, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/` through the tooled lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; in a hand-driven execution the executor runs `aw ipd finalize 8hhd7t --actor <agent/model> --message <summary> --apply`. Backlog `6dmayw` is advanced by the runner's backlog-close step, never by hand.
