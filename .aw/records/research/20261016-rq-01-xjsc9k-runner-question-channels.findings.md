---
id: xjsc9k
created: 20261016
set: rq
order: 01
topic: [runner, questions, notifications]
model: claude-opus-5-5
kind: findings
status: active
outcome: informational
summary: How a live aw run can ask the maintainer a question and take the answer back, over the terminal, a CLI verb, and push/chat channels (ntfy, Telegram, Teams, Google Chat, Signal)
consumed-by: []
---

# How a running `aw` run can ask the maintainer a question, and take the answer back

## Question

Approved spec `6kwd2e` designs how a runner turn surfaces a question: the worker writes it to its
outcome JSON and exits, the driver parks the item and keeps the queue moving, and the human answers
later through an answer file. The maintainer's objection (2026-10-17): as specified, the questions
"sit on the file system somewhere". The requirement is that a human who IS available can answer
WHILE the run is still running, and ideally from wherever they are (phone or chat), not only at a
terminal after the run drains.

This note works out the HOW: where a question is shown, how an answer gets back into a live run, and
which push/chat channels can carry both directions.

## What exists today (measured 2026-10-17)

- The worker cannot ask: OpenCode lanes run with `question: deny`
  (`lane_containment.LANE_PERMISSION_POLICY`); Antigravity has no permission lever and is told in the
  prompt not to ask. Both are deliberate (measured deadlocks) and `6kwd2e` keeps them.
- A worker's "deferred question" is free prose in `decisions-and-questions.md` plus an unvalidated
  `deferred_question_ids` list nothing consumes. `aw runs questions` reads a projection no runner writes.
- No notification exists anywhere in the package (no bell, `notify-send`, webhook, or chat).
- The driver ALREADY resumes a worker's own session mid-run for fix-it turns
  (`resume_via_launcher`, used by the combined-red and spec-anchor send-backs). That is the mechanism
  that makes a fast, context-preserving resume after an answer cheap.
- The driver ALREADY has a cooperative cross-process control file it polls at checkpoints
  (`runner_stop.poll_stop`, written by `aw ... stop`). That is the precedent for "another process
  tells a live driver something".

## Finding 1: one inbox, many adapters

Every way of answering should write the SAME thing to the SAME place, and the driver should read only
that place. Concretely, per run directory:

- `questions/<question_id>.json`: written by the driver when an item parks (question text, artifact
  id6, options if any, fingerprint, the artifact content hash per `6kwd2e` R5.6, status).
- `answers/<question_id>.json`: written by ANY adapter; carries the answer text, `actor: human`, the
  channel it came from, and the channel's sender identity. Written atomically (temp file + rename) so a
  half-written answer is never read.

Adapters are then thin and interchangeable: the terminal, an `aw runs answer` CLI verb, and each
chat channel. None of them talks to the driver directly. This keeps `6kwd2e`'s ledger rule
(`human_answer` must be `actor == "human"`) enforceable in ONE reader, and it means a channel can be
added without touching the run loop.

## Finding 2: answering during the run needs only a checkpoint poll

The driver is serial: between items it is idle for a moment. So "answer while it runs" needs:

1. At every dispatch checkpoint (the same points `poll_stop` is read), scan `answers/`.
2. An answered parked item goes back in the queue AHEAD of not-yet-started items, because its lane
   already holds real work against a base that goes stale while it waits (`6kwd2e` 0.35).
3. Resume it by RESUMING THE SAME AGENT SESSION with the answer as the next message
   (`resume_via_launcher`), not by a fresh turn. The agent keeps its full context, so an answer costs a
   short turn rather than a re-run. Fall back to a fresh turn with the answer in the prompt only when
   the session cannot be resumed.

Latency: an answer is picked up at the next checkpoint, i.e. when the item currently running
finishes (minutes, not hours). Picking it up mid-turn is possible but not worth it: the turn in flight
belongs to a different item.

What this does NOT do, deliberately: hold the questioning turn open while it waits. `6kwd2e` 0.3's
reasons stand (stall watchdog kills a silent child; a live ask requires relaxing `question: deny`;
head-of-line blocking). Parking plus session resume gets almost all of the benefit of a live ask
without any of those costs.

## Finding 3: the terminal, while the run streams

The run's terminal is busy streaming child output and the sticky statusline, so it cannot hold an
interactive prompt open without fighting that output. Workable options, in increasing cost:

- **Statusline count + bell (cheap, `6kwd2e` R4a.3/R4a.4).** "2 questions waiting" in the statusline,
  a bell on the first park. Tells the human to answer, does not take the answer.
- **Answer from a second terminal (cheap).** `aw runs answer <run-id>` lists open questions and takes
  answers interactively in its OWN process, writing the inbox. This works today on any machine,
  needs no new dependency, and is the reference adapter every other channel is tested against.
