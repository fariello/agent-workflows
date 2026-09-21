# IPD: Give the adjudicating agent a parallel pre-work suite baseline pinned to its own base commit

- Date: 2026-09-08
- Kind: child
- Concern: THE AGENT IS ASKED A QUESTION IT CANNOT ANSWER ACCURATELY EVEN WHEN PERFECTLY HONEST. Sibling `daexj1` (`integearn` Order 3) stops the runner silently refusing integration over a red suite and instead ASKS the executing agent to adjudicate, with `SAFE TO IGNORE.` meaning the failure is pre-existing noise. But to know a failure is PRE-EXISTING the agent must know the test was already failing before it started, and nothing tells it. MEASURED: `run_suite_check` is called exactly ONCE per attempt, AFTER the work, at `oc_runipd.py:6670` and `agy_runipd.py:3724`, and no prior result is persisted anywhere (`suite_check` appears only at those two write sites plus the re-export at `agy_runipd.py:320`). So a well-meaning agent that broke something subtly, and genuinely believes the failure is unrelated, answers `SAFE TO IGNORE.` in good faith and is WRONG.
  THIS IS INFORMATION, NOT A GATE, AND THE DISTINCTION IS THE WHOLE DESIGN. The maintainer ruled 2026-09-08 (recorded on `daexj1` OQ-02) that no programmatic check may refuse a verdict on the strength of a baseline: "You cannot build a pre-test that detects deception ... We're mitigating sloppiness, not malice. Asking the agent is 100% the right move." The same ruling rejected the originally-proposed constraint ("refuse `SAFE TO IGNORE.` for any id absent from the baseline") explicitly. The baseline exists so an HONEST agent can be RIGHT, not so a dishonest one can be caught.
  A NAIVE IMPLEMENTATION WAS MEASURABLY WRONG, AND AT REVIEW THAT IS NO LONGER OBSERVABLE (corrected 2026-09-08, F-12). The plan's original argument: the suite behaves DIFFERENTLY in a linked worktree, since `run_suite_check`'s docstring (`oc_runipd.py:3637-3653`) records `tests/test_run_viewer.py` at `36 passed` in the primary checkout against `15 failed, 20 passed` in a lane, because a linked worktree resolves `.aw/state` relative to cwd (backlog `dh0uno`). RE-MEASURED AT REVIEW at HEAD `c170204d`, in a real linked worktree holding ZERO run directories: that file gives `75 passed`, IDENTICAL to the primary checkout, and the FULL bare suite gives `5920 passed, 3 skipped, 2 xfailed` in the worktree against `1 failed, 5919 passed` in the primary checkout, where the single failure is environmental and primary-only. So the divergence has been fixed in the interim (sibling `utwr6y` owns that ground) and now runs the OTHER WAY, by one environmental test. This does not remove the plan's value, but it does mean E-01's likely correct outcome is "no neutralization needed", and that building a subtraction layer from the docstring's fifteen ids would MASK fifteen real failures rather than remove fifteen phantom ones.
  AND THE WALL-CLOCK OBJECTION IS ANSWERABLE, WHICH IS WHY IT IS WORTH BUILDING AT ALL. The suite is ~81 seconds (measured at authoring: `5859 passed, 3 skipped, 2 xfailed in 80.96s`) while an execute turn is minutes to hours. Run concurrently with the turn and collected at its end, the added wall-clock is essentially ZERO. The maintainer asked for exactly this and it is the condition on which the baseline was accepted, given their standing objection that rigid gates in this repository "keep biting us in time and money".
- Scope: Produce a pre-work suite baseline for each execute item, computed CONCURRENTLY with the agent turn in its OWN checkout pinned to that item's base commit and provably NOT the agent's lane, establish that the two results are comparable (re-measuring the divergence first, and building no neutralization layer if none is observable), and hand the result to the adjudication prompt as CONTEXT. CONSUMES `daexj1` E-01's failing-id capture rather than re-deriving ids; this plan cannot produce a failing-id set on its own. EXCLUDES any refusal, gate, or automatic action keyed on the baseline (the maintainer's ruling forbids it); excludes the adjudication prompt and its verdict handling (`daexj1` owns them); excludes capture-time id extraction (`daexj1` E-01 owns it, and `run_evidence.py` is deliberately NOT in Scope-Paths); excludes changing `run_suite_check`'s primary-checkout contract.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_suite_baseline.py
- Item-Dependencies: executed:daexj1
- Status: executed
- Readiness: go-pending-approval
- Set: integearn
- Order: 5
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Blocks-Release: next
- Id: 9lyg5h

## Workflow history
- 2026-09-21 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: 9lyg5h verified (set integearn, attempt 1). [Scope reconciliation - out-of-scope tests/test_gate_answer_wiring.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_orchestrator_probe_cache.py: changed by the plan's approved execution (auto-reconciled by aw oc run)]
- 2026-09-21 executed (opencode its_direct/pt3-claude-opus-5-1m-us): E-01..E-07 all `performed`, V-01..V-07 all `pass` with pasted evidence; `aw ipd lint --phase pre-transition` reports `outcome: clean, exit 0` (one `info` advisory, `check.ipd-uncarried-obligation`, now answered by a new 'Durable carriers' subsection); `aw sanitize --agent` clean. THE HARD PREREQUISITE HELD: `daexj1` is `- Status: executed` and the failing-id capability it owns SHIPPED (re-sited by `h5pyqa`/`gatewire-01` as `oc_runipd.extract_suite_failures` with the typed list at `attempt["suite_check"]["failures"]`), so this plan CONSUMED that field and wrote no second extractor; `run_evidence.py` is unmodified, exactly as `Scope-Paths` demanded.
  E-01 INVERTED AS REVIEW PREDICTED, AND MORE SO: the worktree divergence is ZERO, not merely smaller. Measured at `24aa8d41` in a real `--detach` linked worktree of a fresh clone, `tests/test_run_viewer.py` gives `91 passed` in BOTH checkouts and the full bare suite gives `1 failed, 7830 passed, 3 skipped, 2 xfailed` in BOTH, the SAME single id in each - so it does not even run in review's opposite direction, because that failure's cause is the HOST environment rather than the checkout. NO neutralization layer and NO subtraction list was built; the comparability premise is now MONITORED by a regression test instead.
  THE WORK-DESTROYING HAZARD (F-14) WAS AVOIDED BY ROUTE (b), a plain DETACHED worktree under the gitignored `.aw/state/suite-baselines/`, outside the lane namespace entirely - not a non-colliding lane id, because route (b) removes the hazard by CONSTRUCTION: no branch means `teardown_worktree`'s branch-and-reflog delete has nothing to destroy. Proven ADVERSARIALLY, not by reasoning: with the agent's lane present and EMPTY, the baseline's allocation and cleanup leave its worktree, branch and reflog byte-identical (`REFLOG IDENTICAL? True`, `worktree list IDENTICAL? True`); with the lane HOLDING A COMMIT, no `_attempt2` branch appears, the owner-record set is unchanged (`['abc123.json']` before and after), and the commit stays reachable.
  F-16 REQUIRED NEW STRUCTURE, as the plan said: `execute_item_core` had ZERO `finally:` blocks, so its whole post-dispatch remainder was wrapped in a `try:`/`finally:` covering all FOUR turn-ending paths (`StopNowForce`, `StopAtCheckpoint`, `StallTimeout`, `KeyboardInterrupt`) plus the two `raise DriverError` session-drift paths and every ordinary `return`; enclosure is asserted by AST. F-15 was honored by reading `attempt["worktree_base"]` (written at allocation) and NOT `item["preserved_base"]` (written only after the turn), with a test that fails if the latter appears. F-17 was honored with a new concurrent path (`Popen` + a daemon drain thread) because `run_suite_check` blocks inside `subprocess.run` with no start/poll/collect split.
  THE LOAD-BEARING NOT-A-GATE PROPERTY IS ASSERTED, not intended: a `not-mine` verdict produces an IDENTICAL outcome whether the failing id is in the baseline, absent from it, or the baseline is missing entirely, and an exhaustive record diff shows the ONLY differing key is the audit field `suite_baseline`. An AST test forbids the name `baseline` appearing anywhere in `perform_gate_answer` outside the question and record calls, so a future gate cannot be added silently. The maintainer's ruling and its four reasons are recorded AT the code and asserted present phrase by phrase.
  OQ-02 RESOLVED BY MEASUREMENT: zero-wait collection (option three), because 10.4 ms of added wall-clock against a 104-199s suite makes the no-delay property STRUCTURAL rather than tuned. SPEC-SYNC CHECKED AGAINST LANDED TEXT and the conclusion strengthened: `daexj1` E-10's amendment in spec `0718` explicitly states "a pre-work baseline may be supplied to the agent as INFORMATION so it can answer more accurately, but nothing refuses on it", so this plan implements the spec's own stated remedy and needs no amendment; no `.spec.md` was modified.
  SUITE: BEFORE `1 failed, 7830 passed, 3 skipped, 2 xfailed`; AFTER `1 failed, 7882 passed, 3 skipped, 2 xfailed`. Failure-set delta AFTER-BEFORE is EMPTY; +52 passed is exactly the new module. TWO DEFECTS FILED rather than absorbed: `wx72g3` (bug, `Blocks-Release: next`) for the one surviving failure, a `test_turn_bounds` assertion that an env var is absent from an INHERITED environment, which is red for every agent running the suite inside an agent host; and `nbu56f` (chore) for `run_suite_check`'s stale divergence docstring. THREE DEFECTS FILED in total: the third, `8mkt5l` (bug, `Blocks-Release: next`), is a GENUINE PRODUCTION defect I traced rather than dismissing as a flake - `artifact_audit`'s index cache invalidates on directory MTIME, so a second artifact created inside one mtime tick is invisible and the cache returns a STALE index, reproduced deterministically. TWO OUT-OF-SCOPE-PATH EDITS DECLARED, both on tests whose LOCATORS my structural change broke while their asserted properties stayed intact: `tests/test_orchestrator_probe_cache.py`'s frozen oc->agy import count 53 -> 56 (re-measured with computed attribution, per that test's own documented instruction), and `tests/test_gate_answer_wiring.py`'s exact-substring arm locators, made formatting-insensitive after `ruff-format` legitimately re-wrapped a condition my added indentation pushed past the line limit.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-09 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-501..PR-509 all FIXED in place; review record written; aw ipd lint --phase review-finalize conforms.
