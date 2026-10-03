from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agent_workflows.command_surface import get_declaration
from agent_workflows.run_ledger_schema import ATTEMPT_STATES
from agent_workflows.run_ledger_store import RunLedgerStore, SchemaInvalidRecordError
from agent_workflows.run_state import STATE_RUNNING
from agent_workflows.run_viewer import RUNS_VIEWER_LEAF_NAMES


def _create_valid_one_record_ledger(ledger_path: Path) -> None:
    store = RunLedgerStore(ledger_path)
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


def test_runs_viewer_leaf_names_declared_read_or_check() -> None:
    """Every name in RUNS_VIEWER_LEAF_NAMES with a declaration must be read or check."""
    for leaf in RUNS_VIEWER_LEAF_NAMES:
        decl = get_declaration(f"runs {leaf}")
        if decl is not None:
            assert (
                decl.command_class in ("read", "check")
            ), f"runs {leaf} declared as {decl.command_class}, expected 'read' or 'check'"


def test_runs_resume_handler_purity(tmp_path: Path) -> None:
    """Behavioral proof of handler purity: ledger bytes and files are unchanged after runs resume."""
    ledger_path = tmp_path / "ledger.jsonl"
    _create_valid_one_record_ledger(ledger_path)

    before_bytes = ledger_path.read_bytes()
    before_sha256 = hashlib.sha256(before_bytes).hexdigest()
    before_files = sorted(os.listdir(tmp_path))
    before_record_count = len(
        [line for line in before_bytes.splitlines() if line.strip()]
    )

    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "resume", str(ledger_path)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0

    after_bytes = ledger_path.read_bytes()
    after_sha256 = hashlib.sha256(after_bytes).hexdigest()
    after_files = sorted(os.listdir(tmp_path))
    after_record_count = len(
        [line for line in after_bytes.splitlines() if line.strip()]
    )

    assert before_bytes == after_bytes
    assert before_sha256 == after_sha256
    assert before_record_count == after_record_count
    assert before_files == after_files


