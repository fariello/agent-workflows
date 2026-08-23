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

# --- 256-Color & ANSI Palette ---
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"

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
    text: str, max_width: int, color_enabled: bool, show_long: bool = False
) -> str:
    """Truncate text to max_width visible characters, preserving ANSI codes."""
    if show_long:
        return text

    if not color_enabled:
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
                threads=read_threads(pid) if proc_dir == Path("/proc") else Counter(),
            )
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            continue

    for process in processes.values():
        parent = processes.get(process.ppid)
        if parent is not None:
            parent.children.append(process)

    return processes


def get_process_color(name: str) -> str:
    """Return appropriate 256-color code based on process role."""
    n = name.lower()
    if n in ("agy", "antigravity", "antigravity-cli", "gemini"):
        return C_AGY
    if n in ("opencode", "claude", "codex", "hermes"):
        return C_AGENT
    if n in ("python", "python3", "node", "bun", "deno"):
        return C_PYTHON
    if n in ("bash", "sh", "zsh", "fish", "dash"):
        return C_SHELL
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
        return C_TOOL
    return C_PROC_DEFAULT


def format_colored_argument(arg: str, color_enabled: bool) -> str:
    """Format an argument with shell quoting and syntax highlighting."""
    quoted = shlex.quote(arg)
    if not color_enabled:
        return quoted

    if arg.startswith("-"):
        return f"{C_ARG_FLAG}{quoted}{C_RESET}"
    if "/" in arg or arg.endswith((".py", ".md", ".json", ".sh", ".txt", ".rs", ".go")):
        return f"{C_ARG_PATH}{quoted}{C_RESET}"
    return f"{C_ARG_TEXT}{quoted}{C_RESET}"


def format_arguments(arguments: tuple[str, ...], color_enabled: bool) -> str:
    if not color_enabled:
        return " ".join(shlex.quote(arg) for arg in arguments)
    return " ".join(format_colored_argument(arg, color_enabled) for arg in arguments)


def process_label(
    members: list[Process],
    width: int,
    *,
    is_root: bool = False,
    processes: dict[int, Process] | None = None,
    color_enabled: bool = True,
    show_long: bool = False,
) -> str:
    representative = members[0]
    arguments = format_arguments(representative.arguments, color_enabled)

    # Parent suffix for root processes
    parent_suffix = ""
    if is_root and processes and representative.ppid in processes:
        parent = processes[representative.ppid]
        if parent.pid > 1:
            if color_enabled:
                parent_suffix = (
                    f" {C_PARENT}[parent: {parent.name},{parent.pid}]{C_RESET}"
                )
            else:
                parent_suffix = f" [parent: {parent.name},{parent.pid}]"

    # Head (count + process name + PID)
    proc_color = get_process_color(representative.name) if color_enabled else ""
    reset = C_RESET if color_enabled else ""

    if len(members) == 1:
        if color_enabled:
            head = f"{proc_color}{representative.name}{reset}{C_PID},{representative.pid}{reset}"
        else:
            head = f"{representative.name},{representative.pid}"
    else:
        if color_enabled:
            head = f"{C_COUNT}{len(members)}x{reset} {proc_color}{representative.name}{reset}"
        else:
            head = f"{len(members)}x {representative.name}"

    label = f"{head} {arguments}".rstrip()
    if parent_suffix:
        label = f"{label}{parent_suffix}"
    return ansi_truncate(label, width, color_enabled, show_long=show_long)


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
) -> list[str]:
    # Use Unicode box line art characters
    tree_c = C_TREE if color_enabled else ""
    reset = C_RESET if color_enabled else ""

    if is_root:
        connector = ""
    elif is_last:
        connector = f"{tree_c}└── {reset}"
    else:
        connector = f"{tree_c}├── {reset}"

    lines = [
        f"{prefix}{connector}{process_label(members, width, is_root=is_root, processes=processes, color_enabled=color_enabled, show_long=show_long)}"
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
            if color_enabled:
                lines.append(
                    f"{child_prefix}{entry_connector}{C_THREAD}{count}x {{{thread_name}}}{C_RESET} {C_THREAD_TAG}[threads]{C_RESET}"
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
                    color_enabled=color_enabled,
                    show_long=show_long,
                    exclude_rules=exclude_rules,
                    prefix=child_prefix,
                    is_last=entry_is_last,
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
) -> list[Process]:
    """Find matching processes not already beneath another matching process."""
    # Compute self and ancestor PIDs for pwatch itself so it never monitors itself
    my_pids = {os.getpid()}
    cur = os.getpid()
    while cur in processes:
        my_pids.add(cur)
        cur = processes[cur].ppid

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
) -> tuple[str, list[Process]]:
    roots = matching_roots(processes, proc_rules, exclude_rules)
    if not roots:
        pat_desc = ", ".join(r.pattern for r in proc_rules)
        if color_enabled:
            return f"{C_DIM}No processes matching {pat_desc!r} found.{C_RESET}", []
        return f"No processes matching {pat_desc!r} found.", []

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
                    color_enabled=color_enabled,
                    show_long=show_long,
                    exclude_rules=exclude_rules,
                    is_root=True,
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
        prog="pwatch",
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

    if not proc_rules:
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

    color_enabled = (
        not args.no_color and os.environ.get("NO_COLOR") is None and sys.stdout.isatty()
    )

    def stop_cleanly(_signum: int, _frame: object) -> None:
        raise SystemExit(0)

    signal.signal(signal.SIGINT, stop_cleanly)
    signal.signal(signal.SIGTERM, stop_cleanly)

    # Summary of active filters for banner
    summary_parts = [r.pattern for r in proc_rules]
    summary_str = ", ".join(summary_parts)

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
            snapshot, roots = render_snapshot(
                processes,
                proc_rules,
                exclude_rules,
                args.depth,
                effective_width,
                color_enabled=color_enabled,
                show_long=args.long,
            )

            # Record matching processes in tree if recorder active
            if recorder is not None:
                recorder.record_snapshot(roots, now_iso, now_epoch)

            rec_banner = ""
            if recorder is not None:
                if color_enabled:
                    rec_banner = f" {C_RECORD}[recording -> {recorder.output_path.name}]{C_RESET}"
                else:
                    rec_banner = f" [recording -> {recorder.output_path.name}]"

            if color_enabled:
                header = (
                    f"{C_BANNER}pwatch: {summary_str}{C_RESET}{rec_banner} "
                    f"{C_DIM}(every {args.interval}s){C_RESET} {C_TREE}──{C_RESET} "
                    f"{C_TIMESTAMP}{now_display}{C_RESET}\n\n"
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

    except (KeyboardInterrupt, SystemExit):
        return 0
    except RuntimeError as error:
        print(f"pwatch: {error}", file=sys.stderr)
        return 1
    finally:
        if is_interactive:
            sys.stdout.write(LEAVE_ALT_SCREEN)
            sys.stdout.flush()


if __name__ == "__main__":
    raise SystemExit(main())
