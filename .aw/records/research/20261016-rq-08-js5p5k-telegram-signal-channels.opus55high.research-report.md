---
id: js5p5k
created: 20261017
set: rq
order: 08
topic: [runner, questions, notifications, telegram, signal]
model: opus55high
kind: research-report
status: todo
outcome: none-yet
summary: Response to bao493 by opus55high: two-way Telegram and Signal question channels for aw runners on macOS, Linux and Windows
consumed-by: []
---

# Two-way Telegram and Signal question channels for `aw` runners (macOS, Linux, Windows)

Research performed 2026-10-17 by an OpenCode agent (Claude Opus) with live network access. Every
version, date and quotation below was fetched on 2026-10-17 from the primary source named in
Section 8 (PyPI JSON API, GitHub REST API, raw repository files, core.telegram.org, signal.org,
support.signal.org, docs.python.org). Nothing is from memory unless marked UNVERIFIED.

Codebase under discussion: https://github.com/fariello/agent-workflows (public).

Context note: the repository's spec `6kwd2e` was already amended on 2026-10-17 (R9, R10) to adopt a
standard-library Telegram adapter and defer Signal. This report was produced independently against
the research prompt; where it agrees or disagrees with that amendment it says so.

---

## 1. Summary

- **Telegram: SHIP.** Implement it with the standard library only (`urllib.request` + `json` + `ssl`),
  Bot API long polling via `getUpdates`, no webhook. Every maintained Python Telegram library now
  requires Python >= 3.10, which is above the package floor of 3.9, and the Bot API surface we need is
  five methods. Inline buttons for choices, `force_reply` plus reply-to matching for free text,
  numeric user id AND chat id allowlist.
- **Signal: DO NOT SHIP as a built-in channel now.** The only realistic route is `signal-cli` (Java 25,
  about 124 MB download, releases that may stop working after about three months). It runs natively on
  all three OSes but is heavy and fragile; other options are Docker-only (REST wrapper) or
  unsupported library-level work (libsignal, presage). Document it as "advanced, bring your own
  `signal-cli` daemon" and reach it later through a generic command hook, not a dedicated adapter.
- The reference Telegram code in Section 6 was RUN against a local fake Bot API server under Python
  3.9 and 3.14; it was NOT run against real Telegram.

---

## 2. Telegram

### A1. Transport and library choice

