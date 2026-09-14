"""Sensitivity-tiered analytics export bundles (runanalytics Order 09, ixis0c: E-02..E-05).

THE ALLOWLIST IS THE PRIVACY BOUNDARY. THE DETECTOR IS NOT, AND THAT IS THE WHOLE POINT OF THIS
MODULE'S SHAPE. It is tempting to build an export by dumping run data and then running the shared
leak sanitizer over it, and that intuition is why this docstring leads with the measurement that
refutes it. Measured on 2026-09-14 against :func:`agent_workflows.leak_sanitizer.scan_text` at
``fail`` severity over the twelve canary classes this plan's tests enumerate, only TWO are caught:
a home path and the maintainer's own username. A git remote, a branch name, a commit message, an
``AWS_SECRET_ACCESS_KEY=`` assignment, an ``sk-proj-`` API token, prompt text, a shell command, a
``=cmd|`` spreadsheet formula and a ``../../../etc/passwd`` traversal string ALL return ZERO
findings at BOTH ``fail`` and ``warn``.

WORSE, THE SECOND CATCH DOES NOT TRANSFER TO AN ADOPTER. The username hit comes from the ``handle``
rule, one of three rules (``handle``, ``private-repo``, ``other-account``) compiled from THIS
maintainer's literal tokens. Verified: another user's handle and another private repository name both
return zero findings, while the generic ``home-path`` and ``session-id`` rules do match. So on a
machine that is not the maintainer's, coverage falls to ONE of twelve, and it falls off exactly where
the data is not the maintainer's own. The module has no entropy check and no secret-shape rule at all
(no ``AKIA``, no ``BEGIN ... KEY``): secret scanning in this repository is ``gitleaks`` running in a
CI job over git history, which an export code path cannot invoke.

The consequence is structural rather than stylistic. A bundle is built by NAMING WHAT MAY LEAVE, so
an unnamed field is absent because nothing ever wrote it, not because a pattern failed to match it.
The detector still runs, and its result still ships, but as CORROBORATION carrying an explicit
enumeration of what it does not look for. A report that said "sanitizer clean" without that
enumeration would tell a user their data was checked for things it was never checked for, which is
the one outcome this module exists to prevent.

Three tiers, in increasing sensitivity:

``metrics``
    The default. Re-emits facts that ALREADY crossed Order 02's write-side projector
    (:func:`agent_workflows.run_analytics_privacy.project_facts`), plus aggregate metadata. This
    module deliberately builds NO second projector and NO second sanitizer: Order 02's plan states
    its projector is "the only path by which a fact reaches the envelope", and a competing filter
    here would be a second boundary to keep in sync and a second place to get it wrong.

``events-redacted``
    Bounded structured event facts, field-allowlisted, shipping the blind-spot report.

``raw``
    Selected original run artifacts. May contain prompts, conversations, code, commands, paths and
    secrets. Never the default, never labelled safe, and (see
    :mod:`agent_workflows.run_analytics_submit`) never transmissible.

NEITHER ``metrics`` NOR ``events-redacted`` IS ANONYMOUS, and no string in this module says
otherwise. They are MINIMIZED. Re-identification from timing, sequence and volume is not addressed
by an allowlist, and :func:`residual_risk_notes` states that in the bundle itself rather than in a
docstring a user will never read.
"""

from __future__ import annotations

import hashlib
import json
import re
import tarfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "ExportRefusal",
    "TIERS",
    "DEFAULT_TIER",
    "RAW_TIER",
    "EXPORT_SCHEMA_VERSION",
    "ALLOWED_EXPORT_EVENT_FIELDS",
    "CANARY_CLASSES",
    "DETECTOR_BLIND_SPOTS",
    "DETECTOR_COVERED_CLASSES",
    "ExportManifestEntry",
    "ExportPreview",
    "ExportBundle",
    "tier_is_sensitive",
    "tier_claims_safety",
    "residual_risk_notes",
    "build_metrics_payload",
    "build_redacted_events",
    "sanitizer_blind_spot_report",
    "select_raw_files",
    "preview_raw_selection",
    "build_manifest",
    "write_bundle",
    "archive_member_refusal",
    "tarfile_data_filter_available",
    "safe_extract",
]


