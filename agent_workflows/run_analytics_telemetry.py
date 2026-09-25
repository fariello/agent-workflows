#!/usr/bin/env python3
"""Cross-host resource telemetry: the event schema, the safe probes, and the bounded collector.

WHAT THIS ANSWERS. A duration is uninterpretable without the machine that produced it. The same
plan on a 4-core laptop under load and a 64-core node at idle produces two wall times that mean
completely different things, and a RESUMED run may execute its attempts on DIFFERENT nodes. So
telemetry here is per INVOCATION, never a one-time installation inventory: each execution records
what hardware and what load were actually present while it ran.

THE SCHEMA IS AN ALLOWLIST, AND THAT DIRECTION IS THE WHOLE DESIGN. A field is persisted because
it appears in :data:`ALLOWED_FIELDS` (or an explicitly named nested allowlist), and for NO other
reason. This is stated first because the plan governing this module enumerates a forbidden set
(arbitrary environment values, raw stdout/stderr, file contents, network addresses, absolute paths,
raw hostname) and that list is a TEST CORPUS, never the implementation strategy. A denylist passes
every test written from itself and then leaks on the first field nobody imagined; an enumerated
forbidden set can never be proven complete, while an allowlist can. :func:`validate_event` REFUSES
an unknown key rather than dropping it, for the same reason
:func:`agent_workflows.run_analytics_privacy.project_facts` does: "refused" is a boundary a test
can prove, "dropped" is one it cannot, and a silent drop lets a caller believe its record was
persisted whole. The sibling privacy projector carries the identical requirement, so the two agree.

THE PROBES ARE READ-ONLY, BOUNDED, AND NEVER FATAL. Every probe returns a value or a structured
``unavailable`` / ``timeout`` / ``parse_error`` code; none raises, and none can make a run fail.
Runner reliability must not depend on an optional probe, so a probe layer that could raise would be
a defect even if every probe worked today. Probes are reached through
:class:`ResourceProbeAdapter`, an injectable interface, so tests never touch a real device.

REUSE DECISION, RECORDED HERE BECAUSE IT WAS AN OPEN QUESTION (plan OQ-02). This repository already
ships an 860-line, stdlib-only, read-only implementation of very nearly this probe set:
``.aw/system/workflows/benchmark/tools/bench_env.py`` (CPU model/cores/flags, RAM breakdown, swap,
load, GPU, container/VM hints, filesystem), whose ``_run`` bounds every informational command with
a timeout and swallows failures to ``""``, whose ``_read`` does the same for ``/proc`` and ``/sys``,
and whose docstring states the posture this module needs ("NEVER fabricates a value it could not
read"). THE CHOICE MADE HERE IS: WRITE FRESH, MODELED ON IT, WITH ATTRIBUTION, AND IMPORT NOTHING.
The reason is placement, not quality. That file lives under ``.aw/system/workflows/``, which is
INSTALLED WORKFLOW CONTENT copied into target repositories by the installer, not an importable
package module; a runtime import from ``agent_workflows/`` would couple the shipped package to a
file the installer manages and would break in any target repo that has not installed the benchmark
workflow. Extracting it into the package was rejected as out of this plan's declared
``Scope-Paths``. What this module deliberately borrows is its SHAPE: the bounded-subprocess helper
with ``capture_output``/``timeout``/``check=False``, the total ``/proc`` reader, and the rule that
an unread value is reported as unavailable rather than fabricated. What it deliberately does NOT
do is emit ``""`` for a failure the way ``_run`` does, because an empty string is
indistinguishable from a successful empty read; this module returns a typed
:class:`ProbeOutcome` carrying an explicit reason code instead.

THE SAMPLER COPIES A SHIPPED PATTERN AND OWNS NO PROCESS POLICY. :class:`ResourceSampler` uses the
same structure as ``oc_runipd.StallWatchdog`` and ``lane_containment.TurnBoundWatch``: a
``threading.Event`` stop flag, a ``daemon=True`` thread started in ``__enter__``, a
``_stop.wait(interval)`` loop rather than ``sleep`` (so a stop is observed immediately instead of
after the interval elapses), and ``__exit__`` setting the event then joining with a timeout. It
registers NO signal handler, adds NO cleanup path, and does NOT call
``runner_shutdown.clean_shutdown``. That is not stylistic reticence: spec ``c4gd2h`` R5 requires ONE
cleanup implementation shared by all levels and prohibits divergent per-level cleanup, with A9
demanding a structural check that exactly one exists, and ``oc_runipd`` records a prior plan being
refused permission to register ``signal.signal`` handlers because the ``runstop`` phase owns
SIGINT/SIGTERM and the two designs were incompatible. This module therefore exposes a small
callable stop API, and the runner integration that wires it in is another plan's to write.

WHAT A PASSING IMPLEMENTATION MAY NOT CLAIM. The node identifier here is PSEUDONYMOUS, not
anonymous, and the correlation scope is stated in :func:`node_pseudonym`. Do not document this as
anonymous telemetry, and specifically do not rest a privacy claim on
``aw sanitize``: measured, this repository's leak detector returns ZERO findings at default
settings for a bare hostname (the hostname is derived as a WARN-tier token and is promoted to
``fail`` only when the allowlist sets ``hostname_fail = true``, which ships false), while a username
or a home path both fail immediately. The sanitizer is a corroborating oracle; the load-bearing
check is the direct assertion that the raw hostname does not appear in the output.

Stdlib only.
"""

from __future__ import annotations

import hashlib
import os
import platform
import re
import shutil
import socket
import subprocess
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from agent_workflows.run_analytics_config import (
    MAX_ACCELERATOR_OUTPUT_BYTES,
    MAX_PROBE_SECONDS,
    TelemetryConfig,
)

__all__ = [
    "ALLOWED_ACCELERATOR_FIELDS",
    "ALLOWED_FIELDS",
    "ALLOWED_RESOURCE_FIELDS",
    "EVENT_KINDS",
    "PROBE_REASONS",
    "REQUIRED_FIELDS",
    "TELEMETRY_FILENAME",
    "TELEMETRY_SCHEMA_VERSION",
    "FakeResourceProbeAdapter",
    "ProbeOutcome",
    "ResourceProbeAdapter",
    "ResourceSampler",
    "SchemaRefusal",
    "SystemResourceProbeAdapter",
    "TelemetryCollector",
    "build_event",
    "node_identity_input",
    "node_pseudonym",
    "validate_event",
]

#: The event schema's own version. A reader REFUSES a version it does not know rather than
#: misparsing it. Bump when a field's meaning changes; downstream orders treat this envelope as a
#: CONTRACT (one plan wires it into both runners, one ingests it, one covers it end to end), so a
#: change here is a change to three other plans' input.
TELEMETRY_SCHEMA_VERSION = 1

#: The JSONL stream's filename inside a run directory. One stream per run, one line per event.
TELEMETRY_FILENAME = "telemetry.jsonl"

#: The CLOSED event vocabulary. ``start`` and ``end`` bracket one execution; ``sample`` is an
#: optional periodic observation between them.
EVENT_KINDS: frozenset[str] = frozenset({"start", "sample", "end"})

