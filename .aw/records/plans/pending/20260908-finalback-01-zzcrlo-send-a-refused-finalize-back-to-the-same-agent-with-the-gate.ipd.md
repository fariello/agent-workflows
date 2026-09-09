# IPD: Send a refused finalize back to the same agent with the gate findings, and stop counting a refusal as run success

- Date: 2026-09-08
- Kind: child
- Concern: A refused finalize is a DEAD END that the run then reports as success. Measured in `run-20260908T213552Z-3724920` (agy, plan `xbwq8n`): the agent wrote correct code and committed it to a lane, never ticked its `E-*`/`V-*` boxes, `aw ipd finalize` refused with nine `IPD-S404` findings, and the runner printed `Outcome: COMPLETED`, `Progress: 1/1 [==========] 100%`, exited 0, and left two commits stranded on `aw/lane/xbwq8n`. Order 01 of a ten-plan Set had not landed, and the summary said it had.
  THE REFUSAL IS CORRECT AND STAYS. Nothing here weakens a gate. The defect is what happens NEXT, which today is nothing: the refusal arm writes state, prints, and falls through (`agy_runipd.py:3909-3930`, twin `oc_runipd.py:6852-6873`).
  TWO INDEPENDENT DEFECTS, and the second is the one that actually hurt. FIRST, no retry: nothing routes an `IPD-S404` refusal back to the agent, and `run_recovery.plan_retry` (`:269`) / `retry_budget_remaining` (`:415`) still have ZERO production callers. SECOND, and worse, the run REPORTS SUCCESS: `render_stream.py:1870-1877` sets `outcome_str = "COMPLETED"` when every queue item is in `("executed", "reviewed", "approved", "substantially-complete")`, and `substantially-complete` is also in `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:337`). So a refused finalize is counted as success even if the retry never happens. The honest-reporting fix is separable, smaller, and more urgent than the loop.
  AN APPROVED SPEC ALREADY MANDATES THE LOOP, so this is conformance work rather than a proposal. Spec `25kzda` (`- Status: approved`, `- Blocks-Release: next`) Section 4.6 assigns action `RETRY, then FAIL ITEM` to exactly the three checks this run failed: `IPD-EXEC-E-COMPLETE` (`:711`, "Every E item is checked"), `IPD-EXEC-V-EVIDENCE` (`:712`, "nonempty concrete observed evidence"), and `IPD-EXEC-PRE-TRANSITION` (`:714`, "Linter passes before terminal mutation"). Section 4.1 (`:586`) defines RETRY as "enter `correction_required`, issue a bounded correction packet, and retry the checker while the frozen retry budget remains", Section 5.5 (`:974-975`) explicitly permits spending budget on "failed deterministic check for which a bounded correction is safe" and "missing or stale validation evidence", and Section 5.3 (`:922`) specifies a packet "containing only failed predicates and existing evidence". None of it is built: the spec admits at `:39` that all 11 `IPD-EXEC-*` codes "GREP TO ZERO FILES", which I re-verified at HEAD.
