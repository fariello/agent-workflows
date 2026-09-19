# IPD: Record a host-truncated agy turn as truncated instead of accepting it as a clean exit

- Date: 2026-09-19
- Kind: child
- Concern: THE AGY HOST KILLS THE AGENT'S OWN COMMAND AND THEN REPORTS THE TURN AS `SUCCESS`, AND THE DRIVER BELIEVES THE EXIT CODE. Measured twice on 2026-09-18: the agent issued a plain FOREGROUND `run_command {"CommandLine":"python3 -m pytest"}`, the HOST converted it to a background task, declared `root agent idle; waiting up to 5s for 2 background task(s)`, then `terminating 2 background task(s) on exit`, and closed the turn `{"status":"SUCCESS","duration_seconds":47.46}` with process exit 0. No driver bound fired and none could have (`--print-timeout` `240m`, driver bound 14100s, stall budget 600s, turn 47s, no `turn_bound_expiry`, no `interrupt_reason`, no `turn-bound-expired` event). THE AGENT WAS NOT AT FAULT AND THE EXISTING FIX CANNOT HELP: the FOREGROUND instruction added by `q1z9gn` (`runner_shared.py:10553-10559`) was verbatim in this prompt and was obeyed, because the agent never asked for a background task. So the driver accepts a turn that its own host said it truncated as a normal, complete exit, and scores it from the empty-outcome fallback.
- Scope: Observe the agy host's own truncation lines on the child stdout the driver already reads line by line, classify them host-neutrally, and record a TRUNCATED turn durably on the attempt plus an event - so a turn the host cut is distinguishable from one that finished. Also correct the record in `q1z9gn` and `x7wfyx`, whose premise (the agent chose to background the suite) is measurably wrong for these runs. EXCLUDES changing what the driver DOES about a truncated turn: the retry decision is `dy9ymn`'s, which consumes this signal. EXCLUDES the rescoring fix (`skn8uk` owns it). EXCLUDES any change to `--print-timeout`, `MAX_TURN_TIMEOUT`, `PERMISSION_TIMEOUT` or the stall watchdog: none of them fired and none of them is implicated.
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/agy_runipd.py, tests/test_turn_bounds.py, .aw/records/backlog/open/20260918-x7wfyx-01-x7wfyx-zero-work-turn-retry-and-turn-budget.backlog.md
- Item-Dependencies: none
- Status: to-review
- Set: reaskscore
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: yxfw4k
- Blocks-Release: next
- Work-Kind: bug
- Id: ty7w6o

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `yxfw4k`. The measurement that produced this plan CORRECTS a previously accepted explanation: `q1z9gn` closed on the premise that the agent chose to background its suite, and the session logs show the agent issued a plain foreground command which the HOST backgrounded. Inherits `Blocks-Release: next`.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a host-truncated turn VISIBLE and ATTRIBUTABLE instead of indistinguishable from a clean exit, so
that neither a human reading the run nor the retry logic that follows has to infer from a 47-second
duration that the host killed the work. This plan produces the SIGNAL only; acting on it is `dy9ymn`'s.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: observe and classify the host's own truncation

- [ ] E-01 ADD A HOST-NEUTRAL LINE CLASSIFIER TO `lane_containment.py` THAT RECOGNIZES THE HOST'S TWO OUTCOMES AND DISTINGUISHES THEM, because the same host emits a WAITING line and a CUTTING line and treating them alike would flag healthy turns. Measured across the captured agy sessions: 3 sessions emit `root agent idle; waiting for N background task(s) (bounded by --print-timeout)` and WAIT for the work (healthy); 8 emit `root agent idle; waiting up to 5s for N background task(s)` and then cut (truncating). The classifier must return three outcomes: TRUNCATING (the bounded-wait form, and the `terminating N background task(s) on exit` line), WAITING (the `--print-timeout`-bounded form, which must NOT be reported as truncation), and None for an ordinary line. It MUST live in `lane_containment.py` rather than in the driver: spec `7ckptx` R2.6 requires a rule consumed by a driver to have its single definition in a module the plan declares, and R6.1 forbids the fork where one host becomes the other's de-facto library. Match on a stable SUBSTRING core rather than the full sentence or a digit-exact pattern, since the count and the `5s` bound are host details that may change; document that fragility honestly as `OQ-01`.
  - Depends on: none
  - Expected outcome: `lane_containment` exposes a pure classifier returning TRUNCATING / WAITING / None, with the two measured line forms pinned as fixtures.
  - Execution state: pending

