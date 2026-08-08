"""Canonical research-artifact contract: the single source of truth for research naming and metadata.

This module OWNS the machine-checkable contract for `.agents/docs/research/` defined by the
specification ``.agents/docs/specs/20260730-2152-01-agents-artifact-organization.spec.md`` (Set
``research-org`` Order 01). The create tool (Order 02), the rename/refs tool (Order 04), the index
generator (Order 03), the archival tool (Order 05), the migration (Order 06), and the scaffold
(Order 07) all import from THIS module so the contract cannot fork or drift.

Scope (Order 01): definitions + pure validation/parse/format helpers ONLY. This module has no side
effects: it does not read the filesystem, call a model, use the network, or write anything. It is
stdlib-only (zero runtime dependencies, D46) and Python 3.9 compatible.

It resolves the spec's open questions with the reviewed leans:

* OQ5 -> ``<id6>`` is 6 characters of base36 lowercase (``[0-9a-z]``), collision-checked by the tool.
* OQ4 -> the leading ``YYYYMMDD`` in the name is the SET date; each file also records its own
  ``created`` date in frontmatter.
* OQ6 -> hot states (``intake``/``active``) live at the ``research/`` root; ``reference`` and
  ``archive`` live in weekly ``YYYYMM-Www`` shards.
* OQ1 -> the ``<kind>`` vocabulary is corpus-derived (below) with a documented extension mechanism.
"""

from __future__ import annotations

import re
from typing import Dict, FrozenSet, List, NamedTuple, Optional, Tuple

# --------------------------------------------------------------------------------------
# Identity: the stable, greppable ``<id6>`` (spec 4.1 / OQ5)
# --------------------------------------------------------------------------------------

ID6_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"  # base36 lowercase
ID6_LENGTH = 6

# An id token in isolation (a whole string is exactly the id).
ID6_RE = re.compile(r"\A[0-9a-z]{6}\Z")
# An id token as a word inside a filename or prose. ``\b`` treats ``-`` as a boundary, so a
# ``-`` delimited id in ``...-k7m2xq-...`` and a bare ``k7m2xq`` in prose both match (spec 4.1/D2).
ID6_WORD_RE = re.compile(r"\b[0-9a-z]{6}\b")


def is_valid_id6(token: str) -> bool:
    """True iff ``token`` is exactly a 6-char base36-lowercase id."""

    return bool(ID6_RE.match(token))


def iter_id6_in_text(text: str) -> List[str]:
    """Return every ``\\b<id6>\\b`` word-boundary match in ``text`` (for citation scanning, F5)."""

    return ID6_WORD_RE.findall(text)


# --------------------------------------------------------------------------------------
# Enumerated vocabularies (spec 5.4 / OQ1), grounded in the corpus survey.
# --------------------------------------------------------------------------------------

# ``<model>`` authorship facet. ``reconciliation`` denotes a synthesis with no single author.
MODELS: FrozenSet[str] = frozenset(
    (
        "gpt56",
        "gpt56medium",
        "gemini31pro",
        "gemini36flash",
        "sonnet5",
        "reconciliation",
    )
)

# Spelling/position drift observed in the corpus (``gpt-56`` vs ``gpt56``; product labels).
MODEL_NORMALIZATIONS: Dict[str, str] = {
    "gpt-56": "gpt56",
    "gpt-56-medium": "gpt56medium",
    "gpt56-medium": "gpt56medium",
    "gemini-31-pro": "gemini31pro",
    "gemini-36-flash": "gemini36flash",
    "sonnet-5": "sonnet5",
    "chatgpt": "gpt56",  # a product label mapped to a model version; also record provenance
}

# ``<kind>`` is MANDATORY and drawn from this corpus-derived closed-ish set. New kinds are added
# HERE (the extension mechanism): append to KINDS with a one-line justification in review.
KINDS: FrozenSet[str] = frozenset(
    (
        "research-prompt",
        "research-report",
        "reconciliation-report",
        "findings",
        "requirements",
        "advisory",
        "howto",
        "concept",
        "survey",
        "source-draft",
        "reference-research",
        "assessment",
        "notes",
        "roadmap",
        # multi-part report parts
        "executive-summary",
        "test-evidence",
        "patch-proposal",
    )
)

# Kind spelling drift observed in the corpus (singular vs plural).
KIND_NORMALIZATIONS: Dict[str, str] = {
    "finding": "findings",
    "research": "research-report",
    "requirement": "requirements",
}

# States (spec 4.5) and outcomes.
STATUSES: FrozenSet[str] = frozenset(("intake", "active", "reference", "archive"))
HOT_STATUSES: FrozenSet[str] = frozenset(("intake", "active"))
SHARDED_STATUSES: FrozenSet[str] = frozenset(("reference", "archive"))
OUTCOMES: FrozenSet[str] = frozenset(
    ("adopted", "rejected", "informational", "none-yet")
)


