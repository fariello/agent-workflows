"""CLI entrypoints and handlers for the aw notify command family (spec 6kwd2e R10.6, R10.9).

Provides setup (telegram, webhook, command), test, status, disable, and listen.
"""

from __future__ import annotations

import getpass
import json
import os
from pathlib import Path
import secrets
import signal
import sys
import time
from typing import Any, Optional

from filelock import FileLock, Timeout

from agent_workflows import project_context, term as _term
from agent_workflows.notify import config, core, telegram
from agent_workflows.notify.core import OutboundBatch
from agent_workflows.notify.telegram import (
    TelegramChannel,
    TelegramError,
    TelegramReceiver,
)
from agent_workflows.notify.webhook import (
    CommandChannel,
    WebhookChannel,
    safe_url_summary,
)
from agent_workflows.renderers import get_renderer
from agent_workflows.result_types import (
    CommandResult,
    NextAction,
    OutputContext,
)


def _find_last_event(channel_name: str) -> dict[str, Any] | None:
    """Find the most recent notify-sent or notify-failed event for a channel."""
    aw_home = Path(project_context.get_default_aw_home())
    candidates: list[Path] = []

    # Listen log
    listen_file = aw_home / "notify" / "listen.jsonl"
    if listen_file.is_file():
        candidates.append(listen_file)

    # Repository runs logs
    cwd = Path.cwd()
    for root in (cwd / ".aw" / "records" / "runs", cwd / ".aw" / "state" / "runs"):
        if root.is_dir():
            for p in sorted(root.glob("*/events.jsonl")):
                if p.is_file():
                    candidates.append(p)

    latest_record: dict[str, Any] | None = None
    latest_at = ""

    for events_file in candidates:
        try:
            for line in events_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        continue
                    ev = record.get("event")
                    if ev in ("notify-sent", "notify-failed", "notify-uncertain"):
                        if record.get("channel") == channel_name:
                            at = str(record.get("at") or "")
                            if at >= latest_at:
                                latest_at = at
                                latest_record = record
                except Exception:
                    continue
        except Exception:
            continue

    if latest_record:
        # Redact any details that might contain secrets
        cleaned = dict(latest_record)
        detail = cleaned.get("detail")
        if detail:
            user_cfg = config.load_user_config()
            ch_cfg = user_cfg.get(channel_name, {})
            cleaned["detail"] = core._redact_secrets(str(detail), ch_cfg)
        return cleaned

    return None


