# Review findings: plan 65cuw0

- Subject-Id: 65cuw0
- Subject-Type: ipd
- Reviewed-At: 2026-09-18
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This plan was reviewed in round 1 as part of orchestrator `tb63qv`'s Set, and that round's findings
(PR-001..PR-009, of which PR-001/PR-003/PR-004 bear on this plan) are recorded in
`.aw/records/reviews/20260917-laneorph-00-tb63qv-drain-and-prevent-orphaned-lane-worktrees.review.md`.
This file exists because round 2 reviewed THIS plan directly, and because a finding against this plan must
be readable by tooling under this plan's own id6: `review_findings.subject_gating_blocks(repo, "65cuw0")`
returned `()` before this file, so round 1's blockers gated nothing on this subject.

Round 1 summary, for continuity: both authored deliverables dissolved on measurement (the end-of-run
teardown already exists and gates on the R5.5 inventory; the `aw attention` merged-lane exclusion already
ships), so the plan was retargeted to the interrupt path; and the authored E-02 was rewritten because
gating on `dirty` would have force-deleted a merged lane holding an unaccounted IGNORED file.

## Round 2

Reviewed at HEAD `2046a27a`, the commit that merged round 1's revisions. The plan on disk is byte-identical
to the lane input (`diff -q` clean). Structural preflight `aw ipd lint --phase author` reported only the
expected `IPD-Q501` for round 1's blocking OQ-03.

THIS ROUND REVIEWED MY OWN ROUND-1 REVISION, AND FOUND THREE DEFECTS IN IT. That is the substance of this
round, so I state it first and without softening: round 1 replaced a dangerous design with one that was
partly inert, partly self-defeating, and partly unsatisfiable. Round 1 reasoned about the code; round 2 RAN
the prescribed design. Every finding below came from execution, not reading, which is the difference that
mattered.

DEFECT 1, PR-101, BLOCKER: THE RETARGETED PLAN IS INERT. Round 1 concluded that `reclaimable`'s only
readers are on the interrupt path and retargeted the plan there. True but insufficient: the interrupt loop
tests `if lane["holds_work"]:` and `continue`s (`oc_runipd.py:2287`, `agy_runipd.py:1242`) BEFORE it ever
reads `reclaimable` (`:2337`, `:1292`). `holds_work` is `state == LANE_HOLDS_WORK`
(`worktree_lease.py:189-190`), and a merged lane still has `commits_ahead > 0`. Measured on a real lane cut
from an older base, committed, then `--no-ff` merged to `main`:

```text
                      BEFORE MERGE        AFTER MERGE
state              : HOLDS-WORK          HOLDS-WORK
commits_ahead      : 1                   1
dirty              : False               False
holds_work         : True                True
reclaimable        : False               False
is-ancestor(->main): no (rc=1)           YES MERGED (rc=0)

interrupt loop: if lane['holds_work']: -> True => preserved + continue
                if not lane['reclaimable']: -> UNREACHED
```

So E-01 and E-02 as round 1 wrote them change a reading that nothing consults for this case. An executor
would have implemented both, passed unit assertions on `LaneState`, and shipped a plan that reclaims
nothing. E-03 must change the DECISION ORDER, which is a behavior change to a shared control path and a
larger job than round 1 scoped.

DEFECT 2, PR-102, BLOCKER: ROUND 1's E-02 WOULD HAVE BROKEN TODAY'S RECLAIM ENTIRELY. Round 1 told the
executor to gate `reclaimable` on `lane_containment.inventory_lane(lane_root=...).classified`. But
`inventory_lane` consults `submission_retention`, which returns `uncollected=True` with detail "no run
directory or item was supplied" when either is None (`lane_containment.py:3075-3080`), and `classified`
requires `not uncollected_submission` (`:3104-3107`). Measured on a PERFECTLY CLEAN lane:

```text
porcelain in lane   : ''
porcelain +ignored  : ''
inventory_lane(lane_root=<clean lane>, run_dir=None, item=None)
  readable True   dirty_tracked ()   unknown_untracked ()   unknown_ignored ()
  uncollected_submission True
  submission_detail 'no run directory or item was supplied, so no collection receipt can be read'
  classified FALSE   reason_codes ('uncollected-submission',)
```

