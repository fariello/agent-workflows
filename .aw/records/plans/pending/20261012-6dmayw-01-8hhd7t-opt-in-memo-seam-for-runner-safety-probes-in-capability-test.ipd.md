# IPD: Opt-in memo seam for runner-safety probes in capability test suites

- Date: 2026-10-12
- Kind: child
- Concern: Host capability test suites re-execute the runner-safety probes (fresh-verifier, deny-tcp-port, egress-filtering) on every `detect_host_capabilities` call, spending measurable wall time on identical verdicts.
- Scope: Add an OPT-IN, default-off, restore-on-exit memo seam to `host_sandbox_profile.probe_runner_safety_capabilities`, and enable it in the capability test classes that consume `detect_host_capabilities` output but do not test the runner-safety probes themselves. Production behavior (uncached) is unchanged.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, tests/test_host_capability_extension.py, tests/test_host_sandbox_profile.py, tests/test_hostcapgate_descriptor_freeze.py, tests/test_hostdedup_third_host.py, tests/test_runner_safety_probe_memo.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 6dmayw
- Set: 6dmayw
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 8hhd7t

## Workflow history

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog 6dmayw with measured baseline; review-ready.

## Goal

Stop the host capability test suites from re-running the three executed runner-safety probes on every `detect_host_capabilities` call, by adding a default-off memo seam that tests opt into, while keeping the production prober deliberately uncached and keeping every probe-behavior test executing the real probe.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline measurement

- [ ] E-01 Record the baseline: run the four capability test modules serially with a wrapper counting calls to and wall time inside `host_sandbox_profile.probe_runner_safety_capabilities`, and record the call count, the probe time, and the module wall time in this plan.
  - Depends on: none
  - Expected outcome: A pasted baseline (authoring-time measurement on 2026-10-12 was `113 passed in 9.36s`, `SAFETY_PROBE calls=67 total=5.22s`) to compare E-05 against.
  - Execution state: pending

### Task group 2: Memo seam

- [ ] E-02 Add an opt-in memo seam to `agent_workflows/host_sandbox_profile.py`: a module-level `_RUNNER_SAFETY_MEMO` (default `None`, meaning disabled) and a context manager `memoized_runner_safety_verdicts` that enables it and restores the previous value on exit even when the body raises (same pattern as `forced_runner_safety_verdicts`). Inside `probe_runner_safety_capabilities`, when the memo is enabled, cache each EXECUTED probe's `(ok, note)` keyed by `(capability name, probe callable)` so a test that swaps an entry in `_RUNNER_SAFETY_PROBES` gets a fresh execution, and keep the `_FORCED_RUNNER_SAFETY` check AHEAD of the memo so a forced verdict is never cached and never shadowed. Update the function docstring: production stays uncached for the stated staleness reason; the memo exists only for test processes and is off unless entered.
  - Depends on: E-01
  - Expected outcome: With the memo off, behavior is byte-identical to today; with it on, each probe callable executes at most once per memo scope.
  - Execution state: pending

- [ ] E-03 Add `tests/test_runner_safety_probe_memo.py` exercising the seam by behavior: install counting probe callables into `_RUNNER_SAFETY_PROBES` (saved and restored), then assert (a) with the memo off two calls execute each probe twice, (b) inside `memoized_runner_safety_verdicts()` two calls execute each probe once and return equal verdicts and notes, (c) swapping a probe callable inside the scope re-executes it, (d) a forced verdict via `forced_runner_safety_verdicts` inside the memo scope wins and is not cached for later unforced calls, (e) the memo is disabled again after the context exits, including after the body raises.
  - Depends on: E-02
  - Expected outcome: A new test module that fails if the memo leaks, shadows forced verdicts, or ignores probe swaps.
  - Execution state: pending

### Task group 3: Opt the suites in

- [ ] E-04 Enable the memo (via `setUp`/`addCleanup` or a class-level wrapper entering `memoized_runner_safety_verdicts`) in the test classes that call `detect_host_capabilities` or the `aw host` verbs for reasons OTHER than testing the runner-safety probes: in `tests/test_host_capability_extension.py` `InspectionVerbTests`, `SessionResumeArgvTrackingTests`, `StructuredToolEventsRendererTrackingTests`, `CheckerTests`, `FailClosedPreflightTests`, `DenyPushRemovedTests`, `CommitGatewayClaimConsistencyTests`; in `tests/test_host_sandbox_profile.py` `StructuredToolEventsProbeTests`, `SessionResumeProbeTests`, `CapabilityProbeTests`; `HostCapGateDescriptorFreezeTests` in `tests/test_hostcapgate_descriptor_freeze.py`; and the `ThirdHost*` classes in `tests/test_hostdedup_third_host.py`. Do NOT enable it in `RunnerSafetyProbeTests`, `MockSeamTests`, `DenyTcpPortProbeTests`, or `EgressFilteringProbeTests`, which test the probes and their arrangements and must execute them every time.
  - Depends on: E-02
  - Expected outcome: Only consumer classes share probe verdicts; probe-behavior classes still execute the real probes per call.
  - Execution state: pending

