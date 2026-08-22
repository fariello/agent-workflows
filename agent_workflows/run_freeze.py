"""Requirement freezing + semantic-vs-cosmetic revision detection for a run's success criteria.

awoptimize Order 02 (`viuzu4`) E-04/E-05. Once a run is approved, WHAT it must achieve (its MUST
requirements, scope fence, validation predicates, and required outputs) is FROZEN: each item is bound
to a stable id and a deterministic content digest, emitted as a `requirement_set` record. An executor
that later sees a failure cannot silently redefine or drop a success criterion, because a change to a
requirement's MEANING produces a new `requirement_revision` (prev_digest -> new_digest) and marks the
evidence bound to the superseded digest as invalidated. A purely cosmetic edit (whitespace/formatting
that leaves the normalized content unchanged) is a digest no-op and does not invalidate evidence.

Pure + stdlib-only (D138: the stdlib does this; D139: no runtime YAML). No filesystem, model, or
network side effects: freezing is a deterministic function of its inputs, so the same requirements
always yield the same ids + digests, independent of machine, ordering of input, or run.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Mapping, NamedTuple, Sequence, Tuple

from agent_workflows.run_ledger_schema import Finding, ValidationResult

# The four frozen requirement categories. A frozen item's stable id is "<prefix>-<nn>".
CATEGORIES: Tuple[str, ...] = ("must", "scope", "validation", "output")
_CATEGORY_PREFIX: Dict[str, str] = {
    "must": "M",
    "scope": "SC",
    "validation": "V",
    "output": "O",
}

_WS_RE = re.compile(r"\s+")


class FrozenItem(NamedTuple):
    id: str  # stable "<prefix>-<nn>" id
    category: str  # one of CATEGORIES
    text: str  # the ORIGINAL text (kept verbatim for display/audit)
    digest: str  # sha256 of the normalized content (the semantic identity)


class RequirementSet(NamedTuple):
    requirement_digest: (
        str  # sha256 over the sorted per-item digests (the set identity)
    )
    items: Tuple[FrozenItem, ...]


class Revision(NamedTuple):
    id: str  # the item id whose meaning changed
    prev_digest: str
    new_digest: str
    invalidated_evidence: Tuple[str, ...]  # evidence ids bound to prev_digest


def _normalize(text: str) -> str:
    """Normalize a requirement's content for SEMANTIC comparison: strip, collapse internal runs of
    whitespace to a single space, and lowercase-fold is intentionally NOT applied (case can be
    semantic in code/identifiers). Cosmetic edits (indentation, trailing whitespace, wrapping) map to
    the same normalized string; a meaning change does not."""

    return _WS_RE.sub(" ", text.strip())


def _digest(category: str, normalized: str) -> str:
    # Bind the category into the digest so identical text in two categories are distinct identities.
    payload = json.dumps(
        {"category": category, "content": normalized},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_inputs(requirements: Any) -> Tuple[bool, Tuple[Finding, ...]]:
    findings: List[Finding] = []
    if not isinstance(requirements, Mapping):
        return False, (
            Finding(
                "RF-E001", "", "requirements must be a mapping of category -> list"
            ),
        )
    seen_categories = [c for c in requirements if c in CATEGORIES]
    if not seen_categories:
        findings.append(
            Finding(
                "RF-E002",
                "",
                "no known requirement categories present (expected one of {0})".format(
                    ", ".join(CATEGORIES)
                ),
            )
        )
    for cat in requirements:
        if cat not in CATEGORIES:
            findings.append(
                Finding(
                    "RF-E003", cat, "unknown requirement category '{0}'".format(cat)
                )
            )
            continue
        items = requirements[cat]
        if not isinstance(items, (list, tuple)):
            findings.append(
                Finding("RF-E004", cat, "category '{0}' must map to a list".format(cat))
            )
            continue
        for j, it in enumerate(items):
            if not isinstance(it, str):
                findings.append(
                    Finding(
                        "RF-E005",
                        "{0}[{1}]".format(cat, j),
                        "requirement item must be a string",
                    )
                )
            elif not _normalize(it):
                findings.append(
                    Finding(
                        "RF-E006",
                        "{0}[{1}]".format(cat, j),
                        "requirement item must be non-empty after normalization",
                    )
                )
    return (len(findings) == 0), tuple(findings)


def freeze_requirements(requirements: Mapping[str, Sequence[str]]) -> RequirementSet:
    """Freeze a run's requirements into stable ids + per-item digests + a set digest.

    Deterministic: the same requirements (regardless of dict iteration order) always produce the same
    ids and digests. Ids are assigned per category in the INPUT order of each category's list, so an
    author controls id assignment; the set digest is order-independent (sorted over item digests).

    Raises ValueError with the typed findings if the inputs are malformed (a missing or malformed
    requirement is refused BEFORE any set is emitted, so a partial/ambiguous freeze can never happen).
    """

    ok, findings = _validate_inputs(requirements)
    if not ok:
        raise ValueError(
            "cannot freeze requirements: "
            + "; ".join(
                "{0} {1}: {2}".format(f.code, f.where, f.message) for f in findings
            )
        )

    items: List[FrozenItem] = []
    for cat in CATEGORIES:
        raw = requirements.get(cat) or []
        prefix = _CATEGORY_PREFIX[cat]
        for idx, text in enumerate(raw, start=1):
            normalized = _normalize(text)
            items.append(
                FrozenItem(
                    id="{0}-{1:02d}".format(prefix, idx),
                    category=cat,
                    text=text,
                    digest=_digest(cat, normalized),
                )
            )

    set_payload = json.dumps(
        sorted(it.digest for it in items),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    requirement_digest = hashlib.sha256(set_payload).hexdigest()
    return RequirementSet(requirement_digest=requirement_digest, items=tuple(items))


def requirement_set_record(
    run_id: str,
    seq: int,
    actor: str,
    timestamp: str,
    parent: str,
    frozen: RequirementSet,
) -> Dict[str, Any]:
    """Build a `requirement_set` ledger record (schema-valid per run_ledger_schema) from a frozen set.
    The record binds every MUST/scope/validation/output id + digest so a downstream verifier can check
    each independently."""

    from agent_workflows.run_ledger_schema import LEDGER_SCHEMA_VERSION

    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "kind": "requirement_set",
        "seq": seq,
        "run_id": run_id,
        "actor": actor,
        "timestamp": timestamp,
        "parent": parent,
        "requirement_digest": frozen.requirement_digest,
        "requirements": [
            {"id": it.id, "category": it.category, "digest": it.digest, "text": it.text}
            for it in frozen.items
        ],
        "scope_fence": {
            it.id: it.text for it in frozen.items if it.category == "scope"
        },
    }


def diff_requirements(
    prev: RequirementSet,
    new: RequirementSet,
    evidence_by_digest: Mapping[str, Sequence[str]] | None = None,
) -> Tuple[Revision, ...]:
    """Detect SEMANTIC revisions between two frozen sets and report evidence to invalidate.

    An item id present in both sets whose digest CHANGED is a semantic revision: its meaning changed,
    so any evidence bound to the prior digest is invalidated. An item whose digest is unchanged (a
    cosmetic edit maps to the same digest) yields no revision and invalidates nothing. A newly added or
    a dropped id is also reported as a revision (added: prev_digest ""; dropped: new_digest "") so a
    caller can refuse a drop/redefine of a frozen requirement after approval.
    """

    evidence_by_digest = evidence_by_digest or {}
    prev_by_id = {it.id: it for it in prev.items}
    new_by_id = {it.id: it for it in new.items}
    revisions: List[Revision] = []

    for rid in sorted(set(prev_by_id) | set(new_by_id)):
        p = prev_by_id.get(rid)
        n = new_by_id.get(rid)
        prev_digest = p.digest if p else ""
        new_digest = n.digest if n else ""
        if prev_digest == new_digest:
            continue  # unchanged (cosmetic edits already collapse to the same digest)
        revisions.append(
            Revision(
                id=rid,
                prev_digest=prev_digest,
                new_digest=new_digest,
                invalidated_evidence=tuple(evidence_by_digest.get(prev_digest, ())),
            )
        )
    return tuple(revisions)


def refuse_drop_or_redefine(
    prev: RequirementSet, new: RequirementSet
) -> ValidationResult:
    """Fail closed if the new set DROPS or REDEFINES a frozen requirement relative to the prior set.

    This is the anti-goalpost-moving guard: after approval, an executor may not remove a MUST or change
    its meaning to make a failing run pass. Returns a ValidationResult; ok=True only if every prior id
    is still present with an unchanged digest (additions are allowed).
    """

    findings: List[Finding] = []
    prev_by_id = {it.id: it for it in prev.items}
    new_by_id = {it.id: it for it in new.items}
    for rid, p in sorted(prev_by_id.items()):
        n = new_by_id.get(rid)
        if n is None:
            findings.append(
                Finding(
                    "RF-E010", rid, "frozen requirement '{0}' was dropped".format(rid)
                )
            )
        elif n.digest != p.digest:
            findings.append(
                Finding(
                    "RF-E011",
                    rid,
                    "frozen requirement '{0}' was redefined after approval".format(rid),
                )
            )
    return ValidationResult(len(findings) == 0, tuple(findings))
