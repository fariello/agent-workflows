#!/usr/bin/env python3
"""The validated telemetry configuration model, and the ONE place its bounds are enforced.

WHY THIS IS NOT IN ``config.py``, WHICH IS THE OBVIOUS AND WRONG ANSWER. "Integrate with the
existing config authority" reads as "register a key in :mod:`agent_workflows.config`", and doing
that would silently DISCARD this setting. That module persists an ALLOWLIST of top-level keys
(``_ALLOWED_TOP_KEYS``) and its ``normalize()`` REBUILDS its output from ``default_config()``, so
an unregistered key does not survive a save: it is dropped on the next write, with no error and no
warning. The shipped precedent for a setting that must not go there is ``review_findings_gate``,
whose own comment in ``config.py`` states it is recorded in ``.aw/config/project.json`` and read
there "and not via the XDG user config (which drops unknown keys)", and which round-trips safely
because :func:`agent_workflows.project_schema.parse_portable_policy` preserves unknown keys in
``unknown_fields`` and re-serializes them. This module follows that precedent.

ONE DIVERGENCE FROM THAT PRECEDENT IS DELIBERATE, AND IT IS THE DEFAULT DIRECTION.
``review_findings_gate`` is fail-CLOSED: an absent key means the gate is ACTIVE, because it is a
safety gate and the safe answer to "unset" is "protect anyway". Telemetry is the opposite kind of
thing. Failing closed on a missing telemetry setting would break a run to protect nothing, so an
absent, malformed, or out-of-vocabulary value here lands on the DOCUMENTED DEFAULT and never
raises. Every reader in this module is total: it returns a valid :class:`TelemetryConfig` for any
input, including an unreadable file, a JSON syntax error, a wrong type, and a hostile value.

WHERE EACH SETTING LIVES, AND WHY THE SPLIT IS BY NATURE OF THE SETTING (plan OQ-01).

* ``.aw/config/project.json`` is COMMITTED, so it carries the PROJECT POLICY: whether telemetry is
  enabled, whether periodic sampling is on, and the sampling interval. Those are decisions a team
  shares and reviews, and a teammate cloning the repo should inherit them.
* ``.aw/config/local.json`` is GITIGNORED, so it carries the PER-MACHINE DEVIATION: an operator on
  a constrained or shared box declining sampling. Its existing ``runtime_overrides`` map is exactly
  the shape for this, and nothing written there can reach git history.
* PRECEDENCE IS LOCAL OVERRIDES PROJECT, in the narrow direction that matters: a machine may turn
  something OFF or lengthen an interval it cannot afford, which is a refusal to spend local
  resources. It is deliberately allowed to turn sampling on too, since the interval bound below
  makes that harmless, but the intended use is the restrictive one.

THE INTERVAL BOUND IS ENFORCED IN EXACTLY ONE PLACE, :func:`clamp_interval`, called by the parser
so no other code path can construct an out-of-bound config. A second bound check elsewhere would be
a second authority, and the two would eventually disagree.

Stdlib only.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = [
    "DEFAULT_ENABLED",
    "DEFAULT_SAMPLE_INTERVAL_SECONDS",
    "DEFAULT_SAMPLING_ENABLED",
    "LOCAL_BINDING_REL",
    "MAX_ACCELERATOR_OUTPUT_BYTES",
    "MAX_PROBE_SECONDS",
    "MAX_SAMPLE_INTERVAL_SECONDS",
    "MIN_SAMPLE_INTERVAL_SECONDS",
    "PROJECT_POLICY_REL",
    "TELEMETRY_KEY",
    "TelemetryConfig",
    "clamp_interval",
    "parse_telemetry_settings",
    "read_local_settings",
    "read_project_settings",
    "read_telemetry_config",
]

#: The single key both files use. Deliberately NOT registered in ``config.py``'s ``CONFIG_SCHEMA``,
#: exactly as ``review_findings_gate`` is deliberately absent from it.
TELEMETRY_KEY = "run_analytics_telemetry"

#: The committed, portable project policy (shared) and the gitignored machine binding (private).
PROJECT_POLICY_REL = ("config", "project.json")
LOCAL_BINDING_REL = ("config", "local.json")

#: BASIC start/end telemetry is ON by default: it is two events per execution, it is what makes a
#: duration interpretable at all, and it costs no measurable time. PERIODIC SAMPLING is OFF by
#: default because it is unbounded in count and the plan's required decision says to ask
#: separately before enabling it.
DEFAULT_ENABLED = True
DEFAULT_SAMPLING_ENABLED = False
DEFAULT_SAMPLE_INTERVAL_SECONDS = 15.0

#: The bound. The floor exists because :func:`agent_workflows.runner_shared.append_jsonl` fsyncs
#: EVERY event, so a sub-second interval would turn a telemetry sampler into a synchronous-IO
#: generator competing with the run it is measuring. The ceiling exists so a nominally-enabled
#: sampler cannot be configured into silence.
MIN_SAMPLE_INTERVAL_SECONDS = 1.0
MAX_SAMPLE_INTERVAL_SECONDS = 3600.0

#: The per-probe wall-clock budget and the accelerator output cap, both consumed by the probe
#: layer. They live HERE, with the rest of the configuration, so the probe module has exactly one
#: source for its bounds.
MAX_PROBE_SECONDS = 2.0
MAX_ACCELERATOR_OUTPUT_BYTES = 64 * 1024


@dataclass(frozen=True)
class TelemetryConfig:
    """The effective, already-validated telemetry settings.

    Frozen and total: every instance is in-bounds because :func:`parse_telemetry_settings` is the
    only producer and it clamps. ``sources`` records which files actually contributed, so a
    diagnostic can say WHERE a setting came from without re-reading anything.
    """

    enabled: bool = DEFAULT_ENABLED
    sampling_enabled: bool = DEFAULT_SAMPLING_ENABLED
    sample_interval_seconds: float = DEFAULT_SAMPLE_INTERVAL_SECONDS
    max_probe_seconds: float = MAX_PROBE_SECONDS
    sources: tuple[str, ...] = ()

    @property
    def samples_enabled(self) -> bool:
        """Will a sampler actually run? Sampling requires telemetry itself to be enabled.

        Kept as a derived property rather than a stored flag so "telemetry off" can never be
        contradicted by "sampling on": disabling telemetry disables sampling by construction.
        """

        return self.enabled and self.sampling_enabled

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "sampling_enabled": self.sampling_enabled,
            "sample_interval_seconds": self.sample_interval_seconds,
            "max_probe_seconds": self.max_probe_seconds,
            "sources": list(self.sources),
        }


def clamp_interval(value: Any) -> float:
    """THE one place the sampling-interval bound is enforced. Never raises.

    A non-numeric, boolean, non-finite, or absent value yields the documented default rather than
    an error, because an unparseable telemetry setting must not break a run. A numeric value
    outside the bound is CLAMPED rather than rejected, so an operator who asks for an interval of
    ``0.01`` gets the floor instead of a failure.
    """

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return DEFAULT_SAMPLE_INTERVAL_SECONDS
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        return DEFAULT_SAMPLE_INTERVAL_SECONDS
    return max(MIN_SAMPLE_INTERVAL_SECONDS, min(MAX_SAMPLE_INTERVAL_SECONDS, number))


def _coerce_bool(value: Any, default: bool) -> bool:
    """Read a boolean tolerantly, landing on ``default`` for anything out of vocabulary.

    Accepts a real bool, the usual string spellings, and ``0``/``1``. Anything else (a list, a
    dict, ``"maybe"``) is out of vocabulary and yields the default WITHOUT raising, which is the
    whole contract of this module.
    """

    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in ("true", "yes", "on", "1", "enabled"):
            return True
        if token in ("false", "no", "off", "0", "disabled"):
            return False
    return default


def _telemetry_section(payload: Any) -> dict[str, Any]:
    """Extract the telemetry object from one parsed config file, tolerating every wrong shape.

    Looks in the top level first (the ``review_findings_gate`` shape) and then inside
    ``runtime_overrides``, which is where a machine-local deviation belongs in ``local.json``.
    """

    if not isinstance(payload, Mapping):
        return {}
    found: dict[str, Any] = {}
    overrides = payload.get("runtime_overrides")
    if isinstance(overrides, Mapping):
        nested = overrides.get(TELEMETRY_KEY)
        if isinstance(nested, Mapping):
            found.update({str(k): v for k, v in nested.items()})
    direct = payload.get(TELEMETRY_KEY)
    if isinstance(direct, Mapping):
        # A top-level object wins over a `runtime_overrides` one WITHIN the same file, because it
        # is the more explicit placement in that file.
        found.update({str(k): v for k, v in direct.items()})
    return found


def _read_json_object(path: Path) -> dict[str, Any]:
    """Read one JSON object, or ``{}`` for anything unreadable. Never raises."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return _telemetry_section(payload)


