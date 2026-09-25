"""Shared record placement library (Set specdirs, Order 03, IPD r9uvwc).

This module is the SINGLE AUTHORITY answering "where does a record of type T with status S live"
for both CREATION and TRANSITION.

It unifies the directory placement rules across all lifecycle-bearing record types:
- `plans`: many-to-one mapping (draft/to-review/reviewed/approved/auto-approved -> pending/,
  executed -> executed/, superseded -> superseded/, not-executed -> not-executed/, reusable -> reusable/).
  Derived from `plans.PRE_TERMINAL`, `plans.TERMINAL`, `plans.STANDING` and `layout.py`.
- `prompts`: same disposition mapping as `plans`.
- `backlog`: identity mapping over `backlog.STATUS_DIRS` (open, graduated, blocked, parked, done).
- `specs`: identity mapping over `attention_contract.SPEC_STATUSES` (draft, to-review, reviewed,
  approved, implementing, implemented, deferred, parked, superseded).

It reuses the disposition derivation from `attention._plan_disposition_from_rel` to remain
shard-safe (plans under `<disposition>/YYYYMM/` preserve their shard across terminal transitions
and resolve to the first component rather than reading `path.parent.name`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Set

from agent_workflows import attention_contract as _AC
from agent_workflows import backlog as _BL
from agent_workflows import lifecycle_dirs as _LD
from agent_workflows import plans as _plans


def has_lifecycle_subdirs(record_type: str) -> bool:
    """True if `record_type` uses status/disposition subdirectories."""
    from agent_workflows import layout as _layout

    model = _layout.build_default_layout()
    try:
        rc = model.get_record_class(record_type)
        return bool(rc.lifecycle_subdirs)
    except (KeyError, ValueError):
        return bool(_LD.subdirs_for(record_type))


def target_subdir(record_type: str, status: str) -> Optional[str]:
    """Return the subdirectory name for a record of `record_type` with `status`.

    Returns None if `record_type` has no lifecycle subdirectories.
    """
    if record_type in ("plans", "prompts"):
        if status in _plans.PRE_TERMINAL:
            return "pending"
        if status in _plans.TERMINAL or status in _plans.STANDING:
            return status
        return "pending"

    if record_type == "backlog":
        if status in _BL.STATUS_DIRS:
            return status
        return status

    if record_type == "specs":
        if status in _AC.SPEC_STATUSES:
            return status
        return status

    if has_lifecycle_subdirs(record_type):
        return status

    return None


def resolve_type_dir(record_type: str, repo_root: Optional[Path] = None) -> Path:
    """Resolve physical directory for `record_type`, preferring `.aw/records/` with `.agents/` fallback."""
    from agent_workflows import layout as _layout
    from agent_workflows.record_producers import resolve_record_path

    if repo_root is None:
        repo_root = Path.cwd()

    modern_dir = repo_root / ".aw" / "records" / record_type
    if modern_dir.is_dir():
        return modern_dir

    legacy_sub = _layout.LEGACY_RECORD_SUBPATH_OVERRIDES.get(record_type, record_type)
    legacy_dir = repo_root / ".agents" / legacy_sub
    if legacy_dir.is_dir():
        return legacy_dir

    try:
        base = resolve_record_path(record_type, target_repo=str(repo_root))
    except Exception:
        base = modern_dir

    if not base.is_dir() and legacy_dir.is_dir():
        return legacy_dir

    return base


def resolve_creation_path(
    record_type: str,
    status: str,
    filename: str,
    repo_root: Optional[Path] = None,
) -> Path:
    """Compute the filesystem destination path for a newly created record."""
    type_dir = resolve_type_dir(record_type, repo_root=repo_root)
    subdir = target_subdir(record_type, status)
    if subdir:
        return type_dir / subdir / filename
    return type_dir / filename


def _find_repo_root(path: Path) -> Path:
    """Walk parents of `path` to find the enclosing repo root."""
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    curr = resolved if resolved.is_dir() else resolved.parent
    for p in [curr, *curr.parents]:
        if (p / ".git").exists() or (p / ".aw").exists() or (p / ".agents").exists():
            return p
    return curr


def resolve_transition_path(
    record_type: str,
    current_path: Path,
    new_status: str,
    repo_root: Optional[Path] = None,
) -> Path:
    """Compute the destination path for transitioning `current_path` to `new_status`.

    If the source file already resides in the correct destination directory, returns `current_path`.
    For sharded plans (e.g. `executed/YYYYMM/plan.ipd.md`), moving to another terminal disposition
    preserves the shard subdirectory (`superseded/YYYYMM/plan.ipd.md`), while moving to `pending`
    places the file in `pending/plan.ipd.md`.
    """
    target = target_subdir(record_type, new_status)
    if target is None:
        return current_path

    if repo_root is None:
        repo_root = _find_repo_root(current_path)

    type_dir = resolve_type_dir(record_type, repo_root=repo_root)

    # Re-derive disposition using shared `_plan_disposition_from_rel` when possible
    if record_type in ("plans", "prompts"):
        base_dir = type_dir
        try:
            rel_type = current_path.resolve().relative_to(type_dir.resolve()).as_posix()
        except (ValueError, OSError):
            rel_type = ""
            if current_path.parent.name in _plans.DISPOSITION_DIRS:
                base_dir = current_path.parent.parent
                rel_type = f"{current_path.parent.name}/{current_path.name}"
            elif current_path.parent.parent.name in _plans.DISPOSITION_DIRS:
                base_dir = current_path.parent.parent.parent
                rel_type = f"{current_path.parent.parent.name}/{current_path.parent.name}/{current_path.name}"
            elif current_path.parent.name in ("plans", "prompts"):
                base_dir = current_path.parent
                rel_type = current_path.name

        if rel_type:
            if "/" in rel_type:
                parts = rel_type.split("/")
                old_disp = parts[0]
                if old_disp in _plans.DISPOSITION_DIRS:
                    shard_parts = parts[1:-1]
                    filename = parts[-1]
                    if old_disp == target:
                        return current_path
                    if target == "pending":
                        return base_dir / "pending" / filename
                    if shard_parts:
                        return base_dir / target / "/".join(shard_parts) / filename
                    return base_dir / target / filename

            # File is at the root of plans/prompts directory
            return base_dir / target / current_path.name

        return current_path

    if record_type in ("backlog", "specs"):
        valid_subdirs: Set[str] = set(_LD.subdirs_for(record_type))

        base_dir = type_dir
        try:
            rel_type = current_path.resolve().relative_to(type_dir.resolve()).as_posix()
        except (ValueError, OSError):
            rel_type = ""
            if current_path.parent.name in valid_subdirs:
                base_dir = current_path.parent.parent
                rel_type = f"{current_path.parent.name}/{current_path.name}"
            elif current_path.parent.name == record_type:
                base_dir = current_path.parent
                rel_type = current_path.name

        if rel_type:
            if "/" in rel_type:
                parts = rel_type.split("/")
                old_sub = parts[0]
                if old_sub in valid_subdirs:
                    filename = parts[-1]
                    if old_sub == target:
                        return current_path
                    return base_dir / target / filename

            # File is at the root of backlog/specs directory
            return base_dir / target / current_path.name

        return current_path

    return current_path
