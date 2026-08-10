"""Maintained record producer inventory and routing contract (IPD 20260809-awlayout-08).

This module defines the machine-readable inventory of record-producing workflows and Python
modules, and provides the shared backend-neutral record routing helper specified by
``.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`` Section 11 & 14.

Invariants:
- SHARED ROUTING CONTRACT: All Python and workflow producers query the logical records root and commit policy.
- TARGET-GIT ABSENCE: External records (home, companion) resolve outside the target repo work-tree.
- STATE EXCLUSION: Records producers MUST NOT write beneath the resolved state root.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import LogicalRoot, RecordsBackend


@dataclass(frozen=True)
class RecordProducerEntry:
    """Record producer inventory item (E-01)."""

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
        source_path="agent_workflows/plans.py",
        anchor="scaffold_plan",
        operation="create",
        category="plans",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="specs_create",
        source_path="agent_workflows/specs.py",
        anchor="create_spec",
        operation="create",
        category="specs",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="research_create",
        source_path="agent_workflows/research.py",
        anchor="create_research",
        operation="create",
        category="research",
        resolver_surface="python_api",
        commit_policy_consumer="prompt_and_run_commit",
    ),
    RecordProducerEntry(
        name="ipd_workflow",
        source_path=".agents/workflows/ipd/ipd.md",
        anchor="scaffold",
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
LEGACY_ALLOWLIST = {
    "agent_workflows/attention.py",
    "agent_workflows/attention_contract.py",
    "agent_workflows/artifact_core.py",
    "agent_workflows/specs.py",
    "agent_workflows/plans.py",
    "agent_workflows/research.py",
}


@dataclass(frozen=True)
class RecordRoutingInfo:
    """Logical record routing resolution result (E-02)."""

    records_root: str
    records_backend: str
    commit_destination: Optional[str]  # "repository" if git stageable, None if external
    allow_git_stage: bool


def resolve_record_routing(
    target_repo: Optional[str] = None, aw_home: Optional[str] = None
) -> RecordRoutingInfo:
    """Resolve backend-neutral record routing and commit policy (E-02)."""
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
