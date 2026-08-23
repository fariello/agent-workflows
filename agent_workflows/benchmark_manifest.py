"""Versioned benchmark result-identity manifest for the agent-behavior benchmark corpus.

awoptimize Order 12 (`1jfxvo`) E-01.

This module defines the RESULT-IDENTITY manifest: the exact, versioned tuple of configuration
factors that identify a single benchmark run so results from different configurations can NEVER be
accidentally pooled without every declared factor matching. Two results may be compared/pooled only
when their result-identity keys are identical; otherwise they belong to different cells.

Design invariants (from the IPD, authoritative):

  * Enforcement CEILINGS are time/trial based (per-trial wall-time seconds, trial-count), plus an
    OPTIONAL token ceiling that is admissible ONLY where the host reports tokens. Ceilings are NEVER
    a dollar or credit-pool figure the harness cannot measure. Setting a dollar/credit ceiling is
    rejected.

  * USAGE capture is a set of OPTIONAL, host-tagged fields, each independently present or the literal
    sentinel ``unavailable`` (never inferred, never zero-filled):
        - ``wall_time``       : always captured (seconds, float).
        - ``tokens``          : only where the host emits it, else ``unavailable``.
        - ``credits_or_quota``: opaque, host-specific (e.g. a Gemini pool). Not cross-model comparable.
    A dollar ``cost`` field is NOT a captured or enforced field: constructing usage with a ``cost``
    key is rejected.

  * Every configuration FACTOR (model id, reasoning/effort, host+version, adapter digest, workflow
    digest, tool/permission policy, task seed, trial, timeout, ceilings, environment fingerprint) is
    part of the result-identity key. A result missing any factor is not identifiable and is rejected.

Pure + stdlib-only (D138; D139: no runtime YAML). No filesystem, model, or network side effects: this
module DEFINES and VALIDATES manifest shapes and computes deterministic identity keys/digests.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Tuple

MANIFEST_SCHEMA_VERSION = 1

# The literal sentinel for an unavailable usage field. Never inferred, never zero-filled.
UNAVAILABLE = "unavailable"

# The exact, ordered set of configuration FACTORS that constitute a result's identity. EVERY one is
# required in a manifest; a manifest missing any factor is not identifiable and cannot be a result key.
IDENTITY_FACTORS: Tuple[str, ...] = (
    "model_id",  # exact vendor id or configuration string (e.g. a Gemini thinking level)
    "reasoning_effort",  # reasoning / effort configuration (e.g. "medium", "high", "none")
    "host",  # the runner host name (e.g. "opencode", "claude-code", "gemini")
    "host_version",  # the host's version string
    "adapter_digest",  # sha256 of the runner adapter's semantic contract
    "workflow_digest",  # sha256 of the compiled workflow's semantic view (Order 01)
    "tool_policy_digest",  # sha256 of the tool/permission policy
    "task_seed",  # the seeded task's stable id
    "trial",  # the trial index within a (config, task) cell
    "timeout_seconds",  # the per-trial timeout
    "ceilings_digest",  # sha256 of the enforcement ceilings block
    "environment_fingerprint",  # sha256 of the scrubbed environment fingerprint
)

# The usage-capture field names (each optional, present-or-`unavailable`).
USAGE_FIELDS: Tuple[str, ...] = ("wall_time", "tokens", "credits_or_quota")

# Field names that are FORBIDDEN anywhere in usage: dollar cost is neither captured nor enforced.
_FORBIDDEN_USAGE_KEYS: Tuple[str, ...] = ("cost", "dollars", "usd", "price")

# Ceiling field names that are FORBIDDEN: a harness cannot measure dollars/credit-pools as a ceiling.
_FORBIDDEN_CEILING_KEYS: Tuple[str, ...] = (
    "cost",
    "dollars",
    "usd",
    "price",
    "credits",
    "credit_pool",
    "quota",
)


class ManifestError(ValueError):
    """Raised when a manifest / ceilings / usage block violates a result-identity invariant."""


class Finding(NamedTuple):
    code: str
    where: str
    message: str


class ManifestValidation(NamedTuple):
    ok: bool
    findings: Tuple[Finding, ...]


# ---- canonicalization -----------------------------------------------------------------------------


def _canonical_json(obj: Any) -> str:
    """Deterministic JSON encoding (sorted keys, compact) matching the repo's digest convention."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(obj: Any) -> str:
    return hashlib.sha256(_canonical_json(obj).encode("utf-8")).hexdigest()


