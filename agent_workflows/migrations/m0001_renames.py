"""Step-3 legacy-name rename map, protected citation planner, and scratch apply for m0001.

Implements spec 4sd62s Section 5.2 step 3, OQ-26, OQ-27, and OQ-28:
- ``classify_name``: tests ``artifact_naming._LEGACY_TIMESTAMP_RE`` before
  ``artifact_naming.parse_clustered`` while keeping clustered names with a
  4-digit Set id distinct from legacy names whose slug starts with a 6-letter
  word.
- ``build_rename_map``: computes the deterministic legacy-to-clustered rename
  map with journaled ``id6`` reuse, existing ``Id``/``Set``/logged ``Order``
  preservation, OQ-02 template/non-record exclusions, and collision refusals.
- ``plan_citation_rewrites``: guards against out-of-scratch records resolution,
  plans rewrites once through ``artifact_refs.plan_reference_rewrites_with_warnings``
  over ``M0001_SCAN_ROOTS``, records protected spans (``## Workflow history``,
  review ``- Verdict:`` lines, and explicit exemptions), and produces per-location
  substituted counts and unchanged-occurrence diagnostics.
- ``apply_step3``: applies protected-span-masked citation rewrites via
  ``artifact_core.atomic_write``, asserts byte-identical protected spans,
  moves mapped files inside the scratch copy via ``Path.rename``, and records
  resumable per-file progress in the journal.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

from agent_workflows import (
    artifact_core,
    artifact_meta,
    artifact_naming,
    artifact_refs,
    layout_migration,
    project_context,
    record_history,
)
from agent_workflows.migrations import m0001_discover

# --------------------------------------------------------------------------------------
# Generic scan roots and structural non-record exclusions (no repository constants)
# --------------------------------------------------------------------------------------

M0001_SCAN_ROOTS: Tuple[str, ...] = artifact_core.REFERENCE_SCAN_ROOTS + (
    "agent_workflows",
    "docs",
    ".aw/system",
    "CHANGELOG.md",
    "TODO.md",
    ".gitignore",
    ".aw/.gitignore",
)

OQ02_EXCLUDED_DIRNAMES: frozenset[str] = m0001_discover.EXCLUDED_DIRNAMES

OQ02_EXCLUDED_FILENAMES: frozenset[str] = frozenset({"README.md", "STATUS.md"})

_PROMPT_COMMENT_RE = re.compile(
    r"\A<!--\s*(?:aw-prompt|aw-managed-prompt):\s*(.*?)\s*-->", re.DOTALL
)
_VERDICT_LINE_RE = re.compile(r"^\s*-\s*Verdict:\s*")


class RenameRefusalError(layout_migration.MigrationError, ValueError):
    """Raised when m0001 step-3 rename mapping, citation planning, or apply refuses."""


@dataclass(frozen=True)
class RenameEntry:
    """One mapped legacy-timestamp record and its deterministic clustered target."""

    old_rel: str
    new_rel: str
    old_name: str
    new_name: str
    id6: str
    minted: bool
    set_id: str
    order: int
    date: str
    slug: str
    facet: Optional[str]
    record_type: str


@dataclass(frozen=True)
class RenameMap:
    """Result of ``build_rename_map`` with entries and pre-existing unmapped duplicates."""

    entries: Tuple[RenameEntry, ...]
    unmapped_plan_duplicates: Tuple[Tuple[Tuple[str, int], Tuple[str, ...]], ...] = ()

    @property
    def name_map(self) -> Dict[str, str]:
        """Mapping from legacy basename to clustered basename."""
        return {entry.old_name: entry.new_name for entry in self.entries}

    @property
    def path_map(self) -> Dict[str, str]:
        """Mapping from legacy records-relative POSIX path to new path."""
        return {entry.old_rel: entry.new_rel for entry in self.entries}

    def get_by_id6(self, id6: str) -> Optional[RenameEntry]:
        """Return the entry carrying ``id6``, or None."""
        for entry in self.entries:
            if entry.id6 == id6:
                return entry
        return None

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def __bool__(self) -> bool:
        return bool(self.entries)

    def format_summary(self) -> str:
        """Render a deterministic human-readable summary of the rename map."""
        minted_count = sum(1 for e in self.entries if e.minted)
        preserved_count = len(self.entries) - minted_count
        lines = [
            f"RenameMap: {len(self.entries)} entries "
            f"({minted_count} minted, {preserved_count} preserved), "
            f"{len(self.unmapped_plan_duplicates)} pre-existing unmapped plan duplicate pair(s)"
        ]
        for e in self.entries:
            tag = "minted" if e.minted else "kept"
            lines.append(f"  {e.id6} ({tag}): {e.old_rel} -> {e.new_rel}")
        return "\n".join(lines)


@dataclass(frozen=True)
class ProtectedSpan:
    """A byte-exact span in a file that ``apply_step3`` masks before rewriting."""

    start: int
    end: int
    reason: str
    line_no: int
    text: str


@dataclass(frozen=True)
class UnchangedOccurrence:
    """One citation occurrence intentionally left unchanged by step 3."""

    file: str
    line: int
    reason: str
    token: str


@dataclass(frozen=True)
class CitationPlan:
    """Planned citation rewrites, protected spans, per-location counts, and unchanged list."""

    scratch_root: Path
    name_map: Dict[str, str]
    edits: Tuple[artifact_refs.RefEdit, ...]
    warnings: Tuple[str, ...]
    protected_spans_by_file: Dict[str, Tuple[ProtectedSpan, ...]]
    substituted_by_file: Dict[str, int]
    location_counts: Dict[str, int]
    total_substituted: int
    unchanged_occurrences: Tuple[UnchangedOccurrence, ...]
    unchanged_counts_by_reason: Dict[str, int]

    def format_report(self) -> str:
        """Render the per-location count table and unchanged-occurrence summary."""
        lines = [
            f"CitationPlan: {self.total_substituted} substituted across "
            f"{sum(1 for v in self.substituted_by_file.values() if v > 0)} file(s), "
            f"{len(self.warnings)} warning(s), "
            f"{len(self.unchanged_occurrences)} unchanged occurrence(s)"
        ]
        lines.append("Location counts:")
        for loc in sorted(self.location_counts):
            lines.append(f"  {loc}: {self.location_counts[loc]}")
        lines.append("Unchanged by reason:")
        for reason in sorted(self.unchanged_counts_by_reason):
            lines.append(f"  {reason}: {self.unchanged_counts_by_reason[reason]}")
        return "\n".join(lines)


# --------------------------------------------------------------------------------------
# Name classification (E-01)
# --------------------------------------------------------------------------------------


def classify_name(name: str) -> str:
    """Classify ``name`` as ``'legacy'``, ``'clustered'``, or ``'other'``.

    Tests ``artifact_naming._LEGACY_TIMESTAMP_RE`` before
    ``artifact_naming.parse_clustered`` so legacy names whose slug starts with
    a 6-letter word classify as ``'legacy'``, while clustered names with a
    4-digit Set id and a real digit-bearing ``id6`` or non-HHMM Set id still
    classify as ``'clustered'``.
    """
    return m0001_discover.classify_name(name)


# --------------------------------------------------------------------------------------
# Metadata helpers for rename map
# --------------------------------------------------------------------------------------


def _is_within_strict(child: Path, parent: Path) -> bool:
    """Return True iff ``child`` is strictly inside ``parent`` (after resolving)."""
    try:
        rel = child.resolve().relative_to(parent.resolve())
        return rel != Path(".")
    except ValueError:
        return False


def _rel_posix(path: Path, root: Path) -> str:
    """Return POSIX path of ``path`` relative to ``root`` (resolved if needed)."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.resolve().relative_to(root.resolve()).as_posix()


