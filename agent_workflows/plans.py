"""Scan plan/prompt lifecycle files and read their readiness ``Status:`` (DECISIONS D52/Dnn).

This is the single source of truth for the plan readiness vocabulary and the legacy mapping. It is
shared by the ``aw plans`` board (``cli.py``) and the repository drift-guard test
(``tests/test_plan_status.py``, with live-corpus tests marked ``livecorpus``), so the two can
never diverge.

Directories carry DISPOSITION (pending/executed/superseded/not-executed/reusable; ``done`` is an
accepted alias for ``executed``). The front-matter ``- Status:`` line carries READINESS. See D52 and
``.agents/workflows/assess/templates/ipd.md``.

Everything here is stdlib-only (zero runtime deps, D46). It READS front-matter only; it never
renames, moves, or writes plan files (``render_status_index`` returns text; the caller writes it).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import lifecycle_dirs as _LD

# Readiness vocabulary (D52; `auto-approved` added by D65). Lowercase-kebab; front-matter is the
# single source of truth. `auto-approved` is a sibling of `approved` at the ready-to-execute tier:
# it means an automated checker (e.g. /verify-execution) cleared a low-complexity mechanical
# corrective to run WITHOUT human review; it is NOT human approval.
PRE_TERMINAL = ("draft", "to-review", "reviewed", "approved", "auto-approved")
TERMINAL = ("executed", "superseded", "not-executed")
STANDING = ("reusable",)
RECOGNIZED = frozenset(PRE_TERMINAL + TERMINAL + STANDING)

# Disposition directories under .agents/plans (and the `done` alias for executed).
DISPOSITION_DIRS: Tuple[str, ...] = _LD.LIFECYCLE_SUBDIRS["plans"] + (
    _LD.PLANS_DONE_ALIAS,
)
DIR_TERMINAL = {
    "executed": "executed",
    "superseded": "superseded",
    "not-executed": "not-executed",
}

# Legacy free-text status -> canonical readiness (D52 backward-compat). Case-normalized first.
LEGACY_MAP = {
    "pending": "to-review",
    "done": "executed",  # `done` is the accepted alias for `executed`
}

# Group/sort order for the board: lifecycle order, then legacy/unknown last.
_READINESS_ORDER = {
    name: i for i, name in enumerate(PRE_TERMINAL + TERMINAL + STANDING)
}
LEGACY_GROUP = "legacy/unknown"

_SET_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SET_ID_LEN = 40


def is_set_id_valid(value: Optional[str]) -> bool:
    """Return True if ``value`` is a valid ``Set:`` id (lowercase-kebab, 1..MAX_SET_ID_LEN chars)."""
    if not value or not isinstance(value, str):
        return False
    if len(value) > MAX_SET_ID_LEN:
        return False
    return bool(_SET_ID_RE.match(value))


def parse_order(value: Optional[str]) -> Optional[int]:
    """Parse an ``Order:`` value into a positive int (1-based), or None if absent/invalid."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw.isdigit():
        return None
    n = int(raw)
    return n if n >= 1 else None


class PlanRecord(NamedTuple):
    path: Path
    area: str  # "plans" or "prompts"
    disposition: str  # the directory name (pending/executed/... or "" if top-level)
    status: Optional[str]  # canonical readiness, LEGACY_GROUP, or None (no status)
    set_id: Optional[str] = (
        None  # advisory ordered-set id (D82), or None if not in a set
    )
    order: Optional[int] = None  # 1-based position within the set, or None


def normalize_status(raw: Optional[str]) -> Optional[str]:
    """Case-normalize and legacy-map a raw Status token to the canonical vocabulary.

    Returns a recognized readiness value, ``LEGACY_GROUP`` for an unrecognized token, or ``None``
    when there is no status at all.
    """

    if raw is None:
        return None
    val = raw.strip().rstrip(".").lower()
    if not val:
        return None
    val = LEGACY_MAP.get(val, val)
    return val if val in RECOGNIZED else LEGACY_GROUP


def _status_from_state(st: object) -> Optional[str]:
    """Compute canonical readiness from a cached or in-memory `artifact_meta.State`."""
    raw = getattr(st, "legacy_raw_status", None)
    if not raw or not str(raw).strip():
        return None
    tok = str(raw).strip().split()[0]
    return normalize_status(tok)


