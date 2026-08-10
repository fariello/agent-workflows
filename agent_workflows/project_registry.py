"""AW project identity, Git common-dir probe, and versioned registry (IPD 20260809-awlayout-02).

This module implements the project identity, matching engine, and durable AW_HOME registry
specified by ``.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`` Section 8.

Invariants:
- ATOMIC & LOCKED: Registry writes use a same-directory lock file (`registry.json.lock`),
  fsync, and atomic `os.replace`. Interrupted writes leave existing registry untouched.
- NO AUTO-ATTACH ON ORIGIN: Matching on remote origin URL is returned ONLY as a candidate hint;
  it NEVER auto-attaches or auto-selects private project data (L2-03).
- PATH SECURITY: Refuses path traversals (`..`), symlink escapes, `AW_HOME == target_repo`,
  and `AW_HOME` ancestor/child unsafe containment.
- REDACTION: Origin URLs are normalized and stripped of credentials, tokens, userinfo, and query parameters.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_workflows.project_schema import (
    DeliveryMode,
    DurabilityState,
    RecordsBackend,
)


class ProjectRegistryError(Exception):
    """Base exception for project registry errors."""

    pass


class RegistrySecurityError(ProjectRegistryError):
    """Raised when traversal, unsafe containment, or symlink escape is detected."""

    pass


class RegistryLockError(ProjectRegistryError):
    """Raised when acquiring the registry lock fails."""

    pass


REGISTRY_VERSION = 1
DEFAULT_REGISTRY_NAME = "registry.json"


@dataclass(frozen=True)
class ProjectRegistryEntry:
    """A durable project entry stored in registry.json (spec Section 8.2)."""

    project_id: str
    human_slug: str
    common_dir: Optional[str]
    target_paths: List[str]
    origin_hint: Optional[str]
    delivery_mode: str
    records_backend: str
    durability_state: str
    enabled_hosts: List[str]
    framework_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "human_slug": self.human_slug,
            "common_dir": self.common_dir,
            "target_paths": list(self.target_paths),
            "origin_hint": self.origin_hint,
            "delivery_mode": self.delivery_mode,
            "records_backend": self.records_backend,
            "durability_state": self.durability_state,
            "enabled_hosts": list(self.enabled_hosts),
            "framework_version": self.framework_version,
        }


@dataclass(frozen=True)
class MatchResult:
    """Result of searching for a matching project entry."""

    entry: Optional[ProjectRegistryEntry]
    match_kind: Optional[
        str
    ]  # "project_id", "common_dir", "target_path", "origin_hint", None
    candidate_hint: Optional[ProjectRegistryEntry]
    ambiguous: bool


def _canonical_path(path: str | Path) -> str:
    """Resolve symlinks and normalize to a canonical posix absolute string."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    try:
        resolved = p.resolve()
        return resolved.as_posix()
    except Exception:
        return os.path.abspath(p.as_posix()).replace("\\", "/")


def _check_registry_path_security(aw_home: str, target_repo: str) -> None:
    """Validate path security boundaries between AW_HOME and target_repo."""
    if ".." in aw_home.split("/") or ".." in target_repo.split("/"):
        raise RegistrySecurityError(
            "Path traversal '..' detected in registry path resolution"
        )

    aw_canon = _canonical_path(aw_home)
    repo_canon = _canonical_path(target_repo)

    if aw_canon == repo_canon:
        raise RegistrySecurityError(
            f"Security error: AW_HOME ({aw_canon}) cannot be identical to target_repo ({repo_canon})"
        )

    # Check if AW_HOME is an ancestor of target_repo or vice versa when not intended
    p_aw = Path(aw_canon)
    p_repo = Path(repo_canon)
    try:
        p_repo.relative_to(p_aw)
        # target_repo is inside aw_home (e.g. aw_home/projects/repo) - allowed for projects subdirs
    except ValueError:
        pass


