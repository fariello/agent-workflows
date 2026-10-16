#!/usr/bin/env python3
"""Generic process-tree watcher and recorder (pwatch).

Monitors and visualizes process trees matching user-defined strings or regular expressions,
collapsing identical sibling processes and same-name threads with Unicode box line art
and rich 256-color syntax styling. Supports exclusion rules and structured JSONL recording.

Linux only: process and thread information is read directly from /proc.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import signal
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional

from agent_workflows import term

# --- 256-Color & ANSI Palette ---
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"

# Exit status returned on SIGTERM (aligned with render_stream.install_exit_signal_handler
# and oc_runipd.main's 'return 143 if is_sigterm else 130').
EXIT_SIGTERM = 143


# Tree box-drawing guides
C_TREE = "\033[38;5;241m"  # Slate gray for branch connectors

# Process names by role
C_AGY = "\033[1;38;5;48m"  # Bold emerald green for agy / antigravity
C_AGENT = "\033[1;38;5;177m"  # Bold orchid/purple for opencode / claude / codex
C_PYTHON = "\033[1;38;5;75m"  # Bold sky blue for python3 / python / node
C_SHELL = "\033[1;38;5;208m"  # Bold warm amber for bash / sh / zsh
C_TOOL = "\033[1;38;5;221m"  # Bold gold/yellow for make / pytest / git / hound / tail
C_PROC_DEFAULT = "\033[1;38;5;255m"  # Bold crisp white

# Accents and details
C_PID = "\033[38;5;245m"  # Cool gray for PID
C_COUNT = "\033[1;38;5;220m"  # Bright yellow for count (e.g. 3x)
C_PARENT = "\033[38;5;141m"  # Soft lavender for [parent: ...]
C_THREAD = "\033[38;5;139m"  # Soft purple for thread counts
C_THREAD_TAG = "\033[38;5;242m"  # Muted gray for [threads] tag
C_BANNER = "\033[1;38;5;39m"  # Electric cyan for title banner
C_RECORD = "\033[1;38;5;203m"  # Coral red for recording indicator
C_TIMESTAMP = "\033[38;5;244m"  # Medium gray for timestamp

# Command line argument styling
C_ARG_FLAG = "\033[38;5;117m"  # Ice cyan for flags (-c, --foo)
C_ARG_PATH = "\033[38;5;186m"  # Muted cream/khaki for file paths & scripts
C_ARG_TEXT = "\033[38;5;252m"  # Off-white for general arguments

# Integer palette index constants (256-color palette indices)
IDX_TREE = 241
IDX_AGY = 48
IDX_AGENT = 177
IDX_PYTHON = 75
IDX_SHELL = 208
IDX_TOOL = 221
IDX_PROC_DEFAULT = 255
IDX_PID = 245
IDX_COUNT = 220
IDX_PARENT = 141
IDX_THREAD = 139
IDX_THREAD_TAG = 242
IDX_BANNER = 39
IDX_RECORD = 203
IDX_TIMESTAMP = 244
IDX_ARG_FLAG = 117
IDX_ARG_PATH = 186
IDX_ARG_TEXT = 252
IDX_RUNNER_DEC = 81


def _effective_depth(color_enabled: bool, *, depth: str | None = None) -> str:
    """Return the effective color depth tier based on color_enabled and optional depth."""
    if not color_enabled:
        return term.DEPTH_NONE
    if depth in term.COLOR_DEPTHS:
        return depth
    return term.resolve_color_depth(override=True)


def sgr_256(code: int, *, bold: bool = False, depth: str | None = None) -> str:
    """Format an SGR escape sequence for a 256-color palette index honoring depth."""
    tier = term.resolve_color_depth(override=True) if depth is None else depth
    if tier == term.DEPTH_NONE:
        return ""
    prefix = "1;" if bold else ""
    if tier == term.DEPTH_16:
        return f"\033[{prefix}{term.color_16_for_index(code)}m"
    return f"\033[{prefix}38;5;{code}m"


# Terminal control escapes
ENTER_ALT_SCREEN = "\033[?1049h\033[?25l"
LEAVE_ALT_SCREEN = "\033[?1049l\033[?25h"
CURSOR_HOME = "\033[H"
CLEAR_LINE = "\033[K"
CLEAR_TO_EOS = "\033[J"

ANSI_PATTERN = re.compile(r"\033\[[0-9;]*[a-zA-Z]")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes to compute visible string length."""
    return ANSI_PATTERN.sub("", text)


