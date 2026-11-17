"""Repository-agnostic discovery and classification for migration m0001.

Implements spec 4sd62s Section 5.2a items 1, 4, and 5:
- ``discover(repo) -> Inventory`` inspects the resolved records tree (and any
  legacy ``.agents/`` tree), returning every candidate record with its source
  tree, record type, identity (present or to mint), status, status source
  (bullet, YAML, comment, or disposition directory), and title; every
  unclassifiable file with a human-readable reason; excluded non-records;
  whether a history sidecar is expected (a spec or backlog record's own
  ``## Workflow history`` shows a sidecar-writing setter ran) and present; and
  whether a legacy layout stage is needed.
- Provides shared filename classification, template exclusion, and dynamic
  citation-exemption discovery so no ``m0001_*`` module embeds repository
  constants, id6 literals, record filenames, or corpus counts.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import os
from pathlib import Path
import re
import subprocess
from typing import Dict, List, Mapping, Optional, Set, Tuple, Union

from agent_workflows import (
    artifact_core,
    artifact_meta,
    artifact_naming,
    attention_contract,
    project_context,
    record_history,
    research_contract,
)

TREE_DIR_TO_TYPE: Dict[str, str] = {
    "plans": "ipd",
    "backlog": "backlog",
    "releases": "release",
    "specs": "spec",
    "prompts": "prompt",
    "research": "research",
    "walkthroughs": "walkthrough",
    "roadmaps": "roadmap",
}

STATUSLESS_TYPES: frozenset[str] = frozenset({"walkthrough", "roadmap", "review"})

EXCLUDED_DIRNAMES: frozenset[str] = frozenset(
    {"comms", "prompt-library", "untracked", "runs", "meta", "reviews"}
)

AGENTS_NON_RECORD_TOP_DIRS: frozenset[str] = frozenset(
    {"workflows", "inbox", "runs", "state"}
)
AGENTS_NON_RECORD_TOP_FILES: frozenset[str] = frozenset({"AGENTS.md"})

_PROMPT_COMMENT_RE = re.compile(
    r"\A<!--\s*(?:aw-prompt|aw-managed-prompt):\s*(.*?)\s*-->", re.DOTALL
)
_H1_RE = re.compile(r"^#\s+(.+?)\s*$")
_HYPHEN_DATE_PREFIX_RE = re.compile(
    r"\A(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})-(?P<rest>.+?)(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)
_LEGACY_TRAILING_ID_ACTOR_RE = re.compile(r"\(([^()]+)\)\s*:")


@dataclass(frozen=True)
class DiscoveredRecord:
    """One candidate record discovered by ``discover``."""

    path: Path
    rel_path: str
    repo_rel_path: str
    source_tree: str
    record_type: str
    identity: Optional[str]
    identity_source: str
    needs_mint: bool
    legacy_name: bool
    needs_rename: bool
    status: Optional[str]
    status_source: Optional[str]
    title: Optional[str]
    set_id: Optional[str]
    order_nn: Optional[int]
    filename_date: Optional[str]


@dataclass(frozen=True)
class UnclassifiedFile:
    """One non-record or unclassifiable markdown file encountered during discovery."""

    path: Path
    rel_path: str
    repo_rel_path: str
    source_tree: str
    category: str
    reason: str


@dataclass(frozen=True)
class Inventory:
    """Full repository discovery inventory for migration m0001."""

    repo_root: Path
    records_root: Path
    records: Tuple[DiscoveredRecord, ...]
    reviews: Tuple[DiscoveredRecord, ...]
    unclassifiable: Tuple[UnclassifiedFile, ...]
    excluded: Tuple[UnclassifiedFile, ...]
    sidecar_path: Path
    sidecar_present: bool
    sidecar_expected: bool
    sidecar_expected_reason: str
    layout_stage_needed: bool
    layout_stage_reason: str

    @property
    def legacy_tree(self) -> bool:
        """Alias for ``layout_stage_needed``."""
        return self.layout_stage_needed

    @property
    def legacy_name_records(self) -> Tuple[DiscoveredRecord, ...]:
        """Records whose filename matches the legacy timestamp grammar."""
        return tuple(r for r in self.records if r.legacy_name)

    @property
    def mint_records(self) -> Tuple[DiscoveredRecord, ...]:
        """Records lacking an identity that require a minted id6."""
        return tuple(r for r in self.records if r.needs_mint)

    @property
    def rename_candidates(self) -> Tuple[DiscoveredRecord, ...]:
        """Records requiring a rename to clustered form (legacy names or id-less)."""
        return tuple(r for r in self.records if r.needs_rename)

    def format_summary(self) -> str:
        """Return a concise human-readable inventory summary."""
        legacy_renames = len(self.legacy_name_records)
        legacy_mints = sum(1 for r in self.legacy_name_records if r.needs_mint)
        total_mints = len(self.mint_records)
        lines = [
            f"Inventory: {len(self.records)} records, {len(self.reviews)} reviews, "
            f"{len(self.unclassifiable)} unclassifiable, {len(self.excluded)} excluded",
            f"  Legacy-name renames: {legacy_renames} (mints={legacy_mints}, total_mints={total_mints})",
            f"  Sidecar: present={self.sidecar_present}, expected={self.sidecar_expected} ({self.sidecar_expected_reason})",
            f"  Layout stage needed: {self.layout_stage_needed} ({self.layout_stage_reason})",
        ]
        return "\n".join(lines)


def classify_name(name: str) -> str:
    """Classify ``name`` as ``'legacy'``, ``'clustered'``, or ``'other'``.

    Tests ``artifact_naming._LEGACY_TIMESTAMP_RE`` before
    ``artifact_naming.parse_clustered`` so legacy names whose slug starts with
    a 6-letter word classify as ``'legacy'``, while clustered names with a
    4-digit Set id and a real digit-bearing ``id6`` or non-HHMM Set id still
    classify as ``'clustered'``.
    """
    m_leg = artifact_naming._LEGACY_TIMESTAMP_RE.match(name)
    if m_leg:
        m_clu = artifact_naming.parse_clustered(name)
        if m_clu is not None:
            hhmm = m_leg.group("hhmm")
            hh = int(hhmm[:2])
            mm = int(hhmm[2:])
            valid_hhmm = 0 <= hh <= 23 and 0 <= mm <= 59
            id6_cand = m_clu.group("id6")
            has_digit = any(ch.isdigit() for ch in id6_cand)
            if not valid_hhmm or has_digit:
                return "clustered"
        return "legacy"

    if artifact_naming.parse_clustered(name) is not None:
        return "clustered"
    return "other"


def is_non_record_filename(filename: str) -> bool:
    """Return True for non-record manifest filenames (README, INDEX, STATUS)."""
    return filename in (
        "README.md",
        "STATUS.md",
        "INDEX.md",
        "INDEX.json",
    ) or filename.startswith("INDEX.")


def _agents_skills_top_dir() -> str:
    """Return the top-level directory under ``.agents/`` used for installed skills."""
    from agent_workflows import engine as _engine

    skills_posix = _engine.SKILLS_DIR.replace("\\", "/").strip("/")
    if skills_posix == ".agents" or skills_posix.startswith(".agents/"):
        rest = skills_posix.removeprefix(".agents").strip("/")
        if rest:
            return rest.split("/", 1)[0]
    return "skills"


def _parse_prompt_comment_fields(text: str) -> Dict[str, str]:
    """Extract key/value pairs from a leading ``<!-- aw-prompt: ... -->`` comment."""
    stripped = text.lstrip("\ufeff").lstrip()
    m_prompt = _PROMPT_COMMENT_RE.match(stripped)
    if not m_prompt:
        return {}
    inner = m_prompt.group(1)
    if " . " in inner:
        inner = inner.split(" . ", 1)[0]
    out: Dict[str, str] = {}
    for item in inner.split("|"):
        if ":" in item:
            k, v = item.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _extract_fields_with_source(
    text: str, record_type: str
) -> Tuple[Dict[str, str], str]:
    """Return ``(raw_fields, source_kind)`` from YAML, prompt comment, or bullet block."""
    if text.startswith("---"):
        yaml_probe, _ = artifact_meta._parse_yaml_front_matter(text)
        after_fence = text.split("\n", 1)[1][:200] if "\n" in text else ""
        if yaml_probe and not artifact_meta._BULLET_RE.search(after_fence):
            return dict(yaml_probe), "yaml"

    if record_type == "prompt" and text.lstrip("\ufeff").lstrip().startswith("<!--"):
        prompt_fields = _parse_prompt_comment_fields(text)
        if prompt_fields:
            return prompt_fields, "comment"

    bullets, _, _ = artifact_meta._parse_bullet_metadata(text)
    return bullets, "bullet"


def _extract_first_h1(text: str) -> Optional[str]:
    """Return the first Markdown H1 heading text from ``text``, or None."""
    work = text
    if work.startswith("---"):
        work = artifact_meta._strip_leading_yaml_mirror(work)
    for line in work.splitlines():
        m = _H1_RE.match(line.strip())
        if m:
            title = m.group(1).strip()
            if title:
                return title
    return None


def _filename_identity_parts(
    filename: str,
) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[str]]:
    """Return ``(id6, set_id, order_nn, filename_date)`` from non-legacy filename."""
    if classify_name(filename) == "legacy":
        m_leg = artifact_naming._LEGACY_TIMESTAMP_RE.match(filename)
        if m_leg:
            try:
                nn_val: Optional[int] = int(m_leg.group("nn"))
            except ValueError:
                nn_val = None
            return None, None, nn_val, m_leg.group("date")
        return None, None, None, None

    m_attr = artifact_naming.parse_attributed(filename)
    if m_attr and artifact_core.is_valid_id6(m_attr.id6):
        try:
            nn_val = int(m_attr.nn)
        except ValueError:
            nn_val = None
        return m_attr.id6, m_attr.set, nn_val, m_attr.date

    m_clust = artifact_naming.parse_clustered(filename)
    if m_clust and artifact_core.is_valid_id6(m_clust.group("id6")):
        try:
            nn_val = int(m_clust.group("nn"))
        except ValueError:
            nn_val = None
        return m_clust.group("id6"), m_clust.group("set"), nn_val, m_clust.group("date")

    m_pref = artifact_naming.parse_clustered_prefix(filename)
    if m_pref and artifact_core.is_valid_id6(m_pref.group("id6")):
        try:
            nn_val = int(m_pref.group("nn"))
        except ValueError:
            nn_val = None
        return m_pref.group("id6"), m_pref.group("set"), nn_val, m_pref.group("date")

    m_dsf = artifact_naming._DATED_SLUG_FACET_RE.match(filename)
    if m_dsf:
        return None, None, None, m_dsf.group("date")

    m_hdate = _HYPHEN_DATE_PREFIX_RE.match(filename)
    if m_hdate:
        return (
            None,
            None,
            None,
            f"{m_hdate.group('y')}{m_hdate.group('m')}{m_hdate.group('d')}",
        )

    return None, None, None, None


def is_excluded_template(
    rel_posix: str,
    filename: str,
    text: Optional[str] = None,
) -> bool:
    """Return True iff ``rel_posix``/``filename`` is an excluded non-record template."""
    parts = Path(rel_posix).parts
    if "prompt-library" in parts:
        return True
    if not filename.lower().endswith("-template.md"):
        return False
    if text is None:
        return True

    fn_id, _, _, _ = _filename_identity_parts(filename)
    if fn_id is not None:
        return False
    if text.lstrip("\ufeff").lstrip().startswith("<!--"):
        if _parse_prompt_comment_fields(text):
            return False
    if text.startswith("---"):
        parsed_fm = research_contract.parse_frontmatter(text)
        if parsed_fm and (parsed_fm.get("id") or parsed_fm.get("status")):
            return False
    bullets, _, _ = artifact_meta._parse_bullet_metadata(text)
    if (
        bullets.get("Id")
        or bullets.get("id")
        or bullets.get("Status")
        or bullets.get("status")
    ):
        return False
    return True


def _is_sidecar_setter_actor(actor: str) -> bool:
    """Return True if ``actor`` names a sidecar-writing setter tool."""
    norm = actor.strip().lower()
    if norm == "aw set" or norm.startswith("aw set "):
        return True
    if norm == "aw specs" or norm.startswith("aw specs "):
        return True
    if norm == "aw backlog" or norm.startswith("aw backlog "):
        return True
    return False


def _has_sidecar_setter_history(text: str) -> Optional[str]:
    """Return matching setter actor if ``text``'s history shows a sidecar-writing setter ran."""
    hb = attention_contract.history_block(text)
    for line in hb.record_lines:
        m_fb = _LEGACY_TRAILING_ID_ACTOR_RE.search(line)
        if m_fb and _is_sidecar_setter_actor(m_fb.group(1)):
            return m_fb.group(1)
    return None