#: EVERY key an event may carry, and nothing else. Read this as the privacy boundary it is: adding
#: a name here widens what is persisted, so it belongs with a test proving the new field cannot
#: carry a path, a transcript, a network address, or host identity.
ALLOWED_FIELDS: frozenset[str] = frozenset(
    {
        # --- envelope ---
        "schema_version",
        "event_kind",
        "sequence",
        # --- correlation identifiers (opaque, repo-internal, or pseudonymous) ---
        "execution_id",
        "run_id",
        "ipd_id6",
        "set_id",
        "position",
        "attempt",
        "phase",
        "host",
        "provider",
        "model",
        "model_variant",
        "node_id",
        # --- time ---
        "wall_timestamp",
        "monotonic_offset_seconds",
        "duration_seconds",
        # --- observation payloads (each an object with its OWN nested allowlist) ---
        "resources",
        "accelerators",
        # --- diagnostics: CODES and COUNTS, never text ---
        "warnings",
        "sample_skipped_count",
        "probe_error_count",
        "tool_versions",
    }
)

#: Fields every event must carry. A missing one is a refusal, so a consumer never has to guess
#: whether an absent field means "not observed" or "producer forgot".
REQUIRED_FIELDS: tuple[str, ...] = (
    "schema_version",
    "event_kind",
    "execution_id",
    "wall_timestamp",
    "monotonic_offset_seconds",
)

#: The nested allowlist for ``resources``. Every entry is numeric or a closed-vocabulary label.
#: Note what is ABSENT and why: no hostname, no absolute path, no mount point, no device name, no
#: network address, no environment value, no process command line.
ALLOWED_RESOURCE_FIELDS: frozenset[str] = frozenset(
    {
        "cpu_logical_count",
        "cpu_usable_count",
        "cpu_architecture",
        "platform_system",
        "platform_release_major",
        "load_average_1m",
        "load_average_5m",
        "load_average_15m",
        "memory_total_bytes",
        "memory_available_bytes",
        "swap_total_bytes",
        "swap_free_bytes",
        "process_rss_bytes",
        "process_cpu_seconds",
        "disk_total_bytes",
        "disk_free_bytes",
        "container_hint",
        "unavailable",
    }
)

#: The nested allowlist for one accelerator record. ``vendor``/``name``/``driver_version`` are
#: categorical; the rest are numeric. No serial number, no UUID, no raw tool output.
ALLOWED_ACCELERATOR_FIELDS: frozenset[str] = frozenset(
    {
        "vendor",
        "name",
        "driver_version",
        "memory_total_mib",
        "memory_used_mib",
        "utilization_percent",
    }
)

#: Every structured failure code a probe may report. A consumer can switch on these exhaustively,
#: and a probe may report NOTHING else: a code is a fixed token, never a formatted message, because
#: a formatted message is the natural place a path or a hostname rides in.
PROBE_REASONS: frozenset[str] = frozenset(
    {
        "ok",
        "unavailable",
        "timeout",
        "parse_error",
        "permission_denied",
        "not_supported",
    }
)

#: A categorical label: letters, digits, and a few separators. No space, quote, path separator, or
#: shell metacharacter, which is what keeps a command line or an absolute path out of a label.
_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+@-]{0,127}$")
#: A model identifier legitimately carries ``/`` (``provider/model``), so it gets its own pattern.
_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+@/-]{0,191}$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_PSEUDONYM_RE = re.compile(r"^node:[0-9a-f]{16}$")

#: Keys whose vocabulary is genuinely CLOSED: the permitted values are enumerated here, and any
#: other value is refused.
#:
#: WHY THESE ARE ENUMERATED RATHER THAN PATTERN-CHECKED, and it is the difference between a real
#: allowlist and one in name only. A "short label" pattern accepts ``10.0.0.5:8443``, accepts a
#: session id, and accepts a hostname, because all three ARE short labels. Calling such a field a
#: closed vocabulary while validating it with a character class is a DENYLIST wearing an
#: allowlist's name: it refuses the characters somebody thought of and passes every forbidden value
#: that happens to be spelled conservatively. So a field whose values this package chooses gets its
#: values LISTED. Extending one of these sets is a deliberate act; a producer emitting an
#: unenumerated value gets a refusal naming the field, which is the correct outcome.
_CLOSED_VOCABULARIES: dict[str, frozenset[str]] = {
    "event_kind": frozenset(EVENT_KINDS),
    #: The driver hosts this package supports. Kept in step with the project policy's
    #: ``enabled_hosts`` vocabulary; a new host is a deliberate addition here.
    "host": frozenset({"opencode", "claude", "antigravity", "agy", "unknown"}),
    #: The run phase a measurement belongs to. Coarse by design: a finer-grained phase name would
    #: drift with the runners' internals and become free text in practice.
    "phase": frozenset(
        {
            "queue",
            "begin",
            "execute",
            "validate",
            "finalize",
            "integrate",
            "shutdown",
            "unknown",
        }
    ),
}

#: Keys whose value is an OPAQUE IDENTIFIER this package or its host mints, so their vocabulary
#: cannot be enumerated, but whose SHAPE is pinned to a specific pattern rather than to a general
#: "looks like a label" test. Each pattern is deliberately narrow enough that a path, a network
#: address, a session id, or a hostname fails it.
_SHAPED_ID_KEYS: dict[str, re.Pattern[str]] = {
    #: A driver run id, exactly as the runners mint it: ``run-<UTC stamp>-<pid>``.
    "run_id": re.compile(r"^run-\d{8}T\d{6}Z-\d+$"),
    #: This package's stable 6-character artifact handle.
    "ipd_id6": re.compile(r"^[a-z0-9]{6}$"),
    #: A Set id: lowercase alphanumeric, no separator, as `aw ipd scaffold` derives it.
    "set_id": re.compile(r"^[a-z0-9]{2,32}$"),
    #: One execution's correlation id. Minted by the caller, so it is the loosest of these, but
    #: still refuses a dot (hence a hostname or an IPv4 address), a slash, and a colon.
    "execution_id": re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"),
    #: A provider name, which is a single vendor token.
    "provider": re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$"),
    #: A model variant/tier label.
    "model_variant": re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"),
}
_NON_NEGATIVE_INT_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "sequence",
        "position",
        "attempt",
        "sample_skipped_count",
        "probe_error_count",
    }
)
_NUMBER_KEYS: frozenset[str] = frozenset(
    {"monotonic_offset_seconds", "duration_seconds"}
)

#: The EXECUTABLE allowlist for the accelerator probe. Strict, because this is the only probe that
#: shells out to a vendor tool, and it is the one most likely to hang, flood, or leak.
_ACCELERATOR_EXECUTABLES: tuple[str, ...] = ("nvidia-smi", "rocm-smi")


class SchemaRefusal(ValueError):
    """An event carried an unknown key, a missing required key, or an out-of-vocabulary value.

    Deliberately a refusal rather than a silent drop, matching
    :class:`agent_workflows.run_analytics_privacy.PrivacyRefusal`: a dropped key lets a producer
    believe its record was persisted whole, and the difference between refused and dropped is the
    difference between a boundary a test can prove and one it cannot.
    """

    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        self.reason = reason
        super().__init__(f"telemetry schema refusal: {key!r} {reason}")


