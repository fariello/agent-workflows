"""AW records storage backends, safety boundaries, and durability reporting (IPD 20260809-awlayout-03).

This module implements storage backend resolution (`home`, `companion`, `repository`),
safety boundary validation, and truthful durability state reporting specified by
``.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`` Section 5 & 6.

Invariants:
- TRUTHFUL DURABILITY: A configured remote alone remains a neutral observable fact.
  `durable-private` is assigned ONLY when user explicitly acknowledges remote/backup policy (L3-01 / spec Section 6.2).
- SAFE BOUNDARIES: Rejects path traversal, accidental repository nesting, and identity-conflicting companion repos.
- NO UNREQUESTED REMOTE ACTIONS: Never creates remotes, commits code, or pushes data.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_registry import (
    find_project,
    get_git_origin_url,
    load_registry,
    get_registry_path,
)
from agent_workflows.project_schema import (
    DurabilityState,
    LogicalRoot,
    RecordsBackend,
)


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class StorageSecurityError(StorageError):
    """Raised when safety boundary or nesting checks fail."""

    pass


class IdentityConflictError(StorageError):
    """Raised when companion repository belongs to another project identity."""

    pass


@dataclass(frozen=True)
class StorageStatus:
    """Truthful, observable storage status (spec Section 6.2)."""

    target_repo: str
    project_id: str
    records_backend: str
    records_path: str
    durability_state: str
    has_git: bool
    remote_url: Optional[str]
    remote_acknowledged: bool
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_repo": self.target_repo,
            "project_id": self.project_id,
            "records_backend": self.records_backend,
            "records_path": self.records_path,
            "durability_state": self.durability_state,
            "has_git": self.has_git,
            "remote_url": self.remote_url,
            "remote_acknowledged": self.remote_acknowledged,
            "recommendation": self.recommendation,
        }


def _canonical_path(path: Union[str, Path]) -> str:
    """Resolve symlinks and normalize path."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    try:
        resolved = p.resolve()
        return resolved.as_posix()
    except Exception:
        return os.path.abspath(p.as_posix()).replace("\\", "/")


def validate_storage_boundaries(
    target_repo: str, records_path: str, backend: str, aw_home: str
) -> None:
    """Validate safety boundaries and refuse unsafe or ambiguous storage resolution (E-02)."""
    if ".." in target_repo.split("/") or ".." in records_path.split("/"):
        raise StorageSecurityError("Path traversal '..' detected in storage resolution")

    target_canon = _canonical_path(target_repo)
    records_canon = _canonical_path(records_path)

    # Invariant: external backends (home/companion) MUST NOT resolve inside target repository
    if backend in (RecordsBackend.HOME.value, RecordsBackend.COMPANION.value):
        try:
            Path(records_canon).relative_to(Path(target_canon))
            raise StorageSecurityError(
                f"External backend '{backend}' records path ({records_canon}) cannot resolve inside target repository ({target_canon})"
            )
        except ValueError:
            pass  # Expected: external path is outside target_repo

    # Check for companion identity conflict
    if backend == RecordsBackend.COMPANION.value and os.path.exists(records_canon):
        reg_data = load_registry(get_registry_path(aw_home))
        match_res = find_project(records_canon, registry_data=reg_data, aw_home=aw_home)
        if match_res.entry and match_res.entry.target_paths:
            if target_canon not in match_res.entry.target_paths:
                raise IdentityConflictError(
                    f"Companion storage path ({records_canon}) is attached to project '{match_res.entry.project_id}' "
                    f"which does not include target repo '{target_canon}'"
                )


def _get_ack_file_path(state_root: str) -> Path:
    """Get path to the remote durability acknowledgement record."""
    return Path(state_root) / "remote_durability_ack.json"


