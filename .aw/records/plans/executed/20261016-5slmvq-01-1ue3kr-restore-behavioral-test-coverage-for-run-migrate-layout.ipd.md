# IPD: Restore behavioral test coverage for _run_migrate_layout

- Date: 2026-10-16
- Kind: child
- Concern: The production property PROP-01 "`aw migrate-layout` (`cli._run_migrate_layout`) runs the guided wizard, honors the confirm gate, resolves `--config` keys under CLI-flag precedence, and fails closed when non-interactive and unconfirmed" survives a `return-none` mutation of `cli._run_migrate_layout` (0 failing tests) since commit 19313eed deleted `tests/test_layout_migration.py` and `tests/test_awmigrename.py` (findings `hpjj44`).
- Scope: Add one new behavioral test module that drives `cli.main(["migrate-layout", ...])` in temporary git repos seeded with a legacy `.agents/` tree, asserting on exit codes and on-disk side effects; prove with an in-memory return-none mutant that the module kills the measured mutation. No production code changes.
- Scope-Paths: tests/test_migrate_layout_cli.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 5slmvq
- Set: 5slmvq
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 1ue3kr

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 1ue3kr verified (set 5slmvq, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 PR-002 PR-003 PR-004 PR-005 PR-006
- 2026-10-16 to-review (opencode): authored review-ready plan graduating backlog 5slmvq.
- 2026-10-16 draft (opencode): created.

## Goal

Restore behavioral regression coverage for `agent_workflows.cli._run_migrate_layout` so that a mutation making it return `None` (or dropping its confirm gate, config parsing, or flag precedence) turns the suite red. Coverage drives the real CLI entry point and asserts on exit codes and the resulting filesystem.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Wizard and confirm gate

- [x] E-01 Create `tests/test_migrate_layout_cli.py` with a `unittest.TestCase` fixture whose `setUp` makes a temp git repo with `tests.support.init_repo` (which scrubs inherited `GIT_DIR`/`GIT_INDEX_FILE` etc. via `clean_git_env` and sets local `user.email`/`user.name`/`commit.gpgsign false`, so a test run from inside a hook or lane cannot write to the outer repository), points `AW_HOME` at a temp dir, seeds `.agents/workflows/index.md`, `.agents/plans/pending/p.md`, `.agents/README.md`, commits them (`git add`/`git commit` run with `env=tests.support.clean_git_env()`), and `chdir`s into the repo; `tearDown` restores cwd and `AW_HOME` and removes the temp dir. Add tests: (a) `mock.patch("sys.stdin", io.StringIO("1\n1\ny\n"))` then `cli.main(["migrate-layout"])` returns 0, `.aw/system/workflows/index.md` and `.aw/records/plans/pending/p.md` exist and `.agents/workflows/index.md` is gone; (b) the same with explicit `wizard` action returns 0 and migrates; (c) answers `"1\n1\nn\n"` return 1 and `.aw/` does not exist while all three seeded `.agents/` files still exist with their seeded content.
  - Depends on: none
  - Expected outcome: Three wizard tests pass against current code.
  - Execution state: performed

### Task group 2: Config file and flag precedence

- [x] E-02 In the same module add: (a) a `--config` JSON `{"target_backend": "companion", "leftovers": "keep", "confirm": true}` run returns 0, `.aw/config/config.json` has `records_backend == "companion"`, `.aw/state/runtime/transactions/migration_transaction.json` records `leftover_disposition.disposition == "keep"`, and `.agents/README.md` still exists; (b) the same config plus `--target-backend repository --leftovers remove` returns 0, `records_backend == "repository"`, the transaction disposition is `"remove"`, and `.agents/README.md` is gone (CLI overrides config for BOTH keys); (c) a missing `--config` path returns 1, and a config file containing `{not valid json` returns 1, each with `.aw/` absent.
  - Depends on: E-01
  - Expected outcome: Config/precedence tests pass against current code.
  - Execution state: performed

### Task group 3: Non-interactive gate and preview path

- [x] E-03 In the same module add: (a) with `mock.patch("sys.stdin.isatty", return_value=False)` and no confirmation flag, `cli.main(["migrate-layout"])` returns 1 and `.aw/` is absent; (b) `cli.main(["migrate-layout", "--yes"])` returns 0 and `.aw/state/runtime/transactions/migration_transaction.json` records `leftover_disposition.disposition == "defer"` with `.agents/README.md` still present (default never deletes); (c) `cli.main(["migrate-layout", "plan", "--output", "o.json"])` returns 0, writes `o.json` containing `migration_map`, and creates no `.aw/`.
  - Depends on: E-02
  - Expected outcome: Non-interactive and preview tests pass against current code.
  - Execution state: performed

### Task group 4: Prove the coverage is load-bearing

- [x] E-04 Run an in-memory return-none mutation probe with no source edit: write a pytest plugin in an UNTRACKED scratch directory under the gitignored `.aw/state/` (never committed) that rebinds `agent_workflows.cli._run_migrate_layout` to a function returning `None` at import. Run `PYTHONPATH=<scratch>:. python3 -m pytest -o addopts="" -q -n0 -p <plugin> tests/test_migrate_layout_cli.py` and confirm failures. Rebinding the module attribute reaches the code because `cli.main` dispatches through the global name (`if args.command == "migrate-layout": return _run_migrate_layout(args, term)`). Add a second plugin that wraps the real function but forces the wizard confirm answer to `y` (patch `builtins.input` inside the wrapper to return `"y"` for the prompt beginning `Confirm and execute`) and confirm the decline test from E-01(c) fails. The wrapper must restore `builtins.input` in a `finally`. Pass `-p no:cacheprovider` so the probe writes no `.pytest_cache`. Delete the scratch plugins afterwards. (Mechanism demonstrated at review on 2026-10-16 with a two-test scratch module: unmutated `2 passed`; return-none plugin `2 failed`; confirm-bypass plugin `1 failed, 1 passed` with only the decline test failing.)
  - Depends on: E-03
  - Expected outcome: Under the return-none mutant every test that asserts a 0 or 1 exit code fails (that is every test in the module, since `None` equals neither); under the confirm-bypass mutant the wizard-decline test fails; unmutated code passes.
  - Execution state: performed

### Task group 5: Regression and commit

- [x] E-05 Run the module explicitly (`python3 -m pytest -o addopts="" -v tests/test_migrate_layout_cli.py`), then the fast suite bare (`python3 -m pytest`), and commit only the new module via `aw commit 1ue3kr -- tests/test_migrate_layout_cli.py`.
  - Depends on: E-04
  - Expected outcome: Module green, fast suite green, one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Tests must exercise behavior, not code structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16): no `inspect`/`ast`/regex reads of production source; drive `cli.main` and assert on exit codes and filesystem side effects.
