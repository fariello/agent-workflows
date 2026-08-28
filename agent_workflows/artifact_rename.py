"""Universal artifact rename engine for all canonical repository artifact types.

Implements the noun-verb `aw rename <type> <selector> [--slug <new-slug>] [--set <set-id>] [--order <NN>] [--apply]`
for backlog, specs, prompts, walkthroughs, roadmaps, and releases (plus plans/research via unified dispatch).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows.plans_refs import (
    MutationResult,
)  # shared self-commit result type (jgcm68)
from agent_workflows import artifact_naming as _naming
from agent_workflows import artifact_refs as _refs
from agent_workflows import record_history as _rh
from agent_workflows import selectors
from agent_workflows.project_context import resolve_verb_repo_root

# Filename-grammar regexes are defined ONCE in the naming authority (IPD o6b8l3); re-exported here.
# The rename builder uses the PERMISSIVE uniform form (open facet) so a pre-existing name with an
# arbitrary facet still renames (byte-for-byte behavior preservation, pinned by the golden suite).
_UNIFORM_RE = _naming._UNIFORM_RE
_LEGACY_TIMESTAMP_RE = _naming._LEGACY_TIMESTAMP_RE
_WALKTHROUGH_DATED_RE = _naming._WALKTHROUGH_DATED_RE
_WALKTHROUGH_BARE_RE = _naming._WALKTHROUGH_BARE_RE
_DATED_SLUG_FACET_RE = _naming._DATED_SLUG_FACET_RE

_SET_LINE_RE = re.compile(r"(?m)^- Set:\s*(.+?)\s*$")
_ORDER_LINE_RE = re.compile(r"(?m)^- Order:\s*(\d+)\s*$")


# RefEdit is defined ONCE in the unified reference library (IPD 3cmnfc); re-export it so this
# module's API (`RefEdit(file, kind, old, new, hits)`) is unchanged.
RefEdit = _refs.RefEdit


def _resolve_repo_root(args: argparse.Namespace) -> Path:
    return resolve_verb_repo_root(getattr(args, "dir", None))


def _rel_to_repo(path: Path, repo_root: Path) -> str:
    """Repo-relative POSIX string for ``path`` (falls back to the raw posix path)."""
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _dedup(items: List[str]) -> Tuple[str, ...]:
    """Order-stable de-duplication of the touched-path list."""
    seen: dict = {}
    for it in items:
        seen.setdefault(it, None)
    return tuple(seen.keys())


def _index_paths_for(artifact_type: str, repo_root: Path) -> Tuple[str, ...]:
    """Repo-relative INDEX.json/INDEX.md for an indexed artifact type (jgcm68 self-commit paths)."""
    out: List[str] = []
    if artifact_type == "plans":
        from agent_workflows import plans_index as _pidx

        _repo, base = _pidx._dirs(argparse.Namespace(dir=str(repo_root)))
        names = (_pidx.INDEX_JSON, _pidx.INDEX_MD)
    elif artifact_type == "research":
        from agent_workflows import research_index as _ridx

        _repo, base = _ridx._roots(argparse.Namespace(dir=str(repo_root)))
        names = (_ridx.INDEX_JSON, _ridx.INDEX_MD)
    else:
        return ()
    for name in names:
        p = base / name
        if p.exists():
            out.append(_rel_to_repo(p, repo_root))
    return tuple(out)


def find_target_record(
    repo_root: Path, artifact_type: str, selector: str
) -> Optional[Path]:
    """Resolve a selector (path, id6, setid, or substring) to an existing artifact path."""
    if not selector:
        return None
    # 1. Direct path check
    candidate = Path(selector)
    if candidate.is_file():
        return candidate.resolve()
    candidate_rel = repo_root / selector
    if candidate_rel.is_file():
        return candidate_rel.resolve()

    # 2. Unified resolver (IPD laykok E-03): the full vocabulary (path/id6/setid/status/stem/
    # substring). find_target_record returns a SINGLE path (first, deterministic), preserving its
    # historical single-target contract; the kind-aware ambiguity policy for the MUTATING verbs is
    # applied by their run_* engines via resolve() directly (E-07).
    res = selectors.resolve(repo_root, artifact_type, selector)
    if res.paths:
        return res.paths[0].resolve()
    return None


def compute_target_name(
    src_name: str,
    artifact_type: str,
    new_slug: Optional[str] = None,
    new_set: Optional[str] = None,
    new_order: Optional[int] = None,
    to_id6: bool = False,
    mint_id6: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Compute the new filename given the existing name and mutation arguments.

    Returns (new_name, error_message).

    ``to_id6`` (IPD ha55fi E-04): the id6-minting conversion mode. When set and ``src_name`` is a
    legacy ``YYYYMMDD-HHMM-NN-<slug>[.<facet>].md`` timestamp name, the returned name is the uniform
    id6-clustered form ``YYYYMMDD-<mint_id6>-NN-<mint_id6>-<slug>[.<facet>].md`` (a standalone
    artifact uses its own id6 as the setid). ``mint_id6`` MUST be supplied by the caller
    (``run_rename_generic`` mints it, or reuses an existing ``- Id:``); this pure function does not
    read the filesystem. An already-clustered name in ``--to-id6`` mode is a no-op rename target
    (it already carries an id6), so it flows through the uniform branch unchanged.
    """
    if not to_id6 and not new_slug and new_set is None and new_order is None:
        return None, "at least one of --slug, --set, or --order is required to rename"

    # IPD ha55fi E-04: in id6-minting mode a legacy timestamp name (YYYYMMDD-HHMM-NN-...) is the
    # WHOLE POINT of the conversion, and its HHMM (4 digits) unambiguously distinguishes it from the
    # uniform form (whose set segment can otherwise capture a 4-digit token). So try the legacy
    # timestamp shape FIRST when --to-id6 is set, then fall through to the uniform (already-clustered)
    # branch below for an idempotent no-op on an id6-bearing name.
    if to_id6:
        m_ts_first = _LEGACY_TIMESTAMP_RE.match(src_name)
        if m_ts_first:
            if not mint_id6:
                return None, "internal: --to-id6 conversion requires a minted id6"
            date_str = m_ts_first.group("date")
            slug = _core.kebab(new_slug) if new_slug else m_ts_first.group("slug")
            artifact_type_facet = _naming.TYPE_FACET.get(artifact_type)
            try:
                return (
                    _naming.build_clustered_name(
                        date=date_str,
                        set_id=mint_id6,
                        order=1,
                        id6=mint_id6,
                        slug=slug,
                        artifact_type=artifact_type_facet,
                    ),
                    None,
                )
            except ValueError as exc:
                return None, str(exc)

    m_uni = _UNIFORM_RE.match(src_name)
    if m_uni:
        date_str = m_uni.group("date")
        set_id = _core.kebab(new_set) if new_set else m_uni.group("set")
        order_num = new_order if new_order is not None else int(m_uni.group("nn"))
        id6 = m_uni.group("id6")
        slug = _core.kebab(new_slug) if new_slug else m_uni.group("slug")
        facet = m_uni.group("facet")
        ext = f".{facet}.md" if facet else ".md"
        return f"{date_str}-{set_id}-{order_num:02d}-{id6}-{slug}{ext}", None

    m_ts = _LEGACY_TIMESTAMP_RE.match(src_name)
    if m_ts:
        date_str = m_ts.group("date")
        hhmm = m_ts.group("hhmm")
        order_num = new_order if new_order is not None else int(m_ts.group("nn"))
        slug = _core.kebab(new_slug) if new_slug else m_ts.group("slug")
        facet = m_ts.group("facet")
        ext = f".{facet}.md" if facet else ".md"
        # NOTE: a legacy timestamp name in --to-id6 mode is handled by the earlier to_id6 block
        # (its HHMM disambiguates it from the uniform form); here to_id6 is necessarily False.
        return f"{date_str}-{hhmm}-{order_num:02d}-{slug}{ext}", None

    m_wt_d = _WALKTHROUGH_DATED_RE.match(src_name)
    if m_wt_d:
        date_str = m_wt_d.group("date")
        slug = _core.kebab(new_slug) if new_slug else m_wt_d.group("slug")
        return f"{date_str}-{slug}-walkthrough.md", None

    m_wt_b = _WALKTHROUGH_BARE_RE.match(src_name)
    if m_wt_b:
        slug = _core.kebab(new_slug) if new_slug else m_wt_b.group("slug")
        return f"{slug}-walkthrough.md", None

    m_dated = _DATED_SLUG_FACET_RE.match(src_name)
    if m_dated:
        date_str = m_dated.group("date")
        slug = _core.kebab(new_slug) if new_slug else m_dated.group("slug")
        facet = m_dated.group("facet")
        ext = f".{facet}.md" if facet else ".md"
        return f"{date_str}-{slug}{ext}", None

    # Free-form filename fallback
    if new_slug:
        clean_slug = _core.kebab(new_slug)
        if src_name.endswith(".md"):
            return f"{clean_slug}.md", None
        return f"{clean_slug}", None

    return None, f"unable to parse and compute new name for {src_name}"


