"""Tests verifying that coverage_record and proposal-fallback history writers use the UTC clock.

Spec 2vev8j Section 4.4 ("One timezone for every writer") requires:
"Every writer, tool and human-facing helper alike, records UTC; local time is a
RENDER-TIME concern only."

DECISIONS.md D55 ("Human-facing timestamps use LOCAL time, not UTC") rules filename
prefixes local while history records remain UTC.

IPD 8chbn9 E-02:
Parameterized tests over Pacific/Kiritimati (UTC+14) and Pacific/Honolulu (UTC-10)
verifying that coverage_record.write and runner proposal fallback stamp UTC dates.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import tempfile

import pytest

ZONES = ["Pacific/Kiritimati", "Pacific/Honolulu"]
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _child_env(zone: str, *, drop_execution_role: bool = False) -> dict[str, str]:
    env = dict(os.environ)
    env["TZ"] = zone
    env["AW_NO_REEXEC"] = "1"
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{REPO_ROOT}:{existing_pp}" if existing_pp else str(REPO_ROOT)
    if drop_execution_role:
        env.pop("AW_EXECUTION_ROLE", None)
    return env


def _probe_zone(zone: str) -> tuple[str, str, str]:
    """Run a tiny child under zone and return (local_date, utc_date, package_path)."""
    code = """
import datetime, agent_workflows
local_d = datetime.date.today().isoformat()
utc_d = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
print(f"{local_d},{utc_d},{agent_workflows.__file__}")
"""
    env = _child_env(zone)
    res = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    parts = res.stdout.strip().split(",")
    return parts[0], parts[1], parts[2]


def _check_and_select_skew(target_zone: str) -> None:
    """Probe both zones, assert exactly one is in skew, and skip target_zone if not in skew."""
    import time

    if not hasattr(time, "tzset"):
        pytest.skip("POSIX TZ/tzset required to shift datetime.date.today()")
    probes = {z: _probe_zone(z) for z in ZONES}
    skews = {z: probes[z][0] != probes[z][1] for z in ZONES}
    skewed_count = sum(1 for s in skews.values() if s)
    assert (
        skewed_count == 1
    ), f"Expected exactly one zone in skew, got skews: {skews} (probes: {probes})"
    if not skews[target_zone]:
        local_d, utc_d, _ = probes[target_zone]
        pytest.skip(
            f"{target_zone} is not in skew at this hour (local date {local_d} == UTC date {utc_d})"
        )


@pytest.mark.parametrize("zone", ZONES)
def test_coverage_record_write_records_utc_date(zone: str) -> None:
    """coverage_record.write stamps UTC date in - Coverage-Checked: and workflow history."""
    _check_and_select_skew(zone)

    with tempfile.TemporaryDirectory() as td:
        plan_path = pathlib.Path(td) / "test.ipd.md"
        plan_path.write_text(
            "# IPD: Test\n\n"
            "- Status: approved\n"
            "- Readiness: go\n\n"
            "## Workflow history\n"
            "- 2026-10-01 draft: init\n\n"
            "## Validation and cross-check\n",
            encoding="utf-8",
        )

        child_code = f"""
import datetime, pathlib, agent_workflows
from agent_workflows import coverage_record

p = pathlib.Path({str(plan_path)!r})
now_utc = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
now_local = datetime.date.today().isoformat()
pkg = agent_workflows.__file__
print(f"child: utc={{now_utc}} local={{now_local}} pkg={{pkg}}")

