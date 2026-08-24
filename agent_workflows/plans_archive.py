"""Plans weekly shards + archival (Set plans-adopter, Order 05).

Tames the flat, unbounded terminal disposition dirs by moving cold plans into weekly
``YYYYMM-Www/`` shards INSIDE each terminal dir (``executed/``/``superseded/``/``not-executed/``),
via deliberate, tool-invoked verbs only (never a background side effect). ``pending/`` and
``reusable/`` (hot/standing) stay flat.

* ``aw plans archive <id6|set-id>``: deep-shelve a plan (or a whole Set) into its disposition dir's
  weekly shard; preview by default, ``--apply`` to move.
* bare ``aw plans archive``: a deliberate sweep of terminal plans still at a disposition-dir root
  older than a default age, with a preview before any move.

A shard move is a DIR-ONLY move: it changes the plan's path but NOT its filename, and plans are
cited by basename/stem, so it is a CITATION NO-OP (no reference rewrite). The manifest scan (Order
03) is recursive, so sharded plans stay visible; the INDEX is refreshed after any move. Moves keep
the plan ``Id`` and are atomic tracked ``git mv``. Consumes the Order-01 core (shard math, git mv)
and the Order-03 manifest.
"""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import plans_index as _idx

PLANS_DIR = ".agents/plans"
TERMINAL_DIRS = ("executed", "superseded", "not-executed")
DEFAULT_SWEEP_AGE_DAYS = 14

_ID_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")


class ShardMove(NamedTuple):
    id6: Optional[str]
    old_path: Path
    new_path: Path


def _at_disposition_root(rel_parts: List[str]) -> bool:
    """True when a plan sits directly in a terminal disposition dir (not already in a shard)."""

    return len(rel_parts) == 2 and rel_parts[0] in TERMINAL_DIRS


def _plan_date(text: str) -> str:
    m = re.search(r"(?m)^- Date:\s*(\d{8}|\d{4}-\d{2}-\d{2})\s*$", text)
    if not m:
        return "20260101"
    raw = m.group(1)
    return raw.replace("-", "") if "-" in raw else raw


def _shard_target(
    plans_dir: Path, disposition: str, plan_date: str, filename: str
) -> Path:
    return plans_dir / disposition / _core.shard_for_date(plan_date) / filename


def plan_shard_move(plans_dir: Path, plan_path: Path) -> Optional[ShardMove]:
    """Plan moving a terminal-root plan into its weekly shard. None if not eligible."""

    rel = plan_path.relative_to(plans_dir)
    parts = rel.parts
    if not _at_disposition_root(list(parts)):
        return None  # not at a terminal-dir root (hot/standing, or already sharded)
    text = plan_path.read_text(encoding="utf-8")
    m = _ID_RE.search(text)
    dst = _shard_target(plans_dir, parts[0], _plan_date(text), plan_path.name)
    return ShardMove(m.group(1) if m else None, plan_path, dst)


def _find_targets(plans_dir: Path, selector: str) -> List[Path]:
    """Resolve a selector (a plan Id or a Set id) to terminal-root plan paths."""

    out: List[Path] = []
    for p in plans_dir.rglob("*.md"):
        if p.name in _idx._EXCLUDE_NAMES:
            continue
        rel = p.relative_to(plans_dir)
        if not _at_disposition_root(list(rel.parts)):
            continue
        text = p.read_text(encoding="utf-8")
        m = _ID_RE.search(text)
        sm = re.search(r"(?m)^- Set:\s*(.+?)\s*$", text)
        if (m and m.group(1) == selector) or (sm and sm.group(1) == selector):
            out.append(p)
    return sorted(out)


def _age_days(plan_date: str, today: Optional[date] = None) -> float:
    t = today or date.today()
    try:
        d = datetime.strptime(plan_date, "%Y%m%d").date()
    except ValueError:
        try:
            d = datetime.strptime(plan_date, "%Y-%m-%d").date()
        except ValueError:
            return 0.0
    return float((t - d).days)


