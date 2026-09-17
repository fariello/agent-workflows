# Walkthrough: `run_queue` was MEASURED, and a swallowed run-fatal error fell out (`rununify` Order 08, `ty3cj6`)

- Date: 2026-09-17
- Id: k2vn8p
- Target-Id: ty3cj6
- Plan: `.aw/records/plans/pending/20260915-rununify-08-ty3cj6-split-run-queue-into-a-shared-core-and-a-thin-host-hook.ipd.md`
- Base commit: `24932638`
- Executed by: opencode/its_direct-pt3-claude-opus-5-1m-us, in lane `aw/lane/ty3cj6`
- Set: rqclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`, because a walkthrough may not reuse the Set id of another artifact type)

## Why this walkthrough exists

Three reasons, in descending order of importance.

FIRST, the characterization pass found a **live safety-gate defect that has been latent since
2026-08-30**: `run_queue`'s dedicated `except ToolIdentityError` clause swallows a documented
run-fatal error on BOTH hosts, so a tool-identity mismatch dispatches every remaining item under the
same wrong control plane instead of aborting. That is a bigger finding than anything the plan set out
to do, it was introduced by a merge rather than by a decision, and 29 green tests sit on top of it.

SECOND, a reader coming to this plan later will see a title that says "split `run_queue` into a
shared core and a thin host hook" and a record saying no split was performed, and will reasonably ask
whether the work was abandoned. It was not. The plan as re-scoped at its 2026-09-16 review is a
MEASURE-AND-GUARD plan and it did all five of its items.

THIRD, one of the plan's guards was **vacuous in its first version** and the reason is worth keeping:
it is the same "a test that cannot fail proves nothing" trap sibling `yrqyxb` hit from a different
angle, and it took a measurement rather than a reading to notice.

## Number one: the closure reproduces EXACTLY, which is itself new

Both prior children of this Set found their numbers had moved: `i3d6ml` was cut from 48 symbols to 9
at review, and `yrqyxb`'s fork count IMPROVED from 18 to 11 under re-measurement. This plan's numbers
did not move at all. Measured at HEAD `24932638`:

| Quantity | Plan's claim | Measured |
|---|---|---|
| `run_queue` length, oc / agy | 381 / 336 | 403 / 347 |
| Code lines (comments and blanks stripped) | 229 / 227 | 234 / 232 |
| **Differing code lines** | **12** | **12** |
| Differing lines bearing a host token | 2 | 2 |
| **Free module-level names (the closure)** | **41** | **41** |
| **Still double-defined** | **11** | **11** |

The raw line counts grew by ~20 (ordinary comment growth since 2026-09-15); every load-bearing
number is identical, and the eleven forks are the same eleven by name.

**Why the two numbers must be read together.** 12 differing code lines out of 234 is why the split
LOOKS cheap. 11 still-forked dependencies is why it is not. `run_queue` is a DISPATCH LOOP: its body
is almost entirely calls to other symbols, so its own text barely differs while nearly everything it
DOES lives behind a name that has not been unified. Conflating those two properties is exactly what
made both this plan and sibling `i3d6ml` NO-GO at review, so `tests/test_rununify_run_queue.py`
asserts them side by side in one class, with a message telling a future reader why.

## Number two: the swallowed run-fatal error

This was not on the plan's list. It surfaced because E-02 pins behavior rather than source text: a
test asserting "a `ToolIdentityError` aborts the run" hung on a spin detector instead of passing.

The clause, identical on both hosts:

```python
except ToolIdentityError:
    # lanetruth Order 01 (af7i6p) E-04 / OQ-02: RUN-FATAL, so it must NOT be caught by the
    # item-local `except DriverError` below ... Re-raise to abort the whole run.
    save_state(run_dir, state)
