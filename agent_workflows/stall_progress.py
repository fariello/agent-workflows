#!/usr/bin/env python3
"""Best-effort subagent-progress observer for the OpenCode driver's stall watchdog.

WHY THIS EXISTS
---------------
The driver's :class:`~agent_workflows.oc_runipd.StallWatchdog` is advanced ONLY by lines
arriving on the child's stdout. But ``opencode run --format json`` stdout carries ONLY
PARENT-session events (``step_start``/``step_finish``/``text``/``tool_use``). When the
parent turn delegates to a subagent (a ``task`` tool call), the subagent's work produces
NO parent-session stdout event, so the parent's stdout goes silent for the entire subagent
lifetime while real work is happening. At the default 600s timeout the driver then KILLS a
turn that was progressing.

Measured on a real driver turn (run ``02-plqjt7-attempt-1``, opencode 1.18.25): 570 stdout
events with a largest stdout silence of 246.5s, while opencode's own log showed the
subagent session advancing throughout. Scale that gap past the timeout and a healthy turn
dies.

This module supplies the missing signal by tailing opencode's OWN log and reporting
"progress happened" for activity attributable to the current turn.

ATTRIBUTION: THE TWO-HOP PARENT-SESSION ROUTE
---------------------------------------------
opencode's log lines look like::

    timestamp=<ISO> level=INFO run=<8hex> message=<kind> [session.id=ses_...] ...

A subagent spawn is announced ONCE::

    ... message=created id=ses_<child> ... parentID=ses_<parent> title="... (@explore subagent)"

and thereafter the child's ongoing lines carry ONLY ``session.id=ses_<child>``:

    ... message=loop    session.id=ses_<child> step=0
    ... message=process session.id=ses_<child> messageID=msg_...
    ... message=stream  ... session.id=ses_<child> ... mode=subagent

Crucially, ``parentID`` is NOT usable as the ongoing key: it appears ONLY on the one-shot
``message=created`` line. Verified on the installed version (opencode 1.18.25): of a known
child session's 108 log lines, exactly ONE carried ``parentID`` and that line was the
``created`` line; ZERO ongoing lines carried it.

So attribution is TWO HOPS:

1. The driver knows its own PARENT session id (every stdout event carries ``sessionID``,
   and the very FIRST stdout event already has it: measured 07:27:36.588Z, a full 80s
   BEFORE the child's ``created`` line at 07:28:56.790Z, so the key is available in time).
2. Match ``message=created ... parentID=<our parent>`` to learn each CHILD session id, then
   count that child's subsequent ``session.id=<child>`` lines as our progress.

The alternative ``run=<id>`` per-CLI-process token DOES co-identify a parent and its
subagents (verified: both carry ``run=74347d25``), but the driver has no way to learn its
child's ``run=`` id, so it is not used as the primary key.

PROGRESS vs NOISE (LOAD-BEARING - DO NOT "SIMPLIFY" THIS)
---------------------------------------------------------
Only ``message=loop`` / ``message=process`` / ``message=stream`` count as progress.
Housekeeping is EXCLUDED ON PURPOSE: ``evaluated``, ``asking``, ``llm runtime selected``,
``tracking``, ``resolved path``, ``touching file``, and everything else.

This is not tidiness, it is the true-hang guarantee. A permission-deadlocked opencode
process (see backlog ``qyaime``: a worktree-isolated ``--auto`` turn blocking forever on an
unanswerable ``external_directory`` prompt) KEEPS EMITTING those housekeeping lines while
making no progress. Measured in a 3MB log slice: ``evaluated`` 4174, ``tracking`` 2567,
``llm runtime selected`` 1290, ``resolved path`` 1087, ``asking`` 97. Counting any line for
our process as "progress" would make a deadlocked run IMMORTAL, which is strictly worse
than today's bug: a killed turn is recoverable, an immortal one is not.

BEST-EFFORT CONTRACT (NEVER A HARD DEPENDENCY)
----------------------------------------------
Reading another tool's internal log is coupling to an artifact that carries no
compatibility promise; the format/location may change between opencode versions (observed
format pinned at version 1.18.25). Therefore this observer is OPTIONAL and FAIL-SAFE:

- a missing, unreadable, rotated, truncated, or unparseable log yields NOTHING;
- it never raises into the turn and never blocks the turn;
- if it yields nothing, the watchdog behaves EXACTLY as it does today (stdout-only).

A missing log must never turn into a hung or crashed run.
"""

