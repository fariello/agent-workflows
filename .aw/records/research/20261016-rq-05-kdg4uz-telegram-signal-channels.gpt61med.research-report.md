---
id: kdg4uz
created: 20261017
set: rq
order: 05
topic: [runner, questions, notifications, telegram, signal]
model: gpt61med
kind: research-report
status: todo
outcome: none-yet
summary: Response to bao493 by gpt61med: two-way Telegram and Signal question channels for aw runners on macOS, Linux and Windows
consumed-by: []
---

# Telegram and Signal question channels for agent-workflows

Research checked **2026-10-17**. Response to research prompt `bao493`. Repository context: research `xjsc9k` and approved spec `6kwd2e`, especially R5.4 (human attribution), R5.6 (artifact hash), and R7 (unattended execution). This is research and reference code, not an implementation or a spec amendment. Proposed command names below do not imply shipped commands.

## 1. Summary

**Telegram: ship an opt-in adapter using standard-library HTTPS and long polling**, with one receiver per bot token and durable routing for all local runs. Current library releases add dependencies and require Python 3.10+, above the stated 3.9 baseline. [PTB][T3], [aiogram][T4], [pyTelegramBotAPI][T5]

**Signal: defer a generally supported channel.** An experimental adapter to an operator-installed `signal-cli` is technically plausible on all three OSes, but needs native packaging tests, frequent updates, and a deliberate policy decision about account automation. [signal-cli][S1] [Signal terms][S9]

Keep local answer files authoritative. Neither channel should delay queue dispatch or replace the local answer command.

## 2. Telegram

### A1. Transport and Python library choice

Long polling uses outbound HTTPS; a webhook requires an endpoint Telegram can reach. They are mutually exclusive. [Bot API][T1]

| Implementation | Checked maintenance and compatibility | Dependencies / execution model | License |
|---|---|---|---|
| `urllib.request` | Python standard library; works with the 3.9 language baseline | No added package; synchronous HTTP in a broker thread/process | Python distribution license; original adapter uses repository license |
| `python-telegram-bot` | PyPI 22.8, released 2026-06-12; Python >=3.10 | Asyncio; required HTTPX, plus its dependencies; 769.4 kB package wheel, excluding dependencies | LGPL-3.0-only |
| `aiogram` | Current PyPI release dated 2026-08-26; Python >=3.10,<3.15 | Asyncio; aiohttp, Pydantic, aiofiles, magic-filter and other dependencies | MIT |
| `pyTelegramBotAPI` | PyPI 4.37.0, 2026-09-21; current metadata requires >=3.10 | Sync and async interfaces; current source declares requests and aiohttp | GPLv2 |

Sources: [stdlib][P1], [PTB package and release files][T3], [PTB dependency description][T6], [aiogram package][T4], [aiogram dependency declarations][T7], [pyTelegramBotAPI package][T5], [its current build metadata][T8]. Wheel size is compressed download size, not installed size. Source branches can differ from published packages; measure a resolved installation before promising disk usage. Older Python-compatible releases exist, but retaining an old bot framework solely for 3.9 would create a second compatibility burden.

**Recommendation:** use stdlib for this narrow API subset. If scope grows into a full bot application and Python's minimum rises, PTB is the best library alternative: its HTTPX dependency is relatively modest and it supplies typed objects and update handlers. Do not add a user-account MTProto client for a Bot API task.

### A2. Answer interaction and correlation

The API provides inline callback buttons, callback sender information, message reply references, and ForceReply. Callback data is limited to 1–64 bytes. [Bot API][T1]

Recommended design: persist `(bot identity, chat_id, message_id) -> (run registry key, question_id, artifact_hash, revision)` and an opaque random button token -> option index. Persist before considering delivery complete. Treat button data as untrusted input: resolve only tokens already issued for that message and sender. Never embed an answer-file path in a button.

For text, accept replies only to a known bot question message. ForceReply improves discoverability but is not authentication. For multiple-choice plus custom text, offer an explicit custom-reply instruction; do not rely on a client automatically selecting the intended message. Never interpret an unthreaded “yes” as answering the latest question when several runs are active. Unknown, expired, edited, or already answered questions must not silently change the decision.

**Recommendation:** buttons for fixed options; reply-to-message for text; persist routing independently of runner lifetime and refuse ambiguous replies.

### A3. Poll correctness, concurrency, and limits

`getUpdates` confirms an update once a later request supplies a higher offset; batches contain at most 100 updates, and server retention is at most 24 hours. [Bot API][T1] The Telegram server implementation explicitly aborts a competing long poll with HTTP 409. [Server source][T9]

