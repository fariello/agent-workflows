"""Tests for tools/review_pilot.py (spec k3yx72; IPD kk62qt).

Verifies the pilot driver against a scratch git repository with fake runner launches:
  (a) --dry-run reports 84 cells split 24/24/36 and launches nothing
  (b) a built cell contains its one fixture under pending/ and no tests/fixtures/review-pilot/ path
  (c) a single cell's plan-review.md is byte-identical to the baseline commit's copy and a steps cell's is the pilot commit's
  (d) a cell already recorded as completed in cells.jsonl is not relaunched
  (e) with --budget below the recorded sum, no further cell launches
  (f) the E-06 redaction replaces every agent/model string in a sample after-plan and review record
  (g) the launch argv carries --unattended, --label pilot-k3yx72, and the cell's --review-mode/--review-variant
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from tests import support
import tools.review_pilot as review_pilot


class ReviewPilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(support.REPO_ROOT) / "tmp" / "test-review-pilot"
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Initialize a test git repository
        self.repo = support.init_repo(self.temp_dir / "repo")

        # Create baseline workflow and commit
        wf_dir = self.repo / ".aw" / "system" / "workflows" / "plan-review"
        wf_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_wf_file = wf_dir / "plan-review.md"
        self.baseline_content = (
            b"# Plan Review Workflow - Baseline Pre-Change Version\n"
        )
        self.baseline_wf_file.write_bytes(self.baseline_content)

        subprocess.check_call(["git", "add", "-A"], cwd=self.repo)
        subprocess.check_call(
            [
                "git",
                "-c",
                "user.name=test",
                "-c",
                "user.email=test@invalid",
                "commit",
                "-m",
                "baseline plan review",
            ],
            cwd=self.repo,
        )
        self.baseline_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.repo, text=True
        ).strip()

        # Update README.md with baseline commit and update plan-review.md to steps version
        readme_file = wf_dir / "README.md"
        readme_file.write_text(
            f"# plan-review\n\n## Pre-change baseline commit\n\n- Baseline commit: `{self.baseline_commit}`\n"
        )
        self.pilot_content = (
            b"# Plan Review Workflow - Multi-Prompt Steps Pilot Version\n"
        )
        self.baseline_wf_file.write_bytes(self.pilot_content)

        # Copy fixture manifest and plans from repo root into test repo
        test_fixtures_src = (
            Path(support.REPO_ROOT) / "tests" / "fixtures" / "review-pilot"
        )
        test_fixtures_dst = self.repo / "tests" / "fixtures" / "review-pilot"
        shutil.copytree(test_fixtures_src, test_fixtures_dst)

        # Commit pilot state
        subprocess.check_call(["git", "add", "-A"], cwd=self.repo)
        subprocess.check_call(
            [
                "git",
                "-c",
                "user.name=test",
                "-c",
                "user.email=test@invalid",
                "commit",
                "-m",
                "pilot state",
            ],
            cwd=self.repo,
        )
        self.pilot_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.repo, text=True
        ).strip()

        # Write pilot.json
        self.pilot_json = self.repo / "tmp" / "review-pilot" / "pilot.json"
        self.pilot_json.parent.mkdir(parents=True, exist_ok=True)
        self.pilot_json.write_text(
            json.dumps({"pilot_commit": self.pilot_commit}, indent=2)
        )

        self.cells_file = self.repo / "tmp" / "review-pilot" / "cells.jsonl"
        self.recorded_launches: list[list[str]] = []

    def tearDown(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def fake_launch(self, argv: list[str], cwd: Path | None = None) -> int:
        self.recorded_launches.append(list(argv))
        # Create minimal run state in cwd
        if cwd:
            run_dir = cwd / ".aw" / "records" / "runs" / "run-test-fake-001"
            run_dir.mkdir(parents=True, exist_ok=True)
            state = {
                "run_id": "run-test-fake-001",
                "status": "completed",
                "outcome": "completed",
                "exit_code": 0,
                "options": {"label": "pilot-k3yx72"},
                "queue": [
                    {
                        "id6": "h4nu1j",
                        "action": "review",
                        "status": "completed",
                        "review_tier": "simple",
                    }
                ],
            }
            (run_dir / "state.json").write_text(json.dumps(state, indent=2))
        return 0

    def test_a_dry_run_reports_84_cells_and_launches_nothing(self) -> None:
        """(a) --dry-run reports 84 cells split 24/24/36 and launches nothing."""
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        try:
            rc = review_pilot.main(
                [
                    "run",
                    "--dry-run",
                    "--repo",
                    str(self.repo),
                    "--cells-file",
                    str(self.cells_file),
                    "--pilot-file",
                    str(self.pilot_json),
                ]
            )
        finally:
            sys.stdout = old_stdout

        out = buffer.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("84 cells", out)
        self.assertIn("simple: 24", out)
        self.assertIn("standard: 24", out)
        self.assertIn("complex: 36", out)
        self.assertIn("total: 84", out)
        self.assertEqual(len(self.recorded_launches), 0)

    def test_b_built_cell_contains_one_fixture_and_no_fixtures_tree(self) -> None:
        """(b) a built cell contains its one fixture under pending/ and no tests/fixtures/review-pilot/ path."""
        specs = review_pilot.build_cell_specs(
            self.repo / "tests/fixtures/review-pilot/manifest.json"
        )
        cell = specs[0]
        cell_dir = review_pilot.build_cell(
            cell,
            repo_root=self.repo,
            pilot_commit=self.pilot_commit,
            baseline_commit=self.baseline_commit,
        )

        fixture_in_cell = (
            cell_dir / ".aw" / "records" / "plans" / "pending" / cell.fixture_filename
        )
        fixtures_tree = cell_dir / "tests" / "fixtures" / "review-pilot"

        self.assertTrue(fixture_in_cell.exists())
        self.assertFalse(fixtures_tree.exists())

    def test_c_plan_review_workflow_matches_baseline_or_pilot(self) -> None:
        """(c) a single cell's plan-review.md is byte-identical to the baseline commit's copy and a steps cell's is the pilot commit's."""
        specs = review_pilot.build_cell_specs(
            self.repo / "tests/fixtures/review-pilot/manifest.json"
        )
        single_cell = next(c for c in specs if c.method == "single")
        steps_cell = next(c for c in specs if c.method == "steps")

        single_dir = review_pilot.build_cell(
            single_cell,
            repo_root=self.repo,
            pilot_commit=self.pilot_commit,
            baseline_commit=self.baseline_commit,
        )
        steps_dir = review_pilot.build_cell(
            steps_cell,
            repo_root=self.repo,
            pilot_commit=self.pilot_commit,
            baseline_commit=self.baseline_commit,
        )

        single_wf = (
            single_dir
            / ".aw"
            / "system"
            / "workflows"
            / "plan-review"
            / "plan-review.md"
        )
        steps_wf = (
            steps_dir
            / ".aw"
            / "system"
            / "workflows"
            / "plan-review"
            / "plan-review.md"
        )

        self.assertEqual(single_wf.read_bytes(), self.baseline_content)
        self.assertEqual(steps_wf.read_bytes(), self.pilot_content)

    def test_d_completed_cell_not_relaunched(self) -> None:
        """(d) a cell already recorded as completed in cells.jsonl is not relaunched."""
        specs = review_pilot.build_cell_specs(
            self.repo / "tests/fixtures/review-pilot/manifest.json"
        )
        first_cell = specs[0]

        # Record first cell as completed
        self.cells_file.parent.mkdir(parents=True, exist_ok=True)
        completed_record = {
            "cell_key": first_cell.key,
            "fixture_id6": first_cell.fixture_id6,
            "method": first_cell.method,
            "model": first_cell.model,
            "repeat": first_cell.repeat,
            "outcome": "completed",
            "cost": 1.50,
        }
        self.cells_file.write_text(json.dumps(completed_record) + "\n")

        orig_launcher = review_pilot.launch_runner
        review_pilot.launch_runner = self.fake_launch
        try:
            rc = review_pilot.main(
                [
                    "run",
                    "--repo",
                    str(self.repo),
                    "--cells-file",
                    str(self.cells_file),
                    "--pilot-file",
                    str(self.pilot_json),
                    "--only-cell",
                    first_cell.key,
                ]
            )
            self.assertEqual(rc, 0)
            self.assertEqual(len(self.recorded_launches), 0)
        finally:
            review_pilot.launch_runner = orig_launcher

    def test_e_budget_cap_stops_launches(self) -> None:
        """(e) with --budget below the recorded sum, no further cell launches."""
        self.cells_file.parent.mkdir(parents=True, exist_ok=True)
        # Pre-record $50 spend
        self.cells_file.write_text(
            json.dumps({"cell_key": "prior", "cost": 50.0, "outcome": "completed"})
            + "\n"
        )

        orig_launcher = review_pilot.launch_runner
        review_pilot.launch_runner = self.fake_launch
        try:
            rc = review_pilot.main(
                [
                    "run",
                    "--budget",
                    "25.0",
                    "--repo",
                    str(self.repo),
                    "--cells-file",
                    str(self.cells_file),
                    "--pilot-file",
                    str(self.pilot_json),
                ]
            )
            self.assertEqual(rc, 0)
            self.assertEqual(len(self.recorded_launches), 0)
        finally:
            review_pilot.launch_runner = orig_launcher

    def test_f_redaction_replaces_agent_model_host_runid(self) -> None:
        """(f) the E-06 redaction replaces every agent/model string in a sample after-plan and review record."""
        sample_text = (
            "- Reviewer: opencode uri/its_direct/pt3-claude-opus-5.5-1m-us\n"
            "## Workflow history\n"
            "- 2026-10-25 reviewed (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE\n"
            "- 2026-10-25 review progress (antigravity gemini-3.8-flash-high): Round 1\n"
            "Model: openai/gpt-6.1-sol\n"
            "Run ID: run-20261025T230000Z-1234567\n"
        )
        redacted = review_pilot.redact_text(sample_text)
        self.assertNotIn("pt3-claude-opus", redacted)
        self.assertNotIn("gpt-6.1-sol", redacted)
        self.assertNotIn("gemini-3.8-flash", redacted)
        self.assertNotIn("opencode", redacted.lower())
        self.assertNotIn("antigravity", redacted.lower())
        self.assertNotIn("run-20261025T230000Z-1234567", redacted)
        self.assertIn("<redacted>", redacted)

    def test_g_launch_argv_options(self) -> None:
        """(g) the launch argv carries --unattended, --label pilot-k3yx72, and the cell's --review-mode/--review-variant."""
        specs = review_pilot.build_cell_specs(
            self.repo / "tests/fixtures/review-pilot/manifest.json"
        )
        steps_cell = next(
            c for c in specs if c.method == "steps" and c.review_variant == "grouped-6"
        )

        orig_launcher = review_pilot.launch_runner
        review_pilot.launch_runner = self.fake_launch
        try:
            review_pilot.run_single_cell(
                steps_cell,
                repo_root=self.repo,
                pilot_commit=self.pilot_commit,
                baseline_commit=self.baseline_commit,
                cells_file=self.cells_file,
            )
            self.assertEqual(len(self.recorded_launches), 1)
            argv = self.recorded_launches[0]
            self.assertIn("--unattended", argv)
            self.assertIn("--label", argv)
            self.assertEqual(argv[argv.index("--label") + 1], "pilot-k3yx72")
            self.assertIn("--review-mode", argv)
            self.assertEqual(argv[argv.index("--review-mode") + 1], "steps")
            self.assertIn("--review-variant", argv)
            self.assertEqual(argv[argv.index("--review-variant") + 1], "grouped-6")
        finally:
            review_pilot.launch_runner = orig_launcher


if __name__ == "__main__":
    unittest.main()
