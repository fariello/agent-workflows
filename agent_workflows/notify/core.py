"""Core abstractions, outbound sanitization, inbound routing, and checkpoint dispatcher (spec 6kwd2e R10).

Provides the Channel protocol, OutboundBatch / InboundEvent dataclasses,
leak-sanitizing outbound pipeline (sanitize_outbound), user-level inbound routing
(apply_inbound), and the dispatch_checkpoint runner hook.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Protocol, runtime_checkable
import unicodedata
import warnings

from agent_workflows import leak_sanitizer, question_inbox, render_stream
from agent_workflows.notify import config, registry


def utc_now() -> str:
    """Current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Caps:
    """Channel capabilities."""

    max_text: int = 4096
    answer: bool = False
    buttons: bool = False


@dataclass
class Health:
    """Channel health status."""

    ok: bool
    detail: str = ""


@dataclass
class Receipt:
    """Result of sending an outbound batch or notification."""

    ok: bool
    message_id: str | None = None
    detail: str = ""


@dataclass
class InboundEvent:
    """An event received from a notification/chat channel."""

    channel: str
    event_id: str
    sender: str
    raw: Any = None
    key: str | None = None
    choice: int | None = None
    answer: str | None = None


@dataclass
class OutboundQuestion:
    """Question representation for outbound delivery."""

    question_id: str
    text: str
    options: list[str] | None = None
    allow_free_text: bool = True
    answer_command: str = ""


@dataclass
class OutboundBatch:
    """Batch of questions or status notification to be delivered off-machine."""

    run_id: str
    mode: str  # "terse" or "full"
    message: str
    questions: list[OutboundQuestion] = field(default_factory=list)


@runtime_checkable
class Channel(Protocol):
    """Protocol implemented by notification and chat channels."""

    def capabilities(self) -> Caps: ...
    def send(self, batch: OutboundBatch) -> Receipt: ...
    def health(self) -> Health: ...


_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def sanitize_outbound(
    text: str,
    repo: Path | str | None = None,
    *,
    max_text: int | None = None,
) -> str:
    """Sanitize outbound text before it leaves the machine (spec 6kwd2e R10.3).

    Pipeline guarantees:
    (1) strip ANSI escapes and control characters except newline and tab;
    (2) rewrite home paths per line with leak_sanitizer._rewrite_line;
    (3) replace every remaining absolute path with render_stream._redact_absolute_paths;
    (4) replace every remaining match of leak_sanitizer.build_ruleset(repo) fail patterns
        (session ids, private repo names, maintainer handle, user hints) with <redacted>;
    (5) re-scan with leak_sanitizer.scan_text and, if any fail finding remains, replace
        the whole field with <redacted>.
    Only THEN truncate to max_text characters with trailing '...'.
    """
    if not text:
        return ""

    # (1) Strip ANSI and control characters except \n and \t
    clean = _ANSI_RE.sub("", text)
    chars = []
    for ch in clean:
        if ch in ("\n", "\t"):
            chars.append(ch)
            continue
        code = ord(ch)
        if code < 32 or code == 127 or unicodedata.category(ch) == "Cc":
            continue
        chars.append(ch)
    clean = "".join(chars)

    # (2) Rewrite home paths per line
    lines = clean.split("\n")
    rewritten_lines = [leak_sanitizer._rewrite_line(line) for line in lines]
    clean = "\n".join(rewritten_lines)

    # (3) Replace remaining absolute paths
    clean = render_stream._redact_absolute_paths(clean)

    # (4) Replace matches of fail patterns from the active ruleset
    repo_path = Path(repo).resolve() if repo else Path.cwd().resolve()
    ruleset = leak_sanitizer.build_ruleset(repo_path)
    for pat in ruleset.fail.values():
        clean = pat.sub("<redacted>", clean)

    # (5) Re-scan and replace with <redacted> if any fail finding remains
    findings = leak_sanitizer.scan_text(clean, "outbound", ruleset)
    if any(f.severity == "fail" for f in findings):
        clean = "<redacted>"

    # Truncate after sanitizing
    if max_text is not None and max_text > 0 and len(clean) > max_text:
        cut = max(0, max_text - 3)
        clean = clean[:cut] + "..."

    return clean


