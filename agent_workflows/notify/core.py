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
    uncertain: bool = False


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
    """Question representation for outbound delivery.

    A grouped entry (one deduplicated ``question_inbox.QuestionGroup``) carries
    ``group_id``; its ``question_id`` is the group's REPRESENTATIVE member qid
    (``QuestionGroup.oq_id``), ``member_qids`` names every member question,
    ``raisers`` the distinct raiser artifact id6s, and ``unblock_count`` the
    group's unblock count. An ungrouped entry leaves ``group_id`` as None.
    """

    question_id: str
    text: str
    options: list[str] | None = None
    allow_free_text: bool = True
    answer_command: str = ""
    group_id: str | None = None
    member_qids: list[str] = field(default_factory=list)
    raisers: list[str] = field(default_factory=list)
    unblock_count: int = 0


@dataclass
class OutboundBatch:
    """Batch of questions or status notification to be delivered off-machine.

    ``question_count`` is the total number of open member questions the batch
    reports (spec 6kwd2e R10.4's N). ``None`` means ``len(questions)``, which is
    the meaning every ungrouped batch already has.
    """

    run_id: str
    mode: str  # "terse" or "full"
    message: str
    questions: list[OutboundQuestion] = field(default_factory=list)
    question_count: int | None = None

    @property
    def total_questions(self) -> int:
        """Number of open member questions this batch reports."""
        if self.question_count is not None:
            return self.question_count
        return len(self.questions)


