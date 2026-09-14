# Review: stop a dirty main tree from blocking a run, and let git be the authority on a merge, orchestrator 8lfoum (Set dirtygates)

- Subject-Id: 8lfoum
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `151bcc86`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) on the orchestrator AND on all five children before semantic review.

DISCLOSURE: this Set was authored in this repository by the same model family, so treat it as a
near-self-review worth less than an independent one. Its value rests on what was MEASURED rather than
re-read. Eleven things were measured at review: all four 2026-09-13 runs' per-item statuses, refusal
reasons and costs recomputed from `state.json`; the two stranded lanes' `integration_deferral` strings
read verbatim; `dirty_tree_overlap`'s single definition and sole caller located by symbol; both hosts'
`TERMINAL_STATES` obtained by importing the modules; `integration-deferred` grepped to zero; all six
`not is_review` guard anchors verified on BOTH hosts; the `git merge` behavior re-reproduced in two
scratch repos for the overlapping and non-overlapping dirty cases; `git merge-tree --write-tree` shown
rc=0 in both; the two INDEX files' ignore status checked with `git check-ignore`; spec `7ckptx` R5.4/A14
read at their cited lines; and each colliding plan's id6 resolved in `pending/` with its front matter read.

THE SET'S CORE DIAGNOSIS IS CORRECT AND ITS MEASUREMENTS MOSTLY HOLD. The outage was real and worse than
a summary suggests: 68 items refused across three runs, every refusal naming ONE uncommitted backlog
markdown file, plus 36 cascaded `dependency-blocked`, at ~$131 total cost. The root cause was already
fixed separately (`c53849e5`). Orders 03, 04 and 05 are well-argued, correctly scoped, and their code
anchors verified exactly.

WHAT REVIEW FOUND IS A COLLISION THE SET CANNOT SEE. Three plans are `Status: approved`,
`Readiness: go-pending-approval`, and `Blocks-Release: next`, and each is approved to do the OPPOSITE of
a child here to the SAME symbol: `fujm0y` WIDENS the `dirty_tree_overlap` that Order 02 DELETES;
`51vw4y` builds a non-terminal deferral ladder ON TOP of the refusal Order 02 removes, stating "THE
REFUSAL ITSELF IS CORRECT AND MUST SURVIVE"; `3i0aaz` EXTENDS the clean-base refusal Order 01 deletes to
the `--no-isolate-worktree` path and amends the same spec family. None of the five children mentions any
of them. Worktree isolation does not solve this: it makes concurrent edits safe, not contradictory
intents. Escalated as blocking OQ-02 with three costed options, because a human has already signed off
BOTH sides and choosing is a release-scope call.

THE SECOND FINDING IS THAT ORDER 02'S STRONGEST EVIDENCE IS FALSE. Its F-4 claimed the prediction
stranded lanes `bzz5e6` and `f6idxs`. Both runs record `merge-conflict`, not `integration-blocked`, and
both reasons are git's own "Your local changes ... would be overwritten by merge" naming the dirty
backlog file. So the REAL merge refused them and the prediction passed them through, the dirty path
being outside each lane's `changed_files`. Deleting the prediction would not have saved either lane; it
would only have changed the recorded `kind`, which is exactly what `fujm0y` delivers by widening. No run
record in this repository shows a lane stranded by `dirty_tree_overlap`, while the 2026-09-05 incident
that `51vw4y` cites DID strand four lanes on it and all four merged clean later, which is the case for a
recovery ladder rather than a deletion.

FOUR SMALLER CORRECTIONS. The "100% batch failure rate" is overstated (each run executed at least one
item and completed several reviews, reviews being exempt from the gate). Order 01's F-3 disproof is
specific to a lane cut from a commit and does not transfer to a shared-tree run, so its spec amendment
must not silently remove the obligation `3i0aaz` is approved to extend (blocking OQ-03). Order 04's F-3
index residue is real as a rollback defect but both files are GITIGNORED in this repo and cannot dirty
this checkout, so it is not a live cause of the outage. Order 05's six guard anchors were verified
correct on both hosts, and its E-01-before-changing-anything sequencing is the right shape.

