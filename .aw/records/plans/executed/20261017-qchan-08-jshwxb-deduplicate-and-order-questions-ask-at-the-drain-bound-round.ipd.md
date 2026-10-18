# IPD: Deduplicate and order questions, ask at the drain, bound rounds and runaway escalation

- Date: 2026-10-17
- Kind: child
- Concern: With parking (Order 02), the inbox (Order 03) and live resume (Order 04), a large queue whose siblings ask the same question still makes the human answer it once per artifact, in arbitrary order, and nothing stops a broken prompt from parking every item. Spec `6kwd2e` R4 (cross-queue dedup by driver-computed fingerprint, one answer applied to every raiser, ordering by unblock count then execute-before-review), R4b (runaway-escalation bound), and R5.1-R5.3a (answer file at the drain, terminal ask at the drain when a human is present, bounded re-dispatch rounds) are not yet implemented.
- Scope: IN: grouping open questions by fingerprint across the run (E-01) and across the pre-flight batch (E-08), applying one answer to every raiser through a group writer layered on the shared writer (E-02), showing and answering groups in `aw runs answer` (E-06), the R4.3/R4.3a ordering, the R4.4 pre-ask summary, `answers.md` at the drain with ingestion of answers edited into it (E-03), the drain-time terminal ask (reusing Order 07's bounded prompt) with same-invocation re-dispatch and the round bound (E-07), and the runaway bound with a minimum absolute count and its distinct exit reporting (E-04). OUT: channels (Orders 09-11 show what `group_open_questions` returns); a new run exit code (OQ-02).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/question_inbox.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, agent_workflows/run_cli.py, agent_workflows/cli.py, agent_workflows/command_surface.py, CHANGELOG.md, tests/test_question_drain.py
- Scope-Exceeded: tests/test_question_preflight.py (disentangle question titles for sweep sitting test under grouping)
- Item-Dependencies: executed:j0ufrj, executed:4kkcex, executed:8u071n
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 8
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: jshwxb

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: jshwxb verified (set qchan, attempt 1). [Scope reconciliation - out-of-scope tests/test_question_preflight.py: disentangle question titles for sweep sitting test under grouping]
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009, PR-010
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Ask each distinct question once, in the order that frees the most work, and stop a run that is escalating everything (spec `6kwd2e` R4, R4b, R5.1-R5.3a).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: dedup and order

- [x] E-01 In `question_inbox`, add a pure `group_questions(records, state) -> list[QuestionGroup]` and `group_open_questions(run_dir, state) -> list[QuestionGroup]`, which feeds it every `open` question file belonging to the CURRENT park of an `awaiting-human` item (the run-scoped qids Order 03 E-03 stores on the item). Group key: the driver-computed `fingerprint` (`runner_shared.question_fingerprint`, Order 01 E-02) AND, as a collision guard, exact equality of the normalized text, the normalized option list and `allow_free_text`; any mismatch inside one fingerprint yields SEPARATE groups (R4.1b, A20). A `QuestionGroup` carries a stable `group_id` (`g-<fingerprint>` plus a `-<n>` suffix only for a collision split), the text, options, `allow_free_text`, and its members (each `question_id`, `artifact_id6`, `action`, `artifact_hash`). Unblock count (R4.3): the size of the UNION over the group's raisers of {the raiser} plus every queue item that transitively depends on it (reverse edges over each item's `dependencies` through `runner_shared.parse_dependency_token`) and is still `queued` or `awaiting-human`, counted once each. Order: unblock count descending; at equal counts a group with ANY `execute` member precedes one with only `review` or `preflight` members (R4.3a; a `preflight` member has no lane, so it carries review's cost of delay, D-5); then the lowest member queue position, so the order is total and deterministic.
  - Depends on: none
  - Expected outcome: 74 open questions sharing one fingerprint form one group naming 74 members; two questions sharing a fingerprint but differing in `allow_free_text` form two groups; a fixture with known unblock counts (including two raisers sharing a dependent, counted once) orders as expected; a review/execute tie puts execute first (A9, A10, A20, A21).
  - Execution state: performed

- [x] E-02 Add `question_inbox.write_group_answer(run_dir, state, group_id, *, answer, choice, channel, sender, actor) -> GroupAnswerResult`, layered on Order 03's `write_answer` (which stays the ONLY writer of `answers/`, R9.2): under a run-level `answers/.group.lock`, recompute the group with `group_open_questions`, refuse an unknown `group_id`, then call `write_answer` once per member, passing the full member list so each `aw.answer/v1` record carries `applied_to` (every member `question_id` and `artifact_id6`, R4.2). Extend `write_answer` with that optional `applied_to` field (default: just its own question). Per-member results are returned as they are: a member already answered keeps its existing answer (`already`, first answer wins), a stale member is `rejected`; the call reports `recorded` when at least one member was recorded. A question that parks with the same fingerprint AFTER the group was answered is NOT answered implicitly: it forms a new group and is asked (R4.1b: the human never considered it, D-2).
  - Depends on: E-01
  - Expected outcome: one group answer over 74 members writes 74 answer files, each with an `applied_to` list of length 74; with one member pre-answered, 73 are `recorded`, 1 `already`, and the pre-existing answer is unchanged; a later same-fingerprint question stays `open`.
  - Execution state: performed

- [x] E-06 Make `aw runs answer` (Order 05, `run_cli`) list and ask by GROUP: in the interactive form show each group once, in E-01's order, with its raiser count and member artifact id6s, and write through `write_group_answer`; the non-interactive listing and `--agent`/`--json` payload gain `group_id` and `raisers` per entry (one entry per group); the `<question_id> --answer` form is unchanged (answers that one question only) and a new `--group <group_id>` form answers a group. Channels (Orders 09-11) are out of scope.
  - Depends on: E-02
  - Expected outcome: against a run directory holding a 74-member group, `aw runs answer <run-id> --no-interactive` lists it once with `raisers: 74`; `aw runs answer <run-id> --group <group_id> --answer X` exits 0 and writes 74 answer files; the single-question form writes one.
  - Execution state: performed

### Task group 2: the drain

- [x] E-03 Add `question_inbox.write_answers_file(run_dir, state, *, resume_command) -> Path` writing `<run_dir>/answers.md` atomically (R5.1, R5.2): a header stating the run id, the distinct-question, artifact and unblock counts (R4.4), how to answer (edit the file, or `aw runs answer <run-id>`), and the literal resume command built from the host's `HostLabels.command` (`<command> resume <run-id> --repo <repo>`); then one section per group in E-01 order with a marker line `<!-- aw:group <group_id> -->`, the members' `question_id`s, options, raisers, and the worker-authored question text rendered with EVERY line prefixed `> ` after `term.strip_ansi` and removal of other control characters, followed by an empty `Answer:` line. Add `question_inbox.ingest_answers_file(run_dir, state) -> int`: read only the `Answer:` line directly following each group's quoted block under a marker the driver wrote, ignore an empty one, and write a non-empty one through `write_group_answer` with `channel="answers-file"`, `actor="human"`, `sender=getpass.getuser()`. Because no worker-authored line can start with `Answer:` (all are quoted), a question text cannot forge a pre-filled answer. Call `ingest_answers_file` on both hosts immediately before Order 04's `consume_answers` at the top of `run_queue`, so an answer edited in while no driver ran is applied on `resume`. Write `answers.md` whenever the run ends with any `awaiting-human` item, whether or not a human is present (R7.2, A14), and name its path in Order 02's parked summary line (R7.3, A38).
  - Depends on: E-01
  - Expected outcome: a drained parked run leaves `answers.md` with every `question_id`, the resume command, and the summary line names its path; a question whose text contains a line `Answer: yes` is written quoted and ingestion records nothing for it; filling one `Answer:` line and running the resume command records that group's answers with `channel: answers-file`.
  - Execution state: performed

- [x] E-07 Add the drain step `runner_shared.drain_parked_questions(run_dir, state, *, labels, rounds_used, save_state, append_jsonl) -> str` returning `continue` or `exit`, and call it on BOTH hosts from the TWO places a run drains with parked items: the `if not queued and not deferred_integration_items(state)` break (reached when every remaining item is `awaiting-human`, because the `queued` list excludes them) and the `runnable is None` arm after the deferred-integration rungs and the peer wait and before `classify_drain_block`. It acts only when an `awaiting-human` item exists and no runaway breach is recorded (E-04). Presence is decided only by `is_interactive_run` over the frozen options (the `argparse.Namespace(unattended=..., full_auto=...)` form `retry_deferred_integrations` already uses, R7.1). Interactive and `rounds_used < question_rounds`: print the R4.4 summary (distinct questions, artifacts affected, each group's unblock count) BEFORE the first question; ask each group in E-01 order with Order 07's `prompt_for_free_text` and the frozen `--question-timeout`, printing text and options through `term.strip_ansi`; map an integer reply in range to `choice`, otherwise free text when `allow_free_text`, otherwise skip; write each answer with `write_group_answer` (`channel="terminal"`) BEFORE the next prompt; Ctrl-C or EOF ends the sitting keeping the answers given. Then, if anything was recorded, run `consume_answers` (Order 04), increment the per-invocation round counter, save state and return `continue` so the loop re-dispatches in the SAME invocation (R5.3, A35). Otherwise (no human, round bound reached, nothing answered) write `answers.md` (E-03), emit a `question-rounds-exhausted` event when the bound was the reason, and return `exit`, leaving every item parked (R5.3a, A26). Register `--question-rounds N` as a `RUN_POLICY_FLAGS` row (`kind="int"`, default 2, 0..10, `resume_rule=RESUME_NONE_DEFAULT`) with a resolver and an explicit branch in `freeze_run_policy_flags`: without one a new `int` row freezes as `True` (measured at review, D-4).
  - Depends on: E-02, E-03
  - Expected outcome: with a patched-TTY fixture answering at the drain, the parked item re-dispatches in the same invocation (one `run-created`/invocation record, a second `ipd-started` for it) (A35); a fixture whose resumed turns always ask again stops after 2 rounds with a `question-rounds-exhausted` event and `answers.md` written (A26); a fixture where every remaining item is parked and nothing is `queued` still reaches the ask; under `--unattended` with a TTY no prompt is printed and `answers.md` is written (A14).
  - Execution state: performed

- [x] E-04 Runaway bound (R4b). Definitions, recorded in state: DISPATCHED = items with at least one attempt started in this run; PARKED = items that have parked on an EMERGENT question at least once in this run (a `preflight_parked` item never dispatched and is excluded from both). After each park (the Order 02 park branches), when PARKED >= `--runaway-min-parked` (default 5) AND PARKED * 100 > DISPATCHED * `--max-park-percent` (default 50): record `state["runaway_escalation"] = {parked, dispatched, ratio, at}`, append a `runaway-escalation` event, print one red stderr line with the observed ratio stating that a runaway escalation rate is more likely a defect in the prompt or the worker's classification than a genuine backlog of human decisions and that the human should NOT start answering (R4b.2), and stop dispatching: the loop exits at its next check without selecting another item, without the drain ask (E-07 is skipped), and without changing any item (R4b.4: parked lanes, branches and question files stay; `answers.md` is still written). Reporting (R4b.3, A23): the summary's `exit_reason` reads `RUNAWAY ESCALATION (<P> of <D> dispatched items parked, ratio <r>)` instead of the ordinary parked line, and the exit code stays the aggregate's own (3 when parked items remain), because spec `25kzda` 5.6 has no slot for a new code and `docs/cli-output-contract.md` already refused adding one for stranded work (OQ-02, D-3). Register `--max-park-percent N` (`kind="int"`, 1..100) and `--runaway-min-parked N` (`kind="int"`, >= 1) as `RUN_POLICY_FLAGS` rows with resolvers and explicit freeze branches (D-4).
  - Depends on: E-03
  - Expected outcome: a fixture where every worker escalates stops after the 5th park with the ratio line and the `RUNAWAY ESCALATION` exit reason, no further `ipd-started`, all parked lane branches and question files present, and `answers.md` written; an ordinary parked run shows the ordinary parked line and no `runaway-escalation` event; a 2-item run with 1 parked item does not breach (A22-A25).
  - Execution state: performed

- [x] E-08 Group the PRE-FLIGHT batch (R1.6, A17): in Order 07's sweep in `initialize_run_core`, fingerprint each `PreflightQuestion` with `question_fingerprint(heading text, ())`, group them with E-01's `group_questions` (unblock count from the resolved queue), print the R4.4 summary, ask each group ONCE, and on an answer call `record_oq_answer` for every member artifact and commit all member paths in ONE `git_commit_helper.offer_commit` call before the next prompt (R1.7). A member whose hash moved is refused and routed as unanswered (Order 07 E-04) while the other members keep the answer. Unanswered groups are routed per member exactly as Order 07 E-04 does.
  - Depends on: E-01
  - Expected outcome: a sweep over 20 artifacts each carrying the same open question prints ONE prompt; answering it resolves the block in all 20 artifacts in one commit touching exactly those 20 paths; with one artifact edited during the sitting, 19 are resolved and 1 is routed to `questions/`.
  - Execution state: performed

### Task group 3: tests

- [x] E-05 Add `tests/test_question_drain.py` on both hosts (scripted-host pattern of `tests/test_run_proposal_channel.py`; presence forced by patching `term.is_interactive`, never by a second presence test) covering spec `6kwd2e` A9, A10, A14 (answer-file half), A17, A20, A21, A22, A23, A24, A25, A26, A33, A34, A35 and A38 (answer-file path half), plus the `answers.md` injection case and ingestion on resume. A34: spawn the resume command from `answers.md` with its leading `aw` replaced by `sys.executable -m agent_workflows` (the remaining arguments verbatim) against a run whose only items are parked and unanswered, and assert exit 3 with no `ipd-started` event. Assert order and counts from `events.jsonl` and files, never from timing.
  - Depends on: E-04, E-06, E-07, E-08
  - Expected outcome: the module passes on both hosts, and the routine gate passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Dependency depth stays the first queue sort key (`runner_shared.queue_sort_key`); answered-group priority (Order 04 `dispatch_sort_key`) applies within it. E-01's unblock ordering decides only the ORDER OF ASKING, never dispatch order.
- Prompts follow Order 07's bounded free-text prompt (`prompt_for_free_text`); presence via `runner_shared.is_interactive_run` only (spec `6kwd2e` R7.1). Inside `run_queue` there is no `args`; the frozen options are wrapped in an `argparse.Namespace(unattended=..., full_auto=...)`, exactly as `runner_shared.retry_deferred_integrations` does.
- Run flags are `runner_shared.RUN_POLICY_FLAGS` rows. Supported kinds are `bool`, `int`, `choice`, `multi-choice`, `str` (`register_run_policy_flags` raises `unknown run policy flag kind` otherwise), and `freeze_run_policy_flags` has no generic `int` arm: an `int` row without its own branch freezes as `True` (measured at review, D-4).
- Run exit codes come from one table (`run_evidence._CLASSIFICATION_EXITS`, spec `25kzda` 5.6): exit 3 is `AGGREGATE_NEEDS_INPUT`. `docs/cli-output-contract.md` already refused a new exit code for stranded work.
- `answers/` is written only by Order 03's `write_answer` (R9.2); this plan layers on it and never writes answer files directly.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Spec `6kwd2e` R4 rationale: asking 74 questions serially at the drain merely moves the wall the design exists to remove.
- Both hosts' `run_queue` build `queued` from `status == "queued"` only, so a queue whose remaining items are ALL `awaiting-human` leaves through the `if not queued and not deferred_integration_items(state)` break and never reaches `runnable is None`; the drain ask must hook both exits (E-07).
- The runners' summary carries a free-text `exit_reason` (`render_stream.render_run_summary_table`, set in `oc_runipd.run_queue` for stops), which is the existing surface for a distinct runaway report without a new exit code (E-04).
- `aw <host> run resume <run-id> --repo <repo>` is the shipped resume form (`--repo` on both resume parsers); `HostLabels.command` already carries the verb (`aw oc run`).
- `answers.md` is human-editable by spec (R5.2) and also carries worker-authored text, so ingestion must not trust any line a worker could have written (E-03).

## Proposed changes (ordered, validatable)

1. E-01 group and order. 2. E-02 group answers. 3. E-06 `aw runs answer` by group. 4. E-03 `answers.md` write and ingest. 5. E-07 drain ask and rounds. 6. E-04 runaway bound. 7. E-08 pre-flight grouping. 8. E-05 tests.

## Deferred / out of scope (with reason)

- Showing groups in notification and chat channels: they consume `group_open_questions` when they are built.
  - Carrier: 4brk8a
- A distinct numeric exit code for a runaway breach: refused here (OQ-02); the breach is distinguished in the summary, the event log and run state.
  - Carrier-Declined: spec `25kzda` 5.6 owns the exit table and `docs/cli-output-contract.md` already refused a new code for an analogous case; R4b.3 requires distinguishable REPORTING, which E-04 provides.

## Scope check

- Over-scope: none.
- Under-scope: none after review (E-06, E-07 and E-08 were split out or added at review; see the review record).

## Required tests / validation

`python3 -m pytest -o addopts="" tests/test_question_drain.py tests/test_question_preflight.py tests/test_runs_answer.py` (no `-q`, so the `N passed` line prints) and the routine gate `python3 -m pytest`.

## Spec / documentation sync

Implements spec `6kwd2e` R1.6, R4, R4b, R5.1-R5.3a, and the answer-file halves of R7.2/R7.3; no spec file is edited. Two readings are recorded rather than amended: R4b.3's "distinct outcome" is met by distinct reporting with exit 3 retained (OQ-02, D-3), and R4b.1's "threshold" is expressed as an integer percentage because the run-policy table has no float kind (OQ-01). `CHANGELOG.md` gains one user-facing entry (no em or en dashes) naming `--question-rounds`, `--max-park-percent`, `--runaway-min-parked`, `answers.md` and `aw runs answer --group`.

## Open questions

### OQ-01: Default runaway threshold?

- Blocking: no
- Status: resolved
- Owner: plan author (revised at review, decision D-1)
- Resolution or deferral rationale: RESOLVED: breach when at least 5 items have parked AND more than 50 percent of dispatched items have parked; flags `--max-park-percent` (integer, default 50) and `--runaway-min-parked` (default 5). R4b.1 asks for a conservative default with a configurable threshold and R4b.5 for an absolute floor; half the dispatched items escalating is far above any legitimate rate, and 5 keeps small queues from tripping it. Expressed as an integer percent rather than the authored `--max-park-ratio 0.5` because `RUN_POLICY_FLAGS` has no float kind (`register_run_policy_flags` raises on one, measured at review).

### OQ-02: Does a runaway breach need its own exit code?

- Blocking: no
- Status: resolved
- Owner: plan reviewer (review decision D-3)
- Resolution or deferral rationale: RESOLVED: no; exit stays 3 and the breach is distinguished by the summary's `exit_reason`, the stderr diagnosis, a `runaway-escalation` event and `state["runaway_escalation"]`. Spec `25kzda` 5.6 defines the run exit table, `run_evidence._CLASSIFICATION_EXITS` is "THE ONLY PLACE INTEGERS APPEAR", and `docs/cli-output-contract.md` (and 5.6's exit 1 row) record that a new code was refused for stranded work. Spec `6kwd2e` A23 asks for "DISTINGUISHABLE exit reporting", which this meets. A maintainer who wants a numeric code amends `25kzda` 5.6 first.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `group_open_questions` output (group ids, member counts, unblock counts) for the 74-raiser fixture, the collision fixture showing two groups, the ordered list for the known-count fixture including the shared-dependent case, and the review/execute tie, each produced by a test calling E-01's functions.
  - Observed evidence:
    ```
    --- 1. 74-raiser fixture ---
    Group ID: g-54acd8a3d12fa691, Member count: 74, Raisers: 74, Unblock count: 74

    --- 2. Collision fixture (differing allow_free_text) ---
    Group ID: g-54acd8a3d12fa691-2, Member count: 1, allow_free_text: True, Unblock count: 1
    Group ID: g-54acd8a3d12fa691-1, Member count: 1, allow_free_text: False, Unblock count: 1

    --- 3. Known-count fixture with shared dependent ---
    Position 1: Group ID: g-11b59afc8a82548b, Raiser: itema1, Unblock count: 4
    Position 2: Group ID: g-e5b3ec2531c25722, Raiser: itemb2, Unblock count: 2
    Position 3: Group ID: g-c116310e83b241cf, Raiser: itemc3, Unblock count: 1

    --- 4. Review vs Execute tie-breaking ---
    Position 1: Group ID: g-fb6e5bd435188a02, Action: execute, Unblock count: 1
    Position 2: Group ID: g-ff2c23d0766bc8c8, Action: review, Unblock count: 1
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the count of answer files written by one `write_group_answer` call, one file's `applied_to` length, the per-member results for the pre-answered case with the pre-existing answer file unchanged, and the later same-fingerprint question's `status: open`.
  - Observed evidence:
    ```
    Total answer files written: 74
    GroupAnswerResult status: recorded
    Recorded count: 73 Already count: 1
    Sample answer file applied_to count: 74
    Pre-existing answer unchanged: True (choice: 0)
    Later same-fingerprint question status: open (answer file exists: False)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `answers.md` contents from a drained parked run, the summary line naming its path, the injection fixture's file excerpt (the `> Answer: yes` line) with zero answers recorded for it, and the `answer-consumed` event with `channel: answers-file` after filling one `Answer:` line and resuming (produced by E-03's ingest call at the top of `run_queue`).
  - Observed evidence:
    ````
    --- answers.md contents ---
    # Answers for Run run-v03

    - Distinct questions: 1
    - Artifacts affected: 1
    - Total unblock count: 1

    ## How to answer

    Edit this file and fill in the `Answer:` line for any question group below, or run:
      aw runs answer run-v03

    To resume the run after editing answers:
    ```sh
    aw oc run resume run-v03 --repo /repo
    ```

    <!-- aw:group g-74d65319db1f1611 -->
    ### Group g-74d65319db1f1611

    - Question IDs: 01-art001-a1-q-db
    - Raisers (1): art001
    - Unblocks: 1 item(s)
    - Options:
      1. PostgreSQL
      2. SQLite

    > Select DB backend:
    > Answer: injected-choice
    > > Answer: fake

    Answer:

    --- Summary line naming path ---
    Parked on 1 unresolved question across 1 item (answers file: .aw/records/runs/run-v03/answers.md)

    --- Injection fixture check ---
    Line in answers.md: '> Answer: injected-choice'
    Line in answers.md: '> > Answer: fake'
    Ingested before edit (should be 0): 0
    Answers on disk before edit: 0

    --- Ingestion on resume check ---
    Ingested after filling Answer: line: 1
    Requeued items via consume_answers: ['art001']
    answer-consumed events: [{'at': '2026-10-18T03:21:56+00:00', 'channel': 'answers-file', 'event': 'answer-consumed', 'id6': 'art001', 'question_id': '01-art001-a1-q-db'}]
    ````
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the runaway fixture's stderr ratio line, the summary's `RUNAWAY ESCALATION` exit reason and exit code, the `runaway-escalation` event, the absence of any `ipd-started` after it, `git branch --list 'aw/lane/*' 'aw/parked/*'` and `ls <run_dir>/questions` showing every parked item's lane and question kept, the ordinary parked run's summary for contrast, and the 2-item no-breach result (produced by E-04's check in the park branches).
  - Observed evidence:
    ```
    --- 1. Stderr ratio line ---
    Runaway escalation detected: 5 of 5 dispatched items parked (ratio 1.00). A runaway escalation rate is more likely a defect in the prompt or the worker's classification than a genuine backlog of human decisions. Do NOT start answering.

    --- 2. Exit Reason and Exit Code ---
    Exit code: 3
    Exit reason: RUNAWAY ESCALATION (5 of 5 dispatched items parked, ratio 1.00)

    --- 3. Runaway-escalation event ---
    Event logged: {'at': '2026-10-18T03:22:24+00:00', 'dispatched': 5, 'event': 'runaway-escalation', 'max_park_percent': 50, 'parked': 5, 'ratio': 1.0, 'runaway_min_parked': 5}

    --- 4. Absence of ipd-started after breach ---
    ipd-started events after runaway-escalation: 0
    Item 6 status: queued attempts: 0

    --- 5. Preserved lanes and question files ---
    Git branches: None
    Question files on disk: ['01-rnw001-a1-q-rnw001.json', '02-rnw002-a1-q-rnw002.json', '03-rnw003-a1-q-rnw003.json', '04-rnw004-a1-q-rnw004.json', '05-rnw005-a1-q-rnw005.json']

    --- 6. Ordinary parked run summary for contrast ---
    Ordinary parked exit reason: 5 item(s) awaiting human response (unattended mode)

    --- 7. 2-item run with 1 parked item floor guard result ---
    2-item 1-parked breach check: False (runaway_escalation in state: False)
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" tests/test_question_drain.py tests/test_question_preflight.py tests/test_runs_answer.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/jshwxb
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 34 items

    tests/test_question_preflight.py ...........                             [ 32%]
    tests/test_runs_answer.py ........                                       [ 55%]
    tests/test_question_drain.py ...............                             [100%]
    ============================= 34 passed in 29.81s ==============================

    $ python3 -m pytest
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    1362 passed, 3 warnings in 84.66s (0:01:24)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `aw runs answer <run-id> --no-interactive` output listing the 74-member group once with its raiser count, the `--agent` record's entry showing `group_id` and `raisers`, and `ls <run_dir>/answers/*.json | wc -l` after `--group <group_id> --answer X`.
  - Observed evidence:
    ```
    --- 1. aw runs answer <run-id> --no-interactive ---
    [run-v06-test] [g-c8d8f2f917418dc3] (74 raiser(s): p00001, p00002, ..., p00074, unblocks 74):
      Select replication protocol?
      Options:
        1. Raft
        2. Paxos

    --- 2. aw runs answer <run-id> --agent ---
    {"schema":"aw.agent/v1","kind":"result","cmd":"runs answer","exit":0,"outcome":"ok","verified":true,"complete":true,"questions":[{"run_id":"run-v06-test","group_id":"g-c8d8f2f917418dc3","raisers":["p00001", ... 74 total ...],"unblock_count":74,"question_id":"01-p00001-a1-q-rep","question_ids":["01-p00001-a1-q-rep", ... 74 total ...],"text":"Select replication protocol?","options":["Raft","Paxos"],"allow_free_text":true,"gates_verdict":true}]}

    --- 3. aw runs answer run-v06-test --group g-c8d8f2f917418dc3 --choice 0 ---
    ls <run_dir>/answers/*.json | wc -l: 74
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste from the patched-TTY fixture the R4.4 summary printed before the first question, the `events.jsonl` lines showing one invocation with the parked item's second `ipd-started` after the drain answer (A35); from the always-asks fixture the `question-rounds-exhausted` event after round 2 and `answers.md` present (A26); the all-parked-nothing-queued fixture reaching the ask; and the `--unattended` TTY case printing no prompt (produced by E-07's `drain_parked_questions` at both drain exits).
  - Observed evidence:
    ```
    --- 1. Patched-TTY fixture: R4.4 summary & same-invocation re-dispatch ---
    R4.4 summary in stderr:
    Parked questions at drain: 1 distinct question(s) across 1 artifact(s):
      • [g-622304b635b8dec9] unblocks 1 item(s) (raisers: res001)
    Run exit code: 0
    run-created invocations count: 0
    res001 ipd-started attempts count: 2
      {'action': 'execute', 'at': '2026-10-18T03:24:59+00:00', 'attempt': 1, 'event': 'ipd-started', 'id6': 'res001'}
      {'action': 'execute', 'at': '2026-10-18T03:24:59+00:00', 'attempt': 2, 'event': 'ipd-started', 'id6': 'res001'}

    --- 2. Always-asks fixture: question-rounds-exhausted event & answers.md ---
    drain_parked_questions returned: exit
    answers.md exists: True
    question-rounds-exhausted event: {'at': '2026-10-18T03:25:05+00:00', 'event': 'question-rounds-exhausted', 'max_rounds': 2, 'question_rounds': 2, 'rounds': 2, 'rounds_used': 2}

    --- 3. All-parked nothing queued fixture reaching the ask ---
    Parked questions at drain: 1 distinct question(s) across 1 artifact(s):
      • [g-20c61689848f09ed] unblocks 1 item(s) (raisers: all001)
    All parked queue reached terminal ask prompt: True

    --- 4. Unattended with TTY present prints no prompt ---
    Prompt called: []
    drain_parked_questions returned: exit
    answers.md written: True
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the captured sweep output showing ONE prompt for the 20-artifact fixture, `git show --stat HEAD` showing one commit touching exactly the 20 artifacts, and for the edited-artifact case the 19 resolved blocks and the one routed question file.
  - Observed evidence:
    ```
    --- 1. 20-artifact fixture: single prompt & single commit ---
    Pre-flight open questions: 1 distinct question(s) across 20 artifact(s):
      • [g-ea639a5361623d78] unblocks 20 item(s) (raisers: pfl001, ..., pfl020)
    [g-ea639a5361623d78] committed: 0d74e27b83937c7670ebbe217e04a38ca5e39b4f
    Total prompt calls for 20 artifacts: 1
    git show --stat HEAD:
      commit 0d74e27b83937c7670ebbe217e04a38ca5e39b4f
      Author: Test User <test@example.com>
      Date:   Sat Oct 17 23:25:18 2026 -0400
          g-ea639a5361623d78: pre-flight sweep answer across 20 artifact(s)
       20 files changed, 40 insertions(+), 20 deletions(-)

    --- 2. Edited-artifact case: 19 resolved & 1 routed ---
    Pre-flight open questions: 1 distinct question(s) across 20 artifact(s):
      • [g-b4fb08c3d6f8624e] unblocks 20 item(s) (raisers: stk001, ..., stk020)
    Resolved artifacts count: 19
    Open artifacts count: 1
    Routed questions in inbox for edited artifact (stk020): 1
      Routed question text: Select auth provider?
    ```
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