# Maximum number of raiser id6s listed in a full-mode group entry.
MAX_LISTED_RAISERS = 10


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

    ``questions`` may mix ``OutboundQuestion`` objects, question-record dicts, and
    ``question_inbox.QuestionGroup`` objects. Each group becomes ONE entry whose
    answer command is ``aw runs answer <run-id> --group <group-id>`` and N counts
    every member question. Input order is preserved as given (never re-sorted).
    """
    norm_questions: list[OutboundQuestion] = []
    count = 0
    for q in questions:
        if isinstance(q, question_inbox.QuestionGroup):
            member_qids = [m.question_id for m in q.members if m.question_id]
            norm_questions.append(
                OutboundQuestion(
                    question_id=q.oq_id,
                    text=str(q.text or ""),
                    options=(
                        [str(x) for x in q.options] if q.options is not None else None
                    ),
                    allow_free_text=bool(q.allow_free_text),
                    answer_command=f"aw runs answer {run_id} --group {q.group_id}",
                    group_id=q.group_id,
                    member_qids=member_qids,
                    raisers=list(q.raisers),
                    unblock_count=int(q.unblock_count),
                )
            )
            count += max(1, q.member_count)
        elif isinstance(q, OutboundQuestion):
            norm_questions.append(q)
            count += max(1, len(q.member_qids)) if q.group_id else 1
        elif isinstance(q, dict):
            count += 1
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

    plural = "question" if count == 1 else "questions"

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
            if q.group_id:
                answer_command = f"aw runs answer {run_id} --group {q.group_id}"
            else:
                answer_command = f"aw runs answer {run_id} {q.question_id}"
            san_q = OutboundQuestion(
                question_id=q.question_id,
                text=san_text,
                options=san_opts,
                allow_free_text=q.allow_free_text,
                answer_command=answer_command,
                group_id=q.group_id,
                member_qids=list(q.member_qids),
                raisers=list(q.raisers),
                unblock_count=q.unblock_count,
            )
            sanitized_questions.append(san_q)

            parts.append("")
            if q.group_id:
                parts.append(f"Question: {q.group_id}")
                listed = q.raisers[:MAX_LISTED_RAISERS]
                raiser_line = (
                    f"Asked by {len(q.raisers)} artifact(s): {', '.join(listed)}"
                )
                if len(q.raisers) > len(listed):
                    raiser_line += f" and {len(q.raisers) - len(listed)} more"
                parts.append(raiser_line)
                parts.append(f"Unblocks: {q.unblock_count}")
            else:
                parts.append(f"Question: {q.question_id}")
            parts.append(san_text)
            if san_opts:
                parts.append("Options:")
                for idx, opt in enumerate(san_opts, start=1):
                    parts.append(f"  {idx}) {opt}")
            parts.append(answer_command)

        full_message = "\n".join(parts)
        message = sanitize_outbound(full_message, repo=repo, max_text=caps.max_text)
        return OutboundBatch(
            run_id=run_id,
            mode="full",
            message=message,
            questions=sanitized_questions,
            question_count=count,
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
            question_count=count,
        )


def _apply_group_route(
    run_dir: Path,
    representative_qid: str,
    *,
    answer: str | None,
    choice: int | None,
    channel_name: str,
    sender: str,
) -> str | None:
    """Answer the CURRENT open group containing a group route's representative qid.

    The group id stored on a route is NOT a stable key: collision-split ids
    (``g-<fp>-<n>``) are renumbered when another same-fingerprint question parks,
    so the stored id can name a different question than the one the human saw.
    The representative member qid is stable, so the group is re-resolved by
    membership. Returns the ``write_group_answer`` status, or None when no open
    group contains the representative qid (the caller then falls back to
    ``write_answer`` on that qid, which reports 'already' or 'rejected' truthfully).

    ``write_group_answer`` is NOT atomic across members: each member is
    first-answer-wins under its own per-question lock, so a member answered
    concurrently elsewhere keeps that answer while the rest record this one.
    """
    from agent_workflows import runner_shared

    state: dict[str, Any] | None = None
    if (run_dir / "state.json").is_file():
        try:
            state = runner_shared.load_state(run_dir)
        except Exception:
            state = None
    groups = question_inbox.group_open_questions(run_dir, state)
    current = next(
        (
            g
            for g in groups
            if any(m.question_id == representative_qid for m in g.members)
        ),
        None,
    )
    if current is None:
        return None
    res = question_inbox.write_group_answer(
        run_dir,
        state,
        current.group_id,
        answer=answer,
        choice=choice,
        channel=channel_name,
        sender=sender,
        actor="human",
    )
    return res.status


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
        ack_fn = getattr(channel, "ack", None)
        if callable(ack_fn):
            with contextlib.suppress(Exception):
                ack_fn(event, "rejected")
        return "rejected"

    route = registry.lookup(channel_name, event.key)
    if route is None:
        ack_fn = getattr(channel, "ack", None)
        if callable(ack_fn):
            with contextlib.suppress(Exception):
                ack_fn(event, "rejected")
        return "rejected"

    run_dir = Path(route["run_dir"])
    qid = route["question_id"]
    option = route.get("option")
    choice = option if option is not None else event.choice
    answer = event.answer

    # 4. Write answer through shared answer writer
    outcome: str | None = None
    if route.get("group_id"):
        outcome = _apply_group_route(
            run_dir,
            qid,
            answer=answer,
            choice=choice,
            channel_name=channel_name,
            sender=str(sender),
        )
    if outcome is None:
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
    elif channel_name == "telegram":
        from agent_workflows.notify.telegram import TelegramChannel

        return TelegramChannel(c_cfg)
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

    if "telegram" in effective:
        with contextlib.suppress(Exception):
            from agent_workflows.notify import telegram as notify_telegram

            notify_telegram.ensure_receiver(run_dir, repo=repo)

    notify_dir = run_dir / "notify"
    sent_file = notify_dir / "sent.jsonl"
    events_file = run_dir / "events.jsonl"

    sent_records = _read_jsonl(sent_file)
    sent_questions = {
        (r.get("channel"), r.get("question_id"))
        for r in sent_records
        if r.get("type", "question") == "question"
    }

    # 1. Read open questions, deduplicated into groups (spec 6kwd2e R4). The
    #    grouping is the same one `aw runs answer --group` recomputes, so a group
    #    id printed in a notification is one the CLI resolves.
    run_id = str(state.get("run_id") or run_dir.name)
    groups = question_inbox.group_open_questions(run_dir, state)
    covered = {m.question_id for g in groups for m in g.members if m.question_id}
    # A question no group covers (group_open_questions narrows to the current
    # park's question_ids while a non-parked item may still hold an open
    # question) keeps today's per-question rendering, so nothing stops being
    # notified.
    uncovered = [
        q
        for q in question_inbox.read_open_questions(run_dir)
        if q.get("question_id") and q.get("question_id") not in covered
    ]
    # (entry for build_batch, member qids, group id or None, representative qid)
    entries: list[tuple[Any, list[str], str | None, str]] = []
    for g in groups:
        member_qids = [m.question_id for m in g.members if m.question_id]
        if member_qids:
            entries.append((g, member_qids, g.group_id, g.oq_id))
    for q in uncovered:
        qid = str(q["question_id"])
        entries.append((q, [qid], None, qid))

    def _sent_rows(
        ch_name: str,
        selected: list[tuple[Any, list[str], str | None, str]],
        extra: dict[str, Any],
    ) -> None:
        for _obj, member_qids, gid, rep in selected:
            for mqid in member_qids:
                row: dict[str, Any] = {
                    "channel": ch_name,
                    "question_id": mqid,
                    "type": "question",
                    "at": utc_now(),
                }
                if gid is not None:
                    row["group_id"] = gid
                    row["representative_qid"] = rep
                row.update(extra)
                _append_jsonl(sent_file, row)

    # 2. Send newly parked batch per channel (one batch per channel per checkpoint)
    for ch_name, ch_cfg in effective.items():
        try:
            channel = get_channel(ch_name, ch_cfg)
            if (
                hasattr(channel, "run_dir")
                and getattr(channel, "run_dir", None) is None
            ):
                channel.run_dir = run_dir  # type: ignore[attr-defined]
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
        # A group is NEW for a channel when any member lacks a sent row; it is
        # then rendered with ALL its current members.
        new_entries = [
            e
            for e in entries
            if any((ch_name, mqid) not in sent_questions for mqid in e[1])
        ]
        if new_entries:
            member_total = sum(len(e[1]) for e in new_entries)
            batch = build_batch(
                run_id=run_id,
                questions=[e[0] for e in new_entries],
                mode=ch_cfg.get("mode", "terse"),
                caps=caps,
                repo=repo,
            )
            try:
                receipt = channel.send(batch)
                if receipt.ok:
                    _sent_rows(ch_name, new_entries, {"message_id": receipt.message_id})
                    _append_jsonl(
                        events_file,
                        {
                            "at": utc_now(),
                            "event": "notify-sent",
                            "channel": ch_name,
                            "count": member_total,
                        },
                    )
                else:
                    detail = _redact_secrets(receipt.detail, ch_cfg)
                    ev_type = (
                        "notify-uncertain"
                        if getattr(receipt, "uncertain", False)
                        else "notify-failed"
                    )
                    _append_jsonl(
                        events_file,
                        {
                            "at": utc_now(),
                            "event": ev_type,
                            "channel": ch_name,
                            "detail": detail,
                        },
                    )
                    if getattr(receipt, "uncertain", False):
                        _sent_rows(ch_name, new_entries, {"uncertain": True})
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
    sent_questions = set()
    # Latest (group_id, representative qid) recorded per (channel, qid).
    sent_group: dict[tuple[Any, Any], tuple[str, str]] = {}
    for r in sent_records:
        if r.get("type", "question") != "question":
            continue
        key = (r.get("channel"), r.get("question_id"))
        sent_questions.add(key)
        gid = r.get("group_id")
        if gid:
            sent_group[key] = (
                str(gid),
                str(r.get("representative_qid") or r.get("question_id")),
            )
        else:
            sent_group.pop(key, None)
    sent_acks = {
        (r.get("channel"), r.get("question_id"))
        for r in sent_records
        if r.get("type") == "ack"
    }

    # Bucket pending acknowledgements: one per (channel, group, status); an
    # ungrouped qid is its own bucket, so it keeps today's per-question ack.
    buckets: dict[tuple[str, str, str], dict[str, Any]] = {}
    for ch_name, qid in sorted(sent_questions, key=lambda k: (str(k[0]), str(k[1]))):
        if (ch_name, qid) in sent_acks:
            continue
        if ch_name not in effective:
            continue
        if qid in consumed_events:
            ack_status = "consumed"
        elif qid in stale_events:
            ack_status = "stale"
        else:
            continue
        grp = sent_group.get((ch_name, qid))
        bucket_key = (str(ch_name), f"g:{grp[0]}" if grp else f"q:{qid}", ack_status)
        bucket = buckets.setdefault(
            bucket_key,
            {
                "channel": ch_name,
                "status": ack_status,
                "representative": grp[1] if grp else qid,
                "qids": [],
            },
        )
        bucket["qids"].append(qid)

    for bucket_key in sorted(buckets):
        bucket = buckets[bucket_key]
        ch_name = bucket["channel"]
        ack_status = bucket["status"]
        rep = bucket["representative"]
        qids = bucket["qids"]

        ch_cfg = effective[ch_name]
        try:
            channel = get_channel(ch_name, ch_cfg)
        except Exception:
            continue

        caps = channel.capabilities()
        if ack_status == "consumed":
            first = next(q for q in qids if q in consumed_events)
            ans_channel = consumed_events[first].get("channel") or "terminal"
            ack_text = f"run {run_id} ({rep}): answered via {ans_channel}"
            if len(qids) > 1:
                ack_text += f" (applied to {len(qids)} questions)"
        else:
            ack_text = (
                f"run {run_id} ({rep}): answer not applied: the plan changed; ask again"
            )

        ack_batch = OutboundBatch(
            run_id=run_id,
            mode="terse",
            message=sanitize_outbound(ack_text, repo=repo, max_text=caps.max_text),
            questions=[OutboundQuestion(question_id=rep, text="")] if rep else [],
        )
        try:
            receipt = channel.send(ack_batch)
            if receipt.ok:
                for qid in qids:
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
