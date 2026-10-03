"""Tests for host_runner output bound enforcement and evidence gate integration (fqseay / egywai).

Pins that TaskPacket.max_output_bytes actually bounds worker stdout capture on both
the real-spawn branch and the RunnerFn injection double seam, preserves the unbounded
default, matches the mid-character byte boundary behavior across both branches,
bounds stderr per stream, and enables evidence_gate and
host_launchers.host_result_can_finalize to accept declared, honored output bounds.
"""

from __future__ import annotations

import unittest

from agent_workflows import (
    host_launchers as hl,
)
from agent_workflows import (
    host_runner as hr,
)
from agent_workflows import (
    run_evidence as ev,
)


class TestHostRunnerOutputBound(unittest.TestCase):
    """Pin output bound enforcement on both real spawn and runner double branches."""

    def test_real_spawn_output_bound_enforced(self):
        packet = hr.TaskPacket(
            run_id="run-abc123ff",
            step_id="step-1",
            lane_id="lane-1",
            argv=("python3", "-c", "print('A'*50000)"),
            cwd=".",
            max_output_bytes=100,
        )
        res = hr.run_worker_process(packet)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(len(res.stdout), 100)
        self.assertTrue(res.truncated)

    def test_unbounded_default_preserves_full_output(self):
        # Default constructed without max_output_bytes keyword
        packet = hr.TaskPacket(
            run_id="run-abc123ff",
            step_id="step-1",
            lane_id="lane-1",
            argv=("python3", "-c", "print('A'*50000)"),
            cwd=".",
        )
        self.assertIsNone(packet.max_output_bytes)
        res = hr.run_worker_process(packet)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(len(res.stdout), 50001)
        self.assertFalse(res.truncated)

    def test_runner_double_output_bound_enforced(self):
        packet = hr.TaskPacket(
            run_id="run-abc123ff",
            step_id="step-1",
            lane_id="lane-1",
            argv=("echo", "double"),
            cwd=".",
            max_output_bytes=100,
        )

        def double_runner(argv, cwd, timeout):
            return 0, "B" * 50000, ""

        res = hr.run_worker_process(packet, runner=double_runner)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(len(res.stdout), 100)
        self.assertTrue(res.truncated)

    def test_real_spawn_mid_character_byte_boundary(self):
        # Recipe from F-09: 'A'*5 + '\u00e9'*5
        # 6 bytes raw: 'AAAAA' + first byte of '\u00e9' -> 'AAAAA\ufffd'
        # 7 bytes raw: 'AAAAA' + both bytes of '\u00e9' -> 'AAAAAé'
        cmd = 'import sys; sys.stdout.buffer.write("A".encode("utf-8")*5 + "\u00e9".encode("utf-8")*5)'
        p6 = hr.TaskPacket(
            run_id="run-abc123ff",
            step_id="step-1",
            lane_id="lane-1",
            argv=("python3", "-c", cmd),
            cwd=".",
            max_output_bytes=6,
        )
        r6 = hr.run_worker_process(p6)
        self.assertEqual(r6.stdout, "AAAAA\ufffd")
        self.assertTrue(r6.truncated)

        p7 = hr.TaskPacket(
            run_id="run-abc123ff",
            step_id="step-1",
            lane_id="lane-1",
            argv=("python3", "-c", cmd),
            cwd=".",
            max_output_bytes=7,
        )
        r7 = hr.run_worker_process(p7)
        self.assertEqual(r7.stdout, "AAAAAé")
        self.assertTrue(r7.truncated)

    def test_runner_double_mid_character_byte_boundary(self):
        def double_runner(argv, cwd, timeout):
            return 0, "A" * 5 + "\u00e9" * 5, ""

        p6 = hr.TaskPacket(
            run_id="run-abc123ff",
            step_id="step-1",
            lane_id="lane-1",
            argv=("echo", "double"),
            cwd=".",
            max_output_bytes=6,
        )
        r6 = hr.run_worker_process(p6, runner=double_runner)
        self.assertEqual(r6.stdout, "AAAAA\ufffd")
        self.assertTrue(r6.truncated)

        p7 = hr.TaskPacket(
            run_id="run-abc123ff",
            step_id="step-1",
            lane_id="lane-1",
            argv=("echo", "double"),
            cwd=".",
            max_output_bytes=7,
        )
        r7 = hr.run_worker_process(p7, runner=double_runner)
        self.assertEqual(r7.stdout, "AAAAAé")
        self.assertTrue(r7.truncated)

    def test_stderr_is_bounded_per_stream(self):
        cmd = 'import sys; sys.stdout.write("out"); sys.stderr.write("E"*5000)'
        packet = hr.TaskPacket(
            run_id="run-abc123ff",
            step_id="step-1",
            lane_id="lane-1",
            argv=("python3", "-c", cmd),
            cwd=".",
            max_output_bytes=2,
        )
        res = hr.run_worker_process(packet)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.stdout, "ou")
        self.assertEqual(len(res.stderr), 2)
        self.assertTrue(res.truncated)

        def double_runner(argv, cwd, timeout):
            return 0, "out", "E" * 5000

        res_double = hr.run_worker_process(packet, runner=double_runner)
        self.assertEqual(res_double.exit_code, 0)
        self.assertEqual(res_double.stdout, "ou")
        self.assertEqual(len(res_double.stderr), 2)
        self.assertTrue(res_double.truncated)


