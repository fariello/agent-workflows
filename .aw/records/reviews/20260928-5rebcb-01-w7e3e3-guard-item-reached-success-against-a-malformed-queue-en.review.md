# Review findings: plan w7e3e3

- Subject-Id: w7e3e3
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `abb2b307` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize --agent`
conforms after revision with `findings: 0`. No pre-review snapshot was owed: the plan was committed
and unmodified (`git status --porcelain` clean, the plan's only commit is `7b2a4500`), and the
lane-input copy at `.aw/state/lane-inputs/rev-1/` is byte-identical to the tracked file (`diff`
reported no difference).

THE DEFECT IS REAL, THE FAIL-CLOSED DIRECTION IS RIGHT, AND THE PLAN'S HONESTY WORK IS EXEMPLARY.
Three things this plan did that most do not: it MEASURED that its own backlog item under-reported the
blast radius and said so (F-02), it MEASURED that its own stated motive would not be met by its own
named fix and said so in a Findings row, a Scope-check Under-scope paragraph AND a gate warning
(F-05/F-06), and it FILED three carrier backlog items during authoring rather than leaving the gap in
prose. None of that is disturbed by this review.

WHAT REVIEW FOUND IS THAT THE FIX AS WRITTEN WOULD NOT HAVE FIXED HALF OF WHAT THE PLAN CLAIMED.

**ONE GUARD DOES NOT FIX BOTH CALLERS (PR-001, BLOCKER).** The plan's Scope, Goal, E-01, E-02 and V-02
all rest on "one guard fixes both", and it is false. `exit_code_statuses` opens its loop body with its
own `status = item.get("status")` to test the `queued` literal, and that read runs BEFORE the
`elif item_reached_success(item)` branch. PROVED by monkeypatching an `isinstance(item, Mapping)`-guarded
`item_reached_success` into the module: the guarded predicate returned `False` for `"not-a-mapping"`,
`render_continuation_hint` DID return its resume footer, and `exit_code_statuses(["not-a-mapping"])`
STILL raised `AttributeError` from `runner_shared.py:25537`. The plan's own F-02 explains the crash by
the wrong mechanism ("because its `elif item_reached_success(item)` branch is reached"), and the
unpatched traceback's crash frame is `exit_code_statuses`, not the predicate. Left as authored, E-02's
Expected outcome ("`render_continuation_hint` and `exit_code_statuses` both return") would have been
FALSE on completion, and an executor pasting V-02's demanded probe would have hit a traceback with no
plan step authorizing a second guard.

**THE PROJECTED TOKEN IS A LOAD-BEARING DECISION AND THE PLAN DID NOT MAKE IT (PR-002, HIGH).** Once a
guard is added to `exit_code_statuses`, that branch must choose what the malformed entry projects onto,
and the obvious choice is wrong. `runner_stop.deliberate_stop_exit_code` special-cases the literal
`"queued"` to excuse an item a deliberate stop never started; a malformed entry plainly did not run, so
`"queued"` is the spelling a reader reaches for. Measured both ways: `["queued"]` -> exit 1 not-stopped
but exit **0** under `stopped=True`; a distinct sentinel -> exit 1 on both arms. So the intuitive
spelling silently converts the fail-closed guard into a manufactured success for every stopped run,
which is what `EXIT_SUCCESS_TOKEN`'s own comment and spec `c4gd2h` R22 exist to prevent. E-01's
assertion as authored ("projects onto something that is NOT `EXIT_SUCCESS_TOKEN`") would have PASSED
for the `"queued"` spelling.

**TWO CITATIONS WERE STALE, BOTH LOAD-BEARING FOR THE SCOPE ARGUMENT (PR-003, MEDIUM).** F-11 and
OQ-01's rationale both rest on a collision with "two OPEN items". `b7oicl` is NOT open: it graduated
2026-09-28 (`c763a2fa`, which post-dates this plan's authoring commit `7b2a4500`) into pending plan
`4po0sc`, whose fence is `render_stream.py` plus a new test file and explicitly excludes exit-code and
status work - so it does not collide with `s438xd` at all. And `mjrac4` does not touch
`render_run_summary_table`, which F-11 asserts twice; it names `derive_item_disposition` and
`render_stream`'s DIAGNOSTICS block. The scope decision is still correct, but for a different reason
(the design-decision count and the module boundary), and a reader checking the stated reason would
have found it false.

**A FOURTH UPSTREAM CRASH SITE WAS UNCOUNTED (PR-004, MEDIUM).** F-05 enumerates the exit tail as five
calls and measures four. There are six, and `render_queue_dispositions` (a separate statement in both
hosts' tails, reaching the same `derive_item_disposition`) also raises. Separately, the measurement
surfaced the in-tree PRECEDENT for tolerating this input rather than dying on it: `report_run_spec_edits`
CATCHES the `AttributeError` and prints "SPEC CHANGES: could not be computed (AttributeError)".

**AND THE DELIBERATELY-UNFIXED SITE IS IN THE PLAN'S OWN SCOPE-PATH FILE (PR-005, MEDIUM).** The
`fcodik` deferral describes `write_report` as though it were out of reach, but
`runner_shared.write_report` lives in `agent_workflows/runner_shared.py`, which this plan edits. The
exclusion is a judgement, not a module boundary, and an executor already in that file will be tempted
to fix a one-line crash they can see. Saying so is what makes the deferral hold.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness / G. Plan executability | `runner_shared.exit_code_statuses` loop body (`status = item.get("status")` precedes `elif item_reached_success(item)`), crash at `runner_shared.py:25537`; plan Scope ("so both its shared exit-path callers survive"), Goal ("neither of its two exit-path callers"), E-01 ("one guard fixes both"), E-02 Expected outcome ("`render_continuation_hint` and `exit_code_statuses` both return"), F-02 ("because its `elif item_reached_success(item)` branch is reached"); monkeypatch probe: guarded predicate `False`, footer RETURNED, `exit_code_statuses(["not-a-mapping"])` STILL RAISED | **THE SINGLE GUARD THE PLAN PROPOSES DOES NOT FIX THE SECOND CALLER IT NAMES AS HALF ITS VALUE.** `exit_code_statuses` crashes in its OWN `.get`, which executes BEFORE the predicate is consulted, so the guarded predicate is never reached. The plan would have completed with a FALSE Expected outcome, and an executor pasting V-02's demanded probe would have hit a traceback with no authorized step to fix it. The plan's F-02 also explains the crash by the wrong mechanism, so the error is in the analysis and not only in the wording. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | Split into E-02 (predicate guard) and a NEW E-03 (independent guard in `exit_code_statuses`, with the token decision); old E-03 renumbered E-04; `Highest E allocated` 03 -> 04; V rebuilt 3 -> 4 with V-02 now demanding a SECOND red demonstration whose crash frame is `exit_code_statuses`. Scope, Goal, F-02 and the Under-scope paragraph corrected. New F-02a records the measurement. |
| PR-002 | HIGH | UNDER-SCOPE | A. Correctness / B. fail-closed direction | `runner_stop.deliberate_stop_exit_code`'s `if status != "queued"` comprehension; measured projections: `["queued"]` -> exit 1 / exit **0** under stop, sentinel -> exit 1 / exit 1; `EXIT_SUCCESS_TOKEN`'s comment ("deliberately not a real status, and deliberately not spellable as one"); spec `c4gd2h` R22; E-01's authored assertion (only `NOT EXIT_SUCCESS_TOKEN`) | **THE INTUITIVE TOKEN SILENTLY DESTROYS THE FAIL-CLOSED GUARANTEE UNDER A GRACEFUL STOP, AND THE PLAN'S OWN ASSERTION WOULD NOT HAVE CAUGHT IT.** A malformed entry did not run, so `"queued"` is the spelling a reader reaches for; it is the one literal the consumer special-cases, so an unreadable queue would exit 0 for any stopped run. E-01 asserted only that the projection is not `EXIT_SUCCESS_TOKEN`, which `"queued"` satisfies. The plan named no token at all, leaving the highest-consequence choice in the fix to executor improvisation. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | E-03 now REQUIRES a new module-level sentinel that is neither token, forbids `str(status)` for this case with the reason, and states the measurement. E-01 asserts the projection is neither `EXIT_SUCCESS_TOKEN` nor `"queued"` AND that `deliberate_stop_exit_code` is 1 under BOTH stop arms. V-03 demands the post-fix both-arms measurement and a no-projection-change probe over the cross product. New F-02b records it; the gate names it as the second silent-failure mode. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness (provenance) / F. Honest documentation | `b7oicl` front matter (`- Status: graduated`, `- Graduated-To: b7oicl`), `git log` -> `c763a2fa` 2026-09-28 02:54 versus plan authoring `7b2a4500` 2026-09-28 00:58; `4po0sc` `- Scope-Paths: agent_workflows/render_stream.py, tests/test_zero_dispatch_outcome.py` and `- Scope:` ("No exit code"); `mjrac4` body (names `derive_item_disposition` and `render_stream`'s diagnostics block, never `render_run_summary_table`) | **BOTH CITATIONS CARRYING THE SCOPE ARGUMENT ARE STALE OR WRONG.** F-11 and OQ-01 rest on colliding with "two OPEN items"; `b7oicl` graduated into a pending plan whose fence explicitly excludes exit-code work, so there is no collision, and `mjrac4` does not touch the function F-11 twice says it does. The scope decision survives, but a reader checking its stated basis would find it false, and F-11's whole purpose is to prove E-04 files no duplicate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 rewritten with `b7oicl`'s real status, its graduation commit and date relative to this plan's authoring, `4po0sc`'s declared fence, and `mjrac4`'s real subject; both corrections marked as made at review. OQ-01's rationale re-grounded on the design-decision count and the module boundary, with the superseded collision claim explicitly retracted. The `3z91mq` deferral row drops `b7oicl`. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness / E. Testing | `oc_runipd.run_queue` tail (`write_report` :3932, `render_run_summary_table` :3940, `render_queue_dispositions` :3982, `render_disposition_summary` :4010, `render_continuation_hint` :4014, `exit_code_statuses` :4044); `agy_runipd.py` :3402-:3471 identical; six probes measured, four raise; `report_run_spec_edits` CATCHES and prints "SPEC CHANGES: could not be computed (AttributeError)" | **THE EXIT TAIL HAS SIX CALLS AND FOUR CRASH SITES, NOT FIVE AND THREE.** `render_queue_dispositions` is a separate statement in both hosts' tails, reaches the same `derive_item_disposition`, and raises the same `AttributeError`; F-05 omits it, so V-04's "four-probe" evidence would have under-counted the very gap the plan exists to bound honestly. The probe also surfaced the in-tree PRECEDENT for tolerating this input (`report_run_spec_edits` catches it), which strengthens the plan's fail-closed argument and was unrecorded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 rewritten: six calls enumerated with both hosts' line anchors, four measured crashes, and the `report_run_spec_edits` precedent recorded. The `3z91mq` deferral row, Concern, Under-scope paragraph, OQ-01, E-04 and V-04 all raised to five probes / four upstream sites. |
| PR-005 | MEDIUM | UNDER-SCOPE | C. Architecture / G. Plan executability | `runner_shared.write_report`'s `counts[item["status"]] = counts.get(item["status"], 0) + 1`; plan `- Scope-Paths: agent_workflows/runner_shared.py`; `fcodik` deferral row as authored | **THE DEFERRED SITE IS IN THIS PLAN'S OWN EDIT FILE, WHICH THE DEFERRAL DID NOT SAY.** The `fcodik` row reads as a module-boundary exclusion; it is a judgement call about a function the executor will have open, and a one-line crash in your own file is exactly what gets fixed opportunistically. Doing so would ship a behavior change this plan's tests say nothing about and would silently absorb another item's work. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The `fcodik` deferral now states the site is in an in-scope file, gives the exact crashing expression, and forbids the opportunistic fix with the reason. The gate carries a dedicated paragraph, and V-03 requires the diff to show `write_report` visibly unmodified. |
| PR-006 | LOW | UNDER-SCOPE | E. Testing / G. executability | Required tests as authored (one deliberate-failure demonstration, one no-verdict-change probe); PR-001's two-guard split | The validation plan had one red demonstration and one equivalence probe, both aimed at the predicate. With two independent guards, the interesting red state is the one AFTER E-02 and BEFORE E-03 (footer green, projection still crashing), and the projection needs its own equivalence probe: a token change is invisible to a passing suite because no shipped test asserts the projection of a malformed entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests gains the SECOND red demonstration (crash frame at `exit_code_statuses`) and a NO-PROJECTION-CHANGE probe comparing projections AND exit codes on both stop arms over the cross product. V-02 and V-03 each demand their half, and V-02 states why an executor is most likely to skip the second red run. |
| PR-007 | LOW | IN-SCOPE | G. Plan executability (scope fence wording) | Plan gate as authored (path-scoped commit, never-push, paste-actual-output all present; no out-of-scope-edit clause); workflow Step 4 scope-fence ruling of 2026-09-01 | The gate carried every required execution-contract element except a statement of what to do about an out-of-scope edit. The correct wording is MAKE-AND-JUSTIFY (finalize refuses without a `--scope-reason`), not stop-and-report; adding it closes the gap without importing the wording the 2026-09-01 ruling forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate's executor paragraph now states that an out-of-scope edit is made and then justified with a `--scope-reason`, and explicitly that it is not a reason to stop. No "STOP and report" clause was added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | `exit_code_statuses` needs its own guard (PR-001). Add a second E-item to this plan, or file it as separate work and let this plan ship the predicate guard alone? | ADD IT HERE, as E-03. | (a) File a separate backlog item: rejected, because the plan ALREADY names `exit_code_statuses` as half its value in Scope, Goal, E-01 and V-02, so shipping without it leaves a plan whose own Expected outcome is false and whose test cannot go green. (b) Drop the `exit_code_statuses` claims and narrow the plan to the footer: rejected, it discards F-02, which is the plan's own best finding (the exit code, not a printed line, is the more serious of the two crashes). | The monkeypatch measurement (guarded predicate + still-raising projection); the plan's four textual claims that the projection is fixed; both functions are in the SAME FILE already declared in `- Scope-Paths:`, so no fence widening is needed. | yes |
| D-2 | What token should a malformed entry project onto (PR-002)? | A NEW module-level sentinel, neither `EXIT_SUCCESS_TOKEN` nor `"queued"`; E-03 mandates it and E-01/V-03 pin the resulting exit code on both stop arms. | (a) `"queued"`: rejected on measurement, it yields exit **0** under `stopped=True`, manufacturing a success for an unreadable queue. (b) `str(item)`: rejected, it injects arbitrary corruption-controlled text into the exit-code vocabulary. (c) Leave the choice to the executor: rejected, it is the highest-consequence decision in the fix and E-01's authored assertion would not have caught the wrong answer. | Direct evaluation of `runner_stop.deliberate_stop_exit_code` over both candidates under `stopped` both ways; `EXIT_SUCCESS_TOKEN`'s own comment requiring a token "deliberately not spellable as" a real status; spec `c4gd2h` R22. | yes |
| D-3 | Does E-03's new exit-code behavior for a malformed entry need a spec amendment against `c4gd2h` A1/A4? | No. | Amend `c4gd2h`; declare the spec in `- Scope-Paths:` to be safe. | A1/A4 govern a deliberate stop whose remaining items are `queued`, a state a malformed entry cannot be SHOWN to be in, so exiting 1 for it neither contradicts nor weakens them; R22 forbids rewriting a status on disk, and the projection is in-memory and rewrites nothing (its own docstring: "THIS REWRITES NOTHING"). Recorded in the plan's Spec / documentation sync section so a later reader sees the check was made. | yes |
| D-4 | OQ-01's scope rationale rested on a collision that no longer exists (PR-003). Re-open the question, or re-ground the same answer? | RE-GROUND the same answer (STAY AND CARRY), with the retraction stated. | Re-open it as an OPEN question for the human: rejected, the decision does not depend on the stale citation. Widening remains wrong for reasons that are still true (two extra modules plus an unrelated function in this plan's own file, and three separate design decisions about what an unreadable entry renders/counts/disposes as). | `b7oicl`'s `- Status: graduated` and `4po0sc`'s declared fence (which excludes exit-code work); `mjrac4`'s body; `derive_item_disposition`'s own out-of-fence comment as the in-repo precedent for report-rather-than-reach. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. Both pre-existing open questions (OQ-01, OQ-02) remain `resolved` and non-blocking; OQ-01's
rationale was re-grounded per D-4 and OQ-02's answer is unaffected, since its "in the predicate, not in
the callers" reasoning is orthogonal to the fact that one caller ALSO needs its own guard.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`
  after all edits (the E-02/E-03 split, E-04 renumber, `Highest E allocated` 03 -> 04, V rebuild to 4,
  `Readiness` written, `Status` to `reviewed`).