def _walk_candidate_records(
    records_root: Path, *, repo_root: Optional[Path] = None
) -> List[Path]:
    """Return non-excluded, classifiable record paths under ``records_root`` in sorted order."""
    if not records_root.is_dir():
        return []
    inv = m0001_discover.discover(
        repo_root if repo_root is not None else records_root,
        records_root=records_root,
    )
    return [r.path for r in inv.records]


def _walk_plan_files(records_root: Path) -> List[Path]:
    """Walk ``records_root / 'plans'`` returning all plan ``.md`` files in sorted order."""
    plans_dir = records_root / "plans"
    if not plans_dir.is_dir():
        return []
    found: List[Path] = []
    for cur_dir, dirs, files in os.walk(plans_dir):
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in OQ02_EXCLUDED_DIRNAMES and not d.endswith(".data")
        )
        cur_path = Path(cur_dir)
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            if (
                fname in OQ02_EXCLUDED_FILENAMES
                or fname.startswith("INDEX.")
                or fname.endswith(".review.md")
            ):
                continue
            found.append(cur_path / fname)
    return found


def _parse_prompt_comment_fields(text: str) -> Dict[str, str]:
    """Extract key/value pairs from a leading ``<!-- aw-prompt: ... -->`` comment."""
    stripped = text.lstrip()
    m_prompt = _PROMPT_COMMENT_RE.match(stripped)
    if not m_prompt:
        return {}
    inner = m_prompt.group(1)
    # Strip optional `. This file is ...` trailer if present on aw-prompt comments.
    if " . " in inner:
        inner = inner.split(" . ", 1)[0]
    out: Dict[str, str] = {}
    for item in inner.split("|"):
        if ":" in item:
            k, v = item.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _extract_infile_fields(text: str) -> Dict[str, str]:
    """Extract raw ``Id``/``Set``/``Order`` metadata strings from YAML, prompt comment, or bullets."""
    if text.startswith("---"):
        yaml_probe, _ = artifact_meta._parse_yaml_front_matter(text)
        after_fence = text.split("\n", 1)[1][:200] if "\n" in text else ""
        if yaml_probe and not artifact_meta._BULLET_RE.search(after_fence):
            return dict(yaml_probe)

    if text.lstrip().startswith("<!--"):
        prompt_fields = _parse_prompt_comment_fields(text)
        if prompt_fields:
            return prompt_fields

    bullets, _, _ = artifact_meta._parse_bullet_metadata(text)
    return bullets


def _parse_terse_set(raw_set: Optional[str]) -> Optional[str]:
    """Extract the terse Set id from a ``- Set: <terse> (<desc>)`` field value."""
    if not raw_set:
        return None
    before_paren = raw_set.split("(", 1)[0].strip()
    if not before_paren:
        return None
    return before_paren.split()[0]


def _parse_order_int(raw_order: Optional[str], rel_path: str) -> Optional[int]:
    """Parse an integer ``Order`` field value, raising RenameRefusalError if malformed."""
    if raw_order is None:
        return None
    cleaned = raw_order.strip()
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError as exc:
        raise RenameRefusalError(
            f"Refused: {rel_path} declares non-integer Order {raw_order!r}"
        ) from exc


def _filename_id6_non_legacy(filename: str) -> Optional[str]:
    """Extract ``id6`` from a non-legacy clustered or attributed filename."""
    if classify_name(filename) == "legacy":
        return None
    m_attr = artifact_naming.parse_attributed(filename)
    if m_attr and artifact_core.is_valid_id6(m_attr.id6):
        return m_attr.id6
    m_clust = artifact_naming.parse_clustered(filename)
    if m_clust and artifact_core.is_valid_id6(m_clust.group("id6")):
        return m_clust.group("id6")
    m_pref = artifact_naming.parse_clustered_prefix(filename)
    if m_pref and artifact_core.is_valid_id6(m_pref.group("id6")):
        return m_pref.group("id6")
    return None


