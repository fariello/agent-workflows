# IPD: Restore behavioral test coverage for run_gates human decision gates

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `ziuj5c` (Set `trimgap`, group 14 of the `b1mx2w` filing plan) records that all 3 candidate production keys in `agent_workflows/run_gates.py` (157 exclusive lines), `evaluate_gate`, `GateDecision.is_approved` and `execute_gated_action`, are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. Their behavioral tests lived in class `TestHumanDecisionGates` of `tests/test_run_packet_gates.py` and in `tests/test_migration_complex.py`, both deleted by the suite trim `19313eed`. This module is the consent boundary: it is what guarantees a headless run stops at `needs_input` and that approval is never synthesized from a default. No routine test asserts that today, so a mutation that, for example, made a headless gate return `approved`, made a timeout apply an `approve` default, or made `execute_gated_action` call the action before checking the decision would pass the routine suite.
- Scope: Add ONE new behavioral test module, `tests/test_run_gates_restored_behavior.py`, marked `core`, that drives the 3 keys through their public call surfaces (`run_gates.evaluate_gate`, `run_gates.execute_gated_action`, `GateDecision.is_approved` and `GateDecision.to_dict`, `DecisionGate.to_dict`) and asserts on returned decisions, whether the gated action ran, and the `human_approval` ledger record. It restores the 8 tests of the deleted `TestHumanDecisionGates` class in pytest form and adds the branch cases that class did not pin (handler exception, every timeout-default branch, custom options, case handling, the stdin fallback). EXCLUDES any change to `agent_workflows/run_gates.py` or any other production file. EXCLUDES the `run_packet` classes of the same deleted file (owned by sibling `5jevb2`, backlog `aq04yg`) and EXCLUDES restoring `tests/test_migration_complex.py` (owned by sibling `pdemar`, backlog `x62jok`, which reaches `run_gates` only incidentally and explicitly leaves asserting its contract to this item).
- Scope-Paths: tests/test_run_gates_restored_behavior.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: ziuj5c
- Set: trimgap
- Order: 14
- Highest E allocated: 05
- Author: opencode
- Id: tf8fwt
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005

- 2026-10-17 to-review (opencode): authored from backlog `ziuj5c`. Ran the deleted `19313eed^:tests/test_run_packet_gates.py` `TestHumanDecisionGates` class unchanged against HEAD `1cba1220a` (8 passed) and measured every extra branch by direct call before writing an expected outcome (Findings F-02 to F-05), so the expected values below are observed rather than inferred from docstrings.
- 2026-10-17 draft (opencode): created.

## Goal

Make all 3 `unguarded-unreached` `run_gates` keys from backlog `ziuj5c` reached by the routine (bare, core-tier) test run, through behavioral tests that call the code and assert on decisions, action side effects and ledger records. Done means a mutation that synthesizes consent, mis-maps an option to a status, applies the wrong timeout policy, or runs a gated action without approval turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: new behavioral test module

- [ ] E-01 Create `tests/test_run_gates_restored_behavior.py` with `pytestmark = pytest.mark.core`, importing `agent_workflows.run_gates`, `run_engine`, `run_ledger_store` and `run_ledger_schema`. Add a module docstring naming backlog `ziuj5c`, findings `b1mx2w`, and the deleted source `tests/test_run_packet_gates.py` class `TestHumanDecisionGates` at `19313eed^`. Add fixtures: `deploy_gate` (the deleted `setUp` gate: id `deploy_approval_gate`, options `("approve", "reject", "abort")`, default `abort`, `timeout_seconds=30.0`, policy `refuse`), `side_effects` (a list the sample action appends to, returning `"DEPLOYMENT_SUCCESS"`), and a `timeout_handler` helper that raises `TimeoutError`. Use `tmp_path` only; spawn no subprocess. Disposition rule if a restored test (one of the eight `TestHumanDecisionGates` cases) or a measured expected value fails at execution HEAD (none did at authoring, F-02, nor at review, F-06): do not mark the owning item performed until it is dispositioned. Record it in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.
  - Depends on: none
  - Expected outcome: the file exists, is collected by a bare `python3 -m pytest` (it carries the `core` marker), and imports cleanly.
  - Execution state: pending

