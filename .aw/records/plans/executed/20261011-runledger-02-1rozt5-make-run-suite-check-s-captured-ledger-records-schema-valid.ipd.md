# IPD: Make run_suite_check's captured ledger records schema-valid (runtime / test_report)

- Date: 2026-10-11
- Kind: child
- Concern: `runner_shared.run_suite_check` calls `run_evidence.capture_command` with `actor="driver"` and `evidence_kind="tests"`, neither of which is in the run-ledger schema's closed vocabulary, so both records it produces fail `run_ledger_schema.validate_record` (`RL-E014`, `RL-E033`).
- Scope: Change the two literal arguments at the single defective call site to the legal `actor="runtime"` and `evidence_kind="test_report"`, and add one behavior test that drives the real `run_suite_check` and validates the records `capture_command` actually returned. No schema vocabulary change, no ledger wiring, no change to `host_runner`.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_capture_command_contract.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 1g8lbe
- Blocks-Release: next
- Set: runledger
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1rozt5

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 1rozt5 verified (set runledger, attempt 1).
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (MEDIUM, fixed: suite bar by failing node id, not total), PR-002 (LOW, fixed: finalize ownership and mutation-revert guard in gate). F-01/F-02/F-03 re-measured at HEAD 7b8dde681; E-03's spy test shape demonstrated (HEAD args: RL-E014 / RL-E014+RL-E033; fixed args: clean; SuiteCheckResult unchanged). Record: .aw/records/reviews/20261011-runledger-02-1rozt5-make-run-suite-check-s-captured-ledger-records-schema-valid.review.md.
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-11 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `1g8lbe` after plan `rdjka2` (executed) resolved its OQ-01 to option (b); OQ-02 resolved here from repository evidence.

## Goal

Make the two ledger-shaped records that `runner_shared.run_suite_check` builds on every integration-gate suite run schema-valid, by passing a legal actor role and a legal evidence kind, so the records stop being latently invalid and a future store append would not refuse them. Pin the outcome with a test that validates the records actually produced.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline and re-measure

- [x] E-01 Re-measure F-01 and F-02 at the executing HEAD and capture the bare-suite baseline before any edit.
  - Depends on: none
  - Expected outcome: `git rev-parse HEAD` recorded; the in-process snippet from F-01 re-run, showing `driver`/`tests` produce `RL-E014` on the `tool_event` and `RL-E014` plus `RL-E033` on the envelope, and `runtime`/`test_report` produce `ok=True` on both; `grep -n 'actor="driver"' agent_workflows/runner_shared.py` confirms the call site still exists inside `run_suite_check`; bare `python3 -m pytest` summary line AND its failing node ids (if any) captured as the baseline. If the call site has already changed or the schema vocabulary now contains `driver` or `tests`, STOP and report the premise as moved.
  - Execution state: performed

### Task group 2: Fix the call site

