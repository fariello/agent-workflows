"""Canonical, single-source lifecycle subdirectory table (Set placelib, Order 01, IPD d1lo52).

This module is the SINGLE SOURCE OF TRUTH for which record types have status/disposition
subdirectories, and what those subdirectories are.

LEAF MODULE BY DESIGN:
This module imports NOTHING from `agent_workflows`. This is an architectural invariant:
deliberately dependency-free modules (such as `layout`, `plans`, and `attention_contract`)
can safely import this module without risking import cycles. Do NOT add any intra-package
imports to this module.

SPEC ROW ORDER IS A SHIPPED CONTRACT:
Approved spec `kw5y2s` pins `"lifecycle_subdirs"` as an ordered JSON array for `plans` and `specs`.
`layout.WorkspaceLayout.to_dict` emits `list(rc.lifecycle_subdirs)` positionally.
The `specs` row order here is taken from `layout.build_default_layout()` and MUST be preserved:
("draft", "to-review", "reviewed", "approved", "implementing", "implemented", "deferred", "parked", "superseded").
"""

from __future__ import annotations

import types
from typing import Mapping, Tuple

_RAW_LIFECYCLE_SUBDIRS = {
    "plans": (
        "pending",
        "executed",
        "superseded",
        "not-executed",
        "reusable",
    ),
    "prompts": (
        "pending",
        "executed",
        "superseded",
        "not-executed",
        "reusable",
    ),
    "specs": (
        "draft",
        "to-review",
        "reviewed",
        "approved",
        "implementing",
        "implemented",
        "deferred",
        "parked",
        "superseded",
    ),
    "backlog": (
        "open",
        "graduated",
        "blocked",
        "parked",
        "done",
    ),
}

LIFECYCLE_SUBDIRS: Mapping[str, Tuple[str, ...]] = types.MappingProxyType(
    _RAW_LIFECYCLE_SUBDIRS
)

# Legacy read alias for `executed` in plans (D52/Dnn). Not a real lifecycle subdir.
PLANS_DONE_ALIAS = "done"


def subdirs_for(record_type: str) -> Tuple[str, ...]:
    """Return the lifecycle subdirectories for `record_type`, or () if it has none."""
    return LIFECYCLE_SUBDIRS.get(record_type, ())
