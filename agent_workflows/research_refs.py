"""Research regroup/rename + reference integrity (Set research-org, Order 04).

Delivers the after-the-fact grouping (C4) and citation-rot prevention (F5) the timestamp scheme
lacked:

* ``aw research set-assign`` groups N docs into a set (shared ``YYYYMMDD-<set-id>`` + assigned NN).
* ``aw research mv`` renames/re-slugs one doc within the grammar.
* a reference updater that, on any rename, rewrites ONLY the full old-filename token (never the
  bare ``<id6>``) across a PINNED scan root, per-file preview + atomic write.
* a REUSABLE dangling-cite detector primitive that Order 03's ``index --check`` imports so the gate
  fails on citation rot (spec 5.2), and Order 05's miscategorization flag can consume.

The immutable ``<id6>`` is preserved by every operation, so citations survive. Consumes the Order 01
contract; runs BEFORE Order 03 (its logic resolves against the filesystem + the id6 regex, not the
generated INDEX). Writing safety mirrors ``aw ipd scaffold``: preview by default, ``--apply`` to
write, atomic writes, tracked ``git mv`` for moves.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import research_contract as R

# --------------------------------------------------------------------------------------
# The pinned reference scan-root + scan iteration + writing-safety helpers are defined ONCE in
# the shared core (plans-adopter Order 01) and re-exported here so research's API is unchanged.
# --------------------------------------------------------------------------------------

SCAN_ROOTS: Tuple[str, ...] = _core.SCAN_ROOTS
iter_scan_files = _core.iter_scan_files
_atomic_write = _core.atomic_write
_git_mv = _core.git_mv


# --------------------------------------------------------------------------------------
# Reference rewriting (E-04): full old-filename token only, never the bare id6.
# --------------------------------------------------------------------------------------


class RefEdit(NamedTuple):
    """A planned reference rewrite in a single file."""

    file: Path
    old_name: str
    new_name: str
    hits: int


def plan_reference_rewrites(repo_root: Path, renames: Dict[str, str]) -> List[RefEdit]:
    """Plan rewrites of full old-filename tokens to new names across the scan root.

    ``renames`` maps old filename -> new filename (basenames). We rewrite the full old NAME token
    only; the bare ``<id6>`` is never touched (it is stable and shared by the new name).
    """

    edits: List[RefEdit] = []
    scan_files = iter_scan_files(repo_root)
    for f in scan_files:
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for old_name, new_name in renames.items():
            if old_name == new_name:
                continue
            n = text.count(old_name)
            if n:
                edits.append(RefEdit(f, old_name, new_name, n))
    return edits


def apply_reference_rewrites(edits: List[RefEdit]) -> None:
    """Apply planned rewrites with per-file read/replace/atomic-write."""

    # Group edits by file so each file is written once.
    by_file: Dict[Path, List[RefEdit]] = {}
    for e in edits:
        by_file.setdefault(e.file, []).append(e)
    for f, file_edits in by_file.items():
        text = f.read_text(encoding="utf-8")
        for e in file_edits:
            text = text.replace(e.old_name, e.new_name)
        _atomic_write(f, text)


# --------------------------------------------------------------------------------------
# Dangling-cite detector (E-05): the REUSABLE primitive (consumed by Order 03 --check + Order 05).
# --------------------------------------------------------------------------------------


# The Dangler record + the scan/detection loop are the shared core's (plans-adopter Order 01);
# re-export the record so research's API is unchanged.
Dangler = _core.Dangler


def _current_id6s(research_root: Path) -> set:
    """Every ``<id6>`` currently present in a research filename (the resolvable set)."""

    ids = set()
    if research_root.is_dir():
        for p in research_root.rglob("*.md"):
            parsed, _err = R.parse_name(p.name)
            if parsed is not None:
                ids.add(parsed.id6)
    return ids


def find_dangling_citations(
    repo_root: Path, research_root: Optional[Path] = None
) -> List[Dangler]:
    """Return every research-id CITATION that does not resolve to a current research file.

    Delegates to the area-agnostic ``artifact_core.find_dangling_citations`` with research's
    current-id resolver (``_current_id6s``) and citation matcher (``R.iter_id6_citations``), and
    excludes the research tree itself. A CITATION is the ``RSCH-<id6>`` handle or a full
    research-filename reference; a bare 6-letter word is NOT a citation. Behavior is identical to
    the pre-refactor detector.
    """

    rroot = research_root or R.resolve_research_root(repo_root)
    return _core.find_dangling_citations(
        repo_root,
        current_ids=_current_id6s(rroot),
        cite_matcher=R.iter_id6_citations,
        exclude_root=rroot,
    )


# --------------------------------------------------------------------------------------
# set-assign / mv planning
# --------------------------------------------------------------------------------------


class RenamePlan(NamedTuple):
    """A planned rename of one research file (old -> new), preserving its id6."""

    old_path: Path
    new_path: Path


def _find_by_id6(research_root: Path, id6: str) -> Optional[Path]:
    for p in research_root.rglob("*.md"):
        parsed, _err = R.parse_name(p.name)
        if parsed is not None and parsed.id6 == id6:
            return p
    return None


def plan_set_assign(
    research_root: Path,
    id6s: List[str],
    set_id: str,
    date_str: str,
    start_order: int = 0,
) -> Tuple[Optional[List[RenamePlan]], Optional[str]]:
    """Plan renaming the given docs into a set (shared date + set-id, assigned NN), keeping id6."""

    set_k = R.kebab(set_id)
    if not set_k:
        return None, "a --set id is required"
    plans: List[RenamePlan] = []
    for i, id6 in enumerate(id6s):
        src = _find_by_id6(research_root, id6)
        if src is None:
            return None, f"no research file has id6 '{id6}'"
        parsed, _err = R.parse_name(src.name)
        new_name = R.format_name(
            R.ResearchName(
                date=date_str,
                set_id=set_k,
                order=f"{start_order + i:02d}",
                id6=parsed.id6,
                slug=parsed.slug,
                model=parsed.model,
                kind=parsed.kind,
            )
        )
        plans.append(RenamePlan(src, src.parent / new_name))
    return plans, None


def plan_mv(
    research_root: Path,
    id6: str,
    slug: Optional[str] = None,
    kind: Optional[str] = None,
    model: Optional[str] = None,
) -> Tuple[Optional[RenamePlan], Optional[str]]:
    """Plan renaming/re-slugging one doc within the grammar, keeping id6."""

    src = _find_by_id6(research_root, id6)
    if src is None:
        return None, f"no research file has id6 '{id6}'"
    parsed, _err = R.parse_name(src.name)
    new_kind = parsed.kind
    if kind is not None:
        kr = R.normalize_kind(kind)
        if not kr.ok:
            return None, kr.message
        new_kind = kr.value or kind
    new_model = parsed.model
    if model is not None:
        mr = R.normalize_model(model)
        if not mr.ok:
            return None, mr.message
        new_model = mr.value
    new_slug = R.kebab(slug) if slug else parsed.slug
    new_name = R.format_name(
        R.ResearchName(
            date=parsed.date,
            set_id=parsed.set_id,
            order=parsed.order,
            id6=parsed.id6,
            slug=new_slug,
            model=new_model,
            kind=new_kind,
        )
    )
    return RenamePlan(src, src.parent / new_name), None


# --------------------------------------------------------------------------------------
# CLI handlers
# --------------------------------------------------------------------------------------


def _repo_root(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "dir", None) or ".").resolve()


def _apply_renames(repo_root: Path, plans: List[RenamePlan], apply: bool) -> None:
    """Apply the file renames as tracked git moves plus the reference rewrites."""

    renames = {p.old_path.name: p.new_path.name for p in plans}
    ref_edits = plan_reference_rewrites(repo_root, renames)
    if not apply:
        for p in plans:
            print(f"--- would rename {p.old_path} -> {p.new_path.name} ---")
        for e in ref_edits:
            print(
                f"--- would rewrite {e.hits}x '{e.old_name}' -> '{e.new_name}' in {e.file} ---"
            )
        return
    for p in plans:
        src_rel = p.old_path.relative_to(repo_root).as_posix()
        dst_rel = p.new_path.relative_to(repo_root).as_posix()
        _git_mv(repo_root, src_rel, dst_rel)
        print(f"renamed {src_rel} -> {dst_rel}")
    apply_reference_rewrites(ref_edits)
    for e in ref_edits:
        print(f"rewrote {e.hits}x '{e.old_name}' -> '{e.new_name}' in {e.file}")


def run_set_assign(args: argparse.Namespace) -> int:
    repo_root = _repo_root(args)
    research_root = R.resolve_research_root(repo_root)
    from datetime import date

    ids = [i.strip() for i in (getattr(args, "ids", None) or []) if i.strip()]
    if not ids:
        print("error: at least one <id6> is required")
        return 2
    date_str = getattr(args, "date", None) or date.today().strftime("%Y%m%d")
    start = getattr(args, "order", None)
    plans, err = plan_set_assign(
        research_root,
        ids,
        getattr(args, "set", "") or "",
        date_str,
        start_order=start if start is not None else 0,
    )
    if err:
        print(f"error: {err}")
        return 2
    _apply_renames(repo_root, plans or [], getattr(args, "apply", False))
    return 0


def run_mv(args: argparse.Namespace) -> int:
    repo_root = _repo_root(args)
    research_root = R.resolve_research_root(repo_root)
    plan, err = plan_mv(
        research_root,
        getattr(args, "id", "") or "",
        slug=getattr(args, "slug", None),
        kind=getattr(args, "kind", None),
        model=getattr(args, "model", None),
    )
    if err:
        print(f"error: {err}")
        return 2
    _apply_renames(repo_root, [plan] if plan else [], getattr(args, "apply", False))
    return 0


def run_check_refs(args: argparse.Namespace) -> int:
    """Report dangling citations (the reusable detector as a standalone verb)."""

    repo_root = _repo_root(args)
    danglers = find_dangling_citations(repo_root)
    if getattr(args, "agent", False):
        for d in danglers:
            print(f"{d.file}:{d.line}\tdangling-citation\t{d.id6}")
        return 1 if danglers else 0
    if not danglers:
        print("no dangling citations")
        return 0
    for d in danglers:
        print(f"{d.file}:{d.line}: dangling id6 '{d.id6}': {d.context}")
    return 1
