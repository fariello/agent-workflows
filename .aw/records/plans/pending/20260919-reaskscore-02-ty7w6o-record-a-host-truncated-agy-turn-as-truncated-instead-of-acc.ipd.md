# IPD: Record a host-truncated agy turn as truncated instead of accepting it as a clean exit

- Date: 2026-09-19
- Kind: child
- Concern: THE AGY HOST KILLS THE AGENT'S OWN COMMAND AND THEN REPORTS THE TURN AS `SUCCESS`, AND THE DRIVER BELIEVES THE EXIT CODE. Measured twice on 2026-09-18: the agent issued a plain FOREGROUND `run_command {"CommandLine":"python3 -m pytest"}`, the HOST converted it to a background task, declared `root agent idle; waiting up to 5s for 2 background task(s)`, then `terminating 2 background task(s) on exit`, and closed the turn `{"status":"SUCCESS","duration_seconds":47.46}` with process exit 0. No driver bound fired and none could have (`--print-timeout` `240m`, driver bound 14100s, stall budget 600s, turn 47s, no `turn_bound_expiry`, no `interrupt_reason`, no `turn-bound-expired` event). THE AGENT WAS NOT AT FAULT AND THE EXISTING FIX CANNOT HELP: the FOREGROUND instruction added by `q1z9gn` (the shared execute prompt's "Run every command you need the RESULT of in the FOREGROUND and wait for it to finish" paragraph in `runner_shared`; the plan's original `:10553-10559` offset has drifted, so anchor by that sentence) was verbatim in this prompt and was obeyed, because the agent never asked for a background task. So the driver accepts a turn that its own host said it truncated as a normal, complete exit, and scores it from the empty-outcome fallback.
- Scope: Observe the agy host's own truncation lines on the child stdout the driver already reads line by line, classify them host-neutrally, and record a TRUNCATED turn durably on the attempt plus an event - so a turn the host cut is distinguishable from one that finished. Also correct the record in `q1z9gn` and `x7wfyx`, whose premise (the agent chose to background the suite) is measurably wrong for these runs. EXCLUDES changing what the driver DOES about a truncated turn: the retry decision is `dy9ymn`'s, which consumes this signal. EXCLUDES the rescoring fix (`skn8uk` owns it). EXCLUDES any change to `--print-timeout`, `MAX_TURN_TIMEOUT`, `PERMISSION_TIMEOUT` or the stall watchdog: none of them fired and none of them is implicated.
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/agy_runipd.py, tests/test_turn_bounds.py, .aw/records/backlog/open/20260918-x7wfyx-01-x7wfyx-zero-work-turn-retry-and-turn-budget.backlog.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: reaskscore
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: yxfw4k
- Blocks-Release: next
- Work-Kind: bug
- Id: ty7w6o
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-19 approved (aw set): status set to approved