def _parse_terse_set(raw_set: Optional[str]) -> Optional[str]:
    """Extract terse Set id from ``<terse> (<desc>)``."""
    if not raw_set:
        return None
    before_paren = str(raw_set).split("(", 1)[0].strip()
    if not before_paren:
        return None
    return before_paren.split()[0]


def _detect_source_tree(
    repo_path: Path, records_root: Path, tree_root: Path, *, is_agents: bool
) -> str:
    """Return logical source tree label for files scanned under ``tree_root``."""
    if is_agents:
        return ".agents"
    try:
        if tree_root.resolve() == (repo_path / ".aw" / "records").resolve():
            return ".aw/records"
    except OSError:
        pass
    try:
        ctx = project_context.resolve_project_context(target_repo=str(repo_path))
        backend = str(ctx.records_backend or "").strip()
        if backend in ("companion", "home"):
            return backend
    except Exception:
        pass
    return "records"


def _repo_rel(path: Path, repo_path: Path, fallback_rel: str) -> str:
    """Return ``path`` relative to ``repo_path`` when inside it, else ``fallback_rel``."""
    try:
        return path.resolve().relative_to(repo_path.resolve()).as_posix()
    except (OSError, ValueError):
        return fallback_rel


def _effective_tree_and_disposition(
    rel_parts: Tuple[str, ...], *, is_agents: bool
) -> Tuple[Optional[str], Optional[str], str]:
    """Return ``(record_type, disposition_dir, top_dir)`` for a candidate relative path."""
    if not rel_parts or len(rel_parts) == 1:
        return None, None, ""
    top = rel_parts[0]
    if is_agents and top == "docs" and len(rel_parts) >= 3:
        sub = rel_parts[1]
        rtype = TREE_DIR_TO_TYPE.get(sub)
        disp = rel_parts[2] if len(rel_parts) >= 4 else None
        return rtype, disp, f"docs/{sub}"
    if top == "reviews":
        return "review", None, "reviews"
    rtype = TREE_DIR_TO_TYPE.get(top)
    if rtype is None:
        return None, None, top
    disp = rel_parts[1] if len(rel_parts) >= 3 else None
    return rtype, disp, top


