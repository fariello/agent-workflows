# IPD: Stop project-root climb at temp roots so stray /tmp/.aw or /tmp/.agents cannot poison temp fixtures

- Date: 2026-10-14
- Kind: child
- Concern: project-root climb ceiling at shared temp roots and test session temp boundaries
- Scope: Stop find_project_root, is_project_dir, and _find_git_root at shared temporary root containers (/tmp, /var/tmp, tempfile.gettempdir(), TMPDIR/TEMP/TMP, and AW_PROJECT_CEILING) and export AW_PROJECT_CEILING in conftest.py and tests/__init__.py so stray /tmp/.aw or /tmp/.agents (or an enclosing checkout when basetemp is inside a repo) cannot poison non-project temp fixtures.
- Scope-Paths: agent_workflows/project_context.py, conftest.py, tests/__init__.py, tests/test_nonsurveyable_root_refusal.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: 5tj8g4
- Work-Kind: chore
- Priority: low
- Set: 5tj8g4
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: i44j8w
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review applied revisions
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-14 to-review (aw set): Ready for review; resolves 5tj8g4 temp-root climb ceiling.

- 2026-10-14 draft (Antigravity): created.

## Goal

Prevent `project_context.find_project_root`, `project_context.is_project_dir`, and `project_context._find_git_root` from treating a shared temporary root container (`/tmp`, `/var/tmp`, `tempfile.gettempdir()`, `TMPDIR`/`TEMP`/`TMP`, or an explicit `AW_PROJECT_CEILING` entry) as an AW project root or climbing above it into its ancestor directories, and wire `AW_PROJECT_CEILING` in `conftest.py` and `tests/__init__.py`. This eliminates the 39-40 false test failures across 11 test modules that occur whenever a stray `.aw/` or `.agents/` marker exists in the host's `/tmp` (or when `TMPDIR` / `basetemp` sits inside a directory with an ancestor `.aw/`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Project-root and git-root climb ceiling in `agent_workflows/project_context.py`

- [x] E-01 BEFORE editing, record the pre-edit baseline: (a) the bare `python3 -m pytest` summary line and failing-test-id set; (b) a run of the twelve modules named in `## Required tests / validation` under a polluted `TMPDIR` built as described there (hyphen-free name), with its summary line and failing-test-id set (expected nonzero: 40 failures across the 11 modules were measured at review, context only and not a bar); (c) the V-01 one-liner's output at the pre-edit tree. Then add `_project_climb_ceilings() -> set[Path]` in `agent_workflows/project_context.py` and enforce the ceiling in `project_context.find_project_root`, `project_context.is_project_dir`, and `project_context._find_git_root`, updating all three docstrings to state the ceiling.
  - Depends on: none
  - Expected outcome: the pre-edit baseline (a)-(c) is recorded. `_project_climb_ceilings()` returns resolved canonical `Path` objects for `tempfile.gettempdir()`, POSIX shared temp roots `/tmp` and `/var/tmp` (when present on disk), any path named by `TMPDIR`, `TEMP`, or `TMP` in `os.environ`, and any `os.pathsep`-separated path in `os.environ.get("AW_PROJECT_CEILING", "")`. The ceiling check is the FIRST statement in each loop iteration, before any marker or `.git` check, so it composes with sibling plan `ivq0nr`'s `.git`-boundary check in `find_project_root` (F-04) whichever lands first. `find_project_root(start)` returns `None` immediately when `curr in ceilings` (neither matching the ceiling container itself as a project root nor walking above it into its parents). `is_project_dir(repo_root)` returns `False` when `Path(repo_root).resolve() in _project_climb_ceilings()`, preserving the invariant `is_project_dir(p) == (find_project_root(p) == p.resolve())` required by `classify_project_dir`. `_find_git_root(start_dir)` stops and returns `None` when `curr in ceilings`. Any AW project or git repo created inside a subdirectory of a temp root (such as `/tmp/tmpXXXXXX` or `basetemp / "test_foo0"`) remains a strict descendant of the ceiling and continues to resolve normally.
  - Execution state: performed

### Task group 2: Session ceiling guard in `conftest.py` and `tests/__init__.py`

