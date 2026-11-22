"""Zellij tab status glyphs and non-Zellij terminal window titles for aw runners.

When a runner executes inside Zellij (``$ZELLIJ_SESSION_NAME`` and ``$ZELLIJ_PANE_ID`` set
and attached to a TTY), this module prefixes only the runner's own Zellij tab with a status
glyph (and combines the failure badge ``🚨`` whenever at least one queue item has failed):

    Executing an IPD        : ▶
    Validating an item      : ☑
    Graduating/planning     : ⇑
    Reviewing any item      : 🆁
    Integrating a lane      : ⇄
    Re-running / correction : ↻
    Asking a question       : ❓
    Paused / waiting        : ⏸
    Finished cleanly        : ⏹
    Killed / died uncleanly : ⛒
    Has >= 1 failure        : 🚨  (appended after the current state glyph, e.g. '▶🚨', '⏹🚨')

Outside Zellij (attached to a TTY), this module emits OSC 2 (``ESC ] 2 ; <title> ESC \\``)
using the configured ``title_style`` (``short``, ``medium`` [default], ``long``, or ``none``).
Setting ``title_style`` to ``none`` disables both Zellij tab updates and OSC 2 window titles.

Terminal glyphs (``⏹``, ``⛒``, ``⏸`` at parked drain, plus ``🚨`` on failures) remain on
the tab after exit; starting another runner in the same tab strips any prior runner glyphs
before applying the new state, and ``aw reset-title`` clears them on demand.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Optional, Sequence, TextIO

STATE_EXECUTING = "executing"
STATE_VALIDATING = "validating"
STATE_GRADUATING = "graduating"
STATE_REVIEWING = "reviewing"
STATE_INTEGRATING = "integrating"
STATE_RERUNNING = "rerunning"
STATE_ASKING = "asking"
STATE_FINISHED = "finished"
STATE_KILLED = "killed"
STATE_PAUSED = "paused"

FAILURE_BADGE = "🚨"

STATE_GLYPHS: dict[str, str] = {
    STATE_EXECUTING: "▶",
    STATE_VALIDATING: "☑",
    STATE_GRADUATING: "⇑",
    STATE_REVIEWING: "🆁",
    STATE_INTEGRATING: "⇄",
    STATE_RERUNNING: "↻",
    STATE_ASKING: "❓",
    STATE_FINISHED: "⏹",
    STATE_KILLED: "⛒",
    STATE_PAUSED: "⏸",
}

# Retired glyphs still recognized by strip_runner_glyphs / `aw reset-title`.
_LEGACY_RUNNER_GLYPHS: frozenset[str] = frozenset({"⌕"})

ALL_RUNNER_GLYPHS: frozenset[str] = (
    frozenset(STATE_GLYPHS.values()) | {FAILURE_BADGE} | _LEGACY_RUNNER_GLYPHS
)

TITLE_STYLE_SHORT = "short"
TITLE_STYLE_MEDIUM = "medium"
TITLE_STYLE_LONG = "long"
TITLE_STYLE_NONE = "none"
TITLE_STYLE_VALUES: tuple[str, ...] = (
    TITLE_STYLE_SHORT,
    TITLE_STYLE_MEDIUM,
    TITLE_STYLE_LONG,
    TITLE_STYLE_NONE,
)
DEFAULT_TITLE_STYLE = TITLE_STYLE_MEDIUM

#: Queue item statuses that count as a failure for the combining ``🚨`` badge.
FAILURE_QUEUE_STATUSES: frozenset[str] = frozenset(
    {
        "fail-gate",
        "fail-begin",
        "fail-lane",
        "fail-verify",
        "fail-depend",
        "fail-merge",
        "failed",
        "failed-safely",
        "partial",
        "substantially-complete",
        "blocked",
        "dependency-blocked",
        "integration-blocked",
        "merge-conflict",
        "merge-needs-human",
        "merge-refused",
        "merge-unchecked",
    }
)

_TITLE_STYLE_OVERRIDE: Optional[str] = None
_ACTIVE_LOCK = threading.RLock()
_ACTIVE_CONTROLLER: Optional["RunnerTabStatus"] = None

ZellijRunnerFn = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def set_title_style_override(value: Optional[str]) -> None:
    """Set or clear the process-wide CLI ``--title-style`` override."""
    global _TITLE_STYLE_OVERRIDE
    if value is None:
        _TITLE_STYLE_OVERRIDE = None
        return
    token = str(value).strip().lower()
    if token not in TITLE_STYLE_VALUES:
        raise ValueError(
            f"Invalid title style {value!r}; expected one of: {', '.join(TITLE_STYLE_VALUES)}"
        )
    _TITLE_STYLE_OVERRIDE = token


def get_title_style_override() -> Optional[str]:
    """Return the current process-wide CLI ``--title-style`` override, or None."""
    return _TITLE_STYLE_OVERRIDE


def _configured_title_style() -> Optional[str]:
    """Fail-open reader for user config ``title_style``."""
    try:
        from agent_workflows import config as _config_mod

        return _config_mod.get_title_style()
    except Exception:
        return None


def resolve_title_style(override: Optional[str] = None) -> str:
    """Resolve effective title style (CLI override > config > default 'medium')."""
    for candidate in (override, _TITLE_STYLE_OVERRIDE, _configured_title_style()):
        if isinstance(candidate, str):
            token = candidate.strip().lower()
            if token in TITLE_STYLE_VALUES:
                return token
    return DEFAULT_TITLE_STYLE


def _stream_is_tty(stream: Optional[Any]) -> bool:
    if stream is None:
        return False
    isatty_fn = getattr(stream, "isatty", None)
    if not callable(isatty_fn):
        return False
    try:
        return bool(isatty_fn())
    except Exception:
        return False


def _target_tty_stream(stream: Optional[TextIO] = None) -> Optional[TextIO]:
    """Select the output stream for TTY checks and OSC 2 emission (prefers stderr when TTY)."""
    if stream is not None:
        return stream if _stream_is_tty(stream) else None
    if _stream_is_tty(sys.stderr):
        return sys.stderr
    if _stream_is_tty(sys.stdout):
        return sys.stdout
    return None


def _default_zellij_runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        capture_output=True,
        text=True,
        timeout=2.0,
        check=False,
    )


def strip_runner_glyphs(tab_name: str) -> str:
    """Remove any leading runner status glyphs (and trailing separator spaces) from ``tab_name``.

    Leaves names that do not start with a known runner status glyph untouched.
    """
    if not tab_name:
        return tab_name
    i = 0
    n = len(tab_name)
    saw_glyph = False
    while i < n:
        matched = False
        for glyph in ALL_RUNNER_GLYPHS:
            if tab_name.startswith(glyph, i):
                i += len(glyph)
                saw_glyph = True
                matched = True
                # Consume optional Unicode variation selector following a glyph.
                while i < n and tab_name[i] == "\ufe0f":
                    i += 1
                break
        if matched:
            while i < n and tab_name[i] == " ":
                i += 1
            continue
        break
    if not saw_glyph:
        return tab_name
    return tab_name[i:]


def format_glyph_prefix(state: str, *, has_failure: bool = False) -> str:
    """Build the glyph prefix for ``state``, appending ``🚨`` when ``has_failure`` is True."""
    glyph = STATE_GLYPHS.get(state, "")
    if not glyph:
        return FAILURE_BADGE if has_failure else ""
    return f"{glyph}{FAILURE_BADGE}" if has_failure else glyph


def format_tab_name(base_name: str, state: str, *, has_failure: bool = False) -> str:
    """Format a Zellij tab name with leading runner glyph(s) and cleaned base name (no trailing space)."""
    prefix = format_glyph_prefix(state, has_failure=has_failure)
    clean_base = strip_runner_glyphs(base_name)
    if not prefix:
        return clean_base
    if not clean_base:
        return prefix
    return f"{prefix}{clean_base}"


def format_window_title(
    state: str,
    *,
    style: str,
    host: str,
    repo_name: str,
    has_failure: bool = False,
) -> Optional[str]:
    """Build the non-Zellij OSC 2 terminal window title for ``style`` (None when style=='none')."""
    norm_style = str(style or DEFAULT_TITLE_STYLE).strip().lower()
    if norm_style == TITLE_STYLE_NONE:
        return None
    prefix = format_glyph_prefix(state, has_failure=has_failure)
    clean_repo = (repo_name or "").strip()
    clean_host = (host or "").strip() or "oc"
    if norm_style == TITLE_STYLE_SHORT:
        body = "aw"
    elif norm_style == TITLE_STYLE_LONG:
        body = f"aw {clean_host} run {clean_repo}".strip()
    else:
        body = f"aw {clean_repo}".strip() if clean_repo else "aw"
    return f"{prefix}{body}" if prefix else body


def queue_has_failure(run_state: Optional[Mapping[str, Any]]) -> bool:
    """Return True if at least one queue item in ``run_state`` holds a failure status."""
    if not isinstance(run_state, Mapping):
        return False
    queue = run_state.get("queue")
    if not isinstance(queue, list):
        return False
    for item in queue:
        if not isinstance(item, Mapping):
            continue
        status = str(item.get("status") or "").strip()
        if status in FAILURE_QUEUE_STATUSES:
            return True
    return False


def item_active_state(
    item: Mapping[str, Any],
    *,
    attempt_no: int = 1,
    recovery: bool = False,
) -> str:
    """Map a queue item and attempt metadata to its primary active runner status."""
    if attempt_no > 1 or recovery or item.get("requeue_from_status"):
        return STATE_RERUNNING
    action = str(item.get("action") or "execute").strip().lower()
    if action == "review":
        return STATE_REVIEWING
    if action == "plan":
        return STATE_GRADUATING
    return STATE_EXECUTING


def _is_in_zellij(env: Optional[Mapping[str, str]] = None) -> bool:
    source = os.environ if env is None else env
    return bool(str(source.get("ZELLIJ_SESSION_NAME") or "").strip())


def _resolve_zellij_own_tab(
    *,
    env: Optional[Mapping[str, str]] = None,
    runner: ZellijRunnerFn = _default_zellij_runner,
) -> tuple[Optional[int], Optional[str]]:
    """Resolve ``(tab_id, current_tab_name)`` for this process's own Zellij pane.

    Matches ``$ZELLIJ_PANE_ID`` against non-plugin panes from
    ``zellij action list-panes --tab --json``. Returns ``(None, None)`` if the pane
    cannot be resolved, so a background process never renames the wrong tab.
    """
    source = os.environ if env is None else env
    pane_id = str(source.get("ZELLIJ_PANE_ID") or "").strip()
    if not pane_id:
        return (None, None)
    try:
        res = runner(["zellij", "action", "list-panes", "--tab", "--json"])
        if res.returncode != 0 or not res.stdout.strip():
            return (None, None)
        panes = json.loads(res.stdout)
    except Exception:
        return (None, None)
    if not isinstance(panes, list):
        return (None, None)
    for pane in panes:
        if not isinstance(pane, Mapping):
            continue
        if pane.get("is_plugin"):
            continue
        if str(pane.get("id")) == pane_id:
            tab_id = pane.get("tab_id")
            tab_name = pane.get("tab_name")
            if isinstance(tab_id, int):
                return (tab_id, str(tab_name or ""))
    return (None, None)


def _rename_zellij_tab(
    tab_id: int,
    new_name: str,
    *,
    runner: ZellijRunnerFn = _default_zellij_runner,
) -> bool:
    try:
        res = runner(
            ["zellij", "action", "rename-tab", "--tab-id", str(tab_id), new_name]
        )
        return res.returncode == 0
    except Exception:
        return False


def _emit_osc2_title(title: str, stream: TextIO) -> bool:
    """Write OSC 2 (ST-terminated) to ``stream``."""
    safe_title = title.replace("\x1b", "").replace("\x07", "").replace("\n", " ")
    try:
        stream.write(f"\x1b]2;{safe_title}\x1b\\")
        stream.flush()
        return True
    except OSError:
        return False


class RunnerTabStatus:
    """Stateful controller for a single runner invocation's Zellij tab or OSC 2 title."""

    def __init__(
        self,
        *,
        host: str,
        repo: Path | str | None = None,
        title_style: Optional[str] = None,
        agent_mode: bool = False,
        stream: Optional[TextIO] = None,
        env: Optional[Mapping[str, str]] = None,
        zellij_runner: Optional[ZellijRunnerFn] = None,
    ) -> None:
        self.host = str(host or "oc").strip()
        repo_path = Path(repo) if repo is not None else Path.cwd()
        self.repo_name = repo_path.name or str(repo_path)
        self.title_style = resolve_title_style(title_style)
        self.agent_mode = bool(agent_mode)
        self._env = env
        self._stream = stream
        self._zellij_runner: ZellijRunnerFn = (
            zellij_runner if zellij_runner is not None else _default_zellij_runner
        )
        self._lock = threading.RLock()
        self._enabled = (not self.agent_mode) and (self.title_style != TITLE_STYLE_NONE)
        self._is_zellij = _is_in_zellij(self._env)
        self._tab_resolved = False
        self._tab_id: Optional[int] = None
        self._base_tab_name: Optional[str] = None
        self.current_state: Optional[str] = None
        self.has_failure: bool = False
        self._last_rendered: Optional[str] = None
        self._activated: bool = False
        self._finalized: bool = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def activated(self) -> bool:
        return self._activated

    def _can_emit(self) -> bool:
        if not self._enabled:
            return False
        return _target_tty_stream(self._stream) is not None

    def _ensure_zellij_tab(self) -> bool:
        if self._tab_resolved:
            return self._tab_id is not None
        self._tab_resolved = True
        tab_id, current_name = _resolve_zellij_own_tab(
            env=self._env, runner=self._zellij_runner
        )
        if tab_id is None:
            return False
        self._tab_id = tab_id
        self._base_tab_name = strip_runner_glyphs(current_name or "")
        return True

    def _render(self) -> bool:
        if not self.current_state or not self._can_emit():
            return False
        if self._is_zellij:
            if not self._ensure_zellij_tab() or self._tab_id is None:
                return False
            desired = format_tab_name(
                self._base_tab_name or "",
                self.current_state,
                has_failure=self.has_failure,
            )
            if desired == self._last_rendered:
                return False
            if _rename_zellij_tab(self._tab_id, desired, runner=self._zellij_runner):
                self._last_rendered = desired
                self._activated = True
                return True
            return False

        title = format_window_title(
            self.current_state,
            style=self.title_style,
            host=self.host,
            repo_name=self.repo_name,
            has_failure=self.has_failure,
        )
        if title is None or title == self._last_rendered:
            return False
        target = _target_tty_stream(self._stream)
        if target is None:
            return False
        if _emit_osc2_title(title, target):
            self._last_rendered = title
            self._activated = True
            return True
        return False

    def set_state(
        self,
        state: str,
        *,
        has_failure: Optional[bool] = None,
        run_state: Optional[Mapping[str, Any]] = None,
    ) -> bool:
        """Update the current runner status glyph and re-render if changed."""
        if state not in STATE_GLYPHS:
            return False
        with self._lock:
            self.current_state = state
            if has_failure is not None:
                self.has_failure = bool(has_failure)
            elif run_state is not None:
                self.has_failure = self.has_failure or queue_has_failure(run_state)
            return self._render()

    def refresh_failure(self, run_state: Optional[Mapping[str, Any]]) -> bool:
        """Refresh the ``🚨`` badge from ``run_state`` without changing the primary state."""
        if run_state is None:
            return False
        with self._lock:
            failed = queue_has_failure(run_state)
            if failed == self.has_failure:
                return False
            self.has_failure = failed
            return self._render()

    @contextlib.contextmanager
    def temporary(
        self,
        state: str,
        *,
        has_failure: Optional[bool] = None,
    ) -> Iterator[None]:
        """Temporarily switch to ``state`` and restore the previous state on exit."""
        with self._lock:
            prev_state = self.current_state
            prev_failure = self.has_failure
        self.set_state(state, has_failure=has_failure)
        try:
            yield
        finally:
            with self._lock:
                if not self._finalized:
                    if prev_state is not None:
                        self.current_state = prev_state
                        if has_failure is None:
                            self.has_failure = self.has_failure or prev_failure
                        self._render()

    def mark_finished(
        self,
        run_state: Optional[Mapping[str, Any]] = None,
        *,
        paused: bool = False,
    ) -> bool:
        """Mark the run as cleanly finished (``⏹``) or parked/paused at drain (``⏸``)."""
        with self._lock:
            self._finalized = True
            if run_state is not None:
                self.has_failure = queue_has_failure(run_state)
            target_state = STATE_PAUSED if paused else STATE_FINISHED
            self.current_state = target_state
            return self._render()

    def mark_killed(
        self,
        run_state: Optional[Mapping[str, Any]] = None,
        *,
        only_if_activated: bool = True,
    ) -> bool:
        """Mark the run as killed / died uncleanly (``⛒``)."""
        with self._lock:
            if only_if_activated and not self._activated:
                return False
            self._finalized = True
            if run_state is not None:
                self.has_failure = self.has_failure or queue_has_failure(run_state)
            self.current_state = STATE_KILLED
            return self._render()


