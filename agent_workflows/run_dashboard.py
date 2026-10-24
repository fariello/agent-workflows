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

from agent_workflows import model_names
from agent_workflows.run_analytics_schema import resolve_attempt_model
from agent_workflows.runner_shared import canonical_terminal_status
from agent_workflows.verifier_corroboration import (
    AGY_TERMINAL_STATES,
    tool_call_from_event,
)

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

DASHBOARD_SCHEMA_VERSION = 9
ASSETS_DIRNAME = "run_dashboard_assets"
#: The browser assets the dashboard inlines; packaging tests assert each ships in wheel and sdist.
REQUIRED_ASSETS: tuple[str, ...] = ("dashboard.css", "dashboard.js")
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
    "subagent": "subagent",
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
    "invoke_subagent": "subagent",
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
        # Schema 7 (review-cost analysis): context size per model step, tool OUTPUT bytes, shell
        # command families, files read by path, and the host session id.
        "context_first": None,
        "context_last": None,
        "context_max": None,
        "tool_bytes": {},
        "tool_output_bytes": 0,
        "families": {},
        "read_counts": {},
        "host_session": None,
        # Schema 9: recorded cost apportioned PER STEP with the rate set that reproduces that step's
        # cost (reasoning at the output rate); `cost_split_steps` counts steps that matched one.
        "cost_input": 0.0,
        "cost_output": 0.0,
        "cost_reasoning": 0.0,
        "cost_cache_read": 0.0,
        "cost_split_steps": 0,
        "cost_unsplit_steps": 0,
        # Antigravity reports thinking INSIDE output_tokens; this counts the thinking part so the
        # visible output can be derived without counting thinking twice.
        "thinking_in_output": False,
    }


#: Leading words of a shell segment that are wrappers, not the command being run.
_SHELL_WRAPPERS = frozenset(
    {"sudo", "env", "time", "nice", "nohup", "command", "exec", "xargs"}
)
#: Programs whose FAMILY includes their subcommand, so `git log` and `git diff` stay distinct.
_SUBCOMMAND_PROGRAMS = frozenset(
    {
        "git",
        "gh",
        "make",
        "npm",
        "pnpm",
        "yarn",
        "uv",
        "pip",
        "pip3",
        "cargo",
        "go",
        "docker",
        "opencode",
    }
)
_HEREDOC_RE = re.compile(
    r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?[^\n]*\n.*?\n\s*\1\s*(?=\n|$)", re.S
)
_QUOTED_RE = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")
#: Shell keywords that start a compound command; the family is the command INSIDE it.
_SHELL_KEYWORDS = frozenset(
    {
        "for",
        "while",
        "until",
        "if",
        "then",
        "else",
        "elif",
        "fi",
        "do",
        "done",
        "case",
        "esac",
        "in",
        "function",
    }
)
_PROGRAM_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.+-]*$")


def _strip_shell_payload(command: str) -> str:
    """Remove heredoc BODIES and quoted strings, which are data rather than commands.

    A ``python3 - <<'EOF' ... EOF`` body would otherwise split into hundreds of "commands"
    (``import``, ``def``, ``print``) at every newline. The heredoc's own line is kept (its program
    is the command), and quoted text is replaced by a placeholder so separators inside quotes do
    not split the line.
    """

    text = _HEREDOC_RE.sub(lambda m: m.group(0).split("\n", 1)[0], command)
    return _QUOTED_RE.sub("Q", text)


_SEGMENT_SPLIT_RE = re.compile(r"\|\||&&|;|\||\n")
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def command_families(command: str) -> list[str]:
    """The command FAMILIES in one shell command line, one per pipeline/list segment.

    A family is the program's base name, plus its subcommand for multi-verb tools (``git log``,
    ``gh pr``) and up to two words for the aw CLI (``aw ipd lint``, also reached as
    ``python3 -m agent_workflows ipd lint``). ``python3 -m pytest`` is ``pytest``. Wrappers (``env``,
    ``sudo``, ``timeout N``, ``VAR=value``) and a leading ``cd <dir>`` segment are skipped, so the
    family names what actually ran. Arguments are never kept: no paths, no patterns, no text.
    """

    out: list[str] = []
    for segment in _SEGMENT_SPLIT_RE.split(_strip_shell_payload(command or "")):
        words = segment.strip().split()
        i = 0
        while i < len(words):
            w = words[i]
            if w in ("for", "case", "select") and i + 1 < len(words):
                # `for VAR in LIST`: the loop header is not a command; the body segment is.
                i = len(words)
                break
            if w == "[" or w == "[[" or w == "test":
                i = len(words)
                break
            if (
                _ENV_ASSIGN_RE.match(w)
                or w in _SHELL_WRAPPERS
                or w in _SHELL_KEYWORDS
                or w in ("(", "{", "!", "}", ")")
            ):
                i += 1
            elif w == "timeout":
                i += 2 if i + 1 < len(words) and not words[i + 1].startswith("-") else 1
            else:
                break
        words = [w.strip("()") for w in words[i:] if w.strip("()")]
        if not words:
            continue
        prog = words[0].rsplit("/", 1)[-1]
        if not _PROGRAM_RE.match(prog) or prog[0] == "-":
            continue
        if prog in ("cd", "pushd", "popd", "true", "echo", "printf", "export", "set"):
            if prog == "cd":
                continue
            out.append(prog)
            continue
        # Subcommand words are the LEADING non-flag words only, so a flag's value (`-m <message>`)
        # is never mistaken for a subcommand. `git -C <dir>` / `-c <k=v>` are skipped explicitly.
        tail = words[1:]
        if prog == "git":
            while len(tail) >= 2 and tail[0] in ("-C", "-c"):
                tail = tail[2:]
        rest = []
        for w in tail:
            if w.startswith("-"):
                break
            rest.append(w)
        if prog.startswith("python"):
            if len(words) > 2 and words[1] == "-m":
                mod = words[2]
                if mod == "agent_workflows":
                    prog, rest = "aw", []
                    for w in words[3:]:
                        if w.startswith("-"):
                            break
                        rest.append(w)
                else:
                    out.append(mod)
                    continue
            else:
                out.append("python")
                continue
        if prog in ("aw", "agent-workflows"):
            sub = [w for w in rest[:2] if re.match(r"^[a-z][a-z0-9-]*$", w)]
            out.append(" ".join(["aw"] + sub))
        elif (
            prog in _SUBCOMMAND_PROGRAMS
            and rest
            and re.match(r"^[a-z][a-z0-9-]*$", rest[0])
        ):
            out.append(prog + " " + rest[0])
        else:
            out.append(prog)
    return out


