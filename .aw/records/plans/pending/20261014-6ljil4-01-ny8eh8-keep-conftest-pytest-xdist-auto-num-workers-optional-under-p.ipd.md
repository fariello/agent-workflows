# IPD: Keep conftest pytest_xdist_auto_num_workers optional under -p no:xdist and harden serial xdist-disabled tests

- Date: 2026-10-14
- Kind: child
- Concern: Backlog item `6ljil4` (`Work-Kind: bug`, `Priority: low`, `Blocks-Release: next`) was filed during execution of IPD `sk2rbf` (`7c95d8bbd`, `2026-10-13`) when `conftest.pytest_xdist_auto_num_workers` (`def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:` in `conftest.py`, line 90) carried a bare `@pytest.hookimpl` decorator (introduced by `acd3d406f`). Because `pytest_xdist_auto_num_workers` is a hookspec declared by `xdist.newhooks` (loaded only when `xdist.plugin` is active), running `pytest` with `-p no:xdist` (such as `tools/replay_coverage_diff.py` serial runs or `python3 -m pytest -o addopts="" -p no:xdist`) caused `pluggy`'s `PytestPluginManager.check_pending()` to fail with `pluggy.PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers' in plugin <module 'conftest' ...>`. An un-planned commit (`497d35913`, "cihealth: scale -n auto to all cpus in CI and min 4 locally") subsequently changed `conftest.pytest_xdist_auto_num_workers` (`conftest.py`, line 89) to `@pytest.hookimpl(optionalhook=True)` and added `test_pytest_runs_without_xdist_plugin` (`tests/test_xdist_auto_workers.py`, line 116), but did not link or graduate `6ljil4` and left three defects in `conftest.py` and `tests/test_xdist_auto_workers.py`: (1) `test_pytest_runs_without_xdist_plugin` spawns `pytest -o addopts= -p no:xdist` without scrubbing `PYTEST_ADDOPTS` or `PYTEST_PLUGINS` from the subprocess environment, so any ambient `PYTEST_ADDOPTS` carrying `-n` or `--dist` (prepended before `_initini` in `_pytest.config.Config._preparse`) causes the test to fail with `exit 4` (`unrecognized arguments: -n`); (2) `tests/test_xdist_auto_workers.py` defines bare module-level `def test_*()` functions with no `unittest.TestCase` class, so `make test-serial` (`python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py`) discovers `0 tests` and exits `5` (`NO TESTS RAN`), violating the `pyproject.toml` `unittest.TestCase` contract; and (3) `tests/test_xdist_auto_workers.py` lacks an in-process `pytest.PytestPluginManager.check_pending()` test for `conftest` without `xdist` hookspecs, while `conftest.py` lacks contract documentation explaining why `optionalhook=True` on `pytest_xdist_auto_num_workers` is load-bearing.
- Scope: Document the `optionalhook=True` contract on `conftest.pytest_xdist_auto_num_workers` (`conftest.py`, lines 1-20 and 89-96); convert `tests/test_xdist_auto_workers.py` to a `unittest.TestCase` class (`XdistAutoWorkersTests`) so both `pytest` and `unittest discover` (`make test-serial`) execute all tests; scrub `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` in the `-p no:xdist` subprocess helper (keeping the production `-p no:xdist` argv) and contain the import-time side effects of `import conftest` under `unittest`; and add behavioral tests verifying both ambient-`PYTEST_ADDOPTS` isolation and in-process `pytest.PytestPluginManager.check_pending()` validation of `conftest` without `xdist` hookspecs.
- Scope-Paths: conftest.py, tests/test_xdist_auto_workers.py
- Item-Dependencies: none
- Status: reviewed
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
- 2026-10-15 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-14 to-review (aw set): Authored review-ready child IPD ny8eh8 from backlog 6ljil4

- 2026-10-14 draft (Antigravity): created.

## Goal

Ensure `conftest.pytest_xdist_auto_num_workers` remains an optional hook implementation (`@pytest.hookimpl(optionalhook=True)`) that validates cleanly when `xdist` hookspecs are absent (`-p no:xdist`), and harden `tests/test_xdist_auto_workers.py` so its `-p no:xdist` and worker-scaling checks are immune to ambient `PYTEST_ADDOPTS`/`PYTEST_PLUGINS`, exercise `PytestPluginManager.check_pending()` directly, and run under both `pytest` and `unittest discover` (`make test-serial`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Conftest optionalhook contract and xdist-disabled test hardening

- [ ] E-01 Update `conftest.py` around `conftest.pytest_xdist_auto_num_workers` (`@pytest.hookimpl(optionalhook=True)` / `def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:`, lines 89-96) and the module docstring (`"""Root pytest conftest: guarantee the suite ALWAYS runs in parallel (-n auto)`, lines 1-20) to document why `optionalhook=True` is load-bearing (backlog `6ljil4`: `pytest_xdist_auto_num_workers` is an `xdist.newhooks` hookspec registered only when `xdist.plugin` loads, so omitting `optionalhook=True` raises `pluggy.PluginValidationError` during `PytestPluginManager.check_pending()` whenever `pytest` is invoked with `-p no:xdist`, such as in `tools/replay_coverage_diff.py` serial runs or `-o addopts="" -p no:xdist`), and update the module docstring (`conftest.py`, line 6) to reflect the `pytest_xdist_auto_num_workers` worker-bounding policy rather than `one worker per CPU`; and correct the coordinator-role comment (`conftest.py` line 158, `make test-serial` (`python3 -m unittest`) never loads this file`), which is false once a unittest module imports `conftest` (`F-06`), to say that `unittest` loads it only through an explicit import and that `tests/test_xdist_auto_workers.py` restores `os.environ` around that import. Documentation-only: do NOT change the hook's decorator, signature, return values, or any other `conftest.py` code (the worker-count tests in E-02 pin that behavior unchanged).
  - Depends on: none
  - Expected outcome: `conftest.pytest_xdist_auto_num_workers` retains `@pytest.hookimpl(optionalhook=True)` with an explicit comment and docstring explaining the `-p no:xdist` `PluginValidationError` contract (`6ljil4`), the module docstring accurately states the `-n auto` worker resolution policy, and `git diff -- conftest.py` touches only comment and docstring lines.
  - Execution state: pending

- [ ] E-02 Refactor `tests/test_xdist_auto_workers.py` into a `unittest.TestCase` subclass (`class XdistAutoWorkersTests(unittest.TestCase):`) and harden its `-p no:xdist` coverage:
  - Wrap all existing worker-count and CPU-count tests (`test_auto_num_workers_defaults_to_half_cpus`, `test_auto_num_workers_scaling_and_floors`, `test_auto_num_workers_ci_mode`, `test_auto_num_workers_honors_env_override`, `test_auto_num_workers_env_override_floors_at_one`, `test_auto_num_workers_invalid_env_falls_back_to_local_policy`, `test_available_cpus_returns_positive_integer`, and `test_pytest_runs_without_xdist_plugin`) as methods on `XdistAutoWorkersTests(unittest.TestCase)` so both `python3 -m pytest` and `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py` discover and execute them.
  - Extract a helper `_run_pytest_without_xdist(self) -> subprocess.CompletedProcess[str]` on `XdistAutoWorkersTests` that copies `os.environ`, pops `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` from the copy so ambient xdist flags (`-n`, `--dist`) cannot leak ahead of `-o addopts=` in `_pytest.config.Config._preparse`, and runs `[sys.executable, "-m", "pytest", "-o", "addopts=", "-p", "no:xdist", "tests/test_xdist_auto_workers.py", "-k", "test_available_cpus_returns_positive_integer"]` with `env=<the scrubbed copy>`, `cwd=os.path.dirname(os.path.abspath(conftest.__file__))` (the repository root, so the relative test path resolves regardless of the runner's working directory), `capture_output=True`, `text=True`, `check=False`, and `timeout=120` (so a hung child fails the test instead of hanging `make test-serial`, where the `conftest.py` hang guard does not run). The argv deliberately disables only `xdist`, matching the real serial invocation it protects (`tools/replay_coverage_diff.py` `_build_pytest_cmd`, `cmd.extend(["-p", "no:xdist"])` at line 169); do NOT add `-p no:xdist.looponfail`, which would make the test exercise a different invocation than production.
  - Add `test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags(self) -> None`: sets `PYTEST_ADDOPTS="-n 2 --dist=worksteal"` in `os.environ` via `patch.dict` and asserts `_run_pytest_without_xdist()` exits `0` with neither `PluginValidationError` nor `unrecognized arguments` in `stdout`/`stderr`.
  - Add `test_conftest_registers_on_pluginmanager_without_xdist_hookspecs(self) -> None`: instantiates a fresh `pytest.PytestPluginManager()`, asserts the precondition that `pm.hasplugin("xdist")` is `False` (so no `xdist.newhooks` hookspec is registered), calls `pm.register(conftest)` and `pm.check_pending()`, and asserts that `check_pending()` succeeds without raising `pluggy.PluginValidationError`. (Mechanism demonstrated at review, see `F-05`.)
  - Contain the `conftest` import (`F-06`): replace the module-level `import conftest` with a module-level loader used by `XdistAutoWorkersTests.setUpClass` that returns `sys.modules["conftest"]` when pytest has already loaded it, and otherwise (the `unittest discover` path) raises `unittest.SkipTest` if `importlib.util.find_spec("xdist") is None` (so `_ensure_xdist_then_reexec` can never `pip install` or `os.execv` the unittest process), then snapshots `dict(os.environ)`, imports `conftest`, and restores `os.environ` to the snapshot (`clear()` + `update()`), so the import cannot leak conftest's env scrub/sandbox into later unittest modules.
  - Keep every existing worker-count assertion and its input/expected pairs unchanged; this item only re-homes them as methods (use `self.assertEqual`/`self.assertTrue` or plain `assert`, either runs under both runners).
  - Depends on: E-01
  - Expected outcome: every test in `tests/test_xdist_auto_workers.py` is a method of `XdistAutoWorkersTests(unittest.TestCase)` and passes under both `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py` and `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` (exit `0`, with the unittest `Ran N tests` count equal to the pytest `N passed` count and N greater than zero), including when `PYTEST_ADDOPTS="-n 2 --dist=worksteal"` is set in the outer environment; the two new tests and the re-homed `test_pytest_runs_without_xdist_plugin` are among those run.
  - Execution state: pending

- [ ] E-03 Perform sensitivity verification and full repository validation:
  - Sensitivity check A (hook contract): temporarily change `@pytest.hookimpl(optionalhook=True)` to `@pytest.hookimpl` on `conftest.pytest_xdist_auto_num_workers`, run `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py -k "test_conftest_registers_on_pluginmanager_without_xdist_hookspecs or test_pytest_runs_without_xdist_plugin"`, verify both tests fail with `PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers'`, and restore `@pytest.hookimpl(optionalhook=True)`.
  - Sensitivity check B (env scrub): temporarily delete the `PYTEST_ADDOPTS` pop from `_run_pytest_without_xdist`, run `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py -k test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags`, verify it fails on the child's non-zero exit with `unrecognized arguments: -n` in the captured output, and restore the pop.
  - After both restorations, confirm with `git diff -- conftest.py tests/test_xdist_auto_workers.py` that no sensitivity mutation remains (only the E-01/E-02 edits).
  - Run `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` and `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py`.
  - Run the bare repository test suite (`python3 -m pytest`), `aw check release-gates`, and `aw sanitize --agent`.
  - Depends on: E-01, E-02
  - Expected outcome: Sensitivity check A proves both the in-process `PytestPluginManager.check_pending()` test and the subprocess `-p no:xdist` test fail when `optionalhook=True` is removed; sensitivity check B proves the ambient-`PYTEST_ADDOPTS` test fails when the scrub is removed; both mutations are reverted; `unittest discover`, ambient-`PYTEST_ADDOPTS` pytest, bare `python3 -m pytest`, `aw check release-gates`, and `aw sanitize --agent` all exit `0`.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: Pasted `git diff -- conftest.py` showing `@pytest.hookimpl(optionalhook=True)` on `conftest.pytest_xdist_auto_num_workers` unchanged, the updated docstring and comment citing `6ljil4`, the updated module header docstring, and the corrected `make test-serial` comment (former line 158), with every changed line a comment or docstring line (no executable code changed).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- tests/test_xdist_auto_workers.py` and pasted outputs of (1) `python3 -m pytest -o addopts="" -v tests/test_xdist_auto_workers.py` (reachable via `XdistAutoWorkersTests` created in `E-02`), (2) `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" -v tests/test_xdist_auto_workers.py` (reachable via `XdistAutoWorkersTests._run_pytest_without_xdist` created in `E-02`), and (3) `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` (reachable via `XdistAutoWorkersTests(unittest.TestCase)` created in `E-02`), all exit `0` with every test passing, where the `-v` listings name `test_pytest_runs_without_xdist_plugin`, `test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags`, and `test_conftest_registers_on_pluginmanager_without_xdist_hookspecs` as passed (names are pointers; the bar is the behavior) and the unittest `Ran N tests` equals the pytest `N passed` (N re-derived at execution, non-zero, no `skipped`); and (4) the diff shows `_run_pytest_without_xdist` popping `PYTEST_ADDOPTS`/`PYTEST_PLUGINS`, passing repo-root `cwd` and `timeout=120`, and the `setUpClass` loader restoring `os.environ` around the `conftest` import.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of the sensitivity check in `E-03` (temporarily changing `@pytest.hookimpl(optionalhook=True)` to `@pytest.hookimpl` on `conftest.pytest_xdist_auto_num_workers` and running `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py -k "test_conftest_registers_on_pluginmanager_without_xdist_hookspecs or test_pytest_runs_without_xdist_plugin"`), showing both tests failing with `PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers'` before restoration; pasted output of sensitivity check B showing the ambient-addopts test failing with `unrecognized arguments: -n` while the scrub is removed; pasted `git diff -- conftest.py tests/test_xdist_auto_workers.py` after restoration showing no residual mutation; pasted exit-0 outputs of `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` and `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py`; followed by pasted exit-0 outputs of bare `python3 -m pytest`, `aw check release-gates`, and `aw sanitize --agent`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Execution contract**: Execute `E-01` through `E-03` in dependency order inside an isolated worktree. Do not mark any `E-*` item `performed` before completing its action, and do not mark any `V-*` item `pass` without pasting concrete observed command output into `Observed evidence:`. Run the repository suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`). Paste the ACTUAL runner output for every test claim; never claim a pass you did not run. Open questions: OQ-01 is resolved; none remain open. Scope fence (a declaration, not a stop condition): the declared paths are `conftest.py` and `tests/test_xdist_auto_workers.py`; an edit outside them is permitted only when justified, and `aw ipd finalize` records it via `--scope-reason <path>=<why>` (and `--scope-ack` for a declared path left unmodified). Commit only the paths you changed, plus this IPD, using `aw commit ny8eh8 -- <paths>`; never `git add -A`, and never push. Sensitivity mutations in E-03 are temporary and MUST NOT be committed.
- **Post-gate lifecycle move**: Once `E-01`..`E-03` are `performed`, `V-01`..`V-03` are `pass`, and `aw ipd lint --phase pre-transition` reports 0 errors, the plan must be finalized to `.aw/records/plans/executed/`: under `aw oc run` / `aw agy run` the runner owns that transition (a lane agent does not run `aw ipd finalize`); when executed by hand outside a runner, the executor runs `aw ipd finalize ny8eh8`. Never hand-`git mv` the plan.
