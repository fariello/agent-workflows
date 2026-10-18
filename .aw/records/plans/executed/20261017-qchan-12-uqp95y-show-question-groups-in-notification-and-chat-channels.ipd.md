# IPD: Show question groups in notification and chat channels

- Date: 2026-10-17
- Kind: child
- Concern: In large queues where multiple sibling artifacts ask the same question (such as 74 artifacts sharing a fingerprint), Order 08 (`jshwxb`) groups open questions by fingerprint via `question_inbox.group_open_questions` and provides group-level answering via `question_inbox.write_group_answer` and `aw runs answer --group`. However, notification channels (Order 09 `txl556`) and chat channels were deferred (backlog `4brk8a`). Currently, `notify.core.dispatch_checkpoint` reads ungrouped open questions with `question_inbox.read_open_questions`, and `notify.core.build_batch` creates notifications per individual question. In terse mode, channels report total questions without group awareness; in full mode, channels output redundant question blocks per artifact prompting individual question answers (`aw runs answer <run_id> <qid>`) instead of group answers (`aw runs answer <run_id> --group <group_id>`); and inbound event routing (`notify.core.apply_inbound`) resolves only individual question routes.
- Scope: IN: extending `OutboundQuestion` and `OutboundBatch` in `agent_workflows/notify/core.py` with question group metadata (`group_id`, member question IDs, raiser artifact id6s, unblock count, total member count); updating `build_batch` to accept `question_inbox.QuestionGroup` objects and render one entry per deduplicated group with the group answer command (`aw runs answer <run_id> --group <group_id>`); updating `dispatch_checkpoint` to consume `question_inbox.group_open_questions(run_dir, state)`, track every member question in `notify/sent.jsonl`, and send ONE acknowledgement per answered group instead of one per member; updating `agent_workflows/notify/registry.py` and `apply_inbound` in `notify/core.py` to register and route inbound group events to `question_inbox.write_group_answer`; updating `agent_workflows/notify/webhook.py` to add the group fields to the `aw.notify/v1` JSON; updating `TelegramChannel.send` in `agent_workflows/notify/telegram.py` so full mode sends one message per group and registers its routes with the `group_id` (without this no channel ever creates a group route, so inbound group routing would be unreachable); a CHANGELOG line and the terse/full-mode description in `docs/notifications.md` (written by `mrlblc`, hence the dependency); and behavioral tests in `tests/test_notify_groups.py`. OUT: implementing `group_open_questions` or `write_group_answer` (owned by `jshwxb`, executed); the Telegram receiver, poller, verification and offset handling (owned by `qrup8m`, executed; only `TelegramChannel.send`'s full-mode loop and its route registration change here); `aw notify` CLI commands and the creation of `docs/notifications.md` (owned by `mrlblc`).
- Scope-Paths: agent_workflows/notify/core.py, agent_workflows/notify/registry.py, agent_workflows/notify/webhook.py, agent_workflows/notify/telegram.py, tests/test_notify_groups.py, CHANGELOG.md, docs/notifications.md
- Item-Dependencies: executed:jshwxb, executed:txl556, executed:qrup8m, executed:mrlblc
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- From-Backlog: 4brk8a
- Set: qchan
- Order: 12
- Highest E allocated: 08
- Author: antigravity
- Id: uqp95y

## Workflow history
- 2026-10-18 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5.5-1m-us variant=high profile=opus): aw oc run self-finalize: uqp95y verified (set qchan, attempt 1).
- 2026-10-18 approved (aw set): status set to approved
- 2026-10-18 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010

- 2026-10-18 to-review (antigravity): authored review-ready from backlog 4brk8a.
- 2026-10-18 draft (antigravity): created.

## Goal

Surface deduplicated question groups in the outbound notification channels (full mode and the `aw.notify/v1` JSON; terse text stays exactly as spec `6kwd2e` R10.4 mandates) and route inbound channel answers through `question_inbox.write_group_answer`, so an off-machine operator sees one entry per distinct question and one answer resolves every parked artifact that raised it (spec `6kwd2e` R4.2, A9, extended to channels).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Outbound Batch and Checkpoint Dispatch

