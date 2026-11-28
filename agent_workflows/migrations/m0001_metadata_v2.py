"""Migration 0001 (metadata-v2): journaled execution, sidecar import, and rollback.

Implements spec 4sd62s Sections 5.1 (MigrationManager journal reuse), 5.2 step 0
(dry-run default and resume), 5.2 step 2 (sidecar expectedness, op:legacy queueing,
orphan export, sidecar move, and .aw/.gitignore cleanup), 5.2 step 4a (terminal-commit
marker lifecycle), 5.2 step 5 (STATUS.md and INDEX cleanup), and 5.2a item 5.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple, Union

from agent_workflows import (
    artifact_core,
    artifact_meta,
    artifact_naming,
    git_commit_helper,
    ipd_lifecycle,
    layout_migration,
    project_context,
    record_history,
)
from agent_workflows.migrations import (
    chain,
    m0001_convert,
    m0001_describe,
    m0001_discover,
    m0001_preflight,
    m0001_renames,
    m0001_verify,
)

_EXCLUDED_DIRNAMES = m0001_discover.EXCLUDED_DIRNAMES
_EXCLUDED_FILENAMES = frozenset({"README.md", "STATUS.md"})
_PROMPT_COMMENT_RE = re.compile(
    r"\A<!--\s*(?:aw-prompt|aw-managed-prompt):\s*(.*?)\s*-->", re.DOTALL
)
_SIDECAR_GITIGNORE_LINES = frozenset(
    {"records/history.jsonl", "/records/history.jsonl"}
)
_INDEX_GITIGNORE_LINE_RE = re.compile(
    r"^(?:/?(?:\.aw|\.agents)/)?/?(?:records/)?(?:plans|research|prompts)/INDEX\.(?:json|md)$"
)
_STEP5_INDEX_TREES = ("plans", "research", "prompts")
_STEP5_INDEX_NAMES = ("INDEX.json", "INDEX.md")
_OPS_PROGRESS_FILENAME = "ops-progress.jsonl"


def _utc_now() -> str:
    """Return current UTC ISO-8601 timestamp matching MigrationManager format."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _journal_dir_for(repo_path: Path) -> Tuple[Path, Path]:
    """Return ``(journal_dir, records_root)`` resolved through ``project_context``."""
    ctx = project_context.resolve_project_context(target_repo=str(repo_path))
    state_durable = Path(ctx.physical_classes["state_durable"])
    journal_dir = state_durable / "migrations" / "m0001"
    records_root = project_context.project_records_dir(repo_path)
    return journal_dir, records_root


def _make_rebound_manager(
    repo_path: Path, journal_dir: Path
) -> layout_migration.MigrationManager:
    """Instantiate MigrationManager rebound to ``journal_dir`` without touching layout files."""
    mgr = layout_migration.MigrationManager(str(repo_path))
    mgr.transaction_file = journal_dir / "journal.json"
    mgr.lock_file = journal_dir / "writer.lock"
    return mgr


def _replay_ops_progress(tx_data: Dict[str, Any], journal_dir: Path) -> Dict[str, Any]:
    """Replay uncompacted ``ops-progress.jsonl`` events into ``tx_data``.

    Merges ``backup`` and ``applied`` entries into ``tx_data['backups']`` and
    ``tx_data['applied_files']`` deduplicated by ``op_id``. Ignores a truncated,
    unparseable final non-empty line (torn write on abrupt termination), and
    raises ``layout_migration.MigrationError`` if any earlier line is malformed
    JSON or any parsed line is not a valid event object.
    """
    progress_path = journal_dir / _OPS_PROGRESS_FILENAME
    if not progress_path.is_file():
        return tx_data

    raw_text = progress_path.read_text(encoding="utf-8")
    non_empty: List[Tuple[int, str]] = [
        (lineno, raw_line.strip())
        for lineno, raw_line in enumerate(raw_text.splitlines(), start=1)
        if raw_line.strip()
    ]
    if not non_empty:
        return tx_data

    parsed_events: List[Tuple[str, Dict[str, Any]]] = []
    last_idx = len(non_empty) - 1
    for idx, (lineno, line) in enumerate(non_empty):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            if idx == last_idx:
                break
            raise layout_migration.MigrationError(
                f"Malformed JSON in {progress_path} line {lineno}: {exc}"
            ) from exc
        if not isinstance(obj, dict):
            raise layout_migration.MigrationError(
                f"Expected JSON object in {progress_path} line {lineno}, got {type(obj).__name__}"
            )
        event = obj.get("event")
        entry = obj.get("entry")
        if event not in ("backup", "applied") or not isinstance(entry, dict):
            raise layout_migration.MigrationError(
                f"Invalid progress event in {progress_path} line {lineno}: {obj!r}"
            )
        parsed_events.append((event, entry))

    backups = tx_data.setdefault("backups", [])
    applied_files = tx_data.setdefault("applied_files", [])
    seen_backup_ids: Set[str] = {
        str(e["op_id"]) for e in backups if isinstance(e, dict) and e.get("op_id")
    }
    seen_applied_ids: Set[str] = {
        str(e["op_id"]) for e in applied_files if isinstance(e, dict) and e.get("op_id")
    }

    for event, entry in parsed_events:
        op_id = entry.get("op_id")
        if event == "backup":
            if not op_id or str(op_id) not in seen_backup_ids:
                backups.append(entry)
                if op_id:
                    seen_backup_ids.add(str(op_id))
        else:
            if not op_id or str(op_id) not in seen_applied_ids:
                applied_files.append(entry)
                if op_id:
                    seen_applied_ids.add(str(op_id))
    return tx_data


def _load_journal_with_progress(
    mgr: layout_migration.MigrationManager, journal_dir: Path
) -> Optional[Dict[str, Any]]:
    """Load ``journal.json`` via ``mgr`` and replay any uncompacted ``ops-progress.jsonl``."""
    tx_data = mgr._load_transaction()
    if tx_data is None:
        return None
    return _replay_ops_progress(tx_data, journal_dir)


def _peek_journal(journal_dir: Path) -> Optional[Dict[str, Any]]:
    """Read ``journal.json`` and replay any uncompacted progress log, or return None."""
    tx_path = journal_dir / "journal.json"
    if not tx_path.is_file():
        return None
    try:
        data = json.loads(tx_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return _replay_ops_progress(data, journal_dir)


def _filename_id6(filename: str) -> Optional[str]:
    """Extract a valid id6 from ``filename``, testing legacy timestamp names first."""
    if artifact_naming._LEGACY_TIMESTAMP_RE.match(filename):
        return None
    m_attr = artifact_naming.parse_attributed(filename)
    if m_attr and artifact_core.is_valid_id6(m_attr.id6):
        return m_attr.id6
    m_clust = artifact_naming.parse_clustered(filename)
    if m_clust and artifact_core.is_valid_id6(m_clust.group("id6")):
        return m_clust.group("id6")
    m_prefix = artifact_naming.parse_clustered_prefix(filename)
    if m_prefix and artifact_core.is_valid_id6(m_prefix.group("id6")):
        return m_prefix.group("id6")
    return None


def _infile_id6(text: str) -> Optional[str]:
    """Extract a valid in-file id6 from YAML, prompt comment, or bullet block."""
    if text.startswith("---"):
        yaml_probe, _ = artifact_meta._parse_yaml_front_matter(text)
        after_fence = text.split("\n", 1)[1][:200] if "\n" in text else ""
        if yaml_probe and not artifact_meta._BULLET_RE.search(after_fence):
            cand = yaml_probe.get("id") or yaml_probe.get("Id")
            if isinstance(cand, str) and artifact_core.is_valid_id6(cand.strip()):
                return cand.strip()
            return None

    m_prompt = _PROMPT_COMMENT_RE.match(text.lstrip())
    if m_prompt:
        for item in m_prompt.group(1).split("|"):
            if ":" in item:
                k, v = item.split(":", 1)
                if k.strip() in ("Id", "id") and artifact_core.is_valid_id6(v.strip()):
                    return v.strip()

    bullets, _, _ = artifact_meta._parse_bullet_metadata(text)
    cand = bullets.get("Id") or bullets.get("id")
    if isinstance(cand, str) and artifact_core.is_valid_id6(cand.strip()):
        return cand.strip()
    return None


def _walk_record_files(root: Path, *, exclude_dirs: Set[str]) -> List[Path]:
    """Walk ``root`` yielding non-excluded ``.md`` record files in sorted order."""
    if not root.is_dir():
        return []
    found: List[Path] = []
    for cur_dir, dirs, files in os.walk(root):
        dirs[:] = sorted(
            d for d in dirs if d not in exclude_dirs and not d.endswith(".data")
        )
        cur_path = Path(cur_dir)
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            if m0001_discover.is_non_record_filename(fname) or fname.endswith(
                ".review.md"
            ):
                continue
            fpath = cur_path / fname
            try:
                rel_p = fpath.relative_to(root).as_posix()
            except ValueError:
                rel_p = fname
            if m0001_discover.is_excluded_template(
                rel_p, fname, fpath.read_text(encoding="utf-8", errors="replace")
            ):
                continue
            found.append(fpath)
    return found


def _is_sidecar_expected(records_root: Path) -> bool:
    """Return True if ``records_root`` holds any tracked spec or backlog record with an id6."""
    for sub in ("specs", "backlog"):
        for path in _walk_record_files(
            records_root / sub, exclude_dirs=set(_EXCLUDED_DIRNAMES)
        ):
            if _filename_id6(path.name) is not None:
                return True
            text = path.read_text(encoding="utf-8", errors="replace")
            if _infile_id6(text) is not None:
                return True
    return False


def _collect_tracked_record_id6s(records_root: Path) -> Set[str]:
    """Collect every tracked record id6 under ``records_root``."""
    tracked: Set[str] = set()
    for path in _walk_record_files(records_root, exclude_dirs=set(_EXCLUDED_DIRNAMES)):
        fid = _filename_id6(path.name)
        if fid is not None:
            tracked.add(fid)
        text = path.read_text(encoding="utf-8", errors="replace")
        iid = _infile_id6(text)
        if iid is not None:
            tracked.add(iid)
    return tracked


def _read_sidecar_records(sidecar_path: Path) -> List[Dict[str, Any]]:
    """Read and parse JSONL records from ``sidecar_path`` in file order."""
    records: List[Dict[str, Any]] = []
    raw_text = sidecar_path.read_text(encoding="utf-8")
    for lineno, raw_line in enumerate(raw_text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise layout_migration.MigrationError(
                f"Malformed JSON in sidecar {sidecar_path} line {lineno}: {exc}"
            ) from exc
        if not isinstance(obj, dict):
            raise layout_migration.MigrationError(
                f"Expected JSON object in sidecar {sidecar_path} line {lineno}, got {type(obj).__name__}"
            )
        records.append(obj)
    return records


def _classify_sidecar_records(
    records: List[Dict[str, Any]], tracked_id6s: Set[str]
) -> Tuple[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]], Dict[str, int]]:
    """Partition sidecar records into queued ``op: legacy`` events and unresolvable orphans."""
    sidecar_events: Dict[str, List[Dict[str, Any]]] = {}
    orphans: List[Dict[str, Any]] = []
    orphan_counts: Dict[str, int] = {}

    for idx, rec in enumerate(records):
        key_kind = rec.get("key_kind")
        rec_id6 = rec.get("id6")
        if (
            key_kind != "synthetic"
            and isinstance(rec_id6, str)
            and rec_id6 in tracked_id6s
        ):
            payload: Dict[str, Any] = {
                "op": "legacy",
                "source": "sidecar",
                "observed_day": rec.get("date"),
                "position": idx,
                "ordering_confidence": "unknown",
                "line": rec,
            }
            sidecar_events.setdefault(rec_id6, []).append(payload)
        else:
            orphans.append(rec)
            orphan_key = (
                str(rec_id6) if isinstance(rec_id6, str) and rec_id6 else "<missing>"
            )
            orphan_counts[orphan_key] = orphan_counts.get(orphan_key, 0) + 1

    return sidecar_events, orphans, orphan_counts


