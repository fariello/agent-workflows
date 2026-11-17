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
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from agent_workflows import (
    artifact_core,
    artifact_meta,
    artifact_naming,
    git_commit_helper,
    layout_migration,
    project_context,
    record_history,
)
from agent_workflows.migrations import (
    chain,
    m0001_convert,
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


def _peek_journal(journal_dir: Path) -> Optional[Dict[str, Any]]:
    """Read ``journal.json`` without creating directories or locks, or return None."""
    tx_path = journal_dir / "journal.json"
    if not tx_path.is_file():
        return None
    try:
        data = json.loads(tx_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


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
)


def _stage_scratch(
    repo_path: Path,
    records_root: Path,
    scratch_dir: Path,
    *,
    scan_roots: Optional[Sequence[str]] = None,
) -> Tuple[Optional[str], bool]:
    """Populate ``scratch_dir`` cleanly and return ``(gitignore_scratch_rel, gitignore_changed)``."""
    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    scratch_dir.mkdir(parents=True, exist_ok=True)

    if records_root.is_dir():
        shutil.copytree(records_root, scratch_dir / "records", symlinks=False)

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
        return rel, changed

    agents_gi = repo_path / ".agents" / ".gitignore"
    if agents_gi.is_file():
        agents_dst = scratch_dir / "repo/.agents/.gitignore"
        agents_dst.parent.mkdir(parents=True, exist_ok=True)
        agents_dst.write_text(agents_gi.read_text(encoding="utf-8"), encoding="utf-8")

    return None, False


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


def _save_backup_bytes(
    backups_dir: Path, op_id: str, target_path: Path
) -> Tuple[bool, Optional[str]]:
    """Save pre-apply bytes of ``target_path`` under ``backups_dir``."""
    backups_dir.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        return False, None
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", op_id) + ".bak"
    backup_path = backups_dir / safe_name
    backup_path.write_bytes(target_path.read_bytes())
    return True, safe_name


def _write_bytes_atomic(target: Path, data: bytes) -> None:
    """Atomically write ``data`` to ``target`` via a sibling temp file."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.parent / f".aw-tmp-{target.name}-{os.getpid()}"
    try:
        with open(tmp_path, "wb") as fh:
            fh.write(data)
            fh.flush()
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
    fault_injection: Optional[str] = None,
) -> None:
    """Apply remaining operations from ``journal_dir / 'scratch'``, backing up each target."""
    done_ids = {
        entry.get("op_id")
        for entry in (tx_data.get("applied_files") or [])
        if isinstance(entry, dict) and entry.get("op_id")
    }
    backups_dir = journal_dir / "backups"
    scratch_dir = journal_dir / "scratch"

    for op in tx_data.get("operations") or []:
        op_id = op["op_id"]
        if op_id in done_ids:
            continue

        kind = op["kind"]
        if kind == "move_to_journal":
            src = Path(op["src"])
            dst = Path(op["dst"])
            existed, backup_name = _save_backup_bytes(backups_dir, op_id, src)
            tx_data["backups"].append(
                {
                    "op_id": op_id,
                    "kind": "restore_moved",
                    "target": str(src),
                    "moved_to": str(dst),
                    "existed": existed,
                    "backup_file": backup_name,
                }
            )
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
            tx_data["applied_files"].append(
                {
                    "op_id": op_id,
                    "kind": kind,
                    "path": str(src),
                    "dst": str(dst),
                }
            )
        elif kind == "write_from_scratch":
            target = Path(op["target"])
            scratch_src = scratch_dir / op["scratch_rel"]
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
            _write_bytes_atomic(target, scratch_src.read_bytes())
            tx_data["applied_files"].append(
                {
                    "op_id": op_id,
                    "kind": kind,
                    "path": str(target),
                }
            )
        elif kind == "delete_file":
            target = Path(op["target"])
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
                    "kind": kind,
                    "path": str(target),
                }
            )
        else:
            raise layout_migration.MigrationError(
                f"Unknown m0001 operation kind: {kind!r}"
            )

        mgr._save_transaction(tx_data)

        if fault_injection == "interrupt-mid-apply" and tx_data["applied_files"]:
            raise layout_migration.MigrationError("Injected fault: interrupt-mid-apply")

    tx_data["status"] = "applied"
    mgr._save_transaction(tx_data)


def _collect_stageable_paths(repo_path: Path, tx_data: Dict[str, Any]) -> List[str]:
    """Collect repo-relative paths touched by migration operations that can be staged with ``git add``."""
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

    if not candidates:
        return []

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

    stageable: List[str] = []
    for rel in candidates:
        if rel in tracked_set:
            stageable.append(rel)
            continue
        disk_path = repo_path / rel
        if disk_path.exists() or disk_path.is_symlink():
            ign = subprocess.run(
                ["git", "-C", str(repo_path), "check-ignore", "-q", "--", rel],
                capture_output=True,
                check=False,
            )
            if ign.returncode != 0:
                stageable.append(rel)
    return stageable


def _stage_migration_paths(repo_path: Path, tx_data: Dict[str, Any]) -> List[str]:
    """Stage the migration's complete path list in ``repo_path`` and return staged repo-relative paths."""
    staged = _collect_stageable_paths(repo_path, tx_data)
    for i in range(0, len(staged), 200):
        batch = staged[i : i + 200]
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
        "preflight": steps.get("preflight"),
        "sidecar": steps.get("sidecar"),
        "renames": steps.get("renames"),
        "citations": steps.get("citations"),
        "conversion": steps.get("conversion"),
        "cleanup": steps.get("cleanup"),
        "census": steps.get("census"),
        "round_trip": steps.get("round_trip"),
        "commit": tx_data.get("commit_result"),
        "sidecar_events": tx_data.get("sidecar_events") or {},
        "orphan_export_path": tx_data.get("orphan_export_path"),
        "orphan_counts": tx_data.get("orphan_counts") or {},
        "applied_files": list(tx_data.get("applied_files") or []),
        "staged_paths": list(tx_data.get("staged_paths") or []),
        "minted_ids": dict(tx_data.get("minted_ids") or {}),
        "rename_map": dict(tx_data.get("rename_map") or {}),
        "terminal_commit_marker": tx_data.get("terminal_commit_marker"),
    }