# --- Probe results -----------------------------------------------------------------------------
@dataclass(frozen=True)
class ProbeOutcome:
    """One probe's result: a value, or a REASON it has none. Never an exception, never raw text.

    ``detail_bytes`` exists so a ``parse_error`` can be diagnosed by SIZE without persisting the
    offending bytes. That is the whole point: a vendor tool's output can carry a hostname, a path,
    or a serial number, and the privacy argument of this module collapses if a parse failure is
    recorded by storing the text that failed to parse.
    """

    reason: str
    value: Any = None
    detail_bytes: int = 0

    @property
    def ok(self) -> bool:
        return self.reason == "ok"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"reason": self.reason}
        if self.detail_bytes:
            payload["detail_bytes"] = self.detail_bytes
        return payload


# --- Schema ------------------------------------------------------------------------------------
def _refuse_unknown(
    payload: Mapping[str, Any], allowed: frozenset[str], where: str
) -> None:
    unknown = sorted(set(map(str, payload.keys())) - allowed)
    if unknown:
        raise SchemaRefusal(
            unknown[0],
            f"is not in the {where} allowlist, so it is REFUSED rather than dropped "
            f"(the boundary is an allowlist: add the key deliberately, with a test)",
        )


def _validate_scalar(key: str, value: Any) -> Any:
    if key in _NON_NEGATIVE_INT_KEYS:
        if isinstance(value, bool) or not isinstance(value, int):
            raise SchemaRefusal(key, "must be an integer")
        if value < 0:
            raise SchemaRefusal(key, "must not be negative")
        return value
    if key in _NUMBER_KEYS:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SchemaRefusal(key, "must be a number")
        number = float(value)
        if number != number or number in (float("inf"), float("-inf")):
            raise SchemaRefusal(key, "must be a finite number")
        if number < 0:
            raise SchemaRefusal(
                key, "must not be negative (a monotonic clock cannot go backwards)"
            )
        return value
    if key == "wall_timestamp":
        if not isinstance(value, str) or not _TIMESTAMP_RE.match(value):
            raise SchemaRefusal(key, "must be an ISO-8601 UTC timestamp ending in Z")
        return value
    if key == "node_id":
        if not isinstance(value, str) or not _PSEUDONYM_RE.match(value):
            raise SchemaRefusal(
                key,
                "must be a pseudonym from node_pseudonym(); a raw host identity is REFUSED",
            )
        return value
    if key == "model":
        # The ONE field whose value comes from outside this package and cannot be enumerated (a
        # provider ships a new model name whenever it likes). So it is pattern-pinned to
        # `provider/model` shape: no space, no quote, no backslash, and the leading character class
        # refuses an absolute path.
        if not isinstance(value, str) or not _MODEL_RE.match(value):
            raise SchemaRefusal(key, "must be a short provider/model identifier")
        if _looks_like_path(value):
            raise SchemaRefusal(
                key, "looks like a filesystem path, which no label may carry"
            )
        return value
    vocabulary = _CLOSED_VOCABULARIES.get(key)
    if vocabulary is not None:
        if not isinstance(value, str) or value not in vocabulary:
            raise SchemaRefusal(
                key,
                f"must be one of {sorted(vocabulary)}; the vocabulary is CLOSED and "
                f"enumerated, because a character-class check would admit a hostname, "
                f"a network address, or a session id (all of which are short labels)",
            )
        return value
    pattern = _SHAPED_ID_KEYS.get(key)
    if pattern is not None:
        if not isinstance(value, str) or not pattern.match(value):
            raise SchemaRefusal(
                key,
                f"does not match this identifier's required shape ({pattern.pattern}); "
                f"a value that is merely 'a short label' is REFUSED here",
            )
        return value
    raise SchemaRefusal(key, "has no validation rule, which is itself a refusal")


def _looks_like_path(text: str) -> bool:
    """Conservative structural test for a filesystem path, used to refuse one in a label field.

    Mirrors :func:`agent_workflows.run_analytics_privacy._looks_like_path`, deliberately: the two
    modules are the write-side boundary for two different record kinds and they should agree about
    what a path looks like.
    """

    if text.startswith(("/", "~", "\\\\")) or ".." in text:
        return True
    return bool(re.match(r"^[A-Za-z]:[\\/]", text))


def _validate_label_list(key: str, value: Any) -> list[str]:
    """Validate a list of CODES. Free text is refused, which is why warnings are codes.

    ``warnings`` is the field most likely to smuggle content, because the natural implementation
    formats an exception message into it and an exception message routinely contains a path.
    """

    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise SchemaRefusal(key, "must be a list of short codes")
    codes: list[str] = []
    for entry in value:
        if not isinstance(entry, str):
            raise SchemaRefusal(key, f"contains a {type(entry).__name__}, not a code")
        if not _LABEL_RE.match(entry):
            raise SchemaRefusal(
                key, "contains free text; only short codes are permitted here"
            )
        codes.append(entry)
    return codes


#: The nested observation fields that may hold a STRING at all, each with the exact vocabulary or
#: pattern permitted. EVERY OTHER nested field must be numeric.
#:
#: WHY THIS TABLE EXISTS, and it closed a real hole found by this plan's own test corpus. The
#: nested validator used to accept ANY string matching the general "short label" character class,
#: which meant ``resources.container_hint`` accepted a hostname (``some-host``), an IPv4 address
#: with a port (``10.0.0.5:8443``), and a session id (``ses_<hex>``), because each of those IS a
#: short label. Three of the six categories this module exists to keep out therefore had a way in,
#: through a field whose name sounds harmless. A per-field vocabulary is the fix: a string field is
#: valid because its value is enumerated (or matches a purpose-built pattern), never because it is
#: merely conservatively spelled.
_NESTED_STRING_RULES: dict[str, frozenset[str] | re.Pattern[str]] = {
    #: A containerization hint: exactly the tokens the probe can emit.
    "container_hint": frozenset(
        {"docker", "containerd", "podman", "lxc", "kubepods", "none"}
    ),
    #: A CPU architecture as ``platform.machine()`` reports it.
    "cpu_architecture": re.compile(r"^[A-Za-z0-9_]{1,32}$"),
    #: An OS family as ``platform.system()`` reports it.
    "platform_system": frozenset({"Linux", "Darwin", "Windows", "FreeBSD", "Java"}),
    #: A kernel MAJOR version only: digits. Deliberately not the full release string, which on
    #: some distributions embeds a build host or a vendor tag.
    "platform_release_major": re.compile(r"^\d{1,6}$"),
    #: The composed probe-failure summary this module builds itself, as ``name:reason`` joined by
    #: ``+``. Pinned to that exact shape so a formatted error message (and any path inside it)
    #: cannot arrive through the field that reports failures.
    "unavailable": re.compile(r"^[a-z_]+:[a-z_]+(?:\+[a-z_]+:[a-z_]+)*$"),
    #: An accelerator vendor.
    "vendor": frozenset({"nvidia", "amd", "intel", "apple", "unknown"}),
    #: A GPU model name, whose vocabulary belongs to the vendor. Narrow on purpose: no dot, no
    #: colon, and no underscore, so a hostname, an IPv4 address, and a session id all fail.
    "name": re.compile(r"^[A-Za-z0-9][A-Za-z0-9 -]{0,63}$"),
    #: A driver version: digits and dots.
    "driver_version": re.compile(r"^\d[\d.]{0,31}$"),
}


