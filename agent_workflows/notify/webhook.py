"""Notify-only webhook and command channels (spec 6kwd2e R10.8b).

Webhook channel supports aw (aw.notify/v1 JSON), text (plain chat webhook JSON),
and ntfy (plain-text body with Title/Tags headers).
Command channel executes a configured argv list with the JSON body on stdin.
Neither implements receive and neither writes answers/ directly.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from agent_workflows.notify.core import (
    Caps,
    Health,
    OutboundBatch,
    Receipt,
)


def safe_url_summary(url: str) -> str:
    """Return only scheme://netloc for a URL, keeping path, query, and credentials hidden."""
    try:
        p = urllib.parse.urlsplit(url)
        netloc = p.netloc.split("@")[-1]
        scheme = p.scheme or "https"
        return f"{scheme}://{netloc}"
    except Exception:
        return "<url>"


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse HTTP redirects so requests are never silently forwarded."""

    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> Any:
        return None


class WebhookChannel:
    """Generic incoming webhook notification channel."""

    def __init__(self, config: dict[str, Any]):
        self.url = str(config.get("url") or "").strip()
        self.format = str(config.get("format") or "aw").lower()
        self.mode = str(config.get("mode") or "terse")
        self.name = "webhook"

    def capabilities(self) -> Caps:
        return Caps(max_text=4096, answer=False, buttons=False)

    def health(self) -> Health:
        if not self.url:
            return Health(ok=False, detail="No webhook URL configured")
        summary = safe_url_summary(self.url)
        p = urllib.parse.urlsplit(self.url)
        scheme = p.scheme.lower()
        host = (p.hostname or "").lower()
        loopback = host in ("127.0.0.1", "::1", "localhost")
        if scheme != "https" and not (scheme == "http" and loopback):
            return Health(
                ok=False, detail=f"Non-HTTPS URL on non-loopback host {summary}"
            )
        return Health(
            ok=True, detail=f"Configured for {summary} (format={self.format})"
        )

    def send(self, batch: OutboundBatch) -> Receipt:
        if not self.url:
            return Receipt(ok=False, detail="No webhook URL configured")

        summary = safe_url_summary(self.url)
        p = urllib.parse.urlsplit(self.url)
        scheme = p.scheme.lower()
        host = (p.hostname or "").lower()
        loopback = host in ("127.0.0.1", "::1", "localhost")
        if scheme != "https" and not (scheme == "http" and loopback):
            return Receipt(
                ok=False,
                detail=f"Refusing non-HTTPS URL on non-loopback host: {summary}",
            )

        if self.format == "ntfy":
            body_bytes = batch.message.encode("utf-8")
            headers = {
                "Content-Type": "text/plain; charset=utf-8",
                "Title": f"Run {batch.run_id} questions waiting",
                "Tags": "question,warning",
            }
        elif self.format == "text":
            body_bytes = json.dumps({"text": batch.message}).encode("utf-8")
            headers = {"Content-Type": "application/json; charset=utf-8"}
        else:  # "aw" format default
            q_list = []
            if batch.mode == "full":
                for q in batch.questions:
                    q_list.append(
                        {
                            "question_id": q.question_id,
                            "text": q.text,
                            "options": q.options,
                            "allow_free_text": q.allow_free_text,
                            "answer_command": q.answer_command,
                        }
                    )
            payload = {
                "schema": "aw.notify/v1",
                "run_id": batch.run_id,
                "mode": batch.mode,
                "count": len(batch.questions),
                "message": batch.message,
                "questions": q_list,
            }
            body_bytes = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json; charset=utf-8"}

        opener = urllib.request.build_opener(_NoRedirectHandler)
        req = urllib.request.Request(
            self.url, data=body_bytes, headers=headers, method="POST"
        )
        try:
            with opener.open(req, timeout=10) as resp:
                msg_id = resp.headers.get("X-Message-ID")
                return Receipt(
                    ok=True, message_id=msg_id, detail=f"Delivered to {summary}"
                )
        except urllib.error.HTTPError as err:
            return Receipt(ok=False, detail=f"HTTP {err.code} from {summary}")
        except Exception as exc:
            return Receipt(
                ok=False, detail=f"Request to {summary} failed: {type(exc).__name__}"
            )


class CommandChannel:
    """Command hook notification channel that pipes notification JSON to stdin."""

    def __init__(self, config: dict[str, Any]):
        cmd = config.get("command") or []
        self.command = [str(x) for x in cmd] if isinstance(cmd, list) else []
        self.mode = str(config.get("mode") or "terse")
        self.name = "command"

    def capabilities(self) -> Caps:
        return Caps(max_text=4096, answer=False, buttons=False)

    def health(self) -> Health:
        if not self.command:
            return Health(ok=False, detail="No command configured")
        return Health(ok=True, detail=f"Configured with {self.command[0]}")

    def send(self, batch: OutboundBatch) -> Receipt:
        if not self.command:
            return Receipt(ok=False, detail="No command configured")

        q_list = []
        if batch.mode == "full":
            for q in batch.questions:
                q_list.append(
                    {
                        "question_id": q.question_id,
                        "text": q.text,
                        "options": q.options,
                        "allow_free_text": q.allow_free_text,
                        "answer_command": q.answer_command,
                    }
                )
        payload = {
            "schema": "aw.notify/v1",
            "run_id": batch.run_id,
            "mode": batch.mode,
            "count": len(batch.questions),
            "message": batch.message,
            "questions": q_list,
        }
        input_bytes = json.dumps(payload).encode("utf-8")

        try:
            proc = subprocess.run(
                self.command,
                input=input_bytes,
                timeout=30,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if proc.returncode != 0:
                return Receipt(
                    ok=False,
                    detail=f"Command {self.command[0]} exited with code {proc.returncode}",
                )
            return Receipt(ok=True, detail=f"Command {self.command[0]} succeeded")
        except subprocess.TimeoutExpired:
            return Receipt(
                ok=False, detail=f"Command {self.command[0]} timed out after 30s"
            )
        except Exception as exc:
            return Receipt(
                ok=False,
                detail=f"Command {self.command[0]} failed: {type(exc).__name__}",
            )
