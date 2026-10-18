"""Two-way Telegram notification channel (spec 6kwd2e R10.5, R10.6, R10.8a).

Implements the Channel protocol over urllib.request with long polling,
inline buttons with random tokens, threaded free-text replies, sender
verification, and a per-bot daemon receiver thread with lock takeover.
"""

from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import random
import re
import secrets
import threading
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from filelock import FileLock, Timeout

from agent_workflows import project_context, runner_shared
from agent_workflows.notify import config, registry
from agent_workflows.notify.core import (
    Caps,
    Health,
    InboundEvent,
    OutboundBatch,
    Receipt,
    apply_inbound,
    utc_now,
)


class TelegramError(Exception):
    """Exception raised for Telegram API and transport errors without leaking bot tokens."""

    def __init__(
        self,
        code: int | None,
        description: str,
        retry_after: int | None = None,
    ):
        self.code = code
        self.description = description
        self.retry_after = retry_after
        msg = f"HTTP {code}: {description}" if code is not None else description
        if retry_after is not None:
            msg += f" (retry_after={retry_after})"
        super().__init__(msg)

    def __repr__(self) -> str:
        return (
            f"TelegramError(code={self.code!r}, "
            f"description={self.description!r}, "
            f"retry_after={self.retry_after!r})"
        )


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse HTTP redirects so requests are never silently forwarded."""

    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> Any:
        return None


def truncate_utf16(text: str, max_units: int = 4000) -> str:
    """Truncate text to at most max_units UTF-16 code units without splitting surrogate pairs."""
    units = 0
    chars: list[str] = []
    for ch in text:
        ch_units = 2 if ord(ch) > 0xFFFF else 1
        if units + ch_units > max_units:
            break
        units += ch_units
        chars.append(ch)
    return "".join(chars)


def utf16_len(text: str) -> int:
    """Return the length of text in UTF-16 code units."""
    return len(text.encode("utf-16-le")) // 2


def _truncate_bytes(s: str, max_bytes: int = 64) -> str:
    """Truncate string to at most max_bytes in UTF-8 encoding without splitting characters."""
    encoded = s.encode("utf-8")
    if len(encoded) <= max_bytes:
        return s
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def _get_bot_id(token: str) -> str:
    """Extract numeric bot id from token '123456:ABC...', or fallback."""
    if token and ":" in token:
        prefix = token.split(":", 1)[0].strip()
        if prefix:
            return prefix
    return "bot"


def get_offset_path(bot_id: str) -> Path:
    """Path to the persistent offset file under <AW_HOME>/notify/."""
    aw_home = Path(project_context.get_default_aw_home())
    notify_dir = aw_home / "notify"
    notify_dir.mkdir(parents=True, exist_ok=True)
    return notify_dir / f"telegram-{bot_id}.offset"


def read_offset(bot_id: str) -> int | None:
    """Read the persistent offset for bot_id, or None if not set."""
    path = get_offset_path(bot_id)
    if not path.is_file():
        return None
    try:
        val = path.read_text(encoding="utf-8").strip()
        return int(val) if val else None
    except Exception:
        return None


def save_offset(bot_id: str, offset: int) -> None:
    """Atomically write the persistent offset for bot_id."""
    path = get_offset_path(bot_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f".offset.tmp.{bot_id}.{os.getpid()}.{time.time_ns()}"
    try:
        tmp_path.write_text(f"{offset}\n", encoding="utf-8")
        os.replace(str(tmp_path), str(path))
    finally:
        if tmp_path.exists():
            with contextlib.suppress(OSError):
                tmp_path.unlink()


def get_lock_path(bot_id: str) -> Path:
    """Path to the per-bot receiver lock file under <AW_HOME>/notify/."""
    aw_home = Path(project_context.get_default_aw_home())
    notify_dir = aw_home / "notify"
    notify_dir.mkdir(parents=True, exist_ok=True)
    return notify_dir / f"telegram-{bot_id}.lock"


def get_lock_sidecar_path(bot_id: str) -> Path:
    """Path to the per-bot receiver lock holder sidecar file under <AW_HOME>/notify/."""
    aw_home = Path(project_context.get_default_aw_home())
    notify_dir = aw_home / "notify"
    notify_dir.mkdir(parents=True, exist_ok=True)
    return notify_dir / f"telegram-{bot_id}.lock.sidecar"


def read_lock_holder(bot_id: str) -> int | None:
    """Read receiver lock holder PID from the lock's sidecar, never taking the lock."""
    sidecar = get_lock_sidecar_path(bot_id)
    if not sidecar.is_file():
        return None
    try:
        content = sidecar.read_text(encoding="utf-8").strip()
        m = re.search(r"\d+", content)
        return int(m.group(0)) if m else None
    except Exception:
        return None


