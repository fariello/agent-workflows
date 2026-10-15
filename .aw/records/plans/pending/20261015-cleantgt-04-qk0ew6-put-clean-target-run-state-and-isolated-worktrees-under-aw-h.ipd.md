# IPD: Put clean-target run state and isolated worktrees under AW_HOME

- Date: 2026-10-15
- Kind: child
- Concern: In a clean-delta (`delivery_mode: clean-delta`) repository, per-machine control state and isolated lane worktrees are still composed as `<target>/.aw/...`: `ipd_lifecycle.checkout_control_root` returns `<main>/.aw` (receipts, finalize lock, journals, lane owner records), `worktree_lease.allocate_worktree` creates lanes at `repo_root / WORKTREES_SUBDIR` (`.aw/worktrees/<name>`), and `work_cmd`, `checkup` and `runner_shared.suite_baseline_checkout_path` write `<repo>/.aw/state/...`; measured at HEAD `62803305b` on a scratch clean-target install, every one of those resolved inside the target, so the first `aw ipd begin`, `aw work begin` or `aw oc run` re-creates an (unignored, since clean-delta writes no `.aw/.gitignore`) `.aw/` in the target, defeating the maintainer's zero-delta decision (irjoga OQ-04, resolved 2026-10-15).
- Scope: Make `ipd_lifecycle.checkout_control_root` return `<AW_HOME>/projects/<project_id>` for a clean-delta checkout (from the main tree AND from any linked lane), so every existing caller (receipts, locks, journals, owner records, run-record reads) moves with it; add `worktree_lease.worktrees_root` and `ipd_lifecycle.control_state_dir` accessors and route lane allocation, `lanes_cli`, `oc_runipd`'s sibling-lane scan, `work_cmd`'s lease/evidence dir, `checkup.checkup_dir` and `runner_shared.suite_baseline_checkout_path` through them; make a clean-delta lane self-ignore its in-lane scratch; fix the two display heuristics that assume `.aw/worktrees` (`render_stream._relativize_path`, `runner_shared.lane_worktree_display`) and `ipd_lifecycle.is_main_checkout`, which derives the main tree from the control root; refuse the hardened profile for clean-delta honestly; non-clean-delta modes byte-identical. Outcome tests in a new `tests/test_clean_target_control_state.py`.
- Scope-Paths: agent_workflows/project_context.py, agent_workflows/ipd_lifecycle.py, agent_workflows/worktree_lease.py, agent_workflows/work_cmd.py, agent_workflows/checkup.py, agent_workflows/runner_shared.py, agent_workflows/lanes_cli.py, agent_workflows/oc_runipd.py, agent_workflows/render_stream.py, agent_workflows/runner_stop.py, tests/test_clean_target_control_state.py
- Item-Dependencies: executed:fnnwj3
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: kvwwt0
- Blocks-Release: next
- Set: cleantgt
- Order: 4
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: qk0ew6

## Workflow history
- 2026-10-15 to-review (aw set): authored review-ready child of Set cleantgt (orchestrator ucr3h8) from backlog kvwwt0

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

For a clean-delta repository, put every per-machine control file (begin receipts, finalize lock and journals, lane owner records, `aw work` leases and evidence, checkup record, suite baselines) under `<AW_HOME>/projects/<project_id>/state/` and every isolated lane worktree under `<AW_HOME>/projects/<project_id>/worktrees/<name>/`, resolved identically from the main checkout and from inside a lane, so that ordinary runner and lifecycle use leaves `git -C <target> status --porcelain --ignored` empty, while every non-clean-delta repository keeps its exact current paths (plan `wmuu4k` stands for them).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure and the control-root decision

