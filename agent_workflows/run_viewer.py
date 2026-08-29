"""Run viewer for inspecting and summarizing driver runs (aw oc/agy run records).

Read-only inspection tool for `.aw/records/runs/run-*` directories that displays
the ending state of each IPD step in similar unified format to `aw att` and `aw ipd lint`.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_workflows.attention import _TREE_COLOR_256, _identity_stem
from agent_workflows.render_stream import format_tokens
from agent_workflows.term import Term, strip_ansi


# runstale Order 01 (ssk6nf) E-01/E-03: the DISPLAY-ONLY status a `running` step is projected to when
# no live driver holds its run. Deliberately NOT the bare word `interrupted`: a persisted `interrupted`
# is a fact `oc_runipd.reconcile_interrupted` recorded after resolving the plan, whereas this is an
# inference from "nobody holds the lock" that has inspected nothing. Collapsing the two would let the
# viewer assert a reconciliation that never happened.
ABANDONED = "abandoned?"

# Liveness of the driver that owns a run directory.
HOLDER_LIVE = "live"
HOLDER_NONE = "none"
HOLDER_UNKNOWN = "unknown"


def driver_holder_state(run_dir: Path) -> str:
    """Is a LIVE driver holding ``run_dir``? Read-only; never writes, never unlinks.

    Returns ``HOLDER_LIVE`` / ``HOLDER_NONE`` / ``HOLDER_UNKNOWN``.

    Uses ``flock(LOCK_EX|LOCK_NB)`` acquirability rather than the ``pid=`` recorded inside
    ``driver.lock``, for two measured reasons: the OS releases an ``flock`` when its holder dies (so
    acquirability is authoritative), and a recorded PID can be REUSED by an unrelated process (so a
    ``kill(pid, 0)`` probe can report a live driver that is really something else). A missing lock file
    means no holder. Anything we cannot determine (no ``fcntl`` on this platform, or any OSError) is
    ``HOLDER_UNKNOWN``, never ``HOLDER_NONE``: failing to prove a driver is alive is not proof it is
    dead, and only a proven-dead run may be projected (ssk6nf E-01).
    """
    lock_path = Path(run_dir) / "driver.lock"
    if not lock_path.is_file():
        return HOLDER_NONE
    try:
        import fcntl
    except ImportError:  # pragma: no cover - POSIX-only primitive
        return HOLDER_UNKNOWN
    try:
        with lock_path.open("a+") as handle:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return HOLDER_LIVE
            # Acquired, so nothing else holds it. Release immediately and leave the file in place.
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return HOLDER_NONE
    except OSError:
        return HOLDER_UNKNOWN


@dataclass
class StepSummary:
    position: int
    id6: str
    setid: str
    action: str
    status: str
    configured_file: str
    stem: str
    verification_status: str | None = None
    attempts_count: int = 0
    session_id: str | None = None
    disposition: str | None = None
    summary: str | None = None
    incomplete_requirements: list[str] = field(default_factory=list)
    # ssk6nf E-02: the status as PERSISTED, kept whenever `status` is a projection so a caller can
    # still see what the driver actually recorded. None means `status` is the recorded value.
    persisted_status: str | None = None
    cost: float | None = None
    tokens: dict[str, int] = field(default_factory=dict)

    @property
    def is_projected(self) -> bool:
        """True when ``status`` was derived from driver liveness rather than read from state."""
        return self.persisted_status is not None


@dataclass
class RunSummary:
    run_id: str
    run_dir: Path
    created_at: str | None = None
    updated_at: str | None = None
    driver: str | None = None
    selectors: list[str] = field(default_factory=list)
    setids: list[str] = field(default_factory=list)
    steps: list[StepSummary] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    total_cost: float | None = None
    total_tokens: dict[str, int] = field(default_factory=dict)
    pid: int | None = None
    pid_state: str | None = None
    is_live: bool = False
    runtime_seconds: float | None = None
    runtime_str: str | None = None

    @property
    def timestamp_dt(self) -> datetime | None:
        """Parse the run's effective datetime in UTC."""
        for ts_str in (
            self.created_at,
            self.updated_at,
            self.run_id,
            self.run_dir.name,
        ):
            if not ts_str:
                continue
            cleaned = ts_str.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(cleaned)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (ValueError, TypeError):
                pass
            m = re.search(r"(\d{8})T(\d{6})", ts_str)
            if m:
                try:
                    return datetime.strptime(
                        f"{m.group(1)}T{m.group(2)}", "%Y%m%dT%H%M%S"
                    ).replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass
        return None