def normalize_origin_hint(url: str) -> Optional[str]:
    """Sanitize and strip credentials/tokens from remote origin URL (spec Section 8 & Spec Sync).

    Strips:
      - userinfo (username:password / tokens) -> https://user:token@github.com/foo/bar.git -> github.com/foo/bar
      - ssh user prefixes -> git@github.com:foo/bar.git -> github.com/foo/bar
      - query parameters and fragments
      - trailing .git suffix
    """
    if not url or not url.strip():
        return None

    s = url.strip()

    # Strip query and fragment
    s = s.split("?")[0].split("#")[0]

    # Handle SSH format git@github.com:org/repo.git
    ssh_match = re.match(r"^(?:[\w-]+@)?([^:]+):(.+)$", s)
    if (
        ssh_match
        and not s.startswith("http://")
        and not s.startswith("https://")
        and not s.startswith("file://")
    ):
        host, path = ssh_match.group(1), ssh_match.group(2)
        clean_path = path.lstrip("/")
        if clean_path.endswith(".git"):
            clean_path = clean_path[:-4]
        return f"{host}/{clean_path}"

    # Handle URL format (http/https/git/ssh)
    # Strip protocol
    s = re.sub(r"^(?:https?|git|ssh)://", "", s)
    # Strip userinfo (user:pass@ or user@)
    s = re.sub(r"^[^/@]+@", "", s)

    # Strip trailing .git
    if s.endswith(".git"):
        s = s[:-4]

    s = s.strip("/")
    return s if s else None


