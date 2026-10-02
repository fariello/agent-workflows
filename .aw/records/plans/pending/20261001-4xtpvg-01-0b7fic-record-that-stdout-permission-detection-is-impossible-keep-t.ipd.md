# IPD: Record that stdout permission detection is impossible, keep the bound disabled, and amend spec 7ckptx R4.4b and A10c to match the measurement

- Date: 2026-10-01
- Kind: child
- Concern: `lane_containment.TurnBoundWatch.note_permission_request` has ZERO production callers, so `PERMISSION_TIMEOUT` is disabled twice over: by its `0.0` default and by the absence of any trigger. Backlog `4xtpvg` filed that gap and prescribed spec `7ckptx` A10c option (i) (a real provoked ask with the captured stream and the matched line) as the precondition for wiring it. MEASURED IN THIS LANE AT HEAD `ce55ef615`, AND THE PRESCRIPTION IS UNACHIEVABLE: across 788,504 recorded child-stdout events in 2,414 `.aw/records/runs/*/sessions/*.jsonl` streams the complete type census is `step_update`/`tool_use`/`step_start`/`step_finish`/`text`/`error` and the count of events whose type mentions permission, ask, or question is ZERO, while the host log over the same period carries 1,552 `message=asking ... permission=` lines, 1,166 of them on driver turns. A permission ask is a host-internal event that never crosses into the stream the driver reads, so option (i) cannot be satisfied by trying harder and A10c as written offers a branch nobody can walk. Two further measurements decide the product question rather than deferring it: at the spec's own normative 30-second default the bound would have killed 15 of 1,149 HEALTHY turns that went on to emit stdout, and of the 17 asks followed by no further stdout at all, all 17 are already covered by the shipped `StallWatchdog`, so the benefit on this corpus is zero. Finally the cause is GONE: commit `8a491d4c1` landed the R4.1 deny posture in the same change that added this method, and driver-turn permission asks fall from 1,102 before it to 0 across the 640 driver turns since 2026-09-13.
- Scope: Make the current state DOCUMENTED AND DELIBERATE rather than an unexplained dead method. Amend spec `7ckptx` R4.4b and A10c to record that option (i) is unsatisfiable on stdout and that option (ii) is taken permanently rather than provisionally, citing the stream census. Amend `PERMISSION_TIMEOUT`'s and `note_permission_request`'s own documentation to state the measured impossibility, the false-positive bill, the zero benefit, and the residual non-isolated exposure. Add behavioral coverage proving the bound still WORKS when explicitly armed, so "documented as unarmed" never decays into "quietly broken". CHANGES NO RUNTIME BEHAVIOR: `PERMISSION_TIMEOUT` stays `0.0`, no detector is written, no driver line is added, and `note_permission_request` keeps zero production callers BY DECISION. EXCLUDES deleting the mechanism (OQ-01, a maintainer call) and EXCLUDES closing the non-isolated gap (filed as a carrier).
- Scope-Paths: agent_workflows/lane_containment.py, tests/test_permission_bound_disabled.py, .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md, .aw/records/research/20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: 4xtpvg
- From-Spec: 7ckptx
- Set: 4xtpvg
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 0b7fic

## Workflow history

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `4xtpvg`. THE ITEM'S DIAGNOSIS IS EXACTLY RIGHT AND ITS PRESCRIPTION IS IMPOSSIBLE, and establishing that changed this plan from a wiring plan into a recording plan. The item says wiring "REQUIRES spec 7ckptx A10c option (i) first: a REAL provoked permission ask with the captured stream and the matched line". I did not provoke one; I found that the driver has been RECORDING every child's stdout per attempt all along, in `.aw/records/runs/*/sessions/*.jsonl`, and queried 2,414 of those streams (788,504 events, 1.28 GB) against the host log's 1,552 real permission asks. The stream type census is six types and ZERO permission-typed events, so option (i) is unsatisfiable rather than unattempted: there is no line to match and 1,166 driver-turn asks produced 1,166 absences. The item's own closing sentence anticipated this ("the detector may need to tail the log rather than stdout"), so I measured the log route too, and then measured whether it would be WORTH taking. It would not: at the spec's normative 30s default a log-fed bound kills 15 of 1,149 healthy turns, and all 17 genuinely silent asks are already covered by the shipped `StallWatchdog`, so the measured benefit is zero against a measured cost. One further measurement makes the whole question historical: commit `8a491d4c1` added `note_permission_request` and the R4.1 deny posture in the SAME change, and driver-turn asks go 1,102 before it, 19 after, then 0 across 640 driver turns since 2026-09-13. The bound was a backstop for a hole the same commit filled. Full numbers and the five queries in research `7so8uz`.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Leave a reader of `PERMISSION_TIMEOUT` able to tell, from the artifact alone, that its unarmed state
and its callerless trigger are a MEASURED DECISION rather than unfinished work, and leave spec
`7ckptx` A10c no longer offering a branch that cannot be walked. Prove, behaviorally, that the
mechanism still fires when armed, so the decision is "deliberately off" and never "silently broken".

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish the measurement before relying on it

