#!/usr/bin/env python3
"""The versioned SOURCE layer: what a run directory provides, per driver generation.

WHAT THIS ANSWERS. A run corpus spans several driver generations and each wrote a slightly different
``state.json``. Before any fact can be normalized, something must say WHICH artifacts a given run
actually carries, WHICH generation wrote it, and WHICH fields that generation is capable of
providing at all. That is this module. It reads; it does not normalize (see
:mod:`agent_workflows.run_analytics_schema` for the fact contract and
:mod:`agent_workflows.run_analytics` for the composition).

THE GENERATION IS INFERRED FROM ``driver.path``, NOT FROM ``schema_version``, AND THAT IS MEASURED.
Across this repository's own 135-run corpus at review, ``schema_version`` was uniformly ``1`` in
EVERY run while three different drivers had written them (``oc_runipd.py`` 120, the legacy
``tools/ipdrunner/runipd.py`` 13, ``tools/ipdrunner/ipdrunner.py`` 2). So ``schema_version`` is
necessary but INSUFFICIENT: it cannot discriminate generations and a version-dispatch built on it
would route every historical run to the newest adapter. :func:`driver_generation` therefore keys on
the ``driver.path`` basename, and :func:`inventory_run` records the version alongside it as
corroboration rather than as the discriminator.

THREE SOURCES ARE FIXTURE-ONLY, AND SAYING SO IS PART OF THE JOB.
:data:`FIXTURE_ONLY_SOURCES` names them with the reason each cannot be validated against real data:

* ``agy`` - ZERO Agy runs exist in the corpus, so the Agy adapter conforms to its own assumptions
  and to the ``agy_runipd`` code, never to an observed Agy run. A passing Agy test is NOT cross-host
  corpus validation and must not be reported as such.
* ``ledger`` - ``ledger.jsonl`` was present in ZERO of 135 runs.
* ``telemetry`` - ``telemetry/`` was present in ZERO, which is EXPECTED: the Order that emits it
  (``5f2h8i``) had not executed when the corpus was measured. Runs recorded after it will carry it.

THE REAL DRIFT SURFACE IS A STABLE CORE PLUS FOUR OPTIONAL KEYS, ALSO MEASURED. Six distinct
``state.json`` top-level key shapes existed across the corpus; fourteen keys appeared in ALL of them
(:data:`CORE_STATE_KEYS`) and exactly four varied (:data:`OPTIONAL_STATE_KEYS`). So
:func:`read_state` requires the fourteen, tolerates the four, and records an UNKNOWN key in the
coverage report WITHOUT failing, because a newer driver will add more and a fatal unknown key would
make this module refuse the very future it exists to tolerate.

PRECEDENCE IS NOT REIMPLEMENTED HERE. ``run_viewer.extract_step_usage`` already implements the exact
rule this layer needs (prefer a stored ``attempt["cost"]``/``attempt["tokens"]``, fall back to
``extract_log_metrics`` over the session log only when both are absent, with the relative-path and
moved-log fallbacks), and it is tested. :func:`extract_attempt_usage` DELEGATES to it.
A second precedence rule would agree with it today and diverge after the first bug fix in either,
so there is exactly one, with two callers: the viewer's own call sites and this one.

NOTHING HERE WRITES. Source run directories are read-only inputs; every function in this module is a
reader, and a run that cannot be read degrades ITSELF with a recorded reason and never another run.

Stdlib only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Mapping

__all__ = [
    "SOURCE_SCHEMA_VERSION",
    "CORE_STATE_KEYS",
    "OPTIONAL_STATE_KEYS",
    "KNOWN_STATE_KEYS",
    "DRIVER_GENERATIONS",
    "GENERATION_UNKNOWN",
    "FIXTURE_ONLY_SOURCES",
    "ARTIFACT_NAMES",
    "SourceError",
    "StateReadResult",
    "RunInventory",
    "CorpusInventory",
    "driver_generation",
    "read_state",
    "inventory_run",
    "inventory_corpus",
    "iter_event_lines",
    "read_outcomes",
    "read_telemetry_events",
    "extract_attempt_usage",
    "attempt_phase_usage",
]


#: This module's own version, bumped when the inventory/coverage SHAPE changes.
SOURCE_SCHEMA_VERSION = 1


class SourceError(ValueError):
    """A source artifact could not be read as its generation's contract requires.

    Raised for a MALFORMED required artifact only. An absent optional artifact, an unknown key, or a
    single corrupt line is an OBSERVATION recorded in the coverage report, not an error, because
    treating a tolerable variance as fatal is what makes an ingester unable to read its own history.
    """


# --- The measured drift surface -----------------------------------------------------------------
#: The fourteen ``state.json`` top-level keys measured present in EVERY one of the corpus's six
#: distinct key shapes. Required: a state file lacking one of these is not a run this module can
#: normalize, and guessing would produce facts with no provenance.
CORE_STATE_KEYS: frozenset[str] = frozenset(
    {
        "created_at",
        "driver",
        "manifest",
        "manifest_sha256",
        "options",
        "queue",
        "repo",
        "runbook",
        "runbook_sha256",
        "run_id",
        "schema_version",
        "selectors",
        "set_sessions",
        "updated_at",
    }
)

#: The exactly four keys measured to VARY across the corpus. Optional BY CONTRACT: absence is a
#: normal observation about an older generation, never a defect.
OPTIONAL_STATE_KEYS: frozenset[str] = frozenset(
    {
        "_invocation_start_mono",
        "run_order",
        "session_id",
        "session_turn_counts",
    }
)

KNOWN_STATE_KEYS: frozenset[str] = CORE_STATE_KEYS | OPTIONAL_STATE_KEYS

#: Driver basename -> generation label. The basename is the ONLY discriminator that works; see the
#: module docstring for the ``schema_version`` measurement that rules out the obvious alternative.
DRIVER_GENERATIONS: dict[str, str] = {
    "oc_runipd.py": "oc_runipd",
    "agy_runipd.py": "agy_runipd",
    "runipd.py": "runipd",
    "ipdrunner.py": "ipdrunner",
}

#: The label for a driver basename this module does not recognize. Recorded, never fatal: a future
#: driver is a fact about the corpus, not a parse failure.
GENERATION_UNKNOWN = "unknown"

#: Generation label -> the host it belongs to. ``agy_runipd`` is the Agy host; every other known
#: generation is OpenCode lineage.
_GENERATION_HOSTS: dict[str, str] = {
    "oc_runipd": "opencode",
    "runipd": "opencode",
    "ipdrunner": "opencode",
    "agy_runipd": "agy",
    "scripted": "scripted",
}

#: Sources with NO real-data exemplar, each with the measured reason. A caller reporting coverage
#: MUST surface these rather than implying validation the corpus cannot supply.
FIXTURE_ONLY_SOURCES: dict[str, str] = {
    "agy": (
        "zero Agy runs in the measured corpus; the Agy adapter is validated against "
        "agy_runipd's code and synthetic fixtures only, never an observed Agy run"
    ),
    "ledger": "ledger.jsonl present in zero of the measured runs",
    "telemetry": (
        "telemetry/ present in zero of the measured runs, which is expected: the Order "
        "that emits it had not executed when the corpus was measured"
    ),
}

#: Artifact family -> its path relative to a run directory. A FAMILY LABEL is what reaches a fact;
#: the path stays here so no fact ever carries one.
ARTIFACT_NAMES: dict[str, str] = {
    "state": "state.json",
    "events": "events.jsonl",
    "ledger": "ledger.jsonl",
    "report": "execution-report.md",
    "decisions": "decisions-and-questions.md",
    "outcomes": "outcomes",
    "prompts": "prompts",
    "sessions": "sessions",
    "telemetry": "telemetry",
}


# --- Generation inference -----------------------------------------------------------------------
def driver_generation(state: Mapping[str, Any] | None) -> str:
    """The driver generation label, inferred from ``driver.id`` or ``driver.path``'s BASENAME.

    Returns :data:`GENERATION_UNKNOWN` for an absent, malformed or unrecognized driver record rather
    than raising: an unknown generation is a fact to record, and a corpus older or newer than this
    code must remain readable.

    When ``driver.id`` is present, it is preferred. For pre-cutover records lacking an id, the
    BASENAME of ``driver.path`` is consulted against :data:`DRIVER_GENERATIONS`.
    """

    if not isinstance(state, Mapping):
        return GENERATION_UNKNOWN
    driver = state.get("driver")
    if isinstance(driver, Mapping):
        driver_id = driver.get("id")
        if isinstance(driver_id, str) and driver_id.strip():
            return driver_id.strip()
        raw = str(driver.get("path") or "")
    elif isinstance(driver, str):
        raw = driver
    else:
        raw = ""
    if not raw:
        return GENERATION_UNKNOWN
    basename = Path(raw.replace("\\", "/")).name
    return DRIVER_GENERATIONS.get(basename, GENERATION_UNKNOWN)


def generation_host(generation: str) -> str:
    """The host label for a generation. ``unknown`` for a generation this module does not know."""

    return _GENERATION_HOSTS.get(generation, GENERATION_UNKNOWN)


# --- state.json -------------------------------------------------------------------------------
@dataclass(frozen=True)
class StateReadResult:
    """A parsed ``state.json`` plus what varied about it.

    ``unknown_keys`` is the forward-compatibility record: a key a newer driver added, observed and
    reported and NOT fatal. ``missing_optional_keys`` is the backward-compatibility record: one of
    the four measured-optional keys this generation did not write.
    """

    payload: dict[str, Any]
    generation: str
    schema_version: int | None
    unknown_keys: tuple[str, ...]
    missing_optional_keys: tuple[str, ...]

    @property
    def key_shape(self) -> tuple[str, ...]:
        """The sorted top-level key set, which is what "distinct key shape" means when counting."""

        return tuple(sorted(self.payload.keys()))


def read_state(run_dir: Path | str) -> StateReadResult:
    """Read one ``state.json``, requiring the measured 14-key core and tolerating the rest.

    Raises :class:`SourceError` when the file is absent, is not a JSON object, or lacks a CORE key,
    because none of those can yield facts with honest provenance. Everything else is tolerated and
    recorded: a missing OPTIONAL key and an UNKNOWN key are both normal observations about a corpus
    spanning generations.
    """

    path = Path(run_dir) / ARTIFACT_NAMES["state"]
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SourceError(
            "state.json is absent, so this directory is not a run"
        ) from exc
    except OSError as exc:
        raise SourceError(f"state.json could not be read: {exc.strerror}") from exc
    try:
        payload = json.loads(text)
    except ValueError as exc:
        raise SourceError(f"state.json is not valid JSON: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise SourceError(
            f"state.json must be a JSON object, got {type(payload).__name__}"
        )

    present = set(map(str, payload.keys()))
    absent_core = sorted(CORE_STATE_KEYS - present)
    if absent_core:
        raise SourceError(
            "state.json is missing required core key(s) "
            + ", ".join(repr(k) for k in absent_core)
            + " (the fourteen keys measured present in every generation)"
        )

    raw_version = payload.get("schema_version")
    version = (
        raw_version
        if isinstance(raw_version, int) and not isinstance(raw_version, bool)
        else None
    )
    return StateReadResult(
        payload=dict(payload),
        generation=driver_generation(payload),
        schema_version=version,
        unknown_keys=tuple(sorted(present - KNOWN_STATE_KEYS)),
        missing_optional_keys=tuple(sorted(OPTIONAL_STATE_KEYS - present)),
    )


# --- Inventory ----------------------------------------------------------------------------------
@dataclass(frozen=True)
class RunInventory:
    """WHAT one run directory provides, per its generation.

    This is the read-side answer to "can I even ask that question of this run", so a downstream
    adapter never has to guess whether an absent value means the driver could not write it
    (``unavailable``) or should have and did not (``missing``).
    """

    run_id: str
    generation: str
    host: str
    schema_version: int | None
    #: artifact family -> present?
    artifacts: dict[str, bool] = field(default_factory=dict)
    queue_length: int = 0
    attempt_count: int = 0
    unknown_state_keys: tuple[str, ...] = ()
    missing_optional_state_keys: tuple[str, ...] = ()
    #: The run's sorted ``state.json`` top-level key set. Retained because "how many DISTINCT key
    #: shapes does the corpus hold" is a question about THIS, and deriving it from the artifact
    #: presence map instead (an easy mistake) answers a different question entirely.
    state_key_shape: tuple[str, ...] = ()
    #: Short label codes for anything notable. Never a path and never a formatted exception.
    warnings: tuple[str, ...] = ()
    readable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "generation": self.generation,
            "host": self.host,
            "schema_version": self.schema_version,
            "artifacts": dict(sorted(self.artifacts.items())),
            "queue_length": self.queue_length,
            "attempt_count": self.attempt_count,
            "unknown_state_keys": list(self.unknown_state_keys),
            "missing_optional_state_keys": list(self.missing_optional_state_keys),
            "state_key_shape": list(self.state_key_shape),
            "warnings": list(self.warnings),
            "readable": self.readable,
        }


@dataclass(frozen=True)
class CorpusInventory:
    """The per-generation artifact matrix over a whole corpus, plus the fixture-only record.

    ``generation_counts`` is what V-01 asks for. ``fixture_only`` is carried in the RESULT rather
    than left to prose, so a report cannot accidentally imply real-data coverage for the three
    sources that have none.
    """

    runs: tuple[RunInventory, ...] = ()
    fixture_only: dict[str, str] = field(
        default_factory=lambda: dict(FIXTURE_ONLY_SOURCES)
    )

    @property
    def run_count(self) -> int:
        return len(self.runs)

    @property
    def generation_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for run in self.runs:
            counts[run.generation] = counts.get(run.generation, 0) + 1
        return dict(sorted(counts.items()))

    @property
    def schema_versions(self) -> dict[str, int]:
        """``schema_version`` frequency. Expected to be a SINGLE key, which is the proof it cannot
        discriminate generations while :attr:`generation_counts` shows several."""

        counts: dict[str, int] = {}
        for run in self.runs:
            key = str(run.schema_version)
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    @property
    def artifact_matrix(self) -> dict[str, dict[str, int]]:
        """generation -> artifact family -> present count."""

        matrix: dict[str, dict[str, int]] = {}
        for run in self.runs:
            row = matrix.setdefault(run.generation, {})
            for family in ARTIFACT_NAMES:
                row.setdefault(family, 0)
                if run.artifacts.get(family):
                    row[family] += 1
        return {g: dict(sorted(r.items())) for g, r in sorted(matrix.items())}

    @property
    def key_shape_count(self) -> int:
        """How many DISTINCT ``state.json`` top-level key shapes the corpus holds.

        Counted over :attr:`RunInventory.state_key_shape`, i.e. the actual state keys, and NOT over
        the artifact-presence map: the two are different questions and the review measured this one
        (six distinct shapes across 135 runs). Unreadable runs contribute no shape.
        """

        return len({r.state_key_shape for r in self.runs if r.state_key_shape})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SOURCE_SCHEMA_VERSION,
            "run_count": self.run_count,
            "generation_counts": self.generation_counts,
            "schema_versions": self.schema_versions,
            "artifact_matrix": self.artifact_matrix,
            "fixture_only": dict(sorted(self.fixture_only.items())),
            "runs": [r.to_dict() for r in self.runs],
        }

    def format_matrix(self) -> str:
        """A pasteable per-generation matrix, which is the evidence V-01 requires.

        Emits no path and no absolute location, so the output is safe to paste into a plan.
        """

        lines = [
            f"run_count={self.run_count}  distinct_state_key_shapes={self.key_shape_count}",
            "generation counts (from driver.path basename):",
        ]
        for gen, count in self.generation_counts.items():
            lines.append(f"  {gen:<12} {count}")
        lines.append(
            "schema_version frequency (INSUFFICIENT as a discriminator): "
            + ", ".join(f"{k}={v}" for k, v in self.schema_versions.items())
        )
        lines.append("artifact presence per generation:")
        for gen, row in self.artifact_matrix.items():
            rendered = "  ".join(f"{fam}={n}" for fam, n in row.items())
            lines.append(f"  {gen:<12} {rendered}")
        lines.append("fixture-only sources (no real-data exemplar):")
        for name, reason in sorted(self.fixture_only.items()):
            lines.append(f"  {name}: {reason}")
        return "\n".join(lines)


def inventory_run(run_dir: Path | str) -> RunInventory:
    """Inventory ONE run directory. Never raises for a damaged run: it reports it unreadable.

    That containment is the requirement, not politeness. A corpus is analyzed as a whole, so one
    unparseable member must degrade ITSELF and nothing else; raising here would abort the sweep and
    lose the other 134 runs' facts to one bad file.
    """

    base = Path(run_dir)
    run_id = base.name
    artifacts = {
        family: (base / rel).exists() for family, rel in ARTIFACT_NAMES.items()
    }

    try:
        state = read_state(base)
    except SourceError:
        return RunInventory(
            run_id=run_id,
            generation=GENERATION_UNKNOWN,
            host=GENERATION_UNKNOWN,
            schema_version=None,
            artifacts=artifacts,
            warnings=("state-unreadable",),
            readable=False,
        )

    queue = state.payload.get("queue")
    queue_list = list(queue) if isinstance(queue, (list, tuple)) else []
    attempts = 0
    for item in queue_list:
        if isinstance(item, Mapping):
            item_attempts = item.get("attempts")
            if isinstance(item_attempts, (list, tuple)):
                attempts += len(item_attempts)

    warnings: list[str] = []
    if state.unknown_keys:
        warnings.append("unknown-state-keys")
    if state.missing_optional_keys:
        warnings.append("missing-optional-state-keys")
    if state.generation == GENERATION_UNKNOWN:
        warnings.append("unknown-driver-generation")
    if not artifacts.get("events"):
        warnings.append("no-events-stream")

    return RunInventory(
        run_id=str(state.payload.get("run_id") or run_id),
        generation=state.generation,
        host=generation_host(state.generation),
        schema_version=state.schema_version,
        artifacts=artifacts,
        queue_length=len(queue_list),
        attempt_count=attempts,
        unknown_state_keys=state.unknown_keys,
        missing_optional_state_keys=state.missing_optional_keys,
        state_key_shape=state.key_shape,
        warnings=tuple(warnings),
        readable=True,
    )


def inventory_corpus(runs_root: Path | str) -> CorpusInventory:
    """Inventory every run under ``runs_root``, skipping the reserved analytics subtree.

    THE ANALYTICS SUBTREE IS EXCLUDED DELIBERATELY, and by CONTAINMENT rather than by name: a
    directory named ``run-*`` inside ``analytics/snapshots/`` is analytics OUTPUT and must never be
    ingested as a driver run, which would feed this tool's own output back into its input. Order 01's
    ``path_is_within_analytics`` is the containment authority and is used here rather than a second
    name check.

    This is the function to call on a box that HAS a corpus, and its
    :meth:`CorpusInventory.format_matrix` output is the measurement V-01 asks for.
    """

    from agent_workflows.runner_shared import path_is_within_analytics

    root = Path(runs_root)
    found: list[RunInventory] = []
    if not root.is_dir():
        return CorpusInventory(runs=())
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if path_is_within_analytics(child):
            continue
        if not (child / ARTIFACT_NAMES["state"]).is_file():
            continue
        found.append(inventory_run(child))
    return CorpusInventory(runs=tuple(found))


# --- Event / outcome / telemetry readers --------------------------------------------------------
def iter_event_lines(path: Path | str) -> Iterator[tuple[int, dict[str, Any] | None]]:
    """Yield ``(line_number, parsed_or_None)`` for each line of a JSONL stream.

    A corrupt line yields ``None`` and the iteration CONTINUES. That is the partial-run rule made
    concrete: one bad line costs its own facts and nothing else, so a truncated stream (the normal
    result of an interrupted driver) still produces every fact before the truncation.

    Note the corpus measured at review parsed 100 percent clean, so this path has no real-data
    exemplar and is exercised by a deliberately corrupted fixture. That is stated so nobody reads
    corpus cleanliness as evidence the handling works.
    """

    target = Path(path)
    if not target.is_file():
        return
    try:
        with target.open("r", encoding="utf-8", errors="replace") as handle:
            for lineno, line in enumerate(handle, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    parsed = json.loads(stripped)
                except ValueError:
                    yield lineno, None
                    continue
                yield lineno, parsed if isinstance(parsed, dict) else None
    except OSError:
        return


def read_outcomes(run_dir: Path | str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Read every ``outcomes/*.json`` file, returning ``(by_filename_stem, warning_labels)``.

    An unreadable or non-object outcome file is SKIPPED with a label rather than raising, for the
    same containment reason as :func:`iter_event_lines`. The returned warnings are short codes, never
    formatted messages, because a formatted message is where a path rides in.
    """

    base = Path(run_dir) / ARTIFACT_NAMES["outcomes"]
    found: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    if not base.is_dir():
        return found, warnings
    for path in sorted(base.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            warnings.append("outcome-unreadable")
            continue
        if not isinstance(payload, Mapping):
            warnings.append("outcome-not-an-object")
            continue
        found[path.stem] = dict(payload)
    return found, warnings


def read_telemetry_events(
    run_dir: Path | str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Read the per-invocation telemetry stream Order 04 emits, if present.

    FIXTURE-ONLY against the measured corpus (``telemetry/`` was present in zero of 135 runs), which
    is expected rather than a defect: the emitting Order had not executed when the corpus was
    measured. Validated against the shipped
    :mod:`agent_workflows.run_analytics_telemetry` schema and synthetic fixtures.

    Reads the directory form (``telemetry/<name>.jsonl``) AND a single top-level
    ``telemetry.jsonl``, because the schema module names the file while the cache module names the
    directory as an analytics-relevant subtree, and a reader that knew only one would silently see
    no telemetry on half the shapes.
    """

    base = Path(run_dir)
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    candidates: list[Path] = []

    directory = base / ARTIFACT_NAMES["telemetry"]
    if directory.is_dir():
        candidates.extend(sorted(directory.rglob("*.jsonl")))
    single = base / "telemetry.jsonl"
    if single.is_file():
        candidates.append(single)

    for path in candidates:
        for _lineno, parsed in iter_event_lines(path):
            if parsed is None:
                warnings.append("telemetry-line-unparseable")
                continue
            events.append(parsed)
    return events, warnings


# --- Precedence: ONE implementation, delegated ---------------------------------------------------
def extract_attempt_usage(
    item: Mapping[str, Any], run_dir: Path | str
) -> tuple[
    float | None,
    dict[str, int],
    float | None,
    dict[str, int],
    float | None,
    dict[str, int],
]:
    """THE source-precedence entry point, DELEGATING to ``run_viewer.extract_step_usage``.

    Returns exactly what the viewer returns:
    ``(total_cost, total_tokens, exec_cost, exec_tokens, verify_cost, verify_tokens)``.

    WHY A DELEGATION AND NOT AN EXTRACTION. The precedence rule (prefer a stored
    ``attempt["cost"]``/``attempt["tokens"]``; fall back to ``extract_log_metrics`` over the session
    log ONLY when both are absent; resolve a relative or moved log path) already exists in ONE tested
    place. Two implementations of a precedence rule agree on the day they are written and diverge
    after the first bug fix in either, so this module adds NO fallback of its own: the viewer and the
    ingester are two CALLERS of one authority. Extracting the body into a shared module would edit
    ``run_viewer.py``, which this plan does not declare in its ``Scope-Paths``; when a plan that does
    declare it performs the extraction, this function's body becomes a one-line call to the new home
    and no caller here changes.

    The import is LOCAL to the call for the reason the runners already use the same pattern
    (``oc_runipd`` imports ``extract_log_metrics`` at its call site): it keeps module import order
    free of a cycle, since the viewer imports from the shared runner layer this package also uses.
    """

    from agent_workflows.run_viewer import extract_step_usage

    return extract_step_usage(dict(item), Path(run_dir))


def attempt_phase_usage(
    item: Mapping[str, Any], run_dir: Path | str
) -> dict[str, tuple[float | None, dict[str, int]]]:
    """The same delegated precedence, keyed by PHASE, which is the shape the fact layer wants.

    ``{"execute": (cost, tokens), "verify": (cost, tokens), "total": (cost, tokens)}``. Existing run
    summaries already separate execute from verify, and the fact schema must retain that split rather
    than presenting one merged number; this is the adapter that does it WITHOUT a second precedence
    rule.
    """

    total_cost, total_tokens, e_cost, e_tokens, v_cost, v_tokens = (
        extract_attempt_usage(item, run_dir)
    )
    return {
        "execute": (e_cost, e_tokens),
        "verify": (v_cost, v_tokens),
        "total": (total_cost, total_tokens),
    }
