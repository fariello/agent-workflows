"""Behavioral tests for secret token redaction in run_cli human and machine output (omst3h)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from agent_workflows.run_ledger_store import RunLedgerStore


READ_LEAVES = [
    "show",
    "status",
    "next",
    "resume",
    "evidence",
    "verify-ledger",
]

PROJECTION_LEAVES = [
    "decisions",
    "questions",
]

WRITER_LEAVES = [
    "start",
    "record",
    "cancel",
    "finalize",
]


@pytest.mark.parametrize("leaf", READ_LEAVES)
def test_read_leaves_path_secret_redacted(tmp_path: Path, leaf: str) -> None:
    """E-02: Read leaves must redact secrets from missing target path in human output."""
    token = "ghp_" + "B" * 24
    missing_target = tmp_path / token

    res_human = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", leaf, str(missing_target)],
        capture_output=True,
        text=True,
    )
    res_agent = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            leaf,
            str(missing_target),
            "--agent",
        ],
        capture_output=True,
        text=True,
    )

    assert res_agent.returncode == 2
    assert res_human.returncode == res_agent.returncode

    out_human = res_human.stdout + res_human.stderr
    assert token not in out_human
    assert "[REDACTED]" in out_human


@pytest.mark.parametrize("leaf", PROJECTION_LEAVES)
@pytest.mark.parametrize("mode", ["human", "--agent"])
def test_projection_leaves_path_secret_redacted(leaf: str, mode: str) -> None:
    """E-02: Decisions and questions leaves must redact secrets in both human and --agent mode."""
    token = "ghp_" + "B" * 24
    cmd = [sys.executable, "-m", "agent_workflows", "runs", leaf, token]
    if mode == "--agent":
        cmd.append("--agent")

    res = subprocess.run(cmd, capture_output=True, text=True)

    assert res.returncode == 2

    out = res.stdout + res.stderr
    assert token not in out
    assert "[REDACTED]" in out


@pytest.mark.parametrize("leaf", WRITER_LEAVES)
def test_writer_leaves_path_secret_redacted(tmp_path: Path, leaf: str) -> None:
    """E-02: Writer leaves must redact secrets from missing ledger target in human mode."""
    token = "ghp_" + "B" * 24
    missing_target = tmp_path / token

    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "run", leaf, str(missing_target)],
        capture_output=True,
        text=True,
    )

    assert res.returncode == 2

    out = res.stdout + res.stderr
    assert token not in out
    assert "[REDACTED]" in out


def test_runs_evidence_ledger_content_secret_redacted(tmp_path: Path) -> None:
    """E-03: Ledger content containing Bearer and ghp tokens must be masked in human and agent output."""
    token = "ghp_" + "C" * 24
    ledger_file = tmp_path / "ledger.jsonl"
    store = RunLedgerStore(ledger_file)
    store.append(
        {
            "schema_version": 1,
            "kind": "run",
            "run_id": "run-0000abcd",
            "actor": "runtime",
            "parent": "",
            "workflow_digest": "sha256:" + "0" * 64,
            "requirement_digest": "sha256:" + "0" * 64,
            "repo": "test-repo",
            "head": "0000abcd",
        }
    )
    store.append(
        {
            "schema_version": 1,
            "kind": "tool_event",
            "run_id": "run-0000abcd",
            "actor": "runtime",
            "parent": "",
            "argv": ["curl", "-H", f"Authorization: Bearer {token}"],
            "cwd": "/tmp",
            "exit_code": 0,
            "stdout_sha256": "0" * 64,
        }
    )

    # Ensure token is genuinely written to disk unredacted
    assert token in ledger_file.read_text(encoding="utf-8")

    res_human = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "evidence", str(ledger_file)],
        capture_output=True,
        text=True,
    )
    res_agent = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            "evidence",
            str(ledger_file),
            "--agent",
        ],
        capture_output=True,
        text=True,
    )

    assert res_human.returncode == 0
    assert res_agent.returncode == 0

    out_human = res_human.stdout + res_human.stderr
    assert token not in out_human
    assert "[REDACTED]" in out_human

    out_agent = res_agent.stdout + res_agent.stderr
    assert token not in out_agent
    assert "[REDACTED]" in out_agent
