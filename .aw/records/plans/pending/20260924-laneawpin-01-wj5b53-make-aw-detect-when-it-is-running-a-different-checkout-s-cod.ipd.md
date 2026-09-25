# IPD: Make aw detect when it is running a different checkout's code than the worktree it was invoked in, and make lane turns run the lane's own package

- Date: 2026-09-24
- Kind: child
- Concern: The `aw` console script (`pyproject.toml` `[project.scripts]` `aw = "agent_workflows.cli:main"`) imports `agent_workflows` from whatever single tree the editable install `.pth` names, independent of cwd. So `aw <verb>` run inside a checkout of THIS toolkit that is not that tree (a lane worktree, a scratch worktree, or the main checkout when the install points at a lane) silently executes OTHER code, and any `aw check`/`aw ipd lint`/`aw attention` output pasted as evidence attests to the wrong tree. The failure is silent and biased toward false confidence. Backlog `lcmz33` (the interactive half) and its duplicate `jeh310` (same defect, measured in lane `9iiqmm`: `aw attention` rendered the pre-change board while `python3 -m agent_workflows attention` rendered the new one) both describe it. Commit `eec572d6` (IPD `lhjsu0`) fixed only the TEST side (`conftest.py` sys.path, `tests/support.run_cli`); the console script itself is untouched. Also affected: `python3 -m agent_workflows` from a checkout SUBDIRECTORY (cwd-first finds no package there, so the `.pth` tree wins).
- Scope: IN: (a) a cheap, subprocess-free checkout-mismatch detector called at the top of `cli.main` when `argv is None` (real process entry only); (b) on mismatch, re-exec `sys.executable -m agent_workflows <argv>` with the invoked checkout's toplevel prepended to `PYTHONPATH`, with a one-line stderr notice naming both roots; (c) a loop guard, an `AW_NO_REEXEC=1` opt-out (warn, do not re-exec), and a silent exemption for the runner's pinned nested calls by having `runner_shared._AW_PIN_BOOTSTRAP` mark its process; (d) subprocess tests on throwaway fake checkouts; (e) a CHANGELOG entry. OUT: changing `pinned_child_env`/`pinned_module_argv`/`assert_child_tool_identity` bodies (the af7i6p contract, and both are AST-fingerprinted in `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`); changing the editable install or PATH; managed target repos (no `agent_workflows/` package at their toplevel), which must be byte-for-byte unaffected.
- Scope-Paths: agent_workflows/checkout_pin.py, agent_workflows/cli.py, agent_workflows/runner_shared.py, tests/test_cli_checkout_reexec.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Set: laneawpin
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: wj5b53
- From-Backlog: lcmz33
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog lcmz33 (also covers duplicate jeh310); re-measured at HEAD 877545fc that `python3 -P -c "import agent_workflows"` from this worktree resolves a DIFFERENT worktree (`.aw/worktrees/lkexaw_attempt4`, the current editable target) and that the runner's pinned bootstrap enters `cli.main` from a lane cwd, which forces an explicit exemption.

## Goal

When `aw` (or `python -m agent_workflows`) is started inside a checkout of this toolkit whose package is not the one being imported, re-run once against that checkout's own package and say so on stderr, so in-lane evidence measures the lane's code; leave managed target repos and the runner's deliberately pinned nested calls unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: detector and re-exec

