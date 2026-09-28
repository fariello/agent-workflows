# IPD: Refuse a lane integration that would leave a plan at two lifecycle locations

- Date: 2026-09-28
- Kind: child
- Concern: A lane integration can SUCCEED while leaving one plan at two lifecycle locations, silently regressing the lifecycle. MEASURED 2026-09-28 end to end through `oc_runipd.integrate_lane_branch`: when the plan is ABSENT AT THE MERGE BASE (the lane AUTHORS it at `pending/` while main has since landed the same plan at `executed/`), the two copies are an add/add at different paths with no rename source to collide, git merges CLEAN, and the call returns `integrated=True`, `kind='integrated'`. Main afterwards holds the plan at `pending/` with `- Status: to-review` and at `executed/` with `- Status: executed`. No conflict, no prompt, no refusal, and the regression is recorded as a normal commit by a legitimate verb. `integrate_lane_branch`'s existing pre-merge gates cannot see it: `dirty_tree_overlap` asks only about UN-OWNED DIRT in main, and the merge-and-revalidate gate's conflict-marker scan and combined-suite revalidation both pass because there is no conflict and the merged tree is green. The condition is a LIFECYCLE contradiction, and nothing in the integration path asks a lifecycle question today.
- Scope: Add ONE pre-merge refusal to the shared integration path for the condition "this merge would leave an artifact identity at more than one lifecycle location", consuming Order 1's predicate rather than re-deriving it, with a cause and a verdict sentence so the refusal is legible and durable. IN: the refusal arm, its cause constant and verdict sentence, the prediction of the post-merge placement from the merge's own result, and the integration regression tests on both hosts. OUT: the structural `aw check` rule and its predicate (Order 1 owns them); any change to the deferral ladder's policy vocabulary, budget or statuses; the records-only re-derivation and history-append auto-resolve paths; and the item's fix-sketch point 3.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_shared.py
- Item-Dependencies: executed:tl2b2r
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: wlyg3g
- Blocks-Release: next
- Set: lifecycledup
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 46u3tu

## Workflow history

- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `wlyg3g` alongside Order 1 (`tl2b2r`). GATE NOTE: item `wlyg3g` carries `- Blocks-Release: next`, so this plan INHERITS it.
  THIS PLAN FIXES A DIFFERENT SHAPE FROM THE ONE THE ITEM DESCRIBES, AND THE DIFFERENCE IS MEASURED, NOT ARGUED. The item's scenario, a lane holding a `pending/` copy the base also had against a main that `git mv`-ed it to `executed/`, is ALREADY REFUSED today: git detects the rename/modify collision, `git merge-tree --write-tree` exits 1 with three index stages, and the runner returns `integrated=False`, `kind='fail-merge'`, cause `git-merge-conflict`, leaving ONE copy on main. An executor who builds a gate for the item's stated premise would be gating a condition git already catches. The REAL hole is the add/add shape in this plan's Concern, which the item does not name and which produces NO conflict at all. F-01 through F-04 record both measurements.
  THIS PLAN IS GATED ON ORDER 1 AND THE GATE IS A CORRECTNESS REQUIREMENT, NOT SEQUENCING PREFERENCE. The refusal must consume Order 1's placement predicate. A refusal carrying its own private copy of "which identities sit at more than one lifecycle location" is the two-readers drift this repository has already paid for repeatedly, and `runner_shared`'s own convention states the rule: "NO NEW PATH LITERAL. Enumeration goes through `check_engine._iter_spec_records`". `runner_shared` already imports `check_engine` lazily, so the direction is established and cycle-free. Hence `- Item-Dependencies: executed:tl2b2r`.
  DO NOT MISTAKE THIS FOR A DUPLICATE OF THE RECORDS-ONLY RE-DERIVATION PATH. `classify_conflict_set_for_rederivation` and `auto_resolve_history_append_conflicts` both run only AFTER git has reported a CONFLICT, and both read merge index stages. The add/add shape produces no conflict and no stages, so neither path is ever reached; that is precisely why the hole exists. Do not extend either function.
  THE REFUSAL MUST BE PRE-MERGE, WHICH IS AVAILABLE BECAUSE THE RUNNER ALREADY PREDICTS THE MERGE RESULT. `merge_write_set` runs `git merge-tree --write-tree HEAD <branch>` before any merge, and on the add/add shape it exits 0 and yields a real tree. E-01 reads the PLACEMENT out of that predicted tree, so the refusal happens with main untouched and no abort needed, matching the `dirty_tree_overlap` arm's shape.