class TestEvidenceGateBoundedOutput(unittest.TestCase):
    """Pin evidence gate and finalization behavior on bounded captures."""

    def test_gate_accepts_bounded_capture_carrying_max_bytes(self):
        # Case (a): bounded capture whose record carries max_bytes passes the gate
        event, _ = ev.capture_command(
            "run-abc123ff",
            ["python3", "-c", "print('A'*50000)"],
            max_output_bytes=100,
        )
        self.assertIn("max_bytes", event)
        self.assertEqual(event["max_bytes"], 100)
        gate_res = hr.evidence_gate(event)
        self.assertTrue(gate_res.ok)
        self.assertEqual(len(gate_res.findings), 0)

    def test_gate_rejects_truncated_record_when_max_bytes_deleted(self):
        # Case (b): the same truncated record with max_bytes deleted fails with EV-TRUNCATED-OUTPUT
        event, _ = ev.capture_command(
            "run-abc123ff",
            ["python3", "-c", "print('A'*50000)"],
            max_output_bytes=100,
        )
        modified_event = dict(event)
        del modified_event["max_bytes"]
        gate_res = hr.evidence_gate(modified_event)
        self.assertFalse(gate_res.ok)
        finding_codes = [f.code for f in gate_res.findings]
        self.assertIn("EV-TRUNCATED-OUTPUT", finding_codes)
        self.assertEqual(finding_codes, ["EV-TRUNCATED-OUTPUT"])

    def test_gate_rejects_zero_bound_due_to_missing_output(self):
        # Case (c): bound of 0 fails because EV-MISSING-OUTPUT also fires on empty output
        event, _ = ev.capture_command(
            "run-abc123ff",
            ["python3", "-c", "print('A'*10)"],
            max_output_bytes=0,
        )
        self.assertIn("max_bytes", event)
        gate_res = hr.evidence_gate(event)
        self.assertFalse(gate_res.ok)
        finding_codes = [f.code for f in gate_res.findings]
        self.assertIn("EV-MISSING-OUTPUT", finding_codes)
        self.assertIn("EV-TRUNCATED-OUTPUT", finding_codes)

    def test_gate_rejects_nonzero_exit_under_bound(self):
        # Case (d): nonzero-exit capture under a bound fails with EV-FAILED-EXIT
        event, _ = ev.capture_command(
            "run-abc123ff",
            ["python3", "-c", "import sys; print('fail'); sys.exit(2)"],
            max_output_bytes=100,
        )
        gate_res = hr.evidence_gate(event)
        self.assertFalse(gate_res.ok)
        finding_codes = [f.code for f in gate_res.findings]
        self.assertIn("EV-FAILED-EXIT", finding_codes)

    def test_host_result_can_finalize_with_bounded_worker(self):
        event, _ = ev.capture_command(
            "run-abc123ff",
            ["python3", "-c", "print('A'*50000)"],
            max_output_bytes=100,
        )
        raw = hr.RawWorkerResult(
            exit_code=0,
            stdout=event.stdout,
            stderr=event.stderr,
            diff="--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new",
            changed_files=("file.py",),
            timed_out=False,
            cancelled=False,
            duration_ms=10.0,
            truncated=True,
        )
        can_finalize, reason = hl.host_result_can_finalize(raw, event)
        self.assertTrue(can_finalize)
        self.assertEqual(reason, "completed with a verified side effect")


if __name__ == "__main__":
    unittest.main()
