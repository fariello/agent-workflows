# IPD: Restore behavioral test coverage for agy CLI surfaces, Term components, result types and comms validators

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the output-surface slice: groups 30 (`agy_sessions.py`, 2 keys), 32 (`term.py`, 8), 36 (`attention.py`, 1), 38 (`agy_view.py`, 1), 42 (`result_types.py`, 3), 48 (`agy_run.py`, 1), 54 (`runner_stop.py`, 1) and 56 (`comms.py`, 2), 19 keys in all.
- Scope: Restore seven deleted test modules from `19313eed^` at their original paths, minus code-pinning tests, with `core` markers, plus residual tests for four keys whose wrong value the restored files do not detect reliably (F-04 as corrected by F-06). The 19 keys: `agy_sessions.parse_args`, `agy_sessions.main`; `term.Term.format_diagnostic`, `Term.diagnostic`, `Term.title`, `Term.evidence`, `Term.fix`, `Term.outcome`, `Term.preview`, `Term.section`; `attention._colorize_tree_segment`; `agy_view.main`; `result_types.Diagnostic.from_drift`, `CommandResult.has_findings`, `CommandResult.is_error`; `agy_run.main`; `runner_stop.reset_signal_ladder`; `comms.is_ack_valid`, `comms.is_envelope_header_valid`. EXCLUDES any production change; EXCLUDES `tests/test_attention_priority_blocker.py` (F-05).
- Scope-Paths: tests/test_agy_tools_graduation.py, tests/test_term_components.py, tests/test_attention_stem.py, tests/test_renderer_boundary.py, tests/test_output_contract.py, tests/test_interrupt_tty_wedge.py, tests/test_comms.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 21
- Highest E allocated: 05
- Author: opencode
- Id: y4bt1c
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved

- 2026-10-17 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`, measured per-key reach via coverage contexts, durations, and an early-return mutation sweep over the 19 keys (both polarities for boolean keys); scratch edits reverted, `.coverage` removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make the 19 keys reached by the routine bare core-tier run through restored behavioral tests that drive the `aw agy` CLI leaves, render Term components and result types, run the SIGINT handler and validate comms envelopes and acks, asserting on exit codes, rendered text and returned verdicts. Done means an early-return mutation of any of the 19 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

RESTORE RULE for E-01..E-04: create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent; add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w`, revision `19313eed^` and what was deliberately not restored; keep every other test body unchanged. Remove any import, helper or test class that a deletion leaves unused or empty (the `ruff` pre-commit hook rejects unused imports). Disposition rule if a kept test (or an E-05 measured value) fails at execution HEAD (none did at authoring, F-02, nor at review, F-06): do not mark the owning item performed until it is dispositioned. Record it in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.

### Task group 1: restore the modules