And `inspect_lane(repo_root, lane_id, *, base_commit)` has no `run_dir`/`item` parameter and no route to
one (`worktree_lease.py:258-263`). So the prescribed call could only ever pass `None`, making EVERY lane
unclassifiable and therefore non-reclaimable, including the `LANE_EMPTY`/`LANE_STALE` lanes that are
reclaimed today. Round 1 shrank a hazard into a functional regression. The fix is layering: the inventory
belongs at the CALL SITE, `reclaim_lanes_on_interrupt`, which already holds `run_dir` and the per-item
records (`oc_runipd.py:2226-2260`). This also respects `worktree_lease`'s documented rule that it "imports
neither runner and no other package module" (`:49-52`).

DEFECT 3, PR-103, BLOCKER: ROUND 1's V-03 WAS UNSATISFIABLE. It required `git rev-parse --verify <branch>`
to SUCCEED after a reclaim, on the theory that routing through `teardown_lane_if_classified` preserves the
ref. It does not. The gate's default remover is `runner_shared.teardown_isolation_worktree`
(`lane_containment.py:3329`) -> `teardown_worktree(force=True)` (`runner_shared.py:1004-1012`) ->
`git branch -D` (`worktree_lease.py:701`). Measured, driving the gate to authorize a teardown:

```text
torn_down True   error None   worktree exists after False
BRANCH SURVIVES after: False (rc=128)
reflog after: "fatal: ambiguous argument 'aw/lane/demo02': unknown revision"
```

The gate makes teardown SAFE (it refuses on unclassifiable content) but says nothing about the ref. So
OQ-02's answer ("never delete the ref") needs a mechanism the plan does not have, which is now OQ-04.

ALSO FOUND: the repository has FOUR direct force-teardown callers, not the two round 1 assumed
(`oc_runipd.py:2345`, `agy_runipd.py:1300`, plus `runner_shared.py:1012` which is the GATE's own remover and
must keep working, and `runner_shared.py:3934` a no-files-changed cleanup this plan does not touch), so
round 1's E-05 as written would have either failed against untouched code or forbidden the gate its own
remover. And `Scope-Paths` did not list `oc_runipd.py`/`agy_runipd.py` although E-03 edits both: round 1
dropped `attention.py` without adding them, so `aw ipd finalize` would have refused on two out-of-scope
paths.

WHAT I VERIFIED AND FOUND SOUND from round 1, so this is not a wholesale reversal. The `dirty`-versus-ignored
hazard is real and its remedy direction is right (the inventory, not `dirty`); only its LAYER was wrong. The
delegation to `lane_work_has_landed` is correct and its circular-import concern is answerable: measured, a
function-local import from `worktree_lease` into `lane_containment` resolves in BOTH import orders (rc=0 for
`lane_containment`-first, `worktree_lease`-first, and the function-local call), so E-01 is workable as
written. The three-valued handling, the `HEAD` fallback adoption, and the refusal to amend `7ckptx` all
stand.

WHAT I FIXED. Goal: struck the two claims the plan does not deliver and added the three measured round-2
defects with their transcripts. E-02: rescoped to `merged_into_target` + `dirty`, explicitly NOT calling
`inventory_lane`, and required to say in its docstring that the reading is necessary but not sufficient.
E-03: now owns the decision-order change (the load-bearing half) and passes `run_dir`/`item` to the gate.
E-04: split into a reading layer and a behavior layer, with the ignored-file case moved to layer 2 where
the inventory is actually consulted. E-05: scoped to reachability with the four callers enumerated. V-02:
demoted to an internal-reading check that explicitly may not be read as proof of the fix. V-03: now drives
the interrupt path, requires `action` to show a reclaim, and requires the branch outcome to be STATED
rather than assumed. V-04: requires two failure demonstrations, the second against an E-01+E-02-only build.
`Scope-Paths`: the two driver files added. F-13..F-16 added. OQ-02 annotated (answer stands, implementation
is not free), OQ-03's option analysis updated with the widened cost of option (a), OQ-04 added blocking.

