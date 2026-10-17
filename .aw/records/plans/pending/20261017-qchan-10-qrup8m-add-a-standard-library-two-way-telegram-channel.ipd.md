# IPD: Add a standard-library two-way Telegram channel

- Date: 2026-10-17
- Kind: child
- Concern: Notify-only channels (Order 09) tell the human a question is waiting but cannot carry the answer back. Spec `6kwd2e` R10.5, R10.6 and R10.8a (amended 2026-10-17) require a two-way Telegram channel on the standard library only: long polling with no webhook, inline buttons carrying random tokens, free text accepted only as a reply to a known question message, verified sender (numeric user id AND private chat id), one poller per bot identity per machine attached to a live runner, offset persisted only after the event is handled, and every callback acknowledged. Four independent research reports (`kdg4uz`, `cpcn9k`, `49sv63`, `js5p5k`) agree; `kdg4uz`'s reference code is the base, `cpcn9k`'s is not used.
- Scope: IN: `agent_workflows/notify/telegram.py` implementing the Order 09 `Channel` protocol over `urllib.request` (`getMe`, `getWebhookInfo`, `sendMessage`, `getUpdates`, `answerCallbackQuery`, optional `editMessageReplyMarkup` to clear buttons once answered); the receiver thread with the per-bot user-level lock, takeover when the holder exits, start-of-run drain, offset file, backoff with jitter honoring `retry_after`, stop-and-report on 409/401/403, refusal to run while a webhook is set; routing every inbound event through Order 09's `core.apply_inbound` (verification, event dedup, registry lookup, and the single answer writer, `channel=telegram`); acknowledgements of consumed and stale answers delivered through Order 09's `dispatch_checkpoint`; the token never logged (redacted from every error, event and traceback). OUT: setup, pairing and listen commands (Order 11); a cross-machine receiver (one bot per machine is the documented rule).
- Scope-Paths: agent_workflows/notify/telegram.py, agent_workflows/notify/core.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_notify_telegram.py, tests/fake_telegram.py
- Item-Dependencies: executed:txl556
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 10
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: qrup8m

## Workflow history
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let the human answer a waiting question from Telegram on their phone, with the same guarantees as `aw runs answer` (spec `6kwd2e` R10.5, R10.6, R10.8a).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the adapter

- [ ] E-01 Write `notify/telegram.py` `TelegramChannel` implementing Order 09's `Channel` protocol (`txl556` E-02). TRANSPORT: one `_call(method, params)` over `urllib.request` posting JSON to `<base_url>/bot<token>/<method>`, where `base_url` defaults to `https://api.telegram.org` and is overridable only by the `AW_NOTIFY_TELEGRAM_BASE_URL` environment variable (tests) and only to an `https` URL or a loopback `http` URL; redirects are refused (the Order 09 webhook opener pattern); every `HTTPError`/`URLError`/`OSError` is caught inside `_call` and re-raised as a `TelegramError(code, description, retry_after)` constructed with `from None`, carrying no URL, because `HTTPError.filename` and `geturl()` hold the full token-bearing URL (measured at review); a final `str.replace(token, "<token>")` is applied to every message the module emits. TOKEN: from the Order 09 user config (`notify/config.py`) or `AW_NOTIFY_TELEGRAM_TOKEN`. CAPABILITIES: `answer=True`, `buttons=True`, `max_text=4000` measured in UTF-16 code units (`len(text.encode("utf-16-le")) // 2`, a margin under Telegram's 4096), callback data <= 64 bytes. SEND: Order 09's `build_batch` already sanitized the text; `send` posts plain text (no `parse_mode`, `link_preview_options.is_disabled`), truncating any field over the UTF-16 budget without splitting a surrogate pair. In `terse` mode one message per batch with NO buttons and no `force_reply` (R10.4). In `full` mode one message per question with an inline keyboard whose `callback_data` is `t:` plus 16 characters from `secrets.token_urlsafe` per option (button labels truncated to 64 bytes) and `force_reply` when the question allows free text; each returned `message_id` and each token is registered with `registry.register` (Order 09 E-06) BEFORE the next send. A send that raises a network or timeout error may have been delivered (Telegram has no client request id): record a `notify-uncertain` event and do NOT resend that question automatically. RECEIVE: `receive(cursor, deadline)` calls `getUpdates(offset=cursor, timeout=min(25, remaining), allowed_updates=["message","callback_query"])` with a 40 s socket timeout and returns `(events, next_cursor)` where `next_cursor` is the last `update_id + 1`. VERIFY: returns the sender identity only when `from.id` equals the configured user id, `from.is_bot` is false, `chat.id` equals the configured chat id AND `chat.type == "private"` (for a callback, the chat of `callback_query.message`); otherwise None. ACK: `answerCallbackQuery` for every callback with `recorded`, `already answered`, or `not accepted`, and a threaded text reply likewise for a free-text message. HEALTH: `getMe` and `getWebhookInfo`, reporting bot username and whether a webhook is set, never the token.
  - Depends on: none
  - Expected outcome: against the fake Bot API, a full-mode question produces a `sendMessage` body with no `parse_mode`, previews disabled, every `callback_data` <= 64 bytes and `force_reply` only when free text is allowed; a terse batch has no `reply_markup`; a 401 and a refused connection both raise `TelegramError` whose `str()`, `repr()` and formatted traceback contain no token; a 5000-character text with non-BMP characters at the cut is truncated to <= 4000 UTF-16 units with no lone surrogate.
  - Execution state: pending