# ---- ceilings -------------------------------------------------------------------------------------


class Ceilings(NamedTuple):
    """Enforcement ceilings. Time/trial always; an OPTIONAL token ceiling only where the host reports
    tokens. NEVER a dollar/credit-pool figure."""

    per_trial_wall_seconds: float
    trial_count: int
    token_ceiling: Optional[int]  # admissible ONLY where host_reports_tokens is True
    host_reports_tokens: bool

    def as_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "per_trial_wall_seconds": float(self.per_trial_wall_seconds),
            "trial_count": int(self.trial_count),
            "host_reports_tokens": bool(self.host_reports_tokens),
        }
        # token_ceiling is only present when the host reports tokens; otherwise omitted entirely
        # (not zero-filled) so a token-less host's ceilings block is honest about the absence.
        if self.token_ceiling is not None:
            d["token_ceiling"] = int(self.token_ceiling)
        return d

    def digest(self) -> str:
        return _digest(self.as_dict())


def make_ceilings(
    per_trial_wall_seconds: float,
    trial_count: int,
    *,
    token_ceiling: Optional[int] = None,
    host_reports_tokens: bool = False,
    **forbidden: Any,
) -> Ceilings:
    """Construct enforcement ceilings, rejecting dollar/credit-pool ceilings and a token ceiling on a
    host that does not report tokens."""
    if forbidden:
        bad = sorted(forbidden)
        raise ManifestError(
            "ceilings may not include unmeasurable/forbidden fields: {0}".format(bad)
        )
    if per_trial_wall_seconds <= 0:
        raise ManifestError("per_trial_wall_seconds must be > 0")
    if trial_count <= 0:
        raise ManifestError("trial_count must be > 0")
    if token_ceiling is not None:
        if not host_reports_tokens:
            raise ManifestError(
                "a token_ceiling is admissible ONLY where the host reports tokens"
            )
        if token_ceiling <= 0:
            raise ManifestError("token_ceiling must be > 0 when present")
    return Ceilings(
        per_trial_wall_seconds=float(per_trial_wall_seconds),
        trial_count=int(trial_count),
        token_ceiling=token_ceiling,
        host_reports_tokens=bool(host_reports_tokens),
    )


def validate_ceilings_dict(d: Mapping[str, Any]) -> ManifestValidation:
    """Validate a raw ceilings mapping (e.g. after round-trip): reject any forbidden dollar/credit key."""
    findings: List[Finding] = []
    for k in d:
        if k.lower() in _FORBIDDEN_CEILING_KEYS:
            findings.append(
                Finding(
                    "BM-C010",
                    "ceilings.{0}".format(k),
                    "ceilings may not enforce an unmeasurable dollar/credit figure",
                )
            )
    if "per_trial_wall_seconds" not in d:
        findings.append(
            Finding("BM-C011", "ceilings", "missing per_trial_wall_seconds")
        )
    if "trial_count" not in d:
        findings.append(Finding("BM-C012", "ceilings", "missing trial_count"))
    if "token_ceiling" in d and not d.get("host_reports_tokens"):
        findings.append(
            Finding(
                "BM-C013",
                "ceilings.token_ceiling",
                "token_ceiling present but host_reports_tokens is false",
            )
        )
    return ManifestValidation(len(findings) == 0, tuple(findings))


# ---- usage capture --------------------------------------------------------------------------------


def make_usage(
    wall_time: float,
    *,
    tokens: Any = UNAVAILABLE,
    credits_or_quota: Any = UNAVAILABLE,
    **forbidden: Any,
) -> Dict[str, Any]:
    """Build an honest usage-capture block.

    ``wall_time`` is always captured (a real float, in seconds). ``tokens`` and ``credits_or_quota``
    are each independently present OR the literal ``unavailable`` sentinel: they are NEVER inferred and
    NEVER zero-filled. A dollar ``cost`` (or any forbidden alias) is rejected outright.
    """
    if forbidden:
        raise ManifestError(
            "usage may not include forbidden fields (dollar cost is not captured): {0}".format(
                sorted(forbidden)
            )
        )
    if not isinstance(wall_time, (int, float)) or isinstance(wall_time, bool):
        raise ManifestError("usage.wall_time is always captured and must be a number")
    if wall_time < 0:
        raise ManifestError("usage.wall_time must be >= 0")
    usage: Dict[str, Any] = {"wall_time": float(wall_time)}
    # tokens: either a non-negative int or the sentinel; never zero-filled to fake availability.
    if tokens is UNAVAILABLE or tokens == UNAVAILABLE:
        usage["tokens"] = UNAVAILABLE
    else:
        if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0:
            raise ManifestError(
                "usage.tokens must be a non-negative int or the 'unavailable' sentinel"
            )
        usage["tokens"] = int(tokens)
    # credits_or_quota: opaque host-specific value or the sentinel.
    usage["credits_or_quota"] = (
        UNAVAILABLE
        if (credits_or_quota is UNAVAILABLE or credits_or_quota == UNAVAILABLE)
        else credits_or_quota
    )
    return usage