Use one receiver per token, across machines as well as processes. On one machine, an existing `filelock` dependency can protect a per-user broker lock keyed by bot identity. A filesystem lock on one machine cannot coordinate another machine. Prefer a distinct bot per machine; a shared remote broker would require authenticated host routing and is additional product scope. Serialize setup polling through the same broker. On 409, surface a conflict and stop that receiver; do not create competing restart loops or delete an existing webhook automatically.

Process each update into a durable local journal/answer or a recorded rejection, then persist `update_id + 1`; only then make the next poll. A crash can replay an update. Use idempotent consumption and first-answer-wins publication across *all* channels, not a claim of exactly-once network delivery. Persist routing and cursor together transactionally where practical. Do not skip pending updates at startup. A send timeout may mean the message was sent: Telegram offers no client request id for `sendMessage`, so record uncertain delivery and reconcile or explicitly resend with a duplicate warning.

Operational defaults proposed here: 25-second long poll, 40-second HTTP timeout, bounded exponential backoff with jitter for network/server failures, `retry_after` for 429, explicit allowed update types. Do not retry authentication or ownership conflicts indefinitely. Message text permits 4096 characters after entity parsing. [Bot API][T1] Published guidance is about 1 message/second per chat, 20/minute in a group, and about 30/second for ordinary broadcasts. [Bot FAQ][T2]

Use plain text with no `parse_mode`; paths and excerpts otherwise trigger Markdown/HTML escaping problems. Chunk only after sanitization, keep each chunk below a conservative UTF-16 length budget, and identify the reply-bearing chunk. Disable previews and rate-limit bursts from many parked items. Acknowledge callbacks promptly, but never equate the spinner acknowledgment with a persisted answer.

**Recommendation:** one durable broker, at-least-once processing with idempotent effects, a throttled outbox, and visible uncertain-send/lost-retention states.

### A4. Authorization, secrets, and privacy

Restrict v1 to private chats and require both the configured numeric sender user id and chat id. Usernames and display names are mutable presentation data. A group chat id alone would authorize every participant. Store observed identity, provider event id, and question revision in the answer audit record.

During local setup, generate a random, expiring pairing secret; ask the user to send it to their own bot; accept only that matching private message; show the resulting numeric ids locally and require local confirmation before saving them. Do not adopt the first stranger who contacts the bot or use a third-party id-discovery bot. Test both a callback and a text reply.

The Bot API token is a bearer credential and occurs in request URLs. Avoid URL logging, shell-history entry, tracebacks containing URLs, or token-bearing diagnostics. Prefer an optional `keyring` integration with macOS Keychain, Windows Credential Locker, or Linux Secret Service; headless Linux may lack an unlocked service. Those backends are documented by the keyring project. [Keyring][P3] Environment variables suit unattended injection but are not a vault. A fallback config needs a private directory, POSIX 0600 files, and a Windows user-only ACL; `chmod(0600)` alone is not a Windows ACL policy. Never store tokens in repository config.

Bot conversations are cloud chats, **not end-to-end encrypted Secret Chats**: Telegram's service is within the content trust boundary, as is the bot operator. Cloud chats use client/server encryption; Telegram processes cloud messages and bot interactions under its privacy policy. [Telegram FAQ][T10] [Privacy policy][T11] Sanitization reduces identifying data, not all confidential content.

**Recommendation:** explicit pairing, private-chat sender AND chat checks, OS secret storage where available, and content disclosure opt-in with terse notifications available.

### A5. Minimum setup flow

The official creation route is `@BotFather` and `/newbot`; the resulting token authorizes API calls. The user must initiate contact with the bot. [Official tutorial][T12]

Proposed `aw notify setup telegram`:

1. Explain cloud-chat privacy and open the official BotFather link; the user creates the bot.
2. Read the token using hidden terminal input or an existing secret reference. Run `getMe` and display the bot username; inspect webhook status and refuse silent takeover.
3. Ask the user to open that bot and send the generated pairing phrase. Poll under the broker's ownership; show and locally confirm the candidate numeric identity.
4. Send a button test and a reply test, verify both identities/correlations, then save the configuration and selected content mode.
5. Report receiver health and a local recovery command. On timeout, leave setup incomplete without registering an unrelated sender.

**Recommendation:** automate validation and pairing, while leaving account creation and local identity approval with the user.

### A6. macOS, Linux, and Windows

`urllib.request` supports proxy discovery, including environment variables and platform configuration; its behavior is not equivalent to supporting every corporate proxy authentication scheme. TLS validation uses the Python/OpenSSL configuration; a custom CA can be loaded into an SSL context. [urllib][P1] [ssl][P2]

