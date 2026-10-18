# IPD: Restore behavioral test coverage for agy CLI surfaces, Term components, result types and comms validators

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the output-surface slice: groups 30 (`agy_sessions.py`, 2 keys), 32 (`term.py`, 8), 36 (`attention.py`, 1), 38 (`agy_view.py`, 1), 42 (`result_types.py`, 3), 48 (`agy_run.py`, 1), 54 (`runner_stop.py`, 1) and 56 (`comms.py`, 2), 19 keys in all.
- Scope: Restore seven deleted test modules from `19313eed^` at their original paths, minus code-pinning tests, with `core` markers, plus residual tests for four keys whose wrong value the restored files do not detect reliably (F-04 as corrected by F-06). The 19 keys: `agy_sessions.parse_args`, `agy_sessions.main`; `term.Term.format_diagnostic`, `Term.diagnostic`, `Term.title`, `Term.evidence`, `Term.fix`, `Term.outcome`, `Term.preview`, `Term.section`; `attention._colorize_tree_segment`; `agy_view.main`; `result_types.Diagnostic.from_drift`, `CommandResult.has_findings`, `CommandResult.is_error`; `agy_run.main`; `runner_stop.reset_signal_ladder`; `comms.is_ack_valid`, `comms.is_envelope_header_valid`. EXCLUDES any production change; EXCLUDES `tests/test_attention_priority_blocker.py` (F-05).
- Scope-Paths: tests/test_agy_tools_graduation.py, tests/test_term_components.py, tests/test_attention_stem.py, tests/test_renderer_boundary.py, tests/test_output_contract.py, tests/test_interrupt_tty_wedge.py, tests/test_comms.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 21
- Highest E allocated: 05
- Author: opencode
- Id: y4bt1c

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: y4bt1c verified (set trimgap, attempt 1).
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

