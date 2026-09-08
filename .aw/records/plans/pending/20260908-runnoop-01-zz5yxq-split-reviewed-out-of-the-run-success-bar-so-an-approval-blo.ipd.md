# IPD: Split reviewed out of the run success bar so an approval-blocked queue is not a silent success

- Date: 2026-09-08
- Kind: child
- Concern: `reviewed` is simultaneously a routing decision meaning "execute this" and a completion decision meaning "this already succeeded", and the two cannot both be right. MEASURED at HEAD `44d4950d` by running the deciding expressions against the real symbols: `action_for("child", "reviewed")` returns `'execute'` (`runner_shared.py:2735`, delegating to `determine_action` at `:2727`, which routes everything not `to-review`/`draft` to `execute`); the queue builder freezes that item's queue status as `"reviewed"` rather than `"queued"`, because `reviewed` is absent from the admission tuple `("to-review", "draft", "approved", "auto-approved")` (`oc_runipd.py:3011`, `agy_runipd.py:2026`); and `"reviewed" in SUCCESS_STATES` is `True` (`oc_runipd.py:327`, `agy_runipd.py:388`). So the item is never dispatched AND is counted as a success: `runner_stop.deliberate_stop_exit_code(["reviewed"], success_states=SUCCESS_STATES, stopped=False)` returns `0`.
  THE OBSERVED COST (backlog `em0z50`, 2026-08-29): `aw oc run wtiso` with all 8 `wtiso` plans at `- Status: reviewed` printed the run id, the state dir, and `No OpenCode session was captured for this run.` and exited 0. `aw runs <id>` showed `8 steps: 8 reviewed`, `action=execute`, `Attempts: 0` on every row, an empty `outcomes/`, and a single `run-created` event. The operator believed 8 plans were queued.
  THE CONSTANT IS DUPLICATED, NOT SHARED, which changes the work: measured `oc.SUCCESS_STATES is agy.SUCCESS_STATES` -> `False`, `==` -> `True`. Both hosts must be edited and the equality pinned, or the next fix reaches one host only. `EXECUTION_SUCCESS_STATES` already exists for the execution-success question (`oc_runipd.py:328`, `agy_runipd.py:389`) and is already used correctly in three places, so the vocabulary this plan needs is largely present.
- Scope: Make an execute-action item whose plan is `reviewed`-but-unapproved carry a NEEDS-APPROVAL disposition that is NOT a member of the success bar, on BOTH hosts, and make the run's exit code reflect it. Classify EVERY `SUCCESS_STATES` call site rather than substituting wholesale, because the constant answers five different questions. EXCLUDES making a `reviewed` plan executable (that is the auto-approval bridge, shipped by `97df1z`, deliberately not widened); excludes the per-artifact line (child 02) and the end-of-run summary (child 03); excludes any change to `determine_action`'s routing.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Set: runnoop
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: zz5yxq
- Blocks-Release: next
- From-Backlog: em0z50

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `em0z50` fix (a); inherits its `- Blocks-Release: next`. Every line number in this plan was measured at HEAD `44d4950d` by grep on the SYMBOL, and every behavioral claim was produced by RUNNING the expression rather than reading it. Three measurements changed the design from what the backlog item assumed. FIRST, the item cites `SUCCESS_STATES` at `oc_runipd.py:90`; it is at `:327`, and the agy twin at `:388` is a SEPARATE object, so "audit every use and its agy twin" is two edits plus an equality pin, not one edit. SECOND, there are SEVEN `SUCCESS_STATES` reads in oc and FIVE in agy answering FIVE DIFFERENT questions, and one of them (the orchestrator dispatch bar at `oc_runipd.py:3504`) already passes `EXECUTION_SUCCESS_STATES` deliberately, so a blanket substitution would both over- and under-reach; E-01 classifies them first and the classification is the deliverable, not a step. THIRD, and this is the finding most likely to be missed: `cascade_dependency_blocked` (`oc_runipd.py:4217-4219`) and `edge_satisfied` (`:3373`) BOTH select between the two constants on `item.get("action") != "review"`, and the docstring at `:4186` records a MEASURED failure from hardcoding the execution bar there ("a review-mode Set run was simply impossible to complete", run `run-20260904T042705Z-1025943`). So `reviewed` MUST remain in the review-action bar; only the EXECUTE-action bar may lose it. A fix that removed `reviewed` from `SUCCESS_STATES` outright would re-break review-mode Set runs, which is why E-01 forbids that shape explicitly.