- [x] E-02 Export and restore `AW_PROJECT_CEILING` in `conftest.py` and `tests/__init__.py` so pytest's `basetemp` and the session temp root are always registered as climb ceilings.
  - Depends on: E-01
  - Expected outcome: `conftest.py` records the session temp root (`tempfile.gettempdir()`) in `_SANDBOX_ENV["AW_PROJECT_CEILING"]`, appends `str(tmp_path_factory.getbasetemp().resolve())` (joined with `os.pathsep`) to both `_SANDBOX_ENV["AW_PROJECT_CEILING"]` and `os.environ["AW_PROJECT_CEILING"]` via a session-scoped autouse fixture taking `tmp_path_factory` (the mechanism demonstrated at review, under both `-n auto` and `-n0`; do NOT use the private `config._tmp_path_factory`). Because `_restore_home_sandbox` already re-applies `os.environ.update(_SANDBOX_ENV)` before and after every test, `AW_PROJECT_CEILING` is restored alongside `AW_HOME` and `XDG_CONFIG_HOME` with no change to that fixture (`_HOME_KEYS` has no other reader, so adding the key there is optional). `tests/__init__.py` sets `os.environ.setdefault("AW_PROJECT_CEILING", tempfile.gettempdir())` so `python3 -m unittest discover` gets the same ceiling backstop even when a custom temp root is used.
  - Execution state: performed

### Task group 3: Regression tests for polluted temp roots and explicit ceilings

- [x] E-03 Add behavioral unit and CLI subprocess regression tests in `tests/test_nonsurveyable_root_refusal.py` covering a polluted `TMPDIR` containing stray `.aw/records`, `.agents/plans`, and `.git` markers as well as `AW_PROJECT_CEILING` containment.
  - Depends on: E-01, E-02
  - Expected outcome: New test methods in `tests/test_nonsurveyable_root_refusal.py` create an isolated temporary container `$T` with `$T/.aw/records/specs/draft`, `$T/.agents/plans`, and `$T/.git` planted directly at the temp root, allocate child scratch directories inside `$T` with `TMPDIR=$T`, and verify both in-process (`find_project_root`, `is_project_dir`, `classify_project_dir`, `nonsurveyable_root_refusal`, `git_root_for_message`) and via CLI subprocess (`aw attention --agent`, `aw specs check --agent`) that: (1) the temp root container `$T` itself and non-project child directories inside `$T` report `find_project_root == None`, `is_project_dir == False`, `ProjectLocationCase.NO_PROJECT`, and exit code `2` (`cannot-run`); (2) a real project child `$T/child_proj` with its own `.aw/records` still resolves `is_project_dir($T/child_proj) == True` and `find_project_root($T/child_proj/sub) == $T/child_proj`; (3) `AW_PROJECT_CEILING` stops upward climbs from escaping a custom base directory situated inside an enclosing AW project; and (4) a module-level pytest test `test_tmp_path_does_not_climb_past_basetemp(tmp_path)` asserts `find_project_root(tmp_path) is None`, which under a `--basetemp` placed inside an AW project fails without the E-02 fixture and passes with it (demonstrated at review). The polluted temp container in (1) is created with a hyphen-free prefix (F-03). Every subprocess sets `env` explicitly (copy of `os.environ` with `TMPDIR` overridden) and every temp dir is cleaned up.
  - Execution state: performed

### Task group 4: Changelog sync and polluted-TMPDIR suite verification

