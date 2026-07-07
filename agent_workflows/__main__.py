"""Enable `python -m agent_workflows` to invoke the CLI."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