| OS | Practical verification and proposed handling |
|---|---|
| macOS | Test both Intel and Apple Silicon Python distributions, their CA installation, explicit HTTP CONNECT proxy, Keychain access without a foreground terminal, sleep/wake, and launchd restart. |
| Linux | Test the deployment's CA bundle, headless Secret Service absence, user-service logout behavior, and DNS/proxy changes after reconnect. |
| Windows | Test CPython certificates and enterprise CA configuration, explicit proxy, user ACLs, scheduled task environment, console-less shutdown, and suspend/resume. Avoid assuming Unix sockets or signals. |

These are engineering test requirements, not claims of measured failures in this environment. Across all OSes, use outbound TCP 443 to `api.telegram.org`; request explicit firewall approval where blocked. Never disable certificate verification. Expose a CA-file/proxy option; SOCKS-only and integrated-auth proxy support may justify an optional HTTP client dependency later. On wake, discard dead connections and retry from durable state. A sleeping computer cannot receive; Telegram's short retention makes long offline periods a real reliability limit.

**Recommendation:** platform-neutral broker logic with configurable TLS/proxy settings, bounded retries, and a visible “receiver offline” state; test installers separately.

## 3. Signal

### B1. Realistic implementations and maintenance

| Option | What it actually provides; checked status | Authentication and license |
|---|---|---|
| `signal-cli` | Full send/receive; CLI, JSON-RPC, D-Bus. Latest release observed 0.14.9, 2026-10-07. Upstream warns releases over three months old may stop working. | Register a number or link an existing account; GPLv3. [README][S1] [Release][S2] |
| `signal-cli-rest-api` | Docker wrapper, latest 0.101, 2026-09-25; includes signal-cli 0.14.8, illustrating wrapper lag. | Same underlying account choices; wrapper MIT, underlying signal-cli GPLv3. [Release][S4] [License][S5] |
| Official `libsignal` | Cryptographic/client primitives, Java/Swift/TypeScript bridges; external use explicitly unsupported and APIs may change without notice. Not a ready Python messaging/account API. | You must build the account/network/storage client around it; AGPLv3. [README][S6] |
| Presage | Rust high-level library with receive/send, registration, linking, and SQLite storage. Current README includes recent storage migration references; a dated release/support cadence was not established. | Registration or linked device; AGPL-3.0 repository license. [README][S7] [Repository][S8] |
| Semaphore | Python rule-based framework over signald, not a replacement transport. PyPI latest observed 0.17.0, 2023-12-17. | signald-managed account; AGPLv3+. [Package][S10] |
| signald | Former Signal daemon; its own site says no longer actively maintained and recommends signal-cli. | Not a suitable new dependency. [Project notice][S11] |

All unofficial clients inherit compatibility risk when the service changes; this is an architectural inference, not a measured failure rate. Python bot wrappers around the REST wrapper do not remove its runtime or operational burden. No newer official supported bot API was established by the sources checked.

**Recommendation:** only evaluate `signal-cli` for a first adapter; reject direct libsignal integration, Semaphore/signald, and a new Rust-client maintenance obligation for this Python tool.

### B2. Native support and footprint

The current signal-cli README specifies **JRE 25 minimum**, a native libsignal-client library, and binaries intended for Linux, macOS, and Windows. It lists bundled libraries for x86_64 systems and sends other architectures to additional-build instructions. Experimental GraalVM builds are a distinct option. [README][S1] Do not repeat older Java 17/21 requirements as current facts.

| Option | macOS / Linux / Windows native status | Installation burden |
|---|---|---|
| signal-cli JVM | Upstream says all three; architecture and release-specific smoke tests still required | Java 25 runtime + CLI archive + compatible JNI library + persistent keys/state |
| signal-cli experimental native build | Upstream documents Linux-native download; native macOS/Windows release coverage not verified | Native executable/libraries, no JVM in that mode; experimental |
| REST Docker image | Linux container; Docker on macOS/Windows is not native execution of this client | Container engine, image, persistent volume; desktop Linux VM where applicable |
| Presage | No verified supported three-OS binary distribution | Rust build toolchain and native storage/crypto dependencies; portability unproven here |
| libsignal | Platform bridge builds, not an installable aw transport | Rust/C/C++/protocol compiler toolchain plus a complete client you must author |
| Semaphore/signald | Python portability does not establish daemon portability | Python framework plus obsolete daemon stack; reject |

