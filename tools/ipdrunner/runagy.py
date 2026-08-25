#!/usr/bin/env python3
"""Restartable non-interactive Antigravity (agy) driver for reviewing and executing IPDs (runagy).

This driver manages execution, review, and verification queues for IPDs, Sets, and plan files:
- For plans with status 'to-review' (or 'draft'), it invokes Antigravity with `/plan-review <path>`.
- For plans with status 'approved', it executes them step-by-step using the durable
  driver runbook and records outcome state.
- After an execution turn, it automatically executes a rigorous skeptical verification turn
  in a clean, fresh Antigravity session (unless --no-verify is passed).
- Stores durable run records under the repository's `.aw/records/runs/` directory.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Iterable, NamedTuple, TextIO

SCHEMA_VERSION = 1
DEFAULT_MODEL = "gemini-3.7-flash-high"
DEFAULT_TIMEOUT = "240m"
DEFAULT_STALL_TIMEOUT: float = 600.0
_SIGINT_GRACE_SECONDS = 5.0
_SIGTERM_GRACE_SECONDS = 2.0

TERMINAL_STATES = {
    "executed",
    "reviewed",
    "approved",
    "substantially-complete",
    "partial",
    "blocked",
    "dependency-blocked",
    "failed-safely",
    "not-attempted",
}
SUCCESS_STATES = {"executed", "reviewed", "approved"}
EXECUTION_SUCCESS_STATES = {"executed", "substantially-complete"}
ID6_RE = re.compile(r"^[a-z0-9]{6}$")

# Frontmatter and filename extraction regexes
_ID_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")
_STATUS_RE = re.compile(r"(?m)^-\s*Status:\s*(\S+)\s*$")
_SET_RE = re.compile(r"(?m)^-\s*Set:\s*(.+?)\s*$")
_ORDER_RE = re.compile(r"(?m)^-\s*Order:\s*(\d+)\s*$")
_DEPS_RE = re.compile(r"(?m)^-\s*(?:Dependencies|Depends-on):\s*(.+?)\s*$")
_PLAN_FILENAME_RE = re.compile(
    r"^\d{8}-([a-z0-9_-]+)-(\d{1,3})-([a-z0-9]{6})-(.+)\.(ipd|draft|plan)\.md$"
)

# Terminal output verbosity for the streamed child-agent turn.
OUTPUT_MODES = ("clean", "quiet", "raw")

# ANSI SGR codes.
_ANSI_RESET = "\033[0m"
_ANSI_CODES = {
    "bold": "1",
    "dim": "2",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "gray": "90",
}
_ANSI_STRIP_RE = re.compile(r"\033\[[0-9;]*m")

_STATUS_COLOR = {
    "executed": "green",
    "reviewed": "green",
    "approved": "green",
    "substantially-complete": "green",
    "partial": "yellow",
    "blocked": "yellow",
    "dependency-blocked": "yellow",
    "failed-safely": "red",
    "not-attempted": "gray",
    "interrupted": "yellow",
    "running": "cyan",
    "queued": "gray",
}


def should_color(stream: TextIO | None = None) -> bool:
    """Decide whether to emit ANSI color for ``stream`` (default stdout)."""
    target: TextIO = stream if stream is not None else sys.stdout
    if os.environ.get("FORCE_COLOR"):
        return True
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return bool(target.isatty())
    except (AttributeError, ValueError):
        return False


class Palette:
    """Tiny colorizer: no-ops cleanly when color is disabled."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def __call__(self, text: str, *styles: str) -> str:
        if not self.enabled or not styles:
            return text
        codes = ";".join(_ANSI_CODES[s] for s in styles if s in _ANSI_CODES)
        if not codes:
            return text
        return f"\033[{codes}m{text}{_ANSI_RESET}"

    def status(self, status: str) -> str:
        return (
            self(status, self_color)
            if (self_color := _STATUS_COLOR.get(status))
            else status
        )


def _strip_ansi(text: str) -> str:
    return _ANSI_STRIP_RE.sub("", text)


def _one_line(text: str, limit: int = 200) -> str:
    """Collapse whitespace/newlines to a single line and clip to ``limit`` chars."""
    collapsed = " ".join(text.split())
    if len(collapsed) > limit:
        return collapsed[: limit - 1] + "\u2026"
    return collapsed


def render_agy_event(raw_line: str, pal: Palette) -> str | None:
    """Translate one raw JSONL event from `agy --output-format stream-json` into a
    concise, colored terminal line.
    """
    line = raw_line.rstrip("\n")
    if not line.strip():
        return None
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return pal("  " + _one_line(line), "dim")

    event_type = event.get("event")
    if event_type == "init":
        init_data = event.get("init") or {}
        model = init_data.get("model", "antigravity")
        conv_id = event.get("conversation_id", "")
        cid_str = f" [session: {conv_id[:8]}...]" if conv_id else ""
        return pal(f"  \u2022 Initialized Antigravity ({model}){cid_str}", "dim")

    if event_type == "result":
        res = event.get("result") or {}
        status = res.get("status", "UNKNOWN")
        if status == "SUCCESS":
            return pal(f"  \u2713 Antigravity turn finished: {status}", "green")
        else:
            err = res.get("error") or status
            return pal(f"  \u2717 Antigravity turn failed: {err}", "red")

    if event_type == "step_update":
        step = event.get("step_update") or {}
        state = str(step.get("state", "")).upper()
        step_type = str(step.get("step_type", ""))

        if step_type == "tool":
            tool_info = step.get("tool_info") or {}
            tool_name = tool_info.get("name") or step.get("tool_name") or "tool"
            params = tool_info.get("parameters") or {}
            cmd = ""
            if "CommandLine" in params:
                cmd = str(params["CommandLine"])
            elif "command" in params:
                cmd = str(params["command"])
            elif "cmd" in params:
                cmd = str(params["cmd"])
            elif "Query" in params:
                cmd = f"grep {params['Query']}"
            elif "AbsolutePath" in params:
                cmd = Path(str(params["AbsolutePath"])).name
            elif "TargetFile" in params:
                cmd = Path(str(params["TargetFile"])).name
            elif "Pattern" in params:
                cmd = str(params["Pattern"])

            summary = f": {_one_line(cmd, 120)}" if cmd else ""
            if state == "ACTIVE":
                glyph = pal("\u2026", "yellow")
                return f"    {glyph} {pal(tool_name, 'bold')}{summary}"
            elif state == "DONE":
                glyph = pal("\u2713", "green")
                dur = step.get("duration_seconds")
                dur_str = f" ({dur:.2f}s)" if dur is not None else ""
                return f"    {glyph} {pal(tool_name, 'bold')}{summary}{pal(dur_str, 'dim')}"
            elif state in ("ERROR", "FAILED"):
                glyph = pal("\u2717", "red")
                return f"    {glyph} {pal(tool_name, 'bold')}{summary}"

        if step_type == "agent_response" and state == "DONE":
            usage = step.get("usage") or {}
            toks = usage.get("total_tokens")
            tok_str = f" ({toks} tok)" if toks else ""
            dur = step.get("duration_seconds")
            dur_str = f" in {dur:.2f}s" if dur is not None else ""
            return pal(f"    \u2014 agent response done{tok_str}{dur_str}", "dim")

        if step_type == "subagent":
            subagent = step.get("subagent_info") or {}
            subagents = subagent.get("subagents", [])
            count = len(subagents) if isinstance(subagents, list) else 1
            noun = "subagent" if count == 1 else "subagents"
            glyph = (
                pal("\u2713", "green") if state == "DONE" else pal("\u2026", "yellow")
            )
            return f"    {glyph} {count} {noun} {state.lower()}"

    return None