```

The comment promises a re-raise. There is no `raise`.

**It was authored with one.** `b04c70ce` (lanetruth `af7i6p`, 2026-08-30) added `save_state(run_dir,
state)` followed by a bare `raise`. It is gone by `04a613aa`, the `laneorphan-01` / `zwnjp3` lane
merge the same day, whose FIRST parent (`34aa1812`) has the `raise` and whose SECOND parent
(`6345f3d1`) does not have the clause at all. So a merge resolution dropped a safety behavior and
nobody decided to.

**The measured consequence.** `execute_item` writes `item["status"] = "running"` BEFORE it calls
`assert_child_tool_identity` (`oc_runipd.py:6807` vs `:7057`; `agy_runipd.py:3558` vs `:3755`). So on
a real mismatch, driving both hosts' real `run_queue`:

```
oc  rc=1  dispatches=2  statuses={'aaa111': 'running', 'bbb222': 'running'}
agy rc=1  dispatches=2  (2 == the run did NOT abort)
```

Every remaining item runs under the same wrong control plane, which is precisely the outcome
`af7i6p` OQ-02 says it rejects, and each item is stranded at the non-terminal status `running`, which
is neither terminal nor re-queueable by `--retry-incomplete`.

**Why 29 green tests did not notice.** `tests/test_lane_tool_identity.py:733` asserts only that
`except ToolIdentityError` appears BEFORE `except DriverError` in `inspect.getsource(run_queue)`. It
does. The pin is green on broken code, and the whole file passes. This is the generic weakness of a
source-offset pin, and it is the strongest available argument for the behavioral net this plan
added, so it is asserted as a test
(`test_the_existing_source_pin_is_green_on_this_broken_code`) rather than merely written down.

**Why it was not fixed here.** Restoring the `raise` changes control flow on the run-fatal path of
both runners. This plan's E-03 authorizes ONE named two-line repair, and the parent Set forbids a
child changing what a runner does; the `raise` also changes which handler sees the exception on the
interrupt/teardown path directly below the clause, so it needs its own characterization. Filed as
backlog `mo3h5b` (high, bug), reported in the turn's defect report, and pinned as three tests whose
docstrings instruct that they be DELETED and replaced when the `raise` returns. So the fix announces
itself as a test failure instead of silently diverging from the guard.

## Number three: the guard that could not fail

E-02's F-9 test (agy's missing signal refreshes) PASSED on the defective host in its first version.
The reason is subtle and general.

The property is "after a state reload, the shutdown reporter must not be looking at the old
snapshot". The obvious assertion compares published item STATUSES against the live ones. That
assertion cannot fail under a test stub, because the stub mutates the very dict the loop is holding,
so the pre-reload snapshot and the live object ARE the same object and agree by construction.

What actually distinguishes a refreshed host from a stale one is OBJECT IDENTITY. Measured:

```
oc_runipd  published-is-live-object at each turn: [True]
agy_runipd published-is-live-object at each turn: [False]
```

That probe fails on the defect and passes after the repair, both shown. The lesson is the one the
orchestrator's F10 note already warns about, encountered from a new direction: a guard must be
demonstrated failing on the broken code, and "it passes now" is not evidence that it would.

## Number four: the "every reload must refresh" rule was wrong, and oc proved it

The natural way to pin E-03's repair as a property rather than a count is: every `state =
load_state(...)` inside the dispatch loop must be followed by a `register_signal_report`. That rule
reported FOUR violations on oc, the host this plan treats as correct.

Reading them settled it rather than guessing: `oc_runipd.py:8751` is the post-cascade reload,
`:8916` sits inside the `KeyboardInterrupt` handler and hands `state` straight to
`reclaim_lanes_on_interrupt`, and `:8946`/`:8954` both immediately `break` out of the loop and reach
the end-of-run refresh at `:9021` before any report can render. None is a defect.

So the rule is scoped to reloads after which the loop KEEPS GOING, which is exactly the integration
ladder, and the end-of-run refresh the break paths depend on is pinned SEPARATELY, because the
scoping argument collapses without it. Reported as decision `09-ty3cj6-D3` with the residual risk
stated in the test's own docstring: a future reload on a continuing path outside a
`deferred_integration_items` guard would not be checked.

The alternative was to report oc as defective at four more sites, which would have been an
unevidenced claim, and a guard that fires on correct code gets deleted rather than heeded.

## Number five: the pins are 10 across 9 files, not the plan's 6

The plan's F-10 counts six source-inspection pins. Measured with the committed scanner: **10 pin
sites across 9 files**. The three the plan does not name are
`tests/test_agy_runipd_shim.py:37` and `tests/test_oc_runipd_shim.py:40` (both NEGATIVE assertions
that the shim contains no `def run_queue`, which survive a split trivially and in fact get STRONGER)
and the second `test_runner_shared.py` pin.

Unlike sibling `yrqyxb`, which found three undeclared files, **every file carrying a pin here is
already in `Scope-Paths`** except the two shim files, whose pins are negative. So the fence held.

## What the analysis concluded

OQ-03 is `resolved` on disk and the maintainer's directive is unambiguous: one shared code base with
100% of the otherwise-redundant code. So "should this be split?" is settled and E-04 does not re-ask
it. The remaining question is sequencing, and the measurement answers it: **nine of the eleven forks
survive the entire Set.**

Sibling `tx6q0h` lifts exactly two (`render_continuation_hint`, `write_report`). It DELIBERATELY
REFUSES `driver_actor` on measured grounds a later plan cannot simply overrule (oc reads a profile
subsystem that greps to zero occurrences in `agy_runipd.py`, so lifting it ships permanently dead
branches). `disable_lane_prompt` can NEVER move while `UnmovableSymbolTests` stands. `execute_item`
belongs to executed sibling `yrqyxb`, which also measured rather than split. The remaining seven are
claimed by no plan in the Set.

**The actionable half, which is better news than that paragraph suggests.** FOUR of the seven
unclaimed forks are CLOSURE-CLEAN TODAY and liftable right now, individually, without `run_queue`
moving at all:

| Symbol | oc / agy code lines | Differing | Closure |
|---|---|---|---|
| `_observe_between_turn_stop` | 33 / 27 | 12 | clean |
| `_record_deliberate_stop` | 19 / 17 | 8 | clean |
| `requeue_interrupted` | 39 / 32 | 15 | clean |
| `reconcile_interrupted` | 69 / 69 | **2** | clean |

`reconcile_interrupted` is 69 code lines on both hosts differing by TWO.
`reclaim_lanes_on_interrupt` is similarly near-identical (134/134, two differing lines) but is NOT
clean: it closes over both `disable_lane_prompt` and `_lane_reclaim_prompt`, the pair sibling
`i3d6ml` independently measured as sharing an unmovable module global (its backlog `8hx3g3`). Two
children have now hit that same global from three directions, which is worth noting as a structural
obstacle rather than three coincidences.

Filed as backlog `5jsjnr`, because the Set as authored cannot reach 100% for this function.

## Honest limits

- The characterization net pins the LOOP's decisions: which items it selects, in what order, what
  statuses it writes, when it stops, what it publishes. It does not prove the work each turn performs
  is correct; that assurance stays with the host CLI suites and `execute_item`'s own coverage. Stated
  in the file's docstring so it cannot be over-read.
- No real signal is sent. A test that sends SIGINT to the runner is not safe under `-n auto`, so the
  signal path is characterized through the state the handler WOULD publish, which is the property F-9
  is about but is one step removed from a live interrupt.
- The `ToolIdentityError` defect is pinned, not fixed. The repository is shipping that behavior today
  and this plan did not change it.
- No independent reviewer re-examined this execution. The plan's readiness rested on a maintainer
  attestation rather than a fresh review round, which the plan itself records.

## The 32 bare-suite failures that are not failures

A bare `python3 -m pytest` in this lane reports **32 failed, 7583 passed**. That number needs its
explanation attached wherever it appears.

The 32 are an artifact of running inside a runner-managed worker lane: `AW_EXECUTION_ROLE=worker` is
set, which makes `ipd_lifecycle` refuse driver-only lifecycle verbs by design
(`AW-LIFECYCLE-ROLE-001`), and the affected tests call `driver_begin` and friends directly. Three
measurements establish that they are not mine:

```
$ python3 -m pytest                        # PRE-change baseline, at HEAD 24932638
32 failed, 7516 passed, 3 skipped, 2 xfailed
$ python3 -m pytest                        # POST-change, with my three files
32 failed, 7583 passed, 3 skipped, 2 xfailed
$ diff <(pre FAILED lines) <(post FAILED lines)
IDENTICAL
$ env -u AW_EXECUTION_ROLE python3 -m pytest    # pre-change, role unset
7548 passed, 3 skipped, 2 xfailed
```

Byte-identical failure sets before and after; +67 passing tests and no new failure.

With the role unset the suite is clean apart from ONE test,
`test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`,
which spawns a real driver subprocess and signals it. It is a **pre-existing load-dependent flake, not
mine**, established by reverting E-03 and re-running the whole suite:

```
$ env -u AW_EXECUTION_ROLE python3 -m pytest        # with E-03
1 failed, 7614 passed          # the sigint test
$ git stash push -- agent_workflows/agy_runipd.py   # E-03 reverted, tests kept
$ env -u AW_EXECUTION_ROLE python3 -m pytest
6 failed, 7609 passed          # the SAME sigint test, plus my 5 guards firing on unrepaired agy
$ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_runner_backlog_close.py
47 passed                      # green in isolation
```

That third measurement is the strongest non-vacuity evidence in this turn and it was not planned: with
E-03 reverted, FIVE of the guards this plan added fail **in a full-suite run**, naming both the site
count and the staleness property, while everything else stays green. A guard set that goes green the
moment the repair lands and red the moment it is removed is the whole requirement, and here it is
demonstrated at suite scale rather than only in a targeted sabotage.


---

# Appendix A: E-01, the closure classification

Measured at execution HEAD `24932638` with `closure_scan.py` (reproduced in Appendix C). The scanner
walks `run_queue` with full scope tracking (parameters, assignments, walrus, `for`/`with`/`except`
targets, comprehension and lambda scopes, nested `def`/`class`, function-local imports,
`global`/`nonlocal`), so a name bound locally never surfaces as a dependency.

```
oc free module-level names : 41
agy free module-level names: 41
UNION                      : 41
```

| Class | Count | Members |
|---|---|---|
| resolves-in-runner-shared | 7 | `DriverError`, `append_jsonl`, `dispatch_orchestrator_item`, `load_state`, `print_lane_interrupt_report`, `should_color`, `utc_now` |
| already-one-object | 18 | `Palette`, `Path`, `StreamTracker`, `ToolIdentityError`, `cascade_dependency_blocked`, `contextlib`, `dependency_status`, `dependency_status_detailed`, `emit_shutdown_report`, `queue_sort_key`, `register_signal_report`, `render_run_summary_table`, `report_run_spec_edits`, `runner_shared`, `runner_stop`, `sys`, `time`, `update_execution_order` |
| thin-wrapper | 1 | `save_state` |
| equal-constant | 3 | `EXECUTION_SUCCESS_STATES`, `SUCCESS_STATES`, `TERMINAL_STATES` |
| divergent-constant | 1 | `DEPENDENCY_BLOCK_RECOVERY_HINT` |
| **still-double-defined** | **11** | `_observe_between_turn_stop`, `_record_deliberate_stop`, `disable_lane_prompt`, `driver_actor`, `execute_item`, `reclaim_lanes_on_interrupt`, `reconcile_interrupted`, `render_continuation_hint`, `requeue_interrupted`, `retry_deferred_integrations`, `write_report` |

7 + 18 + 1 + 3 + 1 + 11 = 41.

## Reconciling this table with the plan's Goal table

The plan's table lists the same 41 and the same 11 forks, but partitions the non-forks slightly
differently: it counts 14 as "resolves in `runner_shared` today" and 8 as "already ONE object", where
this scanner reports 7 and 18. The difference is a classification convention, not a disagreement
about any symbol: the plan folded `Path`/`sys`/`time`/`contextlib` and several `render_stream`
imports into its 14, while this scanner puts every name reached through an import of a THIRD module
into `already-one-object` and reserves `resolves-in-runner-shared` for names imported specifically
from `runner_shared`. The plan's own arithmetic note ("14 + 3 + 1 + 8 + 11 = 37, plus
`Path`/`sys`/`time`/`contextlib` already counted in the 14") acknowledges the overlap. Every symbol
lands in a class with the same CONSEQUENCE under both conventions.

Two refinements this scanner adds:

* `save_state` is reported as `thin-wrapper` rather than as a fork. Both hosts define it, but each
  body is a single delegating `runner_shared.save_state(...)` call, which is the sanctioned form the
  maintainer's `818uru` OQ-02 ruling established. Counting it as duplication would OVERSTATE the
  work, which is the same category error as measuring body difference and inferring liftability with
  the sign reversed. This is sibling `yrqyxb`'s contribution, adopted here.
* `disable_lane_prompt`'s permanent status is CONFIRMED, not assumed:
  `tests/test_runner_shared.py:1319` (`UnmovableSymbolTests`) pins it in both runners, asserts
  `runner_shared` does not define it, and asserts the REASON (a `global` write to
  `_LANE_PROMPT_DISABLED` that each host's diverged `_lane_reclaim_prompt` reads separately).
  `run_queue` calls it at `oc_runipd.py:8926`, so a shared core must take it as a parameter forever.


---

# Appendix B: E-04, the split analysis

## What is already decided, stated first

OQ-03 is `resolved`. The maintainer's 2026-09-16 directive:

> at the end of the SET, there should be one code base shared by the two runners that contains 100%
> of the otherwise redundant code that currently is duplicated between the two runners

So route (A), do the split, with the two obstacles ruled to be work rather than blockers, and route
(B)'s ordering permitted as a TACTIC. This item is therefore not a request for a decision already
made. It is the measurement the chosen route needs, plus an honest statement of why the split is not
performed by THIS plan.

## (a) The dependencies a shared core would take, and who lifts them

Eleven, from Appendix A. With owner and verdict:

| Symbol | oc / agy len | Owning sibling | Does that sibling lift it? |
|---|---|---|---|
| `render_continuation_hint` | 48 / 41 | `tx6q0h` (04) E-02 | **YES**, named explicitly among its five host-string-only symbols |
| `write_report` | 71 / 63 | `tx6q0h` (04) E-04 | **YES**, and it repairs a live defect on the way (agy backticks the verify cell; `run_viewer.py:1008` does not strip backticks and `:1370` compares to the bare string, so no agy run has ever rendered the `[verified]` badge) |
| `driver_actor` | 25 / 10 | `tx6q0h` (04) E-05 | **NO, DELIBERATELY.** A host CAPABILITY difference: oc reads `options.variant`/`options.launch_profile` from a profile subsystem where `runner_profiles`, `resolve_launch_profile` and `launch_profile` all grep to ZERO in `agy_runipd.py`, so lifting ships permanently dead branches |
| `disable_lane_prompt` | 4 / 4 | pinned by `UnmovableSymbolTests` | **NEVER.** Injection is permanent, not transitional |
| `execute_item` | 1672 / 1438 | `yrqyxb` (07), EXECUTED | **NO.** That plan measured and guarded; its own analysis recommends extracting cohesive blocks first, and nine of ITS eleven dependencies also survive the Set |
| `_observe_between_turn_stop` | 40 / 29 | none | **NO**, but closure-clean today |
| `_record_deliberate_stop` | 21 / 19 | none | **NO**, but closure-clean today |
| `requeue_interrupted` | 43 / 34 | none | **NO**, but closure-clean today |
| `reconcile_interrupted` | 82 / 79 | none | **NO**, but closure-clean today, and only 2 differing code lines |
| `reclaim_lanes_on_interrupt` | 146 / 146 | none | **NO.** 2 differing code lines, but closes over `disable_lane_prompt` AND `_lane_reclaim_prompt`, so it is blocked by the same unmovable global |
| `retry_deferred_integrations` | 146 / 127 | none | **NO.** 36 differing code lines and it closes over the oc-only `process_backlog_close` (sibling `i3d6ml`'s F-12 names this) |

## (b) How many injections remain after the whole Set executes

**Nine of eleven.** Two clear through `tx6q0h`. One is refused on measured grounds. One can never
move. Seven are unclaimed, and `execute_item` is unclaimed in practice because its own plan executed
without splitting it.

**Is nine acceptable?** No, and the reasoning is mechanical rather than aesthetic:

1. The maintainer's `818uru` OQ-02 ruling sanctions a shared core plus a thin per-host wrapper, and
   that form is correct HERE too. But its virtue is that the wrapper binds a dependency once at the
   original name and signature so no call site changes. That virtue does not address the real cost:
   a nine-parameter core makes the shared body's control flow depend on nine host-supplied callables
   **each of which is itself still duplicated logic**. De-duplicating the CALLER while its callees
   stay forked MOVES the duplication rather than removing it, and the Set's own definition of done is
   100 percent de-duplication.
2. Two of the nine are refused on evidence (`driver_actor`'s dead branches, `disable_lane_prompt`'s
   shared global). So the honest end state for `run_queue` is a shared core plus a hook carrying at
   least those two. That is fine, but it should be the STATED target rather than a discovery.
3. Ten source-reading pins would need re-basing in the same change (see (c)). Re-basing is legitimate
   work under the maintainer's ruling and E-02 demonstrates the technique on the load-bearing ones,
   but doing all of it in the same commit that injects nine dependencies into the dispatch loop both
   runners are built around means one change that relocates the control plane and simultaneously
   rewrites the guards that would catch a mistake in it. Either half alone is fine.

## (c) The pins

**10 source-reading pin sites across 9 files** (measured; the plan's F-10 says six). Verdict legend:
**BREAKS** = the assertion reads text a thin caller would no longer contain. **SURVIVES** = it would
still hold.

| # | Pin | Kind | Asserts | Verdict |
|---|---|---|---|---|
| 1 | `test_runner_backlog_close.py:1228` | getsource, BOTH hosts | `"emit_shutdown_report()"` and `"register_signal_report("` present | BREAKS |
| 2 | `test_oc_runipd_cli.py:233` | getsource | `"tracker = StreamTracker()"`, the exact `execute_item(run_dir, state, runnable, recovery=recovery, tracker=tracker)`, `"render_run_summary_table("`, `"tracker=tracker"` | BREAKS |
| 3 | `test_agy_runipd_cli.py:1569` | getsource | the same four substrings | BREAKS |
| 4 | **`test_lane_tool_identity.py:733`** | getsource | **ORDERING**: `except ToolIdentityError` before `except DriverError` | BREAKS |
| 5 | **`test_runner_stop.py:607`** | split-def | **ORDERING**: the between-item poll is inside the loop and precedes item selection | BREAKS |
| 6 | `test_runner_shared.py:3677` | getsource, BOTH hosts | `'"integration-deferred"'` present | BREAKS |
| 7 | `test_runner_shared.py:3713` | getsource, BOTH hosts | `retry_deferred_integrations`, `deferred_integration_items`, `runnable is None`, `poll=True` present | BREAKS |
| 8 | **`test_orchestrator_retirement.py:3575`** | AST by name, agy only | an `If` whose test mentions `orchestrate`, containing a `Continue`, calling `dispatch_orchestrator_item` | BREAKS |
| 9 | `test_oc_runipd_shim.py:40` | split-def | `"def run_queue"` is **ABSENT** from the shim | **SURVIVES** (negative, and gets stronger) |
| 10 | `test_agy_runipd_shim.py:37` | split-def | the same negative assertion | **SURVIVES** |

**Verdict summary: 8 BREAK, 2 SURVIVE.** Three assert ORDERING (#4, #5, #8), which is the class whose
GUARANTEE must survive a move rather than merely its text.

### The three ordering pins and their behavioral equivalents

Each is **already implemented and passing** in
`tests/test_rununify_run_queue_characterization.py`, so this is a demonstrated route rather than a
proposal.

| Ordering pin | Guarantee | Behavioral equivalent (implemented in E-02) |
|---|---|---|
| `test_lane_tool_identity.py:733` | a wrong control plane cannot keep running items | `ToolIdentityIsRunFatalNotItemLocal::test_the_dedicated_clause_is_reached_rather_than_the_item_local_one`, plus `test_a_plain_driver_error_is_item_local` as the non-vacuity control. **HONEST LIMIT: only the half that HOLDS is asserted, because the run-fatal abort is BROKEN today (backlog `mo3h5b`); the broken half is pinned separately as a documented defect.** |
| `test_runner_stop.py:607` | a stop requested between turns prevents the NEXT dispatch rather than arriving too late | `TheBetweenItemStopCheckpointPrecedesSelection::test_a_stop_request_between_turns_prevents_the_next_dispatch` (a level-2 wind-down leaves the other set's item `queued` and undispatched, which is spec R22's no-fabricated-disposition rule as behavior) |
| `test_orchestrator_retirement.py:3575` | an orchestrator spends NO agent turn | `AnOrchestratorSpendsNoAgentTurn::test_an_orchestrate_item_never_reaches_execute_item`, plus `test_the_dispatcher_receives_both_state_sets_from_its_host` (which also pins that `TERMINAL_STATES` and `EXECUTION_SUCCESS_STATES` are not swapped, a mistake that would compile and change which children count as done) |

The non-ordering pins have equivalents too: #2/#3's tracker wiring becomes
`TheStreamTrackerIsWiredThroughToTheTurn` (an instance reaches the turn, and the SAME instance is
reused across items, which the substring cannot express); #6/#7's ladder reachability becomes
`TheIntegrationLadderIsReachedFromTheLoop`; #1's `register_signal_report` presence becomes
`TheSignalReporterSeesPostReloadState`, which asserts the PROPERTY the calls exist to produce.

**The caveat, stated plainly.** A call-graph or behavior-level ordering assertion is weaker than a
source-offset one in one specific way: it can be satisfied by a call on an unrelated branch. It is
stronger in the way this Set needs: it survives the relocation the split performs. That trade is
deliberate.

## (d) Recommendation on route

**Route (B) as a TACTIC for reaching route (A)'s objective**: shrink the closure first, and let the
split fall out. In dependency order:

1. Let `tx6q0h` (04) land. It removes two of the eleven and repairs a live `run_viewer` defect.
2. **Lift the four closure-clean unclaimed forks as individual acts**, each with its own behavioral
   pin: `reconcile_interrupted` (69/69, TWO differing lines), `_record_deliberate_stop`,
   `requeue_interrupted`, `_observe_between_turn_stop`. None needs `run_queue` to move. This is the
   cheapest real progress available to this Set and no plan currently claims it (backlog `5jsjnr`).
3. Then `retry_deferred_integrations`, once `process_backlog_close` is shared, and
   `reclaim_lanes_on_interrupt`, once the `_LANE_PROMPT_DISABLED` global is resolved (backlog
   `8hx3g3`). Both are blocked on a NAMED prerequisite rather than on judgment.
4. Decide EXPLICITLY that `driver_actor` and `disable_lane_prompt` are permanent host hooks, so
   "100% de-duplication" for this function has a stated, reachable definition.
5. Only then extract the loop, whose remaining injections would be two rather than nine, converting
   the eight breaking pins as E-02 demonstrates.

After step 2 the fork count is five, not eleven, and each step is small, independently verifiable and
independently revertible. The alternative (inject nine now) reaches a shared core whose body is a
nine-parameter shell over still-forked callees and pays the entire pin-rebasing cost in one commit.

## Spec consequence

Checked as the plan's spec-sync section requires, and the check was made rather than assumed. E-03's
repair changes what an operator SEES after a signal on agy, so the two specs the plan names were read:

* `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) governs run/verify
  determinism and V-evidence. It says nothing about the shutdown report's contents.
