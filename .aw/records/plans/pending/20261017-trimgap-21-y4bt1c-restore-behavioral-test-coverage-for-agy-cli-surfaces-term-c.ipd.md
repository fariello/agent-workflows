# IPD: Restore behavioral test coverage for agy CLI surfaces, Term components, result types and comms validators

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the output-surface slice: groups 30 (`agy_sessions.py`, 2 keys), 32 (`term.py`, 8), 36 (`attention.py`, 1), 38 (`agy_view.py`, 1), 42 (`result_types.py`, 3), 48 (`agy_run.py`, 1), 54 (`runner_stop.py`, 1) and 56 (`comms.py`, 2), 19 keys in all.
- Scope: Restore seven deleted test modules from `19313eed^` at their original paths, minus code-pinning tests, with `core` markers, plus residual tests for the four keys whose wrong value no restored test detects (F-04). The 19 keys: `agy_sessions.parse_args`, `agy_sessions.main`; `term.Term.format_diagnostic`, `Term.diagnostic`, `Term.title`, `Term.evidence`, `Term.fix`, `Term.outcome`, `Term.preview`, `Term.section`; `attention._colorize_tree_segment`; `agy_view.main`; `result_types.Diagnostic.from_drift`, `CommandResult.has_findings`, `CommandResult.is_error`; `agy_run.main`; `runner_stop.reset_signal_ladder`; `comms.is_ack_valid`, `comms.is_envelope_header_valid`. EXCLUDES any production change; EXCLUDES `tests/test_attention_priority_blocker.py` (F-05).
- Scope-Paths: tests/test_agy_tools_graduation.py, tests/test_term_components.py, tests/test_attention_stem.py, tests/test_renderer_boundary.py, tests/test_output_contract.py, tests/test_interrupt_tty_wedge.py, tests/test_comms.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 21
- Highest E allocated: 05
- Author: opencode
- Id: y4bt1c

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`, measured per-key reach via coverage contexts, durations, and an early-return mutation sweep over the 19 keys (both polarities for boolean keys); scratch edits reverted, `.coverage` removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make the 19 keys reached by the routine bare core-tier run through restored behavioral tests that drive the `aw agy` CLI leaves, render Term components and result types, run the SIGINT handler and validate comms envelopes and acks, asserting on exit codes, rendered text and returned verdicts. Done means an early-return mutation of any of the 19 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

RESTORE RULE for E-01..E-04: create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent; add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w`, revision `19313eed^` and what was deliberately not restored; keep every other test body unchanged. If a kept test fails at execution HEAD, STOP on it: record it in Findings and either update only that expectation for an intended change (cite the commit `git log -S` finds) or file a `bug` backlog item with `--blocks-release next` for a regression.

### Task group 1: restore the modules