- [ ] E-02 Add headless and serialization tests. (a) Restored `test_headless_noninteractive_run_stops_at_needs_input_before_side_effect`: `execute_gated_action(deploy_gate, action, interactive=False)` returns status `needs_input`, `selected_option is None`, `approver is None`, `interactive is False`, result `None`, and `side_effects == []`. (b) Restored `test_no_synthesized_consent_even_if_default_is_approve`: a gate with `default_option="approve"` and policy `apply_default` evaluated headless is `needs_input` and `is_approved is False`. (c) `evaluate_gate(gate, current_time="T").to_dict()` equals exactly `{"gate_id": ..., "status": "needs_input", "selected_option": None, "approver": None, "actor": "runtime", "timestamp": "T", "interactive": False, "reason": ..., "is_approved": False}` with `reason` a non-empty string (shape asserted by key set and values, not by reason wording). (d) Without `current_time`, the decision timestamp is accepted by `run_ledger_schema.is_timestamp`. (e) `DecisionGate("g", "p").to_dict()` equals `{"gate_id": "g", "prompt": "p", "options": ["approve", "reject", "abort"], "default_option": "abort", "timeout_seconds": None, "timeout_policy": "refuse", "requires_human": True, "metadata": {}}`.
  - Depends on: E-01
  - Expected outcome: headless refusal, no-synthesized-consent, exact decision and gate dict shapes, and the default timestamp pass.
  - Execution state: pending

- [ ] E-03 Add interactive option-mapping tests as one parametrized table over `evaluate_gate(gate, interactive=True, input_handler=lambda _g: choice, approver="alice")`, each row asserting `status`, `is_approved`, `actor` and `selected_option`: `approve`, `Yes`, `proceed` -> `approved`/`True`/`human`; `"  approve "` -> `approved` with `selected_option == "approve"` (whitespace stripped); `reject`, `deny` -> `rejected`/`False`/`human`; `abort`, `ABORT` -> `aborted`/`False`/`human`; `unlisted_invalid_option` -> `refused`/`False` (restored `test_invalid_option_chosen_refused_at_gate`); `"   "` -> `refused` with `actor == "runtime"` (restored `test_empty_input_at_gate_refused`); a gate with custom options `("ship-it", "reject")` and choice `ship-it` -> `approved`; a gate with options `("Ship-It",)` and choice `ship-it` -> `refused` (custom-option match is case-sensitive). Also: an `approved` decision carries `approver == "alice"`; a handler raising `ValueError("x")` -> `refused`, `actor == "runtime"`, `approver is None`; and only the `approved` rows have `is_approved` True (the property is status-equality).
  - Depends on: E-01
  - Expected outcome: every mapping row and the handler-exception case pass.
  - Execution state: pending

- [ ] E-04 Add timeout-policy and stdin-fallback tests. (a) Timeout table, each with `input_handler=timeout_handler`: policy `refuse` (restored) -> `timed_out`; policy `fail` -> `timed_out`; `apply_default` with default `abort` (restored) -> `aborted`, `selected_option == "abort"`; `apply_default` with default `approve` -> `needs_input`, `selected_option is None`, `is_approved is False` (consent never synthesized on timeout); `apply_default` with default `reject` -> `rejected`; `apply_default` with a non-token default `later` -> `rejected`; `apply_default` with `default_option=None` -> `timed_out`. Every timeout row has `actor == "runtime"` and `approver is None`. (b) Stdin fallback (no `input_handler`), using pytest `monkeypatch.setattr("builtins.input", ...)`: an empty reply on a gate with default `abort` -> `aborted` with `selected_option == "abort"`, and the captured prompt string contains the gate id, the `approve/reject/abort` option list and the `[abort]` default marker; reply `approve` -> `approved`; `input` raising `EOFError` -> `aborted`; `input` raising `KeyboardInterrupt` -> `aborted`; `input` raising `RuntimeError` -> `timed_out` under policy `refuse`; an empty reply on a gate with `default_option=None` -> `refused`.
  - Depends on: E-01
  - Expected outcome: every timeout row and stdin-fallback case listed above passes with no real terminal read.
  - Execution state: pending

