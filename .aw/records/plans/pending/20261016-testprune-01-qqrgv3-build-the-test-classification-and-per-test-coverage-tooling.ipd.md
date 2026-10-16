# IPD: Build the test classification and per-test coverage tooling and record a keep, consolidate, speed-up or delete decision for every test module

- Date: 2026-10-16
- Kind: child
- Concern: Prompt `4ul37x` (Set `testprune`) requires every prune, consolidate or speed-up decision to be driven by MEASURED per-test line and branch coverage plus a per-module decision table recorded as research. The baseline (research `offdhr`, main `6ea45c974`) is unfit to drive those decisions: it recorded lines only (`has_arcs = 0` in its `.coverage` meta), and it recorded only 3714 of 8799 collected node ids. Measured while authoring this plan: re-running `tests/test_status_set.py` (110 tests) under the same default coverage core recorded 77 contexts; the same run with `COVERAGE_CORE=ctrace` recorded 103; and with a context-propagating plugin plus `patch = subprocess` it recorded 110 of 110, including the 7 tests that only drive `support.run_cli` subprocesses. So the baseline's "parametrized cases collapse to one context" and "subprocess-only tests record no lines" are artifacts of the measurement (Python 3.14 default sysmon core plus no subprocess attribution), not properties of the suite. Children `tv72xy`, `83nnyn`, `c8bfp9` and `vgus66` all consume this measurement, so it has to be right first.
- Scope: Add reusable, uncollected tooling under `tests/tools/`: (1) a pytest plugin that switches the coverage dynamic context per test node id in the worker AND re-serializes the subprocess coverage config so children inherit the node id as their static context; (2) a runner that executes the full suite (`-m ''`) under `coverage run` with branch coverage, `patch = subprocess` and the C tracer, then combines; (3) an analyzer computing per-test line and arc sets, unique lines and unique arcs per test, identical and subset coverage groups, tests with no recorded coverage, and a per-module rollup; (4) a classifier joining that with `--durations` timings, markers (`core`, `slow`, `livecorpus`), id6/incident citations and the structure-pin scan, emitting a per-module keep / consolidate / speed-up / delete table with a reason; (5) a research record created with `aw research new` holding that table, which later children update. Adds behavioral tests for the analyzer and classifier over synthesized coverage data. Deletes, edits or re-marks NO existing test.
- Scope-Paths: tests/tools/, tests/test_testprune_tools.py, pyproject.toml, CONTRIBUTING.md, .aw/records/research/
- Item-Dependencies: executed:hguae9
- Status: to-review
- Work-Kind: chore
- Priority: high
- Set: testprune
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: qqrgv3

## Workflow history
- 2026-10-16 to-review (aw set): authored from prompt 4ul37x (Set testprune) with baseline research offdhr/7ry5kv

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

One command reproducibly produces, for every collected test node id, its line and branch (arc) coverage over `agent_workflows/` including code reached through subprocesses it spawns, and a recorded per-module keep / consolidate / speed-up / delete decision table that the later `testprune` children execute against and update.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: measurement

- [ ] E-01 Create `tests/tools/__init__.py` and `tests/tools/covctx_plugin.py`, a pytest plugin (loaded with `-p tests.tools.covctx_plugin`, never auto-loaded) whose `pytest_runtest_protocol` hookwrapper (a) calls `coverage.Coverage.current().switch_context(item.nodeid)` when a coverage object is active and (b) when `COVERAGE_PROCESS_CONFIG` is set, deserializes it with `coverage.config.CoverageConfig.deserialize`, sets `context = item.nodeid`, and writes it back with `serialize()`, restoring the original value after the test. The module name has no `test_` prefix, so it is not collected (rule from `tests/test_uncollected_test_modules.py::is_pytest_test_filename`). It must be a no-op when coverage is not running.
  - Depends on: none
  - Expected outcome: a fixture run of two tests, one in-process and one spawning `sys.executable -c "import agent_workflows.<module>"`, records both node ids as contexts with nonzero lines (the design was probed while authoring: 110/110 contexts on `tests/test_status_set.py`).
  - Execution state: pending
