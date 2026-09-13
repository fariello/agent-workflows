"""``aw adopt``: file ONE raw ``.aw/inbox/`` drop into a typed records tree (Set awinbox, Order 01).

Adoption is the single moment unvetted EXTERNAL text crosses into permanent tracked history, so it
is the one moment where the mistake is still cheap to undo. Until this module existed the crossing
was six manual steps with no tooling, no gate, and no provenance: choose a type/kind/slug/set by
hand, mint an id6, derive the conforming name, write front matter, move the file, refresh the index.
That is exactly the hand-naming the artifact-organization specs forbid everywhere else.

WHAT THIS MODULE OWNS, and equally what it deliberately does NOT:

* it DERIVES the conforming name by CALLING ``research_cmd.plan_new`` (the existing planner for the
  research grammar) rather than re-encoding the grammar. There is no second name-deriver here;
* it MINTS a fresh id6 through ``artifact_core.generate_id6`` against a REPOSITORY-WIDE,
  DIALECT-COMPLETE collision set, injected through ``plan_new``'s ``existing_ids`` seam;
* it NEVER adopts an id6 found in the dropped body, in EITHER front-matter dialect. ``AGENTS.md``
  warns that such a line "is almost always a QUOTED EXAMPLE, and honoring it would forge an identity
  claim that collides with a real artifact";
* it GATES on the existing leak sanitizer via ``leak_sanitizer.scan_text`` (never
  ``scan_working_tree``, which enumerates TRACKED files and therefore cannot see a gitignored drop);
* it MOVES rather than copies, with the destructive removal ordered LAST;
* it PREVIEWS by default and writes only on ``--apply``: that pair IS the suggest-then-confirm
  interaction, not a second prompt layer.

DESTINATION TREES SUPPORTED ON DAY ONE: research ONLY. This is a deliberate, stated limit rather
than an oversight. The reusable planner (``research_cmd.plan_new``) normalizes against
``research_contract``'s kind/model vocabularies and emits the spec-5.8 YAML frontmatter block, so it
is research-specific; no equivalent planner exists for the bullet-dialect trees (plans/specs/
backlog), and each has a different frontmatter dialect and vocabulary. A caller naming another type
is REFUSED with that reason rather than served a half-correct artifact.

Stdlib-only, Python 3.9 compatible, and pure apart from the explicit filesystem steps a caller
requests with ``--apply``.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Set, Tuple

from agent_workflows import artifact_core as _core

# The one supported destination tree on day one (see the module docstring for why).
SUPPORTED_TYPES: Tuple[str, ...] = ("research",)

# The inbox lane. OQ-01 resolved NO: `aw adopt` accepts a path INSIDE this directory only, because
# the leak gate, the untrusted-input stance, and the remove-the-original behavior are each justified
# specifically by the inbox being a drop zone for unvetted EXTERNAL material. Pointed at an
# arbitrary file, "move it and delete the original" is a destructive operation on something the
# human may not have meant as a draft.
INBOX_REL = ".aw/inbox"

# --------------------------------------------------------------------------------------
# Body identity scanning: the two front-matter dialects, and the forged-identity guard
# --------------------------------------------------------------------------------------

# The BULLET dialect (`- Id: <id6>`), used by plans/specs/backlog/releases.
_BULLET_ID_RE = re.compile(r"(?m)^-[ \t]*Id:[ \t]*([0-9a-z]{6})[ \t]*$")
# The YAML dialect (`---` fenced, `id: <id6>`), used by RESEARCH per spec
# `20260730-2152-01-agents-artifact-organization` section 5.8 and emitted by
# `research_cmd.build_frontmatter`. This is the dialect the likeliest destination actually uses, so
# a guard written against the bullet form alone would miss the case it meets first.
_YAML_ID_RE = re.compile(r"(?m)^[ \t]*id:[ \t]*([0-9a-z]{6})[ \t]*$")

# How many body id6-shaped tokens to name in a preview before summarizing the rest.
# `artifact_core.iter_id6_in_text` matches ANY 6-char base36 word, so on a long technical document
# ordinary words ("record", "commit", "adopts") match. Reporting them all would drown the preview
# and reporting none would look identical to not having checked, so the report is BOUNDED: every
# DECLARED id (either dialect) is named unconditionally because a declaration is an identity CLAIM,
# while bare prose matches are counted and only the first few named.
BODY_TOKEN_PREVIEW_LIMIT = 5


class BodyIdentities(NamedTuple):
    """What the dropped body says about identity. NONE of this is ever adopted."""

    bullet_declared: Tuple[str, ...]  # `- Id: <id6>` lines
    yaml_declared: Tuple[str, ...]  # `---` fenced `id: <id6>` lines
    prose_tokens: Tuple[
        str, ...
    ]  # bare id6-shaped words (deliberately broad; see limit)

    @property
    def declared(self) -> Tuple[str, ...]:
        """Every id6 the body DECLARES, in either dialect (a claim, not a coincidence)."""

        seen: List[str] = []
        for tok in self.bullet_declared + self.yaml_declared:
            if tok not in seen:
                seen.append(tok)
        return tuple(seen)

    @property
    def any_identity(self) -> bool:
        return bool(self.declared or self.prose_tokens)


def _yaml_frontmatter_block(text: str) -> Optional[str]:
    """Return the leading ``---`` fenced block's INNER text, or None when absent/unterminated.

    Deliberately narrow: only a block whose FIRST line is the fence counts, so a `---` horizontal
    rule in the middle of a report is never mistaken for front matter. Mirrors
    ``research_contract.parse_frontmatter``'s framing without importing its value parsing (this
    module needs the raw text, not a typed mapping).
    """

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


def scan_body_identities(text: str) -> BodyIdentities:
    """Report every id6 the body DECLARES or MENTIONS, in BOTH front-matter dialects.

    This is a REPORTING function, never a source of a minted id. It exists so a human sees that the
    document mentions an identity and that the verb is deliberately not using it: silence here would
    look identical to not having checked.
    """

    bullet = tuple(dict.fromkeys(_BULLET_ID_RE.findall(text)))
    block = _yaml_frontmatter_block(text)
    yaml_ids = tuple(dict.fromkeys(_YAML_ID_RE.findall(block))) if block else ()
    declared = set(bullet) | set(yaml_ids)
    prose = tuple(
        dict.fromkeys(
            tok for tok in _core.iter_id6_in_text(text) if tok not in declared
        )
    )
    return BodyIdentities(
        bullet_declared=bullet, yaml_declared=yaml_ids, prose_tokens=prose
    )


def describe_body_identities(found: BodyIdentities) -> List[str]:
    """Render the BOUNDED preview lines for body identities (see BODY_TOKEN_PREVIEW_LIMIT)."""

    out: List[str] = []
    for tok in found.bullet_declared:
        out.append(
            f"body declares `- Id: {tok}` (bullet dialect): PRESENT BUT NOT ADOPTED; "
            "a fresh id6 is minted instead"
        )
    for tok in found.yaml_declared:
        out.append(
            f"body declares YAML `id: {tok}` (research dialect): PRESENT BUT NOT ADOPTED; "
            "a fresh id6 is minted instead"
        )
    if found.prose_tokens:
        shown = ", ".join(found.prose_tokens[:BODY_TOKEN_PREVIEW_LIMIT])
        extra = len(found.prose_tokens) - BODY_TOKEN_PREVIEW_LIMIT
        tail = f" (+{extra} more)" if extra > 0 else ""
        out.append(
            f"body contains {len(found.prose_tokens)} id6-shaped word(s) in prose: {shown}{tail}. "
            "These are NOT identity claims (the matcher is deliberately broad and matches ordinary "
            "six-letter words); none is adopted."
        )
    return out


# --------------------------------------------------------------------------------------
# The repository-wide, DIALECT-COMPLETE collision set
# --------------------------------------------------------------------------------------


def repository_id6s(repo_root: Path) -> Set[str]:
    """Every id6 already in use ANYWHERE in the repository's records, from BOTH dialects.

    Three sources are UNIONED, because each alone is incomplete and minting a duplicate is only
    discovered after the destination is written and the original deleted:

    1. every filename IDENTITY-SLOT id6 (the invariant ``check.id6-identity-slot`` polices);
    2. every BULLET-declared ``- Id:`` (what ``check_engine._ID_LINE_RE`` reads);
    3. every YAML-declared ``id:`` in a leading front-matter block (which the bullet reader MISSES,
       so a set built the way ``aw check`` builds its declared-id map would omit every research id).

    The id6 invariant is repository-WIDE and fail-closed, so a tree-scoped set (which is what
    ``research_cmd._existing_id6s`` produces) is insufficient by construction.
    """

    from agent_workflows import artifact_naming as _naming
    from agent_workflows import check_engine as _check

    repo_root = Path(repo_root)
    found: Set[str] = set()
    for record_type in _check.SUPPORTED:
        for p in _check._iter_type_files(repo_root, record_type, include_retired=True):
            m = _naming.parse_clustered(p.name)
            if m:
                found.add(m.group("id6"))
            else:
                # Research carries its own `.<model>.<kind>.md` grammar; ask its parser too.
                try:
                    from agent_workflows import research_contract as _R

                    parsed, _err = _R.parse_name(p.name)
                except Exception:  # pragma: no cover - defensive
                    parsed = None
                if parsed is not None:
                    found.add(parsed.id6)
            try:
                text = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            ids = scan_body_identities(text)
            found.update(ids.declared)
    return found


# --------------------------------------------------------------------------------------
# The already-adopted check (a WARNING, never a refusal)
# --------------------------------------------------------------------------------------


def _body_after_frontmatter(text: str) -> str:
    """Return ``text`` with a leading ``---`` fenced block removed, for content comparison."""

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[i + 1 :])
    return text


def _content_digest(text: str) -> str:
    """A whitespace-insensitive digest of a document's PROSE, used only for a cheap match.

    Deliberately NOT general content identity: it normalizes runs of whitespace so a reflowed or
    front-matter-wrapped copy of the same report still matches, and nothing more.
    """

    normalized = re.sub(r"\s+", " ", _body_after_frontmatter(text)).strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class AlreadyAdopted(NamedTuple):
    """A record that looks like it already holds this drop's content."""

    id6: str
    path: str
    reason: str  # "identical-body" | "same-title"