def ansi_truncate(
    text: str,
    max_width: int,
    color_enabled: bool,
    show_long: bool = False,
    *,
    depth: str | None = None,
) -> str:
    """Truncate text to max_width visible characters, preserving ANSI codes."""
    if show_long:
        return text

    tier = _effective_depth(color_enabled, depth=depth)
    if tier == term.DEPTH_NONE:
        clean = strip_ansi(text)
        if len(clean) <= max_width:
            return clean
        return clean[: max(1, max_width - 3)].rstrip() + "..."

    visible_len = len(strip_ansi(text))
    if visible_len <= max_width:
        return text

    target_len = max(1, max_width - 3)
    accumulated = 0
    out: list[str] = []
    i = 0
    while i < len(text) and accumulated < target_len:
        match = ANSI_PATTERN.match(text, i)
        if match:
            out.append(match.group(0))
            i = match.end()
        else:
            out.append(text[i])
            accumulated += 1
            i += 1

    out.append(f"{C_DIM}...{C_RESET}")
    return "".join(out)


class MatchKind(Enum):
    MATCH_CS = auto()  # Substring match, case sensitive
    MATCH_CI = auto()  # Substring match, case insensitive
    REGEX_CS = auto()  # Regular expression match, case sensitive
    REGEX_CI = auto()  # Regular expression match, case insensitive


@dataclass(frozen=True)
class Rule:
    pattern: str
    kind: MatchKind
    _compiled: Optional[re.Pattern[str]] = field(
        default=None, repr=False, compare=False
    )

    @classmethod
    def create(cls, pattern: str, kind: MatchKind) -> Rule:
        compiled: Optional[re.Pattern[str]] = None
        if kind == MatchKind.REGEX_CS:
            compiled = re.compile(pattern)
        elif kind == MatchKind.REGEX_CI:
            compiled = re.compile(pattern, re.IGNORECASE)
        return cls(pattern=pattern, kind=kind, _compiled=compiled)

    def matches_process(self, process: Process) -> bool:
        name = process.name
        cmdline = process.cmdline
        full_cmd = " ".join(cmdline) if cmdline else ""
        exe = os.path.basename(cmdline[0]) if cmdline else ""

        if self.kind == MatchKind.MATCH_CS:
            p = self.pattern
            if (
                p == name
                or p in name
                or (exe and p in exe)
                or (full_cmd and p in full_cmd)
            ):
                return True
            for arg in cmdline:
                if p == arg or p == os.path.basename(arg) or p in arg:
                    return True
            return False

        elif self.kind == MatchKind.MATCH_CI:
            p = self.pattern.lower()
            name_l = name.lower()
            full_cmd_l = full_cmd.lower()
            exe_l = exe.lower()
            if (
                p == name_l
                or p in name_l
                or (exe_l and p in exe_l)
                or (full_cmd_l and p in full_cmd_l)
            ):
                return True
            for arg in cmdline:
                arg_l = arg.lower()
                if p == arg_l or p == os.path.basename(arg_l) or p in arg_l:
                    return True
            return False

        elif self.kind in (MatchKind.REGEX_CS, MatchKind.REGEX_CI):
            rx = self._compiled
            if rx is None:
                return False
            if (
                rx.search(name)
                or (exe and rx.search(exe))
                or (full_cmd and rx.search(full_cmd))
            ):
                return True
            for arg in cmdline:
                if rx.search(arg) or rx.search(os.path.basename(arg)):
                    return True
            return False

        return False


@dataclass
class Process:
    pid: int
    ppid: int
    name: str
    cmdline: tuple[str, ...]
    threads: Counter[str] = field(default_factory=Counter)
    children: list[Process] = field(default_factory=list)
    utime: int = 0
    stime: int = 0
    rss_bytes: int = 0
    cpu_percent: float = 0.0

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
            continue

    return counts


def read_processes(proc_dir: Path = Path("/proc")) -> dict[int, Process]:
    processes: dict[int, Process] = {}

    try:
        proc_entries = list(proc_dir.iterdir())
    except FileNotFoundError as error:
        raise RuntimeError(
            f"{proc_dir} is unavailable; this script requires Linux"
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
            stat_parts = stat[closing_parenthesis + 2 :].split()
            ppid = int(stat_parts[1])
            utime = int(stat_parts[11]) if len(stat_parts) > 11 else 0
            stime = int(stat_parts[12]) if len(stat_parts) > 12 else 0

            rss_bytes = 0
            if proc_dir == Path("/proc"):
                try:
                    statm = (
                        (entry / "statm")
                        .read_text(encoding="utf-8", errors="replace")
                        .split()
                    )
                    if len(statm) > 1:
                        rss_bytes = int(statm[1]) * 4096
                except (
                    FileNotFoundError,
                    PermissionError,
                    ProcessLookupError,
                    ValueError,
                ):
                    pass

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
                threads=read_threads(pid) if proc_dir == Path("/proc") else Counter(),
                utime=utime,
                stime=stime,
                rss_bytes=rss_bytes,
            )
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            continue

    for process in processes.values():
        parent = processes.get(process.ppid)
        if parent is not None:
            parent.children.append(process)

    return processes