The REST wrapper documents per-call JVM, native, and persistent JSON-RPC modes. [Wrapper README][S3] Presage documents SQLCipher/OpenSSL versus BoringSSL dependency interaction. [Presage README][S7] Exact total download size, installed size, resident memory, and CPU architecture coverage were **not measured**. Budget Java-based installs in hundreds of MB and container/toolchain deployments potentially in GB as planning allowances, not vendor-specified sizes; measure clean installations before publishing numbers.

**Recommendation:** describe Signal as experimental with an externally installed runtime. Do not label native Windows impossible, and do not promise universal native support merely because Java is portable.

### B3. Registration and linking

Linking avoids registering a separate number. Registration requires a reachable number and can require CAPTCHA; registering a number already used by a primary client replaces that registration. [signal-cli README][S1] Prefer linking through a QR code, never silently re-register a personal account.

Signal's **current** linked-device support page says the primary phone must come online at least every 30 days, linked devices unlink after 45 days of inactivity, and there are five linked-device slots. [Linked devices][S12] This differs from older references to 30-day linked-device inactivity: use the current page, and do not treat it as a guarantee about every unofficial client's behavior. A few offline days are below that documented inactivity threshold but do not establish queue retention or reconnect correctness.

No dependable numeric registration or message-rate quota was established. Handle service challenges/rate limits visibly, back off, and require human CAPTCHA completion; do not promise automated registration or ban avoidance.

**Recommendation:** optional operator-driven linking, explicit unlink health checks, documented relinking recovery, and no automatic CAPTCHA solving or re-registration.

### B4. Python integration and reply safety

The JSON-RPC manual supports stdin/stdout, Unix sockets, TCP, and HTTP; received messages appear as notifications. Its HTTP SSE endpoint keeps the last 1000 events in memory for reconnect replay, which is not a durable queue. Manual receive subscription is documented to avoid missing messages before subscription. [JSON-RPC manual][S13]

Proposed least-coupled path: one long-lived `signal-cli ... jsonRpc` child owned by the broker, with line-delimited JSON on pipes. Avoid shell execution. Drain stderr separately without exposing message content; match RPC response ids independently of incoming message notifications. Pipes avoid exposing an unauthenticated local TCP service and work across OSes. For an existing daemon, prefer a private Unix socket on supported hosts; a loopback TCP/HTTP service still needs protection from other local users. D-Bus adds OS integration that does not help Windows parity.

Persist each receive event immediately in the broker journal. A crash between underlying client receipt and journal commit may still lose an event; upstream replay does not establish end-to-end durable delivery. Deduplicate by account, sender identity, device where relevant, and message timestamp/event identity. Require explicit short question tokens in text, or verify quoted-message author plus timestamp against an issued question. Display names are not authorization. Pair an ACI (Signal account identity), enforce direct conversations, and do not silently trust changed cryptographic identities.

Linking the *maintainer's own* account creates an extra issue: replies from the phone may appear as sent-message synchronization events, not ordinary inbound messages. Accept only explicitly paired self-account sync events with the correct destination and question token; verify this behavior with the exact client version. A dedicated bot account gives cleaner inbound sender verification but adds account setup. Do not claim self-message reply routing was tested here.

**Recommendation:** persistent JSON-RPC pipes first, dedicated-account inbound messages where acceptable, and gate personal-account self-sync support on real-device tests.

### B5. Terms and account risk

Signal's terms prohibit impermissible communications, giving bulk messaging, auto-messaging, and auto-dialing as examples, and prohibit unauthorized automated account creation. They reserve account termination powers. [Terms][S9] That text creates uncertainty for even low-volume personal automation; an upstream notification use case is not permission from Signal. No authoritative exemption for this tool, safe numeric threshold, or account-ban probability was found.

**Recommendation:** do not present automation as endorsed or risk-free; resolve acceptable-use interpretation before promoting Signal as a supported product feature. This report does not offer a legal determination.

### B6. Ship verdict

Technical feasibility spans all three OSes through an externally installed JVM client, subject to native library and architecture validation. A policy statement of “Linux/macOS with Docker or Java only” would obscure Windows capability while conflating container and native execution.

**Recommendation:** **do not ship Signal as a generally supported channel yet**. If demand justifies it, ship an explicitly experimental external-signal-cli adapter after the policy decision and OS matrix pass; initially list only tested OS/architecture combinations. Keep Docker integration a separate operator guide.

## 4. Cross-cutting

### C1. Shared adapter contract

Proposed interface, not a description of existing code:

```text
capabilities() -> {notify, receive, choices, reply_thread, content_modes}
send(sanitized_question, delivery_key, mode) -> delivery_receipt | uncertain
receive(cursor, deadline) -> events
verify(event, configured_identity) -> verified_reply | rejection
normalize(verified_reply, durable_routes) -> answer_candidate
health() -> status
```

