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
from agent_workflows import artifact_meta as _meta
from agent_workflows.plans_refs import (
    MutationDiagnostic,
    MutationRefEdit,
    MutationResult,
    MutationTarget,
)  # shared self-commit result type (jgcm68)
from agent_workflows import artifact_naming as _naming
from agent_workflows import artifact_refs as _refs
from agent_workflows import project_context as _proj_ctx
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
_ORDER_LINE_RE = re.compile(r"(?m)^- Order:\s*(-?\d+)\s*$")


# RefEdit is defined ONCE in the unified reference library (IPD 3cmnfc); re-export it so this
# module's API (`RefEdit(file, kind, old, new, hits)`) is unchanged.
RefEdit = _refs.RefEdit


def _resolve_repo_root(args: argparse.Namespace) -> Path:
    return resolve_verb_repo_root(getattr(args, "dir", None))


def _rel_to_repo(path: Path, repo_root: Path) -> str:
    """Repo-relative POSIX string for ``path`` (delegates to :func:`artifact_core.repo_relative_posix`)."""
    return _core.repo_relative_posix(path, repo_root)


def _dedup(items: List[str]) -> Tuple[str, ...]:
    """Order-stable de-duplication of the touched-path list."""
    seen: dict = {}
    for it in items:
        seen.setdefault(it, None)
    return tuple(seen.keys())


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

    # dl86am D1/D2: the two DATED non-clustered shapes below cannot hold a set, an order or an id6, so a
    # caller asking for any of those previously got the input name back with err None, i.e. a
    # SUCCESS that changed nothing. With `--to-id6` the target IS constructible (the same clustered
    # form the legacy-timestamp branch builds: the file's own id6 as setid, Order 01); with only
    # `--set`/`--order` and no id6 it is NOT, so that now REFUSES and says why. A slug-only rename of
    # these shapes is unchanged.
    m_dated_any = _WALKTHROUGH_DATED_RE.match(src_name) or _DATED_SLUG_FACET_RE.match(
        src_name
    )
    if m_dated_any and not _UNIFORM_RE.match(src_name):
        if to_id6:
            if not mint_id6:
                return None, "internal: --to-id6 conversion requires a minted id6"
            slug = _core.kebab(new_slug) if new_slug else m_dated_any.group("slug")
            try:
                return (
                    _naming.build_clustered_name(
                        date=m_dated_any.group("date"),
                        set_id=_core.kebab(new_set) if new_set else mint_id6,
                        order=new_order if new_order is not None else 1,
                        id6=mint_id6,
                        slug=slug,
                        artifact_type=_naming.TYPE_FACET.get(artifact_type),
                    ),
                    None,
                )
            except ValueError as exc:
                return None, str(exc)
        if new_set is not None or new_order is not None:
            return None, (
                f"{src_name} has no id6, so it cannot take a Set or Order in its name; "
                "pass --to-id6 to convert it to the clustered form"
            )

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


def plan_reference_rewrites_with_warnings(
    repo_root: Path, old_name: str, new_name: str
) -> Tuple[List[RefEdit], List[str]]:
    """Find inbound references and collect shared legacy prefix warnings (delegates to unified matcher)."""
    return _refs.plan_reference_rewrites_with_warnings(repo_root, {old_name: new_name})


def apply_reference_rewrites(edits: List[RefEdit]) -> None:
    """Apply reference rewrites (unified applier: full-name first, then hyphen-boundaried stem)."""

    _refs.apply_reference_rewrites(edits, prefix=".aw-ref-")


_ID_LINE_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_STATUS_LINE_RE = re.compile(r"(?m)^- Status:\s*.+?\s*$")
_DATE_LINE_RE = re.compile(r"(?m)^- Date:\s*.+?\s*$")


def _meta_target_for_file(
    file_path: Path,
    artifact_type: Optional[str],
    *,
    repo_root: Optional[Path] = None,
    fallback_id6: Optional[str] = None,
) -> Tuple[Path, object, str, _meta.LegacyTarget, str]:
    """Resolve repo root, legacy context, plural record type, LegacyTarget, and records-rel path."""
    rroot = (
        repo_root
        if repo_root is not None
        else (_proj_ctx.record_git_root(file_path) or _core.repo_root_of(file_path))
    )
    ctx = _meta.legacy_context(rroot)
    records_root = Path(ctx.logical_roots["records"])
    _, plural = _meta._normalize_legacy_types(artifact_type, file_path, records_root)
    target_id6 = _read_existing_id6(file_path, plural)
    if not target_id6:
        m_id = _UNIFORM_RE.match(file_path.name)
        if m_id:
            target_id6 = m_id.group("id6")
    if not target_id6:
        target_id6 = fallback_id6
    try:
        rel_path = file_path.resolve().relative_to(records_root.resolve()).as_posix()
    except ValueError:
        rel_path = file_path.name
    return (
        rroot,
        ctx,
        plural,
        _meta.LegacyTarget(file_path, plural, id6=target_id6),
        rel_path,
    )


