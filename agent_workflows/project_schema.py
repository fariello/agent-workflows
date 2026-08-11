"""Canonical schema and vocabulary for AW project layout, roots, and context (IPD 20260810-awphysical-01).

This module OWNS the machine-checkable schema and vocabulary defined by the specification
``.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md``.
All storage, resolver, CLI, and test modules import canonical types and constants from THIS module.

Stdlib-only (Python 3.9+).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class DeliveryMode(str, Enum):
    """The coherent delivery mode (spec Section 5.1, D109)."""

    TRACKED = "tracked"
    CLEAN_DELTA = "clean-delta"


class RecordsBackend(str, Enum):
    """The records storage location (spec Section 5.2)."""

    HOME = "home"
    COMPANION = "companion"
    REPOSITORY = "repository"


class DurabilityState(str, Enum):
    """The observable durability state of records (spec Section 6.2)."""

    UNVERSIONED = "unversioned"
    LOCAL_GIT = "local-git"
    UNACKNOWLEDGED_REMOTE = "unacknowledged-remote"
    ACKNOWLEDGED_DURABLE = "acknowledged-durable"
    REPOSITORY_MANAGED = "repository-managed"
    UNREACHABLE = "unreachable"
    UNKNOWN = "unknown"


class LogicalRoot(str, Enum):
    """The four logical roots of an AW-enabled project (spec Section 4)."""

    SYSTEM = "system"
    CONFIG = "config"
    STATE = "state"
    RECORDS = "records"


class RootClass(str, Enum):
    """The six physical classes of an AW-enabled project (spec Section 4.1)."""

    SYSTEM = "system"
    CONFIG_PROJECT = "config_project"
    CONFIG_LOCAL = "config_local"
    STATE_DURABLE = "state_durable"
    STATE_RUNTIME = "state_runtime"
    RECORDS = "records"


class Placement(str, Enum):
    """The closed initial placement vocabulary (spec Section 5.1)."""

    TARGET_TRACKED = "target-tracked"
    TARGET_IGNORED = "target-ignored"
    HOME_UNTRACKED = "home-untracked"
    COMPANION_TRACKED = "companion-tracked"
    COMPANION_UNTRACKED = "companion-untracked"
    SOURCE_CHECKOUT = "source-checkout"
    CUSTOM = "custom"


class GitPolicy(str, Enum):
    """Git policy for physical classes (spec Section 5.2)."""

    TARGET_GIT = "target-git"
    COMPANION_GIT = "companion-git"
    IGNORED = "ignored"
    UNTRACKED = "untracked"


class ProjectRole(str, Enum):
    """Project role classification (spec Section 5.3 & Section 9)."""

    TARGET = "target"
    SOURCE_CHECKOUT = "source-checkout"


class Preset(str, Enum):
    """The four preset contracts (spec Section 6.1)."""

    PRIVATE_TARGET = "private-target"
    PUBLIC_TARGET_PRIVATE_COMPANION = "public-target-private-companion"
    COMPLETELY_CLEAN_TARGET = "completely-clean-target"
    LOCAL_ONLY = "local-only"


ROOT_CLASSES: Tuple[str, ...] = tuple(c.value for c in RootClass)
PLACEMENTS: Tuple[str, ...] = tuple(p.value for p in Placement)
GIT_POLICIES: Tuple[str, ...] = tuple(g.value for g in GitPolicy)
PROJECT_ROLES: Tuple[str, ...] = tuple(r.value for r in ProjectRole)
PRESETS: Tuple[str, ...] = tuple(p.value for p in Preset)


@dataclass(frozen=True)
class PlacementInfo:
    """Detailed attributes for a given Placement (spec Section 5.1)."""

    placement: str
    containment: str
    git_policy: str
    portability: str
    durability: str
    privacy: str
    clean_target: bool


PLACEMENT_DETAILS: Dict[str, PlacementInfo] = {
    Placement.TARGET_TRACKED.value: PlacementInfo(
        placement=Placement.TARGET_TRACKED.value,
        containment="target",
        git_policy=GitPolicy.TARGET_GIT.value,
        portability="portable",
        durability="durable",
        privacy="target-governed",
        clean_target=False,
    ),
    Placement.TARGET_IGNORED.value: PlacementInfo(
        placement=Placement.TARGET_IGNORED.value,
        containment="target",
        git_policy=GitPolicy.IGNORED.value,
        portability="local",
        durability="transient",
        privacy="target-local",
        clean_target=False,
    ),
    Placement.HOME_UNTRACKED.value: PlacementInfo(
        placement=Placement.HOME_UNTRACKED.value,
        containment="aw_home",
        git_policy=GitPolicy.UNTRACKED.value,
        portability="local",
        durability="transient",
        privacy="private",
        clean_target=True,
    ),
    Placement.COMPANION_TRACKED.value: PlacementInfo(
        placement=Placement.COMPANION_TRACKED.value,
        containment="companion",
        git_policy=GitPolicy.COMPANION_GIT.value,
        portability="portable",
        durability="durable",
        privacy="companion-governed",
        clean_target=True,
    ),
    Placement.COMPANION_UNTRACKED.value: PlacementInfo(
        placement=Placement.COMPANION_UNTRACKED.value,
        containment="companion",
        git_policy=GitPolicy.UNTRACKED.value,
        portability="local",
        durability="transient",
        privacy="companion-local",
        clean_target=True,
    ),
    Placement.SOURCE_CHECKOUT.value: PlacementInfo(
        placement=Placement.SOURCE_CHECKOUT.value,
        containment="source_repo",
        git_policy=GitPolicy.TARGET_GIT.value,
        portability="portable",
        durability="durable",
        privacy="source-governed",
        clean_target=False,
    ),
    Placement.CUSTOM.value: PlacementInfo(
        placement=Placement.CUSTOM.value,
        containment="custom",
        git_policy=GitPolicy.UNTRACKED.value,
        portability="custom",
        durability="custom",
        privacy="custom",
        clean_target=False,
    ),
}


PRESET_PLACEMENTS: Dict[str, Dict[str, str]] = {
    Preset.PRIVATE_TARGET.value: {
        RootClass.SYSTEM.value: Placement.TARGET_TRACKED.value,
        RootClass.CONFIG_PROJECT.value: Placement.TARGET_TRACKED.value,
        RootClass.CONFIG_LOCAL.value: Placement.TARGET_IGNORED.value,
        RootClass.STATE_DURABLE.value: Placement.TARGET_TRACKED.value,
        RootClass.STATE_RUNTIME.value: Placement.TARGET_IGNORED.value,
        RootClass.RECORDS.value: Placement.TARGET_TRACKED.value,
    },
    Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value: {
        RootClass.SYSTEM.value: Placement.TARGET_TRACKED.value,
        RootClass.CONFIG_PROJECT.value: Placement.COMPANION_TRACKED.value,
        RootClass.CONFIG_LOCAL.value: Placement.HOME_UNTRACKED.value,
        RootClass.STATE_DURABLE.value: Placement.COMPANION_TRACKED.value,
        RootClass.STATE_RUNTIME.value: Placement.HOME_UNTRACKED.value,
        RootClass.RECORDS.value: Placement.COMPANION_TRACKED.value,
    },
    Preset.COMPLETELY_CLEAN_TARGET.value: {
        RootClass.SYSTEM.value: Placement.HOME_UNTRACKED.value,
        RootClass.CONFIG_PROJECT.value: Placement.HOME_UNTRACKED.value,
        RootClass.CONFIG_LOCAL.value: Placement.HOME_UNTRACKED.value,
        RootClass.STATE_DURABLE.value: Placement.HOME_UNTRACKED.value,
        RootClass.STATE_RUNTIME.value: Placement.HOME_UNTRACKED.value,
        RootClass.RECORDS.value: Placement.HOME_UNTRACKED.value,
    },
    Preset.LOCAL_ONLY.value: {
        RootClass.SYSTEM.value: Placement.HOME_UNTRACKED.value,
        RootClass.CONFIG_PROJECT.value: Placement.HOME_UNTRACKED.value,
        RootClass.CONFIG_LOCAL.value: Placement.HOME_UNTRACKED.value,
        RootClass.STATE_DURABLE.value: Placement.HOME_UNTRACKED.value,
        RootClass.STATE_RUNTIME.value: Placement.HOME_UNTRACKED.value,
        RootClass.RECORDS.value: Placement.HOME_UNTRACKED.value,
    },
}


def get_placement_info(placement_name: str) -> PlacementInfo:
    """Retrieve PlacementInfo for a given placement string (spec Section 5.1)."""
    if placement_name not in PLACEMENT_DETAILS:
        raise ValueError(f"Unknown placement: {placement_name!r}")
    return PLACEMENT_DETAILS[placement_name]


def get_preset_placements(preset_name: str) -> Dict[str, str]:
    """Retrieve the physical root placement mapping for a preset (spec Section 6.1)."""
    if preset_name not in PRESET_PLACEMENTS:
        raise ValueError(f"Unknown preset: {preset_name!r}")
    return dict(PRESET_PLACEMENTS[preset_name])


def validate_placement_combination(root_class: str, placement: str) -> bool:
    """Validate physical placement rules (spec Section 5.1).
    Rule: config_local and state_runtime MUST NOT be tracked in any Git repository.
    Rule: root_class and placement must be known schema values.
    """
    if root_class not in ROOT_CLASSES:
        return False
    if placement not in PLACEMENTS:
        return False

    if root_class in (RootClass.CONFIG_LOCAL.value, RootClass.STATE_RUNTIME.value):
        if placement in (
            Placement.TARGET_TRACKED.value,
            Placement.COMPANION_TRACKED.value,
            Placement.SOURCE_CHECKOUT.value,
        ):
            return False
    return True


def parse_physical_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate raw physical layout configuration dictionary.
    Fails closed on unknown future or invalid values.
    """
    if not isinstance(config_dict, dict):
        raise ValueError("Configuration must be a dictionary")

    parsed: Dict[str, Any] = {}

    if "preset" in config_dict:
        preset_val = config_dict["preset"]
        if preset_val not in PRESETS:
            raise ValueError(f"Unknown preset: {preset_val!r}")
        parsed["preset"] = preset_val

    if "role" in config_dict:
        role_val = config_dict["role"]
        if role_val not in PROJECT_ROLES:
            raise ValueError(f"Unknown project role: {role_val!r}")
        parsed["role"] = role_val

    if "placements" in config_dict:
        placements_dict = config_dict["placements"]
        if not isinstance(placements_dict, dict):
            raise ValueError("Placements must be a dictionary")
        parsed_placements: Dict[str, str] = {}
        for r_cls, plc in placements_dict.items():
            if r_cls not in ROOT_CLASSES:
                raise ValueError(f"Unknown physical root class: {r_cls!r}")
            if plc not in PLACEMENTS:
                raise ValueError(f"Unknown placement: {plc!r}")
            if not validate_placement_combination(r_cls, plc):
                raise ValueError(
                    f"Invalid placement combination: root class {r_cls!r} cannot use placement {plc!r}"
                )
            parsed_placements[r_cls] = plc
        parsed["placements"] = parsed_placements

    return parsed


