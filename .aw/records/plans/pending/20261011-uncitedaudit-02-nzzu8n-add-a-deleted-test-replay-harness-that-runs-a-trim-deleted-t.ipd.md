# IPD: Add a deleted-test replay harness that runs a trim-deleted test file against HEAD from a temp dir

- Date: 2026-10-11
- Kind: child
- Concern: The cheapest honest way to learn what a deleted test file asserted, and whether that property still holds, is to RUN it against today's code. Reading 102,815 lines of deleted test source by hand (measured: the 209 uncited files total 102,815 lines at `19313eed^`) is not affordable, and reading it without running it cannot tell a still-true property from a regressed one. Nothing in the repo replays a historical test blob today. Measured facts that shape the harness: 46 of the 209 files import `tests.support`, 4 import `tests.test_ipd_lifecycle_cli`, 4 import `tests.conformance_matrix`, 3 import `tests.fixtures`; 2 import `tests.test_run_analytics_export`, which no longer exists at HEAD; 20 import `pytest` and the rest are plain `unittest.TestCase` (`pyproject.toml` comment "the tests themselves are plain stdlib `unittest.TestCase`"). A replay must therefore run with the repo root on `sys.path` (as `conftest.py` arranges via `PYTHONPATH`) while the blob itself lives OUTSIDE the tracked tree, because writing it under `tests/` in a shared checkout would collide with co-workers and with the 4 recreated paths (`1ub8ex` F-03).
- Scope: IN: a new `tools/deleted_test_replay.py` that, given a commit and one or more deleted test paths, materializes each blob from `<commit>^:<path>` into a fresh temporary directory (never under the repo), runs it with `python3 -m pytest -o addopts="" -q -p no:cacheprovider --rootdir <repo>` and `PYTHONPATH=<repo>`, with `cwd` = repo, a per-file timeout, and reports per file one of `pass` / `fail` / `error-collect` / `error-import` / `timeout`, plus per-test outcomes (parsed from a `--junitxml` written into the temp dir), as text and JSON; behavioral tests over a synthesized `tmp_path` git repository; a `tools/README.md` section. OUT: interpreting results (Order 05); mutation (Order 03); restoring any test into `tests/`.
- Scope-Paths: tools/deleted_test_replay.py, tests/test_deleted_test_replay.py, tools/README.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: nzzu8n

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Give the audit a deterministic, side-effect-free way to execute any trim-deleted test file against the current tree and get a machine-readable verdict per file and per test.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Harness

- [ ] E-01 Create `tools/deleted_test_replay.py` with `replay_file(repo_root, commit, rel_path, timeout_s=300, python_prefix=None, extra_env=None) -> ReplayResult` (`python_prefix`, default `[sys.executable]`, lets Order 04 run the same replay as `[sys.executable, "-m", "coverage", "run", "--rcfile", rc]`; `extra_env` is merged into the child env) and a `main(argv)` CLI (`<commit> <path>... [--from-json <inventory.json>] [--format text|json] [--timeout N]`; `--from-json` accepts the `--uncited --format json` output of `tools/lost_guard_census.py` from Order 01 and replays every listed path). For each path: `git show <commit>^:<path>` into `tempfile.mkdtemp()`/<basename>; run `sys.executable -m pytest -o addopts="" -q -p no:cacheprovider -p no:randomly --rootdir <repo_root> --junitxml <tmp>/junit.xml <tmp>/<basename>` with `cwd=repo_root`, `env` = current env plus `PYTHONPATH=<repo_root>` prepended; classify: exit 0 -> `pass`; exit 1 -> `fail`; exit 2 or 4 or 5 with a collection error whose message contains `ModuleNotFoundError`/`ImportError` -> `error-import`, otherwise `error-collect`; `subprocess.TimeoutExpired` -> `timeout`. Parse the junit XML into per-test `(nodeid, outcome)` pairs. Always remove the temp dir. Never write under `repo_root`. Disabling `pytest-randomly` is deliberate for reproducible per-test outcomes in a one-shot replay; it is not the bare-suite run the repo contract governs.
  - Depends on: none
  - Expected outcome: `python3 tools/deleted_test_replay.py 19313eed tests/test_run_freeze.py` reports a verdict and 12 per-test outcomes (the file defines 12 tests at `19313eed^`), and `git status --short` is unchanged by the run.
  - Execution state: pending

### Task group 2: Tests and docs

