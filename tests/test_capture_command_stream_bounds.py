"""Tests for capture_command stream bounds enforcement (lijmwy / 75gxkj).

Pins that max_output_bytes applies per-stream to both stdout and stderr, preserves
diagnostics on timeout (exit 124) and spawn failures (exit 127), matches the raw-byte
mid-character boundary on stderr with stdout, records honest per-stream truncation flags,
and interacts correctly with the ledger schema validator and evidence gate.
"""

from __future__ import annotations

import hashlib
import sys

from agent_workflows import host_runner, run_evidence, run_ledger_schema


def test_symmetric_stream_bounds() -> None:
    """A command writing 100 bytes to each stream under max_output_bytes=10 bounds both streams."""
    cmd = [
        sys.executable,
        "-c",
        'import sys; sys.stdout.write("O" * 100); sys.stderr.write("E" * 100)',
    ]
    tool_event, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd,
        max_output_bytes=10,
        actor="executor",
    )

    assert tool_event["stdout_len"] == 10
    assert tool_event["stderr_len"] == 10
    assert tool_event["stdout_truncated"] is True
    assert tool_event["stderr_truncated"] is True
    assert tool_event["truncated"] is True

    # Digests describe retained bytes
    assert tool_event["stdout_sha256"] == hashlib.sha256(b"O" * 10).hexdigest()
    assert tool_event["stderr_sha256"] == hashlib.sha256(b"E" * 10).hexdigest()

    # Out-of-band attributes match retained text
    assert tool_event.stdout == "O" * 10
    assert tool_event.stderr == "E" * 10


def test_asymmetric_stderr_over_bound() -> None:
    """Stdout under bound, stderr over bound: stderr is truncated and flags are honest."""
    cmd = [
        sys.executable,
        "-c",
        'import sys; sys.stdout.write("O" * 5); sys.stderr.write("E" * 5000)',
    ]
    tool_event, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd,
        max_output_bytes=100,
        actor="executor",
    )

    assert tool_event["stdout_len"] == 5
    assert tool_event["stderr_len"] == 100
    assert tool_event["stdout_truncated"] is False
    assert tool_event["stderr_truncated"] is True
    assert tool_event["truncated"] is True

    # Out-of-band attributes
    assert len(tool_event.stderr.encode("utf-8")) == 100
    assert tool_event.stdout == "O" * 5
    assert tool_event.stderr == "E" * 100


def test_asymmetric_stdout_over_bound() -> None:
    """Stdout over bound, stderr under bound: stdout is truncated and flags are honest."""
    cmd = [
        sys.executable,
        "-c",
        'import sys; sys.stdout.write("O" * 5000); sys.stderr.write("E" * 5)',
    ]
    tool_event, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd,
        max_output_bytes=100,
        actor="executor",
    )

    assert tool_event["stdout_len"] == 100
    assert tool_event["stderr_len"] == 5
    assert tool_event["stdout_truncated"] is True
    assert tool_event["stderr_truncated"] is False
    assert tool_event["truncated"] is True

    # Out-of-band attributes
    assert len(tool_event.stdout.encode("utf-8")) == 100
    assert tool_event.stdout == "O" * 100
    assert tool_event.stderr == "E" * 5


def test_unbounded_default_preserves_full_output() -> None:
    """Omitting max_output_bytes leaves both streams unbounded and per-stream flags False."""
    cmd = [
        sys.executable,
        "-c",
        'import sys; sys.stdout.write("O" * 100); sys.stderr.write("E" * 100)',
    ]
    # max_output_bytes omitted to exercise default None
    tool_event, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd,
        actor="executor",
    )

    assert tool_event["stdout_len"] == 100
    assert tool_event["stderr_len"] == 100
    assert tool_event["stdout_truncated"] is False
    assert tool_event["stderr_truncated"] is False
    assert tool_event["truncated"] is False
    assert "max_bytes" not in tool_event

    assert tool_event.stdout == "O" * 100
    assert tool_event.stderr == "E" * 100


def test_timeout_diagnostic_carve_out() -> None:
    """Command exceeding timeout preserves exit 124 and appended timeout sentinel on stderr."""
    cmd = [
        sys.executable,
        "-c",
        'import time, sys; sys.stderr.write("E" * 200); sys.stderr.flush(); time.sleep(10)',
    ]
    tool_event, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd,
        timeout=0.5,
        max_output_bytes=10,
        actor="executor",
    )

    assert tool_event["exit_code"] == 124
    assert tool_event.stderr.endswith("Command timed out.")
    assert tool_event.stderr == "E" * 10 + "\nCommand timed out."
    assert tool_event["stderr_truncated"] is True
    assert tool_event["truncated"] is True


