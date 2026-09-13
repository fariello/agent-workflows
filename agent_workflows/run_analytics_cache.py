#!/usr/bin/env python3
"""The versioned, privacy-projected, incrementally reusable per-run analytics cache.

WHAT THIS IS FOR. Analyzing a run corpus means reparsing every run's ``state.json``,
``events.jsonl`` and per-item outcome files. That cost grows with the corpus and is paid again on
every invocation, even though almost every run is FINISHED and can never change again. This module
stores one normalized summary per source run and reuses it when, and only when, every
analytics-relevant input is provably unchanged.

WHERE IT LIVES, AND WHY THE PATH IS NEVER COMPOSED HERE. Entries go under
``<resolved-runs-root>/analytics/cache/<source-root-id>/<run-id>/entry.json``, where the root and
the ``analytics/cache`` segment both come from :mod:`agent_workflows.runner_shared`
(:func:`~agent_workflows.runner_shared.analytics_cache_dir`). That resolver consults the project
context, so a records root relocated by ``records_backend`` (``repository``/``companion``/``home``)
still yields the correct location. Hand-composing ``<repo>/.aw/records/runs`` would reintroduce
exactly the hardcoded-literal defect that resolver exists to remove, and would put the cache in
the wrong place for every non-repository backend. Containment is asserted with
:func:`~agent_workflows.runner_shared.path_is_within_analytics` before any write.

THE TREE IS DISPOSABLE, AND THAT IS A DESIGN PROPERTY RATHER THAN A LIMITATION. The runs tree is
gitignored, so nothing here is tracked, migrated, or repaired: a cache entry that cannot be read
is REBUILT. That is why the loader may be strict without being brittle, and it is why the salt
(see :mod:`agent_workflows.run_analytics_privacy`) may live beside the cache and die with it.

FRESHNESS IS A FINGERPRINT, NOT A DIRECTORY MTIME. A driver writes into a run directory
throughout the run and a RESUMED run writes into the SAME directory again, so an mtime comparison
answers the wrong question. :func:`source_fingerprint` digests the identity (relative path, size,
mtime nanoseconds) of every analytics-relevant file plus the run's terminal/in-progress state, and
a run that is NOT terminal is never a stable hit. See :func:`decide` for the whole verdict table.

PUBLICATION IS ATOMIC AND SERIALIZED. Writes go through
:func:`~agent_workflows.runner_shared.atomic_write_json` (temp file plus ``os.replace``), so an
interruption leaves either the previous valid entry or none, never a partial one. Concurrent
analyzers are serialized per entry by :mod:`agent_workflows.platform_lock`, the package's single
lock authority; ``filelock`` and ``fcntl`` are deliberately NOT used directly here (see
:func:`_publish` for the three measured reasons). A BUSY lock SKIPS that one run with a recorded,
machine-readable reason and does not wait, because acquisition in this package is non-blocking by
design with exactly one permitted blocking caller elsewhere, and a hung analyzer costs an operator
their session while a skip costs one rebuild.

PRIVACY IS THE OTHER MODULE'S JOB AND THERE IS ONLY ONE WAY IN.
:func:`~agent_workflows.run_analytics_privacy.project_facts` is the sole path by which a fact
reaches an envelope: :func:`build_entry` calls it and nothing else in this module writes into the
``metric_facts``/``event_facts`` members. The cache is MINIMIZED and REDACTED, NOT anonymous and
NOT cleared for release; see that module's docstring for the residual risk and the hashing
contract.

Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from agent_workflows import platform_lock
from agent_workflows import run_analytics_privacy as privacy
from agent_workflows.runner_shared import (
    analytics_cache_dir,
    atomic_write_json,
    path_is_within_analytics,
)

__all__ = [
    "CACHE_SCHEMA_VERSION",
    "ENTRY_FILENAME",
    "ENVELOPE_FIELDS",
    "CacheError",
    "CacheEnvelopeError",
    "CacheVersionError",
    "CacheEnvelope",
    "CacheDecision",
    "CacheReport",
    "cache_root",
    "entry_dir",
    "entry_path",
    "source_root_id",
    "analytics_relevant_files",
    "source_fingerprint",
    "run_is_terminal",
    "build_entry",
    "encode_envelope",
    "decode_envelope",
    "load_entry",
    "decide",
    "update_cache",
]

#: The envelope's own schema version. BUMP THIS when a field's meaning changes; a reader refuses a
#: version it does not know rather than misparsing it, and the cache is disposable so a bump
#: simply rebuilds.
CACHE_SCHEMA_VERSION = 1

ENTRY_FILENAME = "entry.json"
_LOCK_FILENAME = "entry.lock"

#: EXACTLY the envelope's members. The loader refuses an unknown field and a missing one, so this
#: tuple is the contract rather than a convenience list.
ENVELOPE_FIELDS: tuple[str, ...] = (
    "schema_version",
    "tool_version",
    "source_root_id",
    "run_id",
    "is_complete",
    "source_fingerprint",
    "source_coverage",
    "generated_at",
    "metric_facts",
    "event_facts",
    "quality_flags",
    "warnings",
)

#: The analytics-relevant inputs. A file OUTSIDE this set may change without invalidating an
#: entry, which is the whole point of naming them: a driver rewrites its human-facing report and
#: its lock file constantly, and letting those churn force a rebuild would defeat the cache.
_RELEVANT_TOP_LEVEL_FILES: tuple[str, ...] = (
    "state.json",
    "events.jsonl",
    "ledger.jsonl",
)
_RELEVANT_SUBDIRS: tuple[str, ...] = ("outcomes", "telemetry")

#: Files whose churn is deliberately IGNORED for freshness.
_IGNORED_NAMES: frozenset[str] = frozenset(
    {"driver.lock", "execution-report.md", "decisions-and-questions.md"}
)


class CacheError(Exception):
    """Base class for every refusal this module raises."""


class CacheEnvelopeError(CacheError):
    """The stored bytes are not a conforming envelope, so the entry is REBUILT rather than used."""


class CacheVersionError(CacheEnvelopeError):
    """The entry was written by a different schema generation.

    Separate from :class:`CacheEnvelopeError` because the two need different diagnostics: a
    FUTURE version means a newer tool wrote it and this reader must not guess at its meaning,
    while a PAST version is an ordinary rebuild. Neither is corruption.
    """


@dataclass(frozen=True)
class CacheEnvelope:
    """One run's cached summary, versioned and privacy-projected.

    Every ``metric_facts``/``event_facts`` value has crossed
    :func:`agent_workflows.run_analytics_privacy.project_facts`, enforced in :func:`build_entry`,
    which is the only constructor callers should use.
    """

    schema_version: int
    tool_version: str
    source_root_id: str
    run_id: str
    is_complete: bool
    source_fingerprint: str
    source_coverage: dict[str, Any]
    generated_at: str
    metric_facts: dict[str, Any]
    event_facts: list[dict[str, Any]] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tool_version": self.tool_version,
            "source_root_id": self.source_root_id,
            "run_id": self.run_id,
            "is_complete": self.is_complete,
            "source_fingerprint": self.source_fingerprint,
            "source_coverage": dict(self.source_coverage),
            "generated_at": self.generated_at,
            "metric_facts": dict(self.metric_facts),
            "event_facts": [dict(e) for e in self.event_facts],
            "quality_flags": list(self.quality_flags),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class CacheDecision:
    """What happened to ONE run, in the shape downstream consumers render.

    This is a CONTRACT, not a debug print: the query/analyze surface displays it, so ``verdict``
    values and ``reason`` codes are stable machine-readable tokens rather than prose.
    """

    run_id: str
    verdict: str  # "hit" | "miss" | "rebuild" | "skip"
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "verdict": self.verdict,
            "reason": self.reason,
            "detail": self.detail,
        }


#: Every reason code this module can emit, so a consumer can switch on them exhaustively.
REASON_CODES: frozenset[str] = frozenset(
    {
        "fresh-complete-entry",
        "no-entry",
        "fingerprint-changed",
        "run-not-terminal",
        "entry-incomplete",
        "schema-version-mismatch",
        "entry-unreadable",
        "lock-busy",
        "build-refused",
        "write-failed",
    }
)


@dataclass(frozen=True)
class CacheReport:
    """Per-run decisions plus totals, in the shape the analyze/query surface consumes."""

    decisions: list[CacheDecision]

    @property
    def totals(self) -> dict[str, int]:
        counts = {"hit": 0, "miss": 0, "rebuild": 0, "skip": 0}
        for d in self.decisions:
            counts[d.verdict] = counts.get(d.verdict, 0) + 1
        counts["total"] = len(self.decisions)
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": CACHE_SCHEMA_VERSION,
            "decisions": [d.to_dict() for d in self.decisions],
            "totals": self.totals,
        }


# --- Locations ---------------------------------------------------------------------------------
def cache_root(repo: Path | str | None = None) -> Path:
    """The cache directory, resolved through Order-01's resolver and never composed by hand."""

    return analytics_cache_dir(repo)