**Polling versus webhook.** The Bot API offers two mutually exclusive ways to receive updates:
`getUpdates` (long polling) and `setWebhook`. The docs state: "This method will not work if an
outgoing webhook is set up" and "Incoming updates are stored on the server until the bot receives
them either way, but they will not be kept longer than 24 hours." A webhook requires a public HTTPS
endpoint on ports 443, 80, 88 or 8443, which a workstation does not have. Long polling is outbound
HTTPS only. `getUpdates` takes `timeout` ("Timeout in seconds for long polling. Defaults to 0, i.e.
usual short polling. Should be positive, short polling should be used for testing purposes only."),
`offset`, `limit` (1 to 100) and `allowed_updates`. Current Bot API version on the page: 10.3
(August 24, 2026).

**Library comparison (PyPI and GitHub, checked 2026-10-17):**

| Option | Latest | Released | `requires_python` | Runtime deps | Model | License |
|---|---|---|---|---|---|---|
| stdlib (`urllib`, `json`, `ssl`) | n/a | n/a | any 3.x | none | sync | PSF |
| `python-telegram-bot` | 22.8 | 2026-06-12 | `>=3.10` | `httpx` (pulls `anyio`, `httpcore`, `certifi`, `idna`) | asyncio | LGPL-3.0-only (PyPI); GitHub API reports GPL-3.0 for the repo, the project's own PyPI metadata says LGPL-3.0-only |
| `aiogram` | 3.31.0 | 2026-08-26 | `>=3.10,<3.15` | `aiohttp`, `aiofiles`, `pydantic`, `magic-filter`, `certifi`, `typing-extensions` | asyncio | MIT |
| `pyTelegramBotAPI` | 4.37.0 | 2026-09-21 | `>=3.10` | `requests` and `aiohttp` (both mandatory) | sync or async | GPL-2.0 |
| `telethon` | 1.45.0 | 2026-09-10 | `>=3.5` | `pyaes`, `rsa` | asyncio, MTProto (user or bot) | MIT |
| `pyrogram` | 2.0.106 | 2023-04-30 | `~=3.7` | `pyaes`, `pysocks` | MTProto | LGPLv3; no release in 3.5 years, treat as unmaintained |

Observations:

- All three Bot API libraries are actively maintained (GitHub pushes within the last week), but all
  three have dropped Python 3.9. The last `python-telegram-bot` supporting 3.9 is 21.11.1
  (2025-03-01, `requires_python >=3.9`); pinning a 19-month-old release is worse than 200 lines of
  stdlib code.
- `aiogram` also caps Python at `<3.15`, which is a forward-compatibility risk for an optional extra.
- `pyTelegramBotAPI` is GPL-2.0 and pulls two HTTP stacks.
- Telethon/MTProto is the wrong tool: it adds crypto, a session file, and API id/hash registration
  for no benefit over the Bot API.
- The asyncio libraries would force an event loop into a sync runner, or a thread hosting a loop.

**Recommendation A1.** Standard library only, sync, in a thread of the runner. Five methods are
needed: `getMe`, `getWebhookInfo`, `sendMessage`, `getUpdates`, `answerCallbackQuery` (optionally
`editMessageReplyMarkup` to remove buttons after an answer). No optional extra is needed. This agrees
with `6kwd2e` R10.8(a).

### A2. Receiving the answer and mapping it to a question id

- **Multiple choice: inline keyboard (`callback_query`).** Each button carries `callback_data`,
  "1-64 bytes". Do not put the question id or the answer text in it. Put a random opaque token
  (`secrets.token_urlsafe(12)`, 16 characters) and keep a LOCAL map token -> (run dir, question id,
  option index, artifact hash). Reasons: the 64-byte cap, and callback data is client-supplied, so
  anything in it must be treated as untrusted; a random token that is not in the local map is simply
  rejected. The docs require acknowledging every press: "Telegram clients will display a progress bar
  until you call answerCallbackQuery. It is, therefore, necessary to react by calling
  answerCallbackQuery even if no notification to the user is needed."
- **Free text: `force_reply`.** "Upon receiving a message with this object, Telegram clients will
  display a reply interface to the user (act as if the user has selected the bot's message and tapped
  'Reply')." The incoming `Message` then carries `reply_to_message` ("For replies in the same chat and
  message thread, the original message"), whose `message_id` maps back to the question through a
  local message_id -> question id map. Note the docs say `reply_to_message` "may be omitted" when
  replying to an ephemeral message, so do not send questions as ephemeral messages.
- **Unmatched free text** (a message that is not a reply to a known question message): do not guess.
  Reply with a short help message listing open question ids, or accept an explicit `/answer <qid>
  <text>` command. Never map "the most recent question" implicitly; with several live runs that is a
  wrong-answer hazard.
- After an answer is recorded, edit the original message to remove its keyboard
  (`editMessageReplyMarkup`) so a stale button cannot be pressed again; the "first answer wins" rule in
  the shared writer is still the real guard.

**Recommendation A2.** Buttons with random local tokens for choices; `force_reply` + `reply_to_message`
for text; reject anything that does not resolve through the local maps; always
`answerCallbackQuery` with "Recorded" / "Already answered" / "Not accepted".

### A3. Polling correctness, concurrency, limits, formatting

- **Offset and delivery semantics.** "An update is considered confirmed as soon as getUpdates is
  called with an offset higher than its update_id." And: "In order to avoid getting duplicate updates,
  recalculate offset after each server response." So delivery is at-least-once: if the process dies
  after receiving updates but before the next call, they are re-delivered. Make processing idempotent
  (the answer writer refuses a second answer; `update_id` can be deduplicated), and persist the
  offset only AFTER each update in the batch has been written or rejected. That gives effectively
  exactly-once application on top of at-least-once delivery.
- **Retention.** Unconfirmed updates are kept at most 24 hours. Draining at runner start collects
  answers sent while no runner was live, as long as that was within 24 hours.
- **Two pollers on one token.** The official Bot API docs do not document this case (no "Conflict"
  text appears on the API page). In practice the server returns HTTP 409 with description
  "Conflict: terminated by other getUpdates request"; this is widely reported, for example
  python-telegram-bot issues #4499 (2024-09-25), #1143 and #3610. Treat 409 as "another poller owns
  this token": stop polling and report; do not retry in a tight loop, which just makes the two
  pollers kick each other. Whichever process is not polling can still SEND messages; sending has no
  such conflict.
- **Several concurrent runners on one machine.** Run exactly one receive loop per bot token per user,
  guarded by a user-level `filelock` (already a dependency). Every runner sends; only the lock holder
  polls, and it routes each update through a user-level registry (token/message id -> run dir +
  question id) into the correct run's `answers/`. When the holder exits, another live runner takes
  the lock. This matches `6kwd2e` R10.6.
- **Two machines on one token.** A per-user lock cannot span machines. Options: one bot per machine
  (simplest, recommended; BotFather bots are free), or accept that only one machine polls and the
  others are send-only. Detect the case by 409 and tell the user to create a bot per machine.
- **Long-poll timeout.** Use `timeout=50` seconds on the Bot API side and a socket timeout of about
  65 seconds on the client side so the HTTP read never times out before the server responds.
  UNVERIFIED: the server-side maximum `timeout`; the docs do not state a cap. 50 is a common,
  conservative value.
- **Rate limits** (Bots FAQ): "In a single chat, avoid sending more than one message per second. We
  may allow short bursts that go over this limit, but eventually you'll begin receiving 429 errors."
  On 429, the error carries `parameters.retry_after` ("the number of seconds left to wait before the
  request can be repeated"); honor it. Do not parse `error_code` too precisely: the docs say "its
  contents are subject to change in the future."
- **Message limits.** `sendMessage.text`: "1-4096 characters after entities parsing". Captions:
  1024. `callback_data`: 64 bytes. Truncate AFTER sanitizing.
- **Formatting pitfalls.** MarkdownV2 requires escaping `_ * [ ] ( ) ~ \` > # + - = | { } . !` "in all
  other places"; plan text and file paths are full of these and a single miss returns 400. HTML mode
  needs `<`, `>` and `&` escaped. Recommendation: send PLAIN TEXT (no `parse_mode`). If emphasis is
  ever wanted, use `entities` (explicit offsets in UTF-16 code units) rather than a parse mode.
- **IDs.** User and chat ids "may have more than 32 significant bits ... at most 52 significant
  bits"; Python ints are fine, but do not store them in a 32-bit field anywhere.

**Recommendation A3.** One lock-guarded poller per token per user, offset persisted after processing,
idempotent writer, 409 = stop and report, 429 = sleep `retry_after`, plain text only, `timeout=50`.

### A4. Security

- **Allowlist.** Accept an answer only if BOTH `from.id` equals the configured numeric user id AND
  `chat.id` equals the configured private chat id (for a private chat these are the same number).
  Never authorize by username: usernames are mutable and transferable. Drop and log everything else.
  Also restrict `allowed_updates` to `["message", "callback_query"]`.
- **Groups.** Disable group joins for the bot in BotFather (`/setjoingroups`), so the bot cannot be
  added to a group where other people could press buttons. The chat-id check is the real guard.
- **Discovering your own id safely.** Do not ask the user to paste their id from a third-party
  "what is my id" bot. Instead, during setup the CLI prints a one-time random phrase, the user sends it
  to their own bot, and the CLI reads `getUpdates`, finds the message whose text equals the phrase, and
  shows the detected `from.id`, first name and username for local confirmation. Someone else can only
  win that race if they know both the bot's username and the phrase within the setup window.
- **Token storage.** Order of preference:
  1. Environment variable `AW_TELEGRAM_TOKEN` (CI, containers, power users).
  2. A user-level config file under `AW_HOME`, mode 0600 on POSIX; on Windows the file should live
     under the user profile (default ACL is already user-only for `%APPDATA%`/`%LOCALAPPDATA%`;
     UNVERIFIED for every enterprise policy). Never tracked project config.
  3. Optional OS keychain via `keyring` 25.7.0 (`requires_python >=3.9`, MIT; backends: macOS
     Keychain, Windows Credential Manager via `pywin32-ctypes`, Linux Secret Service via
     `SecretStorage`/`jeepney`) as an OPTIONAL extra. Linux Secret Service is often absent on headless
     servers and SSH sessions, so keyring cannot be the only path.
  If the token leaks, BotFather `/token` regenerates it (docs: "If your existing token is compromised
  or you lost it for some reason, use the /token command to generate a new one."). Never log URLs:
  the token is in the request path (`https://api.telegram.org/bot<token>/METHOD`), so exception
  messages and proxy logs can contain it. Redact `bot\d+:[A-Za-z0-9_-]+` in any error you print.
- **What Telegram can read.** Bot chats are cloud chats. Telegram FAQ: "Messages in Secret Chats use
  client-client encryption, while Cloud Chats use client-server/server-client encryption and are
  stored encrypted in the Telegram Cloud." Secret chats are not available to bots (the Bot API has no
  secret-chat support). So: question text and answers are encrypted in transit, are stored on
  Telegram's servers, and are readable by Telegram (the operator holds the keys) and by anyone holding
  the bot token. The Privacy Policy (section 6) also notes data sent to a bot goes to that bot's
  developer, which here is the user themself. `protect_content: true` only blocks forwarding and saving
  in clients; it is not a confidentiality control.
- **Sanitize first.** Run the leak sanitizer before every send, then truncate. Terse mode default.

**Recommendation A4.** User id + chat id allowlist, phrase-based pairing, token from env or 0600 user
file (keyring optional), redact the token from errors, terse mode by default, and state plainly in
setup that Telegram can read bot chats.

### A5. Setup UX

Minimum human steps: (1) open @BotFather, `/newbot`, choose a name and username, copy the token;
(2) run `aw notify setup telegram`; (3) send the shown phrase to the new bot; (4) press a button and
reply to a test question.

What the CLI automates or verifies:

1. Show what will leave the machine and the encryption statement (A4). Require explicit consent.
2. Read the token with hidden input (`getpass`). Validate its shape, then call `getMe` (401 = bad
   token) and show the bot's username for confirmation.
3. Call `getWebhookInfo`. If `url` is non-empty, refuse (or offer `deleteWebhook`) because polling
   cannot work alongside a webhook.
4. Print a deep link `https://t.me/<bot_username>?start=<phrase>` (the user taps it, Telegram sends
   `/start <phrase>`), plus the plain phrase as a fallback. Long-poll up to about 5 minutes for it.
5. Show detected id, name, username; user confirms locally.
6. Send a test question with two buttons and a `force_reply` prompt; require a button press and a text
   reply; acknowledge both.
7. Save config (0600), set terse mode on, print `aw notify test` and `aw notify status`.
8. Optionally recommend BotFather `/setjoingroups` -> Disable.

**Recommendation A5.** Ship exactly this flow; it verifies token, webhook state, identity, both
answer paths and the sanitizer end to end in about two minutes.

### A6. Per-OS notes

- **Proxies.** `urllib.request` reads `<scheme>_proxy` environment variables on all OSes first, then
  "System Configuration for macOS and Windows Systems Registry for Windows" (docs.python.org). It does
  NOT do PAC files or WPAD, and has no built-in NTLM/Kerberos proxy authentication; behind such a
  corporate proxy the user must set `HTTPS_PROXY` (with credentials, or via a local proxy such as
  cntlm/px). Add a config key to set an explicit proxy URL. macOS caveat from the docs: `getproxies()`
  on macOS is unsafe in a process that later uses `os.fork()`; the runner spawns agents via
  subprocess (fork+exec), so consider resolving proxies once at startup or setting `no_proxy`
  explicitly if crashes appear. UNVERIFIED whether this bites the runner in practice.
- **TLS certificates.**
  - Windows: `ssl.create_default_context()` "loads CA certs from the CA and ROOT system stores", so
    corporate TLS-interception roots installed in Windows usually work.
  - macOS: python.org installers do not use the system keychain; until the user runs
    "Install Certificates.command" (or `certifi` is used) HTTPS can fail with
    `CERTIFICATE_VERIFY_FAILED`. Homebrew Python uses its own OpenSSL bundle. Corporate roots in the
    Keychain are invisible to OpenSSL either way.
  - Linux: uses the distro bundle; usually fine.
  - Mitigation: allow an explicit CA bundle path in config (`cafile`), honor `SSL_CERT_FILE`, and
    optionally use `truststore` (0.10.5, MIT) to use the OS trust store; NOTE `truststore` requires
    Python >= 3.10, so it can only be an opportunistic import, not a dependency.
- **Firewalls.** Only outbound TCP 443 to `api.telegram.org` is needed. Some networks and countries
  block Telegram; there is no in-band workaround beyond a proxy. A self-hosted local Bot API server
  exists (`telegram-bot-api`) but it still has to reach Telegram, so it does not help with blocking.
- **Sleep/wake and network changes.** A long poll in flight across sleep often hangs until the
  socket timeout, or returns `URLError`/`ConnectionResetError`. The client-side socket timeout
  (about 65 s) bounds the hang; catch `URLError`/`OSError`/`TimeoutError` broadly and back off with
  jitter (1 s doubling to 60 s). Wi-Fi changes behave the same way.
- **Windows console.** No special issue for HTTP; avoid printing emoji or non-ASCII to a legacy
  console without `errors="replace"`.

**Recommendation A6.** Stdlib with: optional `proxy` and `cafile` config keys, env-var proxies,
socket timeout greater than poll timeout, broad network exception handling with jittered backoff,
and an `aw notify status` that reports the last successful poll time.

---

## 3. Signal

### B1. Realistic ways to send and receive

| Option | What it is | Latest (checked 2026-10-17) | Health | Auth model | Fragility | License |
|---|---|---|---|---|---|---|
| `signal-cli` | Java CLI and daemon on a patched `libsignal-service-java` (Turasa fork) + native `libsignal-client` | v0.14.9, 2026-10-07; repo pushed 2026-10-14; ~5.0k stars | Active, frequent releases (0.14.6 Jul, 0.14.7 Aug, 0.14.8 Sep, 0.14.9 Oct 2026) | Register a number (SMS/voice, maybe CAPTCHA) OR link as a secondary device (`link`, QR); 0.14.9 added linking phone-numberless accounts | README: "signal-cli releases older than three months may not work correctly." Changelog has repeated "Adapt registration to signal server changes" | GPL-3.0 |
| `signal-cli-rest-api` | Go HTTP wrapper around signal-cli, Docker image | 0.101, 2026-09-25; pushed 2026-10-10; ~2.9k stars | Active | Same as signal-cli | Same, plus image cadence | MIT (wrapper) |
| `libsignal` | Signal's official Rust core with Java/Swift/TypeScript bindings | v0.105.1, 2026-10-15 | Very active | Protocol only; you would build the whole client and server API layer | README: "Use outside of Signal is unsupported ... subject to change without notice" | AGPL-3.0 |
| `presage` | Rust client library on `libsignal-service-rs` | Last tagged release 0.7.0, 2025-05-14; main pushed 2026-10-15; ~270 stars | Active on main, tags lag; README tells you to depend on git | Register or link as secondary | Tracks server changes on main only | AGPL-3.0 |
| `gurk-rs` | Terminal UI client built on presage | v0.10.2, 2026-10-12 | Active | Link | Inherits presage | AGPL-3.0 |
| `semaphore` (`semaphore-bot`) | Python bot framework over signald/signal-cli | 0.17.0, 2023-12-17; GitHub repo now returns 404 | Dead | n/a | n/a | AGPLv3+ |
| `signalbot` | Python bot framework over signal-cli-rest-api (json-rpc mode) | 2.1.0, 2026-10-02 (`signalbot-org/signalbot`) | Active | Via REST API | Inherits REST API | MIT; `requires_python >=3.11`, deps include `aiohttp`, `pydantic`, `apscheduler`, `websockets` |
| `pysignalclirestapi` | Thin REST client | 0.3.25, 2026-03-19 | Light | Via REST API | n/a | (no license metadata on PyPI) |
| signald | Former Go/Java daemon | Not re-checked; widely reported discontinued (UNVERIFIED in this session) | Treat as dead | n/a | n/a | n/a |

No official Signal bot API exists. Every option is a reverse-engineered or unsupported client of
Signal's private server API.

**Recommendation B1.** If Signal is ever supported, `signal-cli` in `daemon` mode is the only
reasonable backend; `signal-cli-rest-api` is an acceptable alternative for users who already run
Docker. Do not build on libsignal or presage (Rust toolchain, AGPL, unsupported), and do not depend on
`semaphore` or `signalbot`.

### B2. Native support per OS and install footprint

- **signal-cli JVM build**: README: binaries "should work on Linux, macOS and Windows"; requires "at
  least Java Runtime Environment (JRE) 25" (since 0.14.0, 2026-03-01: "Attention: Now requires Java
  25"); `libsignal-client` native libs "are bundled for x86_64 Linux (with recent enough glibc),
  Windows and MacOS". Other platforms (Linux ARM, for example Raspberry Pi) need a self-provided
  native lib. Download: `signal-cli-0.14.9.tar.gz` is 124.3 MB, plus a JRE 25 (typically 50 to
  200 MB depending on distribution; UNVERIFIED exact sizes). JRE 25 is new enough that many distro
  package managers do not ship it yet as the default Java (UNVERIFIED per distro); users will often
  need Adoptium/Temurin or similar.
- **signal-cli GraalVM native build**: Linux only in the release assets
  (`signal-cli-0.14.9-Linux-native.tar.gz`, 116.9 MB). No native macOS or Windows binary is published.
- **Native lib on Apple Silicon**: the README says "MacOS" without naming arm64. UNVERIFIED whether
  the bundled jar includes `aarch64` macOS; must be tested by hand.
- **signal-cli-rest-api**: Docker only. On macOS and Windows that means Docker Desktop (licensing
  terms apply to larger companies) or another VM-based runtime. Not native anywhere except Linux with
  Docker.
- **presage/gurk**: Rust; builds on all three in principle; requires a Rust toolchain or prebuilt
  binaries; not a library a Python package can sensibly depend on.

**Recommendation B2.** Signal is "natively possible" on all three OSes only via signal-cli JVM build
+ JRE 25 (about 200 to 300 MB total, UNVERIFIED exact), with the Apple Silicon and Linux ARM native
library cases needing hand verification.

### B3. Registration realities

- **Dedicated number (primary registration)**: needs a number that can receive SMS or a voice call;
  landlines work through the documented `--voice` flow after a first SMS attempt fails. "Registering
  may require solving a CAPTCHA challenge" (manual: open a Signal URL in a browser, copy the
  `signalcaptcha://` link). Registering a number "will unregister any existing client associated with
  the same number", so the user must NEVER register their personal number this way. A second number
  costs money or effort (VoIP numbers are sometimes rejected; UNVERIFIED current policy).
  `submitRateLimitChallenge` exists because sending can also hit CAPTCHA-gated rate limits.
- **Linking as a secondary device to the user's own account**: supported (`signal-cli link`, prints a
  QR code; JSON-RPC `startLink`/`finishLink`). Signal support (article updated 2026-09-22): "After
  linking a device, your phone has to come online at least once every 30 days. Otherwise, your linked
  devices will become unlinked. Linked devices will also become unlinked after 45 days of inactivity."
  "There is a limit of 5 linked devices per account." So a linked signal-cli that is offline for days
  keeps working on reconnect, but one idle for more than 45 days is unlinked and must be re-linked from
  the phone. signal-cli also says the protocol "expects that incoming messages are regularly received"
  for encryption to work efficiently; a daemon that is only up during runs should still be started
  periodically.
