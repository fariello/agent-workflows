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


# --------------------------------------------------------------------------------------
# Optional rename-on-migrate to the uniform .type.md grammar (backlog u9cicx / awnaming OQ-02).
# --------------------------------------------------------------------------------------

# The record SUB-TYPE (the `records/<subtype>/...` segment) -> its filename type facet. comms and
# research are DOCUMENTED EXCEPTIONS (routing-named / `.<model>.<kind>.md`) and are absent here, so
# they are never faceted. Non-durable basenames (README/INDEX/STATUS) are also skipped.
_RECORD_SUBTYPE_FACET = {
    "plans": "ipd",
    "specs": "spec",
    "walkthroughs": "walkthrough",
    "roadmaps": "roadmap",
    "backlog": "backlog",
    "prompts": "prompt",
    "prompt-library": "prompt",
}
_NON_DURABLE_BASENAMES = frozenset(("README.md", "INDEX.md", "STATUS.md"))


def _grammar_facet_for(
    destination_relpath: str, destination_root_class: str
) -> Optional[str]:
    """Return the `.type` facet (no dot) for a migrated record, or None to leave the name bare.

    Only `records`-class items are eligible; the sub-type is parsed from the `records/<subtype>/`
    segment of ``destination_relpath``. comms/research sub-types (absent from the map) and
    non-durable basenames are left bare.
    """

    if destination_root_class != "records":
        return None
    rel = destination_relpath.lstrip("/")
    if not (rel == "records" or rel.startswith("records/")):
        return None
    parts = rel.split("/")
    if len(parts) < 2:
        return None
    subtype = parts[1]
    return _RECORD_SUBTYPE_FACET.get(subtype)


