"""Read commands served through `artifact_meta` (spec `4sd62s` 4.5, 4.8; IPD `1ajqaa`).

Three operator surfaces live here, each answered ONLY by the public `artifact_meta` interface
(`resolve`, `read`, `history`, `query`, and the cache rebuild in `index_rebuild`):

- `aw show <ref> --history`: the event history of every artifact the selector names.
- `aw show <ref> --format json`: the replayed state of every artifact the selector names.
- `aw index rebuild`: delete and rebuild the SQLite cache from the tracked sources.

This module holds no parser of its own. It never opens a `meta/*.jsonl` log or a `.md` record:
the loader inside `artifact_meta` does that (spec C5a), so the commands here give the same answer
on a cold, warm, deleted, or corrupt cache.

Display safety: every string taken from an imported legacy history line, or from a log event's
`message`, passes through `attention_contract.neutralize_control_characters` before it is returned
(4.2, SR-903), so a terminal never receives raw control or bidi characters from record text.
"""

from __future__ import annotations

import contextlib
import dataclasses
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from agent_workflows import artifact_meta as _meta
from agent_workflows import attention_contract as _att
from agent_workflows.result_types import CommandResult, Diagnostic, Evidence, NextAction

__all__ = [
    "MetaContext",
    "meta_context",
    "resolve_selector",
    "show_history",
    "show_json",
    "index_rebuild",
    "refresh_cache",
    "render_history_human",
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

    # Path forms: normalize to a records-root-relative path, then ask `resolve`.
    candidates: List[str] = []
    p = Path(tok)
    with contextlib.suppress(Exception):
        if p.is_absolute():
            candidates.append(str(p.resolve().relative_to(ctx.records_root.resolve())))
    clean = tok.replace("\\", "/")
    candidates.append(clean)
    for prefix in (".aw/records/", "records/"):
        if clean.startswith(prefix):
            candidates.append(clean[len(prefix) :])
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


def index_rebuild(repo_root: Path) -> CommandResult:
    """Delete the cache and rebuild it from empty through `artifact_meta` (4.5).

    Writes no tracked file: the cache lives under the gitignored state root. Reports the counts of
    artifacts, walkthroughs, review files, events, and valid and invalid records. An invalid record
    is a FINDING (exit 1) naming the record, because the rebuild itself succeeded.
    """
    ctx = meta_context(repo_root)
    if not ctx.records_root.is_dir():
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
        _meta.check_freshness(conn, ctx.records_root, force=True)

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
        cache_rel = str((ctx.state_root / "index.db").relative_to(ctx.repo_root))
    except ValueError:
        cache_rel = str(ctx.state_root / "index.db")
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


def refresh_cache(repo_root: Path) -> None:
    """Best-effort freshness pass after a typed `aw index <type>` (IPD `1ajqaa` E-06).

    Swallows every error: the typed spellings keep their own output and exit code in phase A, and
    `aw index rebuild` is the command that reports invalid records.
    """
    with contextlib.suppress(Exception):
        ctx = meta_context(repo_root)
        # A repository with no records tree gets no cache: the typed spelling refused (or had
        # nothing to index), and creating `.aw/state/` there would write into a non-project dir.
        if not ctx.records_root.is_dir():
            return
        conn = _meta.open_cache(ctx.records_root, ctx.state_root)
        try:
            _meta.check_freshness(conn, ctx.records_root)
        finally:
            conn.close()
