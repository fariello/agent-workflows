"""Plans regroup/rename + reference integrity (Set plans-adopter, Order 04).

Enables after-the-fact topic regrouping of plans without breaking citations:

* ``aw plans set-assign <id6...> --set <s> [--order ...] [--rename]`` groups plans into a Set
  (updates ``Set:``/``Order:`` metadata; with ``--rename`` renames to the clustering grammar
  ``YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md`` as an atomic tracked ``git mv``, keeping ``Id``);
* ``aw plans mv <id6> [--slug ... --set ... --order ...]`` renames/re-slugs one plan;
* a reference updater that rewrites the THREE plan-citation forms via an explicit old-name ->
  new-name map (so a bare stem is rewritten ONLY when it maps to a PLAN; a spec-only stem sharing
  the ``YYYYMMDD-HHMM-NN`` grammar is never touched); reuses the shared-core dangling detector.

The immutable ``Id`` (Order 02) is the citation handle. Writing safety mirrors ``aw ipd scaffold``:
preview by default, ``--apply`` to write, atomic writes, tracked ``git mv``. Consumes the Order-01
core, Order-02 ``Id``, and Order-03 manifest scan.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import artifact_refs as _refs
from agent_workflows import plans_index as _idx

PLANS_DIR = ".agents/plans"

# The uniform artifact-type facets and the clustered grammar are defined ONCE in the naming
# authority (IPD o6b8l3); re-exported here so this module's public API is unchanged.
ARTIFACT_TYPE_FACETS = _naming.ARTIFACT_TYPE_FACETS
_FACET_ALT = _naming._FACET_ALT
_CLUSTERED_RE = _naming._CLUSTERED_RE
# An old-style plan stem: YYYYMMDD-HHMM-NN (bare, no slug/.md). Shared with specs, so a bare-stem
# rewrite is driven by an explicit plan map, never by this pattern alone.
_BARE_STEM_RE = re.compile(r"\b(\d{8}-\d{4}-\d{2})\b")


# --------------------------------------------------------------------------------------
# metadata read/write on a plan file
# --------------------------------------------------------------------------------------

_ID_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_DATE_RE = re.compile(r"(?m)^- Date:\s*(\d{8}|\d{4}-\d{2}-\d{2})\s*$")
_SET_LINE_RE = re.compile(r"(?m)^- Set:\s*(.+?)\s*$")
_ORDER_LINE_RE = re.compile(r"(?m)^- Order:\s*(\d+)\s*$")


def _read_id(text: str) -> Optional[str]:
    m = _ID_RE.search(text)
    return m.group(1) if m else None


def _find_plan_by_id(plans_dir: Path, id6: str) -> Optional[Path]:
    for p in plans_dir.rglob("*.md"):
        if p.name in _idx._EXCLUDE_NAMES:
            continue
        if _read_id(p.read_text(encoding="utf-8")) == id6:
            return p
    return None


def _set_value(set_id: str, descriptive: Optional[str]) -> str:
    """The `Set:` metadata value: terse id, optionally with a `(descriptive)` parenthetical."""

    return f"{set_id} ({descriptive})" if descriptive else set_id


def _set_metadata(
    text: str, *, set_id: str, order: int, descriptive: Optional[str] = None
) -> str:
    """Return ``text`` with Set/Order set (updating existing lines or inserting after Author/Id).

    The written `Set:` value is ``<terse-id> (<descriptive>)`` when ``descriptive`` is given, else the
    bare terse id (plans-adopter Order 06 format).
    """

    set_val = _set_value(set_id, descriptive)
    if _SET_LINE_RE.search(text):
        text = _SET_LINE_RE.sub(f"- Set: {set_val}", text, count=1)
    if _ORDER_LINE_RE.search(text):
        text = _ORDER_LINE_RE.sub(f"- Order: {order}", text, count=1)
    if _SET_LINE_RE.search(text) and _ORDER_LINE_RE.search(text):
        return text
    # Insert Set/Order after the Id line (or Author line) when absent.
    lines = text.splitlines(keepends=True)
    anchor = None
    for i, line in enumerate(lines):
        if line.startswith("- Id:"):
            anchor = i
    if anchor is None:
        for i, line in enumerate(lines):
            if line.startswith("- Author:"):
                anchor = i
    if anchor is not None:
        nl = "\n"
        ins = []
        if not _SET_LINE_RE.search(text):
            ins.append(f"- Set: {set_val}{nl}")
        if not _ORDER_LINE_RE.search(text):
            ins.append(f"- Order: {order}{nl}")
        lines[anchor + 1 : anchor + 1] = ins
    return "".join(lines)


def _plan_date(text: str) -> str:
    m = _DATE_RE.search(text)
    if not m:
        return "20260101"
    raw = m.group(1)
    return raw.replace("-", "") if "-" in raw else raw


# --------------------------------------------------------------------------------------
# rename planning
# --------------------------------------------------------------------------------------


class RenamePlan(NamedTuple):
    old_path: Path
    new_path: Path
    id6: str
    # The Order to write into the plan's front matter. None means "use the enumerate index" (the
    # historical set-assign behavior where the caller sequences a batch). `aw plans mv` passes the
    # plan's PRESERVED order so a bare rename does not clobber `- Order:` to 0 (vf03z3).
    order: Optional[int] = None


def clustered_name(
    *,
    date: str,
    set_id: str,
    order: int,
    id6: str,
    slug: str,
    artifact_type: Optional[str] = None,
) -> str:
    """Build a clustered name. When ``artifact_type`` is one of ``ARTIFACT_TYPE_FACETS`` the uniform
    ``<...>.<type>.md`` facet is appended; when None (or empty) the bare ``.md`` form is produced
    (backward-compatible). Delegates to the single naming authority (IPD o6b8l3)."""

    return _naming.build_clustered_name(
        date=date,
        set_id=set_id,
        order=order,
        id6=id6,
        slug=slug,
        artifact_type=artifact_type,
    )


def _slug_of(old_name: str, id6: str) -> str:
    """Derive a slug for the clustered name from an old filename."""

    base = old_name.removesuffix(".md")
    base = base.split(".")[0]  # drop any dotted facets
    parts = [p for p in base.split("-") if p and p != id6]
    # Drop leading date/time/nn numeric tokens.
    while parts and parts[0].isdigit():
        parts.pop(0)
    return _core.kebab("-".join(parts)) or "plan"


def plan_set_assign(
    plans_dir: Path,
    id6s: List[str],
    set_id: str,
    *,
    start_order: int = 0,
    rename: bool = False,
) -> Tuple[Optional[List[RenamePlan]], Optional[str]]:
    """Plan a Set (re)assignment for the given plans; with ``rename`` also plan clustering renames."""

    set_k = _core.kebab(set_id)
    if not set_k:
        return None, "a --set id is required"
    plans: List[RenamePlan] = []
    for i, id6 in enumerate(id6s):
        src = _find_plan_by_id(plans_dir, id6)
        if src is None:
            return None, f"no plan has Id '{id6}'"
        order = start_order + i
        if rename:
            text = src.read_text(encoding="utf-8")
            new_name = clustered_name(
                date=_plan_date(text),
                set_id=set_k,
                order=order,
                id6=id6,
                slug=_slug_of(src.name, id6),
                artifact_type="ipd",
            )
            plans.append(RenamePlan(src, src.parent / new_name, id6, order=order))
        else:
            plans.append(
                RenamePlan(src, src, id6, order=order)
            )  # metadata-only (no rename)
    return plans, None


# --------------------------------------------------------------------------------------
# reference rewriting: the three citation forms, driven by an explicit old->new PLAN map
# --------------------------------------------------------------------------------------


# The RefEdit record is defined ONCE in the unified reference library (IPD 3cmnfc); re-export it so
# this module's API (`RefEdit(file, kind, old, new, hits)`) is unchanged.
RefEdit = _refs.RefEdit


def _old_stem(old_name: str) -> Optional[str]:
    """The old-style YYYYMMDD-HHMM-NN stem of an old plan filename, if it has one."""

    m = re.match(r"\A(\d{8}-\d{4}-\d{2})-", old_name)
    return m.group(1) if m else None


def plan_reference_rewrites(
    repo_root: Path, name_map: Dict[str, str], plans_dir: Path
) -> List[RefEdit]:
    """Plan every FILENAME-derived citation rewrite for a PLAN ``name_map`` (old -> new).

    IPD 3cmnfc E-04: delegates to the ONE unified reference matcher (``artifact_refs``): full name +
    whole stem (covers the range shorthand ``<stem>..NN``) + the legacy ``YYYYMMDD-HHMM-NN`` prefix
    stem, all map-driven and hyphen-boundaried, never touching a bare id6/setid. This also gives a
    CLUSTERED plan rename the whole-stem rewrite it previously lacked (the same fix research gets).
    ``plans_dir`` is retained for API compatibility (matching scans the pinned SCAN_ROOTS).
    """

    return _refs.plan_reference_rewrites(repo_root, name_map)


def apply_reference_rewrites(edits: List[RefEdit]) -> None:
    """Apply planned rewrites via the unified applier (full-name first, then hyphen-boundaried stem)."""

    _refs.apply_reference_rewrites(edits, prefix=".plans-refs-")


# --------------------------------------------------------------------------------------
# apply the renames (metadata + git mv + reference rewrite)
# --------------------------------------------------------------------------------------


def apply_renames(
    repo_root: Path,
    plans_dir: Path,
    plans: List[RenamePlan],
    set_id: str,
    *,
    apply: bool,
    descriptive: Optional[str] = None,
    update_refs: bool = True,
) -> None:
    """Set metadata + (optional) clustering rename + citation rewrite. Preview when not apply.
    update_refs=False (from `--no-refs`, awcmdsurf Order 03) renames the file only, leaving citing
    documents untouched."""

    name_map = {
        p.old_path.name: p.new_path.name for p in plans if p.old_path != p.new_path
    }
    ref_edits = (
        plan_reference_rewrites(repo_root, name_map, plans_dir)
        if (name_map and update_refs)
        else []
    )
    if not apply:
        for i, p in enumerate(plans):
            if p.old_path == p.new_path:
                print(
                    f"--- would set Set={_core.kebab(set_id)} Order={i:02d} on {p.old_path.name} ---"
                )
            else:
                print(f"--- would rename {p.old_path.name} -> {p.new_path.name} ---")
        for e in ref_edits:
            print(
                f"--- would rewrite {e.hits}x [{e.kind}] '{e.old}' -> '{e.new}' in {e.file} ---"
            )
        return
    for i, p in enumerate(plans):
        # Update Set/Order metadata in place first. Use the plan's explicit order when provided
        # (mv preserves it), else the enumerate index (set-assign batch sequencing).
        text = p.old_path.read_text(encoding="utf-8")
        text = _set_metadata(
            text,
            set_id=_core.kebab(set_id),
            order=p.order if p.order is not None else i,
            descriptive=descriptive,
        )
        _core.atomic_write(p.old_path, text, prefix=".plans-refs-")
        if p.old_path != p.new_path:
            src_rel = p.old_path.relative_to(repo_root).as_posix()
            dst_rel = p.new_path.relative_to(repo_root).as_posix()
            _core.git_mv(repo_root, src_rel, dst_rel)
            print(f"renamed {src_rel} -> {dst_rel}")
    apply_reference_rewrites(ref_edits)
    for e in ref_edits:
        print(f"rewrote {e.hits}x [{e.kind}] in {e.file}")
    try:
        _idx.run_index(
            argparse.Namespace(
                dir=str(repo_root),
                check=False,
                as_agent=False,
                json=False,
                no_color=True,
                limit=None,
            )
        )
    except Exception:
        pass


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def _dirs(args: argparse.Namespace) -> Tuple[Path, Path]:
    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    # Layout-aware (IPD awretrofit Order 01): resolve .aw/records/plans with a legacy
    # .agents/plans read-fallback, mirroring plans_index._dirs.
    from agent_workflows.record_producers import resolve_record_path

    try:
        plans_dir = resolve_record_path("plans", target_repo=str(repo_root))
    except Exception:
        plans_dir = repo_root / ".aw" / "records" / "plans"
    if not plans_dir.is_dir() and (repo_root / ".agents" / "plans").is_dir():
        plans_dir = repo_root / ".agents" / "plans"
    elif not plans_dir.is_dir() and (repo_root / ".aw" / "records" / "plans").is_dir():
        plans_dir = repo_root / ".aw" / "records" / "plans"
    return repo_root, plans_dir


def run_set_assign(args: argparse.Namespace) -> int:
    repo_root, plans_dir = _dirs(args)
    ids = [i.strip() for i in (getattr(args, "ids", None) or []) if i.strip()]
    if not ids:
        print("error: at least one <id6> is required")
        return 2
    start = getattr(args, "order", None)
    plans, err = plan_set_assign(
        plans_dir,
        ids,
        getattr(args, "set", "") or "",
        start_order=start if start is not None else 0,
        rename=getattr(args, "rename", False),
    )
    if err:
        print(f"error: {err}")
        return 2
    apply_renames(
        repo_root,
        plans_dir,
        plans or [],
        getattr(args, "set", ""),
        apply=getattr(args, "apply", False),
        update_refs=not getattr(args, "no_refs", False),
    )
    return 0


def run_mv(args: argparse.Namespace) -> int:
    repo_root, plans_dir = _dirs(args)
    id6 = getattr(args, "id", "") or ""
    src = _find_plan_by_id(plans_dir, id6)
    if src is None:
        print(f"error: no plan has Id '{id6}'")
        return 2
    text = src.read_text(encoding="utf-8")
    m = _SET_LINE_RE.search(text)
    om = _ORDER_LINE_RE.search(text)
    existing_terse = _idx.set_terse_id(m.group(1)) if m else None
    set_id = getattr(args, "set", None) or existing_terse or id6
    # Preserve the plan's existing Order unless --order is explicitly given (vf03z3: a bare rename
    # must NOT clobber Order to 0). Prefer the front-matter Order; fall back to the current filename.
    order = getattr(args, "order", None)
    if order is None:
        if om:
            order = int(om.group(1))
        else:
            parsed = _CLUSTERED_RE.match(src.name)
            order = int(parsed.group("nn")) if parsed else 0
    # Preserve the plan's existing date unless we can derive it from the front-matter (vf03z3: a bare
    # rename must NOT recompute the date). Prefer the current filename's date, then the `- Date:` line.
    parsed_name = _CLUSTERED_RE.match(src.name)
    new_date = parsed_name.group("date") if parsed_name else _plan_date(text)
    slug = getattr(args, "slug", None)
    new_name = clustered_name(
        date=new_date,
        set_id=set_id,
        order=order,
        id6=id6,
        slug=slug if slug else _slug_of(src.name, id6),
        artifact_type="ipd",
    )
    plan = RenamePlan(src, src.parent / new_name, id6, order=order)
    apply_renames(
        repo_root,
        plans_dir,
        [plan],
        set_id,
        apply=getattr(args, "apply", False),
        update_refs=not getattr(args, "no_refs", False),
    )
    return 0