def format_duration(seconds: float | None) -> str:
    """Format duration seconds into a human-readable string (e.g. '12.4s', '4m 12s', '1h 04m 12s')."""
    if seconds is None or seconds < 0:
        return "0s"
    if seconds < 60:
        return f"{seconds:.1f}s" if seconds < 10 else f"{int(seconds)}s"
    mins = int(seconds // 60)
    rem_secs = int(seconds % 60)
    if mins < 60:
        return f"{mins}m {rem_secs:02d}s"
    hrs = int(mins // 60)
    rem_mins = int(mins % 60)
    return f"{hrs}h {rem_mins:02d}m {rem_secs:02d}s"


def inspect_run_pid_and_runtime(
    run_dir: Path,
    created_at: str | None,
    updated_at: str | None,
    timestamp_dt: datetime | None,
) -> tuple[int | None, str | None, bool, float | None, str | None]:
    """Inspect PID liveness, process state, and elapsed runtime for a run."""
    holder = driver_holder_state(run_dir)
    pid: int | None = None
    lock_p = run_dir / "driver.lock"
    if lock_p.is_file():
        try:
            m = re.search(
                r"pid=(\d+)",
                lock_p.read_text(encoding="utf-8", errors="ignore"),
            )
            if m:
                pid = int(m.group(1))
        except OSError:
            pass
    if pid is None:
        m = re.search(r"-(\d+)$", run_dir.name)
        if m:
            try:
                pid = int(m.group(1))
            except ValueError:
                pass

    proc_state = None
    if pid is not None:
        proc_file = Path(f"/proc/{pid}/status")
        if proc_file.is_file():
            try:
                for line in proc_file.read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines():
                    if line.startswith("State:"):
                        proc_state = line.split(":", 1)[1].strip()
            except OSError:
                pass

    if holder == HOLDER_LIVE:
        is_live = True
        pid_state = f"live: {proc_state}" if proc_state else "live"
    elif holder == HOLDER_NONE:
        is_live = False
        pid_state = "exited"
    else:
        if proc_state:
            is_live = True
            pid_state = f"live: {proc_state}"
        else:
            is_live = False
            pid_state = "exited"

    # Runtime calculation
    start_dt = timestamp_dt
    end_dt = None
    if is_live:
        end_dt = datetime.now(timezone.utc)
    else:
        if updated_at:
            try:
                cleaned = updated_at.replace("Z", "+00:00")
                end_dt = datetime.fromisoformat(cleaned)
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        if not end_dt and (run_dir / "state.json").is_file():
            try:
                st = (run_dir / "state.json").stat()
                end_dt = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
            except OSError:
                pass

    runtime_seconds = None
    runtime_str = None
    if start_dt and end_dt:
        runtime_seconds = max(0.0, (end_dt - start_dt).total_seconds())
        runtime_str = format_duration(runtime_seconds)

    return pid, pid_state, is_live, runtime_seconds, runtime_str


def parse_since_timestamp(spec: str, now: datetime | None = None) -> datetime:
    """Parse a date, timestamp, or relative timespec into an aware UTC datetime.

    Supports:
      - Relative timespecs with floats: e.g. '1d', '0.5d', '2h', '1.5h', '1w', '2.5w', '1m', '0.5m', '1y'
      - Dates: 'YYYY-MM-DD', 'YYYYMMDD', 'YYYY/MM/DD'
      - Timestamps: 'YYYY-MM-DDTHH:MM:SS', 'YYYY-MM-DD HH:MM:SS', 'YYYYMMDDTHHMMSSZ'
    """
    ref_now = now or datetime.now(timezone.utc)
    s = spec.strip()

    # Relative timespec with unit: e.g. 1d, 1.5w, 2h, 0.5m, 1y
    m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)$", s)
    if m:
        val = float(m.group(1))
        unit = m.group(2).lower()
        if unit in ("h", "hr", "hrs", "hour", "hours"):
            delta = timedelta(hours=val)
        elif unit in ("d", "day", "days"):
            delta = timedelta(days=val)
        elif unit in ("w", "wk", "wks", "week", "weeks"):
            delta = timedelta(days=val * 7)
        elif unit in ("m", "mo", "mon", "month", "months"):
            delta = timedelta(days=val * 30.4375)
        elif unit in ("y", "yr", "yrs", "year", "years"):
            delta = timedelta(days=val * 365.25)
        elif unit in ("min", "mins", "minute", "minutes"):
            delta = timedelta(minutes=val)
        elif unit in ("s", "sec", "secs", "second", "seconds"):
            delta = timedelta(seconds=val)
        else:
            raise ValueError(f"unknown timespec unit '{unit}' (expected h, d, w, m, y)")
        return ref_now - delta

    # Date without delimiters: YYYYMMDD
    if re.match(r"^\d{8}$", s):
        return datetime.strptime(s, "%Y%m%d").replace(tzinfo=timezone.utc)

    # Clean ISO format
    cleaned = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        pass

    # Common date / timestamp patterns
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass

    # Run directory / id pattern: e.g. 20260827T212958
    m_run = re.search(r"(\d{8})T(\d{6})", s)
    if m_run:
        try:
            return datetime.strptime(
                f"{m_run.group(1)}T{m_run.group(2)}", "%Y%m%dT%H%M%S"
            ).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass

    raise ValueError(f"invalid date, timestamp, or timespec '{spec}'")


def resolve_since_timestamp(
    spec: str, repo_root: Path = Path("."), now: datetime | None = None
) -> datetime:
    """Resolve a date, timestamp, timespec, or run ID/dir to an aware UTC datetime."""
    s = spec.strip()
    matched = resolve_target_runs([s], repo_root)
    if matched:
        summary = load_run_summary(matched[0], repo_root)
        if summary and summary.timestamp_dt:
            return summary.timestamp_dt
    return parse_since_timestamp(s, now=now)


def _find_stem_for_id6(repo_root: Path, id6: str) -> str | None:
    """Find the plan file stem for a given id6 across pending and executed plans."""
    for base_rel in (
        Path(".aw/records/plans/pending"),
        Path(".aw/records/plans/executed"),
        Path(".aw/records/plans/reusable"),
        Path(".agents/plans/pending"),
        Path(".agents/plans/executed"),
    ):
        base = repo_root / base_rel
        if base.is_dir():
            for p in base.glob("*.md"):
                if id6 in p.name:
                    return _identity_stem(str(p))
    return None


_STATUS_LINE_RE = re.compile(r"(?m)^- Status:\s*(\S+)\s*$")


@dataclass
class StepArtifactAudit:
    step_id6: str
    stem: str
    run_status: str
    missing_entirely: bool = False
    location_mismatch: bool = False
    status_mismatch: bool = False
    actual_dir: str | None = None
    expected_dir: str | None = None
    file_status: str | None = None
    actual_path: Path | None = None


def find_artifact_file(repo_root: Path, id6: str, stem: str) -> Path | None:
    """Search the repository for an artifact markdown file matching id6 or stem."""
    if not id6 and not stem:
        return None
    search_dirs = [
        repo_root / ".aw" / "records" / "plans" / "pending",
        repo_root / ".aw" / "records" / "plans" / "executed",
        repo_root / ".aw" / "records" / "plans" / "superseded",
        repo_root / ".aw" / "records" / "plans" / "not-executed",
        repo_root / ".aw" / "records" / "plans" / "reusable",
        repo_root / ".aw" / "records" / "plans" / "archive",
        repo_root / ".aw" / "records" / "specs",
        repo_root / ".agents" / "plans" / "pending",
        repo_root / ".agents" / "plans" / "executed",
    ]
    for d in search_dirs:
        if not d.is_dir():
            continue
        for p in d.rglob("*.md"):
            if id6 and id6 in p.name:
                return p
            if stem and stem in p.name:
                return p
    return None


def audit_step_artifact(
    step: StepSummary, repo_root: Path = Path(".")
) -> StepArtifactAudit:
    """Audit a step's artifact location and status on disk."""
    id6 = step.id6
    stem = step.stem or (f"{step.setid}-{step.id6}" if step.setid else step.id6)
    cfg = step.configured_file
    st = "complete" if step.status == "substantially-complete" else step.status

    if st in ("executed", "complete"):
        expected_dir_name = "executed"
    elif st == "superseded":
        expected_dir_name = "superseded"
    elif st == "not-executed":
        expected_dir_name = "not-executed"
    elif st == "reusable":
        expected_dir_name = "reusable"
    else:
        expected_dir_name = "pending"

    actual_file = None
    if cfg and (repo_root / cfg).is_file():
        actual_file = repo_root / cfg
    else:
        actual_file = find_artifact_file(repo_root, id6, stem)

    if actual_file is None:
        return StepArtifactAudit(
            step_id6=id6,
            stem=stem,
            run_status=st,
            missing_entirely=True,
            location_mismatch=False,
            status_mismatch=False,
            actual_dir=None,
            expected_dir=expected_dir_name,
            file_status=None,
            actual_path=None,
        )

    actual_dir_name = actual_file.parent.name
    loc_mismatch = actual_dir_name != expected_dir_name

    file_status = None
    status_mismatch = False
    try:
        txt = actual_file.read_text(encoding="utf-8", errors="ignore")
        m = _STATUS_LINE_RE.search(txt)
        if m:
            file_status = m.group(1).strip()
            f_norm = (
                "complete" if file_status == "substantially-complete" else file_status
            )
            if st in ("executed", "complete"):
                if f_norm not in ("executed", "complete"):
                    status_mismatch = True
            elif st == "reviewed":
                if f_norm not in ("reviewed", "approved"):
                    status_mismatch = True
            elif st in ("queued", "running", "dependency-blocked", "blocked"):
                if f_norm not in (
                    "approved",
                    "to-review",
                    "draft",
                    "reviewed",
                    "queued",
                    "running",
                ):
                    status_mismatch = True
            else:
                if f_norm != st:
                    status_mismatch = True
    except Exception:
        pass

    return StepArtifactAudit(
        step_id6=id6,
        stem=stem,
        run_status=st,
        missing_entirely=False,
        location_mismatch=loc_mismatch,
        status_mismatch=status_mismatch,
        actual_dir=actual_dir_name,
        expected_dir=expected_dir_name,
        file_status=file_status,
        actual_path=actual_file,
    )


def format_artifact_audit_summary(
    audits: list[StepArtifactAudit],
    term: Term,
) -> str:
    """Format a summary of artifact location and status discrepancies."""
    seen: set[str] = set()
    discrepancies: list[StepArtifactAudit] = []
    for a in audits:
        key = a.step_id6 or a.stem
        if key in seen:
            continue
        seen.add(key)
        if a.missing_entirely or a.location_mismatch or a.status_mismatch:
            discrepancies.append(a)

    if not discrepancies:
        return ""

    cnt = len(discrepancies)
    header = (
        term.colorize(
            f"--- Artifact & Status Discrepancies ({cnt} item{'s' if cnt != 1 else ''}) ---",
            "bold",
        )
        if getattr(term, "color", False)
        else f"--- Artifact & Status Discrepancies ({cnt} item{'s' if cnt != 1 else ''}) ---"
    )
    lines = [header]

    for a in discrepancies:
        item_id = a.stem or a.step_id6
        if a.missing_entirely:
            tag = (
                term.color256("!", 196, bold=True)
                if getattr(term, "color", False)
                else "!"
            )
            msg = (
                term.color256(
                    "MISSING ENTIRELY (no artifact file found in repository)",
                    196,
                    bold=True,
                )
                if getattr(term, "color", False)
                else "MISSING ENTIRELY (no artifact file found in repository)"
            )
            lines.append(f"  {tag} {item_id}: {msg}")
        else:
            tag = (
                term.color256("*", 214, bold=True)
                if getattr(term, "color", False)
                else "*"
            )
            parts = []
            if a.location_mismatch and a.actual_dir and a.expected_dir:
                parts.append(
                    f"location: in {a.actual_dir}/ (expected {a.expected_dir}/)"
                )
            if a.status_mismatch and a.file_status:
                parts.append(f"status: file '{a.file_status}' != run '{a.run_status}'")
            desc = ", ".join(parts) if parts else "discrepancy detected"
            lines.append(f"  {tag} {item_id}: {desc}")

    return "\n".join(lines)


def extract_log_metrics(log_path: Path | str) -> tuple[float | None, dict[str, int]]:
    """Extract cumulative cost and token counts from a session JSONL file."""
    p = Path(log_path)
    if not p.is_file():
        return None, {}
    total_cost = 0.0
    has_cost = False
    tokens_agg = {"total": 0, "input": 0, "output": 0, "cache": 0, "reasoning": 0}
    has_tokens = False
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if not isinstance(ev, dict):
                    continue
                if ev.get("type") == "step_finish":
                    part = ev.get("part") or {}
                    c = part.get("cost")
                    if c is not None:
                        try:
                            total_cost += float(c)
                            has_cost = True
                        except (ValueError, TypeError):
                            pass
                    toks = part.get("tokens") or {}
                    if isinstance(toks, dict):
                        has_tokens = True
                        inp = toks.get("input") or 0
                        out = toks.get("output") or 0
                        reasoning = toks.get("reasoning") or 0
                        cache_raw = toks.get("cache") or 0
                        if isinstance(cache_raw, dict):
                            cache_val = (cache_raw.get("read") or 0) + (
                                cache_raw.get("write") or 0
                            )
                        elif isinstance(cache_raw, (int, float)):
                            cache_val = int(cache_raw)
                        else:
                            cache_val = 0
                        tot = toks.get("total")
                        if tot is None:
                            tot = inp + out + cache_val
                        tokens_agg["total"] += int(tot)
                        tokens_agg["input"] += int(inp)
                        tokens_agg["output"] += int(out)
                        tokens_agg["cache"] += int(cache_val)
                        tokens_agg["reasoning"] += int(reasoning)
                elif ev.get("type") == "agent_response" or "usage" in ev:
                    usage = ev.get("usage") or {}
                    if isinstance(usage, dict):
                        has_tokens = True
                        tot = usage.get("total_tokens") or 0
                        inp = (
                            usage.get("prompt_tokens") or usage.get("input_tokens") or 0
                        )
                        out = (
                            usage.get("completion_tokens")
                            or usage.get("output_tokens")
                            or 0
                        )
                        tokens_agg["total"] += int(tot)
                        tokens_agg["input"] += int(inp)
                        tokens_agg["output"] += int(out)
                    c = ev.get("cost")
                    if c is not None:
                        try:
                            total_cost += float(c)
                            has_cost = True
                        except (ValueError, TypeError):
                            pass
    except Exception:
        pass

    cost_res = round(total_cost, 4) if has_cost else None
    tok_res = {k: v for k, v in tokens_agg.items() if v > 0} if has_tokens else {}
    return cost_res, tok_res


def extract_step_usage(
    item: dict[str, Any], run_dir: Path
) -> tuple[float | None, dict[str, int]]:
    """Extract cumulative cost and token counts for a queue item across its attempts."""
    step_cost: float | None = None
    step_tokens: dict[str, int] = {}

    attempts = item.get("attempts") or []
    for att in attempts:
        if not isinstance(att, dict):
            continue
        att_cost = att.get("cost")
        att_toks = att.get("tokens")
        if att_cost is not None or att_toks:
            if att_cost is not None:
                step_cost = (step_cost or 0.0) + float(att_cost)
            if isinstance(att_toks, dict):
                for k, v in att_toks.items():
                    step_tokens[k] = step_tokens.get(k, 0) + int(v)
        else:
            log_path = att.get("log")
            if log_path:
                p = Path(log_path)
                if not p.is_file() and not p.is_absolute():
                    p = run_dir / p
                if not p.is_file():
                    alt = run_dir / "sessions" / p.name
                    if alt.is_file():
                        p = alt
                if p.is_file():
                    c, t = extract_log_metrics(p)
                    if c is not None:
                        step_cost = (step_cost or 0.0) + c
                    if t:
                        for k, v in t.items():
                            step_tokens[k] = step_tokens.get(k, 0) + v

    # Fallback to scanning run_dir / "sessions" if no attempts had logs
    if step_cost is None and not step_tokens and run_dir.is_dir():
        pos = item.get("position", 0)
        id6 = item.get("id6", "")
        sessions_dir = run_dir / "sessions"
        if sessions_dir.is_dir() and id6:
            candidates = list(sessions_dir.glob(f"{pos:02d}-{id6}*.jsonl"))
            if not candidates:
                candidates = list(sessions_dir.glob(f"*{id6}*.jsonl"))
            for sess_file in candidates:
                c, t = extract_log_metrics(sess_file)
                if c is not None:
                    step_cost = (step_cost or 0.0) + c
                if t:
                    for k, v in t.items():
                        step_tokens[k] = step_tokens.get(k, 0) + v

    cost_res = round(step_cost, 4) if step_cost is not None else None
    tok_res = {k: v for k, v in step_tokens.items() if v > 0}
    return cost_res, tok_res


def load_run_summary(run_dir: Path, repo_root: Path = Path(".")) -> RunSummary | None:
    """Load a RunSummary from a run directory."""
    if not run_dir.is_dir():
        return None

    state_file = run_dir / "state.json"
    report_file = run_dir / "execution-report.md"

    run_id = run_dir.name
    created_at = None
    updated_at = None
    driver_name = None
    selectors: list[str] = []
    setids: list[str] = []
    steps: list[StepSummary] = []
    counts: dict[str, int] = {}

    if state_file.is_file():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            run_id = state.get("run_id") or run_dir.name
            created_at = state.get("created_at")
            updated_at = state.get("updated_at")

            driver_info = state.get("driver") or {}
            driver_path = (
                driver_info.get("path")
                if isinstance(driver_info, dict)
                else str(driver_info)
            )
            if driver_path:
                if "oc_runipd" in driver_path:
                    driver_name = "OpenCode"
                elif "agy_runipd" in driver_path or "runagy" in driver_path:
                    driver_name = "Antigravity"
                else:
                    driver_name = Path(driver_path).stem

            queue = state.get("queue") or []
            set_set = set()
            # ssk6nf E-02: a `running` status is only trustworthy while a driver is alive to update it.
            # `oc_runipd.reconcile_interrupted` fixes it durably, but it is reached ONLY from
            # `run_queue` (a resume), so a run killed by SIGKILL/OOM/crash/suspend keeps claiming
            # `running` forever. Probe the holder ONCE per run (not per item) and project below.
            # DISPLAY-ONLY: nothing here writes state; the durable fix is `aw runs repair`.
            holder = driver_holder_state(run_dir)
            for idx, item in enumerate(queue, start=1):
                pos = item.get("position", idx)
                id6 = item.get("id6", "")
                setid = item.get("setid", "")
                if setid:
                    set_set.add(setid)
                action = item.get("action", "execute")
                status = item.get("status", "queued")
                persisted_status = None
                # Only a PROVEN-dead holder projects. HOLDER_UNKNOWN deliberately does not: failing to
                # prove liveness is not proof of death.
                if status == "running" and holder == HOLDER_NONE:
                    persisted_status = status
                    status = ABANDONED
                counts[status] = counts.get(status, 0) + 1

                cfg_file = item.get("configured_file", "")
                stem = ""
                if cfg_file:
                    stem = _identity_stem(cfg_file)
                if not stem or stem == id6:
                    discovered = _find_stem_for_id6(repo_root, id6)
                    stem = (
                        discovered
                        if discovered
                        else (f"{setid}-{id6}" if setid else id6)
                    )

                v_status = item.get("verification_status")
                attempts = item.get("attempts") or []
                att_count = len(attempts)

                session_id = None
                if attempts and isinstance(attempts[-1], dict):
                    session_id = attempts[-1].get("session_id")
                    if not updated_at:
                        updated_at = attempts[-1].get("ended_at")

                outcome = item.get("last_outcome") or {}
                disposition = None
                summary_text = None
                incomplete: list[str] = []
                if isinstance(outcome, dict):
                    disposition = outcome.get("disposition")
                    summary_text = outcome.get("summary")
                    raw_incomplete = outcome.get("incomplete_requirements")
                    if isinstance(raw_incomplete, list):
                        incomplete = [str(r) for r in raw_incomplete]

                step_cost, step_toks = extract_step_usage(item, run_dir)

                steps.append(
                    StepSummary(
                        position=pos,
                        id6=id6,
                        setid=setid,
                        action=action,
                        status=status,
                        configured_file=cfg_file,
                        stem=stem,
                        persisted_status=persisted_status,
                        verification_status=v_status,
                        attempts_count=att_count,
                        session_id=session_id,
                        disposition=disposition,
                        summary=summary_text,
                        incomplete_requirements=incomplete,
                        cost=step_cost,
                        tokens=step_toks,
                    )
                )

            setids = sorted(set_set)
        except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError):
            pass

    # Fallback to report file if state.json was absent or empty
    if not steps and report_file.is_file():
        try:
            report_text = report_file.read_text(encoding="utf-8")
            m_created = re.search(r"(?m)^-\s*Created:\s*(.+)$", report_text)
            if m_created and not created_at:
                created_at = m_created.group(1).strip()
            m_updated = re.search(r"(?m)^-\s*Updated:\s*(.+)$", report_text)
            if m_updated and not updated_at:
                updated_at = m_updated.group(1).strip()
            m_selectors = re.search(r"(?m)^-\s*Selectors:\s*`([^`]+)`", report_text)
            if m_selectors:
                selectors = [
                    s.strip() for s in m_selectors.group(1).split(",") if s.strip()
                ]

            # Parse markdown table
            for line in report_text.splitlines():
                if (
                    line.startswith("|")
                    and not line.startswith("| #")
                    and not line.startswith("|---")
                ):
                    cols = [c.strip() for c in line.split("|")[1:-1]]
                    if len(cols) >= 5:
                        try:
                            pos = int(cols[0])
                        except ValueError:
                            pos = len(steps) + 1
                        id6 = cols[1].replace("`", "").strip()
                        setid = (
                            cols[2].replace("`", "").strip() if len(cols) > 2 else ""
                        )
                        action = (
                            cols[3].replace("`", "").strip()
                            if len(cols) > 3
                            else "execute"
                        )
                        status = cols[4].strip() if len(cols) > 4 else "unknown"
                        v_status = (
                            cols[5].strip()
                            if len(cols) > 5 and cols[5].strip()
                            else None
                        )
                        attempts = 0
                        if len(cols) > 6:
                            try:
                                attempts = int(cols[6].strip())
                            except ValueError:
                                attempts = 1
                        session_id = (
                            cols[7].replace("`", "").strip() if len(cols) > 7 else None
                        )

                        discovered = _find_stem_for_id6(repo_root, id6)
                        stem = (
                            discovered
                            if discovered
                            else (f"{setid}-{id6}" if setid else id6)
                        )
                        counts[status] = counts.get(status, 0) + 1

                        step_cost, step_toks = extract_step_usage(
                            {"position": pos, "id6": id6}, run_dir
                        )

                        steps.append(
                            StepSummary(
                                position=pos,
                                id6=id6,
                                setid=setid,
                                action=action,
                                status=status,
                                configured_file="",
                                stem=stem,
                                verification_status=v_status,
                                attempts_count=attempts,
                                session_id=session_id,
                                cost=step_cost,
                                tokens=step_toks,
                            )
                        )
        except (OSError, ValueError, IndexError):
            pass

    total_cost: float | None = None
    total_tokens: dict[str, int] = {}
    for s in steps:
        if s.cost is not None:
            total_cost = (total_cost or 0.0) + s.cost
        if s.tokens:
            for k, v in s.tokens.items():
                total_tokens[k] = total_tokens.get(k, 0) + v

    dummy = RunSummary(
        run_id=run_id,
        run_dir=run_dir,
        created_at=created_at,
        updated_at=updated_at,
    )
    start_dt = dummy.timestamp_dt
    pid, pid_state, is_live, runtime_seconds, runtime_str = inspect_run_pid_and_runtime(
        run_dir, created_at, updated_at, start_dt
    )

    return RunSummary(
        run_id=run_id,
        run_dir=run_dir,
        created_at=created_at,
        updated_at=updated_at,
        driver=driver_name,
        selectors=selectors,
        setids=setids,
        steps=steps,
        counts=counts,
        total_cost=round(total_cost, 4) if total_cost is not None else None,
        total_tokens=total_tokens if total_tokens else {},
        pid=pid,
        pid_state=pid_state,
        is_live=is_live,
        runtime_seconds=runtime_seconds,
        runtime_str=runtime_str,
    )