- [ ] E-01 Restore `tests/test_agy_tools_graduation.py`, deleting the six tests that pin file contents or re-export identity rather than behavior (F-02): `CompatShimForwardingTests.test_agy_sessions_shim_reexports_and_delegates`, `test_agy_view_shim_reexports_and_delegates`, `test_pwatch_shim_reexports_and_delegates` (each `assertIs` on module attributes), and `AgyRunGraduatedTests.test_agy_run_tool_reduced_to_shim`, `test_packaged_agy_run_core_exists`, `test_agy_run_shim_reexports_and_delegates` (substring checks on `tools/agy_run.py` and `agent_workflows/agy_run.py` source, plus `assertIs`); remove the then-unused `_load_shim` helper, the two then-empty classes `CompatShimForwardingTests` and `AgyRunGraduatedTests`, and the then-unused imports `importlib.util`, `Path` and `REPO_ROOT` (PR-002; confirm each is unused before removing it). Add `@pytest.mark.core` to exactly `AgySessionsSurfaceTests.test_help_forwards_to_core`, `AgyViewSurfaceTests.test_help_forwards_to_core` and `NoAgyRunCollisionTests.test_agy_exec_surface_exists` (these drive `aw agy sessions|view|exec --help` and reach the four agy keys; the file's other subprocess tests stay out of the core tier).
  - Depends on: none
  - Expected outcome: every remaining test passes (14 at authoring and review; context, not the bar); exactly the three named tests are selected by `-m core`; `rg -n "read_text|assertIs\(shim|_load_shim|class CompatShimForwardingTests|class AgyRunGraduatedTests" tests/test_agy_tools_graduation.py` returns nothing; `ruff check` on the file is clean.
  - Execution state: pending

- [ ] E-02 Restore `tests/test_output_contract.py`, deleting `OutputContractDocTests.test_output_contract_doc_exists_and_contains_required_sections` (it asserts substrings of `docs/cli-output-contract.md`, prose not behavior) together with its then-empty class `OutputContractDocTests`, the then-unused `REPO_ROOT` constant and the `Path` import (PR-002); add a module-level `pytestmark = pytest.mark.core`.
  - Depends on: none
  - Expected outcome: every remaining test passes (4 at authoring and review; context, not the bar), all core-selected; `rg -n "read_text|cli-output-contract|OutputContractDocTests" tests/test_output_contract.py` returns nothing; `ruff check` on the file is clean.
  - Execution state: pending

- [ ] E-03 Restore `tests/test_term_components.py`, `tests/test_attention_stem.py`, `tests/test_renderer_boundary.py` and `tests/test_interrupt_tty_wedge.py` unchanged except a module-level `pytestmark = pytest.mark.core` in each, and except deleting `PaletteSingleSourceTests.test_no_parallel_palette_defined` from `tests/test_term_components.py`: it lists the `COLOR` dict names in `term.__dict__` and asserts `STATUS_COLOR_256` is absent, a symbol census `AGENTS.md` forbids, and it calls no Term method, so no key loses reach (PR-003). Counts at authoring: 16 (15 after the deletion), 4, 4 and 14 tests; 0.03, 0.03, 0.6 to 0.9 and 0.05s summed CPU.
  - Depends on: none
  - Expected outcome: every restored test passes (37 after the deletion; context, not the bar), all core-selected; `rg -n "test_no_parallel_palette_defined|T\.__dict__" tests/test_term_components.py` returns nothing.
  - Execution state: pending

- [ ] E-04 Restore `tests/test_comms.py` unchanged except a module-level `pytestmark = pytest.mark.core` (18 tests, 0.03s).
  - Depends on: none
  - Expected outcome: every restored test passes (18 at authoring and review; context, not the bar), all core-selected.
  - Execution state: pending

### Task group 2: residual assertions

- [ ] E-05 Add residual tests asserting values measured at authoring (F-04), each re-measured at execution HEAD first: in `tests/test_comms.py`, a test asserting `comms.is_ack_valid({"re": "m", "state": "please do this thing", "by": "x.y", "at": "2026-07-15T10:00:00Z"})` is False and `comms.is_envelope_header_valid({})` is False (the latter's `validate_envelope_header({})` lists `missing required header: From`, `To`, `Kind`, `Status`); in `tests/test_output_contract.py`, a test asserting `CommandResult(command="c").has_findings` is False, `CommandResult(command="c", exit_code=1).has_findings` is True, `CommandResult(command="c", exit_code=2).has_findings` is False, and `CommandResult(command="c", diagnostics=[Diagnostic(location="a", rule="r", detail="d")]).has_findings` is True (`has_findings` is a property); in `tests/test_interrupt_tty_wedge.py`, a test that sets `runner_stop._SIGINT_PRESSES = 3` and `runner_stop._HANDLER_RUN_DIR = Path("x")`, calls `runner_stop.reset_signal_ladder()`, and asserts `runner_stop.signal_presses() == 0` and `runner_stop._HANDLER_RUN_DIR is None`, restoring both globals in `finally`. This test is what makes the `reset_signal_ladder` kill independent of test order (F-06); the `has_findings` test adds the `exit_code=2` and diagnostics-only cases no restored test pins.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the new tests pass and kill the scratch mutations named in V-05.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md`; `GUIDING_PRINCIPLES` P16): shim re-export identity, source substrings, doc prose assertions and the `term.__dict__` palette census are dropped (E-01, E-02, E-03). The residual `runner_stop` test touches two module globals, which is state the function exists to reset; it asserts the observable reset rather than the code shape.
- THE ROUTINE GATE IS THE CORE TIER (`conftest.pytest_collection_modifyitems`, IPD `hguae9`, 30s budget): `tests/test_agy_tools_graduation.py` runs subprocess CLIs (1.0 to 1.6s summed), so only three of its tests join the core tier.
- Cite code by SYMBOL with a line number only appended, never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `hpjj44` `## Derived properties` | Reaching files: agy keys -> `tests/test_agy_tools_graduation.py`; Term -> `tests/test_term_components.py`; `_colorize_tree_segment` -> `tests/test_attention_priority_blocker.py`, `tests/test_attention_stem.py`; result types -> `tests/test_renderer_boundary.py`, `tests/test_output_contract.py`; `reset_signal_ladder` -> `tests/test_interrupt_tty_wedge.py`; comms -> `tests/test_comms.py`. |
| F-02 | `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`; reading the files | All seven `pass` (20, 16, 4, 4, 5, 14, 18). `test_agy_tools_graduation.py` holds six shim/source pinning tests; `test_output_contract.py` holds one doc-prose test. |
| F-03 | Scratch restore with E-01..E-04, coverage contexts | All 19 keys execute; summed core CPU for this child about 0.65 to 0.96s (63 tests). |
| F-04 | Early-return mutation sweep, bool keys both polarities, each reverted | 15 keys killed in both polarities. SURVIVED: `is_ack_valid` -> True, `is_envelope_header_valid` -> True, `CommandResult.has_findings` -> True (only the True direction is asserted), and `reset_signal_ladder` -> early `None` (each restored caller sets a fresh handler, so a no-op reset is invisible). Direct calls at HEAD produced the E-05 values. |
| F-06 | Plan review at HEAD `5ee9ed96b`: scratch copies `tests/test_zzscr_*.py` from `19313eed^` with the E-01..E-05 edits and markers; an early-return sweep over all 19 keys (`None` for Term printers, which return None; `""` for string keys; `0`/`1` for `main`s; both polarities for booleans) without and then with E-05; coverage JSON mapped to each key's body lines; all scratch files and production edits removed (`git diff agent_workflows/` empty, `git status` clean) | Unedited replay `81 passed`; edited with E-05 `77 passed` (also with `-n 4`); `-m core` selects 66 in `1.69s`, and all 19 keys reach an executed body line. Sweep WITHOUT E-05: only `is_ack_valid -> True` and `is_envelope_header_valid -> True` survive. Correcting F-04: `has_findings -> True` is already killed by `test_clean_result_exit_code_0` (`assertFalse(res.has_findings)`), and `reset_signal_ladder -> None` is killed by `test_the_ladder_still_requests_a_stop_in_the_unsafe_case` only under some orders (killed in file order and at random seeds 1, 3 and 5; survives at seeds 2 and 4; passes when run alone). WITH E-05 every mutation is killed, and the residual reset test fails on its own and at seeds 2 and 4. E-05 values reproduced. After the deletions, `importlib`, `Path` and `REPO_ROOT` are unused in the agy file, and `Path` and `REPO_ROOT` in the output-contract file. |
| F-05 | Replay of `tests/test_attention_priority_blocker.py` | 25 passed, 1 failed (`AssertionError: 5 != 4` on `attention.SCHEMA_VERSION`, bumped by `36e999b37`); `_colorize_tree_segment` is reached by `tests/test_attention_stem.py` alone, so the larger file is not needed for this item. |

## Proposed changes (ordered, validatable)

1. E-01..E-04 restore seven modules with the listed edits and markers.
2. E-05 adds residual assertions for the four keys F-04 named; F-06 records that two of them are fully unguarded and two are only partly guarded.

## Deferred / out of scope (with reason)

- `tests/test_attention_priority_blocker.py` is not restored.
  - Carrier-Declined: no work is owed for this item; F-05 shows its one `q86fxm` key is reached by `tests/test_attention_stem.py`.

## Scope check

- Over-scope: none. Seven test files; no production code.
- Under-scope: none for the 19 keys (F-03, F-04, F-06, E-05); V-05 demands the full sweep the Goal promises.

## Required tests / validation

- `python3 -m pytest <the seven files> -o addopts="" -v` passes, per-test list pasted.
- Reach: `-m core --cov=agent_workflows.agy_sessions --cov=agent_workflows.term --cov=agent_workflows.attention --cov=agent_workflows.agy_view --cov=agent_workflows.result_types --cov=agent_workflows.agy_run --cov=agent_workflows.runner_stop --cov=agent_workflows.comms --cov-report=term-missing`, each of the 19 keys executing.
- Reach per key: run the reach command with `--cov-report=json:<tmp>/cov.json` and, for each of the 19 keys, report whether any line of its function body is in `executed_lines` (a scratch script locating each body by symbol; not committed). `term-missing` alone does not attribute lines to keys.
- Mutation spot-checks (scratch, reverted): `agy_view.main` return 0, `Term.format_diagnostic` return `""`, `_colorize_tree_segment` return `""`, `CommandResult.is_error` return False, plus the four in V-05; then the full 19-key early-return sweep against the seven files (`None` for the Term printers, `""` for string keys, `0` and `1` for each `main`, both polarities for booleans), which is the Goal's bar.
- Bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`; delete any `.coverage` file and scratch script afterwards.

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
  - Required evidence: paste a diff against `19313eed^` showing only the six removed tests, the helper, the two emptied classes, the three unused imports, the markers and docstring; paste the `-v` run showing every test PASSED and zero failed (the count is context, not the bar), `ruff check` clean, `-m core --collect-only -q` listing the 3 marked tests, the empty `rg` output, and the failure of the core-marked tests under a scratch `agy_view.main` return-0 mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff against `19313eed^` (only the removed test, its class, `REPO_ROOT`, the `Path` import, the marker and docstring), the `-v` run showing every test PASSED and zero failed, `ruff check` clean, the empty `rg` output, and the failure from a scratch `CommandResult.is_error` return-False mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of `tests/test_term_components.py` against `19313eed^` (only the census test, the marker and docstring), the `-v` runs of the four files showing every test PASSED and zero failed, the empty `rg` output, and the failures from scratch `Term.format_diagnostic` return-`""` and `_colorize_tree_segment` return-`""` mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` run showing every restored test PASSED, zero failed, and the failure from a scratch `is_ack_valid` return-False mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` lines for the new residual tests PASSED; paste the failures from scratch `is_ack_valid` return-True, `is_envelope_header_valid` return-True, `has_findings` return-True and `reset_signal_ladder` early-`return None` mutations (reverted), each naming a failing `ResidualKeyTests` test; for `reset_signal_ladder`, also paste the residual test failing when run ALONE (`<file>::ResidualKeyTests`), which proves the kill does not depend on order (F-06); paste the per-key reach listing showing all 19 keys REACHED, and the full 19-key sweep from Required tests showing every mutation KILLED; the bare `python3 -m pytest` summary line, and a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Execution contract:

- Open questions: OQ-01 is resolved; none block.
- Scope fence (a declaration, not a stop condition): the seven Scope-Paths test files are the only intended changes. Any other path you edit (for example a `bug` backlog item filed under the RESTORE RULE) must be justified at finalize with `--scope-reason`; a declared path left unmodified needs `--scope-ack`.
- Honesty rule: every V-item MUST paste the ACTUAL runner output; never claim a pass, a kill, or a reach you did not run and observe.
- Mutation spot-checks and the sweep are scratch production edits: revert each immediately, and confirm `git diff agent_workflows/` is empty before committing. Delete any `.coverage` file and scratch script.
- Commit: only the seven Scope-Paths files, through `aw commit y4bt1c -- <paths>`; run `git diff --cached --name-only` first and unstage anything not yours. Never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize y4bt1c` instead. Never hand-`git mv` the plan.