def _closest(token: str, vocab: FrozenSet[str]) -> Optional[str]:
    """A cheap closest-match suggestion for an unknown token (prefix/substring, then edit-ish).

    Deterministic and dependency-free: exact-after-normalization is handled by the callers; this
    only produces a hint. Returns the single best candidate or ``None``.
    """

    t = token.lower()
    # Prefer a candidate that shares the longest common prefix, tie-broken alphabetically.
    best: Optional[str] = None
    best_score = 0
    for cand in sorted(vocab):
        # common prefix length
        n = 0
        for a, b in zip(t, cand):
            if a == b:
                n += 1
            else:
                break
        # substring bonus
        score = n + (2 if t in cand or cand in t else 0)
        if score > best_score:
            best_score = score
            best = cand
    return best if best_score > 0 else None


class VocabResult(NamedTuple):
    """Outcome of validating/normalizing a vocabulary token."""

    ok: bool
    value: Optional[str]  # the normalized canonical value when ok
    suggestion: Optional[str]  # a closest-match hint when not ok
    message: str


def normalize_model(token: str) -> VocabResult:
    """Validate/normalize a ``<model>`` token against MODELS (+ MODEL_NORMALIZATIONS)."""

    raw = token.strip().lower()
    canon = MODEL_NORMALIZATIONS.get(raw, raw)
    if canon in MODELS:
        return VocabResult(True, canon, None, "ok")
    sugg = _closest(raw, MODELS)
    hint = f"; did you mean '{sugg}'?" if sugg else ""
    return VocabResult(False, None, sugg, f"unknown model '{token}'{hint}")


def normalize_kind(token: str) -> VocabResult:
    """Validate/normalize a ``<kind>`` token against KINDS (+ KIND_NORMALIZATIONS)."""

    raw = token.strip().lower()
    canon = KIND_NORMALIZATIONS.get(raw, raw)
    if canon in KINDS:
        return VocabResult(True, canon, None, "ok")
    sugg = _closest(raw, KINDS)
    hint = f"; did you mean '{sugg}'?" if sugg else ""
    return VocabResult(False, None, sugg, f"unknown kind '{token}'{hint}")


# --------------------------------------------------------------------------------------
# Slug + set-id kebab normalization
# --------------------------------------------------------------------------------------

_KEBAB_STRIP_RE = re.compile(r"[^a-z0-9]+")


def kebab(text: str) -> str:
    """Lowercase kebab-case a free string (for ``<slug>`` and ``<set-id>``); collapse separators."""

    return _KEBAB_STRIP_RE.sub("-", text.strip().lower()).strip("-")


# --------------------------------------------------------------------------------------
# Filename grammar (spec 4.2): YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md
# --------------------------------------------------------------------------------------

# The stem is split on ``.`` into: <core>[.<model>].<kind>. The core is
# ``YYYYMMDD-<set-id>-<NN>-<id6>-<slug>``. set-id and slug are kebab (may contain ``-``), so we
# anchor on the fixed-width date, NN, and id6.
_CORE_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)\Z"
)

# Weekly shard directory grammar (spec 4.9): YYYYMM-Www (e.g. 202607-W30).
SHARD_DIR_RE = re.compile(r"\A(?P<yyyymm>\d{6})-W(?P<week>\d{2})\Z")


class ResearchName(NamedTuple):
    """A parsed research filename."""

    date: str  # YYYYMMDD (the SET date)
    set_id: str
    order: str  # NN, two digits
    id6: str
    slug: str
    model: Optional[str]  # optional authorship facet
    kind: str


class NameError_(NamedTuple):
    """A structured filename-parse error."""

    message: str


def format_name(name: ResearchName) -> str:
    """Assemble a filename string from a ResearchName (inverse of ``parse_name``)."""

    model_part = f".{name.model}" if name.model else ""
    return (
        f"{name.date}-{name.set_id}-{name.order}-{name.id6}-{name.slug}"
        f"{model_part}.{name.kind}.md"
    )