def _note_context(stats: dict[str, Any], context: float) -> None:
    """Record one model step's CONTEXT size: new input + cache read + cache write for that step."""

    if stats["context_first"] is None:
        stats["context_first"] = context
    stats["context_last"] = context
    if stats["context_max"] is None or context > stats["context_max"]:
        stats["context_max"] = context


def _apportion_step(
    stats: dict[str, Any],
    cost: float,
    inp: float,
    out: float,
    reasoning: float,
    cache_read: float,
) -> None:
    """Split ONE step's recorded cost by token kind, using the rate set that reproduces it."""

    from agent_workflows import run_analytics_pricing as pricing

    rate = pricing.matching_rate_set(
        input_tokens=inp,
        output_tokens=out,
        reasoning_tokens=reasoning,
        cache_read_tokens=cache_read,
        recorded_usd=cost,
    )
    if rate is None:
        stats["cost_unsplit_steps"] += 1
        return
    _label, r_in, r_out, r_cache = rate
    parts = {
        "cost_input": inp * r_in,
        "cost_output": out * r_out,
        "cost_reasoning": reasoning * r_out,
        "cost_cache_read": cache_read * r_cache,
    }
    total = sum(parts.values())
    if total <= 0:
        if cost == 0:
            stats["cost_split_steps"] += 1
        else:
            stats["cost_unsplit_steps"] += 1
        return
    for k, v in parts.items():
        # Scaled so the parts add up to the RECORDED cost exactly (they already match to ~1e-15).
        stats[k] += cost * v / total
    stats["cost_split_steps"] += 1


