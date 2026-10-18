"""Behavioral tests for aw run and aw runs success payloads under --agent (IPD 2jzld4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pytest

from agent_workflows import (
    agent_schema,
    run_ledger_schema,
    run_ledger_store,
    runner_shared,
)
from tests.conformance_matrix import (
    LEDGER_FIXTURE_RUN_ID,
    live_leaf_argv,
    run_cli,
    seed_ledger_fixture,
)

READ_LEAF_LEGACY_KEYS: Dict[str, str] = {
    "runs show": "run_id",
    "runs status": "run_id",
    "runs next": "run_id",
    "runs resume": "run_id",
    "runs evidence": "ledger",
    "runs verify-ledger": "chain_clean",
    "runs decisions": "content",
    "runs questions": "content",
}


@pytest.fixture
def seeded_fixture(tmp_path: Path) -> Path:
    """Provide an isolated fixture directory initialized with a run ledger."""
    return seed_ledger_fixture(tmp_path)


@pytest.mark.parametrize("leaf,legacy_key", sorted(READ_LEAF_LEGACY_KEYS.items()))
def test_read_leaves_agent_success_records(
    leaf: str, legacy_key: str, seeded_fixture: Path
) -> None:
    """Read leaves under --agent emit valid aw.agent/v1 result records and keep legacy keys."""
    argv = [*live_leaf_argv(leaf, seeded_fixture), "--agent"]
    res = run_cli(argv, cwd=seeded_fixture)

    lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1, f"Expected 1 line, got {len(lines)}: {res.stdout}"

    rec = json.loads(lines[0])
    assert isinstance(rec, dict), f"Output must parse as dict: {lines[0]}"
    assert (
        agent_schema.validate_agent_record(rec) == []
    ), f"Invalid record: {agent_schema.validate_agent_record(rec)}"
    assert rec["kind"] == "result"
    assert rec["cmd"] == leaf
    assert rec["exit"] == res.returncode
    assert rec["outcome"] == ("ok" if res.returncode == 0 else "findings")
    assert legacy_key in rec, f"Expected legacy key {legacy_key!r} in {rec}"


@pytest.mark.parametrize("leaf", sorted(READ_LEAF_LEGACY_KEYS))
def test_read_leaves_agent_fields_filtering(leaf: str, seeded_fixture: Path) -> None:
    """Read leaves under --agent --fields cmd project strictly to preserved fields + cmd."""
    argv = [*live_leaf_argv(leaf, seeded_fixture), "--agent", "--fields", "cmd"]
    res = run_cli(argv, cwd=seeded_fixture)

    lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1, f"Expected 1 line, got {len(lines)}: {res.stdout}"

    rec = json.loads(lines[0])
    assert isinstance(rec, dict), f"Output must parse as dict: {lines[0]}"
    assert (
        agent_schema.validate_agent_record(rec) == []
    ), f"Invalid record: {agent_schema.validate_agent_record(rec)}"
    assert set(rec) <= (
        agent_schema._PRESERVED_FIELDS | {"cmd"}
    ), f"Unexpected fields in: {rec}"


def test_writer_leaves_agent_success_sequence(tmp_path: Path) -> None:
    """Writer leaves emit valid kind: "result" records with cmd "run <leaf>" and keep run_id."""
    fixture1 = tmp_path / "writer_seq"
    fixture1.mkdir(parents=True, exist_ok=True)
    seed_ledger_fixture(fixture1)

    # 1. run start
    res_start = run_cli(
        [
            "run",
            "start",
            LEDGER_FIXTURE_RUN_ID,
            "--step",
            "S-01",
            "--workflow",
            "wf.json",
            "--dir",
            str(fixture1),
            "--agent",
        ],
        cwd=fixture1,
    )
    assert res_start.returncode == 0, f"run start failed: {res_start.stderr}"
    lines_start = [ln.strip() for ln in res_start.stdout.splitlines() if ln.strip()]
    assert len(lines_start) == 1
    rec_start = json.loads(lines_start[0])
    assert agent_schema.validate_agent_record(rec_start) == []
    assert rec_start["kind"] == "result"
    assert rec_start["cmd"] == "run start"
    assert rec_start["run_id"] == LEDGER_FIXTURE_RUN_ID

    # 2. run record
    res_record = run_cli(
        [
            "run",
            "record",
            LEDGER_FIXTURE_RUN_ID,
            "--step",
            "S-01",
            "--state",
            "performed",
            "--workflow",
            "wf.json",
            "--dir",
            str(fixture1),
            "--agent",
        ],
        cwd=fixture1,
    )
    assert res_record.returncode == 0, f"run record failed: {res_record.stderr}"
    lines_record = [ln.strip() for ln in res_record.stdout.splitlines() if ln.strip()]
    assert len(lines_record) == 1
    rec_record = json.loads(lines_record[0])
    assert agent_schema.validate_agent_record(rec_record) == []
    assert rec_record["kind"] == "result"
    assert rec_record["cmd"] == "run record"
    assert rec_record["run_id"] == LEDGER_FIXTURE_RUN_ID

    # 3. run verify
    res_verify = run_cli(
        [
            "run",
            "verify",
            LEDGER_FIXTURE_RUN_ID,
            "--requirement",
            "R-01",
            "--result",
            "satisfied",
            "--dir",
            str(fixture1),
            "--agent",
        ],
        cwd=fixture1,
    )
    assert res_verify.returncode == 0, f"run verify failed: {res_verify.stderr}"
    lines_verify = [ln.strip() for ln in res_verify.stdout.splitlines() if ln.strip()]
    assert len(lines_verify) == 1
    rec_verify = json.loads(lines_verify[0])
    assert agent_schema.validate_agent_record(rec_verify) == []
    assert rec_verify["kind"] == "result"
    assert rec_verify["cmd"] == "run verify"
    assert rec_verify["run_id"] == LEDGER_FIXTURE_RUN_ID

    # 4. run finalize
    res_finalize = run_cli(
        [
            "run",
            "finalize",
            LEDGER_FIXTURE_RUN_ID,
            "--workflow",
            "wf.json",
            "--dir",
            str(fixture1),
            "--agent",
        ],
        cwd=fixture1,
    )
    assert res_finalize.returncode == 0, f"run finalize failed: {res_finalize.stderr}"
    lines_finalize = [
        ln.strip() for ln in res_finalize.stdout.splitlines() if ln.strip()
    ]
    assert len(lines_finalize) == 1
    rec_finalize = json.loads(lines_finalize[0])
    assert agent_schema.validate_agent_record(rec_finalize) == []
    assert rec_finalize["kind"] == "result"
    assert rec_finalize["cmd"] == "run finalize"
    assert rec_finalize["run_id"] == LEDGER_FIXTURE_RUN_ID

    # 5. run cancel on a second fresh fixture
    fixture2 = tmp_path / "writer_cancel"
    fixture2.mkdir(parents=True, exist_ok=True)
    seed_ledger_fixture(fixture2)

    res_cancel = run_cli(
        [
            "run",
            "cancel",
            LEDGER_FIXTURE_RUN_ID,
            "--reason",
            "testing",
            "--dir",
            str(fixture2),
            "--agent",
        ],
        cwd=fixture2,
    )
    assert res_cancel.returncode == 0, f"run cancel failed: {res_cancel.stderr}"
    lines_cancel = [ln.strip() for ln in res_cancel.stdout.splitlines() if ln.strip()]
    assert len(lines_cancel) == 1
    rec_cancel = json.loads(lines_cancel[0])
    assert agent_schema.validate_agent_record(rec_cancel) == []
    assert rec_cancel["kind"] == "result"
    assert rec_cancel["cmd"] == "run cancel"
    assert rec_cancel["run_id"] == LEDGER_FIXTURE_RUN_ID


def test_unchanged_shapes_and_exit_three(tmp_path: Path) -> None:
    """Verify unchanged shapes: --json is bare, and exit-3 payloads stay bare dicts."""
    fixture = seed_ledger_fixture(tmp_path)

    # 1. --json on runs status parses to dict with no "schema" key
    res_status_json = run_cli(
        [
            "runs",
            "status",
            LEDGER_FIXTURE_RUN_ID,
            "--workflow",
            "wf.json",
            "--dir",
            str(fixture),
            "--json",
        ],
        cwd=fixture,
    )
    data_json = json.loads(res_status_json.stdout.strip())
    assert isinstance(data_json, dict)
    assert "schema" not in data_json

    # 2. Start step S-01
    res_start = run_cli(
        [
            "run",
            "start",
            LEDGER_FIXTURE_RUN_ID,
            "--step",
            "S-01",
            "--workflow",
            "wf.json",
            "--dir",
            str(fixture),
            "--agent",
        ],
        cwd=fixture,
    )
    assert res_start.returncode == 0

    # runs next has no more runnable steps, so it exits 3 and emits bare dict
    res_next = run_cli(
        [
            "runs",
            "next",
            LEDGER_FIXTURE_RUN_ID,
            "--workflow",
            "wf.json",
            "--dir",
            str(fixture),
            "--agent",
        ],
        cwd=fixture,
    )
    assert res_next.returncode == 3
    data_next = json.loads(res_next.stdout.strip())
    assert isinstance(data_next, dict)
    assert "schema" not in data_next

    # 3. run record --state failed --agent exits 3 and emits bare dict
    res_rec_failed = run_cli(
        [
            "run",
            "record",
            LEDGER_FIXTURE_RUN_ID,
            "--step",
            "S-01",
            "--state",
            "failed",
            "--workflow",
            "wf.json",
            "--dir",
            str(fixture),
            "--agent",
        ],
        cwd=fixture,
    )
    assert res_rec_failed.returncode == 3
    data_failed = json.loads(res_rec_failed.stdout.strip())
    assert isinstance(data_failed, dict)
    assert "schema" not in data_failed


def test_redaction_in_agent_success_record(tmp_path: Path) -> None:
    """Home paths in payload values are redacted and ANSI stripped in agent result records."""
    fixture = seed_ledger_fixture(tmp_path)
    ledger_file = (
        runner_shared.state_root(fixture) / LEDGER_FIXTURE_RUN_ID / "ledger.jsonl"
    )
    ledger_store = run_ledger_store.RunLedgerStore(ledger_file)

    posix_home_path = "/".join(["", "home", "someuser", "work"])
    tool_rec = {
        "schema_version": run_ledger_schema.LEDGER_SCHEMA_VERSION,
        "kind": "tool_event",
        "run_id": LEDGER_FIXTURE_RUN_ID,
        "parent": "",
        "actor": "executor",
        "timestamp": "2026-10-17T20:00:00Z",
        "argv": ["pytest", "-v"],
        "cwd": posix_home_path,
        "exit_code": 0,
        "stdout_sha256": "e" * 64,
        "stderr_sha256": "0" * 64,
        "truncated": False,
    }
    ledger_store.append(tool_rec)

    res = run_cli(
        ["runs", "evidence", LEDGER_FIXTURE_RUN_ID, "--dir", str(fixture), "--agent"],
        cwd=fixture,
    )
    lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert (
        agent_schema.validate_agent_record(rec) == []
    ), f"Invalid record: {agent_schema.validate_agent_record(rec)}"
    assert (
        "someuser" not in res.stdout
    ), f"Found unredacted username in output: {res.stdout}"
    assert "~/work" in res.stdout, f"Expected redacted '~/work' in output: {res.stdout}"