def test_spawn_failure_diagnostic_carve_out() -> None:
    """Nonexistent binary returns exit 127 with full exception text exempt from truncation."""
    cmd = ["/nonexistent_binary_for_test/12345"]
    tool_event, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd,
        max_output_bytes=10,
        actor="executor",
    )

    assert tool_event["exit_code"] == 127
    assert "No such file or directory" in tool_event.stderr
    assert tool_event["stdout_truncated"] is False
    assert tool_event["stderr_truncated"] is False
    assert tool_event["truncated"] is False


def test_mid_character_byte_boundary() -> None:
    """Mid-character byte truncation on stderr matches stdout raw-byte replacement behavior."""
    # '\u00e9' is 2 bytes in UTF-8 (0xc3 0xa9). 5 characters = 10 bytes.
    # Slicing at 3 bytes keeps first character (2 bytes) + 1 partial byte -> 'é\ufffd'.
    cmd_stderr = [
        sys.executable,
        "-c",
        'import sys; sys.stderr.buffer.write("\u00e9".encode("utf-8") * 5)',
    ]
    cmd_stdout = [
        sys.executable,
        "-c",
        'import sys; sys.stdout.buffer.write("\u00e9".encode("utf-8") * 5)',
    ]
    event_stderr, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd_stderr,
        max_output_bytes=3,
        actor="executor",
    )
    event_stdout, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd_stdout,
        max_output_bytes=3,
        actor="executor",
    )

    assert event_stderr["stderr_len"] == 3
    assert event_stderr.stderr == "é\ufffd"
    assert event_stdout["stdout_len"] == 3
    assert event_stdout.stdout == "é\ufffd"
    assert event_stderr.stderr == event_stdout.stdout


def test_ledger_validator_accepts_widened_record() -> None:
    """A record carrying the two new per-stream truncation keys validates ok under schema."""
    cmd = [
        sys.executable,
        "-c",
        'import sys; sys.stdout.write("A" * 50); sys.stderr.write("B" * 50)',
    ]
    tool_event, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd,
        max_output_bytes=10,
        actor="executor",
    )
    val = run_ledger_schema.validate_record(tool_event)
    assert val.ok is True, f"Validation findings: {val.findings}"
    assert len(val.findings) == 0


def test_legacy_build_tool_event_call_shape() -> None:
    """Legacy callers passing neither per-stream key do not fabricate per-stream keys."""
    # Direct call passing legacy truncated=True and neither per-stream flag
    rec1 = run_evidence.build_tool_event(
        run_id="run-abc123ff",
        argv=["cmd"],
        cwd=".",
        exit_code=0,
        stdout="out",
        stderr="err",
        truncated=True,
        actor="executor",
    )
    assert rec1["truncated"] is True
    assert "stdout_truncated" not in rec1
    assert "stderr_truncated" not in rec1

    # Legacy flag cannot mask per-stream flag: truncated=False, stderr_truncated=True
    rec2 = run_evidence.build_tool_event(
        run_id="run-abc123ff",
        argv=["cmd"],
        cwd=".",
        exit_code=0,
        stdout="out",
        stderr="err",
        truncated=False,
        stderr_truncated=True,
        actor="executor",
    )
    assert rec2["truncated"] is True
    assert rec2["stdout_truncated"] is False
    assert rec2["stderr_truncated"] is True

    # Both false
    rec3 = run_evidence.build_tool_event(
        run_id="run-abc123ff",
        argv=["cmd"],
        cwd=".",
        exit_code=0,
        stdout="out",
        stderr="err",
        stdout_truncated=False,
        stderr_truncated=False,
        actor="executor",
    )
    assert rec3["truncated"] is False
    assert rec3["stdout_truncated"] is False
    assert rec3["stderr_truncated"] is False


def test_declared_bound_evidence_gate_pair() -> None:
    """Declared-bound exemption admits stderr truncation; deleting max_bytes rejects."""
    cmd_asym = [
        sys.executable,
        "-c",
        'import sys; sys.stdout.write("O" * 5); sys.stderr.write("E" * 5000)',
    ]
    tool_event, _ = run_evidence.capture_command(
        "run-abc123ff",
        cmd_asym,
        max_output_bytes=100,
        actor="executor",
    )

    # 1. Bounded record with max_bytes present is admitted by evidence_gate
    gate_ok = host_runner.evidence_gate(tool_event)
    assert gate_ok.ok is True, f"Gate findings: {gate_ok.findings}"

    # 2. Same record with max_bytes deleted must reject with EV-TRUNCATED-OUTPUT
    tampered = dict(tool_event)
    del tampered["max_bytes"]
    gate_tampered = host_runner.evidence_gate(tampered)
    assert gate_tampered.ok is False
    assert [f.code for f in gate_tampered.findings] == ["EV-TRUNCATED-OUTPUT"]
