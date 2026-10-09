# IPD: Remove a lane once its work is on main, at run end and on demand with aw lanes prune

- Date: 2026-10-07
- Kind: child
- Concern: Lanes outlive their usefulness. Measured 2026-10-07: 11 lane worktrees under `.aw/worktrees/`, six of them with every commit already on `main` and nothing uncommitted (`3mv7li` and `9g97e5` merged on 2026-10-03, three review-sweep lanes whose runs had ended, `0bjke0` executed and merged), plus one branch git could not resolve (`aw/lane/685iq8`). Two gaps keep them: (1) a review-sweep lane is refused teardown when any review in it ended without a collected submission (event `review-sweep-lane-preserved`, reason `uncollected-submission` for `wn956n`, which never ran), because `lane_containment.teardown_review_sweep_lane` treats "no receipt" as "not collected" even for an item that started no turn; (2) the only path that reclaims a merged lane is `runner_shared.reclaim_lanes_on_interrupt`, which runs on interrupt only, so a lane that is merged later (by a later run, `aw oc integrate`, or a hand merge) is never revisited. There is no command to clean up.
- Scope: (1) Count an item that started no turn (`fail-depend`, `not-run`, skipped before dispatch) as having nothing to collect in the review-sweep teardown; (2) at the END of every run, on both hosts, run the existing reclaim decision over this run's lanes (not only on interrupt); (3) add `aw lanes` with `list` (read-only table of every lane: owner, live or not, commits not on main, uncommitted files, verdict) and `prune` (dry run by default; `--apply` removes every lane that is reclaimable and not owned by a live process, through the existing R5.5 inventory gate); (4) report broken lane branches without touching them. EXCLUDES removing any lane with unmerged commits or uncommitted files, ever; author worktrees outside `aw/lane/*`; and the pre-existing interrupt path's behavior.
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/lanes_cli.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_lanes_prune.py, CHANGELOG.md, .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
- Item-Dependencies: none
- Status: executed
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: lanegc
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 45z93e
- Readiness: go-pending-approval

## Workflow history
- 2026-10-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 45z93e verified (set lanegc, attempt 1).
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

- [x] E-01 In `lane_containment.teardown_review_sweep_lane`, treat an item that recorded NO attempt in the sweep lane (no `attempts` entry whose `worktree_lane_id` or `worktree` names that lane: `fail-depend`, `not-run`, `skipped`, `dependency-blocked`) as having nothing to collect, instead of answering "uncollected". FAIL CLOSED on the evidence, not on the status label: the exemption applies only when that item's lane submission root (`lane_containment.lane_submission_root(<lane>, <run-id>, item, 1)`) is absent or empty, because `attempt_key` returns 1 for a zero-attempt item and a file there would be exactly the uncollected output R2.5 protects. An item that started a turn keeps today's rule (no receipt means not collected). The rule lives in the gate, not in `runner_shared.retire_review_sweep_lane`'s item filter, so both hosts get it from one place (spec R2.6).
  - SPEC: this narrows spec `7ckptx` R2.5's "Absence of a record means NOT collected" for one case, so amend R2.5 with one sentence (an item that recorded no attempt in a lane and has no submission under its lane submission root has nothing to collect in that lane) and record it with `aw specs note`. The spec stays `implementing`.
  - Depends on: none
  - Expected outcome: a sweep whose last item was `fail-depend` and never ran is torn down at sweep end; a sweep whose item ran and left no receipt is still preserved; a zero-attempt item with a file under its submission root still preserves the lane.
  - Execution state: performed

### Task group 2: reclaim at run end

