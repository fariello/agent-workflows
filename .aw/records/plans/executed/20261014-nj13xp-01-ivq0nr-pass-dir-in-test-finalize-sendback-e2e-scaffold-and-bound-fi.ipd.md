# IPD: Pass --dir in test_finalize_sendback e2e scaffold and bound find_project_root at enclosing git root

- Date: 2026-10-14
- Kind: child
- Concern: Test isolation in test_finalize_sendback e2e and project-root discovery boundary at enclosing git root.
- Scope: Wire --dir into aw ipd scaffold via resolve_verb_repo_root, pass --dir in test_finalize_sendback e2e subprocesses, and stop find_project_root from climbing past an uninstalled .git boundary.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/ipd_authoring.py, agent_workflows/project_context.py, tests/test_finalize_sendback.py, tests/test_ipd_authoring.py, tests/test_nonsurveyable_root_refusal.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: nj13xp
- Blocks-Release: next
- Set: nj13xp
- Order: 1
- Highest E allocated: 07
- Author: antigravity
- Id: ivq0nr

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ivq0nr verified (set nj13xp, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-15 reviewed (/plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (OPEN, escalated OQ-01), PR-002..PR-007 fixed
- 2026-10-14 to-review (antigravity): authored review-ready child IPD for backlog nj13xp

- 2026-10-14 draft (antigravity): created.

## Goal

Prevent `aw ipd scaffold` in `tests/test_finalize_sendback.py` from writing stray `e2e-test-plan.ipd.md` files into an enclosing `.aw/records/plans/pending/` tree (such as `/tmp/.aw/records/plans/pending/` or a parent checkout) by wiring `--dir` through `project_context.resolve_verb_repo_root` on `aw ipd scaffold`, passing `--dir` in the e2e test's subprocess invocations, and bounding `project_context.find_project_root` so upward discovery stops at an enclosing `.git` root that lacks an AW marker.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Wire `--dir` into `aw ipd scaffold` and pass `--dir` in `test_finalize_sendback` e2e

- [x] E-01 Register `--dir` on `p_ipd_scaffold` in `cli.build_parser` (`agent_workflows/cli.py:1790-1854`).
  - Depends on: none
  - Expected outcome: `p_ipd_scaffold.add_argument("--dir", default=None, help="Target repository root (default: discovered project root or CWD).")` is registered on the `ipd scaffold` subparser in `agent_workflows/cli.py`, matching sibling `ipd` subcommands (`begin`, `finalize`, `set`, `coverage`) and sibling authoring verbs (`backlog new`, `specs new`, `releases new`, `research new`).
  - Execution state: performed

- [x] E-02 Route `ipd_authoring.run_scaffold` (`agent_workflows/ipd_authoring.py:436-671`) through `project_context.resolve_verb_repo_root` for project-root resolution.
  - Depends on: E-01
  - Expected outcome: `ipd_authoring.run_scaffold` resolves `repo_root = _ctx.resolve_verb_repo_root(getattr(args, "dir", None))` once at entry, passes `repo_root=repo_root` into `ipd_authoring._setid_length_guard`, passes `repo_root` to `_backlog.find_item(repo_root, from_backlog)`, and substitutes `repo_root` for the `find_project_root(Path.cwd())` result in the existing derived-destination composition when `--path` is omitted (`repo_root / ".aw" / "records" / "plans" / _rp.target_subdir("plans", "to-review")`, unchanged otherwise; do NOT introduce a second path mechanism such as `resolve_record_path` here). The resolution must happen BEFORE the `_setid_length_guard` call, since that guard runs first in `run_scaffold`. An explicit `--path` keeps its current semantics.
  - Execution state: performed

- [x] E-03 Pass `"--dir", str(repo_dir)` to the `ipd` subprocess calls in `TheRetryTriggerIsAPositiveAllowlist.test_e2e_real_finalize_checkbox_mismatch_is_retryable` (`tests/test_finalize_sendback.py:540-658`).
  - Depends on: E-02
  - Expected outcome: The `ipd scaffold`, `ipd begin`, and both `ipd finalize` subprocess invocations in `TheRetryTriggerIsAPositiveAllowlist.test_e2e_real_finalize_checkbox_mismatch_is_retryable` pass `"--dir", str(repo_dir)` explicitly, ensuring the scaffolded `E2E Test Plan` and its lifecycle transitions stay confined to `repo_dir`.
  - Execution state: performed

### Task group 2: Bound `find_project_root` at an enclosing `.git` root and add regression coverage

- [x] E-04 Bound `project_context.find_project_root` (`agent_workflows/project_context.py:315-335`) at an enclosing `.git` directory that lacks an AW marker.
  - Depends on: none
  - Expected outcome: In `project_context.find_project_root`, immediately after checking `_is_project_marker(curr / ".aw") or _is_project_marker(curr / ".agents", legacy=True)`, if `(curr / ".git").exists()` is True, `find_project_root` returns `None` instead of climbing past the git repository boundary into an outer directory's `.aw/` marker. GATED ON OQ-01: perform this item only if the maintainer answers OQ-01 "bound the climb"; if the answer is "keep discovery git-blind", mark E-04 and V-04 `blocked` with the OQ-01 answer cited, drop E-05 parts that depend on E-04 (scaffold-without-`--dir` in a nested repo, and the `find_project_root` boundary tests), and proceed. When performed, ALSO rewrite, in the same edit, the three docstrings this change makes false: `project_context.find_project_root` ("git presence is NOT a marker" stays true, but it must now state that an enclosing `.git` is a CEILING), `project_context.no_project_message` (the "PROBING FOR GIT HERE ... MUST NEVER BE PROMOTED INTO `find_project_root`" paragraph), and `project_context.classify_project_dir` ("Git-blind"), each citing OQ-01's answer.
  - Execution state: performed

- [x] E-05 Add regression tests in `tests/test_ipd_authoring.py` and `tests/test_nonsurveyable_root_refusal.py` for `aw ipd scaffold --dir` and the `.git` climb boundary.
  - Depends on: E-02, E-04
  - Expected outcome: `tests/test_ipd_authoring.py` tests that (1) `aw ipd scaffold --dir <target> --apply` writes inside `<target>` without climbing to an ancestor `.aw/`, and (2) `aw ipd scaffold --apply` without `--dir` inside an uninstalled git repo nested under an outer `.aw/` project writes to the inner git repo's `.aw/records/plans/pending/` rather than the outer project (run from the INNER REPO ROOT: when `find_project_root` returns `None`, `resolve_verb_repo_root` falls back to cwd, not to the git root, so from a subdirectory the plan would land under that subdirectory; pin whichever behavior the test runs, and do not claim the subdirectory case is handled); `tests/test_nonsurveyable_root_refusal.py` tests that `project_context.find_project_root` stops at an inner `.git` boundary nested under an outer `.aw/` project while still discovering `.aw/` from subdirectories of a git-backed or non-git AW project.
  - Execution state: performed

- [x] E-06 Run the targeted regression tests and the full `python3 -m pytest` suite.
  - Depends on: E-03, E-05
  - Expected outcome: `python3 -m pytest tests/test_finalize_sendback.py tests/test_ipd_authoring.py tests/test_nonsurveyable_root_refusal.py tests/test_explicit_dir_non_project.py tests/test_no_project_exit_is_cannot_run.py` pass, and the bare full `python3 -m pytest` suite introduces no new failures (any failure must be shown also failing on the pre-change base commit, with that run pasted). Also reproduce the backlog's leak condition: run `tests/test_finalize_sendback.py` with `TMPDIR` set to a directory nested under a scratch AW project (a temp dir containing `.aw/records/`), and show that the scratch project's `.aw/records/plans/pending/` holds no `*e2e-test-plan.ipd.md` afterwards.
  - Execution state: performed

- [x] E-07 Add one `- Fixed:` entry to the topmost pending section of `CHANGELOG.md` (user-facing prose: no em or en dashes) stating that `aw ipd scaffold` now accepts `--dir` and no longer writes a plan into an enclosing project; if E-04 was performed, state also that project discovery stops at an enclosing git repository that has no agent-workflows install.
  - Depends on: E-06
  - Expected outcome: one `CHANGELOG.md` line added, with zero em or en dashes, matching what was actually performed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Write and authoring verbs resolve their target repository root through `project_context.resolve_verb_repo_root` (`agent_workflows/project_context.py:356-414`), which honors an explicit `--dir` verbatim with no upward climb (`Path(explicit_dir).expanduser().resolve()`) and climbs via `project_context.find_project_root` (`agent_workflows/project_context.py:315-335`) only when `explicit_dir` is `None`.
- Project marker recognition in `project_context._is_project_marker` (`agent_workflows/project_context.py:293-312`) requires `(marker_dir / "records").is_dir()` or `(marker_dir / "config").is_dir()` for `.aw/` (and `plans`, `specs`, `config`, or `aw.toml` for legacy `.agents/`). Any stray creation of `/tmp/.aw/records/plans/pending` turns `/tmp` into a valid AW project root for every test creating temporary directories under `/tmp`.
- In `project_context.find_project_root` (`agent_workflows/project_context.py:315-335`), a bare `.git` directory is deliberately not treated as an AW project marker (`awretrofit` Order 06 OQ-01; `quqyc4` E-02), and non-git `.aw/` projects remain supported when `_is_project_marker` is checked before the `(curr / ".git").exists()` ceiling.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Severity | Location | Finding | Evidence |
|---|----------|----------|---------|----------|
| F-1 | High | `TheRetryTriggerIsAPositiveAllowlist.test_e2e_real_finalize_checkbox_mismatch_is_retryable` (`tests/test_finalize_sendback.py:540-559`) | The e2e test initializes a bare git repo (`repo_dir`) with no `.aw/` directory and invokes `python3 -m agent_workflows ipd scaffold ... --title "E2E Test Plan" --apply` with `cwd=repo_dir` and no `--dir`. When an ancestor of `repo_dir` has `.aw/records` or `.aw/config` (e.g., `/tmp/.aw/records` or `$TMPDIR` inside a checkout or under `$HOME`), `aw ipd scaffold` climbs out of `repo_dir` across `repo_dir/.git` and writes `20261012-testset-01-*-e2e-test-plan.ipd.md` into the ancestor's `.aw/records/plans/pending/`. Once `/tmp/.aw/records/plans/pending` exists, `/tmp` satisfies `project_context._is_project_marker` (`agent_workflows/project_context.py:293-312`), causing 39 non-project tests to fail with `'the specified directory is inside an AW project'`. | `TheRetryTriggerIsAPositiveAllowlist.test_e2e_real_finalize_checkbox_mismatch_is_retryable` (`tests/test_finalize_sendback.py:540-563`) globs `repo_dir / ".aw" / "records" / "plans" / "pending" / "*.ipd.md"` and fails with `IndexError: list index out of range` when the file is written to the ancestor. |
| F-2 | High | `cli.build_parser` (`agent_workflows/cli.py:1790-1854`) and `ipd_authoring.run_scaffold` (`agent_workflows/ipd_authoring.py:436-578`) | `p_ipd_scaffold` does not register `--dir`, and `ipd_authoring.run_scaffold` calls `project_context.find_project_root` (`Path.cwd()`) directly in three places (`ipd_authoring._setid_length_guard` at `agent_workflows/ipd_authoring.py:424`, `from_backlog` resolution at `agent_workflows/ipd_authoring.py:494`, and derived destination path resolution at `agent_workflows/ipd_authoring.py:562`) instead of calling `project_context.resolve_verb_repo_root` (`agent_workflows/project_context.py:356-414`). | Passing `--dir` to `aw ipd scaffold` currently exits 2 in `argparse`, whereas sibling `ipd` verbs (`begin`, `finalize`, `set`, `coverage`) and authoring verbs (`backlog new`, `specs new`, `releases new`, `research new`) accept `--dir` and route through `project_context.resolve_verb_repo_root`. |
| F-3 | Medium | `project_context.find_project_root` (`agent_workflows/project_context.py:315-335`) | `project_context.find_project_root` walks `[curr] + list(curr.parents)` without stopping at an enclosing `.git` boundary that lacks `.aw`/`.agents`. From any uninstalled git repository nested under `$HOME` (when `~/.aw/config` exists), `/tmp` (if `/tmp/.aw` exists), or an outer AW checkout, upward discovery escapes the inner git repository and attaches to the outer `.aw/`. `doctor._run_doctor` (`agent_workflows/doctor.py:2348-2354`) previously added a local workaround (`if git_root is not None and climbed in Path(git_root).resolve().parents: repo_root = cwd`) for this exact climb across `.git` because `project_context.py` was out of scope for IPD `sjsb04`. | In `project_context.find_project_root` (`agent_workflows/project_context.py:329-335`), the loop checks `_is_project_marker(curr / ".aw") or _is_project_marker(curr / ".agents", legacy=True)` and continues to `curr.parents` even when `(curr / ".git").exists()` is True. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/cli.py` (`E-01`)**:
   - In `cli.build_parser` (`agent_workflows/cli.py:1790-1854`), add `--dir` to `p_ipd_scaffold`:
     ```python
     p_ipd_scaffold.add_argument(
         "--dir",
         default=None,
         help="Target repository root (default: discovered project root or CWD).",
     )
     ```
2. **`agent_workflows/ipd_authoring.py` (`E-02`)**:
   - In `ipd_authoring.run_scaffold` (`agent_workflows/ipd_authoring.py:436-671`), resolve `repo_root` once via `project_context.resolve_verb_repo_root`:
     ```python
     from agent_workflows import project_context as _ctx

     repo_root = _ctx.resolve_verb_repo_root(getattr(args, "dir", None))
     ```
   - Pass `repo_root=repo_root` to `ipd_authoring._setid_length_guard` (`agent_workflows/ipd_authoring.py:456`).
   - Use `repo_root` in the `from_backlog` lookup (`_backlog.find_item(repo_root, from_backlog)` at `agent_workflows/ipd_authoring.py:489-497`).
   - Use `repo_root` when deriving the destination path under `pending/` in `ipd_authoring.run_scaffold` (`agent_workflows/ipd_authoring.py:559-578`), removing the redundant `find_project_root(Path.cwd())` call.
3. **`tests/test_finalize_sendback.py` (`E-03`)**:
   - In `TheRetryTriggerIsAPositiveAllowlist.test_e2e_real_finalize_checkbox_mismatch_is_retryable` (`tests/test_finalize_sendback.py:540-658`), append `"--dir", str(repo_dir)` to the `ipd scaffold`, `ipd begin`, and both `ipd finalize` subprocess command lists.
4. **`agent_workflows/project_context.py` (`E-04`)**:
   - In `project_context.find_project_root` (`agent_workflows/project_context.py:315-335`), stop upward traversal when `curr` has a `.git` entry (directory or worktree gitfile) and no valid `.aw` or legacy `.agents` project marker:
     ```python
     for curr in [curr] + list(curr.parents):
         if _is_project_marker(curr / ".aw") or _is_project_marker(
             curr / ".agents", legacy=True
         ):
             return curr
         if (curr / ".git").exists():
             return None
     return None
     ```
5. **`tests/test_ipd_authoring.py` and `tests/test_nonsurveyable_root_refusal.py` (`E-05`, `E-06`)**:
   - Add unit and subprocess tests in `IpdAuthoringTests` (`tests/test_ipd_authoring.py:41-210`) verifying `aw ipd scaffold --dir <repo_dir> --apply` and `aw ipd scaffold --apply` inside an uninstalled git repo nested under an outer AW project.
   - Add unit tests in `tests/test_nonsurveyable_root_refusal.py` (`TestFindProjectRootRequiresMarker` at `tests/test_nonsurveyable_root_refusal.py:39-84`) verifying `project_context.find_project_root` returns `None` when an inner `.git` repo with no `.aw` marker is nested inside an outer `.aw` project, while still returning the project root when called from a subdirectory of a git-backed or non-git `.aw` project.

## Deferred / out of scope (with reason)

- Removing `doctor.run`'s local git-root bound (now redundant if E-04 lands): a separate cleanup; leaving it is behavior-neutral.
  - Carrier-Declined: redundant-but-correct code, no defect.

## Scope check

- Over-scope: none.
- Under-scope: none; both items in backlog `nj13xp` (passing `--dir` in `tests/test_finalize_sendback.py` and bounding project discovery at the enclosing git root in `agent_workflows/project_context.py`, plus the prerequisite `--dir` support on `aw ipd scaffold`) are covered.

## Required tests / validation

- Run `python3 -m pytest tests/test_finalize_sendback.py tests/test_ipd_authoring.py tests/test_nonsurveyable_root_refusal.py tests/test_explicit_dir_non_project.py tests/test_no_project_exit_is_cannot_run.py`.
- Run the full repository test suite via `python3 -m pytest`.

## Spec / documentation sync

- `CHANGELOG.md` gets one `- Fixed:` entry (E-07). If E-04 is performed, the `find_project_root`, `no_project_message` and `classify_project_dir` docstrings are rewritten in E-04, because they currently state the git-blind rule this change reverses. No `.spec.md` governs `find_project_root`. Original note: `--dir` on `aw ipd scaffold` and stopping `find_project_root` at an uninstalled `.git` boundary align `aw ipd scaffold` and `project_context.find_project_root` with the existing `resolve_verb_repo_root` and `sjsb04` contracts without changing any spec-governed CLI grammar or schema.

## Open questions

### OQ-01: Should `project_context.find_project_root` stop climbing when it reaches a `.git` boundary that lacks an AW marker?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Carrier: ivq0nr
- Resolution or deferral rationale: Maintainer decision 2026-10-15: Bound the climb at git boundaries, with a submodule exception: (1) A registered submodule without its own .aw/ resolves to its parent project. Detect it without spawning git: its .git is a file whose gitdir sits under the parent's .git/modules/, and that admin dir has no commondir. Print one notice line saying the parent project was used. (2) Any other nested git repository without .aw/ (its own .git directory, a vendored or scratch clone) stops at its own boundary and never binds to an outer project. (3) A submodule with its own .aw/ uses itself (unchanged). Linked worktrees of the same project are unaffected; they carry their own .aw/, and plan fnnwj3 handles external worktrees. (4) When no project is found, do not silently create records in the current directory. Refuse with a message suggesting aw install or --dir. Perform E-01..E-03 (the --dir test fix) and a revised E-04 implementing rules 1-4. Update the docstrings that say discovery is git-blind, and the no_project_message docstring. Add outcome tests for all four rules, using real temp repos with a real submodule.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: `git diff -- agent_workflows/cli.py` showing `--dir` added to `p_ipd_scaffold`, and output of `python3 -m agent_workflows ipd scaffold --help` showing `--dir DIR`, plus the pre-change output of `ipd scaffold --dir <x> ...` exiting 2 (unrecognized argument) for contrast.
  - Observed evidence:
    `git diff -- agent_workflows/cli.py`:
    ```diff
    @@ -1793,6 +1793,11 @@ def _build_parser() -> argparse.ArgumentParser:
             parents=[common],
             help="Write a new conformant IPD skeleton (dry-run by default; --apply to write).",
         )
    +    p_ipd_scaffold.add_argument(
    +        "--dir",
    +        default=None,
    +        help="Target repository root (default: discovered project root or CWD).",
    +    )
         p_ipd_scaffold.add_argument("--kind", required=True, help="child or orchestrator.")
         p_ipd_scaffold.add_argument(
             "--title", required=True, help="IPD title (after the H1 'IPD: ')."
    ```
    `python3 -m agent_workflows ipd scaffold --help`:
    ```text
    options:
      ...
      --dir DIR             Target repository root (default: discovered project
                            root or CWD).
    ```
    Pre-change contrast: `python3 -m agent_workflows ipd scaffold --dir foo --kind child --title T --set test --order 1 --author test --priority medium --work-kind chore`:
    ```text
    agent-workflows: error: unrecognized arguments: --dir foo
    (exit code 2)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `git diff -- agent_workflows/ipd_authoring.py` showing `run_scaffold` resolving `repo_root = _ctx.resolve_verb_repo_root(getattr(args, "dir", None))` and threading `repo_root` into `_setid_length_guard`, `_backlog.find_item`, and derived destination path resolution; AND the behavioral proof: pasted output of `aw ipd scaffold --dir <target> ... --apply` run from a cwd under a DIFFERENT AW project, showing the written path is under `<target>` and the cwd project's `pending/` is unchanged (covered by the E-05 test; paste its passing output).
  - Observed evidence:
    `git diff -- agent_workflows/ipd_authoring.py`:
    ```diff
    @@ -434,6 +434,9 @@ def _setid_length_guard(setid, *, verb: str, repo_root=None) -> int:


     def run_scaffold(args: argparse.Namespace) -> int:
    +    from agent_workflows import project_context as _ctx
    +
    +    repo_root = _ctx.resolve_verb_repo_root(getattr(args, "dir", None))
         kind = getattr(args, "kind", None)
         if kind not in S.KINDS:
             print("error: --kind must be child or orchestrator")
    @@ -453,7 +456,7 @@ def run_scaffold(args: argparse.Namespace) -> int:
             return 2
         # setidlen x75obw E-06 (catalog I-17): the ONE shared setid-length guard, not a local comparison.
         # Refuses over `max_length`; WARNS and proceeds over `warn_length`.
    -    if _setid_length_guard(set_name, verb="aw ipd scaffold") != 0:
    +    if _setid_length_guard(set_name, repo_root=repo_root, verb="aw ipd scaffold") != 0:
             return 2
         if kind == S.KIND_ORCHESTRATOR and order != 0:
             print("error: orchestrator Order must be 0")
    @@ -488,13 +491,8 @@ def run_scaffold(args: argparse.Namespace) -> int:
         blocks_release = None
         if from_backlog:
             from agent_workflows import backlog as _backlog

    -        try:
    -            _fb_root = _ctx_fb.find_project_root(Path.cwd()) or Path.cwd()
    -        except Exception:
    -            _fb_root = Path.cwd()
    -        _item = _backlog.find_item(_fb_root, from_backlog)
    +        _item = _backlog.find_item(repo_root, from_backlog)
             if _item is None:
                 print(f"error: --from-backlog {from_backlog}: no backlog item has that id")
                 return 2
    @@ -557,14 +555,12 @@ def run_scaffold(args: argparse.Namespace) -> int:
                     )
         else:
             from agent_workflows import plans_refs as _refs

    -        try:
    -            repo_root = _ctx.find_project_root(Path.cwd())
    -        except Exception:
    -            repo_root = None
    -        if repo_root is None:
    -            repo_root = Path.cwd()
    +        explicit_dir = getattr(args, "dir", None)
    +        if explicit_dir is None and _ctx.find_project_root() is None:
    +            msg = _ctx.no_project_message("ipd scaffold", repo_root, explicit=False)
    +            print(f"error: {msg}")
    +            return 2
             pending = (
                 repo_root  # type: ignore[operator]  # checker-limitation: target_subdir returns str for plans
                 / ".aw"
    ```
    Behavioral proof: `python3 -m pytest tests/test_ipd_authoring.py -k test_scaffold_with_dir_writes_inside_target_without_climbing`:
    ```text
    1 passed in 1.75s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `git diff -- tests/test_finalize_sendback.py` showing `"--dir", str(repo_dir)` passed to the `ipd scaffold`, `ipd begin`, and `ipd finalize` subprocess calls in `test_e2e_real_finalize_checkbox_mismatch_is_retryable`, plus passing pytest output for `python3 -m pytest tests/test_finalize_sendback.py`, plus the E-06 leak reproduction (TMPDIR under a scratch AW project) showing zero `*e2e-test-plan.ipd.md` files in that project's `pending/`.
  - Observed evidence:
    `git diff -- tests/test_finalize_sendback.py`:
    ```diff
    @@ -544,6 +544,8 @@ class TheRetryTriggerIsAPositiveAllowlist(unittest.TestCase):
                         "agent_workflows",
                         "ipd",
                         "scaffold",
    +                    "--dir",
    +                    str(repo_dir),
                         "--kind",
                         "child",
                         "--order",
    @@ -609,6 +611,8 @@ class TheRetryTriggerIsAPositiveAllowlist(unittest.TestCase):
                         "ipd",
                         "begin",
                         plan_file.name,
    +                    "--dir",
    +                    str(repo_dir),
                         "--actor",
                         "tester",
                     ],
    @@ -645,6 +649,8 @@ class TheRetryTriggerIsAPositiveAllowlist(unittest.TestCase):
                         "ipd",
                         "finalize",
                         plan_file.name,
    +                    "--dir",
    +                    str(repo_dir),
                         "--actor",
                         "tester",
                         "--message",
    ```
    Passing pytest runner output:
    ```text
    python3 -m pytest tests/test_finalize_sendback.py
    62 passed in 3.47s
    ```
    Leak reproduction check with TMPDIR nested under scratch AW project:
    ```text
    Pytest exit code: 0
    Stray plans in scratch project pending: []
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `git diff -- agent_workflows/project_context.py` showing `if (curr / ".git").exists(): return None` immediately after the `_is_project_marker` check in `find_project_root` and the three rewritten docstrings, plus the OQ-01 answer quoted; OR, if OQ-01 was answered (b), `Result: blocked` citing that answer and an empty `git diff -- agent_workflows/project_context.py`.
  - Observed evidence:
    OQ-01 maintainer decision quoted:
    "Maintainer decision 2026-10-15: Bound the climb at git boundaries, with a submodule exception: (1) A registered submodule without its own .aw/ resolves to its parent project. Detect it without spawning git: its .git is a file whose gitdir sits under the parent's .git/modules/, and that admin dir has no commondir. Print one notice line saying the parent project was used. (2) Any other nested git repository without .aw/ (its own .git directory, a vendored or scratch clone) stops at its own boundary and never binds to an outer project. (3) A submodule with its own .aw/ uses itself (unchanged). Linked worktrees of the same project are unaffected; they carry their own .aw/, and plan fnnwj3 handles external worktrees. (4) When no project is found, do not silently create records in the current directory. Refuse with a message suggesting aw install or --dir. Perform E-01..E-03 (the --dir test fix) and a revised E-04 implementing rules 1-4. Update the docstrings that say discovery is git-blind, and the no_project_message docstring. Add outcome tests for all four rules, using real temp repos with a real submodule."
    `git diff -- agent_workflows/project_context.py`:
    ```diff
    +def _is_registered_submodule(dot_git: Path) -> bool:
    ...
    +        dot_git = curr / ".git"
    +        if dot_git.exists():
    +            if _is_registered_submodule(dot_git):
    +                submodule_encountered = True
    +            else:
    +                return None
    ```
    and the three rewritten docstrings citing OQ-01 in `find_project_root`, `no_project_message`, and `classify_project_dir`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `git diff -- tests/test_ipd_authoring.py tests/test_nonsurveyable_root_refusal.py` and passing pytest output for the new `--dir` and `.git`-boundary regression tests in both files.
  - Observed evidence:
    `git diff -- tests/test_ipd_authoring.py tests/test_nonsurveyable_root_refusal.py` adds `test_scaffold_with_dir_writes_inside_target_without_climbing` and `test_scaffold_without_dir_in_uninstalled_repo_or_non_project_refuses` to `ScaffoldTests`, and adds `FindProjectRootGitBoundariesAndSubmodulesTests` covering rules 1, 2, 3, and non-git discovery.
    Pytest runner output:
    ```text
    python3 -m pytest tests/test_ipd_authoring.py
    31 passed in 2.48s
    python3 -m pytest tests/test_nonsurveyable_root_refusal.py
    12 passed in 3.00s
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Pasted runner output from `python3 -m pytest` showing no new failures versus the pre-change base (paste any base run needed to prove a failure pre-exists), plus the leak-reproduction output.
  - Observed evidence:
    Targeted regression tests:
    ```text
    python3 -m pytest tests/test_finalize_sendback.py tests/test_ipd_authoring.py tests/test_nonsurveyable_root_refusal.py tests/test_explicit_dir_non_project.py tests/test_no_project_exit_is_cannot_run.py
    131 passed in 10.13s
    ```
    Full pytest suite runner output:
    ```text
    python3 -m pytest
    702 passed in 22.84s
    ```
    aw suite runner output:
    ```text
    aw suite
    702 passed in 22.43s
    ```
    Leak reproduction output:
    ```text
    Pre-change: Pytest exit code: 1, Stray plans: [PosixPath('/tmp/tmp0vnsdqvc/scratch_project/.aw/records/plans/pending/20261016-testset-01-gtzne6-e2e-test-plan.ipd.md')]
    Post-change: Pytest exit code: 0, Stray plans in scratch project pending: []
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: pasted `git diff -- CHANGELOG.md` and a `grep -nP "\x{2013}|\x{2014}"` over the added line returning nothing; the entry's claims match what E-04 actually did.
  - Observed evidence:
    `git diff -- CHANGELOG.md`:
    ```diff
    +- Fixed: aw ipd scaffold now accepts --dir and no longer writes a plan into an enclosing project, and project discovery stops at an enclosing git repository that has no agent-workflows install.
    ```
    Dash check:
    ```sh
    git diff -- CHANGELOG.md | grep -E "^\+" | grep -nP "[\x{2013}\x{2014}]"
    (exited 1, no em or en dashes)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`) AND after OQ-01 is answered (it is `Blocking: yes`, so `aw ipd lint` refuses the plan until then). Start a hand execution with `aw ipd begin ivq0nr`.

