"""Step-6 field census, round-trip verifier, and leak scan for migration m0001.

Implements spec 4sd62s Sections 5.2 step 6, 5.2a items 1/3/5, AC-10, AC-16, and AC-20:
- Repository-agnostic field census across bullet metadata, research YAML, leading
  ``aw-prompt`` comments, review metadata, and D177 filename facets.
- Direct ``artifact_meta.replay`` round-trip verification (avoiding legacy-loader
  ``check_freshness`` scans), in-file mirror parsing across all record types and
  reviews, byte-for-byte recovery of legacy fields, inline history lines, sidecar JSON
  objects, and review rounds, legacy-filename absence check, and plan ``(set, order)``
  collision check.
- ``leak_sanitizer.scan_text`` scan over every generated log and rewritten mirror.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple, Union

from agent_workflows import (
    artifact_meta,
    artifact_naming,
    layout_migration,
    leak_sanitizer,
    project_context,
)
from agent_workflows.migrations import m0001_convert, m0001_discover, m0001_renames

_SKIP_DIRNAMES = m0001_discover.EXCLUDED_DIRNAMES
_SKIP_FILENAMES = frozenset({"README.md", "STATUS.md"})


def _is_oq02_excluded_template(rel_posix: str, *, text: Optional[str] = None) -> bool:
    """Return True if ``rel_posix`` (records-root-relative) is an OQ-02 excluded template."""
    return m0001_discover.is_excluded_template(rel_posix, Path(rel_posix).name, text)


def _discover_present_templates(records_root: Path) -> List[str]:
    """Return sorted records-root-relative paths of present OQ-02 excluded templates."""
    if not records_root.is_dir():
        return []
    inv = m0001_discover.discover(records_root, records_root=records_root)
    return sorted(u.rel_path for u in inv.excluded if u.category == "excluded-template")


def _discover_non_leading_research_prompt_comments(records_root: Path) -> List[str]:
    """Return sorted relative paths of research files embedding ``<!-- aw-prompt:`` below YAML."""
    research_dir = records_root / "research"
    if not research_dir.is_dir():
        return []
    found: List[str] = []
    for cur_dir, dirs, files in os.walk(research_dir):
        dirs[:] = sorted(d for d in dirs if not d.endswith(".data"))
        cur_path = Path(cur_dir)
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            if fname in _SKIP_FILENAMES or fname.startswith("INDEX."):
                continue
            fpath = cur_path / fname
            rel = fpath.relative_to(records_root).as_posix()
            if _is_oq02_excluded_template(rel):
                continue
            text = fpath.read_text(encoding="utf-8", errors="replace")
            body = artifact_meta._strip_leading_yaml_mirror(text)
            if "<!-- aw-prompt:" in body or "<!-- aw-managed-prompt:" in body:
                found.append(rel)
    return sorted(found)


def _destination_label(dest: m0001_convert.FieldDestination) -> Tuple[str, str]:
    """Return ``(destination_kind, destination_detail)`` for census reporting."""
    if dest.kind == "log_field":
        return "log_field", dest.target
    if dest.kind == "body_section":
        return "body_section", dest.target
    if dest.kind == "review_event":
        return "review_event", dest.target
    if dest.kind == "review_mirror":
        return "review_mirror", dest.target
    if dest.kind == "identity":
        return "identity", dest.target
    if dest.kind == "status":
        return "status", dest.target
    if dest.kind in ("body_prose", "prompt_body", "comment_value"):
        return f"drop ({dest.kind})", dest.note or dest.target
    return dest.kind, dest.target


def _read_checkpoint_fields(log_path: Path) -> Optional[Dict[str, Any]]:
    """Read the seq-0 checkpoint ``fields`` dictionary from a converted ``meta/<id6>.jsonl`` log."""
    if not log_path.is_file():
        return None
    for raw in log_path.read_text(encoding="utf-8").splitlines(keepends=True):
        if not raw.strip():
            continue
        ev = artifact_meta.decode_line(raw)
        if ev.get("op") == "checkpoint":
            fields = ev.get("fields")
            return dict(fields) if isinstance(fields, dict) else {}
    return None


def _collect_converted_records(
    converted_records_root: Path,
) -> List[Tuple[str, str, str, Path]]:
    """Return ``[(rel_path, id6, art_type, abs_path), ...]`` from ``converted_records_root``."""
    out: List[Tuple[str, str, str, Path]] = []
    for rec_path in m0001_convert._walk_target_records(
        converted_records_root, record_types=m0001_convert.ALL_RECORD_TYPES
    ):
        rel_path = rec_path.relative_to(converted_records_root).as_posix()
        top_dir = Path(rel_path).parts[0] if Path(rel_path).parts else ""
        art_type = m0001_convert.TREE_DIR_TO_TYPE.get(top_dir, "ipd")
        text = rec_path.read_text(encoding="utf-8")
        id6: Optional[str] = None
        if art_type == "prompt":
            try:
                id6 = str(artifact_meta.parse_staged_prompt_mirror(text)["id"])
            except ValueError:
                id6 = None
        elif art_type in ("walkthrough", "roadmap"):
            try:
                id6 = str(artifact_meta.parse_walkthrough_mirror(text)["id"])
            except ValueError:
                id6 = None
        else:
            try:
                id6 = str(
                    artifact_meta.parse_artifact_mirror(
                        text, allow_statusless=(art_type == "research")
                    )["id"]
                )
            except ValueError:
                id6 = None
        if id6 is None:
            art_row, _ = artifact_meta.load_legacy_artifact(
                rec_path, converted_records_root, text=text
            )
            id6 = str(art_row["id6"])
            art_type = str(art_row["type"])
        out.append((rel_path, id6, art_type, rec_path))
    return out


def populate_description_counts(
    census: Dict[str, Any],
    converted_records_root: Union[str, Path],
    *,
    deliberate_description_absences: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Update ``census`` description counts from converted ``meta/<id6>.jsonl`` checkpoints."""
    post_root = Path(converted_records_root)
    meta_dir = post_root / "meta"
    absences_map = dict(deliberate_description_absences or {})
    with_description_count = 0
    without_description_count = 0
    missing_description_paths: List[str] = []
    deliberate_absences_recorded: Dict[str, str] = {}

    if meta_dir.is_dir():
        for rel_path, id6, _art_type, _abs_path in _collect_converted_records(
            post_root
        ):
            cp_fields = _read_checkpoint_fields(meta_dir / f"{id6}.jsonl")
            sd = cp_fields.get("short_description") if cp_fields else None
            if isinstance(sd, str) and sd.strip():
                with_description_count += 1
            elif id6 in absences_map:
                deliberate_absences_recorded[rel_path] = absences_map[id6]
            elif rel_path in absences_map:
                deliberate_absences_recorded[rel_path] = absences_map[rel_path]
            else:
                without_description_count += 1
                missing_description_paths.append(rel_path)
    census["with_description_count"] = with_description_count
    census["without_description_count"] = without_description_count
    census["missing_description_paths"] = sorted(missing_description_paths)
    census["deliberate_description_absences"] = deliberate_absences_recorded
    return census


