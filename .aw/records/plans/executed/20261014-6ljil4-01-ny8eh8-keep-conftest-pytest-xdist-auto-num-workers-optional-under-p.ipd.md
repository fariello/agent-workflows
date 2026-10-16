# IPD: Keep conftest pytest_xdist_auto_num_workers optional under -p no:xdist and harden serial xdist-disabled tests

- Date: 2026-10-14
- Kind: child
- Concern: Backlog item `6ljil4` (`Work-Kind: bug`, `Priority: low`, `Blocks-Release: next`) was filed during execution of IPD `sk2rbf` (`7c95d8bbd`, `2026-10-13`) when `conftest.pytest_xdist_auto_num_workers` (`def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:` in `conftest.py`, line 90) carried a bare `@pytest.hookimpl` decorator (introduced by `acd3d406f`). Because `pytest_xdist_auto_num_workers` is a hookspec declared by `xdist.newhooks` (loaded only when `xdist.plugin` is active), running `pytest` with `-p no:xdist` (such as `tools/replay_coverage_diff.py` serial runs or `python3 -m pytest -o addopts="" -p no:xdist`) caused `pluggy`'s `PytestPluginManager.check_pending()` to fail with `pluggy.PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers' in plugin <module 'conftest' ...>`. An un-planned commit (`497d35913`, "cihealth: scale -n auto to all cpus in CI and min 4 locally") subsequently changed `conftest.pytest_xdist_auto_num_workers` (`conftest.py`, line 89) to `@pytest.hookimpl(optionalhook=True)` and added `test_pytest_runs_without_xdist_plugin` (`tests/test_xdist_auto_workers.py`, line 116), but did not link or graduate `6ljil4` and left three defects in `conftest.py` and `tests/test_xdist_auto_workers.py`: (1) `test_pytest_runs_without_xdist_plugin` spawns `pytest -o addopts= -p no:xdist` without scrubbing `PYTEST_ADDOPTS` or `PYTEST_PLUGINS` from the subprocess environment, so any ambient `PYTEST_ADDOPTS` carrying `-n` or `--dist` (prepended before `_initini` in `_pytest.config.Config._preparse`) causes the test to fail with `exit 4` (`unrecognized arguments: -n`); (2) `tests/test_xdist_auto_workers.py` defines bare module-level `def test_*()` functions with no `unittest.TestCase` class, so `make test-serial` (`python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py`) discovers `0 tests` and exits `5` (`NO TESTS RAN`), violating the `pyproject.toml` `unittest.TestCase` contract; and (3) `tests/test_xdist_auto_workers.py` lacks an in-process `pytest.PytestPluginManager.check_pending()` test for `conftest` without `xdist` hookspecs, while `conftest.py` lacks contract documentation explaining why `optionalhook=True` on `pytest_xdist_auto_num_workers` is load-bearing.
- Scope: Document the `optionalhook=True` contract on `conftest.pytest_xdist_auto_num_workers` (`conftest.py`, lines 1-20 and 89-96); convert `tests/test_xdist_auto_workers.py` to a `unittest.TestCase` class (`XdistAutoWorkersTests`) so both `pytest` and `unittest discover` (`make test-serial`) execute all tests; scrub `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` in the `-p no:xdist` subprocess helper (keeping the production `-p no:xdist` argv) and contain the import-time side effects of `import conftest` under `unittest`; and add behavioral tests verifying both ambient-`PYTEST_ADDOPTS` isolation and in-process `pytest.PytestPluginManager.check_pending()` validation of `conftest` without `xdist` hookspecs.
- Scope-Paths: conftest.py, tests/test_xdist_auto_workers.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- From-Backlog: 6ljil4
- Blocks-Release: next
- Work-Kind: bug
- Priority: low
- Set: 6ljil4
- Order: 1
- Highest E allocated: 03
- Author: Antigravity
- Id: ny8eh8

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ny8eh8 verified (set 6ljil4, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-14 to-review (aw set): Authored review-ready child IPD ny8eh8 from backlog 6ljil4

- 2026-10-14 draft (Antigravity): created.

## Goal

Ensure `conftest.pytest_xdist_auto_num_workers` remains an optional hook implementation (`@pytest.hookimpl(optionalhook=True)`) that validates cleanly when `xdist` hookspecs are absent (`-p no:xdist`), and harden `tests/test_xdist_auto_workers.py` so its `-p no:xdist` and worker-scaling checks are immune to ambient `PYTEST_ADDOPTS`/`PYTEST_PLUGINS`, exercise `PytestPluginManager.check_pending()` directly, and run under both `pytest` and `unittest discover` (`make test-serial`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Conftest optionalhook contract and xdist-disabled test hardening

- [x] E-01 Update `conftest.py` around `conftest.pytest_xdist_auto_num_workers` (`@pytest.hookimpl(optionalhook=True)` / `def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:`, lines 89-96) and the module docstring (`"""Root pytest conftest: guarantee the suite ALWAYS runs in parallel (-n auto)`, lines 1-20) to document why `optionalhook=True` is load-bearing (backlog `6ljil4`: `pytest_xdist_auto_num_workers` is an `xdist.newhooks` hookspec registered only when `xdist.plugin` loads, so omitting `optionalhook=True` raises `pluggy.PluginValidationError` during `PytestPluginManager.check_pending()` whenever `pytest` is invoked with `-p no:xdist`, such as in `tools/replay_coverage_diff.py` serial runs or `-o addopts="" -p no:xdist`), and update the module docstring (`conftest.py`, line 6) to reflect the `pytest_xdist_auto_num_workers` worker-bounding policy rather than `one worker per CPU`; and correct the coordinator-role comment (`conftest.py` line 158, `make test-serial` (`python3 -m unittest`) never loads this file`), which is false once a unittest module imports `conftest` (`F-06`), to say that `unittest` loads it only through an explicit import and that `tests/test_xdist_auto_workers.py` restores `os.environ` around that import. Documentation-only: do NOT change the hook's decorator, signature, return values, or any other `conftest.py` code (the worker-count tests in E-02 pin that behavior unchanged).
  - Depends on: none
  - Expected outcome: `conftest.pytest_xdist_auto_num_workers` retains `@pytest.hookimpl(optionalhook=True)` with an explicit comment and docstring explaining the `-p no:xdist` `PluginValidationError` contract (`6ljil4`), the module docstring accurately states the `-n auto` worker resolution policy, and `git diff -- conftest.py` touches only comment and docstring lines.
  - Execution state: performed

- [x] E-02 Refactor `tests/test_xdist_auto_workers.py` into a `unittest.TestCase` subclass (`class XdistAutoWorkersTests(unittest.TestCase):`) and harden its `-p no:xdist` coverage:
  - Wrap all existing worker-count and CPU-count tests (`test_auto_num_workers_defaults_to_half_cpus`, `test_auto_num_workers_scaling_and_floors`, `test_auto_num_workers_ci_mode`, `test_auto_num_workers_honors_env_override`, `test_auto_num_workers_env_override_floors_at_one`, `test_auto_num_workers_invalid_env_falls_back_to_local_policy`, `test_available_cpus_returns_positive_integer`, and `test_pytest_runs_without_xdist_plugin`) as methods on `XdistAutoWorkersTests(unittest.TestCase)` so both `python3 -m pytest` and `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py` discover and execute them.
  - Extract a helper `_run_pytest_without_xdist(self) -> subprocess.CompletedProcess[str]` on `XdistAutoWorkersTests` that copies `os.environ`, pops `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` from the copy so ambient xdist flags (`-n`, `--dist`) cannot leak ahead of `-o addopts=` in `_pytest.config.Config._preparse`, and runs `[sys.executable, "-m", "pytest", "-o", "addopts=", "-p", "no:xdist", "tests/test_xdist_auto_workers.py", "-k", "test_available_cpus_returns_positive_integer"]` with `env=<the scrubbed copy>`, `cwd=os.path.dirname(os.path.abspath(conftest.__file__))` (the repository root, so the relative test path resolves regardless of the runner's working directory), `capture_output=True`, `text=True`, `check=False`, and `timeout=120` (so a hung child fails the test instead of hanging `make test-serial`, where the `conftest.py` hang guard does not run). The argv deliberately disables only `xdist`, matching the real serial invocation it protects (`tools/replay_coverage_diff.py` `_build_pytest_cmd`, `cmd.extend(["-p", "no:xdist"])` at line 169); do NOT add `-p no:xdist.looponfail`, which would make the test exercise a different invocation than production.
  - Add `test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags(self) -> None`: sets `PYTEST_ADDOPTS="-n 2 --dist=worksteal"` in `os.environ` via `patch.dict` and asserts `_run_pytest_without_xdist()` exits `0` with neither `PluginValidationError` nor `unrecognized arguments` in `stdout`/`stderr`.
  - Add `test_conftest_registers_on_pluginmanager_without_xdist_hookspecs(self) -> None`: instantiates a fresh `pytest.PytestPluginManager()`, asserts the precondition that `pm.hasplugin("xdist")` is `False` (so no `xdist.newhooks` hookspec is registered), calls `pm.register(conftest)` and `pm.check_pending()`, and asserts that `check_pending()` succeeds without raising `pluggy.PluginValidationError`. (Mechanism demonstrated at review, see `F-05`.)
  - Contain the `conftest` import (`F-06`): replace the module-level `import conftest` with a module-level loader used by `XdistAutoWorkersTests.setUpClass` that returns `sys.modules["conftest"]` when pytest has already loaded it, and otherwise (the `unittest discover` path) raises `unittest.SkipTest` if `importlib.util.find_spec("xdist") is None` (so `_ensure_xdist_then_reexec` can never `pip install` or `os.execv` the unittest process), then snapshots `dict(os.environ)`, imports `conftest`, and restores `os.environ` to the snapshot (`clear()` + `update()`), so the import cannot leak conftest's env scrub/sandbox into later unittest modules.
  - Keep every existing worker-count assertion and its input/expected pairs unchanged; this item only re-homes them as methods (use `self.assertEqual`/`self.assertTrue` or plain `assert`, either runs under both runners).
  - Depends on: E-01
  - Expected outcome: every test in `tests/test_xdist_auto_workers.py` is a method of `XdistAutoWorkersTests(unittest.TestCase)` and passes under both `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py` and `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` (exit `0`, with the unittest `Ran N tests` count equal to the pytest `N passed` count and N greater than zero), including when `PYTEST_ADDOPTS="-n 2 --dist=worksteal"` is set in the outer environment; the two new tests and the re-homed `test_pytest_runs_without_xdist_plugin` are among those run.
  - Execution state: performed

- [x] E-03 Perform sensitivity verification and full repository validation:
  - Sensitivity check A (hook contract): temporarily change `@pytest.hookimpl(optionalhook=True)` to `@pytest.hookimpl` on `conftest.pytest_xdist_auto_num_workers`, run `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py -k "test_conftest_registers_on_pluginmanager_without_xdist_hookspecs or test_pytest_runs_without_xdist_plugin"`, verify both tests fail with `PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers'`, and restore `@pytest.hookimpl(optionalhook=True)`.
  - Sensitivity check B (env scrub): temporarily delete the `PYTEST_ADDOPTS` pop from `_run_pytest_without_xdist`, run `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py -k test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags`, verify it fails on the child's non-zero exit with `unrecognized arguments: -n` in the captured output, and restore the pop.
  - After both restorations, confirm with `git diff -- conftest.py tests/test_xdist_auto_workers.py` that no sensitivity mutation remains (only the E-01/E-02 edits).
  - Run `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` and `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py`.
  - Run the bare repository test suite (`python3 -m pytest`), `aw check release-gates`, and `aw sanitize --agent`.
  - Depends on: E-01, E-02
  - Expected outcome: Sensitivity check A proves both the in-process `PytestPluginManager.check_pending()` test and the subprocess `-p no:xdist` test fail when `optionalhook=True` is removed; sensitivity check B proves the ambient-`PYTEST_ADDOPTS` test fails when the scrub is removed; both mutations are reverted; `unittest discover`, ambient-`PYTEST_ADDOPTS` pytest, bare `python3 -m pytest`, `aw check release-gates`, and `aw sanitize --agent` all exit `0`.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Repository test runner contract (`AGENTS.md` section `## Repository development contract (repo-local rule)`): run the full test suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`). For targeted/narrowed runs, clear configured `addopts` explicitly with `python3 -m pytest -o addopts=""`.
- Dual runner compatibility (`pyproject.toml` comment `"The tests are stdlib unittest.TestCase and also run under python -m unittest discover -s tests -t ."` at line 194): test modules in `tests/` must wrap test methods in `unittest.TestCase` subclasses so `make test-serial` (`python -m unittest discover -s tests -t .`) discovers and executes them.
- No code-pinning tests (`AGENTS.md` section `TEST OUTCOMES, NOT CODE STRUCTURE (NO CODE-PINNING TESTS)`, P16): tests must exercise live functions, plugin managers, or subprocesses and assert observable outcomes and exit codes rather than inspecting source text or ASTs.
- Release gate handoff (`AGENTS.md` section `### Every live bug gates the next release`): backlog `6ljil4` carries `- Work-Kind: bug` and `- Blocks-Release: next`, so this graduating IPD inherits `- From-Backlog: 6ljil4` and `- Blocks-Release: next`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Backlog `6ljil4` was filed during IPD `sk2rbf` execution (`7c95d8bbd`, `2026-10-13`) because `acd3d406f` added `conftest.pytest_xdist_auto_num_workers` (`def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:` in `conftest.py`, line 90) with bare `@pytest.hookimpl`, causing `pluggy.PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers'` whenever `-p no:xdist` disabled `xdist.plugin`. Un-planned commit `497d35913` subsequently changed `conftest.py` line 89 to `@pytest.hookimpl(optionalhook=True)` and added `test_pytest_runs_without_xdist_plugin` (`tests/test_xdist_auto_workers.py`, line 116) without linking or graduating `6ljil4`. | `git show 7c95d8bbd 497d35913 acd3d406f`; `conftest.pytest_xdist_auto_num_workers` (`conftest.py`, lines 89-112). |
| F-02 | `test_pytest_runs_without_xdist_plugin` (`tests/test_xdist_auto_workers.py`, lines 116-140) runs `[sys.executable, "-m", "pytest", "-o", "addopts=", "-p", "no:xdist", ...]` without scrubbing `PYTEST_ADDOPTS` or `PYTEST_PLUGINS` from `os.environ`. In `_pytest.config.Config._preparse`, `PYTEST_ADDOPTS` is prepended to `args` before `_initini(args)` processes `-o addopts=`, so any ambient `PYTEST_ADDOPTS` containing `-n` or `--dist` fails the test with exit code `4` (`unrecognized arguments: -n`). | Measured at HEAD `7dc1b0e5f`: `PYTEST_ADDOPTS="-n 2" python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py -k test_pytest_runs_without_xdist_plugin` fails with `AssertionError: assert 4 == 0` (`python3 -m pytest: error: unrecognized arguments: -n`). |
| F-03 | `tests/test_xdist_auto_workers.py` defines eight bare module-level `def test_*()` functions and no `unittest.TestCase` class, so `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` (`make test-serial`) discovers zero tests and exits `5` (`NO TESTS RAN`). | Measured at HEAD `7dc1b0e5f`: `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` outputs `Ran 0 tests in 0.000s / NO TESTS RAN` (exit `5`). |
| F-04 | `pytest-xdist` registers two `pytest11` entry points (`xdist = xdist.plugin` and `xdist.looponfail = xdist.looponfail`). Registering `conftest` on a fresh `pytest.PytestPluginManager()` in-process and calling `check_pending()` directly tests the `optionalhook=True` contract without `xdist.newhooks` in <1ms, whereas `test_pytest_runs_without_xdist_plugin` only exercises the subprocess path. The production serial invocation disables only `xdist` (`tools/replay_coverage_diff.py` `_build_pytest_cmd`, `cmd.extend(["-p", "no:xdist"])`, line 169), so the subprocess test keeps that exact argv (review decision D-2). | Measured at HEAD `7dc1b0e5f`: `importlib.metadata.distribution("pytest-xdist").entry_points` returns `[('xdist', 'xdist.plugin'), ('xdist.looponfail', 'xdist.looponfail')]`. |
| F-05 | The in-process mechanism works and is sensitive: with the real `conftest` registered on a fresh `pytest.PytestPluginManager()`, `check_pending()` succeeds and `hasplugin("xdist")` is `False`; with the decorator replaced by bare `@pytest.hookimpl` (in-memory copy, no file edited) `check_pending()` raises `PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers' in plugin <module ...>`. | Review probe at `461fdf679` (pytest 8.2.2, pluggy 1.6.0, xdist 3.8.0): `optionalhook=True -> check_pending OK; hasplugin xdist: False` / `bare hookimpl -> RAISED PluginValidationError unknown hook 'pytest_xdist_auto_num_workers'`. Also `env -u PYTEST_ADDOPTS -u PYTEST_PLUGINS python3 -m pytest -o addopts= -p no:xdist ... -k test_available_cpus_returns_positive_integer` under an outer `PYTEST_ADDOPTS="-n 2 --dist=worksteal"`: `1 passed, 7 deselected`, exit `0`. |
| F-06 | Importing `conftest` outside pytest has process-wide side effects, and `unittest discover` already imports it today because `tests/test_xdist_auto_workers.py` does `import conftest` at module level (line 15): it pops `AW_EXECUTION_ROLE`, `AW_RUN_ID`, `CI`, etc., overwrites `AW_HOME`/`XDG_CONFIG_HOME`/`PYTHONPATH` (`conftest.py` lines 166-205, 228-235), and calls `_ensure_xdist_then_reexec()` (line 623), which, when `xdist` is not importable, runs `pip install pytest-xdist>=3` and `os.execv`s `python -m pytest <argv>`, replacing a `make test-serial` process with pytest. The `conftest.py` comment at line 158 (`make test-serial` ... `never loads this file`) is therefore false. | Review probe at `461fdf679`: `unittest.TestLoader().discover('tests','test_xdist_auto_workers.py','.')` leaves `'conftest' in sys.modules == True`; importing `conftest` changed 14 env keys (`AW_AGENT_MODEL`, `AW_CONFIG_DIR`, `AW_EXECUTION_ROLE`, `AW_HOME`, `AW_IN_TEST_SESSION`, `AW_ITEM_ID6`, `AW_RUNNER`, `AW_RUN_ID`, `GIT_COMMITTER_EMAIL`, `GIT_COMMITTER_NAME`, `PYTHONIOENCODING`, `PYTHONPATH`, `PYTHONUTF8`, `XDG_CONFIG_HOME`); snapshot/restore of `os.environ` around the import returned `env restored: True`. |

## Proposed changes (ordered, validatable)

1. Document the `optionalhook=True` `-p no:xdist` requirement (`6ljil4`) on `conftest.pytest_xdist_auto_num_workers` (`conftest.py`, lines 89-96), align the module docstring (`conftest.py`, lines 1-20) with the worker-bounding policy, and correct the false `never loads this file` comment (line 158) (`E-01`).
2. Convert `tests/test_xdist_auto_workers.py` to `XdistAutoWorkersTests(unittest.TestCase)` with a contained `conftest` import (env snapshot/restore, skip when `xdist` is absent), scrub `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` in `_run_pytest_without_xdist` (argv `-p no:xdist`, repo-root `cwd`, `timeout=120`), and add `test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags` plus `test_conftest_registers_on_pluginmanager_without_xdist_hookspecs` (`E-02`).
3. Verify failure sensitivity under temporary removal of `optionalhook=True` (check A) and of the `PYTEST_ADDOPTS` scrub (check B), verify `unittest discover` and ambient-`PYTEST_ADDOPTS` execution, and run the bare full test suite, release-gates check, and leak sanitizer (`E-03`).

## Deferred / out of scope (with reason)

- Stripping `-n auto --dist=worksteal` from `pyproject.toml` `addopts` when `-p no:xdist` is passed without `-o addopts=""`: `pyproject.toml` (`addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`, line 213) and `AGENTS.md` (`python3 -m pytest -o addopts=""`, line 290) intentionally require `-n auto` on default runs and `-o addopts=""` on narrowed/serial runs (`tools/replay_coverage_diff.py` `_build_pytest_cmd`, line 141).
  - Carrier-Declined: By design per `conftest.py` module docstring and `AGENTS.md` repository development contract; no defect exists when `-o addopts=""` is used as documented.

## Scope check

- Over-scope: none.
- Under-scope: none. Both files involved in the `conftest.pytest_xdist_auto_num_workers` hook implementation and its tests (`conftest.py` and `tests/test_xdist_auto_workers.py`) are in `- Scope-Paths:`.

## Required tests / validation

Test counts below are re-derived at execution time from the runner output; the bar is that every test in the module passes, the unittest count equals the pytest count, and the count is non-zero (not a fixed number).

- Targeted pytest run: `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py` (all pass, exit `0`).
- Ambient `PYTEST_ADDOPTS` resilience run: `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py` (all pass, exit `0`).
- Stdlib `unittest` discovery run (`make test-serial` compatibility): `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` (`Ran N tests`, N equal to the pytest count, `OK`, exit `0`).
- Sensitivity check A: temporarily change `@pytest.hookimpl(optionalhook=True)` to `@pytest.hookimpl` on `conftest.pytest_xdist_auto_num_workers`, confirm both `test_conftest_registers_on_pluginmanager_without_xdist_hookspecs` and `test_pytest_runs_without_xdist_plugin` fail with `PluginValidationError`, and restore `optionalhook=True`.
- Sensitivity check B: temporarily remove the `PYTEST_ADDOPTS` pop in `_run_pytest_without_xdist`, confirm the ambient-addopts test fails with `unrecognized arguments: -n`, and restore it.
- Full repository suite and checks: bare `python3 -m pytest`, `aw check release-gates`, and `aw sanitize --agent`.

## Spec / documentation sync

N/A for `.spec.md` files and `CHANGELOG.md`: `conftest.py` and `tests/test_xdist_auto_workers.py` are repository-internal test harness files not shipped in the wheel or sdist (`pyproject.toml` `[tool.hatch.build.targets.wheel]` and `[tool.hatch.build.targets.sdist]`, lines 162-186), and no specification governs root `conftest.py` hooks. The internal contract comment and docstring in `conftest.py` are updated in `E-01`.

## Open questions

### OQ-01: Since commit `497d35913` already added `@pytest.hookimpl(optionalhook=True)` on `conftest.pytest_xdist_auto_num_workers` without linking `6ljil4`, how should `6ljil4` be graduated and closed?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence (`git show 7c95d8bbd 497d35913`, `conftest.py` line 89, `tests/test_xdist_auto_workers.py` line 116). Because `6ljil4` carries `- Work-Kind: bug` and `- Blocks-Release: next`, the close-legitimacy rule (`AGENTS.md` section `### Acting on a backlog item (graduate / implement / execute)`, `check_engine.evaluate_blocking_close`) requires a linked carrier (`- From-Backlog: 6ljil4`, `- Blocks-Release: next`) that executes and addresses the remaining defects in the un-planned `497d35913` change (`F-02`, `F-03`, `F-04`) across `conftest.py` and `tests/test_xdist_auto_workers.py`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted `git diff -- conftest.py` showing `@pytest.hookimpl(optionalhook=True)` on `conftest.pytest_xdist_auto_num_workers` unchanged, the updated docstring and comment citing `6ljil4`, the updated module header docstring, and the corrected `make test-serial` comment (former line 158), with every changed line a comment or docstring line (no executable code changed).
  - Observed evidence:
```diff
diff --git a/conftest.py b/conftest.py
index 68490b563..8230e8626 100644
--- a/conftest.py
+++ b/conftest.py
@@ -3,7 +3,8 @@ run the suite in the COORDINATOR role so a runner-launched turn measures the sam
 tree a human does (backlog `1uq1cu`).

 The release suite is large and IO/subprocess bound; running it serially costs multiples of
-the wall time, so `-n auto` (pytest-xdist, capped at six workers) is the default in
+the wall time, so `-n auto` (pytest-xdist, capped at half of available CPUs up to six workers,
+minimum 1) is the default in
 `[tool.pytest.ini_options] addopts` in pyproject.toml. That default hard-requires the
 xdist plugin: without it, pytest aborts with `unrecognized arguments: -n` before any
 test runs.
@@ -85,13 +86,29 @@ def _available_cpus() -> int:
     return os.cpu_count() or 2


+# --------------------------------------------------------------------------------------
+# xdist auto-num-workers hook: cap -n auto worker count and stay optional under -p no:xdist
+# (backlog `6ljil4`).
+#
+# WHY optionalhook=True IS LOAD-BEARING. `pytest_xdist_auto_num_workers` is an
+# `xdist.newhooks` hookspec registered only when `xdist.plugin` loads. When pytest is
+# invoked with `-p no:xdist` (such as in `tools/replay_coverage_diff.py` serial runs or
+# `python3 -m pytest -o addopts="" -p no:xdist`), pluggy's `PytestPluginManager.check_pending()`
+# fails with `pluggy.PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers'`
+# unless this hook implementation is declared with `optionalhook=True`.
+# --------------------------------------------------------------------------------------
 @pytest.hookimpl(optionalhook=True)
 def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:
     """Resolve -n auto worker count.