- Lane input identity: `diff .aw/state/lane-inputs/rev-1/plan-20260928-5rebcb-01-w7e3e3-....ipd.md
  .aw/records/plans/pending/20260928-5rebcb-01-w7e3e3-....ipd.md` -> no difference; `git status
  --short` clean before editing, so no pre-review snapshot was owed.
- F-01 reproduced: `oc_runipd.render_continuation_hint({"repo":"/repo","run_id":"run-xyz",
  "set_sessions":{},"queue":["not-a-mapping"]}, Path("/x"))` -> `AttributeError: 'str' object has no
  attribute 'get'`, final frame `runner_shared.py:25476 in item_reached_success`, `status = item.get("status")`.
- F-02 reproduced AND its mechanism corrected: `runner_shared.exit_code_statuses(["not-a-mapping"])`
  -> same `AttributeError`, but the traceback frame is `runner_shared.py:25537 in exit_code_statuses`,
  its OWN `status = item.get("status")`, NOT the predicate.
- F-02a, the finding that changed the plan: monkeypatched an `isinstance(item, Mapping)`-guarded
  `item_reached_success` into `runner_shared` and re-ran both calls.
  `item_reached_success("not-a-mapping")` -> `False`; `render_continuation_hint` -> RETURNED, with
  `aw oc run resume --repo /repo run-xyz` present and `aw runs` absent (the correct resume branch);
  `exit_code_statuses(["not-a-mapping"])` -> STILL RAISED from `runner_shared.py:25537`.