## Goal

Stop a `reviewed`-but-unapproved execute item from being recorded and counted as a success, on both hosts, without making it executable and without re-breaking review-mode Set runs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: classify before changing

- [ ] E-01 CLASSIFY EVERY `SUCCESS_STATES` READ IN BOTH HOSTS and record the classification in the code as a comment at the constant's definition, naming which question each site asks. Locate the sites by grep on the SYMBOL, never by the line numbers in this plan. Measured at HEAD `44d4950d` there are SEVEN in `oc_runipd.py` (`:327` definition, `:3373` in `edge_satisfied`, `:4219` in `cascade_dependency_blocked`, `:6743` and `:6746` the finish glyph and its color, `:7296` the exit code, `:7377` the continuation hint's `all_success`) and FIVE in `agy_runipd.py` (`:388` definition, `:2275` the `edge_satisfied` twin, `:4013`/`:4016` the glyph pair, `:4509` the exit code, `:4583` the `all_success` twin).
  THE FIVE QUESTIONS, so the classification is not re-derived: (1) IS A PREREQUISITE SATISFIED IN THIS RUN (`edge_satisfied`, `cascade_dependency_blocked`) - these already select between the two constants on `item.get("action") != "review"` and MUST KEEP `reviewed` for the review action; (2) DID THE RUN SUCCEED OVERALL (the exit code); (3) SHOULD THIS ROW SHOW A CHECKMARK (the glyph pair); (4) IS THERE ANYTHING LEFT TO RESUME (`all_success` in the continuation hint); (5) the ORCHESTRATOR DISPATCH BAR, which already passes `EXECUTION_SUCCESS_STATES` explicitly (`oc_runipd.py:3504`) and is NOT a `SUCCESS_STATES` read at all, listed here only so a reader does not "fix" it.
  DO NOT REMOVE `reviewed` FROM `SUCCESS_STATES`. That is the tempting one-line fix and it is WRONG, with measured evidence in-tree: the docstring at `oc_runipd.py:4186-4198` records that hardcoding `EXECUTION_SUCCESS_STATES` in `cascade_dependency_blocked` made a review-mode Set run impossible to complete (run `run-20260904T042705Z-1025943`: a 6-item all-`review` run of the `wslayout` Set reviewed Orders 00 and 01, then killed Orders 02-05 the instant Order 01 reached `reviewed`). `SUCCESS_STATES` IS the review-action bar and `reviewed` belongs in it. The defect is that the EXECUTE-action sites read it too.
  - Depends on: none
  - Expected outcome: a comment at each constant's definition in BOTH hosts naming, per call site, which of the five questions it answers and which bar is correct for it; no behavior change in this item.
  - Execution state: pending

### Task group 2: split the bar for the execute action

- [ ] E-02 GIVE THE EXECUTE-ACTION SITES AN ACTION-AWARE BAR, using the selection shape `edge_satisfied` and `cascade_dependency_blocked` already use (`item.get("action") != "review"`) rather than inventing a second idiom. The sites to change are the ones E-01 classified as questions (2), (3) and (4): the exit code, the glyph pair, and `all_success`. An item whose `action` is `execute` and whose status is `reviewed` must NOT satisfy any of the three.
  SITE THE PREDICATE ONCE, IN `runner_shared.py`, NOT IN EITHER RUNNER. The two hosts must share it or they will drift, and the direction is fixed: `agy_runipd` imports 47 names from `oc_runipd` and zero flow back, so adding this to `oc_runipd` for agy to import would make it 48 and deepen the layering defect backlog `cnwy8g` owns. `runner_shared` already holds `determine_action` and `action_for` (`:2727`, `:2735`), which is exactly this family of decision, so it is the established home.
  - Depends on: E-01
  - Expected outcome: one shared predicate in `runner_shared`, imported by both hosts; a `reviewed` execute item fails all three of exit-code success, checkmark glyph, and `all_success`; a `reviewed` REVIEW item still satisfies all three, unchanged.
  - Execution state: pending

