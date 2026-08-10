"""Unit tests for AW install & update policy wizard (IPD 20260809-awlayout-04)."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.install_wizard import (
    IncompletePolicyError,
    InvalidPolicyError,
    ProjectPolicy,
    resolve_policy_noninteractive,
)
from agent_workflows.project_schema import DeliveryMode, RecordsBackend
from agent_workflows.term import Term


class TestInstallWizardPolicy(unittest.TestCase):
    """Test policy model validation, noninteractive rules, update checkpoints, and accessibility matrix."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_policy_validation_clean_delta_repository_forbidden(self):
        """Rejects clean-delta delivery mode with repository records backend (spec Section 5.2)."""
        invalid_pol = ProjectPolicy(
            delivery_mode=DeliveryMode.CLEAN_DELTA.value,
            records_backend=RecordsBackend.REPOSITORY.value,
        )
        with self.assertRaises(InvalidPolicyError):
            invalid_pol.validate()

    def test_valid_policy_combinations(self):
        """Valid policy combinations pass validation cleanly."""
        pol1 = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
        )
        pol1.validate()

        pol2 = ProjectPolicy(
            delivery_mode=DeliveryMode.CLEAN_DELTA.value,
            records_backend=RecordsBackend.HOME.value,
        )
        pol2.validate()

        pol3 = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.REPOSITORY.value,
        )
        pol3.validate()

    def test_negative_noninteractive_unconfigured_first_install_fails(self):
        """NEGATIVE TEST: Noninteractive first install without complete flags fails before writes (L4-02)."""
        with self.assertRaises(IncompletePolicyError) as cm:
            resolve_policy_noninteractive(
                repo_path=self.target_repo, existing_policy=None
            )

        self.assertIn("Missing required fields", str(cm.exception))

    def test_noninteractive_existing_policy_reuse(self):
        """Existing policy is reused in noninteractive execution unless explicitly overridden."""
        existing = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
        )
        pol = resolve_policy_noninteractive(
            repo_path=self.target_repo,
            existing_policy=existing,
        )
        self.assertEqual(pol.delivery_mode, DeliveryMode.TRACKED.value)
        self.assertEqual(pol.records_backend, RecordsBackend.HOME.value)

    def test_noninteractive_explicit_flag_overrides(self):
        """Explicit flags override noninteractive resolution."""
        existing = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
        )
        pol = resolve_policy_noninteractive(
            repo_path=self.target_repo,
            existing_policy=existing,
            explicit_delivery="clean-delta",
        )
        self.assertEqual(pol.delivery_mode, "clean-delta")

    def test_accessibility_term_and_summary_linear_output(self):
        """Test linear plain-text output across term settings (NO_COLOR, TERM=dumb, --no-color)."""
        buf = io.StringIO()
        term_no_color = Term(stream=buf, color=False)
        term_no_color.heading("Policy Summary")
        term_no_color.status("ok", "Policy validated.")

        output = buf.getvalue()
        self.assertNotIn(
            "\033[",
            output,
            "Output contained ANSI escape sequences when color was disabled!",
        )
        self.assertIn("OK  Policy validated.", output)

    def test_cli_install_dry_run_accessibility_matrix(self):
        """Test `aw install . --dry-run` under NO_COLOR=1, TERM=dumb, and --no-color."""
        base_cmd = [
            "python3",
            "-m",
            "agent_workflows",
            "install",
            ".",
            "--dry-run",
        ]

        # 1. NO_COLOR=1
        env_no_color = dict(os.environ, NO_COLOR="1")
        res1 = subprocess.run(
            base_cmd,
            capture_output=True,
            text=True,
            env=env_no_color,
            cwd=Path(__file__).parent.parent,
        )
        self.assertEqual(res1.returncode, 0, f"NO_COLOR error: {res1.stderr}")
        self.assertNotIn("\033[", res1.stdout)

        # 2. TERM=dumb
        env_dumb = dict(os.environ, TERM="dumb")
        env_dumb.pop("NO_COLOR", None)
        res2 = subprocess.run(
            base_cmd,
            capture_output=True,
            text=True,
            env=env_dumb,
            cwd=Path(__file__).parent.parent,
        )
        self.assertEqual(res2.returncode, 0, f"TERM=dumb error: {res2.stderr}")
        self.assertNotIn("\033[", res2.stdout)

        # 3. --no-color flag
        cmd_flag = base_cmd + ["--no-color"]
        res3 = subprocess.run(
            cmd_flag,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        self.assertEqual(res3.returncode, 0, f"--no-color error: {res3.stderr}")
        self.assertNotIn("\033[", res3.stdout)


if __name__ == "__main__":
    unittest.main()