WHAT REVIEW DID NOT DO: it did not decide OQ-02. "Let git decide" is technically sound and was
re-measured as sound. Whether deleting an approved release-gating guard is the right route to it is the
maintainer's call, and it is irreversible in the direction proposed.

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | G (executability), C (architecture) | `.aw/records/plans/pending/20260907-mergedirty-01-fujm0y-...ipd.md:12`, `20260906-integpath-03-51vw4y-...ipd.md:11`, `20260907-dirtybase-01-3i0aaz-...ipd.md:12` | Three plans that are `approved` + `Blocks-Release: next` are approved to widen, preserve, or extend exactly what Orders 01 and 02 delete. `51vw4y` states the refusal "MUST SURVIVE"; `fujm0y` widens its input set; `3i0aaz` extends it to a second call path. No child names any of them, so an executor cannot see the conflict, and whichever lands second silently negates an approved release blocker. | C:High; U:Low; S:Low; F:Medium-High; Overall:High | OPEN | Escalated as blocking OQ-02 with three costed options and a recommendation (split along the measured evidence: remove the pre-launch whole-tree refusal, keep the integration-time guard for `fujm0y`/`51vw4y`). A collision table added to the orchestrator. Not resolvable by an agent: human approval exists on both sides. |
| PR-002 | HIGH | UNDER-SCOPE | B (security/safety), D (invariants) | `agent_workflows/oc_runipd.py:6122`; Order 01 F-3; `3i0aaz` E-03 | Order 01's F-3 disproof concerns a LANE CUT FROM A COMMIT and does not transfer to a `--no-isolate-worktree` run, where the worker writes into a tree holding another party's uncommitted work. E-04 rewrites spec `7ckptx` R5.4 wholesale from a refusal obligation to a reporting obligation, which would remove the obligation for the shared-tree path that `3i0aaz` is approved to guard. | C:Medium; U:Low; S:Medium-High; F:Medium; Overall:Medium-High | OPEN | Escalated as blocking OQ-03. E-04 revised in place to scope the amendment to the isolated case and to forbid a wholesale removal pending the answer; F-3 given an explicit scope limit. |
| PR-003 | HIGH | IN-SCOPE | E (testing/verification), D | `run-20260913T032416Z-2009920/state.json`, `run-20260913T031521Z-1774617/state.json` per-item `status` + `integration_deferral` | Order 02's F-4 asserted `dirty_tree_overlap` stranded lanes `bzz5e6` and `f6idxs`. Measured: both are `merge-conflict` carrying git's own "Your local changes" text, so the REAL merge refused them and the prediction passed them through. The plan's strongest evidence supports its opposite, and no run record shows any lane stranded by this guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-4 rewritten with the measured truth; new F-4a states the honest, narrower case (rests on F-1/F-5 and simplicity, not on stranded work) and names the 2026-09-05 incident as the case FOR a ladder. Concern block updated. |
| PR-004 | MEDIUM | IN-SCOPE | G (honest documentation) | `.aw/records/runs/run-20260913T031350Z-1732436/state.json` and the two siblings | "100% batch failure rate" and "$106" are both wrong. Each large run executed at least one item and completed 4 to 6 reviews (reviews are exempt from the gate); four-run cost is ~$131. An overstated figure in a plan that will be cited later is a durable inaccuracy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Orchestrator Concern and Order 01 Concern restated with per-run counts, the cascade counts, and the recomputed cost; new F-6 records the measurement and its source. |
| PR-005 | MEDIUM | IN-SCOPE | A (correctness), G | `.aw/.gitignore:45-46`; `git check-ignore -v`; Order 04 F-3 | Order 04's F-3 residue (`?? INDEX.json`, `?? INDEX.md`) cannot dirty THIS checkout: both paths are gitignored and untracked here, so they never appear in `git status --porcelain`. The residue was seen in the harness fixture repo, which lacks that ignore rule. Presenting it as a live cause of the outage overstates it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-3a records the ignore status with its evidence, keeps the rollback defect as genuine, and states E-04's assertion is the durable value because the fixture is where the residue is visible. |
| PR-006 | MEDIUM | IN-SCOPE | G (executability) | orchestrator "Completion criteria"; `fujm0y` `Item-Dependencies: executed:51vw4y` | The Set declares `Item-Dependencies: none` on every child and states the five are independent, but two of them are effectively ordered AFTER a decision about three external approved plans, and `fujm0y` is itself `dependency-blocked` on unexecuted `51vw4y`. An executor told "execute dirtygates" would proceed with no visibility of that. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Collision section added naming each plan, its approved instruction, and the contradicting child, plus the measured fact that `51vw4y` has not executed (`integration-deferred` greps to zero; `integration-blocked` still terminal on both hosts). |
| PR-007 | LOW | IN-SCOPE | G | orchestrator Scope | The orchestrator's Scope said "Five children" while the Concern and completion criteria elsewhere referred to four ("four independent children share one root cause" in the cohesion rationale). Minor internal inconsistency in a plan whose whole job is sequencing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cohesion rationale corrected to five. |
| PR-008 | LOW | IN-SCOPE | E | Order 05 F-2 anchors; `agent_workflows/agy_runipd.py:3262,3291,3409,3584,3629,3720` | Order 05 cites six `not is_review` anchors on the oc host only, though its E-06 requires agy parity. All six verified correct on oc AND the six twins located on agy at review; recording them removes a re-derivation step for the executor. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The agy twin anchors added to Order 05's F-2 so E-01's classification table covers both hosts. |
| PR-009 | LOW | OVER-SCOPE | F (KISS) | Order 02 E-04; `agent_workflows/wtiso_gate.py:287-296`, `runner_shutdown.py:333` | Order 02's E-04 requires a repo-wide zero-hit grep for `dirty_tree_overlap`, which pulls in two unrelated prose sites and five identity-pinning test sites. Under OQ-02 option (b) or (c) this breadth evaporates entirely, so committing to it before the answer risks a large diff that must be reverted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | DEFERRED | Deferred pending OQ-02: the correct breadth is a function of that answer, and narrowing it now would presuppose the maintainer's decision. Recorded so the executor re-reads E-04's scope after the ruling. Consequence if unresolved: an executor may produce a wide deletion diff that a (b)/(c) ruling discards. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the review edit the five children, or only the orchestrator that was named in the invocation? | Edit the orchestrator, and additionally make the minimum in-place corrections to children 01, 02, 04 and 05 where a MEASURABLY FALSE claim would mislead an executor (F-4, F-3 scope, F-3a, the anchors). | Restrict edits strictly to the orchestrator and leave the false F-4 standing; or fully review all five as separate ledger entries with their own records. | `.aw/system/workflows/plan-review/plan-review.md:224-226` ("When a finding spans plans, fix it in the owning plan and cross-reference it from dependent plans"), which requires fixing in the OWNING plan; the ledger stays the orchestrator alone per Step 0.1. | yes |
| D-2 | Is PR-001 resolvable from repository evidence, since AGENTS.md tells a reviewer to resolve rather than ask? | No. Escalate to the maintainer as blocking. | Resolve it by recommending retirement of `fujm0y`/`51vw4y` on this Set's technical merits; or resolve it by narrowing Orders 01/02 unilaterally. | The repository holds a HUMAN approval on both sides (`fujm0y:12`, `51vw4y:11`, `3i0aaz:12`, all `Blocks-Release: next`), and AGENTS.md reserves scope/priority/risk-appetite and public-contract calls to the human. Deleting an approved guard plus amending an approved spec is not cleanly undoable. | no |
| D-3 | Which readiness value does a plan carry whose blocking questions are open? | `no-go`. | `go-pending-approval`, on the grounds that the Set is technically sound and only awaits a decision. | `plan-review.md:543-545`: NO-GO covers "any open question, any unfixed BLOCKER/HIGH". Two blocking questions are open and PR-001 is an unfixed BLOCKER. | yes |
| D-4 | Order 02 E-04's deletion breadth: narrow it now, or defer? | Defer, recording it as PR-009. | Narrow E-04 to a demote-not-delete now, which would presuppose OQ-02 option (b)/(c). | The correct breadth is a strict function of OQ-02's answer, and `plan-review.md:211` makes removal-or-explicit-deferral the default for over-scope; explicit deferral is chosen because the fix itself would encode an unmade decision. | yes |

