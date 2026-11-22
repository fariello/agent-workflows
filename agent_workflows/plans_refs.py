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
from agent_workflows import artifact_meta as _meta
from agent_workflows import artifact_naming as _naming
from agent_workflows import artifact_refs as _refs
from agent_workflows import artifact_types as _types
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

# Writer-side fail-safe regexes retained for `_check_order_lines` (owned by Order 07/11).
_ORDER_LINE_RE = re.compile(r"(?m)^- Order:\s*(-?\d+)\s*$")
_ORDER_LINE_RAW_RE = re.compile(r"(?m)^- Order:[^\r\n]*")
_VALID_DATE_RE = re.compile(r"^(?:\d{8}|\d{4}-\d{2}-\d{2})$")
_SIGNED_INT_RE = re.compile(r"^-?\d+$")


def _read_id(text: str) -> Optional[str]:
    st = _meta.read_text(text, record_type="ipd")
    return st.id6 if (st.id6 and _core.is_valid_id6(st.id6)) else None


def _find_plan_by_id(plans_dir: Path, id6: str) -> Optional[Path]:
    if not plans_dir.is_dir() or not _core.is_valid_id6(id6):
        return None
    pdir_res = plans_dir.resolve()
    ignored_dirs = _core.get_ignored_dirs(plans_dir)
    ctx, records_root, scan_repo = _idx._meta_context_for_plans_dir(pdir_res)
    with _meta.scan_once(), _meta.ephemeral_if_uninitialized():
        res = _meta.query(type="ipd", id6=id6, project_context=ctx)
    for st in res.rows:
        if st.id_derived or not st.path:
            continue
        try:
            abs_p = _meta.source_path(st.path, records_root, scan_repo).resolve()
        except Exception:
            continue
        if (
            abs_p.is_file()
            and abs_p.is_relative_to(pdir_res)
            and abs_p.name not in _idx._EXCLUDE_NAMES
            and not _core.is_ignored_path(abs_p, pdir_res, ignored_dirs)
        ):
            return abs_p
    if pdir_res.name != "plans":
        for p in _idx.plan_files(plans_dir, ignored_dirs=ignored_dirs):
            if _read_id(p.read_text(encoding="utf-8")) == id6:
                return p
    return None


def _set_value(set_id: str, descriptive: Optional[str]) -> str:
    """The `Set:` metadata value: terse id, optionally with a `(descriptive)` parenthetical."""

    return f"{set_id} ({descriptive})" if descriptive else set_id


def _check_order_lines(text: str, *, target: str, require_present: bool) -> None:
    """Enforce the `yqv6b7` E-03 '- Order:' fail-safe before or after metadata rendering."""
    lines = _ORDER_LINE_RAW_RE.findall(text)
    bad_count = (len(lines) != 1) if require_present else (len(lines) > 1)
    if bad_count:
        raise ValueError(
            f"plan '{target}': expected exactly one '- Order:' line after metadata update, "
            f"found {len(lines)}"
        )
    if len(lines) == 1 and not _ORDER_LINE_RE.match(lines[0]):
        raise ValueError(
            f"plan '{target}': expected exactly one '- Order:' line after metadata update, "
            f"found malformed {lines[0]!r}"
        )


def _set_order_events(set_val: str, order: int) -> List[dict]:
    """Build the single `op: 'set'` event updating `Set` and integer `Order`."""
    return [{"op": "set", "fields": {"set": set_val, "order": int(order)}}]


def _set_metadata(
    text: str,
    *,
    set_id: str,
    order: int,
    descriptive: Optional[str] = None,
    plan_name: Optional[str] = None,
) -> str:
    """Return ``text`` with Set/Order set via ``artifact_meta.render_legacy_text``.

    The written `Set:` value is ``<terse-id> (<descriptive>)`` when ``descriptive`` is given, else the
    bare terse id (plans-adopter Order 06 format). Preserves the `yqv6b7` E-03 fail-safe against
    malformed, duplicate, or uninjected `- Order:` lines.
    """

    target = plan_name or _read_id(text) or "plan"
    _check_order_lines(text, target=target, require_present=False)
    events = _set_order_events(_set_value(set_id, descriptive), order)
    render = _meta.LegacyRender(
        "group",
        _core.utc_history_date(),
        "aw",
        history=False,
    )
    updated = _meta.render_legacy_text(
        text,
        events,
        record_type="plans",
        render=render,
        label=target,
    )
    _check_order_lines(updated, target=target, require_present=True)
    return updated


