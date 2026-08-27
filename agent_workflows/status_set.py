"""Unified status transition engine for plans, specs, prompts, backlog, and more.

Supports natural command surface:
  aw set <status> <id6|setid|fname>...
  aw set <type> <status> <id6|setid|fname>...
  aw ipd set <status> <id6|setid|fname>...
  aw spec set <status> <id6|setid|fname>...
  aw specs set <status> <id6|setid|fname>...
  aw backlog set <status> <id6|setid|fname>...

Enforces:
- Atomic pre-flight check: all selectors must resolve, or no changes are made.
- Strict type scoping: when a type is specified, any target resolving to another type is an error.
- Valid status transition per artifact type.
- Clean front-matter + workflow history + directory disposition updates.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import re
from dataclasses import dataclass
from pathlib import Path

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import plans as _plans_mod
from agent_workflows import selectors as _sel
from agent_workflows.result_types import Change
from agent_workflows.term import Term

# Recognized status sets per artifact type
TYPE_STATUSES: dict[str, set[str]] = {
    "plans": {
        "draft",
        "to-review",
        "reviewed",
        "approved",
        "auto-approved",
        "executed",
        "superseded",
        "not-executed",
        "reusable",
        "done",  # alias for executed
        "pending",  # alias for to-review
    },
    "prompts": {
        "draft",
        "to-review",
        "reviewed",
        "approved",
        "auto-approved",
        "executed",
        "superseded",
        "not-executed",
        "reusable",
        "done",
        "pending",
    },
    "specs": {
        "draft",
        "to-review",
        "reviewed",
        "approved",
        "implementing",
        "implemented",
        "deferred",
        "parked",
        "superseded",
    },
    "backlog": {
        "open",
        "blocked",
        "parked",
        "done",
    },
    "releases": {
        "planned",
        "blocked",
        "shipped",
    },
    "research": {
        "open",
        "active",
        "done",
        "parked",
    },
}

# Type aliases / singular mappings to canonical plural
TYPE_ALIASES: dict[str, str] = {
    "ipd": "plans",
    "ipds": "plans",
    "plan": "plans",
    "plans": "plans",
    "spec": "specs",
    "specs": "specs",
    "prompt": "prompts",
    "prompts": "prompts",
    "backlog": "backlog",
    "release": "releases",
    "releases": "releases",
    "research": "research",
    "walkthrough": "walkthroughs",
    "walkthroughs": "walkthroughs",
    "roadmap": "roadmaps",
    "roadmaps": "roadmaps",
}

# Regexes for front-matter inspection and manipulation
_ID_RE = re.compile(r"^-\s*Id:\s*([0-9a-z]{6})\s*$", re.MULTILINE)
_STATUS_RE = re.compile(r"^-\s*Status:\s*(\S+)\s*$", re.MULTILINE)
_SET_RE = re.compile(r"^-\s*Set:\s*(.+?)\s*$", re.MULTILINE)
_HISTORY_HDR_RE = re.compile(r"^##\s*Workflow history\s*$", re.MULTILINE)
_BLOCKS_RELEASE_RE = re.compile(r"^-\s*Blocks-Release:\s*(\S+)\s*$", re.MULTILINE)
_GATE_KIND_RE = re.compile(r"^-\s*Gate-Kind:\s*(\S+)\s*$", re.MULTILINE)
_GATE_REF_RE = re.compile(r"^-\s*Gate-Ref:\s*(.+?)\s*$", re.MULTILINE)
_GATE_SUMMARY_RE = re.compile(r"^-\s*Gate-Summary:\s*(.+?)\s*$", re.MULTILINE)


@dataclass
class ArtifactRecord:
    path: Path
    record_type: str
    id6: str | None
    set_id: str | None
    status: str | None
    raw_text: str


def canonical_type(type_token: str | None) -> str | None:
    """Normalize type token to canonical plural form, or None if not an artifact type."""
    if not type_token:
        return None
    token = type_token.strip().lower()
    return TYPE_ALIASES.get(token, None)


def detect_artifact_type(path: Path, repo_root: Path) -> str | None:
    """Detect the record type of an artifact file based on path facets and location.

    The facet->type mapping is derived from the single naming authority's ``TYPE_FACET`` (IPD
    o6b8l3), so there is one facet-enum definition; only the ``comms`` facet is intentionally not
    resolved to a status-settable type here (no comms status flow)."""
    name = path.name
    for _type, _facet in _naming.TYPE_FACET.items():
        if _type == "comms":
            continue
        if name.endswith(f".{_facet}.md"):
            return _type

    # Location-based detection
    rel_parts = path.resolve().parts
    for i, part in enumerate(rel_parts):
        if part in ("records", ".agents", ".aw") and i + 1 < len(rel_parts):
            next_part = rel_parts[i + 1]
            if next_part in TYPE_ALIASES:
                return TYPE_ALIASES[next_part]
            if next_part == "docs" and i + 2 < len(rel_parts):
                doc_part = rel_parts[i + 2]
                if doc_part in TYPE_ALIASES:
                    return TYPE_ALIASES[doc_part]

    # Fallback to content check
    try:
        text = path.read_text(encoding="utf-8")
        if text.startswith("# IPD:"):
            return "plans"
        if "- Kind: child" in text or "- Kind: orchestrator" in text:
            return "plans"
    except OSError:
        pass
    return None


def read_artifact_record(path: Path, repo_root: Path) -> ArtifactRecord | None:
    """Read and parse an artifact record from disk."""
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    rtype = detect_artifact_type(path, repo_root)
    if not rtype:
        return None

    id_match = _ID_RE.search(text)
    id6 = id_match.group(1) if id_match else None

    status_match = _STATUS_RE.search(text)
    status = status_match.group(1) if status_match else None

    set_match = _SET_RE.search(text)
    set_id = None
    if set_match:
        raw_set = set_match.group(1).strip()
        set_id = raw_set.split("(")[0].strip().split()[0] if raw_set else None

    return ArtifactRecord(
        path=path,
        record_type=rtype,
        id6=id6,
        set_id=set_id,
        status=status,
        raw_text=text,
    )


def inventory_all_artifacts(repo_root: Path) -> list[ArtifactRecord]:
    """Scan and index all non-index *.md artifacts in the repository across all types."""
    records: list[ArtifactRecord] = []
    seen: set[str] = set()

    for rtype in ("plans", "specs", "prompts", "backlog", "releases", "research"):
        for d in _sel.record_dirs(repo_root, rtype):
            if not d.is_dir():
                continue
            for p in d.rglob("*.md"):
                if p.name in _sel._SKIP_NAMES:
                    continue
                try:
                    rp = str(p.resolve())
                except OSError:
                    continue
                if rp in seen:
                    continue
                seen.add(rp)
                rec = read_artifact_record(p, repo_root)
                if rec:
                    records.append(rec)
    return records


def match_selector(
    selector: str,
    all_records: list[ArtifactRecord],
    repo_root: Path,
    scoped_type: str | None = None,
) -> list[ArtifactRecord]:
    """Match a single selector token against the inventory (IPD laykok E-03: thin shim over the ONE
    unified resolver ``selectors.resolve``).

    Resolution covers the full vocabulary with one documented precedence: direct path -> exact id6
    -> exact setid -> exact status -> exact stem -> filename substring. This ADDS the previously
    missing status and bare-stem kinds to `aw set` while preserving every prior successful
    resolution (path/id6/setid/substring). The resolved paths are mapped back to `ArtifactRecord`s
    (from ``all_records`` when known, else read on demand) so the caller's record-based flow is
    unchanged.
    """
    tok = selector.strip()
    if not tok:
        return []

    from agent_workflows import selectors as _sel

    if scoped_type:
        canonical = canonical_type(scoped_type) or scoped_type
        record_types = (canonical,)
    else:
        record_types = (
            "plans",
            "specs",
            "prompts",
            "backlog",
            "releases",
            "research",
            "walkthroughs",
            "roadmaps",
        )
    matched_paths: dict[str, Path] = {}
    for rt in record_types:
        res = _sel.resolve(repo_root, rt, tok)
        for p in res.paths:
            matched_paths[str(p.resolve())] = p.resolve()

    if not matched_paths:
        return []

    by_path = {str(r.path.resolve()): r for r in all_records}
    out: list[ArtifactRecord] = []
    seen: set[str] = set()
    for key in sorted(matched_paths):
        if key in seen:
            continue
        seen.add(key)
        rec = by_path.get(key)
        if rec is None:
            rec = read_artifact_record(matched_paths[key], repo_root)
        if rec:
            out.append(rec)
    return out


def _format_status_transition_line(
    rec: ArtifactRecord,
    dest_path: Path,
    norm_stat: str,
    term: Term,
    args: argparse.Namespace | None = None,
    dry_run: bool = False,
    changed: bool = True,
) -> str:
    from agent_workflows import attention as _att

    old_status = (rec.status or "draft").strip().lower()
    norm_stat_clean = norm_stat.strip().lower()
    arrow = term.glyph("arrow")

    if not changed or old_status == norm_stat_clean:
        status_part = (
            term.status_256("unchanged")
            if getattr(term, "color", False)
            else "unchanged"
        )
    else:
        old_styled = (
            term.status_256(rec.status or "draft")
            if getattr(term, "color", False)
            else (rec.status or "draft")
        )
        new_styled = (
            term.status_256(norm_stat) if getattr(term, "color", False) else norm_stat
        )
        status_part = f"{old_styled} {arrow} {new_styled}"

    m_prio = re.search(r"(?m)^-\s*Priority:\s*(\S+)", rec.raw_text)
    priority = m_prio.group(1).lower() if m_prio else None

    br_arg = getattr(args, "blocks_release", None) if args else None
    if br_arg:
        blocks_release = None if br_arg == "-" else br_arg
    else:
        m_br = re.search(r"(?m)^-\s*Blocks-Release:\s*(\S+)", rec.raw_text)
        blocks_release = m_br.group(1) if m_br else None

    m_gk = re.search(r"(?m)^-\s*Gate-Kind:\s*(\S+)", rec.raw_text)
    m_gr = re.search(r"(?m)^-\s*Gate-Ref:\s*(\S+)", rec.raw_text)
    gate = f"{m_gk.group(1)}:{m_gr.group(1)}" if (m_gk and m_gr) else None

    prio_txt = ""
    if priority:
        pcode = {"high": 196, "medium": 214, "low": 244}.get(priority, 244)
        prio_txt = "  " + (
            term.color256(f"[{priority}]", pcode, bold=True)
            if getattr(term, "color", False)
            else f"[{priority}]"
        )

    blocking_txt = ""
    if blocks_release:
        blocking_txt = "  " + (
            term.color256("[blocking]", 196, bold=True)
            if getattr(term, "color", False)
            else "[blocking]"
        )

    gate_txt = ""
    if gate:
        gate_txt = "  " + (
            term.color256(f"[{gate}]", 203, bold=True)
            if getattr(term, "color", False)
            else f"[{gate}]"
        )

    lead = ">  " if blocks_release else "   "
    type_word = _att._SINGULAR_TYPE.get(rec.record_type, rec.record_type)
    type_txt = (
        term.color256(type_word, _att._TREE_COLOR_256, bold=True)
        if getattr(term, "color", False)
        else type_word
    )
    type_prefix = type_txt + (" " * max(0, 10 - len(type_word))) + "  "
    stem = _att._identity_stem(str(dest_path))
    dry_suffix = "  (dry-run)" if dry_run else ""

    return f"- {lead}{type_prefix}{stem}{prio_txt}{blocking_txt}{gate_txt}  {status_part}{dry_suffix}"


def normalize_target_status(raw_status: str, record_type: str) -> str:
    """Normalize status aliases according to record type."""
    norm = raw_status.strip().lower()
    if record_type in ("plans", "prompts"):
        if norm == "done":
            return "executed"
        if norm == "pending":
            return "to-review"
    return norm


def validate_transition_allowed(
    rec: ArtifactRecord,
    target_status: str,
    args: argparse.Namespace,
) -> tuple[bool, str | None]:
    """Validate that the target status is valid and permitted for the record."""
    norm_status = normalize_target_status(target_status, rec.record_type)
    valid_statuses = TYPE_STATUSES.get(rec.record_type, set())
    if norm_status not in valid_statuses:
        return (
            False,
            f"Status '{target_status}' is not valid for {rec.record_type} (valid: {sorted(valid_statuses)})",
        )

    # Type-specific validation
    if rec.record_type == "specs":
        from agent_workflows import attention_contract as ac

        old_status = rec.status
        if old_status and old_status != norm_status:
            if not ac.transition_allowed(old_status, norm_status):
                return False, f"Illegal spec transition {old_status} -> {norm_status}"
            auth = ac.TRANSITION_AUTHORITY.get(f"->{norm_status}", {})
            if (auth.get("by_human") or auth.get("human_token")) and not getattr(
                args, "by_human", False
            ):
                return (
                    False,
                    f"Transition {old_status} -> {norm_status} requires --by-human attestation",
                )

    if rec.record_type == "backlog" and norm_status == "blocked":
        gk = getattr(args, "gate_kind", None)
        gr = getattr(args, "gate_ref", None)
        if not gk or not gr:
            return (
                False,
                "Moving backlog item to blocked requires --gate-kind and --gate-ref",
            )

    return True, None


def apply_status_change(
    rec: ArtifactRecord,
    target_status: str,
    repo_root: Path,
    args: argparse.Namespace,
) -> tuple[Path, str]:
    """Apply the status change to the artifact on disk, appending workflow history and moving file if needed."""
    norm_status = normalize_target_status(target_status, rec.record_type)
    today = datetime.datetime.now(datetime.timezone.utc).date().strftime("%Y-%m-%d")
    message = getattr(args, "message", None) or f"status set to {norm_status}"
    actor = getattr(args, "actor", None) or "aw set"
    if getattr(args, "by_human", False):
        actor = f"{actor}, --by-human"

    text = rec.path.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Update or insert - Status: <norm_status> in frontmatter only
    status_updated = False
    new_lines = []
    in_frontmatter = True
    is_fenced_yaml = bool(lines and lines[0].strip() == "---")

    for line in lines:
        if is_fenced_yaml:
            if in_frontmatter and line.strip() == "---" and new_lines:
                in_frontmatter = False
            if (
                in_frontmatter
                and not status_updated
                and re.match(r"^status:\s*\S+", line, re.IGNORECASE)
            ):
                new_lines.append(f"status: {norm_status}")
                status_updated = True
            else:
                new_lines.append(line)
        else:
            if in_frontmatter and line.startswith("## "):
                in_frontmatter = False
            if in_frontmatter and not status_updated and _STATUS_RE.match(line):
                new_lines.append(f"- Status: {norm_status}")
                status_updated = True
            else:
                new_lines.append(line)

    if not status_updated:
        if is_fenced_yaml:
            # insert status: before closing ---
            res_lines = []
            inserted = False
            for line in new_lines:
                if not inserted and line.strip() == "---" and res_lines:
                    res_lines.append(f"status: {norm_status}")
                    inserted = True
                res_lines.append(line)
            new_lines = res_lines
        else:
            inserted = False
            res_lines = []
            for i, line in enumerate(new_lines):
                res_lines.append(line)
                if not inserted and (line.startswith(("# ", "- Date:"))):
                    res_lines.append(f"- Status: {norm_status}")
                    inserted = True
            if not inserted:
                res_lines.insert(0, f"- Status: {norm_status}")
            new_lines = res_lines

    # Handle gate fields if moving away from deferred/blocked
    if rec.record_type == "specs":
        if norm_status != "deferred":
            new_lines = [
                line_item
                for line_item in new_lines
                if not _GATE_KIND_RE.match(line_item)
                and not _GATE_REF_RE.match(line_item)
                and not _GATE_SUMMARY_RE.match(line_item)
            ]
        else:
            gk = getattr(args, "gate_kind", None)
            gr = getattr(args, "gate_ref", None)
            gs = getattr(args, "gate_summary", None)
            if gk and gr:
                new_lines = [
                    line_item
                    for line_item in new_lines
                    if not _GATE_KIND_RE.match(line_item)
                    and not _GATE_REF_RE.match(line_item)
                    and not _GATE_SUMMARY_RE.match(line_item)
                ]
                st_idx = -1
                for i, line_item in enumerate(new_lines):
                    if _STATUS_RE.match(line_item):
                        st_idx = i
                        break
                insert_pos = st_idx + 1 if st_idx >= 0 else 1
                gate_lines = [f"- Gate-Kind: {gk}", f"- Gate-Ref: {gr}"]
                if gs:
                    gate_lines.append(f"- Gate-Summary: {gs}")
                for gl in reversed(gate_lines):
                    new_lines.insert(insert_pos, gl)

    # Blocks-Release write (IPD efnn74, root-cause of bug 61qk4a): this mutation is
    # record-type-agnostic and MUST apply to plans and backlog too, not only specs, so it is
    # hoisted OUT of the specs-only guard above. The specs-only Gate-Kind/Gate-Ref/Gate-Summary
    # handling stays inside that guard; only this shared write is lifted. All setter surfaces funnel
    # through the single shared `releases.set_blocks_release_line` primitive (no duplicate write
    # path). The join/split idempotency is preserved so trailing metadata structure is unchanged.
    br = getattr(args, "blocks_release", None)
    if br is not None:
        from agent_workflows import releases as _releases

        tmp_text = "\n".join(new_lines)
        tmp_text = _releases.set_blocks_release_line(tmp_text, br)
        new_lines = tmp_text.splitlines()

    # From-Backlog write (bklggrad ku93tn): the same hoisted, status-branch-independent shape as the
    # Blocks-Release write above, so `aw ipd set --from-backlog <id6|->` persists even on a no-op
    # (same-status) transition. Funnels through the single shared `releases.set_from_backlog_line`
    # primitive (no duplicate write path).
    fb = getattr(args, "from_backlog", None)
    if fb is not None:
        from agent_workflows import releases as _releases

        tmp_text = "\n".join(new_lines)
        tmp_text = _releases.set_from_backlog_line(tmp_text, fb)
        new_lines = tmp_text.splitlines()

    if rec.record_type == "plans" and norm_status != "approved":
        new_lines = [
            line_item
            for line_item in new_lines
            if not re.match(r"^- Approval:\s*", line_item)
        ]

    # The IPD schema REQUIRES an `- Approval:` field exactly when Status is `approved`
    # (ipd_schema.APPROVAL_STATUSES; enforced as IPD-M104). `auto-approved` is a
    # sibling tier that records an automated clear and must NOT carry it. So when a
    # plan transitions to `approved` and has no Approval field yet, write a
    # conformant one here, so the setter never produces a plan that fails lint.
    if rec.record_type == "plans" and norm_status == "approved":
        has_approval = any(
            re.match(r"^- Approval:\s*", line_item) for line_item in new_lines
        )
        if not has_approval:
            attn = (
                'human ("approved")'
                if getattr(args, "by_human", False)
                else "recorded via aw ipd set"
            )
            approval_line = f"- Approval: {today}, {attn}: {message}"
            # Insert as the last front-matter bullet: after `- Id:` if present, else
            # after `- Status:`, else before the first `## ` heading.
            insert_idx = None
            for i, line_item in enumerate(new_lines):
                if line_item.startswith("## "):
                    break
                if re.match(r"^- Id:\s*", line_item):
                    insert_idx = i + 1
            if insert_idx is None:
                for i, line_item in enumerate(new_lines):
                    if line_item.startswith("## "):
                        break
                    if _STATUS_RE.match(line_item):
                        insert_idx = i + 1
            if insert_idx is None:
                for i, line_item in enumerate(new_lines):
                    if line_item.startswith("## "):
                        insert_idx = i
                        break
                if insert_idx is None:
                    insert_idx = len(new_lines)
            new_lines.insert(insert_idx, approval_line)

    # Determine destination path if directory-disposition applies
    dest_path = rec.path
    if rec.record_type in ("plans", "prompts"):
        disposition = "pending"
        if norm_status in (
            "draft",
            "to-review",
            "reviewed",
            "approved",
            "auto-approved",
        ):
            disposition = "pending"
        elif norm_status == "reusable":
            disposition = "reusable"
        elif norm_status == "executed":
            disposition = "executed"
        elif norm_status == "superseded":
            disposition = "superseded"
        elif norm_status == "not-executed":
            disposition = "not-executed"

        if rec.path.parent.name in (
            "pending",
            "executed",
            "superseded",
            "not-executed",
            "reusable",
        ):
            if rec.path.parent.name != disposition:
                dest_path = rec.path.parent.parent / disposition / rec.path.name
        else:
            base_dir = _plans_mod._resolve_area_dir(repo_root, rec.record_type)
            dest_path = base_dir / disposition / rec.path.name

    elif rec.record_type == "backlog":
        if (
            rec.path.parent.name in ("open", "blocked", "parked", "done")
            and rec.path.parent.name != norm_status
        ):
            dest_path = rec.path.parent.parent / norm_status / rec.path.name

    content_changed = new_lines != lines
    path_changed = dest_path.resolve() != rec.path.resolve()

    if not content_changed and not path_changed:
        return rec.path, norm_status

    # Append Workflow history
    hist_entry = f"- {today} {norm_status} ({actor}): {message}"
    has_hist_section = False
    for i, line in enumerate(new_lines):
        if _HISTORY_HDR_RE.match(line):
            has_hist_section = True
            new_lines.insert(i + 1, hist_entry)
            break

    if not has_hist_section:
        insert_idx = len(new_lines)
        for i, line in enumerate(new_lines):
            if line.startswith("## "):
                insert_idx = i
                break
        new_lines.insert(insert_idx, "")
        new_lines.insert(insert_idx, hist_entry)
        new_lines.insert(insert_idx, "## Workflow history")

    updated_text = "\n".join(new_lines).rstrip() + "\n"

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    _core.atomic_write(dest_path, updated_text)

    if dest_path.resolve() != rec.path.resolve() and rec.path.exists():
        try:
            rec.path.unlink()
        except OSError:
            pass

    return dest_path, norm_status


def _auto_index_types(
    touched_types: set[str],
    repo_root: Path,
    changes: list[Change] | None = None,
) -> None:
    """Automatically refresh manifest indices for modified artifact types that maintain an index."""
    for rtype in sorted(touched_types):
        if rtype == "plans":
            with contextlib.suppress(Exception):
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
                _, plans_dir = _pidx._dirs(argparse.Namespace(dir=str(repo_root)))
                if changes is not None and plans_dir.is_dir():
                    idx_json = plans_dir / "INDEX.json"
                    idx_md = plans_dir / "INDEX.md"
                    if idx_json.exists():
                        changes.append(
                            Change(
                                path=str(idx_json),
                                kind="update",
                                applied=True,
                                detail="manifest index auto-refreshed",
                            )
                        )
                    if idx_md.exists():
                        changes.append(
                            Change(
                                path=str(idx_md),
                                kind="update",
                                applied=True,
                                detail="manifest index auto-refreshed",
                            )
                        )
        elif rtype == "research":
            with contextlib.suppress(Exception):
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
                _, res_dir = _ridx._roots(argparse.Namespace(dir=str(repo_root)))
                if changes is not None and res_dir.is_dir():
                    idx_json = res_dir / "INDEX.json"
                    idx_md = res_dir / "INDEX.md"
                    if idx_json.exists():
                        changes.append(
                            Change(
                                path=str(idx_json),
                                kind="update",
                                applied=True,
                                detail="manifest index auto-refreshed",
                            )
                        )
                    if idx_md.exists():
                        changes.append(
                            Change(
                                path=str(idx_md),
                                kind="update",
                                applied=True,
                                detail="manifest index auto-refreshed",
                            )
                        )


def _delegate_plan_executed_to_finalize(
    plan_recs: list[ArtifactRecord],
    all_recs: list[ArtifactRecord],
    repo_root: Path,
    args: argparse.Namespace,
    term,
) -> int:
    """Route a plan -> `executed` `aw set`/`ipd set` request into the gated `aw ipd finalize` (Order wezhxg).

    The raw ungated plan-terminal move is removed: `executed` is unreachable without the begin
    receipt, scope reconciliation, three lint gates, attributed history, and lifecycle commit. This
    delegates transparently (OQ-03) rather than refusing-and-redirecting. A required gate input that
    is genuinely absent (a non-generic `--actor`) fails closed (exit 2) with the exact command to
    supply it - honest, never a fabricated actor, never a bare dead-end.
    """
    from agent_workflows import ipd_lifecycle as _life
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        NextAction,
        select_output,
    )

    ctx = select_output(args)

    # Refuse a mixed batch (plan-executed + others) to keep the transaction one-IPD and unambiguous.
    others = [r for r in all_recs if r not in plan_recs]
    if others:
        msg = (
            "moving a plan to 'executed' delegates into `aw ipd finalize` and must be run per-plan; "
            "do not mix it with other targets in one `aw set`."
        )
        if ctx.is_agent or ctx.is_json:
            return get_renderer(ctx).emit(
                CommandResult(
                    command="set", status="cannot-run", exit_code=2, summary=msg
                ),
                ctx,
            )
        term.status("fail", msg)
        return 2

    actor = (getattr(args, "actor", None) or "").strip()
    message = (getattr(args, "message", None) or "").strip()
    apply = not getattr(args, "dry_run", False)
    scope_reasons = _life._parse_scope_reason_flags(getattr(args, "scope_reason", None))
    scope_acks = _life._parse_scope_ack_flags(getattr(args, "scope_ack", None))

    overall = 0
    for rec in plan_recs:
        selector = rec.id6 or rec.path.name
        if not actor:
            hint = (
                f"aw set executed {selector} --actor <agent/model> --message <summary>"
                if not message
                else f"aw set executed {selector} --actor <agent/model> --message {message!r}"
            )
            summary = (
                "moving a plan to 'executed' now delegates into the gated `aw ipd finalize`, which "
                "REQUIRES an attributed --actor <agent/model> (the machine-default is rejected). "
                f"Re-run: {hint}"
            )
            if ctx.is_agent or ctx.is_json:
                overall = 2
                get_renderer(ctx).emit(
                    CommandResult(
                        command="set",
                        status="cannot-run",
                        exit_code=2,
                        summary=summary,
                        next_actions=[
                            NextAction(command=hint, description="supply the actor")
                        ],
                    ),
                    ctx,
                )
                continue
            term.status("fail", summary)
            overall = 2
            continue

        result = _life.finalize(
            repo_root,
            rec.path,
            actor,
            message or f"finalize {selector} -> executed",
            apply=apply,
            scope_reasons=scope_reasons,
            scope_acks=scope_acks,
            plan_selector=selector,
        )
        if ctx.is_agent or ctx.is_json:
            status = {0: "clean", 1: "findings", 2: "cannot-run"}.get(
                result.exit_code, "cannot-run"
            )
            diags = [
                Diagnostic(
                    location=str(rec.path),
                    rule="IPD-FINALIZE",
                    detail=f,
                    severity="error",
                )
                for f in result.findings
            ]
            get_renderer(ctx).emit(
                CommandResult(
                    command="set",
                    status=status,
                    exit_code=result.exit_code,
                    summary=result.message,
                    diagnostics=diags,
                    data={"commit": result.commit},
                ),
                ctx,
            )
        else:
            prefix = {0: "", 1: "refused: ", 2: "error: "}.get(
                result.exit_code, "error: "
            )
            term.line(f"aw set -> ipd finalize: {prefix}{result.message}")
            for f in result.findings:
                term.line(f"  {f}")
        if result.exit_code != 0:
            overall = result.exit_code if overall == 0 else overall
    return overall


def run_set_command(
    raw_args: list[str],
    scoped_type: str | None = None,
    repo_root: Path | None = None,
    args: argparse.Namespace | None = None,
    term: Term | None = None,
) -> int:
    """Core execution engine for `aw set`, `aw ipd set`, `aw spec set`, etc."""
    if term is None:
        term = Term()
    if repo_root is None:
        from agent_workflows.project_context import resolve_verb_repo_root

        repo_root = resolve_verb_repo_root(getattr(args, "dir", None) if args else None)

    if args is None:
        args = argparse.Namespace()

    if not raw_args:
        term.status("fail", "aw set: missing status and target selector(s).")
        return 2

    first_tok = raw_args[0]
    target_status: str
    selector_tokens: list[str]

    if (
        scoped_type is None
        and canonical_type(first_tok) is not None
        and len(raw_args) >= 3
    ):
        scoped_type = canonical_type(first_tok)
        target_status = raw_args[1]
        selector_tokens = raw_args[2:]
    else:
        target_status = raw_args[0]
        selector_tokens = raw_args[1:]

    if not selector_tokens:
        term.status(
            "fail",
            "aw set: at least one target selector (id6, setid, or filename) is required.",
        )
        return 2

    scoped_type_canonical = canonical_type(scoped_type)

    all_records = inventory_all_artifacts(repo_root)

    resolved_by_token: dict[str, list[ArtifactRecord]] = {}
    matched_records: list[ArtifactRecord] = []
    seen_paths: set[str] = set()

    force = bool(getattr(args, "force", False))
    for tok in selector_tokens:
        matches = match_selector(
            tok, all_records, repo_root, scoped_type=scoped_type_canonical
        )
        if not matches:
            if scoped_type_canonical:
                term.status(
                    "fail", f"No {scoped_type_canonical} artifact matched '{tok}'."
                )
            else:
                term.status("fail", f"No artifact matched '{tok}'.")
            return 2

        # IPD laykok E-07: kind-aware ambiguity for the MUTATING `set` verb. A setid legitimately
        # transitions a whole Set (act on all, no --force); a UNIQUE-id collision (id6/path/stem)
        # ALWAYS refuses; a filename SUBSTRING multi-match refuses unless --force. Determine the
        # winning kind via the unified resolver (scoped to the matched type when known).
        if len(matches) > 1:
            from agent_workflows import selectors as _sel

            _kind = None
            _probe_type = scoped_type_canonical or (
                matches[0].record_type if matches else None
            )
            if _probe_type:
                _kind = _sel.resolve(repo_root, _probe_type, tok).kind
            if _kind == _sel.MATCH_SETID:
                pass  # intentional multi-target
            elif _kind in _sel.UNIQUE_KINDS:
                cand = "\n  ".join(str(m.path) for m in matches)
                term.status(
                    "fail",
                    f"Selector '{tok}' is a {_kind} collision matching multiple files "
                    f"(a data bug to fix, not overridable by --force):\n  {cand}",
                )
                return 2
            elif not force:
                cand = "\n  ".join(str(m.path) for m in matches)
                term.status(
                    "fail",
                    f"Selector '{tok}' is ambiguous ({_kind or 'substring'}) matching multiple "
                    f"files; pass --force to act on all:\n  {cand}",
                )
                return 2

        if scoped_type_canonical:
            mismatches = [m for m in matches if m.record_type != scoped_type_canonical]
            if mismatches:
                mismatch_types = sorted({m.record_type for m in mismatches})
                term.status(
                    "fail",
                    f"Type mismatch: selector '{tok}' resolved to artifact(s) of type {mismatch_types}, "
                    f"but command is scoped to '{scoped_type_canonical}'. Refusing before making changes.",
                )
                return 2

        resolved_by_token[tok] = matches
        for m in matches:
            rp_key = str(m.path.resolve())
            if rp_key not in seen_paths:
                seen_paths.add(rp_key)
                matched_records.append(m)

    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        Diagnostic,
        NextAction,
        select_output,
    )

    ctx = select_output(args)
    for rec in matched_records:
        ok, err_msg = validate_transition_allowed(rec, target_status, args)
        if not ok:
            if ctx.is_agent or ctx.is_json:
                res = CommandResult(
                    command="set",
                    status="findings",
                    exit_code=1,
                    summary=f"Validation error on {rec.path.name}: {err_msg}",
                    diagnostics=[
                        Diagnostic(
                            location=str(rec.path),
                            rule="status.invalid_transition",
                            detail=err_msg or "transition not allowed",
                            severity="error",
                        )
                    ],
                )
                return get_renderer(ctx).emit(res, ctx)
            term.status(
                "fail",
                f"Validation error on {rec.path.name}: {err_msg}. Refusing before making changes.",
            )
            return 1

    # ipdgates Order wezhxg: a request to move a PLAN to `executed` (or its `done` alias) MUST NOT
    # use the raw ungated move - it transparently DELEGATES into the gated `aw ipd finalize`
    # transaction (begin receipt + scope reconciliation + three gates + attributed history +
    # rollback). Keyed on record_type == "plans" AND normalized target `executed` (NOT the status
    # token alone, because PROMPTS share the `executed`/`done` tokens). All other transitions -
    # nonterminal plan (draft/to-review/reviewed/approved), plan RETIREMENT (superseded/not-executed),
    # and every non-plan artifact terminal transition - are UNCHANGED below.
    _plan_executed = [
        rec
        for rec in matched_records
        if rec.record_type == "plans"
        and normalize_target_status(target_status, rec.record_type) == "executed"
    ]
    if _plan_executed:
        return _delegate_plan_executed_to_finalize(
            _plan_executed, matched_records, repo_root, args, term
        )

    is_dry_run = getattr(args, "dry_run", False)
    yes = getattr(args, "yes", False) or getattr(args, "assume_yes", False)

    if (ctx.is_agent or ctx.is_json) and not is_dry_run and not yes:
        changes = [
            Change(
                path=str(r.path),
                kind="update",
                applied=False,
                detail=f"status: {r.status or '-'} -> {normalize_target_status(target_status, r.record_type)}",
            )
            for r in matched_records
        ]
        cmd_str = f"aw set {' '.join(raw_args)} --yes"
        res = CommandResult(
            command="set",
            status="cannot-run",
            exit_code=2,
            summary="confirmation required (--yes needed to execute mutation)",
            changes=changes,
            next_actions=[
                NextAction(command=cmd_str, description="Apply status changes")
            ],
            verified=False,
            complete=False,
        )
        return get_renderer(ctx).emit(res, ctx)

    if is_dry_run:
        if ctx.is_agent or ctx.is_json:
            changes = [
                Change(
                    path=str(r.path),
                    kind="update",
                    applied=False,
                    detail=f"status: {r.status or '-'} -> {normalize_target_status(target_status, r.record_type)}",
                )
                for r in matched_records
            ]
            res = CommandResult(
                command="set",
                status="clean",
                exit_code=0,
                summary=f"would update status on {len(matched_records)} artifact(s)",
                changes=changes,
                data={
                    "items": [
                        {
                            "path": str(r.path),
                            "type": r.record_type,
                            "old_status": r.status,
                            "new_status": normalize_target_status(
                                target_status, r.record_type
                            ),
                            "dry_run": True,
                        }
                        for r in matched_records
                    ]
                },
                verified=True,
                complete=True,
            )
            return get_renderer(ctx).emit(res, ctx)

        for r in matched_records:
            nstat = normalize_target_status(target_status, r.record_type)
            curr = (r.status or "").strip().lower()
            changed = curr != nstat.strip().lower()
            term.line(
                _format_status_transition_line(
                    r, r.path, nstat, term, args, dry_run=True, changed=changed
                )
            )
        return 0

    results: list[tuple[Path, str, ArtifactRecord, bool]] = []
    touched_types: set[str] = set()
    for rec in matched_records:
        old_text = rec.raw_text
        dest_path, norm_stat = apply_status_change(rec, target_status, repo_root, args)
        new_text = dest_path.read_text(encoding="utf-8") if dest_path.exists() else ""
        changed = (old_text != new_text) or (dest_path.resolve() != rec.path.resolve())
        results.append((dest_path, norm_stat, rec, changed))
        if changed:
            touched_types.add(rec.record_type)

    if ctx.is_agent or ctx.is_json:
        changes = [
            Change(
                path=str(dest),
                kind="update" if changed else "noop",
                applied=changed,
                detail=(
                    f"status: {rec.status or '-'} -> {norm_stat}"
                    if changed
                    else f"status: {norm_stat} (unchanged)"
                ),
            )
            for dest, norm_stat, rec, changed in results
        ]
        _auto_index_types(touched_types, repo_root, changes=changes)
        res = CommandResult(
            command="set",
            status="clean",
            exit_code=0,
            summary=f"updated status on {len([r for r in results if r[3]])} artifact(s)",
            changes=changes,
            data={
                "items": [
                    {
                        "path": str(dest),
                        "type": rec.record_type,
                        "old_status": rec.status,
                        "new_status": norm_stat,
                        "changed": changed,
                    }
                    for dest, norm_stat, rec, changed in results
                ]
            },
            verified=True,
            complete=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    _auto_index_types(touched_types, repo_root)

    for dest, norm_stat, rec, changed in results:
        term.line(
            _format_status_transition_line(
                rec, dest, norm_stat, term, args, dry_run=False, changed=changed
            )
        )

    return 0