def get_active_controller() -> Optional[RunnerTabStatus]:
    with _ACTIVE_LOCK:
        return _ACTIVE_CONTROLLER


@contextlib.contextmanager
def runner_status_session(
    *,
    host: str,
    repo: Path | str | None = None,
    title_style: Optional[str] = None,
    agent_mode: bool = False,
    stream: Optional[TextIO] = None,
    env: Optional[Mapping[str, str]] = None,
    zellij_runner: Optional[ZellijRunnerFn] = None,
) -> Iterator[RunnerTabStatus]:
    """Install a :class:`RunnerTabStatus` as the process-active controller for a runner invocation."""
    global _ACTIVE_CONTROLLER
    ctrl = RunnerTabStatus(
        host=host,
        repo=repo,
        title_style=title_style,
        agent_mode=agent_mode,
        stream=stream,
        env=env,
        zellij_runner=zellij_runner,
    )
    with _ACTIVE_LOCK:
        prev = _ACTIVE_CONTROLLER
        _ACTIVE_CONTROLLER = ctrl
    try:
        yield ctrl
    finally:
        with _ACTIVE_LOCK:
            _ACTIVE_CONTROLLER = prev


def set_active_state(
    state: str,
    *,
    has_failure: Optional[bool] = None,
    run_state: Optional[Mapping[str, Any]] = None,
) -> bool:
    ctrl = get_active_controller()
    if ctrl is None:
        return False
    return ctrl.set_state(state, has_failure=has_failure, run_state=run_state)


