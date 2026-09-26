# IPD: Make the upgrade rehearsal install with the checkout under test, not the editable-install checkout

- Date: 2026-09-26
- Kind: child
- Concern: A rehearsal launched from a lane worktree silently installs with the MAIN checkout's package. `default_aw_cmd` (the backlog text calls it `_installer_cmd`, which does not exist) returns `[sys.executable, "-m", "agent_workflows"]` whenever `agent_workflows/cli.py` sits beside the tool, and `run_install` runs that argv with `cwd=<sandbox>` and `env=sandbox_env(...)`, which copies `os.environ` and never sets `PYTHONPATH`. With `cwd` in a sandbox, `-m` resolves the package through `sys.path`, i.e. through the EDITABLE install's `.pth` file, which points at the main checkout. Measured at HEAD `f46b6775`: from `/tmp`, `python3 -c 'import agent_workflows'` imports `<main>/agent_workflows/__init__.py`; with `PYTHONPATH=<main>/.aw/worktrees/0i4fkt` it imports the worktree's copy. The backlog item records the consequence: a rehearsal of a fix in a worktree reported `[version-unchanged]` and a 1.2.1 stamp, and the result flipped on the import path alone. The tool's own docstring names rehearsing a different version as "the one mistake that would invalidate every result this tool produces", and the failure is silent.
- Scope: IN: in `agent_workflows/upgrade_rehearsal.py` (the post-`8ud1is` home of the harness): when the `-m` form is used, prepend the tool's own repo root to `PYTHONPATH` in the child environment `run_install` passes, leaving the argv unchanged; record `imported_from` (the `agent_workflows.__file__` a probe child with the SAME env and cwd imports) in each install result; add a `wrong-checkout` observation when `imported_from` is not under the tool's repo root, surfaced by `report`; behavioral tests driving a temp copied package that simulates a worktree. OUT: changing `default_aw_cmd`'s argv (the restored `CliTests.test_default_aw_cmd_prefers_the_checkout_under_test` pins `[sys.executable, "-m", "agent_workflows"]`); the PATH-`aw` fallback and an explicit `aw_cmd` (neither is the `-m` form; recording `imported_from` for them is also out, since a console script's import cannot be probed with `python -c`); `sandbox_env`'s isolation variables.
- Scope-Paths: agent_workflows/upgrade_rehearsal.py, tests/test_aw_upgrade_test.py
- Item-Dependencies: executed:8ud1is
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: bs1iek
- Blocks-Release: next
- Set: upgrehearse
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: btth0a

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog bs1iek. Re-measured at HEAD f46b6775: the editable install's .pth resolves agent_workflows to the main checkout from any cwd outside it, and PYTHONPATH pointing at the worktree root overrides it. Corrected the backlog's function name (_installer_cmd does not exist; the resolver is default_aw_cmd, run by run_install). Independent of Order 2 (sbo3hl); ordered after 8ud1is because it edits the post-move module.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A rehearsal always installs with the package that sits beside the tool that launched it, and every install result says which package file the child actually imported, so a mismatch is visible in the report instead of invisible.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 REPRODUCE THE WRONG IMPORT. Confirm `8ud1is` is executed (`agent_workflows/upgrade_rehearsal.py` exists; the shim re-exports). Determine the tool's repo root as the moved module computes it (after the move `Path(__file__).resolve().parent.parent` of `upgrade_rehearsal.py` is still the repo root, since the module sits in `agent_workflows/`; confirm by printing it). Then build a SIMULATED WORKTREE: copy the repo's `agent_workflows/` package (excluding `__pycache__`) into `/tmp/opencode/bs1iek/wt/agent_workflows/`, and append a marker line to the copy's `__init__.py`. From a scratch cwd `/tmp/opencode/bs1iek/box`, paste `python3 -c 'import agent_workflows;print(agent_workflows.__file__)'` with the environment `sandbox_env` would build, and again with `PYTHONPATH=/tmp/opencode/bs1iek/wt` prepended.
  - Depends on: none
  - Expected outcome: without `PYTHONPATH` the child imports the editable install's target (the main checkout); with it, the copy. If the machine has no editable install (so the first run fails to import), record that: the defect then presents as a failed install rather than a wrong one, and the fix is the same.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-02 ADD `upgrade_rehearsal.tool_repo_root()` returning the directory that contains the `agent_workflows` package this module was loaded from (`Path(__file__).resolve().parent.parent`), and make `default_aw_cmd` use it for its existing `cli.py` check, so both read one definition. Do NOT change `default_aw_cmd`'s return value.
  - Depends on: E-01
  - Expected outcome: `default_aw_cmd()` still returns `[sys.executable, "-m", "agent_workflows"]` in a checkout; `tool_repo_root() / "agent_workflows" / "cli.py"` exists.
  - Execution state: pending