- [ ] E-02 Map inbound updates through Order 09's `core.apply_inbound` (`txl556` E-06), which does verification, event dedup by `(telegram, update_id)`, the registry lookup and the `question_inbox.write_answer` call; this module only translates an update into an `InboundEvent` with the routing key: a `callback_query` carries its token and the option index the registry maps it to; a text `message` carries `reply_to_message.message_id` and its text, and a text message with no `reply_to_message`, or one whose id is not registered, becomes an event with no routing key that `apply_inbound` rejects (A52). Acknowledge per E-01 ACK from the result, except that an `ignored` (unverified or duplicate) event gets NO reply (A50). OFFSET: hold it in `<AW_HOME>/notify/telegram-<bot_id>.offset`, written atomically, and advance it past an update ONLY after `apply_inbound` returned for it; if `apply_inbound` raises, stop processing the batch, persist the offset of the last handled update, record a `notify-inbound-failed` event, and back off before the next poll, so the failed update is redelivered and the shared writer's first-answer-wins makes a replay harmless.
  - Depends on: E-01
  - Expected outcome: a button press writes the right question's answer with `channel: telegram` and the numeric sender; a threaded reply writes the free-text answer; an unthreaded text writes nothing and is acked `not accepted`; an update from another user, a bot, or a group chat writes nothing and gets no reply; a replayed update writes nothing new; the offset file is not advanced past an update whose handling raised.
  - Execution state: pending

### Task group 2: the receiver

