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
from ._compat import packaged_source_root


def _resolve_own_version() -> str:
    """Best-effort version of this package for `__version__` (never raises).

    - Installed wheel: read the baked VERSION from the bundled data tree
      (`agent_workflows/_data/.agents/workflows/VERSION`) - AC-1.
    - Source checkout: resolve from git via the repo-root tree (two parents up), so a
      clean tagged tree reports the semver and a dirty/ahead tree reports a .devN string.
    """

    try:
        bundled = packaged_source_root()
        if bundled is not None:
            # Installed package: the tree has no git; resolve_version reads its VERSION.
            return versioning.resolve_version(bundled, version_file=bundled / "VERSION")
        # Source checkout: repo root is two parents up from this file.
        repo_root = Path(__file__).resolve().parent.parent
        return versioning.resolve_version(repo_root)
    except Exception:
        return "unknown"


__version__ = _resolve_own_version()