def _cached_states_by_path(root: Path) -> Dict[Path, object]:
    """Return cached `artifact_meta.State` rows keyed by resolved Path for ``root``."""
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import project_context as _proj_ctx

    ctx = _proj_ctx.resolve_project_context(target_repo=str(root))
    records_root = Path(ctx.logical_roots["records"])
    scan_repo = _meta._scan_repo_root(ctx, records_root)
    has_tree = records_root.is_dir() or (
        scan_repo is not None
        and (
            (scan_repo / ".aw" / "records").is_dir() or (scan_repo / ".agents").is_dir()
        )
    )
    if not has_tree:
        return {}
    res = _meta.query(project_context=ctx)
    by_path: Dict[Path, object] = {}
    for st in res.rows:
        if not st.path:
            continue
        try:
            abs_p = _meta.source_path(st.path, records_root, scan_repo).resolve()
        except Exception:
            continue
        by_path[abs_p] = st
    return by_path


def read_status(md: Path, text: Optional[str] = None) -> Optional[str]:
    """Return the canonical readiness status via `artifact_meta`, or None."""
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import project_context as _proj_ctx

    if text is not None:
        return _status_from_state(_meta.read_text(text, record_type="ipd"))

    owner = _proj_ctx.record_owner_root(md)
    if owner is not None:
        try:
            by_path = _cached_states_by_path(owner)
            st = by_path.get(md.resolve())
            if st is not None:
                return _status_from_state(st)
        except OSError:
            return None
        except Exception:
            pass

    try:
        content = md.read_text(encoding="utf-8")
    except OSError:
        return None
    return _status_from_state(_meta.read_text(content, record_type="ipd"))


def read_set(md: Path) -> "tuple[Optional[str], Optional[int]]":
    """Return the advisory ``(set_id, order)`` parsed via `artifact_meta.read_text` (D82).

    ``set_id`` is None when absent or malformed (not a valid lowercase-kebab id); ``order`` is None
    when absent or not a positive integer.
    """
    from agent_workflows import artifact_meta as _meta

    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return (None, None)
    st = _meta.read_text(text, record_type="ipd")
    raw_set = st.legacy_raw_set
    set_id = raw_set if is_set_id_valid(raw_set) else None
    raw_order = st.fields.get("order") if isinstance(st.fields, dict) else None
    order = (
        parse_order(raw_order.strip().split()[0])
        if isinstance(raw_order, str) and raw_order.strip()
        else parse_order(raw_order)
    )
    return (set_id, order)


def _resolve_area_dir(root: Path, area: str) -> Path:
    """Resolve the physical dir for a records ``area`` (plans|prompts), layout-aware.

    Prefers the migrated ``.aw/records/<area>`` (via ``resolve_record_path``); falls back to the
    legacy ``<root>/.agents/<area>`` only when the resolved dir is absent AND the legacy dir exists
    (the retention-window read-fallback, mirroring ``plans_index._dirs``). IPD awretrofit Order 01.
    """
    from agent_workflows.record_producers import resolve_record_path
    from agent_workflows.project_context import (
        project_records_dir,
        has_stored_records_placement,
    )

    modern = project_records_dir(root) / area
    if has_stored_records_placement(root):
        base = modern
    else:
        try:
            base = resolve_record_path(area, target_repo=str(root))
        except Exception:
            base = modern
    if not base.is_dir() and (root / ".agents" / area).is_dir():
        base = root / ".agents" / area
    elif not base.is_dir() and modern.is_dir():
        base = modern
    return base


def scan(root: Path, include_prompts: bool = True) -> List[PlanRecord]:
    """Scan the records ``plans`` (and ``prompts``) area for plan/prompt records via `artifact_meta`.

    Layout-aware (IPD awretrofit Order 01): resolves ``.aw/records/{plans,prompts}`` with a legacy
    ``.agents/{plans,prompts}`` read-fallback. ``README.md`` files are skipped.
    """
    from agent_workflows import artifact_meta as _meta

    records: List[PlanRecord] = []
    areas = ["plans"] + (["prompts"] if include_prompts else [])
    by_path: Optional[Dict[Path, object]] = None
    with _meta.scan_once():
        for area in areas:
            base = _resolve_area_dir(root, area)
            if not base.is_dir():
                continue
            if by_path is None:
                try:
                    by_path = _cached_states_by_path(root)
                except Exception:
                    by_path = {}
            for disp in DISPOSITION_DIRS:
                d = base / disp
                if not d.is_dir():
                    continue
                for f in sorted(d.glob("*.md")):
                    if f.name == "README.md":
                        continue
                    st = by_path.get(f.resolve())
                    status = (
                        _status_from_state(st) if st is not None else read_status(f)
                    )
                    set_id, order = read_set(f)
                    records.append(PlanRecord(f, area, disp, status, set_id, order))
    return records