def plan_reference_rewrites(
    repo_root: Path, old_name: str, new_name: str
) -> List[RefEdit]:
    """Find all inbound references to rewrite (IPD 3cmnfc E-04: delegates to the ONE unified matcher).

    Full name + whole stem (covers range shorthand) + legacy prefix, map-driven and hyphen-
    boundaried; a bare id6/setid is never touched. Signature kept (single old->new) by wrapping it
    into a one-entry name_map.
    """

    return _refs.plan_reference_rewrites(repo_root, {old_name: new_name})


def apply_reference_rewrites(edits: List[RefEdit]) -> None:
    """Apply reference rewrites (unified applier: full-name first, then hyphen-boundaried stem)."""

    _refs.apply_reference_rewrites(edits, prefix=".aw-ref-")


_ID_LINE_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_STATUS_LINE_RE = re.compile(r"(?m)^- Status:\s*.+?\s*$")
_DATE_LINE_RE = re.compile(r"(?m)^- Date:\s*.+?\s*$")


def _update_frontmatter_metadata(
    file_path: Path,
    set_id: Optional[str] = None,
    order: Optional[int] = None,
    id6: Optional[str] = None,
) -> None:
    """Update Set/Order (and, IPD ha55fi E-04, Id) metadata in the file frontmatter if present.

    ``id6``: when supplied and the file has NO ``- Id:`` bullet, inject one into the metadata block
    (after ``- Status:``, else ``- Date:``, else after the H1). When the file already carries an
    ``- Id:`` this is a no-op for that field (the existing id6 is reused, never re-minted); this is
    the idempotence property (V-04/V-05). Set/Order updates are unchanged.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return

    updated = False
    if set_id is not None and _SET_LINE_RE.search(text):
        text = _SET_LINE_RE.sub(f"- Set: {set_id}", text)
        updated = True

    if order is not None and _ORDER_LINE_RE.search(text):
        text = _ORDER_LINE_RE.sub(f"- Order: {order}", text)
        updated = True

    if id6 is not None and not _ID_LINE_RE.search(text):
        lines = text.split("\n")
        insert_at: Optional[int] = None
        for i, line in enumerate(lines):
            if _STATUS_LINE_RE.match(line):
                insert_at = i + 1
                break
        if insert_at is None:
            for i, line in enumerate(lines):
                if _DATE_LINE_RE.match(line):
                    insert_at = i + 1
                    break
        if insert_at is None:
            for i, line in enumerate(lines):
                if line.startswith("# "):
                    insert_at = i + 1
                    break
        if insert_at is None:
            insert_at = 0
        lines.insert(insert_at, f"- Id: {id6}")
        text = "\n".join(lines)
        updated = True

    if updated:
        _core.atomic_write(file_path, text, prefix=".aw-meta-")


def _read_existing_id6(file_path: Path) -> Optional[str]:
    """Return the id6 in a file's `- Id:` metadata, or None (IPD ha55fi E-04 idempotence read)."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = _ID_LINE_RE.search(text)
    return m.group(1) if m else None


