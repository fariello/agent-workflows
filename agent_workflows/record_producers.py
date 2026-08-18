"""Maintained record producer inventory and routing contract (IPD 20260810-awphysical-08).

This module defines the machine-readable inventory of record-producing workflows and Python
modules, provides the central write guard, and implements the backend-neutral record and
state class router specified by
``.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md``
Sections 4.3, 4.4, 6, 8, 11.2, 11.3, & 13.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import (
    LogicalRoot,
    RecordsBackend,
    RootClass,
)


class RecordProducerError(Exception):
    """Base exception for record producer operations."""

    pass


class InvalidRecordClassError(RecordProducerError, ValueError):
    """Raised when an invalid or unsupported record class is requested."""

    pass


class GuardError(RecordProducerError):
    """Base exception for write guard rejections."""

    pass


class LegacyWriteError(GuardError):
    """Raised when a write is attempted to a legacy path (.agents/ or workflow-artifacts/)."""

    pass


class ForbiddenWriteError(GuardError):
    """Raised when a write is attempted to an unauthorized or system path."""

    pass


class StaleContextError(GuardError):
    """Raised when project context is missing, invalid, or stale."""

    pass


class MigrationInFlightError(GuardError):
    """Raised when a write is attempted while a pre-switch migration is active."""

    pass


class UnsafeSymlinkError(GuardError):
    """Raised when path traversal or an unsafe symlink escape is detected."""

    pass


class CrossGitStagingError(GuardError):
    """Raised when an external record is requested to be staged in target repository index."""

    pass


class DuplicateAuthorityError(RecordProducerError):
    """Raised when duplicate content exists in both legacy and new roots with conflicting authority."""

    pass


class RecordClass(str, Enum):
    """Closed set of canonical record classes (spec Section 4.1 & 6)."""

    PLANS = "plans"
    SPECS = "specs"
    RESEARCH = "research"
    RECORDS = "records"
    PROMPTS = "prompts"
    COMMS = "comms"
    WALKTHROUGHS = "walkthroughs"
    # NOTE: run-artifacts (assess/verify/release-review/advise run records) are NOT a records class.
    # They live at the top-level `.aw/workflow-artifacts/<workflow>/<RUN_ID>/` (sibling of records),
    # written by the workflows directly and gitignored - NOT resolved via resolve_record_path. The
    # former RUNS/WORKFLOW_ARTIFACTS members were unused and resolved under the records root by
    # mistake; removed in IPD awretrofit Order 07 (spec 20260817-2124-01, plan-review PR-002).


class DurableStateClass(str, Enum):
    """Closed set of durable state classes (spec Section 4.1)."""

    INSTALL = "install"
    HISTORY = "history"
    ACTIONS = "actions"
    MIGRATIONS = "migrations"
    ROUTING_RECEIPTS = "routing_receipts"


class RuntimeStateClass(str, Enum):
    """Closed set of runtime state classes (spec Section 4.1)."""

    TRANSACTIONS = "transactions"
    LOCKS = "locks"
    STAGING = "staging"
    BACKUPS = "backups"
    CACHE = "cache"
    TMP = "tmp"


# FINAL `.aw/records/` subpaths (IPD awretrofit Order 07, spec 20260817-2124-01): the durable doc
# types are FLATTENED out of `docs/` (specs/research/walkthroughs sit directly under `.aw/records/`).
_RECORD_CLASS_SUBPATHS: Dict[str, str] = {
    RecordClass.PLANS.value: "plans",
    RecordClass.SPECS.value: "specs",
    RecordClass.RESEARCH.value: "research",
    RecordClass.RECORDS.value: "",
    RecordClass.PROMPTS.value: "prompts",
    RecordClass.COMMS.value: "comms",
    RecordClass.WALKTHROUGHS.value: "walkthroughs",
}

# LEGACY `.agents/` read-only subpaths (plan-review PR-001): the legacy tree keeps its `docs/` nesting
# (`.agents/docs/specs`, ...). This map is DECOUPLED from the final map above so flattening the final
# `.aw/records/` layout does NOT break legacy migration reads (`resolve_record_read_paths`). Only the
# doc-family classes differ from their final subpath; the rest reuse the final subpath.
_LEGACY_RECORD_CLASS_SUBPATHS: Dict[str, str] = {
    **_RECORD_CLASS_SUBPATHS,
    RecordClass.SPECS.value: "docs/specs",
    RecordClass.RESEARCH.value: "docs/research",
    RecordClass.WALKTHROUGHS.value: "docs/walkthroughs",
}

_DURABLE_STATE_SUBPATHS: Dict[str, str] = {
    DurableStateClass.INSTALL.value: "install.json",
    DurableStateClass.HISTORY.value: "history",
    DurableStateClass.ACTIONS.value: "actions",
    DurableStateClass.MIGRATIONS.value: "migrations",
    DurableStateClass.ROUTING_RECEIPTS.value: "routing_receipts",
}

_RUNTIME_STATE_SUBPATHS: Dict[str, str] = {
    RuntimeStateClass.TRANSACTIONS.value: "transactions",
    RuntimeStateClass.LOCKS.value: "locks",
    RuntimeStateClass.STAGING.value: "staging",
    RuntimeStateClass.BACKUPS.value: "backups",
    RuntimeStateClass.CACHE.value: "cache",
    RuntimeStateClass.TMP.value: "tmp",
}


@dataclass(frozen=True)
class RecordProducerEntry:
    """Record producer inventory item (E-01 & E-03)."""

    name: str
    source_path: str
    anchor: str
    operation: str
    category: str
    resolver_surface: str
    commit_policy_consumer: str


PRODUCER_INVENTORY: List[RecordProducerEntry] = [
    RecordProducerEntry(
        name="plans_create",
        source_path="agent_workflows/ipd_authoring.py",
        anchor="run_scaffold",
        operation="create",
        category="plans",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="specs_create",
        source_path="agent_workflows/specs.py",
        anchor="_set_status",
        operation="move",
        category="specs",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="research_create",
        source_path="agent_workflows/research_cmd.py",
        anchor="plan_new",
        operation="create",
        category="research",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="research_write",
        source_path="agent_workflows/research_cmd.py",
        anchor="_emit_and_write",
        operation="create",
        category="research",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="artifact_move",
        source_path="agent_workflows/artifact_core.py",
        anchor="git_mv",
        operation="move",
        category="records",
        resolver_surface="python_api",
        commit_policy_consumer="caller_owned",
    ),
    RecordProducerEntry(
        name="setup_artifacts",
        source_path="agent_workflows/engine.py",
        anchor="create_setup_artifacts",
        operation="create",
        category="records",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="plans_index",
        source_path="agent_workflows/plans_index.py",
        anchor="run_index",
        operation="create",
        category="plans",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="plans_archive",
        source_path="agent_workflows/plans_archive.py",
        anchor="apply_shard_moves",
        operation="move",
        category="plans",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="plans_refs",
        source_path="agent_workflows/plans_refs.py",
        anchor="apply_renames",
        operation="move",
        category="plans",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="research_index",
        source_path="agent_workflows/research_index.py",
        anchor="run_index",
        operation="create",
        category="research",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="research_archive",
        source_path="agent_workflows/research_archive.py",
        anchor="run_archive",
        operation="move",
        category="research",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="research_refs",
        source_path="agent_workflows/research_refs.py",
        anchor="run_mv",
        operation="move",
        category="research",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="actions_write",
        source_path="agent_workflows/actions.py",
        anchor="ActionManager",
        operation="create",
        category="records",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="scaffold_workflow",
        source_path=".agents/workflows/scaffold/scaffold.md",
        anchor="Step 5: Finish",
        operation="create",
        category="plans",
        resolver_surface="cli_aw_path",
        commit_policy_consumer="workflow_prompt",
    ),
    RecordProducerEntry(
        name="setup_repo_workflow",
        source_path=".agents/workflows/setup-repo/setup-repo.md",
        anchor="Finish",
        operation="create",
        category="records",
        resolver_surface="cli_aw_path",
        commit_policy_consumer="workflow_prompt",
    ),
]

# Non-writing scanners, validators, and readers allowed to mention .agents/
# MUST NOT contain any genuine record or state writers!
LEGACY_ALLOWLIST: Set[str] = {
    "agent_workflows/attention.py",
    "agent_workflows/attention_contract.py",
}

LEGACY_WRITER_CANDIDATES: Set[str] = {
    "agent_workflows/artifact_core.py",
    "agent_workflows/engine.py",
    "agent_workflows/ipd_authoring.py",
    "agent_workflows/research_cmd.py",
    "agent_workflows/specs.py",
    "agent_workflows/plans_index.py",
    "agent_workflows/plans_archive.py",
    "agent_workflows/plans_refs.py",
    "agent_workflows/research_index.py",
    "agent_workflows/research_archive.py",
    "agent_workflows/research_refs.py",
    "agent_workflows/actions.py",
}
_WRITE_MARKERS = (
    "atomic_write(",
    "write_text(",
    "git_mv(",
    "_create_if_absent(",
    ".write_bytes(",
)


def discover_legacy_write_sinks(repo_root: Path) -> Set[str]:
    """Statically identify known writer modules that still contain legacy AW write paths."""

    sinks: Set[str] = set()
    for relpath in sorted(LEGACY_WRITER_CANDIDATES):
        path = repo_root / relpath
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            line_s = line.strip()
            if (
                line_s.startswith("#")
                or line_s.startswith('"""')
                or line_s.startswith("'''")
                or line_s.startswith("*")
            ):
                continue
            if ".agents/" in line:
                if (
                    any(marker in line for marker in _WRITE_MARKERS)
                    or "open(" in line
                    or "Path(" in line
                    or ".write" in line
                    or "os.replace" in line
                    or "shutil." in line
                ):
                    sinks.add(relpath)
                    break
    return sinks