- [x] E-01 Restore `tests/test_agy_tools_graduation.py`, deleting the six tests that pin file contents or re-export identity rather than behavior (F-02): `CompatShimForwardingTests.test_agy_sessions_shim_reexports_and_delegates`, `test_agy_view_shim_reexports_and_delegates`, `test_pwatch_shim_reexports_and_delegates` (each `assertIs` on module attributes), and `AgyRunGraduatedTests.test_agy_run_tool_reduced_to_shim`, `test_packaged_agy_run_core_exists`, `test_agy_run_shim_reexports_and_delegates` (substring checks on `tools/agy_run.py` and `agent_workflows/agy_run.py` source, plus `assertIs`); remove the then-unused `_load_shim` helper, the two then-empty classes `CompatShimForwardingTests` and `AgyRunGraduatedTests`, and the then-unused imports `importlib.util`, `Path` and `REPO_ROOT` (PR-002; confirm each is unused before removing it). Add `@pytest.mark.core` to exactly `AgySessionsSurfaceTests.test_help_forwards_to_core`, `AgyViewSurfaceTests.test_help_forwards_to_core` and `NoAgyRunCollisionTests.test_agy_exec_surface_exists` (these drive `aw agy sessions|view|exec --help` and reach the four agy keys; the file's other subprocess tests stay out of the core tier).
  - Depends on: none
  - Expected outcome: every remaining test passes (14 at authoring and review; context, not the bar); exactly the three named tests are selected by `-m core`; `rg -n "read_text|assertIs\(shim|_load_shim|class CompatShimForwardingTests|class AgyRunGraduatedTests" tests/test_agy_tools_graduation.py` returns nothing; `ruff check` on the file is clean.
  - Execution state: performed

- [x] E-02 Restore `tests/test_output_contract.py`, deleting `OutputContractDocTests.test_output_contract_doc_exists_and_contains_required_sections` (it asserts substrings of `docs/cli-output-contract.md`, prose not behavior) together with its then-empty class `OutputContractDocTests`, the then-unused `REPO_ROOT` constant and the `Path` import (PR-002); add a module-level `pytestmark = pytest.mark.core`.
  - Depends on: none
  - Expected outcome: every remaining test passes (4 at authoring and review; context, not the bar), all core-selected; `rg -n "read_text|cli-output-contract|OutputContractDocTests" tests/test_output_contract.py` returns nothing; `ruff check` on the file is clean.
  - Execution state: performed

- [x] E-03 Restore `tests/test_term_components.py`, `tests/test_attention_stem.py`, `tests/test_renderer_boundary.py` and `tests/test_interrupt_tty_wedge.py` unchanged except a module-level `pytestmark = pytest.mark.core` in each, and except deleting `PaletteSingleSourceTests.test_no_parallel_palette_defined` from `tests/test_term_components.py`: it lists the `COLOR` dict names in `term.__dict__` and asserts `STATUS_COLOR_256` is absent, a symbol census `AGENTS.md` forbids, and it calls no Term method, so no key loses reach (PR-003). Counts at authoring: 16 (15 after the deletion), 4, 4 and 14 tests; 0.03, 0.03, 0.6 to 0.9 and 0.05s summed CPU.
  - Depends on: none
  - Expected outcome: every restored test passes (37 after the deletion; context, not the bar), all core-selected; `rg -n "test_no_parallel_palette_defined|T\.__dict__" tests/test_term_components.py` returns nothing.
  - Execution state: performed

- [x] E-04 Restore `tests/test_comms.py` unchanged except a module-level `pytestmark = pytest.mark.core` (18 tests, 0.03s).
  - Depends on: none
  - Expected outcome: every restored test passes (18 at authoring and review; context, not the bar), all core-selected.
  - Execution state: performed

### Task group 2: residual assertions

- [x] E-05 Add residual tests asserting values measured at authoring (F-04), each re-measured at execution HEAD first: in `tests/test_comms.py`, a test asserting `comms.is_ack_valid({"re": "m", "state": "please do this thing", "by": "x.y", "at": "2026-07-15T10:00:00Z"})` is False and `comms.is_envelope_header_valid({})` is False (the latter's `validate_envelope_header({})` lists `missing required header: From`, `To`, `Kind`, `Status`); in `tests/test_output_contract.py`, a test asserting `CommandResult(command="c").has_findings` is False, `CommandResult(command="c", exit_code=1).has_findings` is True, `CommandResult(command="c", exit_code=2).has_findings` is False, and `CommandResult(command="c", diagnostics=[Diagnostic(location="a", rule="r", detail="d")]).has_findings` is True (`has_findings` is a property); in `tests/test_interrupt_tty_wedge.py`, a test that sets `runner_stop._SIGINT_PRESSES = 3` and `runner_stop._HANDLER_RUN_DIR = Path("x")`, calls `runner_stop.reset_signal_ladder()`, and asserts `runner_stop.signal_presses() == 0` and `runner_stop._HANDLER_RUN_DIR is None`, restoring both globals in `finally`. This test is what makes the `reset_signal_ladder` kill independent of test order (F-06); the `has_findings` test adds the `exit_code=2` and diagnostics-only cases no restored test pins.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the new tests pass and kill the scratch mutations named in V-05.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: paste a diff against `19313eed^` showing only the six removed tests, the helper, the two emptied classes, the three unused imports, the markers and docstring; paste the `-v` run showing every test PASSED and zero failed (the count is context, not the bar), `ruff check` clean, `-m core --collect-only -q` listing the 3 marked tests, the empty `rg` output, and the failure of the core-marked tests under a scratch `agy_view.main` return-0 mutation (reverted).
  - Observed evidence:
    1. Diff against `19313eed^`:
    ```diff
    $ git diff --no-index <(git show 19313eed^:tests/test_agy_tools_graduation.py) tests/test_agy_tools_graduation.py
    diff --git a/dev/fd/63 b/tests/test_agy_tools_graduation.py
    index 000000000..9e5b581ee 100644
    --- a/dev/fd/63
    +++ b/tests/test_agy_tools_graduation.py
    @@ -18,19 +18,23 @@ These tests assert:
     agy_run.py was dispositioned per OQ-02 as genuinely distinct from the multi-IPD queue
     driver, so it is graduated as `aw agy exec` (NOT `aw agy run`, which stays aliased to
     runipd), tools/agy_run.py is a compat shim, and agent_workflows/agy_run.py is the core.
    +
    +Restored under backlog q86fxm, findings b1mx2w, from revision 19313eed^.
    +Deliberately not restored: code-pinning tests CompatShimForwardingTests and
    +AgyRunGraduatedTests, which asserted source substrings and object identity
    +rather than observable behavior.
     """

     from __future__ import annotations

    -import importlib.util
     import io
     import unittest
    -from contextlib import redirect_stdout, redirect_stderr
    -from pathlib import Path
    +from contextlib import redirect_stderr, redirect_stdout
     from unittest import mock

    +import pytest
    +
     from agent_workflows import agy_run, agy_runipd, agy_sessions, agy_view, cli, pwatch
    -from tests.support import REPO_ROOT


     def _run_cli(argv):
    @@ -56,6 +60,7 @@ class AgySessionsSurfaceTests(unittest.TestCase):
                 cli.main(["antigravity", "sessions", "--all"])
             m.assert_called_once_with(["--all"])

    +    @pytest.mark.core
         def test_help_forwards_to_core(self):
             rc, out, err = _run_cli(["agy", "sessions", "--help"])
             combined = out + err
    @@ -75,6 +80,7 @@ class AgyViewSurfaceTests(unittest.TestCase):
                 cli.main(["agy", "view-antigravity-jsonl", "--match", "x"])
             m.assert_called_once_with(["--match", "x"])

    +    @pytest.mark.core
         def test_help_forwards_to_core(self):
             rc, out, err = _run_cli(["agy", "view", "--help"])
             combined = out + err
    @@ -110,6 +116,7 @@ class NoAgyRunCollisionTests(unittest.TestCase):
                 m_sess.assert_not_called()
                 m_view.assert_not_called()

    +    @pytest.mark.core
         def test_agy_exec_surface_exists(self):
             # puot79e04 graduated agy_run.py under the non-colliding `aw agy exec` surface;
             # its `--help` must now succeed and show the runner usage (NOT an invalid-choice error).
    @@ -149,66 +156,5 @@ class AgyExecSurfaceTests(unittest.TestCase):
             m_ipd.assert_not_called()


    -def _load_shim(path: Path, name: str):
    -    spec = importlib.util.spec_from_file_location(name, path)
    -    assert spec is not None and spec.loader is not None
    -    module = importlib.util.module_from_spec(spec)
    -    spec.loader.exec_module(module)
    -    return module
    -
    -
    -class CompatShimForwardingTests(unittest.TestCase):
    -    """Each tools/*.py shim forwards to its packaged core and re-exports its symbols."""
    -
    -    def test_agy_sessions_shim_reexports_and_delegates(self):
    -        shim = _load_shim(REPO_ROOT / "tools" / "agy_sessions.py", "shim_agy_sessions")
    -        self.assertIs(shim.agy_sessions, agy_sessions)
    -        self.assertIs(shim.get_sessions, agy_sessions.get_sessions)
    -        self.assertIs(shim.SessionInfo, agy_sessions.SessionInfo)
    -        self.assertIs(shim.main, agy_sessions.main)
    -
    -    def test_agy_view_shim_reexports_and_delegates(self):
    -        shim = _load_shim(
    -            REPO_ROOT / "tools" / "view-antigravity-jsonl.py", "shim_agy_view"
    -        )
    -        self.assertIs(shim.agy_view, agy_view)
    -        self.assertIs(shim.format_record, agy_view.format_record)
    -        self.assertIs(shim.main, agy_view.main)
    -
    -    def test_pwatch_shim_reexports_and_delegates(self):
    -        shim = _load_shim(REPO_ROOT / "tools" / "pwatch.py", "shim_pwatch")
    -        self.assertIs(shim.pwatch, pwatch)
    -        self.assertIs(shim.main, pwatch.main)
    -        self.assertIs(shim.build_parser, pwatch.build_parser)
    -
    -
    -class AgyRunGraduatedTests(unittest.TestCase):
    -    """puot79e04: agy_run.py is graduated - tool reduced to a shim, packaged core added."""
    -
    -    def test_agy_run_tool_reduced_to_shim(self):
    -        agy_run_path = REPO_ROOT / "tools" / "agy_run.py"
    -        self.assertTrue(agy_run_path.is_file())
    -        text = agy_run_path.read_text(encoding="utf-8")
    -        # The tool is now a thin compat shim: it re-exports the packaged core and holds no
    -        # tool logic (so the standalone parser `prog="agy_run.py"` no longer lives here).
    -        self.assertNotIn('prog="agy_run.py"', text)
    -        self.assertIn("from agent_workflows import agy_run", text)
    -
    -    def test_packaged_agy_run_core_exists(self):
    -        core = REPO_ROOT / "agent_workflows" / "agy_run.py"
    -        self.assertTrue(core.exists())
    -        # The parser (prog="agy_run.py") now lives in the packaged core.
    -        self.assertIn('prog="agy_run.py"', core.read_text(encoding="utf-8"))
    -
    -    def test_agy_run_shim_reexports_and_delegates(self):
    -        shim = _load_shim(REPO_ROOT / "tools" / "agy_run.py", "shim_agy_run")
    -        self.assertIs(shim.agy_run, agy_run)
    -        self.assertIs(shim.ScriptError, agy_run.ScriptError)
    -        self.assertIs(shim.AgyResult, agy_run.AgyResult)
    -        self.assertIs(shim.resolve_ipd, agy_run.resolve_ipd)
    -        self.assertIs(shim.run_agy, agy_run.run_agy)
    -        self.assertIs(shim.main, agy_run.main)
    -
    -
     if __name__ == "__main__":
         unittest.main()
    ```
    2. `-v` test run:
    ```
    $ python3 -m pytest tests/test_agy_tools_graduation.py -o addopts="" -v
    collecting ... collected 14 items

    tests/test_agy_tools_graduation.py::NoAgyRunCollisionTests::test_agy_run_still_routes_to_runipd PASSED [  7%]
    tests/test_agy_tools_graduation.py::NoAgyRunCollisionTests::test_agy_exec_surface_exists PASSED [ 14%]
    tests/test_agy_tools_graduation.py::AgyViewSurfaceTests::test_help_forwards_to_core PASSED [ 21%]
    tests/test_agy_tools_graduation.py::AgyViewSurfaceTests::test_legacy_name_alias_delegates PASSED [ 28%]
    tests/test_agy_tools_graduation.py::AgyViewSurfaceTests::test_forwarding_delegates_to_packaged_core PASSED [ 35%]
    tests/test_agy_tools_graduation.py::AgyExecSurfaceTests::test_forwarding_delegates_to_packaged_core PASSED [ 42%]
    tests/test_agy_tools_graduation.py::AgyExecSurfaceTests::test_antigravity_alias_delegates_identically PASSED [ 50%]
    tests/test_agy_tools_graduation.py::AgyExecSurfaceTests::test_exec_does_not_route_to_runipd PASSED [ 57%]
    tests/test_agy_tools_graduation.py::AgyExecSurfaceTests::test_help_forwards_to_core PASSED [ 64%]
    tests/test_agy_tools_graduation.py::PwatchSurfaceTests::test_help_forwards_to_core PASSED [ 71%]
    tests/test_agy_tools_graduation.py::PwatchSurfaceTests::test_forwarding_delegates_to_packaged_core PASSED [ 78%]
    tests/test_agy_tools_graduation.py::AgySessionsSurfaceTests::test_help_forwards_to_core PASSED [ 85%]
    tests/test_agy_tools_graduation.py::AgySessionsSurfaceTests::test_antigravity_alias_delegates_identically PASSED [ 92%]
    tests/test_agy_tools_graduation.py::AgySessionsSurfaceTests::test_forwarding_delegates_to_packaged_core PASSED [100%]
    ============================== 14 passed in 1.36s ==============================
    ```
    3. `ruff check --select F` and pre-commit hook:
    ```
    $ ruff check --select F tests/test_agy_tools_graduation.py
    All checks passed!
    $ pre-commit run ruff --files tests/test_agy_tools_graduation.py
    ruff.....................................................................Passed
    ```
    4. `-m core --collect-only -q`:
    ```
    $ python3 -m pytest tests/test_agy_tools_graduation.py -m core --collect-only -q
    tests/test_agy_tools_graduation.py: 3
    ```
    Listing the 3 marked tests:
    - `AgyViewSurfaceTests::test_help_forwards_to_core`
    - `NoAgyRunCollisionTests::test_agy_exec_surface_exists`
    - `AgySessionsSurfaceTests::test_help_forwards_to_core`
    5. Forbidden pattern scan:
    ```
    $ rg -n "read_text|assertIs\(shim|_load_shim|class CompatShimForwardingTests|class AgyRunGraduatedTests" tests/test_agy_tools_graduation.py
    (empty, exit code 1)
    ```
    6. Scratch `agy_view.main` return 0 mutation (reverted):
    ```
    FAILED tests/test_agy_tools_graduation.py::AgyViewSurfaceTests::test_help_forwards_to_core
    AssertionError: 'agy view' not found in ''
    ================== 1 failed, 2 passed, 11 deselected in 0.56s ==================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff against `19313eed^` (only the removed test, its class, `REPO_ROOT`, the `Path` import, the marker and docstring), the `-v` run showing every test PASSED and zero failed, `ruff check` clean, the empty `rg` output, and the failure from a scratch `CommandResult.is_error` return-False mutation (reverted).
  - Observed evidence:
    1. Diff against `19313eed^` (before E-05 residual class):
    ```diff
    $ git diff --no-index <(git show 19313eed^:tests/test_output_contract.py) tests/test_output_contract.py
    diff --git a/dev/fd/63 b/tests/test_output_contract.py
    index 000000000..98051d979 100644
    --- a/dev/fd/63
    +++ b/tests/test_output_contract.py
    @@ -13,75 +13,25 @@ Asserts:
     3. Exactly one machine-readable output convention:
        - Agent output conforms to `aw.agent/v1` JSONL schema
        - No conflicting legacy TSV wire form on migrated handlers
    -4. Contract documentation completeness (verifying sections exist in docs/cli-output-contract.md).
    +
    +Restored under backlog q86fxm, findings b1mx2w, from revision 19313eed^.
    +Deliberately not restored: code-pinning doc-prose test asserting contract documentation text.
     """

     from __future__ import annotations

     import json
     import unittest
    -from pathlib import Path

    +import pytest
    +
    +from agent_workflows.renderers import AgentRenderer
     from agent_workflows.result_types import (
         CommandResult,
         Diagnostic,
     )
    -from agent_workflows.renderers import AgentRenderer

    -REPO_ROOT = Path(__file__).resolve().parent.parent
    -
    -
    -class OutputContractDocTests(unittest.TestCase):
    -    """Verify the presence and completeness of docs/cli-output-contract.md (V-03)."""
    -
    -    def test_output_contract_doc_exists_and_contains_required_sections(self):
    -        doc_path = REPO_ROOT / "docs" / "cli-output-contract.md"
    -        self.assertTrue(doc_path.is_file(), f"Missing {doc_path}")
    -        text = doc_path.read_text(encoding="utf-8")
    -
    -        # Required contract sections (E-03 / V-03):
    -        # 1. Mode Precedence
    -        self.assertIn("Audience Modes and Precedence", text)
    -        self.assertIn("explicit", text.lower())
    -        # 2. Standard Result Types
    -        self.assertIn("Standard Result Types and Renderer Boundary", text)
    -        self.assertIn("CommandResult", text)
    -        # 3. Exit Code Semantics (0, 1, 2)
    -        self.assertIn("Exit Code Semantics", text)
    -        self.assertIn("0", text)
    -        self.assertIn("1", text)
    -        self.assertIn("2", text)
    -        # 4. Stream Separation & Broken Pipes
    -        self.assertIn("Stream Separation and Broken-Pipe Policy", text)
    -        self.assertIn("stdout", text)
    -        self.assertIn("stderr", text)
    -        # 5. Schema Versioning
    -        self.assertIn("Schema Versioning", text)
    -        self.assertIn("aw.agent/v1", text)
    -        # 6. Non-TTY Migration Policy, now RETRACTED.
    -        #
    -        # DELIBERATELY CHANGED by ttyflags `yaxr4i` E-05, and the reason matters more than the new
    -        # string. This assertion used to require the literal heading
    -        # "Automatic Non-TTY Migration Policy (Hard Cutover)", i.e. it pinned the PRESENCE of a
    -        # policy stating that non-TTY stdout adopts `aw.agent/v1` JSONL. That policy WAS NEVER
    -        # IMPLEMENTED (`select_output` has never consulted `stdout.isatty()` for mode selection),
    -        # so the test was holding a false promise in place.
    -        #
    -        # The maintainer resolved OQ-01 by RETRACTING the policy rather than implementing it. So
    -        # this now asserts the RETRACTION IS EXPLICIT and not a silent deletion: a reader must be
    -        # able to tell the policy was reversed on purpose, or the next author re-proposes it as an
    -        # unimplemented contract defect. The section, the word RETRACTED, and the statement of what
    -        # is true instead are all required.
    -        self.assertIn("Automatic Non-TTY Migration Policy", text)
    -        self.assertIn("RETRACTED", text)
    -        self.assertNotIn("(Hard Cutover)", text)
    -        self.assertIn("--agent", text)
    -        # 6a. The color precedence table and the two-axis --tty constraint (E-03 / E-06).
    -        self.assertIn("flag beats env beats detection", text)
    -        self.assertIn("--color", text)
    -        # 7. Relationship to Legacy Drift Convention
    -        self.assertIn("Relationship to Legacy `Drift` Convention", text)
    -        self.assertIn("SUBSUMES and REPLACES", text)
    +pytestmark = pytest.mark.core


     class ExitCodeAndStreamSemanticsTests(unittest.TestCase):
    @@ -131,7 +81,7 @@ class ExitCodeAndStreamSemanticsTests(unittest.TestCase):
             self.assertEqual(record["exit"], 1)
             self.assertEqual(len(record["diagnostics"]), 1)
             # No ANSI codes present
    -        self.assertNotIn("utput)
    +        self.assertNotIn("\x1b[", output)


     if __name__ == "__main__":
    ```
    2. `-v` test run:
    ```
    $ python3 -m pytest tests/test_output_contract.py -o addopts="" -v
    collecting ... collected 4 items

    tests/test_output_contract.py::ExitCodeAndStreamSemanticsTests::test_agent_renderer_emits_single_machine_convention PASSED [ 25%]
    tests/test_output_contract.py::ExitCodeAndStreamSemanticsTests::test_clean_result_exit_code_0 PASSED [ 50%]
    tests/test_output_contract.py::ExitCodeAndStreamSemanticsTests::test_findings_result_exit_code_1 PASSED [ 75%]
    tests/test_output_contract.py::ExitCodeAndStreamSemanticsTests::test_cannot_run_error_exit_code_2 PASSED [100%]
    ============================== 4 passed in 0.22s ===============================
    ```
    3. `ruff check` clean:
    ```
    $ ruff check tests/test_output_contract.py
    All checks passed!
    ```
    4. Forbidden pattern scan:
    ```
    $ rg -n "read_text|cli-output-contract|OutputContractDocTests" tests/test_output_contract.py
    (empty, exit code 1)
    ```
    5. Scratch `CommandResult.is_error` return-False mutation (reverted):
    ```
    FAILED tests/test_output_contract.py::ExitCodeAndStreamSemanticsTests::test_cannot_run_error_exit_code_2
    AssertionError: False is not true
    ========================= 1 failed, 3 passed in 0.26s ==========================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the diff of `tests/test_term_components.py` against `19313eed^` (only the census test, the marker and docstring), the `-v` runs of the four files showing every test PASSED and zero failed, the empty `rg` output, and the failures from scratch `Term.format_diagnostic` return-`""` and `_colorize_tree_segment` return-`""` mutations (reverted).
  - Observed evidence:
    1. Diff of `tests/test_term_components.py` against `19313eed^`:
    ```diff
    $ git diff --no-index <(git show 19313eed^:tests/test_term_components.py) tests/test_term_components.py
    diff --git a/dev/fd/63 b/tests/test_term_components.py
    index 000000000..0c4f3ff4f 100644
    --- a/dev/fd/63
    +++ b/tests/test_term_components.py
    @@ -1,6 +1,9 @@
     """Tests for Term components, 256-color palette extension, ASCII fallback, and single-palette invariant.

     awcliux Order 02 (`czw99i`) E-01 / V-01.
    +
    +Restored under backlog q86fxm, findings b1mx2w, from revision 19313eed^.
    +Deliberately not restored: symbol census test asserting dict names in term module namespace.
     """

     from __future__ import annotations
    @@ -8,11 +11,15 @@ from __future__ import annotations
     import io
     import re
     import unittest
    +
    +import pytest
     from agent_workflows import lifecycle_style as LS
     from agent_workflows import term as T

     _ANSI = re.compile(r"\033\[[0-9;]*m")

    +pytestmark = pytest.mark.core
    +

     class PaletteSingleSourceTests(unittest.TestCase):
         """ONE LIFECYCLE SOURCE plus ONE generic role table, each serving a different vocabulary.
    @@ -94,51 +101,6 @@ class PaletteSingleSourceTests(unittest.TestCase):
                 "a key here is a second lifecycle table by another name.",
             )

    -    def test_no_parallel_palette_defined(self):
    -        """Assert no secondary or parallel palette dict exists in term module.
    -
    -        WHAT "PARALLEL" MEANS HERE, stated because the list grew legitimately (2026-09-20, plan
    -        `pow5sj`, spec `uonrjg` R9.3a.3). The defect this guard exists to catch is a RIVAL table for
    -        the SAME decision: two maps that both answer "what color is this status at this depth",
    -        which is how four disagreeing lifecycle palettes shipped before spec `uonrjg`.
    -        `STAGE_COLOR_16` is NOT that. It is a different RUNG of the one 256/16/none ladder, it is
    -        keyed by SEMANTIC STAGE rather than by status word, and R9.3a.3 REQUIRES it to be an authored
    -        table precisely because deriving it from `STATUS_COLOR_256` would merge stages that must stay
    -        distinguishable.
    -        SO THE GUARD IS AN ALLOWLIST RATHER THAN A COUNT: a NEW palette still fails and must justify
    -        itself here, which keeps the protection, while the two tiers the spec mandates are named with
    -        the role each one serves.
    -
    -        THE ALLOWLIST CHANGED ONCE MORE (plan `qdd5jq` E-04): `STATUS_COLOR_256` became
    -        `ROLE_COLOR_256` when its 32 LIFECYCLE keys left for `lifecycle_style` and its 24 GENERIC
    -        command-outcome and formatting roles stayed. That is a RENAME PLUS A NARROWING of one table,
    -        not a new rival, and the narrowing is what criterion A17 asked for. Both surviving entries are
    -        now non-lifecycle by construction: one is the generic role palette, the other is the 16-color
    -        tier keyed by SEMANTIC STAGE.
    -        """
    -        term_dicts = sorted(
    -            k
    -            for k, v in T.__dict__.items()
    -            if isinstance(v, dict) and "COLOR" in k.upper()
    -        )
    -        self.assertEqual(
    -            term_dicts,
    -            ["ROLE_COLOR_256", "STAGE_COLOR_16"],
    -            "a palette dict appeared in `term` that is neither the generic 256 role palette nor the "
    -            "authored 16-color stage tier. If it is a new RUNG of the documented ladder, add it "
    -            "here with its role; if it answers the same question as an existing table, it is the "
    -            "parallel palette this guard exists to refuse.",
    -        )
    -        # AND THE RETIRED NAME MUST NOT COME BACK, because re-adding `STATUS_COLOR_256` is the one
    -        # edit that would silently restore the mixed lifecycle/generic table this Set dismantled.
    -        self.assertFalse(
    -            hasattr(T, "STATUS_COLOR_256"),
    -            "`term.STATUS_COLOR_256` is back. It mixed 32 lifecycle statuses with 24 generic roles, "
    -            "which is the second lifecycle table spec `uonrjg` criterion A17 forbids; lifecycle "
    -            "color belongs to `lifecycle_style` and the generic roles to `ROLE_COLOR_256`.",
    -        )
    -
    -
     class TermComponentsTests(unittest.TestCase):
         """V-01: 11 shared Term components format correctly in color, monochrome, Unicode, and ASCII fallback."""
     ```
    2. `-v` runs of the four files showing all 37 tests PASSED:
    - `tests/test_term_components.py` (15 passed in 0.29s):
    ```
    tests/test_term_components.py::TermComponentsTests::test_preview_component PASSED [  6%]
    tests/test_term_components.py::TermComponentsTests::test_badge_component PASSED [ 13%]
    tests/test_term_components.py::TermComponentsTests::test_path_component PASSED [ 20%]
    tests/test_term_components.py::TermComponentsTests::test_fix_component PASSED [ 26%]
    tests/test_term_components.py::TermComponentsTests::test_outcome_component PASSED [ 33%]
    tests/test_term_components.py::TermComponentsTests::test_evidence_and_grid_component PASSED [ 40%]
    tests/test_term_components.py::TermComponentsTests::test_next_action_component PASSED [ 46%]
    tests/test_term_components.py::TermComponentsTests::test_stream_print_methods PASSED [ 53%]
    tests/test_term_components.py::TermComponentsTests::test_table_component PASSED [ 60%]
    tests/test_term_components.py::TermComponentsTests::test_title_component PASSED [ 66%]
    tests/test_term_components.py::TermComponentsTests::test_section_component PASSED [ 73%]
    tests/test_term_components.py::TermComponentsTests::test_diagnostic_component PASSED [ 80%]
    tests/test_term_components.py::PaletteSingleSourceTests::test_role_palette_contains_the_generic_roles_and_no_lifecycle_status PASSED [ 86%]
    tests/test_term_components.py::AsciiFallbackDegradationTests::test_all_components_pure_ascii_when_unicode_disabled PASSED [ 93%]
    tests/test_term_components.py::AsciiFallbackDegradationTests::test_ansi_scan_proves_zero_escapes_when_color_disabled PASSED [100%]
    ============================== 15 passed in 0.29s ==============================
    ```
    - `tests/test_attention_stem.py` (4 passed in 0.28s):
    ```
    tests/test_attention_stem.py::AttentionStemTests::test_plain_board_unchanged PASSED [ 25%]
    tests/test_attention_stem.py::AttentionStemTests::test_identity_stem_grammar_and_fallback PASSED [ 50%]
    tests/test_attention_stem.py::AttentionStemTests::test_default_board_shows_stem_not_directory PASSED [ 75%]
    tests/test_attention_stem.py::AttentionStemTests::test_long_shows_full_path PASSED [100%]
    ============================== 4 passed in 0.28s ===============================
    ```
    - `tests/test_renderer_boundary.py` (4 passed in 1.08s):
    ```
    tests/test_renderer_boundary.py::ResultTypesUnitTests::test_diagnostic_roundtrip_with_drift PASSED [ 25%]
    tests/test_renderer_boundary.py::ResultTypesUnitTests::test_command_result_agent_record_format PASSED [ 50%]
    tests/test_renderer_boundary.py::DoctorRendererBoundaryTests::test_doctor_both_renderers_clean_state_fact_parity PASSED [ 75%]
    tests/test_renderer_boundary.py::DoctorRendererBoundaryTests::test_doctor_both_renderers_findings_state_fact_parity PASSED [100%]
    ============================== 4 passed in 1.08s ===============================
    ```
    - `tests/test_interrupt_tty_wedge.py` (14 passed before residual, 15 passed with residual):
    ```
    tests/test_interrupt_tty_wedge.py::PredicateTests::test_both_streams_tty_is_safe PASSED [  7%]
    tests/test_interrupt_tty_wedge.py::PredicateTests::test_the_measured_wedge_shape_is_refused PASSED [ 14%]
    tests/test_interrupt_tty_wedge.py::PredicateTests::test_unreadable_stdin_is_refused PASSED [ 21%]
    tests/test_interrupt_tty_wedge.py::PredicateTests::test_neither_stream_tty_is_refused PASSED [ 28%]
    tests/test_interrupt_tty_wedge.py::PredicateTests::test_a_closed_stream_is_not_a_terminal PASSED [ 35%]
    tests/test_interrupt_tty_wedge.py::ForcedNoninteractiveTests::test_ci_refuses_even_on_a_real_terminal PASSED [ 42%]
    tests/test_interrupt_tty_wedge.py::ForcedNoninteractiveTests::test_aw_noninteractive_refuses_even_on_a_real_terminal PASSED [ 50%]
    tests/test_interrupt_tty_wedge.py::ForcedNoninteractiveTests::test_falsey_spellings_do_not_force PASSED [ 57%]
    tests/test_interrupt_tty_wedge.py::ForcedNoninteractiveTests::test_force_override_works_without_ttys PASSED [ 64%]
    tests/test_interrupt_tty_wedge.py::ForcedNoninteractiveTests::test_ci_beats_the_force_override PASSED [ 71%]
    tests/test_interrupt_tty_wedge.py::HandlerDoesNotBlockTests::test_piped_output_never_reaches_the_prompt PASSED [ 78%]
    tests/test_interrupt_tty_wedge.py::HandlerDoesNotBlockTests::test_ci_never_reaches_the_prompt PASSED [ 85%]
    tests/test_interrupt_tty_wedge.py::HandlerDoesNotBlockTests::test_the_ladder_still_requests_a_stop_in_the_unsafe_case PASSED [ 92%]
    tests/test_interrupt_tty_wedge.py::HandlerDoesNotBlockTests::test_a_real_terminal_still_gets_the_menu PASSED [100%]
    ============================== 14 passed in 0.29s ==============================
    ```
    3. Forbidden pattern scan:
    ```
    $ rg -n "test_no_parallel_palette_defined|T\.__dict__" tests/test_term_components.py
    (empty, exit code 1)
    ```
    4. Scratch `Term.format_diagnostic` return-`""` mutation (reverted):
    ```
    FAILED tests/test_term_components.py::TermComponentsTests::test_stream_print_methods
    FAILED tests/test_term_components.py::TermComponentsTests::test_diagnostic_component
    ========================= 2 failed, 13 passed in 0.29s =========================
    ```
    5. Scratch `_colorize_tree_segment` return-`""` mutation (reverted):
    ```
    FAILED tests/test_attention_stem.py::AttentionStemTests::test_long_shows_full_path
    AssertionError: '.aw/records/backlog/open/20260815-demo-01-aaa111-x.backlog.md' not found
    ========================= 1 failed, 3 passed in 0.35s ==========================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `-v` run showing every restored test PASSED, zero failed, and the failure from a scratch `is_ack_valid` return-False mutation (reverted).
  - Observed evidence:
    1. `-v` test run:
    ```
    $ python3 -m pytest tests/test_comms.py -o addopts="" -v
    collecting ... collected 18 items

    tests/test_comms.py::FilenameSafetyTests::test_rejects_traversal_and_separators PASSED [  5%]
    tests/test_comms.py::FilenameSafetyTests::test_rejects_drive_letter_and_control_chars PASSED [ 11%]
    tests/test_comms.py::FilenameSafetyTests::test_rejects_empty_and_oversize PASSED [ 16%]
    tests/test_comms.py::FilenameSafetyTests::test_accepts_conventional_name PASSED [ 22%]
    tests/test_comms.py::AckTests::test_closed_enum_membership PASSED        [ 27%]
    tests/test_comms.py::AckTests::test_valid_ack PASSED                     [ 33%]
    tests/test_comms.py::AckTests::test_ack_rejects_free_text_state PASSED   [ 38%]
    tests/test_comms.py::AckTests::test_ack_missing_fields_and_bad_at PASSED [ 44%]
    tests/test_comms.py::AckTests::test_ack_filename PASSED                  [ 50%]
    tests/test_comms.py::AckTests::test_authorized_writer_table PASSED       [ 55%]
    tests/test_comms.py::NotBeforeTests::test_rejects_garbage PASSED         [ 61%]
    tests/test_comms.py::NotBeforeTests::test_parses_iso_and_z PASSED        [ 66%]
    tests/test_comms.py::EnvelopeTests::test_injection_in_payload_is_inert PASSED [ 72%]
    tests/test_comms.py::EnvelopeTests::test_parse_reads_header_not_payload PASSED [ 77%]
    tests/test_comms.py::EnvelopeTests::test_missing_required_and_bad_kind PASSED [ 83%]
    tests/test_comms.py::EnvelopeTests::test_bad_status_and_not_before PASSED [ 88%]
    tests/test_comms.py::EnvelopeTests::test_valid_header_passes PASSED      [ 94%]
    tests/test_comms.py::PointerBlockTests::test_agents_block_has_check_inbox_clause PASSED [100%]
    ============================== 18 passed in 0.25s ==============================
    ```
    2. Scratch `is_ack_valid` return-False mutation (reverted):
    ```
    FAILED tests/test_comms.py::AckTests::test_valid_ack - AssertionError: False is not true
    ========================= 1 failed, 17 passed in 0.34s =========================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `-v` lines for the new residual tests PASSED; paste the failures from scratch `is_ack_valid` return-True, `is_envelope_header_valid` return-True, `has_findings` return-True and `reset_signal_ladder` early-`return None` mutations (reverted), each naming a failing `ResidualKeyTests` test; for `reset_signal_ladder`, also paste the residual test failing when run ALONE (`<file>::ResidualKeyTests`), which proves the kill does not depend on order (F-06); paste the per-key reach listing showing all 19 keys REACHED, and the full 19-key sweep from Required tests showing every mutation KILLED; the bare `python3 -m pytest` summary line, and a final empty `git diff agent_workflows/`.
  - Observed evidence:
    1. `-v` lines for new residual tests PASSED:
    ```
    tests/test_comms.py::ResidualKeyTests::test_is_ack_valid_rejects_non_enum_state PASSED
    tests/test_comms.py::ResidualKeyTests::test_is_envelope_header_valid_rejects_empty PASSED
    tests/test_output_contract.py::ResidualKeyTests::test_command_result_has_findings PASSED
    tests/test_interrupt_tty_wedge.py::ResidualKeyTests::test_reset_signal_ladder_clears_globals PASSED
    ```
    2. Failures from scratch mutations naming `ResidualKeyTests`:
    - `is_ack_valid` return True:
    ```
    FAILED tests/test_comms.py::ResidualKeyTests::test_is_ack_valid_rejects_non_enum_state
    AssertionError: True is not false
    ========================= 1 failed, 19 passed in 0.28s =========================
    ```
    - `is_envelope_header_valid` return True:
    ```
    FAILED tests/test_comms.py::ResidualKeyTests::test_is_envelope_header_valid_rejects_empty
    AssertionError: True is not false
    ========================= 1 failed, 19 passed in 0.28s =========================
    ```
    - `CommandResult.has_findings` return True:
    ```
    FAILED tests/test_output_contract.py::ResidualKeyTests::test_command_result_has_findings
    AssertionError: True is not false
    ========================= 2 failed, 3 passed in 0.24s ==========================
    ```
    - `reset_signal_ladder` early `return None`:
    ```
    FAILED tests/test_interrupt_tty_wedge.py::ResidualKeyTests::test_reset_signal_ladder_clears_globals
    AssertionError: 3 != 0
    ========================= 1 failed, 14 passed in 0.34s =========================
    ```
    3. Residual `reset_signal_ladder` test failing when run ALONE:
    ```
    $ python3 -m pytest tests/test_interrupt_tty_wedge.py::ResidualKeyTests -o addopts="" -v
    tests/test_interrupt_tty_wedge.py::ResidualKeyTests::test_reset_signal_ladder_clears_globals FAILED [100%]
    AssertionError: 3 != 0
    ============================== 1 failed in 0.29s ===============================
    ```
    4. Per-key reach listing (all 19 keys REACHED):
    ```
    PER-KEY REACH REPORT (19 keys under -m core):
    -----------------------------------------------------------------
    [  REACHED  ] parse_args (agent_workflows/agy_sessions.py): 5/36 body lines executed ([232, 250, 256, 262, 267]...)
    [  REACHED  ] main (agent_workflows/agy_sessions.py): 1/91 body lines executed ([271]...)
    [  REACHED  ] Term.format_diagnostic (agent_workflows/term.py): 7/8 body lines executed ([1606, 1607, 1608, 1609, 1610]...)
    [  REACHED  ] Term.diagnostic (agent_workflows/term.py): 1/3 body lines executed ([1622]...)
    [  REACHED  ] Term.title (agent_workflows/term.py): 1/3 body lines executed ([1499]...)
    [  REACHED  ] Term.evidence (agent_workflows/term.py): 1/1 body lines executed ([1682]...)
    [  REACHED  ] Term.fix (agent_workflows/term.py): 1/1 body lines executed ([1690]...)
    [  REACHED  ] Term.outcome (agent_workflows/term.py): 1/1 body lines executed ([1515]...)
    [  REACHED  ] Term.preview (agent_workflows/term.py): 1/1 body lines executed ([1652]...)
    [  REACHED  ] Term.section (agent_workflows/term.py): 1/1 body lines executed ([1522]...)
    [  REACHED  ] _colorize_tree_segment (agent_workflows/attention.py): 6/14 body lines executed ([2384, 2385, 2386, 2388, 2389]...)
    [  REACHED  ] main (agent_workflows/agy_view.py): 5/33 body lines executed ([92, 93, 96, 99, 104]...)
    [  REACHED  ] Diagnostic.from_drift (agent_workflows/result_types.py): 1/8 body lines executed ([246]...)
    [  REACHED  ] CommandResult.has_findings (agent_workflows/result_types.py): 1/1 body lines executed ([331]...)
    [  REACHED  ] CommandResult.is_error (agent_workflows/result_types.py): 1/1 body lines executed ([335]...)
    [  REACHED  ] main (agent_workflows/agy_run.py): 4/8 body lines executed ([854, 855, 856, 859]...)
    [  REACHED  ] reset_signal_ladder (agent_workflows/runner_stop.py): 2/4 body lines executed ([1783, 1784]...)
    [  REACHED  ] is_ack_valid (agent_workflows/comms.py): 1/2 body lines executed ([216]...)
    [  REACHED  ] is_envelope_header_valid (agent_workflows/comms.py): 1/2 body lines executed ([183]...)
    -----------------------------------------------------------------
    All 19 keys reached: True
    ```
    5. Full 19-key early-return mutation sweep results (all 26 mutations KILLED):
    ```
    19-KEY EARLY-RETURN MUTATION SWEEP RESULTS:
    Key                              Mutation             Status     Test Summary
    --------------------------------------------------------------------------------
    parse_args                       return None          KILLED     1 failed, 76 passed in 3.06s
    main                             return 0             KILLED     1 failed, 76 passed in 2.55s
    main                             return 1             KILLED     1 failed, 76 passed in 3.69s
    Term.format_diagnostic           return ""            KILLED     2 failed, 75 passed in 3.96s
    Term.diagnostic                  early return None    KILLED     1 failed, 76 passed in 4.20s
    Term.title                       early return None    KILLED     1 failed, 76 passed in 4.24s
    Term.evidence                    early return None    KILLED     1 failed, 76 passed in 3.12s
    Term.fix                         early return None    KILLED     1 failed, 76 passed in 2.68s
    Term.outcome                     early return None    KILLED     1 failed, 76 passed in 2.61s
    Term.preview                     early return None    KILLED     1 failed, 76 passed in 2.84s
    Term.section                     early return None    KILLED     1 failed, 76 passed in 2.86s
    _colorize_tree_segment           return ""            KILLED     1 failed, 76 passed in 5.88s
    main                             return 0             KILLED     1 failed, 76 passed in 2.90s
    main                             return 1             KILLED     1 failed, 76 passed in 3.58s
    Diagnostic.from_drift            return None          KILLED     1 failed, 76 passed in 3.96s
    CommandResult.has_findings       return True          KILLED     2 failed, 75 passed in 2.57s
    CommandResult.has_findings       return False         KILLED     3 failed, 74 passed in 3.94s
    CommandResult.is_error           return True          KILLED     2 failed, 75 passed in 3.56s
    CommandResult.is_error           return False         KILLED     1 failed, 76 passed in 2.93s
    main                             return 0             KILLED     2 failed, 75 passed in 3.92s
    main                             return 1             KILLED     2 failed, 75 passed in 4.21s
    reset_signal_ladder              early return None    KILLED     1 failed, 76 passed in 3.23s
    is_ack_valid                     return True          KILLED     1 failed, 76 passed in 2.66s
    is_ack_valid                     return False         KILLED     1 failed, 76 passed in 2.97s
    is_envelope_header_valid         return True          KILLED     1 failed, 76 passed in 3.83s
    is_envelope_header_valid         return False         KILLED     1 failed, 76 passed in 3.26s
    --------------------------------------------------------------------------------
    Total mutations tested: 26, All killed: True
    ```
    6. Bare `python3 -m pytest` summary line:
    ```
    1535 passed, 3 warnings in 69.23s (0:01:09)
    ```
    7. Final `git diff agent_workflows/`:
    ```
    $ git diff agent_workflows/
    (empty, exit code 0)
    ```
  - Result: pass

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
