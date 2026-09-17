# IPD: Stop a dirty main tree from blocking a run, and let git be the authority on a merge

- Date: 2026-09-13
- Kind: orchestrator
- Concern: Four consecutive IPD batch runs on 2026-09-13 failed heavily, each for the same structural reason: one item's own bookkeeping left the shared checkout dirty, and a whole-tree gate then refused every remaining item. RE-MEASURED AT REVIEW from each run's `state.json` rather than trusted: 68 refusals across three runs (27 of 42, 23 of 41, 18 of 43), every one naming a single uncommitted backlog markdown file, plus 36 cascaded `dependency-blocked`; two verified lanes stranded; ~$131 of agent cost across the four runs producing four executed plans. NOT a 100% failure rate: each of the three large runs did execute at least one item and complete several reviews, so the honest claim is "the majority of every run was lost", which is damning enough without overstating.
- Scope: Stop the runner blocking work it will not touch, and stop it writing to the shared checkout mid-run. SIX children: the pre-launch refusal (isolated path only), the integration-refusal reclassification, the backlog close, orchestrator retirement, review isolation, and the failed-retirement index residue. Excludes the merge-and-revalidate suite run, which is the check that does real work and is deliberately KEPT. Excludes DELETING either dirty-tree guard, per OQ-02's resolution.
  THE COLLISION WITH THREE APPROVED RELEASE-BLOCKING PLANS IS RESOLVED AND DISSOLVED, NOT PENDING. Round 1 of review found that `fujm0y`, `51vw4y` and `3i0aaz` (each `Status: approved`, `Blocks-Release: next`) were signed off to widen, preserve, or extend exactly what Orders 01 and 02 then proposed to delete. OQ-02 was resolved to answer (c) and BOTH children were revised accordingly: Order 01 now removes the refusal for the ISOLATED path only and its spec amendment PRESERVES R5.4's obligation for the shared-tree path that `3i0aaz` E-03 extends; Order 02 now KEEPS `dirty_tree_overlap` and reduces to reclassifying a git local-changes refusal from `merge-conflict` to `integration-blocked`. VERIFIED AT REVIEW ROUND 2 by re-reading both children: Order 02's E-01/E-04/E-05 are WITHDRAWN and its surviving items are E-02/E-03 only. So NO approved plan is contradicted, NO release blocker is negated, and Orders 01 and 02 are no longer gated on anything. Read "Collisions with approved work" below as the RECORD of a resolved conflict, not as a live warning.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, agent_workflows/ipd_lifecycle.py, tests/test_lane_clean_base.py, tests/test_runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_orchestrator_retirement.py, .aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: dirtygates
- Order: 0
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 8lfoum
- Priority: high
- Work-Kind: bug

