# IPD: Consume answers at dispatch checkpoints and resume the parked item in the same session

- Date: 2026-10-17
- Kind: child
- Concern: An answer written to `answers/` (Order 03) changes nothing until the driver reads it. Spec `6kwd2e` R9.3-R9.4 (amended 2026-10-17) require the live driver to consume answers at every dispatch checkpoint, re-queue the answered item AHEAD of not-yet-started work, and resume the SAME agent session with the answer, falling back to a fresh turn on the same preserved lane; R5.6 requires a stale answer (artifact changed since the question) to be refused, not applied.
- Scope: IN: a checkpoint step at the top of both drivers' `run_queue` loops (beside `runner_stop.poll_stop`, the dependency cascade and the deferred-integration retry); staleness check; priority re-queue; same-session resume through the host's own executor launcher with the recorded session id and an answer notice built like `build_fix_it_notice`; fresh-turn fallback on the preserved lane with the answer in the prompt (R5.5); resuming a parked review by merging its `aw/parked/<run_id>/<id6>` branch into the sweep lane; start-of-run and resume drain (the same loop-top call) so answers written while no driver was live are consumed; marking a consumed question `answered` in the inbox and refreshing `open-questions.md`. OUT: re-asking after a stale answer (Order 08 drain), the CLI (Order 05), channels (Orders 09-11).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/question_inbox.py, tests/test_question_resume.py
- Item-Dependencies: executed:mtmqlm
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- From-Spec: 6kwd2e
- Set: qchan
- Order: 4
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: j0ufrj
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make an answer given while a run is live take effect at the next checkpoint, cheaply and in the agent's own context (spec `6kwd2e` R9.3, R9.4, R9.4a, R5.5, R5.6).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: consume at checkpoints

