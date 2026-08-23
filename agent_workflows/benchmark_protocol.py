"""Preregistered, frozen benchmark scoring + stopping protocol.

awoptimize Order 12 (`1jfxvo`) E-04.

Before any live execution (Order 13), the scoring and stopping rules are PREREGISTERED and FROZEN: the
pass/fail ground-truth policy, the adjudication process, the retry policy, randomization, contamination
controls, the flaky-test policy, unavailable-combination handling, and a no-cherry-picking rule are all
committed to a versioned document whose canonical digest is computed once. That digest is the "freeze".

The anti-tuning guarantee: a change to ANY frozen decision field (a metric, threshold, retry count,
exclusion/contamination rule, or ground-truth policy) MUST change the protocol digest, so a post-result
edit is detectable. :func:`assert_frozen` REJECTS any protocol whose digest differs from a frozen digest
unless the ``protocol_version`` was bumped (a declared, honest new version - not a silent retune).

Pure + stdlib-only (D138; D139). No filesystem/model/network side effects.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, NamedTuple, Tuple

PROTOCOL_SCHEMA_VERSION = 1

# The DECISION fields that are frozen. Any change to one of these must bump protocol_version.
# Every field here participates in the frozen digest.
FROZEN_DECISION_FIELDS: Tuple[str, ...] = (
    "pass_fail_ground_truth",  # how ground truth defines pass vs fail (policy string/spec)
    "metrics",  # the metric names computed (ordered list)
    "thresholds",  # numeric thresholds keyed by metric
    "adjudication",  # the adjudication process (tie-break, verifier authority)
    "retries",  # retry policy (max retries, failure classes eligible)
    "randomization",  # seed/order randomization policy
    "contamination_controls",  # controls preventing train/test contamination
    "flaky_test_policy",  # how flaky tests are handled (quarantine, reruns)
    "unavailable_combination_handling",  # what to do when a (host, factor) cell is unavailable
    "no_cherry_picking_rule",  # the rule forbidding post-hoc result selection
    "stopping_rule",  # when to stop trials (sample size / sequential rule)
)


class ProtocolError(ValueError):
    """Raised on a malformed protocol or an unfrozen (untuned-away) change."""


class ProtocolValidation(NamedTuple):
    ok: bool
    findings: Tuple[str, ...]


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _decision_view(protocol: Mapping[str, Any]) -> Dict[str, Any]:
    """The exact subset of a protocol that the frozen digest covers: the version + every frozen
    decision field. Prose commentary, authorship, and dates are deliberately excluded, so a cosmetic
    edit is a digest no-op but a decision change is not."""
    view: Dict[str, Any] = {
        "schema_version": protocol.get("schema_version", PROTOCOL_SCHEMA_VERSION),
        "protocol_version": protocol.get("protocol_version"),
    }
    for field in FROZEN_DECISION_FIELDS:
        view[field] = protocol.get(field)
    return view


def protocol_digest(protocol: Mapping[str, Any]) -> str:
    """SHA-256 over the canonical JSON of the frozen decision view. Two protocols that agree on every
    decision field AND version hash identically; any decision change (or a version bump) differs."""
    return hashlib.sha256(
        _canonical_json(_decision_view(protocol)).encode("utf-8")
    ).hexdigest()


class FrozenProtocol(NamedTuple):
    """A protocol whose digest has been computed and frozen. Carry this beside results; a later
    protocol that must match is checked with :func:`assert_frozen`."""

    protocol_version: int
    digest: str
    decision_view: Dict[str, Any]


def validate_protocol(protocol: Mapping[str, Any]) -> ProtocolValidation:
    """Validate a protocol carries every frozen decision field and an integer protocol_version."""
    findings: List[str] = []
    if not isinstance(protocol, Mapping):
        return ProtocolValidation(False, ("protocol must be a mapping",))
    pv = protocol.get("protocol_version")
    if not isinstance(pv, int) or isinstance(pv, bool) or pv < 1:
        findings.append("protocol_version must be an int >= 1")
    for field in FROZEN_DECISION_FIELDS:
        if field not in protocol:
            findings.append("missing frozen decision field: {0}".format(field))
    return ProtocolValidation(len(findings) == 0, tuple(findings))


def freeze_protocol(protocol: Mapping[str, Any]) -> FrozenProtocol:
    """Validate + freeze a protocol: compute and pin its digest BEFORE any run. Raises ProtocolError if
    the protocol is incomplete."""
    val = validate_protocol(protocol)
    if not val.ok:
        raise ProtocolError(
            "cannot freeze an incomplete protocol: {0}".format(list(val.findings))
        )
    return FrozenProtocol(
        protocol_version=int(protocol["protocol_version"]),
        digest=protocol_digest(protocol),
        decision_view=_decision_view(protocol),
    )


def assert_frozen(candidate: Mapping[str, Any], frozen: FrozenProtocol) -> None:
    """Assert a candidate protocol is either byte-identical (in its decision view) to the frozen one,
    OR is a HONESTLY-DECLARED new version (protocol_version strictly greater).

    Raises ProtocolError when a decision field changed WITHOUT a version bump - i.e. a post-result
    retune of any metric/threshold/retry/exclusion/ground-truth. This is the anti-cherry-picking gate.
    """
    val = validate_protocol(candidate)
    if not val.ok:
        raise ProtocolError(
            "candidate protocol is invalid: {0}".format(list(val.findings))
        )
    cand_version = int(candidate["protocol_version"])
    cand_digest = protocol_digest(candidate)

    if cand_digest == frozen.digest:
        return  # unchanged: fine

    # The digest changed. That is ONLY allowed if the version was honestly bumped.
    if cand_version <= frozen.protocol_version:
        changed = changed_decision_fields(frozen.decision_view, candidate)
        raise ProtocolError(
            "post-result change to frozen decision field(s) {0} without a protocol_version bump "
            "(frozen v{1}, candidate v{2}): a metric/threshold/retry/exclusion/ground-truth may not "
            "be retuned after results without a new protocol version".format(
                changed, frozen.protocol_version, cand_version
            )
        )
    # cand_version > frozen.protocol_version: a declared new version is allowed (a NEW protocol, not a
    # silent retune of the frozen one).
    return


def changed_decision_fields(
    frozen_view: Mapping[str, Any], candidate: Mapping[str, Any]
) -> Tuple[str, ...]:
    """List the frozen decision fields whose value differs between the frozen view and a candidate."""
    cand_view = _decision_view(candidate)
    changed: List[str] = []
    for field in FROZEN_DECISION_FIELDS:
        if frozen_view.get(field) != cand_view.get(field):
            changed.append(field)
    return tuple(changed)