def find_already_adopted(
    repo_root: Path, text: str, *, search_root: Optional[Path] = None
) -> Optional[AlreadyAdopted]:
    """Return an existing record that appears to ALREADY hold this content, or None.

    WHY THIS EXISTS: the inbox is a queue nobody drains, so an inbox file is NOT necessarily
    un-adopted. Measured 2026-09-10: the `awmetastore` topic was already a complete six-file adopted
    set while a variant of it still sat in the inbox. Re-adopting mints a SECOND id6 for content that
    already has one, which is NOT an id6 collision, so ``aw check`` cannot detect it, which makes it
    worse than the forged-identity case the verb does guard.

    Two cheap tests, in order of confidence: an identical normalized body, then an identical first
    heading. This is a WARNING surface; the human decides, exactly as with the leak gate.
    """

    from agent_workflows import research_contract as _R

    root = (
        search_root if search_root is not None else _R.resolve_research_root(repo_root)
    )
    if not Path(root).is_dir():
        return None
    want_digest = _content_digest(text)
    want_title = _first_heading(text)
    title_match: Optional[AlreadyAdopted] = None
    for p in sorted(Path(root).rglob("*.md")):
        parsed, _err = _R.parse_name(p.name)
        if parsed is None:
            continue
        try:
            existing = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if _content_digest(existing) == want_digest:
            return AlreadyAdopted(parsed.id6, str(p), "identical-body")
        if (
            title_match is None
            and want_title
            and _first_heading(existing) == want_title
        ):
            title_match = AlreadyAdopted(parsed.id6, str(p), "same-title")
    return title_match