- **Linked mode has a UX problem for this use case**: when linked to the user's own account, the
  "bot" IS the user. A question sent from the user's account to the user lands in "Note to Self";
  the reply is a sync message (`syncMessage.sentMessage`), not an incoming `dataMessage` from another
  sender. Sender verification then means "message from my own account sent from device N", which is
  weaker and odd. A dedicated number gives a clean "bot contact" but needs the second number.

**Recommendation B3.** If built, require a DEDICATED number registered to signal-cli, and talk to the
user's personal number as a contact. Linking is workable but produces Note-to-Self semantics and a
weaker sender check.

### B4. How a Python CLI should talk to it

- **Subprocess per message** (`signal-cli -a ACC send ...` / `receive`): JVM start per call (slow,
  seconds), and `receive` competes with any daemon. Not recommended.
- **Daemon + JSON-RPC (recommended)**: `signal-cli -a ACC daemon --tcp localhost:7583` (or `--socket`
  for a UNIX socket at `$XDG_RUNTIME_DIR/signal-cli/socket`, or `--http localhost:8080`). Line-delimited
  JSON-RPC 2.0; incoming messages arrive as `receive` notifications. Use `--receive-mode=manual` and
  call `subscribeReceive` so messages are not consumed before the client attaches ("In order to not
  miss messages, automatic receiving of messages can be disabled with the --receive-mode=manual
  parameter."). The `--http` mode exposes `POST /api/v1/rpc` and an SSE stream `GET /api/v1/events`;
  since 0.14.9 it keeps the last 1000 events in memory and supports `Last-Event-ID` replay. All of this
  is stdlib-reachable from Python (`socket` + `json`, or `urllib` for HTTP; SSE is a simple line
  protocol). On Windows, prefer `--tcp` or `--http` bound to localhost (UNIX sockets on Windows exist
  in Java 16+ and Windows 10+ but are less tested; UNVERIFIED).
- **D-Bus**: Linux-only in practice; skip.
- **REST wrapper**: same semantics over HTTP, Docker only.
- **Mapping replies**: Signal supports quoted replies; the incoming `dataMessage` carries a `quote`
  with the original message's `timestamp` (signal-cli JSON; field names per the JSON schemas in the
  release assets; UNVERIFIED field-by-field in this session). Map `send` result `timestamp` ->
  question id, then match `quote.id`. There are no buttons; multiple choice must be "reply with 1, 2
  or 3". Signal polls exist in recent clients but signal-cli support was not verified (UNVERIFIED).