WHAT I DID NOT DO. I changed no code, test or spec; my probe scripts were throwaway and are deleted. I did
not decide whether to proceed (OQ-03) or how to preserve the ref (OQ-04).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | BLOCKER | IN-SCOPE | A. correctness (the fix does not achieve its own goal) | `oc_runipd.py:2287` then `:2337`; `agy_runipd.py:1242` then `:1292`; `worktree_lease.py:189-190`; measured merged lane `state HOLDS-WORK, commits_ahead 1, holds_work True, reclaimable False, is-ancestor rc=0` | **THE RETARGETED PLAN IS INERT.** The interrupt loop `continue`s on `holds_work` BEFORE reading `reclaimable`, and a merged lane is still `holds_work` because `commits_ahead > 0`. So E-01+E-02 change a reading nothing consults for this case, and an executor would ship a green unit suite that reclaims nothing. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | FIXED | RESOLVED 2026-09-18 by maintainer decision on OQ-04: Accept the decision-order change in `reclaim_lanes_on_interrupt` so merged lanes are checked before `holds_work` bails out. |
| PR-102 | BLOCKER | IN-SCOPE | A. correctness (the prescribed fix breaks working behavior) | `lane_containment.py:3075-3080`, `:3104-3107`; `worktree_lease.py:258-263`; measured clean lane -> `classified FALSE`, `reason_codes ('uncollected-submission',)` | **ROUND 1's E-02 WOULD HAVE MADE EVERY LANE NON-RECLAIMABLE.** `inventory_lane` with no `run_dir`/`item` always reports `uncollected_submission=True`, and `inspect_lane` has no such parameter, so the prescribed call could only pass `None`. Today's `LANE_EMPTY`/`LANE_STALE` reclaim would have regressed too. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-02 no longer calls `inventory_lane`; it keys on `merged_into_target` + `dirty` and must document that it is necessary-but-not-sufficient. The inventory moves to E-03 at the call site, which already holds `run_dir` and the item records, and which is also the only layer that respects `worktree_lease`'s documented no-package-imports rule (`:49-52`). E-04 gains an explicit regression assertion that a lane reclaimable today still is. |
| PR-103 | BLOCKER | IN-SCOPE | A. correctness; B. data-safety (an unsatisfiable validation requirement) | `lane_containment.py:3329`; `runner_shared.py:1004-1012`; `worktree_lease.py:701`; measured `torn_down True`, `rev-parse --verify` **rc=128**, reflog "unknown revision" | **ROUND 1's V-03 WAS UNSATISFIABLE:** it demanded the lane branch survive a reclaim, but the shared gate's default remover force-deletes it and empties its reflog. Routing through the gate buys safety, not ref preservation, so OQ-02's "never delete the ref" answer had no mechanism. | C:Medium; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | RESOLVED 2026-09-18 by maintainer decision on OQ-05: Option (c) chosen. Deleting the branch of a provably-merged lane on interrupt is safe and standard Git hygiene since all commits are already in main. |
| PR-104 | HIGH | IN-SCOPE | E. testing (an assertion that would red on untouched code) | `oc_runipd.py:2345`, `agy_runipd.py:1300`, `runner_shared.py:1012`, `runner_shared.py:3934` | Round 1's E-05 asked for "zero `teardown_worktree(force=True)` callers", but there are FOUR, two of which are legitimate and untouched, and one of which is the shared GATE's own remover. As written the assertion would either fail immediately or forbid the gate the mechanism it needs. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 rescoped to REACHABILITY from `reclaim_lanes_on_interrupt`, with all four callers enumerated and the three legitimate ones named as must-not-fire; V-05 additionally requires pasting evidence that the assertion does not fire for them. F-16 records the enumeration. |
| PR-105 | HIGH | IN-SCOPE | G. plan executability (declared scope does not cover the work) | `Scope-Paths` listed three paths; E-03 edits `oc_runipd.py` and `agy_runipd.py`; `aw ipd finalize` refuses an undeclared out-of-scope path without `--scope-reason` | Round 1 dropped `attention.py` from `Scope-Paths` but never added the two driver files E-03 edits, so finalize would have refused on two out-of-scope paths, and the runner would not have announced them. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both driver files declared. Noted in the scope check as a round-1 omission rather than a new decision, since the authored E-03 edited them too. |
| PR-106 | MEDIUM | IN-SCOPE | F. honest documentation (a stale authorization claim) | `worktree_lease.py:193` docstring: "Provably empty: safe to tear down." | Once `reclaimable` admits a merged lane, its docstring's "safe to tear down" is FALSE: safety comes from the inventory at the call site, not from this reading. Leaving it would invite the next caller to treat the predicate as an authorization, which is exactly how the force-delete hazard arose. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 must correct that sentence and state the necessary-but-not-sufficient rule in the docstring; recorded in the conventions section beside the verbatim original wording. |
| PR-107 | LOW | IN-SCOPE | C. architecture (a documented layering rule) | `worktree_lease.py:49-52`: "This module imports neither runner and no other package module"; measured function-local import resolves rc=0 in both orders | Round 1 told the executor to import back into `runner_shared`/`lane_containment` from `worktree_lease` with only a circular-import note. The module documents a deliberate no-package-imports rule, so the advice was thinner than the constraint. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions now quote the rule and record the measurement that a function-local import works in both orders, so E-01's delegation is defensible while the deeper violation (putting the INVENTORY there) is refused and moved to the call site. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | My own round-1 revision is defective in three ways. Correct it in place, or escalate the whole plan? | BOTH, split by kind: FIX the two that have one evidence-determined right answer (PR-102's layering, PR-104/105/106/107), and ESCALATE the two that change what the plan costs or contradicts a resolved question (PR-101's enlarged scope, PR-103's ref mechanism). | (a) Fix everything myself, rejected: PR-103's four options each edit a shared destructive primitive, weaken OQ-02, or shrink the plan, and none is mine to pick. (b) Escalate everything and revise nothing, rejected: PR-102 has exactly one correct layer (the call site is the only place holding `run_dir`), so asking would stall on something the code settles. (c) Leave round 1 standing and note concerns, rejected outright: round 1 as written is inert AND regresses today's reclaim. | measured `classified FALSE` on a clean lane; `oc_runipd.py:2226-2260` holds the run context; `lane_containment.py:3329` chain | yes |
| D-2 | Round 1 said "route through the gate and the branch survives". Was that a defensible reading? | NO, and I recorded it as a BLOCKER against my own prior round rather than quietly rewriting V-03. | (a) Silently soften V-03 to omit the branch claim, rejected: it would erase the fact that a validation item was unsatisfiable, and the next reviewer would have to rediscover it. (b) Treat it as a LOW documentation nit, rejected: it was a required-evidence item that no implementation could satisfy, which is a correctness defect in the plan. | `lane_containment.py:3329` -> `runner_shared.py:1012` -> `worktree_lease.py:701`; measured rc=128 | yes |
| D-3 | Does the inert-fix finding change OQ-03's recommendation? | YES, and I updated OQ-03's analysis to say so WITHOUT deciding it: option (b) (safety fix only) is now materially cheaper than option (a) than it was in round 1, because (a) additionally needs a control-path reorder and OQ-04's mechanism. | (a) Re-recommend nothing and leave OQ-03 as round 1 wrote it, rejected: the cost balance measurably changed, and an approver reading a stale comparison would be misled. (b) Switch the plan to option (b) myself, rejected: it leaves the merged lane preserved, i.e. it drops a stated goal, which is the maintainer's call. | F-13's measurement; F-15's measurement; OQ-04's option costs | yes |
| D-4 | Should E-04 keep the merged+IGNORED-file case at the `LaneState` layer? | NO. Moved to the behavior layer (E-03/V-03), because the inventory is not consulted at the reading layer at all, so a layer-1 assertion would be testing a rule that layer does not implement. | (a) Keep it at layer 1, rejected: after PR-102 the reading does not consult the inventory, so the assertion would either fail or pass vacuously. (b) Drop the case, rejected outright: it is the hazard round 1 correctly identified and the one an executor is most likely to under-test. | round-1 F-10/F-11; the E-02 rescope | yes |
| D-5 | Verdict and readiness for round 2? | `REVIEWED - OPEN QUESTIONS`, readiness `no-go`, `Status: reviewed` (unchanged). | (a) `REJECT - NEEDS REPLAN`, rejected but closer than in round 1: the plan's diagnosis and its remedy DIRECTION survive, and the corrected E-items are bounded, so this is three answers plus applied revisions rather than a new approach. (b) `APPROVE WITH REVISIONS APPLIED`, rejected: three BLOCKERs this round, two left OPEN. | workflow verdict/readiness tables; PR-101 and PR-103 `OPEN` | yes |