def source_root_id(runs_root: Path | str, *, salt: str) -> str:
    """A pseudonym for the runs root, so an entry names its corpus without naming a path.

    A raw runs-root path is an absolute path containing a home directory, which the leak detector
    flags at ``fail`` severity. It is nonetheless needed as an IDENTITY (two corpora must not
    share cache entries), which is exactly what a domain-salted pseudonym provides.
    """

    resolved = str(Path(runs_root).expanduser().resolve())
    return privacy.pseudonymize(resolved, salt=salt, domain="root")


def entry_dir(root_id: str, run_id: str, repo: Path | str | None = None) -> Path:
    """``<cache>/<source-root-id>/<run-id>``, with the pseudonym's ``:`` made path-safe."""

    return cache_root(repo) / root_id.replace(":", "-") / run_id


def entry_path(root_id: str, run_id: str, repo: Path | str | None = None) -> Path:
    return entry_dir(root_id, run_id, repo) / ENTRY_FILENAME


# --- Freshness ---------------------------------------------------------------------------------
def run_is_terminal(run_dir: Path | str) -> bool:
    """Is this run FINISHED, so that its inputs can never change again?

    Conservative by construction: anything unreadable, absent or unrecognized answers False, so an
    ambiguous run rebuilds rather than being cached as stable. A resumed run reuses its directory,
    which is precisely why a non-terminal run may never be a stable hit.
    """

    state = Path(run_dir) / "state.json"
    try:
        payload = json.loads(state.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(payload, Mapping):
        return False

    queue = payload.get("queue")
    if not isinstance(queue, Sequence) or not queue:
        return False
    live_states = {"queued", "running", "interrupted", ""}
    for item in queue:
        if not isinstance(item, Mapping):
            return False
        status = str(item.get("status") or "").strip().lower()
        if status in live_states:
            return False
    if (Path(run_dir) / "driver.lock").exists():
        # A lock file alone does not prove a live holder, so PROBE it rather than assume. Probing
        # goes through platform_lock, which never creates or truncates the file; an undetermined
        # answer (None) is treated as "possibly live" and therefore not terminal.
        free = platform_lock.probe_free(Path(run_dir) / "driver.lock")
        if free is not True:
            return False
    return True


def analytics_relevant_files(run_dir: Path | str) -> list[Path]:
    """Every input whose content can change an analytics fact, sorted for determinism.

    Deliberately NARROW. A driver rewrites ``execution-report.md`` and touches ``driver.lock``
    continuously, and prompt/session transcripts are enormous and privacy-hostile; none of them
    feeds a metric fact, so none participates in freshness.
    """

    base = Path(run_dir)
    found: list[Path] = []
    for name in _RELEVANT_TOP_LEVEL_FILES:
        candidate = base / name
        if candidate.is_file():
            found.append(candidate)
    for sub in _RELEVANT_SUBDIRS:
        sub_dir = base / sub
        if not sub_dir.is_dir():
            continue
        for child in sorted(sub_dir.rglob("*")):
            if child.is_file() and child.name not in _IGNORED_NAMES:
                found.append(child)
    return sorted(found)


def source_fingerprint(run_dir: Path | str) -> str:
    """A deterministic digest of every analytics-relevant input plus terminal state.

    Covers each file's RELATIVE path, byte size and mtime in nanoseconds, plus the run's
    terminal/in-progress flag and the schema version. Deterministic across processes: the inputs
    are sorted, the digest is fed a canonical JSON encoding with sorted keys, and no absolute path,
    dict ordering, locale or process-local value participates.
    """

    base = Path(run_dir)
    members: list[dict[str, Any]] = []
    for path in analytics_relevant_files(base):
        try:
            stat = path.stat()
        except OSError:
            continue
        members.append(
            {
                "rel": path.relative_to(base).as_posix(),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    payload = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "is_terminal": run_is_terminal(base),
        "members": members,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


# --- Envelope encode/decode --------------------------------------------------------------------
def build_entry(
    *,
    run_id: str,
    root_id: str,
    run_dir: Path | str,
    metric_facts: Mapping[str, Any],
    event_facts: Iterable[Mapping[str, Any]] = (),
    tool_version: str = "",
    quality_flags: Iterable[str] = (),
    warnings: Iterable[str] = (),
    fingerprint: str | None = None,
    is_complete: bool | None = None,
    generated_at: str | None = None,
) -> CacheEnvelope:
    """Build an envelope, projecting EVERY fact through the privacy boundary.

    This is the only constructor a producer should use, and the projection call here is what makes
    :mod:`agent_workflows.run_analytics_privacy` "the only path by which a fact reaches the
    envelope": a refused key raises out of this function, so the envelope is never built at all
    rather than being built and then filtered.
    """

    base = Path(run_dir)
    projected_metrics = privacy.project_metric_facts(metric_facts)
    projected_events = [privacy.project_event_facts(e) for e in event_facts]
    flags = privacy.project_facts(
        {"quality_flags": list(quality_flags)},
        allowed=frozenset({"quality_flags"}),
        where="metric",
    )["quality_flags"]
    warns = privacy.project_facts(
        {"warnings": list(warnings)}, allowed=frozenset({"warnings"}), where="metric"
    )["warnings"]

    if tool_version == "":
        tool_version = _tool_version()
    complete = run_is_terminal(base) if is_complete is None else bool(is_complete)
    files = analytics_relevant_files(base)
    coverage = {
        "file_count": len(files),
        "member_names": sorted({p.relative_to(base).parts[0] for p in files}),
        "event_fact_count": len(projected_events),
    }
    return CacheEnvelope(
        schema_version=CACHE_SCHEMA_VERSION,
        tool_version=tool_version,
        source_root_id=privacy.project_facts(
            {"source_root_id": root_id},
            allowed=frozenset({"source_root_id"}),
            where="metric",
        )["source_root_id"],
        run_id=privacy.project_facts(
            {"run_id": run_id}, allowed=frozenset({"run_id"}), where="metric"
        )["run_id"],
        is_complete=complete,
        source_fingerprint=fingerprint
        if fingerprint is not None
        else source_fingerprint(base),
        source_coverage=coverage,
        generated_at=generated_at or _utc_now(),
        metric_facts=projected_metrics,
        event_facts=projected_events,
        quality_flags=flags,
        warnings=warns,
    )


def encode_envelope(envelope: CacheEnvelope) -> dict[str, Any]:
    return envelope.to_dict()


def decode_envelope(payload: Any) -> CacheEnvelope:
    """Parse an envelope STRICTLY: an unknown field is REFUSED, never dropped.

    Refusing rather than dropping is the load-bearing behavior. A loader that dropped an unknown
    field would silently discard a newer generation's data and then report success, so a
    round-trip could lose information without anybody noticing. The version check runs FIRST, so a
    future generation gets a forward-compatible diagnostic instead of a pile of unknown-field
    complaints about fields that are perfectly valid in their own schema.
    """

    if not isinstance(payload, Mapping):
        raise CacheEnvelopeError(
            f"envelope must be a JSON object, got {type(payload).__name__}"
        )

    raw_version = payload.get("schema_version")
    if not isinstance(raw_version, int) or isinstance(raw_version, bool):
        raise CacheEnvelopeError(
            f"envelope schema_version must be an integer, got {raw_version!r}"
        )
    if raw_version > CACHE_SCHEMA_VERSION:
        raise CacheVersionError(
            f"envelope schema_version {raw_version} is NEWER than this tool understands "
            f"({CACHE_SCHEMA_VERSION}); refusing to misparse it. The cache is disposable: "
            f"a newer entry is rebuilt by the newer tool, or discarded by this one."
        )
    if raw_version < CACHE_SCHEMA_VERSION:
        raise CacheVersionError(
            f"envelope schema_version {raw_version} predates this tool's "
            f"{CACHE_SCHEMA_VERSION}; rebuilding rather than migrating (the cache is disposable)."
        )

    unknown = sorted(set(map(str, payload.keys())) - set(ENVELOPE_FIELDS))
    if unknown:
        raise CacheEnvelopeError(
            "envelope carries unknown field(s) "
            + ", ".join(repr(u) for u in unknown)
            + f"; refused rather than dropped (known fields: {', '.join(ENVELOPE_FIELDS)})"
        )
    missing = [f for f in ENVELOPE_FIELDS if f not in payload]
    if missing:
        raise CacheEnvelopeError(
            "envelope is missing required field(s) "
            + ", ".join(repr(m) for m in missing)
        )

    for name, expected in (
        ("tool_version", str),
        ("source_root_id", str),
        ("run_id", str),
        ("is_complete", bool),
        ("source_fingerprint", str),
        ("generated_at", str),
    ):
        if not isinstance(payload[name], expected):
            raise CacheEnvelopeError(
                f"envelope field {name!r} must be {expected.__name__}, "
                f"got {type(payload[name]).__name__}"
            )
    for name in ("source_coverage", "metric_facts"):
        if not isinstance(payload[name], Mapping):
            raise CacheEnvelopeError(f"envelope field {name!r} must be an object")
    for name in ("event_facts", "quality_flags", "warnings"):
        value = payload[name]
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            raise CacheEnvelopeError(f"envelope field {name!r} must be an array")

    # The facts must still satisfy the allowlist on the way IN. A cache file is a file on disk and
    # can be hand-edited, so trusting it because "the projector ran at write time" would let an
    # edited entry reintroduce a forbidden field through the read path.
    metric_facts = privacy.project_metric_facts(payload["metric_facts"])
    event_facts = [privacy.project_event_facts(e) for e in payload["event_facts"]]

    return CacheEnvelope(
        schema_version=raw_version,
        tool_version=payload["tool_version"],
        source_root_id=payload["source_root_id"],
        run_id=payload["run_id"],
        is_complete=payload["is_complete"],
        source_fingerprint=payload["source_fingerprint"],
        source_coverage=dict(payload["source_coverage"]),
        generated_at=payload["generated_at"],
        metric_facts=metric_facts,
        event_facts=event_facts,
        quality_flags=list(payload["quality_flags"]),
        warnings=list(payload["warnings"]),
    )


def load_entry(path: Path | str) -> CacheEnvelope:
    """Read and strictly decode one entry. Raises :class:`CacheEnvelopeError` on anything wrong."""

    target = Path(path)
    try:
        text = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise CacheEnvelopeError(
            f"cache entry could not be read: {exc.strerror}"
        ) from exc
    try:
        payload = json.loads(text)
    except ValueError as exc:
        raise CacheEnvelopeError(f"cache entry is not valid JSON: {exc}") from exc
    return decode_envelope(payload)


# --- The verdict -------------------------------------------------------------------------------
def decide(
    run_dir: Path | str,
    *,
    root_id: str,
    repo: Path | str | None = None,
    run_id: str | None = None,
) -> tuple[CacheDecision, CacheEnvelope | None]:
    """Decide HIT or REBUILD for one run, and return the reusable envelope on a hit.

    The verdict table, each case with the reason code a consumer sees:

    ================================  ==========  ==========================
    Case                              Verdict     Reason
    ================================  ==========  ==========================
    unchanged, terminal, valid entry  ``hit``     ``fresh-complete-entry``
    no entry yet (first scan, added)  ``rebuild`` ``no-entry``
    inputs mutated                    ``rebuild`` ``fingerprint-changed``
    run not terminal (live, resumed)  ``rebuild`` ``run-not-terminal``
    entry was stored as incomplete    ``rebuild`` ``entry-incomplete``
    entry from another schema         ``rebuild`` ``schema-version-mismatch``
    entry corrupt or unreadable       ``rebuild`` ``entry-unreadable``
    ================================  ==========  ==========================

    A REMOVED run produces no decision at all, because it is not enumerated; callers that must
    report removals compare their run list against the cache directory listing.

    Note the ordering: the run's terminal state is checked BEFORE the fingerprint, because a
    non-terminal run whose files happen to be momentarily identical must still rebuild. A resumed
    run reuses its directory, so "the fingerprint matched" is not evidence of stability there.
    """

    base = Path(run_dir)
    rid = run_id or base.name
    target = entry_path(root_id, rid, repo)

    if not run_is_terminal(base):
        return (
            CacheDecision(
                rid, "rebuild", "run-not-terminal", "run is live or resumable"
            ),
            None,
        )

    try:
        envelope = load_entry(target)
    except FileNotFoundError:
        return CacheDecision(rid, "rebuild", "no-entry", "no cached entry"), None
    except CacheVersionError as exc:
        return CacheDecision(rid, "rebuild", "schema-version-mismatch", str(exc)), None
    except (CacheEnvelopeError, privacy.PrivacyRefusal) as exc:
        return CacheDecision(rid, "rebuild", "entry-unreadable", str(exc)), None

    if not envelope.is_complete:
        return (
            CacheDecision(
                rid, "rebuild", "entry-incomplete", "entry was cached mid-run"
            ),
            None,
        )
    current = source_fingerprint(base)
    if current != envelope.source_fingerprint:
        return (
            CacheDecision(
                rid, "rebuild", "fingerprint-changed", "analytics inputs changed"
            ),
            None,
        )
    return CacheDecision(
        rid, "hit", "fresh-complete-entry", "reused without reparsing"
    ), envelope


# --- Publication -------------------------------------------------------------------------------
def _publish(
    envelope: CacheEnvelope, *, repo: Path | str | None = None
) -> CacheDecision:
    """Serialize on the entry's lock, then replace the entry atomically.

    THE LOCK IS ``platform_lock`` AND NOT ``filelock``/``fcntl``, for three measured reasons
    recorded in that module: acquisition is NON-BLOCKING by default and exactly one caller in the
    package (``project_registry.save_registry``) is permitted to block, so an accidental wait here
    would hang an analyzer rather than fail it; ``filelock`` is deliberately NOT re-entrant through
    this API because a second ``acquire()`` on the same object would SUCCEED via a per-object
    counter and silently break mutual exclusion; and ``filelock``'s POSIX backend opens with
    ``O_CREAT | O_TRUNC``, so a FAILED acquire would DESTROY the record of the live holder that
    just refused, corrupting exactly the diagnostic being read. ``probe_free`` is the only safe
    observation.

    A BUSY lock is a SKIP with a recorded reason, never a wait and never a silent pass. The work is
    recomputable, so a skip costs one rebuild on the next invocation while a block costs the
    operator their run; and because :class:`CacheReport` surfaces ``skip`` with its reason, a
    contended entry is visible in the decision output rather than being mistaken for a hit.
    """

    directory = entry_dir(envelope.source_root_id, envelope.run_id, repo)
    if not path_is_within_analytics(directory, repo):
        raise CacheError(
            f"refusing to write a cache entry outside the reserved analytics tree: {directory}"
        )
    directory.mkdir(parents=True, exist_ok=True)
    lock_file = directory / _LOCK_FILENAME
    try:
        handle = platform_lock.acquire(lock_file)
    except platform_lock.LockBusy:
        return CacheDecision(
            envelope.run_id,
            "skip",
            "lock-busy",
            "another analyzer holds this entry; skipped without waiting",
        )
    try:
        atomic_write_json(directory / ENTRY_FILENAME, encode_envelope(envelope))
    except OSError as exc:
        return CacheDecision(
            envelope.run_id,
            "skip",
            "write-failed",
            f"entry could not be written: {exc.strerror}",
        )
    finally:
        handle.release()
    return CacheDecision(
        envelope.run_id, "rebuild", "no-entry", "rebuilt and published"
    )


def update_cache(
    run_dirs: Iterable[Path | str],
    *,
    build_facts,
    repo: Path | str | None = None,
    root_id: str | None = None,
    salt: str | None = None,
) -> CacheReport:
    """Bring the cache up to date for ``run_dirs`` and report what happened to each.

    ``build_facts(run_dir)`` is supplied by the fact producer and returns
    ``(metric_facts, event_facts, quality_flags, warnings)``; this module owns validity, privacy
    and publication, and deliberately owns no parsing. A single run's failure NEVER aborts the
    sweep: one corrupt entry, one refused fact set or one contended lock is isolated to its own
    decision, which is what makes a 135-run corpus analyzable in the presence of one bad member.
    """

    root = cache_root(repo)
    if salt is None:
        salt = privacy.load_or_create_salt(root)
    if root_id is None:
        root_id = source_root_id(root.parent.parent, salt=salt)

    decisions: list[CacheDecision] = []
    for run_dir in run_dirs:
        base = Path(run_dir)
        rid = base.name
        decision, envelope = decide(base, root_id=root_id, repo=repo, run_id=rid)
        if decision.verdict == "hit":
            decisions.append(decision)
            continue
        try:
            metric_facts, event_facts, quality_flags, warnings = build_facts(base)
        except Exception as exc:  # noqa: BLE001 - one run's failure must not end the sweep
            decisions.append(
                CacheDecision(
                    rid,
                    "skip",
                    "build-refused",
                    privacy.redact_text(f"{type(exc).__name__}: {exc}", salt=salt),
                )
            )
            continue
        try:
            envelope = build_entry(
                run_id=rid,
                root_id=root_id,
                run_dir=base,
                metric_facts=metric_facts,
                event_facts=event_facts,
                quality_flags=quality_flags,
                warnings=warnings,
            )
        except privacy.PrivacyRefusal as exc:
            decisions.append(
                CacheDecision(
                    rid,
                    "skip",
                    "build-refused",
                    privacy.redact_text(str(exc), salt=salt),
                )
            )
            continue
        published = _publish(envelope, repo=repo)
        detail = (
            "rebuilt and published"
            if published.verdict == "rebuild"
            else published.detail
        )
        decisions.append(
            CacheDecision(
                rid,
                published.verdict,
                decision.reason if published.verdict == "rebuild" else published.reason,
                detail,
            )
        )
    return CacheReport(decisions=decisions)


# --- Small helpers -----------------------------------------------------------------------------
def _tool_version() -> str:
    try:
        from agent_workflows import __version__ as version

        return str(version)
    except Exception:  # noqa: BLE001 - a version lookup must never break a cache write
        return "unknown"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
