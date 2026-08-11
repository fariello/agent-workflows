"""AW records storage backends, safety boundaries, and durability reporting (IPD 20260809-awlayout-03).

This module implements storage backend resolution (`home`, `companion`, `repository`),
safety boundary validation, and truthful durability state reporting specified by
``.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`` Section 5 & 6.

Invariants:
- TRUTHFUL DURABILITY: A configured remote alone remains a neutral observable fact. The
  ``DurabilityState.ACKNOWLEDGED_DURABLE`` state is assigned ONLY when the user explicitly acknowledges
  the remote/backup policy (L3-01 / spec Section 6.2).
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
    remote_reachable: Optional[bool]
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
            "remote_reachable": self.remote_reachable,
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


def _remote_reachable(records_path: str) -> Optional[bool]:
    """Probe the configured origin without writing, prompting, or hanging indefinitely."""

    try:
        proc = subprocess.run(
            ["git", "-C", records_path, "ls-remote", "--exit-code", "origin", "HEAD"],
            capture_output=True,
            check=False,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.returncode == 0


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
    remote_reachable = _remote_reachable(records_path) if remote_url else None

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

    # Truthful durability state classification (spec Section 6.2), one DurabilityState per case:
    # - repository backend -> REPOSITORY_MANAGED
    # - acknowledged remote + reachable -> ACKNOWLEDGED_DURABLE
    # - acknowledged remote + unreachable -> UNREACHABLE
    # - configured, unacknowledged remote -> UNACKNOWLEDGED_REMOTE
    # - local Git without remote -> LOCAL_GIT
    # - uninitialized -> UNVERSIONED
    if backend == RecordsBackend.REPOSITORY.value:
        durability_state = DurabilityState.REPOSITORY_MANAGED.value
        rec = "Records are stored in target repository Git tree."
    elif has_git and remote_url and remote_acknowledged and remote_reachable is True:
        durability_state = DurabilityState.ACKNOWLEDGED_DURABLE.value
        rec = "Records storage is backed by local Git and acknowledged remote policy."
    elif has_git and remote_url and remote_acknowledged and remote_reachable is False:
        durability_state = DurabilityState.UNREACHABLE.value
        rec = "The acknowledged records remote could not be verified as reachable."
    elif has_git and remote_url and remote_acknowledged:
        durability_state = DurabilityState.UNKNOWN.value
        rec = "The acknowledged records remote reachability result was inconclusive."
    elif has_git and remote_url:
        durability_state = DurabilityState.UNACKNOWLEDGED_REMOTE.value
        rec = "Records have a configured remote whose durability policy is not acknowledged."
    elif has_git:
        durability_state = DurabilityState.LOCAL_GIT.value
        rec = (
            "Records storage has local Git history. Configure a remote or acknowledge the "
            f"backup policy to reach the {DurabilityState.ACKNOWLEDGED_DURABLE.value} state."
        )
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
        remote_reachable=remote_reachable,
        recommendation=rec,
    )


def acknowledge_remote_durability(
    repo_path: Optional[str] = None,
    aw_home: Optional[str] = None,
    acknowledge: bool = True,
) -> StorageStatus:
    """Record or revoke explicit user acknowledgement of remote/backup policy (E-03/E-04)."""
    ctx = resolve_project_context(target_repo=repo_path, aw_home=aw_home)
    state_root = Path(ctx.logical_roots[LogicalRoot.STATE.value])
    state_root.mkdir(parents=True, exist_ok=True)

    ack_file = _get_ack_file_path(str(state_root))
    if not acknowledge:
        if ack_file.is_file():
            ack_file.unlink()
        return get_storage_status(repo_path=repo_path, aw_home=aw_home)

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


# --- Order 05 Companion Attachment and Durability Extensions ---

COMPANION_IDENTITY_RELPATH = ".aw/companion_identity.json"
LOCAL_ATTACHMENT_RELPATH = ".aw/state/durable/companion_attachment.json"


def load_companion_identity(
    companion_dir: Union[str, Path],
) -> Optional[Dict[str, Any]]:
    """Load portable companion identity from companion directory (E-01)."""
    p = Path(companion_dir) / COMPANION_IDENTITY_RELPATH
    if not p.is_file():
        p = Path(companion_dir) / "companion_identity.json"
    if not p.is_file():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def create_companion_identity(
    companion_dir: Union[str, Path],
    project_id: str,
    selected_root_classes: list[str],
    git_common_dir_hash: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Create portable companion identity record without machine-local paths (E-01)."""
    from datetime import datetime

    ident = {
        "schema_version": "1.0.0",
        "project_id": project_id,
        "selected_root_classes": selected_root_classes,
        "git_common_dir_hash": git_common_dir_hash or "",
        "created_at": datetime.now().isoformat(),
    }
    if not dry_run:
        p = Path(companion_dir) / COMPANION_IDENTITY_RELPATH
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.parent / ".companion_ident.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(ident, f, indent=2)
        os.replace(tmp, p)
    return ident