_HEADING_RE = re.compile(r"(?m)^#{1,3}[ \t]+(.+?)[ \t]*$")


def _first_heading(text: str) -> str:
    """The first markdown heading's text (lowercased, whitespace-collapsed), or ``""``."""

    body = _body_after_frontmatter(text)
    m = _HEADING_RE.search(body)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip().lower()


# --------------------------------------------------------------------------------------
# Metadata suggestion (the SUGGEST half of suggest-then-confirm)
# --------------------------------------------------------------------------------------

# Filename hints an external drop commonly carries, mapped onto the research kind vocabulary. Only
# UNAMBIGUOUS hints are listed; anything else falls back to the default below and is shown for
# confirmation like every other suggestion.
_KIND_FILENAME_HINTS: Tuple[Tuple[str, str], ...] = (
    ("reconciliation", "reconciliation-report"),
    ("implementation-prompt", "research-prompt"),
    ("research-prompt", "research-prompt"),
    ("prompt", "research-prompt"),
    ("research-report", "research-report"),
    ("findings", "findings"),
    ("requirements", "requirements"),
    ("advisory", "advisory"),
    ("howto", "howto"),
    ("survey", "survey"),
    ("assessment", "assessment"),
    ("roadmap", "roadmap"),
    ("report", "research-report"),
    ("research", "research-report"),
)

DEFAULT_KIND = "research-report"


class Suggestion(NamedTuple):
    """The proposed metadata, each field flagged as suggested or caller-supplied."""

    type: str
    kind: str
    slug: str
    set_id: str
    model: Optional[str]
    suggested_fields: Tuple[str, ...]


def suggest_metadata(
    filename: str,
    text: str,
    *,
    type_: Optional[str] = None,
    kind: Optional[str] = None,
    slug: Optional[str] = None,
    set_id: Optional[str] = None,
    model: Optional[str] = None,
) -> Suggestion:
    """Propose type/kind/slug/set/model from the drop, keeping any caller-supplied value.

    Reads the FILENAME and the first heading only. It does not need to be clever: whatever it
    proposes is shown for confirmation before anything is written, and a wrong guess costs the human
    one flag rather than a bad artifact.
    """

    stem = filename[: -len(".md")] if filename.endswith(".md") else filename
    # Strip the model/agent facets an external drop often carries (`....gemini31prohigh.agy.md`).
    facets = stem.split(".")
    core = facets[0]
    trailing = [f for f in facets[1:] if f]

    suggested: List[str] = []

    s_type = type_ or "research"
    if type_ is None:
        suggested.append("type")

    s_kind = kind
    if s_kind is None:
        lowered = core.lower()
        s_kind = DEFAULT_KIND
        for hint, mapped in _KIND_FILENAME_HINTS:
            if hint in lowered:
                s_kind = mapped
                break
        suggested.append("kind")

    s_model = model
    if s_model is None:
        from agent_workflows import research_contract as _R

        for facet in trailing:
            res = _R.normalize_model(facet)
            if res.ok:
                s_model = res.value
                suggested.append("model")
                break

    s_slug = slug
    if s_slug is None:
        s_slug = (
            _core.kebab(core) or _core.kebab(_first_heading(text)) or "adopted-drop"
        )
        suggested.append("slug")

    s_set = set_id
    if s_set is None:
        # A singleton whose set-id is the slug, matching `aw research new`'s omitted-set behavior.
        s_set = s_slug
        suggested.append("set")

    return Suggestion(
        type=s_type,
        kind=s_kind,
        slug=s_slug,
        set_id=s_set,
        model=s_model,
        suggested_fields=tuple(suggested),
    )


# --------------------------------------------------------------------------------------
# The leak gate (E-04): scan_text, refuse on `fail`, record the override WITHOUT the leak
# --------------------------------------------------------------------------------------


class LeakReport(NamedTuple):
    """The pre-write leak verdict. Carries rule names and line numbers, NEVER matched text."""

    fail_rules: Tuple[str, ...]
    warn_rules: Tuple[str, ...]
    fail_locations: Tuple[str, ...]
    warn_locations: Tuple[str, ...]
    scan_function: str  # recorded so a reviewer can see WHICH seam was used

    @property
    def has_fail(self) -> bool:
        return bool(self.fail_rules)


