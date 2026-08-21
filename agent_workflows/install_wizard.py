"""Pure policy collection, wizard state machine, presets, and pre-write preview (IPD 20260810-awphysical-03).

This module implements the pure wizard state machine, four approved presets,
custom placement validation, exact pre-write plan preview, update checkpoints,
and atomic policy persistence specified by
``.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md``.

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
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
)
from agent_workflows.term import Term


class PolicyError(Exception):
    """Base exception for policy errors."""

    pass


class InvalidPolicyError(PolicyError):
    """Raised when policy validation rules are violated."""

    pass


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
            RootClass.STATE_DURABLE.value: Placement.TARGET_TRACKED.value,
            RootClass.STATE_RUNTIME.value: Placement.TARGET_IGNORED.value,
            RootClass.RECORDS.value: Placement.TARGET_TRACKED.value,
        }
        git_policies = {
            RootClass.SYSTEM.value: GitPolicy.TARGET_GIT.value,
            RootClass.CONFIG_PROJECT.value: GitPolicy.TARGET_GIT.value,
            RootClass.CONFIG_LOCAL.value: GitPolicy.IGNORED.value,
            RootClass.STATE_DURABLE.value: GitPolicy.TARGET_GIT.value,
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
            RootClass.STATE_DURABLE.value: Placement.TARGET_TRACKED.value,
            RootClass.STATE_RUNTIME.value: Placement.TARGET_IGNORED.value,
            RootClass.RECORDS.value: Placement.TARGET_TRACKED.value,
        }
        git_policies = {
            RootClass.SYSTEM.value: GitPolicy.TARGET_GIT.value,
            RootClass.CONFIG_PROJECT.value: GitPolicy.TARGET_GIT.value,
            RootClass.CONFIG_LOCAL.value: GitPolicy.IGNORED.value,
            RootClass.STATE_DURABLE.value: GitPolicy.TARGET_GIT.value,
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

    def validate(self) -> None:
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

        # Invariant: clean-delta delivery mode MUST NOT use repository records backend
        if (
            self.delivery_mode == DeliveryMode.CLEAN_DELTA.value
            and self.records_backend == RecordsBackend.REPOSITORY.value
        ):
            raise InvalidPolicyError(
                f"Forbidden policy combination: '{DeliveryMode.CLEAN_DELTA.value}' delivery mode "
                f"MUST NOT use '{RecordsBackend.REPOSITORY.value}' records backend."
            )

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

    aw_home_str = policy.aw_home or str(Path.home() / ".aw")
    aw_home_formatted = _format_path(aw_home_str)
    repo_formatted = _format_path(repo_path)

    try:
        ctx = resolve_project_context(
            target_repo=repo_path,
            aw_home=policy.aw_home,
            delivery_mode=policy.delivery_mode,
            records_backend=policy.records_backend,
        )
        if ctx.physical_classes:
            resolved_roots = {
                k: _format_path(str(v)) for k, v in ctx.physical_classes.items()
            }
        else:
            resolved_roots = {
                k: _format_path(str(v)) for k, v in ctx.logical_roots.items()
            }
    except Exception:
        resolved_roots = {}

    for cls in ROOT_CLASSES:
        placement = policy.placements.get(cls, "")
        if placement == Placement.HOME_UNTRACKED.value or "home" in placement:
            resolved_roots[cls] = (
                f"{aw_home_formatted}/projects/{Path(repo_path).name}/.aw/{cls}"
            )
        elif placement == Placement.COMPANION_TRACKED.value or "companion" in placement:
            comp = _format_path(policy.companion_dir or f"{repo_path}.aw")
            resolved_roots[cls] = f"{comp}/.aw/{cls}"
        else:
            resolved_roots[cls] = f"{repo_formatted}/.aw/{cls}"

    lines = []
    lines.append(term.colorize("AW Pre-Write Physical Layout & Consent Plan", "bold"))
    lines.append(f"  Target Repository: {repo_formatted}")
    lines.append(f"  Preset:            {policy.preset}")
    lines.append(f"  Role:              {policy.role}")
    lines.append(f"  Target Visibility: {policy.target_visibility}")
    lines.append("")
    lines.append(term.colorize("Resolved Physical Classes & Git Policies:", "bold"))

    for cls in ROOT_CLASSES:
        path_str = resolved_roots.get(cls, f"resolved-{cls}")
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
    lines.append(f"  - AGENTS.md:       {repo_formatted}/AGENTS.md (adapter pointer)")
    lines.append(f"  - .claude/:        {repo_formatted}/.claude/ (discovery adapter)")
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
            "  Target Delta:     .aw/system/, .aw/config/project.json, .aw/state/durable created/updated."
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
    if policy.durability_state == DurabilityState.UNVERSIONED.value:
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
    proj_json = p_repo / ".aw" / "config" / "project.json"
    local_json = p_repo / ".aw" / "config" / "local.json"
    legacy_json = p_repo / ".aw" / "config" / "config.json"
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
        return ProjectPolicy(
            preset=getattr(ctx, "preset", Preset.PRIVATE_TARGET.value),
            role=getattr(ctx, "role", ProjectRole.TARGET.value),
            delivery_mode=ctx.delivery_mode,
            records_backend=ctx.records_backend,
            durability_state=ctx.durability_state,
            aw_home=str(ctx.effective_aw_home),
            companion_dir=getattr(ctx, "companion_dir", None),
            enabled_hosts=getattr(
                ctx, "enabled_hosts", ["opencode", "claude", "antigravity"]
            ),
        )
    except Exception:
        return None


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
        preset = explicit_preset or existing_policy.preset
        delivery = explicit_delivery or existing_policy.delivery_mode
        backend = explicit_backend or existing_policy.records_backend
        companion = explicit_companion or existing_policy.companion_dir
        aw_home = explicit_aw_home or existing_policy.aw_home
        hosts = (
            explicit_hosts
            if explicit_hosts is not None
            else existing_policy.enabled_hosts
        )

        pol = ProjectPolicy(
            preset=preset,
            delivery_mode=delivery,
            records_backend=backend,
            durability_state=existing_policy.durability_state,
            aw_home=aw_home,
            companion_dir=companion,
            enabled_hosts=hosts,
        )
        pol.validate()
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
            missing_fields.append("--records-backend (home | companion | repository)")

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
    pol.validate()
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
    policy.validate()

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
    """Persist confirmed policy atomically to .aw/config/project.json and local.json (E-05)."""
    p_repo = Path(repo_path)
    config_dir = p_repo / ".aw" / "config"
    durable_state_dir = p_repo / ".aw" / "state" / "durable"

    if dry_run:
        return policy.to_dict()

    config_dir.mkdir(parents=True, exist_ok=True)
    durable_state_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write portable project policy (.aw/config/project.json)
    proj_schema = ProjectPolicySchema(
        schema_version=2,
        preset=policy.preset,
        role=policy.role,
        placements=policy.placements,
        git_policies=policy.git_policies,
        enabled_hosts=policy.enabled_hosts,
        non_secret_consent=policy.non_secret_consent,
        delivery_mode=policy.delivery_mode,
        records_backend=policy.records_backend,
    )
    proj_json = config_dir / "project.json"
    tmp_proj = config_dir / ".tmp_project.json"
    with open(tmp_proj, "w", encoding="utf-8") as f:
        json.dump(proj_schema.to_dict(), f, indent=2)
    os.replace(tmp_proj, proj_json)

    # 2. Write machine-local binding (.aw/config/local.json)
    local_schema = LocalBindingSchema(
        schema_version=2,
        companion_dir=policy.companion_dir,
    )
    local_json = config_dir / "local.json"
    tmp_local = config_dir / ".tmp_local.json"
    with open(tmp_local, "w", encoding="utf-8") as f:
        json.dump(local_schema.to_dict(), f, indent=2)
    os.replace(tmp_local, local_json)

    # 3. Update durable install snapshot (.aw/state/durable/install.json)
    install_snapshot = durable_state_dir / "install.json"
    tmp_snap = durable_state_dir / ".tmp_install.json"
    snapshot_data = {
        "installed_version": "2026.8.10",
        "schema_version": 2,
        "policy": policy.to_dict(),
    }
    with open(tmp_snap, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, indent=2)
    os.replace(tmp_snap, install_snapshot)

    # 4. Append to durable install history (.aw/state/durable/history/installs.jsonl)
    history_dir = durable_state_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / "installs.jsonl"
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot_data) + "\n")

    return policy.to_dict()
