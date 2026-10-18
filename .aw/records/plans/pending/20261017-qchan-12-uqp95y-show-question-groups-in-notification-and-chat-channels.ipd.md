# IPD: Show question groups in notification and chat channels

- Date: 2026-10-17
- Kind: child
- Concern: In large queues where multiple sibling artifacts ask the same question (such as 74 artifacts sharing a fingerprint), Order 08 (`jshwxb`) groups open questions by fingerprint via `question_inbox.group_open_questions` and provides group-level answering via `question_inbox.write_group_answer` and `aw runs answer --group`. However, notification channels (Order 09 `txl556`) and chat channels were deferred (backlog `4brk8a`). Currently, `notify.core.dispatch_checkpoint` reads ungrouped open questions with `question_inbox.read_open_questions`, and `notify.core.build_batch` creates notifications per individual question. In terse mode, channels report total questions without group awareness; in full mode, channels output redundant question blocks per artifact prompting individual question answers (`aw runs answer <run_id> <qid>`) instead of group answers (`aw runs answer <run_id> --group <group_id>`); and inbound event routing (`notify.core.apply_inbound`) resolves only individual question routes.
- Scope: IN: extending `OutboundQuestion` and `OutboundBatch` in `agent_workflows/notify/core.py` with question group metadata (`group_id`, member question IDs, raisers count/artifacts, unblock count); updating `build_batch` to format terse and full notifications by deduplicated question group with group answer commands (`aw runs answer <run_id> --group <group_id>`); updating `dispatch_checkpoint` to consume `group_open_questions(run_dir, state)` and track member questions in `notify/sent.jsonl`; updating `agent_workflows/notify/registry.py` and `apply_inbound` in `notify/core.py` to register and route inbound group events to `question_inbox.write_group_answer`; updating `agent_workflows/notify/webhook.py` to serialize structured `groups` in `aw.notify/v1` format JSON; and adding comprehensive tests in `tests/test_notify_groups.py`. OUT: implementing `group_open_questions` or `write_group_answer` (owned by `jshwxb`); transport adapters for Telegram (owned by `qrup8m`); interactive CLI commands (owned by `mrlblc`).
- Scope-Paths: agent_workflows/notify/core.py, agent_workflows/notify/registry.py, agent_workflows/notify/webhook.py, tests/test_notify_groups.py
- Item-Dependencies: executed:jshwxb, executed:txl556
- Status: to-review
- Work-Kind: feature
- Priority: low
- From-Backlog: 4brk8a
- Set: qchan
- Order: 12
- Highest E allocated: 05
- Author: antigravity
- Id: uqp95y

## Workflow history

- 2026-10-18 to-review (antigravity): authored review-ready from backlog 4brk8a.
- 2026-10-18 draft (antigravity): created.

## Goal

Surface deduplicated question groups in outbound notification channels (terse and full modes) and route inbound channel responses through `question_inbox.write_group_answer`, enabling off-machine operators to see and answer grouped questions across multiple parked artifacts in one action.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Outbound Batch and Checkpoint Dispatch

- [ ] E-01 Extend `OutboundQuestion` and `OutboundBatch` dataclasses in `agent_workflows/notify/core.py` to carry group metadata (`group_id`, `member_qids`, `raisers`, `unblock_count`), and update `build_batch` to format outbound messages by group: in terse mode, report distinct group counts alongside question counts when questions are grouped; in full mode, render each distinct question group once in deterministic order (unblock count descending, execute first), listing raiser counts, member artifact id6s, sanitized question text, sanitized options, and the group answer command `aw runs answer <run_id> --group <group_id>`.
  - Depends on: none
  - Expected outcome: for a fixture with 74 questions in one group, terse mode produces `run <run_id>: 74 questions (1 group) waiting; answer with aw runs answer <run_id>`, and full mode renders exactly one question section with raiser count 74, member artifact list, and `--group <group_id>` command.
  - Execution state: pending

- [ ] E-02 Update `dispatch_checkpoint` in `agent_workflows/notify/core.py` to consume `question_inbox.group_open_questions(run_dir, state)` when available. Map open groups into outbound batches, send to each effective channel once per group, and record each group member's `question_id` in `notify/sent.jsonl` with its associated `group_id` so subsequent checkpoints do not re-notify already-sent group members unless new questions park.
  - Depends on: E-01
  - Expected outcome: in a run with multiple parked artifacts sharing a question, `dispatch_checkpoint` dispatches a single outbound batch for the group; all member question IDs are recorded in `sent.jsonl`; a subsequent checkpoint with no new questions sends nothing.
  - Execution state: pending

### Task group 2: Inbound Routing and Webhook Serialization

- [ ] E-03 Update `agent_workflows/notify/registry.py` to record and look up an optional `group_id` field in route dictionaries. In `agent_workflows/notify/core.py`, update `apply_inbound` to detect when a matched route contains a `group_id`, and route the response to `question_inbox.write_group_answer(run_dir, state, group_id, ...)` instead of `write_answer`, atomically resolving all member questions and recording `applied_to` in each answer record.
  - Depends on: E-02
  - Expected outcome: an inbound event matching a registered group key invokes `write_group_answer`, resolving all member questions across all parked artifacts in that group in one operation.
  - Execution state: pending