def discover_run_dirs(repo_root: Path = Path(".")) -> list[Path]:
    """Discover all run directories across canonical and legacy record roots."""
    roots = [
        repo_root / ".aw" / "records" / "runs",
        repo_root / ".aw" / "runs",
        repo_root / ".agents" / "runs",
    ]
    seen = set()
    found = []
    for r in roots:
        if r.is_dir():
            for p in sorted(r.iterdir()):
                if p.is_dir() and p.name.startswith("run-") and p.name not in seen:
                    seen.add(p.name)
                    found.append(p)
    return found


def resolve_target_runs(
    targets: Sequence[str | Path] | None = None,
    repo_root: Path = Path("."),
) -> list[Path]:
    """Resolve user-specified targets (directories, run_ids, setids, or substrings) to concrete run directories."""
    all_runs = discover_run_dirs(repo_root)

    if not targets:
        return all_runs

    resolved: list[Path] = []
    seen = set()

    for target in targets:
        t_str = str(target).strip()
        if not t_str:
            continue

        p = Path(t_str)
        if p.is_dir() and (p / "state.json").is_file():
            canon = p.resolve()
            if canon not in seen:
                seen.add(canon)
                resolved.append(p)
            continue
        elif (
            p.is_file()
            and p.parent.is_dir()
            and p.name in ("state.json", "events.jsonl", "execution-report.md")
        ):
            canon = p.parent.resolve()
            if canon not in seen:
                seen.add(canon)
                resolved.append(p.parent)
            continue

        # Substring or exact match against run directory name or setid
        matched = False
        for run_p in all_runs:
            if t_str == run_p.name or t_str in run_p.name:
                canon = run_p.resolve()
                if canon not in seen:
                    seen.add(canon)
                    resolved.append(run_p)
                matched = True

        if not matched:
            # Check if target matches a Set ID inside state.json
            for run_p in all_runs:
                s_file = run_p / "state.json"
                if s_file.is_file():
                    try:
                        content = s_file.read_text(encoding="utf-8")
                        if f'"{t_str}"' in content:
                            canon = run_p.resolve()
                            if canon not in seen:
                                seen.add(canon)
                                resolved.append(run_p)
                    except (OSError, json.JSONDecodeError):
                        pass

    return resolved


