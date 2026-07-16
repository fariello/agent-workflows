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

# Relative location of the bundled tree inside the installed package.
_DATA_RELATIVE = ("_data", ".agents", "workflows")


def packaged_source_root() -> Optional[Path]:
    """Return the bundled `.agents/workflows/` dir if this package carries it, else None.

    None means the package has no bundled data (a source checkout / editable install
    where the tree lives at the repo root instead); the caller then uses the repo-root or
    `--source` path.
    """

    # Preferred path on 3.9+: importlib.resources.files() gives a traversable to the
    # package, from which we can reach the bundled data directory.
    try:
        from importlib.resources import files  # 3.9+

        try:
            base = files("agent_workflows")
            candidate = base.joinpath(*_DATA_RELATIVE)
            # `candidate` is a Traversable; for a normal filesystem install it maps to a
            # real path. Convert via str() and Path(); is_dir() confirms presence.
            path = Path(str(candidate))
            if path.is_dir():
                return path
        except (ModuleNotFoundError, FileNotFoundError, TypeError):
            pass
    except ImportError:
        # Below 3.9 importlib.resources.files does not exist; use the fallback below.
        pass

    # Fallback (and belt-and-suspenders for 3.9+ non-zip installs): resolve the
    # data dir relative to this module's file. Works whenever the package is unpacked on
    # disk (our wheel is non-zip-safe).
    here = Path(__file__).resolve().parent
    path = here.joinpath(*_DATA_RELATIVE)
    if path.is_dir():
        return path

    return None
