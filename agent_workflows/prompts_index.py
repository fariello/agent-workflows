"""Prompts scan + drift check (Plan dx0u4s).

``scan_prompts`` lists every bucketed prompt; ``check_drift`` reports name-metadata mismatches and is
reached through ``aw check prompts --all`` and the ``aw index prompts --check`` alias. No INDEX file is
written: the SQLite metadata cache replaced the generated ``INDEX.{json,md}`` views (spec 4sd62s 4.5).

Consumes the shared core (`artifact_core`) and `artifact_naming`.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_meta as _am
from agent_workflows import artifact_naming as _naming

_EXCLUDE_NAMES = {"INDEX.json", "INDEX.md", "README.md"}

# The legacy staged staging name: YYYYMMDD-HHMM-NN-<slug>.prompt.md
# The legacy staged name YYYYMMDD-HHMM-NN-<slug>.prompt.md is read by THE ONE file-name library.
_STAGED_NAME_RE = _naming._LEGACY_TIMESTAMP_RE


class PromptEntry(NamedTuple):
    """One indexed prompt (derived from its disposition dir, filename, and metadata comment)."""

    id6: Optional[str]
    path: str  # posix, relative to prompts_dir
    disposition: str  # pending/executed/superseded/not-executed/reusable
    date: str
    set_id: Optional[str]
    order: Optional[int]
    status: Optional[str]
    kind: Optional[str]
    slug: Optional[str] = None


def _meta_context_for_prompts_dir(
    prompts_dir: Path,
) -> Tuple[Any, Path, Optional[Path]]:
    """Build an ``artifact_meta`` context covering ``prompts_dir``."""
    pdir = prompts_dir.resolve()
    repo_root: Optional[Path] = None
    for cand in (pdir, *pdir.parents):
        cparts = cand.parts
        if len(cparts) >= 4 and cparts[-3:] == (".aw", "records", "prompts"):
            repo_root = cand.parents[2]
            break
        if len(cparts) >= 3 and cparts[-2:] == (".agents", "prompts"):
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
    prompts_ancestor: Optional[Path] = None
    for cand in (pdir, *pdir.parents):
        if cand.name == "prompts":
            prompts_ancestor = cand
            break
    if prompts_ancestor is not None:
        records_root = prompts_ancestor.parent
        state_root = (
            records_root.parent / "state"
            if records_root.name == "records"
            else records_root / ".aw-state"
        )
    else:
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


def _cached_prompt_states(
    prompts_dir: Path, *, include_fields: bool = True
) -> Dict[Path, Any]:
    """Query ``artifact_meta.query(type='prompt')`` indexed by resolved path under ``prompts_dir``."""
    if not prompts_dir.is_dir():
        return {}
    pdir_res = prompts_dir.resolve()
    ctx, records_root, scan_repo = _meta_context_for_prompts_dir(pdir_res)
    with _am.scan_once(), _am.ephemeral_if_uninitialized():
        res = _am.query(
            type="prompt", project_context=ctx, include_fields=include_fields
        )
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


def _state_order(st: Any) -> Optional[int]:
    """Return non-negative integer Order from an ``artifact_meta.State``, or None."""
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


def _filename_slug(name: str) -> Optional[str]:
    """Extract the slug segment from a prompt filename."""
    m_leg = _STAGED_NAME_RE.match(name)
    if m_leg:
        return m_leg.group("slug")
    m_attr = _naming.parse_attributed(name)
    if m_attr:
        return m_attr.slug
    m_clust = _naming.parse_clustered(name)
    if m_clust:
        return m_clust.group("slug")
    return None


def _scan_prompts_with_states(
    prompts_dir: Path,
) -> Tuple[List[PromptEntry], List[_core.Drift], Dict[Path, Any]]:
    """Scan every prompt under ``prompts_dir`` via ``artifact_meta.query``."""
    entries: List[PromptEntry] = []
    drift: List[_core.Drift] = []
    if not prompts_dir.is_dir():
        return entries, drift, {}
    ignored_dirs = _core.get_ignored_dirs(prompts_dir)
    states = _cached_prompt_states(prompts_dir, include_fields=True)
    for p in sorted(prompts_dir.rglob("*.md")):
        if p.name in _EXCLUDE_NAMES or _core.is_ignored_path(
            p, prompts_dir, ignored_dirs
        ):
            continue
        rel = p.relative_to(prompts_dir).as_posix()
        disposition = rel.split("/", 1)[0]
        st = states.get(p.resolve())
        if st is None:
            st = _am.read_text(p.read_text(encoding="utf-8"), record_type="prompt")
            id6 = st.id6 if (st.id6 and _core.is_valid_id6(st.id6)) else None
            set_id = st.set_id or None
            order = _state_order(st)
            date = str(
                st.created_day
                or st.fields.get("created_day")
                or st.fields.get("created")
                or st.fields.get("date")
                or st.filename_date
                or ""
            )
            raw_kind = st.fields.get("prompt_kind") or st.fields.get("plan_role")
            kind = str(raw_kind) if raw_kind else None
            status = str(st.status) if st.status else disposition
            slug = (
                str(st.fields.get("slug"))
                if st.fields.get("slug")
                else _filename_slug(p.name)
            )
        else:
            id6 = None if st.id_derived else (st.id6 or None)
            set_id = st.set_id or None
            order = _state_order(st)
            date = str(
                st.created_day
                or st.fields.get("created_day")
                or (st.created_at[:10] if st.created_at else None)
                or st.filename_date
                or ""
            )
            raw_kind = st.fields.get("prompt_kind")
            kind = str(raw_kind) if raw_kind else None
            status = str(st.status) if st.status else disposition
            slug = _filename_slug(p.name)

        entries.append(
            PromptEntry(
                id6=id6,
                path=rel,
                disposition=disposition,
                date=date,
                set_id=set_id,
                order=order,
                status=status,
                kind=kind,
                slug=slug,
            )
        )
    return entries, drift, states


def scan_prompts(prompts_dir: Path) -> Tuple[List[PromptEntry], List[_core.Drift]]:
    """Scan every prompt under ``prompts_dir`` via ``artifact_meta.query``; return (entries, drift)."""
    entries, drift, _states = _scan_prompts_with_states(prompts_dir)
    return entries, drift


def check_drift(repo_root: Path, prompts_dir: Path) -> List[_core.Drift]:
    entries, drift, states = _scan_prompts_with_states(prompts_dir)

    # Drift: name-vs-metadata mismatch on a clustered name (read via artifact_meta)
    for e in entries:
        base = Path(e.path).name
        m = _naming.parse_clustered(base)
        if not m or re.fullmatch(r"\d{4}", m.group("set")):
            continue
        st = states.get((prompts_dir / e.path).resolve())
        if st is None:
            continue
        meta_id = None if st.id_derived else (st.id6 or None)
        if meta_id and m.group("id6") != meta_id:
            drift.append(
                _core.Drift(
                    e.path,
                    "name-metadata-mismatch",
                    f"name id {m.group('id6')} != metadata Id {meta_id}",
                )
            )
        meta_set = (
            st.set_id
            if getattr(st, "created_at", None) is not None
            else getattr(st, "legacy_raw_set", None)
        )
        if meta_set and m.group("set") != meta_set:
            drift.append(
                _core.Drift(
                    e.path,
                    "name-metadata-mismatch",
                    f"name set {m.group('set')} != metadata Set {meta_set}",
                )
            )

    return drift


def _dirs(args: argparse.Namespace) -> Tuple[Path, Path]:
    from agent_workflows.project_context import resolve_verb_repo_root
    from agent_workflows import prompts as _prompts

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    prompts_dir = _prompts.prompts_root(repo_root)
    return repo_root, prompts_dir