- [x] E-04 Add a `Fixed:` entry under `## 2.0.0 (pending)` in `CHANGELOG.md` (with no em or en dashes) that names the new `AW_PROJECT_CEILING` variable and its semantics (an `os.pathsep`-separated list; a listed directory is never itself a project or git root and the climb never passes above it; the system temp roots are always ceilings), and run both the targeted regression modules under a polluted `TMPDIR` and the full pytest suite.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `CHANGELOG.md` documents the fix and `AW_PROJECT_CEILING` using plain hyphens/colons only; the E-01(b) polluted-`TMPDIR` module run, repeated against the SAME hyphen-free polluted container, reports `0 failed` (contrast with the nonzero E-01(b) baseline); `aw sanitize --agent` exits 0; the bare `python3 -m pytest` failing-test-id set contains no id absent from the E-01(a) baseline.
  - Execution state: performed

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
| F-03 | Fixture compatibility | `NonsurveyableRootRefusalTests.setUp` (`tests/test_nonsurveyable_root_refusal.py:59`) and `TestSpecsDateContainment._assert_target_bounded` (`tests/test_specs_date_containment.py:194`) | Every temporary project fixture in the suite is created inside a child directory allocated under the temp root (`tempfile.TemporaryDirectory()`, `tempfile.mkdtemp()`, or `tmp_path` = `basetemp / "<testname>0"`), never at the temp root container (`/tmp`, `TMPDIR`, or `basetemp`) itself. Additionally, `tests/test_specs_date_containment.py` compares `str(p).replace(date_arg, "").replace(date_compact, "")` against `self.tmp_base`, which breaks if `TMPDIR` itself is rewritten to a path containing hyphens `-`. Re-measured at review: with the E-01 prototype and a polluted `TMPDIR=/tmp/poll-<random>`, `test_absolute_path_date_refused` still fails (also failing at HEAD), while the same run with a hyphen-free `/tmp/pollnohyph<random>` passes, so the validation container MUST have a hyphen-free name (`tempfile.mkdtemp` random suffixes contain no hyphen). | Stopping the climb at the temp root container (and `basetemp` via `AW_PROJECT_CEILING`) without rewriting `TMPDIR` to a hyphenated path keeps all 15 date-containment tests green and preserves project detection for every temp project created inside `mkdtemp` / `TemporaryDirectory` / `tmp_path`. |
| F-04 | Scope boundary with `nj13xp` | `.aw/records/backlog/open/20261012-nj13xp-01-nj13xp-test-finalize-sendback-e2e-runs-aw-ipd-scaffold-wi.backlog.md` and `TheRetryTriggerIsAPositiveAllowlist.test_e2e_real_finalize_checkbox_mismatch_is_retryable` (`tests/test_finalize_sendback.py:678`) | Sibling open backlog item `nj13xp` (`Work-Kind: bug`, `Blocks-Release: next`) specifically tracks passing `--dir` to `aw ipd scaffold` in `tests/test_finalize_sendback.py`. With the temp-root climb ceiling in `project_context.py`, `test_e2e_real_finalize_checkbox_mismatch_is_retryable` also stops climbing into `$TMPDIR/.aw`, while the explicit `--dir` change in `tests/test_finalize_sendback.py` remains owned by `nj13xp`. `nj13xp`'s pending plan `ivq0nr` ALSO changes `project_context.find_project_root` (its E-04 adds `if (curr / ".git").exists(): return None` after the marker check) and adds tests to `tests/test_nonsurveyable_root_refusal.py`. The two ceilings compose: this plan's temp-root check runs first in each iteration, `ivq0nr`'s `.git` check runs after the marker check, and every E-03 expectation holds under either or both. | `tests/test_finalize_sendback.py` is left untouched by this plan and declared out-of-scope with `- Carrier: nj13xp`. E-01 places the ceiling check first in the loop so the result is independent of landing order with `ivq0nr`. |

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
     - Initialize `_SANDBOX_ENV["AW_PROJECT_CEILING"] = _tempfile.gettempdir()` (adding the key to `_HOME_KEYS` is optional; nothing else reads it).
     - In a session-scoped autouse fixture receiving `tmp_path_factory`, append pytest's resolved `basetemp` directory (`os.pathsep.join(...)`) to `_SANDBOX_ENV["AW_PROJECT_CEILING"]` and `os.environ["AW_PROJECT_CEILING"]` so `tmp_path` directories (`basetemp / "<test>0"`) cannot climb past `basetemp` even if `--basetemp` is placed inside an AW project checkout.
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
     - module-level `test_tmp_path_does_not_climb_past_basetemp(tmp_path)`: asserts `find_project_root(tmp_path) is None` (pins the E-02 basetemp ceiling when run with `--basetemp` inside an AW project; V-02).
     - `test_aw_project_ceiling_stops_climb_inside_enclosing_project`: creates a directory `custom_base = self.real_proj / "custom_basetemp"` and a child `scratch = custom_base / "test_case0"`, sets `AW_PROJECT_CEILING=str(custom_base)`, and asserts `find_project_root(scratch)` is `None` and `is_project_dir(custom_base)` is `False`, while `find_project_root(self.deep_subdir)` (outside `custom_base`) still resolves to `self.real_proj`.

4. **`CHANGELOG.md` (E-04)**:
   - Add a `Fixed:` bullet under `## 2.0.0 (pending)` describing the temp-root ceiling in `find_project_root`, `is_project_dir`, and `_find_git_root` plus `AW_PROJECT_CEILING` test session isolation, with no em or en dashes.

## Deferred / out of scope (with reason)

