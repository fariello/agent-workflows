# IPD: Stop project-root climb at temp roots so stray /tmp/.aw or /tmp/.agents cannot poison temp fixtures

- Date: 2026-10-14
- Kind: child
- Concern: project-root climb ceiling at shared temp roots and test session temp boundaries
- Scope: Stop find_project_root, is_project_dir, and _find_git_root at shared temporary root containers (/tmp, /var/tmp, tempfile.gettempdir(), TMPDIR/TEMP/TMP, and AW_PROJECT_CEILING) and export AW_PROJECT_CEILING in conftest.py and tests/__init__.py so stray /tmp/.aw or /tmp/.agents (or an enclosing checkout when basetemp is inside a repo) cannot poison non-project temp fixtures.
- Scope-Paths: agent_workflows/project_context.py, conftest.py, tests/__init__.py, tests/test_nonsurveyable_root_refusal.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- From-Backlog: 5tj8g4
- Work-Kind: chore
- Priority: low
- Set: 5tj8g4
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: i44j8w

## Workflow history
- 2026-10-14 to-review (aw set): Ready for review; resolves 5tj8g4 temp-root climb ceiling.

- 2026-10-14 draft (Antigravity): created.

## Goal

Prevent `project_context.find_project_root`, `project_context.is_project_dir`, and `project_context._find_git_root` from treating a shared temporary root container (`/tmp`, `/var/tmp`, `tempfile.gettempdir()`, `TMPDIR`/`TEMP`/`TMP`, or an explicit `AW_PROJECT_CEILING` entry) as an AW project root or climbing above it into its ancestor directories, and wire `AW_PROJECT_CEILING` in `conftest.py` and `tests/__init__.py`. This eliminates the 39-40 false test failures across 11 test modules that occur whenever a stray `.aw/` or `.agents/` marker exists in the host's `/tmp` (or when `TMPDIR` / `basetemp` sits inside a directory with an ancestor `.aw/`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Project-root and git-root climb ceiling in `agent_workflows/project_context.py`

- [ ] E-01 Add `_project_climb_ceilings() -> set[Path]` in `agent_workflows/project_context.py` and enforce the ceiling in `project_context.find_project_root`, `project_context.is_project_dir`, and `project_context._find_git_root`.
  - Depends on: none
  - Expected outcome: `_project_climb_ceilings()` returns resolved canonical `Path` objects for `tempfile.gettempdir()`, POSIX shared temp roots `/tmp` and `/var/tmp` (when present on disk), any path named by `TMPDIR`, `TEMP`, or `TMP` in `os.environ`, and any `os.pathsep`-separated path in `os.environ.get("AW_PROJECT_CEILING", "")`. `find_project_root(start)` returns `None` immediately when `curr in ceilings` (neither matching the ceiling container itself as a project root nor walking above it into its parents). `is_project_dir(repo_root)` returns `False` when `Path(repo_root).resolve() in _project_climb_ceilings()`, preserving the invariant `is_project_dir(p) == (find_project_root(p) == p.resolve())` required by `classify_project_dir`. `_find_git_root(start_dir)` stops and returns `None` when `curr in ceilings`. Any AW project or git repo created inside a subdirectory of a temp root (such as `/tmp/tmpXXXXXX` or `basetemp / "test_foo0"`) remains a strict descendant of the ceiling and continues to resolve normally.
  - Execution state: pending

### Task group 2: Session ceiling guard in `conftest.py` and `tests/__init__.py`

