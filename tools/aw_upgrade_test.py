#!/usr/bin/env python3
"""Backwards-compatible shim for the upgrade rehearsal harness.

The implementation was graduated into the toolkit package as
``agent_workflows.upgrade_rehearsal`` (upgrehearse Set) and is now available as the
`aw upgrade-test` command. This file is a THIN delegating shim so existing
invocations - ``python3 tools/aw_upgrade_test.py ...`` - keep working with zero
duplicated logic. Prefer ``aw upgrade-test ...`` going forward.

It contains NO tool logic: it adds the repository root to ``sys.path`` (so the
package resolves when this file is run directly from a checkout), imports
``agent_workflows.upgrade_rehearsal``, re-exports its attributes for any caller or
test that imported them off this module, and delegates ``main``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agent_workflows import upgrade_rehearsal  # noqa: E402

# Re-export all module attributes (public and private) so callers/tests access the
# exact same symbols without duplication.
for _k, _v in vars(upgrade_rehearsal).items():
    if not _k.startswith("__"):
        globals()[_k] = _v


if __name__ == "__main__":
    raise SystemExit(upgrade_rehearsal.main(sys.argv[1:]))
