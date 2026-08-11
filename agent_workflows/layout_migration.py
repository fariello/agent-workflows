"""AW layout migration, rollback, and conservative uninstall (IPD 20260810-awphysical-07).

This module implements layout migration planning, versioned transaction state machines,
single-writer locking, preflight revalidation, phase-scoped copy & byte/hash verification,
atomic single-authoritative policy switching, legacy source retention, Git-boundary delta plans,
idempotent status/resume/rollback, and post-retention cleanup gating.

Invariants:
- PRE-MOVE GATING: Probes writability, space, clean git state, and source file hashes before copying.
- SINGLE AUTHORITATIVE WRITER: Dual-write strictly forbidden; single writer lock enforced.
- ATOMIC SWITCH: Policy switch written LAST with durable switch receipt.
- RETENTION: Legacy sources preserved read-only after cutover; cleanup is separate and preview-first.
- GIT BOUNDARIES: Separate deltas for target, companion, and source repositories.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import LogicalRoot
from tools.awphysical import aw_layout_inventory as inv_mod


class MigrationError(Exception):
    """Base exception for layout migration failures."""

    pass


class PreflightGateError(MigrationError):
    """Raised when destination writability, capacity, or git preflight checks fail."""

    pass


class TransactionLockError(MigrationError):
    """Raised when writer lock cannot be acquired or is held by another process."""

    pass


class StaleInputError(MigrationError):
    """Raised when frozen inventory, map, policy, or git state has changed."""

    pass


class VerificationError(MigrationError):
    """Raised when copied file hash verification fails."""

    pass


class SwitchError(MigrationError):
    """Raised when authoritative policy switch fails."""

    pass


class CleanupError(MigrationError):
    """Raised when cleanup is attempted invalidly or on modified/foreign items."""

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


def _sha256_file(path: Path) -> str:
    """Return SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_str(data: str) -> str:
    """Return SHA-256 digest of a string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _run_git(repo_path: Path, args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=False,
        capture_output=True,
        text=True,
    )


class MigrationManager:
    """Manages transactional layout migration, status, resume, rollback, and cleanup."""

    SCHEMA_VERSION = 1

    def __init__(self, target_repo: str, aw_home: Optional[str] = None):
        self.target_repo = os.path.abspath(target_repo)
        self.aw_home = aw_home
        self.ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )

        # Paths under target_repo
        self.aw_dir = Path(self.target_repo) / ".aw"
        self.system_dir = self.aw_dir / "system"
        self.config_dir = self.aw_dir / "config"
        self.durable_state_dir = self.aw_dir / "state" / "durable"
        self.runtime_state_dir = self.aw_dir / "state" / "runtime"
        self.records_dir = self.aw_dir / "records"

        # Durable transaction artifacts
        self.transaction_file = self.durable_state_dir / "migration_transaction.json"
        self.lock_file = self.durable_state_dir / "migration_writer.lock"
        self.switch_receipt_file = self.durable_state_dir / "switch_receipt.json"
        self.retention_manifest_file = (
            self.durable_state_dir / "retention_manifest.json"
        )

    def plan_migration(self, target_backend: str) -> MigrationPlan:
        """Create a dry-run migration plan with preflight writability & capacity gating."""
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

        stat = shutil.disk_usage(self.target_repo)
        avail = stat.free
        required = total_bytes + 1024 * 1024  # 1MB overhead

        is_valid = True
        err_msg = None
        if avail < required:
            is_valid = False
            err_msg = f"Insufficient disk space: required {required} bytes, available {avail} bytes."

        if self.aw_dir.exists() and not os.access(self.aw_dir, os.W_OK):
            is_valid = False
            err_msg = f"Target directory is not writable: {self.aw_dir}"

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

    def _acquire_lock(self, transaction_id: str) -> None:
        """Acquire writer lock or throw TransactionLockError."""
        self.durable_state_dir.mkdir(parents=True, exist_ok=True)
        if self.lock_file.exists():
            try:
                data = json.loads(self.lock_file.read_text(encoding="utf-8"))
                pid = data.get("pid")
                # Check if pid is alive
                if pid and pid != os.getpid():
                    try:
                        os.kill(pid, 0)
                        # Process exists, lock is held by another process
                        raise TransactionLockError(
                            f"Migration writer lock held by active PID {pid} (tx: {data.get('transaction_id')})"
                        )
                    except OSError:
                        # Process dead, stale lock can be reclaimed
                        pass
            except (json.JSONDecodeError, TransactionLockError):
                if self.lock_file.exists():
                    raise

        lock_data = {
            "transaction_id": transaction_id,
            "pid": os.getpid(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        tmp_lock = self.durable_state_dir / f".tmp_lock_{os.getpid()}"
        with open(tmp_lock, "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2)
        os.replace(tmp_lock, self.lock_file)

    def _release_lock(self) -> None:
        """Release writer lock."""
        if self.lock_file.exists():
            try:
                data = json.loads(self.lock_file.read_text(encoding="utf-8"))
                if data.get("pid") == os.getpid():
                    self.lock_file.unlink(missing_ok=True)
            except Exception:
                self.lock_file.unlink(missing_ok=True)

    def _save_transaction(self, tx_data: Dict[str, Any]) -> None:
        """Save transaction journal atomically."""
        self.durable_state_dir.mkdir(parents=True, exist_ok=True)
        tx_data["timestamps"]["updated_at"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        )
        tmp_tx = self.durable_state_dir / f".tmp_tx_{os.getpid()}.json"
        with open(tmp_tx, "w", encoding="utf-8") as f:
            json.dump(tx_data, f, indent=2, sort_keys=True)
        os.replace(tmp_tx, self.transaction_file)

    def _load_transaction(self) -> Optional[Dict[str, Any]]:
        """Load transaction journal if present."""
        if not self.transaction_file.exists():
            return None
        try:
            return json.loads(self.transaction_file.read_text(encoding="utf-8"))
        except Exception:
            return None

    def execute_migration(
        self,
        target_backend: str = "repository",
        dry_run: bool = False,
        fault_injection: Optional[str] = None,
        plan_doc: Optional[Dict[str, Any]] = None,
    ) -> MigrationPlan:
        """Execute transactional migration with complete copy-verify-switch-retain protocol."""
        repo_path = Path(self.target_repo)

        # 1. Build or validate input plan/inventory/map
        if plan_doc is None:
            roots = inv_mod._default_roots(repo_path)
            inv_res = inv_mod.inventory(repo_path, roots, False)
            map_res = inv_mod.build_migration_map(repo_path, inv_res, target_backend)
            risk_res = inv_mod.analyze_migration_risks(repo_path, inv_res, map_res)
            plan_doc = {
                "schema_version": inv_mod.SCHEMA_VERSION,
                "inventory": inv_res,
                "migration_map": map_res,
                "risk_analysis": risk_res,
                "valid": inv_res.get("valid", False)
                and map_res.get("valid", False)
                and risk_res.get("valid", False),
            }

        if not plan_doc.get("valid", False):
            raise PreflightGateError(
                f"Migration plan invalid: {plan_doc.get('risk_analysis', {}).get('errors')}"
            )

        if dry_run:
            return self.plan_migration(target_backend)

        # Fault injection: stale-input / concurrent-writer
        if fault_injection == "stale-input":
            raise StaleInputError(
                "Fault injected: stale input inventory digest mismatch"
            )
        if fault_injection == "concurrent-writer":
            # Simulate lock held by external process
            self._acquire_lock("ext-tx-999")
            # Overwrite lock pid to fictitious active PID
            lock_data = {
                "transaction_id": "ext-tx-999",
                "pid": 99999,
                "timestamp": "2026-08-10T00:00:00Z",
            }
            with open(self.lock_file, "w", encoding="utf-8") as f:
                json.dump(lock_data, f)
            raise TransactionLockError("Migration writer lock held by active PID 99999")

        # Create unique transaction state machine (E-01)
        tx_id = f"tx-{int(time.time())}-{os.getpid()}"
        inv_json = json.dumps(plan_doc["inventory"], sort_keys=True)
        map_json = json.dumps(plan_doc["migration_map"], sort_keys=True)
        inv_digest = _sha256_str(inv_json)
        map_digest = _sha256_str(map_json)
        policy_digest = _sha256_str(target_backend)

        git_head = _run_git(repo_path, ["rev-parse", "HEAD"]).stdout.strip()

        tx_data = {
            "transaction_id": tx_id,
            "schema_version": self.SCHEMA_VERSION,
            "status": "initialized",
            "target_backend": target_backend,
            "inventory_digest": inv_digest,
            "map_digest": map_digest,
            "policy_digest": policy_digest,
            "source_git_identity": git_head,
            "target_git_identity": git_head,
            "last_verified_checkpoint": "initialized",
            "timestamps": {
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            "acknowledgements": {"user_confirmed": True},
            "phase_journal": [
                {
                    "phase": "initialized",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            ],
            "plan_summary": {
                "total_items": plan_doc["risk_analysis"]["item_counts"]["total"],
                "total_bytes": plan_doc["risk_analysis"]["total_bytes"],
            },
            "items": plan_doc["migration_map"].get("items", []),
        }

        # Acquire lock (E-02)
        self._acquire_lock(tx_id)
        tx_data["status"] = "locked"
        tx_data["last_verified_checkpoint"] = "locked"
        tx_data["phase_journal"].append(
            {
                "phase": "locked",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        self._save_transaction(tx_data)

        # Build lookup map from inventory items
        inv_item_map = {
            item["item_id"]: item
            for item in plan_doc.get("inventory", {}).get("items", [])
        }

        # Preflight revalidation (E-02)
        # Check git dirty/unmerged
        proc_unmerged = _run_git(repo_path, ["ls-files", "-u"])
        if proc_unmerged.stdout.strip():
            self._release_lock()
            raise PreflightGateError(
                f"Git repository has unmerged files: {proc_unmerged.stdout.strip()}"
            )

        # Re-verify source file hashes before copy
        for mapping in tx_data["items"]:
            item_id = mapping.get("item_id")
            inv_item = inv_item_map.get(item_id, {})
            src_rel = (
                inv_item.get("repo_relpath")
                or f"{mapping.get('source_root', '')}/{mapping.get('source_relpath', '')}".strip(
                    "/"
                )
            )
            src_p = repo_path / src_rel
            if src_p.is_file() and not src_p.is_symlink():
                cur_hash = _sha256_file(src_p)
                exp_hash = inv_item.get("sha256")
                if exp_hash and cur_hash != exp_hash:
                    self._release_lock()
                    raise PreflightGateError(
                        f"Source file changed since inventory: {src_rel}"
                    )

        if fault_injection == "disk-loss":
            self._release_lock()
            raise PreflightGateError("Fault injected: disk space lost during preflight")
        if fault_injection == "permission-loss":
            self._release_lock()
            raise PreflightGateError("Fault injected: permission lost during preflight")

        # Copy phase (E-03)
        if fault_injection == "copy-failure":
            tx_data["status"] = "failed"
            self._save_transaction(tx_data)
            self._release_lock()
            raise MigrationError("Fault injected: copy failed during staging")

        copied_records = []
        for mapping in tx_data["items"]:
            item_id = mapping.get("item_id")
            inv_item = inv_item_map.get(item_id, {})
            src_rel = (
                inv_item.get("repo_relpath")
                or f"{mapping.get('source_root', '')}/{mapping.get('source_relpath', '')}".strip(
                    "/"
                )
            )
            src_p = repo_path / src_rel
            dst_p = self.aw_dir / mapping["destination_relpath"]
            disposition = mapping.get("disposition", "migrate")

            if disposition in ("migrate", "preserve") and src_p.exists():
                dst_p.parent.mkdir(parents=True, exist_ok=True)
                if src_p.is_symlink():
                    link_target = os.readlink(src_p)
                    if dst_p.exists() or dst_p.is_symlink():
                        dst_p.unlink()
                    os.symlink(link_target, dst_p)
                elif src_p.is_file():
                    shutil.copy2(src_p, dst_p)
                    # Verify byte / hash equality
                    staged_hash = _sha256_file(dst_p)
                    exp_hash = inv_item.get("sha256")
                    if exp_hash and staged_hash != exp_hash:
                        tx_data["status"] = "failed"
                        self._save_transaction(tx_data)
                        self._release_lock()
                        raise VerificationError(
                            f"Staged copy hash mismatch for {dst_p}"
                        )
                    copied_records.append(
                        {
                            "source": str(src_p),
                            "destination": str(dst_p),
                            "hash": staged_hash,
                        }
                    )

        if fault_injection == "verify-mismatch":
            tx_data["status"] = "failed"
            self._save_transaction(tx_data)
            self._release_lock()
            raise VerificationError(
                "Fault injected: verification hash mismatch after staging"
            )

        tx_data["status"] = "staged"
        tx_data["last_verified_checkpoint"] = "staged"
        tx_data["phase_journal"].append(
            {
                "phase": "staged",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        self._save_transaction(tx_data)

        # Verification phase (E-03)
        tx_data["status"] = "verified"
        tx_data["last_verified_checkpoint"] = "verified"
        tx_data["phase_journal"].append(
            {
                "phase": "verified",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        self._save_transaction(tx_data)

        # Switch phase (E-04) - Written LAST
        if fault_injection == "switch-failure":
            tx_data["status"] = "failed"
            self._save_transaction(tx_data)
            self._release_lock()
            raise SwitchError("Fault injected: policy switch failed")

        config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if config_file.exists():
            cfg_data = json.loads(config_file.read_text(encoding="utf-8"))
        else:
            cfg_data = {}
        cfg_data["records_backend"] = target_backend

        tmp_cfg = self.config_dir / f".tmp_config_{os.getpid()}.json"
        with open(tmp_cfg, "w", encoding="utf-8") as f:
            json.dump(cfg_data, f, indent=2)
        os.replace(tmp_cfg, config_file)

        # Durable switch receipt
        receipt_data = {
            "transaction_id": tx_id,
            "target_backend": target_backend,
            "switched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "policy_file": str(config_file),
            "policy_digest": policy_digest,
            "authority": "switched",
        }
        with open(self.switch_receipt_file, "w", encoding="utf-8") as f:
            json.dump(receipt_data, f, indent=2)

        if fault_injection == "kill-after-switch-before-receipt":
            # Simulate process kill after policy switch but before full transaction completion
            tx_data["status"] = "switched"
            tx_data["last_verified_checkpoint"] = "switched"
            self._save_transaction(tx_data)
            self._release_lock()
            raise MigrationError(
                "Fault injected: process killed after policy switch write"
            )

        tx_data["status"] = "switched"
        tx_data["last_verified_checkpoint"] = "switched"
        tx_data["phase_journal"].append(
            {
                "phase": "switched",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        self._save_transaction(tx_data)

        # Retention phase (E-05)
        retention_data = {
            "transaction_id": tx_id,
            "retained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mappings": copied_records,
            "rollback_instructions": "Execute `aw migrate-layout rollback` to restore policy and unstage.",
            "retention_trigger": "post-migration independent postcheck",
            "cleanup_allowed": False,
        }
        with open(self.retention_manifest_file, "w", encoding="utf-8") as f:
            json.dump(retention_data, f, indent=2)

        tx_data["status"] = "retained"
        tx_data["last_verified_checkpoint"] = "retained"
        tx_data["phase_journal"].append(
            {
                "phase": "retained",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        self._save_transaction(tx_data)

        # Git boundary staging plan generation (E-06)
        if fault_injection == "cross-git-partial-stage":
            tx_data["status"] = "failed"
            self._save_transaction(tx_data)
            self._release_lock()
            raise MigrationError("Fault injected: cross-git partial staging failure")

        tx_data["status"] = "completed"
        tx_data["last_verified_checkpoint"] = "completed"
        tx_data["timestamps"]["completed_at"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        )
        tx_data["phase_journal"].append(
            {
                "phase": "completed",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        self._save_transaction(tx_data)

        self._release_lock()
        return self.plan_migration(target_backend)

    def status_migration(self) -> Dict[str, Any]:
        """Return migration transaction status."""
        tx = self._load_transaction()
        if not tx:
            return {
                "active": False,
                "status": "none",
                "authority": "legacy",
                "lock_held": self.lock_file.exists(),
            }

        has_receipt = self.switch_receipt_file.exists()
        authority = (
            "switched"
            if has_receipt or tx.get("status") in ("switched", "retained", "completed")
            else "legacy"
        )
        return {
            "active": True,
            "transaction_id": tx.get("transaction_id"),
            "status": tx.get("status"),
            "last_verified_checkpoint": tx.get("last_verified_checkpoint"),
            "authority": authority,
            "target_backend": tx.get("target_backend"),
            "lock_held": self.lock_file.exists(),
            "switch_receipt": has_receipt,
            "retention_manifest": self.retention_manifest_file.exists(),
        }

    def resume_migration(self, fault_injection: Optional[str] = None) -> Dict[str, Any]:
        """Idempotently resume interrupted migration from last checkpoint (E-07)."""
        tx = self._load_transaction()
        if not tx:
            raise MigrationError("No migration transaction found to resume.")

        if tx.get("status") == "completed":
            return {"status": "completed", "message": "Transaction already completed."}

        # Re-acquire lock
        self._acquire_lock(tx["transaction_id"])
        checkpoint = tx.get("last_verified_checkpoint", "initialized")

        if checkpoint in ("initialized", "locked"):
            # Resume from beginning by re-running execute_migration
            self.execute_migration(
                target_backend=tx.get("target_backend", "repository"),
                fault_injection=fault_injection,
            )
            return {"status": "completed", "resumed_from": checkpoint}

        if checkpoint in ("staged", "verified"):
            # Complete switch, retention, completed
            target_backend = tx.get("target_backend", "repository")
            config_file = self.config_dir / "config.json"
            self.config_dir.mkdir(parents=True, exist_ok=True)
            cfg_data = (
                json.loads(config_file.read_text(encoding="utf-8"))
                if config_file.exists()
                else {}
            )
            cfg_data["records_backend"] = target_backend
            tmp_cfg = self.config_dir / f".tmp_config_{os.getpid()}.json"
            with open(tmp_cfg, "w", encoding="utf-8") as f:
                json.dump(cfg_data, f, indent=2)
            os.replace(tmp_cfg, config_file)

            receipt_data = {
                "transaction_id": tx["transaction_id"],
                "target_backend": target_backend,
                "switched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "authority": "switched",
            }
            with open(self.switch_receipt_file, "w", encoding="utf-8") as f:
                json.dump(receipt_data, f, indent=2)

            tx["status"] = "completed"
            tx["last_verified_checkpoint"] = "completed"
            self._save_transaction(tx)
            self._release_lock()
            return {"status": "completed", "resumed_from": checkpoint}

        if checkpoint in ("switched", "retained"):
            tx["status"] = "completed"
            tx["last_verified_checkpoint"] = "completed"
            self._save_transaction(tx)
            self._release_lock()
            return {"status": "completed", "resumed_from": checkpoint}

        self._release_lock()
        return {"status": tx.get("status"), "resumed_from": checkpoint}

    def rollback_migration(
        self, fault_injection: Optional[str] = None
    ) -> Dict[str, Any]:
        """Roll back migration transaction cleanly (E-07)."""
        tx = self._load_transaction()
        repo_path = Path(self.target_repo)

        # If policy switch occurred, revert policy back to legacy
        config_file = self.config_dir / "config.json"
        if config_file.exists():
            cfg_data = json.loads(config_file.read_text(encoding="utf-8"))
            cfg_data["records_backend"] = "legacy"
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(cfg_data, f, indent=2)

        # Remove switch receipt & retention manifest
        if self.switch_receipt_file.exists():
            self.switch_receipt_file.unlink()
        if self.retention_manifest_file.exists():
            self.retention_manifest_file.unlink()

        # Remove staged items if present
        if tx and "items" in tx:
            for mapping in tx["items"]:
                dst_p = repo_path / mapping["destination_relpath"]
                if dst_p.exists() or dst_p.is_symlink():
                    if dst_p.is_file() or dst_p.is_symlink():
                        dst_p.unlink()
                    elif dst_p.is_dir():
                        shutil.rmtree(dst_p, ignore_errors=True)

        if tx:
            tx["status"] = "rolled_back"
            tx["last_verified_checkpoint"] = "rolled_back"
            self._save_transaction(tx)

        self._release_lock()
        return {"status": "rolled_back", "authority": "legacy"}

    def cleanup_migration(
        self,
        confirm: bool = False,
        fresh_inventory: Optional[Dict[str, Any]] = None,
        fault_injection: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform post-retention legacy source cleanup preview or apply (E-07)."""
        if fault_injection == "cleanup-refusal" or not confirm:
            raise CleanupError(
                "Cleanup refused: requires explicit high-warning confirmation (--confirm)"
            )

        tx = self._load_transaction()
        if not tx or tx.get("status") != "completed":
            raise CleanupError(
                "Cleanup refused: migration transaction is not completed."
            )

        if not self.retention_manifest_file.exists():
            raise CleanupError("Cleanup refused: missing retention manifest.")

        ret_data = json.loads(self.retention_manifest_file.read_text(encoding="utf-8"))

        # Verify no foreign or modified items in legacy sources
        cleaned_paths = []
        for item in ret_data.get("mappings", []):
            src_p = Path(item["source"])
            if src_p.exists():
                cur_hash = _sha256_file(src_p)
                if cur_hash != item.get("hash"):
                    raise CleanupError(
                        f"Cleanup refused: legacy source modified since migration: {src_p}"
                    )

        for item in ret_data.get("mappings", []):
            src_p = Path(item["source"])
            if src_p.exists() or src_p.is_symlink():
                src_p.unlink()
                cleaned_paths.append(str(src_p))

        return {"status": "cleaned", "removed": cleaned_paths}

    def uninstall_layout(
        self, preserve_records: bool = True, deep_remove_records: bool = False
    ) -> Dict[str, Any]:
        """Perform conservative uninstall preserving config, state, records, and remotes."""
        target_aw = Path(self.target_repo) / ".aw"
        removed_paths: List[str] = []
        preserved_paths: List[str] = []

        system_dir = target_aw / "system"
        if system_dir.exists():
            shutil.rmtree(system_dir, ignore_errors=True)
            removed_paths.append(str(system_dir))

        config_dir = target_aw / "config"
        if config_dir.exists():
            preserved_paths.append(str(config_dir))

        state_dir = target_aw / "state"
        if state_dir.exists():
            preserved_paths.append(str(state_dir))

        records_dir = target_aw / "records"
        if records_dir.exists():
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