def run_status(
    args: Any,
    term: _term.Term,
    context: Optional[OutputContext] = None,
) -> int:
    """Report status of configured notification channels (spec 6kwd2e R10.9)."""
    ctx = context or OutputContext()
    repo = Path.cwd()
    policy = config.read_notify_policy(repo)
    user_cfg = config.load_user_config()

    # Determine status of each possible channel
    channels_info: dict[str, Any] = {}
    known_channels = ("telegram", "webhook", "command")

    for ch in known_channels:
        in_user = ch in user_cfg and isinstance(user_cfg[ch], dict)
        env_configured = False
        mode = "terse"
        enabled = False

        if ch == "telegram":
            env_token = os.environ.get("AW_NOTIFY_TELEGRAM_TOKEN")
            env_configured = bool(env_token and env_token.strip())
            c_dict = dict(user_cfg.get("telegram") or {})
            if env_configured:
                c_dict["token"] = env_token.strip()
                enabled = True
            else:
                enabled = bool(c_dict.get("enabled", False))
            mode = str(c_dict.get("mode") or "terse").lower()

            bot_id = telegram._get_bot_id(str(c_dict.get("token") or ""))
            holder_pid = telegram.read_lock_holder(bot_id)
            lock_holder = str(holder_pid) if holder_pid is not None else "none"

        elif ch == "webhook":
            env_url = os.environ.get("AW_NOTIFY_WEBHOOK_URL")
            env_configured = bool(env_url and env_url.strip())
            c_dict = dict(user_cfg.get("webhook") or {})
            if env_configured:
                c_dict["url"] = env_url.strip()
                enabled = True
            else:
                enabled = bool(c_dict.get("enabled", False))
            mode = str(c_dict.get("mode") or "terse").lower()
            lock_holder = "none"

        elif ch == "command":
            env_cmd = os.environ.get("AW_NOTIFY_COMMAND")
            env_configured = bool(env_cmd and env_cmd.strip())
            c_dict = dict(user_cfg.get("command") or {})
            if env_configured:
                enabled = True
            else:
                enabled = bool(c_dict.get("enabled", False))
            mode = str(c_dict.get("mode") or "terse").lower()
            lock_holder = "none"

        is_configured = in_user or env_configured
        if is_configured:
            source = "env" if env_configured else "user"
            last_ev = _find_last_event(ch)
            channels_info[ch] = {
                "source": source,
                "enabled": enabled,
                "mode": mode,
                "policy_ceiling": policy or "none",
                "receiver_lock_holder": lock_holder,
                "last_event": last_ev,
            }

    data: dict[str, Any] = {
        "policy": policy or "none",
        "channels": channels_info,
    }

    if not channels_info:
        hint = (
            "No notification channels configured.\n"
            "Run 'aw notify setup telegram', 'aw notify setup webhook', "
            "or 'aw notify setup command' to configure a channel."
        )
        if ctx.is_agent:
            res = CommandResult(
                command="notify status",
                status="clean",
                exit_code=0,
                summary="no notification channels configured",
                data=data,
                next_actions=[NextAction(command="aw notify setup telegram")],
                complete=True,
                verified=True,
            )
            return get_renderer(ctx).emit(res, ctx)
        elif ctx.is_json:
            ctx.stdout.write(json.dumps(data, indent=2) + "\n")
            ctx.stdout.flush()
            return 0
        ctx.stdout.write(hint + "\n")
        ctx.stdout.flush()
        return 0

    if ctx.is_agent:
        res = CommandResult(
            command="notify status",
            status="ok",
            exit_code=0,
            summary=f"{len(channels_info)} notification channel(s) configured",
            data=data,
            complete=True,
            verified=True,
        )
        return get_renderer(ctx).emit(res, ctx)
    elif ctx.is_json:
        ctx.stdout.write(json.dumps(data, indent=2) + "\n")
        ctx.stdout.flush()
        return 0

    # Human presentation
    lines = ["Notification Channels Status:"]
    lines.append(f"  Tracked policy ceiling: {policy or 'none'}")
    lines.append("")
    for ch_name, info in sorted(channels_info.items()):
        status_str = "enabled" if info["enabled"] else "disabled"
        lines.append(f"Channel: {ch_name}")
        lines.append(f"  Source: {info['source']}")
        lines.append(f"  Status: {status_str}")
        lines.append(f"  Mode: {info['mode']}")
        lines.append(f"  Receiver lock holder: {info['receiver_lock_holder']}")
        last_ev = info.get("last_event")
        if last_ev:
            ev_type = last_ev.get("event", "event")
            at = last_ev.get("at", "")
            detail = last_ev.get("detail") or last_ev.get("count") or ""
            lines.append(f"  Last event: {at} {ev_type} {detail}".strip())
        else:
            lines.append("  Last event: none")
        lines.append("")

    ctx.stdout.write("\n".join(lines).rstrip() + "\n")
    ctx.stdout.flush()
    return 0