- Scope: Make a refused finalize (a) visible in the run outcome instead of being counted as success, and (b) automatically re-dispatched ONCE PER REMAINING BUDGET UNIT to the same item in the same run, carrying the gate's own findings, with FAIL ITEM on exhaustion. Spend the existing frozen retry budget through the already-shipped helpers rather than inventing a second counter. EXCLUDES weakening or changing what any gate decides; excludes the verifier verdict fail-open (`wyw936`/`1bfppy`); excludes the retryable-class allowlist for host/exit failures (`xipfy1`); excludes any new CLI flag.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_render_stream.py, tests/test_finalize_sendback.py
- Item-Dependencies: none
- Status: to-review
- Set: finalback
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: zzcrlo
- From-Backlog: rwibaz
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `rwibaz`, inheriting its `- Blocks-Release: next` because spec `25kzda` is approved, release-gating, and mandates the behavior.
  THIS PLAN DELIBERATELY DOES NOT TRY TO PREVENT A DISHONEST TICK, and that is a correction to the filing item's own suggestion. An earlier framing of `rwibaz` said a plan "must never let the correction turn WEAKEN the gate" and must stop an agent ticking a box without doing the work. That is not implementable and I am not proposing it: a checkbox and a pasted evidence block are just text an agent can write, and no amount of prompt wording changes that. The maintainer ruled this out explicitly (2026-09-08): we are not mitigating malice. What IS implementable is exactly what this plan does, and it is worth stating why it is enough: the pre-transition gate is the WRONG place to look for honesty because it only reads the plan file, but the RUN already holds independent evidence (the actual diff, the actual commits, the actual test output in `sessions/*.jsonl`), and a FALSE tick therefore produces a plan that finalizes while its claims contradict artifacts a later reader can check. Detecting that contradiction is the verifier's job and it is `wyw936`'s fail-open, not this plan's. So the honest scope here is: make the refusal actionable and make the run stop lying about it. A confused or forgetful agent (the measured case: good code, forgotten bookkeeping) is fixed by handing it the findings. A lying agent is out of scope for any prompt-level mechanism.
  THE MOST USEFUL THING I FOUND, and it corrects a claim in the filing item: `finalize_refused` IS ALREADY in `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` (`lane_containment.py:199`), and `prior_attempt_summary` (`:206`) is already interpolated into the recovery prompt as `Prior attempt: {json.dumps(prior, sort_keys=True)}` (`agy_runipd.py:2397`, `oc_runipd.py:4848`). `rwibaz` says the key is absent from that allowlist; it is not. So the FEEDBACK CHANNEL ALREADY EXISTS AND ALREADY CARRIES THE GATE'S MESSAGE: a re-dispatch with `recovery=True` will hand the agent the nine `IPD-S404` findings with no new plumbing. That shrinks E-03 to setting a flag rather than building a packet, and it is why this plan is `standard` rather than an exception.
  THE SECOND USEFUL FINDING: `substantially-complete` is ALREADY in the `--retry-incomplete` status set (`oc_runipd.py:7221-7223`), so an operator can already recover this case by hand. The gap is purely that it is neither automatic nor honestly reported. `requeue_interrupted` (`oc_runipd.py:7066`) is the existing pattern to copy, and its docstring states the design rule this plan must respect: a gate belongs IN the requeue, because "a refusal added anywhere else would simply be BYPASSED by the call that already ran".
  I SPLIT REPORTING FROM RETRYING ON PURPOSE. E-01/E-02 (honest outcome) are independently valuable and independently reviewable: even if the maintainer rejects the automatic loop entirely, a run must not print `COMPLETED` over a refused finalize. E-03..E-05 (the loop) build on them. If review wants to cut this plan down, cut the loop and keep the reporting.

## Goal

Make a refused finalize actionable and honestly reported: the run must not claim success, and the item must be handed back to the same agent in the same run with the gate's own findings while frozen retry budget remains, failing the item when the budget is exhausted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop reporting a refusal as success (independently valuable)

- [ ] E-01 MAKE THE RUN OUTCOME REFLECT A REFUSED FINALIZE instead of counting it as `COMPLETED`.
  THE EXACT DEFECT: `render_stream.py:1870-1877` computes `outcome_str = "COMPLETED"` when every queue item's status is in `("executed", "reviewed", "approved", "substantially-complete")`. An item whose finalize was REFUSED sits at `substantially-complete`, so a run that landed nothing prints `COMPLETED` in green at `100%`.
  DISCRIMINATE ON THE REFUSAL, NOT ON THE DISPOSITION. Do NOT remove `substantially-complete` from that tuple: it is a legitimate success-ish state for an item that finished without a refused transition, and removing it would recategorize runs this plan is not about. The signal to key on is the recorded refusal itself, `item["finalize_refusal"]` (written at `oc_runipd.py:6854`, `agy_runipd.py:3911`), which is currently written and READ NOWHERE. This is its first consumer.
  `PARTIAL` IS THE HONEST WORD and the branch already exists (`render_stream.py:1878-1879`). A run where some work happened but the plan did not land is exactly partial. Do not invent a new outcome token unless `PARTIAL` is provably wrong, and if you do, state why.
  THE SUMMARY TABLE'S PER-ITEM ROW MUST SAY IT TOO. The measured run rendered `Status: substantially-complete` with `Verify: verified` and no indication that finalize refused, which is how a human reads the table as success. Surface the refusal on the row or in a note beneath it, so the table alone is not misleading. Keep it short; the full nine-finding message belongs in the existing stderr line, not in a table cell.
  - Depends on: none
  - Expected outcome: a run containing an item with a non-empty `finalize_refusal` does NOT report `COMPLETED`; the per-item row or an adjacent note shows the refusal; `substantially-complete` without a refusal is unchanged; no gate decision changes.
  - Execution state: pending