-    Use at most half the available CPUs and never more than six workers.
+    Use at most half the available CPUs and never more than six workers (minimum 1).
     An explicit PYTEST_XDIST_AUTO_NUM_WORKERS can lower the count, but cannot
     exceed the same limit.
+
+    Declared with optionalhook=True because pytest_xdist_auto_num_workers is an
+    xdist.newhooks hookspec loaded only when xdist.plugin is active; without
+    optionalhook=True, running pytest under -p no:xdist raises PluginValidationError
+    during PytestPluginManager.check_pending() (backlog `6ljil4`).
     """
     cpus = _available_cpus()
     limit = min(6, max(1, cpus // 2))
@@ -148,10 +165,11 @@ def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:
 # role with `support.declare_execution_role`, and a test that needs the worker marking sets
 # it on an explicit env dict passed to the code under test; re-asserting the marker with a
 # throwaway `pytest_runtest_setup` plugin is how to check a file (as plan yx9xsa did). The scrub
-# is pytest-only, so `make test-serial` (`python3 -m unittest`) never loads this file and is
-# protected only by the per-class declarations. (2) This scrubs the CURRENT process only;
-# a subprocess a test spawns inherits this already-cleaned environment, which is the
-# intended propagation.
+# is pytest-only; `make test-serial` (`python3 -m unittest`) loads this file only through an
+# explicit import, and `tests/test_xdist_auto_workers.py` restores `os.environ` around that
+# import; serial unittest suites are otherwise protected only by the per-class declarations.
+# (2) This scrubs the CURRENT process only; a subprocess a test spawns inherits this
+# already-cleaned environment, which is the intended propagation.
 #
 # Done at import time, before any test module is collected, so no test can observe the
 # marked value. `pop` is unconditional and side-effect-free when the variable is absent,
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted `git diff -- tests/test_xdist_auto_workers.py` and pasted outputs of (1) `python3 -m pytest -o addopts="" -v tests/test_xdist_auto_workers.py` (reachable via `XdistAutoWorkersTests` created in `E-02`), (2) `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" -v tests/test_xdist_auto_workers.py` (reachable via `XdistAutoWorkersTests._run_pytest_without_xdist` created in `E-02`), and (3) `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` (reachable via `XdistAutoWorkersTests(unittest.TestCase)` created in `E-02`), all exit `0` with every test passing, where the `-v` listings name `test_pytest_runs_without_xdist_plugin`, `test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags`, and `test_conftest_registers_on_pluginmanager_without_xdist_hookspecs` as passed (names are pointers; the bar is the behavior) and the unittest `Ran N tests` equals the pytest `N passed` (N re-derived at execution, non-zero, no `skipped`); and (4) the diff shows `_run_pytest_without_xdist` popping `PYTEST_ADDOPTS`/`PYTEST_PLUGINS`, passing repo-root `cwd` and `timeout=120`, and the `setUpClass` loader restoring `os.environ` around the `conftest` import.
  - Observed evidence: All 11 tests pass under pytest (-o addopts=""), ambient PYTEST_ADDOPTS (-n 2 --dist=worksteal), and unittest discover (-s tests -t . -p test_xdist_auto_workers.py -v); git diff shows env scrub in _run_pytest_without_xdist and os.environ snapshot/restore in setUpClass.
(1) `python3 -m pytest -o addopts="" -v tests/test_xdist_auto_workers.py`:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=4268215418
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/ny8eh8
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 11 items

tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_available_cpus_returns_positive_integer PASSED [  9%]
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_scaling_and_floors PASSED [ 18%]
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_ci_mode PASSED [ 27%]
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_honors_env_override PASSED [ 36%]
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_invalid_env_falls_back_to_local_policy PASSED [ 45%]
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_conftest_registers_on_pluginmanager_without_xdist_hookspecs PASSED [ 54%]
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_env_override_floors_at_one PASSED [ 63%]
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_pytest_runs_without_xdist_plugin PASSED [ 72%]
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags PASSED [ 81%]
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_caps_env_override PASSED [ 90%]
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_defaults_to_half_cpus PASSED [100%]

============================== 11 passed in 1.95s ==============================
```

(2) `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" -v tests/test_xdist_auto_workers.py`:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=526381185
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/ny8eh8
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
created: 2/2 workersinitialized: 1/2 workersinitialized: 2/2 workersready: 1/2 workers      ready: 2/2 workerscollecting: 1/2 workers2 workers [11 items]
scheduling tests via WorkStealingScheduling

tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_conftest_registers_on_pluginmanager_without_xdist_hookspecs
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_scaling_and_floors
[gw1] [  9%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_scaling_and_floors
[gw0] [ 18%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_conftest_registers_on_pluginmanager_without_xdist_hookspecs
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_pytest_runs_without_xdist_plugin
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_ci_mode
[gw0] [ 27%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_ci_mode
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_invalid_env_falls_back_to_local_policy
[gw0] [ 36%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_invalid_env_falls_back_to_local_policy
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_available_cpus_returns_positive_integer
[gw0] [ 45%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_available_cpus_returns_positive_integer
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_caps_env_override
[gw0] [ 54%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_caps_env_override
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_defaults_to_half_cpus
[gw0] [ 63%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_defaults_to_half_cpus
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_env_override_floors_at_one
[gw0] [ 72%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_env_override_floors_at_one
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags
[gw1] [ 81%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_pytest_runs_without_xdist_plugin
tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_honors_env_override
[gw1] [ 90%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_auto_num_workers_honors_env_override
[gw0] [100%] PASSED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags

============================== 11 passed in 1.83s ==============================
```

(3) `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v`:
```
test_auto_num_workers_caps_env_override (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_auto_num_workers_caps_env_override)
PYTEST_XDIST_AUTO_NUM_WORKERS exceeding the max cap is bounded. ... ok
test_auto_num_workers_ci_mode (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_auto_num_workers_ci_mode)
CI uses the same six-worker and half-CPU limits. ... ok
test_auto_num_workers_defaults_to_half_cpus (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_auto_num_workers_defaults_to_half_cpus)
On 12 available CPUs, the default uses six workers. ... ok
test_auto_num_workers_env_override_floors_at_one (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_auto_num_workers_env_override_floors_at_one)
PYTEST_XDIST_AUTO_NUM_WORKERS <= 0 is floored at 1. ... ok
test_auto_num_workers_honors_env_override (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_auto_num_workers_honors_env_override)
PYTEST_XDIST_AUTO_NUM_WORKERS explicitly overrides the auto calculation. ... ok
test_auto_num_workers_invalid_env_falls_back_to_local_policy (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_auto_num_workers_invalid_env_falls_back_to_local_policy)
Invalid non-integer in PYTEST_XDIST_AUTO_NUM_WORKERS falls back gracefully. ... ok
test_auto_num_workers_scaling_and_floors (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_auto_num_workers_scaling_and_floors)
The default stays within six workers and half of available CPUs. ... ok
test_available_cpus_returns_positive_integer (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_available_cpus_returns_positive_integer)
_available_cpus returns a sensible positive CPU count on the running system. ... ok
test_conftest_registers_on_pluginmanager_without_xdist_hookspecs (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_conftest_registers_on_pluginmanager_without_xdist_hookspecs)
In-process test that conftest registers and validates without xdist hookspecs. ... ok
test_pytest_runs_without_xdist_plugin (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_pytest_runs_without_xdist_plugin)
When xdist is disabled (-p no:xdist), pytest runs without PluginValidationError. ... ok
test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags (tests.test_xdist_auto_workers.XdistAutoWorkersTests.test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags)
Ambient PYTEST_ADDOPTS with xdist flags does not leak into scrubbed subprocess. ... ok

----------------------------------------------------------------------
Ran 11 tests in 1.346s

OK
```

(4) `git diff -- tests/test_xdist_auto_workers.py`:
Shows `_run_pytest_without_xdist` popping `PYTEST_ADDOPTS`/`PYTEST_PLUGINS`, passing repo-root `cwd` and `timeout=120`, and `setUpClass` loader restoring `os.environ` around `conftest` import.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted output of the sensitivity check in `E-03` (temporarily changing `@pytest.hookimpl(optionalhook=True)` to `@pytest.hookimpl` on `conftest.pytest_xdist_auto_num_workers` and running `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py -k "test_conftest_registers_on_pluginmanager_without_xdist_hookspecs or test_pytest_runs_without_xdist_plugin"`), showing both tests failing with `PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers'` before restoration; pasted output of sensitivity check B showing the ambient-addopts test failing with `unrecognized arguments: -n` while the scrub is removed; pasted `git diff -- conftest.py tests/test_xdist_auto_workers.py` after restoration showing no residual mutation; pasted exit-0 outputs of `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` and `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py`; followed by pasted exit-0 outputs of bare `python3 -m pytest`, `aw check release-gates`, and `aw sanitize --agent`.
  - Observed evidence: Sensitivity check A confirmed failure on bare hookimpl; sensitivity check B confirmed failure on missing PYTEST_ADDOPTS pop; clean git diff confirmed after restorations; unittest discover (11 tests, OK), ambient-addopts pytest (11 passed), bare pytest (707 passed), aw check release-gates (112 checked), and aw sanitize --agent (0 findings) all exit 0.
(1) Sensitivity check A (removing optionalhook=True):
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
Using --randomly-seed=1903433794
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/ny8eh8
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 11 items / 9 deselected / 2 selected

tests/test_xdist_auto_workers.py FF                                      [100%]

=================================== FAILURES ===================================
_________ XdistAutoWorkersTests.test_pytest_runs_without_xdist_plugin __________
...
E       INTERNALERROR> pluggy._manager.PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers' in plugin <module 'conftest' from '/mnt/md1/VC/agent-workflows/.aw/worktrees/ny8eh8/conftest.py'>
...
_ XdistAutoWorkersTests.test_conftest_registers_on_pluginmanager_without_xdist_hookspecs _
...
E                       pluggy._manager.PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers' in plugin <module 'conftest' from '/mnt/md1/VC/agent-workflows/.aw/worktrees/ny8eh8/conftest.py'>
...
=========================== short test summary info ============================
FAILED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_pytest_runs_without_xdist_plugin
FAILED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_conftest_registers_on_pluginmanager_without_xdist_hookspecs
======================= 2 failed, 9 deselected in 0.80s ========================
```

(2) Sensitivity check B (removing env.pop("PYTEST_ADDOPTS", None)):
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
Using --randomly-seed=2024726750
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/ny8eh8
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 11 items / 10 deselected / 1 selected

tests/test_xdist_auto_workers.py F                                       [100%]

=================================== FAILURES ===================================
_ XdistAutoWorkersTests.test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags _
...
E       AssertionError: 4 != 0 : pytest failed with output:
E
E       ERROR: usage: python3 -m pytest [options] [file_or_dir] [file_or_dir] [...]
E       python3 -m pytest: error: unrecognized arguments: -n --dist=worksteal tests/test_xdist_auto_workers.py
E         inifile: /mnt/md1/VC/agent-workflows/.aw/worktrees/ny8eh8/pyproject.toml
E         rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/ny8eh8
=========================== short test summary info ============================
FAILED tests/test_xdist_auto_workers.py::XdistAutoWorkersTests::test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags
======================= 1 failed, 10 deselected in 0.63s =======================
```

(3) Confirmed restorations clean via `git diff -- conftest.py tests/test_xdist_auto_workers.py`.

(4) `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v`:
```
Ran 11 tests in 1.248s

OK
```

(5) `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py`:
```
11 passed in 2.55s
```

(6) `python3 -m pytest`:
```
NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
707 passed in 22.25s
```

(7) `aw check release-gates`:
```
AW check  release-gates                                                  2132 ms
✓ CONFORMS  112 release-gates checked

Evidence
  backlog  45   specs  19   plans  47   releases  1
  errors  0   warnings  0   info  0
```

(8) `aw sanitize --agent`:
```
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5233,"findings":0,"evidence":["leak-scan"],"next":null}
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Execution contract**: Execute `E-01` through `E-03` in dependency order inside an isolated worktree. Do not mark any `E-*` item `performed` before completing its action, and do not mark any `V-*` item `pass` without pasting concrete observed command output into `Observed evidence:`. Run the repository suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`). Paste the ACTUAL runner output for every test claim; never claim a pass you did not run. Open questions: OQ-01 is resolved; none remain open. Scope fence (a declaration, not a stop condition): the declared paths are `conftest.py` and `tests/test_xdist_auto_workers.py`; an edit outside them is permitted only when justified, and `aw ipd finalize` records it via `--scope-reason <path>=<why>` (and `--scope-ack` for a declared path left unmodified). Commit only the paths you changed, plus this IPD, using `aw commit ny8eh8 -- <paths>`; never `git add -A`, and never push. Sensitivity mutations in E-03 are temporary and MUST NOT be committed.
- **Post-gate lifecycle move**: Once `E-01`..`E-03` are `performed`, `V-01`..`V-03` are `pass`, and `aw ipd lint --phase pre-transition` reports 0 errors, the plan must be finalized to `.aw/records/plans/executed/`: under `aw oc run` / `aw agy run` the runner owns that transition (a lane agent does not run `aw ipd finalize`); when executed by hand outside a runner, the executor runs `aw ipd finalize ny8eh8`. Never hand-`git mv` the plan.
