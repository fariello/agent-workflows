"""Agent-side comms acknowledgement writing and per-message status aggregation (IPD ozcfjr).

This module provides stdlib-only utilities for:
1. Target-agent acknowledgement writing (comms.AGENT_ACK_STATES only) to untracked/acks/.
2. Per-message status aggregation across broker delivery observations and agent work states.
3. Command-line interface via `python3 -m agent_workflows.comms_acks`.

Security and untrusted-input posture:
- Closed enum enforcement: an agent can only write states where comms.ack_writer_for(state) == "agent".
  Broker states (scheduled, queued, delivered, etc.) are strictly refused.
- Path traversal defense: msg_id and agent identity must pass comms.is_filename_safe.
- Unverified file authors: ack files on disk are self-asserted metadata. Aggregation classifies
  states into broker delivery and agent work by comms.ack_writer_for, but cannot verify the author
  identity on disk.
- Offset normalization: timestamps are normalized to offset-aware UTC to prevent comparison errors
  between mixed-offset acks.
- Fresh clone resilience: missing lanes (untracked/inbox, untracked/acks) are treated as empty
  without raising FileNotFoundError, and acks/ is created on demand.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from . import comms
from . import engine

__all__ = [
    "write_agent_ack",
    "message_status",
    "main",
]


def _normalize_ack_datetime(at_val: Any) -> Optional[datetime]:
    """Normalize an ISO-8601 string or datetime into an offset-aware UTC datetime.

    comms.validate_ack accepts values parsed by comms.parse_not_before, which returns an
    offset-naive datetime for timestamps lacking an offset and an offset-aware datetime
    otherwise. To prevent TypeError when comparing mixed timestamps, any naive datetime
    is treated as UTC via dt.replace(tzinfo=timezone.utc).
    """
    if not at_val or not isinstance(at_val, str):
        return None
    dt = comms.parse_not_before(at_val)
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _find_message(comms_dir: Path, msg_id: str) -> Optional[Path]:
    """Find message file in untracked/inbox, shared/inbox, or untracked/archive.

    Returns Path to the message file if found, or None. Missing directories are
    treated cleanly without raising FileNotFoundError.
    """
    search_dirs = [
        comms_dir / "untracked" / "inbox",
        comms_dir / "shared" / "inbox",
        comms_dir / "untracked" / "archive",
    ]
    for d in search_dirs:
        if not d.is_dir():
            continue
        p = d / f"{msg_id}.md"
        if p.is_file():
            return p
        p_raw = d / msg_id
        if p_raw.is_file():
            return p_raw
    return None


def write_agent_ack(
    comms_dir: Path | str,
    msg_id: str,
    state: str,
    by: str,
    now: Optional[datetime] = None,
) -> Path:
    """Write an agent-side acknowledgement file atomically to untracked/acks/.

    Refuses unless:
    - comms.ack_writer_for(state) == "agent" (agents cannot write broker states);
    - msg_id and by pass comms.is_filename_safe;
    - the message exists in untracked/inbox/, shared/inbox/, or untracked/archive/.

    Writes an offset-aware UTC timestamp. If the destination ack file already exists,
    the operation is idempotent and leaves the existing file untouched. Missing lane
    directories are created on demand.
    """
    writer = comms.ack_writer_for(state)
    if writer != "agent":
        raise ValueError(
            f"State {state!r} is not an agent ack state (authorized writer: {writer!r})"
        )

    if not comms.is_filename_safe(msg_id):
        raise ValueError(f"msg_id {msg_id!r} is not filename-safe")

    if not comms.is_filename_safe(by):
        raise ValueError(f"by {by!r} is not filename-safe")

    comms_dir = Path(comms_dir)
    msg_file = _find_message(comms_dir, msg_id)
    if msg_file is None:
        raise ValueError(
            f"Message {msg_id!r} not found in inboxes or archive under {comms_dir}"
        )

    if now is None:
        now_dt = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now_dt = now.replace(tzinfo=timezone.utc)
    else:
        now_dt = now.astimezone(timezone.utc)

    at_str = now_dt.isoformat()
    ack_obj: dict[str, Any] = {
        "re": msg_id,
        "state": state,
        "by": by,
        "at": at_str,
    }

    problems = comms.validate_ack(ack_obj)
    if problems:
        raise ValueError(f"Invalid ack object: {problems}")

    acks_dir = comms_dir / "untracked" / "acks"
    acks_dir.mkdir(parents=True, exist_ok=True)

    target_path = acks_dir / comms.ack_filename(msg_id, by, state)
    if target_path.exists():
        return target_path

    temp_fd, temp_path = tempfile.mkstemp(
        prefix="ack-", suffix=".tmp", dir=str(acks_dir)
    )
    with open(temp_fd, "w", encoding="utf-8") as f:
        json.dump(ack_obj, f, indent=2)
        f.write("\n")
    os.replace(temp_path, target_path)
    return target_path


def message_status(comms_dir: Path | str, msg_id: str) -> dict[str, Any]:
    """Derive aggregated status for msg_id across broker and agent acknowledgements.

    The writer of an ack file on disk is self-asserted and unverified on disk;
    classification into delivery (broker) and work (agent) reflects the declared ack
    state's authorized writer via comms.ack_writer_for, not an attested identity.

    Returns a dict with:
    - msg_id: the queried message ID
    - delivery: the newest (by 'at') valid broker-state ack dict, or None
    - work: the newest (by 'at') valid agent-state ack dict, or None
    - unread: True if a delivered broker ack exists and no valid agent ack exists
    - acks: list of all acks for msg_id; invalid files carry a 'problem' field
    """
    comms_dir = Path(comms_dir)
    acks_dir = comms_dir / "untracked" / "acks"

    status: dict[str, Any] = {
        "msg_id": msg_id,
        "delivery": None,
        "work": None,
        "unread": False,
        "acks": [],
    }

    if not acks_dir.is_dir():
        return status

    # Read every .json in untracked/acks/
    matching_acks: list[dict[str, Any]] = []
    broker_acks: list[tuple[datetime, str, dict[str, Any]]] = []
    agent_acks: list[tuple[datetime, str, dict[str, Any]]] = []
    has_delivered = False

    json_files = sorted(
        [
            p
            for p in acks_dir.iterdir()
            if p.is_file() and p.name.endswith(".json") and not p.name.startswith(".")
        ],
        key=lambda p: p.name,
    )

    for p in json_files:
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            if p.name.startswith(f"{msg_id}."):
                matching_acks.append(
                    {"file": p.name, "problem": f"unparseable JSON: {exc}"}
                )
            continue

        if not isinstance(data, dict):
            if p.name.startswith(f"{msg_id}."):
                matching_acks.append(
                    {"file": p.name, "problem": "ack must be a JSON object"}
                )
            continue

        if data.get("re") != msg_id:
            continue

        problems = comms.validate_ack(data)
        if problems:
            entry = dict(data)
            entry["problem"] = "; ".join(problems)
            matching_acks.append(entry)
            continue

        # Valid ack
        matching_acks.append(data)
        norm_dt = _normalize_ack_datetime(data.get("at"))
        if norm_dt is None:
            norm_dt = datetime.min.replace(tzinfo=timezone.utc)

        state = data.get("state")
        writer = comms.ack_writer_for(state) if state else None
        if writer == "broker":
            broker_acks.append((norm_dt, p.name, data))
            if state == "delivered":
                has_delivered = True
        elif writer == "agent":
            agent_acks.append((norm_dt, p.name, data))

    if broker_acks:
        # Sort by normalized timestamp, then filename fallback for stable tie-breaking
        newest_broker = max(broker_acks, key=lambda item: (item[0], item[1]))
        status["delivery"] = newest_broker[2]

    if agent_acks:
        newest_agent = max(agent_acks, key=lambda item: (item[0], item[1]))
        status["work"] = newest_agent[2]

    # unread is True exactly when delivered exists and NO valid agent ack exists
    status["unread"] = bool(has_delivered and not agent_acks)
    status["acks"] = matching_acks
    return status


def _resolve_comms_dir(
    repo_root_arg: Optional[str] = None, comms_dir_arg: Optional[str] = None
) -> Path:
    if comms_dir_arg:
        return Path(comms_dir_arg).resolve()
    repo_root = Path(repo_root_arg).resolve() if repo_root_arg else Path.cwd().resolve()
    layout = engine.resolve_target_layout(repo_root)
    dirs = engine._record_scaffold_dirs(layout)
    return repo_root / dirs["comms"]


def _list_inbox_messages(comms_dir: Path) -> list[str]:
    msg_ids: set[str] = set()
    for d in (comms_dir / "untracked" / "inbox", comms_dir / "shared" / "inbox"):
        if not d.is_dir():
            continue
        for p in d.iterdir():
            if p.is_file() and not p.name.startswith("."):
                mid = p.name.rsplit(".", 1)[0] if p.name.endswith(".md") else p.stem
                if comms.is_filename_safe(mid):
                    msg_ids.add(mid)
    return sorted(msg_ids)


def _print_status_text(st: dict[str, Any]) -> None:
    print(f"Message ID: {st.get('msg_id')}")
    delivery = st.get("delivery")
    if delivery:
        print(
            f"Delivery:   {delivery.get('state')} by {delivery.get('by')} at {delivery.get('at')}"
        )
    else:
        print("Delivery:   None")
    work = st.get("work")
    if work:
        print(
            f"Work:       {work.get('state')} by {work.get('by')} at {work.get('at')}"
        )
    else:
        print("Work:       None")
    print(f"Unread:     {st.get('unread')}")
    acks = st.get("acks", [])
    print(f"Acks ({len(acks)}):")
    for a in acks:
        if "problem" in a:
            ident = a.get("file") or a.get("state") or "unknown"
            print(f"  - [INVALID] {ident}: {a['problem']}")
        else:
            print(f"  - {a.get('state')} by {a.get('by')} at {a.get('at')}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m agent_workflows.comms_acks",
        description="Agent-side comms acknowledgement writing and status aggregation.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="subcommand")

    # ack subcommand
    ack_parser = subparsers.add_parser(
        "ack", help="Write an agent-side acknowledgement"
    )
    ack_parser.add_argument("msg_id", help="Message ID (re)")
    ack_parser.add_argument("state", help="Agent ack state (e.g. read, done, executed)")
    ack_parser.add_argument(
        "--by", required=True, help="Agent identity (e.g. proj.agent)"
    )
    ack_parser.add_argument("--repo-root", default=None, help="Repository root path")
    ack_parser.add_argument(
        "--comms-dir", default=None, help="Explicit comms directory path"
    )

    # status subcommand
    status_parser = subparsers.add_parser("status", help="Show message status")
    status_parser.add_argument(
        "msg_id", nargs="?", default=None, help="Optional message ID"
    )
    status_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (text or json)",
    )
    status_parser.add_argument("--repo-root", default=None, help="Repository root path")
    status_parser.add_argument(
        "--comms-dir", default=None, help="Explicit comms directory path"
    )

    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 0

    if args.subcommand == "ack":
        try:
            comms_dir = _resolve_comms_dir(args.repo_root, args.comms_dir)
            write_agent_ack(comms_dir, args.msg_id, args.state, args.by)
            return 0
        except Exception as exc:
            sys.stderr.write(f"Error: {exc}\n")
            return 2

    if args.subcommand == "status":
        try:
            comms_dir = _resolve_comms_dir(args.repo_root, args.comms_dir)
            if args.msg_id:
                res = message_status(comms_dir, args.msg_id)
                if args.format == "json":
                    print(json.dumps(res, indent=2))
                else:
                    _print_status_text(res)
                return 0
            else:
                msg_ids = _list_inbox_messages(comms_dir)
                statuses = [message_status(comms_dir, mid) for mid in msg_ids]
                if args.format == "json":
                    print(json.dumps(statuses, indent=2))
                else:
                    if not statuses:
                        print("[]")
                    else:
                        for idx, st in enumerate(statuses):
                            if idx > 0:
                                print()
                            _print_status_text(st)
                return 0
        except Exception as exc:
            sys.stderr.write(f"Error: {exc}\n")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
