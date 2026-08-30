# IPD: Land the six verified wtiso lane branches: stack conflict resolution and receipt re-issue

- Date: 2026-08-29
- Kind: child
- Concern: Six verified `wtiso` phases are committed ONLY on unmerged lane branches; landing them requires resolving a semantic conflict with `451739c` and re-issuing begin receipts, neither of which the stranded run can do for itself.
- Scope: Integrate the verified `wtiso` lane branches into `main` and finalize their plans, by (a) resolving the `Statusline`-vs-`TurnBounds` collision in both drivers' turn loops, (b) re-issuing begin receipts so `finalize` stops refusing on a schema-v1 digest, and (c) driving each plan to its terminal lifecycle state. Does NOT change the design of any `wtiso` phase.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, .aw/records/plans/pending, .aw/records/plans/executed, .aw/records/plans/INDEX.json, .aw/records/plans/INDEX.md
- Item-Dependencies: none
- Status: to-review
- Blocks-Release: next
- Set: wtisoland
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 6knsrx
- From-Backlog: xmqv5l

## Workflow history
- 2026-08-30 to-review (aw set): status set to to-review
- 2026-08-30 to-review (aw set): status set to to-review

- 2026-08-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 authored (opencode/its_direct/pt3-claude-opus-5-1m-us): wrote the plan from a live
  verification pass over run `run-20260829T191652Z-4134000`'s six preserved lanes; corrected three
  claims inherited from the session handoff (see Findings F-2, F-4, F-5).

## Goal

Land ~79 commits of verified `wtiso` work that is currently reachable only from six unmerged
`aw/lane/*` branches, and drive the six corresponding plans to a terminal lifecycle state, so the
`wtiso` Set can close and orchestrator `bl9q3d` stops being `dependency-blocked`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: resolve the semantic conflict and land the stack

- [ ] E-01 Resolve the `oc_runipd.py` turn-loop conflict (F-7, F-8) by COMBINING both changes, not
  choosing one. In the conflicted `with ...:` block, keep main's `Statusline` object and its
  unconditional `statusline.touch()` (a progress DISPLAY must refresh on every line), and add the
  lane's `bounds` to the context managers (`with statusline, watchdog, bounds:`), and gate ONLY
  `watchdog.touch()` + `bounds.note_progress()` behind `is_meaningful_event(line)`, preserving the
  lane's `detect_permission_request` -> `bounds.note_permission_request(...)` call and the
  `if bounds.check_now(): break`. Rationale is F-9: the liveness bound must not be reset by display
  noise, which is exactly the defect `wtiso-02` E-05(b) fixed; the display has the opposite
  requirement. Do NOT reintroduce the lane's `Heartbeat` (main deleted it from `oc_runipd.py`;
  `Statusline` is imported from `render_stream` at `oc_runipd.py:46`).
  - Depends on: none
  - Expected outcome: `oc_runipd.py` has no conflict markers, references `Statusline` (not `Heartbeat`),
    and `watchdog.touch()` is reachable only under `is_meaningful_event`.
  - Execution state: pending
- [ ] E-02 Apply the mirror-image resolution to BOTH `agy_runipd.py` conflict hunks (F-7): the second
  hunk is the same turn-loop shape as E-01 (`raw_line`, `wtiso-02` E-06(b)); the first hunk is main's
  added statusline setup block (`queue`/`total_items`/`current_idx`/`is_tty`/`run_start_mono`), which is
  additive and must be KEPT alongside the lane's `stall_timeout` line. Note `agy_runipd.py:244` still
  defines `Heartbeat` and `:1957` builds a `Statusline`, so verify which object this module's loop
  actually uses after the merge rather than assuming symmetry with `oc_runipd.py`.
  - Depends on: E-01
  - Expected outcome: `agy_runipd.py` has no conflict markers and OC/AGY turn-loop semantics are in
    parity.
  - Execution state: pending
- [ ] E-03 Regenerate, do not hand-merge, the derived `INDEX` conflicts: take either side to clear the
  conflict, then run `aw index plans` and commit the regenerated `INDEX.json`/`INDEX.md`. Confirm with
  `aw index plans --check`.
  - Depends on: E-02
  - Expected outcome: `aw index plans --check` reports no `stale-index` finding.
  - Execution state: pending