def _clean_gitignore_history_lines(text: str) -> Tuple[str, bool]:
    """Remove ``records/history.jsonl`` / ``/records/history.jsonl`` lines, preserving all else."""
    lines = text.splitlines(keepends=True)
    kept = [
        ln for ln in lines if ln.rstrip("\r\n").strip() not in _SIDECAR_GITIGNORE_LINES
    ]
    if len(kept) == len(lines):
        return text, False
    return "".join(kept), True


def _clean_gitignore_index_lines(text: str) -> Tuple[str, List[str], bool]:
    """Remove anchored ``records/*/INDEX.*`` ignore lines, preserving surrounding lines and trailing newlines."""
    lines = text.splitlines(keepends=True)
    kept: List[str] = []
    removed: List[str] = []
    for ln in lines:
        stripped = ln.rstrip("\r\n").strip()
        if _INDEX_GITIGNORE_LINE_RE.match(stripped):
            removed.append(stripped)
        else:
            kept.append(ln)
    if not removed:
        return text, [], False
    return "".join(kept), removed, True


def _step5_target_paths(
    repo_path: Path, records_root: Path
) -> Tuple[List[Path], List[Path], List[Path]]:
    """Return ``(status_files, index_files, gitignore_files)`` candidate paths for step 5."""
    status_files: List[Path] = []
    index_files: List[Path] = []
    roots_to_check: List[Path] = [records_root]
    legacy_agents = repo_path / ".agents"
    try:
        if legacy_agents.is_dir() and legacy_agents.resolve() != records_root.resolve():
            roots_to_check.append(legacy_agents)
    except OSError:
        pass

    seen_files: Set[Path] = set()
    for root in roots_to_check:
        status_candidate = root / "plans" / "STATUS.md"
        if status_candidate.is_file():
            try:
                key = status_candidate.resolve()
            except OSError:
                key = status_candidate
            if key not in seen_files:
                seen_files.add(key)
                status_files.append(status_candidate)
        for tree in _STEP5_INDEX_TREES:
            for idx_name in _STEP5_INDEX_NAMES:
                idx_candidate = root / tree / idx_name
                if idx_candidate.is_file():
                    try:
                        key = idx_candidate.resolve()
                    except OSError:
                        key = idx_candidate
                    if key not in seen_files:
                        seen_files.add(key)
                        index_files.append(idx_candidate)

    gitignore_files: List[Path] = []
    for gi in (repo_path / ".aw" / ".gitignore", repo_path / ".agents" / ".gitignore"):
        if gi.is_file():
            gitignore_files.append(gi)
    return status_files, index_files, gitignore_files


