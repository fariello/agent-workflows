#!/usr/bin/env python3
"""Watch process trees rooted at `agy` (or specified agents/processes), collapsing redundant processes/threads.

Monitors processes launched by other agents (OpenCode, Claude Code, etc.) or interactive shells
by inspecting kernel comm, executable paths, script runners, and shell subcommands from /proc.
Linux only: process and thread information is read directly from /proc.
"""

from __future__ import annotations

import argparse
import os
import shlex
import signal
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Process:
    pid: int
    ppid: int
    name: str
    cmdline: tuple[str, ...]
    threads: Counter[str] = field(default_factory=Counter)
    children: list[Process] = field(default_factory=list)

    @property
    def arguments(self) -> tuple[str, ...]:
        return self.cmdline[1:] if self.cmdline else ()

    @property
    def signature(self) -> tuple[str, tuple[str, ...]]:
        """The identity used to collapse otherwise identical processes."""
        return self.name, self.arguments


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def read_threads(pid: int) -> Counter[str]:
    """Count non-main threads by their kernel names."""
    counts: Counter[str] = Counter()
    task_directory = Path("/proc") / str(pid) / "task"

    try:
        tasks = list(task_directory.iterdir())
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return counts

    for task in tasks:
        if not task.name.isdigit() or int(task.name) == pid:
            continue
        try:
            counts[read_text(task / "comm")] += 1
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            # Processes and threads may disappear during a snapshot.
            continue

    return counts


def read_processes() -> dict[int, Process]:
    processes: dict[int, Process] = {}

    try:
        proc_entries = list(Path("/proc").iterdir())
    except FileNotFoundError as error:
        raise RuntimeError(
            "/proc is unavailable; this script requires Linux"
        ) from error

    for entry in proc_entries:
        if not entry.name.isdigit():
            continue

        pid = int(entry.name)
        try:
            stat = read_text(entry / "stat")
            closing_parenthesis = stat.rfind(")")
            if closing_parenthesis < 0:
                continue
            # After `(comm)`, fields begin with state (3), then PPID (4).
            ppid = int(stat[closing_parenthesis + 2 :].split()[1])
            name = read_text(entry / "comm")
            raw_command = (entry / "cmdline").read_bytes().split(b"\0")
            argv = tuple(
                value.decode("utf-8", errors="replace")
                for value in raw_command
                if value
            )
            processes[pid] = Process(
                pid=pid,
                ppid=ppid,
                name=name,
                cmdline=argv,
                threads=read_threads(pid),
            )
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            continue

    for process in processes.values():
        parent = processes.get(process.ppid)
        if parent is not None:
            parent.children.append(process)

    return processes


def format_arguments(arguments: tuple[str, ...]) -> str:
    return " ".join(shlex.quote(argument) for argument in arguments)


def truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: max(1, width - 3)].rstrip() + "..."


def process_label(
    members: list[Process],
    width: int,
    *,
    is_root: bool = False,
    processes: dict[int, Process] | None = None,
) -> str:
    representative = members[0]
    arguments = format_arguments(representative.arguments)

    parent_suffix = ""
    if is_root and processes and representative.ppid in processes:
        parent = processes[representative.ppid]
        if parent.pid > 1:
            parent_suffix = f" [parent: {parent.name},{parent.pid}]"

    if len(members) == 1:
        head = f"{representative.name},{representative.pid}"
    else:
        head = f"{len(members)}x {representative.name}"

    label = f"{head} {arguments}".rstrip()
    if parent_suffix:
        label = f"{label}{parent_suffix}"
    return truncate(label, width)


def group_processes(processes: list[Process]) -> list[list[Process]]:
    groups: dict[tuple[str, tuple[str, ...]], list[Process]] = defaultdict(list)
    for process in processes:
        groups[process.signature].append(process)

    return sorted(
        groups.values(),
        key=lambda group: (group[0].name, group[0].arguments, group[0].pid),
    )


def render_group(
    members: list[Process],
    *,
    level: int,
    max_depth: int,
    width: int,
    processes: dict[int, Process] | None = None,
    prefix: str = "",
    is_last: bool = True,
    is_root: bool = False,
) -> list[str]:
    connector = "" if is_root else ("`-" if is_last else "|-")
    lines = [
        f"{prefix}{connector}{process_label(members, width, is_root=is_root, processes=processes)}"
    ]

    if level >= max_depth:
        return lines

    child_prefix = prefix if is_root else prefix + ("  " if is_last else "| ")

    thread_counts: Counter[str] = Counter()
    child_processes: list[Process] = []
    for member in members:
        thread_counts.update(member.threads)
        child_processes.extend(member.children)

    # Threads are leaves; process groups may have descendants of their own.
    entries: list[tuple[str, object]] = [
        ("process", group) for group in group_processes(child_processes)
    ]
    entries.extend(
        ("thread", (thread_name, count))
        for thread_name, count in sorted(thread_counts.items())
    )

    for index, (entry_type, value) in enumerate(entries):
        entry_is_last = index == len(entries) - 1
        entry_connector = "`-" if entry_is_last else "|-"

        if entry_type == "thread":
            thread_name, count = value  # type: ignore[misc]
            lines.append(
                f"{child_prefix}{entry_connector}{count}x {{{thread_name}}} [threads]"
            )
        else:
            lines.extend(
                render_group(
                    value,  # type: ignore[arg-type]
                    level=level + 1,
                    max_depth=max_depth,
                    width=width,
                    processes=processes,
                    prefix=child_prefix,
                    is_last=entry_is_last,
                )
            )

    return lines


