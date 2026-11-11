"""The single filename-grammar authority for every canonical artifact type (IPD o6b8l3).

This module is the ONLY place in the ``agent_workflows`` package that knows how an artifact
filename is SHAPED. It owns, exactly once:

* the ONE clustered grammar ``YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<facet>].md`` (``_CLUSTERED_RE``);
* the ONE closed facet enum ``ARTIFACT_TYPE_FACETS`` (the ``.<type>.md`` tokens: ``ipd``,
  ``prompt``, ``spec``, ``walkthrough``, ``roadmap``, ``backlog``, ``comms``, ``release``,
  ``review``, ``other``) - the canonical facet POLICY is CLOSED (OQ-03 resolved by the Order 01
  executor: reject unknown/typo facets, matching ``check_engine._TYPE_FACET`` and the shipped
  normalizer). NOTE that ``ARTIFACT_TYPE_FACETS`` (which names are LEGAL) and ``TYPE_FACET`` (which
  record types have a status lifecycle) are deliberately NOT mirrors of each other: ``review`` is a
  legal facet with no ``TYPE_FACET`` entry (revgate Order 01), just as research has its own grammar;
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
existed is produced or accepted identically (the round-trip property is asserted behaviorally by
``tests/test_artifact_naming_round_trip.py`` while the structural single-source property remains
unguarded, having been asserted in ``tests/test_naming_authority_single_source.py`` deleted in
``19313eed`` and deliberately not restored as a source-reading pin, P16; the pre-refactor golden
snapshot that guarded the migration was retired once the migration landed).

Placement (OQ-01 resolved by the Order 01 executor): this authority lives in its OWN module and
imports only ``artifact_core`` primitives (``kebab``); it never imports the selector resolver or the
reference matcher, and ``artifact_core`` never imports THIS module - the import direction flows
toward core (orchestrator g6mbht module-placement principle). Pure, stdlib-only, Python 3.9
compatible.

id6-less legacy types (OQ documentation requirement): walkthroughs adopt the id6-clustered
grammar going forward under the ``walkthrough_id6`` cutover with pre-cutover legacy names
grandfathered, releases mint an id6 at creation (``releases.render_release`` calls ``_core.mint_id6``),
and roadmaps have no producer and are clustered by convention (the checker does not enforce id6
for roadmaps).

Specs are NO LONGER in that id6-less set going forward (IPD ha55fi): ``aw specs new`` mints an id6
and emits the id6-clustered ``.spec.md`` name via :func:`build_clustered_name`, and the checker
enforces the clustered grammar for specs dated at/after the repository's dynamic spec_id6 cutover
date (resolved dynamically via ``config.resolve_cutover_date`` / ``check_engine.SPEC_ID6_CUTOVER_DATE``).
Pre-cutover legacy ``YYYYMMDD-HHMM-NN-<slug>.spec.md`` names remain valid (grandfathered) and can be
converted on demand with ``aw rename specs <legacy> --to-id6``.

PROMPTS ARE ALSO OUT OF THAT SET going forward (IPD ubac5n), on the same pattern and for the same
reason a spec needed it: an artifact with no id6 is unresolvable by every `aw` verb, which for a
staged prompt means it cannot be cited by the research report it produced. ``aw prompts new`` mints an
id6 and emits the id6-clustered ``.prompt.md`` name via :func:`build_clustered_name`, and the checker
enforces the clustered grammar for prompts dated at/after the repository's ``prompt_id6`` cutover
(``config.resolve_cutover_date`` / ``check_engine.PROMPT_ID6_CUTOVER_DATE``). Pre-cutover legacy
``YYYYMMDD-HHMM-NN-<slug>.prompt.md`` names remain valid (grandfathered) and convert on demand with
``aw rename prompts <legacy> --to-id6``. NOTE the id6 destination differs by type: a spec gets a
``- Id:`` front-matter bullet, while a prompt's id6 goes inside its single
``<!-- aw-prompt: ... -->`` comment, because a bullet would be visible text above the prompt body
(approved spec ``20260808-1958-01-prompt-purity-lint`` R1/P4). This REVERSES IPD ``jxqdcw`` OQ-02 on
the maintainer's explicit instruction (2026-09-20), which was a resolved choice on the evidence then
available and not an oversight.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple, Optional, Tuple

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
    "review",
    "other",
)
_FACET_ALT = "|".join(ARTIFACT_TYPE_FACETS)

# Map a record type (plural, as used by check/status) to its canonical facet token.
#
# DELIBERATELY NOT a mirror of ARTIFACT_TYPE_FACETS (revgate Order 01 / 15zvu6, E-01 option b): this
# map is ITERATED, not merely looked up, so an entry here is a behavioral claim that the type has a
# STATUS LIFECYCLE. `status_set.detect_artifact_type` loops every item and returns the matched type,
# which would make `aw set` accept the file as status-settable. A `review` findings artifact has NO
# status lifecycle (its state is its Verdict plus per-finding Decision values, not a `- Status:`
# bullet), and nothing that consumes a `.review.md` needs the plural->facet mapping: the writer
# builds its own name via `build_clustered_name` and the parser is handed a path. So `reviews` is
# ABSENT here on purpose, and `status_set.py` needs no `reviews` exemption beside its `comms` one.
# If a future consumer genuinely needs the mapping, add it here AND add the matching skip in
# `status_set.detect_artifact_type`, or `aw set` will silently accept a review file.
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
# facet enum, and a bare `.md` remains valid (permanent dual-read). The set id and the slug are STRICT
# kebab-case: no leading, trailing or doubled hyphen (maintainer ruling 2026-11-09). That is the rule
# `normalize_plan_names` always enforced; this grammar used to be looser, so 8 tracked records with a
# trailing-hyphen slug were valid here and invalid to `aw ipd lint`. They were renamed in the same
# change, and `artifact_core.kebab_slug` now prevents a cut from producing one.
_CLUSTERED_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9]+(?:-[a-z0-9]+)*?)-(?P<nn>\d{2,3})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)"
    r"(?:\.(?P<type>" + _FACET_ALT + r"))?\.md\Z"
)

# The PERMISSIVE uniform form used ONLY by the rename builder: an OPEN facet `[a-z0-9.-]+`. This
# preserves the pre-refactor `artifact_rename._UNIFORM_RE` acceptance (a name with an arbitrary
# facet still renames). The canonical clustered grammar above stays CLOSED.
_UNIFORM_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2,3})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)"
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

# ORDER WIDTH (maintainer ruling 2026-11-09): `NN` is TWO OR THREE digits. Two digits is the form a
# Set of at most 100 plans has always used and every existing name keeps; a Set past Order 99 (the
# metastore Set reached 279 after its step-complexity split) needs a third digit. Measured before the
# change: all 4,473 tracked two-digit clustered names parse identically under `\d{2,3}`, because the
# id6 is exactly 6 characters and hyphens delimit every field. The builder pads to 2 and lets 100+
# take its natural width, so no existing name changes.
#
# The shared clustered CORE (no facet, no `.md`): YYYYMMDD-<set-id>-<NN>-<id6>-<slug>. Research's
# grammar is this core followed by its own `.<model>.<kind>.md` facets; research re-exports THIS so
# the core is defined once here and the `.<model>.<kind>` assembly stays in research_contract.
_CORE_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2,3})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)\Z"
)

# The clustered IDENTITY PREFIX: `YYYYMMDD-<set-id>-<NN>-<id6>-`, anchored at the START only, with no
# constraint on the tail. Defined HERE, in the authority, and re-exported by any consumer that needs
# it, for the same single-source reason `_CORE_RE` is (a second private copy of this grammar is
# precisely the defect attcor `rkn8ya` E-08 removed from `attention.py`, where a `[A-Za-z0-9]+` set id
# silently rejected the hyphen this module's own builder PRODUCES).
#
# WHY A PREFIX FORM IS NEEDED AT ALL, since `parse_clustered` already exists: that function anchors at
# the tail (`\Z`) with a CLOSED facet enum, so it correctly REJECTS a name whose facets it does not
# own, such as research's `.<model>.<kind>.md`. A consumer that only wants the (set, order) IDENTITY
# of such a name has a well-formed prefix to read and no legal way to read it. This is that way.
#
# THE LAZY QUANTIFIER IS LOAD-BEARING, exactly as in `_CORE_RE`: a greedy `[a-z0-9-]+` reads
# `20260101-foo-12-abc123-bar-01-def456-slug` as set `foo-12-abc123-bar` / order `01`, disagreeing
# with this module's own canonical reading of set `foo` / order `12`.
_CLUSTERED_PREFIX_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2,3})-(?P<id6>[0-9a-z]{6})-"
)


def parse_clustered_prefix(name: str):
    """Return the ``re.Match`` for the clustered IDENTITY PREFIX of ``name``, or ``None``.

    Exposes ``date``, ``set``, ``nn`` and ``id6``. Use this ONLY when the tail is legitimately not the
    canonical closed-facet form (research's `.<model>.<kind>.md`); prefer `parse_clustered`, which
    validates the WHOLE name, whenever the name is supposed to be canonical.
    """

    return _CLUSTERED_PREFIX_RE.match(name)


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


#: The legacy timestamp form as the PLAN-NAME conformance rule reads it: strict kebab slug and the
#: CLOSED facet set (no `review`/`other` facet), exactly the rule `normalize_plan_names` always
#: applied. `_LEGACY_TIMESTAMP_RE` above stays OPEN (it must also read comms message names such as
#: `<date>-<hhmm>-NN-<sender>--to--<recipient>...md`), so conformance and recognition are two named
#: rules here rather than two private copies elsewhere.
_LEGACY_TIMESTAMP_CONFORMANT_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<hhmm>\d{4})-(?P<nn>\d{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)"
    r"(?:\.(?P<type>ipd|prompt|spec|walkthrough|roadmap|backlog|comms|release))?\.md\Z"
)


#: PRE-STANDARD legacy shapes that `normalize_plan_names --apply` can rename into the canonical form
#: (ordered; first match wins). Each yields a date (or y/mo/d), an optional time or NN, and a slug.
LEGACY_RENAMABLE_RES = (
    # YYYYMMDD-HHMM-<slug>  (time, no NN): 4-digit group
    re.compile(r"^(?P<date>\d{8})-(?P<time>\d{4})-(?P<slug>.+)\.md$"),
    # YYYYMMDD-NN-<slug>    (NN, no time): 2-digit group
    re.compile(r"^(?P<date>\d{8})-(?P<nn>\d{2})-(?P<slug>.+)\.md$"),
    # YYYY-MM-DD-NN-<slug>  (hyphenated date + NN)
    re.compile(
        r"^(?P<y>\d{4})-(?P<mo>\d{2})-(?P<d>\d{2})-(?P<nn>\d{2})-(?P<slug>.+)\.md$"
    ),
    # YYYY-MM-DD-<slug>     (hyphenated date)
    re.compile(r"^(?P<y>\d{4})-(?P<mo>\d{2})-(?P<d>\d{2})-(?P<slug>.+)\.md$"),
    # YYYYMMDD-<slug>       (date only)
    re.compile(r"^(?P<date>\d{8})-(?P<slug>.+)\.md$"),
)


def parse_legacy_timestamp(name: str):
    """Return the ``re.Match`` for a legacy ``YYYYMMDD-HHMM-NN-<slug>[.<facet>].md`` name, or None.

    Groups: ``date``, ``hhmm``, ``nn``, ``slug``, ``facet``. Recognition only (open facet)."""

    return _LEGACY_TIMESTAMP_RE.match(name)


def is_legacy_timestamp_conformant(name: str) -> bool:
    """True for a legacy timestamp name that the plan-name rules accept as conformant."""

    return _LEGACY_TIMESTAMP_CONFORMANT_RE.match(name) is not None


_LEGACY_STEM_PREFIX_RE = re.compile(r"\A(\d{8}-\d{4}-\d{2})-")


def legacy_stem_prefix(name: str) -> Optional[str]:
    """The ``YYYYMMDD-HHMM-NN`` stem a legacy timestamp name starts with, or None."""

    m = _LEGACY_STEM_PREFIX_RE.match(name or "")
    return m.group(1) if m else None


def identity_parts(name: str) -> Optional[Tuple[str, str, str, str]]:
    """``(date, set, order, id6)`` from the leading identity of a clustered name, or None.

    Reads only the identity prefix ``YYYYMMDD-<set>-<NN>-<id6>-``, so it also works for names whose
    tail is not the canonical closed facet (research `.<model>.<kind>.md`, attributed names). The
    one reader every display surface (attention board, run viewer) uses for its Set/Order/id6
    columns, so a grammar change reaches them with no second edit."""

    m = _CLUSTERED_PREFIX_RE.match(name or "") or _IDENTITY_NO_SLUG_RE.match(name or "")
    if m is None:
        return None
    return m.group("date"), m.group("set"), m.group("nn"), m.group("id6")


#: The identity with NO slug: `YYYYMMDD-<set>-<NN>-<id6>` followed by a facet or the end (a display
#: surface is handed such stems, and a short record name may omit the slug).
_IDENTITY_NO_SLUG_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2,3})-(?P<id6>[0-9a-z]{6})(?=\.|\Z)"
)


def legacy_identity_parts(name: str) -> Optional[Tuple[str, str, str]]:
    """``(date, order, slug)`` of a legacy ``YYYYMMDD-HHMM-NN-<slug>`` name (no id6, no Set), or None."""

    m = re.match(r"\A(\d{8})-\d{4}-(\d{2})-([a-z0-9-]+)", name or "")
    if m is None:
        return None
    return m.group(1), m.group(2), m.group(3)


def is_plan_name_conformant(
    name: str, expected_type: str = "ipd", require_id6: bool = False
) -> bool:
    """THE filename-conformance rule `aw ipd lint` (`IPD-N001`) and `aw check` apply.

    True for a CLOSED-facet clustered name whose facet (if any) equals ``expected_type``, or, unless
    ``require_id6``, for a legacy ``YYYYMMDD-HHMM-NN-<slug>`` name (its facet is not type-checked,
    which is the compatibility rule this check always had)."""

    if is_clustered_conformant(name, expected_type=expected_type):
        return True
    if _CLUSTERED_RE.match(name) is not None or require_id6:
        return False
    return is_legacy_timestamp_conformant(name)


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


class AttributedName(NamedTuple):
    date: str
    set: str
    nn: str
    id6: str
    slug: str
    ace: Optional[str] = None
    model: Optional[str] = None
    type: Optional[str] = None

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            raise KeyError(key)
        return tuple.__getitem__(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


_FACET_TOKEN_RE = re.compile(r"\A[a-z0-9-]+\Z")


def parse_attributed(name: str) -> Optional[AttributedName]:
    """Parse a D177-attributed artifact filename:
    ``YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<ace>][.<model>].<type>.md``.

    Returns an ``AttributedName`` exposing ``date``, ``set``, ``nn``, ``id6``, ``slug``,
    optional ``ace``, optional ``model``, and ``type``. Returns ``None`` when the name
    does not conform.
    """
    clean = name.replace("\\", "/").rsplit("/", 1)[-1]
    if not clean.endswith(".md"):
        return None
    stem = clean[:-3]
    segments = stem.split(".")
    if not segments:
        return None

    m = _CORE_RE.match(segments[0])
    if m is None:
        return None

    date = m.group("date")
    set_id = m.group("set")
    nn = m.group("nn")
    id6 = m.group("id6")
    slug = m.group("slug")

    facets = segments[1:]
    for f in facets:
        if not _FACET_TOKEN_RE.match(f):
            return None

    if len(facets) == 0:
        return AttributedName(date, set_id, nn, id6, slug, None, None, None)
    elif len(facets) == 1:
        return AttributedName(date, set_id, nn, id6, slug, None, None, facets[0])
    elif len(facets) == 2:
        return AttributedName(date, set_id, nn, id6, slug, None, facets[0], facets[1])
    elif len(facets) == 3:
        return AttributedName(
            date, set_id, nn, id6, slug, facets[0], facets[1], facets[2]
        )
    else:
        return None