- [ ] E-03 RECORD THE NEEDS-APPROVAL DISPOSITION ON THE QUEUE ITEM so it is durable in run state rather than only reflected in an exit code. The queue builder already distinguishes the case: an item whose plan status is not in the admission tuple gets queue status `"reviewed"` (`oc_runipd.py:3011`, `agy_runipd.py:2026`), which is where the needs-approval fact is already implicit. Make it EXPLICIT and name it, so children 02 and 03 have a token to print and count.
  RESOLVE OQ-01 BEFORE WRITING THE TOKEN. Spec `25kzda` §5.6 enumerates the allowed per-item outcomes (`verified`/`ran`/`failed`/`skipped`/`needs_input`/`cancelled`) and does NOT contain a `needs-approval` token, while the runner's own vocabulary is `TERMINAL_STATES` (`oc_runipd.py:308-326`). Take the spec's `needs_input`, whose §5.6 gloss is "a human gate stopped the item" and which fits exactly, OR amend §5.6 and declare that spec file in this plan's `- Scope-Paths:`. Do NOT invent a token that appears in neither. If you amend the spec, say WHY in the spec-sync section: a spec edit changes the contract every other plan is reviewed against.
  DO NOT ADD A NEW MEMBER TO `TERMINAL_STATES` WITHOUT CHECKING ITS READERS. `TERMINAL_STATES` is consulted by `cascade_dependency_blocked` (`:4216`) and `decide_orchestrator_dispatch` (`runner_shared.py:2756`), so a new member changes dependency and retirement behavior. Measure those readers before adding, and if the queue status `"reviewed"` already suffices as the durable carrier, prefer annotating the item over widening the set.
  - Depends on: E-02
  - Expected outcome: the queue item carries an explicit, named needs-approval fact readable by a later reporting child; the chosen name is either the spec's `needs_input` or a spec-amended token, with the choice recorded; `TERMINAL_STATES` readers are measured before any widening.
  - Execution state: pending

- [ ] E-04 PIN THE CROSS-HOST EQUALITY of `SUCCESS_STATES` and `EXECUTION_SUCCESS_STATES` so a future one-sided edit fails a test. Measured today: `is` -> `False`, `==` -> `True` for both pairs. This plan does NOT unify them into one object (that is `rununify`'s job and `cnwy8g`'s layering correction), so the equality assertion is the only thing standing between here and a silent divergence.
  ASSERT THE SHARED PREDICATE BY OBJECT IDENTITY TOO, not by grep: the predicate E-02 adds must resolve to the SAME object from `oc_runipd`, `agy_runipd` and `runner_shared`. Grep cannot tell a shared object from a textually identical copy, which is precisely how `render_stream` was re-forked.
  - Depends on: E-02
  - Expected outcome: a test asserting `oc.SUCCESS_STATES == agy.SUCCESS_STATES` and the same for `EXECUTION_SUCCESS_STATES`, which FAILS if either is edited alone; plus an object-identity assertion for the new shared predicate across all three modules.
  - Execution state: pending

### Task group 3: prove it on the measured case

- [ ] E-05 ADD THE REGRESSION TEST FOR THE MEASURED INCIDENT: a run whose selector resolves ONLY to `reviewed`-not-approved plans must not count those steps as successes and must not exit 0. Build it from the real queue-entry shape rather than a hand-written dict where possible, so the test breaks if the queue builder's admission tuple changes.
  ALSO ADD THE CONTROL, and it is the load-bearing half: an all-`review`-action run whose items reach `reviewed` must STILL succeed and STILL exit 0, because that is the case the in-tree docstring at `oc_runipd.py:4186` records as having been broken once by exactly the fix this plan makes. A test suite that only covers the execute case would pass over a re-broken review-mode Set run.
  - Depends on: E-03, E-04
  - Expected outcome: two tests per host, one asserting the execute case is no longer a silent success and one asserting the review case is unchanged; both pass.
  - Execution state: pending