def _step_5_cleanup(
    repo: Union[str, Path],
    *,
    scratch: bool = False,
    apply: bool = False,
    records_root: Optional[Path] = None,
    journal_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Delete ``plans/STATUS.md``, ``INDEX.{json,md}`` manifests, and INDEX ignore lines (5.2 step 5).

    On ``apply=True`` (and ``scratch=False``), backs up each deleted or modified file under
    ``journal_dir / 'backups'`` and records ``restore_bytes`` entries in ``journal.json`` so
    ``rollback(repo)`` restores them byte-for-byte. On ``apply=False``, reports planned deletions
    without modifying target files (unless ``scratch=True``, which cleans the scratch tree only).
    """
    repo_path = Path(repo)
    resolved_jdir, resolved_rroot = _journal_dir_for(repo_path)
    eff_jdir = journal_dir or resolved_jdir

    if scratch:
        target_repo = eff_jdir / "scratch" / "repo"
        eff_rroot = target_repo / ".aw" / "records"
    else:
        target_repo = repo_path
        eff_rroot = records_root or resolved_rroot

    status_files, index_files, gitignore_files = _step5_target_paths(
        target_repo, eff_rroot
    )

    removed_lines: List[str] = []
    gitignore_updates: List[Tuple[Path, str, List[str]]] = []
    for gi_path in gitignore_files:
        orig_text = gi_path.read_text(encoding="utf-8")
        cleaned_text, removed, changed = _clean_gitignore_index_lines(orig_text)
        if changed:
            gitignore_updates.append((gi_path, cleaned_text, removed))
            removed_lines.extend(removed)

    if scratch:
        for p in [*status_files, *index_files]:
            p.unlink(missing_ok=True)
        for gi_path, cleaned_text, _removed in gitignore_updates:
            _write_bytes_atomic(gi_path, cleaned_text.encode("utf-8"))
    elif apply:
        backups_dir = eff_jdir / "backups"
        mgr = _make_rebound_manager(repo_path, eff_jdir)
        tx_data = mgr._load_transaction()
        if tx_data is None:
            now_utc = _utc_now()
            tx_data = {
                "schema_version": mgr.SCHEMA_VERSION,
                "migration_id": "m0001",
                "transaction_id": f"m0001-step5-{os.getpid()}",
                "status": "applied",
                "timestamps": {"started_at": now_utc, "updated_at": now_utc},
                "records_root": str(eff_rroot),
                "minted_ids": {},
                "rename_map": {},
                "steps": {},
                "applied_files": [],
                "backups": [],
                "operations": [],
                "descriptions": {},
                "sidecar_events": {},
                "orphan_export_path": None,
                "orphan_counts": {},
                "terminal_commit_marker": None,
            }
        tx_data.setdefault("backups", [])
        tx_data.setdefault("applied_files", [])

        for idx_num, target in enumerate([*status_files, *index_files]):
            op_id = f"step5_delete:{idx_num}:{target.name}"
            existed, backup_name = _save_backup_bytes(backups_dir, op_id, target)
            tx_data["backups"].append(
                {
                    "op_id": op_id,
                    "kind": "restore_bytes",
                    "target": str(target),
                    "existed": existed,
                    "backup_file": backup_name,
                }
            )
            target.unlink(missing_ok=True)
            tx_data["applied_files"].append(
                {
                    "op_id": op_id,
                    "kind": "delete_file",
                    "path": str(target),
                }
            )

        for gi_num, (gi_path, cleaned_text, _removed) in enumerate(gitignore_updates):
            op_id = f"step5_gitignore:{gi_num}:{gi_path.parent.name}"
            existed, backup_name = _save_backup_bytes(backups_dir, op_id, gi_path)
            tx_data["backups"].append(
                {
                    "op_id": op_id,
                    "kind": "restore_bytes",
                    "target": str(gi_path),
                    "existed": existed,
                    "backup_file": backup_name,
                }
            )
            _write_bytes_atomic(gi_path, cleaned_text.encode("utf-8"))
            tx_data["applied_files"].append(
                {
                    "op_id": op_id,
                    "kind": "write_from_scratch",
                    "path": str(gi_path),
                }
            )

        mgr._save_transaction(tx_data)

    deleted_all = [str(p) for p in [*status_files, *index_files]]
    return {
        "status_files": [str(p) for p in status_files],
        "index_files": [str(p) for p in index_files],
        "deleted_files": deleted_all,
        "gitignore_files": [str(gi_path) for gi_path, _, _ in gitignore_updates],
        "gitignore_lines_removed": removed_lines,
        "applied": bool(apply and not scratch),
        "scratch": bool(scratch),
    }


_SCRATCH_COPY_IGNORE = shutil.ignore_patterns(
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".ruff_cache",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "tmp",
    ".tmp",
    "*.lock",
)


def _append_git_info_exclude(repo_path: Path, pattern: str) -> None:
    """Idempotently append ``pattern`` to ``<git_common_dir>/info/exclude``."""
    common_dir = ipd_lifecycle.checkout_git_common_dir(repo_path)
    if common_dir is None:
        return
    exclude_path = common_dir / "info" / "exclude"
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = (
        exclude_path.read_text(encoding="utf-8") if exclude_path.is_file() else ""
    )
    stripped = pattern.strip()
    bare = stripped.lstrip("/")
    candidates = {stripped, bare, stripped.rstrip("/"), bare.rstrip("/")}
    if any(line.strip() in candidates for line in existing.splitlines()):
        return
    prefix = "" if (not existing or existing.endswith("\n")) else "\n"
    exclude_path.write_text(existing + prefix + stripped + "\n", encoding="utf-8")


def _ensure_state_gitignored_via_exclude(
    repo_path: Path, journal_dir: Path, *, apply: bool = False
) -> None:
    """Ensure ``.aw/state/`` (and apply-time ``.aw/records/runs/``) are gitignored via ``info/exclude``.

    On ``.agents/``-only repositories, ``<repo>/.aw/.gitignore`` does not exist during dry run
    or after stage-one rollback. When ``journal_dir`` lives under ``<repo>/.aw/state`` and
    ``git check-ignore`` reports it is not ignored, idempotently append ``/.aw/state/`` to
    ``<git_common_dir>/info/exclude`` without creating an untracked ``.aw/.gitignore``.
    Likewise, when ``apply=True`` acquires the integration lock inside ``<repo>/.aw/records/runs``
    on a repository lacking ``.aw/.gitignore`` (e.g. ``no_sidecar``), keep ``/.aw/records/runs/``
    out of ``git status``.
    """
    aw_state = repo_path / ".aw" / "state"
    try:
        j_res = journal_dir.resolve()
        s_res = aw_state.resolve()
        within_repo_state = j_res == s_res or s_res in j_res.parents
    except OSError:
        within_repo_state = False
    if within_repo_state:
        ign = subprocess.run(
            ["git", "-C", str(repo_path), "check-ignore", "-q", "--", ".aw/state/"],
            capture_output=True,
            check=False,
        )
        if ign.returncode != 0:
            _append_git_info_exclude(repo_path, "/.aw/state/")

    if apply:
        from agent_workflows import runner_shared

        lock_path = runner_shared.integration_lock_path(repo_path)
        runs_dir = repo_path / ".aw" / "records" / "runs"
        try:
            l_res = lock_path.resolve()
            r_res = runs_dir.resolve()
            within_repo_runs = l_res == r_res or r_res in l_res.parents
        except OSError:
            within_repo_runs = False
        if within_repo_runs:
            ign_runs = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_path),
                    "check-ignore",
                    "-q",
                    "--",
                    ".aw/records/runs/",
                ],
                capture_output=True,
                check=False,
            )
            if ign_runs.returncode != 0:
                _append_git_info_exclude(repo_path, "/.aw/records/runs/")


def _root_kind_and_rel(
    target_path: Path,
    repo_path: Optional[Path] = None,
    records_root: Optional[Path] = None,
) -> Tuple[str, str]:
    """Return ``(root_kind, relpath)`` for ``target_path`` without failing on external roots."""
    try:
        t_res = target_path.resolve()
    except OSError:
        t_res = target_path
    if records_root is not None:
        try:
            r_res = records_root.resolve()
            if t_res == r_res or r_res in t_res.parents:
                return "records", t_res.relative_to(r_res).as_posix()
        except (OSError, ValueError):
            pass
    if repo_path is not None:
        try:
            rp_res = repo_path.resolve()
            if t_res == rp_res or rp_res in t_res.parents:
                return "repo", t_res.relative_to(rp_res).as_posix()
        except (OSError, ValueError):
            pass
    return "external", target_path.name


def _stage_scratch(
    repo_path: Path,
    records_root: Path,
    scratch_dir: Path,
    *,
    scan_roots: Optional[Sequence[str]] = None,
    stage1_mgr: Optional[layout_migration.MigrationManager] = None,
    stage1_plan: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[str], bool, Optional[Dict[str, Any]]]:
    """Populate ``scratch_dir`` cleanly and return ``(gitignore_scratch_rel, gitignore_changed, stage1_proj)``."""
    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    scratch_dir.mkdir(parents=True, exist_ok=True)

    scratch_repo = scratch_dir / "repo"
    scratch_repo.mkdir(parents=True, exist_ok=True)
    if records_root.is_dir():
        shutil.copytree(
            records_root,
            scratch_repo / ".aw" / "records",
            symlinks=False,
            ignore=_SCRATCH_COPY_IGNORE,
        )

    if scan_roots:
        for rel in scan_roots:
            if (
                rel == ".aw/records"
                or rel.startswith(".aw/records/")
                or rel == ".aw/.gitignore"
            ):
                continue
            src = repo_path / rel
            dst = scratch_repo / rel
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst, symlinks=False, ignore=_SCRATCH_COPY_IGNORE)
            elif src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    stage1_proj: Optional[Dict[str, Any]] = None
    if stage1_mgr is not None and stage1_plan is not None:
        stage1_proj = stage1_mgr.project_stage_one_to_scratch(
            stage1_plan, scratch_repo, backfill_ids=False
        )

    # Snapshot pre-step-3 records (post-stage-1 when stage1 projected) at scratch_dir / "records".
    if (scratch_repo / ".aw" / "records").is_dir():
        shutil.copytree(
            scratch_repo / ".aw" / "records",
            scratch_dir / "records",
            symlinks=False,
        )

    gitignore_path = repo_path / ".aw" / ".gitignore"
    if gitignore_path.is_file():
        orig_text = gitignore_path.read_text(encoding="utf-8")
        cleaned_text, changed = _clean_gitignore_history_lines(orig_text)
        rel = "repo/.aw/.gitignore"
        dst = scratch_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(cleaned_text if changed else orig_text, encoding="utf-8")
        agents_gi = repo_path / ".agents" / ".gitignore"
        if agents_gi.is_file():
            agents_dst = scratch_dir / "repo/.agents/.gitignore"
            agents_dst.parent.mkdir(parents=True, exist_ok=True)
            agents_dst.write_text(
                agents_gi.read_text(encoding="utf-8"), encoding="utf-8"
            )
        return rel, changed, stage1_proj

    agents_gi = repo_path / ".agents" / ".gitignore"
    if agents_gi.is_file():
        agents_dst = scratch_dir / "repo/.agents/.gitignore"
        agents_dst.parent.mkdir(parents=True, exist_ok=True)
        agents_dst.write_text(agents_gi.read_text(encoding="utf-8"), encoding="utf-8")

    return None, False, stage1_proj


def _verify_scratch_scan_roots(
    repo_path: Path,
    records_root: Path,
    scratch_repo: Path,
    scan_roots: Sequence[str],
) -> None:
    """Refuse when any scan root present in the checkout is missing from ``scratch_repo``."""
    scratch_records = scratch_repo / ".aw" / "records"
    for rel in scan_roots:
        if rel == ".aw/records" or rel.startswith(".aw/records/"):
            tail = rel[len(".aw/records/") :] if rel.startswith(".aw/records/") else ""
            src = records_root / tail if tail else records_root
            dst = scratch_records / tail if tail else scratch_records
        else:
            src = repo_path / rel
            dst = scratch_repo / rel
        if src.exists() and not dst.exists():
            raise layout_migration.MigrationError(
                f"Scratch copy is missing scan root {rel!r} (expected at {dst})"
            )


def _save_backup_bytes_keyed(
    backups_dir: Path,
    op_id: str,
    target_path: Path,
    *,
    repo_path: Optional[Path] = None,
    records_root: Optional[Path] = None,
) -> Tuple[bool, Optional[str], str, str]:
    """Save pre-apply bytes of ``target_path`` keyed by ``(root_kind, relpath)``."""
    import hashlib

    backups_dir.mkdir(parents=True, exist_ok=True)
    root_kind, relpath = _root_kind_and_rel(
        target_path, repo_path=repo_path, records_root=records_root
    )
    if not target_path.exists():
        return False, None, root_kind, relpath
    key_digest = hashlib.sha256(
        f"{root_kind}:{relpath}:{op_id}".encode("utf-8")
    ).hexdigest()[:12]
    safe_rel = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{root_kind}__{relpath}")[:120]
    safe_name = f"{safe_rel}_{key_digest}.bak"
    backup_path = backups_dir / safe_name
    backup_path.write_bytes(target_path.read_bytes())
    return True, safe_name, root_kind, relpath


def _save_backup_bytes(
    backups_dir: Path, op_id: str, target_path: Path
) -> Tuple[bool, Optional[str]]:
    """Save pre-apply bytes of ``target_path`` under ``backups_dir``."""
    existed, safe_name, _rk, _rp = _save_backup_bytes_keyed(
        backups_dir, op_id, target_path
    )
    return existed, safe_name


def _write_bytes_atomic(target: Path, data: bytes, *, fsync: bool = True) -> None:
    """Atomically write ``data`` to ``target`` via a sibling temp file."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.parent / f".aw-tmp-{target.name}-{os.getpid()}"
    try:
        with open(tmp_path, "wb") as fh:
            fh.write(data)
            fh.flush()
            if fsync:
                os.fsync(fh.fileno())
        os.replace(tmp_path, target)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def _execute_planned_operations(
    mgr: layout_migration.MigrationManager,
    tx_data: Dict[str, Any],
    journal_dir: Path,
    *,
    repo_path: Optional[Path] = None,
    records_root: Optional[Path] = None,
    fault_injection: Optional[str] = None,
) -> None:
    """Apply remaining operations from ``journal_dir / 'scratch'``, backing up each target."""
    progress_path = journal_dir / _OPS_PROGRESS_FILENAME
    if progress_path.is_file():
        _replay_ops_progress(tx_data, journal_dir)
        mgr._save_transaction(tx_data)
        progress_path.unlink(missing_ok=True)

    tx_data.setdefault("backups", [])
    tx_data.setdefault("applied_files", [])
    done_ids = {
        entry.get("op_id")
        for entry in tx_data["applied_files"]
        if isinstance(entry, dict) and entry.get("op_id")
    }
    backed_up_by_id: Dict[str, Dict[str, Any]] = {
        str(entry["op_id"]): entry
        for entry in tx_data["backups"]
        if isinstance(entry, dict) and entry.get("op_id")
    }
    backups_dir = journal_dir / "backups"
    scratch_dir = journal_dir / "scratch"
    eff_repo = repo_path or Path(mgr.target_repo)
    eff_records = records_root or (
        Path(tx_data["records_root"])
        if tx_data.get("records_root")
        else project_context.project_records_dir(eff_repo)
    )

    journal_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(progress_path, "a", encoding="utf-8") as fh:

            def _append_progress(event: str, entry: Dict[str, Any]) -> None:
                fh.write(
                    json.dumps({"event": event, "entry": entry}, ensure_ascii=False)
                    + "\n"
                )
                fh.flush()

            for op in tx_data.get("operations") or []:
                op_id = op["op_id"]
                if op_id in done_ids:
                    continue

                kind = op["kind"]
                existing_backup = backed_up_by_id.get(op_id)

                if kind == "move_to_journal":
                    src = Path(op["src"])
                    dst = Path(op["dst"])
                    if existing_backup is not None:
                        root_kind = str(existing_backup.get("root_kind") or "")
                        relpath = str(existing_backup.get("relpath") or "")
                        if not root_kind:
                            root_kind, relpath = _root_kind_and_rel(
                                src, repo_path=eff_repo, records_root=eff_records
                            )
                    else:
                        existed, backup_name, root_kind, relpath = (
                            _save_backup_bytes_keyed(
                                backups_dir,
                                op_id,
                                src,
                                repo_path=eff_repo,
                                records_root=eff_records,
                            )
                        )
                        backup_entry: Dict[str, Any] = {
                            "op_id": op_id,
                            "kind": "restore_moved",
                            "root_kind": root_kind,
                            "relpath": relpath,
                            "target": str(src),
                            "moved_to": str(dst),
                            "existed": existed,
                            "backup_file": backup_name,
                        }
                        tx_data["backups"].append(backup_entry)
                        backed_up_by_id[op_id] = backup_entry
                        _append_progress("backup", backup_entry)
                    if src.exists():
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(src), str(dst))
                    applied_entry: Dict[str, Any] = {
                        "op_id": op_id,
                        "kind": kind,
                        "root_kind": root_kind,
                        "relpath": relpath,
                        "path": str(src),
                        "dst": str(dst),
                    }
                    tx_data["applied_files"].append(applied_entry)
                    _append_progress("applied", applied_entry)
                elif kind == "write_from_scratch":
                    target = Path(op["target"])
                    scratch_src = scratch_dir / op["scratch_rel"]
                    if existing_backup is not None:
                        root_kind = str(existing_backup.get("root_kind") or "")
                        relpath = str(existing_backup.get("relpath") or "")
                        if not root_kind:
                            root_kind, relpath = _root_kind_and_rel(
                                target, repo_path=eff_repo, records_root=eff_records
                            )
                    else:
                        existed, backup_name, root_kind, relpath = (
                            _save_backup_bytes_keyed(
                                backups_dir,
                                op_id,
                                target,
                                repo_path=eff_repo,
                                records_root=eff_records,
                            )
                        )
                        backup_entry = {
                            "op_id": op_id,
                            "kind": "restore_bytes",
                            "root_kind": root_kind,
                            "relpath": relpath,
                            "target": str(target),
                            "existed": existed,
                            "backup_file": backup_name,
                        }
                        tx_data["backups"].append(backup_entry)
                        backed_up_by_id[op_id] = backup_entry
                        _append_progress("backup", backup_entry)
                    # Bulk apply loop: atomic temp-file + os.replace per file; durability is
                    # anchored by backups + progress log + transaction commit rather than
                    # thousands of synchronous per-file fsync barriers.
                    _write_bytes_atomic(target, scratch_src.read_bytes(), fsync=False)
                    applied_entry = {
                        "op_id": op_id,
                        "kind": kind,
                        "root_kind": root_kind,
                        "relpath": relpath,
                        "path": str(target),
                    }
                    tx_data["applied_files"].append(applied_entry)
                    _append_progress("applied", applied_entry)
                elif kind == "delete_file":
                    target = Path(op["target"])
                    if existing_backup is not None:
                        root_kind = str(existing_backup.get("root_kind") or "")
                        relpath = str(existing_backup.get("relpath") or "")
                        if not root_kind:
                            root_kind, relpath = _root_kind_and_rel(
                                target, repo_path=eff_repo, records_root=eff_records
                            )
                    else:
                        existed, backup_name, root_kind, relpath = (
                            _save_backup_bytes_keyed(
                                backups_dir,
                                op_id,
                                target,
                                repo_path=eff_repo,
                                records_root=eff_records,
                            )
                        )
                        backup_entry = {
                            "op_id": op_id,
                            "kind": "restore_bytes",
                            "root_kind": root_kind,
                            "relpath": relpath,
                            "target": str(target),
                            "existed": existed,
                            "backup_file": backup_name,
                        }
                        tx_data["backups"].append(backup_entry)
                        backed_up_by_id[op_id] = backup_entry
                        _append_progress("backup", backup_entry)
                    target.unlink(missing_ok=True)
                    applied_entry = {
                        "op_id": op_id,
                        "kind": kind,
                        "root_kind": root_kind,
                        "relpath": relpath,
                        "path": str(target),
                    }
                    tx_data["applied_files"].append(applied_entry)
                    _append_progress("applied", applied_entry)
                else:
                    raise layout_migration.MigrationError(
                        f"Unknown m0001 operation kind: {kind!r}"
                    )

                done_ids.add(op_id)

                if (
                    fault_injection == "interrupt-mid-apply"
                    and tx_data["applied_files"]
                ):
                    raise layout_migration.MigrationError(
                        "Injected fault: interrupt-mid-apply"
                    )
                if fault_injection == "stage2-failure" and tx_data["applied_files"]:
                    raise layout_migration.MigrationError(
                        "Injected fault: stage2-failure"
                    )

            if fault_injection == "stage2-failure":
                raise layout_migration.MigrationError("Injected fault: stage2-failure")

            tx_data["status"] = "applied"
    finally:
        mgr._save_transaction(tx_data)
        progress_path.unlink(missing_ok=True)