- [ ] E-03 Add `TelegramReceiver(bot_id)`: a daemon thread that holds `<AW_HOME>/notify/telegram-<bot_id>.lock` through a non-blocking `filelock.FileLock(..., timeout=0)`, polls with E-01 `receive` and routes with E-02 until its stop event is set, and releases the lock on exit. START: at run start and at resume on both hosts (the top of `run_queue`, beside Order 09's first `dispatch_checkpoint`), when the effective channel set (Order 09 `effective_channels`) includes Telegram, call `notify.telegram.ensure_receiver(run_dir)`; it first checks the webhook (E-04), then tries the lock; on success it starts the thread, whose first poll drains every update Telegram holds (R10.6 start-of-run drain); on failure the runner is send-only and `ensure_receiver` is called again at every checkpoint, so it takes over when the holder exits. The receiver serves EVERY run on the machine through the registry, not only its own run (R10.6). It writes its events to the starting run's `events.jsonl` through `runner_shared.append_jsonl` (`notify-receiver-started`, `notify-receiver-stopped` with reason). STOP: register the receiver with `runner_shared.register_active_sampler` so `runner_shutdown.clean_shutdown` stops it, and stop it explicitly before the run summary; stopping sets the event, waits up to 45 s (one long poll) and never blocks the exit beyond that. ERRORS: network errors and 5xx back off exponentially from 1 s to 60 s with jitter; 429 sleeps `retry_after`; 409 (another poller, possibly on another machine), 401 and 403 stop the thread, release the lock and record `notify-receiver-stopped` with the reason and the remedy (`409`: another process or machine is polling this bot; use one bot per machine), and are NOT retried. No receiver error changes an item or the run's exit code (R10.6 last sentence).
  - Depends on: E-02
  - Expected outcome: two runners on one bot: only the lock holder calls `getUpdates`; when it exits the other takes the lock at its next checkpoint and starts polling; a 409 stops the loop with a `notify-receiver-stopped` event naming 409 and the run's exit code is unchanged; an update queued on the fake server before any runner started is applied after the next run starts (A51); a run with Telegram not configured starts no thread.
  - Execution state: pending

- [ ] E-04 Refuse to poll while a webhook is set: `ensure_receiver` calls `getWebhookInfo`, and a non-empty `url` records one `notify-receiver-stopped` event naming the remedy (`aw notify setup telegram`, Order 11, offers `deleteWebhook`) and leaves the channel send-only; the webhook is NEVER deleted here.
  - Depends on: E-03
  - Expected outcome: with a webhook set on the fake bot, no `getUpdates` and no `deleteWebhook` request is recorded, and sends still succeed.
  - Execution state: pending

- [ ] E-06 Acknowledge consumption in the chat: implement the channel side of Order 09's `dispatch_checkpoint` acknowledgement (`txl556` E-03, which sends once per consumed or stale answer): for a question whose message id is in the registry, call `editMessageReplyMarkup` with an empty keyboard on the original message and send the acknowledgement text as a reply to it; a failure is recorded as `notify-failed` and never retried in a loop. No new hook is added: the acknowledgement is the `send` of an acknowledgement batch that Order 09 already issues.
  - Depends on: E-01
  - Expected outcome: after an answer is consumed, the fake bot records one `editMessageReplyMarkup` for the original message id and one reply `answered via telegram`; a stale answer yields the stale notice; a second checkpoint sends nothing more.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/fake_telegram.py`, a loopback `http.server` emulating `getMe`, `getWebhookInfo`, `sendMessage`, `getUpdates` (offset confirmation, scripted 409, 429 with `retry_after`, 5xx), `answerCallbackQuery` and `editMessageReplyMarkup`, recording every request; and `tests/test_notify_telegram.py` (marked `pytest.mark.core`) covering A50, A51, A52, token redaction, the UTF-16 limit with non-BMP text, terse versus full sends, uncertain delivery, offset handling, the receiver lock and takeover, webhook refusal, acknowledgements, and an end-to-end scripted run on both hosts (scripted-host pattern of `tests/test_run_proposal_channel.py`): a parked question reaches the fake chat, a button press arrives, Order 04's `consume_answers` re-queues the item at the next checkpoint and it resumes. The adapter is pointed at the fake server with `AW_NOTIFY_TELEGRAM_BASE_URL`; receiver threads use short poll timeouts set by a test-only constructor argument, so the module runs in seconds; every test runs under the conftest `AW_HOME` sandbox.
  - Depends on: E-04, E-06
  - Expected outcome: the module passes; no test contacts any host other than loopback; the routine gate passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Standard library HTTP only (`urllib.request`); Python 3.9 floor (`pyproject.toml` `requires-python = ">=3.9"`; maintained Telegram libraries require >= 3.10, research `kdg4uz`/`49sv63`/`js5p5k`); `filelock` (installed 4.x, declared `>=3`) is the only runtime dependency.
- One shared answer writer (`question_inbox.write_answer`); adapters never write `answers/` (spec `6kwd2e` R9.2), and inbound routing goes through Order 09's `core.apply_inbound` (spec R10.1).
- User-level lock and state under `AW_HOME`; tests use the conftest `AW_HOME` sandbox.
- Background threads that must stop on shutdown register with `runner_shared.register_active_sampler`, which `runner_shutdown.clean_shutdown` drains through `stop_active_samplers`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Telegram allows one `getUpdates` consumer per bot token and returns 409 to competitors; a file lock coordinates one machine only, so one bot per machine is the rule (research `kdg4uz` citing the Bot API server source).
- Unconfirmed updates are kept 24 hours; a batch holds at most 100 (research `kdg4uz`, `49sv63`).
- `sendMessage` has no client request id, so a timed-out send may have been delivered; resending risks a duplicate (research `kdg4uz`).
- Bot chats are cloud chats Telegram can read (research `kdg4uz`, `js5p5k`); setup must say so (Order 11).
- Measured at review: `urllib.error.HTTPError.filename` and `geturl()` carry the full request URL, which for the Bot API includes the token; `str(e)` does not. So the token must be stripped by construction in `_call`, not by redacting messages afterwards.
- `cpcn9k`'s sample code accepts replies to any message and trusts button data (reconciliation 2026-10-17); not used.

## Proposed changes (ordered, validatable)

1. E-01 adapter and transport. 2. E-02 inbound translation and offset. 3. E-06 chat acknowledgements. 4. E-03 receiver, lock, takeover and shutdown. 5. E-04 webhook refusal. 6. E-05 fake API and tests.

## Deferred / out of scope (with reason)

- Setup, pairing, test and listen commands: Order 11.
  - Carrier: mrlblc
- Live testing against real Telegram on macOS, Linux and Windows: a hand checklist in Order 11 (research `js5p5k` section 7).
  - Carrier: mrlblc
- One receiver across several machines sharing a bot: a file lock cannot coordinate machines; the 409 stop and the one-bot-per-machine rule are the v1 answer.
  - Carrier-Declined: a shared remote broker is new product scope (research `kdg4uz`), not required by spec `6kwd2e` R10.6, which scopes the lock to one machine

## Scope check

- Over-scope: none.
- Under-scope: none after review (E-06 split out of E-04; `registry.py` and `runner_shared.py` removed from Scope-Paths because they are only called).

## Required tests / validation

`python3 -m pytest -o addopts="" tests/test_notify_telegram.py tests/test_notify_core.py` (no `-q`, so the `N passed` line prints) and the routine gate `python3 -m pytest`.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R10.5, R10.6, R10.8a as amended; no spec file is edited. User documentation and the CHANGELOG entry are Order 11's (`mrlblc` E-03).

## Open questions

### OQ-01: Plain text or HTML formatting?

- Blocking: no
- Status: resolved
- Owner: plan author (settled by spec `6kwd2e` R10.8a "plain text with no parse mode"; recorded at review as decision D-1)
- Resolution or deferral rationale: RESOLVED: plain text with no `parse_mode`. Spec R10.8a requires it, and research `kdg4uz` and `js5p5k` recommend it; HTML or MarkdownV2 escaping failures return 400 and drop the message, and question text is untrusted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the fake server's recorded `sendMessage` bodies for a full-mode question (no `parse_mode`, previews disabled, each `callback_data` byte length, `force_reply`) and a terse batch (no `reply_markup`); the `str()`, `repr()` and formatted traceback of a `TelegramError` from a 401 and from a refused connection, each showing no token; and the UTF-16 length of the truncated non-BMP text.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste test output for button, threaded reply, unthreaded text, wrong user, bot sender, group chat, and replayed update, with `ls answers/` and the fake server's reply log for each; and the offset file contents before and after the batch in which handling raised.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the fake server's request log and both runs' `events.jsonl` lines from the two-runner fixture (only the holder's `getUpdates`, `notify-receiver-started` for the second runner after the first exits), the 409 `notify-receiver-stopped` event with the run's exit code, the answer file written from an update queued before the run started, and a run without Telegram showing no receiver event (produced by E-03's `ensure_receiver` at the top of both hosts' `run_queue`).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the fake server log with a webhook set, showing `getWebhookInfo` and `sendMessage` but no `getUpdates` and no `deleteWebhook`, and the `notify-receiver-stopped` event naming the remedy.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the fake server log after consumption showing one `editMessageReplyMarkup` for the original message id and one threaded `answered via telegram` reply, the stale-notice reply for a stale answer, and the log after a second checkpoint showing no further request (produced by Order 09's `dispatch_checkpoint` calling this channel's `send`).
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
