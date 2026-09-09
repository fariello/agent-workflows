# IPD: Give the adjudicating agent a parallel pre-work suite baseline pinned to its own base commit

- Date: 2026-09-08
- Kind: child
- Concern: THE AGENT IS ASKED A QUESTION IT CANNOT ANSWER ACCURATELY EVEN WHEN PERFECTLY HONEST. Sibling `daexj1` (`integearn` Order 3) stops the runner silently refusing integration over a red suite and instead ASKS the executing agent to adjudicate, with `SAFE TO IGNORE.` meaning the failure is pre-existing noise. But to know a failure is PRE-EXISTING the agent must know the test was already failing before it started, and nothing tells it. MEASURED: `run_suite_check` is called exactly ONCE per attempt, AFTER the work, at `oc_runipd.py:6670` and `agy_runipd.py:3724`, and no prior result is persisted anywhere (`suite_check` appears only at those two write sites plus the re-export at `agy_runipd.py:320`). So a well-meaning agent that broke something subtly, and genuinely believes the failure is unrelated, answers `SAFE TO IGNORE.` in good faith and is WRONG.
  THIS IS INFORMATION, NOT A GATE, AND THE DISTINCTION IS THE WHOLE DESIGN. The maintainer ruled 2026-09-08 (recorded on `daexj1` OQ-02) that no programmatic check may refuse a verdict on the strength of a baseline: "You cannot build a pre-test that detects deception ... We're mitigating sloppiness, not malice. Asking the agent is 100% the right move." The same ruling rejected the originally-proposed constraint ("refuse `SAFE TO IGNORE.` for any id absent from the baseline") explicitly. The baseline exists so an HONEST agent can be RIGHT, not so a dishonest one can be caught.
  A NAIVE IMPLEMENTATION IS MEASURABLY WRONG, WHICH IS WHY THIS IS ITS OWN PLAN. The suite behaves DIFFERENTLY in a linked worktree: `run_suite_check`'s own docstring records why it insists on the primary checkout (`oc_runipd.py:3637-3646`) - a linked worktree resolves `.aw/state` relative to cwd (backlog `dh0uno`), and `tests/test_run_viewer.py` gives `36 passed` in the primary checkout against `15 failed, 20 passed` in a lane, every failure being the state-resolution family. So a worktree baseline reports roughly fifteen PHANTOM failures, and comparing it naively against a primary-checkout post-run result would tell the agent that fifteen tests "were already failing" when they were not.
  AND THE WALL-CLOCK OBJECTION IS ANSWERABLE, WHICH IS WHY IT IS WORTH BUILDING AT ALL. The suite is ~81 seconds (measured at authoring: `5859 passed, 3 skipped, 2 xfailed in 80.96s`) while an execute turn is minutes to hours. Run concurrently with the turn and collected at its end, the added wall-clock is essentially ZERO. The maintainer asked for exactly this and it is the condition on which the baseline was accepted, given their standing objection that rigid gates in this repository "keep biting us in time and money".
