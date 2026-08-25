"""Root pytest conftest: guarantee the suite ALWAYS runs in parallel (-n auto).

The suite is large and IO/subprocess bound; running it serially costs multiples of
the wall time, so `-n auto` (pytest-xdist, one worker per CPU) is the default in
`[tool.pytest.ini_options] addopts` in pyproject.toml. That default hard-requires the
xdist plugin: without it, pytest aborts with `unrecognized arguments: -n` before any
test runs.

This guard makes that default self-healing: if `xdist` is not importable when pytest
starts, install `pytest-xdist` into the current interpreter and re-exec pytest so the
`-n auto` in addopts always has its plugin. The net effect is that EVERY pytest
invocation - `pytest`, `python -m pytest`, `make test`, or an agent shelling out raw -
runs in parallel, with no serial fallback and no manual `pip install '.[test]'` step.

This runs at conftest import time, which pytest performs during startup, before it
parses the ini `addopts` (so the `-n` option is registered by the time argument
parsing happens). It is a no-op on the common path where xdist is already installed.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys


def _ensure_xdist_then_reexec() -> None:
    # Already available: nothing to do (the overwhelmingly common path).
    if importlib.util.find_spec("xdist") is not None:
        return

    # Guard against an infinite re-exec loop if the install silently "succeeds" but
    # the plugin still is not importable (e.g. a broken environment).
    if os.environ.get("AW_XDIST_BOOTSTRAP") == "1":
        return
    os.environ["AW_XDIST_BOOTSTRAP"] = "1"

    sys.stderr.write(
        "conftest: pytest-xdist not found; installing it so the suite runs with -n auto...\n"
    )
    sys.stderr.flush()
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest-xdist>=3"],
            check=True,
        )
    except Exception as exc:  # pragma: no cover - environment-dependent
        sys.stderr.write(
            "conftest: could not auto-install pytest-xdist "
            f"({exc}); run `pip install pytest-xdist` (or `pip install '.[test]'`).\n"
        )
        sys.stderr.flush()
        return

    if importlib.util.find_spec("xdist") is None:  # pragma: no cover
        sys.stderr.write(
            "conftest: pytest-xdist still not importable after install; aborting re-exec.\n"
        )
        sys.stderr.flush()
        return

    # Re-exec the exact same pytest command now that the plugin is present, so the
    # `-n auto` in addopts is honored on this very run.
    os.execv(sys.executable, [sys.executable, "-m", "pytest", *sys.argv[1:]])


_ensure_xdist_then_reexec()
