"""Single source of truth (P8) for home-path detection patterns and prefilters.

Defines the three structural home-path detection classes (POSIX, macOS, Windows)
shared by `agent_schema` (fused alternation) and `leak_sanitizer` (individual fail
rules).

Measured byte-identity (F-01) ensures the fused form `(?:p1|p2|p3)` is derivable directly
from the individual pattern bodies with zero divergence across consumers.

This module is a stdlib-only leaf with no intra-package imports and requires no
sanitizer exemption in `_ALLOWED_PATHS`: the pattern literals themselves scan clean
under `scan_text`.
"""

from __future__ import annotations

from typing import Mapping, Optional


HOME_PATH_RULES: dict[str, tuple[str, tuple[str, ...]]] = {
    # Any user's real POSIX home dir. Generic doc placeholders (u, alice, user, USER, <...>) allowed.
    "home-path": (
        r"/home/(?!u/|alice/|user/|USER/|<)[A-Za-z0-9._-]+",
        ("/home/",),
    ),
    # macOS home dirs.
    "users-path": (
        r"/Users/(?!<|user/)[A-Za-z0-9._-]+",
        ("/Users/",),
    ),
    # Windows home dirs (both slash forms).
    "windows-home": (
        r"[A-Za-z]:[\\/]+Users[\\/]+(?!<)[A-Za-z0-9._-]+",
        ("Users",),
    ),
}


def fused_home_path_pattern(
    rules: Optional[Mapping[str, tuple[str, tuple[str, ...]]]] = None,
) -> str:
    """Render the fused non-capturing alternation of home-path pattern bodies.

    Constructs `(?:body1|body2|...)` in declaration order from the given rules mapping
    (defaults to HOME_PATH_RULES). Pure function with no side effects.
    """
    source = HOME_PATH_RULES if rules is None else rules
    bodies = [body for body, _ in source.values()]
    return "(?:" + "|".join(bodies) + ")"