- [ ] E-04 Merge `aw/lane/1o4eif` (F-10), the independent clean lane, as its own commit so phase 6 is
  not entangled with the stack resolution.
  - Depends on: E-03
  - Expected outcome: `git merge-base --is-ancestor aw/lane/1o4eif main` succeeds.
  - Execution state: pending

### Task group 2: make the lifecycle record match reality

- [ ] E-05 For each of the six plans, re-run `aw ipd begin` against the CURRENT plan content
  immediately before `aw ipd finalize`, because the stored schema-v1 receipts cannot be rescued by the
  frozen-region rule (F-4). Run both verbs from the PRIMARY checkout so state does not fork into a
  worktree again (F-6). Note `7p9n2v` is already `executed` on its lane (F-5), so reconcile its
  location rather than finalizing it twice.
  - Depends on: E-04
  - Expected outcome: each of the six plans is in `.aw/records/plans/executed/` with
    `- Status: executed`, and `.aw/state/ipd-lifecycle/` holds a receipt for each.
  - Execution state: pending
- [ ] E-06 Re-evaluate orchestrator `bl9q3d`, which is `dependency-blocked` only because its children
  could not reach `executed`; drive it to its terminal state once they have.
  - Depends on: E-05
  - Expected outcome: `bl9q3d` is no longer `dependency-blocked`.
  - Execution state: pending
- [ ] E-07 ONLY after E-05 and E-06 are verified, release the six lane worktrees and branches. Until
  then nothing may prune `.aw/worktrees/`: teardown DESTROYS lane-side state (`dh0uno`) and ~79 commits
  of verified work are reachable only from those branches (F-1).
  - Depends on: E-06
  - Expected outcome: `git worktree list` no longer lists the six `wtiso` lanes, and every lane commit
    is an ancestor of `main`.
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

Every row below was verified in this repo at HEAD `2b10ae7`; the commands are reproducible.

| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | Six lanes are preserved and unmerged, holding all the verified work. | `git worktree list` shows all six `.aw/worktrees/<id6>`; `git rev-list --count main..aw/lane/<id6>` gives qcqhj7 3, rchpms 10, 7p9n2v 16, 58ha43 22, 2c122z 26, 1o4eif 2. |
| F-2 | **Phases 1-5 are a LINEAR STACK, not six independent merges.** Merging `aw/lane/2c122z` brings qcqhj7+rchpms+7p9n2v+58ha43 with it. Only `1o4eif` is independent. | `git merge-base --is-ancestor` is true for every pair in the chain qcqhj7 -> rchpms -> 7p9n2v -> 58ha43 -> 2c122z; each lane's tip commit is a `chore(...): base lane on prerequisite lane <prev>` (`b671192`, `d97220c`, `5c094af`, `d756cbe`). This corrects the handoff, which framed six separate merges. |
| F-3 | The five "stale receipt" refusals were SPURIOUS. Each lane's only plan-file delta against main is execution bookkeeping (`- [ ] E-NN` -> `- [x]`, `Execution state: pending` -> `performed`, evidence/history), never the reviewed contract. | Each receipt's `plan_content_digest` equals sha256 of MAIN's plan bytes for all five. Under `rchpms`'s own `frozen_region_digest`, main and lane agree exactly: qcqhj7 `b76f6848`, rchpms `585f7349`, 58ha43 `22171617`, 2c122z `866c8308`, 1o4eif `0b1dd372`. |
| F-4 | **Landing the `rchpms` fix does NOT by itself let finalize replay.** `receipt_is_current` on the lane deliberately falls back to the OLD whole-file rule when `frozen_region_digest` is absent, and all five stored receipts are `schema_version: 1` without that field. So they stay refused; fresh receipts are needed either way. | `git show aw/lane/rchpms:agent_workflows/ipd_lifecycle.py` lines 714-719 (`if stored_frozen is None: return receipt.get("plan_content_digest") == plan_content_digest(plan_text)`); all five receipts report `schema_version 1` and lack the key. This corrects the handoff's recommended first move. |
| F-5 | **`7p9n2v` DID finalize successfully, lane-side**, by re-running `begin` after its evidence commit. It is not a victim of a missing receipt; its receipt is simply absent from MAIN's state dir. | `c3b3fe5 lifecycle(7p9n2v): finalize 7p9n2v -> executed`, whose message records "begin was re-run after the E/V evidence commit changed the plan digest"; the plan sits at `.aw/records/plans/executed/...7p9n2v...` on that lane. This corrects the handoff's "no begin receipt" framing: the receipt existed, in the lane. |
| F-6 | Lifecycle state forks into lanes: receipts exist at `.aw/worktrees/<id6>/.aw/state/ipd-lifecycle/<id6>.receipt.json` for five lanes while MAIN's dir has no `7p9n2v` receipt. This is backlog `dh0uno`, and `58ha43`/`7p9n2v` are the fix. | `ls .aw/worktrees/*/.aw/state/ipd-lifecycle/*.receipt.json`; `ls .aw/state/ipd-lifecycle/7p9n2v.receipt.json` -> No such file. |
| F-7 | **The stack does NOT merge cleanly into current main.** `git merge --no-ff aw/lane/2c122z` conflicts in `oc_runipd.py` (1 hunk), `agy_runipd.py` (2 hunks), plus both plan `INDEX` files. Main advanced 52 commits past the stack's base, so no fast-forward exists. | Tested in a throwaway detached worktree at `main`; `git diff --name-only --diff-filter=U` listed exactly those four paths. Merge was aborted; main untouched. |
| F-8 | The conflict is SEMANTIC and needs a real decision. Maintainer commit `451739c` ("2-line sticky statusline") replaced the `Heartbeat` progress reporter with `Statusline` in the SAME turn-loop block where the lanes insert `TurnBounds` plus meaningful-event gating. Both changes rewrite the same `with ...:` statement and the same `touch()` calls. | Main `oc_runipd.py:1918` builds `Statusline(...)` and the loop calls `statusline.touch()` unconditionally; lane `2c122z` builds `Heartbeat` at its `:3104` and wraps `with heartbeat, watchdog, bounds:`, gating `watchdog.touch()`/`bounds.note_progress()` behind `is_meaningful_event(line)`. `grep -c TurnBounds` in main `oc_runipd.py` is 0. |
| F-9 | The lanes' change is load-bearing, not cosmetic: the unconditional `touch()` main still has is the defect that let a wedged turn reset its own 600s no-progress bound forever. Dropping the lane side to keep `Statusline` would reintroduce it. | Lane comment at the conflict site: "this `touch()` was previously UNCONDITIONAL on every line read, so spinner or heartbeat noise from a wedged turn kept resetting the 600s bound indefinitely" (`wtiso-02` E-05(b), mirrored `wtiso-02` E-06(b) in `agy_runipd.py`). |
| F-10 | `1o4eif` (phase 6) merges CLEANLY and is independently verifiable: 27/27 of its tests pass on the merged tree. | `git merge --no-ff aw/lane/1o4eif` -> "Merge made by the 'ort' strategy", no unmerged paths, +1952 lines across 4 files; `python3 -m pytest tests/test_host_sandbox_profile.py` -> `27 passed in 2.30s`. |
| F-11 | A scratch worktree at main fails 15 `test_run_viewer.py` tests that PASS in the primary checkout, so those failures are worktree-relative-state artifacts, NOT a main regression and NOT lane-caused. Validation of any merge must therefore run in the primary checkout. | Detached worktree at `451739c`, clean tree: `15 failed, 20 passed`. Same file in the primary checkout: `35 passed in 7.29s`. This is F-6's bug observed from the test side. |
| F-12 | All six plans are still `- Status: approved` in main; their `executed` transitions live only on the lanes. So no plan needs re-approval, only finalize. | `grep -m1 '^- Status:' .aw/records/plans/pending/20260828-wtiso-*` -> `approved` for all seven (including orchestrator `bl9q3d`). |

## Proposed changes (ordered, validatable)

1. Resolve the turn-loop collision in both drivers by KEEPING BOTH: main's `Statusline` as the progress
   reporter, and the lanes' `TurnBounds` + `is_meaningful_event` gating as the liveness bound.
2. Merge the `2c122z` stack (which carries phases 1-5) with that resolution, verifying in the primary
   checkout, not a scratch worktree.
3. Merge the independent `1o4eif` lane.
4. Re-issue begin receipts and finalize each plan, so the lifecycle record matches reality.
5. Only then release the lanes.

## Deferred / out of scope (with reason)

- Fixing `dh0uno` (lane-relative state resolution) and `xmqv5l` (whole-file digest). Deferred because
  the fixes ARE the payload of `7p9n2v`/`58ha43` and `rchpms`; this plan lands them rather than
  reimplementing them.
