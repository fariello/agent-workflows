# IPD: Add a standard-library two-way Telegram channel

- Date: 2026-10-17
- Kind: child
- Concern: Notify-only channels (Order 09) tell the human a question is waiting but cannot carry the answer back. Spec `6kwd2e` R10.5, R10.6 and R10.8a (amended 2026-10-17) require a two-way Telegram channel on the standard library only: long polling with no webhook, inline buttons carrying random tokens, free text accepted only as a reply to a known question message, verified sender (numeric user id AND private chat id), one poller per bot identity per machine attached to a live runner, offset persisted only after the event is handled, and every callback acknowledged. Four independent research reports (`kdg4uz`, `cpcn9k`, `49sv63`, `js5p5k`) agree; `kdg4uz`'s reference code is the base, `cpcn9k`'s is not used.
- Scope: IN: `agent_workflows/notify/telegram.py` implementing the Order 09 `Channel` protocol over `urllib.request` (`getMe`, `getWebhookInfo`, `sendMessage`, `getUpdates`, `answerCallbackQuery`, optional `editMessageReplyMarkup` to clear buttons once answered); the receiver thread with the per-bot user-level lock, takeover when the holder exits, start-of-run drain, offset file, backoff with jitter honoring `retry_after`, stop-and-report on 409/401/403, refusal to run while a webhook is set; routing through the Order 09 registry into `question_inbox.write_answer` with `channel=telegram`; token never logged (redact the token from URLs in every error path). OUT: setup and listen commands (Order 11).
- Scope-Paths: agent_workflows/notify/telegram.py, agent_workflows/notify/core.py, agent_workflows/notify/registry.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_notify_telegram.py, tests/fake_telegram.py
- Item-Dependencies: executed:txl556
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 10
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: qrup8m

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let the human answer a waiting question from Telegram on their phone, with the same guarantees as `aw runs answer` (spec `6kwd2e` R10.5, R10.6, R10.8a).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the adapter

- [ ] E-01 Write `notify/telegram.py` `TelegramChannel`: `capabilities()` (answer, buttons, max_text 4096 UTF-16 code units, callback_data 64 bytes); `send()` posts plain text (no `parse_mode`, previews off) with `force_reply` for free-text questions and an inline keyboard whose `callback_data` is `t:<16 random url-safe chars>` per option, registering (message id, tokens) in the registry; `receive(cursor, deadline)` calls `getUpdates(offset, timeout=25, allowed_updates=[message, callback_query])` with a 40 s socket timeout; `verify()` accepts only events whose `from.id` equals the configured user id AND whose chat is the configured PRIVATE chat id and `from.is_bot` is false; `ack()` answers every callback query (`recorded`, `already answered`, `not accepted`) and replies to free text likewise; `health()` reports `getMe`/`getWebhookInfo`. Token read from config or `AW_NOTIFY_TELEGRAM_TOKEN`; every exception message has the token redacted.
  - Depends on: none
  - Expected outcome: against the fake Bot API, a sent question produces the expected request bodies (no parse mode, tokens <= 64 bytes, force_reply when free text is allowed) and errors never contain the token.
  - Execution state: pending

- [ ] E-02 Map inbound events to answers: a callback whose token is in the registry for an open question becomes `write_answer(choice=<index>)`; a text message counts only when `reply_to_message.message_id` matches a registered question message (A52); anything else is acked `not accepted` and logged; unverified senders are dropped and logged without any reply (A50). Persist the offset to `<AW_HOME>/notify/telegram-<bot_id>.offset` ONLY after the batch's answers or rejections are written; if a write raises, do not advance past that update.
  - Depends on: E-01
  - Expected outcome: a button press writes the right question's answer; an unthreaded text message writes nothing; an update from another user or a group chat writes nothing and gets no reply; the offset is not advanced past an update whose write failed.
  - Execution state: pending

### Task group 2: the receiver

