"""hostdedup Order 03 (`xdvglg`): third-host descriptor proof and guard net.

WHAT THIS FILE GUARDS:
1. Demonstrates that a third host can be defined solely as a `HostLabels` descriptor with NO new
   runner module (`*_runipd.py`).
2. Guards host attribution in BOTH directions per maintainer OQ-02 ruling:
   - A runner-less host attributes by explicit `id`.
   - Pre-cutover run records (holding only `driver.path`) continue attributing correctly to their
     historical driver generation and product name via fallback.
3. Guards third-host visibility in `aw host capabilities`.
4. Pins the measured execution LIMIT of the descriptor seam: asserts that a descriptor-only host
   can initialize a run through `initialize_run_core` but is blocked from turn execution by the
   four classified structural/fork boundaries (forked `execute_item`/`run_queue`, lack of spawn
   seam, lack of argv contract, and runner-internal label binding sites).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    agy_runipd,
    host_cmd,
    host_sandbox_profile as hsp,
    oc_runipd,
    run_analytics_sources,
    run_viewer,
    runner_shared,
)

SCRIPTED_HOST_LABELS = runner_shared.HostLabels(
    id="scripted",
    command="aw scripted run",
    review_command="aw scripted review",
    argv_tokens=("scripted", "sc"),
    argv_subcommands=("run", "runipd"),
    product="Scripted",
    report_title="# Scripted IPD Driver Execution Report:",
    shell_tool="run_command",
    emits_launch_identity=False,
    full_auto_actor="aw scripted run --full-auto",
)


class ThirdHostDescriptorTests(unittest.TestCase):
    """E-03 / E-06: The third host exists as a descriptor without a runner module."""

    def test_third_host_needs_no_runner_module(self) -> None:
        """The third host is defined purely as a HostLabels instance with no *_runipd.py module."""
        self.assertIsInstance(SCRIPTED_HOST_LABELS, runner_shared.HostLabels)
        self.assertEqual(SCRIPTED_HOST_LABELS.id, "scripted")
        self.assertEqual(SCRIPTED_HOST_LABELS.product, "Scripted")

        # Verify no scripted_runipd.py exists in agent_workflows/
        aw_dir = Path(runner_shared.__file__).resolve().parent
        self.assertFalse((aw_dir / "scripted_runipd.py").exists())
        self.assertFalse((aw_dir / "sc_runipd.py").exists())

    def test_descriptor_is_distinct_from_existing_hosts(self) -> None:
        self.assertNotEqual(SCRIPTED_HOST_LABELS, runner_shared.OC_HOST_LABELS)
        self.assertNotEqual(SCRIPTED_HOST_LABELS, runner_shared.AGY_HOST_LABELS)


class ThirdHostAttributionTests(unittest.TestCase):
    """E-02 / E-06: Dual-direction host attribution tests."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_runnerless_host_attributes_by_id_in_analytics(self) -> None:
        """A run record with explicit driver.id attributes correctly in run_analytics_sources."""
        state = {
            "schema_version": 1,
            "run_id": "run-test-scripted",
            "driver": {
                "id": "scripted",
                "path": None,
                "sha256": None,
            },
        }
        generation = run_analytics_sources.driver_generation(state)
        self.assertEqual(generation, "scripted")
        self.assertEqual(run_analytics_sources.generation_host(generation), "scripted")

    def test_runnerless_host_attributes_by_id_in_run_viewer(self) -> None:
        """A run record with explicit driver.id attributes correctly in run_viewer."""
        run_dir = self.root / "run-test-scripted"
        run_dir.mkdir(parents=True)
        (run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "run-test-scripted",
                    "driver": {
                        "id": "scripted",
                        "path": None,
                        "sha256": None,
                    },
                    "queue": [],
                    "selectors": [],
                }
            ),
            encoding="utf-8",
        )
        summary = run_viewer.load_run_summary(run_dir, repo_root=self.root)
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.driver, "scripted")

    def test_pre_cutover_path_only_records_still_attribute_in_analytics(self) -> None:
        """Historical run records (holding only driver.path) attribute to historical generations.

        Uses the exact tracked fixture shapes from tests/test_run_analytics_sources.py:141-155, 449.
        """
        historical_cases = [
            ("/home/user/agent_workflows/oc_runipd.py", "oc_runipd", "opencode"),
            ("/home/user/tools/ipdrunner/runipd.py", "runipd", "opencode"),
            ("/home/user/tools/ipdrunner/ipdrunner.py", "ipdrunner", "opencode"),
            ("/home/user/agent_workflows/agy_runipd.py", "agy_runipd", "agy"),
        ]
        for path_val, expected_gen, expected_host in historical_cases:
            with self.subTest(path=path_val):
                state = {
                    "schema_version": 1,
                    "run_id": "run-historical",
                    "driver": {
                        "path": path_val,
                        "sha256": "abcdef123456",
                    },
                }
                gen = run_analytics_sources.driver_generation(state)
                self.assertEqual(gen, expected_gen)
                self.assertEqual(
                    run_analytics_sources.generation_host(gen), expected_host
                )

    def test_pre_cutover_path_only_records_still_attribute_in_run_viewer(self) -> None:
        """Historical run records without driver.id attribute in run_viewer via substring/stem fallback."""
        cases = [
            ("/home/user/agent_workflows/oc_runipd.py", "OpenCode"),
            ("/home/user/agent_workflows/agy_runipd.py", "Antigravity"),
            ("/home/user/tools/ipdrunner/runipd.py", "runipd"),
            ("/home/user/tools/ipdrunner/ipdrunner.py", "ipdrunner"),
        ]
        for idx, (path_val, expected_label) in enumerate(cases):
            with self.subTest(path=path_val):
                run_dir = self.root / f"run-hist-{idx}"
                run_dir.mkdir(parents=True)
                (run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "run_id": f"run-hist-{idx}",
                            "driver": {
                                "path": path_val,
                                "sha256": "abcdef123456",
                            },
                            "queue": [],
                            "selectors": [],
                        }
                    ),
                    encoding="utf-8",
                )
                summary = run_viewer.load_run_summary(run_dir, repo_root=self.root)
                self.assertIsNotNone(summary)
                assert summary is not None
                self.assertEqual(summary.driver, expected_label)


