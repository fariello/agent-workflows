"""Pure placement-switch planner with blockers and per-item moves (IPD xvlemm / Set cfgreloc).

Computes a deterministic SwitchPlan that specifies all file movements, discards,
and rewrites required to switch configuration placement between target and home,
with zero side effects (pure read-only inspection).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Collection, Dict, List, Optional, Set

from agent_workflows import engine, platform_lock, storage
from agent_workflows.install_wizard import (
    ProjectPolicy,
    config_placement_switch,
    get_preset_defaults,
    records_root_switch,
    resolve_existing_policy,
)
from agent_workflows.project_context import (
    _canonical_path,
    _derive_project_id,
    _resolve_effective_aw_home,
    checkout_main_root,
    project_config_dir,
    resolve_project_context,
)
from agent_workflows.project_schema import (
    LocalBindingSchema,
    Preset,
    ProjectPolicySchema,
    parse_local_binding,
    parse_portable_policy,
)

__all__ = [
    "PlacementSwitchError",
    "SwitchBlocker",
    "SwitchItem",
    "SwitchPlan",
    "SwitchResult",
    "plan_placement_switch",
    "plan_records_root_switch",
    "retire_footprint",
    "execute_placement_switch",
    "execute_records_root_switch",
    "resume_placement_switch",
    "rollback_placement_switch",
    "placement_switch_status",
    "render_plan",
]

COMPANION_RECORD_IGNORE_PATTERNS = [
    "records/*/untracked/",
    "records/history.jsonl",
    "records/runs/",
    "records/plans/INDEX.json",
    "records/plans/INDEX.md",
    "records/research/INDEX.json",
    "records/research/INDEX.md",
    "records/prompts/INDEX.json",
    "records/prompts/INDEX.md",
]


class PlacementSwitchError(Exception):
    """Raised when a placement switch or retirement cannot proceed."""


class SwitchBlocker(str):
    """Stable string blocker ID with an associated human-readable message."""

    message: str

    def __new__(cls, blocker_id: str, message: str = "") -> "SwitchBlocker":
        obj = super().__new__(cls, blocker_id)
        obj.message = message
        return obj


@dataclass
class SwitchItem:
    """An individual file operation in a placement switch plan."""

    item_class: str
    source: Path
    destination: Optional[Path] = None
    kind: str = "move"  # "move", "discard", "rewrite"
    tracked: bool = False
    sha256: Optional[str] = None
    size: Optional[int] = None
    mode: Optional[int] = None

    def __init__(
        self,
        item_class: str = "",
        source: str | Path = "",
        destination: Optional[str | Path] = None,
        kind: str = "move",
        tracked: bool = False,
        sha256: Optional[str] = None,
        size: Optional[int] = None,
        mode: Optional[int] = None,
        *,
        class_: Optional[str] = None,
        source_git: Optional[str] = None,
        dest_git: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.item_class = class_ if class_ is not None else item_class
        self.source = Path(source) if source else Path()
        self.destination = Path(destination) if destination is not None else None
        self.kind = kind
        self.tracked = bool(tracked)
        self.sha256 = sha256
        self.size = size
        self.mode = mode
        # Which git repository owns the source / destination path:
        # "target", "companion", or None (AW_HOME or not staged). IPD xc8nae.
        self.source_git = source_git
        self.dest_git = dest_git

    @property
    def class_(self) -> str:
        return self.item_class

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class": self.item_class,
            "item_class": self.item_class,
            "source": str(self.source) if self.source else None,
            "destination": (
                str(self.destination) if self.destination is not None else None
            ),
            "kind": self.kind,
            "tracked": self.tracked,
            "sha256": self.sha256,
            "size": self.size,
            "mode": self.mode,
            "source_git": self.source_git,
            "dest_git": self.dest_git,
        }


@dataclass
class SwitchPlan:
    """Complete planned switch specification with items, blockers, and warnings."""

    repo: Path
    project_id: str
    from_preset: str
    to_preset: str
    from_config_dir: Path
    to_config_dir: Path
    direction: str  # "to-home", "to-target", "in-place", or ""
    items: List[SwitchItem] = field(default_factory=list)
    retire_side: Optional[str] = None  # "target", "home", or None
    blockers: List[str] = field(default_factory=list)
    warnings: Dict[str, int] = field(default_factory=dict)
    blocker_messages: Dict[str, str] = field(default_factory=dict)
    # Companion fields (IPD xc8nae / Set cmpreloc). None/False for cfgreloc plans.
    companion_dir: Optional[Path] = None
    companion_action: Optional[str] = None  # "attach", "detach", or None
    companion_create: bool = False
    config_retrack: Optional[str] = None  # "untrack", "track", or None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo": str(self.repo),
            "project_id": self.project_id,
            "from_preset": self.from_preset,
            "to_preset": self.to_preset,
            "from_config_dir": str(self.from_config_dir),
            "to_config_dir": str(self.to_config_dir),
            "direction": self.direction,
            "retire_side": self.retire_side,
            "blockers": [str(b) for b in self.blockers],
            "blocker_messages": dict(self.blocker_messages),
            "warnings": dict(self.warnings),
            "items": [item.to_dict() for item in self.items],
            "companion_dir": (
                str(self.companion_dir) if self.companion_dir is not None else None
            ),
            "companion_action": self.companion_action,
            "companion_create": self.companion_create,
            "config_retrack": self.config_retrack,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SwitchPlan":
        items = []
        for item_data in data.get("items", []):
            items.append(
                SwitchItem(
                    item_class=item_data.get("item_class")
                    or item_data.get("class", ""),
                    source=item_data.get("source", ""),
                    destination=item_data.get("destination"),
                    kind=item_data.get("kind", "move"),
                    tracked=item_data.get("tracked", False),
                    sha256=item_data.get("sha256"),
                    size=item_data.get("size"),
                    mode=item_data.get("mode"),
                    source_git=item_data.get("source_git"),
                    dest_git=item_data.get("dest_git"),
                )
            )
        comp_dir = data.get("companion_dir")
        return cls(
            repo=Path(data["repo"]),
            project_id=data["project_id"],
            from_preset=data["from_preset"],
            to_preset=data["to_preset"],
            from_config_dir=Path(data["from_config_dir"]),
            to_config_dir=Path(data["to_config_dir"]),
            direction=data["direction"],
            items=items,
            retire_side=data.get("retire_side"),
            blockers=data.get("blockers", []),
            warnings=data.get("warnings", {}),
            blocker_messages=data.get("blocker_messages", {}),
            companion_dir=Path(comp_dir) if comp_dir else None,
            companion_action=data.get("companion_action"),
            companion_create=bool(data.get("companion_create", False)),
            config_retrack=data.get("config_retrack"),
        )


@dataclass
class SwitchResult:
    """Outcome of a placement switch execution or resume."""

    transaction_id: str
    from_preset: str
    to_preset: str
    from_config_dir: Path
    to_config_dir: Path
    direction: str
    items_moved: int
    items_discarded: int
    items_rewritten: int
    staged_paths: List[str]
    retire_actions: List[str]
    receipt_path: Path
    unplanned_leftovers: List[str] = field(default_factory=list)
    companion_dir: Optional[Path] = None
    companion_action: Optional[str] = None
    staged: Optional[Dict[str, List[str]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "from_preset": self.from_preset,
            "to_preset": self.to_preset,
            "from_config_dir": str(self.from_config_dir),
            "to_config_dir": str(self.to_config_dir),
            "direction": self.direction,
            "items_moved": self.items_moved,
            "items_discarded": self.items_discarded,
            "items_rewritten": self.items_rewritten,
            "staged_paths": list(self.staged_paths),
            "retire_actions": list(self.retire_actions),
            "receipt_path": str(self.receipt_path),
            "unplanned_leftovers": list(self.unplanned_leftovers),
            "companion_dir": str(self.companion_dir) if self.companion_dir else None,
            "companion_action": self.companion_action,
            "staged": dict(self.staged) if self.staged is not None else None,
        }


def _run_git_read_only(repo: Path, args: List[str]) -> subprocess.CompletedProcess[str]:
    """Execute git subprocess strictly read-only with GIT_OPTIONAL_LOCKS=0."""
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    cmd = ["git", "-c", "core.fsmonitor=false"] + args
    return subprocess.run(
        cmd,
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _is_git_toplevel(path: Path) -> bool:
    """True when `path` is the TOP of its own git repository (IPD xc8nae F-08).

    A bare `rev-parse --git-dir` is not enough: it succeeds for a plain
    directory nested inside some other repository.
    """
    res = _run_git_read_only(path, ["rev-parse", "--show-toplevel"])
    if res.returncode != 0 or not res.stdout.strip():
        return False
    return _canonical_path(res.stdout.strip()) == _canonical_path(path)


def _get_tracked_files(repo: Path) -> Set[str]:
    """Return relative posix paths of all files tracked in repo git index."""
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    cmd = ["git", "-c", "core.fsmonitor=false", "ls-files", "-z"]
    res = subprocess.run(
        cmd,
        cwd=str(repo),
        capture_output=True,
        env=env,
        check=False,
    )
    if res.returncode != 0 or not res.stdout:
        return set()
    entries = res.stdout.split(b"\x00")
    tracked = set()
    for e in entries:
        if e:
            tracked.add(e.decode("utf-8", errors="replace"))
    return tracked


def _calc_file_meta(
    path: Path,
) -> tuple[Optional[str], Optional[int], Optional[int]]:
    """Return (sha256, size, mode) for a path without following symlinks."""
    try:
        st = path.lstat()
        mode = st.st_mode
        size = st.st_size
    except OSError:
        return None, None, None

    if stat.S_ISLNK(mode):
        return None, size, mode

    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest(), size, mode
    except OSError:
        return None, size, mode


def _census_records(
    old_records_root: Path,
    new_records_root: Path,
    is_tracked_fn: Any,
    *,
    discard_preexisting_scaffold: bool = False,
) -> List[SwitchItem]:
    """Enumerate records files for relocation or discard."""
    records_items: List[SwitchItem] = []
    if not old_records_root.exists():
        return records_items

    scaffold_names = {".gitkeep", "README.md"}

    for root, dirs, files in os.walk(old_records_root, followlinks=False):
        dirs.sort()
        for d in list(dirs):
            dp = Path(root) / d
            if dp.is_symlink():
                dirs.remove(d)
                rel_p = dp.relative_to(old_records_root)
                dest = new_records_root / rel_p
                records_items.append(
                    SwitchItem(
                        item_class="records",
                        source=dp,
                        destination=dest,
                        kind="move",
                        tracked=is_tracked_fn(dp),
                        sha256=None,
                        size=dp.lstat().st_size,
                        mode=dp.lstat().st_mode,
                    )
                )
        for fname in sorted(files):
            fp = Path(root) / fname
            rel_p = fp.relative_to(old_records_root)
            r_sha, r_size, r_mode = _calc_file_meta(fp)
            if fname in ("INDEX.json", "INDEX.md"):
                records_items.append(
                    SwitchItem(
                        item_class="records",
                        source=fp,
                        destination=None,
                        kind="discard",
                        tracked=is_tracked_fn(fp),
                        sha256=r_sha,
                        size=r_size,
                        mode=r_mode,
                    )
                )
            else:
                dest = new_records_root / rel_p
                if (
                    discard_preexisting_scaffold
                    and fname in scaffold_names
                    and (dest.exists() or dest.is_symlink())
                ):
                    records_items.append(
                        SwitchItem(
                            item_class="records",
                            source=fp,
                            destination=None,
                            kind="discard",
                            tracked=is_tracked_fn(fp),
                            sha256=r_sha,
                            size=r_size,
                            mode=r_mode,
                        )
                    )
                else:
                    records_items.append(
                        SwitchItem(
                            item_class="records",
                            source=fp,
                            destination=dest,
                            kind="move",
                            tracked=is_tracked_fn(fp),
                            sha256=r_sha,
                            size=r_size,
                            mode=r_mode,
                        )
                    )
    return records_items


def plan_placement_switch(
    repo_path: str | Path,
    new_policy: ProjectPolicy,
    *,
    aw_home: Optional[str | Path] = None,
) -> SwitchPlan:
    """Pure planner for cross-placement preset switches (spec Section 8.1).

    Reuses install_wizard.config_placement_switch for detection. Returns a SwitchPlan
    containing all per-item moves, rewrites, discards, blockers, and warnings.
    Read-only with zero filesystem writes or index locks.
    """
    repo = Path(repo_path).resolve()
    eff_aw_home_str, _, _ = _resolve_effective_aw_home(
        aw_home=aw_home or getattr(new_policy, "aw_home", None)
    )
    eff_aw_home = Path(eff_aw_home_str)

    # Calculate canonical path-derived project_id
    anchor = repo
    try:
        if (repo / ".git").exists():
            anchor = checkout_main_root(repo) or repo
    except Exception:
        anchor = repo
    canonical_anchor = _canonical_path(anchor)
    derived_project_id = _derive_project_id(canonical_anchor)

    # Determine existing policy and presets
    prev_env_aw_home = os.environ.get("AW_HOME")
    os.environ["AW_HOME"] = str(eff_aw_home)
    try:
        existing_policy = resolve_existing_policy(str(repo))
        from_config_dir = Path(project_config_dir(repo, aw_home=eff_aw_home))

        from_preset = getattr(existing_policy, "preset", "")
        if not from_preset:
            cand_proj = from_config_dir / "project.json"
            if cand_proj.exists():
                try:
                    from_preset = json.loads(cand_proj.read_text(encoding="utf-8")).get(
                        "preset", ""
                    )
                except Exception:
                    pass
        to_preset = getattr(new_policy, "preset", "")

        companion_preset = Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value
        old_is_companion = from_preset == companion_preset
        new_is_companion = to_preset == companion_preset

        # Resolve OLD side project context (physical roots, not placement labels;
        # IPD xc8nae F-01).
        old_ctx = resolve_project_context(target_repo=str(repo), aw_home=eff_aw_home)

        # Resolve NEW side project context
        new_ctx = resolve_project_context(
            target_repo=str(repo),
            delivery_mode=new_policy.delivery_mode,
            records_backend=new_policy.records_backend,
            preset=new_policy.preset,
            role=new_policy.role,
            companion_dir=new_policy.companion_dir,
            aw_home=eff_aw_home,
        )

        old_companion_dir: Optional[Path] = (
            Path(old_ctx.physical_classes["records"]).parent
            if old_is_companion
            else None
        )
        new_companion_dir: Optional[Path] = (
            Path(new_ctx.physical_classes["records"]).parent
            if new_is_companion
            else None
        )

        # companion-to-companion runs BEFORE the not-a-placement-switch short
        # circuit: config_placement_switch returns None for two companion
        # policies, so a check placed after it would be unreachable (xc8nae E-01).
        if (
            old_is_companion
            and new_is_companion
            and old_companion_dir is not None
            and new_companion_dir is not None
            and _canonical_path(old_companion_dir) != _canonical_path(new_companion_dir)
        ):
            msg = (
                f"Moving the companion binding from {old_companion_dir} to "
                f"{new_companion_dir} is not a placement switch; use "
                "`aw storage move` instead."
            )
            return SwitchPlan(
                repo=repo,
                project_id=derived_project_id,
                from_preset=from_preset,
                to_preset=to_preset,
                from_config_dir=from_config_dir,
                to_config_dir=from_config_dir,
                direction="",
                items=[],
                retire_side=None,
                blockers=[SwitchBlocker("companion-to-companion", msg)],
                blocker_messages={"companion-to-companion": msg},
                warnings={},
                companion_dir=new_companion_dir,
            )

        # Placement switch detection reuse
        switch = config_placement_switch(
            repo, new_policy, existing_policy=existing_policy
        )

        if switch is None:
            # Same-placement / no switch required
            return SwitchPlan(
                repo=repo,
                project_id=derived_project_id,
                from_preset=from_preset,
                to_preset=to_preset,
                from_config_dir=from_config_dir,
                to_config_dir=from_config_dir,
                direction="",
                items=[],
                retire_side=None,
                blockers=[
                    SwitchBlocker(
                        "not-a-placement-switch",
                        "Requested policy does not change config placement.",
                    )
                ],
                blocker_messages={
                    "not-a-placement-switch": "Requested policy does not change config placement."
                },
                warnings={},
            )

        # Exactly one side companion: a companion attach or detach (IPD xc8nae).
        # The census is fully populated (IPD xc8nae / Set cmpreloc).
        is_companion_switch = old_is_companion != new_is_companion
        companion_action: Optional[str] = None
        companion_dir: Optional[Path] = None
        if is_companion_switch:
            if new_is_companion:
                companion_action = "attach"
                companion_dir = new_companion_dir
            else:
                companion_action = "detach"
                companion_dir = old_companion_dir
        companion_create = bool(
            companion_action == "attach"
            and companion_dir is not None
            and not companion_dir.exists()
        )
        companion_is_repo_top = bool(
            companion_dir is not None
            and companion_dir.is_dir()
            and _is_git_toplevel(companion_dir)
        )

        to_config_dir = Path(new_ctx.physical_classes["config_project"]).parent

        # Determine direction and retire_side
        is_from_in_target = (
            repo in from_config_dir.resolve().parents
            or from_config_dir.resolve() == repo.resolve()
        )
        is_to_in_target = (
            repo in to_config_dir.resolve().parents
            or to_config_dir.resolve() == repo.resolve()
        )

        if is_from_in_target and not is_to_in_target:
            direction = "to-home"
            retire_side: Optional[str] = "target"
        elif not is_from_in_target and is_to_in_target:
            direction = "to-target"
            retire_side = "home"
        elif is_companion_switch and is_from_in_target and is_to_in_target:
            # Pairs (a)/(b): config directory unchanged, only records move.
            direction = "in-place"
            retire_side = None
        else:
            direction = ""
            retire_side = None

        config_retrack: Optional[str] = None
        if direction == "in-place":
            config_retrack = "untrack" if companion_action == "attach" else "track"

        # Build items
        tracked_files = _get_tracked_files(repo)
        companion_tracked_files: Set[str] = (
            _get_tracked_files(companion_dir)
            if companion_dir is not None and companion_is_repo_top
            else set()
        )
        repo_res = repo.resolve()
        companion_res = companion_dir.resolve() if companion_dir is not None else None

        def git_owner(file_path: Optional[Path]) -> Optional[str]:
            """Return which git repository owns a path: target, companion, or None."""
            if file_path is None:
                return None
            try:
                resolved_f = file_path.resolve()
            except OSError:
                return None
            if companion_res is not None and (
                companion_res in resolved_f.parents or resolved_f == companion_res
            ):
                return "companion"
            if repo_res in resolved_f.parents or resolved_f == repo_res:
                return "target"
            return None

        def is_tracked(file_path: Path) -> bool:
            owner = git_owner(file_path)
            try:
                resolved_f = file_path.resolve()
                if owner == "companion" and companion_res is not None:
                    rel = resolved_f.relative_to(companion_res).as_posix()
                    return rel in companion_tracked_files
                if owner == "target":
                    rel = resolved_f.relative_to(repo_res).as_posix()
                    return rel in tracked_files
            except (OSError, ValueError):
                pass
            return False

        items: List[SwitchItem] = []

        # 1. config_project -> rewrite item
        old_proj_file = from_config_dir / "project.json"
        if not old_proj_file.exists():
            for alt in ("config.json", "policy.json"):
                if (from_config_dir / alt).exists():
                    old_proj_file = from_config_dir / alt
                    break
        new_proj_file = to_config_dir / "project.json"
        sha, size, mode = _calc_file_meta(old_proj_file)
        items.append(
            SwitchItem(
                item_class="config_project",
                source=old_proj_file,
                destination=new_proj_file,
                kind="rewrite",
                tracked=is_tracked(old_proj_file),
                sha256=sha,
                size=size,
                mode=mode,
            )
        )

        # 2. config_local -> rewrite item (if present)
        old_local_file = from_config_dir / "local.json"
        if old_local_file.exists():
            new_local_file = to_config_dir / "local.json"
            l_sha, l_size, l_mode = _calc_file_meta(old_local_file)
            items.append(
                SwitchItem(
                    item_class="config_local",
                    source=old_local_file,
                    destination=new_local_file,
                    kind="rewrite",
                    tracked=is_tracked(old_local_file),
                    sha256=l_sha,
                    size=l_size,
                    mode=l_mode,
                )
            )

        # 3. records -> move regular files and symlinks, discard INDEX.json/INDEX.md
        old_records_root = Path(old_ctx.physical_classes["records"])
        new_records_root = Path(new_ctx.physical_classes["records"])
        items.extend(
            _census_records(
                old_records_root,
                new_records_root,
                is_tracked,
                discard_preexisting_scaffold=False,
            )
        )

        # 4. state_durable -> move history/ and install.json only, discard rest
        old_durable_root = Path(old_ctx.physical_classes["state_durable"])
        new_durable_root = Path(new_ctx.physical_classes["state_durable"])
        durable_items: List[SwitchItem] = []
        if old_durable_root.exists():
            for root, dirs, files in os.walk(old_durable_root, followlinks=False):
                dirs.sort()
                for fname in sorted(files):
                    fp = Path(root) / fname
                    rel_p = fp.relative_to(old_durable_root)
                    d_sha, d_size, d_mode = _calc_file_meta(fp)
                    is_history = len(rel_p.parts) > 1 and rel_p.parts[0] == "history"
                    is_install_json = rel_p.parts == ("install.json",)
                    if is_history or is_install_json:
                        durable_items.append(
                            SwitchItem(
                                item_class="state_durable",
                                source=fp,
                                destination=new_durable_root / rel_p,
                                kind="move",
                                tracked=is_tracked(fp),
                                sha256=d_sha,
                                size=d_size,
                                mode=d_mode,
                            )
                        )
                    else:
                        durable_items.append(
                            SwitchItem(
                                item_class="state_durable",
                                source=fp,
                                destination=None,
                                kind="discard",
                                tracked=is_tracked(fp),
                                sha256=d_sha,
                                size=d_size,
                                mode=d_mode,
                            )
                        )
        items.extend(durable_items)

        # 5. state_runtime -> discard all
        old_runtime_root = Path(old_ctx.physical_classes["state_runtime"])
        runtime_items: List[SwitchItem] = []
        if old_runtime_root.exists():
            for root, dirs, files in os.walk(old_runtime_root, followlinks=False):
                dirs.sort()
                for fname in sorted(files):
                    fp = Path(root) / fname
                    rt_sha, rt_size, rt_mode = _calc_file_meta(fp)
                    runtime_items.append(
                        SwitchItem(
                            item_class="state_runtime",
                            source=fp,
                            destination=None,
                            kind="discard",
                            tracked=is_tracked(fp),
                            sha256=rt_sha,
                            size=rt_size,
                            mode=rt_mode,
                        )
                    )
        items.extend(runtime_items)

        # Companion census adjustments (IPD xc8nae E-01).
        if direction == "in-place":
            # Pairs (a)/(b): durable and runtime state live in the same target
            # directory on both sides (F-01), so they are not items.
            items = [
                it
                for it in items
                if it.item_class not in ("state_durable", "state_runtime")
            ]
            if companion_action == "detach":
                attach_rec = old_durable_root / "companion_attachment.json"
                if attach_rec.exists() or attach_rec.is_symlink():
                    a_sha, a_size, a_mode = _calc_file_meta(attach_rec)
                    items.append(
                        SwitchItem(
                            item_class="state_durable",
                            source=attach_rec,
                            destination=None,
                            kind="discard",
                            tracked=is_tracked(attach_rec),
                            sha256=a_sha,
                            size=a_size,
                            mode=a_mode,
                        )
                    )

        # Which git repository owns each source and destination. Computed for
        # cfgreloc plans too, so the executor has one staging rule.
        for it in items:
            it.source_git = git_owner(it.source) if it.source else None
            it.dest_git = git_owner(it.destination)
            if (
                it.item_class == "config_project"
                and new_is_companion
                and companion_action == "attach"
            ):
                # The in-tree project.json must end untracked, as a fresh
                # companion install leaves it (F-02): never staged.
                it.dest_git = None

        # Blockers detection
        blockers: List[SwitchBlocker] = []
        blocker_messages: Dict[str, str] = {}

        def add_blocker(bid: str, msg: str) -> None:
            if bid not in blocker_messages:
                blockers.append(SwitchBlocker(bid, msg))
                blocker_messages[bid] = msg

        # Blocker: dirty-aw-tree
        if old_is_companion:
            # A fresh companion install leaves exactly `?? .aw/config/project.json`
            # untracked by design (F-02, F-07); exclude that one entry only.
            res_aw = _run_git_read_only(
                repo, ["status", "--porcelain", "-uall", "--", ".aw"]
            )
            aw_lines = [
                line
                for line in res_aw.stdout.splitlines()
                if line.strip() and line != "?? .aw/config/project.json"
            ]
        else:
            res_aw = _run_git_read_only(repo, ["status", "--porcelain", "--", ".aw"])
            aw_lines = [line for line in res_aw.stdout.splitlines() if line.strip()]
        if res_aw.returncode == 0 and aw_lines:
            add_blocker(
                "dirty-aw-tree",
                "Working tree under .aw is dirty (uncommitted changes or untracked non-ignored files).",
            )

        # Companion blockers (IPD xc8nae E-02)
        if is_companion_switch and companion_dir is not None:
            if companion_dir.exists() and not companion_is_repo_top:
                add_blocker(
                    "companion-not-git",
                    f"Companion directory {companion_dir} exists but is not the top of "
                    "its own git repository; the switch will not `git init` a "
                    "directory you already own.",
                )
            if companion_is_repo_top:
                res_c = _run_git_read_only(companion_dir, ["status", "--porcelain"])
                if res_c.returncode == 0 and res_c.stdout.strip():
                    add_blocker(
                        "companion-dirty",
                        f"Companion repository {companion_dir} has uncommitted changes "
                        "or untracked files; commit or clean the companion first.",
                    )
                    for line in res_c.stdout.splitlines():
                        prefix = line[:2]
                        if "U" in prefix or prefix in ("AA", "DD"):
                            add_blocker(
                                "companion-unmerged",
                                f"Companion repository {companion_dir} has unmerged "
                                "conflicts.",
                            )
                            break
            if companion_action == "attach":
                from agent_workflows import storage

                try:
                    storage.validate_companion_preflight(
                        repo,
                        companion_dir,
                        backend="companion",
                        aw_home=str(eff_aw_home),
                    )
                except (
                    storage.StorageSecurityError,
                    storage.IdentityConflictError,
                ) as exc:
                    add_blocker("companion-preflight", str(exc))

                # destination-not-empty over <companion>/records/**: every file
                # already there must be a hash-identical destination of a move.
                comp_records = companion_dir / "records"
                if comp_records.is_dir():
                    planned: Dict[Path, Optional[str]] = {
                        it.destination: it.sha256
                        for it in items
                        if it.kind == "move" and it.destination is not None
                    }
                    for root, dirs, files in os.walk(comp_records, followlinks=False):
                        dirs.sort()
                        hit = None
                        for fname in sorted(files):
                            if fname in ("INDEX.json", "INDEX.md"):
                                continue
                            fp = Path(root) / fname
                            f_sha, _, _ = _calc_file_meta(fp)
                            if fp not in planned or planned[fp] != f_sha:
                                hit = fp
                                break
                        if hit is not None:
                            add_blocker(
                                "destination-not-empty",
                                f"Companion records tree already contains {hit}, which "
                                "is not a hash-identical copy of a planned record; two "
                                "projects' records are never merged.",
                            )
                            break

        # Blocker: unmerged
        res_all = _run_git_read_only(repo, ["status", "--porcelain"])
        if res_all.returncode == 0:
            for line in res_all.stdout.splitlines():
                prefix = line[:2]
                if "U" in prefix or prefix in ("AA", "DD"):
                    add_blocker("unmerged", "Repository has unmerged conflicts.")
                    break

        # Blocker: destination-not-empty
        for it in items:
            if it.destination is not None and it.destination.exists():
                if not it.source.exists():
                    add_blocker(
                        "destination-not-empty",
                        f"Destination {it.destination} already exists but source does not.",
                    )
                    break
                src_sha, _, _ = _calc_file_meta(it.source)
                dst_sha, _, _ = _calc_file_meta(it.destination)
                if src_sha != dst_sha or src_sha is None:
                    if it.source.is_symlink() and it.destination.is_symlink():
                        try:
                            if os.readlink(it.source) != os.readlink(it.destination):
                                add_blocker(
                                    "destination-not-empty",
                                    f"Destination symlink {it.destination} targets differ.",
                                )
                                break
                        except OSError:
                            add_blocker(
                                "destination-not-empty",
                                f"Destination symlink {it.destination} unreadable.",
                            )
                            break
                    else:
                        add_blocker(
                            "destination-not-empty",
                            f"Destination {it.destination} already exists and is not hash-identical to source.",
                        )
                        break

        if direction == "to-home":
            target_pids = {derived_project_id}
            if getattr(new_ctx, "project_id", None):
                target_pids.add(new_ctx.project_id)
            for pid in target_pids:
                home_project_dir = eff_aw_home / "projects" / pid
                journal_file = eff_aw_home / "placement-switches" / pid / "journal.json"
                if not journal_file.exists():
                    if (home_project_dir / "records").exists() or (
                        home_project_dir / "config"
                    ).exists():
                        add_blocker(
                            "destination-not-empty",
                            f"Destination home project directory {home_project_dir} contains a records/ or config/ child not explained by an existing journal.",
                        )
                        break

        # Blocker: live-lane
        from agent_workflows import worktree_lease

        old_wt_root = worktree_lease.worktrees_root(repo).resolve()
        res_wt = _run_git_read_only(repo, ["worktree", "list", "--porcelain"])
        if res_wt.returncode == 0:
            for line in res_wt.stdout.splitlines():
                if line.startswith("worktree "):
                    wt_path_str = line[len("worktree ") :].strip()
                    try:
                        wt_p = Path(wt_path_str).resolve()
                        if wt_p != repo.resolve():
                            wt_p.relative_to(old_wt_root)
                            add_blocker(
                                "live-lane",
                                f"Active git worktree lane exists under old worktrees directory: {wt_p}",
                            )
                            break
                    except (ValueError, OSError):
                        pass

        # Blocker: unparseable-config
        for cand in ("project.json", "local.json", "config.json", "policy.json"):
            cand_path = from_config_dir / cand
            if cand_path.exists():
                try:
                    val = json.loads(cand_path.read_text(encoding="utf-8"))
                    if not isinstance(val, dict):
                        add_blocker(
                            "unparseable-config",
                            f"Config file {cand} is not a JSON object.",
                        )
                except Exception as e:
                    add_blocker(
                        "unparseable-config",
                        f"Config file {cand} cannot be parsed as JSON: {e}",
                    )

        # Blocker: project-id-mismatch
        if direction == "to-home":
            if getattr(new_ctx, "project_id", "") != derived_project_id:
                add_blocker(
                    "project-id-mismatch",
                    f"Destination project_id ({new_ctx.project_id}) does not match canonical path-derived project_id ({derived_project_id}).",
                )
        elif direction == "to-target":
            if getattr(old_ctx, "project_id", "") != derived_project_id:
                add_blocker(
                    "project-id-mismatch",
                    f"Source project_id ({old_ctx.project_id}) does not match canonical path-derived project_id ({derived_project_id}).",
                )

        # Blocker: source-checkout
        if (
            getattr(old_ctx, "project_role", "") == "source-checkout"
            or getattr(new_policy, "role", "") == "source-checkout"
        ):
            add_blocker(
                "source-checkout",
                "Cannot relocate configuration for a source-checkout repository.",
            )

        # Warnings calculation
        warnings: Dict[str, int] = {}
        if direction == "to-home":
            tracked_records = [
                it
                for it in items
                if it.item_class == "records" and it.kind == "move" and it.tracked
            ]
            if tracked_records:
                warnings["records-become-untracked"] = len(tracked_records)
        elif direction == "to-target":
            moved_records = [
                it for it in items if it.item_class == "records" and it.kind == "move"
            ]
            if moved_records:
                warnings["records-become-tracked-candidates"] = len(moved_records)

        # Companion warnings (IPD xc8nae E-02)
        if direction == "in-place" and companion_action == "attach":
            leaving = [
                it
                for it in items
                if it.item_class == "records"
                and it.kind == "move"
                and it.tracked
                and it.source_git == "target"
            ]
            if leaving:
                # They stay in the public target's git history; the switch
                # cannot rewrite history.
                warnings["records-leave-target-history"] = len(leaving)
            warnings["config-becomes-untracked"] = 1
        if companion_action == "detach":
            # The companion repository, its identity file and .gitignore are
            # left on disk, as storage.detach_companion does.
            warnings["companion-left-in-place"] = 1

        return SwitchPlan(
            repo=repo,
            project_id=derived_project_id,
            from_preset=from_preset,
            to_preset=to_preset,
            from_config_dir=from_config_dir,
            to_config_dir=to_config_dir,
            direction=direction,
            items=items,
            retire_side=retire_side,
            blockers=list(blockers),
            warnings=warnings,
            blocker_messages=blocker_messages,
            companion_dir=companion_dir,
            companion_action=companion_action,
            companion_create=companion_create,
            config_retrack=config_retrack,
        )
    finally:
        if prev_env_aw_home is not None:
            os.environ["AW_HOME"] = prev_env_aw_home
        else:
            os.environ.pop("AW_HOME", None)


def plan_records_root_switch(
    repo_path: str | Path,
    new_policy: ProjectPolicy,
    *,
    aw_home: Optional[str | Path] = None,
) -> SwitchPlan:
    """Pure planner for records-only root switches (IPD fxbm7j / Set rbswitch)."""
    repo = Path(repo_path).resolve()
    eff_aw_home_str, _, _ = _resolve_effective_aw_home(
        aw_home=aw_home or getattr(new_policy, "aw_home", None)
    )
    eff_aw_home = Path(eff_aw_home_str)

    anchor = repo
    try:
        if (repo / ".git").exists():
            anchor = checkout_main_root(repo) or repo
    except Exception:
        anchor = repo
    canonical_anchor = _canonical_path(anchor)
    derived_project_id = _derive_project_id(canonical_anchor)

    prev_env_aw_home = os.environ.get("AW_HOME")
    os.environ["AW_HOME"] = str(eff_aw_home)
    try:
        existing_policy = resolve_existing_policy(str(repo))
        from_config_dir = Path(project_config_dir(repo, aw_home=eff_aw_home))

        from_preset = getattr(existing_policy, "preset", "")
        if not from_preset:
            cand_proj = from_config_dir / "project.json"
            if cand_proj.exists():
                try:
                    from_preset = json.loads(cand_proj.read_text(encoding="utf-8")).get(
                        "preset", ""
                    )
                except Exception:
                    pass
        to_preset = getattr(new_policy, "preset", "") or from_preset

        hit = records_root_switch(repo, new_policy, existing_policy=existing_policy)

        if hit is None:
            msg = "Requested policy does not switch the records root or no records exist to move."
            return SwitchPlan(
                repo=repo,
                project_id=derived_project_id,
                from_preset=from_preset,
                to_preset=to_preset,
                from_config_dir=from_config_dir,
                to_config_dir=from_config_dir,
                direction="",
                items=[],
                retire_side=None,
                blockers=[SwitchBlocker("not-a-records-switch", msg)],
                blocker_messages={"not-a-records-switch": msg},
                warnings={},
            )

        if hit.reason == "companion":
            msg = "Companion records root switches are not supported yet (backlog n9vd2h)."
            return SwitchPlan(
                repo=repo,
                project_id=derived_project_id,
                from_preset=from_preset,
                to_preset=to_preset,
                from_config_dir=from_config_dir,
                to_config_dir=from_config_dir,
                direction="",
                items=[],
                retire_side=None,
                blockers=[SwitchBlocker("companion-unsupported", msg)],
                blocker_messages={"companion-unsupported": msg},
                warnings={},
            )

        old_records_root = Path(hit.current_root)
        new_records_root = Path(hit.target_root)

        home_projects_dir = (eff_aw_home / "projects").resolve()
        try:
            new_records_root.resolve().relative_to(home_projects_dir)
            direction = "records-to-home"
        except (ValueError, OSError):
            direction = "records-to-target"

        tracked_files = _get_tracked_files(repo)
        repo_res = repo.resolve()

        def git_owner(file_path: Optional[Path]) -> Optional[str]:
            if file_path is None:
                return None
            try:
                resolved_f = file_path.resolve()
            except OSError:
                return None
            if repo_res in resolved_f.parents or resolved_f == repo_res:
                return "target"
            return None

        def is_tracked(file_path: Path) -> bool:
            try:
                resolved_f = file_path.resolve()
                if git_owner(file_path) == "target":
                    rel = resolved_f.relative_to(repo_res).as_posix()
                    return rel in tracked_files
            except (OSError, ValueError):
                pass
            return False

        items: List[SwitchItem] = _census_records(
            old_records_root,
            new_records_root,
            is_tracked,
            discard_preexisting_scaffold=True,
        )

        for it in items:
            it.source_git = git_owner(it.source) if it.source else None
            it.dest_git = git_owner(it.destination) if it.destination else None

        # Config rewrite items
        # 1. project.json always
        old_proj_file = from_config_dir / "project.json"
        if not old_proj_file.exists():
            for alt in ("config.json", "policy.json"):
                if (from_config_dir / alt).exists():
                    old_proj_file = from_config_dir / alt
                    break
        sha, size, mode = _calc_file_meta(old_proj_file)
        items.append(
            SwitchItem(
                item_class="config_project",
                source=old_proj_file,
                destination=old_proj_file,
                kind="rewrite",
                tracked=is_tracked(old_proj_file),
                sha256=sha,
                size=size,
                mode=mode,
                source_git=git_owner(old_proj_file),
                dest_git=git_owner(old_proj_file),
            )
        )

        # 2. local.json only when it carries records_backend
        old_local_file = from_config_dir / "local.json"
        if old_local_file.exists():
            try:
                raw_local = json.loads(old_local_file.read_text(encoding="utf-8"))
                if isinstance(raw_local, dict) and "records_backend" in raw_local:
                    l_sha, l_size, l_mode = _calc_file_meta(old_local_file)
                    items.append(
                        SwitchItem(
                            item_class="config_local",
                            source=old_local_file,
                            destination=old_local_file,
                            kind="rewrite",
                            tracked=is_tracked(old_local_file),
                            sha256=l_sha,
                            size=l_size,
                            mode=l_mode,
                            source_git=git_owner(old_local_file),
                            dest_git=git_owner(old_local_file),
                        )
                    )
            except Exception:
                pass

        # Blockers
        blockers: List[SwitchBlocker] = []
        blocker_messages: Dict[str, str] = {}

        def add_blocker(bid: str, msg: str) -> None:
            if bid not in blocker_messages:
                blockers.append(SwitchBlocker(bid, msg))
                blocker_messages[bid] = msg

        # dirty-aw-tree (scoped to .aw/records and .aw/config)
        res_aw = _run_git_read_only(
            repo, ["status", "--porcelain", "--", ".aw/records", ".aw/config"]
        )
        if res_aw.returncode == 0:
            aw_lines = [line for line in res_aw.stdout.splitlines() if line.strip()]
            if aw_lines:
                add_blocker(
                    "dirty-aw-tree",
                    "Working tree under .aw/records or .aw/config is dirty (uncommitted changes or untracked non-ignored files).",
                )

        # unmerged
        res_all = _run_git_read_only(repo, ["status", "--porcelain"])
        if res_all.returncode == 0:
            for line in res_all.stdout.splitlines():
                prefix = line[:2]
                if "U" in prefix or prefix in ("AA", "DD"):
                    add_blocker("unmerged", "Repository has unmerged conflicts.")
                    break

        # destination-not-empty
        for it in items:
            if it.destination is not None and it.destination.exists():
                if not it.source.exists() and not it.source.is_symlink():
                    add_blocker(
                        "destination-not-empty",
                        f"Destination {it.destination} already exists but source does not.",
                    )
                    break
                src_sha, _, _ = _calc_file_meta(it.source)
                dst_sha, _, _ = _calc_file_meta(it.destination)
                if it.source.is_symlink() and it.destination.is_symlink():
                    try:
                        if os.readlink(it.source) != os.readlink(it.destination):
                            add_blocker(
                                "destination-not-empty",
                                f"Destination symlink {it.destination} targets differ.",
                            )
                            break
                    except OSError:
                        add_blocker(
                            "destination-not-empty",
                            f"Destination symlink {it.destination} unreadable.",
                        )
                        break
                elif src_sha != dst_sha or src_sha is None:
                    add_blocker(
                        "destination-not-empty",
                        f"Destination {it.destination} already exists and is not hash-identical to source.",
                    )
                    break

        # live-lane
        from agent_workflows import worktree_lease

        old_wt_root = worktree_lease.worktrees_root(repo).resolve()
        res_wt = _run_git_read_only(repo, ["worktree", "list", "--porcelain"])
        if res_wt.returncode == 0:
            for line in res_wt.stdout.splitlines():
                if line.startswith("worktree "):
                    wt_path_str = line[len("worktree ") :].strip()
                    try:
                        wt_p = Path(wt_path_str).resolve()
                        if wt_p != repo.resolve():
                            wt_p.relative_to(old_wt_root)
                            add_blocker(
                                "live-lane",
                                f"Active git worktree lane exists under old worktrees directory: {wt_p}",
                            )
                            break
                    except (ValueError, OSError):
                        pass

        # unparseable-config
        for cand in ("project.json", "local.json", "config.json", "policy.json"):
            cand_path = from_config_dir / cand
            if cand_path.exists():
                try:
                    val = json.loads(cand_path.read_text(encoding="utf-8"))
                    if not isinstance(val, dict):
                        add_blocker(
                            "unparseable-config",
                            f"Config file {cand} is not a JSON object.",
                        )
                except Exception as e:
                    add_blocker(
                        "unparseable-config",
                        f"Config file {cand} cannot be parsed as JSON: {e}",
                    )

        # source-checkout
        if (
            getattr(existing_policy, "role", "") == "source-checkout"
            or getattr(new_policy, "role", "") == "source-checkout"
        ):
            add_blocker(
                "source-checkout",
                "Cannot relocate configuration for a source-checkout repository.",
            )

        # Warnings
        warnings: Dict[str, int] = {}
        if direction == "records-to-home":
            tracked_records = [
                it
                for it in items
                if it.item_class == "records" and it.kind == "move" and it.tracked
            ]
            if tracked_records:
                warnings["records-become-untracked"] = len(tracked_records)
        elif direction == "records-to-target":
            target_rb = getattr(new_policy, "records_backend", None)
            if target_rb == "repository":
                moved_records = [
                    it
                    for it in items
                    if it.item_class == "records" and it.kind == "move"
                ]
                if moved_records:
                    warnings["records-become-tracked-candidates"] = len(moved_records)

        return SwitchPlan(
            repo=repo,
            project_id=derived_project_id,
            from_preset=from_preset,
            to_preset=to_preset,
            from_config_dir=from_config_dir,
            to_config_dir=from_config_dir,
            direction=direction,
            items=items,
            retire_side=None,
            blockers=list(blockers),
            warnings=warnings,
            blocker_messages=blocker_messages,
        )
    finally:
        if prev_env_aw_home is not None:
            os.environ["AW_HOME"] = prev_env_aw_home
        else:
            os.environ.pop("AW_HOME", None)


def retire_footprint(
    repo_root: str | Path,
    side: str,
    *,
    use_git: bool = True,
    preserve: Collection[str] = (),
    changed_out: Optional[list[str]] = None,
    aw_home: Optional[str | Path] = None,
) -> list[str]:
    """Retire the framework footprint on one explicit side (IPD gjylny / Set cfgreloc).

    For side="target", uninstalls in-tree framework-owned files via engine.uninstall_repo
    with side="target", removes shipped .aw/inbox/README.md template if unedited,
    prunes empty .aw/inbox/ and .aw/workflow-artifacts/, and prunes empty dirs under .aw/.
    Preserved paths are untouched.

    For side="home", resolves the derived home project directory, refuses with
    PlacementSwitchError if records/ has any file, else removes system/, state/, config/,
    and worktrees/.owners, then prunes empty dirs.
    """
    repo = Path(repo_root)
    preserve_set = frozenset(preserve)

    if side == "target":
        actions: list[str] = []
        from agent_workflows import engine

        # 1. Base in-tree uninstall with side="target"
        uninst_actions = engine.uninstall_repo(
            repo,
            use_git,
            side="target",
            preserve=preserve_set,
            changed_out=changed_out,
            force=False,
            drift_decider=None,
        )
        actions.extend(uninst_actions)

        # 2. .aw/inbox/README.md template-check and removal
        inbox_readme_rel = ".aw/inbox/README.md"
        inbox_readme_path = repo / inbox_readme_rel
        if (
            not engine._is_preserved(inbox_readme_rel, preserve_set)
            and inbox_readme_path.is_file()
        ):
            source_root = engine.resolve_source_root(None)
            scaffold = engine.collect_scaffold_members(
                repo, source_root, category="inbox"
            )
            expected_bytes = scaffold.get(inbox_readme_rel)
            if expected_bytes is not None:
                actual_bytes = inbox_readme_path.read_bytes()
                if actual_bytes == expected_bytes:
                    engine._uninstall_remove(repo, inbox_readme_rel, use_git)
                    if changed_out is not None:
                        changed_out.append(inbox_readme_rel)
                    actions.append(f"removed {inbox_readme_rel}")
                else:
                    actions.append(
                        f"PRESERVED {inbox_readme_rel} (you edited it; left in place)"
                    )

        # 2b. .aw/workflow-artifacts/README.md template-check and removal
        wf_readme_rel = ".aw/workflow-artifacts/README.md"
        wf_readme_path = repo / wf_readme_rel
        if (
            not engine._is_preserved(wf_readme_rel, preserve_set)
            and wf_readme_path.is_file()
        ):
            source_root = engine.resolve_source_root(None)
            scaffold = engine.collect_scaffold_members(
                repo, source_root, category="workflow_artifacts"
            )
            expected_bytes = scaffold.get(
                wf_readme_rel, engine._ARTIFACTS_README_FALLBACK.encode("utf-8")
            )
            if expected_bytes is not None:
                actual_bytes = wf_readme_path.read_bytes()
                if actual_bytes == expected_bytes:
                    engine._uninstall_remove(repo, wf_readme_rel, use_git)
                    if changed_out is not None:
                        changed_out.append(wf_readme_rel)
                    actions.append(f"removed {wf_readme_rel}")
                else:
                    actions.append(
                        f"PRESERVED {wf_readme_rel} (you edited it; left in place)"
                    )

        # 3. .aw/inbox/ and .aw/workflow-artifacts/ directories are pruned ONLY when empty
        for d_rel in (".aw/inbox", ".aw/workflow-artifacts"):
            d_path = repo / d_rel
            if d_path.is_dir():
                files_inside = sorted(p for p in d_path.rglob("*") if p.is_file())
                if not files_inside:
                    for sub in sorted(
                        (p for p in d_path.rglob("*") if p.is_dir()),
                        key=lambda p: len(p.parts),
                        reverse=True,
                    ):
                        try:
                            sub.rmdir()
                        except OSError:
                            pass
                    try:
                        d_path.rmdir()
                    except OSError:
                        pass
                else:
                    for f in files_inside:
                        rel_f = f.relative_to(repo).as_posix()
                        if not any(a.startswith(f"PRESERVED {rel_f}") for a in actions):
                            actions.append(f"PRESERVED {rel_f}")

        # 4. Prune empty dirs under .aw/
        aw_base = repo / ".aw"
        if aw_base.is_dir():
            for d in sorted(
                (p for p in aw_base.rglob("*") if p.is_dir()),
                key=lambda p: len(p.parts),
                reverse=True,
            ):
                try:
                    rel_d = d.relative_to(repo).as_posix()
                    if not engine._is_preserved(rel_d, preserve_set):
                        d.rmdir()
                except OSError:
                    pass
            try:
                if not engine._is_preserved(".aw", preserve_set):
                    aw_base.rmdir()
            except OSError:
                pass

        return actions

    elif side == "home":
        # Resolve <AW_HOME>/projects/<id>
        eff_aw_home_str, _, _ = _resolve_effective_aw_home(aw_home=aw_home)
        anchor = repo
        try:
            if (repo / ".git").exists():
                anchor = checkout_main_root(repo) or repo
        except (OSError, RuntimeError):
            anchor = repo
        derived_pid = _derive_project_id(_canonical_path(anchor))
        project_dir = Path(eff_aw_home_str) / "projects" / derived_pid

        if not project_dir.is_dir():
            return []

        # Refuse with PlacementSwitchError if records/ has any file
        records_dir = project_dir / "records"
        if records_dir.is_dir():
            if any(p.is_file() for p in records_dir.rglob("*")):
                raise PlacementSwitchError(
                    f"Cannot retire home footprint: records/ under {project_dir} still contains files."
                )

        actions = []
        for target_name in ("system", "state", "config"):
            target_path = project_dir / target_name
            if target_path.is_dir():
                for p in sorted(target_path.rglob("*")):
                    if p.is_file():
                        try:
                            p.unlink()
                            actions.append(f"removed {p}")
                        except OSError:
                            pass
                shutil.rmtree(target_path, ignore_errors=True)
                actions.append(f"removed {target_path}")

        owners_dir = project_dir / "worktrees" / ".owners"
        if owners_dir.is_dir():
            for p in sorted(owners_dir.rglob("*")):
                if p.is_file():
                    try:
                        p.unlink()
                        actions.append(f"removed {p}")
                    except OSError:
                        pass
            shutil.rmtree(owners_dir, ignore_errors=True)
            actions.append(f"removed {owners_dir}")

        # Prune empty dirs under project_dir
        for d in sorted(
            (p for p in project_dir.rglob("*") if p.is_dir()),
            key=lambda p: len(p.parts),
            reverse=True,
        ):
            try:
                d.rmdir()
            except OSError:
                pass
        try:
            project_dir.rmdir()
        except OSError:
            pass

        return actions

    else:
        raise ValueError(f"Invalid side: {side!r}. Must be 'target' or 'home'")


def _resolve_control_and_lock(
    repo_path: str | Path,
    aw_home: Optional[str | Path] = None,
) -> tuple[Path, Path, Path, Path, str]:
    repo = Path(repo_path).resolve()
    eff_aw_home_str, _, _ = _resolve_effective_aw_home(aw_home=aw_home)
    eff_aw_home = Path(eff_aw_home_str)
    anchor = repo
    try:
        if (repo / ".git").exists():
            anchor = checkout_main_root(repo) or repo
    except (OSError, RuntimeError):
        anchor = repo
    canonical_anchor = _canonical_path(anchor)
    project_id = _derive_project_id(canonical_anchor)

    base_switches = eff_aw_home / "placement-switches"
    control_dir = base_switches / project_id
    lock_file = base_switches / f"{project_id}.lock"
    return repo, eff_aw_home, control_dir, lock_file, project_id


def _write_atomic_json(target_path: Path, data: Dict[str, Any]) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.parent / f".tmp_{target_path.name}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp_path, target_path)


def _read_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _run_git_cmd(
    repo: Path,
    args: list[str],
    *,
    input_str: Optional[str] = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    cmd = ["git", "-c", "core.fsmonitor=false"] + args
    res = subprocess.run(
        cmd,
        cwd=str(repo),
        input=input_str,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if check and res.returncode != 0:
        raise subprocess.CalledProcessError(
            res.returncode, cmd, output=res.stdout, stderr=res.stderr
        )
    return res


def _ensure_companion_gitignore(companion_dir: Path, journal: Dict[str, Any]) -> None:
    comp_gi = companion_dir / ".gitignore"
    if not comp_gi.exists():
        journal["created_companion_gitignore"] = True
        comp_gi.write_text(
            "\n".join(COMPANION_RECORD_IGNORE_PATTERNS) + "\n", encoding="utf-8"
        )
        return

    if "prior_companion_gitignore_bytes" not in journal and not journal.get(
        "created_companion_gitignore"
    ):
        journal["prior_companion_gitignore_bytes"] = comp_gi.read_bytes().decode(
            "utf-8", errors="surrogateescape"
        )

    curr_text = comp_gi.read_text(encoding="utf-8")
    missing = [pat for pat in COMPANION_RECORD_IGNORE_PATTERNS if pat not in curr_text]
    if missing:
        new_text = curr_text
        if new_text and not new_text.endswith("\n"):
            new_text += "\n"
        new_text += "\n".join(missing) + "\n"
        comp_gi.write_text(new_text, encoding="utf-8")


def _cleanup_lock(
    lock_file: Path,
    lock_handle: Optional[Any],
    control_dir: Path,
) -> None:
    if lock_handle is not None:
        lock_handle.release()
        if not control_dir.exists():
            try:
                if lock_file.exists():
                    lock_file.unlink()
            except OSError:
                pass
            try:
                lock_file.parent.rmdir()
            except OSError:
                pass


def _perform_rollback(
    repo: Path,
    eff_aw_home: Path,
    control_dir: Path,
    journal: Dict[str, Any],
    plan: Optional[SwitchPlan] = None,
) -> None:
    """Execute the 4-step rollback procedure (E-05)."""
    if plan is None:
        plan = SwitchPlan.from_dict(journal["plan"])

    # 1. Delete new config files listed in new_config_paths
    for p_str in journal.get("new_config_paths", []):
        p = Path(p_str)
        try:
            rel = p.resolve().relative_to(repo.resolve()).as_posix()
            _run_git_cmd(
                repo,
                ["rm", "-q", "--cached", "--ignore-unmatch", "--", rel],
                check=False,
            )
        except (ValueError, OSError):
            pass
        if p.is_file() or p.is_symlink():
            try:
                p.unlink()
            except OSError:
                pass
        if p.parent.is_dir():
            try:
                p.parent.rmdir()
            except OSError:
                pass

    # 2. Restore saved_config/ byte-for-byte
    saved_config_dir = control_dir / "saved_config"
    if saved_config_dir.is_dir():
        for f in saved_config_dir.iterdir():
            if f.is_file():
                dest_f = plan.from_config_dir / f.name
                dest_f.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest_f)
                try:
                    rel = dest_f.resolve().relative_to(repo.resolve()).as_posix()
                    is_tracked = any(
                        it.source.resolve() == dest_f.resolve() and it.tracked
                        for it in plan.items
                    )
                    if is_tracked:
                        _run_git_cmd(repo, ["reset", "-q", "--", rel], check=False)
                except (ValueError, OSError):
                    pass

    # 3. Unstage staged destinations, delete copied destinations, delete .aw/.gitignore, prune dirs
    staged = journal.get("staged_paths", [])
    if staged:
        _run_git_cmd(
            repo,
            ["rm", "-q", "--cached", "--ignore-unmatch", "--"] + staged,
            check=False,
        )

    # Undo config_retrack (AFTER step 2)
    if plan.config_retrack is not None:
        _run_git_cmd(
            repo, ["reset", "-q", "--", ".aw/config/project.json"], check=False
        )

    # Restore companion identity and target attachment record
    if plan.companion_dir is not None:
        comp_ident_p = plan.companion_dir / ".aw" / "companion_identity.json"
        if journal.get("prior_companion_identity_bytes") is not None:
            comp_ident_p.parent.mkdir(parents=True, exist_ok=True)
            comp_ident_p.write_text(
                journal["prior_companion_identity_bytes"], encoding="utf-8"
            )
        else:
            if comp_ident_p.is_file() or comp_ident_p.is_symlink():
                try:
                    comp_ident_p.unlink()
                except OSError:
                    pass

    target_attach_p = repo / ".aw" / "state" / "durable" / "companion_attachment.json"
    if journal.get("prior_attachment_record_bytes") is not None:
        target_attach_p.parent.mkdir(parents=True, exist_ok=True)
        target_attach_p.write_text(
            journal["prior_attachment_record_bytes"], encoding="utf-8"
        )
    else:
        if target_attach_p.is_file() or target_attach_p.is_symlink():
            try:
                target_attach_p.unlink()
            except OSError:
                pass

    # Unstage every journaled companion path
    comp_staged = journal.get("staged", {}).get("companion", [])
    if plan.companion_dir is not None and comp_staged and plan.companion_dir.is_dir():
        _run_git_cmd(
            plan.companion_dir,
            ["rm", "-q", "--cached", "--ignore-unmatch", "--"] + comp_staged,
            check=False,
        )

    # Restore companion .gitignore
    if plan.companion_dir is not None and plan.companion_dir.is_dir():
        comp_gi = plan.companion_dir / ".gitignore"
        existed_before_attach = journal.get("companion_existed_before_attach", {}).get(
            ".gitignore"
        )
        if journal.get("created_companion_gitignore") or existed_before_attach is False:
            if comp_gi.is_file() or comp_gi.is_symlink():
                try:
                    comp_gi.unlink()
                except OSError:
                    pass
        elif journal.get("prior_companion_gitignore_bytes") is not None:
            comp_gi.write_text(
                journal["prior_companion_gitignore_bytes"], encoding="utf-8"
            )

    # Remove companion directories journaled absent before attach
    if plan.companion_dir is not None and plan.companion_dir.is_dir():
        existed_map = journal.get("companion_existed_before_attach", {})
        for rel_d in (
            ".aw/state/durable",
            ".aw/state",
            ".aw/config",
            ".aw/records",
            ".aw",
        ):
            should_check = False
            if rel_d == ".aw/state":
                should_check = not existed_map.get(".aw/state/durable", True)
            else:
                should_check = existed_map.get(rel_d) is False
            if should_check:
                d_p = plan.companion_dir / rel_d
                if d_p.is_dir():
                    try:
                        d_p.rmdir()
                    except OSError:
                        pass

    item_states = journal.get("item_states", {})
    for it in plan.items:
        if it.kind == "move" and it.destination is not None:
            if item_states.get(str(it.source), {}).get("copied"):
                if it.destination.is_symlink() or it.destination.is_file():
                    try:
                        it.destination.unlink()
                    except OSError:
                        pass

    if journal.get("created_aw_gitignore"):
        aw_gi = repo / ".aw" / ".gitignore"
        if aw_gi.exists():
            try:
                _run_git_cmd(
                    repo,
                    [
                        "rm",
                        "-q",
                        "-f",
                        "--cached",
                        "--ignore-unmatch",
                        "--",
                        ".aw/.gitignore",
                    ],
                    check=False,
                )
                aw_gi.unlink()
            except OSError:
                pass

    for d_str in sorted(
        journal.get("created_directories", []),
        key=lambda s: len(Path(s).parts),
        reverse=True,
    ):
        d = Path(d_str)
        if d.is_dir():
            try:
                d.rmdir()
            except OSError:
                pass

    # Delete companion directory only when created_companion
    if journal.get("created_companion") and plan.companion_dir is not None:
        comp = plan.companion_dir
        if comp.is_dir():
            entries = [p for p in comp.iterdir() if p.name != ".git"]
            has_commits = False
            if (comp / ".git").is_dir():
                res = subprocess.run(
                    ["git", "rev-parse", "--verify", "HEAD"],
                    cwd=str(comp),
                    capture_output=True,
                    text=True,
                )
                if res.returncode == 0:
                    has_commits = True
            if entries or has_commits:
                raise PlacementSwitchError(
                    f"Companion directory {comp} contains foreign files or commits; refusing to delete."
                )
            shutil.rmtree(comp)

    # 4. Delete the control dir
    shutil.rmtree(control_dir, ignore_errors=True)


def _perform_records_rollback(
    repo: Path,
    eff_aw_home: Path,
    control_dir: Path,
    journal: Dict[str, Any],
    plan: Optional[SwitchPlan] = None,
) -> None:
    """Execute the rollback procedure for records root switch (IPD fxbm7j / Set rbswitch)."""
    if plan is None:
        plan = SwitchPlan.from_dict(journal["plan"])

    # 1. Restore saved_config/ byte-for-byte
    saved_config_dir = control_dir / "saved_config"
    if saved_config_dir.is_dir():
        for f in saved_config_dir.iterdir():
            if f.is_file():
                dest_f = plan.from_config_dir / f.name
                dest_f.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest_f)
                try:
                    rel = dest_f.resolve().relative_to(repo.resolve()).as_posix()
                    is_tracked = any(
                        it.source.resolve() == dest_f.resolve() and it.tracked
                        for it in plan.items
                    )
                    if is_tracked:
                        _run_git_cmd(
                            repo, ["reset", "-q", "HEAD", "--", rel], check=False
                        )
                    else:
                        _run_git_cmd(
                            repo,
                            ["rm", "-q", "--cached", "--ignore-unmatch", "--", rel],
                            check=False,
                        )
                except (ValueError, OSError):
                    pass

    # 2. Unstage staged destinations, delete copied destinations, delete .aw/.gitignore, prune dirs
    staged = journal.get("staged_paths", [])
    if staged:
        _run_git_cmd(
            repo,
            ["rm", "-q", "--cached", "--ignore-unmatch", "--"] + staged,
            check=False,
        )

    item_states = journal.get("item_states", {})
    for it in plan.items:
        if it.kind == "move" and it.destination is not None:
            if item_states.get(str(it.source), {}).get("copied"):
                if it.destination.is_symlink() or it.destination.is_file():
                    try:
                        it.destination.unlink()
                    except OSError:
                        pass

    if journal.get("created_aw_gitignore"):
        aw_gi = repo / ".aw" / ".gitignore"
        if aw_gi.exists():
            try:
                _run_git_cmd(
                    repo,
                    [
                        "rm",
                        "-q",
                        "-f",
                        "--cached",
                        "--ignore-unmatch",
                        "--",
                        ".aw/.gitignore",
                    ],
                    check=False,
                )
                aw_gi.unlink()
            except OSError:
                pass

    for d_str in sorted(
        journal.get("created_directories", []),
        key=lambda s: len(Path(s).parts),
        reverse=True,
    ):
        d = Path(d_str)
        if d.is_dir():
            try:
                d.rmdir()
            except OSError:
                pass

    # 3. Delete the control dir last
    shutil.rmtree(control_dir, ignore_errors=True)


def _run_transaction(
    repo: Path,
    eff_aw_home: Path,
    control_dir: Path,
    journal: Dict[str, Any],
    plan: SwitchPlan,
    new_policy: ProjectPolicy,
    *,
    fault_injection: Optional[str] = None,
) -> SwitchResult:
    journal_file = control_dir / "journal.json"
    saved_config_dir = control_dir / "saved_config"
    phase = journal.get("phase", "planned")
    item_states: Dict[str, Dict[str, bool]] = journal.setdefault("item_states", {})
    created_directories: List[str] = journal.setdefault("created_directories", [])

    # Phase: planned -> copy
    if phase == "planned":
        if plan.companion_create and plan.companion_dir is not None:
            if not journal.get("created_companion"):
                plan.companion_dir.mkdir(parents=True, exist_ok=True)
                _run_git_cmd(plan.companion_dir, ["init", "-q"])
                journal["created_companion"] = True
                _write_atomic_json(journal_file, journal)

        for it in plan.items:
            if it.kind == "move":
                src = it.source
                dst = it.destination
                if dst is None:
                    continue
                src_key = str(src)
                if item_states.get(src_key, {}).get("copied"):
                    if dst.exists() or dst.is_symlink():
                        continue

                # Missing destination parents
                parents_to_create = []
                curr = dst.parent
                while not curr.exists():
                    parents_to_create.append(curr)
                    curr = curr.parent
                for d in reversed(parents_to_create):
                    d.mkdir(parents=False, exist_ok=True)
                    if str(d) not in created_directories:
                        created_directories.append(str(d))

                # Refuse if destination exists and is not hash-identical
                if dst.exists() or dst.is_symlink():
                    src_sha, _, _ = _calc_file_meta(src)
                    dst_sha, _, _ = _calc_file_meta(dst)
                    if src.is_symlink() and dst.is_symlink():
                        try:
                            if os.readlink(src) != os.readlink(dst):
                                raise PlacementSwitchError(
                                    f"Destination symlink {dst} targets differ."
                                )
                        except OSError as e:
                            raise PlacementSwitchError(
                                f"Destination symlink {dst} unreadable: {e}"
                            )
                    elif src_sha != dst_sha or src_sha is None:
                        raise PlacementSwitchError(
                            f"Destination {dst} already exists and is not hash-identical to source."
                        )
                else:
                    shutil.copy2(src, dst, follow_symlinks=False)

                item_states.setdefault(src_key, {})["copied"] = True
                journal["item_states"] = item_states
                journal["created_directories"] = created_directories
                _write_atomic_json(journal_file, journal)

        journal["phase"] = "copied"
        _write_atomic_json(journal_file, journal)
        phase = "copied"

        if fault_injection == "after-copy":
            raise PlacementSwitchError("Fault injected: after-copy")

    # Phase: copied -> verify & stage
    if phase == "copied":
        verified_count = 0
        for it in plan.items:
            if it.kind == "move":
                dst = it.destination
                if dst is None or (not dst.exists() and not dst.is_symlink()):
                    raise PlacementSwitchError(
                        f"Destination missing during verify: {dst}"
                    )
                if it.source.is_symlink():
                    if not dst.is_symlink() or os.readlink(dst) != os.readlink(
                        it.source
                    ):
                        raise PlacementSwitchError(
                            f"Destination symlink {dst} does not match source."
                        )
                else:
                    d_sha, d_size, d_mode = _calc_file_meta(dst)
                    if d_sha != it.sha256 or d_size != it.size:
                        raise PlacementSwitchError(
                            f"Destination {dst} hash or size mismatch during verify."
                        )
                    if it.mode is not None and stat.S_IMODE(d_mode) != stat.S_IMODE(
                        it.mode
                    ):
                        raise PlacementSwitchError(
                            f"Destination {dst} mode mismatch during verify."
                        )
                verified_count += 1
                if fault_injection == "mid-verify" and verified_count == 1:
                    raise PlacementSwitchError("Fault injected: mid-verify")

        staged_target: list[str] = []
        staged_companion: list[str] = []
        repo_res = repo.resolve()
        companion_res = (
            plan.companion_dir.resolve() if plan.companion_dir is not None else None
        )

        dest_rels_target: list[str] = []
        dest_rels_comp: list[str] = []

        for it in plan.items:
            if it.kind == "move" and it.destination is not None:
                try:
                    d_res = it.destination.resolve()
                    if it.dest_git == "target":
                        dest_rels_target.append(d_res.relative_to(repo_res).as_posix())
                    elif it.dest_git == "companion" and companion_res is not None:
                        dest_rels_comp.append(
                            d_res.relative_to(companion_res).as_posix()
                        )
                except (ValueError, OSError):
                    pass

        # Target staging
        if dest_rels_target:
            created_gi = engine._ensure_aw_gitignore(repo)
            if created_gi:
                journal["created_aw_gitignore"] = True
                _run_git_cmd(repo, ["add", "--", ".aw/.gitignore"], check=False)

            res_ci = subprocess.run(
                ["git", "check-ignore", "--stdin", "-n", "-v", "--non-matching"],
                cwd=str(repo),
                input="\n".join(dest_rels_target) + "\n",
                capture_output=True,
                text=True,
                check=False,
                env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
            )
            target_non_ignored = [
                line[3:]
                for line in res_ci.stdout.splitlines()
                if line.startswith("::\t")
            ]
            if target_non_ignored:
                _run_git_cmd(
                    repo,
                    ["add", "--pathspec-from-file=-"],
                    input_str="\n".join(target_non_ignored) + "\n",
                    check=True,
                )
            staged_target = sorted(target_non_ignored)

        # Companion staging
        if dest_rels_comp and plan.companion_dir is not None:
            _ensure_companion_gitignore(plan.companion_dir, journal)
            res_ci_comp = subprocess.run(
                ["git", "check-ignore", "--stdin", "-n", "-v", "--non-matching"],
                cwd=str(plan.companion_dir),
                input="\n".join(dest_rels_comp) + "\n",
                capture_output=True,
                text=True,
                check=False,
                env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
            )
            comp_non_ignored = [
                line[3:]
                for line in res_ci_comp.stdout.splitlines()
                if line.startswith("::\t")
            ]
            if fault_injection == "mid-companion-stage":
                if comp_non_ignored:
                    _run_git_cmd(
                        plan.companion_dir,
                        ["add", "--", comp_non_ignored[0]],
                        check=True,
                    )
                    staged_companion = [comp_non_ignored[0]]
                    journal["staged"] = {
                        "target": staged_target,
                        "companion": staged_companion,
                    }
                    journal["staged_paths"] = staged_target
                    _write_atomic_json(journal_file, journal)
                    raise PlacementSwitchError("Fault injected: mid-companion-stage")
                elif plan.companion_action is not None:
                    raise PlacementSwitchError("Fault injected: mid-companion-stage")

            if comp_non_ignored:
                _run_git_cmd(
                    plan.companion_dir,
                    ["add", "--pathspec-from-file=-"],
                    input_str="\n".join(comp_non_ignored) + "\n",
                    check=True,
                )
            staged_companion = sorted(comp_non_ignored)
        elif fault_injection == "mid-companion-stage":
            raise PlacementSwitchError("Fault injected: mid-companion-stage")

        journal["staged"] = {
            "target": staged_target,
            "companion": staged_companion,
        }
        journal["staged_paths"] = staged_target
        journal["phase"] = "verified"
        _write_atomic_json(journal_file, journal)
        phase = "verified"

    # Phase: verified -> switch
    if phase == "verified":
        new_proj_file = plan.to_config_dir / "project.json"
        new_local_file = plan.to_config_dir / "local.json"
        new_config_paths = [str(new_proj_file), str(new_local_file)]
        journal["new_config_paths"] = new_config_paths
        _write_atomic_json(journal_file, journal)

        # 1. Project policy write
        old_proj_file = saved_config_dir / "project.json"
        if not old_proj_file.exists():
            for alt in ("config.json", "policy.json"):
                if (saved_config_dir / alt).exists():
                    old_proj_file = saved_config_dir / alt
                    break

        raw_proj = {}
        if old_proj_file.exists():
            try:
                raw_proj = json.loads(old_proj_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        existing_role = None
        existing_enabled_hosts = None
        existing_consent: Dict[str, bool] = {}
        existing_cutovers = None
        existing_setids = None
        existing_unknown: Dict[str, Any] = {}

        if isinstance(raw_proj, dict):
            try:
                parsed_proj = parse_portable_policy(raw_proj)
                existing_role = parsed_proj.role
                existing_enabled_hosts = parsed_proj.enabled_hosts
                existing_cutovers = parsed_proj.cutovers
                existing_setids = parsed_proj.setids
                existing_unknown = dict(parsed_proj.unknown_fields or {})
                existing_consent = dict(parsed_proj.non_secret_consent or {})
            except ValueError:
                known_proj_keys = {
                    "schema_version",
                    "preset",
                    "role",
                    "placements",
                    "git_policies",
                    "enabled_hosts",
                    "non_secret_consent",
                    "delivery_mode",
                    "records_backend",
                    "cutovers",
                    "setids",
                }
                existing_role = raw_proj.get("role")
                existing_enabled_hosts = raw_proj.get("enabled_hosts")
                if isinstance(raw_proj.get("cutovers"), dict):
                    existing_cutovers = dict(raw_proj["cutovers"])
                if isinstance(raw_proj.get("setids"), dict):
                    existing_setids = dict(raw_proj["setids"])
                if isinstance(raw_proj.get("non_secret_consent"), dict):
                    existing_consent = dict(raw_proj["non_secret_consent"])
                existing_unknown = {
                    k: v for k, v in raw_proj.items() if k not in known_proj_keys
                }

        pls, gps, dm, rb, _ = get_preset_defaults(new_policy.preset)
        new_placements = new_policy.placements or pls
        new_git_policies = new_policy.git_policies or gps
        new_delivery_mode = new_policy.delivery_mode or dm
        new_records_backend = new_policy.records_backend or rb
        role_to_use = existing_role or getattr(new_policy, "role", None) or "target"
        hosts_to_use = (
            existing_enabled_hosts
            if existing_enabled_hosts is not None
            else getattr(new_policy, "enabled_hosts", [])
        )
        merged_consent = {
            **existing_consent,
            **(getattr(new_policy, "non_secret_consent", None) or {}),
        }

        new_proj_schema = ProjectPolicySchema(
            schema_version=2,
            preset=new_policy.preset,
            role=role_to_use,
            placements=new_placements,
            git_policies=new_git_policies,
            enabled_hosts=hosts_to_use,
            non_secret_consent=merged_consent if merged_consent else None,
            delivery_mode=new_delivery_mode,
            records_backend=new_records_backend,
            cutovers=existing_cutovers,
            setids=existing_setids,
            unknown_fields=existing_unknown if existing_unknown else None,
        )
        _write_atomic_json(new_proj_file, new_proj_schema.to_dict())

        # 2. Local binding write
        old_local_file = saved_config_dir / "local.json"
        raw_local = {}
        if old_local_file.exists():
            try:
                raw_local = json.loads(old_local_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        existing_slug = ""
        existing_common = None
        existing_worktree = None
        existing_companion = None
        existing_overrides: Dict[str, Any] = {}
        existing_aliases: Dict[str, str] = {}
        existing_local_unknown: Dict[str, Any] = {}

        if isinstance(raw_local, dict):
            try:
                parsed_local = parse_local_binding(raw_local)
                existing_slug = parsed_local.human_slug
                existing_common = parsed_local.common_dir
                existing_worktree = parsed_local.worktree_path
                existing_companion = parsed_local.companion_dir
                existing_overrides = dict(parsed_local.runtime_overrides or {})
                existing_aliases = dict(parsed_local.local_aliases or {})
                existing_local_unknown = dict(parsed_local.unknown_fields or {})
            except ValueError:
                known_local_keys = {
                    "schema_version",
                    "project_id",
                    "human_slug",
                    "common_dir",
                    "worktree_path",
                    "companion_dir",
                    "runtime_overrides",
                    "local_aliases",
                }
                existing_slug = str(raw_local.get("human_slug") or "")
                existing_common = raw_local.get("common_dir")
                existing_worktree = raw_local.get("worktree_path")
                existing_companion = raw_local.get("companion_dir")
                if isinstance(raw_local.get("runtime_overrides"), dict):
                    existing_overrides = dict(raw_local["runtime_overrides"])
                if isinstance(raw_local.get("local_aliases"), dict):
                    existing_aliases = dict(raw_local["local_aliases"])
                existing_local_unknown = {
                    k: v for k, v in raw_local.items() if k not in known_local_keys
                }

        if plan.companion_action == "attach":
            comp_dir_val = str(plan.companion_dir) if plan.companion_dir else None
        elif plan.companion_action == "detach":
            comp_dir_val = None
        else:
            comp_dir_val = (
                getattr(new_policy, "companion_dir", None) or existing_companion
            )

        new_local_schema = LocalBindingSchema(
            schema_version=2,
            project_id=plan.project_id,
            human_slug=existing_slug,
            common_dir=existing_common,
            worktree_path=existing_worktree,
            companion_dir=comp_dir_val,
            runtime_overrides=existing_overrides if existing_overrides else None,
            local_aliases=existing_aliases if existing_aliases else None,
            unknown_fields=existing_local_unknown if existing_local_unknown else None,
        )
        _write_atomic_json(new_local_file, new_local_schema.to_dict())

        # 3. Remove old config files (skipped for in-place)
        if plan.direction != "in-place":
            tracked_files = _get_tracked_files(repo)
            for cand in ("project.json", "local.json", "config.json", "policy.json"):
                cand_path = plan.from_config_dir / cand
                if cand_path.exists() or cand_path.is_symlink():
                    try:
                        rel = cand_path.resolve().relative_to(repo.resolve()).as_posix()
                        if rel in tracked_files:
                            _run_git_cmd(
                                repo, ["rm", "-q", "-f", "--", rel], check=False
                            )
                        else:
                            cand_path.unlink()
                    except (ValueError, OSError):
                        cand_path.unlink()

        # Companion attach / detach
        if plan.companion_action == "attach":
            if plan.companion_dir is None:
                raise PlacementSwitchError(
                    "Companion directory required for companion attach."
                )
            comp_ident_p = plan.companion_dir / ".aw" / "companion_identity.json"
            target_attach_p = (
                repo / ".aw" / "state" / "durable" / "companion_attachment.json"
            )
            journal["attach_started"] = True
            journal["prior_companion_identity_bytes"] = (
                comp_ident_p.read_text(encoding="utf-8")
                if comp_ident_p.is_file()
                else None
            )
            journal["prior_attachment_record_bytes"] = (
                target_attach_p.read_text(encoding="utf-8")
                if target_attach_p.is_file()
                else None
            )
            journal["companion_existed_before_attach"] = {
                ".aw": (plan.companion_dir / ".aw").exists(),
                ".aw/config": (plan.companion_dir / ".aw" / "config").exists(),
                ".aw/state/durable": (
                    plan.companion_dir / ".aw" / "state" / "durable"
                ).exists(),
                ".aw/records": (plan.companion_dir / ".aw" / "records").exists(),
                ".gitignore": (plan.companion_dir / ".gitignore").exists(),
            }
            _write_atomic_json(journal_file, journal)

            try:
                storage.attach_companion(
                    repo,
                    plan.companion_dir,
                    aw_home=str(eff_aw_home),
                )
            except Exception as exc:
                _perform_rollback(repo, eff_aw_home, control_dir, journal, plan)
                raise PlacementSwitchError(str(exc)) from exc

        elif plan.companion_action == "detach":
            target_attach_p = (
                repo / ".aw" / "state" / "durable" / "companion_attachment.json"
            )
            journal["prior_attachment_record_bytes"] = (
                target_attach_p.read_text(encoding="utf-8")
                if target_attach_p.is_file()
                else None
            )
            _write_atomic_json(journal_file, journal)
            storage.detach_companion(repo, aw_home=str(eff_aw_home))

        if plan.config_retrack == "untrack":
            _run_git_cmd(
                repo,
                ["rm", "-q", "--cached", "--", ".aw/config/project.json"],
                check=False,
            )
        elif plan.config_retrack == "track":
            _run_git_cmd(repo, ["add", "--", ".aw/config/project.json"], check=False)

        if fault_injection == "after-attach":
            raise PlacementSwitchError("Fault injected: after-attach")

        journal["phase"] = "switched"
        _write_atomic_json(journal_file, journal)
        phase = "switched"

        if fault_injection == "after-switch":
            raise PlacementSwitchError("Fault injected: after-switch")

        # Invariant assertion
        resolved_dir = project_config_dir(repo, aw_home=eff_aw_home)
        curr_ctx = resolve_project_context(target_repo=str(repo), aw_home=eff_aw_home)
        new_ctx = resolve_project_context(
            target_repo=str(repo),
            delivery_mode=new_policy.delivery_mode,
            records_backend=new_policy.records_backend,
            preset=new_policy.preset,
            role=new_policy.role,
            companion_dir=new_policy.companion_dir,
            aw_home=eff_aw_home,
        )
        expected_records = Path(new_ctx.physical_classes["records"]).resolve()
        actual_records = Path(curr_ctx.physical_classes["records"]).resolve()

        if (
            resolved_dir.resolve() != plan.to_config_dir.resolve()
            or actual_records != expected_records
            or curr_ctx.preset != plan.to_preset
        ):
            _perform_rollback(repo, eff_aw_home, control_dir, journal, plan)
            raise PlacementSwitchError(
                f"Authority flip invariant violated: expected config dir {plan.to_config_dir} (got {resolved_dir}), "
                f"expected records {expected_records} (got {actual_records}), "
                f"expected preset {plan.to_preset} (got {curr_ctx.preset})"
            )

    # Phase: switched -> sources-removed
    if phase == "switched":
        resolved_dir = project_config_dir(repo, aw_home=eff_aw_home)
        curr_ctx = resolve_project_context(target_repo=str(repo), aw_home=eff_aw_home)
        new_ctx = resolve_project_context(
            target_repo=str(repo),
            delivery_mode=new_policy.delivery_mode,
            records_backend=new_policy.records_backend,
            preset=new_policy.preset,
            role=new_policy.role,
            companion_dir=new_policy.companion_dir,
            aw_home=eff_aw_home,
        )
        expected_records = Path(new_ctx.physical_classes["records"]).resolve()
        actual_records = Path(curr_ctx.physical_classes["records"]).resolve()

        if (
            resolved_dir.resolve() != plan.to_config_dir.resolve()
            or actual_records != expected_records
            or curr_ctx.preset != plan.to_preset
        ):
            _perform_rollback(repo, eff_aw_home, control_dir, journal, plan)
            raise PlacementSwitchError(
                f"Authority flip invariant violated: expected config dir {plan.to_config_dir} (got {resolved_dir}), "
                f"expected records {expected_records} (got {actual_records}), "
                f"expected preset {plan.to_preset} (got {curr_ctx.preset})"
            )
        journal["phase"] = "sources-removed"
        _write_atomic_json(journal_file, journal)
        phase = "sources-removed"

    # Phase: sources-removed
    if phase == "sources-removed":
        tracked_target_rels: list[str] = []
        tracked_comp_rels: list[str] = []
        repo_res = repo.resolve()
        comp_res = (
            plan.companion_dir.resolve() if plan.companion_dir is not None else None
        )

        for it in plan.items:
            if it.kind == "move":
                src = it.source
                src_key = str(src)
                if item_states.get(src_key, {}).get("removed"):
                    continue
                if src.exists() or src.is_symlink():
                    if fault_injection == "mid-source-removal":
                        try:
                            if it.source_git == "target" and it.tracked:
                                rel = src.resolve().relative_to(repo_res).as_posix()
                                _run_git_cmd(
                                    repo, ["rm", "-q", "-f", "--", rel], check=False
                                )
                            elif (
                                it.source_git == "companion"
                                and it.tracked
                                and plan.companion_dir is not None
                            ):
                                rel = src.resolve().relative_to(comp_res).as_posix()
                                _run_git_cmd(
                                    plan.companion_dir,
                                    ["rm", "-q", "-f", "--", rel],
                                    check=False,
                                )
                            else:
                                src.unlink()
                        except (ValueError, OSError):
                            src.unlink()
                        item_states.setdefault(src_key, {})["removed"] = True
                        journal["item_states"] = item_states
                        _write_atomic_json(journal_file, journal)
                        raise PlacementSwitchError("Fault injected: mid-source-removal")

                    try:
                        if it.source_git == "target" and it.tracked:
                            rel = src.resolve().relative_to(repo_res).as_posix()
                            tracked_target_rels.append(rel)
                        elif (
                            it.source_git == "companion"
                            and it.tracked
                            and plan.companion_dir is not None
                        ):
                            rel = src.resolve().relative_to(comp_res).as_posix()
                            tracked_comp_rels.append(rel)
                        else:
                            src.unlink()
                    except (ValueError, OSError):
                        src.unlink()
                    item_states.setdefault(src_key, {})["removed"] = True

        if tracked_target_rels:
            _run_git_cmd(
                repo, ["rm", "-q", "-f", "--"] + tracked_target_rels, check=False
            )
        if tracked_comp_rels and plan.companion_dir is not None:
            _run_git_cmd(
                plan.companion_dir,
                ["rm", "-q", "-f", "--"] + tracked_comp_rels,
                check=False,
            )

        # Discard items sources
        if plan.retire_side == "target":
            retired_dirs = [
                repo / ".aw" / "system",
                repo / ".aw" / "state",
                repo / ".aw" / "config",
            ]
        elif plan.retire_side == "home":
            home_p = eff_aw_home / "projects" / plan.project_id
            retired_dirs = [
                home_p / "system",
                home_p / "state",
                home_p / "config",
                home_p / "worktrees" / ".owners",
            ]
        else:
            retired_dirs = []

        for it in plan.items:
            if it.kind == "discard":
                src = it.source
                src_key = str(src)
                if item_states.get(src_key, {}).get("removed"):
                    continue
                if src.exists() or src.is_symlink():
                    is_in_retired = False
                    for rd in retired_dirs:
                        try:
                            src.resolve().relative_to(rd.resolve())
                            is_in_retired = True
                            break
                        except (ValueError, OSError):
                            pass
                    if not is_in_retired:
                        try:
                            if it.source_git == "target" and it.tracked:
                                rel = src.resolve().relative_to(repo_res).as_posix()
                                _run_git_cmd(
                                    repo, ["rm", "-q", "-f", "--", rel], check=False
                                )
                            elif (
                                it.source_git == "companion"
                                and it.tracked
                                and plan.companion_dir is not None
                            ):
                                rel = src.resolve().relative_to(comp_res).as_posix()
                                _run_git_cmd(
                                    plan.companion_dir,
                                    ["rm", "-q", "-f", "--", rel],
                                    check=False,
                                )
                            else:
                                src.unlink()
                        except (ValueError, OSError):
                            src.unlink()
                    item_states.setdefault(src_key, {})["removed"] = True

        journal["item_states"] = item_states
        _write_atomic_json(journal_file, journal)

        if fault_injection == "before-retire":
            raise PlacementSwitchError("Fault injected: before-retire")

        # Retire
        journal["retire_started"] = True
        _write_atomic_json(journal_file, journal)

        # Leftovers check
        if plan.companion_action == "detach" and plan.companion_dir is not None:
            old_records_root = plan.companion_dir / "records"
        elif plan.direction == "to-home":
            old_records_root = plan.from_config_dir.parent / "records"
        else:
            old_records_root = eff_aw_home / "projects" / plan.project_id / "records"

        plan_sources = {it.source.resolve() for it in plan.items}
        unplanned_leftovers = []
        if old_records_root.is_dir():
            for p in old_records_root.rglob("*"):
                if p.is_file() and p.resolve() not in plan_sources:
                    try:
                        if (
                            plan.companion_action == "detach"
                            and plan.companion_dir is not None
                        ):
                            rel = p.resolve().relative_to(comp_res).as_posix()
                        else:
                            rel = p.resolve().relative_to(repo.resolve()).as_posix()
                    except ValueError:
                        rel = str(p)
                    unplanned_leftovers.append(rel)

        journal["unplanned_leftovers"] = unplanned_leftovers

        if plan.retire_side is None:
            retire_actions = []
        else:
            preserve = set()
            if plan.retire_side == "target" and unplanned_leftovers:
                preserve.add(".aw/records")
            if plan.companion_action == "attach":
                preserve.add(".aw/state/durable/companion_attachment.json")

            retire_actions = retire_footprint(
                repo,
                plan.retire_side,
                preserve=preserve,
                aw_home=eff_aw_home,
            )
            journal["retire_actions"] = retire_actions

        journal["phase"] = "retired"
        _write_atomic_json(journal_file, journal)
        phase = "retired"

    # Phase: retired -> done
    if phase == "retired":
        new_ctx = resolve_project_context(
            target_repo=str(repo),
            delivery_mode=new_policy.delivery_mode,
            records_backend=new_policy.records_backend,
            preset=new_policy.preset,
            role=new_policy.role,
            companion_dir=new_policy.companion_dir,
            aw_home=eff_aw_home,
        )
        new_durable = Path(new_ctx.physical_classes["state_durable"])
        receipt_path = new_durable / "migrations" / "placement_switch_receipt.json"

        staged_paths = journal.get("staged_paths", [])
        staged_map = journal.get("staged", {"target": staged_paths, "companion": []})
        unplanned_leftovers = journal.get("unplanned_leftovers", [])
        retire_actions = journal.get("retire_actions", [])
        item_counts = {
            "move": len([it for it in plan.items if it.kind == "move"]),
            "discard": len([it for it in plan.items if it.kind == "discard"]),
            "rewrite": len([it for it in plan.items if it.kind == "rewrite"]),
        }

        receipt_data = {
            "schema_version": 1,
            "transaction_id": journal["transaction_id"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "from_preset": plan.from_preset,
            "to_preset": plan.to_preset,
            "from_config_dir": str(plan.from_config_dir),
            "to_config_dir": str(plan.to_config_dir),
            "direction": plan.direction,
            "retire_side": plan.retire_side,
            "companion_dir": str(plan.companion_dir) if plan.companion_dir else None,
            "companion_action": plan.companion_action,
            "item_counts": item_counts,
            "staged_path_count": len(staged_paths),
            "staged_paths": staged_paths,
            "staged": staged_map,
            "unplanned_leftovers": unplanned_leftovers,
            "retire_actions": retire_actions,
        }
        _write_atomic_json(receipt_path, receipt_data)

        shutil.rmtree(control_dir, ignore_errors=True)

        return SwitchResult(
            transaction_id=journal["transaction_id"],
            from_preset=plan.from_preset,
            to_preset=plan.to_preset,
            from_config_dir=plan.from_config_dir,
            to_config_dir=plan.to_config_dir,
            direction=plan.direction,
            items_moved=item_counts["move"],
            items_discarded=item_counts["discard"],
            items_rewritten=item_counts["rewrite"],
            staged_paths=staged_paths,
            retire_actions=retire_actions,
            receipt_path=receipt_path,
            unplanned_leftovers=unplanned_leftovers,
            companion_dir=plan.companion_dir,
            companion_action=plan.companion_action,
            staged=staged_map,
        )

    raise PlacementSwitchError(f"Unknown placement switch phase: {phase!r}")


def _run_records_transaction(
    repo: Path,
    eff_aw_home: Path,
    control_dir: Path,
    journal: Dict[str, Any],
    plan: SwitchPlan,
    new_policy: ProjectPolicy,
    *,
    fault_injection: Optional[str] = None,
) -> SwitchResult:
    journal_file = control_dir / "journal.json"
    saved_config_dir = control_dir / "saved_config"
    phase = journal.get("phase", "planned")
    item_states: Dict[str, Dict[str, bool]] = journal.setdefault("item_states", {})
    created_directories: List[str] = journal.setdefault("created_directories", [])

    old_records_root = Path(
        journal.get("old_records_root")
        or (
            plan.from_config_dir.parent / "records"
            if plan.direction == "records-to-home"
            else eff_aw_home / "projects" / plan.project_id / "records"
        )
    )
    new_records_root = Path(
        journal.get("new_records_root")
        or (
            eff_aw_home / "projects" / plan.project_id / "records"
            if plan.direction == "records-to-home"
            else plan.to_config_dir.parent / "records"
        )
    )
    journal.setdefault("old_records_root", str(old_records_root))
    journal.setdefault("new_records_root", str(new_records_root))

    # Phase: planned -> copy
    if phase == "planned":
        for it in plan.items:
            if it.kind == "move":
                src = it.source
                dst = it.destination
                if dst is None:
                    continue
                src_key = str(src)
                st = item_states.get(src_key, {})
                if st.get("copied") or st.get("preexisting"):
                    if dst.exists() or dst.is_symlink():
                        continue

                # Missing destination parents
                parents_to_create = []
                curr = dst.parent
                while not curr.exists():
                    parents_to_create.append(curr)
                    curr = curr.parent
                for d in reversed(parents_to_create):
                    d.mkdir(parents=False, exist_ok=True)
                    if str(d) not in created_directories:
                        created_directories.append(str(d))

                # Check if destination exists
                if dst.exists() or dst.is_symlink():
                    src_sha, _, _ = _calc_file_meta(src)
                    dst_sha, _, _ = _calc_file_meta(dst)
                    if src.is_symlink() and dst.is_symlink():
                        try:
                            if os.readlink(src) != os.readlink(dst):
                                raise PlacementSwitchError(
                                    f"Destination symlink {dst} targets differ."
                                )
                        except OSError as e:
                            raise PlacementSwitchError(
                                f"Destination symlink {dst} unreadable: {e}"
                            )
                    elif src_sha != dst_sha or src_sha is None:
                        raise PlacementSwitchError(
                            f"Destination {dst} already exists and is not hash-identical to source."
                        )
                    item_states.setdefault(src_key, {})["preexisting"] = True
                    item_states[src_key]["copied"] = False
                else:
                    shutil.copy2(src, dst, follow_symlinks=False)
                    item_states.setdefault(src_key, {})["copied"] = True
                    item_states[src_key]["preexisting"] = False

                journal["item_states"] = item_states
                journal["created_directories"] = created_directories
                _write_atomic_json(journal_file, journal)

        journal["phase"] = "copied"
        _write_atomic_json(journal_file, journal)
        phase = "copied"

        if fault_injection == "after-copy":
            raise PlacementSwitchError("Fault injected: after-copy")

    # Phase: copied -> verify & stage
    if phase == "copied":
        verified_count = 0
        for it in plan.items:
            if it.kind == "move":
                dst = it.destination
                if dst is None or (not dst.exists() and not dst.is_symlink()):
                    raise PlacementSwitchError(
                        f"Destination missing during verify: {dst}"
                    )
                if it.source.is_symlink():
                    if not dst.is_symlink() or os.readlink(dst) != os.readlink(
                        it.source
                    ):
                        raise PlacementSwitchError(
                            f"Destination symlink {dst} does not match source."
                        )
                else:
                    d_sha, d_size, d_mode = _calc_file_meta(dst)
                    if d_sha != it.sha256 or d_size != it.size:
                        raise PlacementSwitchError(
                            f"Destination {dst} hash or size mismatch during verify."
                        )
                    if it.mode is not None and stat.S_IMODE(d_mode) != stat.S_IMODE(
                        it.mode
                    ):
                        raise PlacementSwitchError(
                            f"Destination {dst} mode mismatch during verify."
                        )
                verified_count += 1
                if fault_injection == "mid-verify" and verified_count == 1:
                    raise PlacementSwitchError("Fault injected: mid-verify")

        staged_paths = []
        if plan.direction == "records-to-target":
            created_gi = engine._ensure_aw_gitignore(repo)
            if created_gi:
                journal["created_aw_gitignore"] = True
                _run_git_cmd(repo, ["add", "--", ".aw/.gitignore"], check=False)

            repo_res = repo.resolve()
            dest_rels = []
            for it in plan.items:
                if it.kind == "move" and it.destination is not None:
                    try:
                        d_res = it.destination.resolve()
                        if repo_res in d_res.parents or d_res == repo_res:
                            dest_rels.append(d_res.relative_to(repo_res).as_posix())
                    except (ValueError, OSError):
                        pass

            if dest_rels:
                res_ci = subprocess.run(
                    ["git", "check-ignore", "--stdin", "-n", "-v", "--non-matching"],
                    cwd=str(repo),
                    input="\n".join(dest_rels) + "\n",
                    capture_output=True,
                    text=True,
                    check=False,
                )
                non_ignored = [
                    line[3:]
                    for line in res_ci.stdout.splitlines()
                    if line.startswith("::\t")
                ]
                if non_ignored:
                    _run_git_cmd(
                        repo,
                        ["add", "--pathspec-from-file=-"],
                        input_str="\n".join(non_ignored) + "\n",
                        check=True,
                    )
                staged_paths = sorted(non_ignored)

        journal["staged_paths"] = staged_paths
        journal["phase"] = "verified"
        _write_atomic_json(journal_file, journal)
        phase = "verified"

    # Phase: verified -> switch
    if phase == "verified":
        new_target_rb = new_policy.records_backend
        if new_target_rb == "repository":
            rec_placement = "target-tracked"
            rec_git = "target-git"
        elif new_target_rb == "repository-untracked":
            rec_placement = "target-ignored"
            rec_git = "ignored"
        elif new_target_rb == "home":
            rec_placement = "home-untracked"
            rec_git = "untracked"
        else:
            raise PlacementSwitchError(
                f"Unsupported records_backend for records switch: {new_target_rb}"
            )

        # 1. Project policy rewrite
        old_proj_file = saved_config_dir / "project.json"
        if not old_proj_file.exists():
            for alt in ("config.json", "policy.json"):
                if (saved_config_dir / alt).exists():
                    old_proj_file = saved_config_dir / alt
                    break

        raw_proj = {}
        if old_proj_file.exists():
            try:
                raw_proj = json.loads(old_proj_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        if not isinstance(raw_proj, dict):
            raw_proj = {}

        new_proj_data = dict(raw_proj)
        new_proj_data["records_backend"] = new_target_rb
        pls = dict(new_proj_data.get("placements") or {})
        pls["records"] = rec_placement
        new_proj_data["placements"] = pls
        gps = dict(new_proj_data.get("git_policies") or {})
        gps["records"] = rec_git
        new_proj_data["git_policies"] = gps

        target_proj_file = plan.to_config_dir / old_proj_file.name
        tmp_proj = plan.to_config_dir / f".tmp_{old_proj_file.name}"
        with open(tmp_proj, "w", encoding="utf-8") as f:
            json.dump(new_proj_data, f, indent=2)
            f.write("\n")
        os.replace(tmp_proj, target_proj_file)

        proj_item = next(
            (it for it in plan.items if it.item_class == "config_project"), None
        )
        if proj_item and proj_item.tracked:
            try:
                rel_proj = (
                    target_proj_file.resolve().relative_to(repo.resolve()).as_posix()
                )
                _run_git_cmd(repo, ["add", "--", rel_proj], check=True)
            except (ValueError, OSError):
                pass

        # 2. Local binding rewrite (if local.json has records_backend)
        old_local_file = saved_config_dir / "local.json"
        if old_local_file.exists():
            try:
                raw_local = json.loads(old_local_file.read_text(encoding="utf-8"))
                if isinstance(raw_local, dict) and "records_backend" in raw_local:
                    new_local_data = dict(raw_local)
                    new_local_data["records_backend"] = new_target_rb
                    target_local_file = plan.to_config_dir / "local.json"
                    tmp_local = plan.to_config_dir / ".tmp_local.json"
                    with open(tmp_local, "w", encoding="utf-8") as f:
                        json.dump(new_local_data, f, indent=2)
                        f.write("\n")
                    os.replace(tmp_local, target_local_file)
            except Exception:
                pass

        journal["phase"] = "switched"
        _write_atomic_json(journal_file, journal)
        phase = "switched"

        if fault_injection == "after-switch":
            raise PlacementSwitchError("Fault injected: after-switch")

    # Phase: switched -> sources-removed
    if phase == "switched":
        resolved_ctx = resolve_project_context(
            target_repo=str(repo), aw_home=eff_aw_home
        )
        resolved_records = Path(resolved_ctx.logical_roots["records"]).resolve()
        expected_records = new_records_root.resolve()

        if resolved_records != expected_records:
            _perform_records_rollback(repo, eff_aw_home, control_dir, journal, plan)
            raise PlacementSwitchError(
                f"Authority flip invariant violated: expected records root {expected_records}, got {resolved_records}"
            )

        journal["phase"] = "sources-removed"
        _write_atomic_json(journal_file, journal)
        phase = "sources-removed"

    # Phase: sources-removed
    if phase == "sources-removed":
        tracked_in_tree_rels = []
        tracked_files = _get_tracked_files(repo)

        for it in plan.items:
            if it.item_class == "records" and it.kind in ("move", "discard"):
                src = it.source
                src_key = str(src)
                if item_states.get(src_key, {}).get("removed"):
                    continue
                if src.exists() or src.is_symlink():
                    if fault_injection == "mid-source-removal":
                        try:
                            rel = src.resolve().relative_to(repo.resolve()).as_posix()
                            if rel in tracked_files or it.tracked:
                                _run_git_cmd(
                                    repo, ["rm", "-q", "-f", "--", rel], check=False
                                )
                            else:
                                src.unlink()
                        except (ValueError, OSError):
                            src.unlink()
                        item_states.setdefault(src_key, {})["removed"] = True
                        journal["item_states"] = item_states
                        _write_atomic_json(journal_file, journal)
                        raise PlacementSwitchError("Fault injected: mid-source-removal")

                    try:
                        rel = src.resolve().relative_to(repo.resolve()).as_posix()
                        if rel in tracked_files or it.tracked:
                            tracked_in_tree_rels.append(rel)
                        else:
                            src.unlink()
                    except (ValueError, OSError):
                        src.unlink()
                    item_states.setdefault(src_key, {})["removed"] = True
                    journal["item_states"] = item_states
                    _write_atomic_json(journal_file, journal)

        if tracked_in_tree_rels:
            _run_git_cmd(
                repo, ["rm", "-q", "-f", "--"] + tracked_in_tree_rels, check=False
            )

        if old_records_root.is_dir():
            for root, dirs, files in os.walk(old_records_root, topdown=False):
                for d in dirs:
                    dp = Path(root) / d
                    try:
                        dp.rmdir()
                    except OSError:
                        pass
            try:
                old_records_root.rmdir()
            except OSError:
                pass

        journal["phase"] = "done"
        _write_atomic_json(journal_file, journal)
        phase = "done"

    # Phase: done
    if phase == "done":
        new_ctx = resolve_project_context(
            target_repo=str(repo),
            delivery_mode=new_policy.delivery_mode,
            records_backend=new_policy.records_backend,
            preset=new_policy.preset,
            role=new_policy.role,
            companion_dir=new_policy.companion_dir,
            aw_home=eff_aw_home,
        )
        new_durable = Path(new_ctx.physical_classes["state_durable"])
        receipt_path = new_durable / "migrations" / "records_switch_receipt.json"

        plan_sources = {it.source.resolve() for it in plan.items}
        unplanned_leftovers = []
        if old_records_root.is_dir():
            for p in old_records_root.rglob("*"):
                if p.is_file() and p.resolve() not in plan_sources:
                    try:
                        rel = p.resolve().relative_to(repo.resolve()).as_posix()
                    except ValueError:
                        rel = str(p)
                    unplanned_leftovers.append(rel)

        staged_paths = journal.get("staged_paths", [])
        item_counts = {
            "move": len([it for it in plan.items if it.kind == "move"]),
            "discard": len([it for it in plan.items if it.kind == "discard"]),
            "rewrite": len([it for it in plan.items if it.kind == "rewrite"]),
        }

        receipt_data = {
            "schema_version": 1,
            "transaction_id": journal["transaction_id"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mode": "records",
            "from_backend": journal.get("from_records_backend"),
            "to_backend": new_policy.records_backend,
            "from_records_root": str(old_records_root),
            "to_records_root": str(new_records_root),
            "from_preset": plan.from_preset,
            "to_preset": plan.to_preset,
            "from_config_dir": str(plan.from_config_dir),
            "to_config_dir": str(plan.to_config_dir),
            "direction": plan.direction,
            "retire_side": plan.retire_side,
            "item_counts": item_counts,
            "staged_path_count": len(staged_paths),
            "staged_paths": staged_paths,
            "unplanned_leftovers": unplanned_leftovers,
        }
        _write_atomic_json(receipt_path, receipt_data)

        shutil.rmtree(control_dir, ignore_errors=True)

        return SwitchResult(
            transaction_id=journal["transaction_id"],
            from_preset=plan.from_preset,
            to_preset=plan.to_preset,
            from_config_dir=plan.from_config_dir,
            to_config_dir=plan.to_config_dir,
            direction=plan.direction,
            items_moved=item_counts["move"],
            items_discarded=item_counts["discard"],
            items_rewritten=item_counts["rewrite"],
            staged_paths=staged_paths,
            retire_actions=[],
            receipt_path=receipt_path,
            unplanned_leftovers=unplanned_leftovers,
        )

    raise PlacementSwitchError(f"Unknown placement switch phase: {phase!r}")


def execute_placement_switch(
    repo_path: str | Path,
    new_policy: ProjectPolicy,
    *,
    aw_home: Optional[str | Path] = None,
    fault_injection: Optional[str] = None,
) -> SwitchResult:
    """Execute a placement switch transaction (spec Section 8.1)."""
    valid_faults = {
        "after-copy",
        "mid-verify",
        "mid-companion-stage",
        "after-attach",
        "after-switch",
        "mid-source-removal",
        "before-retire",
    }
    if fault_injection is not None and fault_injection not in valid_faults:
        raise ValueError(
            f"Invalid fault_injection: {fault_injection!r}. Must be one of {sorted(valid_faults)}"
        )

    repo, eff_aw_home, control_dir, lock_file, project_id = _resolve_control_and_lock(
        repo_path, aw_home=aw_home
    )
    journal_file = control_dir / "journal.json"
    saved_config_dir = control_dir / "saved_config"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = None

    try:
        try:
            lock_handle = platform_lock.acquire(lock_file)
        except platform_lock.LockBusy as exc:
            raise PlacementSwitchError(
                f"another placement switch is running for project {project_id}"
            ) from exc

        if journal_file.exists():
            raise PlacementSwitchError(
                f"An incomplete placement switch transaction already exists for project {project_id}. "
                "Resume it with resume_placement_switch or roll it back with rollback_placement_switch."
            )

        plan = plan_placement_switch(repo, new_policy, aw_home=eff_aw_home)
        if plan.blockers:
            msgs = [f"- {b}: {plan.blocker_messages.get(b, '')}" for b in plan.blockers]
            raise PlacementSwitchError("Placement switch blocked:\n" + "\n".join(msgs))

        saved_config_dir.mkdir(parents=True, exist_ok=True)
        saved_files = []
        for cand in ("project.json", "local.json", "config.json", "policy.json"):
            cand_p = plan.from_config_dir / cand
            if cand_p.is_file() or cand_p.is_symlink():
                shutil.copy2(cand_p, saved_config_dir / cand, follow_symlinks=False)
                saved_files.append(cand)

        transaction_id = f"ps-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        item_states = {
            str(it.source): {"copied": False, "removed": False} for it in plan.items
        }

        new_policy_dict = (
            new_policy.to_dict()
            if hasattr(new_policy, "to_dict")
            else {
                "preset": getattr(new_policy, "preset", plan.to_preset),
                "role": getattr(new_policy, "role", "target"),
                "placements": getattr(new_policy, "placements", None),
                "git_policies": getattr(new_policy, "git_policies", None),
                "delivery_mode": getattr(new_policy, "delivery_mode", None),
                "records_backend": getattr(new_policy, "records_backend", None),
                "durability_state": getattr(new_policy, "durability_state", None),
                "companion_dir": getattr(new_policy, "companion_dir", None),
                "enabled_hosts": getattr(new_policy, "enabled_hosts", None),
                "non_secret_consent": getattr(new_policy, "non_secret_consent", None),
            }
        )

        journal = {
            "schema_version": 1,
            "transaction_id": transaction_id,
            "phase": "planned",
            "plan": plan.to_dict(),
            "new_policy": new_policy_dict,
            "item_states": item_states,
            "created_directories": [],
            "created_companion": False,
            "created_companion_gitignore": False,
            "created_aw_gitignore": False,
            "saved_config_files": saved_files,
            "new_config_paths": [],
            "staged": {"target": [], "companion": []},
            "staged_paths": [],
            "retire_started": False,
            "retire_actions": [],
            "unplanned_leftovers": [],
        }
        _write_atomic_json(journal_file, journal)

        return _run_transaction(
            repo,
            eff_aw_home,
            control_dir,
            journal,
            plan,
            new_policy,
            fault_injection=fault_injection,
        )

    finally:
        _cleanup_lock(lock_file, lock_handle, control_dir)


def execute_records_root_switch(
    repo_path: str | Path,
    new_policy: ProjectPolicy,
    *,
    aw_home: Optional[str | Path] = None,
    fault_injection: Optional[str] = None,
) -> SwitchResult:
    """Execute a records root switch transaction (IPD fxbm7j / Set rbswitch)."""
    valid_faults = {
        "after-copy",
        "mid-verify",
        "after-switch",
        "mid-source-removal",
    }
    if fault_injection is not None and fault_injection not in valid_faults:
        raise ValueError(
            f"Invalid fault_injection for records mode: {fault_injection!r}. Must be one of {sorted(valid_faults)}"
        )

    repo, eff_aw_home, control_dir, lock_file, project_id = _resolve_control_and_lock(
        repo_path, aw_home=aw_home
    )
    journal_file = control_dir / "journal.json"
    saved_config_dir = control_dir / "saved_config"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = None

    try:
        try:
            lock_handle = platform_lock.acquire(lock_file)
        except platform_lock.LockBusy as exc:
            raise PlacementSwitchError(
                f"another placement switch is running for project {project_id}"
            ) from exc

        if journal_file.exists():
            raise PlacementSwitchError(
                f"An incomplete placement switch transaction already exists for project {project_id}. "
                "Resume it with resume_placement_switch or roll it back with rollback_placement_switch."
            )

        plan = plan_records_root_switch(repo, new_policy, aw_home=eff_aw_home)
        if plan.blockers:
            msgs = [f"- {b}: {plan.blocker_messages.get(b, '')}" for b in plan.blockers]
            raise PlacementSwitchError(
                "Records root switch blocked:\n" + "\n".join(msgs)
            )

        saved_config_dir.mkdir(parents=True, exist_ok=True)
        saved_files = []
        for cand in ("project.json", "local.json", "config.json", "policy.json"):
            cand_p = plan.from_config_dir / cand
            if cand_p.is_file() or cand_p.is_symlink():
                shutil.copy2(cand_p, saved_config_dir / cand, follow_symlinks=False)
                saved_files.append(cand)

        transaction_id = f"rs-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        item_states = {
            str(it.source): {"copied": False, "preexisting": False, "removed": False}
            for it in plan.items
        }

        new_policy_dict = (
            new_policy.to_dict()
            if hasattr(new_policy, "to_dict")
            else {
                "preset": getattr(new_policy, "preset", plan.to_preset),
                "role": getattr(new_policy, "role", "target"),
                "placements": getattr(new_policy, "placements", None),
                "git_policies": getattr(new_policy, "git_policies", None),
                "delivery_mode": getattr(new_policy, "delivery_mode", None),
                "records_backend": getattr(new_policy, "records_backend", None),
                "durability_state": getattr(new_policy, "durability_state", None),
                "companion_dir": getattr(new_policy, "companion_dir", None),
                "enabled_hosts": getattr(new_policy, "enabled_hosts", None),
                "non_secret_consent": getattr(new_policy, "non_secret_consent", None),
            }
        )

        existing_policy = resolve_existing_policy(str(repo))
        from_rb = getattr(existing_policy, "records_backend", None)
        if not from_rb:
            old_ctx = resolve_project_context(
                target_repo=str(repo), aw_home=eff_aw_home
            )
            from_rb = old_ctx.records_backend

        old_records_root = (
            plan.from_config_dir.parent / "records"
            if plan.direction == "records-to-home"
            else eff_aw_home / "projects" / plan.project_id / "records"
        )
        new_records_root = (
            eff_aw_home / "projects" / plan.project_id / "records"
            if plan.direction == "records-to-home"
            else plan.to_config_dir.parent / "records"
        )

        journal = {
            "schema_version": 1,
            "mode": "records",
            "transaction_id": transaction_id,
            "phase": "planned",
            "from_records_backend": from_rb,
            "old_records_root": str(old_records_root),
            "new_records_root": str(new_records_root),
            "plan": plan.to_dict(),
            "new_policy": new_policy_dict,
            "item_states": item_states,
            "created_directories": [],
            "created_aw_gitignore": False,
            "saved_config_files": saved_files,
            "new_config_paths": [],
            "staged_paths": [],
            "unplanned_leftovers": [],
        }
        _write_atomic_json(journal_file, journal)

        return _run_records_transaction(
            repo,
            eff_aw_home,
            control_dir,
            journal,
            plan,
            new_policy,
            fault_injection=fault_injection,
        )

    finally:
        _cleanup_lock(lock_file, lock_handle, control_dir)


def resume_placement_switch(
    repo_path: str | Path,
    *,
    aw_home: Optional[str | Path] = None,
) -> SwitchResult:
    """Resume an in-progress placement switch to completion (E-05)."""
    repo, eff_aw_home, control_dir, lock_file, project_id = _resolve_control_and_lock(
        repo_path, aw_home=aw_home
    )
    journal_file = control_dir / "journal.json"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = None

    try:
        try:
            lock_handle = platform_lock.acquire(lock_file)
        except platform_lock.LockBusy as exc:
            raise PlacementSwitchError(
                f"another placement switch is running for project {project_id}"
            ) from exc

        if not journal_file.exists():
            raise PlacementSwitchError(
                f"No placement switch transaction in progress for project {project_id}."
            )

        journal = _read_json(journal_file)
        mode = journal.get("mode", "placement")
        plan = SwitchPlan.from_dict(journal["plan"])

        if "new_policy" in journal:
            np_data = journal["new_policy"]
            new_policy = ProjectPolicy(
                preset=np_data.get("preset", plan.to_preset),
                role=np_data.get("role", "target"),
                placements=np_data.get("placements"),
                git_policies=np_data.get("git_policies"),
                delivery_mode=np_data.get("delivery_mode"),
                records_backend=np_data.get("records_backend"),
                durability_state=np_data.get("durability_state"),
                aw_home=str(eff_aw_home),
                companion_dir=np_data.get("companion_dir"),
                enabled_hosts=np_data.get("enabled_hosts"),
                non_secret_consent=np_data.get("non_secret_consent"),
            )
        else:
            pls, gps, dm, rb, ds = get_preset_defaults(plan.to_preset)
            new_policy = ProjectPolicy(
                preset=plan.to_preset,
                role="target",
                delivery_mode=dm,
                records_backend=rb,
                durability_state=ds,
                aw_home=str(eff_aw_home),
            )

        if mode == "records":
            return _run_records_transaction(
                repo,
                eff_aw_home,
                control_dir,
                journal,
                plan,
                new_policy,
                fault_injection=None,
            )
        else:
            return _run_transaction(
                repo,
                eff_aw_home,
                control_dir,
                journal,
                plan,
                new_policy,
                fault_injection=None,
            )

    finally:
        _cleanup_lock(lock_file, lock_handle, control_dir)


def rollback_placement_switch(
    repo_path: str | Path,
    *,
    aw_home: Optional[str | Path] = None,
) -> None:
    """Roll back an in-progress placement switch before sources-removed (E-05)."""
    repo, eff_aw_home, control_dir, lock_file, project_id = _resolve_control_and_lock(
        repo_path, aw_home=aw_home
    )
    journal_file = control_dir / "journal.json"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = None

    try:
        try:
            lock_handle = platform_lock.acquire(lock_file)
        except platform_lock.LockBusy as exc:
            raise PlacementSwitchError(
                f"another placement switch is running for project {project_id}"
            ) from exc

        if not journal_file.exists():
            raise PlacementSwitchError(
                f"No placement switch transaction in progress for project {project_id}."
            )

        journal = _read_json(journal_file)
        mode = journal.get("mode", "placement")
        phase = journal.get("phase", "")
        if mode == "records":
            if phase in ("sources-removed", "done"):
                raise PlacementSwitchError(
                    "The records move is past the point of no return; finish it with resume, "
                    "then switch back with aw install --records-backend <old> --relocate."
                )
            plan = SwitchPlan.from_dict(journal["plan"])
            _perform_records_rollback(repo, eff_aw_home, control_dir, journal, plan)
        else:
            if phase in ("sources-removed", "retired", "done"):
                raise PlacementSwitchError(
                    "The switch is past the point of no return; finish it with resume, "
                    "then switch back with aw install --preset <old> --relocate."
                )

            plan = SwitchPlan.from_dict(journal["plan"])
            _perform_rollback(repo, eff_aw_home, control_dir, journal, plan)

    finally:
        _cleanup_lock(lock_file, lock_handle, control_dir)


def placement_switch_status(
    repo_path: str | Path,
    *,
    aw_home: Optional[str | Path] = None,
) -> Optional[Dict[str, Any]]:
    """Return placement switch journal status or None if no journal exists (read-only)."""
    repo, eff_aw_home, control_dir, lock_file, project_id = _resolve_control_and_lock(
        repo_path, aw_home=aw_home
    )
    journal_file = control_dir / "journal.json"
    if not journal_file.exists():
        return None
    try:
        journal = _read_json(journal_file)
    except Exception:
        return None

    plan = journal.get("plan", {})
    item_states = journal.get("item_states", {})
    staged = journal.get("staged")
    if staged is None:
        staged = {"target": journal.get("staged_paths", []), "companion": []}
    return {
        "transaction_id": journal.get("transaction_id"),
        "mode": journal.get("mode", "placement"),
        "phase": journal.get("phase"),
        "direction": plan.get("direction"),
        "from_preset": plan.get("from_preset"),
        "to_preset": plan.get("to_preset"),
        "from_config_dir": plan.get("from_config_dir"),
        "to_config_dir": plan.get("to_config_dir"),
        "items_total": len(plan.get("items", [])),
        "items_copied": sum(
            1 for s in item_states.values() if s.get("copied") or s.get("preexisting")
        ),
        "items_removed": sum(1 for s in item_states.values() if s.get("removed")),
        "staged_paths": journal.get("staged_paths", []),
        "created_directories": journal.get("created_directories", []),
        "created_aw_gitignore": journal.get("created_aw_gitignore", False),
        "companion_dir": plan.get("companion_dir"),
        "companion_action": plan.get("companion_action"),
        "staged": staged,
        "created_companion": journal.get("created_companion", False),
        "created_companion_gitignore": journal.get(
            "created_companion_gitignore", False
        ),
    }


def render_plan(plan: SwitchPlan, term: Optional[Any] = None) -> str:
    """Render human-readable placement switch plan preview (spec Section 8 & E-06)."""
    lines: list[str] = []
    lines.append(f"Placement switch plan for {plan.repo}:")
    lines.append(f"  Direction:   {plan.direction or 'none'}")
    lines.append(f"  From:        {plan.from_preset} ({plan.from_config_dir})")
    lines.append(f"  To:          {plan.to_preset} ({plan.to_config_dir})")
    if plan.direction in ("records-to-home", "records-to-target"):
        lines.append("  Retire side: records only")
    else:
        lines.append(f"  Retire side: {plan.retire_side or 'none'}")

    # Count tracked target files that will be staged as removed
    tracked_removals = 0
    if plan.retire_side == "target" and plan.repo.exists():
        res = _run_git_read_only(plan.repo, ["ls-files", "-z", "--", ".aw"])
        if res.returncode == 0 and res.stdout:
            tracked_removals = len([e for e in res.stdout.split("\x00") if e])
        else:
            tracked_removals = sum(
                1
                for it in plan.items
                if it.tracked
                and (
                    plan.repo in it.source.resolve().parents
                    or it.source.resolve() == plan.repo.resolve()
                )
            )
    elif plan.direction == "records-to-home":
        tracked_removals = sum(
            1
            for it in plan.items
            if it.tracked
            and (
                plan.repo in it.source.resolve().parents
                or it.source.resolve() == plan.repo.resolve()
            )
        )
    lines.append(
        f"  Tracked target files that will be staged as removed: {tracked_removals}"
    )

    if plan.companion_action is not None:
        lines.append(f"  Companion directory: {plan.companion_dir}")
        lines.append(f"  Companion action:    {plan.companion_action}")
        if plan.companion_action == "attach" and plan.companion_dir is not None:
            comp_rec = plan.companion_dir / "records"
            if comp_rec.is_dir():
                lines.append(
                    "  Companion records:   already contains records (will merge)"
                )
            else:
                lines.append(
                    "  Companion records:   created (records/ will be created)"
                )
        if plan.companion_create:
            lines.append("  Companion repository will be created and git-initialized")
        if plan.config_retrack == "untrack":
            lines.append("  project.json will be untracked in the target")
        elif plan.config_retrack == "track":
            lines.append("  project.json will be tracked again")

        # Count staged items per repository
        target_staged = 0
        if plan.retire_side == "target":
            target_staged += tracked_removals
        else:
            target_staged += sum(
                1
                for it in plan.items
                if it.source_git == "target"
                and it.tracked
                and it.kind in ("move", "discard")
            )
        target_staged += sum(
            1 for it in plan.items if it.dest_git == "target" and it.kind == "move"
        )
        if plan.config_retrack in ("untrack", "track"):
            target_staged += 1

        companion_staged = sum(
            1 for it in plan.items if it.dest_git == "companion" and it.kind == "move"
        ) + sum(
            1
            for it in plan.items
            if it.source_git == "companion"
            and it.tracked
            and it.kind in ("move", "discard")
        )
        lines.append(
            f"  Staged counts per repository: target: {target_staged} staged, companion: {companion_staged} staged"
        )

    # Per-class counts of move / discard / rewrite items
    class_order = [
        "config_project",
        "config_local",
        "records",
        "state_durable",
        "state_runtime",
    ]
    seen_classes = set(class_order)
    extra_classes = sorted(
        {it.item_class for it in plan.items if it.item_class not in seen_classes}
    )
    all_classes = class_order + extra_classes

    class_ops: dict[str, dict[str, int]] = {
        cls_name: {"move": 0, "discard": 0, "rewrite": 0} for cls_name in all_classes
    }
    for it in plan.items:
        if it.item_class in class_ops and it.kind in class_ops[it.item_class]:
            class_ops[it.item_class][it.kind] += 1
        elif it.item_class in class_ops:
            class_ops[it.item_class][it.kind] = (
                class_ops[it.item_class].get(it.kind, 0) + 1
            )

    lines.append("")
    lines.append("Operations by class:")
    for cls_name in all_classes:
        counts = class_ops[cls_name]
        parts = [f"{count} {op}" for op, count in counts.items() if count > 0]
        if parts:
            lines.append(f"  - {cls_name}: {', '.join(parts)}")
        else:
            lines.append(f"  - {cls_name}: 0 operations")

    # The first 20 paths per kind with a "and <n> more" line
    for kind in ("move", "rewrite", "discard"):
        items_of_kind = [it for it in plan.items if it.kind == kind]
        if items_of_kind:
            lines.append("")
            lines.append(
                f"Planned operations [{kind.upper()}] ({len(items_of_kind)} items):"
            )
            for it in items_of_kind[:20]:
                if it.destination is not None and it.destination != it.source:
                    lines.append(f"  [{kind.upper()}] {it.source} -> {it.destination}")
                else:
                    lines.append(f"  [{kind.upper()}] {it.source}")
            if len(items_of_kind) > 20:
                lines.append(f"  ... and {len(items_of_kind) - 20} more")

    # Blockers
    if plan.blockers:
        lines.append("")
        lines.append(f"Blockers ({len(plan.blockers)}):")
        for b in plan.blockers:
            msg = plan.blocker_messages.get(b, getattr(b, "message", ""))
            lines.append(f"  [BLOCKER] {b}: {msg}")

    # Warnings
    if plan.warnings:
        lines.append("")
        lines.append(f"Warnings ({len(plan.warnings)}):")
        for w_name, w_count in sorted(plan.warnings.items()):
            desc = ""
            if w_name == "records-leave-target-history":
                desc = f": {w_count} tracked records remain in target git history; the switch cannot rewrite history"
            elif w_name == "companion-left-in-place":
                desc = ": the companion repository is left on disk without deleting companion data"
            elif w_name == "config-becomes-untracked":
                desc = ": project.json becomes untracked in the target"
            elif w_name == "records-become-tracked-candidates":
                desc = f": {w_count} records moved to target become tracked candidates"
            else:
                desc = f": {w_count}"
            lines.append(f"  [WARNING] {w_name}{desc}")

    return "\n".join(lines)
