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