- Scope: Produce a pre-work suite baseline for each execute item, computed CONCURRENTLY with the agent turn in its own worktree pinned to that item's own recorded base commit, neutralize the measured worktree divergence so the two results are comparable, and hand the result to the adjudication prompt as CONTEXT. EXCLUDES any refusal, gate, or automatic action keyed on the baseline (the maintainer's ruling forbids it); excludes the adjudication prompt and its verdict handling (`daexj1` owns them); excludes changing `run_suite_check`'s primary-checkout contract.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_suite_baseline.py
- Item-Dependencies: executed:daexj1
- Status: to-review
- Set: integearn
- Order: 5
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Blocks-Release: next
- Id: 9lyg5h

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): SPLIT OUT OF `daexj1` ON THE MAINTAINER'S EXPLICIT INSTRUCTION 2026-09-08, after they asked directly whether the decision needed a replan or a breakup. IT DOES, and the measurement that settled it: `daexj1` already carries TEN E-items across EIGHT files and already reads `Readiness: no-go`, so it was at or past a reviewable unit's capacity before this decision existed. What the decision adds is not a detail but a NEW CAPABILITY: a second checkout created and torn down per item, pinned to a commit, running a suite concurrently with an agent turn, plus neutralizing a measured phantom-failure divergence. `daexj1` contains essentially no concurrency today. THE SEAM IS NATURAL, which is why the split is clean rather than arbitrary: `daexj1`'s value stands alone (asking the agent instead of silently refusing is what fixes the eleven-lane stranding, which cost `03ie04` two executions at `$16.59` then `$32.83`), and this plan only makes the agent's ANSWER more accurate. So `daexj1` can and should ship first, and this declares `Item-Dependencies: executed:daexj1`. CHECKED BEFORE SPLITTING, rather than assumed: `daexj1`'s `no-go` was NOT a size verdict. Its review records `Verdict: REVIEWED - OPEN QUESTIONS` with one advisory `IPD-Z602` density note and no structural error, and the blocking question was OQ-02 itself, which the maintainer has now resolved. So `daexj1` does not need re-cutting on this account; it needs its `no-go` re-examined now that its blocker is answered, which is a review action and not this plan's. THE DESIGN WAS CHOSEN BY THE MAINTAINER FROM FOUR OPTIONS: parallel in its own worktree pinned to the item's own base commit, over pinning to current main (rejected: a mid-turn merge by a human or another agent would make the baseline describe a different tree than the item started from, which was the maintainer's own concern), over sequential-before-the-turn (rejected: a flat 81 seconds added to every item), and over reusing one baseline across items sharing a base (rejected: wrong the moment an item merges and moves the base for later items). ONE COST NAMED AND ACCEPTED: a second checkout plus a full suite run means real disk and CPU concurrent with the agent turn; accepted because wall-clock is unaffected.

## Goal

Let an honest agent answer "was this already failing?" correctly, by telling it what was failing before it started, without adding any gate that could wrongly block work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the two measurements comparable before comparing them

- [ ] E-01 CHARACTERIZE THE WORKTREE DIVERGENCE AND DECIDE HOW TO NEUTRALIZE IT, before building anything that compares two suite results. This is the highest risk in the plan and the reason it exists separately.
  MEASURE IT FIRST, DO NOT TRUST THE CITED NUMBERS. `run_suite_check`'s docstring (`oc_runipd.py:3637-3646`) records `tests/test_run_viewer.py` at `36 passed` in the primary checkout against `15 failed, 20 passed` in a lane, with the cause being `.aw/state` resolving relative to cwd (backlog `dh0uno`). Re-run both today and record the ACTUAL divergent id set: the count and the membership will both have drifted, and a stale subtraction list is worse than none because it would silently mask a real failure.
  DECIDE BETWEEN THE TWO HONEST APPROACHES AND RECORD WHY. Either NEUTRALIZE the cause (make the baseline run resolve the same state root the primary run does, so the two are measured under identical conditions), or SUBTRACT the known-divergent set (cheaper, but it is a hand-maintained list that rots, exactly like the gitignore back-fill list this repository already has). Neutralizing is strictly better if it is achievable; say plainly which you chose and what it costs.
  A THIRD OPTION MAY BE BEST AND MUST BE EVALUATED: run the BASELINE in a way that is comparable BY CONSTRUCTION, for instance by running both the baseline and the post-work check under the same resolution rules rather than making one match the other. Do not assume the primary checkout is the correct reference simply because it is what ships today.
  - Depends on: none
  - Expected outcome: a re-measured divergent id set with today's counts, a recorded choice between neutralizing and subtracting with its reasoning, and an explicit statement of what makes the two results comparable.
  - Execution state: pending

### Task group 2: produce the baseline without slowing the turn

