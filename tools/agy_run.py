#!/usr/bin/env python3
"""Backwards-compatible shim for the Antigravity multi-mode runner (agy_run).

The implementation was graduated into the toolkit package as
``agent_workflows.agy_run`` (runnernorm follow-up puot79e04) and is now the
canonical ``aw agy exec`` subcommand. This file is a THIN delegating shim so
existing invocations - ``python3 tools/agy_run.py ...`` - keep working with zero
duplicated logic. Prefer ``aw agy exec ...`` going forward.

(``aw agy run``/``runagy``/``runipd`` remain aliased to the separate multi-IPD
queue driver ``agy_runipd``; this single-target multi-mode runner is genuinely
distinct and does NOT collide with them.)

It contains NO tool logic: it adds the repository root to ``sys.path`` (so the
package resolves when this file is run directly from a checkout), imports
``agent_workflows.agy_run``, re-exports ALL of its names for any operator code
that imported them off this module (notably ``tools/antigravity_execute_ipd.py``,
which does ``import agy_run`` and re-exports ``ScriptError``/``AgyResult``/
``resolve_ipd``/``run_agy``/etc. off it), and delegates ``main``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agent_workflows import agy_run  # noqa: E402

# Re-export all module attributes (public and private) so callers/tests access the
# exact same symbols without duplication.
for _k, _v in vars(agy_run).items():
    if not _k.startswith("__"):
        globals()[_k] = _v


if __name__ == "__main__":
    raise SystemExit(agy_run.main(sys.argv[1:]))
