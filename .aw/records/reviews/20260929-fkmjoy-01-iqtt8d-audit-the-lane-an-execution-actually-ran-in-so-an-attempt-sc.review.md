# Review findings: plan iqtt8d

- Subject-Id: iqtt8d
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `8c95fa8b` in an isolated review lane. The plan file was committed and byte-identical to the
lane input (`diff -q` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `conforming` after revision. This is the cleanest-entering plan of the sweep:
it arrived with no structural findings, no stale `Scope-Paths`, and all three of its deferred-row carriers
already filed and resolvable, so `check.scope-drift`'s and `check.ipd-uncarried-obligation`'s error-severity
rules were both silent on it from the start.

TEN OF THE ELEVEN FINDINGS RE-DERIVED AND HELD, by running code rather than reading prose. F-1: branches
`aw/lane/om3rzi` and `aw/lane/om3rzi_attempt2` both exist and both HOLD WORK, with `inspect_lane` reporting
`base_sha=cdfddf2e6d35 ahead=1` and `base_sha=d69ed2a8b17f ahead=1` respectively. F-2, the central claim, is
exact: inside the canonical lane `git merge-base --is-ancestor d69ed2a8 HEAD` exits 1 while inside
`_attempt2` it exits 0, and correspondingly `_plan_execution_tree(root, "om3rzi", "d69ed2a8b17f")` returns
`None` while passing the attempt id returns the real lane path. So the rule measures the abandoned sibling and
falls silent on a fully auditable execution, which is a resolution defect and not an honest abstention exactly
as the plan argues, and it is the hazard `lane_branch_name`'s own docstring forbids ("Callers must NOT
reconstruct this by hand from an id6"). F-5: the anchored pattern accepts `om3rzi`, `_attempt2` and
`_attempt12` and rejects the review-sweep lane, which is a real branch on this checkout. F-7's and F-8's
in-tree quotations are present as given. F-9: `drift_exit_code` returns 0 for `info` and 1 for `warning` and
`error`, so E-04's severity choice is verified rather than asserted. F-11: `read_lane_owner` from a lane root
returns `None`. And the three multi-lane `id6` values are live right now (`om3rzi`, `vxqtqm`, `19lmbe`), so
the population this plan repairs exists.

WHAT REVIEW FOUND THAT AUTHORING DID NOT is one HIGH that changes the review question, and three measurement
corrections.

THE HIGH: `check.scope-drift` IS A GATING RULE, AND THE PLAN CALLS IT AN ADVISORY THROUGHOUT. It is registered
`RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-01")`, `drift_exit_code` returns 1 on it,
`check_scope_drift` composes into `check_commit_invariants`, and `aw check release-gates` runs fail-closed in
CI. The plan's Goal says "this rule stays local best-effort feedback" and its Concern, Scope, title and
Proposed-changes all say "advisory". That understatement matters because it changes the review question from
"is this feedback useful" to "is this gate safe to widen": after E-03, an execution that is silent today can
begin FAILING a check. The answer on present evidence is yes, and I measured it rather than assuming: of the
two live receipts on this checkout (`ghna7l`, `q32qeg`) both already resolve their canonical lane and each has
exactly ONE lane candidate, so the enumeration changes nothing for either, while the three `id6`s that DO hold
sibling lanes hold no receipt at all. So the immediate blast radius is zero findings. I did not narrow the
work; I corrected the description, added F-12 and F-13 with the measurements, added E-07 to measure the
before/after gate outcome as part of execution, and put a STOP directive in the gate for the case where a new
`error` finding is not a true positive (PR-001).

THE MEASUREMENT CORRECTIONS. First, E-02 instructs the executor to "recover each lane id with the existing
`lane_id_from_branch` inverse", which reads as though that function groups sibling lanes. It does not:
`lane_id_from_branch("aw/lane/om3rzi_attempt2")` returns `'om3rzi_attempt2'`, and its own docstring says the
colon is deliberately not recovered because "only the branch identity matters for inspection". Grouping the 20
live lane branches by its return value yields ZERO multi-lane groups, which would have made the resolver find
nothing. The function is right for the SECOND step (producing the id `inspect_lane` must be given, which is
the `resumedupe txc9l1` hazard it exists to close) and cannot perform the FIRST. E-02 now separates the two
and carries the review-verified anchored pattern (PR-002, F-14).

Second, F-4 attaches its 272-path figure to the wrong comparison. Measured: `d69ed2a8..aw/lane/om3rzi` (the
receipt base against the WRONG lane) gives 272, while the item's direction (1), substituting the lane's own
base, is `cdfddf2e..aw/lane/om3rzi` and gives 7, which equals that lane's real work. So direction (1) is not
refuted by the 272 number at all; it is refuted by F-6's argument, that a correct diff of the wrong execution
is still the wrong answer. The 272 remains decisive for a different and still-important conclusion: it is what
the rule would report if the ancestry guard were removed, which is why that guard must stay. Corrected in
place, with F-6 given the whole argument and F-4's consequence column reconciled (PR-003).

Third, F-3's zero-findings conclusion survives but its stated reason has drifted. Authoring said all receipts
belong to terminal plans so the rule examines none; at review there are 26 receipts and TWO are reachable and
live. The zero holds for a better reason: those two already resolve their canonical lane and find no
out-of-scope path. The `is_retired` mechanism still explains the other 24 (PR-004).

ONE ENVIRONMENTAL GAP WORTH ITS OWN FINDING: E-01's census asks for each lane's owner-record `disposition` and
`base_commit`, and that column is UNOBTAINABLE if the plan executes in a lane, which it will under a runner.
`.aw/worktrees/` does not exist in a lane worktree at all, `_owner_record_path` composes from the passed root,
and `read_lane_owner` returns `None` for every lane. This is F-11's asymmetry observed where it bites rather
than in the abstract, and it is also the empirical vindication of E-02's design: `inspect_lane` is unaffected
because it reads git refs and the reflog, and it still reported `state=HOLDS-WORK base_sha=d69ed2a8b17f
ahead=1` for `om3rzi_attempt2` with no owner record present. E-01 now expects this and says to record it and
continue (PR-005, F-15).

ON THE TWO OPEN QUESTIONS, both left `open` with `Owner: maintainer`: I did NOT resolve either, and that is
deliberate. Both are risk-appetite and design-direction calls that the repository cannot answer, both are
`Blocking: no` so neither holds the plan, and both already carry a filed, resolvable carrier (`p4hmpz`,
`m94le9`) whose content I read and found complete. OQ-01 asks whether the new `info` rule should ever gate,
which needs a residual-rate datum that only shipping E-03 produces. OQ-02 asks whether the receipt should
record the allocated lane, which the plan correctly identifies as a superseding-rather-than-amending decision.
Asking a human to decide these before execution would block work on answers that execution itself generates.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C. Architecture and operability (the change's own risk class is misstated) | `check_engine`'s registry: `"check.scope-drift": RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-01")`; `artifact_core.drift_exit_code([Drift(severity="error")])` returns 1 (and 0 for `info`); `check_scope_drift` composed into `check_commit_invariants`; the plan's Goal "this rule stays local best-effort feedback" | **The plan calls `check.scope-drift` an advisory and best-effort feedback throughout, but it is `error`-severity and gating, so E-02 and E-03 WIDEN A GATE.** An execution silent today can begin failing `aw check` and CI once its lane resolves. The work is right and the description is not, which matters because it changes the review question from usefulness to gate safety, and it would let an executor ship a new `error` finding believing it could not fail anything | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Goal, Concern and Scope corrected to name the severity and the gating path; new F-12 records the registry entry and the `drift_exit_code` verification; new F-13 records the measured blast radius (zero: both live receipts have one candidate each and already resolve it; the three sibling-lane id6s hold no receipt); new E-07/V-07 measure findings and `aw check` exit codes before and after and require a true-positive judgement on any new `error`; the gate gains a DO NOT NARROW / STOP-AND-REPORT directive and a prohibition on changing the severity, the invariant, the gating-set membership or the ancestry guard |
| PR-002 | HIGH | IN-SCOPE | A. Correctness (the prescribed mechanism cannot do what the step needs) | `lane_id_from_branch("aw/lane/om3rzi_attempt2")` returns `'om3rzi_attempt2'`; its docstring: "The colon is not recovered, and it does not need to be: only the branch identity matters for inspection"; grouping the 20 live lane branches by its return value yields 0 multi-lane groups | **E-02 says to "recover each lane id with the existing `lane_id_from_branch` inverse", which reads as though that function groups sibling lanes, and it cannot.** It returns the attempt-suffixed id, so an executor grouping by it would find zero sibling sets and the resolver would never see a second candidate, silently reproducing today's defect | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 rewritten to separate the two jobs: the anchored match against the target `id6` performs the GROUPING, and `lane_id_from_branch` performs the distinct job of producing the id `inspect_lane` must be given (its `resumedupe txc9l1` purpose). The measured return value and the zero-groups result are quoted, and the review-verified anchored pattern is given with its accept set (`om3rzi`, `_attempt2`, `_attempt12`) and reject set (the review-sweep lane plus three near misses), noting both anchors are required. New F-14 |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness (a measured figure attached to the wrong comparison) | `d69ed2a8..aw/lane/om3rzi` = 272 paths; `cdfddf2e..aw/lane/om3rzi` = 7 paths; `cdfddf2e..aw/lane/om3rzi_attempt2` = 270; `d69ed2a8..aw/lane/om3rzi_attempt2` = 5 | **F-4 says substituting the lane's own base gives 272 paths, and it gives 7.** The 272 comes from diffing the RECEIPT base against the WRONG lane, which is what today's rule would report without its ancestry guard. So the item's direction (1) is not refuted by that number, and a reviewer checking the plan's decisive argument would find it does not reproduce as described | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-4 rewritten with all four measurements and an explicit statement of which comparison yields which, re-attributing the 272 to the guard-removal case and making it the argument for KEEPING the ancestry guard. F-6 now carries the whole rejection argument (a correct diff of the wrong execution is still the wrong answer) rather than leaning on the number, and F-4's consequence column is reconciled |
| PR-004 | MEDIUM | IN-SCOPE | G. Plan executability (a live count and its explanation drifted) | 26 receipts at review (24 at authoring); `ghna7l` and `q32qeg` are reachable from `_iter_type_files` AND pass `_receipt_is_live`; `check_scope_drift(repo)` still returns 0 findings | **F-3's conclusion holds but its stated cause no longer does: it says every receipt belongs to a terminal plan, and two now do not.** The zero survives because those two already resolve their canonical lane and find nothing out of scope, which is a different and stronger reason. Left uncorrected, a reviewer re-deriving F-3 would find the premise false and might discount the finding | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 corrected with both counts, the two named live receipts, and the better reason for the zero, while keeping the `is_retired` mechanism (which still explains the other 24) as a real and still-operative half |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Plan executability (a required census column is unobtainable in the execution environment) | From this review lane: `.aw/worktrees/` does not exist; `_owner_record_path(root, "om3rzi_attempt2")` composes to an absent lane-local path; `read_lane_owner` returns `None`; yet `inspect_lane` reports `state=HOLDS-WORK base_sha=d69ed2a8b17f ahead=1` | **E-01 requires each lane's owner-record `disposition` and `base_commit`, and that column cannot be produced from a lane worktree, which is where this plan will execute under a runner.** F-11 records the asymmetry abstractly; the consequence for E-01 is not drawn, so an executor would hit `None` for every lane and either report false drift or stall | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now states the expectation explicitly with the measurement, instructs the executor to record "owner records unreadable from this root" and continue rather than treating it as drift or a blocker, and notes that `inspect_lane` is unaffected. New F-15 records it as the empirical vindication of E-02's git-refs-only design rather than as a defect to fix |
| PR-006 | LOW | UNDER-SCOPE | G. Plan executability (gate missing conditional finalize ownership) | The gate's closing paragraph read "The terminal transition is the tooled one (`aw ipd finalize`), not a hand `git mv`" | **The gate names the tooled verb but not WHO runs it, so an executing agent under a runner may finalize a transition the driver owns.** The review workflow's Step 4 requires the conditional ownership, and its absence produces either a double transition or a hand-rolled move | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now states the driver owns the transition under `aw oc run`/`aw agy run` while the executor finalizes only on a hand run, and forbids hand-editing `- Status:` or `git mv`ing into `executed/` with the reason (it skips the pre-transition checkpoint) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001 found the plan widens an `error`-severity gating rule while describing it as an advisory. Narrow the work, change the severity, or keep the work and correct the description plus add a measurement gate? | Keep the work, correct the description, and add E-07 to measure the before/after gate outcome with a STOP directive for a non-true-positive finding | Narrowing E-03 so it only resolves lanes for plans that already report a finding, which would defeat the purpose; downgrading `check.scope-drift` to `warning` or `info` to de-risk the widening, which silently weakens a shipped gate; shipping as authored and letting CI discover any new finding | The defect is real and the fix is correct: the rule currently gives a WRONG answer (silence on an auditable execution), and a gate that under-reports is worse than one that reports. Measured blast radius is zero on this checkout, so the risk is bounded today. Downgrading the severity would be a much larger change to a rule carrying invariant `I-01` and is nowhere in this plan's scope. The residual risk is a future false `error`, which E-07 converts from a CI surprise into an execution-time STOP | yes |
| D-2 | E-02's `lane_id_from_branch` instruction cannot group siblings (PR-002). Replace the function, or split the step? | Split the step: anchored match groups, `lane_id_from_branch` produces the inspect id | Grouping by stripping `_attemptN` from `lane_id_from_branch`'s output, which is the hand-built string manipulation `lane_branch_name`'s docstring forbids; adding a new `lane_base_id_from_branch` helper to `worktree_lease`, which is a wider API change than this plan's scope | `lane_id_from_branch` exists specifically to close the `resumedupe txc9l1` hazard (passing a branch name to `inspect_lane` as a lane id), so it must stay in the second position; its docstring is explicit that the colon is deliberately not recovered, so using it for grouping is using it against its stated contract. The anchored regex is confined to the resolver, needs no new module API, and review verified its accept and reject sets including the live review-sweep lane | yes |
| D-3 | F-4's 272 figure is attached to the wrong comparison (PR-003). Delete the figure, or re-attribute it? | Re-attribute it and give F-6 the whole rejection argument | Deleting the 272 as an error, which would discard a genuinely important measurement; leaving it and adding a footnote, which leaves the plan's decisive argument reading as unreproducible | The 272 is real and load-bearing, just for a different conclusion: it is what the rule reports if the ancestry guard is removed without fixing resolution, which is the strongest available argument for keeping that guard. Direction (1) still deserves rejection, and F-6's argument (a correct diff of the wrong execution) does the whole job on its own without a number to dispute | yes |
| D-4 | OQ-01 (should the new `info` rule ever gate) and OQ-02 (should the receipt record the allocated lane) are both `open`, `Owner: maintainer`, `Blocking: no`. Resolve, or leave for the human? | Leave both open for the maintainer, unchanged | Resolving OQ-01 from evidence, which is impossible because the datum (the residual firing rate after E-03) does not exist until E-03 ships; resolving OQ-02 by choosing the enumerating resolver permanently, which pre-empts a design call about the receipt schema | Both are genuine risk-appetite and design-direction calls, which the review workflow reserves to the human, and both already carry a filed resolvable carrier (`p4hmpz`, `m94le9`) whose content I read and found complete with the question, the missing datum, and the risk of deciding blind. Neither blocks: they are `Blocking: no`, so `IPD-Q501` does not fire and the plan can reach `approved`. Asking now would block work on answers the work itself produces | yes |
| D-5 | E-01's owner-record column is unobtainable from a lane (PR-005). Drop the column, or keep it with an expectation? | Keep it, with the measured expectation that it will be empty in a lane and an instruction to record that and continue | Dropping the column, which loses real information when the plan is hand-run from the checkout where the records ARE readable; making the census fail or stop when the records are absent, which would block execution on an environmental fact | The column is genuinely useful from the main checkout (it is how F-1 identified which lane was the real execution) and genuinely unavailable from a lane, so the right answer is conditional rather than binary. Measured that `inspect_lane` supplies `state`/`base_sha`/`commits_ahead` regardless, so nothing the plan actually depends on is lost, and saying so converts a confusing `None` into a recorded expectation | yes |