- [ ] E-02 CREATE THE BASELINE WORKTREE PINNED TO THE ITEM'S OWN RECORDED BASE COMMIT, reusing the existing allocation helper rather than shelling out by hand. `worktree_lease.allocate_worktree` already takes `base_commit` (`:554`) and resolves it before use (`:587`), and the base is already recorded per item (`item["preserved_base"]`, `oc_runipd.py:6900`; the handle's `base_commit`).
  PIN TO THE COMMIT, NEVER TO A BRANCH. This is the maintainer's own requirement and the reason the design survives concurrent activity: if a human or another agent merges to main mid-turn, a commit-pinned baseline still describes the tree THIS item started from, which is the only correct before-picture. A branch-pinned baseline would silently describe a different tree.
  DO NOT REUSE THE AGENT'S LANE. The lane is being written by the agent; reading it would sample half-written files. This is a separate, read-only checkout whose only purpose is to run the suite.
  TEAR IT DOWN, AND TEAR IT DOWN ON EVERY PATH. A crashed turn, a stopped run, or a timeout must not leave a stray checkout behind; this repository already has a measured problem with stranded worktrees (eleven found by hand). Use the existing teardown rather than a new one, and make the cleanup unconditional.
  - Depends on: E-01
  - Expected outcome: a read-only baseline worktree per execute item, pinned to that item's recorded base commit via the existing allocation helper, never the agent's lane, torn down on every exit path including crash and timeout.
  - Execution state: pending

- [ ] E-03 RUN THE BASELINE CONCURRENTLY WITH THE AGENT TURN AND COLLECT IT AT TURN END, which is the condition the maintainer accepted this on. Start at dispatch, collect where the post-work `run_suite_check` result is already consumed (`oc_runipd.py:6670`, `agy_runipd.py:3724`).
  IT MUST NEVER DELAY OR FAIL THE TURN. A baseline that has not finished when the turn ends is a MISSING baseline, not a reason to wait indefinitely and not a reason to fail: bound the wait, and on expiry proceed with the baseline absent. Measured at authoring the suite is ~81 seconds against turns of minutes to hours, so expiry should be rare; the bound exists so it cannot become a hang.
  A FAILED BASELINE IS NOT A FAILED ITEM. If the worktree cannot be created, the suite cannot run, or the process dies, record WHY and proceed with no baseline. The agent then answers as it does today, which is the current behavior and therefore not a regression.
  DO NOT INTRODUCE A SECOND CONCURRENCY MODEL. Use whatever the runner already uses for out-of-band work; if it has none, choose the simplest thing that cannot deadlock with the turn, and say what you chose and why. A background suite run that can wedge a driver would be worse than no baseline at all.
  - Depends on: E-02
  - Expected outcome: the baseline computed concurrently with the turn and collected at its end, with a bounded wait, and both a timeout and a hard failure resolving to a RECORDED ABSENT baseline rather than to any delay or failure of the item.
  - Execution state: pending

### Task group 3: hand it over as context, and prove it is not a gate

- [ ] E-04 GIVE THE BASELINE TO THE ADJUDICATION PROMPT AS CONTEXT, in the shape `daexj1` E-05 defines. State plainly to the agent which tests were ALREADY FAILING before its work, and that this is information to help it judge, not an accusation and not a constraint on its answer.
  SAY SO WHEN THE BASELINE IS ABSENT, and never let absence read as "nothing was failing before". That inversion is exactly the defect class `daexj1` E-02 exists to prevent on the other side ("do NOT let a missing or empty list read as success"). An absent baseline must be stated as UNKNOWN.
  DO NOT RESTATE OR RESHAPE `daexj1`'s PROMPT. It owns the three verdict sentinels and the prompt's structure; this item supplies one additional block of context to it. If the prompt's shape makes that awkward, report it rather than editing that plan's design.
  - Depends on: E-03
  - Expected outcome: the adjudication prompt carries the already-failing set as stated context, an absent baseline is stated as UNKNOWN rather than as an empty set, and `daexj1`'s prompt design is unchanged otherwise.
  - Execution state: pending

- [ ] E-05 PROVE, IN CODE AND IN TEST, THAT NOTHING REFUSES ON THE BASELINE. This is the maintainer's binding constraint and the single property a future reader is most likely to erode, because a baseline sitting in the run record LOOKS like something to check.
  NO CODE PATH MAY COMPARE THE BASELINE TO THE POST-WORK SET AND CHANGE AN OUTCOME. Not the verdict, not the disposition, not the exit code, not integration. Assert this rather than merely intending it: a test that a `SAFE TO IGNORE.` verdict is honored IDENTICALLY whether the failing test appears in the baseline or not is the load-bearing assertion of this plan.
  WRITE THE RULING NEXT TO THE CODE, with its reasoning, so the next reader does not "improve" it into a gate: a gate cannot detect deception, a capable model can make tests pass, an actually malicious agent would rewrite the gate, and the target is sloppiness rather than malice. Without that sentence the field reads as an unfinished check.
  - Depends on: E-04
  - Expected outcome: no code path keys any outcome on the baseline, asserted by a test showing an identical verdict outcome with and without the failing id present in the baseline, and the maintainer's ruling recorded at the code.
  - Execution state: pending

