"""User-level routing registry for two-way notification channels (spec 6kwd2e R10.1).

Stores mappings of channel message IDs or option tokens to run directory, question ID,
option selection, and artifact hash under `<AW_HOME>/notify/registry.json`.
Synchronized with FileLock on `<AW_HOME>/notify/registry.lock`.
"""

from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any

from filelock import FileLock

from agent_workflows import project_context, question_inbox


def utc_now() -> str:
    """Current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _get_registry_paths() -> tuple[Path, Path]:
    """Return (registry_json_path, lock_file_path)."""
    aw_home = Path(project_context.get_default_aw_home())
    reg_dir = aw_home / "notify"
    reg_dir.mkdir(parents=True, exist_ok=True)
    return reg_dir / "registry.json", reg_dir / "registry.lock"


def _read_registry_locked(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"routes": {}, "seen_events": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("routes", {})
            data.setdefault("seen_events", {})
            return data
    except Exception:
        pass
    return {"routes": {}, "seen_events": {}}


def _write_registry_locked(path: Path, data: dict[str, Any]) -> None:
    tmp_path = path.parent / f".registry.tmp.{os.getpid()}.{time.time_ns()}"
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp_path), str(path))
    finally:
        if tmp_path.exists():
            with contextlib.suppress(OSError):
                tmp_path.unlink()


def register(
    channel: str,
    key: str,
    run_dir: Path | str,
    question_id: str,
    option: int | None = None,
    artifact_hash: str = "",
    *,
    group_id: str | None = None,
    member_qids: list[str] | None = None,
) -> None:
    """Register a routing key (channel message id or button token) to a parked question.

    For a question GROUP, ``question_id`` is the group's representative member
    qid and ``group_id``/``member_qids`` are stored as well; inbound routing then
    answers the current open group containing that representative qid.
    """
    reg_path, lock_path = _get_registry_paths()
    with FileLock(str(lock_path), timeout=10):
        data = _read_registry_locked(reg_path)
        channel_routes = data["routes"].setdefault(channel, {})
        route: dict[str, Any] = {
            "run_dir": str(run_dir),
            "question_id": question_id,
            "option": option,
            "artifact_hash": artifact_hash,
            "registered_at": utc_now(),
        }
        if group_id is not None:
            route["group_id"] = group_id
        if member_qids is not None:
            route["member_qids"] = list(member_qids)
        channel_routes[key] = route
        _write_registry_locked(reg_path, data)


def lookup(channel: str, key: str) -> dict[str, Any] | None:
    """Lookup a routing key for a channel; return mapping dict or None."""
    reg_path, lock_path = _get_registry_paths()
    with FileLock(str(lock_path), timeout=10):
        data = _read_registry_locked(reg_path)
        return data.get("routes", {}).get(channel, {}).get(key)


def seen_event(channel: str, event_id: str) -> bool:
    """Record and check for duplicate event IDs.

    Returns True if event_id has already been seen (duplicate),
    False if it is new and was recorded. Bounded to the newest 10,000 IDs.
    """
    reg_path, lock_path = _get_registry_paths()
    with FileLock(str(lock_path), timeout=10):
        data = _read_registry_locked(reg_path)
        seen_list = data["seen_events"].setdefault(channel, [])
        if event_id in seen_list:
            return True
        seen_list.append(event_id)
        if len(seen_list) > 10000:
            data["seen_events"][channel] = seen_list[-10000:]
        _write_registry_locked(reg_path, data)
        return False


def expire() -> int:
    """Drop entries whose run directory is gone or whose question is no longer open.

    Returns the count of expired entries removed.
    """
    reg_path, lock_path = _get_registry_paths()
    removed = 0
    with FileLock(str(lock_path), timeout=10):
        data = _read_registry_locked(reg_path)
        routes = data.get("routes", {})
        for channel, keys in list(routes.items()):
            for key, info in list(keys.items()):
                run_dir = Path(info.get("run_dir", ""))
                qid = info.get("question_id", "")
                if not run_dir.is_dir():
                    del routes[channel][key]
                    removed += 1
                    continue
                q_data = question_inbox.read_question(run_dir, qid)
                if (
                    q_data is None
                    or q_data.get("status") != question_inbox.QUESTION_STATUS_OPEN
                ):
                    del routes[channel][key]
                    removed += 1
        if removed > 0:
            _write_registry_locked(reg_path, data)
    return removed
