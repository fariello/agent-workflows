# IPD: Remove a lane once its work is on main, at run end and on demand with aw lanes prune

- Date: 2026-10-07
- Kind: child
- Concern: Lanes outlive their usefulness. Measured 2026-10-07: 11 lane worktrees under `.aw/worktrees/`, six of them with every commit already on `main` and nothing uncommitted (`3mv7li` and `9g97e5` merged on 2026-10-03, three review-sweep lanes whose runs had ended, `0bjke0` executed and merged), plus one branch git could not resolve (`aw/lane/685iq8`). Two gaps keep them: (1) a review-sweep lane is refused teardown when any review in it ended without a collected submission (event `review-sweep-lane-preserved`, reason `uncollected-submission` for `wn956n`, which never ran), because `lane_containment.teardown_review_sweep_lane` treats "no receipt" as "not collected" even for an item that started no turn; (2) the only path that reclaims a merged lane is `runner_shared.reclaim_lanes_on_interrupt`, which runs on interrupt only, so a lane that is merged later (by a later run, `aw oc integrate`, or a hand merge) is never revisited. There is no command to clean up.
- Scope: (1) Count an item that started no turn (`fail-depend`, `not-run`, skipped before dispatch) as having nothing to collect in the review-sweep teardown; (2) at the END of every run, on both hosts, run the existing reclaim decision over this run's lanes (not only on interrupt); (3) add `aw lanes` with `list` (read-only table of every lane: owner, live or not, commits not on main, uncommitted files, verdict) and `prune` (dry run by default; `--apply` removes every lane that is reclaimable and not owned by a live process, through the existing R5.5 inventory gate); (4) report broken lane branches without touching them. EXCLUDES removing any lane with unmerged commits or uncommitted files, ever; author worktrees outside `aw/lane/*`; and the pre-existing interrupt path's behavior.
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/lanes_cli.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_lanes_prune.py, CHANGELOG.md, .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
- Item-Dependencies: none
- Status: approved
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: lanegc
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 45z93e
- Approval: 2026-10-09, recorded via aw ipd set: status set to approved
- Readiness: go-pending-approval

## Workflow history
- 2026-10-09 approved (aw set): status set to approved
- 2026-10-08 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; see /plan-review record
- 2026-10-08 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed: run-end reuse of the interrupt reclaimer would snapshot preserved lanes and force-remove empty lanes around the R5.5 gate), PR-002 (HIGH, fixed: prune had no run/item context so the gate refuses every lane; new E-07 resolver), PR-003..PR-009 fixed. Record: .aw/records/reviews/20261007-lanegc-01-45z93e-remove-a-lane-once-its-work-is-on-main-at-run-end-and-on-dem.review.md Round 1.
- 2026-10-07 to-review (aw set): authored review-ready at the maintainer's request 2026-10-07

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A lane disappears as soon as nothing in it is unsaved: at the end of the run that made it, or later when someone runs `aw lanes prune --apply`. A lane that holds anything not on `main` is never removed, and the maintainer can always see which lanes exist and why.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the review-sweep lane

- [ ] E-01 In `lane_containment.teardown_review_sweep_lane`, treat an item that recorded NO attempt in the sweep lane (no `attempts` entry whose `worktree_lane_id` or `worktree` names that lane: `fail-depend`, `not-run`, `skipped`, `dependency-blocked`) as having nothing to collect, instead of answering "uncollected". FAIL CLOSED on the evidence, not on the status label: the exemption applies only when that item's lane submission root (`lane_containment.lane_submission_root(<lane>, <run-id>, item, 1)`) is absent or empty, because `attempt_key` returns 1 for a zero-attempt item and a file there would be exactly the uncollected output R2.5 protects. An item that started a turn keeps today's rule (no receipt means not collected). The rule lives in the gate, not in `runner_shared.retire_review_sweep_lane`'s item filter, so both hosts get it from one place (spec R2.6).
  - SPEC: this narrows spec `7ckptx` R2.5's "Absence of a record means NOT collected" for one case, so amend R2.5 with one sentence (an item that recorded no attempt in a lane and has no submission under its lane submission root has nothing to collect in that lane) and record it with `aw specs note`. The spec stays `implementing`.
  - Depends on: none
  - Expected outcome: a sweep whose last item was `fail-depend` and never ran is torn down at sweep end; a sweep whose item ran and left no receipt is still preserved; a zero-attempt item with a file under its submission root still preserves the lane.
  - Execution state: pending