- [ ] E-02 ADD A PER-TURN OBSERVER MODELED EXACTLY ON `MissingInputObserver`, which is the established precedent for this in this file (`lane_containment.py:1846-1871`) and reaches the driver through the loop that already exists. It must accumulate observations for the turn and expose the turn's verdict (was this turn truncated by its host, and how many background tasks were named), and it must NEVER block, raise, or terminate anything: observing is recording. A malformed or unexpected line must be ignored rather than propagating, for the same reason `MissingInputObserver` never kills a turn.
  - Depends on: E-01
  - Expected outcome: a per-turn observer class exists beside `MissingInputObserver`, is constructed per turn, and answers "did the host truncate this turn" from the lines it saw.
  - Execution state: pending

- [ ] E-03 FEED IT FROM THE AGY STDOUT LOOP AT THE SAME SEAM THE EXISTING OBSERVERS USE, `agy_runipd.py:2762-2769`, where `statusline.touch`, `watchdog.touch`, `turn_bounds.note_progress`, `runner_stop.poll_stop` and `missing_input.note_line` are already called for EVERY raw line. Add the call there and nowhere else, independently of `output_mode`, because a signal parsed inside a rendering branch is silently inert under `raw` and `quiet` - a mistake this file already records having made and fixed (see the `y5od1h` E-06 comment at that seam). Note that `agy_runipd.py:2726-2735`'s comment block is grepped by `tests/test_turn_bounds.py:357-368` for the literals `print-timeout`, `EXPECTED TO WIN` and `BACKSTOP`, so do not reflow it.
  - Depends on: E-02
  - Expected outcome: every raw line of an agy turn reaches the observer, under every `output_mode`.
  - Execution state: pending

### Task group 2: record it durably