def _validate_number_map(
    key: str, value: Any, allowed: frozenset[str]
) -> dict[str, Any]:
    """Validate one nested observation object against its OWN allowlist.

    Numeric by default: a nested field may hold a string ONLY if it appears in
    :data:`_NESTED_STRING_RULES`, and then only a value that rule permits. See that table for the
    hole this closed.
    """

    if not isinstance(value, Mapping):
        raise SchemaRefusal(key, f"must be an object, got {type(value).__name__}")
    _refuse_unknown(value, allowed, key)
    validated: dict[str, Any] = {}
    for name in sorted(map(str, value.keys())):
        item = value[name]
        if item is None:
            validated[name] = None
            continue
        if isinstance(item, bool):
            raise SchemaRefusal(
                f"{key}.{name}", "must be a number or a label, not a bool"
            )
        if isinstance(item, (int, float)):
            number = float(item)
            if number != number or number in (float("inf"), float("-inf")):
                raise SchemaRefusal(f"{key}.{name}", "must be a finite number")
            validated[name] = item
            continue
        if isinstance(item, str):
            rule = _NESTED_STRING_RULES.get(name)
            if rule is None:
                raise SchemaRefusal(
                    f"{key}.{name}",
                    "is a numeric observation field, so a string value is REFUSED "
                    "(a string is permitted only where an explicit vocabulary names it)",
                )
            if isinstance(rule, frozenset):
                if item not in rule:
                    raise SchemaRefusal(
                        f"{key}.{name}",
                        f"must be one of {sorted(rule)}; the vocabulary is CLOSED, because a "
                        f"character-class check would admit a hostname, an IP address, or a "
                        f"session id",
                    )
            elif not rule.match(item):
                raise SchemaRefusal(
                    f"{key}.{name}",
                    f"does not match this field's required shape ({rule.pattern}); "
                    f"'a short label' is NOT sufficient here",
                )
            validated[name] = item
            continue
        raise SchemaRefusal(
            f"{key}.{name}",
            f"has type {type(item).__name__}, which no observation field may be",
        )
    return validated