def scan_drop_for_leaks(repo_root: Path, text: str, location: str) -> LeakReport:
    """Scan the DROP CONTENT for leaks before anything is written.

    THE SEAM MATTERS AND THE OBVIOUS CHOICE IS WRONG. ``scan_working_tree`` enumerates TRACKED files
    via ``git ls-files``, and an inbox drop is gitignored and therefore untracked, so a gate built on
    it would silently pass EVERYTHING. ``scan_text`` scans supplied content line by line and is the
    correct seam for a pre-write gate on content that is not yet a tracked file.

    Findings are reduced to RULE NAMES and LOCATIONS here, at the boundary, and the ``Finding``
    objects (which carry an excerpt of the offending line) are never returned. Recording an excerpt
    into the adopted artifact would copy the leaked string into a TRACKED file, and that record would
    then fail ``aw sanitize`` on every later sweep: the naive implementation is the unsafe one.
    """

    from agent_workflows import leak_sanitizer as _leaks

    ruleset = _leaks.build_ruleset(Path(repo_root), include_warn=True)
    findings = _leaks.scan_text(text, location, ruleset, include_warn=True)
    fail_rules: List[str] = []
    warn_rules: List[str] = []
    fail_locs: List[str] = []
    warn_locs: List[str] = []
    for f in findings:
        if f.severity == "fail":
            if f.rule not in fail_rules:
                fail_rules.append(f.rule)
            if f.location not in fail_locs:
                fail_locs.append(f.location)
        else:
            if f.rule not in warn_rules:
                warn_rules.append(f.rule)
            if f.location not in warn_locs:
                warn_locs.append(f.location)
    return LeakReport(
        fail_rules=tuple(fail_rules),
        warn_rules=tuple(warn_rules),
        fail_locations=tuple(fail_locs),
        warn_locations=tuple(warn_locs),
        scan_function="leak_sanitizer.scan_text",
    )


def safe_rule_name(rule: str) -> str:
    """Return a rule name safe to write into a TRACKED artifact.

    A SECOND way the recording requirement can defeat its own purpose, found by the E-07 test rather
    than by reading: some rule NAMES embed the very token they matched. ``build_ruleset`` registers
    the auto-derived advisory patterns as ``derived:<token>`` and a config-promoted hostname as
    ``hostname:<token>``, so writing the rule name verbatim writes the leaked username or hostname
    into the artifact just as surely as writing the matched line would. Those two namespaces are
    therefore reduced to their CLASS (``derived:<redacted>``), which still says what KIND of finding
    fired. Structural rule names (``home-path``, ``handle``, ``session-id``) and indexed config rule
    names (``repo-pattern-0``, ``user-hint-1``) carry no secret and pass through unchanged.
    """

    for prefix in ("derived:", "hostname:"):
        if rule.startswith(prefix):
            return prefix + "<redacted>"
    return rule


def render_leak_note(report: LeakReport, *, override_actor: str) -> str:
    """Render the override's audit note for the adopted artifact.

    Carries the RULE NAMES, the line locations, the actor, and the fact of the override. It carries
    NO matched text, by construction: see ``scan_drop_for_leaks``. Rule names are passed through
    :func:`safe_rule_name` first, because some of them embed the matched token.
    """

    fail_rules = [safe_rule_name(r) for r in report.fail_rules]
    warn_rules = [safe_rule_name(r) for r in report.warn_rules]
    lines = [
        "",
        "<!-- aw-adopt: leak-gate override -->",
        "> LEAK-GATE OVERRIDE RECORDED. This document was adopted from `.aw/inbox/` with",
        f"> `--allow-leaks` by `{override_actor}` after the leak sanitizer reported"
        " fail-severity findings.",
        f"> Scan seam: `{report.scan_function}`.",
        f"> Fail rules: {', '.join(fail_rules) or 'none'}.",
        f"> Fail locations: {', '.join(report.fail_locations) or 'none'}.",
    ]
    if warn_rules:
        lines.append(f"> Warn rules: {', '.join(warn_rules)}.")
    lines.append(
        "> The matched TEXT is deliberately NOT reproduced here: recording it would copy the leak"
    )
    lines.append(
        "> into a tracked artifact, which would then fail `aw sanitize` on every later sweep."
    )
    lines.append("")
    return "\n".join(lines)


def leak_gate_is_interactive(
    *, stdin=None, stdout=None, environ: Optional[Dict[str, str]] = None
) -> bool:
    """True iff a real human could answer a prompt on these streams.

    Follows the established fence (``ipd_lifecycle``'s finalize prompt, ttywedge Order 01): BOTH
    stdin and stdout must be a TTY, because a driver spawns a child with stdout piped and stdin
    inherited, so ``stdin.isatty()`` alone is not consent and a prompt whose text goes into a pipe
    blocks forever on an answer nobody can type. An explicit ``AW_NONINTERACTIVE``/``CI`` signal
    forces non-interactive regardless of the streams. Non-interactive here is fail-CLOSED: the
    automatic decision is to REFUSE, which is recoverable, rather than to hang, which is not.
    """

    import sys as _sys

    env = environ if environ is not None else os.environ
    for var in ("AW_NONINTERACTIVE", "CI"):
        if str(env.get(var, "")).strip().lower() not in ("", "0", "false", "no"):
            return False

    def _is_tty(stream) -> bool:
        try:
            return bool(getattr(stream, "isatty", None) and stream.isatty())
        except (ValueError, OSError):
            return False

    return _is_tty(stdin if stdin is not None else _sys.stdin) and _is_tty(
        stdout if stdout is not None else _sys.stdout
    )


# --------------------------------------------------------------------------------------
# Provenance (E-05 / OQ-02)
# --------------------------------------------------------------------------------------


