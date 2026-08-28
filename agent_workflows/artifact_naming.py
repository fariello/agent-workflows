"""The single filename-grammar authority for every canonical artifact type (IPD o6b8l3).

This module is the ONLY place in the ``agent_workflows`` package that knows how an artifact
filename is SHAPED. It owns, exactly once:

* the ONE clustered grammar ``YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<facet>].md`` (``_CLUSTERED_RE``);
* the ONE closed facet enum ``ARTIFACT_TYPE_FACETS`` (the ``.<type>.md`` tokens) - the canonical
  facet POLICY is CLOSED (OQ-03 resolved by the Order 01 executor: reject unknown/typo facets,
  matching ``check_engine._TYPE_FACET`` and the shipped normalizer);
* the ONE legacy ``YYYYMMDD-HHMM-NN-<slug>[.<facet>].md`` timestamp form (``_LEGACY_TIMESTAMP_RE``);
* the ONE walkthrough dated/bare ``-walkthrough.md`` suffix forms (kept for rename back-compat) and
  the canonical ``.walkthrough.md`` FACET form (OQ-02 resolved: walkthroughs are uniform-facet);
* the ONE dated-slug ``YYYYMMDD-<slug>[.<facet>].md`` form (``_DATED_SLUG_FACET_RE``);
* the ONE permissive ``_UNIFORM_RE`` used ONLY by the rename builder, which accepts an OPEN facet
  ``[a-z0-9.-]+`` so a pre-existing name that ``artifact_rename`` accepted before still renames
  (byte-for-byte behavior preservation, see the golden suite); the CANONICAL clustered grammar
  stays CLOSED;
* research's own ``YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md`` grammar, delegated to
  ``research_contract`` (research is a type WITH extra facets, not the plans grammar).

Every builder and validator in the package imports from HERE instead of re-encoding the grammar, so
it is structurally impossible for a builder to emit a name a validator rejects (they share one
definition). The grammar itself is unchanged: every name produced or accepted before this module
existed is produced or accepted identically (pinned by ``tests/test_naming_authority_golden.py``).

Placement (OQ-01 resolved by the Order 01 executor): this authority lives in its OWN module and
imports only ``artifact_core`` primitives (``kebab``); it never imports the selector resolver or the
reference matcher, and ``artifact_core`` never imports THIS module - the import direction flows
toward core (orchestrator g6mbht module-placement principle). Pure, stdlib-only, Python 3.9
compatible.

id6-less legacy types (OQ documentation requirement): prompts, roadmaps, releases, and walkthroughs
do not yet carry an id6 in most on-disk names; they are represented here through the same clustered
grammar when they DO have an id6 (e.g. a ``.spec.md`` faceted clustered name) and through the legacy
``YYYYMMDD-HHMM-NN`` and dated-slug forms when they do not. This module still does NOT add an id6 to
those types (out of scope); it only represents whatever shape they already use.

Specs are NO LONGER in that id6-less set going forward (IPD ha55fi): ``aw specs new`` mints an id6
and emits the id6-clustered ``.spec.md`` name via :func:`build_clustered_name`, and the checker
enforces the clustered grammar for specs dated at/after ``check_engine.SPEC_ID6_CUTOVER_DATE``.
Pre-cutover legacy ``YYYYMMDD-HHMM-NN-<slug>.spec.md`` names remain valid (grandfathered) and can be
converted on demand with ``aw rename specs <legacy> --to-id6``.
"""

from __future__ import annotations

import re
from typing import Optional

from agent_workflows import artifact_core as _core

# --------------------------------------------------------------------------------------
# The single facet enum (the `.<type>.md` tokens). CLOSED policy (OQ-03).
# --------------------------------------------------------------------------------------

# The uniform artifact-type facets (spec 20260817-2147-01): the TYPE signal in the filename as
# `<...>.<type>.md`. A CLOSED enum so a dotted slug is never mis-parsed as a facet. Research keeps
# its own richer `.<model>.<kind>.md` naming and is NOT in this set.
ARTIFACT_TYPE_FACETS = (
    "ipd",
    "prompt",
    "spec",
    "walkthrough",
    "roadmap",
    "backlog",
    "comms",
    "release",
    "other",
)
_FACET_ALT = "|".join(ARTIFACT_TYPE_FACETS)

# Map a record type (plural, as used by check/status) to its canonical facet token.
TYPE_FACET = {
    "plans": "ipd",
    "specs": "spec",
    "prompts": "prompt",
    "backlog": "backlog",
    "walkthroughs": "walkthrough",
    "roadmaps": "roadmap",
    "releases": "release",
    "comms": "comms",
    "other": "other",
}