- [ ] E-02 STOP TREATING A REFUSED ITEM AS AN EXECUTION SUCCESS FOR IN-RUN DEPENDENTS, because this is the more dangerous half of the same defect.
  WHY THIS MATTERS MORE THAN THE COSMETICS: `EXECUTION_SUCCESS_STATES = {"executed", "substantially-complete"}` (`oc_runipd.py:337`) is consulted by the in-run dependency check (`oc_runipd.py:3377-3380`), which decides whether a LATER item's `Item-Dependencies` edge is satisfied. The measured plan `xbwq8n` is Order 01 of a ten-plan Set whose nine siblings depend on the resolver it delivers. If a sibling had been queued in the same run, it would have been dispatched believing Order 01 landed, when nothing had merged.
  AGAIN, DISCRIMINATE ON THE REFUSAL, not by shrinking the set. Shrinking `EXECUTION_SUCCESS_STATES` would change behavior for every legitimately `substantially-complete` item; the correct test is "reached a success state AND no finalize refusal".
  VERIFY THE BLAST RADIUS BEFORE EDITING: grep every reader of `EXECUTION_SUCCESS_STATES` in both drivers and state what each does with it, because one of them is the dependency gate and others may be reporting. If a reader legitimately wants the looser meaning, leave it alone and say so.
  - Depends on: none
  - Expected outcome: an item whose finalize was refused does NOT satisfy a later item's `Item-Dependencies` edge in the same run; every reader of `EXECUTION_SUCCESS_STATES` enumerated with its intent stated; no change for a refusal-free `substantially-complete` item.
  - Execution state: pending

### Task group 2: hand it back to the agent, bounded by the existing budget

- [ ] E-03 RE-DISPATCH THE ITEM ONCE PER REMAINING BUDGET UNIT after an `IPD-S404` refusal, in the same run, in recovery mode.
  THE CHANNEL ALREADY EXISTS, so this is wiring and not construction. Setting `item["recovery_next"] = True` and returning the item to `queued` is the established pattern (`requeue_interrupted`, `oc_runipd.py:7096-7098`), `run_queue` consumes it (`oc_runipd.py:7358`, `agy_runipd.py:4382`), and the recovery prompt already interpolates `Prior attempt: {json.dumps(prior)}` (`oc_runipd.py:4848`, `agy_runipd.py:2397`) whose safe-key list ALREADY INCLUDES `finalize_refused` (`lane_containment.py:199`). So the agent will receive the gate's exact nine findings without a new packet format.
  PUT THE DECISION IN THE REFUSAL ARM, not in a later sweep. `requeue_interrupted`'s docstring states the rule and the reason: a gate placed anywhere other than the requeue itself "would simply be BYPASSED by the call that already ran". The refusal arm (`agy_runipd.py:3909`, `oc_runipd.py:6852`) is where the run knows a refusal happened.
  DO NOT RE-DISPATCH ON EVERY REFUSAL CLASS. Scope this to the pre-transition/E-V family (`IPD-S404` and the `empty Observed evidence` companion) that spec Section 4.6 marks `RETRY`. A refusal this plan does not understand must fall through to today's behavior (preserve and report), not be retried blindly. Section 5.5's never-retry list (`:978-989`) is the boundary: out-of-scope mutation, ownership conflict, corrupt ledger, unknown transaction outcome, unauthorized status change, human approval gate, hook bypass, push attempt. Read it and honor it.
  BOTH HOSTS, IDENTICALLY. The refusal arms are twins and must stay twins; if the logic is worth sharing, put it in `runner_shared`, which is where the cross-host seam lives.
  - Depends on: E-01, E-02
  - Expected outcome: an `IPD-S404`-class refusal returns the item to `queued` with `recovery_next = True` and re-dispatches in the same run; the agent's prompt carries the gate's findings via the existing `Prior attempt:` channel with no new format; unrecognized refusal classes fall through unchanged; both hosts behave identically.
  - Execution state: pending

