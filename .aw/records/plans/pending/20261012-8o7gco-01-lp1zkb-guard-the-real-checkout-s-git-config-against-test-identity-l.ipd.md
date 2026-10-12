# IPD: Guard the real checkout's git config against test identity leaks and pin the leaking test

- Date: 2026-10-12
- Kind: child
- Concern: Something in the test suite wrote `user.name = Test` / `user.email = test@example.com` into this repository's SHARED `.git/config` (the common dir every worktree reads), so 322 real runner and agent commits between 2026-10-08 01:31:49 and 2026-10-09 09:06:05 carry the test identity (backlog `8o7gco`). Nothing in the suite detects such a write, so it can recur silently.
- Scope: (1) a pytest plugin, loaded by the root `conftest.py`, that snapshots the identity-bearing keys of the real checkout's git config files at session start, re-checks them after every test, FAILS the test that observed a change (naming the key, old and new value, and the file), and restores the snapshot so the damage is contained; (2) harden `tests/support.init_repo` so a failed `git init` can never fall through and run `git config` against an enclosing repository; (3) behavior tests for both; (4) one full-suite run including `slow` under the guard to pin and fix the leaking test, if it still leaks. No history rewrite, no change to product code under `agent_workflows/`.
- Scope-Paths: conftest.py, tests/git_config_guard.py, tests/support.py, tests/test_git_config_guard.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 8o7gco
- Blocks-Release: next
- Set: 8o7gco
- Order: 1
- Highest E allocated: 05
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: lp1zkb

## Workflow history

- 2026-10-12 to-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog 8o7gco; review-ready.
- 2026-10-12 draft (opencode): created.

## Goal

Make any test that writes git identity into the real checkout's config fail loudly, by name, in the run where it happens, with the config restored; and find and fix the test that did it in October 2026 if it still does.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: measure, then guard