def run_disable(
    args: Any,
    term: _term.Term,
    context: Optional[OutputContext] = None,
) -> int:
    """Disable a notification channel in user configuration (spec 6kwd2e R10.9)."""
    ctx = context or OutputContext()
    channel = getattr(args, "channel", "").strip().lower()

    if channel not in ("telegram", "webhook", "command"):
        msg = f"Unknown channel '{channel}'; valid channels are telegram, webhook, command."
        if ctx.is_agent:
            res = CommandResult(
                command=f"notify disable {channel}",
                status="cannot-run",
                exit_code=1,
                summary=msg,
                data={"channel": channel},
                complete=False,
                verified=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        ctx.stderr.write(f"Error: {msg}\n")
        ctx.stderr.flush()
        return 1

    # Check if channel is configured via environment variable
    env_keys = {
        "telegram": "AW_NOTIFY_TELEGRAM_TOKEN",
        "webhook": "AW_NOTIFY_WEBHOOK_URL",
        "command": "AW_NOTIFY_COMMAND",
    }
    env_key = env_keys[channel]
    if os.environ.get(env_key):
        msg = (
            f"Channel '{channel}' is configured via {env_key}. "
            "To disable it, unset the environment variable."
        )
        if ctx.is_agent:
            res = CommandResult(
                command=f"notify disable {channel}",
                status="cannot-run",
                exit_code=1,
                summary=msg,
                data={"channel": channel, "configured_via": env_key},
                complete=False,
                verified=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        ctx.stderr.write(f"Error: {msg}\n")
        ctx.stderr.flush()
        return 1

    user_cfg = config.load_user_config()
    if channel not in user_cfg or not isinstance(user_cfg[channel], dict):
        msg = f"Channel '{channel}' is not configured in user notify config."
        if ctx.is_agent:
            res = CommandResult(
                command=f"notify disable {channel}",
                status="cannot-run",
                exit_code=1,
                summary=msg,
                data={"channel": channel},
                complete=False,
                verified=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        ctx.stderr.write(f"Error: {msg}\n")
        ctx.stderr.flush()
        return 1

    user_cfg[channel]["enabled"] = False
    config.save_user_config(user_cfg)
    msg = f"Disabled channel '{channel}'."

    if ctx.is_agent:
        res = CommandResult(
            command=f"notify disable {channel}",
            status="ok",
            exit_code=0,
            summary=msg,
            data={"channel": channel, "enabled": False},
            complete=True,
            verified=True,
        )
        return get_renderer(ctx).emit(res, ctx)
    elif ctx.is_json:
        ctx.stdout.write(
            json.dumps({"channel": channel, "enabled": False, "message": msg}) + "\n"
        )
        ctx.stdout.flush()
        return 0

    ctx.stdout.write(f"{msg}\n")
    ctx.stdout.flush()
    return 0


def run_test(
    args: Any,
    term: _term.Term,
    context: Optional[OutputContext] = None,
) -> int:
    """Send a test notification to configured channels (spec 6kwd2e R10.9)."""
    ctx = context or OutputContext()
    target_channel = getattr(args, "channel", None)
    effective = config.effective_channels()

    if target_channel:
        target_channel = target_channel.strip().lower()
        if target_channel not in ("telegram", "webhook", "command"):
            msg = f"Unknown channel '{target_channel}'."
            if ctx.is_agent:
                res = CommandResult(
                    command=f"notify test {target_channel}",
                    status="cannot-run",
                    exit_code=1,
                    summary=msg,
                    data={"channel": target_channel},
                    complete=False,
                    verified=False,
                )
                return get_renderer(ctx).emit(res, ctx)
            ctx.stderr.write(f"Error: {msg}\n")
            ctx.stderr.flush()
            return 1

        if target_channel not in effective:
            msg = f"Channel '{target_channel}' is not currently active or enabled."
            if ctx.is_agent:
                res = CommandResult(
                    command=f"notify test {target_channel}",
                    status="cannot-run",
                    exit_code=1,
                    summary=msg,
                    data={"channel": target_channel},
                    complete=False,
                    verified=False,
                )
                return get_renderer(ctx).emit(res, ctx)
            ctx.stderr.write(f"Error: {msg}\n")
            ctx.stderr.flush()
            return 1

        targets = {target_channel: effective[target_channel]}
    else:
        if not effective:
            msg = "No effective notification channels configured to test."
            if ctx.is_agent:
                res = CommandResult(
                    command="notify test",
                    status="cannot-run",
                    exit_code=1,
                    summary=msg,
                    data={},
                    complete=False,
                    verified=False,
                )
                return get_renderer(ctx).emit(res, ctx)
            ctx.stderr.write(f"Error: {msg}\n")
            ctx.stderr.flush()
            return 1
        targets = effective

    results: dict[str, dict[str, Any]] = {}
    any_failed = False

    for name, c_cfg in sorted(targets.items()):
        if name == "telegram":
            bot_id = telegram._get_bot_id(str(c_cfg.get("token") or ""))
            lock_path = telegram.get_lock_path(bot_id)
            lock = FileLock(str(lock_path), timeout=0, thread_local=False)
            try:
                lock.acquire()
            except (Timeout, Exception):
                msg = "stop the run or use a second bot"
                ctx.stderr.write(f"Telegram test failed: {msg}\n")
                ctx.stderr.flush()
                results[name] = {"ok": False, "detail": msg}
                any_failed = True
                continue

            telegram.write_lock_holder(bot_id, os.getpid())
            try:
                tg_chan = TelegramChannel(c_cfg)
                # Send terse test with inline button
                sent = tg_chan._call(
                    "sendMessage",
                    {
                        "chat_id": tg_chan.chat_id,
                        "text": "aw notify test: please click the button below to complete verification.",
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "Acknowledge Test",
                                        "callback_data": "test:ack",
                                    }
                                ]
                            ]
                        },
                    },
                    timeout=10.0,
                )
                if not sent:
                    results[name] = {
                        "ok": False,
                        "detail": "Failed to send test message",
                    }
                    any_failed = True
                    continue

                if not ctx.is_agent and not ctx.is_json:
                    ctx.stdout.write(
                        "Telegram test sent; waiting up to 2 minutes for button press...\n"
                    )
                    ctx.stdout.flush()

                # Poll for button press for up to 120s
                start_poll = time.time()
                offset = telegram.read_offset(bot_id)
                button_pressed = False

                while time.time() - start_poll < 120.0:
                    events, next_cursor = tg_chan.receive(
                        cursor=offset,
                        deadline=min(time.time() + 10.0, start_poll + 120.0),
                    )
                    for ev in events:
                        offset = max(offset or 0, int(ev.event_id) + 1)
                        raw = ev.raw
                        if isinstance(raw, dict) and "callback_query" in raw:
                            cb = raw["callback_query"]
                            sender = str(cb.get("from", {}).get("id", ""))
                            data_cb = cb.get("data", "")
                            if sender == tg_chan.user_id and data_cb == "test:ack":
                                tg_chan._call(
                                    "answerCallbackQuery",
                                    {
                                        "callback_query_id": cb.get("id"),
                                        "text": "Test acknowledged",
                                    },
                                    timeout=10.0,
                                )
                                button_pressed = True
                                break
                    if next_cursor and (offset is None or next_cursor > offset):
                        offset = next_cursor
                    if button_pressed:
                        break

                telegram.save_offset(bot_id, offset)

                if button_pressed:
                    results[name] = {
                        "ok": True,
                        "detail": "Delivered and button acknowledged",
                    }
                    if not ctx.is_agent and not ctx.is_json:
                        ctx.stdout.write("Telegram test: button press confirmed.\n")
                        ctx.stdout.flush()
                else:
                    results[name] = {
                        "ok": False,
                        "detail": "Timed out waiting for button press",
                    }
                    any_failed = True
                    ctx.stderr.write(
                        "Telegram test failed: timed out waiting for button press.\n"
                    )
                    ctx.stderr.flush()

            except Exception as exc:
                clean_err = str(exc).replace(tg_chan.token, "<token>")
                results[name] = {"ok": False, "detail": clean_err}
                any_failed = True
                ctx.stderr.write(f"Telegram test error: {clean_err}\n")
                ctx.stderr.flush()
            finally:
                telegram.release_lock_holder(bot_id)
                lock.release()

        elif name == "webhook":
            wh_chan = WebhookChannel(c_cfg)
            batch = OutboundBatch(
                run_id="test",
                mode="terse",
                message="aw notify test: notification test",
                questions=[],
            )
            receipt = wh_chan.send(batch)
            if receipt.ok:
                results[name] = {"ok": True, "detail": receipt.detail}
                if not ctx.is_agent and not ctx.is_json:
                    ctx.stdout.write(f"Webhook test delivered: {receipt.detail}\n")
                    ctx.stdout.flush()
            else:
                results[name] = {"ok": False, "detail": receipt.detail}
                any_failed = True
                ctx.stderr.write(f"Webhook test failed: {receipt.detail}\n")
                ctx.stderr.flush()

        elif name == "command":
            cmd_chan = CommandChannel(c_cfg)
            batch = OutboundBatch(
                run_id="test",
                mode="terse",
                message="aw notify test: notification test",
                questions=[],
            )
            receipt = cmd_chan.send(batch)
            if receipt.ok:
                results[name] = {"ok": True, "detail": receipt.detail}
                if not ctx.is_agent and not ctx.is_json:
                    ctx.stdout.write(f"Command hook test delivered: {receipt.detail}\n")
                    ctx.stdout.flush()
            else:
                results[name] = {"ok": False, "detail": receipt.detail}
                any_failed = True
                ctx.stderr.write(f"Command hook test failed: {receipt.detail}\n")
                ctx.stderr.flush()

    exit_code = 1 if any_failed else 0
    outcome = "fail" if any_failed else "ok"

    if ctx.is_agent:
        res = CommandResult(
            command="notify test",
            status=outcome,
            exit_code=exit_code,
            summary="all channels passed"
            if not any_failed
            else "one or more channel tests failed",
            data=results,
            complete=not any_failed,
            verified=not any_failed,
        )
        return get_renderer(ctx).emit(res, ctx)
    elif ctx.is_json:
        ctx.stdout.write(
            json.dumps({"success": not any_failed, "results": results}, indent=2) + "\n"
        )
        ctx.stdout.flush()
        return exit_code

    if not any_failed:
        ctx.stdout.write("All notification tests delivered successfully.\n")
        ctx.stdout.flush()
    return exit_code


