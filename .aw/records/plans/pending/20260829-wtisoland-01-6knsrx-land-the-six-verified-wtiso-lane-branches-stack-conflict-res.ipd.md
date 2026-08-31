# IPD: Land the six verified wtiso lane branches: stack conflict resolution and receipt re-issue

- Date: 2026-08-29
- Kind: child
- Concern: Six verified `wtiso` phases are committed ONLY on unmerged lane branches; landing them requires resolving a semantic conflict with `451739c` and re-issuing begin receipts, neither of which the stranded run can do for itself.
- Scope: Integrate the verified `wtiso` lane branches into `main` and finalize their plans, by (a) resolving the `Statusline`-vs-`TurnBounds` collision in both drivers' turn loops, (b) re-issuing begin receipts so `finalize` stops refusing on a schema-v1 digest, and (c) driving each plan to its terminal lifecycle state. Does NOT change the design of any `wtiso` phase.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, .aw/records/plans/pending, .aw/records/plans/executed, .aw/records/plans/INDEX.json, .aw/records/plans/INDEX.md
- Item-Dependencies: none
- Status: approved
- Blocks-Release: next
- Set: wtisoland
- Order: 1
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 6knsrx
- Approval: 2026-08-31, recorded via aw ipd set: status set to approved
- From-Backlog: xmqv5l

## Workflow history
- 2026-08-31 approved (aw set): status set to approved
- 2026-08-31 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001..PR-011
- 2026-08-30 to-review (aw set): status set to to-review
- 2026-08-30 to-review (aw set): status set to to-review

- 2026-08-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 authored (opencode/its_direct/pt3-claude-opus-5-1m-us): wrote the plan from a live
  verification pass over run `run-20260829T191652Z-4134000`'s six preserved lanes; corrected three
  claims inherited from the session handoff (see Findings F-2, F-4, F-5).

## Goal

Land the **26** unique commits of verified `wtiso` work that are currently reachable only from the
five unmerged `aw/lane/*` branches forming the phase 1-5 stack (phase 6 `1o4eif` already landed as
`b08de37d`), and drive the six corresponding plans to a terminal lifecycle state, so the `wtiso` Set
can close and orchestrator `bl9q3d` stops being blocked on its children.

The commit figure is stated as 26, not the "~79" this plan originally claimed: per-lane counts are
CUMULATIVE along a linear stack (F-2), so summing them double-counts the same commits. 26 is
`git rev-list --count main..aw/lane/2c122z`, the stack tip, which contains all five phases.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: resolve the semantic conflict and land the stack

- [ ] E-01 RE-ESTABLISH THE FACTUAL BASIS BEFORE TOUCHING ANYTHING, because main moved 136 commits
  since this plan was written and that falsified F-7 and F-10 (see the BASIS-COMMIT WARNING). Run
  `git merge-tree --write-tree --name-only main aw/lane/2c122z` (a pure tree operation: it never
  touches main or any worktree, which is why it is used here instead of the scratch-worktree merge
  F-11 warns about), and from its output record: the exact conflicting path set, the per-path hunk
  count (`git show <tree>:<path> | grep -c '^<<<<<<<'`), and which conflicting paths fall OUTSIDE this
  plan's `Scope-Paths` (F-13). If the surface differs from F-7's re-verified 6 paths / 26 hunks, STOP
  and report rather than proceeding on a stale map.
  - Depends on: none
  - Expected outcome: a pasted, current conflict inventory, and an explicit go/no-go against F-7.
  - Execution state: pending
- [ ] E-02 Resolve the `oc_runipd.py` turn-loop hunk (the `run_opencode` conflict, 166 main-side vs 25
  lane-side lines) by COMBINING, not choosing. Keep main's `Statusline` and its unconditional
  `statusline.touch("stdout")` (a progress DISPLAY must refresh on every line) AND main's `poller` /
  `force_watch` / checkpoint machinery, which the lane never saw; add the lane's `bounds` to the
  context managers; and gate ONLY `watchdog.touch()` + `bounds.note_progress()` behind
  `is_meaningful_event(line)`, preserving the lane's permission-deadline call and its
  `if bounds.check_now(): break`. Rationale is F-9. Do NOT reintroduce the lane's `Heartbeat`: neither
  side defines it locally any more; both import from `render_stream` (`oc_runipd.py:57`). The background-poller question is RESOLVED (OQ-03): do NOT gate the poller;
  leave `stall_progress` and the poller callback untouched. Its own `classify_progress` filter already
  enforces the same policy on a different data source.
  - Depends on: E-01
  - Expected outcome: the `run_opencode` hunk is resolved with all four mechanisms (statusline,
    watchdog+gating, bounds, poller/force-stop) intact, and `watchdog.touch()` inside the stream loop
    is reachable only under `is_meaningful_event`.
  - Execution state: pending