def _finish_apply_after_ops(
    repo_path: Path,
    mgr: layout_migration.MigrationManager,
    tx_data: Dict[str, Any],
    journal_dir: Path,
    *,
    commit: bool,
) -> Dict[str, Any]:
    """Write ``metadata_schema: 2``, stage explicit paths, write marker, and optionally commit."""
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
    return mgr._load_transaction() or tx_data


def _resume_applying_journal(
    repo_path: Path,
    journal_dir: Path,
    records_root: Path,
    *,
    force: bool = False,
    force_worktree: bool = False,
    fault_injection: Optional[str] = None,
    commit: bool = True,
) -> Dict[str, Any]:
    """Resume an interrupted ``status == 'applying'`` run from ``journal_dir / 'scratch'``."""
    preflight = m0001_preflight.check_preflight(
        repo_path,
        records_root=records_root,
        force=force,
        force_worktree=force_worktree,
        skip_uncommitted=True,
    )
    mgr = _make_rebound_manager(repo_path, journal_dir)
    existing = mgr._load_transaction()
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
            tx_data = mgr._load_transaction()
            if not tx_data or tx_data.get("status") != "applying":
                raise layout_migration.MigrationError(
                    f"Journal at {mgr.transaction_file} is no longer in 'applying' state."
                )
            _execute_planned_operations(
                mgr, tx_data, journal_dir, fault_injection=fault_injection
            )
            tx_data = _finish_apply_after_ops(
                repo_path, mgr, tx_data, journal_dir, commit=commit
            )
            return _format_run_report(tx_data, journal_dir, applied=True, resumed=True)
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
) -> Dict[str, Any]:
    """Execute (or dry-run when ``apply=False``) migration m0001 against ``repo``."""
    repo_path = Path(repo)
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
            fault_injection=fault_injection,
            commit=commit,
        )

    # Step 1: preflight (writes nothing on refusal).
    preflight = m0001_preflight.check_preflight(
        repo_path,
        records_root=records_root,
        force=force,
        force_worktree=force_worktree,
    )

    # Step 2 (pre-journal gate): sidecar expectedness check (writes nothing on refusal).
    sidecar_path = record_history.history_path(repo_path)
    sidecar_present = sidecar_path.is_file()
    sidecar_expected = _is_sidecar_expected(records_root)
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

    # Refusals cleared; enter journaled execution.
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
            gitignore_rel, gitignore_changed = _stage_scratch(
                repo_path,
                records_root,
                scratch_dir,
                scan_roots=m0001_renames.M0001_SCAN_ROOTS,
            )
            scratch_repo = scratch_dir / "repo"
            _verify_scratch_scan_roots(
                repo_path,
                records_root,
                scratch_repo,
                m0001_renames.M0001_SCAN_ROOTS,
            )

            now_utc = _utc_now()
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
                    "sidecar": {
                        "present": sidecar_present,
                        "expected": sidecar_expected,
                        "status": sidecar_status,
                        "record_count": len(sidecar_records),
                        "queued_id6_count": len(sidecar_events),
                        "queued_event_count": sum(
                            len(v) for v in sidecar_events.values()
                        ),
                        "orphan_record_count": len(orphans),
                    },
                },
                "applied_files": [],
                "backups": [],
                "operations": [],
                "descriptions": dict(prior_tx.get("descriptions") or {}),
                "sidecar_events": sidecar_events,
                "orphan_export_path": orphan_export_path,
                "orphan_counts": orphan_counts,
                "terminal_commit_marker": None,
            }

            # Step 3: legacy-name rename map, protected citation plan, and scratch apply.
            rename_map = m0001_renames.build_rename_map(scratch_repo, tx_data)
            citation_plan = m0001_renames.plan_citation_rewrites(
                scratch_repo, rename_map
            )
            step3_summary = m0001_renames.apply_step3(
                scratch_repo,
                rename_map,
                citation_plan,
                tx_data,
                save_callback=lambda: mgr._save_transaction(tx_data),
            )
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
                "unchanged_counts_by_reason": dict(
                    citation_plan.unchanged_counts_by_reason
                ),
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
                    "errors": [
                        "Round-trip verification skipped due to census refusals"
                    ],
                    "leak_fail_count": 0,
                    "leak_warn_count": 0,
                    "leak_fails": [],
                    "leak_warns": [],
                }
                tx_data["steps"]["round_trip"] = round_trip_skipped
                mgr._save_transaction(tx_data)
                if not apply:
                    return _format_run_report(tx_data, journal_dir, applied=False)
                m0001_verify.ensure_apply_gates_pass(census, round_trip_skipped)

            # Step 4: build event logs and rewrite record mirrors/bodies in scratch.
            convert_summary = m0001_convert.convert_records(
                scratch_repo,
                records_root=scratch_repo / ".aw" / "records",
                pre_step3_records_root=scratch_dir / "records",
                repo_root=repo_path,
                rename_map=tx_data["rename_map"],
                sidecar_events=sidecar_events,
                describer=describer,
                descriptions=tx_data.get("descriptions"),
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
                census, scratch_repo / ".aw" / "records"
            )
            round_trip = m0001_verify.verify_round_trip(
                repo_path,
                pre_conversion_records_root=scratch_dir / "records",
                converted_records_root=scratch_repo / ".aw" / "records",
                post_step3_records_root=post_step3_dir
                if post_step3_dir.is_dir()
                else None,
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
            for idx_num, target in enumerate(
                [*step5_status_targets, *step5_index_targets]
            ):
                operations.append(
                    {
                        "op_id": f"delete_step5:{idx_num}:{target.name}",
                        "kind": "delete_file",
                        "target": str(target),
                    }
                )

            renamed_old_rel_set = {
                f".aw/records/{e.old_rel}" for e in rename_map.entries
            }
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

            if not apply:
                return _format_run_report(tx_data, journal_dir, applied=False)

            m0001_verify.ensure_apply_gates_pass(census, round_trip)
            tx_data["status"] = "applying"
            mgr._save_transaction(tx_data)

            _execute_planned_operations(
                mgr, tx_data, journal_dir, fault_injection=fault_injection
            )
            tx_data = _finish_apply_after_ops(
                repo_path, mgr, tx_data, journal_dir, commit=commit
            )
            return _format_run_report(tx_data, journal_dir, applied=True)
        finally:
            mgr._release_lock()


def resume(
    repo: Union[str, Path],
    *,
    fault_injection: Optional[str] = None,
    commit: bool = True,
) -> Dict[str, Any]:
    """Resume an interrupted m0001 migration apply from its journal and scratch dir."""
    repo_path = Path(repo)
    journal_dir, records_root = _journal_dir_for(repo_path)
    return _resume_applying_journal(
        repo_path,
        journal_dir,
        records_root,
        fault_injection=fault_injection,
        commit=commit,
    )


def rollback(repo: Union[str, Path]) -> Dict[str, Any]:
    """Restore pre-apply file bytes from ``journal_dir / 'backups'`` in reverse order."""
    repo_path = Path(repo)
    journal_dir, _records_root = _journal_dir_for(repo_path)
    mgr = _make_rebound_manager(repo_path, journal_dir)
    tx_id = f"m0001-rollback-{os.getpid()}"

    mgr._acquire_lock(tx_id)
    try:
        tx_data = mgr._load_transaction()
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

        _unstage_migration_paths(repo_path, tx_data.get("staged_paths") or [])
        _cleanup_marker(journal_dir, repo=repo_path)

        tx_data = mgr._load_transaction() or tx_data
        tx_data["staged_paths"] = []
        tx_data["terminal_commit_marker"] = None
        tx_data["status"] = "rolled_back"
        mgr._save_transaction(tx_data)

        return {
            "migration_id": "m0001",
            "status": "rolled_back",
            "restored_count": restored,
            "already_rolled_back": False,
            "journal_path": str(mgr.transaction_file),
        }
    finally:
        mgr._release_lock()
