"""Plans regroup/rename + reference integrity (Set plans-adopter, Order 04).

Enables after-the-fact topic regrouping of plans without breaking citations:

* ``aw plans set-assign <id6...> --set <s> [--order ...] [--rename]`` groups plans into a Set
  (updates ``Set:``/``Order:`` metadata; with ``--rename`` renames to the clustering grammar
  ``YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md`` as an atomic tracked ``git mv``, keeping ``Id``);
* ``aw plans mv <id6> [--slug ... --set ... --order ...]`` renames/re-slugs one plan;
* a reference updater that rewrites the THREE plan-citation forms via an explicit old-name ->
  new-name map (so a bare stem is rewritten ONLY when it maps to a PLAN; a spec-only stem sharing
  the ``YYYYMMDD-HHMM-NN`` grammar is never touched); reuses the shared-core dangling detector.

The immutable ``Id`` (Order 02) is the citation handle. Writing safety mirrors ``aw ipd scaffold``:
preview by default, ``--apply`` to write, atomic writes, tracked ``git mv``. Consumes the Order-01
core, Order-02 ``Id``, and Order-03 manifest scan.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import artifact_refs as _refs
from agent_workflows import plans_index as _idx
from agent_workflows import record_history as _rh
from agent_workflows import selectors as _selectors

PLANS_DIR = ".agents/plans"

# The uniform artifact-type facets and the clustered grammar are defined ONCE in the naming
# authority (IPD o6b8l3); re-exported here so this module's public API is unchanged.
ARTIFACT_TYPE_FACETS = _naming.ARTIFACT_TYPE_FACETS
_FACET_ALT = _naming._FACET_ALT
_CLUSTERED_RE = _naming._CLUSTERED_RE
_LEGACY_TIMESTAMP_RE = _naming._LEGACY_TIMESTAMP_RE
# An old-style plan stem: YYYYMMDD-HHMM-NN (bare, no slug/.md). Shared with specs, so a bare-stem
# rewrite is driven by an explicit plan map, never by this pattern alone.
_BARE_STEM_RE = re.compile(r"\b(\d{8}-\d{4}-\d{2})\b")


# --------------------------------------------------------------------------------------
# metadata read/write on a plan file
# --------------------------------------------------------------------------------------

_ID_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_DATE_RE = re.compile(r"(?m)^- Date:\s*(\d{8}|\d{4}-\d{2}-\d{2})\s*$")
_SET_LINE_RE = re.compile(r"(?m)^- Set:\s*(.+?)\s*$")
_ORDER_LINE_RE = re.compile(r"(?m)^- Order:\s*(-?\d+)\s*$")


def _read_id(text: str) -> Optional[str]:
    m = _ID_RE.search(text)
    return m.group(1) if m else None


def _find_plan_by_id(plans_dir: Path, id6: str) -> Optional[Path]:
    ignored_dirs = _core.get_ignored_dirs(plans_dir)
    for p in plans_dir.rglob("*.md"):
        if p.name in _idx._EXCLUDE_NAMES or _core.is_ignored_path(
            p, plans_dir, ignored_dirs
        ):
            continue
        if _read_id(p.read_text(encoding="utf-8")) == id6:
            return p
    return None


def _set_value(set_id: str, descriptive: Optional[str]) -> str:
    """The `Set:` metadata value: terse id, optionally with a `(descriptive)` parenthetical."""

    return f"{set_id} ({descriptive})" if descriptive else set_id


def _set_metadata(
    text: str,
    *,
    set_id: str,
    order: int,
    descriptive: Optional[str] = None,
    plan_name: Optional[str] = None,
) -> str:
    """Return ``text`` with Set/Order set (updating existing lines or inserting after Author/Id).

    The written `Set:` value is ``<terse-id> (<descriptive>)`` when ``descriptive`` is given, else the
    bare terse id (plans-adopter Order 06 format).
    """

    set_val = _set_value(set_id, descriptive)
    if _SET_LINE_RE.search(text):
        text = _SET_LINE_RE.sub(f"- Set: {set_val}", text, count=1)
    if _ORDER_LINE_RE.search(text):
        text = _ORDER_LINE_RE.sub(f"- Order: {order}", text, count=1)
    if not (_SET_LINE_RE.search(text) and _ORDER_LINE_RE.search(text)):
        # Insert Set/Order after the Id line (or Author line) when absent.
        lines = text.splitlines(keepends=True)
        anchor = None
        for i, line in enumerate(lines):
            if line.startswith("- Id:"):
                anchor = i
        if anchor is None:
            for i, line in enumerate(lines):
                if line.startswith("- Author:"):
                    anchor = i
        if anchor is not None:
            nl = "\n"
            ins = []
            if not _SET_LINE_RE.search(text):
                ins.append(f"- Set: {set_val}{nl}")
            if not _ORDER_LINE_RE.search(text):
                ins.append(f"- Order: {order}{nl}")
            lines[anchor + 1 : anchor + 1] = ins
        text = "".join(lines)

    order_lines = re.findall(r"(?m)^- Order:.*$", text)
    if len(order_lines) != 1:
        target = plan_name or _read_id(text) or "plan"
        raise ValueError(
            f"plan '{target}': expected exactly one '- Order:' line after metadata update, "
            f"found {len(order_lines)}"
        )
    return text


def _plan_date(text: str) -> str:
    m = _DATE_RE.search(text)
    if not m:
        return "20260101"
    raw = m.group(1)
    return raw.replace("-", "") if "-" in raw else raw


# --------------------------------------------------------------------------------------
# rename planning
# --------------------------------------------------------------------------------------


class RenamePlan(NamedTuple):
    old_path: Path
    new_path: Path
    id6: str
    # The Order to write into the plan's front matter. None means "use the enumerate index" (the
    # historical set-assign behavior where the caller sequences a batch). `aw plans mv` passes the
    # plan's PRESERVED order so a bare rename does not clobber `- Order:` to 0 (vf03z3).
    order: Optional[int] = None


class MutationResult(NamedTuple):
    """The exact set of paths a records-mutating backend touched, for the self-commit offer.

    selfcommit child jgcm68 (E-03): group/rename backends (``plans_refs``, ``research_refs``,
    ``artifact_rename``) RETURN this instead of a bare int so the CALLER (the ``_run_noun_verb``
    group/rename dispatch, or the ``aw research set-assign``/``mv`` command branch) can place the
    ``git_commit_helper.offer_commit`` offer ONCE at the call site (PR-012: never inside a shared
    backend, or ``aw group research`` would double-fire). The backend itself performs NO commit.

    * ``rc`` - the backend's exit code (0 ok / 1 findings / 2 cannot-run); the router still honors it.
    * ``touched_paths`` - repo-relative paths the backend moved/renamed/rewrote (incl. citing files
      whose references were rewritten), tracked EXPLICITLY during the mutation - never a dirty scan.

    The commit path-set is ``touched_paths``, and that is the WHOLE of it. There is deliberately no
    ``index_paths`` companion: the backends still REGENERATE the INDEX.json/INDEX.md manifests, but
    those are generated output that no `aw` verb commits (idxuntrack `4r0qp1` E-03), so a caller must
    not add them back to a commit path-set. This type is defined here (in scope) and imported by
    ``research_refs`` and ``artifact_rename`` so there is a single shared definition.
    """

    rc: int
    touched_paths: Tuple[str, ...] = ()


def clustered_name(
    *,
    date: str,
    set_id: str,
    order: int,
    id6: str,
    slug: str,
    artifact_type: Optional[str] = None,
) -> str:
    """Build a clustered name. When ``artifact_type`` is one of ``ARTIFACT_TYPE_FACETS`` the uniform
    ``<...>.<type>.md`` facet is appended; when None (or empty) the bare ``.md`` form is produced
    (backward-compatible). Delegates to the single naming authority (IPD o6b8l3)."""

    return _naming.build_clustered_name(
        date=date,
        set_id=set_id,
        order=order,
        id6=id6,
        slug=slug,
        artifact_type=artifact_type,
    )


def _slug_of(old_name: str, id6: str) -> str:
    """Derive the true slug of a clustered plan name (IPD 5rzupk fix).

    Parse the filename with the SAME permissive parser the correct generic rename path uses
    (``artifact_naming.parse_uniform_permissive`` -> ``_UNIFORM_RE``, read as ``m.group("slug")`` by
    ``artifact_rename.compute_target_name``) and return its ``slug`` group, so a
    ``rename --order`` with no ``--slug`` changes only the Order facet and never injects the old
    ``<setid>-NN-`` cluster prefix into the slug. Falls back to the legacy digit-stripping heuristic
    ONLY for a truly legacy name the canonical parser does not match.
    """

    m = _naming.parse_uniform_permissive(old_name)
    if m is not None:
        return _core.kebab(m.group("slug")) or "plan"

    # Legacy fallback (unchanged): a name the canonical parser does not handle.
    base = old_name.removesuffix(".md")
    base = base.split(".")[0]  # drop any dotted facets
    parts = [p for p in base.split("-") if p and p != id6]
    # Drop leading date/time/nn numeric tokens.
    while parts and parts[0].isdigit():
        parts.pop(0)
    return _core.kebab("-".join(parts)) or "plan"


def _preserved_order(name: str, text: str) -> int:
    """The Order a plan ALREADY has: its front-matter ``- Order:``, else its filename's ``NN``, else 0.

    e3hzyc: this is what a bare ``aw group plans ... --set X`` (no ``--order``) must write, so the
    verb stops renumbering every named plan from zero and parking a ``Kind: child`` in the ``00``
    slot the naming grammar reserves for an orchestrator. The tier order matches ``run_mv``'s
    already-shipped fallback (vf03z3: "a bare rename must NOT clobber Order to 0"), which is
    deliberately left byte-unchanged here rather than refactored into a shared helper.
    """

    om = _ORDER_LINE_RE.search(text)
    if om:
        return int(om.group(1))
    parsed = _CLUSTERED_RE.match(name)
    return int(parsed.group("nn")) if parsed else 0


def _preserved_date(name: str, text: str) -> str:
    """The date a plan ALREADY has: filename (clustered then legacy), else front matter, else 20260101.

    949enf: resolve date from current filename before falling back to front matter.
    NOTE THE DELIBERATE TIER-ORDER ASYMMETRY WITH _preserved_order: _preserved_order
    reads FRONT MATTER FIRST and the filename second, while this helper reads the
    FILENAME FIRST. That is deliberate and is what run_mv's existing comment already
    mandates for the date (vf03z3: 'a bare rename must NOT recompute the date'), and
    it is what OQ-01 resolves: the front-matter date cannot be trusted ahead of the name
    here because its own failure mode is a FABRICATED CONSTANT ('20260101') rather than
    an absent value (and a malformed - Date: escapes lint without complaint), so
    consulting front matter first reintroduces the bug.
    """

    parsed_clustered = _CLUSTERED_RE.match(name)
    if parsed_clustered:
        return parsed_clustered.group("date")
    parsed_legacy = _LEGACY_TIMESTAMP_RE.match(name)
    if parsed_legacy:
        return parsed_legacy.group("date")
    return _plan_date(text)


def _order_grammar_error(order: int) -> Optional[str]:
    """Validate that the resolved Order is an integer in 0 to 99 inclusive (the two-digit NN facet)."""
    if not isinstance(order, int) or order < 0 or order > 99:
        return (
            f"Order '{order}' is out of grammar: must be an integer from 0 to 99 "
            "(the two-digit NN facet)"
        )
    return None


def _validate_plan_order(text: str, order: int) -> Optional[str]:
    """Validate that the resolved Order is permitted for the plan's Kind.

    Consults `ipd_schema.validate_metadata` with the plan's Kind and resolved Order.
    Refuses when Kind is present and the resolved Order is forbidden by schema rules
    (child Order must be an integer >= 1, orchestrator Order must be 0; see qhcojn, xvi55d).
    Silent when Kind is absent.
    """
    from agent_workflows import ipd_schema
    from agent_workflows.runner_shared import _read_kind

    kind = _read_kind(text)
    if not kind:
        return None
    fields = {"Kind": kind, "Set": "set", "Order": str(order)}
    for err in ipd_schema.validate_metadata(fields):
        if err.field == "Order":
            return err.message
    return None


def plan_set_assign(
    plans_dir: Path,
    id6s: List[str],
    set_id: str,
    *,
    start_order: Optional[int] = None,
    rename: bool = False,
    allow_invalid_order: bool = False,
    repo_root: Optional[Path] = None,
    force: bool = False,
) -> Tuple[Optional[List[RenamePlan]], Optional[str]]:
    """Plan a Set (re)assignment for the given plans; with ``rename`` also plan clustering renames.

    ``start_order`` is the ``--order`` flag and its ABSENCE is now distinguishable from an explicit
    zero (e3hzyc; the old ``int = 0`` default could not tell them apart):

    * ``None`` (flag omitted) PRESERVES each plan's own Order, resolved per plan by
      ``_preserved_order``. This is what a bare regroup must do, and it applies to BOTH branches
      below, because the Order is resolved ABOVE the ``rename`` split: the clustering branch keeps
      the plan's ``NN`` slot, and the metadata-only branch can no longer write an ``- Order:`` its
      own filename contradicts.
    * an INTEGER (including 0) renumbers the named plans SEQUENTIALLY from it (``start_order + i``),
      which is the legitimate way an operator assembles a Set out of scattered plans.
    * resolved Order validity (qhcojn, xvi55d): if a plan's resolved Order violates either half
      of ``ipd_schema``'s kind-conditional rule (child Order must be >= 1, orchestrator Order must
      be 0), the mutation is refused (returns ``None, err``, exit 2) by consulting
      ``ipd_schema.validate_metadata`` unless ``allow_invalid_order=True``. Mirrors ``run_mv``.
    """

    set_k = _core.kebab(set_id)
    if not set_k:
        return None, "a --set id is required"

    if repo_root is None:
        from agent_workflows.project_context import resolve_verb_repo_root

        repo_root = resolve_verb_repo_root(str(plans_dir))

    # IPD 87m438 E-04 / OQ-04: resolve each selector through selectors.resolve_for_mutation.
    # An intentional multi-target (such as a setid) expands deterministically in sorted-path
    # order before enumeration, so sequential --order renumbers the whole expanded set.
    target_paths: List[Path] = []
    for sel in id6s:
        paths, amb_err = _selectors.resolve_for_mutation(
            repo_root, "plans", sel, force=force
        )
        if amb_err:
            return None, amb_err
        if not paths:
            return None, f"no plans artifact matched '{sel}'"
        for p in paths:
            p_res = p.resolve()
            if p_res not in target_paths:
                target_paths.append(p_res)

    plans: List[RenamePlan] = []
    for i, src in enumerate(target_paths):
        if not src.exists():
            return None, f"no plans artifact matched '{src.name}'"
        text = src.read_text(encoding="utf-8")
        id6 = _read_id(text)
        if not id6:
            return None, f"plan '{src.name}' declares no '- Id:'"
        order = (
            (start_order + i)
            if start_order is not None
            else _preserved_order(src.name, text)
        )
        grammar_err = _order_grammar_error(order)
        if grammar_err:
            return None, f"plan '{id6}' ({src.name}): {grammar_err}"
        order_err = _validate_plan_order(text, order)
        if order_err:
            if allow_invalid_order:
                print(f"note: plan '{id6}' ({src.name}): overridden rule: {order_err}")
            else:
                return (
                    None,
                    f"plan '{id6}' ({src.name}): {order_err} (pass --allow-invalid-order to override)",
                )
        if rename:
            new_name = clustered_name(
                date=_preserved_date(src.name, text),
                set_id=set_k,
                order=order,
                id6=id6,
                slug=_slug_of(src.name, id6),
                artifact_type="ipd",
            )
            plans.append(RenamePlan(src, src.parent / new_name, id6, order=order))
        else:
            plans.append(
                RenamePlan(src, src, id6, order=order)
            )  # metadata-only (no rename)
    return plans, None


# --------------------------------------------------------------------------------------
# reference rewriting: the three citation forms, driven by an explicit old->new PLAN map
# --------------------------------------------------------------------------------------


# The RefEdit record is defined ONCE in the unified reference library (IPD 3cmnfc); re-export it so
# this module's API (`RefEdit(file, kind, old, new, hits)`) is unchanged.
RefEdit = _refs.RefEdit


def _old_stem(old_name: str) -> Optional[str]:
    """The old-style YYYYMMDD-HHMM-NN stem of an old plan filename, if it has one."""

    m = re.match(r"\A(\d{8}-\d{4}-\d{2})-", old_name)
    return m.group(1) if m else None


def plan_reference_rewrites(
    repo_root: Path, name_map: Dict[str, str], plans_dir: Path
) -> List[RefEdit]:
    """Plan every FILENAME-derived citation rewrite for a PLAN ``name_map`` (old -> new).

    IPD 3cmnfc E-04: delegates to the ONE unified reference matcher (``artifact_refs``): full name +
    whole stem (covers the range shorthand ``<stem>..NN``) + the legacy ``YYYYMMDD-HHMM-NN`` prefix
    stem, all map-driven and hyphen-boundaried, never touching a bare id6/setid. This also gives a
    CLUSTERED plan rename the whole-stem rewrite it previously lacked (the same fix research gets).
    ``plans_dir`` is retained for API compatibility (matching scans the pinned SCAN_ROOTS).
    """

    return _refs.plan_reference_rewrites(repo_root, name_map)


def plan_reference_rewrites_with_warnings(
    repo_root: Path, name_map: Dict[str, str], plans_dir: Path
) -> Tuple[List[RefEdit], List[str]]:
    """Plan citation rewrites and collect warnings for a PLAN name_map (old -> new)."""
    return _refs.plan_reference_rewrites_with_warnings(repo_root, name_map)


def apply_reference_rewrites(edits: List[RefEdit]) -> None:
    """Apply planned rewrites via the unified applier (full-name first, then hyphen-boundaried stem)."""

    _refs.apply_reference_rewrites(edits, prefix=".plans-refs-")


# --------------------------------------------------------------------------------------
# apply the renames (metadata + git mv + reference rewrite)
# --------------------------------------------------------------------------------------


def apply_renames(
    repo_root: Path,
    plans_dir: Path,
    plans: List[RenamePlan],
    set_id: str,
    *,
    apply: bool,
    descriptive: Optional[str] = None,
    update_refs: bool = True,
    verb: str = "group",
    yes: bool = False,
) -> Tuple[str, ...]:
    """Set metadata + (optional) clustering rename + citation rewrite. Preview when not apply.
    update_refs=False (from `--no-refs`, awcmdsurf Order 03) renames the file only, leaving citing
    documents untouched.

    Returns the repo-relative paths actually touched on ``apply`` (the mutated plan files at their
    final location + rewritten citing files); empty on preview. The caller adds the regenerated
    INDEX paths and drives the self-commit offer (selfcommit jgcm68 E-03)."""

    name_map = {
        p.old_path.name: p.new_path.name for p in plans if p.old_path != p.new_path
    }
    ref_edits, warnings = (
        plan_reference_rewrites_with_warnings(repo_root, name_map, plans_dir)
        if (name_map and update_refs)
        else ([], [])
    )
    if not apply:
        for w in warnings:
            print(w)
        for i, p in enumerate(plans):
            if p.old_path == p.new_path:
                # e3hzyc: preview the Order that would ACTUALLY be written (the plan's own, when
                # `--order` was omitted), not the loop index, or a dry run reports a renumber the
                # apply no longer performs.
                shown = p.order if p.order is not None else i
                print(
                    f"--- would set Set={_core.kebab(set_id)} Order={shown:02d} on {p.old_path.name} ---"
                )
            else:
                print(f"--- would rename {p.old_path.name} -> {p.new_path.name} ---")
        for e in ref_edits:
            print(
                f"--- would rewrite {e.hits}x [{e.kind}] '{e.old}' -> '{e.new}' in {e.file} ---"
            )
        return ()
    touched: List[str] = []

    def _rel(path: Path) -> str:
        try:
            return path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    # IPD yqv6b7 E-03: Pre-compute every plan's new text in a first pass before any write or
    # git_mv, so an invalid plan raises ValueError before any file in the batch is touched.
    new_texts: List[str] = []
    for i, p in enumerate(plans):
        raw_text = p.old_path.read_text(encoding="utf-8")
        new_text = _set_metadata(
            raw_text,
            set_id=_core.kebab(set_id),
            order=p.order if p.order is not None else i,
            descriptive=descriptive,
            plan_name=p.old_path.name,
        )
        new_texts.append(new_text)

    for p, text in zip(plans, new_texts):
        _core.atomic_write(p.old_path, text, prefix=".plans-refs-")
        if p.old_path != p.new_path:
            src_rel = p.old_path.relative_to(repo_root).as_posix()
            dst_rel = p.new_path.relative_to(repo_root).as_posix()
            _core.git_mv(repo_root, src_rel, dst_rel)
            print(f"renamed {src_rel} -> {dst_rel}")
            # IPD 52zgqr: additive, failure-isolated rename ledger record (never breaks the rename).
            _rh.record_rename(
                repo_root,
                tree="plans",
                verb=verb,
                actor="aw",
                from_name=p.old_path.name,
                to_name=p.new_path.name,
            )
            # The tracked change is at the destination (rename records both delete+add).
            touched.append(src_rel)
            touched.append(dst_rel)
        else:
            touched.append(_rel(p.old_path))
    for w in warnings:
        print(w)
    if update_refs and ref_edits:
        ref_edits = _refs.filter_test_edits_interactive(repo_root, ref_edits, yes=yes)
    if update_refs and ref_edits:
        apply_reference_rewrites(ref_edits)
        for e in ref_edits:
            print(f"rewrote {e.hits}x [{e.kind}] in {e.file}")
            touched.append(_rel(e.file))
    try:
        _idx.run_index(
            argparse.Namespace(
                dir=str(repo_root),
                check=False,
                as_agent=False,
                json=False,
                no_color=True,
                limit=None,
            )
        )
    except Exception:
        pass
    # De-duplicate, order-stable.
    seen: dict = {}
    for t in touched:
        seen.setdefault(t, None)
    return tuple(seen.keys())


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def _dirs(args: argparse.Namespace) -> Tuple[Path, Path]:
    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    # Layout-aware (IPD awretrofit Order 01): resolve .aw/records/plans with a legacy
    # .agents/plans read-fallback, mirroring plans_index._dirs.
    from agent_workflows.record_producers import resolve_record_path

    try:
        plans_dir = resolve_record_path("plans", target_repo=str(repo_root))
    except Exception:
        plans_dir = repo_root / ".aw" / "records" / "plans"
    if not plans_dir.is_dir() and (repo_root / ".agents" / "plans").is_dir():
        plans_dir = repo_root / ".agents" / "plans"
    elif not plans_dir.is_dir() and (repo_root / ".aw" / "records" / "plans").is_dir():
        plans_dir = repo_root / ".aw" / "records" / "plans"
    return repo_root, plans_dir


def run_set_assign(args: argparse.Namespace) -> "MutationResult":
    repo_root, plans_dir = _dirs(args)
    ids = [i.strip() for i in (getattr(args, "ids", None) or []) if i.strip()]
    if not ids:
        print("error: at least one <id6> is required")
        return MutationResult(2)
    # setidlen x75obw E-06 (catalog I-17): the ONE shared setid-length guard, on the PLANS backend of
    # `aw group` (`artifact_types` routes plans here, not to `artifact_rename.run_group_generic`, so
    # guarding only the generic engine would leave the plans tree unguarded). Judged on the KEBABED
    # token, which is what `plan_set_assign` writes.
    from agent_workflows import config as _config

    _setid_err, _setid_warn = _config.validate_setid_length_for_authoring(
        repo_root,
        _core.kebab(getattr(args, "set", "") or ""),
        verb="aw group plans",
    )
    if _setid_err:
        print(f"error: {_setid_err}")
        return MutationResult(2)
    if _setid_warn:
        print(f"note: {_setid_warn}")
    # e3hzyc: pass the flag THROUGH, including its absence. Collapsing None to 0 here was the
    # defect: it renumbered every named plan from zero, so a bare `aw group plans <child> --set X`
    # wrote `- Order: 0` onto a `Kind: child` (and, with --rename, moved it into the `00` filename
    # slot the grammar reserves for an orchestrator). `plan_set_assign` now reads None as "preserve
    # each plan's own Order", the same guarantee `run_mv` has carried since vf03z3.
    plans, err = plan_set_assign(
        plans_dir,
        ids,
        getattr(args, "set", "") or "",
        start_order=getattr(args, "order", None),
        rename=getattr(args, "rename", False),
        allow_invalid_order=bool(getattr(args, "allow_invalid_order", False)),
        repo_root=repo_root,
        force=bool(getattr(args, "force", False)),
    )
    if err:
        print(f"error: {err}")
        return MutationResult(2)
    try:
        touched = apply_renames(
            repo_root,
            plans_dir,
            plans or [],
            getattr(args, "set", ""),
            apply=getattr(args, "apply", False),
            update_refs=not getattr(args, "no_refs", False),
            yes=bool(getattr(args, "yes", False)),
        )
    except ValueError as e:
        print(f"error: {e}")
        return MutationResult(2)
    return MutationResult(0, touched)


def run_mv(args: argparse.Namespace) -> "MutationResult":
    repo_root, plans_dir = _dirs(args)
    selector = getattr(args, "id", "") or getattr(args, "selector", "") or ""
    if not selector:
        print("error: at least one <id6>, <setid>, or <path> is required")
        return MutationResult(2)

    force = bool(getattr(args, "force", False))
    paths, amb_err = _selectors.resolve_for_mutation(
        repo_root, "plans", selector, force=force
    )
    if amb_err:
        print(f"error: {amb_err}")
        return MutationResult(2)
    # IPD 87m438 E-03 / F-15 / OQ-05: rename mutates ONE file; a setid selecting several
    # refuses unless --force, rather than silently renaming an arbitrary member (paths[0]).
    if len(paths) > 1 and not force:
        cand = "\n  ".join(str(p) for p in paths)
        print(
            f"error: selector '{selector}' matched multiple files; rename targets one "
            f"(pass --force to rename the first, or use a unique id6):\n  {cand}"
        )
        return MutationResult(2)
    src = paths[0].resolve()
    if not src.exists():
        print(f"error: no plans artifact matched '{selector}'")
        return MutationResult(2)

    text = src.read_text(encoding="utf-8")
    id6 = _read_id(text)
    if not id6:
        print(f"error: plan '{src.name}' declares no '- Id:'")
        return MutationResult(2)

    m = _SET_LINE_RE.search(text)
    om = _ORDER_LINE_RE.search(text)
    existing_terse = _idx.set_terse_id(m.group(1)) if m else None
    set_id = getattr(args, "set", None) or existing_terse or id6
    # Preserve the plan's existing Order unless --order is explicitly given (vf03z3: a bare rename
    # must NOT clobber Order to 0). Prefer the front-matter Order; fall back to the current filename.
    order = getattr(args, "order", None)
    if order is None:
        if om:
            order = int(om.group(1))
        else:
            parsed = _CLUSTERED_RE.match(src.name)
            order = int(parsed.group("nn")) if parsed else 0
    grammar_err = _order_grammar_error(order)
    if grammar_err:
        print(f"error: plan '{id6}' ({src.name}): {grammar_err}")
        return MutationResult(2)
    # Validity refusal (qhcojn, xvi55d): refuse a resolved Order violating either half of
    # ipd_schema's kind-conditional rule (child must be >= 1, orchestrator must be 0)
    # unless --allow-invalid-order is passed, consulting ipd_schema.validate_metadata.
    # Mirrors plan_set_assign.
    allow_invalid_order = bool(getattr(args, "allow_invalid_order", False))
    order_err = _validate_plan_order(text, order)
    if order_err:
        if allow_invalid_order:
            print(f"note: plan '{id6}' ({src.name}): overridden rule: {order_err}")
        else:
            print(
                f"error: plan '{id6}' ({src.name}): {order_err} (pass --allow-invalid-order to override)"
            )
            return MutationResult(2)
    # Preserve the plan's existing date (vf03z3: a bare rename must NOT recompute the date;
    # 949enf: consult clustered name, then legacy name, then front-matter fallback via _preserved_date).
    new_date = _preserved_date(src.name, text)
    slug = getattr(args, "slug", None)
    new_name = clustered_name(
        date=new_date,
        set_id=set_id,
        order=order,
        id6=id6,
        slug=slug if slug else _slug_of(src.name, id6),
        artifact_type="ipd",
    )
    plan = RenamePlan(src, src.parent / new_name, id6, order=order)
    try:
        touched = apply_renames(
            repo_root,
            plans_dir,
            [plan],
            set_id,
            apply=getattr(args, "apply", False),
            update_refs=not getattr(args, "no_refs", False),
            verb="rename",
            yes=bool(getattr(args, "yes", False)),
        )
    except ValueError as e:
        print(f"error: {e}")
        return MutationResult(2)
    return MutationResult(0, touched)
