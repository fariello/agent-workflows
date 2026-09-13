# IPD: Stop a dirty main tree from blocking a run, and let git be the authority on a merge

- Date: 2026-09-13
- Kind: orchestrator
- Concern: Four consecutive IPD batch runs on 2026-09-13 failed heavily, each for the same structural reason: one item's own bookkeeping left the shared checkout dirty, and a whole-tree gate then refused every remaining item. RE-MEASURED AT REVIEW from each run's `state.json` rather than trusted: 68 refusals across three runs (27 of 42, 23 of 41, 18 of 43), every one naming a single uncommitted backlog markdown file, plus 36 cascaded `dependency-blocked`; two verified lanes stranded; ~$131 of agent cost across the four runs producing four executed plans. NOT a 100% failure rate: each of the three large runs did execute at least one item and complete several reviews, so the honest claim is "the majority of every run was lost", which is damning enough without overstating.
- Scope: Remove the two dirty-tree guards that block work without preventing harm, and stop the runner writing to the shared checkout mid-run at all. Five children: the pre-launch refusal, the pre-merge prediction, the backlog close, orchestrator retirement, and review isolation. Excludes the merge-and-revalidate suite run, which is the check that does real work and is deliberately KEPT.
  THIS SET COLLIDES WITH THREE APPROVED, RELEASE-BLOCKING PLANS AND MUST BE SEQUENCED AGAINST THEM, WHICH IS THE FINDING REVIEW ADDS. See "Collisions with approved work" below and blocking OQ-02. In short: `fujm0y` is APPROVED to WIDEN the very function Order 02 DELETES, `3i0aaz` is APPROVED to EXTEND the very refusal Order 01 REMOVES to a second code path, and `51vw4y` is APPROVED to make the refusal Order 02 deletes NON-TERMINAL. All three carry `Blocks-Release: next`. None was mentioned in any of the five children.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, agent_workflows/ipd_lifecycle.py, tests/test_lane_clean_base.py, tests/test_runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_orchestrator_retirement.py, .aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: dirtygates
- Order: 0
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 8lfoum
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001..PR-009; PR-001 (BLOCKER) and PR-002 (HIGH) left OPEN and escalated to blocking OQ-02/OQ-03; review record written; Readiness no-go.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored during a live debugging session in which each failure was traced to code and each claim measured. One root cause was already fixed and landed separately (commit `c53849e5`, relocate with `git mv`); this Set removes the guards that turned that defect into a whole-run outage and removes the remaining mid-run writes to the shared checkout.

## Goal

Make a dirty shared checkout irrelevant to work that does not touch it, make git the authority on whether a merge is safe, and leave the shared checkout untouched for the whole duration of a run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the children

- [ ] E-01 Execute Order 01 (`d7qoxv`): delete the pre-launch dirty-tree refusal, report it as a warning, and amend spec `7ckptx` R5.4 and A14 to match.
  - Depends on: none
  - Expected outcome: an isolated turn launches against a checkout holding an unrelated dirty tracked path, and the dirty paths are reported rather than refused.
  - Execution state: pending
- [ ] E-02 Execute Order 02 (`metc8b`): stop predicting the merge with `dirty_tree_overlap` and let the real `git merge` attempt decide, mapping its refusal onto `integration-blocked`.
  - Depends on: none
  - Expected outcome: a lane whose changes do not conflict integrates even with a dirty main tree; a genuine clash is refused by git, named by git, and non-destructive.
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

- No gate refuses an isolated turn because of a dirty path the turn will not touch.
- No pre-merge prediction exists; a merge-back is decided by attempting the merge.
- A run performs NO edit, move, or commit in the shared checkout for a successful item, FOR EVERY ACTION TYPE (execute, review, orchestrate).
- A failed orchestrator retirement leaves the shared checkout byte-identical to how it found it.
- The merge-and-revalidate suite run is still in place and still gates integration.
- Both hosts behave identically for every change above.

## Collisions with approved work (added at review; read before executing any child)

MEASURED AT REVIEW, by resolving each id6 in `pending/` and reading its front matter. Three plans are
`Status: approved`, `Readiness: go-pending-approval`, and `Blocks-Release: next`, and each one is
approved to do the OPPOSITE of a child of this Set to the SAME symbol. None of the five children names
any of them, so an executor working only from this Set cannot see the conflict.

