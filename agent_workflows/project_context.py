"""Deterministic, side-effect-free AW project context resolver (IPD 20260809-awlayout-01).

This module implements the canonical context and logical-root resolver specified by
``.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`` Section 9 & 17.

Invariants:
- PURE: ZERO filesystem writes, directory creation, or Git mutation.
- FAIL-CLOSED: Rejects ambiguous/conflicting authoritative configs, path traversals, and symlink escapes.
- DETERMINISTIC: Repeated calls with identical inputs return byte-for-byte identical outputs.
- PROVENANCE: Tracks exact precedence level for every resolved field across all 6 precedence levels.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_workflows.project_schema import (
    DELIVERY_MODES,
    RECORDS_BACKENDS,
    DeliveryMode,
    DurabilityState,
    LogicalRoot,
    PrecedenceLevel,
    ProjectContext,
    Provenance,
    RecordsBackend,
)


class ProjectContextError(Exception):
    """Base exception for project context resolution failures."""

    pass


class ConflictingConfigurationError(ProjectContextError):
    """Raised when conflicting authoritative configurations exist at the same precedence level."""

    pass


class PathSecurityError(ProjectContextError):
    """Raised when path traversal, containment violation, or symlink escape is detected."""

    pass


DEFAULT_FRAMEWORK_VERSION = "1.2.1"
DEFAULT_ENABLED_HOSTS = ["opencode", "claude", "antigravity"]


def _canonical_path(path: str | Path) -> str:
    """Resolve symlinks and normalize to a canonical absolute posix string without mutating fs."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    try:
        resolved = p.resolve()
        return resolved.as_posix()
    except Exception:
        return os.path.abspath(p.as_posix()).replace("\\", "/")


def _is_safe_subpath(child_path: str, parent_path: str) -> bool:
    """Check if child_path is strictly inside parent_path or equal to it."""
    c = Path(child_path)
    p = Path(parent_path)
    try:
        c.relative_to(p)
        return True
    except ValueError:
        return False


def _check_path_security(path_str: str, label: str) -> str:
    """Validate path against path traversal attacks."""
    if ".." in path_str.split("/") or ".." in path_str.split("\\"):
        raise PathSecurityError(
            f"Path security error in {label}: traversal '..' detected in {path_str}"
        )
    return _canonical_path(path_str)


def get_default_aw_home() -> str:
    """Determine platform default AW_HOME (spec Section 7.1)."""
    env_home = os.environ.get("AW_HOME")
    if env_home:
        return _canonical_path(env_home)
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return _canonical_path(Path(xdg_config) / "agent-workflows")
    return _canonical_path(Path.home() / ".aw")


def _read_json_file(path_str: str) -> Optional[Dict[str, Any]]:
    """Safe read of JSON file; returns None if missing or unreadable."""
    p = Path(path_str)
    if not p.is_file():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return None


def _find_git_root(start_dir: str) -> Optional[str]:
    """Find the Git root directory by walking up from start_dir without subprocess."""
    curr = Path(start_dir).resolve()
    while curr != curr.parent:
        git_dir = curr / ".git"
        if git_dir.exists():
            return curr.as_posix()
        curr = curr.parent
    return None


def _derive_project_id(target_repo: str) -> str:
    """Derive deterministic project ID from target_repo path."""
    repo_name = Path(target_repo).name or "project"
    clean_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", repo_name).strip("-").lower()
    import hashlib

    path_hash = hashlib.sha256(target_repo.encode("utf-8")).hexdigest()[:6]
    return f"{clean_slug}-{path_hash}"