def build_field_census(
    repo: Union[str, Path],
    *,
    records_root: Optional[Union[str, Path]] = None,
    pre_conversion_records_root: Optional[Union[str, Path]] = None,
    converted_records_root: Optional[Union[str, Path]] = None,
    sidecar_summary: Optional[Mapping[str, Any]] = None,
    orphan_counts: Optional[Mapping[str, int]] = None,
    rename_summary: Optional[Mapping[str, Any]] = None,
    citation_summary: Optional[Mapping[str, Any]] = None,
    deliberate_description_absences: Optional[Mapping[str, str]] = None,
    layout_stage_summary: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the step-6 repository-agnostic field census (4sd62s AC-20, 5.2 step 6, 5.2a).

    Zero repository-specific ``id6`` or count constants are used; every metric is
    computed from ``records_root`` (or ``pre_conversion_records_root`` /
    ``converted_records_root`` when inspecting a scratch conversion).
    """
    repo_path = Path(repo)
    resolved_default = (
        Path(records_root)
        if records_root is not None
        else project_context.project_records_dir(repo_path)
    )
    legacy_root = (
        Path(pre_conversion_records_root)
        if pre_conversion_records_root is not None
        else resolved_default
    )
    post_root = (
        Path(converted_records_root)
        if converted_records_root is not None
        else resolved_default
    )

    # Aggregated keyed by (source_kind, field_name, dest_kind, dest_target)
    field_agg: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    distinct_bullet_names: Set[str] = set()
    refusals: List[Dict[str, str]] = []
    plan_role_counts: Dict[str, int] = {}
    absent_kind_count = 0
    prompts_without_comment: List[str] = []
    legacy_short_desc_count = 0
    legacy_total_records = 0

    def _record_field(
        source_kind: str,
        field_name: str,
        art_type: str,
        dest_kind: str,
        dest_target: str,
    ) -> None:
        key = (source_kind, field_name, dest_kind, dest_target)
        entry = field_agg.get(key)
        if entry is None:
            entry = {
                "source_kind": source_kind,
                "field": field_name,
                "destination_kind": dest_kind,
                "destination": dest_target,
                "count": 0,
                "record_types": set(),
            }
            field_agg[key] = entry
        entry["count"] += 1
        entry["record_types"].add(art_type)

    def _classify_field(
        art_type: str, field_name: str, *, historical_ipd: bool = False
    ) -> Optional[m0001_convert.FieldDestination]:
        return m0001_convert.classify_field(
            art_type, field_name, historical_ipd=historical_ipd
        )

    target_files = m0001_convert._walk_target_records(
        legacy_root, record_types=m0001_convert.ALL_RECORD_TYPES
    )
    for rec_path in target_files:
        rel_path = rec_path.relative_to(legacy_root).as_posix()
        text = rec_path.read_text(encoding="utf-8")
        art_row, _ = artifact_meta.load_legacy_artifact(
            rec_path, legacy_root, text=text
        )
        art_type = str(art_row["type"])
        legacy_total_records += 1

        # D177 filename facets
        art_fields = art_row.get("fields") or {}
        for facet_key in ("ace", "model", "research_kind"):
            if art_fields.get(facet_key):
                _record_field("facet", facet_key, art_type, "log_field", facet_key)

        if art_type == "prompt":
            pm = m0001_convert._parse_prompt_comment(text)
            if not pm:
                prompts_without_comment.append(rel_path)
            if pm.get("Short-Description"):
                legacy_short_desc_count += 1
            for k, v in pm.items():
                dest = _classify_field("prompt", k)
                if dest is None:
                    refusals.append(
                        {
                            "kind": "unknown-field",
                            "path": rel_path,
                            "record_type": art_type,
                            "field": k,
                            "detail": f"Unknown prompt comment field {k!r}",
                        }
                    )
                    continue
                dk, dt = _destination_label(dest)
                _record_field("prompt_comment", k, art_type, dk, dt)
                if k == "Created" and v and m0001_convert._normalize_day(v) is None:
                    refusals.append(
                        {
                            "kind": "unparseable-value",
                            "path": rel_path,
                            "record_type": art_type,
                            "field": k,
                            "detail": f"Unparseable Created date {v!r}",
                        }
                    )
            continue

        if art_type == "research":
            parsed_fm = artifact_meta.front_matter_mapping(text)
            if parsed_fm is None:
                yaml_map, _ = artifact_meta._parse_yaml_front_matter(text)
                if text.lstrip().startswith("---") and not yaml_map:
                    refusals.append(
                        {
                            "kind": "unparseable-value",
                            "path": rel_path,
                            "record_type": art_type,
                            "field": "frontmatter",
                            "detail": "Malformed research YAML front matter",
                        }
                    )
                ordered_pairs: List[Tuple[str, Any]] = list(yaml_map.items())
                fm_dict: Dict[str, Any] = dict(yaml_map)
            else:
                ordered_pairs = list(parsed_fm.items())
                fm_dict = dict(parsed_fm)

            if fm_dict.get("short-description"):
                legacy_short_desc_count += 1
            for k, v in ordered_pairs:
                dest = _classify_field("research", k)
                if dest is None:
                    refusals.append(
                        {
                            "kind": "unknown-field",
                            "path": rel_path,
                            "record_type": art_type,
                            "field": k,
                            "detail": f"Unknown research YAML field {k!r}",
                        }
                    )
                    continue
                dk, dt = _destination_label(dest)
                _record_field("yaml", k, art_type, dk, dt)
                if k == "order" and v is not None and str(v).strip():
                    try:
                        int(str(v).strip())
                    except ValueError:
                        refusals.append(
                            {
                                "kind": "unparseable-value",
                                "path": rel_path,
                                "record_type": art_type,
                                "field": k,
                                "detail": f"Unparseable integer order {v!r}",
                            }
                        )
                if k == "created" and v is not None and str(v).strip():
                    if m0001_convert._normalize_day(str(v)) is None:
                        refusals.append(
                            {
                                "kind": "unparseable-value",
                                "path": rel_path,
                                "record_type": art_type,
                                "field": k,
                                "detail": f"Unparseable created date {v!r}",
                            }
                        )
            continue

        # Standard bullet-block records (ipd, backlog, release, spec, walkthrough, roadmap)
        raw_bullets, ordered_pairs_b, _ = m0001_convert._parse_multiline_bullets(text)
        if raw_bullets.get("Short-Description"):
            legacy_short_desc_count += 1

        if art_type == "ipd":
            kind_val = raw_bullets.get("Kind")
            if kind_val is None or not kind_val.strip():
                absent_kind_count += 1
            else:
                role = kind_val.strip()
                plan_role_counts[role] = plan_role_counts.get(role, 0) + 1

        historical_ipd = (art_type == "ipd") and m0001_convert.is_historical_ipd(
            rel_path, raw_bullets.get("Status")
        )
        for k, v in ordered_pairs_b:
            distinct_bullet_names.add(k)
            dest = _classify_field(art_type, k, historical_ipd=historical_ipd)
            if dest is None:
                refusals.append(
                    {
                        "kind": "unknown-field",
                        "path": rel_path,
                        "record_type": art_type,
                        "field": k,
                        "detail": f"Unknown bullet field {k!r} on {art_type}",
                    }
                )
                continue
            dk, dt = _destination_label(dest)
            _record_field("bullet", k, art_type, dk, dt)

            if k == "Item-Dependencies":
                try:
                    artifact_meta.parse_item_dependencies_field(v)
                except Exception as exc:
                    refusals.append(
                        {
                            "kind": "unparseable-value",
                            "path": rel_path,
                            "record_type": art_type,
                            "field": k,
                            "detail": f"Unparseable Item-Dependencies {v!r}: {exc}",
                        }
                    )
            elif k == "Order" and v.strip():
                try:
                    int(v.strip())
                except ValueError:
                    refusals.append(
                        {
                            "kind": "unparseable-value",
                            "path": rel_path,
                            "record_type": art_type,
                            "field": k,
                            "detail": f"Unparseable integer Order {v!r}",
                        }
                    )
            elif k == "Date" and v.strip():
                if m0001_convert._normalize_day(v) is None:
                    refusals.append(
                        {
                            "kind": "unparseable-value",
                            "path": rel_path,
                            "record_type": art_type,
                            "field": k,
                            "detail": f"Unparseable Date {v!r}",
                        }
                    )

    # Review files under legacy_root / "reviews"
    reviews_dir = legacy_root / "reviews"
    review_count = 0
    if reviews_dir.is_dir():
        for cur_dir, dirs, files in os.walk(reviews_dir):
            dirs[:] = sorted(d for d in dirs if not d.endswith(".data"))
            cur_path = Path(cur_dir)
            for fname in sorted(files):
                if not fname.endswith(".review.md"):
                    continue
                if fname in _SKIP_FILENAMES or fname.startswith("INDEX."):
                    continue
                fpath = cur_path / fname
                rel_path = fpath.relative_to(legacy_root).as_posix()
                review_count += 1
                text = fpath.read_text(encoding="utf-8")
                work_text = artifact_meta._strip_leading_yaml_mirror(text)
                _, rev_pairs, _ = m0001_convert._parse_multiline_bullets(work_text)
                for k, _v in rev_pairs:
                    distinct_bullet_names.add(k)
                    dest = _classify_field("review", k)
                    if dest is None:
                        refusals.append(
                            {
                                "kind": "unknown-field",
                                "path": rel_path,
                                "record_type": "review",
                                "field": k,
                                "detail": f"Unknown review bullet field {k!r}",
                            }
                        )
                        continue
                    dk, dt = _destination_label(dest)
                    _record_field("bullet", k, "review", dk, dt)

    # Description accounting from converted meta/<id6>.jsonl if present, else legacy count.
    absences_map = dict(deliberate_description_absences or {})
    meta_dir = post_root / "meta"
    with_description_count = 0
    without_description_count = 0
    missing_description_paths: List[str] = []
    deliberate_absences_recorded: Dict[str, str] = {}

    if meta_dir.is_dir():
        converted_recs = _collect_converted_records(post_root)
        for rel_path, id6, _art_type, _abs_path in converted_recs:
            cp_fields = _read_checkpoint_fields(meta_dir / f"{id6}.jsonl")
            sd = cp_fields.get("short_description") if cp_fields else None
            if isinstance(sd, str) and sd.strip():
                with_description_count += 1
            elif id6 in absences_map:
                deliberate_absences_recorded[rel_path] = absences_map[id6]
            elif rel_path in absences_map:
                deliberate_absences_recorded[rel_path] = absences_map[rel_path]
            else:
                without_description_count += 1
                missing_description_paths.append(rel_path)
    else:
        with_description_count = legacy_short_desc_count
        without_description_count = max(
            0, legacy_total_records - legacy_short_desc_count
        )

    inv = m0001_discover.discover(repo_path, records_root=legacy_root)

    # Sidecar status & orphan counts
    sc_info = dict(sidecar_summary or {})
    sc_expected = (
        sc_info.get("expected") if "expected" in sc_info else inv.sidecar_expected
    )
    sc_present = sc_info.get("present") if "present" in sc_info else inv.sidecar_present
    if sc_expected is False and sc_present is False:
        sidecar_status_text = "no sidecar (none expected)"
        norm_orphans: Dict[str, int] = {}
    else:
        sidecar_status_text = str(sc_info.get("status") or "unknown")
        norm_orphans = {
            str(k): int(v) for k, v in sorted((orphan_counts or {}).items())
        }

    if layout_stage_summary is not None:
        layout_stage_doc: Dict[str, Any] = dict(layout_stage_summary)
    else:
        layout_stage_doc = {"status": "skipped", "reason": "already on .aw/"}

    field_rows: List[Dict[str, Any]] = []
    for entry in sorted(
        field_agg.values(),
        key=lambda e: (
            e["source_kind"],
            e["field"].lower(),
            e["field"],
            e["destination_kind"],
            e["destination"],
        ),
    ):
        field_rows.append(
            {
                "source_kind": entry["source_kind"],
                "field": entry["field"],
                "destination_kind": entry["destination_kind"],
                "destination": entry["destination"],
                "count": entry["count"],
                "record_types": sorted(entry["record_types"]),
            }
        )

    present_templates = sorted(
        u.rel_path for u in inv.excluded if u.category == "excluded-template"
    )
    unclassifiable_files = [
        {
            "path": u.rel_path,
            "repo_path": u.repo_rel_path,
            "source_tree": u.source_tree,
            "reason": u.reason,
        }
        for u in inv.unclassifiable
    ]
    disc_by_rel = {r.rel_path: r for r in inv.records}
    minted_records: List[Dict[str, Any]] = []
    for ent in (rename_summary or {}).get("entries") or []:
        if not isinstance(ent, Mapping) or not ent.get("minted"):
            continue
        old_rel = str(ent.get("old_rel") or "")
        disc = disc_by_rel.get(old_rel)
        minted_records.append(
            {
                "id6": ent.get("id6"),
                "old_rel": old_rel,
                "new_rel": ent.get("new_rel"),
                "record_type": disc.record_type if disc else "",
                "status": disc.status if disc else None,
                "status_source": disc.status_source if disc else None,
                "title": disc.title if disc else None,
                "set_id": ent.get("set_id"),
                "order": ent.get("order"),
            }
        )

    non_leading_research_comments = _discover_non_leading_research_prompt_comments(
        legacy_root
    )

    return {
        "records_root": str(legacy_root),
        "record_count": legacy_total_records,
        "review_count": review_count,
        "distinct_bullet_count": len(distinct_bullet_names),
        "distinct_bullet_names": sorted(distinct_bullet_names),
        "field_rows": field_rows,
        "refusals": refusals,
        "unknown_field_refusal_count": sum(
            1 for r in refusals if r["kind"] == "unknown-field"
        ),
        "unparseable_value_refusal_count": sum(
            1 for r in refusals if r["kind"] == "unparseable-value"
        ),
        "plan_role_counts": dict(sorted(plan_role_counts.items())),
        "absent_kind_count": absent_kind_count,
        "prompts_without_comment": sorted(prompts_without_comment),
        "prompts_without_comment_count": len(prompts_without_comment),
        "sidecar_status": sidecar_status_text,
        "orphan_counts": norm_orphans,
        "orphan_record_count": sum(norm_orphans.values()),
        "excluded_templates": present_templates,
        "unclassifiable_files": unclassifiable_files,
        "unclassifiable_count": len(unclassifiable_files),
        "minted_records": minted_records,
        "minted_record_count": len(minted_records),
        "non_leading_research_prompt_comments": non_leading_research_comments,
        "with_description_count": with_description_count,
        "without_description_count": without_description_count,
        "missing_description_paths": sorted(missing_description_paths),
        "deliberate_description_absences": deliberate_absences_recorded,
        "renames": dict(rename_summary or {}),
        "citations": dict(citation_summary or {}),
        "layout_stage": layout_stage_doc,
    }


def _legacy_field_pairs_for_record(
    rec_path: Path,
    records_root: Path,
    art_type: str,
    *,
    text: Optional[str] = None,
) -> Tuple[
    Optional[str],
    Dict[str, Any],
    List[Tuple[str, Any]],
    List[Tuple[str, Optional[str]]],
]:
    """Extract ``(status, raw_fields, ordered_pairs, inline_history)`` from a legacy record."""
    if text is None:
        text = rec_path.read_text(encoding="utf-8")
    is_statusless = art_type in ("walkthrough", "roadmap")

    if art_type == "prompt":
        raw_fields = m0001_convert._parse_prompt_comment(text)
        ordered_pairs: List[Tuple[str, Any]] = list(raw_fields.items())
    elif art_type == "research":
        parsed_fm = artifact_meta.front_matter_mapping(text)
        if parsed_fm is None:
            yaml_map, _ = artifact_meta._parse_yaml_front_matter(text)
            raw_fields = dict(yaml_map)
            ordered_pairs = list(raw_fields.items())
        else:
            raw_fields = dict(parsed_fm)
            ordered_pairs = list(parsed_fm.items())
    else:
        raw_fields, ordered_pairs_b, _ = m0001_convert._parse_multiline_bullets(text)
        ordered_pairs = list(ordered_pairs_b)

    status: Optional[str] = None
    if not is_statusless:
        status_raw = raw_fields.get("Status") or raw_fields.get("status")
        if isinstance(status_raw, str) and status_raw.strip():
            toks = status_raw.strip().split()
            if toks:
                status = toks[0].lower()
        if not status and art_type != "research":
            status = rec_path.parent.name

    hist_span = m0001_convert._find_history_section_span(text.splitlines(keepends=True))
    hist_entries = hist_span[2] if hist_span is not None else []
    return status, raw_fields, ordered_pairs, hist_entries


def verify_round_trip(
    repo: Union[str, Path],
    *,
    pre_conversion_records_root: Union[str, Path],
    converted_records_root: Union[str, Path],
    post_step3_records_root: Optional[Union[str, Path]] = None,
    rename_map: Optional[Mapping[str, str]] = None,
    sidecar_events: Optional[Mapping[str, Sequence[Dict[str, Any]]]] = None,
    unmapped_plan_duplicates: Optional[Sequence[Any]] = None,
) -> Dict[str, Any]:
    """Run the step-6 round-trip verifier and leak scan (4sd62s AC-10, 5.2 step 6, AC-16).

    Replays every generated ``meta/<id6>.jsonl`` log directly via
    ``artifact_meta.replay(id6, art_type, lines, records_root=converted_records_root)``,
    parses every rewritten record/review mirror, verifies byte-for-byte recovery of
    legacy fields (against ``post_step3_records_root`` when provided, or
    ``pre_conversion_records_root`` otherwise), inline history lines (always
    against pre-Step-3 ``pre_conversion_records_root``), sidecar JSON objects, and
    migrated review rounds, confirms zero legacy-timestamp filenames remain
    (excluding OQ-02 templates) and no newly created plan ``(set_id, order)``
    collisions, and runs ``leak_sanitizer.scan_text`` over every generated log
    and rewritten mirror.
    """
    repo_path = Path(repo)
    pre_root = Path(pre_conversion_records_root)
    post_root = Path(converted_records_root)
    field_source_root = (
        Path(post_step3_records_root)
        if post_step3_records_root is not None
        else pre_root
    )
    reverse_rename = {
        new_rel: old_rel for old_rel, new_rel in (rename_map or {}).items()
    }
    renamed_new_rels = set(reverse_rename.keys())

    preexisting_dup_pairs: Set[Tuple[str, int]] = set()
    for dup in unmapped_plan_duplicates or ():
        if isinstance(dup, dict) and dup.get("set_id") and dup.get("order") is not None:
            preexisting_dup_pairs.add((str(dup["set_id"]), int(dup["order"])))
        elif isinstance(dup, (tuple, list)) and len(dup) == 2:
            pair = dup[0]
            if isinstance(pair, (tuple, list)) and len(pair) == 2:
                preexisting_dup_pairs.add((str(pair[0]), int(pair[1])))

    errors: List[str] = []
    legacy_filename_leftovers: List[str] = []
    for rec_path in m0001_convert._walk_target_records(
        post_root, record_types=m0001_convert.ALL_RECORD_TYPES
    ):
        if not artifact_naming._LEGACY_TIMESTAMP_RE.match(rec_path.name):
            continue
        rel = rec_path.relative_to(post_root).as_posix()
        if _is_oq02_excluded_template(
            rel, text=rec_path.read_text(encoding="utf-8", errors="replace")
        ):
            continue
        legacy_filename_leftovers.append(rel)

    if legacy_filename_leftovers:
        errors.append(
            "Legacy-timestamp filename(s) remain after conversion: "
            + ", ".join(legacy_filename_leftovers[:10])
        )

    reviews_by_subject = m0001_convert._discover_review_files(field_source_root)
    converted_records = _collect_converted_records(post_root)
    plan_set_orders: Dict[Tuple[str, int], List[str]] = {}

    ruleset = leak_sanitizer.build_ruleset(repo_path, include_warn=True)
    leak_fails: List[Dict[str, str]] = []
    leak_warns: List[Dict[str, str]] = []

    def _scan_text(txt: str, loc_label: str) -> None:
        for f in leak_sanitizer.scan_text(txt, loc_label, ruleset, include_warn=True):
            item = {
                "location": f.location,
                "rule": f.rule,
                "severity": f.severity,
                "snippet": f.snippet,
            }
            if f.severity == "fail":
                leak_fails.append(item)
            else:
                leak_warns.append(item)

    def _scan_file(fpath: Path, loc_label: str) -> None:
        _scan_text(fpath.read_text(encoding="utf-8", errors="replace"), loc_label)

    replayed_count = 0
    for rel_path, id6, art_type, rec_path in converted_records:
        log_path = post_root / "meta" / f"{id6}.jsonl"
        if not log_path.is_file():
            errors.append(
                f"Missing event log {log_path.relative_to(post_root).as_posix()} for {rel_path}"
            )
            continue

        log_text = log_path.read_text(encoding="utf-8")
        rewritten_text = rec_path.read_text(encoding="utf-8")
        _scan_text(log_text, f"meta/{id6}.jsonl")
        _scan_text(rewritten_text, rel_path)

        raw_lines = [ln for ln in log_text.splitlines(keepends=True) if ln.strip()]
        events = [artifact_meta.decode_line(ln) for ln in raw_lines]

        try:
            state, _fc, _ap, proj = artifact_meta.replay(
                id6,
                art_type,
                raw_lines,
                records_root=post_root,
            )
        except Exception as exc:
            errors.append(f"Replay failed for {rel_path} ({id6}): {exc}")
            continue

        replayed_count += 1

        # Mirror check
        try:
            if art_type == "prompt":
                prompt_lines = rewritten_text.splitlines()
                first_ln = prompt_lines[0].strip() if prompt_lines else ""
                non_empty_after_c = [
                    ln.strip() for ln in prompt_lines[1:] if ln.strip()
                ]
                if first_ln == "---" or (
                    non_empty_after_c and non_empty_after_c[0] == "---"
                ):
                    raise ValueError("staged prompt contains forbidden '---' delimiter")
                mirror = artifact_meta.parse_staged_prompt_mirror(rewritten_text)
                if mirror.get("status") != state.status:
                    errors.append(
                        f"Mirror status mismatch for {rel_path}: {mirror.get('status')!r} != {state.status!r}"
                    )
            elif art_type in ("walkthrough", "roadmap"):
                mirror = artifact_meta.parse_walkthrough_mirror(rewritten_text)
            else:
                mirror = artifact_meta.parse_artifact_mirror(
                    rewritten_text, allow_statusless=(art_type == "research")
                )
                if mirror.get("status") != state.status:
                    errors.append(
                        f"Mirror status mismatch for {rel_path}: {mirror.get('status')!r} != {state.status!r}"
                    )
            if mirror.get("id") != id6:
                errors.append(
                    f"Mirror id mismatch for {rel_path}: {mirror.get('id')!r} != {id6!r}"
                )
        except ValueError as exc:
            errors.append(f"Mirror parse failed for {rel_path}: {exc}")

        if art_type == "ipd" and state.set_id and state.order_nn is not None:
            plan_set_orders.setdefault((state.set_id, state.order_nn), []).append(
                rel_path
            )

        # Byte-for-byte legacy recovery: inline history vs pre-Step-3 source,
        # non-history fields and promoted body sections vs post-Step-3 source.
        old_rel = reverse_rename.get(rel_path)
        pre_path = pre_root / (old_rel or rel_path)
        if not pre_path.is_file():
            errors.append(
                f"Missing pre-conversion source for {rel_path} (looked at {old_rel or rel_path})"
            )
            continue

        field_path = (
            field_source_root / rel_path
            if post_step3_records_root is not None
            else pre_path
        )
        if not field_path.is_file():
            errors.append(
                f"Missing post-step3 source for {rel_path} (looked at {field_path})"
            )
            continue

        field_text = field_path.read_text(encoding="utf-8")
        leg_status, _raw_fields, ordered_pairs, _post_hist = (
            _legacy_field_pairs_for_record(
                field_path, field_source_root, art_type, text=field_text
            )
        )
        if post_step3_records_root is not None:
            pre_text = pre_path.read_text(encoding="utf-8")
            if pre_text == field_text:
                hist_entries = _post_hist
            else:
                _pre_st, _pre_rf, _pre_pairs, hist_entries = (
                    _legacy_field_pairs_for_record(
                        pre_path, pre_root, art_type, text=pre_text
                    )
                )
        else:
            hist_entries = _post_hist
        if art_type not in ("walkthrough", "roadmap") and state.status != leg_status:
            errors.append(
                f"Status round-trip mismatch for {rel_path}: {state.status!r} != {leg_status!r}"
            )

        reg = artifact_meta.REGISTRY.get(art_type, {})
        historical_ipd = (art_type == "ipd") and m0001_convert.is_historical_ipd(
            rel_path, leg_status
        )
        for key, val in ordered_pairs:
            dest = m0001_convert.classify_field(
                art_type, key, historical_ipd=historical_ipd
            )
            if dest is None:
                errors.append(f"Unmapped field {key!r} in {rel_path}")
                continue
            if dest.kind in (
                "identity",
                "status",
                "prompt_body",
                "comment_value",
                "body_prose",
            ):
                continue
            if dest.kind == "body_section":
                val_s = val.strip() if isinstance(val, str) else str(val).strip()
                if val_s and val_s not in rewritten_text:
                    errors.append(
                        f"Body section {dest.target!r} missing verbatim value in {rel_path}"
                    )
                continue

            # dest.kind == "log_field"
            target_field = dest.target
            if key in ("Set", "set"):
                terse = m0001_renames._parse_terse_set(str(val))
                if terse and state.fields.get("set") != terse:
                    errors.append(
                        f"Field 'set' mismatch for {rel_path}: {state.fields.get('set')!r} != {terse!r}"
                    )
            elif key in ("Order", "order"):
                s_val = str(val).strip()
                if s_val and state.fields.get("order") != int(s_val):
                    errors.append(
                        f"Field 'order' mismatch for {rel_path}: {state.fields.get('order')!r} != {int(s_val)!r}"
                    )
            elif key in ("Date", "Created", "created"):
                cday, date_note = m0001_convert._parse_legacy_day(str(val))
                if cday and state.fields.get("created_day") != cday:
                    errors.append(
                        f"Field 'created_day' mismatch for {rel_path}: {state.fields.get('created_day')!r} != {cday!r}"
                    )
                if date_note and date_note not in rewritten_text:
                    errors.append(
                        f"Date annotation note missing verbatim value in {rel_path}"
                    )
            elif key == "Item-Dependencies":
                dep_decl, dep_edges = artifact_meta.parse_item_dependencies_field(val)
                if state.fields.get("dependency_declaration") != dep_decl:
                    errors.append(f"dependency_declaration mismatch for {rel_path}")
                if (
                    dep_decl == "listed"
                    and state.fields.get("item_dependencies") != dep_edges
                ):
                    errors.append(f"item_dependencies mismatch for {rel_path}")
            elif key == "Scope-Exceeded":
                if state.fields.get("scope_result") != "exceeded":
                    errors.append(f"scope_result != 'exceeded' for {rel_path}")
                if state.fields.get("scope_exceeded_raw") != val:
                    errors.append(f"scope_exceeded_raw mismatch for {rel_path}")
            elif key == "Scope-Paths":
                sp_list = m0001_convert._coerce_list_value(val, split_commas=True)
                if sp_list and state.fields.get("scope_paths") != sp_list:
                    errors.append(f"scope_paths mismatch for {rel_path}")
            elif key == "Graduated-To":
                gt_list = artifact_meta.parse_graduated_to(val)
                if gt_list and state.fields.get("graduated_to") != gt_list:
                    errors.append(f"graduated_to mismatch for {rel_path}")
            elif key in ("topic", "consumed-by"):
                lst = m0001_convert._coerce_list_value(val, split_commas=True)
                if state.fields.get(target_field) != lst:
                    errors.append(f"Field {target_field!r} mismatch for {rel_path}")
            elif key in ("Targets", "Concerns", "Results-go-to", "Results"):
                lst = m0001_convert._coerce_list_value(val, split_commas=False)
                if lst and state.fields.get(target_field) != lst:
                    errors.append(f"Field {target_field!r} mismatch for {rel_path}")
            elif target_field in reg and val != "" and val is not None:
                if state.fields.get(target_field) != val:
                    errors.append(
                        f"Field {target_field!r} mismatch for {rel_path}: {state.fields.get(target_field)!r} != {val!r}"
                    )

        # Inline history lines byte-for-byte check
        log_hist = [
            ev.get("line")
            for ev in events
            if ev.get("op") == "legacy" and ev.get("source") == "history"
        ]
        expected_hist = [raw_line for raw_line, _day in hist_entries]
        if log_hist != expected_hist:
            errors.append(
                f"Inline history round-trip mismatch for {rel_path}: {len(log_hist)} != {len(expected_hist)}"
            )

        # Sidecar objects byte-for-byte check
        expected_sc = [sc.get("line") for sc in (sidecar_events or {}).get(id6, ())]
        log_sc = [
            ev.get("line")
            for ev in events
            if ev.get("op") == "legacy" and ev.get("source") == "sidecar"
        ]
        if log_sc != expected_sc:
            errors.append(
                f"Sidecar round-trip mismatch for {rel_path}: {len(log_sc)} != {len(expected_sc)}"
            )

        # Review rounds recovery check
        rf_specs = reviews_by_subject.get(id6, ())
        if rf_specs:
            proj_reviews = proj.get("reviews") or []
            expected_rev_tuples: List[
                Tuple[int, str, Optional[str], Optional[str]]
            ] = []
            for rf in rf_specs:
                for rnd_num in rf.rounds:
                    is_last = rnd_num == rf.last_round
                    expected_rev_tuples.append(
                        (
                            rnd_num,
                            rf.review_kind,
                            rf.review_ref,
                            rf.legacy_verdict if is_last else None,
                        )
                    )
            actual_rev_tuples = [
                (
                    r.get("round"),
                    r.get("review_kind"),
                    r.get("review_ref"),
                    r.get("legacy_verdict"),
                )
                for r in proj_reviews
            ]
            if actual_rev_tuples != expected_rev_tuples:
                errors.append(f"Review round-trip mismatch for {rel_path} ({id6})")

    # Verify rewritten review mirrors and scan them
    post_reviews_dir = post_root / "reviews"
    review_mirrors_checked = 0
    if post_reviews_dir.is_dir():
        for cur_dir, dirs, files in os.walk(post_reviews_dir):
            dirs[:] = sorted(d for d in dirs if not d.endswith(".data"))
            cur_path = Path(cur_dir)
            for fname in sorted(files):
                if not fname.endswith(".review.md"):
                    continue
                if fname in _SKIP_FILENAMES or fname.startswith("INDEX."):
                    continue
                fpath = cur_path / fname
                rel = fpath.relative_to(post_root).as_posix()
                _scan_file(fpath, rel)
                try:
                    artifact_meta.parse_review_mirror(fpath.read_text(encoding="utf-8"))
                    review_mirrors_checked += 1
                except ValueError as exc:
                    errors.append(f"Review mirror parse failed for {rel}: {exc}")

    # Check plan (set_id, order) collisions: any collision on a newly renamed/mapped plan
    # or any collision not already listed in unmapped_plan_duplicates is an error.
    set_order_collisions: List[Dict[str, Any]] = []
    for pair, paths in sorted(plan_set_orders.items()):
        if len(paths) <= 1:
            continue
        involves_renamed = any(p in renamed_new_rels for p in paths)
        if involves_renamed or pair not in preexisting_dup_pairs:
            set_order_collisions.append(
                {"set_id": pair[0], "order": pair[1], "paths": sorted(paths)}
            )
            errors.append(
                f"Duplicate plan (set_id={pair[0]!r}, order={pair[1]}): {', '.join(sorted(paths))}"
            )

    round_trip_passed = len(errors) == 0
    passed = round_trip_passed and len(leak_fails) == 0

    return {
        "passed": passed,
        "round_trip_passed": round_trip_passed,
        "replayed_count": replayed_count,
        "review_mirrors_checked": review_mirrors_checked,
        "legacy_filename_leftovers": legacy_filename_leftovers,
        "set_order_collisions": set_order_collisions,
        "errors": errors,
        "leak_fail_count": len(leak_fails),
        "leak_warn_count": len(leak_warns),
        "leak_fails": leak_fails,
        "leak_warns": leak_warns,
    }


def format_census(census: Mapping[str, Any]) -> str:
    """Render a human-readable step-6 field census summary."""
    lines: List[str] = [
        f"Field Census ({census.get('record_count', 0)} records, {census.get('review_count', 0)} reviews):",
    ]
    layout_stage = census.get("layout_stage")
    if isinstance(layout_stage, Mapping):
        if layout_stage.get("status") == "skipped":
            lines.append("  layout stage: skipped (already on .aw/)")
        else:
            ls_status = layout_stage.get("status", "planned")
            ls_backend = layout_stage.get("target_backend", "repository")
            ls_planned = layout_stage.get("planned_count", 0)
            ls_moved = layout_stage.get("moved", 0)
            ls_dedup = layout_stage.get(
                "dedup_removed", layout_stage.get("dedup_skipped", 0)
            )
            lines.append(
                f"  layout stage: {ls_status} (backend={ls_backend}, planned={ls_planned}, "
                f"moved={ls_moved}, dedup={ls_dedup})"
            )
            for grp, cnt in (layout_stage.get("groups") or {}).items():
                lines.append(f"    - {grp}: {cnt}")
    lines.extend(
        [
            f"  Distinct bullet names before first ##: {census.get('distinct_bullet_count', 0)}",
            f"  Unknown-field refusals: {census.get('unknown_field_refusal_count', 0)}",
            f"  Unparseable-value refusals: {census.get('unparseable_value_refusal_count', 0)}",
            f"  Sidecar: {census.get('sidecar_status', 'unknown')}",
        ]
    )
    orphans = census.get("orphan_counts") or {}
    if orphans:
        lines.append(
            f"  Sidecar orphan id6s ({census.get('orphan_record_count', 0)} records across {len(orphans)} id6):"
        )
        for oid, cnt in sorted(orphans.items()):
            lines.append(f"    - {oid}: {cnt}")
    else:
        lines.append("  Sidecar orphan id6s: 0")

    lines.append(
        f"  Descriptions: with={census.get('with_description_count', 0)}, "
        f"without={census.get('without_description_count', 0)}"
    )
    delib = census.get("deliberate_description_absences") or {}
    if delib:
        lines.append(f"  Deliberate description absences ({len(delib)}):")
        for p, reason in sorted(delib.items()):
            lines.append(f"    - {p}: {reason}")

    plan_roles = census.get("plan_role_counts") or {}
    lines.append(
        f"  Plan roles (Kind -> plan_role): {plan_roles}, absent Kind: {census.get('absent_kind_count', 0)}"
    )
    prompts_no_comment = census.get("prompts_without_comment") or []
    lines.append(f"  Staged prompts without leading comment: {len(prompts_no_comment)}")
    for p in prompts_no_comment:
        lines.append(f"    - {p}")

    templates = census.get("excluded_templates") or []
    lines.append(f"  Excluded templates (kept byte-identical, {len(templates)}):")
    for t in templates:
        lines.append(f"    - {t}")

    minted_recs = census.get("minted_records") or []
    if minted_recs:
        lines.append(f"  Minted id-less records ({len(minted_recs)}):")
        for mr in minted_recs:
            st = mr.get("status") or "none"
            st_src = mr.get("status_source")
            st_lbl = f"{st} [{st_src}]" if st_src else st
            lines.append(
                f"    - {mr.get('id6')}: {mr.get('old_rel')} -> {mr.get('new_rel')} "
                f"(type={mr.get('record_type')}, status={st_lbl}, title={mr.get('title')!r})"
            )
    else:
        lines.append("  Minted id-less records: 0")

    unclass = census.get("unclassifiable_files") or []
    if unclass:
        lines.append(f"  Unclassifiable files (left untouched, {len(unclass)}):")
        for uf in unclass:
            lines.append(f"    - {uf.get('path')}: {uf.get('reason')}")
    else:
        lines.append("  Unclassifiable files (left untouched): 0")

    non_leading = census.get("non_leading_research_prompt_comments") or []
    lines.append(
        f"  Non-leading research aw-prompt comments (body prose per OQ-04, {len(non_leading)}):"
    )
    for r in non_leading:
        lines.append(f"    - {r}")

    lines.append("  Fields by source, destination, and count:")
    for row in census.get("field_rows") or []:
        rtypes = ",".join(row.get("record_types") or [])
        lines.append(
            f"    - [{row['source_kind']}] {row['field']} -> "
            f"{row['destination_kind']}: {row['destination']} "
            f"(count={row['count']}, types={rtypes})"
        )

    for ref in census.get("refusals") or []:
        lines.append(
            f"  REFUSAL [{ref['kind']}] {ref['path']} ({ref['field']}): {ref['detail']}"
        )

    return "\n".join(lines)


def ensure_apply_gates_pass(
    census: Mapping[str, Any],
    round_trip: Mapping[str, Any],
) -> None:
    """Raise ``layout_migration.PreflightGateError`` if step 6 refuses ``--apply``."""
    reasons: List[str] = []
    refusals = census.get("refusals") or []
    if refusals:
        sample = "; ".join(
            f"{r['kind']} in {r['path']} ({r['field']})" for r in refusals[:5]
        )
        reasons.append(f"{len(refusals)} census refusal(s): {sample}")

    without_desc = int(census.get("without_description_count") or 0)
    if without_desc > 0:
        missing = census.get("missing_description_paths") or []
        sample_paths = ", ".join(missing[:5])
        suffix = f" (e.g. {sample_paths})" if sample_paths else ""
        reasons.append(f"{without_desc} record(s) lack a short_description{suffix}")

    if not round_trip.get("round_trip_passed", False):
        rt_errs = round_trip.get("errors") or ["round-trip verification failed"]
        reasons.append(
            f"round-trip verification failed ({len(rt_errs)} error(s)): {'; '.join(rt_errs[:3])}"
        )

    leak_fail_count = int(round_trip.get("leak_fail_count") or 0)
    if leak_fail_count > 0:
        fails = round_trip.get("leak_fails") or []
        sample_leaks = "; ".join(f"{f['location']} [{f['rule']}]" for f in fails[:5])
        reasons.append(
            f"{leak_fail_count} leak_sanitizer fail diagnostic(s): {sample_leaks}"
        )

    if reasons:
        raise layout_migration.PreflightGateError(
            "m0001 step-6 verification refused --apply: " + " | ".join(reasons)
        )
