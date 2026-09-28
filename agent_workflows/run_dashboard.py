#!/usr/bin/env python3
"""runsdash (`97i0ao`): per-session facts and the drill-down run dashboard.

WHY THIS MODULE EXISTS. The analytics cache (Order 05) keeps RUN totals only: no model, no tool
activity, no per-attempt grain. The questions a maintainer actually asks of the corpus are
comparative and per turn: which model or host spends more tokens, time or tool calls on a review
versus an execute versus a verify; what retries and failed attempts waste; which turns thrash on
reads or shell calls. Those answers live in the per-session JSONL logs the drivers already keep,
so this module reads them directly.

ONE ROW PER AGENT SESSION. Each queue attempt in ``state.json`` launches one main session (``log``)
and optionally a verifier session (``verify_log``), a gate-answer session and a defect re-ask
session. Each becomes its own row, labeled with its ROLE, so the cost of verification is visible on
its own rather than folded into the execute turn. Session files that no attempt names are still
counted (role inferred from the filename), so nothing on disk is silently dropped.

THE LOGS ARE THE SOURCE OF TRUTH FOR NUMBERS, ``state.json`` FOR LABELS. Tokens, cost, steps, tools
and timings are summed from the session log itself; ``state.json`` supplies the action, disposition,
verification verdict, Set and model. Where ``state.json`` reports tokens and the log has none
(a truncated or missing log), the state figures are used and the row says so in ``source``.

MODEL IDENTITY IS REPORTED, NEVER GUESSED. A run records its model in ``options.model`` or
``options.cost_attribution.model``; many older runs record neither and OpenCode session logs carry
no model id, so such rows read ``(unrecorded)``. Backlog ``7yz545`` carries the driver-side fix.

A DISPOSABLE STATS CACHE. Parsing ~770 MB of logs takes tens of seconds, so per-file stats are cached
under the reserved analytics namespace keyed by ``(size, mtime_ns)``. Deleting it costs one re-parse.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

__all__ = [
    "DASHBOARD_SCHEMA_VERSION",
    "ASSETS_DIRNAME",
    "TOOL_CATEGORIES",
    "tool_category",
    "command_kind",
    "session_stats",
    "collect_rows",
    "build_payload",
    "render_dashboard",
]

DASHBOARD_SCHEMA_VERSION = 2
ASSETS_DIRNAME = "run_dashboard_assets"
STATS_CACHE_FILENAME = "dashboard-session-stats.json"
UNRECORDED = "(unrecorded)"

# --- tool taxonomy ---------------------------------------------------------------------------------

#: Both hosts' tool names mapped onto one small vocabulary, so a read on OpenCode and a read on
#: Antigravity land in the same column.
TOOL_CATEGORIES: dict[str, str] = {
    # OpenCode
    "bash": "shell",
    "read": "read",
    "edit": "edit",
    "write": "write",
    "grep": "search",
    "glob": "search",
    "list": "search",
    "todowrite": "todo",
    "todoread": "todo",
    "task": "subagent",
    "webfetch": "web",
    "skill": "other",
    # Antigravity
    "run_command": "shell",
    "view_file": "read",
    "view_file_outline": "read",
    "replace_file_content": "edit",
    "multi_replace_file_content": "edit",
    "write_to_file": "write",
    "grep_search": "search",
    "find_by_name": "search",
    "list_dir": "search",
    "manage_task": "todo",
    "schedule": "wait",
    "browser_subagent": "subagent",
}

CATEGORY_ORDER: tuple[str, ...] = (
    "read",
    "edit",
    "write",
    "shell",
    "search",
    "todo",
    "wait",
    "subagent",
    "web",
    "other",
)


def tool_category(name: str) -> str:
    name = (name or "").strip()
    if name in TOOL_CATEGORIES:
        return TOOL_CATEGORIES[name]
    low = name.lower()
    if low.startswith("browser"):
        return "web"
    return "other"


#: Shell command kinds, checked in order against the command text. The first match wins.
_COMMAND_KINDS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("test", re.compile(r"\b(pytest|unittest|make\s+test|tox|nox)\b")),
    (
        "aw",
        re.compile(
            r"(^|[\s;&|(])(aw|agent-workflows)\s|python3?\s+-m\s+agent_workflows\b"
        ),
    ),
    ("git", re.compile(r"(^|[\s;&|(])git\s")),
    ("lint", re.compile(r"\b(ruff|flake8|mypy|black|pre-commit)\b")),
    (
        "inspect",
        re.compile(
            r"(^|[\s;&|(])(cat|head|tail|sed\s+-n|less|wc|ls|find|rg|grep|tree|stat|du|file)\s"
        ),
    ),
    ("python", re.compile(r"(^|[\s;&|(])python3?\b")),
)


def command_kind(command: str) -> str:
    text = " " + (command or "").strip() + " "
    for kind, pattern in _COMMAND_KINDS:
        if pattern.search(text):
            return kind
    return "other"


# --- one session log -------------------------------------------------------------------------------


def _num(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def _empty_stats() -> dict[str, Any]:
    return {
        "format": "unknown",
        "steps": 0,
        "input": 0.0,
        "output": 0.0,
        "reasoning": 0.0,
        "cache_read": 0.0,
        "cache_write": 0.0,
        "cost": 0.0,
        "has_cost": False,
        "has_tokens": False,
        "tools": {},
        "tool_err": {},
        "categories": {},
        "commands": {},
        "tool_calls": 0,
        "tool_errors": 0,
        "tool_seconds": 0.0,
        "llm_seconds": 0.0,
        "first_ts": None,
        "last_ts": None,
        "files_read": 0,
        "files_edited": 0,
        "result_status": None,
        "error_messages": 0,
    }


def _bump(counter: dict[str, int], key: str, by: int = 1) -> None:
    counter[key] = counter.get(key, 0) + by


def _note_ts(stats: dict[str, Any], ts: float | None) -> None:
    if ts is None:
        return
    if stats["first_ts"] is None or ts < stats["first_ts"]:
        stats["first_ts"] = ts
    if stats["last_ts"] is None or ts > stats["last_ts"]:
        stats["last_ts"] = ts


def _record_tool(
    stats: dict[str, Any],
    name: str,
    *,
    error: bool,
    seconds: float,
    command: str | None,
    path: str | None,
    read_paths: set,
    edit_paths: set,
) -> None:
    stats["tool_calls"] += 1
    _bump(stats["tools"], name or "?")
    cat = tool_category(name)
    _bump(stats["categories"], cat)
    if error:
        stats["tool_errors"] += 1
        _bump(stats["tool_err"], name or "?")
    stats["tool_seconds"] += max(0.0, seconds)
    if cat == "shell" and command is not None:
        _bump(stats["commands"], command_kind(command))
    if path:
        if cat == "read":
            read_paths.add(path)
        elif cat in ("edit", "write"):
            edit_paths.add(path)


def session_stats(path: Path | str) -> dict[str, Any]:
    """Parse one session JSONL of either host into numeric stats. Never raises on bad content."""

    stats = _empty_stats()
    read_paths: set[str] = set()
    edit_paths: set[str] = set()
    try:
        handle = open(path, "r", encoding="utf-8", errors="replace")
    except OSError:
        return stats
    with handle:
        for line in handle:
            line = line.strip()
            if not line or line[0] != "{":
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if not isinstance(obj, dict):
                continue
            if "event" in obj:
                stats["format"] = "agy"
                _agy_line(obj, stats, read_paths, edit_paths)
            elif "type" in obj and "part" in obj:
                stats["format"] = "oc"
                _oc_line(obj, stats, read_paths, edit_paths)
    stats["files_read"] = len(read_paths)
    stats["files_edited"] = len(edit_paths)
    return stats


def _oc_line(
    obj: Mapping[str, Any], stats: dict[str, Any], read_paths: set, edit_paths: set
) -> None:
    kind = obj.get("type")
    part: Mapping[str, Any] = (
        obj["part"] if isinstance(obj.get("part"), Mapping) else {}
    )
    ts = obj.get("timestamp")
    _note_ts(stats, _num(ts) / 1000.0 if isinstance(ts, (int, float)) else None)
    if kind == "step_finish":
        stats["steps"] += 1
        toks: Mapping[str, Any] | None = (
            part["tokens"] if isinstance(part.get("tokens"), Mapping) else None
        )
        if toks:
            stats["has_tokens"] = True
            stats["input"] += _num(toks.get("input"))
            stats["output"] += _num(toks.get("output"))
            stats["reasoning"] += _num(toks.get("reasoning"))
            cache = toks.get("cache")
            if isinstance(cache, Mapping):
                stats["cache_read"] += _num(cache.get("read"))
                stats["cache_write"] += _num(cache.get("write"))
            else:
                stats["cache_read"] += _num(cache)
        if isinstance(part.get("cost"), (int, float)) and not isinstance(
            part.get("cost"), bool
        ):
            stats["cost"] += float(part["cost"])
            stats["has_cost"] = True
    elif kind == "tool_use":
        state: Mapping[str, Any] = (
            part["state"] if isinstance(part.get("state"), Mapping) else {}
        )
        name = str(part.get("tool") or "")
        inp: Mapping[str, Any] = (
            state["input"] if isinstance(state.get("input"), Mapping) else {}
        )
        t: Mapping[str, Any] = (
            state["time"] if isinstance(state.get("time"), Mapping) else {}
        )
        secs = (
            (_num(t.get("end")) - _num(t.get("start"))) / 1000.0
            if t.get("end")
            else 0.0
        )
        command = inp.get("command") if name == "bash" else None
        fpath = inp.get("filePath")
        _record_tool(
            stats,
            name,
            error=state.get("status") == "error",
            seconds=secs,
            command=str(command) if command is not None else None,
            path=str(fpath) if fpath else None,
            read_paths=read_paths,
            edit_paths=edit_paths,
        )
    elif kind == "error":
        stats["error_messages"] += 1


def _agy_line(
    obj: Mapping[str, Any], stats: dict[str, Any], read_paths: set, edit_paths: set
) -> None:
    event = obj.get("event")
    if event == "result":
        res: Mapping[str, Any] = (
            obj["result"] if isinstance(obj.get("result"), Mapping) else {}
        )
        stats["result_status"] = res.get("status")
        return
    su = obj.get("step_update")
    if not isinstance(su, Mapping):
        return
    state = su.get("state")
    stype = su.get("step_type")
    if state not in ("DONE", "ERROR"):
        return
    secs = _num(su.get("duration_seconds"))
    if stype == "agent_response":
        stats["steps"] += 1
        stats["llm_seconds"] += secs
        usage: Mapping[str, Any] | None = (
            su["usage"] if isinstance(su.get("usage"), Mapping) else None
        )
        if usage:
            stats["has_tokens"] = True
            stats["input"] += _num(usage.get("input_tokens"))
            stats["output"] += _num(usage.get("output_tokens"))
            stats["reasoning"] += _num(usage.get("thinking_tokens"))
            stats["cache_read"] += _num(usage.get("cache_read_tokens"))
    elif stype == "tool":
        name = str(su.get("tool_name") or "")
        info: Mapping[str, Any] = (
            su["tool_info"] if isinstance(su.get("tool_info"), Mapping) else {}
        )
        params: Mapping[str, Any] = (
            info["parameters"] if isinstance(info.get("parameters"), Mapping) else {}
        )
        command = params.get("CommandLine") if name == "run_command" else None
        fpath = params.get("AbsolutePath") or params.get("TargetFile")
        _record_tool(
            stats,
            name,
            error=state == "ERROR",
            seconds=secs,
            command=str(command) if command is not None else None,
            path=str(fpath) if fpath else None,
            read_paths=read_paths,
            edit_paths=edit_paths,
        )
    elif stype == "error_message":
        stats["error_messages"] += 1


# --- the stats cache -------------------------------------------------------------------------------


class _StatsCache:
    """Per-session-file stats keyed by path with a (size, mtime_ns) freshness check."""

    def __init__(self, path: Path | None) -> None:
        self.path = path
        self.data: dict[str, Any] = {}
        self.dirty = False
        self.hits = 0
        self.misses = 0
        if path is not None and path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if raw.get("schema") == DASHBOARD_SCHEMA_VERSION and isinstance(
                    raw.get("files"), dict
                ):
                    self.data = raw["files"]
            except (OSError, ValueError, AttributeError):
                self.data = {}

    def get(self, file: Path) -> dict[str, Any]:
        key = str(file)
        try:
            st = file.stat()
        except OSError:
            return _empty_stats()
        stamp = [st.st_size, st.st_mtime_ns]
        hit = self.data.get(key)
        if (
            isinstance(hit, dict)
            and hit.get("stamp") == stamp
            and isinstance(hit.get("stats"), dict)
        ):
            self.hits += 1
            return hit["stats"]
        self.misses += 1
        stats = session_stats(file)
        self.data[key] = {"stamp": stamp, "stats": stats}
        self.dirty = True
        return stats

    def save(self, live_keys: set[str]) -> None:
        if self.path is None:
            return
        stale = [k for k in self.data if k not in live_keys]
        for k in stale:
            del self.data[k]
            self.dirty = True
        if not self.dirty:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(
                    {"schema": DASHBOARD_SCHEMA_VERSION, "files": self.data},
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            os.replace(tmp, self.path)
        except OSError:
            pass


def _default_cache_path(repo: Path | str | None) -> Path | None:
    try:
        from agent_workflows.runner_shared import analytics_cache_dir

        return analytics_cache_dir(repo) / STATS_CACHE_FILENAME
    except Exception:
        return None


# --- rows ------------------------------------------------------------------------------------------

_SESSION_NAME_RE = re.compile(
    r"^(?P<pos>\d+)-(?P<id6>[a-z0-9]{6})-(?:(?P<vpre>verify)-)?attempt-(?P<att>\d+)(?:-(?P<role>[a-z-]+))?\.jsonl$"
)

_SUCCESS = {"executed", "reviewed", "approved", "substantially-complete"}
_FAIL = {
    "blocked",
    "fail-gate",
    "fail-merge",
    "fail-verify",
    "failed-safely",
    "integration-blocked",
    "merge-conflict",
    "merge-refused",
    "interrupted",
    "fail-depend",
}


def _outcome(disposition: str | None, role: str, verification: str | None) -> str:
    """Collapse the many dispositions into success / partial / failed / unknown for comparison."""

    if role == "verify":
        if verification == "verified":
            return "success"
        if verification in ("unverified", "blocked"):
            return "failed"
        return "unknown"
    d = (disposition or "").strip()
    if d in ("executed", "reviewed", "approved"):
        return "success"
    if d in ("substantially-complete", "partial"):
        return "partial"
    if d in _FAIL:
        return "failed"
    return "unknown"


def _iso_ts(value: Any) -> float | None:
    if not value:
        return None
    try:
        return _dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _run_model(state: Mapping[str, Any]) -> tuple[str, str]:
    opts: Mapping[str, Any] = (
        state["options"] if isinstance(state.get("options"), Mapping) else {}
    )
    ca: Mapping[str, Any] = (
        opts["cost_attribution"]
        if isinstance(opts.get("cost_attribution"), Mapping)
        else {}
    )
    model = opts.get("model") or opts.get("explicit_model") or ca.get("model")
    source = (
        "options"
        if (opts.get("model") or opts.get("explicit_model"))
        else ("cost_attribution" if ca.get("model") else "")
    )
    return (_normalize_model(str(model)) if model else UNRECORDED, source)


def _normalize_model(model: str) -> str:
    """Strip provider prefixes so the same model reads the same across hosts."""

    m = model.strip()
    for prefix in ("uri/", "google/", "anthropic/", "openai/"):
        if m.startswith(prefix):
            m = m[len(prefix) :]
    return m


def _run_host(state: Mapping[str, Any], formats: Iterable[str]) -> str:
    drv: Mapping[str, Any] = (
        state["driver"] if isinstance(state.get("driver"), Mapping) else {}
    )
    did = str(drv.get("id") or "")
    if did.startswith("agy"):
        return "agy"
    if did.startswith("oc"):
        return "oc"
    opts: Mapping[str, Any] = (
        state["options"] if isinstance(state.get("options"), Mapping) else {}
    )
    if opts.get("opencode"):
        return "oc"
    ca: Mapping[str, Any] = (
        opts["cost_attribution"]
        if isinstance(opts.get("cost_attribution"), Mapping)
        else {}
    )
    if ca.get("host") in ("oc", "agy"):
        return str(ca["host"])
    for f in formats:
        if f in ("oc", "agy"):
            return f
    return "unknown"


def _resolve_log(run_dir: Path, value: Any) -> Path | None:
    """A recorded log path, re-rooted into THIS run dir (records may be moved or read elsewhere)."""

    if not value:
        return None
    name = Path(str(value)).name
    candidate = run_dir / "sessions" / name
    if candidate.is_file():
        return candidate
    raw = Path(str(value))
    return raw if raw.is_file() else None


def _row_from_stats(
    base: Mapping[str, Any],
    stats: Mapping[str, Any],
    role: str,
    fallback_tokens: Mapping[str, Any] | None,
    fallback_cost: Any,
    started: float | None,
    ended: float | None,
) -> dict[str, Any]:
    row = dict(base)
    row["role"] = role
    inp, out, rsn = (
        stats.get("input", 0.0),
        stats.get("output", 0.0),
        stats.get("reasoning", 0.0),
    )
    cread, cwrite = stats.get("cache_read", 0.0), stats.get("cache_write", 0.0)
    source = "log"
    if not stats.get("has_tokens") and isinstance(fallback_tokens, Mapping):
        inp = _num(fallback_tokens.get("input"))
        out = _num(fallback_tokens.get("output"))
        rsn = _num(fallback_tokens.get("reasoning"))
        cread = _num(fallback_tokens.get("cache") or fallback_tokens.get("cache_read"))
        cwrite = 0.0
        source = "state"
    if not stats.get("has_tokens") and not isinstance(fallback_tokens, Mapping):
        source = "none"
    cost: float | None = stats.get("cost") if stats.get("has_cost") else None
    if (
        cost is None
        and isinstance(fallback_cost, (int, float))
        and not isinstance(fallback_cost, bool)
    ):
        cost = float(fallback_cost)
    first, last = stats.get("first_ts"), stats.get("last_ts")
    start = started if started is not None else first
    if role != "main" or start is None:
        start = first if first is not None else start
    end = last if (role != "main" or ended is None) else ended
    wall = (
        (end - start)
        if (start is not None and end is not None and end >= start)
        else None
    )
    cats = stats.get("categories") or {}
    cmds = stats.get("commands") or {}
    row.update(
        {
            "input": inp,
            "output": out,
            "reasoning": rsn,
            "cache_read": cread,
            "cache_write": cwrite,
            "fresh_tokens": inp + out,
            "total_tokens": inp + out + cread + cwrite,
            "cost": cost,
            "wall": wall,
            "start": start,
            "steps": stats.get("steps", 0),
            "tool_calls": stats.get("tool_calls", 0),
            "tool_errors": stats.get("tool_errors", 0),
            "tool_seconds": stats.get("tool_seconds", 0.0),
            "files_read": stats.get("files_read", 0),
            "files_edited": stats.get("files_edited", 0),
            "token_source": source,
            "tools": dict(stats.get("tools") or {}),
            "tool_err": dict(stats.get("tool_err") or {}),
        }
    )
    for c in CATEGORY_ORDER:
        row["t_" + c] = int(cats.get(c, 0))
    for k in ("test", "git", "aw", "inspect", "python", "lint", "other"):
        row["sh_" + k] = int(cmds.get(k, 0))
    return row


def collect_rows(
    run_dirs: Sequence[Path],
    *,
    repo: Path | str | None = None,
    cache_path: Path | None | str = "default",
    progress: Callable[[int, int], None] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """One row per agent session across ``run_dirs``. Returns ``(rows, info)``."""

    if cache_path == "default":
        cpath = _default_cache_path(repo)
    else:
        cpath = Path(cache_path) if cache_path else None
    cache = _StatsCache(cpath)
    rows: list[dict[str, Any]] = []
    live: set[str] = set()
    runs_without_state = 0
    total = len(run_dirs)
    for index, run_dir in enumerate(run_dirs, 1):
        if progress:
            progress(index, total)
        run_dir = Path(run_dir)
        try:
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                state = {}
        except (OSError, ValueError):
            state = {}
            runs_without_state += 1
        sessions_dir = run_dir / "sessions"
        session_files = (
            sorted(sessions_dir.glob("*.jsonl")) if sessions_dir.is_dir() else []
        )
        claimed: set[Path] = set()
        stats_of: dict[Path, dict[str, Any]] = {}
        for f in session_files:
            live.add(str(f))
            stats_of[f] = cache.get(f)
        model, model_source = _run_model(state)
        host = _run_host(state, (s.get("format") for s in stats_of.values()))
        if model == UNRECORDED:
            # Per host, so an unknown OpenCode model never pools with an unknown Antigravity one.
            model = "(unrecorded, {0})".format(host)
        run_id = str(state.get("run_id") or run_dir.name)
        run_start = _iso_ts(state.get("created_at"))
        queue = state.get("queue") if isinstance(state.get("queue"), list) else []
        by_item_attempt: dict[tuple[str, int], dict[str, Any]] = {}
        for item in queue:
            if not isinstance(item, Mapping):
                continue
            id6 = str(item.get("id6") or "")
            action = str(item.get("action") or "execute")
            attempts = (
                item.get("attempts") if isinstance(item.get("attempts"), list) else []
            )
            n_attempts = len(attempts)
            for att in attempts:
                if not isinstance(att, Mapping):
                    continue
                number = int(_num(att.get("number")) or 1)
                att_action = str(att.get("action") or action)
                disposition = att.get("disposition")
                verification = att.get("verification") or att.get("verification_status")
                base = {
                    "run": run_id,
                    "set": str(item.get("setid") or ""),
                    "id6": id6,
                    "kind": str(item.get("kind") or ""),
                    "action": att_action,
                    "attempt": number,
                    "attempts_total": n_attempts,
                    "retry": number > 1,
                    "recovery": bool(att.get("recovery")),
                    "disposition": str(disposition or "(none)"),
                    "verification": str(verification or ""),
                    "item_status": str(item.get("status") or ""),
                    "host": host,
                    "model": model,
                    "model_source": model_source,
                    "exit_code": att.get("exit_code"),
                    "run_start": run_start,
                }
                by_item_attempt[(id6, number)] = base
                started, ended = (
                    _iso_ts(att.get("started_at")),
                    _iso_ts(att.get("ended_at")),
                )
                main = _resolve_log(run_dir, att.get("log"))
                if main is not None:
                    claimed.add(main)
                st = stats_of.get(main) if main is not None else None
                if st is None and main is not None:
                    st = cache.get(main)
                row = _row_from_stats(
                    base,
                    st or _empty_stats(),
                    "main",
                    att.get("tokens"),
                    att.get("cost"),
                    started,
                    ended,
                )
                row["outcome"] = _outcome(str(disposition or ""), "main", verification)
                row["has_log"] = main is not None
                rows.append(row)
                vlog = _resolve_log(run_dir, att.get("verify_log"))
                if vlog is not None or isinstance(att.get("verify_tokens"), Mapping):
                    if vlog is not None:
                        claimed.add(vlog)
                    vst = stats_of.get(vlog) if vlog is not None else None
                    vrow = _row_from_stats(
                        base,
                        vst or _empty_stats(),
                        "verify",
                        att.get("verify_tokens"),
                        att.get("verify_cost"),
                        None,
                        None,
                    )
                    vrow["outcome"] = _outcome(None, "verify", att.get("verification"))
                    vrow["has_log"] = vlog is not None
                    rows.append(vrow)
        # Session files no attempt claimed (gate answers, defect re-asks, older layouts).
        for f in session_files:
            if f in claimed:
                continue
            m = _SESSION_NAME_RE.match(f.name)
            id6 = m.group("id6") if m else ""
            number = int(m.group("att")) if m else 1
            role = (
                "verify"
                if m and m.group("vpre")
                else ((m.group("role") if m else None) or "main")
            )
            base = by_item_attempt.get((id6, number))
            if base is None:
                base = {
                    "run": run_id,
                    "set": "",
                    "id6": id6,
                    "kind": "",
                    "action": "unknown",
                    "attempt": number,
                    "attempts_total": number,
                    "retry": number > 1,
                    "recovery": False,
                    "disposition": "(none)",
                    "verification": "",
                    "item_status": "",
                    "host": host,
                    "model": model,
                    "model_source": model_source,
                    "exit_code": None,
                    "run_start": run_start,
                }
            row = _row_from_stats(base, stats_of[f], role, None, None, None, None)
            row["outcome"] = (
                "unknown"
                if role not in ("main",)
                else _outcome(base.get("disposition"), "main", None)
            )
            row["has_log"] = True
            rows.append(row)
    cache.save(live)
    for r in rows:
        ts = r.get("start") or r.get("run_start")
        r["date"] = (
            _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).strftime("%Y-%m-%d")
            if ts
            else ""
        )
    info = {
        "runs": total,
        "runs_without_state": runs_without_state,
        "sessions": len(live),
        "cache_hits": cache.hits,
        "cache_misses": cache.misses,
    }
    return rows, info


# --- payload + render ------------------------------------------------------------------------------

#: The columns shipped to the browser, in order. ``tools`` (a per-row dict) is flattened into a
#: separate sparse table so the columnar arrays stay flat.
COLUMNS: tuple[str, ...] = (
    (
        "run",
        "set",
        "id6",
        "kind",
        "action",
        "role",
        "attempt",
        "attempts_total",
        "retry",
        "recovery",
        "disposition",
        "outcome",
        "verification",
        "item_status",
        "host",
        "model",
        "model_source",
        "date",
        "start",
        "wall",
        "cost",
        "input",
        "output",
        "reasoning",
        "cache_read",
        "cache_write",
        "fresh_tokens",
        "total_tokens",
        "steps",
        "tool_calls",
        "tool_errors",
        "tool_seconds",
        "files_read",
        "files_edited",
        "token_source",
        "has_log",
    )
    + tuple("t_" + c for c in CATEGORY_ORDER)
    + tuple(
        "sh_" + k for k in ("test", "git", "aw", "inspect", "python", "lint", "other")
    )
)


def build_payload(
    rows: Sequence[Mapping[str, Any]],
    info: Mapping[str, Any],
    *,
    generated_label: str = "",
    generated_at: str = "",
) -> dict[str, Any]:
    cols: dict[str, list[Any]] = {c: [] for c in COLUMNS}
    tool_names: list[str] = []
    tool_index: dict[str, int] = {}
    tools_sparse: list[list[int]] = []
    for r in rows:
        for c in COLUMNS:
            v = r.get(c)
            if isinstance(v, float):
                v = (
                    round(v, 6)
                    if c == "cost"
                    else (round(v, 3) if not v.is_integer() else int(v))
                )
            cols[c].append(v)
        sparse: list[int] = []
        errs = r.get("tool_err") or {}
        for name, n in sorted((r.get("tools") or {}).items()):
            if name not in tool_index:
                tool_index[name] = len(tool_names)
                tool_names.append(name)
            sparse.extend((tool_index[name], int(n), int(errs.get(name, 0))))
        tools_sparse.append(sparse)
    return {
        "schema": DASHBOARD_SCHEMA_VERSION,
        "generated_label": generated_label,
        "generated_at": generated_at,
        "info": dict(info),
        "n": len(rows),
        "columns": cols,
        "tool_names": tool_names,
        "tool_categories": {n: tool_category(n) for n in tool_names},
        "tools": tools_sparse,
    }


def _asset(name: str) -> str:
    return (Path(__file__).parent / ASSETS_DIRNAME / name).read_text(encoding="utf-8")


def render_dashboard(
    payload: Mapping[str, Any], *, title: str = "Run analytics"
) -> str:
    """The whole self-contained dashboard document. Refuses to return one with a network reference."""

    from agent_workflows import run_analytics_spa as spa

    data = spa.escape_json_for_script(
        json.dumps(payload, separators=(",", ":"), sort_keys=True)
    )
    doc = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="referrer" content="no-referrer">\n'
        f"<title>{spa.escape_text(title)}</title>\n"
        f"<style>{_asset('dashboard.css')}</style>\n</head>\n<body>\n"
        '<div id="app"><noscript>This dashboard needs JavaScript. The classic report is '
        '<a href="report.html">report.html</a>.</noscript></div>\n'
        f'<script type="application/json" id="dash-data">{data}</script>\n'
        f"<script>{_asset('dashboard.js')}</script>\n</body>\n</html>\n"
    )
    violations = spa.scan_for_network_references(doc)
    if violations:
        raise spa.SpaError(f"dashboard contains network references: {violations}")
    return doc