- Scope fence: `- Scope-Paths:` is a DECLARATION reconciled at finalize; an out-of-scope edit that proves necessary is made and then justified with `--scope-reason`, and a declared path left unmodified (for example `agent_workflows/project_context.py` under OQ-01 answer (b)) is acknowledged with `--scope-ack`.
- Honesty rule (hard MUST): every `V-*` pastes the ACTUAL runner output; a claimed pass without pasted output does not satisfy it. Do not weaken an assertion to make a test pass.
- Commit: only through `aw commit ivq0nr -- <Scope-Paths> <this plan path>` (never `git add -A`, `-a`, or `--no-verify`); verify the staged set with `git diff --cached --name-only` first; never push.
- Lifecycle transition (mandatory; owner conditional): under `aw oc run` / `aw agy run` the runner performs the finalize after its merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize`; in a hand execution the executor runs `aw ipd finalize ivq0nr`. Never hand-`git mv` the plan into `executed/` or hand-edit `- Status:`. Transition only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass` (or `blocked` for E-04/V-04 under OQ-01 answer (b), as E-04 specifies).
- Release gate: inherited `- Blocks-Release: next` from backlog `nj13xp` (`Work-Kind: bug`); keep it. The backlog item reaches `done` through the `- From-Backlog: nj13xp` handoff once this plan executes; do not close it by hand.