def sweep_candidates(
    plans_dir: Path,
    *,
    older_than_days: float = DEFAULT_SWEEP_AGE_DAYS,
    today: Optional[date] = None,
) -> List[Path]:
    """Terminal-root plans older than ``older_than_days`` (keeping sets together)."""

    all_terminal_root: List[Tuple[Path, str, str]] = []
    set_ages: Dict[str, List[float]] = {}

    for p in sorted(plans_dir.rglob("*.md")):
        if p.name in _idx._EXCLUDE_NAMES:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        sm = re.search(r"(?m)^- Set:\s*(.+?)\s*$", text)
        set_id = sm.group(1).strip() if sm else ""
        p_date = _plan_date(text)
        age = _age_days(p_date, today)
        if set_id:
            set_ages.setdefault(set_id, []).append(age)
        rel = p.relative_to(plans_dir)
        if _at_disposition_root(list(rel.parts)):
            all_terminal_root.append((p, set_id, p_date))

    out: List[Path] = []
    for p, set_id, p_date in all_terminal_root:
        if set_id and set_id in set_ages:
            # Set is only swept if its newest member is at least older_than_days
            if min(set_ages[set_id]) >= older_than_days:
                out.append(p)
        else:
            if _age_days(p_date, today) >= older_than_days:
                out.append(p)

    return sorted(out)


def _refresh_index(repo_root: Path, plans_dir: Path) -> None:
    entries, _drift = _idx.scan_plans(plans_dir)
    plans_dir.mkdir(parents=True, exist_ok=True)
    (plans_dir / _idx.INDEX_JSON).write_text(
        _idx.build_index_json(entries), encoding="utf-8"
    )
    (plans_dir / _idx.INDEX_MD).write_text(
        _idx.build_index_md(entries), encoding="utf-8"
    )


def apply_shard_moves(repo_root: Path, plans_dir: Path, moves: List[ShardMove]) -> None:
    for m in moves:
        src_rel = m.old_path.relative_to(repo_root).as_posix()
        dst_rel = m.new_path.relative_to(repo_root).as_posix()
        _core.git_mv(repo_root, src_rel, dst_rel)
    _refresh_index(repo_root, plans_dir)


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


def run_archive(args: argparse.Namespace) -> int:
    repo_root, plans_dir = _dirs(args)
    target = getattr(args, "target", None)
    apply = getattr(args, "apply", False)
    raw_age = getattr(args, "age", None)

    if target:
        paths = _find_targets(plans_dir, target)
        if not paths:
            from agent_workflows.term import Term
            from agent_workflows.result_types import NextAction

            Term().empty_result(
                summary=f"no terminal-root plan or Set matches '{target}'",
                filters={"target": target},
                next_action=NextAction(
                    command="aw find plans", description="find plans"
                ),
            )
            return 0
        moves = [mv for mv in (plan_shard_move(plans_dir, p) for p in paths) if mv]
        if not apply:
            for mv in moves:
                print(
                    f"--- would archive {mv.old_path.name} -> {mv.new_path.parent.name}/ ---"
                )
            return 0
        apply_shard_moves(repo_root, plans_dir, moves)
        for mv in moves:
            print(
                f"archived {mv.old_path.name} -> {mv.new_path.relative_to(plans_dir).as_posix()}"
            )
        return 0

    # Bare sweep: parse age duration and find candidates keeping sets together
    from agent_workflows.duration import parse_age_duration

    try:
        older_than_days = parse_age_duration(
            raw_age, default_days=DEFAULT_SWEEP_AGE_DAYS
        )
    except ValueError as e:
        print(f"error: {e}")
        return 2

    cands = sweep_candidates(plans_dir, older_than_days=older_than_days)
    if not cands:
        from agent_workflows.term import Term
        from agent_workflows.result_types import NextAction

        Term().empty_result(
            summary="no aged terminal-root plans to sweep",
            filters=None,
            next_action=NextAction(command="aw find plans", description="find plans"),
        )
        return 0
    moves = [mv for mv in (plan_shard_move(plans_dir, p) for p in cands) if mv]
    if not apply:
        age_label = str(raw_age) if raw_age else f"{DEFAULT_SWEEP_AGE_DAYS}d"
        print(
            f"Sweep candidates (terminal-root plans aged >= {age_label}, keeping sets together):"
        )
        for mv in moves:
            print(f"  {mv.old_path.name} -> {mv.new_path.parent.name}/")
        print("preview only; re-run with --apply to move")
        return 0
    apply_shard_moves(repo_root, plans_dir, moves)
    for mv in moves:
        print(
            f"archived {mv.old_path.name} -> {mv.new_path.relative_to(plans_dir).as_posix()}"
        )
    return 0