- [ ] E-01 RE-MEASURE THE STATE BEFORE CHANGING ANYTHING. Run `git config --file "$(git rev-parse --git-common-dir)/config" --get-regexp '^(user|author|committer)\.'` (expected today: no output, exit 1, i.e. the identity block has already been removed, F-02), `git config --show-origin --get user.email` (expected: the global file), and `git log --author=test@example.com --format='%h %ad' | sed -n '1p;$p'` plus `| wc -l` to restate the affected window. If the `[user]` block is PRESENT again, the leak has recurred since 2026-10-12: record the first and last affected commit and DO NOT remove the block by hand in this plan (removal is the maintainer's call per backlog need (1)); continue, because the guard is still required. Paste all output.
  - Depends on: none
  - Expected outcome: pasted current identity state and the affected-commit window, establishing whether the leak is live.
  - Execution state: pending

- [ ] E-02 Add `tests/git_config_guard.py`, a pytest plugin. Target repository: the env var `AW_TEST_GIT_CONFIG_GUARD_REPO` when set (used only by the E-04 end-to-end test), else `config.rootpath`. At `pytest_configure` (runs in the controller and in every xdist worker), resolve the guarded files by running `git -C <repo> rev-parse --git-common-dir` (the shared `config`) and `git -C <repo> rev-parse --git-path config.worktree` (only if it exists), and record for each file the values of every key matching `^(user|author|committer)\.` via `git config --file <f> --get-regexp`. If the target is not a git checkout, the plugin disables itself silently. Then an autouse fixture (or a `pytest_runtest_teardown` hookwrapper) re-reads those keys after each test; on ANY difference it (a) restores the snapshot with `git config --file <f>` (`--unset-all` for an added key, set the old value for a changed or removed one), and (b) fails the test with a message of the form `GIT CONFIG GUARD: <nodeid> left <file> changed: user.email: <absent> -> 'test@example.com'; restored. Under xdist the writer may be a concurrent test in another worker; rerun with -o addopts="" -m '' to attribute it.` Keep the per-test cost to two `git config` subprocesses at most, and skip the subprocess entirely when the files' `(st_mtime_ns, st_size)` are unchanged since the last check, so the bare suite does not slow perceptibly (E-05 measures it). Guard identity keys ONLY, not the whole file: concurrent agents legitimately change other keys (worktrees, branch tracking) during a run, and a whole-file check would fail correct tests (decision D-1).
  - Depends on: E-01
  - Expected outcome: a plugin that, given a repo whose config gains `user.email` during a test, fails that test with the message above and leaves the config as it was before the test.
  - Execution state: pending

- [ ] E-03 Load the plugin and harden the helper. Append `"tests.git_config_guard"` to `pytest_plugins` in `conftest.py` with a comment block in the file's existing style (what went wrong, measured window, why identity keys only). In `tests/support.init_repo`, check the `git init` return code and then assert `git -C <path> rev-parse --show-toplevel` resolves to `path` itself (compare `Path.resolve()`); on either failure raise `RuntimeError` naming the path BEFORE any `git config` runs, and pass `--local` to the three `git config` calls. This closes the specific fall-through where `support.git` (which uses `check=False`) lets a failed init leave `git config` acting on whatever repository encloses `path`.
  - Depends on: E-02
  - Expected outcome: a bare `python3 -m pytest` loads the guard, and `init_repo` on a path whose `git init` fails or whose toplevel is an enclosing repo raises instead of writing config.
  - Execution state: pending

### Task group 2: prove, then pin the culprit

- [ ] E-04 Add `tests/test_git_config_guard.py`, asserting on outcomes only (exit codes, output text, resulting config values; never on source text). Cases: (a) END-TO-END: in `tmp_path`, `git init` a repo, write a `test_leak.py` whose one test runs `git config user.email test@example.com` in that repo and a `test_clean.py` that does nothing; run `sys.executable -m pytest -p tests.git_config_guard -o addopts="" <tmp>` as a subprocess with `PYTHONPATH` = `support.REPO_ROOT`, `AW_TEST_GIT_CONFIG_GUARD_REPO` = the tmp repo, cwd = the tmp repo; assert exit code 1, output contains `GIT CONFIG GUARD` and the leaking test's node id, `test_clean` passed, and `git config --file <tmp>/.git/config --get user.email` afterwards exits 1 (restored); (b) a pre-existing identity value changed by the test is restored to the ORIGINAL value, not unset; (c) a test changing a NON-identity key (e.g. `core.foo`) is not failed; (d) a non-git target disables the guard (exit 0); (e) `support.init_repo` on a path where `git init` cannot succeed (a regular FILE at that path) raises `RuntimeError` and the enclosing tmp repo's config has no `user.email`. Show (a) and (e) FAIL on the base commit (the commit before this plan's first code change) by running the new module in a `git worktree` of it, and paste the failures.
  - Depends on: E-03
  - Expected outcome: the new module passes; (a) and (e) demonstrably fail without the change.
  - Execution state: pending

- [ ] E-05 Run the suites under the guard. First take a bare-suite baseline BEFORE the first code change (`python3 -m pytest`, record the summary line and failing test names). After E-04: run the bare suite again (bar: no NEW failure by test name versus the baseline, and wall time within normal run-to-run variance of the baseline, pasted side by side), then the slow suite `python3 -m pytest -m slow` (the backlog's suspect: the first bad commit came from a lane that ran it). If the guard fires in either, rerun the named test file with `python3 -m pytest -o addopts="" -m '' <file>` (serial, so attribution is exact; this is the one place `-o addopts=""` is justified), find the `git config` call that resolved to the real checkout, fix it to target its temp repo (out-of-Scope-Paths edits justified at finalize with `--scope-reason <path>=fixes the identity leak pinned by the guard`), and rerun until clean. If the guard fires in neither, record that plainly: the original writer is not reproducible at this HEAD and the guard is the protection. Finally re-run the E-01 commands and paste that the real config still carries no identity block.
  - Depends on: E-04
  - Expected outcome: pasted baseline and post-change bare-suite summaries, the slow-suite summary, either the pinned-and-fixed culprit or the explicit "not reproducible" record, and the unchanged real config.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite: run BARE as `python3 -m pytest`; `pyproject.toml` `addopts` already carries `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Narrowed or serial runs use `-o addopts=""`. The slow tier is `-m slow` / `make test-all` (`-m ''`).
- Root `conftest.py` already hosts session-wide isolation guards with explanatory comment blocks (`_restore_home_sandbox`, the `AW_EXECUTION_ROLE` scrub, the hang guard) and loads helper plugins through `pytest_plugins = ["tests.deselect_notice", "tests.livecorpus_notice"]`; the new guard follows the same pattern.
- `tests/support.git` runs with `check=False`, and `tests/support.init_repo` runs `git init` then three `git config` calls through it (quoted: `git(path, "config", "user.email", "test@example.com")`).
- Tests assert on behavior, never on source text (AGENTS.md, GUIDING_PRINCIPLES P16).
- Commit through `aw commit lp1zkb -- <paths>`; never push.
- Cite code by SYMBOL; line numbers drift (spec `ipd-structure-and-linting` 10.2).

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | 322 commits carry `Test <test@example.com>`, all between 2026-10-08 01:31:49 and 2026-10-09 09:06:05; none before. The real identity's last commit before the window is `ea16d89ac` at 01:31:02, the first test-identity commit is `80c8a93d8` (AW-Item `w89bo8`, run `run-20261007T182117Z-1726614`), the last is `e6e12c181`. | `git log --author=test@example.com --format=%h \| wc -l` -> 322; `--until='2026-10-08 01:31:00'` -> 0; `git log --since='2026-10-08 01:31:00' --until='2026-10-09 09:06:06' --format=%an \| sort \| uniq -c` -> `322 Test`, `1 Gabriele Fariello`. (The backlog's "317" was measured earlier on 2026-10-09.) |
| F-02 | The identity block is ALREADY GONE from the shared config at authoring time, so backlog need (1) (restore local identity) is satisfied; commits since 2026-10-10 use the real identity. | `git config --file "$(git rev-parse --git-common-dir)/config" --get-regexp '^user\.'` -> exit 1, no output; `git config --show-origin --get user.email` -> the global `~/.gitconfig`; `git log -3` shows the real author. |
| F-03 | Worktrees share the common-dir `config`; `extensions.worktreeConfig` is not set, so a `git config` run in ANY lane worktree writes the shared file. | `git rev-parse --git-common-dir` from this lane -> the main checkout's `.git`; `git config --get extensions.worktreeConfig` -> exit 1. |
| F-04 | The written values exactly match `tests/support.init_repo`, and `support.git` ignores failures, so a failed `git init` would let the following `git config` calls act on an enclosing repo. Dozens of other tests write the same literal through their own helpers. | `tests/support.py`: `def git(...)` uses `check=False`; `init_repo` writes `user.email test@example.com` / `user.name Test`. `grep -rn 'user.email' tests` lists ~30 files writing `test@example.com` or similar. |
| F-05 | No product code writes `user.*` to a repository config except the upgrade rehearsal, which writes `aw-upgrade-test` into its own sandbox, not `Test`. So the writer is a test, not the toolkit. | `grep -rn 'user\.email\|user\.name' agent_workflows`: only `leak_sanitizer.py` (reads) and `upgrade_rehearsal.py` (`git(sandbox, "config", "--local", "user.name", "aw-upgrade-test", ...)`). |
| F-06 | Nothing in the suite checks the real checkout's git config, so the write went unnoticed for ~31 hours and 322 commits. | Root `conftest.py` guards `AW_HOME`/`XDG_CONFIG_HOME` and the execution role only; no hook references `.git/config`. |

## Proposed changes (ordered, validatable)

1. Measure current state and window (E-01).
2. Identity-key git-config guard plugin: per-test check, fail and restore (E-02).
3. Load it from the root conftest; make `init_repo` fail closed (E-03).
4. Behavior tests, shown failing on the base commit (E-04).
5. Bare and slow suites under the guard; pin and fix the culprit if it still leaks (E-05).

## Deferred / out of scope (with reason)

- Rewriting the 322 commits' authorship: the backlog itself marks it NOT recommended (published commits, and every lane/run record cites those hashes); a history rewrite is a maintainer decision, recorded as OQ-01.
  - Carrier-Declined: deliberate non-goal; rewriting published history is the maintainer's decision and the item recommends against it
- Restoring the local identity: already done (F-02); E-01 re-measures it.
  - Carrier-Declined: already satisfied on disk at authoring time, so no work remains
- Enabling `extensions.worktreeConfig` so lanes cannot write the shared config: changes git semantics for every worktree and every tool in this checkout; the guard catches the write wherever it lands.
  - Carrier-Declined: a repository-wide git configuration change outside this bug's remedy; the guard covers the failure mode
- Auditing every one of the ~30 test helpers that write identity: each already targets its own temp repo by construction; the guard pins any that does not, which is cheaper and complete for the paths the suite exercises.
  - Carrier-Declined: superseded by the guard, which names any offending helper at runtime

## Scope check

- Over-scope: none. `conftest.py` (E-03 plugin load), `tests/git_config_guard.py` (E-02), `tests/support.py` (E-03), `tests/test_git_config_guard.py` (E-04).
- Under-scope: the file holding the leaking test is unknown until E-05 runs; if one is found its fix lands under `--scope-reason` at finalize.

## Required tests / validation

- `tests/test_git_config_guard.py` (new), with cases (a) and (e) shown failing on the base commit.
- Bare suite `python3 -m pytest`, compared to a pre-change baseline by failing-test name and wall time.
- Slow suite `python3 -m pytest -m slow` under the guard.
- Real checkout's shared config carries no identity block after all runs (E-01 commands re-run).

## Spec / documentation sync

N/A: test infrastructure only. No spec governs the test suite's isolation guards (searched `.aw/records/specs/` for "conftest" and "git config"), and no user-facing behavior changes, so no CHANGELOG entry. The rationale lives in the `conftest.py` comment block, matching the existing guards.

## Open questions

### OQ-01: Rewrite the authorship of the 322 test-identity commits?

- Blocking: no
- Status: deferred
- Owner: maintainer
- Resolution or deferral rationale: Not done by this plan. The backlog item states it is NOT recommended (published commits; run records and plan evidence cite these hashes). The maintainer may decide otherwise separately; nothing in this plan depends on it.
- Carrier-Declined: a maintainer-only decision about published history that the backlog recommends against; no code work is owed

### OQ-02: Guard identity keys only, or the whole config file?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Decision D-1, identity keys (`user.*`, `author.*`, `committer.*`) only. Evidence: this checkout is shared by concurrent agents and runners (AGENTS.md "Shared checkout"), and `git worktree add`, branch tracking and remotes legitimately rewrite other keys mid-run, so a whole-file check would fail correct tests at random. The defect and its harm (wrong commit provenance) are confined to identity keys. Reversible: widening the regex is a one-line change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the three E-01 commands' actual output (shared-config identity query with its exit code, `--show-origin` line, affected-commit first/last/count), and state whether the block was present.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `tests/git_config_guard.py`'s diff and the E-04 case (a) subprocess output (produced by the plugin's per-test check from E-02) showing the `GIT CONFIG GUARD: <nodeid> ... restored` failure line naming the leaking test only, plus the post-run `git config --get user.email` exit 1 on the tmp repo.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `conftest.py` and `tests/support.py` diffs, the E-04 case (e) passing, and the header of a bare `python3 -m pytest` run (or `python3 -m pytest --trace-config -o addopts="" --co -q tests/test_git_config_guard.py`) showing `tests.git_config_guard` registered.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_git_config_guard.py` passing all cases (a)-(e), and the same module run in a `git worktree` of the base commit with (a) and (e) FAILING.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the baseline and post-change bare-suite summary lines with wall times and any failing test names, the `python3 -m pytest -m slow` summary, then EITHER the guard failure naming the culprit plus its fix diff and a clean rerun, OR an explicit statement that the guard fired in neither run; and the final E-01 identity query showing exit 1, no output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved lp1zkb --by-human`). Open questions: OQ-01 deferred to the maintainer and non-blocking; OQ-02 resolved (D-1). Begin with `aw ipd begin lp1zkb`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition. A culprit fix pinned by E-05 lands outside it and is justified at finalize with `--scope-reason <path>=<why>`. Do NOT hand-edit `.git/config`: if E-01 finds the identity block present again, report it; removal is the maintainer's decision. Test fixture repos live only under pytest `tmp_path`.

Honesty: paste the ACTUAL runner output for every test or command claim; never claim a result you did not run.

Commits: only the paths you changed, through `aw commit lp1zkb -- <paths>`; never push, never tag.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; by hand, after every `V-*` passes and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize lp1zkb`. Release gate: inherits `Blocks-Release: next` from `8o7gco`, which closes `done` through the From-Backlog handoff once this plan is executed.