- [ ] E-04 RECORD THE TRUNCATION ON THE ATTEMPT AND AS AN EVENT, so it survives the run and is readable afterwards rather than only in scrollback. Write a `host_truncation` record onto the attempt (the host's verdict, the classified lines observed, and the background-task count it named) and append a `host-truncated-turn` event carrying `id6`, `attempt` and that verdict. It MUST NOT change the attempt's `exit_code`, `disposition`, or `item["status"]`: this plan produces a signal and `dy9ymn` decides what to do with it, and quietly rewriting a disposition here would make two plans fight over the same field. Print ONE short warning line naming what the host did, because a turn whose work was killed is something the operator should see at the time and not discover later.
  - Depends on: E-03
  - Expected outcome: `state.json` carries `attempt["host_truncation"]` and `events.jsonl` carries `host-truncated-turn` for a truncated turn, and neither appears for a healthy one; the attempt's `exit_code` and the item's status are untouched.
  - Execution state: pending

- [ ] E-05 CORRECT THE WRITTEN RECORD IN THE TWO BACKLOG ITEMS WHOSE PREMISE THIS MEASUREMENT FALSIFIES, because leaving a superseded explanation in the tree is how the next reader re-derives the wrong fix. `q1z9gn` is `done` and its history states the agent "ran python3 -m pytest as a background task"; `x7wfyx` inherits that framing. Append a correction to the LIVE item (`x7wfyx`, via `aw backlog set` so the history entry is tool-written) stating that the agent issued a plain foreground command and the HOST backgrounded and then terminated it, citing the session evidence, and that the FOREGROUND prompt instruction was present and obeyed. DO NOT rewrite `q1z9gn`'s existing history entries: it is terminal, and editing a closed record to match a later finding destroys the provenance of what was believed when. Reference the correction from the live item instead.
  - Depends on: E-01
  - Expected outcome: `x7wfyx` carries a tool-written history entry recording the corrected cause with citations; `q1z9gn`'s existing entries are unmodified.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- THE DRIVER ALREADY READS EVERY LINE, so no new stream, thread, or parser is needed. `agy_runipd.py:2762-2769` iterates `process.stdout` and fans each raw line out to five existing consumers. This plan adds a sixth at the same point.
- `MissingInputObserver` IS THE PRECEDENT, not an invention: host-neutral class in `lane_containment.py` (`:1846`), constructed per turn by the driver adapter (`agy_runipd.py:2709`), fed every line, never blocking. Its docstring states the non-blocking requirement explicitly; follow the same shape.
- THE SHARED-CODE HOME IS A SPEC OBLIGATION ON THE PLAN, NOT A STYLE PREFERENCE. `7ckptx` R2.6 requires the single definition of a driver-consumed containment rule to live in a module the plan DECLARES in scope. `lane_containment.py` is declared here for exactly that reason.
- THE HOST'S `result.status` IS ALREADY PARSED BUT ONLY FOR DISPLAY (`agy_runipd.py:712-719`), and the exit code comes purely from `process.wait()` (`:2894`). So `SUCCESS` on a truncated turn is currently discarded - which is the correct posture (the driver should not believe it) but leaves no hook where the truncation could be noticed. This plan adds that hook without starting to trust `status`.
- `--print-timeout` IS NOT IMPLICATED AND MUST NOT BE TOUCHED. It was `240m` (`agy_runipd.py:536`, `DEFAULT_TIMEOUT`) on a 47-second turn. The overlap comment at `:2726-2735` is test-grepped (`tests/test_turn_bounds.py:357-368`).
- THE ONE-SIDED-GUARD CLASS IS A KNOWN LOCAL DEFECT PATTERN. A rule that exists on one host only has bitten this repository before (cited in `perform_defect_reask`'s own docstring, `runner_shared.py:8913-8916`). Here the ASYMMETRY IS REAL AND JUSTIFIED: these lines are emitted by the agy CLI and opencode emits nothing resembling them, so the CLASSIFIER is host-neutral and shared while only the agy stdout loop feeds it. `OQ-02` records that judgement so a reviewer can challenge it.

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | The agent obeyed the FOREGROUND instruction; the host backgrounded the command anyway. | `run-20260918T193638Z-2963696/sessions/02-zqs0px-attempt-1.jsonl` step 6: `run_command {"CommandLine":"python3 -m pytest"}`, no background parameter. The prompt at `prompts/02-zqs0px-exec-attempt-1.md:75-81` contains the FOREGROUND paragraph verbatim. |
| F-2 | The host, not the driver, ended the turn, and it terminated the agent's work to do so. | Same log: `root agent idle; waiting up to 5s for 2 background task(s)` then `terminating 2 background task(s) on exit` then `{"status":"SUCCESS","duration_seconds":47.46,"num_turns":1}`. |
| F-3 | No driver bound fired, so this is not a timeout and no bound needs changing. | `state.json` attempt 1: `exit_code: 0`, no `turn_bound_expiry`, no `interrupt_reason`, no `stopped`; `events.jsonl` has no `turn-bound-expired` and no `ipd-stalled`. Frozen options: `timeout: 240m`, `stall_timeout: 600.0`. |
| F-4 | The host has TWO behaviors and only one is a truncation, so the classifier must discriminate. | Across captured agy sessions: 3 x `waiting for N background task(s) (bounded by --print-timeout)` (waits), 8 x `waiting up to 5s for N background task(s)` (cuts). |
| F-5 | Reproduced on a second Set in a second run, so it is systematic. | `run-20260918T190723Z-2697256/sessions/02-zz5yxq-attempt-1.jsonl`: same two lines, turn `28.2s`, `status: SUCCESS`, final response "Waiting for baseline test suite to complete." |
| F-6 | `q1z9gn`'s recorded cause is wrong for these runs, which is why E-05 exists. | `.aw/records/backlog/done/20260918-q1z9gn-...backlog.md` history: "zqs0px ran python3 -m pytest as a background task and polled it with schedule". F-1 shows the agent did not request a background task. |
| F-7 | The agent's `schedule` polling is a SYMPTOM, not the cause: it polls because the host has already detached the command. | In the zqs0px log the `manage_task` polls (steps 10-24) all FOLLOW the host's own idle line at line 11, which precedes them. |

## Proposed changes (ordered, validatable)

1. `lane_containment.py`: pure three-way line classifier for the host's truncating and waiting forms (E-01).
2. `lane_containment.py`: per-turn observer modeled on `MissingInputObserver`, non-blocking, accumulating the turn's verdict (E-02).
3. `agy_runipd.py`: construct it per turn and feed it from the existing every-line seam at `:2762-2769`, under every `output_mode` (E-03).
4. `agy_runipd.py`: record `attempt["host_truncation"]`, append `host-truncated-turn`, print one warning; change no disposition (E-04).
5. `.aw/records/backlog/open/...x7wfyx...`: tool-written history correction citing the real cause; leave `q1z9gn` untouched (E-05).
6. `tests/test_turn_bounds.py`: classifier cases from the real captured lines, the waiting-form negative control, the every-line wiring, and the no-disposition-change property.

## Deferred / out of scope (with reason)

- WHAT TO DO ABOUT A TRUNCATED TURN is `dy9ymn`'s, deliberately. Splitting signal from decision keeps this plan's blast radius to "the driver now records a fact it was discarding", which cannot change any item's fate, and leaves the behavior change where it can be reviewed on its own merits.
  - Carrier: dy9ymn
- THE RESCORING FIX is `skn8uk`'s. Note the two are INDEPENDENT rather than sequential: `skn8uk` fixes the scoring for any cause, this fixes the visibility of this cause, and neither needs the other to be correct.
  - Carrier: s0gnha
- NOT TOUCHING `--print-timeout`, `MAX_TURN_TIMEOUT`, `PERMISSION_TIMEOUT`, OR THE STALL WATCHDOG. F-3 shows none fired; changing a bound that did not fire would be a change with no measured basis.
  - Carrier-Declined: A rejected alternative, recorded so it is not re-proposed. No bound fired in any measured run (F-3), so there is nothing pending: changing one would be a change with no evidence behind it.
- NOT MAKING THE DRIVER TRUST THE HOST'S `result.status`. It reported `SUCCESS` for a turn that produced nothing, so it is not a trustworthy success signal, and the current posture of ignoring it is right. This plan reads the host's TRUNCATION admission, which is a different and more reliable claim (the host is reporting what IT did).
  - Carrier-Declined: Nothing to carry: the current posture of ignoring `result.status` is judged CORRECT rather than deferred, since the host reported `SUCCESS` for a turn that produced nothing. No future act is pending.
- NOT REWRITING `q1z9gn`'s HISTORY. It is a terminal record; editing it to match a later finding would destroy the provenance of what was believed at the time. The correction is appended to the live item instead (E-05).
  - Carrier-Declined: Nothing to carry: preserving a terminal record's provenance is a deliberate permanent choice, and the correction itself IS performed by E-05 on the live item.
- NOT ATTEMPTING TO STOP THE HOST BACKGROUNDING THE COMMAND. Whether a prompt, a flag, or a tool-permission setting can prevent the host from detaching a foreground `run_command` is unknown and is `OQ-03`; it is upstream behavior this repository does not control, and a fix that depends on it would be unverifiable here.
  - Carrier: dy9ymn

## Scope check

- Over-scope: none. One shared module, one host driver, one test file, one backlog record. No bound, no disposition, and no predicate is changed.
- Under-scope: the retry decision (`dy9ymn`) and any attempt to prevent the host behavior (`OQ-03`), both excluded with reasons.

## Required tests / validation

`python3 -m pytest`, run BARE, with the actual summary pasted into each `V-*`. New cases belong in
`tests/test_turn_bounds.py`, whose existing class `TestTheAgentIsToldNotToOutliveItsOwnCommands`
(`:853-931`) already documents this incident family; this plan's cases sit beside it and its docstring
should be corrected where it says the agent chose to background (same correction as E-05, in the test
file's own words).

THE FIXTURES MUST BE THE REAL CAPTURED LINES, byte for byte, for both the truncating and the waiting
form. A hand-paraphrased fixture would pass while the shipped classifier missed the real output, which
is the specific way a string-matching guard fails. Copy them into the test as literals (they contain no
machine-identifying data: no paths, no usernames, no session ids) rather than reading the live,
gitignored `.aw/records/runs/` tree, which CI does not have.

## Spec / documentation sync

Spec `7ckptx` R4.1/R4.1c governs agy's permission posture and R4.4 governs the driver-side bounds; this
plan changes NEITHER, so no amendment is required and no `.spec.md` path is declared in `Scope-Paths`.
The plan does add a new host-neutral containment observer to `lane_containment.py`, which R2.6 requires
be a DECLARED module - satisfied. If a reviewer judges that "the driver must record a host-admitted
truncation" deserves to be a stated requirement rather than an implementation detail, that is an
amendment to `7ckptx` R4 and belongs to a plan that declares the spec file; recorded as `OQ-02`.

## Open questions

### OQ-01: Is substring matching on host log lines an acceptable detector, given it can silently stop working?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: YES, with the fragility stated in the code rather than hidden. It is the only available signal: the host communicates this on stdout and nowhere else (no exit code, no structured event, and its `result.status` says `SUCCESS`). The honest failure mode is FAIL-SILENT: if the host rewords the line, detection stops and behavior reverts to exactly today's, which is a degradation to the status quo and not a new hazard - importantly NOT a false positive, which would be the dangerous direction. Two mitigations are required rather than optional: match a stable substring core instead of the whole sentence or a digit-exact pattern, and state the fail-silent property in a comment at the classifier so the next reader knows a silent stop is possible. The alternative detector (infer truncation from a short duration plus a missing outcome) was rejected because it cannot distinguish a host truncation from a legitimately brief turn, and would fire on healthy work.
- Carrier-Declined: Resolved in this plan rather than deferred: the substring detector is adopted with its fail-silent property documented at the classifier, and the rejected alternative is recorded so it is not re-proposed. No future act is pending.

### OQ-02: Should the host-truncation obligation be written into spec `7ckptx` R4?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING: the code change is correct and complete without it, and the spec as written neither requires nor forbids it. Raised because R4.4 already states the driver-side bounds that "terminate the turn regardless of the host's permission decision", and a companion requirement that the driver must also RECORD a host-initiated termination would sit naturally beside it. Deliberately not done here: amending an approved spec is a contract change a reviewer should authorize, and this plan declares no spec file, so amending one would be an undeclared scope violation.
- Carrier: s0gnha

### OQ-03: Can the host be prevented from backgrounding a foreground command at all?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING and deliberately UNRESOLVED, because it concerns upstream behavior this repository does not control and cannot test. Recorded so it is not mistaken for something this plan achieves: after this plan, the host still truncates turns, and the driver merely knows it happened. Any real prevention would need evidence about the agy CLI's own tool configuration that the captured logs do not contain, and a fix built on a guess would be unverifiable. The measured cost of NOT resolving it is bounded by `dy9ymn`'s retry, which is why a retry is the right compensating control rather than a workaround.
- Carrier: dy9ymn


## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `pytest` output showing the classifier returns TRUNCATING for BOTH real truncating lines (`root agent idle; waiting up to 5s for 2 background task(s)` and `terminating 2 background task(s) on exit`), returns WAITING and explicitly NOT truncating for the real waiting line (`root agent idle; waiting for 1 background task(s) (bounded by --print-timeout)`), and returns None for ordinary JSONL event lines and for an empty line. The waiting-form case is the load-bearing negative control: without it the classifier could flag healthy turns.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output showing the observer accumulates a truncation verdict across a sequence of real lines, reports no truncation for a healthy sequence, and NEVER raises: include a case feeding it malformed and empty input and assert it neither raises nor reports truncation.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output proving the observer is fed from the every-line seam and not from a rendering branch: an assertion that the wiring is independent of `output_mode` (demonstrate detection under a non-`clean` mode such as `raw` or `quiet`, which is the specific bug the `y5od1h` comment at that seam records). Plus confirmation that `tests/test_turn_bounds.py:357-368` still passes, since it greps `run_agy_turn`'s source for three literals.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted output showing, for a truncated turn, `attempt["host_truncation"]` present with the host's verdict and the background-task count, and one `host-truncated-turn` event in `events.jsonl`; for a healthy turn, BOTH absent. Must also assert the negative property explicitly: the attempt's `exit_code`, the computed `disposition`, and `item["status"]` are IDENTICAL with and without the truncation record, proving this plan changes no item's fate.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff` of the `x7wfyx` item showing a tool-written history entry recording the corrected cause with its session citation, plus pasted `aw backlog check` reporting conformance, plus pasted `git status --porcelain` or `git log` evidence that `q1z9gn`'s file is UNMODIFIED. Also paste the full bare `python3 -m pytest` summary line for the whole plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is release-blocking (`Blocks-Release: next`, inherited from backlog `yxfw4k`) and must not be
executed before explicit human approval, which `- Status:` records and which no agent may write on the
maintainer's behalf.

EXECUTION CONTRACT. Commit only the files this plan changed, path-scoped (`git commit -m msg -- <path>`),
never `git add -A`/`-a`/bare, and never push. Before every commit run `git diff --cached --name-only` and
`git restore --staged` anything not yours: this is a SHARED CHECKOUT with concurrent workers, and a
failed pre-commit hook can leave paths in the index you never staged, so re-verify after any failed
attempt. Prefer `aw commit <plan> -- <paths>`.

When reporting tests passed, paste the ACTUAL bare `python3 -m pytest` output. Do not add `-n0`, a second
`-q`, or `-p no:randomly`.

NOTE ON THE BACKLOG EDIT (E-05). Use `aw backlog set` so the history entry is tool-written rather than
hand-inserted, and do NOT set the item `done`: `x7wfyx` carries `Blocks-Release: next`, so closing it
would trip the close-legitimacy gate, and its own substance (the retry) is `dy9ymn`'s work and is not
finished by this plan.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` reports conforming and every `V-*` carries concrete pasted evidence.
