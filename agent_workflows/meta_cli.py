"""Read, drift-check, and repair commands served through `artifact_meta` (spec `4sd62s` 4.3, 4.5-4.8).

Five operator surfaces live here, each answered through the public `artifact_meta` interface:

- `aw show <ref> --history`: the event history of every artifact the selector names.
- `aw show <ref> --format json`: the replayed state of every artifact the selector names.
- `aw index rebuild`: delete and rebuild the SQLite cache from the tracked sources.
- `aw check meta`: check every 4.6 metadata mirror and drift rule against cached state.
- `aw meta repair <id6>`: preview and apply mirror, move, journal, and diverged-tail repairs.

This module holds no metadata parser of its own. All record and mirror parsing goes through
`artifact_meta`, `artifact_naming`, `research_contract`, and `record_placement`.

Display safety: every string taken from an imported legacy history line, or from a log event's
`message`, passes through `attention_contract.neutralize_control_characters` before it is returned
(4.2, SR-903), so a terminal never receives raw control or bidi characters from record text.
"""

from __future__ import annotations

import contextlib
import dataclasses
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from agent_workflows import artifact_meta as _meta
from agent_workflows import attention_contract as _att
from agent_workflows.result_types import (
    Change,
    CommandResult,
    Diagnostic,
    Evidence,
    NextAction,
)

__all__ = [
    "MetaContext",
    "meta_context",
    "resolve_selector",
    "show_history",
    "show_json",
    "index_rebuild",
    "index_alias",
    "render_history_human",
    "check_meta",
    "render_check_meta_human",
    "render_check_meta_agent",
    "meta_repair",
    "render_meta_repair_human",
]


@dataclasses.dataclass
class MetaContext:
    """The two roots `artifact_meta` reads: the records tree and the (gitignored) state root."""

    logical_roots: Dict[str, str]
    repo_root: Path

    @property
    def records_root(self) -> Path:
        return Path(self.logical_roots["records"])

    @property
    def state_root(self) -> Path:
        return Path(self.logical_roots["state"])


def meta_context(repo_root: Path) -> MetaContext:
    """Build the `artifact_meta` project context for ``repo_root``.

    The records root is the one every other record verb reads (`project_context.project_records_dir`,
    which honors a stored records placement and otherwise uses `<repo>/.aw/records`), so `aw show`
    and `aw index rebuild` look at the same tree `aw find` does. The state root comes from the full
    project-context resolver, falling back to `<repo>/.aw/state` if that resolver refuses.
    """
    from agent_workflows import project_context as _pc

    root = Path(repo_root).resolve()
    records = Path(_pc.project_records_dir(root))
    state: Optional[Path] = None
    with contextlib.suppress(Exception):
        state = Path(
            _pc.resolve_project_context(target_repo=str(root)).logical_roots["state"]
        )
    if state is None:
        state = root / ".aw" / "state"
    return MetaContext(
        logical_roots={"records": str(records), "state": str(state)}, repo_root=root
    )


# --------------------------------------------------------------------------------------------------
# Selector resolution
# --------------------------------------------------------------------------------------------------


def resolve_selector(ctx: MetaContext, ref: str) -> List[str]:
    """Return the id6 of every artifact ``ref`` names, in a stable order.

    ``ref`` may be an id6, a path (repo-relative, records-relative, or absolute), a filename or
    filename fragment, a Set id, or a status; a selector that matches several records returns
    every match. Resolution goes through `artifact_meta.resolve` for id6 and path forms and through
    `artifact_meta.query` for the multi-record forms. An id6 whose record is INVALID is still
    returned, so the caller can report its defect instead of pretending it does not exist.
    """
    from agent_workflows import artifact_core as _core

    tok = str(ref).strip()
    if not tok:
        return []
    if _core.ID6_RE.fullmatch(tok):
        return [tok] if _meta.resolve(tok, project_context=ctx) else []

    # Path forms: normalize to a records-root-relative path (or `@repo/...` for extra roots),
    # then ask `resolve`.
    candidates: List[str] = []
    p = Path(tok)
    with contextlib.suppress(Exception):
        if p.is_absolute():
            resolved_p = p.resolve()
            try:
                candidates.append(
                    resolved_p.relative_to(ctx.records_root.resolve()).as_posix()
                )
            except ValueError:
                candidates.append(
                    "@repo/"
                    + resolved_p.relative_to(ctx.repo_root.resolve()).as_posix()
                )
    clean = tok.replace("\\", "/")
    clean_rel = clean[2:] if clean.startswith("./") else clean
    candidates.append(clean)
    if clean_rel != clean:
        candidates.append(clean_rel)
    for prefix in (".aw/records/", "records/"):
        if clean_rel.startswith(prefix):
            candidates.append(clean_rel[len(prefix) :])
    if clean_rel and not clean_rel.startswith("@repo/"):
        candidates.append(f"@repo/{clean_rel}")
    for cand in candidates:
        hit = _meta.resolve(cand, project_context=ctx)
        if hit:
            return _ids_for_paths(ctx, [hit])

    rows = _meta.query(project_context=ctx)
    by_set = [s.id6 for s in rows if s.set_id == tok]
    if by_set:
        return by_set
    low = tok.lower()
    by_status = [s.id6 for s in rows if (s.status or "").lower() == low]
    if by_status:
        return by_status
    return [s.id6 for s in rows if s.path and tok in Path(s.path).name]


def _ids_for_paths(ctx: MetaContext, paths: Sequence[str]) -> List[str]:
    wanted = set(paths)
    return [
        s.id6 for s in _meta.query(project_context=ctx) if s.path in wanted
    ] or _invalid_ids_for_paths(ctx, wanted)


def _invalid_ids_for_paths(ctx: MetaContext, wanted: set) -> List[str]:
    # `query` lists valid records only; an invalid record is found through `resolve` by id6, so
    # recover its id6 from the filename grammar when the path names one.
    from agent_workflows import artifact_naming as _naming

    out: List[str] = []
    for pth in sorted(wanted):
        name = Path(pth).name
        m_attr = _naming.parse_attributed(name)
        if m_attr and m_attr.id6:
            out.append(m_attr.id6)
            continue
        m_cl = _naming.parse_clustered(name)
        if m_cl:
            out.append(m_cl.group("id6"))
    return out


# --------------------------------------------------------------------------------------------------
# Event normalization
# --------------------------------------------------------------------------------------------------


def _safe(value: Any) -> Any:
    if isinstance(value, str):
        return _att.neutralize_control_characters(value)
    return value


def normalize_event(raw: Dict[str, Any], position: int) -> Dict[str, Any]:
    """Map one `artifact_meta.history` row onto the displayed event shape.

    A log event keeps its `seq`, `at`, `op`, `from`/`to`, actor and message. A legacy history line
    (phase B) has no `seq` order and no inferred transition: it becomes `op: legacy` with its file
    position as `seq`, its `observed_day`, and the line itself as `message`. A legacy review round
    becomes `op: review` of its subject (4.1a).
    """
    ev: Dict[str, Any] = {}
    if "line" in raw and "op" not in raw:
        ev["seq"] = raw.get("seq", position)
        ev["observed_day"] = raw.get("observed_day")
        ev["op"] = "legacy"
        ev["source"] = "history"
        ev["message"] = _safe(raw.get("line", ""))
        return ev

    ev["seq"] = raw.get("seq", position)
    if raw.get("at"):
        ev["at"] = raw["at"]
    elif raw.get("observed_day"):
        ev["observed_day"] = raw["observed_day"]
    ev["op"] = raw.get("op")
    for key in (
        "from",
        "to",
        "path",
        "review_kind",
        "round",
        "verdict",
        "legacy_verdict",
        "readiness",
        "reviewer",
        "source",
        "verb",
    ):
        if raw.get(key) is not None:
            ev[key] = _safe(raw[key])
    actor = raw.get("actor")
    actor_out: Dict[str, Any] = {}
    if isinstance(actor, dict):
        for key in ("tool", "model"):
            if actor.get(key):
                actor_out[key] = _safe(actor[key])
    elif raw.get("actor_id"):
        actor_out["id"] = _safe(raw["actor_id"])
    if raw.get("by_human"):
        actor_out["by_human"] = True
    if actor_out:
        ev["actor"] = actor_out
    if raw.get("fields") and ev["op"] in ("create", "set", "checkpoint"):
        ev["fields"] = {k: _safe(v) for k, v in raw["fields"].items()}
    if raw.get("unset"):
        ev["unset"] = raw["unset"]
    if raw.get("message"):
        ev["message"] = _safe(raw["message"])
    elif raw.get("line"):
        ev["message"] = _safe(raw["line"])
    return ev


def _state_dict(st: Any) -> Dict[str, Any]:
    return {
        "id6": st.id6,
        "type": st.type,
        "status": st.status,
        "path": st.path,
        "disposition": st.disposition,
        "title": _safe(st.title),
        "set": st.set_id,
        "order": st.order_nn,
        "short_description": _safe(st.short_description),
        "last_seq": st.last_seq,
        "valid": bool(st.valid),
        "defect": st.defect,
        "fields": {k: _safe(v) for k, v in (st.fields or {}).items()},
    }


