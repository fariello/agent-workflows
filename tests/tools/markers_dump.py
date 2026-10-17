"""Pytest plugin to dump test markers during collection."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.hookimpl
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Dump nodeid -> list of marker names to JSON file if AW_MARKERS_DUMP is set."""
    out_path = os.environ.get("AW_MARKERS_DUMP")
    if not out_path:
        return

    markers_by_nodeid: dict[str, list[str]] = {}
    for item in items:
        markers = [m.name for m in item.iter_markers()]
        markers_by_nodeid[item.nodeid] = markers

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(markers_by_nodeid, f, indent=2)