def validate_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one event against the allowlist, returning a normalized copy or REFUSING.

    Refuses, in this order: a non-object; an unknown schema version; an out-of-vocabulary
    ``event_kind``; an unknown key; a missing required key; and any value failing its per-key rule.
    The version check runs before the key checks so a future generation gets a forward-compatible
    diagnostic instead of complaints about fields that are valid in their own schema.
    """

    if not isinstance(event, Mapping):
        raise SchemaRefusal("event", f"must be an object, got {type(event).__name__}")

    version = event.get("schema_version")
    if isinstance(version, bool) or not isinstance(version, int):
        raise SchemaRefusal("schema_version", "must be an integer")
    if version != TELEMETRY_SCHEMA_VERSION:
        raise SchemaRefusal(
            "schema_version",
            f"is {version}, which this reader does not understand "
            f"(known: {TELEMETRY_SCHEMA_VERSION}); refusing to misparse it",
        )

    kind = event.get("event_kind")
    if not isinstance(kind, str) or kind not in EVENT_KINDS:
        raise SchemaRefusal(
            "event_kind",
            f"must be one of {sorted(EVENT_KINDS)}, got {kind!r} "
            f"(the vocabulary is CLOSED)",
        )

    _refuse_unknown(event, ALLOWED_FIELDS, "event")
    missing = [name for name in REQUIRED_FIELDS if name not in event]
    if missing:
        raise SchemaRefusal(missing[0], "is required and is absent")

    validated: dict[str, Any] = {}
    for key in sorted(map(str, event.keys())):
        value = event[key]
        if key == "resources":
            validated[key] = _validate_number_map(key, value, ALLOWED_RESOURCE_FIELDS)
        elif key == "accelerators":
            validated[key] = _validate_accelerators(value)
        elif key == "tool_versions":
            validated[key] = _validate_tool_versions(value)
        elif key == "warnings":
            validated[key] = _validate_label_list(key, value)
        elif value is None:
            validated[key] = None
        else:
            validated[key] = _validate_scalar(key, value)
    return validated


def _validate_accelerators(value: Any) -> list[dict[str, Any]]:
    """Validate the accelerator list: zero or more records, each on its own allowlist."""

    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise SchemaRefusal("accelerators", "must be a list of accelerator objects")
    records: list[dict[str, Any]] = []
    for index, entry in enumerate(value):
        records.append(
            _validate_number_map(
                f"accelerators[{index}]", entry, ALLOWED_ACCELERATOR_FIELDS
            )
        )
    return records


def _validate_tool_versions(value: Any) -> dict[str, str]:
    """Validate the tool-version map: label keys, label values, nothing free-form.

    An OPEN key set (the tools present vary by host) but a CLOSED value shape, because a version
    string from an unknown tool is exactly where a path could arrive.
    """

    if not isinstance(value, Mapping):
        raise SchemaRefusal("tool_versions", "must be an object")
    out: dict[str, str] = {}
    for raw_name in sorted(map(str, value.keys())):
        if not _LABEL_RE.match(raw_name):
            raise SchemaRefusal(
                f"tool_versions.{raw_name}", "is not a short tool label"
            )
        item = value[raw_name]
        if not isinstance(item, str) or not _LABEL_RE.match(item):
            raise SchemaRefusal(
                f"tool_versions.{raw_name}",
                "must be a short version label; raw command output is REFUSED",
            )
        out[raw_name] = item
    return out


def build_event(
    *,
    event_kind: str,
    execution_id: str,
    monotonic_offset_seconds: float,
    wall_timestamp: str | None = None,
    clock: Callable[[], float] | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """Build and VALIDATE one event. The only constructor a producer should use.

    Validation happens here rather than at write time, so a malformed event never reaches the
    stream at all: the refusal is raised out of the constructor instead of being written and then
    filtered.
    """

    event: dict[str, Any] = {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "event_kind": event_kind,
        "execution_id": execution_id,
        "monotonic_offset_seconds": monotonic_offset_seconds,
        "wall_timestamp": wall_timestamp
        if wall_timestamp is not None
        else _utc_now(clock),
    }
    for key, value in fields.items():
        if value is None:
            continue
        event[key] = value
    return validate_event(event)


def _utc_now(clock: Callable[[], float] | None = None) -> str:
    """An ISO-8601 UTC timestamp. Injectable so a test never depends on the real clock."""

    now = clock() if clock is not None else time.time()
    whole = int(now)
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(whole))


# --- Node identity -----------------------------------------------------------------------------
def node_identity_input() -> str:
    """Assemble the raw machine-identity string that :func:`node_pseudonym` hashes.

    Returned separately so a test can prove the INPUT never reaches the output. The value is
    composed of a hostname, a platform node label, and a machine architecture; each is identifying
    to some degree, which is exactly why it is hashed and never persisted.
    """

    parts: list[str] = []
    for probe in (socket.getfqdn, socket.gethostname, platform.node):
        try:
            value = probe()
        except Exception:  # noqa: BLE001 - identity assembly must never raise
            continue
        if value:
            parts.append(str(value))
    try:
        parts.append(platform.machine())
    except Exception:  # noqa: BLE001
        pass
    if not parts:
        # No identity available at all: fall back to a constant so the pseudonym is still stable
        # on this box. Deliberately NOT a random value, which would make every event a new node,
        # and deliberately NOT an environment value, since env may never be a host-identity source.
        parts.append("unknown-node")
    return "\x00".join(parts)


def node_pseudonym(*, salt: str, raw: str | None = None) -> str:
    """``node:<16 hex>`` from ``sha256(salt || domain || machine identity)``.

    STABLE for one machine and one salt; DIFFERENT on another machine; UNCORRELATABLE across boxes
    or across salt generations, because the salt is per-box and lives with the disposable analytics
    cache (see :mod:`agent_workflows.run_analytics_privacy`, which owns the salt file and states the
    same contract). Rotating the salt invalidates correlation BY DESIGN.

    CORRELATION SCOPE, stated so nobody over-reads it: within one box and one salt generation, two
    events carrying the same ``node_id`` were produced on the same machine. Nothing more. It does
    not identify the machine, it cannot be reversed without the salt, and it must never be
    documented as anonymous: it is a PSEUDONYM, and a pseudonym plus timing side knowledge is
    correlatable in principle.

    NEITHER THE RAW HOSTNAME NOR THE HASH INPUT IS PERSISTED. This function is the only place the
    raw value exists, and it returns only the digest.
    """

    if not salt:
        raise SchemaRefusal("node_id", "cannot be derived without a salt")
    material = node_identity_input() if raw is None else raw
    digest = hashlib.sha256(
        salt.encode("utf-8") + b"\x00node\x00" + material.encode("utf-8")
    ).hexdigest()
    return f"node:{digest[:16]}"


# --- Probes ------------------------------------------------------------------------------------
class ResourceProbeAdapter:
    """The injectable probe interface. Every method returns a :class:`ProbeOutcome`, never raises.

    Two implementations ship: :class:`SystemResourceProbeAdapter` reads the real machine, and
    :class:`FakeResourceProbeAdapter` is what tests use. The interface exists so no test needs a
    real device, a real subprocess, or a real ``/proc``.
    """

    def cpu(self) -> ProbeOutcome:
        raise NotImplementedError

    def memory(self) -> ProbeOutcome:
        raise NotImplementedError

    def load(self) -> ProbeOutcome:
        raise NotImplementedError

    def process(self) -> ProbeOutcome:
        raise NotImplementedError

    def disk(self, path: Path | str) -> ProbeOutcome:
        raise NotImplementedError

    def tool_versions(self) -> ProbeOutcome:
        raise NotImplementedError

    def accelerators(self) -> ProbeOutcome:
        raise NotImplementedError

    def resources(self, *, disk_path: Path | str | None = None) -> dict[str, Any]:
        """Compose one ``resources`` object from the individual probes.

        A failing probe contributes NOTHING except its reason code in ``unavailable``, so a
        degraded host still yields a well-formed record and a completed run.
        """

        resources: dict[str, Any] = {}
        unavailable: list[str] = []
        for name, outcome in (
            ("cpu", self.cpu()),
            ("memory", self.memory()),
            ("load", self.load()),
            ("process", self.process()),
        ):
            if outcome.ok and isinstance(outcome.value, Mapping):
                resources.update({str(k): v for k, v in outcome.value.items()})
            else:
                unavailable.append(f"{name}:{outcome.reason}")
        if disk_path is not None:
            disk = self.disk(disk_path)
            if disk.ok and isinstance(disk.value, Mapping):
                resources.update({str(k): v for k, v in disk.value.items()})
            else:
                unavailable.append(f"disk:{disk.reason}")
        if unavailable:
            # A single joined LABEL, not a message: it must pass the label vocabulary, which is
            # what stops a formatted error string (and the path inside it) from arriving here.
            resources["unavailable"] = "+".join(sorted(unavailable))
        return resources


class SystemResourceProbeAdapter(ResourceProbeAdapter):
    """Read-only, bounded, portable probes for the real machine.

    MODELED ON ``bench_env.py`` (see the module docstring for the reuse decision and why it is not
    imported): a total ``/proc`` reader, a subprocess helper with ``capture_output``, an explicit
    ``timeout`` and ``check=False``, and the rule that an unread value is reported unavailable
    rather than fabricated. Nothing here writes, and nothing here raises.
    """

    def __init__(
        self,
        *,
        max_probe_seconds: float = MAX_PROBE_SECONDS,
        max_output_bytes: int = MAX_ACCELERATOR_OUTPUT_BYTES,
        runner: Callable[[list[str], float], tuple[int, str]] | None = None,
    ) -> None:
        self.max_probe_seconds = max(0.05, float(max_probe_seconds))
        self.max_output_bytes = int(max_output_bytes)
        #: Injectable so the accelerator parser can be tested without a real vendor tool.
        self._runner = runner if runner is not None else self._run_bounded

    # -- helpers --
    def _read_text(self, path: str) -> str:
        """Total ``/proc`` / ``/sys`` reader: ``""`` on any failure, never an exception."""

        try:
            return Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def _run_bounded(self, argv: list[str], timeout: float) -> tuple[int, str]:
        """Run one read-only informational command under a timeout and an output cap.

        Returns ``(returncode, truncated_stdout)``. A missing tool, a non-zero exit, or a timeout
        is reported through the return code rather than an exception, and the output is TRUNCATED
        at the cap so a flooding tool cannot exhaust memory. STDERR is discarded entirely and is
        never returned, because it is the most likely place for a path to appear.
        """

        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            return (-1, "")
        except (OSError, subprocess.SubprocessError):
            return (-2, "")
        return (completed.returncode, (completed.stdout or "")[: self.max_output_bytes])

    # -- probes --
    def cpu(self) -> ProbeOutcome:
        values: dict[str, Any] = {}
        try:
            values["cpu_logical_count"] = os.cpu_count()
        except Exception:  # noqa: BLE001 - a probe may never raise
            values["cpu_logical_count"] = None
        try:
            values["cpu_usable_count"] = (
                len(os.sched_getaffinity(0))
                if hasattr(os, "sched_getaffinity")
                else os.cpu_count()
            )
        except Exception:  # noqa: BLE001
            values["cpu_usable_count"] = None
        try:
            values["cpu_architecture"] = _as_label(platform.machine())
            values["platform_system"] = _as_label(platform.system())
            # LEADING DIGITS ONLY, because the schema requires `^\d{1,6}$` and one non-conforming
            # field makes `validate_event` refuse the WHOLE event. Measured on the Windows Server
            # CI runner: `platform.release()` is `2025Server`, so every start/end event was
            # refused and no telemetry stream was written at all. No digits -> omit the field.
            _release_major = re.match(r"\d{1,6}", platform.release() or "")
            values["platform_release_major"] = (
                _as_label(_release_major.group(0)) if _release_major else None
            )
        except Exception:  # noqa: BLE001
            pass
        values["container_hint"] = self._container_hint()
        cleaned = {k: v for k, v in values.items() if v is not None}
        if not cleaned:
            return ProbeOutcome("unavailable")
        return ProbeOutcome("ok", cleaned)

    def _container_hint(self) -> str | None:
        """A categorical containerization hint, or None. Never a path and never a mount line."""

        if Path("/.dockerenv").exists():
            return "docker"
        cgroup = self._read_text("/proc/1/cgroup")
        if not cgroup:
            return None
        lowered = cgroup.lower()
        for token in ("kubepods", "docker", "containerd", "podman", "lxc"):
            if token in lowered:
                return token
        return None

    def memory(self) -> ProbeOutcome:
        text = self._read_text("/proc/meminfo")
        if not text:
            return ProbeOutcome("unavailable")
        fields = {
            "MemTotal": "memory_total_bytes",
            "MemAvailable": "memory_available_bytes",
            "SwapTotal": "swap_total_bytes",
            "SwapFree": "swap_free_bytes",
        }
        values: dict[str, Any] = {}
        for line in text.splitlines():
            name, _, rest = line.partition(":")
            target = fields.get(name.strip())
            if target is None:
                continue
            parts = rest.split()
            if not parts:
                continue
            try:
                amount = int(parts[0])
            except ValueError:
                continue
            values[target] = amount * 1024 if len(parts) > 1 else amount
        if not values:
            return ProbeOutcome("parse_error", detail_bytes=len(text.encode("utf-8")))
        return ProbeOutcome("ok", values)

    def load(self) -> ProbeOutcome:
        try:
            one, five, fifteen = os.getloadavg()
        except (OSError, AttributeError):
            return ProbeOutcome("not_supported")
        return ProbeOutcome(
            "ok",
            {
                "load_average_1m": round(one, 2),
                "load_average_5m": round(five, 2),
                "load_average_15m": round(fifteen, 2),
            },
        )

    def process(self) -> ProbeOutcome:
        values: dict[str, Any] = {}
        try:
            import resource as resource_module

            usage = resource_module.getrusage(resource_module.RUSAGE_SELF)
            multiplier = 1 if platform.system() == "Darwin" else 1024
            values["process_rss_bytes"] = int(usage.ru_maxrss) * multiplier
            values["process_cpu_seconds"] = round(
                float(usage.ru_utime) + float(usage.ru_stime), 3
            )
        except Exception:  # noqa: BLE001 - absent on some platforms; never fatal
            pass
        if not values:
            return ProbeOutcome("not_supported")
        return ProbeOutcome("ok", values)

    def disk(self, path: Path | str) -> ProbeOutcome:
        """Capacity for the filesystem holding ``path``. The PATH ITSELF IS NEVER PERSISTED."""

        try:
            usage = shutil.disk_usage(str(path))
        except PermissionError:
            return ProbeOutcome("permission_denied")
        except OSError:
            return ProbeOutcome("unavailable")
        return ProbeOutcome(
            "ok", {"disk_total_bytes": usage.total, "disk_free_bytes": usage.free}
        )

    def tool_versions(self) -> ProbeOutcome:
        """Versions of the tools that shape a run's timing. Labels only, never raw output."""

        versions: dict[str, str] = {}
        python_version = _as_label(platform.python_version())
        if python_version:
            versions["python"] = python_version
        try:
            from agent_workflows import __version__ as package_version

            label = _as_label(str(package_version))
            if label:
                versions["agent_workflows"] = label
        except Exception:  # noqa: BLE001 - a version lookup may never break telemetry
            pass
        if not versions:
            return ProbeOutcome("unavailable")
        return ProbeOutcome("ok", versions)

    def accelerators(self) -> ProbeOutcome:
        """The ONE probe that shells out to a vendor tool, hence its own strict rules.

        A STRICT EXECUTABLE ALLOWLIST (never a configurable command), an explicit timeout, an
        output-size cap, and a parser that yields ONLY numeric and categorical fields. On a parse
        failure the outcome carries the error code and the BYTE LENGTH, never the bytes: a vendor
        tool's output can contain a hostname, a path, or a serial number, so persisting the text
        that failed to parse would defeat the entire privacy design of this module.
        """

        for executable in _ACCELERATOR_EXECUTABLES:
            located = shutil.which(executable)
            if not located:
                continue
            if executable == "nvidia-smi":
                argv = [
                    executable,
                    "--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version",
                    "--format=csv,noheader,nounits",
                ]
            else:
                argv = [executable, "--showid", "--csv"]
            code, out = self._runner(argv, self.max_probe_seconds)
            if code == -1:
                return ProbeOutcome("timeout")
            if code != 0 or not out.strip():
                return ProbeOutcome("unavailable")
            vendor = "nvidia" if executable == "nvidia-smi" else "amd"
            records = _parse_accelerator_csv(out, vendor=vendor)
            if records is None:
                # THE BYTE LENGTH, NOT THE BYTES.
                return ProbeOutcome(
                    "parse_error", detail_bytes=len(out.encode("utf-8", "replace"))
                )
            return ProbeOutcome("ok", records)
        return ProbeOutcome("unavailable")


