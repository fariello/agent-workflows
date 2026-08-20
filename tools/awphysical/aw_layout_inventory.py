#!/usr/bin/env python3
"""Backward-compatibility shim for tools.awphysical.aw_layout_inventory.

The layout inventory module has been moved into the shipped package at
`agent_workflows.layout_inventory` so `aw migrate-layout` works when pip-installed.
This shim re-exports all symbols for any legacy source callers.
"""

from __future__ import annotations

import sys

from agent_workflows.layout_inventory import (  # noqa: F401
    _RECORDS_SUBPATH_REWRITES,
    _atomic_json,
    _default_roots,
    _flatten_records_subpath,
    _git_state,
    _ignored_dirs,
    _legacy_class,
    _nul_paths,
    _repo_relative,
    _run_git,
    _walk,
)
from agent_workflows.layout_inventory import *  # noqa: F401, F403

if __name__ == "__main__":
    from agent_workflows.layout_inventory import main

    sys.exit(main())
