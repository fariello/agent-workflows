"""Tests for agent_workflows.comms_acks: agent-side ack writing and status aggregation (IPD ozcfjr)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import pytest

from agent_workflows import comms
from agent_workflows import comms_acks


@pytest.fixture
def comms_env(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create a comms test directory with untracked/inbox and shared/inbox."""
    comms_dir = tmp_path / ".aw" / "records" / "comms"
    untracked_inbox = comms_dir / "untracked" / "inbox"
    shared_inbox = comms_dir / "shared" / "inbox"
    untracked_inbox.mkdir(parents=True, exist_ok=True)
    shared_inbox.mkdir(parents=True, exist_ok=True)
    return comms_dir, untracked_inbox, shared_inbox


def _create_message(inbox_dir: Path, msg_id: str) -> Path:
    """Create a minimal valid message file."""
    msg_path = inbox_dir / f"{msg_id}.md"
    content = (
        "From: test.sender\n"
        "To: target.agent\n"
        "Kind: task\n"
        "Status: queued\n"
        "---\n"
        "Hello payload"
    )
    msg_path.write_text(content, encoding="utf-8")
    return msg_path


# --- Task group 1 & E-01: write_agent_ack tests ------------------------------------------------


def test_write_agent_ack_broker_state_refused(
    comms_env: tuple[Path, Path, Path],
) -> None:
    """Agent cannot write a broker-authored state (e.g. 'delivered')."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)

    with pytest.raises(ValueError, match="not an agent ack state"):
        comms_acks.write_agent_ack(comms_dir, msg_id, "delivered", "target.agent")

    with pytest.raises(ValueError, match="not an agent ack state"):
        comms_acks.write_agent_ack(comms_dir, msg_id, "scheduled", "target.agent")


def test_write_agent_ack_unknown_msg_refused(
    comms_env: tuple[Path, Path, Path],
) -> None:
    """Refuse to write ack if message does not exist in inboxes or archive."""
    comms_dir, _, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-nonexistent"

    with pytest.raises(ValueError, match="not found in inboxes or archive"):
        comms_acks.write_agent_ack(comms_dir, msg_id, "read", "target.agent")


def test_write_agent_ack_unsafe_by_refused(comms_env: tuple[Path, Path, Path]) -> None:
    """Refuse unsafe agent identifier in 'by' parameter."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)

    with pytest.raises(ValueError, match="not filename-safe"):
        comms_acks.write_agent_ack(comms_dir, msg_id, "read", "../malicious.agent")

    with pytest.raises(ValueError, match="not filename-safe"):
        comms_acks.write_agent_ack(comms_dir, msg_id, "read", "bad/agent")


def test_write_agent_ack_unsafe_msg_id_refused(
    comms_env: tuple[Path, Path, Path],
) -> None:
    """Refuse unsafe msg_id."""
    comms_dir, _, _ = comms_env
    with pytest.raises(ValueError, match="not filename-safe"):
        comms_acks.write_agent_ack(
            comms_dir, "../traversal-msg", "read", "target.agent"
        )


def test_write_agent_ack_valid_read_written(comms_env: tuple[Path, Path, Path]) -> None:
    """Valid 'read' ack is written atomically, validates with comms.validate_ack, and has offset."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)

    fixed_now = datetime(2026, 9, 25, 14, 30, 0, tzinfo=timezone.utc)
    ack_path = comms_acks.write_agent_ack(
        comms_dir, msg_id, "read", "target.agent", now=fixed_now
    )

    assert ack_path.is_file()
    assert ack_path.name == f"{msg_id}.target.agent.read.json"

    with ack_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["re"] == msg_id
    assert data["state"] == "read"
    assert data["by"] == "target.agent"
    assert data["at"] == "2026-09-25T14:30:00+00:00"
    assert data["at"].endswith("+00:00") or data["at"].endswith("Z")

    problems = comms.validate_ack(data)
    assert problems == []


def test_write_agent_ack_idempotent(comms_env: tuple[Path, Path, Path]) -> None:
    """Subsequent identical ack write returns existing path and leaves file untouched."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)

    path1 = comms_acks.write_agent_ack(comms_dir, msg_id, "read", "target.agent")
    content1 = path1.read_text(encoding="utf-8")

    path2 = comms_acks.write_agent_ack(comms_dir, msg_id, "read", "target.agent")
    content2 = path2.read_text(encoding="utf-8")

    assert path1 == path2
    assert content1 == content2