## Workflow history
- 2026-09-17 executed (aw oc run): RETIRED as the orchestrator rollup step of a runner Set completion, not executed by an agent: every child of Set dirtygates reached executed, so the runner (run run-20260916T182835Z-1650244) retired this Order-0 plan as bookkeeping. Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate. Justifying children: d7qoxv, metc8b, 9iq461, u23gbn, ajxr5d, 4xt6u4.
- 2026-09-14 approved (aw set): status set to approved
- 2026-09-13 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-13: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own earlier review round while a blocking question was open; the maintainer then answered every open question in this plan through the `askme` workflow on 2026-09-13, one interactive prompt at a time, and each answer is recorded in this plan's `## Open questions` with its reasoning. Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round, having read every resolution as it was written. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the round that ran earlier the same day cost 3h 02m and $106.07 across nine items, cleared three plans, and raised four NEW blocking questions on the rest, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
- 2026-09-13 reviewed (aw set): /plan-review round 2: APPROVE WITH REVISIONS APPLIED; PR-010..PR-022; readiness go-pending-approval
- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review ROUND 2: REVIEWED - OPEN QUESTIONS; PR-010..PR-022; readiness no-go (PR-022 escalated as blocking OQ-04, the only unfixed finding; the other twelve are FIXED). `aw ipd lint` CONFORMING at `--phase author` on the orchestrator and all SIX children before semantic review, and at `--phase review-finalize` after. ROUND 1'S BLOCKER PR-001 IS DISCHARGED, verified in the children's EXECUTABLE text rather than the parent's prose: Order 02 now carries only E-02/E-03 with the deletion items withdrawn, Order 01's E-04 splits spec R5.4 by path with V-04 enforcing it, and `dirty_tree_overlap` still has one definition and one live caller. All round-1 measurements independently recomputed from `state.json` and they hold (27/42, 23/41, 18/43 blocked; 8/12/16 cascaded; $130.96 across five runs; the two stranded lanes are `merge-conflict` carrying git's own text). WHAT ROUND 2 FOUND is a different defect class: the resolution DID NOT PROPAGATE. Nine findings are stale text that would misdirect an executor, and three are consequential. PR-010 (BLOCKER): the orchestrator's own checklist still ordered the executor to stop predicting the merge and delete `dirty_tree_overlap`, the exact act the same document's OQ-02 withdrew. PR-016 (HIGH): the completion criteria still demanded "No pre-merge prediction exists", so a correctly executed Set would fail its own definition of done. PR-013 (BLOCKER, MEASURED): Order 04 E-06's prescribed CAS-then-ff-only sequence is a NO-OP THAT REPORTS SUCCESS; built twice in scratch repos, the merge prints "Already up to date." and touches nothing, leaving the `D `/`A ` inverse dirt F-7 forbids and making the peer-protecting refusal unreachable. Corrected by ordering (the ff-only merge must ITSELF advance the branch; clean case leaves exactly ` M peer.txt` with peer bytes verbatim, contended case refuses rc=1 with HEAD unmoved), and the resulting tension with `commit_isolated`'s own CAS is now named for E-01 to resolve. PR-011/PR-014/PR-015 (HIGH): Orders 02 and 04 still declared resolved questions BLOCKING and pointed at withdrawn or carved-out items, and PR-015 found a genuinely ORPHANED test obligation (the `test_ipd_lifecycle_cli.py` cleanliness hole attached to an E-item that now lives in Order 06), re-assigned in writing. PR-018 added the missing V-evidence that the RETAINED guard survived, without which an implementation could reclassify the post-merge branch while quietly deleting the pre-merge check. PR-022 (HIGH, left OPEN deliberately): Orders 01, 02 and 04 carry stale `Readiness: no-go` from their own round-1 reviews although their blocking questions are now resolved; NOT fixed here because `Readiness` is another review's attestation output and writing it would forge the evidence the auto-approve predicate reads. Each needs its own `/plan-review` round 2. No product code was modified by this review.
- 2026-09-13 to-review (aw set): status set to to-review

- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001..PR-009; PR-001 (BLOCKER) and PR-002 (HIGH) left OPEN and escalated to blocking OQ-02/OQ-03; review record written; Readiness no-go.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored during a live debugging session in which each failure was traced to code and each claim measured. One root cause was already fixed and landed separately (commit `c53849e5`, relocate with `git mv`); this Set removes the guards that turned that defect into a whole-run outage and removes the remaining mid-run writes to the shared checkout.

## Goal

Make a dirty shared checkout irrelevant to work that does not touch it, make git the authority on whether a merge is safe, and leave the shared checkout untouched for the whole duration of a run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the children

- [ ] E-01 Execute Order 01 (`d7qoxv`): turn the pre-launch dirty-tree refusal into a warning FOR THE ISOLATED PATH ONLY, and amend spec `7ckptx` R5.4 and A14 so the obligation is SPLIT BY PATH rather than removed. RESTATED AT REVIEW ROUND 2 to match what Order 01 now says: it does NOT delete the refusal outright, and the shared-tree obligation must survive for `3i0aaz` E-03 to extend. Not gated: OQ-02 is resolved.
  - Depends on: none
  - Expected outcome: an isolated turn launches against a checkout holding an unrelated dirty tracked path and the dirty paths are reported rather than refused, WHILE spec R5.4 still carries a refusal obligation for the non-isolated path.
  - Execution state: pending
- [ ] E-02 Execute Order 02 (`metc8b`): KEEP `dirty_tree_overlap` and reclassify a REAL `git merge` local-changes refusal from the terminal `merge-conflict` to the deferrable `integration-blocked`, keyed on a structural discriminator rather than git's English. CORRECTED AT REVIEW ROUND 2: the earlier wording ("stop predicting the merge with `dirty_tree_overlap`") describes Order 02's WITHDRAWN items and contradicted the OQ-02 resolution recorded in this same plan; the prediction stays. Not gated.
  - Depends on: none
  - Expected outcome: a local-changes refusal is recorded `integration-blocked` (retryable) carrying git's own text, a genuine content conflict still records `merge-conflict`, and the two are told apart by `MERGE_HEAD` presence rather than by message text.
  - Execution state: pending
- [ ] E-03 Execute Order 03 (`9iq461`): perform the backlog close inside the lane so it lands if and only if the merge lands.
  - Depends on: none
  - Expected outcome: main's `git status --porcelain` is empty across an isolated item that closed a backlog item, and the close rides the merge.
  - Execution state: pending
- [ ] E-04 Execute Order 04 (`u23gbn`): retire an orchestrator in a coordinator-owned throwaway worktree, landing the rollup as one ref update, and fix the index residue a failed retirement leaves.
  - Depends on: none
  - Expected outcome: the shared checkout is clean at every observable instant of a retirement, including a failed one.
  - Execution state: pending
- [ ] E-05 Execute Order 05 (`ajxr5d`): isolate a review turn in a worktree too, so its plan edit and review record land via one merge instead of being committed into the shared checkout mid-run.
  - Depends on: none
  - Expected outcome: no action type writes to the shared checkout mid-run, and a review's two output files arrive together or not at all.
  - Execution state: pending
- [ ] E-06 Execute Order 06 (`4xt6u4`): stop a failed orchestrator retirement leaving regenerated index files in the shared checkout, and add the tree-cleanliness assertion the existing fault tests lack.
  - Depends on: none
  - Expected outcome: after a failed retirement the shared checkout is byte-identical to before the attempt, and the suite detects a regression.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---:|---|---|---|
| 01 | `20260913-dirtygates-01-d7qoxv-delete-the-pre-launch-dirty-tree-refusal-and-report-it-as-a.ipd.md` | Pre-launch clean-base gate becomes a warning; amends spec 7ckptx R5.4 + A14 | none |
| 02 | `20260913-dirtygates-02-metc8b-let-git-decide-a-merge-back-instead-of-predicting-it-with-a.ipd.md` | Deletes the pre-merge overlap prediction; git's own refusal is the answer | none |
| 03 | `20260913-dirtygates-03-9iq461-close-a-backlog-item-inside-the-lane-so-nothing-writes-to-th.ipd.md` | Backlog close moves into the lane and rides the merge | none |
| 04 | `20260913-dirtygates-04-u23gbn-retire-an-orchestrator-in-a-coordinator-owned-throwaway-work.ipd.md` | Retirement runs in a coordinator-owned throwaway worktree; index residue fixed | none |
| 05 | `20260913-dirtygates-05-ajxr5d-isolate-a-review-turn-in-a-worktree-too-so-no-turn-writes-to.ipd.md` | Review turns get worktree isolation; their two output files land via one merge | none |
| 06 | `20260913-dirtygates-06-4xt6u4-stop-a-failed-orchestrator-retirement-leaving-regenerated-in.ipd.md` | Failed retirement leaves no index residue; carved from Order 04 at revision | none |

The six are INDEPENDENT by design, so a review may approve and run any subset. Orders 01 and 02 both edit prose in `lane_containment.py` that describes the two gates as a contrasting pair, so whichever runs second owns reconciling that paragraph; Order 02's E-05 states this explicitly. Orders 03, 04 and 05 touch disjoint files, except that Orders 03 and 05 both edit `oc_runipd.py` and `agy_runipd.py` in different regions (the close path versus the review-isolation guards).

## Completion criteria (the whole Set is done only when)

- No PRE-LAUNCH gate refuses an ISOLATED turn because of a dirty path the turn will not touch.
- A pre-launch refusal obligation still exists for the NON-ISOLATED (shared-tree) path, so `3i0aaz` E-03 has a requirement to extend.
- The pre-merge overlap check STILL EXISTS (`dirty_tree_overlap` retained), and a real git local-changes refusal is recorded as the deferrable `integration-blocked` rather than the terminal `merge-conflict`. CORRECTED AT REVIEW ROUND 2: the earlier criterion "No pre-merge prediction exists" was the pre-OQ-02 end state and would have failed a correctly executed Set.
- A run performs NO edit, move, or commit in the shared checkout for a successful item, FOR EVERY ACTION TYPE (execute, review, orchestrate), EXCEPT the single reconciliation Order 04 E-06 owns, which F-7 measures as unavoidable and which must be a refusing fast-forward.
- A failed orchestrator retirement leaves the shared checkout byte-identical to how it found it (Order 06).
- The merge-and-revalidate suite run is still in place and still gates integration for EXECUTE turns.
- Both hosts behave identically for every change above.

## Collisions with approved work (RESOLVED at review round 1; kept as the record)

THIS SECTION DESCRIBES A CONFLICT THAT NO LONGER EXISTS, and it is retained because the reasoning is
what justifies the shapes Orders 01 and 02 now carry. Do NOT read it as a reason to hold either child.

WHAT ROUND 1 MEASURED, by resolving each id6 in `pending/` and reading its front matter. Three plans are
`Status: approved`, `Readiness: go-pending-approval`, and `Blocks-Release: next`, and each was approved
to do the OPPOSITE of a child of this Set to the SAME symbol, while no child named any of them.

| Approved plan | Its approved instruction | What the child does NOW (post-revision) |
|---|---|---|
| `fujm0y` (Set `mergedirty`, Order 1) | WIDEN `dirty_tree_overlap`'s input from `lane.changed_files` to the `git merge-tree --write-tree` result diffed against HEAD, so refusal is MORE accurate | NO CONFLICT. Order 02 KEEPS the symbol; its deletion items E-01/E-04/E-05 are WITHDRAWN. `fujm0y` may still widen it. |
| `51vw4y` (Set `integpath`, Order 3) | Add a non-terminal `integration-deferred` status plus a three-rung ladder ON TOP OF the dirty-overlap refusal ("THE REFUSAL ITSELF IS CORRECT AND MUST SURVIVE ... changes only the DISPOSITION after a refusal, never the refusal condition") | NO CONFLICT, and now COMPLEMENTARY. Order 02's surviving E-02 reclassifies a git local-changes refusal onto the `integration-blocked` arm, which is the exact arm `51vw4y` E-01 makes deferrable. |
| `3i0aaz` (Set `dirtybase`, Order 1) | EXTEND the clean-base REFUSAL to the `--no-isolate-worktree` path by relaxing the `isolate` condition, and add `--allow-dirty-base` as the consent escape hatch (with a spec `25kzda` 2.1 amendment) | NO CONFLICT. Order 01 now changes the ISOLATED path only, and its E-04 SPLITS spec `7ckptx` R5.4 by path, preserving the shared-tree obligation `3i0aaz` E-03 builds on. Its V-04 FAILS the item if that obligation is left absent. |

WHY THE RESOLUTION IS SOUND RATHER THAN A COMPROMISE, and this is the part worth keeping: the two
guards had ASYMMETRIC MEASURED EVIDENCE. The pre-launch WHOLE-TREE refusal has 68 measured refusals
against it in one night and no measured save, so removing it for the isolated path is evidence-led. The
INTEGRATION-TIME overlap check has a measured save behind it (the 2026-09-05 incident, where four lanes
were refused and all four merged clean later), so keeping it and letting `fujm0y` widen it and `51vw4y`
make it recoverable is also evidence-led. Answer (c) is not a split of the difference; it is the answer
each guard's own record supports.

ONE SEQUENCING FACT REMAINS TRUE AND IS NOT A BLOCKER FOR THIS SET. `fujm0y` declares
`Item-Dependencies: executed:6sb3yu, executed:51vw4y`. Re-verified at review round 2: `6sb3yu` IS in
`.aw/records/plans/executed/`, and `51vw4y` has NOT executed (`integration-deferred` greps to ZERO under
`agent_workflows/`, and `integration-blocked` is still in both hosts' `TERMINAL_STATES`, obtained by
importing both modules). So `fujm0y` is `dependency-blocked` at dispatch until `51vw4y` runs. That is a
fact about the `mergedirty`/`integpath` queue, NOT a constraint on this Set: no child of this Set touches
`TERMINAL_STATES` or `dirty_tree_overlap`'s body any more, so this Set may run in any order relative to
those three plans.

## Cross-IPD validation

- Spec coherence: only Order 01 amends a spec (`7ckptx` R5.4/A14) in the default case; Order 04 must amend `77tr3o` ONLY IF its OQ-03 had ruled "fork", which it did not (it ruled option (a), change the shared body), so no `77tr3o` amendment is expected. After the Set, re-read R5.4 and confirm the shared-tree obligation survives.
- Prose coherence: `lane_containment.evaluate_clean_base`'s docstring contrasts itself with `dirty_tree_overlap` (`lane_containment.py:2571`). ONLY Order 01 changes that paragraph now, because Order 02 withdrew its counterpart edit, so the paired cross-reference must still name `dirty_tree_overlap` as a LIVE symbol afterwards. VERIFIED AT REVIEW ROUND 2: `dirty_tree_overlap` is referenced in prose at `wtiso_gate.py:287,296`, `runner_shutdown.py:333`, `runner_shared.py:866` and `oc_runipd.py:1961` as well; since the symbol survives, none of those needs touching, which is a direct saving from the OQ-02 resolution.
- Host parity: confirm each child changed both runners where the behavior is shared. Spec `7ckptx` R4 treats a host-only guard as a divergence, and `z2isfg` already left agy behind once on a neighbouring gate.
- End-to-end: run a multi-item batch with a deliberately dirty unrelated tracked path in the checkout and confirm every item runs. That is the direct regression for the three measured outages.

## Deferred / out of scope (with reason)

- The merge-and-revalidate suite run. KEPT deliberately: it re-runs validation against the combined result, which is where a genuine stale base surfaces as a test failure rather than a guess. Order 01 depends on it remaining.
- DELETING `dirty_tree_overlap`, and deleting the pre-launch refusal for the SHARED-TREE path. Both were in scope when this Set was authored and both are now OUT, by OQ-02's resolution to answer (c). Recorded here so a later reader does not treat the Set's title ("let git be the authority on a merge") as still describing a deletion: the title now overstates what ships, and the Scope line above governs.
- Path-scoping the pre-launch gate to `Scope-Paths` instead of removing the refusal. Considered and rejected in Order 01's deferred section, with the reasoning recorded there.
- The `git mv` relocation fix. ALREADY DONE and landed as commit `c53849e5` before this Set was written, with the suite green. It removes the cause of the dirty path; this Set removes the guards that amplified it into an outage. Both were needed.
- A full audit of every coordinator-side write to the shared checkout. Order 04 fixes retirement only; a wider audit would be its own plan.
- The unrelated queue-build defect where an already-executed Set child is queued with `file: null` and a guessed status, blocking its dependents. Filed separately as backlog `cjefq5`; it is not a dirty-tree problem.

## Scope check

- Over-scope, RESOLVED AT REVIEW ROUND 2 rather than left as a caveat: the earlier note warned that Order 02 "may touch several test files that only pin `dirty_tree_overlap` by identity". That breadth is GONE, because the OQ-02 resolution withdrew the deletion. Order 02 now touches only the post-merge failure branch and its tests. NOTE ONE RESIDUAL DECLARATION TO RECONCILE: Order 02 still declares `agent_workflows/lane_containment.py` and `tests/test_lane_clean_base.py` in `Scope-Paths` although no surviving item edits either (its change 5 is WITHDRAWN and change 1 is WITHDRAWN). Its executor must either drop them from the declaration or acknowledge each with `--scope-ack` at finalize; flagged here because a declared-but-unmodified path costs a `--scope-ack` for no reason (PR-012).
- Under-scope: this Set no longer removes either guard wholesale, so the "no replacement guard" concern narrows to ONE case: the pre-launch refusal on the ISOLATED path. That removal has a named downstream replacement (merge-and-revalidate, which stays) plus a measured disproof (Order 01 F-3) that the gate deferred rather than prevented the harm. The shared-tree path keeps its refusal, so no path is left both unguarded and unmeasured.

## Required tests / validation

- Each child's own validation, with pasted evidence.
- The Set-level end-to-end above: a batch of several isolated execute items, with an unrelated dirty tracked path present, completing every item.
- A batch in which item 1 closes a backlog item, proving items 2 and 3 still run and main stays clean. This is the exact shape of run `run-20260913T031148Z-1722898`, which lost 23 of 41 items.
- Full suite run bare on both hosts' surfaces, with the failure set diffed against a baseline from the same commit.

## Open questions

### OQ-02 (RESOLVED, answer (c) adopted and both children revised): Three approved release-blocking plans were approved to do the OPPOSITE of Orders 01 and 02. Which intent wins?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: NOT resolvable from repository evidence, because the repository contains a human approval on BOTH sides. `fujm0y`, `51vw4y` and `3i0aaz` are each `Status: approved` with `Blocks-Release: next`, and each is approved to widen, preserve, or extend exactly what a child here removes (see "Collisions with approved work"). The decision is a release-scope and risk-appetite judgement, which AGENTS.md reserves to the maintainer, and it is irreversible in the direction this Set proposes: deleting `dirty_tree_overlap` and rewriting spec `7ckptx` R5.4 discards work already reviewed and signed off, and `51vw4y`'s ladder cannot be built afterwards without re-adding the refusal. RESOLVED 2026-09-13 (author revision at the maintainer's direction): ANSWER (c), THE SPLIT ALONG THE MEASURED EVIDENCE, which was this review's own recommendation. NO APPROVED PLAN IS CONTRADICTED and no release blocker is negated, so the collision is DISSOLVED rather than adjudicated. Concretely: Order 01 now removes the pre-launch whole-tree refusal for the ISOLATED path only and its spec amendment PRESERVES R5.4's obligation for the shared-tree path, which is what `3i0aaz` E-03 is approved to extend (that path has 68 measured refusals against it and no measured save). Order 02 now KEEPS `dirty_tree_overlap` and reduces to reclassifying a git local-changes refusal from the terminal `merge-conflict` to the deferrable `integration-blocked`, so `fujm0y` may still widen it and `51vw4y` may still build its ladder on it (that check has a measured save behind it in the 2026-09-05 incident). Orders 03, 04, 05 and 06 were never in conflict. See the revision commit and each child's own resolved OQ for the reasoning.
  VERIFIED AT REVIEW ROUND 2 THAT THE RESOLUTION LANDED IN THE CHILDREN, because a resolution recorded only on the parent is a claim about work nobody did. Order 02 now carries exactly two execution items (E-02, E-03), its "Proposed changes" marks E-01/E-04/E-05 WITHDRAWN, no deliverable of its touches `dirty_tree_overlap`'s body, and its OQ-03 records option (b). Order 01's E-04 now reads "SO THE OBLIGATION IS SPLIT BY PATH, NOT REMOVED", and its V-04 fails the item if the amended requirement leaves `3i0aaz` E-03 nothing to build on. So the collision is dissolved IN THE EXECUTABLE TEXT, not only in this rationale. CONSEQUENCE: NEITHER ORDER 01 NOR ORDER 02 IS GATED ANY MORE. Round 2 corrected the stale sentences elsewhere in this Set that still said they were (PR-010, PR-011); if you find another, it is stale text and this paragraph governs.
  THE THREE COHERENT ANSWERS, each with its real cost. (a) THIS SET WINS: retire `fujm0y` and `51vw4y` to `superseded/` with a reason, and narrow `3i0aaz` to its untracked REPORT plus the shared-tree case only, dropping the refusal extension. Cost: discards two reviewed release blockers, one of which addresses a measured 2026-09-05 incident that lost 7 of 34 items, and that incident's cause (a lane refused at 08:06 that would have merged at 08:40) is NOT addressed by this Set at all. (b) THE APPROVED PLANS WIN: execute `51vw4y` then `fujm0y` then `3i0aaz`, and reduce Order 02 to nothing and Order 01 to the reporting change only. Cost: keeps a guard this Set argues is less accurate than git, and leaves the whole-tree pre-launch refusal that measurably cost 68 items in one night. (c) SPLIT ALONG THE MEASURED EVIDENCE, which is this review's recommendation: the pre-launch WHOLE-TREE refusal (Order 01) is the one with 68 measured refusals against it and NO measured save, so remove it; the INTEGRATION-TIME overlap check (Order 02) has a measured save behind it in the 2026-09-05 incident, so keep the symbol and let `fujm0y` widen it and `51vw4y` make it recoverable, which delivers this Set's actual goal (a non-conflicting lane integrates) without deleting anything approved. Under (c), Orders 03, 04 and 05 are unaffected and can proceed independently.
  WHAT REVIEW ESTABLISHED SO THE CHOICE IS INFORMED, measured in a scratch repo at review and matching the plan's own F-1/F-2/F-3: a real `git merge` with a NON-overlapping dirty path SUCCEEDS and preserves the dirt; with an OVERLAPPING dirty path it REFUSES, names the file, aborts, and leaves both main and the dirty content intact; `git merge-tree --write-tree` returns rc=0 in BOTH cases and is therefore not a valid predictor. So "let git decide" is technically sound. The question is not whether it works; it is whether deleting an approved, release-gating guard is the right way to get there.

### OQ-03: Is the pre-launch clean-base refusal safe to remove for a NON-isolated run too, or only for an isolated one?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: Order 01 removes the refusal at a call site guarded by `if isolate and self_finalize and not is_review`, so it changes ISOLATED runs only, and its F-3 disproof is specifically about a LANE ("a worker lane cut from HEAD lacked an uncommitted change"). That disproof does NOT transfer to a shared-tree run, where the agent writes directly into a tree already holding another party's uncommitted work and its own changes cannot be distinguished from theirs at commit time. Approved plan `3i0aaz` E-03 exists precisely to ADD the refusal to that path, calling it "the case where dirt is MOST dangerous, since the agent writes directly into the tree it is polluting". Order 01 nowhere states whether it intends to block that. Blocking because if the answer is "the shared-tree refusal is still wanted", Order 01's spec amendment to R5.4 must PRESERVE the obligation for the non-isolated case rather than replacing it wholesale, and an amendment that removes it is not something an agent should decide: R5.4 is an approved contract and the weaker version cannot be un-shipped once other plans are reviewed against it. RESOLVED 2026-09-13 (author revision at the maintainer's direction): ONLY FOR AN ISOLATED RUN. The shared-tree refusal is KEPT, because the F-3 disproof is specific to a lane cut from a commit and does not transfer to a tree the agent writes into directly, and because `3i0aaz` E-03 is approved to extend exactly that refusal. Order 01's E-04 now SPLITS R5.4's obligation by path rather than replacing it, and its V-04 fails the item if the amended requirement leaves `3i0aaz` nothing to build on.

### OQ-04: Orders 01, 02 and 04 carry a stale `Readiness: no-go`. Who re-reviews them, given this review's ledger was the orchestrator alone?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-022
- Resolution or deferral rationale: NOT resolvable by this reviewer, because the fix is an ATTESTATION THIS REVIEW DID NOT EARN. THE FACTS, measured at review round 2: Orders 01 (`d7qoxv`), 02 (`metc8b`) and 04 (`u23gbn`) each carry `- Readiness: no-go`, written by their OWN round-1 reviews at a time when each had a blocking question OPEN. All three of those questions are now RESOLVED (Order 01 OQ-02, Order 02 OQ-03, Order 04 OQ-03), and this round verified the resolutions genuinely landed in their executable checklists. So the recorded readiness no longer describes any of the three.
  RESOLVED 2026-09-13 by the maintainer: OPTION (c), THE MAINTAINER'S OWN ATTESTATION IS THE CLEARANCE. Asked directly how the stale verdicts should be cleared, they chose to attest rather than fund another review round, and the `- Readiness:` field on Orders 00, 01, 04 and 05 was set to `go-pending-approval` as THEIR recorded decision, with the attestation written into each plan's workflow history naming who decided, when, on what basis, and that no agent wrote the value on its own authority.
  WHY THIS IS LEGITIMATE AND NOT A SHORTCUT: this question's own analysis said a human may attest what an agent may not, and that is exactly what happened. Every open question in the four plans was put to the maintainer through `askme` on 2026-09-13, ONE interactive prompt at a time, and every answer is recorded in the owning plan with its reasoning. The maintainer read each resolution as it was written.
  WHY OPTION (a) WAS PRICED AND REJECTED ON EVIDENCE RATHER THAN PREFERENCE: option (a) recommended running `/plan-review` on each plan individually. That had ALREADY BEEN DONE the same day, in run `run-20260913T194605Z-526466`: 3h 02m, $106.07, nine items. It cleared three plans and raised FOUR NEW blocking questions on the others, which is precisely why they were stale a second time. So a further round was not expected to produce a clean sheet, and recommending one would have been recommending the same spend for the same outcome.
  HONEST LIMIT, stated because the option carried it: no independent reviewer checked the revised plans, so the maintainer is vouching on their own reading. That is their prerogative and it is now on the record as such.
  WHY THIS IS NOT COSMETIC. AGENTS.md states the auto-approve predicate reads the `Readiness` FIELD FIRST and only falls back to the workflow history when the field is ABSENT. A stale `no-go` is therefore not a neutral leftover: it is a live refusal. The practical consequence is that after human approval this Set would execute Orders 03, 05 and 06 and SILENTLY SKIP the three plans carrying the outage fix that motivated the whole Set, which is the opposite of the intent and would be discovered only by noticing what did not run.
  WHY I DID NOT SIMPLY WRITE THE FIELD, which is the tempting one-line fix. `Readiness` is an OUTPUT of a review OF THAT PLAN. AGENTS.md forbids writing another role's attestation field and names this exact field as the canonical case, because the gate reads the field as evidence that a review cleared the plan. My Step 0 ledger was the orchestrator alone; I read all six children as EVIDENCE and corrected measurably false statements in three of them, but I did not perform an independent full review of each. Writing `go-pending-approval` into three plans I did not fully review would fabricate precisely the evidence the predicate consumes, and under `--full-auto` that fabrication is what promotes a plan to approved.
  THE OPTIONS, so the decision is a choice and not a chore. (a) RUN `/plan-review` ON EACH of `d7qoxv`, `metc8b` and `u23gbn` individually, so each earns its own round-2 record and its own honest readiness. This is the recommendation: it is the only route that produces real attestations, and each plan has changed materially since its round 1 (Order 02 lost three E-items, Order 04 lost two to Order 06 and had its central mechanism corrected here). (b) ACCEPT the risk and approve the Set knowing three children will not auto-promote, promoting them by hand instead. (c) DECIDE that the maintainer's own direction to revise these plans constitutes the clearance, and record that as the attestation with `--by-human`, which is legitimate because a human may attest what an agent may not.
  BLOCKING because it is not a preference: left unanswered, the Set half-executes silently, and the failure mode is an ABSENCE, which is the hardest kind to notice. It blocks the SET's readiness, not the orchestrator's own correctness, which is clean.

### OQ-01: Should this Set also make worktree isolation mandatory rather than a default?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: every child preserves the non-isolated path (`--no-isolate-worktree`), which is why Order 03 keeps `commit_backlog_close` alive for it. If isolation were mandatory, several of these code paths would collapse to one and the shared checkout could never be written mid-run by construction. Non-blocking because the Set achieves its goal for the default path without that decision, and removing an escape hatch is a separate judgement about users the author should not make unilaterally. RESOLVED 2026-09-13 by the maintainer: KEEP `--no-isolate-worktree`, and do NOT make isolation mandatory in this Set. Two reasons they weighed. FIRST, an approved plan of theirs (`3i0aaz`) exists specifically to add a clean-base safety check for the SHARED-TREE case, which only has a subject if that case survives; removing the flag would require narrowing or retiring an approved release blocker. SECOND, Order 03 already keeps the non-isolated code path alive deliberately, so nothing in this Set forces the decision. ACCEPTED COST, stated so it is not discovered later: after this Set lands, every action type the runner performs is isolated (execute already was; review becomes so under Order 05; retirement under Order 04; the backlog close rides the merge under Order 03), so this flag becomes the ONE remaining route by which a run can write directly into the shared checkout mid-run, which is the failure class that refused 68 items on 2026-09-13. The maintainer judged that removing an escape hatch is easier to regret than to postpone. NOT DEFERRED WITH A TRIGGER: it is decided for now and may be revisited once `3i0aaz` has landed and the shared-tree path has its own guard.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Order 01 in `executed/` with all its V-items evidenced, plus the amended R5.4/A14 text pasted and `aw specs check` conforming.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Order 02 in `executed/` with all its V-items evidenced, including the case where a non-conflicting dirty tree no longer blocks integration and the case where git's own refusal is recorded as `integration-blocked` with git's text.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Order 03 in `executed/` with all its V-items evidenced, including main's empty `git status --porcelain` across a closing item and the merge containing the backlog move.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Order 04 in `executed/` with all its V-items evidenced, including the before/after `git status --porcelain` for a fault-injected retirement showing no `INDEX.json`/`INDEX.md` residue.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Order 05 in `executed/` with all its V-items evidenced, including MAIN's `git status --porcelain` sampled DURING a review turn and the merge containing both the plan edit and the review record.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: Order 06 in `executed/` with both its V-items evidenced, including the before/after `git status --porcelain` for a fault-injected retirement and the assertion demonstrated failing against the pre-fix behavior.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: SIX independent children share one root cause and one test surface, so they are reviewed together and may be executed separately. CORRECTED AT REVIEW ROUND 2: an earlier version said "five" children and that Orders 01 and 02 were gated on blocking OQ-02. Both statements are now false. OQ-02 is RESOLVED to answer (c) and both children were revised to that shape, so all six are independent in intent as well as in file scope. The one real ordering constraint left is internal and stated in the child table: Orders 01 and 02 no longer touch each other's prose, and Order 06 was carved from Order 04 precisely so it carries no architecture decision.

Execution contract: commit only files each plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim. Order 01 amends an approved spec and declares that spec file in its `Scope-Paths`.

Post-gate lifecycle move: this orchestrator is retired by the runner once every child is `executed` on disk; it performs no work of its own beyond sequencing.