def validate_usage(usage: Mapping[str, Any]) -> ManifestValidation:
    """Validate a usage block: wall_time present + numeric; forbidden dollar cost absent; each optional
    field is a real value or the ``unavailable`` sentinel (never a silent zero)."""
    findings: List[Finding] = []
    if not isinstance(usage, Mapping):
        return ManifestValidation(
            False, (Finding("BM-U001", "usage", "usage must be a mapping"),)
        )
    for k in usage:
        if k.lower() in _FORBIDDEN_USAGE_KEYS:
            findings.append(
                Finding(
                    "BM-U010",
                    "usage.{0}".format(k),
                    "dollar cost is not a captured usage field",
                )
            )
    wt = usage.get("wall_time")
    if not isinstance(wt, (int, float)) or isinstance(wt, bool):
        findings.append(
            Finding("BM-U011", "usage.wall_time", "wall_time must always be captured")
        )
    for opt in ("tokens", "credits_or_quota"):
        if opt not in usage:
            findings.append(
                Finding(
                    "BM-U012",
                    "usage.{0}".format(opt),
                    "optional usage field must be present-or-'unavailable', not omitted",
                )
            )
    tokens = usage.get("tokens")
    if tokens is not None and tokens != UNAVAILABLE:
        if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0:
            findings.append(
                Finding(
                    "BM-U013",
                    "usage.tokens",
                    "tokens must be a non-negative int or 'unavailable'",
                )
            )
    return ManifestValidation(len(findings) == 0, tuple(findings))


# ---- the manifest ---------------------------------------------------------------------------------


class BenchmarkManifest(NamedTuple):
    """A versioned benchmark result-identity manifest.

    The ``identity`` mapping carries every factor in :data:`IDENTITY_FACTORS`. ``usage`` is the honest
    optional-capture block. ``ceilings`` are enforcement limits (time/trial, optional token).
    """

    schema_version: int
    identity: Dict[str, Any]
    ceilings: Dict[str, Any]
    usage: Dict[str, Any]

    def result_key(self) -> Tuple[Any, ...]:
        """The ordered result-identity key: the tuple of every identity factor's value. Two results
        may be pooled/compared only when their result_key() tuples are equal."""
        return tuple(self.identity[f] for f in IDENTITY_FACTORS)

    def digest(self) -> str:
        """A deterministic digest over the identity + ceilings (usage is a RESULT, not identity)."""
        return _digest(
            {
                "identity": self.identity,
                "ceilings": self.ceilings,
                "schema_version": self.schema_version,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "identity": dict(self.identity),
            "ceilings": dict(self.ceilings),
            "usage": dict(self.usage),
        }

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())


def build_manifest(
    *,
    model_id: str,
    reasoning_effort: str,
    host: str,
    host_version: str,
    adapter_digest: str,
    workflow_digest: str,
    tool_policy_digest: str,
    task_seed: str,
    trial: int,
    timeout_seconds: float,
    ceilings: Ceilings,
    environment_fingerprint: str,
    usage: Optional[Mapping[str, Any]] = None,
) -> BenchmarkManifest:
    """Construct a fully-specified manifest. Every identity factor is required by keyword. The usage
    block defaults to a wall_time=0.0 stub with tokens/credits ``unavailable`` (a not-yet-run result)."""
    ident: Dict[str, Any] = {
        "model_id": str(model_id),
        "reasoning_effort": str(reasoning_effort),
        "host": str(host),
        "host_version": str(host_version),
        "adapter_digest": str(adapter_digest),
        "workflow_digest": str(workflow_digest),
        "tool_policy_digest": str(tool_policy_digest),
        "task_seed": str(task_seed),
        "trial": int(trial),
        "timeout_seconds": float(timeout_seconds),
        "ceilings_digest": ceilings.digest(),
        "environment_fingerprint": str(environment_fingerprint),
    }
    if usage is None:
        usage_block = make_usage(0.0)
    else:
        # validate the provided usage; raise on a forbidden dollar cost
        val = validate_usage(usage)
        if not val.ok:
            raise ManifestError(
                "invalid usage block: {0}".format([f.message for f in val.findings])
            )
        usage_block = dict(usage)
    return BenchmarkManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        identity=ident,
        ceilings=ceilings.as_dict(),
        usage=usage_block,
    )