- **Restricting senders**: compare `envelope.sourceUuid` (ACI) against the configured ACI, not the
  phone number (numbers can be hidden or changed); also require `sourceDevice` checks in linked
  mode. Keep `trust-new-identities` at the default `on-first-use` and alert on identity-key change.
- **Security of the local endpoint**: the JSON-RPC TCP/HTTP endpoint has no authentication. Any
  local process can send as the account. Bind to localhost only; on multi-user machines prefer the
  UNIX socket with directory permissions.

**Recommendation B4.** If built: user-managed `signal-cli daemon --http 127.0.0.1:<port>
--receive-mode=manual`, stdlib HTTP client, SSE receive with `Last-Event-ID` persisted, quote
timestamp mapping, ACI allowlist. `aw` should not install or manage Java or signal-cli itself.

### B5. Terms of service and ban risk

Signal Terms of Service (signal.org/legal, "Effective as of May 25, 2018 Updated May 25, 2018"; the
page is stale but current): users must not use the Services in ways that "involve sending illegal or
impermissible communications such as bulk messaging, auto-messaging, and auto-dialing", nor "create
accounts for our Services through unauthorized or automated means", nor "access ... our Services in
unauthorized manners". Third-party clients are not authorized clients. Low-volume self-notification
(a few messages a day to oneself) is a common, tolerated use of signal-cli (its README says it is
"primarily intended to be used on servers to notify admins of important events"), but the ToS text
plainly covers "auto-messaging", and enforcement is at Signal's discretion: "If we disable your
account for a violation of our Terms, you will not create another account without our permission."
No public evidence was found in this session of bans for low-volume signal-cli notification use
(absence of evidence, not evidence). The risk is asymmetric: linking to a PERSONAL account puts the
user's primary messenger at stake.

