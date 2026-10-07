# IPD: Remove a lane once its work is on main, at run end and on demand with aw lanes prune

- Date: 2026-10-07
- Kind: child
- Concern: Lanes outlive their usefulness. Measured 2026-10-07: 11 lane worktrees under `.aw/worktrees/`, six of them with every commit already on `main` and nothing uncommitted (`3mv7li` and `9g97e5` merged on 2026-10-03, three review-sweep lanes whose runs had ended, `0bjke0` executed and merged), plus one branch git could not resolve (`aw/lane/685iq8`). Two gaps keep them: (1) a review-sweep lane is refused teardown when any review in it ended without a collected submission (event `review-sweep-lane-preserved`, reason `uncollected-submission` for `wn956n`, which never ran), because `lane_containment.teardown_review_sweep_lane` treats "no receipt" as "not collected" even for an item that started no turn; (2) the only path that reclaims a merged lane is `runner_shared.reclaim_lanes_on_interrupt`, which runs on interrupt only, so a lane that is merged later (by a later run, `aw oc integrate`, or a hand merge) is never revisited. There is no command to clean up.
- Scope: (1) Count an item that started no turn (`fail-depend`, `not-run`, skipped before dispatch) as having nothing to collect in the review-sweep teardown; (2) at the END of every run, on both hosts, run the existing reclaim decision over this run's lanes (not only on interrupt); (3) add `aw lanes` with `list` (read-only table of every lane: owner, live or not, commits not on main, uncommitted files, verdict) and `prune` (dry run by default; `--apply` removes every lane that is reclaimable and not owned by a live process, through the existing R5.5 inventory gate); (4) report broken lane branches without touching them. EXCLUDES removing any lane with unmerged commits or uncommitted files, ever; author worktrees outside `aw/lane/*`; and the pre-existing interrupt path's behavior.
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/lanes_cli.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_lanes_prune.py, CHANGELOG.md
- Item-Dependencies: none
- Status: draft
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: lanegc
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 45z93e

## Workflow history

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A lane disappears as soon as nothing in it is unsaved: at the end of the run that made it, or later when someone runs `aw lanes prune --apply`. A lane that holds anything not on `main` is never removed, and the maintainer can always see which lanes exist and why.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the review-sweep lane

- [ ] E-01 In `lane_containment.teardown_review_sweep_lane`, treat an item that recorded NO attempt in the sweep lane (no `attempts` entry naming that lane: `fail-depend`, `not-run`, skipped) as having nothing to collect, instead of answering "uncollected". An item that started a turn keeps today's rule (no receipt means not collected).
  - Depends on: none
  - Expected outcome: a sweep whose last item was `fail-depend` and never ran is torn down at sweep end; a sweep whose item ran and left no receipt is still preserved.
  - Execution state: pending

### Task group 2: reclaim at run end

- [ ] E-02 Call `runner_shared.reclaim_lanes_on_interrupt` (renamed or aliased `reclaim_run_lanes`, keeping the old name for callers) once at the normal END of `run_queue` on both hosts, non-interactively, with reason `run-end`, after the final integration pass and before the summary. It already: leaves live-owned lanes alone, removes recovered and empty lanes through the R5.5 gate, and keeps lanes holding unmerged work. Add one summary line: "lanes: N removed, M kept (aw lanes list)".
  - Depends on: E-01
  - Expected outcome: a two-item scratch run where item A merges and item B is refused ends with A's lane removed and B's kept, both on `oc` and `agy`, and the summary line names the counts.
  - Execution state: pending

### Task group 3: `aw lanes`

- [ ] E-03 Add `agent_workflows/lanes_cli.py` with `aw lanes list`: one row per `aw/lane/*` branch or `.aw/worktrees/*` lane worktree, with columns lane, owner run and pid, LIVE or not (`worktree_lease._owner_is_live`), commits not on `main` (`git cherry`), uncommitted files (`git status --porcelain`), and verdict (`removable`, `keep: unmerged work`, `keep: uncommitted changes`, `keep: live owner`, `broken: <git error>`). Read-only. `--agent`/`--json` supported.
  - Depends on: none
  - Expected outcome: in a scratch repo with one merged clean lane, one unmerged lane, one dirty lane, one lane owned by a live pid and one branch pointing at a missing object, `aw lanes list` prints the five verdicts.
  - Execution state: pending

- [ ] E-04 Add `aw lanes prune`: same table, and for every `removable` row prints the exact commands it would run (`git worktree remove --force <path>` and `git branch -D <branch>`, which is what `runner_shared.teardown_isolation_worktree` does) plus "dry run: pass --apply to remove". With `--apply`, removes each removable lane through `lane_containment.teardown_lane_if_classified` (never a second teardown path) and prints what it removed. A lane whose owner record names another host is `keep: unknown owner`. Broken branches are listed and never removed; the output names the manual command to inspect them.
  - Depends on: E-03
  - Expected outcome: dry run removes nothing and prints the commands; `--apply` removes only the merged clean lane; every other lane and branch is untouched.
  - Execution state: pending

