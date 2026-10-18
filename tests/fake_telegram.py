"""Fake Telegram Bot API HTTP server for tests (qchan-10 qrup8m E-05).

Runs an http.server on loopback emulating Telegram Bot API endpoints:
getMe, getWebhookInfo, sendMessage, getUpdates, answerCallbackQuery,
editMessageReplyMarkup, and records every request.
"""

from __future__ import annotations

import contextlib
import http.server
import json
import threading
from typing import Any


class _FakeHTTPServer(http.server.ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        RequestHandlerClass: Any,
        fake_telegram_server: FakeTelegramServer,
    ):
        super().__init__(server_address, RequestHandlerClass)
        self.fake = fake_telegram_server


class FakeTelegramHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for FakeTelegramServer."""

    @property
    def fake(self) -> FakeTelegramServer:
        return getattr(self.server, "fake")

    def log_message(self, format: str, *args: Any) -> None:
        """Silence standard request logging."""
        pass

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len) if content_len > 0 else b""
        body: dict[str, Any] = {}
        if body_bytes:
            try:
                body = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                pass

        # Path is expected to be /bot<token>/<method>
        path_parts = self.path.strip("/").split("/")
        token = ""
        api_method = ""
        if len(path_parts) >= 2 and path_parts[0].startswith("bot"):
            token = path_parts[0][3:]
            api_method = path_parts[1]
        elif len(path_parts) == 1:
            api_method = path_parts[0]

        record = {
            "path": self.path,
            "method": self.command,
            "token": token,
            "api_method": api_method,
            "headers": dict(self.headers),
            "body": body,
        }
        self.fake.requests.append(record)

        if "invalid" in token:
            self._send_json(
                401,
                {"ok": False, "error_code": 401, "description": "Unauthorized"},
            )
            return

        if api_method == "getMe":
            self._send_json(
                200,
                {
                    "ok": True,
                    "result": {
                        "id": 123456789,
                        "is_bot": True,
                        "first_name": "FakeTestBot",
                        "username": self.fake.bot_username,
                    },
                },
            )
        elif api_method == "getWebhookInfo":
            self._send_json(
                200,
                {
                    "ok": True,
                    "result": {
                        "url": self.fake.webhook_url,
                        "has_custom_certificate": False,
                        "pending_update_count": 0,
                    },
                },
            )
        elif api_method == "deleteWebhook":
            self.fake.webhook_url = ""
            self._send_json(200, {"ok": True, "result": True})
        elif api_method == "sendMessage":
            if self.fake.scripted_send_message:
                action = self.fake.scripted_send_message.pop(0)
                if action == "timeout":
                    return
                elif isinstance(action, int) and action >= 400:
                    self._send_json(
                        action,
                        {
                            "ok": False,
                            "error_code": action,
                            "description": f"HTTP {action} error",
                        },
                    )
                    return
            msg_id = self.fake.next_message_id
            self.fake.next_message_id += 1
            self.fake.sent_messages.append({"message_id": msg_id, **body})
            self._send_json(
                200,
                {
                    "ok": True,
                    "result": {
                        "message_id": msg_id,
                        "chat": {"id": body.get("chat_id")},
                        "text": body.get("text"),
                    },
                },
            )
        elif api_method == "getUpdates":
            if self.fake.scripted_get_updates:
                action = self.fake.scripted_get_updates.pop(0)
                if action == 409:
                    self._send_json(
                        409,
                        {
                            "ok": False,
                            "error_code": 409,
                            "description": "Conflict: can't use getUpdates method while another poller is active",
                        },
                    )
                    return
                elif action == 401:
                    self._send_json(
                        401,
                        {"ok": False, "error_code": 401, "description": "Unauthorized"},
                    )
                    return
                elif action == 403:
                    self._send_json(
                        403,
                        {"ok": False, "error_code": 403, "description": "Forbidden"},
                    )
                    return
                elif isinstance(action, tuple) and action[0] == 429:
                    retry_after = action[1]
                    self._send_json(
                        429,
                        {
                            "ok": False,
                            "error_code": 429,
                            "description": "Too Many Requests",
                            "parameters": {"retry_after": retry_after},
                        },
                    )
                    return
                elif action == 500:
                    self._send_json(
                        500,
                        {
                            "ok": False,
                            "error_code": 500,
                            "description": "Internal Server Error",
                        },
                    )
                    return

            offset = body.get("offset")
            updates: list[dict[str, Any]] = []
            for u in self.fake.updates_queue:
                if offset is None or u.get("update_id", 0) >= offset:
                    updates.append(u)
            self._send_json(200, {"ok": True, "result": updates})
        elif api_method == "answerCallbackQuery":
            self.fake.callback_answers.append(body)
            self._send_json(200, {"ok": True, "result": True})
        elif api_method == "editMessageReplyMarkup":
            self.fake.reply_markup_edits.append(body)
            self._send_json(200, {"ok": True, "result": True})
        else:
            self._send_json(
                404,
                {
                    "ok": False,
                    "error_code": 404,
                    "description": f"Unknown method {api_method}",
                },
            )


class FakeTelegramServer:
    """Threaded loopback HTTP server emulating Telegram Bot API."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self.host = host
        self.port = port
        self.bot_username = "fake_bot"
        self.webhook_url = ""
        self.next_message_id = 1000
        self.requests: list[dict[str, Any]] = []
        self.sent_messages: list[dict[str, Any]] = []
        self.updates_queue: list[dict[str, Any]] = []
        self.scripted_get_updates: list[Any] = []
        self.scripted_send_message: list[Any] = []
        self.callback_answers: list[dict[str, Any]] = []
        self.reply_markup_edits: list[dict[str, Any]] = []
        self._httpd: _FakeHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._httpd = _FakeHTTPServer((self.host, self.port), FakeTelegramHandler, self)
        self.port = self._httpd.server_port
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def add_button_update(
        self,
        update_id: int,
        user_id: int | str,
        chat_id: int | str,
        message_id: int,
        callback_data: str,
        callback_id: str = "cb_123",
        is_bot: bool = False,
        chat_type: str = "private",
    ) -> dict[str, Any]:
        """Enqueue a callback query button press update."""
        update = {
            "update_id": update_id,
            "callback_query": {
                "id": callback_id,
                "from": {
                    "id": int(user_id) if str(user_id).isdigit() else user_id,
                    "is_bot": is_bot,
                    "first_name": "TestUser",
                },
                "message": {
                    "message_id": message_id,
                    "chat": {
                        "id": int(chat_id) if str(chat_id).isdigit() else chat_id,
                        "type": chat_type,
                    },
                },
                "data": callback_data,
            },
        }
        self.updates_queue.append(update)
        return update

    def add_text_update(
        self,
        update_id: int,
        user_id: int | str,
        chat_id: int | str,
        text: str,
        reply_to_message_id: int | None = None,
        chat_type: str = "private",
        is_bot: bool = False,
    ) -> dict[str, Any]:
        """Enqueue a text message update (optionally replying to reply_to_message_id)."""
        msg: dict[str, Any] = {
            "message_id": 2000 + update_id,
            "from": {
                "id": int(user_id) if str(user_id).isdigit() else user_id,
                "is_bot": is_bot,
                "first_name": "TestUser",
            },
            "chat": {
                "id": int(chat_id) if str(chat_id).isdigit() else chat_id,
                "type": chat_type,
            },
            "text": text,
        }
        if reply_to_message_id is not None:
            msg["reply_to_message"] = {"message_id": reply_to_message_id}

        update = {"update_id": update_id, "message": msg}
        self.updates_queue.append(update)
        return update


@contextlib.contextmanager
def run_fake_telegram(host: str = "127.0.0.1"):
    server = FakeTelegramServer(host=host)
    server.start()
    try:
        yield server
    finally:
        server.stop()