def get_process_color(name: str, *, depth: str | None = None) -> str:
    """Return appropriate 256-color code based on process role."""
    tier = term.resolve_color_depth(override=True) if depth is None else depth
    if tier == term.DEPTH_NONE:
        return ""
    n = name.lower()
    if n in ("agy", "antigravity", "antigravity-cli", "gemini"):
        return sgr_256(IDX_AGY, bold=True, depth=tier)
    if n in ("opencode", "claude", "codex", "hermes"):
        return sgr_256(IDX_AGENT, bold=True, depth=tier)
    if n in ("python", "python3", "node", "bun", "deno"):
        return sgr_256(IDX_PYTHON, bold=True, depth=tier)
    if n in ("bash", "sh", "zsh", "fish", "dash"):
        return sgr_256(IDX_SHELL, bold=True, depth=tier)
    if n in (
        "make",
        "pytest",
        "git",
        "hound",
        "tail",
        "grep",
        "pyright",
        "cargo",
        "go",
    ):
        return sgr_256(IDX_TOOL, bold=True, depth=tier)
    return sgr_256(IDX_PROC_DEFAULT, bold=True, depth=tier)


def format_colored_argument(
    arg: str, color_enabled: bool, *, depth: str | None = None
) -> str:
    """Format an argument with shell quoting and syntax highlighting."""
    quoted = shlex.quote(arg)
    tier = _effective_depth(color_enabled, depth=depth)
    if tier == term.DEPTH_NONE:
        return quoted

    if arg.startswith("-"):
        return f"{sgr_256(IDX_ARG_FLAG, depth=tier)}{quoted}{C_RESET}"
    if "/" in arg or arg.endswith((".py", ".md", ".json", ".sh", ".txt", ".rs", ".go")):
        return f"{sgr_256(IDX_ARG_PATH, depth=tier)}{quoted}{C_RESET}"
    return f"{sgr_256(IDX_ARG_TEXT, depth=tier)}{quoted}{C_RESET}"


def format_arguments(
    arguments: tuple[str, ...], color_enabled: bool, *, depth: str | None = None
) -> str:
    tier = _effective_depth(color_enabled, depth=depth)
    if tier == term.DEPTH_NONE:
        return " ".join(shlex.quote(arg) for arg in arguments)
    return " ".join(
        format_colored_argument(arg, color_enabled, depth=tier) for arg in arguments
    )