def _clean_timestamp(ts: str | None) -> str:
    """Format ISO timestamp into clean display date/time."""
    if not ts:
        return ""
    clean = ts.replace("T", " ")
    if "+" in clean:
        clean = clean.split("+")[0]
    if "Z" in clean:
        clean = clean.replace("Z", "")
    return clean[:19]


def format_step_line(
    step: StepSummary,
    term: Term,
    long: bool = False,
    status_width: int = 18,
    stem_width: int = 0,
) -> str:
    """Format a single step summary line aligned with aw att / aw ipd lint style."""
    status_word = step.status
    if status_word == "substantially-complete":
        status_word = "complete"

    status_padded = (
        term.status_256(status_word, width=status_width)
        if getattr(term, "color", False)
        else status_word.ljust(status_width)
    )

    lead = "   "
    type_word = "plan"
    type_txt = (
        term.color256(type_word, _TREE_COLOR_256, bold=True)
        if getattr(term, "color", False)
        else type_word
    )
    type_prefix = type_txt + (" " * max(0, 8 - len(type_word))) + "  "

    stem = step.stem
    if not stem:
        stem = f"{step.setid}-{step.id6}" if step.setid else step.id6

    badges = []
    if step.attempts_count > 0:
        badges.append(f"[attempts: {step.attempts_count}]")
    # ssk6nf E-03: attribute a PROJECTED status so an operator can tell "no live driver holds this run"
    # from "the driver recorded this". Names the persisted value so nothing is hidden.
    if step.is_projected:
        badge = f"[no live driver; recorded {step.persisted_status}]"
        badges.append(
            term.color256(badge, 208, bold=True)
            if getattr(term, "color", False)
            else badge
        )
    if step.verification_status == "verified":
        badges.append(
            term.color256("[verified]", 46, bold=True)
            if getattr(term, "color", False)
            else "[verified]"
        )
    elif step.verification_status == "failed":
        badges.append(
            term.color256("[verify-failed]", 196, bold=True)
            if getattr(term, "color", False)
            else "[verify-failed]"
        )
    if step.cost is not None:
        cost_str = f"${step.cost:.2f}"
        badges.append(
            term.color256(f"[{cost_str}]", 220)
            if getattr(term, "color", False)
            else f"[{cost_str}]"
        )
    if step.action == "review":
        badges.append(
            term.color256("[review]", 226)
            if getattr(term, "color", False)
            else "[review]"
        )

    badge_txt = ("  " + "  ".join(badges)) if badges else ""

    disp_txt = ""
    if step.disposition and step.disposition not in (step.status, status_word):
        disp_styled = (
            term.status_256(step.disposition)
            if getattr(term, "color", False)
            else step.disposition
        )
        disp_txt = f"  {disp_styled}"

    stem_padded = (
        stem.ljust(stem_width) if (stem_width and (badge_txt or disp_txt)) else stem
    )
    return f"- {lead}{status_padded}  {type_prefix}{stem_padded}{badge_txt}{disp_txt}"


