"""Research state lifecycle + monthly archival shards (Set research-org, Order 05).

Implements the four-state lifecycle (intake/active/reference/archive) and the monthly `YYYYMM`
cold shards for reference and archive, with DELIBERATE, tool-invoked archival verbs (never a
background or index-time side effect, spec 4.10):

* a ``status`` transition helper that sets frontmatter ``status`` AND moves the file to the matching
  location (hot root for intake/active; ``reference/YYYYMM/`` or ``archive/YYYYMM/`` for the
  cold states) as an atomic tracked rename, reusing Order 04's reference-updater on move.
* ``aw archive <set-id|doc-id>``: deep-shelve target(s), preview then ``--apply``.
* bare ``aw archive``: a sweep of candidates that are BOTH older than the age threshold AND uncited, with a
  per-item accept/override (reference vs archive) before applying, recording the resulting status.
* a miscategorization flag: a doc in ``archive/`` that IS cited (via ``consumed-by`` or Order 04's
  detector) is reported ("should be reference?").
* an INDEX refresh after any archival move (reference stays in the hot glance; archive excluded).

Consumes Order 01 (contract), Order 03 (index refresh) and Order 04 (reference-updater + detector).
"""

from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import research_contract as R
from agent_workflows import research_index as RI
from agent_workflows import research_refs as RF


class Move(NamedTuple):
    """A planned status transition + file move for one doc."""

    id6: str
    old_path: Path
    new_path: Path
    new_status: str


def _shard_subpath(status: str, created: str) -> Optional[str]:
    """Return the shard subpath for a cold status, or None for hot states (which live at root)."""

    if status == "reference":
        return f"{R.REFERENCE_DIR}/{R.shard_for_date(created)}"
    if status == "archive":
        return f"{R.ARCHIVE_DIR}/{R.shard_for_date(created)}"
    return None


def _target_path(research_root: Path, filename: str, status: str, created: str) -> Path:
    sub = _shard_subpath(status, created)
    if sub is None:
        return research_root / filename
    return research_root / sub / filename


def _all_docs(
    research_root: Path,
) -> List[Tuple[Path, R.ResearchName, Dict[str, object]]]:
    """Return (path, parsed-name, frontmatter) for every conformant research doc."""

    out = []
    if not research_root.is_dir():
        return out
    for p in sorted(research_root.rglob("*.md")):
        if p.name in (RI.INDEX_MD,) or p.name == "README.md":
            continue
        parsed, _err = R.parse_name(p.name)
        if parsed is None:
            continue
        fm = R.parse_frontmatter(p.read_text(encoding="utf-8"))
        if fm is None:
            continue
        out.append((p, parsed, fm))
    return out


def _rewrite_status_in_text(text: str, new_status: str) -> str:
    """Return ``text`` with the frontmatter ``status:`` line set to ``new_status`` (first block)."""

    lines = text.splitlines(keepends=True)
    in_fm = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_fm = True
            continue
        if in_fm and stripped == "---":
            break
        if in_fm and stripped.startswith("status:"):
            newline = "\n" if line.endswith("\n") else ""
            lines[i] = f"status: {new_status}{newline}"
            break
    return "".join(lines)


def plan_transition(
    research_root: Path, id6: str, new_status: str
) -> Tuple[Optional[Move], Optional[str]]:
    """Plan a status transition + move for one doc (keeping id6). No writing."""

    if new_status not in R.STATUSES:
        return None, f"status must be one of {sorted(R.STATUSES)}"
    match = None
    for p, parsed, fm in _all_docs(research_root):
        if parsed.id6 == id6:
            match = (p, parsed, fm)
            break
    if match is None:
        return None, f"no research file has id6 '{id6}'"
    p, parsed, fm = match
    created = str(fm.get("created", parsed.date))
    new_path = _target_path(research_root, p.name, new_status, created)
    return Move(id6, p, new_path, new_status), None


def _collect_all_citations(repo_root: Path, research_root: Path) -> set[str]:
    cited_ids: set[str] = set()
    for f in RF.iter_scan_files(repo_root):
        try:
            f.relative_to(research_root)
            continue
        except ValueError:
            pass
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for cid in R.iter_id6_citations(text):
            cited_ids.add(cid)
    return cited_ids


