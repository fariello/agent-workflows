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
from datetime import date, datetime
from pathlib import Path
import re
from typing import List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import attention_contract as A
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
        if R.companion_owner_stem(p, research_root) is not None:
            continue
        parsed, err = R.parse_name(p.name)
        if parsed is not None:
            found.add(parsed.id6)
    return found


def generate_id6(existing: set, _rng=None) -> str:
    """Generate a fresh 6-char base36-lowercase id not in ``existing`` (delegates to the core).

    KEPT as the module's published seam (it is re-exported and called by tests), but it is NOT a
    second source of truth: it forwards to the pure core generator and nothing else. The
    repository-wide collision set is supplied by :func:`_mint_research_id6` below, which is what the
    two real mint sites call (IPD sk7ggr E-01).
    """

    return _core.generate_id6(existing, _rng)


def _mint_research_id6(research_root: Path, existing: set) -> str:
    """Mint a research id6 against the REPOSITORY-WIDE set, unioned with ``existing``.

    IPD sk7ggr E-01. Research was the tree most implicated in the motivating collision yet its mint
    path was per-tree (``_existing_id6s`` scans research filenames only), so a fresh research id6
    could equal an existing plan's. ``research_root`` is a TREE root, so the repo root is derived
    from it via ``artifact_core.repo_root_of``.
    """

    return _core.mint_id6(_core.repo_root_of(research_root), existing)


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
    status: Optional[str] = None,
    outcome: str,
    summary: str,
    consumed_by: Optional[List[str]] = None,
    priority: Optional[str] = None,
) -> str:
    """Render a full spec-5.8 frontmatter block (the 11 required fields, canonical order).

    xprio Order 6vgd0k: an OPTIONAL `priority:` line is appended ONLY when a non-empty `priority`
    is given (the shared low/medium/high vocab). Omitted priority emits NO line, so a doc created
    without it stays contract-clean (priority is recognized-but-optional, not a required field)."""

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
    ]
    if status is not None:
        lines.append(f"status: {status}")
    lines.extend(
        [
            f"outcome: {outcome}",
            f"summary: {summary}",
            f"consumed-by: {consumed_str}",
        ]
    )
    if priority:
        lines.append(f"priority: {priority}")
    lines += ["---", ""]
    return "\n".join(lines)


def _next_order_for_set(research_root: Path, set_id: str, kind: str = "") -> int:
    """Return the next NN for an existing set (max existing + 1), or 0 for a new prompt set, or 1 for a new non-prompt set."""

    if not research_root.is_dir():
        return 0 if kind == "research-prompt" else 1
    orders = []
    for p in research_root.rglob("*.md"):
        if R.companion_owner_stem(p, research_root) is not None:
            continue
        parsed, err = R.parse_name(p.name)
        if parsed is not None and parsed.set_id == set_id:
            orders.append(int(parsed.order))
    return (max(orders) + 1) if orders else (0 if kind == "research-prompt" else 1)


def _set_date_for_set(research_root: Path, set_id: str, default: str) -> str:
    """Return the shared date of an existing set, or ``default`` for a new set."""

    if not research_root.is_dir():
        return default
    for p in sorted(research_root.rglob("*.md")):
        if R.companion_owner_stem(p, research_root) is not None:
            continue
        parsed, err = R.parse_name(p.name)
        if parsed is not None and parsed.set_id == set_id:
            return parsed.date
    return default


# A planned document: its resolved path and its starter content.
class PlannedFile(NamedTuple):
    path: Path
    content: str


def _refuse_unsafe_descriptive(
    verb: str,
    flag: str,
    value: Optional[str],
    *,
    bound_length: bool = True,
) -> Optional[str]:
    """Judge one descriptive value against Section 8.8 output-safety.

    Delegates to attention_contract.refuse_unsafe_descriptive (IPD 685iq8).
    Preserves module-private name for existing call sites and shipped tests.
    """
    from agent_workflows import attention_contract as _A

    return _A.refuse_unsafe_descriptive(verb, flag, value, bound_length=bound_length)