def render_box_table(
    title: str,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    term: Term,
    alignments: Sequence[str] | None = None,
) -> str:
    """Render a table with rounded box art borders and headers, with no horizontal borders between data rows."""
    use_unicode = getattr(term, "unicode", True)
    if use_unicode:
        tl, tm, tr = "╭", "┬", "╮"
        ml, mm, mr = "├", "┼", "┤"
        bl, bm, br = "╰", "┴", "╯"
        vl, hl = "│", "─"
    else:
        tl = tm = tr = ml = mm = mr = bl = bm = br = "+"
        vl, hl = "|", "-"

    num_cols = len(headers)
    aligns = list(alignments) if alignments else ["left"] * num_cols

    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            raw_len = len(strip_ansi(str(cell)))
            col_widths[idx] = max(col_widths[idx], raw_len)

    top_border = tl + tm.join(hl * (w + 2) for w in col_widths) + tr
    sep_border = ml + mm.join(hl * (w + 2) for w in col_widths) + mr
    bot_border = bl + bm.join(hl * (w + 2) for w in col_widths) + br

    lines = []
    if title:
        lines.append(
            term.colorize(title, "bold") if getattr(term, "color", False) else title
        )
    lines.append(top_border)

    hdr_cells = []
    for idx, (h, w, align) in enumerate(zip(headers, col_widths, aligns)):
        h_styled = term.colorize(h, "bold") if getattr(term, "color", False) else h
        pad = w - len(h)
        spaces = " " * pad
        if align == "right":
            hdr_cells.append(f" {spaces}{h_styled} ")
        else:
            hdr_cells.append(f" {h_styled}{spaces} ")
    lines.append(vl + vl.join(hdr_cells) + vl)
    lines.append(sep_border)

    for row in rows:
        row_cells = []
        for idx, (cell, w, align) in enumerate(zip(row, col_widths, aligns)):
            cell_str = str(cell)
            raw_len = len(strip_ansi(cell_str))
            pad = w - raw_len
            spaces = " " * pad
            if align == "right":
                row_cells.append(f" {spaces}{cell_str} ")
            else:
                row_cells.append(f" {cell_str}{spaces} ")
        lines.append(vl + vl.join(row_cells) + vl)

    lines.append(bot_border)
    return "\n".join(lines)


def render_steps_table(
    steps: list[StepSummary],
    term: Term,
    short: bool = False,
    repo_root: Path = Path("."),
) -> str:
    """Render a list of steps in a rounded box table."""
    if not steps:
        return ""
    if short:
        headers = ["Status", "Item", "Action", "Verified"]
        aligns = ["left", "left", "left", "left"]
    else:
        headers = [
            "Status",
            "Item",
            "Action",
            "Attempts",
            "Cost",
            "Total Tok",
            "Verified",
        ]
        aligns = [
            "left",
            "left",
            "left",
            "right",
            "right",
            "right",
            "left",
        ]
    rows = []
    for step in steps:
        audit = audit_step_artifact(step, repo_root)
        st_disp = "complete" if step.status == "substantially-complete" else step.status
        st_styled = (
            term.status_256(st_disp) if getattr(term, "color", False) else st_disp
        )
        if audit.status_mismatch and audit.file_status:
            diff_badge = f"[file: {audit.file_status}]"
            diff_styled = (
                term.color256(diff_badge, 220)
                if getattr(term, "color", False)
                else diff_badge
            )
            st_styled = f"{st_styled} {diff_styled}"

        item_disp = step.stem or (
            f"{step.setid}-{step.id6}" if step.setid else step.id6
        )
        if audit.missing_entirely:
            badge = "[MISSING]"
            badge_styled = (
                term.color256(badge, 196, bold=True)
                if getattr(term, "color", False)
                else badge
            )
            item_disp = f"{item_disp} {badge_styled}"
        elif audit.location_mismatch and audit.actual_dir:
            badge = f"[in {audit.actual_dir}/]"
            badge_styled = (
                term.color256(badge, 214) if getattr(term, "color", False) else badge
            )
            item_disp = f"{item_disp} {badge_styled}"

        att_disp = str(step.attempts_count) if step.attempts_count else "-"
        cost_disp = f"${step.cost:.2f}" if step.cost is not None else "-"
        tok_disp = (
            format_tokens(step.tokens.get("total", 0))
            if step.tokens.get("total")
            else "-"
        )
        v_val = step.verification_status or step.disposition
        if v_val == "verified":
            v_disp = (
                term.color256("yes", 46, bold=True)
                if getattr(term, "color", False)
                else "yes"
            )
        elif v_val in ("unverified", "verify-failed", "failed"):
            v_disp = (
                term.color256("no", 196, bold=True)
                if getattr(term, "color", False)
                else "no"
            )
        else:
            v_disp = "-"

        if short:
            rows.append([st_styled, item_disp, step.action, v_disp])
        else:
            rows.append(
                [
                    st_styled,
                    item_disp,
                    step.action,
                    att_disp,
                    cost_disp,
                    tok_disp,
                    v_disp,
                ]
            )
    return render_box_table("", headers, rows, term, aligns)


def render_step_details(steps: list[StepSummary], term: Term) -> list[str]:
    """Render detail lines for a list of steps."""
    lines = []
    for step in steps:
        details = []
        if step.incomplete_requirements:
            for req in step.incomplete_requirements:
                details.append(
                    term.color256(f"  ! incomplete: {req}", 214)
                    if getattr(term, "color", False)
                    else f"  ! incomplete: {req}"
                )
        if step.summary:
            sum_text = step.summary.strip().replace("\n", " ")
            if len(sum_text) > 120:
                sum_text = sum_text[:117] + "..."
            details.append(
                term.color256(f"  * summary: {sum_text}", 245)
                if getattr(term, "color", False)
                else f"  * summary: {sum_text}"
            )
        if step.cost is not None:
            details.append(
                term.color256(f"  $ cost: ${step.cost:.2f}", 220)
                if getattr(term, "color", False)
                else f"  $ cost: ${step.cost:.2f}"
            )
        if step.tokens:
            tok_parts = []
            if step.tokens.get("total"):
                tok_parts.append(f"{format_tokens(step.tokens['total'])} tot")
            if step.tokens.get("input"):
                tok_parts.append(f"{format_tokens(step.tokens['input'])} in")
            if step.tokens.get("output"):
                tok_parts.append(f"{format_tokens(step.tokens['output'])} out")
            if step.tokens.get("cache"):
                tok_parts.append(f"{format_tokens(step.tokens['cache'])} cache")
            if tok_parts:
                tok_str = ", ".join(tok_parts)
                details.append(
                    term.color256(f"  * tokens: {tok_str}", 245)
                    if getattr(term, "color", False)
                    else f"  * tokens: {tok_str}"
                )
        if details:
            item_id = step.stem or (
                f"{step.setid}-{step.id6}" if step.setid else step.id6
            )
            lines.append(f"\nDetails for {item_id}:")
            lines.extend(details)
    return lines