D-2 is `Reversible: no` and is ESCALATED as required: raised in the reviewed plan as OQ-02 with
`- Blocking: yes` and `- Finding: PR-001`, so the lint gate refuses the plan at every checkpoint until
the maintainer answers.

## Round 2

Reviewed at HEAD `762d5ba1`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) on the orchestrator AND on all SIX children before semantic review; `--phase review-finalize`
re-run after revisions.

DISCLOSURE: same model family as the author, so this is a near-self-review worth less than an
independent one. Its value rests on what was MEASURED at this HEAD rather than re-read from round 1.

ROUND 1'S BLOCKER IS DISCHARGED, AND I VERIFIED THE DISCHARGE IN THE EXECUTABLE TEXT RATHER THAN TRUSTING
THE PARENT'S PROSE. PR-001 escalated a collision with three approved `Blocks-Release: next` plans;
OQ-02 was resolved to answer (c) and both children were genuinely revised: Order 02 now carries exactly
two execution items (E-02, E-03) with E-01/E-04/E-05 WITHDRAWN and no deliverable touching
`dirty_tree_overlap`, and Order 01's E-04 now splits spec R5.4's obligation by path with a V-04 that
fails the item if `3i0aaz` E-03 is left nothing to build on. Re-measured independently: `dirty_tree_overlap`
still has one definition (`runner_shared.py:888`) and one live caller (`:1003`); `6sb3yu` IS in
`executed/`; `51vw4y` has NOT executed (`integration-deferred` greps to zero, `integration-blocked` still
in both hosts' `TERMINAL_STATES` by import). So no approved plan is contradicted and the collision is
dissolved rather than adjudicated.

THE ROUND-1 MEASUREMENTS ALL HOLD, RECOMPUTED FROM `state.json` RATHER THAN QUOTED. Per-run queue
statuses: 27 of 42, 23 of 41, 18 of 43 `blocked`, with 8, 12 and 16 cascaded `dependency-blocked`
respectively; every refusal names exactly ONE uncommitted backlog markdown file (`0k74my` in the first,
`lsztiu` in the other two); five-run cost sums to $130.96, matching the plan's "~$131". The two stranded
lanes are `merge-conflict` carrying git's own "Your local changes" text, confirming round 1's PR-003
correction. The plan's honesty about NOT being a 100% failure rate is borne out (each large run recorded
4 to 6 `reviewed` items and at least one `executed`).

