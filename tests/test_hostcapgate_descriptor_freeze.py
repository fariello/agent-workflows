"""Tests for host capability descriptor freeze and concurrent-safe launch interception.

bqtgmo (hostcapgate Order 01, spec 25kzda 5.2):
- Property (a): ordinary launches on a concurrent thread succeed during detect_host_capabilities.
- Property (b): one run initialization freezes exactly one descriptor snapshot into durable state.
- Property (c): dispatching multiple items performs no further probe, default-profile
  _apply_execution_profile performs none, and hardened profile with frozen no-sandbox
  descriptor raises HardModeUnavailableError.
- Property (d): an unfrozen state measures once and self-heals, and a raising probe
  records an all-False descriptor without aborting the run.
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import host_sandbox_profile as hsp
from agent_workflows import oc_runipd, runner_shared


class HostCapGateDescriptorFreezeTests(unittest.TestCase):
    """Falsifiable behavior tests for the host capability descriptor freeze (bqtgmo)."""

    def test_concurrent_launches_succeed_during_probe(self) -> None:
        """Property (a): concurrent thread ordinary launches succeed during detect_host_capabilities."""
        worker_successes = 0
        worker_failures: list[tuple[str, str]] = []
        stop = False

        def worker() -> None:
            nonlocal worker_successes
            while not stop:
                try:
                    res = subprocess.run(
                        ["true"],
                        capture_output=True,
                    )
                    if res.returncode == 0:
                        worker_successes += 1
                except Exception as exc:
                    worker_failures.append((type(exc).__name__, str(exc)))
                time.sleep(0.001)

        t = threading.Thread(target=worker)
        t.start()
        try:
            for _ in range(4):
                hsp._HOST_ARGV_CACHE.clear()
                hsp.detect_host_capabilities("opencode")
        finally:
            stop = True
            t.join(timeout=10.0)

        self.assertGreater(
            worker_successes, 0, "concurrent worker must execute launches"
        )
        self.assertEqual(
            worker_failures,
            [],
            "concurrent worker must experience zero launch failures",
        )

    def test_run_initialization_produces_one_descriptor_snapshot_in_durable_state(
        self,
    ) -> None:
        """Property (b): run initialization freezes one descriptor snapshot with host and observed_at."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            for cmd in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Test"],
            ):
                subprocess.run(cmd, cwd=repo_root, check=True)

            pending = repo_root / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True, exist_ok=True)
            plan_file = pending / "20261003-test-01-tst001-sample.ipd.md"
            from tests.test_oc_runipd import _CONFORMING_PLAN

            plan_file.write_text(
                _CONFORMING_PLAN.format(id6="tst001"),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial"], cwd=repo_root, check=True
            )

            args = argparse.Namespace(
                repo=str(repo_root),
                selectors=["all"],
                full_auto=False,
                output_mode="clean",
                verbosity=0,
                stall_timeout=600.0,
                session=None,
                self_finalize=True,
                isolate_worktree=True,
                max_items_per_session=4,
                prepare_only=True,
                action=None,
                run_id="run-20261003T000000Z-111111",
                manifest=None,
                runbook=None,
                types=None,
                allow_mixed=False,
                allow_drafts=False,
                allow_unverifiable=False,
                allow_dirty_base=False,
                allow_concurrent_driver=False,
                allow_uncovered_orchestrator_work=False,
                retry_budget=None,
                integration_retry_limit=None,
                on_integration_blocked=None,
            )

            run_dir = runner_shared.initialize_run_core(
                args,
                host="oc",
                driver_path=Path(__file__),
                host_options={},
                labels=runner_shared.OC_HOST_LABELS,
                expand_selectors_fn=lambda manifest, selectors, **kw: ["tst001"],
                enforce_dependency_preflight_fn=lambda *a, **kw: None,
                announce_run_order_fn=lambda rdir, st: None,
                run_order_rationale_fn=lambda queue, sel: "test rationale",
                write_report_fn=lambda rdir, st: None,
            )

            state_path = run_dir / "state.json"
            self.assertTrue(state_path.is_file(), "state.json must be written")
            state = runner_shared.load_json(state_path)
            self.assertIn("host_capabilities", state)
            hc = state["host_capabilities"]
            self.assertEqual(hc.get("host"), "opencode")
            self.assertIn("observed_at", hc)
            self.assertTrue(hc["observed_at"])
            self.assertIn("descriptor", hc)
            desc = hc["descriptor"]
            self.assertIsInstance(desc, dict)
            self.assertIn("supports_os_sandbox", desc)
            self.assertIn("supports_session_resume", desc)
            self.assertIn("supports_fresh_verifier_session", desc)

    def test_dispatch_and_execution_profile_perform_zero_additional_probes(
        self,
    ) -> None:
        """Property (c): dispatching multiple items performs no further probe, and default _apply_execution_profile performs none."""
        probe_count = 0
        orig_detect = hsp.detect_host_capabilities

        def counting_detect(
            host: str, *a: object, **k: object
        ) -> hsp.HostSandboxCapabilities:
            nonlocal probe_count
            probe_count += 1
            return orig_detect(host, *a, **k)

        # 1. Multiple items reading frozen state perform zero probes:
        state = {
            "run_id": "run-test",
            "host_capabilities": {
                "host": "opencode",
                "observed_at": runner_shared.utc_now(),
                "descriptor": hsp.HostSandboxCapabilities(
                    supports_os_sandbox=True
                ).to_dict(),
            },
        }
        with mock.patch.object(
            hsp, "detect_host_capabilities", side_effect=counting_detect
        ):
            caps1 = runner_shared.ensure_frozen_host_capabilities(state, "opencode")
            caps2 = runner_shared.ensure_frozen_host_capabilities(state, "opencode")
            caps3 = runner_shared.ensure_frozen_host_capabilities(state, "opencode")

        self.assertEqual(
            probe_count,
            0,
            "ensure_frozen_host_capabilities must perform zero probes on frozen state",
        )
        self.assertTrue(caps1.supports_os_sandbox)
        self.assertEqual(caps1, caps2)
        self.assertEqual(caps2, caps3)

        # 2. oc_runipd._apply_execution_profile on default profile performs zero probes:
        oc_probe_count = 0

        def counting_oc_detect(
            host: str, *a: object, **k: object
        ) -> hsp.HostSandboxCapabilities:
            nonlocal oc_probe_count
            oc_probe_count += 1
            return orig_detect(host, *a, **k)

        state_default: dict[str, object] = {"options": {}}
        item: dict[str, object] = {"id6": "t01", "setid": "test", "position": 1}
        argv = ["opencode", "run", "--flag"]
        with mock.patch.object(
            oc_runipd, "detect_host_capabilities", side_effect=counting_oc_detect
        ):
            for _ in range(3):
                res = oc_runipd._apply_execution_profile(
                    state_default, item, argv, "/tmp", "/tmp"
                )
                self.assertEqual(res, argv)

        self.assertEqual(
            oc_probe_count,
            0,
            "default-profile _apply_execution_profile must perform zero capability probes",
        )

        # 3. Hardened request with frozen no-sandbox descriptor raises HardModeUnavailableError:
        state_no_sandbox: dict[str, object] = {
            "options": {"execution_profile": "hardened"},
            "host_capabilities": {
                "host": "opencode",
                "observed_at": runner_shared.utc_now(),
                "descriptor": hsp.HostSandboxCapabilities(
                    supports_os_sandbox=False
                ).to_dict(),
            },
        }
        with self.assertRaises(hsp.HardModeUnavailableError):
            oc_runipd._apply_execution_profile(
                state_no_sandbox, item, argv, "/tmp", "/tmp/lane"
            )

    def test_unfrozen_state_self_heals_once_and_measurement_error_records_all_false(
        self,
    ) -> None:
        """Property (d): an unfrozen state measures once and self-heals, and a raising probe records all-False without aborting."""
        probe_count = 0
        orig_detect = hsp.detect_host_capabilities

        def counting_detect(
            host: str, *a: object, **k: object
        ) -> hsp.HostSandboxCapabilities:
            nonlocal probe_count
            probe_count += 1
            return orig_detect(host, *a, **k)

        # 1. Self-healing on unfrozen state:
        state_unfrozen: dict[str, object] = {}
        with mock.patch.object(
            hsp, "detect_host_capabilities", side_effect=counting_detect
        ):
            c1 = runner_shared.ensure_frozen_host_capabilities(
                state_unfrozen, "opencode"
            )
            c2 = runner_shared.ensure_frozen_host_capabilities(
                state_unfrozen, "opencode"
            )
            c3 = runner_shared.ensure_frozen_host_capabilities(
                state_unfrozen, "opencode"
            )

        self.assertEqual(
            probe_count,
            1,
            "unfrozen state must trigger exactly one probe across multiple items",
        )
        self.assertIn("host_capabilities", state_unfrozen)
        hc = state_unfrozen["host_capabilities"]
        self.assertIsInstance(hc, dict)
        self.assertEqual(hc.get("host"), "opencode")
        self.assertEqual(c1, c2)
        self.assertEqual(c2, c3)

        # 2. Measurement error does not abort: records all-False descriptor with error in notes:
        state_error: dict[str, object] = {}

        def raising_detect(
            host: str, *a: object, **k: object
        ) -> hsp.HostSandboxCapabilities:
            raise RuntimeError("simulated probe failure")

        with mock.patch.object(
            hsp, "detect_host_capabilities", side_effect=raising_detect
        ):
            caps_fallback = runner_shared.ensure_frozen_host_capabilities(
                state_error, "opencode"
            )

        self.assertIn("host_capabilities", state_error)
        desc = state_error["host_capabilities"]["descriptor"]
        self.assertFalse(desc["supports_os_sandbox"])
        self.assertFalse(desc["supports_session_resume"])
        self.assertFalse(desc["supports_fresh_verifier_session"])
        self.assertIn("on_demand_probe_error", desc["probe_notes"])
        self.assertIn(
            "simulated probe failure", desc["probe_notes"]["on_demand_probe_error"]
        )
        self.assertFalse(caps_fallback.supports_os_sandbox)