def test_runs_resume_declared_exit_codes_are_reachable(tmp_path: Path) -> None:
    """Drive the real CLI in a subprocess for each of 0, 2, 5, 7 and verify it is in decl.exit_contract."""
    decl = get_declaration("runs resume")
    assert decl is not None

    # Code 0: clean one-record valid ledger
    clean_ledger = tmp_path / "clean_ledger.jsonl"
    _create_valid_one_record_ledger(clean_ledger)
    res_0 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "resume", str(clean_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_0.returncode == 0
    assert 0 in decl.exit_contract

    # Code 2: absent path, empty file, bad flag
    res_2_absent = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            "resume",
            str(tmp_path / "nonexistent.jsonl"),
        ],
        capture_output=True,
        text=True,
    )
    assert res_2_absent.returncode == 2
    assert 2 in decl.exit_contract

    empty_ledger = tmp_path / "empty_ledger.jsonl"
    empty_ledger.touch()
    res_2_empty = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "resume", str(empty_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_2_empty.returncode == 2

    res_2_badflag = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            "resume",
            "--this-flag-does-not-exist",
        ],
        capture_output=True,
        text=True,
    )
    assert res_2_badflag.returncode == 2

    # Code 5: chain-broken two-record ledger
    broken_ledger = tmp_path / "broken_ledger.jsonl"
    store_5 = RunLedgerStore(broken_ledger)
    store_5.append(
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
    store_5.append(
        {
            "schema_version": 1,
            "kind": "step_attempt",
            "run_id": "run-0000abcd",
            "parent": "",
            "step": "s1",
            "attempt": 1,
            "actor": "runtime",
            "state": "performed",
            "input_digest": "sha256:" + "0" * 64,
        }
    )
    lines_5 = broken_ledger.read_bytes().decode("utf-8").splitlines()
    data_5 = json.loads(lines_5[1])
    data_5["prev_hash"] = "0" * 64
    lines_5[1] = json.dumps(data_5)
    broken_ledger.write_bytes(("\n".join(lines_5) + "\n").encode("utf-8"))

    res_5 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "resume", str(broken_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_5.returncode == 5
    assert 5 in decl.exit_contract

    # Code 7: healthy non-ledger JSONL
    non_ledger = tmp_path / "non_ledger.jsonl"
    non_ledger.write_bytes(b'{"hello": "world"}\n')
    res_7 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "resume", str(non_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_7.returncode == 7
    assert 7 in decl.exit_contract


def test_runs_resume_exit_3_is_unreachable_and_undeclared(tmp_path: Path) -> None:
    """Exit 3 is absent from exit_contract, and mechanically unreachable."""
    decl = get_declaration("runs resume")
    assert decl is not None
    assert (
        3 not in decl.exit_contract
    ), f"exit code 3 must not be in exit_contract: {decl.exit_contract}"

    # (i) Data comparison over runtime constants
    assert STATE_RUNNING not in ATTEMPT_STATES

    # (ii) Exercising the schema refusal RL-E030
    ledger_path = tmp_path / "ledger_unreachable.jsonl"
    store = RunLedgerStore(ledger_path)
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
    with pytest.raises(SchemaInvalidRecordError) as exc_info:
        store.append(
            {
                "schema_version": 1,
                "kind": "step_attempt",
                "run_id": "run-0000abcd",
                "parent": "",
                "step": "s1",
                "attempt": 1,
                "actor": "runtime",
                "state": "running",
                "input_digest": "sha256:" + "0" * 64,
            }
        )
    findings = exc_info.value.findings
    assert any(f.code == "RL-E030" for f in findings)


def _create_terminal_ledger(
    ledger_path: Path, terminal_status: str, moved_to: str
) -> None:
    _create_valid_one_record_ledger(ledger_path)
    store = RunLedgerStore(ledger_path)
    store.append(
        {
            "schema_version": 1,
            "kind": "terminal_transaction",
            "run_id": "run-0000abcd",
            "parent": "",
            "actor": "coordinator",
            "terminal_status": terminal_status,
            "moved_to": moved_to,
        }
    )


def _create_corrupted_ledger(ledger_path: Path) -> None:
    _create_valid_one_record_ledger(ledger_path)
    store = RunLedgerStore(ledger_path)
    store.append(
        {
            "schema_version": 1,
            "kind": "step_attempt",
            "run_id": "run-0000abcd",
            "parent": "",
            "step": "s1",
            "attempt": 1,
            "actor": "runtime",
            "state": "performed",
            "input_digest": "sha256:" + "0" * 64,
        }
    )
    lines = ledger_path.read_bytes().decode("utf-8").splitlines()
    data = json.loads(lines[1])
    data["prev_hash"] = "0" * 64
    lines[1] = json.dumps(data)
    ledger_path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def test_runs_next_declared_exit_codes_are_reachable(tmp_path: Path) -> None:
    """Drive the real CLI in a subprocess for each of 0, 2, 3, 5, 7 and verify it is in decl.exit_contract."""
    decl = get_declaration("runs next")
    assert decl is not None

    # Code 0: terminal complete ledger
    term_complete = tmp_path / "term_complete.jsonl"
    _create_terminal_ledger(
        term_complete, terminal_status="complete", moved_to="executed"
    )
    res_0 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "next", str(term_complete)],
        capture_output=True,
        text=True,
    )
    assert res_0.returncode == 0
    assert 0 in decl.exit_contract

    # Code 2: absent path, empty file, bad flag
    res_2_absent = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            "next",
            str(tmp_path / "nonexistent.jsonl"),
        ],
        capture_output=True,
        text=True,
    )
    assert res_2_absent.returncode == 2
    assert 2 in decl.exit_contract

    empty_ledger = tmp_path / "empty_ledger.jsonl"
    empty_ledger.touch()
    res_2_empty = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "next", str(empty_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_2_empty.returncode == 2

    res_2_badflag = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            "next",
            "--this-flag-does-not-exist",
        ],
        capture_output=True,
        text=True,
    )
    assert res_2_badflag.returncode == 2

    # Code 3: clean one-record valid ledger (non-terminal, no runnable steps)
    clean_ledger = tmp_path / "clean_ledger.jsonl"
    _create_valid_one_record_ledger(clean_ledger)
    res_3 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "next", str(clean_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_3.returncode == 3
    assert 3 in decl.exit_contract

    # Code 5: chain-broken two-record ledger
    broken_ledger = tmp_path / "broken_ledger.jsonl"
    _create_corrupted_ledger(broken_ledger)
    res_5 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "next", str(broken_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_5.returncode == 5
    assert 5 in decl.exit_contract

    # Code 7: healthy non-ledger JSONL
    non_ledger = tmp_path / "non_ledger.jsonl"
    non_ledger.write_bytes(b'{"hello": "world"}\n')
    res_7 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "next", str(non_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_7.returncode == 7
    assert 7 in decl.exit_contract

    # Exact-set assertion in both directions
    measured_codes = {
        res_0.returncode,
        res_2_absent.returncode,
        res_3.returncode,
        res_5.returncode,
        res_7.returncode,
    }
    assert measured_codes == {0, 2, 3, 5, 7}
    assert set(decl.exit_contract) == measured_codes
    assert decl.exit_contract == (0, 2, 3, 5, 7)


def test_runs_status_declared_exit_codes_are_reachable(tmp_path: Path) -> None:
    """Drive the real CLI in a subprocess for each of 0, 1, 2, 3, 5, 7 and verify it is in decl.exit_contract."""
    decl = get_declaration("runs status")
    assert decl is not None

    # Code 0: terminal complete ledger
    term_complete = tmp_path / "term_complete.jsonl"
    _create_terminal_ledger(
        term_complete, terminal_status="complete", moved_to="executed"
    )
    res_0 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "status", str(term_complete)],
        capture_output=True,
        text=True,
    )
    assert res_0.returncode == 0
    assert 0 in decl.exit_contract

    # Code 1: clean one-record valid ledger (non-terminal, pending)
    clean_ledger = tmp_path / "clean_ledger.jsonl"
    _create_valid_one_record_ledger(clean_ledger)
    res_1 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "status", str(clean_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_1.returncode == 1
    assert 1 in decl.exit_contract

    # Code 2: absent path, empty file, bad flag
    res_2_absent = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            "status",
            str(tmp_path / "nonexistent.jsonl"),
        ],
        capture_output=True,
        text=True,
    )
    assert res_2_absent.returncode == 2
    assert 2 in decl.exit_contract

    empty_ledger = tmp_path / "empty_ledger.jsonl"
    empty_ledger.touch()
    res_2_empty = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "status", str(empty_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_2_empty.returncode == 2

    res_2_badflag = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            "status",
            "--this-flag-does-not-exist",
        ],
        capture_output=True,
        text=True,
    )
    assert res_2_badflag.returncode == 2

    # Code 3: terminal cancelled ledger
    term_cancelled = tmp_path / "term_cancelled.jsonl"
    _create_terminal_ledger(
        term_cancelled, terminal_status="cancelled", moved_to="not-executed"
    )
    res_3 = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            "status",
            str(term_cancelled),
        ],
        capture_output=True,
        text=True,
    )
    assert res_3.returncode == 3
    assert 3 in decl.exit_contract

    # Code 5: chain-broken two-record ledger
    broken_ledger = tmp_path / "broken_ledger.jsonl"
    _create_corrupted_ledger(broken_ledger)
    res_5 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "status", str(broken_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_5.returncode == 5
    assert 5 in decl.exit_contract

    # Code 7: healthy non-ledger JSONL
    non_ledger = tmp_path / "non_ledger.jsonl"
    non_ledger.write_bytes(b'{"hello": "world"}\n')
    res_7 = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "runs", "status", str(non_ledger)],
        capture_output=True,
        text=True,
    )
    assert res_7.returncode == 7
    assert 7 in decl.exit_contract

    # Exact-set assertion in both directions
    measured_codes = {
        res_0.returncode,
        res_1.returncode,
        res_2_absent.returncode,
        res_3.returncode,
        res_5.returncode,
        res_7.returncode,
    }
    assert measured_codes == {0, 1, 2, 3, 5, 7}
    assert set(decl.exit_contract) == measured_codes
    assert decl.exit_contract == (0, 1, 2, 3, 5, 7)