A broker owns the durable outbox, routes, journal and provider cursors. A shared answer writer owns locks, first-answer-wins arbitration, atomic publication, run/question identity checks, artifact hash/revision, expiry, input bounds, and audit identity. An answer to a decision is not permission for unrelated actions. Treat remote answer text as human input to the named question; never execute it as a shell command or allow it to choose filesystem destinations.

Register canonical run directories locally under random run keys. Resolve only registered roots; reject symlink/path traversal changes and retired questions. Apply the leak sanitizer before a delivery is enqueued, including button labels, diagnostics, and previews. Do not assume it removes secrets or business-sensitive text.

`mode=terse` sends only “N questions waiting”, coalesced across runs, without project names, paths, options, or inline answer buttons. It directs the human to local answering. An option label or decision itself can leak content, so offer no remote content exchange in this mode.

A notify-only webhook fits `send` and declares `receive=false`. Apprise delivery to Teams/Google Chat does not establish two-way replies; a platform-specific authenticated receive integration remains separate. Future ntfy reception must likewise define its own sender authorization rather than treating a topic name as a human identity.

### C2. Receiver location and OS lifecycle

Choose **one per-user broker**, not a poller in every runner. Start it explicitly or elect a live-runner owner using a per-user lock and durable registration. Other runners write requests to its local spool. A broker death must not kill runners; a replacement recovers routes, pending outbox entries, journal, and cursors. Do not start a worker model or ask for a human decision merely to receive chat.

For the first release, support foreground `aw notify listen` and a broker child while runners are live. An optional installed service can later use launchd on macOS, a systemd user unit on Linux, or a per-user Task Scheduler task on Windows. These are proposed deployment choices, not configurations tested here. Document that receiver shutdown stops reception; queued Telegram replies may expire before the next run. If a run has drained and exited, receipt only stores the answer; resuming requires the runner's documented resume mechanism.

Persistent-service installation should be explicit. Service accounts need the same secret store and filesystem identity as the run registry; do not silently grant system-wide access. Across machines, prefer distinct bots rather than pretending local leader election is distributed coordination.

### C3. Reasons to stop or narrow scope

Do not build content-bearing Telegram support where cloud access to question/answer text is unacceptable. Do not build Signal support without capacity to maintain its external client and test account recovery. Neither transport is suitable as the sole durable answer record or as a general approval bypass. Prioritize local answer-file recovery, Telegram's one-receiver ownership, and durable reply routing before adding more providers.

## 5. Comparison table

Footprints below are dependency categories, except the explicitly measured-by-registry PTB wheel size. “Native” distinguishes client runtime from Docker's Linux environment. Facts and licenses are sourced in A1 and B1–B2; risk assessments are this report's judgments.

| Option | Two-way | Native macOS / Linux / Windows | Install footprint | Setup | Security model | Maintenance risk | License |
|---|---|---|---|---|---|---|---|
| Telegram stdlib | Yes | Yes / Yes / Yes | No new Python package | BotFather, token, private pairing | Cloud plaintext available to service and bot; TLS; sender allowlist | Low transport scope; own retry/state logic | Python runtime + original repository code |
| Telegram PTB 22.8 | Yes | Yes / Yes / Yes, Python >=3.10 | 769.4 kB wheel + HTTPX tree | Same Telegram steps | Same cloud/bot model | Maintained library; incompatible with stated 3.9 minimum | LGPL-3.0-only |
| signal-cli JVM | Yes | Upstream claims all three; per-architecture validation pending | JRE 25 + CLI + JNI + state | Install runtime; link QR or register; pair sender | E2EE to client; local decrypted state and keys | High protocol/update burden | GPLv3 |
| signal-cli native | Yes, experimental | Unverified / Linux download / unverified | Native executable and libraries | Same account setup | Same E2EE endpoint model | Experimental build plus protocol changes | GPLv3 |
| REST wrapper 0.101 | Yes | Container, not native client on desktop OSes | Docker/image/state; optional persistent JVM mode | Install Docker; mount state; link; secure local API | E2EE ends in container; API exposes decrypted content | Wrapper and underlying client updates | MIT wrapper + GPLv3 client |
| Presage | Yes at library level | Three-OS binary support unverified | Rust plus native dependencies and custom integration | Build/package client; link/register | E2EE client under your maintenance | High integration/packaging burden | AGPL-3.0 |
| libsignal directly | Not a ready channel | Platform libraries exist; full client missing | Full client engineering and build toolchain | Implement registration/network/storage | Cryptographic foundation, not complete bot security | External use unsupported | AGPLv3 |
| Semaphore/signald | Historical support; reject now | Daemon stack not validated | Python plus unmaintained daemon | Register/link through daemon | Unofficial client and local state | Unmaintained transport | AGPLv3+ framework |