* `c4gd2h` (`20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md`) governs graceful quit.
  Its acceptance criteria constrain the SIGINT ladder, the interrupt menu's path predicate, exit codes,
  descendant reaping and lock cleanup (R12, A1, A2, A8, A10). None constrains which item statuses the
  report renders. A grep for "shutdown report" across `.aw/records/specs/` returns no file.

So the repair brings agy into conformance with an invariant that is stated in `oc_runipd`'s own
comments rather than in a spec, and it moves agy TOWARD oc rather than away from any written contract.
**No spec was amended, because no spec sentence describes the divergence removed.**

Worth naming as a gap rather than leaving implicit: the "the shutdown report must not run off a stale
snapshot" invariant is load-bearing enough that agy diverged from it silently for as long as the
ladder has existed, and it lives only in a code comment. A future plan may reasonably decide it
belongs in `c4gd2h`.

A future plan that REPLACES an existing ordering pin (rather than adding a parallel behavioral one, as
E-02 does) must carry the spec amendment in the same change and declare the spec path in
`Scope-Paths`.

## What was NOT done, said plainly

**No split was performed.** `run_queue` still has two definitions, one per host, and there is no
shared core. `tests/test_rununify_run_queue.py::TheSplitHasNotBeenPerformed` asserts that state
MECHANICALLY, including the inverse assertion that the eleven are still double-defined and that
`disable_lane_prompt` is still defined in both runners, so the omission is a recorded, guarded state
rather than an oversight a later reader might "finish" without reading this analysis.