def _refuse_unsafe_date(verb: str, value: Optional[str]) -> Optional[str]:
    """Judge one candidate date string against research's date grammar and calendar validity.

    E-01 (IPD iumgvk): Derived from research's own date grammar slot (_CORE_RE).
    The regex check (\\A[0-9]{8}\\Z) is an ASCII format check, not a calendar check;
    the regex alone admits unreachable calendar dates such as 99999999 and 20261332.
    Per OQ-01, validate format first (ASCII-only [0-9]{8}, refusing fullwidth digits like
    '２０２６０９２９'), then calendar validity via datetime.strptime(..., "%Y%m%d"),
    refusing both with exit 2 and the same message shape naming the verb, --date,
    YYYYMMDD, and the received value.
    """
    if value is None:
        return None
    # Format check: research grammar uses YYYYMMDD, not ISO YYYY-MM-DD.
    # ASCII [0-9]{8} closes non-ASCII Unicode digits (PR-002).
    if not re.match(r"\A[0-9]{8}\Z", value):
        return f"{verb}: --date must be YYYYMMDD (got {value!r})"
    # Calendar check: regex alone accepts 99999999 and 20261332.
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError:
        return f"{verb}: --date must be YYYYMMDD (got {value!r})"
    return None


def plan_new(
    *,
    research_root: Path,
    kind: str,
    slug: str,
    summary: str,
    short_description: Optional[str] = None,
    set_id: Optional[str] = None,
    model: Optional[str] = None,
    topic: Optional[List[str]] = None,
    date_str: Optional[str] = None,
    existing_ids: Optional[set] = None,
    priority: Optional[str] = None,
    order: Optional[int] = None,
) -> Tuple[Optional[List[PlannedFile]], Optional[str]]:
    """Plan a single ``new`` document (no writing). Returns (files, None) or (None, error)."""

    kind_res = R.normalize_kind(kind)
    if not kind_res.ok:
        return None, kind_res.message
    kind = kind_res.value or kind

    # xprio 6vgd0k: an optional --priority must be in the shared vocab when given (reuse, no fork).
    if priority is not None:
        from agent_workflows import backlog

        if priority not in backlog.PRIORITIES:
            return None, f"priority must be one of {sorted(backlog.PRIORITIES)}"

    if model is not None:
        model_res = R.normalize_model(model)
        if not model_res.ok:
            return None, model_res.message
        model = model_res.value

    # E-02: Refuse unsafe descriptive value for --summary before minting an id6.
    sum_err = _refuse_unsafe_descriptive("aw research new", "--summary", summary)
    if sum_err:
        return None, sum_err
    if short_description is not None and short_description != summary:
        sd_err = _refuse_unsafe_descriptive(
            "aw research new", "--summary", short_description
        )
        if sd_err:
            return None, sd_err

    # E-03: Refuse unsafe descriptive values for each --topic token before minting an id6.
    if topic:
        for t in topic:
            t_err = _refuse_unsafe_descriptive(
                "aw research new", f"--topic token '{t}'", t
            )
            if t_err:
                return None, t_err

    slug_k = R.kebab(slug) if slug else R.kebab(summary)
    if not slug_k:
        return None, "a --slug or --summary is required to derive the name"

    # E-02 (IPD iumgvk): Validate --date format and calendar validity before minting an id6.
    date_err = _refuse_unsafe_date("aw research new", date_str)
    if date_err:
        return None, date_err

    # Omitted set -> singleton whose set-id is the kebab slug (or summary fallback).
    derived_set = R.kebab(set_id) if set_id else slug_k
    today = date_str or date.today().strftime("%Y%m%d")
    set_date = _set_date_for_set(research_root, derived_set, today)
    if order is not None:
        try:
            order_int = int(order)
        except (ValueError, TypeError):
            return None, f"--order must be between 0 and 999 (got {order!r})"
        if order_int < 0 or order_int > 999:
            return None, f"--order must be between 0 and 999 (got {order})"
        if research_root.is_dir():
            for p in sorted(research_root.rglob("*.md")):
                if R.companion_owner_stem(p, research_root) is not None:
                    continue
                parsed, _ = R.parse_name(p.name)
                if parsed is not None and parsed.set_id == derived_set:
                    if int(parsed.order) == order_int:
                        return (
                            None,
                            f"order {order_int:02d} in set '{derived_set}' is already occupied by {p.name}",
                        )
        order_n = order_int
    else:
        order_n = _next_order_for_set(research_root, derived_set, kind)

    ids = existing_ids if existing_ids is not None else _existing_id6s(research_root)
    id6 = _mint_research_id6(research_root, ids)

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
    dest_path = research_root / filename
    try:
        content = _render_research_create(
            research_root=research_root,
            dest_path=dest_path,
            id6=id6,
            created=today,
            set_id=derived_set,
            order=order_n,
            topic=topic or [],
            model=model,
            kind=kind,
            summary=summary,
            short_description=short_description,
            priority=priority,
        )
    except ValueError as exc:
        return None, str(exc)
    return [PlannedFile(dest_path, content)], None


