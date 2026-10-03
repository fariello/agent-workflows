"""Tests for capture_command's output-text contract, CapturedToolEvent, and consumers.

toolevtext-01 (`emzbut`) E-05, E-06.
Validates the typed out-of-band attribute contract, key set consistency,
persistence safety against the ledger store, error paths, decode asymmetry,
and end-to-end consumer behavior.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import host_runner, run_evidence, run_ledger_schema, runner_shared
from agent_workflows.run_ledger_store import RunLedgerStore

BASE_SCHEMA_KEYS = frozenset(
    {
        "actor",
        "argv",
        "cwd",
        "end_time",
        "env",
        "exit_code",
        "kind",
        "parent",
        "run_id",
        "schema_version",
        "seq",
        "start_time",
        "stderr_len",
        "stderr_sha256",
        "stderr_truncated",
        "stdout_len",
        "stdout_sha256",
        "stdout_truncated",
        "timestamp",
        "truncated",
    }
)


def test_captured_tool_event_type_contract() -> None:
    """CapturedToolEvent is a dict subclass carrying stdout/stderr via __slots__."""
    initial_mapping = {"kind": "tool_event", "exit_code": 0, "run_id": "run-abc123ff"}
    event = run_evidence.CapturedToolEvent(
        initial_mapping,
        stdout="sample stdout text",
        stderr="sample stderr text",
    )

    # Subclass and mapping properties
    assert isinstance(event, dict)
    assert isinstance(event, run_evidence.CapturedToolEvent)
    assert event["kind"] == "tool_event"
    assert event.get("exit_code") == 0

    # Attribute reads
    assert event.stdout == "sample stdout text"
    assert event.stderr == "sample stderr text"

    # Attributes do not appear as mapping keys
    assert "stdout" not in event
    assert "stderr" not in event
    assert "stdout_excerpt" not in event
    assert "stderr_excerpt" not in event
    assert sorted(event.keys()) == sorted(initial_mapping.keys())

    # json.dumps and copy.deepcopy(dict(event)) see only mapping keys
    dumped = json.loads(json.dumps(event))
    assert "stdout" not in dumped
    assert "stderr" not in dumped
    assert dumped == initial_mapping

    copied = copy.deepcopy(dict(event))
    assert "stdout" not in copied
    assert "stderr" not in copied
    assert copied == initial_mapping

    # __slots__ is enforced (no __dict__ creation)
    with pytest.raises(AttributeError):
        event.undeclared_attribute = "forbidden"  # type: ignore[attr-defined]


def test_capture_command_producer_contract() -> None:
    """Real capture_command returns (CapturedToolEvent, envelope) with out-of-band text."""
    cmd = [
        sys.executable,
        "-c",
        "import sys; print('contract_stdout'); print('contract_stderr', file=sys.stderr)",
    ]
    tool_event, envelope = run_evidence.capture_command(
        "run-abc123ff",
        cmd,
        actor="executor",
    )

    assert isinstance(tool_event, run_evidence.CapturedToolEvent)
    assert tool_event.stdout == "contract_stdout\n"
    assert tool_event.stderr == "contract_stderr\n"

    # Mapping contains schema fields, none of the 4 text keys
    assert "stdout" not in tool_event
    assert "stderr" not in tool_event
    assert "stdout_excerpt" not in tool_event
    assert "stderr_excerpt" not in tool_event

    assert "stdout_sha256" in tool_event
    assert "stderr_sha256" in tool_event
    assert "stdout_len" in tool_event
    assert "stderr_len" in tool_event

    # Envelope receives digest from mapping
    assert envelope["stdout_sha256"] == tool_event["stdout_sha256"]


def test_capture_command_key_set_per_call_shape() -> None:
    """Emitted key set matches BASE_SCHEMA_KEYS for unbounded, and adds max_bytes for bounded."""
    cmd = [sys.executable, "-c", "pass"]

    # Unbounded call shape (e.g. used by run_worker_process)
    tool_event_unbounded, _ = run_evidence.capture_command("run-abc123ff", cmd)
    assert set(tool_event_unbounded.keys()) == BASE_SCHEMA_KEYS

    # Bounded call shape (e.g. used by run_suite_check with max_output_bytes=512_000)
    tool_event_bounded, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd,
        max_output_bytes=512_000,
    )
    assert set(tool_event_bounded.keys()) == BASE_SCHEMA_KEYS | {"max_bytes"}

    for key in ("stdout", "stderr", "stdout_excerpt", "stderr_excerpt"):
        assert key not in tool_event_unbounded
        assert key not in tool_event_bounded


def test_capture_command_persistence_clean_in_real_store() -> None:
    """Appending a CapturedToolEvent to a real RunLedgerStore writes no text keys."""
    large_cmd = [
        sys.executable,
        "-c",
        "import sys; sys.stdout.write('X' * 5000); sys.stderr.write('Y' * 500)",
    ]
    tool_event, _ = run_evidence.capture_command(
        "run-abc123ff",
        large_cmd,
        actor="executor",
    )

    # Validates schema clean
    val_res = run_ledger_schema.validate_record(tool_event)
    assert val_res.ok is True, f"Validation findings: {val_res.findings}"

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.jsonl"
        store = RunLedgerStore(ledger_path)

        # Seed fully-valid kind: "run" record
        seed = {
            "schema_version": 2,
            "kind": "run",
            "run_id": "run-abc123ff",
            "actor": "executor",
            "parent": "",
            "workflow_digest": "0" * 64,
            "requirement_digest": "1" * 64,
            "repo": "test-repo",
            "head": "a" * 40,
        }
        store.append(seed)
        store.append(tool_event)

        lines = ledger_path.read_text().splitlines()
        assert len(lines) == 2
        persisted_tool_event = json.loads(lines[1])

        # Assert no text keys in persisted JSONL line
        for text_key in ("stdout", "stderr", "stdout_excerpt", "stderr_excerpt"):
            assert text_key not in persisted_tool_event

        # Digest preserved
        assert persisted_tool_event["stdout_sha256"] == tool_event["stdout_sha256"]

        # Persisted line length is bounded (not containing the 5000-byte output)
        line_bytes_len = len(lines[1].encode("utf-8"))
        assert line_bytes_len < 2000, f"Persisted line length leaked: {line_bytes_len}"

        # In-memory object still holds the full output
        assert tool_event.stdout == "X" * 5000
        assert tool_event.stderr == "Y" * 500


def test_mock_shape_hazard_per_consumer() -> None:
    """A plain-dict mock fails loudly at run_worker_process and fails closed at run_suite_check."""
    packet = host_runner.TaskPacket(
        run_id="run-abc123ff",
        step_id="step-1",
        lane_id="lane-1",
        argv=[sys.executable, "-c", "pass"],
        cwd=".",
        timeout_seconds=30.0,
    )

    # (a) run_worker_process has no try/except, so AttributeError propagates
    with mock.patch(
        "agent_workflows.host_runner._ev.capture_command",
        return_value=({"exit_code": 0}, {}),
    ):
        with pytest.raises(AttributeError) as exc_info:
            host_runner.run_worker_process(packet)
        assert "'dict' object has no attribute 'stdout'" in str(exc_info.value)

    # (b) run_suite_check blind except catches AttributeError and fails closed
    with mock.patch(
        "agent_workflows.run_evidence.capture_command",
        return_value=({"exit_code": 0}, {}),
    ):
        res = runner_shared.run_suite_check(Path("."), "run-abc123ff")
        assert res.passing is False
        assert res.exit_code == 127
        assert "suite check could not run (fail-closed)" in res.reason
        assert "stdout" in res.reason


def test_capture_command_error_paths() -> None:
    """Exit 127 on nonexistent argv and 124 on timeout without raising."""
    # Nonexistent command -> exit 127 with error on stderr
    tool_event_127, _ = run_evidence.capture_command(
        "run-abc123ff",
        ["/nonexistent_binary_xyz987"],
    )
    assert tool_event_127.get("exit_code") == 127
    assert "No such file or directory" in tool_event_127.stderr

    # Timeout -> exit 124 with Command timed out on stderr
    tool_event_124, _ = run_evidence.capture_command(
        "run-abc123ff",
        [sys.executable, "-c", "import time; time.sleep(2)"],
        timeout=0.1,
    )
    assert tool_event_124.get("exit_code") == 124
    assert "Command timed out." in tool_event_124.stderr


def test_capture_command_decode_asymmetry() -> None:
    """Decoded characters and raw byte length/digest diverge correctly."""
    # Multi-byte UTF-8 character ('é' is 2 bytes in UTF-8: b'\xc3\xa9')
    multi_byte_cmd = [
        sys.executable,
        "-c",
        "import sys; sys.stdout.buffer.write('é'.encode('utf-8'))",
    ]
    ev_mb, _ = run_evidence.capture_command(
        "run-abc123ff",
        multi_byte_cmd,
        actor="executor",
    )
    assert ev_mb["stdout_len"] == 2
    assert len(ev_mb.stdout) == 1
    assert ev_mb.stdout == "é"
    assert ev_mb["stdout_len"] > len(ev_mb.stdout)

    # Invalid byte sequence (bytes([255, 254, 253])) decodes with replacement
    raw_invalid = bytes([255, 254, 253])
    invalid_byte_cmd = [
        sys.executable,
        "-c",
        "import sys; sys.stdout.buffer.write(bytes([255, 254, 253]))",
    ]
    ev_inv, _ = run_evidence.capture_command(
        "run-abc123ff",
        invalid_byte_cmd,
        actor="executor",
    )
    assert ev_inv.stdout == "\ufffd\ufffd\ufffd"
    assert ev_inv["stdout_sha256"] == hashlib.sha256(raw_invalid).hexdigest()
    assert ev_inv["stdout_len"] == len(raw_invalid)


def test_run_suite_check_consumer_contract() -> None:
    """run_suite_check reads attributes to recover real summary and failures."""
    # Passing suite execution: summary is non-empty, reason does not have 'no summary line parsed'
    pass_argv = [sys.executable, "-c", "print('3 passed in 0.42s')"]
    with mock.patch.object(runner_shared, "SUITE_CHECK_ARGV", pass_argv):
        res_pass = runner_shared.run_suite_check(Path("."), "run-abc123ff")
        assert res_pass.passing is True
        assert res_pass.summary == "3 passed in 0.42s"
        assert res_pass.reason == "suite passed in . (3 passed in 0.42s)"
        assert "no summary line parsed" not in res_pass.reason

    # Failing suite execution: passing is False, failures tuple is non-empty
    fail_argv = [
        sys.executable,
        "-c",
        "import sys; print('FAILED tests/test_demo.py::test_fail'); print('1 failed in 0.10s'); sys.exit(1)",
    ]
    with mock.patch.object(runner_shared, "SUITE_CHECK_ARGV", fail_argv):
        res_fail = runner_shared.run_suite_check(Path("."), "run-abc123ff")
        assert res_fail.passing is False
        assert res_fail.exit_code == 1
        assert res_fail.failures == ("FAILED tests/test_demo.py::test_fail",)
        assert res_fail.summary == "1 failed in 0.10s"
        assert "1 failed in 0.10s" in res_fail.reason


def test_run_worker_process_consumer_contract() -> None:
    """run_worker_process reads attributes in real spawn, and RunnerFn branch is untouched."""
    # Real subprocess execution
    real_cmd = [
        sys.executable,
        "-c",
        "import sys; print('worker_out'); print('worker_err', file=sys.stderr)",
    ]
    packet = host_runner.TaskPacket(
        run_id="run-abc123ff",
        step_id="step-1",
        lane_id="lane-1",
        argv=real_cmd,
        cwd=".",
        timeout_seconds=30.0,
    )
    res_real = host_runner.run_worker_process(packet)
    assert res_real.exit_code == 0
    assert res_real.stdout == "worker_out\n"
    assert res_real.stderr == "worker_err\n"

    # RunnerFn injection seam
    def custom_runner(
        argv: list[str], cwd: str, timeout: float
    ) -> tuple[int, str, str]:
        return (42, "runner_fn_stdout", "runner_fn_stderr")

    res_injected = host_runner.run_worker_process(packet, runner=custom_runner)
    assert res_injected.exit_code == 42
    assert res_injected.stdout == "runner_fn_stdout"
    assert res_injected.stderr == "runner_fn_stderr"
