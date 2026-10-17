"""Pure policy collection, wizard state machine, presets, and pre-write preview (IPD 20260810-awphysical-03).

This module implements the pure wizard state machine, four approved presets,
custom placement validation, exact pre-write plan preview, update checkpoints,
and atomic policy persistence specified by
``.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md``.

Invariants:
- SEPARATION: Choice logic and policy validation are separate from terminal rendering.
- PRESET CONTRACTS: Four approved presets (private-target, public-private-companion,
  clean-target, local-only) plus advanced custom selection.
- INVARIANT ENFORCEMENT: Rejects clean-delta + repository records, tracked local/runtime config,
  and companion system roots before any write.
- AUTOMATION SAFETY: Noninteractive first install with incomplete choices or --yes alone
  FAILS CLOSED before writes, identifying missing required policy choices.
- PRE-WRITE PREVIEW: One exact plan rendering showing all physical paths, Git owners,
  and deltas before confirmation.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union

from agent_workflows.project_schema import (
    DELIVERY_MODES,
    PRESETS,
    RECORDS_BACKENDS,
    ROOT_CLASSES,
    DeliveryMode,
    DurabilityState,
    GitPolicy,
    LocalBindingSchema,
    Placement,
    Preset,
    ProjectPolicySchema,
    ProjectRole,
    RecordsBackend,
    RootClass,
    parse_local_binding,
    parse_portable_policy,
)
from agent_workflows.term import Term


PROJECT_POLICY_RELPATH = ".aw/config/project.json"
LOCAL_BINDING_RELPATH = ".aw/config/local.json"

WIZARD_WRITTEN_PATHS = (PROJECT_POLICY_RELPATH, LOCAL_BINDING_RELPATH)

WIZARD_PATH_CLASSES: Dict[str, str] = {
    PROJECT_POLICY_RELPATH: RootClass.CONFIG_PROJECT.value,
    LOCAL_BINDING_RELPATH: RootClass.CONFIG_LOCAL.value,
}


class PolicyError(Exception):
    """Base exception for policy errors."""

    pass


class InvalidPolicyError(PolicyError):
    """Raised when policy validation rules are violated."""

    pass


class PlacementSwitch(NamedTuple):
    current_dir: Path
    target_dir: Path
    reason: str


class PlacementSwitchRequired(InvalidPolicyError):
    """Raised when an install/update would switch config placement."""

    def __init__(
        self,
        message: str,
        current_dir: Path,
        target_dir: Path,
        current_preset: Optional[str] = None,
        target_preset: Optional[str] = None,
        reason: str = "path",
    ) -> None:
        super().__init__(message)
        self.current_dir = current_dir
        self.target_dir = target_dir
        self.current_preset = current_preset
        self.target_preset = target_preset
        self.reason = reason


class RecordsRootSwitch(NamedTuple):
    current_root: Path
    target_root: Path
    record_files: int
    reason: str


class RecordsRootSwitchRequired(InvalidPolicyError):
    """Raised when an install/update would repoint the records root away from records."""

    def __init__(
        self,
        message: str,
        current_root: Path,
        target_root: Path,
        current_backend: Optional[str] = None,
        target_backend: Optional[str] = None,
        record_files: int = 0,
        reason: str = "records",
    ) -> None:
        super().__init__(message)
        self.current_root = current_root
        self.target_root = target_root
        self.current_backend = current_backend
        self.target_backend = target_backend
        self.record_files = record_files
        self.reason = reason


class IncompletePolicyError(PolicyError):
    """Raised when noninteractive execution is missing required policy choices."""

    pass


class PolicyCancelledError(PolicyError):
    """Raised when user cancels policy wizard confirmation."""

    pass


# Map preset aliases to canonical preset string values
_PRESET_ALIASES: Dict[str, str] = {
    "private-target": Preset.PRIVATE_TARGET.value,
    "public-private-companion": Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value,
    "public-companion": Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value,
    "public-target-private-companion": Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value,
    "clean-target": Preset.COMPLETELY_CLEAN_TARGET.value,
    "completely-clean-target": Preset.COMPLETELY_CLEAN_TARGET.value,
    "local-only": Preset.LOCAL_ONLY.value,
    "custom": "custom",
}


def normalize_preset(preset_str: str) -> str:
    """Normalize a preset name or alias to canonical Preset enum string."""
    key = preset_str.strip().lower()
    if key in _PRESET_ALIASES:
        return _PRESET_ALIASES[key]
    if preset_str in PRESETS or preset_str == "custom":
        return preset_str
    raise InvalidPolicyError(
        f"Unknown preset: '{preset_str}'. Must be one of {PRESETS} or 'custom'."
    )


def get_preset_defaults(
    preset_str: str,
) -> Tuple[Dict[str, str], Dict[str, str], str, str, str]:
    """Get (placements, git_policies, delivery_mode, records_backend, durability_state) for a preset."""
    canonical_preset = normalize_preset(preset_str)

    if canonical_preset == Preset.PRIVATE_TARGET.value:
        placements = {
            RootClass.SYSTEM.value: Placement.TARGET_TRACKED.value,
            RootClass.CONFIG_PROJECT.value: Placement.TARGET_TRACKED.value,
            RootClass.CONFIG_LOCAL.value: Placement.TARGET_IGNORED.value,
            # .aw/.gitignore ignores /state/ (engine._AW_GITIGNORE_TEMPLATE, D92 leak containment)
            RootClass.STATE_DURABLE.value: Placement.TARGET_IGNORED.value,
            RootClass.STATE_RUNTIME.value: Placement.TARGET_IGNORED.value,
            RootClass.RECORDS.value: Placement.TARGET_TRACKED.value,
        }
        git_policies = {
            RootClass.SYSTEM.value: GitPolicy.TARGET_GIT.value,
            RootClass.CONFIG_PROJECT.value: GitPolicy.TARGET_GIT.value,
            RootClass.CONFIG_LOCAL.value: GitPolicy.IGNORED.value,
            # .aw/.gitignore ignores /state/ (engine._AW_GITIGNORE_TEMPLATE, D92 leak containment)
            RootClass.STATE_DURABLE.value: GitPolicy.IGNORED.value,
            RootClass.STATE_RUNTIME.value: GitPolicy.IGNORED.value,
            RootClass.RECORDS.value: GitPolicy.TARGET_GIT.value,
        }
        return (
            placements,
            git_policies,
            DeliveryMode.TRACKED.value,
            RecordsBackend.REPOSITORY.value,
            DurabilityState.LOCAL_GIT.value,
        )

    elif canonical_preset == Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value:
        placements = {
            RootClass.SYSTEM.value: Placement.TARGET_TRACKED.value,
            RootClass.CONFIG_PROJECT.value: Placement.COMPANION_TRACKED.value,
            RootClass.CONFIG_LOCAL.value: Placement.HOME_UNTRACKED.value,
            RootClass.STATE_DURABLE.value: Placement.COMPANION_TRACKED.value,
            RootClass.STATE_RUNTIME.value: Placement.HOME_UNTRACKED.value,
            RootClass.RECORDS.value: Placement.COMPANION_TRACKED.value,
        }
        git_policies = {
            RootClass.SYSTEM.value: GitPolicy.TARGET_GIT.value,
            RootClass.CONFIG_PROJECT.value: GitPolicy.COMPANION_GIT.value,
            RootClass.CONFIG_LOCAL.value: GitPolicy.UNTRACKED.value,
            RootClass.STATE_DURABLE.value: GitPolicy.COMPANION_GIT.value,
            RootClass.STATE_RUNTIME.value: GitPolicy.UNTRACKED.value,
            RootClass.RECORDS.value: GitPolicy.COMPANION_GIT.value,
        }
        return (
            placements,
            git_policies,
            DeliveryMode.TRACKED.value,
            RecordsBackend.COMPANION.value,
            DurabilityState.LOCAL_GIT.value,
        )

    elif canonical_preset == Preset.COMPLETELY_CLEAN_TARGET.value:
        placements = {
            RootClass.SYSTEM.value: Placement.HOME_UNTRACKED.value,
            RootClass.CONFIG_PROJECT.value: Placement.HOME_UNTRACKED.value,
            RootClass.CONFIG_LOCAL.value: Placement.HOME_UNTRACKED.value,
            RootClass.STATE_DURABLE.value: Placement.HOME_UNTRACKED.value,
            RootClass.STATE_RUNTIME.value: Placement.HOME_UNTRACKED.value,
            RootClass.RECORDS.value: Placement.HOME_UNTRACKED.value,
        }
        git_policies = {
            RootClass.SYSTEM.value: GitPolicy.UNTRACKED.value,
            RootClass.CONFIG_PROJECT.value: GitPolicy.UNTRACKED.value,
            RootClass.CONFIG_LOCAL.value: GitPolicy.UNTRACKED.value,
            RootClass.STATE_DURABLE.value: GitPolicy.UNTRACKED.value,
            RootClass.STATE_RUNTIME.value: GitPolicy.UNTRACKED.value,
            RootClass.RECORDS.value: GitPolicy.UNTRACKED.value,
        }
        return (
            placements,
            git_policies,
            DeliveryMode.CLEAN_DELTA.value,
            RecordsBackend.HOME.value,
            DurabilityState.UNVERSIONED.value,
        )

    elif canonical_preset == Preset.LOCAL_ONLY.value:
        placements = {
            RootClass.SYSTEM.value: Placement.HOME_UNTRACKED.value,
            RootClass.CONFIG_PROJECT.value: Placement.HOME_UNTRACKED.value,
            RootClass.CONFIG_LOCAL.value: Placement.HOME_UNTRACKED.value,
            RootClass.STATE_DURABLE.value: Placement.HOME_UNTRACKED.value,
            RootClass.STATE_RUNTIME.value: Placement.HOME_UNTRACKED.value,
            RootClass.RECORDS.value: Placement.HOME_UNTRACKED.value,
        }
        git_policies = {
            RootClass.SYSTEM.value: GitPolicy.UNTRACKED.value,
            RootClass.CONFIG_PROJECT.value: GitPolicy.UNTRACKED.value,
            RootClass.CONFIG_LOCAL.value: GitPolicy.UNTRACKED.value,
            RootClass.STATE_DURABLE.value: GitPolicy.UNTRACKED.value,
            RootClass.STATE_RUNTIME.value: GitPolicy.UNTRACKED.value,
            RootClass.RECORDS.value: GitPolicy.UNTRACKED.value,
        }
        return (
            placements,
            git_policies,
            DeliveryMode.CLEAN_DELTA.value,
            RecordsBackend.HOME.value,
            DurabilityState.UNVERSIONED.value,
        )

    else:
        # Default fallback for custom
        placements = {
            RootClass.SYSTEM.value: Placement.TARGET_TRACKED.value,
            RootClass.CONFIG_PROJECT.value: Placement.TARGET_TRACKED.value,
            RootClass.CONFIG_LOCAL.value: Placement.TARGET_IGNORED.value,
            # .aw/.gitignore ignores /state/ (engine._AW_GITIGNORE_TEMPLATE, D92 leak containment)
            RootClass.STATE_DURABLE.value: Placement.TARGET_IGNORED.value,
            RootClass.STATE_RUNTIME.value: Placement.TARGET_IGNORED.value,
            RootClass.RECORDS.value: Placement.TARGET_TRACKED.value,
        }
        git_policies = {
            RootClass.SYSTEM.value: GitPolicy.TARGET_GIT.value,
            RootClass.CONFIG_PROJECT.value: GitPolicy.TARGET_GIT.value,
            RootClass.CONFIG_LOCAL.value: GitPolicy.IGNORED.value,
            # .aw/.gitignore ignores /state/ (engine._AW_GITIGNORE_TEMPLATE, D92 leak containment)
            RootClass.STATE_DURABLE.value: GitPolicy.IGNORED.value,
            RootClass.STATE_RUNTIME.value: GitPolicy.IGNORED.value,
            RootClass.RECORDS.value: GitPolicy.TARGET_GIT.value,
        }
        return (
            placements,
            git_policies,
            DeliveryMode.TRACKED.value,
            RecordsBackend.REPOSITORY.value,
            DurabilityState.LOCAL_GIT.value,
        )


@dataclass(frozen=True)
class ProjectPolicy:
    """Immutable project layout and storage policy (spec Section 5 & 6)."""

    preset: str = Preset.PRIVATE_TARGET.value
    role: str = ProjectRole.TARGET.value
    delivery_mode: str = DeliveryMode.TRACKED.value
    records_backend: str = RecordsBackend.REPOSITORY.value
    durability_state: str = DurabilityState.UNVERSIONED.value
    aw_home: Optional[str] = None
    companion_dir: Optional[str] = None
    enabled_hosts: List[str] = field(
        default_factory=lambda: ["opencode", "claude", "antigravity"]
    )
    placements: Dict[str, str] = field(default_factory=dict)
    git_policies: Dict[str, str] = field(default_factory=dict)
    non_secret_consent: Dict[str, bool] = field(default_factory=dict)
    target_visibility: str = "private"
    migration_required: bool = False
    create_companion: bool = False
    init_companion_git: bool = False

    def __post_init__(self):
        # Fill defaults if placements or git_policies are empty
        if not self.placements or not self.git_policies:
            pls, gps, dm, rb, ds = get_preset_defaults(self.preset)
            if not self.placements:
                object.__setattr__(self, "placements", pls)
            if not self.git_policies:
                object.__setattr__(self, "git_policies", gps)

        if self.records_backend == RecordsBackend.REPOSITORY_UNTRACKED.value:
            new_pls = dict(self.placements)
            new_pls[RootClass.RECORDS.value] = Placement.TARGET_IGNORED.value
            object.__setattr__(self, "placements", new_pls)

            new_gps = dict(self.git_policies)
            new_gps[RootClass.RECORDS.value] = GitPolicy.IGNORED.value
            object.__setattr__(self, "git_policies", new_gps)

    def validate(self, repo_path: Optional[Union[str, Path]] = None) -> None:
        """Validate policy rules before rendering or writes (spec Section 5 & 6)."""
        norm_preset = normalize_preset(self.preset)
        if norm_preset not in PRESETS and norm_preset != "custom":
            raise InvalidPolicyError(f"Invalid preset: '{self.preset}'.")

        if self.delivery_mode not in DELIVERY_MODES:
            raise InvalidPolicyError(
                f"Invalid delivery_mode: '{self.delivery_mode}'. Must be one of {DELIVERY_MODES}."
            )

        if self.records_backend not in RECORDS_BACKENDS:
            raise InvalidPolicyError(
                f"Invalid records_backend: '{self.records_backend}'. Must be one of {RECORDS_BACKENDS}."
            )

        # Invariant: clean-delta delivery mode MUST NOT use repository or repository-untracked records backend
        if (
            self.delivery_mode == DeliveryMode.CLEAN_DELTA.value
            and self.records_backend
            in (
                RecordsBackend.REPOSITORY.value,
                RecordsBackend.REPOSITORY_UNTRACKED.value,
            )
        ):
            raise InvalidPolicyError(
                f"Forbidden policy combination: '{DeliveryMode.CLEAN_DELTA.value}' delivery mode "
                f"MUST NOT use '{self.records_backend}' records backend."
            )

        # Refusal: repository-untracked backend on a repo that already tracks records
        if (
            self.records_backend == RecordsBackend.REPOSITORY_UNTRACKED.value
            and repo_path
        ):
            p_repo = Path(repo_path)
            if (p_repo / ".git").exists() or (p_repo / ".git").is_file():
                try:
                    res = subprocess.run(
                        ["git", "-C", str(p_repo), "ls-files", ".aw/records"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    tracked = [
                        line.strip() for line in res.stdout.splitlines() if line.strip()
                    ]
                    if tracked:
                        raise InvalidPolicyError(
                            f"Cannot use '{RecordsBackend.REPOSITORY_UNTRACKED.value}' backend on repository '{p_repo}': "
                            f"it already tracks records in Git ({tracked[0]}). "
                            f"Git ignore rules do not untrack already-tracked files. "
                            f"Use 'aw migrate' or untrack existing records before selecting this backend."
                        )
                except InvalidPolicyError:
                    raise
                except Exception:
                    pass

        # Invariant: config_local and state_runtime MUST NOT be tracked in Git
        for cls in (RootClass.CONFIG_LOCAL.value, RootClass.STATE_RUNTIME.value):
            gp = self.git_policies.get(cls)
            if gp in (GitPolicy.TARGET_GIT.value, GitPolicy.COMPANION_GIT.value):
                raise InvalidPolicyError(
                    f"Forbidden Git policy for {cls}: MUST NOT be tracked ({gp})."
                )

        # Invariant: system root MUST NOT be placed in companion repository
        sys_placement = self.placements.get(RootClass.SYSTEM.value, "")
        if sys_placement.startswith("companion"):
            raise InvalidPolicyError(
                f"Forbidden system placement '{sys_placement}': system root MUST NOT be placed in companion repository."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 2,
            "preset": self.preset,
            "role": self.role,
            "delivery_mode": self.delivery_mode,
            "records_backend": self.records_backend,
            "durability_state": self.durability_state,
            "aw_home": self.aw_home,
            "companion_dir": self.companion_dir,
            "enabled_hosts": list(self.enabled_hosts),
            "placements": dict(self.placements),
            "git_policies": dict(self.git_policies),
            "non_secret_consent": dict(self.non_secret_consent),
            "target_visibility": self.target_visibility,
            "migration_required": self.migration_required,
        }


def format_policy_summary(policy: ProjectPolicy) -> str:
    """Format plain-text linear policy summary without ANSI codes."""
    lines = [
        "Project Policy Summary:",
        f"  Preset:           {policy.preset}",
        f"  Delivery Mode:    {policy.delivery_mode}",
        f"  Records Backend:  {policy.records_backend}",
        f"  Durability State: {policy.durability_state}",
        f"  AW_HOME:          {policy.aw_home or 'platform default (~/.aw)'}",
        f"  Companion Dir:    {policy.companion_dir or 'none'}",
        f"  Enabled Hosts:    {', '.join(policy.enabled_hosts)}",
    ]
    return "\n".join(lines)


def render_pre_write_plan(
    policy: ProjectPolicy, repo_path: str, term: Optional[Term] = None
) -> str:
    """Render exact pre-write plan preview showing resolved paths, Git policies, and deltas (E-04)."""
    from agent_workflows.project_context import resolve_project_context

    term = term or Term(color=False)
    home_dir = str(Path.home())

    def _format_path(p: str) -> str:
        if p.startswith(home_dir):
            return "~" + p[len(home_dir) :]
        return p

    repo_formatted = _format_path(repo_path)

    resolver_error: Optional[str] = None
    resolved_roots: Dict[str, str] = {}
    try:
        ctx = resolve_project_context(
            target_repo=repo_path,
            aw_home=policy.aw_home,
            delivery_mode=policy.delivery_mode,
            records_backend=policy.records_backend,
            preset=policy.preset,
            role=policy.role,
            companion_dir=policy.companion_dir,
        )
        if ctx.physical_classes:
            for cls_name, raw_p in ctx.physical_classes.items():
                fmt = _format_path(str(raw_p))
                if cls_name not in (
                    RootClass.CONFIG_PROJECT.value,
                    RootClass.CONFIG_LOCAL.value,
                ):
                    if not fmt.endswith("/"):
                        fmt += "/"
                resolved_roots[cls_name] = fmt
    except Exception as exc:
        resolver_error = str(exc)
        resolved_roots = {}

    lines = []
    lines.append(term.colorize("AW Pre-Write Physical Layout & Consent Plan", "bold"))
    lines.append(f"  Target Repository: {repo_formatted}")
    lines.append(f"  Preset:            {policy.preset}")
    lines.append(f"  Role:              {policy.role}")
    lines.append(f"  Target Visibility: {policy.target_visibility}")
    lines.append("")
    lines.append(term.colorize("Resolved Physical Classes & Git Policies:", "bold"))

    for cls in ROOT_CLASSES:
        if resolver_error:
            path_str = f"unresolved ({resolver_error})"
        else:
            path_str = resolved_roots.get(cls, "unresolved")
        placement = policy.placements.get(cls, "unknown")
        git_pol = policy.git_policies.get(cls, "untracked")
        owner = (
            "target"
            if "target" in placement
            else ("companion" if "companion" in placement else "home")
        )
        lines.append(f"  - {cls:<15}: {path_str:<45} [{owner}] ({git_pol})")

    lines.append("")
    lines.append(term.colorize("Host Adapter Exceptions:", "bold"))
    if policy.delivery_mode == DeliveryMode.CLEAN_DELTA.value:
        lines.append(
            "  - None in target repository (clean-delta writes no target host adapters)."
        )
    else:
        lines.append(
            f"  - AGENTS.md:       {repo_formatted}/AGENTS.md (adapter pointer)"
        )
        lines.append(
            f"  - .claude/:        {repo_formatted}/.claude/ (discovery adapter)"
        )
        lines.append(
            f"  - .opencode/:      {repo_formatted}/.opencode/ (discovery adapter)"
        )

    lines.append("")
    lines.append(term.colorize("Expected Deltas:", "bold"))
    if policy.delivery_mode == DeliveryMode.CLEAN_DELTA.value:
        lines.append(
            "  Target Delta:     ZERO AW-owned target files created (clean-target)."
        )
    else:
        lines.append(
            "  Target Delta:     .aw/system/, .aw/config/project.json (tracked); .aw/config/local.json, .aw/state/ (written-but-ignored) created/updated."
        )

    if policy.records_backend == RecordsBackend.COMPANION.value:
        comp_path = _format_path(policy.companion_dir or f"{repo_path}.aw")
        lines.append(
            f"  Companion Delta:  {comp_path}/.aw/records and config created/updated."
        )
    else:
        lines.append("  Companion Delta:  None.")

    lines.append("")
    lines.append(term.colorize("Durability & Warnings:", "bold"))
    lines.append(f"  Durability:       {policy.durability_state}")
    if policy.records_backend == RecordsBackend.REPOSITORY_UNTRACKED.value:
        lines.append(
            term.colorize(
                "  [WARNING] Records are git-ignored in this working tree (repository-untracked); they are not durable across clones and are lost if this checkout is deleted.",
                "yellow",
            )
        )
    elif policy.durability_state == DurabilityState.UNVERSIONED.value:
        lines.append(
            term.colorize(
                "  [WARNING] Storage is unversioned; changes are local and not backed up.",
                "yellow",
            )
        )
    if (
        policy.target_visibility == "public"
        and policy.records_backend == RecordsBackend.REPOSITORY.value
    ):
        lines.append(
            term.colorize(
                "  [WARNING] Target is public and records are repository-tracked; private notes may leak if committed.",
                "yellow",
            )
        )

    return "\n".join(lines)


def resolve_existing_policy(repo_path: str) -> Optional[ProjectPolicy]:
    """Attempt to load existing policy from repository context (spec Section 11.2)."""
    p_repo = Path(repo_path)
    from agent_workflows.project_context import project_config_dir

    cfg_dir = project_config_dir(p_repo)
    proj_json = cfg_dir / "project.json"
    local_json = cfg_dir / "local.json"
    legacy_json = cfg_dir / "config.json"
    agents_dir = p_repo / ".agents"

    if not (
        proj_json.exists()
        or local_json.exists()
        or legacy_json.exists()
        or agents_dir.exists()
    ):
        return None

    try:
        from agent_workflows.project_context import resolve_project_context

        ctx = resolve_project_context(target_repo=repo_path)

        comp_dir = None
        if local_json.exists():
            try:
                with open(local_json, "r", encoding="utf-8") as f:
                    ldata = json.load(f)
                if isinstance(ldata, dict):
                    comp_dir = ldata.get("companion_dir")
            except Exception:
                pass

        consent: Dict[str, bool] = {}
        if proj_json.exists():
            try:
                with open(proj_json, "r", encoding="utf-8") as f:
                    pdata = json.load(f)
                if isinstance(pdata, dict) and isinstance(
                    pdata.get("non_secret_consent"), dict
                ):
                    consent = dict(pdata["non_secret_consent"])
            except Exception:
                pass

        return ProjectPolicy(
            preset=getattr(ctx, "preset", Preset.PRIVATE_TARGET.value),
            role=getattr(ctx, "project_role", ProjectRole.TARGET.value),
            delivery_mode=ctx.delivery_mode,
            records_backend=ctx.records_backend,
            durability_state=ctx.durability_state,
            aw_home=str(ctx.effective_aw_home),
            companion_dir=comp_dir,
            enabled_hosts=list(
                getattr(ctx, "enabled_hosts", ["opencode", "claude", "antigravity"])
            ),
            non_secret_consent=consent,
        )
    except Exception:
        return None


def config_placement_switch(
    repo_path: str | Path,
    policy: ProjectPolicy,
    existing_policy: Optional[ProjectPolicy] = None,
) -> Optional[PlacementSwitch]:
    """Pure detector that checks if policy would switch config placement.

    Returns PlacementSwitch(current_dir, target_dir, reason) if a switch is required,
    or None if the write is to the authoritative config directory.
    """
    from agent_workflows.project_context import (
        project_config_dir,
        resolve_project_context,
    )

    current_dir = Path(project_config_dir(repo_path, aw_home=policy.aw_home))

    ctx = resolve_project_context(
        target_repo=str(repo_path),
        aw_home=policy.aw_home,
        delivery_mode=policy.delivery_mode,
        records_backend=policy.records_backend,
        preset=policy.preset,
        role=policy.role,
        companion_dir=policy.companion_dir,
    )
    target_dir = Path(ctx.physical_classes["config_project"]).parent

    # (a) path-based check: any config candidate exists in current_dir and target_dir differs
    has_existing_cfg = any(
        (current_dir / candidate).exists()
        for candidate in ("project.json", "local.json", "config.json", "policy.json")
    )
    if has_existing_cfg and current_dir.resolve() != target_dir.resolve():
        return PlacementSwitch(
            current_dir=current_dir,
            target_dir=target_dir,
            reason="path",
        )

    # (b) label-based check: when existing_policy is passed, check preset defaults
    if existing_policy is not None:
        existing_defaults = get_preset_defaults(existing_policy.preset)
        existing_cfg_placement = existing_policy.placements.get(
            RootClass.CONFIG_PROJECT.value
        ) or existing_defaults[0].get(RootClass.CONFIG_PROJECT.value)
        new_defaults = get_preset_defaults(policy.preset)
        new_cfg_placement = new_defaults[0].get(RootClass.CONFIG_PROJECT.value)
        if new_cfg_placement != existing_cfg_placement:
            return PlacementSwitch(
                current_dir=current_dir,
                target_dir=target_dir,
                reason="label",
            )

    return None


# Files the installer scaffolds (.gitkeep, README.md) or that `aw index` /
# `aw ipd board --write-index` regenerate (INDEX.json, INDEX.md, STATUS.md).
# They carry no record content, so leaving them behind orphans nothing.
_RECORDS_SCAFFOLD_NAMES = frozenset(
    (".gitkeep", "README.md", "INDEX.json", "INDEX.md", "STATUS.md")
)


def _count_record_files(root: Path) -> int:
    if not root.is_dir():
        return 0
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath)
        # os.walk does not descend symlinked dirs; count them as one entry.
        for d in dirnames:
            if (base / d).is_symlink():
                count += 1
        for name in filenames:
            if name in _RECORDS_SCAFFOLD_NAMES:
                continue
            p = base / name
            if p.is_symlink() or p.is_file():
                count += 1
    return count


def records_root_switch(
    repo_path: str | Path,
    policy: ProjectPolicy,
    existing_policy: Optional[ProjectPolicy] = None,
) -> Optional[RecordsRootSwitch]:
    """Pure detector (no writes) for a records-root switch that would orphan records.

    Returns RecordsRootSwitch(current_root, target_root, record_files, reason) when the
    repository is installed, no full config placement switch applies, the records root
    resolved by `policy` differs from the current one, and the current root holds
    record-bearing files. Otherwise returns None.
    """
    from agent_workflows.project_context import (
        project_config_dir,
        resolve_project_context,
    )

    config_dir = Path(project_config_dir(repo_path, aw_home=policy.aw_home))
    if not any(
        (config_dir / candidate).exists()
        for candidate in ("project.json", "local.json", "config.json", "policy.json")
    ):
        return None

    if (
        config_placement_switch(repo_path, policy, existing_policy=existing_policy)
        is not None
    ):
        return None

    current_ctx = resolve_project_context(
        target_repo=str(repo_path), aw_home=policy.aw_home
    )
    target_ctx = resolve_project_context(
        target_repo=str(repo_path),
        aw_home=policy.aw_home,
        delivery_mode=policy.delivery_mode,
        records_backend=policy.records_backend,
        preset=policy.preset,
        role=policy.role,
        companion_dir=policy.companion_dir,
    )
    current_root = Path(current_ctx.logical_roots["records"])
    target_root = Path(target_ctx.logical_roots["records"])
    if current_root.resolve() == target_root.resolve():
        return None

    record_files = _count_record_files(current_root)
    if record_files == 0:
        return None

    companion = RecordsBackend.COMPANION.value
    if current_ctx.records_backend == companion or policy.records_backend == companion:
        reason = "companion"
    else:
        reason = "records"
    return RecordsRootSwitch(
        current_root=current_root,
        target_root=target_root,
        record_files=record_files,
        reason=reason,
    )


def raise_if_records_root_switch(
    repo_path: str | Path,
    policy: ProjectPolicy,
    existing_policy: Optional[ProjectPolicy] = None,
) -> None:
    """Raise RecordsRootSwitchRequired when `records_root_switch` reports a hit."""
    switch = records_root_switch(repo_path, policy, existing_policy=existing_policy)
    if switch is None:
        return
    from agent_workflows.project_context import resolve_project_context

    old = resolve_project_context(
        target_repo=str(repo_path), aw_home=policy.aw_home
    ).records_backend
    new = policy.records_backend
    lead = (
        f"Changing the records backend from {old} ({switch.current_root}) "
        f"to {new} ({switch.target_root}) would leave {switch.record_files} record files"
    )
    if switch.reason == "companion":
        message = (
            f"{lead} behind and involves a companion repository, "
            "which is not supported yet (backlog n9vd2h)."
        )
    else:
        message = (
            f"{lead} in {switch.current_root} where no reader looks. "
            "Moving records between backends is not supported by reinstall yet (backlog wbz75c)."
        )
    raise RecordsRootSwitchRequired(
        message,
        current_root=switch.current_root,
        target_root=switch.target_root,
        current_backend=old,
        target_backend=new,
        record_files=switch.record_files,
        reason=switch.reason,
    )


def resolve_policy_noninteractive(
    repo_path: str,
    existing_policy: Optional[ProjectPolicy] = None,
    explicit_preset: Optional[str] = None,
    explicit_delivery: Optional[str] = None,
    explicit_backend: Optional[str] = None,
    explicit_companion: Optional[str] = None,
    explicit_aw_home: Optional[str] = None,
    explicit_hosts: Optional[List[str]] = None,
    assume_yes: bool = False,
) -> ProjectPolicy:
    """Resolve policy for noninteractive execution (spec Section 11.3 & E-05)."""
    if existing_policy is not None:
        normalized_explicit = (
            normalize_preset(explicit_preset) if explicit_preset else None
        )
        preset = normalized_explicit or existing_policy.preset

        new_defaults = get_preset_defaults(preset)

        if normalized_explicit and normalized_explicit != existing_policy.preset:
            pls, gps, dm, rb, ds = new_defaults
            delivery = explicit_delivery or dm
            backend = explicit_backend or rb
            durability = ds
            placements = pls
            git_policies = gps
        else:
            delivery = explicit_delivery or existing_policy.delivery_mode
            backend = explicit_backend or existing_policy.records_backend
            durability = existing_policy.durability_state
            placements = existing_policy.placements
            git_policies = existing_policy.git_policies

        companion = explicit_companion or existing_policy.companion_dir
        aw_home = explicit_aw_home or existing_policy.aw_home
        hosts = (
            explicit_hosts
            if explicit_hosts is not None
            else existing_policy.enabled_hosts
        )

        pol = ProjectPolicy(
            preset=preset,
            role=existing_policy.role,
            delivery_mode=delivery,
            records_backend=backend,
            durability_state=durability,
            aw_home=aw_home,
            companion_dir=companion,
            enabled_hosts=hosts,
            placements=placements,
            git_policies=git_policies,
            non_secret_consent=dict(existing_policy.non_secret_consent or {}),
        )
        pol.validate(repo_path=repo_path)

        switch = config_placement_switch(
            repo_path, pol, existing_policy=existing_policy
        )
        if switch is not None:
            raise PlacementSwitchRequired(
                f"Switching config placement from {existing_policy.preset} ({switch.current_dir}) "
                f"to {pol.preset} ({switch.target_dir}) is not supported by reinstall yet (backlog ui1aln).",
                current_dir=switch.current_dir,
                target_dir=switch.target_dir,
                current_preset=existing_policy.preset,
                target_preset=pol.preset,
                reason=switch.reason,
            )
        raise_if_records_root_switch(repo_path, pol, existing_policy=existing_policy)
        return pol

    # First install noninteractive resolution
    preset_chosen = explicit_preset or (
        Preset.COMPLETELY_CLEAN_TARGET.value
        if explicit_delivery == DeliveryMode.CLEAN_DELTA.value
        and explicit_backend == RecordsBackend.HOME.value
        else (
            Preset.PRIVATE_TARGET.value
            if explicit_delivery == DeliveryMode.TRACKED.value
            and explicit_backend == RecordsBackend.REPOSITORY.value
            else (
                Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value
                if explicit_delivery == DeliveryMode.TRACKED.value
                and explicit_backend == RecordsBackend.COMPANION.value
                else None
            )
        )
    )

    missing_fields: List[str] = []
    if not preset_chosen and not (explicit_delivery and explicit_backend):
        missing_fields.append(
            "--preset (private-target | public-private-companion | clean-target | local-only)"
        )
        if not explicit_delivery:
            missing_fields.append("--delivery-mode (tracked | clean-delta)")
        if not explicit_backend:
            missing_fields.append(
                "--records-backend (home | companion | repository | repository-untracked)"
            )

    if missing_fields:
        raise IncompletePolicyError(
            f"Noninteractive first install requires complete policy choices. "
            f"Missing required fields: {', '.join(missing_fields)}. "
            f"Pass explicit policy flags (--preset) or run interactively on a TTY."
        )

    preset_name = normalize_preset(preset_chosen or Preset.PRIVATE_TARGET.value)
    pls, gps, dm, rb, ds = get_preset_defaults(preset_name)

    delivery_final = explicit_delivery or dm
    backend_final = explicit_backend or rb

    pol = ProjectPolicy(
        preset=preset_name,
        delivery_mode=delivery_final,
        records_backend=backend_final,
        durability_state=ds,
        aw_home=explicit_aw_home,
        companion_dir=explicit_companion,
        enabled_hosts=explicit_hosts
        if explicit_hosts is not None
        else ["opencode", "claude", "antigravity"],
        placements=pls,
        git_policies=gps,
    )
    pol.validate(repo_path=repo_path)
    return pol


def collect_policy_interactive(
    term: Term,
    repo_path: str,
    existing_policy: Optional[ProjectPolicy] = None,
    assume_yes: bool = False,
    explicit_preset: Optional[str] = None,
    explicit_delivery: Optional[str] = None,
    explicit_backend: Optional[str] = None,
    explicit_companion: Optional[str] = None,
    explicit_aw_home: Optional[str] = None,
    explicit_hosts: Optional[List[str]] = None,
) -> ProjectPolicy:
    """Collect policy interactively with preset-first subflows and pre-write plan preview (E-01..E-06)."""
    if existing_policy is None:
        existing_policy = resolve_existing_policy(repo_path)

    # Check if we can run interactively (or if testing with mocked StringIO stdin)
    is_interactive = not assume_yes and (
        (hasattr(sys.stdin, "isatty") and sys.stdin.isatty())
        or isinstance(sys.stdin, io.StringIO)
    )

    if not is_interactive:
        return resolve_policy_noninteractive(
            repo_path=repo_path,
            existing_policy=existing_policy,
            explicit_preset=explicit_preset,
            explicit_delivery=explicit_delivery,
            explicit_backend=explicit_backend,
            explicit_companion=explicit_companion,
            explicit_aw_home=explicit_aw_home,
            explicit_hosts=explicit_hosts,
            assume_yes=assume_yes,
        )

    # Interactive Update Checkpoint (spec Section 11.2 & E-06)
    if existing_policy is not None:
        term.heading("AW Policy Update Checkpoint")
        term.line(f"Current Policy for {repo_path}:")
        term.line(f"  Preset:          {existing_policy.preset}")
        term.line(f"  Delivery Mode:   {existing_policy.delivery_mode}")
        term.line(f"  Records Backend: {existing_policy.records_backend}")
        term.line(
            f"  AW_HOME:         {existing_policy.aw_home or 'platform default (~/.aw)'}"
        )
        term.line()

        try:
            choice = (
                input("Keep current policy and proceed? [Y/n/review] ").strip().lower()
            )
        except EOFError:
            choice = "y"
        except KeyboardInterrupt:
            raise PolicyCancelledError("Policy update cancelled by user.")

        if choice in ("", "y", "yes"):
            return existing_policy

    # Preset-First Interview Subflow (spec Section 6 & E-02)
    term.heading("AW Installation & Policy Wizard")
    term.line("Select a preset or custom layout for this repository.")
    term.line(
        "  [1] private-target (RECOMMENDED): Target repository carries all AW files (tracked). Best for private repos."
    )
    term.line(
        "  [2] public-private-companion: Target is public; candid AW records live in a private companion repo."
    )
    term.line(
        "  [3] clean-target: Zero AW-owned files in target repo; all AW material lives in AW home or companion."
    )
    term.line("  [4] local-only: Local-only AW home storage; unversioned durability.")
    term.line(
        "  [5] custom: Advanced custom physical placement for each logical class."
    )

    try:
        preset_choice = input("Select preset [1]: ").strip()
    except EOFError:
        preset_choice = "1"
    except KeyboardInterrupt:
        raise PolicyCancelledError("Policy selection cancelled by user.")

    preset_map = {
        "1": Preset.PRIVATE_TARGET.value,
        "2": Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value,
        "3": Preset.COMPLETELY_CLEAN_TARGET.value,
        "4": Preset.LOCAL_ONLY.value,
        "5": "custom",
    }
    selected_preset = preset_map.get(preset_choice, Preset.PRIVATE_TARGET.value)

    # Target Visibility Acknowledgement Subflow (E-03, E-05)
    term.line()
    term.line("Target Repository Visibility:")
    try:
        vis_choice = (
            input(
                f"Is the {repo_path} repository public or private? [private/public] [private]: "
            )
            .strip()
            .lower()
        )
    except EOFError:
        vis_choice = "private"
    except KeyboardInterrupt:
        raise PolicyCancelledError("Repository visibility selection cancelled by user.")

    target_vis = "public" if vis_choice == "public" else "private"
    if target_vis == "public" and selected_preset == Preset.PRIVATE_TARGET.value:
        term.line()
        term.status(
            "warn",
            f"Repository '{repo_path}' is PUBLIC. Storing AW records in the target repository may expose internal notes!",
        )
        try:
            switch_comp = (
                input("Switch to public-private-companion preset? [Y/n]: ")
                .strip()
                .lower()
            )
        except EOFError:
            switch_comp = "y"
        except KeyboardInterrupt:
            raise PolicyCancelledError("Companion switch cancelled by user.")
        if switch_comp in ("", "y", "yes"):
            selected_preset = Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value

    # Companion Subflow (E-03, E-06)
    create_companion = False
    init_companion_git = False
    companion_dir = explicit_companion
    if (
        selected_preset == Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value
        and not companion_dir
    ):
        term.line()
        default_comp = f"{repo_path}.aw"
        try:
            comp_input = input(
                f"Enter companion directory path [{default_comp}]: "
            ).strip()
        except EOFError:
            comp_input = ""
        except KeyboardInterrupt:
            raise PolicyCancelledError("Companion selection cancelled by user.")
        companion_dir = comp_input if comp_input else default_comp

    if (
        selected_preset == Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value
        and companion_dir
    ):
        from agent_workflows.storage import (
            StorageSecurityError,
            IdentityConflictError,
            validate_companion_preflight,
        )

        try:
            preflight = validate_companion_preflight(
                target_repo=repo_path,
                companion_dir=companion_dir,
                backend="companion",
                aw_home=explicit_aw_home,
            )
            for w in preflight.get("warnings", []):
                term.status("warn", w)
        except (StorageSecurityError, IdentityConflictError) as exc:
            term.status("warn", f"Invalid companion path: {exc}")
            raise PolicyCancelledError(f"Companion validation failed: {exc}")

        comp_p = Path(companion_dir).expanduser().resolve()
        if not comp_p.exists():
            term.line()
            term.status(
                "warn",
                f"Companion directory '{companion_dir}' does not exist.",
            )
            try:
                create_choice = (
                    input(
                        f"Create companion directory and initialize Git repository at '{companion_dir}'? [Y/n]: "
                    )
                    .strip()
                    .lower()
                )
            except EOFError:
                create_choice = "y"
            except KeyboardInterrupt:
                raise PolicyCancelledError("Companion creation cancelled by user.")

            if create_choice not in ("", "y", "yes"):
                term.line()
                term.line("To use an existing private companion repository:")
                term.line(
                    f"  git clone <your-private-companion-remote-url> '{companion_dir}'"
                )
                term.line("Then re-run 'aw install'.")
                raise PolicyCancelledError(
                    "Companion directory does not exist and creation was declined."
                )
            create_companion = True
            init_companion_git = True
        else:
            git_dir = comp_p / ".git"
            if not git_dir.exists():
                term.line()
                term.status(
                    "warn",
                    f"Companion directory '{companion_dir}' exists but is not a Git repository.",
                )
                try:
                    init_choice = (
                        input(
                            f"Initialize a Git repository at '{companion_dir}'? [Y/n]: "
                        )
                        .strip()
                        .lower()
                    )
                except EOFError:
                    init_choice = "y"
                except KeyboardInterrupt:
                    raise PolicyCancelledError(
                        "Companion Git initialization cancelled by user."
                    )

                if init_choice not in ("", "y", "yes"):
                    term.line()
                    term.line(
                        "To track AW records in this companion, initialize Git manually:"
                    )
                    term.line(f"  git -C '{companion_dir}' init")
                    term.line(
                        "Or clone an existing private companion before installing."
                    )
                    raise PolicyCancelledError(
                        "Companion directory is not a Git repository and git init was declined."
                    )
                init_companion_git = True

    pls, gps, dm, rb, ds = get_preset_defaults(selected_preset)
    policy = ProjectPolicy(
        preset=selected_preset,
        delivery_mode=explicit_delivery or dm,
        records_backend=explicit_backend or rb,
        durability_state=ds,
        aw_home=explicit_aw_home,
        companion_dir=companion_dir,
        enabled_hosts=explicit_hosts
        if explicit_hosts is not None
        else ["opencode", "claude", "antigravity"],
        placements=pls,
        git_policies=gps,
        target_visibility=target_vis,
        create_companion=create_companion,
        init_companion_git=init_companion_git,
    )
    policy.validate(repo_path=repo_path)

    # Pre-Write Plan Preview (E-04)
    term.line()
    term.line(render_pre_write_plan(policy, repo_path, term=term))
    term.line()

    return policy


def persist_project_policy(
    repo_path: str,
    policy: ProjectPolicy,
    dry_run: bool = False,
    replace_config: bool = False,
) -> Dict[str, Any]:
    """Persist confirmed policy atomically to project.json and local.json (E-03)."""
    if dry_run:
        res = policy.to_dict()
        res["written_paths"] = []
        return res

    switch = config_placement_switch(repo_path, policy)
    if switch is not None:
        cur_preset = None
        cur_proj = switch.current_dir / "project.json"
        if cur_proj.exists():
            try:
                cur_preset = json.loads(cur_proj.read_text(encoding="utf-8")).get(
                    "preset"
                )
            except Exception:
                pass
        from_desc = (
            f"{cur_preset} ({switch.current_dir})"
            if cur_preset
            else str(switch.current_dir)
        )
        raise PlacementSwitchRequired(
            f"Switching config placement from {from_desc} "
            f"to {policy.preset} ({switch.target_dir}) is not supported by reinstall yet (backlog ui1aln).",
            current_dir=switch.current_dir,
            target_dir=switch.target_dir,
            current_preset=cur_preset,
            target_preset=policy.preset,
            reason=switch.reason,
        )

    raise_if_records_root_switch(repo_path, policy)

    from agent_workflows.project_context import resolve_project_context

    ctx = resolve_project_context(
        target_repo=repo_path,
        aw_home=policy.aw_home,
        delivery_mode=policy.delivery_mode,
        records_backend=policy.records_backend,
        preset=policy.preset,
        role=policy.role,
        companion_dir=policy.companion_dir,
    )

    proj_json = Path(ctx.physical_classes["config_project"])
    local_json = Path(ctx.physical_classes["config_local"])

    config_dir = proj_json.parent
    config_dir.mkdir(parents=True, exist_ok=True)
    if local_json.parent != config_dir:
        local_json.parent.mkdir(parents=True, exist_ok=True)

    # 1. Write portable project policy
    existing_cutovers: Optional[Dict[str, str]] = None
    existing_setids: Optional[Dict[str, Any]] = None
    existing_unknown: Dict[str, Any] = {}
    existing_consent: Dict[str, bool] = {}

    if not replace_config and proj_json.exists():
        try:
            with open(proj_json, "r", encoding="utf-8") as f:
                raw_proj = json.load(f)
            if isinstance(raw_proj, dict):
                try:
                    parsed_proj = parse_portable_policy(raw_proj)
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
                    if isinstance(raw_proj.get("cutovers"), dict):
                        existing_cutovers = dict(raw_proj["cutovers"])
                    if isinstance(raw_proj.get("setids"), dict):
                        existing_setids = dict(raw_proj["setids"])
                    if isinstance(raw_proj.get("non_secret_consent"), dict):
                        existing_consent = dict(raw_proj["non_secret_consent"])
                    existing_unknown = {
                        k: v for k, v in raw_proj.items() if k not in known_proj_keys
                    }
        except Exception:
            pass

    merged_consent = {**existing_consent, **(policy.non_secret_consent or {})}

    proj_schema = ProjectPolicySchema(
        schema_version=2,
        preset=policy.preset,
        role=policy.role,
        placements=policy.placements,
        git_policies=policy.git_policies,
        enabled_hosts=policy.enabled_hosts,
        non_secret_consent=merged_consent,
        delivery_mode=policy.delivery_mode,
        records_backend=policy.records_backend,
        cutovers=existing_cutovers,
        setids=existing_setids,
        unknown_fields=existing_unknown if existing_unknown else None,
    )
    tmp_proj = config_dir / ".tmp_project.json"
    with open(tmp_proj, "w", encoding="utf-8") as f:
        json.dump(proj_schema.to_dict(), f, indent=2)
    os.replace(tmp_proj, proj_json)

    # 2. Write machine-local binding
    existing_slug = ""
    existing_common = None
    existing_worktree = None
    existing_companion = None
    existing_overrides: Dict[str, Any] = {}
    existing_aliases: Dict[str, str] = {}
    existing_local_unknown: Dict[str, Any] = {}

    if not replace_config and local_json.exists():
        try:
            with open(local_json, "r", encoding="utf-8") as f:
                raw_local = json.load(f)
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
        except Exception:
            pass

    companion_dir_to_write = policy.companion_dir
    if (
        companion_dir_to_write is None
        and policy.records_backend == RecordsBackend.COMPANION.value
        and existing_companion is not None
    ):
        companion_dir_to_write = existing_companion

    if replace_config or not local_json.exists():
        local_schema = LocalBindingSchema(
            schema_version=2,
            project_id=ctx.project_id,
            companion_dir=policy.companion_dir,
        )
    else:
        local_schema = LocalBindingSchema(
            schema_version=2,
            project_id=ctx.project_id,
            human_slug=existing_slug,
            common_dir=existing_common,
            worktree_path=existing_worktree,
            companion_dir=companion_dir_to_write,
            runtime_overrides=existing_overrides if existing_overrides else None,
            local_aliases=existing_aliases if existing_aliases else None,
            unknown_fields=existing_local_unknown if existing_local_unknown else None,
        )
    tmp_local = local_json.parent / ".tmp_local.json"
    with open(tmp_local, "w", encoding="utf-8") as f:
        json.dump(local_schema.to_dict(), f, indent=2)
    os.replace(tmp_local, local_json)

    # 3. Synchronize cutover dates into project.json
    from agent_workflows import config as _config

    _config.sync_cutovers_on_install(repo_path, aw_home=policy.aw_home)

    p_repo = Path(repo_path).resolve()
    written_paths: List[str] = []
    for p in (proj_json, local_json):
        try:
            rel = p.resolve().relative_to(p_repo)
            written_paths.append(rel.as_posix())
        except ValueError:
            written_paths.append(str(p))

    res = policy.to_dict()
    res["written_paths"] = written_paths
    return res