def _rename_metadata_events(
    text: str,
    rec_type: str,
    rel_path: str,
    *,
    existing_id6: Optional[str],
    set_id: Optional[str] = None,
    order: Optional[int] = None,
    id6: Optional[str] = None,
) -> List[dict]:
    """The `artifact_meta.append` events for a rename's Set/Order update and id6 injection.

    Pure: builds events and writes nothing. Emits `op: "set"` only for fields already present in
    ``text`` (`_SET_LINE_RE` / `_ORDER_LINE_RE`, or `Set:` in the `aw-prompt` comment), and
    `op: "checkpoint"` for ``id6`` when the file declares no id6 yet (IPD ha55fi E-04).
    """
    events: List[dict] = []
    set_fields: dict = {}
    if rec_type == "prompts":
        from agent_workflows import prompts as _prompts

        if _prompts.has_metadata_comment(text):
            first_line = text.split("\n", 1)[0]
            if set_id is not None and re.search(
                r"(?:\A|\|)\s*Set:\s*[^|]+", first_line
            ):
                set_fields["set"] = str(set_id)
        else:
            if set_id is not None and _SET_LINE_RE.search(text):
                set_fields["set"] = str(set_id)
            if order is not None and _ORDER_LINE_RE.search(text):
                set_fields["order"] = int(order)
    else:
        if set_id is not None and _SET_LINE_RE.search(text):
            set_fields["set"] = str(set_id)
        if order is not None and _ORDER_LINE_RE.search(text):
            set_fields["order"] = int(order)

    if set_fields:
        events.append({"op": "set", "fields": set_fields})

    if id6 is not None and existing_id6 is None:
        cp_fields: dict = {"id": id6}
        if rec_type == "prompts" and set_id is not None:
            first_line = text.split("\n", 1)[0]
            if not re.search(r"(?:\A|\|)\s*Set:\s*[^|]+", first_line):
                cp_fields["set"] = str(set_id)
        events.append({"op": "checkpoint", "path": rel_path, "fields": cp_fields})
    return events


def _id6_write_message(
    artifact_type: Optional[str],
    id6: str,
    target_name: str,
    *,
    preview: bool,
    src: Optional[Path] = None,
) -> str:
    """The preview/apply line describing WHERE the id6 is recorded in-file (IPD `ubac5n` E-04).

    Exists so the message cannot describe a destination the writer does not use: a prompt's id6 goes
    into the single `<!-- aw-prompt: ... -->` comment, every other type gets a `- Id:` bullet. The
    NON-PROMPT wording is byte-identical to what shipped before (`would inject '- Id: x' into y` /
    `injected '- Id: x' into y`), deliberately: the spec conversion's own tests assert that literal
    text, and this plan must not change specs' behavior at all.

    A PROMPT WITH NO METADATA COMMENT IS REPORTED HONESTLY rather than claimed as a write. 6 of the 17
    measured prompts have no leading comment, and `prompts.inject_metadata_id6` deliberately refuses
    to mint one (adding a line above the body is the very purity violation this repair removes), so
    such a file keeps its id6 in the FILENAME only and the message says exactly that.
    """
    if artifact_type == "prompts":
        from agent_workflows import prompts as _prompts

        has_comment = True
        if src is not None:
            try:
                has_comment = _prompts.has_metadata_comment(
                    src.read_text(encoding="utf-8")
                )
            except OSError:
                has_comment = False
        if not has_comment:
            verb = "would record" if preview else "recorded"
            return (
                f"{verb} id6 {id6} in the FILENAME ONLY of {target_name} "
                f"(no aw-prompt metadata comment to write it into; one is NOT added, because a new "
                f"line above the prompt body would violate the prompt-purity contract)"
            )
        verb = "would write" if preview else "wrote"
        return (
            f"{verb} 'Id: {id6}' into the aw-prompt metadata comment of {target_name}"
        )
    if src is not None:
        try:
            _src_text = src.read_text(encoding="utf-8")
        except OSError:
            _src_text = ""
        if not (_STATUS_LINE_RE.search(_src_text) or _DATE_LINE_RE.search(_src_text)):
            # a88210: mirrors `run_rename_generic`'s metadata write, which writes no bullet into a
            # file that has no bullet block. The message must not claim a write that will not happen.
            verb = "would record" if preview else "recorded"
            return (
                f"{verb} id6 {id6} in the FILENAME ONLY of {target_name} (no '- Status:'/'- Date:' "
                "metadata bullets to add '- Id:' beside; one is NOT added under the heading, because "
                "that would put metadata into the document body)"
            )
    verb = "would inject" if preview else "injected"
    return f"{verb} '- Id: {id6}' into {target_name}"