- [ ] E-06 MUTATION-CHECK BOTH NEW GUARDS. A guard that cannot fail is not evidence. For E-04's equality pin, edit one host's constant and show the test FAILS, then revert. For E-05's execute-case test, revert the E-02 predicate to the unconditional `SUCCESS_STATES` read and show the test FAILS, then restore.
  - Depends on: E-05
  - Expected outcome: each guard demonstrated to fail under the mutation it exists to catch, and to pass after revert.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE ACTION-AWARE BAR IS AN ESTABLISHED IDIOM, NOT AN INVENTION. `edge_satisfied` (`oc_runipd.py:3365`) and `cascade_dependency_blocked` (`:4217-4219`) both write `EXECUTION_SUCCESS_STATES if is_exec else SUCCESS_STATES` with `is_exec = item.get("action") != "review"`. Reuse that exact shape; a second idiom for one decision is how two functions came to give opposite answers before (the docstring at `:4186` records it).
- THE IMPORT DIRECTION IS ONE-WAY AND MUST STAY SO. `agy_runipd` imports 47 names from `oc_runipd` (AST-measured 2026-09-08); `oc_runipd` imports zero from agy. A shared symbol goes in `runner_shared` (which both import) and never in a host driver.
- `runner_shared` ALREADY OWNS THIS FAMILY OF DECISION: `determine_action` (`:2727`) and `action_for` (`:2735`) live there precisely so the two hosts cannot route differently. The comment at `oc_runipd.py:117-119` records the measured divergence that forced the move (`agy.determine_action('approved')` returned `'execute'` where oc's did not, at HEAD `844d195c`).
- `EXECUTION_SUCCESS_STATES` ALREADY EXISTS and is already the correct bar in three places, so this plan mostly makes more sites use the constant that is already right, rather than inventing a state.
- THE BASELINE MUST BE MEASURED IN THE EXECUTING WORKTREE, not quoted from here. A bare `python3 -m pytest` on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which asserts live plan statuses in this repository and drifts as plans advance). Inside a lane worktree roughly 32 tests fail for environmental reasons, because several read live repo state. Compare failing NODE IDS, never totals.
- Suite bare: `python3 -m pytest`. Do not add `-n0`, a second `-q`, or `-p no:randomly`; `pyproject.toml` `addopts` already supplies the intended flags.

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `oc_runipd.py:327`, `agy_runipd.py:388` | `reviewed` is a member of `SUCCESS_STATES`, which is the "already succeeded" bar. | `"reviewed" in oc.SUCCESS_STATES` -> `True` |
| F-2 | HIGH | `runner_shared.py:2727`, `:2735` | The same status routes to `action=execute`, so one status carries two contradictory meanings. | `action_for("child","reviewed")` -> `'execute'` |
| F-3 | HIGH | `oc_runipd.py:7296`, `agy_runipd.py:4509` | The run exit code is computed against `SUCCESS_STATES`, so an all-`reviewed` queue exits 0 having done nothing. | `runner_stop.deliberate_stop_exit_code(["reviewed"], success_states=SUCCESS_STATES, stopped=False)` -> `0` |
| F-4 | HIGH | `oc_runipd.py:3011`, `agy_runipd.py:2026` | The admission tuple omits `reviewed`, so such an item is frozen as queue status `"reviewed"` and never dispatched. Both hosts, byte-identical expression. | source read, both hosts |
| F-5 | BLOCKER-IF-IGNORED | `oc_runipd.py:4186-4198` | REMOVING `reviewed` FROM `SUCCESS_STATES` WOULD RE-BREAK REVIEW-MODE SET RUNS. The in-tree docstring records the measured failure (run `run-20260904T042705Z-1025943`, `wslayout`, Orders 02-05 killed the instant Order 01 reached `reviewed`) caused by hardcoding the execution bar at that site. `SUCCESS_STATES` IS the review-action bar. | in-tree docstring citing a real run id |
| F-6 | MED | measured | The two constants are duplicated per host, equal but not identical, so a one-sided edit is silent. | `oc.SUCCESS_STATES is agy.SUCCESS_STATES` -> `False`; `==` -> `True` |
| F-7 | MED | `oc_runipd.py:3504` | The orchestrator dispatch bar already passes `EXECUTION_SUCCESS_STATES` explicitly and is NOT a `SUCCESS_STATES` read, so it needs no change and must not be "fixed". | source read |
| F-8 | MED | `.aw/records/specs/20260826-0718-01-...spec.md` §5.6 | The approved spec's per-item outcome vocabulary has no `needs-approval` token, but its `needs_input` ("a human gate stopped the item") fits exactly. So E-03 either reuses that name or amends the spec; it may not invent a third. | spec read |