def parse_name(filename: str) -> Tuple[Optional[ResearchName], Optional[NameError_]]:
    """Parse a research filename into a ResearchName, or return a structured error.

    Grammar: ``YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md``. Returns
    ``(ResearchName, None)`` on success or ``(None, NameError_)`` on failure.
    """

    if not filename.endswith(".md"):
        return None, NameError_("filename must end in '.md'")
    stem = filename[: -len(".md")]
    parts = stem.split(".")
    # parts[0] is the core; the last dotted segment is the kind; an optional middle is the model.
    if len(parts) < 2:
        return None, NameError_("name must include a '.<kind>' suffix before '.md'")
    core = parts[0]
    if len(parts) == 2:
        model: Optional[str] = None
        kind = parts[1]
    elif len(parts) == 3:
        model = parts[1]
        kind = parts[2]
    else:
        return None, NameError_(
            "name has too many dotted segments; expected [.<model>].<kind>"
        )

    m = _CORE_RE.match(core)
    if not m:
        return None, NameError_(
            "core must be 'YYYYMMDD-<set-id>-<NN>-<id6>-<slug>' " f"(got '{core}')"
        )

    kind_res = normalize_kind(kind)
    if not kind_res.ok:
        return None, NameError_(kind_res.message)
    if model is not None:
        model_res = normalize_model(model)
        if not model_res.ok:
            return None, NameError_(model_res.message)
        model = model_res.value

    return (
        ResearchName(
            date=m.group("date"),
            set_id=m.group("set"),
            order=m.group("nn"),
            id6=m.group("id6"),
            slug=m.group("slug"),
            model=model,
            kind=kind_res.value or kind,
        ),
        None,
    )


# --------------------------------------------------------------------------------------
# Directory layout (spec 4.9 / OQ6)
# --------------------------------------------------------------------------------------

RESEARCH_ROOT = ".agents/docs/research"
REFERENCE_DIR = "reference"
ARCHIVE_DIR = "archive"


def shard_dirname(yyyymm: str, week: int) -> str:
    """Return a weekly shard directory name ``YYYYMM-Www`` (e.g. ``202607-W30``)."""

    return f"{yyyymm}-W{week:02d}"


def is_valid_shard_dirname(name: str) -> bool:
    """True iff ``name`` is a valid weekly shard directory name."""

    return bool(SHARD_DIR_RE.match(name))


# --------------------------------------------------------------------------------------
# Frontmatter schema (spec 5.8)
# --------------------------------------------------------------------------------------

# Fields REQUIRED in a research doc's frontmatter, in canonical order.
FRONTMATTER_FIELDS: Tuple[str, ...] = (
    "id",
    "created",
    "set",
    "order",
    "topic",
    "model",
    "kind",
    "status",
    "outcome",
    "summary",
    "consumed-by",
)

_CREATED_RE = re.compile(r"\A\d{8}\Z")  # YYYYMMDD
_ORDER_RE = re.compile(r"\A\d{2}\Z")  # NN


class FrontmatterError(NamedTuple):
    """A structured frontmatter validation error (field + message)."""

    field: str
    message: str


def validate_frontmatter(data: Dict[str, object]) -> List[FrontmatterError]:
    """Validate a research frontmatter mapping against the schema; return structured errors.

    ``data`` is the already-parsed mapping (the caller owns YAML/text parsing so this module stays
    pure and dependency-free). An empty list means the block is valid.
    """

    errors: List[FrontmatterError] = []

    # Presence
    for field in FRONTMATTER_FIELDS:
        if field not in data:
            errors.append(FrontmatterError(field, f"missing required field '{field}'"))

    # id
    if "id" in data:
        val = data["id"]
        if not isinstance(val, str) or not is_valid_id6(val):
            errors.append(
                FrontmatterError("id", "id must be a 6-char base36-lowercase token")
            )
    # created
    if "created" in data:
        val = data["created"]
        if not isinstance(val, str) or not _CREATED_RE.match(val):
            errors.append(FrontmatterError("created", "created must be YYYYMMDD"))
    # order
    if "order" in data:
        val = data["order"]
        if not isinstance(val, str) or not _ORDER_RE.match(val):
            errors.append(
                FrontmatterError("order", "order must be a two-digit string NN")
            )
    # topic
    if "topic" in data and not isinstance(data["topic"], list):
        errors.append(FrontmatterError("topic", "topic must be a list"))
    # model (optional value but the KEY is required; may be a single model or 'reconciliation')
    if "model" in data:
        val = data["model"]
        if val not in (None, "") and isinstance(val, str):
            res = normalize_model(val)
            if not res.ok:
                errors.append(FrontmatterError("model", res.message))
    # kind
    if "kind" in data:
        val = data["kind"]
        if not isinstance(val, str):
            errors.append(FrontmatterError("kind", "kind must be a string"))
        else:
            res = normalize_kind(val)
            if not res.ok:
                errors.append(FrontmatterError("kind", res.message))
    # status
    if "status" in data:
        val = data["status"]
        if val not in STATUSES:
            errors.append(
                FrontmatterError("status", f"status must be one of {sorted(STATUSES)}")
            )
    # outcome
    if "outcome" in data:
        val = data["outcome"]
        if val not in OUTCOMES:
            errors.append(
                FrontmatterError(
                    "outcome", f"outcome must be one of {sorted(OUTCOMES)}"
                )
            )
    # consumed-by
    if "consumed-by" in data and not isinstance(data["consumed-by"], list):
        errors.append(FrontmatterError("consumed-by", "consumed-by must be a list"))

    return errors