- Passing explicit `--dir` to `aw ipd scaffold` in `tests/test_finalize_sendback.py`: owned by dedicated release-blocking bug backlog item `nj13xp` (`.aw/records/backlog/open/20261012-nj13xp-01-nj13xp-test-finalize-sendback-e2e-runs-aw-ipd-scaffold-wi.backlog.md`).
  - Carrier: nj13xp
  - Carrier-Evidence: .aw/records/backlog/done/20261012-nj13xp-01-nj13xp-test-finalize-sendback-e2e-runs-aw-ipd-scaffold-wi.backlog.md

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Run `python3 -m pytest tests/test_nonsurveyable_root_refusal.py` and verify the new polluted-temp-root and `AW_PROJECT_CEILING` tests pass.
- Run all 11 previously failing test modules (`tests/test_no_project_exit_is_cannot_run.py`, `tests/test_explicit_dir_non_project.py`, `tests/test_validator_nonsurveyable_dir.py`, `tests/test_nonsurveyable_root_refusal.py`, `tests/test_read_class_callers_refuse.py`, `tests/test_commit_run_trailers_env.py`, `tests/test_explicit_dir_subdir_resolution.py`, `tests/test_agent_commit_identity.py`, `tests/test_attention.py`, `tests/test_agent_surface_conformance.py`, `tests/test_finalize_sendback.py`) plus `tests/test_specs_date_containment.py` under a private polluted `TMPDIR` created by `tempfile.mkdtemp(prefix="awpoll")` (a HYPHEN-FREE name, F-03) populated with `.aw/records`, `.agents/plans`, and `git init`, once before E-01 (baseline, expected nonzero failures) and once after E-03 (expected `0 failed`).
- Run `aw sanitize --agent` and the full repository test suite (`python3 -m pytest`), comparing the failing-test-id set against the E-01 baseline.
- Run `python3 -m pytest -o addopts="" --basetemp=.aw/state/bt-i44j8w tests/test_nonsurveyable_root_refusal.py` (a basetemp inside this AW checkout, gitignored) to prove the E-02 basetemp ceiling; delete `.aw/state/bt-i44j8w` afterwards.

## Spec / documentation sync

- Update `CHANGELOG.md` under `## 2.0.0 (pending)` (E-04) and update the docstrings of `find_project_root`, `is_project_dir`, and `_find_git_root` in `agent_workflows/project_context.py` (E-01). No specification file requires modification: no live spec governs the upward climb (`rg -n -i 'climb|find_project_root'` over `.aw/records/specs/{approved,implemented,implementing,reviewed}` returns nothing at review), and the layout spec `20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md` lives under `.aw/records/specs/superseded/`, not `implemented/`. The new `AW_PROJECT_CEILING` variable is documented in `CHANGELOG.md` (E-04) and in the `find_project_root` docstring (E-01).

## Open questions

