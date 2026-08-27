#!/usr/bin/env python3
"""List and inspect Antigravity (agy) sessions for a project workspace or directory.

Displays session ID, start time, end time, duration, active status (in use / idle),
and initial prompt summary.
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class SessionInfo:
    conversation_id: str
    workspace: str
    is_active: bool
    start_time: datetime.datetime | None
    end_time: datetime.datetime | None
    duration_str: str
    first_prompt: str
    step_count: int


def _is_session_active(app_data_dir: Path, conversation_id: str) -> bool:
    """Check if the session has an active flock on its presence lockfile."""
    lock_file = app_data_dir / "presence" / f"{conversation_id}.lock"
    if not lock_file.exists():
        return False
    try:
        f = open(lock_file, "r+")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()
        return False
    except (BlockingIOError, PermissionError, OSError):
        return True


def _format_duration(
    start: datetime.datetime | None, end: datetime.datetime | None
) -> str:
    """Format duration between start and end timestamps into human-readable string."""
    if not start or not end:
        return "-"
    delta = end - start
    total_seconds = max(0, int(delta.total_seconds()))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    if minutes > 0:
        return f"{minutes}m {seconds:02d}s"
    return f"{seconds}s"


def _parse_iso_z(ts_str: str) -> datetime.datetime | None:
    """Parse ISO8601 timestamp string (e.g. 2026-08-17T02:25:46Z) to local datetime."""
    if not ts_str:
        return None
    try:
        # Normalize trailing Z to +00:00 for fromisoformat
        normalized = ts_str.replace("Z", "+00:00")
        dt_utc = datetime.datetime.fromisoformat(normalized)
        return dt_utc.astimezone()
    except Exception:
        return None


def get_sessions(
    workspace_filter: str | None = None,
    app_data_dir: Path | None = None,
) -> list[SessionInfo]:
    """Retrieve all sessions, optionally filtered by workspace directory."""
    if app_data_dir is None:
        app_data_dir = Path.home() / ".gemini" / "antigravity-cli"

    history_file = app_data_dir / "history.jsonl"
    brain_dir = app_data_dir / "brain"

    # Map conversation_id -> metadata from history.jsonl
    history_by_id: dict[str, dict] = {}
    if history_file.exists():
        try:
            with history_file.open(encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    cid = obj.get("conversationId")
                    if not cid:
                        continue
                    ws = obj.get("workspace", "")
                    ts = obj.get("timestamp", 0)
                    disp = obj.get("display", "").replace("\n", " ").strip()

                    if cid not in history_by_id:
                        history_by_id[cid] = {
                            "workspace": ws,
                            "first_ts": ts,
                            "last_ts": ts,
                            "first_prompt": disp,
                        }
                    else:
                        if ts > history_by_id[cid]["last_ts"]:
                            history_by_id[cid]["last_ts"] = ts
        except Exception:
            pass

    # Collect all known conversation IDs from history and brain dirs
    all_cids: set[str] = set(history_by_id.keys())
    if brain_dir.is_dir():
        for child in brain_dir.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                all_cids.add(child.name)

    results: list[SessionInfo] = []

    target_ws = str(Path(workspace_filter).resolve()) if workspace_filter else None

    for cid in all_cids:
        hist = history_by_id.get(cid, {})
        ws = hist.get("workspace", "")

        # Read transcript.jsonl if available for accurate timestamps & step count
        transcript_file = (
            brain_dir / cid / ".system_generated" / "logs" / "transcript.jsonl"
        )
        start_dt: datetime.datetime | None = None
        end_dt: datetime.datetime | None = None
        step_count = 0
        first_prompt = hist.get("first_prompt", "")

        if transcript_file.is_file():
            try:
                first_step = None
                last_step = None
                with transcript_file.open(encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            step = json.loads(line)
                        except Exception:
                            continue
                        step_count += 1
                        if first_step is None:
                            first_step = step
                        last_step = step
                if first_step and "created_at" in first_step:
                    start_dt = _parse_iso_z(str(first_step["created_at"]))
                if last_step and "created_at" in last_step:
                    end_dt = _parse_iso_z(str(last_step["created_at"]))
                if not first_prompt and first_step and "content" in first_step:
                    first_prompt = str(first_step["content"]).replace("\n", " ").strip()
            except Exception:
                pass

        # Fallback to history.jsonl timestamps if transcript timestamps missing
        if start_dt is None and hist.get("first_ts"):
            start_dt = datetime.datetime.fromtimestamp(
                hist["first_ts"] / 1000
            ).astimezone()
        if end_dt is None and hist.get("last_ts"):
            end_dt = datetime.datetime.fromtimestamp(
                hist["last_ts"] / 1000
            ).astimezone()

        # If still missing, check file modification time
        if start_dt is None and transcript_file.exists():
            start_dt = datetime.datetime.fromtimestamp(
                transcript_file.stat().st_mtime
            ).astimezone()
            end_dt = start_dt

        # Check if currently active / locked
        is_active = _is_session_active(app_data_dir, cid)

        # Apply workspace filter if specified
        if target_ws and ws:
            try:
                hist_ws_resolved = str(Path(ws).resolve())
                if hist_ws_resolved != target_ws and target_ws not in hist_ws_resolved:
                    continue
            except Exception:
                if target_ws != ws:
                    continue
        elif target_ws and not ws:
            # If no workspace recorded in history, check if transcript mentions target
            continue

        duration_str = _format_duration(start_dt, end_dt)

        results.append(
            SessionInfo(
                conversation_id=cid,
                workspace=ws,
                is_active=is_active,
                start_time=start_dt,
                end_time=end_dt,
                duration_str=duration_str,
                first_prompt=first_prompt[:90],
                step_count=step_count,
            )
        )

    # Sort descending by end_time or start_time
    def _sort_key(s: SessionInfo):
        return (
            1 if s.is_active else 0,
            s.end_time.timestamp() if s.end_time else 0,
            s.start_time.timestamp() if s.start_time else 0,
        )

    results.sort(key=_sort_key, reverse=True)
    return results


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agy sessions",
        description="List and inspect Antigravity (agy) sessions for a project or directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""EXAMPLES:
  # List sessions for the current project / directory:
  python3 tools/agy_sessions.py

  # List sessions for a specific directory:
  python3 tools/agy_sessions.py /path/to/project

  # List all sessions across all workspaces:
  python3 tools/agy_sessions.py --all

  # Output as JSON:
  python3 tools/agy_sessions.py --json
""",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Workspace directory to inspect (default: current working directory).",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="List all sessions across all projects/workspaces.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output session list as JSON.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    ws_filter = None if args.all else str(Path(args.directory).resolve())

    sessions = get_sessions(workspace_filter=ws_filter)

    if args.json:
        data = [
            {
                "conversation_id": s.conversation_id,
                "workspace": s.workspace,
                "is_active": s.is_active,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "duration": s.duration_str,
                "steps": s.step_count,
                "prompt": s.first_prompt,
            }
            for s in sessions
        ]
        print(json.dumps(data, indent=2))
        return 0

    target_label = "all projects" if args.all else ws_filter

    if not sessions:
        print(f"\nAntigravity Sessions ({target_label}):\n")
        print("  No sessions found.\n")
        return 0

    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        if console.is_terminal:
            table = Table(
                title=f"Antigravity Sessions ({target_label})",
                show_header=True,
                header_style="bold cyan",
            )
            table.add_column("Status", justify="center", no_wrap=True)
            table.add_column("Conversation ID", style="bold white", no_wrap=True)
            table.add_column("Start Time", style="green", no_wrap=True)
            table.add_column("Last Active", style="green", no_wrap=True)
            table.add_column("Duration", justify="right", style="yellow", no_wrap=True)
            table.add_column("Steps", justify="right", style="magenta", no_wrap=True)
            table.add_column("Prompt / Title", style="italic")

            for s in sessions:
                status_style = (
                    "[bold green]ACTIVE[/bold green]"
                    if s.is_active
                    else "[dim]IDLE[/dim]"
                )
                start_str = (
                    s.start_time.strftime("%Y-%m-%d %H:%M:%S") if s.start_time else "-"
                )
                end_str = (
                    s.end_time.strftime("%Y-%m-%d %H:%M:%S") if s.end_time else "-"
                )
                prompt_snippet = s.first_prompt or "(no prompt)"
                if len(prompt_snippet) > 60:
                    prompt_snippet = f"{prompt_snippet[:57]}..."
                table.add_row(
                    status_style,
                    s.conversation_id,
                    start_str,
                    end_str,
                    s.duration_str,
                    str(s.step_count),
                    prompt_snippet,
                )

            console.print()
            console.print(table)
            console.print()
            return 0
    except ImportError:
        pass

    print(f"\nAntigravity Sessions ({target_label}):\n")
    header = f"{'STATUS':<8}  {'CONVERSATION ID':<36}  {'START TIME':<19}  {'LAST ACTIVE':<19}  {'DURATION':<11}  {'PROMPT / TITLE'}"
    print(header)
    print("-" * len(header))

    for s in sessions:
        status_str = "ACTIVE" if s.is_active else "IDLE"
        start_str = s.start_time.strftime("%Y-%m-%d %H:%M:%S") if s.start_time else "-"
        end_str = s.end_time.strftime("%Y-%m-%d %H:%M:%S") if s.end_time else "-"
        prompt_snippet = s.first_prompt or "(no prompt)"
        if len(prompt_snippet) > 50:
            prompt_snippet = f"{prompt_snippet[:47]}..."

        print(
            f"{status_str:<8}  {s.conversation_id:<36}  {start_str:<19}  {end_str:<19}  {s.duration_str:<11}  {prompt_snippet}"
        )

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
