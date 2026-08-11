"""Compatibility helpers, notably a version-robust locator for the shipped workflow tree.

The framework ships `.agents/workflows/` as package data. From an installed wheel it
lives at `agent_workflows/_data/.agents/workflows/`; from a source checkout it lives at
the repo root. We must find it without a runtime third-party dependency and across
supported Python versions.

The declared floor is Python 3.9 (`pyproject.toml`; DECISIONS D44/spec).
`importlib.resources.files()` (the clean traversable API) is available on 3.9+, so we
prefer it, and otherwise fall back to a `__file__`-relative path. That fallback keeps
the locator working for a normal (non-zip) wheel install and remains best-effort on an
older interpreter (3.8) even though 3.8 is below the supported floor and not covered by
CI. The wheel is built non-zip-safe so `__file__` is a real filesystem path (IPD-2 R-1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

# Relative locations of the bundled tree inside the installed package.
SYSTEM_DATA_RELATIVE = ("_data", ".aw", "system")
LEGACY_DATA_RELATIVE = ("_data", ".agents", "workflows")
_DATA_RELATIVE = LEGACY_DATA_RELATIVE


def packaged_source_root() -> Optional[Path]:
    """Return the bundled `.aw/system/` or `.agents/workflows/` dir if this package carries it, else None.

    None means the package has no bundled data (a source checkout / editable install
    where the tree lives at the repo root instead); the caller then uses the repo-root or
    `--source` path.
    """

    for rel in (SYSTEM_DATA_RELATIVE, LEGACY_DATA_RELATIVE):
        try:
            from importlib.resources import files  # 3.9+

            try:
                base = files("agent_workflows")
                candidate = base.joinpath(*rel)
                path = Path(str(candidate))
                if path.is_dir():
                    return path
            except (ModuleNotFoundError, FileNotFoundError, TypeError):
                pass
        except ImportError:
            pass

        here = Path(__file__).resolve().parent
        path = here.joinpath(*rel)
        if path.is_dir():
            return path

    return None