def format_run_human(
    run: RunSummary,
    term: Term,
    detail: bool = False,
    short: bool = False,
    repo_root: Path = Path("."),
) -> str:
    """Format a RunSummary as human terminal text."""
    lines = []

    # Header line: run_id [setid] timestamp
    run_id_txt = (
        term.color256(run.run_id, 33, bold=True)
        if getattr(term, "color", False)
        else run.run_id
    )
    set_txt = ""
    if run.setids:
        sets_joined = ", ".join(run.setids)
        set_txt = f"  [{sets_joined}]"

    date_str = _clean_timestamp(run.created_at or run.updated_at)
    date_txt = f"  {date_str}" if date_str else ""

    # Line 1: identity, targets, start timestamp
    lines.append(f"{run_id_txt}{set_txt}{date_txt}")

    # Line 2: PID and runtime info (if present)
    meta_parts = []
    if run.pid is not None:
        p_state = run.pid_state or "unknown"
        if getattr(term, "color", False) and run.is_live:
            p_state_txt = term.color256(f"[{p_state}]", 40, bold=True)
        else:
            p_state_txt = f"[{p_state}]"
        meta_parts.append(f"pid: {run.pid} {p_state_txt}")
    if run.runtime_str:
        meta_parts.append(f"runtime: {run.runtime_str}")

    if meta_parts:
        lines.append(f"  {', '.join(meta_parts)}")

    # Line 3: Step count and status tally
    tally_parts = []
    for st, cnt in sorted(run.counts.items()):
        st_display = "complete" if st == "substantially-complete" else st
        tally_parts.append(f"{cnt} {st_display}")
    tally_str = ", ".join(tally_parts) if tally_parts else f"{len(run.steps)} steps"
    lines.append(f"  {len(run.steps)} steps: {tally_str}")

    # Line 4: Cost and token usage (if present)
    cost_val_str = f"${run.total_cost:.2f}" if run.total_cost is not None else None
    if run.total_tokens.get("total"):
        tot_str = format_tokens(run.total_tokens["total"])
        in_str = format_tokens(run.total_tokens.get("input", 0))
        out_str = format_tokens(run.total_tokens.get("output", 0))
        cache_str = format_tokens(run.total_tokens.get("cache", 0))
        tok_str = f"{tot_str} tok ({in_str} in, {out_str} out, {cache_str} cached)"
        if cost_val_str is not None:
            lines.append(f"  {cost_val_str}, {tok_str}")
        else:
            lines.append(f"  {tok_str}")
    elif cost_val_str is not None:
        lines.append(f"  {cost_val_str}")

    if run.steps:
        tbl = render_steps_table(run.steps, term, short=short, repo_root=repo_root)
        if tbl:
            lines.append(tbl)
        if detail:
            lines.extend(render_step_details(run.steps, term))

    return "\n".join(lines)


def format_latest_only_human(
    summaries: list[RunSummary],
    term: Term,
    detail: bool = False,
    short: bool = False,
    repo_root: Path = Path("."),
) -> str:
    """Format the deduplicated latest step records across matched runs."""
    latest_steps_dict: dict[str, tuple[RunSummary, StepSummary]] = {}
    for s in summaries:
        for step in s.steps:
            key = step.id6 or step.stem or step.item
            latest_steps_dict[key] = (s, step)

    if not latest_steps_dict:
        return "no steps found in matched runs"

    contributing_runs = {r.run_id for r, _ in latest_steps_dict.values()}
    steps = [st for _, st in latest_steps_dict.values()]

    if len(summaries) == 1 or len(contributing_runs) <= 1:
        single_run = next(
            (r for r in summaries if r.run_id in contributing_runs), summaries[0]
        )
        return format_run_human(
            single_run, term, detail=detail, short=short, repo_root=repo_root
        )

    lines = [f"Data from {len(contributing_runs)} runs"]
    tbl = render_steps_table(steps, term, short=short, repo_root=repo_root)
    if tbl:
        lines.append(tbl)
    if detail:
        lines.extend(render_step_details(steps, term))

    return "\n".join(lines)


def build_multi_run_summary_dict(summaries: list[RunSummary]) -> dict[str, Any]:
    """Compute aggregate and category breakdown summary across multiple runs."""
    total_runs = len(summaries)
    total_steps = sum(len(s.steps) for s in summaries)
    total_cost = 0.0
    has_any_cost = False
    cost_steps_count = 0
    total_tokens: dict[str, int] = defaultdict(int)

    by_status: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "count": 0,
            "steps_with_cost": 0,
            "total_cost": 0.0,
            "tokens": defaultdict(int),
            "runs_present": set(),
        }
    )
    by_action: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "count": 0,
            "steps_with_cost": 0,
            "total_cost": 0.0,
            "tokens": defaultdict(int),
            "runs_present": set(),
        }
    )

    for run_idx, s in enumerate(summaries):
        for step in s.steps:
            st = step.status
            act = step.action
            by_status[st]["count"] += 1
            by_status[st]["runs_present"].add(run_idx)
            by_action[act]["count"] += 1
            by_action[act]["runs_present"].add(run_idx)

            if step.cost is not None:
                has_any_cost = True
                cost_steps_count += 1
                total_cost += step.cost
                by_status[st]["steps_with_cost"] += 1
                by_status[st]["total_cost"] = round(
                    by_status[st]["total_cost"] + step.cost, 4
                )
                by_action[act]["steps_with_cost"] += 1
                by_action[act]["total_cost"] = round(
                    by_action[act]["total_cost"] + step.cost, 4
                )
            if step.tokens:
                for k, v in step.tokens.items():
                    total_tokens[k] += v
                    by_status[st]["tokens"][k] += v
                    by_action[act]["tokens"][k] += v

    avg_cost_per_run = (
        round(total_cost / total_runs, 4) if (total_runs > 0 and has_any_cost) else None
    )
    avg_tokens_per_run = (
        {k: int(v / total_runs) for k, v in total_tokens.items()}
        if (total_runs > 0 and total_tokens)
        else {}
    )

    status_summary = {}
    for st, data in by_status.items():
        c_cnt = data["steps_with_cost"]
        runs_cnt = len(data["runs_present"])
        entry: dict[str, Any] = {
            "count": data["count"],
            "steps_with_cost": c_cnt,
            "runs_count": runs_cnt,
        }
        if c_cnt > 0:
            c_tot = data["total_cost"]
            tok_dict = dict(data["tokens"])
            entry["total_cost"] = round(c_tot, 4)
            entry["avg_cost_per_step"] = round(c_tot / c_cnt, 4)
            entry["avg_cost_per_run"] = round(c_tot / total_runs, 4)
            entry["tokens"] = tok_dict
            entry["avg_tokens_per_step"] = {
                k: int(v / c_cnt) for k, v in tok_dict.items()
            }
            entry["avg_tokens_per_run"] = {
                k: int(v / total_runs) for k, v in tok_dict.items()
            }
        status_summary[st] = entry

    action_summary = {}
    for act, data in by_action.items():
        c_cnt = data["steps_with_cost"]
        runs_cnt = len(data["runs_present"])
        entry = {
            "count": data["count"],
            "steps_with_cost": c_cnt,
            "runs_count": runs_cnt,
        }
        if c_cnt > 0:
            c_tot = data["total_cost"]
            tok_dict = dict(data["tokens"])
            entry["total_cost"] = round(c_tot, 4)
            entry["avg_cost_per_step"] = round(c_tot / c_cnt, 4)
            entry["avg_cost_per_run"] = round(c_tot / total_runs, 4)
            entry["tokens"] = tok_dict
            entry["avg_tokens_per_step"] = {
                k: int(v / c_cnt) for k, v in tok_dict.items()
            }
            entry["avg_tokens_per_run"] = {
                k: int(v / total_runs) for k, v in tok_dict.items()
            }
        action_summary[act] = entry

    return {
        "runs_count": total_runs,
        "steps_count": total_steps,
        "steps_with_cost": cost_steps_count,
        "total_cost": round(total_cost, 4) if has_any_cost else None,
        "avg_cost_per_run": avg_cost_per_run,
        "total_tokens": dict(total_tokens) if total_tokens else {},
        "avg_tokens_per_run": avg_tokens_per_run,
        "by_status": status_summary,
        "by_action": action_summary,
    }


