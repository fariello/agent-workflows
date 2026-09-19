# IPD: Triage the lane branches holding unmerged commits (14 at filing, 12 at review round 2)

- Date: 2026-09-17
- Kind: child
- Concern: TWELVE `aw/lane/*` branches hold commits not reachable from `main`, and nobody can currently say which hold recoverable work. Per-branch counts RE-MEASURED at review round 2, HEAD `73c69273`: `2c122z` 26, `58ha43` 22, `7p9n2v` 16, `rchpms` 10, `qcqhj7`/`nna8yz`/`mm5p3v` 3 each, `ybkmzp`/`fn2l1u`/`03ie04` 2 each, `r2i1b1`/`d7qoxv` 1 each. **`upgtest` IS GONE FROM THIS LIST: it was RECOVERED AND MERGED to `main` on 2026-09-17 (`9476b48b`), so it is now an ancestor of `main` and 0 commits ahead.** THE TOTAL IS 40 DISTINCT COMMITS (was 43 while `upgtest` was outstanding): the per-branch counts SUM to 91, but the `wtiso` branches form one shared ancestry chain (`merge-base --is-ancestor aw/lane/58ha43 aw/lane/2c122z` returns 0), so summing double-counts. `git rev-list --count <all 12> --not main` = **40**; the whole `wtiso` group unions to **26**, the same as `2c122z` alone. The authored figure 76 matched neither sum nor union and is corrected. FOUR lane worktrees remain on disk, only two of them for a stranded branch. THE COUNT IS NOT THE RISK, and treating it as one is the trap this plan exists to avoid: most of these commits belong to plans that `main` itself records as SUPERSEDED or already EXECUTED, so the likely correct disposition for most is DELETE, not merge. But `nna8yz` proves the inverse case is also real: its lane holds a 753-line `feat(lane)` commit whose feature DID reach `main` by a different route (`lane_containment.py`), so a naive 'it is not in main, therefore merge it' reading would have re-landed a stale duplicate of shipped work.
- Scope: Decide, per branch, one of THREE dispositions with cited evidence: RECOVER (real work absent from `main`, needs merging or re-planning), DELETE (superseded, or its substance provably landed elsewhere), or ESCALATE (cannot be decided from repository evidence; needs the maintainer). Then execute the DELETE and RECOVER decisions. This plan produces a decision RECORD first and acts second, because a branch deletion is irreversible in practice and 40 commits of history is not something to guess at.
- Scope-Paths: .aw/records/research, .aw/records/backlog
- Item-Dependencies: executed:65cuw0
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: qliia1
- Set: laneorph
- Order: 2
- Highest E allocated: 08
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: ut0vzr
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-18 reviewed (aw set): plan-review round 2: APPROVE WITH REVISIONS APPLIED; PR-101..PR-107 all FIXED; round 1's BLOCKER (PR-002/OQ-04) RETRACTED as false on measurement - deleting a lane branch yields LANE_EMPTY_OF_WORK (silent), not LANE_UNKNOWN, because classify_lane_integration tests holds_work before the landing question; round 1's F-11 also retracted (aw attention resolves out of a lane by design); upgtest already recovered and merged (9476b48b) so the inventory is 12 branches / 40 distinct commits; readiness go-pending-approval
- 2026-09-18 /plan-review round 2 (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; readiness `go-pending-approval`; PR-101..PR-107, all FIXED, none deferred. Reviewed at HEAD `73c69273`. **ROUND 1's BLOCKER IS FALSE AND I RETRACT IT, MEASURED RATHER THAN REASONED.** Round 1 (PR-002 / OQ-04) asserted that deleting a DELETE branch converts its `attention.lane-stranded` row into an equally-failing `attention.lane-unknown` row, making E-08 unreachable and blocking the whole DELETE half. That is wrong, and the error is a mis-read of the DECISION ORDER in `classify_lane_integration`. The landing question is reached only in the `else` branch: `elif not described.get("holds_work")` is tested FIRST (`runner_shared.py:1166-1169`), and a deleted branch makes `inspect_lane` return `LANE_ABSENT` with `holds_work == False`, so the classifier returns `LANE_EMPTY_OF_WORK` and NEVER calls `lane_work_has_landed`. `LANE_EMPTY_OF_WORK` is NOT in `LANE_ATTENTION_STATES` (`:1068`), so the row goes SILENT. Demonstrated on a scratch repo through the real allocator with the owner record cleared: branch present -> `STRANDED / needs_attention=True / attention.lane-stranded`; branch deleted -> `EMPTY / needs_attention=False / NOT REPORTED`. The `LANE_UNKNOWN` path is real but is reached by an unresolvable TARGET, which is exactly what the existing test at `tests/test_runner_shared.py:4014-4019` exercises (`target="refs/heads/no-such-target"`), not by a missing branch. So deletion DOES silence the row, E-08's criterion is reachable as originally authored, and OQ-04 is resolved NO-OP. **ROUND 1's F-11 IS ALSO FALSE:** `aw attention` measures FINE from inside a lane, because `_resolve_runs_repo_root` (`attention.py:2029-2050`) walks out of `.aw/worktrees/` to the owning checkout on purpose. Measured from THIS lane: 19 rows over 12 distinct lanes, resolved runs root = the main checkout. The measuring-tree discipline is kept anyway (it is harmless and `git worktree list` genuinely does differ), but downgraded from a correctness gate to a note. **THE INVENTORY MOVED UNDER THE PLAN:** `upgtest` was RECOVERED AND MERGED on 2026-09-17 (`9476b48b`, "the last lane holding work that existed NOWHERE in main"), so OQ-03's RECOVER disposition is DONE, the branch is now an ancestor of `main`, and the set is 12 branches / 40 distinct commits / 91 summed, not 13 / 43 / 94. That merge also settled `fn2l1u` and `r2i1b1` (their work is in `main` under renamed symbols `ItemRefusal`->`Refusal`, `item_refusal`->`refusal_of_item`, `history_actor`->`actor_refusal`; verified all three names exist at `render_stream.py:1830`, `:1926`, `attention_contract.py:618`), which is E-04 evidence handed to the executor rather than re-derived. Verified UNCHANGED: all six `wtiso` retirement headers quoted verbatim, `6knsrx` still has no ref, all seven `executed`-plan branches still `executed`, `nna8yz`'s landing site (`lane_containment.py`) present. Suite baseline re-measured: `1 failed, 7974 passed, 3 skipped, 2 xfailed` with the one failure a LOAD-DEPENDENT FLAKE that passes in isolation (`1 passed, 46 deselected`), not the worker-role refusal set round 1 assumed.
- 2026-09-18 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; reviewed as part of orchestrator `tb63qv`'s Set (findings PR-001..PR-009 recorded there and in `.aw/records/reviews/20260917-laneorph-00-tb63qv-...review.md`); readiness `no-go` on one blocking finding. THE PLAN'S OWN ACCEPTANCE CRITERION IS UNREACHABLE AS AUTHORED (PR-002, escalated as blocking OQ-04): deleting a DELETE branch does NOT silence its attention row, it converts it into an equally-failing one. `lane_work_has_landed` returns `None` for a missing branch (`runner_shared.py:1093-1096`) -> `LANE_UNKNOWN` (`:1170-1176`) -> which IS in `LANE_ATTENTION_STATES` (`:1068`) -> which `lane_drift_severity` rates `error` ON PURPOSE, its docstring stating "UNKNOWN fails too rather than warning: a landing question we cannot answer is not evidence the work landed" (`attention.py:1103-1111`). So E-07 would perform 13 IRREVERSIBLE deletions and E-08 would still fail, on `attention.lane-unknown` instead of `attention.lane-stranded`. The gate now FORBIDS the DELETE half until OQ-04 is answered while allowing RECOVER to proceed, and E-07 must predict each deleted branch's resulting rule id so E-08 compares against a predicted set rather than an assumed silence. ARITHMETIC CORRECTED (PR-005): the "76 commits" total matches neither the per-branch sum (94) nor the distinct union (43, `git rev-list --count <13> --not main`); the `wtiso` group is 26 distinct commits, IDENTICAL to `main..aw/lane/2c122z` alone, because those branches share one ancestry chain (`merge-base --is-ancestor aw/lane/58ha43 aw/lane/2c122z` -> 0), so "74 of the 76 belong to `wtiso`" was a double-count artifact. MEASUREMENT DISCIPLINE ADDED (PR-006): `aw attention` CANNOT be measured from inside a lane, since `stranded_lane_drift` returns `[]` when it finds no run records (`attention.py:1141-1145`) and `.aw/records/runs/` is gitignored hence absent there, so an in-lane check reports a FALSE clean; E-01, E-08, V-01 and V-08 now require a named non-lane tree and count the two lane rule ids separately. Also: the premise that Order 01 "makes the stranded report trustworthy" is false (it already is; 12/12 reported lanes verified not ancestors of `main`, zero false positives), so the dependency on Order 01 now rests only on not refilling the queue; and `6knsrx` has NO branch, so it needs no disposition. WHAT VERIFIED EXACTLY: every plan-status claim (five `superseded`, seven `executed`), the retirement headers quoted verbatim, all 13 per-branch counts, and `materialize_lane_inputs` present at `lane_containment.py:2140` and called at `oc_runipd.py:6893`. OQ-04 raised `Blocking: yes` carrying PR-002.

- 2026-09-18 reviewed (aw set): plan-review complete (reviewed as part of orchestrator tb63qv's Set): REVIEWED - OPEN QUESTIONS; PR-002 left OPEN at BLOCKER and escalated as blocking OQ-04, since deleting a DELETE branch converts its attention.lane-stranded row into an equally-failing attention.lane-unknown row and E-08 cannot pass; the gate now forbids the DELETE half until it is answered while allowing RECOVER; PR-005 FIXED, the 76-commit total was neither the per-branch sum (94) nor the distinct union (43); PR-006 FIXED, every acceptance check now names a non-lane measuring tree; readiness no-go
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from a measured sweep of .aw/worktrees/ (38 worktrees/4.7G, 28 provably merged and clean) and of the 13 lane branches holding 76 unmerged commits; complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Empty the stranded-lane backlog by DECIDING each branch rather than accumulating it, and leave a cited
record of why each was deleted or recovered.

ONE PREMISE CORRECTED IN REVIEW ROUND 1, AND ONE ROUND-1 CORRECTION ITSELF RETRACTED IN ROUND 2.

FIRST, the clause "Order 01 makes the stranded report trustworthy" was REMOVED because it is false. The
report already excludes a merged lane: `classify_lane_integration` classifies one `LANDED` via
`lane_work_has_landed` and `LANE_ATTENTION_STATES` omits that state (`runner_shared.py:1063-1068`,
`:1110-1180`). Measured at review HEAD, `aw attention --check` reported 12 distinct lanes and ALL 12 were
provably not ancestors of `main`, i.e. zero false positives. So this plan does not inherit a trust problem
from Order 01, and the dependency on Order 01 rests only on not refilling the queue.

SECOND, RETRACTED IN ROUND 2: **DELETING A BRANCH DOES SILENCE ITS ROW, AND THE ROUND-1 BLOCKER WAS A
MIS-READ OF THE DECISION ORDER.** Round 1 claimed a deleted branch makes `lane_work_has_landed` return
`None` and therefore yields a still-failing `LANE_UNKNOWN` row. The `None` is real but the classifier never
sees it, because the landing question sits in the FINAL branch of a three-way decision and `holds_work` is
tested first (`runner_shared.py:1163-1176`):

```text
if live:                              -> LANE_LIVE
elif not described.get("holds_work"): -> LANE_EMPTY_OF_WORK      <- a deleted branch lands HERE
else:                                    ... lane_work_has_landed(...) -> LANDED / STRANDED / UNKNOWN
```

A deleted branch makes `inspect_lane` return `LANE_ABSENT` (`worktree_lease.py:332-346`) whose `holds_work`
is `False` (`:190-191`), so the second arm fires and `lane_work_has_landed` is NOT called.
`LANE_EMPTY_OF_WORK` is absent from `LANE_ATTENTION_STATES` (`:1068`), so the row is SILENT. Measured on a
scratch repo through the real `allocate_worktree` with the owner record cleared:

```text
1. BRANCH PRESENT (the stranded condition E-07 acts on)
    lane_state=STRANDED  landed=False  holds_work=True  ahead=1
    needs_attention=True  ->  attention.lane-stranded
2. WORKTREE REMOVED, BRANCH KEPT (today's state for most of them)
    lane_state=STRANDED  landed=False  holds_work=True  ahead=1
    needs_attention=True  ->  attention.lane-stranded
3. BRANCH DELETED (what E-07 would do)
    lane_state=EMPTY  landed=None  holds_work=False  ahead=0
    needs_attention=False  ->  NOT REPORTED (state not in LANE_ATTENTION_STATES)
```

The `LANE_UNKNOWN` path is genuine but is reached by an unresolvable TARGET, which is exactly what the
existing test exercises (`tests/test_runner_shared.py:4014-4019`, `target="refs/heads/no-such-target"`).
So E-08's acceptance criterion is REACHABLE as originally authored, OQ-04 resolves NO-OP, and the DELETE
half of E-07 is unblocked. The prediction requirement in E-07 is KEPT as cheap insurance, but it is now
a prediction of SILENCE rather than of an unknown-row set.

WHY EVIDENCE-FIRST AND NOT A BULK SWEEP. The four largest branches (26 of the 40 distinct commits, since
they share one ancestry chain) all belong to the
`wtiso` Set, and every one of those plans is filed `superseded` in `main` with an explicit retirement
reason already written (`qcqhj7`: "superseded by the `lanectn` Set"; `58ha43`: "retiring UNLANDED, with
no successor for its main deliverable"; `2c122z`: "retiring UNLANDED ... never reachable"). So the bulk
of the apparent risk is already-decided work whose branches were simply never cleaned up. Deleting them
is correct. But `nna8yz` is the counter-example that forbids doing this by branch size or by Set alone:
its lane holds `feat(lane): materialize lane inputs by copy with a sealed manifest` (753 insertions),
that feature IS present in `main` today, and it got there through `lane_containment.py` rather than
through this branch. Only a per-branch substance check distinguishes those two cases, and getting it
wrong in the RECOVER direction re-lands a stale duplicate of shipped code.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Establish the inventory and the decision rule

- [ ] E-01 Re-measure the branch inventory at execution HEAD and record it, since `main` moves and a stale list would authorize a wrong deletion. For every `refs/heads/aw/lane/*`: commits ahead of the integration target, whether a worktree exists, the last commit date, the owning plan id6 if any, and that plan's CURRENT status and directory in `main`. REPORT BOTH THE PER-BRANCH COUNTS AND THE DISTINCT UNION (`git rev-list --count <branches> --not <target>`), and state which is which: summing per-branch counts double-counts shared ancestry, which is how the authored figure of 76 arose against a real union of 40 (F-1). TAKE `git worktree list` FROM THE MAIN CHECKOUT and name the tree, since that command genuinely does report a different set per tree. `aw attention` may be measured from anywhere: round 1's F-11 claim that it reports a false clean in a lane is FALSE and retracted, because `_resolve_runs_repo_root` (`attention.py:2029-2050`) deliberately walks out of `.aw/worktrees/` to the owning checkout; measured from a review lane it returned 19 rows over 12 distinct lanes. **THE INVENTORY IS ALSO A MOVING TARGET AND HAS ALREADY MOVED ONCE MID-REVIEW: `upgtest` was recovered and merged on 2026-09-17 (`9476b48b`) between review rounds, so a branch this plan names may be gone. Re-derive; do not trust any list in this document, including the corrected one.**
  - Depends on: none
  - Expected outcome: a table of every lane branch with a non-zero ahead-count, with its owning plan's status, plus the distinct-union total stated separately from the sum. The round-2 baseline is **12 branches / 40 distinct commits / 91 summed** (round 1 said 13 / 43 / 94, before `upgtest` landed), and a material difference from that must be noted rather than silently absorbed. A branch named in this plan whose ref no longer resolves (`6knsrx`, which has never had one) or which has become an ancestor of `main` (`upgtest`, now 0 ahead) is recorded as needing no disposition rather than dropped silently.
  - Execution state: pending

- [ ] E-02 Write the DISPOSITION RULE before applying it, so the decisions are reproducible rather than ad hoc. State the evidence that justifies each of DELETE / RECOVER / ESCALATE, and state explicitly that neither branch size nor Set membership is sufficient on its own, citing `nna8yz` (superseded-looking but holds a feature that landed elsewhere) and the `wtiso` four (large but already retired with reasons). THE RULE MUST NAME THE ONE MERGED-NESS PREDICATE IT USES and must be `runner_shared.lane_work_has_landed` (`:1077-1106`), not a hand-rolled git call: a second definition of "merged" is how this plan and Order 01 would drift. THE RULE MUST ALSO FORBID A COMMIT-SUBJECT MATCH as landing evidence (see OQ-03's method correction) and require an ANCESTRY or CONTENT test.
  - Depends on: E-01
  - Expected outcome: a written rule an independent reader could apply to the same table and reach the same dispositions, naming the shared predicate it consumes and explicitly excluding subject-grep as evidence.
  - Execution state: pending

### Task group 2: Decide each branch on evidence

- [ ] E-03 For each branch whose owning plan is `superseded` in `main`, cite the retirement header already recorded there and mark it DELETE. Do not re-litigate a retirement decision the repository already made; the deliverable is the citation, not a fresh judgement.
  - Depends on: E-02
  - Expected outcome: a per-branch citation of the existing `RETIRED <date>:` reason. Expected to cover `qcqhj7`, `rchpms`, `7p9n2v`, `58ha43`, `2c122z`, i.e. 26 of the 40 distinct commits. VERIFIED AT REVIEW ROUND 2: all six `wtiso` plans (including `6knsrx`) still carry a `RETIRED 2026-09-02:` header, and `6knsrx` still has NO BRANCH, so it needs no disposition.
  - Execution state: pending

- [ ] E-04 For each branch whose owning plan is `executed` in `main`, determine per branch whether the lane's SUBSTANCE reached `main` by another route, and cite the landing site. A textual diff against `main` is NOT sufficient evidence, because `main` has evolved since; identify the feature and locate it. Mark DELETE where the substance landed, RECOVER where it did not.
  **THREE OF THE SEVEN ARE ALREADY ANSWERED BY A MERGE COMMIT ON `main`, so start there rather than re-deriving them.** `9476b48b` (2026-09-17) records that `fn2l1u` and `r2i1b1` were examined and their work "turned out to be in main already under renamed symbols: ItemRefusal -> Refusal, item_refusal -> refusal_of_item, history_actor -> actor_refusal", and that both were removed as worktrees with their branches KEPT. All three renamed symbols verified present at review round 2 (`render_stream.py:1830`, `render_stream.py:1926`, `attention_contract.py:618`), which is exactly the ancestry-or-content evidence E-02's rule demands. CITE that commit and confirm the symbols rather than repeating the analysis; then do your own check for `03ie04`, `ybkmzp`, `mm5p3v`, `d7qoxv` and `nna8yz`.
  - Depends on: E-02
  - Expected outcome: a per-branch verdict with the landing site named for each DELETE. `nna8yz` is expected to resolve DELETE with `lane_containment.py` cited as the landing site (verified present at review round 2); `fn2l1u` and `r2i1b1` are expected DELETE citing `9476b48b` plus the three renamed symbols; `03ie04`, `ybkmzp`, `mm5p3v`, `d7qoxv` each need their own check.
  - Execution state: pending

- [ ] E-05 For any branch with no owning plan, or where E-04 cannot reach a cited conclusion, mark ESCALATE and write the specific question the maintainer must answer. Do NOT guess a disposition to make the table look complete. **`upgtest` IS NO LONGER A CANDIDATE FOR THIS ITEM OR ANY OTHER: OQ-03 resolved it RECOVER, and that recovery HAS HAPPENED (`9476b48b`, 2026-09-17, "the last lane holding work that existed NOWHERE in main"), so it is now an ancestor of `main` with 0 commits ahead and needs no disposition.** Record it as already-recovered with that commit cited, so a reader of OQ-03 does not re-open a settled question.
  - Depends on: E-04
  - Expected outcome: an explicit ESCALATE list, each with a one-line question; an empty list is an acceptable outcome and is now the EXPECTED one, since the only branch that lacked an owning plan has been recovered and merged.
  - Execution state: pending

- [ ] E-06 Immortalize the decision table to `.aw/records/research/` with `aw research new`, so the reasoning survives the branch deletions that follow. This must happen BEFORE E-07, since after deletion the evidence for a DELETE is gone.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: a committed research record containing the full table, the rule from E-02, and the per-branch citations.
  - Execution state: pending

### Task group 3: Execute the decisions

- [ ] E-07 Execute the RECOVER decisions first, merging or re-planning each as its evidence requires, and only then delete the DELETE branches. Ordering matters: a deletion is effectively irreversible once the reflog expires, so nothing is deleted until every recovery has landed. **THE ROUND-1 PROHIBITION ON THE DELETION HALF IS LIFTED: deletion DOES silence the attention row (`LANE_EMPTY_OF_WORK`, not `LANE_UNKNOWN`; see the Goal's measured three-case table and F-9), so OQ-04 resolved NO-OP and both halves may proceed.** STILL PREDICT THE OUTCOME PER DELETED BRANCH before running `aw attention` again, so E-08 compares against a prediction rather than an assumption; the prediction is now "the row disappears", and a row that does NOT disappear is a real finding to report rather than absorb.
  - Depends on: E-06
  - Expected outcome: each RECOVER branch's work reachable from the integration target; each DELETE branch's ref removed with its recorded sha noted in the research record for a reflog-window rescue. Plus the per-branch prediction of its post-deletion attention state, written BEFORE E-08 runs.
  - Execution state: pending

- [ ] E-08 Confirm the end state and NAME THE TREE the measurement was taken in: `aw attention --check` reports no row for any deleted branch, and `git worktree list` contains only the main checkout plus any lane a live run owns. Take `git worktree list` from the MAIN CHECKOUT, since that command really is per-tree. Report the `attention.lane-stranded` and `attention.lane-unknown` counts SEPARATELY anyway: they are cheap to separate and an unexpected `lane-unknown` row would be genuine news (it would mean a target failed to resolve, not that a branch is missing). Close backlog `qliia1` with the research record as evidence.
  - Depends on: E-07
  - Expected outcome: a lane report with zero rows for every deleted branch and zero rows for every recovered one, the two rule ids counted separately, the measuring tree named; and `qliia1` closed `done` with cited evidence. An `attention.lane-unknown` row that was not predicted is a failure of this item rather than a footnote.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- A retired plan carries its reason in a `RETIRED <date>: <reason>` header in
  `.aw/records/plans/superseded/`. That header is the authoritative record of an already-made decision;
  this plan CITES it rather than re-deciding.
- `aw attention --check` is the canonical stranded-lane reporter (repaired by plan `pr5b0t`), and it is
  the acceptance surface for E-08. Do not hand-roll a second scan.
- Durable analysis belongs in `.aw/records/research/` via `aw research new`, never hand-named (AGENTS.md).
  E-06 exists because the evidence for a DELETE ceases to exist once the branch is gone.
- A lane BRANCH is the durable record of a lane's work while a WORKTREE is disposable: the 2026-09-17
  sweep removed 28 worktrees and zero branches. This plan is the converse operation and must be held to
  a correspondingly higher evidentiary bar.
- The execution contract forbids `git add -A` and forbids pushing; commit only declared `Scope-Paths`,
  path-scoped.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | **12** lane branches hold **40 DISTINCT** commits unreachable from `main` (per-branch counts sum to 91; the authored figure of 76 was neither, and round 1's 13 / 43 / 94 predates `upgtest` landing) | re-measured at review round 2, HEAD `73c69273`: per-branch `2c122z` 26, `58ha43` 22, `7p9n2v` 16, `rchpms` 10, `qcqhj7`/`nna8yz`/`mm5p3v` 3, `ybkmzp`/`fn2l1u`/`03ie04` 2, `r2i1b1`/`d7qoxv` 1 (sum 91); `git rev-list --count <all 12> --not main` = **40**. The gap is shared ancestry, proven by `merge-base --is-ancestor aw/lane/58ha43 aw/lane/2c122z` -> 0 |
| F-1a | **`upgtest` HAS ALREADY BEEN RECOVERED AND IS NO LONGER A CANDIDATE**, which retires OQ-03's action item and shrinks the inventory | `git merge-base --is-ancestor aw/lane/upgtest main` -> 0; `git rev-list --count aw/lane/upgtest --not main` -> **0**; merged by `9476b48b` (2026-09-17) whose message reads "the last lane holding work that existed NOWHERE in main" and lists all 8 recovered artifacts. Also absent from `stranded_lane_drift` at review round 2 |
| F-2 | The `wtiso` group is **26** distinct commits, not 74, and unions to exactly `2c122z` alone; every plan of that Set is `superseded` in `main` | `git rev-list --count aw/lane/{2c122z,58ha43,7p9n2v,rchpms,qcqhj7} --not main` = 26, identical to `main..aw/lane/2c122z`; `.aw/records/plans/superseded/` holds `qcqhj7`, `rchpms`, `7p9n2v`, `58ha43`, `2c122z`, `6knsrx`, each with a `RETIRED 2026-09-02:` header (ALL SIX verified at review round 2 by extracting the header from each file). NOTE `6knsrx` has NO BRANCH (`git rev-parse --verify aw/lane/6knsrx` fails), so it needs no disposition |
| F-3 | Those retirements are explicit and already reasoned, so the branches need citing not deciding | e.g. `58ha43`: "retiring UNLANDED, with no successor for its main deliverable"; `2c122z`: "retiring UNLANDED ... never reachable" |
| F-4 | Branch size and Set membership are NOT sufficient evidence, in the direction that causes real harm | `nna8yz` (3 commits, plan `executed`) holds `feat(lane) ... sealed manifest` at 753 insertions; that feature IS in `main` via `lane_containment.py`, so RECOVER would re-land shipped work |
| F-5 | A textual diff against `main` cannot answer "did this land", because `main` has moved | all four sampled branches report DIFFERS against `main` for their touched files, including `nna8yz` whose substance demonstrably landed |
| F-6 | Every branch with an owning plan has that plan already `executed` or `superseded` in `main`; none is mid-flight | RE-CHECKED at review round 2, all seven still `executed`: `nna8yz`/`03ie04`/`d7qoxv`/`fn2l1u`/`mm5p3v`/`r2i1b1`/`ybkmzp`; the `wtiso` six all still `superseded` |
| F-7 | ~~`upgtest` has no owning plan id6, so it cannot be dispositioned by plan status~~ **MOOT: IT HAS BEEN RECOVERED AND MERGED** | it was never an `<id6>` lane name, but the question is settled: OQ-03 ruled RECOVER and `9476b48b` performed it. It is no longer in the inventory (F-1a), so E-05's ESCALATE list is expected EMPTY |
| F-8 | Most of the 12 have NO worktree, so they consume no disk and are purely a signal problem | RE-MEASURED at review round 2 from `git worktree list`: only FOUR worktrees exist beside the main checkout (`3v7wo6`, `fujm0y`, `perf-opt`, and this review lane), and of those only two correspond to a stranded branch. So ten of the twelve are branch-only. `git worktree list` genuinely does report a different set per tree, so take it from the MAIN CHECKOUT |
| F-9 | ~~DELETING A DELETE BRANCH DOES NOT REMOVE ITS ROW; it converts it to an equally-failing `attention.lane-unknown` row~~ **FALSE AND RETRACTED AT REVIEW ROUND 2. DELETION DOES SILENCE THE ROW.** | The `None` return is real but the classifier never reaches it: `classify_lane_integration` tests `elif not described.get("holds_work")` BEFORE the landing question (`runner_shared.py:1163-1176`), and a deleted branch yields `LANE_ABSENT` (`worktree_lease.py:332-346`) whose `holds_work` is `False` (`:190-191`), so the result is `LANE_EMPTY_OF_WORK`, which is NOT in `LANE_ATTENTION_STATES` (`:1068`). MEASURED on a scratch repo via the real allocator with the owner cleared: branch present -> `STRANDED / needs_attention=True`; branch deleted -> `EMPTY / needs_attention=False / NOT REPORTED`. The genuine `LANE_UNKNOWN` path is an unresolvable TARGET, which is what `tests/test_runner_shared.py:4014-4019` exercises. E-08's criterion is REACHABLE as authored |
| F-10 | The stranded report is ALREADY free of merged-lane false positives, so this plan inherits no trust problem from Order 01 | measured at review: `aw attention --check` gave 19 rows over 12 DISTINCT lanes, all 12 NOT ancestors of `main`; the six merged lanes named in Order 01 appear zero times. RE-CONFIRMED at round 2: still 19 rows / 12 distinct lanes, all `attention.lane-stranded`, and the now-merged `upgtest` correctly dropped out |
| F-11 | ~~`aw attention` CANNOT BE MEASURED FROM INSIDE A LANE: it reports a false clean~~ **FALSE AND RETRACTED AT REVIEW ROUND 2** | `_resolve_runs_repo_root` (`attention.py:2029-2050`) exists precisely to handle this: when the local `state_root` is absent it walks `.aw/worktrees/` parents to the owning checkout. Measured FROM this review lane: resolved runs root = the main checkout, `stranded_lane_drift` returned **19 rows over 12 distinct lanes**, not `[]`. The `[]`-on-no-run-records path (`:1231-1232`) is real but is reached only when the OWNING checkout has no runs. The measuring-tree discipline is kept for `git worktree list`, which really is per-tree |

## Proposed changes (ordered, validatable)

1. Re-measure the inventory at execution HEAD (E-01) and write the disposition rule (E-02).
2. Disposition each branch on cited evidence: retirement headers for the `superseded` group (E-03),
   substance-landed checks for the `executed` group (E-04), explicit escalation for the remainder (E-05).
3. Immortalize the decision table to `.aw/records/research/` BEFORE any deletion (E-06).
4. Land every RECOVER, then delete every DELETE, recording each deleted sha (E-07).
5. Verify an empty stranded-lane report and close `qliia1` (E-08).

This plan changes no product code. Its deliverables are a research record, a set of branch operations,
and a closed backlog item.

## Deferred / out of scope (with reason)

- PREVENTING future accumulation is Order 01 (`65cuw0`); this plan drains the existing backlog only.
  Running this plan without Order 01 would refill the queue on the next run, which is why the dependency
  is declared rather than merely noted.
- The 2 staged deletions in the `lqly9m` and `pr5b0t` worktrees are a DIFFERENT defect (backlog `5bmq5f`,
  a backlog item duplicated across status directories) and are not lane-work to triage.
- `perf/att-set-speed` is the maintainer's own branch, not an `aw/lane/*` lane, and is untouched.
- Deleting merged lane branches is out of scope here as in Order 01: those hold no unmerged work and are
  not what this plan is about.

## Scope check

- Over-scope: none. Every E-item is on the path from "13 undecided branches" to "an empty stranded
  report with the reasoning recorded".
- Under-scope: the ESCALATE bucket is deliberately left for the maintainer rather than guessed. If E-05
  is non-empty, this plan can still finalize: an escalation with a written question is a completed
  disposition, whereas a fabricated verdict is not.

## Required tests / validation

- `aw attention --check` output pasted with the measuring TREE NAMED, with `attention.lane-stranded` and
  `attention.lane-unknown` counted separately. **AN EMPTY LANE REPORT IS THE EXPECTED OUTCOME** (F-9
  retracted round 1's claim that it could not be reached), and any tree may be used for this command
  (F-11 retracted too); `git worktree list` still comes from the MAIN CHECKOUT because that one really
  is per-tree. Review round-2 baseline: 19 rows over 12 distinct lanes, all `attention.lane-stranded`,
  zero `attention.lane-unknown`.
- The committed research record path, with its decision table, cited per branch.
- For every DELETE: the recorded sha, plus the citation that justified it (a retirement header, or the
  landing site of its substance). Never a commit-SUBJECT match, which OQ-03 records as an unsound method
  that already produced a wrong classification once.
- For every RECOVER: evidence its work is now reachable from the integration target, established with
  `runner_shared.lane_work_has_landed` (the one shared predicate) rather than a hand-rolled check.
- `python3 -m pytest` bare, pasted, since E-07 may merge real code. RUN IT BARE: `addopts`
  already supplies the flags, and a second `-q` suppresses the summary line this item requires. Take a
  baseline in the SAME tree first and gate on NO NEW failures, since a managed worker lane fails a set of
  lifecycle tests by design (backlog `770fkp`). REVIEW ROUND-2 BASELINE, measured with
  `env -u AW_EXECUTION_ROLE`: `1 failed, 7974 passed, 3 skipped, 2 xfailed`. The one failure
  (`tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`)
  is a LOAD-DEPENDENT FLAKE, not a regression and not a role refusal: re-run in isolation it gives
  `1 passed, 46 deselected`. Do NOT "fix" it, and do NOT treat "1 failed" as a red baseline.
- `qliia1` shown `done` with evidence.

## Spec / documentation sync

N/A: no spec governs lane-branch triage, and this plan changes no product behavior. No `.spec.md` is
declared in `Scope-Paths`.

## Open questions

### OQ-01: Is deleting a branch whose plan is already `superseded` a decision this plan may make alone?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, and citing rather than re-deciding is what keeps it in scope.
  The repository ALREADY made the substantive call: each of the six `wtiso` plans carries an explicit
  `RETIRED 2026-09-02:` header stating it was superseded or is unlanded-with-no-successor. Deleting the
  branch of an already-retired plan enacts a recorded decision; it does not make a new one. E-06 preserves
  the sha of every deleted branch so a reflog-window rescue stays possible if a citation turns out wrong.

### OQ-02: What if a RECOVER branch no longer merges cleanly onto a moved `main`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Then it is RE-PLANNED, not force-merged. These branches are between
  three days and three weeks old against a fast-moving `main`, so a conflicted merge is the expected
  case rather than the exception, and resolving a stale three-week-old conflict by hand is exactly how
  shipped behavior gets silently reverted. E-07 therefore permits recovery by authoring a fresh plan that
  re-implements the work against current HEAD, with the lane branch cited as the source. Recovering the
  INTENT is the requirement; replaying the commits is not.

### OQ-03: Should `upgtest` be deleted since it has no owning plan?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-17 by the maintainer: DO NOT DELETE. PRESERVE and
  assess for recovery. **AND THE RECOVERY HAS SINCE BEEN PERFORMED, so this question is not merely
  resolved but DISCHARGED, and no E-item owes it anything.** Verified at review round 2: `9476b48b`
  (2026-09-17) merged the branch to `main` with the message "integrate(upgtest): land the upgrade-rehearsal
  harness and the 8 artifacts it produced ... The last lane holding work that existed NOWHERE in main",
  recording per-artifact verification of all 8 (`hdhzr2`, `x15f0q`, `ygtykn`, `kapm7y`, `u27q6g` backlog and
  `h90ij1`, `z1yefm`, `i8u6hh` plans), zero `git merge-tree` conflicts, `61 passed` on the new suite and
  `7968 passed` on the full one. `git merge-base --is-ancestor aw/lane/upgtest main` now returns 0 and the
  branch is 0 commits ahead, so it has left the inventory (F-1a) and E-05's ESCALATE list is expected empty.
  The maintainer's answer below is preserved verbatim as the record of WHY it was recovered.
  The premise that "nothing in the repository records... whether its work is still
  wanted" was tested and is FALSE: the branch carries 3,063 insertions across 14 files, and the
  repository records what they are.
  MEASURED at 2026-09-17 (re-derive at execution HEAD rather than trusting these figures):
  `tools/aw_upgrade_test.py` (1370 lines, an upgrade rehearsal harness), `tests/test_aw_upgrade_test.py`
  (763 lines), `tools/README.md` (+77), THREE plans that exist NOWHERE in `main` (`h90ij1`, `z1yefm`,
  `i8u6hh`) each with its own `.review.md`, and two backlog items. So this is the one branch in the
  fourteen whose content is genuinely unlanded rather than squash-merged or deliberately retired.
  WHY IT IS WANTED, from its own review record rather than inferred: the review of `z1yefm` records a
  HIGH finding that TWO split-brain detectors disagree, engine's being content-aware
  (`engine.py:119-142`) while doctor's tests a bare `.is_dir()` (`doctor.py:323-326`), and that because
  `.agents/skills` is the intended permanent skills location for BOTH layouts, doctor "misreports
  forever". The record states the plan as originally written "would have shipped, passed its own
  validation, and left the user still reading 'Dual layouts detected'". That is a live user-visible
  defect with a written analysis, which is the opposite of abandoned scratch.
  THE DISPOSITION IS THEREFORE `RECOVER`, NOT `DELETE`, and E-05 should record it as such rather than as
  an ESCALATE. NOTE what recovery still owes, because "preserve" is not "merge": the branch was last
  touched 2026-09-12 and `main` has moved substantially since, so E-07 must establish a baseline, merge,
  and re-run the suite rather than fast-forwarding on the strength of this answer. The three unlanded
  plans are `to-review`/`go-pending-approval` per their own review records and still need human
  approval before any of them EXECUTES; recovering the branch makes them visible, it does not approve
  them.
  A METHOD CORRECTION THIS QUESTION EXPOSED, recorded because it affects E-04 and could authorize a
  wrong deletion. An earlier triage in this repository classified `upgtest` as already-landed by
  matching its tip commit SUBJECT against `git log main --grep`. That method is UNSOUND: the grep
  matched the lane's own commit rather than a commit on `main`, and every one of the three commits
  returns `git merge-base --is-ancestor <sha> main` -> false. E-04 must use an ANCESTRY or CONTENT test,
  never a subject match, and E-02's disposition rule should say so explicitly.

### OQ-04: Does deleting a DELETE branch leave an equally-failing `attention.lane-unknown` row, so that this plan's terminal state must change?

- Blocking: no
- Finding: PR-002
- Status: resolved
- Owner: none
- Resolution or deferral rationale: **NO. RESOLVED NO-OP AT REVIEW ROUND 2 BY MEASUREMENT, and round 1's
  finding is RETRACTED as false.** The question was raised on the belief that a deleted branch makes
  `lane_work_has_landed` return `None`, which becomes `LANE_UNKNOWN`, which is reportable. Each of those
  links is individually true and the CHAIN IS NEVER TRAVERSED, because the landing question is the THIRD
  arm of a three-way decision in `classify_lane_integration` (`runner_shared.py:1163-1176`):

  ```text
  if live:                              -> LANE_LIVE
  elif not described.get("holds_work"): -> LANE_EMPTY_OF_WORK      <- a deleted branch lands HERE
  else:                                    ... lane_work_has_landed(...) -> LANDED / STRANDED / UNKNOWN
  ```

  A deleted branch makes `inspect_lane` return `LANE_ABSENT` (`worktree_lease.py:332-346`), whose
  `holds_work` property is `False` (`:190-191`), so the SECOND arm fires and `lane_work_has_landed` is
  never called. `LANE_EMPTY_OF_WORK` is absent from `LANE_ATTENTION_STATES` (`runner_shared.py:1068`), so
  the row goes silent. MEASURED end to end on a scratch repository built through the real
  `allocate_worktree`, with the lane owner record cleared so the lane is not `LIVE`:

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

  The `LANE_UNKNOWN` state is real and does fail closed as its docstring says, but it is reached by an
  UNRESOLVABLE TARGET rather than a missing branch, which is exactly the condition the existing test
  exercises (`tests/test_runner_shared.py:4014-4019`, `target="refs/heads/no-such-target"`). Conflating
  the two `None` producers is what produced the false blocker.
  CONSEQUENCES: E-08's acceptance criterion is REACHABLE as originally authored and an empty lane report IS
  the expected terminal state; none of round 1's four options (accept-unknown, prune run records, add a
  DISPOSITIONED state, do-not-delete) is needed, and in particular no run-record edit and no new public
  classifier state is required; the gate's prohibition on the DELETE half is LIFTED. The per-branch
  prediction requirement in E-07 is KEPT, because it costs nothing and would catch this class of error from
  the other direction: if a row does NOT vanish, that is real news and must be reported, not absorbed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted inventory table measured at execution HEAD, with the per-branch
    ahead-count, worktree presence, owning plan id6, and that plan's status/directory. BOTH the summed and
    the DISTINCT-UNION commit totals, labelled, with any divergence from the round-2 review baseline
    (**12 branches / 40 distinct / 91 summed**) stated explicitly. The measuring TREE named, and
    `git worktree list` taken from the MAIN CHECKOUT. A branch that has BECOME an ancestor of `main` since
    this plan was written must be reported as such rather than silently dropped: that already happened once
    (`upgtest`, `9476b48b`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the written disposition rule, quoted, showing it names the evidence required for
    each of DELETE / RECOVER / ESCALATE and states that size and Set membership alone are insufficient.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: for each `superseded`-plan branch, the quoted `RETIRED ...` header from the plan
    file in `main`. A verdict with no quoted header does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: per branch, the identified feature and either the landing site in `main` (for
    DELETE) or a demonstration of its absence (for RECOVER). The `nna8yz` row must name
    `lane_containment.py` or correct the 2026-09-17 finding with evidence. The `fn2l1u` and `r2i1b1` rows
    must cite `9476b48b` and show the three renamed symbols (`Refusal`, `refusal_of_item`, `actor_refusal`)
    present, or correct that commit's claim with evidence. A bare `git diff` verdict is explicitly NOT
    acceptable evidence for this item (F-5).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the ESCALATE list with one written question per entry, or a statement that it is
    empty because every branch resolved with a citation.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the committed research record path and its table, shown to exist BEFORE any
    branch deletion (cite the commit order).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: for every RECOVER, proof its work is reachable from the integration target,
    established with `runner_shared.lane_work_has_landed`; for every DELETE, the recorded sha AND the
    written pre-deletion prediction of its resulting attention state. Plus `python3 -m pytest` bare if any
    code merged, compared against a baseline taken in the SAME tree (round-2 baseline `1 failed, 7974
    passed, 3 skipped, 2 xfailed`, the one failure a load-dependent flake that passes in isolation), gating
    on NO NEW failures rather than on an absolute count.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted `aw attention --check` with the measuring tree NAMED, with the
    `attention.lane-stranded` and `attention.lane-unknown` row counts stated SEPARATELY, showing zero rows
    for every deleted branch and every recovered one; pasted `git worktree list` FROM THE MAIN CHECKOUT;
    and `qliia1` shown `done` with evidence. An `attention.lane-unknown` row that E-07 did not predict is a
    failure of this item rather than a footnote, since round 2 measured that deletion produces
    `LANE_EMPTY_OF_WORK` and therefore silence: an unknown row would mean something else is wrong, most
    likely an unresolvable integration target. Round 1's claim that an in-lane measurement is a false clean
    is RETRACTED (F-11), so `aw attention` may be run from any tree provided the tree is named.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution, and it carries a HIGHER bar than most:
E-07 deletes git branches, which is effectively irreversible once the reflog expires. The executor MUST
NOT delete any branch before E-06's research record is committed, and MUST record each deleted sha.

**ROUND 1's PROHIBITION ON THE DELETE HALF IS LIFTED.** It rested on F-9's claim that deletion converts a
stranded row into a still-failing unknown row; round 2 measured that claim FALSE (deletion yields
`LANE_EMPTY_OF_WORK`, which is silent), OQ-04 is resolved NO-OP, and both halves of E-07 may proceed. The
irreversibility bar above is unchanged and is the real gate: research record committed FIRST, every sha
recorded, RECOVER before DELETE.

EXECUTION CONTRACT. All four open questions are RESOLVED; execute their recorded answers and do not
re-litigate them. In particular: `upgtest` is ALREADY RECOVERED (`9476b48b`) and needs no disposition,
`fn2l1u` and `r2i1b1` have cited landing evidence in that same commit, and deletion DOES silence an
attention row. RE-DERIVE THE INVENTORY ANYWAY: it moved once mid-review, so treat every branch list in this
document as history and E-01's measurement as authoritative.
SCOPE FENCE: this plan declares `.aw/records/research` and `.aw/records/backlog`. Note the deliberate
asymmetry, because it will look like a gap: branch deletions and merges are git-ref operations, not file
edits, so they produce no tracked-path diff to declare. An out-of-scope FILE edit that is genuinely required
must be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a
declared-but-unmodified path needs a `--scope-ack`; do not stop over a scope question. DO stop, however, on
a genuinely unsafe condition: a lane whose worktree another agent is working in (this is a SHARED CHECKOUT,
and `3v7wo6` and `fujm0y` had live worktrees at review), or a RECOVER whose merge cannot be resolved without
guessing.
HARD-MUST HONESTY RULE: paste the ACTUAL command output for every `V-*`, name the tree each measurement was
taken in, and never claim a test passed that you did not run. Gate the suite on NO NEW failures against a
baseline taken in the same tree, not on an absolute count.
Work in an isolated worktree. Commit path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never
push, and never create a tag. Before every commit run `git diff --cached --name-only` and unstage anything
that is not yours with `git restore --staged <path>`; re-verify after any failed hook.

Post-gate lifecycle: the finalize obligation is unconditional, but its OWNER is conditional. Under
`aw oc run` / `aw agy run` the RUNNER owns `aw ipd begin` and `aw ipd finalize`; a hand-executed run means
the executor runs `aw ipd finalize` itself. Either way the plan reaches `.aw/records/plans/executed/` only
after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence. Never
hand-roll a `git mv` to `executed/`. A non-empty ESCALATE list does NOT block finalization, provided each
entry carries its written question.