- [ ] E-02 Export and restore `AW_PROJECT_CEILING` in `conftest.py` and `tests/__init__.py` so pytest's `basetemp` and the session temp root are always registered as climb ceilings.
  - Depends on: E-01
  - Expected outcome: `conftest.py` records the session temp root (`tempfile.gettempdir()`) in `_SANDBOX_ENV["AW_PROJECT_CEILING"]`, appends `str(tmp_path_factory.getbasetemp().resolve())` via a session-scoped autouse fixture (or `pytest_configure` on `config._tmp_path_factory` / `basetemp`), and restores `AW_PROJECT_CEILING` alongside `AW_HOME` and `XDG_CONFIG_HOME` in `_restore_home_sandbox`. `tests/__init__.py` sets `os.environ.setdefault("AW_PROJECT_CEILING", tempfile.gettempdir())` so `python3 -m unittest discover` gets the same ceiling backstop even when a custom temp root is used.
  - Execution state: pending

### Task group 3: Regression tests for polluted temp roots and explicit ceilings

- [ ] E-03 Add behavioral unit and CLI subprocess regression tests in `tests/test_nonsurveyable_root_refusal.py` covering a polluted `TMPDIR` containing stray `.aw/records`, `.agents/plans`, and `.git` markers as well as `AW_PROJECT_CEILING` containment.
  - Depends on: E-01, E-02
  - Expected outcome: New test methods in `tests/test_nonsurveyable_root_refusal.py` create an isolated temporary container `$T` with `$T/.aw/records/specs/draft`, `$T/.agents/plans`, and `$T/.git` planted directly at the temp root, allocate child scratch directories inside `$T` with `TMPDIR=$T`, and verify both in-process (`find_project_root`, `is_project_dir`, `classify_project_dir`, `nonsurveyable_root_refusal`, `git_root_for_message`) and via CLI subprocess (`aw attention --agent`, `aw specs check --agent`) that: (1) the temp root container `$T` itself and non-project child directories inside `$T` report `find_project_root == None`, `is_project_dir == False`, `ProjectLocationCase.NO_PROJECT`, and exit code `2` (`cannot-run`); (2) a real project child `$T/child_proj` with its own `.aw/records` still resolves `is_project_dir($T/child_proj) == True` and `find_project_root($T/child_proj/sub) == $T/child_proj`; and (3) `AW_PROJECT_CEILING` stops upward climbs from escaping a custom base directory situated inside an enclosing AW project.
  - Execution state: pending

### Task group 4: Changelog sync and polluted-TMPDIR suite verification

- [ ] E-04 Add a `Fixed:` entry under `## 2.0.0 (pending)` in `CHANGELOG.md` (with no em or en dashes) and run both the targeted regression modules under a polluted `TMPDIR` and the full pytest suite.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `CHANGELOG.md` documents the temp-root project-climb ceiling fix using plain hyphens/colons only; all 11 previously failing test modules pass when run with `TMPDIR` pointing at a directory containing `.aw/records` and `.agents/plans`; `aw sanitize --agent` and `python3 -m pytest` pass with zero failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `project_context.find_project_root` (`agent_workflows/project_context.py:315`, `def find_project_root(start: Optional[str | Path] = None) -> Optional[Path]:`) walks upward via `curr = curr.parent` until `curr == curr.parent`, checking `_is_project_marker(curr / ".aw") or _is_project_marker(curr / ".agents", legacy=True)`.
- `project_context._is_project_marker` (`agent_workflows/project_context.py:337`, `def _is_project_marker(marker: Path, legacy: bool = False) -> bool:`) recognizes `.aw` when it contains any of `("system", "records", "config")` and `.agents` when it contains any of `("workflows", "plans", "docs", "prompts", "comms", "backlog")`.
- `project_context.classify_project_dir` (`agent_workflows/project_context.py:556`, `def classify_project_dir(path: Optional[str | Path] = None) -> ProjectClassification:`) checks `if is_project_dir(p): return ProjectClassification(case=ProjectLocationCase.IS_PROJECT_ROOT, root=p)` and then `enclosing = find_project_root(p)`. Therefore `is_project_dir` and `find_project_root` MUST agree on whether a directory is a project root.
- `project_context.no_project_message` (`agent_workflows/project_context.py:449`, `"PROBING FOR GIT HERE IS A MESSAGE CONCERN AND MUST NEVER BE PROMOTED INTO find_project_root"`) documents that `find_project_root` is deliberately git-blind; `_find_git_root` (`agent_workflows/project_context.py:304`, `def _find_git_root(start_dir: str) -> Optional[str]:`) is used only to attach the `aw install` hint when a directory is inside a git repository without AW.
- `conftest.py` (`conftest.py:228`, `_HOME_KEYS = ("AW_HOME", "XDG_CONFIG_HOME")`) and `_restore_home_sandbox` (`conftest.py:238`, `def _restore_home_sandbox():`) establish session-wide environment sandboxing before test collection and restore it around every test. `tests/__init__.py` (`tests/__init__.py:26`, `if not os.environ.get("AW_HOME"):`) provides the matching fallback for `python3 -m unittest discover`.
- All tests must test observable behavior and outcomes (`AGENTS.md`, `GEMINI.md` Rule 6: no `inspect`, `ast`, regex, or substring checks on production source).
- User-facing prose in `CHANGELOG.md` must contain no em dashes or en dashes (`AGENTS.md`, `GEMINI.md` Rule 3).