def _is_cited(
    repo_root: Path,
    research_root: Path,
    id6: str,
    fm: Dict[str, object],
    all_cited: Optional[set[str]] = None,
) -> bool:
    """True if the doc is cited: a non-empty frontmatter consumed-by, or a resolving citation."""

    consumed = fm.get("consumed-by")
    if isinstance(consumed, list) and consumed:
        return True
    if all_cited is not None:
        return id6 in all_cited
    # A citation elsewhere whose id resolves to this doc.
    for f in RF.iter_scan_files(repo_root):
        try:
            f.relative_to(research_root)
            continue  # skip research files themselves
        except ValueError:
            pass
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if id6 in R.iter_id6_citations(text):
            return True
    return False


def find_miscategorized(repo_root: Path, research_root: Path) -> List[str]:
    """Return id6s of docs currently in ``archive/`` that ARE cited (should be reference?)."""

    flagged = []
    all_cited = _collect_all_citations(repo_root, research_root)
    for p, parsed, fm in _all_docs(research_root):
        if str(fm.get("status")) == "archive":
            if _is_cited(repo_root, research_root, parsed.id6, fm, all_cited=all_cited):
                flagged.append(parsed.id6)
    return flagged


def _age_days(created: str, today: Optional[date] = None) -> float:
    t = today or date.today()
    try:
        d = datetime.strptime(created, "%Y%m%d").date()
    except ValueError:
        try:
            d = datetime.strptime(created, "%Y-%m-%d").date()
        except ValueError:
            return 0.0
    return float((t - d).days)


def sweep_candidates(
    repo_root: Path,
    research_root: Path,
    older_than_days: float = 14.0,
    today: Optional[date] = None,
) -> List[str]:
    """Return id6s eligible for the sweep: aged (>= older_than_days) AND uncited, keeping sets together."""

    all_docs = _all_docs(research_root)
    if not all_docs:
        return []

    all_cited = _collect_all_citations(repo_root, research_root)

    # Group all docs by set_id (or singleton key)
    sets: Dict[str, List[Tuple[Path, R.ResearchName, Dict[str, object]]]] = {}
    for p, parsed, fm in all_docs:
        set_id = parsed.set_id or str(fm.get("set", "")).strip() or None
        key = f"set:{set_id}" if set_id else f"doc:{parsed.id6}"
        sets.setdefault(key, []).append((p, parsed, fm))

    out: List[str] = []
    for key, members in sets.items():
        # Compute ages for all members of the set
        member_ages: List[float] = []
        for p, parsed, fm in members:
            created = str(fm.get("created", parsed.date))
            try:
                member_ages.append(_age_days(created, today))
            except Exception:
                member_ages.append(0.0)

        # Set is only eligible if its newest member is at least older_than_days
        if not member_ages or min(member_ages) < older_than_days:
            continue

        # Include un-archived and uncited members of this eligible set
        for p, parsed, fm in members:
            status = str(fm.get("status", ""))
            # If already in archive with archive status, it is already archived
            if status == "archive" and R.ARCHIVE_DIR in p.parts:
                continue
            if not _is_cited(
                repo_root, research_root, parsed.id6, fm, all_cited=all_cited
            ):
                out.append(parsed.id6)

    return out


# --------------------------------------------------------------------------------------
# Applying a move (frontmatter status + tracked git mv + reference update + index refresh)
# --------------------------------------------------------------------------------------


def apply_moves(repo_root: Path, research_root: Path, moves: List[Move]) -> None:
    """Apply status transitions: rewrite status, git mv into the shard, update references."""

    renames: Dict[str, str] = {}
    for m in moves:
        # Rewrite status in the file's frontmatter first (in place at the old path).
        text = m.old_path.read_text(encoding="utf-8")
        RF._atomic_write(m.old_path, _rewrite_status_in_text(text, m.new_status))
        # Move as a tracked rename.
        src_rel = m.old_path.relative_to(repo_root).as_posix()
        dst_rel = m.new_path.relative_to(repo_root).as_posix()
        RF._git_mv(repo_root, src_rel, dst_rel)
        # The basename is unchanged by an archival move (only the directory changes), so
        # name-based references do not need rewriting; but if a full-path cite exists it is caught
        # by the dangling detector. Record for completeness.
        renames[m.old_path.name] = m.new_path.name
    # Refresh the index after the moves.
    entries, _drift = RI._scan_docs(research_root)
    research_root.mkdir(parents=True, exist_ok=True)
    (research_root / RI.INDEX_JSON).write_text(
        RI.build_index_json(entries), encoding="utf-8"
    )
    (research_root / RI.INDEX_MD).write_text(
        RI.build_index_md(entries), encoding="utf-8"
    )


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def _roots(args: argparse.Namespace) -> Tuple[Path, Path]:
    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    # Layout-aware (IPD awretrofit Order 01): shared research-root resolution.
    return repo_root, R.resolve_research_root(repo_root)