OQ-03 is resolved and its answer is "do the split". What remains is a sequencing judgment, and this
analysis makes it: the split is the right destination and this position is the wrong place to jump to
it in one act.


---

# Appendix C: reproducing the measurements

Both scanners were run from the repository root and their output is quoted above verbatim.

    python3 closure_scan.py   # E-01: the 41-name classification into six classes
    python3 pin_scan.py       # E-04(c): every test that reads run_queue's source text

`closure_scan.py` implements the closure test with full scope tracking and classifies each free
module-level name against `runner_shared` and against the other host, separating a genuine fork from
the sanctioned thin-wrapper form by checking whether the body is a single delegating
`runner_shared.X(...)` call. `pin_scan.py` finds the three ways a test reaches this function's source
(`inspect.getsource`, an AST lookup by function name, and `split("def run_queue")`), reports the
enclosing test name for each, and also lists every test file that merely NAMES `run_queue` (16 files,
9 of which read its source) so nothing is missed silently.

Both live under this run's lane submission at
`.aw/state/lane-submissions/<run>/09-ty3cj6/attempt-1/evidence/`. That tree is GITIGNORED, which is
why every number they produce is quoted in full above rather than only cited: the tables here are the
durable record. The E-01 classification is additionally asserted MECHANICALLY in
`tests/test_rununify_run_queue.py`, so it is re-derived by the suite on every run and cannot go stale
unnoticed.
