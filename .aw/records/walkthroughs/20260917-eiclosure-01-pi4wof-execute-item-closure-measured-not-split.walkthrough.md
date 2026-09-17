# Walkthrough: `execute_item` was MEASURED, not split (`rununify` Order 07, `yrqyxb`)

- Date: 2026-09-17
- Id: pi4wof
- Target-Id: yrqyxb
- Plan: `.aw/records/plans/pending/20260915-rununify-07-yrqyxb-split-execute-item-into-a-shared-core-and-a-thin-host-hook.ipd.md`
- Base commit: `85c14014`
- Executed by: opencode/its_direct-pt3-claude-opus-5-1m-us, in lane `aw/lane/yrqyxb`
- Set: eiclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`, because a walkthrough may not reuse the Set id of another artifact type)

## Why this walkthrough exists

Most executed plans do not need one. This one does, because a reader coming to the plan later will see a
title that says "split `execute_item` into a shared core and a thin host hook" and a record saying the
split was not performed, and will reasonably ask whether the work was simply abandoned. It was not. The
plan as re-scoped at its own 2026-09-16 review is a MEASURE-AND-GUARD plan, and it did all five of its
items. What makes the execution worth narrating is that **three of the plan's own numbers inverted under
re-measurement, and one of them inverted in the plan's FAVOR** - the first time in this Set that a
re-measurement made the job smaller rather than larger.

## The shape of the turn

Five items, no product code. E-01 measured the closure. E-02 pinned the sixteen safety gates as behavior
on both hosts. E-03 enumerated every test that reads `execute_item`'s source text. E-04 wrote the
analysis the sequencing decision needs. E-05 guarded what was measured, including inverse assertions.
Two new test files, 35 tests, all green. Zero lines of `agent_workflows/` changed.

## Number one: the closure is ELEVEN, not eighteen

The plan's F-6 is the finding that made this plan NO-GO at review: body difference had been measured but
liftability inferred, and a closure scan found eighteen symbols still defined twice. Re-running that scan
at execution HEAD gives **eleven**.

The seven that left the list did not leave because the scan is different. They left because they are now
the **sanctioned thin-wrapper form**: `runner_shared` owns the real function and each host keeps a
one-line wrapper at the original name and signature. That is exactly what the maintainer's 2026-09-03
`818uru` OQ-02 ruling established as the correct mechanism. `git_head`, `git_status`, `driver_begin`,
`build_lane_outcome`, `integrate_lane_branch`, `integrate_review_lane_branch` and `save_state` are all in
that shape today.

**This matters more than the arithmetic.** A naive scan classifies a thin wrapper as "defined twice",
because syntactically it is: both modules contain a `def` of that name. Counting it as duplication is the
same category error as F-6's, with the sign reversed - F-6 caught a plan for treating textually-similar
bodies as liftable, and the same plan would have treated already-shared logic as still-forked. So the
scanner committed with this plan reports a `thin-wrapper-over-runner-shared` class separately, and
`tests/test_rununify_execute_item.py` asserts BOTH directions: a name in the fork list must not delegate,
and a name in the wrapper list must. Without the second assertion the wrapper list would be a place to
hide a re-fork by asserting nothing.

Six further names now resolve in `runner_shared` outright, several lifted by sibling `i3d6ml`, which
executed **earlier in this same run**. That is the Set's dependency ordering working as designed, and it
is why E-01 refuses to run on a stale list.

## Number two: the pins are 21 across 12 files, and three files were undeclared

The plan's F-8 counts fourteen source-reading pins across ten files, six asserting gate ordering. Measured
at HEAD: **21 pins across 12 files, eight asserting ordering.** The suite grew between authoring and
execution.

The part worth flagging is not the count but that **three of the twelve files were never in
`Scope-Paths`**, and two of them carry ordering pins over the gates F-2 calls load-bearing:
`tests/test_review_lane_isolation.py` (disposition before integration),
`tests/test_runner_backlog_close_in_lane.py` (close in lane before integrating), and
`tests/test_rununify_conflicts.py`. A future plan that performs the split must declare all twelve or the
finalize scope gate will discover the omission for it. Filed as backlog `3dg3dv` rather than quietly
added, because `Scope-Paths` is a declaration the runner reconciles and editing it silently would defeat
the reconciliation.

Sibling `i3d6ml` hit the same class of problem (its F-17: a scope fence that omitted a test file, found
at execution rather than by reading). Two independent occurrences in one Set suggests the authoring-time
method for finding pins is systematically incomplete, which is worth saying out loud.

## Number three: the baseline is 321, not 305

Minor, and recorded because the plan explicitly says a divergence is information rather than noise.

## What the analysis concluded, and why the split still did not happen

OQ-03 is `resolved` on disk. The maintainer's directive is unambiguous: one shared code base containing
100% of the otherwise-redundant code. So "should this be split?" is settled, and E-04 does not re-ask it.
The remaining question is a sequencing one, and the measurement answers it:

**Nine of the eleven forks survive the entire Set.** Sibling `tx6q0h` lifts exactly two. It
**deliberately refuses** two more, on grounds a later plan cannot simply overrule: `driver_actor` is a
host capability difference (oc reads a profile subsystem that greps to zero occurrences in
`agy_runipd.py`, so lifting it ships permanently dead branches), and `build_prompt` would change what
agy's agent is instructed to do (34 rendered lines differ, 32 of them carrying no host token). The other
seven are claimed by no plan in the Set at all.

So a shared core built today takes nine injected callables, each of which is itself still duplicated
logic. **De-duplicating the caller while its callees stay forked moves the duplication rather than
removing it**, which is not what the directive asks for. And landing it now means one commit that
relocates the repository's largest and most safety-critical symbol while simultaneously rewriting the 19
guards that would catch a mistake in it. That combination is the one worth refusing; either half alone
would be fine.

The recommended route (in E-04, with per-symbol accounting) is to let `tx6q0h` land, lift the four small
closure-clean forks individually, then the two larger ones, then extract cohesive blocks of
`execute_item` one at a time, letting the residual become thin as a consequence. Each step is small,
verifiable and revertible. Filed as backlog `dstnso`, because the Set as authored cannot reach 100% for
this function.

## The technique the maintainer's ruling authorizes, demonstrated

The maintainer ruled that source-reading guards are re-based deliberately, never weakened silently. E-02
demonstrates that on seven of the eight ordering pins: each guarantee is re-expressed on the **call
graph**, which survives a relocation, instead of on the byte offsets of one function's source.

Two of them needed care, and the care is the interesting part. `reconcile_disposition` is called **three
times per host**, and two of those calls sit on the early recovery path. My first version compared the
FIRST call site and failed on correct code; my second would have passed no matter where integration sat,
which is a guard that cannot fail. The shipped version anchors on the tuple assignment whose target is
named `disposition`, which is precisely how the existing pin at
`tests/test_lane_submission_collection.py:240` does it. Two wrong versions before the right one, on a
property that reads as obvious in the plan.

The eighth ordering pin (`tests/test_lane_session_isolation.py:125`) has **no behavioral equivalent
yet**. It asserts a structural subscript guard, and the honest replacement is a two-lane driver-level test
needing a real repo and the driver role. Filed as backlog `9eiwnl` and stated in the plan rather than
glossed, because claiming eight of eight would have been the easy and false thing to write.

## The 31 failures that are not failures

A bare `python3 -m pytest` in this lane reports **31 failed, 7517 passed**. That number needs its
explanation attached wherever it appears, or the next reader will spend an hour on it.

The 31 are an artifact of running inside a runner-managed worker lane. `AW_EXECUTION_ROLE=worker` is set,
which makes `ipd_lifecycle` refuse driver-only lifecycle verbs by design (`AW-LIFECYCLE-ROLE-001`,
`ipd_lifecycle.py:69`); the affected tests call `driver_begin` and friends directly. Two measurements
establish that they are neither mine nor a repo defect:

```
$ python3 -m pytest                                  # with my two files
31 failed, 7517 passed, 3 skipped, 2 xfailed
$ git stash push --include-untracked -- <my two files>; python3 -m pytest
31 failed, 7482 passed, 3 skipped, 2 xfailed         # PRE-CHANGE baseline, same 31
$ env -u AW_EXECUTION_ROLE python3 -m pytest
7548 passed, 3 skipped, 2 xfailed                    # zero failures
```

Identical failure set before and after; my files add 35 passing tests and no failures.

## Verification notes worth keeping

Every guard in this plan was shown non-vacuous, because a test that cannot fail proves nothing:

- The gate net: `assert_child_tool_identity` was removed from agy's `execute_item`. Three tests fired and
  each named the removed gate and the host. Restored via `git checkout --`, re-verified green.
- The guard suite, direction one: a real fork (`driver_finalize`) was misfiled as a thin wrapper. Three
  tests fired, naming the symbol.
- The guard suite, direction two: a real fork (`evaluate_clean_base_for_launch`) was actually converted
  into a `runner_shared` delegation. The inverse assertion fired, naming the symbol.

Both product-code sabotages were reverted with `git checkout --` and confirmed by an empty
`git diff --stat`, so the committed tree contains no experiment residue.

One process note: a `pre-commit` hook reformatted both test files and rejected the first commit attempt.
Per the execution contract I re-ran `git diff --cached --name-only` before retrying (a hook failure
invalidates the earlier index check), confirmed only my two files were staged, re-ran the suite against
the reformatted files, and then committed.

## Honest limits

- The gate net pins that each gate exists, is reached from `execute_item` on both hosts, and refuses what
  it is designed to refuse. It does **not** drive a full driver turn, so it cannot prove the gates compose
  correctly under every real interleaving. That assurance stays with the host CLI suites. This is stated
  in the file's own docstring so it cannot be over-read later.
- A call-graph ordering assertion is weaker than a source-offset one in one specific way: it can be
  satisfied by a call on an unrelated branch. It is stronger in the way this Set needs: it survives the
  relocation the split performs. That trade is deliberate and recorded.
- No independent reviewer re-examined this execution. The plan's readiness rested on a maintainer
  attestation rather than a fresh review round, which the plan itself records.


---

# Appendix A: E-03, the source-inspection pin inventory

Measured at execution HEAD `85c14014` with
`.aw/state/lane-submissions/.../evidence/pin_scan.py` (committed beside this file, so the table
is reproducible rather than asserted).

## Headline correction to the plan

The plan's F-8 states **fourteen pins across ten test files**, six of them ordering pins. At
execution HEAD the real figure is **21 pins across 12 files** (excluding the two files this plan
itself adds). The plan's count was taken 2026-09-16; the suite has grown since, and three of the
twelve files were **never declared in `Scope-Paths`**:

| File missing from `Scope-Paths` | Pins | Why it matters |
|---|---|---|
| `tests/test_review_lane_isolation.py` | 1 | asserts disposition-before-integration ordering (an F-2 gate) |
| `tests/test_runner_backlog_close_in_lane.py` | 2 | asserts close-in-lane-before-integrate ordering (an F-2 gate) |
| `tests/test_rununify_conflicts.py` | 1 | asserts agy's truthful `isolate` value at the `driver_begin` call |

So the plan under-counted the ordering pins as well: **eight** pins assert ordering, not six. This
is recorded as a finding rather than silently fixed, because `Scope-Paths` is a declaration the
runner reconciles and the omission would otherwise be discovered at finalize.

## The 21 pins, with a thin-caller verdict for each

A "thin caller" means the state after the split: `execute_item` in each host becomes a short
function that calls a shared core. Verdict legend:

* **BREAKS** - the assertion reads text that would no longer be in `execute_item`'s body.
* **SURVIVES** - the assertion would still hold on the thin caller.

| # | Pin | Kind | Asserts | Verdict |
|---|---|---|---|---|
| 1 | `test_dirty_base_gate.py:184` | getsource | `report_untracked_dirt_at_run_start` is **absent** (it belongs in `initialize_run`) | SURVIVES (a negative assertion; a thin caller also lacks it) |
| 2 | `test_dirty_base_gate.py:378` | getsource | `"if isolate and self_finalize and not is_review:"` absent, `"shared_tree=not isolate"` present | BREAKS |
| 3 | `test_dirty_base_gate.py:532` | getsource | `"decision.warned"` present | BREAKS |
| 4 | `test_dirty_base_gate.py:829` | getsource | `"shared_tree=not isolate"` present | BREAKS |
| 5 | **`test_dirty_base_gate.py:878`** | getsource | **ORDERING**: clean-base guard before spawn and before allocation | BREAKS |
| 6 | `test_dirty_base_gate.py:892` | getsource | `clean_base_launch_decision(` present; `CLEAN_BASE_REFUSE`/`CLEAN_BASE_CONSENTED` absent | BREAKS (presence half) |
| 7 | `test_defect_report.py:809` | AST by name | the defect-report persistence `if` block contains no `raise`/status write/`driver_finalize`/`return` | BREAKS |
| 8 | **`test_lane_clean_base.py:233`** | split-def | **ORDERING**: guard before spawn and before allocation | BREAKS |
| 9 | `test_lane_clean_base.py:264` | split-def | `attempt["clean_base_dirty_paths"]`, `"event": "clean-base-refused"`, `"event": "clean-base-warning"`, `attempt["clean_base_warning"]` | BREAKS |
| 10 | `test_lane_clean_base.py:617` | split-def | the `if decision.warned:` branch contains no `print(` (record only; operator line is once per run) | BREAKS |
| 11 | **`test_lane_session_isolation.py:125`** | getsource + AST | **ORDERING/STRUCTURE**: the `state["set_sessions"][...]` promotion sits under a `work_dir` guard | BREAKS |
| 12 | `test_lane_session_isolation.py:167` | getsource + AST | agy assigns `session_id = None` and `use_continue = False` | BREAKS |
| 13 | **`test_lane_submission_collection.py:240`** | AST by name | **ORDERING**: `collect_lane_submissions` before the `disposition` tuple assignment | BREAKS |
| 14 | **`test_lane_tool_identity.py:762`** | getsource | **ORDERING**: `assert_child_tool_identity` before `driver_begin(` | BREAKS |
| 15 | `test_oc_runipd_cli.py:243` | getsource | `tracker: StreamTracker | None = None` in the signature, `run_opencode(`, `tracker=tracker` | PARTLY SURVIVES (signature stays on the thin caller; the spawn call moves) |
| 16 | **`test_review_lane_isolation.py:717`** | getsource + AST | **ORDERING**: `reconcile_disposition` before `integrate_lane_branch` | BREAKS |
| 17 | `test_runner_backlog_close.py:1218` | getsource | the literal `process_backlog_close(run_dir, state, item)` | BREAKS |
| 18 | **`test_runner_backlog_close_in_lane.py:1043`** | getsource | **ORDERING**: `lane_repo=Path(work_dir)` before `integrated, integ_reason, integ_kind =`; plus `lane_handle=wt_handle` | BREAKS |
| 19 | `test_runner_backlog_close_in_lane.py:1063` | getsource | the post-merge close is guarded by `if not (item.get("backlog_close") or {}).get("closed"):` | BREAKS |
| 20 | `test_run_flag_surface.py:887` | getsource + regex | every `get("full_auto", ...)` default is exactly `False` | BREAKS |
| 21 | `test_rununify_conflicts.py:450` | getsource | agy passes `driver_begin(..., isolated=True)` in the isolate branch and the 3-arg form otherwise | BREAKS |
| 22 | `test_agy_runipd_cli.py:1579` | getsource | signature + `run_agy_turn(` + `tracker=tracker` | PARTLY SURVIVES (as #15) |

**Count: 22 rows for 21 pin sites** (row 15 and row 22 are the two host-CLI twins; the scanner
reports 21 distinct source-reading lines).

Verdict summary: **19 BREAK, 1 SURVIVES, 2 PARTLY SURVIVE.** The plan's claim that "a thin caller
satisfies none of the fourteen" is very nearly right and slightly overstated: pin #1 is a NEGATIVE
assertion and survives a split trivially, and the two host-CLI pins survive in their signature half.

## The eight ordering pins and their behavioral equivalents

This is what E-03 owes: for each ordering pin, the assertion that would preserve the same
guarantee without reading `execute_item`'s source text. Each is **already implemented and passing**
in `tests/test_rununify_execute_item_gates.py` (E-02), so this is a demonstrated route, not a
proposal.

| Ordering pin | Guarantee | Behavioral equivalent (implemented in E-02) |
|---|---|---|
| `test_dirty_base_gate.py:878`, `test_lane_clean_base.py:233` | the base is judged before a lane is cut from it and before the agent is spawned | `test_the_clean_base_guard_precedes_worktree_allocation`, `test_the_clean_base_verdict_precedes_the_host_spawn` (call-graph ordering, which survives relocation) plus `test_a_dirty_tracked_base_refuses_a_shared_tree_launch` (the refusal itself) |
| `test_lane_tool_identity.py:762` | no nested `aw` lifecycle call runs with an unverified child tool | `test_tool_identity_is_asserted_before_the_first_nested_lifecycle_call` |
| `test_lane_submission_collection.py:240` | the lane's own submission decides the outcome, not driver-side inference | `test_submissions_are_collected_before_the_disposition_is_reconciled` (anchored on the `disposition` tuple assignment, exactly as the existing pin is) |
| `test_review_lane_isolation.py:717` | integration is gated on a decided disposition | `test_the_disposition_is_reconciled_before_integration` |
| `test_runner_backlog_close_in_lane.py:1043` | unverified work cannot reach main | `test_integration_is_earned_before_the_merge_happens` |
| `test_lane_session_isolation.py:125` | a lane session is not promoted into the Set register | NOT YET REPLACED. This one asserts a STRUCTURAL guard (a subscript write under a `work_dir` condition), and the honest behavioral equivalent is a driver-level test that runs two lanes and asserts the second does not inherit the first's session. That needs a real repo and a driver role, so it belongs with the host CLI suites, not this net. Recorded as the one ordering pin whose replacement is NOT yet written. |

**A caveat worth stating plainly.** A call-graph ordering assertion is weaker than a source-offset
one in a specific way: it compares the first (or the anchoring) call site by line, so it can be
satisfied by a call in dead code or on an unrelated branch. It is stronger in the way that matters
for this Set: it survives the relocation the split performs. Two of the six behavioral equivalents
above therefore anchor on the `disposition` ASSIGNMENT rather than on the first
`reconcile_disposition` call, because that function is called three times per host and the two
early calls sit on the recovery path. Anchoring naively there would have produced a guard that
passes no matter where integration sits, which is the class of unfalsifiable evidence the
orchestrator's F10 note warns about.

## Baseline

No test file was edited by this item. Two files were ADDED
(`tests/test_rununify_execute_item_gates.py`, `tests/test_rununify_execute_item.py`); the 12 pin
files are untouched, which is why they are declared-but-unmodified and require `--scope-ack`.


---

# Appendix B: E-04, the split analysis

Measured at execution HEAD `85c14014`, in lane `aw/lane/yrqyxb`.

## What changed since the plan was written, stated first

The plan (and its 2026-09-16 review) recorded OQ-03 as `Blocking: yes` and OPEN. **It is now
`resolved`**: the maintainer's 2026-09-16 directive is unambiguous and is recorded in the plan
itself:

> at the end of the SET, there should be one code base shared by the two runners that contains
> 100% of the otherwise redundant code that currently is duplicated between the two runners

So the route question ("should this be split at all?") is settled: **route (A), do the split**, with
the two obstacles ruled to be work rather than blockers. This item therefore is NOT a request for a
decision that has already been made. It is the measurement the maintainer's chosen route needs in
order to be executed correctly, plus an honest statement of why it is not executed *by this plan*.

## (a) The dependencies a shared core would take, and who lifts them

E-01's closure scan at this HEAD: `execute_item` closes over **55 module-level names** (54 free
names on each host, union 55). Classified:

| Class | Count | Consequence |
|---|---|---|
| Resolves in `runner_shared` today | 20 | moves for free |
| Already ONE object (agy imports from oc, or both import a third module) | 13 | needs relocation, not de-duplication |
| Already a sanctioned THIN WRAPPER over `runner_shared` on both hosts | 7 | single-implementation already; NOT duplication |
| Constant defined twice with equal values | 2 (`SUCCESS_STATES`, `DEFAULT_STALL_TIMEOUT`) | can move with the core |
| Genuinely host-specific (the intended hook) | 1 (`run_opencode` / `run_agy_turn`) | this is F-3 and it is correct |
| **STILL genuinely double-defined** | **11** | each becomes an injected parameter |

**The plan's authored figure was 18. It is now 11**, and the improvement is real rather than a
measurement artifact. Seven names the plan listed have since become thin delegations to
`runner_shared` (`driver_begin` by `ct4w0a`; `git_head`, `git_status`, `build_lane_outcome`,
`integrate_lane_branch`, `integrate_review_lane_branch`, `save_state` by earlier work), and six more
(`StallTimeout`, `attempt_log_path`, `build_review_prompt`, `make_integration_validation_runner`,
`sync_receipt_into_worktree`, `write_prompt`) now resolve in `runner_shared` outright, several of
them lifted by sibling `i3d6ml` which executed EARLIER IN THIS SAME RUN.

The eleven that remain, with the owning sibling and whether that sibling actually lifts it:

| Symbol | oc / agy | Owning sibling | Does that sibling lift it? |
|---|---|---|---|
| `_compute_scope_reconciliation` | 1273 / 1011 | `tx6q0h` (04) E-02 | **YES**, named explicitly in E-02's five |
| `build_verifier_prompt` | 5528 / 2738 | `tx6q0h` (04) E-02 | **YES**, named explicitly (and its F-13 closes a live "Never push" gap in agy's verifier) |
| `driver_actor` | 933 / 971 | `tx6q0h` (04) E-05 | **NO, DELIBERATELY.** Its E-05 refuses: oc reads `options.variant`/`options.launch_profile` from a profile subsystem that greps to ZERO in `agy_runipd.py`, so lifting ships dead branches. This is a host CAPABILITY difference. |
| `build_prompt` | 5399 / 2624 | `tx6q0h` (04) E-05 + its own OQ-03 | **NO, BLOCKED.** The emitted prompts differ by 34 rendered lines, 32 carrying no host token, so unifying changes what agy's agent is INSTRUCTED to do. That child's OQ-03 escalates it. |
| `driver_finalize` | 1305 / 1041 | none claims it | **NO.** Depends on `_compute_scope_reconciliation` (04), so it is liftable only after 04. |
| `evaluate_clean_base_for_launch` | 2424 / 1370 | none claims it | **NO.** Small and closure-clean (both bodies are 2 statements over `_run_git` + `lane_containment`); an easy future lift. |
| `reconcile_disposition` | 6656 / 3389 | none claims it | **NO.** 107 / 84 lines, the largest of the eleven. |
| `route_recovery_turn` | 5306 / 2612 | none claims it | **NO.** oc 76 lines vs agy 9: a genuine capability asymmetry, not drift. |
| `set_plan_approved` | 792 / 909 | none claims it | **NO.** 74 / 59 lines. |
| `_record_checkpoint_stop` | 5802 / 2901 | none claims it | **NO.** |
| `_record_forced_stop` | 5837 / 2935 | none claims it | **NO.** |

## (b) How many injections remain after the whole Set executes

**Answer: nine of eleven.** Sibling `tx6q0h` lifts exactly two
(`_compute_scope_reconciliation`, `build_verifier_prompt`). Two more (`driver_actor`,
`build_prompt`) are DELIBERATELY REFUSED by that same sibling on measured grounds, one of them
(`build_prompt`) behind its own blocking OQ-03. The remaining seven are claimed by no sibling in
this Set at all.

So the plan's F-7 conclusion holds and is slightly worse than it stated in one respect and better
in another: better, because eleven is fewer than eighteen; worse, because only **two** clear
through sibling work rather than the "at best seven" F-7 estimated, and because two of the nine
are refused on grounds a later plan cannot simply overrule (a capability difference and an
agent-instruction change).

**Is nine acceptable?** This is the question V-04 requires an answer to, so here it is, plainly:
**nine injected parameters is a poor shape for a shared core, and it is not the right next act for
this function.** The reasoning, not the aesthetics:

1. The maintainer's `818uru` OQ-02 ruling sanctions the shared-core-plus-thin-wrapper form for a
   function whose OUTSIDE dependencies are injected. That form works because the wrapper binds the
   dependency once at the original name and signature, so no call site changes. It scales badly
   here for a different reason: `execute_item` is not called by 86 sites, it is called by
   `run_queue`; the cost is not call-site churn but that a nine-parameter core makes the shared
   body's control flow depend on nine host-supplied callables, each of which is itself still
   duplicated logic. De-duplicating the CALLER while its nine CALLEES stay forked moves the
   duplication rather than removing it, and the Set's own definition of done is 100 percent
   de-duplication.
2. Two of the nine are not merely unlifted but REFUSED on evidence (`driver_actor`'s dead
   branches, `build_prompt`'s changed agent instructions). A shared core must therefore keep a
   host hook for them permanently, which is fine, but it means the honest end state for
   `execute_item` is a shared core plus a hook carrying at least those two, not a clean split.
3. Nineteen of the 21 source-reading pins BREAK on a thin caller (E-03), eight of them ordering
   pins over the sixteen safety gates. Re-basing them is legitimate work under the maintainer's
   ruling, and E-02 demonstrates the technique on seven of the eight. But doing all of it in the
   SAME change that injects nine dependencies into a 1672-line function means one commit that
   simultaneously relocates the repository's largest and most safety-critical symbol and rewrites
   the guards that would catch a mistake in it. That is the one combination worth refusing.

## (c) The pins

21 source-reading pins across 12 files; 19 break on a thin caller; **eight** assert ordering, not
six as the plan states. Three of the twelve files were never declared in `Scope-Paths`. Full
per-pin verdicts and the behavioral equivalent for each ordering pin are in
`E03-pin-inventory.md`. Seven of the eight ordering guarantees are now asserted behaviorally and
passing in `tests/test_rununify_execute_item_gates.py`; the eighth
(`test_lane_session_isolation.py:125`, the set-session promotion guard) needs a driver-level test
with a real repo and is the one replacement NOT yet written.

## (d) Recommendation on route

**Route (B), shrink first, then let the split fall out** - which is now a TACTIC for reaching the
maintainer's route (A) objective, not an alternative to it. Concretely, and in dependency order:

1. Let `tx6q0h` (04) land. It removes two of the eleven and repairs two live defects on the way.
2. Lift the four SMALL closure-clean forks as individual acts, each with its own pin conversion:
   `evaluate_clean_base_for_launch` (2 statements, and E-02 already pins its behavior),
   `_record_checkpoint_stop`, `_record_forced_stop`, `set_plan_approved`. None of these needs
   `execute_item` to move at all.
3. Then `driver_finalize` (unblocked once 04 lands) and `reconcile_disposition`.
4. Extract cohesive BLOCKS of `execute_item` into named shared helpers one at a time - the
   clean-base preflight, the submission-and-disposition block, the integration block - each
   carrying the two or three pins that read it, converted to behavioral assertions as E-02
   demonstrates.
5. The residual `execute_item` becomes thin as a CONSEQUENCE, with a hook that carries the spawn
   plus the two permanently-host-specific symbols. At that point 100 percent de-duplication of
   this function's SHARED logic is achieved, which is what the directive asks for.

Each step is small, independently verifiable, and independently revertible, and no step breaks
nineteen guards at once. The alternative (inject nine now) reaches a shared core whose body is a
nine-parameter shell over still-forked callees, and pays the entire pin-rebasing cost in one commit.

## Spec consequence, per the plan's spec-sync section

Converting an ordering pin from source text to a behavioral assertion touches a spec-governed
guarantee: spec `c4gd2h` states the clean-base and lane-containment rules cited as R5.4/R6.1 by
`tests/test_lane_clean_base.py`, and spec `7ckptx` covers lane containment. **This plan changed no
spec, because it changed no product code and edited no existing pin**; the E-02 net is purely
additive. A future plan that REPLACES an existing ordering pin must carry the spec amendment in the
same change and declare the spec path in `Scope-Paths`.

## What was NOT done, said plainly

**No split was performed.** `execute_item` still has two definitions, one per host, and there is no
shared core. `tests/test_rununify_execute_item.py` asserts that state MECHANICALLY (including the
inverse assertion that the eleven are still double-defined), so the omission is a recorded,
guarded state rather than an oversight a later reader might "finish" without reading this analysis.

OQ-03 is RESOLVED and its answer is "do the split"; what remains is a SEQUENCING judgment, which
this analysis makes: the split is the right destination and this position in the Set is the wrong
place to jump to it in one act. The recommended sequence above reaches the maintainer's stated
objective. Whether to spend a further child on step 2's four small lifts, or to fold them into the
existing siblings, is the maintainer's call.


---

# Appendix C: reproducing the measurements

Both scanners are committed with this plan so every number above is re-derivable rather than
asserted. They live beside the plan's other execution evidence and are also reproduced here in the
lane submission for this run. Run each from the repository root:

    python3 <closure_scan.py>   # E-01: the closure classification and the two excluded false positives
    python3 <pin_scan.py>       # E-03: every test that reads execute_item's source text

`closure_scan.py` walks `execute_item` with full scope tracking (comprehensions, lambdas, nested
defs, function-local imports, `except as`, `with as`, `for` targets), so a name bound locally never
surfaces as a dependency. That is what excludes `extract_log_metrics` and `reask_prompt_path`
structurally rather than by a hardcoded skip list. It then classifies each free name against
`runner_shared`, and separates a genuine fork from the sanctioned thin-wrapper form by checking
whether the body is a single delegating `runner_shared.X(...)` call.

`pin_scan.py` finds the three ways a test reaches this function's source text
(`inspect.getsource`, an AST lookup by function name, and `split("def execute_item")`) and reports
the enclosing test name for each, which is what makes the per-pin verdict table checkable.
