"""Canonical schema and vocabulary for AW project layout, roots, and context (IPD 20260809-awlayout-01).

This module OWNS the machine-checkable schema and vocabulary defined by the specification
``.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md``.
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
class ProjectContext:
    """Resolved AW project context containing all Section 9 requirements (spec Section 9)."""

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

    def to_dict(self) -> Dict[str, Any]:
        return {
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
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