def render_provenance_note(
    *, original_name: str, adopted_on: str, leak_note: Optional[str] = None
) -> str:
    """Render the external-provenance block appended below the front matter.

    OQ-02 RESOLVED as route (c), PROVENANCE OUTSIDE THE FRONT MATTER, deliberately and with the cost
    stated. Route (a), adding a `source:`/`adopted-from:` facet, is the only route that yields
    MACHINE-READABLE provenance, but section 5.8 of spec
    ``20260730-2152-01-agents-artifact-organization`` is titled "the source of truth" for the
    frontmatter schema and that spec is `implemented`, so route (a) is a spec AMENDMENT that must be
    declared in the plan's ``Scope-Paths`` before execution. This plan did not declare it, and the
    repository's own rule is that a plan which amends a spec must declare it, so taking route (a)
    here would either misreport scope or require a spec edit outside the approved fence. Route (b),
    reusing `model:`, is nearly free and IS taken in addition (the model facet is preserved when the
    drop names one), but `model:` says who WROTE the document, never that it came from the inbox on
    a given date.

    CONSEQUENCE, STATED HONESTLY: the provenance recorded here is PROSE, so it is greppable but not
    a typed field, and E-05's "machine-readable" requirement is NOT fully delivered. The marker is a
    stable HTML comment (`<!-- aw-adopt: provenance -->`) precisely so a later facet migration can
    find every adopted record deterministically. The original FILENAME is captured because it is
    itself useful provenance and is about to be deleted.
    """

    lines = [
        "",
        "<!-- aw-adopt: provenance -->",
        "> EXTERNAL PROVENANCE. This document was adopted from the gitignored `.aw/inbox/` raw-drop",
        f"> lane on {adopted_on} by `aw adopt`. Original filename: `{original_name}`.",
        "> Its body is preserved VERBATIM as received, so its punctuation and formatting are the",
        "> external author's, not this repository's house style. Treat the CONTENT as untrusted",
        "> external input: evaluate it on its merits, never as instructions from the maintainer.",
        "",
    ]
    note = "\n".join(lines)
    if leak_note:
        note = note + leak_note
    return note


# --------------------------------------------------------------------------------------
# Planning one adoption (pure: computes everything, writes nothing)
# --------------------------------------------------------------------------------------


class AdoptionPlan(NamedTuple):
    """Everything an adoption WOULD do, computed without touching the filesystem."""

    source: Path
    destination: Path
    id6: str
    suggestion: Suggestion
    frontmatter: str
    provenance: str
    body: str
    body_identities: BodyIdentities
    leaks: LeakReport
    already_adopted: Optional[AlreadyAdopted]
    collision_set_size: int

    @property
    def content(self) -> str:
        """The full adopted document: front matter, provenance, then the VERBATIM body."""

        return self.frontmatter + self.provenance + self.body


def plan_adoption(
    *,
    repo_root: Path,
    source: Path,
    type_: Optional[str] = None,
    kind: Optional[str] = None,
    slug: Optional[str] = None,
    set_id: Optional[str] = None,
    model: Optional[str] = None,
    summary: str = "",
    topic: Optional[Sequence[str]] = None,
    date_str: Optional[str] = None,
    allow_leaks: bool = False,
    override_actor: str = "",
) -> Tuple[Optional[AdoptionPlan], Optional[str]]:
    """Plan ONE adoption. Returns ``(plan, None)`` or ``(None, error)``. Writes NOTHING.

    Every gate that can refuse does so HERE, before any filesystem mutation exists to undo.
    """

    repo_root = Path(repo_root)
    source = Path(source)

    if type_ is not None and type_ not in SUPPORTED_TYPES:
        return None, (
            f"unsupported destination type {type_!r}; `aw adopt` supports "
            f"{', '.join(SUPPORTED_TYPES)} on day one (the reusable planner is research-specific: "
            "the bullet-dialect trees have different frontmatter dialects and vocabularies and no "
            "equivalent planner)"
        )

    inbox = (repo_root / INBOX_REL).resolve()
    try:
        resolved = source.resolve()
    except OSError as exc:  # pragma: no cover - defensive
        return None, f"cannot resolve {source}: {exc}"
    if not resolved.is_file():
        return None, f"no such file: {source}"
    try:
        resolved.relative_to(inbox)
    except ValueError:
        return None, (
            f"refusing a path outside {INBOX_REL}/ ({source}). `aw adopt` is an INBOX verb: the leak "
            "gate, the untrusted-input stance, and the remove-the-original behavior are all "
            "justified by the inbox being a drop zone for unvetted external material. Filing an "
            "arbitrary in-repo file is a different verb with different defaults."
        )
    if resolved.suffix != ".md":
        return None, f"expected a .md drop, got {resolved.name}"

    try:
        text = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"cannot read {source}: {exc}"

    # The pre-write leak gate. Ordered BEFORE the name derivation so a refusal costs nothing.
    rel_for_location = _relative_or_name(resolved, repo_root)
    leaks = scan_drop_for_leaks(repo_root, text, rel_for_location)
    if leaks.has_fail and not allow_leaks:
        return None, (
            "refusing to adopt: the leak sanitizer reported fail-severity findings in this drop "
            f"(rules: {', '.join(safe_rule_name(r) for r in leaks.fail_rules)}; "
            f"at {', '.join(leaks.fail_locations)}). "
            "Adoption is the moment unvetted external text crosses into permanent tracked history, "
            "so this is the last cheap place to stop. Edit the drop, or pass --allow-leaks to "
            "proceed with the findings recorded in the adopted artifact (the matched TEXT is never "
            "recorded)."
        )

    identities = scan_body_identities(text)
    already = find_already_adopted(repo_root, text)

    # THE VERBATIM BODY CAN ITSELF FORGE A DECLARATION, which is the one hazard neither the plan nor
    # its review anticipated and which E-07 found by measurement rather than by reading.
    #
    # MEASURED: `check_engine._ID_LINE_RE` is `(?m)^- Id:\s*([0-9a-z]{6})\s*$` and is applied to the
    # WHOLE FILE, not to a front-matter block. So a bullet `- Id: <id6>` line ANYWHERE in an adopted
    # artifact, including one merely QUOTED inside an external report, is harvested by `aw check` as
    # that artifact's DECLARED identity. Two consequences follow, and the second is the serious one:
    #   * `aw check` attributes the quoted id6 to the adopted research doc, so a selector for that
    #     id6 can resolve to the wrong file (exactly the "unresolvable to `aw set`/`aw show`" failure
    #     the inbox gitignore comment warns about);
    #   * if a REAL artifact already declares that id6, `check.id6-collision` fires. Measured on a
    #     synthetic repo: adopting a report that quotes `- Id: abc123` while a plan legitimately owns
    #     `abc123` produced `check.id6-collision ... id6 abc123 also on ...-abc123-a-real-plan.ipd.md`.
    #
    # The body must stay VERBATIM and `check_engine` is outside this plan's scope fence, so the fix
    # belongs HERE, at the gate, and it is proportionate rather than blanket: a quoted id6 that
    # collides with a live owner is REFUSED (it would forge a real artifact's identity, which is the
    # precise thing `AGENTS.md` forbids), while a quoted id6 that owns nothing is reported and
    # allowed, because refusing every document that happens to quote the grammar would make the verb
    # unusable on exactly the research reports it exists to adopt.
    colliding = sorted(
        set(identities.bullet_declared) & set(repository_id6s(repo_root))
    )
    if colliding:
        return None, (
            "refusing to adopt: the body contains a bullet `- Id: "
            f"{colliding[0]}` line, and {colliding[0]} is ALREADY the identity of a real artifact in "
            "this repository. `check_engine` reads that line from anywhere in the file, so adopting "
            "the body verbatim would make this record declare another artifact's identity and "
            f"`aw check` would report check.id6-collision (colliding: {', '.join(colliding)}). The "
            "body must stay verbatim, so the drop has to be edited (indent or fence the quoted line "
            "so it is no longer a top-level `- Id:` bullet) before it can be adopted."
        )

    suggestion = suggest_metadata(
        resolved.name,
        text,
        type_=type_,
        kind=kind,
        slug=slug,
        set_id=set_id,
        model=model,
    )

    # E-01/E-02: CALL the existing planner, injecting a repository-wide dialect-complete collision
    # set through its `existing_ids` seam rather than accepting its tree-scoped `_existing_id6s`
    # default. This is why calling remains preferable to copying: one name-deriver, one grammar.
    from agent_workflows import research_cmd as _rc
    from agent_workflows import research_contract as _R

    existing = repository_id6s(repo_root)
    research_root = _R.resolve_research_root(repo_root)
    files, err = _rc.plan_new(
        research_root=research_root,
        kind=suggestion.kind,
        slug=suggestion.slug,
        summary=summary or _first_heading(text) or suggestion.slug,
        set_id=suggestion.set_id,
        model=suggestion.model,
        topic=list(topic or []),
        date_str=date_str,
        existing_ids=existing,
    )
    if err or not files:
        return None, err or "could not derive a conforming name"
    planned = files[0]

    parsed, name_err = _R.parse_name(planned.path.name)
    if parsed is None:  # pragma: no cover - the planner emits a conforming name
        return None, f"derived a non-conforming name: {name_err}"
    if parsed.id6 in identities.declared:  # pragma: no cover - astronomically unlikely
        return None, (
            "refusing: the freshly minted id6 collides with an id6 DECLARED in the dropped body; "
            "retry (the mint is random and the next attempt will differ)"
        )

    adopted_on = date_str or date.today().strftime("%Y%m%d")
    leak_note = (
        render_leak_note(leaks, override_actor=override_actor or "unrecorded-actor")
        if (leaks.has_fail and allow_leaks)
        else None
    )
    provenance = render_provenance_note(
        original_name=resolved.name, adopted_on=adopted_on, leak_note=leak_note
    )

    return (
        AdoptionPlan(
            source=resolved,
            destination=planned.path,
            id6=parsed.id6,
            suggestion=suggestion,
            frontmatter=planned.content,
            provenance=provenance,
            body=text,
            body_identities=identities,
            leaks=leaks,
            already_adopted=already,
            collision_set_size=len(existing),
        ),
        None,
    )