def _compute_layout_stage_needed(
    repo_path: Path, records_root: Path
) -> Tuple[bool, str]:
    """Return ``(layout_stage_needed, reason)`` based on ``.agents/`` contents."""
    agents_dir = repo_path / ".agents"
    if not agents_dir.is_dir():
        return False, "already on .aw/"
    try:
        if agents_dir.resolve() == records_root.resolve():
            return False, "records_root points directly to .agents/"
    except OSError:
        pass

    skills_top = _agents_skills_top_dir()
    non_skill_entries = [
        p.name
        for p in sorted(agents_dir.iterdir())
        if p.name != skills_top and not p.name.startswith(".")
    ]
    if non_skill_entries:
        return (
            True,
            f"legacy .agents/ entries present ({', '.join(non_skill_entries[:5])})",
        )
    return False, "only preserved .agents/skills/ present"


def infer_record_date(path: Path, repo_root: Optional[Path] = None) -> str:
    """Return ``YYYYMMDD`` date for a dateless record via git history or file mtime."""
    if repo_root is not None:
        try:
            proc = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "log",
                    "-n",
                    "1",
                    "--diff-filter=A",
                    "--follow",
                    "--format=%ad",
                    "--date=format:%Y%m%d",
                    "--",
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            val = proc.stdout.strip()
            if proc.returncode == 0 and len(val) == 8 and val.isdigit():
                return val
        except OSError:
            pass
    try:
        ts = path.stat().st_mtime
        return datetime.datetime.fromtimestamp(ts).strftime("%Y%m%d")
    except OSError:
        return datetime.datetime.now().strftime("%Y%m%d")