WHAT ROUND 2 FOUND IS A DIFFERENT CLASS OF DEFECT: THE RESOLUTION DID NOT PROPAGATE. Nine of the twelve
findings are stale text left behind by the revision, and they are not cosmetic. The orchestrator's own
checklist still instructed an executor to "stop predicting the merge with `dirty_tree_overlap`" (PR-010),
which is the WITHDRAWN work and the exact act the same plan's OQ-02 forbids; its completion criteria still
required "No pre-merge prediction exists" (PR-016), which a correctly executed Set now FAILS. Order 02's
gate still said OQ-03 was BLOCKING and named three withdrawn items as must-not-start (PR-011). Order 04's
gate still said OQ-03 gates most of the plan and pointed at E-03/E-04, which were carved out to Order 06
(PR-014, PR-015), leaving a test obligation attached to no checklist item. A resolved question that still
reads as blocking is worse than an open one: it stalls an executor who has permission to proceed.

THE FINDING THAT WOULD HAVE SHIPPED BROKEN CODE IS PR-013, AND IT WAS MEASURED, NOT REASONED. Order 04
E-06 prescribes "after the CAS advances the branch, run the reconciliation as a `--ff-only` merge". Built
by hand in two scratch repos: in that order the merge prints "Already up to date." and exits 0 WITHOUT
touching the working tree, because the branch already points at the landed commit. The shared tree is left
reading `D  p/executed/plan.md` / `A  p/pending/plan.md` while the reconciliation REPORTS SUCCESS, which is
precisely the inverse-direction dirt the plan's own F-7 says must not ship. Worse, the peer-protecting
refusal E-06 exists for becomes UNREACHABLE, since git never checks for an overwrite when there is nothing
to fast-forward. The fix is ordering: let the ff-only merge BE the branch advance. Measured in that order,
clean case is rc=0 "Updating .. / Fast-forward" leaving exactly ` M peer.txt` with the peer's bytes
verbatim, and the contended case is rc=1 with git's own refusal, peer bytes intact, HEAD not advanced.
That also puts E-01's "reuse `commit_isolated`" in tension with E-06, because `commit_isolated` performs
the CAS itself (`commit_lock.py:270`), and the plan nowhere acknowledges it.

