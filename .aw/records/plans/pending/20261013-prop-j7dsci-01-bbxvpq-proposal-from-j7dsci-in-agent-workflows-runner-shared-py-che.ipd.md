# IPD: Make the lane hook-bypass check see a renamed file's deleted source so a tooled move into executed/ is not refused

- Date: 2026-10-13
- Kind: child
- Concern: Agent proposal from run `run-20261013T012222Z-1160687`, item `j7dsci`. `runner_shared.check_lane_hook_bypass` rebuilds a lane's net change in a disposable worktree at `base`, checks out `head` over it, and removes files deleted in `base..head` found with `git diff --name-only --diff-filter=D base head`. Git's default rename detection reports a moved file as `R`, not `D`, so the move's SOURCE is never removed: the disposable index shows the plan in BOTH `pending/` and `executed/`, which the staged-index `ipd-executed-transition-gate` hook reads as a raw ADD into `executed/` and refuses. Measured 2026-10-16 (git 2.43.0, scratch repo, `git mv p/a.md e/a.md`): default `--diff-filter=D` prints nothing; with `--no-renames` it prints `p/a.md`. This repository only escapes the bug because its local `.git/config` sets `diff.renames false` (the proposal's interim workaround), which no clone, CI checkout, or managed repository inherits.
- Scope: Pass `--no-renames` to the `git diff` in `check_lane_hook_bypass` so deleted rename sources are removed in the disposable worktree regardless of user or repo `diff.renames` config; add an outcome test that reproduces the refusal with rename detection forced ON (`-c diff.renames=true` via `GIT_CONFIG_*` env or a repo-local config in the test repo) and asserts the tooled move passes; audit the other `git diff ... --diff-filter` calls in `agent_workflows/` for the same rename blindness and fix any that select deletions. Does NOT change the hook, the gate, or the local `.git/config` (removing the workaround is the maintainer's choice, see OQ-01).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_lane_rule_break_detection.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Blocks-Release: next
- Priority: medium
- Set: prop-j7dsci
- Order: 1
- Highest E allocated: 03
- Author: aw agy run model=Gemini-3.8-Flash-High (fleshed by opencode its_direct/pt3-claude-opus-5.5-1m-us)
- Id: bbxvpq

## Workflow history
- 2026-10-16 to-review (aw set): fleshed from the j7dsci agent proposal; defect reproduced 2026-10-16 (git 2.43.0); reclassified bug/medium gating next release

- 2026-10-13 draft (aw agy run model=Gemini-3.8-Flash-High): created.

## Goal

A lane whose net change moves a plan into `executed/` through the tooled finalize path passes the runner's hook-bypass re-check in every checkout, not only in one whose local git config happens to disable rename detection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce, fix, audit

- [ ] E-01 Add a test to `tests/test_lane_rule_break_detection.py` beside `test_hook_bypass_staged_gate_move_into_executed`, reusing `_setup_repo(pre_commit_cfg=_STAGED_GATE_PRE_COMMIT_CONFIG)`: force rename detection ON for the test repo (`git config diff.renames true` in the temp repo, so the user's global config cannot mask the defect), make a TOOLED move of the plan into `executed/` (one the staged gate accepts: the same finalize-evidence fixture the existing passing cases use, or a non-plan rename such as `src/a.txt` -> `src/b.txt` if no accepting fixture exists, asserting the disposable index does not retain the source), and assert `check_lane_hook_bypass(repo, base, head)` returns `passed is True`. Run it at HEAD and confirm it FAILS for the rename reason before the fix.
  - Depends on: none
  - Expected outcome: a new test that fails before E-02 with the gate refusal (or a retained source path) and passes after.
  - Execution state: pending
- [ ] E-02 In `runner_shared.check_lane_hook_bypass`, change the deletion probe to `["git", "diff", "--no-renames", "--name-only", "--diff-filter=D", base, head]`.
  - Depends on: E-01
  - Expected outcome: E-01 passes; the existing `test_hook_bypass_staged_gate_move_into_executed` (a `--no-verify` raw move) still returns `passed is False`.
  - Execution state: pending
- [ ] E-03 Audit every `git diff` / `git log` call in `agent_workflows/` that uses `--diff-filter` or parses deleted paths (`git grep -n -e "--diff-filter" -- agent_workflows`) and add `--no-renames` wherever the caller needs deletions or adds to appear as such; record each call site and the decision in a table in V-03. Add a CHANGELOG line under `## 2.0.0 (pending)`.
  - Depends on: E-02
  - Expected outcome: audit table covering every match; no other rename-blind deletion probe remains; CHANGELOG line with no em/en dashes.
  - Execution state: pending

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
| F-3 | The false refusal was observed in a real run | proposal `Blocked-By` (run `run-20261013T012222Z-1160687`, item `j7dsci`): gate refused the move of `qrokie` into `executed/` |
| F-4 | Only one `--diff-filter` call exists in `agent_workflows/` at authoring | `git grep -n -e "--diff-filter" -- agent_workflows` -> `runner_shared.check_lane_hook_bypass` only (re-derive at execution) |

## Proposed changes (ordered, validatable)

E-01 (failing test), E-02 (one-flag fix), E-03 (audit + CHANGELOG).

## Deferred / out of scope (with reason)

- Removing the local `diff.renames false` workaround from this checkout's `.git/config`: a per-machine setting outside version control; whether to keep it is the maintainer's call (OQ-01).
  - Carrier-Declined: not repository content; no tracked change can carry it.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest tests/test_lane_rule_break_detection.py -o addopts=""` before E-02 (new test fails) and after (all pass), then the bare `python3 -m pytest`.

## Spec / documentation sync

N/A: no spec describes the disposable-worktree deletion probe; CHANGELOG line only.

## Open questions

### OQ-01: Keep the local `diff.renames false` workaround after the fix?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Not needed for execution. After E-02 the setting is redundant for this check; it still changes `git diff`/`git log` output for humans in this checkout (renames shown as delete+add). Remove with `git config --unset diff.renames` if unwanted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output of the new test FAILING at the pre-fix HEAD, showing the rename-caused refusal or retained source path.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the changed `git diff` argv quoted from `check_lane_hook_bypass`, and pasted `python3 -m pytest tests/test_lane_rule_break_detection.py -o addopts=""` showing the new test and `test_hook_bypass_staged_gate_move_into_executed` both passing.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `git grep -n -e "--diff-filter" -- agent_workflows` output with a decision row per match, the CHANGELOG line quoted, and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Small, low-risk bug fix. Execute after review and approval in an isolated worktree (`aw work begin bbxvpq`), commit via `aw commit bbxvpq -- <paths>`, never push. Paste ACTUAL output in each `V-*`.

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