def process_label(
    members: list[Process],
    width: int,
    *,
    is_root: bool = False,
    processes: dict[int, Process] | None = None,
    color_enabled: bool = True,
    show_long: bool = False,
    runner_decorations: dict[int, str] | None = None,
    depth: str | None = None,
) -> str:
    tier = _effective_depth(color_enabled, depth=depth)
    styled = tier != term.DEPTH_NONE

    representative = members[0]
    arguments = format_arguments(representative.arguments, styled, depth=tier)

    # Parent suffix for root processes
    parent_suffix = ""
    if is_root and processes and representative.ppid in processes:
        parent = processes[representative.ppid]
        if parent.pid > 1:
            if styled:
                c_parent = sgr_256(IDX_PARENT, depth=tier)
                parent_suffix = (
                    f" {c_parent}[parent: {parent.name},{parent.pid}]{C_RESET}"
                )
            else:
                parent_suffix = f" [parent: {parent.name},{parent.pid}]"

    # Head (count + process name + PID)
    proc_color = get_process_color(representative.name, depth=tier) if styled else ""
    reset = C_RESET if styled else ""
    c_pid = sgr_256(IDX_PID, depth=tier) if styled else ""

    if len(members) == 1:
        if styled:
            head = f"{proc_color}{representative.name}{reset}{c_pid},{representative.pid}{reset}"
        else:
            head = f"{representative.name},{representative.pid}"
    else:
        if styled:
            c_count = sgr_256(IDX_COUNT, bold=True, depth=tier)
            head = f"{c_count}{len(members)}x{reset} {proc_color}{representative.name}{reset}"
        else:
            head = f"{len(members)}x {representative.name}"

    runner_suffix = ""
    if is_root and runner_decorations and representative.pid in runner_decorations:
        runner_suffix = f" {runner_decorations[representative.pid]}"

    label = f"{head} {arguments}".rstrip()
    if runner_suffix:
        label = f"{label}{runner_suffix}"
    if parent_suffix:
        label = f"{label}{parent_suffix}"
    return ansi_truncate(label, width, styled, show_long=show_long, depth=tier)


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
    color_enabled: bool = True,
    show_long: bool = False,
    exclude_rules: list[Rule] | None = None,
    prefix: str = "",
    is_last: bool = True,
    is_root: bool = False,
    runner_decorations: dict[int, str] | None = None,
    depth: str | None = None,
) -> list[str]:
    tier = _effective_depth(color_enabled, depth=depth)
    styled = tier != term.DEPTH_NONE

    # Use Unicode box line art characters
    tree_c = sgr_256(IDX_TREE, depth=tier) if styled else ""
    reset = C_RESET if styled else ""

    if is_root:
        connector = ""
    elif is_last:
        connector = f"{tree_c}└── {reset}"
    else:
        connector = f"{tree_c}├── {reset}"

    lines = [
        f"{prefix}{connector}{process_label(members, width, is_root=is_root, processes=processes, color_enabled=styled, show_long=show_long, runner_decorations=runner_decorations, depth=tier)}"
    ]

    if level >= max_depth:
        return lines

    if is_root:
        child_prefix = prefix
    elif is_last:
        child_prefix = prefix + "    "
    else:
        child_prefix = prefix + f"{tree_c}│   {reset}"

    thread_counts: Counter[str] = Counter()
    child_processes: list[Process] = []
    for member in members:
        thread_counts.update(member.threads)
        for child in member.children:
            if exclude_rules and any(r.matches_process(child) for r in exclude_rules):
                continue
            child_processes.extend([child])

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
        if entry_is_last:
            entry_connector = f"{tree_c}└── {reset}"
        else:
            entry_connector = f"{tree_c}├── {reset}"

        if entry_type == "thread":
            thread_name, count = value  # type: ignore[misc]
            if styled:
                c_thread = sgr_256(IDX_THREAD, depth=tier)
                c_thread_tag = sgr_256(IDX_THREAD_TAG, depth=tier)
                lines.append(
                    f"{child_prefix}{entry_connector}{c_thread}{count}x {{{thread_name}}}{C_RESET} {c_thread_tag}[threads]{C_RESET}"
                )
            else:
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
                    color_enabled=styled,
                    show_long=show_long,
                    exclude_rules=exclude_rules,
                    prefix=child_prefix,
                    is_last=entry_is_last,
                    runner_decorations=runner_decorations,
                    depth=tier,
                )
            )

    return lines


def is_matching_process(
    process: Process,
    proc_rules: list[Rule],
    exclude_rules: list[Rule],
    ignored_pids: set[int],
) -> bool:
    """Check if a process matches any proc_rules and none of exclude_rules."""
    if process.pid in ignored_pids:
        return False

    if any(rule.matches_process(process) for rule in exclude_rules):
        return False

    return any(rule.matches_process(process) for rule in proc_rules)