def format_multi_run_summary(summaries: list[RunSummary], term: Term) -> str:
    """Format an aggregate summary across multiple runs for terminal display."""
    summary_data = build_multi_run_summary_dict(summaries)
    total_runs = summary_data["runs_count"]
    total_steps = summary_data["steps_count"]
    has_any_cost = summary_data["total_cost"] is not None
    cost_steps_count = summary_data["steps_with_cost"]
    total_cost = summary_data["total_cost"] or 0.0
    avg_cost_per_run = summary_data["avg_cost_per_run"] or 0.0
    total_toks = summary_data["total_tokens"] or {}
    avg_toks_run = summary_data["avg_tokens_per_run"] or {}

    lines = []
    header_title = f"--- Summary across {total_runs} runs ({total_steps} steps) ---"
    lines.append(
        term.color256(header_title, 33, bold=True)
        if getattr(term, "color", False)
        else header_title
    )

    if has_any_cost:
        cost_str = f"${total_cost:.2f}"
        cost_val_str = (
            term.color256(cost_str, 220, bold=True)
            if getattr(term, "color", False)
            else cost_str
        )
        avg_run_cost_str = f"${avg_cost_per_run:.2f}"
        lines.append(
            f"Total Cost:   {cost_val_str} (across {cost_steps_count}/{total_steps} steps with usage; avg {avg_run_cost_str}/run)"
        )
        if total_toks.get("total"):
            tok_str = format_tokens(total_toks.get("total", 0))
            in_str = format_tokens(total_toks.get("input", 0))
            out_str = format_tokens(total_toks.get("output", 0))
            cache_str = format_tokens(total_toks.get("cache", 0))
            avg_tok_run_str = format_tokens(avg_toks_run.get("total", 0))
            lines.append(
                f"Total Tokens: {tok_str} ({in_str} in, {out_str} out, {cache_str} cached; avg {avg_tok_run_str}/run)"
            )

        # Status Table
        by_status = summary_data["by_status"]
        headers_st = ["Status", "Type", "Cost", "Tokens", "In", "Out", "Cached"]
        aligns_st = ["left", "left", "right", "right", "right", "right", "right"]
        rows_st = []
        for st, data in sorted(
            by_status.items(),
            key=lambda x: (-x[1].get("total_cost", 0.0), -x[1]["count"]),
        ):
            c_cnt = data["steps_with_cost"]
            st_disp = "complete" if st == "substantially-complete" else st
            st_styled = (
                term.status_256(st_disp) if getattr(term, "color", False) else st_disp
            )
            td = data.get("tokens", {})
            avg_td = data.get("avg_tokens_per_step", {})

            if c_cnt > 0:
                c_tot = f"${data['total_cost']:.2f}"
                c_avg = f"${data['avg_cost_per_step']:.2f}"
                t_tot = format_tokens(td.get("total", 0)) if td.get("total") else "-"
                t_avg = (
                    format_tokens(avg_td.get("total", 0))
                    if avg_td.get("total")
                    else "-"
                )
                in_tot = format_tokens(td.get("input", 0)) if td.get("input") else "-"
                in_avg = (
                    format_tokens(avg_td.get("input", 0))
                    if avg_td.get("input")
                    else "-"
                )
                out_tot = (
                    format_tokens(td.get("output", 0)) if td.get("output") else "-"
                )
                out_avg = (
                    format_tokens(avg_td.get("output", 0))
                    if avg_td.get("output")
                    else "-"
                )
                cache_tot = (
                    format_tokens(td.get("cache", 0)) if td.get("cache") else "-"
                )
                cache_avg = (
                    format_tokens(avg_td.get("cache", 0))
                    if avg_td.get("cache")
                    else "-"
                )
            else:
                c_tot = c_avg = t_tot = t_avg = in_tot = in_avg = out_tot = out_avg = (
                    cache_tot
                ) = cache_avg = "-"

            rows_st.append(
                [st_styled, "Total", c_tot, t_tot, in_tot, out_tot, cache_tot]
            )
            rows_st.append(["", "Avg", c_avg, t_avg, in_avg, out_avg, cache_avg])

        lines.append("")
        lines.append(
            render_box_table(
                "Breakdown by Status:", headers_st, rows_st, term, aligns_st
            )
        )

        # Action Table
        by_action = summary_data["by_action"]
        if len(by_action) > 1:
            headers_act = ["Action", "Type", "Cost", "Tokens", "In", "Out", "Cached"]
            aligns_act = ["left", "left", "right", "right", "right", "right", "right"]
            rows_act = []
            for act, data in sorted(
                by_action.items(),
                key=lambda x: (-x[1].get("total_cost", 0.0), -x[1]["count"]),
            ):
                c_cnt = data["steps_with_cost"]
                act_styled = (
                    term.color256(act, 226) if getattr(term, "color", False) else act
                )
                td = data.get("tokens", {})
                avg_td = data.get("avg_tokens_per_step", {})

                if c_cnt > 0:
                    c_tot = f"${data['total_cost']:.2f}"
                    c_avg = f"${data['avg_cost_per_step']:.2f}"
                    t_tot = (
                        format_tokens(td.get("total", 0)) if td.get("total") else "-"
                    )
                    t_avg = (
                        format_tokens(avg_td.get("total", 0))
                        if avg_td.get("total")
                        else "-"
                    )
                    in_tot = (
                        format_tokens(td.get("input", 0)) if td.get("input") else "-"
                    )
                    in_avg = (
                        format_tokens(avg_td.get("input", 0))
                        if avg_td.get("input")
                        else "-"
                    )
                    out_tot = (
                        format_tokens(td.get("output", 0)) if td.get("output") else "-"
                    )
                    out_avg = (
                        format_tokens(avg_td.get("output", 0))
                        if avg_td.get("output")
                        else "-"
                    )
                    cache_tot = (
                        format_tokens(td.get("cache", 0)) if td.get("cache") else "-"
                    )
                    cache_avg = (
                        format_tokens(avg_td.get("cache", 0))
                        if avg_td.get("cache")
                        else "-"
                    )
                else:
                    c_tot = c_avg = t_tot = t_avg = in_tot = in_avg = out_tot = (
                        out_avg
                    ) = cache_tot = cache_avg = "-"

                rows_act.append(
                    [act_styled, "Total", c_tot, t_tot, in_tot, out_tot, cache_tot]
                )
                rows_act.append(["", "Avg", c_avg, t_avg, in_avg, out_avg, cache_avg])

            lines.append("")
            lines.append(
                render_box_table(
                    "Breakdown by Action:",
                    headers_act,
                    rows_act,
                    term,
                    aligns_act,
                )
            )
    else:
        lines.append("No recorded cost/token data for the selected runs.")

    return "\n".join(lines)


def repair_run(run_dir: Path, repo_root: Path = Path(".")) -> tuple[int, str]:
    """ssk6nf E-04: durably reconcile a run abandoned without a terminal status.

    Delegates to ``oc_runipd.reconcile_interrupted``, the SINGLE reconciler (it resolves each running
    item's plan, promotes one that genuinely reached ``executed``, else marks it ``interrupted``).
    Deliberately does not reimplement that logic (GUIDING_PRINCIPLES P8).

    REFUSES while a live driver holds the run: repairing under a running driver would race its writer.
    A run with nothing to reconcile is a no-op. Returns ``(exit_code, message)``.
    """
    run_dir = Path(run_dir)
    if not (run_dir / "state.json").is_file():
        return 2, f"not a run directory: {run_dir}"

    holder = driver_holder_state(run_dir)
    if holder == HOLDER_LIVE:
        return 1, (
            f"refusing to repair {run_dir.name}: a live driver still holds this run "
            "(stop it first, then repair)"
        )
    if holder == HOLDER_UNKNOWN:
        return 1, (
            f"refusing to repair {run_dir.name}: could not prove no driver holds it "
            "(flock unavailable on this platform)"
        )

    from agent_workflows import oc_runipd

    state = oc_runipd.load_state(run_dir)
    stale = [
        i.get("id6", "") for i in state.get("queue", []) if i.get("status") == "running"
    ]
    if not stale:
        return 0, f"{run_dir.name}: nothing to repair (no running steps)"

    oc_runipd.reconcile_interrupted(run_dir, state)

    after = oc_runipd.load_state(run_dir)
    by_id = {i.get("id6", ""): i.get("status") for i in after.get("queue", [])}
    changes = ", ".join(f"{i} running -> {by_id.get(i)}" for i in stale)
    return 0, f"{run_dir.name}: reconciled {len(stale)} step(s): {changes}"


