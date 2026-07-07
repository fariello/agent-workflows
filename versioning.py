"""Back-compat re-export shim for the versioning resolver.

The implementation moved into the package at ``agent_workflows/versioning.py`` (IPD-2,
DECISIONS D46). This 1-line shim preserves the historical top-level import path so the
Makefile (`make version-file`), the build hook, and any caller importing ``versioning``
from the repo root keep working. Prefer ``from agent_workflows.versioning import ...`` in
new code.
"""

from __future__ import annotations

from agent_workflows.versioning import *  # noqa: F401,F403
from agent_workflows.versioning import (  # noqa: F401  (explicit re-export of non-* names)
    _git_describe,
    parse_describe,
    parse_our_version,
    read_version_file,
    resolve_version,
    status,
    compare,
)