def _compose_comparison_summary(user_summary: str, role: str) -> str:
    """Compose the user's comparison summary with the document role.

    If user_summary is empty or all whitespace, returns role unchanged.
    Otherwise, candidate is f"{user} ({role.rstrip('.')})".
    If that candidate fails A.is_safe_descriptive, degrades to stripped user_summary alone.
    """
    user = user_summary.strip()
    if not user:
        return role
    candidate = f"{user} ({role.rstrip('.')})"
    if not A.is_safe_descriptive(candidate):
        return user
    return candidate


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

    # E-03: Refuse unsafe descriptive values for --summary and each --topic token.
    sum_err = _refuse_unsafe_descriptive(
        "aw research new-comparison", "--summary", summary
    )
    if sum_err:
        return None, sum_err

    if topic:
        for t in topic:
            t_err = _refuse_unsafe_descriptive(
                "aw research new-comparison", f"--topic token '{t}'", t
            )
            if t_err:
                return None, t_err

    # E-02 (IPD iumgvk): Validate --date format and calendar validity before minting an id6.
    date_err = _refuse_unsafe_date("aw research new-comparison", date_str)
    if date_err:
        return None, date_err

    today = date_str or date.today().strftime("%Y%m%d")
    # IPD sk7ggr E-01: seed the collision pool with the REPOSITORY-WIDE id6 set, then keep adding each
    # minted id6 as the comparison Set is planned. Unioned ONCE here rather than per document: `_mk`
    # runs once per planned file and a repo-wide rescan inside it would repeat the whole scan N times
    # for one command.
    existing = _existing_id6s(research_root) | _core.global_id6s(
        _core.repo_root_of(research_root)
    )
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
        dest_path = research_root / R.format_name(name)
        content = _render_research_create(
            research_root=research_root,
            dest_path=dest_path,
            id6=id6,
            created=today,
            set_id=derived_set,
            order=order_n,
            topic=topic or [],
            model=model,
            kind=kind,
            summary=sm,
        )
        return PlannedFile(dest_path, content)

    try:
        # 00 = originating prompt
        files.append(
            _mk(
                0,
                "research-prompt",
                None,
                _compose_comparison_summary(
                    summary, "Originating prompt for the comparison set."
                ),
            )
        )
        # 01..N = one report per model
        for i, m in enumerate(norm_models, start=1):
            files.append(
                _mk(
                    i,
                    "research-report",
                    m,
                    _compose_comparison_summary(summary, f"{m} report."),
                )
            )
        # N+1 = reconciliation
        files.append(
            _mk(
                len(norm_models) + 1,
                "reconciliation-report",
                "reconciliation",
                _compose_comparison_summary(summary, "Synthesis of the model reports."),
            )
        )
    except ValueError as exc:
        return None, str(exc)
    return files, None


# --------------------------------------------------------------------------------------
# CLI handlers
# --------------------------------------------------------------------------------------


