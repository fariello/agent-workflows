"""Research scan + query + drift check (Set research-org, Order 03).

``_scan_docs`` builds one ``DocEntry`` per research doc purely from its filename and frontmatter;
``aw find research`` (``run_find``) queries it, and ``check_drift`` reports the non-INDEX drift
classes (missing/invalid frontmatter, name-vs-frontmatter mismatch, a dangling citation via Order
04's imported detector primitive, and the later stale-state, provenance, model, tier and companion
rules), reached through ``aw check research --all`` and the ``aw research index --check`` alias.
No INDEX file is written: the SQLite metadata cache replaced the generated ``INDEX.{json,md}``
views (spec 4sd62s 4.5). Consumes Order 01 (contract) and Order 04 (dangling detector).
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_meta as _am
from agent_workflows import attention_contract as A
from agent_workflows import research_contract as R
from agent_workflows import research_refs as RF

# No INDEX file is written (spec 4sd62s 4.5); the name is kept because `research_archive` and
# `_doc_entry` still skip a leftover `INDEX.md` in an unmigrated repository (cutover, `cxxmyv`).
INDEX_MD = "INDEX.md"


class DocEntry(NamedTuple):
    """One indexed research doc (derived purely from its filename + frontmatter)."""

    id6: str
    path: str  # posix, relative to the research root
    set_id: str
    order: str
    date: str  # set date from the name
    created: str
    topic: List[str]
    model: str
    kind: str
    status: str
    outcome: str
    summary: str
    consumed_by: List[str]
    # xprio Order 6vgd0k: the recognized-but-optional research `priority` (shared low/medium/high
    # vocab). Empty string when the doc carries no `priority:` key. Defaulted so positional
    # construction elsewhere stays valid.
    priority: str = ""
    has_body: bool = False
    companion: str = ""


# The generic drift record is the shared core's (plans-adopter Order 01); re-export it.
Drift = _core.Drift

# Spec 4sd62s section 4.1: match a single leading `<!-- aw-managed: ... -->` banner comment
# (plus surrounding whitespace) after front matter; never match arbitrary HTML comments.
_LEADING_AW_MANAGED_BANNER_RE = re.compile(
    r"\A[ \t\r\n]*<!--\s*aw-managed:.*?-->[ \t\r\n]*", re.DOTALL
)
_ISO_DAY_RE = re.compile(r"\A(\d{4})-(\d{2})-(\d{2})\Z")


def has_research_body(text: str) -> bool:
    """Return True when research markdown ``text`` has body content after front matter.

    Ignores at most one leading 4.1 ``<!-- aw-managed: ... -->`` banner comment plus whitespace,
    and treats any other text (including non-banner HTML comments) as real body content.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return False
    closing_idx = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            closing_idx = idx
            break
    if closing_idx == -1:
        return False
    after_fm = "".join(lines[closing_idx + 1 :])
    stripped = _LEADING_AW_MANAGED_BANNER_RE.sub("", after_fm, count=1)
    return bool(stripped.strip())


def _meta_context_for_research_root(
    research_root: Path,
    *,
    repo_root: Optional[Path] = None,
) -> Tuple[Any, Path, Optional[Path]]:
    """Build an ``artifact_meta`` context covering ``research_root``."""
    rroot = research_root.resolve()
    resolved_repo: Optional[Path] = Path(repo_root).resolve() if repo_root else None
    if resolved_repo is None:
        for cand in (rroot, *rroot.parents):
            cparts = cand.parts
            if len(cparts) >= 4 and cparts[-3:] == (".aw", "records", "research"):
                resolved_repo = cand.parents[2]
                break
            if len(cparts) >= 4 and cparts[-3:] == (".agents", "docs", "research"):
                resolved_repo = cand.parents[2]
                break
    if resolved_repo is None:
        from agent_workflows import project_context as _proj_ctx

        resolved_repo = _proj_ctx.record_owner_root(rroot)
    if resolved_repo is not None:
        ctx = _am.legacy_context(resolved_repo)
        records_root = Path(ctx.logical_roots["records"])
        scan_repo = _am._scan_repo_root(ctx, records_root)
        if rroot.is_relative_to(records_root.resolve()) or (
            scan_repo is not None
            and rroot.is_relative_to((scan_repo / ".agents").resolve())
        ):
            return ctx, records_root, scan_repo
    research_ancestor: Optional[Path] = None
    for cand in (rroot, *rroot.parents):
        if cand.name == "research":
            research_ancestor = cand
            break
    if research_ancestor is not None:
        parent = research_ancestor.parent
        if parent.name == "records":
            records_root = parent
            state_root = parent.parent / "state"
        elif parent.name == "docs" and parent.parent.name == ".agents":
            records_root = parent.parent
            state_root = records_root / ".aw-state"
        else:
            records_root = research_ancestor
            state_root = research_ancestor / ".aw-state"
    else:
        records_root = rroot
        state_root = rroot / ".aw-state"
    ctx = type(
        "LegacyContext",
        (),
        {
            "logical_roots": {"records": str(records_root), "state": str(state_root)},
            "repo_root": resolved_repo or records_root,
        },
    )()
    return ctx, records_root, resolved_repo