def matching_roots(
    processes: dict[int, Process],
    proc_rules: list[Rule],
    exclude_rules: list[Rule],
    root_pids: set[int] | None = None,
) -> list[Process]:
    """Find matching processes not already beneath another matching process."""
    # Compute self and ancestor PIDs for pwatch itself so it never monitors itself
    my_pids = {os.getpid()}
    cur = os.getpid()
    while cur in processes:
        my_pids.add(cur)
        cur = processes[cur].ppid

    if root_pids is not None:
        return [
            processes[pid]
            for pid in sorted(root_pids)
            if pid in processes and pid not in my_pids
        ]

    matches = [
        process
        for process in processes.values()
        if is_matching_process(process, proc_rules, exclude_rules, my_pids)
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


class ProcessRecorder:
    """Records matched processes in the watched tree to a JSONL log."""

    def __init__(
        self,
        output_path: Path,
        record_rules: list[Rule],
        exclude_rules: list[Rule],
    ):
        self.output_path = output_path
        self.record_rules = record_rules
        self.exclude_rules = exclude_rules
        self.seen_pids: dict[int, dict[str, Any]] = {}
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_record(self, record: dict[str, Any]) -> None:
        try:
            with self.output_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as err:
            print(f"pwatch: warning: failed to write log: {err}", file=sys.stderr)

    def record_snapshot(
        self,
        roots: list[Process],
        timestamp_iso: str,
        epoch_time: float,
    ) -> int:
        """Inspect the entire watched tree under roots and record matching processes."""
        if not self.record_rules:
            return 0

        recorded_count = 0
        current_snapshot_pids: set[int] = set()

        def traverse(p: Process, root_pid: int, depth: int) -> None:
            nonlocal recorded_count
            if any(r.matches_process(p) for r in self.exclude_rules):
                return

            matching_rules = [
                r.pattern for r in self.record_rules if r.matches_process(p)
            ]
            if matching_rules:
                current_snapshot_pids.add(p.pid)
                is_first = p.pid not in self.seen_pids
                prev_info = self.seen_pids.get(p.pid, {})
                obs_count = prev_info.get("observations_count", 0) + 1
                first_seen = prev_info.get("first_seen", timestamp_iso)

                self.seen_pids[p.pid] = {
                    "first_seen": first_seen,
                    "last_seen": timestamp_iso,
                    "observations_count": obs_count,
                    "name": p.name,
                    "cmdline": list(p.cmdline),
                    "ppid": p.ppid,
                }

                record = {
                    "timestamp": timestamp_iso,
                    "epoch_time": epoch_time,
                    "event": "first_seen" if is_first else "observed",
                    "pid": p.pid,
                    "ppid": p.ppid,
                    "name": p.name,
                    "cmdline": list(p.cmdline),
                    "exe": os.path.basename(p.cmdline[0]) if p.cmdline else p.name,
                    "arguments": list(p.arguments),
                    "threads": dict(p.threads),
                    "thread_count": sum(p.threads.values()) + 1,
                    "root_pid": root_pid,
                    "tree_depth": depth,
                    "matched_rules": matching_rules,
                    "first_seen": first_seen,
                    "observations_count": obs_count,
                }
                self._write_record(record)
                recorded_count += 1

            for child in p.children:
                traverse(child, root_pid, depth + 1)

        for root in roots:
            traverse(root, root.pid, 0)

        # Detect terminated processes previously tracked
        for prev_pid in list(self.seen_pids.keys()):
            if prev_pid not in current_snapshot_pids:
                info = self.seen_pids.pop(prev_pid)
                term_record = {
                    "timestamp": timestamp_iso,
                    "epoch_time": epoch_time,
                    "event": "terminated",
                    "pid": prev_pid,
                    "ppid": info["ppid"],
                    "name": info["name"],
                    "cmdline": info["cmdline"],
                    "first_seen": info["first_seen"],
                    "last_seen": info["last_seen"],
                    "total_observations": info["observations_count"],
                }
                self._write_record(term_record)

        return recorded_count


def render_snapshot(
    processes: dict[int, Process],
    proc_rules: list[Rule],
    exclude_rules: list[Rule],
    max_depth: int,
    width: int,
    color_enabled: bool = True,
    show_long: bool = False,
    root_pids: set[int] | None = None,
    runner_decorations: dict[int, str] | None = None,
    *,
    depth: str | None = None,
) -> tuple[str, list[Process]]:
    tier = _effective_depth(color_enabled, depth=depth)
    styled = tier != term.DEPTH_NONE

    roots = matching_roots(processes, proc_rules, exclude_rules, root_pids=root_pids)
    if not roots:
        if root_pids is not None:
            msg = "No active aw runners found."
        else:
            pat_desc = ", ".join(r.pattern for r in proc_rules)
            msg = f"No processes matching {pat_desc!r} found."
        if styled:
            return f"{C_DIM}{msg}{C_RESET}", []
        return msg, []

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
                    color_enabled=styled,
                    show_long=show_long,
                    exclude_rules=exclude_rules,
                    is_root=True,
                    runner_decorations=runner_decorations,
                    depth=tier,
                )
            )
        )
    return "\n\n".join(sections), roots


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aw pwatch",
        description=(
            "Continuously show process trees for matching commands and runners, "
            "collapsing identical sibling processes and same-name threads with box line art."
        ),
    )

    # 1. Process matching options
    proc_group = parser.add_argument_group("Process matching (at least one required)")
    proc_group.add_argument(
        "-M",
        "--proc-match",
        action="append",
        default=[],
        metavar="STRING",
        help="case-sensitive string to match processes",
    )
    proc_group.add_argument(
        "-m",
        "--proc-imatch",
        action="append",
        default=[],
        metavar="STRING",
        help="case-insensitive string to match processes",
    )
    proc_group.add_argument(
        "-R",
        "--proc-regex",
        action="append",
        default=[],
        metavar="REGEX",
        help="case-sensitive regular expression to match processes",
    )
    proc_group.add_argument(
        "-r",
        "--proc-iregex",
        action="append",
        default=[],
        metavar="REGEX",
        help="case-insensitive regular expression to match processes",
    )
    proc_group.add_argument(
        "patterns",
        nargs="*",
        default=[],
        metavar="PATTERN",
        help="bare search strings (treated as case-insensitive match strings)",
    )

    # 2. Exclude matching options
    excl_group = parser.add_argument_group("Process exclusions (optional)")
    excl_group.add_argument(
        "-eM",
        "--exclude-match",
        action="append",
        default=[],
        metavar="STRING",
        help="case-sensitive string to exclude processes",
    )
    excl_group.add_argument(
        "-em",
        "--exclude-imatch",
        action="append",
        default=[],
        metavar="STRING",
        help="case-insensitive string to exclude processes",
    )
    excl_group.add_argument(
        "-eR",
        "--exclude-regex",
        action="append",
        default=[],
        metavar="REGEX",
        help="case-sensitive regular expression to exclude processes",
    )
    excl_group.add_argument(
        "-er",
        "--exclude-iregex",
        action="append",
        default=[],
        metavar="REGEX",
        help="case-insensitive regular expression to exclude processes",
    )

    # 3. Record matching options
    rec_group = parser.add_argument_group("Process recording (optional)")
    rec_group.add_argument(
        "-rM",
        "--record-match",
        action="append",
        default=[],
        metavar="STRING",
        help="case-sensitive string to record matching processes in watched trees",
    )
    rec_group.add_argument(
        "-rm",
        "--record-imatch",
        action="append",
        default=[],
        metavar="STRING",
        help="case-insensitive string to record matching processes in watched trees",
    )
    rec_group.add_argument(
        "-rR",
        "--record-regex",
        action="append",
        default=[],
        metavar="REGEX",
        help="case-sensitive regular expression to record matching processes in watched trees",
    )
    rec_group.add_argument(
        "-rr",
        "--record-iregex",
        action="append",
        default=[],
        metavar="REGEX",
        help="case-insensitive regular expression to record matching processes in watched trees",
    )
    rec_group.add_argument(
        "--record-file",
        "-o",
        default=None,
        metavar="PATH",
        help="custom path for recorded JSONL (default: ./pwatch-YYYYMMDD-HHMMSS-<pid>.jsonl)",
    )

    # General display options
    disp_group = parser.add_argument_group("Display and execution options")
    disp_group.add_argument(
        "--depth",
        type=nonnegative_int,
        default=6,
        help="descendant levels shown below each root (default: 6)",
    )
    disp_group.add_argument(
        "--interval",
        type=positive_float,
        default=2.5,
        help="seconds between snapshots (default: 2.5)",
    )
    disp_group.add_argument(
        "--width",
        type=positive_int,
        default=120,
        help="maximum width of each process label (default: 120)",
    )
    disp_group.add_argument(
        "-l",
        "--long",
        action="store_true",
        help="show full untruncated command-line arguments regardless of terminal width",
    )
    disp_group.add_argument(
        "--no-color",
        action="store_true",
        help="disable 256-color output and ANSI styling",
    )
    disp_group.add_argument(
        "--runners",
        action="store_true",
        help="automatically discover and watch all active aw runner process trees",
    )
    disp_group.add_argument(
        "--table",
        action="store_true",
        help="display runner journey and resource dashboard table instead of a tree",
    )
    disp_group.add_argument(
        "--raw-cpu",
        action="store_true",
        help="show unscaled per-core CPU percentages instead of percentage of all CPUs",
    )
    disp_group.add_argument(
        "--repo",
        "-d",
        type=Path,
        default=Path("."),
        help="target repository root for runner discovery (default: current directory)",
    )
    disp_group.add_argument(
        "--once",
        action="store_true",
        help="print one snapshot and exit",
    )

    return parser