class ThirdHostCapabilitiesTests(unittest.TestCase):
    """E-06: Visibility in aw host capabilities."""

    def test_scripted_host_is_in_default_hosts(self) -> None:
        self.assertIn("scripted", host_cmd.DEFAULT_HOSTS)

    def test_scripted_host_describes_cleanly(self) -> None:
        report = host_cmd._describe_host("scripted")
        self.assertEqual(report["host"], "scripted")
        self.assertIn("capabilities", report)
        self.assertIn("actions", report)
        # Sandbox detection fail-closes or probes honestly
        caps = hsp.detect_host_capabilities("scripted")
        self.assertFalse(caps.emits_structured_tool_events)
        self.assertFalse(caps.supports_session_resume)


class ThirdHostInitializationAndLimitTests(unittest.TestCase):
    """E-03 / E-06: Prove initialize_run works for third host, and pin the turn execution LIMIT."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # Create a mini git repo for initialize_run_core
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=self.root, check=True)
        pending = self.root / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        (pending / "20260924-test-01-tst001-test.ipd.md").write_text(
            "# IPD: Test\n\n- Date: 2026-09-24\n- Status: approved\n- Set: test\n- Order: 1\n- Id: tst001\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=self.root, check=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_initialize_run_core_succeeds_with_third_host_descriptor(self) -> None:
        """The third host successfully initializes a run without any runner module."""
        args = argparse.Namespace(
            repo=str(self.root),
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
            run_id="run-20260924T000000Z-999999",
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
        host_options = {"mock_option": True}

        run_dir = runner_shared.initialize_run_core(
            args,
            host="scripted",
            driver_path=None,
            host_options=host_options,
            labels=SCRIPTED_HOST_LABELS,
            expand_selectors_fn=lambda manifest, selectors, **kw: ["tst001"],
            enforce_dependency_preflight_fn=lambda *a, **kw: None,
            announce_run_order_fn=lambda rdir, st: None,
            run_order_rationale_fn=lambda queue, sel: "test rationale",
            write_report_fn=lambda rdir, st: None,
        )

        self.assertTrue(run_dir.exists())
        state = runner_shared.load_state(run_dir)
        self.assertEqual(state["driver"]["id"], "scripted")
        self.assertIsNone(state["driver"]["path"])
        self.assertIsNone(state["driver"]["sha256"])

        # And verify analytics / viewer on this real state
        self.assertEqual(run_analytics_sources.driver_generation(state), "scripted")
        summary = run_viewer.load_run_summary(run_dir, repo_root=self.root)
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.driver, "scripted")

    def test_pin_measured_turn_execution_limits(self) -> None:
        """PIN THE BOUNDARY (E-03/E-04/E-06): A descriptor-only host cannot execute a turn.

        This test fails if:
        1. Shared runner gains an unparameterized spawn seam or argv builder without updating this guard.
        2. execute_item or run_queue is unified into runner_shared without a generic spawn contract.
        """
        # Wall 1: runner_shared does not define a generic run_queue or execute_item
        self.assertFalse(hasattr(runner_shared, "run_queue"))
        self.assertFalse(hasattr(runner_shared, "execute_item"))

        # Wall 2: execute_item is forked in each runner module and hardcodes its own spawn function
        self.assertTrue(hasattr(oc_runipd, "execute_item"))
        self.assertTrue(hasattr(agy_runipd, "execute_item"))
        self.assertTrue(hasattr(oc_runipd, "run_opencode"))
        self.assertTrue(hasattr(agy_runipd, "run_agy_turn"))

        # Wall 3: HostLabels carries no spawn function, argv builder, or per-turn execution contract
        for field in runner_shared.HostLabels._fields:
            self.assertNotIn("spawn", field)
            self.assertNotIn("runner_fn", field)
            self.assertNotIn("argv_builder", field)