class ExportRefusal(ValueError):
    """An export was REFUSED rather than silently narrowed.

    Deliberately a refusal, for the same reason Order 02's :class:`PrivacyRefusal` is one: a caller
    who asked for a tier and got a quietly reduced one would believe the bundle contains data it
    does not, and a caller who passed an unnamed field and got a silent drop would believe the
    allowlist had blessed it. "Refused" is a state a test can assert; "dropped" is not.
    """


#: The sensitivity tiers, ordered least to most sensitive. Order is meaningful: `_TIER_RANK` uses it.
TIERS: tuple[str, ...] = ("metrics", "events-redacted", "raw")

#: The tier used when a caller names none. `metrics` and nothing else.
DEFAULT_TIER: str = "metrics"

#: Named rather than spelled inline, so the "is this the dangerous one" test reads as a predicate.
RAW_TIER: str = "raw"

#: Bumped when the bundle's on-disk shape changes. A consumer that cannot read a version REFUSES it
#: rather than guessing, which is the posture Order 02's `CacheVersionError` already established.
EXPORT_SCHEMA_VERSION: int = 1

_TIER_RANK: dict[str, int] = {name: i for i, name in enumerate(TIERS)}


# --- The `events-redacted` field allowlist ------------------------------------------------------
# THIS IS THE GUARANTEE, so it is a short, closed, deliberately boring list. It is a SUBSET of
# Order 02's `ALLOWED_EVENT_KEYS`: a field may be safe to hold in a local disposable cache and still
# be wrong to put in a bundle a human may hand to someone else. Adding a name here widens what
# leaves the machine, so it belongs with a test that says why.
ALLOWED_EXPORT_EVENT_FIELDS: frozenset[str] = frozenset(
    {
        "event_type",
        "timestamp",
        "sequence",
        "phase",
        "activity",
        "duration_seconds",
        "tokens",
        "token_total",
        "cost",
        "outcome",
        "payload_byte_count",
        "payload_field_count",
        "quality_flags",
    }
)


#: The canary classes the plan's required tests enumerate. Kept as a NAMED TUPLE OF CLASS NAMES
#: rather than as example strings on purpose: the gate forbids committing a canary as a literal, so
#: tests assemble their own payloads from fragments and index into this vocabulary by name.
CANARY_CLASSES: tuple[str, ...] = (
    "prompt-text",
    "response-text",
    "shell-command",
    "filesystem-path",
    "hostname",
    "username",
    "git-remote",
    "branch-name",
    "commit-message",
    "environment-secret",
    "high-entropy-token",
    "spreadsheet-formula",
    "archive-traversal",
)

#: What the shared detector DOES catch, measured. Two entries, and one of them
#: (``username``, via the maintainer-specific ``handle`` rule) does not transfer to another machine.
DETECTOR_COVERED_CLASSES: tuple[str, ...] = ("filesystem-path", "username")

