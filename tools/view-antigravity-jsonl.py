#!/usr/bin/env python3
"""Format Antigravity JSONL event logs as readable, pipe-friendly terminal text."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, TextIO


def compact(value: Any, limit: int = 180) -> str:
    """Render a JSON value on one line, clipping only its display."""
    if isinstance(value, str):
        text = value.replace("\n", "\\n")
    else:
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def duration(value: Any) -> str:
    return f" {float(value):.3f}s" if value is not None else ""


def format_usage(usage: Any) -> str:
    if not isinstance(usage, dict):
        return ""
    parts = []
    for key in (
        "input_tokens",
        "output_tokens",
        "thinking_tokens",
        "cache_read_tokens",
    ):
        if usage.get(key):
            parts.append(f"{key.removesuffix('_tokens')}={usage[key]:,}")
    return f" [{', '.join(parts)}]" if parts else ""


def format_record(line_number: int, record: dict[str, Any]) -> str:
    event = record.get("event", "record")
    if event == "init":
        init = record.get("init", {})
        return f"{line_number:04d} INIT cwd={compact(init.get('cwd', ''))}"
    update = record.get("step_update", record)
    step = update.get("step_index", "?")
    kind = str(update.get("step_type", event)).upper()
    state = update.get("state", "")
    prefix = f"{line_number:04d} {step:>5} {kind:<14} {state:<6}"
    if kind == "TOOL":
        info = update.get("tool_info") or {}
        name = update.get("tool_name") or info.get("name") or "tool"
        parts = [str(name)]
        if info.get("parameters") is not None:
            parts.append(compact(info["parameters"]))
        if info.get("output") is not None:
            parts.append("=> " + compact(info["output"]))
        return (
            prefix + duration(update.get("duration_seconds")) + " " + " | ".join(parts)
        )
    text = prefix + duration(update.get("duration_seconds"))
    if kind in {"AGENT_RESPONSE", "CHECKPOINT"}:
        text += format_usage(update.get("usage"))
    for key in ("message", "content", "text", "error", "reason"):
        if update.get(key) is not None:
            text += " | " + compact(update[key])
            break
    return text


def records(handle: TextIO) -> Iterable[tuple[int, dict[str, Any]]]:
    for line_number, line in enumerate(handle, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            print(f"line {line_number}: invalid JSON ({error.msg})", file=sys.stderr)
            continue
        if not isinstance(value, dict):
            print(f"line {line_number}: expected a JSON object", file=sys.stderr)
            continue
        yield line_number, value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "log", nargs="?", default="-", help="JSONL log path, or - for stdin"
    )
    parser.add_argument(
        "--match", metavar="TEXT", help="Only emit records containing this text"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Also emit each matching source object as indented JSON",
    )
    args = parser.parse_args()
    if args.log == "-":
        handle, close = sys.stdin, False
    else:
        try:
            handle, close = Path(args.log).expanduser().open(encoding="utf-8"), True
        except OSError as error:
            parser.error(str(error))
    needle = args.match.lower() if args.match else None
    try:
        for line_number, record in records(handle):
            rendered = format_record(line_number, record)
            if needle and needle not in (rendered + json.dumps(record)).lower():
                continue
            print(rendered)
            if args.raw:
                print(json.dumps(record, ensure_ascii=False, indent=2))
    finally:
        if close:
            handle.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