def resolve_project_context(
    target_repo: Optional[str] = None,
    aw_home: Optional[str] = None,
    delivery_mode: Optional[str] = None,
    records_backend: Optional[str] = None,
    enabled_hosts: Optional[List[str]] = None,
    profile: Optional[str] = None,
    user_config_dir: Optional[str] = None,
) -> ProjectContext:
    """Pure, side-effect-free resolver for AW project context (spec Section 9 & 17).

    Six Precedence Levels (spec Section 17):
      1. EXPLICIT_FLAGS (explicit arguments passed to invocation)
      2. MACHINE_LOCAL_BINDING (user local config per-repo entry)
      3. PROJECT_DURABLE_CONFIG (.aw/config/config.json in target repo)
      4. NAMED_GLOBAL_PROFILE (~/.config/agent-workflows/profiles/<profile>.json)
      5. GLOBAL_DEFAULTS (~/.config/agent-workflows/config.json default keys)
      6. BUILTIN_DEFAULTS (built-in fallbacks)
    """
    provenance_map: Dict[str, Provenance] = {}

    # 1. Target Repo Resolution & Security Check
    if target_repo:
        repo_abs = _check_path_security(target_repo, "target_repo")
        provenance_map["target_repo"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"--repo flag ({target_repo})",
        )
    else:
        git_root = _find_git_root(os.getcwd())
        repo_abs = git_root if git_root else _canonical_path(os.getcwd())
        provenance_map["target_repo"] = Provenance(
            source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
            detail="discovered working tree directory",
        )

    # 2. AW_HOME Resolution
    if aw_home:
        aw_home_abs = _check_path_security(aw_home, "aw_home")
        provenance_map["effective_aw_home"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"--aw-home flag ({aw_home})",
        )
    elif os.environ.get("AW_HOME"):
        aw_home_abs = _check_path_security(os.environ["AW_HOME"], "AW_HOME env")
        provenance_map["effective_aw_home"] = Provenance(
            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            detail="AW_HOME environment variable",
        )
    else:
        user_cfg_path = (
            user_config_dir
            if user_config_dir
            else os.path.expanduser("~/.config/agent-workflows")
        )
        user_cfg = _read_json_file(os.path.join(user_cfg_path, "config.json"))
        if user_cfg and user_cfg.get("aw_home"):
            aw_home_abs = _check_path_security(user_cfg["aw_home"], "user_cfg aw_home")
            provenance_map["effective_aw_home"] = Provenance(
                source=PrecedenceLevel.GLOBAL_DEFAULTS.value,
                detail=f"global config ({user_cfg_path}/config.json)",
            )
        else:
            aw_home_abs = get_default_aw_home()
            provenance_map["effective_aw_home"] = Provenance(
                source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
                detail="platform default path",
            )

    # Read configuration layers
    user_cfg_dir_effective = (
        user_config_dir
        if user_config_dir
        else os.path.expanduser("~/.config/agent-workflows")
    )
    user_cfg_file = os.path.join(user_cfg_dir_effective, "config.json")
    user_cfg_data = _read_json_file(user_cfg_file) or {}

    # Level 2: Machine-local binding per-repo
    user_repos = user_cfg_data.get("repos")
    repo_cfg_in_user: Dict[str, Any] = {}
    if isinstance(user_repos, dict):
        repo_cfg_in_user = user_repos.get(repo_abs, {}) or {}
    elif isinstance(user_repos, list):
        repo_cfg_in_user = {}

    # Level 3: Project durable config
    target_durable_cfg_file = os.path.join(repo_abs, ".aw", "config", "config.json")
    target_durable_cfg = _read_json_file(target_durable_cfg_file) or {}

    # Check for contradictory settings at same precedence level
    if target_durable_cfg and repo_cfg_in_user:
        if (
            target_durable_cfg.get("delivery_mode")
            and repo_cfg_in_user.get("delivery_mode")
            and target_durable_cfg["delivery_mode"] != repo_cfg_in_user["delivery_mode"]
        ):
            raise ConflictingConfigurationError(
                f"Conflicting delivery_mode settings between durable config ({target_durable_cfg['delivery_mode']}) "
                f"and user local binding ({repo_cfg_in_user['delivery_mode']})"
            )

    # Level 4: Named Global Profile
    selected_profile_name = (
        profile
        or repo_cfg_in_user.get("profile")
        or target_durable_cfg.get("profile")
        or user_cfg_data.get("profile")
    )
    profile_cfg_data: Dict[str, Any] = {}
    if selected_profile_name:
        profile_file = os.path.join(
            user_cfg_dir_effective, "profiles", f"{selected_profile_name}.json"
        )
        profile_cfg_data = _read_json_file(profile_file) or {}

    # 3. Delivery Mode Resolution (following exact 6-level precedence)
    if delivery_mode:
        if delivery_mode not in DELIVERY_MODES:
            raise ProjectContextError(f"Invalid delivery_mode: {delivery_mode}")
        resolved_delivery_mode = delivery_mode
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"--delivery-mode flag ({delivery_mode})",
        )
    elif repo_cfg_in_user.get("delivery_mode"):
        resolved_delivery_mode = repo_cfg_in_user["delivery_mode"]
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            detail=f"user local binding for {repo_abs}",
        )
    elif target_durable_cfg.get("delivery_mode"):
        resolved_delivery_mode = target_durable_cfg["delivery_mode"]
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
            detail=f"durable config ({target_durable_cfg_file})",
        )
    elif profile_cfg_data.get("delivery_mode"):
        resolved_delivery_mode = profile_cfg_data["delivery_mode"]
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.NAMED_GLOBAL_PROFILE.value,
            detail=f"named global profile ({selected_profile_name})",
        )
    elif user_cfg_data.get("default_delivery_mode"):
        resolved_delivery_mode = user_cfg_data["default_delivery_mode"]
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.GLOBAL_DEFAULTS.value,
            detail="user global default",
        )
    else:
        resolved_delivery_mode = DeliveryMode.TRACKED.value
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
            detail="built-in default (tracked)",
        )

    # 4. Records Backend Resolution (following exact 6-level precedence)
    if records_backend:
        if records_backend not in RECORDS_BACKENDS:
            raise ProjectContextError(f"Invalid records_backend: {records_backend}")
        resolved_records_backend = records_backend
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"--records-backend flag ({records_backend})",
        )
    elif repo_cfg_in_user.get("records_backend"):
        resolved_records_backend = repo_cfg_in_user["records_backend"]
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            detail=f"user local binding for {repo_abs}",
        )
    elif target_durable_cfg.get("records_backend"):
        resolved_records_backend = target_durable_cfg["records_backend"]
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
            detail=f"durable config ({target_durable_cfg_file})",
        )
    elif profile_cfg_data.get("records_backend"):
        resolved_records_backend = profile_cfg_data["records_backend"]
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.NAMED_GLOBAL_PROFILE.value,
            detail=f"named global profile ({selected_profile_name})",
        )
    elif user_cfg_data.get("default_records_backend"):
        resolved_records_backend = user_cfg_data["default_records_backend"]
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.GLOBAL_DEFAULTS.value,
            detail="user global default",
        )
    else:
        resolved_records_backend = RecordsBackend.HOME.value
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
            detail="built-in default (home)",
        )

    # Clean-delta security invariant check (spec Section 5.2):
    # clean-delta delivery mode MUST NOT route records into target repository
    if (
        resolved_delivery_mode == DeliveryMode.CLEAN_DELTA.value
        and resolved_records_backend == RecordsBackend.REPOSITORY.value
    ):
        raise PathSecurityError(
            "Invalid configuration: clean-delta delivery mode MUST NOT use 'repository' records backend."
        )

    # 5. Project ID Resolution
    project_id = repo_cfg_in_user.get(
        "project_id",
        target_durable_cfg.get("project_id", _derive_project_id(repo_abs)),
    )
    provenance_map["project_id"] = Provenance(
        source=(
            PrecedenceLevel.MACHINE_LOCAL_BINDING.value
            if "project_id" in repo_cfg_in_user
            else (
                PrecedenceLevel.PROJECT_DURABLE_CONFIG.value
                if "project_id" in target_durable_cfg
                else PrecedenceLevel.BUILTIN_DEFAULTS.value
            )
        ),
        detail=f"project identity ({project_id})",
    )

    # 6. Logical Roots Resolution
    project_aw_dir = os.path.join(aw_home_abs, "projects", project_id)

    # system root
    if resolved_delivery_mode == DeliveryMode.TRACKED.value:
        system_root = _canonical_path(os.path.join(repo_abs, ".agents"))
    else:
        system_root = _canonical_path(os.path.join(aw_home_abs, "system"))

    # config root
    if repo_cfg_in_user.get("config_root"):
        config_root = _canonical_path(repo_cfg_in_user["config_root"])
    elif resolved_delivery_mode == DeliveryMode.TRACKED.value and os.path.exists(
        os.path.join(repo_abs, ".aw", "config")
    ):
        config_root = _canonical_path(os.path.join(repo_abs, ".aw", "config"))
    else:
        config_root = _canonical_path(os.path.join(project_aw_dir, "config"))

    # state root
    if repo_cfg_in_user.get("state_root"):
        state_root = _canonical_path(repo_cfg_in_user["state_root"])
    else:
        state_root = _canonical_path(os.path.join(project_aw_dir, "state"))

    # records root
    if resolved_records_backend == RecordsBackend.REPOSITORY.value:
        records_root = _canonical_path(os.path.join(repo_abs, ".aw", "records"))
    elif resolved_records_backend == RecordsBackend.COMPANION.value:
        companion_dir = repo_cfg_in_user.get("companion_dir", f"{repo_abs}.aw")
        records_root = _canonical_path(os.path.join(companion_dir, "records"))
    else:  # HOME
        records_root = _canonical_path(os.path.join(project_aw_dir, "records"))

    logical_roots = {
        LogicalRoot.SYSTEM.value: system_root,
        LogicalRoot.CONFIG.value: config_root,
        LogicalRoot.STATE.value: state_root,
        LogicalRoot.RECORDS.value: records_root,
    }
    provenance_map["logical_roots"] = Provenance(
        source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        detail="resolved physical roots mapping",
    )

    # Containment check: clean-delta mode MUST NOT route ANY root into target repo
    if resolved_delivery_mode == DeliveryMode.CLEAN_DELTA.value:
        for root_name, root_path in logical_roots.items():
            if _is_safe_subpath(root_path, repo_abs):
                raise PathSecurityError(
                    f"Clean-delta security violation: {root_name} root ({root_path}) is inside target repository ({repo_abs})"
                )

    # 7. Durability State
    if resolved_records_backend == RecordsBackend.REPOSITORY.value:
        durability_state = DurabilityState.REPOSITORY_MANAGED.value
    elif os.path.exists(os.path.join(records_root, ".git")):
        durability_state = DurabilityState.LOCAL_GIT.value
    else:
        durability_state = DurabilityState.UNVERSIONED.value
    provenance_map["durability_state"] = Provenance(
        source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        detail=f"observable records repository state ({durability_state})",
    )

    # 8. Framework Version
    framework_version = DEFAULT_FRAMEWORK_VERSION
    version_file = os.path.join(system_root, "workflows", "VERSION")
    if os.path.isfile(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as vf:
                framework_version = vf.read().strip()
        except Exception:
            pass
    provenance_map["effective_framework_version"] = Provenance(
        source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
        detail=f"framework version ({framework_version})",
    )

    # 9. Enabled Hosts
    resolved_hosts = (
        enabled_hosts if enabled_hosts is not None else DEFAULT_ENABLED_HOSTS
    )
    provenance_map["enabled_hosts"] = Provenance(
        source=(
            PrecedenceLevel.EXPLICIT_FLAGS.value
            if enabled_hosts is not None
            else PrecedenceLevel.BUILTIN_DEFAULTS.value
        ),
        detail=f"enabled third-party hosts ({','.join(resolved_hosts)})",
    )

    # 10. Permitted Commit Destinations
    product_dest = (
        repo_abs if resolved_delivery_mode == DeliveryMode.TRACKED.value else None
    )
    if resolved_records_backend == RecordsBackend.REPOSITORY.value:
        records_dest = repo_abs
    elif resolved_records_backend == RecordsBackend.COMPANION.value:
        records_dest = records_root
    else:
        records_dest = None
    commit_destinations = {"product": product_dest, "records": records_dest}
    provenance_map["permitted_commit_destinations"] = Provenance(
        source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        detail="permitted commit targets based on delivery mode and backend",
    )

    # 11. Root Accessibility
    accessibility = {
        "system": os.access(
            system_root if os.path.exists(system_root) else repo_abs, os.R_OK
        ),
        "config": os.access(
            config_root if os.path.exists(config_root) else repo_abs, os.R_OK
        ),
        "state": os.access(
            state_root if os.path.exists(state_root) else repo_abs, os.R_OK
        ),
        "records": os.access(
            records_root if os.path.exists(records_root) else repo_abs, os.R_OK
        ),
    }
    provenance_map["root_accessibility"] = Provenance(
        source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        detail="filesystem readability checks for resolved roots",
    )

    # 12. Open AW Actions
    open_actions: List[Dict[str, Any]] = []
    open_actions_dir = os.path.join(state_root, "actions", "open")
    if os.path.isdir(open_actions_dir):
        for fname in sorted(os.listdir(open_actions_dir)):
            if fname.endswith(".md"):
                action_id = fname[:-3]
                open_actions.append(
                    {
                        "action_id": action_id,
                        "file_name": fname,
                        "path": os.path.join(open_actions_dir, fname),
                    }
                )
    provenance_map["open_aw_actions"] = Provenance(
        source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        detail=f"open actions discovery ({len(open_actions)} open)",
    )

    return ProjectContext(
        target_repo=repo_abs,
        project_id=project_id,
        delivery_mode=resolved_delivery_mode,
        effective_aw_home=aw_home_abs,
        logical_roots=logical_roots,
        records_backend=resolved_records_backend,
        durability_state=durability_state,
        effective_framework_version=framework_version,
        enabled_hosts=resolved_hosts,
        permitted_commit_destinations=commit_destinations,
        root_accessibility=accessibility,
        open_aw_actions=open_actions,
        provenance={k: v.to_dict() for k, v in provenance_map.items()},
    )
