# Notifications and Remote Question Answering

The `aw notify` command family provides mobile notifications and remote answer routing for long-running workflows and unattended runs. It allows operators to receive alerts when runs complete, fail, or pause for human questions, and to answer those questions directly from a chat client or via fallback CLI tools.

## Channel Overview

The framework supports three notification channel types:

1. **Telegram**: Two-way interactive channel using the standard Telegram Bot API. Supports inline multi-choice option buttons, free-text threaded replies, and sender verification.
2. **Webhook**: Outbound push notifications delivering JSON or plain text to webhook endpoints (such as ntfy, Microsoft Teams Workflows, or Google Chat).
3. **Command Hook**: Outbound notifications executed by spawning a local subprocess with notification JSON delivered on standard input.

## Privacy and Data Governance: What Leaves the Machine

Notification content is subject to strict data governance and leak sanitization:

- **Secrets and Configuration**: Channel secrets (bot tokens, chat IDs, webhook URLs) are stored exclusively in the user-level configuration file (`notify.json` under your `AW_HOME` directory, mode 0600 on POSIX). Secrets are never committed to repository tracking files.
- **Terse Mode (Default)**: In terse mode, notifications contain only the run identifier, the count of open questions, and the local CLI command to answer them (`aw runs answer <run-id>`). No question text, options, code snippets, or prompt details leave the machine.
- **Full Mode**: When opted into full mode (`--full`), notifications include sanitized question text and choices.
- **Outbound Sanitizer**: Before any notification payload leaves the machine, it passes through the outbound leak sanitizer:
  - ANSI color and terminal control sequences are stripped.
  - Home directory paths and usernames are rewritten or redacted.
  - Absolute system paths are replaced.
  - Repository leak rulesets scan for private tokens, session identifiers, and maintainer handles.
- **Transport Security**: Telegram traffic and webhook deliveries require HTTPS on non-loopback destinations. Bot chats on Telegram servers are not end-to-end encrypted; Telegram infrastructure processes bot messages.

## Channel Setup

### Telegram Setup

Telegram setup is an interactive wizard that pairs your bot token with your personal Telegram account and verifies two-way communication before saving configuration:

```sh
aw notify setup telegram
```

To configure in full mode instead of terse:

```sh
aw notify setup telegram --full
```

Setup steps:
1. Displays the privacy notice and explains data handling.
2. Reads your bot token (generated via `@BotFather`) with hidden input, or from `AW_NOTIFY_TELEGRAM_TOKEN`.
3. Verifies the token using `getMe`.
4. Checks `getWebhookInfo` to verify that no webhook is active. If a webhook is set, offers `deleteWebhook` (polling cannot run beside an active webhook).
5. Acquires the local receiver lock to ensure setup does not race another poller on the same bot token.
6. Generates an 8-character one-time pairing phrase and displays a link (`https://t.me/<bot_username>?start=<phrase>`).
7. Waits for a private message from your Telegram client containing the phrase.
8. Displays the detected name, numeric user ID, and chat ID, requiring explicit confirmation.
9. Sends a test question with interactive buttons and a reply prompt, requiring one button click and one threaded text reply. Both are acknowledged.
10. Saves configuration with mode 0600 to `notify.json`.

### Webhook Setup

The generic webhook channel can deliver notifications to services such as ntfy, Microsoft Teams Workflows, and Google Chat:

```sh
aw notify setup webhook --url-stdin --format aw
```

To avoid exposing webhook URLs in shell history, prefer passing the URL via `--url-stdin` or the `AW_NOTIFY_WEBHOOK_URL` environment variable:

```sh
echo "https://ntfy.sh/my-secret-topic" | aw notify setup webhook --url-stdin --format ntfy
```

Supported webhook formats:
- `aw`: Standard `aw.notify/v1` JSON envelope containing structured batch metadata and question lists.
- `text`: Simple JSON object containing `{"text": "..."}` compatible with Microsoft Teams Workflows and Google Chat incoming webhooks.
- `ntfy`: Raw text payload with `Title` and `Tags` HTTP headers suited for ntfy.sh topics.

### Command Hook Setup

A command hook runs a local command line, piping the `aw.notify/v1` JSON payload to standard input:

```sh
aw notify setup command -- /usr/local/bin/my-alert-script --channel ops
```

## Answer Verification and One-Bot-Per-Machine Principle

Telegram updates are validated under strict rules:
- **Sender Verification**: Inbound updates are accepted only when the sender's numeric user ID and private chat ID match the paired user configuration. Updates from unconfigured users, bots, or group chats are dropped and logged, never applied to questions.
- **Message Correlation**: Free-text replies are accepted only when sent as a direct reply to the bot's question message (`reply_to_message`). Uncorrelated messages are rejected.
- **One Bot Per Machine**: Telegram's Bot API allows only one active `getUpdates` poller per bot token. Simultaneous pollers receive `HTTP 409 Conflict`. Run exactly one receiver per bot token per machine.

## Operational Commands

### Checking Channel Status

To inspect active channels, configuration sources, mode, policy ceiling, lock status, and last event:

```sh
aw notify status
```

Machine output is available via `--agent` or `--json`.

### Testing Delivery

To send a test notification across all active channels:

```sh
aw notify test
```

To test a specific channel:

```sh
aw notify test telegram
aw notify test webhook
aw notify test command
```

For Telegram, the test command sends a test message with an inline button and waits up to 2 minutes for a button confirmation from the paired user ID.

### Disabling a Channel

To disable a channel without removing credentials:

```sh
aw notify disable telegram
aw notify disable webhook
aw notify disable command
```

If a channel is configured via an environment variable, `aw notify disable` instructs you to unset the corresponding environment variable.

### Answering Questions From Finished Runs: aw notify listen

When a run is executed without an active background receiver (or after a run has finished while questions remain open), run `aw notify listen` in the foreground:

```sh
aw notify listen
```

The listener acquires the per-bot receiver lock, long-polls Telegram for updates, and routes answers to matching run directories. It prints one log line for each recorded or rejected answer, and shuts down cleanly on Ctrl-C or SIGTERM (exit code 0). If another process holds the receiver lock, `listen` reports the holder PID and exits 1.

### Terminal Fallback: aw runs answer

If you are at your computer or remote channels are unavailable, the local CLI command `aw runs answer` is always available to view and answer open questions directly:

```sh
aw runs answer <run-id>
```

## Cross-Platform Hand-Test Checklist

Before deploying notifications across platforms (macOS, Linux, Windows), verify the following behaviors:

1. **Clean Setup Flow**: Run `aw notify setup telegram` end to end with a fresh bot token. Confirm rejection on an invalid token (HTTP 401) and test the webhook deletion prompt if an active webhook exists.
2. **Proxy and TLS**: Verify delivery through an authenticating proxy using `HTTPS_PROXY` and behind custom certificate authorities using corporate TLS interception.
3. **macOS Certificate Bundle**: On macOS with python.org Python installations, verify that missing root certificates produce a clear error message directing the user to run "Install Certificates.command".
4. **Sleep and Network Wake**: Put a laptop running `aw notify listen` to sleep for 10 or more minutes mid-poll. Confirm clean reconnection on wake across Wi-Fi or VPN transitions without duplicate answers.
5. **Lock Handover and Concurrency**: Run two independent runners with the same bot configuration on one machine; confirm the second runner takes over when the first exits. On two separate machines using the same token, confirm that HTTP 409 Conflict stops the poller with a descriptive remedy.
6. **Start-Up Drain**: Send an answer from Telegram while no runner is active. Start a new run or run `aw notify listen` and confirm the answer is collected by the start-up drain.
7. **Spoofing Resistance**: Send a message or button press from an unconfigured Telegram account. Confirm that the event is ignored and no answer file is written.
8. **Race Conditions**: Click a button on Telegram while simultaneously submitting an answer via `aw runs answer`. Verify that exactly one answer is recorded and the second returns "already answered".
9. **Message Truncation and Encoding**: Send a question with more than 4000 characters and non-BMP Unicode characters (emoji) near the truncation boundary. Verify grapheme-safe truncation without malformed characters.
10. **Log Hygiene**: Inspect all stdout, stderr, run events, and temporary files to verify that no bot token or chat ID is logged in cleartext.
11. **Teams Workflow Rendering**: Test incoming webhook delivery to Microsoft Teams Workflows using the `text` format and confirm card readability.