## 6. Minimal Telegram reference code

Python 3.9 syntax and stdlib only. This is a **single-bot, single-question demonstration**, not the shared broker. Precondition: exactly one process owns the bot and all files below, no other answering channel writes this demo's answer directory, and the supplied directory is private and trusted. The production shared writer must add the cross-channel lock and schema validation described in C1.

The caller supplies already-sanitized text, safe opaque `question_id`, the original artifact hash, and configured numeric ids. State survives restart; uncertain send is deliberately refused rather than silently duplicating. The answer JSON shape is illustrative: integrate with the runner's actual schema before shipping. The code accepts buttons or a threaded free-text reply, rejects edited/nonprivate/unpaired replies, and checkpoints only after durable processing. It does not resume the runner itself.

```python
import json
import os
import re
import secrets
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


class APIError(Exception):
    def __init__(self, code, retry_after=0):
        self.code = code
        self.retry_after = retry_after
        super().__init__('Telegram API failure: %s' % code)


def api(token, method, **params):
    request = urllib.request.Request(
        'https://api.telegram.org/bot' + token + '/' + method,
        data=json.dumps(params).encode('utf-8'),
        headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        try:
            result = json.load(error)
        except (ValueError, OSError):
            raise APIError(error.code) from None
    except (OSError, urllib.error.URLError):
        raise APIError(0) from None  # Do not expose token-bearing URLs.
    if not result.get('ok'):
        raise APIError(result.get('error_code', 0),
                       result.get('parameters', {}).get('retry_after', 0))
    return result['result']


def atomic_json(path, value):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(dir=str(path.parent), prefix='.pending-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def exchange(token, user_id, chat_id, root, question_id, artifact_hash,
             text, options=('Proceed', 'Defer'), call=api):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', question_id):
        raise ValueError('Invalid opaque question id')
    if not text or len(text.encode('utf-16-le')) // 2 > 3500:
        raise ValueError('Question must contain 1 to 3500 UTF-16 units')
    if not options or len(options) > 8 or any(
            not isinstance(x, str) or not x or len(x) > 60 for x in options):
        raise ValueError('Supply 1 to 8 short option labels')
    root = Path(root)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    answers = root / 'answers'
    answers.mkdir(mode=0o700, exist_ok=True)
    state_path = root / 'telegram-state.json'
    answer_path = answers / (question_id + '.json')
    identity = [user_id, chat_id, question_id, artifact_hash, list(options)]
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding='utf-8'))
        if state['identity'] != identity:
            raise ValueError('State belongs to another question or identity')
        if state['phase'] != 'sent':
            raise RuntimeError('Uncertain prior send; reconcile manually')
    else:
        if call(token, 'getWebhookInfo').get('url'):
            raise RuntimeError('Webhook configured; refusing takeover')
        state = {'identity': identity, 'offset': 0, 'phase': 'sending',
                 'nonce': secrets.token_hex(12)}
        atomic_json(state_path, state)  # Crash/send timeout becomes uncertain.
        sent = call(token, 'sendMessage', chat_id=chat_id, text=text,
                    link_preview_options={'is_disabled': True},
                    reply_markup={'inline_keyboard': [[
                        {'text': label,
                         'callback_data': state['nonce'] + ':' + str(index)}
                    ] for index, label in enumerate(options)]})
        state.update(phase='sent', message_id=sent['message_id'])
        atomic_json(state_path, state)
    if answer_path.exists():
        return json.loads(answer_path.read_text(encoding='utf-8'))
    delay = 1
    while True:
        try:
            updates = call(token, 'getUpdates', offset=state['offset'],
                           timeout=25, allowed_updates=['message', 'callback_query'])
        except APIError as error:
            if error.code not in (0, 429) and error.code < 500:
                raise  # Includes 401, 403, 409.
            time.sleep(max(delay, error.retry_after))
            delay = min(30, delay * 2)
            continue
        delay = 1
        for update in updates:
            callback = update.get('callback_query')
            message = (callback.get('message', {}) if callback
                       else update.get('message', {}))
            sender = (callback.get('from', {}) if callback
                      else message.get('from', {}))
            chat = message.get('chat', {})
            valid = (sender.get('id') == user_id and not sender.get('is_bot')
                     and chat.get('id') == chat_id and chat.get('type') == 'private')
            answer = None
            if valid and callback and message.get('message_id') == state['message_id']:
                for index, label in enumerate(options):
                    if callback.get('data') == state['nonce'] + ':' + str(index):
                        answer = label
            elif valid and not callback:
                reply = message.get('reply_to_message', {})
                candidate = message.get('text')
                if (reply.get('message_id') == state['message_id']
                        and isinstance(candidate, str) and candidate.strip()
                        and len(candidate) <= 4096):
                    answer = candidate
            record = None
            if answer is not None:
                record = {'question_id': question_id, 'artifact_hash': artifact_hash,
                          'actor': 'human', 'answer': answer, 'channel': 'telegram',
                          'sender_id': user_id, 'chat_id': chat_id,
                          'provider_event_id': update['update_id'],
                          'answered_at': datetime.now(timezone.utc).isoformat()}
                atomic_json(answer_path, record)
            state['offset'] = update['update_id'] + 1
            atomic_json(state_path, state)
            if callback and valid:
                try:
                    call(token, 'answerCallbackQuery', callback_query_id=callback['id'])
                except APIError:
                    pass  # Receipt and cursor already durable.
            if record is not None:
                return record
```

