# IPD: Add a coverage differential that finds production lines only the replayed deleted tests reach

- Date: 2026-10-11
- Kind: child
- Concern: With no citation to point the way (the defining property of the 209 uncited files, `1ub8ex` F-01), the audit needs a MECHANICAL locator for "what production behavior did this deleted file exercise that nothing surviving exercises?". Line coverage answers exactly that: lines a replayed deleted file executes that the surviving suite never executes are the strongest candidates for a lost guard, and lines both reach are candidates for a surviving guard that mutation (Order 03) must then prove. Coverage also yields, per production function, WHICH surviving tests reach it, which lets Order 07 run each mutant against only those tests instead of the whole 200 s suite: a test that never executes a function body cannot be failed by mutating that body, so the narrowing is sound for in-process reach. It is NOT sound for reach through a subprocess (an `aw ...` CLI call), whose per-test context is lost, so such functions must be flagged and probed against the full selection. Measured: `coverage` 7.15.0 is importable with the C tracer available (`python3 -m coverage debug sys` -> `coverage_version: 7.15.0`, `CTracer: available`), `pytest-cov` is not (`import pytest_cov` fails), and `coverage` is NOT a declared dependency in `pyproject.toml` (`[project.optional-dependencies] test` lists pytest, pytest-xdist, pytest-randomly, PyYAML, mypy, filelock). The repo has no coverage config (`[tool.coverage` absent from `pyproject.toml`; no `.coveragerc`).
- Scope: IN: a new `tools/replay_coverage_diff.py` with two subcommands: `baseline` runs the surviving default selection under `coverage run` (rcfile written to a temp dir: `source = agent_workflows`, `dynamic_context = test_function`, `parallel = true`, `patch = subprocess`; `COVERAGE_FILE` in the temp dir, so nothing is written into the repo) and saves a combined data file plus a JSON summary keyed by `agent_workflows/<module>.py::<qualname>` of covered lines and reaching test contexts; `diff` replays deleted files (reusing `tools/deleted_test_replay.py` from Order 02, run under the same rcfile) and reports, per deleted file, every production function with lines the replay covers, split into `exclusive_lines` (not covered by baseline) and `shared_lines`, plus the baseline's reaching tests for each function and a `subprocess_only` flag when baseline covered the function only under the empty context. The tool refuses with a clear message (exit 2) when `coverage` is not importable. Behavioral tests over a synthesized repo, skipped with a stated reason only when `coverage` is not importable. `tools/README.md` section. OUT: adding `coverage` to any dependency list (it is an audit-time tool, see OQ-01); interpreting results (Order 05).
- Scope-Paths: tools/replay_coverage_diff.py, tests/test_replay_coverage_diff.py, tools/README.md
- Item-Dependencies: executed:nzzu8n
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 4
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: sk2rbf

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Turn "what did this uncited deleted test guard?" from a reading exercise into a computed list of production functions with exclusive and shared line reach, plus the surviving tests that reach each, so per-file verdicts (Order 05), property derivation (Order 06) and mutation (Order 07) start from data.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Tool

- [ ] E-01 Create `tools/replay_coverage_diff.py` with a `baseline [--out DIR] [-- <pytest args>]` subcommand. It writes the rcfile described in Scope to a temp dir and runs `sys.executable -m coverage run --rcfile <rc> -m pytest -o addopts="" -q -p no:randomly -n auto -m 'not slow and not livecorpus' <args>` with `COVERAGE_FILE=<tmp>/.coverage`, `COVERAGE_PROCESS_START=<rc>` and `PYTHONPATH=<repo>`, then `coverage combine`, loads `coverage.CoverageData`, maps covered lines to functions by parsing each `agent_workflows` module with `ast` (function `lineno..end_lineno`, innermost function wins), and writes `<out>/baseline.json` (`{head, xdist, functions: {key: {lines, contexts, subprocess_only}}}`). If xdist workers are not traced (zero measured files beyond the controller), it retries once with `-p no:xdist` and records `xdist: false`. When `import coverage` fails it exits 2 with "coverage is not installed; pip install coverage". It never writes under the repo.
  - Depends on: none
  - Expected outcome: `python3 tools/replay_coverage_diff.py baseline --out <tmp>` completes and writes `baseline.json`, with `git status --short` unchanged.
  - Execution state: pending

- [ ] E-04 Add a `diff <commit> <path>... [--from-json inventory.json] --baseline <dir> [--format text|json]` subcommand to `tools/replay_coverage_diff.py`. For each path it calls `tools.deleted_test_replay.replay_file(..., python_prefix=[sys.executable, "-m", "coverage", "run", "--rcfile", rc], extra_env={"COVERAGE_FILE": ..., "COVERAGE_PROCESS_START": rc})` (the hook `nzzu8n` E-01 defines), maps the replay's covered lines to functions with the same mapper as `baseline`, and emits per deleted file the replay verdict plus, per touched function, `exclusive_lines`, `shared_lines`, the baseline `contexts` count and `subprocess_only`.
  - Depends on: E-01
  - Expected outcome: `diff 19313eed tests/test_run_freeze.py --baseline <tmp>` lists `agent_workflows/run_freeze.py::freeze_requirements` among touched functions, with `git status --short` unchanged.
  - Execution state: pending

### Task group 2: Tests and docs