- The routine gate runs bare: `python3 -m pytest` (pyproject `addopts` = `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`); `testpaths` is a fixed core list, so a new module outside it must be run explicitly. `tests/test_cli.py` is module-marked `pytestmark = pytest.mark.slow`.
- Tests that `chdir` and mutate `AW_HOME` are safe under xdist because each worker is a separate process; restore both in `tearDown`.
- `cli._run_migrate_layout` resolves repo from `os.getcwd()`, so tests must `chdir` into the temp repo.
- The wizard path is taken when `_term_mod.is_interactive()` is true OR `isinstance(sys.stdin, io.StringIO)` (`cli._run_migrate_layout`, "Default Wizard flow"), which is why patching `sys.stdin` with a plain `io.StringIO` drives it.
- Commits go through `aw commit <plan> -- <paths>`.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | `cli._run_migrate_layout` (277 exclusive lines) has its exclusive coverage only in deleted files `tests/test_layout_migration.py` (198 lines, class `MigrateLayoutWizardTests` among others) and `tests/test_awmigrename.py` (79 lines). | `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`, row for `agent_workflows/cli.py::_run_migrate_layout`; backlog `5slmvq`. |
| F2 | A return-none mutant survives the current suite (0 failing) and the control is killed by 11 tests in `tests.test_layout_migration.MigrateLayoutWizardTests`. | Backlog `5slmvq` body ("Survivor verdict: survived (0 failing)"). |
| F3 | Surviving tests `tests/test_cli.py::Order16MigrateLayoutCliTests` (non-interactive gate, `--yes`) and `tests/test_awphysical_tools.py` (wizard decline) exist but are `slow`-marked or did not kill the mutant per the audit; they are not modified here. | `pytestmark = pytest.mark.slow` in `tests/test_cli.py`; F2. |
| F4 | Every behavior targeted by E-01..E-03 was verified against current code during authoring with a scratch probe under `.aw/state/` (deleted afterwards). | Probe output: `RES accept 0 True True`, `RES decline 1 False`, `RES cfg 0 companion`, `RES override 0 repository`, `RES yes 0 {'disposition': 'defer', 'leftovers': ['.agents/README.md'], 'preserved': ['.agents/README.md'], 'removed': [], 'stale_tool_litter': []}`, `RES missingcfg 1`, `RES plan 0 False True`. |
| F5 | The deleted `MigrateLayoutWizardTests` fixture (temp git repo, seeded `.agents/` tree, `AW_HOME`, `chdir`) still works with current code, so its shape is reused. | `git show 19313eed7^:tests/test_layout_migration.py`, class `MigrateLayoutWizardTests`; F4. |

