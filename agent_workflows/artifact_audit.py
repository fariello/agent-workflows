"""The ONE artifact location-and-status audit: "is this artifact where its recorded status says it
should be, and does its own front matter agree?"

BOTH `aw runs` AND `aw doctor` CALL THIS MODULE, so the two diagnosis surfaces cannot drift apart.
That wording is deliberate and follows `check_engine.evaluate_review_finding_escalation`, whose
docstring exists for the same reason: an audit VERDICT that two tools compute separately is an audit
two tools will eventually disagree about. Before IPD `6ltz1y` this predicate lived privately in
`run_viewer.py`, so `aw runs` could tell an operator that a step's plan was in the wrong directory
while `aw doctor`, the tool a human actually reaches for, could not see it at all. The in-repo
precedent for the failure this prevents is `render_stream` plus `tests/test_runner_refork_guard.py`,
which pins 28 (runner, symbol) pairs because two host drivers had already re-forked the same helpers.

WHY THE FILE LOOKUP RESOLVES THROUGH ``selectors`` RATHER THAN A PRIVATE DIRECTORY LIST.
The extracted implementation hardcoded nine directories and returned the FIRST filename containing
the queried id6. Two measured defects came with that, and carrying either into a second consumer is
what this module exists to avoid:

* THE TYPE SET. The list covered plans and specs ONLY, so an artifact of any other type carrying the
  queried id6 was invisible: a `backlog` record returned ``None``. Latent for `aw runs` (whose steps
  are plans today) and live for any second consumer. NOTE, because the motivation is easy to get
  wrong: the old list was NOT blind to archived plans. `aw plans archive` writes MONTHLY ``YYYYMM/``
  shards INSIDE the terminal directories (`plans_archive`; `artifact_core.shard_for_date` returns
  ``cleaned[:6]``), those directories were in the list, and the loop used ``rglob``, so a plan at
  ``executed/202608/...`` was already found. The nonexistent ``plans/archive`` entry and the two
  legacy ``.agents/`` paths were dead weight in a list, not blind spots.
* FIRST-MATCH-WINS WITH NO COLLISION POLICY. ``selectors.resolve`` treats an id6 matching several
  files as "a data bug to fix, not overridable by --force" (``MATCH_ID6`` is in ``UNIQUE_KINDS``);
  the private loop silently picked one. :func:`find_artifact` therefore reports a collision through
  :attr:`ArtifactLookup.collisions` instead of hiding it behind an arbitrary pick.

MATCHING SEMANTICS: EXACT DECLARED ``- Id:`` FIRST, FILENAME ID6 SECOND, and both halves are
load-bearing. The exact rule is what makes widening the type set SAFE: the old substring rule would
also match a REVIEW record, because a review carries its SUBJECT's id6 in its filename, and reviews
were previously unreachable only because the hardcoded list never searched them. A review declares
``- Subject-Id:`` and not ``- Id:``, so the exact rule skips it for free. But an exact-only rule
would REGRESS the audit, which is why the filename tier exists: ``selectors`` reads a BOUNDED 4096-
byte header (``selectors._HEADER_BYTES``), and measured on this repository 268 of 1202 records
declare an ``- Id:`` BELOW that cap (this plan's own file declares it at byte 6485), so an exact-only
lookup reports 268 artifacts as ``missing_entirely`` that are plainly on disk. The filename tier is
restricted to the id6 field of the clustered naming grammar (``artifact_naming.parse_clustered``),
never a bare substring, so it cannot match a review record either.

WHY IT IS LIVENESS-AWARE, and do not remove the guard. The audit maps a recorded status onto an
expected directory (terminal statuses onto their terminal directory, everything pre-terminal onto
``pending/``). A step that is RUNNING RIGHT NOW legitimately has its plan in ``pending/`` with a
status that is neither terminal nor ``pending``, so a liveness-blind consumer reports every in-flight
run as drift, which is the fastest way to make a new diagnostic ignored. Liveness is an INPUT here,
never a derivation: it is computed from a RUN DIRECTORY's PID and lock holder
(``run_viewer.inspect_run_pid_and_runtime``, ``is_live=(holder != HOLDER_NONE)``) and this module only
carries it through. ``check_engine._receipt_is_live`` is the in-repo precedent, including its
FAIL-SAFE direction: when liveness cannot be determined, do NOT report.

THE ``aw check`` DECISION (IPD `6ltz1y` E-05, maintainer ruling 2026-09-08): NO, `aw check` does not
gain this audit as a rule, and the tracked-only alternative is not the right shape either.
`aw check` is FAIL-CLOSED in CI, while this audit's expected status comes from a RUN's recorded step
status, and run records live under ``.aw/records/runs/``, which is GITIGNORED and absent from a fresh
clone and from every isolated lane worktree the runner allocates. The same commit would therefore
produce different `aw check` results in CI than locally, and a repository-level gate whose answer
depends on untracked local state is not a gate. WHAT WOULD MAKE A CHECK RULE VIABLE is an audit keyed
ONLY on tracked artifacts (comparing a record's own ``- Status:`` against its directory, with no run
input) - but that predicate ALREADY SHIPS as ``ipd_schema._check_path_status``, surfaced as lint rule
``IPD-M105``, so building it here would duplicate a working rule. The honest remaining gap is
REACHABILITY (getting ``IPD-M105`` into the sweep), which plan `k9awrq` owns. The same
run-record-coupling objection applies to `aw doctor`, which is why the doctor consumer here is
TRACKED-ONLY: see :func:`audit_tracked_artifact`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from agent_workflows import artifact_naming as _naming
from agent_workflows import selectors as _sel

# The status bullet as this audit reads it. Kept byte-identical to the pattern that shipped inside
# `run_viewer` (`^- Status:\s*(\S+)\s*$`) so the extraction changes no verdict: a multi-word status
# yields NO match here, exactly as before, which matches `selectors._STATUS_RE`'s documented parity
# constraint rather than `plans_index._META_RE`'s looser reading.
_STATUS_LINE_RE = re.compile(r"(?m)^- Status:\s*(\S+)\s*$")

# Every record type whose tree may hold an artifact this audit is asked about. `selectors.resolve`
# takes ONE `record_type` per call and there is deliberately no all-types entry point, so a caller
# that does not know the type loops this vocabulary. Ordered by PRECEDENCE, which matters only for
# the filename tier (an exact `- Id:` match is unique by contract, and a multi-type exact match is
# reported as a collision rather than silently resolved). `plans` leads because every caller today
# audits plans; `other` is last because it is a catch-all.
TYPE_PRECEDENCE: tuple[str, ...] = (
    "plans",
    "specs",
    "backlog",
    "releases",
    "roadmaps",
    "research",
    "prompts",
    "walkthroughs",
    "comms",
    "other",
)

# The recorded status values that expect their artifact in a TERMINAL directory of the same name,
# mapped onto that directory. Everything else expects `pending/`.
_TERMINAL_EXPECTED_DIR = {
    "executed": "executed",
    "complete": "executed",
    "superseded": "superseded",
    "not-executed": "not-executed",
    "reusable": "reusable",
}


@dataclass
class ArtifactLookup:
    """The result of locating one artifact, carrying the COLLISION verdict rather than hiding it.

    * ``path``       - the resolved file, or None when nothing matched.
    * ``collisions`` - every path a UNIQUE-by-contract match landed on when there was more than one.
                       Non-empty means the repository has a data bug (one id6 declared by several
                       records); ``path`` is then None, because picking one arbitrarily is exactly
                       the silent behavior this module was extracted to remove.
    * ``kind``       - how it was found: ``id6`` (exact declared ``- Id:``), ``filename-id6`` (the
                       clustered grammar's id6 field), ``configured`` (a caller-supplied path that
                       exists), or None.
    """

    path: Optional[Path] = None
    collisions: List[Path] = None  # type: ignore[assignment]
    kind: Optional[str] = None

    def __post_init__(self) -> None:
        if self.collisions is None:
            self.collisions = []

    @property
    def is_collision(self) -> bool:
        return len(self.collisions) > 1


@dataclass
class ArtifactAudit:
    """One artifact's location/status verdict.

    Field names and semantics are those of the ``StepArtifactAudit`` this replaces, so the run
    viewer's three call sites render byte-identically. ``is_live`` is carried THROUGH from the
    caller and is never derived here (see the module docstring).
    """

    id6: str
    stem: str
    run_status: str
    missing_entirely: bool = False
    location_mismatch: bool = False
    status_mismatch: bool = False
    actual_dir: Optional[str] = None
    expected_dir: Optional[str] = None
    file_status: Optional[str] = None
    actual_path: Optional[Path] = None
    is_live: bool = False
    collisions: List[Path] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.collisions is None:
            self.collisions = []

    @property
    def has_discrepancy(self) -> bool:
        """True when this audit found ANY drift worth reporting."""
        return bool(
            self.missing_entirely or self.location_mismatch or self.status_mismatch
        )


def expected_dir_for_status(status: str) -> str:
    """The directory a record with this recorded ``status`` is expected to sit in.

    Terminal and standing statuses expect their own directory; everything else (draft, to-review,
    reviewed, approved, queued, running, blocked, ...) expects ``pending/``. THE PRE-TERMINAL FALLBACK
    IS WHY A CONSUMER MUST BE LIVENESS-AWARE: a running step's plan is legitimately in ``pending/``
    while its recorded status is ``running``, so the expectation holds only because ``pending/`` is
    the catch-all.
    """
    st = "complete" if status == "substantially-complete" else status
    return _TERMINAL_EXPECTED_DIR.get(st, "pending")


def _filename_id6(name: str) -> Optional[str]:
    """The id6 field of a clustered artifact filename, or None when the name does not parse.

    Deliberately NOT a substring test. A bare substring would also match a review record, which
    carries its SUBJECT's id6 in its filename by convention; parsing the grammar's id6 FIELD cannot.
    """
    m = _naming.parse_clustered(name)
    if not m:
        return None
    try:
        return m.groupdict().get("id6")
    except (AttributeError, IndexError):
        return None


@dataclass
class ArtifactIndex:
    """One traversal's worth of lookup facts: every record path, and the id6 maps built from them.

    * ``paths``           - every record file found, in type-precedence order.
    * ``by_declared_id``  - id6 -> paths whose front matter DECLARES that ``- Id:`` (exact).
    * ``by_filename_id``  - id6 -> paths whose CLUSTERED FILENAME carries that id6 field.

    A map value with more than one path is a COLLISION, which the caller reports rather than
    resolving arbitrarily.
    """

    paths: List[Path]
    by_declared_id: dict
    by_filename_id: dict


# ONE TRAVERSAL PER (root, type-vocabulary), MEMOIZED, because the run viewer audits EVERY step of
# EVERY displayed run and the enumeration is what costs. Measured on this repository: a full
# multi-type walk is ~560ms (of which the `other` catch-all alone is ~330ms for 4 files, since it
# sweeps the whole records tree to find what no type owns), so a per-step walk made
# `tests/test_run_viewer.py` go from 2.4s to 35s. With this cache it is 2.5s.
#
# THE CACHE IS KEYED ON THE RESOLVED ROOT PLUS THE TYPE VOCABULARY AND IS INVALIDATED BY MTIME of
# every record directory in scope, so a test (or a finalize) that MOVES an artifact and re-audits
# sees the move. Directory mtime changes when an entry is added, removed or renamed within it, which
# is exactly the class of change that relocates an artifact; an in-place EDIT of a file's `- Status:`
# does not change its directory's mtime, which is why only the PATH facts are cached here and the
# status is always read fresh in `audit_artifact`.
_INDEX_CACHE: dict = {}
_INDEX_CACHE_MAX = 8


def _dir_signature(repo_root: Path, record_types: Sequence[str]) -> tuple:
    """A cheap invalidation signature: the mtime of every record directory in scope.

    Walks the LITERAL layout (``.aw/records/<type>`` plus legacy ``.agents/<type>``) rather than
    calling ``selectors.record_dirs`` per type. That is deliberate and measured: ``record_dirs``
    consults the project/registry backend on every call (~1.6ms each, ~16ms per signature across the
    vocabulary), which would cost more than the traversal this cache exists to avoid. The signature
    only has to CHANGE when an artifact moves, so covering the literal trees is sufficient; a
    registry-redirected tree simply re-indexes on its own directory mtimes via the same scan below.
    """
    sig: List[tuple] = []
    for base in (repo_root / ".aw" / "records", repo_root / ".agents"):
        for rt in record_types:
            d = base / rt
            try:
                sig.append((str(d), d.stat().st_mtime_ns))
            except OSError:
                continue
            # Disposition subdirectories (and their monthly shards) are where an artifact MOVES to,
            # so their mtimes matter as much as the tree root's.
            try:
                for child in d.iterdir():
                    if child.is_dir():
                        sig.append((str(child), child.stat().st_mtime_ns))
                        for grand in child.iterdir():
                            if grand.is_dir():
                                sig.append((str(grand), grand.stat().st_mtime_ns))
            except OSError:
                continue
    return tuple(sorted(sig))


def build_index(
    repo_root: Path, *, record_types: Sequence[str] = TYPE_PRECEDENCE
) -> ArtifactIndex:
    """Enumerate every record of ``record_types`` ONCE and build both id6 maps.

    Enumeration goes through ``selectors._iter_paths``, so the dual ``.aw/``/``.agents/`` roots, the
    monthly-shard recursion and the traversal exclusions are the resolver's rather than a private
    walk's; the exact ``- Id:`` reading uses ``selectors``' own bounded header reader, so this module
    matches what ``aw find <id6>`` matches.
    """
    repo_root = Path(repo_root)
    try:
        key = (str(repo_root.resolve()), tuple(record_types))
    except OSError:
        key = (str(repo_root), tuple(record_types))
    sig = _dir_signature(repo_root, record_types)
    cached = _INDEX_CACHE.get(key)
    if cached is not None and cached[0] == sig:
        return cached[1]

    paths: List[Path] = []
    by_declared: dict = {}
    by_filename: dict = {}
    seen: set = set()
    for rt in record_types:
        try:
            candidates = list(_sel._iter_paths(repo_root, rt))
        except Exception:
            continue
        for p in candidates:
            k = str(p)
            if k in seen:
                continue
            seen.add(k)
            paths.append(p)
            fid = _filename_id6(p.name)
            if fid:
                by_filename.setdefault(fid, []).append(p)
            header = _sel._read_header(p)
            if header:
                did = _sel._read_id(header)
                if did:
                    by_declared.setdefault(did, []).append(p)

    index = ArtifactIndex(
        paths=paths, by_declared_id=by_declared, by_filename_id=by_filename
    )
    if len(_INDEX_CACHE) >= _INDEX_CACHE_MAX:
        _INDEX_CACHE.clear()
    _INDEX_CACHE[key] = (sig, index)
    return index


def find_artifact(
    repo_root: Path,
    id6: str,
    stem: str = "",
    *,
    record_types: Sequence[str] = TYPE_PRECEDENCE,
) -> ArtifactLookup:
    """Locate the artifact declaring ``id6`` (or named by ``stem``), through ``selectors``.

    TWO TIERS, IN THIS ORDER, and both are needed. TIER ONE asks ``selectors.resolve`` for an EXACT
    declared ``- Id:`` match, restricted to ``MATCH_ID6`` so no other selector kind can win; a
    multi-file result is returned as a COLLISION rather than resolved. TIER TWO falls back to the
    clustered filename's id6 FIELD, because ``selectors`` reads only a bounded 4096-byte header and
    measured on this repository 268 of 1202 records declare their ``- Id:`` below that cap, so an
    exact-only lookup would report those as missing. ``stem`` is matched on the filename as a last
    resort, preserving the extracted behavior for a caller that knows a stem but no id6.

    Never raises for a missing tree or an unreadable file; an absent artifact is a verdict, not an
    error. ``selectors`` is CONSUMED here and never modified.
    """
    repo_root = Path(repo_root)
    if not id6 and not stem:
        return ArtifactLookup()

    index = build_index(repo_root, record_types=record_types)

    # TIER ONE: exact declared `- Id:`. Hits are accumulated ACROSS types, so a cross-type id6
    # collision is reported rather than masked by the type ordering.
    if id6:
        exact = index.by_declared_id.get(id6, ())
        if len(exact) == 1:
            return ArtifactLookup(path=exact[0], kind="id6")
        if len(exact) > 1:
            return ArtifactLookup(
                path=None, collisions=sorted(exact, key=str), kind="id6"
            )

        # TIER TWO: the clustered filename's id6 FIELD (never a bare substring), which the bounded
        # header read makes necessary; see the module docstring's 268-of-1202 measurement.
        by_name = index.by_filename_id.get(id6, ())
        if len(by_name) == 1:
            return ArtifactLookup(path=by_name[0], kind="filename-id6")
        if len(by_name) > 1:
            return ArtifactLookup(
                path=None, collisions=sorted(by_name, key=str), kind="filename-id6"
            )

    # TIER THREE: the stem as a filename substring, the extracted behavior's last resort, kept for a
    # caller that knows a stem but no id6.
    if stem:
        by_stem = [p for p in index.paths if stem in p.name]
        if by_stem:
            return ArtifactLookup(path=sorted(by_stem, key=str)[0], kind="stem")
    return ArtifactLookup()


def read_declared_status(path: Path) -> Optional[str]:
    """The record's own single-token ``- Status:`` value, or None when absent/unreadable.

    A multi-word status yields None, matching the pattern that shipped inside `run_viewer` and
    `selectors._STATUS_RE`'s documented parity constraint.
    """
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    m = _STATUS_LINE_RE.search(txt)
    return m.group(1).strip() if m else None


def _status_disagrees(recorded: str, declared: str) -> bool:
    """Does a record's own ``declared`` status disagree with the ``recorded`` one?

    The tolerance bands are the extracted ones, unchanged: an executed/complete record must read
    executed or complete; a ``reviewed`` record may read reviewed OR approved; a queued/running/
    blocked/dependency-blocked record may read any pre-terminal value, because a plan that has not
    finished legitimately still carries its authoring status; otherwise the two must be equal.
    """
    rec = "complete" if recorded == "substantially-complete" else recorded
    dec = "complete" if declared == "substantially-complete" else declared
    if rec in ("executed", "complete"):
        return dec not in ("executed", "complete")
    if rec == "reviewed":
        return dec not in ("reviewed", "approved")
    if rec in ("queued", "running", "dependency-blocked", "blocked"):
        return dec not in (
            "approved",
            "to-review",
            "draft",
            "reviewed",
            "queued",
            "running",
        )
    return dec != rec


def audit_artifact(
    repo_root: Path,
    id6: str,
    stem: str = "",
    *,
    status: str = "",
    configured_file: str = "",
    is_live: bool = False,
    record_types: Sequence[str] = TYPE_PRECEDENCE,
) -> ArtifactAudit:
    """THE audit predicate: is the artifact for ``id6`` where ``status`` says it should be?

    Takes PRIMITIVE FACTS rather than a run-viewer ``StepSummary`` (IPD `6ltz1y` OQ-01): a step is a
    run-viewer concept carrying run-specific fields, and a doctor-side consumer has no steps and
    would have to fabricate one. Keeping the signature primitive is what makes the dependency
    one-directional; this module must never import `run_viewer`.

    ``configured_file`` short-circuits the search when the caller already knows the path and it
    exists. ``is_live`` is recorded, never derived, and never suppresses a verdict here: the CONSUMER
    decides what to do with an in-flight artifact, and the run viewer's choice (render it, tagged
    ``[in flight]``) differs from the doctor rule's (do not report it at all).
    """
    stem = stem or id6
    recorded = "complete" if status == "substantially-complete" else status
    expected = expected_dir_for_status(status)

    actual_file: Optional[Path] = None
    collisions: List[Path] = []
    if configured_file and (Path(repo_root) / configured_file).is_file():
        actual_file = Path(repo_root) / configured_file
    else:
        lookup = find_artifact(repo_root, id6, stem, record_types=record_types)
        actual_file = lookup.path
        collisions = list(lookup.collisions)

    if actual_file is None:
        return ArtifactAudit(
            id6=id6,
            stem=stem,
            run_status=recorded,
            missing_entirely=True,
            expected_dir=expected,
            is_live=is_live,
            collisions=collisions,
        )

    actual_dir = actual_file.parent.name
    file_status = read_declared_status(actual_file)
    return ArtifactAudit(
        id6=id6,
        stem=stem,
        run_status=recorded,
        missing_entirely=False,
        location_mismatch=actual_dir != expected,
        status_mismatch=bool(
            file_status is not None and _status_disagrees(recorded, file_status)
        ),
        actual_dir=actual_dir,
        expected_dir=expected,
        file_status=file_status,
        actual_path=actual_file,
        is_live=is_live,
        collisions=collisions,
    )


def audit_tracked_artifact(repo_root: Path, path: Path) -> Optional[ArtifactAudit]:
    """The TRACKED-ONLY audit a fail-safe sweeper may run: does a record's OWN declared status agree
    with the directory it sits in?

    THIS IS THE CANNOT-BE-LIVE ROUTE, and the restriction is the whole point (IPD `6ltz1y` E-04
    route (b)). The run-shaped :func:`audit_artifact` compares a RUN's recorded step status against
    the tree, which requires reading ``.aw/records/runs/`` - gitignored, box-local state that
    `doctor.py` reads nowhere. Coupling a tracked-record sweeper to untracked state is the objection
    OQ-03 accepts as decisive against `aw check`, and it applies to `aw doctor` for the same reason:
    the rule would report nothing in a fresh clone or a lane worktree. So the doctor consumer asks
    only what a TRACKED file can answer by itself.

    Returns None (never a finding) in every case where the question cannot be answered safely:

    * the record declares no single-token ``- Status:`` (nothing to compare);
    * the record already sits where its declared status expects it;
    * the record sits in a directory this audit has no expectation about;
    * the record's declared status is PRE-TERMINAL. Such a record may be mid-flight (a running
      execution's plan legitimately carries ``approved`` in ``pending/``), and liveness cannot be
      read from tracked state at all. This is the fail-safe direction
      ``check_engine._receipt_is_live`` establishes: undeterminable means skip.
    * THE RECORD IS STILL IN ``pending/``, even with a terminal declared status. That is the shape of
      a plan CAUGHT MID-FINALIZE - ``ipd_lifecycle.finalize`` writes the status and moves the file,
      and a sweep that runs between the two would report a transaction in progress as drift. It is
      also precisely the direction the shipped ``IPD-M105`` already covers, so skipping it here costs
      no coverage and avoids duplicating a working rule.

    A finding is returned ONLY for the unambiguous, complementary case: a record sitting in a
    TERMINAL directory while its own declared status names a DIFFERENT terminal (or standing)
    disposition. That cannot describe work in progress, because a live execution has not reached a
    terminal status yet and a finalize moves a file only once. THIS IS EXACTLY THE ``IPD-M105`` BLIND
    SPOT, which is what the doctor rule adds rather than duplicates: measured 2026-09-13,
    ``ipd_lint.lint_file`` on a plan in ``executed/`` declaring ``- Status: superseded`` returns
    disposition ``legacy/not evaluated`` with ZERO diagnostics (the whole terminal tree is exempt),
    while the same file in ``pending/`` declaring ``- Status: executed`` does yield ``IPD-M105``.
    """
    path = Path(path)
    declared = read_declared_status(path)
    if not declared:
        return None
    expected = expected_dir_for_status(declared)
    actual_dir = path.parent.name
    # A shard directory (`executed/202608/`) is named for the month, so climb to the disposition.
    if re.fullmatch(r"\d{6}", actual_dir):
        actual_dir = path.parent.parent.name
    if actual_dir == expected:
        return None
    # FAIL SAFE: only a TERMINAL/standing declared status licenses a finding. A pre-terminal record
    # in an unexpected directory may be mid-flight, and liveness cannot be read from tracked state.
    if expected == "pending":
        return None
    # FAIL SAFE: a record still in `pending/` may be mid-finalize, and `IPD-M105` owns that direction.
    if actual_dir == "pending":
        return None
    # Only judge a record that actually lives in a terminal/standing disposition tree.
    if actual_dir not in set(_TERMINAL_EXPECTED_DIR.values()):
        return None
    return ArtifactAudit(
        id6=_filename_id6(path.name) or "",
        stem=path.name,
        run_status=declared,
        missing_entirely=False,
        location_mismatch=True,
        status_mismatch=False,
        actual_dir=actual_dir,
        expected_dir=expected,
        file_status=declared,
        actual_path=path,
        is_live=False,
    )