def write_lock_holder(bot_id: str, pid: int | None = None) -> None:
    """Write receiver lock holder PID to the lock's sidecar."""
    if pid is None:
        pid = os.getpid()
    sidecar = get_lock_sidecar_path(bot_id)
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(f"{pid}\n", encoding="utf-8")


def release_lock_holder(bot_id: str) -> None:
    """Remove the receiver lock holder sidecar."""
    sidecar = get_lock_sidecar_path(bot_id)
    with contextlib.suppress(OSError):
        sidecar.unlink(missing_ok=True)


class TelegramChannel:
    """Two-way Telegram notification channel using standard library urllib."""

    def __init__(
        self,
        config_dict: dict[str, Any] | None = None,
        *,
        run_dir: Path | str | None = None,
        poll_timeout_cap: float = 25.0,
    ):
        if config_dict is None:
            user_cfg = config.load_user_config()
            config_dict = user_cfg.get("telegram") or {}

        self.token = str(
            config_dict.get("token") or os.environ.get("AW_NOTIFY_TELEGRAM_TOKEN") or ""
        ).strip()
        self.user_id = str(
            config_dict.get("user_id")
            or os.environ.get("AW_NOTIFY_TELEGRAM_USER_ID")
            or ""
        ).strip()
        self.chat_id = str(
            config_dict.get("chat_id")
            or os.environ.get("AW_NOTIFY_TELEGRAM_CHAT_ID")
            or ""
        ).strip()
        self.mode = str(
            config_dict.get("mode")
            or os.environ.get("AW_NOTIFY_TELEGRAM_MODE")
            or "terse"
        ).lower()
        self.name = "telegram"
        self.run_dir = Path(run_dir).resolve() if run_dir else None
        env_timeout = os.environ.get("AW_NOTIFY_TELEGRAM_POLL_TIMEOUT")
        if env_timeout:
            try:
                poll_timeout_cap = float(env_timeout)
            except ValueError:
                pass
        self.poll_timeout_cap = poll_timeout_cap
        self.bot_id = _get_bot_id(self.token)
        self.caps = Caps(max_text=4000, answer=True, buttons=True)

    @property
    def base_url(self) -> str:
        url = os.environ.get(
            "AW_NOTIFY_TELEGRAM_BASE_URL", "https://api.telegram.org"
        ).rstrip("/")
        p = urllib.parse.urlsplit(url)
        scheme = p.scheme.lower()
        host = (p.hostname or "").lower()
        loopback = host in ("127.0.0.1", "::1", "localhost")
        if scheme != "https" and not (scheme == "http" and loopback):
            raise TelegramError(
                None, f"Refusing non-HTTPS URL on non-loopback host: {url}"
            )
        return url

    def _call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = 40.0,
    ) -> Any:
        if not self.token:
            raise TelegramError(None, "No Telegram bot token configured")

        base = self.base_url
        url = f"{base}/bot{self.token}/{method}"
        body_bytes = json.dumps(params or {}).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8"}
        opener = urllib.request.build_opener(_NoRedirectHandler)
        req = urllib.request.Request(
            url, data=body_bytes, headers=headers, method="POST"
        )

        try:
            with opener.open(req, timeout=timeout) as resp:
                data = resp.read().decode("utf-8", errors="replace")
                parsed = json.loads(data)
                if not isinstance(parsed, dict) or not parsed.get("ok"):
                    err_code = (
                        parsed.get("error_code") if isinstance(parsed, dict) else None
                    )
                    desc = (
                        parsed.get("description", "Telegram API returned failure")
                        if isinstance(parsed, dict)
                        else "Unknown error"
                    )
                    retry_after = (
                        parsed.get("parameters", {}).get("retry_after")
                        if isinstance(parsed, dict)
                        else None
                    )
                    clean_desc = desc.replace(self.token, "<token>")
                    raise TelegramError(err_code, clean_desc, retry_after)
                return parsed.get("result")
        except urllib.error.HTTPError as err:
            code = err.code
            desc = str(err.reason or err.code)
            retry_after = None
            try:
                err_body = err.read().decode("utf-8", errors="replace")
                err_json = json.loads(err_body)
                if isinstance(err_json, dict):
                    desc = err_json.get("description", desc)
                    params_obj = err_json.get("parameters")
                    if isinstance(params_obj, dict) and "retry_after" in params_obj:
                        retry_after = int(params_obj["retry_after"])
            except Exception:
                pass
            clean_desc = desc.replace(self.token, "<token>")
            raise TelegramError(code, clean_desc, retry_after) from None
        except urllib.error.URLError as err:
            desc = str(err.reason)
            clean_desc = desc.replace(self.token, "<token>")
            raise TelegramError(None, clean_desc) from None
        except OSError as err:
            desc = str(err)
            clean_desc = desc.replace(self.token, "<token>")
            raise TelegramError(None, clean_desc) from None

    def capabilities(self) -> Caps:
        return self.caps

    def health(self) -> Health:
        if not self.token:
            return Health(ok=False, detail="No Telegram bot token configured")
        try:
            me = self._call("getMe", timeout=10.0)
            username = me.get("username", "<unknown>")
            wh = self._call("getWebhookInfo", timeout=10.0)
            wh_url = wh.get("url", "")
            wh_status = f"webhook set ({wh_url})" if wh_url else "no webhook"
            return Health(
                ok=True,
                detail=f"bot @{username}; {wh_status}",
            )
        except TelegramError as err:
            return Health(ok=False, detail=str(err))
        except Exception as exc:
            msg = str(exc).replace(self.token, "<token>")
            return Health(ok=False, detail=msg)

    def _lookup_registered_message_id(self, question_id: str) -> int | None:
        """Search routing registry for the original Telegram message id of a question."""
        reg_path, lock_path = registry._get_registry_paths()
        with FileLock(str(lock_path), timeout=10):
            data = registry._read_registry_locked(reg_path)
            tg_routes = data.get("routes", {}).get("telegram", {})
            for key, entry in tg_routes.items():
                if (
                    entry.get("question_id") == question_id
                    and entry.get("option") is None
                ):
                    try:
                        return int(key)
                    except ValueError:
                        continue
        return None

    def _record_uncertain(self, batch: OutboundBatch, detail: str) -> None:
        """Record notify-uncertain event in run events.jsonl."""
        run_dir = self.run_dir
        if not run_dir:
            candidate = Path.cwd() / ".aw" / "records" / "runs" / batch.run_id
            if candidate.is_dir():
                run_dir = candidate
            else:
                candidate2 = Path.cwd() / ".aw" / "state" / "runs" / batch.run_id
                if candidate2.is_dir():
                    run_dir = candidate2
        if run_dir:
            with contextlib.suppress(Exception):
                runner_shared.append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "notify-uncertain",
                        "channel": "telegram",
                        "detail": detail,
                    },
                )

    def send(self, batch: OutboundBatch) -> Receipt:
        if not self.token:
            return Receipt(ok=False, detail="No Telegram bot token configured")
        if not self.chat_id:
            return Receipt(ok=False, detail="No Telegram chat_id configured")

        # 1. Detect if this is an acknowledgement batch (from dispatch_checkpoint)
        qid_ack: str | None = None
        if len(batch.questions) == 1 and not batch.questions[0].text:
            qid_ack = batch.questions[0].question_id
        else:
            m = re.match(
                r"^run \S+ \((\S+)\): (?:answered via|answer not applied)",
                batch.message,
            )
            if m:
                qid_ack = m.group(1)

        if qid_ack is not None or (
            not batch.questions and "answered via" in batch.message
        ):
            orig_msg_id = (
                self._lookup_registered_message_id(qid_ack) if qid_ack else None
            )
            try:
                if orig_msg_id is not None:
                    # Clear inline buttons on original message
                    with contextlib.suppress(Exception):
                        self._call(
                            "editMessageReplyMarkup",
                            {
                                "chat_id": self.chat_id,
                                "message_id": orig_msg_id,
                                "reply_markup": {"inline_keyboard": []},
                            },
                            timeout=10.0,
                        )
                    # Send acknowledgement as reply to original message
                    sent = self._call(
                        "sendMessage",
                        {
                            "chat_id": self.chat_id,
                            "text": truncate_utf16(batch.message, self.caps.max_text),
                            "reply_to_message_id": orig_msg_id,
                            "link_preview_options": {"is_disabled": True},
                        },
                        timeout=10.0,
                    )
                else:
                    sent = self._call(
                        "sendMessage",
                        {
                            "chat_id": self.chat_id,
                            "text": truncate_utf16(batch.message, self.caps.max_text),
                            "link_preview_options": {"is_disabled": True},
                        },
                        timeout=10.0,
                    )
                msg_id = str(sent.get("message_id")) if isinstance(sent, dict) else None
                return Receipt(ok=True, message_id=msg_id, detail="Ack delivered")
            except Exception as exc:
                return Receipt(ok=False, detail=str(exc))

        # 2. Terse mode send
        if batch.mode == "terse":
            params = {
                "chat_id": self.chat_id,
                "text": truncate_utf16(batch.message, self.caps.max_text),
                "link_preview_options": {"is_disabled": True},
            }
            try:
                sent = self._call("sendMessage", params)
                msg_id = str(sent.get("message_id")) if isinstance(sent, dict) else None
                return Receipt(ok=True, message_id=msg_id, detail="Terse batch sent")
            except (TelegramError, OSError) as err:
                detail = str(err)
                self._record_uncertain(batch, detail)
                return Receipt(ok=False, detail=detail, uncertain=True)

        # 3. Full mode send
        run_dir = self.run_dir or Path.cwd() / ".aw" / "records" / "runs" / batch.run_id
        last_msg_id: str | None = None
        for q in batch.questions:
            tokens: list[tuple[int, str]] = []
            inline_keyboard: list[list[dict[str, str]]] = []
            if q.options:
                row = []
                for idx, opt in enumerate(q.options):
                    tok = secrets.token_urlsafe(16)[:16]
                    tokens.append((idx, tok))
                    row.append(
                        {
                            "text": _truncate_bytes(opt, 64),
                            "callback_data": f"t:{tok}",
                        }
                    )
                inline_keyboard.append(row)

            reply_markup: dict[str, Any] = {}
            if inline_keyboard:
                reply_markup["inline_keyboard"] = inline_keyboard
            if q.allow_free_text:
                reply_markup["force_reply"] = True

            if q.group_id:
                header = (
                    f"run {batch.run_id} ({q.group_id}, "
                    f"{len(q.member_qids)} artifacts):"
                )
                group_kw: dict[str, Any] = {
                    "group_id": q.group_id,
                    "member_qids": list(q.member_qids),
                }
            else:
                header = f"run {batch.run_id} ({q.question_id}):"
                group_kw = {}
            lines = [header, q.text]
            if q.options:
                lines.append("Options:")
                for idx, opt in enumerate(q.options, start=1):
                    lines.append(f"  {idx}) {opt}")
            if q.answer_command:
                lines.append(q.answer_command)
            text = truncate_utf16("\n".join(lines), self.caps.max_text)

            params = {
                "chat_id": self.chat_id,
                "text": text,
                "link_preview_options": {"is_disabled": True},
            }
            if reply_markup:
                params["reply_markup"] = reply_markup

            try:
                sent = self._call("sendMessage", params)
            except (TelegramError, OSError) as err:
                detail = str(err)
                self._record_uncertain(batch, detail)
                return Receipt(ok=False, detail=detail, uncertain=True)

            msg_id = str(sent.get("message_id")) if isinstance(sent, dict) else "0"
            last_msg_id = msg_id

            # Register message_id BEFORE next send
            registry.register(
                channel="telegram",
                key=msg_id,
                run_dir=run_dir,
                question_id=q.question_id,
                option=None,
                artifact_hash="",
                **group_kw,
            )
            # Register tokens BEFORE next send
            for idx, tok in tokens:
                registry.register(
                    channel="telegram",
                    key=f"t:{tok}",
                    run_dir=run_dir,
                    question_id=q.question_id,
                    option=idx,
                    artifact_hash="",
                    **group_kw,
                )

        return Receipt(ok=True, message_id=last_msg_id, detail="Full questions sent")

    def receive(
        self, cursor: int | None, deadline: float
    ) -> tuple[list[InboundEvent], int | None]:
        remaining = max(0, int(deadline - time.time()))
        poll_timeout = min(int(self.poll_timeout_cap), remaining)
        params: dict[str, Any] = {
            "timeout": poll_timeout,
            "allowed_updates": ["message", "callback_query"],
        }
        if cursor is not None:
            params["offset"] = cursor

        result = self._call("getUpdates", params, timeout=40.0)
        if not isinstance(result, list) or not result:
            return [], cursor

        events: list[InboundEvent] = []
        for upd in result:
            ev = self._translate_update(upd)
            if ev is not None:
                events.append(ev)

        last_update_id = result[-1].get("update_id")
        next_cursor = (last_update_id + 1) if last_update_id is not None else cursor
        return events, next_cursor

    def _translate_update(self, upd: dict[str, Any]) -> InboundEvent | None:
        update_id = str(upd.get("update_id", ""))
        if "callback_query" in upd:
            cb = upd["callback_query"]
            sender = str(cb.get("from", {}).get("id", ""))
            token = cb.get("data")
            return InboundEvent(
                channel="telegram",
                event_id=update_id,
                sender=sender,
                raw=upd,
                key=token,
                choice=None,
                answer=None,
            )
        elif "message" in upd:
            msg = upd["message"]
            sender = str(msg.get("from", {}).get("id", ""))
            reply_to = msg.get("reply_to_message")
            key = (
                str(reply_to.get("message_id"))
                if isinstance(reply_to, dict) and reply_to.get("message_id")
                else None
            )
            text = msg.get("text", "")
            return InboundEvent(
                channel="telegram",
                event_id=update_id,
                sender=sender,
                raw=upd,
                key=key,
                choice=None,
                answer=text,
            )
        return None

    def verify(self, event: InboundEvent) -> str | None:
        raw = event.raw
        if not isinstance(raw, dict):
            return None

        if "callback_query" in raw:
            cb = raw["callback_query"]
            from_obj = cb.get("from", {})
            msg = cb.get("message", {})
            chat = msg.get("chat", {})
        elif "message" in raw:
            msg = raw["message"]
            from_obj = msg.get("from", {})
            chat = msg.get("chat", {})
        else:
            return None

        sender_id = str(from_obj.get("id", ""))
        is_bot = bool(from_obj.get("is_bot", False))
        chat_id = str(chat.get("id", ""))
        chat_type = str(chat.get("type", ""))

        if not self.user_id or not self.chat_id:
            return None

        if sender_id != self.user_id:
            return None
        if is_bot:
            return None
        if chat_id != self.chat_id:
            return None
        if chat_type != "private":
            return None

        return sender_id

    def ack(self, event: InboundEvent, outcome: str) -> None:
        if outcome == "ignored":
            return

        text_map = {
            "recorded": "recorded",
            "already": "already answered",
            "rejected": "not accepted",
        }
        ack_text = text_map.get(outcome, outcome)

        raw = event.raw
        if not isinstance(raw, dict):
            return

        try:
            if "callback_query" in raw:
                cb_id = raw["callback_query"].get("id")
                if cb_id:
                    self._call(
                        "answerCallbackQuery",
                        {"callback_query_id": cb_id, "text": ack_text},
                        timeout=10.0,
                    )
            elif "message" in raw:
                msg_id = raw["message"].get("message_id")
                if msg_id:
                    self._call(
                        "sendMessage",
                        {
                            "chat_id": self.chat_id,
                            "text": ack_text,
                            "reply_to_message_id": msg_id,
                            "link_preview_options": {"is_disabled": True},
                        },
                        timeout=10.0,
                    )
        except Exception:
            pass


