#!/usr/bin/env python3
"""Watch aw runners and display journey progress and process-tree resource usage."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agent_workflows import runners_monitor  # noqa: E402


def main() -> int:
    return runners_monitor.main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
