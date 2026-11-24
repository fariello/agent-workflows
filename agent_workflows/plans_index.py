"""Plans scan + find + drift check (Set plans-adopter, Order 03).

``scan_plans`` lists every plan; ``aw find plans`` queries it; ``check_drift`` reports the
non-INDEX drift classes (missing/invalid ``Id``, name-vs-metadata mismatch on a clustered name,
dangling plan citation) and is reached through ``aw check plans --all`` and the
``aw index plans --check`` alias. No INDEX file is written: the SQLite metadata cache replaced the
generated ``INDEX.{json,md}`` views (spec 4sd62s 4.5).

Consumes the shared core (Order 01: id6, Drift shape, dangling detector) and the required plan
``Id`` (Order 02). The scan is RECURSIVE so plans that Order 05 moves into
``<disposition>/YYYYMM/`` shards remain visible; disposition is the TOP-LEVEL directory even
when a plan sits in a shard subdir. Complements (does not replace) the disposition-grouped
``STATUS.md`` from ``plans.py``.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_meta as _am
from agent_workflows import artifact_naming as _naming
from agent_workflows import plans as _plans

# (The former module-level `PLANS_DIR = ".agents/plans"` was dead - resolution is via `_dirs()` /
# `resolve_record_path` - and was removed in Order 05, S5-DC01.)
_EXCLUDE_NAMES = {"INDEX.json", "INDEX.md", "STATUS.md", "README.md"}


class PlanEntry(NamedTuple):
    """One indexed plan (derived from its disposition dir + metadata)."""

    plan_id: Optional[str]
    path: str  # posix, relative to the plans dir
    disposition: (
        str  # top-level dir (pending/executed/superseded/not-executed/reusable)
    )
    date: str
    set_id: Optional[str]
    order: Optional[int]
    status: Optional[str]
    kind: Optional[str]


def _canonical_status(st: Any) -> Optional[str]:
    """Return canonical normalized plan status from an `artifact_meta.State` (D-1)."""
    raw_st = getattr(st, "status", None)
    if raw_st:
        norm = _plans.normalize_status(str(raw_st))
        return norm if norm != _plans.LEGACY_GROUP else str(raw_st)
    raw_legacy = getattr(st, "legacy_raw_status", None)
    if raw_legacy and str(raw_legacy).strip():
        first = str(raw_legacy).strip().split()[0]
        norm = _plans.normalize_status(first)
        return norm if norm != _plans.LEGACY_GROUP else first
    return None


def _state_set_id(st: Any) -> Optional[str]:
    """Return the terse Set id from an `artifact_meta.State` (preserving None for Set-less legacy plans)."""
    if getattr(st, "created_at", None) is None:
        return set_terse_id(getattr(st, "legacy_raw_set", None))
    return set_terse_id(getattr(st, "set_id", None))


def _state_order(st: Any) -> Optional[int]:
    """Return non-negative integer Order from an `artifact_meta.State`, or None."""
    fields = getattr(st, "fields", None)
    if isinstance(fields, dict):
        raw = fields.get("order")
        if isinstance(raw, int) and raw >= 0:
            return raw
        if isinstance(raw, str) and raw.strip().isdigit():
            return int(raw.strip())
    order_nn = getattr(st, "order_nn", None)
    if isinstance(order_nn, int) and order_nn >= 0:
        return order_nn
    return None


def _meta_context_for_plans_dir(
    plans_dir: Path,
) -> Tuple[Any, Path, Optional[Path]]:
    """Build an `artifact_meta` context covering ``plans_dir``."""
    pdir = plans_dir.resolve()
    repo_root: Optional[Path] = None
    for cand in (pdir, *pdir.parents):
        cparts = cand.parts
        if len(cparts) >= 4 and cparts[-3:] == (".aw", "records", "plans"):
            repo_root = cand.parents[2]
            break
        if len(cparts) >= 3 and cparts[-2:] == (".agents", "plans"):
            repo_root = cand.parents[1]
            break
    if repo_root is None:
        from agent_workflows import project_context as _proj_ctx

        repo_root = _proj_ctx.record_owner_root(pdir)
    if repo_root is not None:
        ctx = _am.legacy_context(repo_root)
        records_root = Path(ctx.logical_roots["records"])
        scan_repo = _am._scan_repo_root(ctx, records_root)
        if pdir.is_relative_to(records_root.resolve()) or (
            scan_repo is not None
            and pdir.is_relative_to((scan_repo / ".agents").resolve())
        ):
            return ctx, records_root, scan_repo
    plans_root: Optional[Path] = None
    for cand in (pdir, *pdir.parents):
        if cand.name == "plans":
            plans_root = cand
            break
    if plans_root is not None:
        records_root = plans_root.parent
        state_root = (
            records_root.parent / "state"
            if records_root.name == "records"
            else records_root / ".aw-state"
        )
    else:
        # Standalone directory with no `plans` ancestor (e.g. a bare temp dir): scope scanning
        # strictly to `pdir` rather than escaping to `pdir.parent` (such as `/tmp`).
        records_root = pdir
        state_root = pdir / ".aw-state"
    ctx = type(
        "LegacyContext",
        (),
        {
            "logical_roots": {"records": str(records_root), "state": str(state_root)},
            "repo_root": repo_root or records_root,
        },
    )()
    return ctx, records_root, repo_root


def _cached_plan_states(
    plans_dir: Path, *, include_fields: bool = True
) -> Dict[Path, Any]:
    """Query `artifact_meta.query(type='ipd')` and index results by resolved path under ``plans_dir``."""
    if not plans_dir.is_dir():
        return {}
    pdir_res = plans_dir.resolve()
    ctx, records_root, scan_repo = _meta_context_for_plans_dir(pdir_res)
    with _am.scan_once(), _am.ephemeral_if_uninitialized():
        res = _am.query(type="ipd", project_context=ctx, include_fields=include_fields)
    by_path: Dict[Path, Any] = {}
    for st in res.rows:
        if not st.path:
            continue
        try:
            abs_p = _am.source_path(st.path, records_root, scan_repo).resolve()
        except Exception:
            continue
        if abs_p.is_relative_to(pdir_res):
            by_path[abs_p] = st
    return by_path


def set_terse_id(raw: Optional[str]) -> Optional[str]:
    """Extract the canonical terse set-id from a `Set:` value of the form ``<terse> (<descriptive>)``.

    The leading whitespace-delimited token before any ``(`` is the set-id; the parenthetical is a
    human-readable display name (plans-adopter Order 06). A bare terse id (no parenthetical) also
    parses. Returns None for None.
    """

    if raw is None:
        return None
    return raw.split("(", 1)[0].strip() or None


def plan_entry(
    plans_dir: Path,
    p: Path,
    *,
    ignored_dirs: set[str],
    _states: Optional[Dict[Path, Any]] = None,
) -> Optional[Tuple[PlanEntry, List[_core.Drift]]]:
    """Build a ``PlanEntry`` for a single plan file at ``p`` under ``plans_dir`` via ``artifact_meta``.

    Returns None if ``p`` is skipped (_EXCLUDE_NAMES, ignored_dirs, or not under plans_dir).
    Keyword-only ``ignored_dirs`` must be provided by the caller to prevent redundant git
    subprocesses (F-6).
    """

    if p.name in _EXCLUDE_NAMES or _core.is_ignored_path(p, plans_dir, ignored_dirs):
        return None
    try:
        rel = p.relative_to(plans_dir).as_posix()
    except ValueError:
        return None

    disposition = rel.split("/", 1)[0]
    states = _states if _states is not None else _cached_plan_states(plans_dir)
    st = states.get(p.resolve())
    if st is not None:
        plan_id = None if st.id_derived else (st.id6 or None)
        set_id = _state_set_id(st)
        order = _state_order(st)
        status = _canonical_status(st)
        kind = st.fields.get("plan_role") or None
        date_val = str(st.created_day or st.filename_date or "")
        if not date_val and p.is_file():
            try:
                st_file = _am.read_text(
                    p.read_text(encoding="utf-8"), record_type="ipd"
                )
                raw_date = st_file.fields.get("date") or st_file.created_day
                date_val = str(raw_date).strip() if raw_date else ""
            except OSError:
                date_val = ""
    else:
        text = p.read_text(encoding="utf-8")
        st_text = _am.read_text(text, record_type="ipd")
        plan_id = (
            st_text.id6 if (st_text.id6 and _core.is_valid_id6(st_text.id6)) else None
        )
        set_id = set_terse_id(st_text.legacy_raw_set)
        order_raw = st_text.fields.get("order")
        order = (
            int(str(order_raw).strip())
            if order_raw is not None and str(order_raw).strip().isdigit()
            else None
        )
        status = _canonical_status(st_text)
        kind = st_text.fields.get("plan_role") or None
        date_val = str(st_text.fields.get("date") or st_text.created_day or "")

    entry = PlanEntry(
        plan_id=plan_id,
        path=rel,
        disposition=disposition,
        date=date_val,
        set_id=set_id,
        order=order,
        status=status,
        kind=kind,
    )
    drift: List[_core.Drift] = []
    # Drift class (a): missing/invalid Id. Terminal plans record finished history and are never
    # rewritten (commit aab5c1e27), so only non-terminal plans are expected to carry an Id.
    if disposition not in _plans.TERMINAL:
        if plan_id is None:
            drift.append(_core.Drift(rel, "id-missing", "no `- Id:` metadata line"))
        elif not _core.is_valid_id6(plan_id):
            drift.append(
                _core.Drift(
                    rel, "id-invalid", f"Id '{plan_id}' is not a 6-char base36 token"
                )
            )
    return entry, drift


def plan_files(
    plans_dir: Path, *, ignored_dirs: Optional[set[str]] = None
) -> List[Path]:
    """Return sorted list of plan file Paths under ``plans_dir``.

    This is THE canonical definition of which files are plans.
    Recursion (`rglob`) and the ignored-path filter are COUPLED: a recursive walk without
    the ignored-path filter returns box-local `untracked/` plans that are never committed.
    (See backlog item `mlcbk9` and `specs._spec_files` docstring recording the same lesson.)

    Skips `_EXCLUDE_NAMES` (`INDEX.json`, `INDEX.md`, `STATUS.md`, `README.md`) and any path
    matching `_core.is_ignored_path(p, plans_dir, ignored_dirs)`.
    For any returned plan `p`, its top-level lifecycle disposition is `p.relative_to(plans_dir).parts[0]`.
    """
    if not plans_dir.is_dir():
        return []
    if ignored_dirs is None:
        ignored_dirs = _core.get_ignored_dirs(plans_dir)
    return [
        p
        for p in sorted(plans_dir.rglob("*.md"))
        if p.name not in _EXCLUDE_NAMES
        and not _core.is_ignored_path(p, plans_dir, ignored_dirs)
    ]


def scan_plans(plans_dir: Path) -> Tuple[List[PlanEntry], List[_core.Drift]]:
    """Recursively scan every plan under ``plans_dir`` via ``artifact_meta.query``; return (entries, drift).

    Disposition is the first path component under ``plans_dir`` (so a plan inside a
    ``<disposition>/YYYYMM/`` shard keeps its top-level disposition). Drift here covers the
    metadata classes (missing/invalid Id); name-vs-metadata and stale-view/dangling are added by
    ``check_drift``.
    """

    entries: List[PlanEntry] = []
    drift: List[_core.Drift] = []
    if not plans_dir.is_dir():
        return entries, drift
    ignored_dirs = _core.get_ignored_dirs(plans_dir)
    states = _cached_plan_states(plans_dir, include_fields=True)
    for p in plan_files(plans_dir, ignored_dirs=ignored_dirs):
        res = plan_entry(plans_dir, p, ignored_dirs=ignored_dirs, _states=states)
        if res is not None:
            entry, item_drift = res
            entries.append(entry)
            drift.extend(item_drift)
    return entries, drift


# --------------------------------------------------------------------------------------
# find
# --------------------------------------------------------------------------------------


def query(
    entries: List[PlanEntry],
    *,
    plan_id: Optional[str] = None,
    set_id: Optional[str] = None,
    status: Optional[str] = None,
    disposition: Optional[str] = None,
    status_not: Optional[str | Sequence[str]] = None,
) -> List[PlanEntry]:
    out = list(entries)
    if plan_id:
        out = [e for e in out if e.plan_id == plan_id]
    if set_id:
        out = [e for e in out if e.set_id == set_id]
    if status:
        out = [e for e in out if e.status == status or e.disposition == status]
    if disposition:
        out = [e for e in out if e.disposition == disposition]
    if status_not:
        from agent_workflows import plans as _p_mod

        if isinstance(status_not, str):
            not_list = [s.strip() for s in status_not.split(",") if s.strip()]
        else:
            not_list = []
            for item in status_not:
                if item:
                    not_list.extend(
                        s.strip() for s in str(item).split(",") if s.strip()
                    )
        not_set = {s.lower() for s in not_list}
        out = [
            e
            for e in out
            if (e.status or "").lower() not in not_set
            and (e.disposition or "").lower() not in not_set
            and (_p_mod.normalize_status(e.status) or "").lower() not in not_set
            and (_p_mod.normalize_status(e.disposition) or "").lower() not in not_set
        ]
    return sorted(out, key=lambda e: (e.set_id or "", e.order or 0, e.path))


# --------------------------------------------------------------------------------------
# citation matcher + current-id resolver for the dangling detector (plan area)
# --------------------------------------------------------------------------------------

# A plan CITATION: the clustered/full plan filename OR a bare stem that resolves to a PLAN via the
# manifest. To avoid the specs-namespace collision, the dangling detector resolves ids from the
# plan manifest only; a bare stem is matched by the caller-supplied resolver, not blindly.
_PLAN_ID_CITE_RE = re.compile(r"\bPLAN-([0-9a-z]{6})\b")


def _plan_cite_matcher(line: str) -> List[str]:
    """Extract plan-id citations: the explicit ``PLAN-<id6>`` handle (bare stems/filenames resolve
    via the manifest path, not by id, so they are handled by the rename tool in Order 04)."""

    return _PLAN_ID_CITE_RE.findall(line)


# --------------------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------------------


def check_drift(repo_root: Path, plans_dir: Path) -> List[_core.Drift]:
    entries, drift = scan_plans(plans_dir)
    # Drift class (b): name-vs-metadata mismatch on a CLUSTERED name only. Old-style
    # YYYYMMDD-HHMM-NN-slug.md names can coincidentally fit the clustering regex (HHMM as a set-id,
    # a slug's first letters as an id6), so distinguish by the second segment: the clustering grammar
    # never has a 4-digit HHMM there (a set-id is kebab, not exactly 4 digits). A name is treated as
    # clustered only when the regex matches AND the second segment is not a bare 4-digit HHMM.
    for e in entries:
        base = Path(e.path).name
        # The clustered grammar is parsed by the single naming authority (IPD o6b8l3).
        m = _naming.parse_clustered(base)
        if not m or re.fullmatch(r"\d{4}", m.group("set")):
            continue  # not clustered (or an old-style HHMM name)
        if e.plan_id and m.group("id6") != e.plan_id:
            drift.append(
                _core.Drift(
                    e.path,
                    "name-metadata-mismatch",
                    f"name id {m.group('id6')} != metadata Id {e.plan_id}",
                )
            )
        if e.set_id and m.group("set") != e.set_id:
            drift.append(
                _core.Drift(
                    e.path,
                    "name-metadata-mismatch",
                    f"name set {m.group('set')} != metadata Set {e.set_id}",
                )
            )
    # Drift class (d): dangling plan citation via the shared-core detector, using the ONE unified
    # id6-handle matcher (IPD 3cmnfc E-04): the PLAN-<id6> handle recognized uniformly with the
    # research RSCH-<id6> handle. The dead-bare-filename flag (OQ-01 option B) is delivered as a
    # tested library primitive (artifact_refs.dead_filename_citations) but is NOT wired as an
    # always-on drift rule here: on real prose it flags legitimate historical/example filenames
    # (false positives), which would violate the Set's "no new aw check findings" criterion and
    # OQ-01's own low-false-positive mandate; enabling it awaits a durable "known real names"
    # source (run decision 05-3cmnfc-D3). setid citations are NOT checked (option C deferred).
    # The severity is stamped here (`check_engine.enrich_drift`) because
    # `check_engine.check_content` forwards these findings without enriching them, and an
    # un-enriched `severity=""` fails `artifact_core.drift_exit_code`. The INDEX-file drift class
    # was deleted by spec `4sd62s` 4.5 (plan `w819as`): the SQLite metadata cache replaced the
    # INDEX files, so an absent or out-of-date INDEX file is not drift.
    from agent_workflows import artifact_refs as _refs
    from agent_workflows import check_engine as _ce

    current_ids = {e.plan_id for e in entries if e.plan_id}
    for d in _core.find_dangling_citations(
        repo_root,
        current_ids=current_ids,
        cite_matcher=_refs.make_cite_matcher("PLAN"),
        exclude_root=plans_dir,
    ):
        drift.append(
            _ce.enrich_drift(
                _core.Drift(f"{d.file}:{d.line}", "dangling-citation", f"PLAN-{d.id6}")
            )
        )
    return drift


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


def run_find(args: argparse.Namespace) -> int:
    repo_root, plans_dir = _dirs(args)
    entries, _drift = scan_plans(plans_dir)
    results = query(
        entries,
        plan_id=getattr(args, "id", None),
        set_id=getattr(args, "set", None),
        status=getattr(args, "status", None),
        disposition=getattr(args, "disposition", None),
        status_not=getattr(args, "status_not", None),
    )
    if not results:
        from agent_workflows.result_types import NextAction
        from agent_workflows.term import Term

        filters_dict = {}
        for k in ("id", "set", "status", "status_not", "disposition"):
            v = getattr(args, k, None)
            if v:
                filters_dict[k] = v
        Term().empty_result(
            summary="no matching plans",
            filters=filters_dict if filters_dict else None,
            next_action=NextAction(
                command="aw find plans", description="find across all plans"
            )
            if filters_dict
            else NextAction(
                command="aw ipd scaffold", description="scaffold a new plan"
            ),
        )
        return 0
    for e in results:
        print(f"{e.plan_id or '??????'}\t{e.disposition}\t{e.set_id or '-'}\t{e.path}")
    return 0
