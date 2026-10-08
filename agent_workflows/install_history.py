"""Install-history audit log (setupmarker Order 01: extracted from the deleted action ledger).

An append-only record of install/update events under the resolved durable state class
(`state/durable/install.json` snapshot + `state/durable/history/installs.jsonl`). This is a genuine
audit artifact with no on-disk-derivable equivalent, so it is KEPT while the operational-action ledger
is removed. Caller-supplied ``details`` are redacted through the canonical leak sanitizer (L6-04)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import agent_workflows
from agent_workflows import layout
from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import (
    RootClass,
    parse_portable_policy,
)


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
    """Atomic install snapshot update and JSONL append under durable state class."""
    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
    durable_path = (
        ctx.physical_classes.get(RootClass.STATE_DURABLE.value)
        if ctx.physical_classes
        else None
    )
    if durable_path:
        durable_root = Path(durable_path)
    else:
        durable_root = Path(target_repo) / ".aw" / "state" / "durable"
    durable_root.mkdir(parents=True, exist_ok=True)

    install_name = layout.DURABLE_STATE_CLASSES.get("install", "install.json")
    history_name = layout.DURABLE_STATE_CLASSES.get("history", "history")
    history_dir = durable_root / history_name
    history_dir.mkdir(parents=True, exist_ok=True)

    project_file = Path(target_repo) / ".aw" / "config" / "project.json"
    policy_summary: Optional[Dict[str, Any]] = None
    if project_file.is_file():
        try:
            with open(project_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            portable = parse_portable_policy(data)
            policy_summary = {
                "preset": portable.preset,
                "role": portable.role,
                "placements": dict(portable.placements or {}),
                "git_policies": dict(portable.git_policies or {}),
                "enabled_hosts": list(portable.enabled_hosts or []),
                "delivery_mode": portable.delivery_mode,
                "records_backend": portable.records_backend,
            }
        except Exception:
            policy_summary = None

    if policy_summary is None:
        from agent_workflows.install_wizard import get_preset_defaults

        try:
            pls, gps, dm, rb, _ = get_preset_defaults(ctx.preset)
        except Exception:
            pls, gps, dm, rb = {}, {}, ctx.delivery_mode, ctx.records_backend
        policy_summary = {
            "preset": ctx.preset,
            "role": getattr(ctx, "project_role", "target"),
            "placements": dict(pls),
            "git_policies": dict(ctx.git_policies or gps),
            "enabled_hosts": list(ctx.enabled_hosts),
            "delivery_mode": ctx.delivery_mode or dm,
            "records_backend": ctx.records_backend or rb,
        }

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    snapshot = {
        "project_id": ctx.project_id,
        "last_installed_at": now,
        "installed_version": agent_workflows.__version__,
        "schema_version": 2,
        "delivery_mode": ctx.delivery_mode,
        "records_backend": ctx.records_backend,
        "event_type": event_type,
        "policy": policy_summary,
    }

    install_file = durable_root / install_name
    tmp_install = durable_root / f".tmp_{install_name}"
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
