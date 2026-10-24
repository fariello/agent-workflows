# IPD: Lock TrialResult.to_dict and RunnerAdapter.adapter_digest behavior into the core tier

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `l9ssp6` (Set `trimgap`, group 13 of the `wo21z5` `## Filing plan`, remedy "investigate probe") carries two keys of `agent_workflows/benchmark_runners.py` that the `wo21z5` budget probe recorded `unprovable` with reason "control survived; overwrote 1": `TrialResult.to_dict` and `RunnerAdapter.adapter_digest`, operator `return-none`, control `tests/test_benchmark_runners_reports.py`. Re-measured at authoring HEAD `9f9c6d625` (F-01): a `return-none` mutant of each SURVIVES both test files that touch the benchmark runner (`tests/test_benchmark_runners_reports.py`, `tests/test_benchmark_corpus.py`) under the full non-slow selection, so the gap is not core-tier membership: no test anywhere asserts on what either key returns. The probe itself is applicable (the operator applies, and each key returns a concrete non-None value a test can read, F-02, F-03). Both keys are on the benchmark report path in production: `BenchmarkRunRecord.to_dict` serializes every trial with `t.to_dict()`, and every `RunnerDouble.run_trial` and `execute_live_runner` manifest is stamped with `adapter.adapter_digest()`.
- Scope: Add ONE new core-marked test module, `tests/test_benchmark_runner_payloads.py`, that drives the two keys through their public objects (`RunnerAdapter`, `RunnerDouble.run_trial`, `TrialResult`) and asserts on the returned digest and dict, then probes each key with `tools/mutation_probe.py` under a `-m core` selection to prove the routine gate now kills the mutants. EXCLUDES any production-code change; EXCLUDES other `benchmark_runners.py` keys (`TrialResult.is_success`, `is_pending`, `is_completed`, `get_adapter`, `RunnerAdapter.build_rerun_command`, the `__init__` keys) which are not in this item; EXCLUDES the sibling benchmark keys owned by plans `1z19cn` (`cell_key`, `MetricSummary.to_dict`, `GateEvaluationResult.to_dict`) and `ya0h23` (manifest digests); EXCLUDES restoring deleted tests verbatim from `19313eed^`.
- Scope-Paths: tests/test_benchmark_runner_payloads.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: l9ssp6
- Set: trimgap
- Order: 37
- Highest E allocated: 04
- Author: opencode
- Id: rempo8
- Approval: 2026-10-24, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-24 approved (aw set): status set to approved
- 2026-10-24 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002. Re-verified F-01 at HEAD `fa3959eaf` (`adapter_digest` return-none still `survived`, `mutant_failing: 0`) and every F-03 value by direct call.

- 2026-10-23 to-review (opencode): authored from backlog `l9ssp6` (group 13). Re-probed both keys at HEAD `9f9c6d625` against both benchmark-runner test files (both `survived`, `mutant_failing: 0`) and measured the concrete values the new tests assert on before writing expected outcomes.
- 2026-10-24 draft (opencode): created.

## Goal

Answer the item's "investigate probe" question for both keys with recorded evidence (the probe is applicable; the gap is a real missing assertion), and close the gap so a `return-none` mutation of either key turns a routine core-tier test red. Done means both keys report `verdict: killed` under a `-m core` selection containing the new module.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the new core-tier module