#: What the shared detector does NOT look for. This is the enumeration that must ship: a report
#: listing a clean scan without it advertises a guarantee the detector does not provide.
DETECTOR_BLIND_SPOTS: tuple[str, ...] = tuple(
    name for name in CANARY_CLASSES if name not in DETECTOR_COVERED_CLASSES
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tier_is_sensitive(tier: str) -> bool:
    """True if `tier` may carry original content, so it needs the explicit attestation."""

    return _tier_rank(tier) >= _TIER_RANK[RAW_TIER]


def _tier_rank(tier: str) -> int:
    try:
        return _TIER_RANK[tier]
    except KeyError:
        raise ExportRefusal(
            f"unknown export tier {tier!r}; choose one of {', '.join(TIERS)}"
        ) from None


def tier_claims_safety(tier: str) -> bool:
    """Always False, for every tier, and the constant is the contract.

    A function rather than an absent feature so a test can assert the claim is unmakeable rather
    than merely unmade. No tier here is anonymous: ``metrics`` is minimized and pseudonymized,
    ``events-redacted`` is field-allowlisted, and ``raw`` is original content. Minimization is not
    anonymity, and the plan forbids claiming anonymization that was never independently
    demonstrated.
    """

    _tier_rank(tier)  # still refuse an unknown tier rather than answering about it
    return False


def residual_risk_notes(tier: str) -> tuple[str, ...]:
    """The risks that SURVIVE this tier's redaction, stated in the bundle a human actually reads."""

    rank = _tier_rank(tier)
    shared = (
        "This bundle is MINIMIZED, not anonymous. No anonymization has been independently "
        "demonstrated, so none is claimed.",
        "Timing, ordering and volume are preserved by design (they are the analytic payload) and "
        "can support re-identification or inference that a field allowlist does not address.",
        "Pseudonyms are stable within one machine and one cache generation, so repeated exports "
        "from the same machine are linkable to each other.",
        "The shared leak detector was run as corroboration only. Measured, it catches "
        f"{len(DETECTOR_COVERED_CLASSES)} of {len(CANARY_CLASSES)} canary classes, and one of "
        "those two relies on a maintainer-specific rule that matches nothing on another machine.",
    )
    if rank == _TIER_RANK["metrics"]:
        return shared + (
            "Facts here already crossed the write-side projector; that means they were minimized "
            "when cached, NOT that they were cleared for release.",
        )
    if rank == _TIER_RANK["events-redacted"]:
        return shared + (
            "Event fields are allowlisted, so an unnamed field is absent because nothing wrote "
            "it. Values of NAMED fields are still real observations.",
            "Counts such as payload_byte_count describe content that is not included, but a size "
            "can itself be identifying.",
        )
    return shared + (
        "THIS IS THE RAW TIER. It contains ORIGINAL run artifacts and may include prompts, "
        "conversations, source code, commands, filesystem paths, hostnames and secrets.",
        "Nothing in this tier has been redacted, filtered or checked. Review every file listed in "
        "the manifest before sharing it with anyone.",
    )


# --- E-02: the `metrics` tier -------------------------------------------------------------------


def build_metrics_payload(
    envelopes: Sequence[Any],
    *,
    projector_version: int | None = None,
    tool_version: str = "",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Re-emit ALREADY-PROJECTED facts as the `metrics` tier. Builds no second filter.

    Each element of `envelopes` must be an Order 02
    :class:`~agent_workflows.run_analytics_cache.CacheEnvelope` (or any object exposing the same
    attributes). Its ``metric_facts`` already crossed
    :func:`~agent_workflows.run_analytics_privacy.project_metric_facts` in ``build_entry``, so this
    function RE-VALIDATES against the same allowlist rather than applying a different one. That
    re-validation is not redundant: it is what makes "the bundle contains only allowlisted keys" a
    property of the bundle rather than a property inherited on trust from an upstream writer.

    The bundle records WHICH projector generation produced it, because a consumer reading a bundle
    a year from now cannot otherwise tell which allowlist was in force.
    """

    from agent_workflows import run_analytics_privacy as privacy

    if projector_version is None:
        projector_version = _projector_version()

    runs: list[dict[str, Any]] = []
    refusals: list[str] = []
    for env in envelopes:
        facts = dict(getattr(env, "metric_facts", None) or {})
        try:
            # THE SAME allowlist Order 02 wrote. Not a copy, not a subset, not a second policy.
            projected = privacy.project_metric_facts(facts)
        except privacy.PrivacyRefusal as exc:
            # A refusal here means an upstream envelope carried a key the allowlist does not name,
            # which is a real defect worth surfacing rather than a fact worth shipping.
            refusals.append(f"{getattr(env, 'run_id', '<unknown>')}: {exc}")
            continue
        runs.append(projected)

    payload: dict[str, Any] = {
        "tier": "metrics",
        "schema_version": EXPORT_SCHEMA_VERSION,
        "projector_version": projector_version,
        "projector_allowlist_size": len(privacy.ALLOWED_METRIC_KEYS),
        "tool_version": tool_version,
        "generated_at": generated_at or _utc_now(),
        "run_count": len(runs),
        "runs": runs,
        "refused_records": refusals,
        "claims_anonymity": False,
        "residual_risk": list(residual_risk_notes("metrics")),
    }
    return payload


def _projector_version() -> int:
    """The write-side cache schema generation, which is what pins the allowlist in force."""

    try:
        from agent_workflows import run_analytics_cache as cache

        value = getattr(cache, "SCHEMA_VERSION", None)
        if isinstance(value, int):
            return value
    except Exception:  # pragma: no cover - defensive: a bundle should still build
        pass
    return EXPORT_SCHEMA_VERSION


# --- E-03: the `events-redacted` tier -----------------------------------------------------------


def build_redacted_events(
    envelopes: Sequence[Any],
    *,
    max_events_per_run: int | None = None,
) -> dict[str, Any]:
    """Field-allowlist event facts STRUCTURALLY. An unnamed field is never written.

    The redaction is a construction, not a scan: the output dict is built by iterating
    :data:`ALLOWED_EXPORT_EVENT_FIELDS` and copying only those names. There is no code path by
    which an unnamed key reaches the result, so "the prompt text is absent" is true because nothing
    ever wrote it, and it stays true for a canary class no pattern would have matched.

    An unnamed field is DROPPED here rather than refused, and that differs deliberately from
    Order 02's projector. Order 02 sits on the WRITE path, where an unexpected key means the
    producer and the schema disagree and someone must fix it. This sits on the EXPORT path, where
    the input is an already-validated cache and the job is to narrow it further; refusing the whole
    bundle because a cache carried a legitimately cached field that is merely too sensitive to
    export would make the tier unusable. The count of what was dropped is reported, so the
    narrowing is visible rather than silent.
    """

    runs: list[dict[str, Any]] = []
    dropped_field_names: set[str] = set()
    total_dropped = 0
    for env in envelopes:
        events_out: list[dict[str, Any]] = []
        for raw_event in list(getattr(env, "event_facts", None) or []):
            if not isinstance(raw_event, Mapping):
                continue
            kept: dict[str, Any] = {}
            for name in sorted(ALLOWED_EXPORT_EVENT_FIELDS):
                if name in raw_event:
                    kept[name] = raw_event[name]
            for present in raw_event.keys():
                if str(present) not in ALLOWED_EXPORT_EVENT_FIELDS:
                    dropped_field_names.add(str(present))
                    total_dropped += 1
            events_out.append(kept)
            if max_events_per_run is not None and len(events_out) >= max_events_per_run:
                break
        runs.append(
            {
                "run_id": getattr(env, "run_id", None),
                "source_root_id": getattr(env, "source_root_id", None),
                "event_count": len(events_out),
                "events": events_out,
            }
        )

    return {
        "tier": "events-redacted",
        "schema_version": EXPORT_SCHEMA_VERSION,
        "redaction_method": "structural-field-allowlist",
        "allowlisted_fields": sorted(ALLOWED_EXPORT_EVENT_FIELDS),
        "dropped_field_names": sorted(dropped_field_names),
        "dropped_field_occurrences": total_dropped,
        "run_count": len(runs),
        "runs": runs,
        "claims_anonymity": False,
        "residual_risk": list(residual_risk_notes("events-redacted")),
    }


def sanitizer_blind_spot_report(
    text_samples: Iterable[str] = (),
    *,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """The corroborating detector pass, shipping its own MEASURED LIMITS by name.

    Runs the shared detector over `text_samples` and returns both what it found and, crucially, an
    explicit enumeration of the canary classes it does not look for. The enumeration is the point.
    A report saying only "0 findings" would be read as "checked and clean", when the measured truth
    is "checked for two of thirteen categories, one of which only matches on the maintainer's own
    machine".
    """

    findings: list[dict[str, Any]] = []
    detector_available = True
    detector_error = ""
    try:
        from agent_workflows import leak_sanitizer

        ruleset = leak_sanitizer.build_ruleset(Path(repo_root or "."))
        rule_names = sorted(getattr(leak_sanitizer, "_FAIL_PATTERNS", {}).keys())
        for index, sample in enumerate(text_samples):
            for hit in leak_sanitizer.scan_text(
                str(sample), f"sample[{index}]", ruleset
            ):
                findings.append(
                    {"location": hit.location, "rule": hit.rule, "severity": "fail"}
                )
    except (
        Exception
    ) as exc:  # pragma: no cover - the report must not be the thing that breaks
        detector_available = False
        detector_error = f"{type(exc).__name__}: {exc}"
        rule_names = []

    return {
        "detector": "agent_workflows.leak_sanitizer",
        "detector_available": detector_available,
        "detector_error": detector_error,
        "detector_role": (
            "CORROBORATION ONLY. The privacy boundary of this bundle is the write-side field "
            "allowlist. This scan can raise confidence; it cannot establish safety."
        ),
        "fail_rules_in_force": rule_names,
        "findings": findings,
        "finding_count": len(findings),
        "canary_classes_considered": list(CANARY_CLASSES),
        "classes_this_detector_catches": list(DETECTOR_COVERED_CLASSES),
        "classes_this_detector_does_not_look_for": list(DETECTOR_BLIND_SPOTS),
        "measured_coverage": (
            f"{len(DETECTOR_COVERED_CLASSES)} of {len(CANARY_CLASSES)} canary classes"
        ),
        "maintainer_specific_rules": ["handle", "private-repo", "other-account"],
        "maintainer_specific_caveat": (
            "The `handle`, `private-repo` and `other-account` rules are compiled from this "
            "repository maintainer's own tokens. On any other machine they match nothing, so "
            "measured coverage there is LOWER than the figure above."
        ),
        "no_secret_shape_detection": (
            "This detector has no entropy test and no secret-shape rule (no AKIA, no "
            "'BEGIN ... KEY', no provider token prefixes). Secret scanning in this repository is "
            "gitleaks in a CI job over git history, which an export code path cannot invoke."
        ),
    }


# --- E-04: the `raw` tier ------------------------------------------------------------------------

#: Category buckets for the raw preview, as (label, matcher). A preview that listed every file would
#: be unusable at real corpus scale, so the summary is by category with counts and bytes.
_RAW_CATEGORIES: tuple[tuple[str, str], ...] = (
    ("prompts", "prompt"),
    ("sessions", "session"),
    ("outcomes", "outcome"),
    ("events", "event"),
    ("reports", "report"),
    ("state", "state"),
)


@dataclass(frozen=True)
class ExportManifestEntry:
    """One file in the bundle, with the checksum that makes tampering detectable."""

    path: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "size_bytes": self.size_bytes, "sha256": self.sha256}


@dataclass(frozen=True)
class ExportPreview:
    """What a `raw` export WOULD copy, shown before anything is written.

    This listing is the only review a human gets before original content leaves its run directory,
    so it reports totals and per-category counts rather than a flat file list. Measured at review,
    the live corpus held on the order of 470 prompt and 460 session files at roughly 238 MB; a flat
    listing of that is not a review artifact.
    """

    tier: str
    file_count: int
    total_bytes: int
    categories: dict[str, dict[str, int]] = field(default_factory=dict)
    files: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "categories": {k: dict(v) for k, v in self.categories.items()},
            "files": list(self.files),
            "warnings": list(self.warnings),
            "claims_anonymity": False,
        }


@dataclass(frozen=True)
class ExportBundle:
    """A written bundle: its directory, its manifest, and the tier that produced it."""

    tier: str
    root: Path
    manifest_path: Path
    entries: tuple[ExportManifestEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "root": str(self.root),
            "manifest_path": str(self.manifest_path),
            "file_count": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }


def select_raw_files(
    run_dirs: Sequence[Path | str],
    *,
    include: Sequence[str] | None = None,
) -> list[Path]:
    """The explicit file selection for a `raw` export. Sorted, so a manifest is deterministic.

    `include` is a sequence of substring selectors; when omitted NOTHING is selected, because the
    default for a tier that may carry secrets must be empty rather than everything. That asymmetry
    is deliberate: an accidental `raw` export of the whole corpus is the failure mode this tier
    most needs to be structurally incapable of.
    """

    if not include:
        return []
    selected: list[Path] = []
    for run_dir in run_dirs:
        base = Path(run_dir)
        if not base.is_dir():
            continue
        for candidate in sorted(base.rglob("*")):
            if not candidate.is_file():
                continue
            rel = str(candidate.relative_to(base))
            if any(token in rel for token in include):
                selected.append(candidate)
    return selected


def preview_raw_selection(
    files: Sequence[Path | str], *, tier: str = RAW_TIER, base: Path | str | None = None
) -> ExportPreview:
    """Summarize a selection by category with counts and bytes, BEFORE writing anything."""

    _tier_rank(tier)
    categories: dict[str, dict[str, int]] = {}
    total = 0
    names: list[str] = []
    for raw in files:
        path = Path(raw)
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        total += size
        shown = str(path.relative_to(base)) if base else str(path)
        names.append(shown)
        bucket = _categorize(shown)
        slot = categories.setdefault(bucket, {"count": 0, "bytes": 0})
        slot["count"] += 1
        slot["bytes"] += size
    warnings: tuple[str, ...] = ()
    if tier == RAW_TIER and names:
        warnings = (
            "RAW TIER: these files are ORIGINAL run artifacts and may contain prompts, "
            "conversations, code, commands, paths and secrets. Nothing here is redacted.",
        )
    return ExportPreview(
        tier=tier,
        file_count=len(names),
        total_bytes=total,
        categories=categories,
        files=tuple(names),
        warnings=warnings,
    )


def _categorize(rel: str) -> str:
    lowered = rel.lower()
    for label, token in _RAW_CATEGORIES:
        if token in lowered:
            return label
    return "other"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(root: Path | str) -> list[ExportManifestEntry]:
    """A deterministic, checksummed manifest of everything under `root`."""

    base = Path(root)
    entries: list[ExportManifestEntry] = []
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        rel = str(path.relative_to(base))
        if rel == "manifest.json":
            continue
        entries.append(
            ExportManifestEntry(
                path=rel, size_bytes=path.stat().st_size, sha256=_sha256_file(path)
            )
        )
    return entries


def write_bundle(
    dest: Path | str,
    *,
    tier: str = DEFAULT_TIER,
    payload: Mapping[str, Any] | None = None,
    raw_files: Sequence[Path | str] = (),
    raw_base: Path | str | None = None,
    sanitizer_report: Mapping[str, Any] | None = None,
) -> ExportBundle:
    """Write a bundle directory and its manifest. Never writes a safety or anonymity label."""

    rank = _tier_rank(tier)
    root = Path(dest)
    root.mkdir(parents=True, exist_ok=True)

    if payload is not None:
        (root / "payload.json").write_text(
            json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if sanitizer_report is not None:
        (root / "sanitizer-report.json").write_text(
            json.dumps(dict(sanitizer_report), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if rank == _TIER_RANK[RAW_TIER]:
        data_dir = root / "raw"
        data_dir.mkdir(parents=True, exist_ok=True)
        for raw in raw_files:
            src = Path(raw)
            rel = Path(str(src.relative_to(raw_base))) if raw_base else Path(src.name)
            target = data_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(src.read_bytes())

    (root / "README.txt").write_text(_bundle_readme(tier), encoding="utf-8")

    entries = build_manifest(root)
    manifest = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "tier": tier,
        "generated_at": _utc_now(),
        "claims_anonymity": False,
        "residual_risk": list(residual_risk_notes(tier)),
        "files": [e.to_dict() for e in entries],
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return ExportBundle(
        tier=tier,
        root=root,
        manifest_path=manifest_path,
        entries=tuple(entries),
    )


def _bundle_readme(tier: str) -> str:
    lines = [
        f"Analytics export bundle, tier: {tier}",
        "",
        "This bundle is MINIMIZED, not anonymous. No anonymization is claimed.",
        "",
        "Residual risks:",
    ]
    lines.extend(f"  - {note}" for note in residual_risk_notes(tier))
    return "\n".join(lines) + "\n"


# --- E-05: archives, on a 3.9 floor -------------------------------------------------------------

_UNSAFE_NAME_RE = re.compile(r"(^/)|(^[A-Za-z]:)|(^\\\\)")


def tarfile_data_filter_available() -> bool:
    """FEATURE-DETECT PEP 706's extraction filter. Do not assume it exists.

    ``requires-python`` is ``>=3.9`` and CI tests 3.9. The filters landed in 3.12 and were
    backported only to 3.9.17+, so on a 3.9.0-3.9.16 interpreter ``tarfile.data_filter`` is ABSENT
    and ``extractall`` is unsafe by default. Writing ``filter="data"`` and trusting it there would
    raise on the very interpreters the package promises to support.
    """

    return hasattr(tarfile, "data_filter")


def archive_member_refusal(
    name: str,
    *,
    is_symlink: bool = False,
    is_hardlink: bool = False,
    is_device: bool = False,
    seen: Iterable[str] = (),
) -> str | None:
    """The single member policy, returning a reason to REFUSE or None to allow.

    One predicate, shared by the tar and zip paths, because two copies of a traversal check are two
    chances to fix only one of them. Every check runs BEFORE any byte is written, so a hostile
    archive is refused whole rather than partially extracted.
    """

    if not name or name.strip() == "":
        return "empty member name"
    if _UNSAFE_NAME_RE.search(name):
        return f"absolute member path {name!r}"
    normalized = name.replace("\\", "/")
    parts = [p for p in normalized.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        return f"path traversal in member {name!r}"
    if normalized in set(seen):
        return f"duplicate member name {name!r}"
    if is_symlink:
        return f"symlink member {name!r}"
    if is_hardlink:
        return f"hardlink member {name!r}"
    if is_device:
        return f"device or special-file member {name!r}"
    return None


def safe_extract(archive: Path | str, dest: Path | str) -> list[str]:
    """Validate EVERY member, then extract. Refuses before writing anything.

    Two passes on purpose. The first pass reads the whole member list and refuses on the first
    hostile entry, so a refusal leaves the destination untouched; a single-pass loop that validated
    and extracted together would leave a partial tree behind on refusal, which is exactly the state
    a caller cannot safely clean up.
    """

    src = Path(archive)
    out = Path(dest)
    names: list[str] = []

    if zipfile.is_zipfile(src):
        with zipfile.ZipFile(src) as zf:
            for info in zf.infolist():
                # The Unix mode lives in the high 16 bits of external_attr; S_IFLNK is 0o120000.
                mode = info.external_attr >> 16
                is_link = bool(mode & 0o170000 == 0o120000)
                reason = archive_member_refusal(
                    info.filename, is_symlink=is_link, seen=names
                )
                if reason:
                    raise ExportRefusal(f"refusing archive {src.name}: {reason}")
                if not info.filename.endswith("/"):
                    names.append(info.filename.replace("\\", "/"))
            out.mkdir(parents=True, exist_ok=True)
            for name in names:
                target = out / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(name) as reader, target.open("wb") as writer:
                    writer.write(reader.read())
        return names

    with tarfile.open(src) as tf:
        members = tf.getmembers()
        for member in members:
            reason = archive_member_refusal(
                member.name,
                is_symlink=member.issym(),
                is_hardlink=member.islnk(),
                is_device=member.ischr() or member.isblk() or member.isfifo(),
                seen=names,
            )
            if reason:
                raise ExportRefusal(f"refusing archive {src.name}: {reason}")
            if member.isfile():
                names.append(member.name.replace("\\", "/"))
        out.mkdir(parents=True, exist_ok=True)
        # Members are validated; extract by hand rather than via `extractall`, so behavior is
        # IDENTICAL on an interpreter with and without `tarfile.data_filter`. The feature detection
        # is still reported (callers and tests assert on it), but no branch depends on it.
        for member in members:
            if not member.isfile():
                continue
            extracted = tf.extractfile(member)
            if extracted is None:
                continue
            target = out / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("wb") as writer:
                writer.write(extracted.read())
    return names