def _staged_paths_in_index(repo_path: Path) -> Set[str]:
    """Return repo-relative paths currently staged in ``repo_path``'s index (including renames)."""
    proc = subprocess.run(
        ["git", "-C", str(repo_path), "diff", "--cached", "--name-status", "-z"],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout:
        return set()
    fields = proc.stdout.decode("utf-8", errors="replace").split("\0")
    staged: Set[str] = set()
    i = 0
    while i < len(fields):
        status = fields[i]
        if not status:
            i += 1
            continue
        if status[:1] in ("R", "C"):
            for cand in fields[i + 1 : i + 3]:
                if cand:
                    staged.add(cand)
            i += 3
            continue
        if i + 1 < len(fields) and fields[i + 1]:
            staged.add(fields[i + 1])
        i += 2
    return staged


def _collect_stageable_paths(
    repo_path: Path, tx_data: Dict[str, Any]
) -> Tuple[List[str], List[str]]:
    """Return ``(all_commit_paths, addable_paths)`` relative to ``repo_path``."""
    try:
        repo_resolved = repo_path.resolve()
    except OSError:
        repo_resolved = repo_path

    candidates: List[str] = []
    seen: Set[str] = set()

    def _add_candidate(raw: Optional[str]) -> None:
        if not raw:
            return
        p = Path(raw)
        if not p.is_absolute():
            p = repo_path / p
        try:
            rel = p.resolve().relative_to(repo_resolved).as_posix()
        except (OSError, ValueError):
            try:
                rel = p.relative_to(repo_path).as_posix()
            except ValueError:
                return
        if rel not in seen:
            seen.add(rel)
            candidates.append(rel)

    for op in tx_data.get("operations") or []:
        kind = op.get("kind")
        if kind in ("write_from_scratch", "delete_file"):
            _add_candidate(op.get("target"))
        elif kind == "move_to_journal":
            _add_candidate(op.get("src"))
    for extra in tx_data.get("extra_stage_paths") or []:
        _add_candidate(extra)
    for included in tx_data.get("include_paths") or []:
        _add_candidate(included)

    if not candidates:
        return [], []

    tracked_set: Set[str] = set()
    for i in range(0, len(candidates), 200):
        batch = candidates[i : i + 200]
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "ls-files", "-z", "--", *batch],
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            for item in proc.stdout.decode("utf-8", errors="replace").split("\0"):
                if item:
                    tracked_set.add(item)

    already_staged = _staged_paths_in_index(repo_path)

    untracked_existing: List[str] = []
    for rel in candidates:
        if rel not in tracked_set:
            disk_path = repo_path / rel
            if disk_path.exists() or disk_path.is_symlink():
                untracked_existing.append(rel)

    ignored_set: Set[str] = set()
    if untracked_existing:
        ign = subprocess.run(
            ["git", "-C", str(repo_path), "check-ignore", "--stdin", "-z"],
            input=("\0".join(untracked_existing) + "\0").encode("utf-8"),
            capture_output=True,
            check=False,
        )
        if ign.returncode == 0 and ign.stdout:
            for item in ign.stdout.decode("utf-8", errors="replace").split("\0"):
                if item:
                    ignored_set.add(item)

    untracked_existing_set = set(untracked_existing)
    stageable: List[str] = []
    addable: List[str] = []
    for rel in candidates:
        if rel in tracked_set:
            stageable.append(rel)
            addable.append(rel)
            continue
        if rel in untracked_existing_set:
            if rel not in ignored_set:
                stageable.append(rel)
                addable.append(rel)
            continue
        if rel in already_staged:
            stageable.append(rel)
    return stageable, addable


def normalize_include_paths(
    repo: Union[str, Path],
    include_paths: Optional[Sequence[Union[str, Path]]],
    *,
    records_root: Optional[Path] = None,
) -> List[str]:
    """Validate ``--include-paths`` and return them as sorted repo-relative POSIX paths.

    Spec 4sd62s 5.2 step 7: the one migration commit may also carry explicitly named extra
    paths (the cutover's code, test and documentation changes). Each must be a file (or a
    tracked file's deletion) inside the repository, not git-ignored, and outside the records
    root that the migration itself rewrites. Raises ``PreflightGateError`` naming every bad
    path before anything is written.
    """
    if not include_paths:
        return []
    repo_path = Path(repo)
    try:
        repo_resolved = repo_path.resolve()
    except OSError:
        repo_resolved = repo_path
    eff_records = records_root or project_context.project_records_dir(repo_path)
    try:
        records_resolved: Optional[Path] = eff_records.resolve()
    except OSError:
        records_resolved = None

    problems: List[str] = []
    accepted: List[str] = []
    for raw in include_paths:
        text = str(raw).strip()
        if not text:
            problems.append("an empty path")
            continue
        cand = Path(text)
        if not cand.is_absolute():
            cand = repo_path / cand
        try:
            resolved = cand.resolve()
            rel = resolved.relative_to(repo_resolved).as_posix()
        except (OSError, ValueError):
            problems.append(f"{text}: outside the repository")
            continue
        if rel in ("", ".") or rel == ".git" or rel.startswith(".git/"):
            problems.append(f"{text}: not a repository file")
            continue
        if records_resolved is not None:
            try:
                resolved.relative_to(records_resolved)
                problems.append(
                    f"{text}: inside the records root, which the migration itself rewrites"
                )
                continue
            except ValueError:
                pass
        if resolved.is_dir():
            problems.append(f"{text}: a directory (name each file explicitly)")
            continue
        tracked = (
            subprocess.run(
                ["git", "-C", str(repo_path), "ls-files", "--error-unmatch", "--", rel],
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )
        if not tracked:
            if not (resolved.exists() or resolved.is_symlink()):
                problems.append(f"{text}: neither tracked nor present on disk")
                continue
            ignored = (
                subprocess.run(
                    ["git", "-C", str(repo_path), "check-ignore", "-q", "--", rel],
                    capture_output=True,
                    check=False,
                ).returncode
                == 0
            )
            if ignored:
                problems.append(f"{text}: ignored by git")
                continue
        if rel not in accepted:
            accepted.append(rel)

    if problems:
        raise layout_migration.PreflightGateError(
            "m0001 --include-paths refused (nothing was written):\n- "
            + "\n- ".join(problems)
        )
    return sorted(accepted)


def _stage_migration_paths(repo_path: Path, tx_data: Dict[str, Any]) -> List[str]:
    """Stage the migration's complete path list in ``repo_path`` and return staged repo-relative paths."""
    staged, addable = _collect_stageable_paths(repo_path, tx_data)
    for i in range(0, len(addable), 200):
        batch = addable[i : i + 200]
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "add", "-A", "--", *batch],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            raise layout_migration.MigrationError(
                f"Failed to stage m0001 migration paths: {proc.stderr.strip() or f'exit {proc.returncode}'}"
            )
    return staged


def _unstage_migration_paths(repo_path: Path, paths: Sequence[str]) -> None:
    """Restore the git index for ``paths`` during rollback without touching unrelated entries."""
    rel_paths = [str(p) for p in paths if str(p).strip()]
    if not rel_paths:
        return
    has_head = (
        subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )
    for i in range(0, len(rel_paths), 200):
        batch = rel_paths[i : i + 200]
        cmd = (
            ["git", "-C", str(repo_path), "reset", "-q", "HEAD", "--", *batch]
            if has_head
            else [
                "git",
                "-C",
                str(repo_path),
                "rm",
                "--cached",
                "-q",
                "--ignore-unmatch",
                "--",
                *batch,
            ]
        )
        subprocess.run(cmd, capture_output=True, check=False)