- [x] E-01 Create `tests/test_benchmark_runner_payloads.py` with a provenance docstring naming backlog `l9ssp6`, plan `rempo8` and findings `wo21z5`, `import pytest`, module-level `pytestmark = pytest.mark.core` (the pattern already used by `tests/test_benchmark_corpus.py`), module-level fixtures shared by both classes (`TASK = SeededTask(task_class="simple_commands", seed_id="t1", task={}, seed_path=Path("/tmp/x"))` with `SeededTask` imported from `agent_workflows.benchmark_corpus`, and `PROFILE = ModelProfile(model_id="m1", reasoning_effort="high", display_name="M", vendor="v")`; `RunnerAdapter`, `RunnerDouble`, `ModelProfile` imported from `agent_workflows.benchmark_runners`; `Path` is never read or written, it is only a field value), and an `AdapterDigestTests` class asserting: `RunnerAdapter("opencode", "1.2.3", extra_flags=["--x"]).adapter_digest()` equals `"da913cd8c86eabc9e0caac47030459a3ba9b7b9b41401b9a69ea6a6bf3c40924"` and also equals `hashlib.sha256(json.dumps({"host": "opencode", "host_version": "1.2.3", "extra_flags": ["--x"]}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()` (the documented canonical-JSON contract); two separately constructed equal adapters return the same digest; `RunnerAdapter("opencode", "1.2.3").adapter_digest()` equals `"09f15fb5d5f124764dc4e7edcd8cb5f94158e1c002c7bdb6cf2a1ecdba7c0b74"` and `RunnerAdapter("opencode", "1.2.4").adapter_digest()` equals `"a9732341a1dc81c8126e7c8fd88ced68c22fa0e278a421305b77d1f826cbbb0c"` (version and flags each change the digest); and the digest reaches the trial manifest: for a `RunnerDouble(adapter, default_outcome="success").run_trial(TASK, PROFILE, trial=1)` result, `result.to_dict()["manifest"]["identity"]["adapter_digest"]` equals `adapter.adapter_digest()` and is a 64-character lowercase hex string.
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_benchmark_runner_payloads.py` shows every `AdapterDigestTests` test PASSED (values measured at authoring, F-03).
  - Execution state: performed

- [x] E-02 Add a `TrialResultToDictTests` class to the module E-01 created, using the module-level `TASK` and `PROFILE` fixtures from E-01 with `RunnerDouble(RunnerAdapter("opencode", "1.2.3"), ...)`. Assert for the `default_outcome="timeout"` result: `to_dict()` keys are exactly `{"trial_id", "status", "manifest", "rerun_command", "failure_kind", "error_message", "transcript", "score_result", "usage"}`, `status == "pending"`, `failure_kind == "timeout"`, `score_result is None`, `transcript is None`, `manifest == result.manifest.to_dict()`, `rerun_command == result.rerun_command` and is non-empty. Assert for the `default_outcome="success"` result: `trial_id == "t1_m1_opencode_t1"`, `status == "completed"`, `failure_kind is None`, and `score_result == {"verdict": "complete", "adversary_class": "", "reasons": ["no violation detected; terminal claim substantiated"], "claimed_complete": True}` (note `reasons` is converted from tuple to list). Assert both dicts round-trip through `json.loads(json.dumps(d)) == d` (it is the report payload `BenchmarkRunRecord.to_dict` emits).
  - Depends on: E-01
  - Expected outcome: every `TrialResultToDictTests` test PASSES at HEAD (values measured at authoring, F-03).
  - Execution state: performed

### Task group 2: commit and prove the mutants die in core

- [x] E-03 Commit the module with `aw commit rempo8 -- tests/test_benchmark_runner_payloads.py` and record the resulting commit hash as `<E-03 commit>` and its parent as `<E-03 parent>` (used by V-04), then run the routine bare gate `python3 -m pytest` and record its summary line and any `CORE TIER BUDGET EXCEEDED` block verbatim, plus `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_benchmark_runner_payloads.py` for the module's own cost.
  - Depends on: E-01, E-02
  - Expected outcome: the bare run shows no failures and includes the new tests; the module's own call time is well under one second (in-memory calls only; `RunnerDouble` makes no network or subprocess call). A pre-existing core wall-time overrun is reported, not treated as a failure of this plan, unless the module's own durations show it is the cause.
  - Execution state: performed

- [x] E-04 For each key K in (`agent_workflows/benchmark_runners.py::TrialResult.to_dict`, `agent_workflows/benchmark_runners.py::RunnerAdapter.adapter_digest`), run `python3 tools/mutation_probe.py --op return-none K -- -o addopts= -q -p no:randomly -n0 -m core tests/test_benchmark_runner_payloads.py`. The tool mutates in its own disposable worktree cut from committed HEAD, so it must run after E-03's commit; never hand-edit `agent_workflows/`. Record each `head`, `verdict`, `baseline_failing` and `newly_failing`. A kill under this core-marked subset is a kill under the full core tier, which is a superset. If either key reports `survived`, add the missing assertion for that key to the module, commit it the same way, and re-probe.
  - Depends on: E-03
  - Expected outcome: two `verdict: killed` results, each with `baseline_failing: 0` and a `newly_failing` list naming at least one test of the new module.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16): every test calls the production object and asserts on its returned value; none reads source.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget. Module-level `pytestmark = pytest.mark.core` is the established way in, and `tests/test_benchmark_corpus.py` already uses it for this subsystem.
- Probe tool: `tools/mutation_probe.py` (`--op {return-none,return-true,return-false,negate-return,raise}`, pytest selection after `--`) is the tool `wo21z5` and siblings `1z19cn`/`di5puw`/`92tzo6` used, so verdicts are comparable. It checks out committed `HEAD` into its own worktree, so a probe must follow a commit.
- Sibling precedent: plan `1z19cn` (same Set, Order 29, backlog `nzc6dm`) resolves the identical `wo21z5` "unprovable; control survived" verdict for three other benchmark keys with the same shape (new core module, then core probe), and explicitly leaves these two keys to `l9ssp6`.
- Commit only through `aw commit rempo8 -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `wo21z5` `## Budget probe results` rows for both keys (`P2`, `return-none`, `files`, 14 collected, survivor `survived`, control `survived`, `unprovable`, "control survived; overwrote 1"); at HEAD `9f9c6d625`: `python3 tools/mutation_probe.py --op return-none agent_workflows/benchmark_runners.py::<K> -- -o addopts= -q -p no:randomly -n0 -m "not slow and not livecorpus" tests/test_benchmark_runners_reports.py tests/test_benchmark_corpus.py` | `TrialResult.to_dict`: `verdict: survived`, `baseline_failing: 0`, `mutant_failing: 0`, `wall_s: 3.84`. `RunnerAdapter.adapter_digest`: `verdict: survived`, `baseline_failing: 0`, `mutant_failing: 0`, `wall_s: 4.1`. The `wo21z5` verdict reproduces, and it holds for the full non-slow selection of both files, not only the core tier: no test asserts on either result. `tests/test_benchmark_runners_reports.py` only stamps a literal `"adapter_digest": "0" * 64` and `tests/test_benchmark_corpus.py` a literal `"a" * 64`; neither calls `adapter_digest()` or `TrialResult.to_dict()` and reads the result. |
| F-02 | `git grep` in `agent_workflows/`: `BenchmarkRunRecord.to_dict` (`"trials": [t.to_dict() for t in self.trials]`); `RunnerDouble.run_trial` and `execute_live_runner` (`adapter_digest=self.adapter.adapter_digest()` / `adapter_digest=adapter.adapter_digest()`) | Both keys are live production paths feeding the benchmark JSON report and every trial manifest's identity, so a silent `None` would corrupt report output and manifest identity without any routine test failing. |
| F-03 | direct calls at HEAD `9f9c6d625` | `RunnerAdapter("opencode","1.2.3",extra_flags=["--x"]).adapter_digest()` -> `da913cd8c86eabc9e0caac47030459a3ba9b7b9b41401b9a69ea6a6bf3c40924`, equal to the sha256 of the sorted compact JSON of `{host, host_version, extra_flags}`; no flags -> `09f15fb5d5f124764dc4e7edcd8cb5f94158e1c002c7bdb6cf2a1ecdba7c0b74`; version `1.2.4` -> `a9732341a1dc81c8126e7c8fd88ced68c22fa0e278a421305b77d1f826cbbb0c`. `RunnerDouble(...).run_trial(task t1, profile m1, trial=1)`: manifest `identity.adapter_digest` equals the adapter's digest for both `success` and `timeout`; `to_dict()` keys `error_message, failure_kind, manifest, rerun_command, score_result, status, transcript, trial_id, usage`; `success`: `trial_id` `t1_m1_opencode_t1`, `status` `completed`, `score_result` `{'verdict': 'complete', 'adversary_class': '', 'reasons': ['no violation detected; terminal claim substantiated'], 'claimed_complete': True}`; `timeout`: `status` `pending`, `failure_kind` `timeout`, `score_result` `None`; both dicts `json.dumps` cleanly. Both keys return non-None values, so the `return-none` operator is observable to any test that reads them: the probe is applicable. |