**Recommendation B5.** Never automate the user's personal account by default. If Signal is offered,
document the ToS clause verbatim and recommend a dedicated number.

### B6. Verdict

Signal is technically possible on all three OSes via signal-cli + JRE 25, but it is not practical as
a built-in optional channel for this tool: about 200+ MB of Java dependencies, a Java version many
systems do not have, a second phone number for a clean setup, a three-month "update or break"
treadmill that `aw` would inherit as support burden, no buttons, an unauthenticated local endpoint,
and explicit ToS language against auto-messaging. Recommendation: do not ship a Signal adapter.
Document "Signal: advanced, user-managed `signal-cli` daemon (Linux/macOS/Windows with Java 25, or
Linux/Docker via signal-cli-rest-api)" and support it later, if demand appears, through the generic
command hook (notify) and possibly a small JSON-RPC receive adapter. This agrees with `6kwd2e`
R10.10.

---

## 4. Cross-cutting

### C1. Adapter interface

One shape, matching `6kwd2e` R10.1 with two additions (an explicit cursor type and an ack hook):

```python
class Channel(Protocol):
    name: str                                   # "telegram", "hook", ...
    def capabilities(self) -> Caps: ...          # notify, answer, buttons, max_text, max_choice_label
    def send(self, q: OutboundQuestion, mode: Literal["terse", "full"]) -> Receipt: ...
    def receive(self, cursor: Cursor, deadline: float) -> tuple[list[InboundEvent], Cursor]: ...
    def verify(self, ev: InboundEvent) -> Optional[str]: ...   # verified sender id or None
    def ack(self, ev: InboundEvent, outcome: Literal["recorded", "already", "rejected"]) -> None: ...
    def health(self) -> Health: ...
```

- `OutboundQuestion` is built AFTER sanitizing and carries only what may leave the machine. In terse
  mode `send` receives a batch summary ("run R: N questions waiting; answer with aw runs answer R"),
  no content, no buttons.
- `Receipt` contains channel message ids and the random option tokens, which the core stores in the
  user-level registry (channel message id/token -> run dir, question id, option index, artifact
  hash). The registry, not the adapter, owns routing.
- `InboundEvent` = (channel event id, raw sender, chat/conversation id, reply-to reference or token,
  text). The core resolves it via the registry, calls `verify`, and passes it to the ONE shared
  answer writer (R9.2: lock, first answer wins, atomic write, ledger entry). Adapters never touch
  `answers/`.