def _step_4a_write_marker(
    repo: Union[str, Path], journal_dir: Union[str, Path]
) -> Path:
    """Capture staged ``git write-tree`` id and write ``terminal_commit_marker.json`` (5.2 step 4a)."""
    repo_path = Path(repo)
    jdir = Path(journal_dir)
    proc = subprocess.run(
        ["git", "-C", str(repo_path), "write-tree"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise layout_migration.PreflightGateError(
            "m0001 step 4a failed to capture staged index tree via `git write-tree`: "
            f"{proc.stderr.strip() or f'exit {proc.returncode}'}"
        )
    tree_id = proc.stdout.strip()
    marker_payload = {
        "migration_id": "m0001",
        "tree_id": tree_id,
        "created_at": artifact_core.utc_history_date(),
    }
    jdir.mkdir(parents=True, exist_ok=True)
    marker_path = jdir / "terminal_commit_marker.json"
    _write_bytes_atomic(
        marker_path,
        (json.dumps(marker_payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )

    mgr = _make_rebound_manager(repo_path, jdir)
    tx_data = mgr._load_transaction()
    if tx_data is None:
        now_utc = _utc_now()
        tx_data = {
            "schema_version": mgr.SCHEMA_VERSION,
            "migration_id": "m0001",
            "transaction_id": f"m0001-marker-{os.getpid()}",
            "status": "applying",
            "timestamps": {"started_at": now_utc, "updated_at": now_utc},
        }
    tx_data["terminal_commit_marker"] = {
        "migration_id": "m0001",
        "tree_id": tree_id,
    }
    mgr._save_transaction(tx_data)
    return marker_path


def _cleanup_marker(
    journal_dir: Union[str, Path], *, repo: Optional[Union[str, Path]] = None
) -> None:
    """Remove ``terminal_commit_marker.json`` and clear ``journal.json['terminal_commit_marker']``."""
    jdir = Path(journal_dir)
    marker_file = jdir / "terminal_commit_marker.json"
    marker_file.unlink(missing_ok=True)

    tx_path = jdir / "journal.json"
    if not tx_path.is_file():
        return
    tx_data = _peek_journal(jdir)
    if tx_data is None:
        return
    tx_data["terminal_commit_marker"] = None
    tx_data.setdefault(
        "timestamps", {"started_at": _utc_now(), "updated_at": _utc_now()}
    )
    repo_hint = Path(repo) if repo is not None else jdir
    mgr = _make_rebound_manager(repo_hint, jdir)
    mgr._save_transaction(tx_data)


def _apply_step6_stamp(
    repo_path: Path,
    mgr: layout_migration.MigrationManager,
    tx_data: Dict[str, Any],
    journal_dir: Path,
) -> Path:
    """Back up resolved ``project.json``, write ``metadata_schema: 2``, and record stage path."""
    done_ids = {
        entry.get("op_id")
        for entry in (tx_data.get("applied_files") or [])
        if isinstance(entry, dict) and entry.get("op_id")
    }
    proj_json_path = chain._resolve_project_json(repo_path)
    if "step6_metadata_schema" not in done_ids:
        backups_dir = journal_dir / "backups"
        existed, backup_name = _save_backup_bytes(
            backups_dir, "step6_metadata_schema", proj_json_path
        )
        tx_data.setdefault("backups", []).append(
            {
                "op_id": "step6_metadata_schema",
                "kind": "restore_bytes",
                "target": str(proj_json_path),
                "existed": existed,
                "backup_file": backup_name,
            }
        )
        chain.write_metadata_schema(repo_path, 2)
        tx_data.setdefault("applied_files", []).append(
            {
                "op_id": "step6_metadata_schema",
                "kind": "write_stamp",
                "path": str(proj_json_path),
            }
        )

    extra_paths = list(tx_data.get("extra_stage_paths") or [])
    try:
        proj_json_path.resolve().relative_to(repo_path.resolve())
        proj_str = str(proj_json_path)
        if proj_str not in extra_paths:
            extra_paths.append(proj_str)
    except (OSError, ValueError):
        pass
    tx_data["extra_stage_paths"] = extra_paths
    mgr._save_transaction(tx_data)
    return proj_json_path


def commit_staged(
    repo: Union[str, Path],
    paths: Optional[Sequence[str]] = None,
    *,
    message: str = "chore(migrate): apply m0001 metadata-v2 migration",
) -> git_commit_helper.CommitOutcome:
    """Execute step-7 path-scoped commit via ``git_commit_helper.offer_commit`` and clean marker."""
    repo_path = Path(repo)
    journal_dir, _records_root = _journal_dir_for(repo_path)
    tx_data = _peek_journal(journal_dir) or {}
    target_paths = (
        list(paths) if paths is not None else list(tx_data.get("staged_paths") or [])
    )
    if not target_paths:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            target_paths = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]

    outcome = git_commit_helper.offer_commit(
        repo_path,
        target_paths,
        message=message,
        assume_yes=True,
        runner=git_commit_helper.RUNNER_AW_COMMIT,
    )
    if outcome.status in (
        git_commit_helper.STATUS_COMMITTED,
        git_commit_helper.STATUS_NOTHING_TO_COMMIT,
    ):
        _cleanup_marker(journal_dir, repo=repo_path)
    return outcome


def _format_run_report(
    tx_data: Dict[str, Any],
    journal_dir: Path,
    *,
    applied: bool,
    resumed: bool = False,
) -> Dict[str, Any]:
    """Build the public return dictionary for ``run`` and ``resume``."""
    steps = tx_data.get("steps") or {}
    return {
        "migration_id": tx_data.get("migration_id", "m0001"),
        "transaction_id": tx_data.get("transaction_id"),
        "status": tx_data.get("status"),
        "applied": applied,
        "dry_run": not applied,
        "resumed": resumed,
        "journal_dir": str(journal_dir),
        "journal_path": str(journal_dir / "journal.json"),
        "scratch_dir": str(journal_dir / "scratch"),
        "layout_stage": tx_data.get("layout_stage") or steps.get("layout_stage"),
        "preflight": steps.get("preflight"),
        "sidecar": steps.get("sidecar"),
        "renames": steps.get("renames"),
        "citations": steps.get("citations"),
        "conversion": steps.get("conversion"),
        "cleanup": steps.get("cleanup"),
        "descriptions_summary": steps.get("descriptions"),
        "census": steps.get("census"),
        "round_trip": steps.get("round_trip"),
        "commit": tx_data.get("commit_result"),
        "companion_commit": tx_data.get("companion_commit_result"),
        "sidecar_events": tx_data.get("sidecar_events") or {},
        "orphan_export_path": tx_data.get("orphan_export_path"),
        "orphan_counts": tx_data.get("orphan_counts") or {},
        "applied_files": list(tx_data.get("applied_files") or []),
        "staged_paths": list(tx_data.get("staged_paths") or []),
        "include_paths": list(tx_data.get("include_paths") or []),
        "minted_ids": dict(tx_data.get("minted_ids") or {}),
        "rename_map": dict(tx_data.get("rename_map") or {}),
        "terminal_commit_marker": tx_data.get("terminal_commit_marker"),
    }


def _stage_and_commit_external_records(
    records_root: Path,
    repo_path: Path,
    tx_data: Dict[str, Any],
    mgr: layout_migration.MigrationManager,
    *,
    commit: bool,
) -> None:
    """Stage (and commit when ``commit=True``) external companion-repo record changes."""
    record_git = project_context.record_git_root(records_root)
    if record_git is None:
        return
    try:
        if record_git.resolve() == repo_path.resolve():
            return
    except OSError:
        return

    staged, addable = _collect_stageable_paths(record_git, tx_data)
    if not staged:
        return
    for i in range(0, len(addable), 200):
        batch = addable[i : i + 200]
        proc = subprocess.run(
            ["git", "-C", str(record_git), "add", "-A", "--", *batch],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            raise layout_migration.MigrationError(
                f"Failed to stage companion records paths: {proc.stderr.strip() or f'exit {proc.returncode}'}"
            )
    tx_data["companion_staged_paths"] = staged
    mgr._save_transaction(tx_data)

    if commit:
        outcome = git_commit_helper.offer_commit(
            record_git,
            staged,
            message="chore(migrate): apply m0001 metadata-v2 migration (records)",
            assume_yes=True,
            runner=git_commit_helper.RUNNER_AW_COMMIT,
        )
        tx_data["companion_commit_result"] = {
            "status": outcome.status,
            "commit_sha": outcome.commit,
            "detail": outcome.message,
        }
        mgr._save_transaction(tx_data)
        if outcome.status == git_commit_helper.STATUS_ERROR:
            raise layout_migration.MigrationError(
                f"m0001 step-7 companion records commit failed: {outcome.message}"
            )


def _finish_apply_after_ops(
    repo_path: Path,
    mgr: layout_migration.MigrationManager,
    tx_data: Dict[str, Any],
    journal_dir: Path,
    *,
    records_root: Optional[Path] = None,
    commit: bool,
) -> Dict[str, Any]:
    """Write ``metadata_schema: 2``, stage explicit paths, write marker, and optionally commit."""
    eff_records = records_root or (
        Path(tx_data["records_root"])
        if tx_data.get("records_root")
        else project_context.project_records_dir(repo_path)
    )
    _apply_step6_stamp(repo_path, mgr, tx_data, journal_dir)
    staged_paths = _stage_migration_paths(repo_path, tx_data)
    tx_data["staged_paths"] = staged_paths
    mgr._save_transaction(tx_data)
    _step_4a_write_marker(repo_path, journal_dir)
    if commit:
        outcome = commit_staged(repo_path, staged_paths)
        tx_data = mgr._load_transaction() or tx_data
        tx_data["commit_result"] = {
            "status": outcome.status,
            "commit_sha": outcome.commit,
            "detail": outcome.message,
        }
        mgr._save_transaction(tx_data)
        if outcome.status == git_commit_helper.STATUS_ERROR:
            raise layout_migration.MigrationError(
                f"m0001 step-7 commit failed: {outcome.message}"
            )
    _stage_and_commit_external_records(
        eff_records, repo_path, tx_data, mgr, commit=commit
    )
    return mgr._load_transaction() or tx_data


def _rollback_all_locked(
    repo_path: Path,
    mgr: layout_migration.MigrationManager,
    tx_data: Dict[str, Any],
    journal_dir: Path,
    *,
    records_root: Optional[Path] = None,
) -> int:
    """Roll back stage two (`applied_files`/`backups` in reverse) and then embedded stage one."""
    tx_data = _replay_ops_progress(tx_data, journal_dir)
    backups_dir = journal_dir / "backups"
    restored = 0
    for entry in reversed(tx_data.get("backups") or []):
        target = Path(entry["target"])
        kind = entry.get("kind")
        existed = bool(entry.get("existed"))
        backup_file = entry.get("backup_file")

        if existed and backup_file:
            raw_bytes = (backups_dir / backup_file).read_bytes()
            _write_bytes_atomic(target, raw_bytes)
        else:
            target.unlink(missing_ok=True)

        if kind == "restore_moved" and entry.get("moved_to"):
            Path(entry["moved_to"]).unlink(missing_ok=True)

        restored += 1

    eff_records = records_root or (
        Path(tx_data["records_root"])
        if tx_data.get("records_root")
        else project_context.project_records_dir(repo_path)
    )
    meta_dir = eff_records / "meta"
    try:
        if meta_dir.is_dir() and not any(meta_dir.iterdir()):
            meta_dir.rmdir()
    except OSError:
        pass

    _unstage_migration_paths(repo_path, tx_data.get("staged_paths") or [])
    comp_staged = tx_data.get("companion_staged_paths") or []
    if comp_staged:
        rec_git = project_context.record_git_root(eff_records)
        if rec_git is not None:
            _unstage_migration_paths(rec_git, comp_staged)

    _cleanup_marker(journal_dir, repo=repo_path)

    tx_data = _load_journal_with_progress(mgr, journal_dir) or tx_data
    ls = tx_data.get("layout_stage")
    if isinstance(ls, dict) and ls.get("status") not in (
        None,
        "skipped",
        "planned",
        "rolled_back",
    ):
        mgr.rollback_embedded_stage_one(tx_data, caller_holds_lock=True)
        tx_data = _load_journal_with_progress(mgr, journal_dir) or tx_data

    tx_data["staged_paths"] = []
    tx_data["companion_staged_paths"] = []
    tx_data["terminal_commit_marker"] = None
    tx_data["status"] = "rolled_back"
    mgr._save_transaction(tx_data)
    (journal_dir / _OPS_PROGRESS_FILENAME).unlink(missing_ok=True)
    return restored


def _build_stage1_report_summary(
    *,
    needed: bool,
    stage1_plan: Optional[Dict[str, Any]] = None,
    stage1_proj: Optional[Dict[str, Any]] = None,
    stage1_applied: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build normalized ``layout_stage`` summary for reports and step-6 census."""
    if not needed:
        return {"status": "skipped", "reason": "already on .aw/"}
    if stage1_applied is not None:
        return {
            "status": str(stage1_applied.get("status") or "completed"),
            "target_backend": stage1_applied.get("target_backend", "repository"),
            "planned_count": int(stage1_applied.get("planned_count") or 0),
            "moved": int(stage1_applied.get("moved") or 0),
            "renamed": int(stage1_applied.get("renamed") or 0),
            "dedup_removed": int(stage1_applied.get("dedup_removed") or 0),
            "groups": dict(
                stage1_applied.get("groups")
                or stage1_applied.get("planned_groups")
                or {}
            ),
        }
    if stage1_proj is not None:
        return {
            "status": "planned",
            "target_backend": stage1_proj.get("target_backend", "repository"),
            "planned_count": int(stage1_proj.get("planned_count") or 0),
            "dedup_skipped": int(stage1_proj.get("dedup_skipped") or 0),
            "groups": dict(stage1_proj.get("groups") or {}),
        }
    if stage1_plan is not None:
        return {
            "status": "planned",
            "target_backend": stage1_plan.get("target_backend", "repository"),
            "planned_count": int(stage1_plan.get("planned_count") or 0),
            "groups": dict(stage1_plan.get("groups") or {}),
        }
    return {"status": "planned"}


def _plan_and_apply_stage2_locked(
    repo_path: Path,
    mgr: layout_migration.MigrationManager,
    tx_data: Dict[str, Any],
    journal_dir: Path,
    records_root: Path,
    *,
    apply: bool,
    describer: Optional[Any],
    fault_injection: Optional[str],
    commit: bool,
    sidecar_path: Path,
    sidecar_present: bool,
    sidecar_records: List[Dict[str, Any]],
    sidecar_summary: Dict[str, Any],
    layout_stage_report: Dict[str, Any],
    stage1_mgr: Optional[layout_migration.MigrationManager] = None,
    stage1_plan: Optional[Dict[str, Any]] = None,
    clear_stale_progress: bool = False,
) -> Dict[str, Any]:
    """Plan stage 2 in scratch and, when ``apply=True``, execute and commit stage 2."""
    tracked_id6s = _collect_tracked_record_id6s(records_root)
    sidecar_events, orphans, orphan_counts = _classify_sidecar_records(
        sidecar_records, tracked_id6s
    )

    orphan_file = journal_dir / "sidecar-orphans.jsonl"
    if orphans:
        journal_dir.mkdir(parents=True, exist_ok=True)
        orphan_payload = "".join(
            json.dumps(rec, ensure_ascii=False) + "\n" for rec in orphans
        )
        orphan_file.write_text(orphan_payload, encoding="utf-8")
        orphan_export_path: Optional[str] = str(orphan_file)
    else:
        if orphan_file.exists():
            orphan_file.unlink()
        orphan_export_path = None

    scratch_dir = journal_dir / "scratch"
    gitignore_rel, gitignore_changed, stage1_proj = _stage_scratch(
        repo_path,
        records_root,
        scratch_dir,
        scan_roots=m0001_renames.M0001_SCAN_ROOTS,
        stage1_mgr=stage1_mgr,
        stage1_plan=stage1_plan,
    )
    scratch_repo = scratch_dir / "repo"
    _verify_scratch_scan_roots(
        repo_path,
        records_root,
        scratch_repo,
        m0001_renames.M0001_SCAN_ROOTS,
    )

    if stage1_proj is not None:
        layout_stage_report = _build_stage1_report_summary(
            needed=True, stage1_plan=stage1_plan, stage1_proj=stage1_proj
        )
        tx_data["layout_stage"] = dict(layout_stage_report)

    tx_data["records_root"] = str(records_root)
    tx_data["steps"]["layout_stage"] = dict(layout_stage_report)
    tx_data["steps"]["sidecar"] = {
        **sidecar_summary,
        "queued_id6_count": len(sidecar_events),
        "queued_event_count": sum(len(v) for v in sidecar_events.values()),
        "orphan_record_count": len(orphans),
    }
    tx_data["sidecar_events"] = sidecar_events
    tx_data["orphan_export_path"] = orphan_export_path
    tx_data["orphan_counts"] = orphan_counts

    # Step 3: legacy-name rename map, protected citation plan, and scratch apply.
    rename_map = m0001_renames.build_rename_map(scratch_repo, tx_data)
    citation_plan = m0001_renames.plan_citation_rewrites(scratch_repo, rename_map)
    step3_summary = m0001_renames.apply_step3(
        scratch_repo,
        rename_map,
        citation_plan,
        tx_data,
        save_callback=None,
    )
    mgr._save_transaction(tx_data)
    post_step3_dir = scratch_dir / "post_step3_records"
    if post_step3_dir.exists():
        shutil.rmtree(post_step3_dir)
    if (scratch_repo / ".aw" / "records").is_dir():
        shutil.copytree(
            scratch_repo / ".aw" / "records",
            post_step3_dir,
            symlinks=False,
        )
    tx_data["rename_map"] = {e.old_rel: e.new_rel for e in rename_map.entries}
    tx_data["steps"]["renames"] = {
        "entry_count": len(rename_map.entries),
        "minted_count": sum(1 for e in rename_map.entries if e.minted),
        "preserved_count": sum(1 for e in rename_map.entries if not e.minted),
        "entries": [
            {
                "id6": e.id6,
                "minted": e.minted,
                "old_rel": e.old_rel,
                "new_rel": e.new_rel,
                "set_id": e.set_id,
                "order": e.order,
            }
            for e in rename_map.entries
        ],
        "unmapped_plan_duplicates": [
            {"set_id": pair[0], "order": pair[1], "paths": list(paths)}
            for pair, paths in rename_map.unmapped_plan_duplicates
        ],
    }
    tx_data["steps"]["citations"] = {
        "total_substituted": citation_plan.total_substituted,
        "location_counts": dict(citation_plan.location_counts),
        "unchanged_counts_by_reason": dict(citation_plan.unchanged_counts_by_reason),
        "unchanged_occurrences": [
            {
                "file": u.file,
                "line": u.line,
                "reason": u.reason,
                "token": u.token,
            }
            for u in citation_plan.unchanged_occurrences
        ],
        "warnings": list(citation_plan.warnings),
        "warning_count": len(citation_plan.warnings),
    }

    # Step 6a (pre-conversion census): check field destinations, unknown-field,
    # and unparseable-value refusals before step 4 builds logs.
    census = m0001_verify.build_field_census(
        repo_path,
        pre_conversion_records_root=scratch_dir / "records",
        converted_records_root=scratch_dir / "records",
        sidecar_summary=tx_data["steps"]["sidecar"],
        orphan_counts=orphan_counts,
        rename_summary=tx_data["steps"]["renames"],
        citation_summary=tx_data["steps"]["citations"],
        layout_stage_summary=layout_stage_report,
    )
    if census.get("refusals"):
        tx_data["steps"]["census"] = census
        round_trip_skipped: Dict[str, Any] = {
            "passed": False,
            "round_trip_passed": False,
            "replayed_count": 0,
            "review_mirrors_checked": 0,
            "legacy_filename_leftovers": [],
            "set_order_collisions": [],
            "errors": ["Round-trip verification skipped due to census refusals"],
            "leak_fail_count": 0,
            "leak_warn_count": 0,
            "leak_fails": [],
            "leak_warns": [],
        }
        tx_data["steps"]["round_trip"] = round_trip_skipped
        mgr._save_transaction(tx_data)
        if clear_stale_progress:
            (journal_dir / _OPS_PROGRESS_FILENAME).unlink(missing_ok=True)
        if not apply:
            return _format_run_report(tx_data, journal_dir, applied=False)
        m0001_verify.ensure_apply_gates_pass(census, round_trip_skipped)

    # Description generation / lookup (4sd62s 5.2 step 0, 4.2, 5.2a) over ONLY
    # m0001_discover-classified convertible records, keyed by id6 or pre-rename
    # resolved-records-root-relative path when m0001 mints id6.
    eff_describer = m0001_describe.Describer() if describer is None else describer
    deliberate_absences: Dict[str, str] = {}
    if isinstance(eff_describer, m0001_describe.Describer):
        pre_step3_root = scratch_dir / "records"
        inv_pre = m0001_discover.discover(scratch_repo, records_root=pre_step3_root)
        minted_by_old_rel = {e.old_rel: e.id6 for e in rename_map.entries if e.minted}
        rename_by_old_rel = {e.old_rel: e.new_rel for e in rename_map.entries}
        describe_targets: List[m0001_describe.DescribeTarget] = []
        for rec in sorted(inv_pre.records, key=lambda r: r.rel_path):
            is_minted = (
                rec.needs_mint
                or (rec.rel_path in minted_by_old_rel)
                or (not rec.identity)
            )
            desc_key = rec.rel_path if is_minted else str(rec.identity)
            final_id6 = minted_by_old_rel.get(rec.rel_path) or rec.identity or ""
            new_rel = rename_by_old_rel.get(rec.rel_path) or rec.rel_path
            describe_targets.append(
                m0001_describe.DescribeTarget(
                    key=desc_key,
                    rel_path=rec.rel_path,
                    record_bytes=rec.path.read_bytes(),
                    id6=final_id6,
                    new_rel=new_rel,
                )
            )
        desc_res = m0001_describe.describe_all(
            describe_targets,
            repo=repo_path,
            journal_dir=journal_dir,
            describer=eff_describer,
        )
        if eff_describer.enabled:
            merged_descs = dict(tx_data.get("descriptions") or {})
            merged_descs.update(desc_res.descriptions)
            for tgt in describe_targets:
                if tgt.key in desc_res.deliberate_absences:
                    merged_descs.pop(tgt.key, None)
        else:
            merged_descs = {}
        tx_data["descriptions"] = merged_descs
        tx_data["steps"]["descriptions"] = desc_res.to_dict()
        for tgt in describe_targets:
            if tgt.key in desc_res.deliberate_absences:
                reason = desc_res.deliberate_absences[tgt.key]
                deliberate_absences[tgt.key] = reason
                deliberate_absences[tgt.rel_path] = reason
                if tgt.id6:
                    deliberate_absences[tgt.id6] = reason
                if tgt.new_rel:
                    deliberate_absences[tgt.new_rel] = reason
        convert_describer: Optional[Any] = None
        convert_descriptions: Optional[Mapping[str, Any]] = merged_descs
    else:
        convert_describer = eff_describer
        convert_descriptions = tx_data.get("descriptions")

    # Step 4: build event logs and rewrite record mirrors/bodies in scratch.
    convert_summary = m0001_convert.convert_records(
        scratch_repo,
        records_root=scratch_repo / ".aw" / "records",
        pre_step3_records_root=scratch_dir / "records",
        repo_root=repo_path,
        rename_map=tx_data["rename_map"],
        sidecar_events=sidecar_events,
        describer=convert_describer,
        descriptions=convert_descriptions,
        record_types=m0001_convert.ALL_RECORD_TYPES,
        include_reviews=True,
    )
    tx_data["steps"]["conversion"] = convert_summary

    # Step 5: cleanup STATUS.md, INDEX manifests, and INDEX ignore lines in scratch.
    cleanup_summary = _step_5_cleanup(
        repo_path,
        scratch=True,
        apply=False,
        records_root=records_root,
        journal_dir=journal_dir,
    )
    tx_data["steps"]["cleanup"] = cleanup_summary

    # Step 6b (post-conversion): update description counts from logs, run round-trip & leak scan.
    m0001_verify.populate_description_counts(
        census,
        scratch_repo / ".aw" / "records",
        deliberate_description_absences=deliberate_absences,
    )
    round_trip = m0001_verify.verify_round_trip(
        repo_path,
        pre_conversion_records_root=scratch_dir / "records",
        converted_records_root=scratch_repo / ".aw" / "records",
        post_step3_records_root=post_step3_dir if post_step3_dir.is_dir() else None,
        rename_map=tx_data["rename_map"],
        sidecar_events=sidecar_events,
        unmapped_plan_duplicates=rename_map.unmapped_plan_duplicates,
    )
    tx_data["steps"]["census"] = census
    tx_data["steps"]["round_trip"] = round_trip

    operations: List[Dict[str, Any]] = []
    if sidecar_present:
        operations.append(
            {
                "op_id": "move_sidecar",
                "kind": "move_to_journal",
                "src": str(sidecar_path),
                "dst": str(journal_dir / "history.jsonl.imported"),
            }
        )
    gitignore_rewritten = ".aw/.gitignore" in set(
        step3_summary.get("rewritten_files") or []
    )
    aw_gi_src = repo_path / ".aw" / ".gitignore"
    aw_gi_scratch = scratch_repo / ".aw" / ".gitignore"
    aw_gi_step5_changed = (
        aw_gi_src.is_file()
        and aw_gi_scratch.is_file()
        and aw_gi_scratch.read_text(encoding="utf-8")
        != aw_gi_src.read_text(encoding="utf-8")
    )
    if (
        gitignore_changed or gitignore_rewritten or aw_gi_step5_changed
    ) and gitignore_rel is not None:
        operations.append(
            {
                "op_id": "clean_gitignore",
                "kind": "write_from_scratch",
                "target": str(aw_gi_src),
                "scratch_rel": gitignore_rel,
            }
        )

    agents_gi_src = repo_path / ".agents" / ".gitignore"
    agents_gi_scratch = scratch_repo / ".agents" / ".gitignore"
    if (
        agents_gi_src.is_file()
        and agents_gi_scratch.is_file()
        and agents_gi_scratch.read_text(encoding="utf-8")
        != agents_gi_src.read_text(encoding="utf-8")
    ):
        operations.append(
            {
                "op_id": "clean_agents_gitignore",
                "kind": "write_from_scratch",
                "target": str(agents_gi_src),
                "scratch_rel": "repo/.agents/.gitignore",
            }
        )

    step5_status_targets, step5_index_targets, _ = _step5_target_paths(
        repo_path, records_root
    )
    for idx_num, target in enumerate([*step5_status_targets, *step5_index_targets]):
        operations.append(
            {
                "op_id": f"delete_step5:{idx_num}:{target.name}",
                "kind": "delete_file",
                "target": str(target),
            }
        )

    renamed_old_rel_set = {f".aw/records/{e.old_rel}" for e in rename_map.entries}
    planned_record_rels: Set[str] = set()
    for rel_from_scratch in step3_summary.get("rewritten_files") or []:
        if rel_from_scratch == ".aw/.gitignore":
            continue
        if rel_from_scratch in renamed_old_rel_set:
            continue
        if rel_from_scratch.startswith(".aw/records/"):
            rec_tail = rel_from_scratch[len(".aw/records/") :]
            planned_record_rels.add(rec_tail)
            target_path = records_root / rec_tail
        else:
            target_path = repo_path / rel_from_scratch
        operations.append(
            {
                "op_id": f"rewrite:{rel_from_scratch}",
                "kind": "write_from_scratch",
                "target": str(target_path),
                "scratch_rel": f"repo/{rel_from_scratch}",
            }
        )

    for entry in rename_map.entries:
        planned_record_rels.add(entry.new_rel)
        operations.append(
            {
                "op_id": f"rename_rm:{entry.old_rel}",
                "kind": "move_to_journal",
                "src": str(records_root / entry.old_rel),
                "dst": str(journal_dir / "renamed-originals" / entry.old_rel),
            }
        )
        operations.append(
            {
                "op_id": f"rename_add:{entry.new_rel}",
                "kind": "write_from_scratch",
                "target": str(records_root / entry.new_rel),
                "scratch_rel": f"repo/.aw/records/{entry.new_rel}",
            }
        )

    for rec_tail in convert_summary.get("rewritten_files") or []:
        if rec_tail in planned_record_rels:
            continue
        planned_record_rels.add(rec_tail)
        operations.append(
            {
                "op_id": f"convert_md:{rec_tail}",
                "kind": "write_from_scratch",
                "target": str(records_root / rec_tail),
                "scratch_rel": f"repo/.aw/records/{rec_tail}",
            }
        )

    for log_rel in convert_summary.get("log_files") or []:
        operations.append(
            {
                "op_id": f"write_log:{log_rel}",
                "kind": "write_from_scratch",
                "target": str(records_root / log_rel),
                "scratch_rel": f"repo/.aw/records/{log_rel}",
            }
        )

    tx_data["operations"] = operations
    mgr._save_transaction(tx_data)
    if clear_stale_progress:
        (journal_dir / _OPS_PROGRESS_FILENAME).unlink(missing_ok=True)

    if not apply:
        return _format_run_report(tx_data, journal_dir, applied=False)

    m0001_verify.ensure_apply_gates_pass(census, round_trip)
    tx_data["status"] = "applying"
    mgr._save_transaction(tx_data)

    _execute_planned_operations(
        mgr,
        tx_data,
        journal_dir,
        repo_path=repo_path,
        records_root=records_root,
        fault_injection=fault_injection,
    )
    tx_data = _finish_apply_after_ops(
        repo_path,
        mgr,
        tx_data,
        journal_dir,
        records_root=records_root,
        commit=commit,
    )
    return _format_run_report(tx_data, journal_dir, applied=True)


def _resume_applying_journal(
    repo_path: Path,
    journal_dir: Path,
    records_root: Path,
    *,
    force: bool = False,
    force_worktree: bool = False,
    describer: Optional[Any] = None,
    fault_injection: Optional[str] = None,
    commit: bool = True,
    include_paths: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Resume an interrupted ``status == 'applying'`` run from stage one or ``journal_dir / 'scratch'``.

    ``include_paths`` of ``None`` keeps the list the interrupted run journaled; a list replaces it.
    """
    preflight = m0001_preflight.check_preflight(
        repo_path,
        records_root=records_root,
        force=force,
        force_worktree=force_worktree,
        skip_uncommitted=True,
    )
    mgr = _make_rebound_manager(repo_path, journal_dir)
    existing = _load_journal_with_progress(mgr, journal_dir)
    if not existing or existing.get("status") != "applying":
        raise layout_migration.MigrationError(
            f"No applying m0001 migration journal found at {mgr.transaction_file}"
        )
    tx_id = str(existing.get("transaction_id") or f"m0001-resume-{os.getpid()}")

    with m0001_preflight.acquire_apply_integration_lock(
        repo_path,
        apply=True,
        lock_overridden=bool(preflight.get("lock_overridden")),
        force=force,
    ):
        mgr._acquire_lock(tx_id)
        try:
            tx_data = _load_journal_with_progress(mgr, journal_dir)
            if not tx_data or tx_data.get("status") != "applying":
                raise layout_migration.MigrationError(
                    f"Journal at {mgr.transaction_file} is no longer in 'applying' state."
                )
            if include_paths is not None:
                tx_data["include_paths"] = list(include_paths)
                mgr._save_transaction(tx_data)
            ls = tx_data.get("layout_stage")
            stage1_interrupted = isinstance(ls, dict) and ls.get("status") not in (
                None,
                "skipped",
                "planned",
                "completed",
                "rolled_back",
            )
            eff_records = (
                Path(tx_data["records_root"])
                if tx_data.get("records_root")
                else records_root
            )
            try:
                if stage1_interrupted:
                    mgr.resume_embedded_stage_one(
                        tx_data, backfill_ids=False, caller_holds_lock=True
                    )
                    eff_records = project_context.project_records_dir(repo_path)
                    stage1_paths = mgr.commit_paths(tx_data.get("layout_stage"))
                    extra = list(tx_data.get("extra_stage_paths") or [])
                    for sp in stage1_paths:
                        if sp not in extra:
                            extra.append(sp)
                    tx_data["extra_stage_paths"] = extra
                    sidecar_path = record_history.history_path(repo_path)
                    sidecar_present = sidecar_path.is_file()
                    sidecar_records = (
                        _read_sidecar_records(sidecar_path) if sidecar_present else []
                    )
                    sidecar_summary = dict(
                        (tx_data.get("steps") or {}).get("sidecar") or {}
                    )
                    stage1_report = _build_stage1_report_summary(
                        needed=True, stage1_applied=tx_data.get("layout_stage")
                    )
                    report = _plan_and_apply_stage2_locked(
                        repo_path,
                        mgr,
                        tx_data,
                        journal_dir,
                        eff_records,
                        apply=True,
                        describer=describer,
                        fault_injection=fault_injection,
                        commit=commit,
                        sidecar_path=sidecar_path,
                        sidecar_present=sidecar_present,
                        sidecar_records=sidecar_records,
                        sidecar_summary=sidecar_summary,
                        layout_stage_report=stage1_report,
                    )
                    report["resumed"] = True
                    return report

                _execute_planned_operations(
                    mgr,
                    tx_data,
                    journal_dir,
                    repo_path=repo_path,
                    records_root=eff_records,
                    fault_injection=fault_injection,
                )
                tx_data = _finish_apply_after_ops(
                    repo_path,
                    mgr,
                    tx_data,
                    journal_dir,
                    records_root=eff_records,
                    commit=commit,
                )
                return _format_run_report(
                    tx_data, journal_dir, applied=True, resumed=True
                )
            except Exception as exc:
                if (
                    fault_injection == "interrupt-mid-apply"
                    and isinstance(exc, layout_migration.MigrationError)
                    and "interrupt-mid-apply" in str(exc)
                ):
                    raise
                _rollback_all_locked(
                    repo_path,
                    mgr,
                    _load_journal_with_progress(mgr, journal_dir) or tx_data,
                    journal_dir,
                    records_root=eff_records,
                )
                if isinstance(exc, layout_migration.PreflightGateError):
                    raise
                if isinstance(exc, layout_migration.MigrationError):
                    raise layout_migration.MigrationError(
                        f"{exc} (rolled back)"
                    ) from exc
                raise layout_migration.MigrationError(f"{exc} (rolled back)") from exc
        finally:
            mgr._release_lock()


def run(
    repo: Union[str, Path],
    *,
    apply: bool = False,
    force: bool = False,
    force_worktree: bool = False,
    describer: Optional[Any] = None,
    fault_injection: Optional[str] = None,
    commit: bool = True,
    include_paths: Optional[Sequence[Union[str, Path]]] = None,
) -> Dict[str, Any]:
    """Execute (or dry-run when ``apply=False``) migration m0001 against ``repo``.

    ``include_paths`` (spec 4sd62s 5.2 step 7) names extra repository files that the one
    migration commit also carries. They are validated in both modes but staged only under
    ``apply=True``, before the step-4a marker captures ``git write-tree``.
    """
    repo_path = Path(repo)
    eff_describer = m0001_describe.Describer() if describer is None else describer
    if isinstance(eff_describer, m0001_describe.Describer) and (
        eff_describer.enabled or eff_describer.host != "oc"
    ):
        eff_describer.validate_host(repo_path)

    schema_ver = chain.read_metadata_schema(repo_path)
    if schema_ver is not None and schema_ver >= 2:
        return {
            "migration_id": "m0001",
            "status": "already_migrated",
            "message": "metadata_schema is 2; nothing to do",
            "metadata_schema": schema_ver,
            "applied": False,
            "dry_run": not apply,
            "resumed": False,
            "applied_files": [],
            "staged_paths": [],
        }

    journal_dir, records_root = _journal_dir_for(repo_path)
    included = normalize_include_paths(
        repo_path, include_paths, records_root=records_root
    )

    existing_peek = _peek_journal(journal_dir)
    if (
        apply
        and existing_peek is not None
        and existing_peek.get("status") == "applying"
    ):
        return _resume_applying_journal(
            repo_path,
            journal_dir,
            records_root,
            force=force,
            force_worktree=force_worktree,
            describer=eff_describer,
            fault_injection=fault_injection,
            commit=commit,
            include_paths=included if include_paths is not None else None,
        )

    # Step 1: preflight (writes nothing on refusal).
    preflight = m0001_preflight.check_preflight(
        repo_path,
        records_root=records_root,
        force=force,
        force_worktree=force_worktree,
    )

    # Step 2 (pre-journal gate): discovery + sidecar expectedness check (writes nothing on refusal).
    inv = m0001_discover.discover(repo_path)
    sidecar_path = inv.sidecar_path
    sidecar_present = inv.sidecar_present
    sidecar_expected = inv.sidecar_expected
    if sidecar_present:
        sidecar_records = _read_sidecar_records(sidecar_path)
        sidecar_status = f"present ({len(sidecar_records)} records)"
    else:
        sidecar_records = []
        if sidecar_expected:
            if not force:
                raise layout_migration.PreflightGateError(
                    f"SIDECAR: expected history sidecar missing at {sidecar_path}; "
                    "pass --force to override if the sidecar is genuinely lost."
                )
            sidecar_status = "missing expected sidecar (overridden by --force)"
            consequence = (
                "History sidecar is missing and overridden with --force; "
                "sidecar-only history records cannot be imported."
            )
            preflight["overridden"].append(
                {
                    "condition": "SIDECAR",
                    "detail": f"Missing expected sidecar at {sidecar_path}",
                    "consequence": consequence,
                }
            )
            preflight["warnings"].append(
                f"SIDECAR override (--force): {sidecar_path} missing. {consequence}"
            )
        else:
            sidecar_status = "no sidecar (none expected)"

    # Refusals cleared; ensure .aw/state/ is gitignored before touching journal_dir.
    _ensure_state_gitignored_via_exclude(repo_path, journal_dir, apply=apply)
    mgr = _make_rebound_manager(repo_path, journal_dir)
    tx_id = f"m0001-{int(time.time())}-{os.getpid()}"

    with m0001_preflight.acquire_apply_integration_lock(
        repo_path,
        apply=apply,
        lock_overridden=bool(preflight.get("lock_overridden")),
        force=force,
    ):
        mgr._acquire_lock(tx_id)
        try:
            prior_tx = mgr._load_transaction() or {}
            can_clear_stale_progress = prior_tx.get("status") != "applying"
            now_utc = _utc_now()
            sidecar_base: Dict[str, Any] = {
                "present": sidecar_present,
                "expected": sidecar_expected,
                "expected_reason": inv.sidecar_expected_reason,
                "status": sidecar_status,
                "record_count": len(sidecar_records),
            }

            tx_data: Dict[str, Any] = {
                "schema_version": mgr.SCHEMA_VERSION,
                "migration_id": "m0001",
                "transaction_id": tx_id,
                "status": "dry_run",
                "timestamps": {"started_at": now_utc, "updated_at": now_utc},
                "records_root": str(records_root),
                "minted_ids": dict(prior_tx.get("minted_ids") or {}),
                "rename_map": {},
                "steps": {
                    "preflight": preflight,
                    "sidecar": dict(sidecar_base),
                },
                "applied_files": [],
                "backups": [],
                "operations": [],
                "extra_stage_paths": [],
                "include_paths": list(included),
                "descriptions": dict(prior_tx.get("descriptions") or {}),
                "sidecar_events": {},
                "orphan_export_path": None,
                "orphan_counts": {},
                "terminal_commit_marker": None,
                "layout_stage": {"status": "skipped", "reason": "already on .aw/"},
            }

            stage1_plan: Optional[Dict[str, Any]] = None
            stage1_mgr: Optional[layout_migration.MigrationManager] = None
            eff_records = records_root

            if inv.layout_stage_needed:
                stage1_plan = mgr.plan_embedded_stage_one()
                layout_migration.MigrationManager._validate_stage_one_plan(stage1_plan)
                if not apply:
                    stage1_mgr = mgr
                    layout_stage_report = _build_stage1_report_summary(
                        needed=True, stage1_plan=stage1_plan
                    )
                    tx_data["layout_stage"] = dict(layout_stage_report)
                else:
                    tx_data["status"] = "applying"
                    mgr._save_transaction(tx_data)
                    if can_clear_stale_progress:
                        (journal_dir / _OPS_PROGRESS_FILENAME).unlink(missing_ok=True)
                    try:
                        ls_done = mgr.apply_embedded_stage_one(
                            tx_data,
                            stage1_plan,
                            backfill_ids=False,
                            leftover_disposition="defer",
                            caller_holds_lock=True,
                        )
                        eff_records = project_context.project_records_dir(repo_path)
                        stage1_paths = mgr.commit_paths(ls_done)
                        tx_data["extra_stage_paths"] = list(stage1_paths)
                        layout_stage_report = _build_stage1_report_summary(
                            needed=True, stage1_applied=ls_done
                        )
                    except Exception as exc:
                        _rollback_all_locked(
                            repo_path,
                            mgr,
                            _load_journal_with_progress(mgr, journal_dir) or tx_data,
                            journal_dir,
                            records_root=eff_records,
                        )
                        if isinstance(exc, layout_migration.MigrationError):
                            raise
                        raise layout_migration.MigrationError(
                            f"Embedded stage-one layout migration failed (rolled back): {exc}"
                        ) from exc
            else:
                layout_stage_report = _build_stage1_report_summary(needed=False)
                tx_data["layout_stage"] = dict(layout_stage_report)

            try:
                return _plan_and_apply_stage2_locked(
                    repo_path,
                    mgr,
                    tx_data,
                    journal_dir,
                    eff_records,
                    apply=apply,
                    describer=eff_describer,
                    fault_injection=fault_injection,
                    commit=commit,
                    sidecar_path=sidecar_path,
                    sidecar_present=sidecar_present,
                    sidecar_records=sidecar_records,
                    sidecar_summary=sidecar_base,
                    layout_stage_report=layout_stage_report,
                    stage1_mgr=stage1_mgr,
                    stage1_plan=stage1_plan,
                    clear_stale_progress=can_clear_stale_progress,
                )
            except Exception as exc:
                if not apply:
                    raise
                if (
                    fault_injection == "interrupt-mid-apply"
                    and isinstance(exc, layout_migration.MigrationError)
                    and "interrupt-mid-apply" in str(exc)
                ):
                    raise
                _rollback_all_locked(
                    repo_path,
                    mgr,
                    _load_journal_with_progress(mgr, journal_dir) or tx_data,
                    journal_dir,
                    records_root=eff_records,
                )
                if isinstance(exc, layout_migration.PreflightGateError):
                    raise
                if isinstance(exc, layout_migration.MigrationError):
                    raise layout_migration.MigrationError(
                        f"{exc} (rolled back)"
                    ) from exc
                raise layout_migration.MigrationError(f"{exc} (rolled back)") from exc
        finally:
            if not apply:
                scratch_dir = journal_dir / "scratch"
                if scratch_dir.exists():
                    shutil.rmtree(scratch_dir, ignore_errors=True)
            mgr._release_lock()


def resume(
    repo: Union[str, Path],
    *,
    describer: Optional[Any] = None,
    fault_injection: Optional[str] = None,
    commit: bool = True,
    include_paths: Optional[Sequence[Union[str, Path]]] = None,
) -> Dict[str, Any]:
    """Resume an interrupted m0001 migration apply from its journal and scratch dir."""
    repo_path = Path(repo)
    journal_dir, records_root = _journal_dir_for(repo_path)
    return _resume_applying_journal(
        repo_path,
        journal_dir,
        records_root,
        describer=describer,
        fault_injection=fault_injection,
        commit=commit,
        include_paths=(
            normalize_include_paths(repo_path, include_paths, records_root=records_root)
            if include_paths is not None
            else None
        ),
    )


def rollback(repo: Union[str, Path]) -> Dict[str, Any]:
    """Restore pre-apply file bytes from ``journal_dir / 'backups'`` and reverse stage one."""
    repo_path = Path(repo)
    journal_dir, records_root = _journal_dir_for(repo_path)
    mgr = _make_rebound_manager(repo_path, journal_dir)
    tx_id = f"m0001-rollback-{os.getpid()}"

    mgr._acquire_lock(tx_id)
    try:
        tx_data = _load_journal_with_progress(mgr, journal_dir)
        if tx_data is None:
            raise layout_migration.MigrationError(
                f"No m0001 migration journal found at {mgr.transaction_file}"
            )
        if tx_data.get("status") == "rolled_back":
            return {
                "migration_id": "m0001",
                "status": "rolled_back",
                "restored_count": 0,
                "already_rolled_back": True,
                "journal_path": str(mgr.transaction_file),
            }

        restored = _rollback_all_locked(
            repo_path,
            mgr,
            tx_data,
            journal_dir,
            records_root=records_root,
        )
        return {
            "migration_id": "m0001",
            "status": "rolled_back",
            "restored_count": restored,
            "already_rolled_back": False,
            "journal_path": str(mgr.transaction_file),
        }
    finally:
        mgr._release_lock()