def build_batch(
    run_id: str,
    questions: list[Any],
    mode: str,
    caps: Caps,
    repo: Path | str | None = None,
) -> OutboundBatch:
    """Build a sanitized OutboundBatch from open questions (spec 6kwd2e R10.4).

    In terse mode: only 'run <run-id>: N question(s) waiting; answer with aw runs answer <run-id>'.
    In full mode: additionally includes each question's sanitized text, options, and answer command.
    """
    count = len(questions)
    plural = "question" if count == 1 else "questions"
    norm_questions: list[OutboundQuestion] = []
    for q in questions:
        if isinstance(q, OutboundQuestion):
            norm_questions.append(q)
        elif isinstance(q, dict):
            qid = str(q.get("question_id") or "")
            raw_opts = q.get("options")
            opts = (
                [str(x) for x in raw_opts]
                if isinstance(raw_opts, (list, tuple))
                else None
            )
            norm_questions.append(
                OutboundQuestion(
                    question_id=qid,
                    text=str(q.get("text") or ""),
                    options=opts,
                    allow_free_text=bool(q.get("allow_free_text", True)),
                    answer_command=f"aw runs answer {run_id} {qid}",
                )
            )

    if mode == "full":
        parts = [
            f"run {run_id}: {count} {plural} waiting; answer with aw runs answer {run_id}"
        ]
        sanitized_questions: list[OutboundQuestion] = []
        for q in norm_questions:
            san_text = sanitize_outbound(q.text, repo=repo)
            san_opts = (
                [sanitize_outbound(o, repo=repo) for o in q.options]
                if q.options is not None
                else None
            )
            san_q = OutboundQuestion(
                question_id=q.question_id,
                text=san_text,
                options=san_opts,
                allow_free_text=q.allow_free_text,
                answer_command=f"aw runs answer {run_id} {q.question_id}",
            )
            sanitized_questions.append(san_q)

            parts.append("")
            parts.append(f"Question: {q.question_id}")
            parts.append(san_text)
            if san_opts:
                parts.append("Options:")
                for idx, opt in enumerate(san_opts, start=1):
                    parts.append(f"  {idx}) {opt}")
            parts.append(f"aw runs answer {run_id} {q.question_id}")

        full_message = "\n".join(parts)
        message = sanitize_outbound(full_message, repo=repo, max_text=caps.max_text)
        return OutboundBatch(
            run_id=run_id,
            mode="full",
            message=message,
            questions=sanitized_questions,
        )
    else:
        # Terse mode: no question text or options
        terse_message = f"run {run_id}: {count} {plural} waiting; answer with aw runs answer {run_id}"
        message = sanitize_outbound(terse_message, repo=repo, max_text=caps.max_text)
        return OutboundBatch(
            run_id=run_id,
            mode="terse",
            message=message,
            questions=norm_questions,
        )