def run_setup_telegram(
    args: Any,
    term: _term.Term,
    context: Optional[OutputContext] = None,
) -> int:
    """Guided pairing and setup for Telegram notifications (spec 6kwd2e R10.9)."""
    ctx = context or OutputContext()

    # Refuse non-interactive execution or --agent (A54, E-01)
    if ctx.is_agent:
        ctx.stderr.write(
            "Error: aw notify setup telegram does not support --agent; an interactive terminal is required.\n"
        )
        ctx.stderr.flush()
        return 2

    if not term.is_interactive():
        ctx.stderr.write(
            "Error: aw notify setup telegram requires an interactive terminal.\n"
        )
        ctx.stderr.flush()
        return 2

    # 1. Print privacy and data notice
    print("\nPrivacy & Data Notice for Telegram Notifications:")
    print(
        "  - In terse mode (default), notifications contain only the run id, question count, and answer command."
    )
    print(
        "  - In full mode, notifications contain sanitized question text and option choices."
    )
    print(
        "  - Telegram bot chats are not end-to-end encrypted: Telegram servers can process bot messages."
    )
    print("  - Terse mode is the default.")
    print("")

    # 2. Read token with hidden input or from environment
    env_token = os.environ.get("AW_NOTIFY_TELEGRAM_TOKEN")
    if env_token and env_token.strip():
        token = env_token.strip()
        print("Using Telegram bot token from AW_NOTIFY_TELEGRAM_TOKEN.")
    else:
        try:
            token = getpass.getpass("Enter Telegram bot token: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSetup aborted.", file=sys.stderr)
            return 1

    if not token:
        print("Error: No bot token provided.", file=sys.stderr)
        return 1

    # 3. Call getMe and verify
    channel = TelegramChannel({"token": token})
    try:
        me = channel._call("getMe", timeout=10.0)
    except TelegramError as err:
        print(f"Error verifying bot token: {err}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    bot_username = me.get("username", "bot")
    bot_id = str(me.get("id") or telegram._get_bot_id(token))
    print(f"Verified bot: @{bot_username} (ID: {bot_id})")

    # 4. Check getWebhookInfo
    try:
        wh = channel._call("getWebhookInfo", timeout=10.0)
        wh_url = wh.get("url", "")
        if wh_url:
            print(
                "\nA webhook is currently configured on this bot. Polling cannot run beside an active webhook."
            )
            try:
                ans = input("Delete active webhook? [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nSetup aborted.", file=sys.stderr)
                return 1
            if ans != "y":
                print(
                    "Webhook deletion declined; setup aborted writing nothing.",
                    file=sys.stderr,
                )
                return 1
            channel._call("deleteWebhook", timeout=10.0)
            print("Webhook deleted.")
    except TelegramError as err:
        print(f"Error checking webhook status: {err}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    # 5. Take per-bot receiver lock non-blocking
    lock_path = telegram.get_lock_path(bot_id)
    lock = FileLock(str(lock_path), timeout=0, thread_local=False)
    try:
        lock.acquire()
    except (Timeout, Exception):
        print("stop the run or use a second bot", file=sys.stderr)
        return 1

    telegram.write_lock_holder(bot_id, os.getpid())

    try:
        # 6. Generate one-time pairing phrase
        phrase = secrets.token_urlsafe(8)
        print(f"\nPlease send the following phrase to your bot:\n  {phrase}")
        print(f"Or open this link: https://t.me/{bot_username}?start={phrase}\n")
        print("Waiting for pairing message (up to 5 minutes)...")

        start_pairing = time.time()
        offset = telegram.read_offset(bot_id)
        paired_sender: dict[str, Any] | None = None

        while time.time() - start_pairing < 300.0:
            try:
                events, next_cursor = channel.receive(
                    cursor=offset,
                    deadline=min(time.time() + 10.0, start_pairing + 300.0),
                )
            except Exception as exc:
                print(f"Polling error: {exc}", file=sys.stderr)
                return 1

            for ev in events:
                offset = max(offset or 0, int(ev.event_id) + 1)
                raw = ev.raw
                if not isinstance(raw, dict):
                    continue
                msg = raw.get("message")
                if not msg:
                    continue
                chat = msg.get("chat", {})
                # MUST be a private message
                if chat.get("type") != "private":
                    continue
                from_obj = msg.get("from", {})
                if from_obj.get("is_bot", False):
                    continue
                text = str(msg.get("text") or "")
                if phrase in text:
                    paired_sender = {
                        "user_id": str(from_obj.get("id")),
                        "first_name": from_obj.get("first_name", ""),
                        "last_name": from_obj.get("last_name", ""),
                        "username": from_obj.get("username", ""),
                        "chat_id": str(chat.get("id")),
                    }
                    break

            if next_cursor and (offset is None or next_cursor > offset):
                offset = next_cursor

            if paired_sender:
                break

        telegram.save_offset(bot_id, offset)

        if not paired_sender:
            print("Pairing timed out; no matching phrase received.", file=sys.stderr)
            return 1

        # 7. Show identity and require explicit confirmation
        name_parts = [paired_sender["first_name"], paired_sender["last_name"]]
        full_name = " ".join(p for p in name_parts if p).strip()
        if paired_sender["username"]:
            full_name += f" (@{paired_sender['username']})"
        print("\nDetected pairing request:")
        print(f"  Name: {full_name}")
        print(f"  User ID: {paired_sender['user_id']}")
        print(f"  Chat ID: {paired_sender['chat_id']}")

        try:
            conf = input("Confirm identity and pair? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nSetup aborted.", file=sys.stderr)
            return 1

        if conf != "y":
            print("Identity confirmation declined; setup aborted.", file=sys.stderr)
            return 1

        # 8. Send test question with two buttons and force_reply
        print("\nSending test question with buttons and reply prompt...")
        test_msg = channel._call(
            "sendMessage",
            {
                "chat_id": paired_sender["chat_id"],
                "text": "Setup test: please click one button below AND reply to this message.",
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {"text": "Option 1", "callback_data": "setup:opt1"},
                            {"text": "Option 2", "callback_data": "setup:opt2"},
                        ]
                    ],
                    "force_reply": True,
                },
            },
            timeout=10.0,
        )
        test_msg_id = test_msg.get("message_id") if isinstance(test_msg, dict) else None

        button_confirmed = False
        reply_confirmed = False
        test_start = time.time()

        while (not (button_confirmed and reply_confirmed)) and (
            time.time() - test_start < 300.0
        ):
            try:
                events, next_cursor = channel.receive(
                    cursor=offset,
                    deadline=min(time.time() + 10.0, test_start + 300.0),
                )
            except Exception as exc:
                print(f"Polling error: {exc}", file=sys.stderr)
                return 1

            for ev in events:
                offset = max(offset or 0, int(ev.event_id) + 1)
                raw = ev.raw
                if not isinstance(raw, dict):
                    continue

                if "callback_query" in raw and not button_confirmed:
                    cb = raw["callback_query"]
                    sender_id = str(cb.get("from", {}).get("id", ""))
                    cb_data = cb.get("data", "")
                    if sender_id == paired_sender["user_id"] and cb_data in (
                        "setup:opt1",
                        "setup:opt2",
                    ):
                        channel._call(
                            "answerCallbackQuery",
                            {
                                "callback_query_id": cb.get("id"),
                                "text": "Button confirmed",
                            },
                            timeout=10.0,
                        )
                        button_confirmed = True
                        print("  Button click confirmed.")

                if "message" in raw and not reply_confirmed:
                    m = raw["message"]
                    sender_id = str(m.get("from", {}).get("id", ""))
                    reply_to = m.get("reply_to_message", {})
                    reply_id = (
                        reply_to.get("message_id")
                        if isinstance(reply_to, dict)
                        else None
                    )
                    if (
                        sender_id == paired_sender["user_id"]
                        and reply_id == test_msg_id
                    ):
                        channel._call(
                            "sendMessage",
                            {
                                "chat_id": paired_sender["chat_id"],
                                "text": "Threaded reply confirmed.",
                                "reply_to_message_id": m.get("message_id"),
                            },
                            timeout=10.0,
                        )
                        reply_confirmed = True
                        print("  Threaded reply confirmed.")

            if next_cursor and (offset is None or next_cursor > offset):
                offset = next_cursor

        telegram.save_offset(bot_id, offset)

        if not (button_confirmed and reply_confirmed):
            print(
                "Setup verification failed: did not receive both button click and reply.",
                file=sys.stderr,
            )
            return 1

        # 9. Save channel config
        mode = "full" if getattr(args, "full", False) else "terse"
        cfg = config.load_user_config()
        cfg["telegram"] = {
            "enabled": True,
            "token": token,
            "chat_id": paired_sender["chat_id"],
            "user_id": paired_sender["user_id"],
            "mode": mode,
        }
        config.save_user_config(cfg)

        print("\nSetup complete! Telegram notifications configured.")
        print(f"Saved to notify.json (mode: {mode}).")
        print("\nRun checks:")
        print("  aw notify test")
        print("  aw notify status")
        return 0

    except KeyboardInterrupt:
        print("\nSetup aborted by user.", file=sys.stderr)
        return 1
    finally:
        telegram.release_lock_holder(bot_id)
        lock.release()


