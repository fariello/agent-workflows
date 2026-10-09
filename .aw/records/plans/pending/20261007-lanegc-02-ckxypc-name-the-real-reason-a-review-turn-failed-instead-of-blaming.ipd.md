# IPD: Name the real reason a review turn failed instead of blaming orchestrator readiness

- Date: 2026-10-07
- Kind: child
- Concern: A review turn that fails for any reason is reported as "review orchestrator readiness failed", even for a child plan. Measured 2026-10-07 in run `run-20261007T165351Z-456357`: the review of child `2j4pd0` ended because the model provider's content filter blocked a reply (`ContentFilterError`, last session record `reason: content-filter`), the host exited 1, and the run recorded `fail-gate` with the lane-preserved reason "review orchestrator readiness failed; lane preserved for inspection" and code `review-orchestrator-failed`. The cause is in `runner_shared.execute_item_core`: after `handle_review_orchestrator_readiness` returns the incoming disposition unchanged for a nonzero exit or a non-orchestrator, the caller tests `review_orch_disp == "fail-gate"`, which is true whenever the turn already failed (`reconcile_disposition` returns `fail-gate` for a review that exited nonzero), and writes the orchestrator reason. The same conflation exists at TWO call sites: the isolated-lane review branch (which also calls `lane_containment.record_lane_preserved` with that reason) and the non-isolated review branch that calls the handler with `tree=repo` and `wt_handle=None` (which sets status only). The real cause (a provider error in the session stream) is never surfaced anywhere in the summary or report.
- Scope: (1) Make the orchestrator-readiness branch fire only when `handle_review_orchestrator_readiness` itself refused (the item is an orchestrator, the turn exited 0, and its readiness check failed), and give every other failed review the preserved-lane reason of its actual cause; (2) read the host session stream's final error event (opencode `{"type":"error", ...}`, agy equivalent) and record it on the attempt as `host_error` with name and message; (3) show `host_error` in the run summary row and the execution report. EXCLUDES retrying the turn (that is `fixfirst` Order 04 `ytas91`), and EXCLUDES changing any disposition.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, tests/test_review_failure_reason.py, agent_workflows/lane_containment.py, tests/fixtures/session_content_filter_error.jsonl
- Item-Dependencies: none
- Status: approved
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: lanegc
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ckxypc
- Approval: 2026-10-09, recorded via aw ipd set: status set to approved
- Readiness: go-pending-approval

## Workflow history
- 2026-10-09 approved (aw set): status set to approved
- 2026-10-08 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; see /plan-review record
- 2026-10-08 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed: E-02 forked the error-event parser render_stream.render_event already owns), PR-002..PR-007 fixed. Record: .aw/records/reviews/20261007-lanegc-02-ckxypc-name-the-real-reason-a-review-turn-failed-instead-of-blaming.review.md Round 1.
- 2026-10-07 to-review (aw set): authored review-ready at the maintainer's request 2026-10-07

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

When a review fails, the summary says why ("provider content filter blocked the response", "host exited 1"), so the maintainer can act without reading session logs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the right reason

- [x] E-01 Make `handle_review_orchestrator_readiness` report WHETHER IT DECIDED, not only a disposition: return a small result (for example a `NamedTuple` `(disposition, evaluated, refused)`) where `refused` is True only on its own `return "fail-gate"` after `review_readiness` ran, and `evaluated` is False on every early `return disposition` (nonzero exit, non-IPD entry, plan file not found or unparseable, `Kind` not `orchestrator`). Do not infer it in the caller by re-reading `Kind`, which would duplicate the handler's plan-file resolution. Update BOTH call sites in `runner_shared.execute_item_core` (the isolated-lane review branch and the non-isolated `tree=repo` branch). Write the "review orchestrator readiness failed" reason and `review-orchestrator-failed` code only when `refused` is True. Otherwise, when the incoming disposition was already `fail-gate` and the lane branch preserves the lane, call `lane_containment.record_lane_preserved` with the turn's own cause: `review-host-error` and `"review turn failed: host <name>: <message>"` when E-02 recorded `host_error`; else `review-turn-exited` and `"review turn exited <code> with no outcome file"` when `exit_code != 0`; else `review-turn-failed` and `"review turn ended <disposition>"`. Add the three codes as constants in `lane_containment` beside the existing retention codes. Never change a disposition (Scope).
  - Depends on: E-02
  - Expected outcome: a child review whose host exits 1 records a preserved-lane reason naming the exit (or the host error) and a code other than `review-orchestrator-failed`; an orchestrator review whose readiness refuses still records the orchestrator reason; both call sites behave the same; dispositions are identical to today's in every case.
  - Execution state: performed