- [ ] E-04 SPEND THE FROZEN RETRY BUDGET THROUGH THE SHIPPED HELPERS, and FAIL THE ITEM when it is exhausted.
  DO NOT INVENT A SECOND COUNTER. `run_recovery.plan_retry` (`:269`) and `retry_budget_remaining` (`:415`) already exist, are tested, and already enforce spec `25kzda` 2.1's 0..10 range via `validate_retry_budget` before any ledger read. They currently have ZERO production callers; this is their first. Read `plan_retry`'s six documented guarantees before wiring: it refuses a non-retryable state, preserves prior attempts, raises `RetryLimitExceededError` rather than looping, is idempotent on a repeated key, and INVALIDATES evidence bound to the retried step so a stale green cannot survive the retry boundary.
  A BUDGET OF 0 MUST MEAN NO RETRY, not one. Spec `:568` is explicit: "`0` means the first failed deterministic check or retryable host attempt immediately fails the item; no correction packet is issued." A test must pin the 0 case, because an off-by-one here converts a deliberate opt-out into a silent retry.
  EXHAUSTION FAILS THE ITEM. Section 4.6's action is `RETRY, then FAIL ITEM`, and the FAIL half is what makes this safe: without it the run still ends up reporting a non-landing as success, which is the defect E-01 fixes. So on exhaustion set a failed status, not `substantially-complete`.
  IF THE HELPERS DO NOT FIT, SAY SO RATHER THAN FORCING THEM. They are written against `run_engine`/`run_state`, which neither driver imports today (verified: the only `run_state` mention in `oc_runipd.py` is a comment). If adapting them is a larger change than this plan's scope, record that as a finding and implement the bound directly against the attempt list, but do NOT quietly duplicate a second budget concept: name the divergence and its reason.
  - Depends on: E-03
  - Expected outcome: each re-dispatch consumes one budget unit through the existing helpers (or a stated, justified alternative); budget 0 performs no retry; exhaustion marks the item FAILED rather than a success state; no second budget counter is introduced.
  - Execution state: pending

### Task group 3: prove it with the measured case

- [ ] E-05 GUARD THE EXACT MEASURED REGRESSION: a refused finalize must never be counted as run success.
  WRITE THIS AS THE FALSIFIABLE CORE OF THE PLAN. Construct a run state whose single item is `substantially-complete` with a non-empty `finalize_refusal` (the literal shape of `run-20260908T213552Z-3724920`) and assert the rendered outcome is NOT `COMPLETED` and that the item does not satisfy a dependent's edge.
  DEMONSTRATE THE PRE-FIX FAILURE. Show the assertion FAILING against current code, because the whole point is that today it passes as success. An assertion that cannot distinguish fixed from unfixed proves nothing, which is the standard this repository already applies.
  USE THE REAL FIXTURE SHAPE, not an invented one. The nine-finding message is in the measured run's `state.json` under `queue[0].attempts[0].finalize_refused`; use that text so the test pins the real `IPD-S404` format rather than a paraphrase that could drift from what `ipd_lint` emits.
  - Depends on: E-04
  - Expected outcome: a test reproducing the measured state asserts the run is not reported `COMPLETED` and the refused item does not satisfy a dependent edge; the assertion is shown to FAIL against pre-change code; the fixture uses the real refusal text.
  - Execution state: pending

- [ ] E-06 COVER THE LOOP'S BOUNDS AND BOTH HOSTS, since an unbounded or single-host correction loop is a worse defect than the one being fixed.
  THE REQUIRED CASES: a refusal with budget remaining re-dispatches exactly once per unit and no more; budget 0 does not retry at all; exhaustion FAILS the item; a successful correction (agent ticks the boxes and pastes evidence on the second turn) finalizes and reports success; a refusal class on Section 5.5's never-retry list is NOT retried; and the re-dispatched prompt actually CONTAINS the gate findings (assert on the rendered prompt text, not on the flag).
  ASSERT NO INFINITE LOOP MECHANICALLY. A test that merely checks "it retried" would pass on an implementation that retries forever. Bound the run and assert a maximum dispatch count.
  BOTH HOSTS. Duplicate the coverage for `agy_runipd` and `oc_runipd`, since the measured incident was agy and the twin is where drift hides.
  - Depends on: E-05
  - Expected outcome: all listed cases pass on BOTH hosts, including a mechanical no-infinite-loop bound and an assertion on the rendered prompt containing the findings.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE FEEDBACK CHANNEL IS ALREADY BUILT. `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` (`:177-204`) INCLUDES `finalize_refused` (`:199`); `prior_attempt_summary` (`:206`) is called at `oc_runipd.py:4820` and `agy_runipd.py:2373`; the prompt renders `Prior attempt: {json.dumps(prior, sort_keys=True)}` (`oc_runipd.py:4848`, `agy_runipd.py:2397`). This corrects `rwibaz`, which claims the key is absent.