- [ ] E-03 Resolve the OTHER EIGHT `oc_runipd.py` hunks, which F-7 as originally written did not know
  existed and which are NOT turn-loop shaped. They are, with their enclosing functions:
  `utc_now`/`self_pinned_env` (L480), `allocate_isolation_worktree` (L943 and L969, the latter 391
  main-side lines against 12), `run_lock` (L2422: main's `RunLockHandle` vs the lane's cross-platform
  `platform_lock.exclusive_file_lock`), `build_prompt` (L3890), `terminate_process` (L4091: shared
  reaper vs `platform_lock._kill_process_tree`), `reconcile_disposition` (L5181), and `execute_item`
  (L5587). Each is an independent semantic decision; treat any hunk you cannot resolve from evidence
  as a STOP-and-report, not a guess.
  - Depends on: E-02
  - Expected outcome: `grep -c '^<<<<<<<' agent_workflows/oc_runipd.py` -> 0, with a one-line
    rationale recorded per hunk.
  - Execution state: pending
- [ ] E-04 Resolve all NINE `agy_runipd.py` hunks, mirroring E-02/E-03 where the shape matches
  (`run_agy_turn` L3012 is the turn loop, on `raw_line`; `run_lock` L1450, `terminate_process` L2739,
  `allocate_isolation_worktree` L708/L733, `build_prompt` L2550, `run_checked` L432, `execute_item`
  L3370). Do NOT assume symmetry with `oc_runipd.py`: verify per hunk. Main's `agy_runipd.py` builds a
  `Statusline` at `:2697` and imports `Heartbeat` only as a re-export (`:44`), so the lane's
  `heartbeat = Heartbeat(...)` line must NOT be restored verbatim.
  - Depends on: E-03
  - Expected outcome: `grep -c '^<<<<<<<' agent_workflows/agy_runipd.py` -> 0 and OC/AGY turn-loop
    semantics are in parity.
  - Execution state: pending
