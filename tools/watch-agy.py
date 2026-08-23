#!/usr/bin/env python3
"""Backwards-compatible wrapper for watch-agy, delegating to pwatch with agy defaults."""

from __future__ import annotations

import sys
from pathlib import Path

# Add tools directory to path
tools_dir = Path(__file__).resolve().parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

import pwatch  # noqa: E402


def main() -> int:
    # If no match flags or positional arguments were passed, default to '-m agy'
    argv = list(sys.argv[1:])
    parser = pwatch.build_parser()
    try:
        args, _ = parser.parse_known_args(argv)
        has_match = bool(
            args.proc_match
            or args.proc_imatch
            or args.proc_regex
            or args.proc_iregex
            or args.patterns
        )
    except Exception:
        has_match = False

    if not has_match:
        argv = ["-m", "agy"] + argv

    return pwatch.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