def run_setup_webhook(
    args: Any,
    term: _term.Term,
    context: Optional[OutputContext] = None,
) -> int:
    """Setup webhook notification channel (spec 6kwd2e R10.9)."""
    ctx = context or OutputContext()

    url: str = ""
    if getattr(args, "url_stdin", False):
        try:
            if term.is_interactive():
                url = getpass.getpass("Enter webhook URL: ").strip()
            else:
                url = sys.stdin.readline().strip()
        except (KeyboardInterrupt, EOFError):
            ctx.stderr.write("Setup aborted.\n")
            ctx.stderr.flush()
            return 1
    elif getattr(args, "url", None):
        print(
            "WARNING: Webhook URL passed on the command line may be recorded in shell history.",
            file=sys.stderr,
        )
        url = str(args.url).strip()
    elif os.environ.get("AW_NOTIFY_WEBHOOK_URL"):
        url = os.environ["AW_NOTIFY_WEBHOOK_URL"].strip()

    if not url:
        ctx.stderr.write(
            "Error: --url, --url-stdin, or AW_NOTIFY_WEBHOOK_URL is required.\n"
        )
        ctx.stderr.flush()
        return 2

    summary = safe_url_summary(url)
    fmt = getattr(args, "format", "aw") or "aw"
    mode = "full" if getattr(args, "full", False) else "terse"

    # Send one test notification through Order 09 webhook channel
    wh_chan = WebhookChannel({"url": url, "format": fmt, "mode": mode})
    batch = OutboundBatch(
        run_id="setup-test",
        mode=mode,
        message="aw notify setup test notification",
        questions=[],
    )
    receipt = wh_chan.send(batch)

    if not receipt.ok:
        ctx.stderr.write(f"Webhook test failed: {receipt.detail}\n")
        ctx.stderr.flush()
        return 1

    # Save to user config on success
    cfg = config.load_user_config()
    cfg["webhook"] = {
        "enabled": True,
        "url": url,
        "format": fmt,
        "mode": mode,
    }
    config.save_user_config(cfg)

    msg = f"Webhook configured successfully for {summary} (format={fmt}, mode={mode})."
    if ctx.is_agent:
        res = CommandResult(
            command="notify setup webhook",
            status="ok",
            exit_code=0,
            summary=msg,
            data={"summary": summary, "format": fmt, "mode": mode},
            complete=True,
            verified=True,
        )
        return get_renderer(ctx).emit(res, ctx)
    elif ctx.is_json:
        ctx.stdout.write(
            json.dumps({"summary": summary, "format": fmt, "mode": mode}) + "\n"
        )
        ctx.stdout.flush()
        return 0

    ctx.stdout.write(f"{msg}\n")
    ctx.stdout.flush()
    return 0