- [ ] E-01 Add `agent_workflows/checkout_pin.py` with a pure function `find_toolkit_checkout(cwd) -> Path | None` and `check_and_reexec(argv0_args) -> None`. `find_toolkit_checkout` walks `Path(cwd).resolve()` and its parents to the FIRST directory containing a `.git` entry (file OR dir; a worktree has a `.git` file), stops there, and returns it only if `<toplevel>/agent_workflows/__init__.py` exists; no `git` subprocess, no reads beyond `stat`. `check_and_reexec` compares `os.path.realpath(<toplevel>)` for EQUALITY (not ancestry) against `os.path.realpath(Path(agent_workflows.__file__).parent.parent)`. Equality is required because the editable target measured at HEAD is itself nested INSIDE the main checkout (`.aw/worktrees/lkexaw_attempt4`), so an ancestor test would wrongly accept it from the main checkout's cwd. Decision table: no toolkit checkout, or roots equal -> return silently. `AW_PINNED_CHILD=1` in env -> return silently (E-03). `AW_NO_REEXEC=1` -> print the one-line notice with "(AW_NO_REEXEC set; not re-running)" and return. Guard var `AW_REEXEC_FROM` already set -> print a notice that the re-exec did not take effect ("still importing <Y> after re-exec; continuing") and return, never exec again. Otherwise print `aw: invoked in checkout <X> but imported agent_workflows from <Y>; re-running with <X>'s package (set AW_NO_REEXEC=1 to disable)` to stderr, set `AW_REEXEC_FROM=<Y>`, prepend `<X>` to `PYTHONPATH`, and `os.execve(sys.executable, [sys.executable, "-m", "agent_workflows", *sys.argv[1:]], env)` on POSIX; on Windows (`os.name == "nt"`) use `subprocess.call` with the same argv/env and `sys.exit` with its code, since `execv` there does not replace the console process cleanly. Wrap the whole check in `try/except OSError` that returns silently, so a permissions quirk can never break the CLI.
  - Depends on: none
  - Expected outcome: new module importable, no imports beyond stdlib plus `agent_workflows` itself, no subprocess on the no-mismatch path.
  - Execution state: pending

- [ ] E-02 Call `checkout_pin.check_and_reexec()` as the FIRST statement of `cli.main`, ONLY when `argv is None`. Rationale: the console script and `__main__` both call `main()` with no argv, while every in-process caller (the test suite, the runners' in-process calls) passes an explicit list and must never have its process replaced by an `execve` (that would kill pytest). Add a short comment citing this plan id and the `argv is None` reason.
  - Depends on: E-01
  - Expected outcome: `cli.main(["--version"])` in-process from any cwd never re-execs; `aw --version` from a mismatched checkout does.
  - Execution state: pending

- [ ] E-03 Exempt the runner's pinned nested calls, and do it WITHOUT touching the fingerprinted functions. MEASURED INTERACTION (why they are NOT naturally unaffected): `runner_shared.pinned_module_argv` launches `python -P -c _AW_PIN_BOOTSTRAP`, whose `runpy.run_module("agent_workflows", run_name="__main__")` reaches `cli.main()` with `argv is None`, with cwd frequently the LANE (e.g. `driver_begin`/`driver_finalize` run in the lane worktree) and with the runner's root pinned first. There the lane toplevel contains `agent_workflows/__init__.py` and the imported package is the runner's, so without an exemption the new check WOULD re-exec into the lane's code, silently undoing the af7i6p / spec `7ckptx` A8 "driver-authoritative" contract that `tests/test_lane_import_root.py` guards. The `AW_PIN_KEEP_ROOT` env var set by `pinned_child_env` is NOT a usable signal, because the agent turn's own env is ALSO `pinned_child_env()` (`oc_runipd` `child_env = pinned_child_env()`, `agy_runipd` likewise), so keying on it would disable the fix precisely inside lane turns, which is where `lcmz33`/`jeh310` were measured. Instead, prepend `os.environ['AW_PINNED_CHILD']='1'\n` to the runpy half of `_AW_PIN_BOOTSTRAP` (after `_AW_PIN_STRIP`, so `_AW_PIN_PROBE` is unchanged). Only a process started through the bootstrap carries it; the agent's console-script `aw` does not. Do NOT edit `pinned_child_env`, `pinned_module_argv`, `assert_child_tool_identity`, or `_AW_PIN_STRIP`.
  - Depends on: E-01
  - Expected outcome: a pinned nested `aw` from a lane cwd still runs the runner's package and prints nothing extra on stderr; `tests/test_lane_import_root.py` and `tests/test_runner_shared.py` (fingerprints) still pass.
  - Execution state: pending

### Task group 2: tests and docs

- [ ] E-04 Add `tests/test_cli_checkout_reexec.py`, all subprocess-based on `tempfile` fixtures (never live worktrees). Fixture "fake checkout": `<tmp>/fake/.git` (a directory; plus a second variant where `.git` is a FILE containing `gitdir: x`) and `<tmp>/fake/agent_workflows/{__init__.py,__main__.py}` whose `__main__` prints `FAKE-RAN` and the `AW_REEXEC_FROM` value. Launcher simulating the console script: `[sys.executable, "-P", "-c", "import sys; sys.path.insert(0, REPO_ROOT); from agent_workflows.cli import main; sys.exit(main())", "--version"]` with `PYTHONPATH`/`AW_*` scrubbed from the env. Cases: (1) cwd=fake -> stdout `FAKE-RAN`, stderr carries one notice naming both roots; (2) cwd=`fake/sub/dir` -> same (walk-up works); (3) `.git`-file variant -> same; (4) loop guard: env `AW_REEXEC_FROM=x` preset -> real CLI runs (`agent-workflows` in stdout), no `FAKE-RAN`, a "did not take effect" notice, exit 0; (5) opt-out `AW_NO_REEXEC=1` -> real CLI runs, notice contains `AW_NO_REEXEC`, no `FAKE-RAN`; (6) target repo `<tmp>/target/.git` with NO `agent_workflows/` -> stderr EMPTY and stdout the real version; (7) pinned child: `runner_shared.pinned_module_argv(["--version"])` with `env=runner_shared.pinned_child_env()` and cwd=fake -> real version, stderr empty, no `FAKE-RAN` (the af7i6p regression guard); (8) in-process: `os.chdir(fake)` then `cli.main(["--version"])` returns normally in the test process (restore cwd in `finally`); (9) cwd = this repo's own root -> stderr empty.
  - Depends on: E-02, E-03
  - Expected outcome: 9 cases pass; cases 1 and 7 each demonstrated FAILING against a deliberate mutation.
  - Execution state: pending

- [ ] E-05 Add a CHANGELOG `Unreleased` entry (user-facing prose, no em/en dashes) stating that `aw` run inside a checkout of agent-workflows whose package differs from the installed one now re-runs itself with that checkout's package and prints a one-line notice, and that `AW_NO_REEXEC=1` turns the re-run off.
  - Depends on: E-02
  - Expected outcome: one entry under the existing Unreleased heading.
  - Execution state: pending

- [ ] E-06 Run the BARE suite `python3 -m pytest` (no extra flags).
  - Depends on: E-04, E-05
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The runner pins nested `aw` to ITS OWN package on purpose (plan `af7i6p`, `runner_shared.assert_child_tool_identity` aborts the run on mismatch, `ToolIdentityError`). Lane-authoritative for evidence, driver-authoritative for control plane: `tests/test_lane_import_root.py` guards both directions and must stay green.
- `pinned_child_env` and `pinned_module_argv` bodies are AST-fingerprinted in `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`; module-level string constants such as `_AW_PIN_BOOTSTRAP` are not, so the bootstrap string is the safe seam.
- `cli.main` must RETURN an int, not `sys.exit`, for in-process callers (its docstring); the re-exec path therefore only runs for `argv is None`.
- Run the suite bare (`python3 -m pytest`); CHANGELOG is user-facing, so no em/en dashes there.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `877545fc` in worktree `/tmp/opencode/graduate-top10`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `aw` console script | The console script is `from agent_workflows.cli import main`; its import resolves the editable `.pth` tree regardless of cwd. The `.pth` currently names a LANE worktree, not the main checkout. | `cat $(which aw)` -> `from agent_workflows.cli import main`; `cat .../_editable_impl_agent_workflows.pth` -> `<main>/.aw/worktrees/lkexaw_attempt4`; from this worktree `python3 -P -c "import agent_workflows;print(agent_workflows.__file__)"` -> `<main>/.aw/worktrees/lkexaw_attempt4/agent_workflows/__init__.py` |
| F-2 | HIGH | `python -m agent_workflows` from a subdir | cwd-first only helps at the checkout ROOT; from a subdirectory the `.pth` tree wins. | from `/tmp/opencode/graduate-top10/tests`: `python3 -c "import agent_workflows;print(agent_workflows.__file__)"` -> `.../lkexaw_attempt4/agent_workflows/__init__.py`; from the root -> `/tmp/opencode/graduate-top10/agent_workflows/__init__.py` |
| F-3 | MED | design | `PYTHONPATH` does beat the `.pth` entry (it precedes site-packages in `sys.path`), so a `PYTHONPATH`-prepended `-m` re-exec is sufficient. | `PYTHONPATH=/tmp/opencode/graduate-top10 python3 -P -m agent_workflows --version` -> `agent-workflows 1.3.0rc2.dev3914+g877545fc` (this tree) vs bare `aw --version` -> `...dev3851+g6a89029d` (the lane) |
| F-4 | HIGH | `runner_shared._AW_PIN_BOOTSTRAP` | Pinned nested calls enter `cli.main()` via `runpy.run_module("agent_workflows",run_name="__main__",...)`, i.e. with `argv is None`, so they are NOT naturally unaffected; and `AW_PIN_KEEP_ROOT` cannot be the exemption because agent turns also get `pinned_child_env()`. | `_AW_PIN_BOOTSTRAP` source; `oc_runipd` and `agy_runipd` both `child_env = pinned_child_env()` for the agent turn |
| F-5 | MED | nesting | The editable target is nested inside the main checkout, so root comparison must be equality, not ancestry. | F-1 path `<main>/.aw/worktrees/lkexaw_attempt4` |
| F-6 | INFO | test side | `eec572d6` (IPD `lhjsu0`) fixed tests only; no `AW_NO_REEXEC`/re-exec logic exists. | `git log --oneline -1 eec572d6`; `grep -rn "AW_NO_REEXEC" agent_workflows tests` -> no output |

## Proposed changes (ordered, validatable)

1. E-01: `agent_workflows/checkout_pin.py` detector plus guarded re-exec.
2. E-02: call it at the top of `cli.main` only when `argv is None`.
3. E-03: mark pinned bootstrap children with `AW_PINNED_CHILD=1` in `_AW_PIN_BOOTSTRAP`.
4. E-04: subprocess tests on fake checkouts, including the pinned-child regression guard.
5. E-05: CHANGELOG entry. E-06: bare suite.

## Deferred / out of scope (with reason)

- Pointing the agent turn's `PATH` at a lane-pinned `aw` wrapper (`jeh310` fix sketch (b)). The in-`aw` re-exec covers the agent turn, humans, and every other entry point at once, so a PATH shim adds a second mechanism with no extra coverage.
  - Carrier-Declined: subsumed by this plan's in-CLI re-exec, which fires in lane turns because the agent's `aw` does not pass through `_AW_PIN_BOOTSTRAP`.
- Lane-prompt / AGENTS.md instruction to use `python3 -m agent_workflows` (`jeh310` sketch (a)). Instruction alone does not hold and becomes unnecessary once the CLI self-corrects.
  - Carrier-Declined: made redundant by the self-correcting CLI; existing guidance stays accurate.
- Closing duplicate backlog `jeh310`. The executor or runner closes it alongside `lcmz33` citing this executed plan.
  - Carrier: jeh310

## Scope check

- Over-scope: none. `runner_shared.py` is touched only in the `_AW_PIN_BOOTSTRAP` string constant.
- Under-scope: a managed target repo gets no protection, by design, because it has no toolkit checkout to prefer; its `aw` is the installed release.

## Required tests / validation

- `python3 -m pytest tests/test_cli_checkout_reexec.py -o addopts="" -q`, plus mutation demos for cases 1 and 7.
- `python3 -m pytest tests/test_lane_import_root.py tests/test_runner_shared.py -o addopts="" -q` (af7i6p contract and fingerprints unchanged).
- Manual: from this checkout's `tests/` subdir, `aw --version` shows the notice and this tree's version.
- Bare `python3 -m pytest`.

## Spec / documentation sync

- CHANGELOG entry (E-05). No spec amendment: spec `7ckptx` A8 (driver-authoritative nested calls) is PRESERVED by E-03, not changed, so no `.spec.md` is in `- Scope-Paths:`.

## Open questions

### OQ-01: Should `AW_NO_REEXEC=1` also suppress the notice?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default chosen: `AW_NO_REEXEC=1` disables the re-exec but STILL prints the one-line notice, because `lcmz33`'s minimum ask is that the mismatch is never silent. The one caller that must be fully silent (the runner's pinned nested call, whose stderr lands in `DriverError` details via `runner_shared.run_checked`) uses the separate `AW_PINNED_CHILD` marker. A maintainer wanting a fully silent opt-out can add a value later without changing this design.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --stat` showing the new `agent_workflows/checkout_pin.py`; paste `grep -n "subprocess\|import " agent_workflows/checkout_pin.py` showing `subprocess` is used ONLY on the `os.name == "nt"` branch; paste the equality comparison line (`realpath(...) == realpath(...)` or `!=`), proving ancestry is not used.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `cli.main` diff showing the call guarded by `if argv is None:` as the first statement; paste the output of running from `/tmp/opencode/graduate-top10/tests` both `python3 -c "import sys; sys.argv=['aw','--version']; from agent_workflows.cli import main; sys.exit(main())"` (expected: stderr notice naming both roots, stdout this tree's version `...g<HEAD>`) and the in-process E-04 case 8 passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff agent_workflows/runner_shared.py` showing ONLY the `_AW_PIN_BOOTSTRAP` string changed; paste `python3 -m pytest tests/test_lane_import_root.py tests/test_runner_shared.py -o addopts="" -q` summary with 0 failed; paste E-04 case 7 FAILING with the `AW_PINNED_CHILD` line temporarily removed from the bootstrap (showing `FAKE-RAN` or a notice in the pinned child) and passing restored.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_cli_checkout_reexec.py -o addopts="" -q` summary showing 9 passed (or the exact count if cases are parametrized, listing them); paste case 1 FAILING with the `os.execve` call replaced by `return` locally, and passing restored.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff CHANGELOG.md` showing the entry under Unreleased, and `grep -nP "[\x{2013}\x{2014}]"` over the added lines returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of bare `python3 -m pytest` showing `N passed` and 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths in `- Scope-Paths:` via `aw commit wj5b53 -- <paths>`, never `git add -A`, and never pushes. Pasted test output must be actual runner output. STOP condition: if exempting pinned children appears to require editing `pinned_child_env`, `pinned_module_argv`, or `assert_child_tool_identity` (fingerprinted, af7i6p contract), stop and report. IRONY TO AVOID: when validating in a lane, gather evidence with `python3 -m agent_workflows` from the lane ROOT until E-02 lands, since the defect under repair affects the evidence commands themselves. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the terminal transition, which the runner owns in a managed lane and the executor otherwise performs with `aw ipd finalize`.