- `requeue_interrupted` (`oc_runipd.py:7066`) IS THE PATTERN TO COPY, and its docstring states the placement rule: put the gate IN the requeue, because a refusal elsewhere "would simply be BYPASSED by the call that already ran".
- `substantially-complete` IS ALREADY RETRYABLE BY HAND: it is in `--retry-incomplete`'s status set (`oc_runipd.py:7221-7223`), so the operator route exists; only the automatic route and honest reporting are missing.
- THE OUTCOME STRING IS COMPUTED IN ONE PLACE: `render_stream.py:1870-1877`. `substantially-complete` is in the `COMPLETED` tuple, which is the reporting defect.
- `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:337`) FEEDS THE IN-RUN DEPENDENCY GATE (`:3377-3380`), which is why the reporting bug is also a correctness bug for Sets.
- THE RETRY HELPERS ARE DORMANT BUT COMPLETE: `run_recovery.plan_retry` (`:269`) documents six guarantees including evidence invalidation and `RetryLimitExceededError`; `retry_budget_remaining` (`:415`); the module states its own dormancy at `:53`. Neither driver imports `run_engine`/`run_state`.
- THE `IPD-EXEC-*` FINDING CODES ARE NAMES ONLY. Spec `25kzda:39` says every non-`RUN-*` family "GREPS TO ZERO FILES"; re-verified. Cite the SHIPPED enforcer (`ipd_lint --phase pre-transition`, `ipd_lint.py:754-782`) rather than the unbound codes, exactly as spec `:106` instructs.
- THE VERIFIER CANNOT BE THE ENFORCEMENT POINT HERE: its prompt does ask about the E/V table (`agy_runipd.py:2496-2499`) yet the measured run recorded `verified` anyway, because the verdict gate fails open (backlog `wyw936`). Do not route this through the verifier.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is currently `5866 passed, 3 skipped, 2 xfailed` (plus one environmental `test_reporting_contract` failure on a box with a gitignored `opencode-recovery/` dump, tracked as backlog `8kttqq`).

## Findings

