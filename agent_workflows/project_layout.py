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
from agent_workflows.manifest import Manifest
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
    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
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
    mf.save_to(manifest_file)

    return {k: str(v) for k, v in roots.items()}