def _cached_research_states(
    research_root: Path,
    *,
    repo_root: Optional[Path] = None,
    include_fields: bool = True,
) -> Dict[Path, Any]:
    """Query ``artifact_meta.query(type='research')`` indexed by resolved path under ``research_root``."""
    if not research_root.is_dir():
        return {}
    rroot_res = research_root.resolve()
    ctx, records_root, scan_repo = _meta_context_for_research_root(
        rroot_res, repo_root=repo_root
    )
    with _am.scan_once(), _am.ephemeral_if_uninitialized():
        res = _am.query(
            type="research", project_context=ctx, include_fields=include_fields
        )
    by_path: Dict[Path, Any] = {}
    for st in res.rows:
        if not st.path:
            continue
        try:
            abs_p = _am.source_path(st.path, records_root, scan_repo).resolve()
        except Exception:
            continue
        if abs_p.is_relative_to(rroot_res):
            by_path[abs_p] = st
    return by_path


def _parse_cached_list(val: object) -> object:
    """Convert a cached list or YAML inline-list string ``[a, b]`` into a list of strings."""
    if isinstance(val, list):
        return [str(x) for x in val]
    if isinstance(val, str):
        s = val.strip()
        if s.startswith("[") and s.endswith("]"):
            inner = s[1:-1].strip()
            return [x.strip() for x in inner.split(",")] if inner else []
    return val


def _is_log_backed_research_state(st: Any, rt: Any) -> bool:
    """True when ``st`` is backed by an ``artifact_meta`` event log rather than legacy YAML only."""
    if st is None:
        return False
    if getattr(st, "created_at", None) is not None:
        return True
    st_fields = getattr(st, "fields", None) or {}
    rt_fields = getattr(rt, "fields", None) or {}
    probe_keys = ("outcome", "created", "summary", "topic", "consumed_by")
    has_st_meta = any(st_fields.get(k) is not None for k in probe_keys)
    has_rt_meta = any(k in rt_fields for k in probe_keys)
    return has_st_meta and not has_rt_meta


def _normalize_created_compact(raw: object) -> str:
    s = str(raw or "").strip()
    m = _ISO_DAY_RE.match(s)
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}"
    return s


def _state_to_frontmatter(
    st: Any,
    text: str,
    *,
    parsed: Optional[R.ResearchName] = None,
) -> Optional[Dict[str, object]]:
    """Build a research frontmatter mapping from ``artifact_meta`` state and ``read_text``."""
    rt = _am.read_text(text, record_type="research")
    if _is_log_backed_research_state(st, rt):
        f = st.fields or {}
        fm: Dict[str, object] = {"id": st.id6}
        created_raw = (
            f.get("created")
            or st.created_day
            or (st.created_at[:10] if st.created_at else None)
            or st.filename_date
            or (parsed.date if parsed else None)
        )
        if created_raw is not None:
            fm["created"] = _normalize_created_compact(created_raw)
        set_raw = st.set_id or f.get("set")
        if set_raw is not None:
            fm["set"] = str(set_raw)
        ord_raw = f.get("order") if f.get("order") is not None else st.order_nn
        if ord_raw is not None:
            fm["order"] = (
                f"{int(ord_raw):02d}" if isinstance(ord_raw, int) else str(ord_raw)
            )
        raw_topic = f.get("topic")
        fm["topic"] = _parse_cached_list(raw_topic) if raw_topic is not None else []
        fm["model"] = str(f.get("model") or "")
        kind_raw = f.get("research_kind") or (parsed.kind if parsed else None)
        if kind_raw is not None:
            fm["kind"] = str(kind_raw)
        if st.status is not None:
            fm["status"] = str(st.status)
        fm["outcome"] = str(f.get("outcome") or "")
        fm["summary"] = str(f.get("summary") or st.short_description or "")
        raw_cb = f.get("consumed_by")
        fm["consumed-by"] = _parse_cached_list(raw_cb) if raw_cb is not None else []
        if f.get("priority"):
            fm["priority"] = str(f["priority"])
        return fm

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---" or not rt.fields:
        return None

    f = (st.fields or {}) if st is not None else {}
    fm = {}
    if "id" in rt.fields:
        raw_id = str(rt.fields["id"])
        if not R.is_valid_id6(raw_id):
            fm["id"] = raw_id
        elif st is not None and not st.id_derived and st.id6:
            fm["id"] = st.id6
        else:
            fm["id"] = rt.id6 or raw_id
    if "created" in rt.fields:
        val = f.get("created") if f.get("created") is not None else rt.fields["created"]
        fm["created"] = str(val)
    if "set" in rt.fields:
        val = (
            st.legacy_raw_set
            if (st is not None and st.legacy_raw_set is not None)
            else rt.fields["set"]
        )
        fm["set"] = str(val)
    if "order" in rt.fields:
        raw_ord = str(rt.fields["order"])
        cached_ord = f.get("order")
        if isinstance(cached_ord, int) and raw_ord.isdigit():
            width = max(2, len(raw_ord))
            fm["order"] = f"{cached_ord:0{width}d}"
        else:
            fm["order"] = raw_ord
    if "topic" in rt.fields:
        raw_t = f.get("topic") if f.get("topic") is not None else rt.fields["topic"]
        fm["topic"] = _parse_cached_list(raw_t)
    if "model" in rt.fields:
        if rt.fields["model"] == "":
            fm["model"] = ""
        else:
            val = f.get("model") if f.get("model") is not None else rt.fields["model"]
            fm["model"] = str(val)
    if "kind" in rt.fields:
        val = (
            f.get("research_kind")
            if f.get("research_kind") is not None
            else rt.fields["kind"]
        )
        fm["kind"] = str(val)
    if "status" in rt.fields:
        if rt.fields["status"] == "":
            fm["status"] = ""
        elif st is not None and st.legacy_raw_status is not None:
            fm["status"] = str(st.legacy_raw_status)
        elif st is not None and st.status is not None:
            fm["status"] = str(st.status)
        else:
            fm["status"] = str(rt.fields["status"])
    if "outcome" in rt.fields:
        val = f.get("outcome") if f.get("outcome") is not None else rt.fields["outcome"]
        fm["outcome"] = str(val)
    if "summary" in rt.fields:
        val = f.get("summary") if f.get("summary") is not None else rt.fields["summary"]
        fm["summary"] = str(val)
    if "consumed_by" in rt.fields:
        raw_cb = (
            f.get("consumed_by")
            if f.get("consumed_by") is not None
            else rt.fields["consumed_by"]
        )
        fm["consumed-by"] = _parse_cached_list(raw_cb)
    if "priority" in rt.fields:
        val = (
            f.get("priority")
            if f.get("priority") is not None
            else rt.fields["priority"]
        )
        fm["priority"] = str(val)
    return fm


