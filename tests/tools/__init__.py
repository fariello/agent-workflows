"""Measurement and audit tooling for test tiers (IPD hguae9)."""

from __future__ import annotations

import os
import pkgutil

# Extend package path so 'import tools.<mod>' finds both tests/tools/ and repo root tools/
__path__ = pkgutil.extend_path(__path__, __name__)
_root_tools = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "tools")
)
if os.path.isdir(_root_tools) and _root_tools not in __path__:
    __path__.append(_root_tools)