def validate_physical_matrix(
    target_repo: str,
    physical_classes: Dict[str, str],
    placements: Dict[str, str],
) -> None:
    """Validate physical policy matrix invariants (spec Section 5.1 & Section 7).
    Refuses symlinks escaping target boundaries for target-contained classes.
    """
    from pathlib import Path

    repo_p = Path(target_repo).resolve()
    for r_cls, path_str in physical_classes.items():
        plc = placements.get(r_cls)
        if not plc:
            continue
        p = Path(path_str)
        if plc in (Placement.TARGET_TRACKED.value, Placement.TARGET_IGNORED.value):
            if p.is_symlink():
                target_dest = p.resolve()
                try:
                    target_dest.relative_to(repo_p)
                except ValueError:
                    from agent_workflows.project_context import PathSecurityError

                    raise PathSecurityError(
                        f"Symlink escape violation: physical class {r_cls!r} at {p} points outside target repository to {target_dest}"
                    )


DELIVERY_MODES: Tuple[str, ...] = tuple(m.value for m in DeliveryMode)
RECORDS_BACKENDS: Tuple[str, ...] = tuple(b.value for b in RecordsBackend)
DURABILITY_STATES: Tuple[str, ...] = tuple(d.value for d in DurabilityState)
LEGACY_DURABILITY_STATE_ALIASES = {
    "durable-private": DurabilityState.ACKNOWLEDGED_DURABLE.value,
}