def group(records: List[PlanRecord]) -> "Dict[str, Dict[str, List[PlanRecord]]]":
    """Group records by disposition dir, then by readiness status (lifecycle-ordered)."""

    by_disp: Dict[str, Dict[str, List[PlanRecord]]] = {}
    for rec in records:
        status = rec.status if rec.status is not None else "(no status)"
        by_disp.setdefault(rec.disposition, {}).setdefault(status, []).append(rec)
    return by_disp


def _status_sort_key(status: str):
    return (_READINESS_ORDER.get(status, len(_READINESS_ORDER) + 1), status)


def group_sets(records: List[PlanRecord]) -> "Dict[str, List[PlanRecord]]":
    """Group records that carry a ``Set:`` by set id (D82). Records without a set are excluded."""

    by_set: Dict[str, List[PlanRecord]] = {}
    for rec in records:
        if rec.set_id:
            by_set.setdefault(rec.set_id, []).append(rec)
    return by_set


def _set_member_sort_key(rec: PlanRecord):
    # Ordered members first (by Order), then unordered members by filename. `order is None` sorts last.
    return (rec.order is None, rec.order if rec.order is not None else 0, rec.path.name)


def set_warnings(set_id: str, members: List[PlanRecord]) -> List[str]:
    """Return soft-warning strings for a set: duplicate `Order:` values, or a mix of ordered and
    unordered members. Empty when the set is cleanly ordered (or cleanly unordered)."""

    warnings: List[str] = []
    orders = [m.order for m in members if m.order is not None]
    if len(orders) != len(set(orders)):
        warnings.append(f"set `{set_id}`: duplicate Order values")
    n_ordered = len(orders)
    if 0 < n_ordered < len(members):
        warnings.append(
            f"set `{set_id}`: some members have Order and some do not (partial ordering)"
        )
    return warnings


def render_status_index(root: Path, records: List[PlanRecord]) -> str:
    """Return a deterministic plain-Markdown STATUS.md body (grouped list, OQ1).

    Deterministic ordering so re-running ``--write-index`` produces no spurious diff.
    """

    lines = [
        "# Plan status index",
        "",
        "Generated by `aw ipd board --write-index` (do not edit by hand). Front-matter `Status:` is the "
        "source of truth; the directory is the disposition. See DECISIONS D52.",
        "",
    ]
    by_disp = group(records)
    total = len(records)
    lines.append(f"Total: {total} plan/prompt file(s).")
    lines.append("")
    for disp in DISPOSITION_DIRS:
        statuses = by_disp.get(disp)
        if not statuses:
            continue
        count = sum(len(v) for v in statuses.values())
        lines.append(f"## {disp}/ ({count})")
        lines.append("")
        for status in sorted(statuses, key=_status_sort_key):
            recs = statuses[status]
            lines.append(f"- **{status}** ({len(recs)})")
            for rec in sorted(recs, key=lambda r: r.path.name):
                lines.append(f"  - `{rec.path.relative_to(root).as_posix()}`")
        lines.append("")

    # Secondary "Sets" view (D82): advisory ordered-set grouping. Kept separate from the primary
    # status board above so set-grouping never disrupts the readiness view. Omitted entirely when no
    # plan declares a `Set:`.
    by_set = group_sets(records)
    if by_set:
        lines.append(f"## Sets ({len(by_set)})")
        lines.append("")
        lines.append(
            "Advisory ordered groupings (`Set:`/`Order:` front-matter). ADVISORY only: they do not "
            "auto-execute or gate approval; the human still approves each plan."
        )
        lines.append("")
        for set_id in sorted(by_set):
            members = by_set[set_id]
            lines.append(f"- **{set_id}** ({len(members)})")
            for rec in sorted(members, key=_set_member_sort_key):
                order = rec.order if rec.order is not None else "-"
                lines.append(
                    f"  - {order}. `{rec.path.relative_to(root).as_posix()}` [{rec.disposition}]"
                )
            for warn in set_warnings(set_id, members):
                lines.append(f"  - WARNING: {warn}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