### Task group 4: persist it and prove the whole path

- [ ] E-06 RECORD THE BASELINE ON THE RUN RECORD beside the existing per-attempt suite result (`attempt["suite_check"]`, `oc_runipd.py:6671`, `agy_runipd.py:3725`), so an auditor can later ask whether a `SAFE TO IGNORE.` was well-founded even though nothing enforced it at the time.
  RECORD FOUR FACTS: the base commit it was taken at, the failing id set, whether it completed or was absent, and the reason if absent. The commit matters most: without it a reader cannot tell whether the baseline described the tree the item actually started from.
  WRITE IT ON BOTH HOSTS AT THE SAME SEAM, since a field written by one host only would make an audit's answer depend on which runner executed the plan.
  - Depends on: E-05
  - Expected outcome: the baseline's base commit, failing id set, completion state and absence reason all persisted beside the existing suite result, identically on both hosts.
  - Execution state: pending

- [ ] E-07 PROVE THE PATH AND THE THREE CASES THAT MUST NOT HURT ANYTHING, on fixtures. Minimum cases: (a) a baseline completes and its failing set reaches the prompt; (b) the baseline TIMES OUT and the item proceeds with an UNKNOWN baseline, not an empty one; (c) the worktree cannot be created and the item proceeds unaffected; (d) a crashed turn leaves NO stray worktree; (e) the verdict outcome is identical with and without the failing id in the baseline (E-05's assertion); (f) both hosts persist the identical shape.
  CASE (b) AND CASE (c) ARE THE REGRESSION GUARDS. This plan's worst failure mode is making the runner more fragile in exchange for better information, so an item must complete exactly as it does today whenever the baseline is unavailable.
  DO NOT RUN THE REAL SUITE IN A TEST. An 81-second suite per case would make this module unusable and would make the tests depend on the repository being green. Stub the suite invocation the way the existing driver tests stub host calls.
  DO NOT CREATE A REAL WORKTREE IN THIS REPOSITORY. Several lanes and live runs exist concurrently and this repository has already lost work to stranded worktrees; use throwaway repos.
  - Depends on: E-06
  - Expected outcome: six fixture cases passing with timeout and creation-failure shown harmless, no stray worktree after a crash, the with-and-without-baseline verdict identity asserted, no real suite run and no real worktree in this repository.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE POST-WORK SUITE RUNS ONCE, AFTER THE WORK, ON BOTH HOSTS: `oc_runipd.py:6670`, `agy_runipd.py:3724`, inside `if integration_gate_relevant and not validate`. Nothing persists a prior result, so there is no before-picture to reuse.
- `run_suite_check` DELIBERATELY DEMANDS THE PRIMARY CHECKOUT, and its docstring says why (`oc_runipd.py:3637-3646`): a linked worktree resolves `.aw/state` relative to cwd (backlog `dh0uno`), measured as `36 passed` primary against `15 failed, 20 passed` in a lane. Do not "fix" this by pointing it at a worktree; that contract is out of scope.
- IT ALSO FAILS CLOSED BY DESIGN: a suite that cannot run is a FAILURE, with timeout as exit 124 and any other exception as exit 127, neither special-cased into a pass. The BASELINE must NOT inherit that stance, because a missing baseline is an absence of information rather than a failure of the item.
- THE WORKTREE MACHINERY EXISTS: `worktree_lease.allocate_worktree` takes and resolves `base_commit` (`:554`, `:587`), `inspect_lane` (`:258`) reports lane state, and teardown exists. Reuse them; do not shell out to `git worktree` by hand.
- THE BASE COMMIT IS ALREADY RECORDED per item (`item["preserved_base"]`, `oc_runipd.py:6900`), which is what makes commit-pinning cheap.
- THE PER-ATTEMPT RESULT SEAM IS ESTABLISHED: `attempt["suite_check"]` written on both hosts (`oc_runipd.py:6671`, `agy_runipd.py:3725`) beside `attempt["disposition"]` and `attempt["verification"]`.
- STRANDED WORKTREES ARE A MEASURED PROBLEM HERE, not a hypothetical: eleven lanes were found only by a hand audit of `git worktree list`. Unconditional teardown is not optional.
- THE MAINTAINER'S STANDING OBJECTION applies to this plan: rigid programmatic gates in this repository "keep biting us in time and money". The baseline was accepted only as INFORMATION and only because it costs no wall-clock.
- Both driver files are under concurrent edit and their line numbers moved by roughly 70 and 95 lines in a single day. Re-locate every symbol by NAME. The suite runs BARE.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the agent cannot answer honestly-but-correctly | To call a failure pre-existing it must know the prior state; the suite runs once, after the work, and no prior result is persisted. So good-faith misattribution is structurally guaranteed. | `oc_runipd.py:6670`, `agy_runipd.py:3724`; `suite_check` write sites only |
| F-2 | HIGH | **a worktree baseline is measurably wrong if compared naively** | The suite diverges in a linked worktree because `.aw/state` resolves relative to cwd: `36 passed` primary versus `15 failed, 20 passed` in a lane. A naive comparison would report ~15 phantom pre-existing failures. | `run_suite_check` docstring, `oc_runipd.py:3637-3646`; backlog `dh0uno` |
| F-3 | HIGH | the maintainer forbids a gate on this | Ruled 2026-09-08: a gate cannot detect deception, a capable model can make tests pass, a malicious agent would rewrite the gate, and the target is sloppiness. The originally-proposed refusal was rejected explicitly. | `daexj1` OQ-02 resolution |
| F-4 | MEDIUM | wall-clock is answerable, which is why it is buildable | Suite ~81 seconds (`5859 passed, 3 skipped, 2 xfailed in 80.96s`) against turns of minutes to hours, so a concurrent baseline adds essentially nothing. | measured at authoring |
| F-5 | MEDIUM | commit-pinning is required, not tidy | A mid-turn merge by a human or another agent would make a branch-pinned baseline describe a different tree than the item started from. The maintainer raised this case directly. | maintainer, 2026-09-08 |
| F-6 | MEDIUM | the machinery already exists | `allocate_worktree` takes and resolves `base_commit`; the per-item base is already recorded. | `worktree_lease.py:554`, `:587`; `oc_runipd.py:6900` |
| F-7 | MEDIUM | `daexj1` was oversized before this decision | Ten E-items across eight files, and `Readiness: no-go`. Adding a concurrent second checkout would have pushed a plan that already failed review. | `daexj1` metadata |
| F-8 | MEDIUM | but its `no-go` was NOT about size | Its review records `Verdict: REVIEWED - OPEN QUESTIONS`, one advisory density note, no structural error, and the blocking question was OQ-02, now resolved. So `daexj1` needs its readiness re-examined, not re-cutting. | `daexj1` review round 1 |
| F-9 | MEDIUM | absence must not read as an empty set | `daexj1` E-02 exists to stop a missing list reading as success on the other side of this same feature; the same inversion here would tell the agent nothing was failing before. | `daexj1` E-02 |
| F-10 | LOW | stranded worktrees are a real cost here | Eleven lanes were found only by a hand audit. Unconditional teardown is mandatory. | the 2026-09-08 recovery |

## Proposed changes (ordered, validatable)

1. Re-measure the worktree divergence and decide how to make the two results comparable (E-01).
2. Create a read-only baseline worktree pinned to the item's own base commit, with unconditional teardown (E-02).
3. Run it concurrently with the turn, bounded, with timeout and failure both harmless (E-03).
4. Hand the failing set to the adjudication prompt as context, absence stated as UNKNOWN (E-04).
5. Prove nothing refuses on it, and record the ruling at the code (E-05).
6. Persist the base commit, the id set, and the completion state on both hosts (E-06).
7. Prove six cases including the two regression guards, without a real suite run or a real worktree (E-07).

## Deferred / out of scope (with reason)

- ANY GATE, REFUSAL, OR AUTOMATIC ACTION KEYED ON THE BASELINE. Forbidden by the maintainer's 2026-09-08 ruling, which rejected the originally-proposed "refuse `SAFE TO IGNORE.` for any id absent from the baseline" in as many words. E-05 exists to prove the absence of such a path.
- THE ADJUDICATION PROMPT, ITS THREE VERDICT SENTINELS, AND THE VERDICT HANDLING. `daexj1` owns all of it; this plan supplies one context block to it.
- CHANGING `run_suite_check`'s PRIMARY-CHECKOUT CONTRACT. It is deliberate and documented, and altering it would change the post-work check's meaning as well. E-01 must make the two comparable WITHOUT relaxing that contract.
- THE POST-MERGE REVALIDATION RUN. `daexj1` E-03/E-04 own it. This plan adds a THIRD suite run in wall-clock terms only, since it is concurrent.
- REUSING ONE BASELINE ACROSS ITEMS SHARING A BASE COMMIT. Rejected by the maintainer: it is wrong the moment an item merges and moves the base for later items. If a future measurement shows the cost matters, it can be revisited with that hazard stated.
- MAKING THE BASELINE AVAILABLE TO ANY OTHER CONSUMER. It is produced for the adjudication prompt. A second consumer would make it load-bearing, which is a step toward the gate the ruling forbids.
- FIXING THE `.aw/state` cwd-RESOLUTION DEFECT ITSELF (backlog `dh0uno`). It is the CAUSE of F-2 and fixing it would make this plan simpler, but it is a separate item with its own blast radius across every worktree consumer.

## Scope check

- Over-scope: none. One baseline producer, one context block, one persisted record, one test module.
- Scope-Paths justification: `agent_workflows/runner_shared.py` is where the host-neutral baseline producer belongs, beside the other shared runner machinery, so neither host owns a private copy; `agent_workflows/oc_runipd.py` holds the dispatch seam where the baseline starts, the post-work collection point (`:6670`), the per-attempt record (`:6671`), `run_suite_check` and its primary-checkout contract (`:3631`, docstring `:3637-3646`), and the recorded base commit (`:6900`); `agent_workflows/agy_runipd.py` holds the twin seams (`:3724`, `:3725`) so both hosts behave identically; `tests/test_suite_baseline.py` is new because no existing module covers a concurrent out-of-band suite run.
- Under-scope, stated rather than left as `none`: this plan adds no gate and no refusal, does not touch the adjudication prompt or its verdicts, does not change `run_suite_check`'s contract, does not fix the underlying state-resolution defect, does not reuse baselines across items, exposes the baseline to no second consumer, and amends no spec.

## Required tests / validation

- THE RE-MEASURED DIVERGENCE (E-01) pasted with today's actual counts and the divergent id set, not the cited historical numbers, plus the recorded choice between neutralizing and subtracting.
- PROOF THE TWO RESULTS ARE COMPARABLE, stated explicitly: what makes the baseline's conditions equal to the post-work check's. If they are not made equal, the plan has produced misleading information rather than useful information.
- SIX FIXTURE CASES (E-07) each named with pasted output: baseline completes and reaches the prompt; baseline times out and the item proceeds with UNKNOWN; worktree creation fails and the item proceeds; a crashed turn leaves no stray worktree; verdict outcome identical with and without the id in the baseline; both hosts persist an identical shape.
- THE TWO REGRESSION GUARDS QUOTED SEPARATELY (timeout, creation failure), since making the runner more fragile in exchange for information is this plan's worst outcome.
- THE NOT-A-GATE ASSERTION QUOTED (E-05): a test showing a `SAFE TO IGNORE.` verdict is honored identically whether the failing test is in the baseline or not. This is the load-bearing property.
- ABSENCE-IS-NOT-EMPTY PROOF: the prompt text for an absent baseline pasted, showing it says UNKNOWN and not "nothing was failing".
- COMMIT-PINNING PROOF: paste evidence the baseline was taken at the item's recorded base commit, and a case where main MOVED during the turn showing the baseline still describes the original base.
- WALL-CLOCK MEASUREMENT: the added wall-clock for a realistic turn, measured rather than asserted, since the whole design was accepted on that basis.
- NO STRAY WORKTREE: `git worktree list` before and after the fixture cases, identical, including the crash case.
- NO REAL SUITE RUN AND NO REAL WORKTREE IN THIS REPOSITORY: show the suite invocation is stubbed and the fixtures use throwaway repos.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated as a set. Measured on main at authoring: `5859 passed, 3 skipped, 2 xfailed`. Criterion: AFTER minus BEFORE is EMPTY.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw ipd lint --phase pre-transition` conforming, pasted.
- `aw sanitize --agent` clean.

## Spec / documentation sync

NO SPEC PATH IS DECLARED, and the reasoning is that this plan adds INFORMATION to an existing prompt and changes no contract. `daexj1` E-10 already amends spec `25kzda` to carry the narrow named exception the adjudication design requires; the baseline does not widen that exception, because it authorizes nothing new and refuses nothing.

BUT VERIFY THAT, RATHER THAN ASSUMING IT. If `daexj1`'s spec amendment describes WHAT the agent is given when it adjudicates, then adding a baseline changes that description and the spec must be amended in the same change, per the rule that a plan may amend a spec but must declare it. Read `daexj1` E-10's actual amendment text before concluding no spec edit is needed, and if it is needed, add the spec path to `Scope-Paths` and say why.

THE RULING MUST BE RECORDED AT THE CODE, not only in this plan (E-05). The sentence that matters: the baseline is information for an honest agent, not a check on a dishonest one, because a gate cannot detect deception, a capable model can make tests pass, a genuinely malicious agent would rewrite the gate, and the target is sloppiness. A baseline sitting in the run record with no such comment reads as an unfinished check, and the next reader will finish it.

DOCUMENT THE WORKTREE COMPARABILITY DECISION where the next reader will hit it, at the baseline producer. Whichever route E-01 chooses, a future maintainer must be able to tell whether a difference between the two id sets is real or an artifact of where each ran. If the route is a subtraction list, say plainly that it is hand-maintained and will rot.

## Open questions

### OQ-01: Can the baseline be made comparable without relaxing the primary-checkout contract?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: OPEN AND ASSIGNED TO E-01, because it is a measurement question the repository can answer and the answer decides the implementation. `run_suite_check` insists on the primary checkout for a documented reason (a linked worktree resolves `.aw/state` relative to cwd, measured as `36 passed` versus `15 failed, 20 passed`), and this plan must not relax that contract because the post-work check depends on it. So the baseline must be made comparable some OTHER way: by neutralizing the state resolution for the baseline run, by subtracting a re-measured divergent set, or by running both sides under identical rules. Each is achievable and each has a different rot profile, with the subtraction list being the weakest because it is hand-maintained. Non-blocking because E-01 is the first item and the plan cannot proceed past it without an answer, so the question cannot be skipped by accident.

### OQ-02: What is the right bound on waiting for a late baseline?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: OPEN AND MEASURABLE, so it is the executor's. The suite is ~81 seconds and turns are minutes to hours, so a baseline should essentially always be ready first and the bound exists only so a wedged suite cannot hang a driver. What the executor must decide from measurement rather than taste: whether the bound is a fixed timeout, a multiple of the observed suite duration, or simply "whatever is ready at collection time with no wait at all". THE LAST OPTION IS PROBABLY BEST and is worth trying first, because a zero-wait collection cannot delay a turn by construction, which is the property the maintainer accepted this design on. Record what you chose and the measurement behind it.

### OQ-03: Should an absent baseline be surfaced to the operator, or only to the agent?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN, AND GENUINELY THE MAINTAINER'S, because it is a reporting-volume judgement rather than a fact. E-04 requires the AGENT be told UNKNOWN rather than shown an empty set, which is settled. What is not settled is whether a HUMAN should see it. FOR: a `SAFE TO IGNORE.` decided without a baseline is materially weaker than one decided with it, and an operator reading the run summary cannot currently tell those apart. AGAINST: this repository already has several plans in flight adding end-of-run reporting, and one more line that says "the baseline did not finish" on an otherwise successful run is noise most of the time. The middle route is to persist it (E-06 does) and let whoever owns the run summary decide whether to surface it, which costs nothing now and keeps the fact available. Non-blocking because the record is written either way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the re-measured suite results from the primary checkout and from a linked worktree, with today's actual counts and the DIVERGENT ID SET listed, not the historical `36` versus `15 failed, 20 passed`. State which neutralization route you chose and why, and state explicitly what makes the baseline's conditions comparable to the post-work check's. If the route is a hand-maintained subtraction list, say so and say that it will rot.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the worktree creation call showing it uses the existing allocation helper with the item's RECORDED base commit, not a branch name. Paste a case where main moved during the turn and show the baseline still describes the original base. Paste `git worktree list` before and after, including after a simulated crash, showing no stray checkout. Confirm the baseline never reads the agent's lane.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the concurrency mechanism and state why it cannot deadlock with the turn. Paste the measured ADDED WALL-CLOCK for a realistic turn, since the design was accepted on that basis. Paste the timeout case and the hard-failure case, each showing the item completing exactly as it does today with the baseline recorded as absent and a reason.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the prompt text WITH a baseline, showing the already-failing set stated as information rather than accusation. Paste the prompt text WITHOUT one, showing it says UNKNOWN and does NOT imply nothing was failing. Confirm by diff that `daexj1`'s prompt structure and its three verdict sentinels are unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the test showing a `SAFE TO IGNORE.` verdict produces an IDENTICAL outcome (verdict, disposition, exit code, integration) whether the failing test appears in the baseline or not. QUOTE that assertion; it is the load-bearing property of this plan. Paste a grep or equivalent showing no code path compares the baseline to the post-work set to change an outcome. Paste the ruling comment recorded at the code.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the persisted record showing all four facts (base commit, failing id set, completion state, absence reason) and show both hosts write the identical shape. Paste an ABSENT case's record and confirm it is distinguishable from a completed baseline that found nothing failing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the ACTUAL passing output of all six cases, QUOTING the timeout and creation-failure guards separately as the cases that must not make the runner more fragile. Show the suite invocation is stubbed and no real worktree was created in this repository. THEN paste the BARE `python3 -m pytest` summaries before and after and state the failure-set delta as a set with the counts you observed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION. OQ-01 and OQ-02 are measurement questions assigned to the executor and OQ-01 is gated by being E-01, so it cannot be skipped. OQ-03 is a reporting judgement the record answers either way.

IT EXISTS BECAUSE THE MAINTAINER ASKED WHETHER THE DECISION NEEDED A SPLIT, and the measurement said yes: `daexj1` already carried ten E-items across eight files and a `no-go` readiness before this capability was added. A reviewer should read the two together: `daexj1` asks the agent, this plan makes the agent's answer accurate, and `daexj1` ships first (`Item-Dependencies: executed:daexj1`).

THE ONE WAY TO GET THIS WRONG IS TO TURN IT INTO A GATE. The maintainer ruled explicitly that no check may refuse on the baseline, on the reasoning that a gate cannot detect deception, a capable model can make tests pass, a malicious agent would rewrite the gate, and the target is sloppiness rather than malice. E-05 and V-05 exist to prove the absence of such a path, and a reviewer should check them first.

THE SECOND WAY IS TO SHIP AN INCOMPARABLE BASELINE. The suite reports roughly fifteen phantom failures when run from a linked worktree, so a naive implementation would tell the agent those tests were already failing. E-01 is first for that reason and V-01 demands the re-measurement rather than the cited numbers.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. Do NOT run the real suite in a test and do NOT create a real worktree in this repository: several lanes and live runs exist concurrently, and this repository has already lost work to stranded worktrees. Re-locate every symbol by NAME; both driver files are under concurrent edit and their line numbers moved by roughly 70 and 95 lines in a single day. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the not-a-gate identity assertion, the re-measured divergence, the timeout and creation-failure guards, and the no-stray-worktree proof.