## Goal

Make the silent lifecycle regression impossible through the runner: a merge that would leave one plan at two lifecycle locations is REFUSED before main is touched, naming both paths and both statuses, instead of being committed as a normal integration. The payoff is that the one route by which this repository actually produces the condition, a lane authoring a plan main has already finalized, fails closed rather than quietly recording a contradiction.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the pre-merge lifecycle refusal

- [ ] E-01 Add a PRE-MERGE placement reading to `runner_shared.integrate_lane_branch` that asks Order 1's predicate about the PREDICTED POST-MERGE TREE, not about the working tree and not about the lane's diff. Place it immediately after the existing `dirty_tree_overlap` refusal arm and BEFORE the merge-and-revalidate gate, so the refusal costs no suite run and leaves main untouched.
  READ THE PREDICTED TREE THAT `merge_write_set` ALREADY BUILDS RATHER THAN ADDING A SECOND `merge-tree` CALL. `merge_write_set` runs `git merge-tree --write-tree HEAD <branch>` and, on the add/add shape, exits 0 with a real tree object; MEASURED 2026-09-28, that is exactly the shape this plan targets. Take the tree from the same invocation (or a single shared one) and enumerate its record paths with `git ls-tree -r --name-only <tree>`; there is precedent for a branch-tree read at `lane_plan_terminal_bucket`, which runs `git ls-tree -r --name-only <branch>` for the same class of question.
  `merge_write_set` RETURNS `None` WHEN IT CANNOT KNOW, AND THAT CASE MUST NOT REFUSE. Its own comment records that `None` means a conflicting merge or a git without `--write-tree`, and that today's behavior on the unknown path is to fall back to the lane's `changed_files` rather than to check nothing. A conflicting merge is git's own to classify and is ALREADY refused (F-02), so an unknown prediction must SKIP this reading and proceed, not manufacture a refusal. State that decision in the code.
  ASK ONLY ABOUT IDENTITIES THIS MERGE WOULD AFFECT, and do not fail the integration for a pre-existing duplicate the lane had nothing to do with. Compare the predicted tree's placement against `HEAD`'s: refuse only where the merge INTRODUCES a second location. A pre-existing duplicate is Order 1's rule to report, and refusing an unrelated lane for it would block recovery of work that is not at fault; this repository currently has none (Order 1 F-07).
  DO NOT ADD A THIRD REFUSAL KIND. Reuse the existing terminal kind used for a measured gate refusal, because this IS a measured refusal: the placement was computed from git's own predicted tree, not guessed. A deferrable kind would be wrong, since repeating the merge cannot change the placement.
  - Depends on: none
  - Expected outcome: on the add/add fixture the call returns `integrated=False` with a terminal kind, main's `HEAD` unmoved, the lane branch and worktree preserved, and NO merge left in progress; on a clean lane the arm is silent and integration still succeeds; an unknown prediction (`merge_write_set` returning `None`) proceeds rather than refusing; a pre-existing duplicate not introduced by the lane does not refuse.
  - Execution state: pending

