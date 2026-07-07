"""agent-workflows: reusable, tool-agnostic agent workflows + their installer/CLI.

This package holds the install engine and CLI. The shipped workflow tree
(`.agents/workflows/`) is bundled as package data under `agent_workflows/_data/` in the
wheel and located at runtime via `_compat.packaged_source_root()`. In a source checkout
the tree lives at the repo root instead; both layouts are supported.

`__version__` is the git-tag-driven semver resolved by `versioning.resolve_version`
(DECISIONS D44): a clean tagged checkout reports e.g. `1.0.0`; a dirty/ahead tree reports
a `1.0.1.devN+g<sha>` string; an installed wheel reads its baked VERSION.
"""

from __future__ import annotations

from pathlib import Path

from . import versioning


def _resolve_own_version() -> str:
    """Best-effort version of this package for `__version__` (never raises)."""

    try:
        # From a git checkout the repo root is two parents up from this file
        # (agent_workflows/__init__.py -> repo root). resolve_version falls back to the
        # baked VERSION file when there is no git tree (wheel/copied-out).
        repo_root = Path(__file__).resolve().parent.parent
        return versioning.resolve_version(repo_root)
    except Exception:
        return "unknown"


__version__ = _resolve_own_version()
