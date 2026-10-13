# IPD: Add a deleted-test replay harness that runs a trim-deleted test file against HEAD from a temp dir

- Date: 2026-10-11
- Kind: child
- Concern: The cheapest honest way to learn what a deleted test file asserted, and whether that property still holds, is to RUN it against today's code. Reading 102,815 lines of deleted test source by hand (measured: the 209 uncited files total 102,815 lines at `19313eed^`) is not affordable, and reading it without running it cannot tell a still-true property from a regressed one. Nothing in the repo replays a historical test blob today. Measured facts that shape the harness: 46 of the 209 files import `tests.support`, 4 import `tests.test_ipd_lifecycle_cli`, 4 import `tests.conformance_matrix`, 3 import `tests.fixtures`; 2 import `tests.test_run_analytics_export`, which no longer exists at HEAD; 20 import `pytest` and the rest are plain `unittest.TestCase` (`pyproject.toml` comment "the tests themselves are plain stdlib `unittest.TestCase`"). A replay must therefore run with the repo root on `sys.path` while the blob itself lives OUTSIDE the invoking checkout, because writing it under `tests/` in a shared checkout would collide with co-workers and with the recreated paths (`1ub8ex` F-03). Review measured that a BARE temp dir is not a faithful environment: 85 of the 298 test files the trim deleted resolve the repo from `Path(__file__)` (most often `REPO_ROOT = Path(__file__).resolve().parents[1]`), and the root `conftest.py` home sandbox (`AW_HOME`/`XDG_CONFIG_HOME`) does not apply to a file outside the rootdir. So each replay runs inside a throwaway detached `git worktree` of `HEAD` created under a temp dir, with the blob written at its ORIGINAL repo-relative path; that is the same isolation `g55j1e` (Order 03) uses.
- Scope: IN: a new `tools/deleted_test_replay.py` that, given a commit and one or more deleted test paths, materializes each blob from `<commit>^:<path>` at `<path>` inside a fresh detached worktree of `HEAD` under `tempfile.mkdtemp()` (never inside the invoking checkout's tree), runs it with `python3 -m pytest -o addopts="" -q -p no:cacheprovider -p no:randomly` with `cwd` = the worktree and `PYTHONPATH=<worktree>`, a per-file timeout that kills the whole process group, and reports per file one of `pass` / `fail` / `error-import` / `error-collect` / `no-tests` / `timeout` / `error`, plus per-test outcomes (parsed from a `--junitxml` written into the temp dir), as text and JSON; behavioral tests over a synthesized `tmp_path` git repository; a `tools/README.md` section. OUT: interpreting results (Order 05); mutation (Order 03); restoring any test into `tests/`.
- Scope-Paths: tools/deleted_test_replay.py, tests/test_deleted_test_replay.py, tools/README.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: nzzu8n
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007. Reviewed at HEAD d2bbf1ded. Replay moved from a bare temp dir to a detached worktree of HEAD with the blob at its original path (demonstrated 6 spurious failures and no home sandbox otherwise; --rootdir cost ~65s/file); verdict set gains no-tests and error; process-group timeout kill; seven-case fixture plus CLI --from-json subprocess test; live count re-derived; gate itemized. Record: .aw/records/reviews/20261011-uncitedaudit-02-nzzu8n-add-a-deleted-test-replay-harness-that-runs-a-trim-deleted-t.review.md.
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Give the audit a deterministic, side-effect-free way to execute any trim-deleted test file against the current tree and get a machine-readable verdict per file and per test.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Harness

- [x] E-01 Create `tools/deleted_test_replay.py` with `replay_file(repo_root, commit, rel_path, timeout_s=300, python_prefix=None, extra_env=None) -> ReplayResult` and a `main(argv)` CLI.
  - Hooks for Order 04 (`sk2rbf` E-04): `python_prefix`, default `[sys.executable]`, lets the same replay run as `[sys.executable, "-m", "coverage", "run", "--rcfile", rc]`; `extra_env` is merged into the child env last.
  - CLI: `<commit> [<path>...] [--from-json <inventory.json>] [--format text|json] [--timeout N]`. `--from-json` accepts the `--uncited --format json` output of `tools/lost_guard_census.py` (Order 01, a JSON list of records each carrying `path`; `1ub8ex` E-01) and replays every listed `path` in list order after any positional paths. No path at all is a usage error (exit 2 via `parser.error`). Exit 0 for any set of verdicts. `--format json` writes ONLY `json.dumps([result, ...], indent=2, sort_keys=True)`; text prints one line per file (verdict, counts) and a totals line per verdict.
  - Isolation: `tmp = tempfile.mkdtemp()`; `git -C <repo_root> worktree add --detach <tmp>/wt HEAD`; write `git show <commit>^:<rel_path>` to `<tmp>/wt/<rel_path>` (creating parents). If that path exists at `HEAD`, set `overwrote_head_path: true`. The replay sees COMMITTED `HEAD` only; uncommitted edits in the invoking checkout are not seen, and `ReplayResult.head` records the sha. Rationale: `Path(__file__)`-relative repo lookups and the root `conftest.py` (home sandbox, `PYTHONPATH`) then behave as they did in-tree (F-02, F-05).
  - Run: `python_prefix + ["-m", "pytest", "-o", "addopts=", "-q", "-p", "no:cacheprovider", "-p", "no:randomly", "--junitxml", "<tmp>/junit.xml", rel_path]` with `cwd=<tmp>/wt`, `env` = current env plus `PYTHONPATH=<tmp>/wt` prepended plus `extra_env`, `start_new_session=True`, stdout/stderr captured. On `timeout_s`, `os.killpg` the group with SIGKILL and reap it, so subprocess-spawning tests leave no orphans (F-06). Disabling `pytest-randomly` is deliberate for reproducible per-test outcomes in a one-shot replay; it is not the bare-suite run the repo contract governs.
  - Classify (exit codes per pytest `ExitCode`): timeout -> `timeout`; exit 0 -> `pass`; exit 1 -> `fail`; exit 2 with a junit `<error>` whose text contains `ModuleNotFoundError` or `ImportError` -> `error-import`; any other exit 2 with a junit `<error>` -> `error-collect`; exit 5 -> `no-tests`; anything else (3 internal error, 4 usage error, a signal, or exit 1/2 with no parsable junit XML) -> `error`. Exit-2-plus-junit-`<error>` text for an import failure was demonstrated at review (F-07).
  - Per-test outcomes: parse the junit XML into sorted `(nodeid, outcome)` pairs, `nodeid = <classname>::<name>`, outcome `passed`/`failed`/`error`/`skipped` from the child element. For `error-import`/`error-collect`, set `error_line` to the first line of the error text that names the exception (Order 05 cites it).
  - Result fields: `commit`, `path`, `head`, `verdict`, `exit_code`, `tests` (the pairs), `counts` (per outcome), `error_line`, `overwrote_head_path`, `replay_root` (the worktree path used, so Order 04 can relativize coverage file paths after the worktree is gone), `wall_s`.
  - Cleanup: a `finally` always runs `git -C <repo_root> worktree remove --force <tmp>/wt`, `git -C <repo_root> worktree prune`, then `shutil.rmtree(tmp, ignore_errors=True)`. Apart from git's own worktree metadata, which this cleanup removes, nothing is written to the invoking checkout.
  - Depends on: none
  - Expected outcome: `python3 tools/deleted_test_replay.py 19313eed tests/test_run_freeze.py --format json` reports a verdict and one per-test outcome for every test pytest collects from that blob, with the count re-derived at execution (at review the blob collected 12 and passed: `12 passed in 0.15s`; context, not the bar). `git status --short` and `git worktree list` of the invoking checkout are identical before and after.
  - Execution state: performed

### Task group 2: Tests and docs

- [x] E-02 Create `tests/test_deleted_test_replay.py` (import as `from tools.deleted_test_replay import ...`, the pattern `tests/test_lost_guard_census.py` uses). A fixture builds a throwaway git repo under a temp dir (`git init -b main`, local `user.name`/`user.email`) containing a tiny package `pkg/` with a function and a data file, plus a root `conftest.py` that sets an env var `REPLAY_CONFTEST=1`. It commits test files that:
  - (a) pass;
  - (b) fail one assertion against the current `pkg`;
  - (c) import a module `pkg.gone` that the trim commit removes;
  - (d) have a syntax error;
  - (e) define no tests;
  - (f) sleep 30s inside one test;
  - (g) read `Path(__file__).resolve().parents[1] / "pkg" / "data.txt"` and assert `os.environ["REPLAY_CONFTEST"] == "1"`.
  Then it commits a trim deleting all seven. Drive `replay_file` per file (timeout 1s for (f), default otherwise) and assert verdicts `pass`, `fail`, `error-import`, `error-collect`, `no-tests`, `timeout`, `pass` respectively. Also assert the per-test `(nodeid, outcome)` lists for (a) and (b), a non-empty `error_line` naming `ModuleNotFoundError` for (c), and that after every call the fixture repo's `git status --porcelain` is empty and `git worktree list` holds only the main worktree. Add one `overwrote_head_path: true` case: a deleted path re-created at `HEAD`. Run the CLI as a subprocess `[sys.executable, <tool path>, <trim sha>, "--from-json", <inv.json>, "--format", "json"]`, where `<inv.json>` is a list of `{"path": ...}` records written to `tmp_path`; assert exit 0 and that the parsed JSON has one result per listed path, in order. Also assert that no path exits 2. No `livecorpus` marker; never reference the real trim shas.
  - Depends on: E-01
  - Expected outcome: the new file passes in the default bare run (under xdist, so no test changes the pytest process's cwd), and every verdict class except `error` has a dedicated case. `error` is the residual class, reachable only through a pytest internal error or a missing junit file, and is deliberately not simulated.
  - Execution state: performed

- [x] E-03 Add a `deleted_test_replay.py` section to `tools/README.md` stating purpose, the isolation rule (a throwaway worktree of committed `HEAD`, never the invoking checkout), the seven verdict classes, and the `--from-json` handoff from `lost_guard_census.py --uncited --format json`. `tools/README.md` is user-facing prose: no em or en dashes.
  - Depends on: E-01
  - Expected outcome: a README section exists with those four points and contains no em or en dash.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Shared checkout: never write into tracked paths another party may edit (`AGENTS.md` "Shared checkout: you are not alone in this repo"); the replay therefore stages blobs in a throwaway worktree under a temp dir.
- `conftest.py` puts the repo root on `PYTHONPATH` (`conftest.py:113` `_current_pp = os.environ.get("PYTHONPATH", "")`) and installs the home sandbox (`conftest.py:140` `_HOME_KEYS = ("AW_HOME", "XDG_CONFIG_HOME")`). Running inside a worktree of `HEAD` makes both apply to the replayed file; the harness additionally sets `PYTHONPATH=<worktree>` so the worktree's package copy wins over the editable install (`g55j1e` F-05 demonstration).
- Tools here are stdlib-only scripts with a `main(argv)` and behavioral tests over synthesized git repos (`tools/lost_guard_census.py`, `tests/test_lost_guard_census.py`).
- P16 (`GUIDING_PRINCIPLES.md` Section 16): the new tests exercise the harness through calls and subprocesses and assert outputs; they read no production source.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The uncited population is 102,815 lines of test source, too large to read unaided. | Authoring probe summing `git show 19313eed^:<p>` line counts over the 209 uncited paths. |
| F-02 | Replayed files need repo-root imports of `tests.*` helpers. | Authoring probe of import lines: `tests.support` 46, `tests.test_ipd_lifecycle_cli` 4, `tests.conformance_matrix` 4, `tests.fixtures` 3; `tests/__init__.py` and `tests/support.py` exist at HEAD. |
| F-03 | Some replays will fail on imports that no longer exist, which is a distinct verdict from a behavioral failure. | `tests.test_run_analytics_export` imported by 2 files, absent at HEAD; `agent_workflows.wtiso_gate` imported by 1 file, absent at HEAD (`1ub8ex` F-04). |
| F-04 | Per-file overhead is small: a detached worktree costs about 0.8s and a one-file run about 0.6s. The authoring design (`--rootdir <repo>` with the file outside it) instead took 66s for a one-assert test. | Review: `git worktree add --detach` `real 0m0.763s`; `tests/test_run_freeze.py` in the worktree `real 0m0.612s`; `--rootdir "$PWD" <tmp>/test_p.py` -> `1 passed in 64.54s`. |
| F-05 | A bare temp dir changes outcomes. 85 of the 298 test files deleted by the trim use `__file__`, mostly as a repo-root anchor. The root conftest's home sandbox does not reach a file outside the rootdir. | Review: `tests/test_shared_checkout_contract.py` from `19313eed^` gives `6 failed, 4 passed` from a temp dir but `10 passed` at its own path in a tree of `HEAD`. A probe printed `AW_HOME= None` from a temp dir and `AW_HOME= /tmp/aw-test-home-...` inside a worktree. |
| F-06 | 137 of the 298 deleted files use `subprocess`, so a timeout that kills only the direct child can orphan grandchildren. | Review grep over the `19313eed^` blobs; process-group kill (`start_new_session` + `os.killpg`) returned at the 2s timeout in a probe. |
| F-07 | Import failures surface as exit 2 with junit `<error message="collection failure">` whose text contains `ModuleNotFoundError`; a syntax error is also exit 2 without it; a file with no tests is exit 5. | Review probes: `i exit=2 ModuleNotFoundError: No module named 'nosuchmod_xyz'`, `s exit=2`, `n exit=5`. |

## Proposed changes (ordered, validatable)

1. Worktree-isolated replay harness with verdict classes and JSON output (E-01).
2. Synthesized-repo behavioral tests covering every verdict (E-02).
3. README section (E-03).

## Deferred / out of scope (with reason)

- Running the replay over the 209 files and interpreting results: Order 05 (`8d0qsg`).
  - Carrier: 8d0qsg
- Restoring any replayed test into `tests/`: a per-gap deliverable decided by Order 08 (`xmr5qj`) when it files items; code-pin restoration is forbidden outright (P16).
  - Carrier: xmr5qj

## Scope check

- Over-scope: none.
- Under-scope: none known. Files needing `tests/fixtures/` relative to their own `__file__` now resolve them, because the blob sits at its original path in a tree of `HEAD`. A file whose fixture was itself deleted by the trim still reports `fail`/`error-collect`; Order 05 records that as `replay-env-limited`. The two classes this review added, `no-tests` and `error`, also map to `replay-env-limited` in Order 05 (`8d0qsg`), with the cause named. They are cross-referenced here because this plan owns the verdict set.

## Required tests / validation

- Before E-01, capture an execution-start baseline: bare `python3 -m pytest`, with the summary line and failing node ids saved outside the repo.
- `python3 -m pytest -o addopts="" -q tests/test_deleted_test_replay.py` passes.
- A live replay of `tests/test_run_freeze.py` at `19313eed` leaves `git status --short` and `git worktree list` unchanged.
- Bare `python3 -m pytest`: paste the actual summary; no new failures versus the baseline.

## Spec / documentation sync

N/A for specs: no `.spec.md` governs audit tooling under `tools/`. `tools/README.md` gains a section (E-03).

## Open questions

### OQ-01: Should the replay run with xdist?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. One file per process with `-o addopts=""` keeps per-test outcomes deterministic; Order 05 parallelizes across files if it needs to. The bare-suite contract in `AGENTS.md` governs suite runs, not single-file replays.

### OQ-02: Should the replay run from a bare temp dir or from a worktree of `HEAD`?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: Worktree. Demonstrated at review (F-05): from a bare temp dir, `tests/test_shared_checkout_contract.py` gives `6 failed, 4 passed`; at its own path in a tree of `HEAD` it gives `10 passed`. The conftest home sandbox applied only in the worktree. The cost is about 0.8s per file (F-04). Recorded as D-1 in the review record.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git status --short` and `git worktree list` before and after, both identical. Also the pasted output of `python3 tools/deleted_test_replay.py 19313eed tests/test_run_freeze.py --format json` (produced by E-01's `main`), showing a verdict and a `tests` list. Its length must equal the count pytest collects from that blob, re-derived at execution: write the blob to a scratch worktree and paste the `--collect-only -q` summary. A hard-coded number is not the bar.
  - Observed evidence:
    1. `git status --short && git worktree list` before:
    ```
    ?? tools/deleted_test_replay.py
    <repo-root>                                            aca2705bf [main]
    <repo-root>/.aw/state/suite-baselines/jzeeky-attempt1  aca2705bf (detached HEAD)
    <repo-root>/.aw/state/suite-baselines/mq715m-attempt1  8bb489cfd (detached HEAD)
    <repo-root>/.aw/state/suite-baselines/mtdxiu-attempt1  349cb62eb (detached HEAD)
    <repo-root>/.aw/state/suite-baselines/nzzu8n-attempt1  150e1d06a (detached HEAD)
    <repo-root>/.aw/worktrees/.aw-isocommit-6xj9ahwx       a283a3216 (detached HEAD)
    <repo-root>/.aw/worktrees/.aw-isocommit-wdtvmbgq       522c7bc42 (detached HEAD)
    <repo-root>/.aw/worktrees/1rozt5                       f52907adc [aw/lane/1rozt5]
    <repo-root>/.aw/worktrees/2hgxi1                       31ef0876b [aw/lane/2hgxi1]
    <repo-root>/.aw/worktrees/34iwyp                       f52907adc [aw/lane/34iwyp]
    <repo-root>/.aw/worktrees/a63epo                       68b86fff5 [aw/lane/a63epo]
    <repo-root>/.aw/worktrees/a63epo_attempt2              fd76c8f5f [aw/lane/a63epo_attempt2]
    <repo-root>/.aw/worktrees/e25iy9                       cadea62b5 [aw/lane/e25iy9]
    <repo-root>/.aw/worktrees/e25iy9_attempt2              f28eba802 [aw/lane/e25iy9_attempt2]
    <repo-root>/.aw/worktrees/gradfix-review               199437f35 [review/gradfix-plan-review]
    <repo-root>/.aw/worktrees/j7dsci                       6d8834886 [aw/lane/j7dsci]
    <repo-root>/.aw/worktrees/j7dsci_attempt2              0659bcee5 [aw/lane/j7dsci_attempt2]
    <repo-root>/.aw/worktrees/jj5ju1_attempt2              82d8aa390 [aw/lane/jj5ju1_attempt2]
    <repo-root>/.aw/worktrees/jzeeky                       aca2705bf [aw/lane/jzeeky]
    <repo-root>/.aw/worktrees/mq715m                       8bb489cfd [aw/lane/mq715m]
    <repo-root>/.aw/worktrees/mtdxiu                       416f4e2d0 [aw/lane/mtdxiu]
    <repo-root>/.aw/worktrees/nzzu8n                       150e1d06a [aw/lane/nzzu8n]
    <repo-root>/.aw/worktrees/tliqz6                       868198ae3 [aw/lane/tliqz6]
    <repo-root>/.aw/worktrees/y9m1ya                       06a7edeee [aw/lane/y9m1ya]
    ```
    After:
    Identical.
    2. Re-derived count at execution from scratch worktree (`python3 -m pytest -o addopts="" --collect-only -q tests/test_run_freeze.py`):
    ```
    tests/test_run_freeze.py::RevisionTest::test_semantic_edit_yields_revision_and_invalidates_evidence
    tests/test_run_freeze.py::RevisionTest::test_addition_after_approval_allowed
    tests/test_run_freeze.py::RevisionTest::test_redefine_after_approval_refused
    tests/test_run_freeze.py::RevisionTest::test_drop_after_approval_refused
    tests/test_run_freeze.py::RevisionTest::test_cosmetic_edit_is_a_digest_noop
    tests/test_run_freeze.py::FreezeDeterminismTest::test_dict_order_does_not_change_set_digest
    tests/test_run_freeze.py::FreezeDeterminismTest::test_same_input_same_ids_and_digests
    tests/test_run_freeze.py::FreezeDeterminismTest::test_binds_every_category_id
    tests/test_run_freeze.py::RequirementSetRecordTest::test_record_is_schema_valid_and_binds_scope
    tests/test_run_freeze.py::MalformedInputTest::test_non_string_item_refused
    tests/test_run_freeze.py::MalformedInputTest::test_non_mapping_refused
    tests/test_run_freeze.py::MalformedInputTest::test_empty_item_refused_before_set_emitted

    12 tests collected in 0.84s
    ```
    3. `python3 tools/deleted_test_replay.py 19313eed tests/test_run_freeze.py --format json`:
    ```json
    [
      {
        "commit": "19313eed",
        "counts": {
          "error": 0,
          "failed": 0,
          "passed": 12,
          "skipped": 0
        },
        "error_line": null,
        "exit_code": 0,
        "head": "150e1d06ae38ab98b7fe4cad7650f6cc9650ba64",
        "overwrote_head_path": false,
        "path": "tests/test_run_freeze.py",
        "replay_root": "/tmp/deleted_test_replay_9y6j3n8m/wt",
        "tests": [
          [
            "tests.test_run_freeze.FreezeDeterminismTest::test_binds_every_category_id",
            "passed"
          ],
          [
            "tests.test_run_freeze.FreezeDeterminismTest::test_dict_order_does_not_change_set_digest",
            "passed"
          ],
          [
            "tests.test_run_freeze.FreezeDeterminismTest::test_same_input_same_ids_and_digests",
            "passed"
          ],
          [
            "tests.test_run_freeze.MalformedInputTest::test_empty_item_refused_before_set_emitted",
            "passed"
          ],
          [
            "tests.test_run_freeze.MalformedInputTest::test_non_mapping_refused",
            "passed"
          ],
          [
            "tests.test_run_freeze.MalformedInputTest::test_non_string_item_refused",
            "passed"
          ],
          [
            "tests.test_run_freeze.RequirementSetRecordTest::test_record_is_schema_valid_and_binds_scope",
            "passed"
          ],
          [
            "tests.test_run_freeze.RevisionTest::test_addition_after_approval_allowed",
            "passed"
          ],
          [
            "tests.test_run_freeze.RevisionTest::test_cosmetic_edit_is_a_digest_noop",
            "passed"
          ],
          [
            "tests.test_run_freeze.RevisionTest::test_drop_after_approval_refused",
            "passed"
          ],
          [
            "tests.test_run_freeze.RevisionTest::test_redefine_after_approval_refused",
            "passed"
          ],
          [
            "tests.test_run_freeze.RevisionTest::test_semantic_edit_yields_revision_and_invalidates_evidence",
            "passed"
          ]
        ],
        "verdict": "pass",
        "wall_s": 3.19
      }
    ]
    ```
    Replay collected and passed exactly 12 tests, matching the re-derived count.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" -q tests/test_deleted_test_replay.py` summary line, and a mapping from each verdict class other than `error` (`pass`, `fail`, `error-import`, `error-collect`, `no-tests`, `timeout`) to the case that asserts it, plus the `__file__`/conftest case (g). Sensitivity check: in a scratch copy, change the classifier so `error-import` falls through to `error-collect`, paste the failing run, and discard the copy.
  - Observed evidence:
    1. Pasted summary line of `python3 -m pytest -o addopts="" -q tests/test_deleted_test_replay.py`:
    `10 passed in 9.63s`
    2. Mapping of verdict classes to test cases:
    - `pass`: `test_case_a_pass` (also `test_case_g_parents_and_conftest`, `test_overwrote_head_path_true`)
    - `fail`: `test_case_b_fail`
    - `error-import`: `test_case_c_error_import`
    - `error-collect`: `test_case_d_error_collect`
    - `no-tests`: `test_case_e_no_tests`
    - `timeout`: `test_case_f_timeout`
    - Case (g) `__file__`/conftest: `test_case_g_parents_and_conftest`
    3. Sensitivity check: changed classifier in `tools/deleted_test_replay.py` so `error-import` fell through to `error-collect`:
    ```
    FAILED tests/test_deleted_test_replay.py::DeletedTestReplayBehavioralTests::test_case_c_error_import
    AssertionError: 'error-collect' != 'error-import'
    1 failed, 9 passed in 10.12s
    ```
    Discarded scratch edit and restored original, re-verified clean pass: `10 passed in 9.63s`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git diff tools/README.md`, and pasted output of a search of the added lines for U+2013/U+2014 that finds none. Also the pasted execution-start baseline and the final bare `python3 -m pytest` summary lines, showing no new failing node ids.
  - Observed evidence:
    1. Pasted `git diff tools/README.md`:
    ```diff
    diff --git a/tools/README.md b/tools/README.md
    index adde25a..6ee5144 100644
    --- a/tools/README.md
    +++ b/tools/README.md
    @@ -382,3 +382,45 @@ python3 tools/mutation_probe.py agent_workflows/m.py::is_even \
         -- tests/test_m.py
     '''
    +
    +## `deleted_test_replay.py`
    +
    +`tools/deleted_test_replay.py` is a test replay harness that executes historical or trim-deleted test files against the current tree and reports machine-readable verdicts and per-test outcomes.
    +
    +### Purpose and Isolation
    +
    +The harness provides a deterministic, side-effect-free way to execute deleted test files against current code to verify whether historical assertions still hold.
    +
    +To prevent collisions with concurrent work and ensure tests see repository root imports and root `conftest.py` sandboxing, the tool creates a throwaway detached git worktree of committed `HEAD` in a temporary directory outside the checkout. The replayed test blob is extracted from git (`<commit>^:<path>`) and written at its original repository-relative path inside that worktree. Uncommitted edits in the invoking checkout are not seen. When execution completes, the harness always removes and prunes the temporary worktree and deletes the temporary directory.
    +
    +### Verdict Classes
    +
    +Each replayed file receives one of seven closed verdict classes:
    +- `pass`: all collected tests passed (exit 0).
    +- `fail`: one or more assertions failed against current code (exit 1).
    +- `error-import`: test collection failed due to a missing module (exit 2 with `ModuleNotFoundError` or `ImportError`).
    +- `error-collect`: test collection failed due to another collection error such as a syntax error (exit 2).
    +- `no-tests`: the test file defines no runnable tests (exit 5).
    +- `timeout`: test execution exceeded the configured timeout (the child process group is terminated with SIGKILL).
    +- `error`: pytest internal error, usage error, unexpected termination, or missing test result XML.
    +
    +### Handoff from `lost_guard_census.py`
    +
    +The harness integrates directly with `tools/lost_guard_census.py`. Passing `--from-json <inventory.json>` accepts the JSON output generated by `tools/lost_guard_census.py --uncited --format json` and replays every listed path in sequence after any positional paths.
    +
    +### Usage
    +
    +(bash snippet: python3 tools/deleted_test_replay.py 19313eed tests/test_run_freeze.py [--format json] [--timeout 60])
    ```
    2. Python search for U+2013 and U+2014 in added text:
    `U+2013 (en-dash) present: False`
    `U+2014 (em-dash) present: False`
    3. Baseline summary:
    `8053 passed, 4 skipped, 18 xfailed, 3 warnings in 757.15s (0:12:37)`
    Final summary:
    `8063 passed, 4 skipped, 18 xfailed, 3 warnings in 1055.18s (0:17:35)`
    Delta: +10 passed, 0 new failures.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT:
- Open questions: OQ-01 and OQ-02 are resolved, and none remain.
- Order: capture the bare-suite baseline, then E-01, then E-02 and E-03.
- Scope fence (a declaration, not a stop rule): the change is expected to touch only the paths in `- Scope-Paths:`. If an out-of-scope edit proves necessary, make it and justify it at finalize: `--scope-reason` for each out-of-scope path, `--scope-ack` for each declared path left unmodified.
- Invariants:
  - The harness never writes a file in the invoking checkout's tree. Blobs go only into its own temp worktree.
  - Every worktree it creates is removed and pruned, even on exception or timeout.
  - A timeout kills the whole process group.
  - If a replay leaves a dirty path or a worktree behind, fix the tool. Do not hand-clean.
- Honesty: paste the ACTUAL runner output for every claim. Never claim a result you did not run.
- Commit: only the declared paths, through `aw commit <plan> -- <paths>`. Verify that `git diff --cached --name-only` lists only your paths. Never `git add -A`, never `--no-verify`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs finalize and the lifecycle move. When executing by hand, finalize with `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms. Never move the plan with a hand `git mv`.