- [ ] E-03 PIN THE CHILD'S IMPORT PATH. In `run_install`, after `env = sandbox_env(sandbox)`, when the resolved `cmd` is the `-m` form (`cmd[1:3] == ["-m", "agent_workflows"]`), set `env["PYTHONPATH"] = os.pathsep.join([str(tool_repo_root()), *existing])` where `existing` is the caller's `PYTHONPATH` split on `os.pathsep` with empties dropped and `tool_repo_root()` removed if already present. Leave `argv` byte-identical. Do this in `run_install`, not in `sandbox_env`: `sandbox_env` is also what the `env` subcommand prints for a human's interactive shell, where pinning a checkout would be a surprise, and the restored safety test `test_sandbox_env_redirects_config_and_home_into_the_sandbox` covers it.
  - Depends on: E-02
  - Expected outcome: the child env for the `-m` form starts `PYTHONPATH` with the tool's repo root; for an explicit `aw_cmd` like `["/usr/bin/aw"]` the env carries no added entry.
  - Execution state: pending

- [ ] E-04 RECORD AND REPORT WHAT THE CHILD IMPORTED. Add `upgrade_rehearsal.probe_import_origin(env, cwd)` that runs `[sys.executable, "-c", "import agent_workflows;print(agent_workflows.__file__)"]` with that env and cwd (timeout 60s, `check=False`) and returns the resolved path string, or `None` on a nonzero exit. In `run_install`, for the `-m` form only, call it with the SAME env and `cwd=str(sandbox)` BEFORE the install and store `imported_from` in the returned dict (for other forms store `None`, stating in a comment why a console script cannot be probed this way). Add `wrong-checkout` to `derive_observations`, reading `state.get("install_import")` (a list of `{"imported_from", "expected_root"}` entries `rehearse` copies from its runs into `result["state"]`): it fires when an `imported_from` is present and not under `expected_root`, with a note naming both paths and saying the rehearsal exercised a different checkout than the one under test, so its results do not describe this code. `report` already prints every observation; additionally print `Imported: <imported_from>` under each install line.
  - Depends on: E-03
  - Expected outcome: a normal rehearsal records an `imported_from` under the tool's repo root and emits no `wrong-checkout`; a state carrying a mismatched entry emits it.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 ADD BEHAVIORAL TESTS to `tests/test_aw_upgrade_test.py`. (1) THE WORKTREE SIMULATION: copy the package under test into a temp dir `wt/agent_workflows/` (skip `__pycache__`), load a fresh `upgrade_rehearsal` module FROM THAT COPY (`importlib.util.spec_from_file_location` on `wt/agent_workflows/upgrade_rehearsal.py`), and call its `run_install` against a sandbox created with `create_sandbox`, passing no `aw_cmd` and a harmless install argument so the child exits quickly (`--help` after `install` is acceptable if it prints and exits 0; otherwise a short timeout on a real `install -y` into the tiny sandbox). Assert the result's `imported_from` is under `wt/`, not under `REPO_ROOT`. (2) The same through `probe_import_origin` directly with the env `run_install` builds: under `wt/`. (3) An explicit `aw_cmd=[sys.executable, "-c", "import os,sys;print(os.environ.get('PYTHONPATH',''))"]` leaves `PYTHONPATH` without the tool root added (the child prints the caller's value) and records `imported_from: None`. (4) `derive_observations` rows: a mismatched `install_import` entry -> `["wrong-checkout"]`; a matching one -> `[]`. The restored `test_default_aw_cmd_prefers_the_checkout_under_test` must pass UNCHANGED. No test reads source text.
  - Depends on: E-04
  - Expected outcome: all pass after the fix; (1), (2) and the mismatch row FAIL against the pre-fix module (case (1) imports the main checkout); (3) and the matching row pass both before and after (they pin the unchanged paths; before the fix `imported_from` is simply absent, so (3) asserts only the `PYTHONPATH` half on the old code).
  - Execution state: pending

- [ ] E-06 RUN THE BARE SUITE `python3 -m pytest` before and after the change and compare failing node IDs.
  - Depends on: E-05
  - Expected outcome: the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The repository is installed EDITABLE here (`site-packages/_editable_impl_agent_workflows.pth`), which is the documented developer setup; a `python -m agent_workflows` from any cwd outside the checkout therefore resolves to whichever checkout was `pip install -e`d, never to a worktree.
- `-m` resolution puts the child's CWD first on `sys.path` (unless `PYTHONSAFEPATH` is set), then `PYTHONPATH`, then site-packages. `run_install` sets `cwd` to the sandbox, which has no `agent_workflows/`, so today `PYTHONPATH` is the only lever and it is unset. Measured with two stub packages: `PYTHONPATH=<a>` from cwd `<b>` (which holds a same-named package) ran `<b>`'s, so cwd outranks `PYTHONPATH`; from a neutral cwd it ran `<a>`'s. The sandbox is a copy of a TARGET repo, which does not contain an `agent_workflows/` package in normal use; E-04's `imported_from` makes the odd case visible rather than assuming it away.
- The restored `CliTests.test_default_aw_cmd_prefers_the_checkout_under_test` pins the argv; the env, not the argv, is where this fix lives.
- `sandbox_env` is also printed for humans by the `env` subcommand; pinning `PYTHONPATH` there would change an interactive shell's imports, so the pin is applied only in `run_install`.
- Plan `8ud1is` moves the functions to `agent_workflows/upgrade_rehearsal.py` behind a re-exporting shim; `tools/aw_upgrade_test.py` needs no edit.
- Test policy (maintainer ruling 2026-09-26): behavioral tests only; no source-text pins. Bare `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `f46b6775`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `run_install` + `sandbox_env` | The child env copies `os.environ` and adds no `PYTHONPATH`, and `cwd` is the sandbox, so `-m agent_workflows` resolves via the editable `.pth`. | `sandbox_env` body: `env = dict(os.environ)` plus XDG/AW_HOME/NO_COLOR/GIT_* only; from `/tmp`, `import agent_workflows` -> `<main>/agent_workflows/__init__.py` |
| F-2 | HIGH | override works | Prepending the worktree root to `PYTHONPATH` makes the child import the worktree's package. | `PYTHONPATH=<main>/.aw/worktrees/0i4fkt python3 -c ...` from `/tmp` -> `<main>/.aw/worktrees/0i4fkt/agent_workflows/__init__.py` |
| F-3 | MEDIUM | backlog text | The backlog names `_installer_cmd`, which does not exist; the resolver is `default_aw_cmd` and its runner is `run_install`. | `grep -n "_installer_cmd" tools/aw_upgrade_test.py` -> no match; `def default_aw_cmd` present |
| F-4 | MEDIUM | observability | No install result records which package the child imported, so a wrong-checkout rehearsal is indistinguishable from a real one. | `run_install` returns only `argv`, `exit_code`, `duration_s`, `output` |
| F-5 | INFO | constraint | The argv is pinned by a restored test and must not change. | `git show 19313eed^:tests/test_aw_upgrade_test.py`: `self.assertEqual(cmd[1:], ["-m", "agent_workflows"])` |

## Proposed changes (ordered, validatable)

1. E-01 reproduces with a simulated worktree.
2. E-02 adds one `tool_repo_root` definition.
3. E-03 prepends it to the child's `PYTHONPATH` for the `-m` form only.
4. E-04 records `imported_from` and adds a `wrong-checkout` observation.
5. E-05 behavioral tests from a copied package.
6. E-06 bare suite.

## Deferred / out of scope (with reason)

- Probing the import origin of a PATH `aw` console script or an explicit `aw_cmd`.
  - Carrier-Declined: a console script's interpreter and path are not those of `sys.executable`, so `python -c` would report a different process's answer; recording `None` is the honest value. No case of a wrong-version console script has been measured in the harness, and the docstring already names preferring `-m` as the guard.

## Scope check

- Over-scope: none.
- Under-scope: none known. `tools/aw_upgrade_test.py` is not declared because the post-`8ud1is` shim re-exports; if E-01 finds otherwise, report it as an `8ud1is` defect.
- Scope-Paths justification: `upgrade_rehearsal.py` holds `default_aw_cmd`, `run_install`, `rehearse`, `derive_observations`, and `report`; the test file receives E-05.

## Required tests / validation

- `python3 -m pytest tests/test_aw_upgrade_test.py -o addopts="" -q` passing, with E-05 (1), (2) and the mismatch row shown FAILING against the pre-fix module, and `test_default_aw_cmd_prefers_the_checkout_under_test` passing unchanged.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A: no spec covers the harness (per `8ud1is`), and no `.spec.md` is in `- Scope-Paths:`.
- `default_aw_cmd`'s docstring is updated in E-02 to say the `-m` form is paired with a pinned `PYTHONPATH` in `run_install`, because the docstring's current claim ("Prefer running the checkout's own package") is what the code fails to deliver today.

## Open questions

### OQ-01: Pin via `PYTHONPATH`, or change the argv (for example `-S` or a `-c` bootstrap)?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `PYTHONPATH`, from repository evidence. The argv is pinned by the restored `CliTests` test, which exists to guard that a rehearsal runs THIS code; changing the argv would require relaxing it. `-S` would also drop site-packages, removing the package's third-party dependencies from the child. `PYTHONPATH` precedes site-packages on `sys.path` (measured in F-2), so it overrides the editable `.pth` while keeping dependencies importable.

### OQ-02: Should a `wrong-checkout` finding fail the run instead of being an observation?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: OBSERVATION, from the harness's own contract: `derive_observations`' docstring says it is "Descriptive, never a pass/fail verdict", and the existing SAFETY finding `remote-present` is also an observation. The fix in E-03 prevents the case; the observation exists to make any residual case (for example a sandbox that happens to contain its own `agent_workflows/`, which outranks `PYTHONPATH` via cwd) visible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `8ud1is` status line, the printed tool repo root, and both `agent_workflows.__file__` outputs from the simulated worktree run (without and with `PYTHONPATH`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `tool_repo_root` and `default_aw_cmd`, and `default_aw_cmd()` printing `[sys.executable, '-m', 'agent_workflows']`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `run_install` diff, and the child-printed `PYTHONPATH` for the `-m` form (tool root first) and for an explicit `aw_cmd` (unchanged).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diff of `probe_import_origin`, `derive_observations`, `rehearse` and `report`; paste a real `rehearse(<scratch source>)` result's `runs[0]["imported_from"]` and the report's `Imported:` line, and `derive_observations` output for a mismatched entry.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_aw_upgrade_test.py -o addopts="" -q` passing with its count; then the run with the E-03/E-04 hunks temporarily reverted showing (1), (2) and the mismatch row FAILING (case (1)'s message naming the main checkout path) and `test_default_aw_cmd_prefers_the_checkout_under_test` passing; then passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. The rehearsal harness pins the child installer's `PYTHONPATH` to the checkout that launched it (argv unchanged), records which `agent_workflows` file the child imported, and reports a `wrong-checkout` observation if it is not the checkout under test. This closes a silent false-negative that has already cost a rehearsal cycle. Graduates backlog `bs1iek` and inherits its `- Blocks-Release: next`. Runs after `8ud1is` (`- Item-Dependencies: executed:8ud1is`); independent of Order 2 (`sbo3hl`), which edits different functions in the same file.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/upgrade_rehearsal.py` (`tool_repo_root`, `default_aw_cmd`'s check and docstring, `run_install`, `probe_import_origin`, `rehearse`'s copy of import records into state, `derive_observations`, `report`) and `tests/test_aw_upgrade_test.py`. If an edit outside those paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-05 must show the worktree-simulation test FAILING against the pre-fix module.

GENUINE STOP CONDITION: if `8ud1is` is not executed, do not execute this plan (the runner's dependency re-check enforces this).

Commit ONLY through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize`. Then close backlog `bs1iek` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