from __future__ import annotations

import os
import re
import threading
import time
from pathlib import Path

# The observed/pinned opencode log format this parser was confirmed against. Recorded so a
# future reader knows what was measured rather than assumed (see module docstring).
OBSERVED_OPENCODE_VERSION = "1.18.25"

# A session token. Real ids are `ses_` + alphanumerics, but the committed test fixtures MUST
# use the redacted form `ses_<redacted>...` because a real-looking token is a leak-sanitizer
# finding (rule `session-id`, leak_sanitizer.py:81, which allows exactly `ses_<redacted>`).
# The angle brackets/dashes are therefore accepted here so the SAME parser handles both the
# live log and the fixtures; there is no second, fixture-only code path to diverge.
_SES_TOKEN = r"ses_[0-9A-Za-z<>_-]+"

# A subagent spawn announcement: `message=created id=ses_<child> ... parentID=ses_<parent>`.
# This is the ONLY line that ties a child to its parent, hence the two-hop route.
_CREATED_RE = re.compile(
    r"\bmessage=created\b.*?\bid=(?P<child>" + _SES_TOKEN + r").*?"
    r"\bparentID=(?P<parent>" + _SES_TOKEN + r")"
)

# An ongoing line's owning session. Children carry only this (never `parentID`).
_SESSION_RE = re.compile(r"\bsession\.id=(?P<sid>" + _SES_TOKEN + r")")

# The AGENT-LOOP progress kinds. Deliberately a CLOSED allowlist, not a denylist of
# housekeeping: a new opencode housekeeping kind must NOT silently start counting as
# progress, because that would defeat true-hang detection (see module docstring).
PROGRESS_MESSAGE_KINDS = frozenset({"loop", "process", "stream"})

_MESSAGE_RE = re.compile(r"\bmessage=(?P<kind>[A-Za-z_]+)")

# Bound on a single read pass so one call cannot consume unbounded memory/time if the log is
# being appended to very fast by many concurrent opencode processes on the same machine.
_MAX_BYTES_PER_POLL = 4 * 1024 * 1024


def default_log_path() -> Path:
    """Resolve opencode's log path from the environment.

    Honors ``XDG_DATA_HOME`` and falls back to ``~/.local/share``. Never hardcodes a home
    directory (that would both break on other machines and be a leak-sanitizer finding).
    """
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "opencode" / "log" / "opencode.log"


def classify_progress(line: str) -> str | None:
    """Return the ``message=`` kind if ``line`` is an agent-loop PROGRESS line, else None.

    Only :data:`PROGRESS_MESSAGE_KINDS` count. Housekeeping lines return ``None`` so a
    permission-deadlocked (but still chatty) process is NOT mistaken for a progressing one.
    """
    match = _MESSAGE_RE.search(line)
    if match is None:
        return None
    kind = match.group("kind")
    return kind if kind in PROGRESS_MESSAGE_KINDS else None