def _rel_posix(target: Path, root: Path) -> str:
    """``target`` relative to ``root`` as a POSIX string, tolerant of two spellings of one directory.

    ``root`` comes back RESOLVED from the repo-root resolver while ``target`` may be built from the
    caller's unresolved ``--dir``. On Windows those differ as an 8.3 short name versus the long name
    (``RUNNER~1`` vs the full profile name), and on POSIX as a symlinked TMPDIR, so a bare
    ``relative_to`` raised ValueError AFTER a successful plan. Fall back to resolving both sides.
    """
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        return target.resolve().relative_to(root.resolve()).as_posix()


def _research_legacy_context(research_root: Path, *, repo_root: Optional[Path] = None):
    """Build a phase-B LegacyContext rooted at ``research_root.parent``."""
    from agent_workflows import artifact_meta as _meta

    resolved_repo = (
        Path(repo_root).resolve()
        if repo_root is not None
        else _core.repo_root_of(research_root).resolve()
    )
    base_ctx = _meta.legacy_context(resolved_repo)
    records_root = research_root.resolve().parent
    return type(
        "LegacyContext",
        (),
        {
            "logical_roots": {
                "records": str(records_root),
                "state": base_ctx.logical_roots["state"],
            },
            "repo_root": resolved_repo,
        },
    )()


def _research_root_for_file(target: Path, args: Optional[argparse.Namespace]) -> Path:
    if args is not None:
        return _research_root(args)
    resolved_parent = target.resolve().parent
    for cand in [resolved_parent] + list(resolved_parent.parents):
        if cand.name == "research":
            return cand
    return resolved_parent


def _render_research_create(
    *,
    research_root: Path,
    dest_path: Path,
    id6: str,
    created: str,
    set_id: str,
    order: int,
    topic: List[str],
    model: Optional[str],
    kind: str,
    summary: str,
    short_description: Optional[str] = None,
    priority: Optional[str] = None,
) -> str:
    """Render a new research document via ``artifact_meta.create(..., dry_run=True)``."""
    from agent_workflows import artifact_meta as _meta

    ctx = _research_legacy_context(research_root)
    records_root = Path(ctx.logical_roots["records"])
    rel_dest = dest_path.resolve().relative_to(records_root).as_posix()
    fields: dict = {
        "created": created,
        "set": set_id,
        "order": int(order),
        "topic": list(topic),
        "model": model,
        "research_kind": kind,
        "outcome": "none-yet",
        "summary": summary,
        "consumed_by": [],
    }
    if kind != "research-prompt":
        fields["status"] = "todo"
    if priority:
        fields["priority"] = priority
    if short_description and short_description.strip():
        fields["short_description"] = short_description
    preview = _meta.create(
        id6,
        "research",
        fields,
        "",
        destination=rel_dest,
        dry_run=True,
        project_context=ctx,
        legacy_render=_meta.LegacyRender(
            tag="created",
            day=_core.utc_history_date(),
            actor_label="aw research",
            history=False,
        ),
    )
    return preview.text