def _parse_accelerator_csv(text: str, *, vendor: str) -> list[dict[str, Any]] | None:
    """Parse vendor CSV into allowlisted records, or None if nothing parsed.

    Returns None rather than a partial record when NO line yields a usable field, so the caller can
    report ``parse_error`` with a byte count. A line that parses partially contributes only the
    fields that parsed, because a missing utilization reading is not a reason to discard a known
    memory total.
    """

    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cells = [cell.strip() for cell in line.split(",")]
        record: dict[str, Any] = {"vendor": vendor}
        name = _as_label(cells[0]) if cells else None
        if name:
            record["name"] = name
        for index, key in (
            (1, "memory_total_mib"),
            (2, "memory_used_mib"),
            (3, "utilization_percent"),
        ):
            if index < len(cells):
                number = _as_int(cells[index])
                if number is not None:
                    record[key] = number
        if len(cells) > 4:
            driver = _as_label(cells[4])
            if driver:
                record["driver_version"] = driver
        if len(record) > 1:
            records.append(record)
    return records or None


def _as_label(text: Any) -> str | None:
    """Accept a probed string AS a label, or reject it. It REJECTS; it does not scrub.

    THIS FUNCTION USED TO DELETE DISALLOWED CHARACTERS, AND THAT WAS THE DENYLIST FAILURE MODE IN
    MINIATURE. Stripping the offending bytes out of ``<html><body>error at /home/<user>/x</body>``
    yields ``htmlbodyerroratholmeuserx``, which passes every label check, is persisted as if it were
    a GPU model name, and (worse) means the accelerator parser reports ``ok`` for a page of HTML
    instead of ``parse_error``. A sanitizer that turns garbage into a plausible value destroys the
    signal that the input was garbage, and it can carry fragments of the very path it was meant to
    remove. So: the ONLY normalization is collapsing internal whitespace to ``-``, because a GPU
    model name legitimately contains spaces. Anything still outside the label character class is a
    REJECTION (``None``), which the caller turns into an explicit reason code.
    """

    if not isinstance(text, str):
        return None
    collapsed = re.sub(r"\s+", "-", text.strip())
    if not collapsed or len(collapsed) > 128:
        return None
    if not _LABEL_RE.match(collapsed):
        return None
    return collapsed


