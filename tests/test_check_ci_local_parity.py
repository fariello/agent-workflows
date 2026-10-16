"""Behavioral tests for CI vs local aw check invocation parity (IPD 96qxfz, backlog crk6wb).

CHARTER AND PURPOSE:
Guards that a CI-shaped `aw check` invocation (cwd is the repository root, CI and GITHUB_ACTIONS
environment variables set, no `--dir` argument) and a local `aw check` invocation (cwd is an
external directory, `--dir <repo>` specified, CI and GITHUB_ACTIONS unset) over the same tree
yield identical findings `(rule, location)` and the same exit code. Covers the four artifact types
gated by the CI attention-check workflow job: plans, releases, backlog, and release-gates.

SENSITIVITY AND VALIDATION MUTATIONS (proven in E-04):
1. CI-dependent finding drop: dropping the first finding in `check_type` when `CI` is set breaks
   all four seeded parity tests.
2. Cwd-dependent location perturbation: replacing `location` with an absolute path when
   `cwd == repo_root` breaks all four seeded parity tests and the clean-tree tests that emit findings.

EXPLICIT BOUND OF THIS MODULE:
This module covers observable black-box outcomes of CLI invocations across invocation shapes.
In accordance with P16, it drives the CLI via subprocesses and asserts observable findings and
exit codes; it never inspects source code or workflow YAML text.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Iterator

import pytest

from tests import support


@contextlib.contextmanager
def temp_repo() -> Iterator[Path]:
    """Build a temporary git repository using tests.support.init_repo."""
    with tempfile.TemporaryDirectory() as td:
        repo = support.init_repo(Path(td))
        yield repo


def _parse_agent_diagnostics(stdout: str) -> list[tuple[str, str]]:
    """Parse (rule, location) finding pairs from the last aw.agent/v1 JSON line of stdout."""
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict) and payload.get("schema") == "aw.agent/v1":
            diagnostics = payload.get("diagnostics", [])
            return sorted({(d["rule"], d["location"]) for d in diagnostics})
    raise AssertionError(f"No aw.agent/v1 record found in stdout:\n{stdout}")


def _run(repo: Path, rtype: str, shape: str) -> tuple[int, list[tuple[str, str]]]:
    """Run `check <rtype> --agent` in either the CI or local invocation shape.

    CI shape: cwd=repo, env with CI=true and GITHUB_ACTIONS=true, no --dir.
    Local shape: cwd=REPO_ROOT, --dir <repo>, env with CI and GITHUB_ACTIONS removed.

    Both shapes route through tests.support.run_cli, which prepends this checkout
    to PYTHONPATH via support.pinned_env so both shapes resolve the package from this tree.
    """
    if shape == "ci":
        ci_env = dict(os.environ)
        ci_env["CI"] = "true"
        ci_env["GITHUB_ACTIONS"] = "true"
        res = support.run_cli("check", rtype, "--agent", cwd=repo, env=ci_env)
    elif shape == "local":
        local_env = dict(os.environ)
        local_env.pop("CI", None)
        local_env.pop("GITHUB_ACTIONS", None)
        res = support.run_cli(
            "check",
            rtype,
            "--agent",
            "--dir",
            str(repo),
            cwd=support.REPO_ROOT,
            env=local_env,
        )
    else:
        raise ValueError(f"Unknown shape: {shape!r}")

    findings = _parse_agent_diagnostics(res.stdout)
    return res.returncode, findings


def _seed_plans(repo: Path) -> str:
    p = repo / ".aw" / "records" / "plans" / "pending"
    p.mkdir(parents=True, exist_ok=True)
    (p / "badname.ipd.md").write_text(
        "# IPD: bad\n- Id: bad001\n- Status: draft\n\n## Goal\ng\n",
        encoding="utf-8",
    )
    return "check.name-nonconformant"


def _seed_releases(repo: Path) -> str:
    p = repo / ".aw" / "records" / "releases"
    p.mkdir(parents=True, exist_ok=True)
    (p / "bad.release.md").write_text(
        "# Release: bad\n- Id: bad\n",
        encoding="utf-8",
    )
    return "check.name-nonconformant"


def _seed_backlog(repo: Path) -> str:
    p = repo / ".aw" / "records" / "backlog" / "open"
    p.mkdir(parents=True, exist_ok=True)
    (p / "bad.backlog.md").write_text(
        "# Backlog: bad\n- Id: bad\n",
        encoding="utf-8",
    )
    return "check.name-nonconformant"


def _seed_release_gates(repo: Path) -> str:
    p = repo / ".aw" / "records" / "backlog" / "open"
    p.mkdir(parents=True, exist_ok=True)
    (p / "20261014-zprobe-01-zprobe-probe-item.backlog.md").write_text(
        "# Backlog: probe item\n"
        "- Id: zprobe\n"
        "- Status: open\n"
        "- Set: zprobe\n"
        "- Priority: low\n"
        "- Work-Kind: chore\n"
        "- Summary: probe item\n"
        "- Blocks-Release: zzzzzz\n\n"
        "## Workflow history\n"
        "- 2026-10-14 open\n",
        encoding="utf-8",
    )
    return "check.blocks-release-dangling"


SEEDED_CASES = [
    ("plans", _seed_plans),
    ("releases", _seed_releases),
    ("backlog", _seed_backlog),
    ("release-gates", _seed_release_gates),
]


@pytest.mark.parametrize("rtype,seeder", SEEDED_CASES, ids=[c[0] for c in SEEDED_CASES])
def test_seeded_violation_parity(rtype: str, seeder):
    """Assert CI and local shapes produce identical findings and exit 1 on seeded violations."""
    with temp_repo() as repo:
        expected_rule = seeder(repo)
        rc_ci, findings_ci = _run(repo, rtype, "ci")
        rc_local, findings_local = _run(repo, rtype, "local")

        # Equal exit codes and equal finding sets
        assert rc_ci == rc_local, f"Exit code mismatch: CI={rc_ci}, local={rc_local}"
        assert (
            findings_ci == findings_local
        ), f"Findings mismatch: CI={findings_ci}, local={findings_local}"

        # Fail-closed exit on seeded violation
        assert rc_ci == 1, f"Expected exit code 1, got {rc_ci}"

        # Non-empty and contains the specific rule targeted by the seed
        assert len(findings_ci) > 0, "Expected non-empty findings set"
        assert any(
            rule == expected_rule for rule, _ in findings_ci
        ), f"Expected rule {expected_rule!r} in findings: {findings_ci}"


@pytest.mark.parametrize("rtype", ["plans", "releases", "backlog", "release-gates"])
def test_clean_tree_parity(rtype: str):
    """Assert CI and local shapes exit 0 and produce equal finding sets on a clean tree."""
    with temp_repo() as repo:
        (repo / ".aw" / "records").mkdir(parents=True, exist_ok=True)
        rc_ci, findings_ci = _run(repo, rtype, "ci")
        rc_local, findings_local = _run(repo, rtype, "local")

        assert (
            rc_ci == 0
        ), f"Expected exit code 0 for CI shape, got {rc_ci} (findings={findings_ci})"
        assert (
            rc_local == 0
        ), f"Expected exit code 0 for local shape, got {rc_local} (findings={findings_local})"
        assert (
            findings_ci == findings_local
        ), f"Findings mismatch: CI={findings_ci}, local={findings_local}"
