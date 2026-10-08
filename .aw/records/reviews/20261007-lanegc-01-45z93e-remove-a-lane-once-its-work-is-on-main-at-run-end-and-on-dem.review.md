# Review findings: plan 45z93e

- Subject-Id: 45z93e
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `5231ca505`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review; after revision
`author` and `review-finalize` both `clean`. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.

Verified anchors: `lane_containment.teardown_review_sweep_lane` (refuses on `probe.uncollected_submission` per
item); `lane_containment.submission_retention` ("NO receipt -> UNCOLLECTED"); `lane_containment.attempt_key`
(`max(len(attempts), 1)`); `lane_containment.teardown_lane_if_classified` ("THE teardown gate (spec R5.5)");
`runner_shared.reclaim_lanes_on_interrupt` (called only from the two hosts' `KeyboardInterrupt` handlers in
`run_queue`); `runner_shared.retire_review_sweep_lane` and its call site directly before `write_report` on both
hosts; `worktree_lease.LaneState.reclaimable`, `_owner_is_live`, `lane_owned_by_other_live_process`;
`runner_shared.classify_lane_integration` ("Do not fork a second lane resolver"); spec `7ckptx` R2.5 and R5.5
(amended 2026-09-18, ignored files disposable), spec in `implementing/`.

Live lane state at review (context only): 13 `aw/lane/*` branches, 6 merged by ancestry; `aw/lane/685iq8` no
longer exists (`git for-each-ref` empty); a detached `.aw-isocommit-*` worktree under `.aw/worktrees/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric A/D; spec `7ckptx` R5.5 | `runner_shared.reclaim_lanes_on_interrupt`: `holds_work` branch calls `worktree_lease.snapshot_lane_dirty_work(..., note=f"Reason: {reason}.")`; final branch calls `worktree_lease.teardown_worktree(repo, handle, force=True)` with no inventory | E-02 reused the interrupt reclaimer unchanged at every run end. It would add a "WIP INTERRUPTED SNAPSHOT" commit to every deliberately preserved dirty lane on every run, and force-remove EMPTY/STALE lanes without the R5.5 inventory, which is blind to an uncollected submission under gitignored `.aw/state/lane-submissions/`. The plan claimed it "removes recovered and empty lanes through the R5.5 gate"; only the recovered case does. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now adds a keyword-only run-end mode: no snapshot, every removal through `reclaim_lane_through_gate`, distinct event names; interrupt behavior unchanged; placement named (after `retire_review_sweep_lane`, before `write_report`); V-02 checks no snapshot and the kept empty lane. |
| PR-002 | HIGH | UNDER-SCOPE | Rubric G/C | `runner_shared.reclaim_lane_through_gate` docstring ("with either missing ... the gate refuses EVERY lane"); E-04 | `aw lanes prune --apply` must call the R5.5 gate, which needs the run dir and owning item, but no item resolved a lane to its run record. As written, prune would refuse every lane, or tempt an executor to bypass the gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-07 resolves lane -> run dir + item via `run_viewer.discover_run_dirs`, `lane_records_including_sweep`, `interrupt_lane_item_record` (sweep lane -> its review items); unresolved -> `keep: no run record`; V-07 added. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric C (one reader) | `runner_shared.classify_lane_integration` ("Do not fork a second lane resolver"); E-03 "commits not on `main` (`git cherry`)" | E-03 specified its own `git cherry` against a literal `main`, a second landing reader, and the target is the checkout `HEAD` (`LANE_INTEGRATION_TARGET_FALLBACK`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 derives every fact from `inspect_lane`, `lane_owned_by_other_live_process` and `classify_lane_integration`; no new git probe. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric A (race) | `worktree_lease.lane_is_safe_to_adopt` (dead owner adoptable); E-04 | Between listing and `--apply`, a new run can adopt a lane. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 re-reads ownership per lane immediately before acting and skips lanes whose run's driver lock is live (`run_viewer.driver_holder_state`). |
| PR-005 | MEDIUM | IN-SCOPE | Spec sync; spec `7ckptx` R2.5 | R2.5 "Absence of a record means NOT collected"; plan "N/A for specs" | E-01 narrows a data-safety rule in an `implementing` spec without amending it. Also it keyed on attempt absence alone; `attempt_key` returns 1 for a zero-attempt item, so a file at that submission root would be discarded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 requires the submission root be absent or empty, puts the rule in the gate (R2.6), and amends R2.5 with `aw specs note`; spec added to Scope-Paths. |
| PR-006 | MEDIUM | IN-SCOPE | Rubric D/E | spec `7ckptx` R5.5 amended 2026-09-18 ("Gitignored files ... do not block teardown"); E-06 "a lane with an ignored-but-unaccounted file is kept" | E-06 demanded a test asserting behavior the spec removed; it would fail against correct code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now tests an unaccounted UNTRACKED file kept and an ignored `.pyc` removed. |
| PR-007 | LOW | IN-SCOPE | Rubric A | `git worktree list`: `.aw/worktrees/.aw-isocommit-*` detached | E-03 enumerated every `.aw/worktrees/*` worktree as a lane. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Non-`aw/lane/*` worktrees are `other: not a lane` and never removal candidates. |
| PR-008 | LOW | IN-SCOPE | Live-artifact convention | F-04 `aw/lane/685iq8` | The cited broken ref no longer exists; V-03 could not show it on this repo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 annotated; broken case tested on a constructed ref; F-07 records the live population as context only. |
| PR-009 | LOW | UNDER-SCOPE | Rubric G (execution contract, evidence) | Gate (one line); V-01..V-06 | Gate lacked the no-loss invariant, staged-set check, scope fence as declaration, finalize ownership, and a ban on running `--apply` against this shared checkout; V-items were thin; E-06 omitted E-01/E-04 dependencies. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full contract added; each V-item names concrete outputs; E-06 depends on E-01, E-02, E-04, E-05, E-07; surface conformance modules named. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Reuse the interrupt reclaimer at run end unchanged? | No; add a run-end mode with no snapshot and gate-only removal. | Reuse unchanged (plan text). REJECTED: snapshots preserved lanes, bypasses R5.5 for empty lanes. Change the interrupt path too. REJECTED: Scope excludes it. | `reclaim_lanes_on_interrupt` body | yes |
| D-2 | How does prune get run context for the gate? | Resolve each lane from run records (E-07); unresolved lanes are kept. | Call the gate with `item=None`. REJECTED: refuses everything. Bypass the gate for merged lanes. REJECTED: AGENTS/spec one-gate rule. | `reclaim_lane_through_gate` docstring; `teardown_lane_if_classified` | yes |
| D-3 | Which reader answers "landed"? | `classify_lane_integration`. | `git cherry main`. REJECTED: second resolver, wrong target name. | `classify_lane_integration` docstring | yes |
| D-4 | When is a never-ran item exempt from R2.5? | Zero attempts in the lane AND empty submission root; amend R2.5. | Status label alone. REJECTED: fails open on a file at attempt-1's root. | `attempt_key`; spec R2.5 | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
