"""Install-history audit log (setupmarker Order 01: extracted from the deleted action ledger).

An append-only record of install/update events under the resolved STATE root
(`state/install.json` snapshot + `state/history/installs.jsonl`). This is a genuine audit artifact
with no on-disk-derivable equivalent, so it is KEPT while the operational-action ledger is removed.
Caller-supplied ``details`` are redacted through the canonical leak sanitizer (L6-04)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import LogicalRoot


def _redact_details(details: Dict[str, Any], *, repo_root: str) -> Dict[str, Any]:
    """Redact machine-identifying values from install-history ``details`` using the canonical
    leak sanitizer (no bespoke regex). Any string value that trips a fail/warn rule (home paths,
    usernames, hostnames) is replaced with ``"[redacted]"`` (L6-04)."""
    from agent_workflows import leak_sanitizer as ls

    ruleset = ls.build_ruleset(Path(repo_root), include_warn=True)
    safe: Dict[str, Any] = {}
    for key, value in details.items():
        if isinstance(value, str) and ls.scan_text(
            value, "install-history", ruleset, include_warn=True
        ):
            safe[key] = "[redacted]"
        else:
            safe[key] = value
    return safe


def record_install_history(
    target_repo: str,
    event_type: str,
    details: Dict[str, Any],
    aw_home: Optional[str] = None,
) -> None:
    """Atomic install snapshot update and JSONL append."""
    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
    state_root = Path(ctx.logical_roots[LogicalRoot.STATE.value])
    state_root.mkdir(parents=True, exist_ok=True)
    history_dir = state_root / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    snapshot = {
        "project_id": ctx.project_id,
        "last_installed_at": now,
        "delivery_mode": ctx.delivery_mode,
        "records_backend": ctx.records_backend,
        "event_type": event_type,
    }

    install_file = state_root / "install.json"
    tmp_install = state_root / ".tmp_install.json"
    with open(tmp_install, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    os.replace(tmp_install, install_file)

    safe_details = _redact_details(details, repo_root=target_repo)
    history_file = history_dir / "installs.jsonl"
    event_line = (
        json.dumps({"timestamp": now, "details": safe_details, **snapshot}) + "\n"
    )
    fd = os.open(str(history_file), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, event_line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