| Approved plan | Its approved instruction | The child that contradicts it |
|---|---|---|
| `fujm0y` (Set `mergedirty`, Order 1) | WIDEN `dirty_tree_overlap`'s input from `lane.changed_files` to the `git merge-tree --write-tree` result diffed against HEAD, so refusal is MORE accurate | Order 02 E-04 DELETES `dirty_tree_overlap` outright and requires `grep` to return zero hits |
| `51vw4y` (Set `integpath`, Order 3) | Add a non-terminal `integration-deferred` status plus a three-rung ladder ON TOP OF the dirty-overlap refusal ("THE REFUSAL ITSELF IS CORRECT AND MUST SURVIVE ... changes only the DISPOSITION after a refusal, never the refusal condition") | Order 02 E-01 deletes the refusal condition the ladder is built on |
| `3i0aaz` (Set `dirtybase`, Order 1) | EXTEND the clean-base REFUSAL to the `--no-isolate-worktree` path by relaxing the `isolate` condition, and add `--allow-dirty-base` as the consent escape hatch (with a spec `25kzda` 2.1 amendment) | Order 01 E-01/E-02 delete the refusal on the isolated path and E-04 rewrites spec `7ckptx` R5.4 from a refusal obligation to a reporting obligation |

`fujm0y` additionally declares `Item-Dependencies: executed:51vw4y`, and `51vw4y` has NOT executed
(`integration-deferred` greps to ZERO in `agent_workflows/`, and `integration-blocked` is still in both
hosts' `TERMINAL_STATES`, verified by importing both modules at review). So `fujm0y` is currently
`dependency-blocked` at dispatch and cannot land before this Set unless `51vw4y` runs first.

THIS IS A SEQUENCING AND AUTHORITY QUESTION, NOT A MERGE-ORDER QUESTION, so the runner's isolation does
NOT solve it. Worktrees make concurrent EDITS to one file safe; they cannot decide whether a function
should exist. Whichever lands second silently negates the other's approved intent, and in two of the
three cases the loser is a plan a human has already signed off as gating the release. Resolve OQ-02
before executing Orders 01 or 02.

WHAT REVIEW DID NOT DO: it did not decide the answer. The argument for this Set is strong and measured
(see the corrected F-3 and the git measurements re-verified at review), and the argument for
`51vw4y`'s ladder is also strong. Choosing between "delete the guard" and "make the guard accurate and
recoverable" is a maintainer's call about the release, so it is escalated rather than resolved.

## Cross-IPD validation

- Spec coherence: only Order 01 amends a spec (`7ckptx` R5.4/A14). After the Set, re-read that requirement and confirm no other child contradicts it.
- Prose coherence: `lane_containment.evaluate_clean_base`'s docstring contrasts itself with `dirty_tree_overlap`. Both are changed by this Set, so confirm the final text describes what shipped and names no deleted symbol.
- Host parity: confirm each child changed both runners where the behavior is shared. Spec `7ckptx` R4 treats a host-only guard as a divergence, and `z2isfg` already left agy behind once on a neighbouring gate.
- End-to-end: run a multi-item batch with a deliberately dirty unrelated tracked path in the checkout and confirm every item runs. That is the direct regression for the three measured outages.

## Deferred / out of scope (with reason)

- The merge-and-revalidate suite run. KEPT deliberately: it re-runs validation against the combined result, which is where a genuine stale base surfaces as a test failure rather than a guess. Orders 01 and 02 both depend on it remaining.
- Path-scoping the pre-launch gate to `Scope-Paths` instead of removing the refusal. Considered and rejected in Order 01's deferred section, with the reasoning recorded there.
- The `git mv` relocation fix. ALREADY DONE and landed as commit `c53849e5` before this Set was written, with the suite green. It removes the cause of the dirty path; this Set removes the guards that amplified it into an outage. Both were needed.
- A full audit of every coordinator-side write to the shared checkout. Order 04 fixes retirement only; a wider audit would be its own plan.
- The unrelated queue-build defect where an already-executed Set child is queued with `file: null` and a guessed status, blocking its dependents. Filed separately as backlog `cjefq5`; it is not a dirty-tree problem.

## Scope check

- Over-scope: Order 02 may touch several test files that only pin `dirty_tree_overlap` by identity. That breadth follows from an existing anti-fork convention, not from scope creep, and Order 02's OQ-01 lets review choose the narrower option.
- Under-scope: this Set does not add a replacement for either removed guard. That is the point: one prevented nothing (measured), and the other was less accurate than the thing it predicted. The real check, merge-and-revalidate, already exists and stays.

## Required tests / validation

- Each child's own validation, with pasted evidence.
- The Set-level end-to-end above: a batch of several isolated execute items, with an unrelated dirty tracked path present, completing every item.
- A batch in which item 1 closes a backlog item, proving items 2 and 3 still run and main stays clean. This is the exact shape of run `run-20260913T031148Z-1722898`, which lost 23 of 41 items.
- Full suite run bare on both hosts' surfaces, with the failure set diffed against a baseline from the same commit.

## Open questions

### OQ-02: Three approved release-blocking plans are approved to do the OPPOSITE of Orders 01 and 02. Which intent wins?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: NOT resolvable from repository evidence, because the repository contains a human approval on BOTH sides. `fujm0y`, `51vw4y` and `3i0aaz` are each `Status: approved` with `Blocks-Release: next`, and each is approved to widen, preserve, or extend exactly what a child here removes (see "Collisions with approved work"). The decision is a release-scope and risk-appetite judgement, which AGENTS.md reserves to the maintainer, and it is irreversible in the direction this Set proposes: deleting `dirty_tree_overlap` and rewriting spec `7ckptx` R5.4 discards work already reviewed and signed off, and `51vw4y`'s ladder cannot be built afterwards without re-adding the refusal.
  THE THREE COHERENT ANSWERS, each with its real cost. (a) THIS SET WINS: retire `fujm0y` and `51vw4y` to `superseded/` with a reason, and narrow `3i0aaz` to its untracked REPORT plus the shared-tree case only, dropping the refusal extension. Cost: discards two reviewed release blockers, one of which addresses a measured 2026-09-05 incident that lost 7 of 34 items, and that incident's cause (a lane refused at 08:06 that would have merged at 08:40) is NOT addressed by this Set at all. (b) THE APPROVED PLANS WIN: execute `51vw4y` then `fujm0y` then `3i0aaz`, and reduce Order 02 to nothing and Order 01 to the reporting change only. Cost: keeps a guard this Set argues is less accurate than git, and leaves the whole-tree pre-launch refusal that measurably cost 68 items in one night. (c) SPLIT ALONG THE MEASURED EVIDENCE, which is this review's recommendation: the pre-launch WHOLE-TREE refusal (Order 01) is the one with 68 measured refusals against it and NO measured save, so remove it; the INTEGRATION-TIME overlap check (Order 02) has a measured save behind it in the 2026-09-05 incident, so keep the symbol and let `fujm0y` widen it and `51vw4y` make it recoverable, which delivers this Set's actual goal (a non-conflicting lane integrates) without deleting anything approved. Under (c), Orders 03, 04 and 05 are unaffected and can proceed independently.
  WHAT REVIEW ESTABLISHED SO THE CHOICE IS INFORMED, measured in a scratch repo at review and matching the plan's own F-1/F-2/F-3: a real `git merge` with a NON-overlapping dirty path SUCCEEDS and preserves the dirt; with an OVERLAPPING dirty path it REFUSES, names the file, aborts, and leaves both main and the dirty content intact; `git merge-tree --write-tree` returns rc=0 in BOTH cases and is therefore not a valid predictor. So "let git decide" is technically sound. The question is not whether it works; it is whether deleting an approved, release-gating guard is the right way to get there.

### OQ-03: Is the pre-launch clean-base refusal safe to remove for a NON-isolated run too, or only for an isolated one?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: Order 01 removes the refusal at a call site guarded by `if isolate and self_finalize and not is_review`, so it changes ISOLATED runs only, and its F-3 disproof is specifically about a LANE ("a worker lane cut from HEAD lacked an uncommitted change"). That disproof does NOT transfer to a shared-tree run, where the agent writes directly into a tree already holding another party's uncommitted work and its own changes cannot be distinguished from theirs at commit time. Approved plan `3i0aaz` E-03 exists precisely to ADD the refusal to that path, calling it "the case where dirt is MOST dangerous, since the agent writes directly into the tree it is polluting". Order 01 nowhere states whether it intends to block that. Blocking because if the answer is "the shared-tree refusal is still wanted", Order 01's spec amendment to R5.4 must PRESERVE the obligation for the non-isolated case rather than replacing it wholesale, and an amendment that removes it is not something an agent should decide: R5.4 is an approved contract and the weaker version cannot be un-shipped once other plans are reviewed against it.

### OQ-01: Should this Set also make worktree isolation mandatory rather than a default?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: every child preserves the non-isolated path (`--no-isolate-worktree`), which is why Order 03 keeps `commit_backlog_close` alive for it. If isolation were mandatory, several of these code paths would collapse to one and the shared checkout could never be written mid-run by construction. Non-blocking because the Set achieves its goal for the default path without that decision, and removing an escape hatch is a separate judgement about users the author should not make unilaterally.

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
- Cohesion rationale: five independent children share one root cause and one test surface, so they are reviewed together and may be executed separately. Note that "independent" is true of their FILE scopes and false of their intent once the approved plans in "Collisions with approved work" are considered: Orders 01 and 02 are gated on blocking OQ-02, while Orders 03, 04 and 05 are genuinely independent and unaffected by it.

Execution contract: commit only files each plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim. Order 01 amends an approved spec and declares that spec file in its `Scope-Paths`.

Post-gate lifecycle move: this orchestrator is retired by the runner once every child is `executed` on disk; it performs no work of its own beyond sequencing.