- [ ] E-01 RE-RUN THE FOUR QUERIES AND CONFIRM OR CORRECT THE NUMBERS BEFORE CHANGING ANY ARTIFACT, because every later item cites them and both corpora are MACHINE-LOCAL AND UNCOMMITTED (the host log at `stall_progress.default_log_path()`, the stream corpus at `.aw/records/runs/*/sessions/*.jsonl`), so a different machine or a later date will not reproduce them exactly. Re-derive, as four separate numbers: (a) the complete `type` census over every recorded stdout stream plus the count of events whose type mentions permission/ask/question, which authoring measured as six types and ZERO; (b) the count of `message=asking ... permission=` lines in the log and how many resolve to an `aw-*` root session, authoring measured 1,552 and 1,166; (c) the ask-to-next-stdout-event distribution and the false-positive count at W in {10,30,60,120,300}, authoring measured 15 at the spec's 30s; (d) the count of asks with no later stdout event and how many of those ALSO have no later subagent progress, authoring measured 17 and 17. IF A NUMBER DIFFERS, use the re-measured one and say so in the plan's history: the ARGUMENT is what must survive, not the digits. IF THE CORPORA ARE ABSENT on the executing machine (no log, or a `.aw/records/runs/` with no `sessions/*.jsonl`), this plan's premise cannot be re-established and the honest outcome is to record that and STOP rather than to assert authoring's numbers as if re-measured; say so and leave this item `blocked`.
  - Depends on: none
  - Expected outcome: four re-derived numbers, each with the command that produced it, either confirming authoring's figures or replacing them. No artifact is edited in this item.
  - Execution state: pending

### Task group 2: the code's own documentation

- [ ] E-02 AMEND `PERMISSION_TIMEOUT`'s `#:` DOCUMENTATION BLOCK so it states the IMPOSSIBILITY rather than the hedge. It currently says detection "is UNVERIFIED against a real ask" and that "the detector may be matching a shape that never reaches the stream it inspects", and it ends "Set this to 30 only together with a captured stream from a real provoked ask showing the line the detector matched." That instruction is now known to be unfollowable, so a future reader who tries will waste the same effort this plan spent. Replace the hedge with the measurement: the stream carries six event types and zero permission-typed events over the recorded corpus (cite research `7so8uz` by id6, and give the counts), so the ask is a HOST-INTERNAL event that never reaches stdout; the log DOES carry it (`message=asking ... permission=<class>`); and arming a log-fed bound at the spec's own 30s default would have killed 15 of 1,149 healthy turns while catching nothing the `StallWatchdog` does not already catch. KEEP the existing statement that `MAX_TURN_TIMEOUT` is the only bound covering a permission deadlock, which is still true and is the sentence A10c option (ii) requires the artifact to carry. Do NOT change the value, which stays `0.0`.
  - Depends on: E-01
  - Expected outcome: the constant's documentation states what was measured, names the two reasons arming is refused (no stdout signal; negative cost-benefit on the log route), cites `7so8uz`, and no longer instructs a reader to produce evidence that cannot exist. The value is unchanged.
  - Execution state: pending

- [ ] E-03 STATE ON `note_permission_request` ITSELF THAT HAVING NO CALLER IS THE DECISION, since that method is where a reader meets the gap and the only place a `grep` for the symbol lands. Its docstring currently documents idempotency and says nothing about being unreached. Add that it has no production caller BY DECISION rather than by omission, name the measurement and the research id6, and state the ONE condition that would change the answer: a host whose stdout stream carries a permission-typed event, which this corpus shows opencode's does not. Also state what the method still earns its place by doing, namely keeping the mechanism correct and tested so a future host needs no redesign, and point at the test file E-05 adds. DO NOT write a `TODO`, a `FIXME`, or "not yet wired": each of those asserts that wiring is pending, which is the false claim this item exists to remove.
  - Depends on: E-02
  - Expected outcome: a reader who greps `note_permission_request` learns from the symbol itself that the absence of callers is intentional, what measurement decided it, and what would reopen it, without having to find the spec or the backlog item.
  - Execution state: pending

### Task group 3: the spec contract

- [ ] E-04 AMEND SPEC `7ckptx` R4.4b AND A10c so the contract matches the tree, declaring the spec file in `- Scope-Paths:` as it already is. R4.4b currently requires "The implementing plan MUST either (i) provoke a real permission ask, capture the stream, and paste the matched line, after which the default may be set to 30 seconds; or (ii) record that detection is not possible on stdout, leave the default at `0`, and state that `MAX_TURN_TIMEOUT` is therefore the only bound covering a permission deadlock." Record that option (i) IS NOW MEASURED UNSATISFIABLE on this host (the stream census, the 1,166 driver-turn asks that produced zero stdout events), so option (ii) is TAKEN PERMANENTLY rather than provisionally, and that reopening it needs a host whose stdout carries the event rather than a better-written regex. In A10c, record that its own prohibition on a synthetic line is CORRECT and now moot for the stdout route, and that the criterion is satisfied by the option (ii) branch plus the cost-benefit measurement, naming research `7so8uz` as the recorded finding. ALSO record the TWO facts the spec does not currently carry and that a future reader would otherwise have to rediscover: that the log is the only carrier, and that a log-fed bound was REFUSED ON MEASUREMENT (15 false kills at 30s, zero cases the stall watchdog misses) rather than on caution. Do NOT weaken R4.4's requirement that the driver bound every unattended turn: `MAX_TURN_TIMEOUT` still does that, and this amendment narrows only the permission half's PROSPECTS, not the obligation.
  - THE SPEC EDIT IS THE POINT OF THIS PLAN, NOT A SIDE EFFECT. A plan that amended only the code comment would leave an APPROVED, release-blocking spec (`- Blocks-Release: next`) demanding an implementing plan satisfy a criterion that cannot be satisfied, which is a worse state than the one this plan found: the next executor to read A10c would attempt option (i) again. The spec amendment is why `- Scope-Paths:` names the spec file and why the runners announce a declared spec edit before this plan runs.
  - Depends on: E-01
  - Expected outcome: R4.4b and A10c read as a settled choice with a cited measurement; `aw specs check` conforms; the spec's status is NOT changed by this plan (it stays `approved`, and the `-> implemented` judgement remains the maintainer's, with `uuh71v` already chartered to produce that packet).
  - Execution state: pending

### Task group 4: behavioral coverage, so "off" never decays into "broken"

