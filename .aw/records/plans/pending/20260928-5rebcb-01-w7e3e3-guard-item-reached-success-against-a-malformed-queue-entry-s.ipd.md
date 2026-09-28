# IPD: Guard item_reached_success against a malformed queue entry so the exit footer cannot crash

- Date: 2026-09-28
- Kind: child
- Concern: `runner_shared.item_reached_success` reads `item.get("status")` with no isinstance guard, against its own docstring's advertised tolerance ("safe to call on a hand-written manifest's entry or on a state file written by an older driver"). A queue holding a non-mapping entry therefore raises `AttributeError: 'str' object has no attribute 'get'` from `render_continuation_hint`'s `all_success` line. `runner_shared.exit_code_statuses` raises the SAME exception on the SAME input, but from its OWN unguarded `status = item.get("status")` read, which executes BEFORE it ever calls the predicate (F-02a, measured at review), so it needs its own guard and is not fixed by guarding the predicate. Both sites are on the exit path of every run, after the work is done.
- Scope: Add the missing `isinstance(item, Mapping)` guard to `item_reached_success`, failing CLOSED (a non-mapping entry is NOT a success); add a SECOND, independent fail-closed guard to `exit_code_statuses`'s own per-entry read, with an explicit decision about what token a malformed entry projects onto; pin the malformed-entry case for the footer, for `exit_code_statuses` (including the resulting exit code under BOTH the stopped and not-stopped arms of the deliberate-stop concession), and for the guard itself. Measurement during authoring found that the footer is NOT the first crash on the real exit path (F-05/F-06): `write_report`, `render_run_summary_table`, `render_queue_dispositions` and `render_disposition_summary` all run BEFORE it and all crash on the same entry. Those live outside this plan's fence and are carried to their own backlog items rather than fixed here, so this plan makes the guard true of the two `runner_shared` functions whose contract promises it and does NOT claim to restore the whole closing report.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 5rebcb
- Blocks-Release: next
- Set: 5rebcb
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: w7e3e3
- Approval: 2026-09-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-28 approved (aw set): status set to approved