### OQ-01: Should the fix stop `find_project_root` at temp root containers (`_project_climb_ceilings`) in `agent_workflows/project_context.py`, or only redirect `TMPDIR` in `conftest.py`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Both layers are combined, with `_project_climb_ceilings()` in `agent_workflows/project_context.py` doing the primary work and `conftest.py` / `tests/__init__.py` exporting `AW_PROJECT_CEILING`. Redirecting `TMPDIR` to `/tmp/aw_test_tmp_XXXXXX` alone fails when `/tmp/.aw` exists on the host because `/tmp` is still an ancestor of `/tmp/aw_test_tmp_XXXXXX` (`find_project_root` walks all the way to `/`), and fails when `TMPDIR` is under `$HOME` where `~/.aw/config` exists (`project_context.resolve_verb_repo_root` at `agent_workflows/project_context.py:372`). Stopping the climb at shared temp root containers (`/tmp`, `/var/tmp`, `tempfile.gettempdir()`, `TMPDIR`/`TEMP`/`TMP`, and `AW_PROJECT_CEILING`) protects both CLI users and all test runners while allowing any AW project created in a subdirectory of a temp root to resolve normally. DEMONSTRATED AT REVIEW (HOW-question rule): a scratch copy of the tree with the E-01 helper applied cut the twelve-module polluted-`TMPDIR` run from `41 failed, 280 passed` (HEAD) to `36 passed` for the three most affected modules and `1 failed, 320 passed` for all twelve. The single remaining failure is the F-03 hyphen artifact, which goes away with a hyphen-free container. The unpolluted run gave `321 passed`, and the full scratch-copy suite gave `4 failed, 8441 passed`, where all 4 failures are scratch-copy artifacts (`doctor.version-unknown` from the scratch git, and a missing history commit) that pass on the real tree.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Paste output of a `python3 -c` one-liner (driven through `agent_workflows.project_context`) that creates a temporary root `T` with `T/.aw/records`, `T/.agents/plans`, and `T/.git`, sets `TMPDIR=T`, and prints `(is_project_dir(T), find_project_root(T), find_project_root(T/'nongit'), _find_git_root(str(T/'nongit')), is_project_dir(T/'proj'), find_project_root(T/'proj'/'sub'))` showing `(False, None, None, None, True, PosixPath('.../proj'))`, beside the E-01(c) pre-edit output of the same one-liner (which must differ, e.g. `True`/`T` in the first slots), plus `git diff -- agent_workflows/project_context.py` showing the ceiling check as the first statement of each climb loop.
  - Observed evidence:
    Pre-edit E-01(c) output:
    ```
    (True, PosixPath('/tmp/awpollprepm358vc5'), PosixPath('/tmp/awpollprepm358vc5'), '/tmp/awpollprepm358vc5', True, PosixPath('/tmp/awpollprepm358vc5/proj'))
    ```
    Post-edit output:
    ```
    (False, None, None, None, True, PosixPath('/tmp/awpollpostbmmnrd8l/proj'))
    ```
    git diff -- agent_workflows/project_context.py:
    ```diff
    diff --git a/agent_workflows/project_context.py b/agent_workflows/project_context.py
    index 8b86f9d55..1c1bdc1bf 100644
    --- a/agent_workflows/project_context.py
    +++ b/agent_workflows/project_context.py
    @@ -19,6 +19,7 @@ import functools
     import os
     import re
     import sys
    +import tempfile
     import types
     from pathlib import Path
     from typing import Any, Dict, List, Mapping, Optional
    @@ -315,15 +316,59 @@ def _is_repos_schema_mapping(value: Dict[str, Any]) -> bool:
         return all(key in _ALLOWED_REPOS_KEYS for key in value)


    +def _project_climb_ceilings() -> set[Path]:
    +    """Return resolved canonical paths that act as ceilings for project-root and git-root climbs.
    +
    +    Candidate ceilings include tempfile.gettempdir(), POSIX shared temp roots (/tmp and /var/tmp
    +    when present on disk), paths named by TMPDIR, TEMP, or TMP in os.environ, and any
    +    os.pathsep-separated path in os.environ.get("AW_PROJECT_CEILING", "").
    +    """
    +    candidates: list[str | Path] = [tempfile.gettempdir()]
    +    for posix_root in ("/tmp", "/var/tmp"):
    +        try:
    +            cand = Path(posix_root)
    +            if cand.exists():
    +                candidates.append(cand)
    +        except (OSError, RuntimeError):
    +            pass
    +    for env_var in ("TMPDIR", "TEMP", "TMP"):
    +        val = os.environ.get(env_var)
    +        if val:
    +            candidates.append(val)
    +    ceiling_env = os.environ.get("AW_PROJECT_CEILING", "")
    +    if ceiling_env:
    +        for entry in ceiling_env.split(os.pathsep):
    +            entry = entry.strip()
    +            if entry:
    +                candidates.append(entry)
    +
    +    ceilings: set[Path] = set()
    +    for candidate in candidates:
    +        try:
    +            p = Path(candidate).expanduser().resolve()
    +            ceilings.add(p)
    +        except (OSError, RuntimeError):
    +            continue
    +    return ceilings
    +
    +
     def _find_git_root(start_dir: str) -> Optional[str]:
    -    """Find the Git root directory by walking up from start_dir without subprocess."""
    +    """Find the Git root directory by walking up from start_dir without subprocess.
    +
    +    Upward walk stops and returns None when reaching a temporary root container or
    +    configured project ceiling (see ``_project_climb_ceilings``).
    +    """
    +    ceilings = _project_climb_ceilings()
         curr = Path(start_dir).resolve()
    -    while curr != curr.parent:
    +    while True:
    +        if curr in ceilings:
    +            return None
             git_dir = curr / ".git"
             if git_dir.exists():
                 return curr.as_posix()
    +        if curr == curr.parent:
    +            return None
             curr = curr.parent
    -    return None


     def _is_registered_submodule(dot_git: Path) -> bool:
    @@ -390,11 +435,20 @@ def find_project_root(start: Optional[str | Path] = None) -> Optional[Path]:
         - Submodules with their own ``.aw/`` use themselves (unchanged). Linked worktrees carry their own ``.aw/``.
         - Any other nested git repository without ``.aw/`` (its own ``.git`` directory, a vendored or scratch
           clone) stops at its own boundary and never binds to an outer project.
    +
    +    Temporary root containers and project ceilings (IPD i44j8w):
    +    - Shared temporary roots (/tmp, /var/tmp, tempfile.gettempdir(), TMPDIR/TEMP/TMP) and any paths
    +      listed in AW_PROJECT_CEILING are ceilings for project discovery: upward discovery stops and
    +      returns None when reaching any ceiling container (neither treating the ceiling itself as a
    +      project root nor escaping above it into ancestor directories).
         """

         curr = Path(start).resolve() if start is not None else Path.cwd().resolve()
    +    ceilings = _project_climb_ceilings()
         submodule_encountered = False
         while True:
    +        if curr in ceilings:
    +            return None
             if _is_project_marker(curr / ".aw") or _is_project_marker(
                 curr / ".agents", legacy=True
             ):
    @@ -580,9 +634,20 @@ def git_root_for_message(start_dir: Optional[str | Path] = None) -> Optional[str
     def is_project_dir(repo_root: str | Path) -> bool:
         """True if ``repo_root`` is (or contains) an AW project marker - i.e. a real project, not a bare
         directory with nothing to survey. Used by repo-scoped verbs to decide between running and
    -    emitting ``no_project_message`` (IPD awretrofit Order 06)."""
    +    emitting ``no_project_message`` (IPD awretrofit Order 06).
    +
    +    Returns False immediately if ``repo_root`` resolves to a temporary root container or
    +    configured project ceiling (see ``_project_climb_ceilings``).
    +    """
    +
    +    try:
    +        p = Path(repo_root).expanduser().resolve()
    +    except (OSError, RuntimeError):
    +        p = Path(repo_root)
    +
    +    if p in _project_climb_ceilings():
    +        return False

    -    p = Path(repo_root)
         return _is_project_marker(p / ".aw") or _is_project_marker(
             p / ".agents", legacy=True
         )
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste (1) `git diff -- conftest.py tests/__init__.py`; (2) the output of `python3 -m pytest -o addopts="" -v --basetemp=.aw/state/bt-i44j8w tests/test_nonsurveyable_root_refusal.py` showing `test_tmp_path_does_not_climb_past_basetemp` PASSED with a basetemp inside this AW checkout (the observation is produced by the E-02 session fixture plus `project_context.find_project_root`); and (3) `env -u AW_PROJECT_CEILING python3 -c "import tests, os; print(os.environ.get('AW_PROJECT_CEILING'))"` printing the temp dir (the `tests/__init__.py` unittest backstop).
  - Observed evidence:
    (1) git diff -- conftest.py tests/__init__.py:
    ```diff
    diff --git a/conftest.py b/conftest.py
    index fbfc45a23..68490b563 100644
    --- a/conftest.py
    +++ b/conftest.py
    @@ -224,6 +224,7 @@ _atexit.register(_shutil.rmtree, _AW_TEST_SANDBOX, True)
     _SANDBOX_ENV = {
         "AW_HOME": _AW_TEST_SANDBOX,
         "XDG_CONFIG_HOME": os.path.join(_AW_TEST_SANDBOX, "xdg-config"),
    +    "AW_PROJECT_CEILING": _tempfile.gettempdir(),
     }
     os.environ.update(_SANDBOX_ENV)

    @@ -241,6 +242,16 @@ def _restore_home_sandbox():
             _shutil.rmtree(_xdg_dir, ignore_errors=True)


    +@pytest.fixture(scope="session", autouse=True)
    +def _register_basetemp_project_ceiling(tmp_path_factory: pytest.TempPathFactory):
    +    """Register pytest's resolved basetemp as an AW project climb ceiling."""
    +    basetemp = str(tmp_path_factory.getbasetemp().resolve())
    +    current = _SANDBOX_ENV.get("AW_PROJECT_CEILING", "")
    +    updated = f"{current}{os.pathsep}{basetemp}" if current else basetemp
    +    _SANDBOX_ENV["AW_PROJECT_CEILING"] = updated
    +    os.environ["AW_PROJECT_CEILING"] = updated
    +
    +
     # --------------------------------------------------------------------------------------
     # Per-test hang guard: dual CPU budget + wall ceiling (IPD 6ye76g).
     # --------------------------------------------------------------------------------------
    diff --git a/tests/__init__.py b/tests/__init__.py
    index 9c21baa18..13c84f088 100644
    --- a/tests/__init__.py
    +++ b/tests/__init__.py
    @@ -35,6 +35,7 @@ if not os.environ.get("AW_HOME"):
     # preventing unintended external host subprocess spawns (e.g. opencode export)
     # when tests drive runner code without an injected launcher double.
     os.environ.setdefault("AW_IN_TEST_SESSION", "1")
    +os.environ.setdefault("AW_PROJECT_CEILING", tempfile.gettempdir())

     # Network/credential guard: a test may create a repo with a real remote (e.g. an
     # https://github.com/... origin) and then reach code that probes it (git ls-remote /
    ```
    (2) python3 -m pytest -o addopts="" -v --basetemp=.aw/state/bt-i44j8w tests/test_nonsurveyable_root_refusal.py:
    ```
    tests/test_nonsurveyable_root_refusal.py::test_tmp_path_does_not_climb_past_basetemp PASSED [  6%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_case_d_git_repo_without_aw_explicit PASSED [ 13%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_case_c_no_project_no_git_explicit PASSED [ 20%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_aw_project_ceiling_stops_climb_inside_enclosing_project PASSED [ 26%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_case_b_project_subdirectory_explicit PASSED [ 33%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_non_explicit_variant_git_repo_without_aw PASSED [ 40%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_non_explicit_variant_no_project_no_git PASSED [ 46%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_stray_markers_in_temp_root_do_not_poison_children PASSED [ 53%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_fixture_preconditions PASSED [ 60%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_purity_and_silence PASSED [ 66%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_case_a_real_project_root PASSED [ 73%]
    tests/test_nonsurveyable_root_refusal.py::FindProjectRootGitBoundariesAndSubmodulesTests::test_inner_git_boundary_stops_discovery_under_outer_aw_project PASSED [ 80%]
    tests/test_nonsurveyable_root_refusal.py::FindProjectRootGitBoundariesAndSubmodulesTests::test_git_submodule_with_own_aw_uses_itself_without_notice PASSED [ 86%]
    tests/test_nonsurveyable_root_refusal.py::FindProjectRootGitBoundariesAndSubmodulesTests::test_nongit_aw_project_subdirectories_discover_root PASSED [ 93%]
    tests/test_nonsurveyable_root_refusal.py::FindProjectRootGitBoundariesAndSubmodulesTests::test_git_submodule_without_aw_resolves_to_parent_with_notice PASSED [100%]
    ============================== 15 passed in 1.41s ==============================
    ```
    (3) env -u AW_PROJECT_CEILING python3 -c "import tests, os; print(os.environ.get('AW_PROJECT_CEILING'))":
    ```
    /tmp
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste `git diff --stat -- tests/test_nonsurveyable_root_refusal.py` and the `python3 -m pytest -o addopts="" -v tests/test_nonsurveyable_root_refusal.py` output showing every collected test PASSED, including the new tests that pin (1) the polluted temp root and its non-project children resolving to no project with CLI exit 2 `cannot-run`, (2) a real child project still resolving, and (3) the `AW_PROJECT_CEILING` containment (test names are non-binding pointers).
  - Observed evidence:
    git diff --stat -- tests/test_nonsurveyable_root_refusal.py:
    ```
     tests/test_nonsurveyable_root_refusal.py | 124 +++++++++++++++++++++++++++++++
     1 file changed, 124 insertions(+)
    ```
    python3 -m pytest -o addopts="" -v tests/test_nonsurveyable_root_refusal.py:
    ```
    tests/test_nonsurveyable_root_refusal.py::test_tmp_path_does_not_climb_past_basetemp PASSED [  6%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_purity_and_silence PASSED [ 13%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_aw_project_ceiling_stops_climb_inside_enclosing_project PASSED [ 20%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_case_a_real_project_root PASSED [ 26%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_case_b_project_subdirectory_explicit PASSED [ 33%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_stray_markers_in_temp_root_do_not_poison_children PASSED [ 40%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_non_explicit_variant_git_repo_without_aw PASSED [ 46%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_case_d_git_repo_without_aw_explicit PASSED [ 53%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_fixture_preconditions PASSED [ 60%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_non_explicit_variant_no_project_no_git PASSED [ 66%]
    tests/test_nonsurveyable_root_refusal.py::NonsurveyableRootRefusalTests::test_case_c_no_project_no_git_explicit PASSED [ 73%]
    tests/test_nonsurveyable_root_refusal.py::FindProjectRootGitBoundariesAndSubmodulesTests::test_nongit_aw_project_subdirectories_discover_root PASSED [ 80%]
    tests/test_nonsurveyable_root_refusal.py::FindProjectRootGitBoundariesAndSubmodulesTests::test_git_submodule_without_aw_resolves_to_parent_with_notice PASSED [ 86%]
    tests/test_nonsurveyable_root_refusal.py::FindProjectRootGitBoundariesAndSubmodulesTests::test_git_submodule_with_own_aw_uses_itself_without_notice PASSED [ 93%]
    tests/test_nonsurveyable_root_refusal.py::FindProjectRootGitBoundariesAndSubmodulesTests::test_inner_git_boundary_stops_discovery_under_outer_aw_project PASSED [100%]
    ============================== 15 passed in 1.29s ==============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste (1) the `git diff -- CHANGELOG.md` showing the new `Fixed:` entry with zero em/en dashes, (2) the summary line of the twelve-module run under the same hyphen-free polluted `TMPDIR` as E-01(b), showing `0 failed`, beside the E-01(b) baseline summary showing nonzero failures; and (3) the `aw sanitize --agent` result record, and the bare `python3 -m pytest` summary line and failing-test-id set compared against the E-01(a) baseline, with zero new failing ids.
  - Observed evidence:
    (1) git diff -- CHANGELOG.md:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index ed070db80..c5869382e 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -25,6 +25,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th
     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

     - Fixed: project_context.resolve_project_context and project_context.project_config_dir now read user configuration through config.config_dir() (honoring AW_CONFIG_DIR and XDG_CONFIG_HOME) instead of a hard-coded ~/.config/agent-workflows path when user_config_dir is omitted.
    +- Fixed: project_context.find_project_root, is_project_dir, and _find_git_root now treat shared system temp roots (/tmp, /var/tmp, tempfile.gettempdir(), TMPDIR/TEMP/TMP) and any paths listed in the new AW_PROJECT_CEILING environment variable (an os.pathsep-separated list) as climb ceilings: a listed directory is never itself a project or git root and upward climbs never pass above it into parent directories, while subdirectories continue to resolve normally, eliminating test fixture pollution from stray markers.
     - Fixed: the shipped conformance host matrix (.aw/system/workflows/conformance/tools/host_matrix.json) no longer carries unproven supported booleans, so aw releases readiness no longer reports 19 stale capability claims; host support is established only by probe evidence recorded in the capability registry.
     - Fixed: aw index all and aw index all --check now emit a single aggregate aw.agent/v1 result record under --agent and a single valid JSON document under --json, ensuring record exit parity with the process exit code and closing multi-document parsing failures.
     - Fixed: aw index plans, prompts, research, and all now refuse with exit code 2 (cannot-run) and a structured record when the records directory does not exist, instead of crashing with a FileNotFoundError traceback.
    ```
    (2) Twelve-module run under polluted TMPDIR:
    Baseline E-01(b): `20 failed, 305 passed in 66.97s (0:01:06)` (EXIT: 1)
    Post-edit: `328 passed in 39.65s` (EXIT: 0) (0 failed)
    (3) aw sanitize --agent:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5227,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    Bare python3 -m pytest summary and failing-test-id comparison:
    Baseline E-01(a): `702 passed in 25.70s`, failing-test-id set: `set()`
    Post-edit: `702 passed in 26.56s`, failing-test-id set: `set()`
    Zero new failing test ids.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`aw ipd set approved i44j8w --by-human`) or dispatch by an authorized runner turn. Open questions: OQ-01 is resolved; none remain. Start execution with `aw ipd begin i44j8w`. `- Scope-Paths:` is a DECLARATION reconciled at finalize: if an out-of-scope edit proves necessary, make it and justify it with `--scope-reason <path>=<why>` (and `--scope-ack` for a declared path left unmodified). HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; never claim a pass you did not run, and run the full suite bare (`python3 -m pytest`). Commit only the declared paths plus this plan through `aw commit i44j8w -- <paths>` (never `git add -A`, `-a`, or `--no-verify`), verify `git diff --cached --name-only` first, never commit the polluted temp container or `.aw/state/bt-i44j8w`, run `aw sanitize --agent`, and never push or tag. Lifecycle: under `aw oc run` / `aw agy run` the runner owns `finalize` after its merge-and-revalidate gate, so do NOT run `aw ipd finalize` inside the runner; when executed by hand, run `aw ipd finalize i44j8w` once `aw ipd lint --phase pre-transition` conforms and `V-01`..`V-04` hold pasted evidence with `Result: pass`. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.
