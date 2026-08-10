"""Pure policy collection, wizard models, and update checkpoints for AW installation (IPD 20260809-awlayout-04).

This module implements the pure policy models, validation, interactive first-install interview,
concise update checkpoint, and noninteractive policy resolution specified by
``.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`` Section 11.

Invariants:
- SEPARATION: Choice logic and policy validation are separate from terminal rendering.
- INVARIANT ENFORCEMENT: Rejects `delivery=clean-delta` plus `records=repository` before any write.
- AUTOMATION SAFETY: Noninteractive first install with incomplete flags or `--yes` alone FAILS CLOSED
  before writes, identifying missing required policy fields.
- SINGLE CONFIRMATION: Interactive setup delegates policy collection here and uses `_confirm`
  as the single no-write confirmation boundary.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent_workflows.project_schema import (
    DELIVERY_MODES,
    RECORDS_BACKENDS,
    DeliveryMode,
    DurabilityState,
    RecordsBackend,
)
from agent_workflows.term import Term


class PolicyError(Exception):
    """Base exception for policy errors."""

    pass


class InvalidPolicyError(PolicyError):
    """Raised when policy validation rules are violated (e.g. clean-delta + repository records)."""

    pass


class IncompletePolicyError(PolicyError):
    """Raised when noninteractive execution is missing required policy choices."""

    pass


@dataclass(frozen=True)
class ProjectPolicy:
    """Immutable project layout and storage policy (spec Section 11)."""

    delivery_mode: str
    records_backend: str
    durability_state: str = DurabilityState.UNVERSIONED.value
    aw_home: Optional[str] = None
    enabled_hosts: List[str] = field(
        default_factory=lambda: ["opencode", "claude", "antigravity"]
    )

    def validate(self) -> None:
        """Validate policy rules before rendering or writes (spec Section 5.2 & 11)."""
        if self.delivery_mode not in DELIVERY_MODES:
            raise InvalidPolicyError(
                f"Invalid delivery_mode: '{self.delivery_mode}'. Must be one of {DELIVERY_MODES}."
            )

        if self.records_backend not in RECORDS_BACKENDS:
            raise InvalidPolicyError(
                f"Invalid records_backend: '{self.records_backend}'. Must be one of {RECORDS_BACKENDS}."
            )

        # Invariant: clean-delta delivery mode MUST NOT use 'repository' records backend (spec Section 5.2)
        if (
            self.delivery_mode == DeliveryMode.CLEAN_DELTA.value
            and self.records_backend == RecordsBackend.REPOSITORY.value
        ):
            raise InvalidPolicyError(
                "Forbidden policy combination: 'clean-delta' delivery mode MUST NOT use 'repository' records backend."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delivery_mode": self.delivery_mode,
            "records_backend": self.records_backend,
            "durability_state": self.durability_state,
            "aw_home": self.aw_home,
            "enabled_hosts": list(self.enabled_hosts),
        }


def format_policy_summary(policy: ProjectPolicy) -> str:
    """Format plain-text linear policy summary without ANSI codes."""
    lines = [
        "Project Policy Summary:",
        f"  Delivery Mode:    {policy.delivery_mode}",
        f"  Records Backend:  {policy.records_backend}",
        f"  Durability State: {policy.durability_state}",
        f"  AW_HOME:          {policy.aw_home or 'platform default (~/.aw)'}",
        f"  Enabled Hosts:    {', '.join(policy.enabled_hosts)}",
    ]
    return "\n".join(lines)


def resolve_policy_noninteractive(
    repo_path: str,
    existing_policy: Optional[ProjectPolicy] = None,
    explicit_delivery: Optional[str] = None,
    explicit_backend: Optional[str] = None,
    explicit_aw_home: Optional[str] = None,
    explicit_hosts: Optional[List[str]] = None,
) -> ProjectPolicy:
    """Resolve policy for noninteractive execution (spec Section 11.3 & E-04).

    Rules:
      - Existing saved policy MAY be reused.
      - First install REQUIRES every policy field (or explicit flags).
      - --yes alone on an unconfigured repo FAILS before writes and lists missing fields.
    """
    if existing_policy is not None:
        # Re-use existing valid policy unless overridden by explicit flags
        delivery = explicit_delivery or existing_policy.delivery_mode
        backend = explicit_backend or existing_policy.records_backend
        aw_home = explicit_aw_home or existing_policy.aw_home
        hosts = (
            explicit_hosts
            if explicit_hosts is not None
            else existing_policy.enabled_hosts
        )
        durability = existing_policy.durability_state

        pol = ProjectPolicy(
            delivery_mode=delivery,
            records_backend=backend,
            durability_state=durability,
            aw_home=aw_home,
            enabled_hosts=hosts,
        )
        pol.validate()
        return pol

    # First install noninteractive resolution
    missing_fields: List[str] = []
    if not explicit_delivery:
        missing_fields.append("--delivery-mode (tracked | clean-delta)")
    if not explicit_backend:
        missing_fields.append("--records-backend (home | companion | repository)")

    if missing_fields:
        raise IncompletePolicyError(
            f"Noninteractive first install requires complete policy choices. "
            f"Missing required fields: {', '.join(missing_fields)}. "
            f"Pass explicit policy flags or run interactively on a TTY."
        )

    pol = ProjectPolicy(
        delivery_mode=explicit_delivery,  # type: ignore
        records_backend=explicit_backend,  # type: ignore
        aw_home=explicit_aw_home,
        enabled_hosts=explicit_hosts
        if explicit_hosts is not None
        else ["opencode", "claude", "antigravity"],
    )
    pol.validate()
    return pol


def resolve_existing_policy(repo_path: str) -> Optional[ProjectPolicy]:
    """Attempt to load existing policy from repository context (spec Section 11.2)."""
    try:
        from agent_workflows.project_context import resolve_project_context

        ctx = resolve_project_context(target_repo=repo_path)
        return ProjectPolicy(
            delivery_mode=ctx.delivery_mode,
            records_backend=ctx.records_backend,
            durability_state=ctx.durability_state,
            aw_home=str(ctx.effective_aw_home),
        )
    except Exception:
        return None


def collect_policy_interactive(
    term: Term,
    repo_path: str,
    existing_policy: Optional[ProjectPolicy] = None,
    assume_yes: bool = False,
) -> ProjectPolicy:
    """Collect policy interactively with pros/cons explanations and update checkpoints (spec Section 11.1 & 11.2)."""

    if existing_policy is None:
        existing_policy = resolve_existing_policy(repo_path)

    # If stdin is not a TTY or --yes is specified, fallback to noninteractive resolution
    if assume_yes or not sys.stdin.isatty():
        return resolve_policy_noninteractive(
            repo_path=repo_path,
            existing_policy=existing_policy,
        )

    # Interactive Update Checkpoint (spec Section 11.2)
    if existing_policy is not None:
        term.heading("AW Policy Update Checkpoint")
        term.line(f"Current Policy for {repo_path}:")
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
        except (EOFError, KeyboardInterrupt):
            choice = "y"

        if choice in ("", "y", "yes"):
            return existing_policy

    # Full First-Install Interview or Policy Review (spec Section 11.1)
    term.heading("AW Installation & Policy Wizard")
    term.line("Configure delivery mode and records storage for this repository.")
    term.line()

    # Step 1: Delivery Mode
    term.line("1. Delivery Mode:")
    term.line(
        "   [1] tracked (RECOMMENDED): Target repository carries selected AW system content."
    )
    term.line(
        "   [2] clean-delta: Target repository carries no AW files; host discovers AW locally."
    )
    try:
        dm_choice = input("Select delivery mode [1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        dm_choice = "1"

    delivery_mode = (
        DeliveryMode.CLEAN_DELTA.value
        if dm_choice == "2"
        else DeliveryMode.TRACKED.value
    )

    # Step 2: Records Backend
    term.line()
    term.line("2. Records Storage Backend:")
    term.line(
        "   [1] home (RECOMMENDED): Records stored under AW_HOME/projects/<project-id>/records/."
    )
    term.line(
        "   [2] companion: Records stored in a separate sibling companion directory."
    )
    if delivery_mode == DeliveryMode.TRACKED.value:
        term.line(
            "   [3] repository: Records stored under target repository .aw/records/."
        )

    try:
        rb_choice = input("Select records backend [1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        rb_choice = "1"

    if rb_choice == "2":
        records_backend = RecordsBackend.COMPANION.value
    elif rb_choice == "3" and delivery_mode == DeliveryMode.TRACKED.value:
        records_backend = RecordsBackend.REPOSITORY.value
    else:
        records_backend = RecordsBackend.HOME.value

    policy = ProjectPolicy(
        delivery_mode=delivery_mode,
        records_backend=records_backend,
        enabled_hosts=["opencode", "claude", "antigravity"],
    )
    policy.validate()

    term.line()
    term.heading("Proposed Policy:")
    term.line(format_policy_summary(policy))
    term.line()

    return policy