def run_viewer_cli(args: argparse.Namespace) -> int:
    """CLI entry point for `aw runs` / run viewer."""
    repo_root = Path(getattr(args, "dir", None) or ".")
    # ssk6nf E-04: `aw runs repair <run-id>` is an opt-in MUTATING verb on an otherwise read-only
    # surface, routed from the first target token so every read path stays side-effect free.
    raw_targets = getattr(args, "target", None) or getattr(args, "targets", None) or []
    if isinstance(raw_targets, str):
        raw_targets = [raw_targets]
    if raw_targets and raw_targets[0] == "repair":
        targets = list(raw_targets[1:])
        if not targets:
            print("error: aw runs repair needs a run id (or a run directory path)")
            return 2
        rc = 0
        for run_dir in resolve_target_runs(targets, repo_root):
            code, message = repair_run(run_dir, repo_root)
            print(message)
            rc = rc or code
        return rc

    run_dirs = resolve_target_runs(raw_targets, repo_root)

    # Filtering options
    set_filter = getattr(args, "set", None)
    ipd_filter = getattr(args, "ipd", None) or getattr(args, "id6", None)
    status_filter = getattr(args, "status", None)
    failed_only = getattr(args, "failed", False)
    active_only = getattr(args, "active", False)
    last_n = getattr(args, "last", None)
    if last_n is None:
        if getattr(args, "latest", False):
            last_n = 1
    elif isinstance(last_n, bool):
        last_n = 1 if last_n else None
    elif isinstance(last_n, str):
        try:
            last_n = int(last_n)
        except ValueError:
            last_n = None
    since_spec = getattr(args, "since", None)
    detail = getattr(args, "detail", False) or getattr(args, "long", False)
    short = getattr(args, "short", False)
    summary_only = getattr(args, "summary_only", False)
    latest_only = getattr(args, "latest_only", False)
    is_json = getattr(args, "json", False)
    is_agent = getattr(args, "agent", False) or getattr(args, "as_agent", False)
    no_color = getattr(args, "no_color", False)

    term = Term(color=False if no_color else None)

    if short and summary_only:
        err_msg = "error: --summary-only/-S cannot be used with --short/-s"
        if is_agent or is_json:
            print(json.dumps({"error": err_msg, "exit_code": 2}))
        else:
            term.line(err_msg)
        return 2

    if latest_only and summary_only:
        err_msg = "error: --latest-only/-L cannot be used with --summary-only/-S"
        if is_agent or is_json:
            print(json.dumps({"error": err_msg, "exit_code": 2}))
        else:
            term.line(err_msg)
        return 2

    since_dt = None
    if since_spec:
        try:
            since_dt = resolve_since_timestamp(since_spec, repo_root=repo_root)
        except ValueError as exc:
            err_msg = f"error: {exc}"
            if is_agent or is_json:
                print(json.dumps({"error": err_msg, "exit_code": 2}))
            else:
                term.line(err_msg)
            return 2

    summaries: list[RunSummary] = []
    for r_dir in run_dirs:
        summary = load_run_summary(r_dir, repo_root)
        if not summary:
            continue

        if (
            set_filter
            and set_filter not in summary.setids
            and set_filter not in summary.selectors
        ):
            continue

        if ipd_filter and not any(s.id6 == ipd_filter for s in summary.steps):
            continue

        if status_filter and not any(s.status == status_filter for s in summary.steps):
            continue

        if failed_only and not any(
            s.status in ("failed", "partial", "blocked", "interrupted")
            for s in summary.steps
        ):
            continue

        if active_only and not any(s.status == "running" for s in summary.steps):
            continue

        if since_dt:
            run_dt = summary.timestamp_dt
            if run_dt and run_dt < since_dt:
                continue

        summaries.append(summary)

    if last_n is not None and summaries:
        if last_n > 0:
            summaries = summaries[-last_n:]
        else:
            summaries = []

    if not summaries:
        if is_agent or is_json:
            print(json.dumps({"runs": []}, indent=2 if is_json else None))
            return 0
        term.line("no matching runs found")
        return 0

    # Collect artifact audits across displayed steps
    all_audits: list[StepArtifactAudit] = []
    if latest_only:
        latest_steps_dict: dict[str, tuple[RunSummary, StepSummary]] = {}
        for s in summaries:
            for step in s.steps:
                key = step.id6 or step.stem or step.item
                latest_steps_dict[key] = (s, step)
        for _, st in latest_steps_dict.values():
            all_audits.append(audit_step_artifact(st, repo_root))
    else:
        for s in summaries:
            for st in s.steps:
                all_audits.append(audit_step_artifact(st, repo_root))

    if is_json:
        if latest_only:
            latest_steps_dict = {}
            for s in summaries:
                for step in s.steps:
                    key = step.id6 or step.stem or step.item
                    latest_steps_dict[key] = (s, step)
            contributing = list({r.run_id for r, _ in latest_steps_dict.values()})
            steps_list = [asdict(st) for _, st in latest_steps_dict.values()]
            payload = {
                "runs_count": len(contributing),
                "runs": contributing,
                "steps": steps_list,
            }
        elif summary_only:
            payload = {"summary": build_multi_run_summary_dict(summaries)}
        else:
            payload = {"runs": [asdict(s) for s in summaries]}
            for r_dict in payload["runs"]:
                r_dict["run_dir"] = str(r_dict["run_dir"])
            if len(summaries) > 1:
                payload["summary"] = build_multi_run_summary_dict(summaries)

        disc = [
            asdict(a)
            for a in all_audits
            if a.missing_entirely or a.location_mismatch or a.status_mismatch
        ]
        for d in disc:
            if d.get("actual_path"):
                d["actual_path"] = str(d["actual_path"])
        if disc:
            payload["artifact_discrepancies"] = disc

        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if is_agent:
        if latest_only:
            latest_steps_dict = {}
            for s in summaries:
                for step in s.steps:
                    key = step.id6 or step.stem or step.item
                    latest_steps_dict[key] = (s, step)
            for _, st in latest_steps_dict.values():
                print(json.dumps(asdict(st), separators=(",", ":"), ensure_ascii=False))
            return 0
        if summary_only:
            s_dict = build_multi_run_summary_dict(summaries)
            print(json.dumps(s_dict, separators=(",", ":"), ensure_ascii=False))
            return 0
        for s in summaries:
            s_dict = asdict(s)
            s_dict["run_dir"] = str(s_dict["run_dir"])
            print(json.dumps(s_dict, separators=(",", ":"), ensure_ascii=False))
        return 0

    # Human display
    if latest_only:
        term.line(
            format_latest_only_human(
                summaries, term, detail=detail, short=short, repo_root=repo_root
            )
        )
        audit_summary_txt = format_artifact_audit_summary(all_audits, term)
        if audit_summary_txt:
            term.line("")
            term.line(audit_summary_txt)
        return 0

    if summary_only:
        term.line(format_multi_run_summary(summaries, term))
        audit_summary_txt = format_artifact_audit_summary(all_audits, term)
        if audit_summary_txt:
            term.line("")
            term.line(audit_summary_txt)
        return 0

    for idx, summary in enumerate(summaries):
        if idx > 0:
            term.line("")
        term.line(
            format_run_human(
                summary, term, detail=detail, short=short, repo_root=repo_root
            )
        )

    if len(summaries) > 1 and not short:
        term.line("")
        term.line(format_multi_run_summary(summaries, term))

    audit_summary_txt = format_artifact_audit_summary(all_audits, term)
    if audit_summary_txt:
        term.line("")
        term.line(audit_summary_txt)

    return 0
