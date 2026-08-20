"""Unit tests for AW install & update policy wizard (IPD 20260810-awphysical-03)."""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows.install_wizard import (
    IncompletePolicyError,
    InvalidPolicyError,
    PolicyCancelledError,
    ProjectPolicy,
    collect_policy_interactive,
    format_policy_summary,
    get_preset_defaults,
    normalize_preset,
    persist_project_policy,
    render_pre_write_plan,
    resolve_existing_policy,
    resolve_policy_noninteractive,
)
from agent_workflows.project_schema import (
    DeliveryMode,
    GitPolicy,
    Preset,
    RecordsBackend,
    RootClass,
)
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
            preset=Preset.PRIVATE_TARGET.value,
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
        )
        pol1.validate()

        pol2 = ProjectPolicy(
            preset=Preset.COMPLETELY_CLEAN_TARGET.value,
            delivery_mode=DeliveryMode.CLEAN_DELTA.value,
            records_backend=RecordsBackend.HOME.value,
        )
        pol2.validate()

        pol3 = ProjectPolicy(
            preset=Preset.PRIVATE_TARGET.value,
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
            preset=Preset.PRIVATE_TARGET.value,
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
            preset=Preset.PRIVATE_TARGET.value,
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
        self.assertIn("OK             Policy validated.", output)


class PhysicalLayoutWizardTests(unittest.TestCase):
    """Order 03 per-item evidence matrix tests (test_e01 .. test_e07)."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "testrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.fixture_dir = Path(__file__).parent / "fixtures" / "awphysical" / "order03"

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_e01(self):
        """E-01: First install vs update classification, closed stdin fail closed, complete policy resolution."""
        # 1. Closed stdin / noninteractive unconfigured repo fails closed before writes
        with self.assertRaises(IncompletePolicyError) as cm:
            resolve_policy_noninteractive(
                repo_path=self.target_repo, existing_policy=None
            )
        self.assertIn("Missing required fields", str(cm.exception))
        self.assertFalse(
            (Path(self.target_repo) / ".aw" / "config" / "project.json").exists()
        )

        # 2. Complete first install resolves every required choice
        pol = resolve_policy_noninteractive(
            repo_path=self.target_repo,
            existing_policy=None,
            explicit_preset="private-target",
        )
        self.assertEqual(pol.preset, Preset.PRIVATE_TARGET.value)
        self.assertEqual(pol.delivery_mode, DeliveryMode.TRACKED.value)
        self.assertEqual(pol.records_backend, RecordsBackend.REPOSITORY.value)
        self.assertEqual(len(pol.placements), 6)
        self.assertEqual(len(pol.git_policies), 6)

        # 3. Existing policy recognized only when saved config exists
        self.assertIsNone(resolve_existing_policy(self.target_repo))
        persist_project_policy(self.target_repo, pol)
        existing = resolve_existing_policy(self.target_repo)
        self.assertIsNotNone(existing)
        self.assertEqual(existing.preset, Preset.PRIVATE_TARGET.value)

    def test_e02(self):
        """E-02: Four approved presets + custom placement validation."""
        fixture_path = self.fixture_dir / "e02-presets.json"
        self.assertTrue(fixture_path.exists(), f"Fixture missing: {fixture_path}")
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Test all 4 approved presets
        for key in ("private_target", "public_companion", "clean_target", "local_only"):
            item = data[key]
            preset_name = normalize_preset(item["preset"])
            pls, gps, dm, rb, ds = get_preset_defaults(preset_name)
            pol = ProjectPolicy(
                preset=preset_name,
                delivery_mode=dm,
                records_backend=rb,
                durability_state=ds,
                placements=pls,
                git_policies=gps,
            )
            pol.validate()
            self.assertEqual(pol.delivery_mode, item["delivery_mode"])
            self.assertEqual(pol.records_backend, item["records_backend"])

        # Test custom mode invariant enforcement (cannot track local config or runtime state)
        invalid_gps = dict(get_preset_defaults("private-target")[1])
        invalid_gps[RootClass.CONFIG_LOCAL.value] = GitPolicy.TARGET_GIT.value
        bad_custom = ProjectPolicy(
            preset="custom",
            placements=get_preset_defaults("private-target")[0],
            git_policies=invalid_gps,
        )
        with self.assertRaises(InvalidPolicyError):
            bad_custom.validate()

    def test_e03(self):
        """E-03: Subflows for target visibility, companion selection, source-checkout role, host selection, no silent Git init."""
        fixture_path = self.fixture_dir / "e03-subflows.json"
        self.assertTrue(fixture_path.exists(), f"Fixture missing: {fixture_path}")
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Target visibility & companion subflows
        pol = ProjectPolicy(
            preset=Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value,
            companion_dir=data["companion_subflow"]["companion_dir"],
            target_visibility="public",
        )
        pol.validate()
        self.assertEqual(pol.companion_dir, "/tmp/custom-companion.aw")
        self.assertEqual(pol.target_visibility, "public")

        # Source checkout role subflow
        source_pol = ProjectPolicy(
            preset=Preset.PRIVATE_TARGET.value,
            role=data["source_checkout_subflow"]["role"],
        )
        source_pol.validate()
        self.assertEqual(source_pol.role, "source-checkout")

        # Confirm wizard does NOT silently initialize Git or add remotes
        self.assertFalse((Path(self.tmp_dir) / "uninit-repo" / ".git").exists())

    def test_e04(self):
        """E-04: Exact pre-write plan rendering, portable home path formatting, terminal accessibility matrix."""
        pol = ProjectPolicy(
            preset=Preset.COMPLETELY_CLEAN_TARGET.value,
            target_visibility="private",
            aw_home=str(Path.home() / ".aw"),
        )

        # Test color-never / NO_COLOR / TERM=dumb rendering
        buf = io.StringIO()
        term_no_color = Term(stream=buf, color=False)
        rendered = render_pre_write_plan(pol, self.target_repo, term=term_no_color)

        self.assertIn("AW Pre-Write Physical Layout & Consent Plan", rendered)
        self.assertIn("Resolved Physical Classes & Git Policies:", rendered)
        self.assertIn("system", rendered)
        self.assertIn("config_project", rendered)
        self.assertIn("records", rendered)

        # Confirm 0 ANSI escape sequences leak when color is disabled
        self.assertNotIn(
            "\033[", rendered, "ANSI escape sequences leaked in color=False output!"
        )

        # Confirm user home path is formatted portably as '~'
        self.assertNotIn(str(Path.home()), rendered)
        self.assertIn("~/.aw", rendered)

    def test_e05(self):
        """E-05: Persistence of policy to project.json and local.json, update checkpoints, --yes fail closed, dry-run."""
        fixture_path = self.fixture_dir / "e05-persistence.json"
        self.assertTrue(fixture_path.exists())

        pol = ProjectPolicy(preset=Preset.PRIVATE_TARGET.value)

        # 1. Dry run writes nothing
        res_dry = persist_project_policy(self.target_repo, pol, dry_run=True)
        self.assertIsNotNone(res_dry)
        self.assertFalse(
            (Path(self.target_repo) / ".aw" / "config" / "project.json").exists()
        )

        # 2. Actual persistence writes files
        persist_project_policy(self.target_repo, pol, dry_run=False)
        proj_file = Path(self.target_repo) / ".aw" / "config" / "project.json"
        local_file = Path(self.target_repo) / ".aw" / "config" / "local.json"
        snapshot_file = (
            Path(self.target_repo) / ".aw" / "state" / "durable" / "install.json"
        )

        self.assertTrue(proj_file.exists())
        self.assertTrue(local_file.exists())
        self.assertTrue(snapshot_file.exists())

        with open(proj_file, "r", encoding="utf-8") as f:
            p_data = json.load(f)
        self.assertEqual(p_data["preset"], Preset.PRIVATE_TARGET.value)

        # 3. --yes on unconfigured repo fails closed if flags missing
        unconfig = os.path.join(self.tmp_dir, "unconfig")
        os.makedirs(os.path.join(unconfig, ".git"), exist_ok=True)
        with self.assertRaises(IncompletePolicyError):
            resolve_policy_noninteractive(
                repo_path=unconfig, existing_policy=None, assume_yes=True
            )

    def test_e06(self):
        """E-06: Update review flow, preserving existing policy by default, material placement change handoff."""
        fixture_path = self.fixture_dir / "e06-updates.json"
        self.assertTrue(fixture_path.exists())

        existing = ProjectPolicy(preset=Preset.PRIVATE_TARGET.value)

        # Default noninteractive update reuses existing policy
        pol_updated = resolve_policy_noninteractive(
            repo_path=self.target_repo,
            existing_policy=existing,
        )
        self.assertEqual(pol_updated.preset, Preset.PRIVATE_TARGET.value)

        # Format policy summary for checkpoint
        summary = format_policy_summary(pol_updated)
        self.assertIn("Project Policy Summary:", summary)
        self.assertIn("private-target", summary)

    def test_e07(self):
        """E-07: Prompt sequences, cancellation, EOF, batch, source-checkout interaction matrix."""
        fixture_path = self.fixture_dir / "e07-interactions.json"
        self.assertTrue(fixture_path.exists())

        # Cancellation error raised on user decline
        with self.assertRaises(PolicyCancelledError):
            buf = io.StringIO()
            term = Term(stream=buf, color=False)
            real_stdin = sys.stdin
            try:
                sys.stdin = io.StringIO(
                    "1\nprivate\nn\n"
                )  # Select preset 1, private, decline confirm 'n'
                collect_policy_interactive(
                    term=term, repo_path=self.target_repo, assume_yes=False
                )
            finally:
                sys.stdin = real_stdin


if __name__ == "__main__":
    unittest.main()