class SubagentProgressObserver:
    """Tail opencode's log and report progress attributable to one parent session.

    Usage is deliberately trivial and side-effect free from the caller's perspective::

        obs = SubagentProgressObserver(parent_session_id=None)
        obs.set_parent_session("ses_...")   # learned from the first stdout event
        if obs.poll():                      # any attributable progress since last poll?
            watchdog.touch()

    Every public method is FAIL-SAFE: it swallows its own errors and returns a falsy value
    rather than raising into the turn.
    """

    def __init__(
        self,
        parent_session_id: str | None = None,
        log_path: Path | None = None,
        start_at_end: bool = True,
    ) -> None:
        self._lock = threading.Lock()
        self._parent = parent_session_id
        self._children: set[str] = set()
        self._log_path = log_path if log_path is not None else default_log_path()
        # Offset-bounded tailing: open at the CURRENT end of file and only ever read
        # forward. The live log is ~148MB and shared by every opencode process on the
        # machine; re-reading history would be both slow and wrong (it would resurrect
        # progress from a previous turn).
        self._offset = self._initial_offset() if start_at_end else 0
        self._last_progress: float | None = None
        self._progress_count = 0
        self._pending = b""

    @property
    def log_path(self) -> Path:
        return self._log_path

    @property
    def parent_session_id(self) -> str | None:
        """The parent session id this observer attributes progress to (None until known)."""
        with self._lock:
            return self._parent

    @property
    def progress_count(self) -> int:
        """Number of attributable agent-loop progress lines observed so far."""
        with self._lock:
            return self._progress_count

    @property
    def last_progress_monotonic(self) -> float | None:
        """``time.monotonic()`` of the last observed progress, or None if never."""
        with self._lock:
            return self._last_progress

    def _initial_offset(self) -> int:
        try:
            return self._log_path.stat().st_size
        except OSError:
            # Missing/unreadable log: start at 0 so that if it later appears we read it
            # from its beginning rather than skipping content.
            return 0

    def set_parent_session(self, session_id: str | None) -> None:
        """Record the parent session id learned from the child's stdout stream."""
        if not session_id or not isinstance(session_id, str):
            return
        if not session_id.startswith("ses_"):
            return
        with self._lock:
            self._parent = session_id

    def known_children(self) -> frozenset[str]:
        with self._lock:
            return frozenset(self._children)

    def _read_new_bytes(self) -> bytes:
        """Read forward from the stored offset. Returns b"" on ANY problem."""
        try:
            size = self._log_path.stat().st_size
        except OSError:
            return b""
        if size < self._offset:
            # Truncation/rotation: the file we were following was replaced or shrunk.
            # Re-anchor to the new end rather than re-reading a fresh file's history.
            self._offset = size
            self._pending = b""
            return b""
        if size == self._offset:
            return b""
        try:
            with self._log_path.open("rb") as handle:
                handle.seek(self._offset)
                chunk = handle.read(_MAX_BYTES_PER_POLL)
        except OSError:
            # Unreadable (permissions, deleted mid-read, ...): degrade to no signal.
            return b""
        self._offset += len(chunk)
        return chunk

    def poll(self) -> bool:
        """Consume newly appended log lines; return True if OUR progress was observed.

        Never raises. Returns False when the log is missing/unreadable/unparseable, when no
        line is attributable to our turn, or when the only new lines are housekeeping noise.
        """
        try:
            return self._poll_inner()
        except Exception:
            # Fail-safe by construction: an observer defect must not break a turn, and must
            # not fabricate progress either.
            return False

    def _poll_inner(self) -> bool:
        chunk = self._read_new_bytes()
        if not chunk:
            return False

        buf = self._pending + chunk
        # A partial final line is NOT parsed; it is carried to the next poll so a mid-line
        # truncated tail can never be misread.
        newline = buf.rfind(b"\n")
        if newline == -1:
            self._pending = buf
            return False
        complete, self._pending = buf[: newline + 1], buf[newline + 1 :]

        try:
            text = complete.decode("utf-8", errors="replace")
        except Exception:
            return False

        observed = False
        with self._lock:
            parent = self._parent
            for line in text.splitlines():
                if not line:
                    continue
                # HOP 1: learn a child id from a spawn announcement naming OUR parent.
                created = _CREATED_RE.search(line)
                if created is not None:
                    if parent and created.group("parent") == parent:
                        self._children.add(created.group("child"))
                    # A `created` line is an announcement, not agent-loop progress.
                    continue
                if not self._children:
                    continue
                # HOP 2: count agent-loop lines owned by one of OUR children.
                if classify_progress(line) is None:
                    continue
                session = _SESSION_RE.search(line)
                if session is None or session.group("sid") not in self._children:
                    continue
                observed = True
                self._progress_count += 1
            if observed:
                self._last_progress = time.monotonic()
        return observed


class ProgressPoller:
    """Run a :class:`SubagentProgressObserver` on a daemon thread, touching sinks.

    The thread is bound to a context manager so it CANNOT outlive the turn or leak across
    attempts. Each observed progress event calls every registered ``touch`` callable (the
    stall watchdog and the live display), which is exactly what stdout lines already do.
    """

    def __init__(
        self,
        observer: SubagentProgressObserver,
        touch_callbacks: tuple = (),
        interval: float = 1.0,
        on_progress=None,
    ) -> None:
        self.observer = observer
        self.interval = max(0.05, float(interval))
        self._touches = tuple(touch_callbacks)
        self._on_progress = on_progress
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _tick(self) -> None:
        if not self.observer.poll():
            return
        for touch in self._touches:
            try:
                touch()
            except Exception:
                # A misbehaving sink must not kill the poller or the turn.
                pass
        if self._on_progress is not None:
            try:
                self._on_progress()
            except Exception:
                pass

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            try:
                self._tick()
            except Exception:
                # Keep polling; a transient failure is not fatal.
                pass

    def __enter__(self) -> ProgressPoller:
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="aw-subagent-progress"
        )
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
