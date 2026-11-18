#!/usr/bin/env python3
"""Scriptable fake OpenCode v1/v2 host executable for m0001_describe tests (ya4ee4 E-09).

Answers ``--version``, OpenCode v1 ``debug agent aw-describe``, OpenCode v2
``debug agents``, and ``run`` (reading stdin and emitting OpenCode JSON events
from a scripted reply table in ``AW_FAKE_HOST_TABLE``).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import sys
from typing import Any


def _load_json_file(path_str: str, default: Any) -> Any:
    if not path_str:
        return default
    p = Path(path_str)
    if not p.is_file():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def _save_json_file(path_str: str, data: Any) -> None:
    if not path_str:
        return
    p = Path(path_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _parse_v1_env_config() -> dict[str, Any]:
    raw = os.environ.get("OPENCODE_CONFIG_CONTENT", "")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except ValueError:
        return {}


def _read_v2_cwd_config(cwd: Path) -> tuple[dict[str, Any], int | None]:
    cfg_path = cwd / ".opencode" / "opencode.json"
    if not cfg_path.is_file():
        return {}, None
    mode = stat.S_IMODE(cfg_path.stat().st_mode)
    try:
        parsed = json.loads(cfg_path.read_text(encoding="utf-8"))
        return (parsed if isinstance(parsed, dict) else {}), mode
    except ValueError:
        return {}, mode


def _handle_debug_agent_v1(argv: list[str]) -> int:
    agent_name = argv[2] if len(argv) > 2 else "aw-describe"
    cfg = _parse_v1_env_config()
    agents = cfg.get("agent") if isinstance(cfg.get("agent"), dict) else {}
    spec = agents.get(agent_name) if isinstance(agents.get(agent_name), dict) else {}

    policy_mode = os.environ.get("AW_FAKE_HOST_POLICY", "ok")
    raw_tools = spec.get("tools") if isinstance(spec.get("tools"), dict) else {}
    wildcard_false = raw_tools.get("*") is False
    tools = {
        "bash": not wildcard_false,
        "read": not wildcard_false,
        "edit": not wildcard_false,
        "write": not wildcard_false,
        "glob": not wildcard_false,
        "grep": not wildcard_false,
    }
    if policy_mode == "v1_tool_enabled":
        tools["bash"] = True

    perms: list[dict[str, Any]] = []
    root_perm = cfg.get("permission") if isinstance(cfg.get("permission"), dict) else {}
    for k, v in root_perm.items():
        perms.append({"permission": k, "action": v, "pattern": "*"})
    agent_perm = (
        spec.get("permission") if isinstance(spec.get("permission"), dict) else {}
    )
    for k, v in agent_perm.items():
        perms.append({"permission": k, "action": v, "pattern": "*"})

    if policy_mode == "post_deny_external_dir":
        perms.append(
            {"permission": "external_directory", "action": "allow", "pattern": "*"}
        )
    elif policy_mode == "post_deny_deny":
        perms.append({"permission": "bash", "action": "deny", "pattern": "*"})
    elif policy_mode == "post_deny_allow":
        perms.append({"permission": "bash", "action": "allow", "pattern": "*"})

    sys.stdout.write(
        json.dumps({"name": agent_name, "tools": tools, "permission": perms}) + "\n"
    )
    return 0


def _handle_debug_agents_v2() -> int:
    cwd = Path.cwd()
    cfg, _mode = _read_v2_cwd_config(cwd)
    agents = cfg.get("agents") if isinstance(cfg.get("agents"), dict) else {}
    spec = (
        agents.get("aw-describe") if isinstance(agents.get("aw-describe"), dict) else {}
    )
    raw_perms = spec.get("permissions")
    perms: list[dict[str, Any]] = (
        [dict(p) for p in raw_perms if isinstance(p, dict)]
        if isinstance(raw_perms, list)
        else []
    )
    # Include an ancestor allow rule BEFORE the wildcard deny from .opencode/opencode.json
    full_perms: list[dict[str, Any]] = [
        {"action": "shell", "resource": "*", "effect": "allow"},
        *perms,
    ]
    policy_mode = os.environ.get("AW_FAKE_HOST_POLICY", "ok")
    if policy_mode == "post_deny_external_dir":
        full_perms.append(
            {"action": "external_directory", "resource": "*", "effect": "allow"}
        )
    elif policy_mode == "post_deny_deny":
        full_perms.append({"action": "shell", "resource": "*", "effect": "deny"})
    elif policy_mode == "post_deny_allow":
        full_perms.append({"action": "bash", "resource": "*", "effect": "allow"})

    payload = [
        {
            "id": "build",
            "name": "build",
            "mode": "primary",
            "permissions": [{"action": "*", "resource": "*", "effect": "allow"}],
        },
        {
            "id": "aw-describe",
            "name": "aw-describe",
            "mode": spec.get("mode", "primary"),
            "permissions": full_perms,
        },
    ]
    sys.stdout.write(json.dumps(payload) + "\n")
    return 0


def _select_reply(
    stdin_text: str, table: dict[str, Any], state_path: str
) -> dict[str, Any]:
    state = _load_json_file(state_path, {"call_count": 0, "cursors": {}})
    state["call_count"] = int(state.get("call_count", 0)) + 1

    rules = table.get("rules") or []
    matched_rule: dict[str, Any] | None = None
    matched_key = "__default__"
    for idx, rule in enumerate(rules):
        needle = rule.get("match")
        if isinstance(needle, str) and needle in stdin_text:
            matched_rule = rule
            matched_key = f"rule:{idx}:{needle}"
            break

    if matched_rule is None:
        default_reply = table.get("default") or {
            "text": "Synthetic fake host description.",
            "cost": 0.002,
            "tokens": 250,
        }
        _save_json_file(state_path, state)
        return dict(default_reply)

    replies = matched_rule.get("replies") or []
    if not replies:
        _save_json_file(state_path, state)
        return {
            "text": "Synthetic fake host description.",
            "cost": 0.002,
            "tokens": 250,
        }

    cursors = dict(state.get("cursors") or {})
    pos = int(cursors.get(matched_key, 0))
    chosen = dict(replies[min(pos, len(replies) - 1)])
    cursors[matched_key] = pos + 1
    state["cursors"] = cursors
    _save_json_file(state_path, state)
    return chosen


def _handle_run(argv: list[str]) -> int:
    stdin_text = sys.stdin.read()
    cwd = Path.cwd()
    mode = os.environ.get("AW_FAKE_HOST_MODE", "v2")
    v1_cfg = _parse_v1_env_config()
    v2_cfg, v2_mode = _read_v2_cwd_config(cwd)

    v1_tools_disabled = (
        isinstance(v1_cfg.get("agent"), dict)
        and isinstance(v1_cfg["agent"].get("aw-describe"), dict)
        and isinstance(v1_cfg["agent"]["aw-describe"].get("tools"), dict)
        and v1_cfg["agent"]["aw-describe"]["tools"].get("*") is False
        and isinstance(v1_cfg.get("permission"), dict)
        and v1_cfg["permission"].get("*") == "deny"
    )
    v2_tools_disabled = (
        isinstance(v2_cfg.get("agents"), dict)
        and isinstance(v2_cfg["agents"].get("aw-describe"), dict)
        and any(
            isinstance(r, dict)
            and r.get("action") == "*"
            and r.get("resource") == "*"
            and r.get("effect") == "deny"
            for r in (v2_cfg["agents"]["aw-describe"].get("permissions") or [])
        )
    )

    log_path = os.environ.get("AW_FAKE_HOST_LOG", "")
    if log_path:
        lp = Path(log_path)
        lp.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "mode": mode,
            "argv": argv,
            "cwd": str(cwd),
            "cwd_mode": oct(stat.S_IMODE(cwd.stat().st_mode)),
            "v2_cfg_mode": oct(v2_mode) if v2_mode is not None else None,
            "v1_tools_disabled": v1_tools_disabled,
            "v2_tools_disabled": v2_tools_disabled,
            "stdin_len": len(stdin_text),
            "stdin": stdin_text,
        }
        with lp.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

    table_path = os.environ.get("AW_FAKE_HOST_TABLE", "")
    table = _load_json_file(table_path, {})
    state_path = os.environ.get("AW_FAKE_HOST_STATE", "") or (
        f"{table_path}.state.json" if table_path else ""
    )

    reply = _select_reply(stdin_text, table, state_path)

    if reply.get("stderr"):
        sys.stderr.write(str(reply["stderr"]) + "\n")

    tool_event = reply.get("tool_event")
    if tool_event == "v1":
        sys.stdout.write(
            json.dumps(
                {
                    "type": "tool_use",
                    "part": {
                        "tool": "bash",
                        "state": {"status": "completed", "input": {"command": "id"}},
                    },
                }
            )
            + "\n"
        )
    elif tool_event == "v2":
        sys.stdout.write(
            json.dumps(
                {
                    "type": "tool",
                    "part": {
                        "tool": "shell",
                        "state": {"status": "completed", "input": {"command": "id"}},
                    },
                }
            )
            + "\n"
        )

    if reply.get("error_event"):
        sys.stdout.write(json.dumps(reply["error_event"]) + "\n")

    if reply.get("text") is not None:
        sys.stdout.write(
            json.dumps(
                {
                    "type": "text",
                    "part": {"type": "text", "text": str(reply["text"])},
                }
            )
            + "\n"
        )

    if not reply.get("omit_step_finish"):
        tokens = int(reply.get("tokens", 250))
        part: dict[str, Any] = {
            "type": "step-finish",
            "reason": str(reply.get("reason", "stop")),
            "cost": float(reply.get("cost", 0.002)),
            "tokens": {
                "total": tokens,
                "input": max(0, tokens - 20),
                "output": min(20, tokens),
            },
        }
        if reply.get("modelID"):
            part["modelID"] = str(reply["modelID"])
        sys.stdout.write(json.dumps({"type": "step_finish", "part": part}) + "\n")

    return int(reply.get("exit_code", 0))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    mode = os.environ.get("AW_FAKE_HOST_MODE", "v2")
    if args == ["--version"] or args == ["-v"]:
        sys.stdout.write("opencode v1.18.35\n" if mode == "v1" else "opencode v2.2.7\n")
        return 0
    if len(args) >= 2 and args[0] == "debug" and args[1] == "agent":
        return _handle_debug_agent_v1(args)
    if len(args) >= 2 and args[0] == "debug" and args[1] == "agents":
        return _handle_debug_agents_v2()
    if len(args) >= 1 and args[0] == "run":
        return _handle_run(args)
    sys.stderr.write(f"fake_host.py: unrecognized args: {args!r}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