- [ ] E-02 Create `tests/tools/percov_run.py` (CLI: `python3 -m tests.tools.percov_run --out DIR [-- pytest-args]`) that writes a coveragerc into DIR (`[run] data_file = DIR/.coverage`, `source` = the absolute `agent_workflows` path of the checkout, `branch = true`, `parallel = true`, `patch = subprocess`), sets `COVERAGE_CORE=ctrace`, runs `coverage run --rcfile ... -m pytest tests/ -m '' -o addopts='-q -n auto --dist=worksteal' -p tests.tools.covctx_plugin --durations=0 --junitxml=DIR/junit.xml`, then `coverage combine`, and records the git HEAD, python version, coverage version, core, worker count and wall time in `DIR/meta.json`. Add `coverage>=7.10` to the `test` extra and the PEP 735 `dev` group in `pyproject.toml` (the `patch = subprocess` option needs 7.10; 7.15 is installed) only if `hguae9` has not already added it.
  - Depends on: E-01
  - Expected outcome: a full-suite run produces a combined `.coverage` with `has_arcs = 1`, a context count equal to the collected node-id count minus tests that execute no `agent_workflows` line at all, and `meta.json`.
  - Execution state: pending
- [ ] E-03 Create `tests/tools/percov_analyze.py` (`python3 -m tests.tools.percov_analyze DIR`) that reads the combined data via `coverage.CoverageData` (`contexts_by_lineno`, `arcs`) and writes `DIR/percov.json` with, per node id: line count, arc count, unique lines, unique arcs (covered by no other node id), the set of node ids whose line-and-arc set equals or strictly contains it (identical / subset groups, capped per test), and flags `no_coverage` (collected in `junit.xml` but no context). Per module: test count, zero-unique-line count, zero-unique-arc count, no-coverage count, union lines/arcs contributed only by that module. Also union totals (lines, arcs, percent of `agent_workflows/` statements and branches), so `vgus66` can diff before and after with the same script (`--compare OTHER_DIR` prints every line and arc covered before and not after).
  - Depends on: E-02
  - Expected outcome: `percov.json` plus a printed summary of totals; `--compare` on two identical directories prints zero lost lines and zero lost arcs.
  - Execution state: pending

### Task group 2: classification and decision table