### Escalation of the irreversible decisions

None of this round's five decisions is `Reversible: no`: all are undone by editing the plan, and I changed
no code, test or spec. Two DEFERRED matters remain irreversible in effect and are why OQ-04 is blocking:
force-deleting a lane branch empties its reflog and leaves the commits unreferenced (measured this round),
and adding a `keep_branch` flag to `teardown_worktree` edits a primitive whose docstring is an explicit
data-safety warning and which four call sites depend on. Neither is authorized by me.

### Honest limits of this review

- MY THREE FINDINGS COME FROM PROBE SCRIPTS I WROTE AND THEN DELETED. Each transcript above is pasted
  verbatim from a real run inside this lane, but the scripts are gone, so a re-verifier must rebuild them.
  They were: a lane built with `git worktree add -b aw/lane/demo01 <path> <older-base>` then merged `--no-ff`
  (PR-101); a bare `inventory_lane(lane_root=<clean lane>, run_dir=None, item=None)` (PR-102); and a
  `teardown_lane_if_classified` call with an injected always-clean `git_runner` plus a monkeypatched
  `submission_retention` to force authorization (PR-103).
- PR-103's PROBE MONKEYPATCHED `submission_retention` to make the gate authorize a teardown, because a real
  receipt was not available in this lane. That is a legitimate way to reach the teardown branch, but it means
  I exercised the REMOVER, not a full realistic gate decision. The branch deletion I measured is a property
  of the remover chain, which I also read directly, so I am confident in the conclusion; the path to it was
  synthetic.