def _output_bytes(value: Any) -> int:
    if value is None:
        return 0
    if not isinstance(value, str):
        try:
            value = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            value = str(value)
    return len(value.encode("utf-8", errors="replace"))


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
    output_bytes: int = 0,
) -> None:
    stats["tool_calls"] += 1
    if output_bytes:
        _bump(stats["tool_bytes"], name or "?", output_bytes)
        stats["tool_output_bytes"] += output_bytes
    _bump(stats["tools"], name or "?")
    cat = tool_category(name)
    _bump(stats["categories"], cat)
    if error:
        stats["tool_errors"] += 1
        _bump(stats["tool_err"], name or "?")
    stats["tool_seconds"] += max(0.0, seconds)
    if cat == "shell" and command is not None:
        _bump(stats["commands"], command_kind(command))
        for fam in command_families(command):
            _bump(stats["families"], fam)
    if path:
        if cat == "read":
            read_paths.add(path)
            _bump(stats["read_counts"], path)
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
    if stats["host_session"] is None and obj.get("sessionID"):
        stats["host_session"] = str(obj.get("sessionID"))
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
                c_read, c_write = _num(cache.get("read")), _num(cache.get("write"))
            else:
                c_read, c_write = _num(cache), 0.0
            stats["cache_read"] += c_read
            stats["cache_write"] += c_write
            _note_context(stats, _num(toks.get("input")) + c_read + c_write)
            step_cost = part.get("cost")
            if isinstance(step_cost, (int, float)) and not isinstance(step_cost, bool):
                _apportion_step(
                    stats,
                    float(step_cost),
                    _num(toks.get("input")),
                    _num(toks.get("output")),
                    _num(toks.get("reasoning")),
                    c_read,
                )
        if isinstance(part.get("cost"), (int, float)) and not isinstance(
            part.get("cost"), bool
        ):
            stats["cost"] += float(part["cost"])
            stats["has_cost"] = True
    elif kind == "tool_use":
        tc = tool_call_from_event(obj)
        if tc is not None:
            st = part.get("state") if isinstance(part.get("state"), Mapping) else {}
            _record_tool(
                stats,
                tc.tool,
                error=tc.error,
                seconds=tc.seconds,
                command=tc.command,
                path=tc.path,
                read_paths=read_paths,
                edit_paths=edit_paths,
                output_bytes=_output_bytes(st.get("output"))
                + _output_bytes(st.get("error")),
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
    if stats["host_session"] is None:
        conv = obj.get("conversation_id") or (
            su.get("conversation_id") if isinstance(su, Mapping) else None
        )
        if conv:
            stats["host_session"] = str(conv)
    if not isinstance(su, Mapping):
        return
    state = su.get("state")
    stype = su.get("step_type")
    if state not in AGY_TERMINAL_STATES:
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
            # MEASURED (2026-10-17, 16,348 steps): Antigravity's `output_tokens` ALREADY INCLUDES
            # `thinking_tokens` (output >= thinking on every step, and total_tokens == input +
            # output exactly). So `output` here is the VISIBLE output, and thinking is counted
            # once, under `reasoning`. Adding both would count every thinking token twice.
            thinking = _num(usage.get("thinking_tokens"))
            stats["input"] += _num(usage.get("input_tokens"))
            stats["output"] += max(0.0, _num(usage.get("output_tokens")) - thinking)
            stats["reasoning"] += thinking
            stats["cache_read"] += _num(usage.get("cache_read_tokens"))
            stats["thinking_in_output"] = True
            _note_context(
                stats,
                _num(usage.get("input_tokens")) + _num(usage.get("cache_read_tokens")),
            )
    elif stype == "tool":
        tc = tool_call_from_event(obj)
        if tc is not None:
            info = (
                su.get("tool_info") if isinstance(su.get("tool_info"), Mapping) else {}
            )
            _record_tool(
                stats,
                tc.tool,
                error=tc.error,
                seconds=tc.seconds,
                command=tc.command,
                path=tc.path,
                read_paths=read_paths,
                edit_paths=edit_paths,
                output_bytes=_output_bytes(info.get("output")),
            )
    elif stype == "subagent":
        tc = tool_call_from_event(obj)
        if tc is not None:
            _record_tool(
                stats,
                tc.tool,
                error=tc.error,
                seconds=tc.seconds,
                command=tc.command,
                path=tc.path,
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
    r"^(?P<pos>\d+)-(?P<id6>[a-z0-9]{6})-(?:(?P<vpre>verify)-)?attempt-(?P<att>\d+)(?:-(?P<role>[a-z][a-z0-9-]*))?\.jsonl$"
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
    "fail-begin",
    "fail-lane",
    "dependency-blocked",
    "merge-needs-human",
}


#: Item END STATES for "how did the queue items finish": completed OK, ended in a failure state, or
#: never completed. Keyed on the queue item's final ``status`` (the runner's verdict for the item,
#: after every attempt), not on one attempt's disposition.
_ITEM_OK = frozenset({"executed", "reviewed", "approved", "already-landed", "retired"})
_ITEM_NOT_COMPLETED = frozenset(
    {"queued", "running", "not-run", "interrupted", "dependency-blocked", "fail-depend"}
)


def item_end_state(status: str | None) -> str:
    """``ok``, ``failed`` or ``not-completed`` for a queue item's final status.

    ``not-completed`` is an item the run never finished: still queued or running when the run ended,
    interrupted, not run, or blocked on an unmet dependency (it never got its turn). Every other
    terminal status that is not a clean success (``fail-*``, ``blocked``, ``partial``,
    ``substantially-complete``, merge refusals) is ``failed``: the item ran and ended in a fail state.
    """

    s = (status or "").strip()
    if s in _ITEM_OK:
        return "ok"
    if not s or s in _ITEM_NOT_COMPLETED:
        return "not-completed"
    return "failed"


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
    # aw: dead-status-token-exempt qvfd4l Raw token must be checked before canonicalization:
    # canonical_terminal_status("partial") is "fail-verify" and
    # canonical_terminal_status("substantially-complete") is "fail-gate", which would fold
    # both into "failed" (OQ-03, E-04).
    if d in ("substantially-complete", "partial"):
        return "partial"
    if d in _FAIL or canonical_terminal_status(d) in _FAIL:
        return "failed"
    return "unknown"


def _iso_ts(value: Any) -> float | None:
    if not value:
        return None
    try:
        return _dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _row_variant(
    att: Mapping[str, Any] | None, state: Mapping[str, Any], role: str, model: str
) -> str:
    """The effort VARIANT a session ran at, when recorded; ``""`` when it was not.

    Main turns: the host-reported ``host_model_variant``, then the attempt's ``variant``, then the
    run's ``options.variant``. Verifier turns: ``verify_variant`` (attempt, then options); the
    executor's variant is used only when the verifier ran the SAME model as the executor, because a
    verifier launched with its own profile may have run at a different effort.
    """

    a = att if isinstance(att, Mapping) else {}
    opts = state.get("options") if isinstance(state.get("options"), Mapping) else {}
    if str(role).strip().lower() == "verify":
        v = (
            a.get("verify_host_model_variant")
            or a.get("verify_variant")
            or opts.get("verify_variant")
        )
        if v:
            return str(v)
        exec_model = a.get("host_model") or a.get("model") or opts.get("model")
        if exec_model and str(exec_model) == model:
            return str(
                a.get("host_model_variant")
                or a.get("variant")
                or opts.get("variant")
                or ""
            )
        return ""
    return str(
        a.get("host_model_variant") or a.get("variant") or opts.get("variant") or ""
    )


def _run_model(state: Mapping[str, Any]) -> tuple[str, str]:
    model, source = resolve_attempt_model(None, state, role="main")
    return (
        _normalize_model(str(model)) if model else UNRECORDED,
        source if model else "",
    )


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
    if did:
        # Lazy import: importing runner_shared costs ~0.17-0.35s and run_dashboard
        # avoids module-level import weight (in-module precedent: _default_cache_path).
        from agent_workflows.runner_shared import host_labels_for_driver_id

        labels = host_labels_for_driver_id(did)
        if labels is not None and labels.argv_tokens:
            # argv_tokens[0] yields the short host token ("oc" / "agy") used by
            # this dashboard for grouping and interpolation, without hand-mapping.
            # The behavioral win is fall-through: an unregistered id falls through
            # to options / cost_attribution / formats rather than being misrouted by
            # prefix matching (e.g. octopus -> oc, agyx -> agy).
            return labels.argv_tokens[0]
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


def _agent_label(host: str, model: str) -> str:
    """The AGENT a row belongs to: which host ran which model, as one groupable label.

    A model id alone pools the same model across OpenCode and Antigravity, and a host alone pools
    every model a host ran; "agent" is the pair, which is what a maintainer means when comparing
    agents. An unrecorded model already carries its host (``(unrecorded, oc)``), so it is not
    repeated.
    """

    host = host or "unknown"
    model = model or UNRECORDED
    if model.startswith("(unrecorded"):
        return model
    return "{0} / {1}".format(host, model)


def split_cost(
    cost: float | None,
    *,
    input_tokens: float,
    output_tokens: float,
    cache_read_tokens: float,
    at: float | None,
    reasoning_tokens: float = 0.0,
) -> tuple[dict[str, float | None], str]:
    """Split a RECORDED session cost into input / output / reasoning / cache-read parts.

    THE FALLBACK. Sessions whose log carries per-step cost are split step by step in
    :func:`session_stats` with the rate set that reproduces each step exactly (method
    ``per-step``). This function is used only when the cost came from ``state.json`` (no usable
    log): it weights each kind by its tokens times the dated era's rate, reasoning at the output
    rate, and scales the parts to sum EXACTLY to the recorded cost (method ``apportioned``).

    NO RECORDED COST, NO SPLIT. A row without a recorded cost (every Antigravity row) returns
    ``None`` parts and method ``none`` rather than an estimate at another model's rates. Cache
    writes have no rate (measured zero in the corpus) and never receive a share.
    """

    empty: dict[str, float | None] = {
        "cost_input": None,
        "cost_output": None,
        "cost_reasoning": None,
        "cost_cache_read": None,
    }
    if cost is None or at is None:
        return empty, "none"
    from agent_workflows import run_analytics_pricing as pricing

    instant = _dt.datetime.fromtimestamp(at, _dt.timezone.utc)
    era = pricing.MEASURED_SCHEDULE.era_for(instant=instant)
    if era is None:
        return empty, "none"
    rates = era.rates
    weights = {
        "cost_input": max(0.0, input_tokens) * rates.input_per_mtok,
        "cost_output": max(0.0, output_tokens) * rates.output_per_mtok,
        "cost_reasoning": max(0.0, reasoning_tokens) * rates.output_per_mtok,
        "cost_cache_read": max(0.0, cache_read_tokens) * rates.cache_read_per_mtok,
    }
    total = sum(weights.values())
    if total <= 0:
        return empty, "none"
    return {k: cost * w / total for k, w in weights.items()}, "apportioned"


#: Width of one step-count bucket ("0-24", "25-49", ...). 25 is the width the review-cost
#: analysis asks for; past 200 steps every attempt shares one open-ended bucket.
STEP_BUCKET_WIDTH = 25
STEP_BUCKET_CAP = 200


def step_bucket(steps: Any) -> str:
    """The step-count bucket label for an attempt with ``steps`` model steps."""

    n = int(_num(steps))
    if n >= STEP_BUCKET_CAP:
        return "{0}+".format(STEP_BUCKET_CAP)
    lo = (n // STEP_BUCKET_WIDTH) * STEP_BUCKET_WIDTH
    return "{0:03d}-{1:03d}".format(lo, lo + STEP_BUCKET_WIDTH - 1)


#: Session roles that are corrective turns around an attempt rather than the attempt itself.
_RECOVERY_ROLES = frozenset(
    {"gate-answer", "defect-reask", "merge-conflict", "combined-red"}
)
_VERIFIER_ROLES = frozenset({"verify", "carrier-verification"})


def phase_of(action: str, role: str, recovery: bool) -> str:
    """The cost PHASE of one session row: review, execute, verifier or recovery (or the action).

    ``verifier`` is any verifier-family session; ``recovery`` is a recovery attempt or a corrective
    session around a turn (gate answer, defect re-ask, merge-conflict or combined-red repair, a
    review-orchestrator correction). Otherwise the queue action (``review``, ``execute``, ``plan``).
    """

    if role in _VERIFIER_ROLES:
        return "verifier"
    if (
        recovery
        or role in _RECOVERY_ROLES
        or role.startswith("review-orchestrator-correction")
        or action.endswith("-correction")
    ):
        return "recovery"
    return action or "unknown"


_PLUS_G_RE = re.compile(r"\+g([0-9a-f]{7,40})")


def _run_context(run_dir: Path, state: Mapping[str, Any]) -> dict[str, Any]:
    """Run-level labels: experiment label and variant, and the commit the run's code came from.

    ``code_commit`` is the toolkit commit, read from ``state.git.aw_version`` (recorded at run start
    from 2026-10-17) or else from the first telemetry event's ``tool_versions.agent_workflows``
    (``...+g<hash>``). ``repo_commit`` is the target repository's HEAD at run start, from
    ``state.git.commit`` or else the first attempt's ``starting_head``. Absent values stay empty and
    read ``(not recorded)`` in the dashboard; nothing is guessed.
    """

    opts = state.get("options") if isinstance(state.get("options"), Mapping) else {}
    git = state.get("git") if isinstance(state.get("git"), Mapping) else {}
    version = str(git.get("aw_version") or "")
    if not version:
        tel = run_dir / "telemetry"
        if tel.is_dir():
            for f in sorted(tel.glob("*.jsonl")):
                try:
                    with open(f, "r", encoding="utf-8", errors="replace") as handle:
                        first = handle.readline()
                    tv = json.loads(first).get("tool_versions") or {}
                    version = str(tv.get("agent_workflows") or "")
                except (OSError, ValueError, AttributeError):
                    version = ""
                if version:
                    break
    m = _PLUS_G_RE.search(version)
    repo_commit = str(git.get("commit") or "")
    if not repo_commit:
        for item in state.get("queue") or []:
            for att in (
                (item.get("attempts") or []) if isinstance(item, Mapping) else []
            ):
                if isinstance(att, Mapping) and att.get("starting_head"):
                    repo_commit = str(att["starting_head"])
                    break
            if repo_commit:
                break
    dirty = git.get("dirty")
    return {
        "label": str(opts.get("label") or ""),
        "review_variant": str(opts.get("review_variant") or ""),
        "code_commit": m.group(1)[:12] if m else "",
        "aw_version": version,
        "repo_commit": repo_commit[:12],
        "repo_dirty": "" if dirty is None else ("dirty" if dirty else "clean"),
    }


_WORKTREE_RE = re.compile(r"/\.aw/worktrees/[^/]+/")


def normalize_read_path(path: str, repo: Path | str | None) -> str:
    """A file path as a REPO-RELATIVE label, so the same file reads the same across worktrees.

    Runner turns execute inside ``.aw/worktrees/<lane>/``, so one repository file appears under many
    absolute prefixes; everything up to and including the lane directory is dropped. A path inside
    ``repo`` is made relative to it. A path outside both keeps only its last two components under an
    ``(outside)/`` prefix, so no home directory or machine path is carried into the analysis.
    """

    text = str(path or "").replace("\\", "/")
    m = _WORKTREE_RE.search(text)
    if m:
        return text[m.end() :]
    if repo is not None:
        root = str(Path(repo)).replace("\\", "/").rstrip("/") + "/"
        if text.startswith(root):
            return text[len(root) :]
    if not text.startswith("/") and not re.match(r"^[A-Za-z]:/", text):
        return text
    if repo is not None:
        # The same checkout reached through another mount or a symlinked home path: match on the
        # repository's directory NAME, so `/other/mount/<name>/x.py` reads as `x.py`.
        marker = "/" + Path(repo).name + "/"
        at = text.rfind(marker)
        if at >= 0 and Path(repo).name:
            return text[at + len(marker) :]
    tail = [p for p in text.split("/") if p][-2:]
    return "(outside)/" + "/".join(tail)


_RETRY_KEY_RE = re.compile(r"^(?P<id6>[a-z0-9]{6}):attempt-(?P<n>\d+)$")
_REFUSAL_EVENTS = (
    "ipd-finalize-refused",
    "ipd-begin-refused",
    "clean-base-refused",
    "ipd-reintegration-refused",
    "red-ci-refused",
)


def _redo_events(run_dir: Path) -> list[dict[str, Any]]:
    """The run's redo-relevant events: turn retries and begin/finalize/clean-base refusals."""

    out: list[dict[str, Any]] = []
    try:
        handle = open(run_dir / "events.jsonl", "r", encoding="utf-8", errors="replace")
    except OSError:
        return out
    with handle:
        for line in handle:
            if (
                '"ipd-turn-retry"' not in line
                and "-refused" not in line
                and '"review-orchestrator-correction"' not in line
            ):
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            name = ev.get("event") if isinstance(ev, Mapping) else None
            if (
                name in ("ipd-turn-retry", "review-orchestrator-correction")
                or name in _REFUSAL_EVENTS
            ):
                out.append(ev)
    return out


def _attach_redo_counts(
    rows: list[dict[str, Any]], events: Sequence[Mapping[str, Any]]
) -> None:
    """Count turn retries, refusals and re-asks onto each MAIN row (one per queue attempt).

    A turn retry names its attempt in ``idempotency_key`` (``<id6>:attempt-<n>``). Refusal events
    carry only ``id6`` and a time, so each goes to the latest attempt of that item that STARTED at or
    before the event (the attempt it interrupted); one before every attempt goes to the first.
    Re-asks are the attempt's own ``defect_reasked`` flag (or its separate defect re-ask session),
    plus each ``review-orchestrator-correction`` event, which re-asks a reviewer to redo its turn.
    """

    mains: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        r.setdefault("turn_retries", 0)
        r.setdefault("refusals", 0)
        r.setdefault("reasks", 0)
        if r.get("role") == "main":
            mains.setdefault(str(r.get("id6") or ""), []).append(r)
    for lst in mains.values():
        lst.sort(key=lambda r: (r.get("start") or 0, r.get("attempt") or 0))
    for r in rows:
        if r.get("role") == "defect-reask":
            for m in mains.get(str(r.get("id6") or ""), []):
                if m.get("attempt") == r.get("attempt"):
                    m["reasks"] += 1
                    break
    for ev in events:
        id6 = str(ev.get("id6") or "")
        cands = mains.get(id6) or []
        if not cands:
            continue
        if ev.get("event") == "review-orchestrator-correction":
            # A correction re-asks the reviewer to redo its turn; it names its attempt.
            n = ev.get("attempt")
            target = (
                next((c for c in cands if c.get("attempt") == n), None) or cands[-1]
            )
            target["reasks"] += 1
            continue
        if ev.get("event") == "ipd-turn-retry":
            mk = _RETRY_KEY_RE.match(str(ev.get("idempotency_key") or ""))
            n = int(mk.group("n")) if mk else None
            target = (
                next((c for c in cands if c.get("attempt") == n), None) or cands[-1]
            )
            target["turn_retries"] += 1
            continue
        at = _iso_ts(ev.get("at"))
        target = cands[0]
        if at is not None:
            for c in cands:
                if c.get("start") is not None and c["start"] <= at:
                    target = c
        target["refusals"] += 1
    for r in rows:
        r["redo_total"] = int(r["turn_retries"]) + int(r["refusals"]) + int(r["reasks"])


def _attach_session_origin(rows: list[dict[str, Any]]) -> None:
    """Mark each row's host session as new to the run, or already used, and by whom.

    ``new``: the first row in the run using that host session. ``reused``: the session was already
    used by an EARLIER row for a DIFFERENT queue item (the review sweep's shared session).
    ``continued``: already used only by an earlier row for the SAME item (a retry or a corrective
    session continuing its own turn). ``unknown``: the log carried no session id.
    """

    by_run: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_run.setdefault(str(r.get("run") or ""), []).append(r)
    for lst in by_run.values():
        lst.sort(
            key=lambda r: (
                float(r["start"]) if r.get("start") is not None else float("inf")
            )
        )
        seen: dict[str, set[str]] = {}
        for r in lst:
            sid = r.get("host_session")
            if not sid:
                r["session_origin"] = "unknown"
                continue
            users = seen.setdefault(str(sid), set())
            item = str(r.get("id6") or "")
            if not users:
                r["session_origin"] = "new"
            elif users - {item}:
                r["session_origin"] = "reused"
            else:
                r["session_origin"] = "continued"
            users.add(item)


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
        if base.get("host") == "agy":
            # Same measured fact as the log path: Antigravity output already contains thinking.
            out = max(0.0, out - rsn)
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
    if (
        source == "log"
        and stats.get("has_cost")
        and stats.get("cost_split_steps")
        and not stats.get("cost_unsplit_steps")
    ):
        parts: dict[str, float | None] = {
            k: float(stats.get(k) or 0.0)
            for k in ("cost_input", "cost_output", "cost_reasoning", "cost_cache_read")
        }
        split_method = "per-step"
    elif source == "log" and stats.get("cost_unsplit_steps"):
        # Some step's cost matches no known rate set (an unpriced model): do not guess a split.
        parts = {
            k: None
            for k in ("cost_input", "cost_output", "cost_reasoning", "cost_cache_read")
        }
        split_method = "none"
    else:
        parts, split_method = split_cost(
            cost,
            input_tokens=inp,
            output_tokens=out,
            reasoning_tokens=rsn,
            cache_read_tokens=cread,
            at=start if start is not None else base.get("run_start"),
        )
    row.update(parts)
    row.update(
        {
            "agent": _agent_label(
                str(base.get("host") or ""), str(base.get("model") or "")
            ),
            "cost_split": split_method,
            "input": inp,
            "output": out,
            "reasoning": rsn,
            "cache_read": cread,
            "cache_write": cwrite,
            # Thinking is generated output and is billed at the output rate, so it belongs in both
            # "in + out" and the total. OpenCode's own `total` is input + output + reasoning + cache
            # (measured on every step), and the Antigravity correction above keeps it single-counted.
            "fresh_tokens": inp + out + rsn,
            "total_tokens": inp + out + rsn + cread + cwrite,
            "cost": cost,
            "wall": wall,
            "start": start,
            "steps": stats.get("steps", 0),
            "tool_calls": stats.get("tool_calls", 0),
            "tool_errors": stats.get("tool_errors", 0),
            "tool_seconds": stats.get("tool_seconds", 0.0),
            # MODEL TIME: wall time not spent inside tools (the model generating, plus host and
            # network overhead between steps). The host logs no separate thinking time, so the
            # thinking share is an ESTIMATE: model time x thinking's share of generated tokens.
            "model_seconds": (
                max(0.0, wall - float(stats.get("tool_seconds") or 0.0))
                if wall is not None
                else None
            ),
            "thinking_seconds_est": (
                max(0.0, wall - float(stats.get("tool_seconds") or 0.0))
                * rsn
                / (rsn + out)
                if wall is not None and (rsn + out) > 0
                else None
            ),
            "files_read": stats.get("files_read", 0),
            "files_edited": stats.get("files_edited", 0),
            "token_source": source,
            "tools": dict(stats.get("tools") or {}),
            "tool_err": dict(stats.get("tool_err") or {}),
            # Schema 7: steps-and-context, tool output volume, command families, files read.
            "context_first": stats.get("context_first"),
            "context_last": stats.get("context_last"),
            "context_max": stats.get("context_max"),
            "step_bucket": step_bucket(stats.get("steps", 0))
            if stats.get("steps")
            else "0",
            "tool_output_bytes": int(stats.get("tool_output_bytes") or 0),
            "tool_bytes": dict(stats.get("tool_bytes") or {}),
            "families": dict(stats.get("families") or {}),
            "read_counts": dict(stats.get("read_counts") or {}),
            "host_session": stats.get("host_session"),
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
    name_overrides = model_names.load_overrides(repo)
    # display name -> (raw model id, variant), so each row also carries the exact recorded id.
    ids: dict[str, tuple[str, str]] = {}
    rows: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
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
        host = _run_host(state, (s.get("format") for s in stats_of.values()))

        def _row_model(
            att_map: Mapping[str, Any] | None, r_role: str
        ) -> tuple[str, str]:
            raw_m, m_src = resolve_attempt_model(att_map, state, role=r_role)
            if not raw_m:
                # Per host, so an unknown OpenCode model never pools with an unknown Antigravity one.
                return "(unrecorded, {0})".format(host), m_src
            variant = _row_variant(att_map, state, r_role, str(raw_m))
            name = model_names.display_name(
                str(raw_m), variant, overrides=name_overrides
            )
            ids[name] = (str(raw_m), variant)
            return name, m_src

        run_id = str(state.get("run_id") or run_dir.name)
        run_start = _iso_ts(state.get("created_at"))
        run_ctx = _run_context(run_dir, state)
        first_row = len(rows)
        queue = state.get("queue") if isinstance(state.get("queue"), list) else []
        # One record per QUEUE ITEM, including items that never got an attempt (and so have no
        # session row): those are exactly the items a run did not complete.
        run_date = (
            _dt.datetime.fromtimestamp(run_start, _dt.timezone.utc).strftime("%Y-%m-%d")
            if run_start
            else ""
        )
        for item in queue:
            if not isinstance(item, Mapping):
                continue
            n_att = len(
                [
                    a
                    for a in (item.get("attempts") or [])
                    if isinstance(a, Mapping) and a.get("number")
                ]
            )
            items.append(
                {
                    "run": run_id,
                    "id6": str(item.get("id6") or ""),
                    "set": str(item.get("setid") or ""),
                    "action": str(item.get("action") or "execute"),
                    "status": str(item.get("status") or ""),
                    "end": item_end_state(item.get("status")),
                    "attempts": n_att,
                    "host": host,
                    "date": run_date,
                }
            )
        by_item_attempt: dict[tuple[str, int], dict[str, Any]] = {}
        by_item_attempt_att: dict[tuple[str, int], Mapping[str, Any]] = {}
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
                main_model, main_model_source = _row_model(att, "main")
                if "review_readiness" in att:
                    raw_rr = att.get("review_readiness")
                    att_readiness = (
                        raw_rr if (isinstance(raw_rr, str) and raw_rr) else "absent"
                    )
                else:
                    att_readiness = ""
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
                    "readiness": att_readiness,
                    "item_status": str(item.get("status") or ""),
                    "item_end": item_end_state(item.get("status")),
                    "host": host,
                    "model": main_model,
                    "model_source": main_model_source,
                    "exit_code": att.get("exit_code"),
                    "run_start": run_start,
                    "defect_reasked": bool(att.get("defect_reasked")),
                    **run_ctx,
                }
                by_item_attempt[(id6, number)] = base
                by_item_attempt_att[(id6, number)] = att
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
                    v_model, v_model_source = _row_model(att, "verify")
                    v_base = dict(base)
                    v_base["model"] = v_model
                    v_base["model_source"] = v_model_source
                    vrow = _row_from_stats(
                        v_base,
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
                # Genuinely synthesized base (no attempt record was found);
                # legitimately keeps the run-level value.
                synth_model, synth_source = _row_model(None, role)
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
                    "readiness": "",
                    "item_status": "",
                    "item_end": "not-completed",
                    "host": host,
                    "model": synth_model,
                    "model_source": synth_source,
                    "exit_code": None,
                    "run_start": run_start,
                    "defect_reasked": False,
                    **run_ctx,
                }
            else:
                base = dict(base)
                # When an attempt record exists, resolve per row using that attempt
                # and its filename-derived role (which may be "verify").
                att = by_item_attempt_att.get((id6, number))
                unclaimed_model, unclaimed_source = _row_model(att, role)
                base["model"] = unclaimed_model
                base["model_source"] = unclaimed_source
            row = _row_from_stats(base, stats_of[f], role, None, None, None, None)
            row["outcome"] = (
                "unknown"
                if role not in ("main",)
                else _outcome(base.get("disposition"), "main", None)
            )
            row["has_log"] = True
            rows.append(row)
        run_rows = rows[first_row:]
        for r in run_rows:
            if r.get("read_counts"):
                norm: dict[str, int] = {}
                for k, v in r["read_counts"].items():
                    nk = normalize_read_path(k, repo)
                    norm[nk] = norm.get(nk, 0) + int(v)
                r["read_counts"] = norm
            r["phase"] = phase_of(
                str(r.get("action") or ""),
                str(r.get("role") or ""),
                bool(r.get("recovery")),
            )
        _attach_redo_counts(run_rows, _redo_events(run_dir))
        for r in run_rows:
            if r.get("role") == "main" and r.get("defect_reasked") and not r["reasks"]:
                r["reasks"] = 1
                r["redo_total"] += 1
        _attach_session_origin(run_rows)
    cache.save(live)
    for r in rows:
        raw_id, variant = ids.get(str(r.get("model") or ""), ("", ""))
        r["model_id"] = raw_id
        r["model_variant"] = variant
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
        "items": items,
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
        "readiness",
        "item_status",
        "item_end",
        "host",
        "model",
        "model_id",
        "model_variant",
        "model_source",
        "agent",
        "phase",
        "label",
        "review_variant",
        "code_commit",
        "repo_commit",
        "repo_dirty",
        "session_origin",
        "step_bucket",
        "context_first",
        "context_last",
        "context_max",
        "tool_output_bytes",
        "turn_retries",
        "refusals",
        "reasks",
        "redo_total",
        "date",
        "start",
        "wall",
        "cost",
        "cost_input",
        "cost_output",
        "cost_reasoning",
        "cost_cache_read",
        "cost_split",
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
        "model_seconds",
        "thinking_seconds_est",
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
    # Per-row name->count maps shipped as [name_index, value, ...] against one name table each.
    sparse_maps: dict[str, tuple[list[str], dict[str, int], list[list[Any]]]] = {
        k: ([], {}, []) for k in ("tool_bytes", "families", "read_counts")
    }
    for r in rows:
        for c in COLUMNS:
            v = r.get(c)
            if isinstance(v, float):
                v = (
                    round(v, 6)
                    if c.startswith("cost")
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
        for key, store in sparse_maps.items():
            names, index, out = store
            row_sparse: list[Any] = []
            for name, n in sorted((r.get(key) or {}).items()):
                if name not in index:
                    index[name] = len(names)
                    names.append(name)
                row_sparse.extend((index[name], int(n)))
            out.append(row_sparse)
    item_list = list(info.get("items") or [])
    item_cols = (
        "run",
        "id6",
        "set",
        "action",
        "status",
        "end",
        "attempts",
        "host",
        "date",
    )
    return {
        "schema": DASHBOARD_SCHEMA_VERSION,
        "generated_label": generated_label,
        "generated_at": generated_at,
        "info": {k: v for k, v in info.items() if k != "items"},
        "items": {c: [it.get(c) for it in item_list] for c in item_cols},
        "n": len(rows),
        "columns": cols,
        "tool_names": tool_names,
        "tool_categories": {n: tool_category(n) for n in tool_names},
        "tools": tools_sparse,
        "maps": {
            k: {"names": names, "rows": out}
            for k, (names, _i, out) in sparse_maps.items()
        },
    }


#: The per-session columns persisted to the bundle's ``attempts.jsonl`` for ``aw runs query``.
ATTEMPT_FACT_FIELDS: tuple[str, ...] = (
    "run",
    "set",
    "id6",
    "kind",
    "action",
    "role",
    "phase",
    "attempt",
    "attempts_total",
    "recovery",
    "disposition",
    "outcome",
    "verification",
    "readiness",
    "item_status",
    "item_end",
    "host",
    "model",
    "model_id",
    "model_variant",
    "model_source",
    "agent",
    "label",
    "review_variant",
    "code_commit",
    "aw_version",
    "repo_commit",
    "repo_dirty",
    "host_session",
    "session_origin",
    "step_bucket",
    "date",
    "start",
    "wall",
    "cost",
    "cost_input",
    "cost_output",
    "cost_reasoning",
    "cost_cache_read",
    "cost_split",
    "input",
    "output",
    "reasoning",
    "cache_read",
    "cache_write",
    "fresh_tokens",
    "total_tokens",
    "steps",
    "context_first",
    "context_last",
    "context_max",
    "tool_calls",
    "tool_errors",
    "tool_output_bytes",
    "tool_seconds",
    "model_seconds",
    "thinking_seconds_est",
    "files_read",
    "files_edited",
    "turn_retries",
    "refusals",
    "reasks",
    "redo_total",
    "token_source",
    "has_log",
)
ATTEMPT_FACT_MAPS: tuple[str, ...] = ("tools", "tool_bytes", "families", "read_counts")
ATTEMPT_FACTS_FILENAME = "attempts.jsonl"
ATTEMPT_FACTS_SCHEMA_VERSION = 3


def attempt_facts_jsonl(
    rows: Sequence[Mapping[str, Any]], info: Mapping[str, Any]
) -> str:
    """The session/attempt-grain facts as JSONL: one header line, then one line per session row.

    The header carries the schema version and the sweep's ``info`` (run count and any date window)
    so a reader can say what population it is answering about.
    """

    lines = [
        json.dumps(
            {
                "record": "header",
                "schema": ATTEMPT_FACTS_SCHEMA_VERSION,
                "info": {k: v for k, v in info.items() if k != "items"},
            },
            sort_keys=True,
        )
    ]
    for r in rows:
        out: dict[str, Any] = {"record": "row"}
        for k in ATTEMPT_FACT_FIELDS:
            v = r.get(k)
            if isinstance(v, float):
                v = (
                    round(v, 6)
                    if k.startswith("cost")
                    else (int(v) if v.is_integer() else round(v, 3))
                )
            out[k] = v
        for k in ATTEMPT_FACT_MAPS:
            out[k] = {name: int(n) for name, n in sorted((r.get(k) or {}).items())}
        if r.get("model_source") in (None, ""):
            out["model_source"] = "none"
        lines.append(json.dumps(out, sort_keys=True, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def _asset(name: str) -> str:
    return (Path(__file__).parent / ASSETS_DIRNAME / name).read_text(encoding="utf-8")


def render_dashboard(
    payload: Mapping[str, Any], *, title: str = "Run analytics"
) -> str:
    """The whole self-contained dashboard document. Refuses to return one with a network reference."""

    from agent_workflows import run_analytics_html as spa

    data = spa.escape_json_for_script(
        json.dumps(payload, separators=(",", ":"), sort_keys=True)
    )
    doc = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="referrer" content="no-referrer">\n'
        f"<title>{spa.escape_text(title)}</title>\n"
        f"<style>{_asset('dashboard.css')}</style>\n</head>\n<body>\n"
        '<div id="app"><noscript>This dashboard needs JavaScript. The same data is available '
        'without it through <code>aw runs query</code>.</noscript></div>\n'
        f'<script type="application/json" id="dash-data">{data}</script>\n'
        f"<script>{_asset('dashboard.js')}</script>\n</body>\n</html>\n"
    )
    violations = spa.scan_for_network_references(doc)
    if violations:
        raise spa.HtmlSafetyError(
            f"dashboard contains network references: {violations}"
        )
    return doc