- [ ] E-01 Re-measure at execution HEAD (after `fnnwj3` landed): the bodies and callers of `ipd_lifecycle.checkout_control_root` (`grep -n "checkout_control_root(" agent_workflows/*.py`), `ipd_lifecycle.is_main_checkout`, `_runtime_dir`, `receipt_dir`, `_run_record_committed_paths`, `worktree_lease.WORKTREES_SUBDIR`/`OWNERS_SUBDIR` and their users (`grep -n "WORKTREES_SUBDIR\|OWNERS_SUBDIR\|\.aw/worktrees\|\"\.aw\" / \"worktrees\"" agent_workflows/*.py`), `worktree_lease.allocate_worktree`, `_owner_record_path`, `lanes_cli` `wt_base`, `oc_runipd._apply_execution_profile`, `work_cmd._WORK_STATE_SUBDIR`, `checkup.CHECKUP_STATE_REL`, `runner_shared.SUITE_BASELINE_SUBDIR`, `runner_shared.state_root`, `runner_shared.lane_worktree_display`, `render_stream._relativize_path`/`note_modified_file`, `attention._resolve_runs_repo_root`, `check_engine`'s scope-drift `.aw/state/`/`.aw/worktrees/` exclusion, and `ipd_set_plan.node_to_lane_request`'s `.aw/worktrees/{0}` label; and re-run the F-01 scratch probe (clean-target install with temp `HOME`/`AW_HOME`/`XDG_CONFIG_HOME`, in-target residue removed, linked worktree under `<AW_HOME>/projects/<id>/worktrees/abc123`) printing every path accessor from the root and from the lane.
  - Depends on: none
  - Expected outcome: the baseline path table (root and lane x control root, receipt dir, finalize lock, owner record, work dir, checkup dir, suite-baseline path, `state_root`, `runs_repo_root`) is pasted into V-01 and matches F-01, with `fnnwj3`'s identity fix visible (`state_root(<lane>)` now the main project's), or drift is recorded and the E-items adjusted before editing.
  - Execution state: pending

- [ ] E-02 Add pure `project_context.clean_delta_project_dir(main_root, aw_home=None) -> Optional[Path]`: when `home_configured_root(main_root)` (added by `fnnwj3`) holds, return `project_config_dir(main_root, aw_home).parent` (that is `<AW_HOME>/projects/<project_id>`, the directory whose `config/project.json` was just read, so identity cannot diverge from the stored config), else `None`. No write, no subprocess. Then change `ipd_lifecycle.checkout_control_root` so that, after it resolves the main worktree from the common dir (the existing "common dir named `.git` -> its parent" branch), it returns `clean_delta_project_dir(main)` when that is set and `<main>/.aw` otherwise; the non-git and bare fallbacks (`start/.aw`) are unchanged, the function stays TOTAL (an `OSError` or `ValueError` from the new lookup falls back to `<main>/.aw` and is NOT cached), and the positive memo stays. Rewrite its docstring: the control root is the `.aw`-equivalent root of the checkout, which is `<main>/.aw` for every mode except clean-delta, where it is the project's home dir (cite irjoga OQ-04 and this plan).
  - Depends on: E-01
  - Expected outcome: for the clean-delta fixture, `checkout_control_root(<root>)` and `checkout_control_root(<lane>)` both equal `<AW_HOME>/projects/<id>`, and `checkout_control_root(<root>) / "state"` equals `Path(resolve_project_context(target_repo=<root>).logical_roots["state"])`; `receipt_dir`, `finalize_lock_path`, `finalize_journal_path`, `commit_lock`'s runtime dir and `worktree_lease._owner_record_path` therefore resolve under `<AW_HOME>/projects/<id>/{state,worktrees/.owners}` with no caller edit, and `_run_record_committed_paths`'s `checkout_control_root(...) / "records" / "runs"` equals `runner_shared.state_root(<root>)`; for a tracked in-repo install, a non-git dir and a bare repo every value equals the E-01 baseline (asserted in E-08).
  - Execution state: pending

- [ ] E-03 Fix `ipd_lifecycle.is_main_checkout`, which today compares `checkout_control_root(repo_root).parent` to `git rev-parse --show-toplevel` and would silently return False everywhere once E-02 makes the clean-delta control root live under `AW_HOME`: derive the main worktree from `checkout_git_common_dir(repo_root)` (common dir named `.git` -> its parent, the same rule) and compare that, keeping the any-error-returns-False contract. Update its docstring's "Preferred:" sentence accordingly.
  - Depends on: E-02
  - Expected outcome: `is_main_checkout(<main>)` is True and `is_main_checkout(<lane>)` is False for both a tracked and a clean-delta checkout, so `maybe_print_lane_nudge`'s advisory still fires from the main checkout of a clean-delta repo (asserted in E-08).
  - Execution state: pending

### Task group 2: Worktrees root and the remaining in-target state writers

