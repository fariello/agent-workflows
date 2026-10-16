"""Pure placement-switch planner with blockers and per-item moves (IPD xvlemm / Set cfgreloc).

Computes a deterministic SwitchPlan that specifies all file movements, discards,
and rewrites required to switch configuration placement between target and home,
with zero side effects (pure read-only inspection).
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from agent_workflows.install_wizard import (
    ProjectPolicy,
    config_placement_switch,
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
from agent_workflows.project_schema import Preset


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
    direction: str  # "to-home", "to-target", or ""
    items: List[SwitchItem] = field(default_factory=list)
    retire_side: Optional[str] = None  # "target", "home", or None
    blockers: List[str] = field(default_factory=list)
    warnings: Dict[str, int] = field(default_factory=dict)
    blocker_messages: Dict[str, str] = field(default_factory=dict)

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

        # Companion pair refusal check (short-circuit)
        if (
            from_preset == Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value
            or to_preset == Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value
        ):
            return SwitchPlan(
                repo=repo,
                project_id=derived_project_id,
                from_preset=from_preset,
                to_preset=to_preset,
                from_config_dir=from_config_dir,
                to_config_dir=switch.target_dir,
                direction="",
                items=[],
                retire_side=None,
                blockers=[
                    SwitchBlocker(
                        "companion-unsupported",
                        "Companion layout is unsupported (backlog n9vd2h).",
                    )
                ],
                blocker_messages={
                    "companion-unsupported": "Companion layout is unsupported (backlog n9vd2h)."
                },
                warnings={},
            )

        # Resolve OLD side project context
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
            retire_side = "target"
        elif not is_from_in_target and is_to_in_target:
            direction = "to-target"
            retire_side = "home"
        else:
            direction = ""
            retire_side = None

        # Build items
        tracked_files = _get_tracked_files(repo)

        def is_tracked(file_path: Path) -> bool:
            try:
                resolved_f = file_path.resolve()
                if repo in resolved_f.parents or resolved_f == repo.resolve():
                    rel = resolved_f.relative_to(repo.resolve()).as_posix()
                    return rel in tracked_files
            except OSError:
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
        records_items: List[SwitchItem] = []
        if old_records_root.exists():
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
                                tracked=is_tracked(dp),
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
                                tracked=is_tracked(fp),
                                sha256=r_sha,
                                size=r_size,
                                mode=r_mode,
                            )
                        )
                    else:
                        dest = new_records_root / rel_p
                        records_items.append(
                            SwitchItem(
                                item_class="records",
                                source=fp,
                                destination=dest,
                                kind="move",
                                tracked=is_tracked(fp),
                                sha256=r_sha,
                                size=r_size,
                                mode=r_mode,
                            )
                        )
        items.extend(records_items)

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

        # Blockers detection
        blockers: List[SwitchBlocker] = []
        blocker_messages: Dict[str, str] = {}

        def add_blocker(bid: str, msg: str) -> None:
            if bid not in blocker_messages:
                blockers.append(SwitchBlocker(bid, msg))
                blocker_messages[bid] = msg

        # Blocker: dirty-aw-tree
        res_aw = _run_git_read_only(repo, ["status", "--porcelain", "--", ".aw"])
        if res_aw.returncode == 0 and res_aw.stdout.strip():
            add_blocker(
                "dirty-aw-tree",
                "Working tree under .aw is dirty (uncommitted changes or untracked non-ignored files).",
            )

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
            blockers=blockers,
            warnings=warnings,
            blocker_messages=blocker_messages,
        )
    finally:
        if prev_env_aw_home is not None:
            os.environ["AW_HOME"] = prev_env_aw_home
        else:
            os.environ.pop("AW_HOME", None)