def normalize_durability_state(value: str) -> str:
    """Normalize a historical durability value without weakening validation."""

    normalized = LEGACY_DURABILITY_STATE_ALIASES.get(value, value)
    if normalized not in DURABILITY_STATES:
        raise ValueError(f"unknown durability state: {value!r}")
    return normalized


LOGICAL_ROOTS: Tuple[str, ...] = tuple(r.value for r in LogicalRoot)


class PrecedenceLevel(str, Enum):
    """The six deterministic resolution precedence levels (spec Section 17)."""

    EXPLICIT_FLAGS = "explicit_flags"
    MACHINE_LOCAL_BINDING = "machine_local_binding"
    PROJECT_DURABLE_CONFIG = "project_durable_config"
    NAMED_GLOBAL_PROFILE = "named_global_profile"
    GLOBAL_DEFAULTS = "global_defaults"
    BUILTIN_DEFAULTS = "builtin_defaults"


PRECEDENCE_ORDER: Tuple[str, ...] = tuple(p.value for p in PrecedenceLevel)


@dataclass(frozen=True)
class Provenance:
    """Provenance details for a resolved context value (spec Section 17)."""

    source: str
    detail: str

    def to_dict(self) -> Dict[str, str]:
        return {"source": self.source, "detail": self.detail}