- 2026-09-08 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-501..PR-509, ALL NINE FIXED in place. Round 1, reviewed at HEAD `c170204d`. Record: `.aw/records/reviews/20260908-integearn-05-9lyg5h-give-the-adjudicating-agent-a-parallel-pre-work-suite-baseli.review.md`. `aw ipd lint` conformed at `--phase author` before semantic review and at `--phase review-finalize` after every edit. THE CORE PREMISE HOLDS, re-verified: the post-work suite runs exactly ONCE, after the work, on both hosts, and no prior result is persisted, so an honest agent genuinely cannot tell whether a failure pre-existed its work. THREE BLOCKERS, each found by EXECUTING a plan instruction rather than reading it, and two of them pull in opposite directions. PR-503 makes the plan MORE DANGEROUS than it understood: following E-02 literally (allocate via `worktree_lease.allocate_worktree` with the item's id6, then tear down unconditionally) was run end to end and ADOPTS the agent's own lane AT THE SAME PATH, then deletes its branch, empties its reflog and leaves its commits reachable from no ref; the documented liveness gate does not stop it because the driver writes no owner record before that point and same-PID counts as allowed self-reallocation, and the other timing merely attempt-scopes an `_attempt2` lane and writes an owner record under a bogus identity. So a checkout the plan calls read-only and harmless had unrecoverable data loss on its default path. PR-501 makes the plan SMALLER: the worktree divergence it calls 'the highest risk in the plan and the reason it exists separately' was re-measured in a real linked worktree and is GONE (`75 passed` in both checkouts; full bare suite `5920 passed, 3 skipped, 2 xfailed` in the worktree against `1 failed, 5919 passed` primary, that one failure being environmental and primary-only), so E-01's honest output is now a measurement plus a regression test, and building the offered subtraction list from the stale fifteen ids would MASK fifteen real failures. PR-506: the failing-id set this plan exists to hand over DOES NOT EXIST in the code, because `SuiteCheckResult` has no such field and the raw output is hashed away at capture, so `Item-Dependencies: executed:daexj1` is a hard functional prerequisite and `run_evidence.py` is deliberately kept OUT of Scope-Paths. Also PR-504 (the base commit E-02 names is written only AFTER the turn), PR-505 (`execute_item` has no `finally`, so cleanup on 'every path' needs added structure for four exits), PR-507 (`run_suite_check` blocks, so it cannot be reused concurrently), PR-502 (sibling `utwr6y` owns the divergence and had already re-measured it), PR-508 (every anchor stale within a day; suite baseline stale) and PR-509 (the spec question was answerable at review and is now answered, with the line that would invalidate it stated). OQ-01 RESOLVED from measurement; OQ-02 and OQ-03 remain non-blocking as authored. Four decisions recorded (D-1..D-4), all reversible.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): SPLIT OUT OF `daexj1` ON THE MAINTAINER'S EXPLICIT INSTRUCTION 2026-09-08, after they asked directly whether the decision needed a replan or a breakup. IT DOES, and the measurement that settled it: `daexj1` already carries TEN E-items across EIGHT files and already reads `Readiness: no-go`, so it was at or past a reviewable unit's capacity before this decision existed. What the decision adds is not a detail but a NEW CAPABILITY: a second checkout created and torn down per item, pinned to a commit, running a suite concurrently with an agent turn, plus neutralizing a measured phantom-failure divergence. `daexj1` contains essentially no concurrency today. THE SEAM IS NATURAL, which is why the split is clean rather than arbitrary: `daexj1`'s value stands alone (asking the agent instead of silently refusing is what fixes the eleven-lane stranding, which cost `03ie04` two executions at `$16.59` then `$32.83`), and this plan only makes the agent's ANSWER more accurate. So `daexj1` can and should ship first, and this declares `Item-Dependencies: executed:daexj1`. CHECKED BEFORE SPLITTING, rather than assumed: `daexj1`'s `no-go` was NOT a size verdict. Its review records `Verdict: REVIEWED - OPEN QUESTIONS` with one advisory `IPD-Z602` density note and no structural error, and the blocking question was OQ-02 itself, which the maintainer has now resolved. So `daexj1` does not need re-cutting on this account; it needs its `no-go` re-examined now that its blocker is answered, which is a review action and not this plan's. THE DESIGN WAS CHOSEN BY THE MAINTAINER FROM FOUR OPTIONS: parallel in its own worktree pinned to the item's own base commit, over pinning to current main (rejected: a mid-turn merge by a human or another agent would make the baseline describe a different tree than the item started from, which was the maintainer's own concern), over sequential-before-the-turn (rejected: a flat 81 seconds added to every item), and over reusing one baseline across items sharing a base (rejected: wrong the moment an item merges and moves the base for later items). ONE COST NAMED AND ACCEPTED: a second checkout plus a full suite run means real disk and CPU concurrent with the agent turn; accepted because wall-clock is unaffected.

## Goal

Let an honest agent answer "was this already failing?" correctly, by telling it what was failing before it started, without adding any gate that could wrongly block work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the two measurements comparable before comparing them

- [x] E-01 RE-MEASURE THE WORKTREE DIVERGENCE FIRST, AND EXPECT TO FIND IT ALREADY GONE (PR-501, measured at review 2026-09-08). This item is still first, but its likely outcome has INVERTED: the divergence this plan was largely built to neutralize was measured at review and is ZERO today.
  WHAT REVIEW MEASURED, at HEAD `c170204d`, so the executor does not repeat it blind. In a real linked worktree created with `git worktree add --detach` and holding ZERO run directories (the exact condition the cited defect describes), `python3 -m pytest tests/test_run_viewer.py` reports `75 passed`, identical to the primary checkout's `75 passed` (which has 140 run dirs). The FULL bare suite in that same worktree reports `5920 passed, 3 skipped, 2 xfailed in 54.09s`, i.e. NO failures at all, against `1 failed, 5919 passed` in the primary checkout, where the single failure is an ENVIRONMENTAL one caused by a gitignored local directory that the worktree does not have. So the divergence now runs in the OPPOSITE direction from the one this plan describes, and it is one test, not fifteen.
  THE HISTORICAL NUMBERS ARE STALE, AND SO IS THE DOCSTRING THAT CARRIES THEM. `run_suite_check`'s docstring (`oc_runipd.py:3637-3653`) still records `36 passed` primary against `15 failed, 20 passed` in a lane. That measurement is real but historical: `tests/test_run_viewer.py` has since been changed (see `0d349cc5`, `ff092eae`, `661643bb`) and now passes in both. Do NOT cite the docstring as a current fact, and do NOT build a subtraction list from it: a list of fifteen ids that no longer fail would subtract fifteen REAL failures if they ever appeared, which is strictly worse than no list.
  IF YOUR RE-MEASUREMENT ALSO SHOWS ZERO DIVERGENCE, SAY SO AND BUILD NOTHING FOR IT. Record the measurement, state that no neutralization and no subtraction is required, and add a test that FAILS if a divergence reappears (so the plan's comparability premise is monitored rather than assumed). Do NOT implement a neutralization layer for a divergence you cannot observe: that is dead code guarding a condition that no longer exists, and it would be the second-largest thing in this plan.
  IF IT REAPPEARS, the original guidance applies: prefer NEUTRALIZING the cause (make both runs resolve the same state root) over SUBTRACTING a hand-maintained divergent set, which rots. Either way state explicitly what makes the two results comparable.
  NOTE THE SIBLING THAT OWNS THIS GROUND (PR-502, F-13). `utwr6y` (`testiso-01`, `to-review`) exists precisely to make `tests/test_run_viewer.py` own its data so it passes in a fresh clone, in a lane, and in the primary checkout alike, and it re-measured the same family at `14 failed, 32 passed` on 2026-09-08. Its work appears to have LANDED already (hence the `75 passed` in a lane). Read it before measuring, and if it explains your result, cite it rather than re-deriving the cause.
  - Depends on: none
  - Expected outcome: a re-measurement with today's actual counts from a real linked worktree, an explicit statement of whether ANY divergence remains, and either (a) a recorded finding of zero divergence plus a regression test that fails if one reappears and NO neutralization code, or (b) if one is found, a recorded choice between neutralizing and subtracting with its reasoning. Either way, the stale docstring numbers are not cited as current.
  - Execution state: performed

### Task group 2: produce the baseline without slowing the turn

- [x] E-02 CREATE THE BASELINE WORKTREE PINNED TO THE ITEM'S OWN RECORDED BASE COMMIT, and do NOT allocate it through `worktree_lease.allocate_worktree` KEYED ON THE ITEM'S id6 (PR-503, BLOCKER, measured at review). The plan's original prescription ("reusing the existing allocation helper") destroys the agent's in-flight work, and the mechanism is exact rather than speculative.
  WHAT REVIEW MEASURED, in a throwaway repo, following this item's own two instructions literally (allocate via the helper with the item's recorded base, then tear down unconditionally):
  (1) The driver allocates the agent's lane: `allocate_worktree(repo, "abc123", base_commit="HEAD")` -> branch `aw/lane/abc123`, path `.aw/worktrees/abc123`, disposition `created`.
  (2) The baseline calls the SAME helper for the SAME lane id at the item's recorded base -> it returns disposition `adopted`, `aw/lane/abc123`, and **THE SAME PATH AS THE AGENT'S LANE** (`baseline.path == agent.path` is `True`).
  (3) The agent then commits work in that worktree.
  (4) E-02's mandated unconditional teardown runs on the baseline handle, and the result is: agent worktree GONE from disk, agent branch DELETED, reflog EMPTY, and the agent's commit reachable from NO ref. The work is unrecoverable.
  WHY THE DOCSTRING'S LIVENESS GATE DOES NOT SAVE YOU. `allocate_worktree`'s docstring says an EMPTY lane is adopted only after "a liveness check: a lane a LIVE process owns is never adopted". Measured: `lane_is_safe_to_adopt` returns `(True, 'no owner record; unclaimed')` for the agent's lane, because the driver's own allocation path is the ONLY writer of an owner record and the baseline runs IN THE SAME PROCESS, where `lane_is_safe_to_adopt` deliberately treats the same PID as "self-reallocation, allowed" (`worktree_lease.py:494-497`). The gate is designed to stop a DIFFERENT live process, which is exactly not this case.
  AND THE OTHER BRANCH IS ALSO WRONG, so there is no safe way to key this on the item's id6. If the agent has already committed, the lane classifies `HOLDS-WORK` and the helper ATTEMPT-SCOPES, returning `aw/lane/abc123_attempt2` (measured). That does not destroy anything, but it (a) creates exactly the `_attempt2` lane clutter that `rl67b0` and `pr5b0t` exist to stop, and (b) writes an owner record for a bogus lane identity (`write_lane_owner` at `worktree_lease.py:654` runs on every successful allocation), polluting the durable lane state that `resolve_prior_lane` and the reclamation classifier read. So both outcomes are defects; only the timing decides which.
  USE A LANE IDENTITY THAT CANNOT COLLIDE WITH THE AGENT'S, or do not use the lane machinery at all. Two acceptable routes, and the executor must choose one and say why: (a) allocate under a DISTINCT lane id that is provably not an execution lane (for example a `baseline:<id6>` identity, noting `_lane_dirname` maps `:` to `_`), so adoption and attempt-scoping can never target the agent's lane; or (b) create a plain detached worktree outside the lane namespace entirely (`git worktree add --detach <path> <commit>`), which is what review used and which needs no owner record, no branch, and no lane classification, because a read-only suite run needs none of those. Route (b) is simpler and is probably right: the lane machinery exists to manage WRITE lanes with ownership and recovery semantics, and this checkout writes nothing.
  DO NOT ALLOCATE A BRANCH FOR IT AT ALL under either route. A branch is what makes teardown destructive (`teardown_worktree` deletes the branch and its reflog, `worktree_lease.py:673-702`, which its own docstring calls a DATA-SAFETY HAZARD). A detached checkout has nothing to delete but a directory.
  PIN TO THE COMMIT, NEVER TO A BRANCH. This is the maintainer's own requirement and the reason the design survives concurrent activity: if a human or another agent merges to main mid-turn, a commit-pinned baseline still describes the tree THIS item started from. A branch-pinned baseline would silently describe a different tree.
  BEWARE THE BASE COMMIT YOU READ (PR-504). `item["preserved_base"]` is written only at `oc_runipd.py:6899`, on the PRESERVATION path, which runs AFTER the turn and only when the item did NOT reach `executed`. At dispatch time it is absent for a first attempt. The value that exists when the baseline must start is `wt_handle.base_commit`, recorded onto the attempt at `oc_runipd.py:6209` (`attempt["worktree_base"]`) immediately after allocation. Read that, and state which field you used. For a NON-isolated turn (`--no-isolate-worktree`) there is no handle at all, so say what the baseline does then; declining to produce one is an acceptable answer.
  DO NOT REUSE OR READ THE AGENT'S LANE. The lane is being written by the agent; reading it would sample half-written files.
  TEAR IT DOWN ON EVERY PATH, AND NOTE THERE IS NO `finally` TO HANG THAT ON TODAY (PR-505). Measured: `execute_item` (now unified in `runner_shared.execute_item_core:11340`, previously `oc_runipd.py:6029`) contains ZERO `finally:` blocks, and between the dispatch point and the collection point there are THREE `except ... raise` paths (`StopNowForce`, `StopAtCheckpoint`, `KeyboardInterrupt`) plus a `StallTimeout` handler, each of which leaves the function without reaching the suite check collection point. So "unconditional" requires ADDING a cleanup construct in `execute_item_core`, not merely calling teardown at the end. Say which construct you added and show it covers all four exits.
  - Depends on: E-01
  - Expected outcome: a read-only baseline checkout per execute item, pinned to the base commit recorded on the attempt at allocation time, allocated under an identity that provably cannot adopt or attempt-scope the agent's lane (or outside the lane namespace entirely, with the choice justified), holding no branch, never reading the agent's lane, and removed on all four exit paths through an explicitly added cleanup construct.
  - Execution state: performed

- [x] E-03 RUN THE BASELINE CONCURRENTLY WITH THE AGENT TURN AND COLLECT IT AT TURN END, which is the condition the maintainer accepted this on. Start at dispatch, collect where the post-work `run_suite_check` result is already consumed in `runner_shared.execute_item_core` (previously `oc_runipd.py:6669`, `agy_runipd.py:3724`).
  THE THING THIS PLAN PRODUCES DOES NOT EXIST YET, AND `daexj1` E-01 IS WHAT CREATES IT (PR-506, BLOCKER, measured at review). Every E-item here speaks of "the failing id set", but `run_suite_check` returns a `SuiteCheckResult` (`oc_runipd.py:3614-3628`) whose fields are `passing`, `exit_code`, `summary`, `reason`, `cwd`, `timeout_seconds`, `elapsed_seconds` and NOTHING ELSE: there is no failing-id list anywhere in it, and none is persisted at `attempt["suite_check"]` (`:6670-6677`). Worse, the raw output the ids would come from is DESTROYED at capture: `build_tool_event` hashes stdout and keeps only `stdout_sha256`/`stdout_len` (measured: the returned event's keys contain no `stdout_excerpt`, and `run_suite_check` reads exactly that missing key at `:3671`, so `summary` is ALWAYS `""` in production). `daexj1` E-01 is the item that fixes this, by extracting the failing node ids at capture time and adding them as a typed field. So this plan CANNOT produce a failing-id set on its own, and its `Item-Dependencies: executed:daexj1` is not merely an ordering preference but a HARD functional prerequisite. State that plainly, consume `daexj1`'s field rather than re-deriving ids, and if `daexj1` shipped a different shape than E-04 assumes, report it instead of building a second extractor.
  DO NOT WRITE A SECOND ID EXTRACTOR. `daexj1` E-01 owns capture-time extraction, its E-08 pins it against real (unstubbed) output, and its `Scope-Paths` includes `run_evidence.py`, which this plan does NOT declare. If you find yourself parsing pytest output here, stop: either `daexj1` has not landed (in which case this plan cannot proceed, which is what the dependency edge already says) or you are forking its work.
  IT MUST NEVER DELAY OR FAIL THE TURN. A baseline that has not finished when the turn ends is a MISSING baseline, not a reason to wait indefinitely and not a reason to fail: bound the wait, and on expiry proceed with the baseline absent. Measured at authoring the suite is ~81 seconds against turns of minutes to hours, so expiry should be rare; the bound exists so it cannot become a hang.
  A FAILED BASELINE IS NOT A FAILED ITEM. If the worktree cannot be created, the suite cannot run, or the process dies, record WHY and proceed with no baseline. The agent then answers as it does today, which is the current behavior and therefore not a regression.
  DO NOT INTRODUCE A SECOND CONCURRENCY MODEL. Use whatever the runner already uses for out-of-band work; if it has none, choose the simplest thing that cannot deadlock with the turn, and say what you chose and why. A background suite run that can wedge a driver would be worse than no baseline at all.
  YOU CANNOT REUSE `run_suite_check` FOR THE BASELINE, AND THE REASON IS STRUCTURAL, NOT STYLISTIC (PR-507). It is SYNCHRONOUS by construction: it calls `run_evidence.capture_command`, which calls `subprocess.run(...)` and blocks until the process exits or its timeout fires (`run_evidence.py:459-465`). There is no start/poll/collect split anywhere in it. Whatever you build must therefore be a NEW concurrent invocation path, and that has two consequences the plan should own rather than leave to discovery. FIRST, it must NOT inherit `run_suite_check`'s fail-closed stance (a suite that cannot run is a FAILURE there); a missing baseline is an absence of information, per the Step 0 note. SECOND, if you route the baseline through `capture_command` on a thread to get its evidence record, note that `capture_command` also writes provenance derived from the cwd (`get_git_head`, `get_git_dirty_digest`, `get_worktree_path`), so a baseline record will legitimately carry the BASELINE checkout's head and worktree, not the primary's. That is correct and useful, but it means the record is distinguishable from the post-work one and must not be confused with it in E-06's persistence.
  - Depends on: E-02
  - Expected outcome: the baseline computed concurrently with the turn and collected at its end, with a bounded wait, and both a timeout and a hard failure resolving to a RECORDED ABSENT baseline rather than to any delay or failure of the item; the new concurrent path is stated, shown not to deadlock, and shown NOT to inherit the fail-closed stance.
  - Execution state: performed

### Task group 3: hand it over as context, and prove it is not a gate

- [x] E-04 GIVE THE BASELINE TO THE ADJUDICATION PROMPT AS CONTEXT, in the shape `daexj1` E-05 defines. State plainly to the agent which tests were ALREADY FAILING before its work, and that this is information to help it judge, not an accusation and not a constraint on its answer.
  SAY SO WHEN THE BASELINE IS ABSENT, and never let absence read as "nothing was failing before". That inversion is exactly the defect class `daexj1` E-02 exists to prevent on the other side ("do NOT let a missing or empty list read as success"). An absent baseline must be stated as UNKNOWN.
  DO NOT RESTATE OR RESHAPE `daexj1`'s PROMPT. It owns the three verdict sentinels and the prompt's structure; this item supplies one additional block of context to it. If the prompt's shape makes that awkward, report it rather than editing that plan's design.
  - Depends on: E-03
  - Expected outcome: the adjudication prompt carries the already-failing set as stated context, an absent baseline is stated as UNKNOWN rather than as an empty set, and `daexj1`'s prompt design is unchanged otherwise.
  - Execution state: performed

- [x] E-05 PROVE, IN CODE AND IN TEST, THAT NOTHING REFUSES ON THE BASELINE. This is the maintainer's binding constraint and the single property a future reader is most likely to erode, because a baseline sitting in the run record LOOKS like something to check.
  NO CODE PATH MAY COMPARE THE BASELINE TO THE POST-WORK SET AND CHANGE AN OUTCOME. Not the verdict, not the disposition, not the exit code, not integration. Assert this rather than merely intending it: a test that a `SAFE TO IGNORE.` verdict is honored IDENTICALLY whether the failing test appears in the baseline or not is the load-bearing assertion of this plan.
  WRITE THE RULING NEXT TO THE CODE, with its reasoning, so the next reader does not "improve" it into a gate: a gate cannot detect deception, a capable model can make tests pass, an actually malicious agent would rewrite the gate, and the target is sloppiness rather than malice. Without that sentence the field reads as an unfinished check.
  - Depends on: E-04
  - Expected outcome: no code path keys any outcome on the baseline, asserted by a test showing an identical verdict outcome with and without the failing id present in the baseline, and the maintainer's ruling recorded at the code.
  - Execution state: performed

### Task group 4: persist it and prove the whole path

- [x] E-06 RECORD THE BASELINE ON THE RUN RECORD beside the existing per-attempt suite result (`attempt["suite_check"]`, `oc_runipd.py:6670`, `agy_runipd.py:3725`), so an auditor can later ask whether a `SAFE TO IGNORE.` was well-founded even though nothing enforced it at the time.
  RECORD FOUR FACTS: the base commit it was taken at, the failing id set, whether it completed or was absent, and the reason if absent. The commit matters most: without it a reader cannot tell whether the baseline described the tree the item actually started from.
  WRITE IT ON BOTH HOSTS AT THE SAME SEAM, since a field written by one host only would make an audit's answer depend on which runner executed the plan.
  - Depends on: E-05
  - Expected outcome: the baseline's base commit, failing id set, completion state and absence reason all persisted beside the existing suite result, identically on both hosts.
  - Execution state: performed

- [x] E-07 PROVE THE PATH AND THE CASES THAT MUST NOT HURT ANYTHING, on fixtures. Minimum cases: (a) a baseline completes and its failing set reaches the prompt; (b) the baseline TIMES OUT and the item proceeds with an UNKNOWN baseline, not an empty one; (c) the worktree cannot be created and the item proceeds unaffected; (d) a crashed turn leaves NO stray worktree; (e) the verdict outcome is identical with and without the failing id in the baseline (E-05's assertion); (f) both hosts persist the identical shape; (g) **THE LANE-SAFETY CASE (F-14): with the agent's lane present and empty, the baseline's allocation and cleanup leave that lane's branch, reflog and worktree INTACT, and with the agent's lane holding a commit, no `_attempt2` lane and no bogus owner record are created.** Case (g) is not optional and is the single case whose absence would let a work-destroying implementation pass: review measured the plan's original prescription deleting an agent's committed work outright.
  CASE (b) AND CASE (c) ARE THE REGRESSION GUARDS. This plan's worst failure mode is making the runner more fragile in exchange for better information, so an item must complete exactly as it does today whenever the baseline is unavailable.
  DO NOT RUN THE REAL SUITE IN A TEST. An 81-second suite per case would make this module unusable and would make the tests depend on the repository being green. Stub the suite invocation the way the existing driver tests stub host calls.
  DO NOT CREATE A REAL WORKTREE IN THIS REPOSITORY. Several lanes and live runs exist concurrently and this repository has already lost work to stranded worktrees; use throwaway repos.
  - Depends on: E-06
  - Expected outcome: seven fixture cases passing with timeout and creation-failure shown harmless, the AGENT'S LANE proven intact across the baseline's allocation and cleanup, no stray worktree after a crash, the with-and-without-baseline verdict identity asserted, no real suite run and no real worktree in this repository.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE POST-WORK SUITE RUNS ONCE, AFTER THE WORK, ON BOTH HOSTS: `oc_runipd.py:6669`, `agy_runipd.py:3724`, inside `if integration_gate_relevant and not validate`. Nothing persists a prior result, so there is no before-picture to reuse. This premise was re-verified at review and holds.
- **THERE IS NO FAILING-ID SET TO HAND OVER YET, AND `daexj1` E-01 IS WHAT CREATES IT (F-11).** `SuiteCheckResult` (`oc_runipd.py:3614-3628`) carries only `passing`/`exit_code`/`summary`/`reason`/`cwd`/`timeout_seconds`/`elapsed_seconds`, and `attempt["suite_check"]` (`:6670-6677`) persists a subset of those. The raw output is destroyed at capture (`build_tool_event` keeps only `stdout_sha256`/`stdout_len`), and `run_suite_check` reads a key that is never written (`stdout_excerpt`, `:3671`), so even `summary` is always `""` today. This plan's entire deliverable therefore DEPENDS on `daexj1` E-01 having landed; the dependency edge is functional, not stylistic.
- **THE CITED WORKTREE DIVERGENCE IS GONE, MEASURED AT REVIEW (F-12).** `run_suite_check`'s docstring (`oc_runipd.py:3637-3653`) still records `36 passed` primary against `15 failed, 20 passed` in a lane, but in a real linked worktree with ZERO run dirs the file now gives `75 passed`, identical to the primary checkout, and the FULL bare suite gives `5920 passed, 3 skipped, 2 xfailed` there against `1 failed, 5919 passed` in the primary checkout (the one failure being environmental and primary-only). The docstring is historical, not current. Do not build a neutralization or subtraction layer for a divergence you cannot measure.
- `run_suite_check` DEMANDS THE PRIMARY CHECKOUT AND IS SYNCHRONOUS. Its primary-checkout insistence is documented (and its stated reason is now stale, above) and out of scope either way. Separately it is BLOCKING by construction: `capture_command` calls `subprocess.run` (`run_evidence.py:459-465`) with no start/poll/collect split, so a CONCURRENT baseline cannot reuse it as-is.
- IT ALSO FAILS CLOSED BY DESIGN: a suite that cannot run is a FAILURE, with timeout as exit 124 and any other exception as exit 127, neither special-cased into a pass. The BASELINE must NOT inherit that stance, because a missing baseline is an absence of information rather than a failure of the item.
- **THE LANE MACHINERY IS THE WRONG TOOL HERE, AND USING IT AS THE PLAN ORIGINALLY SAID DESTROYS THE AGENT'S WORK (F-14).** `allocate_worktree(repo, <item id6>, base_commit=<recorded base>)` ADOPTS the agent's own lane when it is still empty (measured: same path, disposition `adopted`), and the documented liveness gate does not stop it because the driver writes no owner record before this point and `lane_is_safe_to_adopt` treats the same PID as allowed self-reallocation (`worktree_lease.py:494-497`). A subsequent unconditional `teardown_worktree` then deletes the agent's branch and reflog, leaving its commits unreferenced (measured). If the agent has already committed, the helper instead ATTEMPT-SCOPES to `_attempt2` and writes an owner record for a bogus lane identity (`:654`), polluting the state `resolve_prior_lane` reads. Use a non-colliding identity or a plain detached worktree.
- `teardown_worktree` IS EXPLICITLY A DATA-SAFETY HAZARD, and says so (`worktree_lease.py:673-702`): it deletes the lane BRANCH and its reflog, and `--force` destroys uncommitted files, with the commits surviving only as unreferenced objects. Its docstring requires callers to CLASSIFY FIRST and tear down only a provably-empty lane. A baseline checkout that holds no branch has nothing for it to destroy, which is the strongest argument for the detached route.
- **THE BASE COMMIT THE PLAN NAMED IS NOT AVAILABLE AT DISPATCH (F-15).** `item["preserved_base"]` is written at `oc_runipd.py:6899` on the PRESERVATION path, which runs after the turn and only when the item did not reach `executed`, so it is absent for a first attempt at the moment a baseline must start. The value that does exist then is `attempt["worktree_base"]`, written at `:6209` right after allocation from `wt_handle.base_commit`. For a non-isolated turn there is no handle at all.
- **`execute_item` HAS NO `finally`, SO "TEAR IT DOWN ON EVERY PATH" REQUIRES NEW STRUCTURE (F-16).** Measured: zero `finally:` blocks in `execute_item` (`oc_runipd.py:6029` onward), and between dispatch and the collection point there are three `except ... raise` paths (`StopNowForce` `:6364`, `StopAtCheckpoint` `:6393`, `KeyboardInterrupt`) plus a `StallTimeout` handler. Unconditional cleanup must be added, not merely called last.
- THE PER-ATTEMPT RESULT SEAM IS ESTABLISHED: `attempt["suite_check"]` written on both hosts (`oc_runipd.py:6670`, `agy_runipd.py:3725`) beside `attempt["disposition"]` and `attempt["verification"]`.
- STRANDED WORKTREES ARE A MEASURED PROBLEM HERE, not a hypothetical: eleven lanes were found only by a hand audit of `git worktree list`, and at review `git branch --list 'aw/lane/*'` still returns 29 branches including four `_attempt2`/`_attempt3` clusters. Unconditional cleanup is not optional, AND adding an `_attempt2` lane per item (which the original E-02 prescription would do) makes this exact problem worse.
- TWO SIBLING PLANS OWN ADJACENT GROUND AND MUST NOT BE FORKED: `rl67b0` (`integpath-04`, `reviewed`/`go-pending-approval`) adds `aw <host> integrate` and stops resume orphaning lanes; `pr5b0t` (`lanestrand-01`) reports stranded lanes in `aw attention`. Both are about not creating and not losing lane clutter, which is a reason to keep this plan's baseline OUT of the lane namespace entirely.
- `utwr6y` (`testiso-01`, `to-review`) OWNS THE RUN-VIEWER TEST ISOLATION that this plan's comparability premise depends on, and re-measured the same family at `14 failed, 32 passed` in a lane on 2026-09-08. Read it before re-deriving the cause of any divergence you find.
- THE MAINTAINER'S STANDING OBJECTION applies to this plan: rigid programmatic gates in this repository "keep biting us in time and money". The baseline was accepted only as INFORMATION and only because it costs no wall-clock.
- Both driver files are under concurrent edit. Re-locate every symbol by NAME: measured at review, anchors in a sibling plan re-measured one day earlier had moved by up to 300 lines, and this plan's own `:6670`/`:6900`/`:3637-3646` citations were each off by one to three lines at review HEAD `c170204d`. The suite runs BARE.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the agent cannot answer honestly-but-correctly | To call a failure pre-existing it must know the prior state; the suite runs once, after the work, and no prior result is persisted. So good-faith misattribution is structurally guaranteed. | `oc_runipd.py:6669`, `agy_runipd.py:3724`; `suite_check` write sites only |
| F-2 | HIGH | a worktree baseline WAS measurably wrong if compared naively; **SUPERSEDED BY F-12, which measured the divergence gone** | The cited divergence (`36 passed` primary versus `15 failed, 20 passed` in a lane, caused by `.aw/state` resolving relative to cwd) is REAL BUT HISTORICAL. Re-measured at review: `75 passed` in both, and a full bare suite CLEANER in the worktree than in the primary checkout. The hazard the plan was built around is not currently observable; E-01 now expects to find and record that. | `run_suite_check` docstring, `oc_runipd.py:3637-3653` (stale); backlog `dh0uno`; superseded by F-12's measurement |
| F-3 | HIGH | the maintainer forbids a gate on this | Ruled 2026-09-08: a gate cannot detect deception, a capable model can make tests pass, a malicious agent would rewrite the gate, and the target is sloppiness. The originally-proposed refusal was rejected explicitly. | `daexj1` OQ-02 resolution |
| F-4 | MEDIUM | wall-clock is answerable, which is why it is buildable | Suite ~81 seconds (`5859 passed, 3 skipped, 2 xfailed in 80.96s`) against turns of minutes to hours, so a concurrent baseline adds essentially nothing. | measured at authoring |
| F-5 | MEDIUM | commit-pinning is required, not tidy | A mid-turn merge by a human or another agent would make a branch-pinned baseline describe a different tree than the item started from. The maintainer raised this case directly. | maintainer, 2026-09-08 |
| F-6 | MEDIUM | the machinery exists but is the WRONG machinery here (see F-14/F-15) | `allocate_worktree` does take and resolve `base_commit`, but keying it on the item's id6 adopts or attempt-scopes the AGENT's lane, and the per-item base the plan names is not written until after the turn. | `worktree_lease.py:550-556`, `:587`; but see F-14 and F-15 |
| F-7 | MEDIUM | `daexj1` was oversized before this decision | Ten E-items across eight files, and `Readiness: no-go`. Adding a concurrent second checkout would have pushed a plan that already failed review. | `daexj1` metadata |
| F-8 | MEDIUM | but its `no-go` was NOT about size | Its review records `Verdict: REVIEWED - OPEN QUESTIONS`, one advisory density note, no structural error, and the blocking question was OQ-02, now resolved. So `daexj1` needs its readiness re-examined, not re-cutting. | `daexj1` review round 1 |
| F-9 | MEDIUM | absence must not read as an empty set | `daexj1` E-02 exists to stop a missing list reading as success on the other side of this same feature; the same inversion here would tell the agent nothing was failing before. | `daexj1` E-02 |
| F-10 | LOW | stranded worktrees are a real cost here | Eleven lanes were found only by a hand audit. Unconditional teardown is mandatory. | the 2026-09-08 recovery |
| F-11 | BLOCKER | **the failing-id set this plan hands over does not exist yet** | `SuiteCheckResult` carries no id list and persists none; the raw output is hashed away at capture and `run_suite_check` reads a key never written (`stdout_excerpt`), so even `summary` is always `""`. `daexj1` E-01 is what creates the capability. The dependency edge is FUNCTIONAL, not an ordering preference. | `oc_runipd.py:3614-3628`, `:3671`, `:6670-6677`; measured `build_tool_event` keys contain no `stdout_excerpt`; `daexj1` E-01 |
| F-12 | BLOCKER | **the cited worktree divergence is GONE, so the plan's second-largest task guards a condition that no longer exists** | Measured at review in a real linked worktree with zero run dirs: `tests/test_run_viewer.py` gives `75 passed`, identical to the primary checkout; the FULL bare suite gives `5920 passed, 3 skipped, 2 xfailed` there against `1 failed, 5919 passed` primary, the one failure being environmental and primary-only. The docstring's `36` vs `15 failed, 20 passed` is historical. A subtraction list built from it would mask fifteen real failures. | `oc_runipd.py:3637-3653` (the stale docstring); measured worktree and primary runs at HEAD `c170204d` |
| F-13 | MEDIUM | a sibling plan owns the divergence and already re-measured it | `utwr6y` (`testiso-01`, `to-review`) exists to make `tests/test_run_viewer.py` own its data so it passes in a fresh clone, a lane, and the primary checkout alike, and measured `14 failed, 32 passed` in a lane on 2026-09-08. Its work appears already landed, which explains the `75 passed`. | `utwr6y` Concern and Scope |
| F-14 | BLOCKER | **E-02's prescription DESTROYS the agent's in-flight work** | Measured end to end: allocating the baseline via `allocate_worktree` with the item's id6 returns disposition `adopted` at THE SAME PATH as the agent's lane, and the mandated unconditional teardown then deletes the agent's branch and reflog, leaving its commit reachable from no ref. The documented liveness gate does not stop it (no owner record is written by the driver before this point, and same-PID is allowed self-reallocation). If the agent has already committed, the helper instead attempt-scopes to `_attempt2` and writes an owner record under a bogus lane identity. | measured allocate+teardown sequence; `worktree_lease.py:494-497` (self-reallocation allowed), `:600-633` (adopt/attempt-scope branches), `:654` (owner write), `:673-702` (teardown is a stated data-safety hazard) |
| F-15 | HIGH | the base commit the plan names is not available when the baseline must start | `item["preserved_base"]` is written on the POST-turn preservation path and only when the item did not reach `executed`, so it is absent at dispatch for a first attempt. The available value is `attempt["worktree_base"]`, written right after allocation. A non-isolated turn has no handle at all, a case the plan never addresses. | `oc_runipd.py:6899` (preservation write), `:6209` (`attempt["worktree_base"]`), `:6106` (`isolate` may be False) |
| F-16 | HIGH | "tear it down on every path" is not buildable as a trailing call | `execute_item` contains ZERO `finally:` blocks, and three `except ... raise` paths plus a `StallTimeout` handler leave the function between dispatch and the collection point. Unconditional cleanup requires ADDING structure. | measured zero `finally` in `execute_item` (`oc_runipd.py:6029` onward); `:6364`, `:6393` |
| F-17 | MEDIUM | `run_suite_check` cannot be reused for a concurrent baseline | It is synchronous by construction: `capture_command` calls `subprocess.run` and blocks, with no start/poll/collect split. A new concurrent path is required, and it must not inherit the fail-closed stance. | `run_evidence.py:459-465`; `oc_runipd.py:3631` |

## Proposed changes (ordered, validatable)

1. Re-measure the worktree divergence, expect to find it GONE, and build a neutralization layer only if one is actually observable (E-01, F-12).
2. Create a read-only baseline checkout pinned to the item's base commit under an identity that cannot adopt or attempt-scope the agent's lane, holding no branch, cleaned up through an added construct that covers all four exit paths (E-02, F-14/F-15/F-16).
3. Run it concurrently with the turn through a NEW non-blocking path (not `run_suite_check`, which blocks), bounded, with timeout and failure both harmless (E-03, F-17).
4. Hand the failing set to the adjudication prompt as context, absence stated as UNKNOWN (E-04).
5. Prove nothing refuses on it, and record the ruling at the code (E-05).
6. Persist the base commit, the id set, and the completion state on both hosts (E-06).
7. Prove six cases including the two regression guards, without a real suite run or a real worktree (E-07).

## Deferred / out of scope (with reason)

- ANY GATE, REFUSAL, OR AUTOMATIC ACTION KEYED ON THE BASELINE. Forbidden by the maintainer's 2026-09-08 ruling, which rejected the originally-proposed "refuse `SAFE TO IGNORE.` for any id absent from the baseline" in as many words. E-05 exists to prove the absence of such a path.
- THE ADJUDICATION PROMPT, ITS THREE VERDICT SENTINELS, AND THE VERDICT HANDLING. `daexj1` owns all of it; this plan supplies one context block to it.
- CHANGING `run_suite_check`'s PRIMARY-CHECKOUT CONTRACT. It is deliberate and documented, and altering it would change the post-work check's meaning as well. E-01 must make the two comparable WITHOUT relaxing that contract. NOTE its docstring's stated REASON is now stale (F-12) and its `stdout_excerpt` read is a live shipped bug (F-11); neither is this plan's to fix. `daexj1` E-01 owns the excerpt bug explicitly, and correcting the stale docstring is a one-line courtesy at most, not a task here.
- CAPTURE-TIME EXTRACTION OF THE FAILING TEST IDS (F-11). `daexj1` E-01 owns it and declares `run_evidence.py`, which this plan deliberately does not. This plan CONSUMES that field. If it has not landed, this plan cannot run, which is exactly what `Item-Dependencies: executed:daexj1` says.
- FIXING THE STRANDED LANES OR THE `_attempt2` CLUTTER THAT ALREADY EXISTS. 29 `aw/lane/*` branches with four attempt-scoped clusters exist at review; `rl67b0` owns the recovery verb and `pr5b0t` owns the reporting. This plan's obligation is narrower and absolute: do not ADD to that clutter, which is why E-02 must stay out of the lane namespace.
- THE POST-MERGE REVALIDATION RUN. `daexj1` E-03/E-04 own it. This plan adds a THIRD suite run in wall-clock terms only, since it is concurrent.
- REUSING ONE BASELINE ACROSS ITEMS SHARING A BASE COMMIT. Rejected by the maintainer: it is wrong the moment an item merges and moves the base for later items. If a future measurement shows the cost matters, it can be revisited with that hazard stated.
- MAKING THE BASELINE AVAILABLE TO ANY OTHER CONSUMER. It is produced for the adjudication prompt. A second consumer would make it load-bearing, which is a step toward the gate the ruling forbids.
- FIXING THE `.aw/state` cwd-RESOLUTION DEFECT ITSELF (backlog `dh0uno`). It is the CAUSE of F-2 and fixing it would make this plan simpler, but it is a separate item with its own blast radius across every worktree consumer. **RESOLVED SINCE AUTHORING, so nothing is outstanding here:** `dh0uno` is `- Status: done` (fixed in `6771e590`) and its OWN history retracts the acceptance claim ("NOTE the old acceptance claim that ~15 test_run_viewer failures ARE this bug was false"). E-01's re-measurement confirms it: zero divergence.

### Durable carriers for the obligations this section defers (added at execution)

WHY THIS SUBSECTION EXISTS. `aw ipd lint` raises the advisory `check.ipd-uncarried-obligation` against the rows above, and the reasoning is exactly right: once this plan reaches `executed` it classes `done` in `aw attention`, so an obligation recorded ONLY in its prose vanishes with no record. So each row above is resolved here as either CARRIED (a durable artifact a gate can see), OWNED ELSEWHERE (a live sibling artifact), or CLOSED (no obligation remains). Nothing is left as prose-only.

- **CARRIED, filed by this execution.** Backlog **`wx72g3`** (`- Work-Kind: bug`, `- Blocks-Release: next`): `tests/test_turn_bounds.py`'s permission-policy test asserts an env var is ABSENT from an INHERITED environment, so it is red for every agent that runs the suite from inside an agent host. This is the single failure in both the BEFORE and AFTER bare-suite runs, and it degrades the very integration trust signal this Set protects.
- **CARRIED, filed by this execution.** Backlog **`nbu56f`** (`- Work-Kind: chore`): `run_suite_check`'s docstring still cites the stale `36` versus `15 failed, 20 passed` divergence whose cause is fixed and whose claim was retracted. This is the row above about that docstring being "a one-line courtesy at most, not a task here" - now it has a carrier instead of being a note inside a plan that is about to class `done`.
- **OWNED ELSEWHERE, cited rather than re-filed.** The stranded-lane and `_attempt2` clutter row is owned by live siblings `rl67b0` (the recovery verb) and `pr5b0t` (the `aw attention` reporting). This plan's own obligation there was narrow, absolute and DISCHARGED: it added nothing to that clutter, measured under V-02 (owner-record set unchanged, no `_attempt2` branch). The post-merge revalidation row is owned by `daexj1` E-03/E-04, both `Execution state: performed`. Capture-time id extraction is owned by `daexj1` E-01 as shipped by `h5pyqa`.
- **CLOSED: no obligation remains.** Four rows defer things that must NEVER be done rather than things not yet done, so there is nothing for a carrier to track: any gate keyed on the baseline (forbidden by the maintainer's ruling; E-05/V-05 prove its absence), changing `run_suite_check`'s primary-checkout contract (deliberate and unchanged), reusing one baseline across items (rejected by the maintainer), and exposing the baseline to a second consumer (a step toward the forbidden gate). The `dh0uno` row is closed by resolution, above. `daexj1`'s ownership of the prompt and its verdicts is a boundary, not a deferral.

## Scope check

- Over-scope: none. One baseline producer, one context block, one persisted record, one test module.
- Scope-Paths justification: `agent_workflows/runner_shared.py` is where the host-neutral baseline producer belongs, beside the other shared runner machinery, so neither host owns a private copy; `agent_workflows/oc_runipd.py` holds the dispatch seam where the baseline starts, the post-work collection point (`:6669`), the per-attempt record (`:6670`), `run_suite_check` (`:3631`, docstring `:3637-3653`), the base commit actually available at dispatch (`attempt["worktree_base"]`, `:6209`), and the four exit paths a cleanup construct must cover (`:6364`, `:6393`); `agent_workflows/agy_runipd.py` holds the twin seams (`:3724`, `:3725`) so both hosts behave identically; `tests/test_suite_baseline.py` is new because no existing module covers a concurrent out-of-band suite run.
- NOTE ONE PATH IS DELIBERATELY ABSENT AND MUST STAY ABSENT: `agent_workflows/run_evidence.py`. `daexj1` E-01 declares it and owns capture-time failing-id extraction. If the executor finds itself needing to edit it, the dependency has not landed and the correct action is to stop and report, not to add the path (F-11).
- IF `runner_shared.py` IS WHERE THE PRODUCER LANDS, IT MAY NOT IMPORT EITHER DRIVER. `tests/test_runner_shared.py::NoRunnerImportTests` AST-walks that module and fails on any name containing `runipd`, at module level or lazily, and a sibling test re-imports it standalone. `run_suite_check` lives in `oc_runipd.py`, so anything the producer needs from a driver must be INJECTED, following the `run_checked`/`host_label` precedent already in that module. (`tests/test_runner_shared.py` is not in Scope-Paths; if satisfying this needs a test edit there, declare it.)
- Under-scope, stated rather than left as `none`: this plan adds no gate and no refusal, does not touch the adjudication prompt or its verdicts, does not extract failing ids at capture time, does not change `run_suite_check`'s contract or fix its `stdout_excerpt` bug, does not correct its stale docstring measurement, does not fix the underlying state-resolution defect, does not clean up existing lane clutter, does not reuse baselines across items, exposes the baseline to no second consumer, and amends no spec.

## Required tests / validation

- THE RE-MEASURED DIVERGENCE (E-01) pasted with today's actual counts from a REAL linked worktree, and an explicit statement of whether any divergence remains. Do NOT paste the historical `36` versus `15 failed, 20 passed`; review measured `75 passed` in both and a full bare suite of `5920 passed, 3 skipped, 2 xfailed` in a worktree against `1 failed, 5919 passed` primary. If your measurement agrees, state that no neutralization is required and show the regression test that would fail if one reappeared; if it disagrees, paste the divergent id set and the recorded choice between neutralizing and subtracting.
- PROOF THE TWO RESULTS ARE COMPARABLE, stated explicitly: what makes the baseline's conditions equal to the post-work check's. If they are not made equal, the plan has produced misleading information rather than useful information.
- PROOF THE BASELINE CANNOT TOUCH THE AGENT'S LANE (F-14), which is the single most dangerous thing this plan can get wrong. Paste the allocation call and show, by construction, that its identity or mechanism cannot resolve to the agent's lane path; then paste the ADVERSARIAL case: with an agent lane present and EMPTY, run the baseline allocation and its cleanup, and show the agent's branch, its reflog and its worktree all still intact afterwards. Review measured the naive version destroying all three, so an assertion that it does not is required rather than optional.
- PROOF THE FAILING-ID FIELD IS `daexj1`'s, NOT A SECOND EXTRACTOR (F-11). Paste the field you consumed and its owning symbol, and show `run_evidence.py` is unmodified by this plan.
- PROOF THE BASE COMMIT CAME FROM A FIELD THAT EXISTS AT DISPATCH (F-15): paste the field read (`attempt["worktree_base"]` or equivalent) and state what happens on a `--no-isolate-worktree` turn, where no handle exists.
- PROOF THE CLEANUP COVERS ALL FOUR EXITS (F-16): paste the construct added and name the four paths it covers (`StopNowForce`, `StopAtCheckpoint`, `KeyboardInterrupt`, `StallTimeout`), since `execute_item` has no `finally` today.
- SEVEN FIXTURE CASES (E-07) each named with pasted output: baseline completes and reaches the prompt; baseline times out and the item proceeds with UNKNOWN; worktree creation fails and the item proceeds; a crashed turn leaves no stray worktree; verdict outcome identical with and without the id in the baseline; both hosts persist an identical shape; and THE LANE-SAFETY CASE, in which the agent's lane survives the baseline's allocation and cleanup with its branch, reflog and worktree intact (F-14).
- THE TWO REGRESSION GUARDS QUOTED SEPARATELY (timeout, creation failure), since making the runner more fragile in exchange for information is this plan's worst outcome.
- THE NOT-A-GATE ASSERTION QUOTED (E-05): a test showing a `SAFE TO IGNORE.` verdict is honored identically whether the failing test is in the baseline or not. This is the load-bearing property.
- ABSENCE-IS-NOT-EMPTY PROOF: the prompt text for an absent baseline pasted, showing it says UNKNOWN and not "nothing was failing".
- COMMIT-PINNING PROOF: paste evidence the baseline was taken at the item's recorded base commit, and a case where main MOVED during the turn showing the baseline still describes the original base.
- WALL-CLOCK MEASUREMENT: the added wall-clock for a realistic turn, measured rather than asserted, since the whole design was accepted on that basis.
- NO STRAY WORKTREE: `git worktree list` before and after the fixture cases, identical, including the crash case.
- NO REAL SUITE RUN AND NO REAL WORKTREE IN THIS REPOSITORY: show the suite invocation is stubbed and the fixtures use throwaway repos.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated as a set. MEASURE YOUR OWN BEFORE-BASELINE; do not quote this plan's, which has already moved. At authoring: `5859 passed, 3 skipped, 2 xfailed`. Re-measured at review 2026-09-08 (HEAD `c170204d`): `1 failed, 5919 passed, 3 skipped, 2 xfailed in 52.33s`, the failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL (189 files in the gitignored local `opencode-recovery/` dump, a path that test's skip list does not cover) and is absent in a clean checkout. Criterion: AFTER minus BEFORE is EMPTY.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw ipd lint --phase pre-transition` conforming, pasted.
- `aw sanitize --agent` clean.

## Spec / documentation sync

NO SPEC PATH IS DECLARED, and the reasoning is that this plan adds INFORMATION to an existing prompt and changes no contract. `daexj1` E-10 already amends spec `25kzda` to carry the narrow named exception the adjudication design requires; the baseline does not widen that exception, because it authorizes nothing new and refuses nothing.

THAT CONCLUSION WAS CHECKED AT REVIEW RATHER THAN LEFT TO THE EXECUTOR, AND IT SURVIVES, but the reasoning is narrower than the plan's and the executor must hold the line it draws (PR-509). `daexj1` E-10's amendment, per its own Spec / documentation sync section, must state "that a non-clean suite may be cleared for integration ONLY by an explicitly recorded agent adjudication that NAMES THE FAILING TEST IDS IT WAS SHOWN, that the adjudication is itself captured evidence rather than free prose, and that the deterministic finalize gate still applies unchanged afterwards". So the amendment does describe WHAT the agent is shown, and it names the failing-id list as part of what makes the exception reviewable.
WHY NO AMENDMENT IS STILL NEEDED HERE: the ids `daexj1`'s amendment names are the POST-WORK failing ids, which are what the adjudication is ABOUT. This plan adds a second, clearly-labelled context block describing the PRE-WORK state. It authorizes nothing, refuses nothing, and removes nothing from the evidence the amendment requires, so the exception is neither widened nor narrowed. The baseline makes an existing permitted judgement better informed; it does not change what may be cleared or by what authority.
THE LINE THAT WOULD BREAK THAT, and the executor must not cross it: the moment the baseline becomes part of what MAKES a `SAFE TO IGNORE.` acceptable (for instance if the prompt says an id absent from the baseline may not be cleared, or if any code weighs the two sets), the amendment's description of the authority is no longer accurate and this plan MUST amend the spec in the same change. That is the same boundary E-05 already forbids crossing for a different reason, which is a good sign the two constraints agree. If you find yourself needing the spec path, stop and report rather than adding it quietly: it would mean E-05's not-a-gate property has been lost.
RE-READ `daexj1` E-10's ACTUAL LANDED TEXT before relying on this, since `daexj1` executes first and its amendment's final wording is not yet written.

**DONE AT EXECUTION 2026-09-21, AND THE CONCLUSION IS STRONGER THAN THE PLAN EXPECTED: NO AMENDMENT IS NEEDED, AND THE LANDED SPEC TEXT EXPLICITLY AUTHORIZES EXACTLY WHAT THIS PLAN BUILT.** The amendment is in spec `0718` (`aw-run-deterministic-run-and-verify`, the spec `25kzda` resolves to), recorded in its workflow history as "AMENDED by plan daexj1 (integearn-03) E-10". Its `THE HONEST LIMIT` paragraph reads, quoted verbatim from the file:

> THE HONEST LIMIT, stated so the exception is not trusted further than it holds. The agent may answer
> "not mine" in good faith about a failure it actually caused, because it has no baseline of the suite
> before its own work and so cannot know what was already red. The maintainer ruled on 2026-09-08 and again
> on 2026-09-20 that no programmatic gate may refuse the verdict on that basis: a pre-work baseline may be
> supplied to the agent as INFORMATION so it can answer more accurately, but nothing refuses on it. So this
> exception mitigates SLOPPINESS and not deception, and ATTRIBUTION is what makes it safe [...]

So the spec ALREADY NAMES this plan's deliverable and already fixes its terms: a pre-work baseline MAY be supplied AS INFORMATION, and NOTHING may refuse on it. What I built is that sentence implemented, and E-05/V-05 prove the second clause holds in code. Two consequences worth stating plainly. FIRST, this is no longer merely "an amendment is not required": supplying the baseline is the spec's own stated remedy for the limit the exception carries, so building it makes the spec MORE accurate rather than leaving it untouched. SECOND, the line the plan warned against crossing is now a SPEC line and not only a plan line - the moment any code weighed the two id sets, it would contradict "nothing refuses on it" in an APPROVED spec, which is a far louder failure than contradicting a plan's prose. The plan's instinct that the two constraints would agree was right.

I ALSO CHECKED WHAT THE AMENDMENT REQUIRES BE CAPTURED, since the plan's concern was whether the baseline widens or narrows it. The amendment admits the adjudication ONLY as captured evidence comprising "the answer token, the reason, THE FAILING TEST IDENTIFIERS THE AGENT WAS SHOWN, the answering session, and the re-run count/outcome". Those are the POST-WORK ids, which `h5pyqa` already persists at `gate_answer_record`'s `failing_tests`, and this plan does not touch them: it ADDS a separately-keyed `suite_baseline` block describing the PRE-WORK state. Nothing the amendment requires is removed, reshaped, or made optional, and nothing new is authorized or refused. `NO SPEC PATH IS DECLARED` in `Scope-Paths` and none was needed; `git status` shows no `.spec.md` modified by this execution.

THE RULING MUST BE RECORDED AT THE CODE, not only in this plan (E-05). The sentence that matters: the baseline is information for an honest agent, not a check on a dishonest one, because a gate cannot detect deception, a capable model can make tests pass, a genuinely malicious agent would rewrite the gate, and the target is sloppiness. A baseline sitting in the run record with no such comment reads as an unfinished check, and the next reader will finish it.

DOCUMENT THE WORKTREE COMPARABILITY DECISION where the next reader will hit it, at the baseline producer. Whichever route E-01 chooses, a future maintainer must be able to tell whether a difference between the two id sets is real or an artifact of where each ran. If the route is a subtraction list, say plainly that it is hand-maintained and will rot.

## Open questions

### OQ-01: Can the baseline be made comparable without relaxing the primary-checkout contract?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY MEASUREMENT, 2026-09-08: YES, AND AT PRESENT IT REQUIRES NO WORK AT ALL, because the divergence the question presupposes is gone. Measured at HEAD `c170204d` in a real linked worktree created with `git worktree add --detach` and holding ZERO run directories, which is exactly the condition the cited defect describes: `python3 -m pytest tests/test_run_viewer.py` gives `75 passed`, IDENTICAL to the primary checkout's `75 passed` (140 run dirs); and the FULL bare suite gives `5920 passed, 3 skipped, 2 xfailed in 54.09s` in the worktree against `1 failed, 5919 passed, 3 skipped, 2 xfailed` in the primary checkout, where the single failure is environmental and primary-only. So the two are comparable TODAY with no neutralization and no subtraction, and the primary-checkout contract is untouched. The docstring's `36` versus `15 failed, 20 passed` is historical: `tests/test_run_viewer.py` has been changed since (`0d349cc5`, `ff092eae`, `661643bb`) and sibling `utwr6y` (`testiso-01`) owns exactly this ground.
  WHAT E-01 THEREFORE OWES, and it is smaller than the question assumed: RE-MEASURE (do not trust this paragraph either, since the tree moves daily), record the result, and if the divergence is still absent, add a REGRESSION TEST that fails if one reappears rather than a neutralization layer for a condition nobody can observe. Only if a divergence IS found do the three original routes apply, in the stated preference order (neutralize the cause; run both sides under identical rules; subtract a re-measured set, weakest because hand-maintained). Building a subtraction list from the stale fifteen ids would MASK fifteen real failures.

### OQ-02: What is the right bound on waiting for a late baseline?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: OPEN AND MEASURABLE, so it is the executor's. The suite is ~81 seconds and turns are minutes to hours, so a baseline should essentially always be ready first and the bound exists only so a wedged suite cannot hang a driver. What the executor must decide from measurement rather than taste: whether the bound is a fixed timeout, a multiple of the observed suite duration, or simply "whatever is ready at collection time with no wait at all". THE LAST OPTION IS PROBABLY BEST and is worth trying first, because a zero-wait collection cannot delay a turn by construction, which is the property the maintainer accepted this design on. Record what you chose and the measurement behind it.
  **RESOLVED AT EXECUTION 2026-09-21: OPTION THREE, "WHATEVER IS READY AT COLLECTION TIME WITH NO WAIT AT ALL."** Implemented as `SuiteBaselineRun.collect(wait_seconds=0.0)`, with the default on the parameter itself AND the call site passing `0.0` explicitly so a future reader cannot change the behavior by editing one of the two.
  THE MEASUREMENT BEHIND IT, rather than taste. The bare suite in this checkout runs 104-199s (measured 198.60s, 118.47s, 107.20s, 104.49s across the four runs recorded in V-01/V-07; the spread is machine load, and this is notably SLOWER than the ~81s the plan cites, which strengthens the argument rather than weakening it). Against that, the added wall-clock of the zero-wait design measured 10.2 ms to start plus 0.2 ms to collect, with the suite itself running entirely inside the turn's own duration:
  ```
  baseline START cost added to the turn : 10.2 ms
  baseline COLLECT cost added to the turn: 0.2 ms
  the baseline's own suite ran for       : 5.00 s (concurrently)
  TOTAL ADDED WALL-CLOCK                 : 10.4 ms of a 5000 ms turn
  ```
  WHY NOT A POSITIVE BOUND, which is the real content of the decision. A fixed timeout or a multiple of the observed duration would both be SAFE in the common case and would both, in the rare case, do the one thing the maintainer accepted this design on the condition it could never do: delay a turn. A zero wait cannot, BY CONSTRUCTION, so the property is structural rather than empirical - it holds on a slow machine, under load, and if the suite triples in length, none of which a tuned constant survives. And the cost of choosing it is small and bounded: a baseline that is late is merely ABSENT, and absence is already a first-class outcome the agent is told about honestly.
  THE HANG RISK IS STILL CLOSED, separately, so choosing zero is not choosing "no bound anywhere". The CHILD carries its own `SUITE_BASELINE_TIMEOUT_SECONDS` (900s, matching `run_suite_check`'s), and `collect()` KILLS a still-running child rather than orphaning it, so a wedged suite can neither hang the driver nor survive the turn burning CPU unobserved.
  A BOUND REMAINS AVAILABLE as an explicit `wait_seconds` argument for a future caller with a different trade to make; the tests use a positive bound precisely to exercise that path deterministically. Nothing in production passes one.

### OQ-03: Should an absent baseline be surfaced to the operator, or only to the agent?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN, AND GENUINELY THE MAINTAINER'S, because it is a reporting-volume judgement rather than a fact. E-04 requires the AGENT be told UNKNOWN rather than shown an empty set, which is settled. What is not settled is whether a HUMAN should see it. FOR: a `SAFE TO IGNORE.` decided without a baseline is materially weaker than one decided with it, and an operator reading the run summary cannot currently tell those apart. AGAINST: this repository already has several plans in flight adding end-of-run reporting, and one more line that says "the baseline did not finish" on an otherwise successful run is noise most of the time. The middle route is to persist it (E-06 does) and let whoever owns the run summary decide whether to surface it, which costs nothing now and keeps the fact available. Non-blocking because the record is written either way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the re-measured suite results from the primary checkout AND from a real linked worktree, with today's actual counts. Do NOT paste the historical `36` versus `15 failed, 20 passed`: review measured `75 passed` in both and a full bare suite of `5920 passed, 3 skipped, 2 xfailed` in the worktree against `1 failed, 5919 passed` primary (F-12). State explicitly whether ANY divergence remains. If none does, say so, state that no neutralization or subtraction is being built and why that is the honest answer, and paste the regression test that fails if a divergence reappears. If one does, list the divergent id set, state which route you chose and why, and if it is a hand-maintained subtraction list say plainly that it will rot. A pasted neutralization layer with no measured divergence to neutralize is a FAILED validation.
  - Observed evidence: **RE-MEASURED 2026-09-21 AT HEAD `24aa8d41`, AND THE DIVERGENCE IS ZERO. NO neutralization and NO subtraction layer was built.** Measured in a REAL linked worktree created with `git worktree add --detach` off a FRESH `--no-hardlinks` clone, holding ZERO run directories, which is exactly the condition backlog `dh0uno` describes. The clone was made because this lane IS itself a linked worktree, so cloning gives a genuine PRIMARY checkout to compare against.

    ```
    $ git -C <clone>/primary rev-parse HEAD
    24aa8d413d07edce91b14f4a9181995132f3daaf
    $ git -C <clone>/lane rev-parse --git-dir
    <clone>/primary/.git/worktrees/lane
    ```

    THE NAMED FILE, in both checkouts:

    ```
    $ (cd <clone>/primary && python3 -m pytest tests/test_run_viewer.py)
    91 passed in 7.17s
    $ (cd <clone>/lane && python3 -m pytest tests/test_run_viewer.py)
    91 passed in 7.46s
    ```

    THE FULL BARE SUITE, in both checkouts:

    ```
    $ (cd <clone>/primary && python3 -m pytest)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 7830 passed, 3 skipped, 2 xfailed, 3 warnings in 118.47s (0:01:58)
    $ (cd <clone>/lane && python3 -m pytest)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 7830 passed, 3 skipped, 2 xfailed, 3 warnings in 107.20s (0:01:47)
    ```

    **DOES ANY DIVERGENCE REMAIN? NO. ZERO.** The two failing sets are IDENTICAL, not merely equal in count: the same single id in both. So the divergence does not run in the plan's direction, does not run in review's opposite direction either (review saw the environmental failure as primary-only; today it appears in BOTH, because its cause is the HOST environment rather than the checkout - see the defect I filed, `wx72g3`), and is not present at all.

    WHY NO NEUTRALIZATION AND NO SUBTRACTION IS THE HONEST ANSWER, not a shortcut. (1) There is nothing observable to neutralize; a neutralization layer would be dead code guarding a condition nobody can measure, and the plan itself says it would be the second-largest thing here. (2) A subtraction list built from the docstring's fifteen stale ids would SUBTRACT FIFTEEN REAL FAILURES if they ever appeared, which is strictly worse than no list. (3) The cause is fixed and its claim retracted: backlog `dh0uno` is `- Status: done` and its own history records "NOTE the old acceptance claim that ~15 test_run_viewer failures ARE this bug was false". Sibling `utwr6y` (`testiso-01`) owns that ground and explains the result, exactly as PR-502/F-13 anticipated, so I cite it rather than re-deriving the cause.

    WHAT WAS BUILT INSTEAD IS THE PROPERTY, so a regression is a red test rather than an incident. The comparability premise is now monitored by `tests/test_suite_baseline.py::TheTwoMeasurementsAreComparable`, which asserts the two sides share ONE extractor and ONE argv and that no subtraction layer exists:

    ```
    $ python3 -m pytest tests/test_suite_baseline.py::TheTwoMeasurementsAreComparable -o addopts="" -v
    tests/test_suite_baseline.py::TheTwoMeasurementsAreComparable::test_both_sides_extract_failing_ids_with_the_SAME_function PASSED
    tests/test_suite_baseline.py::TheTwoMeasurementsAreComparable::test_the_baseline_runs_the_SAME_argv_as_the_post_work_check PASSED
    tests/test_suite_baseline.py::TheTwoMeasurementsAreComparable::test_the_baseline_builds_NO_neutralization_or_subtraction_layer PASSED
    tests/test_suite_baseline.py::TheTwoMeasurementsAreComparable::test_the_comparability_decision_is_DOCUMENTED_at_the_producer PASSED
    ```

    PROOF THE TWO RESULTS ARE COMPARABLE, stated explicitly as the plan's separate validation line demands. What makes the baseline's conditions equal to the post-work check's: both run the SAME argv (`oc_runipd.SUITE_CHECK_ARGV`, a BARE `python3 -m pytest` whose flags come from `pyproject.toml` `addopts`, asserted equal on both hosts), over the SAME repository, and both extract failing ids through the SAME function (`oc_runipd.extract_suite_failures`, asserted by object identity `OC.extract_suite_failures is AGY.extract_suite_failures` -> `True`). The ONE deliberate difference is the CHECKOUT: post-work in the PRIMARY checkout (contract unchanged), baseline in its own detached checkout at the item's base commit. That difference is the thing measured above and it contributes ZERO today. The reasoning is recorded at the producer under `WHY THE MEASUREMENT IS COMPARABLE TO THE POST-WORK ONE`, so the next reader can tell a real difference from an artifact.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the checkout creation call showing it is pinned to a COMMIT (not a branch name) read from a field that EXISTS AT DISPATCH, and name that field; `item["preserved_base"]` is written only after the turn, so pasting it is a FAILED validation (F-15). State what happens on a `--no-isolate-worktree` turn, where no handle exists.
    THE LOAD-BEARING PASTE IS THAT THE AGENT'S LANE SURVIVES (F-14). Paste the ADVERSARIAL case: with the agent's lane present and EMPTY, run the baseline allocation and then its cleanup, and paste `git branch --list 'aw/lane/*'`, `git reflog show <agent branch>` and the agent worktree's existence, all showing the lane INTACT. Review measured the naive prescription (`allocate_worktree` keyed on the item's id6, then unconditional `teardown_worktree`) adopting the agent's own path and then deleting its branch, reflog and commits, so this assertion is mandatory. Also paste the case where the agent has ALREADY COMMITTED, showing NO `_attempt2` lane was created and NO owner record was written under a bogus identity. State which route you took (non-colliding lane identity, or a detached checkout outside the lane namespace) and why.
    Paste a case where main moved during the turn and show the baseline still describes the original base. Paste `git worktree list` before and after, including after a simulated crash, showing no stray checkout. Confirm the baseline never READS the agent's lane.
  - Observed evidence: **ROUTE (b) WAS TAKEN: A PLAIN DETACHED WORKTREE OUTSIDE THE LANE NAMESPACE.** Not a non-colliding lane identity, and the reason is that route (b) removes the hazard by CONSTRUCTION rather than by careful naming. The lane machinery exists to manage WRITE lanes with ownership, adoption, attempt-scoping and recovery semantics; this checkout writes nothing, so it needs no branch, no owner record and no lane classification. And critically: `teardown_worktree` is destructive ONLY because it deletes a BRANCH and its REFLOG (its own docstring calls that a DATA-SAFETY HAZARD), so a checkout that HAS no branch has nothing to destroy but a directory. A distinct lane id would still have put a branch and an owner record into the namespace that `resolve_prior_lane` and the reclamation classifier read.

    THE CREATION CALL, pinned to a COMMIT and not a branch name (`agent_workflows/runner_shared.py`, `start_suite_baseline`):

    ```python
    resolved = git(["rev-parse", "--verify", f"{commit}^{{commit}}"])
    ...
    sha = str(getattr(resolved, "stdout", "") or "").strip() or commit
    path = suite_baseline_checkout_path(repo, id6, attempt)
    ...
    added = git(["worktree", "add", "--detach", str(path), sha])
    ```

    `--detach` means no branch is created. `sha` is a resolved commit id (`^{commit}`), never a branch name.

    THE FIELD READ, AND IT EXISTS AT DISPATCH (F-15). The field is **`attempt["worktree_base"]`**, written from `wt_handle.base_commit` immediately after lane allocation, upstream of the dispatch point. The call site in `execute_item_core`:

    ```python
    suite_baseline_run, suite_baseline = start_suite_baseline(
        repo,
        id6=item["id6"],
        attempt=attempt_no,
        base_commit=str(attempt.get("worktree_base") or ""),
    ```

    `item["preserved_base"]` is NOT read, and a test asserts it is not: `test_the_base_commit_is_read_from_the_field_written_AT_ALLOCATION` fails if that name appears in the call. It is written only on the POST-turn preservation path and only when the item did NOT reach `executed`, so a baseline pinned to it would never be taken on a first attempt at all.

    ON A `--no-isolate-worktree` TURN there is no handle, so no base is recorded and `start_suite_baseline` returns an ABSENT record naming that case rather than pinning to a moving `HEAD`:

    ```
    state  : absent
    reason : no base commit was recorded for this attempt at dispatch, so no baseline could be
             pinned (a NON-ISOLATED turn has no worktree handle and therefore no base to pin to);
             the pre-work failing set is UNKNOWN
    known  : False
    ```

    **THE LOAD-BEARING PASTE: THE AGENT'S LANE SURVIVES (F-14).** Run in a throwaway repo, performing the exact sequence review measured DESTROYING a branch, reflog and commits:

    ```
    ### CASE (g) PART 1: agent lane present and EMPTY
    agent lane allocated: aw/lane/abc123 at .../abc123 disposition created

    -- BEFORE the baseline --
    $ git branch --list 'aw/lane/*'
    + aw/lane/abc123
    $ git reflog show aw/lane/abc123
    ced29bb aw/lane/abc123@{0}: branch: Created from ced29bb1071386488da67308413e70810cc752d2

    baseline checkout basename : abc123-attempt1
    agent lane basename        : abc123
    SAME PATH?                 : False   <-- MUST be False
    baseline is under .aw/worktrees/ ? False  <-- MUST be False
    baseline result            : completed ('FAILED tests/test_x.py::t - boom',)

    -- AFTER the baseline's allocation AND cleanup --
    agent worktree still exists: True  <-- MUST be True
    $ git branch --list 'aw/lane/*'
    + aw/lane/abc123
    $ git reflog show aw/lane/abc123
    ced29bb aw/lane/abc123@{0}: branch: Created from ced29bb1071386488da67308413e70810cc752d2
    REFLOG IDENTICAL?          : True  <-- MUST be True
    worktree list IDENTICAL?   : True  <-- MUST be True
    baseline checkout gone     : True  <-- MUST be True
    ```

    The agent's WORKTREE, its BRANCH and its REFLOG are all intact, byte for byte. Review measured the naive prescription destroying all three.

    THE OTHER TIMING, where the agent HAS ALREADY COMMITTED (which is where the naive route attempt-scoped instead):

    ```
    ### CASE (g) PART 2: agent lane HOLDING A COMMIT
    agent commit tip: 496b8bfa0635
    owner records BEFORE: ['abc123.json']
    owner records AFTER : ['abc123.json']
    $ git branch --list 'aw/lane/*'
    + aw/lane/abc123
    any _attempt2 lane?        : False  <-- MUST be False
    agent commit still reachable: True  <-- MUST be True
    ```

    NO `_attempt2` lane and NO owner record under a bogus identity: the owner-record set is unchanged (`['abc123.json']` before and after), so the durable lane state `resolve_prior_lane` and the reclamation classifier read is unpolluted, and the `_attempt2` clutter `rl67b0`/`pr5b0t` exist to REDUCE was not added to.

    BY CONSTRUCTION, ASSERTED AS WELL AS MEASURED. Three structural tests make this unreachable rather than merely unobserved: `test_the_baseline_path_is_OUTSIDE_the_lane_namespace_by_construction` (the path cannot contain `.aw/worktrees`), `test_the_producer_calls_NEITHER_allocate_worktree_NOR_teardown_worktree` (over CODE with comments and docstrings stripped, so the explanation may keep naming them), and `test_the_removal_path_can_delete_NO_REF_AT_ALL` (the removal path's code contains no `branch`, `-D`, `update-ref` or `reflog`).

    MAIN MOVED DURING THE TURN, and the baseline still describes the original base (`test_a_MOVED_main_does_not_change_what_the_baseline_describes`): the baseline starts at `base`, a commit then lands on main mid-turn, and afterwards `result.base_commit == base`, `git -C <checkout> rev-parse HEAD == base`, and the mid-turn file is NOT present in the checkout. This is the maintainer's own requirement and the reason commit-pinning rather than branch-pinning was chosen.

    NO STRAY WORKTREE AFTER A SIMULATED CRASH (`test_a_CRASHED_turn_leaves_NO_STRAY_WORKTREE`): `git worktree list` is captured, the baseline is started (list differs), a `KeyboardInterrupt` is raised and handled the way the added `finally` handles it, and `git worktree list` is then asserted EQUAL to the original string. In THIS repository, after every fixture case and after removing my own E-01 scratch clone, `git worktree list` shows 46 entries with ZERO matching `suite-baseline` or `scratch`, and `git branch --list 'aw/lane/*'` shows 82, unchanged.

    THE BASELINE NEVER READS THE AGENT'S LANE, confirmed: the checkout is created from the COMMIT by `git worktree add --detach` run in the PRIMARY repo, so the lane directory is never opened. `test_the_baseline_NEVER_READS_the_agents_lane` asserts the baseline path neither equals nor lies under the agent's lane path.

    ```
    $ python3 -m pytest tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane -o addopts="" -v
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_ADVERSARIAL_a_lane_HOLDING_A_COMMIT_gains_no_attempt2_and_no_owner_record PASSED [ 16%]
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_ADVERSARIAL_an_EMPTY_agent_lane_survives_allocation_and_cleanup PASSED [ 33%]
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_the_producer_calls_NEITHER_allocate_worktree_NOR_teardown_worktree PASSED [ 50%]
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_the_baseline_path_is_OUTSIDE_the_lane_namespace_by_construction PASSED [ 66%]
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_the_removal_path_can_delete_NO_REF_AT_ALL PASSED [ 83%]
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_the_baseline_NEVER_READS_the_agents_lane PASSED [100%]

    ============================== 6 passed in 0.47s ===============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the concurrency mechanism and state why it cannot deadlock with the turn, AND state why `run_suite_check` could not be reused for it (it blocks inside `subprocess.run` with no start/poll/collect split, F-17). Paste the cleanup construct you ADDED and name the four exit paths it covers, since `execute_item` has no `finally` today (F-16). Paste the failing-id field you CONSUMED from `daexj1` E-01 by its owning symbol, and show `run_evidence.py` is unmodified by this plan (F-11). Paste the measured ADDED WALL-CLOCK for a realistic turn, since the design was accepted on that basis. Paste the timeout case and the hard-failure case, each showing the item completing exactly as it does today with the baseline recorded as absent and a reason, and showing the baseline did NOT inherit `run_suite_check`'s fail-closed stance.
  - Observed evidence: **THE CONCURRENCY MECHANISM** is a plain `subprocess.Popen` plus a DAEMON thread that only drains its pipes (`runner_shared.SuiteBaselineRun`):

    ```python
    spawn = popen or subprocess.Popen
    self.process = spawn(
        self.argv,
        cwd=str(self.checkout),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    self._drain = threading.Thread(target=self._pump, daemon=True)
    self._drain.start()
    ```

    WHY IT CANNOT DEADLOCK WITH THE TURN, three structural reasons rather than an assurance. (1) IT SHARES NO LOCK WITH THE TURN: it touches no run lock, no lane owner record, no `state` dict and no run directory, writing only into its own detached checkout, so there is no lock either side can hold while waiting on the other. (2) THE DEPENDENCY IS ONE-WAY: the baseline never waits on the turn, and the turn waits on the baseline only in a BOUNDED collection whose default bound is ZERO. (3) THE PIPES ARE DRAINED BY A DAEMON THREAD, which closes the one classic deadlock this shape admits (a child blocking on a full pipe while the collector waits for the child). Being a daemon, it can never keep the interpreter alive. No new concurrency model was introduced beyond this: the runner already uses `subprocess` plus threads for telemetry sampling, so this follows the existing shape.

    **WHY `run_suite_check` COULD NOT BE REUSED** (F-17), asserted by test rather than asserted in prose (`test_run_suite_check_could_NOT_have_been_reused_because_it_BLOCKS`): it is SYNCHRONOUS BY CONSTRUCTION. It calls `run_evidence.capture_command`, which calls `subprocess.run(...)` and blocks until the process exits or its timeout fires, and there is NO start/poll/collect split anywhere in it - the test asserts the strings `poll`, `communicate` and `Popen` are all ABSENT from its source. So a concurrent baseline required a NEW path.

    IT DID NOT INHERIT THE FAIL-CLOSED STANCE, which was the second consequence the plan required owning. `run_suite_check`'s docstring says "FAIL CLOSED (E-02): a suite that cannot be run is a FAILURE, never a pass", correct THERE because it guards integration. The baseline's equivalent seam says the opposite, in `suite_baseline_absent`: "A BASELINE THAT COULD NOT BE TAKEN IS NOT A FAILED ITEM". Asserted by `test_the_baseline_does_NOT_inherit_run_suite_checks_FAIL_CLOSED_stance`.

    **THE CLEANUP CONSTRUCT I ADDED** (F-16). `execute_item_core` contained ZERO `finally:` blocks, so this is new STRUCTURE: the whole post-dispatch remainder of the function was wrapped in a `try:`, with this `finally:` appended:

    ```python
    finally:
        # integearn-05 (`9lyg5h`) E-02: UNCONDITIONAL, and this is the ONLY teardown of a baseline.
        # ...
        if suite_baseline_run is not None:
            with contextlib.suppress(Exception):
                suite_baseline_run.abandon()
            with contextlib.suppress(Exception):
                remove_suite_baseline_checkout(repo, suite_baseline_run.checkout)
    ```

    THE FOUR EXIT PATHS IT COVERS, named: **`StopNowForce`**, **`StopAtCheckpoint`**, **`StallTimeout`** (each an `except ... return` on the `spawn_executor` call, all three now INSIDE the new `try`) and **`KeyboardInterrupt`** (which propagates out of the function untouched and so passes through the `finally`). It additionally covers the two `raise DriverError` session-drift paths and every ordinary `return`. That the four are enclosed is asserted mechanically by AST in `test_a_try_finally_was_ADDED_and_it_encloses_the_dispatch`, which locates the `ast.Try` whose `finalbody` mentions `remove_suite_baseline_checkout` and requires `spawn_executor(` plus all four names inside its `body`. The `finally` is best-effort and silent by contract, because a raising `finally` would REPLACE the exception the turn was already carrying (including a deliberate stop).

    **THE FAILING-ID FIELD I CONSUMED, BY ITS OWNING SYMBOL** (F-11): **`oc_runipd.extract_suite_failures`** (`agent_workflows/oc_runipd.py:3979`), shipped by `h5pyqa` (`gatewire-01`) which landed `daexj1` E-01's capability. It is reached through injection, never import, because `runner_shared` may not import a driver:

    ```
    $ python3 -c "...; print('oc extract is agy extract:', OC.extract_suite_failures is AGY.extract_suite_failures)"
    oc extract is agy extract: True
    ```

    NO SECOND EXTRACTOR WAS WRITTEN, asserted over CODE (comments/docstrings stripped) by `test_NO_SECOND_ID_EXTRACTOR_WAS_WRITTEN`: the baseline's code contains no `re.compile`, no `FAILED` literal and no `short test summary`.

    `run_evidence.py` IS UNMODIFIED BY THIS PLAN, and its absence from `Scope-Paths` held:

    ```
    $ git status --short agent_workflows/run_evidence.py
    $ git diff --stat HEAD -- agent_workflows/run_evidence.py
    ```

    Both EMPTY. Also asserted structurally by `test_run_evidence_IS_UNMODIFIED_BY_THIS_PLAN`, which requires neither `run_evidence` nor `capture_command` to appear in the baseline's code.

    **THE MEASURED ADDED WALL-CLOCK**, which is the basis the design was accepted on. A realistic turn simulated with a 3s suite against a 5s turn:

    ```
    baseline START cost added to the turn : 10.2 ms
    baseline COLLECT cost added to the turn: 0.2 ms
    the baseline's own suite ran for       : 5.00 s (concurrently)
    state=completed failures=('FAILED tests/test_x.py::t - boom',) summary='1 failed, 2 passed in 3.00s'
    baseline CLEANUP cost                  : 5.2 ms
    TOTAL ADDED WALL-CLOCK                 : 10.4 ms of a 5000 ms turn, while the 3.00s suite ran for free
    ```

    10.4 ms of added wall-clock (plus 5.2 ms of cleanup after the turn), against a real suite of ~105-120s measured above and real turns of minutes to hours. The suite cost is genuinely ZERO because it overlaps the turn, and the collection is a ZERO-wait join by default.

    OQ-02 ANSWERED FROM THAT MEASUREMENT, as the question assigned to this executor requires: **"whatever is ready at collection time with no wait at all"**, the option the plan called probably best and worth trying first. It is implemented as `collect(wait_seconds=0.0)` and the call site passes `0.0` explicitly. The measurement behind the choice: the baseline's suite needs ~105-120s while turns run minutes to hours, so a zero-wait collection essentially always finds a finished baseline, and unlike any positive bound it CANNOT delay a turn by construction - which is the exact property the maintainer accepted the design on. A bound remains available as a parameter, and the child's own `SUITE_BASELINE_TIMEOUT_SECONDS` (900s) means a wedged suite cannot linger.

    **THE TIMEOUT CASE**, showing the item proceeding with an ABSENT baseline and a reason, never an empty set:

    ```
    state  : absent
    known  : False
    failures: ()
    reason : the baseline suite had not finished when the turn ended (waited 0s of a 900s bound);
             the pre-work failing set is UNKNOWN
    prompt : contains "UNKNOWN"; does NOT contain "NOTHING was failing"
    ```

    **THE HARD-FAILURE CASE** (checkout cannot be created), same shape:

    ```
    state  : absent
    reason : the baseline checkout could not be created at <path>: fatal: invalid reference:
             deadbeefdeadbeefdeadbeefdeadbeefdeadbeef
    ```

    Both guards pass, and neither makes the item fail:

    ```
    $ python3 -m pytest "tests/test_suite_baseline.py::TheBaselineRunsConcurrentlyAndCannotDelayTheTurn::test_REGRESSION_GUARD_a_TIMED_OUT_baseline_yields_UNKNOWN_and_not_an_empty_set" "tests/test_suite_baseline.py::TheBaselineRunsConcurrentlyAndCannotDelayTheTurn::test_REGRESSION_GUARD_a_CREATION_FAILURE_leaves_the_item_unaffected" -o addopts="" -v
    tests/test_suite_baseline.py::...::test_REGRESSION_GUARD_a_CREATION_FAILURE_leaves_the_item_unaffected PASSED [ 50%]
    tests/test_suite_baseline.py::...::test_REGRESSION_GUARD_a_TIMED_OUT_baseline_yields_UNKNOWN_and_not_an_empty_set PASSED [100%]

    ============================== 2 passed in 0.27s ===============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the prompt text WITH a baseline, showing the already-failing set stated as information rather than accusation. Paste the prompt text WITHOUT one, showing it says UNKNOWN and does NOT imply nothing was failing. Confirm by diff that `daexj1`'s prompt structure and its three verdict sentinels are unchanged.
  - Observed evidence: **THE PROMPT TEXT WITH A BASELINE** (the block `gate_answer_question` inserts, rendered by `suite_baseline_context`):

    ```
    WHAT WAS ALREADY FAILING BEFORE YOUR TURN, measured by running the same suite at your own base
    commit (24aa8d413d07) in a separate checkout while you worked: these tests were ALREADY FAILING
    before your work existed (1 failed, 7830 passed, 3 skipped, 2 xfailed in 118.47s):

      FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2
      ERROR tests/test_broken_import.py

    THIS IS INFORMATION TO HELP YOU JUDGE, NOT AN ACCUSATION AND NOT A CONSTRAINT ON YOUR ANSWER.
    Nothing checks your answer against this list and nothing refuses on it. A failure that is NOT
    listed here may still genuinely be nothing to do with your work (it may be flaky,
    order-dependent, or caused by something that landed while you worked), and a failure that IS
    listed here is one you can attribute with confidence.
    ```

    STATED AS INFORMATION RATHER THAN ACCUSATION, and the wording does real work in two directions. It says outright that nothing checks the answer against the list and nothing refuses on it, so the agent is not being asked to justify itself; and it says an UNLISTED failure may still genuinely be `not-mine`, which is the important half - without it a well-meaning agent would read the list as an implicit constraint and answer `mine` for anything absent from it, which would be a de-facto gate built out of prose rather than code. Asserted by `test_it_is_stated_as_INFORMATION_and_not_as_an_ACCUSATION_or_a_CONSTRAINT`.

    **THE PROMPT TEXT WITHOUT ONE** (absent), which says UNKNOWN and does NOT imply nothing was failing:

    ```
    WHAT WAS ALREADY FAILING BEFORE YOUR TURN: UNKNOWN. A pre-work baseline of the suite was NOT
    available for this turn (the baseline suite had not finished when the turn ended (waited 0s of a
    900s bound); the pre-work failing set is UNKNOWN). This does NOT mean nothing was failing before
    you started; it means nobody measured. Answer from the evidence you do have, exactly as you
    would if this section were not here.
    ```

    THE INVERSION IS EXPLICITLY CLOSED: "This does NOT mean nothing was failing before you started; it means nobody measured." That is the same defect class `daexj1` E-02 exists to prevent on the other side of this feature, and `test_an_ABSENT_baseline_says_UNKNOWN_and_NEVER_implies_nothing_was_failing` asserts the absent rendering contains `UNKNOWN` and `it means nobody measured` while containing NEITHER `NOTHING was failing` NOR `were ALREADY FAILING`. The parameter DEFAULTS to `None` and `None` renders this same UNKNOWN text, so every pre-existing caller that passes no baseline reads as UNKNOWN rather than as green (`test_the_DEFAULT_is_the_UNKNOWN_wording_not_an_empty_list`).

    A COMPLETED-AND-GREEN baseline is a THIRD, distinct rendering ("NOTHING was failing. The suite was GREEN at your base commit (7830 passed in 104.49s)."), so "nothing was red" and "nobody looked" are never conflated in either direction.

    **`daexj1`'s PROMPT STRUCTURE AND ITS VERDICT SENTINELS ARE UNCHANGED, CONFIRMED BY DIFF.** `test_the_baseline_BLOCK_IS_THE_ONLY_DIFFERENCE_the_prompt_gains` computes the prompt with and without a baseline, replaces each rendering of the context block with a sentinel in its respective copy, and asserts the two results are EQUAL - so the ONLY textual difference the prompt gains is the block itself. Separately `test_daexj1s_PROMPT_STRUCTURE_and_THREE_SENTINELS_are_UNCHANGED` asserts every member of `R.GATE_ANSWERS` (`not-mine`, `fixed`, `mine`, `needs-human`), the outcome-JSON key `R.GATE_ANSWER_KEY`, and the four structural anchors (`This is a question, not an accusation`, `YOUR LANE IS THEN INTEGRATED`, `THE FILES YOUR TURN CHANGED`, `CHOOSE THE ANSWER THAT IS TRUE`) all still appear in the baseline-carrying prompt.

    ONE CORRECTION TO THE PLAN'S OWN WORDING, recorded rather than silently absorbed: the plan and this V-item speak of "`SAFE TO IGNORE.`" and "three verdict sentinels". The SHIPPED design (`h5pyqa`, which landed `daexj1`'s asking) uses FOUR answers written into a JSON key rather than three prose sentinels, and the releasing answer is `not-mine`, not `SAFE TO IGNORE.`. I validated against what SHIPPED. The plan's intent is unaffected: the releasing answer's meaning ("not attributable to my work, or already failing before my turn") is exactly the judgement this baseline informs.

    ```
    $ python3 -m pytest tests/test_suite_baseline.py::ThePromptCarriesTheBaselineAsContext -o addopts="" -v
    tests/test_suite_baseline.py::...::test_daexj1s_PROMPT_STRUCTURE_and_THREE_SENTINELS_are_UNCHANGED PASSED [ 48%]
    tests/test_suite_baseline.py::...::test_the_DEFAULT_is_the_UNKNOWN_wording_not_an_empty_list PASSED [ 52%]
    tests/test_suite_baseline.py::...::test_the_already_failing_set_REACHES_the_prompt PASSED [ 56%]
    tests/test_suite_baseline.py::...::test_an_ABSENT_baseline_says_UNKNOWN_and_NEVER_implies_nothing_was_failing PASSED [ 60%]
    tests/test_suite_baseline.py::...::test_the_baseline_BLOCK_IS_THE_ONLY_DIFFERENCE_the_prompt_gains PASSED [ 64%]
    tests/test_suite_baseline.py::...::test_it_is_stated_as_INFORMATION_and_not_as_an_ACCUSATION_or_a_CONSTRAINT PASSED [ 68%]
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the test showing a `SAFE TO IGNORE.` verdict produces an IDENTICAL outcome (verdict, disposition, exit code, integration) whether the failing test appears in the baseline or not. QUOTE that assertion; it is the load-bearing property of this plan. Paste a grep or equivalent showing no code path compares the baseline to the post-work set to change an outcome. Paste the ruling comment recorded at the code.
  - Observed evidence: **THE LOAD-BEARING ASSERTION, QUOTED IN FULL.** The releasing verdict in the shipped design is `not-mine` (see the V-04 correction on `SAFE TO IGNORE.`). The test runs the SAME answer three times: once where the baseline CONTAINS the failing id (the claim is corroborated), once where the baseline contains a DIFFERENT id entirely (the claim is contradicted by the evidence), and once where the baseline is ABSENT.

    ```python
    def test_a_not_mine_verdict_is_IDENTICAL_with_and_without_the_id_in_the_baseline(self) -> None:
        answer = {"answer": "not-mine", "reason": "it fails in a file I never touched"}
        corroborated = self._perform(answer, _completed((
            "FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2",)))
        contradicted = self._perform(answer,
            _completed(("FAILED tests/test_something_else.py::T::test_other",)))
        absent = self._perform(answer, R.suite_baseline_absent("no baseline was taken"))

        self.assertTrue(corroborated.release)
        self.assertTrue(
            contradicted.release,
            "A `not-mine` whose id is ABSENT from the baseline MUST still release. Refusing here is "
            "precisely the constraint the maintainer rejected on 2026-09-08.",
        )
        self.assertTrue(absent.release)
        for field in ("answer", "reason", "usable", "integrates", "refuses",
                      "awaits_human_decision", "violation", "recheck_attempts",
                      "recheck_passed", "failing_tests"):
            self.assertEqual(corroborated.record[field], contradicted.record[field], ...)
            self.assertEqual(corroborated.record[field], absent.record[field], ...)
    ```

    `release` is the ONLY field the integration decision reads (`GateAnswerOutcome`'s own docstring), so asserting it True in all three cases IS the assertion that the integration outcome does not move. The ten record fields cover the verdict, its usability, the refusal/integration flags, the human-decision routing, the re-check count and result, and the failing-id list. The property is also asserted SYMMETRICALLY for a refusing answer (`test_a_MINE_verdict_is_also_identical_either_way`), so the baseline cannot rescue a refusal either.

    STRONGER STILL, the exhaustive form: `test_the_ONLY_field_that_differs_is_the_RECORDED_baseline_itself` diffs the two whole records and asserts the differing key set is exactly `{"suite_baseline"}` - the audit field. So the claim is not "these ten fields match" but "every field matches except the record of the baseline itself".

    **NO CODE PATH COMPARES THE BASELINE TO THE POST-WORK SET**, proven structurally rather than by grep, because a grep over prose would be defeated by the very comments that explain the rule. `test_NO_CODE_PATH_compares_the_baseline_to_the_post_work_SET` walks `perform_gate_answer`'s AST, collects every `ast.Name` called `baseline` that appears INSIDE a `gate_answer_question(...)` or `gate_answer_record(...)` call, and asserts there are NO others:

    ```python
    stray = [node.lineno for node in ast.walk(fn)
             if isinstance(node, ast.Name) and node.id == "baseline" and id(node) not in allowed]
    self.assertEqual([], stray,
        "`baseline` is used outside the question/record calls in perform_gate_answer (lines "
        f"{stray}); that is a GATE, which the maintainer forbade")
    ```

    So `baseline` cannot appear in an `if`, in the `release` conjunction, in the `earns_recheck` loop or in the `violation` text without failing this test. A companion (`test_the_baseline_reaches_NO_comparison_in_execute_item_core_either`) asserts the same for the wiring seam, rejecting `if suite_baseline.failures`, `in suite_baseline.failures`, `suite_baseline.failures ==` and `suite_baseline.known and`.

    **THE RULING RECORDED AT THE CODE**, in the producer's header comment in `agent_workflows/runner_shared.py`, with its reasoning so the next reader does not "finish" it into a gate:

    ```
    # WHAT THIS IS FOR, AND THE ONE SENTENCE THAT MUST NOT BE "IMPROVED" AWAY:
    #
    #     THE BASELINE IS INFORMATION FOR AN HONEST AGENT, NOT A CHECK ON A DISHONEST ONE. NOTHING MAY
    #     REFUSE, DOWNGRADE, OR OTHERWISE CHANGE AN OUTCOME ON THE STRENGTH OF IT.
    #
    # THE MAINTAINER RULED THAT EXPLICITLY, 2026-09-08 (recorded on `daexj1` OQ-02 and reaffirmed
    # 2026-09-20): "You cannot build a pre-test that detects deception ... We're mitigating sloppiness,
    # not malice. Asking the agent is 100% the right move." The originally-proposed constraint ("refuse
    # `not-mine` for any failing id ABSENT from the baseline") was rejected IN AS MANY WORDS. Four
    # reasons, and each one independently kills the gate idea:
    #
    #   1. A GATE CANNOT DETECT DECEPTION. It can only detect a MISMATCH between two id sets, and a
    #      mismatch has many innocent causes (a flaky test, a test that only fails under a different
    #      shard order, a new test added by a merge that landed mid-turn).
    #   2. A CAPABLE MODEL CAN MAKE TESTS PASS. Any gate keyed on "is this id in the baseline" is
    #      satisfiable by an agent that simply deletes or skips the test, which is strictly worse than
    #      the sloppiness it was built to catch.
    #   3. A GENUINELY MALICIOUS AGENT WOULD REWRITE THE GATE. It has write access to this file.
    #   4. THE TARGET IS SLOPPINESS, NOT MALICE. An agent that broke something subtly and genuinely
    #      believes the failure is unrelated answers `not-mine` in GOOD FAITH and is WRONG. Telling it
    #      what was already red lets it be RIGHT. That is the whole deliverable.
    ```

    The comment is itself asserted present, phrase by phrase, by `test_THE_RULING_IS_RECORDED_AT_THE_CODE_with_its_reasoning`, so deleting the explanation turns a test red. Parallel notes sit on `perform_gate_answer` (spelling out that `baseline` appears in exactly two places and that the absence IS the ruling in executable form), on `gate_answer_question`, and on `gate_answer_record` ("WRITING IT IS NOT READING IT ... a record is not a check").

    ```
    $ python3 -m pytest "tests/test_suite_baseline.py::NothingRefusesOnTheBaseline" -o addopts="" -v
    tests/test_suite_baseline.py::NothingRefusesOnTheBaseline::test_a_MINE_verdict_is_also_identical_either_way PASSED [ 16%]
    tests/test_suite_baseline.py::NothingRefusesOnTheBaseline::test_a_not_mine_verdict_is_IDENTICAL_with_and_without_the_id_in_the_baseline PASSED [ 33%]
    tests/test_suite_baseline.py::NothingRefusesOnTheBaseline::test_THE_RULING_IS_RECORDED_AT_THE_CODE_with_its_reasoning PASSED [ 50%]
    tests/test_suite_baseline.py::NothingRefusesOnTheBaseline::test_the_baseline_reaches_NO_comparison_in_execute_item_core_either PASSED [ 66%]
    tests/test_suite_baseline.py::NothingRefusesOnTheBaseline::test_the_ONLY_field_that_differs_is_the_RECORDED_baseline_itself PASSED [ 83%]
    tests/test_suite_baseline.py::NothingRefusesOnTheBaseline::test_NO_CODE_PATH_compares_the_baseline_to_the_post_work_SET PASSED [100%]

    ============================== 6 passed in 0.23s ===============================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the persisted record showing all four facts (base commit, failing id set, completion state, absence reason) and show both hosts write the identical shape. Paste an ABSENT case's record and confirm it is distinguishable from a completed baseline that found nothing failing.
  - Observed evidence: **THE PERSISTED RECORD, ALL FOUR FACTS.** Written at `attempt["suite_baseline"]` beside the existing `attempt["suite_check"]`:

    ```json
    {
      "state": "completed",
      "base_commit": "24aa8d413d07edce",
      "failures": [
        "FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2",
        "ERROR tests/test_broken_import.py"
      ],
      "reason": "",
      "summary": "1 failed, 7830 passed, 3 skipped, 2 xfailed in 118.47s",
      "exit_code": 1,
      "elapsed_seconds": 118.5
    }
    ```

    The four the plan requires are `base_commit`, `failures`, `state` and `reason`; `summary`, `exit_code` and `elapsed_seconds` are context. THE COMMIT MATTERS MOST and is present in every shape, because without it a reader cannot tell whether the baseline described the tree the item actually started from (`test_the_COMMIT_is_present_because_without_it_the_record_means_nothing`).

    **THE ABSENT CASE'S RECORD**, and it is DISTINGUISHABLE from a completed-green one:

    ```json
    {
      "state": "absent",
      "base_commit": "",
      "failures": [],
      "reason": "the checkout could not be created",
      "summary": "",
      "exit_code": null,
      "elapsed_seconds": 0.0
    }
    ```

    against a COMPLETED baseline that found nothing failing:

    ```json
    {
      "state": "completed",
      "base_commit": "24aa8d41",
      "failures": [],
      "reason": "",
      "summary": "7830 passed in 104.49s",
      "exit_code": 0,
      "elapsed_seconds": 0.0
    }
    ```

    BOTH carry `"failures": []`, which is exactly why the state is carried by an EXPLICIT VALUE and never by emptiness: `"absent"` versus `"completed"` is the difference between "I do not know what was already red" and "nothing was", and `reason` is non-empty only for the former. A third value, `"not-started"`, distinguishes a turn where no baseline was attempted at all (`test_an_UNSUPPLIED_baseline_records_NOT_STARTED_rather_than_a_green_one`). Asserted by `test_an_ABSENT_record_is_DISTINGUISHABLE_from_a_completed_green_one`. The record is JSON-serializable, checked directly, because it lands in `state.json` and a non-serializable field would kill the turn.

    **BOTH HOSTS WRITE THE IDENTICAL SHAPE, BY CONSTRUCTION RATHER THAN BY CONVENTION.** There is exactly ONE writer, in `runner_shared.execute_item_core`, which both hosts delegate to:

    ```python
    attempt["suite_baseline"] = suite_baseline.as_record()
    ```

    `test_BOTH_HOSTS_write_it_at_the_SAME_SEAM` asserts that line is present in the shared core, that it appears AFTER `attempt["suite_check"]` (so the two facts about one attempt sit together), and - the load-bearing half - that NEITHER host's own source contains `attempt["suite_baseline"]`, since a second writer is precisely how two hosts come to persist different shapes. The three injected names are also asserted to be ONE object on both hosts:

    ```
    $ python3 -c "...; print('oc extract is agy extract:', OC.extract_suite_failures is AGY.extract_suite_failures); print('argv:', AGY.SUITE_CHECK_ARGV)"
    oc extract is agy extract: True
    argv: ('<python>', '-m', 'pytest')
    ```

    A NAME MISSING FROM ONE HOST WOULD HAVE BEEN THE REAL FAILURE MODE HERE, and it is worth naming because it is silent: `execute_item_core` resolves these off `driver_module`, so an `agy` that lacked `extract_suite_failures` would simply have produced NO baseline while `oc` produced one, making an audit's answer depend on which runner executed the plan. That is why the three were re-exported through `agy_runipd`'s existing re-export block rather than left on `oc` alone, and why `test_BOTH_HOSTS_expose_the_SAME_injected_objects` asserts object identity rather than mere presence.

    THE AUDIT PATH IS ALSO CARRIED ON THE ANSWER RECORD (`gate_answer_record`'s `suite_baseline` key), so a reader auditing a released `not-mine` afterwards can ask whether it was well-founded without joining two records (`test_the_gate_answer_record_carries_the_baseline_for_AUDIT`).

    ONE CONSEQUENCE OF THIS RE-EXPORT, disclosed rather than absorbed: it moved the frozen oc->agy import-count baseline in `tests/test_orchestrator_probe_cache.py` from 53 to 56. That test's own docstring prescribes re-measuring and recording a note, which I did, with the attribution COMPUTED rather than assumed (`added: ['SUITE_CHECK_ARGV', 'extract_suite_failures', 'parse_suite_summary']`, `removed: []`, diffed against `24aa8d41`). `tests/test_orchestrator_probe_cache.py` is NOT in this plan's `Scope-Paths`; I declare the edit here. It is a one-line count plus its note, on a test whose stated purpose is to make exactly this kind of increase visible, and the alternative (leaving it red) would have added a second permanently-failing test to the very trust signal this Set exists to protect.

    ```
    $ python3 -m pytest tests/test_suite_baseline.py::TheBaselineIsPersistedIdenticallyOnBothHosts -o addopts="" -v
    tests/test_suite_baseline.py::...::test_the_COMMIT_is_present_because_without_it_the_record_means_nothing PASSED [ 72%]
    tests/test_suite_baseline.py::...::test_an_UNSUPPLIED_baseline_records_NOT_STARTED_rather_than_a_green_one PASSED [ 76%]
    tests/test_suite_baseline.py::...::test_BOTH_HOSTS_write_it_at_the_SAME_SEAM PASSED [ 80%]
    tests/test_suite_baseline.py::...::test_BOTH_HOSTS_expose_the_SAME_injected_objects PASSED [ 84%]
    tests/test_suite_baseline.py::...::test_the_record_is_JSON_SERIALIZABLE PASSED [ 88%]
    tests/test_suite_baseline.py::...::test_the_record_carries_ALL_FOUR_FACTS PASSED [ 92%]
    tests/test_suite_baseline.py::...::test_an_ABSENT_record_is_DISTINGUISHABLE_from_a_completed_green_one PASSED [ 96%]
    tests/test_suite_baseline.py::...::test_the_gate_answer_record_carries_the_baseline_for_AUDIT PASSED [100%]

    ============================== 25 passed in 1.46s ==============================
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the ACTUAL passing output of all seven cases, QUOTING the timeout and creation-failure guards separately as the cases that must not make the runner more fragile, and QUOTING the lane-safety case (g) separately as the case that must not destroy work (F-14). Show the suite invocation is stubbed and no real worktree was created in this repository. THEN paste the BARE `python3 -m pytest` summaries before and after and state the failure-set delta as a set with the counts you observed.
  - Observed evidence: **THE WHOLE MODULE PASSES:**

    ```
    $ python3 -m pytest tests/test_suite_baseline.py -o addopts="" -q
    ....................................................                     [100%]
    52 passed in 1.51s
    $ python3 -m pytest tests/test_suite_baseline.py >/dev/null 2>&1; echo $?
    0
    ```

    THE SEVEN CASES, mapped to the tests that perform them:

    | Case | What it proves | Test |
    |---|---|---|
    | (a) | a baseline completes and its failing set reaches the prompt | `test_a_COMPLETED_baseline_carries_the_failing_ids_and_the_count_line` + `test_the_already_failing_set_REACHES_the_prompt` |
    | (b) | TIMES OUT -> item proceeds with UNKNOWN, not empty | `test_REGRESSION_GUARD_a_TIMED_OUT_baseline_yields_UNKNOWN_and_not_an_empty_set` |
    | (c) | checkout cannot be created -> item unaffected | `test_REGRESSION_GUARD_a_CREATION_FAILURE_leaves_the_item_unaffected` |
    | (d) | a crashed turn leaves NO stray worktree | `test_a_CRASHED_turn_leaves_NO_STRAY_WORKTREE` |
    | (e) | verdict identical with and without the id in the baseline | `test_a_not_mine_verdict_is_IDENTICAL_with_and_without_the_id_in_the_baseline` |
    | (f) | both hosts persist the identical shape | `test_BOTH_HOSTS_write_it_at_the_SAME_SEAM` + `test_BOTH_HOSTS_expose_the_SAME_injected_objects` |
    | (g) | THE LANE-SAFETY CASE | `test_ADVERSARIAL_an_EMPTY_agent_lane_survives_allocation_and_cleanup` + `test_ADVERSARIAL_a_lane_HOLDING_A_COMMIT_gains_no_attempt2_and_no_owner_record` |

    **QUOTED SEPARATELY: THE TWO REGRESSION GUARDS**, cases (b) and (c), because this plan's worst possible outcome is making the runner MORE FRAGILE in exchange for better information:

    ```
    $ python3 -m pytest "...::test_REGRESSION_GUARD_a_TIMED_OUT_baseline_yields_UNKNOWN_and_not_an_empty_set" "...::test_REGRESSION_GUARD_a_CREATION_FAILURE_leaves_the_item_unaffected" -o addopts="" -v
    tests/test_suite_baseline.py::...::test_REGRESSION_GUARD_a_CREATION_FAILURE_leaves_the_item_unaffected PASSED [ 50%]
    tests/test_suite_baseline.py::...::test_REGRESSION_GUARD_a_TIMED_OUT_baseline_yields_UNKNOWN_and_not_an_empty_set PASSED [100%]

    ============================== 2 passed in 0.27s ===============================
    ```

    In BOTH the item completes exactly as it does today: the baseline is recorded ABSENT with a reason, the agent is told UNKNOWN, and nothing fails. The timeout guard additionally asserts the prompt says `UNKNOWN` and does NOT say `NOTHING was failing`, and that the checkout is gone afterwards.

    **QUOTED SEPARATELY: THE LANE-SAFETY CASE (g)**, the one case whose absence would let a work-destroying implementation pass (review measured the naive version deleting an agent's branch, reflog and commits):

    ```
    $ python3 -m pytest tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane -o addopts="" -v
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_ADVERSARIAL_a_lane_HOLDING_A_COMMIT_gains_no_attempt2_and_no_owner_record PASSED [ 16%]
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_ADVERSARIAL_an_EMPTY_agent_lane_survives_allocation_and_cleanup PASSED [ 33%]
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_the_producer_calls_NEITHER_allocate_worktree_NOR_teardown_worktree PASSED [ 50%]
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_the_baseline_path_is_OUTSIDE_the_lane_namespace_by_construction PASSED [ 66%]
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_the_removal_path_can_delete_NO_REF_AT_ALL PASSED [ 83%]
    tests/test_suite_baseline.py::TheBaselineCannotTouchTheAgentsLane::test_the_baseline_NEVER_READS_the_agents_lane PASSED [100%]

    ============================== 6 passed in 0.47s ===============================
    ```

    The measured before/after `git branch`, `git reflog` and `git worktree list` output for this case is pasted in full under V-02.

    **THE SUITE INVOCATION IS STUBBED**, so no 2-3 minute suite runs per case and the module does not depend on this repository being green. The stub is a generated script printing canned pytest-shaped output:

    ```python
    def _fake_suite(root: pathlib.Path, *, stdout: str, exit_code: int = 1) -> list[str]:
        """An argv that prints canned pytest-shaped output. THE STUB that keeps this module free."""
        script = root / "fake_suite.py"
        script.write_text("import sys\n" f"sys.stdout.write({stdout!r})\n"
                          f"raise SystemExit({int(exit_code)})\n", encoding="utf-8")
        return [sys.executable, str(script)]
    ```

    The 52 tests run in 1.51s total, which is itself the proof no real suite ran. `_hanging_suite` (a `while True: sleep`) is the timeout case's stub.

    **NO REAL WORKTREE WAS CREATED IN THIS REPOSITORY.** Every git case builds a throwaway repo via `_throwaway_repo` inside a `tempfile.TemporaryDirectory()`. Verified in this checkout after all fixture cases and after removing my own E-01 scratch clone:

    ```
    $ git worktree list | wc -l
    46
    $ git worktree list | grep -i "suite-baseline\|scratch"
    (no matches)
    $ git branch --list 'aw/lane/*' | wc -l
    82
    ```

    46 worktrees and 82 lane branches, with ZERO entries matching `suite-baseline` or `scratch`. (My E-01 measurement did create a temporary clone-plus-worktree, deliberately under the GITIGNORED `.aw/state/` and inside its OWN clone rather than as a worktree of this repository, and it was removed with `git worktree remove --force` followed by `rm -rf`.)

    **THE BARE SUITE, BEFORE AND AFTER.** Measured myself rather than quoting the plan's stale numbers, exactly as the plan instructs.

    BEFORE (at `24aa8d41`, before any edit):

    ```
    $ python3 -m pytest
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 7830 passed, 3 skipped, 2 xfailed, 3 warnings in 198.60s (0:03:18)
    ```

    AFTER (all edits in place):

    ```
    $ python3 -m pytest
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 7882 passed, 3 skipped, 2 xfailed, 3 warnings in 104.49s (0:01:44)
    ```

    **THE FAILURE-SET DELTA, STATED AS A SET:**

    ```
    BEFORE = {tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped}
    AFTER  = {tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped}

    AFTER - BEFORE = {}    <-- EMPTY, which is the criterion
    BEFORE - AFTER = {}
    ```

    Counts: 1 failed both times; passed 7830 -> 7882, i.e. +52, exactly the size of the new module. Skips and xfails unchanged at 3 and 2.

    THE ONE SURVIVING FAILURE IS ENVIRONMENTAL AND PRE-EXISTING, diagnosed rather than waved away. `test_the_permission_policy_by_contrast_IS_isolation_scoped` asserts at `tests/test_turn_bounds.py:310` that `OPENCODE_CONFIG_CONTENT` is ABSENT from a non-isolated turn's environment, but that env is INHERITED from the parent process and any suite run launched from inside an OpenCode session already exports it (`python3 -c "import os;print('OPENCODE_CONFIG_CONTENT' in os.environ)"` -> `True` here). So it observes the HOST's variable, not one the code under test added. It is present in my BEFORE baseline, in the primary checkout and in a fresh linked worktree alike, and is untouched by this plan. I filed it as backlog **`wx72g3`** (`- Work-Kind: bug`, `- Blocks-Release: next`, per the repository's every-live-bug-gates-the-release rule) rather than leaving it as an unexplained red test.

    AN INTERMEDIATE FAILURE I CAUSED AND FIXED, disclosed rather than hidden: `tests/test_orchestrator_probe_cache.py::BothHostsShareEverySymbol::test_the_oc_to_agy_import_count_did_not_increase` went red on my three re-exports (53 -> 56). That test's own docstring prescribes re-measuring and recording a note with the attribution; I did so with the diff COMPUTED against `24aa8d41`, and it passes. See V-06 for the declared out-of-scope-path edit.

    A SECOND INTERMEDIATE FAILURE I CAUSED AND FIXED, in `tests/test_gate_answer_wiring.py` (also NOT in `Scope-Paths`; declared here). `test_the_release_reaches_BOTH_lane_shapes_from_ONE_site` located both self-finalize arms by an EXACT substring including the `if `/`elif ` keyword. My added `try:`/`finally:` deepened `execute_item_core` by four columns, which pushed the isolated arm past the line limit, and `ruff-format` split it into `if (\n self_finalize\n and work_dir\n ...\n):`. The ORDERING PROPERTY the test exists for was completely intact - the release site still precedes both arms - and only the locator broke. I made the locators formatting-insensitive (collapse whitespace, drop the keyword from the needle, leaving the CONDITION as the locator) and recorded why in its docstring, rather than reverting the structure the plan requires or hand-reflowing code against the repository's own formatter.

    **A THIRD FAILURE, WHICH IS A GENUINE PRODUCTION DEFECT I FOUND AND DID NOT CAUSE.** One bare-suite run reported `tests/test_artifact_audit.py::VerdictParityTests::test_four_verdict_shapes` failing on `assertTrue(loc.location_mismatch)`. I did not accept "flake" as an answer: it passed in isolation, in eight consecutive repeats of its own module, in six seeded orderings, and in five consecutive full bare-suite runs, AND a full bare suite at the pristine base commit (my changes stashed) was clean, which rules my changes out. So I traced it, and it is real.

    `artifact_audit.build_index` memoizes its index in `_INDEX_CACHE` and invalidates on `_dir_signature`, which is the set of record-directory MTIMES (`agent_workflows/artifact_audit.py:726-811`). Directory mtime has finite granularity, so a second artifact created within the SAME TICK as the first is invisible to the signature and the cache returns a STALE index. Reproduced deterministically by pinning the directory mtime back (the tick is what makes the natural case timing-dependent):

    ```
    first lookup found it         : True
    second artifact EXISTS on disk: True
    audit sees it?                : False
    location_mismatch (test wants True): False   <-- reproduces the flake
    ```

    The granularity is real on this filesystem, measured: two successive creations in one directory left `st_mtime_ns` byte-identical (`1789985177747625071` twice). This is a PRODUCTION defect rather than a test defect, because `audit_artifact` backs the finalize/executed-plan audit surfaces, so any caller that writes a record and audits within the same tick can be told a real artifact is missing. Filed as backlog **`8mkt5l`** (`- Work-Kind: bug`, `- Blocks-Release: next`) with the fix shape and an explicit warning NOT to "fix" it by sleeping in the test. It is outside this plan's `Scope-Paths` and I did not touch it.

    ```
    $ python3 -m pytest >/dev/null 2>&1; echo "bare suite exit: $?"
    bare suite exit: 1
    ```

    Exit 1 measured UNPIPED, and it is the single pre-existing environmental failure above; the new module's own exit is 0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION. OQ-01 was RESOLVED AT REVIEW by measurement (the divergence it presupposed is gone; E-01 now owes a re-measurement and a regression test rather than a neutralization layer). OQ-02 remains a measurement question assigned to the executor. OQ-03 is a reporting judgement the record answers either way.

BUT IT DOES CARRY A HARD FUNCTIONAL PREREQUISITE, and an approver should weigh it: the failing-id set this plan exists to hand over DOES NOT EXIST in the code yet, and `daexj1` E-01 is what creates it (F-11). `daexj1` itself currently reads `Readiness: no-go`, though review of this plan confirmed that its `no-go` is stale rather than a size verdict, since its only blocking question (OQ-02) has been resolved by the maintainer. So the honest sequencing is: re-review `daexj1` to clear its readiness, execute it, and only then execute this plan. Approving this plan today is reasonable; executing it before `daexj1` is not possible, and the dependency edge already enforces that.

IT EXISTS BECAUSE THE MAINTAINER ASKED WHETHER THE DECISION NEEDED A SPLIT, and the measurement said yes: `daexj1` already carried ten E-items across eight files and a `no-go` readiness before this capability was added. A reviewer should read the two together: `daexj1` asks the agent, this plan makes the agent's answer accurate, and `daexj1` ships first (`Item-Dependencies: executed:daexj1`).

THE ONE WAY TO GET THIS WRONG IS TO TURN IT INTO A GATE. The maintainer ruled explicitly that no check may refuse on the baseline, on the reasoning that a gate cannot detect deception, a capable model can make tests pass, a malicious agent would rewrite the gate, and the target is sloppiness rather than malice. E-05 and V-05 exist to prove the absence of such a path, and a reviewer should check them first.

THE SECOND WAY IS TO DESTROY THE AGENT'S WORK WHILE MEASURING IT, and it is now the plan's largest hazard because review measured it happening (F-14). Following E-02's ORIGINAL prescription literally (allocate the baseline through `worktree_lease.allocate_worktree` with the item's own id6, then tear it down unconditionally) ADOPTS the agent's own lane at the same path and then deletes its branch, its reflog and its commits. The documented liveness gate does not prevent it, because the driver writes no owner record before that point and the helper treats a same-PID caller as an allowed self-reallocation. E-02 has been rewritten and V-02 now demands an adversarial paste proving the lane survives; a reviewer should check that FIRST, alongside E-05.

THE THIRD WAY IS TO SHIP AN INCOMPARABLE BASELINE, though this hazard has SHRUNK rather than grown (F-12). The plan was built around a linked worktree reporting roughly fifteen phantom failures; re-measured at review, that divergence is GONE (`75 passed` in both, and a full bare suite cleaner in the worktree than in the primary checkout). E-01 is still first, but its expected outcome is now "no neutralization needed", and building a subtraction list from the stale docstring would MASK fifteen real failures rather than remove fifteen phantom ones.

THE FOURTH WAY IS TO BUILD WHAT `daexj1` OWNS (F-11). The failing-id set this plan hands over DOES NOT EXIST in the code today: `SuiteCheckResult` has no such field, the raw output is hashed away at capture, and `daexj1` E-01 is the item that creates the capability. This plan's `Item-Dependencies: executed:daexj1` is therefore a hard functional prerequisite, not an ordering preference, and `run_evidence.py` is deliberately absent from `Scope-Paths` to keep the boundary visible.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. Do NOT run the real suite in a test and do NOT create a real worktree in this repository: at review `git worktree list` showed two live lane worktrees and `git branch --list 'aw/lane/*'` showed 29 branches including four attempt-scoped clusters, and this repository has already lost work to stranded worktrees. Re-locate every symbol by NAME: both driver files are under concurrent edit, and every line anchor this plan carried was off by one to three lines at review HEAD `c170204d` a single day after authoring. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

DO NOT ADD `agent_workflows/run_evidence.py` TO `Scope-Paths`. Its absence is deliberate and is the visible boundary with `daexj1` (F-11). If the work seems to require it, the dependency has not landed and the correct action is to STOP and report, which is a genuinely unsafe-prerequisite condition rather than a scope question.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the not-a-gate identity assertion, the LANE-SURVIVES-THE-BASELINE assertion (F-14), the re-measured divergence, the timeout and creation-failure guards, and the no-stray-worktree proof.