## Findings

| ID | Category | Location | Observation | Impact |
| --- | --- | --- | --- | --- |
| F-01 | Root cause | `project_context.find_project_root` (`agent_workflows/project_context.py:315`), `project_context.is_project_dir` (`agent_workflows/project_context.py:502`), `project_context._find_git_root` (`agent_workflows/project_context.py:304`) | `find_project_root` and `_find_git_root` walk upward (`curr = curr.parent`) all the way to the filesystem root `/` without stopping at shared temporary root containers (`/tmp`, `/var/tmp`, `tempfile.gettempdir()`, `TMPDIR`/`TEMP`/`TMP`). When an abandoned `/tmp/.aw/records` or `/tmp/.agents/plans` directory exists on the host, every temporary test directory (`/tmp/tmpXXXXXX`, `/tmp/pytest-of-<user>/...`) climbs into `/tmp` and resolves `/tmp` as an enclosing `IS_PROJECT_ROOT` / `INSIDE_PROJECT`. | Reproduces 40 test failures across 11 test modules when `$TMPDIR/.aw/records` exists: `tests/test_no_project_exit_is_cannot_run.py` (12), `tests/test_explicit_dir_non_project.py` (6), `tests/test_validator_nonsurveyable_dir.py` (5), `tests/test_nonsurveyable_root_refusal.py` (4), `tests/test_read_class_callers_refuse.py` (3), `tests/test_commit_run_trailers_env.py` (3), `tests/test_explicit_dir_subdir_resolution.py` (2), `tests/test_agent_commit_identity.py` (2), `tests/test_attention.py` (1), `tests/test_agent_surface_conformance.py` (1), and `tests/test_finalize_sendback.py` (1). |
| F-02 | Design constraint | `conftest._restore_home_sandbox` (`conftest.py:238`, `_SANDBOX_ENV`) and `project_context.resolve_verb_repo_root` (`agent_workflows/project_context.py:372`, `"is_project_dir(Path.home()) is frequently True"`) | Redirecting `TMPDIR` in `conftest.py` to a subdirectory `/tmp/aw_test_tmp_XXXXXX` is NOT sufficient by itself when `/tmp/.aw` exists on the host, because `/tmp` remains an ancestor of `/tmp/aw_test_tmp_XXXXXX` and `find_project_root` climbs past `TMPDIR` into `/tmp`. Similarly, when `TMPDIR` is under `$HOME` (e.g. Windows `AppData\Local\Temp` or a user-configured `TMPDIR` inside `$HOME` where `~/.aw/config` exists) or when `pytest --basetemp` is inside a repository checkout, climbing above the temp root container escapes into the ancestor `.aw/`. | Stopping the upward climb at temp root containers (`_project_climb_ceilings()`) in `project_context.py` is required so non-project temp fixtures cannot escape the temp root container into `/tmp` or `$HOME`, while `AW_PROJECT_CEILING` in `conftest.py` also bounds `pytest`'s `basetemp`. |
| F-03 | Fixture compatibility | `NonsurveyableRootRefusalTests.setUp` (`tests/test_nonsurveyable_root_refusal.py:59`) and `TestSpecsDateContainment._assert_target_bounded` (`tests/test_specs_date_containment.py:194`) | Every temporary project fixture in the suite is created inside a child directory allocated under the temp root (`tempfile.TemporaryDirectory()`, `tempfile.mkdtemp()`, or `tmp_path` = `basetemp / "<testname>0"`), never at the temp root container (`/tmp`, `TMPDIR`, or `basetemp`) itself. Additionally, `tests/test_specs_date_containment.py` compares `str(p).replace(date_arg, "").replace(date_compact, "")` against `self.tmp_base`, which breaks if `TMPDIR` itself is rewritten to a path containing hyphens `-`. | Stopping the climb at the temp root container (and `basetemp` via `AW_PROJECT_CEILING`) without rewriting `TMPDIR` to a hyphenated path keeps all 15 date-containment tests green and preserves project detection for every temp project created inside `mkdtemp` / `TemporaryDirectory` / `tmp_path`. |
| F-04 | Scope boundary with `nj13xp` | `.aw/records/backlog/open/20261012-nj13xp-01-nj13xp-test-finalize-sendback-e2e-runs-aw-ipd-scaffold-wi.backlog.md` and `TheRetryTriggerIsAPositiveAllowlist.test_e2e_real_finalize_checkbox_mismatch_is_retryable` (`tests/test_finalize_sendback.py:678`) | Sibling open backlog item `nj13xp` (`Work-Kind: bug`, `Blocks-Release: next`) specifically tracks passing `--dir` to `aw ipd scaffold` in `tests/test_finalize_sendback.py`. With the temp-root climb ceiling in `project_context.py`, `test_e2e_real_finalize_checkbox_mismatch_is_retryable` also stops climbing into `$TMPDIR/.aw`, while the explicit `--dir` change in `tests/test_finalize_sendback.py` remains owned by `nj13xp`. | `tests/test_finalize_sendback.py` is left untouched by this plan and declared out-of-scope with `- Carrier: nj13xp` so the two items do not conflict. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/project_context.py` (E-01)**:
   - Import `tempfile` at module top level.
   - Add helper `_project_climb_ceilings() -> set[Path]`:
     - Collect candidate ceiling paths from `tempfile.gettempdir()`, `/tmp`, `/var/tmp`, environment variables `TMPDIR`, `TEMP`, `TMP`, and any `os.pathsep`-separated entries in `os.environ.get("AW_PROJECT_CEILING", "")`.
     - Resolve each non-empty candidate via `Path(raw).expanduser().resolve()` (catching `OSError`/`RuntimeError` defensively) and return the resulting `set[Path]`.
   - In `find_project_root(start: Optional[str | Path] = None) -> Optional[Path]`:
     - Compute `ceilings = _project_climb_ceilings()`.
     - At the top of the `while True:` loop, before checking `_is_project_marker`, check `if curr in ceilings: return None`.
   - In `is_project_dir(repo_root: str | Path) -> bool`:
     - Resolve `p = Path(repo_root).expanduser().resolve()` (falling back to `Path(repo_root)` on `OSError`) and return `False` immediately if `p in _project_climb_ceilings()`.
   - In `_find_git_root(start_dir: str) -> Optional[str]`:
     - Compute `ceilings = _project_climb_ceilings()` and stop the loop (`return None`) if `curr in ceilings`.

2. **`conftest.py` and `tests/__init__.py` (E-02)**:
   - In `conftest.py`:
     - Add `"AW_PROJECT_CEILING"` to `_HOME_KEYS` and initialize `_SANDBOX_ENV["AW_PROJECT_CEILING"] = _tempfile.gettempdir()`.
     - In `pytest_configure(config)` (or a session-scoped autouse fixture receiving `tmp_path_factory`), append pytest's resolved `basetemp` directory (`os.pathsep.join(...)`) to `_SANDBOX_ENV["AW_PROJECT_CEILING"]` and `os.environ["AW_PROJECT_CEILING"]` so `tmp_path` directories (`basetemp / "<test>0"`) cannot climb past `basetemp` even if `--basetemp` is placed inside an AW project checkout.
   - In `tests/__init__.py`:
     - Set `os.environ.setdefault("AW_PROJECT_CEILING", tempfile.gettempdir())` alongside the `AW_IN_TEST_SESSION` guard.

3. **`tests/test_nonsurveyable_root_refusal.py` (E-03)**:
   - Add test methods on `NonsurveyableRootRefusalTests`:
     - `test_stray_markers_in_temp_root_do_not_poison_children`: creates an isolated temp root container `polluted_tmp` containing `.aw/records/specs/draft`, `.agents/plans`, and `.git` (initialized via `git init`), sets `TMPDIR` to `str(polluted_tmp)` in a patched environment, allocates child directories (`nongit_child`, `git_child`, and `real_proj_child` with `.aw/records` plus `real_proj_child/src/sub`), and asserts:
       - `is_project_dir(polluted_tmp)` is `False` and `find_project_root(polluted_tmp)` is `None`.
       - `find_project_root(nongit_child)` is `None`, `classify_project_dir(nongit_child).case == ProjectLocationCase.NO_PROJECT`, `git_root_for_message(nongit_child)` is `None`, and `nonsurveyable_root_refusal("attention", nongit_child, explicit_dir=False)` refuses with `may_proceed=False` and `next_action=None`.
       - `find_project_root(git_child)` is `None`, `git_root_for_message(git_child) == git_child.as_posix()`, and `nonsurveyable_root_refusal("attention", git_child, explicit_dir=False)` offers `aw install .` naming `git_child` (never `polluted_tmp`).
       - `is_project_dir(real_proj_child)` is `True` and `find_project_root(real_proj_child / "src" / "sub") == real_proj_child`.
       - Driving CLI subprocesses `python3 -m agent_workflows.cli attention --agent` and `python3 -m agent_workflows.cli specs check --agent` with `cwd=nongit_child` and `TMPDIR=str(polluted_tmp)` exits `2` with `status == "cannot-run"`.
     - `test_aw_project_ceiling_stops_climb_inside_enclosing_project`: creates a directory `custom_base = self.real_proj / "custom_basetemp"` and a child `scratch = custom_base / "test_case0"`, sets `AW_PROJECT_CEILING=str(custom_base)`, and asserts `find_project_root(scratch)` is `None` and `is_project_dir(custom_base)` is `False`, while `find_project_root(self.deep_subdir)` (outside `custom_base`) still resolves to `self.real_proj`.

4. **`CHANGELOG.md` (E-04)**:
   - Add a `Fixed:` bullet under `## 2.0.0 (pending)` describing the temp-root ceiling in `find_project_root`, `is_project_dir`, and `_find_git_root` plus `AW_PROJECT_CEILING` test session isolation, with no em or en dashes.