| Id | Severity | Location (measured at HEAD `68c71307`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `render_stream.py:1870-1877` | A REFUSED FINALIZE IS REPORTED AS SUCCESS: `outcome_str = "COMPLETED"` when every item is in `("executed","reviewed","approved","substantially-complete")`, and a refused item sits at `substantially-complete`. The measured run printed green `COMPLETED` at `100%` having landed nothing. | source read; the run's own summary |
| F-2 | HIGH | `oc_runipd.py:337`, consumed `:3377-3380` | THE SAME CONFLATION IS A CORRECTNESS BUG, not just cosmetics: `EXECUTION_SUCCESS_STATES` includes `substantially-complete` and feeds the in-run `Item-Dependencies` gate, so a sibling in a ten-plan Set would be dispatched believing Order 01 landed. | source read |
| F-3 | HIGH | `agy_runipd.py:3909-3930`, `oc_runipd.py:6852-6873` | THE REFUSAL ARM IS TERMINAL: it writes `finalize_refused`/`finalize_refusal`, emits an event, prints to stderr, and falls through. No branch returns to a turn. | source read |
| F-4 | MED | `agy_runipd.py:3911`, `oc_runipd.py:6854` | `item["finalize_refusal"]` IS WRITTEN AT TWO SITES AND READ AT ZERO. E-01 is its first consumer. | grep across `agent_workflows/` |
| F-5 | N/A | `lane_containment.py:199`, `:206`; `oc_runipd.py:4848`; `agy_runipd.py:2397` | CORRECTS `rwibaz`: `finalize_refused` IS ALREADY an allowlisted prior-attempt key and IS ALREADY interpolated into the recovery prompt. The feedback channel exists, so E-03 sets a flag rather than building a packet. | source read |
| F-6 | N/A | `oc_runipd.py:7221-7223` | `substantially-complete` IS ALREADY IN `--retry-incomplete`'s SET, so an operator can recover this by hand today. The gap is automatic dispatch plus honest reporting, not the whole mechanism. | source read |
| F-7 | MED | `run_recovery.py:269`, `:415`, `:53` | THE BUDGET HELPERS ARE COMPLETE AND DORMANT (zero production callers, self-documented). `plan_retry` already invalidates evidence across the retry boundary and raises rather than looping. But they are written against `run_engine`/`run_state`, which NEITHER DRIVER IMPORTS, so the fit must be checked (E-04). | source read; import grep |
| F-8 | HIGH | spec `25kzda:711`, `:712`, `:714`, `:586`, `:922`, `:974-975` | AN APPROVED, RELEASE-GATING SPEC MANDATES THIS: Section 4.6 assigns `RETRY, then FAIL ITEM` to E-COMPLETE, V-EVIDENCE and PRE-TRANSITION; 5.5 permits the spend; 5.3 specifies the packet. This is conformance, not a feature. | spec read |
| F-9 | MED | spec `25kzda:39`, `:106`, `:163` | THE `IPD-EXEC-*` CODES ARE UNBOUND NAMES (grep to zero files, admitted by the spec), and `:106` instructs citing the shipped enforcer instead. So this plan must NOT pretend to implement the code family; it implements the behavior against `ipd_lint`'s real refusal. | spec read; grep |
| F-10 | MED | spec `25kzda:568` | BUDGET 0 MUST MEAN ZERO RETRIES ("immediately fails the item; no correction packet is issued"). An off-by-one converts an opt-out into a silent retry, hence a dedicated test. | spec read |
| F-11 | N/A | `agy_runipd.py:2496-2499`; backlog `wyw936` | THE VERIFIER IS NOT A VIABLE ENFORCEMENT POINT: it is prompted to check the E/V table and still returned `verified` in the measured run, because the verdict gate fails open. Route this through the deterministic gate instead. | source read; that item |
| F-12 | LOW | `oc_runipd.py:7066-7084` | THE PLACEMENT RULE IS ALREADY DOCUMENTED: a gate must live in the requeue itself or be bypassed by the call that already ran. E-03 follows it. | source read |

## Proposed changes (ordered, validatable)

1. E-01 keys the run outcome on the recorded refusal so a non-landing run is not reported `COMPLETED`.
2. E-02 stops a refused item from satisfying an in-run dependency edge, after enumerating every reader of `EXECUTION_SUCCESS_STATES`.
3. E-03 re-dispatches an `IPD-S404`-class refusal in the same run via the existing `recovery_next` + `Prior attempt:` channel, honoring Section 5.5's never-retry list.
4. E-04 spends the frozen budget through the shipped helpers, with 0 meaning no retry and exhaustion FAILING the item.
5. E-05 guards the measured regression with a pre-fix failure demonstration using the real refusal text.
6. E-06 covers the loop's bounds, the never-retry classes, the prompt contents, and both hosts.

## Deferred / out of scope (with reason)

- PREVENTING A DISHONEST TICK. Not implementable at the prompt level and explicitly ruled out by the maintainer (2026-09-08): we are not mitigating malice. A checkbox is text; an agent that will write an unearned one is not stopped by wording. The genuine defense is that the run holds independent evidence (diff, commits, session logs) against which a false claim is checkable, and detecting that contradiction is the verifier's concern (`wyw936`), not this plan's.
- THE VERIFIER VERDICT FAIL-OPEN. Backlog `wyw936` (`graduated`) and plan `1bfppy` (`to-review`). Adjacent and complementary: that path decides whether a turn's WORK was verified, while this one acts on a DETERMINISTIC gate refusal. Bundling them would merge a verdict-mapping fix with a scheduling change.
- THE RETRYABLE-CLASS ALLOWLIST FOR HOST AND EXIT FAILURES. Plan `xipfy1` (`to-review`, Set `retrywire`, `Blocks-Release: next`) owns the general allowlist and the flag surface. Its own OQ-01 warns that "a budget with no correction route is dead"; this plan is one such route, for one class. SEQUENCE, do not merge: taking over its scope would violate the graduation contract.
- BINDING THE `IPD-EXEC-*` FINDING CODES. F-9: they are unbound names across all 11, and binding the family is a spec-wide project. This plan implements the BEHAVIOR against the shipped enforcer, which is what spec `:106` instructs.
- ANY NEW CLI FLAG. The budget already has a frozen policy value and `--retry-incomplete` already exists. A new flag would be a second control surface for one behavior.
- SURFACING REFUSAL REMEDIES IN THE RUN VIEWER. Plan `r2i1b1` (`approved`, Set `orchprobe`) owns the read surfaces and adds a `remedy` field; its scope says "OUT: changing what any existing gate decides". This plan changes dispatch, not the viewer.
- RE-DISPATCHING REFUSALS OUTSIDE THE PRE-TRANSITION FAMILY. Section 5.5's never-retry list is the boundary and E-03 honors it; widening it needs its own analysis.

## Scope check

- Over-scope: `tests/test_finalize_sendback.py` is a NEW file and is declared. If E-01's reporting change is better tested inside `tests/test_render_stream.py` alone, then the new file may go unused and must carry a `--scope-ack` at finalize rather than being created empty to satisfy the declaration.
- Under-scope: stated rather than left as `none`. After this plan the verifier still fails open (`wyw936`), the general retryable-class allowlist still does not exist (`xipfy1`), and the `IPD-EXEC-*` codes remain unbound (F-9). Also: if E-04 finds the `run_recovery` helpers cannot be adapted without importing `run_engine`/`run_state` into a driver, the budget may be bounded directly against the attempt list, which leaves the shipped helpers dormant for one more cycle; that outcome must be recorded as a finding, not hidden.

## Required tests / validation

`python3 -m pytest` bare in the executing worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS rather than totals. The decisive validation is E-05's PRE-FIX FAILURE: the measured state must be shown to report `COMPLETED` today and not after. Every loop test must bound the dispatch count mechanically, since a test asserting only "it retried" would pass on an implementation that retries forever. Both hosts must be covered for every behavior, because the incident was agy and the twin is where drift hides. Do NOT assert on the unbound `IPD-EXEC-*` code strings; assert on the real `ipd_lint` pre-transition refusal text (`ipd_lint.py:754-782`), which is what the runner actually receives.

## Spec / documentation sync

NO SPEC IS AMENDED, and the reason is the point of this plan: spec `25kzda` (`- Status: approved`, `- Blocks-Release: next`) ALREADY REQUIRES this behavior in Section 4.6 (`:711`, `:712`, `:714`), Section 4.1 (`:586`), Section 5.3 (`:922`) and Section 5.5 (`:974-975`). This plan brings the code into conformance with text that is already approved, so it declares no spec file and must not edit one.
VERIFY THAT BEFORE EXECUTING rather than trusting it. Re-read Section 4.6's three rows and Section 5.5's two lists, and confirm the implemented trigger and never-retry boundary match them. IF THE IMPLEMENTATION CANNOT SATISFY THE SPEC AS WRITTEN, STOP AND REPORT: `25kzda` is approved and release-gating, so an agent may not resolve a conflict by editing it. That is a maintainer decision.
DO NOT CLAIM TO HAVE BOUND THE `IPD-EXEC-*` CODE FAMILY. F-9: all 11 grep to zero files and the spec itself says so at `:39`, instructing at `:106` to "cite the shipped enforcers, not the codes, until the codes are bound". Binding them is a separate, larger project. If this plan's work makes binding the three pre-transition codes trivial, RECORD that as a follow-up rather than expanding scope.
NO USER-FACING DOCUMENTATION CHANGE IS EXPECTED, since no CLI surface changes. If the run summary's outcome vocabulary is documented anywhere, correct it there.

## Open questions

### OQ-01: Should the correction turn re-run the whole item, or only ask for the bookkeeping?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as RE-DISPATCH THE ITEM IN RECOVERY MODE, which is the existing mechanism, and let the agent decide what remains. The measured case needed only the checkboxes and evidence, so a narrower "just tick the boxes" prompt is tempting, but it is wrong twice over. FIRST, the driver cannot know that the code half is complete: it knows only that a deterministic gate refused, and a prompt asserting the work is done would be the driver making a claim it has not verified. SECOND, the recovery prompt already exists, already carries `Prior attempt:` including `finalize_refused`, and already tells the agent it is continuing prior work, so the narrow variant would be a second prompt shape for no gain. `plan_retry`'s evidence-invalidation guarantee (`run_recovery.py:289-290`) is the right posture here: a retry does not inherit a stale green.

### OQ-02: Is `PARTIAL` the right outcome token, or is a new one needed?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-01's REQUIREMENT is only that the outcome not be `COMPLETED`, and any honest token satisfies it. `PARTIAL` already exists (`render_stream.py:1878-1879`) and reads correctly for "work happened, the plan did not land", which argues for reusing it over inventing vocabulary a human must learn. The case for a distinct token (say `REFUSED`) is that `PARTIAL` currently means "some items finished, some did not", whereas here a single-item run finished its work and failed only its transition, which a reader might misread as partial execution. Decide by reading what `PARTIAL` is documented to mean and state the choice; if a new token is added, check whether anything parses the outcome string before changing its domain.

### OQ-03: Can the shipped `run_recovery` helpers be used without importing `run_engine`/`run_state` into a driver?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-04 states the requirement (one bounded spend per re-dispatch, 0 means none, exhaustion fails the item) and permits a justified alternative. It is recorded because it is the plan's main unknown: `plan_retry(engine, step_id, failure_class, ...)` takes a `run_engine.RunEngine` and reads the budget from a ledger, while neither driver imports `run_engine` or `run_state` at all (the single `run_state` mention in `oc_runipd.py` is a comment). So using the helpers may pull a whole state model into the drivers, which is far larger than this plan. PREFERRED: use them if the adaptation is genuinely small, since they already enforce the 0..10 range and evidence invalidation and this would be their first production use. OTHERWISE: bound the retry directly against the item's `attempts` list, and RECORD the divergence as a finding so the dormancy of `plan_retry` remains visible rather than being quietly accepted for another cycle. Do not create a second competing budget concept either way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the rendered run summary for a state whose single item is `substantially-complete` WITH a non-empty `finalize_refusal`, showing the outcome is NOT `COMPLETED`. PASTE the same render for a `substantially-complete` item WITHOUT a refusal, showing it is UNCHANGED from today. PASTE the per-item row or note showing the refusal is visible. PASTE a diff proving `substantially-complete` was not removed from the outcome tuple and that no gate decision changed. State the OQ-02 token choice.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: PASTE the enumeration of EVERY reader of `EXECUTION_SUCCESS_STATES` in both drivers with its intent. PASTE test output showing a refused item does NOT satisfy a dependent's `Item-Dependencies` edge in the same run, and that a refusal-free `substantially-complete` item still DOES. PASTE the pre-fix run of that assertion showing it FAILED (today the dependent is dispatched).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: PASTE test output showing an `IPD-S404`-class refusal returns the item to `queued` with `recovery_next` set and re-dispatches within the SAME run, on BOTH hosts. PASTE THE RENDERED PROMPT of the second dispatch showing it CONTAINS the gate's refusal text (assert on the prompt, not the flag). PASTE a case where a never-retry class from spec `:978-989` is refused and is NOT retried. PASTE proof the decision lives in the refusal arm, not a later sweep.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: PASTE the budget-0 case showing ZERO retries (spec `:568`). PASTE a case with budget remaining showing exactly one spend per re-dispatch. PASTE the exhaustion case showing the item marked FAILED and the run NOT reporting success. State whether the shipped `run_recovery` helpers were used; if not, PASTE the justification and confirm no second budget counter was introduced (OQ-03).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: PASTE the new test and its passing output. PASTE the SAME test FAILING against pre-change code, which is this plan's central proof. PASTE the fixture showing it uses the real nine-finding `IPD-S404` refusal text from the measured run rather than a paraphrase.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: PASTE all required cases on BOTH hosts: budget-remaining single re-dispatch, budget 0, exhaustion fails, successful correction finalizes and reports success, never-retry class not retried, prompt contains findings. PASTE the mechanical no-infinite-loop assertion (a bounded maximum dispatch count), not merely "it retried". PASTE the `N passed` summary line from a BARE `python3 -m pytest` with the worktree baseline beside it and a node-id comparison. PASTE `git diff --check` clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the paths in `- Scope-Paths:`. Do NOT change what any gate DECIDES: `ipd_lint`'s pre-transition checks and the `ipd_lifecycle` finalize gates keep their current verdicts, and this plan acts on the verdict rather than altering it. Do NOT remove `substantially-complete` from the outcome tuple or from `EXECUTION_SUCCESS_STATES`; discriminate on the recorded refusal instead. Do NOT add a CLI flag. Do NOT touch the verifier verdict mapping (`wyw936`/`1bfppy`) or the general retryable-class allowlist (`xipfy1`). Do NOT edit spec `25kzda` (approved, release-gating): if the code cannot satisfy it as written, STOP AND REPORT. Do NOT claim to have bound the `IPD-EXEC-*` code family. Do NOT retry a class on spec `:978-989`'s never-retry list. Do NOT attempt to detect or prevent a dishonest checkbox: explicitly out of scope by maintainer ruling. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN, and this warning is load-bearing here: `oc_runipd.py` and `agy_runipd.py` moved roughly 70 and 95 lines in a single day and are among the most-edited files in the repository. Find `execute_item`, `requeue_interrupted`, `run_queue`, `build_prompt`, `render_run_summary_table`, `prior_attempt_summary`, `plan_retry`, `retry_budget_remaining` and `EXECUTION_SUCCESS_STATES` by NAME. Find the refusal arm by its `finalize_refused` assignment and its `ipd-finalize-refused` event, not by line.

SHARED CHECKOUT WARNING: both drivers are declared in the `Scope-Paths` of many other pending plans and may be under live edit. Confirm each target site reads as quoted before editing; if it has changed, STOP and report rather than reconciling another agent's in-flight work.

THIS PLAN WILL LIKELY BE EXECUTED BY THE VERY MECHANISM IT CHANGES. Take that seriously: a bug in E-03 or E-04 can put a run into a correction loop over this plan itself. Bound the loop before wiring the dispatch, and prefer landing E-01/E-02 (reporting) in a state that is safe on its own, since they are valuable even if the loop is later reverted.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved zzcrlo --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, backlog `rwibaz` (carried as `- From-Backlog:`) may be closed `done`, and its `- Blocks-Release: next` gate is inherited by this plan and must not be dropped.