- [ ] E-04 Add `worktree_lease.worktrees_root(repo_root) -> Path`: when the checkout is clean-delta, `ipd_lifecycle.checkout_control_root(repo_root) / "worktrees"` (so `<AW_HOME>/projects/<id>/worktrees`, the parent of the owner records `_owner_record_path` already derives from the control root), else exactly `repo_root / WORKTREES_SUBDIR` as today. The import stays FUNCTION-LOCAL and the fallback TOTAL (any exception returns `repo_root / WORKTREES_SUBDIR`), preserving the module's stdlib-only contract pinned by `tests/test_worktree_lease_stdlib_only.py`. Route `allocate_worktree`'s `wt_path` through it, `lanes_cli`'s `wt_base = repo / ".aw" / "worktrees"` scan and its `repo / ".aw" / "worktrees" / lane_id` fallback handle path, and `oc_runipd._apply_execution_profile`'s `(repo_root / WORKTREES_SUBDIR).glob("*")` sibling-lane scan. Update the `WORKTREES_SUBDIR`/`OWNERS_SUBDIR` comments to say the constants are the in-repo layout and the clean-delta root comes from `worktrees_root`.
  - Depends on: E-02
  - Expected outcome: `allocate_worktree(<clean root>, "abc123")` creates the lane at `<AW_HOME>/projects/<id>/worktrees/abc123` with branch `aw/lane/abc123` and its owner record under `<AW_HOME>/projects/<id>/worktrees/.owners/`; `aw lanes list --json` from the main checkout lists it; `teardown_worktree` removes the directory; a tracked repo still allocates at `<repo>/.aw/worktrees/abc123` (asserted in E-08).
  - Execution state: pending

- [ ] E-05 Make a clean-delta lane ignore its own in-lane scratch: right after a successful `git worktree add` in `allocate_worktree`, when the lane was allocated under the clean-delta `worktrees_root`, write `<lane>/.aw/.gitignore` containing exactly `*` (create-if-absent, never overwrite). Rationale (F-05): the runner writes `<lane>/.aw/lane-scratch/`, `<lane>/.aw/state/lane-submissions/` and `<lane>/.aw/state/lane-inputs/` inside the lane, a clean target has no tracked `.aw/.gitignore` to ignore them, per-worktree `info/exclude` is not consulted by git (measured: `git rev-parse --git-path info/exclude` in a linked worktree names the COMMON `.git/info/exclude`) and the maintainer ruled out `.git/info/exclude`; without this, `snapshot_lane_dirty_work` (which stages every path `git status --porcelain` reports) would commit runner scratch into the lane branch and the integration would carry it into the target. The file lives in the lane (outside the target working tree) and ignores itself.
  - Depends on: E-04
  - Expected outcome: in a fresh clean-delta lane, after creating `<lane>/.aw/state/x` and `<lane>/.aw/lane-scratch/y`, `git -C <lane> status --porcelain` is empty, `snapshot_lane_dirty_work` returns `None` (nothing to snapshot), and a tracked-mode lane gets no such file (asserted in E-08).
  - Execution state: pending

- [ ] E-06 Add `ipd_lifecycle.control_state_dir(repo_root, *parts) -> Path`: `checkout_control_root(repo_root) / "state" / parts` for a clean-delta checkout, else exactly `repo_root / ".aw" / "state" / parts` (today's composition, byte-identical, deliberately NOT collapsed to the main checkout for tracked lanes). Route `work_cmd._work_dir` (`_WORK_STATE_SUBDIR` = `.aw/state/work`), `checkup.checkup_dir` (`runs_repo_root(...) / CHECKUP_STATE_REL`) and `runner_shared.suite_baseline_checkout_path` (`repo_root / SUITE_BASELINE_SUBDIR`) through it, keeping each constant for the in-repo layout and its docstring accurate.
  - Depends on: E-02
  - Expected outcome: for the clean-delta fixture the `aw work` lease/evidence dir, `checkup_record_path` and the suite-baseline path all resolve under `<AW_HOME>/projects/<id>/state/{work,checkup,suite-baselines}` from the root and from the lane; for a tracked repo they equal the E-01 baseline (asserted in E-08).
  - Execution state: pending

### Task group 3: Heuristics, hardened profile, docstrings

- [ ] E-07 Fix the path heuristics that assume `.aw/worktrees`, and close the remaining surface. (1) `render_stream._relativize_path`: when the path is ABSOLUTE and lies under `work_dir` but not under `repo_root` (an external lane), relativize it against `work_dir`, appended AFTER the existing `repo_root` attempt so in-repo lanes keep their `.aw/worktrees/<lane>/...` rendering; otherwise an external lane's edits render as absolute `AW_HOME` paths, which `aw sanitize --agent` flags and which `note_modified_file` cannot strip. (2) `runner_shared.lane_worktree_display`: its outside-the-repository branch reconstructs `.aw/worktrees/<name>` whenever the parent dir is named `worktrees`, which for an external lane names a path that does NOT exist in the repository; return `None` (omit, as its docstring's leak rule prescribes) when the worktree lies under the clean-delta `worktrees_root`. (3) `oc_runipd._apply_execution_profile`: when the hardened profile is selected for a clean-delta checkout, raise `SandboxProfileError` with a message naming the gap (the sandbox plan grants no read access to `<AW_HOME>/projects/<id>/{config,system,records}`, so the jailed inner `aw` could not resolve its project); see OQ-02. (4) Rewrite `runner_stop`'s module note ("relocating the driver run root OUT of the repository is NOT IMPLEMENTED") to state the clean-delta exception. `attention._resolve_runs_repo_root`'s `".aw/worktrees" in str(...)` fallback, `check_engine`'s scope-drift exclusion, `ipd_set_plan.node_to_lane_request`'s label and `lane_containment`'s `WORKTREES_SUBDIR` refusal need no change (F-06); E-08 proves the first by test.
  - Depends on: E-04
  - Expected outcome: `_relativize_path("<external lane>/src/x.py", repo_root=<root>, work_dir=<external lane>)` returns `src/x.py`, an in-repo lane path still returns `.aw/worktrees/<lane>/src/x.py`; `lane_worktree_display(<root>, <external lane>)` is `None` and for an in-repo lane unchanged; `--execution-profile hardened` on a clean-delta repo exits with the named refusal while the default profile is unaffected (asserted in E-08).
  - Execution state: pending