res = coverage_record.write(p, "pass", (), model="m", tool="aw oc run")
content = p.read_text(encoding="utf-8")
print("---FILE-CONTENT---")
print(content)
"""

        env = _child_env(zone)
        res = subprocess.run(
            [sys.executable, "-c", child_code],
            cwd=td,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )

        stdout = res.stdout
        header_match = re.search(
            r"child:\s+utc=(\S+)\s+local=(\S+)\s+pkg=(\S+)", stdout
        )
        assert header_match, f"Malformed child header: {stdout}"
        child_utc, child_local, child_pkg = header_match.groups()

        # Confirm child imported this worktree's code
        assert (
            str(REPO_ROOT) in child_pkg
        ), f"Child imported unexpected package {child_pkg}, expected {REPO_ROOT}"
        # Skew is observable
        assert (
            child_local != child_utc
        ), f"Expected observable skew for {zone}, got local={child_local} utc={child_utc}"

        file_content = stdout.split("---FILE-CONTENT---\n", 1)[1]

        chk_match = re.search(
            r"^-\s*Coverage-Checked:\s*(\S+)", file_content, re.MULTILINE
        )
        assert chk_match, f"Coverage-Checked line not found in:\n{file_content}"
        checked_date = chk_match.group(1)

        hist_match = re.search(
            r"^-\s*(\S+)\s+coverage\s+pass\s+\(aw oc run\):", file_content, re.MULTILINE
        )
        assert hist_match, f"Coverage history line not found in:\n{file_content}"
        hist_date = hist_match.group(1)

        assert (
            checked_date == child_utc
        ), f"Coverage-Checked date {checked_date} did not match UTC date {child_utc} (local was {child_local})"
        assert (
            hist_date == child_utc
        ), f"Coverage workflow history date {hist_date} did not match UTC date {child_utc} (local was {child_local})"


@pytest.mark.parametrize("zone", ZONES)
def test_proposal_fallback_record_records_utc_date(zone: str) -> None:
    """runner_shared fallback proposal record stamps UTC date in created history line."""
    _check_and_select_skew(zone)

    with tempfile.TemporaryDirectory() as td:
        child_code = f"""
import contextlib, datetime, pathlib, subprocess
from unittest import mock
import agent_workflows
from agent_workflows import runner_shared

repo = pathlib.Path({str(td)!r})
subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=repo, check=True)
subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)

run_dir = repo / ".aw" / "records" / "runs" / "run-locked"
run_dir.mkdir(parents=True, exist_ok=True)

proposal = {{
    "kind": "tool-defect",
    "blocked_by": "lock error",
    "why": "lock timeout test",
    "proposed_change": "fix tool",
    "paths": ["test.py"],
    "size": "material",
}}
item = {{"id6": "fb0001"}}
state = {{"repo": str(repo), "run_id": "run-locked"}}

now_utc = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
now_local = datetime.date.today().isoformat()
pkg = agent_workflows.__file__
print(f"child: utc={{now_utc}} local={{now_local}} pkg={{pkg}}")

@contextlib.contextmanager
def fake_lock(*a, **k):
    yield runner_shared.IntegrationLockOutcome(
        acquired=False,
        handle=None,
        waited_seconds=5.0,
        holder="peer-agent",
        detail="held",
    )

with mock.patch("agent_workflows.runner_shared.integration_lock", side_effect=fake_lock):
    res = runner_shared.perform_coordinator_proposal_file(
        run_dir=run_dir,
        state=state,
        item=item,
        proposal=proposal,
        timeout=0.01,
    )

props = list((run_dir / "proposals").glob("*proposal.backlog.md"))
if not props:
    print("NO_PROPOSALS_FOUND")
else:
    print("---PROPOSAL-CONTENT---")
    print(props[0].read_text(encoding="utf-8"))
"""

        env = _child_env(zone, drop_execution_role=True)
        res = subprocess.run(
            [sys.executable, "-c", child_code],
            cwd=td,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )

        stdout = res.stdout
        header_match = re.search(
            r"child:\s+utc=(\S+)\s+local=(\S+)\s+pkg=(\S+)", stdout
        )
        assert header_match, f"Malformed child header: {stdout}"
        child_utc, child_local, child_pkg = header_match.groups()

        # Confirm child imported this worktree's code
        assert (
            str(REPO_ROOT) in child_pkg
        ), f"Child imported unexpected package {child_pkg}, expected {REPO_ROOT}"
        # Skew is observable
        assert (
            child_local != child_utc
        ), f"Expected observable skew for {zone}, got local={child_local} utc={child_utc}"

        assert (
            "---PROPOSAL-CONTENT---\n" in stdout
        ), f"No proposal content in:\n{stdout}"
        file_content = stdout.split("---PROPOSAL-CONTENT---\n", 1)[1]

        hist_match = re.search(
            r"^-\s*(\S+)\s+created\s+\(proposal fallback\):", file_content, re.MULTILINE
        )
        assert (
            hist_match
        ), f"Proposal fallback history line not found in:\n{file_content}"
        hist_date = hist_match.group(1)

        assert (
            hist_date == child_utc
        ), f"Proposal fallback history date {hist_date} did not match UTC date {child_utc} (local was {child_local})"
