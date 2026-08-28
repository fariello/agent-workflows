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
        status="todo",
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
            status="todo",
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


def _emit_and_write(
    files: List[PlannedFile],
    apply: bool,
    overwrite: bool,
    command_name: str = "research new",
    args: Optional[argparse.Namespace] = None,
) -> int:
    """Common preview/apply path for planned files. Returns an exit code and prints results."""
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        select_output,
    )

    ctx = select_output(args) if args else None

    # No-clobber check up front (so a partial apply never happens).
    if not overwrite:
        for f in files:
            if f.path.exists():
                if ctx and (ctx.is_agent or ctx.is_json):
                    res = CommandResult(
                        command=command_name,
                        status="findings",
                        exit_code=1,
                        summary=f"refusing to overwrite existing path (pass --overwrite): {f.path}",
                    )
                    return get_renderer(ctx).emit(res, ctx)
                print(
                    f"error: refusing to overwrite existing path (pass --overwrite): {f.path}"
                )
                return 1

    if not apply:
        if ctx and (ctx.is_agent or ctx.is_json):
            changes = [
                Change(path=str(f.path), kind="create", applied=False) for f in files
            ]
            res = CommandResult(
                command=command_name,
                status="clean",
                exit_code=0,
                summary=f"would write {len(files)} file(s)",
                changes=changes,
                verified=True,
                complete=True,
            )
            return get_renderer(ctx).emit(res, ctx)
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
        if ctx and (ctx.is_agent or ctx.is_json):
            res = CommandResult(
                command=command_name,
                status="cannot-run",
                exit_code=2,
                summary=f"research write failed: {exc}",
            )
            return get_renderer(ctx).emit(res, ctx)
        print(f"error: research write failed: {exc}")
        return 2

    if ctx and (ctx.is_agent or ctx.is_json):
        changes = [Change(path=str(f.path), kind="create", applied=True) for f in files]
        res = CommandResult(
            command=command_name,
            status="clean",
            exit_code=0,
            summary=f"wrote {len(files)} file(s)",
            changes=changes,
            verified=True,
            complete=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    for f in files:
        print(f"wrote {f.path}")
    print("next step (informational): run `aw research index` to refresh the manifest")
    return 0


# --------------------------------------------------------------------------------------
# In-place frontmatter field updater + set-outcome (IPD xjrdjp E-01)
# --------------------------------------------------------------------------------------


def _render_list(values: List[str]) -> str:
    """Render a frontmatter flow list ``[a, b]`` (empty -> ``[]``), matching build_frontmatter."""

    return "[" + ", ".join(values) + "]" if values else "[]"


def update_frontmatter_fields(text: str, updates: dict) -> str:
    """Return ``text`` with the named first-block frontmatter scalar/list fields replaced in place.

    Only the given ``updates`` (field -> already-rendered string value) are rewritten; every other
    frontmatter line, its order, the ``---`` fences, and the entire document body are preserved
    byte-for-byte. Rewrites ONLY lines inside the FIRST frontmatter block (so a ``status:`` example
    in the body is never touched). A field not present in the block is left absent (the research
    creators always emit all 11 fields, so ``outcome``/``consumed-by`` are present)."""

    lines = text.splitlines(keepends=True)
    in_fm = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_fm = True
            continue
        if in_fm and stripped == "---":
            break
        if not in_fm:
            continue
        for field, value in updates.items():
            if stripped.startswith(f"{field}:"):
                newline = "\n" if line.endswith("\n") else ""
                lines[i] = f"{field}: {value}{newline}"
                break
    return "".join(lines)


def plan_set_outcome(
    research_root: Path,
    id6: str,
    outcome: Optional[str],
    consumed_by: Optional[List[str]],
    clear_consumed: bool = False,
) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    """Plan an outcome/consumed-by update for one doc; returns (path, new_text, error).

    ``outcome`` (when given) must be in the vocabulary. ``consumed_by`` REPLACES the list;
    ``clear_consumed`` (the ``-`` sentinel) empties it. Reads the doc, applies only the requested
    fields, and returns the new text without writing. Preserves all other fields and the body.
    """

    if outcome is not None and outcome not in R.OUTCOMES:
        return None, None, f"outcome must be one of {sorted(R.OUTCOMES)}"
    target: Optional[Path] = None
    for p in sorted(research_root.rglob("*.md")):
        parsed, _err = R.parse_name(p.name)
        if parsed is not None and parsed.id6 == id6:
            target = p
            break
    if target is None:
        return None, None, f"no research file has id6 '{id6}'"
    text = target.read_text(encoding="utf-8")
    updates: dict = {}
    if outcome is not None:
        updates["outcome"] = outcome
    if clear_consumed:
        updates["consumed-by"] = _render_list([])
    elif consumed_by is not None:
        updates["consumed-by"] = _render_list(consumed_by)
    if not updates:
        return None, None, "nothing to set (provide --to and/or --consumed-by)"
    return target, update_frontmatter_fields(text, updates), None


def run_set_outcome(args: argparse.Namespace) -> int:
    """`aw research set-outcome <id6> --to <outcome> [--consumed-by <id6,...>|-]` (preview/--apply)."""

    root = _research_root(args)
    id6 = (getattr(args, "id", "") or "").strip()
    if not id6:
        print("error: an <id6> is required")
        return 2
    raw_consumed = getattr(args, "consumed_by", None)
    clear = raw_consumed is not None and raw_consumed.strip() == "-"
    consumed_list: Optional[List[str]] = None
    if raw_consumed is not None and not clear:
        consumed_list = [c.strip() for c in raw_consumed.split(",") if c.strip()]
    target, new_text, err = plan_set_outcome(
        root,
        id6,
        getattr(args, "to", None),
        consumed_list,
        clear_consumed=clear,
    )
    if err or target is None or new_text is None:
        print(f"error: {err or 'could not plan update'}")
        return 2
    rel = target.relative_to(root).as_posix()
    if not getattr(args, "apply", False):
        bits = []
        if getattr(args, "to", None) is not None:
            bits.append(f"outcome={args.to}")
        if clear:
            bits.append("consumed-by=[] (cleared)")
        elif consumed_list is not None:
            bits.append(f"consumed-by={_render_list(consumed_list)}")
        print(f"--- would update {rel}: {', '.join(bits)} ---")
        return 0
    _atomic_write(target, new_text)
    print(f"updated {rel}")
    # Refresh the index so INDEX.json carries the new consumed-by (E-02).
    try:
        from agent_workflows import research_index as _ridx

        _ridx.run_index(
            argparse.Namespace(
                dir=getattr(args, "dir", None),
                check=False,
                agent=False,
                limit=None,
                quiet=True,
            )
        )
    except Exception:
        pass
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
        from agent_workflows.renderers import get_renderer
        from agent_workflows.result_types import CommandResult, select_output

        ctx = select_output(args)
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="research new",
                status="cannot-run",
                exit_code=2,
                summary=err,
            )
            return get_renderer(ctx).emit(res, ctx)
        print(f"error: {err}")
        return 2
    return _emit_and_write(
        files or [],
        getattr(args, "apply", False),
        getattr(args, "overwrite", False),
        command_name="research new",
        args=args,
    )


def run_new_comparison(args: argparse.Namespace) -> int:
    root = _research_root(args)
    models = [
        m.strip() for m in (getattr(args, "models", None) or "").split(",") if m.strip()
    ]
    if not models:
        from agent_workflows.renderers import get_renderer
        from agent_workflows.result_types import CommandResult, select_output

        ctx = select_output(args)
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="research new-comparison",
                status="cannot-run",
                exit_code=2,
                summary="--models is required (comma-separated)",
            )
            return get_renderer(ctx).emit(res, ctx)
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
        from agent_workflows.renderers import get_renderer
        from agent_workflows.result_types import CommandResult, select_output

        ctx = select_output(args)
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="research new-comparison",
                status="cannot-run",
                exit_code=2,
                summary=err,
            )
            return get_renderer(ctx).emit(res, ctx)
        print(f"error: {err}")
        return 2
    return _emit_and_write(
        files or [],
        getattr(args, "apply", False),
        getattr(args, "overwrite", False),
        command_name="research new-comparison",
        args=args,
    )