### Task group 4: Outcome tests and suite

- [ ] E-08 Create `tests/test_clean_target_control_state.py` (P16: drive functions and subprocesses, never read source; `setUp` calls `ipd_lifecycle.clear_checkout_control_root_cache()`; temp `HOME`/`AW_HOME`/`XDG_CONFIG_HOME`, `AW_NO_REEXEC=1`). Fixture: `aw install --preset completely-clean-target -y --no-interactive` (and `local-only` for the path table) into a temp git repo, remove in-target residue (simulating Order 05, so this plan does not depend on it) and commit nothing; a tracked `private-target` fixture as the control. Cases: (a) E-02 path table from the root and from an external lane, including `control / "state" == logical_roots["state"]` and run-record root == `state_root`; (b) E-03 `is_main_checkout`; (c) E-04 `allocate_worktree` location, owner record location, subprocess `aw lanes list --json` listing it, teardown; (d) E-05 lane self-ignore and `snapshot_lane_dirty_work` returning `None`; (e) E-06 paths; (f) E-07 heuristics and the hardened refusal; (g) INNER-AW FROM AN EXTERNAL LANE: with cwd = the lane, subprocess `aw context --agent` reports the main project's `project_id`, a `python3 -c` subprocess prints `receipt_dir(Path.cwd())`, `finalize_lock_path(Path.cwd())`, `runner_shared.state_root(None)` and `runs_repo_root(Path.cwd())` equal to the values computed from the main root, and `attention._resolve_runs_repo_root(<lane>)` returns the main root; (h) THE ACCEPTANCE BAR: after (c)..(g) have written receipts/leases/owner records and created and torn down a lane, `git -C <target> status --porcelain --ignored` is empty and `git -C <target> rev-parse HEAD` is unchanged; (i) tracked control: the same operations on the tracked fixture produce exactly the E-01 baseline paths.
  - Depends on: E-03, E-05, E-06, E-07
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_clean_target_control_state.py -v` passes; mutating `checkout_control_root` to ignore `clean_delta_project_dir` fails (a), (g) and (h), and mutating `worktrees_root` to always return `repo_root / WORKTREES_SUBDIR` fails (c) and (h); both pass again after restore.
  - Execution state: pending

- [ ] E-09 Run the neighbouring suites and the bare full suite: `python3 -m pytest -o addopts="" tests/test_clean_target_control_state.py tests/test_clean_target_recognition.py tests/test_worktree_lease.py tests/test_worktree_lease_stdlib_only.py tests/test_lane_owner_record_anchoring.py tests/test_lane_landing_anchor.py tests/test_finalize_refusal_findings.py tests/test_lanes_prune.py tests/test_checkup.py tests/test_suite_baseline_direction.py tests/test_runs_repo_alias.py tests/test_orchestrator_retirement.py`, then bare `python3 -m pytest`.
  - Depends on: E-08
  - Expected outcome: the narrowed run passes; the bare suite shows no failure that does not also fail on the base commit (any such failure reproduced on the base and pasted).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- ONE control root per checkout (backlog `dh0uno`): control state is resolved through `ipd_lifecycle.checkout_control_root` so a lane and the main tree share it; its docstring warns that composing `repo_root/".aw"/...` per caller forked a second store "the driver ... could not see and lane teardown then deleted". E-02 changes the one accessor rather than the callers, and E-04/E-06 add accessors rather than literals.
- `checkout_control_root` must stay TOTAL and is memoized (its docstring: "Only `OSError` is caught ... a raise here would surface in places that cannot handle it"; tests must call `clear_checkout_control_root_cache()` in `setUp`).
- `worktree_lease` imports no first-party module at module level (pinned by `tests/test_worktree_lease_stdlib_only.py`; `_owner_record_path` docstring: "THE IMPORT IS FUNCTION-LOCAL ... THE FALLBACK IS TOTAL").
- `project_context.py` is PURE (module docstring "ZERO filesystem writes"); E-02's helper only reads.
- Every routing decision reads the STORED policy via `fnnwj3`'s `home_configured_root` (stored `delivery_mode == "clean-delta"`), never a preset name (irjoga PR-003/PR-004).
- Suite: bare `python3 -m pytest`; narrowed verbose runs use `-o addopts=""`. Tests assert outcomes (P16).

## Findings

Measured at HEAD `62803305b`: scratch `aw install <tmp>/r --preset completely-clean-target -y --no-interactive` with temp `HOME`, `AW_HOME=<tmp>/h/.aw`, `XDG_CONFIG_HOME`; then `rm -rf <tmp>/r/.aw`; then `git -C <tmp>/r worktree add --detach <tmp>/h/.aw/projects/r-5f5872/worktrees/abc123`; paths below are relative to `<tmp>`.

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | `ipd_lifecycle.checkout_control_root` and its consumers | From the root AND from the external lane: control `/r/.aw`, receipts `/r/.aw/state/ipd-lifecycle`, finalize lock `/r/.aw/state/runtime/locks/ipd_finalize_writer.lock`, owner record `/r/.aw/worktrees/.owners/x1y2z3.json`, checkup `/r/.aw/state/checkup`, suite baseline `/r/.aw/state/suite-baselines/x1y2z3-attempt1`, `work_cmd._work_dir(<root>)` `/r/.aw/state/work/x1y2z3`. All inside the target. Consumers of the control root: `_runtime_dir` (locks, journals; also `commit_lock._runtime_dir` via `finalize_lock_path`), `receipt_dir`, `_run_record_committed_paths` (`/ "records" / "runs"`), `worktree_lease._owner_record_path` (`/ "worktrees/.owners"`), and `is_main_checkout` (`.parent`). Because each composes a `.aw`-relative tail onto the control root, returning `<AW_HOME>/projects/<id>` (whose children are `config/`, `state/`, `records/`, and with this plan `worktrees/`) moves all of them coherently. |
| F-02 | High | `runner_shared.state_root` | Already outside the target for clean-delta: root -> `/h/.aw/projects/r-5f5872/records/runs` (it derives from `resolve_project_context(...).logical_roots["records"]`). From the lane it returned `/h/.aw/projects/abc123-7087a4/records/runs`, a different project, which is `fnnwj3`'s F-03 and is fixed by that dependency, not here. `runs_repo_root(<lane>)` already returns `/r` via `attention._resolve_runs_repo_root`'s gitfile branch. So `state_root` needs no code change; E-08 (g) proves lane and root agree. |
| F-03 | High | `worktree_lease.allocate_worktree` | `wt_path = (repo_root / WORKTREES_SUBDIR / name).resolve()` with `WORKTREES_SUBDIR = ".aw/worktrees"`, so every lane of a clean-delta repo is created INSIDE the target. Callers: `runner_shared.allocate_isolation_worktree` (execute items), the review-sweep lane allocator (`review_sweep_lane_id`), `oc_runipd` audit lanes, and `work_cmd.run_work_begin`; all pass the main repo, so routing the one composition fixes them all. |
| F-04 | High | `ipd_lifecycle.is_main_checkout` | Computes `main_root = checkout_control_root(root_path).parent` and compares to `--show-toplevel`. Under E-02 the clean-delta control root's parent is `<AW_HOME>/projects`, so it would return False from the real main checkout and silently disable the lifecycle lane nudge (`maybe_print_lane_nudge`). Hence E-03. |
| F-05 | High | in-lane scratch with no `.aw/.gitignore` | Measured in a scratch linked worktree: with `<lane>/.aw/state/x` present, `git status --porcelain` shows `?? .aw/`; writing `/.aw/` into the per-worktree admin `info/exclude` did NOT help (git reads the common `.git/info/exclude`, as `git rev-parse --git-path info/exclude` confirms); writing `<lane>/.aw/.gitignore` = `*` made `git status --porcelain` empty and `git add -- .aw/state/x` refused ("paths are ignored"). The runner writes `<lane>/.aw/lane-scratch/` (`oc_runipd.LANE_SCRATCH_SUBDIR`), `<lane>/.aw/state/lane-submissions/` (`lane_containment.LANE_SUBMISSION_SUBDIR`) and `<lane>/.aw/state/lane-inputs/` (`LANE_INPUT_SUBDIR`); `worktree_lease.snapshot_lane_dirty_work` stages every porcelain path. In tracked mode the tracked `.aw/.gitignore` covers `/state/`; in clean-delta nothing does. Hence E-05. |
| F-06 | Medium | `.aw/worktrees` heuristics | `grep -n "\.aw/worktrees" agent_workflows/*.py`: `render_stream.note_modified_file` strips a `.aw/worktrees/<lane>/` prefix and `_relativize_path` relativizes absolute paths against `repo_root` then cwd only, so an external lane's absolute edit path stays absolute (E-07 (1)); `runner_shared.lane_worktree_display` reconstructs `.aw/worktrees/<name>` for any outside-repo path whose parent is named `worktrees`, which is FALSE for `<AW_HOME>/projects/<id>/worktrees/<name>` (E-07 (2)); `attention._resolve_runs_repo_root` tries the lane's `.git` gitfile first (works for external lanes, measured `runs_repo_root(<lane>) = /r`) and only then the substring fallback, so no change; `check_engine`'s scope-drift exclusion filters CHANGED paths of the lane checkout, where clean-delta now has nothing under `.aw/` that git reports (E-05), so no change; `ipd_set_plan.node_to_lane_request`'s `".aw/worktrees/{0}"` is a logical uniqueness label consumed by `orchestrate_isolation` (`share worktree` check), never a filesystem path, so no change; `lane_containment`'s `WORKTREES_SUBDIR` refusal judges a repo-relative requested path and stays correct. |
| F-07 | Medium | hardened execution profile | `oc_runipd._apply_execution_profile` builds a sandbox plan whose writable set is the lane and lane scratch, read-only set is toolchains and the git common dir, and inaccessible set includes `control_root` (= `state_root`) and the main worktree. Nothing grants read access to `<AW_HOME>/projects/<id>/{config,system,records}`, which a clean-delta inner `aw` needs to recognize its project (`fnnwj3`) and read its plan. Making that work is a sandbox-design change; failing closed is honest (E-07 (3), OQ-02). |
| F-08 | Low | other in-target state writers | Install/upgrade/migration paths also compose `<repo>/.aw/state` (`engine` install-state migration and uninstall, `config` install history fallback, `install_history` fallback, `compat_migration.CompatRollback.runtime_dir`, `compat_migration.DeprecationCounter.COUNTER_RELPATH`, `layout_migration`, `storage`). They run under `aw install`/`aw upgrade`/`aw migrate-layout`, which the install child owns; `install_history` already routes through `physical_classes`. |

## Proposed changes (ordered, validatable)

1. `project_context.clean_delta_project_dir` + `ipd_lifecycle.checkout_control_root` clean-delta branch (E-02): one accessor change moves receipts, locks, journals, owner records and the run-record read.
2. `ipd_lifecycle.is_main_checkout` derives the main tree from the common dir (E-03).
3. `worktree_lease.worktrees_root` used by `allocate_worktree`, `lanes_cli` and `oc_runipd`'s sibling scan (E-04); clean-delta lanes self-ignore their `.aw/` (E-05).
4. `ipd_lifecycle.control_state_dir` used by `work_cmd`, `checkup`, `runner_shared.suite_baseline_checkout_path` (E-06).
5. Heuristic fixes in `render_stream` and `runner_shared.lane_worktree_display`, hardened refusal, `runner_stop` note (E-07).
6. `tests/test_clean_target_control_state.py` (E-08), suite runs (E-09).

## Deferred / out of scope (with reason)

- Suppressing install/upgrade-time target writes (`engine` install-state migration, `.aw/.gitignore` back-fill of `/worktrees/`, `compat_migration` runtime and deprecation counter, `layout_migration`, `storage`): install side of the Set.
  - Carrier: 3m8aix
- Removing `<AW_HOME>/projects/<id>/state/` and `worktrees/` on uninstall (and refusing or tearing down live lanes first).
  - Carrier: xoy5yg
- The end-to-end zero-delta proof through `aw work begin`, `aw ipd begin` on a real approved plan and `aw oc run --prepare-only`, and the spec `20260810-1447-01` Section 5 amendment that names clean-delta as the `wmuu4k` exception: E-08 proves the accessors and the bar for the operations this plan owns, while a real plan in home records needs Orders 01..05.
  - Carrier: nwporz
- Hardened execution profile for clean-delta (granting the jailed inner `aw` read access to the project's home `config/`, `system/`, `records/`): this plan refuses it explicitly (E-07 (3)); building it is a sandbox-profile design change with no child in this Set, so it stays owned by the source backlog item until the maintainer answers OQ-02 and a backlog item is filed for it. See OQ-02.
  - Carrier: kvwwt0
- Runtime `.aw/workflow-artifacts/<workflow>/<run-id>/` written by workflow prose (spec Section 5 lists it as per-machine control state): no code accessor exists to route; Order 07 records it in the Section 5 amendment as either routed or a documented residual. See OQ-03.
  - Carrier: nwporz

## Scope check

- Over-scope: none. Every item moves a clean-delta control-state or worktree path out of the target, or repairs a consumer the move would otherwise break (E-03, E-07).
- Under-scope: the brief names `checkout_control_root`, `state_root`, `worktree_lease`, `lanes_cli wt_base`, runner_shared worktree path code, and the `render_stream`/`attention` heuristics; all are covered (E-02, F-02, E-04, E-07). Measurement added three in-target state writers the brief did not name (`work_cmd`, `checkup`, suite baselines; E-06), the lane scratch leak (E-05), `is_main_checkout` (E-03) and the hardened gap (E-07 (3)). Install-time writers are carried by `3m8aix` (F-08).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_clean_target_control_state.py -v` (E-08) with both mutation proofs.
- The narrowed neighbour run in E-09, then bare `python3 -m pytest` (paste the summary line).
- The E-01 scratch probe re-run after E-07, showing every path under `<AW_HOME>/projects/<id>/` for clean-delta and unchanged for tracked.

## Spec / documentation sync

- Spec `20260810-1447-01` Section 5 ("Per-machine control state ... stays IN the target repository ... relocation out of the repo (retired `58ha43`) is not pursued") becomes false for clean-delta once this plan lands. The brief assigns the Set's single Section 4/5 amendment, its `aw specs note`, and the CHANGELOG `- Fixed:` entry to Order 07 `nwporz`, which runs after this plan within the same Set and release gate, so the spec and code converge before `next` ships; this plan therefore edits no `.spec.md` and lists none in `- Scope-Paths:`. The behavior decision itself is already recorded (irjoga OQ-04, maintainer, 2026-10-15).
- Docstrings updated in place: `checkout_control_root`, `is_main_checkout`, `WORKTREES_SUBDIR`/`OWNERS_SUBDIR` comments, `_owner_record_path`, `suite_baseline_checkout_path`, `checkup_dir`, `lane_worktree_display`, `runner_stop` module note.

## Open questions

### OQ-01: Should driver run records move from `<AW_HOME>/projects/<id>/records/runs/` to `<AW_HOME>/projects/<id>/state/`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence: keep them at the records root's `runs/`. The maintainer's criterion (irjoga OQ-04) is that the TARGET working tree contains nothing; `<AW_HOME>/projects/<id>/records/runs` already satisfies it (F-02, measured). The layout contract places runs under `records/runs/` in every mode (the `.aw/.gitignore` template's `records/runs/` line), `runner_shared.state_root`, `run_viewer.discover_run_dirs` and `ipd_lifecycle._run_record_committed_paths` all read them there, and under E-02 `checkout_control_root(...) / "records" / "runs"` equals `state_root` for clean-delta. Moving them would split the run corpus by mode for no zero-delta gain. Order 06 `xoy5yg` decides whether uninstall without `--deep` keeps them with the records.

### OQ-02: What should the hardened execution profile do for a clean-delta repository?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: kvwwt0
- Resolution or deferral rationale: This plan makes it REFUSE with a named reason (E-07 (3)), because F-07 shows the sandbox plan gives the jailed inner `aw` no read access to the project's home config, system or records, so a "working" hardened run would silently resolve no project. Supporting it means extending `host_sandbox_profile.build_sandbox_plan` with a read-only project-home class and deciding whether `state/` is reachable; that is a security-boundary decision for the maintainer. Default-profile runs are unaffected. Not blocking: the refusal is safe and truthful in the meantime.

### OQ-03: Who routes runtime `.aw/workflow-artifacts/` for clean-delta?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: nwporz
- Resolution or deferral rationale: Spec `20260810-1447-01` Section 5 lists `.aw/workflow-artifacts/` as per-machine control state, but its runtime writers are agents following workflow prose (`release-review` and others write `.aw/workflow-artifacts/<workflow>/<run-id>/`), not a code accessor this plan can redirect; the install-time README is `3m8aix`'s. Order 07's ordinary-use proof list in the brief does not exercise a workflow run. Order 07 `nwporz`, which owns the Section 5 amendment, must either route it (for example a resolver verb such as `aw context --class workflow-artifacts` plus prose rewiring, which would need its own child) or record it as a documented residual; it is NOT parked on the orchestrator. Not blocking this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the execution-HEAD sha, the grep outputs named in E-01, and the baseline path table from root and lane (paths relative to the temp dir), showing `state_root(<lane>)` now equal to the root's after `fnnwj3`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the `project_context.py` and `checkout_control_root` diff hunks (code and docstring) and the passing pytest lines for E-08 (a) and the tracked control (i).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the `is_main_checkout` diff and the passing pytest lines for E-08 (b) (main True, lane False, tracked and clean-delta).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the `worktree_lease.py`, `lanes_cli.py` and `oc_runipd.py` diff hunks, the passing pytest lines for E-08 (c), and the actual `aw lanes list --json` lane entry (reached via `lanes_cli` list -> `worktree_lease.enumerate_lane_candidates`) with home paths relative to the temp dir; plus `python3 -m pytest -o addopts="" tests/test_worktree_lease_stdlib_only.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the `allocate_worktree` hunk writing `<lane>/.aw/.gitignore`, and the passing pytest lines for E-08 (d) showing empty lane `git status --porcelain` with scratch present and `snapshot_lane_dirty_work` returning `None`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE the `control_state_dir` hunk and the `work_cmd.py`, `checkup.py`, `runner_shared.py` hunks, and the passing pytest lines for E-08 (e) and (i).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: PASTE the `render_stream.py`, `lane_worktree_display`, `_apply_execution_profile` and `runner_stop.py` hunks, the passing pytest lines for E-08 (f), and the actual refusal text printed for the hardened profile on a clean-delta repo (reached via `oc_runipd._apply_execution_profile`, exercised in-process by E-08 (f)).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: PASTE `python3 -m pytest -o addopts="" tests/test_clean_target_control_state.py -v` passing; the run FAILING under each of the two mutations (name the failing cases, which must include (g) and (h)) and passing after restore; and the literal empty output of `git -C <target> status --porcelain --ignored` with the unchanged HEAD sha captured by case (h).
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: PASTE the narrowed neighbour run summary and the bare `python3 -m pytest` summary line; for any failure, paste the same test failing on the base commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern, where clean-delta control state and lanes live. The control-root move (E-02), the consumers it would break (E-03, E-07) and the sibling accessors (E-04..E-06) must land together: moving only some leaves the driver and an inner `aw` reading different stores, the exact fork `dh0uno` exists to prevent.

EXECUTION CONTRACT. Execute only after explicit human approval and after `fnnwj3` is executed (`- Item-Dependencies:`; the runner re-checks at dispatch). OQ-02 (carried by `kvwwt0`) and OQ-03 (carried by `nwporz`) are open but NOT blocking. Start a hand execution in an isolated worktree with `aw work begin qk0ew6` (or `aw ipd begin qk0ew6` inside the lane). Commit ONLY files changed for this plan through `aw commit qk0ew6 -- <paths>`; never `git add -A`/`-a`, never `--no-verify`, never push; verify the staged set with `git diff --cached --name-only` first (shared checkout). HONESTY RULE (hard MUST): every `V-*` pastes ACTUAL output; run the suite BARE as `python3 -m pytest`. Every scratch install, lane and `aw` subprocess runs with `AW_NO_REEXEC=1` and temp `HOME`, `XDG_CONFIG_HOME`, `AW_HOME`; never touch the operator's real `AW_HOME` or this checkout's own `.aw/worktrees/`. SCOPE FENCE: `- Scope-Paths:` is a declaration reconciled at finalize; a necessary out-of-scope edit is made and justified with `--scope-reason`, a declared path left unmodified is acknowledged with `--scope-ack`. Non-clean-delta paths must stay byte-identical (E-08 (i)).

POST-GATE LIFECYCLE. Under `aw oc run` / `aw agy run` the runner finalizes after its merge-and-revalidate gate, so the executor does not. In a hand execution, fill every `V-*`, confirm `aw ipd lint --phase pre-transition` conforms, then `aw ipd finalize qk0ew6`; never hand-`git mv` the plan. This plan inherits `- Blocks-Release: next` from `kvwwt0`.
