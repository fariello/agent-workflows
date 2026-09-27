# IPD: Make the upgrade rehearsal install with the checkout under test, not the editable-install checkout

- Date: 2026-09-26
- Kind: child
- Concern: A rehearsal launched from a lane worktree silently installs with the MAIN checkout's package. `default_aw_cmd` (the backlog text calls it `_installer_cmd`, which does not exist) returns `[sys.executable, "-m", "agent_workflows"]` whenever `agent_workflows/cli.py` sits beside the tool, and `run_install` runs that argv with `cwd=<sandbox>` and `env=sandbox_env(...)`, which copies `os.environ` and never sets `PYTHONPATH`. With `cwd` in a sandbox, `-m` resolves the package through `sys.path`, i.e. through the EDITABLE install's `.pth` file, which points at the main checkout. Measured in review at HEAD `6b37de99`: from a scratch cwd, `python3 -c 'import agent_workflows'` imports `<main>/agent_workflows/__init__.py`; with `PYTHONPATH=<this worktree>` it imports the worktree's copy. The backlog item records the consequence: a rehearsal of a fix in a worktree reported `[version-unchanged]` and a 1.2.1 stamp, and the result flipped on the import path alone. The tool's own docstring names rehearsing a different version as "the one mistake that would invalidate every result this tool produces", and the failure is silent. THE FIX REUSES THE CANONICAL MECHANISM RATHER THAN A SECOND ONE: this repository already solved child-package pinning in `runner_shared.pinned_child_env` / `pinned_module_argv` / `runner_package_root`, and it already has a SECOND, independent defence in `checkout_pin.check_and_reexec`, which `cli.main` runs on every console-script/`-m` entry. Review measured that a bare `PYTHONPATH` pin does NOT survive either mechanism (see F-6..F-9), so this plan adopts the canonical pin instead of hand-rolling one.
- Scope: IN: in `agent_workflows/upgrade_rehearsal.py` (the post-`8ud1is` home of the harness): when the `-m` form is used, build the child environment and argv for `run_install` with the CANONICAL pin (`runner_shared.pinned_child_env` for the env, including its `AW_PIN_KEEP_ROOT`, and `runner_shared.pinned_module_argv` for the argv, which supplies `-P`/`_AW_PIN_STRIP` so the sandbox cwd cannot outrank the pin), composed so `sandbox_env`'s isolation variables still win on every key EXCEPT `PYTHONPATH`; record `imported_from` (the `agent_workflows.__file__` a probe child with the SAME env and argv shape imports) in each install result; add a `wrong-checkout` observation when `imported_from` is not under the tool's repo root, computed where `probe` can actually see it, and surface it in `report`; behavioral tests driving a temp copied package that simulates a worktree AND a sandbox that contains its own `agent_workflows/`. OUT: changing `default_aw_cmd`'s return value (the restored `CliTests.test_default_aw_cmd_prefers_the_checkout_under_test` pins `[sys.executable, "-m", "agent_workflows"]`, and that function stays the RESOLVER; the `-P`/`-c` bootstrap is applied by `run_install`, which no test pins); the PATH-`aw` fallback and an explicit `aw_cmd` (neither is the `-m` form; recording `imported_from` for them is also out, since a console script's import cannot be probed with `python -c`); `sandbox_env`'s isolation variables (unchanged, and still what the `env` subcommand prints); changing `checkout_pin` or `runner_shared` (this plan is a CONSUMER of both).
- Scope-Paths: agent_workflows/upgrade_rehearsal.py, tests/test_aw_upgrade_test.py
- Item-Dependencies: executed:8ud1is
- Status: to-review
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: bs1iek
- Blocks-Release: next
- Set: upgrehearse
- Order: 3
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: btth0a

## Workflow history

- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-501..PR-509. Reviewed in an isolated lane worktree at HEAD 6b37de99. Re-measured the defect (confirmed) and then measured the FIX as authored and found it insufficient twice over: a bare `PYTHONPATH` pin is outranked by the sandbox cwd, and `checkout_pin.check_and_reexec` re-execs the installer into the SANDBOX's package while the plan's probe reports clean. Rewrote the fix onto the canonical `runner_shared` pin, moved the `wrong-checkout` computation to where `probe` can see it (as authored it could never fire), and replaced the test module-loading mechanism, which fails outright on Python 3.12+. Checklist grew from 6 to 11 E-items and was renumbered; V-* re-bijected.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog bs1iek. Re-measured at HEAD f46b6775: the editable install's .pth resolves agent_workflows to the main checkout from any cwd outside it, and PYTHONPATH pointing at the worktree root overrides it. Corrected the backlog's function name (_installer_cmd does not exist; the resolver is default_aw_cmd, run by run_install). Independent of Order 2 (sbo3hl); ordered after 8ud1is because it edits the post-move module.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A rehearsal always installs with the package that sits beside the tool that launched it, and every install result says which package file the child actually imported, so a mismatch is visible in the report instead of invisible. "Always" is load-bearing and is what review had to repair: the pin must hold even when the sandbox is itself a copy of this toolkit, which is a REACHABLE case (`discover_sources()` offers `agent-workflows` as a rehearsal source at this HEAD), and in that case a bare `PYTHONPATH` pin loses to the child's cwd AND `checkout_pin` re-execs the installer into the sandbox's own package.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 REPRODUCE THE WRONG IMPORT. Confirm `8ud1is` is executed (`agent_workflows/upgrade_rehearsal.py` exists; the shim re-exports). Determine the tool's repo root as the moved module computes it (after the move `Path(__file__).resolve().parent.parent` of `upgrade_rehearsal.py` is still the repo root, since the module sits in `agent_workflows/`; confirm by printing it, and confirm it equals `runner_shared.runner_package_root()`). Then build a SIMULATED WORKTREE: copy the repo's `agent_workflows/` package (excluding `__pycache__`) into a scratch dir `<scratch>/wt/agent_workflows/`, and append a marker line to the copy's `__init__.py`. From a scratch cwd `<scratch>/box`, paste `python3 -c 'import agent_workflows;print(agent_workflows.__file__)'` with the environment `sandbox_env` would build, and again with `PYTHONPATH=<scratch>/wt` prepended.
  - Depends on: none
  - Expected outcome: without `PYTHONPATH` the child imports the editable install's target (the main checkout); with it, the copy. If the machine has no editable install (so the first run fails to import), record that: the defect then presents as a failed install rather than a wrong one, and the fix is the same.
  - Execution state: pending