- [ ] E-01 Restore `tests/test_agy_tools_graduation.py`, deleting the six tests that pin file contents or re-export identity rather than behavior (F-02): `CompatShimForwardingTests.test_agy_sessions_shim_reexports_and_delegates`, `test_agy_view_shim_reexports_and_delegates`, `test_pwatch_shim_reexports_and_delegates` (each `assertIs` on module attributes), and `AgyRunGraduatedTests.test_agy_run_tool_reduced_to_shim`, `test_packaged_agy_run_core_exists`, `test_agy_run_shim_reexports_and_delegates` (substring checks on `tools/agy_run.py` and `agent_workflows/agy_run.py` source, plus `assertIs`); remove the then-unused `_load_shim` helper if no kept test calls it. Add `@pytest.mark.core` to exactly `AgySessionsSurfaceTests.test_help_forwards_to_core`, `AgyViewSurfaceTests.test_help_forwards_to_core` and `NoAgyRunCollisionTests.test_agy_exec_surface_exists` (these drive `aw agy sessions|view|exec --help` and reach the four agy keys; the file's other subprocess tests stay out of the core tier).
  - Depends on: none
  - Expected outcome: 14 tests pass; 3 selected by `-m core`; `rg -n "read_text|assertIs\(shim" tests/test_agy_tools_graduation.py` returns nothing.
  - Execution state: pending

- [ ] E-02 Restore `tests/test_output_contract.py`, deleting `OutputContractDocTests.test_output_contract_doc_exists_and_contains_required_sections` (it asserts substrings of `docs/cli-output-contract.md`, prose not behavior); add a module-level `pytestmark = pytest.mark.core`.
  - Depends on: none
  - Expected outcome: 4 tests pass, all core-selected; `rg -n "read_text|cli-output-contract" tests/test_output_contract.py` returns nothing.
  - Execution state: pending

- [ ] E-03 Restore `tests/test_term_components.py`, `tests/test_attention_stem.py`, `tests/test_renderer_boundary.py` and `tests/test_interrupt_tty_wedge.py` unchanged except a module-level `pytestmark = pytest.mark.core` in each (16, 4, 4 and 14 tests; 0.03, 0.03, 0.6 to 0.9 and 0.05s summed CPU).
  - Depends on: none
  - Expected outcome: 38 tests pass, all core-selected.
  - Execution state: pending

- [ ] E-04 Restore `tests/test_comms.py` unchanged except a module-level `pytestmark = pytest.mark.core` (18 tests, 0.03s).
  - Depends on: none
  - Expected outcome: 18 tests pass, all core-selected.
  - Execution state: pending

### Task group 2: residual assertions

- [ ] E-05 Add residual tests asserting values measured at authoring (F-04), each re-measured at execution HEAD first: in `tests/test_comms.py`, a test asserting `comms.is_ack_valid({"re": "m", "state": "please do this thing", "by": "x.y", "at": "2026-07-15T10:00:00Z"})` is False and `comms.is_envelope_header_valid({})` is False (the latter's `validate_envelope_header({})` lists `missing required header: From`, `To`, `Kind`, `Status`); in `tests/test_output_contract.py`, a test asserting `CommandResult(command="c").has_findings` is False, `CommandResult(command="c", exit_code=1).has_findings` is True, `CommandResult(command="c", exit_code=2).has_findings` is False, and `CommandResult(command="c", diagnostics=[Diagnostic(location="a", rule="r", detail="d")]).has_findings` is True (`has_findings` is a property); in `tests/test_interrupt_tty_wedge.py`, a test that sets `runner_stop._SIGINT_PRESSES = 3` and `runner_stop._HANDLER_RUN_DIR = Path("x")`, calls `runner_stop.reset_signal_ladder()`, and asserts `runner_stop.signal_presses() == 0` and `runner_stop._HANDLER_RUN_DIR is None`, restoring both globals in `finally`.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the new tests pass and kill the scratch mutations named in V-05.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md`; `GUIDING_PRINCIPLES` P16): shim re-export identity, source substrings and doc prose assertions are dropped (E-01, E-02). The residual `runner_stop` test touches two module globals, which is state the function exists to reset; it asserts the observable reset rather than the code shape.
- THE ROUTINE GATE IS THE CORE TIER (`conftest.pytest_collection_modifyitems`, IPD `hguae9`, 30s budget): `tests/test_agy_tools_graduation.py` runs subprocess CLIs (1.0 to 1.6s summed), so only three of its tests join the core tier.
- Cite code by SYMBOL with a line number only appended, never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `hpjj44` `## Derived properties` | Reaching files: agy keys -> `tests/test_agy_tools_graduation.py`; Term -> `tests/test_term_components.py`; `_colorize_tree_segment` -> `tests/test_attention_priority_blocker.py`, `tests/test_attention_stem.py`; result types -> `tests/test_renderer_boundary.py`, `tests/test_output_contract.py`; `reset_signal_ladder` -> `tests/test_interrupt_tty_wedge.py`; comms -> `tests/test_comms.py`. |
| F-02 | `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`; reading the files | All seven `pass` (20, 16, 4, 4, 5, 14, 18). `test_agy_tools_graduation.py` holds six shim/source pinning tests; `test_output_contract.py` holds one doc-prose test. |
| F-03 | Scratch restore with E-01..E-04, coverage contexts | All 19 keys execute; summed core CPU for this child about 0.65 to 0.96s (63 tests). |
| F-04 | Early-return mutation sweep, bool keys both polarities, each reverted | 15 keys killed in both polarities. SURVIVED: `is_ack_valid` -> True, `is_envelope_header_valid` -> True, `CommandResult.has_findings` -> True (only the True direction is asserted), and `reset_signal_ladder` -> early `None` (each restored caller sets a fresh handler, so a no-op reset is invisible). Direct calls at HEAD produced the E-05 values. |
| F-05 | Replay of `tests/test_attention_priority_blocker.py` | 25 passed, 1 failed (`AssertionError: 5 != 4` on `attention.SCHEMA_VERSION`, bumped by `36e999b37`); `_colorize_tree_segment` is reached by `tests/test_attention_stem.py` alone, so the larger file is not needed for this item. |

## Proposed changes (ordered, validatable)

1. E-01..E-04 restore seven modules with the listed edits and markers.
2. E-05 adds residual assertions for the four surviving keys.

## Deferred / out of scope (with reason)

- `tests/test_attention_priority_blocker.py` is not restored.
  - Carrier-Declined: no work is owed for this item; F-05 shows its one `q86fxm` key is reached by `tests/test_attention_stem.py`.

## Scope check

- Over-scope: none. Seven test files; no production code.
- Under-scope: none for the 19 keys (F-03, F-04, E-05).

## Required tests / validation

- `python3 -m pytest <the seven files> -o addopts="" -v` passes, per-test list pasted.
- Reach: `-m core --cov=agent_workflows.agy_sessions --cov=agent_workflows.term --cov=agent_workflows.attention --cov=agent_workflows.agy_view --cov=agent_workflows.result_types --cov=agent_workflows.agy_run --cov=agent_workflows.runner_stop --cov=agent_workflows.comms --cov-report=term-missing`, each of the 19 keys executing.
- Mutation spot-checks (scratch, reverted): `agy_view.main` return 0, `Term.format_diagnostic` return `""`, `_colorize_tree_segment` return `""`, `CommandResult.is_error` return False, plus the four in V-05.
- Bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`.

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Keep the shim-forwarding tests as the only check that `tools/*.py` shims still work?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. They assert object identity and source substrings, which `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" forbids; the kept `*SurfaceTests` drive the real CLI leaves and assert on exit codes and output, which is the behavior those shims exist to preserve.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste a diff against `19313eed^` showing only the six removed tests (and helper), the markers and docstring; paste the `-v` run listing 14 PASSED, `-m core --collect-only -q` listing the 3 marked tests, the empty `rg` output, and the failure of the core-marked tests under a scratch `agy_view.main` return-0 mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff against `19313eed^`, the `-v` run listing 4 restored tests PASSED, the empty `rg` output, and the failure from a scratch `CommandResult.is_error` return-False mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` runs of the four files (38 PASSED) and the failures from scratch `Term.format_diagnostic` return-`""` and `_colorize_tree_segment` return-`""` mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` run listing 18 restored tests PASSED and the failure from a scratch `is_ack_valid` return-False mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` lines for the new residual tests PASSED; paste the failures from scratch `is_ack_valid` return-True, `is_envelope_header_valid` return-True, `has_findings` return-True and `reset_signal_ladder` early-`return None` mutations (reverted); paste the reach output from Required tests, the bare `python3 -m pytest` summary line, and a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the seven Scope-Paths files through `aw commit y4bt1c -- <paths>`; never push. Mutation spot-checks are scratch production edits that must be reverted and absent from the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