- [ ] E-04 Update `agent_workflows/notify/webhook.py` (`WebhookChannel` and `CommandChannel`) to include structured `groups` dictionaries in the `aw` format JSON payload (`aw.notify/v1`), including `group_id`, `member_qids`, `raisers`, `unblock_count`, and `answer_command`, while preserving formatted group representation in `text` and `ntfy` payloads via `batch.message`.
  - Depends on: E-01
  - Expected outcome: webhooks configured with `format: aw` receive a payload containing the structured `groups` list with member metadata; `text` and `ntfy` channels receive messages containing the formatted group text and `--group` answer commands.
  - Execution state: pending

### Task group 3: Behavioral Test Coverage

- [ ] E-05 Add `tests/test_notify_groups.py` (marked `pytest.mark.core`) covering group-aware notifications: (1) `build_batch` terse and full rendering with question groups, (2) `dispatch_checkpoint` grouping and deduplication across parked artifacts, (3) `sent.jsonl` tracking of group members, (4) `apply_inbound` routing to `write_group_answer`, and (5) `WebhookChannel` and `CommandChannel` delivery of group payloads.
  - Depends on: E-03, E-04
  - Expected outcome: `tests/test_notify_groups.py` passes under `pytest` with all assertions passing on loopback without network access.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Notification and chat channels are governed by spec `6kwd2e` R10.
- Outbound text must pass `notify.core.sanitize_outbound` (spec `6kwd2e` R10.3) before leaving the machine.
- All answer writing must go through the shared answer writer (`question_inbox.write_answer` or `question_inbox.write_group_answer`); channels never write to `answers/` directly (spec `6kwd2e` R9.2).
- Route resolution is managed via user-level registry in `agent_workflows/notify/registry.py` under `<AW_HOME>/notify/registry.json`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Backlog item `4brk8a` was filed when Order 08 (`jshwxb`) implemented `group_open_questions` and `write_group_answer` but deferred channel consumption.
- `notify.core.dispatch_checkpoint` receives `state` as an argument (`dispatch_checkpoint(run_dir, state, repo=None)`), providing the exact state object needed by `question_inbox.group_open_questions(run_dir, state)`.
- `build_batch` is the single serialization point for message text across all channels (webhook, command, and telegram), so formatting groups in `build_batch` immediately benefits all channel types.

## Proposed changes (ordered, validatable)

1. E-01: Group support in `OutboundQuestion`, `OutboundBatch`, and `build_batch`.
2. E-02: Group consumption and tracking in `dispatch_checkpoint`.
3. E-03: Group routing in `registry.py` and `apply_inbound`.
4. E-04: Structured group serialization in `webhook.py`.
5. E-05: Behavioral test suite in `tests/test_notify_groups.py`.

## Deferred / out of scope (with reason)

- Implementing `group_open_questions` and `write_group_answer`: owned by prerequisite `jshwxb`.
  - Carrier: jshwxb
- Telegram adapter two-way poller implementation: owned by `qrup8m`.
  - Carrier: qrup8m
  - Carrier-Evidence: .aw/records/plans/executed/20261017-qchan-10-qrup8m-add-a-standard-library-two-way-telegram-channel.ipd.md
- Setup CLI commands (`aw notify setup`): owned by `mrlblc`.
  - Carrier: mrlblc

## Scope check

- Over-scope: none. Changes are focused strictly on consuming question groups within notification and chat channel machinery.
- Under-scope: none. Outbound formatting, checkpoint dispatch, inbound routing, webhook serialization, and tests are all covered.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_notify_groups.py tests/test_notify_core.py`
- Routine test gate: `python3 -m pytest`

## Spec / documentation sync

- Aligns with spec `6kwd2e` R4 (deduplication across queue) and R10 (notification channels).
- No spec modification required.

## Open questions

### OQ-01: How should terse mode report when multiple groups exist?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: When questions fall into groups, terse mode states `run <run_id>: N question(s) (G group(s)) waiting; answer with aw runs answer <run_id>`. When all questions are distinct (each in its own group of 1), it states `run <run_id>: N question(s) waiting; answer with aw runs answer <run_id>`. This maintains strict conformance with R10.4 while providing group density context.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted test output showing `build_batch` output for a 74-member question group, verifying the terse summary string and the full message string containing raiser counts and `aw runs answer <run_id> --group <group_id>`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted test output showing `dispatch_checkpoint` dispatching a single outbound batch for a group of multiple parked questions and recording each question id in `sent.jsonl`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted test output showing an inbound event matching a group route invoking `write_group_answer` and resulting in answer files for all member questions with `applied_to` populated.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted test output showing a local HTTP test server receiving an `aw` format JSON POST request containing the `groups` list with `group_id` and member question IDs.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted pytest runner output from `python3 -m pytest -o addopts="" tests/test_notify_groups.py` showing all tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after prerequisite children `jshwxb` and `txl556` have reached `executed`. EXECUTION CONTRACT: all open questions are resolved. This plan performs scoped modifications to notification channel abstractions and adds dedicated behavioral tests. All changes commit via `aw commit <plan> -- <paths>`. Never push.