### Task group 2: reclaim at run end

- [ ] E-02 Add a RUN-END mode to `runner_shared.reclaim_lanes_on_interrupt` (a keyword-only `mode` parameter defaulting to today's interrupt behavior, plus a `reclaim_run_lanes` alias; existing callers unchanged) and call it once at the normal end of `run_queue` on both hosts, non-interactively, with reason `run-end`: in `oc_runipd.run_queue` and `agy_runipd.run_queue`, directly after the `runner_shared.retire_review_sweep_lane(...)` block and before `write_report(run_dir, state)`, so the report and summary see the result. Run-end mode differs from the interrupt path in exactly three ways, because the interrupt path was written for an aborted run and reusing it unchanged is unsafe at a normal end: (1) it NEVER calls `worktree_lease.snapshot_lane_dirty_work`, since a lane preserved on purpose (integration refused, missing input) would otherwise gain a commit labelled "WIP INTERRUPTED SNAPSHOT (not finished work)" on every run; (2) EVERY removal, including the provably-empty and clean-stale branch that today calls `worktree_lease.teardown_worktree(repo, handle, force=True)` directly, goes through `reclaim_lane_through_gate`, because that direct call is blind to an uncollected submission under the gitignored `.aw/state/lane-submissions/` tree and run-end would apply it to every run rather than only to interrupted ones; (3) its events are named `lane-reclaimed-at-run-end` / `lane-preserved-at-run-end` rather than the `-on-interrupt` names. The interrupt path's behavior is unchanged (Scope). It still leaves lanes owned by another live process alone and keeps lanes holding unmerged work, and the existing spec R5.6a preserved-lane summary stays the place that names kept lanes. Add one summary line: "lanes: N removed, M kept (aw lanes list)".
  - Depends on: E-01
  - Expected outcome: a two-item scratch run where item A merges and item B is refused ends with A's lane removed and B's kept, on both `oc` and `agy`; B's branch gains no snapshot commit; an empty lane holding a file under its submission root is kept with an `uncollected-submission` reason; the summary line names the counts.
  - Execution state: pending

### Task group 3: `aw lanes`

- [ ] E-03 Add `agent_workflows/lanes_cli.py` with `aw lanes list`: one row per `aw/lane/*` branch or per worktree registered on such a branch, with columns lane, owner run and pid, live or not, commits not landed, uncommitted files, and verdict (`removable`, `keep: unmerged work`, `keep: uncommitted changes`, `keep: live owner`, `keep: unknown owner`, `keep: no run record`, `broken: <git error>`). DERIVE EVERY FACT FROM THE EXISTING READERS, never from a new git probe: the lane facts from `worktree_lease.inspect_lane`, ownership from `worktree_lease.lane_owned_by_other_live_process` (which already treats another host or undeterminable liveness as owned), and the landed question from `runner_shared.classify_lane_integration` (ancestry first, then patch id on a clean lane, against `LANE_INTEGRATION_TARGET_FALLBACK`, never a hardcoded `main`). That function's docstring says "Do not fork a second lane resolver", and a `git cherry` column here would be one. A worktree under `.aw/worktrees/` that is not on an `aw/lane/*` branch (for example a detached `.aw-isocommit-*` tree) is listed as `other: not a lane` and is never a removal candidate. Read-only. `--agent`/`--json` supported.
  - Depends on: E-07
  - Expected outcome: in a scratch repo with one merged clean lane, one unmerged lane, one dirty lane, one lane owned by a live pid, one lane with no run record, one detached worktree and one branch pointing at a missing object, `aw lanes list` prints each verdict.
  - Execution state: pending

- [ ] E-04 Add `aw lanes prune`: same table, and for every `removable` row prints the worktree path and branch it would remove plus "dry run: pass --apply to remove". With `--apply`, for each removable row: RE-READ ownership immediately before acting (a driver may have adopted the lane since the table was built; `worktree_lease.lane_is_safe_to_adopt` treats a dead owner as adoptable), skip any lane whose owning run's driver lock is held by a live process (`run_viewer.driver_holder_state(run_dir) == run_viewer.HOLDER_LIVE`), then remove it through `lane_containment.teardown_lane_if_classified` with the `run_dir` and `item` E-07 resolved, or through `lane_containment.teardown_review_sweep_lane` with every item for a sweep lane (never a second teardown path). Without run and item context that gate refuses every lane by design (`submission_retention`: "no run directory or item was supplied"), which is why E-07 exists. A gate refusal is printed with its reason codes and the lane is kept. Broken branches and lanes with no run record are listed and never removed; the output names the manual command to inspect them. Exit 0 when every removable lane was removed or nothing was removable; exit 1 when a removable lane was refused by the gate.
  - Depends on: E-03, E-07
  - Expected outcome: dry run removes nothing; `--apply` removes only the merged clean lane; every other lane and branch is untouched; a lane with an unaccounted untracked file is refused with `unknown-untracked`; a second `--apply` is a no-op.
  - Execution state: pending

- [ ] E-05 Register `lanes` in `cli.py` and `command_surface.py` with help text, and add a `CHANGELOG.md` entry naming `aw lanes list`, `aw lanes prune [--apply]` and the run-end cleanup.
  - Depends on: E-04
  - Expected outcome: `aw lanes --help`, `aw lanes list --help` and `aw lanes prune --help` print; the changelog names all three.
  - Execution state: pending

### Task group 4: tests

- [ ] E-06 Add `tests/test_lanes_prune.py` driving the real CLI and a scripted run in scratch repos for E-01 to E-04, asserting on `git worktree list`, `git branch --list`, exit codes and output. Include: a lane with an unaccounted UNTRACKED file is kept (R5.5 inventory) while a lane whose only extra content is an IGNORED file such as `__pycache__/x.pyc` is removed (R5.5 as amended 2026-09-18: "Gitignored files ... are disposable upon lane destruction and do not block teardown"); a live-owned merged lane is kept; a lane with no run record is kept; the interrupt path still snapshots (its behavior is unchanged); and `--apply` twice is a no-op the second time. No source introspection (AGENTS.md P16).
  - Depends on: E-01, E-02, E-04, E-05, E-07
  - Expected outcome: the module passes, `tests/test_command_surface_declarations.py`, `tests/test_agent_surface_conformance.py` and `tests/test_lane_reclaim_decision_order.py` still pass, and the bare suite adds no failure relative to the lane baseline.
  - Execution state: pending

### Task group 5: lane-to-run resolution

- [ ] E-07 Add, in `agent_workflows/lanes_cli.py`, a resolver from a lane to the run record and queue item that own it: discover run directories with `run_viewer.discover_run_dirs`, load each `state.json`, enumerate its lanes with `runner_shared.lane_records_including_sweep`, match on `(branch, worktree)`, and return the run directory plus the owning item (`runner_shared.interrupt_lane_item_record`) or, for a review sweep lane, every review item exactly as `runner_shared.retire_review_sweep_lane` builds its list. Return none for a lane no run record names; E-03 renders that as `keep: no run record`. Read-only; a malformed `state.json` is skipped, never guessed at.
  - Depends on: none
  - Expected outcome: in a scratch repo with two run records, each lane resolves to its own run and item, a sweep lane resolves to its review items, and an unrecorded lane resolves to none.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- One teardown path: `lane_containment.teardown_lane_if_classified` is "THE teardown gate (spec R5.5)" and a driver "may not call `teardown_isolation_worktree` for a lane on its own".
- One reclaim decision: `runner_shared.reclaim_lanes_on_interrupt` is "THE lane-reclamation decision. Idempotent; safe to call twice; separately callable."
- `worktree_lease.LaneState.reclaimable` is "NECESSARY BUT NOT SUFFICIENT for teardown"; the R5.5 inventory must also clear.
- One landing reader: `runner_shared.classify_lane_integration` ("Do not fork a second lane resolver"), feeding `stranded_lane_records` and `attention.stranded_lane_drift`.
- R5.5 as amended 2026-09-18 (spec `7ckptx`): ignored files never block teardown; dirty tracked, unknown untracked and uncollected submissions do.
- The integration target is the checkout's `HEAD` (`LANE_INTEGRATION_TARGET_FALLBACK`), not a literal `main`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Six lanes held nothing not already on `main`. | 2026-10-07: `git cherry main aw/lane/<lane>` showed every commit as `-` (equivalent on main) for `3mv7li`, `9g97e5`, `0bjke0`; `worktree_lease.inspect_lane` reported `merged True reclaimable True` for three review-sweep lanes. Five were removed by hand that day. |
| F-02 | A sweep lane is kept because an item that never ran has no receipt. | Run `run-20261007T165351Z-456357` event `review-sweep-lane-preserved`: "an uncollected submission (no attempt-keyed collection receipt at 10-wn956n-attempt-1.json ...)"; `wn956n` was `fail-depend` with zero attempts. |
| F-03 | Merged lanes are reclaimed only on interrupt. | `reclaim_lanes_on_interrupt` is called from the hosts' interrupt handlers only (`oc_runipd.run_queue` "repeated-interrupt" path). |
| F-04 | A lane branch can become unreadable. | `git rev-list main..aw/lane/685iq8` failed with "unknown revision" on 2026-10-07. Re-checked at review 2026-10-08: `git for-each-ref refs/heads/aw/lane/685iq8` prints nothing, so that ref is now gone; the broken case is tested on a constructed ref rather than on this repository. |
| F-05 | (review) The interrupt reclaimer snapshots dirty lanes and force-removes empty ones outside the R5.5 gate. | `runner_shared.reclaim_lanes_on_interrupt`: the `holds_work` branch calls `worktree_lease.snapshot_lane_dirty_work(..., note=f"Reason: {reason}.")`; the final empty/stale branch calls `worktree_lease.teardown_worktree(repo, handle, force=True)` with no inventory. Acceptable for an aborted run; not for every normal run end. |
| F-06 | (review) The R5.5 gate refuses every lane without run and item context. | `runner_shared.reclaim_lane_through_gate` docstring: "with either missing, `submission_retention` answers 'no run directory or item was supplied ...' and the gate refuses EVERY lane". |
| F-07 | (review) Live lane population at review. | 2026-10-08 in this checkout: 13 `aw/lane/*` branches; by ancestry 6 merged, 7 not; a detached `.aw/worktrees/.aw-isocommit-*` worktree and four detached `.aw/state/suite-baselines/*` worktrees also exist. Context only; re-derive at execution. |

## Proposed changes (ordered, validatable)

1. Sweep lane accounts for items that never ran (E-01).
2. Reclaim at run end (E-02).
3. `aw lanes list` (E-03).
4. `aw lanes prune [--apply]` (E-04).
5. Registration and changelog (E-05).
6. Tests (E-06).
7. Lane-to-run resolver (E-07).

## Deferred / out of scope (with reason)

- Removing author worktrees (`aw/author/*`). They are created by hand and their owners remove them; `aw lanes list` may show them as informational rows only if trivial, otherwise not at all.
  - Carrier-Declined: no defect; hand-made worktrees are the person's to remove.
- Repairing broken lane branches. The cause is not yet known, and repair would be guesswork; listing them makes them visible.
  - Carrier-Declined: reported by `aw lanes list` so a human can decide; no silent action is owed.

## Scope check

- Over-scope: none. `lane_containment.py` E-01, E-04; `runner_shared.py` and both hosts E-02; `lanes_cli.py`, `cli.py`, `command_surface.py`, `CHANGELOG.md` E-03 to E-05; the test module E-06.
- Under-scope: corrected at review: the lane-to-run resolver (E-07), the run-end mode (E-02), the non-lane worktree rule (E-03), and the spec `7ckptx` R2.5 sentence (E-01), now declared in `- Scope-Paths:`.

## Required tests / validation

- `python3 -m pytest tests/test_lanes_prune.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.
- `aw lanes list` and `aw lanes prune` (dry run) on this repository, pasted; the lane population is live, so no count from this plan is a bar.
- `python3 -m pytest -o addopts="" tests/test_command_surface_declarations.py tests/test_agent_surface_conformance.py tests/test_lane_reclaim_decision_order.py`.
- `aw ipd lint --phase pre-transition --agent <this plan>`, `aw specs check`, `aw sanitize --agent`.

## Spec / documentation sync

Spec `7ckptx` (status `implementing`) R2.5 gains one sentence (E-01), declared in `- Scope-Paths:`. Why: E-01 narrows "Absence of a record means NOT collected" for an item that never ran in the lane, and an unrecorded narrowing of a data-safety rule is the drift the spec exists to prevent. The R5.5 gate itself is unchanged; this plan calls it at two more points. `CHANGELOG.md` records the new command, in user-facing prose with no em or en dashes.

## Open questions

### OQ-01: Should the run-end cleanup also prune lanes from OTHER, finished runs?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: No. A run cleans up what it made; `aw lanes prune --apply` is the explicit, visible way to clean everything else, so a run never removes a lane another run or person might be relying on.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the `review-sweep-lane-retired` event for the never-ran case, the `review-sweep-lane-preserved` event with `uncollected-submission` for the ran-without-receipt case, the same preserved event for a zero-attempt item with a file under its submission root, and the spec R2.5 diff plus its `aw specs note` line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each host, paste `git worktree list` and `git branch --list 'aw/lane/*'` after the two-item scratch run, `git log -1 --format=%s` on B's branch showing no `WIP INTERRUPTED SNAPSHOT` subject, the `lane-reclaimed-at-run-end` event for A, the kept-empty-lane event naming `uncollected-submission`, and the summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw lanes list` and `aw lanes list --agent` on the E-03 scratch repo (every verdict present) and `aw lanes list` on this repository.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the dry run, the `--apply` run with its exit code, the refused lane's reason codes, the second `--apply` showing nothing removed, and `git worktree list` / `git branch --list 'aw/lane/*'` before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the three `--help` outputs and the `CHANGELOG.md` diff.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the passing module run with per-test counts, the three surface/reclaim module runs, the bare `python3 -m pytest` summary line, and the before and after failing node-id sets showing nothing new.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste a scratch-repo session printing, for each lane, the resolved run directory name and item id6 (or the sweep lane's review item list, or none), including the malformed `state.json` case being skipped.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract: no lane holding unmerged commits, uncommitted tracked edits, unknown untracked files or an uncollected submission may be removed by anything this plan adds, and every removal goes through `lane_containment.teardown_lane_if_classified` (directly or via `reclaim_lane_through_gate` / `teardown_review_sweep_lane`). Commit only the Scope-Paths through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. This is a shared checkout: verify the staged set with `git diff --cached --name-only` and unstage anything not yours with `git restore --staged <path>`. Do NOT run `aw lanes prune --apply` against this repository during execution; validate `--apply` in scratch repos only, since this checkout's lanes belong to other runs and people. Paste the ACTUAL runner output into each V-item; a summary you did not produce is not evidence. The Scope-Paths are a declaration: a necessary out-of-scope edit is made and justified with `--scope-reason` at finalize. Do not claim done until `aw ipd lint --phase pre-transition` conforms and every V-item carries observed evidence. Under `aw oc run` / `aw agy run` the RUNNER owns the terminal transition, so do not run `aw ipd finalize` yourself; a hand execution runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-edit `- Status:` and never `git mv` into `executed/`.