- [ ] E-02 Add the cause constant and its verdict sentence so the refusal is legible and durable, following the established channel exactly rather than inventing a transport. Add the cause beside the existing `INTEGRATION_CAUSE_*` constants, map it where the existing causes are mapped, tag the refusal reason with `tag_integration_cause`, and add the verdict sentence to `terminal_refusal_verdict` so `aw runs` and the run report explain the refusal after the fact.
  USE `tag_integration_cause`, THE ONE WRITER, AND DO NOT WIDEN THE RETURN TUPLE. The module records why: `integrate_lane_branch` receives neither `item` nor `state`, so it has no durable sink; a module-level side channel was REFUSED outright because the module is driven concurrently and would cross-attribute one item's cause to another; and widening the 3-tuple was rejected on measured cost, since eleven sites unpack it and both per-host wrappers are pinned to an exact signature by `tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_each_wrapper_keeps_the_ORIGINAL_signature`.
  THE VERDICT SENTENCE MUST NAME THE LIFECYCLE FACT, NOT A CONFLICT. The existing terminal wording asserts a conflict or a red suite, and both would be FALSE here: there is no conflict and the merged tree is green. That mislabelling has already cost this repository once, recorded at `INTEGRATION_REFUSAL_UNMEASURED`, where `integration_failed_combined_red` claimed "revalidation failed" for three items whose suite was never invoked. Say instead that the merge would place one plan at two lifecycle locations, name both, and say which one is terminal.
  MIND THE REDACTION ASYMMETRY BEFORE TAGGING. The module records that the cause tag is what routes a refusal into `record_refusal`, "a writer that does NOT redact", and that two re-derivation arms are deliberately left UNTAGGED because their reason text carries git hook output that can embed an absolute path. This refusal's text carries only repo-relative record paths and statuses, so tagging is safe; verify that at execution and state it, and do not interpolate git stderr into the reason.
  - Depends on: E-01
  - Expected outcome: the refusal reason carries the new cause token, `read_integration_cause` round-trips it, the operator-facing reason has the token stripped, `terminal_refusal_verdict` returns a sentence naming the lifecycle condition and both paths, the recorded `integration_ladder.cause` shows the new value, and the reason is confirmed to contain no absolute path and no git stderr.
  - Execution state: pending

- [ ] E-03 Confirm the refusal is TERMINAL rather than deferred, by reading the existing classifier instead of adding a branch to it. Drive `classify_integration_refusal` and `decide_integration_deferral` with the new kind and cause and record what they return; if the kind reused in E-01 is already terminal, this item CHANGES NO CODE and its deliverable is the recorded evidence.
  DO NOT ADD A LADDER BRANCH TO REACH A TERMINAL OUTCOME THE EXISTING TABLE ALREADY GIVES. The deferral ladder distinguishes deferrable from terminal by KIND, and the terminal kind exists for a refusal repetition cannot resolve, which this is. An added branch would be dead code carrying an untestable claim; the module states that rule for the unreachable gate causes ("DO NOT ADD A CONSTANT OR A VERDICT BRANCH FOR THE UNREACHABLE FOUR").
  IF THE EVIDENCE SHOWS IT IS DEFERRABLE, STOP AND REPORT rather than widening scope: changing the ladder's classification is outside this plan's declared surface and would affect every other refusal sharing that kind.
  - Depends on: E-02
  - Expected outcome: pasted driven output of both functions for the new kind/cause, showing a terminal status and `deferrable=False`; a statement of whether any code changed and why not if not; no new ladder branch.
  - Execution state: pending