def run_setup_command(
    args: Any,
    term: _term.Term,
    context: Optional[OutputContext] = None,
) -> int:
    """Setup command hook notification channel (spec 6kwd2e R10.9)."""
    ctx = context or OutputContext()

    raw_argv = list(getattr(args, "argv", []) or [])
    if raw_argv and raw_argv[0] == "--":
        raw_argv = raw_argv[1:]

    if not raw_argv:
        ctx.stderr.write("Error: command argv is required.\n")
        ctx.stderr.flush()
        return 2

    mode = "full" if getattr(args, "full", False) else "terse"

    cmd_chan = CommandChannel({"command": raw_argv, "mode": mode})
    batch = OutboundBatch(
        run_id="setup-test",
        mode=mode,
        message="aw notify setup test notification",
        questions=[],
    )
    receipt = cmd_chan.send(batch)

    if not receipt.ok:
        ctx.stderr.write(f"Command hook test failed: {receipt.detail}\n")
        ctx.stderr.flush()
        return 1

    cfg = config.load_user_config()
    cfg["command"] = {
        "enabled": True,
        "command": raw_argv,
        "mode": mode,
    }
    config.save_user_config(cfg)

    msg = f"Command hook configured successfully ({raw_argv[0]}, mode={mode})."
    if ctx.is_agent:
        res = CommandResult(
            command="notify setup command",
            status="ok",
            exit_code=0,
            summary=msg,
            data={"command": raw_argv, "mode": mode},
            complete=True,
            verified=True,
        )
        return get_renderer(ctx).emit(res, ctx)
    elif ctx.is_json:
        ctx.stdout.write(json.dumps({"command": raw_argv, "mode": mode}) + "\n")
        ctx.stdout.flush()
        return 0

    ctx.stdout.write(f"{msg}\n")
    ctx.stdout.flush()
    return 0