def manifest_from_dict(d: Mapping[str, Any]) -> BenchmarkManifest:
    """Reconstruct a manifest from a round-tripped mapping, validating structure. Raises ManifestError
    if any identity factor is missing (an unidentifiable result) or usage/ceilings are malformed."""
    if not isinstance(d, Mapping):
        raise ManifestError("manifest must be a mapping")
    ident = d.get("identity")
    if not isinstance(ident, Mapping):
        raise ManifestError("manifest.identity must be a mapping")
    missing = [f for f in IDENTITY_FACTORS if f not in ident]
    if missing:
        raise ManifestError(
            "manifest is missing required identity factors (unidentifiable result): {0}".format(
                sorted(missing)
            )
        )
    ceilings = d.get("ceilings")
    if not isinstance(ceilings, Mapping):
        raise ManifestError("manifest.ceilings must be a mapping")
    cval = validate_ceilings_dict(ceilings)
    if not cval.ok:
        raise ManifestError(
            "invalid ceilings: {0}".format([f.message for f in cval.findings])
        )
    usage = d.get("usage")
    if not isinstance(usage, Mapping):
        raise ManifestError("manifest.usage must be a mapping")
    uval = validate_usage(usage)
    if not uval.ok:
        raise ManifestError(
            "invalid usage: {0}".format([f.message for f in uval.findings])
        )
    return BenchmarkManifest(
        schema_version=int(d.get("schema_version", MANIFEST_SCHEMA_VERSION)),
        identity=dict(ident),
        ceilings=dict(ceilings),
        usage=dict(usage),
    )


def manifest_from_json(text: str) -> BenchmarkManifest:
    return manifest_from_dict(json.loads(text))


def validate_manifest(m: Any) -> ManifestValidation:
    """Validate a manifest (object or mapping). Every identity factor must be present (result identity),
    a dollar cost must be absent from both ceilings and usage, and usage fields honest."""
    findings: List[Finding] = []
    if isinstance(m, BenchmarkManifest):
        d = m.to_dict()
    elif isinstance(m, Mapping):
        d = dict(m)
    else:
        return ManifestValidation(
            False,
            (
                Finding(
                    "BM-M001", "", "manifest must be a mapping or BenchmarkManifest"
                ),
            ),
        )
    ident = d.get("identity")
    if not isinstance(ident, Mapping):
        findings.append(Finding("BM-M002", "identity", "identity must be a mapping"))
        return ManifestValidation(False, tuple(findings))
    for f in IDENTITY_FACTORS:
        if f not in ident:
            findings.append(
                Finding(
                    "BM-M010",
                    "identity.{0}".format(f),
                    "result identity is missing required factor '{0}'".format(f),
                )
            )
    ceilings = d.get("ceilings", {})
    for finding in validate_ceilings_dict(ceilings).findings:
        findings.append(finding)
    usage = d.get("usage", {})
    for finding in validate_usage(usage).findings:
        findings.append(finding)
    return ManifestValidation(len(findings) == 0, tuple(findings))


def can_pool(a: BenchmarkManifest, b: BenchmarkManifest) -> bool:
    """Two results may be pooled/compared only when EVERY declared identity factor matches. Any
    difference (model, reasoning, host, digests, seed, trial, timeout, ceilings, environment) forbids
    pooling."""
    return a.result_key() == b.result_key()


def declared_factors(a: BenchmarkManifest, b: BenchmarkManifest) -> Tuple[str, ...]:
    """Return the identity factors that DIFFER between two manifests (the factors that must be declared
    before results can be split into cells)."""
    diffs: List[str] = []
    for f in IDENTITY_FACTORS:
        if a.identity.get(f) != b.identity.get(f):
            diffs.append(f)
    return tuple(diffs)
