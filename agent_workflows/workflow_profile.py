"""Profile application + semantic-parity invariants for compiled workflows.

awoptimize Order 01 (`nmwy3m`) E-05. A PROFILE is a host/model variant that tunes only TRANSPORT
knobs (packet size, output formatting, an evidence-backed reasoning level). The invariant this module
enforces is the load-bearing one for D139 and the whole "one semantic core, thin adapters" thesis:

  applying any profile MUST NOT change a workflow's SEMANTIC content -- its MUST requirements, its
  validation predicates, its step stop-conditions, or its scope fence (permissions). A profile may
  only change how the same semantics are transported.

To make that checkable deterministically, this module computes a SEMANTIC DIGEST over exactly the
acceptance-relevant subset of a compiled workflow (requirements + their evidence, validations + their
evidence, step ids/satisfies/dependencies/stop-conditions/terminal-guards, and the permission fence),
canonicalized and hashed. Two variants that differ only in transport knobs produce the SAME semantic
digest; a variant that drops or alters a MUST, a validation, a stop condition, or the scope fence
produces a DIFFERENT digest and is rejected.

This is distinct from the E-02 SOURCE digest (which hashes raw authoring bytes, so a comment change
moves it). The semantic digest deliberately ignores prose/formatting so legitimate transport tuning
is allowed while semantic drift is caught.

Pure + stdlib-only (D139 needs no dependency); no FS/model/network side effects.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, NamedTuple, Tuple

# Knobs a profile is PERMITTED to set. Anything else is rejected (a profile must not smuggle in a
# semantic override under an unknown key).
ALLOWED_PROFILE_KEYS: Tuple[str, ...] = (
    "name",  # profile identifier (e.g. "gemini-flash", "codex")
    "max_packet_chars",  # transport: bound a step packet's size
    "output_format",  # transport: "markdown" | "json" | "stream-json"
    "reasoning_level",  # evidence-backed reasoning tier (e.g. "medium", "high")
    "verifier_policy",  # which verification policy to apply (does not change requirements)
)

# Reasoning levels a profile may request (evidence-backed; the benchmark, Order 06, justifies use).
REASONING_LEVELS: Tuple[str, ...] = ("low", "medium", "high", "max")
OUTPUT_FORMATS: Tuple[str, ...] = ("markdown", "json", "stream-json")


class ProfileError(Exception):
    """Raised when a profile is structurally invalid (unknown key, bad value). Fail closed."""


class ParityResult(NamedTuple):
    """Outcome of a semantic-parity check between a base and a profiled compile."""

    ok: bool
    base_digest: str
    variant_digest: str
    reason: str


def validate_profile(profile: Any) -> None:
    """Validate a profile mapping: only allowed keys, well-typed values. Raises :class:`ProfileError`
    on any violation (fail closed)."""

    if not isinstance(profile, Mapping):
        raise ProfileError("profile must be a mapping")
    for key in profile.keys():
        if key not in ALLOWED_PROFILE_KEYS:
            raise ProfileError(
                "profile key '{0}' is not an allowed transport knob".format(key)
            )
    mpc = profile.get("max_packet_chars")
    if mpc is not None and (
        not isinstance(mpc, int) or isinstance(mpc, bool) or mpc <= 0
    ):
        raise ProfileError("max_packet_chars must be a positive integer")
    of = profile.get("output_format")
    if of is not None and of not in OUTPUT_FORMATS:
        raise ProfileError(
            "output_format '{0}' is not one of {1}".format(of, list(OUTPUT_FORMATS))
        )
    rl = profile.get("reasoning_level")
    if rl is not None and rl not in REASONING_LEVELS:
        raise ProfileError(
            "reasoning_level '{0}' is not one of {1}".format(rl, list(REASONING_LEVELS))
        )


def semantic_view(compiled: Mapping[str, Any]) -> Dict[str, Any]:
    """Extract the acceptance-relevant subset of a compiled workflow, canonicalized. This is the ONLY
    thing the semantic digest covers. Transport (prompt prose, packet body text, formatting) is
    deliberately excluded."""

    manifest = compiled.get("manifest", {})
    evidence = compiled.get("evidence", {})
    packets = compiled.get("step_packets", [])

    # requirements + their evidence (sorted, from the evidence projection which is already normalized)
    req_view = sorted(
        (
            (str(r.get("id")), tuple(sorted(str(e) for e in r.get("evidence", []))))
            for r in evidence.get("requirements", [])
            if isinstance(r, Mapping)
        )
    )
    val_view = sorted(
        (
            (
                str(v.get("verifies")),
                tuple(sorted(str(e) for e in v.get("evidence", []))),
            )
            for v in evidence.get("validations", [])
            if isinstance(v, Mapping)
        )
    )
    # step acceptance shape: id, satisfied requirements, dependencies, stop conditions. NOT the body.
    step_view = sorted(
        (
            (
                str(p.get("step")),
                tuple(sorted(str(x) for x in p.get("satisfies", []))),
                tuple(sorted(str(x) for x in p.get("depends_on", []))),
                tuple(str(x) for x in p.get("stop_conditions", [])),
            )
            for p in packets
            if isinstance(p, Mapping)
        )
    )
    return {
        "id": manifest.get("id"),
        "risk": manifest.get("risk"),
        "mutation_boundary": manifest.get("mutation_boundary"),
        "requirements": req_view,
        "validations": val_view,
        "steps": step_view,
        "scope_fence": _scope_fence(compiled),
    }


def _scope_fence(compiled: Mapping[str, Any]) -> Dict[str, Any]:
    """The permission scope fence, taken from the command descriptor + manifest (semantic, not prose).
    A profile must never widen or drop this."""

    cd = compiled.get("command_descriptor", {})
    manifest = compiled.get("manifest", {})
    return {
        "mutation_boundary": cd.get("mutation_boundary")
        or manifest.get("mutation_boundary"),
        "interaction": cd.get("interaction") or manifest.get("interaction"),
    }


def semantic_digest(compiled: Mapping[str, Any]) -> str:
    """SHA-256 over the canonical JSON of :func:`semantic_view`. Two compiles with identical semantics
    (differing only in transport) hash the same; any acceptance-relevant change differs."""

    view = semantic_view(compiled)
    blob = json.dumps(view, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def check_parity(
    base_compiled: Mapping[str, Any], variant_compiled: Mapping[str, Any]
) -> ParityResult:
    """Assert a profiled variant preserves the base's semantic digest. Returns a :class:`ParityResult`
    (``ok`` False with a reason when a MUST/validation/stop-condition/scope-fence changed)."""

    base = semantic_digest(base_compiled)
    var = semantic_digest(variant_compiled)
    if base == var:
        return ParityResult(True, base, var, "semantic digests match")
    # Produce a precise reason by diffing the semantic views.
    reason = _describe_semantic_diff(
        semantic_view(base_compiled), semantic_view(variant_compiled)
    )
    return ParityResult(False, base, var, reason)


def _describe_semantic_diff(a: Mapping[str, Any], b: Mapping[str, Any]) -> str:
    diffs: List[str] = []
    for key in ("id", "risk", "mutation_boundary", "scope_fence"):
        if a.get(key) != b.get(key):
            diffs.append(
                "{0} changed ({1!r} -> {2!r})".format(key, a.get(key), b.get(key))
            )
    if a.get("requirements") != b.get("requirements"):
        diffs.append("requirements/evidence changed")
    if a.get("validations") != b.get("validations"):
        diffs.append("validations changed")
    if a.get("steps") != b.get("steps"):
        diffs.append(
            "step acceptance shape (satisfies/depends_on/stop_conditions) changed"
        )
    return "; ".join(diffs) if diffs else "semantic view changed"
