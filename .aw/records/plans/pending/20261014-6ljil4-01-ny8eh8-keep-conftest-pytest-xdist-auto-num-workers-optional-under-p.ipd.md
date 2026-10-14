# IPD: Keep conftest pytest_xdist_auto_num_workers optional under -p no:xdist and harden serial xdist-disabled tests

- Date: 2026-10-14
- Kind: child
- Concern: Backlog item `6ljil4` (`Work-Kind: bug`, `Priority: low`, `Blocks-Release: next`) was filed during execution of IPD `sk2rbf` (`7c95d8bbd`, `2026-10-13`) when `conftest.pytest_xdist_auto_num_workers` (`def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:` in `conftest.py`, line 90) carried a bare `@pytest.hookimpl` decorator (introduced by `acd3d406f`). Because `pytest_xdist_auto_num_workers` is a hookspec declared by `xdist.newhooks` (loaded only when `xdist.plugin` is active), running `pytest` with `-p no:xdist` (such as `tools/replay_coverage_diff.py` serial runs or `python3 -m pytest -o addopts="" -p no:xdist`) caused `pluggy`'s `PytestPluginManager.check_pending()` to fail with `pluggy.PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers' in plugin <module 'conftest' ...>`. An un-planned commit (`497d35913`, "cihealth: scale -n auto to all cpus in CI and min 4 locally") subsequently changed `conftest.pytest_xdist_auto_num_workers` (`conftest.py`, line 89) to `@pytest.hookimpl(optionalhook=True)` and added `test_pytest_runs_without_xdist_plugin` (`tests/test_xdist_auto_workers.py`, line 116), but did not link or graduate `6ljil4` and left three defects in `conftest.py` and `tests/test_xdist_auto_workers.py`: (1) `test_pytest_runs_without_xdist_plugin` spawns `pytest -o addopts= -p no:xdist` without scrubbing `PYTEST_ADDOPTS` or `PYTEST_PLUGINS` from the subprocess environment, so any ambient `PYTEST_ADDOPTS` carrying `-n` or `--dist` (prepended before `_initini` in `_pytest.config.Config._preparse`) causes the test to fail with `exit 4` (`unrecognized arguments: -n`); (2) `tests/test_xdist_auto_workers.py` defines bare module-level `def test_*()` functions with no `unittest.TestCase` class, so `make test-serial` (`python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py`) discovers `0 tests` and exits `5` (`NO TESTS RAN`), violating the `pyproject.toml` `unittest.TestCase` contract; and (3) `tests/test_xdist_auto_workers.py` lacks an in-process `pytest.PytestPluginManager.check_pending()` test for `conftest` without `xdist` hookspecs (and `-p no:xdist.looponfail` coverage), while `conftest.py` lacks contract documentation explaining why `optionalhook=True` on `pytest_xdist_auto_num_workers` is load-bearing.
- Scope: Document the `optionalhook=True` contract on `conftest.pytest_xdist_auto_num_workers` (`conftest.py`, lines 1-20 and 89-96); convert `tests/test_xdist_auto_workers.py` to a `unittest.TestCase` class (`XdistAutoWorkersTests`) so both `pytest` and `unittest discover` (`make test-serial`) execute all tests; scrub `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` in the `-p no:xdist` subprocess helper and disable `xdist.looponfail` alongside `xdist`; and add behavioral tests verifying both ambient-`PYTEST_ADDOPTS` isolation and in-process `pytest.PytestPluginManager.check_pending()` validation of `conftest` without `xdist` hookspecs.
- Scope-Paths: conftest.py, tests/test_xdist_auto_workers.py
- Item-Dependencies: none
- Status: to-review
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
- 2026-10-14 to-review (aw set): Authored review-ready child IPD ny8eh8 from backlog 6ljil4

- 2026-10-14 draft (Antigravity): created.

## Goal

Ensure `conftest.pytest_xdist_auto_num_workers` remains an optional hook implementation (`@pytest.hookimpl(optionalhook=True)`) that validates cleanly when `xdist` hookspecs are absent (`-p no:xdist`), and harden `tests/test_xdist_auto_workers.py` so its `-p no:xdist` and worker-scaling checks are immune to ambient `PYTEST_ADDOPTS`/`PYTEST_PLUGINS`, exercise `PytestPluginManager.check_pending()` directly, and run under both `pytest` and `unittest discover` (`make test-serial`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Conftest optionalhook contract and xdist-disabled test hardening

- [ ] E-01 Update `conftest.py` around `conftest.pytest_xdist_auto_num_workers` (`@pytest.hookimpl(optionalhook=True)` / `def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:`, lines 89-96) and the module docstring (`"""Root pytest conftest: guarantee the suite ALWAYS runs in parallel (-n auto)`, lines 1-20) to document why `optionalhook=True` is load-bearing (backlog `6ljil4`: `pytest_xdist_auto_num_workers` is an `xdist.newhooks` hookspec registered only when `xdist.plugin` loads, so omitting `optionalhook=True` raises `pluggy.PluginValidationError` during `PytestPluginManager.check_pending()` whenever `pytest` is invoked with `-p no:xdist`, such as in `tools/replay_coverage_diff.py` serial runs or `-o addopts="" -p no:xdist`), and update the module docstring (`conftest.py`, line 6) to reflect the `pytest_xdist_auto_num_workers` worker-bounding policy rather than `one worker per CPU`.
  - Depends on: none
  - Expected outcome: `conftest.pytest_xdist_auto_num_workers` retains `@pytest.hookimpl(optionalhook=True)` with an explicit comment and docstring explaining the `-p no:xdist` `PluginValidationError` contract (`6ljil4`), and the module docstring accurately states the `-n auto` worker resolution policy.
  - Execution state: pending

- [ ] E-02 Refactor `tests/test_xdist_auto_workers.py` into a `unittest.TestCase` subclass (`class XdistAutoWorkersTests(unittest.TestCase):`) and harden its `-p no:xdist` coverage:
  - Wrap all existing worker-count and CPU-count tests (`test_auto_num_workers_defaults_to_half_cpus`, `test_auto_num_workers_scaling_and_floors`, `test_auto_num_workers_ci_mode`, `test_auto_num_workers_honors_env_override`, `test_auto_num_workers_env_override_floors_at_one`, `test_auto_num_workers_invalid_env_falls_back_to_local_policy`, `test_available_cpus_returns_positive_integer`, and `test_pytest_runs_without_xdist_plugin`) as methods on `XdistAutoWorkersTests(unittest.TestCase)` so both `python3 -m pytest` and `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py` discover and execute them.
  - Extract a helper `_run_pytest_without_xdist(self, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]` on `XdistAutoWorkersTests` that copies `os.environ` (plus any `env_overrides`), pops `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` so ambient xdist flags (`-n`, `--dist`) cannot leak ahead of `-o addopts=` in `_pytest.config.Config._preparse`, and runs `[sys.executable, "-m", "pytest", "-o", "addopts=", "-p", "no:xdist", "-p", "no:xdist.looponfail", "tests/test_xdist_auto_workers.py", "-k", "test_available_cpus_returns_positive_integer"]`.
  - Add `test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags(self) -> None`: sets `PYTEST_ADDOPTS="-n 2 --dist=worksteal"` in `os.environ` via `patch.dict` and asserts `_run_pytest_without_xdist()` exits `0` with neither `PluginValidationError` nor `unrecognized arguments` in `stdout`/`stderr`.
  - Add `test_conftest_registers_on_pluginmanager_without_xdist_hookspecs(self) -> None`: instantiates a fresh `pytest.PytestPluginManager()`, calls `pm.register(conftest)` and `pm.check_pending()`, and asserts that `check_pending()` succeeds without raising `pluggy.PluginValidationError` when `xdist.newhooks` is not registered, and that `pm.hasplugin("xdist")` is `False`.
  - Depends on: E-01
  - Expected outcome: `tests/test_xdist_auto_workers.py` executes 10 behavioral tests under both `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py` and `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v`, including when `PYTEST_ADDOPTS="-n 2"` is set in the outer environment.
  - Execution state: pending

- [ ] E-03 Perform sensitivity verification and full repository validation:
  - Sensitivity check: temporarily change `@pytest.hookimpl(optionalhook=True)` to `@pytest.hookimpl` on `conftest.pytest_xdist_auto_num_workers`, run `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py -k "test_conftest_registers_on_pluginmanager_without_xdist_hookspecs or test_pytest_runs_without_xdist_plugin"`, verify both tests fail with `PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers'`, and restore `@pytest.hookimpl(optionalhook=True)`.
  - Run `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` and `PYTEST_ADDOPTS="-n 2" python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py`.
  - Run the bare repository test suite (`python3 -m pytest`), `aw check release-gates`, and `aw sanitize --agent`.
  - Depends on: E-01, E-02
  - Expected outcome: The sensitivity check proves both the in-process `PytestPluginManager.check_pending()` test and the subprocess `-p no:xdist` test fail when `optionalhook=True` is removed; `unittest discover`, `PYTEST_ADDOPTS="-n 2"` pytest, bare `python3 -m pytest`, `aw check release-gates`, and `aw sanitize --agent` all exit `0`.
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
| F-04 | `pytest-xdist` registers two `pytest11` entry points (`xdist = xdist.plugin` and `xdist.looponfail = xdist.looponfail`). Registering `conftest` on a fresh `pytest.PytestPluginManager()` in-process and calling `check_pending()` directly tests the `optionalhook=True` contract without `xdist.newhooks` in <1ms, whereas `test_pytest_runs_without_xdist_plugin` only exercises the subprocess path and does not pass `-p no:xdist.looponfail`. | Measured at HEAD `7dc1b0e5f`: `importlib.metadata.distribution("pytest-xdist").entry_points` returns `[('xdist', 'xdist.plugin'), ('xdist.looponfail', 'xdist.looponfail')]`. |

## Proposed changes (ordered, validatable)

1. Document the `optionalhook=True` `-p no:xdist` requirement (`6ljil4`) on `conftest.pytest_xdist_auto_num_workers` (`conftest.py`, lines 89-96) and align the module docstring (`conftest.py`, lines 1-20) with the worker-bounding policy (`E-01`).
2. Convert `tests/test_xdist_auto_workers.py` to `XdistAutoWorkersTests(unittest.TestCase)`, scrub `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` in `_run_pytest_without_xdist` (passing `-p no:xdist -p no:xdist.looponfail`), and add `test_pytest_runs_without_xdist_when_ambient_pytest_addopts_has_xdist_flags` plus `test_conftest_registers_on_pluginmanager_without_xdist_hookspecs` (`E-02`).
3. Verify failure sensitivity under temporary removal of `optionalhook=True` on `conftest.pytest_xdist_auto_num_workers`, verify `unittest discover` and `PYTEST_ADDOPTS="-n 2"` execution, and run the bare full test suite, release-gates check, and leak sanitizer (`E-03`).

## Deferred / out of scope (with reason)

- Stripping `-n auto --dist=worksteal` from `pyproject.toml` `addopts` when `-p no:xdist` is passed without `-o addopts=""`: `pyproject.toml` (`addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`, line 213) and `AGENTS.md` (`python3 -m pytest -o addopts=""`, line 290) intentionally require `-n auto` on default runs and `-o addopts=""` on narrowed/serial runs (`tools/replay_coverage_diff.py` `_build_pytest_cmd`, line 141).
  - Carrier-Declined: By design per `conftest.py` module docstring and `AGENTS.md` repository development contract; no defect exists when `-o addopts=""` is used as documented.

## Scope check

- Over-scope: none.
- Under-scope: none. Both files involved in the `conftest.pytest_xdist_auto_num_workers` hook implementation and its tests (`conftest.py` and `tests/test_xdist_auto_workers.py`) are in `- Scope-Paths:`.

## Required tests / validation

- Targeted pytest run: `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py` (10 passed).
- Ambient `PYTEST_ADDOPTS` resilience run: `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py` (10 passed).
- Stdlib `unittest` discovery run (`make test-serial` compatibility): `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` (10 passed, exit `0`).
- Sensitivity check: temporarily change `@pytest.hookimpl(optionalhook=True)` to `@pytest.hookimpl` on `conftest.pytest_xdist_auto_num_workers`, confirm both `test_conftest_registers_on_pluginmanager_without_xdist_hookspecs` and `test_pytest_runs_without_xdist_plugin` fail with `PluginValidationError`, and restore `optionalhook=True`.
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
  - Required evidence: Pasted `git diff -- conftest.py` showing `@pytest.hookimpl(optionalhook=True)` on `conftest.pytest_xdist_auto_num_workers` together with the updated docstring and comment citing `6ljil4` and the updated module header docstring.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- tests/test_xdist_auto_workers.py` and pasted outputs of (1) `python3 -m pytest -o addopts="" -v tests/test_xdist_auto_workers.py` (reachable via `XdistAutoWorkersTests` created in `E-02`), (2) `PYTEST_ADDOPTS="-n 2 --dist=worksteal" python3 -m pytest -o addopts="" -v tests/test_xdist_auto_workers.py` (reachable via `XdistAutoWorkersTests._run_pytest_without_xdist` created in `E-02`), and (3) `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py -v` (reachable via `XdistAutoWorkersTests(unittest.TestCase)` created in `E-02`), all showing 10 tests passing and exit code `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of the sensitivity check in `E-03` (temporarily changing `@pytest.hookimpl(optionalhook=True)` to `@pytest.hookimpl` on `conftest.pytest_xdist_auto_num_workers` and running `python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py -k "test_conftest_registers_on_pluginmanager_without_xdist_hookspecs or test_pytest_runs_without_xdist_plugin"`), showing both tests failing with `PluginValidationError: unknown hook 'pytest_xdist_auto_num_workers'` before restoration; followed by pasted exit-0 outputs of bare `python3 -m pytest`, `aw check release-gates`, and `aw sanitize --agent`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Execution contract**: Execute `E-01` through `E-03` in dependency order inside an isolated worktree. Do not mark any `E-*` item `performed` before completing its action, and do not mark any `V-*` item `pass` without pasting concrete observed command output into `Observed evidence:`. Run the repository suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`). Commit only files listed in `- Scope-Paths:` plus this IPD using `aw commit ny8eh8 -- <paths>`.
- **Post-gate lifecycle move**: Once `E-01`..`E-03` are `performed`, `V-01`..`V-03` are `pass`, and `aw ipd lint --phase pre-transition` reports 0 errors, finalize the plan via `aw ipd finalize ny8eh8` (or under `aw oc run` / `aw agy run`, let the runner finalize and move the plan to `.aw/records/plans/executed/`).