# --------------------------------------------------------------------------------------------------
# aw show --history / --format json
# --------------------------------------------------------------------------------------------------


def _collect(
    repo_root: Path, ref: str, *, with_history: bool, with_state: bool
) -> Tuple[List[Dict[str, Any]], List[Diagnostic]]:
    ctx = meta_context(repo_root)
    records: List[Dict[str, Any]] = []
    defects: List[Diagnostic] = []
    for id6 in resolve_selector(ctx, ref):
        entry: Dict[str, Any] = {"id6": id6}
        try:
            st = _meta.read(id6, project_context=ctx)
            if with_state:
                entry.update(_state_dict(st))
            else:
                entry["path"] = st.path
                entry["status"] = st.status
            if with_history:
                rows = _meta.history(id6, project_context=ctx)
                entry["history"] = [
                    normalize_event(r, i) for i, r in enumerate(rows, start=1)
                ]
        except ValueError as exc:
            detail = _safe(str(exc))
            path = _meta.resolve(id6, project_context=ctx) or id6
            defects.append(
                Diagnostic(
                    location=f"{path}",
                    rule="invalid-record",
                    detail=detail,
                    severity="error",
                )
            )
            entry["valid"] = False
            entry["defect"] = detail
            entry["path"] = path
        records.append(entry)
    return records, defects


def _result(
    command: str,
    ref: str,
    records: List[Dict[str, Any]],
    defects: List[Diagnostic],
    *,
    what: str,
) -> CommandResult:
    if defects:
        return CommandResult(
            command=command,
            status="error",
            exit_code=2,
            summary=(
                f"{len(defects)} invalid record(s) for '{ref}'; "
                "fix the metadata, then rerun (no stale state is shown)"
            ),
            diagnostics=defects,
            verified=False,
            complete=False,
            data={"selector": ref, "records": records},
            next_actions=[NextAction(command="aw index rebuild")],
        )
    evidence = [Evidence(key="show-match", value=len(records), status="verified")]
    for rec in records:
        # A compact agent record carries no free-form data, so each record's id6, status and
        # event count travel as evidence items (`<id6>-status:<status>`, `<id6>-events:<n>`).
        if rec.get("status"):
            evidence.append(
                Evidence(
                    key=f"{rec['id6']}-status",
                    value=str(rec["status"]),
                    status="verified",
                )
            )
        if "history" in rec:
            evidence.append(
                Evidence(
                    key=f"{rec['id6']}-events",
                    value=len(rec["history"]),
                    status="verified",
                )
            )
    return CommandResult(
        command=command,
        status="clean",
        exit_code=0,
        summary=f"{what} for {len(records)} artifact(s) matching '{ref}'",
        evidence=evidence,
        data={"selector": ref, "records": records},
    )


def show_history(repo_root: Path, ref: str) -> CommandResult:
    """The event history of every artifact ``ref`` names, in `seq` order (4.8)."""
    records, defects = _collect(repo_root, ref, with_history=True, with_state=False)
    return _result("show", ref, records, defects, what="history")


def show_json(repo_root: Path, ref: str, *, history: bool = False) -> CommandResult:
    """The replayed state of every artifact ``ref`` names, plus its history when asked (4.8)."""
    records, defects = _collect(repo_root, ref, with_history=history, with_state=True)
    return _result("show", ref, records, defects, what="state")


def _fmt_event_row(ev: Dict[str, Any]) -> str:
    when = ev.get("at") or ev.get("observed_day") or "-"
    op = str(ev.get("op") or "-")
    change = ""
    if ev.get("from") or ev.get("to"):
        change = f"{ev.get('from') or '-'} -> {ev.get('to') or '-'}"
    elif op == "review":
        change = " ".join(
            str(x)
            for x in (
                ev.get("review_kind"),
                f"round {ev['round']}" if ev.get("round") is not None else None,
                ev.get("verdict") or ev.get("legacy_verdict"),
            )
            if x
        )
    elif ev.get("fields"):
        change = ", ".join(f"{k}={v}" for k, v in sorted(ev["fields"].items()))
    actor = ev.get("actor") or {}
    who = " ".join(
        str(x)
        for x in (
            actor.get("tool"),
            actor.get("model"),
            "by-human" if actor.get("by_human") else None,
        )
        if x
    )
    msg = ev.get("message") or ""
    parts = [f"{ev.get('seq', '-'):>4}", f"{when:<25}", f"{op:<10}"]
    tail = "  ".join(x for x in (change, who, msg) if x)
    return "  ".join(parts) + ("  " + tail if tail else "")


def render_history_human(result: CommandResult) -> str:
    """Render a `show_history` result as one table per artifact, one row per event."""
    lines: List[str] = []
    for rec in result.data.get("records", []):
        lines.append(
            f"== {rec.get('path') or rec['id6']} ({rec['id6']}, status {rec.get('status') or '-'})"
        )
        if rec.get("defect"):
            lines.append(f"   invalid record: {rec['defect']}")
            continue
        events = rec.get("history", [])
        if not events:
            lines.append("   (no history recorded)")
            continue
        lines.append(f"{'seq':>4}  {'at':<25}  {'op':<10}  detail")
        lines.extend(_fmt_event_row(ev) for ev in events)
    if not result.data.get("records"):
        lines.append(f"no artifact history for '{result.data.get('selector')}'")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------------------------------
# aw index rebuild and the typed-spelling refresh
# --------------------------------------------------------------------------------------------------


def _cache_paths(state_root: Path) -> List[Path]:
    db = state_root / "index.db"
    return [
        db,
        Path(str(db) + "-wal"),
        Path(str(db) + "-shm"),
        Path(str(db) + "-journal"),
    ]


def _has_any_record_root(ctx: MetaContext) -> bool:
    """Return True when the records root or any extra `selectors.record_dirs` root exists."""
    if ctx.records_root.is_dir():
        return True
    from agent_workflows import selectors as _sel

    rec_resolved = ctx.records_root.resolve()
    for rtype in (
        "plans",
        "specs",
        "prompts",
        "backlog",
        "releases",
        "research",
        "walkthroughs",
        "roadmaps",
        "other",
    ):
        for d in _sel.record_dirs(ctx.repo_root, rtype):
            try:
                d_res = d.resolve()
            except OSError:
                continue
            if (
                d_res != rec_resolved
                and not d_res.is_relative_to(rec_resolved)
                and d.is_dir()
            ):
                return True
    return False


def index_rebuild(repo_root: Path) -> CommandResult:
    """Delete the cache and rebuild it from empty through `artifact_meta` (4.5).

    Writes no tracked file: the cache lives under the gitignored state root. Reports the counts of
    artifacts, walkthroughs, review files, events, and valid and invalid records. An invalid record
    is a FINDING (exit 1) naming the record, because the rebuild itself succeeded.
    """
    ctx = meta_context(repo_root)
    if not _has_any_record_root(ctx):
        return CommandResult(
            command="index rebuild",
            status="cannot-run",
            exit_code=2,
            summary="no records directory to index; this is not an aw project (run `aw install .`)",
            diagnostics=[
                Diagnostic(
                    location=".aw/records",
                    rule="records-dir-missing",
                    detail="the records directory does not exist",
                    severity="error",
                )
            ],
            verified=False,
            complete=False,
            next_actions=[NextAction(command="aw install .")],
        )
    for p in _cache_paths(ctx.state_root):
        with contextlib.suppress(FileNotFoundError):
            if p.is_dir():
                import shutil

                shutil.rmtree(p)
            else:
                p.unlink()
    try:
        conn = _meta.open_cache(ctx.records_root, ctx.state_root)
    except Exception as exc:  # cannot-run: the cache could not be created at all
        return CommandResult(
            command="index rebuild",
            status="cannot-run",
            exit_code=2,
            summary=f"cannot rebuild the metadata cache: {exc}",
            verified=False,
            complete=False,
        )
    try:
        _meta.check_freshness(
            conn, ctx.records_root, force=True, repo_root=ctx.repo_root
        )

        def one(sql: str) -> int:
            row = conn.execute(sql).fetchone()
            return int(row[0] or 0) if row else 0

        counts = {
            "artifacts": one(
                "SELECT COUNT(*) FROM artifacts WHERE type != 'walkthrough'"
            ),
            "walkthroughs": one(
                "SELECT COUNT(*) FROM artifacts WHERE type = 'walkthrough'"
            ),
            "review_files": one("SELECT COUNT(*) FROM review_files"),
            "events": one("SELECT COUNT(*) FROM events"),
            "valid": one(
                "SELECT COUNT(*) FROM artifacts WHERE valid = 1 AND defect IS NULL"
            ),
            "invalid": one(
                "SELECT COUNT(*) FROM artifacts WHERE valid = 0 OR defect IS NOT NULL"
            ),
        }
        invalid_rows = conn.execute(
            "SELECT id6, path, defect FROM artifacts WHERE valid = 0 OR defect IS NOT NULL "
            "ORDER BY path"
        ).fetchall()
        in_memory = not (ctx.state_root / "index.db").is_file()
    finally:
        conn.close()

    try:
        cache_rel = (ctx.state_root / "index.db").relative_to(ctx.repo_root).as_posix()
    except ValueError:
        cache_rel = (ctx.state_root / "index.db").as_posix()
    diags = [
        Diagnostic(
            location=str(r[1] or r[0]),
            rule="invalid-record",
            detail=_safe(f"{r[0]}: {r[2]}"),
            severity="error",
        )
        for r in invalid_rows
    ]
    data = {**counts, "cache": cache_rel, "in_memory_fallback": in_memory}
    evidence = [Evidence(key=k, value=v, status="verified") for k, v in counts.items()]
    summary = (
        f"rebuilt {cache_rel}: {counts['artifacts']} artifacts, {counts['walkthroughs']} "
        f"walkthroughs, {counts['review_files']} review files, {counts['events']} events; "
        f"valid: {counts['valid']}, invalid: {counts['invalid']}"
    )
    if diags:
        return CommandResult(
            command="index rebuild",
            status="findings",
            exit_code=1,
            summary=summary,
            diagnostics=diags,
            evidence=evidence,
            data=data,
            next_actions=[NextAction(command="aw show <id6> --history")],
        )
    return CommandResult(
        command="index rebuild",
        status="ok",
        exit_code=0,
        summary=summary,
        evidence=evidence,
        data=data,
    )


