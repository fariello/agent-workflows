#!/usr/bin/env python3
"""Backwards-compatible shim for the OpenCode IPD runner (runipd).

The runner's implementation was graduated into the toolkit package as
``agent_workflows.oc_runipd`` (awocrunner Set) and is now the canonical
`aw oc runipd` subcommand. This file is a THIN delegating shim so existing
invocations - ``python3 tools/ipdrunner/runipd.py ...`` and the driver runbook -
keep working with zero duplicated logic. Prefer ``aw oc runipd ...`` going forward.

It contains NO runner logic: it adds the repository root to ``sys.path`` (so the
package resolves when this file is run directly from a checkout), imports
``agent_workflows.oc_runipd``, re-exports the runner's public names for any operator
code that imported them off this module, and delegates ``main``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# When run as `python3 tools/ipdrunner/runipd.py`, sys.path[0] is this file's directory, so the
# `agent_workflows` package (at the repo root, two levels up) is not importable without this.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agent_workflows import oc_runipd  # noqa: E402

# Re-export the runner's public names for backward compatibility (each IS the packaged object,
# so there is no shadow copy of the logic).
main = oc_runipd.main
DriverError = oc_runipd.DriverError
Palette = oc_runipd.Palette
Heartbeat = oc_runipd.Heartbeat
PlanRecord = oc_runipd.PlanRecord


if __name__ == "__main__":
    raise SystemExit(oc_runipd.main(sys.argv[1:]))