- [x] E-02 In `runner_shared.run_suite_check`, change the `run_evidence.capture_command(...)` keyword arguments from `evidence_kind="tests"` to `evidence_kind="test_report"` and from `actor="driver"` to `actor="runtime"`, and add a short comment beside them stating that both values must stay inside `run_ledger_schema.ROLES` / `EVIDENCE_KINDS` (backlog `1g8lbe`, decision in OQ-01 of this plan). No other line of the function changes.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/runner_shared.py` shows exactly the two argument values changed plus the added comment lines; `SuiteCheckResult` construction, timeout handling and the out-of-band `stdout`/`stderr` reads are untouched.
  - Execution state: performed

### Task group 3: Behavior test

- [x] E-03 Add `test_run_suite_check_records_are_schema_valid` to `tests/test_capture_command_contract.py`. It patches `runner_shared.SUITE_CHECK_ARGV` to a tiny `sys.executable -c "print('1 passed in 0.01s')"` argv (the existing `test_run_suite_check_consumer_contract` pattern), wraps `run_evidence.capture_command` with a spy (`mock.patch.object(run_evidence, "capture_command", side_effect=...)` delegating to the real function and storing its return value), calls the real `runner_shared.run_suite_check(Path("."), "run-abc123ff")`, and asserts: the spy was called once, `run_ledger_schema.validate_record(tool_event).ok` is True and `run_ledger_schema.validate_record(envelope).ok` is True (failure message printing the findings), and the `SuiteCheckResult` is still `passing=True` with summary `1 passed in 0.01s`.
  - Depends on: E-02
  - Expected outcome: the new test passes after E-02 and, when E-02 is temporarily reverted in the working tree, fails naming `RL-E014`/`RL-E033` (demonstrated, then the revert is undone). The test reads no production source text.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Suite command is BARE `python3 -m pytest` (AGENTS.md repository development contract); do not add `-n0`, a second `-q`, or `-p no:randomly`. Narrowed per-test runs use `-o addopts=""`.
- No code-pinning tests (AGENTS.md, GUIDING_PRINCIPLES P16): the test must call `run_suite_check` and assert on `validate_record`'s findings, never grep for the literal argument. The backlog item restates this ("any test must call `capture_command` and assert on `validate_record`'s findings").
- `tests/test_capture_command_contract.py` already owns `run_suite_check`'s consumer contract (`test_run_suite_check_consumer_contract`, which patches `runner_shared.SUITE_CHECK_ARGV`), so the new test belongs beside it.
- `actor="runtime"` is the role the repository already uses for non-agent, machine-driven ledger actions: `run_engine.RunEngine.release_step` / `start_step` default `actor: str = "runtime"`, `run_gates` passes `actor="runtime"`, and `run_cli` defaults `actor ... or "runtime"`.
- `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json` contains an AST dump of `run_suite_check` with the literal `'driver'`/`'tests'`; a grep of `tests/` and `agent_workflows/` finds no test or code reading that fixture, so it is a retained historical capture (the same status `tests/test_runner_shared.py`'s module docstring records for its sibling fixture) and is deliberately NOT edited.
- Commit through `aw commit <plan> -- <paths>`; never push.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The defect reproduces at HEAD `502e8fd5e`: `capture_command(..., actor="driver", evidence_kind="tests")` returns a `tool_event` failing `RL-E014` and an envelope failing `RL-E014` and `RL-E033`; with `actor="runtime", evidence_kind="test_report"` both validate `ok=True, findings=()`. `run_ledger_schema.ROLES` is `coordinator, corrector, executor, human, investigator, runtime, verifier`; `EVIDENCE_KINDS` is `command, diff, artifact, test_report, inspection`. | In-process: `run_evidence.capture_command('run-abcdef1234', ['true'], actor=a, evidence_kind=k)` then `run_ledger_schema.validate_record` on both returned records, for both pairs; printed `sorted(run_ledger_schema.ROLES)`. |
| F-02 | Only ONE production call site is defective: `runner_shared.run_suite_check` passes `evidence_kind="tests"` and `actor="driver"`. `host_runner.run_worker_process`'s default branch passes neither, taking the legal defaults `executor`/`command`; executed plan `rdjka2` F-12 measured both of its records `(True, [])`. | Read `runner_shared.run_suite_check` (the `run_evidence.capture_command(` call) and `host_runner.run_worker_process` (the `else:` arm calling `_ev.capture_command(`); `rdjka2` F-12 "CORRECTED AT REVIEW". |
| F-03 | The records are discarded today: `run_suite_check` binds the envelope to `_envelope` and reads only `tool_event.get("exit_code")` plus the out-of-band `tool_event.stdout`/`.stderr`. So the change cannot alter any observable `SuiteCheckResult`; it only alters the content of two in-memory records. | Read the body of `runner_shared.run_suite_check`. |
| F-04 | The governing decision is made: plan `rdjka2` (executed) resolved its OQ-01 to option (b), driver runs keep `state.json`/`events.jsonl` and do not write a ledger; its OQ-02 named this carrier as owner of the remedy choice. | `.aw/records/plans/executed/20261002-runledger-01-rdjka2-...ipd.md`, OQ-01 "MAINTAINER RESOLUTION (2026-10-08 ...): OPTION (b)" and OQ-02 "Carrier: 1g8lbe". |
| F-05 | Stopping record construction is not a cheaper or cleaner remedy: `capture_command` is the shared bounded subprocess primitive that supplies the timeout-to-124 and spawn-failure-to-127 mapping, per-stream output bound, and the out-of-band `stdout`/`stderr` that `run_suite_check`'s fail-closed reading depends on (its docstring: "`run_evidence.capture_command` already converts a timeout into exit 124 and any other exception into exit 127 instead of raising"). Replacing it would reimplement that machinery or require a new non-record variant of the API. | `run_evidence.capture_command` signature and docstring; `run_suite_check` docstring "FAIL CLOSED (E-02)". |

## Proposed changes (ordered, validatable)

1. Re-measure F-01 and F-02 and capture the baseline (E-01).
2. Change the two argument values at the single defective call site to `runtime` / `test_report` (E-02).
3. Add a behavior test that drives the real `run_suite_check` and validates the records it produced (E-03).

## Deferred / out of scope (with reason)

- WRITING THESE RECORDS TO ANY LEDGER. Out of scope by the maintainer's `rdjka2` OQ-01 decision (option (b)): driver runs do not write a ledger. The records stay discarded; this plan only makes them valid.
  - Carrier-Declined: NOT A DEBT. A recorded maintainer decision settled it; there is nothing outstanding to carry.
- ADDING `driver` TO `ROLES` OR `tests` TO `EVIDENCE_KINDS`. Rejected: `EVIDENCE_KINDS` is documented as "kept in sync with the workflow schema's EVIDENCE_KINDS", and widening a closed ledger vocabulary to fit one discarding caller changes a contract for every ledger consumer. `runtime`/`test_report` already exist and mean exactly this.
  - Carrier-Declined: NOT A DEFECT. The existing vocabulary covers the case; widening it is a rejected option, not deferred work.
- `host_runner.run_worker_process`. Already valid (F-02); editing it would be over-scope.
  - Carrier-Declined: NOT A DEFECT. Measured valid.
- `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`. A historical AST capture that no test reads; refreshing it would be a code-pinning artifact edit with no consumer.
  - Carrier-Declined: NOT A DEFECT. Unread retained fixture.

## Scope check

- Over-scope: none. Two keyword-argument values plus a comment in one function, and one added test.
- Under-scope: none. The item names one defective call site and one sibling to consider; the sibling is measured valid and explicitly left alone.

## Required tests / validation

- Bare `python3 -m pytest` summary line before (E-01) and after (V-02). The bar is by FAILING NODE ID, not by total: every node id failing after the change must also have failed in the E-01 baseline, and the new test's node id must appear as passing. A changed total is not itself a finding, since the suite size drifts between runs on this tree.
- The new test run alone with `-o addopts=""`, passing after E-02, and shown failing with `RL-E014`/`RL-E033` when E-02 is temporarily reverted.
- The existing `test_run_suite_check_consumer_contract` still passes (proves `SuiteCheckResult` behavior is unchanged).
- `aw ipd lint` conforming on this plan.

## Spec / documentation sync

N/A. No spec names `run_suite_check`'s actor or evidence kind; the change makes produced records conform to the existing `run_ledger_schema` contract rather than changing a contract. No user-facing doc mentions these values.

## Open questions

### OQ-01: Under answer (b), should `run_suite_check` stop constructing ledger records, or pass a legal role and evidence kind? (carried from `rdjka2` OQ-02)

- Blocking: no
- Status: resolved
- Owner: author of this plan (carrier `1g8lbe`), from repository evidence
- Resolution or deferral rationale: RESOLVED: pass `actor="runtime"` and `evidence_kind="test_report"`. Evidence: F-05 shows `capture_command` is the shared bounded-subprocess primitive whose timeout/spawn-failure mapping and out-of-band streams `run_suite_check`'s fail-closed contract depends on, so "stop constructing records" means either duplicating that machinery or adding a new API variant, both larger and less reversible than a two-value change. `runtime` is the repository's established role for machine-driven ledger actions (`run_engine.RunEngine.start_step`, `run_gates`, `run_cli` defaults), and `test_report` is the schema's evidence kind for a test run. The change is invisible to `SuiteCheckResult` (F-03), trivially reversible, and keeps the records valid should a future consumer ever bind them. This is not a scope, priority, risk-appetite or public-contract call, so it is resolved here rather than escalated; a reviewer who prefers dropping record construction can dispute it at `/plan-review`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: PASTE `git rev-parse HEAD`, the exact F-01 snippet and its ACTUAL output for both argument pairs, the `grep -n` output locating the call site, and the bare `python3 -m pytest` baseline summary line. State MATCH or DIVERGE for F-01 and F-02. FAILS if any value is reported from memory.
  - Observed evidence:
    Measurement HEAD:
    ```
    $ git rev-parse HEAD
    6eb2906d24a4273cfce488e0c7ec29fea94dda24
    ```

    F-01 in-process measurement snippet:
    ```python
    from agent_workflows import run_evidence, run_ledger_schema
    print('ROLES:', sorted(run_ledger_schema.ROLES))
    print('EVIDENCE_KINDS:', sorted(run_ledger_schema.EVIDENCE_KINDS))

    for actor, kind in [('driver', 'tests'), ('runtime', 'test_report')]:
        te, env = run_evidence.capture_command('run-abcdef1234', ['true'], actor=actor, evidence_kind=kind)
        v_te = run_ledger_schema.validate_record(te)
        v_env = run_ledger_schema.validate_record(env)
        print(f'actor={actor}, evidence_kind={kind}:')
        print('  tool_event:', v_te.ok, [f.code for f in v_te.findings])
        print('  envelope:  ', v_env.ok, [f.code for f in v_env.findings])
    ```
    Actual output:
    ```
    ROLES: ['coordinator', 'corrector', 'executor', 'human', 'investigator', 'runtime', 'verifier']
    EVIDENCE_KINDS: ['artifact', 'command', 'diff', 'inspection', 'test_report']
    actor=driver, evidence_kind=tests:
      tool_event: False ['RL-E014']
      envelope:   False ['RL-E014', 'RL-E033']
    actor=runtime, evidence_kind=test_report:
      tool_event: True []
      envelope:   True []
    ```

    Call site location:
    ```
    $ grep -n 'actor="driver"' agent_workflows/runner_shared.py
    41752:            actor="driver",
    ```

    Bare pytest baseline summary:
    ```
    7489 passed, 2 skipped, 3 warnings in 1115.27s (0:18:35)
    ```
    Failing node ids: none.

    Status for F-01 and F-02:
    - F-01: MATCH
    - F-02: MATCH
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE `git diff agent_workflows/runner_shared.py` in full and confirm by inspection that only the `evidence_kind` and `actor` values changed (to `test_report` and `runtime`) plus added `#` comment lines, all inside `run_suite_check`. PASTE the post-change bare `python3 -m pytest` summary line and failing node ids beside the E-01 baseline, and state that no node id fails now that passed then. FAILS if any other executable line changed, or if a node id that passed at baseline now fails.
  - Observed evidence:
    Full diff of agent_workflows/runner_shared.py:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 272aa1e74..7d0c81d56 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -41748,8 +41748,10 @@ def run_suite_check(
                 run_id,
                 list(SUITE_CHECK_ARGV),
                 cwd=repo_dir,
    -            evidence_kind="tests",
    -            actor="driver",
    +            # Both values must stay inside run_ledger_schema.ROLES / EVIDENCE_KINDS
    +            # (backlog 1g8lbe, decision in OQ-01 of plan 1rozt5).
    +            evidence_kind="test_report",
    +            actor="runtime",
                 timeout=timeout,
                 max_output_bytes=512_000,
             )
    ```

    Inspection confirmation:
    Only `evidence_kind` (from `"tests"` to `"test_report"`) and `actor` (from `"driver"` to `"runtime"`) values changed, plus two comment lines referencing `run_ledger_schema.ROLES / EVIDENCE_KINDS`, all strictly inside `run_suite_check`. No other executable line changed; SuiteCheckResult construction, timeout handling, and out-of-band stdout/stderr handling are untouched.

    Post-change bare pytest summary beside E-01 baseline:
    - Baseline: 7489 passed, 2 skipped, 3 warnings in 1115.27s (0:18:35) (failing node ids: none)
    - Post-change: 7490 passed, 2 skipped, 3 warnings in 611.63s (0:10:11) (failing node ids: none)
    - Node id comparison: No node id fails now that passed then (0 failures in both). The post-change run includes exactly +1 passing test (`tests/test_capture_command_contract.py::test_run_suite_check_records_are_schema_valid`).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the full source of the new test and confirm it contains no `inspect`, no `ast`, and no regex or substring search over production source. PASTE `python3 -m pytest -o addopts="" tests/test_capture_command_contract.py -v` output showing the new test and `test_run_suite_check_consumer_contract` both PASSED. PASTE the output of the new test run with E-02 temporarily reverted, showing it FAILED with `RL-E014` and `RL-E033` in the message, then `git diff` showing E-02 restored. Code path observed: `runner_shared.run_suite_check` -> `run_evidence.capture_command` (real, spied).
  - Observed evidence:
    Full source of test_run_suite_check_records_are_schema_valid:
    ```python
    def test_run_suite_check_records_are_schema_valid() -> None:
        """run_suite_check produces schema-valid tool_event and envelope ledger records."""
        pass_argv = [sys.executable, "-c", "print('1 passed in 0.01s')"]
        captured_records: list[tuple[run_evidence.CapturedToolEvent, dict]] = []
        real_capture_command = run_evidence.capture_command

        def spy_capture_command(*args, **kwargs):
            result = real_capture_command(*args, **kwargs)
            captured_records.append(result)
            return result

        with (
            mock.patch.object(runner_shared, "SUITE_CHECK_ARGV", pass_argv),
            mock.patch.object(run_evidence, "capture_command", side_effect=spy_capture_command),
        ):
            result = runner_shared.run_suite_check(Path("."), "run-abc123ff")

        assert len(captured_records) == 1
        tool_event, envelope = captured_records[0]

        val_tool_event = run_ledger_schema.validate_record(tool_event)
        val_envelope = run_ledger_schema.validate_record(envelope)

        assert (
            val_tool_event.ok and val_envelope.ok
        ), f"tool_event findings: {[f.code for f in val_tool_event.findings]}; envelope findings: {[f.code for f in val_envelope.findings]}"
        assert val_tool_event.ok is True, f"tool_event findings: {val_tool_event.findings}"
        assert val_envelope.ok is True, f"envelope findings: {val_envelope.findings}"

        assert result.passing is True
        assert result.summary == "1 passed in 0.01s"
    ```
    Confirmation: The test contains no `inspect`, no `ast`, and no regex or substring search over production source.

    Targeted test run output (`python3 -m pytest -o addopts="" tests/test_capture_command_contract.py -v`):
    ```
    tests/test_capture_command_contract.py::test_captured_tool_event_type_contract PASSED [ 10%]
    tests/test_capture_command_contract.py::test_run_worker_process_consumer_contract PASSED [ 20%]
    tests/test_capture_command_contract.py::test_capture_command_producer_contract PASSED [ 30%]
    tests/test_capture_command_contract.py::test_capture_command_persistence_clean_in_real_store PASSED [ 40%]
    tests/test_capture_command_contract.py::test_mock_shape_hazard_per_consumer PASSED [ 50%]
    tests/test_capture_command_contract.py::test_capture_command_key_set_per_call_shape PASSED [ 60%]
    tests/test_capture_command_contract.py::test_capture_command_error_paths PASSED [ 70%]
    tests/test_capture_command_contract.py::test_capture_command_decode_asymmetry PASSED [ 80%]
    tests/test_capture_command_contract.py::test_run_suite_check_consumer_contract PASSED [ 90%]
    tests/test_capture_command_contract.py::test_run_suite_check_records_are_schema_valid PASSED [100%]

    ============================== 10 passed in 7.98s ==============================
    ```

    Output with E-02 temporarily reverted:
    ```
    ________________ test_run_suite_check_records_are_schema_valid _________________

        def test_run_suite_check_records_are_schema_valid() -> None:
            ...
    >       assert (
                val_tool_event.ok and val_envelope.ok
            ), f"tool_event findings: {[f.code for f in val_tool_event.findings]}; envelope findings: {[f.code for f in val_envelope.findings]}"
    E       AssertionError: tool_event findings: ['RL-E014']; envelope findings: ['RL-E014', 'RL-E033']
    E       assert (False)
    E        +  where False = ValidationResult(ok=False, findings=(Finding(code='RL-E014', where='actor', message="unknown actor role 'driver'"),)).ok

    tests/test_capture_command_contract.py:337: AssertionError
    NOTE: 9 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    =========================== short test summary info ============================
    FAILED tests/test_capture_command_contract.py::test_run_suite_check_records_are_schema_valid
    ======================= 1 failed, 9 deselected in 4.80s ========================
    ```

    git diff agent_workflows/runner_shared.py showing E-02 restored:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 272aa1e74..7d0c81d56 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -41748,8 +41748,10 @@ def run_suite_check(
                 run_id,
                 list(SUITE_CHECK_ARGV),
                 cwd=repo_dir,
    -            evidence_kind="tests",
    -            actor="driver",
    +            # Both values must stay inside run_ledger_schema.ROLES / EVIDENCE_KINDS
    +            # (backlog 1g8lbe, decision in OQ-01 of plan 1rozt5).
    +            evidence_kind="test_report",
    +            actor="runtime",
                 timeout=timeout,
                 max_output_bytes=512_000,
             )
    ```

    Code path observed: `runner_shared.run_suite_check` -> `run_evidence.capture_command` (real, spied).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the two Scope-Paths files plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never push. Verify `git diff --cached --name-only` before committing. Run the suite BARE and paste the actual summary line; never claim a pass not run. If E-01 shows the premise moved (call site already fixed, or vocabulary widened), stop and report rather than editing.

The E-03 mutation check reverts E-02 only in the working tree and restores it before any commit; never commit the reverted state, and paste `git diff` after restoring.

POST-GATE LIFECYCLE. The terminal move to `.aw/records/plans/executed/` goes through the lifecycle tooling, never a hand `git mv`: in a managed lane the runner finalizes; when executing by hand, run `aw ipd finalize 1rozt5`. Either way, only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. Backlog `1g8lbe` is set `graduated` by the authoring run; it closes `done` via the From-Backlog handoff once this plan is executed, which carries its `- Blocks-Release: next` gate.