- [ ] E-05 ADD `tests/test_permission_bound_disabled.py` PROVING THE BOUND IS OFF BY DEFAULT AND CORRECT WHEN ARMED, every assertion driven by EXECUTING `TurnBoundWatch` rather than by reading its source (GUIDING_PRINCIPLES P16; no `inspect`, no `ast`, no `read_text()` of any `agent_workflows/` path). Four behaviors, each a separate test. (a) DEFAULT CONSTRUCTION DOES NOT ARM: a watch built with no `permission_timeout=` argument, with `note_permission_request()` called and a sleep past any plausible window, records ZERO reap calls; assert through the live object rather than by reading the constant, so the default is proven to PROPAGATE. (b) ARMED, IT FIRES: with `permission_timeout` set explicitly and `max_turn_timeout=0`, a noted ask leads to a reap whose recorded bound is `BOUND_PERMISSION`, so the mechanism is demonstrably intact and the decision is "off", not "broken". (c) PROGRESS DISARMS IT: armed, `note_permission_request()` then `note_progress()` then a sleep past the window records ZERO reaps, which is the resettable semantics `TurnBoundWatch`'s docstring calls the whole design. (d) WITHOUT AN OBSERVATION, NOTHING ARMS IT: armed with `permission_timeout` but with `note_permission_request()` NEVER CALLED, a sleep well past the window records ZERO reaps; this is the production state asserted behaviorally, and it is deliberately written so it stays GREEN if someone later wires a caller correctly, since it exercises a watch this test owns rather than counting callers in the tree.
  - TIMING: `TurnBoundWatch.__init__` takes `check_interval` defaulting to `1.0` and its thread loop is `while not self._stop.wait(self.check_interval)`, so an expired bound is noticed AT A POLL TICK, never at the instant it elapses, and the constructor clamps the interval to at most `nearest/4`. For (b), assert `elapsed >= permission_timeout` as the LOWER bound with a generous ceiling above `bound + check_interval`, and state the interval used. A tight upper bound is the most likely way this file arrives flaky under `-n auto`. For the NEGATIVE cases (a), (c), (d) the correct assertion is an empty reap record after a sleep that is a MULTIPLE of the check interval, so the thread provably got ticks in which it could have fired.
  - DO NOT ASSERT THAT `note_permission_request` HAS NO CALLERS. A caller census is the code-structure pin P16 prohibits, and it would turn RED the day someone correctly wires a detector, punishing the right change. The zero-caller fact belongs in E-03's docstring and in the research record, not in an assertion.
  - Depends on: E-01
  - Expected outcome: four passing tests, with (b) demonstrating a real fire and (a)/(c)/(d) demonstrating the three ways it stays silent. Injected reap doubles are acceptable here because the property under test is which bound the watch DECIDES to fire, not that a child dies; a double must keep the `(bound, timeout)` call shape `TurnBoundWatch._run` invokes.
  - Execution state: pending