def run_archive(args: argparse.Namespace) -> int:
    """`aw archive [<set-id|doc-id>]`: targeted deep-shelve, or a bare aged sweep."""

    repo_root, research_root = _roots(args)
    target = getattr(args, "target", None)
    apply = getattr(args, "apply", False)
    raw_age = getattr(args, "age", None)

    if target:
        # Targeted: archive a specific doc (by id6) or a whole set (by set-id).
        moves: List[Move] = []
        for p, parsed, fm in _all_docs(research_root):
            if parsed.id6 == target or parsed.set_id == target:
                mv, err = plan_transition(research_root, parsed.id6, "archive")
                if err:
                    print(f"error: {err}")
                    return 2
                moves.append(mv)
        if not moves:
            from agent_workflows.term import Term
            from agent_workflows.result_types import NextAction

            Term().empty_result(
                summary=f"no research doc or set matches '{target}'",
                filters={"target": target},
                next_action=NextAction(
                    command="aw research find", description="find research docs"
                ),
            )
            return 0
        if not apply:
            for m in moves:
                print(
                    f"--- would archive {m.old_path.name} -> {m.new_path.parent.name}/ ---"
                )
            return 0
        apply_moves(repo_root, research_root, moves)
        for m in moves:
            print(
                f"archived {m.id6} -> {m.new_path.relative_to(research_root).as_posix()}"
            )
        return 0

    # Bare sweep: parse age duration and find candidates keeping sets together
    from agent_workflows.duration import parse_age_duration

    try:
        older_than_days = parse_age_duration(raw_age, default_days=14.0)
    except ValueError as e:
        print(f"error: {e}")
        return 2

    candidates = sweep_candidates(
        repo_root, research_root, older_than_days=older_than_days
    )
    if not candidates:
        print("no aged candidates to sweep")
        return 0
    age_label = str(raw_age) if raw_age else "14d"
    print(
        f"Sweep candidates (aged >= {age_label}, keeping sets together; default classification = archive):"
    )
    for id6 in candidates:
        print(f"  {id6} -> archive (override to 'reference' with --keep {id6})")
    if not apply:
        print(
            "preview only; re-run with --apply to move (and --keep <id6> to send to reference)"
        )
        return 0
    keep = set(getattr(args, "keep", None) or [])
    moves = []
    for id6 in candidates:
        new_status = "reference" if id6 in keep else "archive"
        mv, err = plan_transition(research_root, id6, new_status)
        if err:
            print(f"error: {err}")
            return 2
        moves.append(mv)
    apply_moves(repo_root, research_root, moves)
    for m in moves:
        print(
            f"{m.new_status}: {m.id6} -> {m.new_path.relative_to(research_root).as_posix()}"
        )
    return 0


def run_promote(args: argparse.Namespace) -> int:
    """`aw research promote <id6> --to <status>`: a deliberate status transition."""

    repo_root, research_root = _roots(args)
    new_status = getattr(args, "to", None) or "reference"
    mv, err = plan_transition(research_root, getattr(args, "id", "") or "", new_status)
    if err:
        print(f"error: {err}")
        return 2
    if not getattr(args, "apply", False):
        print(
            f"--- would set {mv.id6} status={mv.new_status} and move to {mv.new_path.relative_to(research_root).as_posix()} ---"
        )
        return 0
    apply_moves(repo_root, research_root, [mv])
    print(
        f"{mv.new_status}: {mv.id6} -> {mv.new_path.relative_to(research_root).as_posix()}"
    )
    return 0


def run_check_miscategorized(args: argparse.Namespace) -> int:
    """Report archived-but-cited docs (the miscategorization flag)."""

    repo_root, research_root = _roots(args)
    flagged = find_miscategorized(repo_root, research_root)
    if not flagged:
        print("no miscategorized (archived-but-cited) docs")
        return 0
    for id6 in flagged:
        print(f"{id6}: in archive/ but cited; should it be reference?")
    return 1