- `Cursor` is opaque, persisted by the core after the batch is handled (Telegram: offset; Signal SSE:
  Last-Event-ID; ntfy: last message id).
- Idempotency: the core deduplicates by (channel, event id) and the writer refuses a second answer.
- Notify-only channels (generic webhook, command hook, Apprise) implement `send` and `health` only.

### C2. Where the receive loop lives

| Option | macOS | Linux | Windows | Verdict |
|---|---|---|---|---|
| A thread in every runner | 409 fights between runners on one token | same | same | No |
| A thread in ONE live runner, chosen by a user-level `filelock`; others send only; takeover on exit; drain at start | works | works | works (filelock is cross-platform) | **Recommended** |
| Foreground `aw notify listen` | works | works | works | Recommended companion, for answering a finished run |
| Per-user background service | launchd agent plist | systemd user unit (needs lingering for logged-out use) | Task Scheduler or Startup entry; no clean user-service model | Not now: three installers, three uninstallers, a process that outlives the work and a long-lived token holder |

Telegram's 24-hour retention covers the gap between runs: the next runner's start-time drain
collects answers sent while nothing was live. The only loss case is more than 24 hours with no live
runner and no `aw notify listen`, which is acceptable and should be documented.

### C3. Reasons not to build

- **Telegram**: no blocking reason. Real costs: content goes to a third party that can read it
  (mitigated by sanitizer and terse default); a channel answer becomes an agent instruction, so sender
  verification bugs are security bugs; token-in-URL leaks via logs; Telegram is blocked on some
  networks. Each has a mitigation above.
- **Signal**: support burden (Java 25, three-month expiry), ToS exposure, no buttons, a second phone
  number, and an unauthenticated local daemon. These outweigh the benefit for an optional channel.
- **General**: if most users will only want "tell me something is waiting", a notify-only generic
  hook (ntfy, Apprise, Teams/Google Chat webhooks) plus `aw runs answer` delivers most of the value
  with no answer-path attack surface. Build that first or alongside Telegram.

---

## 5. Comparison table

| Option | Two-way | macOS native | Linux native | Windows native | Install footprint | Setup steps | Security model | Maintenance risk | License |
|---|---|---|---|---|---|---|---|---|---|
| Telegram, stdlib `urllib` | Yes, buttons + text | Yes | Yes | Yes | 0 deps | BotFather token, send pairing phrase, test | TLS to Telegram; Telegram can read; token = full control; user id + chat id allowlist | Low; Bot API is versioned and backward compatible in practice; code is ours | n/a (our code) |
| Telegram, `python-telegram-bot` 22.8 | Yes | Yes | Yes | Yes | `httpx` + 4 transitive; Python >= 3.10 | Same | Same | Low for the library; HIGH fit risk (drops 3.9, asyncio) | LGPL-3.0-only |
| Signal, `signal-cli` daemon (JVM) | Yes, text only (quote replies) | Yes, JRE 25; arm64 native lib UNVERIFIED | Yes, JRE 25 or GraalVM native (x86_64) | Yes, JRE 25 | ~124 MB + JRE 25 | Second number + SMS/voice + maybe CAPTCHA, or QR link; run daemon; configure ACI | E2E encrypted Signal protocol; local JSON-RPC endpoint unauthenticated; ACI allowlist | HIGH: releases older than ~3 months may break; ToS exposure | GPL-3.0 |
| Signal, `signal-cli-rest-api` | Yes, text only | Docker Desktop only | Docker | Docker Desktop only | Docker + image (contains signal-cli + JRE) | Same plus Docker | Same; HTTP endpoint unauthenticated | HIGH (inherits signal-cli) | MIT (wrapper), GPL-3.0 inside |
| Signal, presage / libsignal | Yes in principle | Build from source | Build from source | Build from source | Rust toolchain or bespoke binary | Same plus build | Same | VERY HIGH: unsupported APIs, git-only deps | AGPL-3.0 |

---

## 6. Minimal reference code (Telegram, Python 3.9+, standard library only)

Status: RUN on 2026-10-17 against a local fake Bot API HTTP server (see test below) under Python 3.9
and Python 3.14.6. It correctly rejected a callback from a non-allowlisted user, recorded a button
answer, reported a duplicate press as "Already answered", recorded a free-text reply-to answer,
ignored a free-text message that was not a reply, and returned the next offset. NOT run against real
`api.telegram.org`. Production code must also: hold a `filelock` around check-and-rename (the shared
writer, R9.2), persist the token/message registry, sanitize before sending, log rejected events,
redact the token from exceptions, and remove keyboards after an answer.

