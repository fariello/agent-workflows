"""Self-tests for bench_env.py: capture is honest, diagnostics fire on known pitfalls,
scrubbing redacts identity, the disk probe and warm-up are bounded and safe, and output
formats parse. Stdlib unittest only.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.support import BENCH_ENV, REPO_ROOT, run_tool, load_module

BE = load_module("bench_env", BENCH_ENV)


class DiagnosisUnitTests(unittest.TestCase):
    """diagnose() must flag known-bad configs and stay quiet on a clean one."""

    def _rep_with_path(self, fs_type, free_gb=100.0):
        rep = BE.EnvReport()
        rep.paths = [{"path": "/data", "exists": True, "fs_type": fs_type,
                      "source": "srv:/export", "free_gb": free_gb, "total_gb": 500.0}]
        return rep

    def test_flags_network_filesystem_working_set(self):
        rep = self._rep_with_path("nfs4")
        BE.diagnose(rep)
        ids = [d.id for d in rep.diagnostics]
        self.assertIn("storage.network_fs", ids)
        nf = next(d for d in rep.diagnostics if d.id == "storage.network_fs")
        self.assertEqual(nf.severity, "high")
        self.assertTrue(nf.remedy, "network-fs finding must carry a suggested remedy")

    def test_lustre_is_flagged_as_network(self):
        rep = self._rep_with_path("lustre")
        BE.diagnose(rep)
        self.assertIn("storage.network_fs", [d.id for d in rep.diagnostics])

    def test_low_space_flagged(self):
        rep = self._rep_with_path("ext4", free_gb=1.0)
        BE.diagnose(rep)
        self.assertIn("storage.low_space", [d.id for d in rep.diagnostics])

    def test_powersave_governor_flagged(self):
        rep = BE.EnvReport()
        rep.cpu_governor = "powersave"
        BE.diagnose(rep)
        self.assertIn("cpu.governor", [d.id for d in rep.diagnostics])

    def test_performance_governor_not_flagged(self):
        rep = BE.EnvReport()
        rep.cpu_governor = "performance"
        BE.diagnose(rep)
        self.assertNotIn("cpu.governor", [d.id for d in rep.diagnostics])

    def test_swapping_flagged(self):
        rep = BE.EnvReport()
        rep.swap_total_kb = 8 * 1024 * 1024
        rep.swap_free_kb = 1 * 1024 * 1024  # 7 GB used
        BE.diagnose(rep)
        self.assertIn("memory.swapping", [d.id for d in rep.diagnostics])

    def test_busy_host_flagged(self):
        rep = BE.EnvReport()
        rep.cpu_logical = 8
        rep.load_avg = [30.0, 20.0, 10.0]
        BE.diagnose(rep)
        self.assertIn("load.busy", [d.id for d in rep.diagnostics])

    def test_hpc_login_node_flagged(self):
        rep = BE.EnvReport()
        rep.hpc = {"scheduler_detected": True, "primary": "slurm", "inside_allocation": False}
        BE.diagnose(rep)
        self.assertIn("hpc.on_login_node", [d.id for d in rep.diagnostics])

    def test_clean_environment_produces_no_diagnostics(self):
        rep = BE.EnvReport()
        rep.cpu_governor = "performance"
        rep.cpu_logical = 16
        rep.load_avg = [0.1, 0.1, 0.1]
        rep.paths = [{"path": "/w", "exists": True, "fs_type": "ext4", "source": "/dev/sda1",
                      "free_gb": 500.0, "total_gb": 900.0}]
        BE.diagnose(rep)
        self.assertEqual(rep.diagnostics, [])


class HpcDetectionTests(unittest.TestCase):
    """capture_hpc() maps scheduler binaries + job-id env vars to the report (S3-T1)."""

    def test_detects_slurm_and_inside_allocation(self):
        orig_which = BE._which
        orig_run = BE._run
        BE._which = lambda n: n in {"sbatch", "squeue", "sinfo"}
        BE._run = lambda argv, timeout=15: ""  # sinfo partitions -> empty, fine
        os.environ["SLURM_JOB_ID"] = "12345"
        try:
            rep = BE.EnvReport()
            BE.capture_hpc(rep)
        finally:
            BE._which = orig_which
            BE._run = orig_run
            os.environ.pop("SLURM_JOB_ID", None)
        self.assertTrue(rep.hpc["scheduler_detected"])
        self.assertIn("slurm", rep.hpc["schedulers"])
        self.assertEqual(rep.hpc["primary"], "slurm")
        self.assertTrue(rep.hpc["inside_allocation"])

    def test_no_scheduler_when_none_present(self):
        orig_which = BE._which
        BE._which = lambda n: False
        try:
            rep = BE.EnvReport()
            BE.capture_hpc(rep)
        finally:
            BE._which = orig_which
        self.assertFalse(rep.hpc["scheduler_detected"])
        self.assertEqual(rep.hpc["primary"], "")


class ScrubTests(unittest.TestCase):
    def test_scrub_redacts_identity_but_keeps_useful_fields(self):
        rep = BE.EnvReport()
        rep.hostname = "secret-host.example.edu"
        rep.user = "alice"
        rep.paths = [{"path": "/home/alice/data", "exists": True, "fs_type": "nfs4",
                      "source": "srv:/export", "free_gb": 10.0}]
        BE.scrub(rep)
        self.assertNotIn("alice", rep.hostname)
        self.assertNotIn("alice", rep.user)
        self.assertEqual(rep.paths[0]["path"], "path-redacted")
        # the useful bits survive
        self.assertEqual(rep.paths[0]["fs_type"], "nfs4")
        self.assertEqual(rep.paths[0]["free_gb"], 10.0)


class ProbeAndWarmTests(unittest.TestCase):
    def test_disk_probe_is_bounded_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as td:
            scratch = Path(td) / "probe"
            dp = BE.disk_probe(scratch, size_mb=2)
            self.assertIsNotNone(dp.write_mb_s)
            self.assertIsNotNone(dp.read_mb_s)
            # no probe temp file left behind
            leftovers = list(scratch.glob(".bench_probe_*.tmp"))
            self.assertEqual(leftovers, [], "probe temp file was not cleaned up")

    def test_warm_paths_reads_files_and_notes_missing(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "a.bin"
            f.write_bytes(b"x" * 4096)
            notes = BE.warm_paths([f, Path(td) / "missing.bin"])
            joined = " ".join(notes)
            self.assertIn("warmed", joined)
            self.assertIn("does not exist", joined)


class EndToEndTests(unittest.TestCase):
    def test_json_capture_has_required_context_fields(self):
        proc = run_tool(BENCH_ENV, "--repo", str(REPO_ROOT), "--format", "json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        # requirement 6: deep host context must be present as keys (values may be null on
        # some OSes, but the fields must exist and be honest).
        for key in ("hostname", "os", "cpu_model", "cpu_logical", "mem_total_kb",
                    "load_avg", "gpus", "paths", "hpc", "unread", "captured_at_utc"):
            self.assertIn(key, data, f"missing context field: {key}")
        self.assertTrue(data["paths"], "at least the repo path should be captured")

    def test_scrub_flag_end_to_end(self):
        proc = run_tool(BENCH_ENV, "--repo", str(REPO_ROOT), "--format", "json", "--scrub")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["hostname"], "host-redacted")
        self.assertEqual(data["user"], "user-redacted")

    def test_bad_repo_path_is_usage_error(self):
        proc = run_tool(BENCH_ENV, "--repo", "/nonexistent/path/xyz", "--format", "json")
        self.assertEqual(proc.returncode, 2)

    def test_version_flag(self):
        proc = run_tool(BENCH_ENV, "--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        expected = (REPO_ROOT / ".agents/workflows/VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(proc.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