- [ ] E-02 REPRODUCE THE TWO WAYS A BARE `PYTHONPATH` PIN FAILS, because these are what decide the shape of the fix and an executor who skips them will build the insufficient version. Build a SELF-REHEARSAL sandbox: a scratch dir holding a `git init` and a copy of this repo's `agent_workflows/` package (so the sandbox contains its own toolkit package, the case `discover_sources()` makes reachable). Then, with `PYTHONPATH=<tool repo root>` and cwd set to that sandbox, paste (a) what `python3 -c 'import agent_workflows;print(agent_workflows.__file__)'` prints, and (b) the full STDERR of `python3 -m agent_workflows --version`. Repeat (a) and (b) with `PYTHONSAFEPATH=1` added. Also paste `[o.path.name for o in discover_sources()]` filtered to the toolkit's own directory name, establishing the case is reachable and not hypothetical.
  - Depends on: E-01
  - Expected outcome: measured in review at HEAD `6b37de99`. WITHOUT `PYTHONSAFEPATH`: (a) prints the SANDBOX's copy, because `-m` puts the child's cwd ahead of `PYTHONPATH`, so the pin silently loses; (b) is empty, so nothing warns. WITH `PYTHONSAFEPATH=1`: (a) prints the tool root, but (b) now carries `checkout_pin`'s notice `aw: invoked in checkout <sandbox> but imported agent_workflows from <tool root>; re-running with <sandbox>'s package`, i.e. the installer RE-EXECS into the sandbox's package while a `python -c` probe still reports the tool root. That second case is the dangerous one: the plan's own observation would report clean while the rehearsal ran the wrong code. Confirm the toolkit IS discoverable as a source. If either half does not reproduce, STOP and report it: the fix in E-04 is justified by these measurements and must be re-derived, not applied blindly.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-03 ADD `upgrade_rehearsal.tool_repo_root()` returning the directory that contains the `agent_workflows` package this module was loaded from. Implement it by DELEGATING to `runner_shared.runner_package_root()` (import it lazily inside the function, as this module already does for `agent_workflows.config` in `search_roots`, so the harness keeps its cheap import; `runner_shared` costs about 0.12s to import, measured in review, which is acceptable inside a function that is about to spawn an installer but not at module scope). Fall back to `Path(__file__).resolve().parent.parent` if that import fails, and say in a comment why the delegation is preferred: ONE definition of "this toolkit's package root" across the runners and this harness. Make `default_aw_cmd` use `tool_repo_root()` for its existing `cli.py` check so both read one definition, and update its docstring per the spec-sync section. Do NOT change `default_aw_cmd`'s return value.
  - Depends on: E-02
  - Expected outcome: `default_aw_cmd()` still returns `[sys.executable, "-m", "agent_workflows"]` in a checkout; `tool_repo_root() / "agent_workflows" / "cli.py"` exists; `tool_repo_root() == Path(runner_shared.runner_package_root())`; `import agent_workflows.upgrade_rehearsal` does NOT pull in `runner_shared` at module scope (assert via a fresh child interpreter checking `"agent_workflows.runner_shared" not in sys.modules` after the import).
  - Execution state: pending

- [ ] E-04 PIN THE CHILD WITH THE CANONICAL MECHANISM, NOT A BARE `PYTHONPATH`. In `run_install`, when the resolved `cmd` is the `-m` form (`cmd[1:3] == ["-m", "agent_workflows"]`), replace BOTH the env and the argv:
  (1) ENV, in this exact order, because the order is the whole correctness of it: start from `runner_shared.pinned_child_env()` (which prepends `runner_package_root()` to `PYTHONPATH` and sets `AW_PIN_KEEP_ROOT`), then apply `sandbox_env(sandbox)`'s keys EXCEPT `PYTHONPATH` over it. Do NOT write `pinned_child_env(sandbox_env(sandbox))`: `sandbox_env` copies `os.environ` wholesale, so its `PYTHONPATH` value is passed as an override and CLOBBERS the pin. Measured in review with a caller `PYTHONPATH=/caller/entry`: the wrong order yields `PYTHONPATH=/caller/entry` (pin lost), the right order yields `<tool root>:/caller/entry` with `XDG_CONFIG_HOME` and `AW_HOME` still inside the sandbox.
  (2) ARGV: use `runner_shared.pinned_module_argv(["install", str(sandbox), "-y", *install_args])`. This is what makes the pin actually hold: it supplies `-P` on 3.11+ and the `_AW_PIN_STRIP` prologue, which removes the child's cwd from `sys.path` while KEEPING `AW_PIN_KEEP_ROOT`, so a sandbox that contains its own `agent_workflows/` can no longer outrank the pin (E-02 case (a)), and it sets `AW_PINNED_CHILD=1`, which `checkout_pin.check_and_reexec` pops and honors as an exemption, so the installer is no longer re-executed into the sandbox's package (E-02 case (b)). Keep `cwd=str(sandbox)` and the existing `timeout`. Record the argv actually run in the result's `argv` (no test pins that value; verified in review).
  This is applied in `run_install`, NOT in `sandbox_env` or `default_aw_cmd`: `sandbox_env` is also what the `env` subcommand prints for a human's interactive shell, where pinning a checkout would be a surprise, and the restored safety test `test_sandbox_env_redirects_config_and_home_into_the_sandbox` covers it; `default_aw_cmd`'s return value is pinned by a restored test. An explicit `aw_cmd` and the PATH-`aw` fallback take NEITHER change: env and argv stay exactly as today.
  - Depends on: E-03
  - Expected outcome: for the `-m` form the child env's `PYTHONPATH` starts with the tool's repo root and carries `AW_PIN_KEEP_ROOT`, the argv is the `-P`/`-c` bootstrap form, and running it against the E-02 self-rehearsal sandbox prints NO `checkout_pin` notice and resolves the TOOL's package. For an explicit `aw_cmd` like `["/usr/bin/aw"]` the env carries no added `PYTHONPATH` entry and the argv is unchanged. `install --help` through the pinned form still exits 0, proving third-party dependencies remain importable (which is why `-S` was rejected; see OQ-01).
  - Execution state: pending

- [ ] E-05 RECORD WHAT THE CHILD IMPORTED. Add `upgrade_rehearsal.probe_import_origin(env, cwd)` that runs the SAME pinned argv shape the install will use (`[sys.executable, *(["-P"] if sys.version_info >= (3, 11) else []), "-c", runner_shared._AW_PIN_STRIP + "import agent_workflows;print(agent_workflows.__file__)"]`) with that env and cwd (timeout 60s, `check=False`) and returns the resolved path string (`os.path.realpath`), or `None` on a nonzero exit or empty output. THE ARGV SHAPE MUST MATCH THE INSTALL'S: a plain `python -c` probe does not strip the cwd, so it answers a different question than the install asks, and review measured that exact divergence reporting clean while the install ran the sandbox's code. In `run_install`, for the `-m` form only, call it with the SAME env and `cwd=str(sandbox)` BEFORE the install and store `imported_from` plus `expected_root` (`str(tool_repo_root())`) in the returned dict; for other forms store `imported_from: None`, with a comment stating that a console script's interpreter is not `sys.executable` so `python -c` would report a different process's answer.
  - Depends on: E-04
  - Expected outcome: a normal rehearsal records an `imported_from` under the tool's repo root; against the E-02 self-rehearsal sandbox the pinned probe and the pinned install AGREE (both the tool root).
  - Execution state: pending

- [ ] E-06 MAKE `wrong-checkout` ABLE TO FIRE, WHICH AS AUTHORED IT COULD NOT. `derive_observations` is called from INSIDE `probe`, on the dict `probe` itself builds, and `rehearse` only assigns `result["state"] = probe(sandbox)` AFTERWARDS; so any key `rehearse` copies in later cannot influence the already-computed observations, and a mismatch would never be reported. Verified in review: `derive_observations({"install_import": [{"imported_from": "<sandbox>/agent_workflows/__init__.py", "expected_root": "<tool>"}]})` returns `[]` today, and would still return `[]` under the authored design in a real run. Fix it by threading the records INTO the probe rather than onto its output: give `probe` an optional `install_import: Optional[Sequence[Mapping[str, str]]] = None` parameter, put it into `state["install_import"]` BEFORE the `derive_observations(state)` call, and have `rehearse` pass the `{"imported_from", "expected_root"}` records collected from its runs. Keep `probe(sandbox)` working with no argument (the `probe` subcommand calls it that way and must keep doing so; with no records the key is absent and nothing fires). Then add the `wrong-checkout` kind to `derive_observations`, reading `state.get("install_import")`: it fires when an `imported_from` is present and is not under `expected_root` (compare resolved paths with `os.path.commonpath`-style containment, not a bare `startswith`, so `<root>-other` is not treated as inside `<root>`), with a note naming both paths and saying the rehearsal exercised a different checkout than the one under test, so its results do not describe this code. Keep the function's DESCRIPTIVE, never-a-verdict docstring (see OQ-02).
  - Depends on: E-05
  - Expected outcome: `probe(sandbox)` with no argument behaves exactly as today; `probe(sandbox, install_import=[<mismatched record>])["observations"]` contains `wrong-checkout`; a matching record yields no such kind; and a real `rehearse` of a scratch source carries the records through to `result["state"]["observations"]`.
  - Execution state: pending

- [ ] E-07 SURFACE IT TO THE HUMAN. In `report`, print `Imported: <imported_from>` under each install line (omit the line when the value is `None`, so the `aw_cmd` case does not print a bare `None`). The observation list `report` already prints carries `wrong-checkout` itself.
  - Depends on: E-06
  - Expected outcome: `report()` on a result whose run carries `imported_from` prints the `Imported:` line under that run; on a result whose run has `imported_from: None` it prints no such line; a state carrying a mismatched record prints the `[wrong-checkout]` observation.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-08 ADD THE WORKTREE-SIMULATION TESTS to `tests/test_aw_upgrade_test.py`. (1) THE WORKTREE SIMULATION: copy the package under test into a temp dir `wt/agent_workflows/` (skip `__pycache__`), load a fresh `upgrade_rehearsal` module FROM THAT COPY using the suite's OWN helper `support.load_module("<unique name>", wt / "agent_workflows" / "upgrade_rehearsal.py")` and NOT a bare `importlib.util.spec_from_file_location` + `exec_module`: the bare form FAILS on this module on Python 3.12+ (measured in review on 3.14: `AttributeError: 'NoneType' object has no attribute '__dict__'` from `dataclasses._is_type`, because `@dataclass` on `SourceRepo` looks its module up in `sys.modules`), which is exactly why `support.load_module` registers the module and says so in its docstring. Use a unique module name per test and remove it from `sys.modules` in a `finally`, so a registered copy cannot leak into another test under pytest-randomly's ordering. Then call that copy's `run_install` against a sandbox created with `create_sandbox`, passing no `aw_cmd` and `install_args=("--help",)` so the child prints usage and exits 0 quickly (verified in review: `install <dir> -y --help` exits 0). Assert the result's `imported_from` is under `wt/` and NOT under `REPO_ROOT`. (2) The same through `probe_import_origin` directly with the env and argv shape `run_install` builds: under `wt/`.
  - Depends on: E-07
  - Expected outcome: both pass after the fix and FAIL against the pre-fix module (they resolve `REPO_ROOT`'s package, or `imported_from` is absent entirely). If `support.load_module` is unavailable or does not resolve, report it rather than reverting to the bare loader.
  - Execution state: pending

- [ ] E-09 ADD THE SELF-REHEARSAL TEST, which is the one that distinguishes this fix from the insufficient one and MUST NOT be folded into E-08. Build a sandbox that CONTAINS its own `agent_workflows/` package (copy the package under test into the sandbox root after `create_sandbox`, or `git init` a scratch dir holding such a copy), then call `run_install` with no `aw_cmd`. Assert (a) `imported_from` is under the tool's repo root and NOT under the sandbox, and (b) the captured `output` contains no `checkout_pin` notice, asserted against `runner_shared._CHECKOUT_PIN_NOTICE_PREFIX` rather than a hand-copied string (that constant exists precisely so a reworded notice fails a test; `run_install` merges stderr into stdout, so the notice would appear in `output`). Add a third case asserting the `wrong-checkout` observation DOES fire when the records say so, by driving `probe(sandbox, install_import=[<mismatched record>])`.
  - Depends on: E-08
  - Expected outcome: passes after the fix; against the pre-fix module (and also against a bare-`PYTHONPATH`-only implementation) assertion (a) or (b) FAILS, which is what proves the canonical pin is load-bearing and a plain `PYTHONPATH` is not.
  - Execution state: pending

- [ ] E-10 ADD THE UNCHANGED-PATH AND OBSERVATION-ROW TESTS. (1) An explicit `aw_cmd=[sys.executable, "-c", "import os;print(os.environ.get('PYTHONPATH',''))"]` leaves `PYTHONPATH` without the tool root prepended (the child prints the caller's value) and records `imported_from: None`; assert the argv recorded is the caller's, i.e. NOT the pinned bootstrap. (2) `derive_observations` rows driven through `probe`'s new parameter: a mismatched `install_import` entry -> kinds contain `wrong-checkout`; a matching one -> it does not; a sibling-prefix case (`expected_root` `<root>` with `imported_from` under `<root>-other`) -> it DOES fire, pinning the containment comparison rather than `startswith`. (3) `probe(sandbox)` called with NO `install_import` argument yields a state with no `install_import` key and no `wrong-checkout`, pinning the `probe` subcommand's existing call shape. (4) `report()` prints the `Imported:` line when the value is present and omits it when `None`. The restored `test_default_aw_cmd_prefers_the_checkout_under_test` and `test_sandbox_env_redirects_config_and_home_into_the_sandbox` must both pass UNCHANGED. No test reads production source text (maintainer ruling 2026-09-26); referencing the exported constant `_CHECKOUT_PIN_NOTICE_PREFIX` is a value import, not a source-text scan.
  - Depends on: E-09
  - Expected outcome: all pass after the fix. (1), (3) and the matching row pass both before and after (they pin unchanged paths; before the fix `imported_from` is simply absent, so (1) asserts only the `PYTHONPATH` and argv halves on the old code); the mismatch and sibling-prefix rows and (4) fail before.
  - Execution state: pending

- [ ] E-11 RUN THE BARE SUITE `python3 -m pytest` before and after the change and compare failing node IDs.
  - Depends on: E-10
  - Expected outcome: the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The repository is installed EDITABLE here (`site-packages/_editable_impl_agent_workflows.pth`), which is the documented developer setup; a `python -m agent_workflows` from any cwd outside the checkout therefore resolves to whichever checkout was `pip install -e`d, never to a worktree.
- `-m` resolution puts the child's CWD first on `sys.path` (unless `PYTHONSAFEPATH`/`-P` is set), then `PYTHONPATH`, then site-packages. `run_install` sets `cwd` to the sandbox, so `PYTHONPATH` alone is NOT a sufficient lever whenever the sandbox contains an `agent_workflows/` package. Measured with two stub packages: `PYTHONPATH=<a>` from cwd `<b>` (which holds a same-named package) ran `<b>`'s, so cwd outranks `PYTHONPATH`; adding `PYTHONSAFEPATH=1` ran `<a>`'s. THE ODD CASE IS REACHABLE, not hypothetical: `discover_sources()` offers this toolkit's own checkout as a rehearsal source at this HEAD (confirmed in review), so a self-rehearsal produces exactly a sandbox holding its own `agent_workflows/`. That is why the fix uses the canonical bootstrap (which strips the cwd) and not a bare `PYTHONPATH`.
- THIS REPOSITORY ALREADY OWNS CHILD-PACKAGE PINNING, and duplicating it would be a second mechanism to keep in sync. `runner_shared.runner_package_root()` / `pinned_child_env()` / `pinned_module_argv()` are the canonical trio: the env prepends the root and sets `AW_PIN_KEEP_ROOT`, and the argv adds `-P` (3.11+) plus the `_AW_PIN_STRIP` prologue that drops the cwd from `sys.path` while KEEPING the pinned root, and sets `AW_PINNED_CHILD=1`. Verified in review against a self-rehearsal sandbox: the canonical form resolves the tool's package, prints no `checkout_pin` notice, and still imports third-party dependencies (`filelock`, `yaml`).
- THERE IS A SECOND MECHANISM THAT WILL FIGHT A NAIVE PIN: `cli.main` calls `checkout_pin.check_and_reexec()` on every console-script/`-m` entry, and that function RE-EXECS into the checkout enclosing the child's cwd when it differs from the imported package. A sandbox with a `.git` and an `agent_workflows/` therefore captures the installer. `AW_PINNED_CHILD=1` (set by `pinned_module_argv`'s bootstrap and popped by `check_and_reexec`) is the sanctioned exemption. `runner_shared._CHECKOUT_PIN_NOTICE_PREFIX` exists so a test can detect the notice without copying its wording.
- `derive_observations` runs INSIDE `probe`, on the dict `probe` builds; `rehearse` assigns `result["state"] = probe(...)` only afterwards. So an observation that must read install-time records requires those records to reach `probe`, not `result["state"]` (this is what E-06 fixes).
- The restored `CliTests.test_default_aw_cmd_prefers_the_checkout_under_test` pins `default_aw_cmd`'s RETURN VALUE, which stays the resolver's answer. No test pins the argv `run_install` actually spawns or the `argv` it records (verified by grep in review), so `run_install` is free to wrap the resolved form in the canonical bootstrap.
- `support.load_module` (in `tests/support.py`) is the suite's file-path module loader and MUST be used for loading a copied `upgrade_rehearsal`: it registers the module in `sys.modules`, which Python 3.12+ requires for `@dataclass` to resolve `cls.__module__`. A bare `spec_from_file_location` + `exec_module` raises `AttributeError` on this module (measured on 3.14).
- `sandbox_env` is also printed for humans by the `env` subcommand; pinning `PYTHONPATH` there would change an interactive shell's imports, so the pin is applied only in `run_install`.
- Plan `8ud1is` moves the functions to `agent_workflows/upgrade_rehearsal.py` behind a re-exporting shim; `tools/aw_upgrade_test.py` needs no edit.
- Test policy (maintainer ruling 2026-09-26): behavioral tests only; no source-text pins. Bare `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1..F-5 measured at HEAD `f46b6775` (authoring). F-6..F-10 measured in review at HEAD `6b37de99`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `run_install` + `sandbox_env` | The child env copies `os.environ` and adds no `PYTHONPATH`, and `cwd` is the sandbox, so `-m agent_workflows` resolves via the editable `.pth`. | `sandbox_env` body: `env = dict(os.environ)` plus XDG/AW_HOME/NO_COLOR/GIT_* only; from `/tmp`, `import agent_workflows` -> `<main>/agent_workflows/__init__.py` |
| F-2 | HIGH | override works | Prepending the worktree root to `PYTHONPATH` makes the child import the worktree's package. | `PYTHONPATH=<main>/.aw/worktrees/0i4fkt python3 -c ...` from `/tmp` -> `<main>/.aw/worktrees/0i4fkt/agent_workflows/__init__.py` |
| F-3 | MEDIUM | backlog text | The backlog names `_installer_cmd`, which does not exist; the resolver is `default_aw_cmd` and its runner is `run_install`. Post-`8ud1is` the definition lives in `agent_workflows/upgrade_rehearsal.py`; the `tools/` file is a re-exporting shim and contains no `def`. | `def default_aw_cmd` present in `agent_workflows/upgrade_rehearsal.py`; `grep -c "def default_aw_cmd" tools/aw_upgrade_test.py` -> `0` |
| F-4 | MEDIUM | observability | No install result records which package the child imported, so a wrong-checkout rehearsal is indistinguishable from a real one. | `run_install` returns only `argv`, `exit_code`, `duration_s`, `output` |
| F-5 | INFO | constraint | `default_aw_cmd`'s RETURN VALUE is pinned by a restored test. The argv `run_install` spawns is NOT pinned by any test, so the bootstrap wrapper is available. | `git show 19313eed^:tests/test_aw_upgrade_test.py`: `self.assertEqual(cmd[1:], ["-m", "agent_workflows"])`; no test references `result["argv"]` |
| F-6 | BLOCKER | the authored fix (`PYTHONPATH` alone) | A BARE `PYTHONPATH` PIN DOES NOT HOLD. The child's cwd precedes `PYTHONPATH` on `sys.path`, and `run_install` sets `cwd` to the sandbox, so a sandbox containing its own `agent_workflows/` wins and the rehearsal runs the SANDBOX's code, silently. Reachable, not hypothetical: `discover_sources()` offers this toolkit as a source. | self-rehearsal sandbox + `PYTHONPATH=<tool root>`: `import agent_workflows` -> `<sandbox>/agent_workflows/__init__.py`; with `PYTHONSAFEPATH=1` -> `<tool root>/...` |
| F-7 | BLOCKER | `checkout_pin.check_and_reexec` vs the authored fix | EVEN WITH THE CWD STRIPPED, THE INSTALLER IS RE-EXECUTED INTO THE SANDBOX'S PACKAGE. `cli.main` runs `check_and_reexec()`, which re-execs when the checkout enclosing cwd differs from the imported package. Worse, the authored probe would report CLEAN while this happened, because a plain `python -c` probe never enters `cli.main`. This is a false negative in the exact tool whose purpose is to prevent false negatives. | with `PYTHONPATH=<tool root> PYTHONSAFEPATH=1`, cwd the self-rehearsal sandbox: probe prints `<tool root>/...` while `python3 -m agent_workflows --version` STDERR reads `aw: invoked in checkout <sandbox> ... re-running with <sandbox>'s package` |
| F-8 | BLOCKER | `probe` / `derive_observations` / `rehearse` ordering | THE `wrong-checkout` OBSERVATION AS AUTHORED CAN NEVER FIRE. `derive_observations` is called from inside `probe` on the dict `probe` builds; `rehearse` assigns `result["state"] = probe(...)` afterwards, so records copied onto `result["state"]` arrive after the observations are computed. | `probe` body: `state["observations"] = derive_observations(state)`; `rehearse`: `result["runs"].append(...)` precedes `result["state"] = probe(sandbox)`; `derive_observations({"install_import": [<mismatch>]})` -> `[]` |
| F-9 | HIGH | E-08's module-loading mechanism | THE PRESCRIBED TEST LOADER FAILS OUTRIGHT. A bare `spec_from_file_location` + `exec_module` on a copied `upgrade_rehearsal.py` raises, because `@dataclass` on `SourceRepo` resolves `cls.__module__` through `sys.modules` on 3.12+. The suite already has the correct helper. | on 3.14: `AttributeError: 'NoneType' object has no attribute '__dict__'` at `dataclasses._is_type`, raised from `upgrade_rehearsal.py` line with `@dataclass`; `support.load_module` loads the same file successfully and its docstring states the reason |
| F-10 | HIGH | env composition order | `pinned_child_env(sandbox_env(sandbox))` SILENTLY DISCARDS THE PIN, because `sandbox_env` copies `os.environ` (including any caller `PYTHONPATH`) and is applied as an override. The safe order is pin first, then `sandbox_env`'s keys except `PYTHONPATH`. | with caller `PYTHONPATH=/caller/entry`: wrong order -> `PYTHONPATH=/caller/entry`; right order -> `<tool root>:/caller/entry` with `XDG_CONFIG_HOME`/`AW_HOME` still under the sandbox |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the wrong import with a simulated worktree.
2. E-02 reproduces the TWO ways a bare `PYTHONPATH` pin fails (cwd precedence; `checkout_pin` re-exec), which justify the fix's shape.
3. E-03 adds one `tool_repo_root` definition, delegating to `runner_shared.runner_package_root`.
4. E-04 pins the child with the canonical `pinned_child_env` + `pinned_module_argv`, composed in the safe order, for the `-m` form only.
5. E-05 records `imported_from` with a probe whose argv shape matches the install's.
6. E-06 threads the records into `probe` so `wrong-checkout` can actually fire, and adds the observation.
7. E-07 surfaces `Imported:` in the human report.
8. E-08 worktree-simulation tests, loaded with `support.load_module`.
9. E-09 the self-rehearsal test, which is what distinguishes this fix from the insufficient one.
10. E-10 unchanged-path and observation-row tests.
11. E-11 bare suite.

## Deferred / out of scope (with reason)

- Probing the import origin of a PATH `aw` console script or an explicit `aw_cmd`.
  - Carrier-Declined: a console script's interpreter and path are not those of `sys.executable`, so `python -c` would report a different process's answer; recording `None` is the honest value. No case of a wrong-version console script has been measured in the harness, and the docstring already names preferring `-m` as the guard.

## Scope check

- Over-scope: none.
- Under-scope: none known. `tools/aw_upgrade_test.py` is not declared because the post-`8ud1is` shim re-exports; if E-01 finds otherwise, report it as an `8ud1is` defect. `runner_shared.py` and `checkout_pin.py` are NOT declared and must not be edited: this plan CONSUMES their public symbols (`runner_package_root`, `pinned_child_env`, `pinned_module_argv`, `_AW_PIN_STRIP`, `_CHECKOUT_PIN_NOTICE_PREFIX`) and changes neither. If the fix appears to require editing either, STOP and report it: that would be a change to the driver-authoritative pinning contract (spec `llbr2b` C-10 makes nested tool identity an INVARIANT) and is not this plan's to make.
- Scope-Paths justification: `upgrade_rehearsal.py` holds `default_aw_cmd`, `run_install`, `probe`, `rehearse`, `derive_observations`, and `report`; the test file receives E-08/E-09/E-10.
- The two underscore-prefixed `runner_shared` symbols this plan reads (`_AW_PIN_STRIP`, `_CHECKOUT_PIN_NOTICE_PREFIX`) are module-internal by name. They are used deliberately rather than re-spelled: `_AW_PIN_STRIP` is the exact prologue the canonical argv uses, so copying its text would create the second mechanism this plan exists to avoid, and `_CHECKOUT_PIN_NOTICE_PREFIX` is documented in its own comment as the constant tests should assert against. If either is renamed, this plan's tests fail loudly rather than silently, which is the intended direction.

## Required tests / validation

- `python3 -m pytest tests/test_aw_upgrade_test.py -o addopts="" -q` passing, with E-08 (1), (2), the E-09 self-rehearsal assertions and the E-10 mismatch/sibling-prefix rows shown FAILING against the pre-fix module, and `test_default_aw_cmd_prefers_the_checkout_under_test` plus `test_sandbox_env_redirects_config_and_home_into_the_sandbox` passing unchanged.
- THE LOAD-BEARING EVIDENCE IS E-09, NOT THE SUITE COUNT. A bare-`PYTHONPATH` implementation passes E-08 and fails E-09, so E-09 is the only test that distinguishes the correct fix from the insufficient one. A green suite without E-09's two assertions pasted is not evidence this plan's defect is fixed.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A: no spec covers the harness (per `8ud1is`), and no `.spec.md` is in `- Scope-Paths:`, so no spec is amended. Spec `llbr2b` C-10 (nested tool identity is an INVARIANT) is CONSUMED unchanged and is the reason this plan reuses the canonical pin rather than writing a second one; it needs no edit because this plan adds a consumer, not a contract.
- `default_aw_cmd`'s docstring is updated in E-03 to say the `-m` form is paired in `run_install` with the canonical pin (env AND argv), because the docstring's current claim ("Prefer running the checkout's own package") is what the code fails to deliver today, and because a reader who sees only `PYTHONPATH` mentioned would reintroduce the insufficient fix.
- The module docstring's four safety invariants are NOT amended: this plan fixes a correctness/false-negative defect, not a safety invariant, and adding a fifth would overstate what changed.

## Open questions

### OQ-01: Pin via `PYTHONPATH`, or change the argv (for example `-S` or a `-c` bootstrap)?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: REVISED BY REVIEW. `PYTHONPATH` ALONE IS INSUFFICIENT (F-6, F-7): the child's cwd outranks it, and `checkout_pin` re-execs the installer anyway. `-S` is still rejected, for the reason originally given: it drops site-packages and so removes third-party dependencies. The answer is the CANONICAL bootstrap, `runner_shared.pinned_child_env` + `pinned_module_argv`, which uses `-P`/`_AW_PIN_STRIP` (strip the cwd only, keep site-packages) plus `AW_PINNED_CHILD` (the sanctioned `checkout_pin` exemption). It also does not require relaxing the restored `CliTests` test, because that test pins `default_aw_cmd`'s RETURN VALUE and no test pins the argv `run_install` spawns (F-5). Verified in review: the canonical form resolves the tool's package from a self-rehearsal sandbox, prints no re-exec notice, and still imports `filelock` and `yaml`.

### OQ-02: Should a `wrong-checkout` finding fail the run instead of being an observation?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: OBSERVATION, from the harness's own contract: `derive_observations`' docstring says it is "Descriptive, never a pass/fail verdict", and the existing SAFETY finding `remote-present` is also an observation. The fix in E-04 prevents the case; the observation exists to make any residual case visible. Review sharpened the residual case: the sandbox-contains-its-own-package scenario is NOT residual under a bare `PYTHONPATH` pin (it is the common self-rehearsal path, F-6), which is why E-04 now closes it in the mechanism rather than leaving it to the observation. What remains for the observation is the genuinely unforeseen: an interpreter or environment where the pin does not take effect. Note that `remote-present` sets the precedent in the SAFETY class specifically, which is the class this finding belongs to, so consistency favors an observation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `8ud1is` status line, the printed tool repo root, the equality against `runner_shared.runner_package_root()`, and both `agent_workflows.__file__` outputs from the simulated worktree run (without and with `PYTHONPATH`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste, for the self-rehearsal sandbox, all FOUR measurements: the probe's `agent_workflows.__file__` and the full `python3 -m agent_workflows --version` STDERR, each without and with `PYTHONSAFEPATH=1`. The no-SAFEPATH probe MUST name the sandbox's package and the with-SAFEPATH STDERR MUST contain the `checkout_pin` re-exec notice; paste both verbatim. Also paste the `discover_sources()` output showing the toolkit's own directory is offered as a source. If any of the four differs from the Expected outcome, paste it and STOP.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of `tool_repo_root` and `default_aw_cmd`, `default_aw_cmd()` printing `[sys.executable, '-m', 'agent_workflows']`, the `tool_repo_root() == Path(runner_shared.runner_package_root())` comparison, and the fresh-child assertion that `agent_workflows.runner_shared` is absent from `sys.modules` after importing `agent_workflows.upgrade_rehearsal`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `run_install` diff; the child-printed `PYTHONPATH` and `AW_PIN_KEEP_ROOT` for the `-m` form (tool root FIRST) and for an explicit `aw_cmd` (unchanged, no added entry); the spawned argv for each form; and the `install --help` exit code through the pinned form proving dependencies still import. Additionally paste the composition-order check from F-10: with a caller `PYTHONPATH` set, show the resulting `PYTHONPATH` has the tool root first AND `XDG_CONFIG_HOME`/`AW_HOME` still under the sandbox.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of `probe_import_origin` and `run_install`'s call to it; show the probe argv includes the `-P`/`_AW_PIN_STRIP` form (not a plain `python -c`); paste a real `rehearse(<scratch source>)` result's `runs[0]["imported_from"]` and `expected_root`; and paste the `aw_cmd` case recording `imported_from: None`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the diff of `probe`'s new parameter, `rehearse`'s pass-through, and `derive_observations`; paste `probe(sandbox)` with NO argument showing no `install_import` key and no `wrong-checkout`; paste `probe(sandbox, install_import=[<mismatched record>])["observations"]` containing `wrong-checkout`; paste the matching-record case NOT firing; and paste the sibling-prefix case (`<root>-other`) FIRING, proving containment and not `startswith`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `report` diff and its captured stdout for a run WITH `imported_from` (shows the `Imported:` line) and for a run with `imported_from: None` (no such line), plus the `[wrong-checkout]` observation line printed for a mismatched state.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the two new tests' node IDs passing, and paste them FAILING against the pre-fix module with the failure message naming `REPO_ROOT`'s path. Confirm explicitly that `support.load_module` was used and that the bare `spec_from_file_location` loader was not, pasting the module-name cleanup.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: THE LOAD-BEARING VALIDATION. Paste the self-rehearsal test passing, showing `imported_from` under the tool root and the absence of `_CHECKOUT_PIN_NOTICE_PREFIX` in the captured `output`. Then paste it FAILING against an implementation that pins only `PYTHONPATH` (temporarily drop the `pinned_module_argv` half of E-04 and keep the env half), with the failure message. A validation that shows this test passing only against the final code, without the bare-`PYTHONPATH` counter-run, does NOT satisfy this item, because that counter-run is the only evidence the canonical pin is necessary.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `python3 -m pytest tests/test_aw_upgrade_test.py -o addopts="" -q` passing with its count; paste the pre-fix run showing the mismatch row, the sibling-prefix row and the `report` test FAILING while `test_default_aw_cmd_prefers_the_checkout_under_test` and `test_sandbox_env_redirects_config_and_home_into_the_sandbox` PASS; then passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. The rehearsal harness runs the child installer under this repository's CANONICAL child-package pin (`runner_shared.pinned_child_env` + `pinned_module_argv`), so a rehearsal launched from a lane worktree installs with THAT worktree's code; it records which `agent_workflows` file the child imported, and reports a `wrong-checkout` observation if it is not the checkout under test. This closes a silent false-negative that has already cost a rehearsal cycle. Graduates backlog `bs1iek` and inherits its `- Blocks-Release: next`. Runs after `8ud1is` (`- Item-Dependencies: executed:8ud1is`); independent of Order 2 (`sbo3hl`), which edits different functions in the same file, except that BOTH touch `derive_observations` and `probe`, so whichever runs second must rebase its hunks rather than assume the authored surrounding text.

WHAT REVIEW CHANGED, because a maintainer approving this is approving a materially different fix from the one authored. The authored fix (set `PYTHONPATH`, leave the argv alone) was measured and found insufficient TWICE: a sandbox containing its own `agent_workflows/` outranks `PYTHONPATH` via the child's cwd (F-6), and `checkout_pin.check_and_reexec` re-executes the installer into the sandbox's package while the authored probe reports clean (F-7), which is a false negative inside the tool whose purpose is preventing false negatives. The authored `wrong-checkout` observation also could never fire, because `derive_observations` runs inside `probe` before `rehearse` attaches the records (F-8). The plan now consumes the existing canonical mechanism instead of adding a second one. It changes NEITHER `runner_shared` nor `checkout_pin`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/upgrade_rehearsal.py` (`tool_repo_root`, `default_aw_cmd`'s check and docstring, `run_install`, `probe_import_origin`, `probe`'s new `install_import` parameter, `rehearse`'s pass-through, `derive_observations`, `report`) and `tests/test_aw_upgrade_test.py`. If an edit outside those paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-08 must show the worktree-simulation test FAILING against the pre-fix module, and V-09 must ALSO show the self-rehearsal test failing against a `PYTHONPATH`-only implementation. A GREEN SUITE IS NOT SUFFICIENT EVIDENCE HERE: a `PYTHONPATH`-only fix passes every test except E-09's two assertions, so V-09's counter-run is the only thing separating the correct fix from the one review rejected.

GENUINE STOP CONDITIONS: (1) if `8ud1is` is not executed, do not execute this plan (the runner's dependency re-check enforces this); (2) if E-02 does not reproduce BOTH failure modes, stop and report rather than applying E-04 blindly, since E-04's shape is justified by those measurements; (3) if the fix appears to require editing `runner_shared.py` or `checkout_pin.py`, stop and report: nested tool identity is an INVARIANT (spec `llbr2b` C-10) and the driver-authoritative pinning contract is not this plan's to change.

Commit ONLY through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize`. Then close backlog `bs1iek` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