## Proposed changes (ordered, validatable)

1. E-01 classifies the twelve call sites and records the classification at both constants, changing no behavior.
2. E-02 adds ONE shared action-aware predicate in `runner_shared` and routes the exit code, the glyph pair, and `all_success` through it on both hosts.
3. E-03 makes the needs-approval fact explicit and durable on the queue item, under a name the spec already has or a spec-amended one.
4. E-04 pins the cross-host equality and the new predicate's object identity.
5. E-05 tests the measured execute case AND the review-mode control that a naive fix breaks.
6. E-06 mutation-checks both guards.

## Deferred / out of scope (with reason)

- MAKING A `reviewed` PLAN EXECUTABLE. That is the auto-approval bridge (executed plan `97df1z`, `reviewed -> auto-approved` under `--full-auto`), deliberately not widened here. This plan makes the no-op HONEST, not absent.
- The per-artifact output line (child 02 `m85gxh`) and the end-of-run summary (child 03 `bsc457`). This child owns only what a disposition MEANS.
- Unifying the two duplicated constants into one shared object: `rununify` owns the extraction and `cnwy8g` owns the layering. This plan pins their equality instead, which is the cheap durable guard.
- Any change to `determine_action`'s routing. Routing a `reviewed` plan to `execute` is arguably also wrong, but changing it would alter which items a selector picks up, which is a different and larger decision.
- The `render_stream` COMPLETED tuple (`:1872`) and the diagnostics allowlist (`:2152`). The tuple is a RENDERER-local copy of the same idea and pending plan `r2i1b1` is editing that block; child 03 handles the renderer side after `r2i1b1`'s fence is known. Recorded here rather than silently left out, because a reader will notice `reviewed` in that tuple and wonder.

## Scope check

