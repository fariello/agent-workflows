"""Tests for host_runner.redact_worker_output and the run_task fail-closed contract.

Pins the behavior of the one production integration point of security_hardening:
- Detection vs. Masking: redact_worker_output detects leaks (e.g. home paths) via
  check_evidence_redaction returning BoundaryResult(ok=False), but does NOT mask them
  in place because stdout/stderr/diff are not sensitive key names in RedactionPolicy
  and leak_sanitizer only detects.
- Refusal: run_task enforces the caller-side fail-closed contract by replacing stdout
  with [REDACTED-LEAK] and transitioning worker state to failed_final (status failed).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import host_runner as hr


class HostRunnerRedactionTests(unittest.TestCase):
    """Tests for redact_worker_output and run_task leak handling."""

    # Built at runtime from fragments so no literal home path exists in source.
    PLANTED_HOME = "/ho" + "me/" + "probeuser42" + "/notes.txt"

    def test_redact_worker_output_detects_leaks_without_in_place_masking(self):
        """redact_worker_output detects leaks via BoundaryResult(ok=False) but preserves raw text.

        The RedactionPolicy masks sensitive KEYS (none of which match stdout/stderr/diff),
        while leak_sanitizer only DETECTS. Therefore, the raw text survives in the returned
        RawWorkerResult, and the caller is responsible for refusing to admit it.
        """
        raw_leaking = hr.RawWorkerResult(
            exit_code=0,
            stdout="captured log with path: " + self.PLANTED_HOME,
            stderr="",
            diff="--- a\n+++ b",
            changed_files=("notes.txt",),
            timed_out=False,
            cancelled=False,
            duration_ms=15.0,
            truncated=False,
        )

        repo_root = Path.cwd()
        redacted, boundary = hr.redact_worker_output(raw_leaking, repo_root=repo_root)

        # (a) Detection: boundary fails closed
        self.assertFalse(
            boundary.ok, "BoundaryResult must be ok=False for planted home path"
        )
        findings = boundary.evidence.get("findings", [])
        self.assertTrue(
            any(f.startswith("home-path@") for f in findings),
            f"Expected home-path finding in evidence, got: {findings!r}",
        )

        # Raw text is NOT masked in place by redact_worker_output
        self.assertIn(
            self.PLANTED_HOME,
            redacted.stdout,
            "stdout should still carry the raw text because stdout is not a sensitive key "
            "and leak_sanitizer detects rather than masks in place",
        )

        # (b) Clean output passes through untouched with ok=True
        raw_clean = hr.RawWorkerResult(
            exit_code=0,
            stdout="clean output without any leaks",
            stderr="",
            diff="--- a\n+++ b",
            changed_files=("clean.txt",),
            timed_out=False,
            cancelled=False,
            duration_ms=10.0,
            truncated=False,
        )
        redacted_clean, boundary_clean = hr.redact_worker_output(
            raw_clean, repo_root=repo_root
        )
        self.assertTrue(boundary_clean.ok, "Clean output must result in ok=True")
        self.assertEqual(redacted_clean.stdout, raw_clean.stdout)

    def test_run_task_caller_side_fail_closed_contract(self):
        """run_task keeps the fail-closed contract by refusing leaked output and replacing it."""
        pkt = hr.TaskPacket(
            run_id="run-test-01",
            step_id="step-test-01",
            lane_id="lane-test-01",
            argv=("test_command",),
            cwd="/tmp",
        )

        def runner_leaking(argv, cwd, timeout):
            return (0, "tool output: " + self.PLANTED_HOME, "")

        def runner_clean(argv, cwd, timeout):
            return (0, "clean execution output", "")

        def diff_capturer(pkt):
            return ("--- a\n+++ b", ("output.txt",))

        repo_root = Path.cwd()

        # (c-1) Leaking runner double: refused, failed_final, [REDACTED-LEAK]
        env_leak, ws_leak, red_leak = hr.run_task(
            pkt,
            runner=runner_leaking,
            diff_capturer=diff_capturer,
            repo_root=repo_root,
        )
        self.assertEqual(ws_leak, hr.WORKER_FAILED_FINAL)
        self.assertEqual(env_leak.get("status"), "failed")
        self.assertEqual(red_leak.stdout, "[REDACTED-LEAK]")
        self.assertEqual(red_leak.stderr, "[REDACTED-LEAK]")
        self.assertEqual(red_leak.diff, "")

        # (c-2) Clean runner double: admitted, completed, performed
        env_clean, ws_clean, red_clean = hr.run_task(
            pkt,
            runner=runner_clean,
            diff_capturer=diff_capturer,
            repo_root=repo_root,
        )
        self.assertEqual(ws_clean, hr.WORKER_COMPLETED)
        self.assertEqual(env_clean.get("status"), "performed")
        self.assertEqual(red_clean.stdout, "clean execution output")


if __name__ == "__main__":
    unittest.main()
