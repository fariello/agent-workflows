"""Scan plan/prompt lifecycle files and read their readiness ``Status:`` (DECISIONS D52/Dnn).

This is the single source of truth for the plan readiness vocabulary and the legacy mapping. It is
shared by the ``aw plans`` board (``cli.py``) and the repo drift-guard test
(``tests/test_plan_status.py``), so the two can never diverge.

Directories carry DISPOSITION (pending/executed/superseded/not-executed/reusable; ``done`` is an
accepted alias for ``executed``). The front-matter ``- Status:`` line carries READINESS. See D52 and
``.agents/workflows/assess/templates/ipd.md``.

Everything here is stdlib-only (zero runtime deps, D46). It READS front-matter only; it never
renames, moves, or writes plan files (``render_status_index`` returns text; the caller writes it).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

# Readiness vocabulary (D52; `auto-approved` added by D65). Lowercase-kebab; front-matter is the
# single source of truth. `auto-approved` is a sibling of `approved` at the ready-to-execute tier:
# it means an automated checker (e.g. /verify-execution) cleared a low-complexity mechanical
# corrective to run WITHOUT human review; it is NOT human approval.
PRE_TERMINAL = ("draft", "to-review", "reviewed", "approved", "auto-approved")
TERMINAL = ("executed", "superseded", "not-executed")
STANDING = ("reusable",)
RECOGNIZED = frozenset(PRE_TERMINAL + TERMINAL + STANDING)

# Disposition directories under .agents/plans (and the `done` alias for executed).
DISPOSITION_DIRS = (
    "pending",
    "executed",
    "superseded",
    "not-executed",
    "reusable",
    "done",
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

_STATUS_RE = re.compile(r"^- Status:\s*(?P<val>\S+)", re.MULTILINE)

# Optional ordered-SET metadata (D82). ADVISORY only: `Set:`/`Order:` group related plans and make
# their intended run order queryable/visible; they do NOT auto-execute, do not gate approval, and do
# not change the `Status:` lifecycle. They are ORTHOGONAL to the filename convention and `NN` (which
# keep their same-minute-disambiguator role). `Set:` is a lowercase-kebab id shared by a set's
# members; `Order:` is the 1-based position within the set (meaningful only alongside `Set:`).
_SET_RE = re.compile(r"^- Set:\s*(?P<val>\S+)", re.MULTILINE)
_ORDER_RE = re.compile(r"^- Order:\s*(?P<val>\S+)", re.MULTILINE)
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


def read_status(md: Path) -> Optional[str]:
    """Return the canonical readiness status parsed from a file's front-matter, or None."""

    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return None
    m = _STATUS_RE.search(text)
    return normalize_status(m.group("val")) if m else None


def read_set(md: Path) -> "tuple[Optional[str], Optional[int]]":
    """Return the advisory ``(set_id, order)`` from a file's front-matter (D82).

    ``set_id`` is None when absent or malformed (not a valid lowercase-kebab id); ``order`` is None
    when absent or not a positive integer. Reads front-matter only; writes nothing.
    """

    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return (None, None)
    sm = _SET_RE.search(text)
    om = _ORDER_RE.search(text)
    raw_set = sm.group("val") if sm else None
    set_id = raw_set if is_set_id_valid(raw_set) else None
    order = parse_order(om.group("val")) if om else None
    return (set_id, order)


def scan(root: Path, include_prompts: bool = True) -> List[PlanRecord]:
    """Scan ``<root>/.agents/plans`` (and ``.agents/prompts``) for plan/prompt records.

    Reads front-matter only; renames/moves nothing. ``README.md`` files are skipped. Returns an
    empty list when the areas do not exist.
    """

    records: List[PlanRecord] = []
    agents = root / ".agents"
    areas = ["plans"] + (["prompts"] if include_prompts else [])
    for area in areas:
        base = agents / area
        if not base.is_dir():
            continue
        for disp in DISPOSITION_DIRS:
            d = base / disp
            if not d.is_dir():
                continue
            for f in sorted(d.glob("*.md")):
                if f.name == "README.md":
                    continue
                set_id, order = read_set(f)
                records.append(PlanRecord(f, area, disp, read_status(f), set_id, order))
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
        "Generated by `aw plans --write-index` (do not edit by hand). Front-matter `Status:` is the "
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
