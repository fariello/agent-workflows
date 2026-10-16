# IPD: Restore behavioral test coverage for _run_migrate_layout

- Date: 2026-10-16
- Kind: child
- Concern: The production property PROP-01 "`aw migrate-layout` (`cli._run_migrate_layout`) runs the guided wizard, honors the confirm gate, resolves `--config` keys under CLI-flag precedence, and fails closed when non-interactive and unconfirmed" survives a `return-none` mutation of `cli._run_migrate_layout` (0 failing tests) since commit 19313eed deleted `tests/test_layout_migration.py` and `tests/test_awmigrename.py` (findings `hpjj44`).
- Scope: Add one new behavioral test module that drives `cli.main(["migrate-layout", ...])` in temporary git repos seeded with a legacy `.agents/` tree, asserting on exit codes and on-disk side effects; prove with an in-memory return-none mutant that the module kills the measured mutation. No production code changes.
- Scope-Paths: tests/test_migrate_layout_cli.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 5slmvq
- Set: 5slmvq
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 1ue3kr

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready plan graduating backlog 5slmvq.

## Goal

Restore behavioral regression coverage for `agent_workflows.cli._run_migrate_layout` so that a mutation making it return `None` (or dropping its confirm gate, config parsing, or flag precedence) turns the suite red. Coverage drives the real CLI entry point and asserts on exit codes and the resulting filesystem.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Wizard and confirm gate

- [ ] E-01 Create `tests/test_migrate_layout_cli.py` with a `unittest.TestCase` fixture whose `setUp` makes a temp git repo (`git init`, local `user.email`/`user.name`, `commit.gpgsign false`), points `AW_HOME` at a temp dir, seeds `.agents/workflows/index.md`, `.agents/plans/pending/p.md`, `.agents/README.md`, commits them, and `chdir`s into the repo; `tearDown` restores cwd and `AW_HOME` and removes the temp dir. Add tests: (a) `mock.patch("sys.stdin", io.StringIO("1\n1\ny\n"))` then `cli.main(["migrate-layout"])` returns 0, `.aw/system/workflows/index.md` and `.aw/records/plans/pending/p.md` exist and `.agents/workflows/index.md` is gone; (b) the same with explicit `wizard` action returns 0 and migrates; (c) answers `"1\n1\nn\n"` return 1 and `.aw/` does not exist while both seeded `.agents/` files are unchanged.
  - Depends on: none
  - Expected outcome: Three wizard tests pass against current code.
  - Execution state: pending

### Task group 2: Config file and flag precedence

- [ ] E-02 In the same module add: (a) a `--config` JSON `{"target_backend": "companion", "leftovers": "keep", "confirm": true}` run returns 0 and `.aw/config/config.json` has `records_backend == "companion"`; (b) the same config plus `--target-backend repository --leftovers remove` returns 0 and `records_backend == "repository"` (CLI overrides config); (c) a missing `--config` path returns 1, and a config file containing `{not valid json` returns 1, each with `.aw/` absent.
  - Depends on: E-01
  - Expected outcome: Config/precedence tests pass against current code.
  - Execution state: pending

### Task group 3: Non-interactive gate and preview path

- [ ] E-03 In the same module add: (a) with `mock.patch("sys.stdin.isatty", return_value=False)` and no confirmation flag, `cli.main(["migrate-layout"])` returns 1 and `.aw/` is absent; (b) `cli.main(["migrate-layout", "--yes"])` returns 0 and `.aw/state/runtime/transactions/migration_transaction.json` records `leftover_disposition.disposition == "defer"` with `.agents/README.md` still present (default never deletes); (c) `cli.main(["migrate-layout", "plan", "--output", "o.json"])` returns 0, writes `o.json` containing `migration_map`, and creates no `.aw/`.
  - Depends on: E-02
  - Expected outcome: Non-interactive and preview tests pass against current code.
  - Execution state: pending

### Task group 4: Prove the coverage is load-bearing

- [ ] E-04 Run an in-memory return-none mutation probe with no source edit: write a pytest plugin in an UNTRACKED scratch directory under the gitignored `.aw/state/` (never committed) that rebinds `agent_workflows.cli._run_migrate_layout` to a function returning `None` at import. Run `PYTHONPATH=<scratch>:. python3 -m pytest -o addopts="" -q -n0 -p <plugin> tests/test_migrate_layout_cli.py` and confirm failures. Rebinding the module attribute reaches the code because `cli.main` dispatches through the global name (`if args.command == "migrate-layout": return _run_migrate_layout(args, term)`). Add a second plugin that wraps the real function but forces the wizard confirm answer to `y` (patch `builtins.input` inside the wrapper to return `"y"` for the prompt beginning `Confirm and execute`) and confirm the decline test from E-01(c) fails. Delete the scratch plugins afterwards.
  - Depends on: E-03
  - Expected outcome: The return-none mutant fails most tests in the module (at least the wizard-accept, config, override, and `--yes` tests); the confirm-bypass mutant fails the decline test; unmutated code passes.
  - Execution state: pending

### Task group 5: Regression and commit

- [ ] E-05 Run the module explicitly (`python3 -m pytest -o addopts="" -v tests/test_migrate_layout_cli.py`), then the fast suite bare (`python3 -m pytest`), and commit only the new module via `aw commit <plan> -- tests/test_migrate_layout_cli.py`.
  - Depends on: E-04
  - Expected outcome: Module green, fast suite green, one path-scoped commit.
  - Execution state: pending

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
- Adding the new module to `pyproject.toml` `testpaths`: changes the routine-gate composition, a maintainer decision outside this backlog item.
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

- [ ] V-01 validates E-01
  - Required evidence: Pasted `python3 -m pytest -o addopts="" -v tests/test_migrate_layout_cli.py` output showing the wizard-accept, explicit-`wizard`, and wizard-decline tests PASSED, plus the test source lines asserting exit code 0/1 and the presence/absence of `.aw/system/workflows/index.md`, `.aw/records/plans/pending/p.md`, and `.agents/workflows/index.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted runner output showing the config, CLI-override, missing-config and invalid-JSON tests PASSED, plus the assertion lines reading `records_backend` from `.aw/config/config.json` (`companion` vs `repository`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted runner output showing the non-interactive fail-closed, `--yes` defer, and `plan --output` tests PASSED, plus the assertion lines on `migration_transaction.json` disposition `defer`, `.agents/README.md` still present, and `.aw/` absent after `plan`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted output of both mutant runs (`-p <plugin>`) showing a nonzero failure count with the failing test names (return-none: at least wizard-accept, config, override, `--yes`; confirm-bypass: wizard-decline), plus `git status --short` showing no scratch plugin is tracked or staged.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted final summary lines of the explicit module run and of bare `python3 -m pytest` (`N passed`, no failures), plus `git show --stat HEAD` showing only `tests/test_migrate_layout_cli.py` in the commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). The executor follows the AGENTS.md execution contract: path-scoped `aw commit` of the declared Scope-Paths only, no push, actual runner output pasted as evidence. After every `V-*` item is `pass` and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle transition.