def _read_existing_id6(
    file_path: Path, artifact_type: Optional[str] = None
) -> Optional[str]:
    """Return the id6 a file already declares, or None (IPD ha55fi E-04 idempotence read).

    ``artifact_type`` (IPD `ubac5n` E-04): a PROMPT declares its id6 inside the single
    `<!-- aw-prompt: ... -->` comment rather than in a `- Id:` bullet, so the reader must match the
    writer or a `--to-id6` re-run would re-mint over an identity the file already holds.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if artifact_type == "prompts":
        from agent_workflows import prompts as _prompts

        return _prompts.read_metadata_id6(text)
    m = _ID_LINE_RE.search(text)
    return m.group(1) if m else None


_MIRROR_ID_RE = re.compile(r"\A\ufeff?---\r?\nid:\s*([0-9a-z]{6})\s*\r?\n")
_MANAGED_PROMPT_ID_RE = re.compile(
    r"\A\ufeff?<!-- aw-managed-prompt: id:\s*([0-9a-z]{6})\b"
)


def log_format_id6(
    file_path: Path, repo_root: Path, artifact_type: Optional[str] = None
) -> Optional[str]:
    """The id6 of the record at ``file_path`` when it has a `meta/<id6>.jsonl` log, else None.

    Dormancy gate of `v45j1n` (spec `4sd62s` C10a): before the cutover no record has a log, so this
    returns None and every caller keeps its legacy behavior. The id6 is read from the post-cutover
    in-file mirror (`id:` front matter or the staged-prompt comment), a legacy `- Id:` bullet, or a
    uniform filename, and counts only if `artifact_meta._storage_format` reports `log` for it.
    """
    records_root = Path(_proj_ctx.project_records_dir(Path(repo_root).resolve()))
    if not (records_root / "meta").is_dir():
        return None
    candidates: List[str] = []
    try:
        head = file_path.read_text(encoding="utf-8")[:4096]
    except OSError:
        head = ""
    for rx in (_MIRROR_ID_RE, _MANAGED_PROMPT_ID_RE):
        m = rx.match(head)
        if m:
            candidates.append(m.group(1))
    existing = _read_existing_id6(file_path, artifact_type)
    if existing:
        candidates.append(existing)
    m_name = _UNIFORM_RE.match(file_path.name)
    if m_name:
        candidates.append(m_name.group("id6"))
    for cand in candidates:
        if _meta._storage_format(records_root, cand) == "log":
            return cand
    return None


def append_log_rename(
    repo_root: Path,
    id6: str,
    *,
    verb: str,
    new_path: Optional[Path],
    set_fields: Optional[dict] = None,
    tool: Optional[str] = None,
    dry_run: bool = False,
) -> Tuple[str, Optional[str]]:
    """Append ONE append to a log-format record: a `rename` event, then a `set` of changed Set/Order.

    Spec `4sd62s` 4.2 PATH HISTORY: the `rename` event carries ``verb`` (`rename`, `group` or
    `archive`) and the NEW records-root-relative ``path`` only; the previous path is the prior
    path-bearing event in `seq` order. ``new_path=None`` writes no `rename` event (the file did not
    move), only the `set`. Raises ``ValueError``/``RuntimeError`` when the log refuses the append, so a
    caller can pre-validate with ``dry_run=True`` before it moves any file. Returns the log's
    repo-relative path and an optional warning (the change was recorded but a later step failed).
    """
    ctx = _meta.legacy_context(repo_root)
    records_root = Path(ctx.logical_roots["records"])
    events: List[dict] = []
    if new_path is not None:
        try:
            rel = new_path.resolve().relative_to(records_root.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError(
                f"cannot record a rename event for {id6}: {new_path.name} is outside the records root"
            ) from exc
        events.append({"op": "rename", "verb": verb, "path": rel})
    log_rel = _rel_to_repo(records_root / "meta" / f"{id6}.jsonl", repo_root)
    if set_fields:
        # Only a CHANGED field the record's type registers is set (spec 4.2: "the `set` of any
        # changed `set` or `order` field"); a backlog item, for example, has no `order`.
        st = _meta.read(id6, project_context=ctx)
        known = set(_meta.REGISTRY.get(st.type, {}))
        current = {"set": st.set_id, "order": st.order_nn}
        changed = {
            k: v for k, v in set_fields.items() if k in known and current.get(k) != v
        }
        if changed:
            events.append({"op": "set", "fields": changed})
    if not events:
        return log_rel, None
    res = _meta.append(
        id6,
        events,
        dry_run=dry_run,
        project_context=ctx,
        actor={"tool": tool or f"aw {verb}"},
    )
    if isinstance(res, dict) and res.get("committed") is False and not dry_run:
        raise RuntimeError(str(res.get("error") or f"log append for {id6} failed"))
    warning = res.get("warning") if isinstance(res, dict) else None
    return log_rel, warning


_PINNED_PERMALINK_RE = re.compile(r"/(?:blob|tree|raw)/[0-9a-f]{7,40}/")


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
    for f in _core.iter_scan_files(
        repo_root, _core.REFERENCE_SCAN_ROOTS, _core._REFERENCE_TEXT_SUFFIXES
    ):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        text, _ = _refs._mask_fenced_code(text)
        for m in path_re.finditer(text):
            cited = m.group(0)
            # A permalink pinned to a commit (`.../blob/<sha>/...`) names the file AS IT WAS at that
            # commit and stays correct forever, so it is neither stale nor something to rewrite.
            if _PINNED_PERMALINK_RE.search(cited):
                continue
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


def _group_set_fields(set_id: str, order: Optional[int]) -> dict:
    """The `op: "set"` fields a regroup writes: the Set, plus the Order when one was resolved."""
    fields: dict = {"set": str(set_id)}
    if order is not None:
        fields["order"] = int(order)
    return fields


def _group_legacy_render(rec_type: str) -> "_meta.LegacyRender":
    return _meta.LegacyRender(
        "group",
        _core.utc_history_date(),
        "aw",
        history=False,
        is_prompt=(rec_type == "prompts"),
    )


def _mutation_ref_edits(repo_root: Path, edits: List[RefEdit]) -> Tuple:
    return tuple(
        MutationRefEdit(
            file=e.file.relative_to(repo_root).as_posix()
            if isinstance(e.file, Path)
            else str(e.file),
            kind=e.kind,
            old=e.old,
            new=e.new,
            hits=e.hits,
        )
        for e in edits
    )


def _log_refusal(location: str, exc: Exception, emit_human: bool) -> "MutationResult":
    msg = f"error: the record's event log refused the change: {exc}"
    if emit_human:
        print(msg)
    return MutationResult(
        2,
        diagnostics=(
            MutationDiagnostic(
                location=location,
                rule="meta-validation-error",
                detail=msg,
                severity="error",
            ),
        ),
    )


def move_with_log_event(
    repo_root: Path,
    id6: str,
    src: Path,
    dst: Path,
    *,
    verb: str,
    set_fields: Optional[dict] = None,
) -> Tuple[List[str], Optional[str]]:
    """Move one log-format record and append its `rename` event (plus any changed Set/Order).

    The append is validated with a dry run before the move, the file is moved, then the event is
    appended; if that append still fails the move is undone, so the file and its log never disagree.
    Returns the repo-relative touched paths (old, new, log) and an optional post-commit warning.
    """
    moved = src.resolve() != dst.resolve()
    new_path = dst if moved else None
    append_log_rename(
        repo_root,
        id6,
        verb=verb,
        new_path=new_path,
        set_fields=set_fields,
        dry_run=True,
    )
    touched: List[str] = []
    if moved:
        src_rel = src.relative_to(repo_root).as_posix()
        dst_rel = dst.relative_to(repo_root).as_posix()
        _core.git_mv(repo_root, src_rel, dst_rel)
        touched.extend([src_rel, dst_rel])
    try:
        log_rel, warning = append_log_rename(
            repo_root, id6, verb=verb, new_path=new_path, set_fields=set_fields
        )
    except Exception:
        if moved:
            _core.git_mv(repo_root, touched[1], touched[0])
        raise
    if not moved:
        touched.append(_rel_to_repo(dst, repo_root))
    touched.append(log_rel)
    return touched, warning


def _apply_log_rename(
    repo_root: Path,
    id6: str,
    src: Path,
    dst: Path,
    *,
    new_set: Optional[str],
    new_order: Optional[int],
    ref_edits: List[RefEdit],
    warnings: List[str],
    emit_human: bool,
    yes: bool,
) -> "MutationResult":
    """`aw rename` on a log-format record (IPD `v45j1n` E-02, spec `4sd62s` 4.2, AC-31).

    One append: a `rename` event (verb `rename`, the new records-root-relative path) and, when Set or
    Order changed, a `set` of them. No rename-ledger line is written: the event replaces it.
    """
    set_fields: dict = {}
    if new_set is not None:
        set_fields["set"] = new_set
    if new_order is not None:
        set_fields["order"] = int(new_order)
    try:
        touched, warning = move_with_log_event(
            repo_root, id6, src, dst, verb="rename", set_fields=set_fields
        )
    except (ValueError, RuntimeError) as exc:
        return _log_refusal(src.name, exc, emit_human)
    if emit_human and src.resolve() != dst.resolve():
        print(f"renamed {touched[0]} -> {touched[1]}")
    notes: List[str] = []
    if warning:
        msg = f"warning: {warning}"
        if emit_human:
            print(msg)
        notes.append(msg)
    for w in warnings:
        if emit_human:
            print(w)
        notes.append(w)
    if ref_edits:
        ref_edits = _refs.filter_test_edits_interactive(
            repo_root, ref_edits, yes=yes or not emit_human
        )
    if ref_edits:
        apply_reference_rewrites(ref_edits)
        for e in ref_edits:
            try:
                rel_f = e.file.relative_to(repo_root).as_posix()
            except ValueError:
                rel_f = str(e.file)
            if emit_human:
                print(f"rewrote {e.hits}x '{e.old}' -> '{e.new}' in {rel_f}")
            touched.append(rel_f)
    moved = src.resolve() != dst.resolve()
    target = MutationTarget(
        old_path=_rel_to_repo(src, repo_root),
        new_path=_rel_to_repo(dst, repo_root),
        id6=id6,
        kind="rename" if moved else "update",
        detail=f"-> {dst.name}" if moved else (f"Set: {new_set}" if new_set else ""),
    )
    return MutationResult(
        0,
        _dedup(touched),
        targets=(target,),
        applied=True,
        ref_edits=_mutation_ref_edits(repo_root, ref_edits),
        diagnostics=(),
        notes=tuple(notes),
    )


def run_rename_generic(
    args: argparse.Namespace, artifact_type: str, *, emit_human: Optional[bool] = None
) -> "MutationResult":
    """Universal rename execution engine for an artifact type.

    selfcommit jgcm68 E-03: RETURNS a ``MutationResult`` (rc + touched/index paths); performs NO
    commit itself. The caller (``_run_noun_verb`` dispatch) places the self-commit offer ONCE."""
    if emit_human is None:
        emit_human = getattr(args, "emit_human", True)
    repo_root = _resolve_repo_root(args)
    selector = getattr(args, "id", None) or getattr(args, "selector", None)
    if isinstance(selector, list):
        selector = selector[0] if selector else None

    if not selector:
        msg = "error: at least one <id6>, <setid>, or <path> is required"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location="selector",
                    rule="missing-target",
                    detail=msg,
                    severity="error",
                ),
            ),
        )

    # IPD laykok E-07: apply the kind-aware ambiguity policy through the unified resolver. `rename`
    # mutates ONE file, so a UNIQUE-id collision or an unforced substring multi-match REFUSES with
    # the candidate list; a setid selecting several is unusual for rename and, absent --force, also
    # refuses rather than silently renaming an arbitrary member.
    paths, amb_err = selectors.resolve_for_mutation(
        repo_root, artifact_type, selector, force=bool(getattr(args, "force", False))
    )
    if amb_err:
        msg = f"error: {amb_err}"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location=str(selector),
                    rule="ambiguous-selector",
                    detail=msg,
                    severity="error",
                ),
            ),
        )
    if len(paths) > 1 and not bool(getattr(args, "force", False)):
        cand = "\n  ".join(str(p) for p in paths)
        msg = (
            f"error: selector '{selector}' matched multiple files; rename targets one "
            f"(pass --force to rename the first, or use a unique id6):\n  {cand}"
        )
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location=str(selector),
                    rule="multiple-targets",
                    detail=msg,
                    severity="error",
                ),
            ),
        )
    src = paths[0].resolve()
    if not src.exists():
        msg = f"error: no {artifact_type} artifact matched '{selector}'"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location=str(selector),
                    rule="not-found",
                    detail=msg,
                    severity="error",
                ),
            ),
        )

    new_slug = getattr(args, "slug", None)
    new_set = getattr(args, "set", None)
    new_order = getattr(args, "order", None)
    to_id6 = bool(getattr(args, "to_id6", False))
    # IPD v45j1n E-02: a record with a `meta/<id6>.jsonl` log records the rename as a `rename` event
    # (dormant: None for every record before the cutover, which keeps the legacy path below).
    log_id6 = log_format_id6(src, repo_root, artifact_type)

    # IPD ha55fi E-04: id6-minting conversion mode. Reuse an existing `- Id:` (idempotent, never
    # re-mint) else mint a fresh id6 collision-checked against the existing spec id6 set.
    minted_id6: Optional[str] = None
    inject_id6: Optional[str] = None
    if to_id6:
        existing = log_id6 or _read_existing_id6(src, artifact_type)
        if existing:
            minted_id6 = existing  # reuse; no metadata write needed (already present)
        else:
            # IPD sk7ggr E-01: repository-wide mint, unioned with this type's own ids. A conversion
            # mint is the same hazard as a creation mint: the id6 it writes becomes permanent identity.
            minted_id6 = _core.mint_id6(
                repo_root, _existing_type_id6s(repo_root, artifact_type)
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
        msg = f"error: {err}"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location=src.name,
                    rule="target-name-error",
                    detail=msg,
                    severity="error",
                ),
            ),
        )

    assert new_name is not None
    dst = src.parent / new_name

    apply = bool(getattr(args, "apply", False))
    update_refs = not bool(getattr(args, "no_refs", False))

    if dst.resolve() != src.resolve() and dst.exists():
        msg = f"error: destination file already exists: {dst.name}"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location=dst.name,
                    rule="destination-exists",
                    detail=msg,
                    severity="error",
                ),
            ),
        )

    ref_edits, warnings = (
        plan_reference_rewrites_with_warnings(repo_root, src.name, new_name)
        if update_refs
        else ([], [])
    )
    # IPD 69pxm5 E-03: never rewrite citations inside an in-flight plan (live begin receipt).
    ref_edits, _in_flight_notes = _refs.filter_in_flight_plan_edits(
        repo_root, ref_edits
    )
    warnings = list(warnings) + _in_flight_notes

    # IPD ha55fi E-05: surface full-path citations that a filename-only rewrite cannot safely fix.
    unrewritable: List[Tuple[str, str]] = []
    if to_id6 and update_refs and src.name != new_name:
        unrewritable = find_unrewritable_path_citations(repo_root, src.name, src.parent)

    if not apply:
        if emit_human:
            print(
                f"--- would rename {src.relative_to(repo_root).as_posix()} -> {new_name} ---"
            )
        preview_notes: List[str] = []
        if to_id6 and inject_id6:
            # The MESSAGE names the real destination per type (IPD ubac5n E-04): a prompt's id6 goes
            # into its one metadata comment, not into a `- Id:` bullet, and a preview that said
            # otherwise would describe a purity violation as the intended behavior.
            msg = (
                "--- "
                + _id6_write_message(
                    artifact_type, inject_id6, new_name, preview=True, src=src
                )
                + " ---"
            )
            if emit_human:
                print(msg)
            preview_notes.append(msg)
        elif to_id6 and minted_id6:
            # Same per-type phrasing rule as the write message above: a prompt's existing id6 was
            # read out of its metadata comment, so calling it a `- Id:` bullet would be false. The
            # non-prompt text is byte-identical to what shipped (the spec tests assert "no re-mint").
            existing_label = (
                f"'Id: {minted_id6}' in the aw-prompt metadata comment"
                if artifact_type == "prompts"
                else f"'- Id: {minted_id6}'"
            )
            msg = f"--- reuses existing {existing_label} (no re-mint) ---"
            if emit_human:
                print(msg)
            preview_notes.append(msg)
        for w in warnings:
            if emit_human:
                print(w)
            preview_notes.append(w)
        if update_refs:
            for e in ref_edits:
                try:
                    rel_f = e.file.relative_to(repo_root).as_posix()
                except ValueError:
                    rel_f = str(e.file)
                if emit_human:
                    print(
                        f"--- would rewrite {e.hits}x '{e.old}' -> '{e.new}' in {rel_f} ---"
                    )
        for rel_f, cited in unrewritable:
            msg = (
                f"--- WARNING: full-path citation '{cited}' in {rel_f} names a different "
                f"directory and cannot be auto-rewritten; fix it by hand ---"
            )
            if emit_human:
                print(msg)
            preview_notes.append(msg)
        preview_target_id6 = minted_id6 or _read_existing_id6(src, artifact_type) or ""
        if not preview_target_id6:
            m_id = _UNIFORM_RE.match(src.name)
            if m_id:
                preview_target_id6 = m_id.group("id6")
        if src.resolve() != dst.resolve():
            target = MutationTarget(
                old_path=_rel_to_repo(src, repo_root),
                new_path=_rel_to_repo(dst, repo_root),
                id6=preview_target_id6,
                kind="rename",
                detail=f"-> {new_name}",
            )
        else:
            target = MutationTarget(
                old_path=_rel_to_repo(src, repo_root),
                new_path=_rel_to_repo(dst, repo_root),
                id6=preview_target_id6,
                kind="update",
                detail=f"Set: {new_set}" if new_set else "",
            )
        preview_ref_edits = tuple(
            MutationRefEdit(
                file=e.file.relative_to(repo_root).as_posix()
                if isinstance(e.file, Path)
                else str(e.file),
                kind=e.kind,
                old=e.old,
                new=e.new,
                hits=e.hits,
            )
            for e in ref_edits
        )
        return MutationResult(
            0,
            touched_paths=(),
            targets=(target,),
            applied=False,
            ref_edits=preview_ref_edits,
            diagnostics=(),
            notes=tuple(preview_notes),
        )

    if unrewritable:
        # Fail loud on --apply so the operator fixes the un-auto-rewritable citation first.
        diags: List[MutationDiagnostic] = []
        for rel_f, cited in unrewritable:
            msg = (
                f"error: full-path citation '{cited}' in {rel_f} names a different directory "
                f"than the file; cannot auto-rewrite. Fix it by hand, then retry."
            )
            if emit_human:
                print(msg)
            diags.append(
                MutationDiagnostic(
                    location=rel_f,
                    rule="unrewritable-citation",
                    detail=msg,
                    severity="error",
                )
            )
        return MutationResult(2, diagnostics=tuple(diags))

    if log_id6 is not None:
        return _apply_log_rename(
            repo_root,
            log_id6,
            src,
            dst,
            new_set=_core.kebab(new_set) if new_set else None,
            new_order=new_order,
            ref_edits=ref_edits if update_refs else [],
            warnings=warnings,
            emit_human=emit_human,
            yes=bool(getattr(args, "yes", False)),
        )

    # Apply changes
    touched: List[str] = []
    if src.resolve() != dst.resolve():
        src_rel = src.relative_to(repo_root).as_posix()
        dst_rel = dst.relative_to(repo_root).as_posix()
        _core.git_mv(repo_root, src_rel, dst_rel)
        if emit_human:
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

    applied_notes: List[str] = []
    if new_set is not None or new_order is not None or inject_id6 is not None:
        # IPD ha55fi E-04: same atomic transaction writes Set/Order AND injects the minted `- Id:`.
        try:
            dst_text: Optional[str] = dst.read_text(encoding="utf-8")
        except OSError:
            dst_text = None
        if dst_text is not None:
            m_rroot, m_ctx, m_type, m_target, m_rel = _meta_target_for_file(
                dst, artifact_type, repo_root=repo_root, fallback_id6=inject_id6
            )
            m_events = _rename_metadata_events(
                dst_text,
                m_type,
                m_rel,
                existing_id6=_read_existing_id6(dst, m_type),
                set_id=_core.kebab(new_set) if new_set else None,
                order=new_order,
                id6=inject_id6,
            )
            if m_events:
                _meta.append(
                    m_target,
                    m_events,
                    legacy_render=_meta.LegacyRender(
                        "rename",
                        _core.utc_history_date(),
                        "aw",
                        history=False,
                        is_prompt=(m_type == "prompts"),
                    ),
                    repo_root=m_rroot,
                    project_context=m_ctx,
                )
        if inject_id6 is not None:
            # Read `dst` (post-write) rather than `src` (already moved away): for a prompt WITH a
            # comment the id6 is now in it, and for one WITHOUT the file is untouched, so the message
            # reflects what is actually on disk in both cases.
            msg = _id6_write_message(
                artifact_type, inject_id6, dst.name, preview=False, src=dst
            )
            if emit_human:
                print(msg)
            applied_notes.append(msg)
        touched.append(_rel_to_repo(dst, repo_root))

    for w in warnings:
        if emit_human:
            print(w)
        applied_notes.append(w)
    if update_refs and ref_edits:
        ref_edits = _refs.filter_test_edits_interactive(
            repo_root,
            ref_edits,
            yes=bool(getattr(args, "yes", False)) or not emit_human,
        )
    if update_refs and ref_edits:
        apply_reference_rewrites(ref_edits)
        for e in ref_edits:
            try:
                rel_f = e.file.relative_to(repo_root).as_posix()
            except ValueError:
                rel_f = str(e.file)
            if emit_human:
                print(f"rewrote {e.hits}x '{e.old}' -> '{e.new}' in {rel_f}")
            touched.append(rel_f)

    applied_target_id6 = minted_id6 or _read_existing_id6(dst, artifact_type) or ""
    if not applied_target_id6:
        m_id = _UNIFORM_RE.match(dst.name)
        if m_id:
            applied_target_id6 = m_id.group("id6")
    if src.resolve() != dst.resolve():
        target = MutationTarget(
            old_path=src_rel,
            new_path=dst_rel,
            id6=applied_target_id6,
            kind="rename",
            detail=f"-> {dst.name}",
        )
    else:
        target = MutationTarget(
            old_path=_rel_to_repo(src, repo_root),
            new_path=_rel_to_repo(dst, repo_root),
            id6=applied_target_id6,
            kind="update",
            detail=f"Set: {new_set}" if new_set else "",
        )
    mutation_applied_ref_edits = tuple(
        MutationRefEdit(
            file=e.file.relative_to(repo_root).as_posix()
            if isinstance(e.file, Path)
            else str(e.file),
            kind=e.kind,
            old=e.old,
            new=e.new,
            hits=e.hits,
        )
        for e in (ref_edits if update_refs else [])
    )
    return MutationResult(
        0,
        _dedup(touched),
        targets=(target,),
        applied=True,
        ref_edits=mutation_applied_ref_edits,
        diagnostics=(),
        notes=tuple(applied_notes),
    )


def run_group_generic(
    args: argparse.Namespace,
    artifact_type: str,
    emit_human: Optional[bool] = None,
) -> "MutationResult":
    """Universal set assignment / group execution engine for an artifact type."""
    if emit_human is None:
        emit_human = not (getattr(args, "agent", False) or getattr(args, "json", False))
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
        msg = "error: at least one <id6>, <setid>, or <path> is required"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location="selectors",
                    rule="missing-target",
                    detail=msg,
                    severity="error",
                ),
            ),
        )

    new_set = getattr(args, "set", None)
    if not new_set or not new_set.strip():
        msg = "error: --set <set-id> is required"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location="set",
                    rule="missing-set",
                    detail=msg,
                    severity="error",
                ),
            ),
        )

    set_k = _core.kebab(new_set)
    # setidlen x75obw E-06 (catalog I-17): the ONE shared setid-length guard. Judged on the KEBABED
    # token, deliberately, because that is what actually lands in the filename and in `- Set:`; judging
    # the raw argument would let `Research Prompt Pipeline Extras` pass and then write a longer setid
    # than the policy allows. Refuses over `max_length`; warns and proceeds over `warn_length`.
    from agent_workflows import config as _config

    _setid_err, _setid_warn = _config.validate_setid_length_for_authoring(
        repo_root, set_k, verb=f"aw group {artifact_type}"
    )
    if _setid_err:
        msg = f"error: {_setid_err}"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location="set",
                    rule="setid-length-error",
                    detail=msg,
                    severity="error",
                ),
            ),
        )
    group_notes: List[str] = []
    if _setid_warn:
        msg = f"note: {_setid_warn}"
        if emit_human:
            print(msg)
        group_notes.append(msg)
    start_order = getattr(args, "order", None)
    apply = bool(getattr(args, "apply", False))
    update_refs = not bool(getattr(args, "no_refs", False))
    rename_files = bool(getattr(args, "rename", False))

    targets: List[Tuple[Path, Path, Optional[int]]] = []
    all_edits: List[RefEdit] = []
    all_warnings: List[str] = []

    for i, sel in enumerate(selectors_list):
        src = find_target_record(repo_root, artifact_type, sel)
        if src is None or not src.exists():
            msg = f"error: no {artifact_type} artifact matched '{sel}'"
            if emit_human:
                print(msg)
            return MutationResult(
                2,
                diagnostics=(
                    MutationDiagnostic(
                        location=str(sel),
                        rule="not-found",
                        detail=msg,
                        severity="error",
                    ),
                ),
            )
        order_val = (start_order + i) if start_order is not None else None
        if rename_files:
            new_name, err = compute_target_name(
                src.name,
                artifact_type,
                new_set=set_k,
                new_order=order_val,
            )
            if err:
                # dl86am D2: a name the verb cannot re-cluster is REFUSED, not silently kept. The old
                # `new_name = src.name` reported a successful group whose `--rename` half did nothing.
                msg = f"error: cannot --rename {src.name}: {err}"
                if emit_human:
                    print(msg)
                return MutationResult(
                    2,
                    diagnostics=(
                        MutationDiagnostic(
                            location=src.name,
                            rule="target-name-error",
                            detail=msg,
                            severity="error",
                        ),
                    ),
                )
            assert new_name is not None
            dst = src.parent / new_name
        else:
            dst = src

        if dst.resolve() != src.resolve() and dst.exists():
            msg = f"error: destination file already exists: {dst.name}"
            if emit_human:
                print(msg)
            return MutationResult(
                2,
                diagnostics=(
                    MutationDiagnostic(
                        location=dst.name,
                        rule="destination-exists",
                        detail=msg,
                        severity="error",
                    ),
                ),
            )

        targets.append((src, dst, order_val))
        if update_refs and src.name != dst.name:
            edits, warns = plan_reference_rewrites_with_warnings(
                repo_root, src.name, dst.name
            )
            all_edits.extend(edits)
            for w in warns:
                if w not in all_warnings:
                    all_warnings.append(w)
    # IPD 69pxm5 E-03: never rewrite citations inside an in-flight plan (live begin receipt).
    all_edits, _in_flight_notes = _refs.filter_in_flight_plan_edits(
        repo_root, all_edits
    )
    for w in _in_flight_notes:
        if w not in all_warnings:
            all_warnings.append(w)

    if not apply:
        preview_targets: List[MutationTarget] = []
        for src, dst, _order_val in targets:
            src_rel = src.relative_to(repo_root).as_posix()
            t_id6 = _read_existing_id6(src, artifact_type) or ""
            if not t_id6:
                m_id = _UNIFORM_RE.match(src.name)
                if m_id:
                    t_id6 = m_id.group("id6")
            if src.resolve() != dst.resolve():
                if emit_human:
                    print(f"--- would rename {src_rel} -> {dst.name} ---")
                preview_targets.append(
                    MutationTarget(
                        old_path=src_rel,
                        new_path=dst.relative_to(repo_root).as_posix(),
                        id6=t_id6,
                        kind="rename",
                        detail=f"-> {dst.name}",
                    )
                )
            if emit_human:
                print(f"--- would set metadata Set: {set_k} in {src_rel} ---")
            preview_targets.append(
                MutationTarget(
                    old_path=src_rel,
                    new_path=dst.relative_to(repo_root).as_posix()
                    if src.resolve() != dst.resolve()
                    else src_rel,
                    id6=t_id6,
                    kind="update",
                    detail=f"Set: {set_k}",
                )
            )
        for w in all_warnings:
            if emit_human:
                print(w)
            group_notes.append(w)
        if update_refs:
            for e in all_edits:
                try:
                    rel_f = e.file.relative_to(repo_root).as_posix()
                except ValueError:
                    rel_f = str(e.file)
                if emit_human:
                    print(
                        f"--- would rewrite {e.hits}x '{e.old}' -> '{e.new}' in {rel_f} ---"
                    )
        mutation_edits = tuple(
            MutationRefEdit(
                file=e.file.relative_to(repo_root).as_posix()
                if isinstance(e.file, Path)
                else str(e.file),
                kind=e.kind,
                old=e.old,
                new=e.new,
                hits=e.hits,
            )
            for e in all_edits
        )
        return MutationResult(
            0,
            touched_paths=(),
            targets=tuple(preview_targets),
            applied=False,
            ref_edits=mutation_edits,
            diagnostics=(),
            notes=tuple(group_notes),
        )

    # Pre-flight validate every target on disk before any git_mv, record_rename, or file write.
    for src, _dst, order_val in targets:
        try:
            g_rroot, g_ctx, g_type, g_target, _g_rel = _meta_target_for_file(
                src, artifact_type, repo_root=repo_root
            )
            _meta.append(
                g_target,
                [{"op": "set", "fields": _group_set_fields(set_k, order_val)}],
                legacy_render=_group_legacy_render(g_type),
                repo_root=g_rroot,
                project_context=g_ctx,
                dry_run=True,
            )
        except ValueError as exc:
            msg = f"error: {exc}"
            if emit_human:
                print(msg)
            return MutationResult(
                2,
                diagnostics=(
                    MutationDiagnostic(
                        location=_rel_to_repo(src, repo_root),
                        rule="meta-validation-error",
                        detail=msg,
                        severity="error",
                    ),
                ),
            )

    # Apply changes
    touched: List[str] = []
    applied_targets: List[MutationTarget] = []
    for src, dst, order_val in targets:
        t_id6 = _read_existing_id6(src, artifact_type) or ""
        if not t_id6:
            m_id = _UNIFORM_RE.match(src.name)
            if m_id:
                t_id6 = m_id.group("id6")
        # IPD v45j1n E-03: a record with a `meta/<id6>.jsonl` log records the regroup in its log, one
        # append of a `rename` event (verb `group`, the new path) and a `set` of the changed Set/Order
        # (spec 4sd62s 4.2). Dormant before the cutover: no record has a log.
        log_id6 = log_format_id6(src, repo_root, artifact_type)
        if log_id6 is not None:
            moved = src.resolve() != dst.resolve()
            log_set: dict = {"set": set_k}
            if order_val is not None:
                log_set["order"] = int(order_val)
            try:
                log_touched, log_warning = move_with_log_event(
                    repo_root, log_id6, src, dst, verb="group", set_fields=log_set
                )
            except (ValueError, RuntimeError) as exc:
                return _log_refusal(src.name, exc, emit_human)
            if emit_human:
                if moved:
                    print(f"renamed {log_touched[0]} -> {log_touched[1]}")
                print(f"set Set: {set_k} in {log_touched[-1]}")
            if log_warning:
                group_notes.append(f"warning: {log_warning}")
            touched.extend(log_touched)
            src_rel = _rel_to_repo(src, repo_root)
            dst_rel = _rel_to_repo(dst, repo_root)
            applied_targets.append(
                MutationTarget(
                    old_path=src_rel,
                    new_path=dst_rel,
                    id6=log_id6,
                    kind="rename" if moved else "update",
                    detail=f"-> {dst.name}" if moved else f"Set: {set_k}",
                )
            )
            continue
        if src.resolve() != dst.resolve():
            src_rel = src.relative_to(repo_root).as_posix()
            dst_rel = dst.relative_to(repo_root).as_posix()
            _core.git_mv(repo_root, src_rel, dst_rel)
            if emit_human:
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
            applied_targets.append(
                MutationTarget(
                    old_path=src_rel,
                    new_path=dst_rel,
                    id6=t_id6,
                    kind="rename",
                    detail=f"-> {dst.name}",
                )
            )
        g_rroot, g_ctx, g_type, g_target, _g_rel = _meta_target_for_file(
            dst, artifact_type, repo_root=repo_root
        )
        _meta.append(
            g_target,
            [{"op": "set", "fields": _group_set_fields(set_k, order_val)}],
            legacy_render=_group_legacy_render(g_type),
            repo_root=g_rroot,
            project_context=g_ctx,
        )
        dst_rel = dst.relative_to(repo_root).as_posix()
        if emit_human:
            print(f"set metadata Set: {set_k} in {dst_rel}")
        touched.append(dst_rel)
        applied_targets.append(
            MutationTarget(
                old_path=dst_rel,
                new_path=dst_rel,
                id6=t_id6,
                kind="update",
                detail=f"Set: {set_k}",
            )
        )

    for w in all_warnings:
        if emit_human:
            print(w)
        group_notes.append(w)
    if update_refs and all_edits:
        all_edits = _refs.filter_test_edits_interactive(
            repo_root,
            all_edits,
            yes=bool(getattr(args, "yes", False)) or not emit_human,
        )
    if update_refs and all_edits:
        apply_reference_rewrites(all_edits)
        for e in all_edits:
            try:
                rel_f = e.file.relative_to(repo_root).as_posix()
            except ValueError:
                rel_f = str(e.file)
            if emit_human:
                print(f"rewrote {e.hits}x '{e.old}' -> '{e.new}' in {rel_f}")
            touched.append(rel_f)

    applied_mutation_edits = tuple(
        MutationRefEdit(
            file=e.file.relative_to(repo_root).as_posix()
            if isinstance(e.file, Path)
            else str(e.file),
            kind=e.kind,
            old=e.old,
            new=e.new,
            hits=e.hits,
        )
        for e in (all_edits if update_refs else [])
    )
    return MutationResult(
        0,
        _dedup(touched),
        targets=tuple(applied_targets),
        applied=True,
        ref_edits=applied_mutation_edits,
        diagnostics=(),
        notes=tuple(group_notes),
    )


def run_rename_backlog(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_rename_generic(args, "backlog", emit_human=emit_human)


def run_rename_specs(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_rename_generic(args, "specs", emit_human=emit_human)


def run_rename_prompts(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_rename_generic(args, "prompts", emit_human=emit_human)


def run_rename_walkthroughs(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_rename_generic(args, "walkthroughs", emit_human=emit_human)


def run_rename_roadmaps(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_rename_generic(args, "roadmaps", emit_human=emit_human)


def run_rename_releases(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_rename_generic(args, "releases", emit_human=emit_human)


def run_rename_other(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_rename_generic(args, "other", emit_human=emit_human)


def run_group_backlog(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_group_generic(args, "backlog", emit_human=emit_human)


def run_group_specs(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_group_generic(args, "specs", emit_human=emit_human)


def run_group_prompts(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_group_generic(args, "prompts", emit_human=emit_human)


def run_group_walkthroughs(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_group_generic(args, "walkthroughs", emit_human=emit_human)


def run_group_roadmaps(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_group_generic(args, "roadmaps", emit_human=emit_human)


def run_group_releases(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_group_generic(args, "releases", emit_human=emit_human)


def run_group_other(
    args: argparse.Namespace, emit_human: Optional[bool] = None
) -> "MutationResult":
    return run_group_generic(args, "other", emit_human=emit_human)