def _apply_grammar_facet(dst_p: Path, facet: Optional[str]) -> Path:
    """Append `.<facet>` before `.md` unless the name is non-durable or already carries that facet.

    Idempotent: a name that already ends in `.<facet>.md` is returned unchanged.
    """

    if facet is None:
        return dst_p
    name = dst_p.name
    if name in _NON_DURABLE_BASENAMES or not name.endswith(".md"):
        return dst_p
    if name.endswith(f".{facet}.md"):
        return dst_p
    return dst_p.with_name(name[: -len(".md")] + f".{facet}.md")


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

        # Durable & Runtime transaction artifacts (Spec 4.1 Table 4.1)
        self.transaction_file = (
            self.runtime_state_dir / "transactions" / "migration_transaction.json"
        )
        self.lock_file = self.runtime_state_dir / "locks" / "migration_writer.lock"
        self.switch_receipt_file = (
            self.durable_state_dir / "migrations" / "switch_receipt.json"
        )
        self.retention_manifest_file = (
            self.durable_state_dir / "migrations" / "retention_manifest.json"
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

    def generate_git_staging_plans(
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Generate separate target, companion, and source Git staging plans (E-06)."""
        plans: Dict[str, Dict[str, Any]] = {
            "target": {"owner": "target", "staged_paths": [], "index_clean": True},
            "companion": {
                "owner": "companion",
                "staged_paths": [],
                "index_clean": True,
            },
            "source": {"owner": "source", "staged_paths": [], "index_clean": True},
        }
        for item in items:
            owner = item.get("git_owner") or item.get("owner") or "target"
            if owner not in plans:
                owner = "target"
            dst_rel = item.get("destination_relpath") or item.get("target_relpath")
            if dst_rel:
                plans[owner]["staged_paths"].append(dst_rel)
        return plans

    # ------------------------------------------------------------------
    # Move-not-copy helpers (IPD hnzr8v, awphysical Order 14)
    # ------------------------------------------------------------------

    def _records_root_for_backend(self, target_backend: str) -> Path:
        """Resolve the records root for the backend being MIGRATED TO (not the pre-migration
        context default). `repository` -> <target>/.aw/records; `home` -> the AW_HOME projects
        records root; `companion` -> the companion repo's .aw/records.
        """

        if target_backend == "repository":
            return self.records_dir  # <target>/.aw/records
        # home / companion: use the resolved logical root (context reflects these when the
        # policy selects them). Fall back to the target records dir if unresolved.
        try:
            return Path(self.ctx.logical_roots[LogicalRoot.RECORDS.value])
        except (KeyError, TypeError):
            return self.records_dir

    def _resolve_destination_path(
        self, destination_relpath: str, target_backend: str = "repository"
    ) -> Path:
        """Map a map-item destination_relpath to its RESOLVED on-disk destination.

        The `records/` class resolves to the records root for the TARGET backend being
        migrated to (repository -> <target>/.aw/records; companion -> the companion repo's
        .aw/records; home -> <AW_HOME>/projects/<id>/.aw/records). All other classes
        (system/config/state) stay under the target's `.aw/`. For the `repository` backend
        the records root IS `<target>/.aw/records`, identical to the historical
        `self.aw_dir / destination_relpath`, so existing behavior is unchanged.
        """

        rel = destination_relpath.lstrip("/")
        if rel == "records" or rel.startswith("records/"):
            records_root = self._records_root_for_backend(target_backend)
            sub = rel[len("records") :].lstrip("/")
            return records_root / sub if sub else records_root
        return self.aw_dir / rel

    def _is_within(self, path: Path, root: Path) -> bool:
        """True when `path` is inside `root` (both resolved)."""
        try:
            path.resolve().relative_to(root.resolve())
            return True
        except (ValueError, OSError):
            return False

    def _git_toplevel(self, path: Path) -> Optional[Path]:
        """Return the git work-tree top-level containing `path`, or None."""
        probe = path if path.is_dir() else path.parent
        proc = _run_git(probe, ["rev-parse", "--show-toplevel"])
        if proc.returncode == 0 and proc.stdout.strip():
            return Path(proc.stdout.strip()).resolve()
        return None

    def _perform_move(self, src_p: Path, dst_p: Path, was_tracked: bool) -> None:
        """Relocate src_p -> dst_p as a MOVE (no retained twin), honoring git tracking.

        - Same git work tree + tracked: `git mv` (preserves history, stages the rename);
          on failure falls back to filesystem rename + `git rm --cached src` + `git add dst`.
        - Cross work tree (companion/home) + tracked: filesystem move, then a TWO-INDEX
          stage - `git rm --cached` the source in the TARGET index and `git add` the
          destination in the DESTINATION repo's index (a home destination outside any repo
          just leaves the moved file untracked).
        - Untracked (either case): plain filesystem move.
        Symlinks are moved as links (never dereferenced).
        """

        dst_p.parent.mkdir(parents=True, exist_ok=True)
        # FAIL-CLOSED on a FOREIGN pre-existing destination (IPD awretrofit Order 04, M01/E-04).
        # In a normal run the destination is freshly computed and empty; a THIS-transaction dedup
        # twin is handled earlier in the move loop (dest_seen), and an already-journaled item is
        # skipped on resume. So if we reach here and the destination already holds content, it is
        # content this migration did NOT create - refuse to clobber it and surface a conflict,
        # rather than the previous unconditional rmtree/unlink (which could destroy hand-migrated
        # or foreign data). A hash-identical file is the one safe exception (idempotent re-move).
        if dst_p.exists() or dst_p.is_symlink():
            safe_identical = (
                dst_p.is_file()
                and not dst_p.is_symlink()
                and src_p.is_file()
                and not src_p.is_symlink()
                and _sha256_file(dst_p) == _sha256_file(src_p)
            )
            if not safe_identical:
                raise MigrationError(
                    f"Refusing to overwrite a pre-existing destination this migration did not "
                    f"create: {dst_p}. Resolve the conflict (remove/rename it) and re-run; "
                    f"the migration will not destroy foreign content."
                )
            if dst_p.is_dir() and not dst_p.is_symlink():
                shutil.rmtree(dst_p)
            else:
                dst_p.unlink()

        target_top = Path(self.target_repo).resolve()
        dst_top = self._git_toplevel(dst_p)
        same_tree = was_tracked and dst_top is not None and dst_top == target_top

        if same_tree:
            proc = _run_git(target_top, ["mv", "--", str(src_p), str(dst_p)])
            if proc.returncode == 0:
                return
            # Fall back to a manual move that still records the rename in the index.
            self._raw_move(src_p, dst_p)
            _run_git(target_top, ["rm", "--cached", "--", str(src_p)])
            _run_git(target_top, ["add", "--", str(dst_p)])
            return

        # Untracked, or a cross-work-tree (companion/home) destination.
        self._raw_move(src_p, dst_p)
        if was_tracked:
            # Record the removal in the TARGET index; stage the addition in the
            # destination repo's index (if the destination lives in a git work tree).
            _run_git(target_top, ["rm", "--cached", "--", str(src_p)])
            if dst_top is not None:
                _run_git(dst_top, ["add", "--", str(dst_p)])

    @staticmethod
    def _raw_move(src_p: Path, dst_p: Path) -> None:
        """Filesystem move that preserves symlinks (never dereferences)."""
        if src_p.is_symlink():
            link_target = os.readlink(src_p)
            os.symlink(link_target, dst_p)
            src_p.unlink()
        else:
            shutil.move(str(src_p), str(dst_p))

    # Legacy roots whose remaining (unmoved) content the leftover step governs. Host adapters
    # (.claude/.opencode/AGENTS.md/...) are preserved in place and are NOT leftovers.
    _LEGACY_LEFTOVER_ROOTS = (".agents", "workflow-artifacts")

    def _is_removable_leftover(self, rel: str) -> bool:
        """True only for a leftover that is SAFE to delete under `remove` (IPD wvlk84).

        Git TRACKING STATE is the primary safety signal: `remove` deletes ONLY a path that git
        TRACKS in the target repo (a genuine orphaned tracked leftover). Anything UNTRACKED or
        IGNORED is preserved - critically the untracked-but-not-gitignored quarantine lanes
        (`.agents/prompts/untracked/`, `.agents/comms/untracked/`, and the legacy `local/` lane still
        on disk in un-migrated repos), which a `git check-ignore`-only guard would MISS (they are
        untracked, not matched by .gitignore).
        """

        repo_path = Path(self.target_repo)
        norm = rel.replace("\\", "/")
        # Never remove the deliberately-local lanes or the untracked-safety convention, even if
        # some future .gitignore change made git's own state ambiguous.
        if "/local/" in f"/{norm}" or norm.endswith("/local") or "untracked" in norm:
            return False
        # IGNORED -> preserve (belt): check-ignore returns 0 when the path is ignored.
        if _run_git(repo_path, ["check-ignore", "-q", "--", rel]).returncode == 0:
            return False
        # PRIMARY signal: only a TRACKED path is removable. `ls-files --error-unmatch` exits 0
        # iff the path is tracked in the index; nonzero (untracked) -> preserve.
        tracked = (
            _run_git(repo_path, ["ls-files", "--error-unmatch", "--", rel]).returncode
            == 0
        )
        return tracked

    def _handle_leftovers(
        self, tx_data: Dict[str, Any], leftover_disposition: str = "defer"
    ) -> Dict[str, Any]:
        """Dispose of legacy material still present after the classified moves (IPD hnzr8v E-04).

        `leftover_disposition` is one of keep | remove | defer (default defer). This is the
        non-interactive contract used by the engine + CLI flag; an interactive front-end
        (Order 16 wizard) supplies the operator's per-group choice here. `remove` deletes ONLY
        tracked, genuinely-orphaned leftovers and PRESERVES all untracked/ignored/local content
        (IPD wvlk84); `defer` records leftovers for a later cleanup; `keep` leaves them.
        Directory pruning removes ONLY now-empty legacy directories - a directory still holding
        any content (including preserved content) is never removed (never `rmtree` a root wholesale).
        """

        repo_path = Path(self.target_repo)
        leftovers: List[str] = []
        for root_name in self._LEGACY_LEFTOVER_ROOTS:
            root = repo_path / root_name
            if not root.is_dir():
                continue
            for p in sorted(root.rglob("*")):
                if p.is_file() or p.is_symlink():
                    leftovers.append(str(p.relative_to(repo_path).as_posix()))

        result: Dict[str, Any] = {
            "disposition": leftover_disposition,
            "leftovers": leftovers,
            "removed": [],
            "preserved": [],
        }

        if leftover_disposition == "remove":
            for rel in leftovers:
                p = repo_path / rel
                # Only tracked orphans are removable; untracked/ignored/local lanes are PRESERVED
                # (the data-loss guard - a bare unlink here would destroy local-only content).
                if not self._is_removable_leftover(rel):
                    result["preserved"].append(rel)
                    continue
                try:
                    proc = _run_git(repo_path, ["rm", "-f", "--", rel])
                    if proc.returncode == 0:
                        # Cleanly removed via git (staged deletion of a tracked orphan).
                        result["removed"].append(rel)
                    elif p.exists() or p.is_symlink():
                        # git rm failed but the path is still present: force-unlink it, and record
                        # it as a DEGRADED removal, NOT a clean `removed` (IPD awretrofit Order 04,
                        # L01/E-05) - the filesystem and the git index may now disagree, which a
                        # caller/report must be able to see rather than trusting a clean-removed
                        # label.
                        p.unlink()
                        result.setdefault("degraded", []).append(rel)
                    else:
                        # git rm nonzero but the path is already gone: treat as removed.
                        result["removed"].append(rel)
                except OSError:
                    result["preserved"].append(rel)
        else:
            # keep/defer: nothing is deleted; every leftover is preserved.
            result["preserved"] = list(leftovers)

        # Prune now-empty legacy directories (never a directory that still holds content -
        # a directory retaining preserved files is not empty, so it is left intact).
        for root_name in self._LEGACY_LEFTOVER_ROOTS:
            root = repo_path / root_name
            if not root.is_dir():
                continue
            for d in sorted(
                (p for p in root.rglob("*") if p.is_dir()),
                key=lambda x: len(x.parts),
                reverse=True,
            ):
                try:
                    if not any(d.iterdir()):
                        d.rmdir()
                except OSError:
                    pass
            try:
                if root.is_dir() and not any(root.iterdir()):
                    root.rmdir()
            except OSError:
                pass

        return result

    def _acquire_lock(self, transaction_id: str) -> None:
        """Acquire writer lock or throw TransactionLockError."""
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
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
        tmp_lock = self.lock_file.parent / f".tmp_lock_{os.getpid()}"
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
        self.transaction_file.parent.mkdir(parents=True, exist_ok=True)
        tx_data["timestamps"]["updated_at"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        )
        tmp_tx = self.transaction_file.parent / f".tmp_tx_{os.getpid()}.json"
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
        resume_tx: Optional[Dict[str, Any]] = None,
        leftover_disposition: str = "defer",
        rename_to_grammar: bool = False,
    ) -> MigrationPlan:
        """Execute transactional move-verify-switch migration.

        When ``resume_tx`` is provided (a persisted, interrupted transaction), REUSE its
        items, move_journal, and transaction_id rather than rebuilding a fresh inventory:
        after a partial MOVE the legacy sources are gone, so a fresh inventory would no
        longer see them and the partial move could neither complete nor reverse (IPD hnzr8v
        E-06). The move phase is idempotent on re-entry (already-journaled items are skipped).
        """
        repo_path = Path(self.target_repo)

        # 1. Build or validate input plan/inventory/map
        if resume_tx is None and plan_doc is None:
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

        if resume_tx is None:
            assert plan_doc is not None
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

        # Create unique transaction state machine (E-01), or REUSE the interrupted one on resume.
        if resume_tx is not None:
            tx_id = resume_tx["transaction_id"]
            tx_data = resume_tx
        else:
            assert plan_doc is not None
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
                # Persist the inventory items so a RESUME can rebuild inv_item_map without a
                # fresh inventory (which would miss already-moved sources) - IPD hnzr8v E-06.
                "inventory_items": plan_doc.get("inventory", {}).get("items", []),
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

        # Build lookup map from inventory items (persisted in the transaction so RESUME does
        # not need a fresh inventory that would miss already-moved sources - IPD hnzr8v E-06).
        inv_item_map = {
            item["item_id"]: item for item in tx_data.get("inventory_items", [])
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

        # MOVE phase (IPD hnzr8v): relocate each classified item to its resolved
        # destination as a MOVE (no retained legacy twin), journaling each relocation
        # PER ITEM before the next so a crash leaves a precise, resumable record. A prior
        # run's move_journal is reused on re-entry (resume) so already-moved items are
        # skipped rather than re-processed against a source that is now gone.
        move_journal: List[Dict[str, Any]] = tx_data.get("move_journal", [])
        journaled_ids = {e["item_id"] for e in move_journal}
        copied_records = tx_data.get("copied_records", [])
        # Destinations already occupied by THIS transaction's moves (for dedup-remove).
        dest_seen = {
            e["destination"] for e in move_journal if e.get("action") == "move"
        }

        for mapping in tx_data["items"]:
            item_id = mapping.get("item_id")
            if item_id in journaled_ids:
                continue  # already relocated in a prior (interrupted) run; resume-safe
            inv_item = inv_item_map.get(item_id, {})
            src_rel = (
                inv_item.get("repo_relpath")
                or f"{mapping.get('source_root', '')}/{mapping.get('source_relpath', '')}".strip(
                    "/"
                )
            )
            src_p = repo_path / src_rel
            dst_p = self._resolve_destination_path(
                mapping["destination_relpath"], target_backend
            )
            # Optional rename-on-migrate (backlog u9cicx / awnaming OQ-02): append the class-correct
            # .type.md facet to the destination name BEFORE the dedup dest_seen check and journaling,
            # so twins dedup on the final name and rollback (which reverses via the journaled
            # destination) restores correctly. comms/research/non-durable names are left bare.
            if rename_to_grammar:
                facet = _grammar_facet_for(
                    mapping["destination_relpath"],
                    mapping.get("destination_root_class", ""),
                )
                dst_p = _apply_grammar_facet(dst_p, facet)
            disposition = mapping.get("disposition", "migrate")
            was_tracked = inv_item.get("git_state") == "tracked"
            exp_hash = inv_item.get("sha256")

            # Host-required discovery files (host-adapter-in-place) are preserved at their exact
            # repo-root path per spec S3.1/S9; they are NEVER moved (doing so would defeat host
            # discovery and, for a root item, operate on the .aw directory). Leave them untouched.
            if mapping.get("destination_root_class") == "host-adapter-in-place":
                continue

            if disposition not in ("migrate", "preserve") or not (
                src_p.exists() or src_p.is_symlink()
            ):
                continue

            # Only FILES and SYMLINKS are relocated; directory inventory entries are not moved
            # as units (their contained files carry the move, and destination parents are created
            # on demand). This mirrors the pre-move behavior (which guarded on `is_file`).
            if src_p.is_dir() and not src_p.is_symlink():
                continue

            # Dedup twin: build_migration_map may map two identical-hash sources to ONE
            # destination. The first is MOVED; a later identical source cannot be moved onto
            # the already-moved destination, so it is REMOVED (recorded for reversal).
            if str(dst_p) in dest_seen:
                if was_tracked:
                    _run_git(Path(self.target_repo), ["rm", "-f", "--", str(src_p)])
                    if src_p.exists() or src_p.is_symlink():
                        src_p.unlink()
                else:
                    src_p.unlink()
                entry = {
                    "item_id": item_id,
                    "source": str(src_p),
                    "destination": str(dst_p),
                    "hash": exp_hash,
                    "was_tracked": was_tracked,
                    "action": "dedup-remove",
                }
                move_journal.append(entry)
                journaled_ids.add(item_id)
                tx_data["move_journal"] = move_journal
                self._save_transaction(tx_data)
                continue

            self._perform_move(src_p, dst_p, was_tracked)

            # Verify the DESTINATION (the source is gone after the move).
            if not dst_p.is_symlink():
                staged_hash = _sha256_file(dst_p)
                if exp_hash and staged_hash != exp_hash:
                    tx_data["status"] = "failed"
                    self._save_transaction(tx_data)
                    self._release_lock()
                    raise VerificationError(f"Moved-file hash mismatch for {dst_p}")
            else:
                staged_hash = exp_hash

            entry = {
                "item_id": item_id,
                "source": str(src_p),
                "destination": str(dst_p),
                "hash": staged_hash,
                "was_tracked": was_tracked,
                "action": "move",
            }
            move_journal.append(entry)
            journaled_ids.add(item_id)
            dest_seen.add(str(dst_p))
            copied_records.append(
                {
                    "source": str(src_p),
                    "destination": str(dst_p),
                    "hash": staged_hash,
                }
            )
            # Persist the journal PER ITEM (crash-safe resume, E-06).
            tx_data["move_journal"] = move_journal
            tx_data["copied_records"] = copied_records
            self._save_transaction(tx_data)

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
        self.switch_receipt_file.parent.mkdir(parents=True, exist_ok=True)
        receipt_data = {
            "transaction_id": tx_id,
            "target_backend": target_backend,
            "switched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "policy_file": str(config_file),
            "policy_digest": tx_data.get("policy_digest"),
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

        # Move-journal manifest (IPD hnzr8v E-05): under move-not-copy there is no retained
        # legacy twin; the manifest records the MOVES performed (the authoritative rollback
        # source) plus the leftover disposition. `mappings` is kept (the moves) for the legacy
        # `cleanup` consumer, but its meaning is now "what was moved", not "copies to delete".
        self.retention_manifest_file.parent.mkdir(parents=True, exist_ok=True)
        retention_data = {
            "transaction_id": tx_id,
            "retained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mappings": copied_records,
            "move_journal": tx_data.get("move_journal", []),
            "rollback_instructions": "Execute `aw migrate-layout rollback` to reverse the moves and restore policy.",
            "retention_trigger": "post-migration independent postcheck",
            "cleanup_allowed": False,
        }
        with open(self.retention_manifest_file, "w", encoding="utf-8") as f:
            json.dump(retention_data, f, indent=2)

        # Interactive leftover disposition (IPD hnzr8v E-04): after the moves, anything still
        # under the legacy roots is UNMOVED/unclassified material. Decide its fate - keep (leave
        # in place), remove (delete), or defer (record for a later cleanup). Non-interactive
        # default is `defer` (never deletes without an explicit choice). Only truly-empty legacy
        # directories are pruned; a directory that still holds content is never removed.
        leftover_result = self._handle_leftovers(
            tx_data, leftover_disposition=leftover_disposition
        )
        tx_data["leftover_disposition"] = leftover_result
        self._save_transaction(tx_data)

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
        git_plans = self.generate_git_staging_plans(tx_data["items"])
        tx_data["git_staging_plans"] = git_plans

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
            # Re-drive the SAME transaction (reusing its items + move_journal), never a fresh
            # inventory: after a partial MOVE the legacy sources are gone (IPD hnzr8v E-06).
            # Release the lock we just took so execute_migration can re-acquire it cleanly.
            self._release_lock()
            self.execute_migration(
                target_backend=tx.get("target_backend", "repository"),
                fault_injection=fault_injection,
                resume_tx=tx,
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

        # If policy switch occurred, revert policy back to legacy
        config_file = self.config_dir / "config.json"
        if config_file.exists():
            cfg_data = json.loads(config_file.read_text(encoding="utf-8"))
            cfg_data["records_backend"] = "legacy"
            # Atomic write (IPD awretrofit Order 04, L01/E-05): temp-file + os.replace, matching the
            # forward-switch idiom - a crash mid-rollback cannot truncate/corrupt config.json.
            tmp_cfg = config_file.parent / f".tmp_config_{os.getpid()}.json"
            with open(tmp_cfg, "w", encoding="utf-8") as f:
                json.dump(cfg_data, f, indent=2)
            os.replace(tmp_cfg, config_file)

        # Remove switch receipt & retention manifest
        if self.switch_receipt_file.exists():
            self.switch_receipt_file.unlink()
        if self.retention_manifest_file.exists():
            self.retention_manifest_file.unlink()

        # Reverse the MOVE journal (IPD hnzr8v): the apply MOVED classified items (no
        # retained twin), so rollback must MOVE them back, not merely delete a staged copy.
        # Iterate in REVERSE so a dedup twin is restored FROM the surviving destination BEFORE
        # that destination is itself moved back. This is safe from a PARTIAL (mid-move,
        # resumed-or-not) state because it only reverses what the journal actually recorded.
        target_top = Path(self.target_repo).resolve()
        move_journal = (tx or {}).get("move_journal", [])
        for entry in reversed(move_journal):
            src_p = Path(entry["source"])
            dst_p = Path(entry["destination"])
            was_tracked = entry.get("was_tracked", False)
            action = entry.get("action", "move")
            if action == "dedup-remove":
                # The twin's source was removed in favor of the surviving destination;
                # restore it by copying the destination bytes back to the source path.
                if dst_p.exists() and not src_p.exists():
                    src_p.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dst_p, src_p)
                    if was_tracked:
                        _run_git(target_top, ["add", "--", str(src_p)])
                continue
            # action == "move": relocate the destination back to the original source.
            if dst_p.exists() or dst_p.is_symlink():
                self._perform_move(dst_p, src_p, was_tracked)

        # Prune any now-empty relocated-class directories left under .aw/ (never touch
        # host-adapter-in-place destinations, whose "destination" is a live repo-root path).
        if tx and "items" in tx:
            rb_backend = (tx or {}).get("target_backend", "repository")
            for mapping in tx["items"]:
                if mapping.get("destination_root_class") == "host-adapter-in-place":
                    continue
                dst_p = self._resolve_destination_path(
                    mapping["destination_relpath"], rb_backend
                )
                parent = dst_p.parent
                try:
                    while (
                        parent != parent.parent
                        and self._is_within(parent, self.aw_dir)
                        and parent.is_dir()
                        and not any(parent.iterdir())
                    ):
                        parent.rmdir()
                        parent = parent.parent
                except OSError:
                    pass

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
        """Post-migration cleanup preview or apply.

        Reconciled for move-not-copy (IPD hnzr8v E-05): under the MOVE contract the manifest
        `mappings` sources are already GONE (moved, not copied-and-retained), so this finds
        nothing to remove for moved items and is a safe no-op for them. It remains meaningful
        only for material that still exists at a legacy path (e.g. a `keep`/`defer` leftover the
        operator later chooses to remove), and it still refuses on any legacy source whose hash
        changed since the migration. It never deletes a moved item's (nonexistent) source.
        """
        if fault_injection == "cleanup-refusal":
            raise CleanupError("Cleanup refused: fault injected cleanup-refusal")

        tx = self._load_transaction()
        if not tx or tx.get("status") != "completed":
            raise CleanupError(
                "Cleanup refused: migration transaction is not completed."
            )

        if not self.retention_manifest_file.exists():
            raise CleanupError("Cleanup refused: missing retention manifest.")

        ret_data = json.loads(self.retention_manifest_file.read_text(encoding="utf-8"))
        mappings = ret_data.get("mappings", [])

        # Check for modified or foreign items in legacy sources
        legacy_sources = [Path(item["source"]) for item in mappings]
        would_remove = [str(p) for p in legacy_sources if p.exists() or p.is_symlink()]

        for item in mappings:
            src_p = Path(item["source"])
            # Only FILE sources carry a hash; a directory source is content-guarded in the
            # deletion loop below (Order 04 E-03), not hash-checked here.
            if src_p.is_file() and not src_p.is_symlink():
                cur_hash = _sha256_file(src_p)
                if cur_hash != item.get("hash"):
                    raise CleanupError(
                        f"Cleanup refused: legacy source modified since migration: {src_p}"
                    )

        if not confirm:
            return {
                "status": "preview",
                "would_remove": would_remove,
                "confirm_required": True,
                "message": "Preview only. Pass confirm=True (--confirm) to execute deletion.",
            }

        # The set of manifest-recorded source paths - the ONLY content cleanup may remove
        # (IPD awretrofit Order 04, M01/E-03). Anything at a legacy source path that is NOT in
        # this set is content RE-CREATED after the migration (e.g. a fresh install scaffold, a
        # new local file), which cleanup MUST preserve rather than blindly rmtree.
        manifest_paths = {str(p.resolve()) for p in legacy_sources}
        cleaned_paths: List[str] = []
        refused_paths: List[str] = []
        for src_p in legacy_sources:
            if not (src_p.exists() or src_p.is_symlink()):
                continue
            if src_p.is_file() or src_p.is_symlink():
                # File hash was already re-verified against the manifest above; safe to remove.
                src_p.unlink()
                cleaned_paths.append(str(src_p))
            elif src_p.is_dir():
                # Only remove a directory whose ENTIRE remaining content is manifest-recorded
                # (i.e. re-created content is absent). Never blanket-rmtree with ignore_errors:
                # a directory holding any path this migration did not record is REFUSED and
                # preserved intact, so re-created untracked content survives cleanup.
                foreign = [
                    child
                    for child in src_p.rglob("*")
                    if (child.is_file() or child.is_symlink())
                    and str(child.resolve()) not in manifest_paths
                ]
                if foreign:
                    refused_paths.append(str(src_p))
                    continue
                shutil.rmtree(src_p)
                cleaned_paths.append(str(src_p))

        result: Dict[str, Any] = {"status": "cleaned", "removed": cleaned_paths}
        if refused_paths:
            result["refused"] = refused_paths
            result["message"] = (
                "Some legacy dirs were PRESERVED because they hold content re-created after "
                "migration (not recorded in the retention manifest); remove that content manually "
                "if you intend to delete them."
            )
        return result

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