- [x] E-01 Add `consume_answers(run_dir, state) -> list[str]` in `runner_shared.py`: for each `awaiting-human` item, read the answers for the qids of its CURRENT park (the run-scoped qids Order 03 E-03 stores on the item; never every question ever raised for the artifact, which after a re-park (E-04) would count the earlier, already-consumed answers) via `question_inbox.read_answers`; when every `gates_verdict` question of the item is answered (OQ-01), recompute the artifact hash and compare with each answer's `artifact_hash`; on mismatch mark the answer `stale` (event + question status `stale` via `question_inbox.set_question_status`, Order 03 E-05; compute the hash with `runner_shared.sha256_file` over the question's repo-relative `artifact_path` in the main checkout, exactly as Order 03 E-01 captured it), keep the item parked and do not apply it (R5.6, A12); otherwise set the item `queued`, mark it `resume_with_answers`, and record the answers on the item (`item["answers_pending"]`, the list the next attempt's notice is built from). Emit one event per outcome through `append_jsonl`: `answer-consumed` (`id6`, `question_id`, `channel`) for an applied answer and `answer-stale` (`id6`, `question_id`, `expected_hash`, `actual_hash`) for a refused one; a missing or unreadable artifact counts as stale, never as a match. Return the id6s re-queued. Call it at the top of the `run_queue` loop on BOTH hosts (`oc_runipd.run_queue`, `agy_runipd.run_queue`), after `poll_stop` and the state reload and BEFORE the cascade, the `queued = [...]` list and the drain arm, followed by `save_state` and `load_state` when it returned anything (the pattern the cascade uses). The loop top runs before the first selection of every invocation, so this one call site also drains answers written while no driver was live (start and `resume`); do not add a second call before the loop. `consume_answers` must never raise into the loop: an OSError reading the inbox is recorded as an `answer-read-failed` event and the item stays parked.
  - Depends on: none
  - Expected outcome: an answer written while another item runs moves the parked item to `queued` at the next loop iteration with an `answer-consumed` event; a stale one leaves it `awaiting-human` with an `answer-stale` event and the question file `status: stale`.
  - Execution state: performed

- [x] E-02 Give answered items priority (R9.3 "AHEAD of every not-yet-started item"): in the selection step of BOTH hosts' `run_queue`, sort `queued` with the key `(not item.get("resume_with_answers"), *queue_sort_key(item, by_id))`, so answered items come first and dependency depth stays the first key WITHIN each group; the `dependency_status` check that follows is unchanged, so an answered item still dispatches only when satisfied (its prerequisites were satisfied when it first ran, so this does not reorder a dependent ahead of its dependency). Put the key in one shared helper (`runner_shared.dispatch_sort_key`) so the hosts cannot drift.
  - Depends on: E-01
  - Expected outcome: in a 3-item run where item 1 parks and its answer arrives while item 2 runs, item 1 dispatches before item 3 (A43); with no answered item the selection order is identical to `queue_sort_key` alone.
  - Execution state: performed

### Task group 2: resume

- [x] E-03 EXECUTE resume. Add `runner_shared.build_answer_notice(answers) -> str`, shaped like `build_fix_it_notice` (a `## Answers from the maintainer` header, then per question its text, the answer inside a fenced block labelled as quoted human input, and the channel; absolute paths redacted with `_redact_absolute_paths`). In `execute_item_core`'s isolated-execute lane selection, add a branch BESIDE the existing `is_fix_it_recovery` adoption branch, taken when the item carries `resume_with_answers`: resolve the lane with `resolve_prior_lane(item)` (the `preserved_*` fields Order 02 recorded; never reconstruct a branch name) and adopt it with the SAME checks and records that branch uses (`worktree_lease.inspect_lane` registered, `lane_is_safe_to_adopt`, `write_lane_owner`, the `worktree-allocated` event with `disposition: adopted`, `record_allocated_lane`). SESSION: when the parked attempt recorded a `session_id`, set `session_id` to it and `use_continue = False`, so the host's own executor launcher (`spawn_executor` -> `run_opencode(resume_session=...)` / the agy `--conversation` form) carries it and no new launcher caller is added, and send ONLY the answer notice as the prompt (the session already holds the context; spec R9.4 "the answer as the next message"). FALLBACK (R9.4, R5.5): when there is no recorded session id, run a fresh turn (`session_id = None`, `use_continue = False`) in the SAME adopted lane with the notice prepended to the normal execute prompt. Record which path ran as `attempt["answer_resume"] = "session" | "fresh: <reason>"`. REFUSAL: when the preserved lane is absent or not safe to adopt, do NOT allocate a fresh lane (that would silently drop the parked work A6 protects): record an `answer-resume-refused` event and refusal naming the lane, set `fail-lane`, and leave the lane and branch untouched. A session the host itself rejects at launch is not detected in advance; it surfaces as that turn's own failure and is scored by the existing path. After the turn has started (the `ipd-started` event is written), mark each consumed question `answered` with `question_inbox.set_question_status` and clear `resume_with_answers` and `answers_pending`; until then both survive a crash so a `resume` retries the resume.
  - Depends on: E-02
  - Expected outcome: the resumed turn's recorded `attempt["argv"]` carries the parked attempt's session id and its prompt file contains the answer text; with no recorded session, a fresh turn runs in the same lane with the same `preserved_base` and branch and the parked commit still present (A44, A6); with the lane removed the item ends `fail-lane` with an `answer-resume-refused` event and no new lane is allocated.
  - Execution state: performed

- [x] E-06 REVIEW resume. A parked review has no per-item lane: Order 02 (`epsti7` E-06) moved its commits to `aw/parked/<run_id>/<id6>` (`preserved_branch`) and reset the shared sweep lane. In the review branch of `execute_item_core`, after `acquire_review_sweep_lane` returns the lane and BEFORE `attempt["review_lane_tip_before"]` is recorded, when the item carries `resume_with_answers`: refuse on a dirty sweep lane (the `git status --porcelain` check `refresh_sweep_lane` makes), then `git merge --no-ff` the parked branch into the sweep lane (a fast-forward is impossible once a later review has committed on the lane; demonstrated at review, see D-3). On a merge conflict, `git merge --abort`, leave the parked branch, record an `answer-resume-refused` event and set the item `fail-merge`, so no review work is lost. On success record `review_lane_tip_before` AFTER the merge, so the parked work belongs to this review's integration range and lands on main with it. SESSION: reviews share the sweep session (`REVIEW_SWEEP_SESSION_KEY`), so the resumed review keeps using it as today and the answer notice (E-03 `build_answer_notice`) is prepended to the normal review prompt; this IS the same agent session R9.4 asks for whenever the sweep session has not rotated, and the R9.4 fresh-turn fallback otherwise. Delete the parked branch only after `integrate_review_lane_branch` reports the review integrated; on a deferred or refused integration keep it. Mark questions `answered` as in E-03.
  - Depends on: E-03
  - Expected outcome: in a run where review A parks, review B then commits on the sweep lane, and A's answer arrives, A's resumed turn starts on a sweep lane containing both B's commit and A's parked commit; after A integrates, main holds A's parked change and `aw/parked/<run_id>/<A id6>` is gone; a conflicting parked branch leaves the item `fail-merge`, the sweep lane at its prior tip, and the parked branch present.
  - Execution state: performed

- [x] E-04 Re-park if the resumed turn asks again: the Order 02 park branch already handles a new `questions[]`, and Order 03 gives each attempt's questions distinct qids (`-a<attempt>-`), so a reused worker id cannot collide. Ensure the earlier answered questions stay `answered`, the item's current-park qid list (E-01) is REPLACED by the new attempt's qids, only the new ones are written `open`, and a resumed REVIEW that parks again goes back through Order 02's sweep-lane park (its new parked branch then carries both the earlier and the new commits).
  - Depends on: E-06
  - Expected outcome: a scripted resumed turn that returns a second question ends `awaiting-human` with the first question `answered`, the second `open`, and the item's qid list naming only the second; the next checkpoint does not re-queue it until the second is answered.
  - Execution state: performed

### Task group 3: tests

- [x] E-05 Add `tests/test_question_resume.py` on BOTH hosts with the scripted-host pattern (`tests/test_run_proposal_channel.py`), asserting spec `6kwd2e` A6, A12, A36, A37, A43, A44: checkpoint consumption mid-run (A43: the answer is written by the scripted host DURING item 2's turn), priority and unchanged order with no answered item, same-session resume and fresh-turn fallback (A44, A6, asserting lane branch, `preserved_base` and the parked commit), refusal when the preserved lane is gone, staleness including a deleted artifact (A12), start-of-run drain (answer written before `resume`), partial answers (OQ-01: one gating question answered of two does not re-queue; a missing non-gating answer does not block), re-park, the review resume of E-06 including the conflict refusal, and review semantics after an answer: a resumed review whose finding is not cleared still records NO-GO (A36) and no `- Readiness:` value appears that the resumed review did not itself write (A37). Assert dispatch ORDER from `events.jsonl`, never from timing.
  - Depends on: E-04
  - Expected outcome: the module passes on both hosts, and the routine gate passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The `run_queue` loop top already reloads state and runs cheap per-iteration steps (cascade, deferred integration retry); new checkpoint work goes there (`oc_runipd.run_queue` comments).
- Follow-up turns use `runner_shared.resume_via_launcher` so each host keeps exactly two launcher callers (its docstring). A resumed answered item is NOT a follow-up inside a running turn but a new attempt, so it uses the executor launcher with the recorded session, exactly as the `is_fix_it_recovery` branch of `execute_item_core` already resumes a prior session in an adopted lane (`session_id = prior_session_id`, `use_continue = False`); it adds no launcher caller either way.
- Preserved lanes are resolved from `preserved_lane_id`/`preserved_base`/`preserved_branch` through `runner_shared.resolve_prior_lane` (spec `6kwd2e` 0.4), never by reconstructing `aw/lane/<id6>`.
- `oc_runipd.run_queue` already calls `save_state` from several sites, and its docstring notes that a call-site count was once pinned per runner; reuse the cascade's existing `save_state`/`load_state` pattern at the loop top rather than adding persist sites elsewhere.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `resume_via_launcher` already serves combined-red and spec-anchor send-backs, so resuming a session mid-run is proven on both hosts.
- Both drivers re-run selection every iteration, so a status flip at the loop top is picked up without new scheduling machinery.
- Selection today is `sorted(queued, key=lambda it: queue_sort_key(it, by_id))` followed by the first `dependency_status`-satisfied item, on both hosts; a priority prefix on that key is the whole of E-02.
- The loop top runs before the first selection of every invocation (start and `resume` both enter `run_queue`), so one call there covers the start-of-run and resume drain.
- `execute_item_core` resumes a prior session in an adopted lane only on its `is_fix_it_recovery` branch; nothing today routes a parked item back to its preserved lane, so E-03 adds that branch.
- Reviews run in ONE sweep lane with a run-level sweep session (`REVIEW_SWEEP_SESSION_KEY`); `refresh_sweep_lane` is `--ff-only` and refuses on a dirty lane. A parked review's branch cannot be fast-forwarded once a later review has committed on the sweep lane, so E-06 merges it (demonstrated at review, D-3).

## Proposed changes (ordered, validatable)

1. E-01 consume + staleness. 2. E-02 priority. 3. E-03 execute resume and fallback. 4. E-06 review resume from the parked branch. 5. E-04 re-park. 6. E-05 tests.

## Deferred / out of scope (with reason)

- Re-asking a stale question interactively: Order 08.
  - Carrier: jshwxb
- Notifying the human that an answer was consumed: Order 09 (R10.7).
  - Carrier: txl556

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" tests/test_question_resume.py tests/test_question_parking.py tests/test_question_inbox.py` (no `-q`, so the `N passed` line prints) and the routine gate `python3 -m pytest`.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R9.3, R9.4, R5.5, R5.6 as amended; no spec file is edited. R9.4 names `runner_shared.resume_via_launcher` as "the mechanism the fix-it send-backs already use"; this plan resumes the recorded session through the host's executor launcher instead (the same host launcher, with the session flag), because the resumed answered item is a new attempt that must still pass begin, verification, finalize and integration, which an in-turn `resume_via_launcher` call would skip. The normative content of R9.4 (same session, host's own launcher, answer as the next message, fresh-turn fallback on the same preserved lane, staleness first) is met unchanged (review decision D-2).

## Open questions

### OQ-01: Resume when SOME but not all of an item's questions are answered?

- Blocking: no
- Status: resolved
- Owner: plan author (decided at authoring, not by the maintainer; recorded at review as decision D-1)
- Resolution or deferral rationale: RESOLVED: no, unless every unanswered one has `gates_verdict: false`. A turn resumed with a decision still missing would park again immediately and spend a turn for nothing; non-gating questions do not block resumption (they are still delivered as answered or 'unanswered' in the notice).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the event lines from a scripted run showing `answer-consumed` for the parked item at the checkpoint after the answer was written (and, for the start-of-run drain, as the first event of the resumed invocation before any `ipd-started`), and `answer-stale` for the stale case with the item still `awaiting-human` and the question file's `status: stale` (produced by E-01's `consume_answers` call at the top of `run_queue`).
  - Observed evidence:
    Event line for answer-consumed at checkpoint:
    ```json
    {"at": "2026-10-18T01:01:30+00:00", "channel": "cli", "event": "answer-consumed", "id6": "res001", "question_id": "01-res001-a1-q-timeout-val"}
    ```
    Start-of-run drain event before any ipd-started:
    ```json
    {"at": "2026-10-18T00:59:25+00:00", "channel": "cli", "event": "answer-consumed", "id6": "drn001", "question_id": "01-drn001-a1-q-drain"}
    ```
    Event line for answer-stale when artifact is modified:
    ```json
    {"actual_hash": "79666e26076139d4a2256de92cd21908fe64deb686d32664a9e659422ea0e0b2", "at": "2026-10-18T00:59:22+00:00", "event": "answer-stale", "expected_hash": "03384d8daa57472b5315bc1b8968a700469cac0a5f9adc1cfe36ad82187b434e", "id6": "stl001", "question_id": "01-stl001-a1-q-stale"}
    ```
    Item status remains `awaiting-human` and question file status is `stale`:
    ```json
    {"status": "stale"}
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the ordered `ipd-started` events from the A43 fixture showing item 1 (attempt 2) started before item 3, and the same fixture without an answer showing the order `queue_sort_key` alone gives (produced by E-02's `dispatch_sort_key` in both hosts' selection step).
  - Observed evidence:
    Ordered `ipd-started` events with answer arriving mid-run (res001 attempt 2 dispatched before res003):
    ```
    ipd-started: id6=res001 attempt=1
    ipd-started: id6=res002 attempt=1
    ipd-started: id6=res001 attempt=2
    ipd-started: id6=res003 attempt=1
    ```
    Same fixture without answer (queue_sort_key alone):
    ```
    ipd-started: id6=res001 attempt=1
    ipd-started: id6=res002 attempt=1
    ipd-started: id6=res003 attempt=1
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the resumed attempt's recorded `argv` showing the parked attempt's session id and `answer_resume: session`, an excerpt of its prompt file containing the answer; for the fallback case `answer_resume: fresh: ...`, the attempt's `worktree_branch`/`worktree_base` beside the item's `preserved_branch`/`preserved_base` (equal), and `git log` of that branch showing the parked commit; for the refusal case the `answer-resume-refused` event and item status `fail-lane` (produced by E-03's branch in `execute_item_core`).
  - Observed evidence:
    Session resume attempt record:
    ```json
    "answer_resume": "session",
    "argv": ["/tmp/tmp_bin/fake_agent", "--session", "ses-1", "--format", "json"]
    ```
    Session prompt file excerpt:
    ```markdown
    ## Answers from the maintainer

    ### Question: 01-ses001-a1-q-cache-mode
    What cache mode to use?

    ```text quoted human input
    use redis clustered cache
    ```
    Channel: cli
    ```
    Fallback case (`answer_resume: fresh: no prior session recorded`):
    ```
    att_fbk2["worktree_branch"] == item_fbk["preserved_branch"] == "aw/lane/fbk002"
    att_fbk2["worktree_base"] == item_fbk["preserved_base"]
    git log: "fallback attempt 1 commit" present on branch aw/lane/fbk002
    ```
    Refusal case on missing preserved lane:
    ```json
    {"at": "2026-10-18T01:02:28+00:00", "event": "answer-resume-refused", "id6": "ref001", "lane_id": "ref001", "reason": "prior lane 'ref001' is not registered in git"}
    ```
    Item status: `fail-lane`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the final question statuses showing the first `answered` and the second `open` after re-park, the item's stored qid list naming only the second, and the next checkpoint's events showing no `answer-consumed` for the item.
  - Observed evidence:
    Final question statuses in inbox after attempt 2 re-parks:
    ```
    qid1 (01-rep001-a1-q-step-1): answered
    qid2 (01-rep001-a2-q-step-2): open
    ```
    Item's stored question_ids list:
    ```json
    ["01-rep001-a2-q-step-2"]
    ```
    Next checkpoint call to `consume_answers(run_dir, state)` returns `[]`, emitting no `answer-consumed` events for rep001.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
    Specific test suite:
    ```
    $ python3 -m pytest tests/test_question_resume.py tests/test_question_parking.py tests/test_question_inbox.py
    ..............................                                           [100%]
    30 passed in 13.96s
    ```
    Routine gate:
    ```
    $ python3 -m pytest
    ........................................................................ [  7%]
    ........................................................................ [ 14%]
    ........................................................................ [ 21%]
    ........................................................................ [ 29%]
    ........................................................................ [ 36%]
    ........................................................................ [ 43%]
    ......................................................................... [ 50%]
    ........................................................................ [ 58%]
    ........................................................................ [ 65%]
    ........................................................................ [ 72%]
    ........................................................................ [ 79%]
    ........................................................................ [ 87%]
    ........................................................................ [ 94%]
    .........................................................                [100%]
    993 passed in 28.95s
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: from the two-review fixture, paste `git log --oneline --graph` of the sweep lane at the resumed review's `ipd-started` (showing review B's commit and the merged parked commit), `git log --oneline main` after A integrates (A's parked change present), `git branch --list 'aw/parked/*'` before and after (the branch gone after integration); for the conflict case the `answer-resume-refused` event, item status `fail-merge`, the sweep lane's `rev-parse HEAD` equal to its prior tip and the parked branch still listed (produced by E-06's branch in `execute_item_core`).
  - Observed evidence:
    Sweep lane git log at resumed review turn start showing merge of parked branch:
    ```
    *   6129118 merge parked review branch aw/parked/run-review-resume/rva001
    |\
    | * 8eea6d5 review A initial finding
    * | ba6672b review B approve findings
    |/
    * 5fd07e4 add plan rvb002
    ```
    Main git log after review A integration showing both commits present on main:
    ```
    6fa1689 review A post-answer approval
    6129118 merge parked review branch aw/parked/run-review-resume/rva001
    ba6672b review B approve findings
    8eea6d5 review A initial finding
    ```
    Parked branch check:
    ```
    Before integration: aw/parked/run-review-resume/rva001
    After integration: (empty - branch deleted)
    ```
    Merge conflict refusal:
    ```json
    {"at": "2026-10-18T01:03:26+00:00", "branch": "aw/parked/run-review-resume/rvc003", "event": "answer-resume-refused", "id6": "rvc003", "reason": "merge conflict merging parked branch aw/parked/run-review-resume/rvc003 into sweep lane"}
    ```
    Item status: `fail-merge`
    Sweep lane tip preserved at prior commit, parked branch `aw/parked/run-review-resume/rvc003` remains present.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