- [ ] E-05 Resolve the FOUR out-of-scope conflicting paths, which requires the scope decision in
  OQ-04 first (F-13): `worktree_lease.py` (5 hunks: main's `write_lane_owner`/`OWNERS_SUBDIR` from
  `zwnjp3` vs the lane's durable `EventSink` lane-lifecycle events), `cli.py` (1: `aw doctor
  --check-pypi` vs `--lanes`, additive both ways), `ipd_lifecycle.py` (1: an import block plus the
  lane's worker-role refusal), and `tests/test_wtiso_adversarial.py` (1: the process-tree-kill guard,
  which each side re-pointed at a different seam). Do not begin until OQ-04 is answered.
  - Depends on: E-04
  - Expected outcome: those four paths carry no conflict markers, and this plan's `Scope-Paths`
    lists every path actually edited.
  - Execution state: pending
- [ ] E-06 Regenerate, do not hand-merge, the derived `INDEX` conflicts: take either side to clear the
  conflict, then run `aw index plans` and commit the regenerated `INDEX.json`/`INDEX.md`. Confirm with
  `aw index plans --check`. Note it currently reports `clean`, so a stale report after the merge is
  caused by the merge itself.
  - Depends on: E-05
  - Expected outcome: `aw index plans --check` reports clean.
  - Execution state: pending
- [ ] E-07 VERIFY (do not merge) that phase 6 `1o4eif` is landed: it merged as `b08de37d` before this
  plan ran, so the original "merge the independent clean lane" step is a NO-OP (F-10). Confirm the
  landing and confirm its follow-up corrections `909eb007`/`e5b0f939` are present, then record that
  E-07 required no merge.
  - Depends on: E-06
  - Expected outcome: `git merge-base --is-ancestor aw/lane/1o4eif main` succeeds and
    `git rev-list --count main..aw/lane/1o4eif` is 0, with no new merge commit created.
  - Execution state: pending

### Task group 2: make the lifecycle record match reality

- [ ] E-08 Run the full suite BARE in the PRIMARY checkout on the merged tree and reconcile it against
  the CURRENT baseline `3654 passed, 3 skipped, 4 xfailed` (F-14, not the plan's stale 2874). The stack
  lands `58ha43`'s state relocation and `2c122z`'s cross-platform lock, so a legitimate delta is
  expected; every delta must be explained against a NAMED lane change. Any unexplained failure is a
  STOP, not a wave-through. Do this BEFORE any lifecycle transition, so no plan is marked executed on
  a red tree.
  - Depends on: E-07
  - Expected outcome: pasted bare-run output whose counts are either at baseline or explained
    change-by-change.
  - Execution state: pending
- [ ] E-09 Finalize the FIVE plans that are still `pending/` (`qcqhj7`, `rchpms`, `58ha43`, `2c122z`,
  `1o4eif`), re-running `aw ipd begin` against CURRENT content immediately before each `aw ipd
  finalize` because the stored schema-v1 receipts cannot be rescued by the frozen-region rule (F-4);
  `1o4eif`'s receipt is additionally and genuinely STALE (F-3). Do NOT finalize `7p9n2v`: the merge
  brings it in already at `executed/` (F-5), so reconcile its location and its missing main-side
  receipt instead. Run every verb from the PRIMARY checkout so state does not fork into a worktree
  again (F-6).
  - Depends on: E-08
  - Expected outcome: all six phase plans are in `.aw/records/plans/executed/` with
    `- Status: executed`, `7p9n2v` having arrived by merge rather than by a second finalize.
  - Execution state: pending
- [ ] E-10 Drive orchestrator `bl9q3d` to its terminal state once its children are `executed`. Note
  its own E-01 is a whole-Set verification against 15 numbered completion criteria and it currently
  reads `- Status: approved` in `pending/` (F-12), so this is a real verification pass, not a status
  flip. `dependency-blocked` is a RUNNER item state, not a plan `Status:`, so verify the claim in
  whichever surface actually carries it before asserting it changed.
  - Depends on: E-09
  - Expected outcome: `bl9q3d`'s whole-Set verification is performed and recorded, and no runner item
    for it remains `dependency-blocked`.
  - Execution state: pending
- [ ] E-11 ONLY after E-09 and E-10 are verified, release the five still-unmerged lane worktrees and
  branches, plus `1o4eif`'s now-redundant worktree. Until then nothing may prune `.aw/worktrees/`:
  teardown DESTROYS lane-side state (`dh0uno`) and the stack's **26** unique commits (F-1, not "~79",
  which double-counted a cumulative chain) are reachable only from those branches. Do not touch the
  nine unrelated lane worktrees belonging to other Sets.
  - Depends on: E-10
  - Expected outcome: `git worktree list` no longer lists the six `wtiso` lanes, every lane commit is
    an ancestor of `main`, and no non-`wtiso` worktree was removed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Integration has a designed seam and MUST be reused rather than hand-merged where possible:
  `oc_runipd.integrate_lane_branch` (`oc_runipd.py:576`) runs a dirty-tree guard, then
  `orchestrate_isolation.execute_merge_and_revalidate_gate`, then `merge --ff-only` with a controlled
  `--no-ff` fallback, and aborts on real conflict so main stays clean (`oc_runipd.py:637-661`).
- That seam explicitly does NOT resolve conflicts: "conflict DETECTION is the gate's job; conflict
  RESOLUTION is a human/serial ordering" (`oc_runipd.py:587-588`). E-01 below is that human ordering.
- The suite runs parallel by default; `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow'"`.
  Run it BARE. Do not pass `-n0`, a second `-q`, or `-p no:randomly`.
- Plan `INDEX.json`/`INDEX.md` are DERIVED (`aw index plans`), so their conflicts are regenerated, never
  hand-merged. `aw index plans --check` currently already reports both stale.

## Findings

**BASIS-COMMIT WARNING (read before executing anything below).** Rows F-1 through F-12 were
originally verified at HEAD `2b10ae7`. Main has since advanced **136 commits** to `144f3347`
(`git rev-list --count 2b10ae7..HEAD` -> `136`), and that invalidated a large part of this plan's
factual basis. Every row is now annotated with a RE-VERIFIED-AT-`144f3347` result: `HOLDS`,
`CORRECTED`, or `FALSIFIED`. Treat only the re-verified text as authoritative. The single most
important change is F-7/F-10: the conflict surface grew from 4 paths to 6, and from 3 code hunks
to **26**, while lane `1o4eif` LANDED on its own. Re-verify again immediately before executing,
because main is under active concurrent development and will move again.

**RE-MEASURED AGAIN 2026-08-31 at HEAD `cbe144fd`, and the surface GREW A SECOND TIME.** A peer
agent flagged the decay (comms fyi `20260831-0126-01`) and the orchestrator verified it
independently with a throwaway worktree probe. The conflict set merging `aw/lane/2c122z` is now
**7 paths**, not the 6 recorded above:

    .aw/records/plans/INDEX.md
    agent_workflows/agy_runipd.py
    agent_workflows/cli.py
    agent_workflows/ipd_lifecycle.py
    agent_workflows/oc_runipd.py
    agent_workflows/worktree_lease.py
    tests/test_wtiso_adversarial.py

Newly conflicting since the `144f3347` re-verification: `ipd_lifecycle.py`, `cli.py`,
`worktree_lease.py`, `tests/test_wtiso_adversarial.py`. Cause: the orchestrator landed nine lane
branches into main on 2026-08-30/31 (`j4v6ga`, `z2isfg`, `zwnjp3`, the five-plan `runstop` chain,
`8guhs0`) plus `ntf6sx`, several of which touch exactly these files. `worktree_lease.py` is new to
the set because `zwnjp3` rewrote lane allocation there.

CONSEQUENCE FOR THIS PLAN: E-01's stop condition is now KNOWN to trigger. It says "if the surface
differs from F-7's re-verified 6 paths / 26 hunks, STOP and report rather than proceeding on a stale
map" - and it does differ. So this plan must be RE-SCOPED before execution, not merely re-verified:
its `Scope-Paths` and its E-02/E-03 hunk-by-hunk instructions name only the two runner modules, so
four of the seven conflicting paths fall outside its declared fence. That is exactly the F-13
condition it warns about.

Nothing here changes the plan's underlying DIAGNOSIS, which was re-checked and still holds:
`frozen_region_digest` is absent from `ipd_lifecycle.py` and `TurnBounds` is absent from
`oc_runipd.py`. Phases 1-5 remain a linear stack, so merging `2c122z` brings all five; `1o4eif` has
since landed independently, leaving five stranded lanes rather than six.

| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **CORRECTED.** FIVE lanes (not six) are preserved and unmerged; `1o4eif` has LANDED. Re-verified at `144f3347`: `git rev-list --count main..aw/lane/<id6>` gives qcqhj7 3, rchpms 10, 7p9n2v 16, 58ha43 22, 2c122z 26, **1o4eif 0**. Also **the "~79 commits" figure in the Goal/E-07 is wrong**: those counts are CUMULATIVE over a linear stack (F-2), so summing them double-counts. The true unique unmerged total is **26** (`git rev-list --count main..aw/lane/2c122z`), which is the whole stack. | `git worktree list` still shows all six dirs; `git merge-base --is-ancestor aw/lane/1o4eif main` now SUCCEEDS. |
| F-2 | **HOLDS.** Phases 1-5 are a LINEAR STACK, not six independent merges. Merging `aw/lane/2c122z` brings qcqhj7+rchpms+7p9n2v+58ha43 with it. Only `1o4eif` was independent (and it has now landed, F-1). | Re-verified at `144f3347`: `git merge-base --is-ancestor` is true for every pair in the chain qcqhj7 -> rchpms -> 7p9n2v -> 58ha43 -> 2c122z; each lane's base commit is a `chore(...): base lane on prerequisite lane <prev>` (`b671192`, `d97220c`, `5c094af`, `d756cbe`). |
| F-3 | **HOLDS for four of five, CORRECTED for `1o4eif`.** Re-verified at `144f3347` by recomputing `ipd_lifecycle.plan_content_digest` against each receipt's own `plan_path`: qcqhj7 `match`, rchpms `match`, 58ha43 `match`, 2c122z `match`, **1o4eif `STALE`**. `1o4eif`'s receipt genuinely no longer matches its plan, because `e5b0f939` edited that plan after `begin` froze it. So it needs a fresh `begin` for a REAL reason, not a spurious one. | `python3 -c` loop over `.aw/state/ipd-lifecycle/<id6>.receipt.json` comparing `plan_content_digest(Path(r['plan_path']).read_text())` to the stored digest. |
| F-4 | **HOLDS.** Landing the `rchpms` fix does NOT by itself let finalize replay. `receipt_is_current` on the lane deliberately falls back to the OLD whole-file rule when `frozen_region_digest` is absent, and all five stored receipts are `schema_version: 1` without that field. So they stay refused; fresh receipts are needed either way. | Re-verified at `144f3347`: `git show aw/lane/rchpms:agent_workflows/ipd_lifecycle.py` lines 714-719 (`if stored_frozen is None: return receipt.get("plan_content_digest") == plan_content_digest(plan_text)`); all five receipts report `schema_version 1` and lack the key. Main's own `receipt_is_current` is still the unconditional whole-file rule (no `frozen_region_digest` anywhere: `grep -c frozen_region_digest agent_workflows/ipd_lifecycle.py` -> 0). |
| F-5 | **HOLDS.** `7p9n2v` DID finalize successfully, lane-side, by re-running `begin` after its evidence commit. It is not a victim of a missing receipt; its receipt is simply absent from MAIN's state dir. Consequence for E-05: merging the stack will bring `7p9n2v`'s plan in ALREADY at `executed/`, so finalizing it again would be wrong. | Re-verified at `144f3347`: `c3b3fe5 lifecycle(7p9n2v): finalize 7p9n2v -> executed`; `git ls-tree aw/lane/7p9n2v .aw/records/plans/executed/` lists the `7p9n2v` plan and `.../pending/` does not; `ls .aw/state/ipd-lifecycle/7p9n2v.receipt.json` -> No such file. |
| F-6 | **HOLDS.** Lifecycle state forks into lanes: receipts exist at `.aw/worktrees/<id6>/.aw/state/ipd-lifecycle/<id6>.receipt.json` for five lanes while MAIN's dir has no `7p9n2v` receipt. This is backlog `dh0uno`, and `58ha43`/`7p9n2v` are the fix. | Re-verified at `144f3347`: `ls .aw/worktrees/*/.aw/state/ipd-lifecycle/*.receipt.json` -> exactly 5 (1o4eif, 2c122z, 58ha43, qcqhj7, rchpms); `ls .aw/state/ipd-lifecycle/7p9n2v.receipt.json` -> No such file. |
| F-7 | **FALSIFIED AS SCOPED; the conflict surface grew by ~8x.** The stack still does not merge cleanly, but at `144f3347` the conflict is in **6 paths with 26 code hunks**, not 4 paths with 3: `oc_runipd.py` **9 hunks**, `agy_runipd.py` **9 hunks**, `worktree_lease.py` **5 hunks**, `cli.py` 1, `ipd_lifecycle.py` 1, `tests/test_wtiso_adversarial.py` 1, plus `INDEX.md`. THREE of the conflicting paths (`cli.py`, `ipd_lifecycle.py`, `worktree_lease.py`, `tests/test_wtiso_adversarial.py`) are NOT in `Scope-Paths`, so this plan as written cannot legally resolve them. Total merge surface is **55 files, +16902/-837**. | `git merge-tree --write-tree --name-only main aw/lane/2c122z` -> tree `80a9557`, exit 1, listing those paths; per-path `git show 80a9557:<path> \| grep -c '^<<<<<<<'` gives the hunk counts. Non-destructive: `merge-tree` never touches the working tree or main. |
| F-8 | **HOLDS in substance, CORRECTED in detail, and it is now only 1 of 26 hunks.** The turn-loop collision is real and semantic, but main's side has grown far beyond `451739c`: the conflicting `run_opencode` hunk is now **166 main-side lines vs 25 lane-side** and carries THREE more subsystems the lane never saw - the `stallfp kaga7s` subagent progress poller, `runstop foi1b3` level-3 checkpoints, and `runstop m0z0ti` level-4 force-stop. So the resolution is not "keep both objects"; it is reconciling four independently-authored progress/liveness mechanisms. | At `144f3347`: `statusline = Statusline(...)` at `oc_runipd.py:3427`, loop `with statusline, watchdog, poller, force_watch:` at `:3527` with unconditional `statusline.touch("stdout")`/`watchdog.touch()` at `:3531-3532`. Lane `2c122z` has `with heartbeat, watchdog, bounds:` at its `:3112`. `grep -c TurnBounds agent_workflows/oc_runipd.py` -> 0. |
| F-9 | **HOLDS, with an important complication.** The lanes' gating is load-bearing: main's `watchdog.touch()` at `oc_runipd.py:3532` is still unconditional per stream line, so display noise from a wedged turn can still reset the no-progress bound. BUT main has since added a SECOND unconditional reset path the lane never saw: the `stallfp kaga7s` poller calls `watchdog.touch()` from a background thread (`oc_runipd.py:3452-3454`) on best-effort log evidence. Gating only the in-loop call therefore does NOT fully close the defect, and whether the poller must also be gated is an unresolved DESIGN question (see OQ-03), not a mechanical merge step. | Lane comment at the conflict site: "this `touch()` was previously UNCONDITIONAL on every line read, so spinner or heartbeat noise from a wedged turn kept resetting the 600s bound indefinitely" (`wtiso-02` E-05(b), mirrored E-06(b) in `agy_runipd.py`). Main's poller: `def _subagent_progress(): watchdog.touch(); statusline.touch("subagent")` at `oc_runipd.py:3452`. |
| F-10 | **FALSIFIED (superseded by events): `1o4eif` ALREADY LANDED, so E-04 is a no-op.** It was merged as `b08de37d "Merge branch 'aw/lane/1o4eif'"` on 2026-08-30, with follow-ups `909eb007` (two fail-OPEN sandbox-probe holes closed) and `e5b0f939` (V-item evidence harvested). Its code is live in main: `host_sandbox_profile.py` exists and `oc_runipd.py:45-51` imports `select_execution_profile`/`enter_sandbox`. E-04 must become a VERIFY-ONLY step, not a merge. | `git merge-base --is-ancestor aw/lane/1o4eif main` -> exit 0; `git rev-list --count main..aw/lane/1o4eif` -> `0`. |
| F-11 | **HOLDS as a caution.** Worktree-relative state makes a scratch worktree an unreliable validation venue, so validate in the PRIMARY checkout. Note this review deliberately used `git merge-tree` (a pure index/tree operation) rather than a scratch-worktree merge, which sidesteps the issue entirely and touches neither main nor any worktree. | Original: detached worktree at `451739c` gave `15 failed, 20 passed` for `tests/test_run_viewer.py` while the primary checkout gave `35 passed`. This is F-6's bug observed from the test side. |
| F-12 | **HOLDS.** All six phase plans plus orchestrator `bl9q3d` are still `- Status: approved` in main's `pending/`; their `executed` transitions live only on the lanes. So no plan needs re-approval, only finalize. | Re-verified at `144f3347`: `grep -m1 '^- Status:' .aw/records/plans/pending/20260828-wtiso-*` -> `approved` for all seven. `.aw/records/plans/executed/` currently holds only `8zgybk` (Phase 0) from this Set. |
| F-13 | **NEW: three of the six conflicting paths are OUTSIDE this plan's `Scope-Paths`,** which declares only `oc_runipd.py`, `agy_runipd.py`, and the plans/INDEX paths. Resolving the merge REQUIRES editing `cli.py`, `ipd_lifecycle.py`, `worktree_lease.py`, and `tests/test_wtiso_adversarial.py`. As written the plan cannot legally complete without breaching its own scope fence, which its gate forbids. | `Scope-Paths` at line 7 of this plan vs the 6 conflicted paths in F-7. |
| F-14 | **NEW: the full suite is green at `144f3347` with a much higher baseline than this plan states.** Actual: `3654 passed, 3 skipped, 4 xfailed in 48.30s` (bare `python3 -m pytest`, exit 0). The plan's stated "beat `2874 passed`" baseline is 780 tests stale, and the two "known live-state deselections" it warns about did not occur. | Pasted run at `144f3347`, bare invocation per AGENTS.md. |
| F-15 | **NEW: `1o4eif`'s landed follow-up work is itself evidence the merge needs real review, not mechanical resolution.** After the merge, `909eb007` had to close "two fail-OPEN holes in the hardened sandbox probe ladder", i.e. landing a verified lane still produced defects requiring correction on main. This is the empirical case for per-phase integration verification (OQ-02) rather than one coarse 55-file merge. | `git log --oneline --all --grep=1o4eif` -> `909eb007 fix(1o4eif): close two fail-OPEN holes in the hardened sandbox probe ladder`, dated after `b08de37d`. |

## Proposed changes (ordered, validatable)

1. Re-measure the conflict surface with `git merge-tree` before acting, since the original survey is
   136 commits stale (F-7, F-10).
2. Resolve the turn-loop collision in both drivers by KEEPING ALL mechanisms: main's `Statusline` as
   the display, main's poller/stop machinery, and the lanes' `TurnBounds` + `is_meaningful_event`
   gating as the liveness bound.
3. Resolve the remaining 24 hunks across the two drivers and the four out-of-scope paths, each as its
   own reasoned decision.
4. Merge the `2c122z` stack (which carries phases 1-5) with those resolutions, verifying in the primary
   checkout, not a scratch worktree. Phase 6 `1o4eif` needs no merge; it already landed.
5. Prove the suite is green against the re-measured baseline BEFORE any lifecycle transition.
6. Re-issue begin receipts and finalize the five still-pending plans, so the lifecycle record matches
   reality; `7p9n2v` arrives already executed and must not be finalized twice.
7. Only then release the lanes.

## Deferred / out of scope (with reason)

- Fixing `dh0uno` (lane-relative state resolution) and `xmqv5l` (whole-file digest). Deferred because
  the fixes ARE the payload of `7p9n2v`/`58ha43` and `rchpms`; this plan lands them rather than
  reimplementing them.
- The 15 worktree-relative `test_run_viewer.py` failures (F-11). Deferred: they are a symptom of the
  same `dh0uno` defect and are expected to change once `58ha43` lands. Filing them separately would
  duplicate work already in flight.
- Redesigning any `wtiso` phase. Out of scope: all six are `Verified: yes` and `approved` (F-12).

## Scope check

- Over-scope: none.
- **Under-scope (UNRESOLVED, see OQ-04): the declared `Scope-Paths` does not cover the real conflict
  surface.** `Scope-Paths` names only the two drivers plus the plans/INDEX paths, but the measured
  merge conflicts in FOUR more tracked paths: `agent_workflows/worktree_lease.py`,
  `agent_workflows/cli.py`, `agent_workflows/ipd_lifecycle.py`, and
  `tests/test_wtiso_adversarial.py` (F-7, F-13). The plan cannot resolve the merge without editing
  them and cannot edit them without breaching its own scope fence. This MUST be settled by OQ-04
  before execution; do not silently broaden the fence at execution time.
- Under-scope: `agent_workflows/render_stream.py` is deliberately excluded. `Statusline` and
  `Heartbeat` are consumed, never modified. If E-02/E-04 turn out to require a `render_stream` change,
  STOP: that is a signal the resolution is redesigning the display, which this plan forbids.

## Required tests / validation

Run the suite BARE in the PRIMARY checkout, never in a scratch worktree (F-11), and never with `-n0`,
a second `-q`, or `-p no:randomly`.

Baseline to beat, MEASURED at `144f3347` during this review (F-14):

```text
3654 passed, 3 skipped, 4 xfailed in 48.30s
```

exit code 0. This REPLACES the plan's original `2874 passed` figure, which was 780 tests stale; the two
"known live-state deselections" it warned about did not occur in the measured run. Because the stack
lands `58ha43`'s state relocation and `2c122z`'s cross-platform lock, the post-merge counts may
legitimately DIFFER; any delta must be explained against a named lane change, not waved through. Re-measure
the baseline immediately before merging, since main is under active concurrent development.

## Spec / documentation sync

N/A: this plan lands already-reviewed phases and changes no public contract of its own. The phases
carry their own doc updates (e.g. `docs/wtiso-state-taxonomy.md` on `58ha43`).

## Open questions

### OQ-01: Is combining Statusline with TurnBounds the resolution the maintainer wants?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER (2026-08-31): KEEP BOTH, exactly as
  E-01/E-02 propose. The statusline refreshes on EVERY line; the watchdog reset becomes CONDITIONAL.
  The ruling covers all FOUR mechanisms named in the corrected F-8 (statusline, watchdog+gating,
  turn bounds, and the poller/force-stop machinery main gained after the lane was authored): all four
  are preserved, none is dropped.
  Why this is a small edit rather than a merge of two designs, verified in main at the time of the
  ruling: the two concerns are ALREADY separate calls to separate objects sitting on adjacent lines
  (`statusline.touch("stdout")` then `watchdog.touch()` in the stream loop; and `watchdog.touch()`
  then `statusline.touch("subagent")` in the poller callback). So "combining" means only that the
  WATCHDOG call is wrapped in the meaningfulness check while the STATUSLINE call stays unconditional.
  A display timer and a liveness bound are two different consumers of one event stream with opposite
  reset requirements, not competing designs.
  Both alternatives remain REJECTED, recorded so they are not silently re-litigated: (a) keep main's
  `Statusline` and DROP the lane's bounds, which reintroduces the wedged-turn defect `wtiso-02`
  E-05(b) fixed; (b) revert `451739cd` to take the lane wholesale, which discards the maintainer's
  newest display work AND would have to re-drop the poller plus both runstop stop-levels that landed
  after the lane.

### OQ-03: Must the background subagent poller also be gated by `is_meaningful_event`?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-003
- Resolution or deferral rationale: RESOLVED (maintainer ruling 2026-08-31, on measured evidence):
  NO. Gate ONLY the in-loop `watchdog.touch()`; leave the `stallfp kaga7s` poller UNCHANGED. The
  review was right to refuse to choose silently, but the premise that the poller resets the watchdog
  on "best-effort log evidence" understates what it already does, and MEASUREMENT narrowed the
  question to nothing:
  (1) the poller ALREADY filters. `stall_progress.classify_progress` counts only
  `PROGRESS_MESSAGE_KINDS` agent-loop lines and explicitly discards housekeeping, documented in-module
  as ensuring a "permission-deadlocked (but still chatty) process is NOT mistaken for a progressing
  one" - which is precisely the wedged-turn property this OQ feared was missing.
  (2) it also counts only lines it has PROVEN belong to a child session of THIS turn (two-hop
  attribution: a `created` announcement naming our parent, then per-line session matching), so
  unrelated log traffic cannot reset our bound.
  (3) applying `is_meaningful_event` to it would be a CATEGORY ERROR: that predicate parses each line
  as a JSON event and returns False on anything unparseable, whereas the poller reads opencode's
  plain-text log. It would reject essentially every poller line and thereby re-break the sub-task
  keepalive the poller exists to provide - the exact `kaga7s` regression this OQ warned about.
  So the two mechanisms already implement the same policy against two different data sources, and the
  correct action is to leave the poller alone rather than to unify them.
  HONEST RESIDUAL RISK, recorded rather than hidden: if a stuck turn's only output is agent-loop-shaped
  log lines from a still-live child, the poller can still hold the turn open. By the poller's own
  definition that child IS progressing, so this is arguably correct behavior; if it ever proves to be a
  real failure mode in practice, it needs its own plan and a log-line-specific notion of progress, NOT
  a reuse of `is_meaningful_event`.

### OQ-04: May this plan edit the four conflicting paths outside its declared `Scope-Paths`?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-004
- Resolution or deferral rationale: F-13 shows resolving the merge REQUIRES editing `worktree_lease.py`,
  `cli.py`, `ipd_lifecycle.py`, and `tests/test_wtiso_adversarial.py`, none of which are in
  `Scope-Paths`, while the plan's own gate forbids touching anything outside it. The plan is therefore
  self-contradictory as written and cannot complete legally. Options: (a) widen `Scope-Paths` to the
  measured conflict set, which is honest but broadens the scope fence to core lifecycle and CLI code;
  or (b) split the out-of-scope resolutions into a separate child IPD. The maintainer must pick, since
  widening a scope fence to `ipd_lifecycle.py` is a real risk decision, not bookkeeping.

### OQ-02: Should the stack land as one merge or be replayed phase by phase?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: PROMOTED TO BLOCKING by review. It was classified non-blocking on
  the belief that the conflict was 3 hunks; F-7's re-verification shows **26 hunks across 6 paths, 55
  files, +16902/-837**. At that size the choice stops being stylistic: one merge means a single commit
  that no reviewer can meaningfully audit, and F-15 is the empirical warning, since even the CLEAN
  `1o4eif` merge still required `909eb007` to close two fail-OPEN holes afterwards. Replaying per phase
  costs resolving propagating conflicts up to five times but yields five auditable integration points
  with a working suite at each. The original recommendation (one merge) is no longer supported by the
  evidence that produced it, and the maintainer must choose before E-02 begins because the answer
  changes the shape of E-02 through E-06.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full `git merge-tree --write-tree --name-only main aw/lane/2c122z`
    output plus the per-path `grep -c '^<<<<<<<'` counts, and state explicitly whether the surface
    matches F-7's 6 paths / 26 hunks. Paste `git status --porcelain` afterwards proving the working
    tree was NOT modified by the inspection.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the resolved `run_opencode` loop source showing ALL FOUR mechanisms
    present (`statusline`, `watchdog`, `bounds`, and `poller`/`force_watch` in the `with` statement),
    with `watchdog.touch()` and `bounds.note_progress()` indented under `if is_meaningful_event(...)`
    while `statusline.touch(...)` remains ungated. Also paste `grep -c 'class Heartbeat'
    agent_workflows/oc_runipd.py` returning 0, and state OQ-03's resolution as applied.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `grep -c '^<<<<<<<' agent_workflows/oc_runipd.py` returning 0, AND a
    per-hunk table naming each of the eight non-turn-loop hunks (`utc_now`, both
    `allocate_isolation_worktree`, `run_lock`, `build_prompt`, `terminate_process`,
    `reconcile_disposition`, `execute_item`) with the side chosen and why. A bare marker count is NOT
    sufficient: it cannot distinguish a reasoned resolution from a discarded side.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `grep -c '^<<<<<<<' agent_workflows/agy_runipd.py` returning 0, the
    resolved `run_agy_turn` loop showing the retained statusline setup and the gated `watchdog.touch()`,
    and proof no stray `heartbeat = Heartbeat(` was reintroduced
    (`grep -n 'heartbeat = Heartbeat' agent_workflows/agy_runipd.py` -> no output).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste OQ-04's recorded answer, `grep -c '^<<<<<<<'` returning 0 for each of
    `worktree_lease.py`, `cli.py`, `ipd_lifecycle.py`, `tests/test_wtiso_adversarial.py`, and this
    plan's updated `- Scope-Paths:` line covering every path actually edited. Also paste
    `python3 -m pytest tests/test_wtiso_adversarial.py tests/test_platform_lock.py` output.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the full output of `aw index plans --check` showing it reports clean.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste `git merge-base --is-ancestor aw/lane/1o4eif main && echo LANDED` printing
    `LANDED`, `git rev-list --count main..aw/lane/1o4eif` printing `0`, and
    `git log --oneline --grep=1o4eif` showing `b08de37d`, `909eb007`, `e5b0f939` already on main.
    Confirm in prose that NO new merge commit was created for this lane.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste the COMPLETE bare `python3 -m pytest` summary line from the PRIMARY
    checkout on the merged tree, with its exit code, and a line-by-line reconciliation against
    `3654 passed, 3 skipped, 4 xfailed`. Every difference must name the lane change that caused it.
    An unexplained failure means `Result: pending`, never a pass.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep -c wtiso` returning 7 (six phases
    plus the already-executed `8zgybk`), `ls .aw/state/ipd-lifecycle/` showing a receipt per phase
    INCLUDING `7p9n2v`, and the `aw ipd begin`/`finalize` output for each of the five finalized plans.
    State explicitly that `7p9n2v` was NOT finalized a second time.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste `aw find plans bl9q3d` showing it in a terminal location, the recorded
    whole-Set verification artifact path required by `bl9q3d`'s own E-01, and `aw attention` output
    showing no `wtiso` item awaiting attention. If `bl9q3d` is deliberately left non-terminal, say so
    and why rather than reporting success.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: for each of the six lanes, paste `git merge-base --is-ancestor aw/lane/<id6>
    main && echo SAFE` succeeding BEFORE any deletion (proving no verified commit is orphaned), then
    `git worktree list` showing the six `wtiso` lanes gone AND the nine unrelated lane worktrees still
    present.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 11 E-leaves in 2 task groups, under the 18-leaf / 5-group thresholds. Stated
  anyway because the COUNT understates the conceptual density: the eleven E-items are one indivisible
  transaction against a single merge:
  resolving 26 conflict hunks, proving the suite green, and moving the lifecycle record are useless
  apart. Splitting them would leave main holding a half-resolved merge or plans marked executed on an
  unverified tree. E-05 is the one candidate for extraction, and OQ-04 asks the maintainer exactly
  that.

This plan is `to-review` and MUST NOT execute until FOUR blocking open questions are resolved by the
maintainer: OQ-01 (combine `Statusline` with `TurnBounds`), OQ-02 (one merge or per-phase replay, now
blocking because the conflict is 8x larger than surveyed), OQ-03 (whether the background poller must
also be gated, since not gating it lands a partial fix), and OQ-04 (whether the scope fence may widen
to the four paths the merge actually requires). The pre-execution gate correctly refuses a plan
carrying an unresolved `Blocking: yes` question.

HONEST STATEMENT OF WHAT THIS PLAN NOW IS. It was written as a mechanical landing of already-verified
work: resolve one semantic collision, merge, finalize. Re-verification at `144f3347` shows that is no
longer what the work is. The conflict is 26 hunks across 6 paths spanning lock primitives, process
reaping, worktree allocation, lifecycle role enforcement, and disposition reconciliation, in 55 files
totaling +16902/-837. Landing it is a substantial integration engineering task with real regression
risk, not bookkeeping, and it should be resourced and reviewed as such.

Execution contract: commit only files this plan changed, path-scoped, and never push. Other agents and
runs are ACTIVE in this shared checkout, so before every commit verify the staged set with
`git diff --cached --name-only` and `git restore --staged` anything not yours. At authoring time an
`aw oc run` on `revgate-04-c621h9` was live and `agent_workflows/engine.py` +
`agent_workflows/attention.py` were dirty from another party; E-01/E-02 touch neither, but the
dirty-tree guard in `integrate_lane_branch` (`oc_runipd.py:606`) WILL refuse integration if a co-worker's
dirty paths overlap the incoming change, so re-check immediately before merging.

Post-gate lifecycle: on completion move this plan to `.aw/records/plans/executed/` with
`- Status: executed`, per the `ipd-lifecycle` workflow, only after every `V-*` above carries pasted
evidence.