class Heartbeat:
    """Prints a periodic 'still working' line to stderr when the child stream is quiet."""

    def __init__(
        self, pal: Palette, label: str, stream: TextIO, interval: float = 15.0
    ) -> None:
        self.pal = pal
        self.label = label
        self.stream = stream
        self.interval = interval
        self._last_activity = time.monotonic()
        self._start = time.monotonic()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._enabled = interval > 0

    def touch(self) -> None:
        self._last_activity = time.monotonic()

    def format_idle(self) -> str:
        idle = int(time.monotonic() - self._last_activity)
        idle_m, idle_s = divmod(idle, 60)
        return f"{idle_m}m{idle_s:02d}s"

    def format_message(self) -> str:
        elapsed = int(time.monotonic() - self._start)
        mins, secs = divmod(elapsed, 60)
        idle_str = self.format_idle()
        return (
            f"    \u2026 still working on {self.label} "
            f"({mins}m{secs:02d}s elapsed, {idle_str} since last event)"
        )

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            idle = time.monotonic() - self._last_activity
            if idle >= self.interval:
                msg = self.pal(self.format_message(), "dim")
                self.stream.write(msg + "\n")
                self.stream.flush()

    def __enter__(self) -> Heartbeat:
        if self._enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


class DriverError(RuntimeError):
    pass


class StallTimeout(DriverError):
    """Raised when a child turn emits no events for longer than the stall timeout."""

    def __init__(self, timeout_seconds: float, label: str) -> None:
        self.timeout_seconds = timeout_seconds
        self.label = label
        super().__init__(
            f"Turn stalled on {label}: no child-agent events received for "
            f"{int(timeout_seconds)}s (terminated)"
        )