def load_local_attachment_record(
    target_repo: Union[str, Path],
) -> Optional[Dict[str, Any]]:
    """Load machine-local attachment record from target repository state (E-01)."""
    p = Path(target_repo) / LOCAL_ATTACHMENT_RELPATH
    if not p.is_file():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_local_attachment_record(
    target_repo: Union[str, Path],
    companion_dir: Union[str, Path],
    project_id: str,
    selected_root_classes: list[str],
    git_common_dir: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Write machine-local attachment record binding companion to target project (E-01)."""
    from datetime import datetime

    rec = {
        "schema_version": "1.0.0",
        "project_id": project_id,
        "companion_dir": _canonical_path(companion_dir),
        "git_common_dir": git_common_dir or "",
        "selected_root_classes": selected_root_classes,
        "attached_at": datetime.now().isoformat(),
    }
    if not dry_run:
        p = Path(target_repo) / LOCAL_ATTACHMENT_RELPATH
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.parent / ".attachment.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2)
        os.replace(tmp, p)
    return rec


def get_git_common_dir(repo_dir: Union[str, Path]) -> Optional[str]:
    """Resolve Git common directory path if repository is a Git worktree or repo."""
    try:
        res = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            cdir = res.stdout.strip()
            if not os.path.isabs(cdir):
                cdir = os.path.normpath(os.path.join(str(repo_dir), cdir))
            return _canonical_path(cdir)
    except Exception:
        pass
    return None


def validate_companion_preflight(
    target_repo: Union[str, Path],
    companion_dir: Union[str, Path],
    backend: str = "companion",
    aw_home: Optional[str] = None,
) -> Dict[str, Any]:
    """Comprehensive preflight validation for companion attachment (E-02)."""
    target_canon = _canonical_path(target_repo)
    companion_canon = _canonical_path(companion_dir)

    errors: list[str] = []
    warnings: list[str] = []

    # 1. Path traversal check
    if ".." in str(target_repo).split("/") or ".." in str(companion_dir).split("/"):
        raise StorageSecurityError(
            "Path traversal '..' detected in companion path resolution"
        )

    # 2. Accidental repo nesting check
    try:
        Path(companion_canon).relative_to(Path(target_canon))
        raise StorageSecurityError(
            f"Companion directory ({companion_canon}) cannot resolve inside target repo ({target_canon})"
        )
    except ValueError:
        pass

    try:
        Path(target_canon).relative_to(Path(companion_canon))
        raise StorageSecurityError(
            f"Target repo ({target_canon}) cannot resolve inside companion directory ({companion_canon})"
        )
    except ValueError:
        pass

    # 3. Symlink warning
    if os.path.islink(companion_canon) or os.path.islink(target_canon):
        warnings.append("Symlink detected in repository path; canonical path resolved.")

    # 4. Identity conflict check
    ident = load_companion_identity(companion_canon)
    ctx = resolve_project_context(target_repo=target_canon, aw_home=aw_home)
    target_project_id = ctx.project_id

    if ident and ident.get("project_id") and ident["project_id"] != target_project_id:
        raise IdentityConflictError(
            f"Companion repository at '{companion_canon}' belongs to project ID '{ident['project_id']}', "
            f"which conflicts with target project ID '{target_project_id}'."
        )

    # 5. Registry conflict check
    if backend == "companion" and os.path.exists(companion_canon):
        reg_data = load_registry(get_registry_path(aw_home or ctx.effective_aw_home))
        match_res = find_project(
            companion_canon,
            registry_data=reg_data,
            aw_home=aw_home or ctx.effective_aw_home,
        )
        if match_res.entry and match_res.entry.target_paths:
            if target_canon not in match_res.entry.target_paths:
                raise IdentityConflictError(
                    f"Companion storage path ({companion_canon}) is attached to project '{match_res.entry.project_id}' "
                    f"which does not include target repo '{target_canon}'"
                )

    # 6. Dirty state warning check
    if os.path.exists(os.path.join(companion_canon, ".git")):
        try:
            res = subprocess.run(
                ["git", "-C", companion_canon, "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.stdout.strip():
                warnings.append(
                    f"Companion repository at '{companion_canon}' has uncommitted changes."
                )
        except Exception:
            pass

    # 7. Public target leakage check
    if os.path.exists(os.path.join(target_canon, ".git")):
        try:
            res = subprocess.run(
                ["git", "-C", target_canon, "ls-files"],
                capture_output=True,
                text=True,
                check=False,
            )
            staged = res.stdout.splitlines()
            for f in staged:
                if "candid" in f or "private_canary" in f:
                    errors.append(
                        f"Public target leakage: tracked file '{f}' contains candid/private canary marker."
                    )
        except Exception:
            pass

    if errors:
        raise StorageSecurityError(f"Preflight failed with errors: {'; '.join(errors)}")

    return {
        "valid": True,
        "target_repo": target_canon,
        "companion_dir": companion_canon,
        "project_id": target_project_id,
        "warnings": warnings,
        "errors": errors,
        "recovery_choices": [
            "Check git status",
            "Specify distinct companion path",
            "Verify project identity",
        ],
    }


def materialize_companion_storage(
    target_repo: Union[str, Path],
    companion_dir: Union[str, Path],
    selected_root_classes: Optional[list[str]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Materialize companion storage layout and ignore rules (E-03)."""
    selected_root_classes = selected_root_classes or [
        "config",
        "durable_state",
        "records",
    ]
    comp_p = Path(companion_dir)
    deltas = []

    if not dry_run:
        comp_p.mkdir(parents=True, exist_ok=True)
        if "config" in selected_root_classes:
            (comp_p / ".aw" / "config").mkdir(parents=True, exist_ok=True)
            deltas.append("Created .aw/config/")
        if "durable_state" in selected_root_classes:
            (comp_p / ".aw" / "state" / "durable").mkdir(parents=True, exist_ok=True)
            deltas.append("Created .aw/state/durable/")
        if "records" in selected_root_classes:
            (comp_p / ".aw" / "records").mkdir(parents=True, exist_ok=True)
            deltas.append("Created .aw/records/")

        gitignore_path = comp_p / ".gitignore"
        ignore_content = ".aw/config/local.json\n.aw/state/runtime/\n"
        if gitignore_path.is_file():
            curr = gitignore_path.read_text(encoding="utf-8")
            if ".aw/state/runtime/" not in curr:
                gitignore_path.write_text(
                    curr + "\n" + ignore_content, encoding="utf-8"
                )
        else:
            gitignore_path.write_text(ignore_content, encoding="utf-8")
        deltas.append("Configured companion .gitignore ignore rules")
    else:
        deltas = [
            f"[DRY RUN] Would create companion structure at {companion_dir} for classes {selected_root_classes}"
        ]

    return {
        "companion_dir": _canonical_path(companion_dir),
        "selected_root_classes": selected_root_classes,
        "deltas": deltas,
    }


def get_git_commit_boundaries(
    target_repo: Union[str, Path],
    companion_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Report repository-specific staging and commit boundaries (E-06)."""
    target_canon = _canonical_path(target_repo)
    target_git = os.path.exists(os.path.join(target_canon, ".git"))

    companion_info = None
    if companion_dir:
        comp_canon = _canonical_path(companion_dir)
        comp_git = os.path.exists(os.path.join(comp_canon, ".git"))
        companion_info = {
            "companion_dir": comp_canon,
            "has_git": comp_git,
            "git_owner": comp_canon if comp_git else None,
            "commit_command": f"git -C {comp_canon} commit -m <msg> -- <paths>"
            if comp_git
            else None,
        }

    return {
        "target_repo": target_canon,
        "target_has_git": target_git,
        "target_git_owner": target_canon if target_git else None,
        "target_commit_command": f"git -C {target_canon} commit -m <msg> -- <paths>"
        if target_git
        else None,
        "companion": companion_info,
        "boundaries_separated": True,
    }


def attach_companion(
    target_repo: Union[str, Path],
    companion_dir: Union[str, Path],
    selected_root_classes: Optional[list[str]] = None,
    dry_run: bool = False,
    acknowledge_remote: bool = False,
    aw_home: Optional[str] = None,
) -> Dict[str, Any]:
    """Attach a companion repository to target project identity (E-05)."""
    target_str = str(target_repo)
    comp_str = str(companion_dir)
    preflight = validate_companion_preflight(
        target_str, comp_str, backend="companion", aw_home=aw_home
    )
    ctx = resolve_project_context(target_repo=target_str, aw_home=aw_home)
    classes = selected_root_classes or ["config", "durable_state", "records"]

    comp_git_common = get_git_common_dir(comp_str)
    ident = create_companion_identity(
        comp_str,
        ctx.project_id,
        classes,
        git_common_dir_hash=comp_git_common,
        dry_run=dry_run,
    )
    rec = write_local_attachment_record(
        target_str,
        comp_str,
        ctx.project_id,
        classes,
        git_common_dir=comp_git_common,
        dry_run=dry_run,
    )
    mat = materialize_companion_storage(
        target_str, comp_str, selected_root_classes=classes, dry_run=dry_run
    )

    if acknowledge_remote and not dry_run:
        acknowledge_remote_durability(
            repo_path=target_str, aw_home=aw_home, acknowledge=True
        )

    status = get_storage_status(repo_path=target_str, aw_home=aw_home)
    return {
        "target_repo": _canonical_path(target_str),
        "companion_dir": _canonical_path(comp_str),
        "project_id": ctx.project_id,
        "attached": True,
        "dry_run": dry_run,
        "identity": ident,
        "attachment_record": rec,
        "materialization": mat,
        "preflight": preflight,
        "storage_status": status.to_dict(),
    }


def detach_companion(
    target_repo: Union[str, Path],
    dry_run: bool = False,
    aw_home: Optional[str] = None,
) -> Dict[str, Any]:
    """Detach companion binding from target repo without deleting companion data (E-05)."""
    target_canon = _canonical_path(target_repo)
    p = Path(target_canon) / LOCAL_ATTACHMENT_RELPATH
    existed = p.is_file()
    if existed and not dry_run:
        p.unlink()

    return {
        "target_repo": target_canon,
        "detached": True,
        "dry_run": dry_run,
        "companion_deleted": False,
        "durable_content_preserved": True,
    }


def move_companion(
    target_repo: Union[str, Path],
    new_companion_dir: Union[str, Path],
    dry_run: bool = False,
    aw_home: Optional[str] = None,
) -> Dict[str, Any]:
    """Move companion binding to a new directory path (E-05)."""
    target_str = str(target_repo)
    new_comp_str = str(new_companion_dir)
    preflight = validate_companion_preflight(
        target_str, new_comp_str, backend="companion", aw_home=aw_home
    )
    ctx = resolve_project_context(target_repo=target_str, aw_home=aw_home)
    classes = ["config", "durable_state", "records"]
    comp_git_common = get_git_common_dir(new_comp_str)

    ident = create_companion_identity(
        new_comp_str,
        ctx.project_id,
        classes,
        git_common_dir_hash=comp_git_common,
        dry_run=dry_run,
    )
    rec = write_local_attachment_record(
        target_str,
        new_comp_str,
        ctx.project_id,
        classes,
        git_common_dir=comp_git_common,
        dry_run=dry_run,
    )

    return {
        "target_repo": _canonical_path(target_repo),
        "new_companion_dir": _canonical_path(new_companion_dir),
        "moved": True,
        "dry_run": dry_run,
        "identity": ident,
        "attachment_record": rec,
        "preflight": preflight,
    }


def reattach_companion(
    target_repo: Union[str, Path],
    companion_dir: Union[str, Path],
    dry_run: bool = False,
    aw_home: Optional[str] = None,
) -> Dict[str, Any]:
    """Reattach an existing companion repository to target project identity (E-05)."""
    return attach_companion(
        target_repo, companion_dir, dry_run=dry_run, aw_home=aw_home
    )
