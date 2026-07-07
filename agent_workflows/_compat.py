"""Compatibility helpers, notably a 3.8-safe locator for the shipped workflow tree.

The framework ships `.agents/workflows/` as package data. From an installed wheel it
lives at `agent_workflows/_data/.agents/workflows/`; from a source checkout it lives at
the repo root. We must find it without a runtime third-party dependency and while
honoring the 3.8 floor.

`importlib.resources.files()` (the clean traversable API) was ADDED IN PYTHON 3.9, but
the floor is 3.8 (DECISIONS D44/spec). So we prefer `files()` when present (3.9+) and
otherwise fall back to a `__file__`-relative path, which is 3.8-safe and correct for a
normal (non-zip) wheel install. The wheel is built non-zip-safe so `__file__` is a real
filesystem path (IPD-2 R-1).
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
        # Python 3.8: importlib.resources.files does not exist; use the fallback below.
        pass

    # 3.8-safe fallback (and belt-and-suspenders for 3.9+ non-zip installs): resolve the
    # data dir relative to this module's file. Works whenever the package is unpacked on
    # disk (our wheel is non-zip-safe).
    here = Path(__file__).resolve().parent
    path = here.joinpath(*_DATA_RELATIVE)
    if path.is_dir():
        return path

    return None