def _write_planned_research_file(
    planned: PlannedFile,
    *,
    research_root: Path,
    overwrite: bool,
) -> None:
    """Persist one planned research file through ``artifact_meta.create(..., dry_run=False)``."""
    from agent_workflows import artifact_meta as _meta

    ctx = _research_legacy_context(research_root)
    records_root = Path(ctx.logical_roots["records"])
    rel_dest = planned.path.resolve().relative_to(records_root).as_posix()
    fm = _meta.front_matter_mapping(planned.content)
    body = ""
    if fm is not None:
        lines = planned.content.splitlines(keepends=True)
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                body = "".join(lines[i + 1 :])
                break
    else:
        body = planned.content
    parsed_name, _ = R.parse_name(planned.path.name)
    id6 = (str(fm.get("id") or "") if fm is not None else "") or (
        parsed_name.id6 if parsed_name is not None else ""
    )
    fields: dict = {}
    if fm is not None:
        if "created" in fm:
            fields["created"] = fm["created"]
        if "set" in fm:
            fields["set"] = fm["set"]
        if "order" in fm:
            raw_order = fm["order"]
            fields["order"] = (
                int(raw_order)
                if isinstance(raw_order, str) and raw_order.isdigit()
                else raw_order
            )
        if "topic" in fm:
            fields["topic"] = fm["topic"]
        if "model" in fm:
            fields["model"] = fm["model"] or None
        if "kind" in fm:
            fields["research_kind"] = fm["kind"]
        if "status" in fm:
            fields["status"] = fm["status"]
        if "outcome" in fm:
            fields["outcome"] = fm["outcome"]
        if "summary" in fm:
            fields["summary"] = fm["summary"]
        if "consumed-by" in fm:
            fields["consumed_by"] = fm["consumed-by"]
        if fm.get("priority"):
            fields["priority"] = fm["priority"]
        if "short-description" in fm:
            fields["short_description"] = fm["short-description"]
        if "ace" in fm:
            fields["ace"] = fm["ace"]
    _meta.create(
        id6,
        "research",
        fields,
        body,
        destination=rel_dest,
        dry_run=False,
        overwrite=overwrite,
        project_context=ctx,
        legacy_render=_meta.LegacyRender(
            tag="created",
            day=_core.utc_history_date(),
            actor_label="aw research",
            history=False,
        ),
    )


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

    # E-03 (IPD iumgvk): Destination-containment assertion (defense-in-depth).
    # Placed above the no-clobber loop so BOTH the preview arm and the apply arm refuse.
    # Uses Path.relative_to with ValueError as the escape signal (same idiom as
    # check_engine.resolve_evidence_artifact and specs.run_new).
    # OQ-02: When args is None, the research root cannot be derived, so SKIP the
    # assertion rather than guessing. Every CLI path passes args and the planner-level
    # guard still applies.
    if args is not None:
        research_root = _research_root(args)
        resolved_root = research_root.resolve()
        for f in files:
            try:
                resolved_target = f.path.resolve()
                resolved_target.relative_to(resolved_root)
                if resolved_target == resolved_root:
                    raise ValueError(
                        "destination matches records root rather than a record inside it"
                    )
            except ValueError:
                msg = f"destination {f.path} escapes research tree {research_root}"
                if ctx and (ctx.is_agent or ctx.is_json):
                    res = CommandResult(
                        command=command_name,
                        status="cannot-run",
                        exit_code=2,
                        summary=msg,
                    )
                    return get_renderer(ctx).emit(res, ctx)
                print(f"error: {msg}")
                return 2

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
            r_root = _research_root_for_file(f.path, args)
            _write_planned_research_file(f, research_root=r_root, overwrite=overwrite)
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


def _resolved_research_id6(target: Path, requested_id: str) -> Optional[str]:
    parsed, _ = R.parse_name(target.name)
    if parsed is not None:
        return parsed.id6
    if R.is_valid_id6(requested_id):
        return requested_id
    return None


def _apply_research_meta_events(
    *,
    research_root: Path,
    repo_root: Path,
    target: Path,
    requested_id: str,
    events: List[dict],
    tag: str,
    dry_run: bool,
) -> str:
    """Preview or apply field events on a research record via ``artifact_meta.append``."""
    from agent_workflows import artifact_meta as _meta

    ctx = _research_legacy_context(research_root, repo_root=repo_root)
    target_id6 = _resolved_research_id6(target, requested_id)
    preview = _meta.append(
        _meta.LegacyTarget(target, "research", target_id6),
        events,
        dry_run=dry_run,
        project_context=ctx,
        legacy_render=_meta.LegacyRender(
            tag=tag,
            day=_core.utc_history_date(),
            actor_label="aw research",
            history=False,
        ),
    )
    return preview.text


def _outcome_update_fields(
    outcome: Optional[str],
    consumed_by: Optional[List[str]],
    clear_consumed: bool,
) -> dict:
    fields: dict = {}
    if outcome is not None:
        fields["outcome"] = outcome
    if clear_consumed:
        fields["consumed_by"] = []
    elif consumed_by is not None:
        fields["consumed_by"] = list(consumed_by)
    return fields