def _doc_entry(
    research_root: Path,
    p: Path,
    *,
    ignored_dirs: set[str],
    repo_root: Optional[Path] = None,
    _states: Optional[Dict[Path, Any]] = None,
) -> Tuple[Optional[DocEntry], List[Drift]]:
    """Build a ``DocEntry`` for a single research doc at ``p`` via ``artifact_meta``.

    Returns (entry, drift). Returns (None, []) or (None, drift) for skipped docs
    (non-conformant name, missing/invalid frontmatter, or excluded).
    Keyword-only ``ignored_dirs`` must be provided by the caller to prevent redundant git
    subprocesses (F-6).
    """

    if (
        p.name in (INDEX_MD,)
        or p.name == "README.md"
        or _core.is_ignored_path(p, research_root, ignored_dirs)
        or R.companion_owner_stem(p, research_root) is not None
    ):
        return None, []
    try:
        rel = p.relative_to(research_root).as_posix()
    except ValueError:
        return None, []

    states = (
        _states
        if _states is not None
        else _cached_research_states(research_root, repo_root=repo_root)
    )
    st = states.get(p.resolve())

    parsed, name_err = R.parse_name(p.name, repo_root=repo_root)
    if parsed is None:
        # Non-conformant filename: not an indexable research doc; skip quietly (migration
        # handles back-fill). Only report a name-vs-frontmatter mismatch for files that DO
        # carry research frontmatter.
        text = p.read_text(encoding="utf-8")
        if _state_to_frontmatter(st, text, parsed=None) is not None:
            return None, [
                Drift(
                    p.name,
                    "name-invalid",
                    name_err.message if name_err else "bad name",
                )
            ]
        return None, []
    text = p.read_text(encoding="utf-8")
    fm = _state_to_frontmatter(st, text, parsed=parsed)
    if fm is None:
        return None, [Drift(rel, "frontmatter-missing", "no valid frontmatter block")]
    errs = R.validate_frontmatter(fm, repo_root=repo_root)
    if errs:
        return None, [
            Drift(rel, "frontmatter-invalid", f"{e.field}: {e.message}") for e in errs
        ]
    drift: List[Drift] = []
    # name-vs-frontmatter consistency
    if fm.get("id") != parsed.id6:
        drift.append(
            Drift(
                rel,
                "name-frontmatter-mismatch",
                f"id {fm.get('id')} != name {parsed.id6}",
            )
        )
    if fm.get("set") != parsed.set_id:
        drift.append(
            Drift(
                rel,
                "name-frontmatter-mismatch",
                f"set {fm.get('set')} != name {parsed.set_id}",
            )
        )
    if fm.get("order") != parsed.order:
        drift.append(
            Drift(
                rel,
                "name-frontmatter-mismatch",
                f"order {fm.get('order')} != name {parsed.order}",
            )
        )
    fm_kind = fm.get("kind")
    norm_kind = R.normalize_kind(str(fm_kind)).value if fm_kind is not None else None
    if norm_kind != parsed.kind:
        drift.append(
            Drift(
                rel,
                "name-frontmatter-mismatch",
                f"kind {fm_kind} != name {parsed.kind}",
            )
        )
    if parsed.model is not None:
        raw_model = fm.get("model")
        if raw_model is None or (isinstance(raw_model, str) and not raw_model.strip()):
            drift.append(
                Drift(
                    rel,
                    "name-frontmatter-mismatch",
                    f"model (empty) != name {parsed.model}",
                )
            )
        else:
            raw_str = str(raw_model).strip()
            norm_res = R.normalize_model(raw_str, repo_root=repo_root)
            norm_model = norm_res.value if norm_res.ok else raw_str
            if norm_model != parsed.model:
                drift.append(
                    Drift(
                        rel,
                        "name-frontmatter-mismatch",
                        f"model {raw_model} != name {parsed.model}",
                    )
                )
    topic_val = fm.get("topic")
    topic_list = [str(t) for t in topic_val] if isinstance(topic_val, list) else []
    consumed_val = fm.get("consumed-by")
    consumed_list = (
        [str(c) for c in consumed_val] if isinstance(consumed_val, list) else []
    )
    has_body = has_research_body(text)
    comp_dir = R.companion_dir_for(p)
    comp_rel = (
        comp_dir.relative_to(research_root).as_posix() if comp_dir.is_dir() else ""
    )
    entry = DocEntry(
        id6=parsed.id6,
        path=rel,
        set_id=parsed.set_id,
        order=parsed.order,
        date=parsed.date,
        created=str(fm.get("created", "")),
        topic=topic_list,
        model=str(fm.get("model", "") or ""),
        kind=parsed.kind,
        status=str(fm.get("status", "") or ""),
        outcome=str(fm.get("outcome", "") or ""),
        summary=str(fm.get("summary", "") or ""),
        consumed_by=consumed_list,
        priority=str(fm.get("priority", "") or ""),
        has_body=has_body,
        companion=comp_rel,
    )
    return entry, drift