- [ ] E-04 Add the integration regression tests to `tests/test_runner_shared.py` on BOTH hosts, using that file's existing real-git lane harness rather than a new one.
  REUSE THE EXISTING HARNESS AND THE `BOTH`/`_MODULES` HOST TABLE. `LaneIntegrationBehaviorTests` already builds a real repo (`_repo`), a real lane via `git worktree add` returning a `worktree_lease.WorktreeHandle` (`_lane`), and a `_passing_runner`; `_unknown_write_set` already patches `merge_write_set` to return `None`, which is exactly E-01's unknown-prediction case. The dirty-overlap test is the template to imitate, including its post-conditions.
  ASSERT THE POST-CONDITIONS THE TEMPLATE ASSERTS, NOT JUST THE RETURN VALUE: `integrated` is False, the kind is the expected terminal string, the reason names BOTH record paths, main's `HEAD` is UNMOVED, the lane branch still exists, and no merge is in progress (so no abort was left dangling). A test asserting only the tuple would pass for an implementation that refuses AFTER dirtying main.
  FOUR ROWS, EACH FOR A STATED REASON: (a) the ADD/ADD fixture, which must refuse and is the defect; (b) a CLEAN lane touching no records, which must still INTEGRATE, since every other row passes for an arm that refuses unconditionally; (c) `merge_write_set` returning `None`, which must PROCEED rather than refuse; (d) a PRE-EXISTING duplicate present on both sides and not introduced by the lane, which must NOT refuse. Row (b) is the one that catches the worst possible regression here, an arm that blocks all integration.
  BUILD THE ADD/ADD FIXTURE EXACTLY AS MEASURED: the plan must be ABSENT at the merge base, the lane commits it at `pending/`, and main commits the same filename at `executed/`. If the plan exists at the base and main `git mv`-es it, git CONFLICTS and the fixture proves nothing about this arm (F-02). Note git does not track empty directories, so the lifecycle directories need a tracked file (a `README.md`) at the base, or the worktree write will fail; that cost one debugging round trip while authoring this plan.
  - Depends on: E-03
  - Expected outcome: all four rows pass on both hosts; row (a) refuses with main untouched and both paths named; row (b) still integrates; rows (c) and (d) do not refuse; bare `python3 -m pytest` is green with its summary line pasted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.integrate_lane_branch` is THE one merge function; both hosts are thin wrappers binding `host_label`, `run_checked` and `action_kind`, and the wrappers' exact signatures are pinned by a test that forbids exposing the injected parameter.
- Every sanctioned integration runs through `integrate_under_repository_lock`, which reads main's tip INSIDE the lock and defers rather than fails on lock expiry. A test pins that no other site calls an integration callable directly.
- The refusal taxonomy is THREE kinds: a transient deferrable one (un-owned dirty overlap), a terminal measured one, and an "unmeasured" deferrable one added because a harness failure was being reported as a red suite.
- A cause travels as a PREFIXED TOKEN in the reason string, written only by `tag_integration_cause` and read only by `read_integration_cause`; the token is stripped before an operator sees the reason. The module records that a module global was refused outright (concurrent drivers would cross-attribute) and that widening the return tuple was rejected on measured cost.
- `record_integration_refusal` is the single rung-1 write site for status, ladder and events; it is where the cause token is parsed, because it already receives `item`.
- Four of the merge-and-revalidate gate's six statuses are provably UNREACHABLE from this call path, and the module explicitly forbids adding constants or verdict branches for them.
- `merge_write_set` returns `None` for "cannot know", and the established response is to fall back rather than to check nothing.
- `dirty_tree_overlap` asks only about un-owned dirt in main intersected with the incoming write set; it is blind to lifecycle placement.
- The records-only re-derivation and history-append auto-resolve paths run only after a git CONFLICT and read merge index stages, so they are unreachable on a clean merge.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | The item's premise that git merges the described shape CLEAN is FALSE. With the plan present at the base and main `git mv`-ing it to `executed/`, `git merge-tree --write-tree main lane` exits 1 with three index stages and `CONFLICT (content)`; the real `git merge --no-ff` exits 1 identically. Driven across eight variants (lane-touches-plan x main-diverges x `merge.renames=false`), every lane-touches-plan variant conflicted. | Driven 2026-09-28 in throwaway repos reproducing the item's `d7qoxv` shape. | The plan must NOT gate the item's stated shape. Recorded so a reviewer sees the correction rather than inheriting the false premise. |
| F-02 | End to end, that shape is already refused: `oc_runipd.integrate_lane_branch` returned `integrated=False`, `kind='fail-merge'`, cause token `git-merge-conflict`, shape `semantic`, one copy left on main at `- Status: executed`. | Driven 2026-09-28 against a real lane worktree and a real `WorktreeHandle`. | No work is needed for that variant, and E-04 must not build its fixture that way or the test proves nothing. |
| F-03 | The REAL hole is the ADD/ADD shape: plan ABSENT at the merge base, lane commits it at `pending/`, main commits it at `executed/`. No rename source, so git merges CLEAN and the runner returns `integrated=True`, `kind='integrated'`. Main then holds `pending/` at `- Status: to-review` AND `executed/` at `- Status: executed`. Reproduced for a `superseded/` terminal directory too. | Driven 2026-09-28 through `oc_runipd.integrate_lane_branch`; the probe printed `*** DEFECT REPRODUCED: integration SUCCEEDED with the plan in TWO lifecycle dirs ***`. | This is the entire subject of the plan, and it is the common shape for a lane that AUTHORS a plan, which is what this turn does. |
| F-04 | `git merge-tree --write-tree main lane` exits 0 on the add/add shape and yields a real tree whose `ls-tree` shows BOTH paths. | Driven 2026-09-28; the predicted tree listed `pending/...ipd.md` and `executed/...ipd.md`. | The refusal can be PRE-MERGE with main untouched, reusing the prediction `merge_write_set` already makes. No new mechanism is required. |
| F-05 | The existing pre-merge gates cannot see this condition. `dirty_tree_overlap` asks only about un-owned dirt in main; the merge-and-revalidate gate's conflict-marker scan finds no markers and its combined revalidation passes because the merged tree is green. | Read from both functions' contracts plus F-03's clean-merge measurement. | A NEW arm is genuinely required; no existing gate can be tightened to cover it. |
| F-06 | The auto-resolution paths are unreachable here: `classify_conflict_set_for_rederivation` and `auto_resolve_history_append_conflicts` both run only after a git conflict and read merge index stages. | Read from the call sites, which sit inside the post-`CONFLICT` branch. | Do not extend either. Their existence is not coverage of this defect. |
| F-07 | The stale-snapshot framing this refusal needs ALREADY EXISTS in-tree: `format_records_only_conflict_refusal_reason` says "THE INCOMING BRANCH HOLDS A STALE LIFECYCLE SNAPSHOT: its `- Status:` values were read before those transitions, so TAKING ITS SIDE WOULD REVERT N real execution(s)", and `RecordsOnlyConflictVerdict` carries `target_is_terminal` from `run_selection_policy.is_in_terminal_directory`. | Read from `runner_shared`. | E-02's verdict sentence should reuse that framing and that terminal reading so the two surfaces agree, instead of inventing a second phrasing. |
| F-08 | A mislabelled refusal has already cost this repository once: `integration_failed_combined_red` claimed "revalidation failed" for three items whose suite was never invoked, in run `run-20260921T105933Z-1994623`, and the fix was a separate kind. | Recorded at `INTEGRATION_REFUSAL_UNMEASURED`. | E-02 must not reuse conflict or red-suite wording for a refusal where neither happened. |
| F-09 | `runner_shared` already imports `check_engine` lazily and states the convention "NO NEW PATH LITERAL. Enumeration goes through `check_engine._iter_spec_records`". `check_engine` does not import `runner_shared`. | `rg` over both modules 2026-09-28. | Consuming Order 1's predicate is cycle-free and convention-conformant; a private copy here would violate it. |
| F-10 | The test harness this plan needs already exists: `_repo`, `_lane` (real `git worktree add`, returns a `WorktreeHandle`), `_passing_runner`, `_git_trace`, and `_unknown_write_set` (patches `merge_write_set` to return `None`), plus the `BOTH`/`_MODULES` host table. The dirty-overlap test is a directly imitable template asserting `integrated`, kind, reason substring, unmoved `HEAD`, unclobbered file and surviving branch. | Read from `tests/test_runner_shared.py`. | E-04 adds rows to an existing suite; no new harness, and `_unknown_write_set` covers row (c) with no new fixture. |
| F-11 | The suite baseline at authoring is `2937 passed, 2 skipped, 3 warnings in 45.62s` from a bare `python3 -m pytest` (201 deselected as `slow`/`livecorpus`). | Driven 2026-09-28 in this lane. | V-04 compares against this and must account for every added test. |

## Proposed changes (ordered, validatable)

1. E-01 adds the pre-merge placement refusal, reading the predicted post-merge tree and comparing its placement against `HEAD`'s, skipping when the prediction is unknown.
2. E-02 adds the cause constant, its mapping, the tagging call and the verdict sentence, naming the lifecycle fact rather than a conflict.
3. E-03 records, from the existing classifier, that the refusal is terminal; it changes no code if the reused kind already is.
4. E-04 adds the four-row integration regression table on both hosts, reusing the existing real-git lane harness.

## Deferred / out of scope (with reason)

- The structural `aw check` rule and the placement predicate: Order 1 (`tl2b2r`) owns them. This plan consumes the predicate and must not fork it.
  - Carrier: tl2b2r
- Any change to the deferral ladder's policy vocabulary, budget, statuses or classification: out of scope, and E-03 explicitly stops rather than widening if the evidence contradicts the terminal expectation.
  - Carrier-Declined: NOTHING IS OWED, because the expected outcome requires no change at all. The ladder already yields a terminal status for the kind E-01 reuses, and E-03's deliverable is the pasted evidence of that rather than an edit. A carrier would schedule work that only becomes real if E-03's measurement CONTRADICTS the expectation, and in that case E-03 already instructs the executor to STOP and report, which is the correct handling for a shared classification affecting every other refusal using that kind. Filing it now would assert a defect no evidence supports.
- The records-only re-derivation and history-append auto-resolve paths: unreachable on a clean merge (F-06).
  - Carrier-Declined: This row is a PROHIBITION with no residue. Both functions run only inside the post-`CONFLICT` branch and read merge index stages, so on the add/add shape there are no stages and no conflict to classify; extending either would add an unreachable branch carrying an untestable claim, which is the practice `runner_shared` explicitly forbids for the four unreachable gate causes. Nothing is deferred because nothing there is capable of covering this defect.
- The item's shape (present-at-base plus rename): already refused (F-01, F-02). No work.
  - Carrier-Declined: Nothing is owed because the behavior is already correct. MEASURED end to end (F-02): that shape returns `integrated=False`, `kind='fail-merge'`, cause `git-merge-conflict`, leaving one copy on main. A carrier would name work whose outcome already holds, and acting on it would risk adding a redundant gate for a condition git itself catches.
- Item fix-sketch point 3, the lane-triage REGRESSION/SAME/AHEAD verdict: no live consumer (`ut0vzr` is `executed`) and it would fork a second lane classifier alongside `classify_lane_integration`. Recorded in Order 1's F-09.
  - Carrier-Declined: Nothing is owed, for the reason Order 1's identical row records: the consumer has already run (`ut0vzr` is `executed`, and no lane-triage workflow file exists), and `classify_lane_integration`'s `LANE_SUPERSEDED` already distinguishes "the plan reached a terminal directory another way" from "work at risk". Filing a carrier would schedule a second lane classifier for a finished workflow.
- Repairing an existing duplicate: this tree has none.
  - Carrier-Declined: Nothing to repair, so nothing to carry. Zero duplicated artifact locations exist in this tree (Order 1 F-07). This plan is preventive by construction; where the condition already exists, Order 1's rule reports it and that finding is its own record.

## Scope check

- Over-scope: none. Both declared paths are edited by E-01 through E-04.
- Under-scope: none for this plan's stated goal. The hand-merge route the item also mentions is deliberately NOT covered here, because a git hook is local and skippable; it is covered by Order 1's `aw check` rule, which is the portable authority. That split is the reason this Set has two orders rather than one.

## Required tests / validation

- `python3 -m pytest` bare, per AGENTS.md, with the actual summary line pasted. Do not pass `-n0`, an extra `-q`, or `-p no:randomly`.
- The four rows of E-04, on both hosts, each asserting the template's full post-conditions and not merely the returned tuple.
- Driven evidence that the refusal is terminal, from the existing classifier (E-03).
- Driven evidence that the refusal reason round-trips through `read_integration_cause` and carries no absolute path.
- `aw ipd lint --phase pre-transition` conforming before any terminal move.

## Spec / documentation sync

No spec amendment and no `docs/` change. This plan adds a refusal for a condition already prohibited in substance: the lifecycle contract that a plan occupies exactly one disposition directory is stated in `AGENTS.md`'s plan-lifecycle section and in the plans README, and neither describes the integration path's internal refusal taxonomy, which lives in code and in the run records. If execution finds that a spec DOES enumerate the integration refusal kinds or causes, STOP and declare that `.spec.md` in `Scope-Paths` before amending it, per AGENTS.md's rule that a plan may amend a spec but must declare it.

## Open questions

### OQ-01: Should the refusal also fire for a duplicate that already exists on both sides?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to NO, refuse only where the merge INTRODUCES a second location. Refusing for a pre-existing duplicate would block recovery of a lane that had nothing to do with it, which is the "gate that reds during every normal run is a gate that gets bypassed" failure mode this codebase already records for lane reporting. The pre-existing case is Order 1's rule to REPORT, which is the right surface because it names the condition without holding work hostage. This tree has no such duplicate today (Order 1 F-07), so the choice costs nothing now and is a deliberate fail-open on a strictly narrower condition. E-04 row (d) pins it.

### OQ-02: Should this refusal be deferrable or terminal?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to TERMINAL, from the ladder's own criterion: a deferrable kind exists for a condition a re-attempt can clear (a transient dirty overlap, or a harness that could not measure), and repeating this merge cannot change the predicted placement. E-03 verifies rather than assumes this by driving the existing classifier, and stops if the evidence disagrees, because reclassifying a shared kind would affect every other refusal using it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the driven three-tuple from `integrate_lane_branch` on the add/add fixture, showing `integrated=False` and the terminal kind, PLUS the post-conditions as driven output: main's `HEAD` before and after (identical), the lane branch still listed by `git branch`, `git status --short` in main clean, and no `MERGE_HEAD` present. Paste the driven tuple on a clean lane showing `integrated=True`. Paste the driven result with `merge_write_set` patched to return `None`, showing the arm did NOT refuse. Paste the driven result for a pre-existing duplicate not introduced by the lane, showing no refusal. Paste the call site showing the predicate consumed is Order 1's function and not a local copy.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the new cause constant and its mapping entry verbatim. Paste the tagged reason string, then `read_integration_cause` applied to it showing the cause parsed and the operator-facing reason with the token stripped. Paste `terminal_refusal_verdict` for the new cause, showing a sentence that names the lifecycle condition and BOTH paths and does NOT claim a conflict or a failed suite. Paste the recorded `integration_ladder.cause` from a driven refusal. Paste the reason text with a check that it contains no absolute path and no git stderr.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the driven return of `classify_integration_refusal` and `decide_integration_deferral` for the new kind and cause, showing a terminal status and `deferrable=False`. State explicitly whether any code changed for this item, and if not, say that the existing table already yields the terminal outcome and that no branch was added.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the bare `python3 -m pytest` summary line and compare it to the F-11 baseline `2937 passed, 2 skipped, 3 warnings in 45.62s`, accounting for every added test. Paste the four row names and confirm each ran for BOTH hosts (the subTest host labels). Paste row (b)'s assertion that a clean lane still integrates, since that is the row catching an arm that blocks everything. Paste the add/add fixture's construction showing the plan is ABSENT at the merge base, so the row is not silently testing the already-refused F-02 shape.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; it is `to-review` and carries no `- Readiness:` field, because readiness is an output of `/plan-review` and writing one here would forge that attestation.

Dependency gate. `- Item-Dependencies: executed:tl2b2r` must be satisfied before execution. If Order 1's predicate is absent when this executes, STOP: a refusal built on a locally duplicated predicate is the drift the dependency exists to prevent, and the honest outcome is a dependency-blocked item rather than a second reader.

Execution contract. Commit ONLY the two declared `Scope-Paths` through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. If a change appears necessary outside those two paths, STOP and report rather than widening scope. Do not modify the backlog item's requirements, and do not set its status; the runner sets `graduated` on verification.

This plan inherits `- Blocks-Release: next` from item `wlyg3g` and must not silently drop it.

Post-gate lifecycle. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted, concrete evidence. A bare claim that tests passed is not evidence; the actual `python3 -m pytest` summary line is.
