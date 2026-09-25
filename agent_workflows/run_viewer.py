"""Run viewer for inspecting and summarizing driver runs (aw oc/agy run records).

Read-only inspection tool for `.aw/records/runs/run-*` directories that displays
the ending state of each IPD step in similar unified format to `aw att` and `aw ipd lint`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_workflows import agent_schema as _agent_schema
from agent_workflows import platform_lock
from agent_workflows import artifact_audit as _audit
from agent_workflows import lifecycle_style as _LS
from agent_workflows import term as _T

# `_TREE_COLOR_256` IS DELIBERATELY NO LONGER IMPORTED (plan `9zvl2w` E-04). Its only use here was
# painting the artifact TYPE word in `format_step_line`, which criterion A10 forbids; see the note at
# that call site. `attention.py` keeps the constant for the legitimate path-SEGMENT case.
from agent_workflows.attention import _identity_stem
from agent_workflows.render_stream import (
    format_tokens,
    # orchprobe (r2i1b1) E-03/E-04: the SHARED refusal record and its reader. This viewer never
    # re-derives the storage key, because a reader looking under a different name than the writer
    # uses is exactly the defect F-4 measured in the run-summary renderer.
    REFUSAL_KEY,
    Refusal,
    refusal_of_item,
)
from agent_workflows.runner_shared import (
    ANALYTICS_DIRNAME,
    analytics_root,
    canonical_terminal_status,
    extract_verifier_test_commands,
    landed_verdict,
    path_is_within_analytics,
    state_root,
)
from agent_workflows.term import Term, strip_ansi


# runstale Order 01 (ssk6nf) E-01/E-03: the DISPLAY-ONLY status a `running` step is projected to when
# no live driver holds its run. Deliberately NOT the bare word `interrupted`: a persisted `interrupted`
# is a fact `runner_shared.reconcile_interrupted` recorded after resolving the plan AND reading the
# step's own outcome file, whereas this is an inference from "nobody holds the lock" that has inspected
# nothing. Collapsing the two would let the viewer assert a reconciliation that never happened.
#
# STILL THE RIGHT LABEL WHEN NOTHING IS KNOWN, and only then (runrecon-02 `fduoj4` E-04). Since that
# plan the reconciler consults `outcomes/<NN>-<id6>.json`, so a step whose own outcome file records a
# terminal disposition has a KNOWN answer sitting on disk, and calling it `abandoned?` understates what
# is already readable. `_projected_step_status` below therefore reports the recovered disposition, with
# a `?` suffix marking it as read-time and unreconciled; this bare word remains for the genuinely
# unknown case. The read path still MUTATES NOTHING (`GUIDING_PRINCIPLES` P10): making the answer
# DURABLE is `aw runs repair`'s job, which `ssk6nf` shipped as an opt-in verb for exactly this reason.
ABANDONED = "abandoned?"

#: Suffix marking a read-time projection, i.e. a status this VIEW derived rather than one the driver
#: persisted. `abandoned?` carries it already; a recovered disposition carries the same mark so the two
#: read alike and neither can be mistaken for a persisted fact (runrecon-02 `fduoj4` E-04).
PROJECTION_SUFFIX = "?"

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
    means no holder. Anything we cannot determine (no POSIX lock primitive on this platform, or any
    OSError) is ``HOLDER_UNKNOWN``, never ``HOLDER_NONE``: failing to prove a driver is alive is not
    proof it is dead, and only a proven-dead run may be projected (ssk6nf E-01).

    The probe itself is ``platform_lock.probe_free``, shared with ``runner_shutdown.lock_is_free``
    rather than reimplemented here (IPD `y6mfgo`). It observes without creating or truncating, which
    this function's contract requires: the driver records ``pid=`` INSIDE this file and
    :func:`inspect_run_pid_and_runtime` reads it back, so a probe that truncated would destroy a live
    driver's own record.
    """
    lock_path = Path(run_dir) / "driver.lock"
    if not lock_path.is_file():
        return HOLDER_NONE
    free = platform_lock.probe_free(lock_path)
    if free is None:
        return HOLDER_UNKNOWN
    return HOLDER_NONE if free else HOLDER_LIVE


