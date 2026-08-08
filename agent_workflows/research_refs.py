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
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import research_contract as R

# --------------------------------------------------------------------------------------
# The pinned reference scan-root (E-07): ONE authoritative list, consumed by E-04 and E-05.
# Paths are POSIX, relative to the repo root. This is the ONLY enumeration; do not scatter
# divergent lists in prose or elsewhere.
# --------------------------------------------------------------------------------------

SCAN_ROOTS: Tuple[str, ...] = (
    "DECISIONS.md",
    "TODO.md",
    "README.md",
    "ARCHITECTURE.md",
    ".agents/plans",
    ".agents/docs",
)

_TEXT_SUFFIXES = (".md", ".txt")


def iter_scan_files(repo_root: Path) -> List[Path]:
    """Return every tracked-text file under the pinned scan root (deterministic, sorted)."""

    files: List[Path] = []
    for rel in SCAN_ROOTS:
        p = repo_root / rel
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix in _TEXT_SUFFIXES:
                    files.append(f)
    return sorted(set(files))


# --------------------------------------------------------------------------------------
# Atomic write (mirrors ipd_authoring._atomic_write)
# --------------------------------------------------------------------------------------


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".refs-tmp-", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _git_mv(repo_root: Path, src_rel: str, dst_rel: str) -> None:
    """git mv (staged, not committed), with a filesystem fallback for untracked files."""

    (repo_root / dst_rel).parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "-C", str(repo_root), "mv", "--", src_rel, dst_rel],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        import shutil

        shutil.move(str(repo_root / src_rel), str(repo_root / dst_rel))


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


class Dangler(NamedTuple):
    """A dangling citation: an id6 word-match whose surrounding filename does not resolve."""

    file: Path
    line: int
    id6: str
    context: str


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

    A pure, deterministic scan of the pinned scan root. A CITATION is the ``RSCH-<id6>`` handle or a
    full research-filename reference (see ``research_contract.iter_id6_citations``); a bare 6-letter
    word is NOT a citation, so ordinary prose does not false-positive. A citation resolves when its
    id names a current research file; one whose id names no current file (a moved/renamed target
    cited by an old path, or a deleted doc) is reported as dangling. A citation to a moved-but-present
    id still resolves (the id is stable), so it is NOT reported.
    """

    rroot = research_root or (repo_root / R.RESEARCH_ROOT)
    current_ids = _current_id6s(rroot)
    danglers: List[Dangler] = []
    for f in iter_scan_files(repo_root):
        # Do not scan the research files themselves for their own ids as citations.
        try:
            f.relative_to(rroot)
            is_research = True
        except ValueError:
            is_research = False
        if is_research:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            for tok in R.iter_id6_citations(line):
                if tok not in current_ids:
                    danglers.append(Dangler(f, i, tok, line.strip()[:120]))
    return danglers


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
    research_root = repo_root / R.RESEARCH_ROOT
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
    research_root = repo_root / R.RESEARCH_ROOT
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
