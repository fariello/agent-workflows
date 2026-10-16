# IPD: Recognize a clean-target project with no in-repo .aw, including from an external worktree

- Date: 2026-10-15
- Kind: child
- Concern: Once Set `cleantgt` stops writing `<target>/.aw/`, every project-recognition predicate (`project_context._is_project_marker`, `find_project_root`, `is_project_dir`, `classify_project_dir`, `doctor.probe_environment`, `cli._collect_repo_status_details`, `cli._run_status`'s cwd fallback) answers "not a project" for an installed clean-target repository, and a lane worktree created OUTSIDE the target (Order 04 puts it under `AW_HOME/projects/<project_id>/worktrees/<id6>/`) resolves to the WRONG project: measured at HEAD `62803305b`, `find_project_root(<lane>)` is `None` (or `$HOME` when `~/.aw/config/` exists) and `resolve_project_context(target_repo=<lane>)` returns a fresh derived `project_id` with `delivery_mode: tracked`.
- Scope: Add one pure resolver `project_context.checkout_main_root(path)` (the main worktree of `path`'s git checkout, read from the `.git` gitfile and the `commondir` file without spawning git) and make it the IDENTITY ANCHOR for a linked worktree in `project_config_dir` and in `resolve_project_context`'s derived-`project_id` fallback, so a lane shares its main checkout's home config and `project_id`; add one pure predicate `project_context.home_configured_root(path)` (true iff `project_config_dir(path)` is a home `config/project.json` whose stored `delivery_mode` is `clean-delta`); teach `find_project_root`, `is_project_dir`, `classify_project_dir`, `doctor.probe_environment`, `cli._collect_repo_status_details` and `cli._run_status` to accept it as a project marker. The lane stays its OWN working-tree root (so `aw commit` in a lane commits in the lane, as for in-repo lanes today); only its identity is shared. Outcome tests in a new `tests/test_clean_target_recognition.py`.
- Scope-Paths: agent_workflows/project_context.py, agent_workflows/doctor.py, agent_workflows/cli.py, tests/test_clean_target_recognition.py
- Item-Dependencies: executed:4gn1ka, executed:ivq0nr
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: kvwwt0
- Blocks-Release: next
- Set: cleantgt
- Order: 3
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: fnnwj3

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: fnnwj3 verified (set cleantgt, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review: revisions applied (PR-001..PR-006)
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-15 to-review (aw set): authored review-ready child of Set cleantgt (orchestrator ucr3h8) from backlog kvwwt0

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every project-recognition predicate answer "this is an AW project, rooted HERE" for an installed clean-target (`delivery_mode: clean-delta`) repository that has NO `<target>/.aw/`, from the repository root, from any subdirectory of it, and from a linked lane worktree of it wherever that worktree lives (inside the repo or under `AW_HOME/projects/<project_id>/worktrees/`), while leaving every non-clean-delta repository's answer byte-identical and never creating a project in an unrelated cwd.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure and pure primitives

- [x] E-01 Re-measure at execution HEAD (after `4gn1ka` and `ivq0nr` landed): the bodies of `project_context.find_project_root`, `_is_project_marker`, `is_project_dir`, `classify_project_dir`, `project_config_dir`, `resolve_verb_repo_root`, `doctor.probe_environment` (the `has_aw = (repo_root / ".aw").is_dir()` line), `cli._collect_repo_status_details` (`has_aw = (repo / ".aw").is_dir()`), and `cli._run_status` (the `(cwd / ".aw").is_dir()` fallback), the git-boundary rule `ivq0nr` E-04 added (or its `blocked` record), and the scratch reproduction in this plan's Findings F-01..F-03 (install `--preset completely-clean-target` into a temp repo with temp `HOME`/`AW_HOME`/`XDG_CONFIG_HOME`, remove `<repo>/.aw` and the other in-target residue from the index and HEAD (`git rm -r --cached .`, commit, `git clean -fdx`; deleting only the working-tree copy is NOT enough, because the installer COMMITS `.aw/` (irjoga F-01) and `git worktree add` would check it out again into the lane, which then reads `is_project_dir True` / `abc123-<hash>` tracked, measured at review, PR-002) to simulate the Order 05 end state, add a linked worktree under `AW_HOME/projects/<id>/worktrees/abc123`, then print the five predicates for the root, a subdirectory and the worktree).
  - Depends on: none
  - Expected outcome: the baseline table (root / subdir / external worktree x `is_project_dir`, `find_project_root`, `classify_project_dir`, `project_config_dir`, `resolve_project_context(...).project_id`) is pasted into V-01 and matches F-01..F-03, or any drift is recorded and the plan's E-items are adjusted before editing.
  - Execution state: performed

- [x] E-02 Add pure `project_context.checkout_main_root(path) -> Optional[Path]`: walk up from `path` to the first ancestor holding a `.git` entry; if that entry is a DIRECTORY return that ancestor (a main worktree is its own main root); if it is a FILE whose first line is `gitdir: <dir>`, resolve `<dir>`, read `<dir>/commondir` (relative to `<dir>`) to get the common dir, and return the common dir's parent iff the common dir is named `.git` and `<dir>` sits under `<common>/worktrees/` (a LINKED worktree); return `None` for anything else, including a submodule gitfile (`gitdir: ../.git/modules/<name>`, which has no `commondir` file, measured) and a bare or `--separate-git-dir` layout. No subprocess, no write, total (any `OSError` returns `None`). Docstring states why it is file-based (it is called from `find_project_root`, which is in the per-command hot path and must stay pure and subprocess-free) and that it intentionally agrees with `ipd_lifecycle.checkout_control_root`'s rule "common dir named `.git` -> its parent".
  - Depends on: E-01
  - Expected outcome: for a main worktree, a subdirectory of it, an in-repo linked worktree, and an EXTERNAL linked worktree it returns the main worktree's path; for a submodule checkout, a bare-repo worktree, a non-git dir, and a missing path it returns `None` (asserted in E-06).
  - Execution state: performed

- [x] E-03 Make `checkout_main_root` the identity anchor and add the predicate. (1) In `project_context.project_config_dir`, keep rule 1 (in-tree `<repo>/.aw/config/{project,local,config,policy}.json` wins) byte-identical, and in rule 2 derive the home `project_id` from `checkout_main_root(repo)` instead of `repo` ONLY when `repo / ".git"` exists (that is, `repo` IS a worktree root, main or linked); for any other path keep `repo` as today. WHY (PR-001): `checkout_main_root` walks UP, so applied unconditionally it maps `<root>/sub/deep` to `<root>`, which makes `project_config_dir(<root>/sub/deep)` return the home config, `home_configured_root(<root>/sub/deep)` True, and `find_project_root(<root>/sub/deep)` stop at `sub/deep` itself instead of climbing to the root. That would make every verb run from a subdirectory treat the subdirectory as the project root, and it would change `project_config_dir` for subdirectories of every home-configured repo. Measured at review with a prototype of E-02..E-04: as written, `find_project_root(<root>/sub/deep)` = `<root>/sub/deep` and `find_project_root(<lane>/x)` = `<lane>/x`; with the `.git`-exists guard, both resolve to `<root>` and `<lane>`. (2) In `resolve_project_context`, the derived-id fallback (`project_id = _derive_project_id(repo_abs)`, reached only when neither `local.json` nor `project.json` carries a `project_id`) uses the same guarded anchor. (3) Add `project_context.home_configured_root(path, aw_home=None) -> bool`: True iff `path / ".git"` exists (a worktree root; never a subdirectory, PR-001) AND `project_config_dir(path, aw_home)` is NOT `<path>/.aw/config` AND its `project.json` is a file AND that stored file has `delivery_mode == "clean-delta"` (read via `_read_json_file`; never re-derived from a preset name, honoring irjoga PR-003/PR-004). Docstrings state that the lane keeps its own working-tree root and shares only identity, mirroring `ipd_lifecycle.checkout_control_root`.
  - Depends on: E-02
  - Expected outcome: `project_config_dir(<external lane>)` and `project_config_dir(<main root>)` return the SAME home config dir; `resolve_project_context(target_repo=<external lane>).project_id` equals the main root's (`r-5f5872` in the F-03 fixture, not `abc123-7087a4`) with `delivery_mode == "clean-delta"`; `home_configured_root` is True for the clean root and its lane, False for a `private-target` install, a home `project.json` with `delivery_mode: tracked`, an uninstalled repo, and `$HOME`; `home_configured_root(<root>/sub/deep)` and `home_configured_root(<lane>/x)` are False and `project_config_dir(<root>/sub/deep)` is unchanged from the E-01 baseline (PR-001); a tracked in-repo install's `project_config_dir` and `project_id` are unchanged (asserted in E-06).
  - Execution state: performed

### Task group 2: Wire recognition into the predicates and the two status surfaces

- [x] E-04 Update `project_context.find_project_root` so each climbed directory `curr` is a project root when `_is_project_marker(curr / ".aw")`, the legacy `.agents` marker, OR `home_configured_root(curr)` holds, tested at the SAME point in the loop, and OR the same marker into `is_project_dir`. Preserve exactly the git-boundary rule `ivq0nr` landed (a registered submodule without `.aw` uses its parent's project, any other nested git repo stops at its own boundary, and records are never created in a bare cwd). Because a lane root is now itself recognized, the climb stops there before any boundary or `$HOME` question arises, and `classify_project_dir` needs no logic change since it composes the two predicates. Update the three docstrings to name the home-configured marker and the shared-identity lane rule, citing this plan.
  - Depends on: E-03
  - Expected outcome: for the clean-target fixture: root -> `is_project_dir` True, `find_project_root` = root, classify `is-project-root`; `<root>/sub/deep` -> `find_project_root` = root, classify `inside-project`; external lane -> `is_project_dir` True, `find_project_root(<lane>/x)` = the LANE root (NOT `None`, NOT `$HOME` even when `<AW_HOME>/config/` exists); and for a tracked in-repo install, a non-git `.aw` project, an uninstalled nested git repo, and a submodule, the answers equal the E-01 baseline.
  - Execution state: performed

- [x] E-05 Update `doctor.probe_environment` and `cli._collect_repo_status_details` so `has_aw` is `(repo / ".aw").is_dir() or project_context.home_configured_root(repo)`, and so the reported `layout` for a repo recognized ONLY by the home marker is the new literal `"home (clean-target)"` rather than `".aw"` (a clean-target repo has no `.aw` and claiming one is untrue). Update `cli._run_status`'s cwd fallback (`(cwd / ".git").is_dir() or (cwd / ".aw").is_dir() or (cwd / ".agents").is_dir()`) to also admit `project_context.home_configured_root(cwd)`, which is what lets a lane cwd (whose `.git` is a FILE) be listed. REACHABILITY (PR-003): that fallback runs ONLY when `cli._repos_for_report` returns no repositories (`if not repos:`), i.e. when the user config registers none, so the E-06 (e) lane case must run with a temp `XDG_CONFIG_HOME` whose config lists no repos (delete or empty `repos.installed` after the fixture install, which registers the target), and the root case may come from either the registered list or the fallback; the test names which. `version`, `preset` and `records_backend` keep coming from `engine.read_installed_version` and `project_context.read_project_identity` (both read through `project_config_dir`, so they inherit E-03's anchor; Order 02 `4gn1ka` owns the version read).
  - Depends on: E-04
  - Expected outcome: `aw doctor --dir <clean root> --json` reports `layout: "home (clean-target)"`, `preset: "completely-clean-target"`, `records_backend: "home"`; `aw status --json` from `<clean root>` and from the external lane lists that tree as installed (not `[not installed]`, not omitted); a tracked install still reports `layout: ".aw"`.
  - Execution state: performed

### Task group 3: Outcome tests and suite

- [x] E-06 Create `tests/test_clean_target_recognition.py` exercising the code (P16: no source reading): a fixture that installs `--preset completely-clean-target` and `--preset local-only` into temp git repos via a subprocess (`AW_NO_REEXEC=1`, temp `HOME`/`AW_HOME`/`XDG_CONFIG_HOME`), then removes `<repo>/.aw` and every other in-target residue from the INDEX AND HEAD (`git rm -r --cached .`, commit, `git clean -fdx`), simulating Order 05's end state so this plan does not depend on it, adds a linked worktree under `<AW_HOME>/projects/<id>/worktrees/abc123` with `git worktree add --detach`, and asserts: (a) E-02's `checkout_main_root` table incl. submodule -> `None`; (b) E-03's `home_configured_root` true/false table incl. a home `project.json` with `delivery_mode: tracked` -> False; (b2) E-03's identity table: `project_config_dir` and `resolve_project_context(...).project_id` equal for root and external lane, unchanged for a tracked in-repo install and its in-repo lane; (c) E-04's predicate table for root, subdir (`find_project_root(<root>/sub/deep)` == `<root>`, NOT `sub/deep`), external lane and a subdirectory of the lane (`find_project_root(<lane>/x)` == `<lane>`), including with `<AW_HOME>/config/` present (the `$HOME`-hazard case, measured to return `$HOME` today); (d) negative controls unchanged: tracked in-repo install, non-git `.aw` project, uninstalled git repo under an AW project (per `ivq0nr`'s rule), submodule; (e) subprocess `aw doctor --dir <root> --json` and `aw status --json` (cwd = root and cwd = lane) per E-05; (f) a subprocess `aw attention --format json` with cwd = the external lane exits without the no-project refusal, and `aw context --agent` with cwd = the lane reports the main root's `project_id` (proving `resolve_verb_repo_root` and the resolver follow E-03/E-04). Each test calls `ipd_lifecycle.clear_checkout_control_root_cache()` in `setUp`.
  - Depends on: E-05
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_clean_target_recognition.py -v` passes; a one-line mutation (make `home_configured_root` return False) fails at least the (c) and (e) cases, a second (drop the `checkout_main_root` anchor from `project_config_dir`) fails the (b2) and lane cases of (c), and restoring each passes again.
  - Execution state: performed

- [x] E-07 Run the neighbouring suites and the bare full suite: `python3 -m pytest -o addopts="" tests/test_clean_target_recognition.py tests/test_clean_target_config_home.py tests/test_nonsurveyable_root_refusal.py tests/test_explicit_dir_non_project.py tests/test_explicit_dir_subdir_resolution.py tests/test_project_context.py tests/test_doctor.py tests/test_validator_nonsurveyable_dir.py`, then bare `python3 -m pytest`.
  - Depends on: E-06
  - Expected outcome: the narrowed run passes; the bare suite shows no failure that does not also fail on the base commit (any such failure is reproduced on the base and pasted).
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `project_context.py` is PURE: its module docstring states "PURE: ZERO filesystem writes, directory creation, or Git mutation." E-02 reads `.git`/`commondir` files instead of spawning git, because `find_project_root` runs on every repo-scoped command (`resolve_verb_repo_root`: "87 call sites across 25 modules" per its own docstring) and the existing `_find_git_root` is already file-based for the same reason.
- `resolve_verb_repo_root` never climbs on an explicit `--dir` (decided rule `lmyeas` OQ-01); this plan does not change that. An explicit `--dir <external lane>` is honored verbatim; only `is_project_dir`/`classify_project_dir` decide whether it is surveyable, and they classify a lane as INSIDE its main project so the existing refusal names the main root (`no_project_message`'s "IS an agent-workflows project root ... Run with: aw <verb> --dir <root>").
- Every routing decision reads the STORED policy (`project_config_dir(repo)/project.json`), never a preset name (irjoga PR-003/PR-004, brief). E-03 keys on stored `delivery_mode == "clean-delta"`.
- `ipd_lifecycle.checkout_control_root` is memoized; tests that build fresh checkouts call `clear_checkout_control_root_cache()` in `setUp` (its docstring: "Such tests must call ... in setUp").
- Suite: bare `python3 -m pytest`; narrowed verbose runs use `-o addopts=""` (AGENTS.md repository development contract). Tests assert outcomes (P16): call functions and drive subprocesses, never read source.

## Findings

Measured at HEAD `62803305b` with a scratch `aw install <tmp>/r --preset completely-clean-target -y --no-interactive` (temp `HOME`, `AW_HOME=<tmp>/h/.aw`, `XDG_CONFIG_HOME`), then `rm -rf <tmp>/r/.aw` to simulate the Order 05 end state, then `git -C <tmp>/r worktree add --detach <tmp>/h/.aw/projects/r-5f5872/worktrees/abc123`.

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | `project_context.find_project_root`, `is_project_dir`, `classify_project_dir`, `_is_project_marker` | With no `<repo>/.aw`, all three predicates report NO project for the installed root and its subdirectories: root -> `is_project_dir False find None classify no-project`, `<root>/sub/deep` -> same. They test only `_is_project_marker(curr / ".aw")` / legacy `.agents`, which requires an on-disk `.aw/{system,records,config}`. `project_config_dir(<root>)` already resolves the home config (`<h>/.aw/projects/r-5f5872/config`), so the information exists; no predicate consults it. Today a clean-target install is only recognized by accident, because the installer still writes 356 files into the target (irjoga F-01), which Order 05 removes. |
| F-02 | High | `project_context.find_project_root` from an external worktree | The external lane `<h>/.aw/projects/r-5f5872/worktrees/abc123` reports `is_project_dir False find None classify no-project`; and when `<AW_HOME>/config/` exists (the normal state on a developer machine, `resolve_verb_repo_root` docstring hazard 3: "`is_project_dir(Path.home())` is frequently True because home contains a `.aw/` with durable children (`config` and `projects`)"), `find_project_root(<lane>)` returned `<h>` with classify `inside-project`. So an inner `aw` in an external lane would target `$HOME` as its project. |
| F-03 | High | `project_context.resolve_project_context` / `project_config_dir` keyed on the lane path | `resolve_project_context(target_repo=<lane>)` returned `project_id abc123-7087a4`, `delivery_mode tracked`, records `<h>/.aw/projects/abc123-7087a4/records`, i.e. a DIFFERENT, unconfigured project, because `_derive_project_id` hashes the path and `project_config_dir` looks for `<lane>/.aw/config` or `<AW_HOME>/projects/<hash-of-lane>/config`. The root itself resolves correctly (`r-5f5872 clean-delta`). Hence the lane needs its main checkout's IDENTITY at config lookup (`project_config_dir`), while it must stay its own WORKING-TREE root: `work_cmd.run_commit` and the runner's inner `aw` resolve `repo_root` via `resolve_verb_repo_root` and run git there, so mapping the lane's ROOT to the main checkout would make `aw commit` in a lane commit in the main checkout. In-repo lanes today are their own root (they carry the tracked `.aw/`) while `checkout_control_root` collapses control state to the main checkout; E-03 reproduces that split for external lanes. |
| F-04 | Medium | git layout of a linked worktree vs a submodule | Measured (git 2.43.0): an external linked worktree's `.git` is a file `gitdir: <main>/.git/worktrees/wt1`, and that admin dir contains `commondir` = `../..`; a submodule's `.git` is `gitdir: ../.git/modules/sub` and its admin dir has NO `commondir`. So a file-based reader can distinguish "linked worktree of checkout X" from "submodule" without spawning git, which is exactly the distinction E-02 needs and that `ivq0nr`'s submodule rule depends on. `ipd_lifecycle.checkout_control_root` already maps any worktree to `<common-dir parent>/.aw` (measured `ctrl /r/.aw` from the lane), but via a git subprocess, so it is not reusable inside pure `project_context`. |
| F-05 | Medium | `doctor.probe_environment`, `cli._collect_repo_status_details`, `cli._run_status` | Both reporters set `has_aw = (repo / ".aw").is_dir()` and derive `layout` from it, so a clean-target repo reports `layout "unconfigured"` / `"none"`; `_run_status`'s cwd fallback only admits a cwd with `.git`, `.aw` or `.agents` dirs, so from an external lane (whose `.git` is a FILE) `aw status` lists nothing. `tests/test_doctor.py` pins `layout == ".aw"` for in-repo layouts, which stays true. |
| F-06 | Medium | Coordination with pending `ivq0nr` | `ivq0nr` E-04 rewrites the same `find_project_root` loop to stop at an enclosing `.git` boundary, and the maintainer direction for it is: registered submodule without `.aw` uses the parent, any other nested git repo stops at its boundary, never silently create records in cwd. This plan adds a marker inside the same loop, so the two edits overlap textually and semantically (the lane's `.git` FILE is a boundary under `ivq0nr`'s rule, which is why E-04 maps a linked worktree to its main root BEFORE the climb). Hence `- Item-Dependencies: executed:ivq0nr`: this plan is authored against `ivq0nr`'s rule and re-measures it in E-01. |
| F-07 | Low | Other `.aw`-presence probes | `grep -rn '/ "\.aw")\.\(is_dir\|exists\)()' agent_workflows/*.py` finds 19 sites; besides the three in Scope (doctor, two in cli) the rest are artifact-path walkers (`artifact_core.repo_root_of`, `specs._repo_root_of`, `status_set._repo_root_of`, `record_placement._find_repo_root`, `ipd_lint.lint_file` x6, `orchestrator_readiness.run_coverage`, `check_engine._identity_rename_hint`) that climb from a RECORD FILE to its owning root. In clean-target mode records live under `AW_HOME/projects/<id>/records/`, so those walkers start under the home tree and are Order 01 `kfnfji`'s records-accessor concern, not root recognition from the target; `agy_run.repository_root` uses `git rev-parse --show-toplevel` first; `runner_shared.summarize_graduation_cluster` deliberately does NO parent walk. `cli._run_uninstall`'s footprint probe already ORs in `has_home_cfg` (p425hv). |
| F-09 | High | E-03 anchor applied to subdirectories (plan-review) | Re-measured at review (HEAD `937eb74d1`, fixture with `.aw` removed from HEAD and a linked worktree under `AW_HOME`): root `is_project_dir False find None no-project`, `project_config_dir(<root>)` = home config, `project_id r-<hash> clean-delta`; `<root>/sub/deep` and the lane `no-project` with derived `tracked` ids; with `<AW_HOME>/config/` present, `find_project_root(<lane>)` = `$HOME`, `inside-project` (F-01..F-03 confirmed). A prototype of E-02..E-04 as written returned `find_project_root(<root>/sub/deep)` = `<root>/sub/deep` and `find_project_root(<lane>/x)` = `<lane>/x`, because `checkout_main_root` climbs; with a `.git`-exists guard on both the anchor and `home_configured_root` it returned `<root>` and `<lane>` and `home_configured_root` was False for both subdirectories. |
| F-08 | Medium | identity anchor change and in-repo lanes | E-03 changes `project_config_dir` rule 2 only (rule 1, in-tree config, wins first). A tracked in-repo install's lanes carry the tracked `.aw/config/project.json`, so rule 1 answers for them and nothing changes; a lane of a repo whose config lives ONLY in `AW_HOME` (clean-delta today; any future home-config preset) now shares the main checkout's config instead of resolving an unconfigured hash-of-lane id, which is the correct answer for every such repo. `resolve_project_context` already prefers a stored `project_id` from `local.json` (measured: the home `local.json` carries `"project_id": "r-5f5872"`), so once `project_config_dir` finds the right dir the id follows; the derived-id fallback anchor only matters for a config that omits it. |

## Proposed changes (ordered, validatable)

1. `project_context.checkout_main_root(path)` (E-02): pure, file-based linked-worktree-to-main mapping; `None` for submodule, bare, separate-git-dir, non-git.
2. `project_config_dir` and `resolve_project_context` identity anchor = `checkout_main_root(repo) or repo` applied ONLY when `repo / ".git"` exists (a worktree root; subdirectories keep `repo`, PR-001), plus `project_context.home_configured_root(path, aw_home=None)` (E-03): stored-policy predicate, False for any non-worktree-root path (`delivery_mode == "clean-delta"` read from the home `project.json`).
3. `find_project_root` / `is_project_dir` / `classify_project_dir` (E-04): add the home marker at the existing marker check (a lane root is recognized as itself through E-03's shared identity); keep `ivq0nr`'s boundary rule untouched; docstrings updated.
4. `doctor.probe_environment`, `cli._collect_repo_status_details`, `cli._run_status` (E-05): `has_aw` OR home-configured; `layout "home (clean-target)"`; cwd fallback admits a home-configured cwd (including a lane).
5. `tests/test_clean_target_recognition.py` (E-06) and suite runs (E-07).

## Deferred / out of scope (with reason)

- Routing the record-file-to-root walkers (`artifact_core.repo_root_of`, `specs._repo_root_of`, `status_set._repo_root_of`, `record_placement._find_repo_root`, `ipd_lint.lint_file`, `orchestrator_readiness.run_coverage`, `check_engine._identity_rename_hint`) for records that live under `AW_HOME`: they derive a root from a RECORD path, which is the records-root accessor's job.
  - Carrier: 4uw2a6
- Moving control state and isolated worktrees under `AW_HOME`, and making `ipd_lifecycle.checkout_control_root`, `runner_shared.state_root`, `worktree_lease` and the path heuristics honor it: this plan only makes the lane RECOGNIZE its project.
  - Carrier: qk0ew6
- Changing `engine.read_installed_version` to find a home `system/VERSION`: the system-root accessor child owns it; E-05 reuses whatever it returns.
  - Carrier: 4gn1ka
  - Carrier-Evidence: .aw/records/plans/executed/20261015-cleantgt-02-4gn1ka-route-every-system-bundle-reader-through-one-system-root-acc.ipd.md
- Removing `doctor.run`'s local git-root bound (`climbed in Path(git_root).resolve().parents`): redundant once `ivq0nr` lands, behaviour-neutral, and `ivq0nr` already declined it.
  - Carrier-Declined: redundant-but-correct code with no defect; `ivq0nr` Deferred row records the same decision.

## Scope check

- Over-scope: none. Every item serves recognition of a clean-target project with no in-repo `.aw` (backlog `kvwwt0`, Set `cleantgt` Order 03 in the brief).
- Under-scope: the brief names `find_project_root`, `is_project_dir`, `classify_project_dir`, `doctor.probe_environment`, `cli._collect_repo_status_details`, and recognition from an external worktree under `AW_HOME`; all are covered (E-02..E-05). `cli._run_status`'s cwd fallback is added because F-05 shows `aw status` would otherwise list nothing from a lane. The remaining `.aw`-presence probes are classified in F-07 and carried by `kfnfji`.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_clean_target_recognition.py -v` (E-06), with the mutation proof.
- Narrowed neighbour run listed in E-07, then bare `python3 -m pytest` (paste the summary line).
- The E-01 scratch probe re-run after E-05, showing the fixed table.

## Spec / documentation sync

- No `.spec.md` edit in this plan. Spec `20260810-1447-01` Section 4 already states a clean-target policy "can therefore leave no target `.aw/`"; this plan makes the readers consistent with that sentence rather than changing it. The Section 4/5 amendment for the whole Set is owned by Order 07 `nwporz` (brief), which records the behavior once it is end-to-end true.
- Docstrings of `find_project_root`, `is_project_dir`, `classify_project_dir` are updated in E-04 (code documentation, not user-facing prose).
- No CHANGELOG entry here: Order 07 writes the single Set entry.

## Open questions

### OQ-01: Should root recognition key on the stored home `project.json` alone, or also on `delivery_mode == "clean-delta"`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence: key on BOTH. `project_config_dir` returns the home dir whenever `<AW_HOME>/projects/<id>/config/project.json` exists, which `public-target-private-companion` and any custom policy can also produce, and spec `20260810-1447-01` Section 6 keeps those presets' `system` in-tree, so they still carry `<repo>/.aw` and are recognized by the existing marker. Requiring stored `delivery_mode == "clean-delta"` (the value the installer writes, measured in the scratch `project.json`: `"delivery_mode": "clean-delta"`) limits the new marker to exactly the population that has no in-repo `.aw`, and reads the stored policy as the brief requires (never a preset name, irjoga PR-003/PR-004).

### OQ-02: How does an external lane find its project without a git subprocess, and does that break the submodule rule?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved by measurement (F-04): a linked worktree's gitfile points into `<common>/worktrees/<name>`, whose `commondir` file names the common dir; a submodule's gitfile points into `<parent>/.git/modules/<name>`, which has no `commondir`. E-02 maps only the former, so a submodule is never given its parent's identity by this plan and `ivq0nr`'s "registered submodule uses the parent" rule stays the sole authority for submodules. The anchor agrees with `ipd_lifecycle.checkout_control_root` ("common dir named `.git` -> its parent"), so a lane's identity and its control root name the same checkout. The lane keeps its own working-tree root (F-03), which is the property `aw commit` in a lane depends on.

### OQ-03: Should an explicit `--dir <external lane>` be honored as the lane or mapped to the main checkout?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from the decided rule in `resolve_verb_repo_root`'s docstring ("An EXPLICIT `--dir` is honored verbatim (resolved, no climb) ... THIS IS A DECIDED RULE (IPD ci9kx2-02 `lmyeas` OQ-01)"): honored verbatim, and after E-03/E-04 the lane IS a recognized project root (`is_project_dir(<lane>)` True) carrying its main checkout's identity, so `--dir <lane>` and a lane cwd behave the same. Nothing maps a lane to the main checkout's PATH, which keeps lane-scoped git verbs (`aw commit`, `aw ipd finalize` in a lane) operating on the lane.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: PASTE the execution-HEAD sha, the `ivq0nr` boundary rule as it now reads in `find_project_root` (or its `blocked` record), and the pasted baseline table from the scratch probe (root / subdir / external lane x `is_project_dir`, `find_project_root`, `classify_project_dir`, `project_config_dir`, `resolve_project_context(...).project_id`), with home paths shown relative to the temp dir.
  - Observed evidence:
    Execution HEAD sha: `15193e78d07804769b9143dab7089794a36a0331`

    `ivq0nr` boundary rule in `find_project_root` (`agent_workflows/project_context.py`):
    ```python
        dot_git = curr / ".git"
        if dot_git.exists():
            if _is_registered_submodule(dot_git):
                submodule_encountered = True
            else:
                return None
    ```

    Scratch reproduction baseline table (pre-change):
    | Target Path | `is_project_dir` | `find_project_root` | `classify_project_dir` | `project_config_dir` | `resolve_project_context().project_id` |
    | --- | --- | --- | --- | --- | --- |
    | `<repo>` (root) | `False` | `None` | `no-project` | `.aw/projects/r-5f5872/config` | `r-5f5872` (clean-delta) |
    | `<repo>/sub/deep` (subdir) | `False` | `None` | `no-project` | `repo/sub/deep/.aw/config` | `deep-e83610` (tracked) |
    | `<lane>` (`worktrees/abc123`) | `False` | `None` | `no-project` | `lane/.aw/config` | `abc123-7087a4` (tracked) |
    | `<lane>` with `<AW_HOME>/config` | `False` | `<tmp>/h` | `inside-project` | `lane/.aw/config` | `abc123-7087a4` (tracked) |
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE `git diff -- agent_workflows/project_context.py` hunk adding `checkout_main_root`, and the passing pytest lines for the E-06 (a) cases (main, subdir, in-repo lane, external lane, submodule -> None, bare/non-git -> None).
  - Observed evidence:
    `git diff -- agent_workflows/project_context.py` adding `checkout_main_root`:
    ```diff
+def checkout_main_root(path: str | Path) -> Optional[Path]:
+    """Find the main worktree root of a git checkout without spawning git (IPD fnnwj3).
+
+    Pure, file-based resolver: walks up from ``path`` to the first ancestor holding a ``.git``
+    entry. If that entry is a directory, returns that ancestor (a main worktree is its own
+    main root). If it is a file whose first line is ``gitdir: <dir>``, resolves ``<dir>``, reads
+    ``<dir>/commondir`` (relative to ``<dir>``) to find the common git directory, and returns
+    the common directory's parent iff the common directory is named ``.git`` and ``<dir>`` sits
+    under ``<common>/worktrees/`` (a linked worktree). Returns ``None`` for anything else,
+    including a submodule gitfile (``gitdir: ../.git/modules/<name>``, which has no ``commondir``
+    file), a bare repository worktree, a ``--separate-git-dir`` layout, or a non-git directory.
+
+    File-based and subprocess-free because it is called in per-command hot paths (such as
+    ``find_project_root`` and ``project_config_dir``) that must stay pure, fast, and side-effect
+    free. Intentionally agrees with ``ipd_lifecycle.checkout_control_root``'s rule:
+    a common dir named ``.git`` maps to its parent worktree. Total: any OSError or RuntimeError
+    returns None.
+    """
+    try:
+        curr = Path(path).resolve()
+    except (OSError, RuntimeError):
+        return None
+
+    while True:
+        try:
+            dot_git = curr / ".git"
+            if dot_git.is_dir():
+                return curr
+            if dot_git.is_file():
+                try:
+                    content = dot_git.read_text(encoding="utf-8")
+                except OSError:
+                    return None
+                gitdir_line = None
+                for line in content.splitlines():
+                    line = line.strip()
+                    if line.startswith("gitdir:"):
+                        gitdir_line = line[len("gitdir:") :].strip()
+                        break
+                if not gitdir_line:
+                    return None
+                gitdir = (curr / gitdir_line).resolve()
+                commondir_file = gitdir / "commondir"
+                if not commondir_file.is_file():
+                    return None
+                try:
+                    common_rel = commondir_file.read_text(encoding="utf-8").strip()
+                except OSError:
+                    return None
+                common_dir = (gitdir / common_rel).resolve()
+                if common_dir.name != ".git":
+                    return None
+                candidate_main = common_dir.parent.resolve()
+                try:
+                    worktrees_dir = common_dir / "worktrees"
+                    gitdir.relative_to(worktrees_dir)
+                except ValueError:
+                    return None
+                return candidate_main
+            parent = curr.parent
+            if parent == curr:
+                return None
+            curr = parent
+        except (OSError, RuntimeError):
+            return None
    ```

    Passing pytest line:
    `tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_a_checkout_main_root_table PASSED [ 71%]`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the `project_config_dir` / `resolve_project_context` anchor hunks and the `home_configured_root` hunk, and the passing pytest lines for the E-06 (b) and (b2) cases, including the home `project.json` with `delivery_mode: tracked` -> False case and the root/lane `project_id` equality.
  - Observed evidence:
    `project_config_dir` anchor hunk:
    ```diff
@@ -923,9 +1007,15 @@ def project_config_dir(
         if candidate.exists():
             return target_config

-    repo_abs = _canonical_path(repo)
     eff_aw_home, _, _ = _resolve_effective_aw_home(aw_home=aw_home)
-    project_id = _derive_project_id(repo_abs)
+    anchor = repo
+    try:
+        if (repo / ".git").exists():
+            anchor = checkout_main_root(repo) or repo
+    except (OSError, RuntimeError):
+        anchor = repo
+    anchor_abs = _canonical_path(anchor)
+    project_id = _derive_project_id(anchor_abs)
     home_config = Path(eff_aw_home) / "projects" / project_id / "config"
     if (home_config / "project.json").exists():
         return home_config
    ```

    `resolve_project_context` anchor hunk:
    ```diff
@@ -1520,7 +1649,13 @@ def resolve_project_context(
         project_id = policy_pid.strip()
         pid_source = PrecedenceLevel.PROJECT_DURABLE_CONFIG.value
     else:
-        project_id = _derive_project_id(repo_abs)
+        anchor_repo = Path(repo_abs)
+        try:
+            if (anchor_repo / ".git").exists():
+                anchor_repo = checkout_main_root(anchor_repo) or anchor_repo
+        except (OSError, RuntimeError):
+            pass
+        project_id = _derive_project_id(_canonical_path(anchor_repo))
         pid_source = PrecedenceLevel.BUILTIN_DEFAULTS.value
    ```

    `home_configured_root` hunk:
    ```diff
+def home_configured_root(
+    path: str | Path,
+    aw_home: Optional[str | Path] = None,
+) -> bool:
+    """True if ``path`` is an installed clean-target AW project root (IPD fnnwj3).
+
+    True iff:
+    1. ``path / ".git"`` exists (the path is a git worktree root, main or linked; never
+       a subdirectory, avoiding PR-001 false-positives on subdirectories).
+    2. ``project_config_dir(path, aw_home)`` is not ``<path>/.aw/config`` (its configuration
+       is home-stored rather than in-tree).
+    3. The home configuration directory's ``project.json`` is a file.
+    4. The stored ``project.json`` has ``delivery_mode == "clean-delta"`` (read directly;
+       never re-derived from preset name).
+
+    A linked lane worktree keeps its own working-tree root (so git operations within the lane
+    target the lane worktree) and shares only configuration identity with the main checkout,
+    mirroring ``ipd_lifecycle.checkout_control_root``. Total: returns False on any OSError.
+    """
+    try:
+        p = Path(path).resolve()
+        if not (p / ".git").exists():
+            return False
+        cfg = project_config_dir(p, aw_home=aw_home)
+        target_cfg = p / ".aw" / "config"
+        if _canonical_path(cfg) == _canonical_path(target_cfg):
+            return False
+        proj_json = cfg / "project.json"
+        if not proj_json.is_file():
+            return False
+        data = _read_json_file(str(proj_json))
+        if not data or not isinstance(data, dict):
+            return False
+        mode = data.get("delivery_mode")
+        return mode == DeliveryMode.CLEAN_DELTA.value or mode == "clean-delta"
+    except (OSError, RuntimeError):
+        return False
    ```

    Passing pytest lines for E-06 (b) and (b2):
    `tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_b_home_configured_root_table PASSED [ 42%]`
    `tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_b2_identity_table PASSED [100%]`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the `find_project_root`/`is_project_dir`/`classify_project_dir` diff (code and docstrings) and the passing pytest lines for E-06 (c) and (d), including the `<AW_HOME>/config/`-present case returning the lane root rather than `$HOME`, plus the E-01 probe re-run showing the fixed table.
  - Observed evidence:
    `find_project_root` / `is_project_dir` / `classify_project_dir` diff:
    ```diff
@@ -432,7 +502,8 @@ def find_project_root(start: Optional[str | Path] = None) -> Optional[Path]:
       to its enclosing parent project. Detect it without spawning git: its ``.git`` is a file whose
       gitdir sits under the parent's ``.git/modules/``, and that admin dir has no ``commondir``. Prints
       one notice line to stderr saying the parent project was used.
-    - Submodules with their own ``.aw/`` use themselves (unchanged). Linked worktrees carry their own ``.aw/``.
+    - Submodules with their own ``.aw/`` use themselves (unchanged). Linked worktrees carry their own ``.aw/``
+      or are recognized via home configuration (IPD fnnwj3).
     - Any other nested git repository without ``.aw/`` (its own ``.git`` directory, a vendored or scratch
       clone) stops at its own boundary and never binds to an outer project.

@@ -449,8 +520,10 @@ def find_project_root(start: Optional[str | Path] = None) -> Optional[Path]:
     while True:
         if curr in ceilings:
             return None
-        if _is_project_marker(curr / ".aw") or _is_project_marker(
-            curr / ".agents", legacy=True
+        if (
+            _is_project_marker(curr / ".aw")
+            or _is_project_marker(curr / ".agents", legacy=True)
+            or home_configured_root(curr)
         ):
             if submodule_encountered:
                 sys.stderr.write(f"notice: parent project was used at {curr}\n")
@@ -634,7 +707,8 @@ def git_root_for_message(start_dir: Optional[str | Path] = None) -> Optional[str
 def is_project_dir(repo_root: str | Path) -> bool:
     """True if ``repo_root`` is (or contains) an AW project marker - i.e. a real project, not a bare
     directory with nothing to survey. Used by repo-scoped verbs to decide between running and
-    emitting ``no_project_message`` (IPD awretrofit Order 06).
+    emitting ``no_project_message`` (IPD awretrofit Order 06). Also returns True for an installed
+    home-configured clean-target root or linked worktree (IPD fnnwj3, via ``home_configured_root``).

     Returns False immediately if ``repo_root`` resolves to a temporary root container or
     configured project ceiling (see ``_project_climb_ceilings``).
@@ -648,8 +722,10 @@ def is_project_dir(repo_root: str | Path) -> bool:
     if p in _project_climb_ceilings():
         return False

-    return _is_project_marker(p / ".aw") or _is_project_marker(
-        p / ".agents", legacy=True
+    return (
+        _is_project_marker(p / ".aw")
+        or _is_project_marker(p / ".agents", legacy=True)
+        or home_configured_root(p)
     )


@@ -703,6 +779,8 @@ def classify_project_dir(path: Optional[str | Path] = None) -> ProjectClassifica
     re-implementing root detection or walking the filesystem independently. Pure, read-only,
     and side-effect-free. Per IPD ivq0nr OQ-01 maintainer decision (2026-10-15), root detection in
     ``find_project_root`` bounds upward discovery at enclosing git repository ceilings.
+    Recognizes home-configured clean-target projects and linked lane worktrees via
+    ``home_configured_root`` and ``checkout_main_root`` (IPD fnnwj3).
    ```

    Passing pytest lines for E-06 (c) and (d):
    `tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_c_predicate_table PASSED [ 14%]`
    `tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_d_negative_controls PASSED [ 57%]`

    Scratch probe re-run (post-fix table):
    | Target Path | `is_project_dir` | `find_project_root` | `classify_project_dir` | `project_config_dir` | `resolve_project_context().project_id` |
    | --- | --- | --- | --- | --- | --- |
    | root (`repo`) | `True` | `repo` | `is-project-root` | `.aw/projects/repo-7f87cb/config` | `repo-7f87cb` (clean-delta) |
    | subdir (`deep`) | `False` | `repo` | `inside-project` | `repo/sub/deep/.aw/config` | `deep-a8bb49` (tracked) |
    | external lane (`abc123`) | `True` | `abc123` | `is-project-root` | `.aw/projects/repo-7f87cb/config` | `repo-7f87cb` (clean-delta) |
    | lane subdir (`x`) | `False` | `abc123` | `inside-project` | `.aw/projects/repo-7f87cb/worktrees/abc123/x/.aw/config` | `x-eb1b0e` (tracked) |
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the `doctor.py`/`cli.py` diff and the actual JSON fields from `aw doctor --dir <clean root> --json` (`layout`, `preset`, `records_backend`) and `aw status --json` run from the root and from the external lane with a user config registering no repos (subprocesses driven by E-06 (e) and (f), reached via `doctor.run` -> `probe_environment` and `cli._run_status` -> the `if not repos:` cwd fallback -> `_collect_repo_status_details`).
  - Observed evidence:
    `doctor.py` and `cli.py` diffs:
    ```diff
--- a/agent_workflows/doctor.py
+++ b/agent_workflows/doctor.py
@@ -374,7 +374,8 @@ def probe_environment(
-        has_aw = (repo_root / ".aw").is_dir()
+        has_home_clean = project_context.home_configured_root(repo_root)
+        has_aw = (repo_root / ".aw").is_dir() or has_home_clean
         has_agents = (repo_root / ".agents").is_dir()
         if has_aw and engine.detect_split_brain_layout(repo_root):
             res.layout = ".aw + .agents (dual layout / split-brain)"
@@ -387,7 +388,10 @@ def probe_environment(
                 )
             )
         elif has_aw:
-            res.layout = ".aw"
+            if not (repo_root / ".aw").is_dir() and has_home_clean:
+                res.layout = "home (clean-target)"
+            else:
+                res.layout = ".aw"
         elif has_agents:
             res.layout = ".agents"
         else:
--- a/agent_workflows/cli.py
+++ b/agent_workflows/cli.py
@@ -9690,7 +9690,8 @@ def _collect_repo_status_details(repo: Path, packaged: str) -> dict:

     state = "source-root" if is_source else versioning.status(installed, packaged)

-    has_aw = (repo / ".aw").is_dir()
+    has_home_clean = project_context.home_configured_root(repo)
+    has_aw = (repo / ".aw").is_dir() or has_home_clean
         has_agents = (repo / ".agents").is_dir()
@@ -9699,7 +9700,10 @@ def _collect_repo_status_details(repo: Path, packaged: str) -> dict:
         layout = ".aw + .agents"
         split_brain = True
     elif has_aw:
-        layout = ".aw"
+        if not (repo / ".aw").is_dir() and has_home_clean:
+            layout = "home (clean-target)"
+        else:
+            layout = ".aw"
         split_brain = False
     elif has_agents:
         layout = ".agents"
@@ -9855,6 +9859,7 @@ def _run_status(args, term: Term, context: Optional[Any] = None) -> int:
             (cwd / ".git").is_dir()
             or (cwd / ".aw").is_dir()
             or (cwd / ".agents").is_dir()
+            or project_context.home_configured_root(cwd)
         ):
             repos = [cwd]
    ```

    `aw doctor --dir <clean root> --json` actual output fields:
    ```json
      "env": {
        "is_source_repo": false,
        "installed_version": "1.3.0rc2.dev10925+g15193e78d.d20261016",
        "packaged_version": "1.3.0rc2.dev10925+g15193e78d.d20261016",
        "version_status": "dev",
        "layout": "home (clean-target)",
        "preset": "completely-clean-target",
        "backend": "home",
        "setup_needed": false,
        "pypi_latest": null,
        "pypi_checked": false,
        "drift": []
      }
    ```

    `aw status --json` with empty config repos (cwd = clean root):
    ```json
    [
      {
        "path": "/tmp/.../repo",
        "installed": "1.3.0rc2.dev10925+g15193e78d.d20261016",
        "is_source": false,
        "state": "dev",
        "layout": "home (clean-target)",
        "preset": "completely-clean-target",
        "backend": "home",
        "split_brain": false
      }
    ]
    ```

    `aw status --json` with empty config repos (cwd = external lane):
    ```json
    [
      {
        "path": "/tmp/.../worktrees/abc123",
        "installed": "1.3.0rc2.dev10925+g15193e78d.d20261016",
        "is_source": false,
        "state": "dev",
        "layout": "home (clean-target)",
        "preset": "completely-clean-target",
        "backend": "home",
        "split_brain": false
      }
    ]
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE `python3 -m pytest -o addopts="" tests/test_clean_target_recognition.py -v` output passing, the same run FAILING with `home_configured_root` forced to return False (name the failing tests), the same run FAILING with the `checkout_main_root` anchor dropped from `project_config_dir` (name the failing (b2)/(c) lane tests), and passing again after each restore (`git diff -- agent_workflows/project_context.py` empty of the mutation).
  - Observed evidence:
    Passing test run:
    ```
tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_c_predicate_table PASSED [ 14%]
tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_f_attention_and_context_subprocesses PASSED [ 28%]
tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_b_home_configured_root_table PASSED [ 42%]
tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_d_negative_controls PASSED [ 57%]
tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_a_checkout_main_root_table PASSED [ 71%]
tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_e_doctor_and_status_subprocesses PASSED [ 85%]
tests/test_clean_target_recognition.py::TestCleanTargetRecognition::test_b2_identity_table PASSED [100%]
============================== 7 passed in 49.76s ==============================
    ```

    Mutation 1 (force `home_configured_root` to return `False`):
    Failed tests:
    - `test_b_home_configured_root_table`: `AssertionError: False is not true : expected home_configured_root(clean_root) == True`
    - `test_c_predicate_table`: `AssertionError: False is not true : expected is_project_dir(clean_root) == True`
    - `test_e_doctor_and_status_subprocesses`: `AssertionError: 'none' != 'home (clean-target)'`
    - `test_f_attention_and_context_subprocesses`: `AssertionError: 2 != 0 : lane aw attention failed (exit 2)`
    Restored and verified: `git diff -- agent_workflows/project_context.py` clean of mutation.

    Mutation 2 (drop `checkout_main_root` anchor from `project_config_dir`):
    Failed tests:
    - `test_b2_identity_table`: `AssertionError: 'abc123-...' != 'repo-...' : resolve_project_context(lane).project_id must match root`
    - `test_c_predicate_table`: `AssertionError: .../h != .../worktrees/abc123 : find_project_root(lane_with_home_config)`
    - `test_b_home_configured_root_table`: `AssertionError: False is not true : expected home_configured_root(lane) == True`
    - `test_e_doctor_and_status_subprocesses`: `AssertionError: 0 != 1 : expected lane in status repos`
    - `test_f_attention_and_context_subprocesses`: `AssertionError: 'abc123-...' != 'repo-...'`
    Restored and verified: `git diff -- agent_workflows/project_context.py` clean of mutation.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: PASTE the narrowed neighbour run summary and the bare `python3 -m pytest` summary line; for any failure, paste the same test failing on the base commit.
  - Observed evidence:
    Narrowed neighbour run (`python3 -m pytest -o addopts="" tests/test_clean_target_recognition.py tests/test_clean_target_config_home.py tests/test_nonsurveyable_root_refusal.py tests/test_explicit_dir_non_project.py tests/test_explicit_dir_subdir_resolution.py tests/test_project_context.py tests/test_doctor.py tests/test_validator_nonsurveyable_dir.py`):
    ```
======================= 123 passed in 102.13s (0:01:42) ========================
    ```

    Bare full suite (`python3 -m pytest`):
    ```
NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
707 passed in 18.29s
    ```
    No failures observed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern, recognizing a clean-target project root; the primitives (E-02/E-03), the predicate wiring (E-04) and the two reporters (E-05) must ship together or `aw status` and `aw doctor` disagree with the verbs about whether the repo is installed.

EXECUTION CONTRACT. Execute only after explicit human approval, and only after `4gn1ka` and `ivq0nr` are executed (`- Item-Dependencies:`; the runner re-checks at dispatch and marks this plan `dependency-blocked` until then). At review (2026-10-15) `ivq0nr` was `reviewed` with `Readiness: no-go` on its OQ-01 (`Blocking: yes`, `Owner: maintainer`: should `find_project_root` stop at a `.git` boundary with no AW marker); this plan is held until a human answers that question and `ivq0nr` executes. Orchestrator `ucr3h8` records the same external dependency. No question is open. Start a hand execution in an isolated worktree with `aw work begin fnnwj3` (or `aw ipd begin fnnwj3` inside the lane). Commit ONLY files changed for this plan through `aw commit fnnwj3 -- <paths>`; never `git add -A`/`-a`, never `--no-verify`, never push; verify the staged set with `git diff --cached --name-only` first (shared checkout). HONESTY RULE (hard MUST): every `V-*` pastes ACTUAL output; run the suite BARE as `python3 -m pytest`. Every scratch install and `aw` subprocess runs with `AW_NO_REEXEC=1` and temp `HOME`, `XDG_CONFIG_HOME`, `AW_HOME`, never the operator's real `AW_HOME`. SCOPE FENCE: `- Scope-Paths:` is a declaration reconciled at finalize; a necessary out-of-scope edit is made and justified with `--scope-reason`, a declared path left unmodified is acknowledged with `--scope-ack`. Do NOT relocate control state or worktrees here (that is `qk0ew6`).

POST-GATE LIFECYCLE. Under `aw oc run` / `aw agy run` the runner finalizes after its merge-and-revalidate gate, so the executor does not. In a hand execution, fill every `V-*`, confirm `aw ipd lint --phase pre-transition` conforms, then `aw ipd finalize fnnwj3`; never hand-`git mv` the plan. This plan inherits `- Blocks-Release: next` from `kvwwt0`.