## Proposed changes (ordered, validatable)

1. E-01 creates the core-marked module and the `adapter_digest` tests.
2. E-02 adds the `TrialResult.to_dict` payload tests.
3. E-03 commits the module and records the bare core gate and the module's cost.
4. E-04 probes both keys under the core selection against the committed tree.

## Deferred / out of scope (with reason)

- Core-marking `tests/test_benchmark_runners_reports.py` instead of writing a new module.
  - Carrier-Declined: no work is owed; F-01 shows that file does not kill either mutant even in the full non-slow selection, so marking it core would add time without closing the gap.
- Changing `tools/mutation_probe.py` or the `wo21z5` classifier.
  - Carrier-Declined: no work is owed; F-01 and F-03 show the probe tool reported correctly ("control survived" means the control test does not read the value), so there is no probe-tool defect to fix.

## Scope check

- Over-scope: none. Only the new test module is declared; no production file or existing test changes.
- Under-scope: none. Both backlog keys get direct assertions (E-01, E-02) and a core-selection probe (E-04).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_benchmark_runner_payloads.py`: every test PASSED, list pasted (E-01, E-02).
- Bare `python3 -m pytest` summary line and any budget block pasted, plus the module's `--durations=0` output (E-03).
- Two `tools/mutation_probe.py` outputs pasted, each `verdict: killed`, `baseline_failing: 0` (E-04).
- `git diff --stat <E-03 parent>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/` both empty (no production change).

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Is the probe applicable to these "unprovable" keys?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. F-03 shows each key returns a concrete non-None value, so a `return-none` mutant is visible to any test that reads it. `wo21z5` marked them `unprovable` only because the control file also survived (F-01 reproduces that across both benchmark test files), which means no test asserted on the result, not that the probe cannot work. The remedy is therefore a direct assertion, which E-04 proves, matching sibling `1z19cn` OQ-01.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the head of `tests/test_benchmark_runner_payloads.py` showing the provenance docstring (naming `l9ssp6`, `rempo8`, `wo21z5`) and `pytestmark = pytest.mark.core`; paste the `-v` lines for every `AdapterDigestTests` test, each PASSED, and the test body lines asserting the pinned hex digests, the canonical-JSON equality, and the manifest `identity.adapter_digest` equality; paste `grep -nE "inspect|getsource|ast\." tests/test_benchmark_runner_payloads.py` returning nothing.
  - Observed evidence:
    Head of `tests/test_benchmark_runner_payloads.py`:
    ```python
    """Behavioral tests for RunnerAdapter.adapter_digest and TrialResult.to_dict.

    Restores behavioral coverage for benchmark runner payload keys recorded in backlog
    item l9ssp6 (Set trimgap), plan rempo8, and research findings wo21z5.
    """

    from __future__ import annotations

    import hashlib
    import json
    import unittest
    from pathlib import Path

    import pytest

    from agent_workflows.benchmark_corpus import SeededTask
    from agent_workflows.benchmark_runners import (
        ModelProfile,
        RunnerAdapter,
        RunnerDouble,
    )

    pytestmark = pytest.mark.core
    ```

    `python3 -m pytest -o addopts="" -v tests/test_benchmark_runner_payloads.py` lines for `AdapterDigestTests`:
    ```
    tests/test_benchmark_runner_payloads.py::AdapterDigestTests::test_adapter_digest_pinned_and_canonical_json PASSED [ 60%]
    tests/test_benchmark_runner_payloads.py::AdapterDigestTests::test_adapter_digest_equality_and_sensitivity PASSED [ 80%]
    tests/test_benchmark_runner_payloads.py::AdapterDigestTests::test_adapter_digest_reaches_trial_manifest PASSED [100%]
    ```

    Test body lines asserting the pinned hex digests, canonical-JSON equality, and manifest `identity.adapter_digest` equality:
    ```python
    def test_adapter_digest_pinned_and_canonical_json(self) -> None:
        adapter = RunnerAdapter("opencode", "1.2.3", extra_flags=["--x"])
        expected_hex = (
            "da913cd8c86eabc9e0caac47030459a3ba9b7b9b41401b9a69ea6a6bf3c40924"
        )
        assert adapter.adapter_digest() == expected_hex
        canonical_json = json.dumps(
            {"host": "opencode", "host_version": "1.2.3", "extra_flags": ["--x"]},
            sort_keys=True,
            separators=(",", ":"),
        )
        assert (
            adapter.adapter_digest()
            == hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        )

    def test_adapter_digest_equality_and_sensitivity(self) -> None:
        a1 = RunnerAdapter("opencode", "1.2.3", extra_flags=["--x"])
        a2 = RunnerAdapter("opencode", "1.2.3", extra_flags=["--x"])
        assert a1.adapter_digest() == a2.adapter_digest()

        no_flags = RunnerAdapter("opencode", "1.2.3")
        assert (
            no_flags.adapter_digest()
            == "09f15fb5d5f124764dc4e7edcd8cb5f94158e1c002c7bdb6cf2a1ecdba7c0b74"
        )

        bumped_version = RunnerAdapter("opencode", "1.2.4")
        assert (
            bumped_version.adapter_digest()
            == "a9732341a1dc81c8126e7c8fd88ced68c22fa0e278a421305b77d1f826cbbb0c"
        )
        assert no_flags.adapter_digest() != bumped_version.adapter_digest()
        assert no_flags.adapter_digest() != a1.adapter_digest()

    def test_adapter_digest_reaches_trial_manifest(self) -> None:
        adapter = RunnerAdapter("opencode", "1.2.3", extra_flags=["--x"])
        runner = RunnerDouble(adapter, default_outcome="success")
        result = runner.run_trial(TASK, PROFILE, trial=1)
        res_dict = result.to_dict()
        digest = res_dict["manifest"]["identity"]["adapter_digest"]
        assert digest == adapter.adapter_digest()
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)
    ```

    `grep -nE "inspect|getsource|ast\." tests/test_benchmark_runner_payloads.py` returned nothing (exit code 1).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `-v` lines for every `TrialResultToDictTests` test, each PASSED, and the test body lines asserting the exact key set, the `timeout` field values, the `success` `score_result` dict, and the JSON round-trip.
  - Observed evidence:
    `python3 -m pytest -o addopts="" -v tests/test_benchmark_runner_payloads.py` lines for `TrialResultToDictTests`:
    ```
    tests/test_benchmark_runner_payloads.py::TrialResultToDictTests::test_trial_result_to_dict_success_payload PASSED [ 20%]
    tests/test_benchmark_runner_payloads.py::TrialResultToDictTests::test_trial_result_to_dict_timeout_payload PASSED [ 40%]
    ```

    Test body lines asserting the exact key set, the timeout field values, the success score_result dict, and JSON round-trip:
    ```python
    def test_trial_result_to_dict_timeout_payload(self) -> None:
        adapter = RunnerAdapter("opencode", "1.2.3")
        runner = RunnerDouble(adapter, default_outcome="timeout")
        result = runner.run_trial(TASK, PROFILE, trial=1)
        res_dict = result.to_dict()

        expected_keys = {
            "trial_id",
            "status",
            "manifest",
            "rerun_command",
            "failure_kind",
            "error_message",
            "transcript",
            "score_result",
            "usage",
        }
        assert set(res_dict.keys()) == expected_keys
        assert res_dict["status"] == "pending"
        assert res_dict["failure_kind"] == "timeout"
        assert res_dict["score_result"] is None
        assert res_dict["transcript"] is None
        assert res_dict["manifest"] == result.manifest.to_dict()
        assert bool(res_dict["rerun_command"])
        assert res_dict["rerun_command"] == result.rerun_command

        assert json.loads(json.dumps(res_dict)) == res_dict

    def test_trial_result_to_dict_success_payload(self) -> None:
        adapter = RunnerAdapter("opencode", "1.2.3")
        runner = RunnerDouble(adapter, default_outcome="success")
        result = runner.run_trial(TASK, PROFILE, trial=1)
        res_dict = result.to_dict()

        assert res_dict["trial_id"] == "t1_m1_opencode_t1"
        assert res_dict["status"] == "completed"
        assert res_dict["failure_kind"] is None
        assert res_dict["score_result"] == {
            "verdict": "complete",
            "adversary_class": "",
            "reasons": ["no violation detected; terminal claim substantiated"],
            "claimed_complete": True,
        }

        assert json.loads(json.dumps(res_dict)) == res_dict
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `aw commit` output (or `git show --stat HEAD`) naming only `tests/test_benchmark_runner_payloads.py`; paste the bare `python3 -m pytest` summary line showing `passed` and no `failed`, any `CORE TIER BUDGET EXCEEDED` block verbatim, and the module's `--durations=0` output.
  - Observed evidence:
    `git show --stat HEAD`:
    ```
    commit b7e1030af8eb46b4fc9c20010aa1ffeefca733a3 (HEAD -> aw/lane/rempo8)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Sat Oct 24 09:30:03 2026 -0400

        work(rempo8): Lock TrialResult.to_dict and RunnerAdapter.adapter_digest behavior into the core tier

        AW-Run: run-20261024T014611Z-3126016
        AW-Item: rempo8
        AW-Runner: aw agy run

     tests/test_benchmark_runner_payloads.py | 135 ++++++++++++++++++++++++++++++++
     1 file changed, 135 insertions(+)
    ```

    Bare `python3 -m pytest` summary line and budget block:
    ```
    WARNING:
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 72.77s exceeded budget of 30.00s.
    Host 1-minute load average: 14.68 on 12 CPUs
    Core tier budget not enforced: host oversubscribed (1-minute load average above the CPU count)
    Top 10 slowest core tests:
       1.   8.33s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
       2.   8.15s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
       3.   7.55s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
       4.   5.59s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
       5.   5.08s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
       6.   5.06s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
       7.   4.52s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
       8.   4.16s  tests/test_notify_cli.py::test_listen_lifecycle_and_answering
       9.   3.36s  tests/test_local_leaks.py::ThisRepoTests::test_this_repo_working_tree_is_clean
      10.   2.83s  tests/test_status_set.py::TestScopePathCitationRewriteSetter::test_g_setter_spellings_rewrite_citing_pending_plan_and_skip_receipt_plan
    ===========================================================================================
    1815 passed, 11 warnings in 72.76s (0:01:12)
    ```

    Module `--durations=0` output (`python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_benchmark_runner_payloads.py`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1007861226
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/rempo8
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 5 items

    tests/test_benchmark_runner_payloads.py .....                            [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== slowest durations ===============================

    (15 durations < 0.005s hidden.  Use -vv to show these durations.)
    ============================== 5 passed in 0.22s ===============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the recorded `<E-03 commit>` and `<E-03 parent>` hashes; paste both outputs produced by `tools/mutation_probe.py` in E-04, each with `head` equal to the E-03 commit or later, a `selection` containing `-m core tests/test_benchmark_runner_payloads.py`, `verdict: killed`, `baseline_failing: 0`, and a `newly_failing` list naming at least one test of the new module; paste `git diff --stat <E-03 parent>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/`, both empty.
  - Observed evidence:
    `<E-03 commit>`: `b7e1030af8eb46b4fc9c20010aa1ffeefca733a3`
    `<E-03 parent>`: `18bd6aea22c1c87a9662fb9e98b3b6c0bf3efb41`

    Probe outputs:
    `agent_workflows/benchmark_runners.py::TrialResult.to_dict`:
    ```
    head: b7e1030af8eb46b4fc9c20010aa1ffeefca733a3
    target: agent_workflows/benchmark_runners.py::TrialResult.to_dict
    operator: return-none
    selection: -o addopts= -q -p no:randomly -n0 -m core tests/test_benchmark_runner_payloads.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 3
    newly_failing (3 total):
      tests.test_benchmark_runner_payloads.AdapterDigestTests::test_adapter_digest_reaches_trial_manifest
      tests.test_benchmark_runner_payloads.TrialResultToDictTests::test_trial_result_to_dict_success_payload
      tests.test_benchmark_runner_payloads.TrialResultToDictTests::test_trial_result_to_dict_timeout_payload
    wall_s: 5.24
    ```

    `agent_workflows/benchmark_runners.py::RunnerAdapter.adapter_digest`:
    ```
    head: b7e1030af8eb46b4fc9c20010aa1ffeefca733a3
    target: agent_workflows/benchmark_runners.py::RunnerAdapter.adapter_digest
    operator: return-none
    selection: -o addopts= -q -p no:randomly -n0 -m core tests/test_benchmark_runner_payloads.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 3
    newly_failing (3 total):
      tests.test_benchmark_runner_payloads.AdapterDigestTests::test_adapter_digest_equality_and_sensitivity
      tests.test_benchmark_runner_payloads.AdapterDigestTests::test_adapter_digest_pinned_and_canonical_json
      tests.test_benchmark_runner_payloads.AdapterDigestTests::test_adapter_digest_reaches_trial_manifest
    wall_s: 3.87
    ```

    Diff check:
    ```
    $ git diff --stat 18bd6aea22c1c87a9662fb9e98b3b6c0bf3efb41..HEAD -- agent_workflows/
    (empty)
    $ git diff --stat -- agent_workflows/
    (empty)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved (OQ-01). Scope fence: `- Scope-Paths:` (`tests/test_benchmark_runner_payloads.py`) is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and then justified (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path). No production file under `agent_workflows/` may change. Mutation checks use `tools/mutation_probe.py` only, after the E-03 commit. Commit only files you changed, through `aw commit rempo8 -- tests/test_benchmark_runner_payloads.py` (plus this plan when recording evidence); verify `git diff --cached --name-only`; never `git add -A`, never push. You MUST paste the ACTUAL runner and probe output into each `V-*`; never claim a test passed or a mutant was killed that you did not run. Lifecycle: after every `V-*` reads `Result: pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize rempo8` itself.