### Task group 4: Measure and validate

- [ ] E-05 Re-run the E-01 measurement and the full bare suite; record the after numbers next to the baseline.
  - Depends on: E-03, E-04
  - Expected outcome: Probe call count and probe time in the four modules drop materially below the E-01 baseline, all tests pass, and the bare suite passes.
  - Execution state: pending

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
| F-05 | This is a `chore`, not a `bug`: under the default `-n auto` the cost is spread across workers and no operator command waits on it. | AGENTS.md "INEFFICIENCY A USER CAN NOTICE IS A DEFECT" test; backlog `Work-Kind: chore`. |

## Proposed changes (ordered, validatable)

1. Measure the baseline (E-01).
2. Add the default-off memo seam and its context manager (E-02).
3. Add behavioral tests for the seam (E-03).
4. Opt the consumer test classes in (E-04).
5. Measure again and run the bare suite (E-05).

## Deferred / out of scope (with reason)

- Caching in production (`aw host`, runner preflight): out of scope; the docstring's staleness rationale stands and the backlog item is about test suites only.
- A pytest-wide autouse fixture enabling the memo: rejected because it would silently cache inside probe-behavior tests; per-class opt-in keeps those tests honest.
- Reducing `_capture_turn_argv` or sandbox-ladder costs: separate concern, not named by the backlog item.

## Scope check

- Over-scope: none.
- Under-scope: none; every consumer class identified in F-04 and the authoring breakdown is listed in E-04, and the probe-behavior classes are explicitly excluded.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q -n0 tests/test_runner_safety_probe_memo.py` passes (E-03).
- `python3 -m pytest -o addopts="" -q -n0 tests/test_host_sandbox_profile.py tests/test_host_capability_extension.py tests/test_hostdedup_third_host.py tests/test_hostcapgate_descriptor_freeze.py tests/test_runner_safety_probe_memo.py` passes, with the counting-wrapper measurement showing fewer probe calls and less probe time than the E-01 baseline (E-05).
- Bare `python3 -m pytest` passes (E-05).

## Spec / documentation sync

N/A: spec `25kzda` cites `probe_runner_safety_capabilities()` only for its verdicts, which this plan does not change; production remains uncached. No user-facing docs describe test-suite internals. The function docstring is updated in E-02.

## Open questions

### OQ-01: Should the memo also apply in production preflight?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The existing docstring of `probe_runner_safety_capabilities` deliberately keeps it uncached so a verdict cannot outlive the state it was measured against, and the backlog item scopes the problem to test suites. Out of scope.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of the baseline measurement showing the pytest summary line (`N passed in Xs`) and the `SAFETY_PROBE calls=<n> total=<t>s` line, produced by the counting wrapper around `probe_runner_safety_capabilities` (E-01 creates the observation).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff` of `agent_workflows/host_sandbox_profile.py` showing `_RUNNER_SAFETY_MEMO` defaulting to `None`, the `memoized_runner_safety_verdicts` context manager restoring on `__exit__`, the forced-verdict branch preceding the memo lookup, the memo key including the probe callable, and the updated docstring.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted runner output of `python3 -m pytest -o addopts="" -q -n0 tests/test_runner_safety_probe_memo.py` showing all tests passed, plus the test names covering cases (a) through (e).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff` of the four existing test modules showing the memo entered only in the E-04 consumer classes and absent from `RunnerSafetyProbeTests`, `MockSeamTests`, `DenyTcpPortProbeTests`, and `EgressFilteringProbeTests`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted after-measurement output (same command as V-01) with a lower `calls=` and `total=` than V-01, and pasted output of a bare `python3 -m pytest` ending in its `N passed` summary with no failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the Scope-Paths files through `aw commit 8hhd7t -- <paths>`, never push. Move this plan to `.aw/records/plans/executed/` through the tooled lifecycle only after `aw ipd lint --phase pre-transition` conforms and every V-* item reads `pass` with pasted evidence.