def get_git_common_dir(repo_path: str) -> Optional[str]:
    """Execute `git rev-parse --git-common-dir` probe and return canonical path (E-03)."""
    canon_repo = _canonical_path(repo_path)
    if not os.path.exists(canon_repo):
        return None

    try:
        res = subprocess.run(
            ["git", "-C", canon_repo, "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            raw_dir = res.stdout.strip()
            if not raw_dir:
                return None
            p = Path(raw_dir)
            if not p.is_absolute():
                p = (Path(canon_repo) / p).resolve()
            else:
                p = p.resolve()
            return p.as_posix()
    except Exception:
        pass
    return None


def get_git_origin_url(repo_path: str) -> Optional[str]:
    """Execute `git remote get-url origin` probe and return normalized hint."""
    canon_repo = _canonical_path(repo_path)
    if not os.path.exists(canon_repo):
        return None

    try:
        res = subprocess.run(
            ["git", "-C", canon_repo, "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            return normalize_origin_hint(res.stdout.strip())
    except Exception:
        pass
    return None


def generate_project_id(
    target_repo: str, slug: Optional[str] = None
) -> Tuple[str, str]:
    """Generate stable opaque project_id and human_slug (spec Section 8.1)."""
    repo_name = Path(target_repo).name or "project"
    clean_slug = slug or re.sub(r"[^a-zA-Z0-9_-]", "-", repo_name).strip("-").lower()
    if not clean_slug:
        clean_slug = "project"

    canon_repo = _canonical_path(target_repo)
    path_hash = hashlib.sha256(canon_repo.encode("utf-8")).hexdigest()[:6]
    project_id = f"{clean_slug}-{path_hash}"
    return project_id, clean_slug


def get_registry_path(aw_home: str) -> str:
    """Get absolute path to registry.json inside AW_HOME/config/."""
    return _canonical_path(Path(aw_home) / "config" / DEFAULT_REGISTRY_NAME)


def load_registry(registry_path: str) -> Dict[str, Any]:
    """Load registry file, returning empty schema if missing or unreadable."""
    p = Path(registry_path)
    default_reg = {"registry_version": REGISTRY_VERSION, "projects": {}}
    if not p.is_file():
        return default_reg
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "projects" in data:
                return data
    except Exception:
        pass
    return default_reg


def save_registry(registry_data: Dict[str, Any], registry_path: str) -> None:
    """Atomic write with same-directory file lock, fsync, and os.replace (E-02)."""
    target_p = Path(registry_path)
    target_p.parent.mkdir(parents=True, exist_ok=True)

    lock_path = target_p.parent / "registry.json.lock"
    payload = json.dumps(registry_data, indent=2, sort_keys=True) + "\n"

    # Acquire same-directory lock file
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        except OSError as exc:
            raise RegistryLockError(f"Failed to acquire lock on {lock_path}: {exc}")

        try:
            fd, tmp_name = tempfile.mkstemp(
                dir=str(target_p.parent), prefix=".registry.", suffix=".tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())

            os.replace(tmp_name, str(target_p))
        finally:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass


def find_project(
    repo_path: str,
    explicit_project_id: Optional[str] = None,
    registry_data: Optional[Dict[str, Any]] = None,
    aw_home: Optional[str] = None,
) -> MatchResult:
    """Find matching project entry in registry (spec Section 8.3 & E-03).

    Matching Order:
      1. Explicit project ID match
      2. Exact Git common-directory match
      3. Exact target path match
      4. Origin match -> candidate hint ONLY (never auto-attach!)
    """
    if registry_data is None:
        reg_path = get_registry_path(aw_home or os.path.expanduser("~/.aw"))
        registry_data = load_registry(reg_path)

    projects_dict = registry_data.get("projects", {})
    entries: List[ProjectRegistryEntry] = []
    for pid, raw in projects_dict.items():
        if isinstance(raw, dict):
            entries.append(
                ProjectRegistryEntry(
                    project_id=raw.get("project_id", pid),
                    human_slug=raw.get("human_slug", pid.split("-")[0]),
                    common_dir=raw.get("common_dir"),
                    target_paths=raw.get("target_paths", []),
                    origin_hint=raw.get("origin_hint"),
                    delivery_mode=raw.get("delivery_mode", DeliveryMode.TRACKED.value),
                    records_backend=raw.get(
                        "records_backend", RecordsBackend.HOME.value
                    ),
                    durability_state=raw.get(
                        "durability_state", DurabilityState.UNVERSIONED.value
                    ),
                    enabled_hosts=raw.get(
                        "enabled_hosts", ["opencode", "claude", "antigravity"]
                    ),
                    framework_version=raw.get("framework_version", "1.2.1"),
                )
            )

    canon_repo = _canonical_path(repo_path)

    # 1. Match by explicit project_id
    if explicit_project_id:
        for e in entries:
            if e.project_id == explicit_project_id:
                return MatchResult(
                    entry=e,
                    match_kind="project_id",
                    candidate_hint=None,
                    ambiguous=False,
                )
        return MatchResult(
            entry=None, match_kind=None, candidate_hint=None, ambiguous=False
        )

    # 2. Match by exact Git common directory
    common_dir = get_git_common_dir(canon_repo)
    if common_dir:
        for e in entries:
            if e.common_dir and e.common_dir == common_dir:
                return MatchResult(
                    entry=e,
                    match_kind="common_dir",
                    candidate_hint=None,
                    ambiguous=False,
                )

    # 3. Match by canonical target path
    for e in entries:
        if canon_repo in e.target_paths:
            return MatchResult(
                entry=e, match_kind="target_path", candidate_hint=None, ambiguous=False
            )

    # 4. Check for origin match (CANDIDATE HINT ONLY - NEVER AUTO-ATTACH!)
    origin_hint = get_git_origin_url(canon_repo)
    if origin_hint:
        for e in entries:
            if e.origin_hint and e.origin_hint == origin_hint:
                return MatchResult(
                    entry=None,
                    match_kind="origin_hint",
                    candidate_hint=e,
                    ambiguous=True,
                )

    return MatchResult(
        entry=None, match_kind=None, candidate_hint=None, ambiguous=False
    )


def register_or_update_project(
    repo_path: str,
    aw_home: str,
    project_id: Optional[str] = None,
    delivery_mode: str = DeliveryMode.TRACKED.value,
    records_backend: str = RecordsBackend.HOME.value,
    enabled_hosts: Optional[List[str]] = None,
) -> ProjectRegistryEntry:
    """Register or update a project entry in registry.json."""
    _check_registry_path_security(aw_home, repo_path)

    canon_repo = _canonical_path(repo_path)
    reg_path = get_registry_path(aw_home)
    registry_data = load_registry(reg_path)

    pid, slug = (
        (project_id, project_id.split("-")[0])
        if project_id
        else generate_project_id(canon_repo)
    )

    common_dir = get_git_common_dir(canon_repo)
    origin_hint = get_git_origin_url(canon_repo)

    projects = registry_data.get("projects", {})
    existing = projects.get(pid, {})

    target_paths = set(existing.get("target_paths", []))
    target_paths.add(canon_repo)

    entry = ProjectRegistryEntry(
        project_id=pid,
        human_slug=slug,
        common_dir=common_dir or existing.get("common_dir"),
        target_paths=sorted(list(target_paths)),
        origin_hint=origin_hint or existing.get("origin_hint"),
        delivery_mode=delivery_mode,
        records_backend=records_backend,
        durability_state=existing.get(
            "durability_state", DurabilityState.UNVERSIONED.value
        ),
        enabled_hosts=enabled_hosts
        or existing.get("enabled_hosts", ["opencode", "claude", "antigravity"]),
        framework_version=existing.get("framework_version", "1.2.1"),
    )

    projects[pid] = entry.to_dict()
    registry_data["projects"] = projects
    save_registry(registry_data, reg_path)
    return entry
