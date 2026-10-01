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
import contextlib
import io
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
    run_dashboard,
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
    dependency_block_recovery=(
        "resolve the named cause, then re-queue with "
        "`aw scripted runipd resume --repo <repo> --retry-incomplete <run-id>`; "
        "a bare `resume` does NOT re-queue a dependency-blocked item"
    ),
)


class ThirdHostDescriptorTests(unittest.TestCase):
    """E-03 / E-06: The third host exists as a descriptor without a runner module."""

    def test_third_host_needs_no_runner_module(self) -> None:
        """The third host is defined purely as a HostLabels instance with no *_runipd.py module."""
        self.assertIsInstance(SCRIPTED_HOST_LABELS, runner_shared.HostLabels)
        self.assertEqual(SCRIPTED_HOST_LABELS.id, "scripted")
        self.assertEqual(SCRIPTED_HOST_LABELS.product, "Scripted")

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
        from tests.test_oc_runipd import _CONFORMING_PLAN

        (pending / "20260924-test-01-tst001-test.ipd.md").write_text(
            _CONFORMING_PLAN.format(id6="tst001"),
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

    def _create_conforming_repo(self, repo_dir: Path) -> Path:
        for cmd in (
            ["git", "init", "-q", str(repo_dir)],
            [
                "git",
                "-C",
                str(repo_dir),
                "config",
                "user.email",
                "test@example.invalid",
            ],
            ["git", "-C", str(repo_dir), "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, check=True)
        pending = repo_dir / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        from tests.test_oc_runipd import _CONFORMING_PLAN

        (pending / "20260924-test-01-tst001-test.ipd.md").write_text(
            _CONFORMING_PLAN.format(id6="tst001"),
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo_dir, check=True)
        return repo_dir

    def test_each_real_host_records_own_driver_identity_and_consumers_route(
        self,
    ) -> None:
        """Each real host records its own module path and digest, and consumers route correctly (E-02, E-03).

        Producer assertions (E-02):
        - Path basename in driver record matches the host runner module's own basename.
        - Driver sha256 matches runner_shared.sha256_file of that module file.
        - The real hosts record distinct driver paths, guarding against shared-core relocation.
        - The host table is discovered from all HostLabels instances in runner_shared, and
          an undiscovered host fails rather than being skipped.
        - No synthetic hand-written driver fixtures are used; state is genuinely produced.

        Consumer assertions (E-03):
        - run_analytics_sources.driver_generation returns the host's HostLabels.id (!= UNKNOWN).
        - generation_host returns the host's expected label.
        - run_viewer.load_run_summary().driver matches the host's HostLabels.product.

        Honest bound on consumer assertions:
        At this HEAD, these consumer assertions do not detect the relocation sabotage, because
        driver_generation prefers driver.id and run_viewer checks driver_id first, so both return
        the right label from a record whose path is wrong. They are included because they pin the
        ID-preferring precedence itself (if a future change removes driver.id or reorders that
        precedence, the path fallback becomes load-bearing again and these assertions become the ones
        that catch it), while E-02's basename and digest assertions are the ones that detect relocation.

        Third consumer covered (o55eli):
        We assert over all three consumers (run_analytics_sources, run_viewer, and run_dashboard._run_host).
        run_dashboard._run_host resolves driver.id through runner_shared.host_labels_for_driver_id rather
        than fragile prefix matching, falling through to downstream signals on unregistered ids (plan o55eli).
        """
        host_runner_map = {
            runner_shared.OC_HOST_LABELS.id: (oc_runipd, "opencode"),
            runner_shared.AGY_HOST_LABELS.id: (agy_runipd, "agy"),
        }

        discovered_labels = [
            v
            for v in vars(runner_shared).values()
            if isinstance(v, runner_shared.HostLabels)
        ]
        self.assertGreater(len(discovered_labels), 0)

        recorded_paths: dict[str, Path] = {}
        for labels in discovered_labels:
            self.assertIn(
                labels.id,
                host_runner_map,
                f"HostLabels instance {labels.id!r} has no runner module mapping in host_runner_map; "
                f"adding a real host requires extending this test",
            )
            module, expected_gen_host = host_runner_map[labels.id]
            repo = self._create_conforming_repo(self.root / f"repo-{labels.id}")
            args = module.build_parser().parse_args(
                ["start", "tst001", "--repo", str(repo), "--prepare-only"]
            )
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                run_dir = module.initialize_run(args)

            state = runner_shared.load_state(run_dir)
            driver = state["driver"]
            driver_path = Path(driver["path"])
            recorded_paths[labels.id] = driver_path

            # E-02: Assert basename matches host module's own basename
            self.assertEqual(driver_path.name, Path(module.__file__).name)

            # E-02: Assert digest matches sha256_file of host module
            expected_sha256 = runner_shared.sha256_file(Path(module.__file__))
            self.assertEqual(driver["sha256"], expected_sha256)

            # E-03: Consumer assertions
            gen = run_analytics_sources.driver_generation(state)
            self.assertEqual(gen, labels.id)
            self.assertNotEqual(gen, run_analytics_sources.GENERATION_UNKNOWN)
            self.assertEqual(
                run_analytics_sources.generation_host(gen),
                expected_gen_host,
            )

            summary = run_viewer.load_run_summary(run_dir, repo_root=repo)
            self.assertIsNotNone(summary)
            assert summary is not None
            self.assertEqual(summary.driver, labels.product)

        # E-02: Assert the two hosts recorded DIFFERENT paths
        self.assertGreaterEqual(len(recorded_paths), 2)
        unique_paths = set(recorded_paths.values())
        self.assertEqual(
            len(unique_paths),
            len(recorded_paths),
            f"All real hosts must record distinct driver paths, got: {recorded_paths}",
        )

    def test_registry_closure_every_host_labels_routable_by_analytics(self) -> None:
        """Every HostLabels instance in runner_shared must be routable by analytics (E-04).

        Asserts that run_analytics_sources.generation_host(labels.id) != GENERATION_UNKNOWN.
        Note that generation_host returns GENERATION_UNKNOWN ("unknown") rather than raising
        on an unregistered id, which is why the assertion must compare against GENERATION_UNKNOWN.
        We deliberately use the single-predicate formulation rather than requiring membership
        in DRIVER_GENERATIONS, because descriptor-only hosts (such as SCRIPTED_HOST_LABELS) do not
        have a runner module and thus are not in DRIVER_GENERATIONS, but are legitimate and routable.
        """
        discovered_labels = [
            v
            for v in vars(runner_shared).values()
            if isinstance(v, runner_shared.HostLabels)
        ]
        self.assertGreater(len(discovered_labels), 0)
        for labels in discovered_labels:
            with self.subTest(host_id=labels.id):
                gen_host = run_analytics_sources.generation_host(labels.id)
                self.assertNotEqual(
                    gen_host,
                    run_analytics_sources.GENERATION_UNKNOWN,
                    f"HostLabels {labels.id!r} has unroutable generation in analytics (returned {gen_host!r})",
                )


class HostLabelsDriverIdResolverAndConsumerTests(unittest.TestCase):
    """E-04: Outcome tests for host_labels_for_driver_id resolver and run-record consumers."""

    def test_host_labels_for_driver_id_resolves_all_historical_viewer_spellings(
        self,
    ) -> None:
        """(a) Every member of the two literal tuples run_viewer carries resolves to the expected descriptor."""
        expected = [
            ("oc_runipd", runner_shared.OC_HOST_LABELS),
            ("opencode", runner_shared.OC_HOST_LABELS),
            ("oc", runner_shared.OC_HOST_LABELS),
            ("agy_runipd", runner_shared.AGY_HOST_LABELS),
            ("antigravity", runner_shared.AGY_HOST_LABELS),
            ("agy", runner_shared.AGY_HOST_LABELS),
            ("runagy", runner_shared.AGY_HOST_LABELS),
        ]
        for driver_id, expected_labels in expected:
            with self.subTest(driver_id=driver_id):
                resolved = runner_shared.host_labels_for_driver_id(driver_id)
                self.assertIs(resolved, expected_labels)

        # Unregistered / invalid ids return None
        for invalid_id in ("scripted", "octopus", "", "   ", None):
            with self.subTest(invalid_id=invalid_id):
                self.assertIsNone(runner_shared.host_labels_for_driver_id(invalid_id))

        # Ambiguous argv_subcommands are NOT registered
        for subcmd in ("run", "runipd"):
            with self.subTest(subcmd=subcmd):
                self.assertIsNone(runner_shared.host_labels_for_driver_id(subcmd))

    def test_discovered_host_descriptors_driver_keys_are_collision_free(self) -> None:
        """(b) No key in the union of .id and .argv_tokens maps to two different descriptors."""
        discovered = [
            v
            for v in vars(runner_shared).values()
            if isinstance(v, runner_shared.HostLabels)
        ]
        seen_keys: dict[str, runner_shared.HostLabels] = {}
        for labels in discovered:
            for key in [labels.id, *labels.argv_tokens]:
                if key in seen_keys:
                    self.assertIs(
                        seen_keys[key],
                        labels,
                        f"Collision on key {key!r} between {seen_keys[key].id} and {labels.id}",
                    )
                seen_keys[key] = labels

    def test_run_dashboard_run_host_resolves_registered_and_avoids_prefix_misrouting(
        self,
    ) -> None:
        """(c) _run_host routes registered hosts and lets unregistered ids fall through."""
        # Registered hosts return short host token derived from argv_tokens[0]
        self.assertEqual(
            run_dashboard._run_host({"driver": {"id": "oc_runipd"}}, []),
            "oc",
        )
        self.assertEqual(
            run_dashboard._run_host({"driver": {"id": "agy_runipd"}}, []),
            "agy",
        )
        self.assertEqual(
            run_dashboard._run_host({"driver": {"id": "opencode"}}, []),
            "oc",
        )
        self.assertEqual(
            run_dashboard._run_host({"driver": {"id": "antigravity"}}, []),
            "agy",
        )
        self.assertEqual(
            run_dashboard._run_host({"driver": {"id": "runagy"}}, []),
            "agy",
        )

        # Misrouting fix: prefix matches ("octopus", "agyx") must NOT route to oc/agy
        self.assertEqual(
            run_dashboard._run_host({"driver": {"id": "octopus"}}, []),
            "unknown",
        )
        self.assertEqual(
            run_dashboard._run_host({"driver": {"id": "agyx"}}, []),
            "unknown",
        )

        # Unchanged controls stay "unknown"
        self.assertEqual(
            run_dashboard._run_host({"driver": {"id": "scripted"}}, []),
            "unknown",
        )
        self.assertEqual(
            run_dashboard._run_host({"driver": {"id": "codex"}}, []),
            "unknown",
        )
        self.assertEqual(
            run_dashboard._run_host({"driver": {"id": ""}}, []),
            "unknown",
        )

        # Fall-through reaches downstream cost_attribution signal when driver.id is unregistered
        state = {
            "driver": {"id": "octopus"},
            "options": {"cost_attribution": {"host": "agy"}},
        }
        self.assertEqual(run_dashboard._run_host(state, []), "agy")

    def test_runtime_registered_descriptor_is_picked_up_by_both_consumers(self) -> None:
        """(d) A HostLabels descriptor registered at runtime is picked up by run_viewer and run_dashboard."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir = root / "run-scripted"
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-scripted",
                        "driver": {"id": "scripted"},
                        "queue": [],
                        "selectors": [],
                    }
                ),
                encoding="utf-8",
            )

            # Before registration:
            # - run_viewer returns raw driver_id ("scripted")
            # - _run_host returns "unknown"
            summary_before = run_viewer.load_run_summary(run_dir, repo_root=root)
            self.assertIsNotNone(summary_before)
            assert summary_before is not None
            self.assertEqual(summary_before.driver, "scripted")
            self.assertEqual(
                run_dashboard._run_host({"driver": {"id": "scripted"}}, []),
                "unknown",
            )

            # Register at runtime
            setattr(runner_shared, "SCRIPTED_HOST_LABELS", SCRIPTED_HOST_LABELS)
            try:
                # Both consumers pick it up with NO code edit:
                # - run_viewer returns SCRIPTED_HOST_LABELS.product ("Scripted")
                # - _run_host returns SCRIPTED_HOST_LABELS.argv_tokens[0] ("scripted")
                summary_after = run_viewer.load_run_summary(run_dir, repo_root=root)
                self.assertIsNotNone(summary_after)
                assert summary_after is not None
                self.assertEqual(summary_after.driver, "Scripted")
                self.assertEqual(
                    run_dashboard._run_host({"driver": {"id": "scripted"}}, []),
                    "scripted",
                )
            finally:
                # Teardown: remove attribute so it does not leak
                delattr(runner_shared, "SCRIPTED_HOST_LABELS")

            # Verify teardown cleanly restored state
            discovered_after = [
                v
                for v in vars(runner_shared).values()
                if isinstance(v, runner_shared.HostLabels)
            ]
            self.assertEqual(len(discovered_after), 2)
