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
from agent_workflows import plans_index as _idx

PLANS_DIR = ".agents/plans"

# The clustering grammar target: YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md
_CLUSTERED_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)\.md\Z"
)
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


def clustered_name(*, date: str, set_id: str, order: int, id6: str, slug: str) -> str:
    return f"{date}-{_core.kebab(set_id)}-{order:02d}-{id6}-{_core.kebab(slug)}.md"


def _slug_of(old_name: str, id6: str) -> str:
    """Derive a slug for the clustered name from an old filename."""

    base = old_name[:-3] if old_name.endswith(".md") else old_name
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
            )
            plans.append(RenamePlan(src, src.parent / new_name, id6))
        else:
            plans.append(RenamePlan(src, src, id6))  # metadata-only (no rename)
    return plans, None


# --------------------------------------------------------------------------------------
# reference rewriting: the three citation forms, driven by an explicit old->new PLAN map
# --------------------------------------------------------------------------------------


class RefEdit(NamedTuple):
    file: Path
    kind: str  # full-name | bare-stem
    old: str
    new: str
    hits: int


def _old_stem(old_name: str) -> Optional[str]:
    """The old-style YYYYMMDD-HHMM-NN stem of an old plan filename, if it has one."""

    m = re.match(r"\A(\d{8}-\d{4}-\d{2})-", old_name)
    return m.group(1) if m else None


def plan_reference_rewrites(
    repo_root: Path, name_map: Dict[str, str], plans_dir: Path
) -> List[RefEdit]:
    """Plan rewrites of the three citation forms for a PLAN old-name -> new-name ``name_map``.

    (a) full old filename -> new filename (exact string);
    (b) bare stem ``YYYYMMDD-HHMM-NN`` -> the NEW stem, ONLY for stems that belong to a plan in the
        map (so spec-only stems sharing the grammar are never touched);
    (c) range shorthand is a special case of (b): the stem inside a range is rewritten by the same
        stem map, so a ``<oldstem>..NN`` range becomes ``<newstem>..NN``.
    """

    # Build a bare-stem map from ONLY the plan renames (old stem -> new stem, both stemmed).
    stem_map: Dict[str, str] = {}
    for old_name, new_name in name_map.items():
        os_ = _old_stem(old_name)
        # The "new stem" is the clustered name without its `.md` (used for bare/range cites).
        if os_ is not None:
            stem_map[os_] = new_name[:-3] if new_name.endswith(".md") else new_name

    edits: List[RefEdit] = []
    for f in _core.iter_scan_files(repo_root):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # (a) full filename
        for old_name, new_name in name_map.items():
            if old_name != new_name and old_name in text:
                edits.append(
                    RefEdit(f, "full-name", old_name, new_name, text.count(old_name))
                )
        # (b)+(c) bare stem (also covers the stem inside a range shorthand), plan-map-driven only.
        for old_stem, new_stem in stem_map.items():
            # Count occurrences of the stem as a standalone token (word-boundaried), which also
            # matches the stem inside a `<stem>`..`NN` range shorthand.
            pat = re.compile(
                r"(?<![0-9A-Za-z-])" + re.escape(old_stem) + r"(?![0-9A-Za-z-])"
            )
            n = len(pat.findall(text))
            if n:
                edits.append(RefEdit(f, "bare-stem", old_stem, new_stem, n))
    return edits


def apply_reference_rewrites(edits: List[RefEdit]) -> None:
    by_file: Dict[Path, List[RefEdit]] = {}
    for e in edits:
        by_file.setdefault(e.file, []).append(e)
    for f, file_edits in by_file.items():
        text = f.read_text(encoding="utf-8")
        # Apply full-name rewrites first (longest, most specific), then bare-stem (word-boundaried).
        for e in sorted(file_edits, key=lambda x: 0 if x.kind == "full-name" else 1):
            if e.kind == "full-name":
                text = text.replace(e.old, e.new)
            else:
                pat = re.compile(
                    r"(?<![0-9A-Za-z-])" + re.escape(e.old) + r"(?![0-9A-Za-z-])"
                )
                text = pat.sub(e.new, text)
        _core.atomic_write(f, text, prefix=".plans-refs-")


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
) -> None:
    """Set metadata + (optional) clustering rename + citation rewrite. Preview when not apply."""

    name_map = {
        p.old_path.name: p.new_path.name for p in plans if p.old_path != p.new_path
    }
    ref_edits = (
        plan_reference_rewrites(repo_root, name_map, plans_dir) if name_map else []
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
        # Update Set/Order metadata in place first.
        text = p.old_path.read_text(encoding="utf-8")
        text = _set_metadata(
            text, set_id=_core.kebab(set_id), order=i, descriptive=descriptive
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
    order = getattr(args, "order", None)
    order = order if order is not None else (int(om.group(1)) if om else 0)
    slug = getattr(args, "slug", None)
    new_name = clustered_name(
        date=_plan_date(text),
        set_id=set_id,
        order=order,
        id6=id6,
        slug=slug if slug else _slug_of(src.name, id6),
    )
    plan = RenamePlan(src, src.parent / new_name, id6)
    apply_renames(
        repo_root, plans_dir, [plan], set_id, apply=getattr(args, "apply", False)
    )
    return 0