- [ ] E-03 Add the receiver loop: `TelegramReceiver(bot_id)` takes `<AW_HOME>/notify/telegram-<bot_id>.lock` with a non-blocking `filelock`; a live runner with Telegram enabled starts it as a daemon thread at run start (both hosts), drains once immediately (collecting answers sent while no runner was live, within Telegram's 24 hour retention), then long-polls until the run ends; a runner that cannot take the lock only sends, and retries the lock at each checkpoint so it takes over when the holder exits. Backoff with jitter on network errors and 5xx; honor `retry_after` on 429; on 409 (another poller) or 401/403 stop the loop, record a `notify-receiver-stopped` event with the reason, and leave the run unaffected (R10.6).
  - Depends on: E-02
  - Expected outcome: two runners on one bot: only the lock holder polls; when it exits the other takes over; a 409 stops the loop with an event; an answer queued before any runner started is consumed after the next run starts (A51).
  - Execution state: pending

- [ ] E-04 Refuse to poll while a webhook is configured on the bot (`getWebhookInfo.url` non-empty): record an event naming the remedy (`deleteWebhook`, done by `aw notify setup telegram` in Order 11) and fall back to send-only. When an answer is consumed (Order 09 `on_consumed`), edit the original message's keyboard away and reply `answered via <channel>`.
  - Depends on: E-03
  - Expected outcome: with a webhook set on the fake bot the receiver does not call `getUpdates`; after consumption the fake bot records an `editMessageReplyMarkup` and an acknowledgement message.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/fake_telegram.py`, a local `http.server` that emulates the five Bot API methods (including 409, 429 with `retry_after`, and webhook state), and `tests/test_notify_telegram.py` covering A50, A51, A52, the token-redaction rule, length limits with non-BMP characters near the boundary, and an end-to-end scripted run: a parked question reaches the fake chat, a button press is consumed at the next checkpoint, and the item resumes. Point the adapter at the fake server through a base-URL setting used only by tests.
  - Depends on: E-04
  - Expected outcome: the module passes; no test touches the real Telegram API.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Standard library HTTP only (`urllib.request`); Python 3.9 floor (all maintained Telegram libraries require >= 3.10, research `kdg4uz`/`49sv63`/`js5p5k`).
- One shared answer writer (`question_inbox.write_answer`); adapters never write `answers/` (spec `6kwd2e` R9.2).
- User-level lock and state under `AW_HOME`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Telegram allows one `getUpdates` consumer per bot token and returns 409 to competitors (research `kdg4uz` citing the Bot API server source).
- Unconfirmed updates are kept 24 hours (research `kdg4uz`, `49sv63`).
- Bot chats are cloud chats Telegram can read (research `kdg4uz`, `js5p5k`); setup must say so (Order 11).
- `cpcn9k`'s sample code accepts replies to any message and trusts button data (reconciliation 2026-10-17); not used.

## Proposed changes (ordered, validatable)

1. E-01 adapter. 2. E-02 event mapping and offset. 3. E-03 receiver with lock and takeover. 4. E-04 webhook refusal and answered edits. 5. E-05 fake API and tests.

## Deferred / out of scope (with reason)

- Setup, pairing, test and listen commands: Order 11.
  - Carrier: mrlblc
- Live testing against real Telegram on macOS, Linux and Windows: a hand checklist in Order 11 (research `js5p5k` section 7).
  - Carrier: mrlblc

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_notify_telegram.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R10.5, R10.6, R10.8a as amended.

## Open questions

### OQ-01: Plain text or HTML formatting?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED: plain text with no `parse_mode`. Research `kdg4uz` and `js5p5k` recommend it; HTML or MarkdownV2 escaping failures return 400 and drop the message, and question text is untrusted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the fake server's recorded request bodies for a sent question (no parse_mode, callback_data lengths, force_reply) and a forced error message showing the token redacted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste test output for button, threaded reply, unthreaded text, wrong user, group chat, and the failed-write offset case, with the offset file contents.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the event log of the two-runner fixture (lock holder polls, takeover after exit, 409 stop event) and the pre-start answer consumed after start (E-03's receiver).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the fake server log showing no `getUpdates` while a webhook is set, and the `editMessageReplyMarkup` plus acknowledgement after consumption.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
  - Result: pending

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