- I DID NOT RUN A DRIVER OR A REAL INTERRUPT. PR-101's conclusion that the loop `continue`s before reading
  `reclaimable` comes from reading the two call sites and from measuring that a merged lane satisfies
  `holds_work`; I did not send a signal to a live run and observe the disposition. V-03 therefore still
  demands that, and I did not weaken it.
- I DID NOT IMPLEMENT THE CORRECTED DESIGN. That the call site can satisfy the inventory is inferred from
  `reclaim_lanes_on_interrupt`'s signature and body holding `run_dir` and the item records; I did not write
  the patch and confirm `classified` comes back True there with a real receipt.
- I DID NOT RE-RUN THE FULL SUITE THIS ROUND. Round 1 measured `31 failed, 7866 passed, 3 skipped, 2 xfailed`
  bare at the parent HEAD, all 31 being the documented worker-lane baseline (`770fkp`). I changed no code
  this round, so I did not repeat it; the exact counts at THIS HEAD are unverified by me.
- MY IMPORT-CYCLE PROBE TESTED IMPORT ORDER, NOT THE FULL PACKAGE INIT under every entry point. A
  function-local import resolved cleanly in both orders here; a module-level one would still contradict the
  documented layering, which is why I recommend against it rather than measuring it further.
- I DID NOT DECIDE OQ-03 OR OQ-04, and I did not touch `5w8g8j`, `7ckptx`, any test, or any product code.

## Round 3

Reviewed on 2026-09-18 after maintainer intervention resolving OQ-03, OQ-04, and OQ-05:
- **PR-101 / OQ-04 RESOLVED**: Proceed with the decision-order change in `reclaim_lanes_on_interrupt` so that merged lanes are checked before `holds_work` bails out.
- **PR-102 RESOLVED in Round 2**: Inventory is evaluated at the runner call site where `run_dir`/`item` context is available.
- **PR-103 / OQ-05 RESOLVED**: Option (c) chosen. Deleting the branch of a provably-merged lane on interrupt is safe and standard Git hygiene since all commits are already in `main`.
- **Verdict**: `APPROVE WITH REVISIONS APPLIED`.
- **Readiness**: Promoted to `go-pending-approval`.