## Deferred / out of scope (with reason)

- Passing explicit `--dir` to `aw ipd scaffold` in `tests/test_finalize_sendback.py`: owned by dedicated release-blocking bug backlog item `nj13xp` (`.aw/records/backlog/open/20261012-nj13xp-01-nj13xp-test-finalize-sendback-e2e-runs-aw-ipd-scaffold-wi.backlog.md`).
  - Carrier: nj13xp

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Run `python3 -m pytest tests/test_nonsurveyable_root_refusal.py` and verify the new polluted-temp-root and `AW_PROJECT_CEILING` tests pass.
- Run all 11 previously failing test modules (`tests/test_no_project_exit_is_cannot_run.py`, `tests/test_explicit_dir_non_project.py`, `tests/test_validator_nonsurveyable_dir.py`, `tests/test_nonsurveyable_root_refusal.py`, `tests/test_read_class_callers_refuse.py`, `tests/test_commit_run_trailers_env.py`, `tests/test_explicit_dir_subdir_resolution.py`, `tests/test_agent_commit_identity.py`, `tests/test_attention.py`, `tests/test_agent_surface_conformance.py`, `tests/test_finalize_sendback.py`) plus `tests/test_specs_date_containment.py` under a private `TMPDIR` populated with `.aw/records`, `.agents/plans`, and `.git`, and verify 0 failures.
- Run `aw sanitize --agent` and the full repository test suite (`python3 -m pytest`).