def apply_inbound(channel: Any, event: InboundEvent) -> str:
    """Apply an inbound event from a two-way channel to the question inbox.

    Returns one of: 'recorded', 'already', 'rejected', 'ignored'.
    - duplicate event id: 'ignored'
    - unverified sender: 'ignored' (logged, no answer written)
    - unknown routing key: 'rejected'
    - verified event: written via question_inbox.write_answer with actor='human'
    """
    channel_name = getattr(channel, "name", event.channel)

    # 1. Duplicate event check
    if registry.seen_event(channel_name, event.event_id):
        return "ignored"

    # 2. Sender verification
    verify_fn = getattr(channel, "verify", None)
    if not callable(verify_fn):
        return "ignored"

    sender = verify_fn(event)
    if sender is None:
        warnings.warn(
            f"Unverified sender in inbound event {event.event_id} on {channel_name}; ignoring",
            UserWarning,
            stacklevel=2,
        )
        return "ignored"

    # 3. Resolve routing key
    if not event.key:
        return "rejected"

    route = registry.lookup(channel_name, event.key)
    if route is None:
        return "rejected"

    run_dir = Path(route["run_dir"])
    qid = route["question_id"]
    option = route.get("option")
    choice = option if option is not None else event.choice
    answer = event.answer

    # 4. Write answer through shared answer writer
    ans_res = question_inbox.write_answer(
        run_dir,
        qid,
        answer=answer,
        choice=choice,
        channel=channel_name,
        sender=str(sender),
        actor="human",
    )
    outcome = ans_res.status  # 'recorded', 'already', or 'rejected'

    ack_fn = getattr(channel, "ack", None)
    if callable(ack_fn):
        with contextlib.suppress(Exception):
            ack_fn(event, outcome)

    return outcome


def get_channel(channel_name: str, c_cfg: dict[str, Any]) -> Channel:
    """Instantiate a channel adapter by name."""
    if channel_name == "webhook":
        from agent_workflows.notify.webhook import WebhookChannel

        return WebhookChannel(c_cfg)
    elif channel_name == "command":
        from agent_workflows.notify.webhook import CommandChannel

        return CommandChannel(c_cfg)
    else:
        raise ValueError(f"Unknown notification channel {channel_name!r}")


def _redact_secrets(detail: str, c_cfg: dict[str, Any]) -> str:
    """Redact secret strings such as webhook URLs from failure details."""
    url = c_cfg.get("url")
    if url and isinstance(url, str):
        from agent_workflows.notify.webhook import safe_url_summary

        summary = safe_url_summary(url)
        detail = detail.replace(url, summary)
    return detail


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    return records


