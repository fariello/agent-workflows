"""agent-workflows: reusable, tool-agnostic agent workflows + their installer/CLI.

This package holds the install engine and CLI. The shipped workflow tree
(`.aw/system/`, legacy `.agents/workflows/`) is bundled as package data under `agent_workflows/_data/` in the
wheel and located at runtime via `_compat.packaged_source_root()`. In a source checkout
the tree lives at the repo root instead; both layouts are supported.

`__version__` is the git-tag-driven semver resolved by `versioning.resolve_version`
(DECISIONS D44): a clean tagged checkout reports e.g. `1.0.0`; a dirty/ahead tree reports
a `1.0.1.devN+g<sha>` string; an installed wheel reports its distribution version.
"""

from __future__ import annotations

from pathlib import Path

from . import versioning
from ._compat import packaged_source_root


def _resolve_own_version() -> str:
    """Best-effort version of this package for `__version__` (never raises).

    - Installed wheel: locate the sibling `agent_workflows-*.dist-info` directory
      (`Path(__file__).resolve().parent.parent`) and read its distribution metadata version via
      `importlib.metadata.Distribution.at(...)`, falling back to the baked VERSION from
      the bundled data tree (`agent_workflows/_data/.aw/system/VERSION`, legacy
      `.agents/workflows/VERSION`) if no sibling dist-info resolves.
    - Source checkout: resolve from git via the repo-root tree (two parents up), so a
      clean tagged tree reports the semver and a dirty/ahead tree reports a .devN string.
    """

    try:
        bundled = packaged_source_root()
        if bundled is not None:
            # Installed package: look up the sibling dist-info that owns this module.
            try:
                import importlib.metadata

                site_packages = Path(__file__).resolve().parent.parent
                candidates = sorted(site_packages.glob("agent_workflows-*.dist-info"))
                if not candidates:
                    candidates = sorted(
                        site_packages.glob("agent-workflows-*.dist-info")
                    )
                for dist_info in candidates:
                    if dist_info.is_dir():
                        dist = importlib.metadata.Distribution.at(str(dist_info))
                        ver = dist.version
                        if ver:
                            return ver
            except Exception:
                pass
            # Fall back to the bundled VERSION file.
            return versioning.resolve_version(bundled, version_file=bundled / "VERSION")
        # Source checkout: repo root is two parents up from this file.
        repo_root = Path(__file__).resolve().parent.parent
        return versioning.resolve_version(repo_root)
    except Exception:
        return "unknown"


__version__ = _resolve_own_version()