def find_unrewritable_path_citations(
    repo_root: Path, old_name: str, src_dir: Path
) -> List[Tuple[str, str]]:
    """Find full-PATH citations of ``old_name`` whose directory differs from the file's real dir.

    IPD ha55fi E-05: a ``--to-id6`` rename keeps the file in ``src_dir`` and only changes the
    FILENAME, so the standard full-name substitution correctly rewrites a full-path citation whose
    directory equals ``src_dir``. But a citation that names a DIFFERENT directory (e.g. a stale or
    hand-typed path) cannot be safely auto-rewritten by a filename-only substitution: replacing the
    filename would leave a still-wrong directory. These are surfaced fail-loud so an operator fixes
    them by hand. Returns a list of (repo-relative-file, cited-path) pairs.
    """
    try:
        src_dir_rel = src_dir.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        src_dir_rel = src_dir.as_posix()
    # A path-citation is a run of path chars ending in `/<old_name>`.
    path_re = re.compile(r"[A-Za-z0-9._/\-]*/" + re.escape(old_name))
    out: List[Tuple[str, str]] = []
    for f in _core.iter_scan_files(repo_root):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in path_re.finditer(text):
            cited = m.group(0)
            cited_dir = cited[: -(len(old_name) + 1)]  # strip `/<old_name>`
            # Normalize a leading `./` and compare the directory tail against the real dir.
            norm = cited_dir.lstrip("./")
            if (
                norm
                and not src_dir_rel.endswith(norm)
                and not norm.endswith(src_dir_rel)
            ):
                try:
                    rel_f = f.relative_to(repo_root).as_posix()
                except ValueError:
                    rel_f = str(f)
                out.append((rel_f, cited))
    return out