def dispatch_checkpoint(
    run_dir: Path | str,
    state: dict[str, Any],
    repo: Path | str | None = None,
) -> None:
    """Run notification checkpoint dispatch across all effective channels (spec 6kwd2e R10.7).

    Called at top of run_queue and immediately before run summary rendering.
    With no effective channel, does nothing and writes nothing.
    """
    run_dir = Path(run_dir).resolve()
    if repo is None:
        repo = Path(state.get("repo") or Path.cwd()).resolve()
    repo = Path(repo).resolve()

    # Tracked secret warnings: print once per run if present
    tracked_warnings = config.tracked_secret_warnings(repo)
    if tracked_warnings and not state.get("_notify_tracked_warnings_printed"):
        for tw in tracked_warnings:
            print(f"WARNING: {tw}", file=sys.stderr)
        state["_notify_tracked_warnings_printed"] = True

    effective = config.effective_channels(repo)
    if not effective:
        return

    notify_dir = run_dir / "notify"
    sent_file = notify_dir / "sent.jsonl"
    events_file = run_dir / "events.jsonl"

    sent_records = _read_jsonl(sent_file)
    sent_questions = {
        (r.get("channel"), r.get("question_id"))
        for r in sent_records
        if r.get("type", "question") == "question"
    }
    sent_acks = {
        (r.get("channel"), r.get("question_id"))
        for r in sent_records
        if r.get("type") == "ack"
    }

    # 1. Read open questions
    open_qs = question_inbox.read_open_questions(run_dir)
    run_id = str(state.get("run_id") or run_dir.name)

    # 2. Send newly parked batch per channel
    for ch_name, ch_cfg in effective.items():
        try:
            channel = get_channel(ch_name, ch_cfg)
        except Exception as exc:
            detail = _redact_secrets(str(exc), ch_cfg)
            _append_jsonl(
                events_file,
                {
                    "at": utc_now(),
                    "event": "notify-failed",
                    "channel": ch_name,
                    "detail": detail,
                },
            )
            continue

        caps = channel.capabilities()
        new_qs = [
            q for q in open_qs if (ch_name, q.get("question_id")) not in sent_questions
        ]
        if new_qs:
            batch = build_batch(
                run_id=run_id,
                questions=new_qs,
                mode=ch_cfg.get("mode", "terse"),
                caps=caps,
                repo=repo,
            )
            try:
                receipt = channel.send(batch)
                if receipt.ok:
                    for q in new_qs:
                        _append_jsonl(
                            sent_file,
                            {
                                "channel": ch_name,
                                "question_id": q["question_id"],
                                "type": "question",
                                "at": utc_now(),
                                "message_id": receipt.message_id,
                            },
                        )
                    _append_jsonl(
                        events_file,
                        {
                            "at": utc_now(),
                            "event": "notify-sent",
                            "channel": ch_name,
                            "count": len(new_qs),
                        },
                    )
                else:
                    detail = _redact_secrets(receipt.detail, ch_cfg)
                    _append_jsonl(
                        events_file,
                        {
                            "at": utc_now(),
                            "event": "notify-failed",
                            "channel": ch_name,
                            "detail": detail,
                        },
                    )
            except Exception as exc:
                detail = _redact_secrets(str(exc), ch_cfg)
                _append_jsonl(
                    events_file,
                    {
                        "at": utc_now(),
                        "event": "notify-failed",
                        "channel": ch_name,
                        "detail": detail,
                    },
                )

    # 3. Check for consumed or stale answers needing acknowledgement
    events = _read_jsonl(events_file)
    consumed_events: dict[str, dict[str, Any]] = {}
    stale_events: dict[str, dict[str, Any]] = {}
    for ev in events:
        ev_name = ev.get("event")
        qid = ev.get("question_id")
        if not qid:
            continue
        if ev_name == "answer-consumed":
            consumed_events[qid] = ev
        elif ev_name == "answer-stale":
            stale_events[qid] = ev

    # Re-read sent_records in case new questions were sent above
    sent_records = _read_jsonl(sent_file)
    sent_questions = {
        (r.get("channel"), r.get("question_id"))
        for r in sent_records
        if r.get("type", "question") == "question"
    }
    sent_acks = {
        (r.get("channel"), r.get("question_id"))
        for r in sent_records
        if r.get("type") == "ack"
    }

    for ch_name, qid in sent_questions:
        if (ch_name, qid) in sent_acks:
            continue
        if ch_name not in effective:
            continue

        ch_cfg = effective[ch_name]
        try:
            channel = get_channel(ch_name, ch_cfg)
        except Exception:
            continue

        caps = channel.capabilities()
        ack_text: str | None = None
        ack_status: str | None = None

        if qid in consumed_events:
            ans_channel = consumed_events[qid].get("channel") or "terminal"
            ack_text = f"run {run_id} ({qid}): answered via {ans_channel}"
            ack_status = "consumed"
        elif qid in stale_events:
            ack_text = (
                f"run {run_id} ({qid}): answer not applied: the plan changed; ask again"
            )
            ack_status = "stale"

        if ack_text is not None and ack_status is not None:
            ack_batch = OutboundBatch(
                run_id=run_id,
                mode="terse",
                message=sanitize_outbound(ack_text, repo=repo, max_text=caps.max_text),
                questions=[],
            )
            try:
                receipt = channel.send(ack_batch)
                if receipt.ok:
                    _append_jsonl(
                        sent_file,
                        {
                            "channel": ch_name,
                            "question_id": qid,
                            "type": "ack",
                            "status": ack_status,
                            "at": utc_now(),
                        },
                    )
                else:
                    detail = _redact_secrets(receipt.detail, ch_cfg)
                    _append_jsonl(
                        events_file,
                        {
                            "at": utc_now(),
                            "event": "notify-failed",
                            "channel": ch_name,
                            "detail": detail,
                        },
                    )
            except Exception as exc:
                detail = _redact_secrets(str(exc), ch_cfg)
                _append_jsonl(
                    events_file,
                    {
                        "at": utc_now(),
                        "event": "notify-failed",
                        "channel": ch_name,
                        "detail": detail,
                    },
                )