I DID NOT WEAKEN THE SET'S GOAL, and one correction strengthened a child. Order 02's reclassification was
at risk of reading as cosmetic, since both kinds are terminal at HEAD today; I recorded WHY it is real
(`resume` re-queues both, so the near-term win is an honest record, while `51vw4y` E-01 makes only the
`integration-blocked` arm deferrable, so a misclassification today is excluded from that ladder tomorrow)
and added the V-item evidence that proves the retained guard survived, which nothing previously demanded.

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | G (executability), C (architecture) | `20260907-mergedirty-01-fujm0y-...ipd.md:12`, `20260906-integpath-03-51vw4y-...ipd.md:11`, `20260907-dirtybase-01-3i0aaz-...ipd.md:12`; Order 02 E-list; Order 01 E-04 | CARRIED FROM ROUND 1 AND NOW DISCHARGED. Three approved `Blocks-Release: next` plans were approved to widen, preserve or extend exactly what Orders 01 and 02 deleted. Re-verified at round 2 that the revision genuinely landed in both children's checklists (Order 02 reduced to E-02/E-03 with the deletion items withdrawn; Order 01 E-04 splitting R5.4 by path with V-04 enforcing it), so no approved intent is negated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 resolved to answer (c) by the maintainer; both children revised; collision section rewritten as the RECORD of a resolved conflict with a per-plan "what the child does NOW" column. No longer gating. |
| PR-010 | BLOCKER | IN-SCOPE | A (correctness), G | orchestrator E-02 (pre-edit); orchestrator OQ-02 resolution | The orchestrator's OWN execution checklist instructed the executor to "stop predicting the merge with `dirty_tree_overlap` and let the real `git merge` attempt decide", which is the work OQ-02 WITHDREW in the same document. An executor following the checklist would delete a symbol two approved release blockers depend on, and would believe the parent authorized it. A checklist that contradicts its own resolved question is the most dangerous kind of stale text, because the checklist is what gets executed. | C:Low; U:Low; S:Medium; F:Medium-High; Overall:Medium | FIXED | E-02 rewritten to the shipped shape (KEEP the guard, reclassify the refusal, key on a structural discriminator), with the correction and its reason stated inline. E-01 likewise restated as isolated-path-only with the spec split named. |
| PR-013 | BLOCKER | IN-SCOPE | A (correctness), E (testing) | Order 04 E-06, F-7; measured in two scratch repos at review; `commit_lock.py:270` | Order 04 E-06's prescribed sequence (CAS the ref, then `git merge --ff-only` in the shared tree) IS A NO-OP THAT REPORTS SUCCESS. Measured: the merge says "Already up to date.", exits 0, touches no file, and leaves `D `/`A ` staged entries for the plan's two paths, i.e. exactly the inverse-direction dirt F-7 forbids. The peer-protecting refusal branch is unreachable in that order, because git performs no overwrite check when there is nothing to fast-forward. It also contradicts E-01's "reuse `commit_isolated`", which performs the CAS itself. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | FIXED | New F-10 records both orderings with measured output. E-06 corrected: the ff-only merge must ITSELF advance the branch; clean and contended cases re-measured and pasted. E-01 gains an explicit instruction to resolve the `commit_isolated` tension and record the route. V-06 now requires proving the output is NOT "Already up to date." and that no separate `update-ref` is performed, plus that the recorded phase matches whether the commit actually landed. |
| PR-011 | HIGH | IN-SCOPE | G (executability) | Order 02 gate (pre-edit): "OQ-01 is answered (DELETE), and OQ-03 is BLOCKING ... E-01, E-04 and E-05 MUST NOT be started" | Every clause was false after the revision: OQ-03 is resolved to (b), which supersedes OQ-01's DELETE ruling, and E-01/E-04/E-05 no longer exist as checklist items. An executor would stall on an answered blocking question while hunting three absent items. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten: nothing gated, OQ-01's DELETE explicitly does not stand, an affirmative prohibition on touching `dirty_tree_overlap` or its call site, and the scope-declaration reconciliation (PR-012) stated. |
| PR-014 | HIGH | IN-SCOPE | G (executability) | Order 04 gate and E-01 (pre-edit): "OQ-03 IS BLOCKING AND GATES MOST OF THIS PLAN"; OQ-03 resolution at `:167` | Order 04's OQ-03 was RESOLVED by the maintainer to option (a), yet both its gate paragraph and E-01's first bullet still forbade starting E-01/E-02/E-05/E-06 until it was answered. The plan therefore refused itself. The resolution also carries two consequences the gate never propagated: the shared-body answer makes `tests/test_ipd_lifecycle_cli.py` mandatory, and it makes the `77tr3o` amendment NOT expected. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate and E-01 rewritten to state the answer and both consequences; the "fork" branch's spec obligation explicitly voided so no executor declares that spec file needlessly. |
| PR-015 | HIGH | UNDER-SCOPE | E (testing), G | Order 04 "Proposed changes" 3-4, Scope check, Required tests (pre-edit); Order 06 Scope-Paths; `tests/test_ipd_lifecycle_cli.py:969,985` | Order 04 still described E-03 and E-04 as its own items and told the executor to fall back to them; both were carved to Order 06. The consequence was a real ORPHANED OBLIGATION: the requirement to close the identical tree-cleanliness hole in `tests/test_ipd_lifecycle_cli.py` attached to E-04, which no longer exists in that plan, while Order 06 declares only `tests/test_orchestrator_retirement.py` in its `Scope-Paths`. Verified at review that neither fault test in `test_ipd_lifecycle_cli.py` asserts tree cleanliness, so the hole is genuine and was owned by nobody. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | Order 04's list, scope check and test section rewritten; the obligation SPLIT and re-assigned in writing (the assertion hole to Order 06, which must add that file to its own `Scope-Paths`; the suite run to Order 04 for the independent shared-body reason). Stale anchors `:968`/`:983` corrected to `:969`/`:985`. |
| PR-016 | HIGH | IN-SCOPE | D (invariants), G | orchestrator "Completion criteria" (pre-edit): "No pre-merge prediction exists" | The Set's completion criteria encoded the PRE-resolution end state, so a correctly executed Set would FAIL its own definition of done, and an executor optimizing for the criteria would delete the guard OQ-02 preserved. Criteria are read at the end, when the cost of acting on them is highest. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Criteria rewritten to the shipped end state: the prediction is retained, a local-changes refusal is `integration-blocked`, the shared-tree refusal obligation survives, and Order 04 E-06's single reconciliation is named as the one allowed shared-tree write. |
| PR-017 | MEDIUM | IN-SCOPE | E (testing) | Order 02 "Required tests" first bullet (pre-edit); `runner_shared.py:1003` | Order 02 still required "a test proving integration SUCCEEDS with a dirty tracked path in main that does not conflict with the lane's changes", described as the direct regression for F-4. Against the shipped code that test's premise belongs to the withdrawn deletion; the retained guard still refuses on intersection, so an executor would either write a failing test or "fix" it by removing the guard. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Bullet replaced with an explicit do-not-write note explaining why, and the non-overlapping case attributed to `fujm0y`, which is approved to change that input set. |
| PR-018 | MEDIUM | UNDER-SCOPE | E (testing), D | Order 02 V-02; `runner_shared.py:888,1003` | No V-item required proof that `dirty_tree_overlap` SURVIVED. Since the whole OQ-02 resolution turns on retaining it, an implementation that reclassified the post-merge branch while removing the pre-merge check would have passed every existing V-item. The `merge-conflict` arm was likewise unprotected against being collapsed into `integration-blocked`, which would make a human-resolution case retry forever. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | V-02 gains two required-evidence bullets: grep proving definition and live call site both present with the overlap refusal intact, and the content-conflict arm still recorded `merge-conflict` with the reason that arm matters. |
| PR-019 | MEDIUM | IN-SCOPE | G (honest documentation) | Order 02 E-02; both hosts' `TERMINAL_STATES` by import; `oc_runipd.py:7234-7247` | The surviving deliverable's VALUE was overstated by implication. Measured: `integration-blocked` and `merge-conflict` are BOTH terminal at HEAD on both hosts, and `resume` re-queues both, so the reclassification rescues no item today. Left unstated, a later reader could dismiss it as a cosmetic relabel and revert it, or oversell it as a recovery fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now states what the change buys today (an honest record, not a retry) and what it buys later (`51vw4y` E-01 makes only the `integration-blocked` arm deferrable, so a misclassification is excluded from that ladder), with an instruction to say so in the code comment. |
| PR-012 | LOW | OVER-SCOPE | G | Order 02 `Scope-Paths:8`; its withdrawn changes 1 and 5 | Order 02 still declares `agent_workflows/lane_containment.py` and `tests/test_lane_clean_base.py`, which were needed only by the withdrawn items. A declared-but-unmodified path costs the executor a `--scope-ack` at finalize for no reason, and invites a pointless edit to make the declaration true. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded in Order 02's gate and in the orchestrator's scope check as a reconciliation to perform (drop the declaration or `--scope-ack`), with an explicit instruction not to edit the files merely to justify it. |
| PR-020 | LOW | IN-SCOPE | A (correctness), G | Order 01 E-03; `lane_containment.py:2571`; `3i0aaz` PR-002 finding | Order 01 E-03 told the executor to preserve the `dirty_tree_overlap` cross-reference "Order 02 changes that neighbour", a coordination that no longer exists. Separately, E-03 rewrites the ONE shared `reason` string, and `3i0aaz` E-03 is approved to route a shared-tree REFUSAL through the same rule, so a warning-only wording would hand that plan a string contradicting its behavior. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 rewritten: the cross-reference stays and stays true (rewrite only this check's half), plus an instruction to keep the reason structure able to express both a report and a refusal. |
| PR-021 | LOW | IN-SCOPE | G | orchestrator Scope, cohesion rationale (pre-edit) | The orchestrator said "Five children" in Scope and "five independent children" in the cohesion rationale while the Set has SIX (Order 06 was carved from Order 04), and the cohesion rationale still asserted Orders 01 and 02 were gated on OQ-02. Round 1 fixed a four-versus-five instance of the same drift; the count moved again. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both corrected to six, with the gating claim removed and the correction noted so the next reader sees the count was verified rather than copied. |
| PR-022 | HIGH | IN-SCOPE | G (executability) | `20260913-dirtygates-01-...:11`, `-02-...:11`, `-04-...:10` all `- Readiness: no-go`; each child's own round-1 review record | THREE CHILDREN CARRY A STALE `no-go` READINESS. Orders 01, 02 and 04 were each set `no-go` by their OWN round-1 reviews because each had a blocking open question OPEN at the time. All three of those questions are now RESOLVED (Order 01 OQ-02, Order 02 OQ-03, Order 04 OQ-03), so the recorded readiness no longer describes the plans. This matters mechanically, not cosmetically: the auto-approve predicate reads the `Readiness` FIELD FIRST, and a `no-go` field means these three will not be picked up even after human approval, so the Set would silently execute only Orders 03, 05 and 06. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | OPEN | NOT FIXED BY THIS REVIEW, DELIBERATELY. `Readiness` is an attestation OUTPUT of a review of THAT plan, and AGENTS.md forbids writing another role's attestation field; my Step 0 ledger is the orchestrator alone, and I did not perform a full independent review of Orders 03, 05 or 06. Writing `go-pending-approval` into three children I did not fully review would forge exactly the evidence the gate reads. REQUIRED NEXT STEP, for the human: run `/plan-review` on each of `d7qoxv`, `metc8b` and `u23gbn` individually so each gets its own round-2 record and its own honest readiness. Not escalated as a blocking question in the orchestrator because it is not a decision anyone needs to make and it blocks nothing until approval; it is a mechanical follow-up, reported here and in the final report. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-022 (the three children's stale `Readiness: no-go`) is a HIGH I cannot fix without forging an attestation. Fix it anyway, report it only, or escalate it as blocking? | ESCALATE as blocking OQ-04. Writing the field is forbidden; reporting alone would leave a HIGH unescalated, which `check.review-finding-unescalated` correctly refuses. | Write `go-pending-approval` into the three children (fast, and forges the evidence the auto-approve predicate reads); or report it in the final report only and set `Blocking: no`, which the lint would have accepted only by understating the impact. | AGENTS.md names `Readiness` as the canonical attestation field an agent must never hand-write, because the auto-approve predicate reads the FIELD FIRST. `plan-review.md:335-341` requires a finding left OPEN at or above the gate threshold (`HIGH`) to be raised as a `Blocking: yes` question naming the finding. Both rules point the same way. | yes |
| D-2 | Order 04 E-06's mechanism was measured broken. Fix it in place, or mark the plan REPLAN? | Fix in place: correct the ORDERING (let the ff-only merge be the branch advance) and record the `commit_isolated` tension for E-01 to resolve. | REPLAN Order 04, on the grounds that its central mechanism did not work as prescribed; or defer the finding to the executor as an open question. | `plan-review.md:227-229` reserves REPLAN for an approach unsound and unrepairable with bounded edits. The approach (mutate off the shared tree, reconcile with a refusing fast-forward) is sound and was re-measured working; only the step order was wrong, which is a bounded edit. The residual `commit_isolated` question is an implementation shape question inside one function, which `plan-review.md:211` does not require escalating. | yes |
| D-3 | The Set's TITLE ("let git be the authority on a merge") now overstates what ships, since the prediction is retained. Rename the plans, or record the discrepancy? | Record it in the Deferred section rather than rename. | Rename the orchestrator and Order 02 to match the reduced scope. | Renaming a plan file changes the `<slug>` in the uniform artifact name and every cross-reference (six children, five review records, the plans index, and three sibling plans citing `metc8b`), and AGENTS.md forbids hand-naming plans (`aw rename plans` is the tool). The cost of a stale-but-explained title is one paragraph; the cost of a rename is a wide reference update for no behavioral gain. | yes |
| D-4 | Which readiness value does the orchestrator carry now? | `no-go`, and the verdict is REVIEWED - OPEN QUESTIONS. | `go-pending-approval`, on the grounds that twelve of thirteen findings are FIXED and the plan's own content is clean. | `plan-review.md:543-545` makes NO-GO the correct value when ANY open question or ANY unfixed HIGH remains; OQ-04 is open and PR-022 is an unfixed HIGH, so a positive readiness would be false. `aw ipd lint --phase review-finalize` independently refused the earlier `go-pending-approval` with `IPD-Q501`, which is the gate working as intended rather than an obstacle. | yes |

No `Reversible: no` decision was taken in this round, so no escalation is required under
`plan-review.md:279-292`. Round 1's D-2 was `Reversible: no` and was escalated as OQ-02; the maintainer
has since answered it, which is what discharged PR-001.

HONEST NOTE ON THIS ROUND'S VERDICT: I initially set `Readiness: go-pending-approval`, reasoning that the
orchestrator's own content was clean. `aw ipd lint --phase review-finalize` refused it (`IPD-Q501`, and
before that `check.review-finding-unescalated`), correctly: an unfixed HIGH must be escalated, and an
escalated blocking question means NO-GO. The verdict and readiness were corrected to match rather than the
finding downgraded to fit the verdict. Recorded because the wrong version existed briefly and the gate,
not the reviewer, is what caught it.

## Round 3

DISCHARGE ONLY. NO NEW REVIEW WAS PERFORMED. This round exists to record that round 2's gating finding
was resolved by the maintainer's own decision, taken on 2026-09-13 through the `askme` workflow, one
interactive prompt at a time. Nothing in the plan was re-reviewed here and no new finding was sought;
appending a round is the mechanism `plan-review.md:187` prescribes for this, since the gate reads only
the current round. The earlier rounds are left exactly as written.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-022 | HIGH | IN-SCOPE | G (executability) | the resolved `OQ-04` in this plan's `## Open questions` | Three children carried a stale `Readiness: no-go`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer set `Readiness: go-pending-approval` on Orders 00, 01, 04 and 05 as their own attested decision, recorded in each plan's workflow history naming who decided, when, and that no agent wrote the value. Round 2 left this OPEN because writing the field itself would have forged the attestation the auto-approve predicate reads; a human may attest what an agent may not, and did. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the maintainer's answer to OQ-04 discharge PR-022, or does the finding need a fresh review pass? | It discharges it; record the discharge and leave the earlier rounds untouched. | Run a further full review round on this plan. | The finding's own recorded remedy was a human decision, and that decision is now recorded in the owning plan with its reasoning. A further round was priced on evidence and rejected: the round earlier the same day cost 3h 02m and $106.07 across nine items and raised four NEW blocking questions, so it was not expected to yield a clean sheet. | yes |

HONEST LIMIT: the discharge rests on the maintainer's decision, not on an independent reviewer's
re-examination. If a later reader needs assurance that this plan's content was checked afresh, that
assurance is in rounds 1 and 2 and not here.