### Task group 2: capture the host's error

- [x] E-02 Factor the error-field extraction that `render_stream.render_event` ALREADY performs in its `if etype == "error":` branch (name from `error.name`, message from `error.data.message`, `error.data` as a string, or `error.message`) into one pure helper in `render_stream` (for example `host_error_of_event(event) -> tuple[str, str] | None`), make `render_event` call it so its rendered line is byte-identical, and add a second pure helper that scans a session log for the LAST such event and returns it. That branch's own comment records the observed shape (`{"type":"error","error":{"name":"UnknownError","data":{"message":"The operation timed out."}}}`), so a separate parser would be a second definition of the same event. The Antigravity stream has no such event; its failure is a `{"event":"result","result":{"status":...,"error":...}}` record (see `agy_runipd.render_agy_event`), so on agy the helper reads the last non-SUCCESS `result` and maps it to `(status, error)`; if that shape is absent it returns nothing. Call the scan once per turn in the shared `execute_item_core` after the host process exits, using `attempt["log"]` (`runner_shared.attempt_log_path`), and store `attempt["host_error"] = {"name": ..., "message": ...}` when found, copying it to `item["host_error"]` so renderers that read the item see it. Bound both strings (name 80 characters, message 300, single line, the same `_one_line` bound `render_event` already applies) because the message is provider-authored text that reaches the summary and report. An unreadable or missing log yields nothing and never raises.
  - Depends on: none
  - Expected outcome: against a fixture reproducing the observed content-filter tail (a `"reason":"content-filter"` record followed by the error event, written by hand from F-01's quoted lines; the original run directory is outside this lane), it returns `("ContentFilterError", "The response was blocked by the provider's content filter")`; against a clean session and an agy SUCCESS result it returns nothing; `render_event`'s output for the error event is unchanged (`! diag:  ContentFilterError: The response was blocked by the provider's content filter`, measured at review).
  - Execution state: performed

- [x] E-03 Show `host_error` in the end-of-run summary's existing `Diagnostics / Blocked Items:` block in `render_stream.render_run_summary_table` (one `    host error: <name>: <message>` line under the item's existing bullet, or its own `  • <id6>: <status> (host <name>: <message>)` bullet when the item has none), and in `execution-report.md` as one line beside the existing preserved-lane section (`lane_containment.format_preserved_lanes` already prints "Why preserved", which E-01 now fills correctly; add the host-error line in the shared `runner_shared.write_report` composer so both hosts render it). The run has no `--agent` record of its own, so the machine-readable surface is the attempt and item field in `state.json` from E-02; no new output format is added. An item without `host_error` renders exactly as today.
  - Depends on: E-01, E-02
  - Expected outcome: a scripted run whose host emits a content-filter error shows `host ContentFilterError: The response was blocked by the provider's content filter` against that item in the summary and the report; a run with no host error produces byte-identical summary and report text.
  - Execution state: performed

### Task group 3: tests

- [x] E-04 Add `tests/test_review_failure_reason.py` driving the real runner with a scripted host (the `fake_opencode` pattern in `tests/test_silent_turn_observability.py`) that (a) emits a content-filter error and exits 1 on a child review, (b) exits 1 silently on a child review, (c) exits 0 on an orchestrator whose readiness fails, and (d) exits 1 on an orchestrator review (the handler must not evaluate, so no orchestrator reason). Assert the preserved-lane reason and code from `events.jsonl` and `state.json`, the `host_error` field, the item's final disposition equal to today's, and the summary and report text. Add unit tests for the E-02 helpers (opencode error, agy failed result, clean log, missing log, over-long message bounded) and for `render_event`'s unchanged error line. No source introspection (AGENTS.md P16).
  - Depends on: E-01, E-03
  - Expected outcome: the module passes, existing `render_stream` and review-orchestrator tests still pass, and the bare suite adds no failure relative to the lane baseline.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `handle_review_orchestrator_readiness` returns the incoming `disposition` unchanged when `exit_code != 0` or the plan is not an orchestrator; only its own refusal path returns `"fail-gate"` by decision.
