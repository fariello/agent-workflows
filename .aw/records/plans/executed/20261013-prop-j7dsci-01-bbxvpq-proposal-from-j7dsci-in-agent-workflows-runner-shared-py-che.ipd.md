# IPD: Make the lane hook-bypass check see a renamed file's deleted source so a rename inside executed/ is not refused

- Date: 2026-10-13
- Kind: child
- Concern: Agent proposal from run `run-20261013T012222Z-1160687`, item `j7dsci`. `runner_shared.check_lane_hook_bypass` rebuilds a lane's net change in a disposable worktree at `base`, checks out `head` over it, and removes files deleted in `base..head` found with `git diff --name-only --diff-filter=D base head`. Git's default rename detection reports a moved file as `R`, not `D`, so the move's SOURCE is never removed: the disposable index shows the plan in BOTH `pending/` and `executed/`, which the staged-index `ipd-executed-transition-gate` hook reads as a raw ADD. That ADD is refused when the destination is in `executed/` and the source was ALREADY there (a rename inside `executed/`, e.g. a filename-date repair): the gate exempts an in-`executed/` edit only when `executed_transition_gate._staged_plan_executed_transitions` sees the same `- Id:` at the HEAD path, and an `A` has no HEAD blob. The observed case was exactly this: commit `0d15f3685` renamed `executed/20260101-instsafe-07-qrokie-...` to `executed/20260723-instsafe-07-qrokie-...` (`R099`). A pending->executed move is NOT affected: the gate refuses it without finalize evidence and accepts it with evidence whether or not the source is retained (review probe 2026-10-16). Measured 2026-10-16 (git 2.43.0, scratch repo, `git mv p/a.md e/a.md`): default `--diff-filter=D` prints nothing; with `--no-renames` it prints `p/a.md`. This repository only escapes the bug because its local `.git/config` sets `diff.renames false` (the proposal's interim workaround), which no clone, CI checkout, or managed repository inherits.
- Scope: Pass `--no-renames` to the `git diff` in `check_lane_hook_bypass` so deleted rename sources are removed in the disposable worktree regardless of user or repo `diff.renames` config; add an outcome test that reproduces the refusal for a rename inside `executed/` under the REAL gate hook with rename detection forced ON (repo-local `git config diff.renames true`) and asserts it passes after the fix; give `leak_sanitizer._staged_files` (`--diff-filter=ACM`, which drops a renamed file from the staged leak scan under rename detection) the same `--no-renames` fix with its own test; audit the remaining `--diff-filter` calls in `agent_workflows/`. Does NOT change the hook, the gate, or the local `.git/config` (removing the workaround is the maintainer's choice, see OQ-01).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_lane_rule_break_detection.py, agent_workflows/leak_sanitizer.py, tests/test_leak_sanitizer.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Blocks-Release: next
- Priority: medium
- Set: prop-j7dsci
- Order: 1
- Highest E allocated: 04
- Author: aw agy run model=Gemini-3.8-Flash-High (fleshed by opencode its_direct/pt3-claude-opus-5.5-1m-us)
- Id: bbxvpq

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: bbxvpq verified (set prop-j7dsci, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 PR-002 PR-003 PR-004
- 2026-10-16 to-review (aw set): fleshed from the j7dsci agent proposal; defect reproduced 2026-10-16 (git 2.43.0); reclassified bug/medium gating next release

- 2026-10-13 draft (aw agy run model=Gemini-3.8-Flash-High): created.

## Goal

A lane whose net change renames a file (in particular a plan already in `executed/`) passes the runner's hook-bypass re-check in every checkout, not only in one whose local git config happens to disable rename detection; and the staged leak scan covers renamed files under the same condition.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce, fix, audit

- [x] E-01 Add a test to `tests/test_lane_rule_break_detection.py` beside `test_hook_bypass_staged_gate_move_into_executed`. Fixture: `_setup_repo(pre_commit_cfg=<new config>)` where the new module-level config runs the REAL gate (`entry: "{_PY_ENTRY}" -m agent_workflows ipd-executed-gate`, `pass_filenames: false`, `always_run: true`), with `PYTHONPATH` set to this repository root via `mock.patch.dict(os.environ, ...)` (`check_lane_hook_bypass` passes `dict(os.environ)` to the hook, and the disposable worktree's cwd is the temp repo, so `-m agent_workflows` does not otherwise resolve to the code under test). Run `git config diff.renames true` in the temp repo (the disposable worktree shares that config, so the user's global and this checkout's `.git/config` cannot mask the defect). Base commit: the plan already in `executed/` with `- Status: executed` and its `- Id:`; head commit: `git mv` of that file to a new filename inside `executed/` (same content, same `- Id:`), committed with `--no-verify`. Assert `check_lane_hook_bypass(repo, base, head)` returns `passed is True`. Run it at the pre-fix HEAD and confirm it FAILS with the gate's `raw plan->executed transition (moved into executed/)` refusal.
  - Depends on: none
  - Expected outcome: a new test that fails before E-02 with the real gate's refusal and passes after (review probe 2026-10-16 reproduced exactly this: pre-fix staged `A executed/<new>`, gate exit 1; with `--no-renames`, staged `R100`, gate exit 0).
  - Execution state: performed
- [x] E-02 In `runner_shared.check_lane_hook_bypass`, change the deletion probe to `["git", "diff", "--no-renames", "--name-only", "--diff-filter=D", base, head]`.
  - Depends on: E-01
  - Expected outcome: E-01 passes; the existing `test_hook_bypass_staged_gate_move_into_executed` (a `--no-verify` raw move under the fake staged gate) still returns `passed is False`.
  - Execution state: performed
- [x] E-03 In `leak_sanitizer._staged_files`, add `--no-renames` to the `git diff --cached --name-only --diff-filter=ACM` argv, and add a test to `tests/test_leak_sanitizer.py` that, in a temp repo with `git config diff.renames true`, commits a clean multi-line file, `git mv`s it, appends a planted home-path leak (built by concatenation as the existing staged tests do), stages it, and asserts `run(repo, staged=True)` reports the leak at the NEW path. Confirm the test fails before the one-flag change.
  - Depends on: none
  - Expected outcome: the renamed-and-modified file is scanned in staged mode under rename detection (review probe 2026-10-16: with `diff.renames=true` the ACM probe printed nothing for a renamed file; with `--no-renames` it printed `b.txt`).
  - Execution state: performed
- [x] E-04 Audit every remaining `--diff-filter` use in `agent_workflows/` (`git grep -n -e "--diff-filter" -- agent_workflows`, re-derived at execution) and record each call site and decision in a table in V-04; a call needs `--no-renames` only if it selects added or deleted paths. Add a CHANGELOG line under `## 2.0.0 (pending)` covering E-02 and E-03.
  - Depends on: E-02, E-03
  - Expected outcome: audit table covering every match; no rename-blind add/delete probe remains; CHANGELOG line with no em/en dashes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `check_lane_hook_bypass` was added by plan `62sdwr` E-03 and is called from `runner_shared.execute_item_core` (the `hook_passed, hook_msg = check_lane_hook_bypass(lane_path, lane_base, lane_head)` site); a refusal spends the item's retry budget (`HOOK_BYPASS_RETRY_COUNT_KEY`), so a false refusal costs a whole attempt.
- Tests exercise the function on real temp git repos (`LaneRuleBreakDetectionTests._setup_repo`), per P16.
- Bug-kind work gates the next release (AGENTS.md "Every live bug gates the next release").

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Default rename detection hides a moved file from `--diff-filter=D` | scratch repo 2026-10-16, git 2.43.0: default prints nothing, `--no-renames` prints `p/a.md` |
| F-2 | This checkout escapes only through a local config | `git config --show-origin --get diff.renames` -> `file:.git/config false`; no global value; not set in any tracked file |
| F-3 | The false refusal was observed in a real run, and it was a rename INSIDE `executed/` | proposal `Blocked-By` (run `run-20261013T012222Z-1160687`, item `j7dsci`); `git show -M --name-status 0d15f3685` -> `R099 .aw/records/plans/executed/20260101-instsafe-07-qrokie-... .aw/records/plans/executed/20260723-instsafe-07-qrokie-...` |
| F-3a | A pending->executed move is gated identically whether or not the source is retained, so it cannot reproduce the defect | review probe 2026-10-16 against `executed_transition_gate.check`: retained/removed source with no journal both exit 1; with a matching finalize journal both exit 0 |
| F-4 | Two `--diff-filter` calls select added/deleted paths and are rename-blind | `git grep -n -e "--diff-filter" -- agent_workflows` at review: `runner_shared.check_lane_hook_bypass` (`=D`), `leak_sanitizer._staged_files` (`=ACM`); the other matches are `--diff-filter=U` (unmerged entries, unaffected by renames) in `runner_shared` (re-derive at execution) |
| F-5 | The staged leak scan skips a renamed file under rename detection | review probe 2026-10-16: renamed + appended file, `git -c diff.renames=true diff --cached --name-only --diff-filter=ACM` -> empty; `diff.renames=false` or `--no-renames` -> `b.txt` |

## Proposed changes (ordered, validatable)

E-01 (failing test, real gate, rename inside `executed/`), E-02 (one-flag fix), E-03 (same fix + test for the staged leak scan), E-04 (audit + CHANGELOG).

## Deferred / out of scope (with reason)

- Removing the local `diff.renames false` workaround from this checkout's `.git/config`: a per-machine setting outside version control; whether to keep it is the maintainer's call (OQ-01).
  - Carrier-Declined: not repository content; no tracked change can carry it.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest tests/test_lane_rule_break_detection.py -o addopts=""` before E-02 (new test fails) and after (all pass); `python3 -m pytest tests/test_leak_sanitizer.py -o addopts=""` before and after E-03's flag change; then the bare `python3 -m pytest`.

## Spec / documentation sync

N/A: no spec describes the disposable-worktree deletion probe; CHANGELOG line only.

## Open questions

### OQ-01: Keep the local `diff.renames false` workaround after the fix?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: maintainer decision on machine-local configuration outside repository content
- Resolution or deferral rationale: Not needed for execution. After E-02 the setting is redundant for this check; it still changes `git diff`/`git log` output for humans in this checkout (renames shown as delete+add). Remove with `git config --unset diff.renames` if unwanted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the new test's fixture config line naming `ipd-executed-gate` quoted, and pasted pytest output of the new test FAILING at the pre-fix HEAD with the gate's `moved into executed/` refusal text.
  - Observed evidence:
    Fixture config line in `tests/test_lane_rule_break_detection.py`:
    ```python
    _REAL_GATE_PRE_COMMIT_CONFIG = f"""repos:
    - repo: local
      hooks:
      - id: ipd-executed-gate
        name: ipd executed transition gate
        entry: '"{_PY_ENTRY}" -m agent_workflows ipd-executed-gate'
        language: system
        pass_filenames: false
        always_run: true
    """
    ```
    Pasted pytest failure output at pre-fix HEAD:
    ```
    =================================== FAILURES ===================================
    _ LaneRuleBreakDetectionTests.test_hook_bypass_rename_inside_executed_passes_under_real_gate _

    self = <tests.test_lane_rule_break_detection.LaneRuleBreakDetectionTests testMethod=test_hook_bypass_rename_inside_executed_passes_under_real_gate>

        def test_hook_bypass_rename_inside_executed_passes_under_real_gate(self):
    ...
            with mock.patch.dict(os.environ, {"PYTHONPATH": str(support.REPO_ROOT)}):
                passed, msg = runner_shared.check_lane_hook_bypass(repo, base, head)
    >       self.assertTrue(
                passed, f"expected check_lane_hook_bypass to pass, but got: {msg}"
            )
    E       AssertionError: False is not true : expected check_lane_hook_bypass to pass, but got: ipd executed transition gate.............................................Failed
    E       - hook id: ipd-executed-gate
    E       - exit code: 1
    E
    E       aw ipd executed-transition gate REFUSED this commit (local prevention; the raw plan->executed path bypasses the finalize gates):
    E         - .aw/records/plans/executed/20260901-demo-01-det001-demo.ipd.md (det001): raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/. Do not hand-edit/`git mv` a plan to executed; run `aw ipd finalize det001 --actor <agent/model> --message <summary> --apply` (which runs the receipt/scope/attribution gates and makes the lifecycle commit).
    E       (This is a LOCAL best-effort hook; `--no-verify` bypasses it and the local `aw check`/`aw doctor` proclint detector is the backstop.)

    tests/test_lane_rule_break_detection.py:821: AssertionError
    ----------------------------- Captured stdout call -----------------------------
    [master e1c71b7] add pre-commit config
     1 file changed, 9 insertions(+)
     create mode 100644 .pre-commit-config.yaml
    [master 0c76991] base executed plan
     1 file changed, 1 insertion(+), 1 deletion(-)
     rename .aw/records/plans/{pending => executed}/20260828-demo-01-det001-demo.ipd.md (98%)
    [master 1ee5a7b] rename within executed
     1 file changed, 0 insertions(+), 0 deletions(-)
     rename .aw/records/plans/executed/{20260828-demo-01-det001-demo.ipd.md => 20260901-demo-01-det001-demo.ipd.md} (100%)
    NOTE: 9 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    =========================== short test summary info ============================
    FAILED tests/test_lane_rule_break_detection.py::LaneRuleBreakDetectionTests::test_hook_bypass_rename_inside_executed_passes_under_real_gate
    ======================= 1 failed, 9 deselected in 1.97s ========================
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the changed `git diff` argv quoted from `check_lane_hook_bypass`, and pasted `python3 -m pytest tests/test_lane_rule_break_detection.py -o addopts=""` showing the new test and `test_hook_bypass_staged_gate_move_into_executed` both passing.
  - Observed evidence:
    Changed `git diff` probe argv in `agent_workflows/runner_shared.py` (`check_lane_hook_bypass`):
    ```python
            ["git", "diff", "--no-renames", "--name-only", "--diff-filter=D", base, head]
    ```
    Pasted `python3 -m pytest tests/test_lane_rule_break_detection.py -o addopts=""` output:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=4257740200
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/bbxvpq
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 10 items                                                            collected 10 items

    tests/test_lane_rule_break_detection.py ..........                       [100%]

    ============================= 10 passed in 37.66s ==============================
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the changed `_staged_files` argv quoted, pasted output of the new leak-sanitizer test failing before the flag change and passing after, and pasted `python3 -m pytest tests/test_leak_sanitizer.py -o addopts=""` summary.
  - Observed evidence:
    Changed `_staged_files` argv in `agent_workflows/leak_sanitizer.py`:
    ```python
        out = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "diff",
                "--no-renames",
                "--cached",
                "--name-only",
                "--diff-filter=ACM",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    ```
    Pasted output of new test failing before flag change:
    ```
    =================================== FAILURES ===================================
    _ BinaryAndStagedScanTests.test_staged_scan_renamed_and_modified_file_under_rename_detection _

    self = <tests.test_leak_sanitizer.BinaryAndStagedScanTests testMethod=test_staged_scan_renamed_and_modified_file_under_rename_detection>

        def test_staged_scan_renamed_and_modified_file_under_rename_detection(self):
    ...
            fails, _warns = ls.run(repo, staged=True)
            leaks_at_new_path = [
                f
                for f in fails
                if f.rule == "home-path" and f.location.startswith("leaky_new.txt:")
            ]
    >       self.assertTrue(
                leaks_at_new_path,
                f"expected home-path leak at leaky_new.txt, got findings: {fails}",
            )
    E       AssertionError: [] is not true : expected home-path leak at leaky_new.txt, got findings: []

    tests/test_leak_sanitizer.py:851: AssertionError
    NOTE: 16 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    =========================== short test summary info ============================
    FAILED tests/test_leak_sanitizer.py::BinaryAndStagedScanTests::test_staged_scan_renamed_and_modified_file_under_rename_detection
    ======================= 1 failed, 16 deselected in 0.36s =======================
    ```
    Pasted output of new test passing after flag change:
    ```
    tests/test_leak_sanitizer.py .                                           [100%]

    NOTE: 16 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 1 passed, 16 deselected in 0.32s =======================
    ```
    Pasted `python3 -m pytest tests/test_leak_sanitizer.py -o addopts=""` summary:
    ```
    tests/test_leak_sanitizer.py .................                           [100%]

    ============================== 17 passed in 3.72s ==============================
    ```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted `git grep -n -e "--diff-filter" -- agent_workflows` output with a decision row per match, the CHANGELOG line quoted, and the bare `python3 -m pytest` summary line.
  - Observed evidence:
    Pasted `git grep -n -e "--diff-filter" -- agent_workflows`:
    ```
    agent_workflows/leak_sanitizer.py:719:            "--diff-filter=ACM",
    agent_workflows/runner_shared.py:658:    Read via `git diff --name-only --diff-filter=U`, which reports exactly the conflicted entries and
    agent_workflows/runner_shared.py:664:    _rc, out, _err = _run_git(repo, ["diff", "--name-only", "--diff-filter=U"])
    agent_workflows/runner_shared.py:676:    * a CONTENT CONFLICT starts the merge, so `MERGE_HEAD` EXISTS, `git diff --diff-filter=U` names
    agent_workflows/runner_shared.py:679:      by merge") never starts the merge at all, so `MERGE_HEAD` is ABSENT, `--diff-filter=U` is EMPTY,
    agent_workflows/runner_shared.py:6229:            wt_path, ["diff", "--name-only", "--diff-filter=U"]
    agent_workflows/runner_shared.py:6378:    rc_u, out_u, _ = _run_git(lane_path, ["diff", "--name-only", "--diff-filter=U"])
    agent_workflows/runner_shared.py:10174:            ["git", "diff", "--no-renames", "--name-only", "--diff-filter=D", base, head],
    ```
    Audit table:
    | Match | Function / Context | Filter | Needs `--no-renames`? | Decision & Rationale |
    | --- | --- | --- | --- | --- |
    | `agent_workflows/leak_sanitizer.py:719` | `_staged_files` | `ACM` | Yes | Added `--no-renames` so staged renames are not classified as `R`, ensuring the added destination is scanned for leaks. |
    | `agent_workflows/runner_shared.py:658, 664, 676, 679` | `_conflicted_paths` | `U` | No | Unmerged conflicted entries cannot be resolved as renames; unaffected by rename detection. Keep as-is. |
    | `agent_workflows/runner_shared.py:6229` | `_merge_and_revalidate_candidate` | `U` | No | Unmerged conflict check; unaffected by rename detection. Keep as-is. |
    | `agent_workflows/runner_shared.py:6378` | `_report_unmerged_conflicts` | `U` | No | Unmerged conflict reporting; unaffected by rename detection. Keep as-is. |
    | `agent_workflows/runner_shared.py:10174` | `check_lane_hook_bypass` | `D` | Yes | Added `--no-renames` so deleted rename sources are reported as `D` and removed from the disposable worktree, preventing false raw add refusals in `executed/`. |

    Quoted CHANGELOG line:
    ```markdown
    - Fixed: `runner_shared.check_lane_hook_bypass` and `leak_sanitizer._staged_files` now pass `--no-renames` to `git diff`, ensuring deleted rename sources are removed in disposable worktrees and renamed files are scanned for staged leaks even when git rename detection is enabled.
    ```

    Pasted bare `python3 -m pytest` summary line:
    ```
    708 passed in 34.08s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Small, low-risk bug fix. Execution contract:

- Open questions: OQ-01 is non-blocking and needs no answer for execution.
- Scope fence: `- Scope-Paths:` declares what this plan edits. An edit outside it is allowed when needed and must be justified at finalize (`--scope-reason`); do not stop over it.
- Honesty: you MUST paste the ACTUAL runner output in each `V-*`; never claim a pass you did not run.
- Commits: path-scoped via `aw commit bbxvpq -- <paths>`; never `git add -A`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize, so leave the plan in `pending/`. Executed by hand (`aw work begin bbxvpq`), finish with `aw ipd finalize bbxvpq --actor <agent/model> --message <summary> --apply`; never `git mv` the plan to `executed/`.

## Agent Proposal from j7dsci

- Run-Id: run-20261013T012222Z-1160687
- Proposing-Item: j7dsci
- Lane-Branch: aw/lane/j7dsci
- Blocked-By: aw ipd executed-transition gate REFUSED this commit (local prevention; the raw plan->executed path bypasses the finalize gates): .aw/records/plans/executed/20260723-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md (qrokie): raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/.
- Kind: tool-defect
- Size: small

### Why
check_lane_hook_bypass in runner_shared.py prepares a detached test worktree by checking out head and running git diff --name-only --diff-filter=D base head to find and remove deleted files. Because git diff performs rename detection by default, any rename is classified as R rather than D, leaving proc_diff empty. As a result, the old filename from base is never removed from the disposable worktree while the new filename is added, turning the staged rename into a raw addition (A) into executed/, which triggers the ipd-executed-transition-gate refusal. Fixing this in runner_shared.py requires passing --no-renames to git diff, but editing runner_shared.py is out of scope for IPD j7dsci.

### Proposed Change
In agent_workflows/runner_shared.py:check_lane_hook_bypass, pass --no-renames to git diff: subprocess.run(["git", "diff", "--no-renames", "--name-only", "--diff-filter=D", base, head], ...). In the interim, setting git config diff.renames false in the repository config allows git diff to report the deleted rename source without modifying runner code out of scope.

### Affected Paths
- agent_workflows/runner_shared.py
