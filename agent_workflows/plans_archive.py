"""Plans monthly shards + archival (Set plans-adopter, Order 05).

Tames the flat, unbounded terminal disposition dirs by moving cold plans into monthly
``YYYYMM/`` shards INSIDE each terminal dir (``executed/``/``superseded/``/``not-executed/``),
via deliberate, tool-invoked verbs only (never a background side effect). ``pending/`` and
``reusable/`` (hot/standing) stay flat.

* ``aw plans archive <id6|set-id>``: deep-shelve a plan (or a whole Set) into its disposition dir's
  monthly shard; preview by default, ``--apply`` to move.
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
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_meta as _am
from agent_workflows import artifact_naming as _naming
from agent_workflows import plans_index as _idx

PLANS_DIR = ".agents/plans"
TERMINAL_DIRS = ("executed", "superseded", "not-executed")
DEFAULT_SWEEP_AGE_DAYS = 14

_VALID_DATE_RE = re.compile(r"^(?:\d{8}|\d{4}-\d{2}-\d{2})$")


class ShardMove(NamedTuple):
    id6: Optional[str]
    old_path: Path
    new_path: Path


def _at_disposition_root(rel_parts: List[str]) -> bool:
    """True when a plan sits directly in a terminal disposition dir (not already in a shard)."""

    return len(rel_parts) == 2 and rel_parts[0] in TERMINAL_DIRS


def _normalize_date_value(raw: Optional[object]) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    s = raw.strip()
    if not _VALID_DATE_RE.fullmatch(s):
        return None
    return s.replace("-", "") if "-" in s else s


def _plan_date(text: str) -> str:
    st = _am.read_text(text, record_type="ipd")
    val = _normalize_date_value(st.fields.get("date") or st.created_day)
    return val or "20260101"


def _resolve_plan_date(
    filename: str, text: str = "", *, state: Optional[Any] = None
) -> str:
    """Resolve a plan's date across four tiers: front matter, clustered filename, legacy filename, 20260101.

    NOTE THE DELIBERATE INVERSION OF 949enf's TIER ORDER:
    `plans_refs._preserved_date` reads filename first, but this resolver reads
    FRONT MATTER FIRST. That inversion is deliberate and measured (OQ-01, F-06):
    front-matter-first touches only the no-match branch and is provably a no-op on
    every input where existing code produces an answer (0 changed across the corpus).
    Filename-first would additionally change the result whenever a usable `- Date:`
    disagrees with a filename (e.g. `- Date: 20260801` under a `20260716-` name),
    which is an unrequested behavior change and an undecided question (mt6j1p).
    Furthermore, 949enf's reason to invert does not apply here: a RENAME must not
    recompute the date it is preserving, whereas an ARCHIVE is merely reading a
    date to place a file.

    Filename dates are additionally validated as real calendar dates with
    `datetime.strptime` (review PR-001) to fall through on impossible dates (like
    `20261399`), while front-matter acceptance is preserved unchanged.
    """
    if state is not None:
        fields = getattr(state, "fields", None)
        state_date = _normalize_date_value(
            getattr(state, "created_day", None)
            or (fields.get("date") if isinstance(fields, dict) else None)
        )
        if state_date:
            return state_date
    if text:
        st_text = _am.read_text(text, record_type="ipd")
        text_date = _normalize_date_value(
            st_text.fields.get("date") or st_text.created_day
        )
        if text_date:
            return text_date

    parsed_clustered = _naming._CLUSTERED_RE.match(filename)
    if parsed_clustered:
        d = parsed_clustered.group("date")
        try:
            datetime.strptime(d, "%Y%m%d")
            return d
        except ValueError:
            pass

    parsed_legacy = _naming._LEGACY_TIMESTAMP_RE.match(filename)
    if parsed_legacy:
        d = parsed_legacy.group("date")
        try:
            datetime.strptime(d, "%Y%m%d")
            return d
        except ValueError:
            pass

    return "20260101"


def _shard_target(
    plans_dir: Path, disposition: str, plan_date: str, filename: str
) -> Path:
    return plans_dir / disposition / _core.shard_for_date(plan_date) / filename


def plan_shard_move(
    plans_dir: Path,
    plan_path: Path,
    *,
    _states: Optional[Dict[Path, Any]] = None,
) -> Optional[ShardMove]:
    """Plan moving a terminal-root plan into its weekly shard. None if not eligible."""

    rel = plan_path.relative_to(plans_dir)
    parts = rel.parts
    if not _at_disposition_root(list(parts)):
        return None  # not at a terminal-dir root (hot/standing, or already sharded)
    states = (
        _states
        if _states is not None
        else _idx._cached_plan_states(plans_dir, include_fields=False)
    )
    st = states.get(plan_path.resolve())
    text = ""
    if st is not None:
        plan_id = None if st.id_derived else (st.id6 or None)
        if st.created_at is None and not st.created_day:
            try:
                text = plan_path.read_text(encoding="utf-8")
            except OSError:
                text = ""
    else:
        text = plan_path.read_text(encoding="utf-8")
        st_text = _am.read_text(text, record_type="ipd")
        plan_id = (
            st_text.id6 if (st_text.id6 and _core.is_valid_id6(st_text.id6)) else None
        )
    dst = _shard_target(
        plans_dir,
        parts[0],
        _resolve_plan_date(plan_path.name, text, state=st),
        plan_path.name,
    )
    return ShardMove(plan_id, plan_path, dst)


def _plan_status(
    plan_path: Path,
    plans_dir: Path,
    *,
    _states: Optional[Dict[Path, Any]] = None,
) -> str:
    """Read the declared status of a plan via ``artifact_meta``, noting if it is already in a shard."""
    try:
        states = (
            _states
            if _states is not None
            else _idx._cached_plan_states(plans_dir, include_fields=False)
        )
        st_obj = states.get(plan_path.resolve())
        if st_obj is not None:
            st = _idx._canonical_status(st_obj) or plan_path.parent.name
        else:
            text = plan_path.read_text(encoding="utf-8")
            st = (
                _idx._canonical_status(_am.read_text(text, record_type="ipd"))
                or plan_path.parent.name
            )
    except Exception:
        st = "unknown"
    try:
        rel = plan_path.resolve().relative_to(plans_dir.resolve())
        if len(rel.parts) > 2 and rel.parts[0] in TERMINAL_DIRS:
            return f"{st}, already in {rel.parts[1]}/ shard"
    except Exception:
        pass
    return st


def _find_targets(
    repo_root_or_plans_dir: Path,
    plans_dir_or_selector: Union[Path, str],
    selector_or_none: Optional[str] = None,
    *,
    force: bool = False,
) -> Tuple[List[Path], Optional[str]]:
    """Resolve an explicit target through selectors.resolve_for_mutation and filter to terminal-root plans."""
    from agent_workflows import selectors

    if selector_or_none is None:
        plans_dir = repo_root_or_plans_dir
        selector = str(plans_dir_or_selector)
        from agent_workflows.project_context import resolve_verb_repo_root

        repo_root = resolve_verb_repo_root(plans_dir)
    else:
        repo_root = repo_root_or_plans_dir
        plans_dir = Path(plans_dir_or_selector)
        selector = str(selector_or_none)

    paths, err = selectors.resolve_for_mutation(
        repo_root,
        "plans",
        selector,
        force=force,
    )
    if err is not None:
        return [], err

    # Post-resolution filter: confine to plans directly at a terminal disposition root
    terminal_root: List[Path] = []
    pdir_resolved = plans_dir.resolve()
    for p in paths:
        if p.name in _idx._EXCLUDE_NAMES:
            continue
        try:
            rel = p.resolve().relative_to(pdir_resolved)
        except ValueError:
            continue
        if _at_disposition_root(list(rel.parts)):
            terminal_root.append(p)

    if paths and not terminal_root:
        if len(paths) == 1:
            p = paths[0]
            st = _plan_status(p, plans_dir)
            return [], f"plan '{p.name}' is not terminal (status: {st})"
        names = ", ".join(f"'{p.name}' ({_plan_status(p, plans_dir)})" for p in paths)
        return [], f"matched plans are not terminal: {names}"

    return sorted(terminal_root), None


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
    """Terminal-root plans older than ``older_than_days`` (keeping sets together) via ``artifact_meta.query``."""

    all_terminal_root: List[Tuple[Path, str, str]] = []
    set_ages: Dict[str, List[float]] = {}
    states = _idx._cached_plan_states(plans_dir, include_fields=False)

    for p in _idx.plan_files(plans_dir):
        st = states.get(p.resolve())
        text = ""
        if st is not None:
            set_id = _idx._state_set_id(st) or ""
            if st.created_at is None and not st.created_day:
                try:
                    text = p.read_text(encoding="utf-8")
                except Exception:
                    text = ""
        else:
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                continue
            st_text = _am.read_text(text, record_type="ipd")
            set_id = _idx.set_terse_id(st_text.legacy_raw_set) or ""
        p_date = _resolve_plan_date(p.name, text, state=st)
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


def apply_shard_moves(
    repo_root: Path, plans_dir: Path, moves: List[ShardMove]
) -> List[str]:
    """Apply archival shard moves; RETURN repo-relative touched paths (the MOVED FILES) for the
    self-commit offer (selfcommit jgcm68 E-02). The caller drives the offer.

    The regenerated INDEX.json/INDEX.md are deliberately NOT in the returned list. They are still
    refreshed on disk (`_refresh_index` below), but generated manifests are not committed by any
    `aw` verb (idxuntrack `4r0qp1` E-07), and the caller commits this list verbatim."""
    from agent_workflows import artifact_rename as _rename

    touched: List[str] = []
    for m in moves:
        # IPD v45j1n E-04: a plan with a `meta/<id6>.jsonl` log records the shard move as a `rename`
        # event (verb `archive`); a legacy plan (every plan before the cutover) is moved as before.
        log_id6 = _rename.log_format_id6(m.old_path, repo_root, "plans")
        if log_id6 is not None:
            touched.extend(
                _rename.move_with_log_event(
                    repo_root, log_id6, m.old_path, m.new_path, verb="archive"
                )[0]
            )
            continue
        src_rel = m.old_path.relative_to(repo_root).as_posix()
        dst_rel = m.new_path.relative_to(repo_root).as_posix()
        _core.git_mv(repo_root, src_rel, dst_rel)
        touched.append(src_rel)
        touched.append(dst_rel)
    _refresh_index(repo_root, plans_dir)
    seen: dict = {}
    for t in touched:
        seen.setdefault(t, None)
    return list(seen.keys())


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def _dirs(args: argparse.Namespace) -> Tuple[Path, Path]:
    from agent_workflows.project_context import (
        resolve_verb_repo_root,
        project_records_dir,
        has_stored_records_placement,
    )

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    # Layout-aware (IPD awretrofit Order 01): resolve .aw/records/plans with a legacy
    # .agents/plans read-fallback, mirroring plans_index._dirs.
    from agent_workflows.record_producers import resolve_record_path

    modern_plans = project_records_dir(repo_root) / "plans"
    if has_stored_records_placement(repo_root):
        plans_dir = modern_plans
    else:
        try:
            plans_dir = resolve_record_path("plans", target_repo=str(repo_root))
        except Exception:
            plans_dir = modern_plans
    if not plans_dir.is_dir() and (repo_root / ".agents" / "plans").is_dir():
        plans_dir = repo_root / ".agents" / "plans"
    elif not plans_dir.is_dir() and modern_plans.is_dir():
        plans_dir = modern_plans
    return repo_root, plans_dir


def run_archive(args: argparse.Namespace) -> int:
    repo_root, plans_dir = _dirs(args)
    target = getattr(args, "target", None)
    apply = getattr(args, "apply", False)
    raw_age = getattr(args, "age", None)

    if target:
        force = bool(getattr(args, "force", False))
        paths, err = _find_targets(repo_root, plans_dir, target, force=force)
        if not paths:
            from agent_workflows.term import Term
            from agent_workflows.result_types import NextAction

            if err:
                if err.startswith("no plans artifact matched"):
                    summary = f"no plan or Set matches '{target}'"
                else:
                    summary = err
            else:
                summary = f"no terminal-root plan or Set matches '{target}'"

            Term().empty_result(
                summary=summary,
                filters={"target": target},
                next_action=NextAction(
                    command="aw find plans", description="find plans"
                ),
            )
            return 2
        with _am.scan_once(), _am.ephemeral_if_uninitialized():
            states = _idx._cached_plan_states(plans_dir, include_fields=False)
            moves = [
                mv
                for mv in (plan_shard_move(plans_dir, p, _states=states) for p in paths)
                if mv
            ]
        if not apply:
            for mv in moves:
                print(
                    f"--- would archive {mv.old_path.name} -> {mv.new_path.parent.name}/ ---"
                )
            return 0
        touched = apply_shard_moves(repo_root, plans_dir, moves)
        for mv in moves:
            print(
                f"archived {mv.old_path.name} -> {mv.new_path.relative_to(plans_dir).as_posix()}"
            )
        _offer_archive_commit(args, repo_root, touched)
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

    with _am.scan_once(), _am.ephemeral_if_uninitialized():
        cands = sweep_candidates(plans_dir, older_than_days=older_than_days)
        if not cands:
            from agent_workflows.term import Term
            from agent_workflows.result_types import NextAction

            Term().empty_result(
                summary="no aged terminal-root plans to sweep",
                filters=None,
                next_action=NextAction(
                    command="aw find plans", description="find plans"
                ),
            )
            return 0
        states = _idx._cached_plan_states(plans_dir, include_fields=False)
        moves = [
            mv
            for mv in (plan_shard_move(plans_dir, p, _states=states) for p in cands)
            if mv
        ]
    if not apply:
        age_label = str(raw_age) if raw_age else f"{DEFAULT_SWEEP_AGE_DAYS}d"
        print(
            f"Sweep candidates (terminal-root plans aged >= {age_label}, keeping sets together):"
        )
        for mv in moves:
            print(f"  {mv.old_path.name} -> {mv.new_path.parent.name}/")
        print("preview only; re-run with --apply to move")
        return 0
    touched = apply_shard_moves(repo_root, plans_dir, moves)
    for mv in moves:
        print(
            f"archived {mv.old_path.name} -> {mv.new_path.relative_to(plans_dir).as_posix()}"
        )
    _offer_archive_commit(args, repo_root, touched)
    return 0


def _offer_archive_commit(
    args: argparse.Namespace, repo_root: Path, touched: List[str]
) -> None:
    """selfcommit jgcm68 E-02: offer to path-scoped-commit the archived plan moves. The regenerated
    INDEX is NOT included (idxuntrack `4r0qp1` E-07): it is refreshed on disk but never committed.
    Interactive-gated via child-01 ``offer_commit`` (TTY prompts; non-interactive-without
    ``--commit`` is a NO-OP); path-scoped, no push, no ``add -A``; unrelated dirty files never
    folded in. A commit failure is non-fatal (the archive already happened)."""
    if not touched:
        return
    from agent_workflows import git_commit_helper as _gch

    # jgcm68 D2: unstage the git-mv'd paths first so offer_commit's `git add` cleanly re-stages them.
    _gch._git(repo_root, ["reset", "--quiet", "HEAD", "--", *touched])
    outcome = _gch.offer_commit(
        repo_root,
        touched,
        message="chore(plans): archive aged artifacts and regenerate index",
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