def run_listen(
    args: Any,
    term: _term.Term,
    context: Optional[OutputContext] = None,
) -> int:
    """Foreground Telegram listener for answering questions from finished runs (spec 6kwd2e R10.6)."""
    ctx = context or OutputContext()
    effective = config.effective_channels()

    if "telegram" not in effective:
        msg = "No Telegram channel configured. Run 'aw notify setup telegram' first."
        if ctx.is_agent:
            res = CommandResult(
                command="notify listen",
                status="cannot-run",
                exit_code=1,
                summary=msg,
                data={},
                complete=False,
                verified=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        ctx.stderr.write(f"Error: {msg}\n")
        ctx.stderr.flush()
        return 1

    tg_cfg = effective["telegram"]
    bot_id = telegram._get_bot_id(str(tg_cfg.get("token") or ""))
    lock_path = telegram.get_lock_path(bot_id)
    lock = FileLock(str(lock_path), timeout=0, thread_local=False)

    try:
        lock.acquire()
    except (Timeout, Exception):
        holder = telegram.read_lock_holder(bot_id)
        holder_str = f"pid {holder}" if holder is not None else "another process"
        msg = f"Telegram receiver lock held by {holder_str}."
        if ctx.is_agent:
            res = CommandResult(
                command="notify listen",
                status="cannot-run",
                exit_code=1,
                summary=msg,
                data={"lock_holder": holder},
                complete=False,
                verified=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        ctx.stderr.write(f"Error: {msg}\n")
        ctx.stderr.flush()
        return 1

    telegram.write_lock_holder(bot_id, os.getpid())

    aw_home = Path(project_context.get_default_aw_home())
    events_file = aw_home / "notify" / "listen.jsonl"
    events_file.parent.mkdir(parents=True, exist_ok=True)

    def on_inbound_event(ev: Any, outcome: str) -> None:
        if outcome in ("recorded", "already"):
            ctx.stdout.write(f"Answer recorded: {outcome} from sender {ev.sender}\n")
            ctx.stdout.flush()
        elif outcome == "rejected":
            ctx.stdout.write(f"Answer rejected from sender {ev.sender}\n")
            ctx.stdout.flush()

    channel = TelegramChannel(tg_cfg)
    receiver = TelegramReceiver(
        bot_id=bot_id,
        channel=channel,
        run_dir=events_file.parent,
        lock=lock,
        events_path=events_file,
        on_event=on_inbound_event,
    )

    import threading

    stop_event = threading.Event()

    def _sig_handler(signum: int, frame: Any) -> None:
        stop_event.set()

    old_term = signal.signal(signal.SIGTERM, _sig_handler)
    old_int = signal.signal(signal.SIGINT, _sig_handler)

    try:
        receiver.drain_startup()
        receiver.start()
        if not ctx.is_agent and not ctx.is_json:
            ctx.stdout.write(
                "aw notify listen running in foreground. Press Ctrl-C to stop.\n"
            )
            ctx.stdout.flush()

        while not stop_event.is_set():
            if not receiver.is_alive():
                break
            time.sleep(0.1)

    finally:
        receiver.stop(timeout=10.0)
        signal.signal(signal.SIGTERM, old_term)
        signal.signal(signal.SIGINT, old_int)

    if ctx.is_agent:
        res = CommandResult(
            command="notify listen",
            status="ok",
            exit_code=0,
            summary="listen stopped cleanly",
            data={},
            complete=True,
            verified=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    return 0