- 2026-09-19 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /askme: OQ-04 RESOLVED BY THE MAINTAINER, clearing this plan's only blocking question and with it its `no-go`. They chose route (a), append the corrected cause to `x7wfyx`'s BODY PROSE as an ordinary tracked edit, on the ground that it asserts ONLY the correction; (b) `set graduated` was declined as a half-true handoff claim (item A, the turn budget, has no plan), and (c) a new `aw backlog note` verb as separate release-blocking work this correction must not wait behind. NO CHECKLIST EDIT WAS NEEDED: E-05 already named (a) as its preferred route and `V-05` already demanded a non-empty `git diff` plus a statement of which route was used, so the answer removed the choice and not the instruction. RE-MEASURED AT RESOLUTION rather than trusted, because the finding is precisely that the command lies about what it wrote: on a throwaway copy the same-status call printed `unchanged` with md5 `03436eff23acf67f690cb026931f0f30` before AND after, `grep -c PROBE` 0, history stuck at 2 lines; the declined (b) was also measured and DOES work (file moves to `graduated/`, history 2 -> 3, `Blocks-Release: next` preserved), so it was declined on what it asserts, not on whether it functions. PR-001 recorded FIXED. The underlying tooling defect stays filed as backlog `x6tk1u` and `hg2oop` (both `open`, high, release-blocking) and is not this plan's to fix. `aw ipd lint --phase review-finalize` now reports `conforming` where it previously reported the expected `IPD-Q501`; `review_findings.subject_gating_blocks` returns `()` where it returned one HIGH/open block, which also cleared sibling `svacmz`'s refused dependency edge. Readiness `no-go` -> `go-pending-approval`; HUMAN APPROVAL IS STILL REQUIRED and no agent may write it.
- 2026-09-19 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001..PR-007, six FIXED, PR-001 escalated as blocking OQ-04; Readiness `no-go` pending that answer. Reviewed at HEAD `9a04b829`; the plan was byte-identical to the sealed lane input and the tree was clean, so no pre-review snapshot. `aw ipd lint --phase author` reported `clean` before the revisions and `--phase review-finalize` reports only the expected `IPD-Q501` (OQ-04 blocking and open) after them. THE SIGNAL-ONLY DESIGN IS RIGHT AND ITS PREMISES CHECK OUT. I verified the stream really does carry the host's diagnostics (`popen_kwargs` merges `stderr` into `stdout`), the every-line seam really does fan out to five consumers under every `output_mode`, `MissingInputObserver` really is the precedent it is described as, the `--print-timeout` grep-pin really does read `run_agy_turn`'s source for its three literals, and `q1z9gn`'s falsified history sentence is quoted verbatim and accurately. TWO ITEMS COULD NOT HAVE BEEN PERFORMED AS WRITTEN. (1) E-05's `aw backlog set` CANNOT append history without a status change, and it FAILS SILENTLY: measured by running the real command against a throwaway copy in a scratch repo, it printed `unchanged`, left the file byte-identical, and dropped the message, because `status_set.apply_status_change` returns early when neither content nor path changed and the history write sits after that return. `aw backlog` has no `note` verb (its spec twin `aw specs note` does exactly this job). An executor would have ticked E-05, passed `aw backlog check`, and written nothing; escalated as blocking OQ-04 with three options. (2) E-04 could not reach the attempt dict from its declared scope: `run_agy_turn` returns a fixed 4-tuple that is TYPED in `execute_item_core`'s signature and shared with the oc twin, and the `attempt` dict is created there, so both obvious routes require `runner_shared.py`, which this plan does not declare. E-04 now names the in-scope route (`item["attempts"][-1]`, verified reachable because the attempt is appended before the spawn) and requires the resulting host asymmetry be commented; the neutral alternative is OQ-05. ALSO FIXED: E-01 had no guard against the classifier firing on an AGENT that merely quotes the host's wording, which is live in this Set because two siblings reproduce those lines verbatim - the host's diagnostics are bare text while every echo arrives inside a JSON envelope, so a JSON-refusal guard separates them, and `root agent idle` was measured to match BOTH line forms and so cannot discriminate. And the cited run directories are absent from the tree, so F-4's 3-vs-8 ratio is unreproducible and is now flagged as a recorded historical measurement rather than something to re-derive. Full record: `.aw/records/reviews/20260919-reaskscore-02-ty7w6o-record-a-host-truncated-agy-turn-as-truncated-instead-of-acc.review.md`.
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
  REFUSE ANY LINE THAT PARSES AS JSON, WHICH IS THE ONE GUARD THAT STOPS A FALSE POSITIVE, and note the original plan had no such guard. The stream this classifier reads is the agy CLI's merged stdout+stderr (`popen_kwargs` sets `stderr=subprocess.STDOUT`, verified at review), and it carries JSONL event envelopes whose payloads contain the AGENT's own assistant text and tool output. So an agent that merely QUOTES these strings would be classified as a host truncation - and that is a live hazard in this very Set, because `dy9ymn` and `svacmz` reproduce the host's lines verbatim in their own text, so an agent executing them may echo them. The host's own diagnostics are BARE TEXT and do NOT parse as JSON, while every agent echo arrives inside a JSON envelope, so requiring `json.loads(line)` to FAIL before classifying separates them exactly. The driver already makes this distinction (`render_agy_event` parses the line and falls through on `json.JSONDecodeError`), so this reuses an established reading of the stream rather than inventing one.
  ORDER THE TWO FORMS SO THEY CANNOT BE CONFUSED. Measured at review against the real line forms: `root agent idle` matches BOTH the truncating and the waiting line and therefore cannot discriminate; the sound discriminators are `waiting up to` (truncating only), `bounded by --print-timeout` (waiting only) and `terminating` (the exit line only). Test the WAITING form before, or independently of, the truncating one, and do not use a shared `root agent idle` prefix as the trigger.
  - Depends on: none
  - Expected outcome: `lane_containment` exposes a pure classifier returning TRUNCATING / WAITING / None, with the two measured line forms pinned as fixtures, which returns None for any JSON-parseable line, and whose discriminators are the three measured-unambiguous substrings rather than the shared `root agent idle` prefix.
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
  THE ROUTE TO THE ATTEMPT DICT IS NOT OBVIOUS AND MUST BE THE ONE NAMED HERE, because the two natural routes both leave this plan's declared scope. Established at review: `run_agy_turn` returns a fixed 4-tuple `(rc, conv_id, log_path, argv)`, and that shape is TYPED IN `runner_shared.execute_item_core`'s own signature (its `spawn_executor` and `spawn_verifier` parameters are `Callable[..., tuple[int, str | None, Path, list[str]]]`) and is shared with the oc twin, so RETURNING the truncation record would require editing `runner_shared.py`, which this plan does NOT declare. Equally, the `attempt` dict itself is CREATED in `execute_item_core`, not here.
  USE THIS ROUTE: mutate `item["attempts"][-1]` from inside `run_agy_turn`. It is reachable and correct - `item` is already a parameter of `run_agy_turn`, and `execute_item_core` appends the attempt to `item["attempts"]` BEFORE it spawns (verified at review: the append precedes the `spawn_executor` call), so during the turn `item["attempts"][-1]` IS this turn's attempt. Several `save_state` calls follow the spawn's return, so the mutation is persisted without adding a call site.
  STATE THE ASYMMETRY HONESTLY IN A COMMENT AT THE WRITE, because this route has a real cost the plan should not hide: `run_agy_turn` today performs NO state writing at all (measured: zero `save_state`, zero `append_jsonl`, zero `item[...]` assignments in its body), so this adds a new responsibility to a launcher that had none, and the oc twin will not have it. That is the one-sided-guard pattern this plan's own conventions section warns about. It is ACCEPTED here for the reason `OQ-02` already gives (only agy emits these lines), and the comment must say so, so a later reader does not "fix" the asymmetry by copying the write into the oc launcher where it can never fire. If a reviewer prefers the host-neutral shape, that means declaring `runner_shared.py` and putting the observer in `execute_item_core`; recorded as `OQ-05`.
  - Depends on: E-03
  - Expected outcome: `state.json` carries `attempt["host_truncation"]` and `events.jsonl` carries `host-truncated-turn` for a truncated turn, and neither appears for a healthy one; the attempt's `exit_code` and the item's status are untouched; the write goes through `item["attempts"][-1]` and the 4-tuple return shape is UNCHANGED, so no edit to `runner_shared.py` is required.
  - Execution state: pending