class TelegramReceiver:
    """Daemon thread that polls Telegram and routes updates to the inbox."""

    def __init__(
        self,
        bot_id: str,
        channel: TelegramChannel,
        run_dir: Path,
        lock: FileLock | None = None,
        poll_timeout_cap: float = 25.0,
        events_path: Path | None = None,
        on_event: Any | None = None,
    ):
        self.bot_id = bot_id
        self.channel = channel
        self.run_dir = Path(run_dir)
        self.lock = lock
        self.poll_timeout_cap = poll_timeout_cap
        self.events_path = (
            Path(events_path) if events_path else self.run_dir / "events.jsonl"
        )
        self.on_event = on_event
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._stopped_event_recorded = False

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def drain_startup(self) -> None:
        """Perform start-of-run drain synchronously (R10.6, A51)."""
        offset = read_offset(self.bot_id)
        try:
            now = time.time()
            events, next_cursor = self.channel.receive(cursor=offset, deadline=now)
            stopped_early = False
            for ev in events:
                try:
                    outcome = apply_inbound(self.channel, ev)
                    if self.on_event is not None:
                        with contextlib.suppress(Exception):
                            self.on_event(ev, outcome)
                    try:
                        update_id = int(ev.event_id)
                        offset = update_id + 1
                        save_offset(self.bot_id, offset)
                    except ValueError:
                        pass
                except Exception as exc:
                    runner_shared.append_jsonl(
                        self.events_path,
                        {
                            "at": utc_now(),
                            "event": "notify-inbound-failed",
                            "channel": "telegram",
                            "update_id": int(ev.event_id)
                            if ev.event_id.isdigit()
                            else ev.event_id,
                            "detail": str(exc),
                        },
                    )
                    stopped_early = True
                    break

            if (
                not stopped_early
                and next_cursor is not None
                and (offset is None or next_cursor > offset)
            ):
                save_offset(self.bot_id, next_cursor)
        except TelegramError as err:
            if err.code in (401, 403, 409):
                remedy_map = {
                    409: "another process or machine is polling this bot; use one bot per machine",
                    401: "bot token is invalid or revoked",
                    403: "bot was blocked by user or forbidden",
                }
                remedy = remedy_map.get(err.code, "check bot configuration")
                detail = f"HTTP {err.code}: {err.description}. Remedy: {remedy}"
                runner_shared.append_jsonl(
                    self.events_path,
                    {
                        "at": utc_now(),
                        "event": "notify-receiver-stopped",
                        "channel": "telegram",
                        "reason": f"HTTP {err.code}",
                        "detail": detail,
                    },
                )
                self._stopped_event_recorded = True
                self._stop_event.set()
                self._release_lock()
        except Exception:
            pass

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run,
            name=f"telegram-receiver-{self.bot_id}",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 45.0) -> None:
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self._release_lock()
        runner_shared.unregister_active_sampler(self)

    def _release_lock(self) -> None:
        release_lock_holder(self.bot_id)
        if self.lock is not None:
            with contextlib.suppress(Exception):
                self.lock.release()
            self.lock = None

    def _run(self) -> None:
        runner_shared.append_jsonl(
            self.events_path,
            {
                "at": utc_now(),
                "event": "notify-receiver-started",
                "channel": "telegram",
            },
        )

        offset = read_offset(self.bot_id)
        delay = 1.0
        max_delay = 60.0

        try:
            while not self._stop_event.is_set():
                try:
                    now = time.time()
                    deadline = now + self.poll_timeout_cap
                    events, next_cursor = self.channel.receive(
                        cursor=offset, deadline=deadline
                    )
                    delay = 1.0

                    stopped_early = False
                    for ev in events:
                        if self._stop_event.is_set():
                            stopped_early = True
                            break
                        try:
                            outcome = apply_inbound(self.channel, ev)
                            if self.on_event is not None:
                                with contextlib.suppress(Exception):
                                    self.on_event(ev, outcome)
                            try:
                                update_id = int(ev.event_id)
                                offset = update_id + 1
                                save_offset(self.bot_id, offset)
                            except ValueError:
                                pass
                        except Exception as exc:
                            runner_shared.append_jsonl(
                                self.events_path,
                                {
                                    "at": utc_now(),
                                    "event": "notify-inbound-failed",
                                    "channel": "telegram",
                                    "update_id": int(ev.event_id)
                                    if ev.event_id.isdigit()
                                    else ev.event_id,
                                    "detail": str(exc),
                                },
                            )
                            # Stop processing the batch, back off, do NOT advance offset
                            stopped_early = True
                            self._stop_event.wait(min(delay, 2.0))
                            break

                    if (
                        not stopped_early
                        and next_cursor is not None
                        and (offset is None or next_cursor > offset)
                    ):
                        offset = next_cursor
                        save_offset(self.bot_id, offset)

                    if not events:
                        self._stop_event.wait(min(0.05, self.poll_timeout_cap))

                except TelegramError as err:
                    if self._stop_event.is_set():
                        break
                    if err.code in (401, 403, 409):
                        remedy_map = {
                            409: "another process or machine is polling this bot; use one bot per machine",
                            401: "bot token is invalid or revoked",
                            403: "bot was blocked by user or forbidden",
                        }
                        remedy = remedy_map.get(err.code, "check bot configuration")
                        detail = f"HTTP {err.code}: {err.description}. Remedy: {remedy}"
                        runner_shared.append_jsonl(
                            self.events_path,
                            {
                                "at": utc_now(),
                                "event": "notify-receiver-stopped",
                                "channel": "telegram",
                                "reason": f"HTTP {err.code}",
                                "detail": detail,
                            },
                        )
                        self._stopped_event_recorded = True
                        break
                    elif err.code == 429:
                        sleep_time = float(err.retry_after or 1.0)
                        self._stop_event.wait(sleep_time)
                    else:
                        jitter = random.uniform(0, 0.5 * delay)
                        sleep_time = min(max_delay, delay + jitter)
                        self._stop_event.wait(sleep_time)
                        delay = min(max_delay, delay * 2)
                except Exception as exc:
                    if self._stop_event.is_set():
                        break
                    runner_shared.append_jsonl(
                        self.events_path,
                        {
                            "at": utc_now(),
                            "event": "notify-failed",
                            "channel": "telegram",
                            "detail": str(exc),
                        },
                    )
                    self._stop_event.wait(min(delay, 5.0))
        finally:
            if not self._stopped_event_recorded:
                runner_shared.append_jsonl(
                    self.events_path,
                    {
                        "at": utc_now(),
                        "event": "notify-receiver-stopped",
                        "channel": "telegram",
                        "reason": "shutdown",
                    },
                )
                self._stopped_event_recorded = True
            self._release_lock()
            runner_shared.unregister_active_sampler(self)