def _load_journal_minted(
    journal: Optional[Union[Dict[str, Any], str, Path]],
) -> Tuple[Optional[Path], Optional[Dict[str, Any]], Dict[str, str]]:
    """Read ``minted_ids`` from ``journal`` (dict, file/dir path, or None)."""
    if journal is None:
        return None, None, {}
    if isinstance(journal, dict):
        raw = journal.get("minted_ids") or {}
        return None, journal, {str(k): str(v) for k, v in raw.items()}
    p = Path(journal)
    jpath = p / "journal.json" if p.is_dir() else p
    if jpath.is_file():
        data = json.loads(jpath.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RenameRefusalError(
                f"Refused: journal at {jpath} must contain a JSON object"
            )
    else:
        data = {"minted_ids": {}}
    raw = data.get("minted_ids") or {}
    return jpath, data, {str(k): str(v) for k, v in raw.items()}


def _save_journal_data(
    jpath: Optional[Path],
    jdata: Optional[Dict[str, Any]],
) -> None:
    """Persist ``jdata`` atomically to ``jpath`` when ``jpath`` is not None."""
    if jpath is None or jdata is None:
        return
    payload = json.dumps(jdata, indent=2, ensure_ascii=False) + "\n"
    artifact_core.atomic_write(jpath, payload)


def _record_type_from_rel(rel_path: str, facet: Optional[str]) -> str:
    """Map a records-root-relative path and facet to its logical record type."""
    top_dir = Path(rel_path).parts[0] if Path(rel_path).parts else ""
    dir_map = {
        "plans": "ipd",
        "specs": "spec",
        "backlog": "backlog",
        "research": "research",
        "releases": "release",
        "prompts": "prompt",
        "walkthroughs": "walkthrough",
        "roadmaps": "roadmap",
    }
    if top_dir in dir_map:
        return dir_map[top_dir]
    return facet or "other"


def _parse_non_legacy_name_parts(
    path: Path,
    rel_path: str,
    repo_path: Path,
) -> Tuple[str, str, Optional[str], int]:
    """Return ``(date, slug, facet, default_nn)`` for a non-legacy-timestamp id-less record."""
    fname = path.name
    m_dsf = artifact_naming._DATED_SLUG_FACET_RE.match(fname)
    if m_dsf:
        date = m_dsf.group("date")
        raw_slug = m_dsf.group("slug")
        raw_facet = m_dsf.group("facet")
    else:
        m_hd = m0001_discover._HYPHEN_DATE_PREFIX_RE.match(fname)
        if m_hd:
            date = f"{m_hd.group('y')}{m_hd.group('m')}{m_hd.group('d')}"
            raw_slug = m_hd.group("rest")
            raw_facet = m_hd.group("facet")
        else:
            date = m0001_discover.infer_record_date(path, repo_path)
            stem = fname[:-3] if fname.endswith(".md") else fname
            raw_facet = None
            if "." in stem:
                base, cand_facet = stem.rsplit(".", 1)
                if cand_facet in artifact_naming.ARTIFACT_TYPE_FACETS:
                    raw_slug = base
                    raw_facet = cand_facet
                else:
                    raw_slug = stem
            else:
                raw_slug = stem

    if raw_facet is not None and raw_facet not in artifact_naming.ARTIFACT_TYPE_FACETS:
        raise RenameRefusalError(
            f"Refused: record {rel_path} has unknown facet {raw_facet!r} "
            f"(must be in ARTIFACT_TYPE_FACETS)"
        )

    top_dir = Path(rel_path).parts[0] if Path(rel_path).parts else ""
    facet = (
        raw_facet if raw_facet is not None else artifact_naming.TYPE_FACET.get(top_dir)
    )
    slug = artifact_core.kebab_slug(raw_slug, 60, "record")
    return date, slug, facet, 1


def build_rename_map(
    repo: Union[str, Path],
    journal: Optional[Union[Dict[str, Any], str, Path]] = None,
) -> RenameMap:
    """Build the deterministic legacy-name and id-less rename map for ``repo``.

    Scans every discovered candidate record under
    ``project_context.project_records_dir(repo)`` (excluding comms, ``.data/``,
    READMEs, templates, and unclassifiable files). Reuses minted ``id6`` values
    stored in ``journal['minted_ids']``, or lazily seeds the repository-wide
    collision pool once from ``artifact_core.global_id6s`` and generates
    repository-unique ``id6`` values in memory via
    ``artifact_core.generate_id6``, recording them in ``journal`` before
    returning (when ``journal=None``, mints in memory and writes nothing).
    """
    repo_path = Path(repo)
    records_root = project_context.project_records_dir(repo_path)
    jpath, jdata, journal_minted = _load_journal_minted(journal)

    candidate_files = _walk_candidate_records(records_root, repo_root=repo_path)

    # First pass: index all existing record id6s and unmapped plan (set, order) pairs.
    other_ids_by_id: Dict[str, List[str]] = {}
    rename_targets: List[Tuple[Path, str]] = []
    unmapped_plan_pairs: Dict[Tuple[str, int], List[str]] = {}

    for path in candidate_files:
        rel_path = _rel_posix(path, records_root)
        text = path.read_text(encoding="utf-8", errors="replace")
        fields = _extract_infile_fields(text)
        raw_id = fields.get("Id") or fields.get("id")
        infile_id = (
            raw_id.strip()
            if isinstance(raw_id, str) and artifact_core.is_valid_id6(raw_id.strip())
            else None
        )
        fname_id = _filename_id6_non_legacy(path.name)
        is_legacy_name = classify_name(path.name) == "legacy"

        if is_legacy_name:
            rename_targets.append((path, rel_path))
            if infile_id is not None:
                other_ids_by_id.setdefault(infile_id, []).append(rel_path)
        elif infile_id is None and fname_id is None:
            rename_targets.append((path, rel_path))
        else:
            rec_id = infile_id or fname_id
            if rec_id is not None:
                other_ids_by_id.setdefault(rec_id, []).append(rel_path)
            if rel_path.startswith("plans/"):
                terse_set = _parse_terse_set(fields.get("Set") or fields.get("set"))
                raw_ord = fields.get("Order") or fields.get("order")
                order_nn: Optional[int] = None
                if raw_ord is not None and str(raw_ord).strip():
                    try:
                        order_nn = int(str(raw_ord).strip())
                    except ValueError:
                        order_nn = None
                m_clu = artifact_naming.parse_clustered(path.name)
                if m_clu:
                    if terse_set is None:
                        terse_set = m_clu.group("set")
                    if order_nn is None:
                        order_nn = int(m_clu.group("nn"))
                if terse_set is not None and order_nn is not None:
                    norm_set = artifact_core.kebab(terse_set)
                    unmapped_plan_pairs.setdefault((norm_set, order_nn), []).append(
                        rel_path
                    )

    unmapped_duplicates: List[Tuple[Tuple[str, int], Tuple[str, ...]]] = []
    for pair, paths in sorted(unmapped_plan_pairs.items()):
        if len(paths) > 1:
            unmapped_duplicates.append((pair, tuple(sorted(paths))))

    # Second pass: build rename entries for every legacy-name and id-less record.
    entries: List[RenameEntry] = []
    minted_in_pass: Set[str] = set()
    new_journal_entries: Dict[str, str] = {}
    by_old_name: Dict[str, List[str]] = {}
    mapped_id_owners: Dict[str, List[str]] = {}

    all_known_ids: Set[str] = set(other_ids_by_id.keys()) | set(journal_minted.values())
    global_pool: Optional[Set[str]] = None

    for path, rel_path in rename_targets:
        m_leg = artifact_naming._LEGACY_TIMESTAMP_RE.match(path.name)
        if m_leg is not None:
            facet = m_leg.group("facet")
            if facet is not None and facet not in artifact_naming.ARTIFACT_TYPE_FACETS:
                raise RenameRefusalError(
                    f"Refused: legacy record {rel_path} has unknown facet {facet!r} "
                    f"(must be in ARTIFACT_TYPE_FACETS)"
                )
            date_str = m_leg.group("date")
            slug_str = m_leg.group("slug")
            default_nn = int(m_leg.group("nn"))
        else:
            date_str, slug_str, facet, default_nn = _parse_non_legacy_name_parts(
                path, rel_path, repo_path
            )

        text = path.read_text(encoding="utf-8", errors="replace")
        fields = _extract_infile_fields(text)
        raw_id = fields.get("Id") or fields.get("id")
        existing_id: Optional[str] = None
        if isinstance(raw_id, str) and raw_id.strip():
            cand_id = raw_id.strip()
            if not artifact_core.is_valid_id6(cand_id):
                raise RenameRefusalError(
                    f"Refused: legacy record {rel_path} declares invalid Id {cand_id!r}"
                )
            existing_id = cand_id

        if existing_id is not None:
            id6 = existing_id
            minted = False
        else:
            reused = journal_minted.get(rel_path)
            if reused is not None:
                if not artifact_core.is_valid_id6(reused):
                    raise RenameRefusalError(
                        f"Refused: journal holds invalid id6 {reused!r} for {rel_path}"
                    )
                id6 = reused
                minted = True
            else:
                if global_pool is None:
                    global_pool = (
                        artifact_core.global_id6s(repo_path)
                        | all_known_ids
                        | minted_in_pass
                    )
                id6 = artifact_core.generate_id6(global_pool)
                minted = True
                global_pool.add(id6)
                minted_in_pass.add(id6)
                all_known_ids.add(id6)
                new_journal_entries[rel_path] = id6

            # Refusal (c): minted or reused id6 must not equal another record's id6.
            colliding = [p for p in other_ids_by_id.get(id6, []) if p != rel_path]
            if colliding:
                raise RenameRefusalError(
                    f"Refused (c): minted/reused id6 {id6!r} for {rel_path} collides with "
                    f"existing record(s): {', '.join(colliding)}"
                )

        mapped_id_owners.setdefault(id6, []).append(rel_path)
        if len(mapped_id_owners[id6]) > 1:
            raise RenameRefusalError(
                f"Refused (c): id6 {id6!r} is shared by multiple mapped records: "
                f"{', '.join(mapped_id_owners[id6])}"
            )

        terse_set = _parse_terse_set(fields.get("Set") or fields.get("set"))
        set_id = terse_set if terse_set else id6
        logged_order = _parse_order_int(
            fields.get("Order") or fields.get("order"), rel_path
        )
        order_nn = logged_order if logged_order is not None else default_nn

        new_name = artifact_naming.build_clustered_name(
            date=date_str,
            set_id=set_id,
            order=order_nn,
            id6=id6,
            slug=slug_str,
            artifact_type=facet,
        )
        parent_rel = Path(rel_path).parent
        new_rel = (
            new_name if parent_rel == Path(".") else (parent_rel / new_name).as_posix()
        )
        record_type = _record_type_from_rel(rel_path, facet)

        by_old_name.setdefault(path.name, []).append(rel_path)
        entries.append(
            RenameEntry(
                old_rel=rel_path,
                new_rel=new_rel,
                old_name=path.name,
                new_name=new_name,
                id6=id6,
                minted=minted,
                set_id=artifact_core.kebab(set_id),
                order=order_nn,
                date=date_str,
                slug=slug_str,
                facet=facet,
                record_type=record_type,
            )
        )

    # Refusal (b): duplicate legacy filenames across mapped records.
    for old_name, paths in sorted(by_old_name.items()):
        if len(paths) > 1:
            raise RenameRefusalError(
                f"Refused (b): duplicate legacy filename {old_name!r} at {', '.join(paths)}"
            )

    # Refusal (a): a mapped plan's new (Set, Order) collides with ANY other plan.
    mapped_plan_pairs: Dict[Tuple[str, int], List[str]] = {}
    for entry in entries:
        if entry.old_rel.startswith("plans/") or entry.facet == "ipd":
            pair = (entry.set_id, entry.order)
            unmapped_hits = unmapped_plan_pairs.get(pair, [])
            if unmapped_hits:
                raise RenameRefusalError(
                    f"Refused (a): mapped plan {entry.old_rel} -> {entry.new_rel} "
                    f"with (Set={entry.set_id!r}, Order={entry.order}) collides with "
                    f"unmapped plan(s): {', '.join(unmapped_hits)}"
                )
            mapped_plan_pairs.setdefault(pair, []).append(entry.old_rel)
            if len(mapped_plan_pairs[pair]) > 1:
                raise RenameRefusalError(
                    f"Refused (a): mapped plans share (Set={entry.set_id!r}, "
                    f"Order={entry.order}): {', '.join(mapped_plan_pairs[pair])}"
                )

    # All checks passed: persist newly minted ids into the journal before returning.
    if jdata is not None and new_journal_entries:
        merged_minted = dict(jdata.get("minted_ids") or {})
        merged_minted.update(new_journal_entries)
        jdata["minted_ids"] = merged_minted
        _save_journal_data(jpath, jdata)
    elif jdata is not None and "minted_ids" not in jdata:
        jdata["minted_ids"] = {}

    return RenameMap(
        entries=tuple(entries),
        unmapped_plan_duplicates=tuple(unmapped_duplicates),
    )


# --------------------------------------------------------------------------------------
# Protected-span detection, masking, and citation planning (E-02)
# --------------------------------------------------------------------------------------


def _coerce_name_map(
    rename_map: Union[RenameMap, Sequence[RenameEntry], Dict[str, str]],
) -> Dict[str, str]:
    """Extract ``{old_basename: new_basename}`` from ``RenameMap`` or mapping."""
    if isinstance(rename_map, RenameMap):
        return rename_map.name_map
    if isinstance(rename_map, dict):
        return {Path(k).name: Path(v).name for k, v in rename_map.items()}
    return {e.old_name: e.new_name for e in rename_map}


def _coerce_entries(
    rename_map: Union[RenameMap, Sequence[RenameEntry]],
) -> Tuple[RenameEntry, ...]:
    if isinstance(rename_map, RenameMap):
        return rename_map.entries
    return tuple(rename_map)


def _line_offsets(text: str) -> List[Tuple[int, int, str]]:
    """Return ``[(start_offset, end_offset, line_text), ...]`` preserving line endings."""
    out: List[Tuple[int, int, str]] = []
    pos = 0
    for line in text.splitlines(keepends=True):
        end = pos + len(line)
        out.append((pos, end, line))
        pos = end
    return out


def _is_review_file(path: Path, records_dir: Path) -> bool:
    """True iff ``path`` is a review record (under ``reviews/`` or ``*.review.md``)."""
    if path.name.endswith(".review.md"):
        return True
    try:
        rel = path.resolve().relative_to(records_dir.resolve())
        return bool(rel.parts) and rel.parts[0] == "reviews"
    except ValueError:
        return False


def _exemption_patterns_for_name(old_name: str) -> List[Tuple[str, re.Pattern[str]]]:
    """Return ordered ``(kind, regex)`` patterns matching ``old_name`` and all derived stems."""
    patterns: List[Tuple[str, re.Pattern[str]]] = [
        ("full", re.compile(re.escape(old_name)))
    ]
    whole = artifact_refs._whole_stem(old_name)
    if whole != old_name:
        patterns.append(("whole", artifact_refs._boundaried(whole)))
    leg = artifact_refs._legacy_prefix_stem(old_name)
    if leg is not None:
        patterns.append(("legacy", artifact_refs._boundaried(leg)))
    facetless = artifact_refs._facetless_stem(old_name)
    if facetless is not None and facetless != whole:
        patterns.append(("facetless", artifact_refs._facetless_boundaried(facetless)))
    return patterns


def _find_fenced_ranges(
    lines_info: List[Tuple[int, int, str]],
) -> List[Tuple[int, int, int]]:
    """Return ``[(start, end, start_line_no), ...]`` of Markdown fenced code blocks."""
    ranges: List[Tuple[int, int, int]] = []
    in_fence = False
    fence_marker = ""
    fence_start = 0
    fence_start_line = 0
    for idx, (s_off, e_off, line) in enumerate(lines_info, start=1):
        m = artifact_refs._FENCE_RE.match(line)
        if not in_fence:
            if m:
                in_fence = True
                fence_marker = m.group(2)
                fence_start = s_off
                fence_start_line = idx
        else:
            if m and m.group(2) == fence_marker:
                ranges.append((fence_start, e_off, fence_start_line))
                in_fence = False
                fence_marker = ""
    if in_fence and lines_info:
        ranges.append((fence_start, lines_info[-1][1], fence_start_line))
    return ranges


def _overlaps_any(start: int, end: int, intervals: Sequence[Tuple[int, int]]) -> bool:
    for a, b in intervals:
        if start < b and end > a:
            return True
    return False


def _find_protected_spans(
    text: str,
    rel_posix: str,
    *,
    is_review: bool,
    exemptions: Sequence[str],
) -> List[ProtectedSpan]:
    """Identify non-overlapping protected spans in ``text`` in document order.

    Span priority:
    1. ``history-section``: ``## Workflow history`` (outside fences) through next ``## ``
       heading (outside fences) or EOF.
    2. ``verdict-line``: ``- Verdict:`` line in a review record (outside history & fences).
    3. ``exemption``: exempted legacy filenames and their derived stems (outside
       history, verdict, and fenced blocks).
    """
    lines_info = _line_offsets(text)
    fenced_ranges = _find_fenced_ranges(lines_info)
    fenced_intervals = [(a, b) for a, b, _ in fenced_ranges]

    spans: List[ProtectedSpan] = []
    covered: List[Tuple[int, int]] = []

    # 1. History sections
    in_hist = False
    hist_start = 0
    hist_start_line = 0
    for idx, (s_off, _e_off, line) in enumerate(lines_info, start=1):
        in_fence_line = _overlaps_any(s_off, s_off + 1, fenced_intervals)
        if not in_hist:
            if not in_fence_line and line.strip() == "## Workflow history":
                in_hist = True
                hist_start = s_off
                hist_start_line = idx
        else:
            if not in_fence_line and line.startswith("## "):
                spans.append(
                    ProtectedSpan(
                        start=hist_start,
                        end=s_off,
                        reason="history-section",
                        line_no=hist_start_line,
                        text=text[hist_start:s_off],
                    )
                )
                covered.append((hist_start, s_off))
                in_hist = False
    if in_hist and lines_info:
        end_eof = lines_info[-1][1]
        spans.append(
            ProtectedSpan(
                start=hist_start,
                end=end_eof,
                reason="history-section",
                line_no=hist_start_line,
                text=text[hist_start:end_eof],
            )
        )
        covered.append((hist_start, end_eof))

    # 2. Review - Verdict: lines
    if is_review:
        for idx, (s_off, e_off, line) in enumerate(lines_info, start=1):
            if _overlaps_any(s_off, e_off, covered) or _overlaps_any(
                s_off, e_off, fenced_intervals
            ):
                continue
            if _VERDICT_LINE_RE.match(line):
                spans.append(
                    ProtectedSpan(
                        start=s_off,
                        end=e_off,
                        reason="verdict-line",
                        line_no=idx,
                        text=text[s_off:e_off],
                    )
                )
                covered.append((s_off, e_off))

    # 3. Exemptions for (rel_posix, legacy_filename) across all derived stems
    if exemptions:
        ex_matches: List[Tuple[int, int, int]] = []
        # Compute line number lookup helper
        line_starts = [s for s, _, _ in lines_info]
        for legacy_name in exemptions:
            for _kind, pat in _exemption_patterns_for_name(legacy_name):
                for m in pat.finditer(text):
                    ms, me = m.start(), m.end()
                    if _overlaps_any(ms, me, covered) or _overlaps_any(
                        ms, me, fenced_intervals
                    ):
                        continue
                    if _overlaps_any(ms, me, [(a, b) for a, b, _ in ex_matches]):
                        continue
                    # Determine 1-based line number
                    lineno = _line_number_at(line_starts, ms)
                    ex_matches.append((ms, me, lineno))
        for ms, me, lineno in sorted(ex_matches):
            spans.append(
                ProtectedSpan(
                    start=ms,
                    end=me,
                    reason="exemption",
                    line_no=lineno,
                    text=text[ms:me],
                )
            )
            covered.append((ms, me))

    spans.sort(key=lambda s: s.start)
    return spans


def _line_number_at(line_starts: List[int], offset: int) -> int:
    """Return 1-based line number for character ``offset`` given sorted ``line_starts``."""
    lo, hi = 0, len(line_starts) - 1
    ans = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if line_starts[mid] <= offset:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans + 1


def _mask_protected_spans(
    text: str, spans: Sequence[ProtectedSpan]
) -> Tuple[str, Callable[[str], str]]:
    """Replace ``spans`` in ``text`` with inert ``\\x00AWPROTECTED<idx>\\x00`` tokens."""
    if not spans:
        return text, lambda s: s

    saved: List[str] = []
    parts: List[str] = []
    cursor = 0
    for idx, sp in enumerate(spans):
        parts.append(text[cursor : sp.start])
        saved.append(sp.text)
        parts.append(f"\x00AWPROTECTED{idx}\x00")
        cursor = sp.end
    parts.append(text[cursor:])
    masked = "".join(parts)

    def _restore(s: str) -> str:
        return re.sub(r"\x00AWPROTECTED(\d+)\x00", lambda m: saved[int(m.group(1))], s)

    return masked, _restore


def _edit_order_key(edit: artifact_refs.RefEdit) -> int:
    if edit.kind == artifact_refs.FULL_NAME:
        return 0
    if edit.kind == artifact_refs.BARE_STEM:
        return 1
    if edit.kind == artifact_refs.FACETLESS_STEM:
        return 2
    return 3


def _apply_masked_edits(
    text: str,
    file_edits: Sequence[artifact_refs.RefEdit],
    spans: Sequence[ProtectedSpan],
) -> Tuple[str, int]:
    """Mask protected spans, fenced code, and permalinks; apply edits; restore; return ``(new_text, sub_count)``."""
    masked, restore_protected = _mask_protected_spans(text, spans)
    masked, restore_fenced = artifact_refs._mask_fenced_code(masked)
    masked, restore_permalinks = artifact_refs._mask_permalinks(masked)

    sub_count = 0
    for edit in sorted(file_edits, key=_edit_order_key):
        if edit.kind == artifact_refs.FULL_NAME:
            cnt = masked.count(edit.old)
            if cnt:
                masked = masked.replace(edit.old, edit.new)
                sub_count += cnt
        elif edit.kind == artifact_refs.FACETLESS_STEM:
            masked, cnt = artifact_refs._facetless_boundaried(edit.old).subn(
                edit.new, masked
            )
            sub_count += cnt
        else:
            masked, cnt = artifact_refs._boundaried(edit.old).subn(edit.new, masked)
            sub_count += cnt

    restored = restore_protected(restore_fenced(restore_permalinks(masked)))
    return restored, sub_count


def _build_citation_matchers(
    name_map: Dict[str, str],
) -> List[Tuple[str, re.Pattern[str]]]:
    """Return non-overlapping citation matchers ordered full-name -> whole -> legacy -> facetless."""
    full_pats: List[Tuple[str, re.Pattern[str]]] = []
    whole_pats: List[Tuple[str, re.Pattern[str]]] = []
    legacy_pats: List[Tuple[str, re.Pattern[str]]] = []
    facetless_pats: List[Tuple[str, re.Pattern[str]]] = []

    seen_whole: Set[str] = set()
    seen_leg: Set[str] = set()
    seen_fac: Set[str] = set()

    for old_name in sorted(name_map, key=len, reverse=True):
        full_pats.append(("full", re.compile(re.escape(old_name))))
        whole = artifact_refs._whole_stem(old_name)
        if whole != old_name and len(whole) >= 6 and whole not in seen_whole:
            seen_whole.add(whole)
            whole_pats.append(("whole", artifact_refs._boundaried(whole)))
        leg = artifact_refs._legacy_prefix_stem(old_name)
        if leg is not None and leg not in seen_leg:
            seen_leg.add(leg)
            legacy_pats.append(("legacy", artifact_refs._boundaried(leg)))
        fac = artifact_refs._facetless_stem(old_name)
        if fac is not None and fac != whole and fac not in seen_fac:
            seen_fac.add(fac)
            facetless_pats.append(
                ("facetless", artifact_refs._facetless_boundaried(fac))
            )

    return full_pats + whole_pats + legacy_pats + facetless_pats


def _scan_unchanged_in_span(
    span_text: str,
    start_line_no: int,
    file_rel: str,
    reason: str,
    matchers: Sequence[Tuple[str, re.Pattern[str]]],
) -> List[UnchangedOccurrence]:
    """Find non-overlapping citation occurrences inside one unchanged span."""
    occ: List[UnchangedOccurrence] = []
    for offset_line, line in enumerate(span_text.splitlines()):
        lineno = start_line_no + offset_line
        taken: List[Tuple[int, int]] = []
        line_hits: List[Tuple[int, str]] = []
        for _kind, pat in matchers:
            for m in pat.finditer(line):
                ms, me = m.start(), m.end()
                if _overlaps_any(ms, me, taken):
                    continue
                taken.append((ms, me))
                line_hits.append((ms, m.group(0)))
        for _pos, tok in sorted(line_hits):
            occ.append(
                UnchangedOccurrence(
                    file=file_rel,
                    line=lineno,
                    reason=reason,
                    token=tok,
                )
            )
    return occ


def _location_for_file(file_path: Path, records_dir: Path, scratch_root: Path) -> str:
    """Return location bucket: ``records/<type>`` under records_dir, else first path segment."""
    f_res = file_path.resolve()
    rec_res = records_dir.resolve()
    try:
        rel_rec = f_res.relative_to(rec_res)
        first = rel_rec.parts[0] if rel_rec.parts else ""
        return f"records/{first}" if first else "records"
    except ValueError:
        rel_root = f_res.relative_to(scratch_root.resolve())
        return rel_root.parts[0] if rel_root.parts else ""


def plan_citation_rewrites(
    scratch_root: Union[str, Path],
    rename_map: Union[RenameMap, Sequence[RenameEntry], Dict[str, str]],
) -> CitationPlan:
    """Plan m0001 citation rewrites inside ``scratch_root`` and compute the report.

    1. Refuses unless ``project_context.project_records_dir(scratch_root)``
       resolves strictly inside ``scratch_root``.
    2. Calls ``artifact_refs.plan_reference_rewrites_with_warnings`` once over
       ``M0001_SCAN_ROOTS`` and refuses on any warning, out-of-scratch edit, or
       sidecar path.
    3. Records protected spans (``## Workflow history``, review ``- Verdict:``
       lines, and ``M0001_CITATION_EXEMPTIONS``), recomputes substituted counts
       on masked text per location, and lists every unchanged occurrence with
       ``file``, ``line``, and ``reason``.
    """
    scratch_path = Path(scratch_root)
    scratch_resolved = scratch_path.resolve()
    records_dir = project_context.project_records_dir(scratch_path)
    records_resolved = records_dir.resolve()

    if not _is_within_strict(records_resolved, scratch_resolved):
        raise RenameRefusalError(
            f"Refused: project records directory {records_resolved} resolves outside "
            f"scratch root {scratch_resolved}"
        )

    name_map = _coerce_name_map(rename_map)
    if not name_map:
        return CitationPlan(
            scratch_root=scratch_path,
            name_map={},
            edits=(),
            warnings=(),
            protected_spans_by_file={},
            substituted_by_file={},
            location_counts={},
            total_substituted=0,
            unchanged_occurrences=(),
            unchanged_counts_by_reason={},
        )

    edits, warnings = artifact_refs.plan_reference_rewrites_with_warnings(
        scratch_path, name_map, scan_roots=M0001_SCAN_ROOTS
    )
    if warnings:
        raise RenameRefusalError(
            "Refused: citation planner returned ambiguity warning(s):\n"
            + "\n".join(warnings)
        )

    sidecar_resolved = record_history.history_path(scratch_path).resolve()
    edits_by_file: Dict[Path, List[artifact_refs.RefEdit]] = {}
    for edit in edits:
        f_res = edit.file.resolve()
        if not _is_within_strict(f_res, scratch_resolved):
            raise RenameRefusalError(
                f"Refused: planned citation edit {f_res} lies outside scratch root {scratch_resolved}"
            )
        if (
            f_res == sidecar_resolved
            or f_res.suffix == ".jsonl"
            or f_res.name == "history.jsonl"
        ):
            raise RenameRefusalError(
                f"Refused: sidecar file {f_res} appeared in planned citation edits"
            )
        edits_by_file.setdefault(f_res, []).append(edit)

    # Pre-filter candidate files that could hold any citation (either in edits or protected/fenced spans).
    prefixes = sorted(
        {
            artifact_naming.legacy_stem_prefix(k) or artifact_refs._whole_stem(k)
            for k in name_map
        }
    )
    prefilter_re = re.compile("|".join(re.escape(p) for p in prefixes))
    matchers = _build_citation_matchers(name_map)

    protected_spans_by_file: Dict[str, Tuple[ProtectedSpan, ...]] = {}
    substituted_by_file: Dict[str, int] = {}
    location_counts: Dict[str, int] = {}
    unchanged_occurrences: List[UnchangedOccurrence] = []
    unchanged_counts_by_reason: Dict[str, int] = {}

    scan_files = artifact_core.iter_scan_files(
        scratch_path,
        M0001_SCAN_ROOTS,
        suffixes=artifact_core._REFERENCE_TEXT_SUFFIXES,
    )
    for fpath in scan_files:
        if fpath.name in artifact_refs._GENERATED_MANIFEST_NAMES:
            continue
        f_res = fpath.resolve()
        if f_res == sidecar_resolved:
            raise RenameRefusalError(
                f"Refused: sidecar file {f_res} appeared in scan files"
            )
        try:
            text = fpath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        file_edits = edits_by_file.get(f_res, [])
        if not file_edits and not prefilter_re.search(text):
            continue

        rel_posix = _rel_posix(f_res, scratch_resolved)
        is_review = _is_review_file(f_res, records_resolved)
        file_exemptions = m0001_discover.discover_citation_exemptions(
            text, rel_posix, name_map
        )

        spans = _find_protected_spans(
            text,
            rel_posix,
            is_review=is_review,
            exemptions=file_exemptions,
        )
        if spans:
            protected_spans_by_file[rel_posix] = tuple(spans)

        # Record unchanged occurrences in protected spans
        for sp in spans:
            occ_list = _scan_unchanged_in_span(
                sp.text, sp.line_no, rel_posix, sp.reason, matchers
            )
            unchanged_occurrences.extend(occ_list)
            if occ_list:
                unchanged_counts_by_reason[sp.reason] = unchanged_counts_by_reason.get(
                    sp.reason, 0
                ) + len(occ_list)

        # Record unchanged occurrences in fenced code blocks and pinned permalinks
        # outside already-protected spans (track original line numbers on unmasked text).
        orig_lines = _line_offsets(text)
        prot_intervals = [(sp.start, sp.end) for sp in spans]
        fenced_ranges = _find_fenced_ranges(orig_lines)
        fenced_intervals = [(a, b) for a, b, _ in fenced_ranges]

        for f_start, f_end, f_line in fenced_ranges:
            if _overlaps_any(f_start, f_end, prot_intervals):
                continue
            occ_list = _scan_unchanged_in_span(
                text[f_start:f_end],
                f_line,
                rel_posix,
                "fenced-or-permalink",
                matchers,
            )
            unchanged_occurrences.extend(occ_list)
            if occ_list:
                unchanged_counts_by_reason["fenced-or-permalink"] = (
                    unchanged_counts_by_reason.get("fenced-or-permalink", 0)
                    + len(occ_list)
                )

        orig_line_starts = [s for s, _, _ in orig_lines]
        for pm in artifact_refs._PINNED_PERMALINK_RE.finditer(text):
            ps, pe = pm.start(), pm.end()
            if _overlaps_any(ps, pe, prot_intervals) or _overlaps_any(
                ps, pe, fenced_intervals
            ):
                continue
            p_line = _line_number_at(orig_line_starts, ps)
            occ_list = _scan_unchanged_in_span(
                pm.group(0),
                p_line,
                rel_posix,
                "fenced-or-permalink",
                matchers,
            )
            unchanged_occurrences.extend(occ_list)
            if occ_list:
                unchanged_counts_by_reason["fenced-or-permalink"] = (
                    unchanged_counts_by_reason.get("fenced-or-permalink", 0)
                    + len(occ_list)
                )

        # Compute exact substituted count on masked text for files with RefEdits
        if file_edits:
            _new_text, sub_cnt = _apply_masked_edits(text, file_edits, spans)
            substituted_by_file[rel_posix] = sub_cnt
            if sub_cnt > 0:
                loc = _location_for_file(f_res, records_resolved, scratch_resolved)
                location_counts[loc] = location_counts.get(loc, 0) + sub_cnt

    total_substituted = sum(substituted_by_file.values())
    return CitationPlan(
        scratch_root=scratch_path,
        name_map=name_map,
        edits=tuple(edits),
        warnings=tuple(warnings),
        protected_spans_by_file=protected_spans_by_file,
        substituted_by_file=substituted_by_file,
        location_counts=location_counts,
        total_substituted=total_substituted,
        unchanged_occurrences=tuple(unchanged_occurrences),
        unchanged_counts_by_reason=unchanged_counts_by_reason,
    )


# --------------------------------------------------------------------------------------
# Step-3 apply on scratch copy (E-04)
# --------------------------------------------------------------------------------------


def _load_step3_journal(
    journal: Optional[Union[Dict[str, Any], str, Path]],
) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
    """Load or initialize ``step3_progress`` inside ``journal``."""
    if journal is None:
        return None, None
    if isinstance(journal, dict):
        prog = journal.setdefault("step3_progress", {})
        prog.setdefault("rewritten_files", [])
        prog.setdefault("moved_files", [])
        return None, journal
    p = Path(journal)
    jpath = p / "journal.json" if p.is_dir() else p
    if jpath.is_file():
        data = json.loads(jpath.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RenameRefusalError(
                f"Refused: journal at {jpath} must contain a JSON object"
            )
    else:
        data = {}
    prog = data.setdefault("step3_progress", {})
    prog.setdefault("rewritten_files", [])
    prog.setdefault("moved_files", [])
    return jpath, data


def _verify_protected_spans_preserved(
    orig_text: str,
    new_text: str,
    spans: Sequence[ProtectedSpan],
    rel_posix: str,
    *,
    is_review: bool,
    exemptions: Sequence[str],
) -> None:
    """Assert that every protected span from ``orig_text`` is byte-identical in ``new_text``."""
    if not spans:
        return
    new_spans = _find_protected_spans(
        new_text,
        rel_posix,
        is_review=is_review,
        exemptions=exemptions,
    )
    orig_by_reason = [(sp.reason, sp.text.encode("utf-8")) for sp in spans]
    new_by_reason = [(sp.reason, sp.text.encode("utf-8")) for sp in new_spans]
    if orig_by_reason != new_by_reason:
        raise RenameRefusalError(
            f"Refused: protected span bytes changed in {rel_posix} after citation rewrite"
        )


def apply_step3(
    scratch_root: Union[str, Path],
    rename_map: Union[RenameMap, Sequence[RenameEntry]],
    citation_plan: CitationPlan,
    journal: Optional[Union[Dict[str, Any], str, Path]] = None,
    *,
    save_callback: Optional[Callable[[], None]] = None,
) -> Dict[str, Any]:
    """Apply step-3 citation rewrites and file moves inside ``scratch_root``.

    Order:
    1. For each file of ``citation_plan``, mask protected spans before fenced
       code and permalinks, substitute ``RefEdit``s in ``apply_reference_rewrites``
       order, restore tokens, assert byte-identical protected spans before and
       after writing via ``artifact_core.atomic_write``, and record per-file
       progress in ``journal``.
    2. Move each mapped file to its new name in the same directory of the
       scratch copy via ``Path.rename`` (skipping entries already moved,
       refusing when both paths exist), recording per-file progress.
    """
    scratch_path = Path(scratch_root)
    scratch_resolved = scratch_path.resolve()
    records_dir = project_context.project_records_dir(scratch_path)
    records_resolved = records_dir.resolve()

    if not _is_within_strict(records_resolved, scratch_resolved):
        raise RenameRefusalError(
            f"Refused: project records directory {records_resolved} resolves outside "
            f"scratch root {scratch_resolved}"
        )

    jpath, jdata = _load_step3_journal(journal)
    entries = _coerce_entries(rename_map)

    def _persist() -> None:
        _save_journal_data(jpath, jdata)
        if save_callback is not None:
            save_callback()

    done_rewrites: Set[str] = (
        set((jdata.get("step3_progress") or {}).get("rewritten_files") or [])
        if jdata is not None
        else set()
    )
    done_moves: Set[str] = (
        set((jdata.get("step3_progress") or {}).get("moved_files") or [])
        if jdata is not None
        else set()
    )

    # Map old_rel -> new_rel so an idempotent second call on an already-moved scratch copy
    # resolves moved pre-move paths to their post-move paths and leaves them unchanged.
    old_to_new_path: Dict[Path, Path] = {}
    for entry in entries:
        old_to_new_path[(records_resolved / entry.old_rel).resolve()] = (
            records_resolved / entry.new_rel
        )

    edits_by_file: Dict[Path, List[artifact_refs.RefEdit]] = {}
    for edit in citation_plan.edits:
        f_res = edit.file.resolve()
        if not _is_within_strict(f_res, scratch_resolved):
            raise RenameRefusalError(
                f"Refused: edit target {f_res} lies outside scratch root {scratch_resolved}"
            )
        edits_by_file.setdefault(f_res, []).append(edit)

    rewritten_now: List[str] = []
    for f_res, file_edits in sorted(edits_by_file.items(), key=lambda kv: str(kv[0])):
        target_path = f_res
        if not target_path.exists() and f_res in old_to_new_path:
            moved_candidate = old_to_new_path[f_res]
            if moved_candidate.exists():
                target_path = moved_candidate
        rel_posix = _rel_posix(target_path, scratch_resolved)
        orig_rel_posix = _rel_posix(f_res, scratch_resolved)

        if orig_rel_posix in done_rewrites or rel_posix in done_rewrites:
            continue

        orig_text = target_path.read_text(encoding="utf-8")
        is_review = _is_review_file(target_path, records_resolved)
        file_exemptions = m0001_discover.discover_citation_exemptions(
            orig_text, orig_rel_posix, citation_plan.name_map
        )
        spans = _find_protected_spans(
            orig_text,
            orig_rel_posix,
            is_review=is_review,
            exemptions=file_exemptions,
        )

        new_text, _sub_cnt = _apply_masked_edits(orig_text, file_edits, spans)
        _verify_protected_spans_preserved(
            orig_text,
            new_text,
            spans,
            orig_rel_posix,
            is_review=is_review,
            exemptions=file_exemptions,
        )

        if new_text != orig_text:
            artifact_core.atomic_write(target_path, new_text)
            written_text = target_path.read_text(encoding="utf-8")
            _verify_protected_spans_preserved(
                orig_text,
                written_text,
                spans,
                orig_rel_posix,
                is_review=is_review,
                exemptions=file_exemptions,
            )
            rewritten_now.append(orig_rel_posix)

        if jdata is not None:
            jdata["step3_progress"]["rewritten_files"].append(orig_rel_posix)
            done_rewrites.add(orig_rel_posix)
            _persist()

    moved_now: List[Tuple[str, str]] = []
    for entry in entries:
        if entry.old_rel in done_moves:
            continue
        old_path = records_resolved / entry.old_rel
        new_path = records_resolved / entry.new_rel
        old_exists = old_path.exists()
        new_exists = new_path.exists()

        if old_exists and new_exists:
            raise RenameRefusalError(
                f"Refused: both source {old_path} and target {new_path} exist in scratch copy"
            )
        if not old_exists and new_exists:
            if jdata is not None:
                jdata["step3_progress"]["moved_files"].append(entry.old_rel)
                done_moves.add(entry.old_rel)
                _persist()
            continue
        if not old_exists and not new_exists:
            raise RenameRefusalError(
                f"Refused: neither source {old_path} nor target {new_path} exists in scratch copy"
            )

        new_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)
        moved_now.append((entry.old_rel, entry.new_rel))
        if jdata is not None:
            jdata["step3_progress"]["moved_files"].append(entry.old_rel)
            done_moves.add(entry.old_rel)
            _persist()

    return {
        "rewritten_files": rewritten_now,
        "moved_files": moved_now,
        "total_substituted": citation_plan.total_substituted,
        "location_counts": dict(citation_plan.location_counts),
        "unchanged_counts_by_reason": dict(citation_plan.unchanged_counts_by_reason),
    }