# --------------------------------------------------------------------------------------------------
# aw index plans|research|prompts|all and aw research index (spec 4sd62s 4.5, IPD tqknnc)
# --------------------------------------------------------------------------------------------------

_STALE_INDEX_RULE_PREFIX = "check.stale-index-"

# The clean lines the per-type `run_index --check` printed, kept byte-identical for scripts.
_INDEX_ALIAS_CLEAN: Dict[str, str] = {
    "plans": "plans index --check: clean",
    "research": "index --check: clean",
    "prompts": "prompts index --check: clean",
    "all": "all index --check: clean",
}


def _index_alias_drift(args: Any, artifact_type: str) -> List[Any]:
    """The surviving (non-INDEX) drift classes the typed `--check` gated before (`q6epwc` OQ-01).

    Each type's directory is resolved by the same resolver its `run_index` used, so `--check` reads
    the tree it always read and reports what `aw check <type> --all` reports from `check_drift`,
    minus the INDEX drift classes (`check.stale-index-*`): no command writes an INDEX file any more,
    so a missing or stale one is not drift `aw index <type>` can repair (OQ-01: "the non-INDEX
    drift classes"). The rules themselves are deleted by Orders 224 and 229.
    """
    from agent_workflows import check_engine as _ce
    from agent_workflows import plans_index as _pidx
    from agent_workflows import prompts_index as _pridx
    from agent_workflows import research_index as _ridx

    if artifact_type == "plans":
        repo_root, root = _pidx._dirs(args)
        found = _pidx.check_drift(repo_root, root)
    elif artifact_type == "research":
        repo_root, root = _ridx._roots(args)
        found = _ridx.check_drift(repo_root, root)
    elif artifact_type == "prompts":
        repo_root, root = _pridx._dirs(args)
        found = _pridx.check_drift(repo_root, root)
    else:
        return []
    return [
        _ce.enrich_drift(d)
        for d in found
        if not str(d.rule).startswith(_STALE_INDEX_RULE_PREFIX)
    ]


def _index_alias_check(
    args: Any, repo_root: Path, artifact_type: str, spelling: str
) -> CommandResult:
    from agent_workflows import agent_schema as _schema
    from agent_workflows import artifact_core as _core

    # `aw index all --check` reports in the order and shape the per-type loop it replaced used:
    # plans, prompts, research, one human block each, and a `by_type` summary.
    types = (
        ("plans", "prompts", "research") if artifact_type == "all" else (artifact_type,)
    )
    drift: List[Any] = []
    human = ""
    by_type: Dict[str, Dict[str, Any]] = {}
    for t in types:
        found = _index_alias_drift(args, t)
        rc_t = _core.drift_exit_code(found)
        by_type[t] = {
            "status": "conforms" if rc_t == 0 else "findings",
            "exit_code": rc_t,
            "findings": len(found),
        }
        if found:
            human += "".join(f"{d.location}: {d.rule}: {d.detail}\n" for d in found)
        else:
            human += _INDEX_ALIAS_CLEAN.get(t, f"{spelling} --check: clean") + "\n"
        drift.extend(found)
    exit_code = _core.drift_exit_code(drift)
    clean = _INDEX_ALIAS_CLEAN.get(artifact_type, f"{spelling} --check: clean")
    summary = (
        clean
        if not drift
        else f"{len(drift)} finding(s) detected across {artifact_type}"
    )
    data: Dict[str, Any] = {"target": artifact_type, "human_rendered": human}
    if artifact_type == "all":
        data["by_type"] = by_type
    return CommandResult(
        command="index",
        target=artifact_type,
        status="conforms" if exit_code == 0 else "findings",
        exit_code=exit_code,
        summary=summary,
        diagnostics=[
            Diagnostic(
                location=_schema.normalize_repo_path(d.location, repo_root),
                rule=d.rule,
                detail=d.detail,
                severity=d.severity or "error",
                fix=d.recovery or None,
            )
            for d in drift
        ],
        data=data,
        repo_root=repo_root,
        verified=True,
        complete=True,
    )


def index_alias(
    args: Any,
    *,
    artifact_type: Optional[str] = None,
    spelling: Optional[str] = None,
) -> int:
    """Serve `aw index plans|research|prompts|all` and `aw research index` as aliases (4.5).

    Without `--check` this runs `aw index rebuild` and exits as it does. `--limit` is accepted and
    ignored. With `--check` it runs the surviving content drift rules of the type and exits as
    `aw check <type> --all` would on them (`q6epwc` OQ-01); it does not touch the cache. Either way
    one information line names the alias: an `info` diagnostic under `--agent`/`--json`, a stderr
    line for a human. Writes no tracked file and no INDEX file.
    """
    from agent_workflows.project_context import resolve_verb_repo_root
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import select_output

    t = artifact_type or getattr(args, "resolved_type", None) or "all"
    said = spelling or f"aw index {t}"
    notice = f"`{said}` is an alias of `aw index rebuild`; INDEX files are no longer generated"
    ctx = select_output(args)
    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    if getattr(args, "check", False):
        result = _index_alias_check(args, repo_root, t, said)
    else:
        result = index_rebuild(repo_root)
    if ctx.is_human:
        with contextlib.suppress(BrokenPipeError, OSError):
            ctx.stderr.write(notice + "\n")
            ctx.stderr.flush()
    else:
        result.data.pop("human_rendered", None)
        result.diagnostics.insert(
            0,
            Diagnostic(
                location=said,
                rule="index-alias",
                detail=notice,
                severity="info",
            ),
        )
    return get_renderer(ctx).emit(result, ctx)


# --------------------------------------------------------------------------------------------------
# aw check meta (spec 4sd62s 4.6)
# --------------------------------------------------------------------------------------------------

_ROUND_HEADING_RE = re.compile(r"^## Round (\d+)", re.MULTILINE)
_ISO_DAY_RE = re.compile(r"\A(\d{4})-(\d{2})-(\d{2})\Z")
_COMPACT_DAY_RE = re.compile(r"\A(\d{4})(\d{2})(\d{2})\Z")

_TRACKED_RECORD_TOP_DIRS = frozenset(
    (
        "plans",
        "specs",
        "prompts",
        "backlog",
        "research",
        "releases",
        "walkthroughs",
        "roadmaps",
    )
)

_TYPE_TO_PLURAL: Dict[str, str] = {
    "ipd": "plans",
    "prompt": "prompts",
    "spec": "specs",
    "backlog": "backlog",
}


def _display_location(path: Path, ctx: MetaContext, fallback: str) -> str:
    """Return a repo-relative POSIX path when ``path`` sits under ``ctx.repo_root``."""
    try:
        return path.resolve().relative_to(ctx.repo_root.resolve()).as_posix()
    except (ValueError, OSError):
        return fallback


def _extract_record_parts(rel_path: str) -> Tuple[str, Tuple[str, ...]]:
    """Return ``(top_dir, parts_from_top_dir)`` for a records-relative or ``@repo/`` path."""
    norm = str(rel_path).replace("\\", "/")
    if norm.startswith("@repo/"):
        norm = norm[len("@repo/") :]
    for prefix in (".aw/records/", ".agents/docs/", ".agents/"):
        if norm.startswith(prefix):
            norm = norm[len(prefix) :]
            break
    parts = tuple(p for p in norm.split("/") if p)
    return (parts[0] if parts else ""), parts