- [ ] E-05 CORRECT THE WRITTEN RECORD IN THE TWO BACKLOG ITEMS WHOSE PREMISE THIS MEASUREMENT FALSIFIES, because leaving a superseded explanation in the tree is how the next reader re-derives the wrong fix. `q1z9gn` is `done` and its history states, verbatim, "zqs0px ran python3 -m pytest as a background task and polled it with schedule" (quotation verified at review); `x7wfyx` inherits that framing. Record on the LIVE item (`x7wfyx`) that the agent issued a plain foreground command and the HOST backgrounded and then terminated it, citing the session evidence, and that the FOREGROUND prompt instruction was present and obeyed. DO NOT rewrite `q1z9gn`'s existing history entries: it is terminal, and editing a closed record to match a later finding destroys the provenance of what was believed when. Reference the correction from the live item instead.
  `aw backlog set` CANNOT DO THIS AND WILL SILENTLY DROP YOUR MESSAGE, which the plan asserted before review and which is FALSE. MEASURED at review by running the real command against a throwaway copy of the item in a scratch repo: `aw backlog set open x7wfyx --message "..."` printed `unchanged`, the file was BYTE-IDENTICAL afterwards, and the message did not appear anywhere in it. The cause is structural, not a flag: `status_set.apply_status_change` computes `content_changed`/`path_changed` and RETURNS EARLY when both are false, and the `## Workflow history` write sits AFTER that early return, so a same-status call cannot append history by construction. There is no `--force`, and `aw backlog` offers only `new|set|check` - the verb that does exactly what this item wants, `aw specs note` ("Append a workflow-history record to a spec WITHOUT changing its status"), exists for specs and HAS NO BACKLOG TWIN. So an executor following the original instruction would report E-05 done, `aw backlog check` would pass, and NOTHING would have been written.
  USE ONE OF THESE INSTEAD, and say which you used in `V-05`. (a) PREFERRED: append the correction to the item's BODY prose (not its history section) with a hand edit, which is an ordinary tracked file edit of a path this plan already declares, and note in the edit that it is a review-time correction rather than a status transition. (b) If the maintainer would rather the item MOVE, `aw backlog set graduated x7wfyx --message "..."` DOES write history because the status genuinely changes - but do NOT choose this unilaterally: `graduated` asserts the design is handed off, and while `dy9ymn` arguably is that handoff for item B, item A (the turn budget) has no plan at all, so the claim would be half true. That judgement is `OQ-04`. (c) Add a `note` verb to `aw backlog` mirroring `aw specs note`: correct in the long run, out of scope here, and recorded as `OQ-04` too.
  - Depends on: E-01
  - Expected outcome: `x7wfyx` carries the corrected cause with its session citation, written by a route that DEMONSTRABLY changes the file (verified by `git diff`, not by a command's exit code); `q1z9gn`'s existing entries are unmodified; and if route (a) was used, no status transition was fabricated.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- THE DRIVER ALREADY READS EVERY LINE, so no new stream, thread, or parser is needed. `agy_runipd.py:2762-2769` iterates `process.stdout` and fans each raw line out to five existing consumers. This plan adds a sixth at the same point.
- `MissingInputObserver` IS THE PRECEDENT, not an invention: host-neutral class in `lane_containment.py` (`:1846`, verified accurate), constructed per turn by the driver adapter as `lane_containment.MissingInputObserver(state["repo"])` inside `run_agy_turn` just above the stdout loop, fed every line via `note_line`, never blocking. Its docstring states the non-blocking requirement explicitly ("IT DOES NOT BLOCK THE WORKER"); follow the same shape. NOTE the plan's original citation of `agy_runipd.py:2709` for that construction is WRONG (that line is `_raise_if_forced`); anchor by symbol.
- THE STREAM CARRIES BOTH FDS AND BOTH THE HOST'S AND THE AGENT'S WORDS. `popen_kwargs` sets `stdout=subprocess.PIPE` with `stderr=subprocess.STDOUT`, so the loop sees the host's bare-text diagnostics AND every JSONL event envelope, whose payloads include the agent's assistant text and tool output. That is why E-01's JSON-refusal guard is required rather than defensive.
- THE SHARED-CODE HOME IS A SPEC OBLIGATION ON THE PLAN, NOT A STYLE PREFERENCE. `7ckptx` R2.6 requires the single definition of a driver-consumed containment rule to live in a module the plan DECLARES in scope. `lane_containment.py` is declared here for exactly that reason.
- THE HOST'S `result.status` IS ALREADY PARSED BUT ONLY FOR DISPLAY (`agy_runipd.py:712-719`), and the exit code comes purely from `process.wait()` (`:2894`). So `SUCCESS` on a truncated turn is currently discarded - which is the correct posture (the driver should not believe it) but leaves no hook where the truncation could be noticed. This plan adds that hook without starting to trust `status`.
- `--print-timeout` IS NOT IMPLICATED AND MUST NOT BE TOUCHED. It was `240m` (`agy_runipd.py:536`, `DEFAULT_TIMEOUT`) on a 47-second turn. The overlap comment at `:2726-2735` is test-grepped (`tests/test_turn_bounds.py:357-368`).
- THE ONE-SIDED-GUARD CLASS IS A KNOWN LOCAL DEFECT PATTERN. A rule that exists on one host only has bitten this repository before (see `runner_shared.perform_defect_reask`'s own docstring; the plan's original `:8913-8916` offset has drifted, so anchor by symbol). Here the ASYMMETRY IS REAL AND JUSTIFIED: these lines are emitted by the agy CLI and opencode emits nothing resembling them, so the CLASSIFIER is host-neutral and shared while only the agy stdout loop feeds it. `OQ-02` records that judgement so a reviewer can challenge it, and E-04 requires the asymmetry be stated in a comment at the write site so nobody "fixes" it by copying the write into the oc launcher where it can never fire.
- THE TWO `runner_shared.py` LINE CITATIONS IN THIS PLAN HAVE DRIFTED and must be re-derived by symbol; every `agy_runipd.py`, `lane_containment.py` and `tests/` citation was verified accurate at review, EXCEPT `agy_runipd.py:2709` (see the `MissingInputObserver` note above). `runner_shared.py` grew after this plan was authored, which is why only its offsets moved. None is out of range, so none announces itself.
- `run_agy_turn` RETURNS A FIXED 4-TUPLE `(rc, conv_id, log_path, argv)` and that shape is typed in `runner_shared.execute_item_core`'s `spawn_executor`/`spawn_verifier` parameters and shared with the oc twin, so the truncation record CANNOT be returned without editing a file this plan does not declare. E-04 names the route that stays in scope.

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

1. `lane_containment.py`: pure three-way line classifier for the host's truncating and waiting forms, refusing any JSON-parseable line and discriminating on `waiting up to` / `bounded by --print-timeout` / `terminating` rather than the shared `root agent idle` prefix (E-01).
2. `lane_containment.py`: per-turn observer modeled on `MissingInputObserver`, non-blocking, accumulating the turn's verdict (E-02).
3. `agy_runipd.py`: construct it per turn beside the `MissingInputObserver` construction and feed it from the existing every-line seam, under every `output_mode` (E-03).
4. `agy_runipd.py`: record the truncation onto `item["attempts"][-1]` (NOT via the 4-tuple return, which is a cross-host contract), append `host-truncated-turn`, print one warning, comment the deliberate host asymmetry; change no disposition (E-04).
5. `.aw/records/backlog/open/...x7wfyx...`: the corrected cause written by whichever route `OQ-04` settles, proven by a non-empty `git diff`; leave `q1z9gn` untouched (E-05).
6. `tests/test_turn_bounds.py`: classifier cases from the real captured lines, the waiting-form and agent-echo negative controls, the every-line wiring, and the no-disposition-change property; and correct the `TestTheAgentIsToldNotToOutliveItsOwnCommands` docstring, which states the falsified premise in two places ("started `python3 -m pytest` as a BACKGROUND task" and "the agent chose to stop").

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
- Under-scope: the retry decision (`dy9ymn`), any attempt to prevent the host behavior (`OQ-03`), the host-neutral placement of the truncation write (`OQ-05`), and a `note` verb for `aw backlog` (`OQ-04` option c), each excluded with reasons.
- Scope fence: the four declared `- Scope-Paths:` are the whole intended surface. Do not expand it casually; if the work genuinely requires a file outside the fence, MAKE the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path). ONE FILE IS SPECIFICALLY FENCED OUT and review found the plan structurally pulled toward it: `agent_workflows/runner_shared.py`. Both of the obvious routes for E-04 (widening `run_agy_turn`'s return tuple, or creating the observer where the `attempt` dict is created) land there, which is why E-04 names the `item["attempts"][-1]` route that does not. Editing it would also collide with `skn8uk` and `dy9ymn`, which both declare it.

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

WHERE TO GET THOSE LITERALS, since the obvious source is gone. Confirmed at review: `.aw/records/runs/`
is EMPTY in a lane worktree and a fresh clone, so neither cited run directory exists and F-1, F-2, F-4,
F-5 and F-7 CANNOT be re-verified from the tree. The three line forms survive in exactly two tracked
places - this plan's own Concern, E-01 and V-01, and the existing
`TestTheAgentIsToldNotToOutliveItsOwnCommands` docstring (which carries `terminating 2 background
task(s) on exit`) - so copy them from here, and treat this plan as the provenance record for them. TWO
CONSEQUENCES FOLLOW AND ARE STATED RATHER THAN LEFT TO BE DISCOVERED. First, F-4's ratio (3 waiting
sessions against 8 truncating ones) is the evidence the whole classifier design rests on and it is NOT
reproducible; an executor must take it as a recorded historical measurement, not re-derive it, and must
not weaken the WAITING branch on the grounds that it cannot find an example. Second, because the plan is
now the only in-tree source of the strings, do not "tidy" them here.

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