@dataclass(frozen=True)
class RootAccessibility:
    """Per-root accessibility flags (spec Section 9)."""

    system: bool = True
    config: bool = True
    state: bool = True
    records: bool = True

    def to_dict(self) -> Dict[str, bool]:
        return {
            "system": self.system,
            "config": self.config,
            "state": self.state,
            "records": self.records,
        }


@dataclass(frozen=True)
class PermittedCommitDestinations:
    """Permitted commit destinations for product changes and records (spec Section 9)."""

    product: Optional[str]
    records: Optional[str]

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {"product": self.product, "records": self.records}


@dataclass(frozen=True)
class ProjectIdentity:
    """Stable project identity details (spec Section 8)."""

    project_id: str
    human_slug: str
    common_dir: Optional[str] = None
    worktree_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "human_slug": self.human_slug,
            "common_dir": self.common_dir,
            "worktree_path": self.worktree_path,
        }


@dataclass(frozen=True)
class ProjectPolicySchema:
    """Portable project policy schema for .aw/config/project.json (spec Section 4.2 & 10)."""

    schema_version: int = 2
    preset: str = Preset.PRIVATE_TARGET.value
    role: str = ProjectRole.TARGET.value
    placements: Dict[str, str] = None  # type: ignore
    git_policies: Dict[str, str] = None  # type: ignore
    enabled_hosts: List[str] = None  # type: ignore
    non_secret_consent: Dict[str, bool] = None  # type: ignore
    unknown_fields: Dict[str, Any] = None  # type: ignore

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "preset": self.preset,
            "role": self.role,
            "placements": dict(self.placements or {}),
            "git_policies": dict(self.git_policies or {}),
            "enabled_hosts": list(self.enabled_hosts or []),
            "non_secret_consent": dict(self.non_secret_consent or {}),
        }
        if self.unknown_fields:
            for k, v in self.unknown_fields.items():
                if k not in res:
                    res[k] = v
        return res