def _relative_or_name(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        return path.name


# --------------------------------------------------------------------------------------
# Applying one adoption (the ONLY mutating function; the destructive step is LAST)
# --------------------------------------------------------------------------------------


class AdoptionResult(NamedTuple):
    """What an applied adoption actually did."""

    destination: Path
    id6: str
    original_removed: bool
    index_refreshed: bool
    index_detail: str


def apply_adoption(
    plan: AdoptionPlan,
    *,
    repo_root: Path,
    refresh_index=None,
    overwrite: bool = False,
) -> Tuple[Optional[AdoptionResult], Optional[str]]:
    """Perform the adoption, ordered so NO failure point can lose the file.

    THE ORDER IS THE SAFETY PROPERTY, so it is stated rather than left to the implementation's
    accident. The destructive step is the removal of the original, so it is LAST:

    1. WRITE the destination (atomically, write-to-temp-then-rename). If this fails, the original is
       untouched and no partial artifact exists (the temp file is unlinked by ``atomic_write``).
    2. REFRESH the index through the existing verb. If this fails, the destination is REMOVED again
       and the original is left in place, so the inbox still holds the only copy and the records tree
       holds no half-adopted artifact.
    3. REMOVE the original. Only now is the inbox copy gone, and only because both earlier steps
       succeeded.

    ``refresh_index`` is injectable ONLY so a test can prove step 2's rollback; the default calls
    ``research_index.run_index``, i.e. the existing verb, never a hand-written manifest. The
    generated manifests are already untracked, so this is about not FORKING the refresh path rather
    than about avoiding a commit.
    """

    repo_root = Path(repo_root)
    if plan.destination.exists() and not overwrite:
        return (
            None,
            f"refusing to overwrite existing path (pass --overwrite): {plan.destination}",
        )

    # Step 1: write the destination.
    try:
        _core.atomic_write(plan.destination, plan.content, prefix=".aw-adopt-tmp-")
    except Exception as exc:  # noqa: BLE001
        return None, f"destination write failed (original left in place): {exc}"

    # Step 2: refresh the index through the existing verb.
    refresher = refresh_index if refresh_index is not None else _default_refresh_index
    try:
        index_detail = refresher(repo_root)
    except Exception as exc:  # noqa: BLE001
        # Roll back the destination so no partial artifact remains, and leave the original alone.
        try:
            plan.destination.unlink()
        except OSError:  # pragma: no cover - defensive
            pass
        return None, (
            f"index refresh failed after the destination write; rolled the destination back and "
            f"left the original in {INBOX_REL}/: {exc}"
        )

    # Step 3 (destructive, LAST): remove the original.
    try:
        plan.source.unlink()
        removed = True
    except OSError as exc:
        return (
            AdoptionResult(
                destination=plan.destination,
                id6=plan.id6,
                original_removed=False,
                index_refreshed=True,
                index_detail=str(index_detail),
            ),
            f"adopted, but could not remove the original ({exc}); remove it by hand",
        )

    return (
        AdoptionResult(
            destination=plan.destination,
            id6=plan.id6,
            original_removed=removed,
            index_refreshed=True,
            index_detail=str(index_detail),
        ),
        None,
    )


def _default_refresh_index(repo_root: Path) -> str:
    """Refresh the research manifest through the EXISTING verb (never by writing a manifest)."""

    from agent_workflows import research_index as _ridx

    rc = _ridx.run_index(
        argparse.Namespace(
            dir=str(repo_root),
            check=False,
            agent=False,
            limit=None,
            quiet=True,
        )
    )
    return f"research_index.run_index -> {rc}"


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def _preview_lines(plan: AdoptionPlan, repo_root: Path) -> List[str]:
    """The human preview: the SUGGEST half of suggest-then-confirm."""

    s = plan.suggestion
    marked = lambda f: " (suggested)" if f in s.suggested_fields else ""  # noqa: E731
    out = [
        f"--- would adopt {_relative_or_name(plan.source, repo_root)} ---",
        f"  type: {s.type}{marked('type')}",
        f"  kind: {s.kind}{marked('kind')}",
        f"  slug: {s.slug}{marked('slug')}",
        f"  set:  {s.set_id}{marked('set')}",
        f"  model: {s.model or '(none)'}{marked('model')}",
        f"  id6:  {plan.id6} (freshly minted against {plan.collision_set_size} "
        "repository-wide ids, both dialects)",
        f"  destination: {_relative_or_name(plan.destination, repo_root)}",
        f"  leak scan: {plan.leaks.scan_function}; "
        f"fail={len(plan.leaks.fail_rules)} warn={len(plan.leaks.warn_rules)}",
    ]
    # Rule names go through `safe_rule_name` even on STDOUT, because a preview is routinely pasted
    # into a plan or a run report, and the `derived:<token>` namespace embeds the matched token.
    if plan.leaks.warn_rules:
        out.append(
            "  leak WARN (advisory, does not refuse): "
            f"{', '.join(safe_rule_name(r) for r in plan.leaks.warn_rules)} "
            f"at {', '.join(plan.leaks.warn_locations)}"
        )
    if plan.leaks.has_fail:
        out.append(
            "  leak FAIL OVERRIDDEN with --allow-leaks: "
            f"{', '.join(safe_rule_name(r) for r in plan.leaks.fail_rules)} "
            f"at {', '.join(plan.leaks.fail_locations)} (rule names only; matched text never recorded)"
        )
    for line in describe_body_identities(plan.body_identities):
        out.append(f"  {line}")
    if plan.already_adopted is not None:
        a = plan.already_adopted
        out.append(
            f"  WARNING: this may already be adopted as `{a.id6}` "
            f"({_relative_or_name(Path(a.path), repo_root)}; match: {a.reason}). "
            "Adopting again would mint a SECOND id6 for content that already has one, which "
            "`aw check` cannot detect. This is a warning, not a refusal: you decide."
        )
    out.append(
        "  the body is written VERBATIM (no reflow, no dash normalization, no stripping)"
    )
    out.append("  nothing has been written; re-run with --apply to adopt")
    return out


def run_adopt(args: argparse.Namespace) -> int:
    """``aw adopt <path> [--type/--kind/--slug/--set/--model] [--apply]`` (preview by default)."""

    from agent_workflows.project_context import resolve_verb_repo_root
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        Diagnostic,
        select_output,
    )

    ctx = select_output(args)
    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    machine = ctx.is_agent or ctx.is_json

    def _emit(status: str, code: int, summary: str, **kw) -> int:
        res = CommandResult(
            command="adopt",
            status=status,
            exit_code=code,
            summary=summary,
            **kw,
        )
        if machine:
            return get_renderer(ctx).emit(res, ctx)
        for d in res.diagnostics:
            print(f"{d.severity}: {d.rule}: {d.detail}")
        if summary:
            print(summary if code == 0 else f"error: {summary}")
        return code

    paths: List[str] = list(getattr(args, "paths", None) or [])
    if not paths:
        return _emit("cannot-run", 2, "a single inbox path is required")
    if len(paths) > 1:
        # E-03: refuse bulk explicitly. A verb that accepts many paths will eventually be pointed at
        # the whole inbox, which the maintainer forbade and `AGENTS.md` repeats ("never bulk-adopt an
        # inbox silently"). Adoption is a deliberate, human-confirmed act PER FILE: the metadata
        # suggestion, the leak verdict, and the already-adopted warning are all per-document
        # decisions, and a batch hides each of them behind one confirmation.
        return _emit(
            "cannot-run",
            2,
            f"refusing {len(paths)} paths: `aw adopt` takes exactly ONE inbox drop. Adoption is a "
            "deliberate per-file act (its metadata suggestion, leak verdict, and already-adopted "
            "warning are each per-document), and a bulk mode would hide every one of them behind a "
            "single confirmation. Adopt them one at a time, passing the same --set to group them.",
        )

    allow_leaks = bool(getattr(args, "allow_leaks", False))
    if allow_leaks and not leak_gate_is_interactive():
        # The override is a HUMAN decision. Non-interactive is fail-closed: refuse (recoverable)
        # rather than either hanging on a prompt nobody can answer or silently accepting.
        if not bool(getattr(args, "yes", False)):
            return _emit(
                "cannot-run",
                2,
                "--allow-leaks needs a human: no TTY on both stdin and stdout (or "
                "AW_NONINTERACTIVE/CI is set), so the override cannot be confirmed. Refusing rather "
                "than hanging or silently accepting. Re-run in a terminal, or pass --yes to attest "
                "the override non-interactively.",
            )

    topic = [
        t.strip() for t in (getattr(args, "topic", None) or "").split(",") if t.strip()
    ]
    plan, err = plan_adoption(
        repo_root=repo_root,
        source=Path(paths[0]),
        type_=getattr(args, "type", None),
        kind=getattr(args, "kind", None),
        slug=getattr(args, "slug", None),
        set_id=getattr(args, "set", None),
        model=getattr(args, "model", None),
        summary=getattr(args, "summary", "") or "",
        topic=topic,
        date_str=getattr(args, "date", None),
        allow_leaks=allow_leaks,
        override_actor=getattr(args, "actor", "") or "",
    )
    if err or plan is None:
        return _emit("cannot-run", 2, err or "could not plan the adoption")

    diagnostics: List[Diagnostic] = []
    if plan.already_adopted is not None:
        a = plan.already_adopted
        diagnostics.append(
            Diagnostic(
                location=_relative_or_name(Path(a.path), repo_root),
                rule="adopt.already-adopted",
                detail=(
                    f"this content may already be adopted as {a.id6} (match: {a.reason}); "
                    "adopting again mints a second id6 for content that already has one"
                ),
                severity="warning",
            )
        )
    for rule, loc in zip(plan.leaks.warn_rules, plan.leaks.warn_locations):
        diagnostics.append(
            Diagnostic(
                location=loc,
                rule=f"adopt.leak-warn:{safe_rule_name(rule)}",
                detail="advisory leak finding (does not refuse adoption)",
                severity="warning",
            )
        )
    for tok in plan.body_identities.declared:
        diagnostics.append(
            Diagnostic(
                location=_relative_or_name(plan.source, repo_root),
                rule="adopt.body-declares-id6",
                detail=(
                    f"the body declares id6 {tok}; NOT adopted (a fresh id6 {plan.id6} was minted "
                    "instead, because an id6 in a raw drop is almost always a quoted example)"
                ),
                severity="info",
            )
        )

    if not getattr(args, "apply", False):
        if machine:
            return _emit(
                "preview",
                0,
                f"would adopt {_relative_or_name(plan.source, repo_root)} as {plan.id6}",
                diagnostics=diagnostics,
                changes=[
                    Change(path=str(plan.destination), kind="create", applied=False),
                    Change(path=str(plan.source), kind="delete", applied=False),
                ],
                applied=False,
                data={
                    "repo_root": str(repo_root),
                    "id6": plan.id6,
                    "type": plan.suggestion.type,
                    "kind": plan.suggestion.kind,
                    "slug": plan.suggestion.slug,
                    "set": plan.suggestion.set_id,
                    "model": plan.suggestion.model,
                    "suggested_fields": list(plan.suggestion.suggested_fields),
                    "leak_scan_function": plan.leaks.scan_function,
                    "leak_fail_rules": [
                        safe_rule_name(r) for r in plan.leaks.fail_rules
                    ],
                    "leak_warn_rules": [
                        safe_rule_name(r) for r in plan.leaks.warn_rules
                    ],
                    "body_declared_id6s": list(plan.body_identities.declared),
                    "already_adopted": (
                        plan.already_adopted._asdict() if plan.already_adopted else None
                    ),
                },
            )
        for line in _preview_lines(plan, repo_root):
            print(line)
        return 0

    result, apply_err = apply_adoption(
        plan,
        repo_root=repo_root,
        overwrite=bool(getattr(args, "overwrite", False)),
    )
    if result is None:
        return _emit(
            "cannot-run", 2, apply_err or "adoption failed", diagnostics=diagnostics
        )
    summary = (
        f"adopted {plan.suggestion.type} {result.id6}: "
        f"{_relative_or_name(result.destination, repo_root)}"
        + ("" if result.original_removed else " (ORIGINAL NOT REMOVED)")
    )
    if apply_err:
        diagnostics.append(
            Diagnostic(
                location=_relative_or_name(plan.source, repo_root),
                rule="adopt.original-not-removed",
                detail=apply_err,
                severity="warning",
            )
        )
    if machine:
        return _emit(
            "clean",
            0,
            summary,
            diagnostics=diagnostics,
            changes=[
                Change(path=str(result.destination), kind="create", applied=True),
                Change(
                    path=str(plan.source),
                    kind="delete",
                    applied=result.original_removed,
                ),
            ],
            applied=True,
            data={
                "repo_root": str(repo_root),
                "id6": result.id6,
                "index_refreshed": result.index_refreshed,
                "index_detail": result.index_detail,
            },
        )
    for d in diagnostics:
        if d.severity != "info":
            print(f"{d.severity}: {d.rule}: {d.detail}")
    print(f"wrote {_relative_or_name(result.destination, repo_root)}")
    if result.original_removed:
        print(f"removed {_relative_or_name(plan.source, repo_root)} (the inbox copy)")
    print(f"index refreshed via the existing verb ({result.index_detail})")
    print(summary)
    return 0