### OQ-04: How should the `x7wfyx` correction be written, given `aw backlog set` cannot append history without a status change?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-19 (`/askme`): OPTION (a), APPEND THE CORRECTION TO THE ITEM'S BODY PROSE as an ordinary tracked edit. The reason they gave is that it is the route which asserts ONLY the correction: it records the measured cause without claiming anything else about the item's state. Option (b) was declined because `graduated` would assert a design handoff that is only half true (item A, the turn budget, has no plan at all), and option (c) because adding a `note` verb is separate release-blocking work this correction must not wait behind. E-05 ALREADY NAMES (a) AS ITS PREFERRED ROUTE, so this answer requires NO edit to the checklist: it removes the choice, not the instruction, and `V-05` still demands the route be named and proven with a NON-EMPTY `git diff`.
  RE-MEASURED AT RESOLUTION TIME rather than carried on the review's word, because the whole finding is that a command lies about what it wrote. On a throwaway copy of the real item in a scratch git repo: `aw backlog set open <item> --message "PROBE: same-status note"` printed `unchanged`, the file's md5 was `03436eff23acf67f690cb026931f0f30` both BEFORE and AFTER, `grep -c PROBE` returned 0, and the history line count stayed at 2. So the silent drop is confirmed live at HEAD and option (a) is not a preference but the only route that writes anything by hand. FOR COMPLETENESS the declined route was measured too: `aw backlog set graduated <item> --message "..."` DID write (the file moved to `.aw/records/backlog/graduated/`, history grew 2 -> 3, and `- Blocks-Release: next` was preserved), which confirms the review's claim that (b) works mechanically; it was declined on what it ASSERTS, not on whether it functions.
  THE UNDERLYING DEFECT IS ALREADY FILED TWICE AND IS NOT THIS PLAN'S TO FIX: backlog `x6tk1u` (`open`, high, `Blocks-Release: next`) records the same-status `--message` drop with this exact root cause, and `hg2oop` (`open`, high, `Blocks-Release: next`) records the related history-durability defect and independently notes the missing `aw backlog note` verb. Both already carry option (c) as a candidate fix, so nothing is lost by declining it here.
  ORIGINAL FINDING, PRESERVED: BLOCKING because E-05 as authored COULD NOT BE PERFORMED and its failure was SILENT, so an executor would tick it, `aw backlog check` would pass, and no correction would exist. MEASURED at review by running the real command against a throwaway copy in a scratch repo: `aw backlog set open x7wfyx --message "..."` printed `unchanged`, the file was byte-identical afterwards, and the message appeared nowhere in it. The cause is structural rather than a missing flag: `status_set.apply_status_change` returns early when neither content nor path changed, and the `## Workflow history` write sits after that return, so a same-status call cannot append history by construction. `aw backlog` exposes only `new|set|check`, and the verb that does exactly what E-05 wants (`aw specs note`, "Append a workflow-history record to a spec WITHOUT changing its status") has NO BACKLOG TWIN. THE THREE OPTIONS, of which the maintainer should pick one: (a) append the correction to the item's BODY PROSE as an ordinary tracked edit of a path this plan already declares, which is honest, in scope, and writes no fabricated transition - the reviewer's recommendation; (b) `aw backlog set graduated x7wfyx --message "..."`, which DOES write history because the status really changes, but asserts a design handoff that is only half true (`dy9ymn` arguably hands off item B, while item A, the turn budget, has no plan at all), so it must not be chosen unilaterally; (c) add a `note` verb to `aw backlog` mirroring `aw specs note`, which is the right long-run fix and is out of scope for a signal-recording plan. E-05 now names all three and requires `V-05` to state which was used and to prove it with a NON-EMPTY `git diff`, so whichever the maintainer picks, the silent-failure mode is closed.
