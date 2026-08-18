"""The ``aw research`` creation verbs: ``new`` and ``new-comparison`` (Set research-org, Order 02).

Deterministic creation of correctly-named research docs with starter frontmatter, so naming is a
tool call rather than a fallible convention. Consumes the Order 01 contract
(``agent_workflows.research_contract``); it does NOT restate the id/grammar/vocab/frontmatter and it
does NOT assume the index (Order 03).

Writing-command safety mirrors ``aw ipd scaffold`` (``ipd_authoring``): preview by default, an
explicit ``--apply`` to write, atomic write-to-temp-rename, refuse to clobber an existing file
without ``--overwrite``, and a nonzero exit on any failure (never a false success).
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import research_contract as R


# --------------------------------------------------------------------------------------
# id generation (collision-checked against existing on-disk id6 tokens)
# --------------------------------------------------------------------------------------


def _existing_id6s(research_root: Path) -> set:
    """Collect every ``<id6>`` already present in a filename under the research tree."""

    found = set()
    if not research_root.is_dir():
        return found
    for p in research_root.rglob("*.md"):
        parsed, err = R.parse_name(p.name)
        if parsed is not None:
            found.add(parsed.id6)
    return found


def generate_id6(existing: set, _rng=None) -> str:
    """Generate a fresh 6-char base36-lowercase id not in ``existing`` (delegates to the core)."""

    return _core.generate_id6(existing, _rng)


# --------------------------------------------------------------------------------------
# frontmatter rendering
# --------------------------------------------------------------------------------------


def build_frontmatter(
    *,
    id6: str,
    created: str,
    set_id: str,
    order: str,
    topic: List[str],
    model: Optional[str],
    kind: str,
    status: str,
    outcome: str,
    summary: str,
    consumed_by: Optional[List[str]] = None,
) -> str:
    """Render a full spec-5.8 frontmatter block (all 11 fields, canonical order)."""

    topic_str = "[" + ", ".join(topic) + "]" if topic else "[]"
    consumed = consumed_by or []
    consumed_str = "[" + ", ".join(consumed) + "]" if consumed else "[]"
    model_str = model if model else ""
    lines = [
        "---",
        f"id: {id6}",
        f"created: {created}",
        f"set: {set_id}",
        f"order: {order}",
        f"topic: {topic_str}",
        f"model: {model_str}",
        f"kind: {kind}",
        f"status: {status}",
        f"outcome: {outcome}",
        f"summary: {summary}",
        f"consumed-by: {consumed_str}",
        "---",
        "",
    ]
    return "\n".join(lines)


def _next_order_for_set(research_root: Path, set_id: str) -> int:
    """Return the next NN for an existing set (max existing + 1), or 0 for a new set."""

    if not research_root.is_dir():
        return 0
    orders = []
    for p in research_root.rglob("*.md"):
        parsed, err = R.parse_name(p.name)
        if parsed is not None and parsed.set_id == set_id:
            orders.append(int(parsed.order))
    return (max(orders) + 1) if orders else 0


def _set_date_for_set(research_root: Path, set_id: str, default: str) -> str:
    """Return the shared date of an existing set, or ``default`` for a new set."""

    if not research_root.is_dir():
        return default
    for p in sorted(research_root.rglob("*.md")):
        parsed, err = R.parse_name(p.name)
        if parsed is not None and parsed.set_id == set_id:
            return parsed.date
    return default


# --------------------------------------------------------------------------------------
# atomic write (mirrors ipd_authoring._atomic_write)
# --------------------------------------------------------------------------------------


def _atomic_write(path: Path, text: str) -> None:
    """Write-to-temp-then-rename so an interrupted apply never leaves a partial file (core)."""

    _core.atomic_write(path, text, prefix=".research-tmp-")


# A planned document: its resolved path and its starter content.
class PlannedFile(NamedTuple):
    path: Path
    content: str


def plan_new(
    *,
    research_root: Path,
    kind: str,
    slug: str,
    summary: str,
    set_id: Optional[str] = None,
    model: Optional[str] = None,
    topic: Optional[List[str]] = None,
    date_str: Optional[str] = None,
    existing_ids: Optional[set] = None,
) -> Tuple[Optional[List[PlannedFile]], Optional[str]]:
    """Plan a single ``new`` document (no writing). Returns (files, None) or (None, error)."""

    kind_res = R.normalize_kind(kind)
    if not kind_res.ok:
        return None, kind_res.message
    kind = kind_res.value or kind

    if model is not None:
        model_res = R.normalize_model(model)
        if not model_res.ok:
            return None, model_res.message
        model = model_res.value

    slug_k = R.kebab(slug) if slug else R.kebab(summary)
    if not slug_k:
        return None, "a --slug or --summary is required to derive the name"

    # Omitted set -> singleton whose set-id is the kebab slug (or summary fallback).
    derived_set = R.kebab(set_id) if set_id else slug_k
    today = date_str or date.today().strftime("%Y%m%d")
    set_date = _set_date_for_set(research_root, derived_set, today)
    order_n = _next_order_for_set(research_root, derived_set)

    ids = existing_ids if existing_ids is not None else _existing_id6s(research_root)
    id6 = generate_id6(ids)

    name = R.ResearchName(
        date=set_date,
        set_id=derived_set,
        order=f"{order_n:02d}",
        id6=id6,
        slug=slug_k,
        model=model,
        kind=kind,
    )
    filename = R.format_name(name)
    content = build_frontmatter(
        id6=id6,
        created=today,
        set_id=derived_set,
        order=f"{order_n:02d}",
        topic=topic or [],
        model=model,
        kind=kind,
        status="intake",
        outcome="none-yet",
        summary=summary,
    )
    return [PlannedFile(research_root / filename, content)], None


def plan_new_comparison(
    *,
    research_root: Path,
    set_id: str,
    slug: str,
    models: List[str],
    summary: str = "",
    topic: Optional[List[str]] = None,
    date_str: Optional[str] = None,
) -> Tuple[Optional[List[PlannedFile]], Optional[str]]:
    """Plan the multi-model comparison scaffold: 00 prompt, 01..N model reports, N+1 reconciliation."""

    derived_set = R.kebab(set_id)
    slug_k = R.kebab(slug)
    if not derived_set or not slug_k:
        return None, "--set and --slug are required"

    norm_models: List[str] = []
    for m in models:
        res = R.normalize_model(m)
        if not res.ok:
            return None, res.message
        norm_models.append(res.value or m)

    today = date_str or date.today().strftime("%Y%m%d")
    existing = _existing_id6s(research_root)
    files: List[PlannedFile] = []

    def _mk(order_n: int, kind: str, model: Optional[str], sm: str) -> PlannedFile:
        id6 = generate_id6(existing)
        existing.add(id6)
        name = R.ResearchName(
            date=today,
            set_id=derived_set,
            order=f"{order_n:02d}",
            id6=id6,
            slug=slug_k,
            model=model,
            kind=kind,
        )
        content = build_frontmatter(
            id6=id6,
            created=today,
            set_id=derived_set,
            order=f"{order_n:02d}",
            topic=topic or [],
            model=model,
            kind=kind,
            status="intake",
            outcome="none-yet",
            summary=sm or summary,
        )
        return PlannedFile(research_root / R.format_name(name), content)

    # 00 = originating prompt
    files.append(
        _mk(0, "research-prompt", None, "Originating prompt for the comparison set.")
    )
    # 01..N = one report per model
    for i, m in enumerate(norm_models, start=1):
        files.append(_mk(i, "research-report", m, f"{m} report."))
    # N+1 = reconciliation
    files.append(
        _mk(
            len(norm_models) + 1,
            "reconciliation-report",
            "reconciliation",
            "Synthesis of the model reports.",
        )
    )
    return files, None


# --------------------------------------------------------------------------------------
# CLI handlers
# --------------------------------------------------------------------------------------


def _research_root(args: argparse.Namespace) -> Path:
    from agent_workflows.project_context import resolve_verb_repo_root

    root = resolve_verb_repo_root(getattr(args, "dir", None))
    return R.resolve_research_root(root)


def _emit_and_write(files: List[PlannedFile], apply: bool, overwrite: bool) -> int:
    """Common preview/apply path for planned files. Returns an exit code and prints results."""

    # No-clobber check up front (so a partial apply never happens).
    if not overwrite:
        for f in files:
            if f.path.exists():
                print(
                    f"error: refusing to overwrite existing path (pass --overwrite): {f.path}"
                )
                return 1
    if not apply:
        for f in files:
            print(f"--- would write {f.path} ---")
            print(f.content)
        print(
            "next step (informational): after --apply, run `aw research index` to refresh the manifest"
        )
        return 0
    try:
        for f in files:
            _atomic_write(f.path, f.content)
    except Exception as exc:  # noqa: BLE001
        print(f"error: research write failed: {exc}")
        return 2
    for f in files:
        print(f"wrote {f.path}")
    print("next step (informational): run `aw research index` to refresh the manifest")
    return 0


def run_new(args: argparse.Namespace) -> int:
    root = _research_root(args)
    topic = [
        t.strip() for t in (getattr(args, "topic", None) or "").split(",") if t.strip()
    ]
    files, err = plan_new(
        research_root=root,
        kind=getattr(args, "kind", ""),
        slug=getattr(args, "slug", "") or "",
        summary=getattr(args, "summary", "") or "",
        set_id=getattr(args, "set", None),
        model=getattr(args, "model", None),
        topic=topic,
        date_str=getattr(args, "date", None),
    )
    if err:
        print(f"error: {err}")
        return 2
    return _emit_and_write(
        files or [], getattr(args, "apply", False), getattr(args, "overwrite", False)
    )


def run_new_comparison(args: argparse.Namespace) -> int:
    root = _research_root(args)
    models = [
        m.strip() for m in (getattr(args, "models", None) or "").split(",") if m.strip()
    ]
    if not models:
        print("error: --models is required (comma-separated)")
        return 2
    topic = [
        t.strip() for t in (getattr(args, "topic", None) or "").split(",") if t.strip()
    ]
    files, err = plan_new_comparison(
        research_root=root,
        set_id=getattr(args, "set", "") or "",
        slug=getattr(args, "slug", "") or "",
        models=models,
        summary=getattr(args, "summary", "") or "",
        topic=topic,
        date_str=getattr(args, "date", None),
    )
    if err:
        print(f"error: {err}")
        return 2
    return _emit_and_write(
        files or [], getattr(args, "apply", False), getattr(args, "overwrite", False)
    )