def refresh_active_failure(run_state: Optional[Mapping[str, Any]]) -> bool:
    ctrl = get_active_controller()
    if ctrl is None:
        return False
    return ctrl.refresh_failure(run_state)


@contextlib.contextmanager
def temporary_active_state(
    state: str,
    *,
    has_failure: Optional[bool] = None,
) -> Iterator[None]:
    ctrl = get_active_controller()
    if ctrl is None:
        yield
        return
    with ctrl.temporary(state, has_failure=has_failure):
        yield


def mark_active_finished(
    run_state: Optional[Mapping[str, Any]] = None,
    *,
    paused: bool = False,
) -> bool:
    ctrl = get_active_controller()
    if ctrl is None:
        return False
    return ctrl.mark_finished(run_state, paused=paused)


def mark_active_killed(
    run_state: Optional[Mapping[str, Any]] = None,
    *,
    only_if_activated: bool = True,
) -> bool:
    ctrl = get_active_controller()
    if ctrl is None:
        return False
    return ctrl.mark_killed(run_state, only_if_activated=only_if_activated)


def reset_title(
    *,
    all_tabs: bool = False,
    explicit_name: Optional[str] = None,
    stream: Optional[TextIO] = None,
    env: Optional[Mapping[str, str]] = None,
    zellij_runner: Optional[ZellijRunnerFn] = None,
) -> dict[str, Any]:
    """Reset / clear runner status glyphs from the Zellij tab(s) or outer terminal window title.

    Under Zellij:
      - By default, resolves this pane's own tab via ``$ZELLIJ_PANE_ID`` and strips any
        leading runner status glyphs (or renames to ``explicit_name`` if provided).
      - With ``all_tabs=True``, strips leading runner status glyphs from every tab in the
        current Zellij session that currently carries them.

    Outside Zellij:
      - Emits OSC 2 with an empty title (or ``explicit_name``) to the attached TTY stream.
    """
    runner = zellij_runner if zellij_runner is not None else _default_zellij_runner
    if _is_in_zellij(env):
        if all_tabs:
            try:
                res = runner(["zellij", "action", "list-tabs", "--all", "--json"])
                tabs = (
                    json.loads(res.stdout)
                    if res.returncode == 0 and res.stdout.strip()
                    else []
                )
            except Exception:
                return {
                    "environment": "zellij",
                    "changed": False,
                    "tabs_reset": [],
                    "message": "Could not query Zellij tabs.",
                }
            reset_entries: list[dict[str, Any]] = []
            for tab in tabs:
                if not isinstance(tab, Mapping):
                    continue
                tab_id = tab.get("tab_id")
                name = str(tab.get("name") or "")
                if not isinstance(tab_id, int):
                    continue
                cleaned = strip_runner_glyphs(name)
                if cleaned != name:
                    if _rename_zellij_tab(tab_id, cleaned, runner=runner):
                        reset_entries.append(
                            {"tab_id": tab_id, "before": name, "after": cleaned}
                        )
            return {
                "environment": "zellij",
                "changed": bool(reset_entries),
                "tabs_reset": reset_entries,
                "message": (
                    f"Reset {len(reset_entries)} Zellij tab(s)."
                    if reset_entries
                    else "No Zellij tabs had runner status glyphs."
                ),
            }

        tab_id, current_name = _resolve_zellij_own_tab(env=env, runner=runner)
        if tab_id is None:
            return {
                "environment": "zellij",
                "changed": False,
                "tabs_reset": [],
                "message": "Could not resolve current Zellij tab from ZELLIJ_PANE_ID.",
            }
        before = current_name or ""
        after = (
            explicit_name if explicit_name is not None else strip_runner_glyphs(before)
        )
        if after == before:
            return {
                "environment": "zellij",
                "changed": False,
                "tabs_reset": [],
                "tab_id": tab_id,
                "before": before,
                "after": after,
                "message": f"Tab {tab_id} ({before!r}) already has no runner status glyphs.",
            }
        ok = _rename_zellij_tab(tab_id, after, runner=runner)
        return {
            "environment": "zellij",
            "changed": ok,
            "tabs_reset": (
                [{"tab_id": tab_id, "before": before, "after": after}] if ok else []
            ),
            "tab_id": tab_id,
            "before": before,
            "after": after,
            "message": (
                f"Restored tab {tab_id}: {before!r} -> {after!r}."
                if ok
                else f"Failed to rename Zellij tab {tab_id}."
            ),
        }

    # Outside Zellij: clear (or set explicit) OSC 2 terminal window title when attached to a TTY.
    target = _target_tty_stream(stream)
    if target is None:
        return {
            "environment": "terminal",
            "changed": False,
            "message": "Not attached to a TTY; terminal window title not modified.",
        }
    desired = explicit_name if explicit_name is not None else ""
    ok = _emit_osc2_title(desired, target)
    return {
        "environment": "terminal",
        "changed": ok,
        "title": desired,
        "message": (
            f"Set terminal window title to {desired!r}."
            if desired
            else "Cleared terminal window title."
        )
        if ok
        else "Failed to write terminal window title sequence.",
    }