def compile_rules(
    match_cs: list[str],
    match_ci: list[str],
    regex_cs: list[str],
    regex_ci: list[str],
) -> list[Rule]:
    rules: list[Rule] = []
    for s in match_cs:
        if s:
            rules.append(Rule.create(s, MatchKind.MATCH_CS))
    for s in match_ci:
        if s:
            rules.append(Rule.create(s, MatchKind.MATCH_CI))
    for r in regex_cs:
        if r:
            try:
                rules.append(Rule.create(r, MatchKind.REGEX_CS))
            except re.error as err:
                raise ValueError(f"invalid regular expression {r!r}: {err}") from err
    for r in regex_ci:
        if r:
            try:
                rules.append(Rule.create(r, MatchKind.REGEX_CI))
            except re.error as err:
                raise ValueError(f"invalid regular expression {r!r}: {err}") from err
    return rules


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "runners", False) and getattr(args, "table", False):
        from agent_workflows import runners_monitor

        return runners_monitor.run_table_dashboard(args)

    # Gather match rules
    match_ci = list(args.proc_imatch) + list(args.patterns)
    try:
        proc_rules = compile_rules(
            args.proc_match,
            match_ci,
            args.proc_regex,
            args.proc_iregex,
        )
    except ValueError as err:
        print(f"pwatch: error: {err}", file=sys.stderr)
        return 2

    if not proc_rules and not getattr(args, "runners", False):
        print(
            "pwatch: error: at least one process match pattern is required "
            "(-M, -m, -R, -r, or bare pattern arguments)",
            file=sys.stderr,
        )
        return 2

    # Gather exclude rules
    try:
        exclude_rules = compile_rules(
            args.exclude_match,
            args.exclude_imatch,
            args.exclude_regex,
            args.exclude_iregex,
        )
    except ValueError as err:
        print(f"pwatch: error: {err}", file=sys.stderr)
        return 2

    # Gather record rules
    try:
        record_rules = compile_rules(
            args.record_match,
            args.record_imatch,
            args.record_regex,
            args.record_iregex,
        )
    except ValueError as err:
        print(f"pwatch: error: {err}", file=sys.stderr)
        return 2

    # Setup recorder if record rules provided
    recorder: Optional[ProcessRecorder] = None
    if record_rules:
        if args.record_file:
            log_path = Path(args.record_file)
        else:
            stamp = time.strftime("%Y%m%d-%H%M%S")
            log_path = Path(f"./pwatch-{stamp}-{os.getpid()}.jsonl")
        recorder = ProcessRecorder(log_path, record_rules, exclude_rules)

    is_interactive = not args.once and sys.stdout.isatty()

    # The `--no-color` FLAG sits ABOVE the shared capability decision, which is the whole shape of
    # this expression (IPD `z8ddk0` E-04). `term.should_color` reads no argparse state and cannot,
    # so replacing the whole expression with a bare call would SILENTLY DELETE the flag; measured on
    # a real pty 2026-09-19, that naive replacement returns True with `--no-color` passed. The two
    # shipped tests that pass `--no-color` run through a PIPE, where `isatty()` is already False, so
    # they keep passing with the flag entirely removed and cannot detect the loss - hence the former
    # pty-based case in `tests/test_pwatch.py` (deleted in `19313eed`; restored in
    # `tests/test_pwatch_tty_color.py` for Linux only).
    #
    # WHAT DELEGATING CHANGED: this module previously reimplemented the decision and IGNORED
    # `FORCE_COLOR` completely, so `FORCE_COLOR=1 aw pwatch | cat` was plain while every other
    # command colorized, and it ignored `TERM`, so `TERM=dumb` got color. Both are now `term`'s
    # answers.
    depth = term.DEPTH_NONE if args.no_color else term.resolve_color_depth(sys.stdout)
    color_enabled = depth != term.DEPTH_NONE

    old_sigint = signal.getsignal(signal.SIGINT)
    old_sigterm = signal.getsignal(signal.SIGTERM)

    def stop_cleanly(signum: int, _frame: object) -> None:
        if signum == signal.SIGTERM:
            raise SystemExit(EXIT_SIGTERM)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, stop_cleanly)
    signal.signal(signal.SIGTERM, stop_cleanly)

    try:
        if is_interactive:
            sys.stdout.write(ENTER_ALT_SCREEN)
            sys.stdout.flush()

        while True:
            if is_interactive and not args.long:
                term_cols = shutil.get_terminal_size((args.width, 24)).columns
                effective_width = min(args.width, max(20, term_cols - 1))
            else:
                effective_width = args.width

            now_epoch = time.time()
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now_epoch))
            now_display = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_epoch))

            processes = read_processes()
            root_pids: set[int] | None = None
            runner_decorations: dict[int, str] | None = None

            if getattr(args, "runners", False):
                from agent_workflows import runners_monitor

                repo = Path(getattr(args, "repo", ".") or ".").resolve()
                active_runners = runners_monitor.find_active_runners(repo)
                root_pids = {pid for pid, _dir, _id in active_runners}
                runner_decorations = {}
                for pid, r_dir, r_id in active_runners:
                    step_str, setid, id6, action, attempt, host = (
                        runners_monitor.extract_journey_info(r_dir)
                    )
                    descendants = {pid}
                    stack = [pid]
                    while stack:
                        curr = stack.pop()
                        for p in processes.values():
                            if p.ppid == curr and p.pid not in descendants:
                                descendants.add(p.pid)
                                stack.append(p.pid)
                    activity = " ".join(
                        runners_monitor.classify_activity(
                            pid, descendants, processes, host
                        ).split()
                    )
                    tot_rss = sum(
                        processes[p].rss_bytes for p in descendants if p in processes
                    )
                    tot_cpu = sum(
                        processes[p].cpu_percent for p in descendants if p in processes
                    )
                    total_cpus = os.cpu_count() or 1
                    sys_pct = tot_cpu / total_cpus
                    parts = [
                        f"step {step_str}",
                        f"set: {setid}",
                        f"id6: {id6} ({action})",
                        activity,
                    ]
                    if tot_cpu > 0.0:
                        if getattr(args, "raw_cpu", False):
                            parts.append(f"{tot_cpu:.1f}% CPU")
                        else:
                            parts.append(f"{sys_pct:.1f}% of {total_cpus} CPUs")
                    parts.append(f"{runners_monitor.format_bytes(tot_rss)} RAM")
                    dec_text = f"[{' | '.join(parts)}]"
                    if color_enabled:
                        c_run_dec = sgr_256(IDX_RUNNER_DEC, depth=depth)
                        runner_decorations[pid] = f"{c_run_dec}{dec_text}{C_RESET}"
                    else:
                        runner_decorations[pid] = dec_text

            snapshot, roots = render_snapshot(
                processes,
                proc_rules,
                exclude_rules,
                args.depth,
                effective_width,
                color_enabled=color_enabled,
                show_long=args.long,
                root_pids=root_pids,
                runner_decorations=runner_decorations,
                depth=depth,
            )

            # Record matching processes in tree if recorder active
            if recorder is not None:
                recorder.record_snapshot(roots, now_iso, now_epoch)

            rec_banner = ""
            if recorder is not None:
                if color_enabled:
                    c_record = sgr_256(IDX_RECORD, bold=True, depth=depth)
                    rec_banner = f" {c_record}[recording -> {recorder.output_path.name}]{C_RESET}"
                else:
                    rec_banner = f" [recording -> {recorder.output_path.name}]"

            if getattr(args, "runners", False):
                summary_str = "aw runners"
            else:
                summary_parts = [r.pattern for r in proc_rules]
                summary_str = ", ".join(summary_parts)

            if color_enabled:
                c_banner = sgr_256(IDX_BANNER, bold=True, depth=depth)
                c_tree = sgr_256(IDX_TREE, depth=depth)
                c_timestamp = sgr_256(IDX_TIMESTAMP, depth=depth)
                header = (
                    f"{c_banner}pwatch: {summary_str}{C_RESET}{rec_banner} "
                    f"{C_DIM}(every {args.interval}s){C_RESET} {c_tree}──{C_RESET} "
                    f"{c_timestamp}{now_display}{C_RESET}\n\n"
                )
            else:
                header = (
                    f"pwatch: {summary_str}{rec_banner} "
                    f"(every {args.interval}s) -- {now_display}\n\n"
                )

            if is_interactive:
                frame_lines = f"{header}{snapshot}".split("\n")
                frame = "".join(f"{line}{CLEAR_LINE}\n" for line in frame_lines)
                sys.stdout.write(f"{CURSOR_HOME}{frame}{CLEAR_TO_EOS}")
                sys.stdout.flush()
            else:
                sys.stdout.write(f"{header}{snapshot}\n")
                sys.stdout.flush()

            if args.once:
                return 0
            time.sleep(args.interval)

    except KeyboardInterrupt:
        return 0
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 0
    except RuntimeError as error:
        print(f"pwatch: {error}", file=sys.stderr)
        return 1
    finally:
        if old_sigint is not None:
            signal.signal(signal.SIGINT, old_sigint)
        if old_sigterm is not None:
            signal.signal(signal.SIGTERM, old_sigterm)
        if is_interactive:
            sys.stdout.write(LEAVE_ALT_SCREEN)
            sys.stdout.flush()


if __name__ == "__main__":
    raise SystemExit(main())