**Verification:** the code was extracted and exercised locally with a fake Bot API, including authorized buttons, wrong sender/chat, unrelated messages, threaded text, answer persistence, restart, and uncertain-send refusal. No real bot message was sent. No live Telegram polling, Python 3.9 runtime, Windows/macOS execution, corporate proxy, or crash/power-loss experiment was run. `fsync` of the file plus atomic replacement prevents partial JSON visibility; full power-loss durability also requires platform-specific directory/volume guarantees. This demonstration's backoff omits jitter and its one-answer return leaves later updates unconfirmed for a future invocation. The production broker needs continuous multi-question processing, expiry/staleness checks, and journaled rejection reasons.

Actual local verification output (`python /tmp/verify_telegram_reference.py`):

```text
PASS: Python 3.9 syntax; button/text routing; sender/chat rejection; persistence; restart; hash mismatch; uncertain send refusal
```

## 7. Open risks and unknowns

- **Repository contract:** the prompt's per-question inbox is a design direction in `xjsc9k`, not proof of a stable shipped answer JSON schema. Integrate through one writer/reader contract, preserving `6kwd2e`'s original artifact hash and human provenance. Refuse stale answers at application time.
- **Versions:** live pages and moving branches may differ. PTB's checked package advertises Bot API 10.0 while Telegram's current API page is 10.3; the recommended endpoints are older stable primitives. Do not infer that newest APIs are required for this adapter.
- **Unverified primary material:** Semaphore's GitHub page could not be retrieved; its publisher-owned PyPI description and signald's own end-of-maintenance notice support exclusion. A Presage release cadence and reliable packaged Windows/macOS builds were not established. No exhaustive census of private or newly published clients is possible.
- **OS matrix:** for each supported Python/OS/CPU combination, test install footprint, native library load, credentials after logout/reboot, proxy/CA configuration, sleep/wake, multiple runner ownership, and clean shutdown. Test Telegram recovery before and after 24 hours offline.
- **Correctness:** kill between send and state save, answer publication and cursor save, broker and runner restarts, duplicate/out-of-order events, parallel channels, stale revisions, rejected senders, token rotation, directory relocation, and a second host sharing a token. Verify first-answer-wins under contention, not just a sequential fixture.
- **Signal:** test current linked-device policy against actual devices; dedicated-account replies versus same-account sync messages; CAPTCHA/challenges; key changes; missed subscriptions; offline queues; JVM/native memory; Windows process pipes; and wrapper version lag. No real Signal account was registered, linked, or messaged.
- **Terms and confidentiality:** Signal acceptable use remains unresolved. Telegram cannot meet end-to-end confidentiality requirements. Notification failure must leave the local question visible and answerable, never synthesize consent or mark the parked work complete.

## 8. Sources

All external sources below were checked on **2026-10-17**. “Current branch/page” means a moving document, not a pinned release. Links are primary project, publisher, or service documentation.