class StallWatchdog:
    """Monitors event arrival and forcefully reaps the child process if it wedges."""

    def __init__(
        self,
        process: subprocess.Popen,
        timeout_seconds: float,
        label: str,
        pal: Palette,
        stream: TextIO = sys.stderr,
    ) -> None:
        self.process = process
        self.timeout_seconds = timeout_seconds
        self.label = label
        self.pal = pal
        self.stream = stream
        self._last_event = time.monotonic()
        self._stop = threading.Event()
        self._triggered = False
        self._thread: threading.Thread | None = None
        self._enabled = timeout_seconds > 0

    def touch(self) -> None:
        self._last_event = time.monotonic()

    @property
    def triggered(self) -> bool:
        return self._triggered

    def _run(self) -> None:
        check_step = (
            min(1.0, self.timeout_seconds / 4.0) if self.timeout_seconds > 0 else 1.0
        )
        while not self._stop.wait(check_step):
            if self.process.poll() is not None:
                return
            silence = time.monotonic() - self._last_event
            if silence >= self.timeout_seconds:
                self._triggered = True
                mins = int(self.timeout_seconds // 60)
                secs = int(self.timeout_seconds % 60)
                dur = f"{mins}m{secs:02d}s" if mins else f"{int(self.timeout_seconds)}s"
                msg = self.pal(
                    f"\n[watchdog] STALL DETECTED on {self.label}: no events for {dur}. Terminating wedged turn...",
                    "red",
                    "bold",
                )
                self.stream.write(msg + "\n")
                self.stream.flush()
                terminate_process(self.process)
                return

    def __enter__(self) -> StallWatchdog:
        if self._enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_checked(argv: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise DriverError(
            f"Command failed ({result.returncode}): {shlex.join(argv)}\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def extract_last_history_entry(text: str) -> str:
    """Return the last workflow history bullet from plan text, or full text if no history."""
    history_idx = text.rfind("## Workflow history")
    if history_idx == -1:
        return text
    history_text = text[history_idx:]
    bullets = [
        line.strip()
        for line in history_text.splitlines()
        if line.strip().startswith("- ")
    ]
    return bullets[-1] if bullets else history_text


def is_plan_review_approved(plan_path: Path) -> bool:
    """Check whether a reviewed plan's latest review verdict is 'GO - PENDING HUMAN APPROVAL'."""
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return False
    last_entry = extract_last_history_entry(text)
    if not re.search(r"GO\s*-\s*PENDING\s*HUMAN\s*APPROVAL", last_entry, re.IGNORECASE):
        return False
    if re.search(r"Readiness:\s*(NO-GO|CONDITIONAL-GO)", last_entry, re.IGNORECASE):
        return False
    return True


def set_plan_approved(
    repo: Path, id6: str, message: str = "Full-auto approval via runagy"
) -> None:
    """Transition a reviewed plan to approved via aw set approved --by-human."""
    cmd = [
        sys.executable,
        "-m",
        "agent_workflows",
        "set",
        "approved",
        id6,
        "--by-human",
        "--dir",
        str(repo),
        "-m",
        message,
    ]
    try:
        run_checked(cmd, cwd=repo)
        return
    except (DriverError, FileNotFoundError, OSError):
        pass
    if shutil.which("aw"):
        run_checked(
            [
                "aw",
                "set",
                "approved",
                id6,
                "--by-human",
                "--dir",
                str(repo),
                "-m",
                message,
            ],
            cwd=repo,
        )
    else:
        raise DriverError(
            f"Unable to run 'aw set approved {id6}': aw command not available"
        )


def git_common_dir(repo: Path) -> Path:
    raw = run_checked(["git", "rev-parse", "--git-common-dir"], cwd=repo)
    path = Path(raw)
    return path if path.is_absolute() else (repo / path).resolve()


def git_head(repo: Path) -> str:
    return run_checked(["git", "rev-parse", "HEAD"], cwd=repo)


def git_branch(repo: Path) -> str:
    result = subprocess.run(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout.strip() if result.returncode == 0 else "(detached)"


def git_status(repo: Path) -> str:
    return run_checked(["git", "status", "--short"], cwd=repo)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DriverError(f"Required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DriverError(f"Invalid JSON in {path}: {exc}") from exc


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        if hasattr(os, "O_DIRECTORY"):
            with contextlib.suppress(OSError):
                dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
        handle.flush()


def run_lock_path(run_dir: Path) -> Path:
    return run_dir / ".run.lock"


@contextlib.contextmanager
def run_lock(run_dir: Path) -> Iterable[None]:
    lock_file = run_lock_path(run_dir)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with lock_file.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise DriverError(
                f"Another process holds the lock for {run_dir} ({lock_file})"
            ) from exc
        try:
            handle.seek(0)
            handle.truncate()
            handle.write(f"pid={os.getpid()}\nstarted={utc_now()}\n")
            handle.flush()
            yield
        finally:
            with contextlib.suppress(Exception):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _read_id(text: str) -> str | None:
    m = _ID_RE.search(text)
    return m.group(1) if m else None


def _read_status(text: str) -> str | None:
    m = _STATUS_RE.search(text)
    return m.group(1) if m else None


def _read_set(text: str) -> str | None:
    m = _SET_RE.search(text)
    if not m:
        return None
    raw = m.group(1).split("(")[0].strip()
    if not raw:
        return None
    token = raw.split()[0].strip("\"'").strip()
    return token if token else None


def _read_order(text: str) -> int | None:
    m = _ORDER_RE.search(text)
    return int(m.group(1)) if m else None


def _read_deps(text: str) -> list[str]:
    m = _DEPS_RE.search(text)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw or raw.lower() in ("none", "none.", "n/a"):
        return []
    raw = re.sub(r"\(.*?\)", "", raw)
    tokens = re.split(r"[,;\s]+", raw)
    cleaned = [tok.strip("[]'\"(),;").strip() for tok in tokens]
    return [tok for tok in cleaned if ID6_RE.fullmatch(tok)]


class PlanRecord(NamedTuple):
    id6: str
    setid: str
    status: str
    order: int
    path: Path
    rel_path: str
    dependencies: list[str]


def parse_plan_file(path: Path, repo: Path) -> PlanRecord | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    id6 = _read_id(text)
    if not id6:
        m = _PLAN_FILENAME_RE.match(path.name)
        if m:
            id6 = m.group(3)
    if not id6:
        return None
    setid = _read_set(text)
    if not setid:
        m = _PLAN_FILENAME_RE.match(path.name)
        setid = m.group(1) if m else "misc"
    order = _read_order(text)
    if order is None:
        m = _PLAN_FILENAME_RE.match(path.name)
        order = int(m.group(2)) if m else 99
    status = _read_status(text) or "unknown"
    deps = _read_deps(text)
    try:
        rel = str(path.relative_to(repo))
    except ValueError:
        rel = str(path)
    return PlanRecord(
        id6=id6,
        setid=setid,
        status=status,
        order=order,
        path=path,
        rel_path=rel,
        dependencies=deps,
    )


def discover_plans(repo: Path) -> list[PlanRecord]:
    plans_dir = repo / ".aw" / "records" / "plans"
    if not plans_dir.is_dir():
        return []
    found: list[PlanRecord] = []
    for path in sorted(plans_dir.rglob("*.md")):
        if path.name.startswith("INDEX") or path.name.startswith("README"):
            continue
        rec = parse_plan_file(path, repo)
        if rec is not None:
            found.append(rec)
    return found


def resolve_plan_path(repo: Path, setid: str, id6: str) -> Path:
    plans_dir = repo / ".aw" / "records" / "plans"
    for bucket in ("pending", "reusable", "executed", "superseded", "not-executed"):
        bucket_dir = plans_dir / bucket
        if not bucket_dir.is_dir():
            continue
        for candidate in bucket_dir.glob(f"*-{id6}-*.md"):
            if candidate.is_file():
                return candidate
    for candidate in plans_dir.rglob(f"*-{id6}-*.md"):
        if candidate.is_file():
            return candidate
    for candidate in repo.rglob("*.ipd.md"):
        if candidate.is_file() and f"-{id6}-" in candidate.name:
            return candidate
    raise DriverError(f"Cannot resolve plan file for id6={id6} under {repo}")


def plan_bucket(plan_path: Path) -> str:
    for part in plan_path.parts:
        if part in ("pending", "reusable", "executed", "superseded", "not-executed"):
            return part
    return "unknown"


def determine_action(status: str, bucket: str) -> str:
    if status in ("to-review", "draft"):
        return "review"
    if status in ("approved", "auto-approved") or bucket == "reusable":
        return "execute"
    if status == "reviewed":
        return "execute"
    if status in TERMINAL_STATES:
        return "execute"
    return "execute"


def expand_selectors(
    selectors: list[str],
    manifest: dict[str, Any],
    repo: Path,
    plans: list[PlanRecord],
) -> list[dict[str, Any]]:
    by_id = {p.id6: p for p in plans}
    by_set: dict[str, list[PlanRecord]] = {}
    for p in plans:
        by_set.setdefault(p.setid, []).append(p)

    resolved: list[dict[str, Any]] = []
    seen: set[str] = set()

    if selectors == ["all"]:
        pending_actionable: list[PlanRecord] = []
        for p in plans:
            bucket = plan_bucket(p.path)
            if bucket == "pending" and p.status in (
                "to-review",
                "draft",
                "reviewed",
                "approved",
                "auto-approved",
            ):
                pending_actionable.append(p)
        pending_actionable.sort(key=lambda rec: (rec.setid, rec.order, rec.id6))
        for p in pending_actionable:
            if p.id6 in seen:
                continue
            seen.add(p.id6)
            action = determine_action(p.status, plan_bucket(p.path))
            resolved.append(
                {
                    "id6": p.id6,
                    "setid": p.setid,
                    "path": p.rel_path,
                    "dependencies": p.dependencies,
                    "order": p.order,
                    "initial_status": p.status,
                    "action": action,
                }
            )
        return resolved

    for sel in selectors:
        if ID6_RE.fullmatch(sel):
            p = by_id.get(sel)
            if not p:
                raise DriverError(f"Plan with id6={sel!r} not found in repo {repo}")
            if p.id6 not in seen:
                seen.add(p.id6)
                action = determine_action(p.status, plan_bucket(p.path))
                resolved.append(
                    {
                        "id6": p.id6,
                        "setid": p.setid,
                        "path": p.rel_path,
                        "dependencies": p.dependencies,
                        "order": p.order,
                        "initial_status": p.status,
                        "action": action,
                    }
                )
            continue

        if sel in by_set:
            group = sorted(by_set[sel], key=lambda x: (x.order, x.id6))
            for p in group:
                if p.id6 not in seen:
                    seen.add(p.id6)
                    action = determine_action(p.status, plan_bucket(p.path))
                    resolved.append(
                        {
                            "id6": p.id6,
                            "setid": p.setid,
                            "path": p.rel_path,
                            "dependencies": p.dependencies,
                            "order": p.order,
                            "initial_status": p.status,
                            "action": action,
                        }
                    )
            continue

        path_cand = Path(sel)
        if not path_cand.is_absolute():
            path_cand = repo / path_cand
        if path_cand.is_file():
            p = parse_plan_file(path_cand, repo)
            if not p:
                raise DriverError(f"File {sel!r} is not a valid IPD")
            if p.id6 not in seen:
                seen.add(p.id6)
                action = determine_action(p.status, plan_bucket(p.path))
                resolved.append(
                    {
                        "id6": p.id6,
                        "setid": p.setid,
                        "path": p.rel_path,
                        "dependencies": p.dependencies,
                        "order": p.order,
                        "initial_status": p.status,
                        "action": action,
                    }
                )
            continue

        raise DriverError(f"Selector {sel!r} did not match an id6, set, or file path")

    return resolved


def resolve_agy(explicit_path: str | None) -> str:
    """Return an executable agy path or raise DriverError."""
    if explicit_path:
        cand = Path(explicit_path).expanduser()
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand.resolve())
        raise DriverError(f"The --agy path is not executable: {cand}")
    discovered = shutil.which("agy")
    if discovered:
        return discovered
    raise DriverError(
        "Cannot find 'agy' on PATH. Install Antigravity CLI or pass --agy PATH."
    )


def state_root(repo: Path) -> Path:
    return repo / ".aw" / "records" / "runs"


def new_run_id() -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    salt = hashlib.sha256(f"{os.getpid()}:{time.time_ns()}".encode()).hexdigest()[:6]
    return f"run-{stamp}-{salt}"


def resolve_run_dir(repo: Path, run_id: str) -> Path:
    return state_root(repo) / run_id


def initialize_run(
    repo: Path,
    selectors: list[str],
    options: dict[str, Any],
    manifest_path: Path | None = None,
    runbook_path: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    repo = repo.resolve()
    plans = discover_plans(repo)
    raw_manifest: dict[str, Any] = {}
    if manifest_path and manifest_path.is_file():
        raw_manifest = load_json(manifest_path)

    items = expand_selectors(selectors, raw_manifest, repo, plans)
    if not items:
        raise DriverError(f"No actionable plans resolved from selectors: {selectors}")

    run_id = new_run_id()
    run_dir = resolve_run_dir(repo, run_id)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    initial_session = options.get("session")

    queue: list[dict[str, Any]] = []
    full_auto = options.get("full_auto", True)

    for idx, item in enumerate(items, start=1):
        plan_p = resolve_plan_path(repo, item["setid"], item["id6"])
        rec = parse_plan_file(plan_p, repo)
        status = rec.status if rec else item["initial_status"]
        action = determine_action(status, plan_bucket(plan_p))

        if (
            full_auto
            and action == "execute"
            and status == "reviewed"
            and is_plan_review_approved(plan_p)
        ):
            try:
                set_plan_approved(repo, item["id6"])
                status = "approved"
            except Exception:
                pass

        queue.append(
            {
                "position": idx,
                "id6": item["id6"],
                "setid": item["setid"],
                "path": item["path"],
                "dependencies": item["dependencies"],
                "order": item["order"],
                "action": action,
                "status": "queued",
                "attempts": [],
                "attempts_count": 0,
                "last_error": None,
                "verification_status": None,
            }
        )

    state: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "repo": str(repo),
        "runbook": str(runbook_path.resolve()) if runbook_path else None,
        "manifest": str(manifest_path.resolve()) if manifest_path else None,
        "session_id": initial_session,
        "set_sessions": {item["setid"]: initial_session} if initial_session else {},
        "options": options,
        "queue": queue,
    }

    state_file = run_dir / "state.json"
    atomic_write_json(state_file, state)
    write_initial_registers(run_dir, state)
    return state, run_dir


def write_initial_registers(run_dir: Path, state: dict[str, Any]) -> None:
    decisions = run_dir / "decisions-and-questions.md"
    if not decisions.exists():
        decisions.write_text(
            f"# Decisions and Questions Register\n\nRun ID: `{state['run_id']}`\n\n",
            encoding="utf-8",
        )
    report = run_dir / "execution-report.md"
    if not report.exists():
        report.write_text(
            f"# Antigravity IPD Driver Report: `{state['run_id']}`\n\n",
            encoding="utf-8",
        )


def load_state(run_dir: Path) -> dict[str, Any]:
    return load_json(run_dir / "state.json")


def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    atomic_write_json(run_dir / "state.json", state)


def extract_session_id(log_path: Path) -> str | None:
    if not log_path.is_file():
        return None
    try:
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                if event.get("conversation_id"):
                    return str(event["conversation_id"])
                res = event.get("result")
                if isinstance(res, dict) and res.get("conversation_id"):
                    return str(res["conversation_id"])
                init = event.get("init")
                if isinstance(init, dict) and init.get("conversation_id"):
                    return str(init["conversation_id"])
    except OSError:
        pass
    return None


def dependency_status(
    item: dict[str, Any], state: dict[str, Any]
) -> tuple[bool, list[str]]:
    by_id = {entry["id6"]: entry for entry in state["queue"]}
    repo = Path(state["repo"])
    unsatisfied: list[str] = []
    is_exec = item.get("action") != "review"
    required_states = EXECUTION_SUCCESS_STATES if is_exec else SUCCESS_STATES

    for dep in item.get("dependencies", []):
        if dep in by_id:
            if by_id[dep]["status"] not in required_states:
                unsatisfied.append(dep)
            continue
        try:
            dep_path = resolve_plan_path(repo, "", dep)
        except DriverError:
            unsatisfied.append(dep)
            continue
        bucket = plan_bucket(dep_path)
        if is_exec:
            if bucket != "executed":
                unsatisfied.append(dep)
        else:
            if bucket not in ("executed", "reviewed", "approved"):
                unsatisfied.append(dep)
    return not unsatisfied, unsatisfied


def build_review_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    repo: Path,
) -> str:
    try:
        rel_path = str(plan_path.relative_to(repo))
    except ValueError:
        rel_path = str(plan_path)
    return f"/plan-review {rel_path}"


def build_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    recovery: bool,
) -> str:
    setid = item["setid"]
    decisions = run_dir / "decisions-and-questions.md"
    outcome = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    report = run_dir / "execution-report.md"
    mode = "RECOVERY/CONTINUATION" if recovery else "NORMAL EXECUTION"
    prior = item.get("attempts", [])[-1] if recovery and item.get("attempts") else None
    return f"""# Antigravity IPD Driver Turn

Mode: {mode}
Run ID: {state["run_id"]}
Queue position: {item["position"]}
Assigned IPD: {item["id6"]}
Assigned Set: {setid}
Plan file at launch: {plan_path}
External run directory: {run_dir}
Decisions/questions register: {decisions}
Required JSON outcome: {outcome}
Driver report: {report}
Prior attempt: {json.dumps(prior, sort_keys=True) if prior else "none"}

Execute only IPD {item["id6"]}. Read every applicable repository instruction,
the assigned IPD in full, its current orchestrator, current repository state,
and completed prerequisite artifacts before editing. Do not implement another IPD in this turn.

All target IPDs are approved. Do not ask for approval. This run is non-interactive:
do not invoke an interactive question tool or wait for human input. When a material question
arises, investigate the approved plans, repository decisions, source, tests, history,
and current primary documentation. Choose a reasonable recommended approach, record it in
the decisions/questions register with evidence, rationale, confidence, scope, and validation,
then continue.

Maximize safe forward progress. Do not weaken checks, fabricate evidence, broaden approved
scope, bypass lifecycle controls, discard unrelated work, or push. Do not use git add -A,
git add ., git commit -a, --no-verify, destructive reset/clean, or stashing that could hide
ownership. Use path-scoped commits (`git commit -m msg -- <paths>`).

Before exiting, write valid JSON to {outcome} with at least:
{{
  "schema_version": 1,
  "run_id": "{state["run_id"]}",
  "position": {item["position"]},
  "id6": "{item["id6"]}",
  "setid": "{setid}",
  "disposition": "executed|substantially-complete|partial|blocked|failed-safely",
  "summary": "...",
  "starting_head": "...",
  "ending_head": "...",
  "commits": [],
  "files_changed": [],
  "tests": [],
  "decision_ids": [],
  "deferred_question_ids": [],
  "incomplete_requirements": [],
  "partial_work_location": null,
  "recommended_next_action": "...",
  "pushed": false
}}

The disposition must describe the actual repository result, not merely your effort.
Explicitly confirm pushed=false.
"""


def build_verifier_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
) -> str:
    outcome = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    verify_outcome = (
        run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}-verification.json"
    )
    return f"""# Independent Rigorous Verification of Executed IPD

Plan: `{plan_path}`
Id: `{item['id6']}`
Set: `{item['setid']}`
Run ID: `{state['run_id']}`
Execution Outcome JSON: `{outcome}`
Verification Outcome JSON to write: `{verify_outcome}`

You are an independent, skeptical verifier running in a fresh Antigravity session to audit
the execution of this IPD. Your goal is to rigorously verify whether the code, tests,
and documentation satisfy every requirement before this plan can be considered executed.

## Verification Requirements:

1. **Inspect Concrete Diffs & Commits**:
   - Inspect the git commits and working tree diffs produced for this IPD.
   - Verify that real functional changes were made, not just cosmetic/vocabulary additions.
   - Ensure all referenced files and symbols in the plan's Scope-Paths actually exist and are wired correctly.

2. **Evidence Table (E-* and V-*)**:
   - Check every Execution item (`E-*`) and every Validation item (`V-*`) in the IPD.
   - Check if the recorded observed evidence matches real code and passing tests.

3. **Run and Verify Test Suite**:
   - Run the required tests and validation commands for this IPD using `run_command` (e.g. `pytest <test_file> -v` or `python3 -m unittest ...`).
   - Paste the actual runner output with exit code.
   - Confirm that tests are genuine and testing real assertions (not trivial passes).

4. **In-Scope Fixes**:
   - If you discover safely correctable defects, regressions, or missing test cases within the approved scope, fix them, re-run validation, and commit path-scoped (`git commit -m msg -- <paths>`).
   - If any unresolvable defect or scope gap remains, report it clearly.

5. **Write Verification Outcome**:
   Before exiting, write valid JSON to `{verify_outcome}`:
   {{
     "schema_version": 1,
     "id6": "{item['id6']}",
     "verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED",
     "summary": "...",
     "evidence": [],
     "tests_run": [],
     "corrections_made": []
   }}

Begin independent verification now.
"""