```python
"""Minimal Telegram two-way question channel, Python 3.9+, standard library only."""
import json
import os
import secrets
import ssl
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

API = os.environ.get("AW_TELEGRAM_API", "https://api.telegram.org")


class TelegramError(Exception):
    def __init__(self, code, description, retry_after=None):
        super().__init__(f"{code}: {description}")
        self.code, self.retry_after = code, retry_after


def call(token, method, params, timeout=10):
    """POST a JSON body to one Bot API method; return `result` or raise TelegramError."""
    req = urllib.request.Request(
        f"{API}/bot{token}/{method}",
        data=json.dumps(params).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:  # 4xx/5xx still carry a JSON body
        try:
            body = json.loads(e.read().decode("utf-8"))
        except ValueError:
            raise TelegramError(e.code, e.reason) from None
    if not body.get("ok"):
        ra = (body.get("parameters") or {}).get("retry_after")
        raise TelegramError(body.get("error_code"), body.get("description"), ra)
    return body["result"]


def atomic_write_json(path, obj):
    """Write obj to path via temp file in the same dir + fsync + rename. Refuse to overwrite."""
    path = Path(path)
    if path.exists():
        return False  # first answer wins
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        if path.exists():  # re-check; real code holds a filelock across check+rename
            os.unlink(tmp)
            return False
        os.replace(tmp, str(path))
        return True
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def send_question(token, chat_id, question, registry):
    """Send one question. `registry` maps random tokens and message ids to local state."""
    text = f"[{question['run_id']}] {question['text']}"[:4096]  # plain text, no parse_mode
    buttons = []
    for i, label in enumerate(question.get("options") or []):
        tok = secrets.token_urlsafe(12)  # 16 chars, well under the 64-byte callback_data cap
        registry["tokens"][tok] = {"qid": question["question_id"], "choice": i, "label": label}
        buttons.append([{"text": label[:64], "callback_data": tok}])
    params = {"chat_id": chat_id, "text": text}
    if buttons:
        params["reply_markup"] = {"inline_keyboard": buttons}
    else:
        params["reply_markup"] = {"force_reply": True, "input_field_placeholder": "Your answer"}
    msg = call(token, "sendMessage", params)
    registry["messages"][str(msg["message_id"])] = question["question_id"]
    return msg["message_id"]


def poll_once(token, cfg, registry, questions, answers_dir, offset, long_poll=50):
    """One getUpdates round. Returns the next offset. Persist it only after this returns."""
    updates = call(
        token,
        "getUpdates",
        {"offset": offset, "timeout": long_poll, "allowed_updates": ["message", "callback_query"]},
        timeout=long_poll + 15,
    )
    for upd in updates:
        offset = max(offset, upd["update_id"] + 1)
        cq, msg = upd.get("callback_query"), upd.get("message")
        if cq:
            sender = cq["from"]["id"]
            chat = ((cq.get("message") or {}).get("chat") or {}).get("id")
            ok = sender == cfg["user_id"] and chat == cfg["chat_id"]
            hit = registry["tokens"].get(cq.get("data") or "") if ok else None
            note = "Not accepted"
            if hit and hit["qid"] in questions:
                wrote = atomic_write_json(
                    Path(answers_dir) / f"{hit['qid']}.json",
                    _answer(hit["qid"], hit["label"], hit["choice"], sender, questions[hit["qid"]]),
                )
                note = "Recorded" if wrote else "Already answered"
            call(token, "answerCallbackQuery", {"callback_query_id": cq["id"], "text": note})
        elif msg:
            sender = (msg.get("from") or {}).get("id")
            if sender != cfg["user_id"] or msg["chat"]["id"] != cfg["chat_id"]:
                continue  # drop and (in real code) log
            parent = msg.get("reply_to_message") or {}
            qid = registry["messages"].get(str(parent.get("message_id")))
            if qid in questions and msg.get("text"):
                wrote = atomic_write_json(
                    Path(answers_dir) / f"{qid}.json",
                    _answer(qid, msg["text"], None, sender, questions[qid]),
                )
                call(token, "sendMessage", {
                    "chat_id": cfg["chat_id"],
                    "text": "Recorded" if wrote else "Already answered",
                    "reply_parameters": {"message_id": msg["message_id"]},
                })
    return offset


def _answer(qid, text, choice, sender, question):
    return {
        "question_id": qid, "answer": text, "choice": choice, "actor": "human",
        "channel": "telegram", "sender": f"telegram:{sender}",
        "artifact_hash": question.get("artifact_hash"),
        "answered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def receive_loop(token, cfg, registry, questions, answers_dir, load_offset, save_offset, stop):
    """Backoff with jitter; honor retry_after; stop on 401/409 instead of spinning."""
    offset, delay = load_offset(), 1.0
    while not stop():
        try:
            offset = poll_once(token, cfg, registry, questions, answers_dir, offset)
            save_offset(offset)
            delay = 1.0
        except TelegramError as e:
            if e.code in (401, 409):
                raise  # bad token, or another poller holds the token
            time.sleep(e.retry_after or delay)
            delay = min(delay * 2, 60)
        except (urllib.error.URLError, OSError, ValueError):  # network, DNS, sleep/wake, bad JSON
            time.sleep(delay + secrets.randbelow(1000) / 1000)
            delay = min(delay * 2, 60)
```

Known simplification: `poll_once` updates `offset` per update but only returns it at the end; if an
exception occurs mid-batch the whole batch is re-delivered, which is safe because the writer refuses
duplicates. `receive_loop` was not exercised in the test (only `poll_once` and `send_question`).

Observed output of the fake-server test (Python 3.14.6; Python 3.9 produced the same first lines):

```
next offset 15
q1 {'question_id': 'q1', 'answer': 'B', 'choice': 1, 'actor': 'human', 'channel': 'telegram', 'sender': 'telegram:42', 'artifact_hash': 'h1', 'answered_at': '2026-10-17T04:28:44Z'}
q2 {'question_id': 'q2', 'answer': 'use plan X', 'choice': None, 'actor': 'human', 'channel': 'telegram', 'sender': 'telegram:42', 'artifact_hash': 'h2', 'answered_at': '2026-10-17T04:28:44Z'}
files ['q1.json', 'q2.json']
callback notes ['Not accepted', 'Recorded', 'Already answered']
first send {'chat_id': 42, 'text': '[r1] Pick one', 'reply_markup': {'inline_keyboard': [[{'text': 'A', 'callback_data': 'GlqGniZT34QN246Q'}], [{'text': 'B', 'callback_data': 'BPmRnPbTCZwKMNH5'}]]}}
```

---

## 7. Open risks and unknowns

Could not verify in this session:

- The exact Telegram 409 response body and whether it is raised to the OLDER or NEWER poller in every
  case (only community issue reports; not in the official docs).
- The server-side maximum for `getUpdates` `timeout`.
- Whether Telegram ever delivers a `reply_to_message` for a `force_reply` answer typed in a client
  that ignores force-reply (desktop web clients). Test on iOS, Android, Desktop, Web.
- signal-cli on macOS arm64 and Windows end to end; whether the bundled `libsignal-client` covers
  `aarch64-apple-darwin`; JRE 25 availability per Linux distro; total disk footprint.
- signal-cli JSON field names for quoted replies (`quote.id`) and poll support.
- Status of signald (not re-checked).
- Current Signal enforcement against low-volume automated self-notification.

Hand tests before shipping Telegram, on each of macOS (python.org installer AND Homebrew), Linux, and
Windows 10/11:

1. Setup flow end to end with a fresh bot, including a deliberately wrong token (401) and a bot with a
   webhook set.