- [ ] E-05 Add `execute_gated_action` tests. (a) Restored `test_interactive_choice_recorded_and_executes_action_when_approved`: approval by `alice-lead` returns result `"DEPLOYMENT_SUCCESS"`, `side_effects == [1]` (exactly one call), decision approved with that approver. (b) Parametrized refusal rows, each asserting result `None` and `side_effects == []`: interactive `reject` (restored), `abort`, unlisted option (restored), handler `TimeoutError` under policy `refuse`, and headless. (c) Restored `test_gate_integration_with_run_engine_and_ledger`: a `run_ledger_store.RunLedgerStore(tmp_path / "run.jsonl")` seeded with the deleted test's `run` and `requirement_set` records and a `run_engine.RunEngine` over the one-step `gated-wf` whose `S-01` carries `gates: ["deploy_approval_gate"]`; `engine.get_runnable_steps() == []` before; after an approved `execute_gated_action(..., engine=engine, approver="carol-lead")`, the runnable step ids are `["S-01"]` and `store.read_records(verify=True)` holds exactly one `human_approval` record with `gate == "deploy_approval_gate"`, `approver == "carol-lead"`, `actor == "human"`. (d) Control: a REJECTED `execute_gated_action` with the same seeded engine appends no `human_approval` record (record count unchanged) and `get_runnable_steps()` stays `[]`.
  - Depends on: E-01
  - Expected outcome: approved action runs exactly once and records approval; every refusal leaves the action uncalled and the ledger unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). No `inspect`, `ast`, regex over production source, or docstring pinning. Every assertion calls the function and checks a returned decision, whether the action was called, or a ledger record. `reason` strings are asserted only as non-empty, never for wording. The stdin prompt fragments in E-04 are the rendered output a human reads, asserted for presence of the gate id, options and default only.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`), under a 30s budget. The new module must carry `pytestmark = pytest.mark.core` and stay fast; the restored class ran its 8 tests in 0.38s including collection (F-02).
- Sibling plans `5jevb2` (Order 5) and `33f8tn` (Order 9) set the precedent this plan follows: one new `*_restored_behavior.py` core-marked module per backlog item, no production edits, mutation spot-checks as reverted scratch edits.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows for `agent_workflows/run_gates.py::*`; `rg -l run_gates tests/` | Exactly 3 `run_gates` keys, all `unreached` / `unguarded-unreached`. No surviving test module imports `run_gates`: the only `tests/` hits (`test_runner_shared.py`, `test_run_evidence_completion.py`, `test_lifecycle_style.py`) mention the name in strings or comments and never call it. |
| F-02 | `git show 19313eed^:tests/test_run_packet_gates.py > tmp; python3 -m pytest -o addopts="" -k HumanDecision tmp` at HEAD `1cba1220a` | `8 passed, 12 deselected in 0.38s`. The deleted class still describes current behavior and can be restored with its original inputs. |
| F-03 | direct calls of `evaluate_gate` with a handler | `Yes`/`approve` -> `approved`; `deny` -> `rejected`; `abort`/`ABORT` -> `aborted` actor `human`; `"  approve "` stored as `approve`; custom option `ship-it` in `("ship-it","reject")` -> `approved`; `ship-it` against `("Ship-It",)` -> `refused`; handler raising `ValueError` -> `refused` with runtime actor. |
| F-04 | direct calls with a `TimeoutError` handler | `apply_default` + `approve` -> `needs_input` with `selected_option None`; `+ reject` and `+ later` -> `rejected`; `+ None` -> `timed_out`; policy `fail` -> `timed_out`. |
| F-06 | plan review, HEAD `5299cf65d`: deleted class rerun, every E-02 to E-05 expected value re-measured by direct call, then a scratch pytest module encoding E-02 to E-05 and scratch mutations of `agent_workflows/run_gates.py` (restored after each; `git diff agent_workflows/` empty afterwards) | Deleted class: `8 passed, 12 deselected in 0.29s`. Every expected value in E-02 to E-05 reproduced, including the rejected-control (d): `rejected None True []` (status, result, record count unchanged, runnable steps). Scratch module: `26 passed in 0.47s`, `run_gates.py 102 stmts, 0 miss, 100%`. KILLED: the three `b1mx2w` operators (`execute_gated_action@return-none`, `GateDecision.is_approved@return-false`, `evaluate_gate@return-none`); the four V-item mutations; and four extra mutations (no `record_approval` call, `EOFError` mapped to `approve`, case-insensitive custom-option match, handler exception mapped to `approved`). Deleting the `norm_def in _APPROVAL_TOKENS` guard makes an `approve` default on timeout return `rejected` (`rejected approve False`), not an approval. |
| F-05 | direct calls with `builtins.input` replaced | Prompt is `'\n[GATE g] p? (approve/reject/abort) [abort]: '`; empty reply -> `aborted`/`abort`; `approve` -> `approved`; `EOFError` -> `aborted`; `RuntimeError` -> `timed_out`; empty reply with no default -> `refused`. Headless `execute_gated_action` returned `needs_input`, result `None`, and never called the action. `DecisionGate("g","p").to_dict()` and the headless `GateDecision.to_dict()` match the shapes in E-02. |

## Proposed changes (ordered, validatable)

1. E-01 creates the core-marked module and fixtures.
2. E-02 covers the headless path of `evaluate_gate`, `GateDecision.is_approved`, and both `to_dict` shapes.
3. E-03 covers the interactive option-to-status mapping of `evaluate_gate`.
4. E-04 covers timeout policies and the stdin fallback of `evaluate_gate`.
5. E-05 covers `execute_gated_action`, including its ledger side effect.

## Deferred / out of scope (with reason)

- The `run_packet` classes of the deleted `tests/test_run_packet_gates.py` exercise `agent_workflows/run_packet.py`, not `run_gates`.
  - Carrier: 5jevb2
- Restoring `tests/test_migration_complex.py`, the other deleted file the backlog item names, is owned by the `migration_complex` item; it reaches `run_gates` only through `migration_complex` callers and explicitly leaves the `run_gates` contract to this item.
  - Carrier: pdemar

## Scope check

- Over-scope: none. One new test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none. All 3 keys named by `ziuj5c` are covered by E-02 to E-05, every branch of `evaluate_gate` measured in F-03 to F-05 has a row, and V-05 demonstrates each key is guarded by its `b1mx2w` operator (F-06).

## Required tests / validation

- `python3 -m pytest tests/test_run_gates_restored_behavior.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest` passes (core tier, including the new module, within the 30s budget), with the summary line pasted.
- Reach: `python3 -m pytest tests/test_run_gates_restored_behavior.py -o addopts="" --cov=agent_workflows.run_gates --cov-report=term-missing` (or `coverage run -m pytest ...` then `coverage report -m --include=agent_workflows/run_gates.py`) shows the bodies of all 3 keys executed; paste the output.
- Mutation spot-checks (scratch edits, never committed, each reverted): listed per V-item below, plus the three `b1mx2w` key operators in V-05; then confirm `git diff agent_workflows/` is empty and delete any `.coverage` data file.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Should the new module be core-marked, or only non-slow?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: core-marked. The routine gate a bare `python3 -m pytest` runs is the core tier (`conftest.pytest_collection_modifyitems`), so non-core coverage would still be absent from the merge gate, which is the gap `ziuj5c` records. The restored cases run in well under a second (F-02); V-01 requires the runtime be shown.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short` and `git diff --stat HEAD` showing only `tests/test_run_gates_restored_behavior.py` added; paste the `tests/test_run_gates_restored_behavior.py: N` line from bare `python3 -m pytest --collect-only -q` (the core selection prints one `path: N` line per file, so `rg -c` would print 1, not N), with N matching the per-test list of the Required tests `-v` run; paste the bare `python3 -m pytest` summary line (if it prints `CORE TIER BUDGET EXCEEDED`, paste that too with the same run's line without the module, and report it rather than un-marking tests; a pre-existing overrun is tracked separately, backlog `o58dro`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing the headless, no-synthesized-consent, dict-shape and timestamp tests as PASSED, and the failure produced by a scratch edit making the non-interactive branch of `evaluate_gate` return `GATE_STATUS_APPROVED` (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing every option-mapping row and the handler-exception case as PASSED, and the failure produced by a scratch edit making the abort branch of `evaluate_gate` return `GATE_STATUS_REJECTED` instead of `GATE_STATUS_ABORTED` (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` output listing every timeout row and stdin-fallback case from E-04 as PASSED; paste the failure produced by a scratch edit disabling the `norm_def in _APPROVAL_TOKENS` guard (for example `if False:`), which makes an `approve` default on timeout fall through to `rejected` instead of `needs_input` (F-06), with the `apply_default` + `approve` row among the failures; and paste the failure produced by a scratch edit mapping the stdin `EOFError`/`KeyboardInterrupt` fallback to `"approve"` instead of `"abort"` (each reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` output listing the approved, refusal-row, ledger-integration and rejected-control tests as PASSED; the failure produced by a scratch edit moving `result = action()` above the `if not decision.is_approved` check in `execute_gated_action`, and the failure produced by replacing the `engine.record_approval(` call with a no-op (each reverted afterwards); the failures produced by each `b1mx2w` operator applied at the top of its key's body, `execute_gated_action` -> `return None`, `GateDecision.is_approved` -> `return False`, `evaluate_gate` -> `return None` (each reverted afterwards, all three KILLED); the coverage output showing the bodies of all 3 keys executed; and a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:

- Open questions: all resolved (OQ-01).
- Scope fence: `tests/test_run_gates_restored_behavior.py` is the only declared path. An out-of-scope edit (for example a gated `bug` backlog item filed under the E-01 disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks are scratch edits to `agent_workflows/run_gates.py` that must be reverted before commit and must be absent from the diff; delete any `.coverage` data file a coverage run leaves behind.
- Honesty: you MUST paste the actual runner output for every test, coverage and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit tf8fwt -- tests/test_run_gates_restored_behavior.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize tf8fwt` instead. Never hand-`git mv` the plan.