- [ ] E-06 RECONCILE THE RESEARCH RECORD WITH WHAT THE EXECUTION ACTUALLY FOUND, which is the only part of this plan whose content cannot be written at authoring. AUTHORING ALREADY SET the provenance frontmatter (`consumed-by: [0b7fic]`) and the shelf state (`status: active`, `outcome: answered`, replacing the `todo`/`none-yet` a fresh scaffold writes), so this item does NOT re-do that; it VERIFIES those three fields survived and then does the one thing that needs E-01's result: if E-01 re-measured any figure differently, update the corresponding number in `7so8uz` so the durable record states what was observed on the executing machine rather than what authoring observed on another. Refresh the manifest with `aw research index`. IF E-01 CONFIRMED EVERY FIGURE, say so explicitly and change no number: an unchanged record is the correct outcome, not a skipped item.
  - Depends on: E-01, E-04
  - Expected outcome: `7so8uz` carries `consumed-by: [0b7fic]`, `status: active`, `outcome: answered`, and figures that match E-01's re-measurement; `aw research index --check` reports consistent. The manifest files themselves are GENERATED, GITIGNORED and LOCAL (see `.aw/records/research/README.md`), so they are NOT committed and must not appear in this plan's staged set.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- A test must exercise behavior and never pin code structure or text: no `inspect`, `ast`, regex or substring reads of production source, no caller counts, no docstring pins (`GUIDING_PRINCIPLES.md` Section 16). This bites TWICE in this plan: it forbids asserting the zero-caller fact (E-05's second note) and it is why plan `3vh74b` deliberately did NOT restore the deleted `test_turn_bounds.py` assertions that read `lane_containment`'s own source with `inspect.getfile(...).read_text()`.
- A plan MAY amend a spec and MUST declare the `.spec.md` file in `- Scope-Paths:`, because both runners announce declared spec edits before the run and reconcile them at finalize (`AGENTS.md`, "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT").
- The two constants document themselves with `#:` COMMENT BLOCKS, not string docstrings. Measured by plan `4fodkt`, whose own evidence records that an `ast` probe looking for docstrings "found none, because both constants document themselves with `#:` comment blocks". An executor editing E-02 must edit the comment block above `PERMISSION_TIMEOUT`, and a verifier must read it the same way.
- Both bounds are IN-CODE CONSTANTS WITH NO CONFIG ENTRY AND NO CLI FLAG, by spec R4.4c's KISS ruling, and spec A10e makes that a criterion in the NEGATIVE direction. So this plan must not add a knob, which is a real temptation when documenting a disabled default.
- Research manifests (`INDEX.json`/`INDEX.md`) are generated, gitignored, local views and are never committed; a conflict in a tracked generated manifest once stranded a lane's merge (`.aw/records/research/README.md`).
- The research record's own `status:`/`outcome:` are tool-owned for answer documents; a fresh `aw research new` writes `todo`/`none-yet`, which are wrong for a record that already carries its answer.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | THE DRIVER HAS BEEN RECORDING THE EXACT STREAM A10c ASKS FOR, PER ATTEMPT, FOR MONTHS | `.aw/records/runs/*/sessions/*.jsonl`, 2,414 files, 788,504 JSON events, 1.28 GB. `oc_runipd.run_opencode` writes each line it reads in `for line in process.stdout` to the attempt log, so this corpus IS the stream the detector would inspect. | A10c option (i) never needed a provoked ask. It needed a query nobody had run. This is why the plan can settle the question at authoring instead of scheduling an experiment. |
| F-2 | THE STREAM CARRIES SIX EVENT TYPES AND ZERO PERMISSION EVENTS | Type census: `step_update` 273,961 (carried as `{"event":...}` with no `type` key), `tool_use` 148,886, `step_start` 135,208, `step_finish` 135,049, `text` 94,623, `error` 10. Events whose type mentions permission/ask/question: **0**. The 5,775 lines whose RAW TEXT contains `permission` are all `tool_use` payloads whose own arguments mention the word. | THE CENTRAL FINDING. Option (i) is UNSATISFIABLE, not unattempted. E-02 and E-04 replace the spec's and the code's hedge with this. |
| F-3 | THE ASKS ARE REAL, NUMEROUS, AND IN THE LOG | 1,552 `message=asking ... permission=` lines in a 2,493,369-line log spanning 2026-07-08 to 2026-10-01, plus 2,245 `questions=<N>` lines. 1,166 of the permission asks resolve to a driver turn. Shape: `timestamp=... run=<8hex> message=asking id=per_<id> permission=external_directory patterns="[...]"`. | The absence in F-2 is NOT an absence of asks. It is an absence of asks ON STDOUT, which is a much stronger result: 1,166 real asks produced 1,166 stdout silences. |
| F-4 | ATTRIBUTION ON THE LOG ROUTE IS SOUND AND AVAILABLE BEFORE THE ASK | 917 of 918 `aw-*` root sessions resolve to a `run=` token; for 1,219 of 1,552 asks the token was ALREADY bound to an `aw-*` root EARLIER in the log; ambiguity is **0** (no ask's token bound to two roots, no session id to two tokens); 1,558 of 1,559 recorded streams have a first `sessionID` that resolves to an `aw-*` root `created` line. | A log-fed detector is BUILDABLE and is not refused for lack of attribution. It is refused on F-5 and F-6. Stating this matters: refusing a design for the wrong reason invites someone to "fix" the wrong thing. |
| F-5 | THE SPEC'S OWN 30-SECOND DEFAULT WOULD KILL 15 HEALTHY TURNS | Ask-to-next-stdout-event over 1,149 joined asks: p50 0.025s, p90 0.351s, p95 2.512s, p99 40.106s, max 163.5s. False positives by window: 10s -> 20, **30s -> 15**, 60s -> 7, 120s -> 4, 300s -> 0, 600s -> 0. | R4.4b's stated risk ("a false positive kills a healthy turn") is QUANTIFIED, and the spec's own normative default (R4.4(a), "default 30 SECONDS") is the costly one. A reader tempted to arm at 30 now has the bill. |
| F-6 | THE BENEFIT IS ZERO: ALL 17 CANDIDATE CASES ARE ALREADY COVERED | 17 of 1,166 asks had no later stdout event at all, the only shape a permission bound could usefully kill. Of those 17, the number with later SUBAGENT log progress (which `stall_progress.ProgressPoller` feeds to `StallWatchdog`, resetting it) is **0**, so all 17 are killed by the existing watchdog (`DEFAULT_STALL_TIMEOUT = 900.0`). | Decides the product question. A bound with a measured cost and a measured benefit of zero is not worth arming. CHECKED RATHER THAN ASSUMED: the worry that a chatty deadlocked child defeats the watchdog is real in principle (`stall_progress` measures `evaluated` 4174, `tracking` 2567, `asking` 97 in one slice) but the observer counts a CLOSED ALLOWLIST of `loop`/`process`/`stream`, and that design holds on all 17 real cases. |
| F-7 | THE CAUSE WAS REMOVED IN PRODUCT AND THE ASKS STOPPED | Driver-turn asks per period, isolated vs non-isolated: all time 1,121/45; on or before 2026-09-05 **1,102**/21; after 2026-09-05 **19**/24; after 2026-09-13 **0**/0, across 640 driver turns including 89 on 2026-10-01. Commit `8a491d4c1` (2026-09-05) landed the R4.1 deny posture AND `note_permission_request` in the same change. The four residual isolated asks are all 2026-09-06, all from `run-20260905T211011Z-3780617`, the run executing the `lanectn` Set itself. | The bound was a backstop for a hole the SAME COMMIT filled by denial, which is the stronger fix and the one backlog `qyaime` prescribed. This reframes the item from "finish the wiring" to "record why the wiring is not wanted". |
| F-8 | THE DENY POSTURE IS ISOLATED-TURNS-ONLY, SO A RESIDUAL GAP EXISTS | `oc_runipd.run_opencode` applies `build_permission_policy_env` inside `if work_dir:`, with the in-code rationale "ISOLATED TURNS ONLY, deliberately narrower than the bounds below", because a non-isolated turn legitimately works in the main checkout where an external-directory denial would refuse its ordinary work. 24 of the 45 non-isolated asks postdate the deny posture for exactly this reason. | The one place a future permission deadlock could still arise. Named in E-02's documentation and filed as a carrier rather than fixed here, since changing a non-isolated turn's posture is a behavior change with its own risk profile. |
| F-9 | ANTIGRAVITY HAS NO DENIAL POSTURE AT ALL, PERMANENTLY AND BY DESIGN | `lane_containment`'s R4 header records `ANTIGRAVITY  NO denial posture exists, permanently and by design (R4.1, R4.1c)`, because the only alternative to `--dangerously-skip-permissions` needs interactive permissions an unattended turn cannot answer. That driver constructs `TurnBoundWatch` identically and also calls only `note_progress()`. | The conclusion is NOT host-symmetric and the documentation must not imply it is. On that host containment rests on R1 plus the bounds, and `MAX_TURN_TIMEOUT` is the whole of the bound half. This plan changes nothing there and says so. |
| F-10 | THE MECHANISM ITSELF IS CORRECT AND IS THE ONLY PART WITH NO LIVE COVERAGE TODAY | `TurnBoundWatch._expired` consults `_permission_pending_since`, which only `note_permission_request` sets, and `note_progress` clears it; `BOUND_PERMISSION` is referenced only by its own definition and that one return. Plan `3vh74b` (pending, approved, `From-Backlog: f15tne`) measured ZERO test hits for eleven R4.4 symbols including `note_permission_request`, and would add `tests/test_turn_bounds.py`. | E-05 adds a SEPARATE file for the four disabled-state behaviors rather than editing `tests/test_turn_bounds.py`, which `3vh74b` owns and which does not exist yet. Two plans writing one new file is a collision; two files is not. Stated as a deliberate choice, not an oversight. |

## Proposed changes (ordered, validatable)

1. Re-establish the four measurements on the executing machine before relying on them, and record any
   drift (E-01). This precedes every other item because both corpora are machine-local.
2. Replace `PERMISSION_TIMEOUT`'s hedge with the measurement, including the unfollowable instruction
   it currently ends with (E-02).
3. Say on `note_permission_request` that having no caller is the decision and what would reopen it
   (E-03).
4. Amend spec `7ckptx` R4.4b and A10c so the contract stops demanding an unsatisfiable criterion
   (E-04). This is the plan's point, not a side effect.
5. Add behavioral coverage for the three silent paths and the one firing path, so "off" cannot decay
   into "broken" unnoticed (E-05).
6. Record the research provenance in the direction a reader travels (E-06).

## Deferred / out of scope (with reason)

- DELETING `note_permission_request`, `PERMISSION_TIMEOUT`, `BOUND_PERMISSION` and the
  `_permission_pending_since` half of `TurnBoundWatch`. A real option on GUIDING_PRINCIPLES P6 (no
  mechanism for a hypothetical need) and the honest alternative to this plan's choice, so it is raised
  as OQ-01 rather than buried. NOT DONE HERE because the two readings are both defensible and the
  choice is the maintainer's: the mechanism costs nothing at `0.0`, it is the correct design if any
  host ever emits the event, and E-05 makes it tested rather than merely present. Also note the spec
  constrains the deletion route: A10b requires the constants exist and be named as specified, so
  deleting them needs a spec amendment of its own, which is a larger change than this plan's.
  - Carrier-Declined: nothing is owed unless the maintainer decides to delete. Recorded as OQ-01 with
    both readings stated so the decision is cheap to make later, and the research record carries the
    same alternative in its own recommendation 3.
- CLOSING THE NON-ISOLATED GAP (F-8): a non-isolated unattended turn gets no deny posture and relies
  on `--auto` plus the stall watchdog. A behavior change to a turn class that legitimately works in
  the main checkout, with its own risk profile and its own spec question (R4.1 scopes the posture to
  isolated turns deliberately), so it is not a documentation plan's to make.
  - Carrier: 8ctu3u
  Filed at AUTHORING rather than left for execution, so the gap is tracked whether or not this plan
  runs. It records F-8's measurement (the `if work_dir:` scoping, the in-code rationale, the 24-of-45
  split across the `8a491d4c1` boundary), states why this is residual exposure and not a live hang
  (the stall watchdog covers all 17 corpus cases), and enumerates three options with the reason the
  decision is not obvious: narrowing a non-isolated turn's permissions could refuse that turn's
  ordinary work, which is the worse failure. `qyaime` is `done` and covers the ISOLATED case only, so
  it is not that carrier.
- WIRING A LOG-FED PERMISSION DETECTOR, which F-4 shows is buildable. Refused ON MEASUREMENT, not on
  caution: F-5 prices it at 15 false kills at the spec's own default and F-6 measures its benefit at
  zero, so building it would add a kill path that catches nothing new.
  - Carrier-Declined: DELIBERATELY NOT WANTED on current evidence. The condition that would reopen it
    is recorded in E-02 and E-04 (a host whose stdout carries the event, or a measured case the stall
    watchdog misses), so a future reader can reopen it on evidence rather than rediscovering the
    question.
- RESTORING `tests/test_turn_bounds.py` OR ANY OTHER R4.4 COVERAGE BEYOND THE FOUR DISABLED-STATE
  BEHAVIORS. Owned by plan `3vh74b` (approved, pending) against spec A10/A10b/A10c/A10d.
  - Carrier: 3vh74b
- CHANGING SPEC `7ckptx`'s `- Status:` or recommending its `-> implemented` transition. Owned by plan
  `uuh71v`, which is chartered to produce that evidence packet. This plan amends two requirements and
  leaves the status judgement alone.
  - Carrier: uuh71v

## Scope check

- Over-scope: TWO TEMPTATIONS NAMED. FIRST, an executor who reads F-4 and sees that a log-fed detector
  is buildable may build it; do not, for F-5 and F-6's measured reasons, and note that doing so would
  also invalidate E-05(d), which asserts the production state. SECOND, an executor documenting a
  disabled default may want to make it configurable so an operator can arm it; do not, because spec
  R4.4c's KISS ruling forbids a config entry and a CLI flag for either bound and A10e makes their
  absence a criterion.
- Under-scope: this plan changes NO runtime behavior and closes the backlog item by RECORDING rather
  than by wiring, which is a legitimate outcome but is not what the item's text anticipated, so a
  reviewer should weigh that directly: the item said wiring "REQUIRES" A10c option (i) first, and this
  plan's answer is that option (i) cannot be satisfied and option (ii)'s route is not worth taking. It
  also leaves F-8's non-isolated gap open with a carrier, leaves the delete-versus-keep choice to
  OQ-01, and leaves the broader R4.4 coverage to `3vh74b`.

## Required tests / validation

1. The bare suite, run as `python3 -m pytest`, with its ACTUAL summary line pasted. Bars are by NODE
   ID rather than by total count: no test that passed before may fail after, and the four new tests
   must pass. A raw total is not a bar, because the suite's size drifts between runs on this tree
   (plan `3vh74b`'s review measured a 172-test drift inside two days, both runs fully green).
2. `python3 -m pytest tests/test_permission_bound_disabled.py -v` with every test named and its
   result shown, so each of the four behaviors is individually visible rather than hidden in a total.
3. A MUTATION CHECK proving the new file can FAIL, which is the difference between coverage and the
   appearance of it. With `TurnBoundWatch._expired` stubbed to always return `None`, E-05(b) must FAIL
   while (a), (c) and (d) still PASS, and that SPLIT must be shown: a mutation that reddens all four
   has not isolated the firing path from the silent ones. Mutate via `monkeypatch`/`mock.patch.object`
   in a throwaway process, NEVER by editing `agent_workflows/lane_containment.py`, and paste
   `git status --porcelain` afterwards showing no production file touched. The stub must accept the
   `now` argument (`lambda self, now: None`), since the loop calls `self._expired(time.monotonic())`.
4. A pasted search over the new test file showing ZERO uses of `inspect.getsource`,
   `inspect.getsourcelines`, `inspect.getfile`, `ast.parse`, `ast.walk`, and zero `read_text()`
   against any `agent_workflows/` path (P16).
5. `aw specs check` conforming after the spec amendment.
6. `aw ipd lint --phase pre-transition` conforming.
7. `aw check` reporting no NEW violations relative to a baseline captured before the first edit.
8. `aw sanitize --agent` exiting zero. THIS ONE CARRIES REAL RISK IN THIS PLAN rather than being
   routine: every measurement in it came from a machine-local log under the maintainer's home
   directory and from run records naming lane paths, so a pasted command line or a quoted log line can
   trivially carry a home path, a username, or a session id. Paste a REDACTED form of any log line, and
   note that the leak sanitizer allows exactly `ses_<redacted>` for a session token
   (`stall_progress`'s `_SES_TOKEN` comment records the rule and why its own fixtures use that form).

## Spec / documentation sync

- Spec `7ckptx` IS AMENDED and is declared in `- Scope-Paths:`. R4.4b and A10c change, for the reason
  E-04 states: an approved, release-blocking spec currently requires an implementing plan to satisfy a
  criterion that measurement shows cannot be satisfied, and leaving it standing would send the next
  executor down the same dead end. The amendment NARROWS the permission half's prospects and changes
  no obligation: R4.4's requirement that every unattended turn be bounded is untouched and still met by
  `MAX_TURN_TIMEOUT`. The spec's `- Status:` is NOT changed here.
- `agent_workflows/lane_containment.py` carries the published rationale for both bounds in `#:` comment
  blocks and in `TurnBoundWatch`'s docstring; E-02 and E-03 amend it so the code and the spec say the
  same thing. Spec R4.4's own rule that each bound document WHAT INSTANT it measures from and WHETHER
  ANYTHING RESETS IT must survive the edit: both facts stay.
- Research `7so8uz` is the durable record of the measurement (GUIDING_PRINCIPLES P4) and is declared in
  `- Scope-Paths:` because E-06 edits its `consumed-by:` frontmatter. Its generated manifests are
  gitignored and are NOT committed.
- CHANGELOG: NO entry. Nothing user-visible changes: no behavior, no CLI surface, no output, no
  default value. `ipd_lifecycle._is_implicitly_allowed` does not grant `CHANGELOG.md`, so the path is
  deliberately absent from `- Scope-Paths:` rather than declared and unused.
- `AGENTS.md`, `README.md` and `RELEASING.md`: N/A, none documents either bound.

## Open questions

### OQ-01: Keep the permission-bound mechanism documented-but-unarmed, or delete it outright?

- Blocking: no
- Status: deferred
- Owner: maintainer
- Carrier: e6zeta
- Resolution or deferral rationale: DEFERRED TO THE MAINTAINER AND CARRIED BY BACKLOG `e6zeta`, which
  is filed, so the question survives this plan reaching `executed` instead of vanishing with it. NOT
  RESOLVED AT AUTHORING DELIBERATELY: it is a judgement about standing policy rather than a fact the
  repository can settle, and an agent picking a side here would be making a scope decision that is the
  maintainer's. THE CASE FOR KEEPING, which this plan implements: `TurnBoundWatch` already gets the
  resettable semantics right, the cost at `PERMISSION_TIMEOUT = 0.0` is zero at runtime, E-05 makes it
  tested rather than merely present, and a host whose stream does carry a permission event could arm it
  with no redesign. THE CASE FOR DELETING: GUIDING_PRINCIPLES P6 refuses a mechanism kept for a
  hypothetical need, the trigger has never had a caller since `8a491d4c1` introduced it, and F-7 shows
  the deadlock class was closed by denial instead, so the mechanism is a solution to a problem the
  product solved another way. WHAT MAKES DELETION THE LARGER CHANGE, and the reason this plan does not
  simply pick it: spec A10b requires the constants EXIST and be named `PERMISSION_TIMEOUT` and
  `MAX_TURN_TIMEOUT`, and R4.4(a) specifies the permission bound's own default, so deleting them needs
  its own spec amendment and its own review, where this plan's amendment only narrows two requirements'
  PROSPECTS. If the maintainer prefers deletion, the right shape is a follow-on plan amending A10b and
  R4.4(a) together with the removal, and this plan's documentation and tests make that plan's job
  SMALLER rather than larger, since the state it would delete is by then described and pinned. THIS
  QUESTION IS NON-BLOCKING because the status quo is safe in either direction: a bound at `0.0` cannot
  fire, so nothing is at risk while the decision waits.

### OQ-02: Does the non-isolated residual gap (F-8) warrant its own item, or is it already covered?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AND DISCHARGED AT AUTHORING: it warranted its own item,
  and backlog `8ctu3u` is FILED, so nothing is left for the executor to decide here. The search was
  done rather than deferred: `qyaime` is `done` and its closing history explicitly covers the ISOLATED
  case ("an isolated turn is now ALWAYS a fresh session"), so it is not that carrier, and no other item
  matched. The gap is real and narrow: `oc_runipd.run_opencode` applies the deny posture inside
  `if work_dir:` with the in-code rationale that a non-isolated turn legitimately works in the main
  checkout, and 24 of the 45 non-isolated asks in this corpus postdate the posture for exactly that
  reason. It is DELIBERATE per R4.1, not a defect, which is why the item asks for a maintainer DECISION
  rather than reporting a bug: narrowing a non-isolated turn's permissions could refuse that turn's
  ordinary work, which is the opposite failure and a worse one. `8ctu3u` records the three options and
  notes that the most promising (deny `question` but not `external_directory`) is UNMEASURED, since
  nobody has checked whether a non-isolated turn ever legitimately needs `question`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: FOUR re-derived numbers, each with the exact command that produced it and its real output pasted: (a) the stdout type census plus the permission/ask/question count, which must be ZERO for this plan's premise to hold; (b) the log ask count and the driver-attributable subset; (c) the false-positive table over W in {10,30,60,120,300}; (d) the silent-ask count and how many of those also lack subagent progress. State explicitly, for each, whether it CONFIRMS authoring's figure (0 permission-typed events; 1,552 and 1,166; 15 at 30s; 17 and 17) or REPLACES it, and if any differs, state whether the ARGUMENT still holds. The argument needs (a) to be zero, (c) to be materially above zero, and (d)'s two numbers to be equal.
  - IF (a) IS NOT ZERO, STOP AND REPORT RATHER THAN PROCEEDING. A single permission-typed stdout event refutes this plan's central premise, makes A10c option (i) satisfiable after all, and means the honest next step is the opposite plan (wire the detector). Recording "detection is impossible" while holding evidence that it is possible would be the worst outcome available here, so this is a hard gate and not a caution.
  - IF THE CORPORA ARE ABSENT, paste what was looked for and where, mark this item `blocked`, and do not proceed to E-02 or E-04: an unmeasured premise must not be written into an approved spec.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff` of the `#:` block above `PERMISSION_TIMEOUT` showing (i) the hedging language replaced by the measurement with its counts, (ii) research `7so8uz` cited by id6, (iii) the unfollowable closing instruction ("Set this to 30 only together with a captured stream from a real provoked ask showing the line the detector matched") GONE, (iv) the `MAX_TURN_TIMEOUT`-is-the-only-cover sentence RETAINED, since A10c option (ii) requires the artifact carry it, and (v) the MEASURED-FROM and RESET-BY facts retained, since spec R4.4 requires every bound document both. Paste `python3 -c "import agent_workflows.lane_containment as m; print(m.PERMISSION_TIMEOUT)"` showing `0.0`, so the documentation edit provably did not change the value.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff` of `note_permission_request`'s docstring showing it states the no-caller state is a DECISION, names the measurement and `7so8uz`, and names the condition that would reopen it. Paste a search over the diff showing it introduces no `TODO`, `FIXME`, `XXX`, or "not yet wired", each of which would assert the pending work this item exists to deny. Also paste the live `help()` or `__doc__` of the method as imported, proving the text reaches a reader through the object and not only through the file.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff` of the spec showing BOTH R4.4b and A10c amended, and specifically that (i) option (i) is recorded UNSATISFIABLE with the stream census cited, (ii) option (ii) is recorded as taken permanently rather than provisionally, (iii) the log-route refusal is recorded with its two numbers (the false-positive count at 30s and the zero-benefit result), and (iv) R4.4's obligation that every unattended turn be bounded is UNWEAKENED. Paste `aw specs check` conforming. Paste the spec's `- Status:` line before and after, showing it is UNCHANGED at `approved`, since this plan has no authority over that transition and `uuh71v` owns the packet. Paste the spec's `- Blocks-Release:` line showing it is untouched.
  - A DIFF THAT AMENDS ONLY A10c FAILS THIS ITEM. R4.4b is the requirement that carries the two-option instruction; amending the acceptance criterion while leaving the requirement demanding option (i) would leave the contradiction in place in the normative half, which is the specific defect E-04 exists to remove.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the pasted result of `python3 -m pytest tests/test_permission_bound_disabled.py -v` naming all four tests, PLUS the bare-suite summary line, PLUS the mutation split from required-validation item 3: with `_expired` stubbed to return `None`, test (b) FAILS and (a), (c), (d) PASS, each result pasted, followed by `git status --porcelain` showing no production file touched and no probe left behind. For test (b), state the `check_interval` used and show the observed elapsed time satisfying `elapsed >= permission_timeout` with the generous ceiling, so the poll-tick behavior is accounted for rather than discovered as flakiness. For (a), (c) and (d), paste the reap record as an ACTUAL empty collection and state the sleep used as a multiple of the check interval, so the thread provably had ticks in which it could have fired. Finally paste the P16 search from required-validation item 4.
  - A MUTATION THAT REDDENS ALL FOUR TESTS FAILS THIS ITEM, because it shows the file does not distinguish the firing path from the silent ones, which is the entire distinction it was written to pin.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: THREE parts. FIRST, the research record's frontmatter pasted, showing `consumed-by: [0b7fic]`, `status: active` and `outcome: answered` (set at authoring; this verifies they SURVIVED, and a change is not required). SECOND, an explicit statement of the reconciliation outcome, which is one of exactly two: either name each figure E-01 re-measured differently and paste the corresponding `git diff` of the record, or state that E-01 CONFIRMED every figure and that the record therefore needed no correction. BOTH ANSWERS PASS; what fails is silence about which one happened, since that is indistinguishable from not having checked. THIRD, paste `aw research index --check` reporting consistent, and `git status --porcelain .aw/records/research/` showing the generated `INDEX.json`/`INDEX.md` are NOT staged, since they are gitignored generated views and committing one has previously stranded a lane's merge.
  - IF THE SECOND ANSWER APPLIES, the declared research path is unmodified by this execution and needs a `--scope-ack` at finalize, not an invented edit. See the scope fence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A REVIEWER SHOULD PUSH HARDEST ON, because this plan's whole value rests on one negative claim.
THE CLAIM IS THAT A PERMISSION ASK NEVER REACHES STDOUT, and a negative is exactly the kind of claim
that is wrong when the query was wrong rather than when the world is. So check the QUERY, not the
conclusion: it must cover every recorded stream rather than a sample, it must count events whose
`type` key is ABSENT (273,961 of 788,504 lines are `step_update` records carrying `{"event":...}` with
no `type`, so a census keyed naively on `type` would silently drop a third of the corpus), and it must
be cross-checked against the log over the SAME period so the absence is shown to coincide with 1,166
real asks rather than with a quiet stretch. V-01 demands all three and makes a nonzero count a HARD
STOP, because recording "detection is impossible" while holding evidence that it is possible is the
worst outcome available here.

THE SECOND THING WORTH CHALLENGING is the inference from "the asks stopped on 2026-09-13" (F-7) to
"the deadlock class is closed". The 640 driver turns since then are evidence of a REMOVED CAUSE on ONE
host under ONE configuration, not a proof. Two honest limits are already recorded rather than left for
a reviewer to find: the deny posture is isolated-turns-only (F-8), and antigravity has no denial
posture at all (F-9), so on that host `MAX_TURN_TIMEOUT` is the entire bound half. Neither limit
changes this plan's conclusion, and both belong in the documentation it writes.

Execution contract: commit ONLY the paths named in `- Scope-Paths:`, through
`aw commit <plan> -- <paths>`, never `git add -A` and never push. This is a SHARED CHECKOUT: verify
the staged set with `git diff --cached --name-only` before committing, unstage anything that is not
yours with `git restore --staged <path>`, and re-verify after ANY failed raw commit attempt. Run the
suite BARE as `python3 -m pytest` and PASTE ITS ACTUAL SUMMARY LINE; a summary you did not produce is
not evidence, and the same hard rule governs every pasted census, every mutation result, and every
`git diff` the `V-*` items demand. Do NOT commit the generated research manifests.

LEAK DISCIPLINE IS NOT ROUTINE IN THIS PLAN, it is load-bearing. Every number here was derived from a
machine-local log under the maintainer's home directory and from run records naming absolute lane
paths, so a pasted command, a quoted log line, or a pasted path can carry a home directory, a
username, or a real session id into permanent history. Redact before pasting, use the
`ses_<redacted>` form the leak sanitizer allows for a session token, and run `aw sanitize --agent` to
exit zero before treating any of it as committed.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT (not an instruction to stop). The four
`- Scope-Paths:` entries are the whole surface, and THREE NEGATIVE CONSTRAINTS carry real weight.
FIRST, do NOT change `PERMISSION_TIMEOUT`'s VALUE: it stays `0.0`, and V-02 proves it. SECOND, do NOT
add a config entry or a CLI flag for either bound: spec R4.4c forbids both and A10e makes their
absence a criterion. THIRD, do NOT write a detector, a log tail, or any new driver line: this plan
changes no runtime behavior, and E-05(d) asserts the production state it would invalidate. An
out-of-scope edit that turns out to be necessary is to be MADE and then JUSTIFIED to `aw ipd finalize`
with a `--scope-reason` per path, and a declared-but-unmodified path needs a `--scope-ack`; neither is
a reason to stop.

ONE DECLARED PATH MAY LEGITIMATELY GO UNMODIFIED, and it is named here so the executor reaches for
`--scope-ack` rather than inventing an edit to satisfy the gate. If E-01 confirms every one of
authoring's four figures, E-06's correct outcome is to change NO number in the research record, in
which case `.aw/records/research/20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md`
is declared but unmodified by this execution (its `consumed-by:`, `status:` and `outcome:` were set at
authoring, and V-06 verifies they survived rather than requiring they change). Ack it with the reason
"E-01 confirmed every figure, so the record needed no correction"; do NOT manufacture a cosmetic edit
to make the path look touched, which would be a fabricated justification for a gate that is working.

LIFECYCLE TRANSITION. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence.
Reaching `executed/` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` /
`aw agy run` the RUNNER owns the terminal transition and finalize, so do NOT invoke `aw ipd finalize`
yourself in a runner-driven execution; a HAND execution invokes it
(`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-edit
`- Status:` and never hand-roll a `git mv` into `executed/`, which would skip the pre-transition
checkpoint. Do NOT set backlog `4xtpvg` to `done`: the runner sets `graduated` on verification.