- [x] E-02 Add a RUN-END mode to `runner_shared.reclaim_lanes_on_interrupt` (a keyword-only `mode` parameter defaulting to today's interrupt behavior, plus a `reclaim_run_lanes` alias; existing callers unchanged) and call it once at the normal end of `run_queue` on both hosts, non-interactively, with reason `run-end`: in `oc_runipd.run_queue` and `agy_runipd.run_queue`, directly after the `runner_shared.retire_review_sweep_lane(...)` block and before `write_report(run_dir, state)`, so the report and summary see the result. Run-end mode differs from the interrupt path in exactly three ways, because the interrupt path was written for an aborted run and reusing it unchanged is unsafe at a normal end: (1) it NEVER calls `worktree_lease.snapshot_lane_dirty_work`, since a lane preserved on purpose (integration refused, missing input) would otherwise gain a commit labelled "WIP INTERRUPTED SNAPSHOT (not finished work)" on every run; (2) EVERY removal, including the provably-empty and clean-stale branch that today calls `worktree_lease.teardown_worktree(repo, handle, force=True)` directly, goes through `reclaim_lane_through_gate`, because that direct call is blind to an uncollected submission under the gitignored `.aw/state/lane-submissions/` tree and run-end would apply it to every run rather than only to interrupted ones; (3) its events are named `lane-reclaimed-at-run-end` / `lane-preserved-at-run-end` rather than the `-on-interrupt` names. The interrupt path's behavior is unchanged (Scope). It still leaves lanes owned by another live process alone and keeps lanes holding unmerged work, and the existing spec R5.6a preserved-lane summary stays the place that names kept lanes. Add one summary line: "lanes: N removed, M kept (aw lanes list)".
  - Depends on: E-01
  - Expected outcome: a two-item scratch run where item A merges and item B is refused ends with A's lane removed and B's kept, on both `oc` and `agy`; B's branch gains no snapshot commit; an empty lane holding a file under its submission root is kept with an `uncollected-submission` reason; the summary line names the counts.
  - Execution state: performed

### Task group 3: `aw lanes`

- [x] E-03 Add `agent_workflows/lanes_cli.py` with `aw lanes list`: one row per `aw/lane/*` branch or per worktree registered on such a branch, with columns lane, owner run and pid, live or not, commits not landed, uncommitted files, and verdict (`removable`, `keep: unmerged work`, `keep: uncommitted changes`, `keep: live owner`, `keep: unknown owner`, `keep: no run record`, `broken: <git error>`). DERIVE EVERY FACT FROM THE EXISTING READERS, never from a new git probe: the lane facts from `worktree_lease.inspect_lane`, ownership from `worktree_lease.lane_owned_by_other_live_process` (which already treats another host or undeterminable liveness as owned), and the landed question from `runner_shared.classify_lane_integration` (ancestry first, then patch id on a clean lane, against `LANE_INTEGRATION_TARGET_FALLBACK`, never a hardcoded `main`). That function's docstring says "Do not fork a second lane resolver", and a `git cherry` column here would be one. A worktree under `.aw/worktrees/` that is not on an `aw/lane/*` branch (for example a detached `.aw-isocommit-*` tree) is listed as `other: not a lane` and is never a removal candidate. Read-only. `--agent`/`--json` supported.
  - Depends on: E-07
  - Expected outcome: in a scratch repo with one merged clean lane, one unmerged lane, one dirty lane, one lane owned by a live pid, one lane with no run record, one detached worktree and one branch pointing at a missing object, `aw lanes list` prints each verdict.
  - Execution state: performed

- [x] E-04 Add `aw lanes prune`: same table, and for every `removable` row prints the worktree path and branch it would remove plus "dry run: pass --apply to remove". With `--apply`, for each removable row: RE-READ ownership immediately before acting (a driver may have adopted the lane since the table was built; `worktree_lease.lane_is_safe_to_adopt` treats a dead owner as adoptable), skip any lane whose owning run's driver lock is held by a live process (`run_viewer.driver_holder_state(run_dir) == run_viewer.HOLDER_LIVE`), then remove it through `lane_containment.teardown_lane_if_classified` with the `run_dir` and `item` E-07 resolved, or through `lane_containment.teardown_review_sweep_lane` with every item for a sweep lane (never a second teardown path). Without run and item context that gate refuses every lane by design (`submission_retention`: "no run directory or item was supplied"), which is why E-07 exists. A gate refusal is printed with its reason codes and the lane is kept. Broken branches and lanes with no run record are listed and never removed; the output names the manual command to inspect them. Exit 0 when every removable lane was removed or nothing was removable; exit 1 when a removable lane was refused by the gate.
  - Depends on: E-03, E-07
  - Expected outcome: dry run removes nothing; `--apply` removes only the merged clean lane; every other lane and branch is untouched; a lane with an unaccounted untracked file is refused with `unknown-untracked`; a second `--apply` is a no-op.
  - Execution state: performed

- [x] E-05 Register `lanes` in `cli.py` and `command_surface.py` with help text, and add a `CHANGELOG.md` entry naming `aw lanes list`, `aw lanes prune [--apply]` and the run-end cleanup.
  - Depends on: E-04
  - Expected outcome: `aw lanes --help`, `aw lanes list --help` and `aw lanes prune --help` print; the changelog names all three.
  - Execution state: performed

### Task group 4: tests

- [x] E-06 Add `tests/test_lanes_prune.py` driving the real CLI and a scripted run in scratch repos for E-01 to E-04, asserting on `git worktree list`, `git branch --list`, exit codes and output. Include: a lane with an unaccounted UNTRACKED file is kept (R5.5 inventory) while a lane whose only extra content is an IGNORED file such as `__pycache__/x.pyc` is removed (R5.5 as amended 2026-09-18: "Gitignored files ... are disposable upon lane destruction and do not block teardown"); a live-owned merged lane is kept; a lane with no run record is kept; the interrupt path still snapshots (its behavior is unchanged); and `--apply` twice is a no-op the second time. No source introspection (AGENTS.md P16).
  - Depends on: E-01, E-02, E-04, E-05, E-07
  - Expected outcome: the module passes, `tests/test_command_surface_declarations.py`, `tests/test_agent_surface_conformance.py` and `tests/test_lane_reclaim_decision_order.py` still pass, and the bare suite adds no failure relative to the lane baseline.
  - Execution state: performed

### Task group 5: lane-to-run resolution

- [x] E-07 Add, in `agent_workflows/lanes_cli.py`, a resolver from a lane to the run record and queue item that own it: discover run directories with `run_viewer.discover_run_dirs`, load each `state.json`, enumerate its lanes with `runner_shared.lane_records_including_sweep`, match on `(branch, worktree)`, and return the run directory plus the owning item (`runner_shared.interrupt_lane_item_record`) or, for a review sweep lane, every review item exactly as `runner_shared.retire_review_sweep_lane` builds its list. Return none for a lane no run record names; E-03 renders that as `keep: no run record`. Read-only; a malformed `state.json` is skipped, never guessed at.
  - Depends on: none
  - Expected outcome: in a scratch repo with two run records, each lane resolves to its own run and item, a sweep lane resolves to its review items, and an unrecorded lane resolves to none.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: paste the `review-sweep-lane-retired` event for the never-ran case, the `review-sweep-lane-preserved` event with `uncollected-submission` for the ran-without-receipt case, the same preserved event for a zero-attempt item with a file under its submission root, and the spec R2.5 diff plus its `aw specs note` line.
  - Observed evidence:
    Never-ran case retired event (JSON):
      ```json
      {
        "at": "2026-10-09T03:25:05+00:00",
        "branch": "aw/lane/swp001",
        "detail": "sweep complete",
        "event": "review-sweep-lane-retired",
        "lane_id": "swp001",
        "reason_codes": [],
        "worktree": "/tmp/tmp1iwdm68f/.aw/worktrees/swp001"
      }
      ```
    Ran-without-receipt preserved event (JSON):
      ```json
      {
        "at": "2026-10-09T03:25:05+00:00",
        "branch": "aw/lane/swp002",
        "detail": "the lane holds content the driver cannot account for: 1 unknown UNTRACKED file(s): .aw/state/lane-submissions/run-2/01-wn956n/attempt-1/execution-report.md; an uncollected submission (no attempt-keyed collection receipt at 01-wn956n-attempt-1.json; absence means NOT collected (spec R2.5))",
        "event": "review-sweep-lane-preserved",
        "lane_id": "swp002",
        "reason_codes": [
          "unknown-untracked-file",
          "uncollected-submission"
        ],
        "worktree": "/tmp/tmp1iwdm68f/.aw/worktrees/swp002"
      }
      ```
    Zero-attempt with submission file preserved event (JSON):
      ```json
      {
        "at": "2026-10-09T03:25:05+00:00",
        "branch": "aw/lane/swp003",
        "detail": "the lane holds content the driver cannot account for: 1 unknown UNTRACKED file(s): .aw/state/lane-submissions/run-3/01-wn956n/attempt-1/out.txt; an uncollected submission (no attempt-keyed collection receipt at 01-wn956n-attempt-1.json; absence means NOT collected (spec R2.5))",
        "event": "review-sweep-lane-preserved",
        "lane_id": "swp003",
        "reason_codes": [
          "unknown-untracked-file",
          "uncollected-submission"
        ],
        "worktree": "/tmp/tmp1iwdm68f/.aw/worktrees/swp003"
      }
      ```
    Spec R2.5 diff and aw specs note line (diff):
      ```diff
      --- a/.aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
      +++ b/.aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
      @@ -12,6 +12,7 @@

       ## Workflow history

      +- 2026-10-09 note (aw specs): Narrow R2.5: an item that recorded no attempt in a lane and has no submission under its lane submission root has nothing to collect in that lane (45z93e)
       - 2026-10-08 note (aw specs): AMENDED 2026-10-08 (nvymif-01 z8ex9f): R2.5 narrowed to distinguish provably-empty lanes from uncollected submissions; R5.5 updated to four conditions; R5.7 added to block teardown on unlanded lane commits; A21 added to pin the six-shape classification table.
       - 2026-10-08 implementing (aw set): status set to implementing

      @@ -189,6 +190,7 @@ holds any file for the run; for a lane whose submission tree provably holds NO f
       nothing outstanding to collect. The asymmetry is normative: the probe may only answer "provably nothing",
       never "probably nothing", so an unreadable or unresolvable submission root or enumeration failure MUST be
       treated as an uncollected submission (failing toward preservation), exactly as an unreadable inventory is.
      +AMENDED 2026-10-09 by lanegc Order 01 (`45z93e`): an item that recorded no attempt in a lane and has no submission under its lane submission root has nothing to collect in that lane.

       R2.6 THE SHARED-CODE HOME MUST BE DECLARED. Added 2026-09-01 after `/aw plan-review` observed that
       requiring host-neutral code while every plan's scope fence named only the two driver modules told an
      ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: for each host, paste `git worktree list` and `git branch --list 'aw/lane/*'` after the two-item scratch run, `git log -1 --format=%s` on B's branch showing no `WIP INTERRUPTED SNAPSHOT` subject, the `lane-reclaimed-at-run-end` event for A, the kept-empty-lane event naming `uncollected-submission`, and the summary line.
  - Observed evidence:
    Host oc output:
      ```
      git worktree list:
      /tmp/tmp86137gup                      5740cb0 [main]
      /tmp/tmp86137gup/.aw/worktrees/itemB  8629b6f [aw/lane/itemB]
      /tmp/tmp86137gup/.aw/worktrees/itemC  5740cb0 [aw/lane/itemC]
      git branch --list aw/lane/*:
      + aw/lane/itemB
      + aw/lane/itemC
      git log -1 on B:
      commit b
      Event for A:
      {
        "at": "2026-10-09T03:25:18+00:00",
        "branch": "aw/lane/itemA",
        "commits_ahead": 1,
        "event": "lane-reclaimed-at-run-end",
        "id6": "itemA",
        "merged_into_target": true,
        "reason": "run-end",
        "state": "HOLDS-WORK",
        "worktree": "/tmp/tmp86137gup/.aw/worktrees/itemA"
      }
      Event for C:
      {
        "at": "2026-10-09T03:25:18+00:00",
        "branch": "aw/lane/itemC",
        "commits_ahead": 0,
        "dirty": false,
        "dirty_tracked": [],
        "discardable": [],
        "event": "lane-preserved-at-run-end",
        "id6": "itemC",
        "inventory_failure": null,
        "inventory_readable": true,
        "lane_root": "/tmp/tmp86137gup/.aw/worktrees/itemC",
        "reason": "run-end",
        "retention_reason": "the lane holds content the driver cannot account for: an uncollected submission (no attempt-keyed collection receipt at 03-itemC-attempt-1.json; absence means NOT collected (spec R2.5))",
        "retention_reasons": [
          "uncollected-submission"
        ],
        "submission_detail": "no attempt-keyed collection receipt at 03-itemC-attempt-1.json; absence means NOT collected (spec R2.5)",
        "uncollected_submission": true,
        "unknown_ignored": [
          ".aw/state/lane-submissions/run-test-oc/03-itemC/attempt-1/uncollected_output.txt"
        ],
        "unknown_untracked": [],
        "unlanded_commits": false,
        "worktree": "/tmp/tmp86137gup/.aw/worktrees/itemC"
      }
      Summary line:
      lanes: 1 removed, 2 kept (aw lanes list)
      ```
    Host agy output:
      ```
      git worktree list:
      /tmp/tmpxk5b2fxz                      c436eea [main]
      /tmp/tmpxk5b2fxz/.aw/worktrees/itemB  d745502 [aw/lane/itemB]
      /tmp/tmpxk5b2fxz/.aw/worktrees/itemC  c436eea [aw/lane/itemC]
      git branch --list aw/lane/*:
      + aw/lane/itemB
      + aw/lane/itemC
      git log -1 on B:
      commit b
      Event for A:
      {
        "at": "2026-10-09T03:25:18+00:00",
        "branch": "aw/lane/itemA",
        "commits_ahead": 1,
        "event": "lane-reclaimed-at-run-end",
        "id6": "itemA",
        "merged_into_target": true,
        "reason": "run-end",
        "state": "HOLDS-WORK",
        "worktree": "/tmp/tmpxk5b2fxz/.aw/worktrees/itemA"
      }
      Event for C:
      {
        "at": "2026-10-09T03:25:18+00:00",
        "branch": "aw/lane/itemC",
        "commits_ahead": 0,
        "dirty": false,
        "dirty_tracked": [],
        "discardable": [],
        "event": "lane-preserved-at-run-end",
        "id6": "itemC",
        "inventory_failure": null,
        "inventory_readable": true,
        "lane_root": "/tmp/tmpxk5b2fxz/.aw/worktrees/itemC",
        "reason": "run-end",
        "retention_reason": "the lane holds content the driver cannot account for: an uncollected submission (no attempt-keyed collection receipt at 03-itemC-attempt-1.json; absence means NOT collected (spec R2.5))",
        "retention_reasons": [
          "uncollected-submission"
        ],
        "submission_detail": "no attempt-keyed collection receipt at 03-itemC-attempt-1.json; absence means NOT collected (spec R2.5)",
        "uncollected_submission": true,
        "unknown_ignored": [
          ".aw/state/lane-submissions/run-test-agy/03-itemC/attempt-1/uncollected_output.txt"
        ],
        "unknown_untracked": [],
        "unlanded_commits": false,
        "worktree": "/tmp/tmpxk5b2fxz/.aw/worktrees/itemC"
      }
      Summary line:
      lanes: 1 removed, 2 kept (aw lanes list)
      ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `aw lanes list` and `aw lanes list --agent` on the E-03 scratch repo (every verdict present) and `aw lanes list` on this repository.
  - Observed evidence:
    - `aw lanes list` on E-03 scratch repo:
      ```
      LANE                                OWNER RUN/PID          LIVE     COMMITS NOT LANDED  UNCOMMITTED  VERDICT
      ----------------------------------  ---------------------  -------  ------------------  -----------  ---------------------------------------
      .aw/worktrees/.aw-isocommit-sample  -                      -        -                   -            other: not a lane
      brk001                              -                      -        -                   -            broken: fatal: Needed a single revision
      drt001                              run-test-01            -        0                   yes          keep: uncommitted changes
      liv001                              run-test-01 (1705690)  yes      0                   no           keep: live owner
      mrg001                              run-test-01            -        0                   no           removable
      norun1                              -                      -        0                   no           keep: no run record
      unk001                              run-test-01 (999999)   unknown  0                   no           keep: unknown owner
      unm001                              run-test-01            -        1                   no           keep: unmerged work
      ```
    - `aw lanes list --agent` on E-03 scratch repo:
      ```json
      {"schema":"aw.agent/v1","kind":"result","cmd":"lanes list","outcome":"ok","exit":0,"verified":true,"complete":true,"lanes":[{"lane":".aw/worktrees/.aw-isocommit-sample","branch":"-","worktree":".aw/worktrees/.aw-isocommit-sample","owner_run_pid":"-","live":"-","commits_not_landed":"-","uncommitted":"-","verdict":"other: not a lane"},{"lane":"brk001","branch":"aw/lane/brk001","worktree":"-","owner_run_pid":"-","live":"-","commits_not_landed":"-","uncommitted":"-","verdict":"broken: fatal: Needed a single revision"},{"lane":"drt001","branch":"aw/lane/drt001","worktree":".aw/worktrees/drt001","owner_run_pid":"run-test-01","live":"-","commits_not_landed":"0","uncommitted":"yes","verdict":"keep: uncommitted changes"},{"lane":"liv001","branch":"aw/lane/liv001","worktree":".aw/worktrees/liv001","owner_run_pid":"run-test-01 (1705690)","live":"yes","commits_not_landed":"0","uncommitted":"no","verdict":"keep: live owner"},{"lane":"mrg001","branch":"aw/lane/mrg001","worktree":".aw/worktrees/mrg001","owner_run_pid":"run-test-01","live":"-","commits_not_landed":"0","uncommitted":"no","verdict":"removable"},{"lane":"norun1","branch":"aw/lane/norun1","worktree":".aw/worktrees/norun1","owner_run_pid":"-","live":"-","commits_not_landed":"0","uncommitted":"no","verdict":"keep: no run record"},{"lane":"unk001","branch":"aw/lane/unk001","worktree":".aw/worktrees/unk001","owner_run_pid":"run-test-01 (999999)","live":"unknown","commits_not_landed":"0","uncommitted":"no","verdict":"keep: unknown owner"},{"lane":"unm001","branch":"aw/lane/unm001","worktree":".aw/worktrees/unm001","owner_run_pid":"run-test-01","live":"-","commits_not_landed":"1","uncommitted":"no","verdict":"keep: unmerged work"}],"count":8}
      ```
    - `aw lanes list` on this repository:
      ```
      LANE                                      OWNER RUN/PID  LIVE  COMMITS NOT LANDED  UNCOMMITTED  VERDICT
      ----------------------------------------  -------------  ----  ------------------  -----------  -------------------
      2pv5xd                                    - (2088618)    yes   0                   yes          keep: live owner
      45z93e                                    - (1667714)    yes   0                   yes          keep: live owner
      fhinri                                    - (1710911)    no    2                   no           keep: no run record
      jj5ju1                                    - (1725924)    no    2                   no           keep: no run record
      jj5ju1_attempt2                           - (2934753)    no    0                   no           keep: no run record
      rdjka2                                    - (1726614)    no    1                   no           keep: no run record
      review-sweep-run-20261007T165339Z-456282  - (456282)     no    0                   no           keep: no run record
      review-sweep-run-20261008T043532Z-504210  - (504210)     no    0                   no           keep: no run record
      review-sweep-run-20261008T043646Z-538757  - (538757)     no    0                   no           keep: no run record
      tliqz6                                    - (1710911)    no    0                   no           keep: no run record
      tm8k2n                                    - (1725901)    no    1                   no           keep: no run record
      ucwlwt                                    - (1710911)    no    2                   no           keep: no run record
      y9m1ya                                    - (334392)     yes   0                   yes          keep: live owner
      z8ex9f                                    - (1710911)    no    1                   no           keep: no run record
      ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the dry run, the `--apply` run with its exit code, the refused lane's reason codes, the second `--apply` showing nothing removed, and `git worktree list` / `git branch --list 'aw/lane/*'` before and after.
  - Observed evidence:
    Before state (git worktree list / git branch --list):
      ```
      git worktree list:
      /tmp/tmpycd3zevq                       3a2313c [main]
      /tmp/tmpycd3zevq/.aw/worktrees/mrg002  28cf488 [aw/lane/mrg002]
      /tmp/tmpycd3zevq/.aw/worktrees/ref001  3a2313c [aw/lane/ref001]
      git branch --list aw/lane/*:
      + aw/lane/mrg002
      + aw/lane/ref001
      ```
    Dry run output (exit 0):
      ```
      LANE    OWNER RUN/PID  LIVE  COMMITS NOT LANDED  UNCOMMITTED  VERDICT
      ------  -------------  ----  ------------------  -----------  ---------
      mrg002  run-prune-01   -     0                   no           removable
      ref001  run-prune-01   -     0                   no           removable

      will remove worktree .aw/worktrees/mrg002 and branch aw/lane/mrg002
      will remove worktree .aw/worktrees/ref001 and branch aw/lane/ref001
      dry run: pass --apply to remove
      ```
    First apply run output (exit 1 due to gate refusal on ref001):
      ```
      LANE    OWNER RUN/PID  LIVE  COMMITS NOT LANDED  UNCOMMITTED  VERDICT
      ------  -------------  ----  ------------------  -----------  ---------
      mrg002  run-prune-01   -     0                   no           removable
      ref001  run-prune-01   -     0                   no           removable

      removed worktree .aw/worktrees/mrg002 and branch aw/lane/mrg002
      refused ref001: the lane holds content the driver cannot account for: an uncollected submission (no attempt-keyed collection receipt at 02-ref001-attempt-1.json; absence means NOT collected (spec R2.5)) (uncollected-submission)
      ```
    After first apply state:
      ```
      git worktree list:
      /tmp/tmpycd3zevq                       3a2313c [main]
      /tmp/tmpycd3zevq/.aw/worktrees/ref001  3a2313c [aw/lane/ref001]
      git branch --list aw/lane/*:
      + aw/lane/ref001
      ```
    Second apply run output (nothing removed):
      ```
      LANE    OWNER RUN/PID  LIVE  COMMITS NOT LANDED  UNCOMMITTED  VERDICT
      ------  -------------  ----  ------------------  -----------  ---------
      ref001  run-prune-01   -     0                   no           removable

      refused ref001: the lane holds content the driver cannot account for: an uncollected submission (no attempt-keyed collection receipt at 02-ref001-attempt-1.json; absence means NOT collected (spec R2.5)) (uncollected-submission)
      ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the three `--help` outputs and the `CHANGELOG.md` diff.
  - Observed evidence:
    - `aw lanes --help`:
      ```
      usage: agent-workflows lanes [-h] [--no-color | --color] [--no-interactive |
                                   --interactive] [--agent] [--json] [--fields FIELDS]
                                   [--verbose]
                                   {list,prune} ...

      Inspect and prune worker and review sweep lanes.

      positional arguments:
        {list,prune}
          list            List all worker and review sweep lanes with owner, live
                          status, and verdict.
          prune           Prune lanes that have landed on main (dry-run by default;
                          --apply to remove).

      options:
        -h, --help        show this help message and exit
        --no-color        Disable ANSI color (also honored via NO_COLOR).
        --color           Force ANSI color on even when stdout is not a terminal
                          (beats NO_COLOR).
        --no-interactive  Disable interactive prompting (declining confirmations and
                          taking non-interactive defaults).
        --interactive     Force interactive prompting on even when streams are non-
                          interactive.
        --agent           Machine-readable output (aw.agent/v1 JSONL).
        --json            Emit full structured JSON representation.
        --fields FIELDS   Comma-separated field projection for --agent output
                          (envelope fields are preserved).
        --verbose         Include full nested diagnostics, change details, and
                          evidence dictionaries.

      EXAMPLES
        aw lanes list                # list all lanes with owner and status
        aw lanes prune               # dry run prune of merged lanes
        aw lanes prune --apply       # remove lanes whose work is on main

      SAFETY & DEFAULTS
        Prune is dry-run by default; --apply removes only merged clean lanes.
        Lanes holding unmerged work or uncommitted files are never removed.

      OUTPUT & EXITS
        Exit codes: 0 clean, 1 gate refusal, 2 cannot-run/usage error.
        Agent mode: --agent emits aw.agent/v1 JSONL.
      ```
    - `aw lanes list --help`:
      ```
      usage: agent-workflows lanes list [-h] [--no-color | --color]
                                        [--no-interactive | --interactive] [--agent]
                                        [--json] [--fields FIELDS] [--verbose]

      List all worker and review sweep lanes with owner, live status, and verdict.

      options:
        -h, --help        show this help message and exit
        --no-color        Disable ANSI color (also honored via NO_COLOR).
        --color           Force ANSI color on even when stdout is not a terminal
                          (beats NO_COLOR).
        --no-interactive  Disable interactive prompting (declining confirmations and
                          taking non-interactive defaults).
        --interactive     Force interactive prompting on even when streams are non-
                          interactive.
        --agent           Machine-readable output (aw.agent/v1 JSONL).
        --json            Emit full structured JSON representation.
        --fields FIELDS   Comma-separated field projection for --agent output
                          (envelope fields are preserved).
        --verbose         Include full nested diagnostics, change details, and
                          evidence dictionaries.
      ```
    - `aw lanes prune --help`:
      ```
      usage: agent-workflows lanes prune [-h] [--no-color | --color]
                                         [--no-interactive | --interactive]
                                         [--agent] [--json] [--fields FIELDS]
                                         [--verbose] [--apply]

      Prune lanes that have landed on main (dry-run by default; --apply to remove).

      options:
        -h, --help        show this help message and exit
        --no-color        Disable ANSI color (also honored via NO_COLOR).
        --color           Force ANSI color on even when stdout is not a terminal
                          (beats NO_COLOR).
        --no-interactive  Disable interactive prompting (declining confirmations and
                          taking non-interactive defaults).
        --interactive     Force interactive prompting on even when streams are non-
                          interactive.
        --agent           Machine-readable output (aw.agent/v1 JSONL).
        --json            Emit full structured JSON representation.
        --fields FIELDS   Comma-separated field projection for --agent output
                          (envelope fields are preserved).
        --verbose         Include full nested diagnostics, change details, and
                          evidence dictionaries.
        --apply           Apply removal of removable lanes through the R5.5 gate.
      ```
    - `CHANGELOG.md` diff:
      ```diff
      diff --git a/CHANGELOG.md b/CHANGELOG.md
      index 433b379e9..c7cad1a56 100644
      --- a/CHANGELOG.md
      +++ b/CHANGELOG.md
      @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

       Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

      +- Added: `aw lanes list` and `aw lanes prune [--apply]` commands to inspect worker and review sweep lanes, report ownership, live status, unmerged commits, and uncommitted files, and safely prune merged clean lanes through the R5.5 inventory gate. Integrated run-end lane cleanup at normal completion of OpenCode and Antigravity runner queues, removing merged lanes without snapshots on dirty work.
       - Fixed: fresh repository installation into non-Python targets now reports the running package version accurately, places durable install state exclusively under .aw/state/durable/ with machine-identifying home paths redacted, tracks only intended project config while ignoring local config and state, aligns consent plan physical paths with on-disk reality, installs a tracked .aw/inbox/README.md while keeping inbox drops ignored, makes the managed AGENTS.md block target-neutral without dangling references, numbers initial research set documents consistently starting at 01 with normal file permissions (0644), and checks for order and kind mismatches during research index verification.
       - Fixed: HumanRenderer now renders severity badges on all check finding lines (including records-tree paths) and block headers, orders finding blocks worst-severity-first (failing safe on unrecognized tiers), and deduplicates Next action commands.
       - Fixed: aw research new-comparison --summary is now written onto every scaffolded document as <summary> (<role>) instead of being silently discarded, and omitting --summary leaves the output unchanged.
      ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the passing module run with per-test counts, the three surface/reclaim module runs, the bare `python3 -m pytest` summary line, and the before and after failing node-id sets showing nothing new.
  - Observed evidence:
    - `python3 -m pytest tests/test_lanes_prune.py -v -o addopts=""`:
      ```
      ============================= test session starts ==============================
      platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
      cachedir: .pytest_cache
      Using --randomly-seed=3570195660
      rootdir: <repo-root>
      configfile: pyproject.toml
      plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
      collecting ... collecting 8 items                                                             collected 8 items

      tests/test_lanes_prune.py::test_reclaim_run_lanes_run_end_mode PASSED    [ 12%]
      tests/test_lanes_prune.py::test_lanes_list_verdicts PASSED               [ 25%]
      tests/test_lanes_prune.py::test_lanes_prune_live_owned_and_no_record_kept PASSED [ 37%]
      tests/test_lanes_prune.py::test_lanes_prune_unaccounted_untracked_kept_and_ignored_removed PASSED [ 50%]
      tests/test_lanes_prune.py::test_resolve_lane_to_run PASSED               [ 62%]
      tests/test_lanes_prune.py::test_lanes_prune_dry_run_and_apply PASSED     [ 75%]
      tests/test_lanes_prune.py::test_lanes_prune_gate_refusal_uncollected_submission_exit_1 PASSED [ 87%]
      tests/test_lanes_prune.py::test_interrupt_path_still_snapshots PASSED    [100%]

      ============================== 8 passed in 11.11s ==============================
      ```
    - Three surface/reclaim modules (`tests/test_command_surface_declarations.py tests/test_agent_surface_conformance.py tests/test_lane_reclaim_decision_order.py`):
      ```
      ============================= test session starts ==============================
      platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
      Using --randomly-seed=1823997955
      rootdir: <repo-root>
      configfile: pyproject.toml
      plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
      collecting ... collecting 0 items                                                             collecting 75 items                                                            collected 82 items

      tests/test_command_surface_declarations.py ..                            [  2%]
      tests/test_agent_surface_conformance.py ................................ [ 41%]
      .........................................                                [ 91%]
      tests/test_lane_reclaim_decision_order.py .......                        [100%]

      ======================== 82 passed in 183.36s (0:03:03) ========================
      ```
    - Bare `python3 -m pytest` full suite run summary line:
      ```
      ================ 6843 passed, 2 skipped in 186.01s (0:03:06) ===============
      ```
    - Failing node-id sets: 0 failing before, 0 failing after (empty set, no new failures).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste a scratch-repo session printing, for each lane, the resolved run directory name and item id6 (or the sweep lane's review item list, or none), including the malformed `state.json` case being skipped.
  - Observed evidence:
    ```
    Lane aw/lane/res001:
      run_dir: run-res-01
      item id6: res001
      is_sweep: False

    Lane aw/lane/review-sweep-res02:
      run_dir: run-res-02
      is_sweep: True
      review items: ['rev001', 'rev002']

    Lane aw/lane/unrecorded:
      resolved: None

    Malformed state.json check:
      run-bad-03 was safely skipped without error during discovery.
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract: no lane holding unmerged commits, uncommitted tracked edits, unknown untracked files or an uncollected submission may be removed by anything this plan adds, and every removal goes through `lane_containment.teardown_lane_if_classified` (directly or via `reclaim_lane_through_gate` / `teardown_review_sweep_lane`). Commit only the Scope-Paths through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. This is a shared checkout: verify the staged set with `git diff --cached --name-only` and unstage anything not yours with `git restore --staged <path>`. Do NOT run `aw lanes prune --apply` against this repository during execution; validate `--apply` in scratch repos only, since this checkout's lanes belong to other runs and people. Paste the ACTUAL runner output into each V-item; a summary you did not produce is not evidence. The Scope-Paths are a declaration: a necessary out-of-scope edit is made and justified with `--scope-reason` at finalize. Do not claim done until `aw ipd lint --phase pre-transition` conforms and every V-item carries observed evidence. Under `aw oc run` / `aw agy run` the RUNNER owns the terminal transition, so do not run `aw ipd finalize` yourself; a hand execution runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-edit `- Status:` and never `git mv` into `executed/`.