@dataclass(frozen=True)
class LocalBindingSchema:
    """Machine-local binding schema for .aw/config/local.json (spec Section 4.2 & 10)."""

    schema_version: int = 2
    project_id: str = ""
    human_slug: str = ""
    common_dir: Optional[str] = None
    worktree_path: Optional[str] = None
    companion_dir: Optional[str] = None
    runtime_overrides: Dict[str, Any] = None  # type: ignore
    local_aliases: Dict[str, str] = None  # type: ignore
    unknown_fields: Dict[str, Any] = None  # type: ignore

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "human_slug": self.human_slug,
            "common_dir": self.common_dir,
            "worktree_path": self.worktree_path,
            "companion_dir": self.companion_dir,
            "runtime_overrides": dict(self.runtime_overrides or {}),
            "local_aliases": dict(self.local_aliases or {}),
        }
        if self.unknown_fields:
            for k, v in self.unknown_fields.items():
                if k not in res:
                    res[k] = v
        return res


def parse_portable_policy(data: Dict[str, Any]) -> ProjectPolicySchema:
    """Strict parsing and fail-closed validation of project.json policy."""
    ver = data.get("schema_version", 2)
    if ver > 2:
        raise ValueError(
            f"Unsupported schema_version {ver}: exceeds current supported version 2"
        )

    preset_str = data.get("preset", Preset.PRIVATE_TARGET.value)
    if preset_str not in PRESETS and preset_str != "custom":
        raise ValueError(f"Unknown preset: {preset_str!r}")

    role_str = data.get("role", ProjectRole.TARGET.value)
    if role_str not in PROJECT_ROLES:
        raise ValueError(f"Unknown project role: {role_str!r}")

    known_keys = {
        "schema_version",
        "preset",
        "role",
        "placements",
        "git_policies",
        "enabled_hosts",
        "non_secret_consent",
        "delivery_mode",
        "records_backend",
    }
    unknown_fields = {k: v for k, v in data.items() if k not in known_keys}

    placements = data.get("placements", {})
    git_policies = data.get("git_policies", {})

    return ProjectPolicySchema(
        schema_version=ver,
        preset=preset_str,
        role=role_str,
        placements=dict(placements),
        git_policies=dict(git_policies),
        enabled_hosts=list(
            data.get("enabled_hosts", ["opencode", "claude", "antigravity"])
        ),
        non_secret_consent=dict(data.get("non_secret_consent", {})),
        unknown_fields=unknown_fields,
    )


def parse_local_binding(data: Dict[str, Any]) -> LocalBindingSchema:
    """Strict parsing and fail-closed validation of local.json binding."""
    ver = data.get("schema_version", 2)
    if ver > 2:
        raise ValueError(
            f"Unsupported schema_version {ver}: exceeds current supported version 2"
        )

    known_keys = {
        "schema_version",
        "project_id",
        "human_slug",
        "common_dir",
        "worktree_path",
        "companion_dir",
        "runtime_overrides",
        "local_aliases",
    }
    unknown_fields = {k: v for k, v in data.items() if k not in known_keys}

    return LocalBindingSchema(
        schema_version=ver,
        project_id=data.get("project_id", ""),
        human_slug=data.get("human_slug", ""),
        common_dir=data.get("common_dir"),
        worktree_path=data.get("worktree_path"),
        companion_dir=data.get("companion_dir"),
        runtime_overrides=dict(data.get("runtime_overrides", {})),
        local_aliases=dict(data.get("local_aliases", {})),
        unknown_fields=unknown_fields,
    )


