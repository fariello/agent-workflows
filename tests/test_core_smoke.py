"""End-to-end subprocess smoke tests for the core tier (E-04).

These tests execute a bounded number of real subprocess invocations (at most 6)
to verify the CLI entrypoint, argument parsing, error envelopes, and basic
subcommand dispatch under real operating conditions.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

pytestmark = pytest.mark.core


def test_smoke_cli_version() -> None:
    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "--version"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert (
        "agent-workflows" in res.stdout
        or "agent_workflows" in res.stdout
        or res.stdout.strip()
    )


def test_smoke_cli_help() -> None:
    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "usage:" in res.stdout.lower()


def test_smoke_check_agent_envelope(tmp_path: Path) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "check", "--agent"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    data = json.loads(res.stdout)
    assert data.get("schema") == "aw.agent/v1"
    assert data.get("kind") == "error"


def test_smoke_host_capabilities_json() -> None:
    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "host", "capabilities", "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data.get("schema") == "aw.agent/v1"


def test_smoke_specs_check_help() -> None:
    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "specs", "check", "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "usage:" in res.stdout.lower()


def test_smoke_ipd_lint_help() -> None:
    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "ipd", "lint", "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "usage:" in res.stdout.lower()