2. HTTPS behind an authenticating corporate proxy via `HTTPS_PROXY`, and behind TLS interception
   with a custom `cafile`.
3. macOS python.org Python before running "Install Certificates.command" (expect a clear error).
4. Laptop sleep for 10+ minutes mid long poll; Wi-Fi switch; VPN on/off. Expect recovery within one
   backoff cycle and no duplicate answers.
5. Two runners on one machine (lock handover when the poller exits) and two machines on one token
   (409 is reported, not looped).
6. Answer sent while no runner is live, collected by the next runner within 24 hours.
7. Spoofing: a second Telegram account messages and presses forwarded buttons; nothing is written.
8. Double-tap a button and answer the same question from `aw runs answer` and Telegram at once: one
   answer, the other reported "already answered".
9. Message length: a question longer than 4096 characters after sanitizing; non-BMP characters
   (emoji) near the truncation boundary.
10. Confirm no token appears in any log, exception, or `aw runs` output.

---

## 8. Sources (all fetched 2026-10-17)

Telegram:
- Telegram Bot API reference, Bot API 10.3 (August 24, 2026): https://core.telegram.org/bots/api
  (getUpdates, offset/confirmation, 24-hour retention, setWebhook/deleteWebhook/getWebhookInfo,
  InlineKeyboardButton.callback_data 1-64 bytes, answerCallbackQuery note, ForceReply,
  Message.reply_to_message, sendMessage text 1-4096, MarkdownV2/HTML escaping, ResponseParameters
  retry_after, error_code caveat, id bit-width note, local Bot API server).
- Telegram Bots FAQ: https://core.telegram.org/bots/faq (one message per second per chat, 429,
  20/min in groups, 30/s broadcast; what messages a bot receives).
- Telegram bot features: https://core.telegram.org/bots/features (privacy mode, BotFather `/token`,
  `/setjoingroups`, `/setprivacy`).
- Telegram FAQ: https://telegram.org/faq (Secret Chats client-client encryption vs Cloud Chats
  client-server/server-client encryption; "Are bots safe?").
- Telegram Privacy Policy, section 6 "Bot Messages": https://telegram.org/privacy
- python-telegram-bot issues on 409 Conflict: #4499 (2024-09-25), #1143 (2018-06-22), #3610
  (2023-03-20), https://github.com/python-telegram-bot/python-telegram-bot/issues
- PyPI JSON API: python-telegram-bot 22.8 (2026-06-12, >=3.10, LGPL-3.0-only), 21.11.1 (2025-03-01,
  >=3.9); aiogram 3.31.0 (2026-08-26, >=3.10,<3.15, MIT); pyTelegramBotAPI 4.37.0 (2026-09-21,
  >=3.10, GPL2); telethon 1.45.0 (2026-09-10, MIT); pyrogram 2.0.106 (2023-04-30); httpx 0.28.1;
  keyring 25.7.0 (2025-11-16, >=3.9, MIT); truststore 0.10.5 (>=3.10, MIT); apprise 2.0.1
  (2026-10-03, >=3.9, BSD-2-Clause).
- GitHub REST API repo metadata (pushed_at, license, latest release) for python-telegram-bot,
  aiogram, pyTelegramBotAPI, apprise, keyring.

Signal:
- signal-cli README (master): https://github.com/AsamK/signal-cli (JRE 25, bundled native libs,
  three-month expiry warning, link/register/CAPTCHA, regular receive hint).
- signal-cli CHANGELOG (0.14.0 requires Java 25, 2026-03-01; 0.14.6 to 0.14.9 dates; "Adapt
  registration to signal server changes").
- signal-cli v0.14.9 release (2026-10-07) and asset sizes, GitHub releases API.
- signal-cli man pages: `man/signal-cli.1.adoc` (daemon --socket/--tcp/--http, --receive-mode,
  submitRateLimitChallenge), `man/signal-cli-jsonrpc.5.adoc` (jsonRpc, subscribeReceive,
  startLink/finishLink, SSE events with Last-Event-ID, 1000 kept events).
- signal-cli-rest-api README and release 0.101 (2026-09-25):
  https://github.com/bbernhard/signal-cli-rest-api (normal/native/json-rpc/json-rpc-native modes,
  AUTO_RECEIVE_SCHEDULE warning).
- libsignal README and release v0.105.1 (2026-10-15): https://github.com/signalapp/libsignal ("Use
  outside of Signal is unsupported").
- presage README, latest release 0.7.0 (2025-05-14): https://github.com/whisperfish/presage
- gurk-rs release v0.10.2 (2026-10-12): https://github.com/boxdot/gurk-rs
- semaphore-bot PyPI 0.17.0 (2023-12-17); its GitHub repo `lwesterhof/semaphore` returned 404.
- signalbot PyPI 2.1.0 (2026-10-02, >=3.11, MIT), repo `signalbot-org/signalbot` (pushed
  2026-10-13).
- pysignalclirestapi PyPI 0.3.25 (2026-03-19).
- Signal Terms of Service: https://signal.org/legal/ (Effective/Updated May 25, 2018).
- Signal Support, "Linked Devices" (updated 2026-09-22):
  https://support.signal.org/hc/en-us/articles/360007320551 (30-day phone check-in, 45-day
  inactivity unlink, 5 device limit).

Python and repository:
- `urllib.request` docs (proxy discovery from env, macOS System Configuration, Windows Registry;
  macOS fork warning): https://docs.python.org/3/library/urllib.request.html
- `ssl` docs (`load_default_certs` on Windows loads CA and ROOT stores):
  https://docs.python.org/3/library/ssl.html
- CPython macOS installer ReadMe ("Install Certificates" command), cpython 3.13 branch.
- Repository spec `6kwd2e` (R9, R10, amended 2026-10-17) and research note `xjsc9k` in
  https://github.com/fariello/agent-workflows under `.aw/records/`.

Source disagreements noted: python-telegram-bot's license is LGPL-3.0-only per its PyPI metadata,
while GitHub's license detector reports GPL-3.0 for the repository (LGPL-3.0 text references the
GPL; PyPI is authoritative for the distributed package). The Telegram 409 behavior is undocumented
officially and rests on community reports. Signal's ToS page has not been updated since 2018.