- [ ] E-04 Create `tests/tools/pinscan.py` (`python3 -m tests.tools.pinscan`) that reproduces and extends the baseline structure-pin scan as a reviewable candidate list of (file, line, pattern-id, enclosing test function): `inspect.getsource*`, `ast.parse`/`ast.walk` over a module `__file__`, `read_text` of a path under the real `agent_workflows/` (`REPO_ROOT / "agent_workflows"`, `Path(<mod>.__file__)`, `rglob("*.py")` over the package), `hasattr`/`not hasattr` on a production module or class, `assertIs` between host-module attributes (`oc_runipd`/`agy_runipd` vs `runner_shared`), `__module__`/`__doc__` assertions, `not in sys.modules`, `len(<mod>.<CONST>) ==`, and `.md` docs read for prose. It emits candidates only; it never decides (child `tv72xy` classifies by reading). It reads test files, not production source, so it is test tooling and not a P16 pin.
  - Depends on: none
  - Expected outcome: a JSON and table listing; on the authoring tree the union file count is reproduced (88 files at authoring by the union of these patterns; 56 by the baseline's original pattern set).
  - Execution state: pending
- [ ] E-05 Create `tests/tools/classify.py` (`python3 -m tests.tools.classify DIR`) that joins `percov.json`, per-test durations from `junit.xml`, markers from `pytest --collect-only` (`core`, `slow`, `livecorpus`), defect citations (a backlog/plan id6 that resolves through `aw find` or an incident/run id in the test's docstring, name or body) and `pinscan` hits, and proposes per test and per module one of `keep`, `consolidate`, `speed-up`, `delete-candidate` with a machine-stated reason. Fixed rules: `livecorpus`, `aw.agent/v1` conformance, exit-code contract, leak-sanitizer, release-gate and lifecycle-gate tests are never `delete-candidate`; a test citing a defect id is `consolidate` at most; a `no_coverage` test is never classed marginal by metric and is flagged `read-required`; a test over 2s wall is at least `speed-up`; a test with zero unique lines AND zero unique arcs AND an identical-coverage peer is `consolidate`; a `pinscan` hit is `read-required` (pin) for `tv72xy`. Output is a markdown table per module (module, tests, wall seconds, unique lines, unique arcs, proposed disposition, reason, owner child id6) and a per-test JSON.
  - Depends on: E-03, E-04
  - Expected outcome: every collected module appears exactly once; every row names an owner child (`tv72xy` delete pins, `83nnyn` consolidate, `c8bfp9` speed-up, or `keep`).
  - Execution state: pending
- [ ] E-06 Write behavioral tests `tests/test_testprune_tools.py` that build a small synthetic `CoverageData` (via `coverage.CoverageData.add_arcs` with `set_context`) and a synthetic junit file in `tmp_path`, then drive `percov_analyze` and `classify` and assert exact unique-line/arc counts, identical/subset grouping, `no_coverage` detection, `--compare` lost-line output, and the fixed classifier rules (livecorpus never deleted; id6-citing test capped at consolidate). One test drives `covctx_plugin` through `pytester`-free subprocess `coverage run -m pytest` on a two-test fixture directory and asserts both contexts exist. No assertion reads tool or production source.
  - Depends on: E-05
  - Expected outcome: the new module passes and is collected (`tests/test_uncollected_test_modules.py` stays green).
  - Execution state: pending

### Task group 3: record and document

- [ ] E-07 Run E-02, E-03, E-05 on the post-`hguae9` main, then create the decision-table research record with `AW_NO_REEXEC=1 aw research new --kind assessment --slug test-prune-decision-table --set testprune --topic testing --summary "<counts>" --apply` (setid `testprune` is 9 characters) and fill it with: measurement metadata, union line and branch totals, per-module table from E-05, counts per proposed disposition, the `read-required` list (no-coverage tests and pin candidates), the 2s-plus list, and an empty "Recorded deletions" table (`node id | category | reason | child id6 | commit`) that later children append to. Then run `aw research index`. Update research `offdhr` only by appending a pointer line naming the new record and the measurement correction (lines-only, sysmon under-recording).
  - Depends on: E-06
  - Expected outcome: the new research file exists, `aw research index --check` passes, and every module has a row.
  - Execution state: pending
- [ ] E-08 Document the tooling in `CONTRIBUTING.md` (one short section: the commands for run, analyze, compare, classify, pinscan; that output directories are scratch and not committed; that subprocess attribution relies on `patch = subprocess`; runtime about 1.3 to 2x an uninstrumented full run). No em or en dashes in that user-facing prose.
  - Depends on: E-07
  - Expected outcome: the section exists and its commands match the CLIs as built.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Uncollected helpers live beside tests with a non-`test_` name (`tests/support.py`, `tests/conformance_matrix.py`, `tests/deselect_notice.py`); `tests/test_uncollected_test_modules.py` fails on a tracked `test_*.py` that pytest does not collect, so the tools must not use that prefix.
- Prior art in `tools/replay_coverage_diff.py` (`_make_rc_content`: `dynamic_context = test_function`, `patch = subprocess`; `_collect_function_coverage` marks `subprocess_only` when no context exists). That tool keys contexts with coverage's own `test_function` dynamic context, which does not propagate into children, which is exactly the gap E-01 closes; it is retained, not replaced, because it serves the deleted-test replay audit.
- `conftest.pytest_xdist_auto_num_workers` caps at min(6, cpus/2); `addopts` must be overridden with `-o addopts=...` to run `-m ''`.
- Research records are created only through `aw research new` and indexed with `aw research index` (`.aw/records/research/README.md`).
- P16 (`GUIDING_PRINCIPLES.md` "Test outcomes and behavior"): new tests exercise the tooling on synthesized inputs; `pinscan` reads test files, which is outside P16's production-source prohibition.

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Baseline is lines only | `/tmp/opencode/ctx/.coverage` meta `has_arcs = 0`; research `offdhr` "lines only" |
| F-2 | Baseline recorded 3714 of 8799 collected node ids; 5085 missing, 1848 of them parametrized and 3237 not | authoring-time join of `pytest tests/ -m '' --collect-only -q` (8799) against the baseline context table |
| F-3 | The default core on Python 3.14.6 / coverage 7.15.0 under-records dynamic contexts | `tests/test_status_set.py`: 77/110 contexts default, 103/110 with `COVERAGE_CORE=ctrace`; `tests/test_descriptive_refusal_hoist.py` with ctrace: 996 contexts for 997 tests, 995 parametrized, so parametrized cases do NOT collapse under ctrace |
| F-4 | Subprocess children can be attributed to the spawning test | probe: re-serialized `COVERAGE_PROCESS_CONFIG` with `context=<nodeid>` gave the child's lines that context; plugin plus `patch=subprocess` gave 110/110 on `tests/test_status_set.py` including the 7 `support.run_cli` tests, 900628 arcs, 34 MB data file |
| F-5 | 287 test modules spawn subprocesses (`subprocess.run/Popen/check_*`, `support.run_cli`, `run_installer`) | `rg -l` over `tests/test_*.py` |
| F-6 | Full uninstrumented run 565s; instrumented lines-only run 735s | research `7ry5kv`, `offdhr` |

## Proposed changes (ordered, validatable)

E-01 plugin -> E-02 runner -> E-03 analyzer (measurement); E-04 pin scan and E-05 classifier (decision); E-06 tool tests; E-07 research record; E-08 docs.

## Deferred / out of scope (with reason)

- Deleting, consolidating, or speeding up any test.
  - Carrier: tv72xy, 83nnyn, c8bfp9 (Set `testprune` Orders 02 to 04).
- Mutation spot-check, flake check, and before/after parity proof.
  - Carrier: vgus66 (Set `testprune` Order 05), which reuses `percov_analyze --compare` from E-03.
- Replacing `tools/replay_coverage_diff.py` with the new plugin.
  - Carrier-Declined: it serves the executed deleted-test replay audit and still works for its purpose; merging tools is refactoring with no measured defect.

## Scope check

- Over-scope: none.
- Under-scope: none; the per-module table includes every collected module, so later children never re-derive classification.

## Required tests / validation

Per V-items: `python3 -m pytest tests/test_testprune_tools.py tests/test_uncollected_test_modules.py -o addopts="" -q -n 0`; bare `python3 -m pytest` (core tier from `hguae9`); one full instrumented run pasted with its summary.

## Spec / documentation sync

No spec governs test tooling. `CONTRIBUTING.md` documented in E-08; research `offdhr` gets a pointer line (append only).

## Open questions

### OQ-01: Is the instrumented full run affordable?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence: the lines-only instrumented run took 735s against 565s uninstrumented (F-6); branch tracking and subprocess measurement add cost and data size (34 MB for one module, F-4). The run is a one-off measurement repeated twice (here and in `vgus66`), not a gate, so a run of up to about 30 minutes is acceptable; E-02 records the actual wall time in `meta.json`.

### OQ-02: Should the plugin use coverage's built-in `dynamic_context = test_function` instead?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence: no. `test_function` labels by function name, not by pytest node id, so parametrized cases and classes merge, and it does not reach subprocess children. Node-id contexts via `switch_context` plus config re-serialization are what F-3 and F-4 measured to work.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of the two-test fixture run (code path: `covctx_plugin` hookwrapper created by E-01) listing both node-id contexts with their nonzero line counts, the subprocess test included.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `meta.json`, the pytest summary line of the instrumented full run, and a query showing `has_arcs = 1` and the context count next to the collected node-id count (code path: `percov_run` from E-02).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `percov_analyze` summary (union lines, union arcs, percents, zero-unique and no-coverage counts) and pasted `--compare DIR DIR` output showing zero lost lines and arcs.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `pinscan` summary with per-pattern file counts and the total file count.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted disposition counts, pasted check that every collected module appears exactly once, and five sample rows including one `livecorpus` module shown as `keep`.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted pytest output for `tests/test_testprune_tools.py` and `tests/test_uncollected_test_modules.py` with pass counts.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: the new research file path, its summary line, and pasted `aw research index --check` output.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: the `CONTRIBUTING.md` diff and a pasted `--help` from each CLI matching the documented commands.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and human approval, after `hguae9` is executed (Item-Dependencies), in an isolated worktree (`aw work begin qqrgv3`); commit via `aw commit qqrgv3 -- <paths>` in small batches (tooling, tests, research, docs); never push or tag; publish via `aw integration-lock -- git merge --ff-only <branch>`. No existing test is changed, so the `core` tier coverage defined by `hguae9` cannot drop; confirm with bare `python3 -m pytest`. Paste ACTUAL output in each V-item, then move to `executed/` through the lifecycle tooling once `aw ipd lint --phase pre-transition` conforms.