def _normalize_iso_day(value: Any) -> Optional[str]:
    """Normalize ``YYYYMMDD`` or ``YYYY-MM-DD`` to ``YYYY-MM-DD``; return None otherwise."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    m_iso = _ISO_DAY_RE.match(s)
    if m_iso:
        return s
    m_cmp = _COMPACT_DAY_RE.match(s)
    if m_cmp:
        return f"{m_cmp.group(1)}-{m_cmp.group(2)}-{m_cmp.group(3)}"
    return None


def _norm_opt_str(value: Any) -> Optional[str]:
    """Normalize an optional metadata scalar string, treating blank/null/none as None."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in ("none", "null", "n/a"):
        return None
    return s


def _is_log_format_repo(repo_root: Path) -> bool:
    """True when ``repo_root`` declares metadata_schema >= 2 (post-cutover log format)."""
    from agent_workflows.migrations import chain as _chain

    with contextlib.suppress(Exception):
        ver = _chain.read_metadata_schema(repo_root)
        return ver is not None and ver >= 2
    return False


def _parse_log_backed_mirror(
    text: str, art_type: str
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Parse a log-backed record's in-file mirror through `artifact_meta`.

    Returns ``(in_file_id, in_file_status, parse_error)``. If the strict mirror parser fails,
    `artifact_meta.read_text` supplies whatever key is still readable so a broken status line
    does not falsely report id drift (and vice versa).
    """
    try:
        if art_type == "prompt":
            m = _meta.parse_staged_prompt_mirror(text)
        elif art_type in ("walkthrough", "roadmap"):
            m = _meta.parse_walkthrough_mirror(text)
        else:
            m = _meta.parse_artifact_mirror(
                text, allow_statusless=(art_type == "research")
            )
        return m.get("id"), m.get("status"), None
    except ValueError as exc:
        fb = _meta.read_text(text, record_type=art_type)
        return (fb.id6 or None), fb.status, str(exc)


def _check_disposition_drift(
    st: Any, top_dir: str, rel_parts: Tuple[str, ...]
) -> Optional[str]:
    """Compare a record's directory disposition against its status; return detail or None."""
    from agent_workflows import plans as _plans
    from agent_workflows import record_placement as _rp
    from agent_workflows import research_contract as _rc

    if st.type in _TYPE_TO_PLURAL:
        plural = _TYPE_TO_PLURAL[st.type]
        eff_status = st.status
        if eff_status is None and st.type == "ipd" and st.legacy_raw_status:
            first_tok = st.legacy_raw_status.strip().split()[0]
            eff_status = _plans.normalize_status(first_tok)
        if not eff_status:
            return None
        expected = _rp.target_subdir(plural, eff_status)
        if not expected:
            return None
        actual = rel_parts[1] if len(rel_parts) >= 3 else ""
        if actual != expected:
            return (
                f"disposition directory {actual or '<root>'!r} disagrees with "
                f"status {eff_status!r} (expected {expected!r})"
            )
        return None

    if st.type == "research" and st.status:
        eff_status = _rc.STATUS_NORMALIZATIONS.get(st.status, st.status)
        subdir = rel_parts[1] if len(rel_parts) >= 3 else ""
        if eff_status in _rc.HOT_STATUSES and subdir in ("reference", "archive"):
            return (
                f"research status {eff_status!r} expects hot root under research/, "
                f"found under research/{subdir}/"
            )
        if eff_status in _rc.SHARDED_STATUSES and subdir != eff_status:
            return (
                f"research status {eff_status!r} expects research/{eff_status}/, "
                f"found {subdir or '<root>'!r}"
            )
    return None


def _check_research_facets(st: Any, fname: str, repo_root: Path) -> Optional[str]:
    """Compare research filename facets (order, model, kind) against cached metadata."""
    from agent_workflows import artifact_naming as _naming
    from agent_workflows import research_contract as _rc

    if _naming.parse_legacy_timestamp(fname):
        return None

    rname, rerr = _rc.parse_name(fname, repo_root=repo_root)
    if rname is None:
        if _naming.parse_attributed(fname) is not None:
            return (
                f"research filename facets invalid: {rerr.message if rerr else fname}"
            )
        return None

    mismatches: List[str] = []

    # order
    fname_ord = int(rname.order)
    f_ord = st.fields.get("order")
    exp_ord: Optional[int] = None
    if f_ord is not None and str(f_ord).strip() != "":
        with contextlib.suppress(ValueError, TypeError):
            exp_ord = int(f_ord)
    elif st.order_nn is not None:
        exp_ord = st.order_nn
    if exp_ord is not None and fname_ord != exp_ord:
        mismatches.append(f"order filename={fname_ord:02d} cached={exp_ord:02d}")

    # model
    raw_mod = _norm_opt_str(st.fields.get("model"))
    exp_mod: Optional[str] = None
    if raw_mod is not None:
        mres = _rc.normalize_model(raw_mod, repo_root=repo_root)
        exp_mod = mres.value if mres.ok else raw_mod.lower()
    if rname.model != exp_mod:
        mismatches.append(f"model filename={rname.model!r} cached={exp_mod!r}")

    # kind
    raw_kind = _norm_opt_str(st.fields.get("research_kind"))
    exp_kind: Optional[str] = None
    if raw_kind is not None:
        kres = _rc.normalize_kind(raw_kind)
        exp_kind = kres.value if kres.ok else raw_kind.lower()
    if exp_kind is not None and rname.kind != exp_kind:
        mismatches.append(f"kind filename={rname.kind!r} cached={exp_kind!r}")

    if mismatches:
        return "research filename facet drift: " + "; ".join(mismatches)
    return None


def check_meta(repo_root: Path) -> CommandResult:
    """Run all spec `4sd62s` 4.6 metadata mirror and drift checks over `artifact_meta.query`.

    In phase B (legacy format), rows that require event logs (`logged-path` and `orphan-record`)
    are reported explicitly as `not-applicable (legacy format)` instead of being skipped silently.
    Exit codes: 0 clean, 1 findings, 2 cannot-run.
    """
    from agent_workflows import artifact_naming as _naming
    from agent_workflows import layout as _layout

    ctx = meta_context(repo_root)
    if not _has_any_record_root(ctx):
        return CommandResult(
            command="check meta",
            status="cannot-run",
            exit_code=2,
            summary="no records directory to check; this is not an aw project (run `aw install .`)",
            diagnostics=[
                Diagnostic(
                    location=".aw/records",
                    rule="records-dir-missing",
                    detail="the records directory does not exist",
                    severity="error",
                )
            ],
            verified=False,
            complete=False,
            next_actions=[NextAction(command="aw install .")],
            repo_root=ctx.repo_root,
        )

    try:
        rows = _meta.query(project_context=ctx, include_fields=True)
    except Exception as exc:
        return CommandResult(
            command="check meta",
            status="cannot-run",
            exit_code=2,
            summary=f"cannot query metadata cache: {_safe(str(exc))}",
            verified=False,
            complete=False,
            next_actions=[NextAction(command="aw index rebuild")],
            repo_root=ctx.repo_root,
        )

    log_format_repo = _is_log_format_repo(ctx.repo_root)
    not_applicable: List[Dict[str, str]] = []
    if not log_format_repo:
        not_applicable = [
            {"row": "logged-path", "status": "not-applicable (legacy format)"},
            {"row": "orphan-record", "status": "not-applicable (legacy format)"},
        ]

    skip_names = set(_layout.RECORD_SCAN_SKIP_NAMES)
    kept: List[Any] = []
    for st in rows:
        if not st.path:
            continue
        fname = Path(st.path).name
        if fname in skip_names:
            continue
        top_dir, _ = _extract_record_parts(st.path)
        if top_dir not in _TRACKED_RECORD_TOP_DIRS:
            continue
        kept.append(st)

    # Read cached review_files, reviews, events (op='review'), files, and artifact_paths
    # from the already-fresh SQLite cache in one pass.
    review_files_rows: List[Tuple[str, str, Optional[str], int, int]] = []
    legacy_review_rounds: Dict[Tuple[str, Optional[str]], List[int]] = {}
    logged_review_rounds: Dict[Tuple[str, Optional[str]], List[int]] = {}
    md_file_ids: Set[str] = set()
    load_error_files: List[Tuple[str, str, Optional[str], str]] = []
    latest_logged_path: Dict[str, str] = {}

    conn = _meta.open_cache(ctx.records_root, ctx.state_root)
    try:
        review_files_rows = conn.execute(
            "SELECT path, subject_id6, review_ref, round_count, parse_ok "
            "FROM review_files ORDER BY path"
        ).fetchall()
        for sid, rref, rnd in conn.execute(
            "SELECT subject_id6, review_ref, round FROM reviews ORDER BY subject_id6, seq"
        ).fetchall():
            if rnd is not None:
                legacy_review_rounds.setdefault((sid, rref), []).append(int(rnd))
        for sid, raw_ev in conn.execute(
            "SELECT id6, raw FROM events WHERE op = 'review' ORDER BY id6, seq"
        ).fetchall():
            if raw_ev:
                with contextlib.suppress(Exception):
                    ev = json.loads(raw_ev)
                    if ev.get("round") is not None:
                        logged_review_rounds.setdefault(
                            (sid, ev.get("review_ref")), []
                        ).append(int(ev["round"]))
        for fpath, frole, fid6, ferr in conn.execute(
            "SELECT path, file_role, id6, load_error FROM files"
        ).fetchall():
            if frole in ("artifact", "walkthrough") and fid6:
                abs_f = _meta.source_path(fpath, ctx.records_root, ctx.repo_root)
                if abs_f.is_file():
                    md_file_ids.add(fid6)
            if ferr:
                load_error_files.append((fpath, frole or "", fid6, ferr))
        if log_format_repo:
            for aid6, apath in conn.execute(
                "SELECT id6, path FROM artifact_paths ORDER BY id6, seq"
            ).fetchall():
                if apath:
                    latest_logged_path[aid6] = apath
    finally:
        conn.close()

    diagnostics: List[Diagnostic] = []
    meta_dir = ctx.records_root / "meta"

    def _add(loc: str, rule: str, detail: str) -> None:
        diagnostics.append(
            Diagnostic(
                location=loc,
                rule=rule,
                detail=_safe(detail),
                severity="error",
            )
        )

    for st in kept:
        abs_p = _meta.source_path(st.path, ctx.records_root, ctx.repo_root)
        loc = _display_location(abs_p, ctx, st.path)
        top_dir, rel_parts = _extract_record_parts(st.path)
        fname = abs_p.name
        has_log = (meta_dir / f"{st.id6}.jsonl").is_file()

        if abs_p.is_file():
            md_file_ids.add(st.id6)
            text = abs_p.read_text(encoding="utf-8", errors="replace")
        else:
            text = None

        in_file: Optional[Any] = None

        # 1 & 2. In-file id mirror and status mirror
        if text is not None:
            if has_log:
                file_id, file_status, mirror_err = _parse_log_backed_mirror(
                    text, st.type
                )
                if not file_id or file_id != st.id6:
                    _add(
                        loc,
                        "meta.id-mirror-drift",
                        f"in-file id mirror {file_id!r} disagrees with log id {st.id6!r}"
                        + (f" ({mirror_err})" if mirror_err else ""),
                    )
                if st.type not in ("walkthrough", "roadmap"):
                    if file_status != st.status:
                        _add(
                            loc,
                            "meta.status-mirror-drift",
                            f"in-file status mirror {file_status!r} disagrees with log status {st.status!r}"
                            + (f" ({mirror_err})" if mirror_err else ""),
                        )
            else:
                in_file = _meta.read_text(text, record_type=st.type)
                file_id = in_file.id6 or None
                if not file_id or file_id != st.id6:
                    _add(
                        loc,
                        "meta.id-mirror-drift",
                        f"in-file id mirror {file_id!r} disagrees with cached id {st.id6!r}",
                    )
                if st.type not in ("walkthrough", "roadmap"):
                    if st.status is not None:
                        if in_file.status != st.status:
                            _add(
                                loc,
                                "meta.status-mirror-drift",
                                f"in-file status mirror {in_file.status!r} disagrees with cached status {st.status!r}",
                            )
                    else:
                        _add(
                            loc,
                            "meta.status-mirror-drift",
                            f"in-file status mirror is missing or non-canonical ({st.legacy_raw_status!r})",
                        )

        # 3-7. Filename Set, NN, id6, date, and D177 facets (through artifact_naming)
        if not _naming.parse_legacy_timestamp(fname):
            parsed = _naming.parse_attributed(fname)
            if parsed is not None:
                # 3. Filename Set
                if st.set_id and parsed.set != st.set_id:
                    _add(
                        loc,
                        "meta.filename-set-drift",
                        f"filename Set {parsed.set!r} disagrees with cached set {st.set_id!r}",
                    )
                elif (
                    not has_log
                    and st.legacy_raw_set
                    and not st.legacy_raw_set.startswith(("`", "'", '"'))
                    and parsed.set != st.legacy_raw_set
                ):
                    _add(
                        loc,
                        "meta.filename-set-drift",
                        f"filename Set {parsed.set!r} disagrees with declared Set {st.legacy_raw_set!r}",
                    )

                # 4. Filename NN (non-research; research order belongs to research facet row)
                if st.type != "research":
                    fname_nn = int(parsed.nn)
                    f_ord = st.fields.get("order")
                    exp_ord: Optional[int] = None
                    if f_ord is not None and str(f_ord).strip() != "":
                        with contextlib.suppress(ValueError, TypeError):
                            exp_ord = int(f_ord)
                    elif st.order_nn is not None:
                        exp_ord = st.order_nn
                    if exp_ord is not None and fname_nn != exp_ord:
                        _add(
                            loc,
                            "meta.filename-order-drift",
                            f"filename order {fname_nn:02d} disagrees with cached order {exp_ord:02d}",
                        )

                # 5. Filename id6
                if parsed.id6 != st.id6:
                    _add(
                        loc,
                        "meta.filename-id-drift",
                        f"filename id6 {parsed.id6!r} disagrees with cached id {st.id6!r}",
                    )

                # 6. Filename date (never compared against created_day or UTC at)
                parsed_iso = f"{parsed.date[:4]}-{parsed.date[4:6]}-{parsed.date[6:8]}"
                exp_date = _normalize_iso_day(st.filename_date)
                if exp_date and parsed_iso != exp_date:
                    _add(
                        loc,
                        "meta.filename-date-drift",
                        f"filename date {parsed_iso!r} disagrees with filename_date {exp_date!r}",
                    )
                elif not has_log and st.type != "research" and in_file is not None:
                    file_date = _normalize_iso_day(in_file.fields.get("date"))
                    if file_date and parsed_iso != file_date:
                        _add(
                            loc,
                            "meta.filename-date-drift",
                            f"filename date {parsed_iso!r} disagrees with declared Date {file_date!r}",
                        )

                # 7. D177 attribution facets (ace, model) on non-research artifacts
                if st.type != "research":
                    exp_ace = _norm_opt_str(st.fields.get("ace"))
                    exp_model = _norm_opt_str(st.fields.get("model"))
                    d177_diffs: List[str] = []
                    if (parsed.ace or None) != exp_ace:
                        d177_diffs.append(
                            f"ace filename={parsed.ace!r} cached={exp_ace!r}"
                        )
                    if (parsed.model or None) != exp_model:
                        d177_diffs.append(
                            f"model filename={parsed.model!r} cached={exp_model!r}"
                        )
                    if d177_diffs:
                        _add(
                            loc,
                            "meta.filename-d177-drift",
                            "D177 filename facet drift: " + "; ".join(d177_diffs),
                        )

        # 8. Research filename facets (order, model, kind)
        if st.type == "research":
            res_err = _check_research_facets(st, fname, ctx.repo_root)
            if res_err:
                _add(loc, "meta.research-facet-drift", res_err)

        # 9. Disposition directory against status
        disp_err = _check_disposition_drift(st, top_dir, rel_parts)
        if disp_err:
            _add(loc, "meta.disposition-drift", disp_err)

        # 12 & 13. Log-format-only checks (logged path and orphan record)
        if log_format_repo:
            if has_log:
                logged_p = latest_logged_path.get(st.id6)
                if logged_p and not abs_p.is_file():
                    _add(
                        loc,
                        "meta.path-drift",
                        f"logged path {logged_p!r} does not exist on disk",
                    )
                elif logged_p and logged_p != st.path:
                    _add(
                        loc,
                        "meta.path-drift",
                        f"logged path {logged_p!r} disagrees with discovered path {st.path!r}",
                    )
            else:
                _add(
                    loc,
                    "meta.orphan-record",
                    f"record {st.id6} has no metadata log at meta/{st.id6}.jsonl",
                )

    # 10. Review rounds against cached review rows (4.1a K4, 4.6)
    seen_review_bindings: Set[Tuple[str, Optional[str]]] = set()
    for rf_path, sid, rref, _rcnt, _pok in review_files_rows:
        binding = (sid, rref)
        seen_review_bindings.add(binding)
        abs_rf = _meta.source_path(rf_path, ctx.records_root, ctx.repo_root)
        rf_loc = _display_location(abs_rf, ctx, rf_path)
        if not abs_rf.is_file():
            continue
        rf_text = abs_rf.read_text(encoding="utf-8", errors="replace")
        file_rounds = [int(m) for m in _ROUND_HEADING_RE.findall(rf_text)]
        subject_has_log = (meta_dir / f"{sid}.jsonl").is_file()
        if subject_has_log:
            expected_rounds = logged_review_rounds.get(binding, [])
            if (
                len(file_rounds) != len(set(file_rounds))
                or len(expected_rounds) != len(set(expected_rounds))
                or sorted(file_rounds) != sorted(expected_rounds)
            ):
                _add(
                    rf_loc,
                    "meta.review-rounds-drift",
                    f"review rounds {file_rounds} disagree with logged review events {expected_rounds} for {sid}",
                )
        else:
            expected_rounds = legacy_review_rounds.get(binding, [])
            if len(file_rounds) != len(set(file_rounds)):
                _add(
                    rf_loc,
                    "meta.review-rounds-drift",
                    f"duplicate review round heading(s) in {rf_loc}: {file_rounds}",
                )
            elif file_rounds and sorted(file_rounds) != sorted(expected_rounds):
                _add(
                    rf_loc,
                    "meta.review-rounds-drift",
                    f"review rounds {file_rounds} disagree with cached review rows {expected_rounds} for {sid}",
                )

    for binding, expected_rounds in sorted(
        logged_review_rounds.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")
    ):
        if binding not in seen_review_bindings and expected_rounds:
            sid, rref = binding
            log_p = meta_dir / f"{sid}.jsonl"
            log_loc = _display_location(log_p, ctx, f"meta/{sid}.jsonl")
            _add(
                log_loc,
                "meta.review-rounds-drift",
                f"logged review rounds {expected_rounds} for {sid} (ref={rref!r}) have no bound review file",
            )

    # 11. Orphans: a meta/*.jsonl file with no tracked artifact or walkthrough record
    incomplete_set = set(rows.incomplete)
    if meta_dir.is_dir():
        for log_p in sorted(meta_dir.glob("*.jsonl")):
            log_id6 = log_p.stem
            log_loc = _display_location(log_p, ctx, f"meta/{log_p.name}")
            if log_id6 not in md_file_ids:
                _add(
                    log_loc,
                    "meta.orphan-log",
                    f"orphan metadata log {log_p.name} has no corresponding record",
                )
            elif log_id6 in incomplete_set:
                err_detail = next(
                    (
                        ferr
                        for fpath, _frole, fid6, ferr in load_error_files
                        if fid6 == log_id6 and fpath == f"meta/{log_p.name}"
                    ),
                    "invalid metadata log",
                )
                _add(log_loc, "meta.invalid-log", err_detail)

    for fpath, frole, _fid6, ferr in load_error_files:
        if frole != "log":
            abs_f = _meta.source_path(fpath, ctx.records_root, ctx.repo_root)
            _add(_display_location(abs_f, ctx, fpath), "meta.invalid-record", ferr)

    diagnostics.sort(key=lambda d: (d.location, d.rule, d.detail))

    counts_by_rule: Dict[str, int] = {}
    for d in diagnostics:
        counts_by_rule[d.rule] = counts_by_rule.get(d.rule, 0) + 1
    counts_by_rule = dict(sorted(counts_by_rule.items()))

    exit_code = 0 if not diagnostics else 1
    status = "clean" if exit_code == 0 else "findings"
    summary = (
        f"0 metadata drift findings across {len(kept)} record(s)"
        if exit_code == 0
        else f"{len(diagnostics)} metadata drift finding(s) across {len(kept)} record(s)"
    )

    evidence = [
        Evidence(key="checked", value=len(kept), status="verified"),
        Evidence(key="findings", value=len(diagnostics), status=status),
    ]
    for rule_id, cnt in counts_by_rule.items():
        evidence.append(Evidence(key=rule_id, value=cnt, status="findings"))

    return CommandResult(
        command="check meta",
        status=status,
        exit_code=exit_code,
        summary=summary,
        diagnostics=diagnostics,
        evidence=evidence,
        data={
            "target": "meta",
            "checked": len(kept),
            "findings": len(diagnostics),
            "counts_by_rule": counts_by_rule,
            "not_applicable": not_applicable,
            "repo_root": str(ctx.repo_root),
        },
        next_actions=(
            [NextAction(command="aw meta repair <id6>")] if diagnostics else []
        ),
        verified=True,
        complete=True,
        repo_root=ctx.repo_root,
    )


def render_check_meta_human(result: CommandResult) -> str:
    """Render an `aw check meta` result for human operators."""
    lines: List[str] = []
    for d in result.diagnostics:
        lines.append(f"{d.location}: {d.rule}: {d.detail}")
    na_rows = result.data.get("not_applicable") or []
    for row in na_rows:
        lines.append(f"  [{row['row']}] {row['status']}")
    counts = result.data.get("counts_by_rule") or {}
    if counts:
        lines.append("Counts by rule:")
        for rule_id, cnt in counts.items():
            lines.append(f"  {rule_id}: {cnt}")
    lines.append(result.summary)
    return "\n".join(lines) + "\n"


def render_check_meta_agent(result: CommandResult, ctx: Any) -> str:
    """Render an `aw check meta` result as streaming `aw.agent/v1` JSONL ending with `summary`."""
    from agent_workflows import agent_schema as _schema
    from agent_workflows.renderers import AgentRenderer

    renderer = AgentRenderer()
    if result.exit_code == 2 or result.status in ("cannot-run", "error"):
        return renderer.render(result, ctx)

    repo_root = result.repo_root or result.data.get("repo_root")
    all_items: List[Dict[str, Any]] = [
        {
            "location": _schema.normalize_repo_path(d.location, repo_root),
            "rule": d.rule,
            "detail": _schema.redact_home_paths(d.detail),
            "severity": d.severity,
        }
        for d in result.diagnostics
    ]

    tot = len(all_items)
    limit = getattr(ctx, "limit", None)
    if limit is not None and limit < tot:
        emitted_items = all_items[:limit]
        omitted = tot - limit
        complete = False
        next_cmd: Optional[str] = f"aw check meta --agent --limit {tot}"
    else:
        emitted_items = all_items
        omitted = 0
        complete = True
        next_cmd = None

    lines: List[str] = []
    for item in emitted_items:
        lines.append(renderer.render_item(item, cmd="check meta", context=ctx))

    summary_rec: Dict[str, Any] = {
        "schema": _schema.SCHEMA_VERSION,
        "kind": "summary",
        "cmd": "check meta",
        "outcome": result.status,
        "exit": result.exit_code,
        "total": tot,
        "emitted": len(emitted_items),
        "omitted": omitted,
        "complete": complete,
        "checked": int(result.data.get("checked", 0)),
        "counts_by_rule": dict(result.data.get("counts_by_rule") or {}),
        "not_applicable": list(result.data.get("not_applicable") or []),
    }
    if next_cmd is not None:
        summary_rec["next"] = next_cmd
    fields = getattr(ctx, "fields", None)
    if fields:
        summary_rec = _schema.filter_record_fields(summary_rec, fields)
        if next_cmd is not None and "next" not in summary_rec:
            summary_rec["next"] = next_cmd
    lines.append(_schema.render_guarded_jsonl_record(summary_rec))
    return "".join(lines)


# --------------------------------------------------------------------------------------------------
# aw meta repair (spec 4sd62s 4.3, 4.7, 4.8)
# --------------------------------------------------------------------------------------------------


def _compute_diverged_tail(
    events: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split a duplicate-seq log into ``(winning_prefix, resequenced_tail)`` matching `artifact_meta.repair`."""
    winning_prefix: List[Dict[str, Any]] = []
    seen: Set[int] = set()
    tail_events: List[Dict[str, Any]] = []
    for ev in events:
        s = ev["seq"]
        if s not in seen and not tail_events:
            seen.add(s)
            winning_prefix.append(ev)
        else:
            tail_events.append(ev)

    last_k = winning_prefix[-1]["seq"] if winning_prefix else 0
    resequenced: List[Dict[str, Any]] = []
    for i, ev in enumerate(tail_events, start=1):
        ev_copy = dict(ev)
        ev_copy["seq"] = last_k + i
        ev_copy["append"] = last_k + i
        resequenced.append(ev_copy)
    return winning_prefix, resequenced


def _state_field_diffs(before: Any, after: Any) -> List[Dict[str, Any]]:
    """Compute every resulting field change between two `artifact_meta.State` snapshots."""
    diffs: List[Dict[str, Any]] = []
    for attr, label in (
        ("status", "status"),
        ("path", "path"),
        ("set_id", "set"),
        ("order_nn", "order"),
        ("title", "title"),
        ("short_description", "short_description"),
    ):
        old_v = getattr(before, attr, None)
        new_v = getattr(after, attr, None)
        if old_v != new_v:
            diffs.append({"field": label, "before": old_v, "after": new_v})

    seen_keys = {"status", "path", "set", "order", "title", "short_description"}
    all_field_keys = sorted(
        (set((before.fields or {}).keys()) | set((after.fields or {}).keys()))
        - seen_keys
    )
    for k in all_field_keys:
        old_v = (before.fields or {}).get(k)
        new_v = (after.fields or {}).get(k)
        if old_v != new_v:
            diffs.append({"field": k, "before": old_v, "after": new_v})
    return diffs


def _find_pending_move_source(
    ctx: MetaContext,
    id6: str,
    target_rel: str,
    artifact_paths: Sequence[Dict[str, Any]],
) -> Optional[Tuple[str, Path]]:
    """Find an existing file on disk that belongs to ``id6`` when ``target_rel`` does not exist."""
    for ap in reversed(artifact_paths):
        cand_rel = ap.get("path")
        if not cand_rel or cand_rel == target_rel:
            continue
        cand_p = _meta.source_path(cand_rel, ctx.records_root, ctx.repo_root)
        if cand_p.is_file():
            return cand_rel, cand_p
    return None


def _describe_mirror_diff(
    current_txt: str,
    expected_txt: str,
    id6: str,
    art_type: str,
    target_status: Optional[str],
) -> str:
    """Summarize the mirror change between ``current_txt`` and ``expected_txt``."""
    old_id, old_status, _ = _parse_log_backed_mirror(current_txt, art_type)
    parts: List[str] = []
    if old_id != id6:
        parts.append(f"id: {old_id!r} -> {id6!r}")
    if art_type not in ("walkthrough", "roadmap") and old_status != target_status:
        parts.append(f"status: {old_status!r} -> {target_status!r}")
    if not parts:
        parts.append("normalize in-file front-matter mirror and managed banner")
    return "; ".join(parts)


def meta_repair(
    repo_root: Path,
    id6: str,
    *,
    apply: bool = False,
    confirm: bool = False,
) -> CommandResult:
    """Preview or apply metadata repair for ``id6`` over `artifact_meta.repair` (4.3, 4.7).

    Preview by default (writes nothing). `--apply` performs deterministic mirror, journal, and
    pending-move repair with no new event (log stays byte-identical, idempotent). A diverged tail
    prints every resulting field change and requires `--apply --confirm`. On a phase-B legacy
    record with no log, reports `nothing to repair (legacy format)`.
    """
    from agent_workflows import artifact_core as _core

    ctx = meta_context(repo_root)
    tok = str(id6 or "").strip()
    if not _core.ID6_RE.fullmatch(tok):
        return CommandResult(
            command="meta repair",
            status="cannot-run",
            exit_code=2,
            summary=f"invalid id6 {tok!r}: expected 6 lowercase base36 characters",
            diagnostics=[
                Diagnostic(
                    location=tok or "<id6>",
                    rule="invalid-id6",
                    detail=f"invalid id6 {tok!r}",
                    severity="error",
                )
            ],
            next_actions=[NextAction(command="aw meta repair --help")],
            verified=False,
            complete=False,
            applied=False,
            repo_root=ctx.repo_root,
        )

    if not _has_any_record_root(ctx):
        return CommandResult(
            command="meta repair",
            status="cannot-run",
            exit_code=2,
            summary="no records directory found; this is not an aw project (run `aw install .`)",
            next_actions=[NextAction(command="aw install .")],
            verified=False,
            complete=False,
            applied=False,
            repo_root=ctx.repo_root,
        )

    log_path = ctx.records_root / "meta" / f"{tok}.jsonl"
    j_file = _meta._journal_dir(ctx.state_root) / f"{tok}.json"

    if not log_path.is_file() and not j_file.is_file():
        legacy_hit = _meta.resolve(tok, project_context=ctx)
        if legacy_hit:
            return CommandResult(
                command="meta repair",
                status="clean",
                exit_code=0,
                summary="nothing to repair (legacy format)",
                data={
                    "id6": tok,
                    "format": "legacy",
                    "path": legacy_hit,
                    "diverged": False,
                    "field_changes": [],
                    "planned_actions": [],
                    "repaired": False,
                },
                verified=True,
                complete=True,
                applied=False,
                repo_root=ctx.repo_root,
            )
        return CommandResult(
            command="meta repair",
            status="cannot-run",
            exit_code=2,
            summary=f"artifact not found: {tok}",
            diagnostics=[
                Diagnostic(
                    location=tok,
                    rule="artifact-not-found",
                    detail=f"no metadata log or tracked record found for {tok}",
                    severity="error",
                )
            ],
            next_actions=[NextAction(command=f"aw find {tok}")],
            verified=False,
            complete=False,
            applied=False,
            repo_root=ctx.repo_root,
        )

    # Check journal-only pending create before reading log
    journal_data: Optional[Dict[str, Any]] = None
    if j_file.is_file():
        try:
            journal_data = json.loads(j_file.read_text(encoding="utf-8"))
        except Exception as exc:
            return CommandResult(
                command="meta repair",
                status="cannot-run",
                exit_code=2,
                summary=f"corrupt operation journal for {tok}: {_safe(str(exc))}",
                next_actions=[NextAction(command="aw check meta")],
                verified=False,
                complete=False,
                applied=False,
                repo_root=ctx.repo_root,
            )
        if journal_data.get("op") == "create" and not journal_data.get("body"):
            return CommandResult(
                command="meta repair",
                status="cannot-run",
                exit_code=2,
                summary="refused repair: missing recovery source (empty body)",
                diagnostics=[
                    Diagnostic(
                        location=f"meta/{tok}.jsonl",
                        rule="missing-recovery-source",
                        detail="pending create journal has no body payload",
                        severity="error",
                    )
                ],
                next_actions=[NextAction(command="aw check meta")],
                verified=False,
                complete=False,
                applied=False,
                repo_root=ctx.repo_root,
            )

    if not log_path.is_file():
        # Journal exists without log: delegate on apply, preview on dry-run
        dest_rel = str((journal_data or {}).get("destination") or "")
        planned = [
            {
                "kind": "restore",
                "path": dest_rel,
                "detail": "restore body from operation journal",
            }
        ]
        if not apply:
            return CommandResult(
                command="meta repair",
                status="preview",
                exit_code=0,
                summary=f"preview: 1 journal recovery action for {tok}",
                changes=[Change(kind="create", path=dest_rel, applied=False)],
                next_actions=[NextAction(command=f"aw meta repair {tok} --apply")],
                data={
                    "id6": tok,
                    "diverged": False,
                    "field_changes": [],
                    "planned_actions": planned,
                    "repaired": False,
                },
                verified=True,
                complete=True,
                applied=False,
                repo_root=ctx.repo_root,
            )
        _meta.repair(tok, confirm=confirm, project_context=ctx)
        return CommandResult(
            command="meta repair",
            status="ok",
            exit_code=0,
            summary=f"repaired {tok}: restored from operation journal",
            changes=[Change(kind="create", path=dest_rel, applied=True)],
            data={
                "id6": tok,
                "diverged": False,
                "field_changes": [],
                "planned_actions": planned,
                "repaired": True,
            },
            verified=True,
            complete=True,
            applied=True,
            repo_root=ctx.repo_root,
        )

    # Log exists: decode and inspect without mutating any file
    try:
        raw_lines = (
            log_path.read_text(encoding="utf-8")
            .replace("\r\n", "\n")
            .splitlines(keepends=True)
        )
        events = [_meta.decode_line(ln) for ln in raw_lines]
        if not events:
            raise ValueError("empty event log")
    except Exception as exc:
        return CommandResult(
            command="meta repair",
            status="cannot-run",
            exit_code=2,
            summary=f"cannot decode log for {tok}: {_safe(str(exc))}",
            diagnostics=[
                Diagnostic(
                    location=_display_location(log_path, ctx, f"meta/{tok}.jsonl"),
                    rule="invalid-log",
                    detail=_safe(str(exc)),
                    severity="error",
                )
            ],
            next_actions=[NextAction(command="aw check meta")],
            verified=False,
            complete=False,
            applied=False,
            repo_root=ctx.repo_root,
        )

    art_type = events[0].get("fields", {}).get("type", "ipd")
    seqs = [e["seq"] for e in events]
    has_duplicate_seq = len(seqs) != len(set(seqs))

    field_diffs: List[Dict[str, Any]] = []
    tail_notes: List[str] = []
    resequenced_count = 0

    if has_duplicate_seq:
        winning_prefix, resequenced = _compute_diverged_tail(events)
        resequenced_count = len(resequenced)
        try:
            prefix_state, _, _, _ = _meta.replay(
                tok, art_type, winning_prefix, records_root=ctx.records_root
            )
            target_state, _, artifact_paths, _ = _meta.replay(
                tok,
                art_type,
                winning_prefix + resequenced,
                records_root=ctx.records_root,
            )
        except Exception as exc:
            return CommandResult(
                command="meta repair",
                status="cannot-run",
                exit_code=2,
                summary=f"refused divergent-tail repair for {tok}: {_safe(str(exc))} (both histories preserved)",
                diagnostics=[
                    Diagnostic(
                        location=_display_location(log_path, ctx, f"meta/{tok}.jsonl"),
                        rule="diverged-tail-unreconcilable",
                        detail=_safe(str(exc)),
                        severity="error",
                    )
                ],
                next_actions=[NextAction(command=f"aw show {tok} --history")],
                data={
                    "id6": tok,
                    "diverged": True,
                    "field_changes": [],
                    "repaired": False,
                },
                verified=False,
                complete=False,
                applied=False,
                repo_root=ctx.repo_root,
            )
        field_diffs = _state_field_diffs(prefix_state, target_state)
        for ev in resequenced:
            if ev.get("op") == "note" and ev.get("message"):
                tail_notes.append(_safe(str(ev["message"])))
    else:
        try:
            target_state, _, artifact_paths, _ = _meta.replay(
                tok, art_type, raw_lines, records_root=ctx.records_root
            )
        except Exception as exc:
            return CommandResult(
                command="meta repair",
                status="cannot-run",
                exit_code=2,
                summary=f"cannot replay log for {tok}: {_safe(str(exc))}",
                diagnostics=[
                    Diagnostic(
                        location=_display_location(log_path, ctx, f"meta/{tok}.jsonl"),
                        rule="invalid-log",
                        detail=_safe(str(exc)),
                        severity="error",
                    )
                ],
                next_actions=[NextAction(command="aw check meta")],
                verified=False,
                complete=False,
                applied=False,
                repo_root=ctx.repo_root,
            )

    planned_actions: List[Dict[str, Any]] = []
    change_objs: List[Change] = []

    if has_duplicate_seq:
        log_loc = _display_location(log_path, ctx, f"meta/{tok}.jsonl")
        planned_actions.append(
            {
                "kind": "resequence",
                "path": log_loc,
                "detail": f"resequence {resequenced_count} diverged tail event(s) after seq {winning_prefix[-1]['seq']}",
            }
        )
        change_objs.append(Change(kind="modify", path=log_loc, applied=False))

    if journal_data is not None and journal_data.get("op") == "create":
        dest_rel = str(journal_data.get("destination") or target_state.path or "")
        dest_p = _meta.source_path(dest_rel, ctx.records_root, ctx.repo_root)
        dest_loc = _display_location(dest_p, ctx, dest_rel)
        planned_actions.append(
            {
                "kind": "restore",
                "path": dest_loc,
                "detail": "restore body from pending create journal",
            }
        )
        change_objs.append(Change(kind="create", path=dest_loc, applied=False))

    move_pair: Optional[Tuple[Path, Path, str, str]] = None
    target_path_rel = target_state.path
    if target_path_rel:
        dest_p = _meta.source_path(target_path_rel, ctx.records_root, ctx.repo_root)
        dest_loc = _display_location(dest_p, ctx, target_path_rel)
        if not dest_p.is_file() and not (
            journal_data is not None and journal_data.get("op") == "create"
        ):
            found = _find_pending_move_source(ctx, tok, target_path_rel, artifact_paths)
            if found is not None:
                src_rel, src_p = found
                src_loc = _display_location(src_p, ctx, src_rel)
                move_pair = (src_p, dest_p, src_loc, dest_loc)
                planned_actions.append(
                    {
                        "kind": "move",
                        "from": src_loc,
                        "path": dest_loc,
                        "detail": f"move {src_loc} -> {dest_loc}",
                    }
                )
                change_objs.append(Change(kind="rename", path=dest_loc, applied=False))
            else:
                return CommandResult(
                    command="meta repair",
                    status="cannot-run",
                    exit_code=2,
                    summary=(
                        f"refused repair for {tok}: missing recovery source "
                        f"(artifact file absent at {dest_loc})"
                    ),
                    diagnostics=[
                        Diagnostic(
                            location=dest_loc,
                            rule="missing-recovery-source",
                            detail=(
                                f"artifact file absent at {dest_loc} and no pending "
                                "move source or create journal exists"
                            ),
                            severity="error",
                        )
                    ],
                    next_actions=[NextAction(command="aw check meta")],
                    data={
                        "id6": tok,
                        "diverged": has_duplicate_seq,
                        "field_changes": field_diffs,
                        "planned_actions": planned_actions,
                        "repaired": False,
                    },
                    verified=False,
                    complete=False,
                    applied=False,
                    repo_root=ctx.repo_root,
                )

        # Check in-file mirror diff against the file that exists (at dest_p or move source)
        inspect_p = (
            dest_p if dest_p.is_file() else (move_pair[0] if move_pair else None)
        )
        if inspect_p is not None and inspect_p.is_file():
            cur_txt = inspect_p.read_text(encoding="utf-8")
            exp_txt = _meta.apply_in_file_mirror(
                cur_txt, tok, target_state.type, target_state.status
            )
            if cur_txt != exp_txt:
                diff_desc = _describe_mirror_diff(
                    cur_txt, exp_txt, tok, target_state.type, target_state.status
                )
                planned_actions.append(
                    {
                        "kind": "mirror",
                        "path": dest_loc,
                        "detail": diff_desc,
                    }
                )
                change_objs.append(Change(kind="modify", path=dest_loc, applied=False))

    # Nothing to repair (idempotent clean state)
    if not planned_actions:
        return CommandResult(
            command="meta repair",
            status="clean",
            exit_code=0,
            summary=f"nothing to repair: {tok} mirrors and location match the log",
            data={
                "id6": tok,
                "diverged": False,
                "field_changes": [],
                "planned_actions": [],
                "repaired": False,
            },
            verified=True,
            complete=True,
            applied=False,
            repo_root=ctx.repo_root,
        )

    # Preview mode (default)
    if not apply:
        next_cmd = (
            f"aw meta repair {tok} --apply --confirm"
            if has_duplicate_seq
            else f"aw meta repair {tok} --apply"
        )
        summary = (
            f"preview: {len(planned_actions)} repair action(s) for {tok} "
            f"(diverged tail requires --confirm)"
            if has_duplicate_seq
            else f"preview: {len(planned_actions)} repair action(s) for {tok}"
        )
        return CommandResult(
            command="meta repair",
            status="preview",
            exit_code=0,
            summary=summary,
            changes=change_objs,
            next_actions=[NextAction(command=next_cmd)],
            data={
                "id6": tok,
                "diverged": has_duplicate_seq,
                "field_changes": field_diffs,
                "tail_notes": tail_notes,
                "planned_actions": planned_actions,
                "repaired": False,
            },
            verified=True,
            complete=True,
            applied=False,
            repo_root=ctx.repo_root,
        )

    # Diverged tail requires --confirm on --apply (spec 4.7)
    if has_duplicate_seq and not confirm:
        return CommandResult(
            command="meta repair",
            status="cannot-run",
            exit_code=2,
            summary=(
                f"diverged tail detected for {tok}; review the resulting field changes "
                f"and re-run with --apply --confirm"
            ),
            diagnostics=[
                Diagnostic(
                    location=_display_location(log_path, ctx, f"meta/{tok}.jsonl"),
                    rule="diverged-tail-confirm-required",
                    detail="pass --confirm to resequence diverged tail events",
                    severity="error",
                )
            ],
            next_actions=[
                NextAction(command=f"aw meta repair {tok} --apply --confirm")
            ],
            data={
                "id6": tok,
                "diverged": True,
                "field_changes": field_diffs,
                "tail_notes": tail_notes,
                "planned_actions": planned_actions,
                "repaired": False,
            },
            verified=False,
            complete=False,
            applied=False,
            repo_root=ctx.repo_root,
        )

    # Apply mode
    if move_pair is not None:
        src_p, dest_p, _src_loc, _dest_loc = move_pair
        dest_p.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_p), str(dest_p))

    rep = _meta.repair(tok, confirm=confirm, project_context=ctx)
    applied_changes = [
        Change(kind=c.kind, path=c.path, applied=True) for c in change_objs
    ]
    return CommandResult(
        command="meta repair",
        status="ok",
        exit_code=0,
        summary=f"repaired {tok}: {len(planned_actions)} action(s) applied",
        changes=applied_changes,
        evidence=[
            Evidence(key="id6", value=tok, status="verified"),
            Evidence(key="actions", value=len(planned_actions), status="verified"),
            Evidence(key="seq", value=int(rep.get("seq", 0)), status="verified"),
        ],
        data={
            "id6": tok,
            "diverged": has_duplicate_seq,
            "field_changes": field_diffs,
            "tail_notes": tail_notes,
            "planned_actions": planned_actions,
            "repaired": bool(rep.get("repaired")),
            "status": rep.get("status"),
            "seq": rep.get("seq"),
        },
        verified=True,
        complete=True,
        applied=True,
        repo_root=ctx.repo_root,
    )


def render_meta_repair_human(result: CommandResult) -> str:
    """Render an `aw meta repair` result for human operators."""
    lines: List[str] = []
    field_changes = result.data.get("field_changes") or []
    tail_notes = result.data.get("tail_notes") or []
    planned_actions = result.data.get("planned_actions") or []

    if field_changes or tail_notes:
        lines.append("Resulting field changes from tail reconciliation:")
        for fc in field_changes:
            lines.append(f"  {fc['field']}: {fc['before']!r} -> {fc['after']!r}")
        for note in tail_notes:
            lines.append(f"  note: {note}")

    if planned_actions:
        header = (
            "Applied:"
            if result.applied
            else "Planned changes (preview, no files modified):"
        )
        lines.append(header)
        for act in planned_actions:
            lines.append(f"  [{act['kind']}] {act['path']}: {act['detail']}")

    lines.append(result.summary)
    if result.next_actions and not result.applied:
        lines.append(f"Next: {result.next_actions[0].command}")
    return "\n".join(lines) + "\n"