- Carrier: x7wfyx

### OQ-05: Should the truncation write be host-neutral in `execute_item_core` instead of one-sided in `run_agy_turn`?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING because the route E-04 now names is correct, in scope, and testable, and because the asymmetry is the one `OQ-02` already justifies on evidence (only the agy CLI emits these lines). Raised because the route has a real cost worth a reviewer's eye: `run_agy_turn` performs NO state writing today (measured: zero `save_state`, zero `append_jsonl`, zero `item[...]` assignments), so E-04 adds a new responsibility to a launcher that had none, and the oc twin will not have it - the very one-sided-guard shape this plan's conventions section names as a known local defect pattern. The host-neutral alternative is to construct the observer in `runner_shared.execute_item_core` and pass it to the launcher, which would put the write where the `attempt` dict is created and give both hosts the same code path; it is excluded here only because it requires declaring `runner_shared.py`, which would widen a signal-recording plan into the shared runner core that two sibling plans are already editing. If the reviewer prefers the neutral shape, it belongs to a plan that declares that file. E-04 requires the asymmetry be stated in a comment at the write site either way, so the choice is visible to the next reader rather than inferred.
- Carrier-Declined: THE CHOSEN ROUTE IS COMPLETE AND SELF-DOCUMENTING, so nothing is pending on a future artifact: E-04 names the in-scope route, verifies it works, and requires the asymmetry be recorded in the code. Should the reviewer prefer the host-neutral shape, that is a new plan declaring `runner_shared.py`, decided at that point rather than owed by this one.


## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `pytest` output showing the classifier returns TRUNCATING for BOTH real truncating lines (`root agent idle; waiting up to 5s for 2 background task(s)` and `terminating 2 background task(s) on exit`), returns WAITING and explicitly NOT truncating for the real waiting line (`root agent idle; waiting for 1 background task(s) (bounded by --print-timeout)`), and returns None for ordinary JSONL event lines and for an empty line. The waiting-form case is a load-bearing negative control: without it the classifier could flag healthy turns.
    THE SECOND LOAD-BEARING CONTROL IS THE AGENT-ECHO CASE, added at review. Feed the classifier a JSON envelope whose PAYLOAD contains a truncating line verbatim, e.g. `{"event":"assistant","text":"terminating 2 background task(s) on exit"}` and `{"event":"tool_result","output":"root agent idle; waiting up to 5s for 2 background task(s)"}`, and assert BOTH return None. Without this control the classifier fires on an agent that merely quotes the host's wording, which is a live risk in this Set because two sibling plans reproduce those lines verbatim in text an executing agent reads and may echo. Also assert the discriminators are not the shared `root agent idle` prefix (measured at review to match both forms).
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
  - Required evidence: pasted NON-EMPTY `git diff` of the `x7wfyx` item showing the corrected cause with its session citation actually present in the file, plus a statement of WHICH route from E-05 was used. THE NON-EMPTY DIFF IS THE LOAD-BEARING PART: measured at review, `aw backlog set` on a same-status item prints `unchanged` and writes nothing, so a command's exit code or its printed line is NOT evidence here and must not be accepted as such. If route (b) was used, the diff must also show the status transition and the file move, and `OQ-04` must be resolved first. Plus pasted `aw backlog check` reporting conformance, plus pasted `git status --porcelain` or `git log` evidence that `q1z9gn`'s file is UNMODIFIED, plus confirmation that `x7wfyx`'s `- Blocks-Release: next` is still present. Also paste the full bare `python3 -m pytest` summary line for the whole plan.
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