## Spec / documentation sync

- Update `CHANGELOG.md` under `## 2.0.0 (pending)` (E-04) and update the docstrings of `find_project_root`, `is_project_dir`, and `_find_git_root` in `agent_workflows/project_context.py` (E-01). No specification file requires modification because `.aw/records/specs/implemented/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md` defines project root markers without licensing upward traversal into shared system temp containers (`/tmp`, `/var/tmp`, `TMPDIR`).

## Open questions

### OQ-01: Should the fix stop `find_project_root` at temp root containers (`_project_climb_ceilings`) in `agent_workflows/project_context.py`, or only redirect `TMPDIR` in `conftest.py`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Both layers are combined, with `_project_climb_ceilings()` in `agent_workflows/project_context.py` doing the primary work and `conftest.py` / `tests/__init__.py` exporting `AW_PROJECT_CEILING`. Redirecting `TMPDIR` to `/tmp/aw_test_tmp_XXXXXX` alone fails when `/tmp/.aw` exists on the host because `/tmp` is still an ancestor of `/tmp/aw_test_tmp_XXXXXX` (`find_project_root` walks all the way to `/`), and fails when `TMPDIR` is under `$HOME` where `~/.aw/config` exists (`project_context.resolve_verb_repo_root` at `agent_workflows/project_context.py:372`). Stopping the climb at shared temp root containers (`/tmp`, `/var/tmp`, `tempfile.gettempdir()`, `TMPDIR`/`TEMP`/`TMP`, and `AW_PROJECT_CEILING`) protects both CLI users and all test runners while allowing any AW project created in a subdirectory of a temp root to resolve normally.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste output of a `python3 -c` one-liner (driven through `agent_workflows.project_context`) that creates a temporary root `T` with `T/.aw/records`, `T/.agents/plans`, and `T/.git`, sets `TMPDIR=T`, and prints `(is_project_dir(T), find_project_root(T), find_project_root(T/'nongit'), _find_git_root(str(T/'nongit')), is_project_dir(T/'proj'), find_project_root(T/'proj'/'sub'))` showing `(False, None, None, None, True, PosixPath('.../proj'))`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste output of `python3 -m pytest tests/test_nonsurveyable_root_refusal.py -k ceiling` and a `python3 -c "import tests, os; print(bool(os.environ.get('AW_PROJECT_CEILING')))"` check confirming `AW_PROJECT_CEILING` is populated in both `pytest` (including `basetemp`) and `unittest` initialization.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the test runner output from `python3 -m pytest tests/test_nonsurveyable_root_refusal.py` showing all existing and new polluted-temp-root and `AW_PROJECT_CEILING` tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste (1) the `git diff -- CHANGELOG.md` showing the new `Fixed:` entry with zero em/en dashes, (2) the output of running all 11 previously failing test modules plus `tests/test_specs_date_containment.py` under a private `TMPDIR` containing `.aw/records`, `.agents/plans`, and `.git` (`0 failed`), and (3) the output of `aw sanitize --agent` and `python3 -m pytest`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Do not execute implementation steps until this IPD reaches `- Status: approved` (or is dispatched by an authorized runner turn). Upon completion of all `E-*` and `V-*` items and passing validation gates, finalize the IPD to `executed` via `aw ipd finalize`.