def _scan_docs(
    research_root: Path,
    *,
    repo_root: Optional[Path] = None,
) -> Tuple[List[DocEntry], List[Drift]]:
    """Scan every research doc via ``artifact_meta.query``; return (entries, drift)."""

    entries: List[DocEntry] = []
    drift: List[Drift] = []
    if not research_root.is_dir():
        return entries, drift
    ignored_dirs = _core.get_ignored_dirs(research_root)
    states = _cached_research_states(
        research_root, repo_root=repo_root, include_fields=True
    )
    for p in sorted(research_root.rglob("*.md")):
        if R.companion_owner_stem(p, research_root) is not None:
            continue
        entry, item_drift = _doc_entry(
            research_root,
            p,
            ignored_dirs=ignored_dirs,
            repo_root=repo_root,
            _states=states,
        )
        if entry is not None:
            entries.append(entry)
        drift.extend(item_drift)
    return entries, drift


# --------------------------------------------------------------------------------------
# find
# --------------------------------------------------------------------------------------


def query(
    entries: List[DocEntry],
    *,
    id6: Optional[str] = None,
    set_id: Optional[str] = None,
    topic: Optional[str] = None,
    status: Optional[str] = None,
    position: Optional[str] = None,
    status_not: Optional[str | Sequence[str]] = None,
) -> List[DocEntry]:
    """Filter entries by any combination of id/set/topic/status/position (deterministic order)."""

    out = list(entries)
    if id6:
        out = [e for e in out if e.id6 == id6]
    if set_id:
        out = [e for e in out if e.set_id == set_id]
    if topic:
        out = [e for e in out if topic in e.topic]
    if status:
        # rstodo p3o9je: normalize both sides so `--status todo` matches a legacy `intake` doc (and
        # `--status intake` still matches) during the migration window.
        want = R.normalize_status(status).value or status
        out = [
            e for e in out if (R.normalize_status(e.status).value or e.status) == want
        ]
    if status_not:
        if isinstance(status_not, str):
            not_list = [s.strip() for s in status_not.split(",") if s.strip()]
        else:
            not_list = []
            for item in status_not:
                if item:
                    not_list.extend(
                        s.strip() for s in str(item).split(",") if s.strip()
                    )
        not_set = {(R.normalize_status(s).value or s).lower() for s in not_list}
        out = [
            e
            for e in out
            if (R.normalize_status(e.status).value or e.status or "").lower()
            not in not_set
        ]
    if position:
        positions = derive_pipeline_positions(entries)
        # Shelf outranks position: only a statusless prompt matches position
        out = [
            e
            for e in out
            if e.kind == "research-prompt"
            and not e.status
            and positions.get(e.set_id) == position
        ]
    return sorted(out, key=lambda e: (e.set_id, e.order, e.id6))


# --------------------------------------------------------------------------------------
# pipeline position / unrun / RUN derivation (IPD 5e3nj2): body-aware structural signal
# --------------------------------------------------------------------------------------


def derive_pipeline_positions(entries: List[DocEntry]) -> Dict[str, str]:
    """Derive set-level pipeline positions: unrun / partial / synthesized.

    A set has a position only if some member is `kind: research-prompt`.
    LANDED = non-prompt members with has_body.
    - 'synthesized' if any LANDED member's kind is in SYNTHESIS_KINDS ('reconciliation-report', 'findings');
    - 'partial' if LANDED is non-empty otherwise;
    - 'unrun' if LANDED is empty AND every prompt in the set has outcome == 'none-yet' AND
      no cold shelf status ('reference'/'archive');
    - otherwise absent (a provenance or cold-shelved prompt, not pipeline work).
    """
    by_set: Dict[str, List[DocEntry]] = {}
    for e in entries:
        by_set.setdefault(e.set_id, []).append(e)

    positions: Dict[str, str] = {}
    for set_id, members in by_set.items():
        prompts = [m for m in members if m.kind == "research-prompt"]
        if not prompts:
            continue
        landed = [m for m in members if m.kind != "research-prompt" and m.has_body]
        if any(m.kind in R.SYNTHESIS_KINDS for m in landed):
            positions[set_id] = "synthesized"
        elif landed:
            positions[set_id] = "partial"
        else:
            all_none_yet = all(p.outcome == "none-yet" for p in prompts)
            no_cold = all(
                (R.normalize_status(p.status).value not in R.SHARDED_STATUSES)
                if p.status
                else True
                for p in prompts
            )
            if all_none_yet and no_cold:
                positions[set_id] = "unrun"
    return positions