- Scripted hosts: `tests/test_silent_turn_observability.py` `fake_opencode`.
- One parser per event: `render_stream.render_event` already decodes the opencode `error` event ("this branch DID NOT EXIST, so a real observed event ... rendered as `None`"); agy failures arrive as a `result` record (`agy_runipd.render_agy_event`).
- Diagnostics in the summary go through the existing `Diagnostics / Blocked Items:` block; preserved-lane reasons through `lane_containment.record_lane_preserved` and `format_preserved_lanes` (spec `7ckptx` R5.6/R5.6a).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The child review failed on a provider content filter. | `sessions/09-2j4pd0-attempt-1.jsonl` last records: `"reason":"content-filter"` then `{"type":"error",...,"error":{"name":"ContentFilterError","data":{"message":"The response was blocked by the provider's content filter"}}}`. |
| F-02 | The run blamed orchestrator readiness. | Event `worktree-preserved` for `2j4pd0`: `"reason": "review orchestrator readiness failed; lane preserved for inspection"`, `"retention_reasons": ["review-orchestrator-failed"]`; `2j4pd0` is `- Kind: child`. |
| F-03 | The caller's test conflates "already failed" with "readiness refused". | `execute_item_core`: `if review_orch_disp == "fail-gate":` after `handle_review_orchestrator_readiness(..., disposition=disposition, exit_code=exit_code)`, whose first lines are `if exit_code != 0: return disposition`. |
| F-04 | (review) There are two call sites with the same test. | `execute_item_core`: the isolated-lane review branch (`tree=Path(wt_handle.path)`, then `record_lane_preserved(..., reason="review orchestrator readiness failed; lane preserved for inspection")`) and the non-isolated branch (`tree=repo`, `wt_handle=None`, status only). |
| F-05 | (review) The opencode error event is already decoded. | `render_stream.render_event`, `if etype == "error":` branch; review run: `render_event(json.dumps(ev), Palette(False), use_unicode=False)` printed `! diag:  ContentFilterError: The response was blocked by the provider's content filter`. |
| F-06 | (review) The run directory cited by F-01 is not in this lane. | `.aw/records/runs/` is gitignored (`.aw/.gitignore` `records/runs/`), so the fixture is written from F-01's quoted lines. |

## Proposed changes (ordered, validatable)

1. Correct reason selection (E-01).
2. Capture the host's error (E-02).
3. Surface it (E-03).
4. Tests (E-04).

## Deferred / out of scope (with reason)

- Retrying a review that failed on a provider error.
  - Carrier: ytas91

## Scope check

- Over-scope: none. `runner_shared.py` E-01, E-02, E-03 (`write_report`); `render_stream.py` E-02, E-03; `lane_containment.py` E-01 (reason codes); the test module and fixture E-04. `oc_runipd.py` and `agy_runipd.py` stay declared because a host's `write_report` wrapper may need to pass the new section through; if neither changes, acknowledge them with `--scope-ack` at finalize.
- Under-scope: corrected at review: the second call site (F-04), the agy event shape, the reason codes, and the fixture path.

## Required tests / validation