def test_write_agent_ack_no_lane_creates_lane_and_has_offset(tmp_path: Path) -> None:
    """Fresh clone case (d): comms dir without untracked/ directory creates acks/ and writes offset."""
    comms_dir = tmp_path / "fresh-clone" / ".aw" / "records" / "comms"
    # Create only a shared inbox message
    shared_inbox = comms_dir / "shared" / "inbox"
    shared_inbox.mkdir(parents=True, exist_ok=True)
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-shared"
    _create_message(shared_inbox, msg_id)

    # Note untracked/ does not exist at all yet
    assert not (comms_dir / "untracked").exists()

    ack_path = comms_acks.write_agent_ack(comms_dir, msg_id, "read", "target.agent")

    assert ack_path.is_file()
    assert (comms_dir / "untracked" / "acks").is_dir()

    with ack_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Assert at carries an offset
    assert "+" in data["at"] or data["at"].endswith("Z")
    assert comms.validate_ack(data) == []


# --- Task group 1 & E-02: message_status tests -------------------------------------------------


def test_message_status_no_broker_delivery_none(
    comms_env: tuple[Path, Path, Path],
) -> None:
    """With no broker acks, delivery is None and unread is False."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)

    st = comms_acks.message_status(comms_dir, msg_id)
    assert st["msg_id"] == msg_id
    assert st["delivery"] is None
    assert st["work"] is None
    assert st["unread"] is False
    assert st["acks"] == []


def test_message_status_unread_after_delivered_and_cleared_after_read(
    comms_env: tuple[Path, Path, Path],
) -> None:
    """unread is True after delivered and False after read."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)

    # Broker writes delivered
    acks_dir = comms_dir / "untracked" / "acks"
    acks_dir.mkdir(parents=True, exist_ok=True)
    delivered_ack = {
        "re": msg_id,
        "state": "delivered",
        "by": "aw.comms-broker",
        "at": "2026-09-25T12:00:00+00:00",
    }
    (acks_dir / comms.ack_filename(msg_id, "aw.comms-broker", "delivered")).write_text(
        json.dumps(delivered_ack), encoding="utf-8"
    )

    st1 = comms_acks.message_status(comms_dir, msg_id)
    assert st1["delivery"] == delivered_ack
    assert st1["work"] is None
    assert st1["unread"] is True

    # Target agent writes read
    comms_acks.write_agent_ack(comms_dir, msg_id, "read", "target.agent")

    st2 = comms_acks.message_status(comms_dir, msg_id)
    assert st2["delivery"] == delivered_ack
    assert st2["work"] is not None
    assert st2["work"]["state"] == "read"
    assert st2["unread"] is False


def test_message_status_invalid_ack_reported_not_counted(
    comms_env: tuple[Path, Path, Path],
) -> None:
    """Invalid ack files are reported in acks with problem and never counted."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)

    acks_dir = comms_dir / "untracked" / "acks"
    acks_dir.mkdir(parents=True, exist_ok=True)

    # Hand-plant an invalid ack file (invalid state)
    invalid_ack = {
        "re": msg_id,
        "state": "bogus-state",
        "by": "target.agent",
        "at": "2026-09-25T12:00:00+00:00",
    }
    (acks_dir / f"{msg_id}.target.agent.bogus.json").write_text(
        json.dumps(invalid_ack), encoding="utf-8"
    )

    # Hand-plant a corrupt JSON file
    (acks_dir / f"{msg_id}.target.agent.corrupt.json").write_text(
        "INVALID JSON CONTENT {{{", encoding="utf-8"
    )

    st = comms_acks.message_status(comms_dir, msg_id)
    assert st["delivery"] is None
    assert st["work"] is None
    assert st["unread"] is False

    # Check reported problems
    problems = [a for a in st["acks"] if "problem" in a]
    assert len(problems) == 2
    assert any("not in the closed enum" in p["problem"] for p in problems)
    assert any("unparseable JSON" in p["problem"] for p in problems)


def test_message_status_mixed_offset(comms_env: tuple[Path, Path, Path]) -> None:
    """Case (a): mixed-offset at values ('...Z' and offset-naive) compare without TypeError."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)

    acks_dir = comms_dir / "untracked" / "acks"
    acks_dir.mkdir(parents=True, exist_ok=True)

    # Earlier ack with Z offset
    ack1 = {
        "re": msg_id,
        "state": "read",
        "by": "target.agent",
        "at": "2026-09-24T10:00:00Z",
    }
    # Later ack with offset-naive datetime
    ack2 = {
        "re": msg_id,
        "state": "in-progress",
        "by": "target.agent",
        "at": "2026-09-24T11:00:00",
    }

    assert comms.validate_ack(ack1) == []
    assert comms.validate_ack(ack2) == []

    (acks_dir / comms.ack_filename(msg_id, "target.agent", "read")).write_text(
        json.dumps(ack1), encoding="utf-8"
    )
    (acks_dir / comms.ack_filename(msg_id, "target.agent", "in-progress")).write_text(
        json.dumps(ack2), encoding="utf-8"
    )

    st = comms_acks.message_status(comms_dir, msg_id)
    assert st["work"] is not None
    assert st["work"]["state"] == "in-progress"


