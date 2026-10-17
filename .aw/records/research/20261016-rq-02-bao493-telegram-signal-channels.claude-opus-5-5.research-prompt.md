---
id: bao493
created: 20261016
set: rq
order: 02
topic: [runner, questions, notifications, telegram, signal]
model: claude-opus-5-5
kind: research-prompt
outcome: none-yet
summary: Upload-ready research prompt: best way to implement two-way Telegram and Signal question/answer channels for aw runners on macOS, Linux and Windows
consumed-by: []
---

# Research task: two-way Telegram and Signal channels for a developer CLI, on macOS, Linux and Windows

You are a research agent with web search. Use it heavily: this task depends on current facts
(API behavior, library maintenance status, packaging, rate limits, licensing) that change over time
and that you must verify against primary sources rather than recall. For every factual claim that
drives a recommendation, cite the source (official docs, the project's repository, release notes, or
issue tracker) and the date or version you checked.

## The codebase under discussion

The project is `agent-workflows`, a public, open-source Python toolkit:

    https://github.com/fariello/agent-workflows

You may read it. Relevant facts, so you do not have to rediscover them:

- It ships a CLI, `aw`, as a Python package (`agent_workflows/`). `requires-python = ">=3.9"`.
  Its only runtime dependency today is `filelock`. Keeping the core install dependency-light is a
  strong preference: an optional extra (for example `pip install agent-workflows[telegram]`) is
  acceptable, a heavy mandatory dependency is not.
- It must run on macOS, Linux and Windows.
- `aw oc run` and `aw agy run` are long-running "runner" processes (often hours, often unattended)
  that drive AI coding agents through a queue of work items. Each item runs in its own agent session.
- The design being implemented (see the repository's spec `6kwd2e`, "Surfacing a mid-run question to
  the human without stopping the queue", and research note `xjsc9k`, "runner question channels",
  under `.aw/records/`): when an agent needs a human decision, it writes the question to a file and
  exits; the runner parks that item and keeps working on others. Each question is written to a
  per-run inbox (`questions/<question_id>.json`), and ANY answering channel writes the human's
  answer to `answers/<question_id>.json`. Between items the runner checks for answers and resumes the
  parked item in the same agent session with the answer.
- So a chat channel is an ADAPTER with two jobs: (1) deliver a question to the human's phone or
  desktop, and (2) carry the human's reply back into `answers/`. It must not require the human to run
  a public HTTPS server. Outbound-only connections (polling) are strongly preferred.
- Questions may contain short excerpts of plan text and file paths. The project already has a leak
  sanitizer that strips absolute paths, usernames and hostnames before text leaves the machine.

## What to research

### A. Telegram (two-way)

1. The best way for a Python 3.9+ CLI to send a message and receive replies through a Telegram bot
   with NO inbound webhook: Bot API long polling (`getUpdates`) versus a webhook, and whether a
   library is worth its weight. Compare raw HTTPS calls to the Bot API using only the standard
   library (`urllib`) against maintained libraries (for example `python-telegram-bot`, `aiogram`,
   `pyTelegramBotAPI`, and any others you find). Cover maintenance status, Python version support,
   install footprint, async requirements, and license.
2. How to receive the answer: inline keyboard buttons (callback queries) for multiple-choice
   questions, and reply-to-message or force-reply for free-text answers. How to reliably map a reply
   back to the right question id.
3. Polling correctness: `offset` handling, at-least-once versus exactly-once delivery, what happens
   when two runner processes on the same machine (or two machines) poll the same bot token at once
   (`409 Conflict`?), and the recommended pattern when several concurrent runners share one bot.
   Include long-poll timeouts, rate limits, message length limits, and formatting/escaping pitfalls.
