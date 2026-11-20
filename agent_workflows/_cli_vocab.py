"""Zero-heavy-import CLI parser vocabulary constants.

Kept separate from runtime modules (`run_viewer`, `backlog`, `completion`) so `cli._build_parser()`
does not transitively import `runner_shared`, `platform_lock`/`filelock`, or `check_engine` on
every `aw` CLI invocation. The runtime modules re-export these constants directly to preserve a
single source of truth with zero drift.
"""

from __future__ import annotations

from agent_workflows import lifecycle_dirs as _LD

RUNS_VIEWER_LEAF_NAMES: tuple[str, ...] = (
    "decisions",
    "evidence",
    "list",
    "next",
    "questions",
    "resume",
    "show",
    "status",
    "verify-ledger",
)

SUPPORTED_SHELLS: tuple[str, ...] = ("bash", "zsh", "fish")

BACKLOG_STATUS_DIRS = _LD.LIFECYCLE_SUBDIRS["backlog"]
BACKLOG_STATUSES = frozenset(BACKLOG_STATUS_DIRS)
BACKLOG_PRIORITIES = frozenset(("high", "medium", "low"))
BACKLOG_KINDS = frozenset(("bug", "feature", "chore", "security", "followup"))