def _projected_step_status(run_dir: Path, item: Mapping[str, Any]) -> str:
    """The label for a `running` step whose run no live driver holds. READS ONLY; never writes.

    runrecon-02 (`fduoj4`) E-04. Before this, the projection had exactly two inputs (the item's status
    and the lock holder) and always produced `abandoned?`, whose question mark means "no live driver,
    but nothing recorded what happened". That sentence is FALSE for a step that DID record what
    happened: the measured incident's `outcomes/02-97df1z.json` says `substantially-complete` and names
    a commit, and this view called it `abandoned?` anyway while the answer sat in the same run
    directory. So the third input is the step's own recorded outcome, read through the SAME shared
    precedence the reconciler uses (`runner_shared.outcome_precedence_disposition`), never a second
    copy of those rules.

    IT MUTATES NOTHING, and that is settled precedent rather than a preference. `GUIDING_PRINCIPLES`
    P10 ("a read command must not mutate") is why executed plan `ssk6nf` REJECTED auto-repair on read
    and shipped the opt-in `aw runs repair` verb instead; this function reports a better-informed
    label and leaves `state.json` byte-for-byte untouched. Making the answer DURABLE remains the
    repair verb's job, and a test asserts both the content and the mtime of `state.json` across a read.

    THE `?` SUFFIX IS KEPT ON THE RECOVERED VALUE, deliberately. A bare `substantially-complete` here
    would be indistinguishable from a status the driver actually persisted, which is the exact
    confusion `ABANDONED`'s own comment exists to prevent. `persisted_status` still carries the real
    recorded value (`running`) in every case, so nothing is hidden either way.

    IT PASSES NO BUCKET, so the plan's directory plays no part here. The directory promotion is a
    reconciliation decision with an R22 gate on it, and a read surface must not reach a verdict that
    gate governs; consulting the outcome file alone cannot promote anything to `executed`, because the
    shared precedence downgrades a self-claimed `executed` to `substantially-complete`. An INDETERMINATE
    step is left at `abandoned?` for the same reason the reconciler refuses to recover it.
    """

    from agent_workflows import runner_shared, runner_stop

    if runner_stop.is_indeterminate(item):
        return ABANDONED
    if item.get("action", "execute") in ("review", "orchestrate"):
        return ABANDONED
    outcome = runner_shared.read_recorded_outcome(Path(run_dir), item)
    recovered = runner_shared.outcome_precedence_disposition(None, outcome)
    if recovered is None:
        return ABANDONED
    return f"{recovered}{PROJECTION_SUFFIX}"


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
    exec_cost: float | None = None
    exec_tokens: dict[str, int] = field(default_factory=dict)
    verify_cost: float | None = None
    verify_tokens: dict[str, int] = field(default_factory=dict)
    is_live: bool = False
    elapsed_seconds: float | None = None
    elapsed_str: str | None = None
    # THE TIME BOUND FOR THE ARTIFACT AUDIT'S EVIDENCE CHECK (IPD `zexed1` E-02): the git HEAD as it
    # stood when this item's LAST attempt ended, read straight off the run record's `attempts[]` (both
    # drivers write it; measured at review, 103 of 143 run records and 439 of 491 attempts carry it).
    # It answers "did a finalize happen AFTER this run recorded this status", which is the same
    # after-the-fact semantics the pre-commit gate gets from `HEAD..<incoming>`. An absent value is an
    # honest `unknown`, never a licence to fall back to an unbounded reachable-from-HEAD check.
    ending_head: str | None = None
    # orchprobe (r2i1b1) E-04/E-05: the refusal the run recorded for this step, as the JSON-safe
    # mapping `render_stream.Refusal.to_dict` produces (`code`/`reason`/`remedy`). Carried as a plain
    # dict rather than the dataclass so `dataclasses.asdict` renders it directly into the `--json` and
    # `--agent` payloads as DISCRETE FIELDS; read it through `step_refusal`, never by hand.
    refusal: dict[str, str] | None = None
    # runverdict (bxx9af) E-07: verifier evidence (tests_run / corrections_made) surfaced in StepSummary
    tests_run: list[Any] = field(default_factory=list)
    corrections_made: list[str] = field(default_factory=list)

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
    exec_cost: float | None = None
    exec_tokens: dict[str, int] = field(default_factory=dict)
    verify_cost: float | None = None
    verify_tokens: dict[str, int] = field(default_factory=dict)
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
    """Format duration seconds into a human-readable string (e.g. '12.4s', '4m 12s', '1h 04m 12s', '1d 03h 07m 56s')."""
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
    if hrs < 24:
        return f"{hrs}h {rem_mins:02d}m {rem_secs:02d}s"
    days = int(hrs // 24)
    rem_hrs = int(hrs % 24)
    return f"{days}d {rem_hrs}h {rem_mins:02d}m {rem_secs:02d}s"


def format_step_duration(seconds: float | None) -> str:
    """Format step duration seconds into 'HH:MM:SS' or 'Nd HH:MM:SS' if >= 24h."""
    if seconds is None or seconds < 0:
        return "-"
    total_secs = int(round(seconds))
    days, rem = divmod(total_secs, 86400)
    hrs, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"


def _parse_iso_timestamp_utc(val: Any) -> datetime | None:
    if not val or not isinstance(val, str):
        return None
    try:
        cleaned = val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def extract_step_elapsed(
    item: dict[str, Any],
    *,
    is_live: bool = False,
    fallback_end: datetime | None = None,
    now: datetime | None = None,
) -> tuple[float | None, str | None]:
    """Extract cumulative elapsed duration for a queue item across its attempts.

    For finished attempts, computes (ended_at - started_at).
    For in-flight attempts, computes (now - started_at) if running/live.
    Returns (elapsed_seconds, elapsed_str) or (None, None) if not run.
    """
    attempts = item.get("attempts") or []
    if not attempts:
        return None, None

    now_dt = now or datetime.now(timezone.utc)
    total_sec = 0.0
    has_timing = False

    for att in attempts:
        if not isinstance(att, dict):
            continue
        st = _parse_iso_timestamp_utc(att.get("started_at"))
        et = _parse_iso_timestamp_utc(att.get("ended_at") or att.get("interrupted_at"))
        if st and et:
            has_timing = True
            total_sec += max(0.0, (et - st).total_seconds())
        elif st and not et:
            has_timing = True
            end_point = now_dt if is_live else (fallback_end or now_dt)
            total_sec += max(0.0, (end_point - st).total_seconds())

    if not has_timing:
        return None, None

    return total_sec, format_step_duration(total_sec)


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


# THE AUDIT PREDICATE AND ITS FILE LOOKUP LIVE IN `artifact_audit`, NOT HERE (IPD 6ltz1y E-02/E-03).
# `aw runs` and `aw doctor` must not compute artifact location/status drift two different ways, which
# is the same reason `render_stream` and `evaluate_review_finding_escalation` exist. These names are
# re-exported for the run viewer's own call sites (and its tests) and are the SAME OBJECTS as the
# owner's - asserted by object identity in `tests/test_artifact_audit.py`, following the
# `tests/test_runner_refork_guard.py` pattern, because a behavioral comparison passes against a copy.
#
# `StepArtifactAudit` is an ALIAS of `artifact_audit.ArtifactAudit`, whose `id6` field replaced the
# run-specific name `step_id6`; `find_artifact_file` is a thin path-returning shim over the shared
# lookup, which additionally reports an id6 COLLISION the old first-match-wins loop hid.
StepArtifactAudit = _audit.ArtifactAudit


def find_artifact_file(repo_root: Path, id6: str, stem: str) -> Path | None:
    """The artifact declaring ``id6`` (or named by ``stem``), or None. Thin shim over the shared
    lookup, kept because this module's callers want a bare path.

    Resolves through ``artifact_audit.find_artifact``, which consumes ``selectors`` instead of a
    private directory list: see that module's docstring for the two defects the private loop carried
    (a hardcoded plans+specs-only type set, and first-match-wins with no collision policy). An id6
    COLLISION returns None here rather than an arbitrary pick; a caller that needs to SEE the
    collision calls ``artifact_audit.find_artifact`` directly.
    """
    return _audit.find_artifact(repo_root, id6, stem).path


def step_issue_reasons(
    audit: _audit.ArtifactAudit,
    step: StepSummary | None = None,
) -> list[str]:
    """Every reason ``aw runs`` should report this step as an issue, most specific first.

    THE ONE PREDICATE, AND THE EXTRACTION WAS THE POINT (orchprobe r2i1b1 E-03/F-2). The same
    three-term expression ``missing_entirely or location_mismatch or status_mismatch`` was copied at
    FIVE sites: ``format_artifact_audit_summary``, ``render_steps_table``, and three ``run_viewer_cli``
    branches serving ``--json``, ``--agent --issues`` and human ``--issues``. Extending one copy is
    precisely how the surfaces come to DISAGREE, with the table saying YES while ``--json`` omits the
    same item, so the extraction landed BEFORE the extension rather than after it.

    TWO INDEPENDENT REASON CLASSES, which is why this returns a list rather than a bool:

    * an ARTIFACT DISCREPANCY, the original three terms, meaning the plan file is in the wrong
      DIRECTORY or its on-disk status disagrees with what the run recorded; and
    * a REFUSAL (E-04), meaning the run declined to do something for a SEMANTIC reason. Every one of
      these previously left the column reading ``no``, because all three original terms describe
      location drift and a refused item's artifact is typically exactly where it should be.
    """
    reasons: list[str] = []
    refusal = step_refusal(step) if step is not None else None
    if refusal is not None:
        reasons.append(f"refused: {refusal.reason}")
    if audit.missing_entirely:
        reasons.append("artifact missing")
    elif audit.location_mismatch:
        reasons.append("artifact in unexpected directory")
    if audit.status_mismatch:
        reasons.append("on-disk status disagrees with the run record")
    return reasons


def step_has_issue(
    audit: _audit.ArtifactAudit,
    step: StepSummary | None = None,
) -> bool:
    """True when ``aw runs`` should flag this step. The ONE predicate all five surfaces call.

    ``step`` is optional ONLY because ``format_artifact_audit_summary`` receives bare audits with no
    step in hand; pass it whenever available, since a refusal is recorded on the STEP and is invisible
    from the audit alone.
    """
    return bool(step_issue_reasons(audit, step))


def step_refusal(step: StepSummary | None) -> Refusal | None:
    """The refusal recorded for one step, or None.

    Reads through the SHARED reader (``render_stream.refusal_of_item``) rather than re-deriving the
    key, so this viewer cannot look under a name different from the one the runners write: that exact
    reader/writer split is the defect F-4 measured.
    """
    if step is None:
        return None
    return refusal_of_item({REFUSAL_KEY: step.refusal} if step.refusal else {})


def audit_step_artifact(
    step: StepSummary,
    repo_root: Path = Path("."),
    evidence: _audit.FinalizeEvidenceIndex | None = None,
) -> _audit.ArtifactAudit:
    """Audit a STEP's artifact location and status: the run-viewer-shaped adapter over the shared
    predicate.

    This adapter exists so the shared module never has to know what a ``StepSummary`` is (IPD 6ltz1y
    OQ-01): the audit takes primitive facts (id6, stem, configured path, status, liveness), and the
    step-to-primitives projection - including the ``setid-id6`` stem fallback - belongs to the run
    viewer, which owns the type. ``is_live`` is passed THROUGH to the shared predicate, which records
    it without deriving it; liveness comes from this module's own run-directory probe
    (``inspect_run_pid_and_runtime``) and nothing in the shared module can compute it.

    ``evidence`` is the ONE git-history index for the whole table (IPD `zexed1` E-02), built once by
    the caller and reused for every row; the step's own ``ending_head`` is the time bound. OMITTING it
    is safe and honest, not silently degrading: every forward row then classifies `unknown` with a
    reason saying no evidence index was supplied, so an omission can never read as a clean pass.
    """
    return _audit.audit_artifact(
        repo_root,
        step.id6,
        step.stem or (f"{step.setid}-{step.id6}" if step.setid else step.id6),
        status=step.status,
        configured_file=step.configured_file,
        is_live=step.is_live,
        evidence=evidence,
        ending_head=step.ending_head or "",
    )


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
                elif (
                    ev.get("type") == "agent_response"
                    or "usage" in ev
                    or (
                        isinstance(ev.get("step_update"), dict)
                        and "usage" in ev["step_update"]
                    )
                ):
                    step_data = (
                        ev.get("step_update")
                        if isinstance(ev.get("step_update"), dict)
                        else {}
                    )
                    usage = step_data.get("usage") or ev.get("usage") or {}
                    if isinstance(usage, dict):
                        has_tokens = True
                        inp = (
                            usage.get("input_tokens")
                            or usage.get("prompt_tokens")
                            or usage.get("input")
                            or 0
                        )
                        out = (
                            usage.get("output_tokens")
                            or usage.get("completion_tokens")
                            or usage.get("output")
                            or 0
                        )
                        cache_raw = (
                            usage.get("cache_read_tokens")
                            if "cache_read_tokens" in usage
                            else usage.get("cache") or 0
                        )
                        if isinstance(cache_raw, dict):
                            cache_val = (cache_raw.get("read") or 0) + (
                                cache_raw.get("write") or 0
                            )
                        elif isinstance(cache_raw, (int, float)):
                            cache_val = int(cache_raw)
                        else:
                            cache_val = 0
                        reasoning = (
                            usage.get("thinking_tokens")
                            or usage.get("reasoning_tokens")
                            or 0
                        )
                        tot = usage.get("total_tokens")
                        if tot is None:
                            tot = inp + out + cache_val
                        tokens_agg["total"] += int(tot)
                        tokens_agg["input"] += int(inp)
                        tokens_agg["output"] += int(out)
                        tokens_agg["cache"] += int(cache_val)
                        tokens_agg["reasoning"] += int(reasoning)
                    c = step_data.get("cost") or ev.get("cost")
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
) -> tuple[
    float | None,
    dict[str, int],
    float | None,
    dict[str, int],
    float | None,
    dict[str, int],
]:
    """Extract cumulative execution, verification, and total cost/token metrics for a queue item."""
    exec_cost: float | None = None
    exec_tokens: dict[str, int] = {}
    verify_cost: float | None = None
    verify_tokens: dict[str, int] = {}

    attempts = item.get("attempts") or []
    pos = item.get("position", 0)
    id6 = item.get("id6", "")

    for att_idx, att in enumerate(attempts):
        if not isinstance(att, dict):
            continue
        att_num = att.get("attempt") or (att_idx + 1)

        # Execution metrics
        att_cost = att.get("cost")
        att_toks = att.get("tokens")
        if att_cost is not None or att_toks:
            if att_cost is not None:
                exec_cost = (exec_cost or 0.0) + float(att_cost)
            if isinstance(att_toks, dict):
                for k, v in att_toks.items():
                    exec_tokens[k] = exec_tokens.get(k, 0) + int(v)
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
                        exec_cost = (exec_cost or 0.0) + c
                    if t:
                        for k, v in t.items():
                            exec_tokens[k] = exec_tokens.get(k, 0) + v

        # Verification metrics
        v_cost = att.get("verify_cost")
        v_toks = att.get("verify_tokens")
        if v_cost is not None or v_toks:
            if v_cost is not None:
                verify_cost = (verify_cost or 0.0) + float(v_cost)
            if isinstance(v_toks, dict):
                for k, v in v_toks.items():
                    verify_tokens[k] = verify_tokens.get(k, 0) + int(v)
        else:
            v_log_path = att.get("verify_log")
            v_file = None
            if v_log_path:
                vp = Path(v_log_path)
                if not vp.is_file() and not vp.is_absolute():
                    vp = run_dir / vp
                if vp.is_file():
                    v_file = vp
            if not v_file and run_dir.is_dir():
                sessions_dir = run_dir / "sessions"
                if sessions_dir.is_dir() and id6:
                    cand = (
                        sessions_dir / f"{pos:02d}-{id6}-attempt-{att_num}-verify.jsonl"
                    )
                    if cand.is_file():
                        v_file = cand
                    else:
                        matches = list(
                            sessions_dir.glob(f"*{id6}*attempt-{att_num}*verify*.jsonl")
                        )
                        if matches:
                            v_file = matches[0]
            if v_file and v_file.is_file():
                c, t = extract_log_metrics(v_file)
                if c is not None:
                    verify_cost = (verify_cost or 0.0) + c
                if t:
                    for k, v in t.items():
                        verify_tokens[k] = verify_tokens.get(k, 0) + v

    # Fallback to scanning run_dir / "sessions" if no attempts had logs
    if (
        exec_cost is None
        and not exec_tokens
        and verify_cost is None
        and not verify_tokens
        and run_dir.is_dir()
    ):
        sessions_dir = run_dir / "sessions"
        if sessions_dir.is_dir() and id6:
            candidates = list(sessions_dir.glob(f"{pos:02d}-{id6}*.jsonl"))
            if not candidates:
                candidates = list(sessions_dir.glob(f"*{id6}*.jsonl"))
            for sess_file in candidates:
                if "verify" in sess_file.name:
                    c, t = extract_log_metrics(sess_file)
                    if c is not None:
                        verify_cost = (verify_cost or 0.0) + c
                    if t:
                        for k, v in t.items():
                            verify_tokens[k] = verify_tokens.get(k, 0) + v
                else:
                    c, t = extract_log_metrics(sess_file)
                    if c is not None:
                        exec_cost = (exec_cost or 0.0) + c
                    if t:
                        for k, v in t.items():
                            exec_tokens[k] = exec_tokens.get(k, 0) + v

    total_cost: float | None = None
    if exec_cost is not None or verify_cost is not None:
        total_cost = round((exec_cost or 0.0) + (verify_cost or 0.0), 4)

    total_tokens: dict[str, int] = {}
    for k, v in exec_tokens.items():
        total_tokens[k] = total_tokens.get(k, 0) + v
    for k, v in verify_tokens.items():
        total_tokens[k] = total_tokens.get(k, 0) + v

    e_cost_res = round(exec_cost, 4) if exec_cost is not None else None
    v_cost_res = round(verify_cost, 4) if verify_cost is not None else None
    e_tok_res = {k: v for k, v in exec_tokens.items() if v > 0}
    v_tok_res = {k: v for k, v in verify_tokens.items() if v > 0}
    tot_tok_res = {k: v for k, v in total_tokens.items() if v > 0}

    return (
        total_cost,
        tot_tok_res,
        e_cost_res,
        e_tok_res,
        v_cost_res,
        v_tok_res,
    )


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
            driver_id = driver_info.get("id") if isinstance(driver_info, dict) else None
            if driver_id:
                if driver_id in ("oc_runipd", "opencode", "oc"):
                    driver_name = "OpenCode"
                elif driver_id in ("agy_runipd", "antigravity", "agy", "runagy"):
                    driver_name = "Antigravity"
                else:
                    driver_name = driver_id
            elif driver_path:
                if "oc_runipd" in driver_path:
                    driver_name = "OpenCode"
                elif "agy_runipd" in driver_path or "runagy" in driver_path:
                    driver_name = "Antigravity"
                else:
                    driver_name = Path(driver_path).stem

            queue = state.get("queue") or []
            set_set = set()
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
                if status == "running" and holder == HOLDER_NONE:
                    persisted_status = status
                    status = _projected_step_status(run_dir, item)
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
                step_ending_head = None
                if attempts and isinstance(attempts[-1], dict):
                    session_id = attempts[-1].get("session_id")
                    if not updated_at:
                        updated_at = attempts[-1].get("ended_at")
                # The LAST attempt's ending head: the artifact audit's evidence range starts where this
                # item's most recent attempt left the tree. Reading the last (not the first) attempt is
                # what makes a retried item's bound describe the run's final observation of it.
                for att in reversed(attempts):
                    if isinstance(att, dict) and att.get("ending_head"):
                        step_ending_head = str(att["ending_head"]).strip() or None
                        break

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

                (
                    step_cost,
                    step_toks,
                    step_e_cost,
                    step_e_toks,
                    step_v_cost,
                    step_v_toks,
                ) = extract_step_usage(item, run_dir)

                step_el_sec, step_el_str = extract_step_elapsed(
                    item,
                    is_live=(holder != HOLDER_NONE),
                    fallback_end=_parse_iso_timestamp_utc(updated_at),
                )

                item_tests_run = item.get("tests_run")
                item_corrections = item.get("corrections_made")
                if (item_tests_run is None or item_corrections is None) and run_dir:
                    v_outcome_file = (
                        run_dir / "outcomes" / f"{pos:02d}-{id6}-verification.json"
                    )
                    if v_outcome_file.is_file():
                        try:
                            _v_data = json.loads(
                                v_outcome_file.read_text(encoding="utf-8")
                            )
                            if item_tests_run is None:
                                item_tests_run = _v_data.get("tests_run")
                            if item_corrections is None:
                                item_corrections = _v_data.get("corrections_made")
                        except Exception:
                            pass
                tests_run_list = (
                    list(item_tests_run) if isinstance(item_tests_run, list) else []
                )
                corrections_list = (
                    [str(c) for c in item_corrections]
                    if isinstance(item_corrections, list)
                    else []
                )

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
                        exec_cost=step_e_cost,
                        exec_tokens=step_e_toks,
                        verify_cost=step_v_cost,
                        verify_tokens=step_v_toks,
                        elapsed_seconds=step_el_sec,
                        elapsed_str=step_el_str,
                        ending_head=step_ending_head,
                        # orchprobe (r2i1b1) E-04: read the refusal the runner recorded through the
                        # SHARED reader, which tolerates a run directory frozen before this record
                        # existed (it returns None) and normalizes a malformed one rather than raising.
                        refusal=(
                            _rf.to_dict()
                            if (_rf := refusal_of_item(item)) is not None
                            else None
                        ),
                        # runverdict (bxx9af) E-07: verifier evidence in StepSummary
                        tests_run=tests_run_list,
                        corrections_made=corrections_list,
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

                        (
                            step_cost,
                            step_toks,
                            step_e_cost,
                            step_e_toks,
                            step_v_cost,
                            step_v_toks,
                        ) = extract_step_usage({"position": pos, "id6": id6}, run_dir)

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
                                exec_cost=step_e_cost,
                                exec_tokens=step_e_toks,
                                verify_cost=step_v_cost,
                                verify_tokens=step_v_toks,
                            )
                        )
        except (OSError, ValueError, IndexError):
            pass

    total_cost: float | None = None
    total_tokens: dict[str, int] = {}
    exec_cost: float | None = None
    exec_tokens: dict[str, int] = {}
    verify_cost: float | None = None
    verify_tokens: dict[str, int] = {}

    for s in steps:
        if s.cost is not None:
            total_cost = (total_cost or 0.0) + s.cost
        if s.tokens:
            for k, v in s.tokens.items():
                total_tokens[k] = total_tokens.get(k, 0) + v
        if s.exec_cost is not None:
            exec_cost = (exec_cost or 0.0) + s.exec_cost
        if s.exec_tokens:
            for k, v in s.exec_tokens.items():
                exec_tokens[k] = exec_tokens.get(k, 0) + v
        if s.verify_cost is not None:
            verify_cost = (verify_cost or 0.0) + s.verify_cost
        if s.verify_tokens:
            for k, v in s.verify_tokens.items():
                verify_tokens[k] = verify_tokens.get(k, 0) + v

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

    if is_live:
        for s in steps:
            s.is_live = True

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
        exec_cost=round(exec_cost, 4) if exec_cost is not None else None,
        exec_tokens=exec_tokens if exec_tokens else {},
        verify_cost=round(verify_cost, 4) if verify_cost is not None else None,
        verify_tokens=verify_tokens if verify_tokens else {},
        pid=pid,
        pid_state=pid_state,
        is_live=is_live,
        runtime_seconds=runtime_seconds,
        runtime_str=runtime_str,
    )