- [ ] E-02 Create `tests/test_deleted_test_replay.py` that builds a throwaway git repo under `tmp_path` containing a tiny package `pkg/` with a function, commits test files that (a) pass, (b) fail one assertion against the current `pkg`, (c) import a module that the trim commit removes, then commits a trim deleting all three; drive `replay_file` against that repo and assert verdicts `pass`, `fail`, `error-import` respectively, the per-test outcome lists, and that the fixture repo's `git status --porcelain` is empty afterwards. Also drive `main([... , "--format", "json"])` and assert the parsed JSON and exit code. Add one `timeout` case with a test that sleeps beyond a 1s timeout. No `livecorpus` marker; never references the real trim shas.
  - Depends on: E-01
  - Expected outcome: the new file passes in the default bare run; each verdict class is exercised.
  - Execution state: pending

- [ ] E-03 Add a `deleted_test_replay.py` section to `tools/README.md` stating purpose, the temp-dir isolation rule, the verdict classes, and the `--from-json` handoff from `lost_guard_census.py --uncited --format json`.
  - Depends on: E-01
  - Expected outcome: a README section exists with those four points.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Shared checkout: never write into tracked paths another party may edit (`AGENTS.md` "Shared checkout: you are not alone in this repo"); the replay therefore stages blobs in a temp dir.
- `conftest.py` puts the repo root on `PYTHONPATH` ("os.environ[\"PYTHONPATH\"] = f\"{_REPO_ROOT}...") so subprocesses import the checkout's package; the harness reproduces that explicitly because a temp-dir test file is outside the conftest's reach.
- Tools here are stdlib-only scripts with a `main(argv)` and behavioral tests over synthesized git repos (`tools/lost_guard_census.py`, `tests/test_lost_guard_census.py`).
- P16 (`GUIDING_PRINCIPLES.md` Section 16): the new tests exercise the harness through calls and subprocesses and assert outputs; they read no production source.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The uncited population is 102,815 lines of test source, too large to read unaided. | Authoring probe summing `git show 19313eed^:<p>` line counts over the 209 uncited paths. |
| F-02 | Replayed files need repo-root imports of `tests.*` helpers. | Authoring probe of import lines: `tests.support` 46, `tests.test_ipd_lifecycle_cli` 4, `tests.conformance_matrix` 4, `tests.fixtures` 3; `tests/__init__.py` and `tests/support.py` exist at HEAD. |
| F-03 | Some replays will fail on imports that no longer exist, which is a distinct verdict from a behavioral failure. | `tests.test_run_analytics_export` imported by 2 files, absent at HEAD; `agent_workflows.wtiso_gate` imported by 1 file, absent at HEAD (`1ub8ex` F-04). |
| F-04 | A pytest run of a file outside the repo is cheap to start (~0.4s). | `time python3 -m pytest -o addopts="" -q -p no:randomly <tmpdir>/x.py` -> `real 0m0.419s` at authoring. |

## Proposed changes (ordered, validatable)

1. Replay harness with verdict classes and JSON output (E-01).
2. Synthesized-repo behavioral tests covering every verdict (E-02).
3. README section (E-03).

## Deferred / out of scope (with reason)

- Running the replay over the 209 files and interpreting results: Order 05 (`8d0qsg`).
  - Carrier: 8d0qsg
- Restoring any replayed test into `tests/`: a per-gap deliverable decided by Order 08 (`xmr5qj`) when it files items; code-pin restoration is forbidden outright (P16).
  - Carrier: xmr5qj

## Scope check

- Over-scope: none.
- Under-scope: none known. If some files need fixtures from `tests/fixtures/` relative to their own `__file__`, they will report `fail`/`error-collect`; Order 05 records that as `replay-env-limited` rather than this harness special-casing it.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_deleted_test_replay.py` passes.
- A live replay of `tests/test_run_freeze.py` at `19313eed` leaves `git status --short` unchanged.
- Bare `python3 -m pytest`, actual summary pasted, no new failures versus an execution-start baseline.

## Spec / documentation sync

N/A for specs: no `.spec.md` governs audit tooling under `tools/`. `tools/README.md` gains a section (E-03).

## Open questions

### OQ-01: Should the replay run with xdist?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. One file per process with `-o addopts=""` keeps per-test outcomes deterministic; Order 05 parallelizes across files if it needs to. The bare-suite contract in `AGENTS.md` governs suite runs, not single-file replays.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git status --short` before and after, and the pasted output of `python3 tools/deleted_test_replay.py 19313eed tests/test_run_freeze.py --format json` (produced by E-01's `main`), showing a verdict and 12 per-test outcomes.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" -q tests/test_deleted_test_replay.py` summary line, and a list of which test asserts each of the five verdict classes.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff tools/README.md`; pasted bare `python3 -m pytest` summary line with no new failures versus the execution-start baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: commit only the declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`; never `git add -A`, never `--no-verify`, never push. The harness must never write under the repository; a replay that dirties the tree is a defect to fix, not to clean up by hand. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.