def derive_unrun_prompts(entries: List[DocEntry]) -> List[DocEntry]:
    """Return the UNRUN research prompts, derived from pipeline positions."""

    positions = derive_pipeline_positions(entries)
    unrun_sets = {s for s, pos in positions.items() if pos == "unrun"}
    unrun = [
        e for e in entries if e.set_id in unrun_sets and e.kind == "research-prompt"
    ]
    return sorted(unrun, key=lambda e: (e.set_id, e.id6))


def unrun_set_ids(entries: List[DocEntry]) -> set:
    """The set-ids that are structurally UNRUN (position == 'unrun')."""

    return {e.set_id for e in derive_unrun_prompts(entries)}


def run_prompt_set_ids(entries: List[DocEntry]) -> set:
    """The set-ids that are RUN PROMPT sets: partial or synthesized."""

    positions = derive_pipeline_positions(entries)
    return {s for s, pos in positions.items() if pos in ("partial", "synthesized")}


# --------------------------------------------------------------------------------------
# cited-by-executed derivation (IPD m383qb E-02): which research id6s are cited by an
# EXECUTED artifact (plan under executed/, spec implemented, or backlog item done). This is
# the REVERSE of find_dangling_citations (which finds a doc's OWN unresolved citations): here
# we scan executed artifacts and collect citations that resolve to a research id6. Built on the
# shared primitives (iter_scan_files + R.iter_id6_citations); does NOT bend find_dangling_citations.
# --------------------------------------------------------------------------------------


def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _plan_is_executed(path: Path, repo_root: Path) -> bool:
    """True when a plan file sits under an ``executed/`` disposition directory.

    A plan's disposition is the first path component under the plans root (kept even inside a
    ``executed/YYYYMM/`` shard). We look at the repo-relative parts so the repo's own directory
    names cannot false-trigger.
    """

    parts = path.parts
    if "executed" not in parts or "plans" not in parts:
        return False
    rel_parts = path.relative_to(repo_root).parts if _under(path, repo_root) else parts
    if "plans" not in rel_parts:
        return False
    idx = rel_parts.index("plans")
    return idx + 1 < len(rel_parts) and rel_parts[idx + 1] == "executed"


def _spec_is_implemented(text: str) -> bool:
    return _am.read_text(text, record_type="spec").status == "implemented"


def _backlog_is_done(path: Path, text: str) -> bool:
    # Directory disposition takes precedence (an item under done/ is done), then cached/parsed status.
    if path.parent.name == "done":
        return True
    return _am.read_text(text, record_type="backlog").status == "done"


def cited_by_executed_ids(
    repo_root: Path,
    research_root: Path,
    *,
    candidate_ids: Optional[Sequence[str] | set[str]] = None,
) -> set:
    """Return the research id6s that are cited by an EXECUTED artifact.

    An artifact is executed when: it is a plan file under an ``executed/`` disposition dir; OR a
    spec whose status in ``artifact_meta`` is ``implemented``; OR a backlog item that is ``done``
    (its ``done/`` dir or ``status == 'done'`` in ``artifact_meta``). A citation from a merely
    pending/draft artifact does NOT count. Reuses ``iter_scan_files`` + ``R.iter_id6_citations``
    (the shared citation primitives); the research tree itself is excluded so a doc citing another
    research doc is not treated as an executed-artifact citation here.

    When ``candidate_ids`` is supplied, only ids in that set are sought, allowing a cheap
    substring precheck and early exit once every candidate has been matched.
    """
    remaining: Optional[set[str]] = (
        set(candidate_ids) if candidate_ids is not None else None
    )
    if remaining is not None and not remaining:
        return set()

    ctx = _am.legacy_context(repo_root)
    records_root = Path(ctx.logical_roots["records"])
    scan_repo = _am._scan_repo_root(ctx, records_root)
    spec_states: Dict[Path, Any] = {}
    backlog_states: Dict[Path, Any] = {}
    with _am.scan_once(), _am.ephemeral_if_uninitialized():
        for rec_type, target_map in (
            ("spec", spec_states),
            ("backlog", backlog_states),
        ):
            for st in _am.query(type=rec_type, project_context=ctx).rows:
                if not st.path:
                    continue
                try:
                    abs_p = _am.source_path(st.path, records_root, scan_repo).resolve()
                except Exception:
                    continue
                target_map[abs_p] = st

    cited: set = set()
    _EXEC_SCAN_ROOTS = (
        ".agents/plans",
        ".agents/docs",
        ".agents/backlog",
        ".aw/records/plans",
        ".aw/records/specs",
        ".aw/records/backlog",
    )
    cand_bytes_re: Optional[re.Pattern[bytes]] = None
    if remaining is not None:
        cand_bytes_re = re.compile(
            b"|".join(re.escape(c.encode("ascii")) for c in sorted(remaining))
        )
    for f in _core.iter_scan_files(repo_root, scan_roots=_EXEC_SCAN_ROOTS):
        if remaining is not None and not remaining:
            break
        # Skip the research tree itself (we want EXECUTED plan/spec/backlog citers).
        if _under(f, research_root):
            continue
        parts = f.parts
        is_plan = "plans" in parts and f.name.endswith(".md")
        is_spec = "specs" in parts and f.name.endswith(".md")
        is_backlog = "backlog" in parts and f.name.endswith(".md")
        if not (is_plan or is_spec or is_backlog):
            continue
        if is_plan and not _plan_is_executed(f, repo_root):
            continue
        executed = False
        text: Optional[str] = None
        if is_plan:
            executed = True
        elif is_spec:
            st = spec_states.get(f.resolve())
            if st is not None:
                executed = st.status == "implemented"
            else:
                try:
                    text = f.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                executed = _spec_is_implemented(text)
        elif is_backlog:
            if f.parent.name == "done":
                executed = True
            else:
                st = backlog_states.get(f.resolve())
                if st is not None:
                    executed = st.status == "done"
                else:
                    try:
                        text = f.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        continue
                    executed = _backlog_is_done(f, text)
        if not executed:
            continue
        if remaining is not None and text is None and cand_bytes_re is not None:
            try:
                raw_bytes = f.read_bytes()
            except OSError:
                continue
            if not cand_bytes_re.search(raw_bytes):
                continue
            try:
                text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                continue
        if text is None:
            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
        if remaining is not None:
            if not any(cid in text for cid in remaining):
                continue
            prev_len = len(remaining)
            for cid in R.iter_id6_citations(text):
                if cid in remaining:
                    cited.add(cid)
                    remaining.discard(cid)
                    if not remaining:
                        break
            if remaining and len(remaining) != prev_len:
                cand_bytes_re = re.compile(
                    b"|".join(re.escape(c.encode("ascii")) for c in sorted(remaining))
                )
        else:
            for cid in R.iter_id6_citations(text):
                cited.add(cid)
    return cited