def plan_set_outcome(
    research_root: Path,
    id6: str,
    outcome: Optional[str],
    consumed_by: Optional[List[str]],
    clear_consumed: bool = False,
    *,
    repo_root: Optional[Path] = None,
) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    """Plan an outcome/consumed-by update for one doc; returns (path, new_text, error).

    ``outcome`` (when given) must be in the vocabulary. ``consumed_by`` REPLACES the list;
    ``clear_consumed`` (the ``-`` sentinel) empties it. Reads the doc, applies only the requested
    fields, and returns the new text without writing. Preserves all other fields and the body.
    """

    if outcome is not None and outcome not in R.OUTCOMES:
        return None, None, f"outcome must be one of {sorted(R.OUTCOMES)}"
    if consumed_by is not None:
        for c in consumed_by:
            c_err = _refuse_unsafe_descriptive(
                "aw research set-outcome", f"--consumed-by token '{c}'", c
            )
            if c_err:
                return None, None, c_err
    if repo_root is None:
        repo_root = _core.repo_root_of(research_root)
    from agent_workflows.research_archive import _resolve_one_research

    target, err = _resolve_one_research(
        repo_root, research_root, id6, verb="set-outcome"
    )
    if err:
        return None, None, err
    if target is None:
        return None, None, f"no research file has id6 '{id6}'"
    fields = _outcome_update_fields(outcome, consumed_by, clear_consumed)
    if not fields:
        return None, None, "nothing to set (provide --to and/or --consumed-by)"
    try:
        new_text = _apply_research_meta_events(
            research_root=research_root,
            repo_root=repo_root,
            target=target,
            requested_id=id6,
            events=[{"op": "set", "fields": fields}],
            tag="set-outcome",
            dry_run=True,
        )
    except ValueError as exc:
        return None, None, str(exc)
    return target, new_text, None


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
    repo_root = getattr(args, "dir", None)
    if repo_root is not None:
        repo_root = Path(repo_root)
    else:
        repo_root = _core.repo_root_of(root)
    outcome_val = getattr(args, "to", None)
    target, new_text, err = plan_set_outcome(
        root,
        id6,
        outcome_val,
        consumed_list,
        clear_consumed=clear,
        repo_root=repo_root,
    )
    if err or target is None or new_text is None:
        print(f"error: {err or 'could not plan update'}")
        return 2
    rel = _rel_posix(target, root)
    if not getattr(args, "apply", False):
        bits = []
        if outcome_val is not None:
            bits.append(f"outcome={outcome_val}")
        if clear:
            bits.append("consumed-by=[] (cleared)")
        elif consumed_list is not None:
            bits.append(f"consumed-by={_render_list(consumed_list)}")
        print(f"--- would update {rel}: {', '.join(bits)} ---")
        return 0
    fields = _outcome_update_fields(outcome_val, consumed_list, clear)
    try:
        _apply_research_meta_events(
            research_root=root,
            repo_root=repo_root,
            target=target,
            requested_id=id6,
            events=[{"op": "set", "fields": fields}],
            tag="set-outcome",
            dry_run=False,
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    print(f"updated {rel}")
    return 0


def _priority_events(to: Optional[str]) -> List[dict]:
    if to in (None, "-"):
        return [{"op": "unset", "fields": ["priority"]}]
    return [{"op": "set", "fields": {"priority": to}}]


def plan_set_priority(
    research_root: Path,
    id6: str,
    to: Optional[str],
    *,
    repo_root: Optional[Path] = None,
) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    """Plan a priority set/clear for one doc; returns (path, new_text, error). Mirrors
    ``plan_set_outcome``. ``to`` must be in the shared vocab (or '-'/None to clear)."""
    from agent_workflows import backlog
    from agent_workflows.research_archive import _resolve_one_research

    clearing = to in (None, "-")
    if not clearing and to not in backlog.PRIORITIES:
        return None, None, f"priority must be one of {sorted(backlog.PRIORITIES)}"
    if repo_root is None:
        repo_root = _core.repo_root_of(research_root)
    target, err = _resolve_one_research(
        repo_root, research_root, id6, verb="set-priority"
    )
    if err:
        return None, None, err
    if target is None:
        return None, None, f"no research file has id6 '{id6}'"
    try:
        new_text = _apply_research_meta_events(
            research_root=research_root,
            repo_root=repo_root,
            target=target,
            requested_id=id6,
            events=_priority_events(to),
            tag="set-priority",
            dry_run=True,
        )
    except ValueError as exc:
        return None, None, str(exc)
    return target, new_text, None


def run_set_priority(args: argparse.Namespace) -> int:
    """`aw research set-priority <id6> --to <low|medium|high|-> ` (preview/--apply); mirrors
    set-outcome's shape (xprio 6vgd0k)."""

    root = _research_root(args)
    id6 = (getattr(args, "id", "") or "").strip()
    if not id6:
        print("error: an <id6> is required")
        return 2
    to = getattr(args, "to", None)
    repo_root = getattr(args, "dir", None)
    if repo_root is not None:
        repo_root = Path(repo_root)
    else:
        repo_root = _core.repo_root_of(root)
    target, new_text, err = plan_set_priority(root, id6, to, repo_root=repo_root)
    if err or target is None or new_text is None:
        print(f"error: {err or 'could not plan update'}")
        return 2
    rel = _rel_posix(target, root)
    if not getattr(args, "apply", False):
        label = "priority=[] (cleared)" if to in (None, "-") else f"priority={to}"
        print(f"--- would update {rel}: {label} ---")
        return 0
    try:
        _apply_research_meta_events(
            research_root=root,
            repo_root=repo_root,
            target=target,
            requested_id=id6,
            events=_priority_events(to),
            tag="set-priority",
            dry_run=False,
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    print(f"updated {rel}")
    return 0


def _setid_length_guard(args: argparse.Namespace, setid):
    """Return ``(error, warning)`` from the ONE shared setid-length validator (setidlen `x75obw` E-06).

    The comparison lives in :func:`config.validate_setid_length_for_authoring` and is never re-spelled
    here; this only resolves the repo root the way this module's other verbs do.
    """
    from agent_workflows import config as _config
    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    return _config.validate_setid_length_for_authoring(
        repo_root, setid, verb="aw research new"
    )


def _emit_new_error(args: argparse.Namespace, message: str) -> int:
    """Report a `research new` refusal through this verb's EXISTING error shape (human + agent/JSON)."""
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import CommandResult, select_output

    ctx = select_output(args)
    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="research new",
            status="cannot-run",
            exit_code=2,
            summary=message,
        )
        return get_renderer(ctx).emit(res, ctx)
    print(f"error: {message}")
    return 2


def run_new(args: argparse.Namespace) -> int:
    root = _research_root(args)
    topic = [
        t.strip() for t in (getattr(args, "topic", None) or "").split(",") if t.strip()
    ]
    # setidlen x75obw E-06 (catalog I-17): the ONE shared setid-length guard. Reported through this
    # verb's OWN error channel (the `err` string below, which already renders in both the human and
    # the agent/JSON shapes) rather than a bare print, so a refusal is machine-readable here too.
    _setid_err, _setid_warn = _setid_length_guard(args, getattr(args, "set", None))
    if _setid_err:
        return _emit_new_error(args, _setid_err)
    if _setid_warn:
        print(f"note: {_setid_warn}")
    summary_val = getattr(args, "summary", "") or ""
    files, err = plan_new(
        research_root=root,
        kind=getattr(args, "kind", ""),
        slug=getattr(args, "slug", "") or "",
        summary=summary_val,
        short_description=summary_val,
        set_id=getattr(args, "set", None),
        model=getattr(args, "model", None),
        topic=topic,
        date_str=getattr(args, "date", None),
        priority=getattr(args, "priority", None),
        order=getattr(args, "order", None),
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
