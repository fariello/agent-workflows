"""Unified status transition engine for plans, specs, prompts, backlog, and more.

Supports natural command surface:
  aw set <status> <id6|setid|fname>...
  aw set <type> <status> <id6|setid|fname>...
  aw ipd set <status> <id6|setid|fname>...
  aw spec set <status> <id6|setid|fname>...
  aw specs set <status> <id6|setid|fname>...
  aw backlog set <status> <id6|setid|fname>...

Enforces:
- Atomic pre-flight check: all selectors must resolve, or no changes are made.
- Strict type scoping: when a type is specified, any target resolving to another type is an error.
- Valid status transition per artifact type.
- Clean front-matter + workflow history + directory disposition updates.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import backlog as _backlog_mod
from agent_workflows import ipd_schema as _ipd_schema
from agent_workflows import lifecycle_dirs as _LD
from agent_workflows import lifecycle_style as _LS
from agent_workflows import plans as _plans_mod
from agent_workflows import research_contract as _research_contract
from agent_workflows import selectors as _sel
from agent_workflows.result_types import Change
from agent_workflows.term import Term

# Recognized status sets per artifact type
TYPE_STATUSES: dict[str, set[str]] = {
    "plans": {
        "draft",
        "to-review",
        "reviewed",
        "approved",
        "auto-approved",
        "executed",
        "superseded",
        "not-executed",
        "reusable",
        "done",  # alias for executed
        "pending",  # alias for to-review
    },
    # prompts Order 01 (7z3ovv) E-01: DERIVED from `lifecycle_dirs.LIFECYCLE_SUBDIRS["prompts"]`, never
    # re-listed, plus the retained `done` alias (normalize_target_status). A stale copy previously
    # accepted six non-bucket statuses that write no valid bucket (bug um8ikz).
    "prompts": set(_LD.LIFECYCLE_SUBDIRS["prompts"]) | {"done"},
    # Set placelib (d1lo52) E-05: DERIVED from `lifecycle_dirs.LIFECYCLE_SUBDIRS["specs"]`, never re-listed.
    "specs": set(_LD.LIFECYCLE_SUBDIRS["specs"]),
    # bklgrad Order 01 (v58bvy) E-01: DERIVED from `backlog.STATUSES`, never re-listed. This copy is
    # what refused `aw backlog set graduated` after the vocabulary grew, so it is now identical by
    # construction (GUIDING_PRINCIPLES P8) and a future status cannot desync the setter.
    "backlog": set(_backlog_mod.STATUSES),
    "releases": {
        "planned",
        "blocked",
        "shipped",
    },
    # resstatus Order 01 (5e3nj2) E-09: DERIVED from `research_contract.HOT_STATUSES`, never re-listed.
    "research": set(_research_contract.HOT_STATUSES),
    "other": {
        "draft",
        "to-review",
        "reviewed",
        "approved",
        "auto-approved",
        "open",
        "active",
        "done",
        "parked",
        "superseded",
        "not-executed",
        "executed",
        "pending",
    },
}

# Type aliases / singular mappings to canonical plural
TYPE_ALIASES: dict[str, str] = {
    "ipd": "plans",
    "ipds": "plans",
    "plan": "plans",
    "plans": "plans",
    "spec": "specs",
    "specs": "specs",
    "prompt": "prompts",
    "prompts": "prompts",
    "backlog": "backlog",
    "release": "releases",
    "releases": "releases",
    "research": "research",
    "walkthrough": "walkthroughs",
    "walkthroughs": "walkthroughs",
    "roadmap": "roadmaps",
    "roadmaps": "roadmaps",
    "other": "other",
    "others": "other",
    "misc": "other",
}

# Regexes for front-matter inspection and manipulation
_ID_RE = re.compile(r"^-\s*Id:\s*([0-9a-z]{6})\s*$", re.MULTILINE)
_STATUS_RE = re.compile(r"^-\s*Status:\s*(\S+)\s*$", re.MULTILINE)
_SET_RE = re.compile(r"^-\s*Set:\s*(.+?)\s*$", re.MULTILINE)
_HISTORY_HDR_RE = re.compile(r"^##\s*Workflow history\s*$", re.MULTILINE)
_GATE_KIND_RE = re.compile(r"^-\s*Gate-Kind:\s*(\S+)\s*$", re.MULTILINE)
_GATE_REF_RE = re.compile(r"^-\s*Gate-Ref:\s*(.+?)\s*$", re.MULTILINE)
_GATE_SUMMARY_RE = re.compile(r"^-\s*Gate-Summary:\s*(.+?)\s*$", re.MULTILINE)

# The ONE status per record type in which a typed `Gate-Kind`/`Gate-Ref` pair is valid. A gate is
# valid IFF the record sits in that status, so ANY transition to a different status must clear it,
# for every gate-carrying tree and not just specs (bug `43p53n`). Plans and prompts carry no gate
# fields, so they are absent here and no clearing applies to them.
_GATE_STATUS_BY_TYPE: dict[str, str] = {
    "specs": "deferred",
    "backlog": "blocked",
}


@dataclass
class ArtifactRecord:
    path: Path
    record_type: str
    id6: str | None
    set_id: str | None
    status: str | None
    raw_text: str


def canonical_type(type_token: str | None) -> str | None:
    """Normalize type token to canonical plural form, or None if not an artifact type."""
    if not type_token:
        return None
    token = type_token.strip().lower()
    return TYPE_ALIASES.get(token, None)


def detect_artifact_type(path: Path, repo_root: Path) -> str | None:
    """Detect the record type of an artifact file based on path facets and location.

    The facet->type mapping is derived from the single naming authority's ``TYPE_FACET`` (IPD
    o6b8l3), so there is one facet-enum definition; only the ``comms`` facet is intentionally not
    resolved to a status-settable type here (no comms status flow)."""
    name = path.name
    for _type, _facet in _naming.TYPE_FACET.items():
        if _type == "comms":
            continue
        if name.endswith(f".{_facet}.md"):
            return _type

    # Location-based detection
    rel_parts = path.resolve().parts
    for i, part in enumerate(rel_parts):
        if part in ("records", ".agents", ".aw") and i + 1 < len(rel_parts):
            next_part = rel_parts[i + 1]
            if next_part in TYPE_ALIASES:
                return TYPE_ALIASES[next_part]
            if next_part == "docs" and i + 2 < len(rel_parts):
                doc_part = rel_parts[i + 2]
                if doc_part in TYPE_ALIASES:
                    return TYPE_ALIASES[doc_part]

    # Fallback to content check
    try:
        text = path.read_text(encoding="utf-8")
        if text.startswith("# IPD:"):
            return "plans"
        if "- Kind: child" in text or "- Kind: orchestrator" in text:
            return "plans"
    except OSError:
        pass

    # Fallback for any other record in .aw/records or .agents
    with contextlib.suppress(OSError):
        resolved = path.resolve()
        for base in (
            (repo_root / ".aw" / "records").resolve(),
            (repo_root / ".agents").resolve(),
        ):
            if base.is_dir() and (base == resolved or base in resolved.parents):
                try:
                    rel_parts = set(resolved.relative_to(base).parts)
                    if any(ex in _sel.EXCLUDED_RECORD_DIRS for ex in rel_parts):
                        return None
                except ValueError:
                    pass
                return "other"

    return None


def read_artifact_record(path: Path, repo_root: Path) -> ArtifactRecord | None:
    """Read and parse an artifact record from disk."""
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    rtype = detect_artifact_type(path, repo_root)
    if not rtype:
        return None

    meta = _sel.metadata_region(text)

    id_match = _ID_RE.search(meta)
    id6 = id_match.group(1) if id_match else None
    if not id6:
        yaml_id = re.search(r"(?m)^id:\s*([0-9a-z]{6})\s*$", meta)
        if yaml_id:
            id6 = yaml_id.group(1)

    status_match = _STATUS_RE.search(meta)
    status = status_match.group(1) if status_match else None
    if not status:
        yaml_status = re.search(r"(?m)^status:\s*(\S+)\s*$", meta)
        if yaml_status:
            status = yaml_status.group(1)
    if not status and rtype == "prompts":
        from agent_workflows import prompts as _prompts

        status = _prompts.read_metadata_status(text)

    set_match = _SET_RE.search(meta)
    set_id = None
    if set_match:
        raw_set = set_match.group(1).strip()
        set_id = raw_set.split("(")[0].strip().split()[0] if raw_set else None

    return ArtifactRecord(
        path=path,
        record_type=rtype,
        id6=id6,
        set_id=set_id,
        status=status,
        raw_text=text,
    )


def inventory_all_artifacts(
    repo_root: Path, scoped_type: str | None = None
) -> list[ArtifactRecord]:
    """Scan and index all non-index *.md artifacts in the repository across all types."""
    records: list[ArtifactRecord] = []
    seen: set[str] = set()

    types = (
        (scoped_type,)
        if scoped_type
        else (
            "plans",
            "specs",
            "prompts",
            "backlog",
            "releases",
            "research",
            "walkthroughs",
            "roadmaps",
            "other",
        )
    )

    for rtype in types:
        for d in _sel.record_dirs(repo_root, rtype):
            if not d.is_dir():
                continue
            for p in d.rglob("*.md"):
                if p.name in _sel._SKIP_NAMES:
                    continue
                rp = p.as_posix()
                if rp in seen:
                    continue
                seen.add(rp)
                rec = read_artifact_record(p, repo_root)
                if rec:
                    records.append(rec)
    return records


def match_selector(
    selector: str,
    all_records: list[ArtifactRecord],
    repo_root: Path,
    scoped_type: str | None = None,
) -> list[ArtifactRecord]:
    """Match a single selector token against the inventory (IPD laykok E-03: thin shim over the ONE
    unified resolver ``selectors.resolve``).

    Resolution covers the full vocabulary with one documented precedence: direct path -> exact id6
    -> exact setid -> exact status -> exact stem -> filename substring. This ADDS the previously
    missing status and bare-stem kinds to `aw set` while preserving every prior successful
    resolution (path/id6/setid/substring). The resolved paths are mapped back to `ArtifactRecord`s
    (from ``all_records`` when known, else read on demand) so the caller's record-based flow is
    unchanged.

    TYPE SAFETY IS DELIVERED BY TWO INDEPENDENT, NON-REDUNDANT NARROWING SITES (IPD `jw6cm3`).
    Neither site is redundant and removing either is a cross-type defect. They cover disjoint
    selector kinds:

      1. The FAST-PATH candidate filter (``cands = [r for r in all_records if not target_type or r.record_type == target_type]``)
         is the ONLY type guard for the ``id6`` and ``setid`` kinds, which return early and never
         reach the resolver. Removing it permits foreign-type records through (e.g. a plans-scoped
         backlog id6 returns a backlog record, degrading refusal messages from "No plans artifact
         matched" to caller-level wrong-type errors).

      2. The RESOLVER narrowing (``if scoped_type: record_types = (canonical,)``) is the ONLY type
         guard for the ``status``, ``stem``, and ``substring`` kinds, which the fast path cannot
         see. Removing it allows cross-type resolution for status tokens, foreign stems, and
         shared substrings.

    DIRECT PATH EXEMPTION: Neither site guards a direct PATH. ``selectors.resolve``'s first
    precedence rule matches an existing file regardless of the type requested, and the record's
    type is then read off the real path, so ``match_selector(<a plan path>, scoped_type="specs")``
    legitimately returns a ``plans`` record. Callers that must not act across types therefore need
    their own post-resolution type check; ``run_set_command``'s ``Type mismatch`` refusal is that
    check, and it is the only guard on this case.
    """
    tok = selector.strip()
    if not tok:
        return []

    # Fast path: exact id6 or setid from all_records before falling back to filesystem walk
    cand = Path(tok)
    cand_is_path = cand.is_file() or (
        not cand.is_absolute() and (repo_root / tok).is_file()
    )
    if not cand_is_path:
        target_type = (
            canonical_type(scoped_type) or scoped_type if scoped_type else None
        )
        # FAST-PATH TYPE GUARD (IPD `jw6cm3` E-05): guards the `id6` and `setid` kinds.
        # These return early and never reach the resolver below, making this filter their ONLY
        # type guard. Removing it leaks foreign types: a plans-scoped backlog id6 returns a
        # backlog record (measured: degrading refusal diagnostics from "No plans artifact matched"
        # to a wrong-type error), and a plans-scoped setid returns foreign-type records.
        # An id6 test alone fails under both mutations and cannot isolate this site; companion
        # setid is what isolates it.
        # NOTE: This guard is INVISIBLE when callers pass a pre-narrowed record list
        # (`inventory_all_artifacts(..., scoped_type=...)`), but production callers such as
        # `run_dependencies_set_command` pass an unnarrowed inventory, making this guard
        # reachable and load-bearing in production. Tests must pass an unnarrowed list to exercise it.
        # Correctness is the reason to keep this filter; DO NOT DELETE IT AS DEAD CODE OR REDUNDANT.
        cands = [
            r for r in all_records if not target_type or r.record_type == target_type
        ]
        if _core.ID6_RE.match(tok):
            id6_matches = [r for r in cands if r.id6 == tok]
            if id6_matches:
                return id6_matches
        set_matches = [r for r in cands if r.set_id == tok]
        if set_matches:
            return set_matches

    from agent_workflows import selectors as _sel

    # RESOLVER TYPE GUARD (IPD `jw6cm3` E-05): guards the `status`, `stem`, and `substring` kinds.
    # The fast path above only inspects `id6` and `set_id`, so it cannot guard these three kinds;
    # restricting `record_types` to `(canonical,)` here is their ONLY type guard. Removing it
    # leaks foreign types when resolving status tokens, filename stems, or substring matches.
    # DO NOT DELETE OR DISABLE THIS BRANCH.
    if scoped_type:
        canonical = canonical_type(scoped_type) or scoped_type
        record_types = (canonical,)
    else:
        record_types = (
            "plans",
            "specs",
            "prompts",
            "backlog",
            "releases",
            "research",
            "walkthroughs",
            "roadmaps",
            "other",
        )
    matched_paths: dict[str, Path] = {}
    for rt in record_types:
        res = _sel.resolve(repo_root, rt, tok)
        for p in res.paths:
            matched_paths[p.as_posix()] = p

    if not matched_paths:
        return []

    by_path = {r.path.as_posix(): r for r in all_records}
    out: list[ArtifactRecord] = []
    seen: set[str] = set()
    for key in sorted(matched_paths):
        if key in seen:
            continue
        seen.add(key)
        rec = by_path.get(key)
        if rec is None:
            rec = read_artifact_record(matched_paths[key], repo_root)
        if rec:
            out.append(rec)
    return out


#: The `lifecycle_style` FAMILY for each record type this setter writes (spec `uonrjg` Sections 6.1
#: to 6.6, R10.3). Named as an explicit map rather than passed through, because the two vocabularies
#: are NOT everywhere identical and a bare pass-through would raise `UnknownFamily` from a read-only
#: echo line: `other` is this module's catch-all bucket and is not a lifecycle family at all, and
#: `comms`/`walkthroughs`/`roadmaps` reach `detect_artifact_type` without owning a plan-style
#: lifecycle. A type ABSENT here renders no lifecycle marker, which is Section 6.7's answer, and is
#: deliberately NOT the same thing as `unknown`.
_LIFECYCLE_FAMILY_BY_TYPE: dict[str, str] = {
    "plans": _LS.FAMILY_PLANS,
    "specs": _LS.FAMILY_SPECS,
    "prompts": _LS.FAMILY_PROMPTS,
    "backlog": _LS.FAMILY_BACKLOG,
    "research": _LS.FAMILY_RESEARCH,
    "releases": _LS.FAMILY_RELEASES,
    "walkthroughs": _LS.FAMILY_WALKTHROUGHS,
    "roadmaps": _LS.FAMILY_ROADMAPS,
}


def _resolve_record_lifecycle(record_type: str, native_status: str) -> _LS.Resolved:
    """Resolve one record's lifecycle presentation through the SHARED resolver (spec R10.3).

    THE ONE LIFECYCLE RESOLUTION PATH IN THIS MODULE, mirroring `attention._resolve_item_lifecycle`
    deliberately: the same status must render identically in `aw set`, `aw find` and `aw attention`,
    and the cheapest guarantee of that is one resolver reached the same way from each.

    A RECORD TYPE WITH NO LIFECYCLE FAMILY RESOLVES `unknown` RATHER THAN RAISING.
    `term.resolve_lifecycle` raises `UnknownFamily` for a family it has no policy for, and this is an
    echo line printed AFTER a successful write, so a raise here would turn a completed transition
    into a traceback. R10.4 makes the `unknown`-versus-`none` distinction load-bearing, so this
    returns `unknown` plus a diagnostic (a status this view could not classify) and never a silent
    parked gray.
    """

    family = _LIFECYCLE_FAMILY_BY_TYPE.get(record_type)
    if family is None:
        return _LS.Resolved(
            stage=_LS.UNKNOWN,
            style=_LS.style_for(_LS.UNKNOWN),
            family=record_type,
            native_status=native_status or None,
            diagnostic=f"record type {record_type!r} is not a lifecycle family",
        )
    from agent_workflows import term as _T

    return _T.resolve_lifecycle(family, native_status)


def _format_status_transition_line(
    rec: ArtifactRecord,
    dest_path: Path,
    norm_stat: str,
    term: Term,
    args: argparse.Namespace | None = None,
    dry_run: bool = False,
    changed: bool = True,
) -> str:
    from agent_workflows import attention as _att

    old_status = (rec.status or "draft").strip().lower()
    norm_stat_clean = norm_stat.strip().lower()
    arrow = term.glyph("arrow")

    if not changed or old_status == norm_stat_clean:
        # `unchanged` IS NOT A LIFECYCLE STATUS AND MUST NOT BE ROUTED THROUGH THE RESOLVER
        # (plan `9zvl2w` E-02, spec `uonrjg` R10.3). It is a no-op OUTCOME word: it appears in no
        # Section 6 or 7 table, it greps to zero in the spec, and it is not a value any artifact's
        # `- Status:` can hold. Sent through `resolve_lifecycle` it would land on criterion A20's
        # unknown path and print `?` for a SUCCESSFUL no-op. Convert by VALUE, not by call site: the
        # two calls below render `rec.status` and `norm_stat`, which ARE lifecycle, and this one does
        # not. Its current gray (245 via `term.ROLE_COLOR_256`) is deliberately kept.
        status_part = (
            term.status_256("unchanged")
            if getattr(term, "color", False)
            else "unchanged"
        )
    else:
        # THE SHARED RESOLVER, for both ends of the transition (R10.3). The glyph precedes the
        # transition pair so its referent is the NEW state, which is what the line reports; Section
        # 9.1 requires the glyph to immediately precede either the id6 or the status word.
        old_resolved = _resolve_record_lifecycle(rec.record_type, rec.status or "draft")
        new_resolved = _resolve_record_lifecycle(rec.record_type, norm_stat)
        old_styled = term.style_lifecycle_text(rec.status or "draft", old_resolved)
        new_styled = term.style_lifecycle_text(norm_stat, new_resolved)
        new_marker = term.format_lifecycle_marker(new_resolved, width=2)
        status_part = f"{old_styled} {arrow} {new_marker} {new_styled}"

    m_prio = re.search(r"(?m)^-\s*Priority:\s*(\S+)", rec.raw_text)
    priority = m_prio.group(1).lower() if m_prio else None

    br_arg = getattr(args, "blocks_release", None) if args else None
    if br_arg:
        blocks_release = None if br_arg == "-" else br_arg
    else:
        # Note: the previous unanchored regex r"(?m)^-\s*Blocks-Release:\s*(\S+)" was missing the
        # '$' anchor and unbounded to metadata region, diverging from releases.py.
        blocks_release = _sel.read_front_matter_blocks_release(rec.raw_text)

    m_gk = re.search(r"(?m)^-\s*Gate-Kind:\s*(\S+)", rec.raw_text)
    m_gr = re.search(r"(?m)^-\s*Gate-Ref:\s*(\S+)", rec.raw_text)
    gate = f"{m_gk.group(1)}:{m_gr.group(1)}" if (m_gk and m_gr) else None

    prio_txt = ""
    if priority:
        pcode = {"high": 196, "medium": 214, "low": 244}.get(priority, 244)
        prio_txt = "  " + (
            term.color256(f"[{priority}]", pcode, bold=True)
            if getattr(term, "color", False)
            else f"[{priority}]"
        )

    blocking_txt = ""
    if blocks_release:
        blocking_txt = "  " + (
            term.color256("[blocking]", 196, bold=True)
            if getattr(term, "color", False)
            else "[blocking]"
        )

    gate_txt = ""
    if gate:
        gate_txt = "  " + (
            term.color256(f"[{gate}]", 203, bold=True)
            if getattr(term, "color", False)
            else f"[{gate}]"
        )

    lead = ">  " if blocks_release else "   "
    # THE ARTIFACT TYPE CARRIES NO COLOR (criterion A10; Section 9.1: "The artifact type and title do
    # not inherit lifecycle color"; Section 11 item 5 limits color to glyph, id6 and status). It was
    # painted `attention._TREE_COLOR_256` bold, the SAME violation plan `f9t5hz` removed from
    # `attention.py`'s rows, replicated here. Section 11 item 5's "existing independent convention"
    # exemption does NOT stretch to cover it: that convention is for the tree SEGMENT OF A PATH
    # (`attention._colorize_tree_segment`), where one colored directory component identifies the tree
    # inside a longer string; a bare type word in a row is not a path, and coloring it made A10
    # untestable on this view.
    type_word = _att._SINGULAR_TYPE.get(rec.record_type, rec.record_type)
    type_prefix = type_word + (" " * max(0, 10 - len(type_word))) + "  "
    stem = _att._identity_stem(str(dest_path))
    dry_suffix = "  (dry-run)" if dry_run else ""

    return f"- {lead}{type_prefix}{stem}{prio_txt}{blocking_txt}{gate_txt}  {status_part}{dry_suffix}"


def normalize_target_status(raw_status: str, record_type: str) -> str:
    """Normalize status aliases according to record type."""
    norm = raw_status.strip().lower()
    if record_type in ("plans", "prompts"):
        if norm == "done":
            return "executed"
    if record_type == "plans":
        if norm == "pending":
            return "to-review"
    if record_type == "research":
        res = _research_contract.normalize_status(norm)
        if res.value:
            return res.value
    return norm


def _repo_root_of(artifact_path: Path) -> Path:
    """Walk up from an artifact to its repo root, falling back to cwd.

    The FALLBACK ONLY, for a direct caller of `validate_transition_allowed` that does not pass the
    already-resolved root. Same marker set and same shape as `specs._repo_root_of`, kept local rather
    than imported so this module gains no dependency on the specs verb for one path walk.
    """
    p = artifact_path.resolve()
    for anc in [p] + list(p.parents):
        if (
            (anc / ".aw").is_dir()
            or (anc / ".agents").is_dir()
            or (anc / ".git").exists()
        ):
            return anc
    return Path.cwd()


def plan_priority_work_kind_problems(
    text: str, *, priority: str | None = None, work_kind: str | None = None
) -> list[str]:
    """Why a plan's Priority / Work-Kind do not clear the ready-to-execute tier. Empty means clear.

    planprio lkexaw E-11. ``priority``/``work_kind`` are values about to be written in the same call;
    they take precedence over the file's. Judged by the SAME ``ipd_schema.parse_plan_priority`` /
    ``parse_plan_work_kind`` the lint gate uses, so the setter and the gate cannot disagree about what
    is decided. ``grandfathered`` passes here exactly as it passes (advisory-satisfied) at the gate.
    """
    # Read the metadata region the SAME forgiving way the setter reads `- Status:` (any `- Field:`
    # bullet above the first `## ` heading), not through `ipd_lint.parse`, which requires the H1 first.
    # A stricter reader here would report "missing" for a field the setter can plainly see.
    head = re.split(r"(?m)^## ", text, maxsplit=1)[0]
    fields: dict[str, str] = {}
    for m in re.finditer(r"(?m)^- ([A-Za-z][A-Za-z-]*):[ \t]*(.*?)[ \t]*$", head):
        fields.setdefault(m.group(1), m.group(2))
    problems: list[str] = []
    for name, override, parser in (
        (_ipd_schema.META_PRIORITY, priority, _ipd_schema.parse_plan_priority),
        (_ipd_schema.META_WORK_KIND, work_kind, _ipd_schema.parse_plan_work_kind),
    ):
        value = override if override is not None else fields.get(name)
        if value is None:
            problems.append(f"{name} is missing")
            continue
        _v, _grand, err = parser(value)
        if err:
            problems.append(err)
    return problems


def validate_transition_allowed(
    rec: ArtifactRecord,
    target_status: str,
    args: argparse.Namespace,
    repo_root: Path | None = None,
) -> tuple[bool, str | None]:
    """Validate that the target status is valid and permitted for the record.

    ``repo_root`` is OPTIONAL and defaults to walking up from ``rec.path``, so every existing caller
    keeps working unchanged. It exists for the apprvguard d7bnhc approval gate below, which must
    locate the typed review artifacts under ``.aw/records/reviews/``; the caller in
    ``run_set_command`` already holds the resolved root and passes it, and the walk-up is only the
    fallback for a direct caller that does not.
    """
    norm_status = normalize_target_status(target_status, rec.record_type)
    valid_statuses = TYPE_STATUSES.get(rec.record_type, set())

    # relexempt ghna7l E-05: validate release exemption flags
    _rel_exempt_kind = getattr(args, "release_exempt_kind", None)
    _rel_exempt_ref = getattr(args, "release_exempt_ref", None)
    if _rel_exempt_kind is not None or _rel_exempt_ref is not None:
        from agent_workflows import backlog as _backlog

        _exempt_err = _backlog.validate_release_exempt_flags(
            "aw set", _rel_exempt_kind, _rel_exempt_ref
        )
        if _exempt_err:
            return False, _exempt_err
    # resstatus Order 01 (5e3nj2) E-09: research-specific validation
    if rec.record_type == "research":
        if (
            norm_status in _research_contract.SHARDED_STATUSES
            or target_status.strip().lower() in _research_contract.SHARDED_STATUSES
        ):
            target_id = rec.id6 or rec.path.name
            return (
                False,
                f"Setting research status to '{target_status}' is not supported via aw set; use 'aw research promote {target_id} --to {target_status}' instead.",
            )
        # resvocab Order 01 (4a8yws) E-02: refuse hot status when record sits in cold shard
        if norm_status in _research_contract.HOT_STATUSES:
            eff_root = repo_root if repo_root is not None else _repo_root_of(rec.path)
            rec_path = rec.path if rec.path.is_absolute() else (eff_root / rec.path)
            res_root = _research_contract.resolve_research_root(eff_root)
            try:
                rel = rec_path.resolve().relative_to(res_root.resolve())
                first_seg = rel.parts[0] if rel.parts else ""
            except ValueError:
                first_seg = ""
            if first_seg in (
                _research_contract.REFERENCE_DIR,
                _research_contract.ARCHIVE_DIR,
            ):
                target_id = rec.id6 or rec.path.name
                return (
                    False,
                    f"Setting research status to '{target_status}' is not supported via aw set; use 'aw research promote {target_id} --to {target_status}' instead.",
                )
        is_prompt = (
            rec.path.name.endswith(".research-prompt.md")
            or "- Kind: research-prompt" in rec.raw_text
            or "kind: research-prompt" in rec.raw_text
        )
        if is_prompt and norm_status in _research_contract.HOT_STATUSES:
            return (
                False,
                "a research-prompt carries no hot status; its pipeline position is derived",
            )

    if norm_status not in valid_statuses:
        return (
            False,
            f"Status '{target_status}' is not valid for {rec.record_type} (valid: {sorted(valid_statuses)})",
        )

    # Type-specific validation
    _sentinel_override = getattr(args, "allow_unresolvable_release_sentinel", None)
    if _sentinel_override is not None and not _sentinel_override.strip():
        return (
            False,
            "--allow-unresolvable-release-sentinel requires a non-empty justification",
        )

    if rec.record_type == "releases":
        eff_root = repo_root if repo_root is not None else _repo_root_of(rec.path)
        old_status = (
            normalize_target_status((rec.status or "planned"), "releases")
            .strip()
            .lower()
        )
        if old_status == "planned" and norm_status != "planned":
            from agent_workflows import releases as _releases

            sentinel_res = _releases.resolve_release_outcome(eff_root, "next")
            planned_paths = [p.resolve() for p in sentinel_res.paths]
            rec_resolved = rec.path.resolve()
            if rec_resolved in planned_paths and len(planned_paths) == 1:
                count = _releases.count_blocks_release_sentinel(eff_root)
                if count > 0 and _sentinel_override is None:
                    return (
                        False,
                        f"transitioning {rec.path.name} to '{norm_status}' would leave zero planned releases, "
                        f"causing {count} record(s) with '- Blocks-Release: next' to dangle. "
                        f"Create the successor first with 'aw releases new --version <X.Y.Z> --summary ... --apply' "
                        f"or pass --allow-unresolvable-release-sentinel '<justification>'",
                    )

    if rec.record_type == "specs":
        from agent_workflows import attention_contract as ac

        old_status = rec.status
        if old_status and old_status != norm_status:
            if not ac.transition_allowed(old_status, norm_status):
                return False, f"Illegal spec transition {old_status} -> {norm_status}"
            auth = ac.TRANSITION_AUTHORITY.get(f"->{norm_status}", {})
            if (auth.get("by_human") or auth.get("human_token")) and not getattr(
                args, "by_human", False
            ):
                from agent_workflows import term as _term

                is_interactive = (
                    _term.stdin_is_interactive()
                    and not getattr(args, "agent", False)
                    and not getattr(args, "as_agent", False)
                    and not getattr(args, "json", False)
                )
                if is_interactive:
                    args.by_human = True
                if not getattr(args, "by_human", False):
                    return (
                        False,
                        f"Transition {old_status} -> {norm_status} requires --by-human attestation",
                    )
            # revsweep 5slbpi E-04: the `->reviewed` ATTESTATION, on THIS surface too. The positional
            # `aw specs set reviewed <selector>` spelling routes HERE while the `--status` spelling
            # routes to the forked `specs.run_set`, exactly as the approval gate below documents, so a
            # gate installed in only one of them is bypassed by choosing the other. Both call the SAME
            # `specs._review_attestation_refusal`, which in turn delegates the judgement to the one
            # shared `review_findings.review_attestation_missing` predicate: one rule, one message,
            # three consumers (both setters and `aw check`).
            if ac.TRANSITION_AUTHORITY.get(f"->{norm_status}", {}).get("review_record"):
                from agent_workflows import specs as _specs

                reason = _specs._review_attestation_refusal(rec.path, rec.raw_text)
                if reason is not None:
                    # `validate_transition_allowed` returns a one-line reason; the shared message is
                    # multi-line for the CLI, so it is flattened here rather than forked into a second
                    # wording that could drift from the other surface's.
                    return False, " ".join(reason.split())

    if rec.record_type == "plans":
        from agent_workflows import ipd_lifecycle as _life

        # ipdsetback nvsz19 E-03/E-04: THE PLAN TRANSITION GATE.
        # THE SITE IS LOAD-BEARING: this function is reached by BOTH real spellings (`aw set` and
        # `aw ipd set` both dispatch into `status_set.run_set_command`, which calls it in its pre-flight
        # loop), so one delegation here cannot be dodged by choosing another spelling. It lands inside
        # the established "Refusing before making changes" all-or-nothing batch contract, before the
        # dry-run branch and before any write.
        #
        # FIVE REFUSALS-TO-REFUSE ARE MANDATORY:
        # (1) Treat `unknown target status` as NOT-A-REFUSAL and fall through: `superseded`,
        #     `not-executed`, and `reusable` are absent from `_PLAN_STATUS_RANKS`, and refusing them
        #     would break legitimate retirement / off-sequence moves (E-02's OFF-SEQUENCE class).
        # (2) Do NOT pass `actor=`: that argument makes every `-> executed` target fail as
        #     `unauthorized terminal transition` for the setter's default actor.
        # (3) Do NOT re-list the legal backward edges here: consult `_LEGAL_BACKWARD_EDGES` through
        #     the predicate, never a second copy, avoiding desync.
        # (4) SKIP A NORMALIZED `-> executed` TARGET ENTIRELY (F-06b): the finalize delegation sits
        #     DOWNSTREAM of this site in `run_set_command`. Without this skip, this gate would preempt
        #     it and convert its exit 2 actor refusal into an exit 1 transition refusal on
        #     `draft`/`to-review -> executed`.
        # (5) CASE-FOLD THE SOURCE through `normalize_target_status(rec.status, "plans")` (F-06c):
        #     `read_artifact_record` captures the on-disk token verbatim and `_status_rank` is a bare
        #     dict lookup, so an uppercase `- Status: APPROVED` measures `ok=True` without folding,
        #     and 25 live plans carry one.
        #
        # TERMINAL-SOURCE CARVE-OUT (E-04, PR-802): Stand aside for the WHOLE terminal-source class
        # unconditionally, so the shipped terminal-reopen guard downstream keeps sole ownership of it.
        # Keying the carve-out on the flag would preempt the bare terminal case with exit 1 instead of 2.
        # The terminal set is derived from `_plans_mod.TERMINAL`, never a re-listed literal.
        raw_source = rec.status or ""
        source_status = normalize_target_status(raw_source, "plans").strip().lower()

        if source_status and source_status != norm_status:
            terminal_statuses = {s.strip().lower() for s in _plans_mod.TERMINAL}
            is_terminal_source = source_status in terminal_statuses
            is_target_executed = norm_status == "executed"

            if not is_terminal_source and not is_target_executed:
                ok, reason = _life.validate_transition(source_status, norm_status)
                if not ok:
                    if not (reason and reason.startswith("unknown target status")):
                        return False, f"Illegal plan transition: {reason}"

    # apprvguard Order 01 (d7bnhc): THE APPROVAL GATE. Until this existed, reaching `approved` - the
    # state that LICENSES EXECUTION - required only that the status token be spelled correctly. On
    # 2026-08-30 a blanket "I APPROVE all the reviewed IPDs" therefore swept FIVE plans whose own
    # newest review said `REJECT - NEEDS REPLAN` into `approved`, and only an unrelated pre-execution
    # gate firing for an unrelated reason stopped them from rebuilding shipped subsystems.
    #
    # Keyed on `ipd_schema.READY_TO_EXECUTE`, DERIVED and never re-listed: both `approved` and
    # `auto-approved` license execution, so a gate keyed on the literal `approved` would leave the
    # automated tier ungated AT THE SETTER (d7bnhc D3). `--full-auto` does check a predicate before
    # calling `aw set auto-approved`, but that guard lives in the CALLER, and a caller-side check is
    # exactly what a DIFFERENT caller skips - which is this gate's whole thesis.
    #
    # The pre-flight loop in `run_set_command` calls this for EVERY matched record before any write,
    # so a batch containing one rejected plan approves NONE of them, rather than partially applying.
    #
    # SPECS ARE GATED HERE TOO, and leaving them out was a real bypass caught in validation: the
    # POSITIONAL `aw specs set approved <selector>` spelling routes to THIS function while the
    # `--status` spelling routes to the forked `specs.run_set` (E-07), so gating only plans here left
    # the positional spec spelling approving a spec over a blocking open question that the other
    # spelling refused. `READY_TO_EXECUTE` is a PLAN vocabulary (`auto-approved` is not a spec
    # status), so the two types are tested separately rather than by one union that would imply a
    # spec can be `auto-approved`.
    _gated_approval = (
        rec.record_type == "plans" and norm_status in _ipd_schema.READY_TO_EXECUTE
    ) or (rec.record_type == "specs" and norm_status == "approved")
    if _gated_approval:
        from agent_workflows import plan_readiness as _readiness

        refusals = _readiness.approval_refusals(
            repo_root if repo_root is not None else _repo_root_of(rec.path),
            rec.path,
            rec.raw_text,
            allow_open_questions=bool(getattr(args, "allow_open_questions", False)),
        )
        if refusals:
            return (
                False,
                "refusing to set {0} for {1} {2}: ".format(
                    norm_status,
                    "plan" if rec.record_type == "plans" else "spec",
                    rec.id6 or rec.path.name,
                )
                + "; ".join(refusals),
            )

    # planprio lkexaw E-11: THE PRIORITY / WORK-KIND BACKSTOP. Both are decided where the work is first
    # recorded (the backlog item, or `aw ipd scaffold`, which refuses without them) and the lint gate
    # blocks an undecided value from `review-finalize` on, so on a healthy path this NEVER FIRES
    # (maintainer ruling 2026-09-24). It exists because approval is the state that licenses
    # execution: without it a hand-written plan still carrying `unresolved` would be approved into a
    # plan the pre-execution gate then refuses, silently, in an unattended run. A value passed in the
    # SAME call (`--priority`/`--work-kind`) counts, since `apply_status_change` writes it.
    if rec.record_type == "plans" and norm_status in _ipd_schema.READY_TO_EXECUTE:
        _undecided = plan_priority_work_kind_problems(
            rec.raw_text,
            priority=getattr(args, "priority", None),
            work_kind=getattr(args, "work_kind", None),
        )
        if _undecided:
            return (
                False,
                f"refusing to set {norm_status} for plan {rec.id6 or rec.path.name}: "
                + "; ".join(_undecided)
                + ". These are decided when the work is first recorded (the backlog item, or "
                "`aw ipd scaffold`); set them with `aw ipd set <status> <id6> --priority ... "
                "--work-kind ...`",
            )

    if rec.record_type == "backlog":
        from agent_workflows import attention_contract as _ac

        # ORDERING CONSEQUENCE: this pre-flight loop runs BEFORE the evaluate_blocking_close
        # loop in run_set_command. A request that is BOTH an illegal transition and an
        # illegitimate release-gate close will now report the TRANSITION refusal and not
        # the gate refusal. Both exit 1, so no exit code changes; only the message does.
        #
        # THREE COMPOSITION CONSTRAINTS:
        # (1) SKIP THE SELF-EDGE: X -> X returns ok=True for every backlog status (measured).
        #     aw backlog note exists so annotation does not need a transition call;
        #     a same-status set is documented misuse, not an invalid transition error.
        # (2) CASE-FOLD THE SOURCE: read_artifact_record captures - Status: token verbatim;
        #     an uppercase - Status: DONE would bypass an unfolded check (matching plans).
        #     Live corpus measured zero non-canonical tokens, so this is prophylactic.
        # (3) PRESERVE EXISTING ->blocked GATE-FLAG RULE: checking gate flags is a distinct
        #     question from transition legality and preserves its own refusal and message.
        raw_source = rec.status or ""
        old_status = normalize_target_status(raw_source, "backlog").strip().lower()

        if old_status and old_status != norm_status:
            if not _ac.backlog_transition_allowed(old_status, norm_status):
                return (
                    False,
                    f"Illegal backlog transition {old_status} -> {norm_status}",
                )

        if norm_status == "blocked":
            gk = getattr(args, "gate_kind", None)
            gr = getattr(args, "gate_ref", None)
            if not gk or not gr:
                return (
                    False,
                    "Moving backlog item to blocked requires --gate-kind and --gate-ref",
                )

    # THE ACTOR SHAPE GATE (plan fn2l1u E-07). Refused HERE, in the shared pre-flight, so the CLI
    # reports a one-line refusal BEFORE any record in the batch is written; `apply_status_change`
    # raises on the same condition as the fail-closed backstop for a direct caller that skips this
    # pre-flight. Both delegate to the ONE validator (`attention_contract.actor_refusal`).
    #
    # WHY THIS IS THE HIGH-VALUE GUARD, and not merely tidiness. A parenthesized actor makes the
    # history record unparseable to `plan_readiness._HISTORY_RECORD_PARTS_RE`, so
    # `is_review_history_entry` returns False, so `newest_verdict` returns None, so the approval gate
    # directly above emits ZERO refusals. Reproduced end to end before this landed: writing
    # `reviewed` with a parenthesized actor and the message `/plan-review: REJECT - NEEDS REPLAN`,
    # then `aw set approved --by-human`, EXITED 0 and wrote `- Status: approved`, while the identical
    # sequence with a slash-form actor EXITED 1 with "This refusal has NO override." A formatting
    # accident therefore silently converted the one un-overridable approval refusal into a no-op -
    # precisely the failure this gate was built after. Plan fn2l1u E-08 also widened that reader, so
    # the hole is closed from both ends: old lines now parse, and new ones cannot take this shape.
    #
    # An actor is only refused when one was PASSED. An absent `--actor` falls back to the default
    # `aw set` further down in `apply_status_change`, which is parenthesis-free by construction, so
    # this never fires on the common no-flag path.
    _passed_actor = getattr(args, "actor", None)
    if _passed_actor is not None and str(_passed_actor).strip():
        from agent_workflows import attention_contract as _ac

        _actor_problem = _ac.actor_refusal(str(_passed_actor))
        if _actor_problem is not None:
            return False, _actor_problem

    return True, None


def same_status_message_is_duplicate(
    text: str, *, status: str, date: str, message: str
) -> bool:
    """Whether writing ``message`` as a ``status``/``date`` record would merely REPEAT the newest one.

    True when the artifact's NEWEST existing history record already carries the same status token
    (or ``same-status`` tag), the same date, and a byte-identical message. Pure; ``text`` is whole artifact text.

    WHY THIS PREDICATE EXISTS (plan ``vhbvwz`` E-01, finding F-10; plan ``1i300e`` E-03, finding F-9).
    Making a same-status write record its history - the ``x6tk1u`` fix - cannot key on message
    PRESENCE alone or bypass defaulted messages, because that grows duplicate history on idempotent
    re-assertions or repeated metadata writes. Both explicit ``--message`` and defaulted same-status
    records are deduplicated here against the newest existing entry.

    DELIBERATELY COMPARED AGAINST THE NEWEST RECORD ONLY, not against every record in the file. The
    rule must distinguish "I am re-asserting the state I just asserted" (silent) from "I am adding a
    new note" (recorded), and a genuinely new note that happens to reuse an older wording is the
    SECOND case. Scanning the whole file would refuse it, which is the ``x6tk1u`` defect wearing a
    different hat. The ACTOR is deliberately NOT compared either: the same note re-asserted under a
    different actor string is still the same note.
    """

    from agent_workflows import attention as _att
    from agent_workflows import attention_contract as _ac
    from agent_workflows import plan_readiness as _readiness

    newest = _ac.newest_history_record(
        [line.strip() for line in _att._history_section_lines(text)]
    )
    if newest is None:
        return False
    # The SHARED record parser, not a second copy of the grammar: `plan_readiness` already owns it and
    # `attention_contract.actor_refusal` exists because that shape is a contract rather than a habit.
    m = _readiness._HISTORY_RECORD_PARTS_RE.match(newest)
    if m is None:
        return False
    mid = m.group("mid").strip()
    status_match = (
        (mid == status) or (mid == "same-status") or (status == "same-status")
    )
    return (
        m.group("date") == date
        and status_match
        and m.group("msg").strip() == (message or "").strip()
    )


class StatusChangeResult(tuple):
    """Result of apply_status_change: a 2-tuple (dest_path, norm_status) with rewritten_paths and optional warning attributes."""

    def __new__(
        cls,
        dest_path: Path,
        norm_status: str,
        rewritten_paths: list[str] | None = None,
        warning: str | None = None,
    ):
        return super().__new__(cls, (dest_path, norm_status))

    def __init__(
        self,
        dest_path: Path,
        norm_status: str,
        rewritten_paths: list[str] | None = None,
        warning: str | None = None,
    ) -> None:
        self.dest_path = dest_path
        self.norm_status = norm_status
        self.rewritten_paths = list(rewritten_paths or [])
        self.warning = warning


def inherit_from_backlog_release_gate(
    text: str,
    repo_root: Path,
    from_backlog: str | None,
    blocks_release: str | None,
    verb_label: str = "aw set",
) -> str:
    """Inherit the backlog item's release gate at graduation if artifact has no gate.

    nobugship di08i9 E-03: INHERIT THE ITEM'S RELEASE GATE AT GRADUATION, so the handoff
    obligation stops depending on prose.

    Shared between `status_set.apply_status_change` and `specs.run_set` (c6f6sj E-02).
    Text in, text out.

    Three semantics preserved:
    (1) A write, never a refusal: un-inheritable gate does not fail the call.
    (2) An explicit blocks_release in the same call wins (guarded by blocks_release is None).
    (3) An existing gate on the artifact is never overwritten (carrier_br is None).
    """
    if not from_backlog or from_backlog == "-":
        return text
    if blocks_release is not None:
        return text
    carrier_br = _sel.read_front_matter_blocks_release(text)
    if carrier_br is not None:
        return text
    from agent_workflows import backlog as _backlog
    from agent_workflows import releases as _releases

    item_gate = _backlog.blocks_release_of_item(Path(repo_root), from_backlog)
    if not item_gate:
        return text
    prefix = verb_label if verb_label.endswith(":") else f"{verb_label}:"
    updated_text = _releases.set_blocks_release_line(text, item_gate)
    sys.stdout.write(
        f"{prefix} inherited - Blocks-Release: {item_gate} from backlog item "
        f"{from_backlog} (graduation handoff: the gate travels with the work)\n"
    )
    return updated_text


def apply_status_change(
    rec: ArtifactRecord,
    target_status: str,
    repo_root: Path,
    args: argparse.Namespace,
    close_verdict: Any = None,
) -> tuple[Path, str]:
    """Apply the status change on disk, recording workflow history (NEWEST-FIRST: the record is
    PREPENDED under the `## Workflow history` heading, not appended) and moving the file if needed.

    For a genuine status transition (old != target), the status token is the target status and the
    default message is `status set to <status>`. For an untooled status change on a plan (old ==
    target on disk, but HEAD status differs), the change is treated as a genuine transition from
    HEAD: the status token is the target status and the default message is `status set to <status>`,
    while preserving duplicate suppression. For a true same-status write (old == target and HEAD
    matches), the history record is tagged with `same-status` so verdict readers do not mistake it
    for a review record, and its default message is `status unchanged (<status>)`. Pure no-ops (no
    field or message changes) write nothing. Same-status writes (both defaulted and explicit messages)
    are deduplicated against the newest record via `same_status_message_is_duplicate`."""
    norm_status = normalize_target_status(target_status, rec.record_type)
    curr_rec_status = rec.status
    if curr_rec_status is None and rec.record_type == "prompts":
        from agent_workflows import prompts as _prompts

        curr_rec_status = _prompts.read_metadata_status(rec.raw_text)
    old_status = (
        normalize_target_status((curr_rec_status or "draft"), rec.record_type)
        .strip()
        .lower()
    )
    is_same_status = old_status == norm_status.strip().lower()
    today = _core.utc_history_date()

    untooled_transition = False
    if is_same_status:
        status_tag = "same-status"
        default_message = f"status unchanged ({norm_status})"
        if rec.record_type == "plans":
            try:
                from agent_workflows import check_engine as _ce

                try:
                    rel = rec.path.resolve().relative_to(repo_root.resolve()).as_posix()
                except ValueError:
                    rel = str(rec.path)
                head_text = _ce._blob_text(repo_root, "HEAD", rel)
                head_status = _ce._status_meta(head_text)
                if head_status is not None:
                    norm_head = (
                        normalize_target_status(head_status, "plans").strip().lower()
                    )
                    if norm_head != norm_status.strip().lower():
                        status_tag = norm_status
                        default_message = f"status set to {norm_status}"
                        untooled_transition = True
            except Exception:
                pass
    else:
        status_tag = norm_status
        default_message = f"status set to {norm_status}"

    _is_backward_plan = False
    _demotion_warning: str | None = None
    if rec.record_type == "plans":
        from agent_workflows.ipd_lifecycle import _LEGAL_BACKWARD_EDGES

        if (old_status, norm_status) in _LEGAL_BACKWARD_EDGES:
            _is_backward_plan = True
            reason = (getattr(args, "message", None) or "").strip()
            plan_id = rec.id6 or rec.path.name
            if old_status in ("approved", "auto-approved"):
                _demotion_warning = f"DEMOTED {plan_id}: {old_status} -> {norm_status}: APPROVAL WITHDRAWN: {reason}"
                message = f"demoted {old_status} -> {norm_status}: APPROVAL WITHDRAWN: {reason}"
            else:
                _demotion_warning = (
                    f"DEMOTED {plan_id}: {old_status} -> {norm_status}: {reason}"
                )
                message = f"demoted {old_status} -> {norm_status}: {reason}"
        else:
            message = getattr(args, "message", None) or default_message
    else:
        message = getattr(args, "message", None) or default_message
    actor = getattr(args, "actor", None) or "aw set"
    # THE BACKSTOP for the actor-shape gate (plan fn2l1u E-07). `validate_transition_allowed` refuses
    # this in the CLI pre-flight with a clean one-line message; this raise catches a DIRECT caller of
    # this function that never ran that pre-flight. It is checked BEFORE the `--by-human` /
    # `--allow-open-questions` suffixes are folded in and before any file is touched, so a refused
    # call writes nothing. See `attention_contract.actor_refusal` for why the parenthesis refusal
    # remains correct even though the readers now tolerate that shape.
    from agent_workflows import attention_contract as _ac

    _actor_problem = _ac.actor_refusal(actor)
    if _actor_problem is not None:
        raise ValueError(_actor_problem)
    if getattr(args, "by_human", False):
        actor = f"{actor}, --by-human"
    # apprvguard d7bnhc E-06: an OVERRIDDEN approval must be auditable in the ARTIFACT, not only in
    # someone's shell history. Folded into the actor string, following the `--by-human` precedent
    # directly above, so it is machine-greppable rather than buried in free-text prose. Recorded only
    # where it could have had an effect (a plan reaching a ready-to-execute status), so an
    # inconsequential flag on an unrelated transition does not litter history with a false claim.
    if getattr(args, "allow_open_questions", False) and (
        (rec.record_type == "plans" and norm_status in _ipd_schema.READY_TO_EXECUTE)
        or (rec.record_type == "specs" and norm_status == "approved")
    ):
        actor = f"{actor}, --allow-open-questions"
    # setterguard `4bc1nd` E-02: the terminal-reopen OVERRIDE must be auditable in the ARTIFACT, not
    # only in someone's shell history - the same reasoning as `--allow-open-questions` directly above,
    # and the property OQ-01's review note required of this flag. Recorded ONLY where it could have
    # had an effect (a PLAN actually leaving a terminal status for a nonterminal one), so the flag
    # never litters history with a false claim on a transition it did not unlock.
    if getattr(args, "allow_terminal_reopen", False) and rec.record_type == "plans":
        _terminal_statuses = {s.strip().lower() for s in _plans_mod.TERMINAL}
        _was_terminal = (
            normalize_target_status((rec.status or ""), "plans").strip().lower()
            in _terminal_statuses
        )
        if _was_terminal and norm_status.strip().lower() not in _terminal_statuses:
            actor = f"{actor}, --allow-terminal-reopen"

    _sentinel_override = getattr(args, "allow_unresolvable_release_sentinel", None)
    if _sentinel_override is not None:
        _sentinel_override = _sentinel_override.strip()
        if not _sentinel_override:
            raise ValueError(
                "--allow-unresolvable-release-sentinel requires a non-empty justification"
            )

    if rec.record_type == "releases" and norm_status != "planned":
        curr_status = (
            normalize_target_status((rec.status or "planned"), "releases")
            .strip()
            .lower()
        )
        if curr_status == "planned":
            from agent_workflows import releases as _releases

            sentinel_res = _releases.resolve_release_outcome(repo_root, "next")
            planned_paths = [p.resolve() for p in sentinel_res.paths]
            rec_resolved = rec.path.resolve()
            if rec_resolved in planned_paths and len(planned_paths) == 1:
                count = _releases.count_blocks_release_sentinel(repo_root)
                if count > 0 and not _sentinel_override:
                    raise ValueError(
                        f"transitioning {rec.path.name} to '{norm_status}' would leave zero planned releases, "
                        f"causing {count} record(s) with '- Blocks-Release: next' to dangle. "
                        f"Create the successor first with 'aw releases new --version <X.Y.Z> --summary ... --apply' "
                        f"or pass --allow-unresolvable-release-sentinel '<justification>'"
                    )

    if rec.record_type == "releases" and _sentinel_override:
        actor = f"{actor}, --allow-unresolvable-release-sentinel"
        if getattr(args, "message", None):
            message = f"{message} (override: {_sentinel_override})"
        else:
            message = f"{default_message} (override: {_sentinel_override})"

    text = rec.path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if rec.record_type == "prompts":
        from agent_workflows import prompts as _prompts

        if _prompts.has_metadata_comment(text):
            updated_text = _prompts.update_metadata_status(text, norm_status)
            new_lines = updated_text.splitlines()
        else:
            # Commentless prompt (OQ-02): adopt refusal-to-mint posture; status lives in directory only.
            new_lines = list(lines)
            sys.stdout.write(
                f"aw set: note: prompt {rec.id6 or rec.path.name} has no metadata comment; "
                f"status lives in directory only\n"
            )
    else:
        # Update or insert - Status: <norm_status> in frontmatter only
        status_updated = False
        new_lines = []
        in_frontmatter = True
        is_fenced_yaml = bool(lines and lines[0].strip() == "---")

        for line in lines:
            if is_fenced_yaml:
                if in_frontmatter and line.strip() == "---" and new_lines:
                    in_frontmatter = False
                if (
                    in_frontmatter
                    and not status_updated
                    and re.match(r"^status:\s*\S+", line, re.IGNORECASE)
                ):
                    new_lines.append(f"status: {norm_status}")
                    status_updated = True
                else:
                    new_lines.append(line)
            else:
                if in_frontmatter and line.startswith("## "):
                    in_frontmatter = False
                if in_frontmatter and not status_updated and _STATUS_RE.match(line):
                    new_lines.append(f"- Status: {norm_status}")
                    status_updated = True
                else:
                    new_lines.append(line)

        if not status_updated:
            if is_fenced_yaml:
                # insert status: before closing ---
                res_lines = []
                inserted = False
                for line in new_lines:
                    if not inserted and line.strip() == "---" and res_lines:
                        res_lines.append(f"status: {norm_status}")
                        inserted = True
                    res_lines.append(line)
                new_lines = res_lines
            else:
                inserted = False
                res_lines = []
                for i, line in enumerate(new_lines):
                    res_lines.append(line)
                    if not inserted and (line.startswith(("# ", "- Date:"))):
                        res_lines.append(f"- Status: {norm_status}")
                        inserted = True
                if not inserted:
                    res_lines.insert(0, f"- Status: {norm_status}")
                new_lines = res_lines

    # Gate fields: clear them on any transition OUT of the gate-carrying status. This is
    # record-type-agnostic in the SAME way the Blocks-Release write below is (bug 61qk4a): the guard
    # used to read `rec.record_type == "specs"`, so `aw backlog set open <id6>` moved a blocked item
    # to open while LEAVING its Gate-Kind/Gate-Ref behind. `aw backlog check` then reported
    # `backlog.gate-unexpected`, and the only way out was the hand-edit the house rules forbid
    # (bug 43p53n). `backlog.run_set` already cleared correctly, but the positional
    # `aw backlog set <status> <selector>` form routes here instead, so that fix was unreachable.
    gate_status = _GATE_STATUS_BY_TYPE.get(rec.record_type)
    if gate_status is not None:
        if norm_status != gate_status:
            new_lines = [
                line_item
                for line_item in new_lines
                if not _GATE_KIND_RE.match(line_item)
                and not _GATE_REF_RE.match(line_item)
                and not _GATE_SUMMARY_RE.match(line_item)
            ]
        else:
            gk = getattr(args, "gate_kind", None)
            gr = getattr(args, "gate_ref", None)
            gs = getattr(args, "gate_summary", None)
            if gk and gr:
                new_lines = [
                    line_item
                    for line_item in new_lines
                    if not _GATE_KIND_RE.match(line_item)
                    and not _GATE_REF_RE.match(line_item)
                    and not _GATE_SUMMARY_RE.match(line_item)
                ]
                st_idx = -1
                for i, line_item in enumerate(new_lines):
                    if _STATUS_RE.match(line_item):
                        st_idx = i
                        break
                insert_pos = st_idx + 1 if st_idx >= 0 else 1
                gate_lines = [f"- Gate-Kind: {gk}", f"- Gate-Ref: {gr}"]
                if gs:
                    gate_lines.append(f"- Gate-Summary: {gs}")
                for gl in reversed(gate_lines):
                    new_lines.insert(insert_pos, gl)

    # Blocks-Release write (IPD efnn74, root-cause of bug 61qk4a): this mutation is
    # record-type-agnostic and MUST apply to plans and backlog too, not only specs, so it is
    # hoisted OUT of the specs-only guard above. The specs-only Gate-Kind/Gate-Ref/Gate-Summary
    # handling stays inside that guard; only this shared write is lifted. All setter surfaces funnel
    # through the single shared `releases.set_blocks_release_line` primitive (no duplicate write
    # path). The join/split idempotency is preserved so trailing metadata structure is unchanged.
    br = getattr(args, "blocks_release", None)
    if br is not None:
        from agent_workflows import releases as _releases

        tmp_text = "\n".join(new_lines)
        tmp_text = _releases.set_blocks_release_line(tmp_text, br)
        new_lines = tmp_text.splitlines()

    # relexempt ghna7l E-05: release exemption write, beside Blocks-Release above.
    rel_exempt_kind = getattr(args, "release_exempt_kind", None)
    rel_exempt_ref = getattr(args, "release_exempt_ref", None)
    if rel_exempt_kind is not None or rel_exempt_ref is not None:
        from agent_workflows import backlog as _backlog

        tmp_text = "\n".join(new_lines)
        if rel_exempt_kind == "-":
            tmp_text = _backlog.set_release_exempt_kind_line(tmp_text, "-")
            tmp_text = _backlog.set_release_exempt_ref_line(tmp_text, "-")
        else:
            if rel_exempt_ref is not None:
                tmp_text = _backlog.set_release_exempt_ref_line(
                    tmp_text, rel_exempt_ref
                )
            if rel_exempt_kind is not None:
                tmp_text = _backlog.set_release_exempt_kind_line(
                    tmp_text, rel_exempt_kind
                )
        new_lines = tmp_text.splitlines()

    # From-Backlog write (bklggrad ku93tn): the same hoisted, status-branch-independent shape as the
    # Blocks-Release write above, so `aw ipd set --from-backlog <id6|->` persists even on a no-op
    # (same-status) transition. Funnels through the single shared `releases.set_from_backlog_line`
    # primitive (no duplicate write path).
    fb = getattr(args, "from_backlog", None)
    if fb is not None:
        if fb != "-":
            # IPD izh17y E-03: validation backstop in apply_status_change preventing unresolvable
            # dangling links even via direct calls. Resolves via `backlog.existing_backlog_ids` (P8).
            # An empty id set skips the refusal so an invisible backlog corpus cannot make every write fail.
            # DELIBERATE DIVERGENCE FROM CHECKER (F-12): `releases.check_from_backlog` has no empty-set skip
            # and its own docstring explicitly records that asymmetry ("THE TWO BACK-LINK TWINS DISAGREE ON
            # FAIL-SAFETY, AND THIS ONE IS THE LESS SAFE ... Do NOT 'harmonize' that guard away to match this
            # function; the difference is a known gap here, not a standard to spread"). The setter takes the
            # safe posture rather than copying the checker's less-safe posture.
            from agent_workflows import backlog as _backlog

            known_backlog = _backlog.existing_backlog_ids(repo_root)
            if known_backlog and fb not in known_backlog:
                raise ValueError(
                    f"unresolvable backlog id '{fb}' (does not resolve to an existing backlog item)"
                )
        from agent_workflows import releases as _releases

        tmp_text = "\n".join(new_lines)
        tmp_text = _releases.set_from_backlog_line(tmp_text, fb)
        new_lines = tmp_text.splitlines()

        # nobugship di08i9 E-03 / c6f6sj E-02: INHERIT THE ITEM'S RELEASE GATE AT GRADUATION.
        # Collapsed to shared inherit_from_backlog_release_gate.
        tmp_text = "\n".join(new_lines)
        tmp_text = inherit_from_backlog_release_gate(
            tmp_text,
            repo_root,
            fb,
            getattr(args, "blocks_release", None),
            verb_label="aw set",
        )
        new_lines = tmp_text.splitlines()

    # From-Spec write (IPD 0ykozn E-02): the same hoisted, status-branch-independent shape as the
    # Blocks-Release and From-Backlog writes above, so `aw ipd set --from-spec <id6|->` persists even
    # on a no-op (same-status) transition. Funnels through the single shared
    # `releases.set_from_spec_line` primitive (no duplicate write path).
    fs = getattr(args, "from_spec", None)
    if fs is not None:
        if fs != "-":
            # IPD 0ykozn E-02 / review finding PR-504: validation backstop in apply_status_change.
            # Deliberately STRICTER than its twin (--from-backlog writes unchecked), preventing
            # unresolvable dangling links from being written even via direct calls.
            # An empty union skips the refusal so an invisible spec corpus cannot make every write fail.
            from agent_workflows import check_engine as _ce

            known = _ce.known_spec_ids(repo_root)
            if known and fs not in known:
                raise ValueError(
                    f"unresolvable spec id '{fs}' (does not resolve to an existing spec)"
                )
        from agent_workflows import releases as _releases

        tmp_text = "\n".join(new_lines)
        tmp_text = _releases.set_from_spec_line(tmp_text, fs)
        new_lines = tmp_text.splitlines()

    # Item-Dependencies write (ipddeps g69y23): the SAME hoisted, status-branch-independent shape as
    # the Blocks-Release / From-Backlog writes above, so `aw ipd dependencies set` persists even on a
    # no-op (same-status) transition. Funnels through the single shared
    # `releases.set_item_dependencies_line` primitive (spec-2.7 position, no duplicate write path).
    # The value is already canonicalized + validated by the `dependencies set` handler before it
    # reaches here; `-`/None clears.
    idep = getattr(args, "item_dependencies", None)
    if idep is not None:
        from agent_workflows import releases as _releases

        tmp_text = "\n".join(new_lines)
        tmp_text = _releases.set_item_dependencies_line(tmp_text, idep)
        new_lines = tmp_text.splitlines()

    # Priority write (xprio 1b45el): the SAME hoisted, status-branch-independent shape so
    # `aw ipd set --priority <low|medium|high|->` (and, once children 02/03 land, spec/research
    # setters) persists even on a no-op (same-status) transition. Funnels through the single shared
    # `releases.set_priority_line` primitive (no duplicate write path). `-`/None clears. The ENUM
    # value is validated by `aw check`, not here.
    prio = getattr(args, "priority", None)
    if prio is not None:
        from agent_workflows import releases as _releases

        tmp_text = "\n".join(new_lines)
        tmp_text = _releases.set_priority_line(tmp_text, prio)
        new_lines = tmp_text.splitlines()

    # Work-Kind write (wkindname ng2blv): the SAME hoisted, status-branch-independent shape as the
    # Priority write above, so `aw ipd set --work-kind <bug|feature|chore|security|followup|->`
    # persists even on a no-op (same-status) transition. Funnels through the single shared
    # `releases.set_work_kind_line` primitive (no duplicate write path). `-`/None clears. The ENUM
    # value is validated by `aw check` (check.work-kind-invalid), not here.
    work_kind = getattr(args, "work_kind", None)
    if work_kind is not None:
        from agent_workflows import releases as _releases

        tmp_text = "\n".join(new_lines)
        tmp_text = _releases.set_work_kind_line(tmp_text, work_kind)
        new_lines = tmp_text.splitlines()

    # Graduated-To write (setidhard bwgyum E-04): the FIFTH hoisted, status-branch-independent
    # field-write on this path, in the SAME shape as the four above (Blocks-Release, From-Backlog,
    # Item-Dependencies, Priority/Work-Kind), funnelling through the single shared
    # `releases.set_graduated_to_line` primitive so there is no duplicate write path. `-`/None clears.
    #
    # WHY HERE RATHER THAN IN `backlog.run_set` (plan OQ-03, and the one place the plan's original
    # design was wrong). This function is record-type-AGNOSTIC and is the shared handler for
    # `aw backlog set`, `aw specs set`, `aw ipd set` and the bare `aw set`, so ONE write here serves the
    # BACKLOG source, the SPEC source and the plan side at once. Spec 4w7d6s G3 puts the field on specs
    # as well as items, and that half is therefore the same lines of code rather than a second
    # implementation. A flag bolted onto `backlog.run_set` would serve one spelling of one verb.
    #
    # THE VALUE IS VALIDATED BEFORE IT REACHES HERE, at each setter surface, through the shared
    # `releases.canonicalize_graduated_to` (which judges the token shape with the existing
    # `plans.is_set_id_valid`), so this call site stays a pure write exactly like its four neighbours.
    graduated_to = getattr(args, "graduated_to", None)
    if graduated_to is not None:
        from agent_workflows import releases as _releases

        tmp_text = "\n".join(new_lines)
        tmp_text = _releases.set_graduated_to_line(tmp_text, graduated_to)
        new_lines = tmp_text.splitlines()

    # nobugship di08i9 E-02 / gatefollows vsgd48 E-02: THE POSITIONAL SPELLING'S DEFAULT (ON
    # RECLASSIFICATION AND ON STATUS TRANSITIONS INTO A LIVE STATUS). When an item's Work-Kind
    # BECOMES `bug`, OR when an existing `bug` item transitions into a live status, and it carries no
    # gate, the release gate is defaulted here too, through the SAME shared
    # `backlog.decide_gate_default` predicate `backlog.run_new` and `backlog.run_set` call, and
    # written through the SAME shared `releases.set_blocks_release_line` primitive as every other gate
    # write on this path.
    #
    # BOTH DISPATCH PATHS ARE REQUIRED AND THAT IS WHY THIS EXISTS. `aw backlog set` forks on whether
    # `--status` was PASSED (cli.py): the positional spelling routes HERE, and the `--status` spelling
    # routes to `backlog.run_set`. A default wired into one only would fire for one spelling of one
    # verb and not the other, which is worse than not shipping it because it teaches a false
    # expectation. The shared predicate is what keeps the two from drifting.
    #
    # SCOPED TO BACKLOG RECORDS DELIBERATELY. This function is shared by plans and specs, whose
    # `- Work-Kind:` is a recognized-but-optional descriptive field rather than the REQUIRED
    # classification a backlog item carries, and whose gate arrives by graduation (E-03's
    # `--from-backlog` inheritance), not by reclassification. Defaulting a gate onto a plan because
    # someone labelled it `bug` would invent a release obligation from a descriptive edit.
    if rec.record_type == "backlog" and getattr(args, "blocks_release", None) is None:
        from agent_workflows import backlog as _backlog
        from agent_workflows import releases as _releases

        _current_text = "\n".join(new_lines)
        _effective_kind = work_kind or _backlog.parse_item(_current_text).kind
        _existing_br = _sel.read_front_matter_blocks_release(_current_text)
        _parsed_item = _backlog.parse_item(_current_text)
        _is_exempt = bool(
            _parsed_item.release_exempt_kind
            and _parsed_item.release_exempt_ref
            and _parsed_item.release_exempt_kind != "-"
            and _parsed_item.release_exempt_ref != "-"
        )
        _gate_default, _gate_notice = _backlog.decide_gate_default(
            repo_root,
            kind=_effective_kind,
            status=norm_status,
            explicit_blocks_release=None,
            existing_blocks_release=_existing_br,
            is_exempt=_is_exempt,
        )
        if _gate_default is not None:
            tmp_text = _releases.set_blocks_release_line(_current_text, _gate_default)
            new_lines = tmp_text.splitlines()
        if _gate_notice:
            sys.stdout.write(f"aw backlog set: {_gate_notice}\n")

    # Close-Evidence write (gh409m byzkr7 E-03/E-04): write the cited evidence durably on an
    # evidence-satisfied close for backlog records. Scoped to rec.record_type == "backlog".
    # Keyed on verdict.legitimate and verdict.path == "SATISFIED", never on args.evidence alone.
    if rec.record_type == "backlog":
        verdict = close_verdict
        if verdict is None and getattr(args, "evidence", None):
            from agent_workflows import check_engine as _ce
            from agent_workflows import backlog as _backlog_eval

            verdict = _ce.evaluate_blocking_close(
                repo_root,
                rec.path,
                norm_status,
                evidence=getattr(args, "evidence", None),
                item_text="\n".join(new_lines),
                prior_priority=_backlog_eval.parse_item(text).priority,
            )
        if verdict and verdict.legitimate and verdict.path == "SATISFIED":
            from agent_workflows import backlog as _backlog

            accepted_evidence = (
                getattr(args, "evidence", None)
                or _backlog.parse_item("\n".join(new_lines)).close_evidence
            )
            if accepted_evidence:
                tmp_text = "\n".join(new_lines)
                tmp_text = _backlog.set_close_evidence_line(
                    tmp_text, accepted_evidence, repo_root=repo_root
                )
                new_lines = tmp_text.splitlines()

    if rec.record_type == "plans" and norm_status != "approved":
        new_lines = [
            line_item
            for line_item in new_lines
            if not re.match(r"^- Approval:\s*", line_item)
        ]
    if (
        rec.record_type == "plans"
        and _is_backward_plan
        and norm_status in ("draft", "to-review")
    ):
        new_lines = [
            line_item
            for line_item in new_lines
            if not re.match(r"^- Readiness:\s*", line_item)
        ]

    # The IPD schema REQUIRES an `- Approval:` field exactly when Status is `approved`
    # (ipd_schema.APPROVAL_STATUSES; enforced as IPD-M104). `auto-approved` is a
    # sibling tier that records an automated clear and must NOT carry it. So when a
    # plan transitions to `approved` and has no Approval field yet, write a
    # conformant one here, so the setter never produces a plan that fails lint.
    if rec.record_type == "plans" and norm_status == "approved":
        has_approval = any(
            re.match(r"^- Approval:\s*", line_item) for line_item in new_lines
        )
        if not has_approval:
            attn = (
                'human ("approved")'
                if getattr(args, "by_human", False)
                else "recorded via aw ipd set"
            )
            approval_line = f"- Approval: {today}, {attn}: {message}"
            # Insert as the last front-matter bullet: after `- Id:` if present, else
            # after `- Status:`, else before the first `## ` heading.
            insert_idx = None
            for i, line_item in enumerate(new_lines):
                if line_item.startswith("## "):
                    break
                if re.match(r"^- Id:\s*", line_item):
                    insert_idx = i + 1
            if insert_idx is None:
                for i, line_item in enumerate(new_lines):
                    if line_item.startswith("## "):
                        break
                    if _STATUS_RE.match(line_item):
                        insert_idx = i + 1
            if insert_idx is None:
                for i, line_item in enumerate(new_lines):
                    if line_item.startswith("## "):
                        insert_idx = i
                        break
                if insert_idx is None:
                    insert_idx = len(new_lines)
            new_lines.insert(insert_idx, approval_line)

    # Determine destination path using the shared record placement library (Set specdirs, IPD r9uvwc)
    from agent_workflows import record_placement as _placement

    dest_path = _placement.resolve_transition_path(
        rec.record_type, rec.path, norm_status, repo_root=repo_root
    )

    content_changed = new_lines != lines
    path_changed = dest_path.resolve() != rec.path.resolve()

    # WRITE A DELIBERATE `--message` EVEN WHEN NOTHING ELSE MOVED (plan `vhbvwz` E-01, bug `x6tk1u`).
    #
    # THE BUG THIS FIXES: this early return used to be unconditional, and it sits BEFORE the history
    # write below, so `aw set <the-status-it-already-has> <artifact> --message "<reasoning>"` discarded
    # the message and exited 0. Measured on this repository: roughly 2000 characters of recorded
    # reasoning were swallowed, noticed only because `git status` showed no modification. Nothing else
    # records it either - this module writes NOTHING to the history sidecar - so the note was simply
    # gone.
    #
    # THE SHAPE IS THE ESTABLISHED ONE. Four field writes above (`Blocks-Release`, `From-Backlog`,
    # `Item-Dependencies`, `Priority`) were each hoisted out of the status-change branch for exactly
    # this reason: the field must be written even when the status does not move. The FROM-BACKLOG
    # PRECEDENT is the closest, since it was hoisted specifically so `aw ipd set --from-backlog`
    # persists "even on a no-op (same-status) transition"; this is the same correction applied to the
    # history record.
    #
    # PRESENCE ALONE IS NOT THE DISCRIMINATOR, and the dedup half is not optional: see
    # `same_status_message_is_duplicate` for the measured three-identical-records run and for the two
    # runner call sites that would otherwise append a duplicate on every re-run.
    _explicit_message = (getattr(args, "message", None) or "").strip()
    is_dup = (
        same_status_message_is_duplicate(
            text, status=status_tag, date=today, message=message
        )
        if is_same_status
        else False
    )
    _write_history_anyway = (
        bool(_explicit_message) or untooled_transition
    ) and not is_dup

    if not content_changed and not path_changed and not _write_history_anyway:
        return StatusChangeResult(rec.path, norm_status, [], warning=_demotion_warning)

    # Write the Workflow history record. NEWEST-FIRST, NOT appended: the `insert(i + 1, ...)` below
    # PREPENDS the new record directly under the `## Workflow history` heading, so the FIRST record
    # in the section is the most recent one. This is the CONTRACT (fullauto 97df1z E-07 corrected the
    # comment, which used to say "Append", and the matching sentence in
    # `.aw/records/plans/README.md`); the writer's behavior is deliberately unchanged, because
    # reordering every existing plan's history would be a destructive rewrite. Any reader wanting
    # "the latest entry" must take the FIRST record of the BOUNDED section - use the shared
    # `plan_readiness.extract_newest_history_entry`, and do not hand-roll another parser.
    #
    # A same-status write is tagged `same-status` and is deduplicated so successive metadata-only
    # writes on the same day do not accumulate duplicate records (plan `1i300e` E-02, E-03).
    should_write_history = not (is_same_status and is_dup)
    if should_write_history:
        hist_entry = f"- {today} {status_tag} ({actor}): {message}"
        has_hist_section = False
        for i, line in enumerate(new_lines):
            if _HISTORY_HDR_RE.match(line):
                has_hist_section = True
                new_lines.insert(i + 1, hist_entry)
                break

        if not has_hist_section:
            insert_idx = len(new_lines)
            if rec.record_type != "prompts":
                for i, line in enumerate(new_lines):
                    if line.startswith("## "):
                        insert_idx = i
                        break
            new_lines.insert(insert_idx, "")
            new_lines.insert(insert_idx, hist_entry)
            new_lines.insert(insert_idx, "## Workflow history")

    updated_text = "\n".join(new_lines).rstrip() + "\n"

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # RELOCATE WITH `git mv`, NOT write-then-unlink.
    #
    # THE BUG THIS FIXES, measured 2026-09-13 on run `run-20260913T031350Z-1732436`: this function
    # used to `atomic_write` the destination and then `unlink` the source, which git sees as TWO
    # unrelated facts (an untracked file appeared; a tracked file vanished) that a caller then has to
    # find and stage together. `oc_runipd.commit_backlog_close` does exactly that pairing and it
    # committed only the ADD (commit `52837644` contains `A done/...` and no `D graduated/...`),
    # leaving the deletion uncommitted in the main tree. The spec-R5.4 clean-base guard then
    # correctly refused every following unattended isolated turn, so ONE unstaged deletion the tooling
    # itself left behind blocked 27 of that run's 42 items.
    #
    # `git mv` makes the relocation a SINGLE staged rename, so there are no halves to pair up and no
    # half to lose. This is also the pattern already used by every other relocating surface in the
    # package (`artifact_rename`, `plans_archive`, `plans_refs`, `research_refs`, `research_archive`,
    # `engine`); this function was the lone exception, which is why the class of bug reached only here.
    #
    # ORDER IS LOAD-BEARING: move FIRST, then write the updated content at the destination. Writing
    # first would leave an untracked file at `dest_path`, which makes `git mv` refuse (destination
    # exists), and the fallback would then hide the failure. `git_mv` already falls back to a plain
    # filesystem move when the source is untracked, so a not-yet-tracked artifact still relocates.
    moving = dest_path.resolve() != rec.path.resolve()
    if moving and rec.path.exists():
        _core.git_mv(
            repo_root,
            str(rec.path.relative_to(repo_root)),
            str(dest_path.relative_to(repo_root)),
        )

    _core.atomic_write(dest_path, updated_text)

    # Belt and braces: if the source somehow survived the move (a fallback that copied rather than
    # moved), drop it, because a surviving source is the very dirty-path residue described above.
    if moving and rec.path.exists():
        try:
            rec.path.unlink()
        except OSError:
            pass

    rewritten_citations: list[str] = []
    if (
        moving
        and getattr(args, "rewrite_citations", False)
        and not getattr(args, "dry_run", False)
    ):
        try:
            old_rel = rec.path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            old_rel = rec.path.as_posix()
        try:
            new_rel = dest_path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            new_rel = dest_path.as_posix()

        citation_changes = getattr(args, "_citation_changes", None)
        if citation_changes is None and (
            getattr(args, "agent", False) or getattr(args, "json", False)
        ):
            citation_changes = []
            setattr(args, "_citation_changes", citation_changes)

        from agent_workflows import artifact_refs as _refs

        rewritten_citations = _refs.post_relocation_citation_rewrite(
            repo_root,
            old_rel,
            new_rel,
            is_agent_or_json=bool(
                getattr(args, "agent", False) or getattr(args, "json", False)
            ),
            changes=citation_changes,
        )

    return StatusChangeResult(
        dest_path, norm_status, rewritten_citations, warning=_demotion_warning
    )


def _auto_index_types(
    touched_types: set[str],
    repo_root: Path,
    changes: list[Change] | None = None,
) -> None:
    """Automatically refresh manifest indices for modified artifact types that maintain an index."""
    for rtype in sorted(touched_types):
        if rtype == "plans":
            with contextlib.suppress(Exception):
                from agent_workflows import plans_index as _pidx

                _pidx.run_index(
                    argparse.Namespace(
                        dir=str(repo_root),
                        check=False,
                        as_agent=False,
                        json=False,
                        no_color=True,
                        limit=None,
                        quiet=True,
                    )
                )
                _, plans_dir = _pidx._dirs(argparse.Namespace(dir=str(repo_root)))
                if changes is not None and plans_dir.is_dir():
                    idx_json = plans_dir / "INDEX.json"
                    idx_md = plans_dir / "INDEX.md"
                    if idx_json.exists():
                        changes.append(
                            Change(
                                path=str(idx_json),
                                kind="update",
                                applied=True,
                                detail="manifest index auto-refreshed",
                            )
                        )
                    if idx_md.exists():
                        changes.append(
                            Change(
                                path=str(idx_md),
                                kind="update",
                                applied=True,
                                detail="manifest index auto-refreshed",
                            )
                        )
        elif rtype == "research":
            with contextlib.suppress(Exception):
                from agent_workflows import research_index as _ridx

                _ridx.run_index(
                    argparse.Namespace(
                        dir=str(repo_root),
                        check=False,
                        agent=False,
                        limit=None,
                        quiet=True,
                    )
                )
                _, res_dir = _ridx._roots(argparse.Namespace(dir=str(repo_root)))
                if changes is not None and res_dir.is_dir():
                    idx_json = res_dir / "INDEX.json"
                    idx_md = res_dir / "INDEX.md"
                    if idx_json.exists():
                        changes.append(
                            Change(
                                path=str(idx_json),
                                kind="update",
                                applied=True,
                                detail="manifest index auto-refreshed",
                            )
                        )
                    if idx_md.exists():
                        changes.append(
                            Change(
                                path=str(idx_md),
                                kind="update",
                                applied=True,
                                detail="manifest index auto-refreshed",
                            )
                        )


# Flags declared on any `set` family spelling that are safe to echo.
# This is an explicit ALLOW-LIST of non-path flags (IPD 5poaqh E-02, F-19).
# Path-valued flags (--dir, --evidence, --gate-dir, --scope-reason, --scope-ack)
# are deliberately EXCLUDED because:
# (1) CommandResult.to_agent_record calls assert_valid_agent_record, whose
#     _HOME_PATH_RE raises ValueError on an operator-local home path in any field;
# (2) normalizing to repo-relative paths produces invalid arguments from caller's cwd;
# (3) a hint without --dir already preserves today's cwd-dependent behavior (F-14).
# Mode flags (--agent, --json, --color, --no-color, --interactive, --no-interactive,
# --dry-run) and --yes are excluded because they are rendering/safety options, not part
# of the requested mutation.
_RETRY_FLAG_ALLOWLIST: tuple[tuple[str, str, bool], ...] = (
    # (dest, flag_name, is_value_flag)
    (
        "message",
        "--message",
        True,
    ),  # Always long form; -m is not on specs/backlog set (F-17)
    ("actor", "--actor", True),
    ("by_human", "--by-human", False),
    ("priority", "--priority", True),
    ("work_kind", "--work-kind", True),
    ("from_backlog", "--from-backlog", True),
    ("graduated_to", "--graduated-to", True),
    ("blocks_release", "--blocks-release", True),
    ("gate_kind", "--gate-kind", True),
    ("gate_ref", "--gate-ref", True),
    ("gate_summary", "--gate-summary", True),
    ("force", "--force", False),
    ("allow_open_questions", "--allow-open-questions", False),
    ("no_commit", "--no-commit", False),
    ("commit", "--commit", False),
    ("status", "--status", True),
    ("date", "--date", True),
)


def _retry_command(
    args: argparse.Namespace | None,
    raw_args: list[str],
    scoped_type: str | None = None,
    extra: list[str] | str | None = None,
) -> str:
    """Reconstruct an echo-safe retry command reproducing the caller's request.

    Adheres to three governing rules (IPD 5poaqh E-01):
    RULE 1: RECONSTRUCT THE VERB FROM THE ROUTING DEST, NOT FROM A GUESS.
      `cli._dispatch` sets `args.command` to the family name and a per-family dest to `set`.
      When a family dest equals 'set', emit `aw {args.command} set`. When `args.command == 'set'`,
      emit `aw set`. Preserves alias spellings (e.g. `aw spec set` vs `aw specs set`).
    RULE 2: FALL BACK WHEN NAMESPACE CARRIES NO ROUTING INFORMATION.
      Hand-built namespaces (e.g. from `work_cmd.run_finish` or `run_dependencies_set_command`)
      lack a `command` attribute. In that case, fall back to `aw set` with `raw_args`.
    RULE 3: PRESERVE LEADING-TYPE-TOKEN SPELLING.
      On the untyped verb, `run_set_command` adopts a leading type token out of `raw_args`,
      so echoing `raw_args` verbatim reproduces `aw set plans reviewed <sel>`. Do NOT
      additionally synthesize a type token from `scoped_type` for a typed verb.

    Echo-safe flag allow-list (IPD 5poaqh E-02):
      Appends caller's declared flags from `args` using an explicit ALLOW-LIST of non-path
      flags. All path-valued flags (--dir, --evidence, --gate-dir, --scope-reason, --scope-ack)
      are deliberately excluded because echoing operator-local home paths causes
      `CommandResult.to_agent_record` to fail schema validation with ValueError. Consequently,
      a command pasted from a different working directory than the original invocation may not
      resolve, which preserves the status quo behavior.
      Renderer/mode flags (--agent, --json, --color, --no-color, --interactive, --no-interactive,
      --dry-run) and --yes are not echoed; extra tokens are supplied by the caller.
      The flag --message is always echoed in long form because the -m alias is not declared
      on `aw specs set` or `aw backlog set`.
    """
    cmd = getattr(args, "command", None) if args is not None else None
    family_dest = (
        (
            (getattr(args, f"{cmd}_command", None) if cmd else None)
            or getattr(args, "specs_command", None)
            or getattr(args, "ipd_command", None)
            or getattr(args, "backlog_command", None)
            or getattr(args, "prompts_command", None)
        )
        if args is not None
        else None
    )

    if cmd and family_dest == "set":
        verb = f"aw {cmd} set"
    elif cmd == "set":
        verb = "aw set"
    else:
        # Rule 2 fallback
        verb = "aw set"

    tokens: list[str] = [verb]
    if raw_args:
        tokens.extend(raw_args)

    if args is not None:
        for dest, flag, is_value in _RETRY_FLAG_ALLOWLIST:
            val = getattr(args, dest, None)
            if is_value:
                if val is not None and str(val).strip():
                    tokens.append(flag)
                    tokens.append(shlex.quote(str(val)))
            else:
                if val:
                    tokens.append(flag)

    if extra:
        if isinstance(extra, str):
            tokens.append(extra)
        else:
            tokens.extend(extra)

    return " ".join(tokens)


def _delegate_plan_executed_to_finalize(
    plan_recs: list[ArtifactRecord],
    all_recs: list[ArtifactRecord],
    repo_root: Path,
    args: argparse.Namespace,
    term,
    scoped_type: str | None = "plans",
) -> int:
    """Route a plan -> `executed` `aw set`/`ipd set` request into the gated `aw ipd finalize` (Order wezhxg).

    The raw ungated plan-terminal move is removed: `executed` is unreachable without the begin
    receipt, scope reconciliation, three lint gates, attributed history, and lifecycle commit. This
    delegates transparently (OQ-03) rather than refusing-and-redirecting. A required gate input that
    is genuinely absent (a non-generic `--actor`) fails closed (exit 2) with the exact command to
    supply it - honest, never a fabricated actor, never a bare dead-end.
    """
    from agent_workflows import ipd_lifecycle as _life
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        NextAction,
        select_output,
    )

    ctx = select_output(args)

    # Refuse a mixed batch (plan-executed + others) to keep the transaction one-IPD and unambiguous.
    others = [r for r in all_recs if r not in plan_recs]
    if others:
        msg = (
            "moving a plan to 'executed' delegates into `aw ipd finalize` and must be run per-plan; "
            "do not mix it with other targets in one `aw set`."
        )
        if ctx.is_agent or ctx.is_json:
            return get_renderer(ctx).emit(
                CommandResult(
                    command="set", status="cannot-run", exit_code=2, summary=msg
                ),
                ctx,
            )
        term.status("fail", msg)
        return 2

    actor = (getattr(args, "actor", None) or "").strip()
    message = (getattr(args, "message", None) or "").strip()
    apply = not getattr(args, "dry_run", False)
    scope_reasons = _life._parse_scope_reason_flags(getattr(args, "scope_reason", None))
    scope_acks = _life._parse_scope_ack_flags(getattr(args, "scope_ack", None))

    overall = 0
    for rec in plan_recs:
        selector = rec.id6 or rec.path.name
        if not actor:
            extra_tokens = (
                ["--actor <agent/model>", "--message <summary>"]
                if not message
                else ["--actor <agent/model>"]
            )
            hint = _retry_command(
                args,
                ["executed", selector],
                scoped_type=scoped_type,
                extra=extra_tokens,
            )
            summary = (
                "moving a plan to 'executed' now delegates into the gated `aw ipd finalize`, which "
                "REQUIRES an attributed --actor <agent/model> (the machine-default is rejected). "
                f"Re-run: {hint}"
            )
            if ctx.is_agent or ctx.is_json:
                overall = 2
                get_renderer(ctx).emit(
                    CommandResult(
                        command="set",
                        status="cannot-run",
                        exit_code=2,
                        summary=summary,
                        next_actions=[
                            NextAction(command=hint, description="supply the actor")
                        ],
                    ),
                    ctx,
                )
                continue
            term.status("fail", summary)
            overall = 2
            continue

        result = _life.finalize(
            repo_root,
            rec.path,
            actor,
            message or f"finalize {selector} -> executed",
            apply=apply,
            scope_reasons=scope_reasons,
            scope_acks=scope_acks,
            plan_selector=selector,
        )
        if ctx.is_agent or ctx.is_json:
            status = {0: "clean", 1: "findings", 2: "cannot-run"}.get(
                result.exit_code, "cannot-run"
            )
            diags = [
                Diagnostic(
                    location=str(rec.path),
                    rule="IPD-FINALIZE",
                    detail=f,
                    severity="error",
                )
                for f in result.findings
            ]
            get_renderer(ctx).emit(
                CommandResult(
                    command="set",
                    status=status,
                    exit_code=result.exit_code,
                    summary=result.message,
                    diagnostics=diags,
                    data={"commit": result.commit},
                ),
                ctx,
            )
        else:
            prefix = {0: "", 1: "refused: ", 2: "error: "}.get(
                result.exit_code, "error: "
            )
            term.line(f"aw set -> ipd finalize: {prefix}{result.message}")
            for f in result.findings:
                term.line(f"  {f}")
        if result.exit_code != 0:
            overall = result.exit_code if overall == 0 else overall
    return overall


def _offer_self_commit(
    args: argparse.Namespace | None,
    repo_root: Path,
    touched_paths: list[str],
    target_status: str,
    scoped_type_canonical: str | None,
) -> None:
    """selfcommit jgcm68 E-05: offer to path-scoped-commit exactly the artifact file(s) this `set`
    rewrote. ONE integration in the shared engine covers every `set` variant
    (`aw set`/`ipd set`/`spec set`/`prompts set`/`backlog set`). Interactive-gated via child-01
    ``offer_commit``: TTY prompts, non-interactive-without-``--commit`` is a NO-OP; path-scoped, no
    push, no ``add -A``, unrelated dirty files never folded in.

    The regenerated INDEX.json/INDEX.md are deliberately NOT in this path-set. They are still
    refreshed on disk by `_auto_index_types` and still REPORTED in the agent-mode changes list; they
    are simply generated output that no `aw` verb commits (idxuntrack `4r0qp1` E-02)."""
    if not touched_paths:
        return
    from agent_workflows import git_commit_helper as _gch

    paths = list(touched_paths)
    label = scoped_type_canonical or "records"
    # jgcm68 D2: unstage exactly these touched paths first (a no-op for in-place set rewrites) so the
    # helper cleanly re-stages them; scoped to the verb's own paths, never global.
    _gch._git(repo_root, ["reset", "--quiet", "HEAD", "--", *paths])
    outcome = _gch.offer_commit(
        repo_root,
        paths,
        message=f"chore({label}): set status {target_status}",
        assume_yes=bool(
            getattr(args, "commit", False)
            or (
                getattr(args, "yes", False)
                and not (
                    getattr(args, "agent", False)
                    or getattr(args, "json", False)
                    or getattr(args, "as_agent", False)
                )
            )
        )
        if args
        else False,
        no_commit=bool(getattr(args, "no_commit", False)) if args else False,
        on_unrelated_staged="scope",
    )
    is_agent_or_json = (
        bool(
            getattr(args, "agent", False)
            or getattr(args, "json", False)
            or getattr(args, "as_agent", False)
        )
        if args
        else False
    )
    if is_agent_or_json:
        if outcome.status == _gch.STATUS_ERROR:
            sys.stderr.write(f"warning: self-commit skipped: {outcome.message}\n")
        return
    if outcome.status == _gch.STATUS_COMMITTED:
        print(f"Committed {len(outcome.staged)} path(s): {outcome.commit}:")
        for p in outcome.staged:
            print(p)
    elif outcome.status == _gch.STATUS_ERROR:
        print(f"warning: self-commit skipped: {outcome.message}")


def _refuse_unsafe_descriptive(
    verb: str,
    flag: str,
    value: str | None,
    *,
    bound_length: bool = True,
) -> str | None:
    """Judge one descriptive value against Section 8.8 output-safety.

    Delegates to backlog._refuse_unsafe_descriptive to keep refusal wording byte-identical
    across trees without a third copy (IPD 4gwgo3 E-01).
    """
    from agent_workflows import backlog as _backlog

    return _backlog._refuse_unsafe_descriptive(
        verb, flag, value, bound_length=bound_length
    )


def run_set_command(
    raw_args: list[str],
    scoped_type: str | None = None,
    repo_root: Path | None = None,
    args: argparse.Namespace | None = None,
    term: Term | None = None,
) -> int:
    """Core execution engine for `aw set`, `aw ipd set`, `aw spec set`, etc."""
    if term is None:
        term = Term()
    if repo_root is None:
        from agent_workflows.project_context import resolve_verb_repo_root

        repo_root = resolve_verb_repo_root(getattr(args, "dir", None) if args else None)

    if args is None:
        args = argparse.Namespace()

    if not raw_args:
        term.status("fail", "aw set: missing status and target selector(s).")
        return 2

    first_tok = raw_args[0]
    target_status: str
    selector_tokens: list[str]

    if (
        scoped_type is None
        and canonical_type(first_tok) is not None
        and len(raw_args) >= 3
    ):
        scoped_type = canonical_type(first_tok)
        target_status = raw_args[1]
        selector_tokens = raw_args[2:]
    else:
        target_status = raw_args[0]
        selector_tokens = raw_args[1:]

    if not selector_tokens:
        term.status(
            "fail",
            "aw set: at least one target selector (id6, setid, or filename) is required.",
        )
        return 2

    # setidhard bwgyum E-04: validate + canonicalize `--graduated-to` ONCE, here, BEFORE any artifact
    # is resolved or written, so a malformed setid refuses with exit 2 instead of being persisted and
    # then reported by `aw check`. Canonicalizing at the entry (rather than per record inside
    # `apply_status_change`) means every target of a multi-selector call gets the same bytes, and the
    # write site stays a pure write like its four neighbours. The shape authority is the shared
    # `plans.is_set_id_valid`, reached through `releases.canonicalize_graduated_to`; `-` clears.
    if getattr(args, "graduated_to", None) is not None:
        from agent_workflows import releases as _releases_gt

        _gt_canonical, _gt_err = _releases_gt.canonicalize_graduated_to(
            getattr(args, "graduated_to", None)
        )
        if _gt_err:
            term.status("fail", f"aw set: {_gt_err}")
            return 2
        args.graduated_to = _gt_canonical

    # IPD izh17y E-03: validate `--from-backlog` value BEFORE any artifact is resolved or written,
    # so an unresolvable backlog id refuses with exit 2 instead of creating a dangling link.
    # Resolves via existing authority `backlog.existing_backlog_ids` (P8: no second scanner).
    # An empty id set skips the refusal so an invisible backlog corpus cannot make every write fail.
    # DELIBERATE DIVERGENCE FROM CHECKER (F-12): `releases.check_from_backlog` has no empty-set skip
    # and its own docstring explicitly records that asymmetry ("THE TWO BACK-LINK TWINS DISAGREE ON
    # FAIL-SAFETY, AND THIS ONE IS THE LESS SAFE ... Do NOT 'harmonize' that guard away to match this
    # function; the difference is a known gap here, not a standard to spread"). The setter takes the
    # safe posture rather than copying the checker's less-safe posture.
    fb_val = getattr(args, "from_backlog", None)
    if fb_val is not None and fb_val != "-":
        from agent_workflows import backlog as _backlog

        known_backlog = _backlog.existing_backlog_ids(repo_root)
        if known_backlog and fb_val not in known_backlog:
            term.status(
                "fail",
                f"aw set: unresolvable backlog id '{fb_val}' (does not resolve to an existing backlog item)",
            )
            return 2

    # IPD 0ykozn E-02 (review finding PR-504): validate `--from-spec` value BEFORE any artifact
    # is resolved or written, so an unresolvable spec id6 refuses with a nonzero exit instead of
    # creating a dangling link.
    # THE ASYMMETRY WITH `--from-backlog` IS DELIBERATE AND MUST BE STATED IN THE CODE:
    # `--from-backlog` performs no value validation at all, so an unresolvable backlog ID is
    # caught only afterwards by `check.from-backlog-dangling`. Adding a refusal here is
    # deliberately STRICTER than its twin, because adding a refusal costs nothing while the
    # alternative writes a known-bad link that errors on `check.from-spec-dangling`.
    # The id is resolved against the SAME `_iter_spec_records` plus `specs._existing_spec_ids`
    # union E-04 uses, reached through the shared `check_engine.known_spec_ids` helper rather
    # than a second construction (P8). An EMPTY union skips the refusal so an invisible spec
    # corpus cannot make every write fail.
    fs_val = getattr(args, "from_spec", None)
    if fs_val is not None and fs_val != "-":
        from agent_workflows import check_engine as _ce

        known = _ce.known_spec_ids(repo_root)
        if known and fs_val not in known:
            term.status(
                "fail",
                f"aw set: unresolvable spec id '{fs_val}' (does not resolve to an existing spec)",
            )
            return 2

    # relexempt ghna7l E-05: validate release exemption flags BEFORE resolving or writing anything
    _rel_exempt_kind = getattr(args, "release_exempt_kind", None)
    _rel_exempt_ref = getattr(args, "release_exempt_ref", None)
    if _rel_exempt_kind is not None or _rel_exempt_ref is not None:
        from agent_workflows import backlog as _backlog

        _exempt_err = _backlog.validate_release_exempt_flags(
            "aw set", _rel_exempt_kind, _rel_exempt_ref
        )
        if _exempt_err:
            term.status("fail", _exempt_err)
            return 2

    # IPD 4gwgo3 E-02, E-03: validate descriptive and identity fields BEFORE resolving or writing
    # anything, so an unsafe value carrying newlines, control characters, or exceeding length bounds
    # refuses with exit 2 without mutating artifacts or forging workflow history / front matter
    # across any tree. Mode is line-integrity only for --message (no length bound); bounded for
    # --actor, --gate-ref, --gate-summary, --blocks-release, and --gate-kind.
    for _val, _flag, _bound in [
        (getattr(args, "message", None), "--message", False),
        (getattr(args, "actor", None), "--actor", True),
        (getattr(args, "gate_ref", None), "--gate-ref", True),
        (getattr(args, "gate_summary", None), "--gate-summary", True),
        (getattr(args, "blocks_release", None), "--blocks-release", True),
        (getattr(args, "gate_kind", None), "--gate-kind", True),
    ]:
        if _val is not None:
            _err = _refuse_unsafe_descriptive(
                "aw set", _flag, _val, bound_length=_bound
            )
            if _err:
                term.status("fail", _err)
                return 2

    scoped_type_canonical = canonical_type(scoped_type)

    all_records = inventory_all_artifacts(repo_root, scoped_type=scoped_type_canonical)

    resolved_by_token: dict[str, list[ArtifactRecord]] = {}
    matched_records: list[ArtifactRecord] = []
    seen_paths: set[str] = set()

    force = bool(getattr(args, "force", False))
    for tok in selector_tokens:
        matches = match_selector(
            tok, all_records, repo_root, scoped_type=scoped_type_canonical
        )
        if not matches:
            if scoped_type_canonical:
                term.status(
                    "fail", f"No {scoped_type_canonical} artifact matched '{tok}'."
                )
            else:
                term.status("fail", f"No artifact matched '{tok}'.")
            return 2

        # IPD laykok E-07: kind-aware ambiguity for the MUTATING `set` verb. A setid legitimately
        # transitions a whole Set (act on all, no --force); a UNIQUE-id collision (id6/path/stem)
        # ALWAYS refuses; a filename SUBSTRING multi-match refuses unless --force. Determine the
        # winning kind via the unified resolver (scoped to the matched type when known).
        if len(matches) > 1:
            _kind = None
            _probe_type = scoped_type_canonical or (
                matches[0].record_type if matches else None
            )
            if _probe_type:
                _kind = _sel.resolve(repo_root, _probe_type, tok).kind
            if _kind == _sel.MATCH_SETID:
                pass  # intentional multi-target
            elif _kind in _sel.UNIQUE_KINDS:
                cand = "\n  ".join(str(m.path) for m in matches)
                term.status(
                    "fail",
                    f"Selector '{tok}' is a {_kind} collision matching multiple files "
                    f"(a data bug to fix, not overridable by --force):\n  {cand}",
                )
                return 2
            elif not force:
                cand = "\n  ".join(str(m.path) for m in matches)
                term.status(
                    "fail",
                    f"Selector '{tok}' is ambiguous ({_kind or 'substring'}) matching multiple "
                    f"files; pass --force to act on all:\n  {cand}",
                )
                return 2

        # setidfix `w2y5ac` E-02: THIS REFUSAL IS LIVE AND LOAD-BEARING. DO NOT DELETE IT AS DEAD
        # CODE. `match_selector` does narrow `record_types` to `scoped_type` (its `if scoped_type:`
        # branch setting `record_types = (canonical,)`), so it is
        # tempting to conclude a scoped call can never surface a foreign type and that this branch is
        # unreachable. That conclusion is FALSE FOR ONE SELECTOR KIND: the pre-filter only narrows
        # which types the RESOLVER is QUERIED for, while `selectors.resolve`'s FIRST precedence rule
        # (direct PATH) matches an existing FILE regardless of the type it was asked about, after
        # which `detect_artifact_type` reads the record's real type off the real path. MEASURED:
        # `match_selector(<a plan path>, scoped_type="specs")` returns one match of type `plans`.
        # So a type-scoped verb handed a foreign-type PATH reaches here, and this is the ONLY guard
        # between it and a cross-type write. Deleting it was measured to let
        # `aw specs set approved <a plan path> --yes --by-human` rewrite the PLAN to `approved` and
        # append a forged `--by-human` human-approval attestation to that plan's own history. Pinned
        # by `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing`; if that test ever
        # looks removable, re-read this comment first.
        if scoped_type_canonical:
            mismatches = [m for m in matches if m.record_type != scoped_type_canonical]
            if mismatches:
                mismatch_types = sorted({m.record_type for m in mismatches})
                term.status(
                    "fail",
                    f"Type mismatch: selector '{tok}' resolved to artifact(s) of type {mismatch_types}, "
                    f"but command is scoped to '{scoped_type_canonical}'. Refusing before making changes.",
                )
                return 2

        # setidfix `w2y5ac` E-03 + E-04, implementing spec `2lcqno` N1/N4: a setid is a SHARED
        # cross-type TOPIC label, so ONE token routinely names artifacts of several types. On the
        # UNTYPED verb (`aw set`, the only surface reached with `scoped_type=None`) that makes the
        # operator's intent genuinely unknown, and BOTH previous behaviors were wrong:
        #   * when the requested status was invalid for one matched type, the per-record
        #     `validate_transition_allowed` loop below died on whichever foreign artifact it reached
        #     first, reporting an unrelated type's vocabulary (measured: `aw set approved
        #     agentadhere` naming a BACKLOG item's valid-status list when the operator plainly meant
        #     the 7-plan Set);
        #   * when the status was valid for SEVERAL matched types - the COMMON case, since 15
        #     statuses in `TYPE_STATUSES` are valid for two or more types - it silently wrote ALL of
        #     them (measured: `aw set to-review <setid shared by a plan and a spec> --yes` rewrote
        #     both at exit 0). N4 forbids exactly that: report the CANDIDATES BY TYPE, never guess.
        # SO WE REFUSE AND ASK FOR THE TYPE, with ONE code path covering both cases, and print the
        # candidates grouped by type with a RUNNABLE disambiguating command for each.
        # THE DISAMBIGUATING SPELLING ALREADY SHIPS: `run_set_command` accepts a LEADING TYPE TOKEN
        # on the untyped verb (see the `canonical_type(first_tok)` adoption at the top of this
        # function), so `aw set <type> <status> <selector>` resolves within one type today. DO NOT
        # ADD A `--type` FLAG; it would be a second spelling for a shipped one.
        # NOT OVERRIDABLE BY `--force`, on the id6-collision precedent above: `--force` means "yes,
        # act on all the files this ONE type matched", and cross-type fan-out is a different
        # question (which tree did you mean?) whose answer is a type scope. A confirmation flag was
        # the considered alternative and was REJECTED here because plan `4bc1nd` (Set `setterguard`,
        # carrying backlog `f5pttg`) OWNS the confirmation-before-write question for every setter;
        # implementing confirmation here too would be a second implementation of that fix.
        # WITHIN-TYPE setid fan-out is untouched and stays deliberate (IPD `laykok` E-07): this
        # refusal fires only when the matched records span MORE THAN ONE type.
        if scoped_type_canonical is None:
            matched_types = sorted({m.record_type for m in matches})
            if len(matched_types) > 1:
                by_type: dict[str, list[ArtifactRecord]] = {}
                for m in matches:
                    by_type.setdefault(m.record_type, []).append(m)
                width = max(len(t) for t in matched_types)
                lines = [
                    f"Selector '{tok}' names artifacts of {len(matched_types)} types "
                    f"({', '.join(matched_types)}), so 'aw set' cannot tell which you meant. "
                    "A setid is a shared cross-type topic label, not an identity; name the type "
                    "you meant. Candidates by type:"
                ]
                for rtype in matched_types:
                    n = len(by_type[rtype])
                    lines.append(
                        f"  {rtype.ljust(width)}  {n} artifact(s): "
                        f"aw set {rtype} {target_status} {tok}"
                    )
                lines.append("Refusing before making changes; nothing was written.")
                term.status("fail", "\n".join(lines))
                return 2

        resolved_by_token[tok] = matches
        for m in matches:
            rp_key = str(m.path.resolve())
            if rp_key not in seen_paths:
                seen_paths.add(rp_key)
                matched_records.append(m)

    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        Diagnostic,
        NextAction,
        select_output,
    )

    ctx = select_output(args)
    for rec in matched_records:
        ok, err_msg = validate_transition_allowed(rec, target_status, args, repo_root)
        if not ok:
            if ctx.is_agent or ctx.is_json:
                res = CommandResult(
                    command="set",
                    status="findings",
                    exit_code=1,
                    summary=f"Validation error on {rec.path.name}: {err_msg}",
                    diagnostics=[
                        Diagnostic(
                            location=str(rec.path),
                            rule="status.invalid_transition",
                            detail=err_msg or "transition not allowed",
                            severity="error",
                        )
                    ],
                )
                return get_renderer(ctx).emit(res, ctx)
            term.status(
                "fail",
                f"Validation error on {rec.path.name}: {err_msg}. Refusing before making changes.",
            )
            return 1

    # gatebypass 47ttnv E-01/E-02/E-03: release-gate close-legitimacy check for backlog records.
    # Calls the single shared predicate `check_engine.evaluate_blocking_close` on the positional
    # dispatch path so both spellings of `aw backlog set` enforce the close-legitimacy rule.
    # Placed in the pre-flight loop region:
    #   (a) BEFORE `is_dry_run`, so a dry run on an illegitimate close refuses rather than previewing;
    #   (b) BEFORE `apply_status_change`, so a refusal writes nothing and moves nothing;
    #   (c) preserving the all-or-nothing batch contract ("Refusing before making changes").
    # The predicate is evaluated against `repo_root`: the positional path has no `--gate-dir` concept
    # (honored only by `backlog.run_set` for runner split-tree lane closes).
    from agent_workflows import check_engine as _ce
    from agent_workflows import releases as _releases

    backlog_close_verdicts: dict[Path, _ce.CloseVerdict] = {}
    for rec in matched_records:
        if rec.record_type != "backlog":
            continue

        norm_target = normalize_target_status(target_status, rec.record_type)

        # Compute gate-relevant post-mutation item text for the predicate (E-02).
        # Ensures same-call de-gating (`--blocks-release -`) and same-call gate defaulting
        # are judged against the state the item will actually carry.
        item_text = rec.raw_text
        if getattr(args, "priority", None) is not None:
            item_text = _releases.set_priority_line(
                item_text, getattr(args, "priority", None)
            )
        if getattr(args, "work_kind", None) is not None:
            item_text = _releases.set_work_kind_line(
                item_text, getattr(args, "work_kind", None)
            )

        br_arg = getattr(args, "blocks_release", None)
        if br_arg is not None:
            item_text = _releases.set_blocks_release_line(item_text, br_arg)
        else:
            _current_text = item_text
            _effective_kind = (
                getattr(args, "work_kind", None)
                or _backlog_mod.parse_item(_current_text).kind
            )
            _existing_br = _sel.read_front_matter_blocks_release(_current_text)
            _parsed_item = _backlog_mod.parse_item(_current_text)
            _is_exempt = bool(
                _parsed_item.release_exempt_kind
                and _parsed_item.release_exempt_ref
                and _parsed_item.release_exempt_kind != "-"
                and _parsed_item.release_exempt_ref != "-"
            )
            _gate_default, _ = _backlog_mod.decide_gate_default(
                repo_root,
                kind=_effective_kind,
                status=norm_target,
                explicit_blocks_release=None,
                existing_blocks_release=_existing_br,
                is_exempt=_is_exempt,
            )
            if _gate_default is not None:
                item_text = _releases.set_blocks_release_line(
                    _current_text, _gate_default
                )

        ev_arg = getattr(args, "evidence", None)
        prior_prio = _backlog_mod.parse_item(rec.raw_text).priority

        verdict = _ce.evaluate_blocking_close(
            repo_root,
            rec.path,
            norm_target,
            evidence=ev_arg,
            item_text=item_text,
            prior_priority=prior_prio,
        )

        prefix = (
            "aw backlog set"
            if (scoped_type_canonical == "backlog" or scoped_type == "backlog")
            else "aw set"
        )
        if not verdict.legitimate and verdict.severity == "error":
            if ctx.is_agent or ctx.is_json:
                res = CommandResult(
                    command="set",
                    status="findings",
                    exit_code=1,
                    summary=f"refused: {verdict.reason}",
                    diagnostics=[
                        Diagnostic(
                            location=str(rec.path),
                            rule=verdict.rule
                            or "check.blocking-item-closed-without-gate",
                            detail=verdict.reason,
                            severity="error",
                        )
                    ],
                )
                return get_renderer(ctx).emit(res, ctx)
            sys.stderr.write(f"{prefix}: refused: {verdict.reason}.\n")
            for fix in verdict.fixes:
                sys.stderr.write(f"  - {fix}\n")
            return 1

        if verdict.severity == "warn":
            sys.stderr.write(f"{prefix}: warning: {verdict.reason}.\n")

        backlog_close_verdicts[rec.path] = verdict

    # gradcover sbiv1j E-02 / E-03: refuse aw backlog set graduated and aw specs set implementing
    # when handoff is not ready. Evaluated in the pre-flight loop before any file write or move.
    for rec in matched_records:
        norm_target = normalize_target_status(target_status, rec.record_type)
        if (
            rec.record_type == "backlog"
            and norm_target == "graduated"
            and rec.status != "graduated"
        ):
            handoff_res = _ce.evaluate_handoff_ready(repo_root, "backlog", rec.id6)
            if not handoff_res.ready:
                prefix = (
                    "aw backlog set"
                    if (scoped_type_canonical == "backlog" or scoped_type == "backlog")
                    else "aw set"
                )
                if ctx.is_agent or ctx.is_json:
                    res = CommandResult(
                        command="set",
                        status="findings",
                        exit_code=1,
                        summary=f"refused: handoff for backlog {rec.id6} is not ready",
                        diagnostics=[
                            Diagnostic(
                                location=str(rec.path),
                                rule="check.graduation-incomplete",
                                detail=f"[{f.code}] {f.detail}",
                                severity="error",
                            )
                            for f in handoff_res.findings
                        ],
                        data={
                            "id6": rec.id6,
                            "source_type": "backlog",
                            "ready": False,
                            "findings": [
                                {
                                    "code": f.code,
                                    "plan_id6": f.plan_id6,
                                    "detail": f.detail,
                                    "remedy": f.remedy,
                                }
                                for f in handoff_res.findings
                            ],
                        },
                    )
                    return get_renderer(ctx).emit(res, ctx)
                sys.stderr.write(
                    f"{prefix}: refused: handoff for backlog {rec.id6} is not ready.\n"
                )
                for f in handoff_res.findings:
                    subj = f" [{f.plan_id6}]" if f.plan_id6 else ""
                    sys.stderr.write(f"  - [{f.code}]{subj} {f.detail}\n")
                    if f.remedy:
                        sys.stderr.write(f"    Remedy: {f.remedy}\n")
                return 1

        if (
            rec.record_type == "specs"
            and norm_target == "implementing"
            and rec.status == "approved"
        ):
            handoff_res = _ce.evaluate_handoff_ready(repo_root, "spec", rec.id6)
            if not handoff_res.ready:
                prefix = (
                    "aw specs set"
                    if (scoped_type_canonical == "specs" or scoped_type == "specs")
                    else "aw set"
                )
                if ctx.is_agent or ctx.is_json:
                    res = CommandResult(
                        command="set",
                        status="findings",
                        exit_code=1,
                        summary=f"refused: handoff for spec {rec.id6} is not ready",
                        diagnostics=[
                            Diagnostic(
                                location=str(rec.path),
                                rule="check.graduation-incomplete",
                                detail=f"[{f.code}] {f.detail}",
                                severity="error",
                            )
                            for f in handoff_res.findings
                        ],
                        data={
                            "id6": rec.id6,
                            "source_type": "spec",
                            "ready": False,
                            "findings": [
                                {
                                    "code": f.code,
                                    "plan_id6": f.plan_id6,
                                    "detail": f.detail,
                                    "remedy": f.remedy,
                                }
                                for f in handoff_res.findings
                            ],
                        },
                    )
                    return get_renderer(ctx).emit(res, ctx)
                sys.stderr.write(
                    f"{prefix}: refused: handoff for spec {rec.id6} is not ready.\n"
                )
                for f in handoff_res.findings:
                    subj = f" [{f.plan_id6}]" if f.plan_id6 else ""
                    sys.stderr.write(f"  - [{f.code}]{subj} {f.detail}\n")
                    if f.remedy:
                        sys.stderr.write(f"    Remedy: {f.remedy}\n")
                return 1

    # ipdgates Order wezhxg: a request to move a PLAN to `executed` (or its `done` alias) MUST NOT
    # use the raw ungated move - it transparently DELEGATES into the gated `aw ipd finalize`
    # transaction (begin receipt + scope reconciliation + three gates + attributed history +
    # rollback). Keyed on record_type == "plans" AND normalized target `executed` (NOT the status
    # token alone, because PROMPTS share the `executed`/`done` tokens). All other transitions -
    # nonterminal plan (draft/to-review/reviewed/approved), plan RETIREMENT (superseded/not-executed),
    # and every non-plan artifact terminal transition - are UNCHANGED below.
    _plan_executed = [
        rec
        for rec in matched_records
        if rec.record_type == "plans"
        and normalize_target_status(target_status, rec.record_type) == "executed"
    ]
    if _plan_executed:
        return _delegate_plan_executed_to_finalize(
            _plan_executed,
            matched_records,
            repo_root,
            args,
            term,
            scoped_type=scoped_type,
        )

    # setterguard `4bc1nd` E-02: REFUSE WALKING A PLAN BACKWARDS OUT OF A TERMINAL DISPOSITION.
    # There was a gate for entering `executed` (the delegation directly above) and NONE for leaving
    # it, so `executed -> approved` took the raw ungated path. MEASURED 2026-09-10: a bare
    # `aw ipd set approved <setid>` reverted SEVEN plans out of `.aw/records/plans/executed/` at exit
    # 0, fabricating a regression of a completed Set. `AGENTS.md` already forbids re-opening an
    # executed plan in place and directs a corrective IPD instead, so this ENFORCES a stated contract
    # rather than inventing policy.
    #
    # THIS IS A SECOND, INDEPENDENT GUARD AND IS DELIBERATELY ABOVE THE `--yes` CHECK: confirming you
    # meant to run a bulk transition is a different question from being allowed to un-execute a plan,
    # so `--yes` must NOT satisfy it.
    #
    # KEYED LIKE THE FORWARD GATE, for the same reasons: `record_type == "plans"` (so PROMPTS, which
    # share the `executed`/`done` tokens, and SPECS, which have their own transition table permitting
    # `implemented -> deferred` and `superseded -> draft`, are untouched BY CONSTRUCTION), plus the
    # NORMALIZED target rather than the raw token.
    #
    # THE TERMINAL SET IS DERIVED, NEVER RE-LISTED (`_plans_mod.TERMINAL`), per GUIDING_PRINCIPLES P8
    # and the precedent stated in the `backlog` entry of `TYPE_STATUSES` above: a re-listed copy is
    # what desynced this setter once already.
    #
    # THE CURRENT STATUS IS CASE-FOLDED, and that is a CORRECTNESS requirement rather than tidiness.
    # `read_artifact_record` captures the on-disk token VERBATIM with no normalization, and 25 of 479
    # plans in `.aw/records/plans/executed/` carry an uppercase `- Status: EXECUTED` or `- Status:
    # DONE` from the pre-vocabulary era. A guard comparing `rec.status` directly against lowercase
    # `TERMINAL` would silently miss exactly those 25 files. The `done` alias is routed through
    # `normalize_target_status` for the same reason.
    #
    # FORWARD moves INTO a terminal state are UNAFFECTED: retirement (`reviewed -> superseded`,
    # `-> not-executed`) stays allowed, because the target is terminal too. An over-broad guard here
    # would have blocked the very cleanup that discovered this bug, which performed three retirements.
    _norm_for_plans = normalize_target_status(target_status, "plans")
    _terminal = {s.strip().lower() for s in _plans_mod.TERMINAL}
    _reopened = (
        [
            rec
            for rec in matched_records
            if rec.record_type == "plans"
            and normalize_target_status((rec.status or ""), "plans").strip().lower()
            in _terminal
        ]
        if _norm_for_plans not in _terminal
        else []
    )
    if _reopened and not getattr(args, "allow_terminal_reopen", False):
        # A DEDICATED override flag, NOT `--force`. `--force` already means "act on all of an
        # ambiguous multi-match" in this same function, and overloading one flag to also mean "yes,
        # un-execute a completed plan" would make it answer two unrelated risk questions at once, so
        # a caller disambiguating a filename substring would silently acquire reopen authority.
        # Follows `--allow-open-questions` in all three of its properties (apprvguard `d7bnhc` E-06):
        # a named flag, declared on EVERY surface routing here so the gate cannot be dodged by
        # choosing another spelling, and RECORDED IN THE ARTIFACT'S actor string (see
        # `apply_status_change`) so the override is auditable in the FILE and not only in a shell
        # history. OQ-01 recommended exactly this shape over an absolute refusal, on the grounds that
        # a refusal with no escape hatch gets routed around by hand-editing, which is less auditable.
        _listing = "\n".join(
            f"  {rec.path.name}  (- Status: {rec.status or '-'})" for rec in _reopened
        )
        _summary = (
            f"refusing to move {len(_reopened)} plan(s) BACKWARDS out of a terminal disposition "
            f"to '{_norm_for_plans}'. A terminal plan is a historical record: re-opening it in place "
            "would assert that completed, validated work is pending again. AGENTS.md directs a "
            "CORRECTIVE IPD for a post-execution gap, not an in-place edit of the executed plan. "
            "If this plan reached a terminal state in error, pass --allow-terminal-reopen (recorded "
            "in the artifact's history)."
        )
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="set",
                status="cannot-run",
                exit_code=2,
                summary=_summary,
                diagnostics=[
                    Diagnostic(
                        location=str(rec.path),
                        rule="status.terminal_reopen_refused",
                        detail=(
                            f"current status '{rec.status or '-'}' is terminal; target "
                            f"'{_norm_for_plans}' is not"
                        ),
                        severity="error",
                    )
                    for rec in _reopened
                ],
                next_actions=[
                    NextAction(
                        command="aw ipd scaffold --title <corrective plan title>",
                        description="Write a corrective IPD instead (the AGENTS.md route)",
                    ),
                    NextAction(
                        command=_retry_command(
                            args,
                            raw_args,
                            scoped_type=scoped_type,
                            extra=["--allow-terminal-reopen", "--yes"],
                        ),
                        description="Override: reopen anyway, recorded in the artifact history",
                    ),
                ],
                verified=False,
                complete=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        term.status("fail", f"{_summary}\nRefusing; nothing was written:\n{_listing}")
        return 2

    # E-05: Require an explicit --message for every backward plan transition.
    from agent_workflows.ipd_lifecycle import _LEGAL_BACKWARD_EDGES, _status_rank

    _explicit_message = (getattr(args, "message", None) or "").strip()
    _backward_plan_moves: list[tuple[ArtifactRecord, str, str]] = []
    for rec in matched_records:
        if rec.record_type == "plans":
            _cur = (
                normalize_target_status(rec.status or "draft", "plans").strip().lower()
            )
            _tgt = normalize_target_status(target_status, "plans").strip().lower()
            if (_cur, _tgt) in _LEGAL_BACKWARD_EDGES:
                _backward_plan_moves.append((rec, _cur, _tgt))

    if _backward_plan_moves and not _explicit_message:
        _err_summary = "aw set: backward plan transition requires an explicit --message"
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="set",
                status="cannot-run",
                exit_code=2,
                summary=_err_summary,
                diagnostics=[
                    Diagnostic(
                        location=str(r.path),
                        rule="status.backward_plan_message_required",
                        detail=f"demoting plan from '{c}' to '{t}' requires an explicit --message",
                        severity="error",
                    )
                    for r, c, t in _backward_plan_moves
                ],
                next_actions=[
                    NextAction(
                        command=_retry_command(
                            args,
                            raw_args,
                            scoped_type=scoped_type,
                            extra=['--message "<reason>"'],
                        ),
                        description="Specify --message with the demotion reason",
                    )
                ],
                verified=False,
                complete=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        term.status(
            "fail",
            f"{_err_summary} explaining why the plan was demoted; refusing before making changes.",
        )
        return 2

    # E-01 / E-02 / E-03: Orchestrator review readiness gate.
    from agent_workflows import orchestrator_readiness as _orch_readiness
    from agent_workflows import ipd_lint as _ipd_lint

    _gated_orchestrators: list[tuple[ArtifactRecord, str]] = []
    _ready_forward_targets = frozenset(
        {"to-review", "reviewed", "approved", "auto-approved"}
    )

    for rec in matched_records:
        if rec.record_type == "plans":
            _tgt = normalize_target_status(target_status, "plans").strip().lower()
            if _tgt in _ready_forward_targets:
                _doc = _ipd_lint.parse(rec.raw_text)
                _kind = (_doc.meta_fields.get("Kind") or "").strip().lower()
                if _kind == "orchestrator":
                    _cur = (
                        normalize_target_status(rec.status or "draft", "plans")
                        .strip()
                        .lower()
                    )
                    if _status_rank(_tgt) > _status_rank(_cur):
                        _gated_orchestrators.append((rec, _tgt))

    if _gated_orchestrators:
        _unready_results: list[_orch_readiness.ReviewReadiness] = []
        for orch_rec, orch_target in _gated_orchestrators:
            orch_doc = _ipd_lint.parse(orch_rec.raw_text)
            raw_set = (orch_doc.meta_fields.get("Set") or "").strip()
            orch_setid = (
                raw_set.split("(")[0].strip().split()[0].strip() if raw_set else ""
            )

            status_overrides: dict[str, str] = {}
            for other_rec in matched_records:
                if other_rec.record_type == "plans":
                    other_doc = _ipd_lint.parse(other_rec.raw_text)
                    other_set_raw = (other_doc.meta_fields.get("Set") or "").strip()
                    other_setid = (
                        other_set_raw.split("(")[0].strip().split()[0].strip()
                        if other_set_raw
                        else ""
                    )
                    if other_setid == orch_setid:
                        other_id6 = (other_doc.meta_fields.get("Id") or "").strip()
                        if other_id6:
                            other_target = (
                                normalize_target_status(target_status, "plans")
                                .strip()
                                .lower()
                            )
                            status_overrides[other_id6] = other_target

            r_res = _orch_readiness.review_readiness(
                repo_root,
                orch_rec.path,
                ask=False,
                status_overrides=status_overrides,
            )
            if not r_res.ready:
                _unready_results.append(r_res)

        if _unready_results:
            cmd_str = "ipd set" if scoped_type_canonical == "plans" else "set"
            if ctx.is_agent or ctx.is_json:
                findings_payload = [
                    {
                        "code": f.code,
                        "subject": f.subject,
                        "detail": f.detail,
                        "remedy": f.remedy,
                    }
                    for r in _unready_results
                    for f in r.findings
                ]
                rec_payload = {
                    "schema": "aw.agent/v1",
                    "kind": "result",
                    "cmd": cmd_str,
                    "exit": 1,
                    "outcome": "findings",
                    "verified": True,
                    "complete": True,
                    "summary": (
                        f"orchestrator {_unready_results[0].id6} is not ready for review ({len(_unready_results[0].findings)} finding(s))"
                        if len(_unready_results) == 1
                        else f"{len(_unready_results)} orchestrator(s) are not ready for review ({len(findings_payload)} finding(s))"
                    ),
                    "data": {
                        "id6": _unready_results[0].id6
                        if len(_unready_results) == 1
                        else ",".join(r.id6 for r in _unready_results),
                        "setid": _unready_results[0].setid
                        if len(_unready_results) == 1
                        else ",".join(r.setid for r in _unready_results),
                        "ready": False,
                        "finding_codes": [f["code"] for f in findings_payload],
                        "findings": findings_payload,
                    },
                }
                if ctx.is_json:
                    print(json.dumps(rec_payload, indent=2))
                else:
                    from agent_workflows import agent_schema as _as

                    print(_as.render_jsonl_record(rec_payload), end="")
                return 1

            for r in _unready_results:
                term.line(_orch_readiness.render_human(r))
            return 1

    # E-02: Sort writes so children are applied first, orchestrators last.
    def _plan_is_orchestrator(r: ArtifactRecord) -> int:
        if r.record_type != "plans":
            return 0
        from agent_workflows import ipd_lint as _ipd_lint_sort

        doc = _ipd_lint_sort.parse(r.raw_text)
        return (
            1
            if (doc.meta_fields.get("Kind") or "").strip().lower() == "orchestrator"
            else 0
        )

    matched_records.sort(key=_plan_is_orchestrator)

    is_dry_run = getattr(args, "dry_run", False)
    yes = getattr(args, "yes", False) or getattr(args, "assume_yes", False)

    # setterguard `4bc1nd` E-01: THE CONFIRMATION REFUSAL APPLIES TO EVERY CALLER, not only one
    # renderer's. This predicate used to read `(ctx.is_agent or ctx.is_json) and not is_dry_run and
    # not yes`, so the speed bump before a destructive bulk write existed ONLY for a caller that
    # passed `--agent` or `--json`.
    #
    # WHAT THAT CONDITION ACTUALLY TESTED, stated precisely because the obvious reading is wrong: it
    # tested THE `--agent`/`--json` FLAGS AND NOTHING ELSE. `select_output` consults no `isatty` for
    # mode selection at all (`result_types.select_output`, whose docstring now says so explicitly
    # after ttyflags `yaxr4i` retracted the never-implemented non-TTY rule), so the unguarded set was
    # "every caller that passed NEITHER flag", TTY or pipe, human or script -- NOT "the human path".
    # Do not re-describe this as protecting a machine rather than a human; that framing is the
    # misreading this plan's review corrected (F-7), and it would have mislabelled the fix.
    #
    # WHY THE OLD SPLIT WAS BACKWARDS: the flags mark the AUDIENCE, not the RISK. A `--agent` caller
    # is the one best able to parse a structured refusal and retry with `--yes`, while a flagless
    # caller got an immediate multi-file write with no preview and no undo. MEASURED 2026-09-10 on
    # the real repository: a bare `aw ipd set approved <setid>` moved SEVEN plans out of
    # `.aw/records/plans/executed/` into `pending/` and rewrote each status, printing six
    # `executed -> approved` lines at exit 0.
    #
    # For agent or json callers, require confirmation (--yes) to execute mutation.
    # Interactive human callers execute the status change directly and are prompted by
    # _offer_self_commit unless --yes / -y / --commit is provided for automatic commit.
    if (ctx.is_agent or ctx.is_json) and not is_dry_run and not yes:
        changes = [
            Change(
                path=str(r.path),
                kind="update",
                applied=False,
                detail=f"status: {r.status or '-'} -> {normalize_target_status(target_status, r.record_type)}",
            )
            for r in matched_records
        ]
        cmd_str = _retry_command(
            args, raw_args, scoped_type=scoped_type, extra=["--yes"]
        )
        res = CommandResult(
            command="set",
            status="cannot-run",
            exit_code=2,
            summary="confirmation required (--yes needed to execute mutation)",
            changes=changes,
            next_actions=[
                NextAction(command=cmd_str, description="Apply status changes")
            ],
            verified=False,
            complete=False,
        )
        return get_renderer(ctx).emit(res, ctx)

    if is_dry_run:

        def _dry_run_disposition(r: ArtifactRecord) -> tuple[str, bool]:
            nstat = normalize_target_status(target_status, r.record_type)
            curr = (r.status or "").strip().lower()
            return nstat, curr != nstat.strip().lower()

        dry_results = [(r, *_dry_run_disposition(r)) for r in matched_records]

        if ctx.is_agent or ctx.is_json:
            changes = [
                Change(
                    path=str(r.path),
                    kind="update" if changed else "noop",
                    applied=False,
                    detail=(
                        f"status: {r.status or '-'} -> {nstat}"
                        if changed
                        else f"status: {nstat} (unchanged)"
                    ),
                )
                for r, nstat, changed in dry_results
            ]
            res = CommandResult(
                command="set",
                status="clean",
                exit_code=0,
                summary=f"would update status on {len([r for r, _, changed in dry_results if changed])} artifact(s)",
                changes=changes,
                data={
                    "items": [
                        {
                            "path": str(r.path),
                            "type": r.record_type,
                            "old_status": r.status,
                            "new_status": nstat,
                            "changed": changed,
                            "dry_run": True,
                        }
                        for r, nstat, changed in dry_results
                    ]
                },
                verified=True,
                complete=True,
            )
            return get_renderer(ctx).emit(res, ctx)

        for r, nstat, changed in dry_results:
            term.line(
                _format_status_transition_line(
                    r, r.path, nstat, term, args, dry_run=True, changed=changed
                )
            )
        return 0

    results: list[tuple[Path, str, ArtifactRecord, bool]] = []
    touched_types: set[str] = set()
    touched_paths: list[str] = []
    demotion_warnings: list[tuple[Path, str]] = []
    for rec in matched_records:
        old_text = rec.raw_text
        res = apply_status_change(
            rec,
            target_status,
            repo_root,
            args,
            close_verdict=backlog_close_verdicts.get(rec.path),
        )
        dest_path, norm_stat = res
        if getattr(res, "warning", None):
            demotion_warnings.append((dest_path, res.warning))
        new_text = dest_path.read_text(encoding="utf-8") if dest_path.exists() else ""
        changed = (old_text != new_text) or (dest_path.resolve() != rec.path.resolve())
        results.append((dest_path, norm_stat, rec, changed))
        if changed:
            touched_types.add(rec.record_type)
            try:
                dest_rel = (
                    dest_path.resolve().relative_to(repo_root.resolve()).as_posix()
                )
            except ValueError:
                dest_rel = dest_path.as_posix()
            try:
                src_rel = rec.path.resolve().relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                src_rel = rec.path.as_posix()
            if src_rel != dest_rel and src_rel not in touched_paths:
                touched_paths.append(src_rel)
            if dest_rel not in touched_paths:
                touched_paths.append(dest_rel)
        if hasattr(res, "rewritten_paths"):
            for rp in res.rewritten_paths:
                if rp not in touched_paths:
                    touched_paths.append(rp)

    if ctx.is_agent or ctx.is_json:
        changes = [
            Change(
                path=str(dest),
                kind="update" if changed else "noop",
                applied=changed,
                detail=(
                    f"status: {rec.status or '-'} -> {norm_stat}"
                    if changed
                    else f"status: {norm_stat} (unchanged)"
                ),
            )
            for dest, norm_stat, rec, changed in results
        ]
        if hasattr(args, "_citation_changes") and args._citation_changes:
            changes.extend(args._citation_changes)
        _auto_index_types(touched_types, repo_root, changes=changes)
        _offer_self_commit(
            args,
            repo_root,
            touched_paths,
            target_status,
            scoped_type_canonical,
        )
        demotion_diags = [
            Diagnostic(
                location=str(path),
                rule="status.plan_demoted",
                detail=w,
                severity="warning",
            )
            for path, w in demotion_warnings
        ]
        res_data: dict[str, Any] = {
            "items": [
                {
                    "path": str(dest),
                    "type": rec.record_type,
                    "old_status": rec.status,
                    "new_status": norm_stat,
                    "changed": changed,
                }
                for dest, norm_stat, rec, changed in results
            ]
        }
        if demotion_warnings:
            res_data["warnings"] = [w for _, w in demotion_warnings]
        res = CommandResult(
            command="set",
            status="clean",
            exit_code=0,
            summary=f"updated status on {len([r for r in results if r[3]])} artifact(s)",
            changes=changes,
            diagnostics=demotion_diags,
            data=res_data,
            verified=True,
            complete=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    _auto_index_types(touched_types, repo_root)

    for _, w in demotion_warnings:
        sys.stderr.write(f"{w}\n")

    for dest, norm_stat, rec, changed in results:
        term.line(
            _format_status_transition_line(
                rec, dest, norm_stat, term, args, dry_run=False, changed=changed
            )
        )

    _offer_self_commit(
        args,
        repo_root,
        touched_paths,
        target_status,
        scoped_type_canonical,
    )
    return 0


def resolve_dependency_edge_targets(
    repo_root: Path,
    edges: list,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Resolve each parsed dependency edge's TARGET against the repository identity index.

    Returns ``(dangling, ambiguous)``, each a list of ``(canonical_edge, detail)`` pairs in the
    input order. An ``ok`` edge appears in neither list.

    ONE EDGE RESOLVER, DELIBERATELY THE CHECKER'S (depverb f6idxs E-01, finding F-11). This
    delegates ENTIRELY to ``check_engine.build_dependency_index`` + ``check_engine._resolve_edge``,
    the SAME pair ``check_engine.evaluate_ipd_dependencies`` calls, so the setter and ``aw check``
    cannot disagree about an edge. It deliberately does NOT use ``match_selector``: that resolver
    has no edge TYPE enforcement (``ipd_schema.ITEM_DEP_TYPE_TO_RECORD_TYPE``) and no ``ambiguous``
    verdict, and the divergence is REAL rather than theoretical - id6 ``uyeko5`` is owned by one
    ``plans`` record and two ``research`` records in this repository, so a selector-based existence
    check and the shared evaluator can reach different conclusions about the same id6. Building on
    ``match_selector`` would create the second authority spec 25kzda section 2.10 forbids ("All
    surfaces call this evaluator; none reimplements it").

    Pure with respect to the repository: reads only, writes nothing.
    """
    from agent_workflows import check_engine as _ce

    index = _ce.build_dependency_index(Path(repo_root))
    dangling: list[tuple[str, str]] = []
    ambiguous: list[tuple[str, str]] = []
    for edge in edges:
        verdict, detail = _ce._resolve_edge(edge, index)
        if verdict == "dangling":
            dangling.append((edge.canonical(), detail or ""))
        elif verdict == "ambiguous":
            ambiguous.append((edge.canonical(), detail or ""))
    return dangling, ambiguous


def run_dependencies_set_command(
    args: argparse.Namespace,
    repo_root: Path | None = None,
    term: Term | None = None,
) -> int:
    """`aw ipd dependencies set <selector> <edge...>` (ipddeps Order g69y23 E-03).

    Sets a plan's machine-readable, id6-grounded cross-IPD ``Item-Dependencies`` field. Reuses the
    SAME hoisted, status-branch-independent write as ``aw ipd set --from-backlog`` by driving a
    same-status (no-op) transition through ``run_set_command`` while carrying the canonicalized
    value in ``args.item_dependencies``; persistence-on-no-op is thus inherited, not reimplemented.
    Validates + canonicalizes the edges via ``ipd_schema.canonical_item_dependencies`` BEFORE any
    write, so a malformed statement is rejected non-zero and nothing is written. A history receipt
    is appended by ``apply_status_change`` (like every other setter). This is a DIFFERENT field
    from the intra-plan ``Depends on:`` E-item ordering; the two namespaces never collide.

    EXISTENCE IS CHECKED PRE-WRITE TOO, NOT ONLY GRAMMAR (depverb f6idxs E-01/E-02). Every target is
    resolved through ``resolve_dependency_edge_targets`` (the checker's own resolver) at the SAME
    point the grammar is validated, so a typo is refused before anything is written rather than
    surfacing later from ``aw check``. ``--allow-dangling`` admits a DELIBERATE forward reference
    (authoring a Set parent-first, naming a child that does not exist yet) and names every target it
    admits; it deliberately does NOT admit an ``ambiguous`` target, because an id6 owned by two
    artifacts cannot become unambiguous by waiting.
    """
    from agent_workflows import ipd_schema as _schema
    from agent_workflows.project_context import resolve_verb_repo_root

    if term is None:
        term = Term()
    if repo_root is None:
        repo_root = resolve_verb_repo_root(getattr(args, "dir", None))

    selector = getattr(args, "selector", None)
    if not selector:
        term.status("fail", "aw ipd dependencies set: a plan selector is required.")
        return 2

    # Assemble the raw value from the positional edges: allow space- AND comma-separated tokens.
    raw_edges = list(getattr(args, "edges", None) or [])
    joined = ",".join(tok for tok in raw_edges if tok is not None)
    raw_value = joined.strip()

    # `-` / empty / `none` clears to the explicit `none`; `unresolved` is preserved as the sentinel.
    if raw_value in ("", "-", _schema.ITEM_DEPENDENCIES_NONE):
        canonical_value: str = _schema.ITEM_DEPENDENCIES_NONE
    else:
        canonical_value_opt, err = _schema.canonical_item_dependencies(raw_value)
        if err is not None or canonical_value_opt is None:
            term.status(
                "fail",
                f"aw ipd dependencies set: invalid Item-Dependencies value: {err}. "
                "Refusing before making changes.",
            )
            return 2
        canonical_value = canonical_value_opt

        # EXISTENCE, at the same pre-write seam as the grammar (depverb f6idxs E-01). The grammar
        # check above proves the token is WELL FORMED; this proves the target is REAL. Both refuse
        # with the same established "Refusing before making changes." contract, so a typo can never
        # be persisted and then reported later by a different surface.
        parsed_edges, _ready, _perr = _schema.parse_item_dependencies(canonical_value)
        dangling, ambiguous = resolve_dependency_edge_targets(repo_root, parsed_edges)
        # AMBIGUOUS IS REFUSED UNCONDITIONALLY, and `--allow-dangling` does not reach it: unlike a
        # forward reference, an id6 owned by two artifacts of the target type can never become valid
        # by the target being authored later, so admitting it would write an unresolvable edge.
        if ambiguous:
            for _canon, detail in ambiguous:
                term.status(
                    "fail",
                    f"aw ipd dependencies set: ambiguous Item-Dependencies target: {detail}. "
                    "Refusing before making changes.",
                )
            term.status(
                "info",
                "An ambiguous target cannot be admitted with --allow-dangling; repair the "
                "duplicate stable identity instead.",
            )
            return 2
        if dangling:
            if getattr(args, "allow_dangling", False):
                # LOUD, not silent: name every admitted target so the deferral is visible in the
                # transcript, and say that the repository gate still reports it.
                for canon, detail in dangling:
                    term.status(
                        "warn",
                        f"aw ipd dependencies set: accepting DANGLING target {canon} "
                        f"(--allow-dangling): {detail}",
                    )
                term.status(
                    "info",
                    "`aw check` still reports a dangling edge as an error "
                    f"({_schema.RULE_IPD_DEP_DANGLING}); resolve it before the plan advances.",
                )
            else:
                for _canon, detail in dangling:
                    term.status(
                        "fail",
                        f"aw ipd dependencies set: dangling Item-Dependencies target: {detail}. "
                        "Refusing before making changes.",
                    )
                term.status(
                    "info",
                    "Pass --allow-dangling to record a deliberate forward reference to a target "
                    "that does not exist yet.",
                )
                return 2

    # Resolve the plan(s) to read each one's CURRENT status (the setter performs a no-op transition).
    all_records = inventory_all_artifacts(repo_root)
    matches = match_selector(selector, all_records, repo_root, scoped_type="plans")
    if not matches:
        term.status("fail", f"No plans artifact matched '{selector}'.")
        return 2
    plan_matches = [m for m in matches if m.record_type == "plans"]
    if not plan_matches:
        term.status(
            "fail",
            f"Selector '{selector}' did not resolve to a plan; "
            "`aw ipd dependencies set` only applies to IPDs.",
        )
        return 2

    # A single Set selector may legitimately match several plans; drive each at its own current
    # status so no plan is force-transitioned. Group by current status for a single no-op each.
    rc_final = 0
    for rec in plan_matches:
        rc = _write_item_dependencies(
            args,
            repo_root,
            term,
            rec,
            canonical_value,
            default_message=f"set Item-Dependencies to {canonical_value}",
        )
        if rc != 0:
            rc_final = rc
    return rc_final


def _write_item_dependencies(
    args: argparse.Namespace,
    repo_root: Path,
    term: Term,
    rec: ArtifactRecord,
    canonical_value: str,
    *,
    default_message: str,
) -> int:
    """Persist one plan's canonical ``Item-Dependencies`` value through the EXISTING write path.

    THE ONE WRITER for this field's CLI surface (depverb f6idxs E-03). Both ``set`` and ``remove``
    call this, so ``remove`` inherits persistence-on-a-no-op rather than introducing a second
    writer: it drives a SAME-STATUS (no-op) transition through ``run_set_command`` carrying the value
    in ``args.item_dependencies``, exactly as ``aw ipd set --from-backlog`` does, and the actual line
    edit happens in ``apply_status_change`` via the shared ``releases.set_item_dependencies_line``
    primitive.
    """
    current = (rec.status or "draft").strip()
    deps_args = argparse.Namespace(
        args=[current, str(rec.path)],
        dir=str(repo_root),
        message=getattr(args, "message", None) or default_message,
        item_dependencies=canonical_value,
        dry_run=getattr(args, "dry_run", False),
        yes=True,
        actor=getattr(args, "actor", None),
    )
    return run_set_command(
        [current, str(rec.path)],
        scoped_type="plans",
        repo_root=repo_root,
        args=deps_args,
        term=term,
    )


def read_item_dependencies_value(text: str) -> str | None:
    """The plan's raw ``Item-Dependencies`` value, or None when the field is absent.

    Reads the metadata block through ``ipd_lint.parse`` - the SAME structural, fence-aware reader the
    lint/lifecycle surfaces and both host runners use - so no private regex for this field is added
    here (spec 25kzda 2.10's single-authority rule; depverb f6idxs E-05).
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema

    try:
        fields = _lint.parse(text).meta_fields
    except Exception:
        return None
    return fields.get(_schema.META_ITEM_DEPENDENCIES)


def run_dependencies_remove_command(
    args: argparse.Namespace,
    repo_root: Path | None = None,
    term: Term | None = None,
) -> int:
    """`aw ipd dependencies remove <selector> <edge...>` (depverb f6idxs E-03/E-04).

    Drops the named edges from a plan's ``Item-Dependencies`` statement and rewrites the REMAINDER,
    so dropping one edge from a many-edge statement is a verb rather than a hand-rewrite of the whole
    list (which silently races a concurrent edit). Four behaviors are deliberate:

    * EDGES ARE MATCHED IN CANONICAL FORM. The operator's tokens are parsed by
      ``ipd_schema.parse_item_dependencies`` and compared by ``ItemDependency.canonical()``, so a
      spelling the grammar treats as identical (whitespace, ordering) matches. The grammar REFUSES
      ``state:ipd:executed:<id6>`` rather than redirecting it, so that token is a grammar error here
      exactly as it is in ``set``; the canonical comparison is what makes every ACCEPTED spelling
      match.
    * EXISTENCE IS NOT VALIDATED. Removing an edge whose target has since been deleted is the NORMAL
      repair case, so E-01's dangling/ambiguous refusal deliberately does NOT apply to removal; a
      broken edge must stay removable.
    * AN ABSENT EDGE IS AN ERROR BY DEFAULT, named explicitly, because a silent no-op on a typo'd
      edge would leave the operator believing they removed something they did not.
      ``--if-present`` downgrades it to a notice and a clean no-op (idempotent).
    * AN EMPTIED STATEMENT BECOMES THE EXPLICIT ``none``, the grammar's zero. NOT ``unresolved``:
      the parser treats that as the not-ready sentinel, so writing it would flip the plan not-ready
      as a side effect of dropping one edge.
    """
    from agent_workflows import ipd_schema as _schema
    from agent_workflows.project_context import resolve_verb_repo_root

    if term is None:
        term = Term()
    if repo_root is None:
        repo_root = resolve_verb_repo_root(getattr(args, "dir", None))

    selector = getattr(args, "selector", None)
    if not selector:
        term.status("fail", "aw ipd dependencies remove: a plan selector is required.")
        return 2

    raw_edges = list(getattr(args, "edges", None) or [])
    raw_value = ",".join(tok for tok in raw_edges if tok is not None).strip()
    if not raw_value:
        term.status(
            "fail",
            "aw ipd dependencies remove: at least one edge to remove is required "
            "(use `aw ipd dependencies set <selector> none` to clear the whole statement).",
        )
        return 2

    # Parse the OPERATOR's tokens through the one grammar authority, so a malformed request is
    # refused pre-write with the established contract and so the comparison below is canonical.
    requested, _ready, err = _schema.parse_item_dependencies(raw_value)
    if err is not None:
        term.status(
            "fail",
            f"aw ipd dependencies remove: invalid Item-Dependencies value: {err}. "
            "Refusing before making changes.",
        )
        return 2
    if not requested:
        term.status(
            "fail",
            "aw ipd dependencies remove: a sentinel (`none`/`unresolved`) is not an edge; "
            "use `aw ipd dependencies set` to write a sentinel. "
            "Refusing before making changes.",
        )
        return 2
    wanted = [e.canonical() for e in requested]

    all_records = inventory_all_artifacts(repo_root)
    matches = match_selector(selector, all_records, repo_root, scoped_type="plans")
    if not matches:
        term.status("fail", f"No plans artifact matched '{selector}'.")
        return 2
    plan_matches = [m for m in matches if m.record_type == "plans"]
    if not plan_matches:
        term.status(
            "fail",
            f"Selector '{selector}' did not resolve to a plan; "
            "`aw ipd dependencies remove` only applies to IPDs.",
        )
        return 2

    if_present = bool(getattr(args, "if_present", False))
    # MULTI-MATCH SEMANTICS, stated rather than inherited by accident: a Set selector legitimately
    # matches several plans, and this loop mirrors `set`'s - it accumulates a non-zero exit rather
    # than aborting, so one plan lacking the edge does NOT prevent the others from being repaired.
    # That is the right default for a repair verb: aborting would make a partial fleet unfixable in
    # one call, while the non-zero exit still tells the operator something did not apply.
    rc_final = 0
    for rec in plan_matches:
        present_raw = read_item_dependencies_value(rec.raw_text)
        current_edges, _cready, cerr = _schema.parse_item_dependencies(
            present_raw or ""
        )
        if cerr is not None:
            term.status(
                "fail",
                f"{rec.path.name}: existing Item-Dependencies is malformed ({cerr}); "
                "repair it with `aw ipd dependencies set` before removing an edge.",
            )
            rc_final = 2
            continue
        present = [e.canonical() for e in current_edges]
        absent = [c for c in wanted if c not in present]
        if absent:
            names = ", ".join(absent)
            if if_present:
                term.status(
                    "info",
                    f"{rec.path.name}: edge(s) not present, nothing to remove "
                    f"(--if-present): {names}",
                )
            else:
                term.status(
                    "fail",
                    f"{rec.path.name}: Item-Dependencies does not declare {names}; "
                    "nothing removed. Pass --if-present to treat an absent edge as a no-op.",
                )
                rc_final = 2
                continue
        remaining = [c for c in present if c not in wanted]
        if remaining == present:
            # Nothing to write for this plan (every requested edge was absent under --if-present):
            # a clean no-op, which is what makes repeated removal idempotent rather than a
            # partial write.
            continue
        canonical_value_opt, verr = _schema.canonical_item_dependencies(
            ", ".join(remaining) if remaining else _schema.ITEM_DEPENDENCIES_NONE
        )
        if verr is not None or canonical_value_opt is None:
            term.status(
                "fail",
                f"{rec.path.name}: removal would leave an invalid statement ({verr}). "
                "Refusing before making changes.",
            )
            rc_final = 2
            continue
        rc = _write_item_dependencies(
            args,
            repo_root,
            term,
            rec,
            canonical_value_opt,
            default_message=(
                f"removed Item-Dependencies edge(s) {', '.join(wanted)}; "
                f"remaining {canonical_value_opt}"
            ),
        )
        if rc != 0:
            rc_final = rc
    return rc_final