- [x] E-01 Extend the dataclasses and `build_batch` in `agent_workflows/notify/core.py`. `OutboundQuestion` gains optional `group_id: str | None = None`, `member_qids: list[str]` (default empty), `raisers: list[str]` (default empty) and `unblock_count: int = 0`; `OutboundBatch` gains `question_count: int | None = None` (the total number of open member questions, R10.4's N; `None` means `len(questions)`, so existing callers are unchanged). `build_batch` additionally accepts `question_inbox.QuestionGroup` objects in `questions` (detected with `isinstance`): each group becomes ONE `OutboundQuestion` whose `question_id` is the group's first member qid (the REPRESENTATIVE, `QuestionGroup.oq_id`), whose `answer_command` is `aw runs answer <run_id> --group <group_id>`, and whose group fields are filled from the group; `question_count` is the sum of member counts. Plain dict and `OutboundQuestion` inputs keep today's per-question rendering and `aw runs answer <run_id> <qid>` command byte-for-byte (D-5). Input order is preserved as given (`group_open_questions` already sorts per R4.3/R4.3a; `build_batch` MUST NOT re-sort). TERSE text is unchanged: exactly `run <run_id>: N question(s) waiting; answer with aw runs answer <run_id>` with N = `question_count` and no group wording (D-2). FULL text: the same first line, then per entry a block with `Question: <group_id>` (or the qid for an ungrouped entry), `Asked by <k> artifact(s): <id6>, ...` listing at most 10 raiser id6s followed by `and <m> more` when there are more, `Unblocks: <unblock_count>`, the sanitized text, the sanitized numbered options, and the answer command. Every text and option still passes `sanitize_outbound`, and the whole message is truncated after sanitizing (R10.3).
  - Depends on: none
  - Expected outcome: given ONE `QuestionGroup` of 74 members built by `question_inbox.group_questions` from 74 question records sharing text and options, terse mode yields exactly `run <run_id>: 74 questions waiting; answer with aw runs answer <run_id>` and no question text; full mode contains the question text exactly once, `Asked by 74 artifact(s):` with 10 id6s and `and 64 more`, and `aw runs answer <run_id> --group <group_id>`; the existing `OutboundQuestion` input still renders `aw runs answer <run_id> <qid>`.
  - Execution state: performed

- [x] E-02 Update `dispatch_checkpoint` in `agent_workflows/notify/core.py` to build its outbound set from `question_inbox.group_open_questions(run_dir, state)` (the same grouping `aw runs answer --group` uses in `run_cli`, so the group id a notification prints is one the CLI resolves). Any question in `question_inbox.read_open_questions(run_dir)` that no group covers (possible when `group_open_questions` narrows to the current park's `question_ids` while a non-parked item still holds an open question) is appended as an ungrouped dict entry with today's per-question rendering, so no question that is notified today stops being notified (D-4). A group is NEW for a channel when any member qid lacks a `(channel, question_id)` row in `notify/sent.jsonl`; all new groups and new ungrouped questions for a channel go into ONE batch per channel per checkpoint (R10.7, once per park batch), and a new group is rendered with ALL its current members. On a successful (or uncertain) send, append one `sent.jsonl` row per member qid carrying `group_id` (absent for an ungrouped entry), so the existing `(channel, question_id)` dedup still prevents re-notification. The `notify-sent` event's `count` stays the number of member questions sent.
  - Depends on: E-01
  - Expected outcome: three parked items each with one question of identical text produce, at the first checkpoint, exactly one `send` per channel whose batch has one entry, `question_count` 3 and the `--group` command; `sent.jsonl` holds three rows with the same `group_id`; a second checkpoint with nothing new sends nothing; a fourth item parking the same question at a later checkpoint triggers one new batch whose group lists four raisers.
  - Execution state: performed

- [x] E-06 Collapse acknowledgements per group in `dispatch_checkpoint`'s acknowledgement pass (`agent_workflows/notify/core.py`). Today it sends one "answered via" message per `(channel, question_id)`, which for a 74-member group answered once is 74 chat messages. Group the consumed (and, separately, the stale) member qids of this checkpoint by the `group_id` recorded in `sent.jsonl`; send ONE acknowledgement per `(channel, group_id)` whose batch carries a single `OutboundQuestion(question_id=<representative qid>, text="")` and the message `run <run_id> (<representative qid>): answered via <channel>` followed by ` (applied to <k> questions)` when k > 1 (stale: `answer not applied: the plan changed; ask again`), keeping the prefix that `TelegramChannel.send` already recognizes as an acknowledgement and the qid it uses to find the original message. On success append an `ack` row for EVERY member qid acknowledged, so none is acknowledged twice. Ungrouped qids keep today's per-question acknowledgement.
  - Depends on: E-02
  - Expected outcome: after `write_group_answer` answers a three-member group and `answer-consumed` events are present for all three, one checkpoint sends exactly one acknowledgement batch per channel naming the representative qid and `applied to 3 questions`, writes three `ack` rows, and the next checkpoint sends nothing.
  - Execution state: performed

### Task group 2: Inbound Routing and Channel Serialization

- [x] E-03 Route inbound group answers. In `agent_workflows/notify/registry.py`, `register` gains keyword-only `group_id: str | None = None` and `member_qids: list[str] | None = None`, stored in the route only when given (existing routes and callers unchanged; `question_id` stays the representative qid, so `registry.expire` and `TelegramChannel._lookup_registered_message_id` keep working). In `apply_inbound` (`agent_workflows/notify/core.py`), when the matched route carries `group_id`: load state with `runner_shared.load_state(run_dir)` when `run_dir / "state.json"` exists (else `None`, the same rule `run_cli` uses), recompute `question_inbox.group_open_questions(run_dir, state)`, and select the CURRENT group that contains the route's representative `question_id`, NOT the group whose id equals the stored `group_id`: collision-split ids (`g-<fp>-<n>`) are renumbered when another same-fingerprint question parks (measured at review: `g-deadbeefdeadbeef-1` named "Use B?" before a third variant parked and "Use A?" after), so a stored id can name a different question and would apply the human's answer to a decision they never saw (R4.1b) (D-1). If such a group exists, call `question_inbox.write_group_answer(run_dir, state, <that group's current id>, answer=..., choice=..., channel=..., sender=..., actor="human")` and use its `status` (`recorded`/`already`/`rejected`) as the outcome; if no open group contains the representative qid, fall back to today's `write_answer` on that qid, which reports `already` or `rejected` truthfully. Routes without `group_id` take today's path unchanged. `write_group_answer` is not atomic across members (each member is first-answer-wins under its own lock); describe it that way in the docstring.
  - Depends on: E-02
  - Expected outcome: a route registered for a three-member group records three answers each with `applied_to` naming all three members, and acks `recorded`; after a third collision variant renumbers the split ids, a route registered for the "Use B?" group still answers only the "Use B?" members; a route without `group_id` behaves as before.
  - Execution state: performed

- [x] E-04 Update `agent_workflows/notify/webhook.py` (`WebhookChannel.send` `aw` format and `CommandChannel.send`) so the `aw.notify/v1` payload's `count` is `batch.question_count` when set (else `len(batch.questions)`), keeping its meaning as the number of open questions; add a top-level `distinct_count` (the number of entries); and, in full mode only, add `group_id`, `member_qids`, `raisers` and `unblock_count` to each `questions[]` entry (additive keys; an ungrouped entry carries `group_id: null` and empty lists). Terse payloads still carry no question content (R10.4). `text` and `ntfy` formats need no code change: they carry `batch.message`, which E-01 already formats.
  - Depends on: E-01
  - Expected outcome: a loopback HTTP server receiving a full-mode `aw` POST for one three-member group sees `count` 3, `distinct_count` 1, and one `questions[]` entry with `group_id` and three `member_qids`; a terse POST has `count` 3 and an empty `questions` list; the command hook receives the same JSON on stdin; `text` and `ntfy` bodies contain the `--group` command in full mode.
  - Execution state: performed

- [x] E-07 Make Telegram full mode group-aware in `TelegramChannel.send` (`agent_workflows/notify/telegram.py`), the only channel that registers inbound routes: for an entry with `group_id`, the message header reads `run <run_id> (<group_id>, <k> artifacts):` instead of the single qid, and the message-id route and every option-token route are registered with `question_id=<representative qid>`, `group_id` and `member_qids`. Entries without `group_id` are sent and registered exactly as today. No change to the receiver, verification, offsets or acknowledgement handling. Without this item no group route is ever created and E-03's inbound path is unreachable from a real channel.
  - Depends on: E-01, E-03
  - Expected outcome: against `tests/fake_telegram.py`, a full-mode batch with one three-member group produces ONE `sendMessage`, and the registry holds a message route and one token route per option, each with the `group_id` and three `member_qids`; pressing a button through `apply_inbound` records three answers.
  - Execution state: performed

### Task group 3: Behavioral Test Coverage and Documentation

- [x] E-05 Add `tests/test_notify_groups.py` (module-level `pytestmark = pytest.mark.core`) driving the real functions against `tmp_path` run directories populated with `question_inbox.write_question`, under the conftest `AW_HOME` sandbox, with no network beyond loopback: (1) `build_batch` terse and full rendering of a group, the raiser cap, and the unchanged per-question rendering; (2) `dispatch_checkpoint` grouping, one batch per channel, `sent.jsonl` member rows, no re-notify, re-notify on a new member, and an uncovered open question still notified; (3) one acknowledgement per answered group; (4) `apply_inbound` group routing including the renumbered-split case and the fallback; (5) the `aw` webhook payload against a loopback `http.server` and the command hook on stdin; (6) Telegram full mode against `tests/fake_telegram.py`. Tests assert outputs, files written and HTTP bodies received, never source text.
  - Depends on: E-03, E-04, E-06, E-07
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_notify_groups.py tests/test_notify_core.py tests/test_notify_telegram.py` passes, so the new behavior is covered and the existing notify tests still pass unchanged.
  - Execution state: performed

- [x] E-08 Document the change for users. Add one `CHANGELOG.md` line under the pending 2.0.0 entry (for example: notification channels now show one entry per distinct question in full mode, with the group answer command, and one Telegram reply or button answers every parked plan that asked it). In `docs/notifications.md` (created by `mrlblc`), update the terse versus full description to say full mode lists each distinct question once with how many plans asked it, and that terse text is unchanged. User-facing prose: no em or en dashes.
  - Depends on: E-01
  - Expected outcome: `git diff` shows the CHANGELOG line and the `docs/notifications.md` paragraph, and neither contains an em or en dash.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Notification and chat channels are governed by spec `6kwd2e` R10; deduplication and ordering by R4.
- Outbound text must pass `notify.core.sanitize_outbound` (spec `6kwd2e` R10.3) before leaving the machine.
- All answer writing must go through the shared answer writer (`question_inbox.write_answer`, which `question_inbox.write_group_answer` calls per member); channels never write to `answers/` directly (spec `6kwd2e` R9.2, R10.1).
- Route resolution is managed via the user-level registry in `agent_workflows/notify/registry.py` under `<AW_HOME>/notify/registry.json`; only `TelegramChannel.send` registers routes today.
- `aw runs answer --group` (`run_cli`) recomputes groups with `question_inbox.group_open_questions(run_dir, runner_shared.load_state(run_dir))`, so a group id shown to a human is only meaningful if computed the same way.
- User-facing prose (CHANGELOG, docs) carries no em or en dashes (AGENTS.md execution contract).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Backlog item `4brk8a` was filed when Order 08 (`jshwxb`) implemented `group_open_questions` and `write_group_answer` but deferred channel consumption.
- `notify.core.dispatch_checkpoint(run_dir, state, repo=None)` receives `state`, which is exactly what `question_inbox.group_open_questions(run_dir, state)` needs; it currently calls `question_inbox.read_open_questions(run_dir)` and sends one entry per question.
- `build_batch` is the single serialization point for `batch.message` across all channels, but not for structure: `WebhookChannel.send`/`CommandChannel.send` serialize `batch.questions` and compute `"count": len(batch.questions)`, and `TelegramChannel.send` iterates `batch.questions` and registers routes per entry. So grouping entries changes the meaning of `count` unless `OutboundBatch` carries the total (E-01 `question_count`, E-04).
- `question_inbox.group_questions` assigns `g-<fp>` to a fingerprint with one collision key and `g-<fp>-<n>` (sorted by normalized text, options, free-text flag) when a fingerprint splits. MEASURED at review: with records "Use C?"/"Use B?" sharing a fingerprint, `g-deadbeefdeadbeef-1` is "Use B?"; adding "Use A?" makes `-1` "Use A?". Also measured: options `["pg","mysql"]` vs `["mysql","pg"]` share the driver fingerprint but split, so splits arise from ordinary input. A stored group id is therefore not a stable route key; the representative member qid is (E-03, D-1).
- `question_inbox.group_open_questions` reads only the `question_ids` of `awaiting-human` items when any exist, and falls back to all open questions otherwise; `runner_shared` writes non-blocking pre-flight questions for items that stay queued, so the two sets can differ (E-02, D-4).
- `notify.core.dispatch_checkpoint`'s acknowledgement pass sends one message per `(channel, question_id)` with an `answer-consumed` event; `runner_shared.consume_answers` emits one such event per member, so a group answer would produce one chat acknowledgement per member (E-06).
- `TelegramChannel.send` treats a batch with one empty-text question, or a message matching `^run \S+ \((\S+)\): (?:answered via|answer not applied)`, as an acknowledgement and replies to the message registered for that qid; the group acknowledgement keeps both shapes.

## Proposed changes (ordered, validatable)

1. E-01: Group fields and `question_count` on the dataclasses; group rendering in `build_batch`.
2. E-02: Group consumption, uncovered-question fallback, and member tracking in `dispatch_checkpoint`.
3. E-06: One acknowledgement per answered group.
4. E-03: Group routes in `registry.register` and representative-member resolution in `apply_inbound`.
5. E-04: Additive group fields and a truthful `count` in the `aw.notify/v1` payload.
6. E-07: One Telegram message per group and group-tagged route registration.
7. E-05: Behavioral test suite in `tests/test_notify_groups.py`.
8. E-08: CHANGELOG line and `docs/notifications.md` paragraph.

## Deferred / out of scope (with reason)

- Implementing `group_open_questions` and `write_group_answer`: owned by prerequisite `jshwxb`.
  - Carrier: jshwxb
  - Carrier-Evidence: .aw/records/plans/executed/20261017-qchan-08-jshwxb-deduplicate-and-order-questions-ask-at-the-drain-bound-round.ipd.md
- Telegram receiver, poller, sender verification and offset handling: owned by `qrup8m`; this plan changes only `TelegramChannel.send`'s full-mode loop and route registration.
  - Carrier: qrup8m
  - Carrier-Evidence: .aw/records/plans/executed/20261017-qchan-10-qrup8m-add-a-standard-library-two-way-telegram-channel.ipd.md
- Setup CLI commands (`aw notify setup`) and creating `docs/notifications.md`: owned by `mrlblc`.
  - Carrier: mrlblc
  - Carrier-Evidence: .aw/records/plans/executed/20261017-qchan-11-mrlblc-add-aw-notify-setup-test-status-and-listen.ipd.md

## Scope check

- Over-scope: none. Changes are confined to consuming question groups in the notification and chat channel machinery.
- Under-scope: none after review. Telegram route registration (the only producer of inbound routes), group acknowledgements, the uncovered-question fallback, and user documentation were added at review.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_notify_groups.py tests/test_notify_core.py tests/test_notify_telegram.py`
- Routine test gate: `python3 -m pytest` (paste the `N passed` summary line).

## Spec / documentation sync

- Implements spec `6kwd2e` R4.1-R4.3a and A9 in the channels, within R10.1 (core owns routing), R10.3 (sanitize then truncate), R10.4 (terse text unchanged), and R10.7 (once per park batch; one acknowledgement per answered group satisfies "MUST send a short answered via acknowledgement").
- No spec modification required: the terse text is unchanged and every other change is within R10's existing wording.
- User documentation: `CHANGELOG.md` and `docs/notifications.md` (E-08).

## Open questions

### OQ-01: How should terse mode report when multiple groups exist?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode)
- Resolution or deferral rationale: RESOLVED at review (D-2), replacing the author's resolution. Terse text stays exactly `run <run_id>: N question(s) waiting; answer with aw runs answer <run_id>` with N the number of open member questions, because spec `6kwd2e` R10.4 says terse mode sends "only" that sentence; the author's `(G group(s))` insertion contradicted that while claiming conformance. Group density reaches terse consumers only as the numeric `distinct_count` field of the `aw.notify/v1` JSON envelope (E-04), which carries no question content, the same way `count` and `run_id` already do.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted pytest output for the test(s) that call `notify.core.build_batch` with a 74-member `QuestionGroup` built by `question_inbox.group_questions`, plus the asserted terse string (exactly `run <run_id>: 74 questions waiting; answer with aw runs answer <run_id>`, no question text) and the asserted full-mode facts (text once, `Asked by 74 artifact(s):`, `and 64 more`, `--group <group_id>`), and the passing assertion that an `OutboundQuestion` input still renders `aw runs answer <run_id> <qid>`. Re-derive at execution; a test name is only a pointer.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -p no:cacheprovider -p no:randomly -v tests/test_notify_groups.py
    tests/test_notify_groups.py::test_build_batch_group_terse_full_and_raiser_cap PASSED [ 10%]
    tests/test_notify_groups.py::test_build_batch_ungrouped_rendering_unchanged PASSED [ 20%]
    ```
    Asserted terse string (74-member group from `question_inbox.group_questions`): `run run-g74: 74 questions waiting; answer with aw runs answer run-g74`, and "Which database?" not in it. Full-mode message printed by the test (-s):
    ```
    run run-g74: 74 questions waiting; answer with aw runs answer run-g74

    Question: g-16c202344a04d130
    Asked by 74 artifact(s): g00000, g00001, g00002, g00003, g00004, g00005, g00006, g00007, g00008, g00009 and 64 more
    Unblocks: 74
    Which database?
    Options:
      1) pg
      2) mysql
    aw runs answer run-g74 --group g-16c202344a04d130
    ```
    Test asserts text appears once. Ungrouped `OutboundQuestion` asserts exact message ending `aw runs answer run-u 01-abc123-a1-q1` and `answer_command == "aw runs answer run-u 01-abc123-a1-q1"` (PASSED).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted pytest output for tests driving `notify.core.dispatch_checkpoint` (code path: `dispatch_checkpoint` -> `question_inbox.group_open_questions` -> `build_batch` -> channel `send`) with a recording channel, showing: one send per channel with one entry and `question_count` 3; three `sent.jsonl` rows sharing a `group_id` (paste the rows); a second checkpoint sending nothing; a new member re-notifying with four raisers; and an open question outside every group still sent with its per-question command.
  - Observed evidence:
    ```
    tests/test_notify_groups.py::test_dispatch_checkpoint_groups_and_tracks_members PASSED [ 30%]
    tests/test_notify_groups.py::test_dispatch_checkpoint_notifies_question_outside_every_group PASSED [ 40%]
    ```
    Asserted: one batch, one entry, `question_count == 3`, `--group <gid>` in message; notify-sent count `[3]`; second checkpoint sends nothing; a fourth park re-notifies with raisers `["aaa001","aaa002","aaa003","aaa004"]` and "Asked by 4 artifact(s)"; an uncovered open question (non-parked item) is sent with `aw runs answer run-unc <qid>` and its sent row carries no `group_id`. sent.jsonl rows printed by the test:
    ```
    {"channel": "webhook", "question_id": "01-aaa001-a1-q1", "type": "question", "group_id": "g-820befb4ad0c0e88", "representative_qid": "01-aaa001-a1-q1", "message_id": "m1", ...}
    {"channel": "webhook", "question_id": "02-aaa002-a1-q1", "type": "question", "group_id": "g-820befb4ad0c0e88", "representative_qid": "01-aaa001-a1-q1", "message_id": "m1", ...}
    {"channel": "webhook", "question_id": "03-aaa003-a1-q1", "type": "question", "group_id": "g-820befb4ad0c0e88", "representative_qid": "01-aaa001-a1-q1", "message_id": "m1", ...}
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted pytest output for tests driving `notify.core.apply_inbound` with a group route (code path: `apply_inbound` -> `registry.lookup` -> `group_open_questions` -> `write_group_answer`), showing the three answer files with `applied_to` naming all three members (paste one answer file), the renumbered-split case answering only the originally shown question's members, the fallback to `write_answer` when the group is gone, and an unchanged result for a route without `group_id`.
  - Observed evidence:
    ```
    tests/test_notify_groups.py::test_apply_inbound_group_route_answers_all_members PASSED [ 60%]
    tests/test_notify_groups.py::test_apply_inbound_renumbered_split_answers_only_shown_question PASSED [ 70%]
    tests/test_notify_groups.py::test_apply_inbound_route_without_group_unchanged PASSED [ 80%]
    ```
    One answer file (all three exist with choice 1):
    ```
    {"schema": "aw.answer/v1", "question_id": "01-ddd001-a1-q1", "answer": "no", "choice": 1, "actor": "human", "channel": "telegram", "sender": "tg-user-1",
     "applied_to": [{"question_id": "01-ddd001-a1-q1", "artifact_id6": "ddd001"}, {"question_id": "02-ddd002-a1-q1", "artifact_id6": "ddd002"}, {"question_id": "03-ddd003-a1-q1", "artifact_id6": "ddd003"}], ...}
    ```
    Renumbered split: route registered for `g-deadbeefdeadbeef-1` ("Use B?"); after "Use A?" parks, `-1` is "Use A?" (asserted) and the inbound answer writes only the two "Use B?" answer files (asserted). Fallback: a second press after the group is fully answered returns `already` via `write_answer`. A route without `group_id` answers only its own qid.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted pytest output plus the JSON body received by a loopback `http.server` for a full-mode `aw` POST (`count` 3, `distinct_count` 1, one entry with `group_id` and three `member_qids`) and for a terse POST (`count` 3, empty `questions`), and the stdin JSON received by the command hook (code path: `WebhookChannel.send` / `CommandChannel.send`).
  - Observed evidence:
    ```
    tests/test_notify_groups.py::test_aw_webhook_and_command_payloads_carry_groups PASSED [ 90%]
    ```
    Body received by the loopback `http.server` (full `aw` POST):
    ```
    {"schema": "aw.notify/v1", "run_id": "run-wh", "mode": "full", "count": 3, "distinct_count": 1, "message": "...aw runs answer run-wh --group g-16c202344a04d130",
     "questions": [{"question_id": "01-g00000-a1-q1", "text": "Which database?", "options": ["pg","mysql"], "allow_free_text": true, "answer_command": "aw runs answer run-wh --group g-16c202344a04d130",
       "group_id": "g-16c202344a04d130", "member_qids": ["01-g00000-a1-q1","02-g00001-a1-q1","03-g00002-a1-q1"], "raisers": ["g00000","g00001","g00002"], "unblock_count": 3}]}
    ```
    Terse POST:
    ```
    {"schema": "aw.notify/v1", "run_id": "run-wh", "mode": "terse", "count": 3, "distinct_count": 1, "message": "run run-wh: 3 questions waiting; answer with aw runs answer run-wh", "questions": []}
    ```
    Command hook stdin JSON printed by the test is identical to the full body above (`count` 3, `distinct_count` 1, `group_id` set). `text` and `ntfy` bodies asserted to contain `--group g-16c202344a04d130`; an ungrouped entry carries `group_id: null`, `member_qids: []`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted runner output of `python3 -m pytest -o addopts="" tests/test_notify_groups.py tests/test_notify_core.py tests/test_notify_telegram.py` showing every test passing and zero failures, and the pasted `N passed` summary line of the routine gate `python3 -m pytest`.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -p no:cacheprovider -p no:randomly tests/test_notify_groups.py tests/test_notify_core.py tests/test_notify_telegram.py
    ======================= 48 passed, 6 warnings in 14.93s ========================
    ```
    Routine gate:
    ```
    $ aw suite
    1675 passed, 11 warnings in 77.21s (0:01:17)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted pytest output for a test that answers a three-member group with `write_group_answer`, appends the three `answer-consumed` events, and drives `notify.core.dispatch_checkpoint` with a recording channel (code path: the acknowledgement pass of `dispatch_checkpoint`), showing exactly one acknowledgement batch per channel whose message names the representative qid and `applied to 3 questions`, three `ack` rows in `sent.jsonl` (paste them), and nothing sent at the next checkpoint.
  - Observed evidence:
    ```
    tests/test_notify_groups.py::test_one_acknowledgement_per_answered_group PASSED [ 50%]
    ```
    Ack message printed by the test: `run run-ack (01-ccc001-a1-q1): answered via terminal (applied to 3 questions)`; exactly one ack batch whose only question is the representative qid; next checkpoint sends nothing. ack rows:
    ```
    {"channel": "webhook", "question_id": "01-ccc001-a1-q1", "type": "ack", "status": "consumed", ...}
    {"channel": "webhook", "question_id": "02-ccc002-a1-q1", "type": "ack", "status": "consumed", ...}
    {"channel": "webhook", "question_id": "03-ccc003-a1-q1", "type": "ack", "status": "consumed", ...}
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: pasted pytest output for a test running `TelegramChannel.send` against `tests/fake_telegram.py` with a full-mode batch holding one three-member group (code path: `TelegramChannel.send` full-mode loop -> `registry.register`), showing the fake server recorded ONE `sendMessage`, the pasted registry routes carrying `group_id` and three `member_qids`, and a button event passed through `notify.core.apply_inbound` producing three answer files.
  - Observed evidence:
    ```
    tests/test_notify_groups.py::test_telegram_full_mode_sends_one_message_per_group PASSED [100%]
    ```
    Fake server recorded exactly one `sendMessage` (asserted), header `run run-tg (g-820befb4ad0c0e88, 3 artifacts):`. Registry routes (message route, then two option-token routes) printed by the test:
    ```
    {"question_id": "01-hhh001-a1-q1", "option": null, "group_id": "g-820befb4ad0c0e88", "member_qids": ["01-hhh001-a1-q1","02-hhh002-a1-q1","03-hhh003-a1-q1"], ...}
    {"question_id": "01-hhh001-a1-q1", "option": 0, "group_id": "g-820befb4ad0c0e88", "member_qids": [...same three...], ...}
    {"question_id": "01-hhh001-a1-q1", "option": 1, "group_id": "g-820befb4ad0c0e88", "member_qids": [...same three...], ...}
    ```
    A button update passed through `apply_inbound` returned `recorded` and produced answer files for all three qids (asserted).
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: pasted `git diff -- CHANGELOG.md docs/notifications.md` showing the new CHANGELOG line and the updated terse versus full paragraph, plus pasted output of a search of those added lines for U+2014 and U+2013 returning nothing.
  - Observed evidence:
    ```
    $ git diff -- CHANGELOG.md docs/notifications.md
    +- Added: Notification channels now show question groups. In full mode each distinct question appears once, with how many plans asked it and the group answer command, the `aw.notify/v1` JSON gains `distinct_count` and per-entry group fields, and one Telegram reply or button press answers every parked plan that asked the question. Terse text is unchanged.
    -- **Full Mode**: When opted into full mode (`--full`), notifications include sanitized question text and choices.
    +- **Full Mode**: When opted into full mode (`--full`), notifications include sanitized question text and choices. When several parked plans ask the same question, full mode lists that question once, says how many plans asked it, and shows the group answer command (`aw runs answer <run-id> --group <group-id>`). One answer, from the terminal or a Telegram reply or button, then answers every plan that asked it. Terse text is unchanged: it still reports the total number of open questions.
    $ git diff -- CHANGELOG.md docs/notifications.md | grep '^+' | grep -nP '[\x{2013}\x{2014}]'; echo "dash-search exit=$?"
    dash-search exit=1
    ```
    (grep exit 1: no U+2013/U+2014 in the added lines.)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `jshwxb`, `txl556`, `qrup8m` and `mrlblc` have reached `executed` (see `- Item-Dependencies:`).

Execution contract:
- All open questions are resolved (OQ-01, D-2).
- Scope fence: the paths in `- Scope-Paths:`. An out-of-scope edit is made and then justified at finalize (`--scope-reason`), not a reason to stop. Stop only if a prerequisite symbol this plan relies on (`question_inbox.group_open_questions`, `question_inbox.write_group_answer`, `QuestionGroup.oq_id`) is absent, and report it.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written, HTTP bodies), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