def discover(
    repo: Union[str, Path],
    *,
    records_root: Optional[Union[str, Path]] = None,
) -> Inventory:
    """Discover candidate records, unclassifiable files, sidecar expectation, and layout stage need."""
    repo_path = Path(repo)
    eff_records_root = (
        Path(records_root)
        if records_root is not None
        else project_context.project_records_dir(repo_path)
    )

    scan_roots: List[Tuple[Path, bool]] = []
    seen_roots: Set[Path] = set()
    if eff_records_root.is_dir():
        res_rec = eff_records_root.resolve()
        seen_roots.add(res_rec)
        scan_roots.append((eff_records_root, False))

    if records_root is None:
        agents_dir = repo_path / ".agents"
        if agents_dir.is_dir():
            res_ag = agents_dir.resolve()
            if res_ag not in seen_roots:
                seen_roots.add(res_ag)
                scan_roots.append((agents_dir, True))

    skills_top = _agents_skills_top_dir()
    records_out: List[DiscoveredRecord] = []
    reviews_out: List[DiscoveredRecord] = []
    unclassifiable_out: List[UnclassifiedFile] = []
    excluded_out: List[UnclassifiedFile] = []
    seen_files: Set[Path] = set()

    sidecar_expected = False
    sidecar_expected_reason = (
        "no spec or backlog history names a sidecar-writing setter"
    )

    for tree_root, is_agents in scan_roots:
        source_tree = _detect_source_tree(
            repo_path, eff_records_root, tree_root, is_agents=is_agents
        )
        for cur_dir, dirs, files in os.walk(tree_root):
            cur_path = Path(cur_dir)
            rel_dir = cur_path.relative_to(tree_root)
            rel_dir_parts = rel_dir.parts if rel_dir != Path(".") else ()

            kept_dirs: List[str] = []
            excluded_subdirs: List[Tuple[str, str, str]] = []
            for dname in sorted(dirs):
                if dname.endswith(".data"):
                    excluded_subdirs.append(
                        (dname, "excluded-data", "excluded .data/ companion directory")
                    )
                    continue
                if dname in ("comms", "untracked", "runs", "meta"):
                    cat = "excluded-comms" if dname == "comms" else "excluded-runtime"
                    excluded_subdirs.append(
                        (dname, cat, f"excluded '{dname}/' directory")
                    )
                    continue
                if dname == "prompt-library":
                    excluded_subdirs.append(
                        (
                            dname,
                            "excluded-template",
                            "excluded prompt-library template directory",
                        )
                    )
                    continue
                if (
                    is_agents
                    and not rel_dir_parts
                    and (dname == skills_top or dname in AGENTS_NON_RECORD_TOP_DIRS)
                ):
                    excluded_subdirs.append(
                        (
                            dname,
                            "excluded-non-record",
                            f"non-record '.agents/{dname}/' directory",
                        )
                    )
                    continue
                kept_dirs.append(dname)

            # Record files inside excluded subtrees without treating them as records.
            for dname, ex_cat, ex_reason in excluded_subdirs:
                sub_path = cur_path / dname
                for ex_cur, _ex_dirs, ex_files in os.walk(sub_path):
                    ex_cur_p = Path(ex_cur)
                    for fname in sorted(ex_files):
                        if not fname.endswith(".md"):
                            continue
                        fpath = ex_cur_p / fname
                        f_res = fpath.resolve()
                        if f_res in seen_files:
                            continue
                        seen_files.add(f_res)
                        rel_p = fpath.relative_to(tree_root).as_posix()
                        eff_cat = (
                            "excluded-manifest"
                            if is_non_record_filename(fname)
                            else ex_cat
                        )
                        eff_reason = (
                            "excluded README/INDEX/STATUS manifest"
                            if is_non_record_filename(fname)
                            else ex_reason
                        )
                        excluded_out.append(
                            UnclassifiedFile(
                                path=fpath,
                                rel_path=rel_p,
                                repo_rel_path=_repo_rel(fpath, repo_path, rel_p),
                                source_tree=source_tree,
                                category=eff_cat,
                                reason=eff_reason,
                            )
                        )

            dirs[:] = kept_dirs

            for fname in sorted(files):
                if not fname.endswith(".md"):
                    continue
                fpath = cur_path / fname
                f_res = fpath.resolve()
                if f_res in seen_files:
                    continue
                seen_files.add(f_res)

                rel_p = fpath.relative_to(tree_root).as_posix()
                repo_rel_p = _repo_rel(fpath, repo_path, rel_p)
                rel_parts = Path(rel_p).parts

                if (
                    is_agents
                    and len(rel_parts) == 1
                    and fname in AGENTS_NON_RECORD_TOP_FILES
                ):
                    excluded_out.append(
                        UnclassifiedFile(
                            path=fpath,
                            rel_path=rel_p,
                            repo_rel_path=repo_rel_p,
                            source_tree=source_tree,
                            category="excluded-non-record",
                            reason="non-record agent pointer file",
                        )
                    )
                    continue

                if is_non_record_filename(fname):
                    excluded_out.append(
                        UnclassifiedFile(
                            path=fpath,
                            rel_path=rel_p,
                            repo_rel_path=repo_rel_p,
                            source_tree=source_tree,
                            category="excluded-manifest",
                            reason="excluded README/INDEX/STATUS manifest",
                        )
                    )
                    continue

                rtype, disp_dir, top_label = _effective_tree_and_disposition(
                    rel_parts, is_agents=is_agents
                )

                if rtype == "review":
                    if not fname.endswith(".review.md"):
                        unclassifiable_out.append(
                            UnclassifiedFile(
                                path=fpath,
                                rel_path=rel_p,
                                repo_rel_path=repo_rel_p,
                                source_tree=source_tree,
                                category="unclassifiable",
                                reason="file under reviews/ does not end with '.review.md'",
                            )
                        )
                        continue
                    fn_id, fn_set, fn_nn, fn_date = _filename_identity_parts(fname)
                    reviews_out.append(
                        DiscoveredRecord(
                            path=fpath,
                            rel_path=rel_p,
                            repo_rel_path=repo_rel_p,
                            source_tree=source_tree,
                            record_type="review",
                            identity=fn_id,
                            identity_source="filename" if fn_id else "subject",
                            needs_mint=False,
                            legacy_name=classify_name(fname) == "legacy",
                            needs_rename=False,
                            status=None,
                            status_source=None,
                            title=None,
                            set_id=fn_set,
                            order_nn=fn_nn,
                            filename_date=fn_date,
                        )
                    )
                    continue

                if rtype is None:
                    if is_excluded_template(rel_p, fname):
                        excluded_out.append(
                            UnclassifiedFile(
                                path=fpath,
                                rel_path=rel_p,
                                repo_rel_path=repo_rel_p,
                                source_tree=source_tree,
                                category="excluded-template",
                                reason="excluded template file",
                            )
                        )
                        continue
                    reason = (
                        f"unrecognized directory '{top_label}/' and no record type facet or metadata marker"
                        if top_label
                        else "top-level markdown file outside any recognized record tree"
                    )
                    unclassifiable_out.append(
                        UnclassifiedFile(
                            path=fpath,
                            rel_path=rel_p,
                            repo_rel_path=repo_rel_p,
                            source_tree=source_tree,
                            category="unclassifiable",
                            reason=reason,
                        )
                    )
                    continue

                text = fpath.read_text(encoding="utf-8", errors="replace")
                if is_excluded_template(rel_p, fname, text):
                    excluded_out.append(
                        UnclassifiedFile(
                            path=fpath,
                            rel_path=rel_p,
                            repo_rel_path=repo_rel_p,
                            source_tree=source_tree,
                            category="excluded-template",
                            reason="excluded OQ-02 template file",
                        )
                    )
                    continue

                raw_fields, field_source = _extract_fields_with_source(text, rtype)
                fn_id, fn_set, fn_nn, fn_date = _filename_identity_parts(fname)
                raw_id = raw_fields.get("Id") or raw_fields.get("id")
                infile_id = (
                    str(raw_id).strip()
                    if isinstance(raw_id, str)
                    and artifact_core.is_valid_id6(str(raw_id).strip())
                    else None
                )

                is_legacy_name = classify_name(fname) == "legacy"
                if is_legacy_name:
                    identity = infile_id
                    id_source = field_source if infile_id else "to-mint"
                else:
                    identity = fn_id or infile_id
                    if fn_id:
                        id_source = "filename"
                    elif infile_id:
                        id_source = field_source
                    else:
                        id_source = "to-mint"

                needs_mint = identity is None
                needs_rename = is_legacy_name or needs_mint

                status: Optional[str] = None
                status_source: Optional[str] = None
                if rtype not in STATUSLESS_TYPES:
                    raw_status = raw_fields.get("Status") or raw_fields.get("status")
                    if isinstance(raw_status, str) and raw_status.strip():
                        toks = raw_status.strip().split()
                        if toks:
                            status = toks[0].lower()
                            status_source = field_source
                    if status is None and rtype != "research" and disp_dir:
                        status = disp_dir.lower()
                        status_source = "disposition"

                title = _extract_first_h1(text)
                if title is None and field_source == "yaml":
                    raw_title = raw_fields.get("title")
                    if isinstance(raw_title, str) and raw_title.strip():
                        title = raw_title.strip()

                terse_set = _parse_terse_set(
                    raw_fields.get("Set") or raw_fields.get("set")
                )
                set_id = terse_set or fn_set

                order_nn = fn_nn
                raw_order = raw_fields.get("Order") or raw_fields.get("order")
                if raw_order is not None and str(raw_order).strip():
                    try:
                        order_nn = int(str(raw_order).strip())
                    except ValueError:
                        pass

                if not sidecar_expected and rtype in ("spec", "backlog"):
                    setter_actor = _has_sidecar_setter_history(text)
                    if setter_actor:
                        sidecar_expected = True
                        sidecar_expected_reason = f"setter '{setter_actor}' in {rel_p}"

                records_out.append(
                    DiscoveredRecord(
                        path=fpath,
                        rel_path=rel_p,
                        repo_rel_path=repo_rel_p,
                        source_tree=source_tree,
                        record_type=rtype,
                        identity=identity,
                        identity_source=id_source,
                        needs_mint=needs_mint,
                        legacy_name=is_legacy_name,
                        needs_rename=needs_rename,
                        status=status,
                        status_source=status_source,
                        title=title,
                        set_id=set_id,
                        order_nn=order_nn,
                        filename_date=fn_date,
                    )
                )

    sidecar_path = record_history.history_path(repo_path)
    sidecar_present = sidecar_path.is_file()
    layout_needed, layout_reason = _compute_layout_stage_needed(
        repo_path, eff_records_root
    )

    return Inventory(
        repo_root=repo_path,
        records_root=eff_records_root,
        records=tuple(records_out),
        reviews=tuple(reviews_out),
        unclassifiable=tuple(unclassifiable_out),
        excluded=tuple(excluded_out),
        sidecar_path=sidecar_path,
        sidecar_present=sidecar_present,
        sidecar_expected=sidecar_expected,
        sidecar_expected_reason=sidecar_expected_reason,
        layout_stage_needed=layout_needed,
        layout_stage_reason=layout_reason,
    )