# --------------------------------------------------------------------------------------
# The single grammar regexes.
# --------------------------------------------------------------------------------------

# The CANONICAL clustered grammar: YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<type>].md with a CLOSED
# facet enum, and a bare `.md` remains valid (permanent dual-read).
_CLUSTERED_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)"
    r"(?:\.(?P<type>" + _FACET_ALT + r"))?\.md\Z"
)

# The PERMISSIVE uniform form used ONLY by the rename builder: an OPEN facet `[a-z0-9.-]+`. This
# preserves the pre-refactor `artifact_rename._UNIFORM_RE` acceptance (a name with an arbitrary
# facet still renames). The canonical clustered grammar above stays CLOSED.
_UNIFORM_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)"
    r"(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)

# The legacy timestamp form: YYYYMMDD-HHMM-NN-<slug>[.<facet>].md (open facet, as artifact_rename).
_LEGACY_TIMESTAMP_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<hhmm>\d{4})-(?P<nn>\d{2})-(?P<slug>[a-z0-9-]+)"
    r"(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)

# Walkthrough SUFFIX forms (kept for rename back-compat; the canonical builder emits the FACET form).
_WALKTHROUGH_DATED_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<slug>[a-z0-9-]+)-walkthrough\.md\Z"
)
_WALKTHROUGH_BARE_RE = re.compile(r"\A(?P<slug>[a-z0-9-]+)-walkthrough\.md\Z")

# The dated-slug form: YYYYMMDD-<slug>[.<facet>].md.
_DATED_SLUG_FACET_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<slug>[a-z0-9-]+)(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)

# The shared clustered CORE (no facet, no `.md`): YYYYMMDD-<set-id>-<NN>-<id6>-<slug>. Research's
# grammar is this core followed by its own `.<model>.<kind>.md` facets; research re-exports THIS so
# the core is defined once here and the `.<model>.<kind>` assembly stays in research_contract.
_CORE_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)\Z"
)


# --------------------------------------------------------------------------------------
# BUILD: the one clustered-name builder.
# --------------------------------------------------------------------------------------


def build_clustered_name(
    *,
    date: str,
    set_id: str,
    order: int,
    id6: str,
    slug: str,
    artifact_type: Optional[str] = None,
) -> str:
    """Assemble a clustered filename ``YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<type>].md``.

    When ``artifact_type`` is one of ``ARTIFACT_TYPE_FACETS`` the uniform ``.<type>`` facet is
    appended; when ``None`` (or empty) the bare ``.md`` form is produced (backward-compatible).
    Raises ``ValueError`` for an unknown ``artifact_type``.
    """

    facet = ""
    if artifact_type:
        if artifact_type not in ARTIFACT_TYPE_FACETS:
            raise ValueError(f"unknown artifact_type {artifact_type!r}")
        facet = f".{artifact_type}"
    return (
        f"{date}-{_core.kebab(set_id)}-{order:02d}-{id6}-{_core.kebab(slug)}{facet}.md"
    )


# --------------------------------------------------------------------------------------
# PARSE / VALIDATE: the one clustered parser + conformance wrapper.
# --------------------------------------------------------------------------------------


def parse_clustered(name: str):
    """Return the ``re.Match`` for the CANONICAL (closed-facet) clustered grammar, or ``None``.

    The match exposes groups ``date``, ``set``, ``nn``, ``id6``, ``slug``, and ``type`` (the facet,
    or ``None`` for a bare ``.md``). An unknown/typo facet does NOT match (closed enum, OQ-03).
    """

    return _CLUSTERED_RE.match(name)


def parse_uniform_permissive(name: str):
    """Return the ``re.Match`` for the PERMISSIVE uniform form (open facet), or ``None``.

    Used ONLY by the rename builder to preserve the pre-refactor acceptance of an arbitrary facet.
    The match exposes ``date``, ``set``, ``nn``, ``id6``, ``slug``, ``facet``.
    """

    return _UNIFORM_RE.match(name)


def is_clustered_conformant(name: str, expected_type: str = "ipd") -> bool:
    """True iff ``name`` is a valid CLOSED-facet clustered name whose facet (if present) equals
    ``expected_type`` (a bare ``.md`` is conformant for any type; a wrong/typo facet is not)."""

    m = _CLUSTERED_RE.match(name)
    if m is None:
        return False
    facet = m.groupdict().get("type")
    return facet is None or facet == expected_type