def write_prompt(
    run_dir: Path, item: dict[str, Any], prompt: str, attempt_no: int, suffix: str = ""
) -> Path:
    prefix = "review" if item.get("action") == "review" else "exec"
    tag = f"-{suffix}" if suffix else ""
    path = (
        run_dir
        / "prompts"
        / f"{item['position']:02d}-{item['id6']}-{prefix}{tag}-attempt-{attempt_no}.md"
    )
    path.write_text(prompt, encoding="utf-8")
    return path


def attempt_log_path(
    run_dir: Path, item: dict[str, Any], attempt_no: int, suffix: str = ""
) -> Path:
    tag = f"-{suffix}" if suffix else ""
    return (
        run_dir
        / "sessions"
        / f"{item['position']:02d}-{item['id6']}{tag}-attempt-{attempt_no}.jsonl"
    )


def terminate_process(process: subprocess.Popen) -> None:
    """Reap a child process and its process group without leaving orphans."""
    if process.poll() is not None:
        _close_process_streams(process)
        return

    def _signal(sig: int) -> bool:
        if hasattr(os, "killpg") and hasattr(os, "getpgid") and hasattr(os, "getpgrp"):
            try:
                pgid = os.getpgid(process.pid)
                if pgid != os.getpgrp():
                    os.killpg(pgid, sig)
                    return True
            except (ProcessLookupError, OSError):
                pass
        try:
            process.send_signal(sig)
            return True
        except (ProcessLookupError, OSError):
            return False

    for sig, grace in (
        (signal.SIGINT, _SIGINT_GRACE_SECONDS),
        (signal.SIGTERM, _SIGTERM_GRACE_SECONDS),
    ):
        if not _signal(sig):
            break
        try:
            process.wait(timeout=grace)
            _close_process_streams(process)
            return
        except subprocess.TimeoutExpired:
            continue

    _signal(signal.SIGKILL)
    with contextlib.suppress(Exception):
        process.wait(timeout=_SIGTERM_GRACE_SECONDS)
    _close_process_streams(process)