def _plan_date(text: str) -> str:
    st = _meta.read_text(text, record_type="ipd")
    raw = st.fields.get("date") or st.created_day
    if isinstance(raw, str) and _VALID_DATE_RE.fullmatch(raw.strip()):
        val = raw.strip()
        return val.replace("-", "") if "-" in val else val
    return "20260101"


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


class MutationTarget(NamedTuple):
    old_path: str
    new_path: str
    id6: str
    kind: str
    detail: str


class MutationRefEdit(NamedTuple):
    file: str
    kind: str
    old: str
    new: str
    hits: int


class MutationDiagnostic(NamedTuple):
    location: str
    rule: str
    detail: str
    severity: str


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
    * ``targets`` - per-target old/new path pairs, id6, change kind ("rename"|"update"|"noop"), and
      human-meaningful detail suffix.
    * ``applied`` - True when applied, False on preview.
    * ``ref_edits`` - citation rewrites actually applied on apply, or planned on preview.
    * ``diagnostics`` - structured refusal or advisory diagnostics (location, rule, detail, severity).
    * ``notes`` - advisory lines (setid length warning, override note, ref-rewrite warnings, etc.).
    """

    rc: int
    touched_paths: Tuple[str, ...] = ()
    targets: Tuple[MutationTarget, ...] = ()
    applied: bool = False
    ref_edits: Tuple[MutationRefEdit, ...] = ()
    diagnostics: Tuple[MutationDiagnostic, ...] = ()
    notes: Tuple[str, ...] = ()
    generated: Tuple[str, ...] = ()


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


def _preserved_order(
    name: str, text: str = "", *, state: Optional[_meta.State] = None
) -> int:
    """The Order a plan ALREADY has: its front-matter ``- Order:``, else its filename's ``NN``, else 0.

    e3hzyc: this is what a bare ``aw group plans ... --set X`` (no ``--order``) must write, so the
    verb stops renumbering every named plan from zero and parking a ``Kind: child`` in the ``00``
    slot the naming grammar reserves for an orchestrator. The tier order matches ``run_mv``'s
    already-shipped fallback (vf03z3: "a bare rename must NOT clobber Order to 0"), which is
    deliberately left byte-unchanged here rather than refactored into a shared helper.
    """

    if state is not None and state.created_at is not None:
        raw_s = state.fields.get("order") if isinstance(state.fields, dict) else None
        if isinstance(raw_s, int):
            return raw_s
        if isinstance(raw_s, str) and _SIGNED_INT_RE.fullmatch(raw_s.strip()):
            return int(raw_s.strip())
        if isinstance(state.order_nn, int):
            return state.order_nn
    if text:
        st_text = _meta.read_text(text, record_type="ipd")
        raw_t = st_text.fields.get("order")
        if isinstance(raw_t, int):
            return raw_t
        if isinstance(raw_t, str) and _SIGNED_INT_RE.fullmatch(raw_t.strip()):
            return int(raw_t.strip())
    parsed = _CLUSTERED_RE.match(name)
    return int(parsed.group("nn")) if parsed else 0


def _preserved_date(
    name: str, text: str = "", *, state: Optional[_meta.State] = None
) -> str:
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
    if state is not None and isinstance(state.created_day, str):
        val = state.created_day.strip()
        if _VALID_DATE_RE.fullmatch(val):
            return val.replace("-", "") if "-" in val else val
    return _plan_date(text)


def _order_grammar_error(order: int) -> Optional[str]:
    """Validate that the resolved Order is an integer in 0 to 999 inclusive (the 2-3 digit NN facet)."""
    if not isinstance(order, int) or order < 0 or order > 999:
        return (
            f"Order '{order}' is out of grammar: must be an integer from 0 to 999 "
            "(the two- or three-digit NN facet)"
        )
    return None


def _validate_plan_order(
    text: str, order: int, *, state: Optional[_meta.State] = None
) -> Optional[str]:
    """Validate that the resolved Order is permitted for the plan's Kind.

    Consults `ipd_schema.validate_metadata` with the plan's Kind and resolved Order.
    Refuses when Kind is present and the resolved Order is forbidden by schema rules
    (child Order must be an integer >= 1, orchestrator Order must be 0; see qhcojn, xvi55d).
    Silent when Kind is absent.
    """
    from agent_workflows import ipd_schema

    kind: Optional[str] = None
    if state is not None and isinstance(state.fields, dict):
        raw_k = state.fields.get("plan_role")
        kind = str(raw_k).strip() if raw_k else None
    if not kind and text:
        raw_k = _meta.read_text(text, record_type="ipd").fields.get("plan_role")
        kind = str(raw_k).strip() if raw_k else None
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
    notes: Optional[List[str]] = None,
    emit_human: bool = True,
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

    states = _idx._cached_plan_states(plans_dir, include_fields=True)
    plans: List[RenamePlan] = []
    for i, src in enumerate(target_paths):
        if not src.exists():
            return None, f"no plans artifact matched '{src.name}'"
        st = states.get(src.resolve())
        text = src.read_text(encoding="utf-8")
        if st is not None:
            id6 = None if st.id_derived else (st.id6 or None)
        else:
            id6 = _read_id(text)
        if not id6:
            return (
                None,
                f"plan '{src.name}' declares no '- Id:'; add one with `aw ipd sync {src} --apply`",
            )
        order = (
            (start_order + i)
            if start_order is not None
            else _preserved_order(src.name, text, state=st)
        )
        grammar_err = _order_grammar_error(order)
        if grammar_err:
            return None, f"plan '{id6}' ({src.name}): {grammar_err}"
        order_err = _validate_plan_order(text, order, state=st)
        if order_err:
            if allow_invalid_order:
                msg = f"note: plan '{id6}' ({src.name}): overridden rule: {order_err}"
                if emit_human:
                    print(msg)
                if notes is not None:
                    notes.append(msg)
            else:
                return (
                    None,
                    f"plan '{id6}' ({src.name}): {order_err} (pass --allow-invalid-order to override)",
                )
        if rename:
            new_name = clustered_name(
                date=_preserved_date(src.name, text, state=st),
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

    return _naming.legacy_stem_prefix(old_name)


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


def _in_flight_target_error(
    repo_root: Path, src: Path, id6: Optional[str] = None
) -> Optional[str]:
    """Return an error message if `src` is an in-flight plan holding a live begin receipt.

    Reuses `artifact_refs.classify_citing_plans_for_rewrite` as the single liveness predicate.
    """
    _, must_skip = _refs.classify_citing_plans_for_rewrite(repo_root, [src])
    if not must_skip:
        return None
    _, reason = must_skip[0]
    if reason == _refs._CLASSIFY_MISSING_ID_REASON:
        return None
    try:
        rel = src.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        rel = src.as_posix()
    plan_id = id6
    if not plan_id:
        try:
            plan_id = _read_id(src.read_text(encoding="utf-8")) or "unknown"
        except OSError:
            plan_id = "unknown"
    return (
        "cannot rename or regroup in-flight plan %s (%s): %s "
        "(wait for aw ipd finalize, or remove the stale receipt under .aw/state/ipd-lifecycle/ if its session is dead)"
        % (plan_id, rel, reason)
    )


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
    notes: Tuple[str, ...] = (),
    emit_human: bool = True,
) -> MutationResult:
    """Set metadata + (optional) clustering rename + citation rewrite. Preview when not apply.
    update_refs=False (from `--no-refs`, awcmdsurf Order 03) renames the file only, leaving citing
    documents untouched.

    Returns a ``MutationResult`` carrying the touched paths, targets, applied flag, ref_edits,
    and notes. Touched paths are empty on preview."""

    if not emit_human:
        yes = True

    for p in plans:
        err = _in_flight_target_error(repo_root, p.old_path, p.id6)
        if err is not None:
            if emit_human:
                print(f"error: {err}")
            try:
                rel = p.old_path.resolve().relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                rel = p.old_path.as_posix()
            return MutationResult(
                _types.EXIT_CANNOT_RUN,
                applied=False,
                diagnostics=(
                    MutationDiagnostic(
                        location=rel,
                        rule="in-flight-plan",
                        detail=f"error: {err}",
                        severity="error",
                    ),
                ),
                notes=tuple(notes),
            )

    name_map = {
        p.old_path.name: p.new_path.name for p in plans if p.old_path != p.new_path
    }
    ref_edits, warnings = (
        plan_reference_rewrites_with_warnings(repo_root, name_map, plans_dir)
        if (name_map and update_refs)
        else ([], [])
    )
    # IPD 69pxm5 E-03: never rewrite citations inside an in-flight plan (live begin receipt).
    ref_edits, _in_flight_notes = _refs.filter_in_flight_plan_edits(
        repo_root, ref_edits
    )
    warnings = list(warnings) + _in_flight_notes

    def _rel(path: Path) -> str:
        try:
            return path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    if not apply:
        if emit_human:
            for w in warnings:
                print(w)
        targets: List[MutationTarget] = []
        for i, p in enumerate(plans):
            if p.old_path == p.new_path:
                # e3hzyc: preview the Order that would ACTUALLY be written (the plan's own, when
                # `--order` was omitted), not the loop index, or a dry run reports a renumber the
                # apply no longer performs.
                shown = p.order if p.order is not None else i
                if emit_human:
                    print(
                        f"--- would set Set={_core.kebab(set_id)} Order={shown:02d} on {p.old_path.name} ---"
                    )
                targets.append(
                    MutationTarget(
                        old_path=_rel(p.old_path),
                        new_path=_rel(p.old_path),
                        id6=p.id6,
                        kind="update",
                        detail=f"Set: {_core.kebab(set_id)}",
                    )
                )
            else:
                if emit_human:
                    print(
                        f"--- would rename {p.old_path.name} -> {p.new_path.name} ---"
                    )
                targets.append(
                    MutationTarget(
                        old_path=_rel(p.old_path),
                        new_path=_rel(p.new_path),
                        id6=p.id6,
                        kind="rename",
                        detail=f"-> {p.new_path.name}",
                    )
                )
        for e in ref_edits:
            if emit_human:
                print(
                    f"--- would rewrite {e.hits}x [{e.kind}] '{e.old}' -> '{e.new}' in {e.file} ---"
                )
        mutation_ref_edits = tuple(
            MutationRefEdit(
                file=_rel(e.file) if isinstance(e.file, Path) else str(e.file),
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
            targets=tuple(targets),
            applied=False,
            ref_edits=mutation_ref_edits,
            diagnostics=(),
            notes=tuple(notes) + tuple(warnings),
        )

    touched: List[str] = []
    targets_applied: List[MutationTarget] = []

    meta_ctx = _meta.legacy_context(repo_root)
    meta_render = _meta.LegacyRender(
        verb,
        _core.utc_history_date(),
        "aw",
        history=False,
    )
    set_val = _set_value(_core.kebab(set_id), descriptive)

    # IPD yqv6b7 E-03 / fnu6kw E-01: Pre-validate every plan in a first pass (both the - Order:
    # fail-safe and artifact_meta.append(..., dry_run=True)) before any write, git_mv, or
    # rename-ledger record is touched.
    prepared: List[Tuple[RenamePlan, _meta.LegacyTarget, List[dict]]] = []
    for i, p in enumerate(plans):
        raw_text = p.old_path.read_text(encoding="utf-8")
        target_label = p.old_path.name or _read_id(raw_text) or "plan"
        _check_order_lines(raw_text, target=target_label, require_present=False)
        order_val = p.order if p.order is not None else i
        events = _set_order_events(set_val, order_val)
        meta_target = _meta.LegacyTarget(p.old_path, "plans", id6=p.id6)
        preview = _meta.append(
            meta_target,
            events,
            dry_run=True,
            legacy_render=meta_render,
            repo_root=repo_root,
            project_context=meta_ctx,
        )
        _check_order_lines(preview.text, target=target_label, require_present=True)
        prepared.append((p, meta_target, events))

    for p, meta_target, events in prepared:
        _meta.append(
            meta_target,
            events,
            legacy_render=meta_render,
            repo_root=repo_root,
            project_context=meta_ctx,
        )
        if p.old_path != p.new_path:
            src_rel = p.old_path.relative_to(repo_root).as_posix()
            dst_rel = p.new_path.relative_to(repo_root).as_posix()
            _core.git_mv(repo_root, src_rel, dst_rel)
            if emit_human:
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
            targets_applied.append(
                MutationTarget(
                    old_path=src_rel,
                    new_path=dst_rel,
                    id6=p.id6,
                    kind="rename",
                    detail=f"-> {p.new_path.name}",
                )
            )
        else:
            old_rel = _rel(p.old_path)
            touched.append(old_rel)
            targets_applied.append(
                MutationTarget(
                    old_path=old_rel,
                    new_path=old_rel,
                    id6=p.id6,
                    kind="update",
                    detail=f"Set: {_core.kebab(set_id)}",
                )
            )
    if emit_human:
        for w in warnings:
            print(w)
    if update_refs and ref_edits:
        ref_edits = _refs.filter_test_edits_interactive(repo_root, ref_edits, yes=yes)
    if update_refs and ref_edits:
        apply_reference_rewrites(ref_edits)
        for e in ref_edits:
            if emit_human:
                print(f"rewrote {e.hits}x [{e.kind}] in {e.file}")
            touched.append(_rel(e.file))
    generated: List[str] = []
    try:
        rc_idx = _idx.run_index(
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
        if rc_idx == 0:
            for mf in (plans_dir / "INDEX.json", plans_dir / "INDEX.md"):
                if mf.exists():
                    generated.append(_rel(mf))
    except Exception:
        pass
    # De-duplicate, order-stable.
    seen: dict = {}
    for t in touched:
        seen.setdefault(t, None)
    mutation_applied_ref_edits = tuple(
        MutationRefEdit(
            file=_rel(e.file) if isinstance(e.file, Path) else str(e.file),
            kind=e.kind,
            old=e.old,
            new=e.new,
            hits=e.hits,
        )
        for e in (ref_edits if update_refs else [])
    )
    return MutationResult(
        0,
        touched_paths=tuple(seen.keys()),
        targets=tuple(targets_applied),
        applied=True,
        ref_edits=mutation_applied_ref_edits,
        diagnostics=(),
        notes=tuple(notes) + tuple(warnings),
        generated=tuple(generated),
    )


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def _dirs(args: argparse.Namespace) -> Tuple[Path, Path]:
    from agent_workflows.project_context import (
        resolve_verb_repo_root,
        project_records_dir,
        has_stored_records_placement,
    )

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    # Layout-aware (IPD awretrofit Order 01): resolve .aw/records/plans with a legacy
    # .agents/plans read-fallback, mirroring plans_index._dirs.
    from agent_workflows.record_producers import resolve_record_path

    modern_plans = project_records_dir(repo_root) / "plans"
    if has_stored_records_placement(repo_root):
        plans_dir = modern_plans
    else:
        try:
            plans_dir = resolve_record_path("plans", target_repo=str(repo_root))
        except Exception:
            plans_dir = modern_plans
    if not plans_dir.is_dir() and (repo_root / ".agents" / "plans").is_dir():
        plans_dir = repo_root / ".agents" / "plans"
    elif not plans_dir.is_dir() and modern_plans.is_dir():
        plans_dir = modern_plans
    return repo_root, plans_dir


def run_set_assign(
    args: argparse.Namespace, *, emit_human: Optional[bool] = None
) -> "MutationResult":
    if emit_human is None:
        emit_human = getattr(args, "emit_human", True)
    repo_root, plans_dir = _dirs(args)
    ids = [i.strip() for i in (getattr(args, "ids", None) or []) if i.strip()]
    if not ids:
        msg = "error: at least one <id6> is required"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location="ids",
                    rule="missing-target",
                    detail=msg,
                    severity="error",
                ),
            ),
        )
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
    collected_notes: List[str] = []
    if _setid_warn:
        msg = f"note: {_setid_warn}"
        if emit_human:
            print(msg)
        collected_notes.append(msg)
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
        notes=collected_notes,
        emit_human=emit_human,
    )
    if err:
        msg = f"error: {err}"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location="set",
                    rule="plan-error",
                    detail=msg,
                    severity="error",
                ),
            ),
        )
    try:
        return apply_renames(
            repo_root,
            plans_dir,
            plans or [],
            getattr(args, "set", ""),
            apply=getattr(args, "apply", False),
            update_refs=not getattr(args, "no_refs", False),
            yes=bool(getattr(args, "yes", False)),
            notes=tuple(collected_notes),
            emit_human=emit_human,
        )
    except ValueError as e:
        msg = f"error: {e}"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location="set",
                    rule="metadata-order-error",
                    detail=msg,
                    severity="error",
                ),
            ),
        )


def run_mv(
    args: argparse.Namespace, *, emit_human: Optional[bool] = None
) -> "MutationResult":
    if emit_human is None:
        emit_human = getattr(args, "emit_human", True)
    repo_root, plans_dir = _dirs(args)
    selector = getattr(args, "id", "") or getattr(args, "selector", "") or ""
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

    force = bool(getattr(args, "force", False))
    paths, amb_err = _selectors.resolve_for_mutation(
        repo_root, "plans", selector, force=force
    )
    if amb_err:
        msg = f"error: {amb_err}"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location=selector,
                    rule="ambiguous-selector",
                    detail=msg,
                    severity="error",
                ),
            ),
        )
    # IPD 87m438 E-03 / F-15 / OQ-05: rename mutates ONE file; a setid selecting several
    # refuses unless --force, rather than silently renaming an arbitrary member (paths[0]).
    if len(paths) > 1 and not force:
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
                    location=selector,
                    rule="multiple-targets",
                    detail=msg,
                    severity="error",
                ),
            ),
        )
    src = paths[0].resolve()
    if not src.exists():
        msg = f"error: no plans artifact matched '{selector}'"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location=selector,
                    rule="not-found",
                    detail=msg,
                    severity="error",
                ),
            ),
        )

    states = _idx._cached_plan_states(plans_dir, include_fields=True)
    st = states.get(src.resolve())
    text = src.read_text(encoding="utf-8")
    if st is not None:
        id6 = None if st.id_derived else (st.id6 or None)
    else:
        id6 = _read_id(text)
    if not id6:
        msg = f"error: plan '{src.name}' declares no '- Id:'; add one with `aw ipd sync {src} --apply`"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location=src.name,
                    rule="missing-id",
                    detail=msg,
                    severity="error",
                ),
            ),
        )

    if st is not None:
        existing_terse = _idx._state_set_id(st)
    else:
        existing_terse = _idx.set_terse_id(
            _meta.read_text(text, record_type="ipd").legacy_raw_set
        )
    set_id = getattr(args, "set", None) or existing_terse or id6
    # Preserve the plan's existing Order unless --order is explicitly given (vf03z3: a bare rename
    # must NOT clobber Order to 0). Prefer the front-matter Order; fall back to the current filename.
    order = getattr(args, "order", None)
    if order is None:
        order = _preserved_order(src.name, text, state=st)
    grammar_err = _order_grammar_error(order)
    if grammar_err:
        msg = f"error: plan '{id6}' ({src.name}): {grammar_err}"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location=src.name,
                    rule="order-grammar-error",
                    detail=msg,
                    severity="error",
                ),
            ),
        )
    # Validity refusal (qhcojn, xvi55d): refuse a resolved Order violating either half of
    # ipd_schema's kind-conditional rule (child must be >= 1, orchestrator must be 0)
    # unless --allow-invalid-order is passed, consulting ipd_schema.validate_metadata.
    # Mirrors plan_set_assign.
    allow_invalid_order = bool(getattr(args, "allow_invalid_order", False))
    order_err = _validate_plan_order(text, order, state=st)
    collected_notes: List[str] = []
    if order_err:
        if allow_invalid_order:
            msg = f"note: plan '{id6}' ({src.name}): overridden rule: {order_err}"
            if emit_human:
                print(msg)
            collected_notes.append(msg)
        else:
            msg = f"error: plan '{id6}' ({src.name}): {order_err} (pass --allow-invalid-order to override)"
            if emit_human:
                print(msg)
            return MutationResult(
                2,
                diagnostics=(
                    MutationDiagnostic(
                        location=src.name,
                        rule="invalid-order",
                        detail=msg,
                        severity="error",
                    ),
                ),
            )
    # Preserve the plan's existing date (vf03z3: a bare rename must NOT recompute the date;
    # 949enf: consult clustered name, then legacy name, then front-matter fallback via _preserved_date).
    new_date = _preserved_date(src.name, text, state=st)
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
        return apply_renames(
            repo_root,
            plans_dir,
            [plan],
            set_id,
            apply=getattr(args, "apply", False),
            update_refs=not getattr(args, "no_refs", False),
            verb="rename",
            yes=bool(getattr(args, "yes", False)),
            notes=tuple(collected_notes),
            emit_human=emit_human,
        )
    except ValueError as e:
        msg = f"error: {e}"
        if emit_human:
            print(msg)
        return MutationResult(
            2,
            diagnostics=(
                MutationDiagnostic(
                    location=src.name,
                    rule="metadata-order-error",
                    detail=msg,
                    severity="error",
                ),
            ),
        )