- [ ] E-02 Create `tests/test_replay_coverage_diff.py`. Guard the module with `unittest.skipUnless(importlib.util.find_spec("coverage"), "coverage not installed: audit-only tool")`, the one legitimate skip (the tool's own refusal path is tested unconditionally by running `main` with `coverage` import forced to fail via `mock.patch.dict(sys.modules, {"coverage": None})` and asserting exit code 2 and the message). With coverage present: synthesize a git repo under `tmp_path` with `agent_workflows/m.py` defining `a()` and `b()`, a surviving `tests/test_m.py` calling only `a()`, and a deleted test (committed, then removed by a trim commit) calling `a()` and `b()`; run `baseline` (serial is fine in the fixture: pass `-p no:xdist`) and `diff`; assert `b` appears with non-empty `exclusive_lines` and `a` with only `shared_lines`, `a`'s contexts name the surviving test, and the fixture repo's `git status --porcelain` is empty. Add one case where the surviving test reaches `b()` only through `subprocess.run([sys.executable, "-c", "import agent_workflows.m as m; m.b()"])` and assert `b` is `subprocess_only: true`.
  - Depends on: E-01, E-04
  - Expected outcome: the new file passes in the default bare run on this machine (coverage installed) and each classification is asserted.
  - Execution state: pending

- [ ] E-03 Add a `replay_coverage_diff.py` section to `tools/README.md`: purpose, why coverage narrows mutation selection soundly for in-process reach and not for subprocess reach, the `coverage` audit-time requirement, the temp-dir data rule, and the measured baseline wall time from V-01.
  - Depends on: E-01
  - Expected outcome: README section with those points.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Runtime dependencies are minimal by policy (`pyproject.toml`: `dependencies = ["filelock>=3"]`, with comments explaining why each test-only tool lives in the `test` extra). An audit-only script under `tools/` that refuses cleanly without `coverage` keeps that policy.
- `conftest.py` sets `PYTHONPATH` to the repo root so CLI subprocesses import the checkout; `patch = subprocess` makes those subprocesses measured.
- Narrowed and instrumented runs use `-o addopts=""`; bare-suite contract governs suite validation runs (repo-local development contract in `AGENTS.md`).
- P16: tests drive the tool over synthesized repos and assert outputs; the tool's `ast` mapping of line numbers to functions is the tool's behavior, not a test pin.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `coverage` is available but undeclared; `pytest-cov` is absent. | `python3 -m coverage debug sys` -> `coverage_version: 7.15.0`, `CTracer: available`; `python3 -c "import pytest_cov"` fails; `pyproject.toml` `test` extra lists no coverage package. |
| F-02 | Coverage 7.15 supports measuring subprocesses via config. | `coverage.config` defines the `run:patch` list option and checks `"subprocess" in self.patch` (read from the installed package at authoring). |
| F-03 | Mutation narrowing by reaching tests is sound only for in-process reach. | A function body that a test never executes cannot change that test's outcome when mutated; a subprocess's coverage carries the empty dynamic context, so its reaching test is unknown. |
| F-04 | No coverage config exists to collide with. | `grep -n "\[tool.coverage" pyproject.toml` -> no match; no `.coveragerc` or `setup.cfg` at the repo root. |

## Proposed changes (ordered, validatable)

1. `baseline` subcommand with temp-dir data and refusal without coverage (E-01).
2. `diff` subcommand reusing Order 02's replay (E-04).
3. Synthesized-repo tests including the subprocess-only flag (E-02).
4. README section (E-03).

## Deferred / out of scope (with reason)

- Declaring `coverage` in the `test` extra: not needed for the shipped suite, which this Set does not change.
  - Carrier-Declined: Won't-fix in this Set; the tool refuses cleanly without it and its tests skip with a stated reason, so no hidden dependency is introduced.
- Interpreting the diff per file: Order 05 (`8d0qsg`).
  - Carrier: 8d0qsg

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_replay_coverage_diff.py` passes.
- A live `baseline` run plus one `diff` on the real tree, with `git status --short` unchanged and the wall time recorded.
- Bare `python3 -m pytest`, actual summary pasted, no new failures versus an execution-start baseline.

## Spec / documentation sync

N/A for specs: no `.spec.md` governs `tools/` audit scripts. `tools/README.md` gains a section (E-03).

## Open questions

### OQ-01: Should `coverage` become a declared test dependency?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The tool is audit-only, the shipped suite does not import it except in this tool's own test module, which skips with a stated reason when absent, and `pyproject.toml` comments show test extras are added deliberately with a recorded reason. Least disruptive and reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git status --short` before and after, and the pasted tail of the live `baseline` run (produced by E-01's `baseline` subcommand) with wall time and the recorded `xdist` value.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" -q tests/test_replay_coverage_diff.py` summary line showing passes, not skips, on this machine; mapping of `exclusive`, `shared`, `contexts`, `subprocess_only` and the no-coverage refusal to their asserting test nodes.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff tools/README.md`; pasted bare `python3 -m pytest` summary line with no new failures versus the execution-start baseline.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the pasted `diff 19313eed tests/test_run_freeze.py --baseline <tmp> --format json` entry (produced by E-04's `diff` subcommand) for `agent_workflows/run_freeze.py::freeze_requirements` with its exclusive and shared line counts, and pasted `git status --short` after the run unchanged.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: commit only the declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`; never `git add -A`, never `--no-verify`, never push. Coverage data must live in a temp dir; a stray `.coverage*` file in the repo is a defect in the tool. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.