- Over-scope: none. `runner_shared.py` is in scope ONLY to hold the new shared predicate. Do NOT change `determine_action` or `action_for`.
- Under-scope: stated rather than left as `none`. This child does not make the needs-approval fact appear in `aw runs`, in `--json`, or in the summary table; those are children 02/03 and pending plan `r2i1b1`.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. `tests/test_runner_shared.py` holds the cross-host wrapper and call-site-count pins (its `WrapperTests::test_no_call_site_was_rewritten` counts `save_state` call sites per runner), so adding a call site there is deliberate and must be reflected rather than worked around. `tests/test_runner_refork_guard.py` is the symmetric sharing guard and its `REFORK_TABLE` is the place a newly shared symbol is registered.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) §5.6 owns the per-item outcome vocabulary and the run exit-code table. TWO OBLIGATIONS FOLLOW.
FIRST, OQ-01 decides whether this plan amends it. If E-03 reuses `needs_input`, NO amendment is needed and this section records that; if E-03 needs a new token, the spec file MUST be added to `- Scope-Paths:` before execution, because the runners announce declared spec edits before a run starts and the finalize scope gate reconciles declared against actual.
SECOND, THE EXIT-CODE TABLE MAY BE AFFECTED. §5.6's table says exit 1 means "at least one item failed, ended `dependency_not_met`, or ended `ran`/`unavailable` without `--unverifiable-ok`". A needs-approval item is none of those, and the spec's exit 3 is "Human input or explicit acknowledgement is required", which is a closer fit. Determine which exit code this case should produce, state the answer, and if it is 3, check whether the shipped drivers can return it at all (they return only 0/2/130/143 today, per the spec's own §5.6 note). Do NOT edit §4.2's finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Does the needs-approval disposition take spec `25kzda` §5.6's `needs_input` name, or a new token requiring a spec amendment?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer only if a spec amendment is chosen
- Resolution or deferral rationale: NOT blocking, because both answers are implementable and the choice is bounded. `needs_input` already exists in the approved vocabulary and its gloss ("a human gate stopped the item") describes this case exactly, so it needs no amendment and is the cheaper answer. A new token is defensible if `needs_input` is already load-bearing for a different case in shipped code (check before deciding: grep for it), but it costs a spec amendment plus a `Scope-Paths` declaration. Inventing a token present in neither the spec nor `TERMINAL_STATES` is not an option. Recorded as an OQ rather than pre-decided because the grep result decides it and must be run, not guessed.

### OQ-02: Should the run's exit code for an all-needs-approval queue be 1 or spec `25kzda`'s 3?

- Blocking: no
- Status: open
- Owner: this plan's executor, with the maintainer for the operational preference
- Resolution or deferral rationale: NOT blocking, because ANY nonzero exit fixes the measured defect (the silent 0), so the plan is executable under either answer and the choice is a refinement. Spec §5.6 assigns 3 to "Human input or explicit acknowledgement is required", which fits, but the shipped drivers return only 0/2/130/143 and the spec itself records an unreconciled conflict between its exit table and `run_cli.py`'s. If reaching 3 requires touching that reconciliation, prefer 1 and record why, since the spec explicitly warns that whoever binds those codes must reconcile BOTH tables rather than assume the spec row is authoritative.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the classification comment as written at BOTH constants. Paste a fresh grep of `SUCCESS_STATES` in both hosts showing the site count and, for each site, which of the five questions the comment assigns it. If the count differs from this plan's seven and five, say so and explain: both files are edited by live runs and the numbers will move.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new predicate as written and its location in `runner_shared.py`. Paste a `python3 -c` showing it resolves to the SAME object from `oc_runipd`, `agy_runipd` and `runner_shared`. Then paste FOUR evaluations: a `reviewed` EXECUTE item failing all three of exit-code success, checkmark glyph, and `all_success`; and a `reviewed` REVIEW item satisfying all three. Show the exit code for an all-`reviewed`-execute queue is nonzero, pasting the actual returned integer.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the durable needs-approval fact as it appears in a real `state.json` queue entry, not as a code snippet. State which name OQ-01 resolved to and paste the grep that decided it. If `TERMINAL_STATES` was widened, paste the measurement of its readers (`cascade_dependency_blocked` and `decide_orchestrator_dispatch`) showing the widening changed neither dependency nor retirement behavior; if it was not widened, say so.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the equality test and the object-identity assertion, and paste them PASSING. Then paste the pre-change measurement (`is` -> False, `==` -> True) so the reader can see what the test pins and what it deliberately does not.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste both tests per host and their actual runner output. The REVIEW-MODE CONTROL is the load-bearing half: paste it passing and state explicitly that it covers the failure the docstring at `oc_runipd.py:4186` records (run `run-20260904T042705Z-1025943`). A V-05 that pastes only the execute case is incomplete.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: for EACH of the two guards, paste the mutation, the FAILING output under it, the revert, and the passing output after. Two mutations, two failures, two passes, all four outputs pasted verbatim.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the six paths in `- Scope-Paths:`. Do NOT remove `reviewed` from `SUCCESS_STATES` (F-5). Do NOT change `determine_action` or `action_for`. Do NOT make a `reviewed` plan executable. Do NOT add a symbol to `oc_runipd` for `agy_runipd` to import. Do NOT edit `render_stream.py` (child 03 and pending plan `r2i1b1` own that surface). Do NOT edit spec `25kzda` unless OQ-01 resolves to a new token, and never its §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs; measured, their line numbers moved roughly 70 and 95 lines in a single day. Find `SUCCESS_STATES`, `EXECUTION_SUCCESS_STATES`, `edge_satisfied`, `cascade_dependency_blocked`, `determine_action`, `action_for`, `render_continuation_hint`, and `deliberate_stop_exit_code` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved zz5yxq --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. Do NOT close backlog `em0z50` here: its fixes (b) and (c) ship in children 02 and 03, and closing it after this plan would claim reporting behavior no code yet produces.
