#!/usr/bin/env python3
"""Execute an AW IPD with the Antigravity CLI, then audit the result.

This script is a backwards-compatible frontend that delegates directly to
``tools/agy_run.py`` in IPD mode. All existing CLI options and behaviors are preserved.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

# Import shared functionality from agy_run
sys.path.insert(0, str(Path(__file__).resolve().parent))
import agy_run

# Re-export classes and functions for backward compatibility
ScriptError = agy_run.ScriptError
AgyResult = agy_run.AgyResult
repository_root = agy_run.repository_root
resolve_ipd = agy_run.resolve_ipd
stable_id_from_filename = agy_run.stable_id_from_filename
relative_posix = agy_run.relative_posix
resolve_agy = agy_run.resolve_agy
run_agy = agy_run.run_agy


def parse_args(argv: Iterable[str] | None = None):
    return agy_run.parse_args(argv)


def audit_prompt(ipd_path: str) -> str:
    return agy_run.build_turn2_prompt("ipd", ipd_path)


def main(argv: Iterable[str] | None = None) -> int:
    return agy_run.main(argv)


def run(argv: Iterable[str] | None = None) -> int:
    return agy_run.run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