def discover_citation_exemptions(
    text: str,
    rel_posix: str,
    name_map: Mapping[str, str],
) -> List[str]:
    """Discover legacy filenames that are deliberate examples/fixtures in ``text``.

    Replaces hardcoded repository exemption pairs:
    1. Misparse/old-grammar examples in Python files: lines discussing
       ``parse_clustered``, ``misparse``, or ``id6=`` for a legacy filename that
       ``artifact_naming.parse_clustered`` also matches.
    2. Legacy-name fixture literals in ``tests/*rename*.py`` outside ``#`` comments.
    """
    if not rel_posix.endswith(".py") or not name_map:
        return []

    lines = text.splitlines()
    is_rename_test = rel_posix.startswith("tests/") and "rename" in rel_posix.lower()
    exempted: List[str] = []
    seen: Set[str] = set()

    for old_name in sorted(name_map):
        if old_name in seen:
            continue
        is_misparse_trap = (
            classify_name(old_name) == "legacy"
            and artifact_naming.parse_clustered(old_name) is not None
        )
        matched = False
        for idx, line in enumerate(lines):
            if old_name not in line:
                continue
            if is_misparse_trap:
                prev_line = lines[idx - 1] if idx > 0 else ""
                context = f"{prev_line}\n{line}".lower()
                if any(
                    tok in context for tok in ("parse_clustered", "misparse", "id6=")
                ):
                    matched = True
                    break
            if is_rename_test:
                code_part = line.split("#", 1)[0]
                if f'"{old_name}"' in code_part or f"'{old_name}'" in code_part:
                    matched = True
                    break
        if matched:
            seen.add(old_name)
            exempted.append(old_name)

    return exempted