def get_storage_status(
    repo_path: Optional[str] = None, aw_home: Optional[str] = None
) -> StorageStatus:
    """Pure, side-effect-free observable storage status inspector (spec Section 6.2 & E-03)."""
    ctx = resolve_project_context(target_repo=repo_path, aw_home=aw_home)
    backend = ctx.records_backend
    records_path = ctx.logical_roots[LogicalRoot.RECORDS.value]

    validate_storage_boundaries(
        ctx.target_repo, records_path, backend, ctx.effective_aw_home
    )

    # Check git existence in records_path
    git_dir = Path(records_path) / ".git"
    has_git = git_dir.exists()

    # Probe remote origin URL if git exists
    remote_url = None
    if has_git:
        remote_url = get_git_origin_url(records_path)

    # Check explicit remote acknowledgement record
    ack_file = _get_ack_file_path(ctx.logical_roots[LogicalRoot.STATE.value])
    remote_acknowledged = False
    if ack_file.is_file():
        try:
            with open(ack_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                remote_acknowledged = bool(data.get("acknowledged"))
        except Exception:
            pass

    # Truthful durability state classification (spec Section 6.2):
    # - repository backend -> repository-managed
    # - has_git + remote_acknowledged -> durable-private
    # - has_git -> local-git
    # - uninitialized -> unversioned
    if backend == RecordsBackend.REPOSITORY.value:
        durability_state = DurabilityState.REPOSITORY_MANAGED.value
        rec = "Records are stored in target repository Git tree."
    elif has_git and remote_acknowledged:
        durability_state = DurabilityState.DURABLE_PRIVATE.value
        rec = "Records storage is backed by local Git and acknowledged remote policy."
    elif has_git:
        durability_state = DurabilityState.LOCAL_GIT.value
        rec = "Records storage has local Git history. Configure remote or acknowledge backup policy for durable-private status."
    else:
        durability_state = DurabilityState.UNVERSIONED.value
        rec = "Records storage is unversioned local files. Run 'aw storage init' to create a local Git repository."

    return StorageStatus(
        target_repo=ctx.target_repo,
        project_id=ctx.project_id,
        records_backend=backend,
        records_path=records_path,
        durability_state=durability_state,
        has_git=has_git,
        remote_url=remote_url,
        remote_acknowledged=remote_acknowledged,
        recommendation=rec,
    )


def acknowledge_remote_durability(
    repo_path: Optional[str] = None,
    aw_home: Optional[str] = None,
    acknowledge: bool = True,
) -> StorageStatus:
    """Record explicit user acknowledgement of remote/backup policy (E-03)."""
    ctx = resolve_project_context(target_repo=repo_path, aw_home=aw_home)
    state_root = Path(ctx.logical_roots[LogicalRoot.STATE.value])
    state_root.mkdir(parents=True, exist_ok=True)

    ack_file = _get_ack_file_path(str(state_root))
    payload = {
        "project_id": ctx.project_id,
        "acknowledged": acknowledge,
        "records_backend": ctx.records_backend,
    }

    tmp_path = ack_file.parent / ".remote_ack.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_path, ack_file)

    return get_storage_status(repo_path=repo_path, aw_home=aw_home)


def init_records_storage(
    repo_path: Optional[str] = None,
    aw_home: Optional[str] = None,
    git_init: bool = True,
    acknowledge_remote: bool = False,
) -> StorageStatus:
    """Explicit storage initialization flow (E-04). Writes ONLY when explicitly commanded."""
    ctx = resolve_project_context(target_repo=repo_path, aw_home=aw_home)
    backend = ctx.records_backend
    records_path = ctx.logical_roots[LogicalRoot.RECORDS.value]

    validate_storage_boundaries(
        ctx.target_repo, records_path, backend, ctx.effective_aw_home
    )

    # Materialize records directory if missing
    rec_p = Path(records_path)
    rec_p.mkdir(parents=True, exist_ok=True)

    # Initialize local Git if requested and absent (NEVER creates remote or pushes!)
    git_dir = rec_p / ".git"
    if git_init and not git_dir.exists():
        subprocess.run(
            ["git", "-C", str(rec_p), "init"],
            capture_output=True,
            check=True,
            text=True,
        )

    if acknowledge_remote:
        acknowledge_remote_durability(
            repo_path=repo_path, aw_home=aw_home, acknowledge=True
        )

    return get_storage_status(repo_path=repo_path, aw_home=aw_home)
