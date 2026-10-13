# IPD: Add a coverage differential that finds production lines only the replayed deleted tests reach

- Date: 2026-10-11
- Kind: child
- Concern: With no citation to point the way (the defining property of the 209 uncited files, `1ub8ex` F-01), the audit needs a MECHANICAL locator for "what production behavior did this deleted file exercise that nothing surviving exercises?". Line coverage answers exactly that: lines a replayed deleted file executes that the surviving suite never executes are the strongest candidates for a lost guard, and lines both reach are candidates for a surviving guard that mutation (Order 03) must then prove. Coverage also yields, per production function, WHICH surviving tests reach it, which lets Order 07 run each mutant against only those tests instead of the whole 200 s suite: a test that never executes a function body cannot be failed by mutating that body, so the narrowing is sound for in-process reach. It is NOT sound for reach through a subprocess (an `aw ...` CLI call), whose per-test context is lost, so such functions must be flagged and probed against the full selection. Measured: `coverage` 7.15.0 is importable with the C tracer available (`python3 -m coverage debug sys` -> `coverage_version: 7.15.0`, `CTracer: available`), `pytest-cov` is not (`import pytest_cov` fails), and `coverage` is NOT a declared dependency in `pyproject.toml` (`[project.optional-dependencies] test` lists pytest, pytest-xdist, pytest-randomly, PyYAML, mypy, filelock). The repo has no coverage config (`[tool.coverage` absent from `pyproject.toml`; no `.coveragerc`).
- Scope: IN: a new `tools/replay_coverage_diff.py` with two subcommands: `baseline` runs the surviving default selection under `coverage run` (rcfile written to a temp dir: `source = agent_workflows`, `dynamic_context = test_function`, `parallel = true`, `patch = subprocess`; `COVERAGE_FILE` in the temp dir, so nothing is written into the repo) and saves a combined data file plus a JSON summary keyed by `agent_workflows/<module>.py::<qualname>` of covered lines and reaching test contexts; `diff` replays deleted files (reusing `tools/deleted_test_replay.py` from Order 02, run under the same rcfile) and reports, per deleted file, every production function with lines the replay covers, split into `exclusive_lines` (not covered by baseline) and `shared_lines`, plus the baseline's reaching tests for each function and a `subprocess_only` flag when baseline covered the function only under the empty context. The tool refuses with a clear message (exit 2) when `coverage` is not importable. Behavioral tests over a synthesized repo, skipped with a stated reason only when `coverage` is not importable. `tools/README.md` section. OUT: adding `coverage` to any dependency list (it is an audit-time tool, see OQ-01); interpreting results (Order 05).
- Scope-Paths: tools/replay_coverage_diff.py, tests/test_replay_coverage_diff.py, tools/README.md
- Scope-Exceeded: .aw/records/backlog/open/20261013-6ljil4-01-6ljil4-conftest-pytest-xdist-auto-num-workers-hookimpl-fa.backlog.md (Defect found during execution recorded to backlog as required by driver contract)
- Item-Dependencies: executed:nzzu8n
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 4
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: sk2rbf

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: sk2rbf verified (set uncitedaudit, attempt 2). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261013-6ljil4-01-6ljil4-conftest-pytest-xdist-auto-num-workers-hookimpl-fa.backlog.md: Defect found during execution recorded to backlog as required by driver contract]
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Reviewed at HEAD c7234010c. Recipe demonstrated (xdist and subprocess traced, nothing written to repo, ~1.8x overhead); paths keyed relative to each run root (raw keying made every line exclusive across nzzu8n's worktree); def lines excluded from reach (import-time empty context); stale-baseline refusal; -p no:xdist not -n 0; gate itemized. Record: .aw/records/reviews/20261011-uncitedaudit-04-sk2rbf-add-a-coverage-differential-that-finds-production-lines-only.review.md.
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Turn "what did this uncited deleted test guard?" from a reading exercise into a computed list of production functions with exclusive and shared line reach, plus the surviving tests that reach each, so per-file verdicts (Order 05), property derivation (Order 06) and mutation (Order 07) start from data.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Tool

- [x] E-01 Create `tools/replay_coverage_diff.py` with a `baseline [--out DIR] [-- <pytest args>]` subcommand and a `main(argv)` entry point.
  - Rcfile: written to `tmp = tempfile.mkdtemp()` as `[run]` with `source = agent_workflows`, `dynamic_context = test_function`, `parallel = true`, `patch = subprocess`.
  - Run: `sys.executable -m coverage run --rcfile <rc> -m pytest -o addopts="" -q -p no:randomly -p no:cacheprovider -n auto -m 'not slow and not livecorpus' <args>` with `cwd=<repo>` and env `COVERAGE_FILE=<tmp>/.coverage`, `COVERAGE_PROCESS_START=<rc>`, `PYTHONPATH=<repo>`. Trailing `<args>` are appended after the default selection; pass `-p no:xdist` (NOT `-n 0`/`-n auto` removal) to run serially, because `-n` is unrecognized once xdist is disabled (review measured `unrecognized arguments: -n`).
  - Combine: `coverage combine --rcfile <rc> -q <tmp>`, then load `coverage.CoverageData(basename=<tmp>/.coverage)`.
  - Path keying: every measured file is keyed RELATIVE to the root it ran in (`os.path.relpath(f, repo)`), and files outside that root are dropped. This is load-bearing for E-04, whose replay runs in a different root (F-06).
  - Function mapping: parse each measured `agent_workflows` module with `ast`; a function owns lines `node.body[0].lineno .. node.end_lineno`, so its `def` line is excluded, and the innermost function wins. A covered line no function owns is ignored. The key is `agent_workflows/<module>.py::<qualname>` with class-qualified names. Excluding the `def` line matters because def lines execute at import time under the empty context, and keeping them would mark every imported function as "reached" (F-05: of the functions with any covered line in a review run, 1,789 had ONLY their header covered).
  - Per function, record `lines` (sorted body lines covered), `contexts` (sorted non-empty context names reaching any body line; review measured names in the form `tests.test_m.T.test_a`, i.e. dotted module plus class plus function, with no parametrization suffix), and `subprocess_only` (body lines covered but `contexts` empty: reached only through a subprocess or at import time; review run: 157 of 1,134 reached functions).
  - Output: `<out>/baseline.json` = `{head, xdist, selection, wall_s, functions: {key: {lines, contexts, subprocess_only}}}`, written with `sort_keys=True`. `--out` defaults to a new temp dir whose path is printed.
  - Xdist check: if the combined data has no non-empty context at all, retry once with `-p no:xdist` and record `xdist: false`; otherwise `xdist: true`. At review, xdist workers WERE traced under this recipe (`-n 2` and `-n auto` both yielded per-test contexts), so the retry is a guard, not the expected path.
  - Refusal: when `import coverage` fails, exit 2 with "coverage is not installed; pip install coverage". The tool never writes under the repo; the temp data dir is removed after `baseline.json` is written unless it is the `--out` dir.
  - Depends on: none
  - Expected outcome: `python3 tools/replay_coverage_diff.py baseline --out <tmp>` completes and writes `baseline.json`, with `git status --porcelain --ignored` unchanged (so a stray ignored `.coverage*` would also show). Coverage overhead measured at review on three files: 9.8s plain vs 17.6s under the recipe (about 1.8x), so the full default selection (about 200s, `rq3q7v`) should take on the order of 6 minutes. That figure is context, not the bar.
  - Execution state: performed

- [x] E-04 Add a `diff <commit> [<path>...] [--from-json inventory.json] --baseline <dir> [--format text|json] [--timeout N]` subcommand to `tools/replay_coverage_diff.py`.
  - Replay: for each path, write the same rcfile to a fresh per-path temp dir and call `tools.deleted_test_replay.replay_file(repo_root, commit, path, timeout_s=N, python_prefix=[sys.executable, "-m", "coverage", "run", "--rcfile", rc], extra_env={"COVERAGE_FILE": <tmp>/.coverage, "COVERAGE_PROCESS_START": rc})` (the hook `nzzu8n` E-01 defines). Then `coverage combine` that dir.
  - Path keying: key measured files relative to the replay's `ReplayResult.replay_root`, NOT `repo_root`. `nzzu8n` runs every replay in its own throwaway worktree, so its absolute paths never match the baseline's. Demonstrated at review: raw-path keying classified every covered line as exclusive (`[1, 2, 5, 6, 7]`), while root-relative keying gave exclusive `[6, 7]` and shared `[1, 2, 5]`. The data stays readable after the worktree is removed.
  - Mapping: use the same function mapper as `baseline` (body lines only).
  - Output per deleted file: `{commit, path, verdict, tests_count, functions: {key: {exclusive_lines, shared_lines, baseline_contexts, baseline_subprocess_only}}}`, where `exclusive_lines = replay_lines - baseline_lines` and `shared_lines = replay_lines & baseline_lines`, both computed over BODY lines. A function absent from the baseline has `baseline_contexts: 0` and every line exclusive. `baseline_contexts` is the reaching-test COUNT; the full list stays in `baseline.json`, which Order 07 reads for its narrowed selection.
  - Exit codes and modes: refuse with exit 2 if `--baseline` lacks `baseline.json` or if `baseline.json`'s `head` differs from the current `git rev-parse HEAD`. Line numbers are only comparable on the same tree, so a stale baseline would silently misclassify. `--from-json` and the no-path usage error follow `nzzu8n`'s CLI. `--format json` writes ONLY `json.dumps([...], indent=2, sort_keys=True)`.
  - Depends on: E-01
  - Expected outcome: `diff 19313eed tests/test_run_freeze.py --baseline <tmp>` lists `agent_workflows/run_freeze.py::freeze_requirements` among touched functions, with `git status --porcelain --ignored` and `git worktree list` unchanged.
  - Execution state: performed

### Task group 2: Tests and docs

- [x] E-02 Create `tests/test_replay_coverage_diff.py`. Guard the module with `unittest.skipUnless(importlib.util.find_spec("coverage"), "coverage not installed: audit-only tool")`, the one legitimate skip (the tool's own refusal path is tested unconditionally by running `main` with `coverage` import forced to fail via `mock.patch.dict(sys.modules, {"coverage": None})` and asserting exit code 2 and the message). With coverage present: synthesize a git repo under `tmp_path` with `agent_workflows/m.py` defining `a()`, `b()` and `c()`, a surviving `tests/test_m.py` calling only `a()`, and a deleted test (committed, then removed by a trim commit) calling `a()` and `b()`; run `baseline` (serial is fine in the fixture: pass `-p no:xdist`) and `diff`. Assert: `b` appears with non-empty `exclusive_lines`; `a` has only `shared_lines`; `a`'s baseline contexts name the surviving test; a function NO test calls (`c()`) is absent from `baseline.json` even though its `def` line executed at import (pins the body-line rule); and the fixture repo's `git status --porcelain --ignored` is empty. Further cases:
  - Subprocess-only: the surviving test reaches `b()` only through `subprocess.run([sys.executable, "-c", "import agent_workflows.m as m; m.b()"])`; assert `b` is `subprocess_only: true` (demonstrated at review: the subprocess's lines carry only the empty context).
  - Stale baseline: `diff` against a `baseline.json` whose `head` differs exits 2 with a message naming both shas.
  - Root-relative keying: covered by the main case, because `nzzu8n` replays in a separate worktree. If the shared lines come out empty, keying is broken.
  Run the CLI as a subprocess with `cwd` set to the fixture repo, never changing the pytest process's cwd (xdist).
  - Depends on: E-01, E-04
  - Expected outcome: the new file passes in the default bare run on this machine (coverage installed), and each classification plus the stale-baseline refusal is asserted.
  - Execution state: performed

- [x] E-03 Add a `replay_coverage_diff.py` section to `tools/README.md`: purpose, why coverage narrows mutation selection soundly for in-process reach and not for subprocess reach, the `coverage` audit-time requirement, the temp-dir data rule, the measured baseline wall time from V-01, and the rule that a baseline is valid only for the `HEAD` it records. `tools/README.md` is user-facing prose: no em or en dashes.
  - Depends on: E-01
  - Expected outcome: README section with those points and no em or en dash.
  - Execution state: performed

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
| F-05 | Function `def` lines are covered at IMPORT time under the empty context. Counting them would mark every imported function as reached and as `subprocess_only`. | Review fixture: `def a()`/`def b()` lines (1, 5) covered under `''` only, body lines under `tests.test_m.test_a`/`tests.test_m.T.test_a`. Real-tree run over `test_lost_guard_census.py`, `test_cli.py`, `test_agy_runipd_cli.py` (65 tests): by body lines, 735 functions in-process only, 242 mixed, 157 empty-context only; 1,789 had only their header covered. |
| F-06 | Baseline and replay run in DIFFERENT roots (repo vs `nzzu8n`'s throwaway worktree), so absolute coverage paths never match. | Review probe: raw-path exclusive = all lines `[1, 2, 5, 6, 7]`; relative to each root, exclusive `[6, 7]`, shared `[1, 2, 5]`; data readable after the replay root was deleted. |
| F-07 | The recipe works with xdist and subprocesses, and writes nothing to the repo. | Review: `-n 2` -> per-test contexts present; `-n auto` real-tree run -> 58 data files combined in 1.2s, 193 measured files all inside the repo, `git status --porcelain --ignored` unchanged. `-p no:xdist -n auto` -> `unrecognized arguments: -n`. Overhead 9.8s -> 17.6s. |
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
- Under-scope: none known after review. Lines executed at import time under the empty context are deliberately not attributed to any test (F-05). A function whose only reach is a module-level statement is therefore invisible to the narrowing, which is the conservative direction: Order 07 then uses the full selection.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_replay_coverage_diff.py` passes.
- A live `baseline` run plus one `diff` on the real tree, with `git status --short` unchanged and the wall time recorded.
- Before E-01, capture an execution-start baseline: bare `python3 -m pytest`, saving the summary line and failing node ids outside the repo.
- Bare `python3 -m pytest`, actual summary pasted, no new failures versus that baseline.

## Spec / documentation sync

N/A for specs: no `.spec.md` governs `tools/` audit scripts. `tools/README.md` gains a section (E-03).

## Open questions

### OQ-01: Should `coverage` become a declared test dependency?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The tool is audit-only, the shipped suite does not import it except in this tool's own test module, which skips with a stated reason when absent, and `pyproject.toml` comments show test extras are added deliberately with a recorded reason. Least disruptive and reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git status --porcelain --ignored` before and after, identical. The pasted tail of the live `baseline` run (produced by E-01's `baseline` subcommand), with wall time, the recorded `xdist` value, the function count, and the `subprocess_only` count. A pasted `jq`/`python3 -c` excerpt of one `baseline.json` entry showing `lines`, `contexts` and `subprocess_only`.
  - Observed evidence:
```
$ git status --porcelain --ignored
?? tests/test_replay_coverage_diff.py
?? tools/replay_coverage_diff.py
!! .aw/records/history.jsonl
!! .aw/state/
!! .aw/system/workflows/assess/tools/__pycache__/
!! .aw/system/workflows/setup-repo/tools/__pycache__/
!! .pytest_cache/
!! __pycache__/
!! agent_workflows/__pycache__/
!! agent_workflows/hooks/__pycache__/
!! tests/__pycache__/
!! tests/fixtures/run_analytics/__pycache__/
!! tools/__pycache__/
!! tools/ipdrunner/__pycache__/

$ python3 tools/replay_coverage_diff.py baseline --out /tmp/sk2rbf_baseline
Baseline recorded to /tmp/sk2rbf_baseline/baseline.json
head: 1823e4e7e2367786a094ce08ebbe4bb729248f3c
xdist: True
functions: 4136
subprocess_only: 115
wall_s: 1043.18

$ git status --porcelain --ignored
?? tests/test_replay_coverage_diff.py
?? tools/replay_coverage_diff.py
!! .aw/records/history.jsonl
!! .aw/state/
!! .aw/system/workflows/assess/tools/__pycache__/
!! .aw/system/workflows/setup-repo/tools/__pycache__/
!! .pytest_cache/
!! __pycache__/
!! agent_workflows/__pycache__/
!! agent_workflows/hooks/__pycache__/
!! tests/__pycache__/
!! tests/fixtures/run_analytics/__pycache__/
!! tools/__pycache__/
!! tools/ipdrunner/__pycache__/

$ python3 -c "import json; d = json.load(open('/tmp/sk2rbf_baseline/baseline.json')); print('lines:', d['functions']['agent_workflows/run_freeze.py::freeze_requirements']['lines'][:5]); print('contexts_count:', len(d['functions']['agent_workflows/run_freeze.py::freeze_requirements']['contexts'])); print('subprocess_only:', d['functions']['agent_workflows/run_freeze.py::freeze_requirements']['subprocess_only'])"
lines: [142, 143, 151, 152, 153]
contexts_count: 100
subprocess_only: False
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" -q tests/test_replay_coverage_diff.py` summary line showing passes, not skips, on this machine; mapping of `exclusive`, `shared`, `contexts`, `subprocess_only`, the def-line exclusion, the stale-baseline refusal and the no-coverage refusal to their asserting test nodes. Sensitivity check: in a scratch copy, key paths absolutely instead of root-relative, paste the failing run, and discard the copy.
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" -q tests/test_replay_coverage_diff.py
......                                                                   [100%]
6 passed in 5.73s

Mapping to asserting test nodes:
- exclusive: tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_main_flow_exclusive_and_shared_lines
- shared: tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_main_flow_exclusive_and_shared_lines
- contexts: tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_main_flow_contexts
- subprocess_only: tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_subprocess_only_flag
- def-line exclusion: tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_def_line_exclusion_uncalled_function_absent
- stale-baseline refusal: tests/test_replay_coverage_diff.py::TestReplayCoverageDiff::test_stale_baseline_refusal
- no-coverage refusal: tests/test_replay_coverage_diff.py::TestCoverageRefusal::test_coverage_not_installed_refusal

Sensitivity check (raw/absolute path keying in scratch copy):
SENSITIVITY CHECK CONFIRMED FAILURE:
'agent_workflows/m.py::b' not found in {'/tmp/deleted_test_replay_lfqxbu3q/wt/agent_workflows/m.py::a': {'baseline_contexts': 0, 'baseline_subprocess_only': False, 'exclusive_lines': [2], 'shared_lines': []}, '/tmp/deleted_test_replay_lfqxbu3q/wt/agent_workflows/m.py::b': {'baseline_contexts': 0, 'baseline_subprocess_only': False, 'exclusive_lines': [5], 'shared_lines': []}}
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git diff tools/README.md`; pasted bare `python3 -m pytest` summary line with no new failures versus the execution-start baseline.
  - Observed evidence:
```
$ git diff -U0 tools/README.md
diff --git a/tools/README.md b/tools/README.md
index 73b988380..df8c2bf9c 100644
--- a/tools/README.md
+++ b/tools/README.md
@@ -422,0 +423,48 @@ python3 tools/deleted_test_replay.py 19313eed tests/test_run_freeze.py --timeout
+
+## `replay_coverage_diff.py`
+
+`tools/replay_coverage_diff.py` computes production line coverage differentials between surviving tests and replayed deleted tests to mechanically identify functions and lines whose test guards were lost.
+
+### Purpose and Architecture
+
+When evaluating uncited deleted tests, the tool provides a mechanical way to determine what production behavior a deleted test exercised that surviving tests do not. It runs in two phases:
+1. `baseline`: runs surviving tests under `coverage run` with dynamic test contexts and subprocess tracing, producing a `baseline.json` mapping each production function to its covered body lines and reaching test contexts.
+2. `diff`: replays deleted test files in detached worktrees via `deleted_test_replay.py` under the same coverage instrumentation, comparing replayed line reach against the baseline to categorize covered lines into `exclusive_lines` and `shared_lines`.
+
+### In-Process vs Subprocess Narrowing
+
+Coverage dynamic contexts record the specific test function names that execute each line of code. For in-process test calls, narrowing mutation probe execution to only the reaching tests is sound: a test that never executes a function body cannot have its outcome altered by mutating that body.
+
+In contrast, reach through an external subprocess (such as CLI command invocations) executes in a separate process where pytest dynamic context tracking is unavailable, recording only the empty context. Functions covered only through child processes are flagged with `subprocess_only: true` in `baseline.json`. These functions cannot be narrowed safely and must be probed against the full selection.
+
+### Audit-Time Dependency and Temp-Dir Rule
+
+The script is an audit-time tool. The `coverage` package is not declared as a runtime or shipped test dependency. If `coverage` is not installed, the tool refuses execution with exit code 2 and prints an installation message.
+
+All coverage databases, process start files, and combined data are kept strictly in temporary directories outside the repository tree and cleaned up after execution. No `.coverage*` files are ever left in the repository.
+
+### Baseline Validation and Performance
+
+A baseline is valid only for the exact git `HEAD` commit it records. Because line numbers are only comparable on the same tree, `diff` refuses with exit code 2 if `baseline.json`'s `head` differs from current `HEAD`.
+
+In validation (V-01), computing the baseline over the surviving test selection with pytest-xdist completed in 1043.18 seconds (approximately 17.4 minutes), measuring 4136 production functions of which 115 were marked `subprocess_only`.
+
+### Usage
+
+```bash
+# Generate baseline coverage for the current tree:
+python3 tools/replay_coverage_diff.py baseline --out /tmp/base
+
+# Run baseline serially or pass targeted pytest arguments:
+python3 tools/replay_coverage_diff.py baseline --out /tmp/base -- -p no:xdist tests/test_m.py
+
+# Diff a deleted test file against the baseline:
+python3 tools/replay_coverage_diff.py diff 19313eed tests/test_run_freeze.py --baseline /tmp/base
+
+# Output machine-readable diff JSON:
+python3 tools/replay_coverage_diff.py diff 19313eed tests/test_run_freeze.py --baseline /tmp/base --format json
+
+# Diff an entire inventory list from lost_guard_census.py:
+python3 tools/replay_coverage_diff.py diff 19313eed --from-json uncited_inventory.json --baseline /tmp/base --format json
+```

$ python3 -m pytest
8253 passed, 4 skipped, 18 xfailed, 3 warnings in 713.11s (0:11:53)
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the pasted `diff 19313eed tests/test_run_freeze.py --baseline <tmp> --format json` entry (produced by E-04's `diff` subcommand) for `agent_workflows/run_freeze.py::freeze_requirements` with its exclusive and shared line counts, and pasted `git status --porcelain --ignored` and `git worktree list` after the run, both unchanged.
  - Observed evidence:
```
$ python3 tools/replay_coverage_diff.py diff 19313eed tests/test_run_freeze.py --baseline /tmp/sk2rbf_baseline --format json
...
      "agent_workflows/run_freeze.py::freeze_requirements": {
        "baseline_contexts": 100,
        "baseline_subprocess_only": false,
        "exclusive_lines": [
          144,
          145,
          146,
          147
        ],
        "shared_lines": [
          142,
          143,
          151,
          152,
          153,
          154,
          155,
          156,
          157,
          158,
          159,
          160,
          161,
          162,
          166,
          167,
          168,
          169,
          170,
          171,
          172
        ]
      }
...

$ git status --porcelain --ignored
 M tools/README.md
?? tests/test_replay_coverage_diff.py
?? tools/replay_coverage_diff.py
!! .aw/records/history.jsonl
!! .aw/state/
!! .aw/system/workflows/assess/tools/__pycache__/
!! .aw/system/workflows/setup-repo/tools/__pycache__/
!! .pytest_cache/
!! __pycache__/
!! agent_workflows/__pycache__/
!! agent_workflows/hooks/__pycache__/
!! tests/__pycache__/
!! tests/fixtures/run_analytics/__pycache__/
!! tools/__pycache__/
!! tools/ipdrunner/__pycache__/

$ git worktree list
<repo-root>                                       38b2bf808 [main]
<repo-root>/.aw/worktrees/.aw-isocommit-6xj9ahwx  a283a3216 (detached HEAD)
<repo-root>/.aw/worktrees/.aw-isocommit-wdtvmbgq  522c7bc42 (detached HEAD)
<repo-root>/.aw/worktrees/1rozt5                  f52907adc [aw/lane/1rozt5]
<repo-root>/.aw/worktrees/2hgxi1                  31ef0876b [aw/lane/2hgxi1]
<repo-root>/.aw/worktrees/34iwyp                  f52907adc [aw/lane/34iwyp]
<repo-root>/.aw/worktrees/a63epo                  68b86fff5 [aw/lane/a63epo]
<repo-root>/.aw/worktrees/a63epo_attempt2         fd76c8f5f [aw/lane/a63epo_attempt2]
<repo-root>/.aw/worktrees/e25iy9                  cadea62b5 [aw/lane/e25iy9]
<repo-root>/.aw/worktrees/e25iy9_attempt2         f28eba802 [aw/lane/e25iy9_attempt2]
<repo-root>/.aw/worktrees/gradfix-review          199437f35 [review/gradfix-plan-review]
<repo-root>/.aw/worktrees/j7dsci                  6d8834886 [aw/lane/j7dsci]
<repo-root>/.aw/worktrees/j7dsci_attempt2         0659bcee5 [aw/lane/j7dsci_attempt2]
<repo-root>/.aw/worktrees/j7dsci_attempt3         27b44c3c4 [aw/lane/j7dsci_attempt3]
<repo-root>/.aw/worktrees/jj5ju1_attempt2         82d8aa390 [aw/lane/jj5ju1_attempt2]
<repo-root>/.aw/worktrees/mnwkqu                  38b2bf808 [aw/lane/mnwkqu]
<repo-root>/.aw/worktrees/mq715m                  1758e1ae9 [aw/lane/mq715m]
<repo-root>/.aw/worktrees/ncmugb                  d75cb0d15 [aw/lane/ncmugb]
<repo-root>/.aw/worktrees/p1kbhl                  6b25a8ea9 [aw/lane/p1kbhl]
<repo-root>/.aw/worktrees/p425hv                  407606a7b [aw/lane/p425hv]
<repo-root>/.aw/worktrees/r6ykw2                  53e1f8032 [aw/lane/r6ykw2]
<repo-root>/.aw/worktrees/sk2rbf                  1823e4e7e [aw/lane/sk2rbf]
<repo-root>/.aw/worktrees/thzrpo                  3b0f54e76 [aw/lane/thzrpo]
<repo-root>/.aw/worktrees/tliqz6                  868198ae3 [aw/lane/tliqz6]
<repo-root>/.aw/worktrees/y9m1ya                  06a7edeee [aw/lane/y9m1ya]
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT:
- Open questions: OQ-01 is resolved, and none remain.
- Prerequisite: `nzzu8n` executed (`- Item-Dependencies:`). Its `replay_file`, `python_prefix`, `extra_env` and `replay_root` are this plan's inputs. If any is absent at execution, that is an unsafe prerequisite: stop and report.
- Order: capture the bare-suite baseline, then E-01, E-04, E-02, E-03.
- Scope fence (a declaration, not a stop rule): the change is expected to touch only `- Scope-Paths:`. If an out-of-scope edit proves necessary, make it and justify it at finalize: `--scope-reason` per out-of-scope path, `--scope-ack` per declared path left unmodified.
- Invariants: coverage data lives only in temp dirs; a stray `.coverage*` file in the repo (tracked or ignored) is a defect in the tool to fix, not to clean by hand. Every worktree `nzzu8n` creates is gone afterwards.
- Honesty: paste the ACTUAL runner output for every claim. Never claim a result you did not run.
- Commit: only the declared paths, through `aw commit <plan> -- <paths>`. Verify `git diff --cached --name-only` first. Never `git add -A`, never `--no-verify`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner finalizes and moves the plan. By hand, run `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms. Never hand `git mv`.