def is_matching_process(
    process: Process, targets: set[str], ignored_pids: set[int]
) -> bool:
    """Check if a process matches any of the target names via comm, binary name, runner, or shell command."""
    if process.pid in ignored_pids:
        return False

    name_lower = process.name.lower()
    cmdline = process.cmdline
    cmd_text = " ".join(cmdline).lower() if cmdline else ""

    for target in targets:
        t = target.lower().strip()
        if not t:
            continue

        if t == "all":
            return True

        if t in ("agy", "antigravity"):
            # Kernel comm match
            if name_lower in ("agy", "antigravity", "antigravity-cli", "gemini"):
                return True

            # Binary name or path match
            if cmdline:
                exe = os.path.basename(cmdline[0]).lower()
                if exe in ("agy", "antigravity", "antigravity-cli"):
                    return True

            # Script runner match (e.g. python3 tools/agy_run.py)
            for arg in cmdline:
                base = os.path.basename(arg).lower()
                if base in (
                    "agy_run.py",
                    "antigravity_execute_ipd.py",
                    "agy_sessions.py",
                    "view-antigravity-jsonl.py",
                ):
                    return True

            # Shell subcommand or inline script match (e.g. bash -c "...agy...")
            if (
                "agy " in cmd_text
                or "agy\n" in cmd_text
                or "agy_run" in cmd_text
                or "antigravity" in cmd_text
            ) and "watch-agy" not in cmd_text:
                return True

        else:
            # Generic target matching
            if name_lower == t:
                return True
            if cmdline:
                exe = os.path.basename(cmdline[0]).lower()
                if exe == t or exe.startswith((f"{t}-", f"{t}.")):
                    return True
            if (
                f"{t} " in cmd_text
                or f"/{t} " in cmd_text
                or cmd_text.endswith(f"/{t}")
            ):
                return True

    return False


def matching_roots(processes: dict[int, Process], targets: set[str]) -> list[Process]:
    """Find matching processes not already beneath another matching process."""
    # Compute self and ancestor PIDs for watch-agy itself so it never monitors itself
    my_pids = {os.getpid()}
    cur = os.getpid()
    while cur in processes:
        my_pids.add(cur)
        cur = processes[cur].ppid

    matches = [
        process
        for process in processes.values()
        if is_matching_process(process, targets, my_pids)
    ]
    match_pids = {process.pid for process in matches}
    roots: list[Process] = []

    for process in matches:
        ancestor_pid = process.ppid
        seen: set[int] = set()
        nested = False

        while ancestor_pid in processes and ancestor_pid not in seen:
            if ancestor_pid in match_pids:
                nested = True
                break
            seen.add(ancestor_pid)
            ancestor_pid = processes[ancestor_pid].ppid

        if not nested:
            roots.append(process)

    return roots


def render_snapshot(process_spec: str, max_depth: int, width: int) -> str:
    processes = read_processes()
    targets = {t.strip() for t in process_spec.split(",") if t.strip()}
    roots = matching_roots(processes, targets)
    if not roots:
        return f"No processes matching {process_spec!r} found."

    sections = []
    for group in group_processes(roots):
        sections.append(
            "\n".join(
                render_group(
                    group,
                    level=0,
                    max_depth=max_depth,
                    width=width,
                    processes=processes,
                    is_root=True,
                )
            )
        )
    return "\n\n".join(sections)


def positive_float(value: str) -> float:
    result = float(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return result


def nonnegative_int(value: str) -> int:
    result = int(value)
    if result < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return result


def positive_int(value: str) -> int:
    result = int(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return result


ENTER_ALT_SCREEN = "\033[?1049h\033[?25l"
LEAVE_ALT_SCREEN = "\033[?1049l\033[?25h"
CURSOR_HOME = "\033[H"
CLEAR_TO_EOS = "\033[J"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Continuously show process trees for agy and other agent-launched processes, "
            "collapsing identical sibling processes and same-name threads."
        )
    )
    parser.add_argument(
        "--process",
        default="agy",
        help="process name(s) to watch (comma-separated, default: agy; matches comm, cmdline, and runners)",
    )
    parser.add_argument(
        "--depth",
        type=nonnegative_int,
        default=4,
        help="descendant levels shown below each root (default: 4)",
    )
    parser.add_argument(
        "--interval",
        type=positive_float,
        default=1.0,
        help="seconds between snapshots (default: 1)",
    )
    parser.add_argument(
        "--width",
        type=positive_int,
        default=120,
        help="maximum width of each process label (default: 120)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="print one snapshot and exit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    is_interactive = not args.once and sys.stdout.isatty()

    def stop_cleanly(_signum: int, _frame: object) -> None:
        raise SystemExit(0)

    signal.signal(signal.SIGINT, stop_cleanly)
    signal.signal(signal.SIGTERM, stop_cleanly)

    try:
        if is_interactive:
            sys.stdout.write(ENTER_ALT_SCREEN)
            sys.stdout.flush()

        while True:
            header = (
                f"{args.process} process trees (every {args.interval}s) -- "
                f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            snapshot = render_snapshot(args.process, args.depth, args.width)

            if is_interactive:
                sys.stdout.write(f"{CURSOR_HOME}{header}{snapshot}\n{CLEAR_TO_EOS}")
                sys.stdout.flush()
            else:
                sys.stdout.write(f"{header}{snapshot}\n")
                sys.stdout.flush()

            if args.once:
                return 0
            time.sleep(args.interval)
    except (KeyboardInterrupt, SystemExit):
        return 0
    except RuntimeError as error:
        print(f"watch-agy: {error}", file=sys.stderr)
        return 1
    finally:
        if is_interactive:
            sys.stdout.write(LEAVE_ALT_SCREEN)
            sys.stdout.flush()


if __name__ == "__main__":
    raise SystemExit(main())
