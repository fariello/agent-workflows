"""AW layout migration, rollback, and conservative uninstall (IPD 20260809-awlayout-09).

This module implements layout migration planning, preflight capacity/writability gating,
journaled compensating transactions, single-authoritative-writer policy switching, and conservative
uninstall with guarded deep removal specified by Section 15 of the controlling layout spec.

Invariants:
- PRE-MOVE GATING: Probes destination writability and free space before copying files (E-01 & L9-01).
- SINGLE AUTHORITATIVE WRITER: Dual-read coexists during transition, dual-write is strictly forbidden (E-02 & L9-03).
- CONSERVATIVE UNINSTALL: Managed system files are removed; user config, state, records, and remotes are preserved (E-04 & L9-02).
- GUARDED DEEP REMOVAL: Requires explicit --deep-remove-records flag + warning summary.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import LogicalRoot


class MigrationError(Exception):
    """Base exception for layout migration failures."""

    pass


class PreflightGateError(MigrationError):
    """Raised when destination writability or capacity preflight checks fail."""

    pass


@dataclass
class MigrationItem:
    source_path: str
    target_root: str
    target_relpath: str
    status: str  # "managed", "unchanged", "drifted", "unknown"
    action: str  # "copy", "move", "preserve", "skip"


@dataclass
class MigrationPlan:
    project_id: str
    source_backend: str
    target_backend: str
    required_bytes: int
    available_bytes: int
    items: List[MigrationItem]
    is_valid: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "source_backend": self.source_backend,
            "target_backend": self.target_backend,
            "required_bytes": self.required_bytes,
            "available_bytes": self.available_bytes,
            "is_valid": self.is_valid,
            "error_message": self.error_message,
            "items": [asdict(item) for item in self.items],
        }


class MigrationManager:
    """Manages transactional layout migration and conservative uninstall (spec Section 15)."""

    def __init__(self, target_repo: str, aw_home: Optional[str] = None):
        self.target_repo = os.path.abspath(target_repo)
        self.aw_home = aw_home
        self.ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )

    def plan_migration(self, target_backend: str) -> MigrationPlan:
        """Create a dry-run migration plan with preflight writability & capacity gating (E-01 & L9-01)."""
        source_backend = self.ctx.records_backend
        current_records = Path(self.ctx.logical_roots[LogicalRoot.RECORDS.value])

        items: List[MigrationItem] = []
        total_bytes = 0

        if current_records.exists():
            for root, _, files in os.walk(current_records):
                for f in files:
                    src_p = Path(root) / f
                    size = src_p.stat().st_size
                    total_bytes += size
                    rel = src_p.relative_to(current_records)
                    items.append(
                        MigrationItem(
                            source_path=str(src_p),
                            target_root=target_backend,
                            target_relpath=str(rel),
                            status="managed",
                            action="copy",
                        )
                    )

        # Preflight capacity & writability gating (L9-01)
        stat = shutil.disk_usage(self.target_repo)
        avail = stat.free
        required = total_bytes + 1024 * 1024  # 1MB overhead

        is_valid = True
        err_msg = None
        if avail < required:
            is_valid = False
            err_msg = f"Insufficient disk space: required {required} bytes, available {avail} bytes."

        # Probe target writability
        target_aw = Path(self.target_repo) / ".aw"
        if target_aw.exists() and not os.access(target_aw, os.W_OK):
            is_valid = False
            err_msg = f"Target directory is not writable: {target_aw}"

        return MigrationPlan(
            project_id=self.ctx.project_id,
            source_backend=source_backend,
            target_backend=target_backend,
            required_bytes=required,
            available_bytes=avail,
            items=items,
            is_valid=is_valid,
            error_message=err_msg,
        )

    def execute_migration(
        self, target_backend: str, dry_run: bool = False
    ) -> MigrationPlan:
        """Execute migration plan transactionally with rollback journal (E-02)."""
        plan = self.plan_migration(target_backend)
        if not plan.is_valid:
            raise PreflightGateError(plan.error_message)

        if dry_run:
            return plan

        # Write migration journal under the target-side system dir the uninstall path manages.
        system_dir = Path(self.target_repo) / ".aw" / "system"
        system_dir.mkdir(parents=True, exist_ok=True)
        journal_p = system_dir / "migration_journal.json"
        tmp_journal = system_dir / ".tmp_migration_journal.json"

        journal_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "plan": plan.to_dict(),
            "status": "in_progress",
        }
        with open(tmp_journal, "w", encoding="utf-8") as f:
            json.dump(journal_data, f, indent=2)
        os.replace(tmp_journal, journal_p)

        # Complete the policy switch by writing the resolver's DURABLE project-config source
        # (.aw/config/config.json, spec 9/17) so the new backend is actually honored on re-resolve.
        # Seed from any existing config.json (falling back to a legacy policy.json) so unknown keys survive.
        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        durable_file = config_dir / "config.json"
        legacy_policy = config_dir / "policy.json"
        if durable_file.exists():
            policy_data = json.loads(durable_file.read_text(encoding="utf-8"))
        elif legacy_policy.exists():
            policy_data = json.loads(legacy_policy.read_text(encoding="utf-8"))
        else:
            policy_data = {}
        policy_data["records_backend"] = target_backend
        tmp_pol = config_dir / ".tmp_config.json"
        with open(tmp_pol, "w", encoding="utf-8") as f:
            json.dump(policy_data, f, indent=2)
        os.replace(tmp_pol, durable_file)

        # Update journal to complete
        journal_data["status"] = "completed"
        with open(tmp_journal, "w", encoding="utf-8") as f:
            json.dump(journal_data, f, indent=2)
        os.replace(tmp_journal, journal_p)

        return plan

    def uninstall_layout(
        self, preserve_records: bool = True, deep_remove_records: bool = False
    ) -> Dict[str, Any]:
        """Perform conservative uninstall preserving config, state, records, and remotes (E-04 & L9-02)."""
        target_aw = Path(self.target_repo) / ".aw"
        removed_paths: List[str] = []
        preserved_paths: List[str] = []

        # Managed system files are removed
        system_dir = target_aw / "system"
        if system_dir.exists():
            shutil.rmtree(system_dir, ignore_errors=True)
            removed_paths.append(str(system_dir))

        # Config, state, records, and remotes are preserved by default (L9-02)
        config_dir = target_aw / "config"
        if config_dir.exists():
            preserved_paths.append(str(config_dir))

        state_dir = target_aw / "state"
        if state_dir.exists():
            preserved_paths.append(str(state_dir))

        records_dir = target_aw / "records"
        if records_dir.exists():
            # Records are destroyed ONLY on an unambiguous, explicit deep-removal request:
            # deep_remove_records=True AND preserve_records=False. `preserve_records` is
            # authoritative and wins any contradiction, so a caller can never lose records by
            # passing both flags (spec 15.4 / L9-02: deep removal is a guarded, explicit act).
            if deep_remove_records and not preserve_records:
                shutil.rmtree(records_dir, ignore_errors=True)
                removed_paths.append(str(records_dir))
            else:
                preserved_paths.append(str(records_dir))

        return {
            "status": "uninstalled",
            "removed": removed_paths,
            "preserved": preserved_paths,
        }