def _existing_type_id6s(repo_root: Path, artifact_type: str) -> set:
    """Every id6 already used by any artifact of ``artifact_type`` (mint collision set, E-04).

    Scans that type's on-disk names for a clustered id6 AND each file's ``- Id:`` metadata bullet,
    so a freshly minted id6 never collides with an existing standalone/legacy-with-Id artifact.
    """
    ids: set = set()
    try:
        for p, text in selectors._iter_files(repo_root, artifact_type):
            m_name = _UNIFORM_RE.match(p.name)
            if m_name:
                ids.add(m_name.group("id6"))
            m_id = _ID_LINE_RE.search(text)
            if m_id:
                ids.add(m_id.group(1))
    except Exception:
        pass
    return ids


def _update_or_inject_set_metadata(
    file_path: Path, set_id: Optional[str] = None, order: Optional[int] = None
) -> None:
    """Update or inject Set and Order metadata in the file frontmatter."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return

    lines = text.splitlines()
    updated = False
    is_fenced_yaml = bool(lines and lines[0].strip() == "---")

    if is_fenced_yaml:
        new_lines = []
        set_done = False
        in_fm = True
        for line in lines:
            if in_fm and line.strip() == "---" and new_lines:
                in_fm = False
                if set_id is not None and not set_done:
                    new_lines.append(f"set: {set_id}")
                    if order is not None:
                        new_lines.append(f"order: {order}")
                    set_done = True
                    updated = True
                new_lines.append(line)
            elif in_fm and re.match(r"^set:\s*", line, re.IGNORECASE):
                if set_id is not None:
                    new_lines.append(f"set: {set_id}")
                    set_done = True
                    updated = True
                else:
                    new_lines.append(line)
            elif (
                in_fm
                and order is not None
                and re.match(r"^order:\s*", line, re.IGNORECASE)
            ):
                new_lines.append(f"order: {order}")
                updated = True
            else:
                new_lines.append(line)
        lines = new_lines
    else:
        # Markdown bullet frontmatter
        set_done = False
        new_lines = []
        in_fm = True
        for line in lines:
            if in_fm and line.startswith("## "):
                in_fm = False
                if set_id is not None and not set_done:
                    new_lines.append(f"- Set: {set_id}")
                    if order is not None:
                        new_lines.append(f"- Order: {order}")
                    set_done = True
                    updated = True
            if in_fm and _SET_LINE_RE.match(line):
                if set_id is not None:
                    new_lines.append(f"- Set: {set_id}")
                    set_done = True
                    updated = True
                else:
                    new_lines.append(line)
            elif in_fm and order is not None and _ORDER_LINE_RE.match(line):
                new_lines.append(f"- Order: {order}")
                updated = True
            else:
                new_lines.append(line)

        if set_id is not None and not set_done:
            inserted = False
            res = []
            for line in new_lines:
                res.append(line)
                if not inserted and (
                    line.startswith("# ") or line.startswith("- Date:")
                ):
                    res.append(f"- Set: {set_id}")
                    if order is not None:
                        res.append(f"- Order: {order}")
                    inserted = True
                    updated = True
            if not inserted:
                res.insert(0, f"- Set: {set_id}")
                if order is not None:
                    res.insert(1, f"- Order: {order}")
                updated = True
            lines = res
        else:
            lines = new_lines

    if updated:
        _core.atomic_write(
            file_path, "\n".join(lines).rstrip() + "\n", prefix=".aw-meta-"
        )


def run_rename_generic(
    args: argparse.Namespace, artifact_type: str
) -> "MutationResult":
    """Universal rename execution engine for an artifact type.

    selfcommit jgcm68 E-03: RETURNS a ``MutationResult`` (rc + touched/index paths); performs NO
    commit itself. The caller (``_run_noun_verb`` dispatch) places the self-commit offer ONCE."""
    repo_root = _resolve_repo_root(args)
    selector = getattr(args, "id", None) or getattr(args, "selector", None)
    if isinstance(selector, list):
        selector = selector[0] if selector else None

    if not selector:
        print("error: at least one <id6>, <setid>, or <path> is required")
        return MutationResult(2)

    # IPD laykok E-07: apply the kind-aware ambiguity policy through the unified resolver. `rename`
    # mutates ONE file, so a UNIQUE-id collision or an unforced substring multi-match REFUSES with
    # the candidate list; a setid selecting several is unusual for rename and, absent --force, also
    # refuses rather than silently renaming an arbitrary member.
    paths, amb_err = selectors.resolve_for_mutation(
        repo_root, artifact_type, selector, force=bool(getattr(args, "force", False))
    )
    if amb_err:
        print(f"error: {amb_err}")
        return MutationResult(2)
    if len(paths) > 1 and not bool(getattr(args, "force", False)):
        cand = "\n  ".join(str(p) for p in paths)
        print(
            f"error: selector '{selector}' matched multiple files; rename targets one "
            f"(pass --force to rename the first, or use a unique id6):\n  {cand}"
        )
        return MutationResult(2)
    src = paths[0].resolve()
    if not src.exists():
        print(f"error: no {artifact_type} artifact matched '{selector}'")
        return MutationResult(2)

    new_slug = getattr(args, "slug", None)
    new_set = getattr(args, "set", None)
    new_order = getattr(args, "order", None)
    to_id6 = bool(getattr(args, "to_id6", False))

    # IPD ha55fi E-04: id6-minting conversion mode. Reuse an existing `- Id:` (idempotent, never
    # re-mint) else mint a fresh id6 collision-checked against the existing spec id6 set.
    minted_id6: Optional[str] = None
    inject_id6: Optional[str] = None
    if to_id6:
        existing = _read_existing_id6(src)
        if existing:
            minted_id6 = existing  # reuse; no metadata write needed (already present)
        else:
            minted_id6 = _core.generate_id6(
                _existing_type_id6s(repo_root, artifact_type)
            )
            inject_id6 = (
                minted_id6  # must be written into the file during the transaction
            )

    new_name, err = compute_target_name(
        src.name,
        artifact_type,
        new_slug=new_slug,
        new_set=new_set,
        new_order=new_order,
        to_id6=to_id6,
        mint_id6=minted_id6,
    )
    if err:
        print(f"error: {err}")
        return MutationResult(2)

    assert new_name is not None
    dst = src.parent / new_name

    apply = bool(getattr(args, "apply", False))
    update_refs = not bool(getattr(args, "no_refs", False))

    if dst.resolve() != src.resolve() and dst.exists():
        print(f"error: destination file already exists: {dst.name}")
        return MutationResult(2)

    ref_edits = (
        plan_reference_rewrites(repo_root, src.name, new_name) if update_refs else []
    )

    # IPD ha55fi E-05: surface full-path citations that a filename-only rewrite cannot safely fix.
    unrewritable: List[Tuple[str, str]] = []
    if to_id6 and update_refs and src.name != new_name:
        unrewritable = find_unrewritable_path_citations(repo_root, src.name, src.parent)

    if not apply:
        print(
            f"--- would rename {src.relative_to(repo_root).as_posix()} -> {new_name} ---"
        )
        if to_id6 and inject_id6:
            print(f"--- would inject '- Id: {inject_id6}' into {new_name} ---")
        elif to_id6 and minted_id6:
            print(f"--- reuses existing '- Id: {minted_id6}' (no re-mint) ---")
        if update_refs:
            for e in ref_edits:
                try:
                    rel_f = e.file.relative_to(repo_root).as_posix()
                except ValueError:
                    rel_f = str(e.file)
                print(
                    f"--- would rewrite {e.hits}x '{e.old}' -> '{e.new}' in {rel_f} ---"
                )
        for rel_f, cited in unrewritable:
            print(
                f"--- WARNING: full-path citation '{cited}' in {rel_f} names a different "
                f"directory and cannot be auto-rewritten; fix it by hand ---"
            )
        return MutationResult(0)

    if unrewritable:
        # Fail loud on --apply so the operator fixes the un-auto-rewritable citation first.
        for rel_f, cited in unrewritable:
            print(
                f"error: full-path citation '{cited}' in {rel_f} names a different directory "
                f"than the file; cannot auto-rewrite. Fix it by hand, then retry."
            )
        return MutationResult(2)

    # Apply changes
    touched: List[str] = []
    if src.resolve() != dst.resolve():
        src_rel = src.relative_to(repo_root).as_posix()
        dst_rel = dst.relative_to(repo_root).as_posix()
        _core.git_mv(repo_root, src_rel, dst_rel)
        print(f"renamed {src_rel} -> {dst_rel}")
        # IPD 52zgqr: additive, failure-isolated rename ledger record (never breaks the rename).
        _rh.record_rename(
            repo_root,
            tree=artifact_type,
            verb="rename",
            actor="aw",
            from_name=src.name,
            to_name=dst.name,
        )
        touched.append(src_rel)
        touched.append(dst_rel)
    else:
        touched.append(_rel_to_repo(dst, repo_root))

    if new_set is not None or new_order is not None or inject_id6 is not None:
        # IPD ha55fi E-04: same atomic transaction writes Set/Order AND injects the minted `- Id:`.
        _update_frontmatter_metadata(
            dst,
            set_id=_core.kebab(new_set) if new_set else None,
            order=new_order,
            id6=inject_id6,
        )
        if inject_id6 is not None:
            print(f"injected '- Id: {inject_id6}' into {dst.name}")
        touched.append(_rel_to_repo(dst, repo_root))

    if update_refs and ref_edits:
        apply_reference_rewrites(ref_edits)
        for e in ref_edits:
            try:
                rel_f = e.file.relative_to(repo_root).as_posix()
            except ValueError:
                rel_f = str(e.file)
            print(f"rewrote {e.hits}x '{e.old}' -> '{e.new}' in {rel_f}")
            touched.append(rel_f)

    # Auto-index if supported
    index_paths: Tuple[str, ...] = ()
    if artifact_type in {"plans", "research"}:
        try:
            if artifact_type == "plans":
                from agent_workflows import plans_index as _pidx

                _pidx.run_index(
                    argparse.Namespace(
                        dir=str(repo_root),
                        check=False,
                        as_agent=False,
                        json=False,
                        no_color=True,
                        limit=None,
                        quiet=True,
                    )
                )
            elif artifact_type == "research":
                from agent_workflows import research_index as _ridx

                _ridx.run_index(
                    argparse.Namespace(
                        dir=str(repo_root),
                        check=False,
                        agent=False,
                        limit=None,
                        quiet=True,
                    )
                )
            index_paths = _index_paths_for(artifact_type, repo_root)
        except Exception:
            pass

    return MutationResult(0, _dedup(touched), index_paths)


def run_group_generic(args: argparse.Namespace, artifact_type: str) -> "MutationResult":
    """Universal set assignment / group execution engine for an artifact type."""
    repo_root = _resolve_repo_root(args)
    raw_selectors = (
        getattr(args, "ids", None)
        or getattr(args, "selector", None)
        or [getattr(args, "id", None)]
    )
    if isinstance(raw_selectors, str):
        raw_selectors = [raw_selectors]
    selectors_list = [s.strip() for s in (raw_selectors or []) if s and s.strip()]

    if not selectors_list:
        print("error: at least one <id6>, <setid>, or <path> is required")
        return MutationResult(2)

    new_set = getattr(args, "set", None)
    if not new_set or not new_set.strip():
        print("error: --set <set-id> is required")
        return MutationResult(2)

    set_k = _core.kebab(new_set)
    start_order = getattr(args, "order", None)
    apply = bool(getattr(args, "apply", False))
    update_refs = not bool(getattr(args, "no_refs", False))
    rename_files = bool(getattr(args, "rename", False))

    targets: List[Tuple[Path, Path, Optional[int]]] = []
    all_edits: List[RefEdit] = []

    for i, sel in enumerate(selectors_list):
        src = find_target_record(repo_root, artifact_type, sel)
        if src is None or not src.exists():
            print(f"error: no {artifact_type} artifact matched '{sel}'")
            return MutationResult(2)
        order_val = (start_order + i) if start_order is not None else None
        if rename_files:
            new_name, err = compute_target_name(
                src.name,
                artifact_type,
                new_set=set_k,
                new_order=order_val,
            )
            if err:
                new_name = src.name
            assert new_name is not None
            dst = src.parent / new_name
        else:
            dst = src

        if dst.resolve() != src.resolve() and dst.exists():
            print(f"error: destination file already exists: {dst.name}")
            return MutationResult(2)

        targets.append((src, dst, order_val))
        if update_refs and src.name != dst.name:
            all_edits.extend(plan_reference_rewrites(repo_root, src.name, dst.name))

    if not apply:
        for src, dst, _order_val in targets:
            src_rel = src.relative_to(repo_root).as_posix()
            if src.resolve() != dst.resolve():
                print(f"--- would rename {src_rel} -> {dst.name} ---")
            print(f"--- would set metadata Set: {set_k} in {src_rel} ---")
        if update_refs:
            for e in all_edits:
                try:
                    rel_f = e.file.relative_to(repo_root).as_posix()
                except ValueError:
                    rel_f = str(e.file)
                print(
                    f"--- would rewrite {e.hits}x '{e.old}' -> '{e.new}' in {rel_f} ---"
                )
        return MutationResult(0)

    # Apply changes
    touched: List[str] = []
    for src, dst, order_val in targets:
        if src.resolve() != dst.resolve():
            src_rel = src.relative_to(repo_root).as_posix()
            dst_rel = dst.relative_to(repo_root).as_posix()
            _core.git_mv(repo_root, src_rel, dst_rel)
            print(f"renamed {src_rel} -> {dst_rel}")
            # IPD 52zgqr: additive, failure-isolated rename ledger record.
            _rh.record_rename(
                repo_root,
                tree=artifact_type,
                verb="group",
                actor="aw",
                from_name=src.name,
                to_name=dst.name,
            )
            touched.append(src_rel)
            touched.append(dst_rel)
        _update_or_inject_set_metadata(dst, set_id=set_k, order=order_val)
        dst_rel = dst.relative_to(repo_root).as_posix()
        print(f"set metadata Set: {set_k} in {dst_rel}")
        touched.append(dst_rel)

    if update_refs and all_edits:
        apply_reference_rewrites(all_edits)
        for e in all_edits:
            try:
                rel_f = e.file.relative_to(repo_root).as_posix()
            except ValueError:
                rel_f = str(e.file)
            print(f"rewrote {e.hits}x '{e.old}' -> '{e.new}' in {rel_f}")
            touched.append(rel_f)

    # Auto-index if indexed type
    index_paths: Tuple[str, ...] = ()
    if artifact_type in {"plans", "research"}:
        try:
            if artifact_type == "plans":
                from agent_workflows import plans_index as _pidx

                _pidx.run_index(
                    argparse.Namespace(
                        dir=str(repo_root),
                        check=False,
                        as_agent=False,
                        json=False,
                        no_color=True,
                        limit=None,
                        quiet=True,
                    )
                )
            elif artifact_type == "research":
                from agent_workflows import research_index as _ridx

                _ridx.run_index(
                    argparse.Namespace(
                        dir=str(repo_root),
                        check=False,
                        agent=False,
                        limit=None,
                        quiet=True,
                    )
                )
            index_paths = _index_paths_for(artifact_type, repo_root)
        except Exception:
            pass

    return MutationResult(0, _dedup(touched), index_paths)


def run_rename_backlog(args: argparse.Namespace) -> "MutationResult":
    return run_rename_generic(args, "backlog")


def run_rename_specs(args: argparse.Namespace) -> "MutationResult":
    return run_rename_generic(args, "specs")


def run_rename_prompts(args: argparse.Namespace) -> "MutationResult":
    return run_rename_generic(args, "prompts")


def run_rename_walkthroughs(args: argparse.Namespace) -> "MutationResult":
    return run_rename_generic(args, "walkthroughs")


def run_rename_roadmaps(args: argparse.Namespace) -> "MutationResult":
    return run_rename_generic(args, "roadmaps")


def run_rename_releases(args: argparse.Namespace) -> "MutationResult":
    return run_rename_generic(args, "releases")


def run_rename_other(args: argparse.Namespace) -> "MutationResult":
    return run_rename_generic(args, "other")


def run_group_backlog(args: argparse.Namespace) -> "MutationResult":
    return run_group_generic(args, "backlog")


def run_group_specs(args: argparse.Namespace) -> "MutationResult":
    return run_group_generic(args, "specs")


def run_group_prompts(args: argparse.Namespace) -> "MutationResult":
    return run_group_generic(args, "prompts")


def run_group_walkthroughs(args: argparse.Namespace) -> "MutationResult":
    return run_group_generic(args, "walkthroughs")


def run_group_roadmaps(args: argparse.Namespace) -> "MutationResult":
    return run_group_generic(args, "roadmaps")


def run_group_releases(args: argparse.Namespace) -> "MutationResult":
    return run_group_generic(args, "releases")


def run_group_other(args: argparse.Namespace) -> "MutationResult":
    return run_group_generic(args, "other")