def _as_int(text: Any) -> int | None:
    try:
        return int(str(text).strip())
    except (TypeError, ValueError):
        return None


class FakeResourceProbeAdapter(ResourceProbeAdapter):
    """A deterministic adapter for tests: no device, no subprocess, no ``/proc``, no sleep.

    Every probe's outcome is supplied by the caller, so a test can construct any degraded system
    (procfs absent, GPU tool absent, malformed output, a timeout) without touching the host. It
    also COUNTS calls, which is how a test proves a probe was or was not invoked.
    """

    def __init__(
        self,
        *,
        cpu: ProbeOutcome | None = None,
        memory: ProbeOutcome | None = None,
        load: ProbeOutcome | None = None,
        process: ProbeOutcome | None = None,
        disk: ProbeOutcome | None = None,
        tool_versions: ProbeOutcome | None = None,
        accelerators: ProbeOutcome | None = None,
        delay: float = 0.0,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self._cpu = (
            cpu if cpu is not None else ProbeOutcome("ok", {"cpu_logical_count": 8})
        )
        self._memory = (
            memory
            if memory is not None
            else ProbeOutcome("ok", {"memory_total_bytes": 1 << 34})
        )
        self._load = (
            load if load is not None else ProbeOutcome("ok", {"load_average_1m": 0.5})
        )
        self._process = (
            process
            if process is not None
            else ProbeOutcome("ok", {"process_rss_bytes": 1 << 24})
        )
        self._disk = (
            disk
            if disk is not None
            else ProbeOutcome("ok", {"disk_free_bytes": 1 << 36})
        )
        self._tool_versions = (
            tool_versions
            if tool_versions is not None
            else ProbeOutcome("ok", {"python": "3.14.0"})
        )
        self._accelerators = (
            accelerators if accelerators is not None else ProbeOutcome("unavailable")
        )
        #: A SIMULATED probe cost. Applied through an injected sleeper so a test can make a probe
        #: "slower than the sampling interval" without spending real time.
        self.delay = float(delay)
        self._sleeper = sleeper
        self.calls: dict[str, int] = {}

    def _count(self, name: str) -> None:
        self.calls[name] = self.calls.get(name, 0) + 1
        if self.delay and self._sleeper is not None:
            self._sleeper(self.delay)

    def cpu(self) -> ProbeOutcome:
        self._count("cpu")
        return self._cpu

    def memory(self) -> ProbeOutcome:
        self._count("memory")
        return self._memory

    def load(self) -> ProbeOutcome:
        self._count("load")
        return self._load

    def process(self) -> ProbeOutcome:
        self._count("process")
        return self._process

    def disk(self, path: Path | str) -> ProbeOutcome:
        self._count("disk")
        return self._disk

    def tool_versions(self) -> ProbeOutcome:
        self._count("tool_versions")
        return self._tool_versions

    def accelerators(self) -> ProbeOutcome:
        self._count("accelerators")
        return self._accelerators


# --- Collector ---------------------------------------------------------------------------------
@dataclass
class _CollectorCounters:
    """Mutable counters the collector reports in its ``end`` event."""

    sequence: int = 0
    samples_skipped: int = 0
    probe_errors: int = 0
    warnings: list[str] = field(default_factory=list)


class TelemetryCollector:
    """Context-managed collector: exactly one ``start``, a best-effort ``end``, idempotent close.

    USES THE EXISTING WRITER. Events go through
    :func:`agent_workflows.runner_shared.append_jsonl`, which is the package's JSONL authority and
    is used throughout both runners. NOTE THE PROPERTY THAT MATTERS FOR OVERHEAD: that function
    calls ``os.fsync`` on EVERY event. That is correct for low-volume run events and is a real
    per-sample cost for a periodic sampler, which is why the sampling interval has a floor of one
    second (see :mod:`agent_workflows.run_analytics_config`) and why the measured cost is stated in
    this plan's validation rather than assumed. A second, unsynced writer was deliberately NOT
    added: one writer, one durability contract.

    NEVER FATAL. Every write is wrapped: an unwritable stream, a full disk, or a permission error
    records a warning code and continues, because runner reliability must not depend on telemetry.

    OWNS NO PROCESS POLICY. This object registers no signal handler and calls no shutdown routine;
    it exposes ``close()`` (and the context-manager protocol) and nothing more. Spec ``c4gd2h`` R5
    makes ``runner_shutdown.clean_shutdown`` the ONE cleanup implementation and prohibits divergent
    per-level cleanup, so the wiring belongs to the runner-integration plan, not here.
    """

    def __init__(
        self,
        stream_path: Path | str,
        *,
        execution_id: str,
        salt: str,
        config: TelemetryConfig | None = None,
        adapter: ResourceProbeAdapter | None = None,
        context: Mapping[str, Any] | None = None,
        monotonic: Callable[[], float] | None = None,
        wall_clock: Callable[[], float] | None = None,
        writer: Callable[[Path, dict[str, Any]], None] | None = None,
        disk_path: Path | str | None = None,
    ) -> None:
        self.stream_path = Path(stream_path)
        self.execution_id = execution_id
        self.salt = salt
        self.config = config if config is not None else TelemetryConfig()
        self.adapter = (
            adapter
            if adapter is not None
            else SystemResourceProbeAdapter(
                max_probe_seconds=self.config.max_probe_seconds
            )
        )
        self.context = dict(context or {})
        self._monotonic = monotonic if monotonic is not None else time.monotonic
        self._wall_clock = wall_clock if wall_clock is not None else time.time
        self._disk_path = disk_path
        self.counters = _CollectorCounters()
        self._started_at: float | None = None
        self._closed = False
        self._lock = threading.Lock()
        if writer is not None:
            self._writer = writer
        else:
            from agent_workflows.runner_shared import append_jsonl

            self._writer = append_jsonl

    # -- lifecycle --
    def __enter__(self) -> TelemetryCollector:
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def start(self) -> dict[str, Any] | None:
        """Emit the single ``start`` event. Idempotent: a second call emits nothing."""

        with self._lock:
            if self._started_at is not None:
                return None
            self._started_at = self._monotonic()
        return self._emit("start")

    def sample(self) -> dict[str, Any] | None:
        """Emit one ``sample`` event, or nothing when telemetry is disabled or already closed."""

        if self._closed or self._started_at is None:
            return None
        return self._emit("sample")

    def close(self) -> dict[str, Any] | None:
        """Emit the best-effort ``end`` event. IDEMPOTENT: a second call is a no-op.

        Idempotency is load-bearing rather than defensive. The runner integration will reach this
        from a normal return, from an exception path, and from the shared cleanup routine, and a
        second ``end`` would corrupt every duration computed from the stream.
        """

        with self._lock:
            if self._closed or self._started_at is None:
                self._closed = True
                return None
            self._closed = True
        return self._emit("end")

    @property
    def closed(self) -> bool:
        return self._closed

    def elapsed_seconds(self) -> float:
        """Seconds since ``start``, from the MONOTONIC clock, so it can never be negative.

        A wall clock can step backwards (NTP correction, a suspended laptop, a container clock
        skew) and would produce a negative duration that the schema refuses; the monotonic clock
        cannot, which is why durations derive from it and only TIMESTAMPS come from the wall clock.
        """

        if self._started_at is None:
            return 0.0
        return max(0.0, self._monotonic() - self._started_at)

    # -- internals --
    def _emit(self, kind: str) -> dict[str, Any] | None:
        if not self.config.enabled:
            return None
        self.counters.sequence += 1
        resources = self._observe_resources()
        accelerators, accel_warning = self._observe_accelerators()
        tool_versions = self._observe_tool_versions()
        warnings = list(dict.fromkeys(self.counters.warnings + accel_warning))

        payload: dict[str, Any] = {
            "schema_version": TELEMETRY_SCHEMA_VERSION,
            "event_kind": kind,
            "execution_id": self.execution_id,
            "monotonic_offset_seconds": round(self.elapsed_seconds(), 6),
            "wall_timestamp": _utc_now(self._wall_clock),
            "sequence": self.counters.sequence,
            "node_id": self._node_id(),
            "resources": resources,
        }
        if accelerators:
            payload["accelerators"] = accelerators
        if tool_versions:
            payload["tool_versions"] = tool_versions
        if warnings:
            payload["warnings"] = warnings
        if kind == "end":
            payload["duration_seconds"] = round(self.elapsed_seconds(), 6)
            payload["sample_skipped_count"] = self.counters.samples_skipped
            payload["probe_error_count"] = self.counters.probe_errors
        for key, value in self.context.items():
            if key in ALLOWED_FIELDS and key not in payload and value is not None:
                payload[key] = value

        try:
            event = validate_event(payload)
        except SchemaRefusal:
            # A refusal here is a BUG in this module, not in the host, and it must not take the run
            # down. Record the code and drop the event; the stream stays well formed.
            self._note("telemetry-event-refused")
            return None
        self._write(event)
        return event

    def _node_id(self) -> str | None:
        try:
            return node_pseudonym(salt=self.salt)
        except Exception:  # noqa: BLE001 - identity failure is a warning, never fatal
            self._note("node-id-unavailable")
            return None

    def _observe_resources(self) -> dict[str, Any]:
        try:
            resources = self.adapter.resources(disk_path=self._disk_path)
        except Exception:  # noqa: BLE001 - an adapter is third-party-ish; never trust it to behave
            self.counters.probe_errors += 1
            self._note("resource-probe-failed")
            return {"unavailable": "resources:unavailable"}
        if "unavailable" in resources:
            self.counters.probe_errors += 1
        return resources

    def _observe_accelerators(self) -> tuple[list[dict[str, Any]], list[str]]:
        try:
            outcome = self.adapter.accelerators()
        except Exception:  # noqa: BLE001
            self.counters.probe_errors += 1
            return ([], ["accelerator-probe-failed"])
        if outcome.ok and isinstance(outcome.value, list):
            return (outcome.value, [])
        self.counters.probe_errors += 1
        # The REASON CODE only. `detail_bytes` is deliberately not persisted as a field, because it
        # is a diagnostic about a failure and the warning code already says which failure it was.
        return ([], [f"accelerator-{outcome.reason}"])

    def _observe_tool_versions(self) -> dict[str, str]:
        try:
            outcome = self.adapter.tool_versions()
        except Exception:  # noqa: BLE001
            return {}
        if outcome.ok and isinstance(outcome.value, Mapping):
            return {str(k): str(v) for k, v in outcome.value.items()}
        return {}

    def _note(self, code: str) -> None:
        if code not in self.counters.warnings:
            self.counters.warnings.append(code)

    def _write(self, event: dict[str, Any]) -> None:
        try:
            self._writer(self.stream_path, event)
        except Exception:  # noqa: BLE001 - an unwritable stream must never end a run
            self._note("telemetry-write-failed")

    def note_skipped_sample(self) -> None:
        """Count an overlapping sample the sampler SKIPPED rather than queued."""

        self.counters.samples_skipped += 1


# --- Sampler -----------------------------------------------------------------------------------
class ResourceSampler:
    """A bounded background sampler. Stops on every path, and SKIPS rather than accumulating.

    THE SHAPE IS COPIED, NOT INVENTED. ``oc_runipd.StallWatchdog`` and
    ``lane_containment.TurnBoundWatch`` already implement this pattern in this package, and a third
    shape would be a third thing to get wrong: a ``threading.Event`` stop flag, a ``daemon=True``
    thread started in ``__enter__``, a ``_stop.wait(interval)`` loop rather than ``sleep`` (so a
    stop is observed at once instead of after the interval), and ``__exit__`` setting the event then
    joining with a timeout. ``daemon=True`` plus the join is what makes it impossible for a
    telemetry thread to outlive its run or to block shutdown.

    SKIP, NEVER QUEUE. If a sample takes longer than the interval (a slow ``/proc``, a wedged
    vendor tool), the next tick is SKIPPED and COUNTED. Accumulating would make a degraded machine
    progressively more degraded, which is the opposite of what an observability feature may do.

    NO SIGNAL HANDLER, NO SECOND CLEANUP PATH. Stopping is a plain method call. Spec ``c4gd2h`` R5
    requires one cleanup implementation and A9 a structural check that exactly one exists, and the
    runner already records a prior plan being refused permission to register ``signal.signal``
    handlers; so the runner integration calls ``stop()``, and this class knows nothing about
    signals or processes.
    """

    def __init__(
        self,
        collector: TelemetryCollector,
        *,
        interval_seconds: float | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self.collector = collector
        configured = (
            interval_seconds
            if interval_seconds is not None
            else collector.config.sample_interval_seconds
        )
        self.interval = max(0.01, float(configured))
        #: Clamped against the interval exactly as the shipped watchdogs clamp their check period,
        #: so a stop is observed promptly even with a long interval.
        self.check_interval = min(self.interval, max(0.05, self.interval / 4.0))
        self._monotonic = monotonic if monotonic is not None else time.monotonic
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._sampling = threading.Event()
        self.samples_taken = 0
        self.samples_skipped = 0

    @property
    def enabled(self) -> bool:
        """Sampling runs only when BOTH telemetry and sampling are enabled."""

        return self.collector.config.samples_enabled

    def tick(self) -> bool:
        """Take ONE sample unless one is already in flight. Returns True if a sample was taken.

        Separated from the thread loop so a test can drive the skip logic deterministically,
        without a real thread and without real time.
        """

        if self._sampling.is_set():
            self.samples_skipped += 1
            self.collector.note_skipped_sample()
            return False
        self._sampling.set()
        try:
            self.collector.sample()
            self.samples_taken += 1
            return True
        finally:
            self._sampling.clear()

    def _run(self) -> None:
        last = self._monotonic()
        while not self._stop.wait(self.check_interval):
            now = self._monotonic()
            if now - last < self.interval:
                continue
            last = now
            try:
                self.tick()
            except Exception:  # noqa: BLE001 - a sampler failure must not kill the thread
                return

    def start(self) -> None:
        if self._thread is not None or not self.enabled:
            return
        self._thread = threading.Thread(
            target=self._run, name="aw-telemetry-sampler", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """The whole stop API. Idempotent, bounded, and safe to call from any path."""

        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=1.0)
            self._thread = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def __enter__(self) -> ResourceSampler:
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()