def migrate_legacy_config(
    legacy_data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Migrate shipped or legacy .aw/config/config.json or policy.json into portable & local parts.
    Preserves human-owned unknown keys in their respective targets.
    """
    ver = legacy_data.get("schema_version", 1)
    if ver > 2:
        raise ValueError(
            f"Unsupported legacy schema_version {ver}: exceeds current supported version 2"
        )

    # Portable fields
    preset = legacy_data.get("preset", Preset.PRIVATE_TARGET.value)
    role = legacy_data.get("role", ProjectRole.TARGET.value)

    # Infer placements/git_policies if legacy config has delivery_mode or records_backend
    placements = dict(legacy_data.get("placements", {}))
    git_policies = dict(legacy_data.get("git_policies", {}))

    if (
        legacy_data.get("records_backend") == "companion"
        or legacy_data.get("delivery_mode") == "clean-delta"
    ):
        preset = Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value

    if not placements:
        placements = get_preset_placements(preset)

    portable_dict: Dict[str, Any] = {
        "schema_version": 2,
        "preset": preset,
        "role": role,
        "placements": placements,
        "git_policies": git_policies,
        "enabled_hosts": legacy_data.get(
            "enabled_hosts", ["opencode", "claude", "antigravity"]
        ),
        "non_secret_consent": legacy_data.get("non_secret_consent", {}),
    }

    # Machine-local fields
    local_dict: Dict[str, Any] = {
        "schema_version": 2,
        "project_id": legacy_data.get("project_id", ""),
        "human_slug": legacy_data.get("human_slug", ""),
        "common_dir": legacy_data.get("common_dir"),
        "worktree_path": legacy_data.get("worktree_path"),
        "companion_dir": legacy_data.get("companion_dir"),
        "runtime_overrides": legacy_data.get("runtime_overrides", {}),
        "local_aliases": legacy_data.get("local_aliases", {}),
    }

    # Preserve unknown keys
    known_portable = {
        "schema_version",
        "preset",
        "role",
        "placements",
        "git_policies",
        "enabled_hosts",
        "non_secret_consent",
        "delivery_mode",
        "records_backend",
    }
    known_local = {
        "schema_version",
        "project_id",
        "human_slug",
        "common_dir",
        "worktree_path",
        "companion_dir",
        "runtime_overrides",
        "local_aliases",
    }

    for k, v in legacy_data.items():
        if k not in known_portable and k not in known_local:
            # Place unknown field into portable_dict by default
            portable_dict[k] = v

    return portable_dict, local_dict


def atomic_save_json(
    path_str: str, data: Dict[str, Any], no_clobber: bool = False
) -> None:
    """Atomic write of JSON object with optional no_clobber protection."""
    import tempfile
    import os
    from pathlib import Path

    p = Path(path_str)
    if no_clobber and p.exists():
        raise FileExistsError(
            f"Target config file already exists and no_clobber is True: {path_str}"
        )

    p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=p.parent, delete=False, encoding="utf-8"
    ) as tf:
        json.dump(data, tf, indent=2)
        tmp_name = tf.name

    os.replace(tmp_name, p)


@dataclass(frozen=True)
class ProjectContext:
    """Resolved AW project context containing all Section 9 & Order 02 requirements (spec Section 9)."""

    target_repo: str
    project_id: str
    delivery_mode: str
    effective_aw_home: str
    logical_roots: Dict[str, str]
    records_backend: str
    durability_state: str
    effective_framework_version: str
    enabled_hosts: List[str]
    permitted_commit_destinations: Dict[str, Optional[str]]
    root_accessibility: Dict[str, bool]
    open_aw_actions: List[Dict[str, Any]]
    provenance: Dict[str, Dict[str, str]]
    physical_classes: Optional[Dict[str, str]] = None
    git_policies: Optional[Dict[str, str]] = None
    project_role: str = ProjectRole.TARGET.value
    preset: str = Preset.PRIVATE_TARGET.value
    is_configured: bool = True

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "target_repo": self.target_repo,
            "project_id": self.project_id,
            "delivery_mode": self.delivery_mode,
            "effective_aw_home": self.effective_aw_home,
            "logical_roots": dict(self.logical_roots),
            "records_backend": self.records_backend,
            "durability_state": self.durability_state,
            "effective_framework_version": self.effective_framework_version,
            "enabled_hosts": list(self.enabled_hosts),
            "permitted_commit_destinations": dict(self.permitted_commit_destinations),
            "root_accessibility": dict(self.root_accessibility),
            "open_aw_actions": [dict(a) for a in self.open_aw_actions],
            "provenance": {k: dict(v) for k, v in self.provenance.items()},
            "project_role": self.project_role,
            "preset": self.preset,
            "is_configured": self.is_configured,
        }
        if self.physical_classes:
            d["physical_classes"] = dict(self.physical_classes)
        if self.git_policies:
            d["git_policies"] = dict(self.git_policies)
        return d

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