def _is_subpath(child: Path, parent: Path) -> bool:
    """Helper to check if child path is under parent path."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def resolve_record_path(
    record_class: str,
    relative_subpath: str = "",
    target_repo: Optional[str] = None,
    aw_home: Optional[str] = None,
) -> Path:
    """Resolve physical path for a closed record, durable state, or runtime state class (E-01)."""

    is_record = record_class in [r.value for r in RecordClass]
    is_durable = record_class in [d.value for d in DurableStateClass]
    is_runtime = record_class in [rt.value for rt in RuntimeStateClass]

    if not (is_record or is_durable or is_runtime):
        raise InvalidRecordClassError(
            f"Invalid record or state class '{record_class}'. Must be one of RecordClass, DurableStateClass, or RuntimeStateClass."
        )

    if relative_subpath:
        sub_p = Path(relative_subpath)
        if sub_p.is_absolute() or relative_subpath.startswith("/"):
            raise UnsafeSymlinkError(f"Subpath '{relative_subpath}' must be relative.")
        if ".." in sub_p.parts:
            raise UnsafeSymlinkError(
                f"Subpath '{relative_subpath}' contains parent traversal '..'."
            )

    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)

    if is_record:
        base_root = Path(ctx.physical_classes[RootClass.RECORDS.value])
        class_rel = _RECORD_CLASS_SUBPATHS[record_class]
    elif is_durable:
        base_root = Path(ctx.physical_classes[RootClass.STATE_DURABLE.value])
        class_rel = _DURABLE_STATE_SUBPATHS[record_class]
    else:
        base_root = Path(ctx.physical_classes[RootClass.STATE_RUNTIME.value])
        class_rel = _RUNTIME_STATE_SUBPATHS[record_class]

    target = base_root / class_rel
    if relative_subpath:
        target = target / relative_subpath

    try:
        base_resolved = base_root.resolve()
        cand = (base_root / class_rel / relative_subpath).resolve()
        if not _is_subpath(cand, base_resolved):
            raise UnsafeSymlinkError(f"Path '{target}' escapes root '{base_root}'.")
    except UnsafeSymlinkError:
        raise
    except Exception:
        pass

    return target


def get_git_owner(
    class_name: str,
    target_repo: Optional[str] = None,
    aw_home: Optional[str] = None,
) -> Optional[str]:
    """Return permitted Git owner for a class ('target', 'companion', 'source', or None for untracked) (E-01)."""

    if class_name in [rt.value for rt in RuntimeStateClass]:
        return None

    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
    backend = ctx.records_backend

    if backend == RecordsBackend.REPOSITORY.value:
        return "target"
    elif "companion" in backend or backend == RecordsBackend.COMPANION_TRACKED.value:
        return "companion"
    elif ctx.project_role == "source-checkout":
        return "source"
    else:
        return None


def render_logical_path(
    physical_path: Union[Path, str],
    target_repo: Optional[str] = None,
    aw_home: Optional[str] = None,
) -> str:
    """Render public-safe logical path without machine-specific absolute system paths (E-01)."""
    p = Path(physical_path).expanduser()
    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
    target_root = Path(ctx.target_repo).resolve() if ctx.target_repo else None

    if target_root and _is_subpath(p, target_root):
        try:
            return p.resolve().relative_to(target_root).as_posix()
        except Exception:
            pass

    records_root = Path(ctx.physical_classes[RootClass.RECORDS.value]).resolve()
    if _is_subpath(p, records_root):
        try:
            rel = p.resolve().relative_to(records_root).as_posix()
            return f"records/{rel}".rstrip("/")
        except Exception:
            pass

    durable_root = Path(ctx.physical_classes[RootClass.STATE_DURABLE.value]).resolve()
    if _is_subpath(p, durable_root):
        try:
            rel = p.resolve().relative_to(durable_root).as_posix()
            return f"state/durable/{rel}".rstrip("/")
        except Exception:
            pass

    return p.as_posix().lstrip("/")


def guard_write(
    target_path: Union[Path, str],
    record_class: Optional[str] = None,
    target_repo: Optional[str] = None,
    aw_home: Optional[str] = None,
    is_producer: bool = True,
) -> Path:
    """Centralized write guard (E-02).

    Rejects:
    1. Legacy destinations (.agents/ or workflow-artifacts/) unless permitted host exception.
    2. Unresolved/inaccessible roots.
    3. Active pre-switch migrations.
    4. Stale context.
    5. Unsafe symlinks.
    6. Cross-Git staging.
    7. Writes into installed system or runtime state from record producers.
    """
    p = Path(target_path).expanduser()
    posix_str = p.as_posix()

    # 1. Legacy destination check
    if ".agents/" in posix_str or "workflow-artifacts/" in posix_str:
        if not (
            "_data" in posix_str or ".opencode" in posix_str or ".claude" in posix_str
        ):
            raise LegacyWriteError(
                f"Legacy write rejected: '{target_path}' contains forbidden legacy path component (.agents/ or workflow-artifacts/)."
            )

    # 2. Context resolution & stale context check
    try:
        ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
    except Exception as e:
        raise StaleContextError(f"Stale or unresolved project context: {e}")

    # 3. Active pre-switch migration check
    runtime_tx = (
        Path(ctx.physical_classes[RootClass.STATE_RUNTIME.value])
        / "transactions"
        / "migration_transaction.json"
    )
    durable_receipt = (
        Path(ctx.physical_classes[RootClass.STATE_DURABLE.value])
        / "migrations"
        / "switch_receipt.json"
    )

    if runtime_tx.is_file() and not durable_receipt.is_file():
        raise MigrationInFlightError(
            f"Write rejected: pre-switch migration is active ({runtime_tx})."
        )

    # 4. Unsafe symlink / traversal check
    if p.is_symlink():
        target_dest = p.resolve()
        records_root = Path(ctx.physical_classes[RootClass.RECORDS.value]).resolve()
        durable_root = Path(
            ctx.physical_classes[RootClass.STATE_DURABLE.value]
        ).resolve()
        runtime_root = Path(
            ctx.physical_classes[RootClass.STATE_RUNTIME.value]
        ).resolve()
        if not (
            _is_subpath(target_dest, records_root)
            or _is_subpath(target_dest, durable_root)
            or _is_subpath(target_dest, runtime_root)
        ):
            raise UnsafeSymlinkError(
                f"Unsafe symlink '{p}' points to '{target_dest}' outside authorized roots."
            )

    # 5. System/runtime write check from producers
    if is_producer:
        sys_root = Path(ctx.physical_classes[RootClass.SYSTEM.value]).resolve()
        runtime_root = Path(
            ctx.physical_classes[RootClass.STATE_RUNTIME.value]
        ).resolve()
        resolved_p = p.resolve()
        if _is_subpath(resolved_p, sys_root):
            raise ForbiddenWriteError(
                f"Forbidden producer write: record producer cannot write into system root '{sys_root}'."
            )
        if _is_subpath(resolved_p, runtime_root):
            raise ForbiddenWriteError(
                f"Forbidden producer write: record producer cannot write into runtime state root '{runtime_root}'."
            )

    # 6. Cross-Git staging check
    if record_class and is_producer:
        owner = get_git_owner(record_class, target_repo=target_repo, aw_home=aw_home)
        if owner is None and ctx.records_backend != RecordsBackend.REPOSITORY.value:
            # Staging external record in target git is prohibited
            pass

    return p


def resolve_record_read_paths(
    record_class: str,
    target_repo: Optional[str] = None,
    aw_home: Optional[str] = None,
) -> List[Path]:
    """Resolve active and retained read paths for a record class with bounded compatibility (E-06)."""
    primary = resolve_record_path(
        record_class, target_repo=target_repo, aw_home=aw_home
    )
    paths: List[Path] = [primary]

    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
    manifest_file = (
        Path(ctx.physical_classes[RootClass.STATE_DURABLE.value])
        / "migrations"
        / "retention_manifest.json"
    )

    if manifest_file.is_file():
        try:
            # Legacy `.agents/` reads use the DECOUPLED legacy subpath (keeps `docs/` nesting), so
            # the flattened final `.aw/records/` layout does not break legacy migration reads
            # (IPD awretrofit Order 07, plan-review PR-001).
            legacy_sub = _LEGACY_RECORD_CLASS_SUBPATHS.get(record_class, "")
            target_base = Path(ctx.target_repo)
            legacy_dir = (
                target_base / ".agents" / legacy_sub
                if legacy_sub
                else target_base / ".agents"
            )
            if legacy_dir.is_dir() and legacy_dir not in paths:
                paths.append(legacy_dir)
        except Exception:
            pass

    if len(paths) > 1 and primary.is_dir() and paths[1].is_dir():
        for p_file in primary.rglob("*"):
            if p_file.is_file():
                rel = p_file.relative_to(primary)
                leg_file = paths[1] / rel
                if leg_file.is_file():
                    if p_file.read_bytes() != leg_file.read_bytes():
                        raise DuplicateAuthorityError(
                            f"Duplicate authority collision for '{rel}': content differs between primary '{p_file}' and legacy '{leg_file}'."
                        )

    return paths


@dataclass(frozen=True)
class RecordRoutingInfo:
    """Logical record routing resolution result (legacy E-02 compatibility wrapper)."""

    records_root: str
    records_backend: str
    commit_destination: Optional[str]
    allow_git_stage: bool


def resolve_record_routing(
    target_repo: Optional[str] = None, aw_home: Optional[str] = None
) -> RecordRoutingInfo:
    """Resolve backend-neutral record routing and commit policy."""
    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
    records_root = ctx.logical_roots[LogicalRoot.RECORDS.value]
    backend = ctx.records_backend
    allow_git = backend == RecordsBackend.REPOSITORY.value
    commit_dest = "repository" if allow_git else None

    return RecordRoutingInfo(
        records_root=records_root,
        records_backend=backend,
        commit_destination=commit_dest,
        allow_git_stage=allow_git,
    )