## Proposed changes (ordered, validatable)

1. Add `tests/test_migrate_layout_cli.py` with wizard/confirm-gate tests (E-01).
2. Add config and precedence tests (E-02).
3. Add non-interactive gate and preview tests (E-03).
4. Demonstrate mutation kill (E-04), then regression and commit (E-05).

## Deferred / out of scope (with reason)

- Restoring the non-CLI parts of the deleted files (`MigrationManager` move/rollback/cleanup, leftover disposition internals, stale-litter predicate, grammar facet helpers): separate properties tracked by other audit rows; backlog `5slmvq` names only `_run_migrate_layout`.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- The candidate test names in the backlog that exercise `MigrationManager` directly (`test_apply_moves_not_copies`, `test_cleanup_preserves_recreated_dir_content`, `test_cleanup_removes_manifest_only_file`, `test_apply_facet_transform`, `test_agents_readme_disposition_per_leftover_mode`): they do not reach `_run_migrate_layout` as an entry point except incidentally; the CLI-level wizard tests in the control set are the ones that killed the mutant (F2).
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- `status`/`resume`/`rollback`/`cleanup`/`inventory` sub-action dispatch: thin wrappers over `MigrationManager`; adding them is optional and not required to kill the measured mutant.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Adding the new module to `pyproject.toml` `testpaths`: changes the routine-gate composition, a maintainer decision outside this backlog item. The guard is still load-bearing without it: CI's `Run self-tests (parallel)` step in `.github/workflows/tests.yml` runs `python -m pytest tests/ -n auto -rfEs`, which collects every unmarked module under `tests/`, so the new module must NOT carry a `slow` or `livecorpus` mark.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none; the backlog asks for behavioral coverage of `_run_migrate_layout`, which E-01..E-03 provide through the real CLI entry point, and E-04 proves the coverage kills the return-none mutant the audit measured.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_migrate_layout_cli.py` passes (E-01, E-02, E-03).
- The return-none and confirm-bypass mutant plugins (E-04) each make the module fail.
- Bare `python3 -m pytest` summary shows no failures (E-05).

## Spec / documentation sync

N/A: test-only change; no spec or user-facing documentation describes this test file, and no behavior changes.

## Open questions

### OQ-01: Should the restored tests recreate `tests/test_layout_migration.py`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. A new, narrowly named module keeps scope to this backlog item and avoids implying the rest of the deleted file was restored (same choice as executed plan `df486j` for backlog `mv18lz`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted `python3 -m pytest -o addopts="" -v tests/test_migrate_layout_cli.py` output showing the wizard-accept, explicit-`wizard`, and wizard-decline tests PASSED, plus the test source lines asserting exit code 0/1 and the presence/absence of `.aw/system/workflows/index.md`, `.aw/records/plans/pending/p.md`, and `.agents/workflows/index.md`.
  - Observed evidence:
```
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_wizard_action_explicit PASSED [ 11%]
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_interactive_wizard_decline_makes_no_mutations PASSED [ 22%]
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_interactive_wizard_accept_runs_migration_after_confirm PASSED [ 33%]
```
Source assertions:
```python
    def test_interactive_wizard_accept_runs_migration_after_confirm(self) -> None:
        with mock.patch("sys.stdin", io.StringIO("1\n1\ny\n")):
            code = cli.main(["migrate-layout"])
        self.assertEqual(code, 0)
        self.assertTrue((self.repo / ".aw/system/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".aw/records/plans/pending/p.md").is_file())
        self.assertFalse((self.repo / ".agents/workflows/index.md").exists())

    def test_wizard_action_explicit(self) -> None:
        with mock.patch("sys.stdin", io.StringIO("1\n1\ny\n")):
            code = cli.main(["migrate-layout", "wizard"])
        self.assertEqual(code, 0)
        self.assertTrue((self.repo / ".aw/system/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".aw/records/plans/pending/p.md").is_file())
        self.assertFalse((self.repo / ".agents/workflows/index.md").exists())

    def test_interactive_wizard_decline_makes_no_mutations(self) -> None:
        with mock.patch("sys.stdin", io.StringIO("1\n1\nn\n")):
            code = cli.main(["migrate-layout"])
        self.assertEqual(code, 1)
        self.assertFalse((self.repo / ".aw").exists())
        self.assertTrue((self.repo / ".agents/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".agents/plans/pending/p.md").is_file())
        self.assertTrue((self.repo / ".agents/README.md").is_file())
        self.assertEqual(
            (self.repo / ".agents/workflows/index.md").read_text(encoding="utf-8"),
            "# w\n",
        )
        self.assertEqual(
            (self.repo / ".agents/plans/pending/p.md").read_text(encoding="utf-8"),
            "# p\n",
        )
        self.assertEqual(
            (self.repo / ".agents/README.md").read_text(encoding="utf-8"),
            "# agents readme\n",
        )
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted runner output showing the config, CLI-override, missing-config and invalid-JSON tests PASSED, plus the assertion lines reading `records_backend` from `.aw/config/config.json` (`companion` vs `repository`) and the transaction `leftover_disposition.disposition` (`keep` vs `remove`) with the `.agents/README.md` presence/absence assertions.
  - Observed evidence:
```
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_config_file_noninteractive PASSED [ 55%]
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_missing_and_invalid_config_files PASSED [ 77%]
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_cli_flags_override_config_file PASSED [ 88%]
```
Source assertions:
```python
    def test_config_file_noninteractive(self) -> None:
...
        code = cli.main(["migrate-layout", "--config", str(cfg_file)])
        self.assertEqual(code, 0)
        pol_file = self.repo / ".aw/config/config.json"
        self.assertTrue(pol_file.is_file())
        pol_data = json.loads(pol_file.read_text(encoding="utf-8"))
        self.assertEqual(pol_data.get("records_backend"), "companion")
        tx_path = (
            self.repo / ".aw/state/runtime/transactions/migration_transaction.json"
        )
        self.assertTrue(tx_path.is_file())
        tx_data = json.loads(tx_path.read_text(encoding="utf-8"))
        self.assertEqual(
            tx_data.get("leftover_disposition", {}).get("disposition"), "keep"
        )
        self.assertTrue((self.repo / ".agents/README.md").is_file())

    def test_cli_flags_override_config_file(self) -> None:
...
        self.assertEqual(code, 0)
        pol_file = self.repo / ".aw/config/config.json"
        self.assertTrue(pol_file.is_file())
        pol_data = json.loads(pol_file.read_text(encoding="utf-8"))
        self.assertEqual(pol_data.get("records_backend"), "repository")
        tx_path = (
            self.repo / ".aw/state/runtime/transactions/migration_transaction.json"
        )
        self.assertTrue(tx_path.is_file())
        tx_data = json.loads(tx_path.read_text(encoding="utf-8"))
        self.assertEqual(
            tx_data.get("leftover_disposition", {}).get("disposition"), "remove"
        )
        self.assertFalse((self.repo / ".agents/README.md").exists())

    def test_missing_and_invalid_config_files(self) -> None:
        code = cli.main(
            ["migrate-layout", "--config", str(self.repo / "nonexistent.json")]
        )
        self.assertEqual(code, 1)
        self.assertFalse((self.repo / ".aw").exists())

        bad_cfg = self.repo / "bad.json"
        bad_cfg.write_text("{not valid json", encoding="utf-8")
        code2 = cli.main(["migrate-layout", "--config", str(bad_cfg)])
        self.assertEqual(code2, 1)
        self.assertFalse((self.repo / ".aw").exists())
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted runner output showing the non-interactive fail-closed, `--yes` defer, and `plan --output` tests PASSED, plus the assertion lines on `migration_transaction.json` disposition `defer`, `.agents/README.md` still present, and `.aw/` absent after `plan`.
  - Observed evidence:
```
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_yes_without_leftovers_remove_does_not_delete_leftovers PASSED [ 44%]
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_underspecified_noninteractive_fails_closed PASSED [ 66%]
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_plan_preview_writes_output_and_creates_no_aw PASSED [100%]
```
Source assertions:
```python
    def test_underspecified_noninteractive_fails_closed(self) -> None:
        with mock.patch("sys.stdin.isatty", return_value=False):
            code = cli.main(["migrate-layout"])
        self.assertEqual(code, 1)
        self.assertFalse((self.repo / ".aw").exists())

    def test_yes_without_leftovers_remove_does_not_delete_leftovers(self) -> None:
        code = cli.main(["migrate-layout", "--yes"])
        self.assertEqual(code, 0)
        tx_path = (
            self.repo / ".aw/state/runtime/transactions/migration_transaction.json"
        )
        self.assertTrue(tx_path.is_file())
        tx_data = json.loads(tx_path.read_text(encoding="utf-8"))
        self.assertEqual(
            tx_data.get("leftover_disposition", {}).get("disposition"), "defer"
        )
        self.assertTrue((self.repo / ".agents/README.md").is_file())

    def test_plan_preview_writes_output_and_creates_no_aw(self) -> None:
        out_path = self.repo / "o.json"
        code = cli.main(["migrate-layout", "plan", "--output", str(out_path)])
        self.assertEqual(code, 0)
        self.assertTrue(out_path.is_file())
        out_data = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertIn("migration_map", out_data)
        self.assertFalse((self.repo / ".aw").exists())
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted output of the unmutated run and both mutant runs (`-p <plugin>`) with their summary lines: return-none shows every test failing (or names any that survive with the reason); confirm-bypass shows the wizard-decline test failing. Plus the plugin source pasted, and `git status --short` showing no scratch plugin is tracked or staged.
  - Observed evidence: Unmutated baseline passed 9/9; return-none mutant failed 9/9; confirm-bypass mutant failed decline test (1 failed, 8 passed); scratch plugins deleted.
    Unmutated baseline run:
```
$ python3 -m pytest -o addopts="" -q -n0 -p no:cacheprovider tests/test_migrate_layout_cli.py
.........                                                                [100%]
9 passed in 1.84s
```
    Return-none mutant run (kills all 9 tests):
```
$ PYTHONPATH=.aw/state/scratch_mutants:. python3 -m pytest -o addopts="" -q -n0 -p return_none_plugin -p no:cacheprovider tests/test_migrate_layout_cli.py
FFFFFFFFF                                                                [100%]
=================================== FAILURES ===================================
...
9 failed in 0.95s
```
    Confirm-bypass mutant run (kills decline test):
```
$ PYTHONPATH=.aw/state/scratch_mutants:. python3 -m pytest -o addopts="" -q -n0 -p confirm_bypass_plugin -p no:cacheprovider tests/test_migrate_layout_cli.py
..F......                                                                [100%]
=================================== FAILURES ===================================
FAILED tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_interactive_wizard_decline_makes_no_mutations
1 failed, 8 passed in 1.48s
```
    Plugin source `return_none_plugin.py`:
```python
import agent_workflows.cli