- `python3 -m pytest tests/test_review_failure_reason.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit; record failing node ids before and after, and the bar is an empty after-minus-before set.
- `aw ipd lint --phase pre-transition --agent <this plan>`; `aw sanitize --agent` exit 0 (provider messages reach the report).

## Spec / documentation sync

N/A for specs: no spec text names the review preserved-lane reason (spec `7ckptx` R5.6 requires a reason be recorded, which this keeps and corrects). It adds an attempt field and three retention reason codes; no CHANGELOG entry because the summary line is a diagnostic, not a new command or flag.

## Open questions

### OQ-01: Should a content-filter error get its own disposition?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Dispositions are a closed vocabulary (`runner_shutdown.KNOWN_ITEM_STATUSES`); the error is recorded as `host_error` and `ytas91`'s `turn_failure_kind` decides retry.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the `worktree-preserved` (or equivalent `record_lane_preserved`) event, with `reason` and `retention_reasons`, for cases (a), (b), (c) and (d) of E-04, and each item's final `status` from `state.json` showing dispositions unchanged.
  - Observed evidence:
    ```
    === Case (a): child review content filter error ===
    item final status in state.json: fail-gate
    worktree-preserved event:
    {
      "at": "2026-10-09T04:34:34+00:00",
      "base_commit": "aa43fe4a57a607add942b69b1cd99eabdcecdb0b",
      "branch": "aw/lane/review-sweep-test_run",
      "event": "worktree-preserved",
      "id6": "chd001",
      "lane_id": "review-sweep-test_run",
      "reason": "review turn failed: host ContentFilterError: The response was blocked by the provider's content filter",
      "retention_reasons": [
        "review-host-error"
      ],
      "status": "fail-gate",
      "worktree": "/tmp/tmp22h9infw/repo/.aw/worktrees/review-sweep-test_run"
    }

    === Case (b): child review silent exit 1 ===
    item final status in state.json: fail-gate
    worktree-preserved event:
    {
      "at": "2026-10-09T04:34:35+00:00",
      "base_commit": "1d617eac4f796164c63c1f4fdbd90c2315f2afba",
      "branch": "aw/lane/review-sweep-test_run",
      "event": "worktree-preserved",
      "id6": "chd002",
      "lane_id": "review-sweep-test_run",
      "reason": "review turn exited 1 with no outcome file",
      "retention_reasons": [
        "review-turn-exited"
      ],
      "status": "fail-gate",
      "worktree": "/tmp/tmp9ndn4ea6/repo/.aw/worktrees/review-sweep-test_run"
    }

    === Case (c): orchestrator review readiness fails ===
    item final status in state.json: fail-gate
    worktree-preserved event:
    {
      "at": "2026-10-09T04:34:36+00:00",
      "base_commit": "30940c967273a20cdd4c921604b810693409eefe",
      "branch": "aw/lane/review-sweep-test_run",
      "event": "worktree-preserved",
      "id6": "orc001",
      "lane_id": "review-sweep-test_run",
      "reason": "review orchestrator readiness failed; lane preserved for inspection",
      "retention_reasons": [
        "review-orchestrator-failed"
      ],
      "status": "fail-gate",
      "worktree": "/tmp/tmp1cpz75hs/repo/.aw/worktrees/review-sweep-test_run"
    }

    === Case (d): orchestrator review exit 1 ===
    item final status in state.json: fail-gate
    worktree-preserved event:
    {
      "at": "2026-10-09T04:34:37+00:00",
      "base_commit": "6d768bb25f8cf3ac38f0da86b69e95ae48673c9f",
      "branch": "aw/lane/review-sweep-test_run",
      "event": "worktree-preserved",
      "id6": "orc002",
      "lane_id": "review-sweep-test_run",
      "reason": "review turn exited 1 with no outcome file",
      "retention_reasons": [
        "review-turn-exited"
      ],
      "status": "fail-gate",
      "worktree": "/tmp/tmpxq6qpkxu/repo/.aw/worktrees/review-sweep-test_run"
    }
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a `python3 -c` session printing the scan helper's result on the content-filter fixture, a clean opencode log, an agy failed-result log, an agy SUCCESS log, a missing path, and a 2000-character message (showing the bound), plus `render_event`'s line for the error event matching the review measurement in E-02.
  - Observed evidence:
    ```
    1. content-filter fixture:
       ('ContentFilterError', "The response was blocked by the provider's content filter")
    2. clean opencode log:
       None
    3. agy failed-result log:
       ('FAILED', 'Antigravity model crash')
    4. agy SUCCESS log:
       None
    5. missing path:
       None
    6. 2000-character message (bounded):
       name: 'OverlongError' (len=13)
       msg: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...'XXXXXXXXX…' (len=300)
    7. render_event error line:
       ! diag:  ContentFilterError: The response was blocked by the provider's content filter
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the summary's `Diagnostics / Blocked Items:` block and the `execution-report.md` excerpt naming the host error for case (a), and a `diff` showing the summary and report of a no-error run are unchanged against a run on the pre-change code.
  - Observed evidence:
    ```
    === Case (a) Diagnostics / Blocked Items ===
    Diagnostics / Blocked Items:
      • chd001: fail-gate (the turn PROVABLY attempted nothing: it wrote no outcome file and its lane holds no commit beyond its base and its tree is clean; no host-truncation record accompanied it, which does not weaken the verdict because the evidence conditions are what prove it (the truncation signal is SUPPORTING); attempt log is events)
        host error: ContentFilterError: The response was blocked by the provider's content filter
        → remedy: inspect session log and retry turn for chd001

    === Case (a) execution-report.md excerpt ===
    ## Host errors

    - `chd001`: host ContentFilterError: The response was blocked by the provider's content filter

    ## Review

    Review `decisions-and-questions.md` first, then `outcomes/` and `sessions/`.

    === Clean Run Comparison (Pre-change vs Post-change) ===
    Summary Diff (clean run):
    NO DIFF (byte-identical)

    Report Diff (clean run):
    NO DIFF (byte-identical)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_review_failure_reason.py` with per-test counts, the bare `python3 -m pytest` summary line, and the before and after failing node-id sets showing nothing new.
  - Observed evidence:
    ```
    === python3 -m pytest -o addopts="" -v tests/test_review_failure_reason.py ===
    tests/test_review_failure_reason.py::ReviewFailureReasonIntegrationTests::test_case_c_orchestrator_review_readiness_fails PASSED [  4%]
    tests/test_review_failure_reason.py::ReviewFailureReasonIntegrationTests::test_case_b_child_review_silent_exit_1 PASSED [  9%]
    tests/test_review_failure_reason.py::ReviewFailureReasonIntegrationTests::test_case_d_orchestrator_review_exit_1 PASSED [ 14%]
    tests/test_review_failure_reason.py::ReviewFailureReasonIntegrationTests::test_case_a_child_review_content_filter_error PASSED [ 19%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_host_error_of_event_bounded PASSED [ 23%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_host_error_of_event_clean_event PASSED [ 28%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_render_run_summary_table_host_error_under_bullet PASSED [ 33%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_host_error_of_event_opencode_message_field PASSED [ 38%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_scan_last_host_error_clean_log PASSED [ 42%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_scan_last_host_error_agy_success PASSED [ 47%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_host_error_of_event_agy_success_result PASSED [ 52%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_render_run_summary_table_host_error_own_bullet PASSED [ 57%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_render_event_error_unchanged PASSED [ 61%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_host_error_of_event_opencode_string_data PASSED [ 66%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_scan_last_host_error_agy_failed PASSED [ 71%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_scan_last_host_error_fixture PASSED [ 76%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_host_error_of_event_opencode PASSED [ 80%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_scan_last_host_error_missing_path PASSED [ 85%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_host_error_of_event_agy_failed_result PASSED [ 90%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_host_error_of_event_non_dict PASSED [ 95%]
    tests/test_review_failure_reason.py::HostErrorHelpersUnitTests::test_write_report_byte_identical_when_no_host_error PASSED [100%]
    ============================== 21 passed in 6.50s ==============================

    === Bare python3 -m pytest summary line ===
    6908 passed, 2 skipped, 3 warnings in 722.06s (0:12:02)

    === Baseline Comparison ===
    Before (baseline): 6887 passed, 2 skipped, 3 warnings (0 failures)
    After:              6908 passed, 2 skipped, 3 warnings (0 failures)
    Failing node-id sets (before and after):
    Before: set()
    After:  set()
    After minus before: set() (0 new failures, exactly +21 new tests passed)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract: change no disposition, no retry behavior (owned by `ytas91`, which edits `execute_item_core` too; if it has landed first, rebase onto it and keep its `turn_failure_kind` alongside `host_error`, they answer different questions), and no lane retention decision; only reasons, codes and a recorded field change. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. This is a shared checkout: verify the staged set with `git diff --cached --name-only` and unstage anything not yours with `git restore --staged <path>`. Paste the ACTUAL runner output into each V-item; a summary you did not produce is not evidence. The Scope-Paths are a declaration: a necessary out-of-scope edit is made and justified with `--scope-reason` at finalize. Do not claim done until `aw ipd lint --phase pre-transition` conforms and every V-item carries observed evidence. Under `aw oc run` / `aw agy run` the RUNNER owns the terminal transition, so do not run `aw ipd finalize` yourself; a hand execution runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-edit `- Status:` and never `git mv` into `executed/`.