def test_message_status_dot_bearing_msg_id(comms_env: tuple[Path, Path, Path]) -> None:
    """Case (b): dot-bearing msg-id is correctly selected by the re field."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260924-1200-01-a.b--to--c.d-ask-x"
    _create_message(untracked_inbox, msg_id)

    comms_acks.write_agent_ack(comms_dir, msg_id, "read", "c.d")

    st = comms_acks.message_status(comms_dir, msg_id)
    assert st["msg_id"] == msg_id
    assert st["work"] is not None
    assert st["work"]["state"] == "read"
    assert st["work"]["by"] == "c.d"


def test_message_status_glob_metachar_msg_id(
    comms_env: tuple[Path, Path, Path],
) -> None:
    """Case (c): msg-id with glob metacharacters ('[') is selected without glob matching errors."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260924-1200-01-a[b--to--c.d-ask-x"
    assert comms.is_filename_safe(msg_id)
    _create_message(untracked_inbox, msg_id)

    comms_acks.write_agent_ack(comms_dir, msg_id, "read", "c.d")

    st = comms_acks.message_status(comms_dir, msg_id)
    assert st["msg_id"] == msg_id
    assert st["work"] is not None
    assert st["work"]["state"] == "read"


def test_message_status_no_lane_at_all(tmp_path: Path) -> None:
    """Case (d): against a comms dir with no untracked/ subdirectory, message_status returns cleanly."""
    comms_dir = tmp_path / ".aw" / "records" / "comms"
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"

    st = comms_acks.message_status(comms_dir, msg_id)
    assert st["delivery"] is None
    assert st["work"] is None
    assert st["unread"] is False
    assert st["acks"] == []


def test_message_status_not_done_clears_unread(
    comms_env: tuple[Path, Path, Path],
) -> None:
    """Case (e): unread is False after ANY agent ack including 'not-done'."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)

    # Broker delivered
    acks_dir = comms_dir / "untracked" / "acks"
    acks_dir.mkdir(parents=True, exist_ok=True)
    delivered_ack = {
        "re": msg_id,
        "state": "delivered",
        "by": "aw.comms-broker",
        "at": "2026-09-25T12:00:00+00:00",
    }
    (acks_dir / comms.ack_filename(msg_id, "aw.comms-broker", "delivered")).write_text(
        json.dumps(delivered_ack), encoding="utf-8"
    )

    st1 = comms_acks.message_status(comms_dir, msg_id)
    assert st1["unread"] is True

    # Agent writes not-done
    comms_acks.write_agent_ack(comms_dir, msg_id, "not-done", "target.agent")

    st2 = comms_acks.message_status(comms_dir, msg_id)
    assert st2["work"] is not None
    assert st2["work"]["state"] == "not-done"
    assert st2["unread"] is False


# --- Task group 1 & E-03: CLI tests -------------------------------------------------------------


def test_cli_help() -> None:
    """CLI --help prints help and exits 0."""
    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows.comms_acks", "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "subcommand" in res.stdout
    assert "ack" in res.stdout
    assert "status" in res.stdout


def test_cli_ack_refusal_exit_2(tmp_path: Path) -> None:
    """CLI ack with broker state 'delivered' exits 2 with acks dir absent or empty."""
    comms_dir = tmp_path / ".aw" / "records" / "comms"
    acks_dir = comms_dir / "untracked" / "acks"

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.comms_acks",
            "ack",
            "any-msg",
            "delivered",
            "--by",
            "target.agent",
            "--comms-dir",
            str(comms_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    assert "not an agent ack state" in res.stderr
    assert not acks_dir.exists() or len(list(acks_dir.iterdir())) == 0


def test_cli_ack_success(comms_env: tuple[Path, Path, Path]) -> None:
    """CLI ack with valid agent state writes ack and exits 0."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.comms_acks",
            "ack",
            msg_id,
            "read",
            "--by",
            "target.agent",
            "--comms-dir",
            str(comms_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    ack_file = comms_dir / "untracked" / "acks" / f"{msg_id}.target.agent.read.json"
    assert ack_file.is_file()


def test_cli_status_no_untracked_lane_exits_0(tmp_path: Path) -> None:
    """CLI status in a repo with no untracked/ lane exits 0."""
    comms_dir = tmp_path / ".aw" / "records" / "comms"
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.comms_acks",
            "status",
            "--comms-dir",
            str(comms_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "[]" in res.stdout


def test_cli_status_json_format(comms_env: tuple[Path, Path, Path]) -> None:
    """CLI status --format json emits valid JSON."""
    comms_dir, untracked_inbox, _ = comms_env
    msg_id = "20260925-1000-01-sender.agent--to--target.agent-task-01"
    _create_message(untracked_inbox, msg_id)
    comms_acks.write_agent_ack(comms_dir, msg_id, "read", "target.agent")

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.comms_acks",
            "status",
            msg_id,
            "--format",
            "json",
            "--comms-dir",
            str(comms_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["msg_id"] == msg_id
    assert data["work"]["state"] == "read"