- F-02b, the token measurement, via `runner_stop.deliberate_stop_exit_code(..., success_states=
  {EXIT_SUCCESS_TOKEN}, stopped=S)`:
  - `["queued"]` -> `stopped=False` exit 1, `stopped=True` exit **0**.
  - `["aw-item-entry-was-unreadable"]` (a candidate sentinel) -> exit 1 on BOTH arms.
  - `[{"status":"executed","action":"execute"}]` -> exit 0 both arms (unchanged control).
  - `[{"status":"executed","action":"execute"}, "not-a-mapping"]` -> exit 1 both arms.
- F-04 identity probe: `oc_runipd.item_reached_success is runner_shared.item_reached_success` -> True;
  `agy_runipd.item_reached_success is ...` -> True; the same two for `exit_code_statuses` -> True, True.
  `tests/test_runner_shared.py:408-410` pins these with `assertIs`.
- F-05 re-measured as SIX probes against the same malformed state, in both hosts' tail order:
  - `write_report` -> `TypeError: string indices must be integers, not 'str'`, from
    `runner_shared.py:26075`, `counts[item["status"]] = counts.get(item["status"], 0) + 1`.
  - `render_run_summary_table` -> `AttributeError: 'str' object has no attribute 'get'`.
  - `render_queue_dispositions` -> same `AttributeError` (**the site F-05 omitted**).
  - `render_disposition_summary` -> same `AttributeError`.
  - `render_continuation_hint` -> same `AttributeError`.
  - `exit_code_statuses` -> same `AttributeError`.
  - `report_run_spec_edits` -> RETURNED, printing `SPEC CHANGES: could not be computed
    (AttributeError); the run is starting anyway.` (the in-tree tolerate-rather-than-die precedent).