# --------------------------------------------------------------------------------------
# consumer-id resolution (IPD xjrdjp E-03): the resolvable id6 set spanning the PLAN, SPEC, and
# BACKLOG trees (consumed-by points at those, NOT at research ids). Assembled from artifact_meta;
# this is a cross-tree set, deliberately NOT the research-only resolver (research_refs) nor a
# release-only resolver.
# --------------------------------------------------------------------------------------


def resolvable_consumer_ids(repo_root: Path) -> set:
    """Return every id6 declared by a plan, spec, or backlog artifact via ``artifact_meta.query``.

    These are the artifacts a research doc's ``consumed-by`` may legitimately point at.
    """

    ctx = _am.legacy_context(repo_root)
    ids: set = set()
    with _am.scan_once(), _am.ephemeral_if_uninitialized():
        for rec_type in ("ipd", "spec", "backlog"):
            for st in _am.query(type=rec_type, project_context=ctx).rows:
                if st.id6 and not st.id_derived:
                    ids.add(st.id6)
    return ids


# --------------------------------------------------------------------------------------
# check (the four drift classes + the stale-state-to-promote rule + provenance rules)
# --------------------------------------------------------------------------------------

STALE_STATE_RULE = "stale-state-to-promote"
DANGLING_CONSUMED_RULE = "dangling-consumed-by"
ADOPTED_NO_CONSUMER_RULE = "adopted-without-consumer"
UNRECOGNIZED_MODEL_RULE = "unrecognized-model"
FRONTMATTER_KEY_REPEATED_RULE = "research.frontmatter-key-repeated"
STATUS_TIER_MISMATCH_RULE = "status-tier-mismatch"
RESEARCH_COMPANION_ORPHANED_RULE = "check.research-companion-orphaned"