- [ ] E-05 Register `lanes` in `cli.py` and `command_surface.py` with help text, and add a `CHANGELOG.md` entry naming `aw lanes list`, `aw lanes prune [--apply]` and the run-end cleanup.
  - Depends on: E-04
  - Expected outcome: `aw lanes --help`, `aw lanes list --help` and `aw lanes prune --help` print; the changelog names all three.
  - Execution state: pending

### Task group 4: tests

- [ ] E-06 Add `tests/test_lanes_prune.py` driving the real CLI and a scripted run in scratch repos for E-01 to E-04, asserting on `git worktree list`, `git branch --list`, exit codes and output. Include: a lane with an ignored-but-unaccounted file is kept (R5.5 inventory), a live-owned merged lane is kept, and `--apply` twice is a no-op the second time. No source introspection.
  - Depends on: E-02, E-05
  - Expected outcome: the module passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- One teardown path: `lane_containment.teardown_lane_if_classified` is "THE teardown gate (spec R5.5)" and a driver "may not call `teardown_isolation_worktree` for a lane on its own".
- One reclaim decision: `runner_shared.reclaim_lanes_on_interrupt` is "THE lane-reclamation decision. Idempotent; safe to call twice; separately callable."
- `worktree_lease.LaneState.reclaimable` is "NECESSARY BUT NOT SUFFICIENT for teardown"; the R5.5 inventory must also clear.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Six lanes held nothing not already on `main`. | 2026-10-07: `git cherry main aw/lane/<lane>` showed every commit as `-` (equivalent on main) for `3mv7li`, `9g97e5`, `0bjke0`; `worktree_lease.inspect_lane` reported `merged True reclaimable True` for three review-sweep lanes. Five were removed by hand that day. |
| F-02 | A sweep lane is kept because an item that never ran has no receipt. | Run `run-20261007T165351Z-456357` event `review-sweep-lane-preserved`: "an uncollected submission (no attempt-keyed collection receipt at 10-wn956n-attempt-1.json ...)"; `wn956n` was `fail-depend` with zero attempts. |
| F-03 | Merged lanes are reclaimed only on interrupt. | `reclaim_lanes_on_interrupt` is called from the hosts' interrupt handlers only (`oc_runipd.run_queue` "repeated-interrupt" path). |
| F-04 | A lane branch can become unreadable. | `git rev-list main..aw/lane/685iq8` failed with "unknown revision" on 2026-10-07. |

## Proposed changes (ordered, validatable)

1. Sweep lane accounts for items that never ran (E-01).
2. Reclaim at run end (E-02).
3. `aw lanes list` (E-03).
4. `aw lanes prune [--apply]` (E-04).
5. Registration and changelog (E-05).
6. Tests (E-06).

## Deferred / out of scope (with reason)

- Removing author worktrees (`aw/author/*`). They are created by hand and their owners remove them; `aw lanes list` may show them as informational rows only if trivial, otherwise not at all.
  - Carrier-Declined: no defect; hand-made worktrees are the person's to remove.
- Repairing broken lane branches. The cause is not yet known, and repair would be guesswork; listing them makes them visible.
  - Carrier-Declined: reported by `aw lanes list` so a human can decide; no silent action is owed.

## Scope check

- Over-scope: none. `lane_containment.py` E-01, E-04; `runner_shared.py` and both hosts E-02; `lanes_cli.py`, `cli.py`, `command_surface.py`, `CHANGELOG.md` E-03 to E-05; the test module E-06.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_lanes_prune.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.
- `aw lanes list` and `aw lanes prune` (dry run) on this repository, pasted.

## Spec / documentation sync

N/A for specs: the R5.5 gate and reclaim rules are unchanged; this plan only calls them at one more point. `CHANGELOG.md` records the new command.

## Open questions

### OQ-01: Should the run-end cleanup also prune lanes from OTHER, finished runs?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: No. A run cleans up what it made; `aw lanes prune --apply` is the explicit, visible way to clean everything else, so a run never removes a lane another run or person might be relying on.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the sweep-end event for the never-ran case (torn down) and the ran-without-receipt case (preserved).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git worktree list` after the two-item scratch run on each host and the summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw lanes list` on the five-lane scratch repo and on this repository.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the dry run, the `--apply` run, and `git worktree list` / `git branch --list 'aw/lane/*'` before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the three `--help` outputs and the `CHANGELOG.md` diff.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the passing module run with per-test counts and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.