- Both hosts' exit tails read and confirmed identical in order: `oc_runipd.py:3932/:3940/:3982/:4010/
  :4014/:4044` and `agy_runipd.py:3402/:3410/:3428/:3446/:3450/:3471`.
- F-07 confirmed: `runner_shared.py:140-147` imports `Mapping` from `collections.abc`; the module also
  already imports `Sequence`, which `exit_code_statuses` is annotated with. No import is owed for
  either guard.
- F-11 corrections: `b7oicl` front matter reads `- Status: graduated`, `- Graduated-To: b7oicl`;
  `git log` on it -> `c763a2fa` 2026-09-28 02:54, versus this plan's authoring commit `7b2a4500`
  2026-09-28 00:58, so it graduated AFTER authoring and `c763a2fa` is in current HEAD's history.
  Pending plan `4po0sc` declares `- Scope-Paths: agent_workflows/render_stream.py,
  tests/test_zero_dispatch_outcome.py` and `- Scope:` "ONLY the `COMPLETED` branch ... No exit code".
  `mjrac4` (`open`, `chore`) names `derive_item_disposition` and `render_stream`'s diagnostics block,
  and the string `render_run_summary_table` does not appear in it.
- Carrier items confirmed live: `s438xd`, `3z91mq`, `fcodik` all present in
  `.aw/records/backlog/open/`, each `- Status: open`, `- Work-Kind: bug`, `- Blocks-Release: next`.
  `aw find backlog s438xd` -> `open s438xd`. All three were committed with the plan in `7b2a4500`.
  Their bodies were read in full and each correctly describes its own crash site and exception.
- Source-of-origin item `5rebcb` read: `- Status: graduated`, `- Graduated-To: 5rebcb`,
  `- Blocks-Release: next`, `- Work-Kind: bug`. The plan's `- From-Backlog: 5rebcb` and inherited
  `- Blocks-Release: next` are both correct.
- Test-coverage census for F-09: `item_reached_success` appears in `tests/` only at
  `tests/test_runner_shared.py:408` (identity loop) and `tests/test_inlane_retirement_lands.py:147,157`
  (well-formed items). `exit_code_statuses` appears in `test_runner_shared.py`,
  `test_liftaudit_stop_halts_run.py:194`, `test_action_table_runner_parity.py:460,469,478` and
  `test_typed_queue_entries.py:606,617,630`. None passes a non-mapping entry, so E-01 is new coverage
  and no shipped test asserts the projection this plan changes - which is exactly why PR-002's token
  error would have been invisible to a green suite.
- F-12 baseline re-measured at this HEAD with a BARE run: `2935 passed, 2 skipped, 3 warnings in
  44.64s` (the plan records `in 53.07s` from authoring; the count matches, the duration is machine load).
- `success_states_for_action` read at the symbol and its four bars enumerated
  (`SUCCESS_STATES`, `EXECUTE_OR_RETIRED_REPORTING_SUCCESS_STATES`, `SKIP_REPORTING_SUCCESS_STATES`,
  `PLAN_REPORTING_SUCCESS_STATES`), confirming the cross product the two equivalence probes must cover.
- `no_turn_was_attempted` read at the symbol: it guards `isinstance(item, dict)` inside itself and
  documents the fail-closed direction, confirming F-01's and OQ-02's in-module precedent claim.
- No code, test, or configuration file was modified by this review. It edited the plan and wrote this
  record. Every probe ran in-process via `python3 -c`-style heredocs against temporary directories from
  `tempfile.mkdtemp()`; no repository file was written by a probe.