def _mutant(*args, **kwargs):
    return None

agent_workflows.cli._run_migrate_layout = _mutant
```
    Plugin source `confirm_bypass_plugin.py`:
```python
import builtins
import agent_workflows.cli

_real_run_migrate_layout = agent_workflows.cli._run_migrate_layout

def _confirm_bypass_wrapper(args, term):
    orig_input = builtins.input

    def _fake_input(prompt=""):
        if prompt.startswith("Confirm and execute"):
            return "y"
        return orig_input(prompt)

    builtins.input = _fake_input
    try:
        return _real_run_migrate_layout(args, term)
    finally:
        builtins.input = orig_input

agent_workflows.cli._run_migrate_layout = _confirm_bypass_wrapper
```
    Git status:
```
$ git status --short
# clean (scratch plugins deleted after run)
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted final summary lines of the explicit module run and of bare `python3 -m pytest` (`N passed`, no failures), `python3 -m pytest -o addopts="" --collect-only -q -m 'not slow and not livecorpus' tests/test_migrate_layout_cli.py` showing the module is collected by the CI marker filter, plus `git show --stat HEAD` showing only `tests/test_migrate_layout_cli.py` in the commit.
  - Observed evidence: Module explicit run passed 9/9; bare fast test suite passed 707/707; CI marker collection verified (9 collected); git show confirms only tests/test_migrate_layout_cli.py in commit.
    Explicit module run:
```
============================== 9 passed in 2.11s ===============================
```
    Bare fast test suite run:
```
NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
707 passed in 25.78s
```
    CI marker collection check:
```
$ python3 -m pytest -o addopts="" --collect-only -q -m 'not slow and not livecorpus' tests/test_migrate_layout_cli.py
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_underspecified_noninteractive_fails_closed
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_interactive_wizard_decline_makes_no_mutations
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_plan_preview_writes_output_and_creates_no_aw
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_cli_flags_override_config_file
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_config_file_noninteractive
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_interactive_wizard_accept_runs_migration_after_confirm
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_missing_and_invalid_config_files
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_yes_without_leftovers_remove_does_not_delete_leftovers
tests/test_migrate_layout_cli.py::MigrateLayoutCliTests::test_wizard_action_explicit

9 tests collected in 0.20s
```
Commit diffstat:
```
$ git show --stat HEAD
commit 9dd4e58cf8a367a9bb1afa1ae96fa0cd40425370 (HEAD -> aw/lane/1ue3kr)
Author: Gabriele Fariello <gabriele.fariello@gmail.com>
Date:   Fri Oct 16 18:19:25 2026 -0400

    work(1ue3kr): Restore behavioral test coverage for _run_migrate_layout

    AW-Run: run-20261016T221358Z-3466651
    AW-Item: 1ue3kr
    AW-Runner: aw agy run

 tests/test_migrate_layout_cli.py | 224 +++++++++++++++++++++++++++++++++++++++
 1 file changed, 224 insertions(+)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Execution contract:

- Open questions: OQ-01 is resolved; nothing blocks execution.
- Scope fence: `- Scope-Paths:` declares what this plan edits. An edit outside it is allowed when needed and must be justified at finalize (`--scope-reason`); do not stop over it. No production code changes.
- Honesty: you MUST paste the ACTUAL runner output in each `V-*`; never claim a pass you did not run.
- Commits: path-scoped via `aw commit 1ue3kr -- tests/test_migrate_layout_cli.py`; never `git add -A`, never commit the scratch mutation plugins, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize, so leave the plan in `pending/`. Executed by hand (`aw work begin 1ue3kr`), finish with `aw ipd finalize 1ue3kr --actor <agent/model> --message <summary> --apply` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms; never `git mv` the plan to `executed/`.
