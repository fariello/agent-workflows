"""setupmarker Order 01: the AW operational-action LEDGER was removed.

It was redundant with the backlog tier (the general operational-task machinery) and its
`ActionManager.__init__` eagerly created `.aw/state/actions/*` - which a read-only attention scan
reached, stamping `.aw/state/` into every scanned repo (write-on-read). The single reminder it held
(post-install `setup-repo`) is now the self-explaining, gitignored, per-repo marker
`.aw/setup-repo-needed.md` (see `engine.write_setup_marker` / `attention.setup_needed`).

The install-history audit log (a genuine append-only artifact) lives on in
`agent_workflows.install_history`; it is re-exported here for back-compatibility.
"""

from __future__ import annotations

from agent_workflows.install_history import (  # noqa: F401  (back-compat re-export)
    record_install_history,
    _redact_details,
)