def _close_process_streams(process: subprocess.Popen) -> None:
    for stream in (process.stdout, process.stderr, process.stdin):
        if stream is not None:
            with contextlib.suppress(Exception):
                stream.close()


def run_agy_turn(
    state: dict[str, Any],
    run_dir: Path,
    item: dict[str, Any],
    prompt_path: Path,
    attempt_no: int,
    session_id: str | None,
    use_continue: bool,
    log_suffix: str = "",
    label_suffix: str = "",
) -> tuple[int, str | None, Path, str | None]:
    options = state.get("options", {})
    agy_bin = options.get("agy_executable") or options.get("agy") or resolve_agy(None)
    prompt_text = prompt_path.read_text(encoding="utf-8")
    timeout = options.get("timeout", DEFAULT_TIMEOUT)

    argv = [
        agy_bin,
        "-p",
        prompt_text,
        "--output-format",
        "stream-json",
        "--print-timeout",
        str(timeout),
    ]

    if options.get("dangerously_skip_permissions", True):
        argv.append("--dangerously-skip-permissions")

    if options.get("model"):
        argv.extend(["--model", options["model"]])
    if options.get("effort"):
        argv.extend(["--effort", options["effort"]])

    if session_id:
        argv.extend(["--conversation", session_id])
    elif use_continue:
        argv.append("--continue")

    output_mode = options.get("output_mode", "clean")
    pal = Palette(should_color(sys.stdout))
    action_label = item.get("action", "turn")
    tag = f" {label_suffix}" if label_suffix else ""
    label = (
        pal(f"{item['id6']}", "bold") + f" ({action_label}{tag} attempt {attempt_no})"
    )
    log_path = attempt_log_path(run_dir, item, attempt_no, suffix=log_suffix)

    popen_kwargs: dict[str, Any] = {
        "cwd": state["repo"],
        "text": True,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "bufsize": 1,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True

    stall_timeout = options.get("stall_timeout", DEFAULT_STALL_TIMEOUT)
    last_response: str | None = None
    captured_conv_id: str | None = session_id

    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(argv, **popen_kwargs)
        if process.stdout is None:
            terminate_process(process)
            raise DriverError("Failed to open child agy stdout stream")

        with Heartbeat(pal, label, sys.stderr) as hb, StallWatchdog(
            process, stall_timeout, label, pal
        ) as watchdog:
            for raw_line in process.stdout:
                log.write(raw_line)
                log.flush()
                hb.touch()
                watchdog.touch()

                try:
                    event = json.loads(raw_line.strip())
                    if isinstance(event, dict):
                        if event.get("conversation_id"):
                            captured_conv_id = str(event["conversation_id"])
                        res = event.get("result")
                        if isinstance(res, dict):
                            if res.get("conversation_id"):
                                captured_conv_id = str(res["conversation_id"])
                            if res.get("response"):
                                last_response = str(res["response"])
                except Exception:
                    pass

                if output_mode == "raw":
                    sys.stdout.write(raw_line)
                    sys.stdout.flush()
                elif output_mode == "clean":
                    rendered = render_agy_event(raw_line, pal)
                    if rendered:
                        sys.stdout.write(rendered + "\n")
                        sys.stdout.flush()

        rc = process.wait()
        if watchdog.triggered:
            raise StallTimeout(stall_timeout, label)

    return rc, captured_conv_id, log_path, last_response


def execute_item(
    state: dict[str, Any], run_dir: Path, item: dict[str, Any]
) -> dict[str, Any]:
    repo = Path(state["repo"])
    pal = Palette(should_color(sys.stdout))
    attempt_no = item.get("attempts_count", 0) + 1
    action = item.get("action", "execute")
    is_review = action == "review"

    plan_path = resolve_plan_path(repo, item["setid"], item["id6"])
    plan_record = parse_plan_file(plan_path, repo)
    if not plan_record:
        raise DriverError(f"Plan file {plan_path} vanished or is unparseable")

    if is_review:
        prompt_text = build_review_prompt(item, state, run_dir, plan_path, repo)
    else:
        prompt_text = build_prompt(
            item, state, run_dir, plan_path, recovery=(attempt_no > 1)
        )

    prompt_file = write_prompt(run_dir, item, prompt_text, attempt_no)
    session_id = (
        state.get("session_id")
        or state.get("set_sessions", {}).get(item["setid"])
        or state.get("options", {}).get("session")
    )
    use_continue = (
        False if state.get("options", {}).get("new_session") else (session_id is None)
    )

    start_time = utc_now()
    head_before = git_head(repo)

    rc, captured_session, log_file, _resp = run_agy_turn(
        state,
        run_dir,
        item,
        prompt_file,
        attempt_no,
        session_id=session_id,
        use_continue=use_continue,
        log_suffix="",
        label_suffix="",
    )

    if captured_session:
        state["set_sessions"][item["setid"]] = captured_session
        state["session_id"] = captured_session

    head_after = git_head(repo)
    end_time = utc_now()

    # Reconcile primary turn disposition
    rec = parse_plan_file(plan_path, repo)
    status_now = rec.status if rec else "unknown"
    bucket_now = plan_bucket(plan_path)
    outcome_file = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"

    if is_review:
        if status_now == "reviewed":
            disp = "reviewed"
        elif rc == 0:
            disp = "reviewed"
        else:
            disp = "failed-safely"
    else:
        if bucket_now == "executed" or status_now in (
            "executed",
            "substantially-complete",
        ):
            disp = "executed"
        elif outcome_file.is_file():
            try:
                data = json.loads(outcome_file.read_text(encoding="utf-8"))
                disp = data.get("disposition") or ("executed" if rc == 0 else "partial")
            except Exception:
                disp = "executed" if rc == 0 else "partial"
        elif rc == 0:
            disp = "executed"
        else:
            disp = "failed-safely"

    # Turn 2: Rigorous Skeptical Self-Validation Turn (in a clean session)
    verify_disp = None
    no_verify = state.get("options", {}).get("no_verify") or state.get(
        "options", {}
    ).get("no_audit")
    if (
        not is_review
        and disp in ("executed", "substantially-complete")
        and not no_verify
    ):
        v_prompt_text = build_verifier_prompt(item, state, run_dir, plan_path)
        v_prompt_file = write_prompt(
            run_dir, item, v_prompt_text, attempt_no, suffix="verify"
        )
        print(
            pal(
                f"\n  \u2022 Running independent verification for {item['id6']} in clean session...",
                "cyan",
            ),
            file=sys.stderr,
            flush=True,
        )

        v_rc, _v_session, _v_log, _v_resp = run_agy_turn(
            state,
            run_dir,
            item,
            v_prompt_file,
            attempt_no,
            session_id=None,
            use_continue=False,
            log_suffix="verify",
            label_suffix="verification",
        )

        v_outcome_file = (
            run_dir
            / "outcomes"
            / f"{item['position']:02d}-{item['id6']}-verification.json"
        )
        if v_outcome_file.is_file():
            try:
                v_data = json.loads(v_outcome_file.read_text(encoding="utf-8"))
                verify_verdict = v_data.get("verdict", "").upper()
                if "BLOCKED" in verify_verdict or "NOT CONFORMING" in verify_verdict:
                    verify_disp = "blocked"
                    disp = "partial"
                else:
                    verify_disp = "verified"
            except Exception:
                verify_disp = "verified" if v_rc == 0 else "unverified"
        else:
            verify_disp = "verified" if v_rc == 0 else "unverified"

    attempt_record = {
        "attempt": attempt_no,
        "action": action,
        "started_at": start_time,
        "completed_at": end_time,
        "exit_code": rc,
        "head_before": head_before,
        "head_after": head_after,
        "session_id": captured_session,
        "log_path": str(log_file.relative_to(run_dir)),
        "disposition": disp,
        "verification": verify_disp,
    }

    item["attempts"].append(attempt_record)
    item["attempts_count"] = attempt_no
    item["status"] = disp
    item["verification_status"] = verify_disp

    # Full-auto review-to-execution progression
    full_auto = state.get("options", {}).get("full_auto", True)
    if (
        is_review
        and disp == "reviewed"
        and full_auto
        and is_plan_review_approved(plan_path)
    ):
        try:
            set_plan_approved(repo, item["id6"])
            item["status"] = "approved"
            item["action"] = "execute"
        except Exception:
            pass

    save_state(run_dir, state)
    return item


def render_continuation_hint(state: dict[str, Any], run_dir: Path) -> str:
    pal = Palette(should_color(sys.stdout))
    repo = state.get("repo", ".")
    run_id = state.get("run_id", "run-...")
    sessions = state.get("set_sessions", {})
    captured: list[tuple[str, str]] = [
        (s, sid) for s, sid in sessions.items() if sid and isinstance(sid, str)
    ]

    lines = ["", pal("--- OpenCode / Antigravity Session Continuity ---", "bold")]
    if not captured:
        lines.append("No Antigravity session was captured for this run.")
    elif len(captured) == 1:
        setid, sid = captured[0]
        lines.append(f"Captured session: {pal(sid, 'cyan')} (Set: {setid})")
        lines.append("To run a new plan under the same session:")
        lines.append(f"  runagy --session {sid} <selector>")
    else:
        lines.append("Captured sessions by Set:")
        for setid, sid in captured:
            lines.append(f"  - {pal(setid, 'bold')}: {pal(sid, 'cyan')}")
        last_sid = captured[-1][1]
        lines.append("To run a new plan under the most recent session:")
        lines.append(f"  runagy --session {last_sid} <selector>")

    lines.append("To resume this run:")
    lines.append(f"  runagy resume --repo {repo} {run_id}")
    lines.append("")
    return "\n".join(lines)


def write_report(run_dir: Path, state: dict[str, Any]) -> None:
    report_file = run_dir / "execution-report.md"
    lines = [
        "# Antigravity IPD Driver Execution Report",
        "",
        f"- Run ID: `{state['run_id']}`",
        f"- Started: `{state['created_at']}`",
        f"- Updated: `{state['updated_at']}`",
        f"- Repository: `{state['repo']}`",
        "",
        "## Queue Summary",
        "",
        "| Position | Id | Set | Action | Status | Verification | Attempts |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for item in state["queue"]:
        v_stat = item.get("verification_status") or "N/A"
        lines.append(
            f"| {item['position']} | `{item['id6']}` | `{item['setid']}` | "
            f"`{item.get('action', 'execute')}` | `{item['status']}` | `{v_stat}` | "
            f"{item.get('attempts_count', 0)} |"
        )
    lines.append("")
    report_file.write_text("\n".join(lines), encoding="utf-8")


def run_queue(run_dir: Path) -> int:
    pal = Palette(should_color(sys.stdout))
    with run_lock(run_dir):
        state = load_state(run_dir)
        queue = state["queue"]

        while True:
            state = load_state(run_dir)
            queue = state["queue"]
            actionable_idx: int | None = None

            for idx, item in enumerate(queue):
                if item["status"] in ("queued", "approved", "interrupted"):
                    sat, _missing = dependency_status(item, state)
                    if sat:
                        actionable_idx = idx
                        break
                    else:
                        item["status"] = "dependency-blocked"
                        save_state(run_dir, state)

            if actionable_idx is None:
                # Check if any dependency-blocked items are unblocked
                unblocked = False
                for item in queue:
                    if item["status"] == "dependency-blocked":
                        sat, _ = dependency_status(item, state)
                        if sat:
                            item["status"] = "queued"
                            unblocked = True
                if unblocked:
                    save_state(run_dir, state)
                    continue
                break

            target = queue[actionable_idx]
            target["status"] = "running"
            save_state(run_dir, state)

            print(
                pal(
                    f"\n>>> Starting [{target['action']}] on {target['id6']} (Set: {target['setid']})",
                    "bold",
                    "cyan",
                ),
                flush=True,
            )
            execute_item(state, run_dir, target)
            print(
                pal(
                    f"<<< Finished {target['id6']}: status={target['status']}\n",
                    "bold",
                    "green" if target["status"] in SUCCESS_STATES else "yellow",
                ),
                flush=True,
            )

        write_report(run_dir, state)
        hint = render_continuation_hint(state, run_dir)
        print(hint)

        failures = [it for it in queue if it["status"] not in SUCCESS_STATES]
        return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="runagy.py",
        description="Restartable non-interactive Antigravity (agy) IPD review & execution driver.",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # start
    p_start = sub.add_parser("start", help="Start a new driver queue run")
    p_start.add_argument(
        "selectors",
        nargs="+",
        help="Target plan selectors: ID6, Set ID, IPD filename, or 'all'",
    )
    p_start.add_argument(
        "--repo", default=".", help="Repository root directory (default: .)"
    )
    p_start.add_argument("--manifest", help="Optional pre-baked manifest JSON path")
    p_start.add_argument("--runbook", help="Optional driver runbook markdown path")
    p_start.add_argument(
        "--agy",
        "--agy-executable",
        dest="agy_executable",
        help="Path to agy executable",
    )
    p_start.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Antigravity model (default: {DEFAULT_MODEL})",
    )
    p_start.add_argument("--effort", help="Reasoning effort (low|medium|high)")
    p_start.add_argument(
        "--timeout",
        default=DEFAULT_TIMEOUT,
        help=f"Timeout per turn (default: {DEFAULT_TIMEOUT})",
    )
    p_start.add_argument(
        "--session", help="Resume or bind a specific Antigravity conversation ID"
    )
    p_start.add_argument(
        "--new-session", action="store_true", help="Force fresh session for each Set"
    )
    p_start.add_argument(
        "--dangerously-skip-permissions",
        "--dangerous",
        dest="dangerously_skip_permissions",
        action="store_true",
        default=True,
        help="Auto-approve all tool permission requests in agy (default: True)",
    )
    p_start.add_argument(
        "--no-dangerously-skip-permissions",
        dest="dangerously_skip_permissions",
        action="store_false",
        help="Require interactive tool permissions in agy",
    )
    p_start.add_argument(
        "--no-verify",
        "--no-audit",
        dest="no_verify",
        action="store_true",
        help="Skip turn-2 clean-session skeptical validation",
    )
    p_start.add_argument(
        "--mode", dest="output_mode", choices=OUTPUT_MODES, default="clean"
    )
    p_start.add_argument("--stall-timeout", type=float, default=DEFAULT_STALL_TIMEOUT)
    p_start.add_argument(
        "--full-auto",
        dest="full_auto",
        action="store_true",
        default=True,
        help="Auto-approve reviewed plans with GO verdict and immediately execute",
    )
    p_start.add_argument(
        "--no-full-auto",
        dest="full_auto",
        action="store_false",
        help="Do not auto-approve reviewed plans",
    )

    # resume
    p_resume = sub.add_parser("resume", help="Resume an existing run")
    p_resume.add_argument("run_id", help="Run ID to resume")
    p_resume.add_argument("--repo", default=".", help="Repository root directory")
    p_resume.add_argument("--agy", dest="agy_executable")
    p_resume.add_argument(
        "--mode", dest="output_mode", choices=OUTPUT_MODES, default="clean"
    )
    p_resume.add_argument("--stall-timeout", type=float, default=DEFAULT_STALL_TIMEOUT)
    p_resume.add_argument(
        "--full-auto", dest="full_auto", action="store_true", default=True
    )

    # status
    p_status = sub.add_parser("status", help="Show status of a run")
    p_status.add_argument("run_id", help="Run ID")
    p_status.add_argument("--repo", default=".")
    p_status.add_argument("--json", action="store_true")

    # report
    p_report = sub.add_parser("report", help="Show execution report for a run")
    p_report.add_argument("run_id", help="Run ID")
    p_report.add_argument("--repo", default=".")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()

    if args.subcommand == "start":
        options = {
            "agy_executable": args.agy_executable,
            "model": args.model,
            "effort": args.effort,
            "timeout": args.timeout,
            "session": args.session,
            "new_session": args.new_session,
            "dangerously_skip_permissions": args.dangerously_skip_permissions,
            "no_verify": args.no_verify,
            "output_mode": args.output_mode,
            "stall_timeout": args.stall_timeout,
            "full_auto": args.full_auto,
        }
        manifest_p = Path(args.manifest) if args.manifest else None
        runbook_p = Path(args.runbook) if args.runbook else None

        state, run_dir = initialize_run(
            repo,
            args.selectors,
            options,
            manifest_path=manifest_p,
            runbook_path=runbook_p,
        )
        pal = Palette(should_color(sys.stdout))
        print(
            pal(
                f"Initialized run: {state['run_id']} ({len(state['queue'])} items queued)",
                "bold",
            )
        )
        print(f"Run directory: {run_dir}")
        return run_queue(run_dir)

    if args.subcommand == "resume":
        run_dir = resolve_run_dir(repo, args.run_id)
        if not run_dir.is_dir():
            print(f"error: run directory {run_dir} not found", file=sys.stderr)
            return 2
        return run_queue(run_dir)

    if args.subcommand == "status":
        run_dir = resolve_run_dir(repo, args.run_id)
        if not run_dir.is_dir():
            print(f"error: run directory {run_dir} not found", file=sys.stderr)
            return 2
        state = load_state(run_dir)
        if args.json:
            print(json.dumps(state, indent=2, sort_keys=True))
            return 0
        pal = Palette(should_color(sys.stdout))
        print(pal(f"Run ID: {state['run_id']}", "bold"))
        print(f"Created: {state['created_at']} | Updated: {state['updated_at']}")
        print(f"Queue ({len(state['queue'])} items):")
        for it in state["queue"]:
            st = pal.status(it["status"])
            v = (
                f" [verify: {it.get('verification_status')}]"
                if it.get("verification_status")
                else ""
            )
            print(f"  {it['position']:02d}. {it['id6']} ({it['setid']}): {st}{v}")
        return 0

    if args.subcommand == "report":
        run_dir = resolve_run_dir(repo, args.run_id)
        rep = run_dir / "execution-report.md"
        if not rep.is_file():
            print(f"error: report {rep} not found", file=sys.stderr)
            return 2
        print(rep.read_text(encoding="utf-8"))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