def check_drift(repo_root: Path, research_root: Path) -> List[Drift]:
    """Return every drift finding across the spec-5.2 four classes."""

    entries, drift = _scan_docs(research_root, repo_root=repo_root)
    # The INDEX-file drift class was deleted by spec `4sd62s` 4.5 (plan `6qh68x`, the research twin
    # of `w819as`): the SQLite metadata cache replaced the INDEX files, so an absent or out-of-date
    # INDEX file is not drift. No INDEX writer remains (plan `s6k01k`).
    # Severity is stamped at the emitter (`check_engine.enrich_drift`) because
    # `check_engine.check_content` does not enrich these findings, so an un-enriched `severity=""`
    # would fail `artifact_core.drift_exit_code`. Enriching at the emitter is what makes the
    # registry the single source of severity for every consumer (sevreg qgpanb E-04 extended it to
    # `dangling-citation`, `stale-state-to-promote`, and `adopted-without-consumer`).
    from agent_workflows import check_engine as _ce

    # Dangling citations via Order 04's imported detector primitive.
    for d in RF.find_dangling_citations(repo_root, research_root):
        drift.append(
            _ce.enrich_drift(
                Drift(f"{d.file}:{d.line}", "dangling-citation", f"id6 {d.id6}")
            )
        )
    # Stale-state-to-promote (IPD m383qb E-02 / IPD 5e3nj2 E-04): a todo/active doc whose SET is SYNTHESIZED
    # OR that is cited by an EXECUTED artifact is stale hot state and must be promoted.
    # A landed todo report in a partial set is legitimately awaiting ingestion.
    hot = [e for e in entries if R.normalize_status(e.status).value in R.HOT_STATUSES]
    if hot:
        positions = derive_pipeline_positions(entries)
        synthesized_sets = {s for s, pos in positions.items() if pos == "synthesized"}
        cited_exec = cited_by_executed_ids(repo_root, research_root)
        for e in hot:
            if e.set_id in synthesized_sets:
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            STALE_STATE_RULE,
                            f"{e.status} doc in RUN set '{e.set_id}'; promote it",
                        )
                    )
                )
            elif e.id6 in cited_exec:
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            STALE_STATE_RULE,
                            f"{e.status} doc cited by an executed artifact; promote it",
                        )
                    )
                )

    # Provenance rules (IPD xjrdjp E-03): a consumed-by that resolves to no plan/spec/backlog
    # artifact is dangling; an adopted doc must name at least one consumer.
    needs_provenance = [e for e in entries if e.consumed_by or e.outcome == "adopted"]
    if needs_provenance:
        consumer_ids = resolvable_consumer_ids(repo_root)
        for e in needs_provenance:
            for cid in e.consumed_by:
                if cid not in consumer_ids:
                    drift.append(
                        Drift(
                            e.path,
                            DANGLING_CONSUMED_RULE,
                            f"consumed-by id6 '{cid}' resolves to no plan/spec/backlog artifact",
                        )
                    )
            if e.outcome == "adopted" and not e.consumed_by:
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            ADOPTED_NO_CONSUMER_RULE,
                            "outcome: adopted requires a non-empty consumed-by",
                        )
                    )
                )

    # Advisory unrecognized-model drift rule (Set modelvocab Order 01 / IPD t38a4o E-07).
    # Emitted in check_drift ONLY (never in _doc_entry or _scan_docs), so the scan that
    # `aw find research` reads is not blocked by unrecognized models.
    for e in entries:
        if e.model:
            m_res = R.normalize_model(e.model, repo_root=repo_root)
            if m_res.ok and not m_res.recognized:
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            UNRECOGNIZED_MODEL_RULE,
                            f"model '{e.model}' is unrecognized; bless with 'aw research add-model {m_res.value or e.model}'",
                        ),
                        recovery=f"aw research add-model {m_res.value or e.model}",
                    )
                )

    # Repeated frontmatter keys (Set jnpl08 / IPD 7d4bgs E-02).
    # Emitted in check_drift ONLY (never in _doc_entry, _scan_docs, or validate_frontmatter),
    # so the scan is not blocked and offending docs are not dropped from `aw find research`.
    # Reads raw text because parse_frontmatter destroys key duplicates by last-wins assignment.
    for e in entries:
        doc_file = research_root / e.path
        try:
            raw_text = doc_file.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = raw_text.splitlines()
        if not lines or lines[0].strip() != "---":
            continue
        key_counts: Dict[str, int] = {}
        seen_closing = False
        for line in lines[1:]:
            if line.strip() == "---":
                seen_closing = True
                break
            if ":" not in line:
                continue
            key = line.partition(":")[0].strip()
            if not key:
                continue
            if key in ("blocks_release", "Blocks-Release"):
                key = "blocks-release"
            key_counts[key] = key_counts.get(key, 0) + 1
        if not seen_closing:
            continue
        for key, count in key_counts.items():
            if count > 1:
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            FRONTMATTER_KEY_REPEATED_RULE,
                            f"frontmatter key '{key}' appears {count} times",
                        )
                    )
                )

    # Unsafe descriptive fields (Section 8.8 / IPD xnogdl E-02).
    # Emitted in check_drift ONLY (never in _doc_entry or validate_frontmatter),
    # so offending docs remain in the scan and are not dropped from `aw find research` (F-06).
    for e in entries:
        if not A.is_safe_descriptive(e.summary):
            drift.append(
                _ce.enrich_drift(
                    Drift(
                        e.path,
                        "attention.unsafe-field",
                        "Summary is over-length or has control chars/newlines",
                    )
                )
            )
        for t in e.topic:
            if not A.is_safe_descriptive(str(t)):
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            "attention.unsafe-field",
                            "Topic is over-length or has control chars/newlines",
                        )
                    )
                )
        for c in e.consumed_by:
            if not A.is_safe_descriptive(str(c)):
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            "attention.unsafe-field",
                            "Consumed-by is over-length or has control chars/newlines",
                        )
                    )
                )

    # Status-versus-tier drift rule (Set zdsf35 / IPD ucwlwt E-02).
    # Emitted in check_drift ONLY (never in _doc_entry or _scan_docs), so the scan that
    # `aw find research` reads is not blocked by tier drift.
    for e in entries:
        st_res = R.normalize_status(e.status or "")
        st = st_res.value
        # F-10: Seven indexed hot-root docs carry status: '' (.research-prompt.md) and normalize
        # to value=None. Missing status is owned by _doc_entry frontmatter classes, not tier drift.
        if st is None:
            continue

        parts = e.path.split("/")
        first_comp = parts[0] if len(parts) > 1 else ""

        # Tier classification:
        # If no directory component, doc sits at the HOT ROOT.
        # If first component is REFERENCE_DIR or ARCHIVE_DIR, doc sits in that COLD tier.
        # If first component is an unrecognized non-cold directory (e.g. plan-review), stay silent (F-06).
        if len(parts) == 1:
            if st in R.SHARDED_STATUSES:
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            STATUS_TIER_MISMATCH_RULE,
                            f"status '{e.status}' requires sharded tier '{st}' but doc sits at hot root; promote with 'aw research promote'",
                        ),
                        recovery=f"aw research promote {e.id6} --to {st}",
                    )
                )
        elif first_comp in (R.REFERENCE_DIR, R.ARCHIVE_DIR):
            if st in R.HOT_STATUSES:
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            STATUS_TIER_MISMATCH_RULE,
                            f"status '{e.status}' requires hot root tier but doc sits in '{first_comp}'; promote with 'aw research promote'",
                        ),
                        recovery=f"aw research promote {e.id6} --to {st}",
                    )
                )

    # Orphaned companion directories (Set rescomp / IPD mtdxiu E-03).
    # Emitted for every *.data directory under research_root (outside ignored dirs) whose owning stem
    # names no document in the SAME directory.
    if research_root.is_dir():
        ignored_dirs = _core.get_ignored_dirs(research_root)
        for dirpath, dirnames, _ in os.walk(research_root):
            dirnames[:] = [
                d
                for d in dirnames
                if not _core.is_ignored_path(
                    Path(dirpath) / d, research_root, ignored_dirs
                )
            ]
            companion_dirs = [d for d in dirnames if d.endswith(R.COMPANION_SUFFIX)]
            dirnames[:] = [d for d in dirnames if not d.endswith(R.COMPANION_SUFFIX)]
            for cdir in sorted(companion_dirs):
                data_dir = Path(dirpath) / cdir
                stem = cdir[: -len(R.COMPANION_SUFFIX)]
                parsed, _ = R.parse_name(stem + ".md", repo_root=repo_root)
                if parsed is None:
                    continue
                doc_path = Path(dirpath) / f"{stem}.md"
                if not doc_path.is_file():
                    rel_companion = data_dir.relative_to(research_root).as_posix()
                    matches = [e for e in entries if e.id6 == parsed.id6]
                    if matches:
                        target = matches[0]
                        detail = f"owning doc sits at '{target.path}'"
                        expected = (
                            R.companion_dir_for(research_root / target.path)
                            .relative_to(research_root)
                            .as_posix()
                        )
                        rec = f"mv {rel_companion} {expected}"
                    else:
                        detail = f"owning doc '{stem}.md' not found"
                        rec = f"rm -rf {rel_companion}"
                    drift.append(
                        _ce.enrich_drift(
                            Drift(
                                rel_companion,
                                RESEARCH_COMPANION_ORPHANED_RULE,
                                f"orphaned companion directory; {detail}",
                            ),
                            recovery=rec,
                        )
                    )

    return drift


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def _roots(args: argparse.Namespace) -> Tuple[Path, Path]:
    from agent_workflows.project_context import (
        resolve_verb_repo_root,
        project_records_dir,
        has_stored_records_placement,
    )

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    from agent_workflows.record_producers import resolve_record_path

    modern_root = project_records_dir(repo_root) / "research"
    if has_stored_records_placement(repo_root):
        res_root = modern_root
    else:
        try:
            res_root = resolve_record_path("research", target_repo=str(repo_root))
        except Exception:
            res_root = modern_root
    if not res_root.is_dir() and (repo_root / ".agents" / "docs" / "research").is_dir():
        res_root = repo_root / ".agents" / "docs" / "research"
    elif not res_root.is_dir() and modern_root.is_dir():
        res_root = modern_root
    return repo_root, res_root