_CURRENT_RECEIVER: TelegramReceiver | None = None
_RECEIVER_LOCK = threading.Lock()


def ensure_receiver(
    run_dir: Path | str,
    repo: Path | str | None = None,
    poll_timeout_cap: float = 25.0,
) -> TelegramReceiver | None:
    """Ensure the per-bot receiver thread is running, or attempt takeover if prior holder exited."""
    global _CURRENT_RECEIVER

    with _RECEIVER_LOCK:
        if _CURRENT_RECEIVER is not None and _CURRENT_RECEIVER.is_alive():
            return _CURRENT_RECEIVER

        eff = config.effective_channels(repo)
        if "telegram" not in eff:
            return None

        tg_cfg = eff["telegram"]
        channel = TelegramChannel(
            tg_cfg, run_dir=run_dir, poll_timeout_cap=poll_timeout_cap
        )
        if not channel.token:
            return None

        # Check webhook first (E-04)
        try:
            wh = channel._call("getWebhookInfo", timeout=10.0)
            if wh.get("url"):
                runner_shared.append_jsonl(
                    Path(run_dir) / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "notify-receiver-stopped",
                        "channel": "telegram",
                        "detail": (
                            "Webhook active; polling disabled. "
                            "Remedy: aw notify setup telegram offers deleteWebhook."
                        ),
                    },
                )
                return None
        except Exception:
            return None

        # Try to acquire per-bot lock non-blocking (E-03)
        bot_id = channel.bot_id
        lock_path = get_lock_path(bot_id)
        lock = FileLock(str(lock_path), timeout=0, thread_local=False)
        try:
            lock.acquire()
        except (Timeout, Exception):
            return None

        write_lock_holder(bot_id, os.getpid())

        receiver = TelegramReceiver(
            bot_id=bot_id,
            channel=channel,
            run_dir=Path(run_dir),
            lock=lock,
            poll_timeout_cap=poll_timeout_cap,
        )
        receiver.drain_startup()
        receiver.start()
        _CURRENT_RECEIVER = receiver
        runner_shared.register_active_sampler(receiver)
        return receiver


def stop_receiver(timeout: float = 45.0) -> None:
    """Stop the current active Telegram receiver."""
    global _CURRENT_RECEIVER

    with _RECEIVER_LOCK:
        if _CURRENT_RECEIVER is not None:
            try:
                _CURRENT_RECEIVER.stop(timeout=timeout)
            finally:
                _CURRENT_RECEIVER = None
