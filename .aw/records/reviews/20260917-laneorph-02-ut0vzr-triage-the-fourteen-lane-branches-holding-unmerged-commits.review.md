# Review findings: plan ut0vzr

- Subject-Id: ut0vzr
- Subject-Type: ipd
- Reviewed-At: 2026-09-18
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Round 1 reviewed this plan as part of orchestrator `tb63qv`'s Set, and its findings (PR-001..PR-009, with
PR-002 and PR-005/PR-006 the ones bearing on this child) live in
`.aw/records/reviews/20260917-laneorph-00-tb63qv-drain-and-prevent-orphaned-lane-worktrees.review.md`. They
are NOT restated here. This file exists because round 2's scope is `ut0vzr` ALONE, and the reviews tree keys
a record to the reviewed artifact's own id6.

Round 1's verdict for this plan was `REVIEWED - OPEN QUESTIONS` with readiness `no-go`, on one blocking
finding (PR-002, escalated as this plan's OQ-04).

## Round 2

Reviewed at HEAD `73c69273` in an isolated review lane, with the plan byte-identical to the lane input, so
no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author` reported only the
`IPD-Q501` for round 1's blocking OQ-04 before revision; `--phase review-finalize` CONFORMS after, with no
findings at all, because this round resolves that question rather than adding another.

**I RETRACT ROUND 1's BLOCKER. IT IS FALSE, AND I MEASURED RATHER THAN RE-READ.**

Round 1 (PR-002 -> OQ-04) asserted that deleting a DELETE branch does not silence its `aw attention` row but
converts it into an equally-failing `attention.lane-unknown` row, so E-07 would perform 13 irreversible
deletions to reach an end state E-08 could never accept. It forbade the whole DELETE half on that basis. Each
link in its chain is individually true and the chain is never traversed, because the landing question is the
THIRD arm of a three-way decision and `holds_work` is tested first (`runner_shared.py:1163-1176`):

```text
if live:                              -> LANE_LIVE
elif not described.get("holds_work"): -> LANE_EMPTY_OF_WORK      <- a deleted branch lands HERE
else:                                    ... lane_work_has_landed(...) -> LANDED / STRANDED / UNKNOWN
```

A deleted branch makes `inspect_lane` return `LANE_ABSENT` (`worktree_lease.py:332-346`), whose `holds_work`
property is `False` (`:190-191`), so the second arm fires and `lane_work_has_landed` is NEVER CALLED.
`LANE_EMPTY_OF_WORK` is absent from `LANE_ATTENTION_STATES` (`runner_shared.py:1068`), so the row goes
silent. Measured end to end on a scratch repository built through the real `allocate_worktree`, with the
lane owner record cleared so the lane is not classified `LIVE`:

```text
1. BRANCH PRESENT (the stranded condition E-07 acts on)
    lane_state=STRANDED  landed=False  holds_work=True  ahead=1
    needs_attention=True  ->  attention.lane-stranded
2. WORKTREE REMOVED, BRANCH KEPT (today's state for ten of the twelve)
    lane_state=STRANDED  landed=False  holds_work=True  ahead=1
    needs_attention=True  ->  attention.lane-stranded
3. BRANCH DELETED (what E-07 would do)
    lane_state=EMPTY  landed=None  holds_work=False  ahead=0
    needs_attention=False  ->  NOT REPORTED (state not in LANE_ATTENTION_STATES)
```

The `LANE_UNKNOWN` state is real and does fail closed exactly as its docstring says. It is reached by an
UNRESOLVABLE TARGET, not by a missing branch, and the repository's own test says so: the only test that
produces it passes `target="refs/heads/no-such-target"` (`tests/test_runner_shared.py:4014-4019`).
Conflating the two `None` producers of `lane_work_has_landed` is the whole error. Round 1 cited
`runner_shared.py:1093-1096` (the `rev-parse --verify` failure returning `None`) correctly, and then assumed
a caller that never runs.

WHY THIS MATTERED ENOUGH TO SPEND A ROUND ON. The false finding was not merely noise: it BLOCKED the
plan's entire purpose. `qliia1` is a `high`-priority open backlog item, twelve branches carrying 40 commits
sit unresolved, and round 1's gate said the deletions "may not" proceed pending a maintainer answer to a
question with four options, two of which (prune run records, add a public `DISPOSITIONED` classifier state)
would have expanded the Set. Left standing it would have cost a maintainer round trip and possibly a new
plan, to fix a defect that does not exist.

**ROUND 1's F-11 IS ALSO FALSE.** It claimed `aw attention` cannot be measured from inside a lane because
`stranded_lane_drift` returns `[]` with no run records and `.aw/records/runs/` is gitignored hence absent
there, so an in-lane check is a false clean. But `_resolve_runs_repo_root` (`attention.py:2029-2050`) exists
precisely to handle this and deliberately walks `.aw/worktrees/` parents to the owning checkout. Measured
FROM this review lane, whose own `.aw/records/runs/` genuinely does not exist:

```text
this tree         : review-sweep-run-20260917T231229Z-2701568
resolved runs root: agent-workflows
stranded_lane_drift rows from INSIDE this lane: 19
by rule: {'attention.lane-stranded': 19}
distinct lanes: 12
severities: {'error': 19}
```

Nineteen rows, not zero. I kept the measuring-tree discipline for `git worktree list`, which really is
per-tree (measured: 7 entries from the main checkout), and downgraded it for `aw attention` from a
correctness gate to a naming convention.

**THE INVENTORY MOVED UNDER THE PLAN BETWEEN ROUNDS, WHICH IS THE MOST OPERATIONALLY USEFUL FINDING HERE.**
`upgtest` was the plan's one RECOVER case, settled by the maintainer in OQ-03 as "DO NOT DELETE. PRESERVE and
assess for recovery". That recovery HAS HAPPENED: `9476b48b` (2026-09-17) merged it to `main`, its message
reading "the last lane holding work that existed NOWHERE in main" and recording per-artifact verification of
all eight recovered artifacts, zero `git merge-tree` conflicts, `61 passed` on the new suite and `7968
passed` on the full one. Measured now: `git merge-base --is-ancestor aw/lane/upgtest main` -> 0, and
`git rev-list --count aw/lane/upgtest --not main` -> 0. It is also absent from `stranded_lane_drift`. So the
inventory is 12 branches / 40 distinct / 91 summed, not round 1's 13 / 43 / 94, and E-05's ESCALATE list is
now expected EMPTY (the only branch with no owning plan is gone).

That same merge commit also hands E-04 two of its seven verdicts on a plate: it records that `fn2l1u` and
`r2i1b1` were examined and their work "turned out to be in main already under renamed symbols: ItemRefusal
-> Refusal, item_refusal -> refusal_of_item, history_actor -> actor_refusal", with both branches KEPT and
their worktrees removed. All three renamed symbols verified present at review round 2 (`render_stream.py:1830`,
`render_stream.py:1926`, `attention_contract.py:618`), which is precisely the ancestry-or-content evidence
E-02's rule demands and E-04 would otherwise have re-derived.

WHAT I RE-VERIFIED AND FOUND UNCHANGED, so the executor does not re-do it: all six `wtiso` plans still carry
a `RETIRED 2026-09-02:` header (extracted from each file, including `6knsrx`); `6knsrx` still has no branch;
all seven `executed`-plan branches (`nna8yz`, `03ie04`, `d7qoxv`, `fn2l1u`, `mm5p3v`, `r2i1b1`, `ybkmzp`) are
still `executed`; `nna8yz`'s landing site `lane_containment.py` is present with `materialize_lane_inputs` at
`:2140`; the shared-ancestry proof still holds (`merge-base --is-ancestor aw/lane/58ha43 aw/lane/2c122z` ->
0) and the `wtiso` union is still 26, identical to `2c122z` alone; and the four `_attempt2` branches
(`d7qoxv_attempt2`, `fn2l1u_attempt2`, `mm5p3v_attempt2`, `r2i1b1_attempt2`), which no round of this review
had checked, are all 0 commits ahead of `main` and therefore need no disposition.

THE SUITE BASELINE IS NOT WHAT ROUND 1 ASSUMED EITHER. Measured bare with `env -u AW_EXECUTION_ROLE`:
`1 failed, 7974 passed, 3 skipped, 2 xfailed in 236.19s`. The single failure is
`tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`,
and it is a LOAD-DEPENDENT FLAKE rather than a role refusal or a regression: re-run in isolation it gives
`1 passed, 46 deselected`. Round 1's required-tests wording said "bare and green" and attributed a failing
set to the worker-role refusals (backlog `770fkp`), which would have had an executor either chasing a
non-defect or dismissing a real one.

WHAT REMAINS SOUND AND SURVIVED WHOLESALE, stated because this round is otherwise a list of corrections: the
plan's evidence-first design is right and is its best feature. Record before act (E-06 before E-07), RECOVER
before DELETE, cite an existing retirement rather than re-deciding it, forbid a commit-subject match as
landing evidence, name ONE merged-ness predicate rather than hand-rolling git, and refuse to guess a
disposition to make a table look complete. The `nna8yz` counter-example is exactly the right thing to have
found, and OQ-03's method correction (an earlier triage misclassified `upgtest` by grepping subjects, and the
grep matched the lane's own commit) is the kind of finding that prevents a wrong irreversible act.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | BLOCKER | IN-SCOPE | A. correctness (a false blocker gating real work) | `runner_shared.py:1163-1176` (decision order), `worktree_lease.py:332-346` and `:190-191` (`LANE_ABSENT.holds_work` is False), `runner_shared.py:1068` (`LANE_EMPTY_OF_WORK` not in `LANE_ATTENTION_STATES`), `tests/test_runner_shared.py:4014-4019` (the real `LANE_UNKNOWN` trigger is an unresolvable TARGET); measured three-case table on a scratch repo through the real allocator | **ROUND 1's BLOCKER IS FALSE: DELETING A BRANCH DOES SILENCE ITS ATTENTION ROW.** The landing question sits in the third arm of a three-way decision and a deleted branch is caught by the second (`not holds_work`), yielding `LANE_EMPTY_OF_WORK`, which is not reportable. `lane_work_has_landed` is never called. So E-08's criterion is reachable as originally authored, and round 1 blocked the plan's entire purpose on a defect that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-04 resolved NO-OP with the measured table and the decision-order quote; F-9 struck through and replaced with the retraction plus evidence; the Goal's second premise rewritten; the gate's prohibition on the DELETE half LIFTED; E-07's prediction requirement KEPT but re-aimed at predicting silence, so the same class of error would be caught from the other direction. |
| PR-102 | HIGH | IN-SCOPE | A. correctness (a stale inventory would authorize a wrong act) | `git merge-base --is-ancestor aw/lane/upgtest main` -> 0; `git rev-list --count aw/lane/upgtest --not main` -> 0; merge commit `9476b48b` (2026-09-17); `stranded_lane_drift` no longer lists it; recount `git rev-list --count <12> --not main` -> 40, per-branch sum 91 | **THE PLAN'S ONE RECOVER CASE HAS ALREADY BEEN RECOVERED, AND THE INVENTORY IS NOW 12 / 40 / 91.** `upgtest` was merged to `main` between review rounds, so OQ-03's action item is discharged, the branch needs no disposition, and every count in the plan (including round 1's corrected 13 / 43 / 94) is stale. A plan that names a branch which has since landed risks an executor "recovering" it twice. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern, Goal, F-1 (plus new F-1a), F-7, E-01, E-03, E-05, V-01 and the H1 title all corrected to 12 / 40 / 91 with `upgtest` recorded as already-recovered and `9476b48b` cited. E-01 now carries an explicit warning that the inventory is a moving target and HAS moved once, so no list in the document may be trusted over a fresh measurement. |
| PR-103 | HIGH | IN-SCOPE | E. testing (a measurement discipline built on a false mechanism) | `attention.py:2029-2050` (`_resolve_runs_repo_root` walks out of `.aw/worktrees/`); measured from this lane: resolved runs root = main checkout, 19 rows / 12 distinct lanes; `git worktree list` -> 7 entries from the main checkout | **ROUND 1's F-11 IS FALSE: `aw attention` MEASURES CORRECTLY FROM INSIDE A LANE.** The `[]`-on-no-run-records path is real but is reached only when the OWNING checkout has no runs; the resolver exists precisely to handle a lane. Round 1 turned this into a correctness gate on E-01, E-08, V-01 and V-08, which would have made an executor believe a valid measurement was worthless. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 struck through with the resolver cited and the 19-row measurement pasted; E-01, E-08, V-08 and the required-tests item now require only that the tree be NAMED, while keeping the main-checkout requirement for `git worktree list`, which genuinely is per-tree. |
| PR-104 | MEDIUM | UNDER-SCOPE | E. testing (a baseline an executor cannot meet) | measured `1 failed, 7974 passed, 3 skipped, 2 xfailed`; the same test in isolation `1 passed, 46 deselected` | **THE REQUIRED-TESTS ITEM SAID "BARE AND GREEN" AND MISATTRIBUTED THE FAILURE.** The suite is not green: one test fails under load and passes in isolation. Round 1 attributed a failing set to the worker-role refusals, so an executor would either "fix" a flake or dismiss a genuine failure as expected. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The measured baseline written into the required-tests item and into V-07, with the flake NAMED, its isolation result recorded, an instruction not to "fix" it, and the gate changed from "green" to NO NEW failures against a same-tree baseline. |
| PR-105 | MEDIUM | UNDER-SCOPE | A. correctness (evidence already on `main` that E-04 would re-derive) | `9476b48b` message; `render_stream.py:1830` (`Refusal`), `render_stream.py:1926` (`refusal_of_item`), `attention_contract.py:618` (`actor_refusal`) | **TWO OF E-04's SEVEN VERDICTS ARE ALREADY ESTABLISHED ON `main` AND THE PLAN DOES NOT SAY SO.** `9476b48b` records that `fn2l1u` and `r2i1b1` were examined and their work is in `main` under three renamed symbols, all three of which I verified present. Without the pointer E-04 repeats the analysis, and a renamed symbol is exactly the case a careless check would miss and mark RECOVER. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now names the commit, quotes the three renames, states they were verified at review, and instructs the executor to CITE and confirm rather than re-derive; its expected outcome and V-04 both require that citation or an evidenced correction of it. |
| PR-106 | MEDIUM | UNDER-SCOPE | G. executability (missing execution-contract elements) | the authored gate had the irreversibility bar, worktree, path-scoped-commit and never-push clauses only | The execution contract omitted the resolved-question list, the scope fence (and the reason this plan's fence looks thin: git-ref operations produce no tracked diff), the shared-checkout re-verification step, the conditional finalize ownership, and a stop condition for the one genuinely unsafe case (a lane another agent is working in; two lanes had live worktrees at review). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All added, with the fence in DECLARE-and-JUSTIFY form per the 2026-09-01 ruling, an explicit note on the ref-vs-file asymmetry so the thin fence is not read as an omission, a legitimate stop for a concurrently-edited lane or an unresolvable RECOVER merge, and the finalize obligation stated unconditional with a conditional owner. |
| PR-107 | LOW | IN-SCOPE | G. executability (a title and an unchecked branch class) | H1 said "fourteen" against a body describing twelve; `git rev-list --count aw/lane/{d7qoxv,fn2l1u,mm5p3v,r2i1b1}_attempt2 --not main` -> 0 for all four | The H1 title still claimed fourteen branches, and no round had checked the four `*_attempt2` branches, which look exactly like abandoned first attempts a triage should classify. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Title changed to "(14 at filing, 12 at review round 2)" so the filename's slug stays honest against the body. The four `_attempt2` branches measured at 0 ahead and therefore correctly outside the inventory; recorded in this record so a future reader does not re-open them. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Round 1's BLOCKER contradicts my measurement. Retract it, or defer to the earlier round? | RETRACT IT, with the measurement pasted and the mechanism quoted, and lift the gate it imposed. | (a) Leave it standing because an earlier round raised it, rejected: that would leave a `high`-priority backlog item blocked on a maintainer answer to a question about a defect that does not exist, which is a worse outcome than a reviewer being wrong once in public. (b) Soften it to a MEDIUM caution, rejected: it is either true or false, and it is false; a hedge would leave an executor unsure whether deletion is safe. | the three-way decision order at `runner_shared.py:1163-1176`; `LANE_ABSENT.holds_work` False; `LANE_EMPTY_OF_WORK` not in `LANE_ATTENTION_STATES`; the measured three-case table; the existing test proving `LANE_UNKNOWN` comes from a bad TARGET | yes |
| D-2 | Does retracting the blocker require the maintainer's assent, since round 1 escalated it to them? | NO. A finding retracted on measured evidence is resolved, not re-delegated. Set OQ-04 `Status: resolved`, `Blocking: no`, with the evidence in the question body. | (a) Leave OQ-04 open and add my measurement as a comment, rejected: the question asked "what is this plan's terminal state given X", and X is false, so there is nothing left for a human to decide; leaving it open would burn a round trip on a non-question. (b) Ask the maintainer to confirm the retraction, rejected: the repository's standard is to resolve from evidence and record the decision, and asking a human to adjudicate a measurable fact is exactly what that standard exists to prevent. | the workflow's "resolve questions from authoritative evidence first; do not ask the human what the repository already answers"; the measured table | yes |
| D-3 | `upgtest` has been recovered. Rewrite OQ-03, or annotate it? | ANNOTATE IT: mark the recovery DISCHARGED with the commit cited, and PRESERVE the maintainer's answer verbatim. | (a) Rewrite OQ-03 to say "already done", rejected: it is the maintainer's own written ruling and the record of WHY the branch was worth recovering, which is still the justification for the merge that happened; overwriting it would erase the reasoning behind a completed act. (b) Delete the question as moot, rejected outright: it documents a method correction (subject-grep is unsound) that E-02 and E-04 still depend on. | `9476b48b`; the plan-review rule to preserve valid content; OQ-03's method correction still load-bearing for E-02/E-04 | yes |
| D-4 | The plan's fence declares only two records paths while E-07 deletes branches and merges code. Widen it? | NO. Explain the asymmetry in the gate instead: git-ref operations produce no tracked-path diff, so there is nothing to declare, and a merge's paths are unknowable until E-04 decides. | (a) Add `agent_workflows/` and `tests/` to `Scope-Paths` speculatively, rejected: a fence naming paths the plan may not touch is a false declaration and would need a `--scope-ack` per unmodified path at finalize; the finalize gate already handles a justified out-of-scope edit. (b) Say nothing, rejected: a thin fence on a plan that merges code reads as an oversight and a reviewer or executor will flag it. | the 2026-09-01 declare-and-justify ruling; `aw ipd finalize`'s `--scope-reason`/`--scope-ack` mechanism | yes |
| D-5 | Verdict and readiness, with the only blocker retracted? | `APPROVE WITH REVISIONS APPLIED`, readiness `go-pending-approval`, `Status: reviewed`. | (a) Keep `no-go`, rejected: the readiness table reserves `NO-GO` for a genuine not-ready condition, and after the retraction there is no open question, no unfixed BLOCKER or HIGH, and a conforming lint; a clean plan awaiting sign-off is `GO - PENDING HUMAN APPROVAL` by definition. (b) `GO`, rejected: the human has not approved, and `Status` is `reviewed` not `approved`. | workflow verdict/readiness tables; `aw ipd lint --phase review-finalize` conforming with zero findings; all four OQs resolved | yes |

### Escalation of the irreversible decisions

NONE of this round's five decisions is `Reversible: no`, and D-3 deserves a note because I first classified
it wrongly and corrected it. D-3 touches a DURABLE record (OQ-03 holds the maintainer's own verbatim ruling,
and the act it authorized, merging `upgtest` into `main`, has already been performed and cannot be cleanly
undone), so it initially read as irreversible. It is not, and the distinction is the one the workflow asks
for: judge the cost of being wrong about MY DECISION, not about the underlying event. My decision was
"annotate rather than rewrite", which ADDS a discharge note and removes nothing, and a later maintainer
undoes it by deleting a paragraph. The irreversible act in the vicinity is the merge, which was the
maintainer's, was complete before this review began, and which this round neither performed nor authorized.
Recording an irreversible EVENT is not the same as making an irreversible DECISION, and conflating them
would have raised a blocking question over a paragraph of annotation.

Every one of the five decisions is therefore undone by editing this plan or this record before the plan
executes; none publishes an interface, migrates data, deletes anything, or produces a released artifact.

### Honest limits of this review

- I did NOT execute the plan. Every disposition claim is verified as EVIDENCE THE PLAN CITES being true
  today, not as the branch triage having been performed. Twelve branches remain outstanding.
- My retraction of round 1's blocker is proven for the case E-07 performs (`git branch -D` on a lane with
  no live owner). I did NOT prove it for every path into `LANE_UNKNOWN`: an unresolvable integration TARGET
  still produces a failing row, which is why I kept E-07's prediction requirement and V-08's separate
  count rather than deleting them as now-pointless.
- I measured `stranded_lane_drift` directly and via `aw attention --check`, both from a lane. I did NOT run
  either from the main checkout, since writing there is outside this lane's authorization; the resolver
  makes the two equivalent for this command, and that is an inference from the code plus one measurement,
  not two measurements.
- The suite flake is characterized as load-dependent on the strength of one isolation re-run. I did not
  attempt to reproduce it under load a second time, so "flake" is the best available reading rather than a
  proven intermittency profile.
- I did not re-review sibling `65cuw0` or orchestrator `tb63qv`, both of which carry round 1's other two
  BLOCKERs and both of which still read `Readiness: no-go`. This plan declares
  `Item-Dependencies: executed:65cuw0`, and `65cuw0` is `reviewed`/`no-go` and unexecuted, so this plan
  cannot run yet regardless of its own readiness. That is a Set-level sequencing fact, not a defect in this
  plan, and PR-101's retraction may well apply to the orchestrator's copy of the same finding: a follow-up
  round on `tb63qv` and `65cuw0` should re-examine their PR-002 text against this measurement.