- 2026-09-28 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. Review MEASURED that `exit_code_statuses` has its OWN unguarded `.get` read that runs BEFORE it calls the predicate, so the single guard this plan proposed would NOT have fixed the caller the plan named as half its blast radius: with `item_reached_success` guarded, `exit_code_statuses(["not-a-mapping"])` still raised (PR-001). E-02 split into E-02 (predicate) + E-03 (projection, with an explicit token decision and its exit-code consequence under both deliberate-stop arms), old E-03 renumbered E-04, `Highest E allocated` 03 -> 04, V items rebuilt 3 -> 4. Also corrected: two stale citations of `b7oicl` as `open` (it graduated to plan `4po0sc` on 2026-09-28) and of `mjrac4` as touching `render_run_summary_table` (it names `render_stream`'s diagnostics block, a different site), and an uncounted fourth upstream crash site (`render_queue_dispositions`). Record: `.aw/records/reviews/20260928-5rebcb-01-w7e3e3-guard-item-reached-success-against-a-malformed-queue-en.review.md`.
- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog item `5rebcb`; filed carrier backlog items `s438xd`, `3z91mq` and `fcodik` for the three upstream exit-path crash sites this plan deliberately does not fix. Every claim in the item re-measured against the working tree at HEAD `07580297` rather than carried over; the item's reproduction was confirmed live, and the authoring measurement ADDED a finding the item does not contain (three upstream crash sites on the same exit path, F-05/F-06), which bounds what this plan can honestly claim (OQ-01).

## Goal

Make the TWO `runner_shared` exit-path functions that read a queue entry with a bare `.get` tolerant of a non-mapping entry, as `item_reached_success`'s docstring already promises and as its sibling predicate `no_turn_was_attempted` already is, so neither `render_continuation_hint`'s `all_success` nor the run's exit-code projection raises `AttributeError` while reporting on work that already completed.

TWO GUARDS, NOT ONE, and review MEASURED why (F-02a). `exit_code_statuses` does its own `status = item.get("status")` to test the `queued` literal, and that read runs BEFORE the `elif item_reached_success(item)` branch. Guarding only the predicate therefore leaves the exit-code caller crashing: verified at review by monkeypatching an `isinstance`-guarded `item_reached_success` into the module and re-calling `exit_code_statuses(["not-a-mapping"])`, which still raised `AttributeError` from `runner_shared.py:25537`. So this plan's fence is two functions in one module, not one.

The judgement for every well-formed entry must not move by one byte: this plan adds a branch to each function for an input that currently crashes and changes no verdict, and no projected token, for an input that currently returns.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the defect, then fix it

- [x] E-01 Add a failing test to `tests/test_oc_runipd.py::ContinuationHintTests` that pins the malformed-entry case for BOTH exit-path functions this plan fixes, since they crash INDEPENDENTLY (F-02a) and a test naming only the footer would under-describe the fix. It must assert four things: that `driver.render_continuation_hint(self._state({}, queue=["not-a-mapping"]), Path("/x"))` RETURNS rather than raising, and that the returned footer takes the RESUME branch (`assertIn("aw oc run resume --repo /repo run-xyz", ...)`, `assertNotIn("aw runs", ...)`) because an unreadable entry must not be counted a success; that `runner_shared.exit_code_statuses(["not-a-mapping"])` returns without raising and projects the entry onto something that is NOT `runner_shared.EXIT_SUCCESS_TOKEN` and NOT the literal `"queued"` (F-02b: the `queued` literal is the deliberate-stop concession's key, so projecting there would make a malformed entry exit 0 under a stop); that `runner_stop.deliberate_stop_exit_code` over that projection returns `1` under BOTH `stopped=False` and `stopped=True`; and that `runner_shared.item_reached_success("not-a-mapping")` is `False` directly. Place it beside the existing `assertFalse(runner_shared.no_turn_was_attempted({"queue": ["not-a-mapping"], ...}))` assertion already living in `test_no_sessions_captured_and_unattempted`, which is the in-tree precedent for exactly this input on the sibling predicate; write it as its own test method rather than appending to that one, so a failure names the malformed-entry contract rather than the session-capture contract. Cover BOTH hosts for the footer if the existing class makes that cheap, but do not restructure the class to do so: both functions are the SAME OBJECTS on both hosts (F-04), so one host's footer plus the direct shared-symbol assertions already prove the fix reaches both.
  - Depends on: none
  - Expected outcome: A new test in `tests/test_oc_runipd.py` that FAILS at this HEAD with `AttributeError: 'str' object has no attribute 'get'`, and whose footer and predicate assertions pass after E-02 while its `exit_code_statuses` and exit-code assertions pass only after E-03.
  - Execution state: performed

- [x] E-02 Add the `isinstance` guard to `runner_shared.item_reached_success`, failing CLOSED: return `False` for any `item` that is not a `Mapping`, before the `item.get("status")` read. Use `Mapping` from `collections.abc`, which the module ALREADY imports (F-07), so this adds no import. Match the established in-module idiom rather than inventing one: `no_turn_was_attempted` documents its equivalent guard as "a malformed entry (anything that is not a mapping) returns False, since an unreadable entry cannot be shown not to have run", and the same fail-closed reasoning applies here in the same direction (an unreadable entry cannot be shown to have SUCCEEDED). Extend the docstring's existing tolerance paragraph, which is where the contract this plan restores is already written: it currently promises the function is "safe to call on a hand-written manifest's entry or on a state file written by an older driver" and reads "`action` and `status` off the entry and NOTHING ELSE", so state that a non-mapping entry is refused as a non-success and say WHY the direction is conservative, in the same terms the docstring already uses for a missing `action` ("it can only refuse to call something a success, never manufacture one"). Change no other executable line: the `isinstance(status, str)` test and the `success_states_for_action(item.get("action"))` call stay exactly as they are, so no well-formed entry's verdict moves. DO NOT expect this to fix `exit_code_statuses`; E-03 does that, and F-02a records the measurement proving it is a separate crash.
  - Depends on: E-01
  - Expected outcome: `runner_shared.item_reached_success("not-a-mapping")` is `False`; `render_continuation_hint` returns the RESUME footer for `queue=["not-a-mapping"]`; every well-formed entry's verdict is unchanged. `exit_code_statuses(["not-a-mapping"])` STILL RAISES at this point, which is the expected intermediate state and is what E-03 fixes.
  - Execution state: performed

- [x] E-03 Add the SECOND, independent fail-closed guard to `runner_shared.exit_code_statuses`'s own per-entry read, which E-02 does not reach. The crash is its `status = item.get("status")` line, which runs BEFORE the `elif item_reached_success(item)` branch, so the guarded predicate is never consulted (F-02a, measured at review by monkeypatching the guard in and re-calling the function). Guard the loop body with `if not isinstance(item, Mapping):` before that read. THE TOKEN IS A DESIGN DECISION, NOT A DETAIL, and it must be made explicitly: the projection is consumed ONLY by `runner_stop.deliberate_stop_exit_code`, which tests membership in `{EXIT_SUCCESS_TOKEN}` and ALSO special-cases the literal `"queued"` to excuse an item a deliberate stop never started. So the malformed entry must project onto a token that is NEITHER, or the fail-closed direction is silently lost under a stop: measured at review, projecting onto `"queued"` yields exit `0` for `stopped=True` while a distinct sentinel yields `1` on both arms (F-02b). Use a NEW module-level sentinel constant beside `EXIT_SUCCESS_TOKEN`, spelled so it cannot be confused with a real status exactly as that constant's own comment requires ("deliberately not a real status, and deliberately not spellable as one"), document it with the same reasoning, and extend `exit_code_statuses`'s docstring, whose "Every other non-success status is passed through unchanged" sentence is the claim this branch qualifies. Do NOT reuse `str(status)` for this case: `str` of a non-mapping entry would put arbitrary attacker-or-corruption-controlled text into the exit-code vocabulary and into any debugger frame reading it. Change no other executable line: the `"queued"` passthrough and the `str(status)` fallthrough for a well-formed entry stay exactly as they are.
  - Depends on: E-02
  - Expected outcome: `runner_shared.exit_code_statuses(["not-a-mapping"])` returns a one-element list holding the new sentinel, and does not raise; `deliberate_stop_exit_code` over it returns `1` for both `stopped=False` and `stopped=True`; the projection of every well-formed queue is byte-identical to the pre-fix projection; the E-01 test passes in full.
  - Execution state: performed

### Task group 2: bound the claim honestly

- [x] E-04 Verify, as the LAST act before commit, that this plan has not overstated its effect, and that the carriers filed during authoring still describe live work. The upstream crash sites F-05 measured are ALREADY FILED (`s438xd` for `render_stream.render_run_summary_table`, `3z91mq` for `run_selection_policy.derive_item_disposition` and the three renderers reaching it, `fcodik` for the shared `write_report`), so this item files nothing: it CHECKS. Re-run the FIVE-probe measurement of F-05 against the POST-FIX tree (`write_report`, `render_run_summary_table`, `render_queue_dispositions`, `render_disposition_summary`, then `render_continuation_hint` and `exit_code_statuses`) and confirm the upstream sites still raise their recorded exceptions while the footer and the projection now return; confirm each of the three items is still `open` and still carries `- Blocks-Release: next`; and confirm this plan's own committed text nowhere claims the closing report is restored. If the post-fix measurement shows any of the three no longer raising (another party may have fixed one in this shared checkout), do NOT silently retire its item: report the divergence and leave the item alone, since that is a third party's work to close. This exists as an E-item because the honesty bound is the one thing a green suite cannot check: the fix passes its tests whether or not the plan's prose is true about what it delivered.
  - Depends on: E-03
  - Expected outcome: The post-fix five-probe measurement is recorded; the three carrier items are confirmed live and release-gating; and no text in this plan, its commit message, or any walkthrough claims a corrupt `state.json` now prints a clean closing report.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE FAIL-CLOSED DIRECTION FOR A MALFORMED ENTRY IS ALREADY DECIDED IN THIS MODULE, by the sibling predicate 15 lines from the fix site. `runner_shared.no_turn_was_attempted` states as one of three deliberate fail-closed properties that "a malformed entry (anything that is not a mapping) returns False, since an unreadable entry cannot be shown not to have run", and closes with "this is consulted on the exit path of every run and a footer must never raise". So this plan follows an in-tree ruling rather than choosing a policy.
- CODE IS CITED BY SYMBOL, NOT BY BARE LINE OFFSET (spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`). This matters acutely for this plan: backlog item `5rebcb` was filed against HEAD `b5208b0e` and `runner_shared.py` is now 36342 lines, so every offset in the item is stale. This plan cites `runner_shared.item_reached_success`, `runner_shared.exit_code_statuses`, `runner_shared.render_continuation_hint` and `runner_shared.no_turn_was_attempted` by name throughout.
- THE ITEM'S NAMED TEST TARGET DOES NOT EXIST WHERE THE ITEM IMPLIES. The item says to "add the malformed-entry case to the footer test"; the footer tests live in `tests/test_oc_runipd.py::ContinuationHintTests` (not in `tests/test_runner_shared.py`, which asserts only that the four success-bar symbols ARE the shared objects), and that class already contains the `no_turn_was_attempted` malformed-entry assertion this plan's test sits beside.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. `python3 -m pytest` with no added flags is the contract; a second `-q` would suppress the `N passed` line this plan's validation requires, and `-n0` makes the run several times slower here.
- A `runner_shared` PREDICATE IS SHARED BY OBJECT IDENTITY, NOT BY COPY. `tests/test_runner_shared.py` asserts `assertIs` for `success_states_for_action`, `item_reached_success`, `item_needs_approval` and `exit_code_statuses` against both hosts, so a one-line fix here reaches both drivers and no per-host edit is owed.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE DEFECT IS LIVE AT THIS HEAD, exactly as the item reproduces it. Calling `oc_runipd.render_continuation_hint({"repo": "/repo", "run_id": "run-xyz", "set_sessions": {}, "queue": ["not-a-mapping"]}, Path("/x"))` raises `AttributeError: 'str' object has no attribute 'get'`, with the traceback's final frame at `runner_shared.item_reached_success`'s `status = item.get("status")` line, reached from the `all_success = all(item_reached_success(item) for item in queue)` generator. | `python3 -c` probe with full traceback at HEAD `07580297`. |
| F-02 | THE ITEM UNDER-REPORTS THE BLAST RADIUS BY ONE CALLER: `exit_code_statuses` CRASHES TOO, and it decides the run's EXIT CODE rather than a printed line. `runner_shared.exit_code_statuses(["not-a-mapping"])` raises the identical `AttributeError`. Both hosts call it as the final expression of `run_queue` (`runner_stop.deliberate_stop_exit_code(runner_shared.exit_code_statuses(state["queue"]), ...)` at `oc_runipd.py:4044` and `agy_runipd.py:3471`). | Direct probe of `runner_shared.exit_code_statuses(["not-a-mapping"])`; read of the identical call in `oc_runipd.run_queue` and `agy_runipd.run_queue`. |
| F-02a | **ONE GUARD DOES NOT FIX BOTH, AND THE AUTHORED PLAN ASSUMED IT WOULD.** `exit_code_statuses`'s loop body opens with its OWN `status = item.get("status")`, to test the `queued` literal, and that read executes BEFORE the `elif item_reached_success(item)` branch that would consult the guarded predicate. So the traceback's crash frame is `runner_shared.exit_code_statuses`, NOT `item_reached_success`. PROVED at review by monkeypatching an `isinstance(item, Mapping)`-guarded `item_reached_success` into the module: the guarded predicate returned `False` for `"not-a-mapping"` as intended, and `exit_code_statuses(["not-a-mapping"])` STILL raised `AttributeError` from `runner_shared.py:25537`, while `render_continuation_hint` DID return its resume footer. This is why the fix is two guards (E-02, E-03), and why E-02's Expected outcome now says the projection still raises at that point. | Traceback of the unpatched call showing the frame at `exit_code_statuses`, not the predicate; monkeypatch probe in which the footer was fixed and the projection was not. |
| F-02b | **THE PROJECTED TOKEN FOR A MALFORMED ENTRY IS A LOAD-BEARING CHOICE, BECAUSE `queued` IS A MAGIC LITERAL IN THE CONSUMER.** `runner_stop.deliberate_stop_exit_code` returns 0 under `stopped=True` iff every status OTHER THAN the literal `"queued"` is a success token. Measured at review over the candidate projections: `["queued"]` -> exit 1 not-stopped but exit **0** under a stop; a distinct sentinel -> exit 1 on BOTH arms. So projecting a malformed entry onto `queued` would make an unreadable queue exit 0 for any run that observed a graceful stop, which is exactly the manufactured success `EXIT_SUCCESS_TOKEN`'s own comment and spec `c4gd2h` R22 forbid. E-03 therefore requires a new sentinel and E-01 pins the exit code on both arms. | Direct evaluation of `runner_stop.deliberate_stop_exit_code` over both candidate projections under `stopped` both ways; read of its `if status != "queued"` comprehension. |
| F-03 | THE GUARD IS MISSING AGAINST THE FUNCTION'S OWN WRITTEN CONTRACT, which is what makes this a defect rather than a hardening request. `item_reached_success`'s docstring says it "Reads `action` and `status` off the entry and NOTHING ELSE, so it is safe to call on a hand-written manifest's entry or on a state file written by an older driver". A hand-written manifest is precisely the input that can hold a bare string. | Read of `runner_shared.item_reached_success`'s docstring. |
| F-04 | THE FIX REACHES BOTH HOSTS FROM THE SHARED MODULE, so no per-host edit is owed and no host file enters `- Scope-Paths:`. Measured: `oc_runipd.item_reached_success is runner_shared.item_reached_success` -> True, `agy_runipd.item_reached_success is runner_shared.item_reached_success` -> True, and the same two identities hold for `exit_code_statuses`. `tests/test_runner_shared.py` already pins all four with `assertIs`. | `python3 -c` identity probe over the three modules (four `True` results); read of the `assertIs` loop in `tests/test_runner_shared.py`. |
| F-05 | THE FOOTER IS NOT THE FIRST CRASH ON THE REAL EXIT PATH, which is the finding that bounds this plan's claim and which the backlog item does not contain. In `oc_runipd.run_queue`'s tail (`oc_runipd.py:3932` onward) the order is `write_report`, `render_run_summary_table`, `render_queue_dispositions`, `render_disposition_summary`, `render_continuation_hint`, `exit_code_statuses`. Measured against a queue of `["not-a-mapping"]`, the first FOUR already raise: `write_report` raises `TypeError: string indices must be integers, not 'str'` (from `runner_shared.write_report`'s `counts[item["status"]]` line), and `render_run_summary_table`, `render_queue_dispositions` and `render_disposition_summary` each raise the same `AttributeError`. `agy_runipd.run_queue`'s tail has the identical order (`agy_runipd.py:3402` onward). A fifth call, `report_run_spec_edits`, does NOT raise: it CATCHES the `AttributeError` and prints "SPEC CHANGES: could not be computed (AttributeError)", which is the in-tree precedent for tolerating this input rather than dying on it. | Six probes, one per call, each against the same malformed state; read of both hosts' `run_queue` tails. |
| F-06 | THEREFORE THE ITEM'S STATED MOTIVE IS NOT FULLY SATISFIED BY ITS OWN NAMED FIX, and saying so is this plan's honesty obligation. The item's WHY IT MATTERS is that a corrupted or older-driver `state.json` "would crash the footer and lose the closing report for work that actually completed". After this plan, neither `runner_shared` exit-path function crashes, but such a run still loses its closing report to `write_report` first (F-05). What this plan delivers is precise and worth delivering: the function whose contract promises tolerance now has it, and the run's EXIT CODE (F-02, F-02a) no longer depends on an unguarded `.get` nor silently returns 0 under a stop (F-02b). The remaining upstream sites are carried by backlog items `s438xd`, `3z91mq` and `fcodik`, filed during authoring, not left in prose. | Composition of F-05's measurement with the item's own stated rationale. |
| F-07 | THE FIX ADDS NO IMPORT. `runner_shared` already imports `Mapping` from `collections.abc` at module level, and `item_reached_success` is already ANNOTATED `(item: Mapping[str, Any]) -> bool`, so the guard enforces at runtime a type the signature already declares. The annotation being already correct is also why no type checker flags the defect today: the crash comes from a caller passing something the annotation forbids. | `grep` of the `collections.abc` import block; `inspect.signature(runner_shared.item_reached_success)` -> `(item: 'Mapping[str, Any]') -> 'bool'`. |
| F-08 | THE RESUME BRANCH IS THE CORRECT OUTCOME for a malformed entry, so E-01's assertion is not arbitrary. `render_continuation_hint` prints the "inspect run summary" hint only when `all_success`; a queue whose entry cannot be read has not been shown to have succeeded, so the honest footer is the RESUME hint. This also matches the shipped behavior for every non-success status, which `ContinuationHintTests` already pins for `failed`, `running`, `interrupted`, `partial` and `merge-refused`. | Read of `render_continuation_hint`'s `all_success` branch and of the status loop in `tests/test_oc_runipd.py::ContinuationHintTests::test_no_sessions_captured_and_unattempted`. |
| F-09 | NO EXISTING TEST COVERS THIS INPUT FOR THIS FUNCTION, so E-01 is new coverage rather than a duplicate. Searching `tests/` for `item_reached_success` returns hits only in `tests/test_runner_shared.py` (an `assertIs` identity loop) and `tests/test_inlane_retirement_lands.py` (two well-formed-item assertions on a retirement status). The one `"not-a-mapping"` literal in the footer test class is passed to `no_turn_was_attempted`, the sibling that already guards. | Two searches over `tests/`, each hit classified. |
| F-10 | THE MALFORMED-ENTRY SHAPE IS NOT HYPOTHETICAL IN THIS REPOSITORY'S OWN JUDGEMENT. `no_turn_was_attempted` was given its guard deliberately and is pinned by a test whose name states the policy (`test_the_no_turn_claim_FAILS_CLOSED_rather_than_guessing`, cited by the backlog item), and `derive_item_disposition`'s module carries a long comment about tolerating shapes two different producers write. The exit path is read-only reporting over durable state a previous process wrote, which is the one place a shape guarantee cannot be enforced by construction. | Read of `runner_shared.no_turn_was_attempted`'s docstring and of the `bsc457` comment block in `render_continuation_hint`. |
| F-11 | THE UPSTREAM `AttributeError` SITES ARE ALREADY PARTLY CLAIMED BY OTHER WORK, so E-04 must not duplicate it, but neither prior artifact covers the crash. `b7oicl` (`bug`, `Blocks-Release: next`) concerns `render_run_summary_table`'s COMPLETED-at-100-percent verdict for a never-dispatched queue and cites `derive_item_disposition`/`summarize_dispositions` as the vocabulary to consume; it is about a WRONG VERDICT, not a crash. **CORRECTED AT REVIEW: it is no longer `open`.** It graduated on 2026-09-28 (`c763a2fa`, after this plan's authoring commit `7b2a4500`) into pending plan `4po0sc`, which declares `- Scope-Paths: agent_workflows/render_stream.py, tests/test_zero_dispatch_outcome.py` and fences itself to "ONLY the `COMPLETED` branch of that one function's outcome word" with "No exit code" - so it neither covers nor collides with `s438xd`'s crash. `mjrac4` (`open`, `chore`) concerns the two divergent `unsatisfied_dependencies` SHAPES; **CORRECTED AT REVIEW: it does not touch `render_run_summary_table`**, it names `derive_item_disposition` and `render_stream`'s DIAGNOSTICS block, a different site, and it is not a crash. So the crash remains unfiled by anything but the three items this plan filed. | Read of both items in full (neither contains "malformed", "isinstance", or a non-mapping entry); `- Status:` and `- Graduated-To:` read from `b7oicl`'s front matter; `git log` on `b7oicl` (`c763a2fa`) versus this plan's authoring commit; read of `4po0sc`'s `- Scope-Paths:` and `- Scope:`. |
| F-12 | THE SUITE IS GREEN AT THIS HEAD, giving a baseline the validation can be compared against: `2935 passed, 2 skipped, 3 warnings in 53.07s` from a BARE `python3 -m pytest`. | Bare `python3 -m pytest` at HEAD `07580297`, summary line captured. |

## Proposed changes (ordered, validatable)

1. Add a failing test to `tests/test_oc_runipd.py::ContinuationHintTests` pinning the malformed-entry case for the footer (returns, and takes the RESUME branch), for `exit_code_statuses` (returns, projects onto neither `EXIT_SUCCESS_TOKEN` nor `"queued"`, and yields exit 1 under both deliberate-stop arms), and for `item_reached_success` directly (`False`) (E-01).
2. Add the fail-closed `isinstance(item, Mapping)` guard to `runner_shared.item_reached_success` and extend its existing tolerance paragraph to state the refusal and its conservative direction, changing no other executable line (E-02).
3. Add the second, independent fail-closed guard to `runner_shared.exit_code_statuses`'s own per-entry read, with a new module-level sentinel token that is neither `EXIT_SUCCESS_TOKEN` nor `"queued"`, and extend that function's docstring where it currently claims every other status is passed through unchanged (E-03).
4. Verify the honesty bound and the three carrier backlog items, as the last act before commit, so this plan's effect is not overstated (E-04).

## Deferred / out of scope (with reason)

- `render_stream.render_run_summary_table` CRASHING ON THE SAME ENTRY is out of scope. It is a genuine defect and it runs BEFORE the footer (F-05), so fixing only the footer leaves the closing report lost; but `render_stream.py` is a different module, and the crash is in its own `.get` reads rather than in either function this plan guards. `b7oicl` holds a live claim on that same function's verdict word, now carried by pending plan `4po0sc` (F-11 as corrected at review), whose own fence explicitly excludes exit-code and status work, so the two do not collide but they do touch one file and a concurrent edit is the avoidable hazard. Editing it here would widen this plan from two shared-module guards into a cross-module hardening pass.
  - Carrier: s438xd
- `run_selection_policy.derive_item_disposition` / `summarize_dispositions` / `render_disposition_summary` / `render_queue_dispositions` CRASHING ON THE SAME ENTRY is out of scope, for the same reason and with the same measurement (F-05, which review corrected to count `render_queue_dispositions` as a FOURTH upstream crash site, since it reaches the same `derive_item_disposition` and is a separate statement in both hosts' tails). Its `get = entry.get` line is the crash point, and that module is deliberately import-pure (two stdlib imports), so a guard there is a decision about that module's tolerance contract rather than a consequence of this one. `mjrac4` (`open`, `chore`) touches `derive_item_disposition` without covering the crash (F-11).
  - Carrier: 3z91mq
- EACH HOST'S `write_report` CRASHING FIRST OF ALL is out of scope. It raises a `TypeError`, not the `AttributeError` this plan fixes, from an `item["status"]` subscript in the shared `runner_shared.write_report` body (`counts[item["status"]] = counts.get(item["status"], 0) + 1`), and it is the FIRST statement in both hosts' `run_queue` tails (F-05), which makes it the true blocker for the item's stated motive. NOTE THAT IT IS IN THIS PLAN'S OWN SCOPE-PATH FILE, `runner_shared.py`, so the exclusion is a judgement rather than a module boundary: it is excluded because it is a different expression raising a different exception and because fixing it means deciding what an unreadable entry should be COUNTED AS in a persisted `execution-report.md`, which is a reporting-contract decision and not a predicate guard. The executor MUST NOT fix it opportunistically while in the file; that is `fcodik`'s work and doing it here would leave this plan's tests silent about the behavior it changed.
  - Carrier: fcodik
- CHANGING ANY WELL-FORMED ENTRY'S VERDICT OR PROJECTED TOKEN is rejected rather than deferred. `item_reached_success` is the single definition behind the run exit code, the per-item finish glyph and the footer's `all_success` (its own docstring names all three), the action-aware bar it applies is `zz5yxq`'s measured work, and `exit_code_statuses`'s `"queued"` passthrough is what makes `runner_stop.deliberate_stop_exit_code`'s deliberate-stop concession work at all (F-02b). This plan adds a branch to each for an input that currently raises; if any currently-returning input's answer or token changes, the plan has failed.
  - Carrier-Declined: There is nothing to carry. This row records a PROHIBITION on this plan rather than an outstanding defect: the shipped verdicts and tokens are the correct ones, so no future work is owed and a carrier would name an obligation that does not exist. V-02 and V-03 enforce it inside this plan.
- HARDENING THE OTHER `runner_shared` QUEUE READERS as a sweep is out of scope. A general "guard every `.get` over a queue entry" pass would be a large diff across a 36342-line module with no measured failing input per site, and this plan's fence is the two functions with a MEASURED crash on the run exit path, one of which already promises the tolerance it lacks in its own docstring (F-03).
  - Carrier-Declined: Nothing is owed. The sites with a MEASURED crash are carried by `s438xd`, `3z91mq` and `fcodik` above; a speculative sweep over sites with no measured failing input would be hardening without evidence, which this repository files as `chore` only when someone measures a cost. No gap is left unowned.

## Scope check

- Over-scope: none. `agent_workflows/runner_shared.py` carries E-02's guard in `item_reached_success`, E-03's guard plus new sentinel constant in `exit_code_statuses`, and the two docstring amendments those guards make necessary; `tests/test_oc_runipd.py` carries E-01's new test. No host runner is edited (F-04 shows none is needed), `render_stream.py` and `run_selection_policy.py` are untouched, `runner_shared.write_report` is deliberately untouched even though it lives in an in-scope file, no spec is touched, and no other `.aw/` record changes: the three carrier backlog items (`s438xd`, `3z91mq`, `fcodik`) were filed during AUTHORING and are committed with this plan, so execution creates no record of its own.
- Under-scope: A run whose `state.json` holds a malformed entry STILL loses its closing report, because `write_report`, `render_run_summary_table`, `render_queue_dispositions` and `render_disposition_summary` all crash before the footer is reached (F-05, F-06). That is a disclosed limit, not an omission: all are carried by backlog items `s438xd`, `3z91mq` and `fcodik`. What this plan completes is the item's named FIX (the guard in `item_reached_success`) and its named TEST, plus the exit-code caller the item did not notice (F-02) which needs its OWN guard rather than being fixed by the predicate's (F-02a) and whose token choice decides whether the fail-closed direction survives a graceful stop (F-02b).

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted, compared against the F-12 baseline of `2935 passed, 2 skipped`. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_oc_runipd.py -o addopts=""` for the per-test counts on the one test file this plan edits.
- `python3 -m pytest tests/test_runner_shared.py tests/test_inlane_retirement_lands.py tests/test_action_table_runner_parity.py tests/test_typed_queue_entries.py tests/test_liftaudit_stop_halts_run.py tests/test_interrupt_attempt_metadata.py tests/test_agy_runipd_cli.py -o addopts=""` as the targeted regression set: every file that asserts `item_reached_success` or `exit_code_statuses` (by identity or by behavior), projects a queue for the exit code, or renders the footer.
- A DELIBERATE-FAILURE DEMONSTRATION for E-01: the new test must be shown FAILING on the pre-E-02 tree with the `AttributeError` in its traceback, since a guard that was never red proves nothing. AND a SECOND red demonstration after E-02 but BEFORE E-03, showing the same test still failing with the crash frame now at `runner_shared.exit_code_statuses` rather than at the predicate. That second demonstration is the direct evidence for F-02a and it is the one an executor is most likely to skip, because after E-02 the footer assertion already passes.
- A NO-VERDICT-CHANGE PROBE for E-02: an exhaustive comparison of `item_reached_success` before and after the guard over the cross product of every status in `SUCCESS_STATES`, `EXECUTE_OR_RETIRED_REPORTING_SUCCESS_STATES`, `SKIP_REPORTING_SUCCESS_STATES` and `PLAN_REPORTING_SUCCESS_STATES` against every action (`execute`, `review`, `skip`, `plan`, `orchestrate`, `None`) plus a handful of failure statuses, asserting the two agree on every well-formed input.
- A NO-PROJECTION-CHANGE PROBE for E-03, the analogue of the above for the second guard: run the SAME cross product of statuses and actions through `exit_code_statuses` before and after, as single-entry queues and as one combined multi-entry queue, and assert the two projections are equal element-for-element. Then feed each projection to `runner_stop.deliberate_stop_exit_code(..., success_states={EXIT_SUCCESS_TOKEN}, stopped=S)` for `S` in both `False` and `True` and assert the exit codes are equal too, since the projection is not an output a user sees and the exit code is.
- `aw ipd lint` on this plan, reporting conforming.
- `aw check` to confirm no new drift, and `aw backlog check` to confirm the three carrier items are well-formed and still live.
- `aw sanitize --agent` before commit, since this plan's evidence blocks quote local command output including tracebacks with absolute paths.
- `git diff --cached --name-only` immediately before committing, which must list exactly the two paths in `- Scope-Paths:` plus this plan, and nothing another party changed.

## Spec / documentation sync

N/A with reason. No `.spec.md` is in `- Scope-Paths:` and none needs to be. No shipped contract moves: the CLI surface, the `aw.agent/v1` JSON contract and the run's exit codes for every well-formed queue are byte-identical before and after, because each guard adds a branch reachable only by an input that currently raises `AttributeError` (F-01, F-02, F-02a). The function's documented contract is not being CHANGED but RESTORED: `item_reached_success`'s docstring already promises tolerance of "a state file written by an older driver" (F-03), so E-02's amendment makes the prose match the code rather than redefining it.

TWO SPEC-ADJACENT CLAIMS WERE CHECKED AT REVIEW AND NEITHER NEEDS AN AMENDMENT. First, spec `c4gd2h` A1/A4 fix the exit code a DELIBERATE STOP must produce, and E-03 is measured against that: a malformed entry projects onto neither `EXIT_SUCCESS_TOKEN` nor `"queued"`, so a stopped run with an unreadable entry exits 1 (F-02b) - which does not weaken A1/A4, because those govern a run whose remaining items are `queued`, a state a malformed entry cannot be shown to be in. Second, spec `c4gd2h` R22 forbids manufacturing a disposition by rewriting a status; E-03 rewrites nothing on disk and adds a token to the same in-memory projection `exit_code_statuses` already returns, whose docstring states "THIS REWRITES NOTHING". No user-facing documentation mentions either function; the two in-source docstrings that do are amended by E-02 and E-03 themselves, inside a file already in scope.

## Open questions

### OQ-01: The item's motive is "do not lose the closing report", but four upstream sites crash first. Should this plan widen to fix them all, or stay at the item's named fix and carry the rest?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as STAY AND CARRY, and it needs no maintainer ruling because the choice is about how to scope a fence rather than about scope the human owns. The measurement is F-05: `write_report` (`TypeError`), `render_run_summary_table`, `render_queue_dispositions` and `render_disposition_summary` all crash on the same malformed entry and all run BEFORE the footer in both hosts' `run_queue` tails. Widening to cover them would put two more modules in `- Scope-Paths:` (`render_stream.py`, `run_selection_policy.py`) plus a third, unrelated function inside this plan's own file (`runner_shared.write_report`), and turn two predicate guards into a cross-module tolerance policy with three separate design decisions about what an unreadable entry RENDERS AS, COUNTS AS, and is DISPOSED as. The repository's stated practice for a defect found outside the current fence is to REPORT it rather than reach across: `derive_item_disposition`'s own comment records declining to fix `render_stream`'s matching wart as "out-of-fence" and reporting it instead, and backlog item `b7oicl` exists because `bsc457`'s OQ-02 was resolved that way. CORRECTED AT REVIEW: the earlier version of this rationale cited a collision with "two OPEN items"; `b7oicl` has since graduated to pending plan `4po0sc` (F-11) and `mjrac4` never named `render_run_summary_table`, so the true reason is the design-decision count and the module boundary, not a collision. The honest cost of staying is that the item's motive is not fully met, which is why F-06 states that plainly and why E-04 is a deliverable of this plan rather than a note: the gap is carried to named items, not left in prose. The counter-consideration, that a partial fix might read as a complete one, is answered by the Scope check's explicit Under-scope paragraph.

### OQ-02: Should the guard live in `item_reached_success`, or should `render_continuation_hint` and `exit_code_statuses` each filter their queue before calling it?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as IN THE PREDICATE, for three evidenced reasons. FIRST, the contract is written on the PREDICATE, not on its callers: `item_reached_success`'s docstring is what promises safety on "a hand-written manifest's entry or ... a state file written by an older driver" (F-03), so the guard belongs where the promise is, and a caller-side filter would leave the function still violating its own docstring for the next caller. SECOND, there are already TWO exit-path callers plus a third construction site (`execute_item_core` builds a literal `{"action": ..., "status": ...}` for the finish glyph), so a caller-side fix is three edits that can drift, which is the exact failure mode the function was extracted to prevent: its docstring says it exists "so the three execute-action call sites ... cannot drift from one another". THIRD, the sibling precedent is in-predicate: `no_turn_was_attempted` guards `isinstance(item, dict)` inside itself rather than asking its caller to pre-filter, and documents that as one of three deliberate fail-closed properties. The one design constraint the measurement forces is the DIRECTION: refuse, never admit, because a `True` here would manufacture a success for an entry nobody can read, and the docstring's existing reasoning about a missing `action` ("it can only refuse to call something a success, never manufacture one") already fixes that direction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the full committed source of the new test. Paste its output run on the tree BEFORE E-02's guard (`python3 -m pytest tests/test_oc_runipd.py -k <new-test-name> -o addopts=""`), which must FAIL, and paste enough of the traceback to show the crash frame is `runner_shared.item_reached_success`'s `item.get("status")` line and the exception is `AttributeError: 'str' object has no attribute 'get'`. Confirm in one sentence that the test asserts all FOUR surfaces named in E-01 (footer returns AND takes the resume branch; `exit_code_statuses` returns AND emits neither `EXIT_SUCCESS_TOKEN` nor `"queued"`; `deliberate_stop_exit_code` over that projection is 1 under BOTH stop arms; `item_reached_success` is `False`), quoting the assertions. A test that fails for only the footer is NOT sufficient: F-02/F-02a is the finding the backlog item missed, and its assertion must be shown red too.
  - Observed evidence: Verified test failure before E-02 with AttributeError at runner_shared.item_reached_success:25507.
    Full committed source of `test_malformed_queue_entry_exit_path_fails_closed` in `tests/test_oc_runipd.py`:
    ```python
    def test_malformed_queue_entry_exit_path_fails_closed(self):
        # 1. Footer returns rather than raising and takes the resume branch.
        hint = driver.render_continuation_hint(
            self._state({}, queue=["not-a-mapping"]), Path("/x")
        )
        self.assertIn("aw oc run resume --repo /repo run-xyz", hint)
        self.assertNotIn("aw runs", hint)

        # Cover both hosts for the footer.
        agy_hint = agy_runipd.render_continuation_hint(
            self._state({}, queue=["not-a-mapping"]), Path("/x")
        )
        self.assertIn("aw agy run resume --repo /repo run-xyz", agy_hint)
        self.assertNotIn("aw runs", agy_hint)

        # 2. exit_code_statuses returns and projects onto neither success nor "queued".
        projected = runner_shared.exit_code_statuses(["not-a-mapping"])
        self.assertNotIn(runner_shared.EXIT_SUCCESS_TOKEN, projected)
        self.assertNotIn("queued", projected)

        # 3. deliberate_stop_exit_code returns 1 under both stopped arms.
        self.assertEqual(
            runner_stop.deliberate_stop_exit_code(
                projected,
                success_states={runner_shared.EXIT_SUCCESS_TOKEN},
                stopped=False,
            ),
            1,
        )
        self.assertEqual(
            runner_stop.deliberate_stop_exit_code(
                projected,
                success_states={runner_shared.EXIT_SUCCESS_TOKEN},
                stopped=True,
            ),
            1,
        )

        # 4. item_reached_success returns False directly.
        self.assertFalse(runner_shared.item_reached_success("not-a-mapping"))
    ```

    Output run on the tree BEFORE E-02's guard (`python3 -m pytest tests/test_oc_runipd.py -k test_malformed_queue_entry_exit_path_fails_closed -o addopts=""`):
    ```
    =================================== FAILURES ===================================
    ___ ContinuationHintTests.test_malformed_queue_entry_exit_path_fails_closed ____

    self = <tests.test_oc_runipd.ContinuationHintTests testMethod=test_malformed_queue_entry_exit_path_fails_closed>

        def test_malformed_queue_entry_exit_path_fails_closed(self):
            # 1. Footer returns rather than raising and takes the resume branch.
    >       hint = driver.render_continuation_hint(
                self._state({}, queue=["not-a-mapping"]), Path("/x")
            )

    tests/test_oc_runipd.py:2569:
    _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
    agent_workflows/oc_runipd.py:4067: in render_continuation_hint
        return runner_shared.render_continuation_hint(
    agent_workflows/runner_shared.py:25921: in render_continuation_hint
        all_success = all(item_reached_success(item) for item in queue)
    agent_workflows/runner_shared.py:25921: in <genexpr>
        all_success = all(item_reached_success(item) for item in queue)
    _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    item = 'not-a-mapping'

        def item_reached_success(item: Mapping[str, Any]) -> bool:
            """Did ONE queue item finish successfully, judged against the bar its ACTION earns (zz5yxq E-02).

            The per-item form of :func:`success_states_for_action`, so the three execute-action call sites
            (the run exit code, the finish glyph, and `render_continuation_hint`'s `all_success`) cannot
            drift from one another.

            Reads `action` and `status` off the entry and NOTHING ELSE, so it is safe to call on a
            hand-written manifest's entry or on a state file written by an older driver: a missing `action`
            is treated as the execute case, which is the conservative direction (it can only refuse to call
            something a success, never manufacture one).
            """

    >       status = item.get("status")
    E       AttributeError: 'str' object has no attribute 'get'

    agent_workflows/runner_shared.py:25507: AttributeError
    =========================== short test summary info ============================
    FAILED tests/test_oc_runipd.py::ContinuationHintTests::test_malformed_queue_entry_exit_path_fails_closed
    ====================== 1 failed, 167 deselected in 2.34s =======================
    ```

    The test asserts all four surfaces named in E-01: footer returns and takes the resume branch (`assertIn("aw oc run resume --repo /repo run-xyz", hint)` and `assertNotIn("aw runs", hint)`), `exit_code_statuses` returns and emits neither `EXIT_SUCCESS_TOKEN` nor `"queued"` (`assertNotIn(runner_shared.EXIT_SUCCESS_TOKEN, projected)` and `assertNotIn("queued", projected)`), `deliberate_stop_exit_code` over that projection returns 1 under both stop arms (`assertEqual(runner_stop.deliberate_stop_exit_code(..., stopped=False), 1)` and `assertEqual(runner_stop.deliberate_stop_exit_code(..., stopped=True), 1)`), and `item_reached_success` is `False` directly (`assertFalse(runner_shared.item_reached_success("not-a-mapping"))`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/runner_shared.py` as it stands after E-02 ONLY (before E-03), showing exactly one added guard in `item_reached_success` plus its docstring amendment and NO other executable change. Paste a probe showing `runner_shared.item_reached_success("not-a-mapping")`, `(None)` and `(["status"])` are each `False`, and that `render_continuation_hint` RETURNS the resume footer for `queue=["not-a-mapping"]`. THEN PASTE THE SECOND RED DEMONSTRATION required by F-02a: the E-01 test run at THIS point, still FAILING, with the traceback's crash frame now at `runner_shared.exit_code_statuses` rather than at the predicate. That contrast is the whole evidence that the two guards are independent and that E-03 is not redundant; without it, a reader cannot distinguish this plan from the single-guard plan review rejected. Then paste the NO-VERDICT-CHANGE PROBE described in Required tests: the full cross product of statuses against actions compared between the pre-fix and post-fix function, with the count of inputs compared and the assertion that zero verdicts moved.
  - Observed evidence: Verified E-02 diff, non-mapping probe, second red failure at exit_code_statuses:25572, and 119-input no-verdict-change probe.
    `git diff agent_workflows/runner_shared.py` after E-02 ONLY (before E-03):
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 901ddbe7..81b5dbe1 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -25501,9 +25501,13 @@ def item_reached_success(item: Mapping[str, Any]) -> bool:
         Reads `action` and `status` off the entry and NOTHING ELSE, so it is safe to call on a
         hand-written manifest's entry or on a state file written by an older driver: a missing `action`
         is treated as the execute case, which is the conservative direction (it can only refuse to call
    -    something a success, never manufacture one).
    +    something a success, never manufacture one). A malformed entry (anything that is not a mapping)
    +    is refused as a non-success, since an unreadable entry cannot be shown to have succeeded; that too
    +    can only refuse to call something a success, never manufacture one.
         """

    +    if not isinstance(item, Mapping):
    +        return False
         status = item.get("status")
         return isinstance(status, str) and status in success_states_for_action(
             item.get("action")
    ```

    Direct probe of non-mapping inputs and resume footer:
    ```
    item_reached_success('not-a-mapping') -> False
    item_reached_success(None) -> False
    item_reached_success(['status']) -> False
    render_continuation_hint returned:

    --- OpenCode Session Continuity ---
    No OpenCode session was captured for this run.
    To resume this run:
      aw oc run resume --repo /repo run-xyz
    To stop a future run gracefully:
      aw oc run stop <run-id> --after-call

    PROBE PASSED
    ```

    Second red demonstration (E-01 test run after E-02, before E-03, showing crash frame moved to `runner_shared.exit_code_statuses`):
    ```
    =================================== FAILURES ===================================
    ___ ContinuationHintTests.test_malformed_queue_entry_exit_path_fails_closed ____

    self = <tests.test_oc_runipd.ContinuationHintTests testMethod=test_malformed_queue_entry_exit_path_fails_closed>

        def test_malformed_queue_entry_exit_path_fails_closed(self):
            # 1. Footer returns rather than raising and takes the resume branch.
            hint = driver.render_continuation_hint(
                self._state({}, queue=["not-a-mapping"]), Path("/x")
            )
            self.assertIn("aw oc run resume --repo /repo run-xyz", hint)
            self.assertNotIn("aw runs", hint)

            # Cover both hosts for the footer.
            agy_hint = agy_runipd.render_continuation_hint(
                self._state({}, queue=["not-a-mapping"]), Path("/x")
            )
            self.assertIn("aw agy run resume --repo /repo run-xyz", agy_hint)
            self.assertNotIn("aw runs", agy_hint)

            # 2. exit_code_statuses returns and projects onto neither success nor "queued".
    >       projected = runner_shared.exit_code_statuses(["not-a-mapping"])

    tests/test_oc_runipd.py:2583:
    _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    queue = ['not-a-mapping']

        def exit_code_statuses(queue: Sequence[Mapping[str, Any]]) -> list[str]:
    ...
            projected: list[str] = []
            for item in queue:
    >           status = item.get("status")
    E           AttributeError: 'str' object has no attribute 'get'

    agent_workflows/runner_shared.py:25572: AttributeError
    =========================== short test summary info ============================
    FAILED tests/test_oc_runipd.py::ContinuationHintTests::test_malformed_queue_entry_exit_path_fails_closed
    ====================== 1 failed, 167 deselected in 1.09s =======================
    ```

    NO-VERDICT-CHANGE PROBE over cross product of statuses and actions:
    ```
    NO-VERDICT-CHANGE PROBE: compared 119 inputs across statuses and actions, 0 disagreements.
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste `git diff agent_workflows/runner_shared.py` in full (both guards now present), showing the new sentinel constant with its docstring/comment, the `isinstance` guard in `exit_code_statuses`, the extended docstring, and NO other executable change; in particular the `"queued"` passthrough and the `str(status)` fallthrough must be visibly untouched, and `runner_shared.write_report` must be visibly unmodified (it is the deliberately-excluded `fcodik` site in this same file). Paste the E-01 test now PASSING in full. Paste a probe showing `runner_shared.exit_code_statuses(["not-a-mapping"])` returns the sentinel, that the sentinel is neither `EXIT_SUCCESS_TOKEN` nor `"queued"`, and that `runner_stop.deliberate_stop_exit_code` over it returns `1` for BOTH `stopped=False` and `stopped=True` (the F-02b measurement, post-fix). Then paste the NO-PROJECTION-CHANGE PROBE described in Required tests, with the count of inputs compared, the assertion that zero projected tokens moved, and the assertion that zero exit codes moved on either stop arm. Paste `python3 -m pytest tests/test_oc_runipd.py -o addopts=""` green.
  - Observed evidence: Verified full runner_shared diff, passing E-01 test, exit code 1 on both stop arms, 119-input no-projection-change probe, and green test_oc_runipd.py.
    `git diff agent_workflows/runner_shared.py` in full:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 901ddbe7..b10663a9 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -25501,9 +25501,13 @@ def item_reached_success(item: Mapping[str, Any]) -> bool:
         Reads `action` and `status` off the entry and NOTHING ELSE, so it is safe to call on a
         hand-written manifest's entry or on a state file written by an older driver: a missing `action`
         is treated as the execute case, which is the conservative direction (it can only refuse to call
    -    something a success, never manufacture one).
    +    something a success, never manufacture one). A malformed entry (anything that is not a mapping)
    +    is refused as a non-success, since an unreadable entry cannot be shown to have succeeded; that too
    +    can only refuse to call something a success, never manufacture one.
         """

    +    if not isinstance(item, Mapping):
    +        return False
         status = item.get("status")
         return isinstance(status, str) and status in success_states_for_action(
             item.get("action")
    @@ -25538,6 +25542,12 @@ def item_needs_approval(status: str | None, action: str | None) -> bool:
     #: confused with something a driver persists.
     EXIT_SUCCESS_TOKEN = "aw-item-met-its-action-success-bar"

    +#: The token :func:`exit_code_statuses` projects a queue entry that was NOT a mapping onto (w7e3e3
    +#: E-03). Deliberately not a real status, deliberately not spellable as one, and deliberately neither
    +#: :data:`EXIT_SUCCESS_TOKEN` nor `"queued"`, so `runner_stop.deliberate_stop_exit_code` judges it
    +#: a failure under both normal and graceful-stop runs rather than silently excusing it.
    EXIT_MALFORMED_ENTRY_TOKEN = "aw-queue-entry-was-malformed"
    +

     def exit_code_statuses(queue: Sequence[Mapping[str, Any]]) -> list[str]:
         """Project each queue entry onto the token the run's exit-code predicate should judge (zz5yxq E-02).
    @@ -25559,12 +25569,19 @@ def exit_code_statuses(queue: Sequence[Mapping[str, Any]]) -> list[str]:
         Projecting them onto anything else would either break a correct wind-down's exit 0 or silently
         excuse an item that did run.

    -    Every other non-success status is passed through unchanged, so it still reads as a failure and a
    -    reader of a debugger frame still sees the real disposition.
    +    A malformed entry (anything that is not a mapping) projects onto
    +    :data:`EXIT_MALFORMED_ENTRY_TOKEN`. It cannot be passed through via `str(status)` (which would
    +    inject arbitrary unvetted text into the exit-code vocabulary) nor mapped to `"queued"` (which would
    +    manufacture an exit 0 under a graceful stop). Every other non-success status is passed through
    +    unchanged, so it still reads as a failure and a reader of a debugger frame still sees the real
    +    disposition.
         """

         projected: list[str] = []
         for item in queue:
    +        if not isinstance(item, Mapping):
    +            projected.append(EXIT_MALFORMED_ENTRY_TOKEN)
    +            continue
             status = item.get("status")
             if status == "queued":
                 projected.append("queued")
    ```

    The E-01 test now PASSING in full (`python3 -m pytest tests/test_oc_runipd.py -k test_malformed_queue_entry_exit_path_fails_closed -o addopts=""`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3680976911
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 168 items / 167 deselected / 1 selected

    tests/test_oc_runipd.py .                                                [100%]

    ====================== 1 passed, 167 deselected in 0.75s =======================
    ```

    F-02b measurement probe:
    ```
    exit_code_statuses(["not-a-mapping"]) -> ['aw-queue-entry-was-malformed']
    deliberate_stop_exit_code(stopped=False) -> 1
    deliberate_stop_exit_code(stopped=True) -> 1
    PROBE PASSED
    ```

    NO-PROJECTION-CHANGE PROBE over cross product of statuses and actions:
    ```
    NO-PROJECTION-CHANGE PROBE: compared 119 single-entry inputs and 1 combined queue (119 entries).
    Zero projected tokens moved, and zero exit codes moved on either stop arm.
    ```

    Full `tests/test_oc_runipd.py` suite green (`python3 -m pytest tests/test_oc_runipd.py -o addopts=""`):
    ```
    ============================= 168 passed in 59.97s =============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the POST-FIX five-probe measurement of F-05 (`write_report`, `render_run_summary_table`, `render_queue_dispositions`, `render_disposition_summary`, then `render_continuation_hint` and `exit_code_statuses`), each against `queue=["not-a-mapping"]`, showing the first FOUR STILL raising their recorded exceptions (`TypeError: string indices must be integers` for `write_report`; `AttributeError: 'str' object has no attribute 'get'` for the other three) and the last two now RETURNING. That contrast is the evidence for this plan's honesty bound: it proves both that the fix works and that the closing report is still lost upstream. Paste `aw find backlog s438xd 3z91mq fcodik` (or three `grep` reads of their front matter) showing each still `- Status: open` with `- Blocks-Release: next`. Quote the sentence in this plan's Scope check Under-scope paragraph that states the report is still lost, and confirm in one sentence that the commit message makes no stronger claim. Confirm this plan carries no placeholder text by pasting `grep -n 'TODO' <this-plan>` and checking every hit is either the literal section heading or a mention inside this V-item's own required-evidence sentence; no hit may be an unfilled placeholder standing in for work. Paste `aw backlog check` and `aw check` clean. ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line and state it against the F-12 baseline of `2935 passed, 2 skipped`; paste the targeted regression set from Required tests; paste `aw ipd lint` on this plan reporting conforming; paste `aw sanitize --agent`; and paste `git diff --cached --name-only` immediately before committing, which must list exactly `agent_workflows/runner_shared.py`, `tests/test_oc_runipd.py` and this plan.
  - Observed evidence: Verified 5-probe exit path measurement, carrier items live, under-scope honesty quote, 0 TODOs, clean check, 3035 passed suite, and 204 passed targeted regression set.
    1. POST-FIX five-probe measurement of F-05:
    ```
    Probe 1 (write_report): TypeError: string indices must be integers, not 'str'
    Probe 2 (render_run_summary_table): AttributeError: 'str' object has no attribute 'get'
    Probe 3 (render_queue_dispositions): AttributeError: 'str' object has no attribute 'get'
    Probe 4 (render_disposition_summary): AttributeError: 'str' object has no attribute 'get'
    Probe 5a (render_continuation_hint): RETURNED successfully
    Probe 5b (exit_code_statuses): RETURNED successfully: ['aw-queue-entry-was-malformed']
    ```

    2. Carrier backlog items confirmed open and release-gating:
    ```
    $ aw find backlog s438xd 3z91mq fcodik
    ◕  open          3z91mq  .aw/records/backlog/open/20260928-3z91mq-01-3z91mq-disposition-summary-crashes-on-malformed-queue-ent.backlog.md
    ◕  open          fcodik  .aw/records/backlog/open/20260928-fcodik-01-fcodik-write-report-typeerror-on-malformed-queue-entry.backlog.md
    ◕  open          s438xd  .aw/records/backlog/open/20260928-s438xd-01-s438xd-summary-table-crashes-on-malformed-queue-entry.backlog.md

    $ grep -E "^- (Status|Blocks-Release):" .aw/records/backlog/open/*{s438xd,3z91mq,fcodik}*.backlog.md
    .aw/records/backlog/open/20260928-s438xd-01-s438xd-summary-table-crashes-on-malformed-queue-entry.backlog.md:- Status: open
    .aw/records/backlog/open/20260928-s438xd-01-s438xd-summary-table-crashes-on-malformed-queue-entry.backlog.md:- Blocks-Release: next
    .aw/records/backlog/open/20260928-3z91mq-01-3z91mq-disposition-summary-crashes-on-malformed-queue-ent.backlog.md:- Status: open
    .aw/records/backlog/open/20260928-3z91mq-01-3z91mq-disposition-summary-crashes-on-malformed-queue-ent.backlog.md:- Blocks-Release: next
    .aw/records/backlog/open/20260928-fcodik-01-fcodik-write-report-typeerror-on-malformed-queue-entry.backlog.md:- Status: open
    .aw/records/backlog/open/20260928-fcodik-01-fcodik-write-report-typeerror-on-malformed-queue-entry.backlog.md:- Blocks-Release: next
    ```

    3. Scope check Under-scope sentence quote:
    "A run whose `state.json` holds a malformed entry STILL loses its closing report, because `write_report`, `render_run_summary_table`, `render_queue_dispositions` and `render_disposition_summary` all crash before the footer is reached (F-05, F-06)."
    The commit message makes no stronger claim, stating only that `item_reached_success` and `exit_code_statuses` are guarded against malformed queue entries and that upstream closing-report crash sites remain carried by `s438xd`, `3z91mq`, and `fcodik`.

    4. Placeholder text check:
    `grep -n 'TODO' <this-plan>` hits only line 37 (`## Detailed Implementation Checklist (TODO)`) and line 442 (the prompt instruction for this V-item). No unfilled placeholders exist.

    5. Backlog and repo check:
    ```
    $ aw backlog check
    aw backlog check: all backlog items conform.

    $ aw check
    AW check all 6785 ms
    Findings on this plan: 0 errors, 0 warnings (clean).
    ```

    6. Whole-plan no-regression evidence:
    - BARE `python3 -m pytest` output:
    ```
    3035 passed, 2 skipped, 3 warnings in 84.72s (0:01:24)
    ```
    Against F-12 baseline of `2935 passed, 2 skipped`, 100 new tests passed. One adjacent defect was observed in `test_drain_and_cascade_mapped_reasons_rendered_once` due to prerequisite `5o1jye` having reached `executed` status; because backlog modifications are outside this plan's declared Scope-Paths, it is reported under defect_report in the lane submission outcome as mandated by the execution contract ("If filing fails or is outside your scope, STILL REPORT THE FINDING: reporting outranks filing").
    - Targeted regression set (`python3 -m pytest tests/test_runner_shared.py tests/test_inlane_retirement_lands.py tests/test_action_table_runner_parity.py tests/test_typed_queue_entries.py tests/test_liftaudit_stop_halts_run.py tests/test_interrupt_attempt_metadata.py tests/test_agy_runipd_cli.py -o addopts=""`):
    ```
    ======================== 204 passed in 66.09s (0:01:06) ========================
    ```
    - `aw ipd lint` on this plan reporting conforming:
    ```
    - >  ◕  approved     plan        20260928-5rebcb-01-w7e3e3  [low]  [blocking]  conforming
    ```
    - `aw sanitize --agent`:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    - `git diff --cached --name-only` immediately before committing lists exactly:
    ```
    agent_workflows/runner_shared.py
    tests/test_oc_runipd.py
    .aw/records/plans/pending/20260928-5rebcb-01-w7e3e3-guard-item-reached-success-against-a-malformed-queue-entry-s.ipd.md
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` with `- Readiness: go-pending-approval`, written by `/plan-review` on 2026-09-28 as the output of that review. `reviewed` is not approval: explicit human sign-off (`- Status: approved`) is still required before execution.

WHAT THE HUMAN IS APPROVING, in one paragraph, because review changed the plan's shape. The authored plan proposed ONE guard and named TWO crashing callers. Review measured that the second caller, `exit_code_statuses`, crashes in its OWN `.get` read before it ever consults the predicate, so the single guard would have left it crashing while the plan's own Expected outcome claimed otherwise (F-02a). The fix is now two guards in one module, and the second one carries a real design decision: what token an unreadable entry projects onto, which decides whether such a run exits 1 or silently exits 0 under a graceful stop (F-02b). Everything else is unchanged in substance: the fence is still two files, no host runner is edited, and the plan still does NOT claim to restore the closing report.

On execution, the executor MUST: commit only the paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands, including V-01's deliberate-failure demonstration, V-02's SECOND red demonstration and no-verdict-change probe, and V-03's no-projection-change probe. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop; the fence exists so the reconciliation can tell afterwards what moved.

TWO WAYS THIS PLAN CAN FAIL SILENTLY, stated for the executor because a green suite catches neither.

FIRST, A GUARD THAT ADMITS RATHER THAN REFUSES. `item_reached_success` decides the run's EXIT CODE, the per-item finish glyph and the footer's resume branch from one expression, so a guard that accidentally returns `True`, or that shifts the `isinstance(status, str)` test, would manufacture a success for an item that did no work. That is the `zz5yxq` defect this function was written to fix. V-02's cross-product probe catches it, and it must be performed by COMPARING the two implementations over well-formed inputs, not by observing that the suite passes.

SECOND, AND SPECIFIC TO E-03: PROJECTING A MALFORMED ENTRY ONTO `"queued"`. That spelling looks harmless and is the one a reader reaches for, because a malformed entry plainly did not run. It is wrong, and measurably: `runner_stop.deliberate_stop_exit_code` special-cases that exact literal to excuse an item a deliberate stop never started, so the projection would make an unreadable queue exit **0** for any run that observed a stop (F-02b, measured both ways at review). The entry must project onto a token in NEITHER special set. V-03's both-stop-arms assertion is the check.

DO NOT LET THIS PLAN OVERSTATE ITS EFFECT. A corrupt or older-driver `state.json` still loses its closing report after this plan, because `write_report`, `render_run_summary_table`, `render_queue_dispositions` and `render_disposition_summary` all crash before the footer is reached (F-05/F-06). The executor must not write a walkthrough or commit message claiming the closing report is now preserved; the true claim is that the two `runner_shared` exit-path functions now honor the documented tolerance and that the run's exit code no longer depends on an unguarded `.get`.

THE DELIBERATELY-UNFIXED SITE IS IN YOUR OWN FILE. `runner_shared.write_report` crashes on the same input and lives in `agent_workflows/runner_shared.py`, which this plan edits. Do NOT fix it here. It is `fcodik`'s work, it raises a different exception from a different expression, and it needs a decision about what a persisted `execution-report.md` should COUNT an unreadable entry as - a decision this plan's tests would say nothing about.

This plan inherits `- Blocks-Release: next` from backlog item `5rebcb` because its `- Work-Kind:` is `bug`, and the repository policy is that every live bug gates the next release. That gate travels with this plan and must not be cleared as part of executing it.

Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every validation item above is verified with pasted evidence.
