#!/usr/bin/env python3
"""DEPRECATED shim: use the `agent-workflows` / `aw` CLI instead.

The install engine moved into the `agent_workflows` package (IPD-2, DECISIONS D46). This
root script is kept as a thin, back-compatible shim so existing invocations
(`python3 install-workflows.py --repo ... --source ...`) and any downstream automation
keep working. It parses the same historical flags (`--repo`, `--source`, `--dry-run`,
`--no-backup`, `--no-prune`, `--version`) via the engine and delegates to it.

Prefer the installed CLI:  `aw install <dir>`  (or `agent-workflows install <dir>`).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the sibling `agent_workflows` package importable when this shim is run directly
# from a source checkout (before any `pip install`).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_workflows import engine  # noqa: E402


def main() -> int:
    print(
        "note: install-workflows.py is deprecated; use 'aw install <dir>' "
        "(or 'agent-workflows install <dir>'). Delegating to the engine.",
        file=sys.stderr,
    )
    # engine.main() reads sys.argv and honors the historical flags unchanged.
    return engine.main()


if __name__ == "__main__":
    raise SystemExit(main())