- [T1: Telegram Bot API][T1], page reports Bot API 10.3 dated 2026-08-24; update semantics, callback/reply objects, limits, HTTP methods.
- [T2: Telegram Bots FAQ][T2], current page; polling and rate guidance.
- [T3: python-telegram-bot PyPI][T3], 22.8 (2026-06-12); Python requirement, license, wheel size.
- [T4: aiogram PyPI][T4], current release dated 2026-08-26; Python range, async support, MIT license.
- [T5: pyTelegramBotAPI PyPI][T5], 4.37.0 (2026-09-21); maintenance and interface description.
- [T6: PTB published package metadata][T6], current package description; HTTPX and asyncio.
- [T7: aiogram pyproject][T7], current dev-3.x; dependency declarations.
- [T8: pyTelegramBotAPI pyproject][T8], current master; Python >=3.10, GPL2, requests/aiohttp.
- [T9: Telegram Bot API server source][T9], current master `Client::abort_long_poll` / `fail_query_conflict`; competing-poll 409 behavior.
- [T10: Telegram FAQ][T10], cloud versus Secret Chat encryption.
- [T11: Telegram privacy policy][T11], cloud-message and bot processing.
- [T12: Official bot tutorial][T12], account creation and initiation.
- [S1: signal-cli README][S1], current master; runtime/platform/account/update requirements and GPLv3.
- [S2: signal-cli 0.14.9 release][S2], 2026-10-07; recent development, linking and SSE changes.
- [S3: signal-cli-rest-api README][S3], current master; Docker, linking, execution modes.
- [S4: REST wrapper 0.101 release][S4], 2026-09-25; embedded client 0.14.8 and fixes.
- [S5: REST wrapper license][S5], current master, MIT.
- [S6: libsignal README][S6], current main; unsupported external use, bridges, build requirements, AGPLv3.
- [S7: Presage README][S7], current master; messaging/linking/storage and crypto dependency interaction.
- [S8: Presage repository][S8], current default branch; AGPL-3.0 license.
- [S9: Signal terms and privacy][S9], current page; acceptable-use restrictions and termination.
- [S10: Semaphore PyPI][S10], 0.17.0 (2023-12-17); signald requirement, AGPLv3+.
- [S11: signald project notice][S11], current page; no active maintenance, recommends signal-cli.
- [S12: Signal linked devices][S12], current page; primary phone 30-day connection, 45-day linked-device inactivity, five slots.
- [S13: signal-cli JSON-RPC manual][S13], current master; pipes/socket/HTTP receive modes and in-memory SSE replay.
- [P1: Python urllib.request][P1], Python 3.9.25 documentation; proxy discovery and HTTPS client.
- [P2: Python ssl][P2], Python 3.9.25 documentation; certificate verification and CA loading.
- [P3: keyring documentation][P3], current docs reporting 25.7.1 development version; OS backends and headless considerations.
- Local sources: research `xjsc9k`, spec `6kwd2e`, and originating prompt `bao493`, read from this checkout; these establish project intent, not external service guarantees.

[T1]: https://core.telegram.org/bots/api
[T2]: https://core.telegram.org/bots/faq
[T3]: https://pypi.org/project/python-telegram-bot/
[T4]: https://pypi.org/project/aiogram/
[T5]: https://pypi.org/project/pyTelegramBotAPI/
[T6]: https://pypi.org/pypi/python-telegram-bot/json
[T7]: https://github.com/aiogram/aiogram/blob/dev-3.x/pyproject.toml
[T8]: https://github.com/eternnoir/pyTelegramBotAPI/blob/master/pyproject.toml
[T9]: https://raw.githubusercontent.com/tdlib/telegram-bot-api/master/telegram-bot-api/Client.cpp
[T10]: https://telegram.org/faq
[T11]: https://telegram.org/privacy
[T12]: https://core.telegram.org/bots/tutorial
[S1]: https://github.com/AsamK/signal-cli/blob/master/README.md
[S2]: https://github.com/AsamK/signal-cli/releases/tag/v0.14.9
[S3]: https://raw.githubusercontent.com/bbernhard/signal-cli-rest-api/master/README.md
[S4]: https://github.com/bbernhard/signal-cli-rest-api/releases/tag/0.101
[S5]: https://raw.githubusercontent.com/bbernhard/signal-cli-rest-api/master/LICENSE
[S6]: https://raw.githubusercontent.com/signalapp/libsignal/main/README.md
[S7]: https://raw.githubusercontent.com/whisperfish/presage/master/README.md
[S8]: https://github.com/whisperfish/presage
[S9]: https://signal.org/legal/
[S10]: https://pypi.org/project/semaphore-bot/
[S11]: https://signald.org/
[S12]: https://support.signal.org/hc/en-us/articles/360007320551-Linked-Devices
[S13]: https://raw.githubusercontent.com/AsamK/signal-cli/master/man/signal-cli-jsonrpc.5.adoc
[P1]: https://docs.python.org/3.9/library/urllib.request.html
[P2]: https://docs.python.org/3.9/library/ssl.html
[P3]: https://keyring.readthedocs.io/en/latest/
