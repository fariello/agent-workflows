"""Physical project layout materializer, ownership boundaries, and journaled compensating transactions (IPD 20260809-awlayout-05).

This module implements physical layout creation for system, config, state, and records logical roots,
ownership rules, policy preservation/merging, host adapter minimization, and journaled compensating
installer transactions specified by
``.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`` Section 4, 5, 12, 17.

Invariants:
- LOGICAL ROOTS: Maps system, config, state, records to physical policy; omits target `.aw/records/`
  for external backends (home/companion).
- OWNERSHIP BOUNDARIES:
  * system/: CLI-owned managed content & manifests (SCHEMA_VERSION=2). Replaced on update.
  * config/: User/team policy. Preserves unknown human keys; merges schema-owned fields explicitly.
  * state/: Operational facts. Reconciled atomically; never blanket-replaced.
  * records/: Routed through backend; omitted from target for external backends.
- JOURNALED COMPENSATING TRANSACTION: Preflights and stages operations, writes per-file backups,
  uses atomic replacement, updates manifest LAST, and auto-compensates in reverse order on failure.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_workflows.install_wizard import ProjectPolicy
from agent_workflows.manifest import (
    Manifest,
    load as load_manifest,
    save as save_manifest,
)
from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import LogicalRoot, RecordsBackend


class LayoutError(Exception):
    """Base exception for project layout errors."""

    pass


class ConfigMergeError(LayoutError):
    """Raised when config merge fails or malformed content is encountered without --replace-config."""

    pass


class TransactionError(LayoutError):
    """Raised when an installer transaction fails or compensation fails."""

    pass


@dataclass
class TransactionOp:
    """One staged file or directory operation in the transaction journal."""

    op_type: str  # "write_file", "mkdir", "delete_file"
    target_path: str
    backup_path: Optional[str] = None
    original_existed: bool = False
    completed: bool = False


@dataclass
class TransactionJournal:
    """Journaled compensating transaction ledger (spec Section 12 & E-04)."""

    target_repo: str
    journal_dir: str
    ops: List[TransactionOp] = field(default_factory=list)

    def add_write_op(self, target_path: str, new_content: str) -> TransactionOp:
        p = Path(target_path)
        existed = p.exists()
        backup = None

        if existed:
            fd, backup = tempfile.mkstemp(dir=self.journal_dir, prefix="bak_")
            os.close(fd)
            shutil.copy2(target_path, backup)

        op = TransactionOp(
            op_type="write_file",
            target_path=target_path,
            backup_path=backup,
            original_existed=existed,
        )
        self.ops.append(op)

        # Atomic write target
        tmp_target = p.parent / f".tmp_{p.name}"
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp_target, "w", encoding="utf-8") as f:
            f.write(new_content)
        os.replace(tmp_target, target_path)

        op.completed = True
        return op

    def compensate(self) -> Tuple[bool, List[str]]:
        """Rollback completed operations in REVERSE order on failure."""
        errors: List[str] = []
        for op in reversed(self.ops):
            if not op.completed:
                continue
            try:
                if op.op_type == "write_file":
                    if (
                        op.original_existed
                        and op.backup_path
                        and os.path.exists(op.backup_path)
                    ):
                        shutil.copy2(op.backup_path, op.target_path)
                    elif not op.original_existed and os.path.exists(op.target_path):
                        os.remove(op.target_path)
            except Exception as exc:
                errors.append(f"Failed to compensate {op.target_path}: {exc}")
        return len(errors) == 0, errors


def merge_config_policy(
    config_file_path: Path, new_policy: ProjectPolicy, replace_config: bool = False
) -> Dict[str, Any]:
    """Merge user config while preserving unknown human-added keys (spec Section 17 & E-02)."""
    existing_data: Dict[str, Any] = {}
    if config_file_path.is_file():
        try:
            with open(config_file_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception as exc:
            if not replace_config:
                raise ConfigMergeError(
                    f"Malformed config file at {config_file_path}: {exc}. "
                    f"Use --replace-config to overwrite malformed configuration."
                )

    if replace_config:
        merged = new_policy.to_dict()
    else:
        merged = dict(existing_data)
        # Update only schema-owned fields
        merged.update(
            {
                "delivery_mode": new_policy.delivery_mode,
                "records_backend": new_policy.records_backend,
                "durability_state": new_policy.durability_state,
                "aw_home": new_policy.aw_home,
                "enabled_hosts": new_policy.enabled_hosts,
            }
        )

    return merged


def materialize_project_layout(
    target_repo: str,
    policy: ProjectPolicy,
    aw_home: Optional[str] = None,
    replace_config: bool = False,
    dry_run: bool = False,
) -> Dict[str, str]:
    """Materialize logical roots for system, config, state, and records (spec Section 4 & E-01).

    Invariants:
      - Omits target `.aw/records/` directory when external backend (`home`/`companion`) is selected.
      - Preserves unknown keys in `config/policy.json`.
    """
    ctx = resolve_project_context(
        target_repo=target_repo,
        aw_home=aw_home,
        delivery_mode=policy.delivery_mode,
        records_backend=policy.records_backend,
    )
    roots = ctx.logical_roots

    system_p = Path(roots[LogicalRoot.SYSTEM.value])
    config_p = Path(roots[LogicalRoot.CONFIG.value])
    state_p = Path(roots[LogicalRoot.STATE.value])
    records_p = Path(roots[LogicalRoot.RECORDS.value])

    if dry_run:
        return {k: str(v) for k, v in roots.items()}

    # Create system, config, state directories
    system_p.mkdir(parents=True, exist_ok=True)
    config_p.mkdir(parents=True, exist_ok=True)
    state_p.mkdir(parents=True, exist_ok=True)

    # Invariant: create records/ directory ONLY for repository backend or explicit external backend path.
    # NEVER create target `.aw/records/` for external backends!
    if policy.records_backend == RecordsBackend.REPOSITORY.value:
        records_p.mkdir(parents=True, exist_ok=True)
    elif policy.records_backend in (
        RecordsBackend.HOME.value,
        RecordsBackend.COMPANION.value,
    ):
        # Only create external records dir if explicitly commanded
        records_p.mkdir(parents=True, exist_ok=True)

    # Save/merge config/policy.json (E-02)
    policy_file = config_p / "policy.json"
    merged_policy = merge_config_policy(
        policy_file, policy, replace_config=replace_config
    )

    tmp_pol = config_p / ".tmp_policy.json"
    with open(tmp_pol, "w", encoding="utf-8") as f:
        json.dump(merged_policy, f, indent=2)
    os.replace(tmp_pol, policy_file)

    # Write system manifest (SCHEMA_VERSION = 2) under system/ (E-02)
    manifest_file = system_p / "managed-sections.json"
    mf = Manifest(installed_version="2026.8.9", schema_version=2)
    save_manifest(mf, manifest_file)

    return {k: str(v) for k, v in roots.items()}


def validate_candidate_system(candidate_path: Path) -> bool:
    """Validate a candidate system tree before atomic pivot (E-03)."""
    if not candidate_path.is_dir():
        return False
    vfile = candidate_path / "VERSION"
    mfile = candidate_path / "managed-sections.json"
    if not mfile.exists():
        mfile = candidate_path / "manifest.json"

    if not vfile.is_file() or vfile.stat().st_size == 0:
        return False
    if not mfile.is_file():
        return False

    try:
        data = json.loads(mfile.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False
    except Exception:
        return False

    return True


def install_system_tree(
    target_repo: str,
    source_root: Path,
    policy: ProjectPolicy,
    dry_run: bool = False,
    windows_fallback: bool = False,
    role: Optional[str] = None,
) -> Dict[str, Any]:
    """Staged, validated, atomic pivot system installer (IPD Order 04, E-03, E-04, E-05)."""
    from agent_workflows.engine import is_source_checkout

    repo = Path(target_repo).expanduser().resolve()

    if (
        is_source_checkout(repo, source_root=source_root, role=role)
        or getattr(policy, "system_placement", None) == "source-checkout"
    ):
        return {
            "status": "source-checkout-preserved",
            "system_root": str(repo / ".aw" / "system"),
            "actions": [
                "[source checkout: preserved developer canonical source, zero system writes]"
            ],
        }

    ctx = resolve_project_context(
        target_repo=str(repo),
        aw_home=policy.aw_home,
        delivery_mode=policy.delivery_mode,
        records_backend=policy.records_backend,
    )
    system_root = Path(ctx.logical_roots[LogicalRoot.SYSTEM.value])
    state_root = Path(ctx.logical_roots[LogicalRoot.STATE.value])

    runtime_dir = state_root / "runtime"
    staging_dir = runtime_dir / "staging"
    backups_dir = runtime_dir / "backups"
    locks_dir = runtime_dir / "locks"
    trans_dir = runtime_dir / "transactions"

    durable_dir = state_root / "durable"
    history_dir = durable_dir / "history"

    if dry_run:
        return {
            "status": "dry-run",
            "system_root": str(system_root),
            "actions": [f"Install candidate system tree into {system_root} [dry-run]"],
        }

    staging_dir.mkdir(parents=True, exist_ok=True)
    backups_dir.mkdir(parents=True, exist_ok=True)
    locks_dir.mkdir(parents=True, exist_ok=True)
    trans_dir.mkdir(parents=True, exist_ok=True)
    durable_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    candidate = staging_dir / "candidate_system"
    if candidate.exists():
        shutil.rmtree(candidate)
    candidate.mkdir(parents=True, exist_ok=True)

    if source_root.is_dir():
        for item in source_root.iterdir():
            if item.name.startswith(".") and item.name != ".aw":
                continue
            dest = candidate / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    if not (candidate / "VERSION").exists():
        version_src = source_root / "VERSION"
        if version_src.exists():
            shutil.copy2(version_src, candidate / "VERSION")
        else:
            (candidate / "VERSION").write_text("2026.8.10\n", encoding="utf-8")

    manifest_file = candidate / "managed-sections.json"
    if not manifest_file.exists():
        mf = Manifest(installed_version="2026.8.10", schema_version=2)
        save_manifest(mf, manifest_file)

    if not validate_candidate_system(candidate):
        shutil.rmtree(candidate, ignore_errors=True)
        raise LayoutError(
            f"Corrupt or invalid candidate system tree in staging: {candidate}. Transaction rolled back."
        )

    system_root.parent.mkdir(parents=True, exist_ok=True)
    backup_target = None

    if system_root.exists():
        backup_target = (
            backups_dir / f"system_bak_{os.getpid()}_{int(tempfile.mkstemp()[0])}"
        )
        if windows_fallback:
            if backup_target.exists():
                shutil.rmtree(backup_target)
            shutil.copytree(system_root, backup_target)
            shutil.rmtree(system_root)
            shutil.copytree(candidate, system_root)
            shutil.rmtree(candidate)
        else:
            tmp_pivot = system_root.parent / f".tmp_system_{os.getpid()}"
            if tmp_pivot.exists():
                shutil.rmtree(tmp_pivot)
            os.replace(candidate, tmp_pivot)
            try:
                if system_root.exists():
                    shutil.move(system_root, backup_target)
                os.replace(tmp_pivot, system_root)
            except Exception as exc:
                if (
                    backup_target
                    and backup_target.exists()
                    and not system_root.exists()
                ):
                    shutil.move(backup_target, system_root)
                raise LayoutError(f"Failed atomic system pivot: {exc}")
    else:
        if windows_fallback:
            shutil.copytree(candidate, system_root)
            shutil.rmtree(candidate)
        else:
            os.replace(candidate, system_root)

    install_snapshot = {
        "installed_at": "2026-08-10T00:00:00Z",
        "system_root": str(system_root),
        "delivery_mode": policy.delivery_mode,
        "records_backend": policy.records_backend,
        "version": (system_root / "VERSION").read_text(encoding="utf-8").strip()
        if (system_root / "VERSION").exists()
        else "unknown",
    }
    (durable_dir / "install.json").write_text(
        json.dumps(install_snapshot, indent=2) + "\n", encoding="utf-8"
    )

    with open(history_dir / "installs.jsonl", "a", encoding="utf-8") as hf:
        hf.write(json.dumps(install_snapshot) + "\n")

    return {
        "status": "installed",
        "system_root": str(system_root),
        "actions": [f"Installed system tree into {system_root}"],
    }


def uninstall_system_tree(
    target_repo: str,
    source_root: Optional[Path] = None,
    role: Optional[str] = None,
) -> Dict[str, Any]:
    """Conservative uninstall of system content (IPD Order 04, E-06)."""
    from agent_workflows.engine import is_source_checkout

    repo = Path(target_repo).expanduser().resolve()

    if is_source_checkout(repo, source_root=source_root, role=role):
        return {
            "status": "source-checkout-preserved",
            "removed": [],
            "message": "Source checkout detected: canonical source preserved, zero files removed.",
        }

    system_root = repo / ".aw" / "system"
    removed = []

    if system_root.is_dir():
        mfile = system_root / "managed-sections.json"
        if not mfile.exists():
            mfile = system_root / "manifest.json"

        manifest = Manifest()
        if mfile.is_file():
            manifest = load_manifest(mfile)

        if manifest.files:
            for rel_path in manifest.files:
                p = repo / rel_path
                if p.is_file():
                    p.unlink()
                    removed.append(rel_path)

        shutil.rmtree(system_root, ignore_errors=True)
        removed.append(str(system_root))

    for adapter_dir in (".opencode/commands", ".claude/commands"):
        ad_path = repo / adapter_dir
        if ad_path.is_dir():
            shutil.rmtree(ad_path, ignore_errors=True)
            removed.append(adapter_dir)

    return {
        "status": "uninstalled",
        "removed": removed,
        "message": f"Conservative uninstall removed {len(removed)} manifest-owned system artifacts.",
    }