def read_project_settings(repo_root: Path | str) -> dict[str, Any]:
    """The telemetry object from the COMMITTED project policy, or ``{}``."""

    return _read_json_object(Path(repo_root).joinpath(".aw", *PROJECT_POLICY_REL))


def read_local_settings(repo_root: Path | str) -> dict[str, Any]:
    """The telemetry object from the GITIGNORED machine binding, or ``{}``."""

    return _read_json_object(Path(repo_root).joinpath(".aw", *LOCAL_BINDING_REL))


def parse_telemetry_settings(
    project: Mapping[str, Any] | None = None,
    local: Mapping[str, Any] | None = None,
) -> TelemetryConfig:
    """Merge project policy with the machine-local override and validate. Never raises.

    The ONLY producer of a :class:`TelemetryConfig`, which is what makes the clamp in
    :func:`clamp_interval` the single enforcement point: there is no other way to build one.
    """

    merged: dict[str, Any] = {}
    sources: list[str] = []
    if project:
        merged.update({str(k): v for k, v in project.items()})
        sources.append("project")
    if local:
        merged.update({str(k): v for k, v in local.items()})
        sources.append("local")

    enabled = _coerce_bool(merged.get("enabled"), DEFAULT_ENABLED)
    sampling = _coerce_bool(merged.get("sampling_enabled"), DEFAULT_SAMPLING_ENABLED)
    interval = (
        clamp_interval(merged["sample_interval_seconds"])
        if "sample_interval_seconds" in merged
        else DEFAULT_SAMPLE_INTERVAL_SECONDS
    )
    probe_budget = merged.get("max_probe_seconds")
    if isinstance(probe_budget, bool) or not isinstance(probe_budget, (int, float)):
        probe_seconds = MAX_PROBE_SECONDS
    else:
        candidate = float(probe_budget)
        if candidate != candidate or candidate <= 0 or candidate == float("inf"):
            probe_seconds = MAX_PROBE_SECONDS
        else:
            probe_seconds = min(candidate, MAX_PROBE_SECONDS)

    return TelemetryConfig(
        enabled=enabled,
        sampling_enabled=sampling,
        sample_interval_seconds=interval,
        max_probe_seconds=probe_seconds,
        sources=tuple(sources),
    )


def read_telemetry_config(repo_root: Path | str | None = None) -> TelemetryConfig:
    """The effective configuration for ``repo_root``, reading both files. Never raises.

    A repository with neither file (or with no telemetry key in either) yields the documented
    defaults with an empty ``sources``, which is how a caller can tell "configured to the default"
    from "not configured".
    """

    base = Path(repo_root) if repo_root is not None else Path.cwd()
    return parse_telemetry_settings(
        project=read_project_settings(base), local=read_local_settings(base)
    )