def discover_run_dirs(repo_root: Path = Path(".")) -> list[Path]:
    """Discover all run directories across canonical and legacy record roots."""
    roots = [
        state_root(repo_root),
        repo_root / ".aw" / "runs",
        repo_root / ".agents" / "runs",
    ]
    seen = set()
    found = []
    a_roots: set[Path] = set()
    try:
        a_roots.add(analytics_root(repo_root).resolve())
    except Exception:
        pass
    a_roots.add((repo_root / ".aw" / "runs" / ANALYTICS_DIRNAME).resolve())
    a_roots.add((repo_root / ".agents" / "runs" / ANALYTICS_DIRNAME).resolve())

    for r in roots:
        if r.is_dir():
            for p in sorted(r.iterdir()):
                if (
                    p.is_dir()
                    and p.name.startswith("run-")
                    and p.name != ANALYTICS_DIRNAME
                    and p.resolve() not in a_roots
                    and p.name not in seen
                ):
                    seen.add(p.name)
                    found.append(p)
    return found


def _state_setids(run_dir: Path) -> set[str]:
    """The Set ids a run's `state.json` actually declares, read from the setid FIELDS.

    runsverify 7wei1o E-07. This replaces a raw substring test over the whole file
    (``if f'"{t_str}"' in content``), which matched any quoted JSON KEY or VALUE anywhere and so
    resolved ordinary tokens to nearly every run in the repository. Measured against 106 live run
    records before the fix: ``status``, ``run``, ``opencode``, ``driver``, ``run_id`` and
    ``options`` each resolved 106 of 106, ``clean`` 105, ``main`` 96, ``json`` 79, ``execute`` 53,
    ``approved`` 46, ``verified`` 13. None of those is a Set id.

    That over-matching is LOAD-BEARING for the unresolvable-target refusal, not cosmetic: a token
    that "resolves" to every run is never unresolved, so it would be silently EXEMPTED from the
    refusal and keep reporting success. Reading the field instead of the text is what makes the
    refusal reachable.

    Reads the same two places ``load_run_summary`` does, so the resolver and the renderer cannot
    disagree about what a run's Set is: each queue item's ``setid``, plus the run-level
    ``selectors`` (the Set ids the run was LAUNCHED with, which a queue emptied by dependency
    blocking would otherwise lose).
    """
    s_file = run_dir / "state.json"
    if not s_file.is_file():
        return set()
    try:
        state = json.loads(s_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return set()
    if not isinstance(state, dict):
        return set()

    found: set[str] = set()
    queue = state.get("queue")
    if isinstance(queue, list):
        for item in queue:
            if isinstance(item, dict):
                setid = item.get("setid")
                if isinstance(setid, str) and setid.strip():
                    found.add(setid.strip())
    for key in ("selectors", "setids"):
        vals = state.get(key)
        if isinstance(vals, list):
            for v in vals:
                if isinstance(v, str) and v.strip():
                    found.add(v.strip())
        elif isinstance(vals, str) and vals.strip():
            found.add(vals.strip())
    setid = state.get("setid")
    if isinstance(setid, str) and setid.strip():
        found.add(setid.strip())
    return found


def resolve_target_runs_detailed(
    targets: Sequence[str | Path] | None = None,
    repo_root: Path = Path("."),
) -> tuple[list[Path], list[str]]:
    """Resolve targets to run directories AND report which requested tokens matched NOTHING.

    runsverify 7wei1o E-01. Returns ``(resolved, unresolved)``:

      * ``resolved``   - the union of matched run directories, in discovery order per token
                         (exactly what ``resolve_target_runs`` returns).
      * ``unresolved`` - the requested tokens that matched no run at all, in the order given.

    WHY THIS FUNCTION EXISTS: the union alone cannot distinguish "you asked for nothing specific"
    from "everything you asked for is missing", because both arrive at the caller as an empty (or
    partial) list. That ambiguity is the whole defect: ``aw runs verify <run-id>`` dropped the
    unmatched ``verify`` token, rendered the run, and exited 0, so an operator asking for an
    integrity check got a normal-looking report. One function owns the answer so no caller
    re-derives it and drifts.

    A bare call (no tokens) returns ``(all_runs, [])``: asking for EVERYTHING and finding nothing
    is a legitimate empty repository, not a failed request.
    """
    all_runs = discover_run_dirs(repo_root)

    if not targets:
        return all_runs, []

    resolved: list[Path] = []
    seen = set()
    unresolved: list[str] = []

    for target in targets:
        t_str = str(target).strip()
        if not t_str:
            continue

        p = Path(t_str)
        if p.is_dir() and (p / "state.json").is_file():
            if path_is_within_analytics(p, repo_root):
                unresolved.append(t_str)
                continue
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
            if path_is_within_analytics(p.parent, repo_root):
                unresolved.append(t_str)
                continue
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
            # Check if the target names a Set the run declares (setid FIELDS, not raw text).
            for run_p in all_runs:
                if t_str in _state_setids(run_p):
                    canon = run_p.resolve()
                    if canon not in seen:
                        seen.add(canon)
                        resolved.append(run_p)
                    matched = True

        if not matched:
            unresolved.append(t_str)

    return resolved, unresolved


def resolve_target_runs(
    targets: Sequence[str | Path] | None = None,
    repo_root: Path = Path("."),
) -> list[Path]:
    """Resolve user-specified targets (directories, run_ids, setids, or substrings) to concrete run directories.

    The union only. A caller that must distinguish an UNRESOLVABLE token from an absent one (so it
    can refuse instead of silently reporting success) wants ``resolve_target_runs_detailed``.
    """
    return resolve_target_runs_detailed(targets, repo_root)[0]


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


# ======================================================================================
# The lifecycle resolution seam (spec `uonrjg` R10.3, Sections 7.2 and 7.3)
# ======================================================================================
#
# EVERY LIFECYCLE COLOR AND GLYPH IN THIS MODULE COMES THROUGH THE TWO HELPERS BELOW, and that is
# the property criterion A17 asserts. Before plan `9zvl2w` E-04 this module resolved lifecycle
# presentation TWO ways: four `Term.status_256` calls (which read `term.STATUS_COLOR_256`) and a
# handful of DIRECT `term.color256(..., <literal>)` calls that bypassed every table. Four of those
# literals CONTRADICTED spec Section 5, measured 2026-09-19:
#
#   :1628  "[in flight]"     214  ->  the spec's `active` is 220; 214 is `waiting-input` ONLY
#   :1847  "YES (in flight)" 214  ->  same collapse, in the audit table
#   :1401  "[review]"        226  ->  226 is not one of Section 5's eleven indices at all
#   :1995  "[<pid state>]"    40  ->  40 is not one of them either; live/`ready` is 45
#
# So the run views painted IN-FLIGHT WORK the exact color the spec reserves for "a human is being
# asked a question", which is the confusion Section 5's fixed palette exists to prevent. Two of the
# literals happened to be right (`[verified]` 46 = `done`, `[verify-failed]` 196 = `failed`) and
# that is worse than wrong, not better: they agreed by luck, nothing held them to the table, and the
# next palette change would have silently broken them.
#
# THE GENERIC CALLS ARE DELIBERATELY LEFT ALONE, because R10.3 says so in terms and criterion A18
# tests for it. Cost (`220`), run ids and headers (`33`), elapsed/summary/token dimming (`245`),
# audit DIFFERENCE CLASSES (`_AUDIT_CLASS_COLOR`, an independent vocabulary owned by
# `artifact_audit`), refusal/remedy severity, phase names, and the `yes`/`no`/`YES` ISSUE column are
# formatting and severity, NOT artifact lifecycle state. Remapping them would be exactly the
# "mechanically replace every checkmark" mistake R10.3 warns against.


def _resolve_item_status(
    native_status: str | None, *, action: str | None = None
) -> _LS.Resolved:
    """Resolve a RUNNER ITEM status (spec Section 7.2) through the shared resolver.

    ``action`` is passed as the ACTIVITY only for a genuinely running item, which is what Section
    7.2's `running` row asks for ("action-aware activity from 7.1, otherwise active"): a `review`
    action in flight displays `reviewing` (`◎`) rather than generic `active` (`●`). It is NOT passed
    for a settled item, because the activity overlay OUTRANKS the native mapping in Section 8's
    precedence, so handing it an action unconditionally would paint every finished row as though its
    work were still running - the stale-runtime-field failure criterion A8 exists to catch.

    AN ACTION THE ACTIVITY TABLE DOES NOT KNOW IS DROPPED RATHER THAN PASSED, and that guard is not
    hypothetical: `runner_shared.ACTION_CHOICES` is `('review', 'plan', 'execute')`, and measured
    2026-09-20 `lifecycle_style.ACTIVITY_FROM_ACTION` maps `review` and `execute` but NOT `plan`. An
    unrecognized activity resolves `unknown` WITH a diagnostic (Section 8 rung 4), which is correct
    for a validation boundary and wrong for this view: a running `plan` item would have printed `?`
    instead of the generic `active` its native `running` status already earns. Section 7.2's own
    wording is "action-aware activity from 7.1, OTHERWISE active", so falling back is what the spec
    asks for. This is a RENDERING fallback only; it neither widens the activity table nor hides the
    gap, which stays visible in the resolver's diagnostic for any caller that asks for it.
    """

    token = (native_status or "").strip().lower()
    activity = None
    if token in ("running", "in-flight", "in_flight") and action:
        action_token = str(action).strip().lower()
        if (
            action_token in _LS.ACTIVITY_FROM_ACTION
            or action_token in _LS.ACTIVITY_STAGES
        ):
            activity = action_token
    return _T.resolve_lifecycle(
        _LS.FAMILY_RUNNER_ITEM, native_status, activity=activity
    )


def _resolve_ledger_status(native_status: str | None) -> _LS.Resolved:
    """Resolve a RUN LEDGER or SET state (spec Section 7.3) through the shared resolver.

    Kept separate from :func:`_resolve_item_status` because Section 7.3 is a DIFFERENT owner enum with
    a different key set (`run_state` owns the bare words, `set_state` prefixes its own), and one
    function taking a family argument would invite a caller to guess. `performed` resolving to
    `verifying` rather than `done` is the distinction that matters most here: unverified completion
    MUST NOT be styled as verified success.
    """

    return _T.resolve_lifecycle(_LS.FAMILY_RUN_LEDGER, native_status)


def format_step_line(
    step: StepSummary,
    term: Term,
    long: bool = False,
    status_width: int = 18,
    stem_width: int = 0,
) -> str:
    """Format a single step summary line aligned with aw att / aw ipd lint style."""
    status_word = canonical_terminal_status(step.status)

    # THE RUNNER ITEM STATUS THROUGH THE SHARED RESOLVER (plan `9zvl2w` E-04, spec `uonrjg` Section
    # 7.2, R10.3). This is what makes `ran` render `recovering` (`↩︎`, amber) rather than a success
    # green, and `unknown_outcome` render `failed` rather than the lookup-failure `?`: both were
    # decided in Section 7.2 and neither is reachable through the old `STATUS_COLOR_256` table, which
    # has no entry for either word and so painted both neutral gray.
    status_resolved = _resolve_item_status(step.status, action=step.action)
    status_marker = term.format_lifecycle_marker(status_resolved, width=2)
    status_padded = (
        status_marker
        + " "
        + term.style_lifecycle_text(status_word, status_resolved)
        # PADDED BY VISIBLE COLUMNS (Section 9.4), never `len()` on styled text.
        + (" " * max(0, status_width - _T.visible_width(status_word)))
    )

    lead = "   "
    # PLAIN TYPE WORD (criterion A10, Section 9.1: "The artifact type and title do not inherit
    # lifecycle color"). It was `attention._TREE_COLOR_256` bold, the same violation `f9t5hz` removed
    # from the attention rows; Section 11 item 5's exemption covers a path SEGMENT, not a bare word.
    type_word = "plan"
    type_prefix = type_word + (" " * max(0, 8 - len(type_word))) + "  "

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
    # THE TWO VERIFICATION BADGES ARE LIFECYCLE STATE and were the pair that matched Section 5 BY
    # LUCK (`46` = `done`, `196` = `failed`). Agreeing by coincidence is not a property, it is an
    # unheld invariant, so both are resolved through the shared table: the rendered bytes are
    # unchanged today and can no longer drift from the spec tomorrow.
    if step.verification_status == "verified":
        badges.append(
            term.style_lifecycle_text("[verified]", _resolve_item_status("verified"))
        )
    elif step.verification_status == "failed":
        badges.append(
            term.style_lifecycle_text("[verify-failed]", _resolve_item_status("failed"))
        )
    if step.cost is not None:
        cost_str = f"${step.cost:.2f}"
        badges.append(
            term.color256(f"[{cost_str}]", 220)
            if getattr(term, "color", False)
            else f"[{cost_str}]"
        )
    if step.action == "review":
        # THE `[review]` BADGE NAMES A LIFECYCLE ACTIVITY and took a HARDCODED 226 that is not one of
        # spec Section 5's eleven indices at all (F-07). The spec's `reviewing` stage is 220, and it
        # is resolved here through the shared ACTIVITY overlay (Section 7.1) rather than by looking up
        # the word, because `review` is an ACTION this run performed and not a stored status.
        review_resolved = _T.resolve_lifecycle(
            _LS.FAMILY_RUNNER_ITEM, None, activity="review"
        )
        badges.append(term.style_lifecycle_text("[review]", review_resolved))

    badge_txt = ("  " + "  ".join(badges)) if badges else ""

    disp_txt = ""
    if step.disposition and step.disposition not in (step.status, status_word):
        # A RUN ITEM DISPOSITION IS SECTION 7.2 VOCABULARY, not a generic outcome word, which is the
        # difference between this column and `ipd_lint`'s same-named one. Every value it holds
        # (`executed`, `partial`, `dependency-blocked`, `failed-safely`, `unknown_outcome`, ...) is a
        # row in that table, so the WHOLE column converts. `unknown_outcome` in particular now renders
        # `failed` per Section 7.2 rather than the neutral gray the old table's missing key gave it.
        disp_resolved = _resolve_item_status(step.disposition)
        disp_styled = term.style_lifecycle_text(step.disposition, disp_resolved)
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

    hdr_lines_list = [str(h).splitlines() if str(h) else [""] for h in headers]
    max_hdr_lines = max((len(lines) for lines in hdr_lines_list), default=1)

    col_widths = [
        max((len(line) for line in lines), default=0) for lines in hdr_lines_list
    ]
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

    for l_idx in range(max_hdr_lines):
        hdr_cells = []
        for c_idx, (h_lines, w, align) in enumerate(
            zip(hdr_lines_list, col_widths, aligns)
        ):
            h_line = h_lines[l_idx] if l_idx < len(h_lines) else ""
            h_styled = (
                term.colorize(h_line, "bold")
                if (h_line and getattr(term, "color", False))
                else h_line
            )
            pad = w - len(h_line)
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


def audit_row_is_issue(audit: StepArtifactAudit) -> bool:
    """THE one definition of "is this audit row an issue", consulted by every call site.

    ONE DEFINITION, NOT SIX (IPD `zexed1` E-05). The boolean triple was tested in FIVE hand-written
    places - the discrepancy table's row selection, the steps table's `Issue` column, `--json`,
    `--agent`, and the `--issues` human path - and hand-copying a SIX-VALUE classification into five
    places would have been strictly worse than the boolean version it replaced.

    THE ROW SET IS DELIBERATELY UNCHANGED: this delegates to the shipped
    `artifact_audit.ArtifactAudit.has_discrepancy`, so exactly the rows that were candidates before are
    candidates now. That matters because two of the five call sites emit PUBLISHED `aw.agent` records:
    narrowing the predicate would silently change what a machine consumer receives, which is beyond
    this plan's remit (`zexed1` "Deferred / out of scope": shrinking the table's row count). What the
    classification changes is how a selected row is CLASSIFIED and STYLED.

    RESOLVED 2026-09-14, when `r2i1b1` (`orchprobe-01`) was merged alongside this lane. Both survive
    and they are NOT competitors, because they answer different questions:

      * `audit_row_is_issue(audit)` -- ARTIFACT-ONLY. Kept deliberately narrow so the PUBLISHED row
        set is provably unchanged, which is what `test_the_published_row_set_is_unchanged` and
        `test_the_one_definition_delegates_to_the_dataclass` pin (both assert equality with
        `has_discrepancy` for every boolean combination). This is the predicate the CLASSIFICATION
        surfaces use, where a row must be selected before it can be classified and styled.
      * `step_has_issue(audit, step)` -- WIDER: refusal OR discrepancy. It is a strict superset and is
        what every ISSUE-REPORTING surface now calls (the steps table's `Issue` column, `--json`,
        `--agent`, and the `--issues` human path), because a refusal is recorded on the STEP and is
        invisible from the audit alone.

    So this function is no longer "the one definition" for the issue QUESTION; it is the one definition
    of ARTIFACT DISCREPANCY, which `step_has_issue` itself consults. Do not collapse the two: doing so
    would either narrow the refusal-aware surfaces or silently widen the published machine row set,
    and each is a defect one of the two lanes exists to prevent.
    """
    return audit.has_discrepancy


def summarize_audit_classes(audits: Sequence[StepArtifactAudit]) -> dict[str, int]:
    """Per-class counts over the ISSUE rows, in :data:`_audit.ALL_CLASSES` report order.

    Exists because this change does NOT shrink the row count (IPD `zexed1` E-04, review PR-206): the
    selection predicate still admits every non-agreeing row, so a reader who saw hundreds of red rows
    now sees hundreds of rows in several colors. That is an improvement in HONESTY and not yet one in
    USABILITY, so the shape has to be legible without reading every row.
    """
    counts = {cls: 0 for cls in _audit.ALL_CLASSES}
    for a in audits:
        if not audit_row_is_issue(a):
            continue
        counts[a.difference_class] = counts.get(a.difference_class, 0) + 1
    return counts


def format_artifact_audit_summary(
    audits: list[StepArtifactAudit],
    term: Term,
    all_classes: bool = False,
    steps: list[StepSummary] | None = None,
) -> str:
    """Format artifact location/status discrepancies CLASSIFIED BY DIRECTION, plus any REFUSALS.

    ``all_classes`` restores the rows suppressed by default. THE DEFAULT SUPPRESSES `resolved` AND
    `retired` ONLY, with their counts still printed (IPD `zexed1` E-04, OQ-01): both classes HAVE
    evidence behind them, and at the review-measured distribution 446 of 508 rows fell into them, so
    leaving them in kept the table unreadable and defeated the change's purpose.

    THERE IS NO SUPPRESSION PATH FOR `unknown` OR `regressed`, under this flag or any other. `unknown`
    is a CONFESSION that this audit could not prove the difference either way, and an invisible
    confession is indistinguishable from a clean pass to every reader; refusing that is the entire
    point of the 2026-09-05 maintainer ruling this classification was built to satisfy.

    ``steps`` is optional and additive (orchprobe r2i1b1 E-04): passed, this reports a refused item
    even when its artifact sits exactly where it belongs, which is the normal case for a semantic
    refusal and is why every such item previously left this table empty. Omitted, the refusal block
    is empty and the artifact table is unchanged.
    """
    seen: set[str] = set()
    issues: list[StepArtifactAudit] = []
    for a in audits:
        key = a.id6 or a.stem
        if key in seen:
            continue
        seen.add(key)
        # orchprobe (r2i1b1) E-03: through the ONE predicate. This site receives bare audits with no
        # step in hand, so it cannot see a refusal; a refused item reaches the REFUSALS block below
        # through the `steps` argument instead.
        if audit_row_is_issue(a):
            issues.append(a)

    counts = summarize_audit_classes(issues)
    if all_classes:
        discrepancies = issues
    else:
        discrepancies = [
            a for a in issues if a.difference_class not in _audit.SUPPRESSIBLE_CLASSES
        ]

    count_line = format_audit_class_counts(counts, term, suppressed=not all_classes)

    refusal_block = format_refusal_summary(steps or [], term)

    if not discrepancies:
        # The counts still print. A table with no ALARMING and no UNKNOWN row, but hundreds of
        # evidenced `resolved` ones, is a genuinely clean result and must SAY so with its numbers
        # rather than render as silence (which reads as "the audit did not run"). The refusal block
        # is joined UNCONDITIONALLY: a refused item commonly has NO artifact discrepancy at all
        # (r2i1b1 E-04), so returning early without it is exactly the silence that defect describes.
        tail = count_line if any(counts.values()) else ""
        return "\n".join(x for x in (tail, refusal_block) if x)

    headers = [
        "Item",
        "Class",
        "Expected\nLocation",
        "Actual\nLocation",
        "Expected\nStatus",
        "Actual\nStatus",
        "Why",
    ]
    aligns = ["left", "left", "left", "left", "left", "left", "left"]
    rows = []

    for a in discrepancies:
        raw_item_id = a.stem or a.id6
        if a.is_live:
            # `[in flight]` MEANS WORK IS RUNNING, and it took a hardcoded 214 - which in spec Section
            # 5 means `waiting-input` ONLY, i.e. "a human is being asked". The spec's stage for live
            # work whose subtype is unavailable is `active` (220). This row knows the item is live but
            # not WHAT it is doing, so generic `active` is the honest resolution.
            flag_txt = term.style_lifecycle_text(
                "[in flight]", _resolve_item_status("running")
            )
            item_id = f"{raw_item_id} {flag_txt}"
        else:
            item_id = raw_item_id

        # THE STYLING NOW FOLLOWS THE CLASS, NOT THE BOOLEANS. Reserving red for a difference that
        # indicates something actually wrong is the whole point: a red block that is mostly false
        # trains an operator to skim past the rows that matter.
        alarming = a.difference_class in _audit.ALARMING_CLASSES
        cls_color = _AUDIT_CLASS_COLOR.get(a.difference_class, 250)
        cls_disp = (
            term.color256(a.difference_class, cls_color, bold=alarming)
            if getattr(term, "color", False)
            else a.difference_class
        )

        def _styled(text: str) -> str:
            if not getattr(term, "color", False):
                return text
            return term.color256(text, cls_color, bold=alarming)

        exp_loc = f"{a.expected_dir}/" if a.expected_dir else "-"
        if a.missing_entirely:
            act_loc_disp = _styled("missing")
        else:
            act_loc_raw = f"{a.actual_dir}/" if a.actual_dir else "-"
            act_loc_disp = _styled(act_loc_raw) if a.location_mismatch else act_loc_raw

        exp_st = a.run_status or "-"
        if a.missing_entirely:
            act_st_disp = _styled("-")
        else:
            act_st_raw = a.file_status or "-"
            act_st_disp = _styled(act_st_raw) if a.status_mismatch else act_st_raw

        rows.append(
            [
                item_id,
                cls_disp,
                exp_loc,
                act_loc_disp,
                exp_st,
                act_st_disp,
                a.class_reason or "-",
            ]
        )

    title = "Artifact & Status Differences"
    table = render_box_table(title, headers, rows, term, aligns)
    body = f"{count_line}\n{table}" if count_line else table
    return f"{body}\n\n{refusal_block}" if refusal_block else body


#: Per-class row color. `regressed`/`missing` keep the alarming red the boolean version used for every
#: row; `unknown` is amber (visible, unproven, NOT an accusation); `resolved`/`retired`/`unchanged` are
#: non-alarming.
_AUDIT_CLASS_COLOR: dict[str, int] = {
    _audit.CLASS_REGRESSED: 196,
    _audit.CLASS_MISSING: 196,
    _audit.CLASS_UNKNOWN: 214,
    _audit.CLASS_RESOLVED: 46,
    _audit.CLASS_RETIRED: 245,
    _audit.CLASS_UNCHANGED: 46,
}


def format_audit_class_counts(
    counts: dict[str, int], term: Term, suppressed: bool = False
) -> str:
    """One line naming each non-zero class and its count, plus how to see the suppressed rows."""
    parts: list[str] = []
    for cls in _audit.ALL_CLASSES:
        n = counts.get(cls, 0)
        if not n:
            continue
        color = _AUDIT_CLASS_COLOR.get(cls, 250)
        label = f"{cls} {n}"
        parts.append(
            term.color256(label, color, bold=cls in _audit.ALARMING_CLASSES)
            if getattr(term, "color", False)
            else label
        )
    if not parts:
        return ""
    line = "artifact differences: " + "  ".join(parts)
    hidden = sum(counts.get(c, 0) for c in _audit.SUPPRESSIBLE_CLASSES)
    if suppressed and hidden:
        line += f"  ({hidden} evidenced rows hidden; --all-classes shows them)"
    return line


def format_refusal_summary(steps: list[StepSummary], term: Term) -> str:
    """The REFUSALS block: what the run declined, why, and WHAT TO DO ABOUT IT.

    RENDERED WITHOUT ANY FLAG (orchprobe r2i1b1 E-05/F-5). `render_step_details` runs only under
    ``if detail:``, so a remedy placed only there leaves the default ``aw runs`` showing ``Issue: YES``
    while never saying why or what to do, which defeats the purpose: the reader who most needs the
    remedy is the one who just saw YES with no flag.

    THE REMEDY IS WHY THIS BLOCK EXISTS AT ALL, not decoration. `AGENTS.md` records the measured
    failure mode: a refusal that names only the prohibition gets complied with by DELETION, so a
    message like "abd123 contains items that are not allowed" plausibly gets fixed by deleting items
    someone thought important enough to write. Every line here therefore pairs the reason with the
    constructive action.
    """
    refused: list[tuple[StepSummary, Refusal]] = []
    seen: set[str] = set()
    for st in steps:
        rf = step_refusal(st)
        if rf is None:
            continue
        key = st.id6 or st.stem
        if key in seen:
            continue
        seen.add(key)
        refused.append((st, rf))

    if not refused:
        return ""

    def _c(text: str, color: int, bold: bool = False) -> str:
        return (
            term.color256(text, color, bold=bold)
            if getattr(term, "color", False)
            else text
        )

    lines = [_c("Refusals (what the run declined, and what to do):", 214, bold=True)]
    for st, rf in refused:
        ident = st.stem or (f"{st.setid}-{st.id6}" if st.setid else st.id6)
        lines.append(f"  {_c('!', 196, bold=True)} {ident} [{rf.code}]: {rf.reason}")
        lines.append(f"    {_c('→ remedy:', 46, bold=True)} {rf.remedy}")
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
        headers = ["Status", "Landed", "Item", "Action", "Verified", "Issue"]
        aligns = ["left", "left", "left", "left", "left", "left"]
    else:
        headers = [
            "Status",
            "Landed",
            "Item",
            "Action",
            "Attempts",
            "Elapsed",
            "Cost",
            "Total Tok",
            "Verified",
            "Issue",
        ]
        aligns = [
            "left",
            "left",
            "left",
            "left",
            "right",
            "right",
            "right",
            "right",
            "left",
            "left",
        ]
    rows = []
    for step in steps:
        audit = audit_step_artifact(step, repo_root)
        st_disp = canonical_terminal_status(step.status)
        # THE AUDIT TABLE'S Status COLUMN, through the shared resolver (R10.3). Deliberately WITHOUT a
        # glyph: `render_box_table` measures every cell with `len(strip_ansi(cell))`, not by rendered
        # width, so a 2-code-point / 1-column grapheme (`⚠︎`, `↩︎`) would over-count its column by one
        # and skew the box art. Section 11 item 2 makes that trade safe - glyph and color are
        # REDUNDANT cues, either may be dropped - and the native word, which Section 0 makes the
        # authority, is present in the cell either way.
        st_resolved = _resolve_item_status(step.status, action=step.action)
        st_styled = term.style_lifecycle_text(st_disp, st_resolved)

        # Landed column derived from the plan's terminal directory on disk (statusvocab 9x7otz)
        l_verdict = landed_verdict(audit)
        if l_verdict == "yes":
            landed_disp = (
                term.color256("yes", 46) if getattr(term, "color", False) else "yes"
            )
        elif l_verdict == "no":
            landed_disp = (
                term.color256("no", 196) if getattr(term, "color", False) else "no"
            )
        elif l_verdict == "n/a":
            landed_disp = (
                term.color256("n/a", 245) if getattr(term, "color", False) else "n/a"
            )
        else:
            landed_disp = (
                term.color256("unknown", 214)
                if getattr(term, "color", False)
                else "unknown"
            )

        item_disp = step.stem or (
            f"{step.setid}-{step.id6}" if step.setid else step.id6
        )

        att_disp = str(step.attempts_count) if step.attempts_count else "-"
        elapsed_disp = step.elapsed_str or "-"
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

        # ONE definition of "is this row an issue" (IPD `zexed1` E-05, IPD `r2i1b1` E-03/E-04), not a
        # fourth hand-written copy. Called WITH the step so a semantic refusal reads YES here instead
        # of `no`: the three original terms all describe a plan being in the wrong DIRECTORY, so a
        # refused item whose artifact is exactly where it belongs used to leave this column `no`.
        # `step_has_issue` is the wider predicate (refusal OR discrepancy) and subsumes
        # `audit_row_is_issue`, which `zexed1` wrote anticipating exactly this merge.
        has_issue = step_has_issue(audit, step)
        if has_issue:
            if audit.is_live:
                # THE LIVE VARIANT IS STYLED AS LIFECYCLE `active`, NOT AS SEVERITY, and that keeps the
                # column's existing intent while removing its palette collision. The whole cell took a
                # hardcoded 214, which spec Section 5 reserves for `waiting-input` ("a human is being
                # asked") - so a row that merely had work RUNNING wore the color that means a question
                # is outstanding. The deliberate design here is that a live row is DE-ESCALATED (amber,
                # not the red the settled `YES` gets) because the discrepancy is expected while work is
                # in flight; `active` (220) preserves exactly that and is the spec's stage for it.
                # The plain `YES`/`no` verdicts below stay GENERIC severity, per R10.3 and criterion
                # A18: an issue verdict is not an artifact lifecycle state.
                issue_disp = term.style_lifecycle_text(
                    "YES (in flight)", _resolve_item_status("running")
                )
            else:
                issue_disp = (
                    term.color256("YES", 196, bold=True)
                    if getattr(term, "color", False)
                    else "YES"
                )
        else:
            issue_disp = (
                term.color256("no", 46) if getattr(term, "color", False) else "no"
            )

        if short:
            rows.append(
                [st_styled, landed_disp, item_disp, step.action, v_disp, issue_disp]
            )
        else:
            rows.append(
                [
                    st_styled,
                    landed_disp,
                    item_disp,
                    step.action,
                    att_disp,
                    elapsed_disp,
                    cost_disp,
                    tok_disp,
                    v_disp,
                    issue_disp,
                ]
            )
    return render_box_table("", headers, rows, term, aligns)


def render_step_details(steps: list[StepSummary], term: Term) -> list[str]:
    """Render detail lines for a list of steps."""
    lines = []
    for step in steps:
        details = []
        # orchprobe (r2i1b1) E-05: the FULL, untruncated reason and remedy. This is the detail view,
        # so nothing is elided here; the flagless reader is served by `format_refusal_summary`
        # instead, because this function runs ONLY under `if detail:`.
        refusal = step_refusal(step)
        if refusal is not None:
            details.append(
                term.color256(f"  ! refused [{refusal.code}]: {refusal.reason}", 196)
                if getattr(term, "color", False)
                else f"  ! refused [{refusal.code}]: {refusal.reason}"
            )
            details.append(
                term.color256(f"    → remedy: {refusal.remedy}", 46)
                if getattr(term, "color", False)
                else f"    → remedy: {refusal.remedy}"
            )
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
        if step.elapsed_str and step.elapsed_str != "-":
            details.append(
                term.color256(f"  * elapsed: {step.elapsed_str}", 245)
                if getattr(term, "color", False)
                else f"  * elapsed: {step.elapsed_str}"
            )
        if step.cost is not None:
            if step.verify_cost is not None:
                c_details = f" (exec: ${step.exec_cost or 0:.2f}, verify: ${step.verify_cost:.2f})"
            else:
                c_details = ""
            details.append(
                term.color256(f"  $ cost: ${step.cost:.2f}{c_details}", 220)
                if getattr(term, "color", False)
                else f"  $ cost: ${step.cost:.2f}{c_details}"
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
                if step.verify_tokens.get("total"):
                    e_t = format_tokens(step.exec_tokens.get("total", 0))
                    v_t = format_tokens(step.verify_tokens.get("total", 0))
                    tok_str += f" [exec: {e_t}, verify: {v_t}]"
                details.append(
                    term.color256(f"  * tokens: {tok_str}", 245)
                    if getattr(term, "color", False)
                    else f"  * tokens: {tok_str}"
                )
        if step.tests_run:
            cmds = extract_verifier_test_commands({"tests_run": step.tests_run})
            for cmd in cmds:
                truncated = cmd if len(cmd) <= 120 else cmd[:117] + "..."
                details.append(
                    term.color256(f"  > test: {truncated}", 36)
                    if getattr(term, "color", False)
                    else f"  > test: {truncated}"
                )
        if step.corrections_made:
            for corr in step.corrections_made:
                corr_str = str(corr).strip()
                truncated = corr_str if len(corr_str) <= 120 else corr_str[:117] + "..."
                details.append(
                    term.color256(f"  ~ correction: {truncated}", 33)
                    if getattr(term, "color", False)
                    else f"  ~ correction: {truncated}"
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
        if run.is_live:
            # A LIVE DRIVER PROCESS IS THE RUN'S LIFECYCLE STATE, and this cell took a hardcoded 40,
            # which is not one of spec Section 5's eleven indices at all. It resolves through the RUN
            # LEDGER family (Section 7.3) rather than the item family, because the subject is the RUN,
            # and `running` there is the row this cell means. A NON-live run keeps its plain rendering:
            # `exited` is not a ledger state and inventing one would assert an outcome this line does
            # not know (the run may have completed, failed, or been killed).
            p_state_txt = term.style_lifecycle_text(
                f"[{p_state}]", _resolve_ledger_status("running")
            )
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
        st_display = canonical_terminal_status(st)
        tally_parts.append(f"{cnt} {st_display}")
    tally_str = ", ".join(tally_parts) if tally_parts else f"{len(run.steps)} steps"
    lines.append(f"  {len(run.steps)} steps: {tally_str}")

    # Line 4: Cost and token usage (if present)
    has_verification = run.verify_cost is not None or (
        bool(run.verify_tokens) and run.verify_tokens.get("total", 0) > 0
    )

    if not has_verification:
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
    else:

        def _fmt_cost_tok(c: float | None, toks: dict[str, int]) -> str:
            c_str = f"${c:.2f}" if c is not None else "$0.00"
            if toks.get("total"):
                tot_s = format_tokens(toks["total"])
                in_s = format_tokens(toks.get("input", 0))
                out_s = format_tokens(toks.get("output", 0))
                cache_s = format_tokens(toks.get("cache", 0))
                return (
                    f"{c_str}, {tot_s} tok ({in_s} in, {out_s} out, {cache_s} cached)"
                )
            return c_str

        tot_line = _fmt_cost_tok(run.total_cost, run.total_tokens)
        exec_line = _fmt_cost_tok(run.exec_cost, run.exec_tokens)
        ver_line = _fmt_cost_tok(run.verify_cost, run.verify_tokens)

        lines.append(f"  Total:        {tot_line}")
        lines.append(f"    - Execute:  {exec_line}")
        lines.append(f"    - Verify:   {ver_line}")

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

    # Scoped strictly to IPDs that were executed and verified
    verified_steps_count = 0
    verified_runs_present: set[int] = set()
    verified_exec_cost = 0.0
    verified_exec_tokens: dict[str, int] = defaultdict(int)
    verified_verify_cost = 0.0
    verified_verify_tokens: dict[str, int] = defaultdict(int)

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

            # Compare execution vs verification ONLY for steps that were verified
            has_verify = step.verify_cost is not None or (
                bool(step.verify_tokens) and step.verify_tokens.get("total", 0) > 0
            )
            if has_verify:
                verified_steps_count += 1
                verified_runs_present.add(run_idx)
                if step.exec_cost is not None:
                    verified_exec_cost += step.exec_cost
                if step.exec_tokens:
                    for k, v in step.exec_tokens.items():
                        verified_exec_tokens[k] += v
                if step.verify_cost is not None:
                    verified_verify_cost += step.verify_cost
                if step.verify_tokens:
                    for k, v in step.verify_tokens.items():
                        verified_verify_tokens[k] += v

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

    by_phase = None
    if verified_steps_count > 0:
        # Scoped strictly to IPDs that were executed and verified
        total_verified_cost = round(verified_exec_cost + verified_verify_cost, 4)
        total_verified_tokens: dict[str, int] = defaultdict(int)
        for k, v in verified_exec_tokens.items():
            total_verified_tokens[k] += v
        for k, v in verified_verify_tokens.items():
            total_verified_tokens[k] += v

        by_phase = {
            "steps_count": verified_steps_count,
            "runs_count": len(verified_runs_present),
            "execution": {
                "total_cost": round(verified_exec_cost, 4),
                "avg_cost_per_step": (
                    round(verified_exec_cost / verified_steps_count, 4)
                    if verified_steps_count > 0
                    else None
                ),
                "avg_cost_per_run": (
                    round(verified_exec_cost / total_runs, 4)
                    if (total_runs > 0 and verified_exec_cost)
                    else None
                ),
                "tokens": dict(verified_exec_tokens) if verified_exec_tokens else {},
                "avg_tokens_per_step": (
                    {
                        k: int(v / verified_steps_count)
                        for k, v in verified_exec_tokens.items()
                    }
                    if verified_steps_count > 0
                    else {}
                ),
                "avg_tokens_per_run": (
                    {k: int(v / total_runs) for k, v in verified_exec_tokens.items()}
                    if total_runs > 0
                    else {}
                ),
            },
            "verification": {
                "total_cost": round(verified_verify_cost, 4),
                "avg_cost_per_step": (
                    round(verified_verify_cost / verified_steps_count, 4)
                    if verified_steps_count > 0
                    else None
                ),
                "avg_cost_per_run": (
                    round(verified_verify_cost / total_runs, 4)
                    if (total_runs > 0 and verified_verify_cost)
                    else None
                ),
                "tokens": (
                    dict(verified_verify_tokens) if verified_verify_tokens else {}
                ),
                "avg_tokens_per_step": (
                    {
                        k: int(v / verified_steps_count)
                        for k, v in verified_verify_tokens.items()
                    }
                    if verified_steps_count > 0
                    else {}
                ),
                "avg_tokens_per_run": (
                    {k: int(v / total_runs) for k, v in verified_verify_tokens.items()}
                    if total_runs > 0
                    else {}
                ),
            },
            "total": {
                "total_cost": total_verified_cost,
                "avg_cost_per_step": (
                    round(total_verified_cost / verified_steps_count, 4)
                    if verified_steps_count > 0
                    else None
                ),
                "avg_cost_per_run": (
                    round(total_verified_cost / total_runs, 4)
                    if (total_runs > 0 and total_verified_cost)
                    else None
                ),
                "tokens": (
                    dict(total_verified_tokens) if total_verified_tokens else {}
                ),
                "avg_tokens_per_step": (
                    {
                        k: int(v / verified_steps_count)
                        for k, v in total_verified_tokens.items()
                    }
                    if verified_steps_count > 0
                    else {}
                ),
                "avg_tokens_per_run": (
                    {k: int(v / total_runs) for k, v in total_verified_tokens.items()}
                    if total_runs > 0
                    else {}
                ),
            },
        }

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
        "by_phase": by_phase,
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

        # Phase Table (ONLY for verified IPDs, if any exist in the dataset)
        by_phase = summary_data.get("by_phase")
        if by_phase and by_phase.get("steps_count", 0) > 0:
            v_cnt = by_phase["steps_count"]
            headers_ph = [
                "Phase",
                "Type",
                "Cost",
                "%",
                "Tokens",
                "%",
                "In",
                "%",
                "Out",
                "%",
                "Cached",
                "%",
            ]
            aligns_ph = [
                "left",
                "left",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
            ]
            rows_ph = []

            tot_phase_cost = by_phase.get("total", {}).get("total_cost") or 0.0
            tot_phase_toks = by_phase.get("total", {}).get("tokens", {})

            def _pct(num: float | int | None, denom: float | int | None) -> str:
                if num is None or not denom:
                    return "-"
                pct_val = round((num / denom) * 100)
                return f"{pct_val}%"

            for phase_name in ("execution", "verification", "total"):
                p_data = by_phase.get(phase_name, {})
                p_styled = (
                    term.color256(phase_name, 226, bold=(phase_name == "total"))
                    if getattr(term, "color", False)
                    else phase_name
                )
                td = p_data.get("tokens", {})
                avg_td = p_data.get("avg_tokens_per_step", {})

                c_val = p_data.get("total_cost")
                c_avg_val = p_data.get("avg_cost_per_step")
                c_pct = _pct(c_val, tot_phase_cost)

                t_val = td.get("total")
                t_avg_val = avg_td.get("total")
                t_pct = _pct(t_val, tot_phase_toks.get("total"))

                in_val = td.get("input")
                in_avg_val = avg_td.get("input")
                in_pct = _pct(in_val, tot_phase_toks.get("input"))

                out_val = td.get("output")
                out_avg_val = avg_td.get("output")
                out_pct = _pct(out_val, tot_phase_toks.get("output"))

                cache_val = td.get("cache")
                cache_avg_val = avg_td.get("cache")
                cache_pct = _pct(cache_val, tot_phase_toks.get("cache"))

                if c_val is not None or td:
                    c_tot = f"${(c_val or 0.0):.2f}"
                    c_avg = f"${(c_avg_val or 0.0):.2f}"
                    t_tot = format_tokens(t_val) if t_val else "-"
                    t_avg = format_tokens(t_avg_val) if t_avg_val else "-"
                    in_tot = format_tokens(in_val) if in_val else "-"
                    in_avg = format_tokens(in_avg_val) if in_avg_val else "-"
                    out_tot = format_tokens(out_val) if out_val else "-"
                    out_avg = format_tokens(out_avg_val) if out_avg_val else "-"
                    cache_tot = format_tokens(cache_val) if cache_val else "-"
                    cache_avg = format_tokens(cache_avg_val) if cache_avg_val else "-"
                else:
                    c_tot = c_avg = t_tot = t_avg = in_tot = in_avg = out_tot = (
                        out_avg
                    ) = cache_tot = cache_avg = "-"

                rows_ph.append(
                    [
                        p_styled,
                        "Total",
                        c_tot,
                        c_pct,
                        t_tot,
                        t_pct,
                        in_tot,
                        in_pct,
                        out_tot,
                        out_pct,
                        cache_tot,
                        cache_pct,
                    ]
                )
                rows_ph.append(
                    [
                        "",
                        "Avg",
                        c_avg,
                        c_pct,
                        t_avg,
                        t_pct,
                        in_avg,
                        in_pct,
                        out_avg,
                        out_pct,
                        cache_avg,
                        cache_pct,
                    ]
                )

            lines.append("")
            table_title = f"Breakdown for Verified Executions ({v_cnt} step{'s' if v_cnt != 1 else ''}):"
            lines.append(
                render_box_table(table_title, headers_ph, rows_ph, term, aligns_ph)
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
            st_disp = canonical_terminal_status(st)
            # THE ANALYTICS Status COLUMN, through the shared resolver (R10.3). Its keys are runner
            # ITEM statuses (the same words `by_status` is aggregated from), so it uses the same family
            # as the item rows above and renders one vocabulary with them. Glyph omitted for the box
            # table's width reason recorded at the audit table.
            st_styled = term.style_lifecycle_text(st_disp, _resolve_item_status(st))
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


#: Help text for the `aw runs repair` verb. It lives here rather than in an argparse subparser
#: because `repair` is routed from the first positional token, deliberately, so that every READ
#: path on `aw runs` stays side-effect free (ssk6nf E-04). The cost of that choice is that argparse
#: cannot render help for it, so `aw runs repair --help` fell through to the generic `runs` help and
#: described a read-only inspector. This string is what the verb prints instead.
REPAIR_HELP = """usage: aw runs repair <run-id|run-dir> [<run-id|run-dir> ...]

Durably reconcile a run that was abandoned WITHOUT a terminal status, so it stops being reported as
still running. This is the one MUTATING verb on `aw runs`; every other form is read-only.

WHEN YOU NEED IT
  A driver killed mid-turn (crash, reboot, SIGKILL, closed laptop) never writes a terminal status,
  so its step stays `running` in the run's state.json while no process holds the run. `aw runs`
  projects a label for such a step, with a trailing `?` meaning "read at display time, nothing
  recorded durably". This verb decides the question and writes the answer down.

WHAT IT DOES, per step still marked `running`
  - Resolves the step's plan and looks at which lifecycle directory it now sits in.
  - Plan is in executed/  -> records `executed` (the work did land before the driver died).
  - Otherwise, reads the step's own outcomes/<NN>-<id6>.json and honors the disposition recorded
    there, marking it `recovered-from-outcome` and reporting any commit shas it names. A recorded
    `executed` is downgraded to `substantially-complete`, because an agent's claim about its own turn
    is not completion authority.
  - Only when there is no readable recorded disposition -> records `interrupted` (honest: as far as
    anything on disk shows, it stopped partway).
  - Recovers the agent session id from the attempt log when it can, so the turn stays traceable.
  It delegates to the single reconciler (`runner_shared.reconcile_interrupted`) rather than
  reimplementing the decision, so the read view and this repair can never disagree.

WHAT IT REFUSES TO DO
  - Refuses while a LIVE driver still holds the run (that would race the driver's own writer).
    Stop the run first, then repair.
  - Refuses when it cannot PROVE no driver holds the run (flock unavailable on this platform).
  - Refuses to record `executed` for a turn that was force-interrupted at stop level 4, even if the
    plan sits in executed/, because the driver never established that the work was complete. It
    records a reconciliation conflict for a human instead of fabricating success.
  - Does NOT delete the stale `driver.lock`, does NOT touch any plan file or its `- Status:`, does
    NOT merge or discard lane work, and does NOT re-run anything.

EXIT CODES
  0  reconciled, or nothing to reconcile (no running steps: a no-op, safe to re-run)
  1  refused (a live driver holds the run, or liveness could not be proven)
  2  not a run directory

EXAMPLES
  aw runs repair run-20260902T013603Z-1758564     # one run by id
  aw runs repair .aw/records/runs/run-2026...     # or by directory path
  aw runs --active                               # find runs that still look alive first

LIMITS WORTH KNOWING
  A recovered disposition is only as good as the file it came from. The driver never validated that
  outcome JSON: it was written by an agent whose process then died, so the step is marked
  `recovered-from-outcome` rather than reported as though the driver had scored the turn itself.
  A recorded commit sha is REPORTED, not checked for mergeability and never merged; a sha that does
  not resolve in this repository is reported as recorded but unresolved.
  A turn that was force-interrupted at stop level 4 is never recovered from its own outcome file,
  because that is precisely the case in which the driver established nothing.
  This verb also does not delete the stale `driver.lock`, and it cannot repair a run a live driver
  still holds."""


#: The nine READ-ONLY leaves registered under `aw runs`. Kept as ONE list so the refusal message
#: below and `cli._RUNS_VIEWER_LEAVES` cannot drift into disagreeing about what is registered; the
#: parser imports this rather than holding a second copy (runsverify 7wei1o E-02).
RUNS_VIEWER_LEAF_NAMES: tuple[str, ...] = (
    "decisions",
    "evidence",
    "list",
    "next",
    "questions",
    "resume",
    "show",
    "status",
    "verify-ledger",
)

#: Exit code for an unresolvable target. Reuses the SHIPPED invalid-invocation code
#: (`run_cli.EXIT_INVALID_INVOCATION` == 2) rather than inventing one, so this refusal reads the
#: same as the analogous `aw runs verify-ledger <absent>` refusal that already exits 2.
EXIT_UNRESOLVABLE_TARGET: int = 2


def format_unresolvable_target_message(
    unresolved: Sequence[str],
    repo_root: Path = Path("."),
) -> str:
    """The human refusal text for one or more targets that matched no run.

    runsverify 7wei1o E-02. Names the unresolved token (a bare exit code leaves the operator
    guessing WHICH token was wrong, which matters most in the mixed case where the rest of the
    request rendered fine), the registered leaves, and the closest leaf match when there is one.

    The motivating case is a one-edit typo: `aw runs verify <run-id>` names no leaf, so `verify`
    became a TARGET, resolved to nothing, was silently dropped, and the command rendered an
    ordinary report at exit 0 while verifying nothing. The suggestion turns that into
    `verify-ledger`.
    """
    import difflib

    tokens = list(unresolved)
    if len(tokens) == 1:
        head = f"error: no run matched target {tokens[0]!r}"
    else:
        joined = ", ".join(repr(t) for t in tokens)
        head = f"error: no run matched targets {joined}"

    lines = [head]
    for tok in tokens:
        if path_is_within_analytics(tok, repo_root):
            lines.append(
                f"  note: {tok!r} is within the reserved analytics tree "
                f"({analytics_root(repo_root)}); analytics artifacts cannot be targeted as execution runs"
            )
        else:
            close = difflib.get_close_matches(
                tok, RUNS_VIEWER_LEAF_NAMES, n=1, cutoff=0.6
            )
            if close:
                lines.append(
                    f"  did you mean the leaf `aw runs {close[0]}`? (not {tok!r})"
                )
    lines.append(f"  leaves: {' '.join(RUNS_VIEWER_LEAF_NAMES)}")
    lines.append(
        "  a TARGET is a run id, a run directory path, or a Set id; "
        "force viewer interpretation of a leaf-like name with `aw runs -- <target>`"
    )
    return "\n".join(lines)


def _unresolvable_target_refusal(
    unresolved: Sequence[str],
    term: Term,
    *,
    repo_root: Path = Path("."),
    is_agent: bool = False,
    is_json: bool = False,
) -> int:
    """Emit the unresolvable-target refusal in whichever renderer is active. Returns the exit code.

    runsverify 7wei1o E-02. HONORED IN ALL THREE RENDERERS deliberately. The empty-state used to
    have a MACHINE branch returning `{"runs": []}` at exit 0 BEFORE the human line, and the machine
    branch is the one automation actually reads, so a refusal implemented only on the human path
    would leave the fail-open exactly where it silently misleads a script.

    The machine record is a conformant `aw.agent/v1` error record carrying the nonzero `exit`, not a
    bare payload, because the conformance matrix asserts an agent summary's `exit` agrees with the
    process return code.
    """
    message = format_unresolvable_target_message(unresolved, repo_root=repo_root)
    if is_agent or is_json:
        record = {
            "schema": _agent_schema.SCHEMA_VERSION,
            "kind": "error",
            "cmd": "runs",
            "outcome": "cannot-run",
            "exit": EXIT_UNRESOLVABLE_TARGET,
            "verified": False,
            "complete": False,
            "findings": len(list(unresolved)),
            "unresolved_targets": list(unresolved),
            "error": message,
            "next": None,
        }
        _agent_schema.assert_valid_agent_record(record)
        print(json.dumps(record, indent=2 if is_json else None, ensure_ascii=False))
        return EXIT_UNRESOLVABLE_TARGET
    # Human: to STDERR, so a refusal never lands in a report a caller is parsing on stdout.
    print(message, file=sys.stderr)
    return EXIT_UNRESOLVABLE_TARGET


def repair_run(run_dir: Path, repo_root: Path = Path(".")) -> tuple[int, str]:
    """ssk6nf E-04: durably reconcile a run abandoned without a terminal status.

    Delegates to ``runner_shared.reconcile_interrupted``, the SINGLE reconciler (it resolves each
    running item's plan, promotes one that genuinely reached ``executed``, else honors the disposition
    the step itself recorded in ``outcomes/<NN>-<id6>.json``, else marks it ``interrupted``).
    Deliberately does not reimplement that logic (GUIDING_PRINCIPLES P8).

    RE-POINTED FROM ``oc_runipd`` BY runrecon-02 (`fduoj4`) E-01, which made that function ONE shared
    definition instead of a per-host fork. This verb previously ran the OpenCode host's copy for every
    run whatever host wrote it, so it could disagree with the Antigravity crash path.

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

    # runrecon-02 (`fduoj4`) E-01: RE-POINTED at `runner_shared`, which now owns the ONE reconciler.
    # It was `oc_runipd.reconcile_interrupted`, which meant this verb ran the OpenCode host's copy for
    # every run whatever wrote it, and could therefore disagree with the Antigravity crash path. The
    # oc wrapper still exists and still delegates here, so this is a re-point and not a second route.
    from agent_workflows import oc_runipd, runner_shared

    state = oc_runipd.load_state(run_dir)
    stale = [
        i.get("id6", "") for i in state.get("queue", []) if i.get("status") == "running"
    ]
    if not stale:
        return 0, f"{run_dir.name}: nothing to repair (no running steps)"

    runner_shared.reconcile_interrupted(run_dir, state, save_state=oc_runipd.save_state)

    after = oc_runipd.load_state(run_dir)
    by_id = {i.get("id6", ""): i for i in after.get("queue", [])}
    parts = []
    for i in stale:
        entry = by_id.get(i) or {}
        status = entry.get("status")
        # runrecon-02 (`fduoj4`) E-02/E-03: SAY WHEN A VERDICT WAS RECOVERED, and from what. A recovered
        # disposition was read out of the step's own outcome file, which the driver never validated; a
        # directory-derived one was resolved here. Reporting them identically would hide that
        # difference from the operator who just asked this verb to decide the question.
        note = ""
        if entry.get(runner_shared.RECOVERY_PROVENANCE_KEY) == (
            runner_shared.RECOVERED_FROM_OUTCOME
        ):
            note = f" ({runner_shared.RECOVERED_FROM_OUTCOME})"
            commits = entry.get(runner_shared.RECOVERED_COMMITS_KEY) or []
            if commits:
                rendered = ", ".join(
                    c.get("sha", "")
                    + ("" if c.get("resolved") else " [recorded, unresolved here]")
                    for c in commits
                )
                note += f", recorded commits: {rendered}"
        parts.append(f"{i} running -> {status}{note}")
    changes = ", ".join(parts)
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
        # `repair` is routed from a positional token rather than a subparser (so every READ path
        # stays side-effect free), which means argparse never learns it is a verb and cannot render
        # its help. `aw runs repair --help` therefore reached the generic `runs` help, describing a
        # read-only inspector while the user was asking about a MUTATING verb. Handle the help
        # request here, where the verb is actually known.
        if any(t in ("-h", "--help") for t in targets):
            print(REPAIR_HELP)
            return 0
        if not targets:
            print("error: aw runs repair needs a run id (or a run directory path)")
            print()
            print(REPAIR_HELP)
            return 2
        # runsverify 7wei1o E-08: refuse an UNRESOLVABLE repair target instead of silently
        # succeeding. When nothing resolved, the loop body below never ran, so `rc` stayed 0 and
        # NOTHING was printed (measured: `aw runs repair totalgibberish` -> exit 0, zero bytes).
        # That is strictly worse than the read path, because `repair` is the one MUTATING verb on
        # this surface and the operator was told nothing at all. The adjacent missing-target case
        # two lines above was already correct, so this closes an inconsistency inside one function.
        repair_dirs, repair_unresolved = resolve_target_runs_detailed(
            targets, repo_root
        )
        if repair_unresolved:
            return _unresolvable_target_refusal(
                repair_unresolved, Term(color=None), repo_root=repo_root
            )
        rc = 0
        for run_dir in repair_dirs:
            code, message = repair_run(run_dir, repo_root)
            print(message)
            rc = rc or code
        return rc

    run_dirs, unresolved_targets = resolve_target_runs_detailed(raw_targets, repo_root)

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
    issues_only = getattr(args, "issues", False)
    # IPD `zexed1` E-04: restores the evidenced `resolved`/`retired` rows the table suppresses by
    # default. It cannot unhide anything alarming, because nothing alarming is ever hidden.
    all_classes = getattr(args, "all_classes", False)
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

    if issues_only and summary_only:
        err_msg = "error: --issues/-i cannot be used with --summary-only/-S"
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

    # runsverify 7wei1o E-02/E-04: REFUSE a target that resolved to nothing, rather than dropping it
    # and rendering a plausible report at exit 0.
    #
    # The motivating case: `aw runs verify <run-id>` names no leaf, so `verify` was read as a TARGET,
    # matched nothing, was discarded, and the command rendered the run's ordinary report and exited
    # 0. An operator (or an agent following a recovery message, which is what seven shipped strings
    # in `run_evidence.py` told them to run) reasonably concluded the ledger had been checked.
    #
    # THE MIXED CASE IS REFUSED TOO, deliberately, and it is the variant that matters most:
    # `aw runs totalgibberish <real-run-id>` printed the real run at exit 0 with the bogus token
    # silently dropped, so the output LOOKED like a complete answer to the question asked. A
    # partially-honored request that looks complete is precisely the defect being removed, so a
    # request is either honored in full or refused; it is never quietly narrowed.
    #
    # Placed AFTER the flag-conflict and `--since` validation so those existing refusals keep their
    # own messages and precedence, and BEFORE any rendering so no partial report is ever emitted.
    # A bare `aw runs` yields no unresolved tokens by construction, so an empty repository stays
    # exit 0: asking for EVERYTHING and finding nothing is a healthy state, not a failed request
    # (OQ-01).
    if unresolved_targets:
        return _unresolvable_target_refusal(
            unresolved_targets,
            term,
            repo_root=repo_root,
            is_agent=is_agent,
            is_json=is_json,
        )

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

    # The genuine EMPTY STATE, which stays a SUCCESS. Every token the caller named resolved to a run
    # (an unresolvable one was refused above), so reaching here means a FILTER excluded what matched,
    # or the repository simply has no runs. Neither is a failed request, so both keep exit 0
    # (runsverify 7wei1o, OQ-01).
    if not summaries and not issues_only:
        if is_agent or is_json:
            print(json.dumps({"runs": []}, indent=2 if is_json else None))
            return 0
        term.line("no matching runs found")
        return 0

    # Collect artifact audits across displayed steps.
    #
    # ONE GIT PASS FOR THE WHOLE TABLE (IPD `zexed1` E-02), built here and reused for every row.
    # Measured in this lane over 3160 commits: this single pass costs ~68ms, while spawning a
    # `git log --grep` (~49ms) plus a `merge-base --is-ancestor` (~2.7ms) PER ROW costs ~26 SECONDS at
    # the review-measured 508 rows. That is the difference between a usable interactive read and an
    # unusable one, which is why the index is a parameter rather than something each audit fetches.
    #
    # orchprobe (r2i1b1) E-04: the STEP is collected alongside its audit, in the same order, because a
    # refusal is recorded on the step and is invisible from the audit alone. Without this, the machine
    # surfaces below could not see a refusal even though the ONE predicate can, which is the surface
    # DISAGREEMENT F-2 predicts (the table saying YES while `--json` omits the same item).
    evidence_index = _audit.build_finalize_evidence_index(repo_root)
    all_audits: list[StepArtifactAudit] = []
    all_steps: list[StepSummary] = []
    if latest_only:
        latest_steps_dict: dict[str, tuple[RunSummary, StepSummary]] = {}
        for s in summaries:
            for step in s.steps:
                key = step.id6 or step.stem or step.item
                latest_steps_dict[key] = (s, step)
        for _, st in latest_steps_dict.values():
            all_audits.append(audit_step_artifact(st, repo_root, evidence_index))
            all_steps.append(st)
    else:
        for s in summaries:
            for st in s.steps:
                all_audits.append(audit_step_artifact(st, repo_root, evidence_index))
                all_steps.append(st)

    def _issue_records() -> list[dict[str, Any]]:
        """The issue set for the machine surfaces: artifact discrepancies AND refusals.

        ONE builder for `--json` and `--agent --issues` (r2i1b1 E-04), so the two cannot disagree.
        Each record keeps the artifact-audit shape it always had, and a refused step additionally
        carries `refusal` with `code`/`reason`/`remedy` as DISCRETE fields rather than embedded prose
        (E-05), so a tool can read the remedy without parsing a sentence.
        """
        out: list[dict[str, Any]] = []
        for audit, step in zip(all_audits, all_steps):
            reasons = step_issue_reasons(audit, step)
            if not reasons:
                continue
            rec = asdict(audit)
            if rec.get("actual_path"):
                rec["actual_path"] = str(rec["actual_path"])
            rec["issue_reasons"] = reasons
            rf = step_refusal(step)
            if rf is not None:
                rec["refusal"] = rf.to_dict()
            out.append(rec)
        return out

    if is_json:
        # orchprobe (r2i1b1) E-03/E-04: through the ONE builder over the ONE predicate.
        disc = _issue_records()

        if issues_only:
            payload = {"artifact_discrepancies": disc}
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0

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

        if disc:
            payload["artifact_discrepancies"] = disc

        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if is_agent:
        if issues_only:
            # orchprobe (r2i1b1) E-03/E-04: the SAME builder `--json` uses, so the two machine
            # surfaces cannot report different issue sets. The builder already stringifies
            # `actual_path`, so the hand-written coercion this replaced is not lost.
            for d in _issue_records():
                print(json.dumps(d, separators=(",", ":"), ensure_ascii=False))
            return 0
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
    if issues_only:
        # orchprobe (r2i1b1) E-03/E-04: through the ONE predicate, WITH the steps, so `--issues`
        # reports a refusal rather than claiming a clean run. The old wording named only artifacts,
        # which would have been a lie about a refused run.
        disc = [a for a, st in zip(all_audits, all_steps) if step_has_issue(a, st)]
        if not disc:
            # WORDING DELIBERATELY UNCHANGED (r2i1b1 D-1). This line is reached only when there is
            # NOTHING to report (no discrepancy AND no refusal), so it is never shown on a refused
            # run and cannot mislead. It is pinned by `tests/test_run_viewer.py`, which this plan does
            # NOT declare in `Scope-Paths`, and E-04 requires a clean run to be unchanged at all five
            # surfaces; broadening the sentence would have edited an undeclared test to no reader's
            # benefit.
            term.line("no artifact or status discrepancies found")
            return 0
        term.line(
            format_artifact_audit_summary(
                all_audits, term, all_classes, steps=all_steps
            )
        )
        return 0

    if latest_only:
        term.line(
            format_latest_only_human(
                summaries, term, detail=detail, short=short, repo_root=repo_root
            )
        )
        audit_summary_txt = format_artifact_audit_summary(
            all_audits, term, all_classes, steps=all_steps
        )
        if audit_summary_txt:
            term.line("")
            term.line(audit_summary_txt)
        return 0

    if summary_only:
        term.line(format_multi_run_summary(summaries, term))
        audit_summary_txt = format_artifact_audit_summary(
            all_audits, term, all_classes, steps=all_steps
        )
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

    audit_summary_txt = format_artifact_audit_summary(
        all_audits, term, all_classes, steps=all_steps
    )
    if audit_summary_txt:
        term.line("")
        term.line(audit_summary_txt)

    return 0
