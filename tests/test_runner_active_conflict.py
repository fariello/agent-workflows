#!/usr/bin/env python3

"""Tests for active runner conflict resolution policy (drop, refuse, force, prompt)."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    runner_shared,
)
from agent_workflows.runner_shared import (
    DEFAULT_ON_CONFLICT,
    ON_CONFLICT_DROP,
    ON_CONFLICT_FORCE,
    ON_CONFLICT_PROMPT,
    ON_CONFLICT_REFUSE,
    DriverError,
    RunFlagRefusal,
    enforce_no_active_runner_conflict,
    freeze_run_policy_flags,
    resolve_on_conflict,
)


class RunnerConflictFlagTests(unittest.TestCase):
    """Test CLI argument parsing and convenience flags across both runner hosts."""

    def test_oc_runner_flag_registration_and_aliases(self) -> None:
        parser = oc_runipd.build_parser()

        # Omitted flag -> None
        args = parser.parse_args(["start", "all"])
        self.assertIsNone(args.on_conflict)

        # Main flag --on-conflict
        args = parser.parse_args(["start", "all", "--on-conflict", "refuse"])
        self.assertEqual(args.on_conflict, "refuse")
        args = parser.parse_args(["start", "all", "--on-conflict", "drop"])
        self.assertEqual(args.on_conflict, "drop")
        args = parser.parse_args(["start", "all", "--on-conflict", "force"])
        self.assertEqual(args.on_conflict, "force")
        args = parser.parse_args(["start", "all", "--on-conflict", "prompt"])
        self.assertEqual(args.on_conflict, "prompt")
        args = parser.parse_args(["start", "all", "--on-conflict", "ask"])
        self.assertEqual(args.on_conflict, "ask")

        # Alias --conflict
        args = parser.parse_args(["start", "all", "--conflict", "drop"])
        self.assertEqual(args.on_conflict, "drop")

        # Refuse convenience flags
        args = parser.parse_args(["start", "all", "--refuse-conflicts"])
        self.assertEqual(args.on_conflict, "refuse")
        args = parser.parse_args(["start", "all", "--refuse-running"])
        self.assertEqual(args.on_conflict, "refuse")

        # Drop convenience flags
        args = parser.parse_args(["start", "all", "--drop-conflicts"])
        self.assertEqual(args.on_conflict, "drop")
        args = parser.parse_args(["start", "all", "--drop-running"])
        self.assertEqual(args.on_conflict, "drop")

        # Force convenience flags
        args = parser.parse_args(["start", "all", "--force-conflicts"])
        self.assertEqual(args.on_conflict, "force")
        args = parser.parse_args(["start", "all", "--dangerously-force-conflict"])
        self.assertEqual(args.on_conflict, "force")
        args = parser.parse_args(["start", "all", "--force-running"])
        self.assertEqual(args.on_conflict, "force")

        # Prompt convenience flags
        args = parser.parse_args(["start", "all", "--prompt-conflicts"])
        self.assertEqual(args.on_conflict, "prompt")
        args = parser.parse_args(["start", "all", "--ask-conflicts"])
        self.assertEqual(args.on_conflict, "prompt")

    def test_agy_runner_flag_registration_and_aliases(self) -> None:
        parser = agy_runipd.build_parser()

        args = parser.parse_args(["start", "all"])
        self.assertIsNone(args.on_conflict)

        args = parser.parse_args(["start", "all", "--refuse-conflicts"])
        self.assertEqual(args.on_conflict, "refuse")
        args = parser.parse_args(["start", "all", "--drop-conflicts"])
        self.assertEqual(args.on_conflict, "drop")
        args = parser.parse_args(["start", "all", "--force-conflicts"])
        self.assertEqual(args.on_conflict, "force")
        args = parser.parse_args(["start", "all", "--prompt-conflicts"])
        self.assertEqual(args.on_conflict, "prompt")


class ConflictPolicyResolutionTests(unittest.TestCase):
    """Test policy resolution hierarchy: CLI > project policy > user config > default."""

    def test_cli_value_takes_highest_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"run": {"on_conflict": "drop"}}), encoding="utf-8"
            )

            # CLI "refuse" overrides project "drop"
            res = resolve_on_conflict("refuse", repo=repo)
            self.assertEqual(res, "refuse")

            # CLI "force" overrides project "drop"
            res = resolve_on_conflict("force", repo=repo)
            self.assertEqual(res, "force")

            # CLI "ask" normalizes to "prompt"
            res = resolve_on_conflict("ask", repo=repo)
            self.assertEqual(res, "prompt")

    def test_invalid_cli_value_raises_run_flag_refusal(self) -> None:
        with self.assertRaises(RunFlagRefusal) as ctx:
            resolve_on_conflict("invalid-mode")
        self.assertIn("invalid-mode", str(ctx.exception))

    def test_project_policy_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)

            # Nested under run.on_conflict
            (cfg_dir / "project.json").write_text(
                json.dumps({"run": {"on_conflict": "refuse"}}), encoding="utf-8"
            )
            res = resolve_on_conflict(None, repo=repo)
            self.assertEqual(res, "refuse")

            # Flat on_conflict
            (cfg_dir / "project.json").write_text(
                json.dumps({"on_conflict": "force"}), encoding="utf-8"
            )
            res = resolve_on_conflict(None, repo=repo)
            self.assertEqual(res, "force")

            # Project policy "ask" normalizes to "prompt"
            (cfg_dir / "project.json").write_text(
                json.dumps({"run": {"on_conflict": "ask"}}), encoding="utf-8"
            )
            res = resolve_on_conflict(None, repo=repo)
            self.assertEqual(res, "prompt")

    def test_user_config_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            uconf_dir = Path(td) / "user_config"
            uconf_dir.mkdir()
            uconf_file = uconf_dir / "config.json"

            with mock.patch(
                "agent_workflows.config.config_path", return_value=uconf_file
            ):
                # Set in user config under defaults.on_conflict
                uconf_file.write_text(
                    json.dumps({"defaults": {"on_conflict": "prompt"}}),
                    encoding="utf-8",
                )
                res = resolve_on_conflict(None, repo=repo)
                self.assertEqual(res, "prompt")

                # Project policy overrides user config
                cfg_dir = repo / ".aw" / "config"
                cfg_dir.mkdir(parents=True)
                (cfg_dir / "project.json").write_text(
                    json.dumps({"run": {"on_conflict": "refuse"}}), encoding="utf-8"
                )
                res = resolve_on_conflict(None, repo=repo)
                self.assertEqual(res, "refuse")

    def test_default_resolution_when_unset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            res = resolve_on_conflict(None, repo=repo)
            self.assertEqual(res, DEFAULT_ON_CONFLICT)
            self.assertEqual(res, "drop")

    def test_malformed_project_policy_warns_and_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"run": {"on_conflict": "not-a-valid-choice"}}),
                encoding="utf-8",
            )

            warnings: list[str] = []
            res = resolve_on_conflict(None, repo=repo, warn=warnings.append)
            self.assertEqual(res, "drop")
            self.assertEqual(len(warnings), 1)
            self.assertIn("not-a-valid-choice", warnings[0])

    def test_freeze_run_policy_flags_includes_on_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"run": {"on_conflict": "refuse"}}), encoding="utf-8"
            )

            class MockArgs:
                on_conflict = None
                unattended = False
                full_auto = False
                allow_unverifiable = False
                unverifiable_ok = False
                retry_budget = None
                allow_dirty_base = False
                integration_retry_limit = None
                on_integration_blocked = None
                allow_uncovered_orchestrator_work = None
                allow_concurrent_driver = None
                types = None
                allow_mixed = False
                allow_drafts = False

            frozen = freeze_run_policy_flags(MockArgs(), repo=repo)
            self.assertEqual(frozen.get("on_conflict"), "refuse")


class EnforceActiveRunnerConflictTests(unittest.TestCase):
    """Test enforce_no_active_runner_conflict behavior under each mode."""

    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.repo = Path(self.td.name)
        plans_dir = self.repo / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True)

        self.plan1 = plans_dir / "20260925-test01-01-aaaaaa-item-one.ipd.md"
        self.plan1.write_text(
            "---\n- Id: aaaaaa\n- Status: approved\n- Set: test01\n---\n# Plan 1\n",
            encoding="utf-8",
        )
        self.plan2 = plans_dir / "20260925-test01-02-bbbbbb-item-two.ipd.md"
        self.plan2.write_text(
            "---\n- Id: bbbbbb\n- Status: approved\n- Set: test01\n---\n# Plan 2\n",
            encoding="utf-8",
        )

        self.manifest = {
            "plans": {
                "aaaaaa": {
                    "file": str(self.plan1.relative_to(self.repo)),
                    "status": "approved",
                    "set": "test01",
                },
                "bbbbbb": {
                    "file": str(self.plan2.relative_to(self.repo)),
                    "status": "approved",
                    "set": "test01",
                },
            }
        }

    def tearDown(self) -> None:
        self.td.cleanup()

    def test_no_active_runs_proceeds_cleanly(self) -> None:
        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value={}
        ):
            q_ids, p_paths = enforce_no_active_runner_conflict(
                self.repo,
                ["aaaaaa", "bbbbbb"],
                [self.plan1, self.plan2],
                manifest=self.manifest,
            )
            self.assertEqual(q_ids, ["aaaaaa", "bbbbbb"])
            self.assertEqual(p_paths, [self.plan1, self.plan2])

    def test_drop_mode_drops_conflicting_items_and_narrates(self) -> None:
        # aaaaaa is actively running; bbbbbb is not
        active_map = {"aaaaaa": "running"}
        stream = io.StringIO()

        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value=active_map
        ):
            q_ids, p_paths = enforce_no_active_runner_conflict(
                self.repo,
                ["aaaaaa", "bbbbbb"],
                [self.plan1, self.plan2],
                manifest=self.manifest,
                on_conflict=ON_CONFLICT_DROP,
                stream=stream,
            )

        # aaaaaa was dropped; bbbbbb was kept
        self.assertEqual(q_ids, ["bbbbbb"])
        self.assertEqual(p_paths, [self.plan2])

        output = stream.getvalue()
        self.assertIn("Notice: Removed 1 artifact(s) from the queue", output)
        self.assertIn("aaaaaa", output)

    def test_drop_mode_when_all_items_conflict_raises_driver_error(self) -> None:
        # Both aaaaaa and bbbbbb are actively running / queued
        active_map = {"aaaaaa": "running", "bbbbbb": "queued"}
        stream = io.StringIO()

        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value=active_map
        ):
            with self.assertRaises(DriverError) as ctx:
                enforce_no_active_runner_conflict(
                    self.repo,
                    ["aaaaaa", "bbbbbb"],
                    [self.plan1, self.plan2],
                    manifest=self.manifest,
                    on_conflict=ON_CONFLICT_DROP,
                    stream=stream,
                )

        self.assertIn(
            "No artifacts left to run: all selected artifacts are already being processed",
            str(ctx.exception),
        )
        output = stream.getvalue()
        self.assertIn("Notice: Removed 2 artifact(s) from the queue", output)

    def test_refuse_mode_raises_driver_error_with_table(self) -> None:
        active_map = {"aaaaaa": "running"}
        stream = io.StringIO()

        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value=active_map
        ):
            with self.assertRaises(DriverError) as ctx:
                enforce_no_active_runner_conflict(
                    self.repo,
                    ["aaaaaa", "bbbbbb"],
                    [self.plan1, self.plan2],
                    manifest=self.manifest,
                    on_conflict=ON_CONFLICT_REFUSE,
                    stream=stream,
                )

        self.assertIn(
            "Cannot run artifacts that are actively being processed by another runner",
            str(ctx.exception),
        )
        self.assertIn("aaaaaa", str(ctx.exception))

    def test_force_mode_warns_and_retains_all_items(self) -> None:
        active_map = {"aaaaaa": "running"}
        stream = io.StringIO()

        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value=active_map
        ):
            q_ids, p_paths = enforce_no_active_runner_conflict(
                self.repo,
                ["aaaaaa", "bbbbbb"],
                [self.plan1, self.plan2],
                manifest=self.manifest,
                on_conflict=ON_CONFLICT_FORCE,
                stream=stream,
            )

        self.assertEqual(q_ids, ["aaaaaa", "bbbbbb"])
        self.assertEqual(p_paths, [self.plan1, self.plan2])
        output = stream.getvalue()
        self.assertIn("WARNING: Dangerously forcing execution of 1 artifact(s)", output)

    def test_prompt_mode_interactive_drop_choice(self) -> None:
        active_map = {"aaaaaa": "running"}
        stream = io.StringIO()

        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value=active_map
        ):
            with mock.patch("sys.stdin", io.StringIO("d\n")):
                q_ids, p_paths = enforce_no_active_runner_conflict(
                    self.repo,
                    ["aaaaaa", "bbbbbb"],
                    [self.plan1, self.plan2],
                    manifest=self.manifest,
                    on_conflict=ON_CONFLICT_PROMPT,
                    interactive=True,
                    stream=stream,
                )

        self.assertEqual(q_ids, ["bbbbbb"])
        self.assertEqual(p_paths, [self.plan2])
        output = stream.getvalue()
        self.assertIn(
            "What would you like to do? [D]rop conflicting items (default) / [R]efuse / [F]orce:",
            output,
        )
        self.assertIn("Notice: Removed 1 artifact(s) from the queue", output)

    def test_prompt_mode_interactive_default_on_empty_enter(self) -> None:
        active_map = {"aaaaaa": "running"}
        stream = io.StringIO()

        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value=active_map
        ):
            with mock.patch("sys.stdin", io.StringIO("\n")):
                q_ids, p_paths = enforce_no_active_runner_conflict(
                    self.repo,
                    ["aaaaaa", "bbbbbb"],
                    [self.plan1, self.plan2],
                    manifest=self.manifest,
                    on_conflict=ON_CONFLICT_PROMPT,
                    interactive=True,
                    stream=stream,
                )

        # Empty enter defaults to "drop"
        self.assertEqual(q_ids, ["bbbbbb"])
        self.assertEqual(p_paths, [self.plan2])

    def test_prompt_mode_interactive_refuse_choice(self) -> None:
        active_map = {"aaaaaa": "running"}
        stream = io.StringIO()

        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value=active_map
        ):
            with mock.patch("sys.stdin", io.StringIO("r\n")):
                with self.assertRaises(DriverError) as ctx:
                    enforce_no_active_runner_conflict(
                        self.repo,
                        ["aaaaaa", "bbbbbb"],
                        [self.plan1, self.plan2],
                        manifest=self.manifest,
                        on_conflict=ON_CONFLICT_PROMPT,
                        interactive=True,
                        stream=stream,
                    )
        self.assertIn(
            "Cannot run artifacts that are actively being processed by another runner",
            str(ctx.exception),
        )

    def test_prompt_mode_interactive_force_choice(self) -> None:
        active_map = {"aaaaaa": "running"}
        stream = io.StringIO()

        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value=active_map
        ):
            with mock.patch("sys.stdin", io.StringIO("f\n")):
                q_ids, p_paths = enforce_no_active_runner_conflict(
                    self.repo,
                    ["aaaaaa", "bbbbbb"],
                    [self.plan1, self.plan2],
                    manifest=self.manifest,
                    on_conflict=ON_CONFLICT_PROMPT,
                    interactive=True,
                    stream=stream,
                )
        self.assertEqual(q_ids, ["aaaaaa", "bbbbbb"])
        self.assertEqual(p_paths, [self.plan1, self.plan2])

    def test_prompt_mode_non_interactive_falls_back_to_drop(self) -> None:
        active_map = {"aaaaaa": "running"}
        stream = io.StringIO()

        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value=active_map
        ):
            q_ids, p_paths = enforce_no_active_runner_conflict(
                self.repo,
                ["aaaaaa", "bbbbbb"],
                [self.plan1, self.plan2],
                manifest=self.manifest,
                on_conflict=ON_CONFLICT_PROMPT,
                interactive=False,
                stream=stream,
            )

        self.assertEqual(q_ids, ["bbbbbb"])
        self.assertEqual(p_paths, [self.plan2])
        output = stream.getvalue()
        self.assertIn(
            "Non-interactive run: defaulting to dropping conflicting items.", output
        )
        self.assertIn("Notice: Removed 1 artifact(s) from the queue", output)

    def test_initialize_run_core_drops_conflicting_artifacts(self) -> None:
        """initialize_run_core prunes active items when on_conflict='drop'."""
        import argparse
        import subprocess

        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=self.repo, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=self.repo, check=True)

        args = argparse.Namespace(
            repo=str(self.repo),
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
            run_id="run-20260925T000000Z-111111",
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
            on_conflict="drop",
        )

        active_map = {"aaaaaa": "running"}
        with mock.patch(
            "agent_workflows.attention.get_active_runs_map", return_value=active_map
        ):
            run_dir = runner_shared.initialize_run_core(
                args,
                host="oc",
                driver_path=None,
                host_options={},
                labels=runner_shared.OC_HOST_LABELS,
                expand_selectors_fn=lambda manifest, selectors, **kw: [
                    "aaaaaa",
                    "bbbbbb",
                ],
                enforce_dependency_preflight_fn=lambda *a, **kw: None,
                announce_run_order_fn=lambda rdir, st: None,
                run_order_rationale_fn=lambda queue, sel: "test rationale",
                write_report_fn=lambda rdir, st: None,
            )

        self.assertTrue(run_dir.exists())
        state = runner_shared.load_state(run_dir)
        queue_ids = [item["id6"] for item in state["queue"]]
        self.assertEqual(queue_ids, ["bbbbbb"])
        self.assertEqual(state["options"]["on_conflict"], "drop")


if __name__ == "__main__":
    unittest.main()