def run_find(args: argparse.Namespace) -> int:
    repo_root, research_root = _roots(args)
    entries, _drift = _scan_docs(research_root, repo_root=repo_root)
    results = query(
        entries,
        id6=getattr(args, "id", None),
        set_id=getattr(args, "set", None),
        topic=getattr(args, "topic", None),
        status=getattr(args, "status", None),
        position=getattr(args, "position", None),
        status_not=getattr(args, "status_not", None),
    )
    if not results:
        from agent_workflows.term import Term
        from agent_workflows.result_types import NextAction

        filters_dict = {}
        for k in ("id", "set", "topic", "status", "status_not", "position"):
            v = getattr(args, k, None)
            if v:
                filters_dict[k] = v
        Term().empty_result(
            summary="no matching research docs",
            filters=filters_dict if filters_dict else None,
            next_action=NextAction(
                command="aw research find", description="find across all research docs"
            )
            if filters_dict
            else NextAction(
                command="aw research new", description="create a new research doc"
            ),
        )
        return 0
    for e in results:
        print(f"{e.id6}\t{e.status}\t{e.path}\t{e.summary}")
    return 0


def run_pending(args: argparse.Namespace) -> int:
    """`aw research pending`: list the UNRUN research prompts (IPD h40usm E-01).

    Uses the structural unrun derivation (E-01 of child 01) over the manifest - a set whose NN=00
    research-prompt has no NN>=01 sibling. Human output is one ``id6<TAB>path<TAB>summary`` line per
    prompt; ``--agent`` output is the same tab-separated shape (no prose) for machine consumption.
    """

    _repo_root, research_root = _roots(args)
    entries, _drift = _scan_docs(research_root, repo_root=_repo_root)
    unrun = derive_unrun_prompts(entries)
    if getattr(args, "agent", False):
        for e in unrun:
            print(f"{e.id6}\t{e.path}\t{e.summary}")
        return 0
    if not unrun:
        from agent_workflows.term import Term
        from agent_workflows.result_types import NextAction

        Term().empty_result(
            summary="no unrun research prompts",
            next_action=NextAction(
                command="aw research find",
                description="query all research docs",
            ),
        )
        return 0
    for e in unrun:
        print(f"{e.id6}\t{e.path}\t{e.summary}")
    return 0