- The 15 worktree-relative `test_run_viewer.py` failures (F-11). Deferred: they are a symptom of the
  same `dh0uno` defect and are expected to change once `58ha43` lands. Filing them separately would
  duplicate work already in flight.
- Redesigning any `wtiso` phase. Out of scope: all six are `Verified: yes` and `approved` (F-12).

## Scope check

- Over-scope: none. The two driver files are the conflict surface (F-7); the plan/INDEX paths are the
  lifecycle surface (E-03, E-05).
- Under-scope: `agent_workflows/render_stream.py` is deliberately excluded. `Statusline` is consumed,
  never modified. If E-01/E-02 turn out to require a `render_stream` change, STOP: that is a signal the
  resolution is redesigning the display, which this plan forbids.

## Required tests / validation

Run the suite BARE in the PRIMARY checkout, never in a scratch worktree (F-11), and never with `-n0`
or `-p no:randomly`. Baseline to beat: `2874 passed, 3 skipped, 4 xfailed` with two known live-state
deselections (`test_run_viewer_cli_issues_flag`, `test_todo_matches_attention`, owned by `i79rgh`).
Because the stack lands `58ha43`'s state relocation, the post-merge baseline may legitimately DIFFER;
any delta must be explained against a named lane change, not waved through.

## Spec / documentation sync

N/A: this plan lands already-reviewed phases and changes no public contract of its own. The phases
carry their own doc updates (e.g. `docs/wtiso-state-taxonomy.md` on `58ha43`).

## Open questions

### OQ-01: Is combining Statusline with TurnBounds the resolution the maintainer wants?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: E-01/E-02 propose keeping BOTH sides, justified by F-9 (the
  liveness bound and the display have opposite reset requirements). This is a design call in the
  maintainer's own most recent commit (`451739c`), so it needs their ruling before execution. The two
  rejected alternatives, recorded so they are not silently re-litigated: (a) keep main's `Statusline`
  and DROP the lane's bounds, which reintroduces the wedged-turn defect `wtiso-02` E-05(b) fixed;
  (b) revert `451739c` to take the lane wholesale, which discards the maintainer's newest work.

### OQ-02: Should the stack land as one merge or be replayed phase by phase?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: F-2 means merging `2c122z` lands phases 1-5 in a single commit,
  which is simplest and preserves lane history, but yields one coarse integration point. Replaying each
  lane separately would give five reviewable merges at the cost of resolving the same conflict up to
  five times as it propagates. Recommendation: one merge, since the phases were authored and verified as
  a stack. Not blocking because either choice satisfies E-01 through E-07.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n 'with statusline, watchdog, bounds:' agent_workflows/oc_runipd.py`
    returning a line, plus `grep -c 'class Heartbeat' agent_workflows/oc_runipd.py` returning 0, plus
    the pasted post-merge source of the loop body showing `watchdog.touch()` indented under
    `if is_meaningful_event(line):`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `grep -c '^<<<<<<<' agent_workflows/agy_runipd.py` returning 0 and the
    pasted turn-loop block showing both the retained statusline setup and the gated `watchdog.touch()`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the full output of `aw index plans --check` showing no `stale-index` line.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `git merge-base --is-ancestor aw/lane/1o4eif main && echo LANDED` printing
    `LANDED`, and `python3 -m pytest tests/test_host_sandbox_profile.py` output showing 27 passed.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep -c wtiso` returning 7 (six phases
    plus the already-executed `8zgybk`), and `ls .aw/state/ipd-lifecycle/` showing a receipt per phase.
    Also paste the BARE full-suite output with its pass/fail counts, explaining any delta from the
    `2874 passed` baseline against a named lane change.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `aw attention` (or `aw find plans bl9q3d`) output showing `bl9q3d` is no
    longer `dependency-blocked`.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste `git worktree list` showing no `.aw/worktrees/<id6>` entry for the six
    lanes, AND, for each of the six, `git merge-base --is-ancestor aw/lane/<id6> main` succeeding BEFORE
    any branch deletion, proving no verified commit was orphaned.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and MUST NOT execute until OQ-01 is resolved by the maintainer: the blocking
open question is a design call inside the maintainer's own `451739c`, and the pre-execution gate
correctly refuses a plan carrying an unresolved `Blocking: yes` question.

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