4. Security: how to restrict accepted answers to the maintainer only (numeric user id or chat id
   allowlist), how the maintainer can safely discover their own id during setup, how to store the
   bot token (environment variable, OS keychain such as macOS Keychain, Windows Credential Manager,
   Linux Secret Service, or a user config file with restricted permissions), and what Telegram can
   read (bot chats are not end-to-end encrypted: state this precisely with a source).
5. Setup UX: the minimum steps for a user to go from nothing to a working two-way channel
   (BotFather, token, first message, id discovery), and how a CLI can automate or verify each step
   (for example an `aw notify setup telegram` command that sends a test message and waits for a
   reply).
6. Per-OS notes for macOS, Linux and Windows: proxies, TLS/certificate issues, corporate firewalls,
   sleep/wake behavior of long polls, and anything else that breaks in practice.

### B. Signal (two-way)

1. Every realistic way for a program to send and receive Signal messages today, with current
   status: `signal-cli` (Java; its JSON-RPC and D-Bus daemon modes), `signal-cli-rest-api` (Docker),
   `libsignal` bindings, `presage` or other Rust clients, `semaphore`, and anything newer you find.
   For each: maintenance health, how it authenticates (dedicated registered number versus linking as
   a secondary device to the user's own account), how fragile it is when Signal's servers change, and
   its license.
2. For each option, whether it runs NATIVELY on macOS, Linux and Windows (not only under WSL or
   Docker), what it needs installed (JRE version, Docker, native libraries), and how large that is.
3. Registration realities: does it need a separate phone number, CAPTCHA handling, rate limits,
   whether linking to the user's existing account as a secondary device is supported and stable,
   and what happens to the linked device if it is offline for days.
4. How a Python CLI should talk to it with the least coupling: subprocess per message, a long-running
   daemon with JSON-RPC over a local socket or TCP, or a REST wrapper. How to receive replies
   reliably, map them to a question id, and restrict accepted senders.
5. Terms of service and account-ban risk for automated use of a personal account.
6. A frank verdict: is Signal practical as an OPTIONAL channel for this tool on all three OSes, or
   should it be documented as "Linux/macOS with Docker or Java only"?

### C. Cross-cutting

1. The adapter interface you would recommend so Telegram, Signal and future channels (ntfy, Teams,
   Google Chat webhooks via Apprise) share one shape: `send(question)`, a poll or receive loop,
   sender verification, idempotency, and a "terse mode" that sends only "N questions waiting" with no
   content.
2. Where the receive loop should live: inside each runner process (several runners may be live at
   once), or in one small per-user background process that serves all runs and writes into each
   run's `answers/` directory. Weigh this per OS (launchd on macOS, systemd user units on Linux, Task
   Scheduler or a startup entry on Windows, or simply "only while a runner is live").
3. Anything that would make you recommend AGAINST building either channel.

## Deliverable

Return your answer as a DOWNLOADABLE markdown file named
`telegram-signal-channels-research.md`. Structure it as:

1. **Summary** (10 lines or fewer): the recommended approach for Telegram and for Signal, each in
   one or two sentences, and a ship/don't-ship verdict for each.
2. **Telegram**: sections A1 to A6, each ending with a concrete recommendation.
3. **Signal**: sections B1 to B6, each ending with a concrete recommendation.
4. **Cross-cutting**: sections C1 to C3.
5. **Comparison table**: rows Telegram (stdlib), Telegram (best library), each viable Signal option;
   columns: two-way support, macOS / Linux / Windows native support, install footprint, setup steps,
   security model, maintenance risk, license.
6. **Minimal reference code** for the recommended Telegram approach (Python 3.9+, standard library
   only if that is your recommendation): send a question with buttons, long-poll for the reply,
   verify the sender, write the answer JSON atomically. Keep it short and correct; mark anything you
   did not run.
7. **Open risks and unknowns**: what you could not verify, and what should be tested by hand on each
   OS before shipping.
8. **Sources**: every source you used, with the date or version you checked.

Do not pad. Where sources disagree or information is stale, say so explicitly rather than picking one
silently.