- **In-run hotkey (expensive).** Pressing a key in the run's terminal pauses the stream and opens the
  same answer prompt. Needs raw-mode keyboard handling alongside the existing SIGINT menu machinery
  (`runner_stop.interrupt_menu_is_safe`), which is the most wedge-prone code in the runners. Defer.
- **Ask at the drain (cheap, `6kwd2e` R5.3).** When nothing else is dispatchable and the human is
  present, ask the remaining questions in the run's own terminal, then re-dispatch.

## Finding 4: push and chat channels

The key property is whether a channel can carry the ANSWER back without the maintainer running a
public HTTPS server. A channel that needs an inbound webhook endpoint is far harder to deploy from a
workstation than one the driver can poll outbound.

| Channel | Notify | Answer back | How the answer comes back | Setup | Verdict |
|---|---|---|---|---|---|
| Telegram | yes | yes, free text and buttons | Bot API long-polling (`getUpdates`); outbound HTTPS only, no server | Create a bot with BotFather, put the token and your numeric user id in config | **Best two-way fit.** Inline buttons for multiple choice, reply-to-message for free text. |
| ntfy | yes | yes, with a reply topic | Driver subscribes to a second "answers" topic over an outbound streaming GET; you publish the answer from the ntfy app. Action buttons can also publish a fixed answer. | A topic name (a secret unless self-hosted with an access token) | **Easiest to set up**, but replies are clunky: free text means typing into the app with the question id. |
| Signal | yes | yes | `signal-cli` (or its REST wrapper in Docker) `receive` loop | A dedicated phone number registered to signal-cli, a Java or Docker dependency | Works, but the heaviest local dependency. |
| Microsoft Teams | yes, via an incoming Workflows webhook | not practically | Two-way needs a registered Bot Framework/Azure bot and a public HTTPS endpoint, or Graph API polling with tenant consent | Tenant admin involvement for two-way | Notify-only unless you already run Azure bot infrastructure. |
| Google Chat | yes, via an incoming webhook | possible, heavy | A Chat app in a Google Cloud project, receiving events over Pub/Sub pull (avoids a public endpoint) | A Workspace account and a GCP project | Notify-only in practice; two-way only if the Workspace/GCP setup already exists. |
| Generic (Apprise library) | yes, 100+ services | no | n/a | One URL per service | Good catch-all for notify-only. |

So "easily wire in": Telegram and ntfy, yes, both directions. Signal, yes with a heavier helper. Teams
and Google Chat, notify easily, answer only with real platform setup.

## Finding 5: the risks a chat channel adds, and their mitigations

An answer becomes an instruction an agent acts on, so a channel is an authority boundary, not just a
transport.

- **Spoofed answers.** Anyone who finds a Telegram bot or guesses an ntfy topic can send it messages.
  The adapter MUST accept answers only from configured sender identities (Telegram numeric user id;
  ntfy access token or a self-hosted server with auth; Signal sender number) and MUST record the
  sender in the answer. An answer from anyone else is dropped and logged, never applied.
- **Data leaving the machine.** A question quotes plan text and file paths, and it goes to a third
  party's servers. Channels MUST be opt-in per repository, and the outbound text MUST go through the
  same leak sanitizer `aw sanitize` uses (absolute paths, usernames, hostnames) before it is sent.
  A "terse" mode that sends only "run X has 2 questions" plus a question id, and takes the answer in
  the terminal or CLI, should exist for repositories whose content must not leave the machine.
- **Secrets in config.** Bot tokens and topic names belong in the user-level config or environment,
  never in tracked project config.
- **Stale answers.** Unchanged from `6kwd2e` R5.6: an answer records the artifact hash it was given
  against, and the driver refuses to apply it silently to a rewritten artifact.
- **Unattended runs.** Under `--unattended`, the driver still parks, writes the inbox and notifies;
  what it must not do is prompt at the terminal (`6kwd2e` R7). A chat answer arriving during an
  unattended run is still a human answer and may be applied: "unattended" means nobody at the
  terminal, not "nobody may answer".

## Recommendation

1. Amend `6kwd2e` (or add a companion spec) with: the per-run question/answer inbox as the single
   carrier (Finding 1); checkpoint polling plus same-session resume (Finding 2); `aw runs answer` as
   the reference adapter (Finding 3); a channel adapter interface with sender allowlisting,
   sanitized outbound text and a terse mode (Finding 5).
2. Build channels in this order: terminal bell + statusline count; `aw runs answer`; Telegram
   (two-way); ntfy (two-way via reply topic); an Apprise-backed notify-only adapter that covers Teams
   and Google Chat webhooks for free; Signal last, if wanted.
3. Then implement the whole of `6kwd2e` plus this amendment as a plan Set, per the maintainer's
   choice of the full-spec route.
