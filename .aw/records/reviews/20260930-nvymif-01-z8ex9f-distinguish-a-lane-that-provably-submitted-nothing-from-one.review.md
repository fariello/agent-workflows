# Review findings: plan z8ex9f

- Subject-Id: z8ex9f
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review and
again at `author` and `review-finalize` after revision. The plan is `- Kind: child`, so the `IPD-S407`
orchestrator child-row check does not apply.

THIS IS THE STRONGEST PLAN IN THIS SWEEP AND ITS CENTRAL SAFETY JUDGEMENT IS CORRECT. The backlog item
asked for one narrowing; the author measured what else that refusal was holding up, found it was the only
thing standing between a lane holding unmerged committed work and a force-remove that also deletes the
branch, and added the compensating condition in the same change. I REPRODUCED THAT BLOCKER INDEPENDENTLY
rather than trusting it, on real git worktrees with real run directories at review HEAD:

- F-01 reproduces verbatim. An empty lane reports `readable True`, `dirty_tracked ()`,
  `unknown_untracked ()`, `unknown_ignored ()`, `uncollected_submission True`, `classified False`,
  `reason_codes ('uncollected-submission',)`, with the detail string exactly as quoted ("no attempt-keyed
  collection receipt at `01-aaaaaa-attempt-1.json`; absence means NOT collected (spec R2.5)").
- F-05 REPRODUCES, INCLUDING THE DATA-LOSS AUTHORIZATION. A lane with one unmerged commit
  (`rev-list --count main..` = 1, `merge-base --is-ancestor` rc=1, clean porcelain, no submissions) is
  blocked ONLY by `uncollected-submission`; clearing that single field via `LaneInventory._replace` yields
  `classified True reason_codes ()`. I confirmed the structural reason rather than inferring it:
  `LaneInventory` has no commit-related field and `RETENTION_*` has no commit-related code, so nothing
  else can catch it. I also confirmed E-03's remedy works: `lane_work_has_landed` returns `False` for that
  branch, so the proposed condition does block it.
- F-02 reproduces: `prepare_lane_submission_dir` leaves the attempt directory PRESENT with zero files, so
  a directory-existence probe gets the common interrupted shape wrong and E-02's file-keyed probe is right.
- F-09 reproduces, and it is the subtlest claim in the plan. With `attempt-1/outcomes/01-aaaaaa.json` on
  disk and `attempt_key` returning 2, the attempt-keyed root does not exist (reads as "wrote nothing")
  while the whole-tree probe finds the file. The plan's insistence on the whole tree is correct and its
  framing is better than "more cautious": the attempt-keyed answer is WRONG about the question asked.
- F-07 reproduces in both directions, which is the measurement that makes E-02's precision load-bearing.
  With `.aw/state/` gitignored (this repo's real shape) the submission reports as `unknown_ignored` and
  clearing the submission bit yields `classified True`; in a repo ignoring nothing it reports
  `unknown_untracked` and yields `classified False`. So the untracked rule is genuinely not a backstop here.
- F-10, F-12 and F-13 verify: `lane_containment` imports `runner_shared` at module level (line 55),
  `lane_work_has_landed` is three-valued with `None` meaning unanswerable, no surviving test references
  `submission_retention`/`inventory_lane`/`teardown_lane_if_classified`, the new test file does not exist,
  and `aw find specs 7ckptx` still resolves to `specs/approved/`.

THE ONE HIGH FINDING IS A WRONG CALLER CENSUS, AND CORRECTING IT MAKES THE PLAN SIMPLER AND SAFER
(PR-001). E-03, the Scope check and V-03 all asserted that `runner_shared.reclaim_lanes_on_interrupt`
calls `inventory_lane` DIRECTLY in its probe loop without a branch, treating that as the plan's "most
likely surprise", requiring it be measured, and warning the executor to STOP if a caller change were
needed. Measured: `runner_shared` does not reference `inventory_lane` AT ALL (zero occurrences). There are
exactly THREE call sites and all three are inside `lane_containment` itself - one in
`teardown_lane_if_classified` and two in `teardown_review_sweep_lane` (a `probe` and a `final`). The
interrupt path reaches the gate through `reclaim_lane_through_gate`, a thin delegation passing
`repo`/`handle`/`run_dir`/`item`. So every caller that needs the branch ALREADY HOLDS THE HANDLE,
`handle.branch` is the documented accessor, and NO undeclared file needs editing. Left unfixed this would
have cost an execution pass hunting a call site that does not exist, with a live risk that the executor
widened scope into `runner_shared.py` to "fix" what it found. I also redirected V-03's evidence at the
surface that IS genuinely at risk under the corrected census: `teardown_review_sweep_lane` calls the
inventory twice and F-04 already records that it needed a workaround for this predicate, so a sweep lane
made permanently unretirable by the new condition would reintroduce the exact defect class this plan fixes.

THE SECOND FINDING WOULD HAVE CORRUPTED AN APPROVED SPEC'S ID SPACE (PR-002). E-01 said to add the new
requirement at "the next free id in that section" and the criterion "beside A15". Both would have been
guessed wrong: the R5 section already contains `R5.6` AND `R5.6a`, so the next free requirement id is
`R5.7`, and the Section 4 criteria already run to `A20` with lettered variants throughout (`A5b`, `A10e`,
`A15b`), so the next free is `A21` and not `A16`. An executor following the prose literally could have
written over an existing id, and V-01's own enumeration check would then have failed the item AFTER the
edit was made to an approved, release-blocking contract. E-01 now names both measured ids, requires
re-derivation at execution (another pending plan may take one first), and forbids renumbering to achieve
adjacency with A15.

WHAT I CHECKED AND LEFT ALONE, because a review that rewrites a sound plan is worse than one that does
not. The three open questions are all `resolved`, all non-blocking, and each is answered from a
measurement I reproduced, so none needed escalation and I added none. OQ-01's conclusion (E-02 and E-03
must ship together) is correct and is the plan's best judgement. OQ-02's conclusion (whole tree, not
attempt-keyed) is correct and its "strictly more conservative so it cannot be the unsafe choice" reasoning
is sound. OQ-03's conclusion (the amendment is required, and reading R2.5 as already permitting the
narrowing would be dishonest) is right, and the sentence it quotes really is the one the shipped code
cites in its own detail string, which I verified. The `chore` classification survives scrutiny for the
reason the gate already states: the SHIPPED behavior produces no wrong answer and no user-perceptible
latency, and the data-loss finding is a property of a fix not yet applied, so there is no live bug to gate
and inventing a `Blocks-Release` would be wrong. The deferral rows are unusually honest, including three
`Carrier-Declined` entries with real reasons and one that correctly declines to file a carrier because the
work is not owed until this plan's narrowing is accepted.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C (architecture) / G (executability) | `grep -rn "inventory_lane(" agent_workflows/` -> 3 call sites, all in `lane_containment` (`teardown_lane_if_classified`, and `probe`+`final` in `teardown_review_sweep_lane`); `grep -c inventory_lane agent_workflows/runner_shared.py` -> 0; `runner_shared.reclaim_lane_through_gate` body delegating with `repo`/`handle`/`run_dir`/`item`; `worktree_lease.lane_branch_name` docstring "read `handle.branch` instead" | **THE CALLER CENSUS IS WRONG, AND THE TRUTH IS SIMPLER AND SAFER.** E-03, the Scope check and V-03 each asserted that `runner_shared.reclaim_lanes_on_interrupt` calls `inventory_lane` directly in its probe loop without a branch, making E-03's blocking default a cross-module behavior change that had to be measured and might force a STOP. `runner_shared` does not reference `inventory_lane` at all; all three call sites are inside the declared module and each already holds the handle. An executor would have burned a pass hunting a nonexistent call site, with a live risk of widening scope into `runner_shared.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now states the measured census (three sites, all in `lane_containment`), notes `inventory_lane` is already keyword-only so the new parameter breaks no positional caller, says every caller already holds the handle via `handle.branch`, and forbids touching `reclaim_lane_through_gate` or `runner_shared.py`. The Scope check's second under-scope bullet is corrected in place. V-03's evidence is REDIRECTED from the nonexistent caller to the sweep-lane path that is genuinely at risk, requiring it be driven in both landed and unlanded states. The gate's STOP directive now notes it should not fire. New F-14. |
| PR-002 | MEDIUM | IN-SCOPE | A (correctness) / G | `grep -oE "^R5\.[0-9]+[a-z]*"` -> `R5.1 R5.1a R5.2 R5.3 R5.4 R5.5 R5.6 R5.6a`; `grep -oE "^- A[0-9]+[a-z]*"` -> through `A20` with lettered variants | **BOTH NEW SPEC IDS WOULD HAVE BEEN GUESSED WRONG, ON AN APPROVED RELEASE-BLOCKING SPEC.** E-01 said "the next free id in that section" and "beside A15". `R5.6` and `R5.6a` already exist so the next free requirement id is `R5.7`; the criteria run to `A20` so the next free is `A21`, not `A16`. Writing over an existing id would then have failed V-01's own enumeration check after the spec edit was already made, and other plans cite these numbers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 names `R5.7` and `A21` as the review-measured ids, requires re-derivation at execution with an explicit instruction to take the next free one and say so if taken, and forbids renumbering to make the criterion adjacent to A15 ("a correct id in the wrong position is fine, a renumbered id is a failed validation"). The Expected outcome names both ids. New F-15. |
| PR-003 | MEDIUM | IN-SCOPE | E (verification) | Review HEAD `406e73cf6`: bare `python3 -m pytest` -> `3527 passed, 2 skipped, 3 warnings`, 208 deselected, against the plan's recorded `3284 passed, 2 skipped` at HEAD `5b44c5d3` | **THE AUTHORED SUITE BASELINE HAS DRIFTED BY +243 AND THREE PLACES TREAT IT AS A BAR.** The Required-tests section, V-05 ("confirm the count ROSE from the authored baseline of `3284 passed, 2 skipped`") and the gate's honesty paragraph all quote the figure. An executor comparing against it would misread a legitimate, unrelated difference, and V-05's rise-check would be computed from the wrong origin. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three sites now state that the authored AND review figures are CONTEXT, record both with their HEADs, and make the bar the executor's own pre-edit measurement at its own HEAD. V-05's rise-check is re-anchored to "YOUR OWN pre-edit baseline". |
| PR-004 | LOW | IN-SCOPE | A | `LaneInventory(NamedTuple)` at `lane_containment.py`; `inventory_lane(*, lane_root, ...)` keyword-only signature | **TWO SHAPE FACTS AN EXECUTOR WILL HIT IMMEDIATELY WERE UNSTATED,** and both bear on E-03's mechanics. `LaneInventory` is a `NamedTuple` and not a dataclass (so field addition and any test-side substitution use `_replace`, not `dataclasses.replace` - I hit this myself reproducing F-05), and `inventory_lane` is already keyword-only (so E-03's new parameter is purely additive and breaks no positional caller). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states the keyword-only signature explicitly as the reason the addition is safe; F-16 records both facts with the reproduction that surfaced them. |
| PR-005 | LOW | IN-SCOPE | A / E | Independent reproduction of F-01, F-02, F-05, F-07 and F-09 at review HEAD | **THE PLAN'S MEASUREMENTS WERE ALL AUTHORING-TIME AND NONE HAD BEEN INDEPENDENTLY CONFIRMED,** which matters disproportionately here because the entire design (and the decision to add E-03 at all) rests on them, and because E-01 amends an approved spec on their strength. Not a defect in the plan; an absence of corroboration for an unusually consequential set of claims. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-16 records the independent reproduction of all five, including the verbatim F-01 detail string, the F-05 `classified True reason_codes ()` data-loss authorization with `lane_work_has_landed` returning `False`, F-02's present-but-empty attempt directory, F-09's attempt-keyed-versus-whole-tree divergence, and F-07's both-repo contrast. Every one reproduces. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan's caller census is wrong. Correct it in place, or raise it as a blocking question for the author? | CORRECT IT IN PLACE and redirect V-03's evidence at the real risk surface. | (a) Raise it blocking: REJECTED, the correction makes the plan STRICTLY simpler (no undeclared caller, no cross-module change, the branch already in hand), so there is no decision a human needs to arbitrate and blocking would hold a sound plan for a fact the repository answers. (b) Delete the undeclared-caller evidence requirement entirely: REJECTED, it was pointed at the wrong function but the UNDERLYING concern (a new blocking condition changing a caller's verdict) is real and lands on `teardown_review_sweep_lane`, which calls the inventory twice and already needed a workaround for this very predicate. | Measured: zero `inventory_lane` references in `runner_shared`; three call sites all in `lane_containment`; `reclaim_lane_through_gate` delegates with the handle; `handle.branch` is the documented accessor per `worktree_lease.lane_branch_name`'s docstring. | yes |
| D-2 | E-01's new spec ids are specified as "next free" and "beside A15", both of which resolve wrongly. Name them, or leave the executor to derive them? | NAME the measured ids (`R5.7`, `A21`) AND require re-derivation at execution. | (a) Leave "next free": REJECTED, it is what would have produced `R5.6` (taken, with an `R5.6a` variant) or `A16` (taken), i.e. an overwritten id on an approved release-blocking spec. (b) Name them and treat them as fixed: REJECTED, another pending plan may take an id first, so a hard-coded id is the live-artifact mistake in the other direction; the instruction is to take the next free and SAY SO. | Full id enumeration at review: R5 runs to `R5.6`/`R5.6a`; criteria run to `A20` with lettered variants (`A5b`, `A10e`, `A15b`). V-01 already enumerates ids before and after, which is what makes a wrong guess a failed validation rather than a silent corruption. | yes |
| D-3 | Should any of the three resolved open questions be re-opened or escalated? | NO. All three stay `resolved` and non-blocking. | Re-opening OQ-01 (ship E-02 alone, as the backlog item asks): REJECTED, I reproduced the data-loss authorization myself, so the plan's answer is measured fact rather than preference. Escalating OQ-02 or OQ-03 to the maintainer: REJECTED, both are answered decisively by repository evidence (the attempt-key divergence and R2.5's own cited sentence), and the workflow forbids asking a human what the repository already answers. | F-05/F-06 reproduced: clearing the submission bit alone yields `classified True reason_codes ()` and `lane_work_has_landed` returns `False`; F-09 reproduced; R2.5's sentence confirmed as the one `submission_retention` cites in its returned detail string. | yes |
| D-4 | Verdict and readiness, given one HIGH finding now fixed and no blocking open questions. | `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`. | `REJECT - NEEDS REPLAN`: REJECTED, the design is sound and every finding was repairable with bounded edits to prose and evidence requirements; no mechanism needed rethinking. `REVIEWED - OPEN QUESTIONS`: REJECTED, all three OQs are `resolved`. Bare `NO-GO`: REJECTED, the workflow reserves it for genuine not-ready conditions and says a reviewed clean plan awaiting sign-off is `GO - PENDING HUMAN APPROVAL`. | Workflow readiness vocabulary; zero findings left OPEN or DEFERRED at or above the `high` gate threshold, so no escalation to a `Blocking: yes` question is owed; `aw ipd lint` clean at `author` and `review-finalize`; `aw check plans` reports no finding naming `z8ex9f`. | yes |
